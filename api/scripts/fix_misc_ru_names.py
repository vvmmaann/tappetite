"""Translate the most clearly out-of-place English item names to Russian.

Scope (per user decision — variant C, "minimum-decent"):
  - Dating apps         → Дейтинг-приложения
  - Local experience    → Локальный опыт
  - Mac & cheese        → Макароны с сыром
  - Audio rooms         → Аудио-комнаты

Everything else (Streetwear / Phonk / Quiet luxury / brand names) stays
because those terms are commonly used in Russian internet subculture
as-is, or are proper nouns.
"""
import json, shutil
from datetime import datetime, timezone
from pathlib import Path

CATS = Path('/opt/untitled-pick-game-api/data/categories.json')

# (category_id, item_id) → new Russian name
FIXES = {
    ('dating_2025', 'dating_2025-apps'): 'Дейтинг-приложения',
    ('traveler_type', 'traveler_type-local-experience'): 'Локальный опыт',
    ('comfort_food', 'comfort_food-mac-cheese'): 'Макароны с сыром',
    ('content_format_2020s', 'content_format_2020s-audio-rooms'): 'Аудио-комнаты',
}

ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
shutil.copy2(CATS, CATS.with_name(f'categories.json.bak.misc_ru.{ts}'))

raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw

patched = []
unmatched = []

for (cid, iid), new_name in FIXES.items():
    cat = next((c for c in cats if c.get('id') == cid), None)
    if not cat:
        unmatched.append(f'{cid} (category not found)')
        continue
    # Try strict id match first; fall back to name-substring match
    item = next((it for it in (cat.get('items') or []) if it.get('id') == iid), None)
    if not item:
        # Fallback: search by current English name in case the id slug differs
        en_target = {
            'dating_2025-apps': 'dating apps',
            'traveler_type-local-experience': 'local experience',
            'comfort_food-mac-cheese': 'mac & cheese',
            'content_format_2020s-audio-rooms': 'audio rooms',
        }[iid]
        item = next((it for it in (cat.get('items') or [])
                     if (it.get('name') or '').strip().lower() == en_target), None)
    if not item:
        unmatched.append(f'{cid}/{iid}')
        continue
    old = item.get('name')
    item['name'] = new_name
    patched.append(f'{cid}: {old!r} → {new_name!r}')

# Atomic write
tmp = CATS.with_suffix('.json.tmp')
tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
tmp.replace(CATS)

print(f'Patched: {len(patched)}/{len(FIXES)}')
for line in patched: print(' ', line)
if unmatched:
    print('Unmatched:')
    for u in unmatched: print(' ', u)
