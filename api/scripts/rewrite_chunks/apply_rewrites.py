"""Merge all chunk_NN_OUTPUT.json into the live categories.json.

Reads:  ./chunk_NN_OUTPUT.json (each = AI editor output array)
Writes: target categories.json (server path or local copy passed as argv[1])
Backup: target.bak.rewrite_p1.<timestamp>

Validation before write:
  - Every output entry has key matching a real archetype
  - new_p1_ru length 80-220 chars (slack vs spec 120-180)
  - new_p1_en length 80-220 chars (if present)
  - new_p1 contains NO item names from that category
  - Replaces ONLY the first paragraph (\\n\\n separator); preserves п2-п4

Aborts if any chunk has missing/invalid entries vs the chunk's input — the
batch is treated as atomic; partial application would be confusing.
"""
import io, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

HERE = Path(__file__).parent
CATS = Path(sys.argv[1] if len(sys.argv) > 1 else '/opt/untitled-pick-game-api/data/categories.json')


def replace_first_paragraph(body: str, new_p1: str) -> str:
    """Replace the first paragraph of a body with new_p1, preserving the rest.

    Handles three storage formats:
      - Canonical RU style: paragraphs separated by \\n\\n. Split on \\n\\n,
        replace first part.
      - Editor EN style: paragraphs separated by SINGLE \\n (no double-newline).
        Split on \\n, replace first part.
      - Single block (no separators): no p2-p4 to preserve, replace whole body.

    Earlier bug: the EN single-\\n case fell through to a "find first ' . '"
    fallback that replaced only the first SENTENCE, leaving the rest of the
    old first paragraph appended after the new opener — causing 32% of EN
    bodies to bloat to 600-850 chars. (Fixed 2026-05-08 round-3 of rewrites.)
    """
    if not body or not new_p1: return new_p1 or body
    # Canonical \n\n form (RU)
    if '\n\n' in body:
        parts = body.split('\n\n', 1)
        return new_p1 + '\n\n' + parts[1]
    # Single-\n form (EN bodies stored without double-newlines)
    if '\n' in body:
        parts = body.split('\n', 1)
        return new_p1 + '\n' + parts[1]
    # No separators at all — single block, no p2-p4 to preserve
    return new_p1


def validate_new_p1(new_p1: str, item_names: list, lang: str) -> tuple[bool, str]:
    """True/False + error message. Slack on length range to allow editor judgment."""
    if not new_p1 or not new_p1.strip():
        return False, f'{lang}: empty'
    n = len(new_p1)
    if n < 80 or n > 220:
        return False, f'{lang}: length {n} outside 80-220'
    # Item-name check: lowercase substring match. False positives possible (e.g.
    # "вода" might be in both an item and a generic word) — accept slight risk.
    p_lower = new_p1.lower()
    found = []
    for name in item_names:
        if not name or len(name) < 4: continue  # skip very short items (false positive risk)
        if name.lower() in p_lower:
            found.append(name)
    if found:
        return False, f'{lang}: contains item names: {found[:3]}'
    return True, ''


# ─── Load categories.json + index ───
raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw
cat_by_id = {c['id']: c for c in cats}

# ─── Load all chunks + outputs ───
# Inputs: chunk_NN.json (exclude _OUTPUT files which the glob also catches)
chunks = sorted(p for p in HERE.glob('chunk_[0-9]*.json') if not p.stem.endswith('_OUTPUT'))
outputs = sorted(HERE.glob('chunk_[0-9]*_OUTPUT.json'))
print(f'Chunks found: {len(chunks)}')
print(f'Outputs found: {len(outputs)}')
if len(outputs) != len(chunks):
    missing = {c.stem for c in chunks} - {o.stem.replace('_OUTPUT','') for o in outputs}
    print(f'  ✗ Missing outputs: {sorted(missing)}')
    print('Aborting — process all chunks first then re-run.')
    sys.exit(1)

# ─── Index outputs by key ───
all_outputs = {}
for out_path in outputs:
    arr = json.loads(out_path.read_text(encoding='utf-8'))
    for entry in arr:
        all_outputs[entry['key']] = entry

# ─── Validate every chunk-input has an output ───
total_input = 0
missing_keys = []
for c in chunks:
    arr = json.loads(c.read_text(encoding='utf-8'))
    for entry in arr:
        total_input += 1
        if entry['key'] not in all_outputs:
            missing_keys.append(entry['key'])
if missing_keys:
    print(f'  ✗ {len(missing_keys)} input entries missing in outputs: {missing_keys[:5]}')
    sys.exit(1)
print(f'Total entries to apply: {total_input}')

# ─── Validate each output, then apply ───
backup = CATS.with_name(f'{CATS.name}.bak.rewrite_p1.{datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")}')
shutil.copy2(CATS, backup)
print(f'Backup: {backup}')

applied_ru = 0
applied_en = 0
skipped_unchanged = 0
errors = []

# Re-walk chunks to apply in order (so we know each entry's items_in_category context)
for c in chunks:
    arr = json.loads(c.read_text(encoding='utf-8'))
    for entry in arr:
        out = all_outputs[entry['key']]
        if out.get('unchanged'):
            skipped_unchanged += 1
            continue
        cat_id, arch_name = entry['key'].split('::', 1)
        cat = cat_by_id.get(cat_id)
        if not cat:
            errors.append(f'cat not found: {cat_id}'); continue
        arch = next((a for a in (cat.get('archetypes') or []) if a['name'] == arch_name), None)
        if not arch:
            errors.append(f'arch not found: {entry["key"]}'); continue
        item_names = entry['items_in_category']

        # RU
        if entry['needs_ru']:
            new_p1 = (out.get('new_p1_ru') or '').strip()
            if new_p1 and new_p1 != entry['current_p1_ru']:
                ok, err = validate_new_p1(new_p1, item_names, 'RU')
                if not ok:
                    errors.append(f'{entry["key"]} {err}'); continue
                arch['body'] = replace_first_paragraph(arch.get('body', ''), new_p1)
                applied_ru += 1

        # EN
        if entry['needs_en']:
            new_p1 = (out.get('new_p1_en') or '').strip()
            if new_p1 and new_p1 != entry['current_p1_en']:
                ok, err = validate_new_p1(new_p1, item_names, 'EN')
                if not ok:
                    errors.append(f'{entry["key"]} {err}'); continue
                arch['body_en'] = replace_first_paragraph(arch.get('body_en', ''), new_p1)
                applied_en += 1

if errors:
    print()
    print(f'  ✗ {len(errors)} validation errors — NOT writing.')
    for e in errors[:15]: print(f'    - {e}')
    sys.exit(1)

# ─── Atomic write ───
tmp = CATS.with_suffix('.json.tmp')
tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
tmp.replace(CATS)

print()
print(f'✓ Applied {applied_ru} RU + {applied_en} EN p1 rewrites')
print(f'  Skipped unchanged: {skipped_unchanged}')
print(f'  Total touched: {applied_ru + applied_en}')
print(f'  Output: {CATS}')
