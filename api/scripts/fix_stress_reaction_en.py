"""Surgical fix: add missing name_en + blurb_en for stress_reaction category."""
import io, json, shutil, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

CATS = Path(sys.argv[1] if len(sys.argv) > 1 else '/opt/untitled-pick-game-api/data/categories.json')
ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
shutil.copy2(CATS, CATS.with_name(f'{CATS.name}.bak.stress_reaction_en.{ts}'))

raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw
sr = next(c for c in cats if c['id'] == 'stress_reaction')
sr['name_en'] = 'How you react to stress'
sr['blurb_en'] = 'Pick your reaction under pressure'
print(f'name_en added: {sr["name_en"]}')
print(f'blurb_en added: {sr["blurb_en"]}')

tmp = CATS.with_suffix('.json.tmp')
tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
tmp.replace(CATS)
print(f'Wrote: {CATS}')
