"""Insight engine for the «Прочтение» / «Readout» profile section.

This module is the data-gathering layer for the insight cards system.
It does NOT yet expose an HTTP endpoint or implement the rule engine;
that lives in main.py (planned chunks B2/B3).

Scope of B1 (this file):
- load_templates(): read insight_templates.json once, cache by mtime
- compute_user_stats(): single function that runs a series of SQL queries
  against the results table and returns a dict of EASY-tier placeholder
  values for one user (~25 fields like top_cluster, top_item_count, etc.)
- format_phrase(): plural-aware Russian number-noun formatter
- clean_archetype_name(): strips «» from hybrid archetype names
- render_template_text(): substitutes {placeholders} in a template

NOT yet in scope:
- Trigger DSL eval / priority-sort / rotation (B2)
- HTTP endpoint with cache (B3)
- MEDIUM-tier stats: contrarian, twins, opposites (B1b)
- Stats requiring new tables: least_item, twin history, skip telemetry (B1c)

Design choices:
- compute_user_stats() is pure: takes (conn, user_id, categories_list)
  and returns dict. No global state. Easy to unit-test.
- Categories list is passed in (not loaded internally) so callers can
  reuse main.py's cached _load_categories().
- Missing stats are returned as None (or omitted). Rule engine will
  interpret None as "trigger does not fire" via try/except on the DSL.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Path to the templates JSON. Same env-var pattern as DB_PATH in main.py.
TEMPLATES_JSON_PATH = Path(os.environ.get(
    "UPG_INSIGHT_TEMPLATES_PATH",
    "/opt/untitled-pick-game-api/data/insight_templates.json",
))

# In-process cache for templates, keyed by mtime so updates to the JSON
# file are picked up automatically without a server restart.
_templates_cache: dict = {"mtime": None, "data": []}


def load_templates() -> list[dict]:
    """Return list of insight template dicts. Re-reads file on mtime change.

    Each template has shape:
      {
        "id": str,
        "type": str,
        "trigger": str (DSL expression),
        "priority": int,
        "ru": {"headline": str, "body": str},
        "en": {"headline": str, "body": str},
      }
    """
    if not TEMPLATES_JSON_PATH.exists():
        return []
    try:
        mtime = TEMPLATES_JSON_PATH.stat().st_mtime
    except OSError:
        return _templates_cache.get("data", [])
    if mtime != _templates_cache.get("mtime"):
        try:
            _templates_cache["data"] = json.loads(
                TEMPLATES_JSON_PATH.read_text(encoding="utf-8")
            )
            _templates_cache["mtime"] = mtime
        except Exception:
            # Fail safe: keep old cache rather than crash.
            pass
    return _templates_cache.get("data", [])


# ---------------------------------------------------------------------------
# Russian plural forms
# ---------------------------------------------------------------------------
# Maps each `_count`-like stat to its (singular, few, many) noun forms.
# Used by format_phrase() to build strings like "5 раз", "2 турнира".
# IMPORTANT: the forms here are NOMINATIVE plural; templates must put the
# {X_phrase} placeholder in a position where nominative reads naturally
# (e.g. "уже {top_item_count_phrase}" = "уже 5 раз"). The grammar-fix
# prompt enforces this convention in template text.
PHRASE_FORMS: dict[str, tuple[str, str, str]] = {
    "top_item_count":              ("раз", "раза", "раз"),
    "top_cat_count":               ("раз", "раза", "раз"),
    "top_twin_count":              ("турнир", "турнира", "турниров"),
    "archetype_most_freq_count":   ("раз", "раза", "раз"),
    "streak_days":                 ("день", "дня", "дней"),
    "best_streak_days":            ("день", "дня", "дней"),
    "previous_streak_days":        ("день", "дня", "дней"),
    "least_item_count":            ("раз", "раза", "раз"),
    "contrarian_count":            ("раз", "раза", "раз"),
    "avg_session_len_min":         ("минута", "минуты", "минут"),
}


def plural_ru(n: int, forms: tuple[str, str, str]) -> str:
    """Pick the right Russian noun form for a count.

    forms = (singular, few, many)
      singular: для 1, 21, 31 (но не 11)
      few:      для 2-4, 22-24 (но не 12-14)
      many:     для 5-20, 25-30, etc.

    Examples:
      plural_ru(1, ('раз','раза','раз'))  -> 'раз'
      plural_ru(2, ('раз','раза','раз'))  -> 'раза'
      plural_ru(11, ('день','дня','дней')) -> 'дней'
    """
    n10 = n % 10
    n100 = n % 100
    if n10 == 1 and n100 != 11:
        return forms[0]
    if 2 <= n10 <= 4 and not (12 <= n100 <= 14):
        return forms[1]
    return forms[2]


def format_phrase(stat_key: str, n) -> str | None:
    """Build the plural-aware Russian string for one numeric stat.

    Special handling:
    - n < 1 for time-like stats: returns "меньше минуты" / "меньше дня"
    - n == 0 for count stats: returns "0 раз" (still grammatical)
    - fractional n: rounded to nearest int before pluralizing
    """
    if n is None:
        return None
    if stat_key not in PHRASE_FORMS:
        return None
    forms = PHRASE_FORMS[stat_key]
    # Sub-unit values: avg_session_len_min=0.8 should NOT render as "0 минут"
    try:
        n_float = float(n)
    except (TypeError, ValueError):
        return None
    if n_float < 1:
        # Special wording for "less than one"
        if stat_key == "avg_session_len_min":
            return "меньше минуты"
        if stat_key in ("streak_days", "best_streak_days", "previous_streak_days"):
            return "меньше дня"
        # For count-like (раз): fall through to 0
    n_int = int(round(n_float))
    return f"{n_int} {plural_ru(n_int, forms)}"


# ---------------------------------------------------------------------------
# Archetype name cleanup
# ---------------------------------------------------------------------------
# Hybrid archetypes are stored as «Имя1» × «Имя2» (from synthesizeHybridArchetype
# in game.html). When templates wrap them in additional «» they become
# ««Имя1» × «Имя2»» which reads badly. Strip the inner «» so the template's
# outer wrap (if any) is the only quoting.

def clean_archetype_name(name: str | None) -> str | None:
    """Strip Russian guillemets «» from an archetype name.

    Input  → Output examples:
      "«А» × «Б»"  → "А × Б"
      "«А»"        → "А"
      "А × Б"      → "А × Б"
      "А"          → "А"
      None         → None
    """
    if not name:
        return name
    return name.replace("«", "").replace("»", "")


# ---------------------------------------------------------------------------
# Stats aggregator
# ---------------------------------------------------------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(s: str | None) -> datetime | None:
    """Parse an ISO datetime from results.completed_at. Handles trailing Z."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_user_stats(
    conn: sqlite3.Connection,
    user_id: int,
    categories: list[dict],
) -> dict:
    """Compute EASY-tier insight stats for one user.

    Returns a flat dict suitable for both trigger DSL evaluation and
    template rendering. Keys are placeholder names without the {} braces.

    Implementation: one SELECT pulls all of the user's results into memory
    (typical user has <500 rows, no need for streaming). Aggregations are
    done in Python with collections.Counter for clarity. SQL re-queries
    would be more efficient at scale, but at our user count the difference
    is noise and Python is easier to reason about.

    The categories list is for cluster/coverage lookups (it lives in
    categories.json, not the DB).
    """
    cat_by_id: dict[str, dict] = {c["id"]: c for c in categories if "id" in c}
    total_cat_count = len(cat_by_id)
    stats: dict = {}

    # ------- Load all results for the user (descending by time) -------
    rows = conn.execute(
        """
        SELECT category_id, category_name, top1_id, top1_name,
               archetype_name, archetype_source, duration_sec, completed_at
        FROM results
        WHERE user_id = ?
        ORDER BY completed_at DESC
        """,
        (user_id,),
    ).fetchall()
    results = [dict(r) for r in rows]

    # ------- Basic counts -------
    stats["total_tournaments"] = len(results)

    now = _utc_now()
    cutoff_7d_iso = (now - timedelta(days=7)).isoformat()
    recent7 = [r for r in results if (r["completed_at"] or "") > cutoff_7d_iso]
    stats["tournaments_last_7d"] = len(recent7)

    if not results:
        # Early return: warmup_empty_readout_v1 will be the only match.
        _add_phrase_fields(stats)
        return stats

    # ------- Coverage (% of all categories played at least once) -------
    unique_cats_played = set(r["category_id"] for r in results)
    stats["coverage_pct"] = (
        round(100 * len(unique_cats_played) / total_cat_count)
        if total_cat_count else 0
    )

    # ------- Cluster distribution -------
    cluster_counts: Counter = Counter()
    for r in results:
        cat = cat_by_id.get(r["category_id"])
        if cat:
            cluster_counts[cat.get("cluster", "?")] += 1
    if cluster_counts:
        top_cluster, top_cluster_n = cluster_counts.most_common(1)[0]
        stats["top_cluster"] = top_cluster
        stats["top_cluster_pct"] = round(100 * top_cluster_n / len(results))
        if len(cluster_counts) >= 2:
            second_cluster, second_n = cluster_counts.most_common(2)[1]
            stats["second_cluster"] = second_cluster
            stats["second_cluster_pct"] = round(100 * second_n / len(results))

    # ------- Top category (most-played) -------
    cat_counts = Counter(r["category_id"] for r in results)
    if cat_counts:
        top_cat_id, top_cat_n = cat_counts.most_common(1)[0]
        stats["top_cat"] = cat_by_id.get(top_cat_id, {}).get("name", top_cat_id)
        stats["top_cat_count"] = top_cat_n

    # ------- Most recently played category -------
    stats["recently_played_cat"] = results[0]["category_name"]

    # ------- Top item (most-winning) -------
    item_counts = Counter(r["top1_id"] for r in results if r["top1_id"])
    if item_counts:
        top_item_id, top_item_n = item_counts.most_common(1)[0]
        # Find first occurrence to get name + category
        for r in results:
            if r["top1_id"] == top_item_id:
                stats["top_item"] = r["top1_name"] or top_item_id
                stats["top_item_cat"] = r["category_name"]
                break
        stats["top_item_count"] = top_item_n

    # ------- Archetypes -------
    arch_counts = Counter(
        clean_archetype_name(r["archetype_name"])
        for r in results
        if r["archetype_name"]
    )
    if arch_counts:
        am, ac = arch_counts.most_common(1)[0]
        stats["archetype_most_freq"] = am
        stats["archetype_most_freq_count"] = ac

    last_arch = results[0]["archetype_name"]
    if last_arch:
        stats["archetype_last"] = clean_archetype_name(last_arch)
        stats["archetype_last_cat"] = results[0]["category_name"]

    # ------- Archetype shift (recent vs older half) -------
    # Compare the most-frequent archetype in the recent half vs older half.
    # Only fires if user has enough history to make a halving meaningful.
    if len(results) >= 6:
        half = len(results) // 2
        old_arch = Counter(
            clean_archetype_name(r["archetype_name"])
            for r in results[half:]
            if r["archetype_name"]
        )
        new_arch = Counter(
            clean_archetype_name(r["archetype_name"])
            for r in results[:half]
            if r["archetype_name"]
        )
        if old_arch and new_arch:
            old_top = old_arch.most_common(1)[0][0]
            new_top = new_arch.most_common(1)[0][0]
            if old_top != new_top:
                stats["archetype_recent_shift_from"] = old_top
                stats["archetype_recent_shift_to"] = new_top

    # ------- Cluster shift (last 7d vs older) -------
    if len(results) >= 6 and recent7:
        old_c: Counter = Counter()
        new_c: Counter = Counter()
        for r in results:
            cat = cat_by_id.get(r["category_id"])
            if not cat:
                continue
            cl = cat.get("cluster", "?")
            if (r["completed_at"] or "") > cutoff_7d_iso:
                new_c[cl] += 1
            else:
                old_c[cl] += 1
        if old_c and new_c:
            old_top = old_c.most_common(1)[0][0]
            new_top = new_c.most_common(1)[0][0]
            if old_top != new_top:
                stats["recent_shift_from"] = old_top
                stats["recent_shift_to"] = new_top

    # ------- Time-of-day favorite -------
    # Hour of UTC completed_at, modal. Note: this is UTC, not user's local
    # TZ. For Almaty users it's offset by 5h. For now we accept the skew;
    # localizing would require storing user TZ which we don't.
    hours: Counter = Counter()
    for r in results:
        ts = r["completed_at"]
        if ts and len(ts) >= 13:
            try:
                hours[int(ts[11:13])] += 1
            except ValueError:
                pass
    if hours:
        stats["fav_hour"] = hours.most_common(1)[0][0]

    # ------- Days since last play -------
    last_dt = _parse_dt(results[0]["completed_at"])
    if last_dt:
        stats["days_since_last_play"] = (now - last_dt).days

    # ------- Average session duration (minutes) -------
    durs = [r["duration_sec"] for r in results if r["duration_sec"]]
    if durs:
        # Keep one decimal; format_phrase() handles the sub-1-min case.
        stats["avg_session_len_min"] = round(sum(durs) / len(durs) / 60, 1)

    # ------- Play streak (consecutive days ending today/yesterday) -------
    # Mirrors compute_play_streak() in main.py to avoid a cross-module
    # dependency. Pure function over the user's distinct play-dates.
    played_dates = sorted(
        set((r["completed_at"] or "")[:10] for r in results if r["completed_at"]),
        reverse=True,
    )
    stats["streak_days"] = _consecutive_streak_from_dates(played_dates, now)

    # ------- Uniqueness (% of choices that differ from the median) -------
    # Reuses the same shape as /api/stats/me but recomputed inline so
    # this module stays self-contained. The metric: for each (user, cat)
    # latest result, compare user's top1 against majority of others'
    # latest top1 for that cat; uniqueness = 100 - avg(majority_share).
    stats["uniqueness_pct"] = _compute_uniqueness(
        conn, user_id, only_last_7d=False, now=now
    )
    stats["uniqueness_pct_recent"] = _compute_uniqueness(
        conn, user_id, only_last_7d=True, now=now
    )

    # ------- Add _phrase versions for every eligible numeric stat -------
    _add_phrase_fields(stats)

    return stats


