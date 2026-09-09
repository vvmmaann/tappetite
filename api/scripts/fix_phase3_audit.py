"""Phase 3 audit fixes: 8 surgical category corrections.

Per audit findings:
  - 4 categories with T3 trigger-length violations
  - 4 categories with T4 overlap >50% (mostly identical-twin archetypes)

After applying, runs internal T1-T4 validation. If new violations appear,
aborts with rollback (backup is left in place).
"""
import io, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

CATS = Path(sys.argv[1] if len(sys.argv) > 1 else '/opt/untitled-pick-game-api/data/categories.json')

ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
bak = CATS.with_name(f'{CATS.name}.bak.phase3_audit.{ts}')
shutil.copy2(CATS, bak)
print(f'Backup: {bak}')

raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw
def get(cid): return next(c for c in cats if c['id'] == cid)
def find_arch(cat, name): return next(a for a in cat['archetypes'] if a['name'] == name)
def find_item_id(cat, name): return next(it['id'] for it in cat['items'] if it['name'] == name)
def del_arch(cat, name):
    cat['archetypes'] = [a for a in cat['archetypes'] if a['name'] != name]


def violation_counts(cat):
    """Return dict with counts of T1/T2/T3/T4 violations in a category."""
    items = cat.get('items') or []
    archs = cat.get('archetypes') or []
    item_ids = [it['id'] for it in items]
    appearance = {iid: 0 for iid in item_ids}
    for a in archs:
        for t in (a.get('triggers') or []):
            appearance[t] = appearance.get(t, 0) + 1
    dead = sum(1 for iid in item_ids if appearance.get(iid, 0) == 0)
    over = sum(1 for c in appearance.values() if c >= 3)
    bad_t3 = sum(1 for a in archs if not (2 <= len(a.get('triggers') or []) <= 5))
    bad_overlap = 0
    for i, a in enumerate(archs):
        for b in archs[i+1:]:
            sa, sb = set(a.get('triggers') or []), set(b.get('triggers') or [])
            if not sa or not sb: continue
            common = sa & sb
            denom = min(len(sa), len(sb))
            ratio = len(common) / denom if denom else 0
            if ratio > 0.5: bad_overlap += 1
    return {'T1_dead': dead, 'T2_over': over, 'T3_bad': bad_t3, 'T4_overlap': bad_overlap}


# Capture baseline BEFORE any fix runs — so we only block if my changes
# introduce NEW violations. Pre-existing issues in untouched archetypes pass.
TOUCHED = ['hollywood_actors_50plus', 'supercars', 'ideal_vacation', 'ideal_city',
           'your_sport', 'ideal_evening', 'your_mood_color', 'your_background']
baseline = {cid: violation_counts(get(cid)) for cid in TOUCHED}

print()
print('=== FIX 1: hollywood_actors_50plus / Голливуд большого бюджета 6t→5t (move Костнер→Маскулинная классика) ===')
c = get('hollywood_actors_50plus')
big = find_arch(c, 'Голливуд большого бюджета')
masc = find_arch(c, 'Маскулинная классика')
kostner_id = find_item_id(c, 'Кевин Костнер')
big['triggers'] = [t for t in big['triggers'] if t != kostner_id]
if kostner_id not in masc['triggers']:
    masc['triggers'].append(kostner_id)
print(f'  «Голливуд большого бюджета» now {len(big["triggers"])}t')
print(f'  «Маскулинная классика» now {len(masc["triggers"])}t (Костнер re-homed there — Westerns / Yellowstone fit)')

print()
print('=== FIX 2: supercars / Перфекционист гипер-класса 1t→2t (add Pagani Huayra) ===')
c = get('supercars')
a = find_arch(c, 'Перфекционист гипер-класса')
pagani_id = find_item_id(c, 'Pagani Huayra')
if pagani_id not in a['triggers']:
    a['triggers'].append(pagani_id)
print(f'  triggers now: {len(a["triggers"])}')

print()
print('=== FIX 3: ideal_vacation / Друзья и природа 1t→2t (add Сёрф-кемп) ===')
c = get('ideal_vacation')
a = find_arch(c, 'Друзья и природа')
surf_id = find_item_id(c, 'Сёрф-кемп')
if surf_id not in a['triggers']:
    a['triggers'].append(surf_id)
print(f'  triggers now: {len(a["triggers"])}')

