"""Add dead items to the most logical archetype's triggers.

hollywood_actors_50plus:
  - dzhordzh-kluni (George Clooney)  → "Голливуд большого бюджета" (prestige mainstream A-list)
  - bred-pitt (Brad Pitt)            → "Голливуд большого бюджета" (same bucket)

your_2007:
  - nickelback                       → "Тяжёлый фронт" (post-grunge alt-rock heavyweights)
"""
import json, shutil
from datetime import datetime, timezone
from pathlib import Path

CATS = Path('/opt/untitled-pick-game-api/data/categories.json')

# (category_id, archetype_name) → list of item_ids to ADD to triggers
ADD = {
    ('hollywood_actors_50plus', 'Голливуд большого бюджета'): [
        'hollywood_actors_50plus-dzhordzh-kluni',
        'hollywood_actors_50plus-bred-pitt',
    ],
    ('your_2007', 'Тяжёлый фронт'): [
        'nickelback',
    ],
}

ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
shutil.copy2(CATS, CATS.with_name(f'categories.json.bak.dead_triggers.{ts}'))

raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw

added = 0
for (cid, arch_name), new_ids in ADD.items():
    cat = next((c for c in cats if c.get('id') == cid), None)
    if not cat:
        print(f'FAIL: category {cid} not found')
        continue
    arch = next((a for a in (cat.get('archetypes') or []) if a.get('name') == arch_name), None)
    if not arch:
        print(f'FAIL: archetype {arch_name!r} not in {cid}')
        continue
    triggers = list(arch.get('triggers') or [])
    for nid in new_ids:
        if nid not in triggers:
            triggers.append(nid)
            print(f'  added {nid} to {cid}/{arch_name!r}')
            added += 1
        else:
            print(f'  skip (already present): {nid} in {cid}/{arch_name!r}')
    arch['triggers'] = triggers

tmp = CATS.with_suffix('.json.tmp')
tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
tmp.replace(CATS)

print(f'\nTotal triggers added: {added}')
