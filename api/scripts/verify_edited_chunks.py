"""Verify the editor-AI's work without applying anything yet.

Checks per chunk:
  1. Editorial notes present?
  2. Same number of UI keys / categories / items / archetypes / achievements?
  3. Any IDs (in `backticks`) lost or invented?
  4. Any RU originals (name (RU): / blurb (RU):) tampered with?
  5. Length of each individual item kept within ±25% (we want polish, not rewrite)?
  6. Spot-check a few values to read quality.

Output: stats + warnings + a couple of before/after samples.
"""
import re
from pathlib import Path
from collections import Counter

ORIG = Path('C:/Users/uncle/Claude/taste_twins/en_chunks')
EDIT = ORIG / 'edited'

CHUNKS = sorted(ORIG.glob('EN_CHUNK_*.md'))

# Patterns
KEY_LINE = re.compile(r'^\|\s*`([a-zA-Z0-9_.\-]+)`\s*\|\s*(.*?)\s*\|\s*$')
H3_CAT   = re.compile(r'^### (.+)$')
ID_LINE  = re.compile(r'^- \*\*id:\*\* `([^`]+)`')
NAME_RU  = re.compile(r'^- \*\*name \(RU\):\*\* (.+)$')
BLURB_RU = re.compile(r'^- \*\*blurb \(RU\):\*\* (.+)$')
ITEM_LINE = re.compile(r'^(\d+)\. \*\*([^*]+)\*\*(?: — (.+))?$')
ARCH_LINE = re.compile(r'^\*\*(.+?)\*\*$')


def parse_ui(text):
    keys = {}
    for line in text.splitlines():
        m = KEY_LINE.match(line)
        if m:
            keys[m.group(1)] = m.group(2)
    return keys


def parse_categories(text):
    """Returns list of dicts: {id, name (header), name_ru, blurb_ru, items, archetypes, default}."""
    cats = []
    cur = None
    in_items = False
    in_archs = False
    archetype_collecting = None
    archetype_body = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        h = H3_CAT.match(line)
        if h and not h.group(1).lower().startswith('achievements'):
            if cur:
                cats.append(cur)
            cur = {'h3_name': h.group(1), 'id': None, 'name_ru': None, 'blurb_ru': None,
                   'items': [], 'archetypes': [], 'default': None}
            in_items = False
            in_archs = False
            i += 1
            continue
        if cur is None:
            i += 1
            continue
        m = ID_LINE.match(line)
        if m:
            cur['id'] = m.group(1)
        m = NAME_RU.match(line)
        if m:
            cur['name_ru'] = m.group(1)
        m = BLURB_RU.match(line)
        if m:
            cur['blurb_ru'] = m.group(1)
        if line.startswith('#### Items'):
            in_items = True; in_archs = False
        elif line.startswith('#### Archetypes'):
            in_items = False; in_archs = True
        elif line.startswith('---'):
            in_items = False; in_archs = False
        elif in_items:
            m = ITEM_LINE.match(line)
            if m:
                cur['items'].append({'name': m.group(2).strip(), 'ctx': (m.group(3) or '').strip()})
        elif in_archs:
            m = ARCH_LINE.match(line)
            if m:
                name = m.group(1)
                if name.startswith('Default archetype: '):
                    cur['default'] = {'name': name.replace('Default archetype: ', ''), 'body': []}
                else:
                    cur['archetypes'].append({'name': name, 'body': []})
        i += 1
    if cur:
        cats.append(cur)
    return cats


def parse_achievements(text):
    achs = []
    for line in text.splitlines():
        # | `id` | icon | name | desc |
        if line.startswith('| `') and ' | ' in line:
            parts = [p.strip() for p in line.strip('|').split('|')]
            if len(parts) == 4 and parts[0].startswith('`'):
                achs.append({'id': parts[0].strip('`'), 'icon': parts[1],
                             'name': parts[2], 'desc': parts[3]})
    return achs


