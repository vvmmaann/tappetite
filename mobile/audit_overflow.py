"""UI overflow audit for Tappetite (live https://isverifiedby.me).

For each (scene, lang) pair: navigate, screenshot, then run a JS sweep that
finds elements whose scrollWidth > clientWidth or scrollHeight > clientHeight,
and prints what spilled. Worst-case categories chosen for stress testing
(longest names in dataset).

Output: screenshots/audit_overflow_<scene>_<lang>.png + JSON report on stdout.
"""
import sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

OUT = Path(__file__).parent / 'screenshots'
OUT.mkdir(exist_ok=True)
VIEWPORT = {'width': 360, 'height': 640}
DEVICE_SCALE = 3
BASE = 'https://isverifiedby.me'

# JS that walks every visible element on screen and reports overflow.
# Skips: invisible elements (display none / 0 size), scroll containers
# we know are intentionally scrollable, off-screen siblings of inactive screens.
OVERFLOW_PROBE = r"""
(() => {
  const out = [];
  // Only inspect elements inside the currently active screen + global overlays
  const roots = [
    ...document.querySelectorAll('.screen.active'),
    ...document.querySelectorAll('.modal-overlay:not([style*="display: none"])'),
    ...document.querySelectorAll('.toast'),
    ...document.querySelectorAll('.welcome-overlay:not(.hide)'),
    ...document.querySelectorAll('.onboard-overlay:not(.hide)'),
    ...document.querySelectorAll('#registerPrompt'),
  ];
  // Allowlist: elements that are MEANT to scroll (lists, etc.)
  const SCROLL_OK = new Set([
    'clusterThemeList', 'homeThemeList', 'themeList',
    'historyList', 'achievementsList', 'submitItemsList',
    'sharePreview',
  ]);
  function walk(node) {
    if (!(node instanceof Element)) return;
    const cs = getComputedStyle(node);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const w = node.clientWidth, h = node.clientHeight;
    if (w === 0 && h === 0) return;
    // Skip elements with their own scrollbar (they're allowed to overflow internally)
    const overX = cs.overflowX, overY = cs.overflowY;
    const scrollableX = overX === 'auto' || overX === 'scroll';
    const scrollableY = overY === 'auto' || overY === 'scroll';
    if (!SCROLL_OK.has(node.id)) {
      if (!scrollableX && node.scrollWidth > w + 1) {
        out.push({
          tag: node.tagName.toLowerCase(),
          id: node.id || null,
          cls: node.className && node.className.toString ? node.className.toString().slice(0, 80) : null,
          axis: 'x',
          scrollW: node.scrollWidth, clientW: w,
          text: (node.textContent || '').trim().slice(0, 80),
        });
      }
      if (!scrollableY && node.scrollHeight > h + 1) {
        // Suppress containers whose oversize is just because a child was tracked above.
        out.push({
          tag: node.tagName.toLowerCase(),
          id: node.id || null,
          cls: node.className && node.className.toString ? node.className.toString().slice(0, 80) : null,
          axis: 'y',
          scrollH: node.scrollHeight, clientH: h,
          text: (node.textContent || '').trim().slice(0, 80),
        });
      }
    }
    for (const c of node.children) walk(c);
  }
  for (const r of roots) walk(r);
  return out;
})()
"""


def shoot(page, name):
    out = OUT / f'{name}.png'
    page.screenshot(path=str(out), full_page=False)
    return out.name


def probe(page):
    return page.evaluate(OVERFLOW_PROBE)


def boot_ctx(p, lang):
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport=VIEWPORT,
        device_scale_factor=DEVICE_SCALE,
        is_mobile=True,
        has_touch=True,
        locale='en-US' if lang == 'en' else 'ru-RU',
    )
    ctx.add_init_script(f"""
        try {{
          localStorage.setItem('upg.welcome.seen.v1', '1');
          localStorage.setItem('upg.onboard.seen.v1', '1');
          localStorage.setItem('upg.lang', '{lang}');
          localStorage.setItem('upg.user', JSON.stringify({{
            id: 'guest_overflow_audit',
            nickname: 'verylongnickname_test',
            is_guest: true,
            avatarGlyph: '★',
            createdAt: new Date().toISOString(),
            theme: 'light'
          }}));
        }} catch (e) {{}}
    """)
    return browser, ctx


# Categories chosen for stress: longest item names + longest category titles.
# adult_truth has 51-char Russian items / 60-char English items — biggest hammer.
# weird_animals = the user-flagged "Самые странные животные Земли" case.
# hollywood_actors_50plus = realistic mid-length names with ctx subtitle.
# ru_classic_memes = longest EN category name (51 chars).
# your_real_profession = long category name.
WORST_CATS = {
    'adult_truth': 'longest items (51-char RU / 60-char EN)',
    'weird_animals': 'long category title in RU',
    'ru_classic_memes': 'longest EN category title (51 chars)',
    'hollywood_actors_50plus': 'people names with ctx subtitle',
    'night_films': 'long film titles like "Lord of the Rings: Return of the King"',
}


def play_to_result(page, max_clicks=22):
    """Click cardA until result screen activates."""
    for _ in range(max_clicks):
        on_result = page.evaluate("document.getElementById('screen-result').classList.contains('active')")
        if on_result:
            return True
        try:
            page.locator('#cardA').click(timeout=2000)
            page.wait_for_timeout(180)
        except Exception:
            return False
    return False


