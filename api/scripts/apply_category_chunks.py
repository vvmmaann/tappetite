"""Apply edited EN_CHUNK_NN_categories_edited.md chunks to categories.json.

For each chunk:
  - Parse categories: id, h3 (=name_en), `**blurb (EN):**` value, items, archetypes
  - For each category, locate by id in categories.json:
      * Update name_en (from h3 line — stripped)
      * Update blurb_en
      * Items match by index (export script preserves order; editor was told not to reorder)
        - Update name_en (bold text) and ctx_en (after ' — ')
      * Archetypes match by index
        - Update name_en (bold text) and body_en (joined blockquote lines)
      * Default archetype updates name_en + body_en

Safety:
  - Abort per-category if item or archetype count mismatch
  - Backup categories.json before any write
  - Print full per-chunk summary

Run remotely on server (where categories.json lives).
"""
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

CHUNKS_DIR = Path('/tmp/en_edited')   # we'll scp the edited dir here
CATS_PATH = Path('/opt/untitled-pick-game-api/data/categories.json')

H3 = re.compile(r'^### (.+)$')
ID_LINE = re.compile(r'^- \*\*id:\*\* `([^`]+)`')
BLURB_EN = re.compile(r'^- \*\*blurb \(EN\):\*\* (.+)$')
ITEM_LINE = re.compile(r'^(\d+)\. \*\*(.+?)\*\*(?: — (.+))?$')
ARCH_NAME = re.compile(r'^\*\*(.+?)\*\*$')


def parse_chunk(text):
    """Return list of category dicts: {id, name_en, blurb_en, items, archetypes, default}."""
    cats = []
    cur = None
    section = None  # None | 'items' | 'archetypes'
    cur_arch = None
    cur_arch_body = []
    is_default = False

    def commit_arch():
        nonlocal cur_arch, cur_arch_body, is_default
        if cur_arch is None:
            return
        body = '\n\n'.join(p for p in '\n'.join(cur_arch_body).split('\n\n') if p.strip())
        # Normalize: each blockquote line "> text" → "text"
        # We've been collecting raw lines. Join paragraphs by blank.
        joined = '\n'.join(cur_arch_body).strip()
        # Replace blank lines (which represent paragraph breaks) with a single \n\n
        # But we already stripped '> ' prefix while collecting.
        target = is_default and 'default' or 'archetypes'
        if is_default:
            cur['default'] = {'name_en': cur_arch, 'body_en': joined}
        else:
            cur['archetypes'].append({'name_en': cur_arch, 'body_en': joined})
        cur_arch = None
        cur_arch_body = []
        is_default = False

    for raw in text.splitlines():
        line = raw.rstrip()
        # New category?
        m = H3.match(line)
        if m and not m.group(1).lower().startswith('achievements'):
            if cur:
                commit_arch()
                cats.append(cur)
            cur = {'id': None, 'name_en': m.group(1).strip(), 'blurb_en': None,
                   'items': [], 'archetypes': [], 'default': None}
            section = None
            continue
        if cur is None:
            continue
        m = ID_LINE.match(line)
        if m:
            cur['id'] = m.group(1)
            continue
        m = BLURB_EN.match(line)
        if m:
            cur['blurb_en'] = m.group(1).strip()
            continue
        if line.startswith('#### Items'):
            commit_arch()
            section = 'items'
            continue
        if line.startswith('#### Archetypes'):
            commit_arch()
            section = 'archetypes'
            continue
        if line.startswith('---'):
            commit_arch()
            section = None
            continue

        if section == 'items':
            m = ITEM_LINE.match(line)
            if m:
                cur['items'].append({'name_en': m.group(2).strip(), 'ctx_en': (m.group(3) or '').strip()})

        elif section == 'archetypes':
            # Archetype boundary: a `**name**` line. If we were collecting body,
            # commit it first, then start a new arch.
            if line.startswith('> '):
                # body line — strip "> "
                cur_arch_body.append(line[2:])
                continue
            m = ARCH_NAME.match(line)
            if m:
                # Commit previous before starting next
                commit_arch()
                name = m.group(1).strip()
                if name.startswith('Default archetype: '):
                    cur_arch = name[len('Default archetype: '):].strip()
                    is_default = True
                else:
                    cur_arch = name
                    is_default = False
                continue
            # Blank line inside body: append a blank to preserve paragraph break
            if not line.strip():
                if cur_arch is not None and cur_arch_body and cur_arch_body[-1] != '':
                    cur_arch_body.append('')
                continue
    if cur:
        commit_arch()
        cats.append(cur)
    return cats


def joined_body(lines_list):
    """Join collected body lines into the final body_en (preserving paragraph breaks)."""
    return '\n'.join(lines_list).strip()


