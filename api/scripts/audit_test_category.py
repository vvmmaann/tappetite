"""Independent audit of agent-generated category against T1-T6 + tier scoring."""
import json
import itertools
from collections import Counter
from pathlib import Path

import sys
CAT_FILE = Path(sys.argv[1] if len(sys.argv) > 1 else 'test_generated_category.json')


def score_archetype(arch, top1, top2, top3):
    triggers = set(arch.get('triggers') or [])
    s = 0
    if top1 in triggers: s += 3
    if top2 and top2 in triggers: s += 2
    if top3 and top3 in triggers: s += 1
    return s


def winning_archetype(cat, top1, top2, top3):
    archs = cat.get('archetypes') or []
    if not archs:
        return '<no-archs>'
    scored = [(a['name'], score_archetype(a, top1, top2, top3)) for a in archs]
    scored.sort(key=lambda x: -x[1])
    a_name, a_score = scored[0]
    b_name, b_score = scored[1] if len(scored) > 1 else (None, 0)
    if a_score >= 5:
        return a_name
    if a_score >= 3 and b_score >= 2:
        return f'[hybrid: {a_name} x {b_name}]'
    return f'[default: {(cat.get("defaultArchetype") or {}).get("name", "?")}]'


def main():
    cat = json.loads(CAT_FILE.read_text(encoding='utf-8'))

    items = cat.get('items') or []
    archs = cat.get('archetypes') or []
    item_ids = [it['id'] for it in items]

    print(f'Category: {cat.get("name")} (id: {cat.get("id")})')
    print(f'  items: {len(items)}, archetypes: {len(archs)}')
    print(f'  cluster: {cat.get("cluster")}, type: {cat.get("category_type")}/{cat.get("category_subtype")}')
    print()

    # T1+T2: per-item appearance count
    appearance = Counter()
    for a in archs:
        for tid in (a.get('triggers') or []):
            appearance[tid] += 1

    print('=== T1+T2: per-item trigger count ===')
    dead = []
    overload = []
    counts_breakdown = Counter()
    for iid in item_ids:
        c = appearance.get(iid, 0)
        counts_breakdown[c] += 1
        if c == 0:
            dead.append(iid)
        elif c >= 3:
            overload.append((iid, c))
    print(f'  count=0 (DEAD):       {counts_breakdown[0]}  {dead if dead else ""}')
    print(f'  count=1 (good):       {counts_breakdown[1]}')
    print(f'  count=2 (good, max):  {counts_breakdown[2]}')
    print(f'  count=3+ (OVERLOAD):  {sum(counts_breakdown[k] for k in counts_breakdown if k >= 3)}  {overload if overload else ""}')
    t1_pass = len(dead) == 0
    t2_pass = len(overload) == 0
    print(f'  T1 (no dead items):    {"PASS" if t1_pass else "FAIL"}')
    print(f'  T2 (no overload):      {"PASS" if t2_pass else "FAIL"}')
    print()

    # T3: per-archetype trigger length
    print('=== T3: per-archetype trigger length ===')
    t3_pass = True
    for a in archs:
        n = len(a.get('triggers') or [])
        ok = 2 <= n <= 5
        if not ok: t3_pass = False
        print(f'  {a["name"]:30s}  triggers={n}  {"ok" if ok else "FAIL (must be 2-5)"}')
    print(f'  T3 (all archs 2-5):    {"PASS" if t3_pass else "FAIL"}')
    print()

    # T4: pairwise overlap between archetypes
    print('=== T4: pairwise trigger overlap ===')
    t4_pass = True
    worst = (0.0, '', '')
    for i, a in enumerate(archs):
        for b in archs[i+1:]:
            sa, sb = set(a.get('triggers') or []), set(b.get('triggers') or [])
            if not sa or not sb: continue
            common = sa & sb
            # use jaccard-style: common / smaller-of-two
            denom = min(len(sa), len(sb))
            ratio = len(common) / denom if denom else 0
            if ratio > worst[0]:
                worst = (ratio, a['name'], b['name'])
            if ratio > 0.50:
                t4_pass = False
                print(f'  FAIL: "{a["name"]}" vs "{b["name"]}" overlap = {len(common)}/{denom} = {ratio:.0%}')
    print(f'  worst pair: "{worst[1]}" vs "{worst[2]}" = {worst[0]:.0%}')
    print(f'  T4 (no pair >50% overlap): {"PASS" if t4_pass else "FAIL"}')
    print()

    # Tier-scoring simulation: what % of top-3 combinations land where?
    print('=== TIER-SCORING SIMULATION (all C(N,3) ordered top-3 combos) ===')
    outcomes = Counter()
    sample = item_ids  # use all items
    for top1, top2, top3 in itertools.permutations(sample, 3):
        outcomes[winning_archetype(cat, top1, top2, top3)] += 1
    total = sum(outcomes.values())

    sorted_out = outcomes.most_common()
    top_arch, top_count = sorted_out[0]
    top_pct = round(100 * top_count / total)

    default_count = sum(c for n, c in sorted_out if n.startswith('[default'))
    default_pct = round(100 * default_count / total)
    hybrid_count = sum(c for n, c in sorted_out if n.startswith('[hybrid'))
    hybrid_pct = round(100 * hybrid_count / total)
    clear_count = total - default_count - hybrid_count
    clear_pct = round(100 * clear_count / total)

    print(f'  total combos:         {total}')
    print(f'  clear archetype wins: {clear_count} ({clear_pct}%)')
    print(f'  hybrid synthesis:     {hybrid_count} ({hybrid_pct}%)')
    print(f'  default fallback:     {default_count} ({default_pct}%)')
    print()
    print(f'  top winner: "{top_arch}" — {top_pct}% of all combos')
    print()
    print('  Top 8 outcomes:')
    for name, cnt in sorted_out[:8]:
        pct = round(100 * cnt / total)
        print(f'    {pct:>3d}%  {name}')

    # Severity verdict
    print()
    print('=== VERDICT ===')
    severity = 0
    flags = []
    if top_pct >= 40 and not top_arch.startswith('[default'):
        severity += 2
        flags.append(f'COLLAPSE: "{top_arch}" wins {top_pct}%')
    if default_pct >= 40:
        severity += 1
        flags.append(f'DEFAULT-FALLBACK: {default_pct}% land on default')
    if dead:
        severity += 1
        flags.append(f'DEAD ITEMS: {len(dead)}')
    if overload:
        severity += 1
        flags.append(f'OVERLOADED: {len(overload)}')
    if flags:
        print(f'  Severity: {severity}')
        for f in flags:
            print(f'    - {f}')
    else:
        print(f'  Severity: 0 (CLEAN)')
        print(f'  All audit checks passed.')


if __name__ == '__main__':
    main()
