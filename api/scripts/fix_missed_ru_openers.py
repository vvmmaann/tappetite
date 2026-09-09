"""Surgical fix for 14 RU archetype openers that were missed by the chunker
detector (because items in their categories are stored only in English, so
cross-reference between RU body tokens and item names didn't match).

Manually-written replacements following H2 rules: 120-180 chars, no item names,
opener varies (scene / antithesis / paradox / sensory / direct-speech).
"""
import io, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

CATS = Path(sys.argv[1] if len(sys.argv) > 1 else '/opt/untitled-pick-game-api/data/categories.json')

# (category_id, archetype_name, new_p1_ru)
FIXES = [
    ('comeback_games', 'Открытый мир',
     'Главный квест может подождать — впереди дорога уходит налево, и тебе важно знать куда. Тебе нравятся игры, в которых сюжет — лишь одна линия, а вокруг неё целая жизнь.'),
    ('your_2007_rap_hiphop', 'Мейнстрим-эпоха',
     'В 2007 рэп вышел из андеграунда и стал главной музыкой эпохи. Тебе нравилось, что мейнстрим тогда был хорошим — и не приходилось стыдиться этого выбора.'),
    ('mood_artist', 'Поп-универсалы',
     'В наушниках, в супермаркете, на свадьбе — один и тот же припев работает везде. Тебе по душе поп-универсалы: общая валюта музыки, звук который понимают все.'),
    ('your_real_profession', 'Tech-делатель',
     'Ты не «обслуживаешь IT» — ты строишь продукт. Продуктовая технологическая команда: твой режим, где результат можно показать пальцем и пощупать.'),
    ('your_real_profession', 'Креатив-делатель',
     'Ты создаёшь то, что видят люди. Визуальный креатив — твой режим: каждое решение в кадре, композиции и монтаже становится частью разговора.'),
    ('your_real_profession', 'Творческий нарратор',
     'Ты творец смысла. Не «делаешь продукт» — создаёшь произведение: текст, песню, картину, материал. Главный твой инструмент — собственный голос.'),
    ('your_real_profession', 'Цифры и стратегия',
     'Анализ, фреймворки, рекомендации — это твой инструментарий. Ты работаешь с цифрами и стратегиями: смотришь на данные и видишь куда двигаться дальше.'),
    ('your_real_profession', 'Старт и риск',
     'Тебе нужен риск как часть профессии. Не «стабильная зарплата с понятным потолком», а большой потенциал и большая возможность провала — один на один с неопределённостью.'),
    ('your_real_profession', 'Помощь людям',
     'Твоя работа — это люди и их состояния. Ты в помогающей профессии: смотришь на конкретного человека и думаешь, как ему станет лучше.'),
    ('your_real_profession', 'Точная инженерия',
     'В твоей профессии нет «приблизительно» — есть «правильно» и «неправильно». Точность здесь не стиль, а условие; ошибка стоит дорого, и ты это уважаешь.'),
    ('your_real_profession', 'Слова и убеждение',
     'Твой инструмент — слово. Ты убеждаешь, продаёшь, защищаешь, объясняешь. Без правильно сказанной фразы ничего не двигается, и ты это умеешь.'),
    ('your_real_profession', 'Особый артистизм',
     'Ты творишь не словами и не кодом — другим материалом. Едой, звуком, краской, светом: это сложнее объяснить, но узнаётся сразу.'),
    ('your_real_profession', 'Мост культур',
     'Ты работаешь между мирами. Между языками, между странами, между разными аудиториями — переводишь не только слова, но и контексты.'),
    ('your_real_profession', 'Спорт и тело',
     'Твоя профессия требует физической формы. Не «офисная работа» с креслом и кофе — а активная, на ногах, с реальной нагрузкой и реальными последствиями.'),
]


def replace_first_paragraph(body, new_p1):
    if not body or not new_p1: return new_p1 or body
    if '\n\n' in body: return new_p1 + '\n\n' + body.split('\n\n', 1)[1]
    if '\n' in body: return new_p1 + '\n' + body.split('\n', 1)[1]
    return new_p1


# ─── Backup + load ───
ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
bak = CATS.with_name(f'{CATS.name}.bak.fix_missed_ru.{ts}')
shutil.copy2(CATS, bak)
print(f'Backup: {bak}')

raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw
by_id = {c['id']: c for c in cats}

# ─── Apply ───
applied = 0; not_found = []
for cat_id, arch_name, new_p1 in FIXES:
    cat = by_id.get(cat_id)
    if not cat:
        not_found.append(f'category {cat_id}'); continue
    arch = next((a for a in (cat.get('archetypes') or []) if a['name'] == arch_name), None)
    if not arch:
        not_found.append(f'archetype {cat_id}::{arch_name}'); continue
    # Length sanity check
    if not (80 <= len(new_p1) <= 220):
        print(f'  ⚠ {cat_id}::{arch_name}: new p1 length {len(new_p1)} out of 80-220, skipping')
        continue
    arch['body'] = replace_first_paragraph(arch.get('body', ''), new_p1)
    applied += 1
    print(f'  ✓ {cat_id} / «{arch_name}» — {len(new_p1)}c')

if not_found:
    print()
    for nf in not_found: print(f'  ✗ not found: {nf}')

# ─── Atomic write ───
tmp = CATS.with_suffix('.json.tmp')
tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
tmp.replace(CATS)
print()
print(f'Applied: {applied} / {len(FIXES)}')
print(f'Output: {CATS}')
