"""Replace 'apple' item in brand_reflects_style category with Maison Margiela.

Reason: tester (user) flagged that brand_reflects_style category was 15
clothing/fashion brands + Apple — visually inconsistent. Apple was the only
non-apparel item. It was originally placed there because Apple's industrial-
design ethos fits the "Детали решают" archetype (engineering hidden in a
detail), alongside Stone Island. We replace it with Maison Margiela, which
keeps the SAME archetype intent (craft-detail focus: tabi split-toe, white
numbered labels, replica project) but stays squarely in the fashion lane.

Changes:
1. Items: replace `apple` with `maison-margiela` (new id + bilingual name/ctx).
2. Archetype "Детали решают": update triggers `['apple', 'stone-island']` →
   `['maison-margiela', 'stone-island']`.
3. Archetype "Детали решают" body п1 (RU + EN): remove the
   "phone chamfer" sentence that specifically referenced Apple. Replace
   with a clothing-craft analogue so the narrative stays cohesive with
   the now-all-fashion item set.

Run on server:
    cd /opt/untitled-pick-game-api
    python3 scripts/fix_brand_apple_to_margiela_20260516.py
    systemctl restart untitled-pick-game-api

Backs up categories.json with a UTC timestamp before writing.
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
CATEGORY_ID = "brand_reflects_style"
OLD_ITEM_ID = "apple"
NEW_ITEM_ID = "maison-margiela"
ARCH_NAME = "Детали решают"

NEW_ITEM = {
    "id": NEW_ITEM_ID,
    "name": "Maison Margiela",
    "name_en": "Maison Margiela",
    "ctx": "Анверс шестёрка · табы · белые ярлыки · реплики",
    "ctx_en": "Antwerp Six · tabi · white labels · replica project",
}

# New п1 for "Детали решают" — drops the phone-specific reference, keeps
# the Stone Island compass-badge example, adds a Margiela tabi-split-toe
# example. Generic-enough that the archetype works even if a future cluster
# update changes triggers.
NEW_P1_RU = (
    "Компас на рукаве, который можно снять и постирать отдельно. "
    "Раздвоенный носок ботинка, который ложится по анатомии стопы точнее, чем обычный закруглённый. "
    "Ты замечаешь такие вещи — и именно они определяют твой выбор, не название на этикетке."
)
NEW_P1_EN = (
    "A compass badge on the sleeve that detaches for washing separately. "
    "A split-toe boot that follows the actual anatomy of your foot more precisely than a rounded one. "
    "You notice things like this — and they determine your choice, not the name on the label."
)


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

    cat = next((c for c in cats if c.get("id") == CATEGORY_ID), None)
    if not cat:
        print(f"[err] category '{CATEGORY_ID}' not found", file=sys.stderr)
        sys.exit(1)

    # 1. Replace the item
    items = cat.get("items", [])
    idx = next((i for i, it in enumerate(items) if it.get("id") == OLD_ITEM_ID), None)
    if idx is None:
        print(f"[err] item '{OLD_ITEM_ID}' not found in '{CATEGORY_ID}'", file=sys.stderr)
        sys.exit(1)
    old_item = items[idx]
    items[idx] = NEW_ITEM
    print(f"[ok] item replaced: {old_item.get('name')} → {NEW_ITEM['name']}")
    print(f"    old id: {OLD_ITEM_ID!r} → new id: {NEW_ITEM_ID!r}")

    # 2. Update archetype triggers
    arch = next((a for a in (cat.get("archetypes") or []) if a.get("name") == ARCH_NAME), None)
    if not arch:
        print(f"[err] archetype '{ARCH_NAME}' not found", file=sys.stderr)
        sys.exit(1)
    old_triggers = list(arch.get("triggers") or [])
    new_triggers = [NEW_ITEM_ID if t == OLD_ITEM_ID else t for t in old_triggers]
    arch["triggers"] = new_triggers
    print(f"[ok] archetype '{ARCH_NAME}' triggers: {old_triggers} → {new_triggers}")

    # 3. Update archetype п1 body (RU + EN)
    body_ru = arch.get("body", "") or ""
    body_en = arch.get("body_en", "") or ""
    paras_ru = body_ru.split("\n\n")
    paras_en = body_en.split("\n\n")
    if paras_ru:
        old_p1_ru = paras_ru[0]
        paras_ru[0] = NEW_P1_RU
        arch["body"] = "\n\n".join(paras_ru)
        print(f"[ok] RU п1 replaced:")
        print(f"    old: {old_p1_ru[:120]}…")
        print(f"    new: {NEW_P1_RU[:120]}…")
    if paras_en:
        old_p1_en = paras_en[0]
        paras_en[0] = NEW_P1_EN
        arch["body_en"] = "\n\n".join(paras_en)
        print(f"[ok] EN п1 replaced:")
        print(f"    old: {old_p1_en[:120]}…")
        print(f"    new: {NEW_P1_EN[:120]}…")

    SRC.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[ok] wrote: {SRC}")
    print("Next: systemctl restart untitled-pick-game-api")


if __name__ == "__main__":
    main()
