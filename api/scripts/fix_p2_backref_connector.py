# -*- coding: utf-8 -*-
"""Strip the backref connector that opens P2 in most archetypes, so the
paragraph stands alone when the synthesizer splices it into a blended portrait
(and reads cleaner solo too).

  "Это работает потому, что ты ценишь X. ..."  ->  "Ты ценишь X. ..."
  "This works because you value X. ..."        ->  "You value X. ..."

Only P2 (paragraph index 1) opening is touched; nothing else changes.
Deterministic + reversible (backup). Idempotent (skips already-clean P2).

Usage:
  python3 fix_p2_backref_connector.py                # dry-run, TEST_IDS
  python3 fix_p2_backref_connector.py --apply        # apply to TEST_IDS
  python3 fix_p2_backref_connector.py --all          # dry-run, ALL categories
  python3 fix_p2_backref_connector.py --all --apply  # apply to ALL
"""
import json, shutil, sys, re
from datetime import datetime

CATEGORIES_PATH = '/opt/untitled-pick-game-api/data/categories.json'

TEST_IDS = ['aesthetic_vibe', 'addictive_game', 'core_values']

# Connector prefixes to strip from the START of P2. RU + EN. Matched
# case-insensitively at position 0; the remainder is re-capitalized.
CONNECTORS = [
    'Это работает потому, что ',
    'Это работает потому что ',
    'Это работает, потому что ',
    'This works because ',
    'This works, because ',
    'It works because ',
    'It works, because ',
]


def paras(t):
    t = (t or '').strip()
    if not t:
        return [], '\n\n'
    sep = '\n\n' if '\n\n' in t else '\n'
    return [s.strip() for s in t.split(sep) if s.strip()], sep


def cap_first(s):
    for i, ch in enumerate(s):
        if ch.isalpha():
            return s[:i] + ch.upper() + s[i+1:]
        if ch.isdigit():
            return s  # starts with a number, fine as-is
    return s


def transform_p2(p2):
    low = p2.lower()
    for con in CONNECTORS:
        if low.startswith(con.lower()):
            rest = p2[len(con):]
            # drop any stray leading punctuation/space left behind
            rest = rest.lstrip(' ,-—')
            return cap_first(rest), con
    return p2, None


def fix_body(text):
    ps, sep = paras(text)
    if len(ps) < 2:
        return text, None
    new_p2, con = transform_p2(ps[1])
    if con is None:
        return text, None
    ps[1] = new_p2
    return '\n\n'.join(ps), con


def main():
    do_all = '--all' in sys.argv
    dry = '--apply' not in sys.argv
    with open(CATEGORIES_PATH, encoding='utf-8') as f:
        cats = json.load(f)

    targets = cats if do_all else [c for c in cats if c.get('id') in TEST_IDS]
    changes = []
    for c in targets:
        arts = list(c.get('archetypes', []))
        if c.get('defaultArchetype'):
            arts.append(c['defaultArchetype'])
        for a in arts:
            for fld in ('body', 'body_en'):
                new, con = fix_body(a.get(fld, ''))
                if con:
                    a[fld] = new
                    changes.append((c.get('id'), a.get('name', '?'), fld))

    print(f'SCOPE: {"ALL" if do_all else TEST_IDS}')
    print(f'P2 openings stripped: {len(changes)}')
    # per-category tally
    from collections import Counter
    tally = Counter(cid for cid, _, _ in changes)
    for cid, n in tally.most_common():
        print(f'  {cid}: {n}')

    if dry:
        print('\n=== DRY RUN - add --apply ===')
        return

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    bak = CATEGORIES_PATH + f'.bak.p2_connector.{ts}'
    shutil.copy(CATEGORIES_PATH, bak)
    print(f'\nBackup: {bak}')
    with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    print('Saved')


if __name__ == '__main__':
    main()
