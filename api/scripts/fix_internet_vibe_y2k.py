"""Remove Dark academia from "Y2K-возвращенец" triggers in internet_vibe category.

T5 violation: Dark academia (library/tweed/manuscripts aesthetic, 2010s+) doesn't
literally embody Y2K-throwback (glitter/neon/early-2000s). Was causing tied 5-5
score with "Тихий вкус" for users picking Dark academia + Soft online combos.

Backup written before edit.
"""
import io
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

CATS = Path(sys.argv[1] if len(sys.argv) > 1 else '/opt/untitled-pick-game-api/data/categories.json')

ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
bak = CATS.with_name(f'{CATS.name}.bak.internet_vibe_y2k.{ts}')
shutil.copy2(CATS, bak)
print(f'Backup: {bak}')

raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw
iv = next(c for c in cats if c['id'] == 'internet_vibe')

# Find Y2K archetype, drop dark-academia trigger
y2k = next(a for a in iv['archetypes'] if a['name'] == 'Y2K-возвращенец')
da_id = 'internet_vibe-dark-academia'
before = list(y2k.get('triggers') or [])
y2k['triggers'] = [t for t in before if t != da_id]
print(f'Y2K-возвращенец triggers: {len(before)} -> {len(y2k["triggers"])}')
print(f'  removed: {da_id if da_id in before else "(not present, no-op)"}')
print(f'  remaining: {y2k["triggers"]}')

tmp = CATS.with_suffix('.json.tmp')
tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
tmp.replace(CATS)
print(f'Wrote: {CATS}')
