"""Install DIY error tracker: DB schema + 3 endpoints + exception handler + SSE hook."""
from pathlib import Path

P = Path('/opt/untitled-pick-game-api/main.py')
src = P.read_text(encoding='utf-8')


# ─── 1. Add `errors` table to db_init ────────────────────────────
ddl_anchor = '            CREATE INDEX IF NOT EXISTS idx_subs_user ON submissions(user_id);'
ddl_inject = ddl_anchor + '''

            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,                  -- 'backend' | 'frontend'
                level TEXT NOT NULL DEFAULT 'error',   -- 'error' | 'warning' | 'info'
                message TEXT NOT NULL,
                stack TEXT,
                url TEXT,
                user_agent TEXT,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                nickname TEXT,
                ip TEXT,
                context_json TEXT,
                dedupe_key TEXT,
                occurred_at TEXT NOT NULL,
                seen_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_errors_seen   ON errors(seen_at, occurred_at DESC);
            CREATE INDEX IF NOT EXISTS idx_errors_dedupe ON errors(dedupe_key, occurred_at DESC);
'''
assert ddl_anchor in src, 'DDL anchor missing'
src = src.replace(ddl_anchor, ddl_inject, 1)


# ─── 2. Pydantic models + helpers + 3 endpoints + exception handler
# Insert before /api/admin/anthropic-status
insert_anchor = '@app.get("/api/admin/anthropic-status")'

