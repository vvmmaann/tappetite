"""
Tappetite · backend API
FastAPI + SQLite + cookie session auth (HttpOnly + Secure + SameSite=Lax)

Endpoints:
  GET  /api/health              public ping
  POST /api/register            { nickname, email, password }
  POST /api/login               { email_or_nick, password }
  POST /api/logout
  GET  /api/me                  returns user or { user: null }
  POST /api/results             auth required, save tournament result
  GET  /api/results             auth required, list user's results
  POST /api/admin/login         { password } - dev-mode admin auth (legacy)
  GET  /api/admin/check         returns { is_admin: bool }
"""

from __future__ import annotations

import os
import re
import math
import random
import secrets
import sqlite3
import json
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import bcrypt
import subprocess
import html as html_module
import httpx
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from starlette.responses import StreamingResponse
import asyncio
from pydantic import BaseModel, EmailStr, Field, field_validator

# Anthropic SDK — optional. If not installed or no API key, ctx is left blank.
try:
    import anthropic  # type: ignore
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None  # type: ignore
    _ANTHROPIC_AVAILABLE = False

# Mailer (Resend transport) + bilingual email templates. Used by password
# reset flow (chunk 6), broadcast announcements, and any future verification
# / notification emails.
from mailer import send_email, EmailSendError
from email_templates import password_reset_email, broadcast_email

# AI portrait engine (B4: «Прочтение» AI-generated cross-category portraits).
# Reads ANTHROPIC_API_KEY from env at call time, so missing key only breaks
# portrait endpoints, not the rest of the app.
import portrait as portrait_mod

logger = logging.getLogger("upg.api")

# ─── CONFIG ─────────────────────────────────────────────────────

DB_PATH = Path(os.environ.get("UPG_DB_PATH", "/opt/untitled-pick-game-api/data/db.sqlite"))
# CANONICAL categories source-of-truth — production lives at this path on the
# server. Local copies in C:\...\taste_twins\api\categories.json (etc) are
# stale dev artifacts and must NOT be deployed. Always pull from this path
# before audit. Ad-hoc fix scripts (api/scripts/fix_*.py) target this path
# directly via SSH+exec, never local copies.
CATEGORIES_JSON_PATH = Path(os.environ.get("UPG_CATEGORIES_PATH", "/opt/untitled-pick-game-api/data/categories.json"))
COOKIE_NAME = "upg_session"
SESSION_TTL_DAYS = 30

# Admin cookie name. Bumping the version-suffix invalidates all existing
# admin/moderator sessions in one shot (forces everyone to re-login).
ADMIN_COOKIE_NAME = "upg_admin_v3"  # bumped v2→v3 to invalidate forged "ok" cookies (P0 hotfix 2026-05-08)
ADMIN_SESSION_TTL_DAYS = 7  # admin sessions live 7 days, then re-login required

# Admin master password — REQUIRED in production via /etc/untitled-pick-game-api.env.
# No fallback default: if the env var is missing, fail loudly at startup rather
# than silently accept a weak password.
ADMIN_PASS = os.environ.get("UPG_ADMIN_PASS")
if not ADMIN_PASS:
    raise RuntimeError(
        "UPG_ADMIN_PASS env var is required. Set it in /etc/untitled-pick-game-api.env "
        "(e.g. UPG_ADMIN_PASS=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))'))"
    )

# CSRF secret reserved for future cross-origin POST protection.
# Read once at startup so a future middleware can use it without restart.
CSRF_SECRET = os.environ.get("UPG_CSRF_SECRET")  # may be None until set; non-fatal for now
ANTHROPIC_MODEL = os.environ.get("UPG_ANTHROPIC_MODEL", "claude-opus-4-7")

# When set, every newly-registered user gets an asymmetric "follow" relationship
# from this account (admin sees them in friends; they don't see admin until
# they explicitly send a friend request, which then auto-mutualises).
# Set to empty string to disable.
AUTO_FRIEND_ADMIN_NICKNAME = os.environ.get("UPG_AUTO_FRIEND_NICKNAME", "Uncle")

# Latin-only nicknames (matches frontend regex). Cyrillic + other Unicode is
# rejected so display is consistent across all surfaces (URLs, share cards,
# legacy 7-bit systems). Existing rows in DB with non-Latin nicknames (mod1,
# mod2 placeholders) are unaffected — regex only runs on INSERT/UPDATE.
NICK_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")

# Social-auth (Sign in with Apple / Google) configuration. These are the
# OAuth client IDs the FRONTEND uses to obtain ID tokens — backend just
# validates the audience claim matches. Set via env vars in production.
# Placeholder defaults are empty strings which means "auth endpoint will
# return 503 social_not_configured" — flip on when provider setup is done.
GOOGLE_OAUTH_CLIENT_ID_WEB = os.environ.get("GOOGLE_OAUTH_CLIENT_ID_WEB", "")
GOOGLE_OAUTH_CLIENT_ID_ANDROID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID_ANDROID", "")
GOOGLE_OAUTH_CLIENT_ID_IOS = os.environ.get("GOOGLE_OAUTH_CLIENT_ID_IOS", "")
APPLE_BUNDLE_ID = os.environ.get("APPLE_BUNDLE_ID", "me.isverifiedby.pickgame")

# Web Push config (2026-05-11). Three env vars:
#   - UPG_VAPID_PRIVATE_PEM_PATH: filesystem path to the PEM private key
#     (root:upgapi, 0640). We do NOT inline the PEM in the env file because
#     env files get cat'd to logs/dumps; keeping it in a separate restricted
#     file is the cleaner secrets-hygiene pattern.
#   - UPG_VAPID_PUBLIC_KEY: URL-safe base64 (no padding) of the EC public
#     key. Same value is baked into the frontend as applicationServerKey
#     when calling pushManager.subscribe().
#   - UPG_VAPID_CLAIMS_SUB: contact identifier sent to push services; spec
#     requires mailto: or https: prefix. Push services may rate-limit or
#     contact us if our pushes misbehave.
# Empty values mean "push disabled" — the helper short-circuits and the
# endpoints return 503. Lets us deploy code before the env var is set.
VAPID_PRIVATE_PEM_PATH = os.environ.get("UPG_VAPID_PRIVATE_PEM_PATH", "")
VAPID_PUBLIC_KEY = os.environ.get("UPG_VAPID_PUBLIC_KEY", "")
VAPID_CLAIMS_SUB = os.environ.get("UPG_VAPID_CLAIMS_SUB", "mailto:hello@isverifiedby.me")

# Audit M5: /api/docs and the OpenAPI schema are gated behind UPG_API_DOCS=1.
# In prod (no env var set) they return 404, which keeps the full endpoint
# schema (including admin routes) out of casual-poking range. Set
# UPG_API_DOCS=1 in /etc/untitled-pick-game-api.env for a brief reading
# session, then unset.
_DOCS_ENABLED = os.environ.get("UPG_API_DOCS", "").lower() in ("1", "true", "yes")
app = FastAPI(
    title="Tappetite API",
    version="0.1.0",
    docs_url="/api/docs" if _DOCS_ENABLED else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if _DOCS_ENABLED else None,
)


# ─── ORIGIN-CHECK MIDDLEWARE (audit-6 M3) ──────────────────────────
# Defence-in-depth against CSRF. Cookies are SameSite=Lax (which already
# blocks most cross-site POST scenarios) and we don't enable CORS at all
# (so cross-origin fetch with credentials fails preflight). But this
# middleware adds an explicit Origin/Referer check on unsafe HTTP methods
# so any future config drift (someone adding a permissive CORS later) is
# safely backstopped.
# Allowed origins: our own domain + www subdomain. App requests from
# Capacitor WebView use scheme `capacitor://` or `https://localhost` —
# allowed because they come from the bundled HTML which is part of our
# trust boundary.
_TRUSTED_ORIGINS = {
    "https://isverifiedby.me",
    "https://www.isverifiedby.me",
    "capacitor://localhost",            # iOS Capacitor
    "http://localhost",                 # Android Capacitor (server.url loads from https but local fetches sometimes scheme-mixed)
    "https://localhost",
}
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def origin_check_middleware(request: Request, call_next):
    if request.method in _UNSAFE_METHODS and request.url.path.startswith("/api/"):
        origin = request.headers.get("origin")
        referer = request.headers.get("referer")
        # If neither header is set, allow (some legitimate non-browser clients
        # don't send Origin — e.g. mobile native fetch). If either is set,
        # it must point to a trusted origin.
        if origin and origin not in _TRUSTED_ORIGINS:
            from fastapi.responses import JSONResponse
            logger.warning("origin_blocked path=%s origin=%s ip=%s",
                           request.url.path, origin, _client_ip(request))
            return JSONResponse(status_code=403, content={"detail": "untrusted_origin"})
        if not origin and referer:
            # Compare scheme+host of Referer against trusted origins
            from urllib.parse import urlparse
            try:
                p = urlparse(referer)
                ref_origin = f"{p.scheme}://{p.netloc}"
                if ref_origin not in _TRUSTED_ORIGINS:
                    from fastapi.responses import JSONResponse
                    logger.warning("referer_blocked path=%s referer=%s ip=%s",
                                   request.url.path, ref_origin, _client_ip(request))
                    return JSONResponse(status_code=403, content={"detail": "untrusted_referer"})
            except Exception:
                pass
        # Audit-11 Low: log requests with neither Origin NOR Referer on
        # unsafe methods. Legitimate native (Capacitor) requests look like
        # this, but so does the rare scripted attacker. We allow these
        # through (mobile compat) but emit a warning so unusual patterns
        # are visible in logs without blocking real users.
        if not origin and not referer:
            logger.info("origin_referer_absent method=%s path=%s ua=%s ip=%s",
                        request.method, request.url.path,
                        (request.headers.get("user-agent") or "")[:120],
                        _client_ip(request))
    return await call_next(request)


# ─── ADMIN REAL-TIME EVENTS (SSE) ─────────────────────────────────
# In-process pub/sub for the admin queue. Each connected admin/moderator gets
# their own asyncio.Queue; publish_admin_event broadcasts to all of them.
# Single-process safe by design (uvicorn --workers 1).
_admin_event_clients: "set[asyncio.Queue]" = set()
_admin_events_lock = asyncio.Lock()
# Captured at app startup so sync endpoints (running in a thread pool) can
# schedule coroutines onto the main uvicorn event loop via run_coroutine_threadsafe.
_main_loop: "asyncio.AbstractEventLoop | None" = None

@app.on_event("startup")
async def _capture_main_loop() -> None:
    global _main_loop
    _main_loop = asyncio.get_running_loop()

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
    main uvicorn loop via run_coroutine_threadsafe so it works from FastAPI's
    sync handlers (which run in a thread pool, not on the loop)."""
    if _main_loop is None or not _main_loop.is_running():
        return  # loop not yet up (or torn down)
    try:
        asyncio.run_coroutine_threadsafe(publish_admin_event(event_type, data), _main_loop)
    except RuntimeError:
        pass



# ─── DB BOOTSTRAP ───────────────────────────────────────────────

def db_init() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript("""
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                nickname TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT,
                avatar_glyph TEXT DEFAULT '✦',
                created_at TEXT NOT NULL,
                last_login_at TEXT,
                is_admin INTEGER DEFAULT 0,
                role TEXT DEFAULT 'user',
                email_verified INTEGER DEFAULT 0,
                is_paid INTEGER DEFAULT 0,
                wallet_address TEXT,
                social_providers TEXT DEFAULT '[]',
                badges TEXT DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                last_seen_at TEXT,
                ip TEXT,
                user_agent TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

            -- Password reset tokens. Store SHA256 hash, never the raw token,
            -- so even if DB leaks the tokens can't be reused. Single-use
            -- (used_at column), 1h expiry. Cascade delete with user.
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                request_ip TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id);
            CREATE INDEX IF NOT EXISTS idx_password_resets_expires ON password_resets(expires_at);

            -- GDPR / KZ-PD explicit-consent audit log. Every time a user
            -- explicitly accepts our privacy/terms (registration, re-accept
            -- after policy bump, etc), we INSERT a row here with version +
            -- timestamp + IP + UA. Lets us prove in court "Ivanov accepted
            -- version X on date Y from IP Z" if ever challenged.
            -- Multiple rows per user are expected (one per acceptance event).
            CREATE TABLE IF NOT EXISTS consent_acceptances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                consent_version TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'registration',
                accepted_at TEXT NOT NULL,
                ip TEXT,
                user_agent TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_consent_user ON consent_acceptances(user_id);
            CREATE INDEX IF NOT EXISTS idx_consent_version ON consent_acceptances(consent_version);

            -- CURRENT consent state per user, per category. Optimized for fast
            -- read on every request that needs to check "is this user opted in
            -- to email marketing?" — vs scanning the audit log.
            -- Categories:
            --   'core' — mandatory, granted at registration. Covers all
            --       processing necessary for the service to function:
            --       account, results, friends, anonymized analytics,
            --       improvement of recommendations, transfers in M&A,
            --       processors disclosed in privacy.html (PostHog, Resend,
            --       Google, Apple).
            --   'email_marketing' — optional, opt-in only. Newsletters,
            --       product updates, occasional promo. Required separately
            --       under EU ePrivacy / CAN-SPAM.
            --   'push_marketing'  — optional, opt-in only. Mobile push
            --       notifications for engagement (not transactional).
            -- The audit log (consent_acceptances) records every change so
            -- we can prove what was granted/revoked and when.
            CREATE TABLE IF NOT EXISTS consent_state (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                is_granted INTEGER NOT NULL DEFAULT 0,
                last_changed_at TEXT NOT NULL,
                consent_version TEXT NOT NULL,
                PRIMARY KEY (user_id, category)
            );
            CREATE INDEX IF NOT EXISTS idx_consent_state_user ON consent_state(user_id);

            -- Social identities (Sign in with Apple, Sign in with Google).
            -- One user CAN have multiple identities (link Apple + Google to
            -- same account). One provider+provider_user_id pair maps to
            -- exactly ONE user (UNIQUE). Fast lookup on signin: query by
            -- (provider, provider_user_id) returns user_id in O(1).
            CREATE TABLE IF NOT EXISTS social_identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                email TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(provider, provider_user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_social_user ON social_identities(user_id);

            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                category_id TEXT NOT NULL,
                category_name TEXT,
                top1_id TEXT,
                top1_name TEXT,
                top2_id TEXT,
                top2_name TEXT,
                top3_id TEXT,
                top3_name TEXT,
                archetype_name TEXT,
                archetype_body TEXT,
                battles_played INTEGER DEFAULT 0,
                duration_sec INTEGER DEFAULT 0,
                completed_at TEXT NOT NULL,
                is_public INTEGER DEFAULT 1,
                public_slug TEXT,
                shared_count INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_results_user ON results(user_id, completed_at DESC);
            CREATE INDEX IF NOT EXISTS idx_results_category ON results(category_id);

            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id INTEGER REFERENCES users(id),
                action TEXT NOT NULL,
                target TEXT,
                extras_json TEXT,
                at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_admin_actions_at ON admin_actions(at DESC);

            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                friend_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                status TEXT NOT NULL DEFAULT 'pending',  -- pending | accepted | blocked
                created_at TEXT NOT NULL,
                responded_at TEXT,
                UNIQUE(user_id, friend_user_id)
            );
            CREATE INDEX IF NOT EXISTS idx_friendships_user_status ON friendships(user_id, status);
            CREATE INDEX IF NOT EXISTS idx_friendships_friend_status ON friendships(friend_user_id, status);

            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                type TEXT NOT NULL,                  -- 'category' | 'item'
                status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected | needs_review
                title TEXT NOT NULL,
                description TEXT,
                cluster TEXT,
                target_category_id TEXT,             -- for type='item'
                examples_json TEXT,                  -- for type='category' (JSON array)
                ai_check_json TEXT,                  -- placeholder for AI moderation report
                submitted_at TEXT NOT NULL,
                decided_at TEXT,
                decided_by INTEGER REFERENCES users(id),
                decision_note TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_subs_status_at ON submissions(status, submitted_at DESC);
            CREATE INDEX IF NOT EXISTS idx_subs_user ON submissions(user_id);

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


            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                achievement_id TEXT NOT NULL,
                unlocked_at TEXT NOT NULL,
                progress_int INTEGER DEFAULT NULL,
                UNIQUE(user_id, achievement_id)
            );
            CREATE INDEX IF NOT EXISTS idx_ach_user ON user_achievements(user_id);

            -- Short URL store: challenges(slug → payload)
            -- Slug is a 7-8 char URL-safe token (token_urlsafe(5)).
            -- payload_json stores the same shape as the legacy #c= hash.
            -- by_user_id nullable: guests can also shorten.
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL,
                by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_challenges_slug ON challenges(slug);
            CREATE INDEX IF NOT EXISTS idx_challenges_user ON challenges(by_user_id, created_at DESC);

            -- General-purpose feedback channel. Replaces the old "suggest a variant"
            -- form which was too noisy. Users send free text + optional category;
            -- admin reads, triages, marks status. Auth optional (anonymous OK).
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                type TEXT NOT NULL,                       -- 'theme_idea' | 'item_idea' | 'bug' | 'other'
                text TEXT NOT NULL,
                email_for_reply TEXT,
                status TEXT NOT NULL DEFAULT 'new',       -- 'new' | 'read' | 'done' | 'archived'
                created_at TEXT NOT NULL,
                decided_at TEXT,
                decided_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                decision_note TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_feedback_status_at ON feedback(status, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id, created_at DESC);

            -- Admin/moderator session tokens. Replaces the legacy literal cookie
            -- ('ok' for master, 'mod:<uid>' for named) which was forgeable: anyone
            -- could send Cookie: upg_admin_v2=ok and become admin (P0 fixed 2026-05-08).
            -- Now: each successful admin login creates a row with a random token;
            -- the cookie value IS the token. require_admin/require_mod_or_admin
            -- look up the token in this table.
            -- user_id is NULL for master-password sessions (legacy bootstrap path).
            CREATE TABLE IF NOT EXISTS admin_sessions (
                token TEXT PRIMARY KEY,
                role TEXT NOT NULL,                       -- 'admin' or 'moderator'
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                ip TEXT,
                user_agent TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_admin_sess_expires ON admin_sessions(expires_at);
            CREATE INDEX IF NOT EXISTS idx_admin_sess_user ON admin_sessions(user_id);

            -- AI-generated cross-category portraits for the «Прочтение» section.
            -- Schema is multi-scope ready: phase 1 only stores scope_kind='global',
            -- later phases add 'cluster'/'pair'/'group' without migration.
            -- participant_ids is a JSON array of user ids (solo = [uid], pair = [u1, u2]).
            -- tournaments_at_gen is used for the activity-gate (button stays disabled
            -- until user plays at least one more tournament after their last portrait).
            -- credits_spent = 0 for free generations; >0 reserved for wallet-paid path
            -- in Phase 2 (no wallet logic in Phase 1).
            CREATE TABLE IF NOT EXISTS user_portraits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope_kind TEXT NOT NULL DEFAULT 'global',
                scope_key TEXT,
                participant_ids TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                tournaments_at_gen INTEGER NOT NULL,
                content_md TEXT NOT NULL,
                lang TEXT NOT NULL,
                is_public INTEGER DEFAULT 0,
                public_slug TEXT UNIQUE,
                model_used TEXT,
                credits_spent INTEGER DEFAULT 0,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_portraits_lookup
                ON user_portraits(participant_ids, scope_kind, scope_key, generated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_portraits_slug ON user_portraits(public_slug);

            -- Append-only audit of every Anthropic API call. Decoupled from
            -- user_portraits: if a portrait gets deleted/replaced, the spend
            -- record stays here. This is the authoritative source for the
            -- admin spend banner — never read costs from user_portraits.
            -- `kind` field reserved for future call types (pair, group,
            -- cluster portraits, ad-hoc rewrites).
            CREATE TABLE IF NOT EXISTS anthropic_spend_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                occurred_at TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'portrait_global',
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                ref_portrait_id INTEGER,
                model_used TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0,
                notes TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_ledger_at ON anthropic_spend_ledger(occurred_at DESC);
            CREATE INDEX IF NOT EXISTS idx_ledger_user ON anthropic_spend_ledger(user_id, occurred_at DESC);

            -- Generic key/value app settings (2026-05-28). First use: the
            -- "new registrations since baseline" topbar counter stores its
            -- baseline timestamp here so the count survives browser/device
            -- changes and is a single source of truth across admin sessions.
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            );
        """)
        conn.commit()
        # Idempotent migrations for new columns added later (SQLite ≥3.35 supports IF NOT EXISTS)
        for ddl in [
            "ALTER TABLE results ADD COLUMN items_count INTEGER DEFAULT NULL",
            "ALTER TABLE users ADD COLUMN submissions_unlimited INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN last_approval_seen_at TEXT DEFAULT NULL",
            "ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL REFERENCES users(id)",
            "ALTER TABLE results ADD COLUMN client_id TEXT DEFAULT NULL",
            # Audit-11 P2.c: provenance marker for archetype_name/body. Values:
            #   'client' — archetype computed by frontend engine, server stored
            #             as-is (current state — script-able, low integrity).
            #   'server' — archetype recomputed server-side from validated
            #             top picks (future state when engine is ported to
            #             Python). Allows analytics/admin to filter trustable
            #             rows from spoofable ones.
            "ALTER TABLE results ADD COLUMN archetype_source TEXT DEFAULT 'client'",
            # Admin/owner override: bypass the 1-portrait-per-week cooldown and
            # the activity-gate. Set to 1 manually for owner accounts; default 0.
            # Once wallet/credits land in Phase 2, this column may become
            # "unlimited credits" semantics.
            "ALTER TABLE users ADD COLUMN portrait_unlimited INTEGER DEFAULT 0",
            # Optional gender field. Values: NULL (unknown), 'male', 'female'.
            # Used by portrait generation to instruct AI on past-tense + short
            # adjective forms in Russian. If NULL, prompt falls back to strict
            # gender-neutral instructions (which Haiku tends to slip on).
            "ALTER TABLE users ADD COLUMN gender TEXT DEFAULT NULL",
            # Admin god-mode (2026-05-11): allow attribution override for
            # submissions. The original `user_id` column stays as the audit
            # trail of who actually submitted the form; `attributed_user_id`
            # is what gets DISPLAYED ("from @lmya"). Use case: a friend tells
            # the admin about a theme idea face-to-face — admin enters the
            # submission themselves, then attributes it to the friend so the
            # public credit is correct. NULL = no override, fall back to
            # original user_id.
            "ALTER TABLE submissions ADD COLUMN attributed_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL DEFAULT NULL",
            # Streaks (2026-05-11): track which calendar days a user opened
            # the app on, so we can compute consecutive-day visit streaks +
            # award achievements ("неделя", "месяц"). Dates are stored as
            # ISO strings in a fixed timezone (Asia/Almaty / UTC+5) — see
            # _streak_today() for the rationale. Future: per-user TZ from
            # push subscription. CREATE TABLE IF NOT EXISTS runs idempotently.
            (
                "CREATE TABLE IF NOT EXISTS user_daily_visits ("
                "  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,"
                "  visit_date TEXT NOT NULL,"
                "  PRIMARY KEY (user_id, visit_date)"
                ")"
            ),
            "CREATE INDEX IF NOT EXISTS idx_udv_user_date ON user_daily_visits(user_id, visit_date DESC)",
            # Web Push subscriptions (2026-05-11). One row per (user, device).
            # endpoint is unique — same browser re-subscribing replaces the row
            # via ON CONFLICT clause in the insert. p256dh + auth are part of
            # the subscription payload (browser-generated keys used to encrypt
            # the push body so only the user's device can decrypt). user_agent
            # is informational — admin can see "iPhone Safari" vs "Chrome
            # Desktop" when debugging delivery. last_delivery_at / last_error
            # are populated by the send helper for observability.
            (
                "CREATE TABLE IF NOT EXISTS push_subscriptions ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,"
                "  endpoint TEXT NOT NULL UNIQUE,"
                "  p256dh TEXT NOT NULL,"
                "  auth TEXT NOT NULL,"
                "  user_agent TEXT,"
                "  created_at TEXT NOT NULL,"
                "  last_delivery_at TEXT,"
                "  last_error TEXT,"
                "  failure_count INTEGER DEFAULT 0"
                ")"
            ),
            "CREATE INDEX IF NOT EXISTS idx_push_user ON push_subscriptions(user_id)",
            # Native FCM tokens (2026-05-12). Separate from push_subscriptions
            # because the delivery mechanism is completely different:
            #   - push_subscriptions: web browser, delivered via pywebpush+VAPID
            #     to {endpoint, p256dh, auth} triple
            #   - push_fcm_tokens: Capacitor on Android/iOS, delivered via
            #     Firebase Admin SDK to a single FCM `token` string
            # Same user can have BOTH (web browser + phone app) → we send to
            # both in the notification fanout loop.
            # UNIQUE(token) so re-registering the same token on the same app
            # just bumps last_seen_at and doesn't insert a duplicate.
            (
                "CREATE TABLE IF NOT EXISTS push_fcm_tokens ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,"
                "  token TEXT NOT NULL UNIQUE,"
                "  platform TEXT NOT NULL,"
                "  created_at TEXT NOT NULL,"
                "  last_seen_at TEXT NOT NULL,"
                "  last_delivery_at TEXT,"
                "  last_error TEXT,"
                "  failure_count INTEGER DEFAULT 0"
                ")"
            ),
            "CREATE INDEX IF NOT EXISTS idx_fcm_user ON push_fcm_tokens(user_id)",
            # Tournament votes (2026-05-12). Users can like/dislike a turnir
            # after completing it. UNIQUE(user_id, category_id) guarantees one
            # vote per user per turnir; re-voting via INSERT OR REPLACE updates
            # in place. vote = +1 (like) | -1 (dislike). Index on category_id
            # for fast count aggregation when rendering tile badges.
            (
                "CREATE TABLE IF NOT EXISTS tournament_votes ("
                "  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,"
                "  category_id TEXT NOT NULL,"
                "  vote INTEGER NOT NULL CHECK (vote IN (-1, 1)),"
                "  voted_at TEXT NOT NULL,"
                "  PRIMARY KEY (user_id, category_id)"
                ")"
            ),
            "CREATE INDEX IF NOT EXISTS idx_tvotes_cat ON tournament_votes(category_id, vote)",
            # ─── FAVORITES (added 2026-05-16) ────────────────────────
            # User-selected favorite CLUSTERS. Show their categories at top
            # of home in a dedicated "Тебе ближе" section. User picks 1-10
            # clusters at the popup that fires after their first tournament,
            # editable later from profile. The dismiss tracking is needed
            # because the popup re-shows after 5 tournaments if the user
            # dismissed without picking (per product decision 2026-05-16) —
            # we compute "tournaments since dismissal" on the frontend by
            # counting result rows with completed_at > favorites_dismissed_at.
            "ALTER TABLE users ADD COLUMN favorites_dismissed_at TEXT DEFAULT NULL",
            (
                "CREATE TABLE IF NOT EXISTS user_favorite_clusters ("
                "  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,"
                "  cluster_name TEXT NOT NULL,"
                "  set_at TEXT NOT NULL,"
                "  PRIMARY KEY (user_id, cluster_name)"
                ")"
            ),
            "CREATE INDEX IF NOT EXISTS idx_ufc_user ON user_favorite_clusters(user_id)",
        ]:
            try:
                conn.execute(ddl)
                conn.commit()
            except sqlite3.OperationalError:
                pass  # column already exists
        # Idempotent partial-unique index for results dedup by (user_id, client_id).
        # NULL client_id allows multiple legacy rows; new rows always send client_id.
        try:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_results_user_clientid "
                "ON results(user_id, client_id) WHERE client_id IS NOT NULL"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Audit re-review H-1: backfill 'core' consent_state for users that
        # registered before this table existed. They DO have a row in
        # consent_acceptances (audit log) from registration, but no current-
        # state row, which would make /api/me/consents report them as
        # un-consented (wrong + scary in profile UI). Idempotent INSERT OR
        # IGNORE picks the EARLIEST acceptance timestamp as last_changed_at;
        # version 'legacy' marks the rows as backfilled rather than freshly
        # accepted. Runs once per boot; cheap on small user counts.
        try:
            conn.execute(
                "INSERT OR IGNORE INTO consent_state "
                "(user_id, category, is_granted, last_changed_at, consent_version) "
                "SELECT u.id, 'core', 1, "
                "       COALESCE("
                "         (SELECT MIN(accepted_at) FROM consent_acceptances WHERE user_id = u.id), "
                "         u.created_at"
                "       ), "
                "       'legacy' "
                "FROM users u"
            )
            conn.commit()
        except sqlite3.OperationalError as e:
            logger.warning("consent_state backfill skipped: %s", e)


@contextmanager
def db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


# ─── HELPERS ────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ─── APP SETTINGS (key/value) ──────────────────────────────────────
def get_setting(key: str, default: str | None = None) -> str | None:
    """Read a value from app_settings. Returns `default` if the key is absent."""
    with db() as conn:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    """Upsert a value into app_settings."""
    with db() as conn:
        conn.execute(
            "INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (key, value, now_iso()),
        )


def get_registrations_baseline() -> str:
    """Baseline timestamp for the "new registrations" counter. Seeded to NOW
    the first time it's read so the counter starts at 0 (excludes all users
    that already existed when the counter was introduced)."""
    ts = get_setting("registrations_baseline_ts")
    if not ts:
        ts = now_iso()
        set_setting("registrations_baseline_ts", ts)
    return ts


# ─── STREAKS (2026-05-11) ──────────────────────────────────────────
# Visit-streak = how many consecutive days the user opened the app, counting
# back from today. Used for achievements ("неделя", "месяц") and (later) for
# "streak at risk" push notifications.
#
# TIMEZONE NOTE: streaks reset at MIDNIGHT in Asia/Almaty (UTC+5). We chose
# this single global offset for MVP because:
#   - vast majority of current users are in Almaty/Astana
#   - tracking per-user TZ adds schema + invalidation complexity not worth
#     the marginal correctness gain
#   - users in distant TZs (e.g. EU/-5h or US/-10h) get a slightly skewed
#     streak boundary, but the streak still increments daily — only the
#     "midnight reset" wall-clock time shifts
# When we add push notifications and start collecting user TZ from the
# Intl.DateTimeFormat() at subscribe time, we'll re-evaluate.
STREAK_TZ_OFFSET_HOURS = 5  # Asia/Almaty


def _streak_today() -> str:
    """Return today's date (YYYY-MM-DD) in the streak timezone. ALL streak
    arithmetic — recording visits, comparing for consecutive days, achievement
    triggers — must use this function so dates align across all callers."""
    now_local = datetime.now(timezone.utc) + timedelta(hours=STREAK_TZ_OFFSET_HOURS)
    return now_local.date().isoformat()


def _record_visit(conn: sqlite3.Connection, user_id: int) -> None:
    """Mark today as visited for this user. INSERT OR IGNORE so multiple
    requests in the same day are no-ops (per-day uniqueness). Called from
    any authenticated entry point that means "user is using the app today"
    — concretely from /api/me which fires on every app boot."""
    try:
        conn.execute(
            "INSERT OR IGNORE INTO user_daily_visits (user_id, visit_date) VALUES (?, ?)",
            (user_id, _streak_today()),
        )
    except sqlite3.OperationalError:
        # Table missing on a stale schema — fail silently, will retry next request
        pass


def _consecutive_streak(dates: list[str]) -> int:
    """Given a DESC-ordered list of ISO dates, return the count of consecutive
    days ending at today (or yesterday). A gap of 2+ days breaks the streak.
    Yesterday counts as "still alive today" so users who haven't opened the
    app yet today don't see their streak drop to 0 until tomorrow."""
    if not dates:
        return 0
    today = datetime.fromisoformat(_streak_today()).date()
    yesterday = today - timedelta(days=1)
    parsed = [datetime.fromisoformat(d).date() for d in dates]
    # Streak still alive only if most recent date is today or yesterday.
    if parsed[0] != today and parsed[0] != yesterday:
        return 0
    streak = 1
    for i in range(1, len(parsed)):
        if parsed[i - 1] - parsed[i] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def compute_visit_streak(conn: sqlite3.Connection, user_id: int) -> int:
    """Current visit-streak (consecutive days ending today/yesterday)."""
    rows = conn.execute(
        "SELECT visit_date FROM user_daily_visits "
        "WHERE user_id = ? ORDER BY visit_date DESC LIMIT 400",
        (user_id,),
    ).fetchall()
    return _consecutive_streak([r["visit_date"] for r in rows])


def compute_play_streak(conn: sqlite3.Connection, user_id: int) -> int:
    """Current play-streak (consecutive days ending today/yesterday where
    the user completed at least one tournament). Derived from results table;
    no separate tracking needed."""
    rows = conn.execute(
        "SELECT DISTINCT substr(completed_at, 1, 10) AS played_date "
        "FROM results WHERE user_id = ? "
        "ORDER BY played_date DESC LIMIT 400",
        (user_id,),
    ).fetchall()
    # NB: completed_at is stored UTC, not Almaty-local. For MVP we accept
    # this ~5h skew — play_streak may undercount in edge cases (user playing
    # at 01:00 Almaty = previous-day UTC date). Visit-streak uses Almaty TZ
    # so they may briefly disagree by a day; ok for MVP.
    return _consecutive_streak([r["played_date"] for r in rows])


def compute_total_visit_days(conn: sqlite3.Connection, user_id: int) -> int:
    """Lifetime total of unique days the user visited (not just consecutive)."""
    row = conn.execute(
        "SELECT COUNT(*) FROM user_daily_visits WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return int(row[0]) if row else 0


# ─── WEB PUSH (2026-05-11) ─────────────────────────────────────────
# We deliver browser push via pywebpush. The flow:
#   1. Frontend asks Notification.requestPermission(), then calls
#      pushManager.subscribe({applicationServerKey: VAPID_PUBLIC_KEY,
#                              userVisibleOnly: true})
#   2. Browser returns a PushSubscription object with endpoint + keys.p256dh
#      + keys.auth. Frontend POSTs that to /api/push/subscribe.
#   3. When backend wants to send a push, it loads the subscription rows
#      for the user and calls send_push(sub, payload) per row.
#   4. pywebpush builds the VAPID JWT signature + AES-GCM-encrypts the
#      payload with the user's keys and POSTs to the endpoint (FCM/Mozilla/
#      Apple/etc — whichever push service the user's browser uses).
#
# Common errors handled here:
#   - 404/410 Gone from push service → subscription is dead, mark + delete
#   - 401/403 → VAPID key mismatch (likely env misconfig)
#   - 429 → rate-limited, retry later (we log + skip)
#
# Helper is sync because pywebpush is sync. For high-volume sends we'd
# need an async wrapper or worker queue; for current scale (tens of pushes
# per request) inline is fine.
_push_module = None
def _get_push_module():
    """Lazy-load pywebpush so the API still starts if the package isn't
    installed yet (e.g. fresh deploy where requirements.txt updated but
    pip install hasn't run). Returns the module or None."""
    global _push_module
    if _push_module is False:
        return None
    if _push_module is not None:
        return _push_module
    try:
        from pywebpush import webpush, WebPushException  # type: ignore
        _push_module = type("_PushMod", (), {
            "webpush": staticmethod(webpush),
            "WebPushException": WebPushException,
        })
        return _push_module
    except ImportError:
        logger.warning("pywebpush not installed — push delivery disabled")
        _push_module = False  # type: ignore
        return None


def _load_vapid_private_key() -> str | None:
    """Read the PEM private key from disk. Cached after first read since
    the file rarely changes. Returns None if config is incomplete (caller
    should treat as 'push disabled')."""
    if not VAPID_PRIVATE_PEM_PATH:
        return None
    try:
        with open(VAPID_PRIVATE_PEM_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error("Failed to read VAPID PEM at %s: %s", VAPID_PRIVATE_PEM_PATH, e)
        return None


_vapid_private_pem_cache: str | None = None
def _vapid_private_pem() -> str | None:
    global _vapid_private_pem_cache
    if _vapid_private_pem_cache is None:
        _vapid_private_pem_cache = _load_vapid_private_key() or ""
    return _vapid_private_pem_cache or None


def push_is_configured() -> bool:
    """True iff all VAPID env vars are populated AND pywebpush is importable.
    Used by /api/push/status to tell the frontend whether to even offer
    the 'enable notifications' UI."""
    return (
        bool(VAPID_PUBLIC_KEY)
        and bool(_vapid_private_pem())
        and _get_push_module() is not None
    )


def send_push_to_subscription(sub_row: dict, payload: dict) -> tuple[bool, str | None]:
    """Send one push to one subscription. Returns (ok, error_code).
    Caller is responsible for marking dead subscriptions; we just report
    what happened. Payload should be a small dict (we serialize to JSON).
    Browser-side service worker receives the data via event.data.json()."""
    mod = _get_push_module()
    pem = _vapid_private_pem()
    if not mod or not pem or not VAPID_PUBLIC_KEY:
        return (False, "push_not_configured")

    subscription_info = {
        "endpoint": sub_row["endpoint"],
        "keys": {
            "p256dh": sub_row["p256dh"],
            "auth": sub_row["auth"],
        },
    }
    try:
        mod.webpush(  # type: ignore[attr-defined]
            subscription_info=subscription_info,
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=pem,
            vapid_claims={"sub": VAPID_CLAIMS_SUB},
            timeout=10,
        )
        return (True, None)
    except mod.WebPushException as e:  # type: ignore[attr-defined]
        status = getattr(e.response, "status_code", None) if e.response else None
        if status in (404, 410):
            # Subscription expired / unsubscribed by user / browser uninstalled.
            return (False, f"gone_{status}")
        if status == 413:
            return (False, "payload_too_large")
        return (False, f"http_{status}" if status else f"err:{str(e)[:120]}")
    except Exception as e:
        return (False, f"unexpected:{str(e)[:120]}")


def send_push_web_to_user(user_id: int, payload: dict, ttl: int = 86400) -> dict:
    """Web-channel only. Used internally by the unified send_push_to_user
    below. Looks up all push subscriptions for `user_id` and sends `payload`
    to each. Dead subscriptions (404/410) are deleted from DB so subsequent
    sends don't waste time on them. Returns {sent, failed, deleted}."""
    sent = 0
    failed = 0
    deleted = 0
    with db() as conn:
        rows = conn.execute(
            "SELECT id, endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        for r in rows:
            ok, err = send_push_to_subscription(dict(r), payload)
            now = now_iso()
            if ok:
                sent += 1
                conn.execute(
                    "UPDATE push_subscriptions SET last_delivery_at = ?, last_error = NULL, "
                    "failure_count = 0 WHERE id = ?",
                    (now, r["id"]),
                )
            else:
                failed += 1
                # Permanent failures (browser unsubscribed) → delete the row.
                # Transient errors (timeout, 429) → bump failure_count; we
                # don't auto-delete since the subscription might come back.
                if err and err.startswith("gone_"):
                    conn.execute("DELETE FROM push_subscriptions WHERE id = ?", (r["id"],))
                    deleted += 1
                else:
                    conn.execute(
                        "UPDATE push_subscriptions SET last_error = ?, last_delivery_at = ?, "
                        "failure_count = failure_count + 1 WHERE id = ?",
                        (err, now, r["id"]),
                    )
    return {"sent": sent, "failed": failed, "deleted": deleted}


# ─── NATIVE PUSH via FCM (2026-05-12) ──────────────────────────────
# Web Push doesn't work inside Capacitor WebView (no Service Worker, no
# Notification API in WebView). For mobile-app users we deliver via FCM
# using the firebase-admin SDK. Same fanout pattern as web push above —
# look up tokens, send to each, mark dead ones for deletion.
#
# Setup on the server:
#   1. pip install firebase-admin
#   2. Generate service-account JSON in Firebase Console → Project Settings
#      → Service Accounts → "Generate new private key"
#   3. Set FIREBASE_CREDENTIALS env var to the JSON path

FIREBASE_CREDENTIALS_PATH = os.environ.get("FIREBASE_CREDENTIALS", "")
_fcm_app = None         # cached firebase_admin.App after first init
_fcm_messaging = None   # cached firebase_admin.messaging module
_fcm_load_failed = False  # True once we've tried + failed (don't retry per request)


def _get_fcm_module():
    """Lazy-init firebase-admin. Returns (app, messaging) tuple or (None, None)
    if either firebase-admin isn't installed OR FIREBASE_CREDENTIALS not set/
    invalid. Cached so we only pay the import + cert parse once per process."""
    global _fcm_app, _fcm_messaging, _fcm_load_failed
    if _fcm_load_failed:
        return (None, None)
    if _fcm_app is not None and _fcm_messaging is not None:
        return (_fcm_app, _fcm_messaging)
    if not FIREBASE_CREDENTIALS_PATH:
        _fcm_load_failed = True
        logger.warning("FIREBASE_CREDENTIALS not set — FCM push delivery disabled")
        return (None, None)
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        # initialize_app raises if already initialized — guard with try.
        try:
            _fcm_app = firebase_admin.initialize_app(cred)
        except ValueError:
            _fcm_app = firebase_admin.get_app()
        _fcm_messaging = messaging
        logger.info("firebase-admin initialized for FCM delivery")
        return (_fcm_app, _fcm_messaging)
    except ImportError:
        logger.warning("firebase-admin not installed — FCM push delivery disabled")
        _fcm_load_failed = True
        return (None, None)
    except Exception as e:
        logger.error("firebase-admin init failed: %s", e)
        _fcm_load_failed = True
        return (None, None)


def fcm_is_configured() -> bool:
    """True iff firebase-admin loaded AND credentials valid. Used to gate
    UI elements that depend on native push availability."""
    app, msg = _get_fcm_module()
    return bool(app and msg)


def send_fcm_to_token(token: str, payload: dict) -> tuple[bool, str | None]:
    """Send one push to one FCM token. Payload conventions (mirrors web push):
      - title:  short heading shown in notification (defaults to "Tappetite")
      - body:   one-line message text
      - url:    deep-link path to open on tap (e.g. "/c/abc" or full URL)
      - tag:    optional dedup key (multiple notifications with same tag stack)
    Returns (ok, error_code). Caller marks dead tokens via the error.
    Permanent errors (token invalid/unregistered) → error starts with 'gone_'."""
    app, messaging = _get_fcm_module()
    if not app or not messaging:
        return (False, "fcm_not_configured")

    title = str(payload.get("title") or "Tappetite")
    body = str(payload.get("body") or "")
    # All non-notification fields go into `data` (string values only — FCM
    # validates types here). Frontend tap-handler reads action.notification.data
    # to figure out where to navigate.
    data = {k: str(v) for k, v in payload.items() if k not in ("title", "body") and v is not None}

    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data,
            token=token,
            # Android-specific options: high priority + show in notification tray
            # even when app is backgrounded (default behaviour for FCM v1).
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body,
                    # Tag for dedup — FCM passes this through to Android NotificationManager
                    tag=str(payload.get("tag") or "tappetite"),
                ),
            ),
        )
        # send() returns the FCM message id (string); we don't store it.
        messaging.send(message)
        return (True, None)
    except Exception as e:
        # firebase-admin raises specific exceptions for different failures.
        # The class name reveals the category — we map permanent failures to
        # 'gone_*' so the caller knows to delete the token row.
        cls = type(e).__name__
        if cls in ("UnregisteredError", "InvalidArgumentError", "SenderIdMismatchError"):
            return (False, f"gone_{cls}")
        return (False, f"err:{cls}:{str(e)[:120]}")


def send_fcm_to_user(user_id: int, payload: dict) -> dict:
    """Fan out FCM push to all of `user_id`'s registered native tokens.
    Mirror of send_push_to_user — same {sent, failed, deleted} return shape
    so callers can use them interchangeably or combine results."""
    if not fcm_is_configured():
        return {"sent": 0, "failed": 0, "deleted": 0}
    sent = 0
    failed = 0
    deleted = 0
    with db() as conn:
        rows = conn.execute(
            "SELECT id, token FROM push_fcm_tokens WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        for r in rows:
            ok, err = send_fcm_to_token(r["token"], payload)
            now = now_iso()
            if ok:
                sent += 1
                conn.execute(
                    "UPDATE push_fcm_tokens SET last_delivery_at = ?, last_error = NULL, "
                    "failure_count = 0 WHERE id = ?",
                    (now, r["id"]),
                )
            else:
                failed += 1
                if err and err.startswith("gone_"):
                    conn.execute("DELETE FROM push_fcm_tokens WHERE id = ?", (r["id"],))
                    deleted += 1
                else:
                    conn.execute(
                        "UPDATE push_fcm_tokens SET last_error = ?, last_delivery_at = ?, "
                        "failure_count = failure_count + 1 WHERE id = ?",
                        (err, now, r["id"]),
                    )
    return {"sent": sent, "failed": failed, "deleted": deleted}


def send_push_to_user(user_id: int, payload: dict, ttl: int = 86400) -> dict:
    """Unified entry: deliver to BOTH web push subscriptions AND native FCM
    tokens for this user. Same user might have both (browser + phone app).
    Returns combined counts in the same {sent, failed, deleted} shape as the
    old web-only function so existing callers work unchanged.
    `ttl` is kept in the signature for compatibility but currently unused —
    web push TTL was a noop in the old impl too."""
    web = send_push_web_to_user(user_id, payload)
    fcm = send_fcm_to_user(user_id, payload)
    return {
        "sent": web["sent"] + fcm["sent"],
        "failed": web["failed"] + fcm["failed"],
        "deleted": web["deleted"] + fcm["deleted"],
        # Sub-channel detail kept for debugging / admin test endpoint.
        "web": web,
        "fcm": fcm,
    }


def _mutual_friend_ids(conn: sqlite3.Connection, user_id: int) -> list[int]:
    """Return user_ids of all MUTUAL friends (both sides accepted). Used to
    decide who gets notified when this user plays a tournament."""
    rows = conn.execute(
        "SELECT f1.friend_user_id AS fid "
        "FROM friendships f1 "
        "JOIN friendships f2 ON f2.user_id = f1.friend_user_id "
        "                   AND f2.friend_user_id = f1.user_id "
        "WHERE f1.user_id = ? AND f1.status = 'accepted' AND f2.status = 'accepted'",
        (user_id,),
    ).fetchall()
    return [int(r["fid"]) for r in rows]


def _compute_match_score_server(my_top: dict, friend_top: dict) -> int:
    """Mirror of frontend computeMatchScore() — kept identical so server-side
    push payloads match what the frontend would have shown.

    Scoring (must match game.html computeMatchScore):
      - same #1: +50 pts
      - each of my top3 also in opponent top3: +25 pts
      - capped at 100
    Returns 0..100.
    """
    score = 0
    my1 = my_top.get("top1_id")
    my2 = my_top.get("top2_id")
    my3 = my_top.get("top3_id")
    opp1 = friend_top.get("top1_id")
    opp2 = friend_top.get("top2_id")
    opp3 = friend_top.get("top3_id")
    if my1 and opp1 and my1 == opp1:
        score += 50
    opp_set = {x for x in (opp1, opp2, opp3) if x}
    for mid in (my1, my2, my3):
        if mid and mid in opp_set:
            score += 25
    return min(100, score)


def notify_friends_of_completion(conn: sqlite3.Connection,
                                  player_id: int,
                                  player_nickname: str,
                                  result_row: dict) -> None:
    """Fan out a push to each mutual friend who has at least one push
    subscription. The payload uses match-score language when the friend has
    a result in the same category (richer signal), else falls back to the
    plain "@nick прошёл «X»" form. Best-effort — never raises; logs failures.

    Tag is "friend_played:<player_id>:<category_id>" so back-to-back
    plays in the same category replace the previous notification on the
    friend's lock screen instead of stacking."""
    try:
        friend_ids = _mutual_friend_ids(conn, player_id)
        if not friend_ids:
            return
        category_id = result_row.get("category_id")
        category_name = result_row.get("category_name") or category_id
        my_top1_name = result_row.get("top1_name") or "?"

        for fid in friend_ids:
            # Skip friends with no push subscriptions to avoid wasted work.
            sub_count = conn.execute(
                "SELECT COUNT(*) FROM push_subscriptions WHERE user_id = ?",
                (fid,),
            ).fetchone()[0]
            if not sub_count:
                continue

            # Try to find the friend's most recent result in this category
            # so we can compute and surface a match score.
            friend_result = conn.execute(
                "SELECT top1_id, top2_id, top3_id, top1_name FROM results "
                "WHERE user_id = ? AND category_id = ? "
                "ORDER BY completed_at DESC LIMIT 1",
                (fid, category_id),
            ).fetchone()

            if friend_result:
                score = _compute_match_score_server(
                    {
                        "top1_id": result_row.get("top1_id"),
                        "top2_id": result_row.get("top2_id"),
                        "top3_id": result_row.get("top3_id"),
                    },
                    {
                        "top1_id": friend_result["top1_id"],
                        "top2_id": friend_result["top2_id"],
                        "top3_id": friend_result["top3_id"],
                    },
                )
                title = f"@{player_nickname} прошёл «{category_name}»"
                body = f"Совпадение с тобой: {score}%"
            else:
                title = f"@{player_nickname} прошёл «{category_name}»"
                body = f"№1: {my_top1_name}. Сыграй и сравни!"

            payload = {
                "title": title,
                "body": body,
                "url": f"/?cat={category_id}",
                "tag": f"friend_played:{player_id}:{category_id}",
            }
            try:
                send_push_to_user(fid, payload)
            except Exception as e:
                logger.warning("notify_friends_of_completion send failed for fid=%s: %s",
                               fid, e)
    except Exception as e:
        logger.warning("notify_friends_of_completion outer error: %s", e)


# ─── RATE LIMITING (in-memory IP bucket) ────────────────────────
# Tracks per-IP attempt timestamps for sensitive endpoints (login + register).
# In-memory means resets on service restart; that's fine for our scale (one box).
# Multi-instance would need Redis. Each endpoint has its own bucket so a hit on
# /api/login doesn't count toward /api/admin/login limits.
import time as _time
from collections import deque as _deque
from threading import Lock as _Lock
_rate_buckets: dict[tuple[str, str], _deque] = {}
_rate_lock = _Lock()

def _client_ip(request: Request) -> str:
    """Best-effort real client IP for rate limiting.

    Order of trust:
      1. X-Real-IP — nginx sets this to $remote_addr (single trusted value, not
         attacker-controllable). Most reliable.
      2. X-Forwarded-For LAST value — nginx uses $proxy_add_x_forwarded_for
         which APPENDS the real client IP after any client-supplied header
         garbage. The LAST value is the one nginx wrote. (Round-3 audit
         finding 2026-05-08: previous code took FIRST value of XFF, which is
         attacker-spoofable, allowing rate-limit bypass.)
      3. request.client.host — direct connection IP (the nginx box itself
         when behind proxy, but useful in tests).
    """
    real = request.headers.get("x-real-ip", "").strip()
    if real:
        return real
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        # Last value = the IP nginx appended; earlier values are client-controlled.
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[-1]
    return (request.client.host if request.client else "unknown")

# Round-4 audit fix: periodic sweep of the bucket dict to prevent slow memory
# growth from a botnet/scanner flooding with unique IPs. Each call increments a
# counter; every Nth call we sweep ALL buckets, dropping entries with no live
# attempts (all expired). Plus a hard cap on dict size as a backstop.
_rate_calls_since_sweep = 0
_RATE_SWEEP_EVERY = 200          # sweep on every 200th rate_limit() call
_RATE_BUCKET_HARD_CAP = 10000    # if we exceed this, force-trim aggressively

def _rate_sweep_locked(now: float) -> None:
    """Drop expired buckets, then enforce hard cap by oldest-first eviction.
    Caller MUST hold _rate_lock.

    Two passes:
      1. Age-based: drop buckets whose last entry is older than 1 hour
         (longest window we use = register at 1h). These are safely stale.
      2. Cap-based: if dict still exceeds _RATE_BUCKET_HARD_CAP after age
         sweep (e.g. botnet flooded with 10k+ unique IPs in <1h), evict
         oldest-by-last-timestamp until size is back at cap. Per Round-5
         audit: previously the age sweep alone could leave the dict above
         cap if all entries were fresh. The cap is a real ceiling now.
    """
    # Pass 1: age-based
    cutoff = now - 3600
    dead = [k for k, b in _rate_buckets.items() if not b or b[-1] < cutoff]
    for k in dead:
        del _rate_buckets[k]

    # Pass 2: cap enforcement (oldest-by-last-timestamp eviction)
    excess = len(_rate_buckets) - _RATE_BUCKET_HARD_CAP
    if excess > 0:
        # Sort by last-timestamp ascending; evict the oldest `excess` entries.
        # Stable in CPython 3.7+. O(n log n) but only when above cap, rare.
        ranked = sorted(_rate_buckets.items(), key=lambda kv: kv[1][-1] if kv[1] else 0)
        for k, _ in ranked[:excess]:
            del _rate_buckets[k]


def rate_limit(request: Request, endpoint: str, max_attempts: int, window_sec: int) -> None:
    """Raise HTTPException(429) if this IP has hit the endpoint too often.

    Sliding window: counts attempts in last `window_sec` seconds. If >= max_attempts,
    rejects with 429 and Retry-After header set to seconds until oldest entry expires.
    """
    global _rate_calls_since_sweep
    ip = _client_ip(request)
    key = (endpoint, ip)
    now = _time.time()
    cutoff = now - window_sec
    with _rate_lock:
        # Periodic sweep: every Nth call, drop empty/old buckets. Cheap because
        # only iterates dict keys, no nested deques inspected. Caps memory.
        # Round-6 audit fix: trigger on `>= cap` (not `> cap`) so when we're
        # exactly at cap and about to insert a new key, sweep fires FIRST,
        # ensuring post-insert size never exceeds cap.
        _rate_calls_since_sweep += 1
        if _rate_calls_since_sweep >= _RATE_SWEEP_EVERY or len(_rate_buckets) >= _RATE_BUCKET_HARD_CAP:
            _rate_sweep_locked(now)
            _rate_calls_since_sweep = 0

        bucket = _rate_buckets.get(key)
        if bucket is None:
            # Round-7 audit fix: seed the deque with `now` BEFORE inserting it
            # into _rate_buckets and BEFORE the post-insert cap recheck.
            # Two reasons:
            #   1. _rate_sweep_locked drops empty buckets (`not b`) — without
            #      seeding, the new bucket would be torn out by the sweep
            #      immediately and our local `bucket` variable would point at
            #      a deque detached from the dict. The later `bucket.append(
            #      now)` would then write into a deque nobody else holds, and
            #      the first request from this key would be silently lost.
            #   2. With `now` already present, the bucket's last-seen
            #      timestamp is the freshest possible, so the cap-eviction
            #      pass (which evicts oldest-by-last-seen) won't pick it.
            bucket = _deque([now])
            _rate_buckets[key] = bucket
            # Defense in depth: if this insert pushed us back to/over the cap
            # (e.g. sweep couldn't free anything because all entries are fresh),
            # run cap enforcement again immediately. Worst case: O(n log n) but
            # only when actually saturated.
            if len(_rate_buckets) > _RATE_BUCKET_HARD_CAP:
                _rate_sweep_locked(now)
            # Brand-new bucket with exactly one entry — under any reasonable
            # max_attempts (>=2) this passes the rate check, so we're done.
            return
        # Existing-bucket path: trim expired entries (left = oldest)
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= max_attempts:
            # Compute retry-after as remaining seconds until the oldest entry expires
            retry_after = max(1, int(bucket[0] + window_sec - now))
            raise HTTPException(
                status_code=429,
                detail="rate_limited",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)


def hash_password(pw: str) -> str:
    # bcrypt silently truncates after 72 bytes — pre-truncate to be explicit
    pw_bytes = pw.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def check_password(pw: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(pw.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


def make_token() -> str:
    return secrets.token_urlsafe(32)


# ─── PASSWORD RESET TOKENS ──────────────────────────────────────────
# Generate, hash, validate one-time tokens emailed to users for password reset.
# Tokens are stored as SHA256 hashes in DB (never the raw value), so even a
# DB leak doesn't enable replay. Tokens are single-use + 1h expiry.

import hashlib
import hmac as _hmac  # for constant-time secret comparison (audit-5 M2)

PASSWORD_RESET_EXPIRY_HOURS = 1
PASSWORD_RESET_TOKEN_BYTES = 32  # → 43-char URL-safe base64 string

# Challenges (short share-link payloads): how long anonymous (guest) challenges
# linger before lazy-cleanup deletes them. Authored challenges (by_user_id NOT
# NULL) live forever — people reshare old links. Audit H2.
CHALLENGE_RETENTION_DAYS = 90

# Privacy/Terms version. Bump this DATESTAMP whenever the policy text in
# privacy.html or terms.html gets a material change. Users who registered
# under an older version are still on the older terms — we can prompt them
# to re-accept by comparing CURRENT_CONSENT_VERSION against their latest
# consent_acceptances row.
CURRENT_CONSENT_VERSION = "2026-05-10"

# Consent categories — see consent_state table comment for full semantics.
# 'core' is mandatory (granted at registration, can only be revoked by
# deleting the account). The rest are optional opt-in toggles managed in
# the profile.
CONSENT_CATEGORIES = ("core", "email_marketing", "push_marketing")
MANDATORY_CONSENT_CATEGORIES = ("core",)
OPTIONAL_CONSENT_CATEGORIES = tuple(c for c in CONSENT_CATEGORIES if c not in MANDATORY_CONSENT_CATEGORIES)


def _grant_consent(conn, user_id: int, category: str, ip: Optional[str], ua: Optional[str],
                   kind_suffix: str = "grant", version: Optional[str] = None) -> None:
    """Mark a consent category as granted for the user.
    Writes the current state (consent_state) AND an audit-log entry
    (consent_acceptances). Idempotent — re-granting an already-granted
    category just refreshes the timestamp, no side effects.
    """
    if category not in CONSENT_CATEGORIES:
        raise ValueError(f"unknown consent category: {category}")
    v = (version or CURRENT_CONSENT_VERSION).strip() or CURRENT_CONSENT_VERSION
    ts = now_iso()
    conn.execute(
        "INSERT INTO consent_state (user_id, category, is_granted, last_changed_at, consent_version) "
        "VALUES (?, ?, 1, ?, ?) "
        "ON CONFLICT(user_id, category) DO UPDATE SET "
        "  is_granted = 1, last_changed_at = excluded.last_changed_at, "
        "  consent_version = excluded.consent_version",
        (user_id, category, ts, v),
    )
    conn.execute(
        "INSERT INTO consent_acceptances (user_id, consent_version, kind, accepted_at, ip, user_agent) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, v, f"{category}_{kind_suffix}", ts, ip, ua),
    )


def _revoke_consent(conn, user_id: int, category: str, ip: Optional[str], ua: Optional[str],
                    version: Optional[str] = None) -> None:
    """Mark an OPTIONAL consent category as revoked. Refuses to revoke
    mandatory categories (you can only escape 'core' by deleting your account).
    """
    if category not in OPTIONAL_CONSENT_CATEGORIES:
        raise HTTPException(400, "cannot_revoke_mandatory_consent")
    v = (version or CURRENT_CONSENT_VERSION).strip() or CURRENT_CONSENT_VERSION
    ts = now_iso()
    conn.execute(
        "INSERT INTO consent_state (user_id, category, is_granted, last_changed_at, consent_version) "
        "VALUES (?, ?, 0, ?, ?) "
        "ON CONFLICT(user_id, category) DO UPDATE SET "
        "  is_granted = 0, last_changed_at = excluded.last_changed_at, "
        "  consent_version = excluded.consent_version",
        (user_id, category, ts, v),
    )
    conn.execute(
        "INSERT INTO consent_acceptances (user_id, consent_version, kind, accepted_at, ip, user_agent) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, v, f"{category}_revoke", ts, ip, ua),
    )


def _get_consent_state(conn, user_id: int) -> dict:
    """Return current consent state as {category: {granted, since, version}}.
    Categories not present in DB are reported as not-granted with since=None.
    """
    rows = conn.execute(
        "SELECT category, is_granted, last_changed_at, consent_version "
        "FROM consent_state WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    state = {c: {"granted": False, "since": None, "version": None} for c in CONSENT_CATEGORIES}
    for r in rows:
        state[r["category"]] = {
            "granted": bool(r["is_granted"]),
            "since": r["last_changed_at"],
            "version": r["consent_version"],
        }
    return state


def _hash_reset_token(raw_token: str) -> str:
    """SHA256 hex digest of the raw token. Used to look up tokens in DB
    without ever storing the raw value. Constant-time comparison happens
    automatically because hash output is uniform-length."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _generate_password_reset_token(conn: sqlite3.Connection, user_id: int,
                                    request_ip: str) -> str:
    """Create a fresh reset token for `user_id`, store its hash, return raw.

    The raw token is shown only once (in the email). After this function
    returns, the only way to retrieve the token is from the email link.
    """
    raw_token = secrets.token_urlsafe(PASSWORD_RESET_TOKEN_BYTES)
    token_hash = _hash_reset_token(raw_token)
    now = now_iso()
    expires = (datetime.now(timezone.utc)
               + timedelta(hours=PASSWORD_RESET_EXPIRY_HOURS)).isoformat()
    conn.execute(
        "INSERT INTO password_resets (user_id, token_hash, created_at, expires_at, request_ip) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, token_hash, now, expires, request_ip),
    )
    return raw_token


def _consume_password_reset_token(conn: sqlite3.Connection,
                                   raw_token: str) -> Optional[int]:
    """Validate + atomically mark-used a reset token. Returns user_id on
    success, None on any failure (token unknown, expired, already used).

    The function is intentionally generic about WHY it failed — caller
    surfaces the same "invalid_or_expired" error regardless, to avoid
    leaking which case applied (which could help an attacker enumerate).
    """
    if not raw_token or len(raw_token) < 20:
        return None
    token_hash = _hash_reset_token(raw_token)
    row = conn.execute(
        "SELECT id, user_id, expires_at, used_at FROM password_resets "
        "WHERE token_hash = ?",
        (token_hash,),
    ).fetchone()
    if not row:
        return None
    if row["used_at"]:
        return None  # already consumed
    if row["expires_at"] < now_iso():
        return None  # expired
    # Atomically mark used. If another concurrent request already consumed it
    # (rowcount=0), treat as failure.
    cur = conn.execute(
        "UPDATE password_resets SET used_at = ? WHERE id = ? AND used_at IS NULL",
        (now_iso(), row["id"]),
    )
    if cur.rowcount != 1:
        return None
    return int(row["user_id"])


def auto_friend_admin(conn: sqlite3.Connection, new_user_id: int) -> None:
    """Insert asymmetric friendship from the configured admin to a freshly-registered
    user. The admin sees the new user in their friends list immediately (so they can
    use 'compare', browse results, etc., without going through the admin panel).
    The new user does NOT see the admin — their friends list is still empty until
    they explicitly send a friend request (which goes through the normal pending flow
    and can be accepted by the admin as usual).

    Best-effort: silently skips on any failure (auto-friend should never block register).
    """
    nick = (AUTO_FRIEND_ADMIN_NICKNAME or "").strip()
    if not nick:
        return  # disabled
    try:
        admin = conn.execute(
            "SELECT id FROM users WHERE nickname = ? COLLATE NOCASE",
            (nick,),
        ).fetchone()
        if not admin:
            return  # configured admin not found — skip silently
        admin_id = admin["id"]
        if admin_id == new_user_id:
            return  # don't auto-friend self
        # INSERT OR IGNORE so a re-run is safe (UNIQUE on user_id+friend_user_id)
        conn.execute(
            "INSERT OR IGNORE INTO friendships (user_id, friend_user_id, status, created_at, responded_at) "
            "VALUES (?, ?, 'accepted', ?, ?)",
            (admin_id, new_user_id, now_iso(), now_iso()),
        )
    except Exception as e:
        logger.warning("auto_friend_admin failed: %s", e)


def get_session_user(session: str | None, request: Request | None = None) -> dict | None:
    if not session:
        return None
    with db() as conn:
        row = conn.execute(
            "SELECT u.*, s.expires_at AS sess_expires "
            "FROM sessions s JOIN users u ON s.user_id = u.id "
            "WHERE s.token = ?",
            (session,),
        ).fetchone()
        if not row:
            return None
        if row["sess_expires"] < now_iso():
            conn.execute("DELETE FROM sessions WHERE token = ?", (session,))
            return None
        conn.execute(
            "UPDATE sessions SET last_seen_at = ? WHERE token = ?",
            (now_iso(), session),
        )
        return dict(row)


def require_user(session: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> dict:
    user = get_session_user(session)
    if not user:
        raise HTTPException(status_code=401, detail="not_authenticated")
    return user


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_DAYS * 86400,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


def public_user(u: dict) -> dict:
    return {
        "id": u["id"],
        "nickname": u["nickname"],
        "email": u.get("email"),
        "avatar_glyph": u.get("avatar_glyph") or "✦",
        "created_at": u["created_at"],
        "is_admin": bool(u.get("is_admin", 0)),
        "role": u.get("role", "user"),
        "email_verified": bool(u.get("email_verified", 0)),
        "is_paid": bool(u.get("is_paid", 0)),
    }


def real_ip(request: Request) -> str | None:
    """Resolve the real client IP. Audit re-review LOW: previously this
    only checked X-Real-IP, while _client_ip() (used by the rate limiter)
    has more thorough X-Forwarded-For handling. Two helpers diverging
    invites bugs — `real_ip` is now a thin alias to keep call-sites
    unchanged while sharing a single source of truth."""
    return _client_ip(request)


# ─── SOCIAL AUTH (Sign in with Apple / Google) ──────────────────────
# Frontend (Capacitor app) obtains an ID token from native Apple or Google
# auth flow. Backend validates the token's signature + audience claim, then
# either returns existing user (by social_identities lookup OR by email match)
# or creates a new one using the nickname provided by the user.

def _validate_google_id_token(id_token: str) -> Optional[dict]:
    """Verify a Google ID token by calling Google's tokeninfo endpoint.

    No JWT-validation libs needed: Google does the crypto for us if we just
    HTTP GET the tokeninfo URL. They reject expired/tampered tokens with 4xx.

    Returns dict with {sub, email, email_verified, aud, name, picture} on
    success, None on any failure (invalid, expired, tampered, network).
    """
    if not id_token or len(id_token) < 50:
        return None
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
            )
        if r.status_code != 200:
            logger.warning("google tokeninfo rejected: %d %s", r.status_code, r.text[:200])
            return None
        data = r.json()
        # Verify audience matches one of our configured client IDs
        aud = data.get("aud", "")
        valid_auds = {a for a in (
            GOOGLE_OAUTH_CLIENT_ID_WEB,
            GOOGLE_OAUTH_CLIENT_ID_ANDROID,
            GOOGLE_OAUTH_CLIENT_ID_IOS,
        ) if a}
        if not valid_auds:
            # No client IDs configured yet — auth is not enabled
            logger.error("google_auth_not_configured: no GOOGLE_OAUTH_CLIENT_ID_* env vars set")
            return None
        if aud not in valid_auds:
            logger.warning("google audience mismatch: got %s, expected one of %s", aud, valid_auds)
            return None
        return data
    except Exception as e:
        logger.warning("google tokeninfo exception: %s", e)
        return None


def _validate_apple_id_token(id_token: str) -> Optional[dict]:
    """Verify an Apple ID token (JWT signed with one of Apple's public keys).

    NOTE: requires `pyjwt` + `cryptography` packages installed. We do a
    soft-import; if missing, returns None (and logs an error). To enable:
      pip install "PyJWT[crypto]>=2.8" cryptography

    Returns dict with {sub, email, email_verified, aud, ...} or None.
    """
    try:
        import jwt as pyjwt  # type: ignore
        from jwt import PyJWKClient  # type: ignore
    except ImportError:
        logger.error("apple_auth_pyjwt_missing: install PyJWT[crypto] to enable Apple sign-in")
        return None
    if not id_token or len(id_token) < 50:
        return None
    try:
        # Apple publishes their JWK set; PyJWKClient fetches and caches.
        jwks_url = "https://appleid.apple.com/auth/keys"
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        decoded = pyjwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=APPLE_BUNDLE_ID,
            issuer="https://appleid.apple.com",
        )
        return decoded
    except Exception as e:
        logger.warning("apple jwt validation failed: %s", e)
        return None


def _sanitize_nick_from_token(decoded: dict) -> str:
    """Pick a fallback nickname from an OAuth ID token's claims when the
    user didn't type one (e.g. signing in via the login button rather than
    the welcome flow). Tries given_name → name → email-prefix → "user".
    Strips to Latin [A-Za-z0-9_.-] to match NICK_RE, truncates to 24."""
    raw = (decoded.get("given_name") or decoded.get("name") or "").strip()
    if not raw and decoded.get("email"):
        raw = decoded["email"].split("@")[0]
    if not raw:
        raw = "user"
    # Strip to Latin chars allowed by NICK_RE
    cleaned = re.sub(r"[^A-Za-z0-9_.\-]", "", raw)
    if not cleaned or len(cleaned) < 2:
        cleaned = "user"
    return cleaned[:24]


def _suggest_nickname(conn: sqlite3.Connection, base: str, max_tries: int = 50) -> Optional[str]:
    """Find a nickname variant that's not taken. Tries base, base_2, base_3, ...
    Returns the available variant, or None if all 50 are taken (unlikely)."""
    base = (base or "").strip()
    if not base or not NICK_RE.match(base):
        return None
    if not conn.execute(
        "SELECT 1 FROM users WHERE nickname = ? COLLATE NOCASE", (base,)
    ).fetchone():
        return base
    for n in range(2, max_tries + 1):
        candidate = f"{base}_{n}"
        if not conn.execute(
            "SELECT 1 FROM users WHERE nickname = ? COLLATE NOCASE", (candidate,)
        ).fetchone():
            return candidate
    return None


def _social_signin_or_create(
    conn: sqlite3.Connection,
    provider: str,
    provider_user_id: str,
    email: Optional[str],
    email_verified: bool,
    requested_nickname: str,
    request: Request,
    consent: bool = False,
) -> tuple[int, str, bool]:
    """Resolve a social-auth identity to a user_id. Three paths:
       1. (provider, provider_user_id) already linked → return existing user
       2. Email matches an existing user AND provider verified the email →
          link this social identity to that user (account merge)
       3. Otherwise → create new user with requested_nickname

    SECURITY (audit C2): Path 2 ONLY proceeds when the OAuth provider asserts
    `email_verified=true`. Otherwise an attacker who registered a social
    account with someone's email (without proving ownership) could log into
    that victim's password-protected account. With email_verified=false we
    fall through to Path 3 and create a separate account; if the email is
    already taken (UNIQUE) we drop email from the new row so the existing
    account stays untouched.

    CONSENT (UX-1, 2026-05-11): the `consent` parameter is REQUIRED only
    for path 3 (new account creation). Paths 1 and 2 ignore it because the
    user already accepted T&Cs at original registration — re-asking on
    every login is annoying friction. If path 3 is hit with consent=False,
    we raise 409 consent_required_new_account so the frontend can show
    a one-time consent modal and retry with consent=true.

    Returns (user_id, final_nickname, is_new_user).
    Raises HTTPException on validation/conflict errors.
    """
    # Path 1: existing social identity (always safe — provider sub is
    # cryptographically tied to the same account on every login)
    row = conn.execute(
        "SELECT user_id FROM social_identities "
        "WHERE provider = ? AND provider_user_id = ?",
        (provider, provider_user_id),
    ).fetchone()
    if row:
        uid = int(row["user_id"])
        u = conn.execute(
            "SELECT nickname FROM users WHERE id = ?", (uid,)
        ).fetchone()
        return (uid, u["nickname"] if u else "", False)

    # Path 2: email match (link social to existing email-registered account)
    # GUARDED by email_verified — see security note above.
    if email and email_verified:
        row = conn.execute(
            "SELECT id, nickname FROM users WHERE email = ? COLLATE NOCASE",
            (email.lower(),),
        ).fetchone()
        if row:
            uid = int(row["id"])
            conn.execute(
                "INSERT INTO social_identities "
                "(user_id, provider, provider_user_id, email, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (uid, provider, provider_user_id, email, now_iso()),
            )
            return (uid, row["nickname"], False)

    # Path 3: create new user.
    # CONSENT GATE (UX-1, 2026-05-11): only this path requires consent.
    # Frontend MAY call without consent on the login form (existing-user
    # case is the 99% norm) — if we land here, frontend gets 409 and shows
    # a one-time "create account?" modal with the consent checkbox, then
    # retries the same id_token with consent=true.
    if not consent:
        raise HTTPException(409, "consent_required_new_account")
    # If the email is unverified OR already taken by some other account, we
    # drop it from the new user row so there's no email collision and so the
    # existing account isn't even named in the new user's profile.
    nick = (requested_nickname or "").strip()
    if not nick or not NICK_RE.match(nick) or len(nick) < 2 or len(nick) > 24:
        raise HTTPException(422, "invalid_nickname")
    final_nick = _suggest_nickname(conn, nick)
    if not final_nick:
        raise HTTPException(409, "nickname_unavailable")

    # Decide what email to store on the new account.
    insert_email: Optional[str] = None
    if email and email_verified:
        # Verified and (per Path 2 above) didn't match any existing user.
        # Re-check uniqueness in case of TOCTOU race; if taken, drop email.
        clash = conn.execute(
            "SELECT 1 FROM users WHERE email = ? COLLATE NOCASE",
            (email.lower(),),
        ).fetchone()
        insert_email = None if clash else email.lower()
    # else: unverified OR no email → store NULL so we don't lock out the
    # legitimate owner from later registering the email properly.

    conn.execute(
        "INSERT INTO users (nickname, email, password_hash, created_at, last_login_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (final_nick, insert_email, None, now_iso(), now_iso()),
    )
    new_uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO social_identities "
        "(user_id, provider, provider_user_id, email, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (new_uid, provider, provider_user_id, email, now_iso()),
    )
    # Auto-friend admin (same as email register)
    auto_friend_admin(conn, new_uid)
    # Grant 'core' consent. The mobile welcome flow shows the privacy/terms
    # checkbox before triggering native OAuth, so by the time we reach this
    # branch the user has explicitly accepted. Optional categories
    # (email_marketing, push_marketing) stay off; user opts in later.
    _grant_consent(
        conn, new_uid, "core",
        real_ip(request), (request.headers.get("user-agent") or "")[:500],
        kind_suffix=f"social_{provider}",
    )
    return (new_uid, final_nick, True)


# ─── PYDANTIC MODELS ───────────────────────────────────────────

class RegisterIn(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=24)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    # Referrer nickname (optional). If user landed via a challenge link from
    # an existing user, frontend captures that user's nick and forwards it here.
    # Backend resolves to user_id and stores in users.referred_by + unlocks
    # an achievement for the referrer.
    referrer_nickname: Optional[str] = Field(default=None, min_length=2, max_length=24)
    # Explicit consent (GDPR / 152-ФЗ). Frontend already enforces the checkbox,
    # but backend re-validates as defense in depth. Without consent=true the
    # registration is rejected with 400 consent_required.
    consent: bool = Field(default=False)
    # Version of the policy the user accepted. Frontend sends a constant
    # matching the live privacy.html / terms.html date. Stored in
    # consent_acceptances so we can prove which version was accepted.
    consent_version: Optional[str] = Field(default=None, max_length=40)
    # Optional gender. Used by AI portrait generation to pick the correct
    # Russian gendered forms. None (skipped) → strict gender-neutral prompt
    # rules apply. Accepted values: 'male' | 'female'.
    gender: Optional[str] = Field(default=None, max_length=8)

    @field_validator("nickname")
    @classmethod
    def _nick(cls, v: str) -> str:
        v = v.strip()
        if not NICK_RE.match(v):
            raise ValueError("nickname can only contain letters, digits, _ . -")
        return v

    @field_validator("gender")
    @classmethod
    def _gender(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        if v == "":
            return None
        if v not in ("male", "female"):
            raise ValueError("gender must be 'male' or 'female'")
        return v


class LoginIn(BaseModel):
    email_or_nick: str = Field(..., min_length=2, max_length=128)
    password: str = Field(..., min_length=1, max_length=72)


class SocialAuthIn(BaseModel):
    """Used by both /api/auth/google and /api/auth/apple endpoints.

    nickname is optional: required only if creating a new account (path 3
    in _social_signin_or_create). For existing-user login (paths 1/2) the
    server ignores it and uses the existing nickname. If empty/missing on
    new-account path, server uses Google's `name` claim from the ID token
    as fallback, or generates user_<random> if that's also missing."""
    id_token: str = Field(..., min_length=50, max_length=8192)
    nickname: Optional[str] = Field(default=None, max_length=24)
    consent: bool = Field(default=False)
    consent_version: Optional[str] = Field(default=None, max_length=40)


class NicknameCheckIn(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=24)


class ConsentUpdateIn(BaseModel):
    """User opts in or out of an OPTIONAL consent category from the profile.
    Mandatory categories (e.g. 'core') reject revoke and 200-OK on grant
    (idempotent — they're already granted at registration)."""
    category: str = Field(..., min_length=1, max_length=40)
    granted: bool


class PushSubscribeIn(BaseModel):
    """Body the frontend sends after pushManager.subscribe() returns.
    Fields map directly to the PushSubscription JSON shape. endpoint is the
    full push-service URL (e.g. https://fcm.googleapis.com/fcm/send/...);
    p256dh + auth are URL-safe base64 keys the push service uses to encrypt
    delivery to the user's specific device."""
    endpoint: str = Field(..., min_length=20, max_length=2000)
    p256dh: str = Field(..., min_length=20, max_length=200)
    auth: str = Field(..., min_length=10, max_length=100)


class PushUnsubscribeIn(BaseModel):
    """Looser model for unsubscribe — caller only needs to identify the
    subscription by endpoint URL. Used both by the explicit toggle in
    profile AND by the SW pushsubscriptionchange handler (which doesn't
    have access to the new keys at that moment)."""
    endpoint: str = Field(..., min_length=20, max_length=2000)


class FcmTokenSubscribeIn(BaseModel):
    """Body the frontend sends after Capacitor PushNotifications plugin's
    `registration` event fires on native. `token` is the FCM device token
    (~200 chars of opaque ASCII), `platform` is 'android' or 'ios' so the
    server can format payloads correctly downstream (iOS uses APNS via
    Firebase, Android uses native FCM channels with different field sets)."""
    token: str = Field(..., min_length=20, max_length=400)
    platform: str = Field(..., pattern=r'^(android|ios)$')


class FcmTokenUnsubscribeIn(BaseModel):
    """Just the token — same as web unsubscribe model, simpler shape since
    FCM tokens are self-identifying."""
    token: str = Field(..., min_length=20, max_length=400)


class AdminPushTestIn(BaseModel):
    """Admin tool: send a test push to a specific user by nickname.
    Used to verify VAPID setup end-to-end before wiring up real triggers."""
    nickname: str = Field(..., min_length=2, max_length=24)
    title: Optional[str] = Field(default="Тест Tappetite", max_length=120)
    body: Optional[str] = Field(default="Если ты это видишь — пуши работают.", max_length=300)


class TournamentVoteIn(BaseModel):
    """Vote on a turnir after completion. vote=1 like, vote=-1 dislike,
    vote=0 removes any existing vote (toggle off). Frontend sends 0 when
    user taps the same button they already selected."""
    vote: int = Field(..., ge=-1, le=1)


# Mirror of frontend SYSTEM_AUTHORS — used to decide whether a turnir's
# submitter should be credited with creator-side achievements (only real
# user-submitted UGC counts; system-authored seed content does not).
SYSTEM_AUTHOR_NICKS = {"Uncle", "uncle"}

def isSystemAuthor_py(nick: str) -> bool:
    return (nick or "").strip() in SYSTEM_AUTHOR_NICKS


class ResultIn(BaseModel):
    category_id: str = Field(..., min_length=1, max_length=64)
    category_name: Optional[str] = Field(default=None, max_length=200)
    top1_id: str = Field(..., min_length=1, max_length=64)
    top1_name: Optional[str] = Field(default=None, max_length=200)
    top2_id: Optional[str] = Field(default=None, max_length=64)
    top2_name: Optional[str] = Field(default=None, max_length=200)
    top3_id: Optional[str] = Field(default=None, max_length=64)
    top3_name: Optional[str] = Field(default=None, max_length=200)
    archetype_name: Optional[str] = Field(default=None, max_length=200)
    archetype_body: Optional[str] = Field(default=None, max_length=2000)
    battles_played: int = Field(default=0, ge=0, le=100000)
    duration_sec: int = Field(default=0, ge=0, le=86400)
    is_public: bool = True
    items_count: Optional[int] = Field(default=None, ge=0, le=10000)  # snapshot of category size at completion
    # Client-generated ID (e.g. 'r_a8f3k7d2lm9q'). Used for idempotent inserts —
    # if the same (user_id, client_id) is POSTed twice, we return the existing
    # row instead of creating a duplicate. Critical for retries / double-taps.
    client_id: Optional[str] = Field(default=None, min_length=3, max_length=64)


class AdminLoginIn(BaseModel):
    password: str = Field(..., min_length=1, max_length=128)
    nickname: Optional[str] = Field(default=None, min_length=1, max_length=24)


class CreateModeratorIn(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=24)
    password: str = Field(..., min_length=6, max_length=128)
    email: Optional[EmailStr] = None


class SubmissionIn(BaseModel):
    type: str = Field(..., pattern=r'^(category|item)$')
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    cluster: Optional[str] = Field(default=None, max_length=80)
    target_category_id: Optional[str] = Field(default=None, max_length=64)
    examples: Optional[list[str]] = Field(default=None, max_length=20)

    @field_validator('title')
    @classmethod
    def _t(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("title too short")
        return v


class SubmissionUpdate(BaseModel):
    # All fields optional — caller patches whatever it wants. status is the
    # most common, but admin can also edit title/description/cluster/target
    # before approval (e.g. fix typos in player's submission).
    status: Optional[str] = Field(default=None, pattern=r'^(pending|approved|rejected|needs_review)$')
    decision_note: Optional[str] = Field(default=None, max_length=1000)
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    cluster: Optional[str] = Field(default=None, max_length=80)
    target_category_id: Optional[str] = Field(default=None, max_length=64)
    # Admin god-mode (2026-05-11): override displayed submitter. Empty string
    # CLEARS the override (falls back to original user_id). Non-empty must
    # resolve to an existing user (NICK_RE-validated, looked up COLLATE NOCASE).
    # Use case: friend tells admin an idea verbally → admin enters submission
    # themselves → attributes credit to friend. Audit log keeps original user_id.
    attributed_nickname: Optional[str] = Field(default=None, max_length=24)


class AddFriendIn(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=24)

    @field_validator('nickname')
    @classmethod
    def _n(cls, v: str) -> str:
        v = v.strip()
        if not NICK_RE.match(v):
            raise ValueError("invalid nickname")
        return v


def _lookup_admin_session(token: str | None) -> dict | None:
    """Validate an admin/mod cookie token against admin_sessions table.

    Returns {role, user_id, nickname} for a valid (non-expired, non-revoked)
    session, or None otherwise. Side effect: deletes the row if expired so
    we don't accumulate dead sessions.

    For named-user sessions (user_id != NULL), also re-checks that the user
    still has 'moderator' or 'admin' role — guards against demoted users
    keeping admin access via still-valid cookie.
    """
    if not token:
        return None
    with db() as conn:
        row = conn.execute(
            "SELECT a.token, a.role AS sess_role, a.user_id, a.expires_at, "
            "       u.nickname, u.role AS user_role "
            "FROM admin_sessions a "
            "LEFT JOIN users u ON u.id = a.user_id "
            "WHERE a.token = ?",
            (token,),
        ).fetchone()
        if not row:
            return None
        # Expired? clean up and reject.
        if row["expires_at"] < now_iso():
            conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
            return None
        # Named session: user must STILL hold a privileged role.
        if row["user_id"] is not None:
            if not row["user_role"] or row["user_role"] not in ("moderator", "admin"):
                conn.execute("DELETE FROM admin_sessions WHERE token = ?", (token,))
                return None
    # For named sessions, derive the EFFECTIVE role from the user's CURRENT
    # users.role rather than the role stored at login time. Otherwise an admin
    # demoted to moderator keeps full admin powers until session expiry, since
    # `sess_role` was frozen at login. (Round-3 audit fix 2026-05-08.)
    # Master-password sessions have user_id=NULL → keep stored sess_role='admin'.
    effective_role = row["user_role"] if row["user_id"] is not None else row["sess_role"]
    return {
        "role": effective_role,
        "user_id": row["user_id"],
        "nickname": row["nickname"],  # NULL for master-password sessions
    }


def require_admin(upg_admin: str | None = Cookie(default=None, alias=ADMIN_COOKIE_NAME)) -> bool:
    """FULL admin only. Validates the cookie token against admin_sessions —
    no longer trusts a literal value (P0 fixed 2026-05-08; previously any
    HTTP client could send Cookie: upg_admin_v2=ok and become admin)."""
    sess = _lookup_admin_session(upg_admin)
    if not sess or sess["role"] != "admin":
        raise HTTPException(403, "admin_required")
    return True


def require_mod_or_admin(upg_admin: str | None = Cookie(default=None, alias=ADMIN_COOKIE_NAME)) -> str:
    """Admin or named moderator. Validates cookie token against admin_sessions."""
    sess = _lookup_admin_session(upg_admin)
    if not sess or sess["role"] not in ("admin", "moderator"):
        raise HTTPException(403, "admin_required")
    return sess["role"]


def log_admin_action(conn: sqlite3.Connection, actor: dict, action: str, target: str | None,
                     extras: dict | None = None) -> None:
    """Centralised audit log writer. `actor` comes from get_admin_actor — its
    user_id is non-null for moderator actions (cookie 'mod:<id>'), null for
    full admin actions (master-password login). Extras json-serialised."""
    conn.execute(
        "INSERT INTO admin_actions (admin_user_id, action, target, extras_json, at) "
        "VALUES (?, ?, ?, ?, ?)",
        (actor.get('user_id') if actor else None,
         action, target,
         json.dumps(extras or {}, ensure_ascii=False),
         now_iso())
    )


def get_admin_actor(upg_admin: str | None = Cookie(default=None, alias=ADMIN_COOKIE_NAME)) -> dict:
    """Returns {role, user_id, nickname} for admin-action logging.
    Doesn't raise — safe to call when caller's already authenticated."""
    sess = _lookup_admin_session(upg_admin)
    if sess:
        return sess
    return {"role": "anonymous", "user_id": None, "nickname": None}


def submission_to_dict(row: sqlite3.Row, with_user: bool = True) -> dict:
    d = dict(row)
    # Decode JSON fields
    if d.get('examples_json'):
        try: d['examples'] = json.loads(d['examples_json'])
        except Exception: d['examples'] = []
    else:
        d['examples'] = []
    d.pop('examples_json', None)
    if d.get('ai_check_json'):
        try: d['ai_check'] = json.loads(d['ai_check_json'])
        except Exception: d['ai_check'] = None
    else:
        d['ai_check'] = None
    d.pop('ai_check_json', None)
    return d


# ─── ENDPOINTS ─────────────────────────────────────────────────

@app.get("/api/categories")
def categories(response: Response):
    """Serve the categories list for game.html and admin.html.
    Reads from a JSON file (regenerated via api/extract_categories.py).
    Cached on client side via localStorage; this endpoint sets ETag for HTTP caching too."""
    if not CATEGORIES_JSON_PATH.exists():
        raise HTTPException(503, "categories_not_seeded")
    try:
        raw = CATEGORIES_JSON_PATH.read_text(encoding='utf-8')
        data = json.loads(raw)
    except Exception as e:
        raise HTTPException(500, f"categories_load_failed: {e}")
    # Short cache so admin approvals propagate to clients within ~30s.
    # `must-revalidate` forces browsers to confirm freshness past max-age.
    response.headers["Cache-Control"] = "public, max-age=30, must-revalidate"
    version = int(CATEGORIES_JSON_PATH.stat().st_mtime)
    response.headers["ETag"] = f'W/"cats-{version}"'
    return {"categories": data, "count": len(data), "version": version}


# ─── TOURNAMENT VOTES (likes/dislikes) ─────────────────────────────

@app.get("/api/tournaments/votes")
def tournaments_vote_summary(session: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    """Aggregate vote counts for ALL turnirs in a single round-trip. Frontend
    calls this once on home/cluster render and uses the response to label
    every tile with its current likes/dislikes. Per-user 'my_vote' is
    populated only for authenticated callers (guests see counts but no
    'I voted' state)."""
    user = get_session_user(session)
    user_id = user["id"] if user else None
    with db() as conn:
        rows = conn.execute(
            "SELECT category_id, "
            "       SUM(CASE WHEN vote = 1 THEN 1 ELSE 0 END) AS likes, "
            "       SUM(CASE WHEN vote = -1 THEN 1 ELSE 0 END) AS dislikes "
            "FROM tournament_votes GROUP BY category_id"
        ).fetchall()
        my_votes = {}
        if user_id is not None:
            for r in conn.execute(
                "SELECT category_id, vote FROM tournament_votes WHERE user_id = ?",
                (user_id,),
            ).fetchall():
                my_votes[r["category_id"]] = int(r["vote"])
    out = {}
    for r in rows:
        cid = r["category_id"]
        out[cid] = {
            "likes": int(r["likes"] or 0),
            "dislikes": int(r["dislikes"] or 0),
            "my_vote": my_votes.get(cid, 0),
        }
    # Include zero-row entries for turnirs the user voted on but with no
    # aggregate row yet (shouldn't happen, but defensive).
    for cid, v in my_votes.items():
        if cid not in out:
            out[cid] = {"likes": 0, "dislikes": 0, "my_vote": v}
    return {"votes": out}


@app.post("/api/tournaments/{cat_id}/vote")
def tournament_vote(cat_id: str,
                     body: TournamentVoteIn,
                     request: Request,
                     user: dict = Depends(require_user)):
    """Cast / change / remove the current user's vote on a turnir.
    vote=1 like, vote=-1 dislike, vote=0 removes any existing vote.
    Returns updated counts so the UI can re-render without a follow-up GET.

    Achievement side-effects:
      - Voter's 'voter_count' may have crossed 1/10/100 → unlock checks fire
      - Creator (if it's a UGC turnir) gets checked for received-likes thresholds
    """
    rate_limit(request, "tournament_vote", max_attempts=60, window_sec=600)
    # Validate category exists in the live JSON (so we don't accumulate votes
    # on stale or deleted categories).
    cats = _load_categories()
    cat = next((c for c in cats if c.get("id") == cat_id), None)
    if not cat:
        raise HTTPException(404, "category_not_found")

    creator_user_id: int | None = None
    with db() as conn:
        if body.vote == 0:
            conn.execute(
                "DELETE FROM tournament_votes WHERE user_id = ? AND category_id = ?",
                (user["id"], cat_id),
            )
        else:
            conn.execute(
                "INSERT INTO tournament_votes (user_id, category_id, vote, voted_at) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(user_id, category_id) DO UPDATE SET "
                "  vote = excluded.vote, "
                "  voted_at = excluded.voted_at",
                (user["id"], cat_id, body.vote, now_iso()),
            )
        # Re-read counts for return payload
        agg = conn.execute(
            "SELECT "
            "  COALESCE(SUM(CASE WHEN vote = 1 THEN 1 ELSE 0 END), 0) AS likes, "
            "  COALESCE(SUM(CASE WHEN vote = -1 THEN 1 ELSE 0 END), 0) AS dislikes "
            "FROM tournament_votes WHERE category_id = ?",
            (cat_id,),
        ).fetchone()

        # Resolve creator user_id if turnir was submitted by a real user (so
        # we can fire their achievement check). System-authored turnirs have
        # no submitter; skip the lookup quietly.
        submitter_nick = (cat.get("submitted_by") or "").strip()
        if submitter_nick and not isSystemAuthor_py(submitter_nick):
            row = conn.execute(
                "SELECT id FROM users WHERE nickname = ? COLLATE NOCASE",
                (submitter_nick,),
            ).fetchone()
            if row:
                creator_user_id = int(row["id"])

    # Voter achievements (1 / 10 / 100 likes given) — recompute always since
    # vote=0 also matters (their voter_count went down).
    voter_unlocked: list[str] = []
    try:
        voter_unlocked = check_and_unlock_achievements(user["id"])
    except Exception as e:
        logger.warning("voter achievement check failed: %s", e)

    # Creator achievements (your turnir got 1 / 10 / 100 likes) — only
    # meaningful when the action was a like (vote=1) AND creator is a real
    # user. Even after dislike/unvote we recompute to be safe.
    creator_unlocked: list[str] = []
    if creator_user_id and creator_user_id != user["id"]:
        try:
            creator_unlocked = check_and_unlock_achievements(creator_user_id)
        except Exception as e:
            logger.warning("creator achievement check failed: %s", e)

    return {
        "ok": True,
        "category_id": cat_id,
        "likes": int(agg["likes"]),
        "dislikes": int(agg["dislikes"]),
        "my_vote": body.vote,
        "newly_unlocked_achievements": voter_unlocked,
    }


# ─── AUTO-APPLY APPROVED ITEM SUBMISSIONS ───────────────────────
# When admin approves a submission of type='item', append the new item to the
# target category in categories.json. The item's `ctx` (one-line description)
# is generated by Claude API in the same style as existing items in that category.

def _slugify_id(name: str, max_len: int = 32) -> str:
    """Make a URL-safe id slug from a name (Cyrillic-safe via simple normalisation)."""
    s = name.strip().lower()
    # Map some common Cyrillic to latin so ids stay ascii where possible
    cyr_map = str.maketrans({
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y',
        'к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f',
        'х':'h','ц':'c','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    })
    s = s.translate(cyr_map)
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return (s or 'item')[:max_len]


def _generate_item_ctx(category: dict, new_item_name: str) -> tuple[str, str, Optional[str]]:
    """Generate bilingual (ru, en) one-line ctx for a new item in the given
    category via Claude API.

    Returns (ctx_ru, ctx_en, error_message_or_None). On any failure, both
    strings are empty and error explains why — caller decides whether to
    apply the item without ctx (won't pass the bilingual validator) or
    refuse the auto-apply.

    Audit-5 H1 changed signature from (str, error) → (str, str, error) so
    item-submission approval can fill BOTH name_en and ctx_en, satisfying
    _validate_category_for_publish().
    """
    if not _ANTHROPIC_AVAILABLE:
        return "", "", "anthropic_sdk_not_installed"
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return "", "", "anthropic_api_key_missing"

    items = [it for it in (category.get("items") or []) if it.get("ctx")]
    if not items:
        # No examples to model the format on; admin will fill in manually.
        return "", "", "no_format_examples_in_category"

    # Sample up to 5 existing items as format reference. Use a deterministic
    # sort + slice (not random) so prompt caching has a stable prefix per
    # category — random.sample would defeat the cache.
    sample = sorted(items, key=lambda it: it.get('id', ''))[:5]
    examples_ru = "\n".join(f"  - {it['name']} -> {it['ctx']}" for it in sample)
    examples_en = "\n".join(
        f"  - {it.get('name_en') or it['name']} -> {it.get('ctx_en') or '[missing]'}"
        for it in sample
    )

    system_prompt = (
        "Ты редактор контента для турнирной игры выбора любимых вариантов.\n"
        "Твоя задача: написать короткую подпись (ctx) для нового участника,\n"
        "добавляемого в существующую категорию. Нужна ДВУЯЗЫЧНАЯ версия — RU + EN.\n\n"
        f"Категория: {category.get('name', '')} / {category.get('name_en') or category.get('name', '')}\n"
        f"Что выбираем: {category.get('blurb', '')}\n\n"
        "Примеры подписей RU (соблюдай ровно тот же формат, длину и стиль):\n"
        f"{examples_ru}\n\n"
        "Примеры EN:\n"
        f"{examples_en}\n\n"
        "Правила:\n"
        "1. Соблюдай структуру и длину примеров (разделители - · :, порядок данных).\n"
        "2. Используй настоящие факты из своих знаний.\n"
        "3. Не выдумывай факты - если не уверен, выбери более общую формулировку.\n"
        "4. Отвечай СТРОГО в формате двух строк, без префиксов и кавычек:\n"
        "   RU: <русская подпись>\n"
        "   EN: <english caption>\n"
    )

    try:
        client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var
        msg = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=400,
            system=[{
                "type": "text",
                "text": system_prompt,
                # Cache so multiple approvals in the same category in a 5-min window
                # share the prefix. Note: minimum cacheable prefix on Opus 4.7 is
                # 4096 tokens; smaller categories silently won't cache (no harm).
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": f"Напиши двуязычную подпись для: {new_item_name}"}],
        )
    except anthropic.AuthenticationError:
        return "", "", "anthropic_auth_failed"
    except anthropic.RateLimitError:
        return "", "", "anthropic_rate_limited"
    except anthropic.APIConnectionError:
        return "", "", "anthropic_connection_error"
    except anthropic.APIStatusError as e:
        return "", "", f"anthropic_api_error_{e.status_code}"
    except Exception as e:
        logger.warning("anthropic call failed: %s", e)
        return "", "", f"anthropic_unknown_error: {type(e).__name__}"

    raw = ""
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            raw = (block.text or "").strip()
            break

    # Parse "RU: ...\nEN: ..." lines tolerantly. Accept either order, accept
    # extra whitespace, accept variants ("Russian:", "English:").
    ctx_ru, ctx_en = "", ""
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        low = s.lower()
        if low.startswith("ru:") or low.startswith("russian:") or low.startswith("ру:"):
            ctx_ru = s.split(":", 1)[1].strip()
        elif low.startswith("en:") or low.startswith("english:") or low.startswith("ен:"):
            ctx_en = s.split(":", 1)[1].strip()

    # Strip wrapping quotes if Claude added them anyway
    def _strip_quotes(t):
        while t and t[0] in '«"\'' and t[-1] in '»"\'':
            t = t[1:-1].strip()
        return t[:200].rstrip() if len(t) > 200 else t
    ctx_ru = _strip_quotes(ctx_ru)
    ctx_en = _strip_quotes(ctx_en)

    if not ctx_ru or not ctx_en:
        return ctx_ru, ctx_en, "anthropic_response_unparseable"
    return ctx_ru, ctx_en, None


def _apply_item_submission(submission_row: dict) -> dict:
    """Auto-apply of an approved item-type submission to categories.json.

    Audit-6 M1: DISABLED. The previous implementation (audit-5 H1) added
    the new item to category.items + ran the validator + saved. But the
    bilingual-coverage validator (T1) requires every item to be referenced
    by at least one regular archetype's `triggers` array, NOT just the
    defaultArchetype. We have no UI/UX for the moderator to choose which
    archetypes to attach the new item to during the approve action, so the
    validator always failed and rolled back. Auto-apply was effectively a
    no-op + always-error workflow.

    Until that UI exists, we explicitly skip auto-apply: admin can still
    approve the submission status (the moderation decision is recorded),
    but the item is NOT inserted into categories.json. Moderator manually
    adds the item via the admin Categories editor where they can pick the
    target archetypes properly.

    Returns a dict {applied: bool, error: str|None, ctx: str|None,
    item_id: str|None} matching the previous shape so the caller (PATCH
    /api/admin/submissions/{id}) doesn't need to change.
    """
    return {
        "applied": False,
        "error": "manual_categorization_required",
        "ctx": None,
        "item_id": None,
    }


def _apply_item_submission_disabled_internal(submission_row: dict) -> dict:
    """Original auto-apply implementation, kept for reference. Do not call —
    use _apply_item_submission() above which short-circuits with
    manual_categorization_required.
    """
    out = {"applied": False, "error": None, "ctx": None, "item_id": None}

    target_id = submission_row.get("target_category_id")
    if not target_id:
        out["error"] = "no_target_category_id"
        return out

    name = (submission_row.get("title") or "").strip()
    if not name:
        out["error"] = "empty_title"
        return out

    if not CATEGORIES_JSON_PATH.exists():
        out["error"] = "categories_json_missing"
        return out

    try:
        data = json.loads(CATEGORIES_JSON_PATH.read_text(encoding='utf-8'))
    except Exception as e:
        out["error"] = f"categories_load_failed: {e}"
        return out

    cat = next((c for c in data if c.get("id") == target_id), None)
    if not cat:
        out["error"] = f"target_category_not_found: {target_id}"
        return out

    # De-dup: if an item with the same lowercase name exists, skip insertion.
    existing_names = {(it.get("name") or "").strip().lower() for it in (cat.get("items") or [])}
    if name.lower() in existing_names:
        out["error"] = "item_already_exists"
        return out

    # Audit-5 H1: generate BILINGUAL ctx (RU + EN) so the new item satisfies
    # the bilingual covenant enforced by _validate_category_for_publish.
    # If Claude is unavailable, refuse the auto-apply (admin can do it
    # manually via the per-item edit UI which has its own translation flow).
    ctx_ru, ctx_en, ctx_err = _generate_item_ctx(cat, name)
    if ctx_err or not ctx_ru or not ctx_en:
        out["error"] = f"ctx_generation_failed: {ctx_err or 'empty_response'}"
        return out

    # name_en: if the title is already ASCII-only (English movie/band/etc),
    # keep it as the EN form. For Cyrillic titles we'd ideally translate via
    # Claude, but here we conservatively reuse `name` — _validate_category
    # only requires name_en to be non-empty when name is set, not that it
    # actually be in English.
    name_en = name if name.isascii() else name

    # Build new item id, ensuring uniqueness within the category.
    base_id = f"{target_id}-{_slugify_id(name)}"
    new_id = base_id
    existing_ids = {it.get("id") for it in (cat.get("items") or [])}
    n = 2
    while new_id in existing_ids:
        new_id = f"{base_id}-{n}"
        n += 1

    # Look up submitter nickname for attribution
    submitter_nick = None
    submitter_user_id = submission_row.get("user_id")
    if submitter_user_id:
        try:
            with db() as conn:
                u = conn.execute("SELECT nickname FROM users WHERE id = ?", (submitter_user_id,)).fetchone()
                if u:
                    submitter_nick = u["nickname"]
        except Exception:
            pass

    new_item = {
        "id": new_id,
        "name": name,
        "name_en": name_en,
        "ctx": ctx_ru,
        "ctx_en": ctx_en,
        "submitted_by": submitter_nick,           # @nick (or null if unknown)
        "submitted_at": now_iso(),                 # ISO timestamp of when item entered the category
    }
    cat.setdefault("items", []).append(new_item)

    # Audit-5 H1: validate the mutated category before persisting. If our
    # auto-generated ctx broke any bilingual / structural rule, roll back
    # the in-memory append and refuse to write — better to leave the
    # submission pending than to corrupt categories.json.
    errors, _warnings = _validate_category_for_publish(cat)
    if errors:
        # Roll back the in-memory append (we mutated cat in place).
        cat["items"].pop()
        out["error"] = "validation_failed: " + "; ".join(errors[:3])
        return out

    # Audit-5 H1: route through _save_categories so we get the rotated
    # backup, the threading lock, and the in-process cache invalidation —
    # all of which the previous direct-tmp-write skipped.
    try:
        _save_categories(data)
    except Exception as e:
        cat["items"].pop()  # roll back in-memory
        out["error"] = f"categories_write_failed: {e}"
        return out

    out["applied"] = True
    out["ctx"] = ctx_ru
    out["item_id"] = new_id
    return out


@app.get("/api/health")
def health():
    with db() as conn:
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        results_count = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
    return {
        "ok": True,
        "ts": now_iso(),
        "version": app.version,
        "users": users_count,
        "results": results_count,
    }


@app.post("/api/register", status_code=201)
def register(body: RegisterIn, response: Response, request: Request):
    # Rate limit: 5 registers / hour per IP — stops bot account flooding without
    # blocking legitimate signup spikes (someone showing the app to 5 friends).
    rate_limit(request, "register", max_attempts=5, window_sec=3600)

    # Defense in depth: frontend already requires the consent checkbox, but
    # an API caller bypassing the UI must still explicitly opt in. Reject
    # registration without consent — GDPR / 152-ФЗ require active consent.
    if not body.consent:
        raise HTTPException(400, "consent_required")

    nick = body.nickname
    email = body.email.lower()
    pw_hash = hash_password(body.password)
    client_ip = real_ip(request)
    client_ua = (request.headers.get("user-agent") or "")[:500]

    with db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE nickname = ? COLLATE NOCASE", (nick,)).fetchone():
            # Nickname is public UX (visible on profile, leaderboards, share
            # cards) so taking-state is not enumeration-sensitive — return
            # specific code so user can pick a different nick.
            raise HTTPException(409, "nickname_taken")
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            # FA-012 fix 2026-05-15: was "email_registered", changed to
            # generic "registration_failed" so attackers can't probe email
            # existence by registering with a fresh nickname + various
            # emails and reading the differentiated error code. Real users
            # with a forgotten account see the generic message + a hint
            # toward password reset (i18n: auth.err.registration.failed).
            raise HTTPException(409, "registration_failed")

        # Resolve referrer (if any). Referrer is "credited" if they exist and
        # aren't trying to refer themselves (impossible since they're already registered).
        referrer_id = None
        if body.referrer_nickname:
            ref_row = conn.execute(
                "SELECT id FROM users WHERE nickname = ? COLLATE NOCASE",
                (body.referrer_nickname.strip(),)
            ).fetchone()
            if ref_row and ref_row['id']:
                referrer_id = ref_row['id']

        conn.execute(
            "INSERT INTO users (nickname, email, password_hash, created_at, last_login_at, referred_by, gender) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nick, email, pw_hash, now_iso(), now_iso(), referrer_id, body.gender),
        )
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        # Grant 'core' consent — covers everything in privacy.html (account
        # storage, processing for service operation, anonymized analytics,
        # disclosed processors, M&A transfer). Writes both consent_state
        # (current) and consent_acceptances (audit log).
        # Optional categories (email_marketing, push_marketing) are NOT
        # granted here — user opts in later via /api/me/consents.
        consent_version = (body.consent_version or "").strip() or CURRENT_CONSENT_VERSION
        _grant_consent(conn, user_id, "core", client_ip, client_ua,
                       kind_suffix="registration", version=consent_version)

        token = make_token()
        expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)).isoformat().replace("+00:00", "Z")
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at, ip, user_agent) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (token, user_id, now_iso(), expires, client_ip, client_ua),
        )

        # Auto-friend admin sees this new user in their friends list immediately
        # (one-way; new user doesn't see admin until they explicitly add back)
        auto_friend_admin(conn, user_id)

        user = dict(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())

    set_session_cookie(response, token)

    # If we credited a referrer, fire achievement check for THEM (so they get
    # their referral-count achievement immediately on the next refresh).
    if referrer_id:
        try:
            check_and_unlock_achievements(referrer_id)
        except Exception as e:
            logger.warning("achievement check after referral failed: %s", e)

    return {"user": public_user(user), "referred_by": referrer_id}


@app.post("/api/login")
def login(body: LoginIn, response: Response, request: Request):
    # Rate limit: 10 attempts / 5 min per IP — slows brute force on user passwords
    # but doesn't punish typo-fingered users. Counts both successes + failures
    # (simpler — and successful login means cookie's set, so subsequent requests
    # don't hit /login).
    rate_limit(request, "login", max_attempts=10, window_sec=300)

    ident = body.email_or_nick.strip()
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? OR nickname = ? COLLATE NOCASE",
            (ident.lower(), ident),
        ).fetchone()
        if not row or not check_password(body.password, row["password_hash"]):
            raise HTTPException(401, "invalid_credentials")

        user = dict(row)
        token = make_token()
        expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)).isoformat().replace("+00:00", "Z")
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at, ip, user_agent) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (token, user["id"], now_iso(), expires, real_ip(request), request.headers.get("user-agent", "")[:500]),
        )
        conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?", (now_iso(), user["id"]))

    set_session_cookie(response, token)
    return {"user": public_user(user)}


# ─── SOCIAL AUTH ENDPOINTS (Phase B, mobile apps) ────────────────────
# Frontend (Capacitor) gets ID token from native flow → POSTs here. Server
# validates token + creates/finds user + returns session cookie.

def _do_social_signin(provider: str, decoded: dict, body: SocialAuthIn,
                       response: Response, request: Request) -> dict:
    """Shared logic for /api/auth/google and /api/auth/apple. The provider-
    specific bits (token validation) happen in the route, then the resulting
    decoded claim dict is passed here for user resolution + session creation.

    CONSENT (UX-1, 2026-05-11): consent is no longer required up-front. It
    is enforced only inside _social_signin_or_create when path 3 (new
    account creation) is hit. Existing-user logins (paths 1 & 2) skip the
    check entirely — user already consented at original registration.
    """
    sub = (decoded.get("sub") or "").strip()
    if not sub:
        raise HTTPException(400, "invalid_token_no_sub")
    email = (decoded.get("email") or "").strip().lower() or None
    # email_verified comes back from Google as bool, from Apple as either
    # bool or "true"/"false" string. Normalize defensively. Default to False
    # — if the provider didn't tell us, we treat it as unverified.
    ev_raw = decoded.get("email_verified", False)
    if isinstance(ev_raw, str):
        email_verified = ev_raw.strip().lower() == "true"
    else:
        email_verified = bool(ev_raw)
    # Fallback nickname for new-account path: Google's `given_name` first,
    # then `name`, then "user". Server-side suggest_nickname will append
    # numeric suffix if it collides. Existing users (paths 1/2) ignore this.
    fallback_nick = (body.nickname or "").strip() or _sanitize_nick_from_token(decoded)

    with db() as conn:
        user_id, final_nick, is_new = _social_signin_or_create(
            conn=conn, provider=provider, provider_user_id=sub,
            email=email, email_verified=email_verified,
            requested_nickname=fallback_nick, request=request,
            consent=bool(body.consent),
        )

        token = make_token()
        expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)
                   ).isoformat().replace("+00:00", "Z")
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at, ip, user_agent) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (token, user_id, now_iso(), expires,
             real_ip(request), (request.headers.get("user-agent") or "")[:500]),
        )
        conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?",
                     (now_iso(), user_id))
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    set_session_cookie(response, token)
    return {
        "user": public_user(dict(user_row)),
        "is_new_user": is_new,
        "final_nickname": final_nick,  # may differ from requested if auto-suggested
    }


@app.post("/api/auth/google")
def auth_google(body: SocialAuthIn, response: Response, request: Request):
    """Sign in / register via Google ID token (from Capacitor Google Auth plugin)."""
    rate_limit(request, "auth_google", max_attempts=10, window_sec=300)
    decoded = _validate_google_id_token(body.id_token)
    if not decoded:
        raise HTTPException(401, "invalid_google_token")
    return _do_social_signin("google", decoded, body, response, request)


@app.post("/api/auth/apple")
def auth_apple(body: SocialAuthIn, response: Response, request: Request):
    """Sign in / register via Apple ID token (from Capacitor Apple Sign-In plugin)."""
    rate_limit(request, "auth_apple", max_attempts=10, window_sec=300)
    decoded = _validate_apple_id_token(body.id_token)
    if not decoded:
        raise HTTPException(401, "invalid_apple_token")
    return _do_social_signin("apple", decoded, body, response, request)


@app.post("/api/users/nickname/check")
def check_nickname(body: NicknameCheckIn, request: Request):
    """Check if a nickname is available; if not, suggest an alternative.
    Used by the welcome screen "Как тебя зовут?" so user gets instant feedback
    before trying to register and getting a 409.

    Returns:
      {"available": true, "nickname": "Anna"}                 if free
      {"available": false, "suggestion": "Anna_2"}            if taken, alt found
      {"available": false, "suggestion": null}                if all variants taken
    """
    rate_limit(request, "nickname_check", max_attempts=60, window_sec=60)
    nick = body.nickname.strip()
    if not NICK_RE.match(nick):
        raise HTTPException(422, "invalid_nickname_chars")
    with db() as conn:
        taken = conn.execute(
            "SELECT 1 FROM users WHERE nickname = ? COLLATE NOCASE", (nick,)
        ).fetchone()
        if not taken:
            return {"available": True, "nickname": nick}
        suggestion = _suggest_nickname(conn, nick)
    return {"available": False, "suggestion": suggestion}


@app.post("/api/logout")
def logout(response: Response, session: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    if session:
        with db() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (session,))
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


# ─── PASSWORD RESET (chunk 6, 2026-05-09) ──────────────────────────
# Standard 2-step flow:
#   1. POST /api/password-reset/request {email}
#      → server generates token, emails reset link, returns 202 (always)
#   2. User clicks link in email → frontend opens with #reset=TOKEN
#      (audit-10 P1: token in URL FRAGMENT, not query — fragments are
#      not transmitted in HTTP requests, so the bearer-secret can't be
#      logged by nginx, Cloudflare, or any middlebox between user and us)
#   3. POST /api/password-reset/complete {token, new_password}
#      → server validates, updates password, kills all sessions, returns 200
#
# Security:
#   - Always 202 in step 1 (no email enumeration: caller can't tell if
#     the email exists in our DB)
#   - Tokens stored as SHA256 hash, never raw (DB leak doesn't enable replay)
#   - Single-use + 1h expiry
#   - On reset success, ALL sessions for that user are deleted (kicks any
#     potentially-compromised cookies out)
#   - Rate-limit: 3/h per IP for "request", 10/h for "complete"

class PasswordResetRequestIn(BaseModel):
    email: EmailStr
    # Optional explicit language override. Frontend can pass current UI lang
    # (from localStorage) so the email matches what user sees in the app.
    # If omitted, server falls back to Accept-Language header → 'ru' default.
    lang: Optional[str] = Field(default=None, max_length=8)


class PasswordResetCompleteIn(BaseModel):
    token: str = Field(..., min_length=20, max_length=120)
    new_password: str = Field(..., min_length=8, max_length=128)


def _detect_email_lang(request: Request, override: Optional[str] = None) -> str:
    """Pick 'ru' or 'en' for an outbound email.

    Priority:
      1. Explicit override from request body (e.g. frontend's current UI lang)
      2. First language in browser's Accept-Language header
      3. 'ru' default (predominant audience)
    """
    if override:
        ov = override.lower().strip()
        if ov in ("ru", "en"):
            return ov
    al = (request.headers.get("accept-language") or "").lower()
    # Take the FIRST language tag (highest q-value by convention), strip
    # region/subtag/quality. e.g. "en-US,en;q=0.9,ru;q=0.8" → "en"
    if al:
        first = al.split(",")[0].split("-")[0].split(";")[0].strip()
        if first == "ru":
            return "ru"
        if first == "en":
            return "en"
    return "ru"


def _send_reset_email_bg(email: str, subject: str, html_body: str, text_body: str,
                          user_id: int, ip: Optional[str], lang: str) -> None:
    """Background-task wrapper around send_email. Errors are logged but not
    surfaced — caller already returned 202 to the client (no enumeration)."""
    try:
        send_email(to=email, subject=subject, html=html_body, text=text_body)
        logger.info("password_reset_email_sent user_id=%s ip=%s lang=%s", user_id, ip, lang)
    except EmailSendError as e:
        logger.error("password_reset_email_failed user_id=%s err=%s", user_id, e)


from fastapi import BackgroundTasks  # local import keeps top of file tidy


@app.post("/api/password-reset/request", status_code=202)
def password_reset_request(body: PasswordResetRequestIn, request: Request,
                            background_tasks: BackgroundTasks):
    """Request a password reset email. Always returns 202 regardless of
    whether the email is registered (security: no email enumeration).

    Audit re-review M-3: email sending moved to a background task so the
    response timing is identical for found vs. not-found emails. Previously
    the known-email branch took ~hundreds of ms (Resend round-trip) while
    unknown-email returned immediately, making timing-based enumeration
    feasible despite the generic 202 body.
    """
    rate_limit(request, "password_reset_request", max_attempts=6, window_sec=3600)

    email = body.email.lower().strip()
    ip = _client_ip(request)
    lang = _detect_email_lang(request, body.lang)

    with db() as conn:
        user_row = conn.execute(
            "SELECT id, nickname FROM users WHERE email = ? COLLATE NOCASE",
            (email,),
        ).fetchone()

        if user_row:
            raw_token = _generate_password_reset_token(conn, user_row["id"], ip)
            # Audit-10 P1: token in URL FRAGMENT (#) not query (?). Fragments
            # are never sent in HTTP requests by browsers, so the token can't
            # leak into nginx access logs, Cloudflare logs, or any middlebox
            # telemetry between the user's email client and our origin.
            # Frontend reads location.hash on boot.
            reset_url = f"https://isverifiedby.me/#reset={raw_token}"
            template = password_reset_email(
                reset_url,
                nickname=user_row["nickname"],
                lang=lang,
            )
            background_tasks.add_task(
                _send_reset_email_bg,
                email, template["subject"], template["html"], template["text"],
                int(user_row["id"]), ip, lang,
            )
        else:
            # Unknown email — log at info level (not warning, this is a normal
            # case for typos / forgotten which email was used). Still tick up
            # rate-limit so attackers can't enumerate cheaply.
            logger.info("password_reset_unknown_email ip=%s", ip)

    # Generic 202 message — same for found/not-found
    return {
        "ok": True,
        "message": "If that email is registered, a reset link has been sent.",
    }


@app.post("/api/password-reset/complete")
def password_reset_complete(body: PasswordResetCompleteIn, request: Request):
    """Complete password reset using token from email. Updates password +
    kills all sessions for that user.

    Audit-11 P2.b: wrapped in BEGIN IMMEDIATE / COMMIT so token consumption,
    password update, and session kill are atomic. Previously each statement
    autocommitted individually — a failure between consume_token (which
    marks token used_at) and the UPDATE users would have stranded the
    user with a used-but-no-effect token AND unchanged password (and they
    can't request a new reset until rate limit window expires)."""
    rate_limit(request, "password_reset_complete", max_attempts=10, window_sec=3600)

    # Hash OUTSIDE the transaction — bcrypt is slow (intentional) and we
    # don't want to hold the SQLite write lock during it.
    new_hash = hash_password(body.new_password)

    with db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            user_id = _consume_password_reset_token(conn, body.token)
            if not user_id:
                conn.execute("ROLLBACK")
                raise HTTPException(400, "invalid_or_expired_token")

            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, user_id),
            )

            # Kill every existing session — security best practice on password
            # change. User must re-login on every device, including this one.
            sessions_killed = conn.execute(
                "DELETE FROM sessions WHERE user_id = ?", (user_id,)
            ).rowcount

            conn.execute("COMMIT")
        except HTTPException:
            raise
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise

        logger.info("password_reset_complete user_id=%s sessions_killed=%d",
                    user_id, sessions_killed)

    return {
        "ok": True,
        "message": "Password updated. Please sign in with your new password.",
    }


@app.get("/api/me")
def me(session: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    user = get_session_user(session)
    if not user:
        return {"user": None}
    # Streaks (2026-05-11): record today's visit and surface current streak
    # numbers so the frontend can display them on profile + result screens
    # without an extra round-trip. _record_visit is idempotent per user-day,
    # so refreshing the page 100 times today still inserts only one row.
    # check_and_unlock_achievements then evaluates streak achievements
    # ("Неделя", "Месяц", etc) in the same transaction.
    streak_visit = 0
    streak_play = 0
    newly_unlocked: list[str] = []
    try:
        with db() as conn:
            _record_visit(conn, user["id"])
            streak_visit = compute_visit_streak(conn, user["id"])
            streak_play = compute_play_streak(conn, user["id"])
        try:
            newly_unlocked = check_and_unlock_achievements(user["id"])
        except Exception as e:
            logger.warning("achievement check from /api/me failed: %s", e)
    except sqlite3.OperationalError:
        # Table missing on a stale schema (init_db migration hasn't run yet).
        # Don't crash /api/me — streak just shows 0 until next deploy.
        pass

    # Resolve referrer (if any) — frontend uses this to show "invited by @X"
    # in profile or hide the one-time inviter-entry input once set.
    # 2026-05-16 added for profile inviter UI.
    referred_by_id = None
    referred_by_nickname = None
    try:
        rb = user.get("referred_by")
        if rb:
            with db() as conn:
                rb_row = conn.execute(
                    "SELECT id, nickname FROM users WHERE id = ?", (int(rb),)
                ).fetchone()
                if rb_row:
                    referred_by_id = int(rb_row["id"])
                    referred_by_nickname = rb_row["nickname"]
    except Exception:
        pass

    return {
        "user": public_user(user),
        "visit_streak": streak_visit,
        "play_streak": streak_play,
        "newly_unlocked_achievements": newly_unlocked,
        "referred_by_id": referred_by_id,
        "referred_by_nickname": referred_by_nickname,
    }


@app.get("/api/me/consents")
def get_my_consents(user: dict = Depends(require_user)):
    """Return current granular consent state for this user.
    Shape: {consents: {core: {granted, since, version}, email_marketing: {...}, ...},
            mandatory: ['core'], current_version: '2026-05-10'}
    Frontend uses this to render the profile's "My Consents" section.
    """
    with db() as conn:
        state = _get_consent_state(conn, user["id"])
    return {
        "consents": state,
        "mandatory": list(MANDATORY_CONSENT_CATEGORIES),
        "current_version": CURRENT_CONSENT_VERSION,
    }


@app.post("/api/me/consents")
def update_my_consent(body: ConsentUpdateIn, request: Request, user: dict = Depends(require_user)):
    """Opt in or out of an optional consent category.
    - Granting a mandatory category is a no-op (already granted at registration).
    - Revoking a mandatory category returns 400 cannot_revoke_mandatory_consent.
    - Unknown category returns 400 unknown_consent_category.
    Each change writes both consent_state (current) and consent_acceptances
    (audit log) so we can reconstruct the full history.
    """
    rate_limit(request, "consent_update", max_attempts=20, window_sec=300)
    if body.category not in CONSENT_CATEGORIES:
        raise HTTPException(400, "unknown_consent_category")
    client_ip = real_ip(request)
    client_ua = (request.headers.get("user-agent") or "")[:500]
    with db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")
            if body.granted:
                # Grant on a mandatory category that's already granted is a
                # silent refresh of timestamp — fine. Same for re-grant of
                # an already-granted optional category.
                _grant_consent(conn, user["id"], body.category, client_ip, client_ua,
                               kind_suffix="profile_grant")
            else:
                # _revoke_consent rejects mandatory categories with 400.
                _revoke_consent(conn, user["id"], body.category, client_ip, client_ua)
            state = _get_consent_state(conn, user["id"])
            conn.execute("COMMIT")
        except HTTPException:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise
    return {
        "consents": state,
        "mandatory": list(MANDATORY_CONSENT_CATEGORIES),
        "current_version": CURRENT_CONSENT_VERSION,
    }


class SetReferrerIn(BaseModel):
    nickname: str = Field(min_length=2, max_length=24)


@app.post("/api/me/referrer")
def set_my_referrer(body: SetReferrerIn, request: Request,
                     user: dict = Depends(require_user)):
    """One-shot: set referrer for current user by nickname.

    Used by the profile screen's "who invited you" entry (added 2026-05-16).
    The user typically gets referred at REGISTRATION via the referrer_nickname
    param on /api/register (when they came in via a friend's link). But not
    everyone arrives via a tracked link — they may have heard about Tappetite
    from a friend offline, registered cold, and only later want to credit
    that friend. This endpoint covers that case.

    Strictly one-shot: once referred_by is set (either at registration or via
    this endpoint), it CANNOT be changed. Returns 409 referrer_already_set on
    repeat attempts. The atomicity is enforced at SQL level via the WHERE
    clause `AND referred_by IS NULL` — no read-then-write race.

    Validates:
    - nickname maps to an existing user (NOCASE).
    - user isn't referring themselves.
    - user's referred_by is currently NULL.
    """
    rate_limit(request, "set_referrer", max_attempts=10, window_sec=300)
    ref_nick = (body.nickname or "").strip()
    if not ref_nick:
        raise HTTPException(400, "nickname_required")

    with db() as conn:
        ref_row = conn.execute(
            "SELECT id, nickname FROM users WHERE nickname = ? COLLATE NOCASE",
            (ref_nick,),
        ).fetchone()
        if not ref_row:
            raise HTTPException(404, "referrer_not_found")
        ref_id = int(ref_row["id"])
        ref_nickname_canonical = ref_row["nickname"]

        if ref_id == user["id"]:
            raise HTTPException(400, "self_referral")

        # Atomic one-shot. rowcount==0 means either no such user (impossible
        # because require_user) OR referred_by was already set — either way
        # the right response is 409 "already set".
        cur = conn.execute(
            "UPDATE users SET referred_by = ? WHERE id = ? AND referred_by IS NULL",
            (ref_id, user["id"]),
        )
        if cur.rowcount == 0:
            raise HTTPException(409, "referrer_already_set")

    # Fire achievement check for the referrer so their "I invited N people"
    # badge updates immediately. Best-effort — if it throws, we still return ok.
    try:
        check_and_unlock_achievements(ref_id)
    except Exception as e:
        logger.warning("achievement check after late referral failed: %s", e)

    return {
        "ok": True,
        "referred_by_id": ref_id,
        "referred_by_nickname": ref_nickname_canonical,
    }


# ─── FAVORITES (added 2026-05-16) ────────────────────────────────────
# User-selected favorite clusters. After first tournament we ask the user
# what kind of themes they care about (cluster-level), surface those at the
# top of home in a "Тебе ближе" section. Editable later from profile.
# If user dismisses the popup without picking, re-ask after 5 more
# tournaments (frontend computes the threshold).

MAX_FAVORITE_CLUSTERS = 10  # mirrored on frontend; over-cap requests rejected


class SetFavoritesIn(BaseModel):
    # List of cluster names; replaces the user's full favorites set.
    clusters: list[str] = Field(default_factory=list, max_length=MAX_FAVORITE_CLUSTERS)


def _valid_cluster_set() -> set[str]:
    """Compute the set of cluster names currently in the published catalog.
    Used to validate PUT /api/me/favorites input — rejects unknown clusters
    so a scripted user can't store garbage labels."""
    try:
        cats = _load_categories()
    except Exception:
        return set()
    out = set()
    for c in cats:
        name = (c.get("cluster") or "").strip()
        if name:
            out.add(name)
    return out


@app.get("/api/me/favorites")
def get_my_favorites(user: dict = Depends(require_user)):
    """Return the user's favorite clusters + last-dismiss timestamp.
    Frontend uses this to decide whether to show the favorites popup."""
    with db() as conn:
        rows = conn.execute(
            "SELECT cluster_name, set_at FROM user_favorite_clusters "
            "WHERE user_id = ? ORDER BY set_at",
            (user["id"],),
        ).fetchall()
        clusters = [r["cluster_name"] for r in rows]
        # Fetch dismissed_at directly from users (column added 2026-05-16)
        dismissed_at = None
        try:
            row = conn.execute(
                "SELECT favorites_dismissed_at FROM users WHERE id = ?",
                (user["id"],),
            ).fetchone()
            if row:
                dismissed_at = row["favorites_dismissed_at"]
        except Exception:
            pass
    return {
        "clusters": clusters,
        "dismissed_at": dismissed_at,
        # Cap for client display; if it changes server-side, client picks it up.
        "max_count": MAX_FAVORITE_CLUSTERS,
    }


@app.put("/api/me/favorites")
def set_my_favorites(body: SetFavoritesIn, request: Request,
                      user: dict = Depends(require_user)):
    """Replace the user's favorite-clusters set. Empty list is valid (clears).
    Validates each cluster against the live catalog so unknown labels can't
    be stored. Returns the canonical accepted list."""
    rate_limit(request, "set_favorites", max_attempts=20, window_sec=300)
    valid = _valid_cluster_set()
    requested = list(dict.fromkeys((c or "").strip() for c in body.clusters if c))
    # Filter to valid + dedup while preserving order
    accepted = [c for c in requested if c in valid][:MAX_FAVORITE_CLUSTERS]
    rejected = [c for c in requested if c not in valid]

    now = now_iso()
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Replace strategy: wipe all then insert. Tiny table so cost is
            # negligible. Atomic via the transaction.
            conn.execute("DELETE FROM user_favorite_clusters WHERE user_id = ?", (user["id"],))
            for c in accepted:
                conn.execute(
                    "INSERT INTO user_favorite_clusters (user_id, cluster_name, set_at) "
                    "VALUES (?, ?, ?)",
                    (user["id"], c, now),
                )
            # If user explicitly sets favorites we clear the dismissed_at —
            # they engaged, so the re-prompt logic shouldn't keep nagging.
            try:
                conn.execute(
                    "UPDATE users SET favorites_dismissed_at = NULL WHERE id = ?",
                    (user["id"],),
                )
            except Exception:
                pass
            conn.execute("COMMIT")
        except Exception:
            try: conn.execute("ROLLBACK")
            except Exception: pass
            raise

    return {
        "ok": True,
        "clusters": accepted,
        "rejected": rejected,
        "count": len(accepted),
    }


@app.post("/api/me/favorites/dismiss")
def dismiss_favorites_prompt(request: Request,
                              user: dict = Depends(require_user)):
    """Record that the user dismissed the favorites popup without picking.
    Sets favorites_dismissed_at to now; frontend uses this + count of
    subsequent tournaments to decide whether to re-prompt after 5."""
    rate_limit(request, "dismiss_favorites", max_attempts=20, window_sec=300)
    now = now_iso()
    with db() as conn:
        try:
            conn.execute(
                "UPDATE users SET favorites_dismissed_at = ? WHERE id = ?",
                (now, user["id"]),
            )
        except Exception:
            # Column may not exist on a stale schema — fail silently, frontend
            # treats the absence as "never dismissed" which is acceptable.
            pass
    return {"ok": True, "dismissed_at": now}


@app.get("/i/{nickname}")
def invite_link_redirect(nickname: str, request: Request):
    """Smart invite-link router. User shares https://isverifiedby.me/i/Uncle.

    Behaviour depends on the recipient's platform (sniffed from User-Agent):

    - Android UA, app NOT installed → 302 to Play Store URL with the official
      `referrer` query param. Google captures that during install, and the
      app reads it back via InstallReferrerClient API on first launch — that
      gives us proper attribution for ads-free deferred deep linking, zero
      third-party SDK.
    - Android UA, app IS installed → THIS ENDPOINT IS NEVER REACHED. Android
      App Links interception (per assetlinks.json + intent-filter on this
      path) opens the app directly with the URL, browser/server bypassed.
      The app's WebView lands on /i/<nickname>, the same JS frontend reads
      the path and sets LS_PENDING_REFERRER. Existing register-flow consumes.
    - iOS UA → for now, redirect to web with ?ref=<nickname>. TODO when iOS
      app ships: redirect to App Store + run fingerprint/Branch attribution.
    - Anything else (desktop, other) → web with ?ref=<nickname>.

    Cookie `tappetite_ref` is set on every response as a 30-day fallback.
    The web frontend reads URL param first, falls back to cookie if param
    missing (e.g. if some intermediate redirect ate the query string).
    """
    from fastapi.responses import RedirectResponse
    import urllib.parse as _url

    nick = (nickname or "").strip()
    # Cheap validation; deep validation is done at register-time.
    if not nick or len(nick) > 24 or len(nick) < 2:
        raise HTTPException(404, "invalid_nickname")

    ua = (request.headers.get("user-agent") or "").lower()
    is_android = "android" in ua
    is_ios = ("iphone" in ua) or ("ipad" in ua) or ("ipod" in ua)
    # "wv)" is the Android WebView marker (vs full Chrome) — set by Android
    # WebView UA per spec. If a request comes in with this token it means
    # the user already has the Tappetite app installed and Android App Links
    # routed the click to the app, whose Capacitor WebView is now opening
    # the URL itself. We must NOT redirect to Play Store in that case
    # (Capacitor allowNavigation would block the cross-origin nav). Treat
    # like a normal web user — redirect to /?ref= so the existing in-page
    # JS captures the referrer into LS_PENDING_REFERRER.
    is_webview = "wv)" in ua or "; wv)" in ua
    nick_enc = _url.quote(nick)

    if is_android and not is_webview:
        target = (
            "https://play.google.com/store/apps/details?"
            f"id=me.isverifiedby.pickgame&referrer=ref%3D{nick_enc}"
        )
    else:
        # iOS, Android-in-WebView (app already installed), desktop, everything
        # else — land on web with ?ref=. The WebView path means the user
        # already has the app and the frontend JS captures the referrer via
        # the URL param. iOS will get its own App Store branch once the iOS
        # build ships.
        target = f"https://isverifiedby.me/?ref={nick_enc}"

    response = RedirectResponse(url=target, status_code=302)
    # Cookie fallback for the rare case where query param gets stripped in
    # transit (some link-shortener proxies, certain in-app browsers, etc).
    # Frontend prefers URL param when both are present.
    response.set_cookie(
        key="tappetite_ref",
        value=nick,
        max_age=30 * 24 * 3600,
        path="/",
        httponly=False,  # JS on landing reads this to populate LS_PENDING_REFERRER
        samesite="lax",
        secure=True,
    )
    return response


@app.post("/api/results", status_code=201)
def save_result(body: ResultIn, request: Request, user: dict = Depends(require_user)):
    # Audit-6 H2: server-side validation of submitted tournament result.
    # Previously the server trusted EVERY field from the client — fake
    # category_id, fake item IDs, fake names, fake battles_played → all
    # accepted into the dataset that powers stats, friend compare, future
    # social/dating matching. Now we:
    #   - Verify category_id exists in categories.json
    #   - Verify top1/top2/top3 item IDs all exist in that category
    #   - SERVER-RESOLVE category_name + top*_name (client-supplied values
    #     are ignored to prevent display spoofing)
    #   - Sanity-clamp battles_played and duration_sec to realistic ranges
    #   - Rate-limit 100 saves per IP per hour
    #   - items_count comes from server, not client
    # archetype_name/body remain client-supplied: re-deriving them server-
    # side would require porting the full archetype-matching engine; for
    # now we accept them but length-limit via Pydantic Field already.
    rate_limit(request, "save_result", max_attempts=100, window_sec=3600)

    cats = _load_categories()
    cat = next((c for c in cats if c.get("id") == body.category_id), None)
    if not cat:
        raise HTTPException(422, "unknown_category")
    items_by_id = {it.get("id"): it for it in (cat.get("items") or [])}
    if body.top1_id not in items_by_id:
        raise HTTPException(422, "unknown_top1_id")
    if body.top2_id and body.top2_id not in items_by_id:
        raise HTTPException(422, "unknown_top2_id")
    if body.top3_id and body.top3_id not in items_by_id:
        raise HTTPException(422, "unknown_top3_id")

    # Server-authoritative names (override whatever the client sent)
    server_category_name = cat.get("name") or body.category_id
    server_top1_name = items_by_id[body.top1_id].get("name") or body.top1_id
    server_top2_name = items_by_id[body.top2_id].get("name") if body.top2_id else None
    server_top3_name = items_by_id[body.top3_id].get("name") if body.top3_id else None
    server_items_count = len(cat.get("items") or [])

    # Sanity-validate tournament metadata. Audit-7 P1.2 hardening, refined
    # again in audit-8 P2.
    #
    # battles_played: a single-elimination bracket of N items plays exactly
    # (N - 1) battles regardless of N being a power of two — byes don't
    # contribute battles. Audit-8 P2.b note: previously this used
    # recommended_tournament_size, but several categories have items.length
    # > recommended (e.g. hollywood_actors_50plus has 18 items, rec=16).
    # Frontend currently plays cat.items.slice() (all items), so the real
    # battles_played = items_count - 1. We validate against items_count
    # primarily, with rec_size as the lower-bound floor for safety.
    items_count = server_items_count
    rec_size = int(cat.get("recommended_tournament_size") or 16)
    expected_min = max(1, min(items_count, rec_size) - 1)
    expected_max = max(items_count - 1, rec_size - 1) + 5  # +5 slack for replays/skips
    bp = body.battles_played or 0
    if bp < expected_min or bp > expected_max:
        raise HTTPException(422, "battles_played_out_of_range")
    # Duration: REJECT rather than clamp (audit-7 P1.2). Physical floor
    # ~300ms per battle for a real human tap; anything faster is scripted.
    # Audit-8 P2.a: math.ceil instead of int() — int(15 * 0.3) = 4, but
    # the intent of "minimum 0.3s per battle" rounds UP to 5 for a 15-tap
    # tournament. Without ceil() the speed floor was slightly leakier than
    # advertised.
    ds = body.duration_sec or 0
    physical_min_sec = max(2, math.ceil(bp * 0.3))
    if ds < physical_min_sec:
        raise HTTPException(422, "duration_implausibly_fast")
    if ds > 86400:
        raise HTTPException(422, "duration_implausibly_slow")

    with db() as conn:
        # Dedup: if client_id sent and same (user_id, client_id) already exists,
        # return the existing row instead of inserting a duplicate. Makes the
        # endpoint idempotent against retries / double-taps / network jitter.
        if body.client_id:
            existing = conn.execute(
                "SELECT * FROM results WHERE user_id = ? AND client_id = ?",
                (user["id"], body.client_id)
            ).fetchone()
            if existing:
                row = dict(existing)
                return {"result": row, "deduped": True, "newly_unlocked_achievements": []}

        conn.execute(
            """
            INSERT INTO results
              (user_id, category_id, category_name,
               top1_id, top1_name, top2_id, top2_name, top3_id, top3_name,
               archetype_name, archetype_body,
               battles_played, duration_sec, completed_at, is_public, items_count, client_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"], body.category_id, server_category_name,
                body.top1_id, server_top1_name,
                body.top2_id, server_top2_name,
                body.top3_id, server_top3_name,
                body.archetype_name, body.archetype_body,
                bp, ds,
                now_iso(), 1 if body.is_public else 0,
                server_items_count,
                body.client_id,
            ),
        )
        rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        row = dict(conn.execute("SELECT * FROM results WHERE id = ?", (rid,)).fetchone())
        # Phase C trigger #1 (2026-05-12): fan out a push to mutual friends
        # who have notifications enabled, with a computed match-score if the
        # friend has played the same category. Done inside the same conn so
        # we read consistent friend + result data; the actual HTTPS POSTs to
        # push services happen synchronously inline (~50-200ms per friend
        # who has subs). For high-volume users this should move to a worker
        # queue, but at current scale (<5 friends typical) it's fine.
        try:
            notify_friends_of_completion(conn, user["id"], user["nickname"], row)
        except Exception as e:
            logger.warning("friend-push fanout failed: %s", e)
    # After save: opportunistic achievement check (results_count, clusters_played,
    # coverage_percent, speed-based ones may have changed). Doesn't block response.
    newly_unlocked = []
    try:
        newly_unlocked = check_and_unlock_achievements(user["id"])
    except Exception as e:
        logger.warning("achievement check after save_result failed: %s", e)
    return {"result": row, "newly_unlocked_achievements": newly_unlocked}


@app.get("/api/results")
def list_results(user: dict = Depends(require_user), limit: int = 50):
    if limit > 200:
        limit = 200
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM results WHERE user_id = ? ORDER BY completed_at DESC LIMIT ?",
            (user["id"], limit),
        ).fetchall()
    return {"results": [dict(r) for r in rows]}


# ─── WEB PUSH ENDPOINTS (2026-05-11) ─────────────────────────────

@app.get("/api/push/config")
def push_config():
    """Public endpoint — returns the VAPID public key the browser needs
    when calling pushManager.subscribe({applicationServerKey: ...}).
    Frontend caches this once on boot. `enabled` flag tells the UI
    whether to even offer the 'enable notifications' affordance (false
    if VAPID env isn't fully set up server-side)."""
    return {
        "enabled": push_is_configured(),
        "public_key": VAPID_PUBLIC_KEY if push_is_configured() else "",
    }


@app.get("/api/push/status")
def push_status(user: dict = Depends(require_user)):
    """How many active push subscriptions does the current user have?
    Used by the profile-page toggle to render the right state (on/off).
    Note: this is across all devices — if the user has Chrome on desktop
    AND Safari on iPhone subscribed, count is 2."""
    with db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM push_subscriptions WHERE user_id = ?",
            (user["id"],),
        ).fetchone()[0]
    return {"subscribed": count > 0, "count": int(count)}


@app.post("/api/push/subscribe", status_code=201)
def push_subscribe(body: PushSubscribeIn,
                    request: Request,
                    user: dict = Depends(require_user)):
    """Persist a push subscription for the current user. Same endpoint can
    be called many times (re-subscribe, page-refresh) — we use INSERT
    OR REPLACE on the unique endpoint constraint so the row gets refreshed
    with the latest p256dh/auth + user_agent. Returns the row id."""
    if not push_is_configured():
        raise HTTPException(503, "push_not_configured")
    rate_limit(request, "push_subscribe", max_attempts=10, window_sec=600)
    ua = (request.headers.get("user-agent") or "")[:300]
    with db() as conn:
        # Upsert by endpoint: same browser/device subscribing again replaces
        # its keys (browsers occasionally rotate them).
        conn.execute(
            "INSERT INTO push_subscriptions "
            "(user_id, endpoint, p256dh, auth, user_agent, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(endpoint) DO UPDATE SET "
            "  user_id = excluded.user_id, "
            "  p256dh = excluded.p256dh, "
            "  auth = excluded.auth, "
            "  user_agent = excluded.user_agent, "
            "  last_error = NULL, "
            "  failure_count = 0",
            (user["id"], body.endpoint, body.p256dh, body.auth, ua, now_iso()),
        )
        row = conn.execute(
            "SELECT id FROM push_subscriptions WHERE endpoint = ?",
            (body.endpoint,),
        ).fetchone()
    return {"id": row["id"] if row else None, "ok": True}


@app.post("/api/push/unsubscribe", status_code=204)
def push_unsubscribe(body: PushUnsubscribeIn,
                      user: dict = Depends(require_user)):
    """Remove a subscription by endpoint. Called when user toggles off in
    profile OR when the SW reports that the browser invalidated it. Only
    the endpoint is required (no keys) since DELETE is by URL match."""
    with db() as conn:
        conn.execute(
            "DELETE FROM push_subscriptions WHERE user_id = ? AND endpoint = ?",
            (user["id"], body.endpoint),
        )
    return None


@app.post("/api/push/fcm/subscribe", status_code=201)
def push_fcm_subscribe(body: FcmTokenSubscribeIn,
                        request: Request,
                        user: dict = Depends(require_user)):
    """Persist an FCM device token for native push delivery. Same token can
    be sent multiple times (re-launches, token rotation, plugin re-register)
    — UPSERT on the unique token constraint refreshes last_seen_at + clears
    any prior error/failure-count without inserting a duplicate row.
    Token rotation: if FCM gives Capacitor a NEW token for the same physical
    device (which can happen on reinstall, OS upgrade, or 60-day idle), the
    old row stays in the DB until cleaned up by next send failure. That's
    OK — we'd just waste one send attempt before deleting the dead token."""
    rate_limit(request, "push_fcm_subscribe", max_attempts=20, window_sec=600)
    now = now_iso()
    with db() as conn:
        conn.execute(
            "INSERT INTO push_fcm_tokens "
            "(user_id, token, platform, created_at, last_seen_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(token) DO UPDATE SET "
            "  user_id = excluded.user_id, "
            "  platform = excluded.platform, "
            "  last_seen_at = excluded.last_seen_at, "
            "  last_error = NULL, "
            "  failure_count = 0",
            (user["id"], body.token, body.platform, now, now),
        )
        row = conn.execute(
            "SELECT id FROM push_fcm_tokens WHERE token = ?",
            (body.token,),
        ).fetchone()
    return {"id": row["id"] if row else None, "ok": True}


@app.post("/api/push/fcm/unsubscribe", status_code=204)
def push_fcm_unsubscribe(body: FcmTokenUnsubscribeIn,
                          user: dict = Depends(require_user)):
    """Remove an FCM token. Called when user toggles off push in profile
    OR when the client itself decides to wipe (logout, reset). Scoped by
    user_id so a stolen/leaked token can't delete another user's row."""
    with db() as conn:
        conn.execute(
            "DELETE FROM push_fcm_tokens WHERE user_id = ? AND token = ?",
            (user["id"], body.token),
        )
    return None


@app.post("/api/admin/push/test")
def admin_push_test(body: AdminPushTestIn,
                     _role: str = Depends(require_admin),
                     actor: dict = Depends(get_admin_actor)):
    """Admin: send a test push to the user with the given nickname. Used
    to validate VAPID setup end-to-end without wiring up real triggers."""
    if not push_is_configured():
        raise HTTPException(503, "push_not_configured")
    with db() as conn:
        row = conn.execute(
            "SELECT id, nickname FROM users WHERE nickname = ? COLLATE NOCASE",
            (body.nickname,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "user_not_found")
        result = send_push_to_user(int(row["id"]), {
            "title": body.title or "Тест Tappetite",
            "body": body.body or "Если ты это видишь — пуши работают.",
            "url": "/",
            "tag": "admin-test",
        })
        log_admin_action(conn, actor, "push_test_send", row["nickname"], {
            "to_user_id": row["id"],
            "result": result,
        })
    return {"ok": True, "result": result, "to": row["nickname"]}


# Phase C trigger #5/#6/#7 (2026-05-12) — cron-based pushes. The script in
# scripts/notif_cron.sh (systemd timer) calls this endpoint once a day,
# typically at 18:00 Asia/Almaty (13:00 UTC). It handles three batches in
# a single pass so we don't have to set up three separate timers:
#
#   #5 daily — users with push subs who DID visit today: tournament-of-the-day
#      reminder. Skipped if user already played a tournament today (no need
#      to nudge an active player).
#   #6 comeback — users who haven't visited for 7+ days: bring-back push.
#      Capped at one per (user, week) so we don't hammer dropouts.
#   #7 streak-under-threat — users with visit_streak ≥3 who haven't visited
#      TODAY: "your X-day streak is at risk". Only sent if the streak is
#      currently alive (yesterday counts) — we time this for late evening
#      so the user has a chance to react.
def _notify_submission_approved(submission_user_id: int, kind: str,
                                 title: str, category_id: str | None = None) -> None:
    """Push the submitter when their submission gets approved.
    Called from both approval paths:
      - apply-from-json (category publish)
      - PATCH submissions {status='approved'} (item add)
    Silent best-effort — if push fails (no tokens, FCM down, etc) we just
    log a warning, don't break the approval flow.

    `kind` ∈ {'category', 'item'} — drives the push copy.
    `title` — the submission title shown in the push body (quoted).
    `category_id` — if known, opens that category directly via deep link.
    """
    if not submission_user_id:
        return
    title = (title or "тема").strip()
    if kind == "category":
        push_title = "Твою тему одобрили!"
        push_body  = f"«{title}» теперь в каталоге — открой и сыграй"
    else:  # item
        push_title = "Твой вариант добавили!"
        push_body  = f"«{title}» теперь в одной из тем — спасибо"
    payload = {
        "title": push_title,
        "body":  push_body,
        "url":   (f"/?cat={category_id}" if category_id else "/"),
        "tag":   f"submission_approved:{kind}",
    }
    try:
        send_push_to_user(submission_user_id, payload)
    except Exception as e:
        logger.warning("submission-approved push failed for uid=%s: %s",
                       submission_user_id, e)


def _pick_user_daily_cat(conn, uid: int, default_cat: dict,
                           real_cats: list, today: str) -> dict | None:
    """Pick the best daily-push category for ONE user. Logic ladder:

      1. Use the global `default_cat` (same for everyone today) if user
         hasn't played it before. This preserves the "shared theme of the
         day" social signal whenever possible.
      2. Else look for an unplayed cat in the user's FAVORITE clusters
         (from user_favorite_clusters table, set via the favorites popup).
         Pick deterministic by hash(uid + today) so repeat batch runs land
         on the same suggestion.
      3. Else any unplayed cat, same deterministic pick.
      4. Else None (user has played everything; caller skips silently).

    Added 2026-05-16 v2 to fix "we pushed AB21 a tournament she already
    played" bug + leverage favorites for engagement personalization.
    """
    import hashlib as _hashlib

    default_id = default_cat.get("id") if default_cat else None
    if default_id:
        played_default = bool(conn.execute(
            "SELECT 1 FROM results WHERE user_id = ? AND category_id = ? LIMIT 1",
            (uid, default_id),
        ).fetchone())
        if not played_default:
            return default_cat

    # User already played the global daily cat. Find an alternative.
    played_ids = set(
        r["category_id"] for r in conn.execute(
            "SELECT DISTINCT category_id FROM results WHERE user_id = ?", (uid,)
        ).fetchall()
        if r["category_id"]
    )
    unplayed = [c for c in real_cats if c.get("id") and c.get("id") not in played_ids]
    if not unplayed:
        return None

    # Deterministic per-user pick — same suggestion if batch re-runs today.
    def _det_pick(cats: list) -> dict:
        if len(cats) == 1:
            return cats[0]
        key = f"{uid}-{today}".encode("utf-8")
        idx = int(_hashlib.md5(key).hexdigest(), 16) % len(cats)
        return cats[idx]

    # Tier 1: favorites-aware. Look at this user's favorite clusters and
    # filter unplayed to those clusters first. If they have favorites set
    # AND at least one unplayed cat lives in those clusters, use that.
    fav_clusters = set(
        r["cluster_name"] for r in conn.execute(
            "SELECT cluster_name FROM user_favorite_clusters WHERE user_id = ?",
            (uid,),
        ).fetchall()
    )
    if fav_clusters:
        fav_unplayed = [c for c in unplayed if c.get("cluster") in fav_clusters]
        if fav_unplayed:
            return _det_pick(fav_unplayed)

    # Tier 2: any unplayed cat
    return _det_pick(unplayed)


@app.post("/api/admin/notif/run-daily-batch")
def admin_run_daily_batch(_role: str = Depends(require_admin),
                          actor: dict = Depends(get_admin_actor)):
    """Run the daily push-notification batch (5+6+7). Idempotent per-day
    via tagging — repeat runs the same day will replace banners, not stack.
    Returns counts per task."""
    if not push_is_configured():
        raise HTTPException(503, "push_not_configured")

    today = _streak_today()
    yesterday = (datetime.fromisoformat(today).date() - timedelta(days=1)).isoformat()
    week_ago = (datetime.fromisoformat(today).date() - timedelta(days=7)).isoformat()

    summary = {
        "daily_sent": 0,
        "comeback_sent": 0,
        "streak_at_risk_sent": 0,
        "errors": 0,
    }

    with db() as conn:
        # Cache: list of currently-published category names for the daily theme.
        try:
            all_cats = _load_categories()
            real_cats = [c for c in all_cats if not c.get("is_name_tournament")
                          and not c.get("hidden")]
        except Exception:
            real_cats = []

        # Pick "tournament of the day" — deterministic by date so the same
        # category surfaces to everyone today (lets users compare results).
        daily_cat = None
        if real_cats:
            # Hash today's date to a category index — stable across the run.
            import hashlib as _hashlib
            idx = int(_hashlib.md5(today.encode()).hexdigest(), 16) % len(real_cats)
            daily_cat = real_cats[idx]

        # Iterate all users with at least one push channel — EITHER web push
        # (push_subscriptions) OR native FCM (push_fcm_tokens). Doing per-user
        # checks (vs. SQL aggregation) keeps the logic readable; volume is
        # small enough that the cost is negligible.
        # 2026-05-16 fix: was JOIN push_subscriptions only — that's web push;
        # native Android app users have tokens in push_fcm_tokens instead, so
        # they were silently excluded from every daily/comeback/streak push.
        # Result: 0 sent every day since FCM-enabled v0.1.1 shipped because
        # nobody happens to have web push enabled.
        users = conn.execute(
            "SELECT DISTINCT u.id, u.nickname FROM users u "
            "WHERE u.id IN ("
            "  SELECT user_id FROM push_subscriptions "
            "  UNION "
            "  SELECT user_id FROM push_fcm_tokens "
            ")"
        ).fetchall()

        for u in users:
            uid = int(u["id"])
            nick = u["nickname"]

            # Was the user active TODAY?
            today_visited = bool(conn.execute(
                "SELECT 1 FROM user_daily_visits WHERE user_id = ? AND visit_date = ?",
                (uid, today),
            ).fetchone())

            # Last visit date — used for both comeback (>=7 days ago) and
            # streak-at-risk (yesterday but not today).
            last_visit_row = conn.execute(
                "SELECT visit_date FROM user_daily_visits WHERE user_id = ? "
                "ORDER BY visit_date DESC LIMIT 1",
                (uid,),
            ).fetchone()
            last_visit = last_visit_row["visit_date"] if last_visit_row else None

            # Played at least one tournament today?
            played_today = bool(conn.execute(
                "SELECT 1 FROM results WHERE user_id = ? "
                "AND substr(completed_at, 1, 10) = ? LIMIT 1",
                (uid, today),
            ).fetchone())

            # ─── #5 Daily reminder ─────────────────────────────────
            # Only send if user visited today AND hasn't played a tournament
            # yet AND we have a featured-of-the-day. Visited-today gate avoids
            # double-pushing dropouts (they get the comeback push instead).
            if today_visited and not played_today and daily_cat:
                # 2026-05-16 v2: smart per-user daily cat. Logic ladder:
                #   1. Use the global daily_cat IF user hasn't played it yet.
                #   2. Else try to pick an unplayed cat from user's FAVORITE
                #      clusters (set via the favorites popup) — surfaces
                #      taste-aligned content first.
                #   3. Else pick any unplayed cat, deterministic by (uid+today)
                #      so re-runs same day land on same suggestion.
                #   4. Else (truly played everything) → silent skip.
                # Previous version (v1, 2026-05-16) just skipped when daily_cat
                # was already played — wasted re-engagement opportunity.
                # Reported by user after AB21 got push for already-played cat.
                effective_cat = _pick_user_daily_cat(
                    conn, uid, daily_cat, real_cats, today
                )
                if not effective_cat:
                    # User has played everything → silent skip (rare for now,
                    # less rare as users mature). Could route to a separate
                    # "exhausted" push later if it matters.
                    pass
                else:
                    cat_name = effective_cat.get("name") or effective_cat.get("id")
                    try:
                        res = send_push_to_user(uid, {
                            "title": "Турнир дня",
                            "body": f"«{cat_name}» — 4 минуты, узнай свой топ-3",
                            "url": f"/?cat={effective_cat.get('id', '')}",
                            "tag": f"daily:{today}",
                        })
                        if res.get("sent"):
                            summary["daily_sent"] += 1
                    except Exception as e:
                        logger.warning("daily push failed for uid=%s: %s", uid, e)
                        summary["errors"] += 1

            # ─── #6 Comeback (no activity for 7+ days) ─────────────
            # Only send if last_visit is at least week_ago (or never). Tagged
            # so we don't double-fire if cron runs twice a day.
            elif last_visit and last_visit <= week_ago:
                try:
                    res = send_push_to_user(uid, {
                        "title": "Соскучились!",
                        "body": "Прошла неделя — у нас новые турниры. Заглянешь?",
                        "url": "/",
                        "tag": f"comeback:{today}",
                    })
                    if res.get("sent"):
                        summary["comeback_sent"] += 1
                except Exception as e:
                    logger.warning("comeback push failed for uid=%s: %s", uid, e)
                    summary["errors"] += 1

            # ─── #7 Streak under threat (visited yesterday, not today) ──
            # Compute current streak; if it's ≥3 AND user hasn't visited today
            # AND last visit was yesterday, the streak is still alive but at
            # risk of breaking at midnight Almaty.
            if not today_visited and last_visit == yesterday:
                streak = compute_visit_streak(conn, uid)
                if streak >= 3:
                    try:
                        res = send_push_to_user(uid, {
                            "title": f"🔥 {streak}-дневный стрик под угрозой",
                            "body": "Открой приложение сегодня, чтобы не потерять серию.",
                            "url": "/",
                            "tag": f"streak_at_risk:{today}",
                            "requireInteraction": False,
                        })
                        if res.get("sent"):
                            summary["streak_at_risk_sent"] += 1
                    except Exception as e:
                        logger.warning("streak-at-risk push failed for uid=%s: %s", uid, e)
                        summary["errors"] += 1

        log_admin_action(conn, actor, "notif_daily_batch", "", summary)

    return {"ok": True, "summary": summary, "today": today}


# ─── ACCOUNT MANAGEMENT (export + delete) ─────────────────────
# GDPR-style data portability + App Store 5.1.1(v) account-deletion compliance.

@app.get("/api/me/export")
def export_my_data(user: dict = Depends(require_user)):
    """Download all user-owned data as a single JSON file.

    Includes: profile (no password hash), results, submissions, friendships
    (both directions: outgoing requests + incoming requests + accepted),
    achievements, feedback, authored challenges. Excludes internal data
    (sessions, errors, admin actions).

    Response headers:
      - Content-Disposition uses RFC 5987 (filename* with UTF-8 percent-encoding)
        plus an ASCII `filename=` fallback (`user{id}`) so non-Latin nicknames
        like "Алексей" don't break Starlette's latin-1 header encoding.
      - Cache-Control: private, no-store — sensitive PII shouldn't be cached
        anywhere (browser, CDN, proxy).
    """
    from urllib.parse import quote

    uid = user["id"]
    with db() as conn:
        u_row = conn.execute(
            "SELECT id, email, nickname, avatar_glyph, created_at, last_login_at, "
            "is_admin, role, email_verified, badges, social_providers, "
            "is_paid, wallet_address, referred_by "
            "FROM users WHERE id = ?",
            (uid,),
        ).fetchone()
        u_dict = dict(u_row) if u_row else {}
        results = [dict(r) for r in conn.execute(
            "SELECT category_id, category_name, top1_id, top1_name, top2_id, top2_name, "
            "top3_id, top3_name, archetype_name, archetype_body, battles_played, "
            "duration_sec, completed_at, is_public, public_slug, shared_count, items_count "
            "FROM results WHERE user_id = ? ORDER BY completed_at DESC",
            (uid,),
        ).fetchall()]
        submissions = [dict(r) for r in conn.execute(
            "SELECT type, status, title, description, cluster, target_category_id, "
            "examples_json, submitted_at, decided_at, decision_note "
            "FROM submissions WHERE user_id = ? ORDER BY submitted_at DESC",
            (uid,),
        ).fetchall()]
        # Friendships: union both directions so user sees outgoing AND incoming
        # requests + accepted. Without this, incoming pending requests would be
        # silently omitted (false implication "we hold nothing about that").
        # ORDER BY uses column position (3 = created_at) — SQLite UNION queries
        # don't accept aliased column names in ORDER BY, only positional refs.
        friendships = [dict(r) for r in conn.execute(
            "SELECT 'outgoing' AS direction, f.status, f.created_at, f.responded_at, "
            "       u.nickname AS friend_nickname, u.avatar_glyph AS friend_avatar "
            "FROM friendships f JOIN users u ON u.id = f.friend_user_id "
            "WHERE f.user_id = ? "
            "UNION ALL "
            "SELECT 'incoming' AS direction, f.status, f.created_at, f.responded_at, "
            "       u.nickname AS friend_nickname, u.avatar_glyph AS friend_avatar "
            "FROM friendships f JOIN users u ON u.id = f.user_id "
            "WHERE f.friend_user_id = ? "
            "ORDER BY 3 DESC",
            (uid, uid),
        ).fetchall()]
        achievements = [dict(r) for r in conn.execute(
            "SELECT achievement_id, unlocked_at, progress_int "
            "FROM user_achievements WHERE user_id = ? ORDER BY unlocked_at DESC",
            (uid,),
        ).fetchall()]
        feedback = [dict(r) for r in conn.execute(
            "SELECT type, text, status, created_at, decided_at, decision_note "
            "FROM feedback WHERE user_id = ? ORDER BY created_at DESC",
            (uid,),
        ).fetchall()]
        challenges = [dict(r) for r in conn.execute(
            "SELECT slug, payload_json, created_at "
            "FROM challenges WHERE by_user_id = ? ORDER BY created_at DESC",
            (uid,),
        ).fetchall()]
        # Consent — current state + full audit trail. Required for GDPR
        # data portability ("everything we hold about you, including
        # records of consents you've given").
        consent_state = _get_consent_state(conn, uid)
        consent_history = [dict(r) for r in conn.execute(
            "SELECT consent_version, kind, accepted_at, ip, user_agent "
            "FROM consent_acceptances WHERE user_id = ? ORDER BY accepted_at DESC",
            (uid,),
        ).fetchall()]

    payload = {
        "exported_at": now_iso(),
        "format_version": 3,  # bumped: now includes consent state + history
        "app": "Tappetite",
        "user": u_dict,
        "results": results,
        "submissions": submissions,
        "friendships": friendships,
        "achievements": achievements,
        "feedback": feedback,
        "challenges": challenges,
        "consents": {
            "current_state": consent_state,
            "history": consent_history,
        },
    }

    # Filename: ASCII-safe primary (latin-1 OK for Content-Disposition) +
    # RFC 5987 filename* with UTF-8 percent-encoding so modern browsers
    # show the user's actual nickname even when it's Cyrillic, Chinese, etc.
    date_str = now_iso()[:10]
    nickname = u_dict.get("nickname") or "user"
    ascii_filename = f"untitled-pick-game-data-user{uid}-{date_str}.json"
    utf8_filename  = f"untitled-pick-game-data-{nickname}-{date_str}.json"
    cd = (
        f'attachment; filename="{ascii_filename}"; '
        f"filename*=UTF-8''{quote(utf8_filename)}"
    )

    body_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=body_bytes,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": cd,
            "Cache-Control": "private, no-store, max-age=0",
            "Pragma": "no-cache",
            "Vary": "Cookie",
        },
    )


@app.delete("/api/me", status_code=204)
def delete_my_account(user: dict = Depends(require_user)):
    """Permanently delete the user's account and all personal data.

    Three layers of cleanup, all in one transaction:
      1. CASCADE — sessions, results, friendships, submissions, user_achievements,
         consent_state, consent_acceptances all dropped automatically.
      2. SET NULL — errors.user_id, challenges.by_user_id, feedback.user_id,
         feedback.decided_by — FK link gone but row retained for service ops.
      3. ANONYMIZE (this layer is what audit C3 demanded) — strip personal
         identifiers from the surviving rows so the "delete wipes everything"
         promise actually holds:
           - errors.nickname/ip/user_agent → NULL (we still need stack/message
             for crash analysis, but nothing tying them to a person)
           - feedback.email_for_reply → NULL (was contact info)
           - feedback.text → tombstone string (FA-004 fix 2026-05-15: was
             "kept as-is" before, but the report-content trade-off lost the
             "delete wipes everything" promise when users typed PII into the
             text body. Row is preserved (so audit trail of "a feedback was
             filed" stays) but content is replaced. If admin needs to action
             a report from a now-deleted user they had to do it before delete.)
           - challenges.payload_json → replaced with a tombstone marker so the
             public share link still resolves to a "this user has left" page
             instead of 404 (better UX for recipients) BUT the nickname + top-3
             that were originally embedded are gone.
      4. Manual NULL on FKs without CASCADE/SET NULL — admin_actions.admin_user_id,
         submissions.decided_by, users.referred_by.
      5. DELETE user row.

    Atomicity: db() runs autocommit, so we wrap in BEGIN IMMEDIATE / COMMIT.
    Any failure → ROLLBACK leaves everything unchanged. 0-rowcount DELETE means
    the user vanished between auth and delete (parallel delete) — 404 not 500.

    This action is irreversible.
    """
    uid = user["id"]
    # Tombstone payload for surviving challenges. Keeps the slug working
    # (legacy share links don't 404) but strips the user's identity.
    challenge_tombstone = json.dumps({
        "deleted": True,
        "n1": "—", "n2": "—", "n3": "—",
        "t1": "", "t2": "", "t3": "",
        "c": "",
    }, ensure_ascii=False)
    with db() as conn:
        try:
            conn.execute("BEGIN IMMEDIATE")

            # Anonymize errors — drop nickname, IP, UA. Keep stack/message
            # for crash analysis (no PII in those once nick/ip/ua are gone).
            conn.execute(
                "UPDATE errors SET nickname = NULL, ip = NULL, user_agent = NULL "
                "WHERE user_id = ?",
                (uid,),
            )
            # Anonymize feedback — drop email_for_reply AND replace text with
            # tombstone (FA-004 fix 2026-05-15). Row is preserved so admin
            # audit trail keeps "a feedback was filed" but the user-typed
            # body (which can contain PII) is gone. The "delete wipes
            # everything" promise now actually holds.
            conn.execute(
                "UPDATE feedback SET email_for_reply = NULL, "
                "text = '[content removed on user account deletion]' "
                "WHERE user_id = ?",
                (uid,),
            )
            # Anonymize challenges — replace payload (which embedded the
            # user's nickname + their top-3 picks) with a tombstone.
            conn.execute(
                "UPDATE challenges SET payload_json = ? WHERE by_user_id = ?",
                (challenge_tombstone, uid),
            )

            # Manual NULL on FKs without CASCADE/SET NULL.
            conn.execute("UPDATE admin_actions SET admin_user_id = NULL WHERE admin_user_id = ?", (uid,))
            conn.execute("UPDATE submissions    SET decided_by   = NULL WHERE decided_by   = ?", (uid,))
            conn.execute("UPDATE users          SET referred_by  = NULL WHERE referred_by  = ?", (uid,))

            cur = conn.execute("DELETE FROM users WHERE id = ?", (uid,))
            if cur.rowcount == 0:
                conn.execute("ROLLBACK")
                raise HTTPException(404, "user_not_found")
            conn.execute("COMMIT")
        except HTTPException:
            raise
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except Exception:
                pass
            raise

    resp = Response(status_code=204)
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp


# ─── ADMIN (legacy compat for existing admin.html) ─────────────

@app.post("/api/admin/login")
def admin_login(body: AdminLoginIn, response: Response, request: Request):
    """Issue a random admin session token after credential check.

    Two paths:
      1. Nickname + password → moderator/admin login (validates against users table)
      2. Master password only → full admin (legacy bootstrap path; used by Uncle)

    Cookie value is a random 256-bit token (secrets.token_urlsafe(32)) that's
    looked up in admin_sessions on every privileged request. Forged cookies
    won't match any row → 403. Sessions live ADMIN_SESSION_TTL_DAYS (7 days).
    """
    # Strictest rate limit — admin master pw brute-force is high-value target.
    # 5 attempts / 10 min per IP. Legitimate admins know their password.
    rate_limit(request, "admin_login", max_attempts=5, window_sec=600)
    role: str
    user_id: int | None = None
    nickname_resp: str | None = None

    if body.nickname:
        # Named-account login (moderator or admin role on a real user)
        with db() as conn:
            row = conn.execute(
                "SELECT id, password_hash, role FROM users WHERE nickname = ? COLLATE NOCASE",
                (body.nickname.strip(),),
            ).fetchone()
        if not row:
            raise HTTPException(401, "invalid_credentials")
        if not check_password(body.password, row["password_hash"]):
            raise HTTPException(401, "invalid_credentials")
        user_role = row["role"] or "user"
        if user_role not in ("moderator", "admin"):
            raise HTTPException(403, "not_a_moderator")
        # Named users with role='admin' get full admin; role='moderator' is mod.
        role = "admin" if user_role == "admin" else "moderator"
        user_id = row["id"]
        nickname_resp = body.nickname.strip()
    else:
        # Master password path (full admin, no user link).
        # Audit-5 M2: hmac.compare_digest is constant-time; `!=` leaks
        # password length / prefix via timing side-channel. Rate limit
        # already makes brute-force impractical, but compare_digest is
        # the cheap industry-standard form expected by any future audit.
        if not _hmac.compare_digest(
            (body.password or "").encode("utf-8"),
            (ADMIN_PASS or "").encode("utf-8"),
        ):
            raise HTTPException(401, "invalid_credentials")
        role = "admin"
        user_id = None
        nickname_resp = None

    # Generate session token + persist
    token = secrets.token_urlsafe(32)
    now = now_iso()
    expires_dt = datetime.now(timezone.utc) + timedelta(days=ADMIN_SESSION_TTL_DAYS)
    expires = expires_dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    # Audit M1/M9: use real_ip() helper which respects X-Forwarded-For
    # rather than request.client.host (which is nginx loopback).
    ip = real_ip(request)
    ua = (request.headers.get("user-agent") or "")[:300]

    with db() as conn:
        conn.execute(
            "INSERT INTO admin_sessions(token, role, user_id, created_at, expires_at, ip, user_agent) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (token, role, user_id, now, expires, ip, ua),
        )

    response.set_cookie(
        key=ADMIN_COOKIE_NAME,
        value=token,
        max_age=86400 * ADMIN_SESSION_TTL_DAYS,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return {"ok": True, "role": role, "nickname": nickname_resp}


@app.get("/api/admin/check")
def admin_check(upg_admin: str | None = Cookie(default=None, alias=ADMIN_COOKIE_NAME)):
    actor = get_admin_actor(upg_admin)
    return {
        "is_admin": actor["role"] in ("admin", "moderator"),
        "role": actor["role"],
        "nickname": actor["nickname"],
    }


@app.get("/api/admin/whoami")
def admin_whoami(upg_admin: str | None = Cookie(default=None, alias=ADMIN_COOKIE_NAME)):
    """Detailed identity info for the admin UI to gate features by role."""
    return get_admin_actor(upg_admin)


@app.post("/api/admin/logout")
def admin_logout(response: Response, upg_admin: str | None = Cookie(default=None, alias=ADMIN_COOKIE_NAME)):
    """Revoke the current admin session token (DELETE row + clear cookie).
    Idempotent: ok to call without a valid cookie."""
    if upg_admin:
        with db() as conn:
            conn.execute("DELETE FROM admin_sessions WHERE token = ?", (upg_admin,))
    response.delete_cookie(ADMIN_COOKIE_NAME, path="/")
    return {"ok": True}


# ─── PERSONAL STATS / TASTE OVERVIEW ──────────────────────────

@app.get("/api/stats/me")
def stats_me(user: dict = Depends(require_user)):
    """Honest taste analytics for the current user, comparing their picks
    against the rest of the player base.

    Returns:
      - uniqueness_percent: 0-100, average of (100 - popularity_of_your_pick)
        across categories where >= 1 other user has played. Higher = rarer taste.
      - uniqueness_label: human label bucketed from the percent
      - compared_categories: how many of your results had co-voters to compare against
      - highlights: list of 3 concrete examples (2 rarest + 1 most-common typically)
      - empty: true if user has no results
      - insufficient: true if user has results but nobody else played the same categories
    """
    me_id = user["id"]
    with db() as conn:
        # Get user's latest result per category
        my_rows = conn.execute(
            """
            SELECT r.category_id, r.category_name, r.top1_id, r.top1_name
            FROM results r
            WHERE r.user_id = ?
              AND r.completed_at = (
                SELECT MAX(completed_at) FROM results
                WHERE user_id = r.user_id AND category_id = r.category_id
              )
            """,
            (me_id,),
        ).fetchall()

        if not my_rows:
            return {"empty": True, "reason": "no_results"}

        per_category = []
        for r in my_rows:
            cat_id = r["category_id"]
            my_pick_id = r["top1_id"]
            # Distribution of top1 across OTHER users' latest result for this category
            dist = conn.execute(
                """
                SELECT r.top1_id, COUNT(*) AS cnt
                FROM results r
                WHERE r.category_id = ? AND r.user_id != ?
                  AND r.completed_at = (
                    SELECT MAX(completed_at) FROM results
                    WHERE user_id = r.user_id AND category_id = r.category_id
                  )
                GROUP BY r.top1_id
                """,
                (cat_id, me_id),
            ).fetchall()
            total_others = sum(d["cnt"] for d in dist)
            if total_others == 0:
                continue  # nobody else played — can't compare honestly
            my_count = sum(d["cnt"] for d in dist if d["top1_id"] == my_pick_id)
            share = round(100 * my_count / total_others)
            per_category.append({
                "category_id": cat_id,
                "category_name": r["category_name"] or cat_id,
                "your_pick_id": my_pick_id,
                "your_pick_name": r["top1_name"] or "?",
                "share_percent": share,                  # what % of others picked the same
                "voters_excluding_you": total_others,
            })

    if not per_category:
        return {
            "empty": False,
            "insufficient": True,
            "uniqueness_percent": None,
            "uniqueness_label": "пока никто не пересёкся с тобой",
            "compared_categories": 0,
            "highlights": [],
        }

    avg_share = sum(c["share_percent"] for c in per_category) / len(per_category)
    uniqueness = round(100 - avg_share)

    # Each bucket is framed as a positive identity, never as a put-down.
    # The two extremes both sound proud (rare = pioneer, common = guardian of classics).
    if uniqueness >= 75: label = "редчайший вкус"
    elif uniqueness >= 60: label = "свой угол зрения"
    elif uniqueness >= 40: label = "широкий спектр"
    elif uniqueness >= 20: label = "хранитель классики"
    else:                  label = "в сердце культуры"

    # Highlights: 2 rarest + 1 most common (for contrast). Skip duplicates.
    sorted_rare = sorted(per_category, key=lambda c: c["share_percent"])
    highlights = []
    for c in sorted_rare[:2]:
        highlights.append({**c, "type": "rare"})
    seen_ids = {h["category_id"] for h in highlights}
    for c in sorted(per_category, key=lambda c: -c["share_percent"]):
        if c["category_id"] not in seen_ids and c["share_percent"] >= 50:
            highlights.append({**c, "type": "common"})
            break

    return {
        "empty": False,
        "insufficient": False,
        "uniqueness_percent": uniqueness,
        "uniqueness_label": label,
        "compared_categories": len(per_category),
        "highlights": highlights,
    }


# ─── AI PORTRAIT («Прочтение») ────────────────────────────────────────
# AI-generated cross-category portrait of the user, gated to one free
# generation per week + activity-gate (user must play at least one
# tournament since their last portrait). Paid path (wallet) lands in Phase 2.
#
# Endpoints:
#   POST /api/me/portrait/generate   - create new portrait (free, gated)
#   GET  /api/me/portrait            - latest cached + button status
#   GET  /p/portrait/{slug}          - public read for sharing
#
# Latency: 15-40s per call. Frontend must show a loading state.

class PortraitGenerateIn(BaseModel):
    # Phase 1: only 'global' scope is supported. Schema is multi-scope ready
    # (cluster/pair/group later) so we accept the field but validate strictly.
    scope: str = Field(default="global", max_length=20)
    # Optional UI language override. If absent, falls back to Accept-Language
    # header → 'ru' default. Same logic as _detect_email_lang.
    lang: Optional[str] = Field(default=None, max_length=8)


def _serialize_portrait(row: dict, include_content: bool = True) -> dict:
    """Convert a user_portraits DB row into the API response shape.
    `include_content` lets us omit content_md when only metadata is needed."""
    out = {
        "id": row.get("id"),
        "scope_kind": row.get("scope_kind"),
        "scope_key": row.get("scope_key"),
        "generated_at": row.get("generated_at"),
        "tournaments_at_gen": row.get("tournaments_at_gen"),
        "lang": row.get("lang"),
        "is_public": bool(row.get("is_public")),
        "public_slug": row.get("public_slug"),
        "model_used": row.get("model_used"),
    }
    if include_content:
        out["content_md"] = row.get("content_md")
    return out


@app.post("/api/me/portrait/generate", status_code=201)
def generate_portrait(
    body: PortraitGenerateIn,
    request: Request,
    user: dict = Depends(require_user),
):
    """Generate a new AI portrait for the current user.

    Returns HTTP 201 + portrait JSON on success.
    HTTP 409 if user hasn't played any tournaments yet, or no new tournaments
       since last generation.
    HTTP 429 if cooldown not yet elapsed (next_available_at in body).
    HTTP 503 if Anthropic API key missing or upstream API fails.
    """
    if body.scope != "global":
        raise HTTPException(400, "only scope=global supported in phase 1")

    lang = _detect_email_lang(request, override=body.lang)

    with db() as conn:
        # 1. Gate evaluation (cooldown + activity)
        gate = portrait_mod.evaluate_gates(conn, user["id"], scope_kind="global")
        if not gate["can_generate"]:
            reason = gate["blocked_reason"]
            if reason == "cooldown":
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "cooldown",
                        "next_available_at": gate["next_available_at"],
                        "message": "Next portrait available later (1 per week limit)",
                    },
                )
            if reason == "no_new_tournaments":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "no_new_tournaments",
                        "message": "Play at least one new tournament to refresh your portrait",
                    },
                )
            if reason == "no_tournaments":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "no_tournaments",
                        "message": "Play your first tournament first",
                    },
                )
            if reason == "not_enough_tournaments":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "not_enough_tournaments",
                        "message": "Play at least 10 tournaments to unlock the portrait",
                        "current_tournaments": gate.get("current_tournaments", 0),
                        "required": portrait_mod.MIN_TOURNAMENTS_FOR_FIRST_PORTRAIT,
                    },
                )
            # Unknown reason — fail safe
            raise HTTPException(503, f"portrait blocked: {reason}")

        # 2. Load categories (reuse main.py's cached loader)
        cats = _load_categories()

        # 3. Call Anthropic. This is 15-40s — caller must handle loading UI.
        try:
            result = portrait_mod.generate_global_portrait(
                conn, user["id"], cats, lang=lang
            )
        except RuntimeError as e:
            # Auth, network, format errors all surface as RuntimeError from
            # call_anthropic. Log + return 503 so client can show "try later".
            logger.warning("portrait gen failed for user %s: %s", user["id"], e)
            raise HTTPException(503, "portrait_generation_failed")

        # 4. Persist
        saved = portrait_mod.save_portrait(
            conn, user["id"], result, lang=lang, scope_kind="global"
        )
        conn.commit()

    return {
        "portrait": _serialize_portrait(saved, include_content=True),
        "metrics": {
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
            "cost_usd": result.get("cost_usd", 0),
            "latency_sec": result.get("latency_sec", 0),
        },
    }


@app.get("/api/me/portrait")
def get_my_portrait(
    scope: str = "global",
    user: dict = Depends(require_user),
):
    """Return user's latest cached portrait for the given scope, plus the
    gate status (so the frontend can render the generate button correctly).

    portrait field is null if no portrait has been generated yet."""
    if scope != "global":
        raise HTTPException(400, "only scope=global supported in phase 1")

    with db() as conn:
        latest = portrait_mod.get_latest_portrait(conn, user["id"], "global")
        gate = portrait_mod.evaluate_gates(conn, user["id"], "global")

    return {
        "portrait": _serialize_portrait(latest, include_content=True) if latest else None,
        "gate": {
            "can_generate": gate["can_generate"],
            "blocked_reason": gate["blocked_reason"],
            "next_available_at": gate["next_available_at"],
            "current_tournaments": gate["current_tournaments"],
            "tournaments_at_last_gen": gate["tournaments_at_last_gen"],
            "last_generated_at": gate["last_generated_at"],
            "is_unlimited": gate.get("is_unlimited", False),
        },
    }


class PortraitVisibilityIn(BaseModel):
    portrait_id: int
    is_public: bool


@app.patch("/api/me/portrait/visibility")
def set_portrait_visibility(
    body: PortraitVisibilityIn,
    user: dict = Depends(require_user),
):
    """Toggle is_public on one of the user's own portraits. Used by the
    «Поделиться» button on the profile to make a portrait shareable before
    handing the public URL to the OS share sheet.

    Auth: the portrait must belong to the calling user. We check via the
    participant_ids JSON array (single-element for solo portraits)."""
    expected_participants = json.dumps([user["id"]])
    with db() as conn:
        row = conn.execute(
            "SELECT id, participant_ids, public_slug FROM user_portraits WHERE id = ?",
            (body.portrait_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "not_found")
        # Ownership check via participants array (multi-user portraits later)
        if row["participant_ids"] != expected_participants:
            raise HTTPException(403, "not_owner")
        conn.execute(
            "UPDATE user_portraits SET is_public = ? WHERE id = ?",
            (1 if body.is_public else 0, body.portrait_id),
        )
        conn.commit()
        return {
            "id": body.portrait_id,
            "is_public": body.is_public,
            "public_slug": row["public_slug"],
        }


@app.get("/api/portrait/p/{slug}")
def get_public_portrait_json(slug: str):
    """JSON read for a shared portrait. Used by frontend on /p/portrait/{slug}
    landing if the server-side inline payload is missing. Public (no auth)."""
    if not re.fullmatch(r"[a-z0-9]{6,16}", slug):
        raise HTTPException(404, "not_found")
    with db() as conn:
        row = portrait_mod.get_portrait_by_slug(conn, slug)
        if not row or not row.get("is_public"):
            raise HTTPException(404, "not_found")
        try:
            participants = json.loads(row["participant_ids"])
            author_uid = participants[0] if participants else None
        except (json.JSONDecodeError, KeyError, IndexError):
            author_uid = None
        author_nick = None
        if author_uid:
            urow = conn.execute(
                "SELECT nickname FROM users WHERE id = ?", (author_uid,)
            ).fetchone()
            if urow and urow["nickname"]:
                author_nick = urow["nickname"]
    return {
        "portrait": _serialize_portrait(row, include_content=True),
        "author_nick": author_nick,
    }


@app.get("/p/portrait/{slug}")
def public_portrait_landing(slug: str):
    """Server-rendered public landing page for a shared portrait.

    Mirrors the /c/{slug} pattern: takes game.html, injects OG meta tags
    (so Telegram/WhatsApp/iMessage previews show author + headline), and
    inlines the portrait payload as window._INITIAL_SHARED_PORTRAIT so
    the frontend skips a second roundtrip on initial render.

    If the slug is invalid or the portrait is private, we still serve
    game.html (unmodified) so the user lands on the home screen rather
    than seeing a raw 404 page."""
    html_text = _load_template_cached(GAME_HTML_PATH, _game_html_cache)
    if not html_text:
        raise HTTPException(500, "game_html_unavailable")

    if not re.fullmatch(r"[a-z0-9]{6,16}", slug):
        return HTMLResponse(content=html_text, headers={"Cache-Control": "no-cache"})

    with db() as conn:
        row = portrait_mod.get_portrait_by_slug(conn, slug)
        if not row or not row.get("is_public"):
            return HTMLResponse(content=html_text, headers={"Cache-Control": "no-cache"})

        # Author nickname
        try:
            participants = json.loads(row["participant_ids"])
            author_uid = participants[0] if participants else None
        except (json.JSONDecodeError, KeyError, IndexError):
            author_uid = None
        author_nick = "?"
        if author_uid:
            urow = conn.execute(
                "SELECT nickname FROM users WHERE id = ?", (author_uid,)
            ).fetchone()
            if urow and urow["nickname"]:
                author_nick = urow["nickname"]

    # Extract headline from markdown (first line starting with "# ")
    body_md = row.get("content_md") or ""
    headline = ""
    for line in body_md.split("\n"):
        s = line.strip()
        if s.startswith("# "):
            headline = s[2:].strip()
            break
    if not headline:
        headline = "Прочтение"

    # First paragraph (after headline) for the description preview
    first_para = ""
    in_body = False
    for para in body_md.split("\n\n"):
        p = para.strip()
        if not p:
            continue
        if p.startswith("# "):
            in_body = True
            continue
        if in_body:
            # Strip ** wrappers if present
            if p.startswith("**") and p.endswith("**"):
                p = p[2:-2].strip()
            first_para = p[:200]
            break

    title = f"{author_nick} · {headline} - Tappetite"
    description = first_para or f"Прочтение от @{author_nick} в Tappetite."
    page_url = f"https://isverifiedby.me/p/portrait/{slug}"
    # Per-portrait OG image, rendered server-side from og_portrait.svg template.
    # Lazy-rendered on first crawl, cached forever (slug is immutable).
    image_url = f"https://isverifiedby.me/og/portrait/{slug}.png"
    image_alt = f"AI-портрет @{author_nick} в Tappetite"

    html_text = _set_meta(html_text, 'property', 'og:title', title)
    html_text = _set_meta(html_text, 'property', 'og:description', description)
    html_text = _set_meta(html_text, 'property', 'og:url', page_url)
    html_text = _set_meta(html_text, 'property', 'og:image', image_url)
    html_text = _set_meta(html_text, 'property', 'og:image:alt', image_alt)
    html_text = _set_meta(html_text, 'name', 'twitter:title', title)
    html_text = _set_meta(html_text, 'name', 'twitter:description', description)
    html_text = _set_meta(html_text, 'name', 'twitter:image', image_url)

    # Inline payload so client skips /api/portrait/p/{slug} fetch on landing.
    # _safe_inline_json escapes </script> + U+2028/U+2029 to prevent XSS.
    payload = {
        "slug": slug,
        "portrait": _serialize_portrait(row, include_content=True),
        "author_nick": author_nick,
    }
    inline_payload = _safe_inline_json(payload)
    inject = f'<script>window._INITIAL_SHARED_PORTRAIT = {inline_payload};</script>\n</head>'
    html_text = html_text.replace('</head>', inject, 1)

    # NO caching — share previews go through Telegram/WhatsApp/Safari which
    # all aggressively cache HTML. With caching, a JS bug fix wouldn't reach
    # the recipient. Portrait shares are low-traffic, the perf cost is
    # negligible. Also tells Cloudflare not to cache at edge.
    return HTMLResponse(content=html_text, headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    })


# ─── BROADCAST EMAIL (admin announcement to all users) ───────────────
# Sends one custom email to every qualifying user via Resend (mailer.send_email).
# Filters out moderators (role='moderator'), the admin themselves (optional),
# and synthetic placeholder emails (@isverifiedby.me — used by mod accounts).
# Always supports dry_run mode that returns the would-be-recipient list
# WITHOUT sending. Sender should always dry-run first to verify the list.

class BroadcastIn(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    body_html: str = Field(..., min_length=1, max_length=50000)
    body_text: str = Field(..., min_length=1, max_length=20000)
    dry_run: bool = Field(default=True)  # safe default — explicit false to send
    include_moderators: bool = Field(default=False)
    exclude_self: bool = Field(default=True)
    exclude_user_ids: Optional[list[int]] = Field(default=None)


@app.post("/api/admin/broadcast")
def admin_broadcast(body: BroadcastIn,
                     _admin: bool = Depends(require_admin),
                     actor: dict = Depends(get_admin_actor)):
    """Send a custom email to all qualifying users.

    Filters:
      - role='moderator' excluded unless include_moderators=true
      - email ending @isverifiedby.me excluded (synthetic placeholder accts)
      - email NULL or empty excluded
      - the admin themselves excluded if exclude_self=true
      - any IDs in exclude_user_ids excluded

    Behavior:
      - dry_run=true (DEFAULT): returns recipient list, sends nothing
      - dry_run=false: sends one-by-one via mailer.send_email(), logs each
        send to admin_actions, returns summary {sent[], failed[], skipped[]}

    Always wraps body in branded Tappetite layout via broadcast_email().
    """
    actor_uid = actor.get("user_id") if actor else None
    excl_ids = set(body.exclude_user_ids or [])
    if body.exclude_self and actor_uid:
        excl_ids.add(int(actor_uid))

    recipients = []
    skipped = []
    with db() as conn:
        rows = conn.execute(
            "SELECT id, nickname, email, role FROM users ORDER BY id"
        ).fetchall()
        for r in rows:
            uid = int(r["id"])
            email = (r["email"] or "").strip().lower()
            nick = r["nickname"] or ""
            role = r["role"] or "user"

            if not email:
                skipped.append({"id": uid, "nickname": nick, "reason": "no_email"})
                continue
            if email.endswith("@isverifiedby.me"):
                # Synthetic placeholder — created by admin for moderator accounts
                skipped.append({"id": uid, "nickname": nick, "reason": "synthetic_email"})
                continue
            if uid in excl_ids:
                skipped.append({"id": uid, "nickname": nick, "reason": "excluded_explicit"})
                continue
            if role == "moderator" and not body.include_moderators:
                skipped.append({"id": uid, "nickname": nick, "reason": "moderator"})
                continue
            recipients.append({"id": uid, "nickname": nick, "email": email})

    if body.dry_run:
        return {
            "dry_run": True,
            "would_send_count": len(recipients),
            "would_send": recipients,
            "skipped_count": len(skipped),
            "skipped": skipped,
            "subject": body.subject,
        }

    # Real send — wrap once, send per recipient
    template = broadcast_email(body.subject, body.body_html, body.body_text)
    sent = []
    failed = []
    for r in recipients:
        try:
            result = send_email(
                to=r["email"],
                subject=template["subject"],
                html=template["html"],
                text=template["text"],
            )
            sent.append({"id": r["id"], "email": r["email"], "resend_id": result.get("id")})
            logger.info("broadcast_sent uid=%s email=%s resend_id=%s",
                        r["id"], r["email"], result.get("id"))
        except EmailSendError as e:
            failed.append({"id": r["id"], "email": r["email"], "error": str(e)[:200]})
            logger.error("broadcast_failed uid=%s email=%s err=%s",
                         r["id"], r["email"], e)

    # Log to admin_actions for audit trail
    with db() as conn:
        log_admin_action(conn, actor, "broadcast_sent", body.subject[:80], {
            "subject": body.subject,
            "recipients_count": len(recipients),
            "sent_count": len(sent),
            "failed_count": len(failed),
            "skipped_count": len(skipped),
        })

    return {
        "dry_run": False,
        "sent_count": len(sent),
        "failed_count": len(failed),
        "skipped_count": len(skipped),
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
    }


@app.post("/api/admin/moderators/create")
def admin_create_moderator(body: CreateModeratorIn,
                            _admin: bool = Depends(require_admin),
                            actor: dict = Depends(get_admin_actor)):
    """Full admin only. Creates a new user account with role='moderator',
    or upgrades an existing user's role to moderator. Returns the user record.
    """
    nick = body.nickname.strip()
    if not NICK_RE.match(nick):
        raise HTTPException(422, "invalid_nickname")
    pw_hash = hash_password(body.password)
    with db() as conn:
        existing = conn.execute(
            "SELECT id, role FROM users WHERE nickname = ? COLLATE NOCASE", (nick,)
        ).fetchone()
        if existing:
            # Upgrade existing user
            conn.execute(
                "UPDATE users SET role = 'moderator', password_hash = ? WHERE id = ?",
                (pw_hash, existing["id"]),
            )
            uid = existing["id"]
            action = "upgraded_to_moderator"
        else:
            email = (body.email or f"{nick.lower()}+mod@isverifiedby.me").lower()
            conn.execute(
                "INSERT INTO users (nickname, email, password_hash, created_at, role) "
                "VALUES (?, ?, ?, ?, 'moderator')",
                (nick, email, pw_hash, now_iso()),
            )
            uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            # Auto-friend admin sees this new mod too (same flow as register)
            auto_friend_admin(conn, uid)
            action = "created_moderator"
        # Audit
        log_admin_action(conn, actor, action, nick, {"user_id": uid})
        user = dict(conn.execute(
            "SELECT id, nickname, email, role, created_at FROM users WHERE id = ?", (uid,)
        ).fetchone())
    return {"ok": True, "user": user, "action": action}


@app.get("/api/admin/stats/live")
def admin_stats_live(_admin: bool = Depends(require_admin)):
    """Lightweight counters for the admin topbar — polled every ~15s.
    Returns user totals + recent activity so admin can watch the player base
    grow in real time. Single quick query, no joins."""
    now = datetime.now(timezone.utc)
    today_iso = now.strftime("%Y-%m-%dT00:00:00Z")
    hour_ago = (now - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    baseline_ts = get_registrations_baseline()
    with db() as conn:
        users_total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        users_today = conn.execute(
            "SELECT COUNT(*) FROM users WHERE created_at >= ?", (today_iso,)
        ).fetchone()[0]
        users_last_hour = conn.execute(
            "SELECT COUNT(*) FROM users WHERE created_at >= ?", (hour_ago,)
        ).fetchone()[0]
        # New registrations since the baseline (the topbar "new since launch"
        # counter). Counted by created_at >= baseline rather than (total - N)
        # so a later user deletion can't push the count negative.
        users_since_baseline = conn.execute(
            "SELECT COUNT(*) FROM users WHERE created_at >= ?", (baseline_ts,)
        ).fetchone()[0]
        results_total = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        results_today = conn.execute(
            "SELECT COUNT(*) FROM results WHERE completed_at >= ?", (today_iso,)
        ).fetchone()[0]
        subs_pending = conn.execute(
            "SELECT COUNT(*) FROM submissions WHERE status IN ('pending', 'needs_review')"
        ).fetchone()[0]
    return {
        "users_total": users_total,
        "users_today": users_today,
        "users_last_hour": users_last_hour,
        "users_since_baseline": users_since_baseline,
        "registrations_baseline_ts": baseline_ts,
        "results_total": results_total,
        "results_today": results_today,
        "submissions_pending": subs_pending,
        "ts": now_iso(),
    }


@app.post("/api/admin/stats/registrations/reset-baseline")
def admin_reset_registrations_baseline(
    _admin: bool = Depends(require_admin),
    actor: dict = Depends(get_admin_actor),
):
    """Reset the "new registrations" counter baseline to NOW. Use on launch
    day to zero the counter so it tracks only post-launch signups. Returns the
    new baseline + the (now zero) count for that instant."""
    new_ts = now_iso()
    set_setting("registrations_baseline_ts", new_ts)
    with db() as conn:
        log_admin_action(conn, actor, "reset_registrations_baseline", new_ts, None)
    return {"registrations_baseline_ts": new_ts, "users_since_baseline": 0}


@app.get("/api/admin/anthropic/spend")
def admin_anthropic_spend(_role: str = Depends(require_mod_or_admin)):
    """AI portrait spend rollup for the admin/moderator topbar banner.

    Anthropic has no public balance API, so we self-track from
    user_portraits.{input_tokens, output_tokens, model_used} multiplied by
    per-model pricing (defined in portrait.MODEL_PRICING_USD_PER_MTOK).

    If ANTHROPIC_BUDGET_USD env var is set (e.g. '50'), we also return
    budget_usd + remaining_usd so the banner can show the burn percentage.
    """
    now = datetime.now(timezone.utc)
    today_iso = now.strftime("%Y-%m-%dT00:00:00Z")
    month_start_iso = now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).isoformat().replace("+00:00", "Z")

    # Read from append-only ledger (decoupled from user_portraits). Cost is
    # already pre-computed at insert time, so we don't recompute pricing here.
    with db() as conn:
        rows = conn.execute(
            "SELECT occurred_at, cost_usd FROM anthropic_spend_ledger"
        ).fetchall()

    today_usd = 0.0
    month_usd = 0.0
    total_usd = 0.0
    count_today = 0
    count_month = 0
    last_call = None
    for r in rows:
        c = float(r["cost_usd"] or 0)
        total_usd += c
        oa = r["occurred_at"] or ""
        if oa >= month_start_iso:
            month_usd += c
            count_month += 1
        if oa >= today_iso:
            today_usd += c
            count_today += 1
        if last_call is None or oa > last_call:
            last_call = oa

    out = {
        "today_usd": round(today_usd, 4),
        "month_usd": round(month_usd, 4),
        "total_usd": round(total_usd, 4),
        "count_today": count_today,
        "count_month": count_month,
        "count_total": len(rows),
        "last_call_at": last_call,
    }

    # Optional self-set budget. If env var present, we add budget + remaining.
    budget_str = os.environ.get("ANTHROPIC_BUDGET_USD")
    if budget_str:
        try:
            budget = float(budget_str)
            out["budget_usd"] = budget
            out["remaining_usd"] = round(budget - total_usd, 4)
            out["spent_pct"] = round(100 * total_usd / budget, 1) if budget > 0 else 0
        except ValueError:
            pass

    return out


@app.get("/api/admin/portraits")
def admin_list_portraits(_role: str = Depends(require_mod_or_admin)):
    """Full list of generated AI portraits for the admin/moderator panel.

    Returns rows ordered by generation time (newest first) with user info
    joined (nickname + when user registered). Includes computed cost per
    portrait so the admin can audit spend distribution per user.
    """
    pricing = portrait_mod.MODEL_PRICING_USD_PER_MTOK
    with db() as conn:
        rows = conn.execute(
            """
            SELECT p.id, p.scope_kind, p.scope_key, p.participant_ids,
                   p.generated_at, p.tournaments_at_gen, p.lang,
                   p.is_public, p.public_slug, p.model_used,
                   p.input_tokens, p.output_tokens, p.credits_spent,
                   p.content_md
            FROM user_portraits p
            ORDER BY p.generated_at DESC
            """
        ).fetchall()

        # Resolve participant_ids[0] → user info per row
        out = []
        user_cache: dict[int, dict] = {}
        for r in rows:
            d = dict(r)
            # Strip content_md down to just the headline (first line that
            # starts with "# ") + length, to keep the response small.
            md = d.pop("content_md") or ""
            headline = ""
            for line in md.split("\n"):
                s = line.strip()
                if s.startswith("# "):
                    headline = s[2:].strip()
                    break
            d["headline"] = headline
            d["content_chars"] = len(md)

            # Cost calc (strip date suffix for pricing lookup)
            m = (d.get("model_used") or "")
            m_lookup = re.sub(r"-\d{8}$", "", m)
            in_price, out_price = pricing.get(m_lookup, pricing.get(m, (0.0, 0.0)))
            in_tok = d.get("input_tokens") or 0
            out_tok = d.get("output_tokens") or 0
            d["cost_usd"] = round(
                (in_tok / 1_000_000) * in_price + (out_tok / 1_000_000) * out_price,
                4,
            )

            # Author lookup (cached)
            author_uid = None
            try:
                participants = json.loads(d["participant_ids"])
                author_uid = participants[0] if participants else None
            except (json.JSONDecodeError, TypeError, IndexError):
                pass
            d["user_id"] = author_uid
            if author_uid is not None:
                if author_uid not in user_cache:
                    urow = conn.execute(
                        "SELECT nickname, email, created_at, gender "
                        "FROM users WHERE id = ?",
                        (author_uid,),
                    ).fetchone()
                    if urow:
                        user_cache[author_uid] = {
                            "nickname": urow["nickname"],
                            "email": urow["email"],
                            "user_created_at": urow["created_at"],
                            "gender": urow["gender"],
                        }
                    else:
                        user_cache[author_uid] = {
                            "nickname": None, "email": None,
                            "user_created_at": None, "gender": None,
                        }
                d.update(user_cache[author_uid])
            out.append(d)

    return {"portraits": out, "total": len(out)}


@app.get("/api/admin/portraits/{portrait_id}/content")
def admin_portrait_content(portrait_id: int, _role: str = Depends(require_mod_or_admin)):
    """Full content_md of a single portrait — for the admin detail view.

    Bypasses is_public: admin/moderator role is enough to read any portrait
    body, including private ones the author hasn't shared. The list endpoint
    (/api/admin/portraits) intentionally returns only the headline to keep
    that response small; this endpoint is the on-demand "give me the whole
    thing" companion for the detail pane.

    Added 2026-05-19 after the admin couldn't read DGR's private portrait
    via the existing public JSON endpoint (which 404s for is_public=0)."""
    with db() as conn:
        row = conn.execute(
            "SELECT id, content_md, lang, is_public, public_slug, generated_at "
            "FROM user_portraits WHERE id = ?",
            (portrait_id,),
        ).fetchone()
    if not row:
        raise HTTPException(404, "portrait_not_found")
    return {
        "id": row["id"],
        "content_md": row["content_md"],
        "lang": row["lang"],
        "is_public": bool(row["is_public"]),
        "public_slug": row["public_slug"],
        "generated_at": row["generated_at"],
    }


@app.get("/api/admin/orphaned-submissions")
def admin_orphaned_submissions(_role: str = Depends(require_mod_or_admin)):
    """Find submissions in inconsistent state. Two integrity invariants:

    1. "approved" type='category' submission ↔ matching category exists in
       categories.json (matched by category_published audit log carrying
       submission_id, OR by exact id/name match).
    2. "approved" type='item' submission ↔ item present under target_category.

    Returns lists of orphans for the admin UI; should normally be empty.
    The guard in PATCH /api/submissions and the atomic update in
    apply-from-json prevent NEW orphans from forming.
    """
    orphans_cat: list[dict] = []
    orphans_item: list[dict] = []
    try:
        data = json.loads(CATEGORIES_JSON_PATH.read_text(encoding='utf-8'))
        cats = data if isinstance(data, list) else (data.get('categories') or [])
    except Exception:
        cats = []
    cat_by_id = {c.get('id'): c for c in cats}
    cat_names = {(c.get('name') or '').strip().lower() for c in cats}

    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM submissions WHERE status = 'approved' ORDER BY decided_at DESC"
        ).fetchall()
        # Pre-fetch published submission_ids from audit log to short-circuit name matching
        published_sids = set()
        for a in conn.execute(
            "SELECT extras_json FROM admin_actions WHERE action = 'category_published'"
        ).fetchall():
            try:
                ej = json.loads(a['extras_json'] or '{}')
                if isinstance(ej.get('submission_id'), int):
                    published_sids.add(ej['submission_id'])
            except Exception:
                pass

    for r in rows:
        sd = submission_to_dict(r)
        if r['type'] == 'category':
            ok = (r['id'] in published_sids) or ((r['title'] or '').strip().lower() in cat_names)
            if not ok:
                orphans_cat.append(sd)
        elif r['type'] == 'item':
            tcid = r['target_category_id']
            cat = cat_by_id.get(tcid)
            ok = False
            if cat:
                title_l = (r['title'] or '').strip().lower()
                ok = any((it.get('name') or '').strip().lower() == title_l for it in (cat.get('items') or []))
            if not ok:
                orphans_item.append(sd)
    return {
        "orphans_category": orphans_cat,
        "orphans_item": orphans_item,
        "counts": {"category": len(orphans_cat), "item": len(orphans_item)},
    }


@app.get("/api/admin/events")
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
            yield "event: hello\ndata: {\"ok\":true}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    line = (
                        f"event: {payload['type']}\n"
                        f"data: {json.dumps(payload['data'], ensure_ascii=False)}\n\n"
                    )
                    yield line
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
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


# Audit-11 P1: cap context payload so unauthenticated /api/errors can't
# be turned into a cheap storage/memory DoS. We accept a small dict of
# diagnostic key/values; anything bigger is truncated server-side.
_ERR_CTX_MAX_KEYS = 32
_ERR_CTX_MAX_KEY_LEN = 64
_ERR_CTX_MAX_VAL_LEN = 1024
_ERR_CTX_MAX_SERIALIZED = 4096

def _sanitize_error_context(ctx: Optional[dict]) -> Optional[dict]:
    """Bound context shape: max N top-level keys, key/value lengths capped,
    nested values stringified at depth 1 (no recursion to defeat deep-nesting
    parse cost). Returns None if input was None/empty/invalid."""
    if not ctx or not isinstance(ctx, dict):
        return None
    out: dict = {}
    for i, (k, v) in enumerate(ctx.items()):
        if i >= _ERR_CTX_MAX_KEYS:
            out["_truncated"] = f"dropped {len(ctx) - i} more keys"
            break
        # Coerce key to short str
        key = str(k)[:_ERR_CTX_MAX_KEY_LEN]
        # Coerce value: primitives kept, complex objects stringified
        if isinstance(v, (str, int, float, bool)) or v is None:
            val = v
            if isinstance(val, str) and len(val) > _ERR_CTX_MAX_VAL_LEN:
                val = val[:_ERR_CTX_MAX_VAL_LEN] + "…"
        else:
            try:
                val = json.dumps(v, ensure_ascii=False)[:_ERR_CTX_MAX_VAL_LEN]
            except Exception:
                val = "<unserializable>"
        out[key] = val
    # Final guard against pathological key inflation: enforce serialized cap
    try:
        serialized = json.dumps(out, ensure_ascii=False)
        if len(serialized) > _ERR_CTX_MAX_SERIALIZED:
            return {"_truncated": "context exceeded serialized size cap"}
    except Exception:
        return {"_truncated": "context unserializable"}
    return out


class ErrorReportIn(BaseModel):
    """Public error report from the browser (window.onerror, unhandledrejection)."""
    message: str = Field(..., min_length=1, max_length=2000)
    stack: Optional[str] = Field(default=None, max_length=20000)
    url: Optional[str] = Field(default=None, max_length=2000)
    level: Optional[str] = Field(default='error', pattern=r'^(error|warning|info)$')
    # Audit-11 P1: max_length on dict counts top-level keys (Pydantic
    # default behaviour) — additional structural validation happens via
    # _sanitize_error_context in the route, which truncates oversized
    # values + serializes-cap to defeat memory/storage DoS.
    context: Optional[dict] = Field(default=None, max_length=_ERR_CTX_MAX_KEYS)


# Simple in-memory rate limit: {ip: [timestamps]}, sliding 60s window.
# 100 reports/min/IP is generous; any client bug-loop hits this and stops.
# FA-009 fix 2026-05-15: bounded by _ERR_RL_MAX_KEYS to prevent memory
# growth under botnet IP rotation through Cloudflare. When the dict is full,
# we sweep stale (empty-bucket) entries first; if still over cap, drop the
# oldest by first-timestamp. Worst case: legitimate slow-trickle errors get
# evicted in extreme adversarial conditions, which is acceptable.
_err_rl: dict = {}
_ERR_RL_LIMIT = 100
_ERR_RL_WINDOW = 60.0
_ERR_RL_MAX_KEYS = 10000

def _err_rate_limit(ip: str) -> bool:
    """Returns True if allowed, False if throttled."""
    import time as _t
    now = _t.time()
    bucket = _err_rl.setdefault(ip, [])
    # drop timestamps outside the window
    cutoff = now - _ERR_RL_WINDOW
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)
    # Bound dictionary size against IP-rotation memory exhaustion (FA-009).
    # Sweep is amortized — only kicks in when we cross the cap.
    if len(_err_rl) > _ERR_RL_MAX_KEYS:
        # First pass: drop entries whose buckets are fully expired.
        for k in [k for k, b in _err_rl.items() if not b]:
            _err_rl.pop(k, None)
        # If still over cap, drop oldest by earliest timestamp in their bucket.
        if len(_err_rl) > _ERR_RL_MAX_KEYS:
            items = sorted(
                ((k, (b[0] if b else 0.0)) for k, b in _err_rl.items()),
                key=lambda kv: kv[1],
            )
            for k, _ts in items[: len(_err_rl) - _ERR_RL_MAX_KEYS]:
                _err_rl.pop(k, None)
    if len(bucket) >= _ERR_RL_LIMIT:
        return False
    bucket.append(now)
    return True


def _dedupe_key(source: str, message: str, stack: str | None) -> str:
    """Hash of (source + first stack line + first 60 chars of message).
    Used to group similar errors for the admin view."""
    import hashlib
    first_line = (stack or '').strip().split('\n')[0] if stack else ''
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
    """Public endpoint for browser-side error reports. Rate-limited per IP.

    Third-party noise filter: drops reports clearly from external scripts
    (PostHog vendored lib, browser wallet/extension scripts) — they pollute
    the errors table without giving us anything actionable. Reports still
    return 200 to avoid client retries; they're just not persisted."""
    # Audit M1: real_ip() respects CF-Connecting-IP / X-Forwarded-For so
    # we don't end up rate-limiting all users by nginx loopback (127.0.0.1).
    ip = real_ip(request) or 'unknown'
    if not _err_rate_limit(ip):
        raise HTTPException(429, "rate_limited")

    # Drop third-party noise. Match in either message or stack frames.
    NOISE_MARKERS = (
        '/ph/static/web-vitals',          # PostHog bundled web-vitals (Array.at() on old WebKit)
        'this.o.at is not a function',
        'Talisman extension',              # Talisman wallet browser extension
        'Extension context invalidated',   # any browser extension getting unloaded
        'tronlinkParams',                  # TronLink wallet extension
        'inpage.js',                       # generic wallet-extension injected script
        'chrome-extension://',
        'moz-extension://',
        'safari-extension://',
    )
    haystack = (body.message or '') + '\n' + (body.stack or '') + '\n' + (body.url or '')
    if any(marker in haystack for marker in NOISE_MARKERS):
        return {"ok": True, "id": None, "filtered": True}
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
        context=_sanitize_error_context(body.context),
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
    # Audit M1: real_ip() — see report_error above.
    ip = real_ip(request) or 'unknown'
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


@app.get("/api/admin/anthropic-status")
def admin_anthropic_status(_role: str = Depends(require_mod_or_admin)):
    """Tell admin UI whether the Claude API path is available, so it can show
    the 'auto-fill via API' button (or hide it and show only the copy-paste flow)."""
    return {
        "sdk_installed": _ANTHROPIC_AVAILABLE,
        "key_configured": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "model": ANTHROPIC_MODEL,
    }


# ─── ITEM CTX EDITING (manual ctx fill for approved items) ─────

class SetCtxIn(BaseModel):
    category_id: str = Field(..., min_length=1, max_length=120)
    item_id: str = Field(..., min_length=1, max_length=200)
    ctx: str = Field("", max_length=400)
    # Round-7 audit fix: accept optional `ctx_en` so the same call can keep
    # bilingual coverage. UI sends both when admin edits an item that needs
    # an EN version too. None means "don't touch", "" means "clear it".
    ctx_en: Optional[str] = Field(default=None, max_length=400)


class CategoryPatchIn(BaseModel):
    """Admin god-mode (2026-05-11): patch top-level fields on a published
    category in categories.json. Currently supports cluster move (rename or
    move to existing/new cluster) and display name. Items + archetypes are
    edited via separate endpoints — this is for the wrapper metadata only.

    All fields optional; pass only what you want to change.
    `cluster` MAY name a cluster that doesn't exist yet — the home screen
    auto-groups by cluster string, so typing "Криптовалюта" instantly creates
    that section on the public page after refresh."""
    cluster: Optional[str] = Field(default=None, min_length=1, max_length=80)
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    # Hide from home screen without deleting (soft toggle that's already in
    # the admin UI but was wired through localStorage overrides; this puts
    # it server-side so it persists across devices).
    hidden: Optional[bool] = Field(default=None)


@app.post("/api/admin/items/set-ctx")
def admin_item_set_ctx(body: SetCtxIn,
                        _role: str = Depends(require_mod_or_admin),
                        actor: dict = Depends(get_admin_actor)):
    """Update the `ctx` (one-line description) of a single item in categories.json.

    Used by the copy-paste workflow: admin pastes the response from claude.ai
    (or types manually) and saves.

    Round-7 audit fix: was previously the last admin endpoint that wrote
    `categories.json` directly without (a) running the validator and (b)
    using `_save_categories()` (so no rotated backup, no in-process cache
    invalidation). Now uses the same snapshot+validate+rollback pattern as
    theme/item PATCH (sections 13.1, 13.2 of the audit bundle), and accepts
    an optional `ctx_en` so the call doesn't introduce a bilingual gap.
    """
    cats = _load_categories()
    cat = next((c for c in cats if c.get("id") == body.category_id), None)
    if not cat:
        raise HTTPException(404, "category_not_found")
    item = next((it for it in (cat.get("items") or []) if it.get("id") == body.item_id), None)
    if not item:
        raise HTTPException(404, "item_not_found")

    old_ctx = item.get("ctx", "")
    old_ctx_en = item.get("ctx_en", "")
    new_ctx = (body.ctx or "").strip()
    item["ctx"] = new_ctx
    # ctx_en: only touched when caller explicitly provided it (None = leave alone)
    new_ctx_en = old_ctx_en
    if body.ctx_en is not None:
        new_ctx_en = body.ctx_en.strip()
        item["ctx_en"] = new_ctx_en

    # Validate the mutated theme. Same pattern as theme/item PATCH: rollback
    # in-memory state on errors so the admin can retry without drift.
    errors, warnings = _validate_category_for_publish(cat)
    if errors:
        item["ctx"] = old_ctx
        if body.ctx_en is not None:
            item["ctx_en"] = old_ctx_en
        raise HTTPException(
            status_code=422,
            detail={"reason": "validation_failed", "errors": errors, "warnings": warnings,
                    "hint": "Most common cause: setting `ctx` while `ctx_en` is empty (or vice versa). Pass both fields to keep bilingual coverage."},
        )

    _save_categories(cats)

    # Audit trail
    with db() as conn:
        log_admin_action(conn, actor, "item_set_ctx", item.get("name", ""), {
            "category_id": body.category_id,
            "item_id": body.item_id,
            "old_ctx": old_ctx,
            "new_ctx": new_ctx,
            "old_ctx_en": old_ctx_en if body.ctx_en is not None else None,
            "new_ctx_en": new_ctx_en if body.ctx_en is not None else None,
        })

    return {
        "ok": True,
        "item": {
            "id": body.item_id,
            "name": item.get("name"),
            "ctx": new_ctx,
            "ctx_en": new_ctx_en,
        },
        "category_id": body.category_id,
        "previous_ctx": old_ctx,
        "warnings": warnings,
    }


class ApplyCategoryIn(BaseModel):
    submission_id: int = Field(..., gt=0)
    json_text: str = Field(..., min_length=20, max_length=200_000)
    publish: bool = Field(default=True)


def _validate_category_for_publish(cat: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a parsed category dict.

    Errors BLOCK publish (T1, T2, T3 violations + missing _en + structural).
    Warnings ALLOW publish but surface to admin (T4 overlap + length nits).
    Mirrors the moderator-facing preview checks in admin.html so server-side
    can never accept categories the UI marked as broken.
    """
    errors: list[str] = []
    warnings: list[str] = []

    items = cat.get("items") or []
    archs = cat.get("archetypes") or []
    default_arch = cat.get("defaultArchetype") or {}

    # Structural minimums
    if not items:
        errors.append("structural: items array is empty")
    if not archs:
        errors.append("structural: archetypes array is empty")
    if not default_arch.get("name") or not default_arch.get("body"):
        errors.append("structural: defaultArchetype missing name or body")

    # Bilingual coverage — every user-facing field needs _en sibling
    if cat.get("name") and not cat.get("name_en"):
        errors.append("bilingual: category.name_en missing")
    if cat.get("blurb") and not cat.get("blurb_en"):
        errors.append("bilingual: category.blurb_en missing")
    for it in items:
        if it.get("name") and not it.get("name_en"):
            errors.append(f"bilingual: items[{it.get('id','?')}].name_en missing")
        if it.get("ctx") and not it.get("ctx_en"):
            errors.append(f"bilingual: items[{it.get('id','?')}].ctx_en missing")
    for a in archs:
        if a.get("name") and not a.get("name_en"):
            errors.append(f"bilingual: archetype «{a.get('name','?')}».name_en missing")
        if a.get("body") and not a.get("body_en"):
            errors.append(f"bilingual: archetype «{a.get('name','?')}».body_en missing")
    if default_arch.get("name") and not default_arch.get("name_en"):
        errors.append("bilingual: defaultArchetype.name_en missing")
    if default_arch.get("body") and not default_arch.get("body_en"):
        errors.append("bilingual: defaultArchetype.body_en missing")

    # Structural: archetype triggers must reference real item ids. A typo like
    # 'broken-i999' that doesn't match any items[].id would silently never fire
    # at runtime, reducing effective trigger count and corrupting profiles.
    # (Round-3 audit fix 2026-05-08.)
    item_ids = [it["id"] for it in items if it.get("id")]
    item_id_set = set(item_ids)
    invalid_triggers = []
    for a in archs:
        a_name = a.get("name", "?")
        for tid in (a.get("triggers") or []):
            if tid not in item_id_set:
                invalid_triggers.append((a_name, tid))
    if invalid_triggers:
        examples = ", ".join(f"«{n}»→{t}" for n, t in invalid_triggers[:5])
        errors.append(f"structural: {len(invalid_triggers)} archetype triggers reference non-existent items: {examples}")

    # T1: every item must be in at least one archetype's triggers (only counts
    # valid trigger references — invalid ones already flagged above).
    appearance: dict[str, int] = {iid: 0 for iid in item_ids}
    for a in archs:
        for tid in (a.get("triggers") or []):
            if tid in item_id_set:
                appearance[tid] = appearance.get(tid, 0) + 1
    dead = [iid for iid in item_ids if appearance.get(iid, 0) == 0]
    if dead:
        errors.append(f"T1: {len(dead)} dead items (not in any archetype): {', '.join(dead[:5])}{'...' if len(dead) > 5 else ''}")

    # T2: no item in 3+ archetypes
    overload = [(iid, c) for iid, c in appearance.items() if c >= 3]
    if overload:
        errors.append(f"T2: {len(overload)} overloaded items (in 3+ archetypes): {', '.join(f'{i}({c})' for i, c in overload[:5])}")

    # T3: every archetype has 2-5 triggers
    bad_t3 = [(a.get("name", "?"), len(a.get("triggers") or [])) for a in archs
              if not (2 <= len(a.get("triggers") or []) <= 5)]
    if bad_t3:
        errors.append(f"T3: {len(bad_t3)} archetypes with trigger count outside 2-5: {', '.join(f'«{n}»({c}t)' for n, c in bad_t3[:5])}")

    # T4: pairwise trigger overlap (warning only)
    for i, a in enumerate(archs):
        for j in range(i + 1, len(archs)):
            sa = set(a.get("triggers") or [])
            sb = set(archs[j].get("triggers") or [])
            if not sa or not sb:
                continue
            common = sa & sb
            denom = min(len(sa), len(sb))
            ratio = len(common) / denom if denom else 0
            if ratio > 0.5:
                warnings.append(f"T4: «{a.get('name')}» × «{archs[j].get('name')}» overlap = {round(100*ratio)}%")

    return errors, warnings


@app.post("/api/admin/categories/apply-from-json")
def admin_apply_category_from_json(body: ApplyCategoryIn,
                                    _role: str = Depends(require_mod_or_admin),
                                    actor: dict = Depends(get_admin_actor)):
    """Take a Claude-generated JSON for a whole new category, validate it, and
    add it to categories.json. Used by the copy-prompt workflow for
    type='category' submissions.

    Validation:
      - Must be a JSON object with `name`, `blurb`, `items`.
      - `items` must be a non-empty array of objects with `name` (each).
      - Auto-fills missing `id` (slugify), `cluster`, `category_type`,
        `category_subtype`, `recommended_tournament_size`, `is_experimental`,
        `archetypes`, `defaultArchetype`.
      - Rejects if a category with the same id already exists.
    Returns the parsed category object so admin can preview before final save
    (publish=true commits, publish=false just validates).
    """
    # Get the submission for context (submitter id, target_category for items, title fallback)
    with db() as conn:
        sub_row = conn.execute("SELECT * FROM submissions WHERE id = ?", (body.submission_id,)).fetchone()
        if not sub_row:
            raise HTTPException(404, "submission_not_found")
        if sub_row["type"] != "category":
            raise HTTPException(400, "submission_not_category_type")
        submitter_id = sub_row["user_id"]
        submitter_nick = None
        if submitter_id:
            u = conn.execute("SELECT nickname FROM users WHERE id = ?", (submitter_id,)).fetchone()
            if u:
                submitter_nick = u["nickname"]

    # Parse incoming JSON. Strip ```json fences if Claude added them.
    raw = body.json_text.strip()
    # Strip code fences
    if raw.startswith("```"):
        # Drop first ```... line and final ```
        lines = raw.split("\n")
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        cat = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(422, f"json_parse_failed: line {e.lineno} col {e.colno}: {e.msg}")
    if not isinstance(cat, dict):
        raise HTTPException(422, "json_must_be_object")

    # Required fields
    name = str(cat.get("name", "")).strip()
    blurb = str(cat.get("blurb", "")).strip()
    items_in = cat.get("items")
    if not name:
        raise HTTPException(422, "name_required")
    if not blurb:
        raise HTTPException(422, "blurb_required")
    if not isinstance(items_in, list) or len(items_in) < 4:
        raise HTTPException(422, "items_must_be_list_of_4_or_more")

    # Build category id (slugify if not provided)
    cat_id = str(cat.get("id", "") or _slugify_id(name)).strip()
    cat_id = re.sub(r'[^a-z0-9_]+', '_', cat_id.lower())[:64].strip('_')
    if not cat_id:
        raise HTTPException(422, "could_not_derive_category_id")

    # Sanitise items
    items_out = []
    used_ids = set()
    now = now_iso()
    for idx, it in enumerate(items_in):
        if not isinstance(it, dict):
            raise HTTPException(422, f"items[{idx}]_not_object")
        nm = str(it.get("name", "")).strip()
        if not nm:
            raise HTTPException(422, f"items[{idx}]_missing_name")
        ctx = str(it.get("ctx", "")).strip()[:400]
        # Generate id if missing or non-unique
        item_id = str(it.get("id", "") or "").strip()
        if not item_id:
            item_id = f"{cat_id}-{_slugify_id(nm)}"
        item_id = re.sub(r'[^a-zA-Z0-9_\-]+', '-', item_id)[:120].strip('-')
        base = item_id; n = 2
        while item_id in used_ids:
            item_id = f"{base}-{n}"; n += 1
        used_ids.add(item_id)
        new_it = {"id": item_id, "name": nm, "ctx": ctx}
        # Preserve any extra fields Claude added (genre, tags, etc.) but skip None
        for k, v in it.items():
            if k not in new_it and v is not None:
                new_it[k] = v
        items_out.append(new_it)

    # 2026-06-08: ранее размер снэппился к ближайшему {4,8,16,32,64}.
    # Сняли — single-elimination бракет умеет любое N через byes (см. коммент
    # в _commit_result_for_user). Модератор задаёт точное число (44/48/etc),
    # бэк только клампит к диапазону [2, items_count].
    raw_size = int(cat.get("recommended_tournament_size") or len(items_out))
    rec_size = max(2, min(raw_size, len(items_out)))

    final = {
        "id": cat_id,
        "name": name,
        "name_en": cat.get("name_en") or None,    # Round-3 audit fix: was being
        "blurb": blurb,                            # dropped from final, then
        "blurb_en": cat.get("blurb_en") or None,   # validator demanded it back.
        "category_type": str(cat.get("category_type") or "general").lower(),
        "category_subtype": str(cat.get("category_subtype") or "entertainment").lower(),
        "cluster": str(cat.get("cluster") or sub_row["cluster"] or "Сообщество"),
        "recommended_tournament_size": rec_size,
        "is_experimental": bool(cat.get("is_experimental", False)),
        "items": items_out,
        "archetypes": cat.get("archetypes") if isinstance(cat.get("archetypes"), list) else [],
        "defaultArchetype": cat.get("defaultArchetype") if isinstance(cat.get("defaultArchetype"), dict) else {
            "name": "По умолчанию",
            "body": "Один из вариантов нашёл отклик.",
        },
        "submitted_by": submitter_nick,
        "submitted_at": now,
    }
    if cat.get("gender_scope") in ("male", "female"):
        final["gender_scope"] = cat["gender_scope"]

    # Server-side T1-T6 + bilingual validator. Mirrors admin.html preview.
    # Errors block; warnings allow but surface to admin in the preview response.
    errors, warnings = _validate_category_for_publish(final)

    # Dry run (preview): never blocks, just returns parsed + validator results.
    if not body.publish:
        return {
            "preview": final,
            "would_create_id": cat_id,
            "validation": {"errors": errors, "warnings": warnings},
        }

    # Publish: hard-block on validation errors. Admin must fix and retry.
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"reason": "validation_failed", "errors": errors, "warnings": warnings},
        )

    # Write to categories.json
    if not CATEGORIES_JSON_PATH.exists():
        raise HTTPException(503, "categories_json_missing")
    try:
        data = json.loads(CATEGORIES_JSON_PATH.read_text(encoding='utf-8'))
    except Exception as e:
        raise HTTPException(500, f"categories_load_failed: {e}")
    if any(c.get("id") == cat_id for c in data):
        raise HTTPException(409, f"category_id_already_exists: {cat_id}")

    # Insert before any name_tournament block to keep that one last
    insert_idx = len(data)
    for i, c in enumerate(data):
        if c.get("is_name_tournament"):
            insert_idx = i
            break
    data.insert(insert_idx, final)

    # Audit re-review M-3 (CHUNK A): use the central _save_categories() so
    # we get the rotated backup + threading lock + cache invalidation. The
    # previous direct-tmp-write skipped backups (a fresh insert that broke
    # things would have been unrecoverable from rotated history).
    try:
        _save_categories(data)
    except Exception as e:
        raise HTTPException(500, f"categories_write_failed: {e}")

    # Audit + atomically mark the submission as approved (single source of truth:
    # a category submission only becomes 'approved' when the actual category is published).
    with db() as conn:
        conn.execute(
            # Round-4 audit fix: actor dict has 'user_id' (named-mod sessions),
            # not 'id'. Old code wrote NULL for every named-moderator publish.
            "UPDATE submissions SET status = 'approved', decided_at = ?, decided_by = ? WHERE id = ?",
            (now_iso(), (actor or {}).get('user_id'), body.submission_id),
        )
        log_admin_action(conn, actor, "category_published", final["name"], {
            "submission_id": body.submission_id,
            "category_id": cat_id,
            "items_count": len(items_out),
        })

    # Notify admin clients that this submission moved to approved + a real category exists
    with db() as conn:
        new_row = conn.execute("SELECT * FROM submissions WHERE id = ?", (body.submission_id,)).fetchone()
    if new_row:
        publish_admin_event_sync('submission_updated', submission_to_dict(new_row))
        # 2026-05-16: push the submitter to celebrate their category going live.
        try:
            sub_uid = int(new_row["user_id"]) if new_row["user_id"] else None
            sub_title = new_row["title"] or final.get("name") or "тема"
            if sub_uid:
                _notify_submission_approved(sub_uid, "category", sub_title, cat_id)
        except Exception as e:
            logger.warning("submission-approved push wrap failed: %s", e)
    return {"created": True, "category_id": cat_id, "category": final, "warnings": warnings}


@app.patch("/api/admin/categories/{cat_id}")
def admin_patch_category(cat_id: str,
                          body: CategoryPatchIn,
                          _role: str = Depends(require_mod_or_admin),
                          actor: dict = Depends(get_admin_actor)):
    """Edit metadata of an already-published category. Only fields the caller
    actually sends are touched.

    Most common use: move a category to a different cluster (typing a new
    cluster string creates a new home-screen section automatically — clusters
    are not a separate enumeration, just whatever string each category claims).

    Validation: the mutated category must still pass `_validate_category_for_publish`.
    On failure we ROLL BACK the in-memory change and return 422 with the
    validator's error list, leaving categories.json untouched.
    """
    cats = _load_categories()
    cat = next((c for c in cats if c.get("id") == cat_id), None)
    if not cat:
        raise HTTPException(404, "category_not_found")

    edited = {}
    if body.cluster is not None:
        old = cat.get("cluster")
        new = body.cluster.strip()
        if new == "":
            raise HTTPException(422, "cluster_cannot_be_empty")
        if old != new:
            cat["cluster"] = new
            edited["cluster"] = {"old": old, "new": new}
    if body.name is not None:
        old = cat.get("name")
        new = body.name.strip()
        if new == "":
            raise HTTPException(422, "name_cannot_be_empty")
        if old != new:
            cat["name"] = new
            edited["name"] = {"old": old, "new": new}
    if body.hidden is not None:
        old = bool(cat.get("hidden", False))
        new = bool(body.hidden)
        if old != new:
            cat["hidden"] = new
            edited["hidden"] = {"old": old, "new": new}

    if not edited:
        return {"ok": True, "category": cat, "no_changes": True}

    # Validate before persisting. On failure, restore the original values
    # (we have them in `edited`) and return 422.
    errors, warnings = _validate_category_for_publish(cat)
    if errors:
        # Roll back in-memory state so the loaded cats list isn't poisoned
        # for any subsequent ops in the same process.
        for field, change in edited.items():
            cat[field] = change["old"]
        raise HTTPException(
            status_code=422,
            detail={"reason": "validation_failed", "errors": errors, "warnings": warnings},
        )

    _save_categories(cats)

    with db() as conn:
        log_admin_action(conn, actor, "category_patched", cat.get("name", cat_id), {
            "category_id": cat_id,
            "edited": edited,
        })

    return {"ok": True, "category": cat, "edited": edited, "warnings": warnings}


@app.post("/api/admin/items/generate-ctx")
def admin_item_generate_ctx(body: SetCtxIn, _role: str = Depends(require_mod_or_admin)):
    """Generate ctx via Claude API for an existing item without saving.

    Returns {ctx, error}. Frontend gets the suggestion, admin can edit before
    calling /set-ctx to commit. The body.ctx field is ignored here.
    """
    if not CATEGORIES_JSON_PATH.exists():
        raise HTTPException(503, "categories_json_missing")
    try:
        data = json.loads(CATEGORIES_JSON_PATH.read_text(encoding='utf-8'))
    except Exception as e:
        raise HTTPException(500, f"categories_load_failed: {e}")
    cat = next((c for c in data if c.get("id") == body.category_id), None)
    if not cat:
        raise HTTPException(404, "category_not_found")
    item = next((it for it in (cat.get("items") or []) if it.get("id") == body.item_id), None)
    if not item:
        raise HTTPException(404, "item_not_found")
    name = item.get("name", "")
    ctx, err = _generate_item_ctx(cat, name)
    return {"ctx": ctx, "error": err, "model": ANTHROPIC_MODEL if not err else None}


# ─── ADMIN USER VIEWER ─────────────────────────────────────────

@app.get("/api/admin/mod-activity")
def admin_mod_activity(
    _admin: bool = Depends(require_admin),
    user_id: int | None = None,
    action: str | None = None,
    limit: int = 200,
):
    """All admin_actions performed by named moderators (admin_user_id IS NOT NULL).
    Excludes full-admin actions (those have NULL admin_user_id by design).

    Optional filters:
      - user_id: only actions by a specific moderator
      - action: only specific action type (e.g. 'submission_approved')
    """
    limit = max(1, min(500, limit))
    where_parts = ["a.admin_user_id IS NOT NULL"]
    params: list = []
    if user_id is not None:
        where_parts.append("a.admin_user_id = ?")
        params.append(user_id)
    if action:
        where_parts.append("a.action = ?")
        params.append(action)
    where_sql = " AND ".join(where_parts)

    with db() as conn:
        rows = conn.execute(
            f"""SELECT a.id, a.admin_user_id, u.nickname AS admin_nickname, u.role AS admin_role,
                       a.action, a.target, a.extras_json, a.at
                FROM admin_actions a
                LEFT JOIN users u ON u.id = a.admin_user_id
                WHERE {where_sql}
                ORDER BY a.at DESC LIMIT ?""",
            params + [limit]
        ).fetchall()
        # Per-moderator summary (counts by action type)
        summary_rows = conn.execute(
            """SELECT a.admin_user_id, u.nickname, COUNT(*) AS total,
                       MAX(a.at) AS last_at,
                       SUM(CASE WHEN a.action LIKE 'submission_approved%' THEN 1 ELSE 0 END) AS approvals,
                       SUM(CASE WHEN a.action LIKE 'submission_rejected%' THEN 1 ELSE 0 END) AS rejections,
                       SUM(CASE WHEN a.action = 'submission_edited' THEN 1 ELSE 0 END) AS edits,
                       SUM(CASE WHEN a.action = 'item_set_ctx' THEN 1 ELSE 0 END) AS ctx_edits,
                       SUM(CASE WHEN a.action = 'category_published' THEN 1 ELSE 0 END) AS publishes
                FROM admin_actions a
                LEFT JOIN users u ON u.id = a.admin_user_id
                WHERE a.admin_user_id IS NOT NULL
                GROUP BY a.admin_user_id
                ORDER BY total DESC"""
        ).fetchall()

    actions = []
    for r in rows:
        try:
            extras = json.loads(r['extras_json']) if r['extras_json'] else None
        except Exception:
            extras = None
        actions.append({
            "id": r['id'],
            "admin_user_id": r['admin_user_id'],
            "admin_nickname": r['admin_nickname'],
            "admin_role": r['admin_role'],
            "action": r['action'],
            "target": r['target'],
            "extras": extras,
            "at": r['at'],
        })
    summary = [dict(r) for r in summary_rows]
    return {"actions": actions, "summary": summary, "total": len(actions)}


@app.get("/api/admin/users")
def admin_list_users(
    _admin: bool = Depends(require_admin),
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """List users with aggregate stats. Optionally filter by nickname/email substring (`q`)."""
    limit = max(1, min(500, limit))
    offset = max(0, offset)
    where = ""
    params: list = []
    if q:
        where = "WHERE u.nickname LIKE ? COLLATE NOCASE OR u.email LIKE ? COLLATE NOCASE"
        like = f"%{q}%"
        params.extend([like, like])
    sql = f"""
        SELECT u.id, u.nickname, u.email, u.avatar_glyph, u.created_at, u.last_login_at,
               u.is_admin, u.role, u.is_paid,
               (SELECT COUNT(*) FROM results r WHERE r.user_id = u.id)            AS results_count,
               (SELECT COUNT(*) FROM submissions s WHERE s.user_id = u.id)        AS submissions_count,
               (SELECT COUNT(*) FROM friendships f WHERE f.user_id = u.id AND f.status = 'accepted') AS friends_count,
               (SELECT MAX(completed_at) FROM results r WHERE r.user_id = u.id)   AS last_result_at,
               (SELECT MAX(submitted_at) FROM submissions s WHERE s.user_id = u.id) AS last_submission_at
        FROM users u
        {where}
        ORDER BY u.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    with db() as conn:
        rows = conn.execute(sql, params).fetchall()
        total = conn.execute(
            f"SELECT COUNT(*) FROM users u {where}",
            params[:-2] if where else []
        ).fetchone()[0]
    return {
        "users": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/admin/users/{user_id}")
def admin_user_detail(user_id: int, _admin: bool = Depends(require_admin)):
    """Full activity dump for one user: profile, results, submissions, friends, related admin actions."""
    with db() as conn:
        u = conn.execute(
            """SELECT id, nickname, email, avatar_glyph, created_at, last_login_at,
                      is_admin, role, is_paid, email_verified, social_providers, badges
               FROM users WHERE id = ?""",
            (user_id,)
        ).fetchone()
        if not u:
            raise HTTPException(404, "user_not_found")
        results = conn.execute(
            "SELECT * FROM results WHERE user_id = ? ORDER BY completed_at DESC LIMIT 200",
            (user_id,)
        ).fetchall()
        submissions = conn.execute(
            "SELECT * FROM submissions WHERE user_id = ? ORDER BY submitted_at DESC LIMIT 200",
            (user_id,)
        ).fetchall()
        # Friends: outgoing accepted (we joined friend_user_id) — we keep the schema simple here
        friends = conn.execute(
            """SELECT f.id, f.status, f.created_at, f.responded_at,
                      u2.id AS friend_user_id, u2.nickname AS friend_nickname,
                      u2.avatar_glyph AS friend_avatar_glyph
               FROM friendships f
               JOIN users u2 ON u2.id = f.friend_user_id
               WHERE f.user_id = ?
               ORDER BY f.created_at DESC""",
            (user_id,)
        ).fetchall()
        # Admin actions touching this user: their submissions OR their nickname as target.
        # Audit H9: rewritten to use ? placeholders for every value (sid is a
        # server-side int, so f-string was technically safe, but the pattern
        # is fragile and rots — one wrong cast and the query becomes injectable).
        nick = u['nickname']
        sub_ids = [r['id'] for r in submissions]
        admin_actions: list = []
        if sub_ids:
            or_clauses: list[str] = []
            params: list = [nick]
            for sid in sub_ids:
                or_clauses.append(
                    "extras_json LIKE ? OR extras_json LIKE ? OR extras_json LIKE ?"
                )
                params.extend([
                    f'%"id": {int(sid)}%',
                    f'%"id":{int(sid)},%',
                    f'%"id":{int(sid)}' + '}%',
                ])
            admin_actions = conn.execute(
                "SELECT * FROM admin_actions "
                "WHERE (target = ? OR (action LIKE 'submission_%' "
                "  AND extras_json LIKE '%\"id\":%' AND ("
                + " OR ".join(or_clauses) + "))) "
                "ORDER BY at DESC LIMIT 200",
                params,
            ).fetchall()
        else:
            admin_actions = conn.execute(
                "SELECT * FROM admin_actions WHERE target = ? ORDER BY at DESC LIMIT 200",
                (nick,)
            ).fetchall()
    return {
        "user": dict(u),
        "results": [dict(r) for r in results],
        "submissions": [submission_to_dict(r) for r in submissions],
        "friends": [dict(f) for f in friends],
        "admin_actions": [dict(a) for a in admin_actions],
    }


# ─── ADMIN: CLUSTERS / THEMES / RESULTS DRILL-DOWN ──────────────
# Drives the new "Кластеры" sidebar section. Three levels of detail:
#   /api/admin/clusters              → list all clusters with theme + play counts
#   /api/admin/clusters/{cl}/themes  → themes inside one cluster with stats
#   /api/admin/themes/{tid}          → full theme detail (items, win stats, recent results)
# Plus /api/admin/results for the fixed "Турниры" view (server-wide, not localStorage).

@app.get("/api/admin/clusters")
def admin_clusters(_admin: bool = Depends(require_admin)):
    """List all clusters with theme counts and total play counts.
    Sorted by play count descending so most-active clusters bubble up."""
    cats = _load_categories()
    by_cluster: dict = {}
    for c in cats:
        cl = c.get("cluster") or "(без кластера)"
        if cl not in by_cluster:
            by_cluster[cl] = {"cluster": cl, "themes_count": 0, "theme_ids": []}
        by_cluster[cl]["themes_count"] += 1
        by_cluster[cl]["theme_ids"].append(c.get("id"))

    with db() as conn:
        rows = conn.execute(
            "SELECT category_id, COUNT(*) AS c FROM results GROUP BY category_id"
        ).fetchall()
    plays_by_cat = {r["category_id"]: r["c"] for r in rows}

    out = []
    for cl, d in by_cluster.items():
        plays = sum(plays_by_cat.get(tid, 0) for tid in d["theme_ids"])
        out.append({
            "cluster": cl,
            "themes_count": d["themes_count"],
            "plays_count": plays,
        })
    out.sort(key=lambda x: (-x["plays_count"], x["cluster"]))
    return {
        "clusters": out,
        "total_themes": sum(d["themes_count"] for d in by_cluster.values()),
        "total_plays": sum(plays_by_cat.values()),
    }


@app.get("/api/admin/clusters/{cluster_name}/themes")
def admin_cluster_themes(cluster_name: str, _admin: bool = Depends(require_admin)):
    """Themes inside a single cluster with play counts and most-frequent winner.
    Empty clusters return an empty list, not 404 (helps the UI show 'no themes yet')."""
    cats = _load_categories()
    themes = [c for c in cats if (c.get("cluster") or "(без кластера)") == cluster_name]
    if not themes:
        return {"cluster": cluster_name, "themes": []}

    theme_ids = [c.get("id") for c in themes]
    placeholders = ",".join(["?"] * len(theme_ids))
    with db() as conn:
        plays_rows = conn.execute(
            f"SELECT category_id, COUNT(*) AS c FROM results WHERE category_id IN ({placeholders}) GROUP BY category_id",
            theme_ids,
        ).fetchall()
        plays_by_cat = {r["category_id"]: r["c"] for r in plays_rows}

        # Top winner per theme — most frequent top1_id (one query per theme; OK for ~80 themes)
        top_winners = {}
        for tid in theme_ids:
            row = conn.execute(
                """SELECT top1_id, top1_name, COUNT(*) AS c FROM results
                   WHERE category_id = ? AND top1_id IS NOT NULL
                   GROUP BY top1_id ORDER BY c DESC LIMIT 1""",
                (tid,),
            ).fetchone()
            if row:
                top_winners[tid] = {"id": row["top1_id"], "name": row["top1_name"], "wins": row["c"]}

    out = []
    for c in themes:
        cid = c.get("id")
        out.append({
            "id": cid,
            "name": c.get("name"),
            "blurb": c.get("blurb"),
            "items_count": len(c.get("items") or []),
            "plays_count": plays_by_cat.get(cid, 0),
            "top_winner": top_winners.get(cid),
            "is_experimental": bool(c.get("is_experimental", False)),
            "is_visible": bool(c.get("is_visible", True)),
            "category_subtype": c.get("category_subtype"),
            "recommended_tournament_size": c.get("recommended_tournament_size"),
        })
    out.sort(key=lambda x: (-x["plays_count"], x["name"] or ""))
    return {"cluster": cluster_name, "themes": out}


@app.get("/api/admin/themes/{theme_id}")
def admin_theme_detail(theme_id: str, _admin: bool = Depends(require_admin)):
    """Full theme detail: every item with podium statistics + recent results."""
    cats = _load_categories()
    theme = next((c for c in cats if c.get("id") == theme_id), None)
    if not theme:
        raise HTTPException(404, "theme_not_found")

    items = theme.get("items") or []
    with db() as conn:
        plays_total = conn.execute(
            "SELECT COUNT(*) FROM results WHERE category_id = ?", (theme_id,)
        ).fetchone()[0]

        # Per-item win stats across all 3 podium positions
        win_stats: dict = {}
        for pos in (1, 2, 3):
            rows = conn.execute(
                f"SELECT top{pos}_id AS iid, COUNT(*) AS c FROM results "
                f"WHERE category_id = ? AND top{pos}_id IS NOT NULL GROUP BY top{pos}_id",
                (theme_id,),
            ).fetchall()
            for r in rows:
                ws = win_stats.setdefault(r["iid"], {"top1": 0, "top2": 0, "top3": 0})
                ws[f"top{pos}"] = r["c"]

        recent_rows = conn.execute(
            """SELECT r.id, r.user_id, u.nickname, r.top1_name, r.top2_name, r.top3_name,
                      r.archetype_name, r.completed_at
               FROM results r LEFT JOIN users u ON u.id = r.user_id
               WHERE r.category_id = ? ORDER BY r.completed_at DESC LIMIT 30""",
            (theme_id,),
        ).fetchall()

    items_out = []
    for it in items:
        iid = it.get("id")
        ws = win_stats.get(iid, {"top1": 0, "top2": 0, "top3": 0})
        items_out.append({
            "id": iid,
            "name": it.get("name"),
            "ctx": it.get("ctx"),
            "top1_count": ws["top1"],
            "top2_count": ws["top2"],
            "top3_count": ws["top3"],
            "podium_count": ws["top1"] + ws["top2"] + ws["top3"],
        })
    items_out.sort(key=lambda x: (-x["top1_count"], -x["podium_count"], x["name"] or ""))

    recent = [{
        "id": r["id"],
        "user_id": r["user_id"],
        "nickname": r["nickname"],
        "top1_name": r["top1_name"],
        "top2_name": r["top2_name"],
        "top3_name": r["top3_name"],
        "archetype_name": r["archetype_name"],
        "completed_at": r["completed_at"],
    } for r in recent_rows]

    # Round-7 audit fix: surface archetype names + trigger counts so the
    # add-item UI can render checkboxes for `add_to_archetypes`. Without
    # this, admin clicks "+ ДОБАВИТЬ", fills the form, hits save, and the
    # backend correctly rejects with 422 (T1 dead item) — but the UI has
    # no way to construct a valid payload.
    archs_summary = [
        {
            "name": a.get("name"),
            "name_en": a.get("name_en"),
            "triggers_count": len(a.get("triggers") or []),
        }
        for a in (theme.get("archetypes") or [])
        if a.get("name")
    ]
    return {
        "id": theme_id,
        "name": theme.get("name"),
        "blurb": theme.get("blurb"),
        "cluster": theme.get("cluster"),
        "category_type": theme.get("category_type"),
        "category_subtype": theme.get("category_subtype"),
        "is_experimental": bool(theme.get("is_experimental", False)),
        "is_visible": bool(theme.get("is_visible", True)),
        "recommended_tournament_size": theme.get("recommended_tournament_size"),
        "items_count": len(items),
        "plays_count": plays_total,
        "items": items_out,
        "archetypes": archs_summary,
        "recent_results": recent,
    }


@app.get("/api/admin/results")
def admin_results(
    limit: int = 100,
    offset: int = 0,
    cluster: Optional[str] = None,
    theme_id: Optional[str] = None,
    _admin: bool = Depends(require_admin),
):
    """All tournament results across all users — fixes the legacy admin
    'Турниры' view that only saw the local admin's own browser results.
    Filterable by cluster or single theme."""
    limit = max(1, min(500, limit))
    offset = max(0, offset)
    where = []
    params: list = []
    if theme_id:
        where.append("r.category_id = ?")
        params.append(theme_id)
    elif cluster:
        cats = _load_categories()
        theme_ids = [c.get("id") for c in cats if (c.get("cluster") or "(без кластера)") == cluster]
        if not theme_ids:
            return {"results": [], "total": 0, "limit": limit, "offset": offset}
        placeholders = ",".join(["?"] * len(theme_ids))
        where.append(f"r.category_id IN ({placeholders})")
        params.extend(theme_ids)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM results r {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""SELECT r.id, r.user_id, u.nickname, r.category_id, r.category_name,
                       r.top1_name, r.top2_name, r.top3_name, r.archetype_name,
                       r.completed_at, r.duration_sec, r.battles_played
                FROM results r LEFT JOIN users u ON u.id = r.user_id
                {where_sql}
                ORDER BY r.completed_at DESC LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()
    return {
        "results": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ─── ADMIN: THEMES + ITEMS CRUD ────────────────────────────────
# Direct admin editing of categories.json (theme metadata + variants).
# Each mutating operation: writes a timestamped backup, atomically replaces
# the file, invalidates in-memory caches, logs to admin_actions.
# Backups rotated to last 20 in same directory as categories.json.

class ThemePatchIn(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    name_en: Optional[str] = Field(default=None, max_length=120)
    blurb: Optional[str] = Field(default=None, max_length=280)
    blurb_en: Optional[str] = Field(default=None, max_length=280)
    cluster: Optional[str] = Field(default=None, max_length=50)
    recommended_tournament_size: Optional[int] = None
    is_visible: Optional[bool] = None
    is_experimental: Optional[bool] = None
    category_subtype: Optional[str] = Field(default=None, max_length=40)

    @field_validator('recommended_tournament_size')
    @classmethod
    def _size_valid(cls, v):
        if v is not None and v not in (4, 8, 16, 32, 64, 128):
            raise ValueError('size must be one of 4, 8, 16, 32, 64, 128')
        return v


class ItemCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    name_en: Optional[str] = Field(default=None, max_length=120)
    ctx: Optional[str] = Field(default="", max_length=400)
    ctx_en: Optional[str] = Field(default=None, max_length=400)
    # Round-5 audit fix: optional list of archetype names to add this item to
    # as a trigger. Solves "direct create can leave dead item" — caller can
    # batch the trigger assignment in the same request, validator passes.
    add_to_archetypes: Optional[list[str]] = Field(default=None)


class ItemPatchIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    name_en: Optional[str] = Field(default=None, max_length=120)
    ctx: Optional[str] = Field(default=None, max_length=400)
    ctx_en: Optional[str] = Field(default=None, max_length=400)


# Process-wide lock around categories writes. Audit M4: without this, two
# concurrent admin saves could race — both load the SAME pre-mutation
# version, each apply different edits, then last writer wins (silently
# losing the first edit). The lock serializes the load-mutate-save cycle.
# Note: only protects writes within THIS process; no protection against
# parallel uvicorn workers (we run a single worker, so safe).
_categories_save_lock = _Lock()


def _save_categories(cats: list) -> None:
    """Atomic write categories.json + rotated backup + cache invalidation.
    Serialized via _categories_save_lock to prevent admin-write races.
    Audit-11 P2.a: low-level write helper. For mutations (load → modify →
    save), use _mutate_categories() below — it holds the lock around the
    whole load-modify-save cycle so concurrent admin requests can't
    silently overwrite each other's edits."""
    with _categories_save_lock:
        _save_categories_unlocked(cats)


def _save_categories_unlocked(cats: list) -> None:
    """Internal: same as _save_categories but assumes the caller already
    holds _categories_save_lock. Used by _mutate_categories() to avoid
    re-entrant lock acquisition."""
    try:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        bak = CATEGORIES_JSON_PATH.parent / f"categories.json.bak.{ts}"
        bak.write_bytes(CATEGORIES_JSON_PATH.read_bytes())
        backups = sorted(CATEGORIES_JSON_PATH.parent.glob('categories.json.bak.*'))
        for old in backups[:-20]:
            try:
                old.unlink()
            except Exception:
                pass
    except Exception as e:
        logger.warning("categories backup failed: %s", e)
    tmp = CATEGORIES_JSON_PATH.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(cats, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(CATEGORIES_JSON_PATH)
    # Invalidate caches so subsequent reads pick up the new file
    _categories_full_cache["mtime"] = 0.0
    _categories_resolve_cache["mtime"] = 0.0


def _mutate_categories(fn):
    """Run `fn(categories_list) -> (mutated_list, return_value)` under the
    save lock so the entire load → mutate → save cycle is serialized.
    Audit-11 P2.a: previously the lock only covered the final write, which
    let two concurrent admin requests both load the same pre-state, both
    apply different edits, and the later writer silently clobbered the
    earlier one's change.

    fn receives the freshly-loaded list (NOT cached) and must return either
    the mutated list (if mutation succeeded) or raise to abort. The return
    value of fn is forwarded to the caller. fn may also return a tuple
    (mutated_list, extra_value) — _mutate_categories returns extra_value.
    """
    with _categories_save_lock:
        try:
            data = json.loads(CATEGORIES_JSON_PATH.read_text(encoding='utf-8'))
        except Exception as e:
            raise HTTPException(500, f"categories_load_failed: {e}")
        result = fn(data)
        if isinstance(result, tuple) and len(result) == 2:
            new_data, extra = result
        else:
            new_data, extra = result, None
        _save_categories_unlocked(new_data)
        return extra


def _make_unique_item_id(theme_id: str, name: str, used: set) -> str:
    """Generate a fresh item id within a theme. Suffix -2/-3/... on collisions."""
    base = f"{theme_id}-{_slugify_id(name)}"
    base = re.sub(r'[^a-zA-Z0-9_\-]+', '-', base)[:120].strip('-') or f"{theme_id}-item"
    item_id = base
    n = 2
    while item_id in used:
        item_id = f"{base}-{n}"
        n += 1
    return item_id


@app.patch("/api/admin/themes/{theme_id}")
def admin_theme_update(theme_id: str, body: ThemePatchIn,
                       _admin: bool = Depends(require_admin),
                       actor: dict = Depends(get_admin_actor)):
    """Patch any subset of theme fields (name, blurb, cluster, size, flags).

    Round-6 audit fix: runs the same validator as apply-from-json and rejects
    if the patch would clear required bilingual fields (name_en, blurb_en) or
    otherwise corrupt the category. Caller can patch non-structural flags
    (is_visible, is_featured) freely; user-facing text edits require the
    edited theme to still pass validation.
    """
    cats = _load_categories()
    theme = next((c for c in cats if c.get("id") == theme_id), None)
    if not theme:
        raise HTTPException(404, "theme_not_found")
    changes: dict = {}
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        if isinstance(v, str):
            v = v.strip()
            if k in ('name', 'cluster') and not v:
                raise HTTPException(422, f"{k}_cannot_be_empty")
        old = theme.get(k)
        if old != v:
            theme[k] = v
            changes[k] = {"from": old, "to": v}
    if not changes:
        return {"theme": theme, "changes": {}, "saved": False}

    # Validate the mutated theme. If errors (e.g. cleared name_en), roll back
    # the changes in-memory before returning 422 so caller can retry without
    # state drift.
    errors, warnings = _validate_category_for_publish(theme)
    if errors:
        for k, change in changes.items():
            theme[k] = change["from"]
        raise HTTPException(
            status_code=422,
            detail={"reason": "validation_failed", "errors": errors, "warnings": warnings,
                    "hint": "This patch leaves the category invalid. Most common cause: clearing name_en or blurb_en — keep both filled."},
        )

    _save_categories(cats)
    with db() as conn:
        log_admin_action(conn, actor, "theme_updated", theme.get("name", theme_id), {
            "theme_id": theme_id, "changes": changes,
        })
    return {"theme": theme, "changes": changes, "saved": True, "warnings": warnings}


@app.delete("/api/admin/themes/{theme_id}")
def admin_theme_delete(theme_id: str,
                       _admin: bool = Depends(require_admin),
                       actor: dict = Depends(get_admin_actor)):
    """Remove a theme entirely. Existing results stay in DB (orphaned by category_id)
    so historic statistics still resolve names from the result row."""
    cats = _load_categories()
    idx = next((i for i, c in enumerate(cats) if c.get("id") == theme_id), -1)
    if idx < 0:
        raise HTTPException(404, "theme_not_found")
    removed = cats.pop(idx)
    _save_categories(cats)
    with db() as conn:
        log_admin_action(conn, actor, "theme_deleted", removed.get("name", theme_id), {
            "theme_id": theme_id,
            "items_count": len(removed.get("items") or []),
            "cluster": removed.get("cluster"),
        })
    return {"deleted": True, "theme_id": theme_id, "name": removed.get("name")}


@app.post("/api/admin/themes/{theme_id}/items", status_code=201)
def admin_item_create(theme_id: str, body: ItemCreateIn,
                      _admin: bool = Depends(require_admin),
                      actor: dict = Depends(get_admin_actor)):
    """Append a variant to a theme + optional trigger assignment.

    Round-5 audit fix: validates the mutated category against T1-T6 + bilingual
    rules. If creation would leave the category broken (item is dead, archetype
    overload, missing EN, etc.), reject with 422 + errors list. Admin must
    either supply `add_to_archetypes` to attach the new item, or fix manually
    via separate archetype edit before retrying.
    """
    cats = _load_categories()
    theme = next((c for c in cats if c.get("id") == theme_id), None)
    if not theme:
        raise HTTPException(404, "theme_not_found")
    items = theme.setdefault("items", [])
    used = {it.get("id") for it in items if it.get("id")}
    new_id = _make_unique_item_id(theme_id, body.name, used)
    new_item = {"id": new_id, "name": body.name.strip(), "ctx": (body.ctx or "").strip()}
    if body.name_en and body.name_en.strip():
        new_item["name_en"] = body.name_en.strip()
    if body.ctx_en and body.ctx_en.strip():
        new_item["ctx_en"] = body.ctx_en.strip()
    items.append(new_item)

    # Optional: assign new item as trigger to specified archetypes (batch flow).
    archs = theme.get("archetypes") or []
    if body.add_to_archetypes:
        for a_name in body.add_to_archetypes:
            a = next((x for x in archs if x.get("name") == a_name), None)
            if not a:
                # Roll back — item not added, no save.
                items.pop()
                raise HTTPException(400, f"archetype_not_found: {a_name}")
            triggers = list(a.get("triggers") or [])
            if new_id not in triggers:
                triggers.append(new_id)
                a["triggers"] = triggers

    # Validate the mutated theme. Block if any errors (including missing EN,
    # T1 dead item, T3 trigger length out of range from over-assignment).
    errors, warnings = _validate_category_for_publish(theme)
    if errors:
        # Roll back (don't save). Strip any triggers we added.
        items.pop()
        if body.add_to_archetypes:
            for a in archs:
                t = a.get("triggers") or []
                if new_id in t:
                    a["triggers"] = [x for x in t if x != new_id]
        raise HTTPException(
            status_code=422,
            detail={"reason": "validation_failed", "errors": errors, "warnings": warnings,
                    "hint": "Set add_to_archetypes (list of archetype names) to attach this item, OR fix the category structure first."},
        )

    _save_categories(cats)
    with db() as conn:
        log_admin_action(conn, actor, "item_added", new_item["name"], {
            "theme_id": theme_id, "item_id": new_id,
            "added_to_archetypes": body.add_to_archetypes or [],
        })
    return {"item": new_item, "items_count": len(items), "warnings": warnings,
            "added_to_archetypes": body.add_to_archetypes or []}


@app.patch("/api/admin/themes/{theme_id}/items/{item_id}")
def admin_item_update(theme_id: str, item_id: str, body: ItemPatchIn,
                      _admin: bool = Depends(require_admin),
                      actor: dict = Depends(get_admin_actor)):
    """Patch name or ctx of one variant. id stays the same so result-row
    references survive.

    Round-6 audit fix: runs the same validator as apply-from-json. Rejects
    edits that clear required bilingual fields (name_en, ctx_en). Same
    snapshot+rollback pattern as item create/delete.
    """
    cats = _load_categories()
    theme = next((c for c in cats if c.get("id") == theme_id), None)
    if not theme:
        raise HTTPException(404, "theme_not_found")
    items = theme.get("items") or []
    item = next((it for it in items if it.get("id") == item_id), None)
    if not item:
        raise HTTPException(404, "item_not_found")
    changes: dict = {}
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        if isinstance(v, str):
            v = v.strip()
            if k == 'name' and not v:
                raise HTTPException(422, "name_cannot_be_empty")
        old = item.get(k)
        if old != v:
            item[k] = v
            changes[k] = {"from": old, "to": v}
    if not changes:
        return {"item": item, "changes": {}, "saved": False}

    # Validate the mutated theme. Same pattern as item create/delete:
    # roll back the in-memory changes if validator returns errors.
    errors, warnings = _validate_category_for_publish(theme)
    if errors:
        for k, change in changes.items():
            item[k] = change["from"]
        raise HTTPException(
            status_code=422,
            detail={"reason": "validation_failed", "errors": errors, "warnings": warnings,
                    "hint": "This patch leaves the category invalid. Most common cause: clearing name_en or ctx_en — keep both filled."},
        )

    _save_categories(cats)
    with db() as conn:
        log_admin_action(conn, actor, "item_updated", item.get("name", item_id), {
            "theme_id": theme_id, "item_id": item_id, "changes": changes,
        })
    return {"item": item, "changes": changes, "saved": True, "warnings": warnings}


@app.delete("/api/admin/themes/{theme_id}/items/{item_id}")
def admin_item_delete(theme_id: str, item_id: str,
                      _admin: bool = Depends(require_admin),
                      actor: dict = Depends(get_admin_actor)):
    """Remove a variant. Historical results referencing this item id stay
    in DB (orphaned), but admin sees them via per-result top1_name etc.

    Round-4 audit fix: also strip the deleted id from any archetype.triggers[]
    that references it. Otherwise we end up with phantom triggers — runtime
    scoring silently ignores them and the audit script can drift since the
    server validator now treats unknown trigger ids as structural errors."""
    cats = _load_categories()
    theme = next((c for c in cats if c.get("id") == theme_id), None)
    if not theme:
        raise HTTPException(404, "theme_not_found")
    items = theme.get("items") or []
    idx = next((i for i, it in enumerate(items) if it.get("id") == item_id), -1)
    if idx < 0:
        raise HTTPException(404, "item_not_found")

    # Snapshot for rollback if validation fails
    saved_items_snapshot = list(items)
    saved_triggers_snapshot = {a.get("name"): list(a.get("triggers") or []) for a in (theme.get("archetypes") or [])}

    removed = items.pop(idx)
    triggers_cleaned = 0
    for a in (theme.get("archetypes") or []):
        before = a.get("triggers") or []
        if item_id in before:
            a["triggers"] = [t for t in before if t != item_id]
            triggers_cleaned += 1

    # Round-5 audit fix: validate after stripping. If the removed item was a
    # critical trigger, an archetype may now be below T3 minimum (1 trigger),
    # or this could newly create a dead item. Reject and roll back; admin must
    # restructure archetype first (e.g. add a different trigger or delete arch).
    errors, warnings = _validate_category_for_publish(theme)
    if errors:
        # Roll back in-memory mutation
        theme["items"] = saved_items_snapshot
        for a in (theme.get("archetypes") or []):
            if a.get("name") in saved_triggers_snapshot:
                a["triggers"] = saved_triggers_snapshot[a.get("name")]
        raise HTTPException(
            status_code=422,
            detail={"reason": "validation_failed", "errors": errors, "warnings": warnings,
                    "hint": "Removing this item leaves the category invalid. Edit affected archetypes first (add a different trigger or delete the archetype)."},
        )

    _save_categories(cats)
    with db() as conn:
        log_admin_action(conn, actor, "item_deleted", removed.get("name", item_id), {
            "theme_id": theme_id, "item_id": item_id,
            "triggers_cleaned": triggers_cleaned,
        })
    return {"deleted": True, "item_id": item_id, "items_count": len(items),
            "triggers_cleaned": triggers_cleaned, "warnings": warnings}


# ─── FEEDBACK (general-purpose channel) ───────────────────────
# Replaces the old "suggest a variant" UI: too noisy, hard to moderate.
# Now users send free text + a coarse type. Admin reads, triages in admin UI.

ALLOWED_FB_TYPES = {'theme_idea', 'item_idea', 'bug', 'other'}
ALLOWED_FB_STATUSES = {'new', 'read', 'done', 'archived'}


class FeedbackIn(BaseModel):
    type: str = Field(..., min_length=1, max_length=20)
    text: str = Field(..., min_length=3, max_length=2000)
    email_for_reply: Optional[str] = Field(default=None, max_length=200)

    @field_validator('type')
    @classmethod
    def _type_valid(cls, v):
        if v not in ALLOWED_FB_TYPES:
            raise ValueError('invalid_type')
        return v

    @field_validator('email_for_reply')
    @classmethod
    def _email_valid(cls, v):
        if v is None or v == '':
            return None
        v = v.strip()
        if not v:
            return None
        # Audit M9: stronger validation via the same EmailStr machinery used
        # elsewhere (RegisterIn, etc). Defends against junk like "@.@" that
        # the previous loose check accepted.
        from pydantic import TypeAdapter
        try:
            return str(TypeAdapter(EmailStr).validate_python(v))
        except Exception:
            raise ValueError('invalid_email')


class FeedbackPatchIn(BaseModel):
    status: Optional[str] = None
    decision_note: Optional[str] = Field(default=None, max_length=500)

    @field_validator('status')
    @classmethod
    def _status_valid(cls, v):
        if v is not None and v not in ALLOWED_FB_STATUSES:
            raise ValueError('invalid_status')
        return v


@app.post("/api/feedback", status_code=201)
def submit_feedback(body: FeedbackIn, request: Request,
                    upg_session: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    """Anyone can submit feedback (auth optional). Rate-limit: 10 per 24h
    per user_id, or 10 per IP for anonymous (audit-6 L2: previously the
    anonymous bucket was global — one noisy guest could lock out everyone)."""
    # Optional auth
    user_id = None
    if upg_session:
        u = get_session_user(upg_session)
        if u:
            user_id = u['id']

    # Rate-limit: 10 per 24h per user_id (or per IP for anonymous).
    # The in-memory rate_limit() helper handles per-IP buckets cleanly;
    # we use the DB count only for authenticated users so the count
    # survives process restarts (signed-in user is the more important
    # case to enforce reliably).
    if user_id is None:
        rate_limit(request, "feedback_anon", max_attempts=10, window_sec=86400)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    with db() as conn:
        if user_id is not None:
            count_row = conn.execute(
                "SELECT COUNT(*) FROM feedback WHERE user_id = ? AND created_at >= ?",
                (user_id, cutoff)
            ).fetchone()
            if count_row[0] >= 10:
                raise HTTPException(429, "rate_limit_exceeded")

        cur = conn.execute(
            "INSERT INTO feedback (user_id, type, text, email_for_reply, status, created_at) "
            "VALUES (?, ?, ?, ?, 'new', ?)",
            (user_id, body.type, body.text.strip(), body.email_for_reply, now_iso())
        )
        new_id = cur.lastrowid
    return {"id": new_id, "ok": True}


@app.get("/api/admin/feedback")
def admin_list_feedback(
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
    _admin: bool = Depends(require_admin),
):
    """Admin: list feedback with optional filters."""
    limit = max(1, min(500, limit))
    offset = max(0, offset)
    if status is not None and status not in ALLOWED_FB_STATUSES and status != 'all':
        raise HTTPException(400, "invalid_status_filter")
    if type is not None and type not in ALLOWED_FB_TYPES and type != 'all':
        raise HTTPException(400, "invalid_type_filter")

    where = []
    params: list = []
    if status and status != 'all':
        where.append("f.status = ?")
        params.append(status)
    if type and type != 'all':
        where.append("f.type = ?")
        params.append(type)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM feedback f {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""SELECT f.id, f.user_id, u.nickname, f.type, f.text, f.email_for_reply,
                       f.status, f.created_at, f.decided_at, f.decision_note
                FROM feedback f LEFT JOIN users u ON u.id = f.user_id
                {where_sql}
                ORDER BY f.created_at DESC LIMIT ? OFFSET ?""",
            params + [limit, offset]
        ).fetchall()
        # Counts by status for sidebar tally
        counts_rows = conn.execute(
            "SELECT status, COUNT(*) AS c FROM feedback GROUP BY status"
        ).fetchall()
    counts = {r["status"]: r["c"] for r in counts_rows}
    return {
        "feedback": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
        "counts": counts,
    }


@app.patch("/api/admin/feedback/{fid}")
def admin_patch_feedback(fid: int, body: FeedbackPatchIn,
                          _admin: bool = Depends(require_admin),
                          actor: dict = Depends(get_admin_actor)):
    """Admin: update status / decision_note on a feedback entry."""
    with db() as conn:
        row = conn.execute("SELECT * FROM feedback WHERE id = ?", (fid,)).fetchone()
        if not row:
            raise HTTPException(404, "feedback_not_found")
        changes: dict = {}
        if body.status is not None and body.status != row["status"]:
            conn.execute(
                "UPDATE feedback SET status = ?, decided_at = ?, decided_by = ? WHERE id = ?",
                (body.status, now_iso(), actor.get('user_id'), fid)
            )
            changes["status"] = {"from": row["status"], "to": body.status}
        if body.decision_note is not None and body.decision_note != (row["decision_note"] or ''):
            conn.execute(
                "UPDATE feedback SET decision_note = ? WHERE id = ?",
                (body.decision_note, fid)
            )
            changes["decision_note"] = {"from": row["decision_note"], "to": body.decision_note}
        if changes:
            log_admin_action(conn, actor, "feedback_patched", "feedback#" + str(fid), {
                "feedback_id": fid, "changes": changes,
            })
        updated = conn.execute("SELECT * FROM feedback WHERE id = ?", (fid,)).fetchone()
    return {"feedback": dict(updated), "changes": changes}


# ─── SUBMISSIONS (UGC: new categories OR new items for existing categories) ──

@app.post("/api/submissions", status_code=201)
def submit(body: SubmissionIn, user: dict = Depends(require_user)):
    # Type-specific validation
    if body.type == 'item' and not body.target_category_id:
        raise HTTPException(400, "target_category_id required for type=item")
    if body.type == 'category' and not body.cluster:
        raise HTTPException(400, "cluster required for type=category")

    examples_json = json.dumps(body.examples or []) if body.examples else None
    with db() as conn:
        # Rate-limit bypass:
        #  - role IN ('moderator', 'admin') — staff posts as much as needed
        #  - submissions_unlimited flag — explicit per-user opt-out (set in DB)
        urow = conn.execute(
            "SELECT role, submissions_unlimited FROM users WHERE id = ?",
            (user['id'],)
        ).fetchone()
        is_exempt = urow and (
            (urow['role'] or '') in ('moderator', 'admin')
            or (urow['submissions_unlimited'] or 0) == 1
        )
        if not is_exempt:
            # Per-user soft rate-limit: max 5 pending in last 24h
            recent = conn.execute(
                "SELECT COUNT(*) FROM submissions WHERE user_id = ? AND submitted_at > ?",
                (user['id'], (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace('+00:00', 'Z'))
            ).fetchone()[0]
            if recent >= 5:
                raise HTTPException(429, "submission_rate_limit · max 5 per day")

        conn.execute(
            "INSERT INTO submissions (user_id, type, status, title, description, cluster, target_category_id, examples_json, submitted_at) "
            "VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?)",
            (user['id'], body.type, body.title.strip(), body.description, body.cluster, body.target_category_id, examples_json, now_iso())
        )
        sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        row = conn.execute("SELECT * FROM submissions WHERE id = ?", (sid,)).fetchone()
    sub_dict = submission_to_dict(row)
    publish_admin_event_sync('submission_new', sub_dict)
    return {"submission": sub_dict}


@app.get("/api/submissions/mine")
def my_submissions(user: dict = Depends(require_user), limit: int = 50):
    if limit > 100: limit = 100
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM submissions WHERE user_id = ? ORDER BY submitted_at DESC LIMIT ?",
            (user['id'], limit)
        ).fetchall()
    return {"submissions": [submission_to_dict(r) for r in rows]}


# ─── CELEBRATIONS (approval popup notifications) ───────────────

@app.get("/api/me/celebrations")
def my_celebrations(user: dict = Depends(require_user)):
    """Returns approved submissions the user hasn't yet acknowledged.
    Used by the frontend to show a single congrats popup batched across
    multiple approvals. last_approval_seen_at is per-user and per-account
    (works cross-device since the cookie session is server-tracked).
    """
    with db() as conn:
        u_row = conn.execute(
            "SELECT last_approval_seen_at FROM users WHERE id = ?", (user['id'],)
        ).fetchone()
        last_seen = u_row['last_approval_seen_at'] if u_row else None
        # All approved submissions decided after last_seen (or all if never seen)
        if last_seen:
            rows = conn.execute(
                """SELECT id, type, title, decided_at, target_category_id
                   FROM submissions
                   WHERE user_id = ? AND status = 'approved' AND decided_at > ?
                   ORDER BY decided_at DESC""",
                (user['id'], last_seen)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, type, title, decided_at, target_category_id
                   FROM submissions
                   WHERE user_id = ? AND status = 'approved' AND decided_at IS NOT NULL
                   ORDER BY decided_at DESC""",
                (user['id'],)
            ).fetchall()
    return {
        "approvals": [dict(r) for r in rows],
        "count": len(rows),
        "last_seen_at": last_seen,
    }


class ChallengeIn(BaseModel):
    """Payload of a challenge link — challenger's category + top-3 + identity.
    Same shape as the long #c= hash, just stored on server for short slug URLs.

    SECURITY: every string field is validated to reject HTML/script-injection
    payloads. The challenge payload is later inlined into the SSR /c/{slug}
    page as JSON inside a <script> block; without these validators a malicious
    nickname like `</script><script>alert(1)</script>` would break out and
    execute on our origin (audit finding C1, fixed defence-in-depth: both
    here at input time AND in the SSR escape helper).
    """
    c: str = Field(..., min_length=1, max_length=64)              # category id
    by: str = Field(..., min_length=1, max_length=24)             # challenger nickname
    g: Optional[str] = Field(default=None, max_length=8)          # avatar glyph
    t1: str = Field(..., min_length=1, max_length=200)            # top1 id
    n1: Optional[str] = Field(default=None, max_length=200)
    t2: Optional[str] = Field(default=None, max_length=200)
    n2: Optional[str] = Field(default=None, max_length=200)
    t3: Optional[str] = Field(default=None, max_length=200)
    n3: Optional[str] = Field(default=None, max_length=200)
    ts: Optional[int] = None

    @field_validator("c", "by", "g", "t1", "n1", "t2", "n2", "t3", "n3")
    @classmethod
    def _no_html(cls, v):
        if v is None:
            return v
        # Reject HTML/script-injection vectors. Catches `<`, `>` (tag delims),
        # ASCII control chars (0x00-0x1F minus \t \n \r), and U+2028/U+2029
        # (JS-string line terminators that would break out of an inline
        # JSON-in-<script> context). Doesn't reject `&` or `"` — those
        # appear legitimately in nicknames/category names; the SSR escape
        # helper handles them.
        if "<" in v or ">" in v:
            raise ValueError("html_not_allowed")
        for ch in v:
            o = ord(ch)
            # ASCII control chars (except common whitespace) — invalid.
            if o < 0x20 and ch not in "\t\n\r":
                raise ValueError("control_chars")
            # JS line terminators U+2028 / U+2029 would break out of an
            # inline JSON-in-<script> string literal — reject those too.
            if o == 0x2028 or o == 0x2029:
                raise ValueError("invalid_line_sep")
        return v


def _safe_inline_json(obj) -> str:
    """JSON-encode `obj` for safe inlining inside an HTML <script> block.

    Python's json.dumps does NOT escape characters that have meaning to the
    HTML parser, so a string like `</script><script>alert(1)</script>`
    survives intact and breaks out of the script context. Audit finding C1.

    We escape:
      - `<` → \\u003c, `>` → \\u003e, `&` → \\u0026 (HTML-parser breakouts)
      - U+2028, U+2029 → \\u2028, \\u2029 (JS line terminators that would
        break out of a multi-line string literal — though our ChallengeIn
        validator already rejects these on input, defence-in-depth.)
    """
    s = json.dumps(obj, ensure_ascii=False)
    return (s.replace("<", "\\u003c")
             .replace(">", "\\u003e")
             .replace("&", "\\u0026")
             .replace(" ", "\\u2028")
             .replace(" ", "\\u2029"))


@app.post("/api/challenges", status_code=201)
def create_challenge(body: ChallengeIn, request: Request,
                     upg_session: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    """Stores a challenge payload, returns a short slug.
    Auth optional — guests can also create short links (by_user_id stays NULL).

    Audit H2: rate-limited to 30 challenges per IP per 10 min so a bot can't
    flood the table with garbage payloads. Each insert opportunistically
    sweeps challenges older than CHALLENGE_RETENTION_DAYS so the table
    self-bounds without needing a cron job (1% of inserts trigger sweep).
    """
    rate_limit(request, "challenges_create", max_attempts=30, window_sec=600)

    # Optional user attribution
    by_user_id = None
    session_nick = None
    if upg_session:
        u = get_session_user(upg_session)
        if u:
            by_user_id = u['id']
            session_nick = u.get('nickname')

    # Audit-6 H3: server-authoritative challenge payload. Previously the
    # client could set `by` to any nickname (impersonate any user) and
    # `n1/n2/n3` to any string (claim a top-3 of items that don't exist).
    # Now we:
    #   1. Validate category + top item IDs exist in categories.json
    #   2. Server-resolve n1/n2/n3 from canonical item names (ignore client)
    #   3. For logged-in users, set `by` from session (ignore client)
    #   4. For guests, prefix `by` with "guest:" AND reject if it collides
    #      with a registered nickname (no impersonation surface)
    cats = _load_categories()
    cat = next((c for c in cats if c.get("id") == body.c), None)
    if not cat:
        raise HTTPException(422, "unknown_category")
    items_by_id = {it.get("id"): it for it in (cat.get("items") or [])}
    if body.t1 not in items_by_id:
        raise HTTPException(422, "unknown_t1_id")
    if body.t2 and body.t2 not in items_by_id:
        raise HTTPException(422, "unknown_t2_id")
    if body.t3 and body.t3 not in items_by_id:
        raise HTTPException(422, "unknown_t3_id")
    # Audit-7 P3: t3 without t2 is logically broken (3rd place but no 2nd).
    # Either both bottom places are present or neither. Reject the orphan.
    if body.t3 and not body.t2:
        raise HTTPException(422, "t3_without_t2")

    # Build server-authoritative payload — start from validated body, then
    # overwrite identity + names with server values.
    payload = body.model_dump()
    payload["n1"] = items_by_id[body.t1].get("name") or body.t1
    payload["n2"] = items_by_id[body.t2].get("name") if body.t2 else None
    payload["n3"] = items_by_id[body.t3].get("name") if body.t3 else None

    if session_nick:
        # Logged-in user: server-attested identity.
        payload["by"] = session_nick
    else:
        # Guest: reject if their typed nickname collides with a real user
        # (otherwise anyone could publish a "by: <real_username>" link).
        with db() as conn:
            collision = conn.execute(
                "SELECT 1 FROM users WHERE nickname = ? COLLATE NOCASE",
                (body.by,),
            ).fetchone()
        if collision:
            raise HTTPException(409, "guest_nickname_collides_registered")
        # Prefix "guest:" so recipients see this is an unauthenticated claim.
        payload["by"] = f"guest:{body.by}"

    payload_json = json.dumps(payload, ensure_ascii=False)

    # Generate unique slug. 5 bytes → ~7 char token; collision space ~10^12.
    # Retry a few times to be safe (basically impossible to hit twice).
    with db() as conn:
        for _attempt in range(5):
            slug = secrets.token_urlsafe(5).rstrip('-_')[:8] or secrets.token_urlsafe(6)
            try:
                conn.execute(
                    "INSERT INTO challenges (slug, payload_json, by_user_id, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (slug, payload_json, by_user_id, now_iso())
                )
                break
            except sqlite3.IntegrityError:
                continue
        else:
            raise HTTPException(500, "could_not_generate_slug")

        # Lazy cleanup: 1% of writes prune old rows. Acceptable bound on
        # table growth without scheduled cron. Keep authored challenges
        # forever (people may reshare old links); sweep only anonymous ones.
        if random.randint(1, 100) == 1:
            cutoff = (datetime.now(timezone.utc) -
                      timedelta(days=CHALLENGE_RETENTION_DAYS)).isoformat().replace("+00:00", "Z")
            try:
                conn.execute(
                    "DELETE FROM challenges WHERE by_user_id IS NULL AND created_at < ?",
                    (cutoff,)
                )
            except Exception as e:
                logger.warning("challenges lazy cleanup failed: %s", e)

    return {
        "slug": slug,
        "url": f"https://isverifiedby.me/?ch={slug}",
    }


@app.get("/api/challenges/{slug}")
def get_challenge(slug: str):
    """Returns the stored challenge payload by slug. Public — no auth needed
    (recipients of share links may not be logged in yet)."""
    if not re.match(r'^[a-zA-Z0-9_-]{4,16}$', slug):
        raise HTTPException(400, "invalid_slug")
    with db() as conn:
        row = conn.execute(
            "SELECT payload_json, by_user_id, created_at FROM challenges WHERE slug = ?",
            (slug,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "challenge_not_found")
    try:
        payload = json.loads(row['payload_json'])
    except Exception:
        raise HTTPException(500, "challenge_payload_invalid")
    return {"payload": payload, "created_at": row['created_at']}


# ─── DYNAMIC OG IMAGES + CHALLENGE LANDING ─────────────────────
# When someone shares a challenge URL like https://isverifiedby.me/c/{slug},
# Telegram/WhatsApp/Twitter preview bots fetch that URL. We serve game.html
# with og:* meta rewritten to point at /og/{slug}.png — a per-challenge
# image rendered from an SVG template by rsvg-convert, cached on disk.
# Humans landing on the same URL get the same HTML; their JS reads
# window._INITIAL_CHALLENGE (inlined below) and skips a second API roundtrip.

GAME_HTML_PATH = Path(os.environ.get("UPG_GAME_HTML_PATH", "/opt/untitled-pick-game/game.html"))
OG_TEMPLATE_PATH = Path(os.environ.get("UPG_OG_TEMPLATE_PATH", "/opt/untitled-pick-game-api/templates/og_challenge.svg"))
OG_PORTRAIT_TEMPLATE_PATH = Path(os.environ.get("UPG_OG_PORTRAIT_TEMPLATE_PATH", "/opt/untitled-pick-game-api/templates/og_portrait.svg"))
OG_DEFAULT_PNG_PATH = Path(os.environ.get("UPG_OG_DEFAULT_PATH", "/opt/untitled-pick-game/og-default.png"))
OG_CACHE_DIR = Path(os.environ.get("UPG_OG_CACHE_DIR", "/opt/untitled-pick-game-api/data/og_cache"))
try:
    OG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception as _e:
    logger.warning("could not create OG cache dir %s: %s", OG_CACHE_DIR, _e)

# In-memory caches of file content keyed by mtime - re-read on file change.
_game_html_cache: dict = {"mtime": 0.0, "content": ""}
_og_template_cache: dict = {"mtime": 0.0, "content": ""}
_og_portrait_template_cache: dict = {"mtime": 0.0, "content": ""}


def _load_template_cached(path: Path, cache: dict) -> str:
    """Read text file, cache by mtime. Returns '' if file unreadable."""
    try:
        m = path.stat().st_mtime
    except OSError:
        return cache.get("content", "")
    if m != cache.get("mtime"):
        try:
            cache["content"] = path.read_text(encoding="utf-8")
            cache["mtime"] = m
        except Exception as e:
            logger.warning("could not read template %s: %s", path, e)
            return cache.get("content", "")
    return cache["content"]


def _truncate(text: str, max_chars: int) -> str:
    """Cut long strings with an ellipsis so they fit the SVG card."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _xml_escape(text: str) -> str:
    """SVG-safe escape: &, <, >, ', "."""
    if not text:
        return ""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


_categories_resolve_cache: dict = {"mtime": 0.0, "by_id": {}}
_categories_full_cache: dict = {"mtime": 0.0, "data": []}


def _load_categories() -> list:
    """Cached load of full categories.json. Re-reads on file mtime change.
    Used by admin endpoints (clusters / themes / results filters)."""
    if not CATEGORIES_JSON_PATH.exists():
        return []
    try:
        m = CATEGORIES_JSON_PATH.stat().st_mtime
    except OSError:
        return _categories_full_cache.get("data", [])
    if m != _categories_full_cache.get("mtime"):
        try:
            _categories_full_cache["data"] = json.loads(CATEGORIES_JSON_PATH.read_text(encoding="utf-8"))
            _categories_full_cache["mtime"] = m
        except Exception as e:
            logger.warning("categories full-load failed: %s", e)
    return _categories_full_cache.get("data", [])


def _resolve_category_name(cat_id: str) -> str:
    """Look up category display name by id from categories.json. Falls back
    to the id itself if not found. Result cached by mtime of the source file."""
    if not cat_id:
        return ""
    try:
        m = CATEGORIES_JSON_PATH.stat().st_mtime
    except OSError:
        return cat_id
    if m != _categories_resolve_cache.get("mtime"):
        try:
            cats = json.loads(CATEGORIES_JSON_PATH.read_text(encoding="utf-8"))
            _categories_resolve_cache["by_id"] = {c.get("id"): c.get("name", c.get("id")) for c in cats if isinstance(c, dict)}
            _categories_resolve_cache["mtime"] = m
        except Exception as e:
            logger.warning("category cache rebuild failed: %s", e)
            return cat_id
    return _categories_resolve_cache["by_id"].get(cat_id, cat_id)


_MONTH_NAMES_RU = ["", "ЯНВ", "ФЕВ", "МАР", "АПР", "МАЙ", "ИЮН",
                   "ИЮЛ", "АВГ", "СЕН", "ОКТ", "НОЯ", "ДЕК"]


def _render_og_svg(payload: dict) -> str:
    """Substitute placeholders in the challenge OG SVG template.
    All values XML-escaped and length-truncated.

    Top-1/2/3 are intentionally NOT exposed here: the welcome screen hides
    the sender's picks behind '? · откроется после прохождения' so the
    receiver can't peek before playing. The OG preview that messengers
    auto-fetch must honor the same promise — otherwise WhatsApp/Telegram
    leak the picks in the link thumbnail. Layout shows category + sender
    + "? · ? · ?" placeholder instead.

    Masthead is brand-only (no issue number, no date). The magazine "ВЫПУСК
    № X · MMM YYYY" framing was vestigial — a challenge link is real-time,
    issue/date carry no information."""
    template = _load_template_cached(OG_TEMPLATE_PATH, _og_template_cache)
    if not template:
        return ""
    cat = _truncate(_resolve_category_name(payload.get("c", "")), 38)
    nickname = _truncate(payload.get("by", "?"), 22)
    return (template
            .replace("{{CATEGORY}}", _xml_escape(cat))
            .replace("{{NICKNAME}}", _xml_escape(nickname)))


def _render_og_png(slug: str, payload: dict) -> Optional[bytes]:
    """Render PNG for slug via rsvg-convert, cache on disk. Returns PNG bytes
    or None if rendering fails (caller should fall back to default OG)."""
    cache_path = OG_CACHE_DIR / f"{slug}.png"
    if cache_path.exists() and cache_path.stat().st_size > 0:
        try:
            return cache_path.read_bytes()
        except Exception:
            pass  # fallthrough to re-render
    svg = _render_og_svg(payload)
    if not svg:
        return None
    # Audit re-review M-2 (and follow-up): render to a tmp path FIRST, then
    # atomically promote. Tmp filename uses secrets.token_hex so two
    # concurrent renders of the same slug in the same process don't collide
    # on a shared `{slug}.png.tmp.{pid}` filename (the previous attempt at
    # this fix). Each request gets its own tmp; whichever finishes last
    # promotes its bytes to cache_path (acceptable — both are valid PNGs).
    from pathlib import Path as _Path
    tmp_path = _Path(str(cache_path) + f".tmp.{secrets.token_hex(8)}")
    try:
        result = subprocess.run(
            ["rsvg-convert", "-w", "1200", "-h", "630", "-o", str(tmp_path)],
            input=svg.encode("utf-8"),
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            logger.warning("rsvg-convert failed for %s: %s", slug,
                           result.stderr.decode("utf-8", errors="ignore"))
            try: tmp_path.unlink()
            except Exception: pass
            return None
        # Atomic promote — only now does the cache path exist with valid bytes.
        os.replace(str(tmp_path), str(cache_path))
        return cache_path.read_bytes()
    except subprocess.TimeoutExpired:
        logger.warning("rsvg-convert timeout for %s", slug)
        try: tmp_path.unlink()
        except Exception: pass
        return None
    except Exception as e:
        logger.warning("rsvg-convert exception for %s: %s", slug, e)
        try: tmp_path.unlink()
        except Exception: pass
        return None


@app.get("/og/{slug}.png")
def og_image(slug: str, request: Request):
    """Per-challenge OG image, rendered from a server-side SVG template.

    Cache strategy: the slug content (challenge payload) IS immutable, BUT the
    rendered output depends on the SVG template, which can change when we
    fix bugs (e.g. a privacy leak in the layout) or rebrand. Previously this
    used `max-age=31536000, immutable` on the assumption "same URL = same
    bytes forever" — but a template change broke that contract and CF held
    a 1-year-old stale image for every existing slug.

    New strategy: short max-age + long stale-while-revalidate. CF refreshes
    from origin every hour, but serves the cached copy meanwhile (no user
    sees a slow render). Worst case after a template change: 1 hour of CF
    staleness for downstream consumers (TG/WhatsApp bots have their own
    cache layered on top — separate concern, handled out-of-band).

    Audit H3: rate-limit applies ONLY to first-time renders (cache miss).
    Cached PNGs are served at memory speed and cost us nothing, so crawlers
    hammering existing slugs aren't throttled. Cache misses fork rsvg-convert
    (10s timeout, real CPU) — that's the path we protect.
    """
    if not re.match(r'^[a-zA-Z0-9_-]{4,16}$', slug):
        raise HTTPException(400, "invalid_slug")

    cache_headers = {"Cache-Control": "public, max-age=3600, stale-while-revalidate=86400"}

    # Fast path: cache hit. No rate-limit, no DB lookup.
    cache_path = OG_CACHE_DIR / f"{slug}.png"
    if cache_path.exists() and cache_path.stat().st_size > 0:
        try:
            return Response(content=cache_path.read_bytes(), media_type="image/png",
                            headers=cache_headers)
        except Exception:
            pass  # fallthrough to re-render

    # Slow path (cache miss). Throttle: 60 unique-slug renders per IP per 10
    # min. Legitimate previewbots rarely hit a slug they don't have cached.
    rate_limit(request, "og_render", max_attempts=60, window_sec=600)

    with db() as conn:
        row = conn.execute(
            "SELECT payload_json FROM challenges WHERE slug = ?", (slug,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "challenge_not_found")
    try:
        payload = json.loads(row["payload_json"])
    except Exception:
        raise HTTPException(500, "invalid_payload")
    png = _render_og_png(slug, payload)
    if png is None:
        # Render failed — serve the static default so previews still work
        try:
            default = OG_DEFAULT_PNG_PATH.read_bytes()
            return Response(content=default, media_type="image/png",
                            headers={"Cache-Control": "public, max-age=300"})
        except Exception:
            raise HTTPException(500, "og_render_failed")
    return Response(content=png, media_type="image/png",
                    headers=cache_headers)


# ─── PORTRAIT OG IMAGE ────────────────────────────────────────────────
# Per-portrait OG card, rendered at first request and cached forever
# (portrait slugs are immutable; new portraits get new slugs). Cache file
# name pattern is `portrait_{slug}.png` to avoid collision with challenge
# cache (slugs come from different generators with overlapping alphabets).

def _wrap_headline_for_og(headline: str, max_chars_per_line: int = 30) -> tuple[list[str], int]:
    """Wrap the portrait headline into up to 3 lines. Returns (lines, font_size).
    Font size adapts to total length so longer headlines stay inside the canvas:
      ≤32 chars: 56px, fits one line easily
      ≤60 chars: 48px, fits two lines
      ≤90 chars: 42px, fits three lines
      else:       36px, three lines + truncation
    Always returns exactly 3 strings (empty strings padded) so the SVG tspan
    template doesn't break when fewer lines are needed."""
    words = headline.split()
    lines: list[list[str]] = [[]]
    cur_len = 0
    for w in words:
        # Soft wrap at max_chars; allow overshoot if word itself is long
        if cur_len + len(w) + (1 if cur_len else 0) > max_chars_per_line and lines[-1]:
            lines.append([w])
            cur_len = len(w)
        else:
            lines[-1].append(w)
            cur_len += len(w) + (1 if cur_len else 0)
    str_lines = [" ".join(parts) for parts in lines if parts]
    # Cap at 3 lines (truncate last with ellipsis if more)
    if len(str_lines) > 3:
        str_lines = str_lines[:2] + [" ".join(str_lines[2:])[:max_chars_per_line - 1] + "…"]
    total_len = len(headline)
    if total_len <= 32:
        font_size = 56
    elif total_len <= 60:
        font_size = 48
    elif total_len <= 90:
        font_size = 42
    else:
        font_size = 36
    # Pad to exactly 3 strings so SVG template substitution works cleanly
    while len(str_lines) < 3:
        str_lines.append("")
    return str_lines, font_size


def _render_portrait_og_svg(nickname: str, headline: str) -> str:
    """Substitute placeholders in the portrait OG SVG template."""
    template = _load_template_cached(OG_PORTRAIT_TEMPLATE_PATH, _og_portrait_template_cache)
    if not template:
        return ""
    nick = _truncate(nickname or "?", 22)
    head_clean = (headline or "Прочтение").strip()
    lines, font_size = _wrap_headline_for_og(head_clean)
    return (template
            .replace("{{NICKNAME}}", _xml_escape(nick))
            .replace("{{HEADLINE_L1}}", _xml_escape(lines[0]))
            .replace("{{HEADLINE_L2}}", _xml_escape(lines[1]))
            .replace("{{HEADLINE_L3}}", _xml_escape(lines[2]))
            .replace("{{HEADLINE_FONT_SIZE}}", str(font_size)))


def _render_portrait_og_png(slug: str, nickname: str, headline: str) -> Optional[bytes]:
    """Same rsvg-convert pipeline as challenge OG, separate cache file."""
    cache_path = OG_CACHE_DIR / f"portrait_{slug}.png"
    if cache_path.exists() and cache_path.stat().st_size > 0:
        try:
            return cache_path.read_bytes()
        except Exception:
            pass
    svg = _render_portrait_og_svg(nickname, headline)
    if not svg:
        return None
    from pathlib import Path as _Path
    tmp_path = _Path(str(cache_path) + f".tmp.{secrets.token_hex(8)}")
    try:
        result = subprocess.run(
            ["rsvg-convert", "-w", "1200", "-h", "630", "-o", str(tmp_path)],
            input=svg.encode("utf-8"),
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0:
            logger.warning("portrait rsvg-convert failed for %s: %s", slug,
                           result.stderr.decode("utf-8", errors="ignore"))
            try: tmp_path.unlink()
            except Exception: pass
            return None
        os.replace(str(tmp_path), str(cache_path))
        return cache_path.read_bytes()
    except subprocess.TimeoutExpired:
        logger.warning("portrait rsvg-convert timeout for %s", slug)
        try: tmp_path.unlink()
        except Exception: pass
        return None
    except Exception as e:
        logger.warning("portrait rsvg-convert exception for %s: %s", slug, e)
        try: tmp_path.unlink()
        except Exception: pass
        return None


@app.get("/og/portrait/{slug}.png")
def og_portrait_image(slug: str, request: Request):
    """Per-portrait OG image (1200x630). Served to Telegram/WhatsApp/Twitter
    when they crawl the /p/portrait/{slug} share URL. Cached forever — slugs
    are immutable per portrait."""
    if not re.fullmatch(r"[a-z0-9]{6,16}", slug):
        raise HTTPException(400, "invalid_slug")

    # Fast path: cache hit
    cache_path = OG_CACHE_DIR / f"portrait_{slug}.png"
    if cache_path.exists() and cache_path.stat().st_size > 0:
        try:
            return Response(content=cache_path.read_bytes(), media_type="image/png",
                            headers={"Cache-Control": "public, max-age=31536000, immutable"})
        except Exception:
            pass

    # Slow path
    rate_limit(request, "og_portrait_render", max_attempts=60, window_sec=600)
    with db() as conn:
        row = portrait_mod.get_portrait_by_slug(conn, slug)
        if not row or not row.get("is_public"):
            raise HTTPException(404, "not_found")
        try:
            participants = json.loads(row["participant_ids"])
            author_uid = participants[0] if participants else None
        except (json.JSONDecodeError, TypeError, IndexError):
            author_uid = None
        nickname = "?"
        if author_uid:
            urow = conn.execute(
                "SELECT nickname FROM users WHERE id = ?", (author_uid,)
            ).fetchone()
            if urow and urow["nickname"]:
                nickname = urow["nickname"]
        # Extract headline (first "# " line of content_md)
        md = row.get("content_md") or ""
        headline = "Прочтение"
        for line in md.split("\n"):
            s = line.strip()
            if s.startswith("# "):
                headline = s[2:].strip()
                break

    png = _render_portrait_og_png(slug, nickname, headline)
    if png is None:
        # Render failed — serve generic placeholder rather than break previews
        try:
            return Response(content=OG_DEFAULT_PNG_PATH.read_bytes(), media_type="image/png",
                            headers={"Cache-Control": "no-cache"})
        except Exception:
            raise HTTPException(500, "render_failed")
    return Response(content=png, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=31536000, immutable"})


def _set_meta(html_str: str, attr: str, name: str, new_content: str) -> str:
    """Replace content="..." of a single <meta {attr}="{name}" content="..."> tag.
    Tolerates extra whitespace between attributes. No-op if the tag is missing."""
    pat = re.compile(
        r'(<meta\s+' + attr + r'\s*=\s*"' + re.escape(name) + r'"\s+content\s*=\s*)"[^"]*"',
        re.IGNORECASE,
    )
    repl = '"' + html_module.escape(new_content, quote=True) + '"'
    return pat.sub(lambda m: m.group(1) + repl, html_str)


@app.get("/c/{slug}")
def challenge_landing(slug: str):
    """Server-rendered challenge landing — game.html with og:* meta personalized
    for THIS challenge, plus the challenge payload inlined as window._INITIAL_CHALLENGE
    so the client doesn't need a second API roundtrip."""
    if not re.match(r'^[a-zA-Z0-9_-]{4,16}$', slug):
        raise HTTPException(400, "invalid_slug")

    with db() as conn:
        row = conn.execute(
            "SELECT payload_json FROM challenges WHERE slug = ?", (slug,)
        ).fetchone()

    html_text = _load_template_cached(GAME_HTML_PATH, _game_html_cache)
    if not html_text:
        raise HTTPException(500, "game_html_unavailable")

    if not row:
        # Bad/expired slug — serve game.html unmodified so user lands on home
        return HTMLResponse(content=html_text,
                            headers={"Cache-Control": "no-cache"})

    try:
        payload = json.loads(row["payload_json"])
    except Exception:
        raise HTTPException(500, "invalid_payload")

    cat_name = _resolve_category_name(payload.get("c", ""))
    nickname = payload.get("by", "?")

    # NOTE: top1/top2/top3 are in the payload but NEVER surfaced in OG meta.
    # They leak the sender's picks before the receiver plays, which contradicts
    # the welcome-screen promise that picks are revealed after playing.
    # Both og:image and og:description must be receiver-safe.
    title = f"Вызов от @{nickname} · «{cat_name}» - Tappetite"
    description = f"@{nickname} зовёт сыграть турнир «{cat_name}» и сравнить вкус. Свои топ-3 ты увидишь после прохождения."
    image_url = f"https://isverifiedby.me/og/{slug}.png"
    page_url = f"https://isverifiedby.me/c/{slug}"
    image_alt = f"Вызов от @{nickname}: турнир «{cat_name}»"

    html_text = _set_meta(html_text, 'property', 'og:title', title)
    html_text = _set_meta(html_text, 'property', 'og:description', description)
    html_text = _set_meta(html_text, 'property', 'og:url', page_url)
    html_text = _set_meta(html_text, 'property', 'og:image', image_url)
    html_text = _set_meta(html_text, 'property', 'og:image:alt', image_alt)
    html_text = _set_meta(html_text, 'name', 'twitter:title', title)
    html_text = _set_meta(html_text, 'name', 'twitter:description', description)
    html_text = _set_meta(html_text, 'name', 'twitter:image', image_url)

    # Inline payload so client skips /api/challenges/{slug} fetch on landing.
    # CRITICAL: must use _safe_inline_json — plain json.dumps does NOT escape
    # `</script>` or U+2028/U+2029, which would let a maliciously-crafted
    # nickname or category name escape the script context (XSS, audit C1).
    # Belt-and-braces: ChallengeIn has a field_validator that rejects `<`/`>`
    # on input, but this escape is the second layer in case input ever sneaks
    # past validation.
    inline_payload = _safe_inline_json({"slug": slug, "payload": payload})
    inject = f'<script>window._INITIAL_CHALLENGE = {inline_payload};</script>\n</head>'
    html_text = html_text.replace('</head>', inject, 1)

    return HTMLResponse(content=html_text,
                        headers={"Cache-Control": "public, max-age=300"})


@app.get("/api/referrals/me")
def my_referrals(user: dict = Depends(require_user)):
    """How many users registered via this user's challenge/share link."""
    with db() as conn:
        rows = conn.execute(
            "SELECT id, nickname, created_at FROM users WHERE referred_by = ? ORDER BY created_at DESC",
            (user['id'],)
        ).fetchall()
    return {
        "count": len(rows),
        "referrals": [{"id": r["id"], "nickname": r["nickname"], "joined_at": r["created_at"]} for r in rows],
    }


@app.post("/api/me/celebrations/seen")
def mark_celebrations_seen(user: dict = Depends(require_user)):
    """Marks all current approvals as seen — sets last_approval_seen_at = now()."""
    with db() as conn:
        conn.execute(
            "UPDATE users SET last_approval_seen_at = ? WHERE id = ?",
            (now_iso(), user['id'])
        )
    return {"ok": True}


# ─── ACHIEVEMENTS ──────────────────────────────────────────────
# Catalog defined in code (versioned, easy to extend). User unlocks stored
# in user_achievements. Auto-checked after relevant actions (result save,
# friend add, submission approval).

ACHIEVEMENTS = [
    # ─── Tournaments played (journal/editorial voice — выпуски, номера, архив)
    {"id": "first_tournament", "icon": "✦", "name": "Дебютный выпуск",
     "description": "Прошёл свой первый турнир.",
     "name_en": "Debut issue", "description_en": "You finished your first tournament.",
     "criteria": ("results_count", 1)},
    {"id": "ten_tournaments", "icon": "📰", "name": "Десять номеров",
     "description": "Прошёл десять турниров.",
     "name_en": "Ten issues", "description_en": "You finished ten tournaments.",
     "criteria": ("results_count", 10)},
    {"id": "fifty_tournaments", "icon": "📚", "name": "Постоянный читатель",
     "description": "Прошёл пятьдесят турниров.",
     "name_en": "Regular reader", "description_en": "You finished fifty tournaments.",
     "criteria": ("results_count", 50)},
    {"id": "hundred_tournaments", "icon": "🏛", "name": "Хроникёр",
     "description": "Прошёл сто турниров — цифра уже не просто статистика.",
     "name_en": "Chronicler", "description_en": "You finished one hundred tournaments — at this point, the number is more than a statistic.",
     "criteria": ("results_count", 100)},

    # ─── Coverage
    {"id": "explorer", "icon": "🗺", "name": "Знаток рубрик",
     "description": "Прошёл хотя бы по одной теме в пяти разных кластерах.",
     "name_en": "Section connoisseur", "description_en": "You played at least one theme in five different categories.",
     "criteria": ("clusters_played", 5)},
    {"id": "completionist", "icon": "👑", "name": "Закрыл архив",
     "description": "Прошёл все доступные темы журнала.",
     "name_en": "Closed the archive", "description_en": "You finished every theme in the journal.",
     "criteria": ("coverage_percent", 100)},

    # ─── Submissions / community
    {"id": "first_submission", "icon": "✉️", "name": "Первое слово в редакцию",
     "description": "Отправил своё первое предложение в журнал.",
     "name_en": "First letter to the editor", "description_en": "You sent your first suggestion to the journal.",
     "criteria": ("submissions_count", 1)},
    {"id": "first_approval", "icon": "✨", "name": "Опубликован",
     "description": "Одно из твоих предложений приняли в выпуск.",
     "name_en": "Published", "description_en": "One of your suggestions made it into print.",
     "criteria": ("approved_count", 1)},
    {"id": "five_approvals", "icon": "🖋", "name": "Постоянный автор",
     "description": "Пять твоих предложений вышли в выпуске.",
     "name_en": "Regular contributor", "description_en": "Five of your suggestions appeared in the journal.",
     "criteria": ("approved_count", 5)},

    # ─── Social
    {"id": "first_friend", "icon": "🤝", "name": "Первая подписка",
     "description": "Связан хотя бы с одним игроком взаимной дружбой.",
     "name_en": "First connection", "description_en": "You and at least one player are mutual friends.",
     "criteria": ("friends_count", 1)},
    {"id": "five_friends", "icon": "✿", "name": "Свой круг",
     "description": "Пять и больше игроков в твоём списке друзей.",
     "name_en": "Your circle", "description_en": "Five or more players are in your circle.",
     "criteria": ("friends_count", 5)},

    # ─── Taste profile (uniqueness-based)
    {"id": "rare_taste", "icon": "🦄", "name": "Редкий вкус",
     "description": "Уникальность твоих выборов 75% и выше.",
     "name_en": "Rare taste", "description_en": "Your picks are at least 75% unique.",
     "criteria": ("uniqueness_min", 75)},
    {"id": "culture_heart", "icon": "❤️", "name": "В сердце культуры",
     "description": "Уникальность 19% или ниже — твои выборы совпадают с миллионами.",
     "name_en": "At the heart of culture", "description_en": "Uniqueness is 19% or lower — your picks echo the crowd.",
     "criteria": ("uniqueness_max", 19)},

    # ─── Referrals (journal-vocab: подписчик / тираж)
    {"id": "first_referral", "icon": "📨", "name": "Первый подписчик",
     "description": "Первый игрок пришёл по твоей рекомендации.",
     "name_en": "First subscriber", "description_en": "Your first player joined through your invite.",
     "criteria": ("referrals_count", 1)},
    {"id": "five_referrals", "icon": "🗞", "name": "Малый тираж",
     "description": "Пятеро пришли по твоим рекомендациям.",
     "name_en": "Small print run", "description_en": "Five people joined through your invites.",
     "criteria": ("referrals_count", 5)},
    {"id": "ten_referrals", "icon": "📰", "name": "Полный тираж",
     "description": "Десять и больше игроков пришли по твоим рекомендациям.",
     "name_en": "Full print run", "description_en": "Ten or more players joined through your invites.",
     "criteria": ("referrals_count", 10)},

    # ─── Behavior
    {"id": "speedrunner", "icon": "⚡", "name": "Молниеносный выбор",
     "description": "Завершил турнир со средней скоростью меньше двух секунд на бой.",
     "name_en": "Lightning choice", "description_en": "You finished a tournament with an average pace under two seconds per fight.",
     "criteria": ("avg_battle_speed_max", 2)},
    {"id": "contemplative", "icon": "🌙", "name": "Долгий взгляд",
     "description": "Завершил турнир со средней скоростью больше пятнадцати секунд на бой.",
     "name_en": "Long look", "description_en": "You finished a tournament with an average pace over fifteen seconds per fight.",
     "criteria": ("avg_battle_speed_min", 15)},

    # ─── Visit streaks (open the app on N consecutive days)
    # Tracking starts the day the user first authenticates after the
    # 2026-05-11 deploy — existing users don't get retroactive credit.
    {"id": "visit_streak_3", "icon": "🔥", "name": "Три дня подряд",
     "description": "Открывал приложение три дня подряд.",
     "name_en": "Three-day streak", "description_en": "You opened the app three days in a row.",
     "criteria": ("visit_streak", 3)},
    {"id": "visit_streak_7", "icon": "📅", "name": "Неделя на связи",
     "description": "Семь дней подряд — целая неделя в журнале.",
     "name_en": "Week-long streak", "description_en": "Seven days in a row — a full week with the journal.",
     "criteria": ("visit_streak", 7)},
    {"id": "visit_streak_30", "icon": "🗓", "name": "Месяц",
     "description": "Тридцать дней подряд. Это уже привычка.",
     "name_en": "A whole month", "description_en": "Thirty days in a row. That's a habit now.",
     "criteria": ("visit_streak", 30)},
    {"id": "visit_streak_100", "icon": "💎", "name": "Сотня дней",
     "description": "Сто дней подряд. Без комментариев.",
     "name_en": "One hundred days", "description_en": "One hundred days in a row. No comment.",
     "criteria": ("visit_streak", 100)},

    # ─── Play streaks (complete at least one tournament daily for N days)
    {"id": "play_streak_7", "icon": "🌟", "name": "Неделя выпусков",
     "description": "Каждый день недели прошёл хотя бы один турнир.",
     "name_en": "A week of issues", "description_en": "You played at least one tournament every day for a week.",
     "criteria": ("play_streak", 7)},
    {"id": "play_streak_30", "icon": "🏆", "name": "Месяц выпусков",
     "description": "Месяц подряд — каждый день минимум один турнир.",
     "name_en": "A month of issues", "description_en": "A full month — at least one tournament every single day.",
     "criteria": ("play_streak", 30)},

    # ─── Cumulative visits (not necessarily consecutive)
    {"id": "visits_30", "icon": "📖", "name": "Тридцать заходов",
     "description": "Открывал приложение в тридцати разных днях.",
     "name_en": "Thirty visits", "description_en": "You opened the app on thirty different days.",
     "criteria": ("total_visit_days", 30)},
    {"id": "visits_100", "icon": "📚", "name": "Сотня заходов",
     "description": "Сто различных дней с приложением.",
     "name_en": "Hundred visits", "description_en": "A hundred different days with the app.",
     "criteria": ("total_visit_days", 100)},

    # ─── Voter (you liked someone else's turnir N times)
    {"id": "voter_first", "icon": "👍", "name": "Первый лайк",
     "description": "Поставил первый лайк турниру.",
     "name_en": "First like given", "description_en": "You liked your first tournament.",
     "criteria": ("voter_likes_given", 1)},
    {"id": "voter_10", "icon": "💝", "name": "Десять лайков",
     "description": "Лайкнул десять турниров.",
     "name_en": "Ten likes given", "description_en": "You liked ten tournaments.",
     "criteria": ("voter_likes_given", 10)},
    {"id": "voter_100", "icon": "💞", "name": "Сотня лайков",
     "description": "Сто турниров с твоим одобрением.",
     "name_en": "Hundred likes given", "description_en": "A hundred tournaments with your approval.",
     "criteria": ("voter_likes_given", 100)},

    # ─── Creator (one of your turnirs got N likes)
    {"id": "creator_liked_first", "icon": "🌱", "name": "Первый лайк твоему турниру",
     "description": "Кто-то поставил лайк турниру, который ты предложил.",
     "name_en": "Your turnir got its first like", "description_en": "Someone liked a tournament you suggested.",
     "criteria": ("received_likes_max", 1)},
    {"id": "creator_liked_10", "icon": "🌿", "name": "Десять лайков твоему турниру",
     "description": "Один из твоих турниров собрал десять лайков.",
     "name_en": "Ten likes on your turnir", "description_en": "One of your tournaments has ten likes.",
     "criteria": ("received_likes_max", 10)},
    {"id": "creator_liked_100", "icon": "🌳", "name": "Сотня лайков твоему турниру",
     "description": "Один из твоих турниров собрал сто лайков. Хит.",
     "name_en": "Hundred likes on your turnir", "description_en": "One of your tournaments hit a hundred likes. A hit.",
     "criteria": ("received_likes_max", 100)},
]

ACHIEVEMENTS_BY_ID = {a["id"]: a for a in ACHIEVEMENTS}


def _compute_user_metrics(conn: sqlite3.Connection, user_id: int) -> dict:
    """Computes once-per-check user metrics needed by achievement criteria."""
    m = {}
    m["results_count"] = conn.execute(
        "SELECT COUNT(*) FROM results WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    m["submissions_count"] = conn.execute(
        "SELECT COUNT(*) FROM submissions WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    m["approved_count"] = conn.execute(
        "SELECT COUNT(*) FROM submissions WHERE user_id = ? AND status = 'approved'",
        (user_id,)
    ).fetchone()[0]
    m["friends_count"] = conn.execute(
        "SELECT COUNT(*) FROM friendships WHERE user_id = ? AND status = 'accepted'",
        (user_id,)
    ).fetchone()[0]
    m["referrals_count"] = conn.execute(
        "SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,)
    ).fetchone()[0]
    # Clusters played: distinct clusters across user's results.
    # Audit M6: use the cached _load_categories() instead of re-reading
    # categories.json from disk on every metric computation (this function
    # runs on every result-save AND every achievement check).
    played_cat_ids = [r[0] for r in conn.execute(
        "SELECT DISTINCT category_id FROM results WHERE user_id = ?", (user_id,)
    ).fetchall()]
    cats_data = _load_categories() if played_cat_ids else []
    if cats_data:
        try:
            cluster_set = set()
            played_set = set(played_cat_ids)
            for c in cats_data:
                if c.get("id") in played_set:
                    cl = c.get("cluster")
                    if cl: cluster_set.add(cl)
            m["clusters_played"] = len(cluster_set)
            # Coverage percent
            real_cats = [c for c in cats_data if not c.get("is_name_tournament")]
            played_real = [c for c in real_cats if c.get("id") in played_set]
            m["coverage_percent"] = round(100 * len(played_real) / max(1, len(real_cats)))
        except Exception:
            m["clusters_played"] = 0
            m["coverage_percent"] = 0
    else:
        m["clusters_played"] = 0
        m["coverage_percent"] = 0
    # Battle speed (best/worst across all results)
    speed_rows = conn.execute(
        "SELECT duration_sec, battles_played FROM results WHERE user_id = ? AND battles_played > 0",
        (user_id,)
    ).fetchall()
    if speed_rows:
        speeds = [r["duration_sec"] / r["battles_played"] for r in speed_rows if r["battles_played"]]
        m["avg_battle_speed_min"] = max(speeds) if speeds else 0  # 'min' means "at least this slow"
        m["avg_battle_speed_max"] = min(speeds) if speeds else 999  # 'max' means "no faster than this"
    else:
        m["avg_battle_speed_min"] = 0
        m["avg_battle_speed_max"] = 999
    # Streak metrics (2026-05-11). See compute_visit_streak / compute_play_streak
    # for date arithmetic in Asia/Almaty TZ.
    m["visit_streak"] = compute_visit_streak(conn, user_id)
    m["play_streak"] = compute_play_streak(conn, user_id)
    m["total_visit_days"] = compute_total_visit_days(conn, user_id)

    # Tournament vote metrics (2026-05-12). Two angles:
    #   - voter_likes_given: how many turnirs THIS user has liked
    #     (drives the "voted on 1/10/100" achievements)
    #   - received_likes_max: max likes on any turnir THIS user submitted
    #     (drives the "your turnir got 1/10/100 likes" achievements)
    voter_row = conn.execute(
        "SELECT COUNT(*) FROM tournament_votes WHERE user_id = ? AND vote = 1",
        (user_id,),
    ).fetchone()
    m["voter_likes_given"] = int(voter_row[0]) if voter_row else 0

    # received_likes_max: lookup user's nickname, find all categories.json
    # entries with submitted_by == that nick, count likes per category, take max.
    user_row = conn.execute(
        "SELECT nickname FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    received_max = 0
    if user_row and not isSystemAuthor_py(user_row["nickname"]):
        try:
            cats_full = _load_categories()
            my_nick = user_row["nickname"]
            my_cat_ids = [c.get("id") for c in cats_full
                          if (c.get("submitted_by") or "").strip().lower()
                              == my_nick.lower() and c.get("id")]
            if my_cat_ids:
                placeholders = ",".join("?" for _ in my_cat_ids)
                max_row = conn.execute(
                    f"SELECT category_id, COUNT(*) AS cnt FROM tournament_votes "
                    f"WHERE vote = 1 AND category_id IN ({placeholders}) "
                    f"GROUP BY category_id ORDER BY cnt DESC LIMIT 1",
                    my_cat_ids,
                ).fetchone()
                if max_row:
                    received_max = int(max_row["cnt"])
        except Exception as e:
            logger.warning("received_likes_max compute failed: %s", e)
    m["received_likes_max"] = received_max
    return m


def _check_criterion(criterion, metrics) -> bool:
    """Evaluates a single achievement criterion against user metrics."""
    key, threshold = criterion
    val = metrics.get(key)
    if val is None:
        return False
    if key in ("avg_battle_speed_max", "uniqueness_max", "coverage_below"):
        return val <= threshold
    # Default: greater-or-equal
    return val >= threshold


def check_and_unlock_achievements(user_id: int, extra_metrics: dict | None = None) -> list[str]:
    """Runs all criteria checks for user_id, unlocks any newly-met achievements.
    Returns list of newly-unlocked achievement IDs.
    `extra_metrics` lets callers pass values not derivable from DB alone (e.g. uniqueness_percent
    computed in /api/stats/me)."""
    newly = []
    with db() as conn:
        # Already-unlocked set
        existing = set(r["achievement_id"] for r in conn.execute(
            "SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,)
        ).fetchall())
        if len(existing) >= len(ACHIEVEMENTS):
            return []  # all unlocked already, nothing to do
        metrics = _compute_user_metrics(conn, user_id)
        if extra_metrics:
            metrics.update(extra_metrics)
        now = now_iso()
        for ach in ACHIEVEMENTS:
            if ach["id"] in existing:
                continue
            if _check_criterion(ach["criteria"], metrics):
                conn.execute(
                    "INSERT OR IGNORE INTO user_achievements (user_id, achievement_id, unlocked_at) VALUES (?, ?, ?)",
                    (user_id, ach["id"], now)
                )
                newly.append(ach["id"])
    # Phase C trigger #4 (2026-05-12): congrats push for streak / visit
    # milestones. Other achievement types (first_tournament, explorer, etc)
    # already fire visible toasts in-app — only milestone STREAKS warrant
    # waking the user up because the streak metaphor only works if the user
    # remembers it's running. We iterate `newly` (the just-unlocked IDs) so
    # we don't spam every push subscription on every metric recheck.
    streak_unlocks = [aid for aid in newly if aid.startswith("visit_streak_")
                      or aid.startswith("play_streak_")]
    if streak_unlocks:
        try:
            for aid in streak_unlocks:
                ach = ACHIEVEMENTS_BY_ID.get(aid)
                if not ach:
                    continue
                send_push_to_user(user_id, {
                    "title": f"{ach.get('icon', '🔥')} {ach.get('name', '')}",
                    "body": ach.get("description", ""),
                    "url": "/?screen=achievements",
                    "tag": f"streak_unlock:{aid}",
                })
        except Exception as e:
            logger.warning("streak-unlock push failed: %s", e)
    return newly


@app.get("/api/achievements/me")
def my_achievements(user: dict = Depends(require_user)):
    """Returns full achievement state for the user: which are unlocked,
    locked (still TODO), and their progress where measurable."""
    # Trigger an opportunistic check on every fetch (cheap; covers stale state
    # in case some hook missed an unlock). Costs a couple SQL counts.
    check_and_unlock_achievements(user['id'])
    with db() as conn:
        unlocked_rows = conn.execute(
            "SELECT achievement_id, unlocked_at FROM user_achievements WHERE user_id = ?",
            (user['id'],)
        ).fetchall()
        unlocked_map = {r['achievement_id']: r['unlocked_at'] for r in unlocked_rows}
        metrics = _compute_user_metrics(conn, user['id'])

    items = []
    for ach in ACHIEVEMENTS:
        is_unlocked = ach["id"] in unlocked_map
        criterion = ach["criteria"]
        cur_val = metrics.get(criterion[0]) if criterion else None
        threshold = criterion[1] if criterion else None
        items.append({
            "id": ach["id"],
            "icon": ach["icon"],
            "name": ach["name"],
            "name_en": ach.get("name_en"),
            "description": ach["description"],
            "description_en": ach.get("description_en"),
            "unlocked": is_unlocked,
            "unlocked_at": unlocked_map.get(ach["id"]),
            "current": cur_val,
            "threshold": threshold,
        })
    return {
        "achievements": items,
        "unlocked_count": len(unlocked_map),
        "total_count": len(ACHIEVEMENTS),
    }


@app.get("/api/submissions")
def list_submissions(_role: str = Depends(require_mod_or_admin), status: str | None = None, limit: int = 100):
    if limit > 500: limit = 500
    # Admin god-mode (2026-05-11): COALESCE prefers the attributed user's
    # nickname when set, else falls back to the original submitter's. The
    # JOIN against users-aliased-as-`a` is a LEFT JOIN because attribution
    # is optional (NULL = no override).
    base_select = (
        "SELECT s.*, "
        "       COALESCE(a.nickname, u.nickname) AS submitter_nickname, "
        "       u.nickname AS original_submitter_nickname, "
        "       a.nickname AS attributed_nickname "
        "FROM submissions s "
        "JOIN users u ON s.user_id = u.id "
        "LEFT JOIN users a ON s.attributed_user_id = a.id "
    )
    with db() as conn:
        if status:
            rows = conn.execute(
                base_select + "WHERE s.status = ? ORDER BY s.submitted_at DESC LIMIT ?",
                (status, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                base_select + "ORDER BY s.submitted_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
    return {"submissions": [submission_to_dict(r) for r in rows]}


# ─── FRIENDS ───────────────────────────────────────────────────

def _friend_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "friend_user_id": row["friend_user_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "responded_at": row["responded_at"],
        "friend_nickname": row["friend_nickname"] if "friend_nickname" in row.keys() else None,
        "friend_avatar_glyph": row["friend_avatar_glyph"] if "friend_avatar_glyph" in row.keys() else "✦",
    }


@app.post("/api/friends/add", status_code=201)
def add_friend(body: AddFriendIn, user: dict = Depends(require_user)):
    target_nick = body.nickname.strip()
    if target_nick.lower() == user["nickname"].lower():
        raise HTTPException(400, "cannot_add_self")

    with db() as conn:
        target = conn.execute(
            "SELECT id, nickname FROM users WHERE nickname = ? COLLATE NOCASE",
            (target_nick,),
        ).fetchone()
        if not target:
            raise HTTPException(404, "user_not_found")

        # Existing forward (we already sent them a request OR are already friends)
        existing = conn.execute(
            "SELECT * FROM friendships WHERE user_id = ? AND friend_user_id = ?",
            (user["id"], target["id"]),
        ).fetchone()
        if existing:
            if existing["status"] == "accepted":
                raise HTTPException(409, "already_friends")
            if existing["status"] == "pending":
                raise HTTPException(409, "request_already_sent")

        # Reverse direction (they sent us a request earlier — we accept by adding them back)
        reverse = conn.execute(
            "SELECT * FROM friendships WHERE user_id = ? AND friend_user_id = ?",
            (target["id"], user["id"]),
        ).fetchone()

        if reverse and reverse["status"] == "pending":
            # Auto-accept: mark reverse accepted + create our forward as accepted
            conn.execute(
                "UPDATE friendships SET status = 'accepted', responded_at = ? WHERE id = ?",
                (now_iso(), reverse["id"]),
            )
            conn.execute(
                "INSERT INTO friendships (user_id, friend_user_id, status, created_at, responded_at) "
                "VALUES (?, ?, 'accepted', ?, ?)",
                (user["id"], target["id"], now_iso(), now_iso()),
            )
            # Phase C trigger #3 (2026-05-12): mutual friendship just formed.
            # Notify the OTHER person ("@nick принял твой запрос"). The acceptor
            # (current user) doesn't need a push — they just initiated the
            # action and see the success in-UI.
            try:
                send_push_to_user(int(target["id"]), {
                    "title": f"@{user['nickname']} теперь твой друг",
                    "body": "Можешь сравнить вкусы и слать вызовы.",
                    "url": "/?screen=friends",
                    "tag": f"friend_accepted:{user['id']}",
                })
            except Exception as e:
                logger.warning("friend-accept push failed: %s", e)
            return {"ok": True, "auto_accepted": True, "friend": {"id": target["id"], "nickname": target["nickname"]}}

        # New pending request
        conn.execute(
            "INSERT INTO friendships (user_id, friend_user_id, status, created_at) "
            "VALUES (?, ?, 'pending', ?)",
            (user["id"], target["id"], now_iso()),
        )
        # Phase C trigger #2 (2026-05-12): notify the recipient that someone
        # added them. They click → land on profile → see incoming request.
        try:
            send_push_to_user(int(target["id"]), {
                "title": f"@{user['nickname']} хочет в друзья",
                "body": "Открой профиль, чтобы принять или отклонить.",
                "url": "/?screen=friends",
                "tag": f"friend_request:{user['id']}",
                "requireInteraction": False,
            })
        except Exception as e:
            logger.warning("friend-request push failed: %s", e)
        return {"ok": True, "auto_accepted": False, "friend": {"id": target["id"], "nickname": target["nickname"]}}


@app.get("/api/friends")
def list_friends(user: dict = Depends(require_user)):
    with db() as conn:
        # Outgoing pending (I sent, awaiting them)
        outgoing = conn.execute(
            """
            SELECT f.*, u.nickname AS friend_nickname, u.avatar_glyph AS friend_avatar_glyph
            FROM friendships f JOIN users u ON f.friend_user_id = u.id
            WHERE f.user_id = ? AND f.status = 'pending'
            ORDER BY f.created_at DESC
            """,
            (user["id"],),
        ).fetchall()
        # Incoming pending (they sent, awaiting me)
        incoming = conn.execute(
            """
            SELECT f.*, u.nickname AS friend_nickname, u.avatar_glyph AS friend_avatar_glyph
            FROM friendships f JOIN users u ON f.user_id = u.id
            WHERE f.friend_user_id = ? AND f.status = 'pending'
            ORDER BY f.created_at DESC
            """,
            (user["id"],),
        ).fetchall()
        # Accepted (mutual) — read from my forward direction (canonical)
        accepted = conn.execute(
            """
            SELECT f.*, u.nickname AS friend_nickname, u.avatar_glyph AS friend_avatar_glyph
            FROM friendships f JOIN users u ON f.friend_user_id = u.id
            WHERE f.user_id = ? AND f.status = 'accepted'
            ORDER BY COALESCE(f.responded_at, f.created_at) DESC
            """,
            (user["id"],),
        ).fetchall()

    return {
        "outgoing": [_friend_row_to_dict(r) for r in outgoing],
        "incoming": [_friend_row_to_dict(r) for r in incoming],
        "accepted": [_friend_row_to_dict(r) for r in accepted],
    }


@app.post("/api/friends/{fid}/accept")
def accept_friend_request(fid: int, user: dict = Depends(require_user)):
    other_user_id: int | None = None
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM friendships WHERE id = ? AND friend_user_id = ? AND status = 'pending'",
            (fid, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(404, "request_not_found")
        other_user_id = int(row["user_id"])
        # Mark incoming as accepted
        conn.execute(
            "UPDATE friendships SET status = 'accepted', responded_at = ? WHERE id = ?",
            (now_iso(), fid),
        )
        # Insert (or update) reverse direction
        existing_reverse = conn.execute(
            "SELECT id FROM friendships WHERE user_id = ? AND friend_user_id = ?",
            (user["id"], row["user_id"]),
        ).fetchone()
        if existing_reverse:
            conn.execute(
                "UPDATE friendships SET status = 'accepted', responded_at = ? WHERE id = ?",
                (now_iso(), existing_reverse["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO friendships (user_id, friend_user_id, status, created_at, responded_at) "
                "VALUES (?, ?, 'accepted', ?, ?)",
                (user["id"], row["user_id"], now_iso(), now_iso()),
            )
    # Phase C trigger #3 (2026-05-12): notify the ORIGINAL requester that
    # we accepted. They sent the request earlier and presumably forgot;
    # this prompt brings them back into the app to start interacting.
    if other_user_id is not None:
        try:
            send_push_to_user(other_user_id, {
                "title": f"@{user['nickname']} принял твой запрос",
                "body": "Теперь вы друзья. Можешь сравнить вкусы.",
                "url": "/?screen=friends",
                "tag": f"friend_accepted:{user['id']}",
            })
        except Exception as e:
            logger.warning("friend-accept push failed: %s", e)
    return {"ok": True}


@app.post("/api/friends/{fid}/decline")
def decline_friend_request(fid: int, user: dict = Depends(require_user)):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM friendships WHERE id = ? AND (user_id = ? OR friend_user_id = ?) AND status = 'pending'",
            (fid, user["id"], user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(404, "request_not_found")
        # Delete the pending request (sender or receiver can drop it)
        conn.execute("DELETE FROM friendships WHERE id = ?", (fid,))
    return {"ok": True}


@app.delete("/api/friends/{fid}")
def remove_friend(fid: int, user: dict = Depends(require_user)):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM friendships WHERE id = ? AND (user_id = ? OR friend_user_id = ?)",
            (fid, user["id"], user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(404, "not_found")
        # Drop both directions
        conn.execute(
            "DELETE FROM friendships WHERE (user_id = ? AND friend_user_id = ?) OR (user_id = ? AND friend_user_id = ?)",
            (row["user_id"], row["friend_user_id"], row["friend_user_id"], row["user_id"]),
        )
    return {"ok": True}


# ─── Position-pair scoring table for friend-compare (v2, 2026-05-21) ───
# Each shared item between two users' top-3 is scored by where it sits on
# each side. Symmetric (1+2 = 2+1). Values were tuned to user intuition:
# top-1 perfect match is the gold standard; one-position drift costs ~35%;
# items at the bottom of both lists still register but at quarter strength.
_PAIR_SCORES: dict = {
    (1, 1): 1.00,
    (1, 2): 0.65, (2, 1): 0.65,
    (2, 2): 0.55,
    (1, 3): 0.40, (3, 1): 0.40,
    (2, 3): 0.30, (3, 2): 0.30,
    (3, 3): 0.20,
}
# Max achievable sum when N items are shared and placed optimally.
# N=1: only one item can occupy any pair, best is 1+1 = 1.0
# N=2: 1+1 plus 2+2 = 1.55
# N=3: 1+1 plus 2+2 plus 3+3 = 1.75
_MAX_BY_N: dict = {0: 0.0, 1: 1.0, 2: 1.55, 3: 1.75}


def _per_category_fit(my_top3: list, their_top3: list) -> float:
    """Sum-adaptive per-category match score in 0.0..1.0.

    Considers ALL items both sides ranked in their top-3, not just the
    best pair. Normalizes by the max possible for the number of shared
    items (so e.g. a single top-1 match scores 100%, not 57%, because
    that's all there is to share). Case-insensitive name matching."""
    my_pos: dict = {}
    for i, name in enumerate(my_top3, 1):
        if name and name.strip():
            my_pos[name.strip().lower()] = i
    their_pos: dict = {}
    for i, name in enumerate(their_top3, 1):
        if name and name.strip():
            their_pos[name.strip().lower()] = i
    shared = set(my_pos) & set(their_pos)
    n = len(shared)
    if n == 0:
        return 0.0
    total = sum(_PAIR_SCORES.get((my_pos[k], their_pos[k]), 0.0) for k in shared)
    denom = _MAX_BY_N.get(n, 1.75)
    return total / denom if denom > 0 else 0.0


@app.get("/api/friends/{friend_user_id}/compare")
def compare_with_friend(friend_user_id: int, user: dict = Depends(require_user)):
    """Compare the current user's results with a friend's, category-by-category.

    Returns:
      - friend: {id, nickname, avatar_glyph}
      - my_total / their_total / overlap_count
      - match_percent (agreed / overlap_count, 0 if no overlap)
      - agreed: [{category_id, category_name, top1_name}]  (same top1)
      - disagreed: [{category_id, category_name, my_top1_name, their_top1_name,
                    my_top3, their_top3, soft_overlap}]
      - my_only / their_only: categories only one side has played

    'soft_overlap' is true when each side's top1 appears in the other's top3
    (a near-miss signal even when top1s differ).
    """
    me_id = user["id"]
    if friend_user_id == me_id:
        raise HTTPException(400, "cannot_compare_with_self")

    with db() as conn:
        # Must be accepted friendship in either direction
        f = conn.execute(
            """SELECT 1 FROM friendships
               WHERE status = 'accepted'
                 AND ((user_id = ? AND friend_user_id = ?)
                   OR (user_id = ? AND friend_user_id = ?))
               LIMIT 1""",
            (me_id, friend_user_id, friend_user_id, me_id),
        ).fetchone()
        if not f:
            raise HTTPException(403, "not_friends")

        friend = conn.execute(
            "SELECT id, nickname, avatar_glyph FROM users WHERE id = ?",
            (friend_user_id,)
        ).fetchone()
        if not friend:
            raise HTTPException(404, "friend_user_not_found")

        my_results = conn.execute(
            "SELECT * FROM results WHERE user_id = ? ORDER BY completed_at DESC",
            (me_id,)
        ).fetchall()
        their_results = conn.execute(
            "SELECT * FROM results WHERE user_id = ? ORDER BY completed_at DESC",
            (friend_user_id,)
        ).fetchall()

    # Build "latest result per category" maps
    def _latest_by_cat(rows):
        out: dict = {}
        for r in rows:  # rows already DESC by completed_at
            cid = r["category_id"]
            if cid and cid not in out:
                out[cid] = r
        return out

    mine = _latest_by_cat(my_results)
    theirs = _latest_by_cat(their_results)

    overlap_ids = set(mine.keys()) & set(theirs.keys())
    my_only_ids = set(mine.keys()) - set(theirs.keys())
    their_only_ids = set(theirs.keys()) - set(mine.keys())

    agreed: list = []
    disagreed: list = []
    for cid in overlap_ids:
        mr = mine[cid]
        tr = theirs[cid]
        my_top1 = (mr["top1_name"] or "").strip()
        their_top1 = (tr["top1_name"] or "").strip()
        my_top3 = [t for t in [mr["top1_name"], mr["top2_name"], mr["top3_name"]] if t]
        their_top3 = [t for t in [tr["top1_name"], tr["top2_name"], tr["top3_name"]] if t]
        if my_top1 and my_top1.lower() == their_top1.lower():
            agreed.append({
                "category_id": cid,
                "category_name": mr["category_name"] or tr["category_name"],
                "top1_name": my_top1,
                # 2026-05-12: include item_id so frontend's _localizedItemName
                # can resolve the localized name. Without this it falls back
                # to top1_name (whichever language was used at play time),
                # which causes mixed-lang renders on the compare screen.
                "top1_id": mr["top1_id"],
            })
        else:
            soft = (
                my_top1 and their_top1
                and (my_top1 in their_top3 or their_top1 in my_top3)
            )
            disagreed.append({
                "category_id": cid,
                "category_name": mr["category_name"] or tr["category_name"],
                "my_top1_name": my_top1,
                "their_top1_name": their_top1,
                # Same fix as agreed: include ids for per-side localization.
                "my_top1_id": mr["top1_id"],
                "their_top1_id": tr["top1_id"],
                "my_top3": my_top3,
                "their_top3": their_top3,
                "soft_overlap": bool(soft),
            })

    overlap_count = len(overlap_ids)
    # ─── POSITION-AWARE MATCH SCORING (v2, 2026-05-21) ───────────────
    # Two-layer model:
    #   1. per_category_fit (sum-adaptive): for each category in overlap,
    #      look at every item BOTH sides ranked in their top-3, score the
    #      pair by position pair (e.g. 1+1 = 1.0, 1+3 = 0.4), sum the
    #      pair scores, and normalize by the max achievable for that
    #      number of shared items (so top-1-only matches don't get
    #      penalized for "missing" extra matches that couldn't exist).
    #   2. coverage = overlap_count / asker_total. Penalizes the player
    #      with more categories played for the friend's unexplored ones.
    #
    # Display rule is asymmetric per user request:
    #   - asker is the SMALLER player (or equal+tiny overlap) → show
    #     optimistic per_cat_fit alone + "play more for accuracy" hint
    #   - asker is the BIGGER player → show coverage-adjusted score
    #     + "matched on N tournaments" context
    # This matches the human reading: smaller player needs encouragement
    # to keep playing; bigger player needs honest confidence-adjusted view.
    per_cat_scores: dict = {}
    for cid in overlap_ids:
        mr = mine[cid]
        tr = theirs[cid]
        my_top3 = [t for t in [mr["top1_name"], mr["top2_name"], mr["top3_name"]] if t]
        their_top3 = [t for t in [tr["top1_name"], tr["top2_name"], tr["top3_name"]] if t]
        per_cat_scores[cid] = _per_category_fit(my_top3, their_top3)

    # Attach per-category fit to each agreed/disagreed row for the UI
    # to render per-row mini-percentages (replaces the binary "in your
    # top 3" badge with a quantitative indicator).
    for a in agreed:
        a["per_category_fit"] = round(100 * per_cat_scores.get(a["category_id"], 1.0))
    for d in disagreed:
        d["per_category_fit"] = round(100 * per_cat_scores.get(d["category_id"], 0.0))

    per_cat_fit = (sum(per_cat_scores.values()) / overlap_count) if overlap_count > 0 else 0.0
    my_total_count = len(mine)
    their_total_count = len(theirs)
    asker_coverage = (overlap_count / my_total_count) if my_total_count > 0 else 0.0

    # Provisional = "the number is preliminary, play more for accuracy".
    # Two triggers: asker has fewer categories (their view is more limited)
    # OR the absolute overlap is too small to be statistically meaningful.
    _PROVISIONAL_OVERLAP_THRESHOLD = 3
    if my_total_count < their_total_count:
        is_provisional = True
    elif my_total_count > their_total_count:
        is_provisional = False
    else:
        is_provisional = (overlap_count < _PROVISIONAL_OVERLAP_THRESHOLD)

    if is_provisional:
        match_percent = round(per_cat_fit * 100)
    else:
        match_percent = round(per_cat_fit * asker_coverage * 100)

    # Lightweight category summaries for "only one side played" lists.
    # Include top1_id (not just name) so the frontend's _localizedItemName
    # can resolve EN/RU from CATEGORIES instead of falling back to the
    # play-time snapshot. Fixes the mixed-language compare screen bug
    # reported 2026-05-12.
    def _only_summary(ids, src):
        return [
            {
                "category_id": cid,
                "category_name": src[cid]["category_name"],
                "top1_name": src[cid]["top1_name"],
                "top1_id": src[cid]["top1_id"],
            }
            for cid in ids
        ]

    return {
        "friend": dict(friend),
        "my_total": my_total_count,
        "their_total": their_total_count,
        "overlap_count": overlap_count,
        "match_percent": match_percent,
        # Extra fields for the v2 UI to render proper context labels and
        # per-row scores. `per_cat_fit_avg` is the "pure" quality number
        # (0..100, ignores coverage); `is_provisional` flips the header
        # label between "play more for accuracy" and "matched on N".
        "per_cat_fit_avg": round(per_cat_fit * 100),
        "is_provisional": is_provisional,
        "agreed": agreed,
        "disagreed": disagreed,
        "my_only": _only_summary(my_only_ids, mine),
        "their_only": _only_summary(their_only_ids, theirs),
    }


@app.patch("/api/submissions/{sid}")
def update_submission(sid: int, body: SubmissionUpdate,
                      _role: str = Depends(require_mod_or_admin),
                      actor: dict = Depends(get_admin_actor)):
    apply_result: Optional[dict] = None
    with db() as conn:
        row = conn.execute("SELECT * FROM submissions WHERE id = ?", (sid,)).fetchone()
        if not row:
            raise HTTPException(404, "submission_not_found")

        # Build dynamic UPDATE: only patch fields the caller actually sent.
        sets, vals = [], []
        edited_fields = []
        if body.status is not None:
            # Guard: a category submission can only become 'approved' via
            # POST /api/admin/categories/apply-from-json (which atomically writes
            # the category to categories.json AND flips status). Direct PATCH
            # would leave an orphaned 'approved' row with no real category.
            if body.status == "approved" and row['type'] == "category":
                raise HTTPException(
                    400,
                    "category_must_be_published_via_apply_from_json",
                )
            sets.append("status = ?"); vals.append(body.status)
            sets.append("decided_at = ?"); vals.append(now_iso())
            edited_fields.append("status")
        if body.decision_note is not None:
            sets.append("decision_note = ?"); vals.append(body.decision_note)
            edited_fields.append("decision_note")
        if body.title is not None:
            new_title = body.title.strip()
            if not new_title:
                raise HTTPException(422, "title_empty")
            sets.append("title = ?"); vals.append(new_title)
            edited_fields.append("title")
        if body.description is not None:
            sets.append("description = ?"); vals.append(body.description)
            edited_fields.append("description")
        if body.cluster is not None:
            sets.append("cluster = ?"); vals.append(body.cluster)
            edited_fields.append("cluster")
        if body.target_category_id is not None:
            sets.append("target_category_id = ?"); vals.append(body.target_category_id)
            edited_fields.append("target_category_id")
        if body.attributed_nickname is not None:
            # Empty string → clear the attribution (NULL → fall back to original user_id).
            # Non-empty → resolve nickname to user_id, set attribution. NICK_RE
            # validation here so we fail fast with a useful error before hitting
            # the DB lookup. NOCASE so admin can type "Lmya" or "lmya" identically.
            nick_raw = body.attributed_nickname.strip()
            if nick_raw == "":
                sets.append("attributed_user_id = NULL")
                edited_fields.append("attributed_user_id_cleared")
            else:
                if not NICK_RE.match(nick_raw):
                    raise HTTPException(422, "invalid_attributed_nickname")
                target = conn.execute(
                    "SELECT id FROM users WHERE nickname = ? COLLATE NOCASE",
                    (nick_raw,)
                ).fetchone()
                if not target:
                    raise HTTPException(404, "attributed_user_not_found")
                sets.append("attributed_user_id = ?"); vals.append(int(target["id"]))
                edited_fields.append(f"attributed_user_id={target['id']}")

        if not sets:
            raise HTTPException(422, "no_fields_to_update")

        vals.append(sid)
        conn.execute(f"UPDATE submissions SET {', '.join(sets)} WHERE id = ?", vals)

        action_extras = {"id": sid, "type": row['type'], "edited": edited_fields}
        # Auto-apply approved 'item' submissions to categories.json. Re-read after
        # the UPDATE so we use the freshly-edited title (in case admin renamed before approve).
        # Single source of truth: if apply fails we ROLL BACK the status to
        # 'needs_review' so the user is NOT notified about a fake approval and
        # the submission stays in the moderator queue with the failure note.
        # Audit-7 P2.3: manual_categorization_required is NOT a failure —
        # it's the new explicit "approve recorded, item insertion deferred
        # to manual categorization in admin UI" path. Treat as success so
        # the moderator's approve decision sticks.
        approve_failed = False
        if body.status == "approved" and row['type'] == "item":
            updated_row = conn.execute("SELECT * FROM submissions WHERE id = ?", (sid,)).fetchone()
            apply_result = _apply_item_submission(dict(updated_row))
            action_extras["auto_apply"] = apply_result
            err = apply_result.get("error") or ""
            if not apply_result.get("applied") and err != "manual_categorization_required":
                conn.execute(
                    "UPDATE submissions SET status='needs_review', decided_at=NULL, decision_note=? WHERE id=?",
                    (f"auto-apply failed: {err or 'unknown_error'}", sid),
                )
                approve_failed = True
            elif err == "manual_categorization_required":
                # Approve sticks; just annotate the decision so admin sees
                # why categories.json wasn't auto-mutated.
                conn.execute(
                    "UPDATE submissions SET decision_note=? WHERE id=?",
                    ("approved — add manually via Categories editor "
                     "(auto-apply disabled until trigger-assignment UI exists)", sid),
                )

        # Action label: prefer status change name, else 'edit' for content edits.
        # If apply rolled back, log it as 'submission_apply_failed' so audit reflects reality.
        if approve_failed:
            action_label = "submission_apply_failed"
        else:
            action_label = f"submission_{body.status}" if body.status else "submission_edited"
        log_admin_action(conn, actor, action_label, body.title or row['title'], action_extras)
        # Re-read WITH the COALESCE join so the response carries the updated
        # submitter_nickname (matches GET /api/submissions shape). Otherwise
        # the admin UI gets stale display name after editing attribution.
        new_row = conn.execute(
            "SELECT s.*, "
            "       COALESCE(a.nickname, u.nickname) AS submitter_nickname, "
            "       u.nickname AS original_submitter_nickname, "
            "       a.nickname AS attributed_nickname "
            "FROM submissions s "
            "JOIN users u ON s.user_id = u.id "
            "LEFT JOIN users a ON s.attributed_user_id = a.id "
            "WHERE s.id = ?",
            (sid,)
        ).fetchone()
    sub_dict = submission_to_dict(new_row)
    publish_admin_event_sync('submission_updated', sub_dict)
    # 2026-05-16: push the submitter on approval (item-type only — category
    # approval goes through the apply-from-json endpoint which fires its own
    # push). Guarded by approve_failed so users aren't notified about a
    # rolled-back approval.
    try:
        if (body.status == "approved" and row['type'] == "item"
                and not approve_failed):
            sub_uid = int(row["user_id"]) if row["user_id"] else None
            sub_title = body.title or row["title"] or "вариант"
            target_cat = (row["target_category_id"] if row["target_category_id"] else None)
            if sub_uid:
                _notify_submission_approved(sub_uid, "item", sub_title, target_cat)
    except Exception as e:
        logger.warning("item-approved push wrap failed: %s", e)
    resp = {"submission": sub_dict}
    if apply_result is not None:
        resp["auto_apply"] = apply_result
    return resp


# ─── INIT ──────────────────────────────────────────────────────

db_init()