print()
print('=== FIX 4: ideal_city / split «Европейский урбанист» 10t into 2×5t archetypes ===')
c = get('ideal_city')
old = find_arch(c, 'Европейский урбанист')
nordic_names = ['Копенгаген', 'Стокгольм', 'Хельсинки', 'Осло', 'Амстердам']
mitteleuropa_names = ['Берлин', 'Вена', 'Прага', 'Варшава', 'Будапешт']
nordic_ids = [find_item_id(c, n) for n in nordic_names]
mitteleuropa_ids = [find_item_id(c, n) for n in mitteleuropa_names]
del_arch(c, 'Европейский урбанист')

c['archetypes'].append({
    'name': 'Северо-европейский эколог',
    'name_en': 'Northern-European ecologist',
    'body': (
        'Чистый воздух, велосипедные дорожки, кафе с книгой на столе. Тебя тянет в города где жизнь течёт ровно — без крика, без show-off, с уважением к тишине. Дизайн спокойный, природа в шаге от центра, социальная система не давит.\n\n'
        'Это работает потому что ты понимаешь — настоящее качество жизни не в роскоши, а в инфраструктуре. Где можно дойти пешком до моря, до парка, до работы. Где обсуждение климата это не модa, а здравый смысл. Тебе важна цельность среды.\n\n'
        'Окружающие иногда называют это «скучным» — мол, нет драмы, нет страсти. Ты не споришь, но видишь по-другому: то что они называют скучным, ты называешь «здоровым». Драма исчерпаема, ровность — нет.\n\n'
        'Что стоит знать: эти города работают только если ты понимаешь язык или готов учить. Иначе остаёшься в expat-пузыре и не доходишь до настоящей жизни. Готовься: первый год везде такой же сложный, и в Копенгагене, и в Стокгольме. Награда — за два-три года.'
    ),
    'body_en': (
        "Clean air, bike lanes, coffee shops where you can sit with a book. You're drawn to cities where life flows evenly — no shouting, no show-off, deep respect for quiet. Design is calm, nature is a step from the center, the social system doesn't crush you.\n"
        "This works because you understand that real quality of life isn't luxury — it's infrastructure. Where you can walk to the sea, to the park, to work. Where climate discussions aren't a trend but common sense. You value the wholeness of the environment.\n"
        "Other people sometimes call it 'boring' — no drama, no passion. You don't argue but see it differently: what they call boring, you call 'healthy'. Drama runs out; evenness doesn't.\n"
        "What's worth knowing: these cities only work if you understand the language or are willing to learn. Otherwise you stay in the expat bubble and never reach real life. Prepare: the first year is hard everywhere — Copenhagen, Stockholm alike. The reward comes after two or three years."
    ),
    'triggers': nordic_ids,
})

c['archetypes'].append({
    'name': 'Центрально-европейский',
    'name_en': 'Mitteleuropa',
    'body': (
        'Кафе с историей, трамваи, фасады с лепниной, вечерняя прогулка в парк. Тебя тянет в города где культурный слой осязаем — здесь ходили философы, играли композиторы, велись войны и подписывались мирные договоры. Прошлое не в музеях, оно в воздухе.\n\n'
        'Это работает потому что ты ценишь контекст. Тебе важно жить в месте где у каждой улицы есть имя и история, а не просто номер квартала. Глубина воспринимаемого фона — это твоя пища. И тебя не пугает что это значит немного больше чёрного, немного больше серого, немного меньше пластика.\n\n'
        'Окружающие иногда говорят: «там же холодно, мрачно, всё закрывается рано». Ты соглашаешься. И что? Зато здесь работает культурная инфраструктура которая старше большинства стран мира.\n\n'
        'Что стоит знать: эти города требуют времени на адаптацию. Берлин не открывается за выходные, Вена не любит туристов которые думают что были «там, где Моцарт». Готовься читать, ходить в местные книжные, приглашать на кофе людей которые тут живут давно — иначе ты турист, и города это чувствуют.'
    ),
    'body_en': (
        "Cafés with history, trams, facades with stucco, evening walks to the park. You're drawn to cities where the cultural layer is tangible — philosophers walked here, composers played here, wars were fought and treaties signed. The past isn't in museums; it's in the air.\n"
        "This works because you value context. You need to live in a place where every street has a name and a story, not just a block number. The depth of perceived background is your food. And you're not scared that this means a little more black, a little more grey, a little less plastic.\n"
        "Other people sometimes say: 'but it's cold/gloomy/everything closes early there'. You agree. So what? Cultural infrastructure here is older than most countries in the world.\n"
        "What's worth knowing: these cities demand time to adapt. Berlin doesn't open up over a weekend; Vienna doesn't like tourists who think they were 'where Mozart was'. Prepare to read, to go to local bookshops, to invite long-time residents for coffee — otherwise you're a tourist, and these cities feel that."
    ),
    'triggers': mitteleuropa_ids,
})
print(f'  + Северо-европейский эколог: {len(nordic_ids)}t')
print(f'  + Центрально-европейский: {len(mitteleuropa_ids)}t')
print(f'  - Европейский урбанист: deleted')

