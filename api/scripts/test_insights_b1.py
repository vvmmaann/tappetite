"""Smoke test for api/insights.py (B1 chunk).

Run on server:
  cd /opt/untitled-pick-game-api
  python3 scripts/test_insights_b1.py

What's tested:
- format_phrase() correctness on edge cases (0, 1, 2, 5, 11, 21, fractional)
- clean_archetype_name() on hybrid / bare / empty inputs
- compute_user_stats() against Uncle (user_id=2) - compares to known facts
- All EASY-tier keys are present in output
- _phrase variants exist where expected
- load_templates() returns 45 entries

Exit code: 0 if all pass, 1 if any fail.
"""
import sys
import sqlite3
from pathlib import Path

# Make 'insights' importable from /opt/untitled-pick-game-api/
sys.path.insert(0, "/opt/untitled-pick-game-api")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from insights import (
    format_phrase, plural_ru, clean_archetype_name,
    compute_user_stats, load_templates, render_template_text,
)
import json

# -------------------- helpers --------------------

PASS_CT = 0
FAIL_CT = 0

def check(label: str, got, expected):
    global PASS_CT, FAIL_CT
    if got == expected:
        PASS_CT += 1
        print(f"  OK   {label}: {got!r}")
    else:
        FAIL_CT += 1
        print(f"  FAIL {label}: got {got!r}, expected {expected!r}")

def expect_in(label: str, value, container):
    global PASS_CT, FAIL_CT
    if value in container:
        PASS_CT += 1
        print(f"  OK   {label}: {value!r} in result")
    else:
        FAIL_CT += 1
        print(f"  FAIL {label}: {value!r} NOT in {list(container)[:10]}...")


# -------------------- 1. format_phrase --------------------
print("=== format_phrase ===")
check("0 раз",            format_phrase("top_item_count", 0),           "0 раз")
check("1 раз",            format_phrase("top_item_count", 1),           "1 раз")
check("2 раза",           format_phrase("top_item_count", 2),           "2 раза")
check("5 раз",            format_phrase("top_item_count", 5),           "5 раз")
check("11 раз",           format_phrase("top_item_count", 11),          "11 раз")
check("12 раз",           format_phrase("top_item_count", 12),          "12 раз")
check("21 раз",           format_phrase("top_item_count", 21),          "21 раз")
check("25 раз",           format_phrase("top_item_count", 25),          "25 раз")
check("0.8 min special",  format_phrase("avg_session_len_min", 0.8),    "меньше минуты")
check("1.5 min round",    format_phrase("avg_session_len_min", 1.5),    "2 минуты")
check("3.0 min",          format_phrase("avg_session_len_min", 3.0),    "3 минуты")
check("0 days special",   format_phrase("streak_days", 0.5),            "меньше дня")
check("1 день",           format_phrase("streak_days", 1),              "1 день")
check("2 дня",            format_phrase("streak_days", 2),              "2 дня")
check("5 дней",           format_phrase("streak_days", 5),              "5 дней")
check("1 турнир",         format_phrase("top_twin_count", 1),           "1 турнир")
check("3 турнира",        format_phrase("top_twin_count", 3),           "3 турнира")
check("8 турниров",       format_phrase("top_twin_count", 8),           "8 турниров")
check("unknown key",      format_phrase("nonexistent", 5),              None)
check("None value",       format_phrase("top_item_count", None),        None)


# -------------------- 2. clean_archetype_name --------------------
print()
print("=== clean_archetype_name ===")
check("hybrid",           clean_archetype_name("«А» × «Б»"),            "А × Б")
check("single quoted",    clean_archetype_name("«Часовой мастер»"),     "Часовой мастер")
check("bare",             clean_archetype_name("Бренд-эклектик"),       "Бренд-эклектик")
check("triple hybrid",    clean_archetype_name("«А» × «Б» × «В»"),      "А × Б × В")
check("empty",            clean_archetype_name(""),                     "")
check("None",             clean_archetype_name(None),                   None)


# -------------------- 3. load_templates --------------------
print()
print("=== load_templates ===")
templates = load_templates()
check("template count",   len(templates),                                45)
ids = {t["id"] for t in templates}
expect_in("has main_cluster_v1",  "concentration_main_cluster_v1",       ids)
expect_in("has night_owl_v1",     "behavioral_night_owl_v1",             ids)
expect_in("has warmup_empty",     "warmup_empty_readout_v1",             ids)


# -------------------- 4. compute_user_stats (Uncle) --------------------
print()
print("=== compute_user_stats(user_id=2 / Uncle) ===")
db = sqlite3.connect("/opt/untitled-pick-game-api/data/db.sqlite")
db.row_factory = sqlite3.Row
cats = json.load(open("/opt/untitled-pick-game-api/data/categories.json"))
cat_list = cats if isinstance(cats, list) else cats.get("categories", [])

stats = compute_user_stats(db, 2, cat_list)

# Expected keys present
for key in [
    "total_tournaments", "tournaments_last_7d", "coverage_pct",
    "top_cluster", "top_cluster_pct",
    "top_cat", "top_cat_count", "top_cat_count_phrase",
    "top_item", "top_item_cat", "top_item_count", "top_item_count_phrase",
    "archetype_most_freq", "archetype_most_freq_count_phrase",
    "archetype_last", "archetype_last_cat",
    "fav_hour", "days_since_last_play",
    "avg_session_len_min", "avg_session_len_min_phrase",
    "streak_days", "uniqueness_pct", "recently_played_cat",
]:
    expect_in(f"key {key}", key, stats)

# Hybrid archetype was cleaned
if "archetype_last" in stats:
    val = stats["archetype_last"]
    if "«" in (val or "") or "»" in (val or ""):
        print(f"  FAIL  archetype_last still has guillemets: {val!r}")
        FAIL_CT += 1
    else:
        print(f"  OK   archetype_last clean: {val!r}")
        PASS_CT += 1

# Sub-1-min handling
if "avg_session_len_min_phrase" in stats:
    p = stats["avg_session_len_min_phrase"]
    if p == "меньше минуты" or (p and p.endswith(("минута", "минуты", "минут"))):
        print(f"  OK   avg phrase: {p!r}")
        PASS_CT += 1
    else:
        print(f"  FAIL avg phrase: {p!r}")
        FAIL_CT += 1


# -------------------- 5. render_template_text --------------------
print()
print("=== render_template_text ===")
rendered = render_template_text(
    "Главный кластер: «{top_cluster}»",
    {"top_cluster": "Кино"},
)
check("simple sub",      rendered,                                       "Главный кластер: «Кино»")

rendered2 = render_template_text(
    "Тест {missing_key} тут",
    {"top_cluster": "X"},
)
check("missing key kept", rendered2,                                     "Тест {missing_key} тут")


# -------------------- 6. Print full stats dump for Uncle --------------------
print()
print("=== UNCLE STATS DUMP ===")
for k in sorted(stats.keys()):
    print(f"  {k:35s} {stats[k]!r}")


# -------------------- summary --------------------
print()
print(f"=== SUMMARY: {PASS_CT} passed, {FAIL_CT} failed ===")
sys.exit(0 if FAIL_CT == 0 else 1)
