"""Apply EN_CHUNK_99_achievements_edited.md → name_en/description_en in main.py.

Parses table rows: | `id` | icon | name | description |
For each id, finds the matching `"id": "X"` block in ACHIEVEMENTS list and
updates the `"name_en"` + `"description_en"` fields surgically.

Backup: main.py.bak.ach_chunk.<ts>
"""
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

MAIN = Path('/opt/untitled-pick-game-api/main.py')
CHUNK = Path('/tmp/en_edited/EN_CHUNK_99_achievements_edited.md')

ROW = re.compile(r'^\|\s*`([a-zA-Z0-9_]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$')


def parse(text):
    out = {}
    for line in text.splitlines():
        m = ROW.match(line)
        if m and m.group(1) != 'id':
            out[m.group(1)] = {'icon': m.group(2), 'name_en': m.group(3), 'description_en': m.group(4)}
    return out


def js_escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def main():
    parsed = parse(CHUNK.read_text(encoding='utf-8'))
    print(f'Parsed {len(parsed)} achievement rows')

    src = MAIN.read_text(encoding='utf-8')
    ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    bak = MAIN.with_name(f'main.py.bak.ach_chunk.{ts}')
    shutil.copy2(MAIN, bak)

    updated = 0
    missing = []
    for aid, vals in parsed.items():
        pattern_str = (
            r'(\{"id":\s*"' + re.escape(aid) + r'"[\s\S]+?"name_en":\s*")'
            r'[^"]*'
            r'("[\s\S]+?"description_en":\s*")'
            r'[^"]*'
            r'(")'
        )
        pat = re.compile(pattern_str)
        new_name = js_escape(vals['name_en'])
        new_desc = js_escape(vals['description_en'])
        replaced = [False]
        def _r(m):
            replaced[0] = True
            return m.group(1) + new_name + m.group(2) + new_desc + m.group(3)
        new_src, n = pat.subn(_r, src, count=1)
        if n == 0:
            missing.append(aid)
            continue
        if new_src != src:
            updated += 1
        src = new_src

    MAIN.write_text(src, encoding='utf-8')

    print(f'Backup: {bak.name}')
    print(f'Updated achievements: {updated}/{len(parsed)}')
    if missing:
        print('Missing in main.py:')
        for m in missing:
            print(f'  - {m}')


if __name__ == '__main__':
    main()