print()
print('=== FIX 5: your_sport — delete «Серф и волна» (100% dup), delete «Снег», add Лыжи to «Природа и движение», remove Плавание from «Дальняя дистанция» ===')
c = get('your_sport')
del_arch(c, 'Серф и волна')
ski_id = find_item_id(c, 'Лыжи / сноуборд')
del_arch(c, 'Снег')
nature = find_arch(c, 'Природа и движение')
if ski_id not in nature['triggers']:
    nature['triggers'].append(ski_id)
# After deleting «Серф и волна», Плавание ended up in 3 archs (Вода/Дальняя/Тело).
# Remove from Дальняя дистанция (still keeps Бег+Велоспорт+Хайкинг = 3t).
swim_id = find_item_id(c, 'Плавание')
distance = find_arch(c, 'Дальняя дистанция')
distance['triggers'] = [t for t in distance['triggers'] if t != swim_id]
print(f'  «Природа и движение» now {len(nature["triggers"])}t')
print(f'  «Дальняя дистанция» now {len(distance["triggers"])}t (removed Плавание to fix T2)')

print()
print('=== FIX 6: ideal_evening — delete «Игровой вечер» (100% dup of «Активная социальность») ===')
c = get('ideal_evening')
del_arch(c, 'Игровой вечер')
print(f'  archetypes now: {len(c["archetypes"])}')

print()
print('=== FIX 7: your_mood_color — delete «Нейтральная пауза» (100% dup), trim «Землистое» ===')
c = get('your_mood_color')
del_arch(c, 'Нейтральная пауза')
# Землистое: Тёмно-зелёный + Бордовый. 2t. Avoids 67% overlap with Глубокая
# тишина that arose when including Дымчато-зелёный.
zem = find_arch(c, 'Землистое')
zem['triggers'] = [find_item_id(c, n) for n in ['Тёмно-зелёный', 'Бордовый']]
print(f'  «Землистое» now {len(zem["triggers"])}t')

print()
print('=== FIX 8: your_background — trim «Творчество», delete «Чужой город» (100% dup), remove «Пустая улица» from «Транзит и движение» ===')
c = get('your_background')
tvor = find_arch(c, 'Творчество')
tvor['triggers'] = [find_item_id(c, n) for n in ['Творческая студия', 'Галерея или музей']]
del_arch(c, 'Чужой город')
# After deleting Чужой город, Пустая улица still in 3 archs (Город ночью + Транзит + Ночь и одиночество).
# Remove from «Транзит и движение» (improbable transit anyway — empty street isn't a transit mode).
empty_street_id = find_item_id(c, 'Пустая улица на рассвете')
transit = find_arch(c, 'Транзит и движение')
transit['triggers'] = [t for t in transit['triggers'] if t != empty_street_id]
print(f'  «Творчество» now {len(tvor["triggers"])}t')
print(f'  «Транзит и движение» now {len(transit["triggers"])}t (removed Пустая улица to fix T2)')
print(f'  archetypes now: {len(c["archetypes"])}')

# ─── DELTA VALIDATION on touched categories ───────
# Compare AFTER state to BEFORE baseline. Block only if any T-counter went UP
# (i.e. my fix introduced a NEW violation). Pre-existing issues are tolerated
# — they're not Phase 3 scope and would distort the gate.
print()
print('=== DELTA VALIDATION (touched cats) ===')
new_issues = 0
for cid in TOUCHED:
    after = violation_counts(get(cid))
    before = baseline[cid]
    deltas = {k: after[k] - before[k] for k in after}
    summary = ' '.join(f'{k}:{before[k]}→{after[k]}' for k in after)
    regression = any(v > 0 for v in deltas.values())
    if regression:
        new_issues += 1
        print(f'  ✗ {cid}: {summary}  (REGRESSION: {[k for k,v in deltas.items() if v > 0]})')
    else:
        print(f'  ✓ {cid}: {summary}  (no regressions)')

if new_issues > 0:
    print(f'\n!! {new_issues} categories regressed — NOT writing. Fix script logic and retry.')
    sys.exit(1)

# ─── All clean — atomic write ────────
tmp = CATS.with_suffix('.json.tmp')
tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
tmp.replace(CATS)
print(f'\nWrote: {CATS}')
