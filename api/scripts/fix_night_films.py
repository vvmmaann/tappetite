"""Surgically fix night_films archetypes per T1-T6:
  - Trim 3 magnet archetypes (Сюжет-головоломка 10→5, Холодный сай-фай 10→5, Тёмная психология 8→4)
  - Move displaced items to other existing archetypes (no orphans)
  - Rewrite p1 of 3 affected archetype bodies (RU + EN where opener mentions removed films)

Run on server. Backup written before edit.
"""
import io
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 stdout (Windows cp1251 default mangles Cyrillic + arrows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# Local test path or prod path — passed as arg
CATS = Path(sys.argv[1] if len(sys.argv) > 1 else '/opt/untitled-pick-game-api/data/categories.json')


def find_item_id(items, name):
    """Find item id by exact Russian name. Raises if not found."""
    for it in items:
        if it.get('name') == name:
            return it['id']
    raise ValueError(f'item not found: {name}')


def find_arch(archs, name):
    """Find archetype by name. Raises if not found."""
    for a in archs:
        if a.get('name') == name:
            return a
    raise ValueError(f'archetype not found: {name}')


def main():
    ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    bak = CATS.with_name(f'{CATS.name}.bak.night_films.{ts}')
    shutil.copy2(CATS, bak)
    print(f'Backup: {bak}')

    raw = json.loads(CATS.read_text(encoding='utf-8'))
    cats = raw.get('categories') if isinstance(raw, dict) else raw
    nf = next(c for c in cats if c['id'] == 'night_films')
    items = nf['items']
    archs = nf['archetypes']

    # === Build name → id map for clarity ===
    R = lambda name: find_item_id(items, name)
    A = lambda name: find_arch(archs, name)

    # Verify all needed items exist
    needed_names = [
        'Мементо', 'Начало', 'Шестое чувство', 'Шоу Трумана', 'Престиж',
        'Исчезновение', 'Вечное сияние чистого разума', 'Криминальное чтиво', 'Прочь', 'Подозрительные лица',
        'Прибытие', 'Экс Машина', 'Бегущий по лезвию 2049', 'Солярис', 'Аннигиляция',
        'Маяк', 'Под кожей', 'Лобстер', 'Матрица', 'Чужой',
        'Бойцовский клуб', 'Чёрный лебедь', 'Джокер', 'Таксист', 'Семь', 'Сияние', 'Тёмный рыцарь',
        'Олдбой',
    ]
    name_to_id = {}
    for n in needed_names:
        try:
            name_to_id[n] = R(n)
        except ValueError as e:
            print(f'  WARN: {e}')
            return

    print(f'  All {len(name_to_id)} needed items found.')

    # === Edit 1: Сюжет-головоломка trim 10 → 5 ===
    a = A('Сюжет-головоломка')
    a['triggers'] = [name_to_id[n] for n in ['Мементо', 'Начало', 'Шестое чувство', 'Шоу Трумана', 'Престиж']]
    # Rewrite p1 RU
    parts_ru = a['body'].split('\n\n')
    parts_ru[0] = 'Мементо, Начало, Шестое чувство, Шоу Трумана, Престиж. Тебе нужно, чтобы фильм заставлял думать в реальном времени. Хронология ломается, реальность многослойна, и в финале всё (или ничего) сходится.'
    a['body'] = '\n\n'.join(parts_ru)
    # Rewrite p1 EN — only if EN has the gone-girl mention
    parts_en = a['body_en'].split('\n\n')
    parts_en[0] = 'What grabs you isn\'t "who did it" but "how is the film structured". "Memento" runs backward; "Inception" stacks layers within layers; "The Sixth Sense" waits till the final shot to recontextualize every frame before it. You watch as much for construction as for character — and you\'re often the one who notices the trick a beat before everyone else.'
    a['body_en'] = '\n\n'.join(parts_en)
    print(f'  [1] Сюжет-головоломка: trimmed to {len(a["triggers"])}')

    # === Edit 2: Слой за слоем + Подозрительные лица ===
    a = A('Слой за слоем')
    sus_id = name_to_id['Подозрительные лица']
    if sus_id not in a['triggers']:
        a['triggers'].append(sus_id)
    print(f'  [2] Слой за слоем: now {len(a["triggers"])} triggers')

    # === Edit 3: Холодный сай-фай trim 10 → 5 ===
    a = A('Холодный сай-фай')
    a['triggers'] = [name_to_id[n] for n in ['Прибытие', 'Экс Машина', 'Бегущий по лезвию 2049', 'Солярис', 'Аннигиляция']]
    # RU p1 mentioned Маяк — rewrite
    parts_ru = a['body'].split('\n\n')
    parts_ru[0] = 'Прибытие, Экс Машина, Бегущий по лезвию 2049, Солярис, Аннигиляция. Тебе нравится умное и атмосферное кино, в котором фантастика — это не спецэффекты, а философский эксперимент.'
    a['body'] = '\n\n'.join(parts_ru)
    # EN p1 already mentions only Arrival/Ex Machina/Annihilation (all kept) — leave alone
    print(f'  [3] Холодный сай-фай: trimmed to {len(a["triggers"])}')

    # === Edit 4: Артхаус с шоком — swap Олдбой → Лобстер ===
    a = A('Артхаус с шоком')
    a['triggers'] = [t for t in a['triggers'] if t != name_to_id['Олдбой']]
    if name_to_id['Лобстер'] not in a['triggers']:
        a['triggers'].append(name_to_id['Лобстер'])
    print(f'  [4] Артхаус с шоком: now {len(a["triggers"])} triggers (swapped Олдбой → Лобстер)')

    # === Edit 5: Тёмная психология trim 8 → 4 ===
    a = A('Тёмная психология')
    a['triggers'] = [name_to_id[n] for n in ['Джокер', 'Таксист', 'Тёмный рыцарь', 'Семь']]
    parts_ru = a['body'].split('\n\n')
    parts_ru[0] = 'Джокер, Таксист, Тёмный рыцарь, Семь. Ты любишь фильмы, которые лезут в голову. Не «история» — а «состояние». Где главный герой постепенно теряет/находит себя, и ты вместе с ним.'
    a['body'] = '\n\n'.join(parts_ru)
    parts_en = a['body_en'].split('\n\n')
    parts_en[0] = 'You\'re drawn to films that climb inside the broken parts of a mind. Not the violence itself but the structure underneath it: how someone arrives at the place they end up. Travis Bickle in his cab; the late-stage Joker; the doomsday detective in "Se7en"; the moral grey of "The Dark Knight". You want to understand the wiring.'
    a['body_en'] = '\n\n'.join(parts_en)
    print(f'  [5] Тёмная психология: trimmed to {len(a["triggers"])}')

    # === Edit 6: Психологический ужас + Сияние ===
    a = A('Психологический ужас')
    sh_id = name_to_id['Сияние']
    if sh_id not in a['triggers']:
        a['triggers'].append(sh_id)
    print(f'  [6] Психологический ужас: now {len(a["triggers"])} triggers')

    # === Edit 7: Тревога и крах — Джокер removed ===
    a = A('Тревога и крах')
    j_id = name_to_id['Джокер']
    a['triggers'] = [t for t in a['triggers'] if t != j_id]
    print(f'  [7] Тревога и крах: now {len(a["triggers"])} triggers (Джокер removed)')

    # === Write atomically ===
    tmp = CATS.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(CATS)
    print(f'\nWrote: {CATS}')


if __name__ == '__main__':
    main()
