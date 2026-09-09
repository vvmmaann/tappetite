"""Install SSE real-time admin queue: pub/sub + endpoint + 3 publishers.

Run on the server (the script edits /opt/untitled-pick-game-api/main.py in place).
"""
from pathlib import Path

P = Path('/opt/untitled-pick-game-api/main.py')
src = P.read_text(encoding='utf-8')

# ─── 1. Imports ────────────────────────────────────────────────
old_imp = 'from fastapi.responses import HTMLResponse'
new_imp = (
    'from fastapi.responses import HTMLResponse\n'
    'from starlette.responses import StreamingResponse\n'
    'import asyncio'
)
assert old_imp in src, 'import anchor not found'
src = src.replace(old_imp, new_imp, 1)

# ─── 2. Pub/sub primitives — inject after `app = FastAPI(...)` line ─────
app_anchor = 'app = FastAPI(title="UNTITLED PICK GAME API"'
idx = src.find(app_anchor)
assert idx >= 0, 'app anchor not found'
line_end = src.find('\n', idx)
inject = '''


# ─── ADMIN REAL-TIME EVENTS (SSE) ─────────────────────────────────
# In-process pub/sub for the admin queue. Each connected admin/moderator gets
# their own asyncio.Queue; publish_admin_event broadcasts to all of them.
# Single-process safe by design (uvicorn --workers 1).
_admin_event_clients: "set[asyncio.Queue]" = set()
_admin_events_lock = asyncio.Lock()

async def publish_admin_event(event_type: str, data: dict) -> None:
    """Push an event to every connected admin SSE listener. Best-effort:
    a full queue drops the event for that one client (over-subscribed)."""
    payload = {"type": event_type, "data": data}
    async with _admin_events_lock:
        clients = list(_admin_event_clients)
    for q in clients:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass

def publish_admin_event_sync(event_type: str, data: dict) -> None:
    """Sync wrapper for non-async endpoints. Schedules the broadcast on the
    running asyncio loop. No-op if no loop (e.g. test harness)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(publish_admin_event(event_type, data))
        else:
            asyncio.run(publish_admin_event(event_type, data))
    except RuntimeError:
        pass

'''
src = src[:line_end + 1] + inject + src[line_end + 1:]

# ─── 3. SSE endpoint — insert before /api/admin/anthropic-status ─────
anchor = '@app.get("/api/admin/anthropic-status")'
sse_block = '''@app.get("/api/admin/events")
async def admin_events(request: Request,
                       _role: str = Depends(require_mod_or_admin)):
    """Server-Sent Events stream for the admin queue. Each admin/moderator
    holds one connection; new submissions / status changes are pushed in
    real time so the queue updates without page refresh.

    Event types:
      - submission_new      → server appended a new pending submission
      - submission_updated  → status / title / fields changed
      - heartbeat           → comment frame every ~15s to keep proxies happy

    Client wires EventSource('/api/admin/events') and listens to the typed events.
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=64)
    async with _admin_events_lock:
        _admin_event_clients.add(queue)

    async def event_stream():
        try:
            yield "event: hello\\ndata: {\\"ok\\":true}\\n\\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    line = (
                        f"event: {payload['type']}\\n"
                        f"data: {json.dumps(payload['data'], ensure_ascii=False)}\\n\\n"
                    )
                    yield line
                except asyncio.TimeoutError:
                    yield ": heartbeat\\n\\n"
        finally:
            async with _admin_events_lock:
                _admin_event_clients.discard(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # disable nginx buffering
            "Connection": "keep-alive",
        },
    )


'''
assert anchor in src, 'anthropic-status anchor not found'
src = src.replace(anchor, sse_block + anchor, 1)

# ─── 4. Hook publishers ─────────────────────────────────────────

# (a) POST /api/submissions
old_post = '''        row = conn.execute("SELECT * FROM submissions WHERE id = ?", (sid,)).fetchone()
    return {"submission": submission_to_dict(row)}'''
new_post = '''        row = conn.execute("SELECT * FROM submissions WHERE id = ?", (sid,)).fetchone()
    sub_dict = submission_to_dict(row)
    publish_admin_event_sync('submission_new', sub_dict)
    return {"submission": sub_dict}'''
assert old_post in src, 'POST anchor not found'
src = src.replace(old_post, new_post, 1)

# (b) PATCH /api/submissions/{sid}
old_patch = '''    resp = {"submission": submission_to_dict(new_row)}
    if apply_result is not None:
        resp["auto_apply"] = apply_result
    return resp'''
new_patch = '''    sub_dict = submission_to_dict(new_row)
    publish_admin_event_sync('submission_updated', sub_dict)
    resp = {"submission": sub_dict}
    if apply_result is not None:
        resp["auto_apply"] = apply_result
    return resp'''
assert old_patch in src, 'PATCH anchor not found'
src = src.replace(old_patch, new_patch, 1)

# (c) apply-from-json (publishes the status flip to approved)
old_apply = '''    return {"created": True, "category_id": cat_id, "category": final}'''
new_apply = '''    # Notify admin clients that this submission moved to approved + a real category exists
    with db() as conn:
        new_row = conn.execute("SELECT * FROM submissions WHERE id = ?", (body.submission_id,)).fetchone()
    if new_row:
        publish_admin_event_sync('submission_updated', submission_to_dict(new_row))
    return {"created": True, "category_id": cat_id, "category": final}'''
assert old_apply in src, 'apply anchor not found'
src = src.replace(old_apply, new_apply, 1)

P.write_text(src, encoding='utf-8')
print('OK: imports + pub/sub + SSE endpoint + 3 publishers wired')
