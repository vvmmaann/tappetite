"""Archetype EN backfill — batch 5: ideal_vacation (1 cat, 6 archetypes — short bodies)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "ideal_vacation": {
        "Адреналин и движение": ("Adrenaline and motion",
            "A vacation without physical exertion isn't a vacation to you. The goal — to have your legs ache pleasantly by the end of the day."),
        "Тёплая вода и лень": ("Warm water and lounging",
            "You've earned the quiet. A sun lounger, a cocktail, and no itineraries — that's your medical norm."),
        "Городской культурный": ("Urban-cultural",
            "You love a packed program: gallery, wine, a dinner that has a name. Vacation as a lecture course."),
        "Тишина и восстановление": ("Silence and reset",
            "You need to reflash your head. The point — drop out of schedules and hear your own brain at least once."),
        "Друзья и природа": ("Friends and nature",
            "The best vacation is people you chose and a place without signal. Bonfire and silence do the rest."),
        "_default": ("Universal vacationer",
            "You don't have one mode — each vacation you assemble for the current state of your life."),
    },
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats_by_id = {c.get("id"): c for c in raw}
    arch_done, arch_skip, arch_missing = 0, 0, 0
    for cat_id, tr in T.items():
        cat = cats_by_id.get(cat_id)
        if cat is None: print(f"  [skip] cat {cat_id}"); continue
        for a in cat.get("archetypes", []):
            ru = a.get("name"); pair = tr.get(ru)
            if not pair: arch_missing += 1; print(f"    [warn] {cat_id}/{ru!r}"); continue
            if a.get("body_en") and a.get("name_en"): arch_skip += 1; continue
            a["name_en"], a["body_en"] = pair; arch_done += 1
        da = cat.get("defaultArchetype")
        if da:
            pair = tr.get("_default")
            if pair:
                if not (da.get("body_en") and da.get("name_en")):
                    da["name_en"], da["body_en"] = pair; arch_done += 1
                else: arch_skip += 1
        print(f"  ✓ {cat_id}")
    print(f"\nArchetypes: done={arch_done}, missing={arch_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch5.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
