"""Split archetype p1's that need rewriting into chunks for batch AI editor.

Reads ../categories_live.json (must be present locally).
Writes chunk_NN.json files in this directory.
"""
import io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

HERE = Path(__file__).parent
CATS = Path(sys.argv[1] if len(sys.argv) > 1 else (HERE / '..' / 'categories_live.json'))
CHUNK_SIZE = 30  # archetypes per chunk — balance: small enough for one agent run, big enough to be efficient


def is_itemlist_opener(text, item_names=None):
    """True if first sentence looks like an item-list opener.

    Two-pass detection:
      1) STRICT (cross-reference): tokens MATCH actual item_names → high
         confidence. Used when item_names is provided.
      2) LOOSE (any comma-list of capitalized tokens): catches cases where
         items are stored only in one language but body uses translated terms
         (e.g. Russian body mentions «Ведьмак» when items[].name is the
         English «The Witcher 3: Wild Hunt»). Used when item_names is
         unavailable OR strict mode found nothing.

    The loose mode has higher false-positive rate (legitimate atmospheric
    sentences like «Море, вино, ужин в 22:00.» get flagged), so prefer
    strict when item names are reliable.
    """
    if not text:
        return False
    t = text.strip()
    first_period = t.find('.')
    first_emdash = t.find(' — ')
    if first_period == -1: first_period = len(t)
    if first_emdash == -1: first_emdash = len(t)
    end = min(first_period, first_emdash)
    first = t[:end].strip()
    if len(first) > 100 or first.count(',') < 2:
        return False
    tokens = [s.strip() for s in first.split(',')]

    # STRICT pass — token cross-reference with item names (higher precision)
    if item_names:
        item_lower = [n.lower() for n in item_names if n]
        matches = 0
        for tk in tokens:
            tk_lower = tk.lower()
            if not tk_lower: continue
            for it in item_lower:
                if tk_lower == it or tk_lower in it or it in tk_lower:
                    matches += 1
                    break
        if matches >= 2:
            return True

    # LOOSE pass — pure morphology check (any 3+ capitalized comma-tokens).
    # Catches cross-language item references that strict pass misses.
    cap_count = sum(1 for tk in tokens if tk and (tk[0].isupper() or tk[0].isdigit()))
    return cap_count >= 3


raw = json.loads(CATS.read_text(encoding='utf-8'))
cats = raw.get('categories') if isinstance(raw, dict) else raw

work = []
for cat in cats:
    cid = cat.get('id', '?')
    cname = cat.get('name', '?')
    items_ru = [it.get('name', '') for it in (cat.get('items') or []) if it.get('name')]
    items_en = [it.get('name_en', '') for it in (cat.get('items') or []) if it.get('name_en')]
    all_items = list(set(items_ru + items_en))
    for a in (cat.get('archetypes') or []):
        ru_body = a.get('body', '') or ''
        en_body = a.get('body_en', '') or ''
        ru_p1 = ru_body.split('\n\n')[0]
        en_p1 = en_body.split('\n\n')[0]
        needs_ru = is_itemlist_opener(ru_p1, items_ru)
        needs_en = is_itemlist_opener(en_p1, items_en)
        if needs_ru or needs_en:
            work.append({
                'key': f"{cid}::{a['name']}",
                'category_id': cid,
                'category_name': cname,
                'archetype_name': a['name'],
                'items_in_category': all_items,
                'current_p1_ru': ru_p1,
                'current_p1_en': en_p1,
                'needs_ru': needs_ru,
                'needs_en': needs_en,
            })

print(f'Total archetypes needing rewrite: {len(work)}')
print(f'Chunk size: {CHUNK_SIZE}')
n_chunks = (len(work) + CHUNK_SIZE - 1) // CHUNK_SIZE
print(f'Will write {n_chunks} chunk files')

# Clean any old chunks
for old in HERE.glob('chunk_*.json'):
    old.unlink()
for old in HERE.glob('chunk_*_OUTPUT.json'):
    old.unlink()

for i in range(n_chunks):
    chunk = work[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
    out_path = HERE / f'chunk_{i+1:02d}.json'
    out_path.write_text(json.dumps(chunk, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'  {out_path.name}: {len(chunk)} archetypes')

print()
print(f'Done. Hand each chunk_NN.json + EDITOR_PROMPT.md to a fresh agent.')
print(f'Agent must save its output to chunk_NN_OUTPUT.json (same dir).')
print(f'Then run apply_rewrites.py to merge all outputs back into categories.json.')
