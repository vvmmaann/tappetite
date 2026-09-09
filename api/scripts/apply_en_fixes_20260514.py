"""Apply 21 English-side fixes to /opt/untitled-pick-game-api/data/categories.json.

Mirror of yesterday's apply_ctx_fixes_20260513.py but for the *_en fields.
Three classes of fix:

1. biggest_future_fear ctx_en — 14 dev-placeholder English single-word labels
   ("burnout", "regret", "anhedonia"...) replaced with evocative phrases that
   parallel the new Russian ctx values applied yesterday.

2. Five awkward translations:
   - 2 archetype name_en using "Adept of" calque
   - 1 ctx_en where "Russian models" reads ambiguous
   - 1 ctx_en where "Russian and global" is oxymoronic
   - 1 archetype name_en where "Mainstream stan" is too vague

3. Two category-level blurb_en mini-fixes (anime_2000s_nostalgia,
   rodnye_00e) — vocabulary clean-up.

Run on server:
    cd /opt/untitled-pick-game-api
    python3 scripts/apply_en_fixes_20260514.py
    systemctl restart untitled-pick-game-api

Backs up the file with a timestamp suffix before writing.
"""
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = Path("/opt/untitled-pick-game-api/data/categories.json")

# ---- ITEM ctx_en (id -> new ctx_en) ----------------------------------------
ITEM_CTX_EN = {
    # biggest_future_fear — flat dev-placeholders → evocative phrases
    "biggest_future_fear-not-find-self":     "and never know who you are",
    "biggest_future_fear-no-money":          "and not know how you'll get by",
    "biggest_future_fear-lose-freedom":      "and live by someone else's rules",
    "biggest_future_fear-burn-out":          "burn down before you build anything",
    "biggest_future_fear-wrong-profession":  "and figure it out at 40",
    "biggest_future_fear-years-wasted":      "and realize too late",
    "biggest_future_fear-alone":             "with no one to call",
    "biggest_future_fear-disappoint-self":   "seeing yourself from the outside",
    "biggest_future_fear-family-expect":     '"we believed in you"',
    "biggest_future_fear-others-life":       "following someone else's script",
    "biggest_future_fear-not-realize":       "doors closing, you still inside",
    "biggest_future_fear-compare-others":    "and always come out short",
    "biggest_future_fear-lose-interest":     "nothing pulls you anymore",
    "biggest_future_fear-comfort-trap":      "afraid of any change",
    "biggest_future_fear-never-understand":  "right up to retirement",
    # Misc ctx_en fixes
    "ai_tool_2020s-yandex-giga":             "Russian-made models",
    "music_vibe_2020s-rap-global":           "Russian and Western",
}

# ---- ARCHETYPE name_en — keyed by (category_id, archetype RU name) --------
# Archetypes live in cat["archetypes"] (list of {name, name_en, body, body_en}).
# Match on RU `name` to find the right archetype within the category.
ARCH_NAME_EN = {
    ("hollywood_actresses_50plus", "Адепт серьёзной школы"): "Devotee of the serious school",
    ("supercars",                  "Адепт нестандартного"):  "Outlier devotee",
    ("kpop_boys",                  "Mainstream-стан"):       "Chart-topper stan",
}

# ---- CATEGORY blurb_en (cat_id -> new blurb_en) ----------------------------
CAT_BLURB_EN = {
    "anime_2000s_nostalgia": "The STS / 2x2 channel era",
    "rodnye_00e":            "Who defines your 2000s vibe?",
}


def main():
    if not SRC.exists():
        print(f"[err] not found: {SRC}", file=sys.stderr)
        sys.exit(1)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = SRC.with_suffix(f".json.bak.{ts}")
    shutil.copy2(SRC, backup)
    print(f"[ok] backup: {backup}")

    data = json.loads(SRC.read_text(encoding="utf-8"))
    cats = data if isinstance(data, list) else data.get("categories", [])

    items_applied = []
    items_missing = set(ITEM_CTX_EN)
    arch_applied  = []
    arch_missing  = set(ARCH_NAME_EN)
    blurb_applied = []
    blurb_missing = set(CAT_BLURB_EN)

    for cat in cats:
        cat_id = cat.get("id")

        # 1. Items
        for it in cat.get("items", []):
            iid = it.get("id")
            if iid in ITEM_CTX_EN:
                old = it.get("ctx_en", "")
                new = ITEM_CTX_EN[iid]
                it["ctx_en"] = new
                items_applied.append((iid, old, new))
                items_missing.discard(iid)

        # 2. Archetypes
        for arch in cat.get("archetypes", []) or []:
            arch_name_ru = arch.get("name", "")
            key = (cat_id, arch_name_ru)
            if key in ARCH_NAME_EN:
                old = arch.get("name_en", "")
                new = ARCH_NAME_EN[key]
                arch["name_en"] = new
                arch_applied.append((key, old, new))
                arch_missing.discard(key)

        # 3. Category-level blurb
        if cat_id in CAT_BLURB_EN:
            old = cat.get("blurb_en", "")
            new = CAT_BLURB_EN[cat_id]
            cat["blurb_en"] = new
            blurb_applied.append((cat_id, old, new))
            blurb_missing.discard(cat_id)

    # Report
    print(f"\n[items] applied {len(items_applied)}/{len(ITEM_CTX_EN)}:")
    for iid, old, new in items_applied:
        print(f"  [{iid}]")
        print(f"    old: {old!r}")
        print(f"    new: {new!r}")
    if items_missing:
        print(f"[items][warn] not found: {sorted(items_missing)}")

    print(f"\n[archetypes] applied {len(arch_applied)}/{len(ARCH_NAME_EN)}:")
    for (cid, arch_ru), old, new in arch_applied:
        print(f"  [{cid} / {arch_ru!r}]")
        print(f"    old: {old!r}")
        print(f"    new: {new!r}")
    if arch_missing:
        print(f"[archetypes][warn] not found: {sorted(arch_missing)}")

    print(f"\n[blurbs] applied {len(blurb_applied)}/{len(CAT_BLURB_EN)}:")
    for cid, old, new in blurb_applied:
        print(f"  [{cid}]")
        print(f"    old: {old!r}")
        print(f"    new: {new!r}")
    if blurb_missing:
        print(f"[blurbs][warn] not found: {sorted(blurb_missing)}")

    total = len(items_applied) + len(arch_applied) + len(blurb_applied)
    print(f"\n[ok] {total} total fixes applied")

    SRC.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[ok] wrote: {SRC}")
    print("\nNext: systemctl restart untitled-pick-game-api")


if __name__ == "__main__":
    main()
