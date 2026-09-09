"""Patch name_the_game items: brand candidates keep their names but get ctx_en."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

# Brand-candidate names stay the same; we just translate the ctx (which describes
# the etymology/feel of the candidate name).
ITEMS_EN = {
    "choix":        ("Choix",        "French for 'choice' · short"),
    "oneout":       ("Oneout",       "one out of many · concise"),
    "favora":       ("Favora",       "from 'favorite' · brand-friendly"),
    "ranko":        ("Ranko",        "from 'rank' · playful ending"),
    "verto":        ("Verto",        "Latin for 'turn' · unusual"),
    "tastecut":     ("Tastecut",     "taste + cut · sharp"),
    "duelist":      ("Duelist",      "duelist · tournament feel"),
    "the_pick":     ("The Pick",     "the pick · with the · brand-feel"),
    "only_one":     ("Only One",     "the only one · emotional"),
    "hard_pick":    ("Hard Pick",    "a hard pick · spot-on for the game"),
    "finalist":     ("Finalist",     "finalist · tournament outcome"),
    "bracket":      ("Bracket",      "tournament bracket · technical"),
    "topline":      ("Topline",      "top one · newspaper term"),
    "pick_one":     ("Pick One",     "pick one · literal"),
    "taste_check":  ("Taste Check",  "checking taste · functional"),
    "final_taste":  ("Final Taste",  "the final taste · the result"),
    "preference":   ("Preference",   "preference · academic"),
    "pairwise":     ("Pairwise",     "pair by pair · technical"),
    "tastefight":   ("Tastefight",   "battle of tastes · energetic"),
    "rankline":     ("Rankline",     "ranking line · sporty"),
    "one_wins":     ("One Wins",     "one wins · tournament"),
    "last_pick":    ("Last Pick",    "the last pick · mysterious"),
    "true_pick":    ("True Pick",    "the true pick · confident"),
    "best_of":      ("Best Of",      "best of · the classic"),
    "the_final":    ("The Final",    "the final · brand-feel"),
    "vibe_pick":    ("Vibe Pick",    "pick by vibe · modern"),
    "hot_pick":     ("Hot Pick",     "the hot pick · TikTok-friendly"),
    "no_mid":       ("No Mid",       "no mediocrity · Gen-Z slang"),
    "top_three":    ("Top Three",    "top three · clear"),
    "inner_rank":   ("Inner Rank",   "inner ranking · personal"),
    "pickwise":     ("Pickwise",     "the wise pick · elegant"),
    "taste_duel":   ("Taste Duel",   "duel of tastes · tournament"),
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    target = next((c for c in raw if c.get("id") == "name_the_game"), None)
    if not target:
        print("ERROR: name_the_game not found")
        return 1
    n = 0
    for it in target.get("items", []):
        iid = it.get("id")
        if iid in ITEMS_EN:
            it["name_en"], it["ctx_en"] = ITEMS_EN[iid]; n += 1
    print(f"Patched {n}/{len(target.get('items', []))} items")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.ntg_items.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
