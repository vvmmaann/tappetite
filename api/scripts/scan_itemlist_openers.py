"""Scan all archetype p1's in live categories.json for item-list-opener pattern.

Pattern detection: first sentence (text before first '.' or em-dash) of body
that has >=2 commas AND <=80 chars — indicates an item-list opener like
«Реквием, Олдбой, Чёрный лебедь, Джокер.» or «Алсу, Губин, Корни, Smash!!»

Also checks body_en symmetrically.
"""
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

CATS = Path(sys.argv[1] if len(sys.argv) > 1 else 'categories_live.json')

def is_itemlist_opener(text, item_names):
    """True only if first-sentence comma-tokens MATCH actual item names in this
    category. Distinguishes «Реквием, Олдбой, Чёрный лебедь...» (real item-list)
    from «Море, вино, ужин в 22:00...» (atmospheric scene — different beast).
    """
    if not text or not item_names:
        return False
    t = text.strip()
    first_period = t.find('.')
    first_emdash = t.find(' — ')
    if first_period == -1: first_period = len(t)
    if first_emdash == -1: first_emdash = len(t)
    end = min(first_period, first_emdash)
    first = t[:end].strip()
    if len(first) > 100 or first.count(',') < 2:
        return False
    # Tokenize by comma, normalize each
    tokens = [s.strip().lower() for s in first.split(',')]
    item_lower = [n.lower() for n in item_names if n]
    # How many tokens match an item name (exact or substring)?
    matches = 0
    for tk in tokens:
        if not tk: continue
        for it in item_lower:
            if tk == it or tk in it or it in tk:
                matches += 1
                break
    # 2+ matching item names = real item-list opener
    return matches >= 2

raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw

total_archs = 0
ru_bad = 0
en_bad = 0
both_bad = 0
by_cat = {}  # cat_id → list of (arch_name, ru_opener_short, en_opener_short)
samples_ru = []
samples_en = []

for cat in cats:
    cid = cat.get('id', '?')
    item_names_ru = [it.get('name','') for it in (cat.get('items') or [])]
    item_names_en = [it.get('name_en','') for it in (cat.get('items') or [])]
    for a in (cat.get('archetypes') or []):
        total_archs += 1
        ru_body = a.get('body', '') or ''
        en_body = a.get('body_en', '') or ''
        ru_p1 = ru_body.split('\n\n')[0].split('\n')[0]
        en_p1 = en_body.split('\n\n')[0].split('\n')[0]
        ru_is_bad = is_itemlist_opener(ru_p1, item_names_ru)
        en_is_bad = is_itemlist_opener(en_p1, item_names_en)
        if ru_is_bad: ru_bad += 1
        if en_is_bad: en_bad += 1
        if ru_is_bad and en_is_bad: both_bad += 1
        if ru_is_bad or en_is_bad:
            by_cat.setdefault(cid, []).append({
                'arch': a.get('name', '?'),
                'ru_opener': ru_p1[:80] if ru_is_bad else None,
                'en_opener': en_p1[:80] if en_is_bad else None,
            })
            if len(samples_ru) < 8 and ru_is_bad:
                samples_ru.append((cat.get('name','?'), a.get('name','?'), ru_p1[:120]))
            if len(samples_en) < 5 and en_is_bad:
                samples_en.append((cat.get('name','?'), a.get('name','?'), en_p1[:120]))

print(f'Total archetypes scanned: {total_archs}')
print(f'  RU bodies with item-list opener: {ru_bad} ({100*ru_bad//total_archs}%)')
print(f'  EN bodies with item-list opener: {en_bad} ({100*en_bad//total_archs}%)')
print(f'  Both RU+EN bad: {both_bad}')
print()
print(f'Categories affected: {len(by_cat)} of {len(cats)}')
print()
print('=== TOP 10 categories with most bad-openers ===')
top = sorted(by_cat.items(), key=lambda kv: -len(kv[1]))[:10]
for cid, archs in top:
    print(f'  {cid}: {len(archs)} bad archetypes')
print()
print('=== SAMPLES (RU) ===')
for cname, aname, opener in samples_ru:
    print(f'  «{cname}» / «{aname}»')
    print(f'    {opener}...')
print()
print('=== SAMPLES (EN) ===')
for cname, aname, opener in samples_en:
    print(f'  «{cname}» / «{aname}»')
    print(f'    {opener}...')
