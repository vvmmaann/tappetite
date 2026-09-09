"""Re-apply EN p1 rewrites only, fixing the single-\\n bug from the first apply pass.

Background: original apply_rewrites.py had a bug for EN bodies stored without
\\n\\n paragraph separators (single-\\n style). The fallback "replace before
first '. '" branch only replaced the first SENTENCE, leaving the rest of the
old first paragraph appended — bloating 228 EN bodies to 600-850 chars.

This script:
  1. Reads OLD body_en from a backup file (pre-rewrite-pass state)
  2. Reads NEW p1_en from chunk_NN_OUTPUT.json files
  3. Applies the FIXED replace_first_paragraph (handles \\n\\n / \\n / single-block)
  4. Replaces body_en in target categories.json (current prod) atomically

Does NOT touch body (RU). RU was applied correctly the first time.

Usage:
  python reapply_en_only.py <backup.json> <target.json>
"""
import io, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

if len(sys.argv) != 3:
    print('Usage: python reapply_en_only.py <backup.json> <target.json>')
    sys.exit(2)

BACKUP = Path(sys.argv[1])
TARGET = Path(sys.argv[2])
HERE = Path(__file__).parent


def replace_first_paragraph_fixed(body, new_p1):
    """Same as the FIXED version in apply_rewrites.py."""
    if not body or not new_p1:
        return new_p1 or body
    if '\n\n' in body:
        return new_p1 + '\n\n' + body.split('\n\n', 1)[1]
    if '\n' in body:
        return new_p1 + '\n' + body.split('\n', 1)[1]
    return new_p1


# ─── Load all OUTPUT files (agent's new EN p1's) ───────────────
all_outputs = {}
for out_path in sorted(HERE.glob('chunk_[0-9]*_OUTPUT.json')):
    for entry in json.loads(out_path.read_text(encoding='utf-8')):
        all_outputs[entry['key']] = entry
print(f'Loaded {len(all_outputs)} agent outputs')

# ─── Load all INPUT files to know which archetypes had needs_en=True ───
inputs = {}
for in_path in sorted(p for p in HERE.glob('chunk_[0-9]*.json') if not p.stem.endswith('_OUTPUT')):
    for entry in json.loads(in_path.read_text(encoding='utf-8')):
        inputs[entry['key']] = entry

# ─── Load backup (source of OLD body_en) and target (current state) ───
print(f'Backup: {BACKUP}')
print(f'Target: {TARGET}')
backup_data = json.loads(BACKUP.read_text(encoding='utf-8'))
target_data = json.loads(TARGET.read_text(encoding='utf-8'))
backup_cats = backup_data.get('categories') if isinstance(backup_data, dict) else backup_data
target_cats = target_data.get('categories') if isinstance(target_data, dict) else target_data

# Index by id+name for both
def index_archs(cats):
    idx = {}
    for cat in cats:
        cid = cat.get('id')
        for a in (cat.get('archetypes') or []):
            idx[f"{cid}::{a['name']}"] = a
    return idx

backup_idx = index_archs(backup_cats)
target_idx = index_archs(target_cats)

# ─── Take a fresh backup of current target before overwriting ───
ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
fresh_backup = TARGET.with_name(f'{TARGET.name}.bak.reapply_en.{ts}')
shutil.copy2(TARGET, fresh_backup)
print(f'Fresh backup of current target: {fresh_backup}')

# ─── Apply EN-only rewrites with fixed logic ───────────────────
applied = 0
skipped = 0
errors = []

for key, inp in inputs.items():
    if not inp.get('needs_en'):
        continue
    out = all_outputs.get(key)
    if not out:
        errors.append(f'{key}: no output found')
        continue
    if out.get('unchanged'):
        skipped += 1
        continue
    new_p1_en = (out.get('new_p1_en') or '').strip()
    if not new_p1_en:
        skipped += 1
        continue

    # Source the OLD body_en from BACKUP (not from current target — current is bloated)
    backup_arch = backup_idx.get(key)
    target_arch = target_idx.get(key)
    if not backup_arch or not target_arch:
        errors.append(f'{key}: not found in backup or target')
        continue

    old_body_en = backup_arch.get('body_en', '')
    new_body_en = replace_first_paragraph_fixed(old_body_en, new_p1_en)
    target_arch['body_en'] = new_body_en
    applied += 1

if errors:
    print()
    print(f'⚠ {len(errors)} errors:')
    for e in errors[:10]: print(f'  - {e}')

# ─── Atomic write ────────────────────────────────────────────
tmp = TARGET.with_suffix('.json.tmp')
tmp.write_text(json.dumps(target_data, ensure_ascii=False, indent=2), encoding='utf-8')
tmp.replace(TARGET)

print()
print(f'✓ Re-applied EN p1 for {applied} archetypes')
print(f'  Skipped (unchanged or empty): {skipped}')
print(f'  Errors: {len(errors)}')
print(f'  Output: {TARGET}')
