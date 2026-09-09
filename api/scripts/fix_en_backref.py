# -*- coding: utf-8 -*-
"""Strip EN backref connectors that open P2 (missed by the first pass, which
only knew "this works because"/"it works because"). EN generation used many
phrasings: "Why it works:", "Why it lands:", "The reason it works:",
"The logic is simple:", "It lands because", "This fits because", etc.

Safe colon-form: only strips when the clause BEFORE the first colon starts with
a known backref word (why / the reason / the logic / what makes / here's why),
so legitimate "X: Y" content is never touched.

EN body_en only. P2 only. Run: python3 fix_en_backref.py [--apply] [--samples]
"""
import json, shutil, sys, re
from datetime import datetime
CATEGORIES_PATH = '/opt/untitled-pick-game-api/data/categories.json'

BECAUSE = [
    'it works because ', 'this works because ',
    'it lands because ', 'this lands because ',
    'it fits because ', 'this fits because ',
    'it clicks because ', 'this clicks because ',
]
COLON_STARTS = ('why ', 'the reason', 'the logic', 'what makes', "here's why", 'here is why', 'the appeal')
REASON_NOCOLON = re.compile(r'^the reason (?:it (?:works|lands|fits|clicks) is|is)\s+', re.IGNORECASE)


def cap_first(s):
    for i, ch in enumerate(s):
        if ch.isalpha():
            return s[:i] + ch.upper() + s[i+1:]
        if ch.isdigit():
            return s
    return s


def strip_en(p2):
    low = p2.lower()
    for pat in BECAUSE:
        if low.startswith(pat):
            return cap_first(p2[len(pat):].lstrip(' ,-—')), pat
    # colon-form FIRST (so "The reason it works is simple: X" -> "X",
    # not "Simple: X" which the no-colon rule below would wrongly leave)
    m = re.match(r'^([^:]{1,42}):\s*', p2)
    if m:
        clause = m.group(1).lower().strip()
        if clause.startswith(COLON_STARTS):
            return cap_first(p2[m.end():].lstrip(' ,-—')), clause[:24] + ':'
    m = REASON_NOCOLON.match(p2)
    if m:
        return cap_first(p2[m.end():].lstrip(' ,-—')), 'the reason ... is'
    return p2, None


def paras(t):
    t = (t or '').strip()
    if not t:
        return [], '\n'
    sep = '\n\n' if '\n\n' in t else '\n'
    return [s.strip() for s in t.split(sep) if s.strip()], sep


def fix_body(text):
    ps, sep = paras(text)
    if len(ps) < 2:
        return text, None
    new_p2, con = strip_en(ps[1])
    if not con:
        return text, None
    ps[1] = new_p2
    return sep.join(ps), con   # preserve original separator (single-\n EN stays single-\n)


def main():
    dry = '--apply' not in sys.argv
    show = '--samples' in sys.argv
    with open(CATEGORIES_PATH, encoding='utf-8') as f:
        cats = json.load(f)
    changes = []
    samples = []
    for c in cats:
        arts = list(c.get('archetypes', []))
        if c.get('defaultArchetype'):
            arts.append(c['defaultArchetype'])
        for a in arts:
            old = a.get('body_en', '')
            new, con = fix_body(old)
            if con:
                a['body_en'] = new
                changes.append(con)
                if len(samples) < 18:
                    op_old = [s for s in paras(old)[0]][1][:62]
                    op_new = [s for s in paras(new)[0]][1][:62]
                    samples.append((a.get('name', '?'), op_old, op_new))
    print(f'EN P2 backrefs stripped: {len(changes)}')
    from collections import Counter
    for k, v in Counter(changes).most_common():
        print(f'  {v:4d}  «{k}»')
    if show:
        print('\nSAMPLES (before -> after):')
        for nm, o, n in samples:
            print(f'  [{nm}]\n    {o}\n -> {n}')
    if dry:
        print('\n=== DRY RUN - add --apply ===')
        return
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(CATEGORIES_PATH, CATEGORIES_PATH + f'.bak.en_backref.{ts}')
    with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    print('Saved')


if __name__ == '__main__':
    main()