def _add_phrase_fields(stats: dict) -> None:
    """For every key in PHRASE_FORMS that has a value in stats, add
    a sibling key '<key>_phrase' with the pluralized string."""
    for key in PHRASE_FORMS:
        if key in stats and stats[key] is not None:
            phrase = format_phrase(key, stats[key])
            if phrase is not None:
                stats[f"{key}_phrase"] = phrase


def _consecutive_streak_from_dates(dates: list[str], now: datetime) -> int:
    """Count consecutive days at the head of `dates` (ISO YYYY-MM-DD,
    descending). Allows yesterday as the head (so users who haven't yet
    played today don't see a 0)."""
    if not dates:
        return 0
    today = now.date()
    yesterday = today - timedelta(days=1)
    try:
        parsed = [datetime.fromisoformat(d).date() for d in dates]
    except ValueError:
        return 0
    if parsed[0] != today and parsed[0] != yesterday:
        return 0
    streak = 1
    for i in range(1, len(parsed)):
        if (parsed[i - 1] - parsed[i]) == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def _compute_uniqueness(
    conn: sqlite3.Connection,
    user_id: int,
    only_last_7d: bool,
    now: datetime,
) -> int | None:
    """Average uniqueness across categories where the user has co-voters.

    Logic mirrors stats_me in main.py:
      - Per (user, cat), take latest result.
      - For each user-cat, compute share = % of OTHERS who picked same top1.
      - Average shares, uniqueness = 100 - avg_share.

    If only_last_7d=True, restrict the user's set to results completed in
    the last 7 days (others' latest results are unchanged - those are the
    baseline).

    Returns None if no overlapping categories exist (insufficient data).
    """
    cutoff = (now - timedelta(days=7)).isoformat() if only_last_7d else None

    # User's latest per-cat result (optionally restricted to last 7d)
    if cutoff:
        my_rows = conn.execute(
            """
            SELECT category_id, top1_id FROM results r
            WHERE user_id = ? AND completed_at > ?
              AND completed_at = (
                SELECT MAX(completed_at) FROM results
                WHERE user_id = r.user_id AND category_id = r.category_id
              )
            """,
            (user_id, cutoff),
        ).fetchall()
    else:
        my_rows = conn.execute(
            """
            SELECT category_id, top1_id FROM results r
            WHERE user_id = ?
              AND completed_at = (
                SELECT MAX(completed_at) FROM results
                WHERE user_id = r.user_id AND category_id = r.category_id
              )
            """,
            (user_id,),
        ).fetchall()

    if not my_rows:
        return None

    shares: list[int] = []
    for me in my_rows:
        dist = conn.execute(
            """
            SELECT top1_id, COUNT(*) AS cnt FROM results r
            WHERE category_id = ? AND user_id != ?
              AND completed_at = (
                SELECT MAX(completed_at) FROM results
                WHERE user_id = r.user_id AND category_id = r.category_id
              )
            GROUP BY top1_id
            """,
            (me["category_id"], user_id),
        ).fetchall()
        total = sum(d["cnt"] for d in dist)
        if total == 0:
            continue
        my_count = sum(d["cnt"] for d in dist if d["top1_id"] == me["top1_id"])
        shares.append(round(100 * my_count / total))

    if not shares:
        return None
    return round(100 - sum(shares) / len(shares))


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

_PLACEHOLDER_RE = re.compile(r"\{([a-z_]+)\}")


def render_template_text(text: str, stats: dict) -> str:
    """Replace {placeholder} occurrences with stats[placeholder].

    Missing placeholders render as the literal string (e.g. '{foo}') so
    the issue is visible during development. In production, the rule
    engine should never select a template whose trigger references a
    missing stat - this fallback is a safety net, not a normal path.
    """
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key in stats and stats[key] is not None:
            return str(stats[key])
        return m.group(0)
    return _PLACEHOLDER_RE.sub(sub, text)
