"""Audit archetype trigger coverage to find categories where:
  - one archetype wins disproportionately many top-3 combinations (collapse)
  - items appear in NO archetype triggers (dead items)
  - items appear in 3+ archetype triggers (semantic confusion)
  - top-3 combinations land on default-archetype (no real archetype matched)

For each category we enumerate ALL C(N,2) ordered pairs as candidate top-2 sets
and a sample of top-3 pickings, then mimic the same generateArchetype logic.

Output: a report ranked by severity.
"""
import json
import itertools
from collections import Counter, defaultdict
from pathlib import Path

CATS = Path('/opt/untitled-pick-game-api/data/categories.json')


def score_archetype(arch, top1_id, top2_id, top3_id):
    triggers = set(arch.get('triggers') or [])
    score = 0
    if top1_id in triggers: score += 3
    if top2_id and top2_id in triggers: score += 2
    if top3_id and top3_id in triggers: score += 1
    return score


def winning_archetype(cat, top1_id, top2_id, top3_id):
    """Mirror the new 3-tier logic from game.html:
       Tier 1 (score >= 5): clear winner — return its name.
       Tier 2 (a.score >= 3 AND b.score >= 2): hybrid — return synthetic name.
       Tier 3: default archetype.
    """
    archs = cat.get('archetypes') or []
    if not archs:
        return '<no archetypes>'
    scored = [(a['name'], score_archetype(a, top1_id, top2_id, top3_id)) for a in archs]
    scored.sort(key=lambda x: -x[1])
    a_name, a_score = scored[0]
    b_name, b_score = scored[1] if len(scored) > 1 else (None, 0)
    if a_score >= 5:
        return a_name
    if a_score >= 3 and b_score >= 2:
        return f'[hybrid: {a_name} × {b_name}]'
    return f'[default: {(cat.get("defaultArchetype") or {}).get("name", "?")}]'


def audit_category(cat):
    items = cat.get('items') or []
    archs = cat.get('archetypes') or []
    if not items or not archs:
        return None

    item_ids = [it['id'] for it in items]

    # Coverage per item: in how many archetypes' triggers is it?
    appearance = Counter()
    for a in archs:
        for tid in (a.get('triggers') or []):
            appearance[tid] += 1

    dead_items = [i for i in item_ids if appearance.get(i, 0) == 0]
    overloaded = [(i, appearance[i]) for i in item_ids if appearance[i] >= 3]

    # Sample top-3 outcomes: take all 3-permutations from a representative subset
    # (limit to 12 items for tractability — gives ~1320 combos per cat)
    sample_items = item_ids[:12] if len(item_ids) > 12 else item_ids
    outcomes = Counter()
    for top1, top2, top3 in itertools.permutations(sample_items, 3):
        winner = winning_archetype(cat, top1, top2, top3)
        outcomes[winner] += 1
    total = sum(outcomes.values()) or 1

    # Find dominant archetype (and default-fallback rate)
    sorted_out = outcomes.most_common()
    top_arch_name, top_count = sorted_out[0]
    top_pct = round(100 * top_count / total)

    default_count = sum(c for n, c in sorted_out if n.startswith('[default'))
    default_pct = round(100 * default_count / total)

    # Severity
    severity = 0
    flags = []
    if top_pct >= 40 and not top_arch_name.startswith('[default'):
        severity += 2
        flags.append(f'COLLAPSE: "{top_arch_name}" wins {top_pct}% of combos')
    if default_pct >= 40:
        severity += 1
        flags.append(f'DEFAULT-FALLBACK: {default_pct}% land on default')
    if dead_items:
        severity += 1
        flags.append(f'DEAD ITEMS: {len(dead_items)} never trigger any archetype')
    if overloaded:
        severity += 1
        flags.append(f'OVERLOADED: {len(overloaded)} items in 3+ archetypes')

    return {
        'cat_id': cat['id'],
        'cat_name': cat.get('name', '?'),
        'severity': severity,
        'flags': flags,
        'top_arch': top_arch_name,
        'top_pct': top_pct,
        'default_pct': default_pct,
        'dead_items': dead_items,
        'overloaded': overloaded,
        'distribution': sorted_out[:5],
        'n_items': len(item_ids),
        'n_archs': len(archs),
    }


def main():
    raw = json.loads(CATS.read_text(encoding='utf-8'))
    cats = raw.get('categories') if isinstance(raw, dict) else raw

    reports = []
    for c in cats:
        r = audit_category(c)
        if r and r['severity'] > 0:
            reports.append(r)

    reports.sort(key=lambda r: -r['severity'])

    print(f'Total categories with issues: {len(reports)} of {len(cats)}\n')
    print(f'{"="*78}')
    for r in reports:
        sev_marker = '!' * r['severity']
        print(f'\n[{sev_marker:>4s}]  {r["cat_name"]}')
        print(f'         id: {r["cat_id"]}  ({r["n_items"]} items, {r["n_archs"]} archetypes)')
        for f in r['flags']:
            print(f'         - {f}')
        print(f'         top winner: "{r["top_arch"]}" {r["top_pct"]}%')
        print(f'         distribution (top 5):')
        for name, cnt in r['distribution']:
            pct = round(100 * cnt / sum(c for _, c in r['distribution']))
            print(f'           {pct:>3d}%  {name}')
        if r['dead_items']:
            print(f'         dead items: {r["dead_items"][:5]}')
        if r['overloaded']:
            print(f'         overloaded: {[(i.split("-",1)[-1], n) for i, n in r["overloaded"][:5]]}')

    # Summary
    print(f'\n{"="*78}')
    print(f'SUMMARY')
    sev_counts = Counter(r['severity'] for r in reports)
    print(f'  Severity 4 (multiple problems):  {sev_counts.get(4, 0)} cats')
    print(f'  Severity 3:                      {sev_counts.get(3, 0)} cats')
    print(f'  Severity 2 (single major flag):  {sev_counts.get(2, 0)} cats')
    print(f'  Severity 1 (single minor flag):  {sev_counts.get(1, 0)} cats')
    print(f'  Clean (no issues):               {len(cats) - len(reports)} cats')


if __name__ == '__main__':
    main()