def apply(cats_data, chunks_data):
    """Apply parsed chunks to the live categories array. Returns stats."""
    stats = {'cats_seen': 0, 'cats_updated': 0, 'items_updated': 0, 'archs_updated': 0,
             'defaults_updated': 0, 'cats_missing': [], 'mismatches': []}
    by_id = {c.get('id'): c for c in cats_data}
    for chunk in chunks_data:
        for parsed in chunk:
            stats['cats_seen'] += 1
            cid = parsed['id']
            live = by_id.get(cid)
            if not live:
                stats['cats_missing'].append(cid)
                continue
            # Sanity: item & archetype counts must match
            if len(parsed['items']) != len(live.get('items') or []):
                stats['mismatches'].append(f'{cid}: items {len(parsed["items"])} vs {len(live.get("items") or [])}')
                continue
            if len(parsed['archetypes']) != len(live.get('archetypes') or []):
                stats['mismatches'].append(f'{cid}: archetypes {len(parsed["archetypes"])} vs {len(live.get("archetypes") or [])}')
                continue
            # Apply category-level
            cat_changed = False
            if parsed['name_en'] and live.get('name_en') != parsed['name_en']:
                live['name_en'] = parsed['name_en']
                cat_changed = True
            if parsed['blurb_en'] and live.get('blurb_en') != parsed['blurb_en']:
                live['blurb_en'] = parsed['blurb_en']
                cat_changed = True
            # Items by index
            for i, p_it in enumerate(parsed['items']):
                live_it = (live.get('items') or [])[i]
                if p_it['name_en'] and live_it.get('name_en') != p_it['name_en']:
                    live_it['name_en'] = p_it['name_en']
                    stats['items_updated'] += 1
                if p_it['ctx_en'] and live_it.get('ctx_en') != p_it['ctx_en']:
                    live_it['ctx_en'] = p_it['ctx_en']
                    stats['items_updated'] += 1
            # Archetypes by index
            for i, p_ar in enumerate(parsed['archetypes']):
                live_ar = (live.get('archetypes') or [])[i]
                if p_ar['name_en'] and live_ar.get('name_en') != p_ar['name_en']:
                    live_ar['name_en'] = p_ar['name_en']
                    stats['archs_updated'] += 1
                if p_ar['body_en'] and live_ar.get('body_en') != p_ar['body_en']:
                    live_ar['body_en'] = p_ar['body_en']
                    stats['archs_updated'] += 1
            # Default archetype
            if parsed['default']:
                live_d = live.get('defaultArchetype') or {}
                if live_d:
                    if parsed['default']['name_en'] and live_d.get('name_en') != parsed['default']['name_en']:
                        live_d['name_en'] = parsed['default']['name_en']
                        stats['defaults_updated'] += 1
                    if parsed['default']['body_en'] and live_d.get('body_en') != parsed['default']['body_en']:
                        live_d['body_en'] = parsed['default']['body_en']
                        stats['defaults_updated'] += 1
            if cat_changed:
                stats['cats_updated'] += 1
    return stats


def main():
    chunks = sorted(CHUNKS_DIR.glob('EN_CHUNK_*_categories_edited.md'))
    print(f'Found {len(chunks)} category chunks')

    parsed_chunks = []
    for chunk in chunks:
        text = chunk.read_text(encoding='utf-8')
        cats = parse_chunk(text)
        print(f'  {chunk.name}: parsed {len(cats)} categories')
        parsed_chunks.append(cats)

    raw = json.loads(CATS_PATH.read_text(encoding='utf-8'))
    cats_data = raw.get('categories') if isinstance(raw, dict) else raw

    stats = apply(cats_data, parsed_chunks)

    # Backup + write
    ts = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    bak = CATS_PATH.with_name(f'categories.json.bak.editor_chunks.{ts}')
    shutil.copy2(CATS_PATH, bak)
    tmp = CATS_PATH.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(CATS_PATH)

    print()
    print(f'Backup: {bak.name}')
    print(f'Categories seen: {stats["cats_seen"]}')
    print(f'Category-level fields updated: {stats["cats_updated"]}')
    print(f'Item fields updated:           {stats["items_updated"]}')
    print(f'Archetype fields updated:      {stats["archs_updated"]}')
    print(f'Default-archetype fields:      {stats["defaults_updated"]}')
    if stats['cats_missing']:
        print(f'Missing in JSON: {stats["cats_missing"]}')
    if stats['mismatches']:
        print(f'Skipped (count mismatch):')
        for m in stats['mismatches']:
            print(f'  {m}')


if __name__ == '__main__':
    main()
