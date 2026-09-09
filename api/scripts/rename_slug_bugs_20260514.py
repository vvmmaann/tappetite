"""Rename two stale-slug items + their archetype trigger references.

Background: id was set when the slot held one piece of content; later the
content was replaced but the id stayed. Result: cosmetic mismatch in code/
analytics/logs. User-facing UI is unaffected (slug isn't displayed).

Item-level renames:
    actors_without_oscar:
        item id  joaquin-phoenix-pre  →  josh-brolin
        (content: Josh Brolin, "No Country for Old Men · Mystic River · no Oscar")
    rodnye_00e:
        item id  t_killah  →  timati
        (content: Тимати, "звёздный пафос · Не сходи с ума · В клубе")

Side effects handled:
- archetype triggers arrays in the SAME category are rewritten so the matcher
  keeps finding the renamed item.

Side effects NOT handled by this script (separate companion SQL migration):
- the API server's results table stores top1_id/top2_id/top3_id values; any
  saved historic result that referenced the old slug needs a one-shot UPDATE.
  See companion SQL run-from-server in the deploy block below.

Run on server:
    cd /opt/untitled-pick-game-api
    python3 scripts/rename_slug_bugs_20260514.py
    # then companion SQL migration on results.db (see deploy script)
    systemctl restart untitled-pick-game-api
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

RENAMES = [
    # (cat_id, old_item_id, new_item_id)
    ("actors_without_oscar", "joaquin-phoenix-pre", "josh-brolin"),
    ("rodnye_00e",           "t_killah",            "timati"),
]


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

    for cat_id, old_id, new_id in RENAMES:
        cat = next((c for c in cats if c.get("id") == cat_id), None)
        if not cat:
            print(f"[err] category {cat_id!r} not found", file=sys.stderr)
            continue

        # Sanity: old must exist, new must not exist (in this same category)
        items = cat.get("items", [])
        old_item = next((it for it in items if it.get("id") == old_id), None)
        new_collide = next((it for it in items if it.get("id") == new_id), None)
        if not old_item:
            print(f"[err] {cat_id}: item id {old_id!r} not found — skipping")
            continue
        if new_collide:
            print(f"[err] {cat_id}: item id {new_id!r} ALREADY EXISTS — would collide. Skipping.")
            continue

        # Rename item id
        old_item["id"] = new_id

        # Rewrite trigger refs in archetypes of THIS category
        rewrites = 0
        for arch in cat.get("archetypes", []) or []:
            triggers = arch.get("triggers", [])
            if old_id in triggers:
                arch["triggers"] = [new_id if t == old_id else t for t in triggers]
                rewrites += 1

        # Default archetype rarely has triggers, but check anyway
        da = cat.get("defaultArchetype", {})
        if isinstance(da, dict) and old_id in (da.get("triggers") or []):
            da["triggers"] = [new_id if t == old_id else t for t in da["triggers"]]
            rewrites += 1

        print(f"[ok] {cat_id}: {old_id} → {new_id}  (item renamed, {rewrites} archetype trigger refs updated)")
        print(f"     content: name={old_item.get('name')!r}, name_en={old_item.get('name_en')!r}")

    SRC.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[ok] wrote: {SRC}")
    print()
    print("Companion SQL migration (run separately):")
    print("  sqlite3 /opt/untitled-pick-game-api/data/app.db <<'SQL'")
    print("  UPDATE results SET top1_id='josh-brolin' WHERE category_id='actors_without_oscar' AND top1_id='joaquin-phoenix-pre';")
    print("  UPDATE results SET top2_id='josh-brolin' WHERE category_id='actors_without_oscar' AND top2_id='joaquin-phoenix-pre';")
    print("  UPDATE results SET top3_id='josh-brolin' WHERE category_id='actors_without_oscar' AND top3_id='joaquin-phoenix-pre';")
    print("  UPDATE results SET top1_id='timati'      WHERE category_id='rodnye_00e'           AND top1_id='t_killah';")
    print("  UPDATE results SET top2_id='timati'      WHERE category_id='rodnye_00e'           AND top2_id='t_killah';")
    print("  UPDATE results SET top3_id='timati'      WHERE category_id='rodnye_00e'           AND top3_id='t_killah';")
    print("  SQL")
    print("Then: systemctl restart untitled-pick-game-api")


if __name__ == "__main__":
    main()
