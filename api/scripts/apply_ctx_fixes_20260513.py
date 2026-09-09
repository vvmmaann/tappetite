"""Apply 16 ctx text fixes to /opt/untitled-pick-game-api/data/categories.json.

Two classes of fixes:

1. Four single-word ctxs that read as cryptic fragments (rf_opozd "хроника",
   rf_appr "других", gf_gossip "никогда", ch_invis "правда") — replaced with
   evocative 2-4 word phrases matching the style of well-written items in the
   same categories ("не перебивая", "без напоминаний", "потому что так быстрее").

2. All 12 biggest_future_fear items had English-only dev-placeholder ctxs
   ("burnout", "career anxiety", "regret"...) leaking into Russian display.
   The category is Russian; the ctx field must be Russian. ctx_en is left
   alone — it's correct that EN users see "burnout" etc.

Run on server:
    cd /opt/untitled-pick-game-api
    python scripts/apply_ctx_fixes_20260513.py
    systemctl restart untitled-pick-game-api

Backs up the original with a timestamp suffix before writing.
"""
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = Path("/opt/untitled-pick-game-api/data/categories.json")

# id -> new ctx (Russian only; ctx_en left untouched)
FIXES = {
    # red_flag — cryptic single-word fragments → fuller phrases
    "rf_opozd":                "это хроническое",
    "rf_appr":                 "от каждого встречного",
    # green_flag
    "gf_gossip":               "это для меня табу",
    # chat_style
    "ch_invis":                "честно, не видел",
    # biggest_future_fear — English placeholders → Russian phrases
    "biggest_future_fear-burn-out":          "сгореть и не восстать",
    "biggest_future_fear-wrong-profession":  "понять это в 40",
    "biggest_future_fear-years-wasted":      "и понять это поздно",
    "biggest_future_fear-alone":             "не с кем поговорить",
    "biggest_future_fear-disappoint-self":   "увидеть себя со стороны",
    "biggest_future_fear-family-expect":     "«мы верили в тебя»",
    "biggest_future_fear-others-life":       "по чужому сценарию",
    "biggest_future_fear-not-realize":       "оглянуться, а уже поздно",
    "biggest_future_fear-compare-others":    "и всегда проигрывать",
    "biggest_future_fear-lose-interest":     "ничего не хочется",
    "biggest_future_fear-comfort-trap":      "бояться любых изменений",
    "biggest_future_fear-never-understand":  "до самой пенсии",
}


def main():
    if not SRC.exists():
        print(f"[err] not found: {SRC}", file=sys.stderr)
        sys.exit(1)

    # Backup first — never overwrite without one
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup = SRC.with_suffix(f".json.bak.{ts}")
    shutil.copy2(SRC, backup)
    print(f"[ok] backup: {backup}")

    data = json.loads(SRC.read_text(encoding="utf-8"))
    cats = data if isinstance(data, list) else data.get("categories", [])

    applied = []
    missing = []
    for cat in cats:
        for it in cat.get("items", []):
            iid = it.get("id")
            if iid in FIXES:
                old = it.get("ctx", "")
                new = FIXES[iid]
                it["ctx"] = new
                applied.append((iid, old, new))

    found_ids = {a[0] for a in applied}
    for fid in FIXES:
        if fid not in found_ids:
            missing.append(fid)

    if missing:
        print(f"[warn] {len(missing)} ids not found in categories.json:")
        for m in missing:
            print(f"  - {m}")

    print(f"[ok] applied {len(applied)} fixes:")
    for iid, old, new in applied:
        print(f"  [{iid}]")
        print(f"    old: {old!r}")
        print(f"    new: {new!r}")

    # Write back. Preserve top-level shape (list-or-{categories: [...]}).
    SRC.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] wrote: {SRC}")
    print()
    print("Next: systemctl restart untitled-pick-game-api")


if __name__ == "__main__":
    main()
