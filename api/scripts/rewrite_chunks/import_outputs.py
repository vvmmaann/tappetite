"""Copy agent's rewritten files into the expected location + normalize en-dash → em-dash.

Source: ./rewritten/chunk_NN_rewritten_p1.json
Target: ./chunk_NN_OUTPUT.json

Em-dash normalization: agent used en-dash («–»), our existing typography uses
em-dash («—»). Replace ' – ' → ' — ' to match house style.
"""
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

HERE = Path(__file__).parent
SRC_DIR = HERE / 'rewritten'

if not SRC_DIR.is_dir():
    print(f'ERR: {SRC_DIR} does not exist'); sys.exit(1)

src_files = sorted(SRC_DIR.glob('chunk_*_rewritten_p1.json'))
print(f'Found {len(src_files)} agent outputs in rewritten/')

total_endash_replacements = 0
imported = 0

for src in src_files:
    # Extract chunk number from filename
    stem = src.stem  # chunk_06_rewritten_p1
    parts = stem.split('_')
    if len(parts) < 2 or not parts[1].isdigit():
        print(f'  ✗ skipping {src.name} (cannot extract chunk number)'); continue
    chunk_num = parts[1]
    target = HERE / f'chunk_{chunk_num}_OUTPUT.json'

    raw = src.read_text(encoding='utf-8')
    # Em-dash normalization: en-dash with surrounding spaces is what agent used
    # for parenthetical breaks. Em-dash is our house style.
    before_count = raw.count(' – ')
    raw_normalized = raw.replace(' – ', ' — ')
    total_endash_replacements += before_count

    # Validate JSON parses (catches typos / corrupted output)
    try:
        json.loads(raw_normalized)
    except Exception as e:
        print(f'  ✗ {src.name}: invalid JSON after normalization — {e}'); continue

    target.write_text(raw_normalized, encoding='utf-8')
    print(f'  ✓ {src.name} → {target.name}  (em-dash fixes: {before_count})')
    imported += 1

print()
print(f'Imported: {imported} of {len(src_files)} chunks')
print(f'Total en-dash → em-dash replacements: {total_endash_replacements}')
print()
print(f'Next: python apply_rewrites.py [path/to/categories.json]')