new_block = '''class ErrorReportIn(BaseModel):
    """Public error report from the browser (window.onerror, unhandledrejection)."""
    message: str = Field(..., min_length=1, max_length=2000)
    stack: Optional[str] = Field(default=None, max_length=20000)
    url: Optional[str] = Field(default=None, max_length=2000)
    level: Optional[str] = Field(default='error', pattern=r'^(error|warning|info)$')
    context: Optional[dict] = None


# Simple in-memory rate limit: {ip: [timestamps]}, sliding 60s window.
# 100 reports/min/IP is generous; any client bug-loop hits this and stops.
_err_rl: dict = {}
_ERR_RL_LIMIT = 100
_ERR_RL_WINDOW = 60.0

def _err_rate_limit(ip: str) -> bool:
    """Returns True if allowed, False if throttled."""
    import time as _t
    now = _t.time()
    bucket = _err_rl.setdefault(ip, [])
    # drop timestamps outside the window
    cutoff = now - _ERR_RL_WINDOW
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    if len(bucket) >= _ERR_RL_LIMIT:
        return False
    bucket.append(now)
    return True


def _dedupe_key(source: str, message: str, stack: str | None) -> str:
    """Hash of (source + first stack line + first 60 chars of message).
    Used to group similar errors for the admin view."""
    import hashlib
    first_line = (stack or '').strip().split('\\n')[0] if stack else ''
    raw = f"{source}|{first_line}|{(message or '')[:60]}"
    return hashlib.sha1(raw.encode('utf-8', 'replace')).hexdigest()[:16]


def _store_error(*, source: str, message: str, stack: str | None,
                 url: str | None, user_agent: str | None,
                 user_id: int | None, nickname: str | None,
                 ip: str | None, level: str = 'error',
                 context: dict | None = None) -> int:
    """Inserts an error row, returns its id. Also publishes an SSE event."""
    key = _dedupe_key(source, message, stack)
    ctx = json.dumps(context, ensure_ascii=False) if context else None
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO errors (source, level, message, stack, url, user_agent, "
            "user_id, nickname, ip, context_json, dedupe_key, occurred_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (source, level, message[:2000], (stack or '')[:20000], url, user_agent,
             user_id, nickname, ip, ctx, key, now_iso()),
        )
        eid = cur.lastrowid
    # Push to admin SSE listeners (best-effort; sync wrapper handles loop scheduling)
    try:
        publish_admin_event_sync('error_new', {
            'id': eid,
            'source': source,
            'level': level,
            'message': message[:200],
            'occurred_at': now_iso(),
            'dedupe_key': key,
        })
    except Exception:
        pass
    return eid


@app.post("/api/errors", status_code=201)
async def report_error(body: ErrorReportIn, request: Request):
    """Public endpoint for browser-side error reports. Rate-limited per IP."""
    ip = (request.client.host if request.client else None) or 'unknown'
    if not _err_rate_limit(ip):
        raise HTTPException(429, "rate_limited")
    user_agent = request.headers.get('user-agent', '')[:500]
    # Try to attach the user (best-effort; anonymous OK)
    user_id, nickname = None, None
    try:
        sess = request.cookies.get(COOKIE_NAME)
        if sess:
            with db() as conn:
                row = conn.execute(
                    "SELECT u.id, u.nickname FROM sessions s JOIN users u ON u.id = s.user_id "
                    "WHERE s.token = ? AND (s.expires_at IS NULL OR s.expires_at > ?)",
                    (sess, now_iso())
                ).fetchone()
                if row:
                    user_id, nickname = row['id'], row['nickname']
    except Exception:
        pass
    eid = _store_error(
        source='frontend',
        message=body.message,
        stack=body.stack,
        url=body.url,
        user_agent=user_agent,
        user_id=user_id,
        nickname=nickname,
        ip=ip,
        level=body.level or 'error',
        context=body.context,
    )
    return {"ok": True, "id": eid}


@app.exception_handler(Exception)
async def _backend_exception_handler(request: Request, exc: Exception):
    """Catches uncaught backend exceptions and writes them to the errors table.
    HTTPException is re-raised normally (those are intentional 4xx, not bugs).
    Returns 500 with a minimal body — full stack stays server-side."""
    if isinstance(exc, HTTPException):
        # Let FastAPI handle 4xx/intentional 5xx as before
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    import traceback
    stack = traceback.format_exc()
    ip = (request.client.host if request.client else None) or 'unknown'
    user_agent = request.headers.get('user-agent', '')[:500]
    try:
        _store_error(
            source='backend',
            message=f"{type(exc).__name__}: {str(exc)[:500]}",
            stack=stack,
            url=str(request.url.path),
            user_agent=user_agent,
            user_id=None,
            nickname=None,
            ip=ip,
            level='error',
            context={'method': request.method},
        )
    except Exception:
        # Even error-logging can fail (DB down etc.) — don't recurse
        logging.exception("error logger itself failed")
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": "internal_error"})


@app.get("/api/admin/errors")
def admin_list_errors(_role: str = Depends(require_mod_or_admin),
                      source: str | None = None,
                      hours: int | None = None,
                      only_unseen: bool = False,
                      limit: int = 100,
                      offset: int = 0):
    """List errors with simple filters. Default sort: newest first."""
    if limit > 500: limit = 500
    where, vals = ["1=1"], []
    if source in ('frontend', 'backend'):
        where.append("source = ?"); vals.append(source)
    if hours and hours > 0:
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat().replace('+00:00', 'Z')
        where.append("occurred_at >= ?"); vals.append(cutoff)
    if only_unseen:
        where.append("seen_at IS NULL")
    sql = (
        "SELECT id, source, level, message, stack, url, user_agent, user_id, "
        "nickname, ip, context_json, dedupe_key, occurred_at, seen_at "
        f"FROM errors WHERE {' AND '.join(where)} ORDER BY occurred_at DESC LIMIT ? OFFSET ?"
    )
    vals += [limit, offset]
    with db() as conn:
        rows = conn.execute(sql, vals).fetchall()
        unseen_total = conn.execute(
            "SELECT COUNT(*) FROM errors WHERE seen_at IS NULL"
        ).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM errors").fetchone()[0]
    out = []
    for r in rows:
        ctx = None
        if r['context_json']:
            try: ctx = json.loads(r['context_json'])
            except Exception: pass
        out.append({
            'id': r['id'],
            'source': r['source'],
            'level': r['level'],
            'message': r['message'],
            'stack': r['stack'],
            'url': r['url'],
            'user_agent': r['user_agent'],
            'user_id': r['user_id'],
            'nickname': r['nickname'],
            'ip': r['ip'],
            'context': ctx,
            'dedupe_key': r['dedupe_key'],
            'occurred_at': r['occurred_at'],
            'seen_at': r['seen_at'],
        })
    return {'errors': out, 'total': total, 'unseen': unseen_total}


@app.post("/api/admin/errors/{err_id}/seen")
def admin_mark_error_seen(err_id: int, _role: str = Depends(require_mod_or_admin)):
    with db() as conn:
        conn.execute("UPDATE errors SET seen_at = ? WHERE id = ? AND seen_at IS NULL",
                     (now_iso(), err_id))
    return {'ok': True}


@app.post("/api/admin/errors/seen-all")
def admin_mark_all_errors_seen(_role: str = Depends(require_mod_or_admin)):
    with db() as conn:
        cur = conn.execute("UPDATE errors SET seen_at = ? WHERE seen_at IS NULL", (now_iso(),))
        n = cur.rowcount
    return {'ok': True, 'marked': n}


@app.delete("/api/admin/errors/cleanup")
def admin_cleanup_errors(older_than_days: int = 30,
                         _role: str = Depends(require_mod_or_admin)):
    """Delete errors older than N days. Default 30."""
    if older_than_days < 1: older_than_days = 1
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat().replace('+00:00', 'Z')
    with db() as conn:
        cur = conn.execute("DELETE FROM errors WHERE occurred_at < ?", (cutoff,))
        n = cur.rowcount
    return {'ok': True, 'deleted': n, 'older_than_days': older_than_days}


'''
assert insert_anchor in src, 'insert anchor missing'
src = src.replace(insert_anchor, new_block + insert_anchor, 1)


# ─── 3. COOKIE_NAME — find existing or stub ──────────────
if 'COOKIE_NAME' not in src:
    # Fall back to looking up cookie name dynamically
    src = src.replace(
        "sess = request.cookies.get(COOKIE_NAME)",
        "sess = next((v for k, v in request.cookies.items() if k.startswith('upg_session') or k == 'session'), None)"
    )


P.write_text(src, encoding='utf-8')
print('OK: errors table + 5 endpoints + exception handler + SSE hook installed')
