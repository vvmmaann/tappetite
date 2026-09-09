"""Audit ALL live categories against T1-T6 + tier-scoring logic.

Usage:
  python audit_live_full.py [path/to/categories.json]

If no arg given, defaults to ./categories_live.json (which moderator-machine
audits typically scp from prod). The report header includes SHA256 of the
input file so the reviewer can verify the audit was run against the exact
production data, not a stale local copy.

Output: a ranked report (severity descending). Writes UTF-8 file so Russian renders.

Tier-simulation note: for each category we permute through the FIRST 12 items
(yields up to ~1320 top-3 combos) — fast and stable. The summary clearly
labels this as "first-12 sample". For full enumeration on a single large cat
(e.g. night_films 64 items = 249984 combos), use the inline simulator in
fix_night_films.py / individual cat scripts.
"""
import json
import itertools
import sys
import io
import hashlib
from collections import Counter
from pathlib import Path

CATS = Path(sys.argv[1] if len(sys.argv) > 1 else 'categories_live.json')
OUT = Path('audit_live_report.txt')

# Force UTF-8 stdout (Windows cp1251 will mangle Cyrillic otherwise)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)


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


def audit_category(cat):
    items = cat.get('items') or []
    archs = cat.get('archetypes') or []
    if not items or not archs:
        return None

    item_ids = [it['id'] for it in items]
    item_id_set = set(item_ids)

    # Round-4 audit fix: mirror server-side invalid-trigger check. The server
    # validator now treats any trigger id not in items[].id as a structural
    # error, but the audit script previously counted them in `appearance`,
    # masking dead/orphaned entries. Now: collect them separately, count only
    # valid references in `appearance`.
    invalid_triggers = []
    for a in archs:
        a_name = a.get('name', '?')
        for tid in (a.get('triggers') or []):
            if tid not in item_id_set:
                invalid_triggers.append((a_name, tid))

    # T1+T2: per-item appearance count (only counts valid trigger refs)
    appearance = Counter()
    for a in archs:
        for tid in (a.get('triggers') or []):
            if tid in item_id_set:
                appearance[tid] += 1

    dead = [iid for iid in item_ids if appearance.get(iid, 0) == 0]
    overload = [(iid, appearance[iid]) for iid in item_ids if appearance[iid] >= 3]

    # T3: arch-trigger length
    bad_trigger_lens = []
    for a in archs:
        n = len(a.get('triggers') or [])
        if n < 2 or n > 5:
            bad_trigger_lens.append((a['name'], n))

    # T4: pairwise overlap
    bad_pairs = []
    for i, a in enumerate(archs):
        for b in archs[i+1:]:
            sa, sb = set(a.get('triggers') or []), set(b.get('triggers') or [])
            if not sa or not sb: continue
            common = sa & sb
            denom = min(len(sa), len(sb))
            if denom and len(common) / denom > 0.50:
                bad_pairs.append((a['name'], b['name'], len(common), denom))

    # Tier-scoring sim: SAMPLED to first-12 items per category (1320 combos
    # max). Trade-off: tractable on 100+ cats vs. exhaustive (262080 combos for
    # a 64-item cat). Sample picks first-12 from items[] which is editorial
    # order — usually the most "central" items. Hidden risk: a magnet archetype
    # whose triggers are all in items[12:] would not be detected. For one-off
    # exhaustive verification of a single cat, use individual fix scripts.
    sample = item_ids[:12] if len(item_ids) > 12 else item_ids
    outcomes = Counter()
    for top1, top2, top3 in itertools.permutations(sample, 3):
        outcomes[winning_archetype(cat, top1, top2, top3)] += 1
    total = sum(outcomes.values()) or 1

    sorted_out = outcomes.most_common()
    top_arch, top_count = sorted_out[0]
    top_pct = round(100 * top_count / total)

    default_count = sum(c for n, c in sorted_out if n.startswith('[default'))
    default_pct = round(100 * default_count / total)
    hybrid_count = sum(c for n, c in sorted_out if n.startswith('[hybrid'))
    hybrid_pct = round(100 * hybrid_count / total)
    clear_count = total - default_count - hybrid_count
    clear_pct = round(100 * clear_count / total)

    # Severity scoring
    severity = 0
    flags = []
    if top_pct >= 30 and not top_arch.startswith('[default') and not top_arch.startswith('[hybrid'):
        # Single archetype winning ≥30% = collapse
        severity += 3
        flags.append(f'COLLAPSE: «{top_arch}» = {top_pct}% всех топ-3')
    if default_pct >= 40:
        severity += 2
        flags.append(f'DEFAULT-FALLBACK: {default_pct}% уходят в default')
    if dead:
        severity += 2
        flags.append(f'DEAD ITEMS: {len(dead)} никогда не триггерят')
    if overload:
        severity += 1
        flags.append(f'OVERLOADED: {len(overload)} items в 3+ архетипах')
    if bad_trigger_lens:
        severity += 1
        flags.append(f'BAD TRIGGER COUNT: {len(bad_trigger_lens)} архетипов с триггерами вне 2-5')
    if bad_pairs:
        severity += 1
        flags.append(f'OVERLAP >50%: {len(bad_pairs)} пары архетипов сильно пересекаются')
    if invalid_triggers:
        # Invalid trigger ids = phantom triggers, never fire at runtime.
        # Critical for content integrity (mirrors server validator's structural error).
        severity += 2
        flags.append(f'INVALID TRIGGERS: {len(invalid_triggers)} ссылок на несуществующие items')

    return {
        'cat_id': cat['id'],
        'invalid_triggers': invalid_triggers,
        'cat_name': cat.get('name', '?'),
        'cluster': cat.get('cluster', '?'),
        'severity': severity,
        'flags': flags,
        'top_arch': top_arch,
        'top_pct': top_pct,
        'default_pct': default_pct,
        'hybrid_pct': hybrid_pct,
        'clear_pct': clear_pct,
        'dead': dead,
        'overload': overload,
        'bad_trigger_lens': bad_trigger_lens,
        'bad_pairs': bad_pairs,
        'distribution': sorted_out[:5],
        'n_items': len(item_ids),
        'n_archs': len(archs),
    }


