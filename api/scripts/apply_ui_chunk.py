"""Apply EN_CHUNK_00_ui_edited.md changes to STRINGS.en block in game.html.

Conservative approach:
  - Parse edited chunk into key→value dict
  - For each key, locate the line in game.html STRINGS.en block via regex
  - Replace ONLY the value (preserve key, indentation, trailing comma)
  - Keys not present in chunk → left as-is (don't delete)
  - New keys in chunk → log a warning (we want exact 1:1 set)

Backup: game.html.bak.ui_chunk.<ts>
"""
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

GAME = Path('C:/Users/uncle/Claude/taste_twins/game.html')
CHUNK = Path('C:/Users/uncle/Claude/taste_twins/en_chunks/edited/EN_CHUNK_00_ui_edited.md')

KEY_LINE = re.compile(r'^\|\s*`([a-zA-Z0-9_.\-]+)`\s*\|\s*(.*?)\s*\|\s*$')

def parse_chunk(text):
    out = {}
    for line in text.splitlines():
        m = KEY_LINE.match(line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def main():
    chunk_text = CHUNK.read_text(encoding='utf-8')
    edited_strings = parse_chunk(chunk_text)
    print(f'Parsed {len(edited_strings)} UI keys from edited chunk')

    src = GAME.read_text(encoding='utf-8')

    # Find STRINGS.en block bounds (between `en: {` and matching `},` at depth 0)
    en_anchor = re.search(r'\n\s*en:\s*\{', src)
    if not en_anchor:
        print('FAIL: STRINGS.en anchor not found')
        return
    block_start = en_anchor.end()
    # Walk to find matching close brace
    depth = 1
    i = block_start
    while i < len(src) and depth > 0:
        c = src[i]
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        i += 1
    block_end = i  # one past closing brace
    en_block = src[block_start:block_end]

    # For each line that looks like a key entry, check if value differs and replace
    # Format: '    'key':                'value',
    # We preserve the key + indentation + trailing comma
    line_pat = re.compile(
        r"^(?P<lead>\s*)'(?P<key>[a-zA-Z0-9_.\-]+)':\s*'(?P<val>(?:[^'\\]|\\.)*)'(?P<tail>,?\s*(?://.*)?)$",
        re.MULTILINE,
    )

    replaced, unchanged, missing_in_chunk, missing_in_src = 0, 0, 0, 0
    used_keys = set()

    def js_escape(s):
        # Escape backslashes and single quotes for inclusion inside '...' literal
        return s.replace('\\', '\\\\').replace("'", "\\'")

    def js_unescape(s):
        # Reverse JS string escaping for comparison
        return s.replace("\\'", "'").replace('\\\\', '\\')

    def repl(m):
        nonlocal replaced, unchanged, missing_in_chunk
        key = m.group('key')
        old_val_js = m.group('val')
        old_val = js_unescape(old_val_js)
        if key not in edited_strings:
            missing_in_chunk += 1
            return m.group(0)  # leave alone
        used_keys.add(key)
        new_val = edited_strings[key]
        if old_val == new_val:
            unchanged += 1
            return m.group(0)
        replaced += 1
        new_val_js = js_escape(new_val)
        return f"{m.group('lead')}'{key}': '{new_val_js}'{m.group('tail')}"

    new_block = line_pat.sub(repl, en_block)

    # Diff: chunk keys not seen in source
    invented = [k for k in edited_strings if k not in used_keys]
    missing_in_src = len(invented)

    # Backup + write
    ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    bak = GAME.with_name(f'game.html.bak.ui_chunk.{ts}')
    shutil.copy2(GAME, bak)
    new_src = src[:block_start] + new_block + src[block_end:]
    GAME.write_text(new_src, encoding='utf-8')

    print()
    print(f'Backup: {bak.name}')
    print(f'Replaced: {replaced}')
    print(f'Unchanged: {unchanged}')
    print(f'Source keys not in chunk (left alone): {missing_in_chunk}')
    print(f'Chunk keys not found in source: {missing_in_src}')
    if invented:
        print('  Invented keys (not applied):')
        for k in invented[:10]:
            print(f'    - {k}')
        if len(invented) > 10:
            print(f'    ... +{len(invented)-10} more')


if __name__ == '__main__':
    main()