def audit_lang(lang, p, report):
    print(f'=== AUDIT lang={lang} ===')
    browser, ctx = boot_ctx(p, lang)
    page = ctx.new_page()
    page.goto(f'{BASE}/?fakemobile=1' + ('&l=en' if lang == 'en' else ''),
              wait_until='domcontentloaded')
    page.wait_for_selector('.cluster-card', state='visible', timeout=15000)
    page.wait_for_timeout(1500)

    def check(scene, wait=400):
        page.wait_for_timeout(wait)
        fn = shoot(page, f'audit_overflow_{scene}_{lang}')
        results = probe(page)
        # filter low-signal: oversize by < 4 px isn't visible
        results = [r for r in results
                   if (r.get('axis') == 'x' and (r.get('scrollW', 0) - r.get('clientW', 0) >= 2))
                   or (r.get('axis') == 'y' and (r.get('scrollH', 0) - r.get('clientH', 0) >= 2))]
        # collapse near-dup parent/child reports of same overflow text
        for r in results:
            r['scene'] = scene
            r['lang'] = lang
        report.extend(results)
        flag = '!!' if results else 'ok'
        print(f'  [{flag}] {scene} -> {fn} (overflows={len(results)})')

    # 1. Home
    check('home_default')

    # 2. Open a cluster (use 'Психология' which has many themes incl. adult_truth)
    page.evaluate("openCluster('Психология')")
    try:
        page.wait_for_selector('.toc-row', state='visible', timeout=5000)
    except Exception:
        pass
    check('cluster_psychology', wait=600)

    # 2b. Cluster with longest titles
    page.evaluate("openCluster('Кино')")
    try:
        page.wait_for_selector('.toc-row', state='visible', timeout=5000)
    except Exception:
        pass
    check('cluster_kino', wait=600)

    # 3. Battle screen — adult_truth (longest items)
    page.evaluate("startTournament('adult_truth')")
    page.wait_for_selector('#cardA .name', state='visible', timeout=5000)
    check('battle_adult_truth_round1', wait=900)

    # play a couple of rounds to expose different name pairs
    for i in range(3):
        try:
            page.locator('#cardA').click(timeout=2000)
            page.wait_for_timeout(250)
        except Exception:
            break
    check('battle_adult_truth_round4', wait=400)

    # 4. Result screen — adult_truth (worst-case hero name)
    play_to_result(page)
    page.wait_for_timeout(2500)
    page.evaluate("""
        try { const rp = document.getElementById('registerPrompt');
              if (rp) rp.style.display = 'none'; } catch (e) {}
    """)
    check('result_adult_truth', wait=600)

    # 5. Battle — weird_animals (the user's reported "Плоскоземельщики" type case)
    page.evaluate("startTournament('weird_animals')")
    page.wait_for_selector('#cardA .name', state='visible', timeout=5000)
    check('battle_weird_animals', wait=900)

    play_to_result(page)
    page.wait_for_timeout(2500)
    page.evaluate("""
        try { const rp = document.getElementById('registerPrompt');
              if (rp) rp.style.display = 'none'; } catch (e) {}
    """)
    check('result_weird_animals', wait=600)

    # 6. Share screen for the result we just have
    try:
        page.evaluate('renderShareScreen()')
        check('share_weird_animals', wait=800)
    except Exception as e:
        print(f'  [skip] share: {type(e).__name__} {e}')

    # 7. Battle — hollywood_actors_50plus (realistic name+ctx)
    page.evaluate("startTournament('hollywood_actors_50plus')")
    page.wait_for_selector('#cardA .name', state='visible', timeout=5000)
    check('battle_hollywood', wait=900)

    # 8. Profile
    page.evaluate("showScreen('profile'); renderProfile();")
    check('profile', wait=900)

    # 9. Submit
    page.evaluate("showScreen('submit')")
    check('submit', wait=800)

    # 10. Force-show registerPrompt (guest CTA)
    try:
        page.evaluate("""
            const rp = document.getElementById('registerPrompt');
            if (rp) rp.style.display = '';
        """)
        check('register_prompt', wait=400)
    except Exception:
        pass

    # 11. Onboarding overlay (if available — clear seen flag and show)
    try:
        page.evaluate("""
            try {
              localStorage.removeItem('upg.onboard.seen.v1');
              if (typeof showOnboarding === 'function') showOnboarding();
              else {
                const ov = document.querySelector('.onboard-overlay');
                if (ov) ov.classList.remove('hide');
              }
            } catch (e) {}
        """)
        page.wait_for_timeout(500)
        check('onboarding', wait=400)
    except Exception:
        pass

    ctx.close()
    browser.close()


def main():
    report = []
    with sync_playwright() as p:
        for lang in ('ru', 'en'):
            audit_lang(lang, p, report)

    # Dump JSON report so we can diff later
    rpt_path = OUT / 'audit_overflow_report.json'
    rpt_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print()
    print(f'Report -> {rpt_path}')
    print(f'Total overflow findings: {len(report)}')
    # Group by scene/lang for terse review
    by = {}
    for r in report:
        k = f"{r['scene']} [{r['lang']}]"
        by.setdefault(k, []).append(r)
    for k, items in sorted(by.items()):
        print(f'\n  {k}: {len(items)} elem(s)')
        for it in items[:5]:
            label = f"{it.get('id') or it.get('cls') or it['tag']}"
            extra = (f"x:{it['scrollW']}/{it['clientW']}" if it['axis'] == 'x'
                     else f"y:{it['scrollH']}/{it['clientH']}")
            txt = it['text'][:50].replace('\n', ' ')
            print(f"    - <{it['tag']}> {label[:50]} {extra} text={txt!r}")


if __name__ == '__main__':
    main()
