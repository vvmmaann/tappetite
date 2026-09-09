"""
One-shot extractor: parse `const CATEGORIES = [...]` from game.html
into clean JSON for /api/categories endpoint.

Run from C:\\Users\\uncle\\Claude\\taste_twins\\:
    python api/extract_categories.py

Outputs: api/categories.json
"""
import re
import json
import sys
from pathlib import Path

GAME_HTML = Path(__file__).parent.parent / 'game.html'
OUT_JSON = Path(__file__).parent / 'categories.json'

if not GAME_HTML.exists():
    print(f"ERROR: {GAME_HTML} not found")
    sys.exit(1)

src = GAME_HTML.read_text(encoding='utf-8')

# 1) Find the array bounds via bracket depth-counting
start_marker = 'const CATEGORIES = ['
start = src.index(start_marker)
i = src.index('[', start)
arr_start = i
depth = 1
i += 1
in_str = False
str_quote = None
while i < len(src) and depth > 0:
    c = src[i]
    if in_str:
        if c == '\\':
            i += 2
            continue
        if c == str_quote:
            in_str = False
        i += 1
        continue
    if c in ("'", '"'):
        in_str = True
        str_quote = c
        i += 1
        continue
    if c == '[':
        depth += 1
    elif c == ']':
        depth -= 1
    i += 1
arr_end = i  # one past closing ]
js_array = src[arr_start:arr_end]
print(f"Extracted {len(js_array)} chars of JS array")

# 2) Strip JS comments (line + block) carefully (skip inside strings)
def strip_comments(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        # Line comment
        if c == '/' and i + 1 < n and text[i+1] == '/':
            j = text.find('\n', i)
            if j < 0:
                break
            i = j  # keep the newline
            continue
        # Block comment
        if c == '/' and i + 1 < n and text[i+1] == '*':
            j = text.find('*/', i + 2)
            if j < 0:
                break
            i = j + 2
            continue
        # String literal — copy as-is
        if c in ("'", '"'):
            out.append(c)
            quote = c
            i += 1
            while i < n:
                if text[i] == '\\' and i + 1 < n:
                    out.append(text[i:i+2])
                    i += 2
                elif text[i] == quote:
                    out.append(text[i])
                    i += 1
                    break
                else:
                    out.append(text[i])
                    i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)

js_array = strip_comments(js_array)

# 3) Convert single-quoted strings → double-quoted, escape internal "
def js_strings_to_json(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "'":
            # collect contents
            content = []
            i += 1
            while i < n and text[i] != "'":
                if text[i] == '\\' and i + 1 < n:
                    nxt = text[i+1]
                    if nxt == "'":
                        content.append("'")
                    elif nxt == '"':
                        content.append('\\"')
                    elif nxt == '\\':
                        content.append('\\\\')
                    elif nxt == 'n':
                        content.append('\\n')
                    elif nxt == 't':
                        content.append('\\t')
                    else:
                        content.append('\\' + nxt)
                    i += 2
                else:
                    if text[i] == '"':
                        content.append('\\"')
                    elif text[i] == '\\':
                        content.append('\\\\')
                    else:
                        content.append(text[i])
                    i += 1
            i += 1  # skip closing '
            out.append('"' + ''.join(content) + '"')
        elif c == '"':
            # already double-quoted, copy as-is
            out.append(c)
            i += 1
            while i < n and text[i] != '"':
                if text[i] == '\\' and i + 1 < n:
                    out.append(text[i:i+2])
                    i += 2
                else:
                    out.append(text[i])
                    i += 1
            if i < n:
                out.append('"')
                i += 1
        else:
            out.append(c)
            i += 1
    return ''.join(out)

js_array = js_strings_to_json(js_array)

# 4) Quote unquoted object keys: word: → "word":
# Match pattern: (start of object/comma + whitespace) (word) (whitespace) (:)
# Skip lookahead inside strings (already converted to double-quoted)
def quote_keys(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        # Inside string — copy verbatim until end of string
        if c == '"':
            out.append(c)
            i += 1
            while i < n and text[i] != '"':
                if text[i] == '\\' and i + 1 < n:
                    out.append(text[i:i+2])
                    i += 2
                else:
                    out.append(text[i])
                    i += 1
            if i < n:
                out.append('"')
                i += 1
            continue
        # Not in string — look for word followed by :
        if c.isalpha() or c == '_':
            # collect word
            j = i
            while j < n and (text[j].isalnum() or text[j] == '_'):
                j += 1
            word = text[i:j]
            # Check what follows after optional whitespace
            k = j
            while k < n and text[k] in ' \t':
                k += 1
            if k < n and text[k] == ':':
                # It's a key — quote it
                out.append('"' + word + '"')
                i = j
                continue
            else:
                out.append(word)
                i = j
                continue
        out.append(c)
        i += 1
    return ''.join(out)

js_array = quote_keys(js_array)

# 5) Remove trailing commas before ] or }
js_array = re.sub(r',(\s*[}\]])', r'\1', js_array)

# 6) Try to parse as JSON
try:
    data = json.loads(js_array)
except json.JSONDecodeError as e:
    print(f"ERROR parsing converted JSON: {e}")
    # Save the offending text for debug
    debug_path = Path(__file__).parent / 'categories_debug.txt'
    debug_path.write_text(js_array, encoding='utf-8')
    print(f"Wrote debug to {debug_path}")
    # Show context around error
    lines = js_array.split('\n')
    if hasattr(e, 'lineno'):
        for ln in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
            marker = '>>> ' if ln == e.lineno - 1 else '    '
            print(f"{marker}{ln+1}: {lines[ln]}")
    sys.exit(1)

print(f"Successfully parsed {len(data)} categories")

# 7) Write JSON
OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"Wrote {OUT_JSON} ({OUT_JSON.stat().st_size} bytes)")

# 8) Quick stats
print()
print("=== Category breakdown ===")
print(f"Total: {len(data)}")
types = {}
subtypes = {}
for c in data:
    t = c.get('category_type', '?')
    s = c.get('category_subtype', '?')
    types[t] = types.get(t, 0) + 1
    subtypes[s] = subtypes.get(s, 0) + 1
print(f"By type: {types}")
print(f"By subtype: {subtypes}")
print(f"Items total: {sum(len(c.get('items', [])) for c in data)}")
