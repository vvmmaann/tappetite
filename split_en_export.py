"""Split EN_EXPORT.md into chunks for editorial review.

Output:
  EN_CHUNK_00_ui.md        — UI strings table only
  EN_CHUNK_NN_categories.md — ~10 categories per chunk (1-10)
  EN_CHUNK_99_achievements.md — Achievements table only

Each chunk includes the file header so the editor agent has context.
"""
from pathlib import Path

SRC = Path(__file__).parent / 'EN_EXPORT.md'
OUT_DIR = Path(__file__).parent / 'en_chunks'
OUT_DIR.mkdir(exist_ok=True)

CATS_PER_CHUNK = 10

text = SRC.read_text(encoding='utf-8')
lines = text.splitlines()

# Find section boundaries by matching heading patterns
ui_start = next(i for i, l in enumerate(lines) if l == '## 1. UI strings (STRINGS.en)')
cats_start = next(i for i, l in enumerate(lines) if l == '## 2. Categories, items, archetypes')
ach_start = next(i for i, l in enumerate(lines) if l == '## 3. Achievements catalog')

# Common header (lines 0..ui_start) — included in every chunk for context
header = lines[:ui_start]

# Chunk 0: UI strings (between ui_start and cats_start)
ui_chunk = header + ['---', ''] + lines[ui_start:cats_start]
(OUT_DIR / 'EN_CHUNK_00_ui.md').write_text('\n'.join(ui_chunk), encoding='utf-8')

# Cats chunks: split by H3 headers
cats_lines = lines[cats_start:ach_start]
# Find H3 indices within cats_lines
h3_indices = [i for i, l in enumerate(cats_lines) if l.startswith('### ')]
# Group by CATS_PER_CHUNK
groups = [h3_indices[i:i+CATS_PER_CHUNK] for i in range(0, len(h3_indices), CATS_PER_CHUNK)]
for n, group in enumerate(groups, 1):
    start = group[0]
    end = h3_indices[group[-1]//CATS_PER_CHUNK*CATS_PER_CHUNK + len(group)] if (group[-1]//CATS_PER_CHUNK*CATS_PER_CHUNK + len(group)) < len(h3_indices) else len(cats_lines)
    # Better: end is the start of the next group, or end of cats section
    next_group_idx = n * CATS_PER_CHUNK
    end = h3_indices[next_group_idx] if next_group_idx < len(h3_indices) else len(cats_lines)
    chunk_body = cats_lines[start:end]
    chunk = header + ['---', '', '## 2. Categories (chunk ' + str(n) + ')', ''] + chunk_body
    fn = f'EN_CHUNK_{n:02d}_categories.md'
    (OUT_DIR / fn).write_text('\n'.join(chunk), encoding='utf-8')

# Chunk 99: achievements
ach_chunk = header + ['---', ''] + lines[ach_start:]
(OUT_DIR / 'EN_CHUNK_99_achievements.md').write_text('\n'.join(ach_chunk), encoding='utf-8')

# Summary
print(f'Wrote {len(list(OUT_DIR.glob("*.md")))} chunks to {OUT_DIR}/')
for f in sorted(OUT_DIR.glob('*.md')):
    kb = f.stat().st_size // 1024
    print(f'  {f.name}  ({kb} KB)')