def report_chunk(orig_path, edit_path):
    out = []
    out.append(f"\n{'='*72}\n{orig_path.name}  vs  {edit_path.name}\n{'='*72}")

    if not edit_path.exists():
        out.append('  MISSING: edited file does not exist')
        return out, {'errors': 1, 'warnings': 0}

    o = orig_path.read_text(encoding='utf-8')
    e = edit_path.read_text(encoding='utf-8')

    errors = []
    warnings = []
    notes = []

    # Editorial notes present?
    if 'Editorial notes' in e or 'Significant changes' in e or 'editorial notes' in e.lower():
        notes.append('OK: editorial notes section present')
    else:
        warnings.append('WARN: no editorial notes section found')

    # Detect chunk type
    is_ui = '## 1. UI strings' in o
    is_ach = '## 3. Achievements' in o
    is_cats = '## 2. Categories' in o

    if is_ui:
        ok = parse_ui(o)
        ek = parse_ui(e)
        out.append(f'  UI strings: original {len(ok)} -> edited {len(ek)}')
        # Check key sets
        only_orig = set(ok) - set(ek)
        only_edit = set(ek) - set(ok)
        if only_orig:
            errors.append(f'LOST KEYS: {len(only_orig)} (e.g. {sorted(only_orig)[:5]})')
        if only_edit:
            errors.append(f'INVENTED KEYS: {len(only_edit)} (e.g. {sorted(only_edit)[:5]})')
        # Sample 3 changed values
        changed = []
        for k in sorted(ok):
            if k in ek and ok[k] != ek[k]:
                changed.append((k, ok[k], ek[k]))
        out.append(f'  Changed values: {len(changed)} of {len(ok)} ({100 * len(changed) // max(1, len(ok))}%)')
        if changed:
            out.append('  Sample edits:')
            for k, a, b in changed[:5]:
                out.append(f'    `{k}`')
                out.append(f'      - {a!r}')
                out.append(f'      + {b!r}')
        unchanged_pct = 100 - (100 * len(changed) // max(1, len(ok)))
        if unchanged_pct > 95:
            warnings.append(f'WARN: only {len(changed)} keys changed (lazy editor?)')

    if is_cats:
        oc = parse_categories(o)
        ec = parse_categories(e)
        out.append(f'  Categories: original {len(oc)} -> edited {len(ec)}')
        if len(oc) != len(ec):
            errors.append(f'COUNT MISMATCH: {len(oc)} vs {len(ec)} categories')

        # Match by id
        oc_by_id = {c['id']: c for c in oc if c['id']}
        ec_by_id = {c['id']: c for c in ec if c['id']}
        lost = set(oc_by_id) - set(ec_by_id)
        gained = set(ec_by_id) - set(oc_by_id)
        if lost:
            errors.append(f'LOST CATEGORY IDS: {len(lost)} ({sorted(lost)[:3]}...)')
        if gained:
            errors.append(f'INVENTED CATEGORY IDS: {len(gained)}')

        # Per-category checks
        ru_changed = 0
        item_count_mismatch = 0
        arch_count_mismatch = 0
        names_unchanged = 0
        sample_diffs = []
        for cid, oc_d in oc_by_id.items():
            if cid not in ec_by_id: continue
            ec_d = ec_by_id[cid]
            # RU originals must be untouched
            if oc_d['name_ru'] != ec_d['name_ru']:
                ru_changed += 1
            if oc_d['blurb_ru'] != ec_d['blurb_ru']:
                ru_changed += 1
            # Item count
            if len(oc_d['items']) != len(ec_d['items']):
                item_count_mismatch += 1
            # Archetype count
            if len(oc_d['archetypes']) != len(ec_d['archetypes']):
                arch_count_mismatch += 1
            # Sample some name diffs
            if oc_d['h3_name'] == ec_d['h3_name']:
                names_unchanged += 1
            else:
                if len(sample_diffs) < 3:
                    sample_diffs.append((oc_d['h3_name'], ec_d['h3_name']))

        if ru_changed:
            errors.append(f'RU ORIGINALS TOUCHED in {ru_changed} fields (must be context-only!)')
        if item_count_mismatch:
            errors.append(f'ITEM COUNT MISMATCH in {item_count_mismatch} categories')
        if arch_count_mismatch:
            errors.append(f'ARCHETYPE COUNT MISMATCH in {arch_count_mismatch} categories')

        unchanged_pct = 100 * names_unchanged // max(1, len(oc_by_id))
        out.append(f'  Category names: {len(oc_by_id) - names_unchanged} of {len(oc_by_id)} edited ({100 - unchanged_pct}%)')
        if sample_diffs:
            out.append('  Sample H3 edits:')
            for a, b in sample_diffs:
                out.append(f'    - {a}')
                out.append(f'    + {b}')
        if unchanged_pct > 90:
            warnings.append(f'WARN: only {len(oc_by_id) - names_unchanged} category names changed')

    if is_ach:
        oa = parse_achievements(o)
        ea = parse_achievements(e)
        out.append(f'  Achievements: original {len(oa)} -> edited {len(ea)}')
        if len(oa) != len(ea):
            errors.append(f'COUNT MISMATCH: {len(oa)} vs {len(ea)}')
        oa_by_id = {a['id']: a for a in oa}
        ea_by_id = {a['id']: a for a in ea}
        if set(oa_by_id) != set(ea_by_id):
            errors.append('ACHIEVEMENT IDS DIFFER')
        else:
            changed = sum(1 for k in oa_by_id if oa_by_id[k]['name'] != ea_by_id[k]['name'] or oa_by_id[k]['desc'] != ea_by_id[k]['desc'])
            out.append(f'  Achievements changed: {changed}/{len(oa_by_id)}')
            for k in sorted(oa_by_id):
                if oa_by_id[k]['name'] != ea_by_id[k]['name'] or oa_by_id[k]['desc'] != ea_by_id[k]['desc']:
                    out.append(f'    `{k}` name: {oa_by_id[k]["name"]!r} -> {ea_by_id[k]["name"]!r}')

    # Notes / errors / warnings
    if notes: out.extend(['  ' + n for n in notes])
    if warnings: out.extend(['  ' + w for w in warnings])
    if errors: out.extend(['  ' + 'X ERROR: ' + e for e in errors])
    return out, {'errors': len(errors), 'warnings': len(warnings)}


def main():
    total_errors = 0
    total_warnings = 0
    full_report = []
    for orig in CHUNKS:
        edit = EDIT / orig.name.replace('.md', '_edited.md')
        out, stats = report_chunk(orig, edit)
        full_report.extend(out)
        total_errors += stats['errors']
        total_warnings += stats['warnings']
    full_report.append(f'\n{"="*72}\nTOTAL: {total_errors} errors / {total_warnings} warnings')
    out_text = '\n'.join(full_report)
    out_path = Path('C:/Users/uncle/Claude/taste_twins/_chunk_verify_report.txt')
    out_path.write_text(out_text, encoding='utf-8')
    print(f'Wrote {out_path}')
    print(f'Total: {total_errors} errors / {total_warnings} warnings')


if __name__ == '__main__':
    main()
