"""Fix your_real_profession items: name field had English; rewrite to Russian."""
import json, shutil
from datetime import datetime, timezone
from pathlib import Path

CATS = Path('/opt/untitled-pick-game-api/data/categories.json')

# id → Russian name. EN stays as it is.
RU = {
    'your_real_profession-pm':           'Продакт-менеджер',
    'your_real_profession-dev':          'Разработчик',
    'your_real_profession-ux':           'UX-дизайнер',
    'your_real_profession-graphic':      'Графический дизайнер',
    'your_real_profession-creator':      'Контент-креатор',
    'your_real_profession-marketing':    'Маркетолог',
    'your_real_profession-analyst':      'Аналитик данных',
    'your_real_profession-founder':      'Основатель · предприниматель',
    'your_real_profession-teacher':      'Преподаватель · тьютор',
    'your_real_profession-engineer':     'Инженер',
    'your_real_profession-doctor':       'Врач',
    'your_real_profession-therapist':    'Психотерапевт · психолог',
    'your_real_profession-lawyer':       'Юрист',
    'your_real_profession-journalist':   'Журналист',
    'your_real_profession-filmmaker':    'Режиссёр',
    'your_real_profession-photographer': 'Фотограф',
    'your_real_profession-musician':     'Музыкант · композитор',
    'your_real_profession-writer':       'Писатель',
    'your_real_profession-chef':         'Шеф-повар',
    'your_real_profession-architect':    'Архитектор',
    'your_real_profession-scientist':    'Учёный · исследователь',
    'your_real_profession-artist':       'Художник',
    'your_real_profession-athlete':      'Спортсмен · тренер',
    'your_real_profession-banker':       'Инвестбанкир',
    'your_real_profession-consultant':   'Консультант',
    'your_real_profession-sales':        'Менеджер по продажам',
    'your_real_profession-pr':           'PR-специалист',
    'your_real_profession-hr':           'HR-специалист',
    'your_real_profession-translator':   'Переводчик · лингвист',
    'your_real_profession-pilot':        'Пилот',
    'your_real_profession-diplomat':     'Дипломат',
    'your_real_profession-game-dev':     'Геймдев',
}

# Backup
ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
shutil.copy2(CATS, CATS.with_name(f'categories.json.bak.profession_ru.{ts}'))

raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw

cat = next((c for c in cats if c.get('id') == 'your_real_profession'), None)
if not cat:
    print('FAIL: category not found')
    raise SystemExit(1)

# Match by id when possible; fall back to fuzzy match on existing name
patched = 0
unmatched = []
for it in (cat.get('items') or []):
    iid = it.get('id')
    if iid in RU:
        it['name'] = RU[iid]
        patched += 1
    else:
        unmatched.append((iid, it.get('name')))

# Atomic write
tmp = CATS.with_suffix('.json.tmp')
tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
tmp.replace(CATS)

print(f'Patched: {patched}/{len(cat.get("items") or [])}')
if unmatched:
    print('Unmatched:')
    for iid, nm in unmatched:
        print(f'  id={iid!r}  name={nm!r}')