def main():
    raw_bytes = CATS.read_bytes()
    raw = json.loads(raw_bytes.decode('utf-8'))
    cats = raw.get('categories') if isinstance(raw, dict) else raw

    # SHA256 of the audited file — pinned in the report header so reviewer can
    # verify the audit was run against the exact production data and not a
    # stale local copy. (Round-3 audit fix 2026-05-08.)
    file_sha = hashlib.sha256(raw_bytes).hexdigest()

    # Find "best film" specifically
    film_keywords = ['фильм', 'кино', 'movie', 'film']
    film_cats = [c for c in cats if any(k in (c.get('name', '') + c.get('blurb', '')).lower() for k in film_keywords)]

    out_lines = []
    def w(s=''):
        print(s)
        out_lines.append(s)

    w('=' * 80)
    w(f'AUDIT REPORT — {len(cats)} live categories')
    w(f'  source: {CATS.resolve()}')
    w(f'  sha256: {file_sha}')
    w(f'  bytes:  {len(raw_bytes)}')
    w(f'  tier-simulation: first-12 items per category (sample, not exhaustive)')
    w('=' * 80)
    w()

    # Special section: film-related categories first
    if film_cats:
        w('=== FILM-RELATED CATEGORIES (zoom for user complaint about dark archetype) ===')
        w()
        for c in film_cats:
            r = audit_category(c)
            if not r:
                w(f'  • {c.get("name")} (id: {c.get("id")}) — нет items/archetypes, пропуск')
                continue
            w(f'  • «{r["cat_name"]}»  (id: {r["cat_id"]}, кластер: {r["cluster"]})')
            w(f'    {r["n_items"]} items, {r["n_archs"]} архетипов')
            w(f'    severity: {r["severity"]}')
            for f in r['flags']:
                w(f'      - {f}')
            w(f'    Распределение топ-3:  чистый {r["clear_pct"]}% / гибрид {r["hybrid_pct"]}% / default {r["default_pct"]}%')
            w(f'    Топ-победитель: «{r["top_arch"]}» = {r["top_pct"]}%')
            w(f'    Топ-5 исходов:')
            for name, cnt in r['distribution']:
                pct = round(100 * cnt / sum(c2 for _, c2 in r['distribution']))
                w(f'      {pct:>3d}%  {name}')
            if r['dead']:
                w(f'    DEAD items: {r["dead"]}')
            if r['overload']:
                w(f'    OVERLOADED items: {[(i.split("-",1)[-1] if "-" in i else i, n) for i, n in r["overload"]]}')
            w()
        w()

    # Run full audit
    reports = []
    for c in cats:
        r = audit_category(c)
        if r and r['severity'] > 0:
            reports.append(r)
    reports.sort(key=lambda r: -r['severity'])

    w('=' * 80)
    w(f'FULL AUDIT — {len(reports)} категорий с проблемами из {len(cats)} живых')
    w('=' * 80)
    w()

    for r in reports:
        sev = '!' * r['severity']
        w(f'[{sev:>5s}]  «{r["cat_name"]}»  (id: {r["cat_id"]}, кластер: {r["cluster"]})')
        w(f'         {r["n_items"]} items, {r["n_archs"]} архетипов')
        for f in r['flags']:
            w(f'         - {f}')
        w(f'         распределение: чистый {r["clear_pct"]}% / гибрид {r["hybrid_pct"]}% / default {r["default_pct"]}%')
        w(f'         топ-победитель: «{r["top_arch"]}» {r["top_pct"]}%')
        if r['dead']:
            w(f'         dead: {r["dead"][:5]}{"..." if len(r["dead"]) > 5 else ""}')
        if r['overload']:
            short = [(i.split("-",1)[-1] if "-" in i else i, n) for i, n in r['overload'][:5]]
            w(f'         overload: {short}')
        w()

    # Summary
    sev_counts = Counter(r['severity'] for r in reports)
    w('=' * 80)
    w('SUMMARY')
    w('=' * 80)
    w(f'  Severity 6+ (multiple critical):  {sum(1 for r in reports if r["severity"] >= 6)} cats')
    w(f'  Severity 5 (critical):            {sev_counts.get(5, 0)} cats')
    w(f'  Severity 4 (major):               {sev_counts.get(4, 0)} cats')
    w(f'  Severity 3 (significant):         {sev_counts.get(3, 0)} cats')
    w(f'  Severity 2 (moderate):            {sev_counts.get(2, 0)} cats')
    w(f'  Severity 1 (minor):               {sev_counts.get(1, 0)} cats')
    w(f'  Clean (no issues):                {len(cats) - len(reports)} cats')
    w()
    w(f'  Categories with COLLAPSE (>=30% single winner):  {sum(1 for r in reports if any("COLLAPSE" in f for f in r["flags"]))}')
    w(f'  Categories with DEAD items:                       {sum(1 for r in reports if any("DEAD" in f for f in r["flags"]))}')
    w(f'  Categories with OVERLOADED items:                 {sum(1 for r in reports if any("OVERLOADED" in f for f in r["flags"]))}')
    w(f'  Categories with INVALID TRIGGERS (phantom ids):   {sum(1 for r in reports if any("INVALID TRIGGERS" in f for f in r["flags"]))}')
    w(f'  Categories with BAD TRIGGER COUNT (T3 violations):{sum(1 for r in reports if any("BAD TRIGGER COUNT" in f for f in r["flags"]))}')
    w(f'  Categories with OVERLAP >50% (T4 violations):     {sum(1 for r in reports if any("OVERLAP" in f for f in r["flags"]))}')

    OUT.write_text('\n'.join(out_lines), encoding='utf-8')
    print(f'\nReport saved to: {OUT.resolve()}')


if __name__ == '__main__':
    main()
