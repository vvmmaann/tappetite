"""Capture Play Store phone screenshots in EN locale.

Mirror of capture_screenshots.py but forces EN throughout via localStorage
seed (LS_LANG=en) so every screen renders in English. Output named *_en.png
to live alongside the RU versions in the same screenshots/ folder.

Used for EN-language Play Store listing translation.
"""
import sys
from playwright.sync_api import sync_playwright
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)

VIEWPORT = {"width": 360, "height": 640}
DEVICE_SCALE = 3
BASE = "https://isverifiedby.me"


def shoot(page, name, wait_ms=500):
    page.wait_for_timeout(wait_ms)
    out = OUT / f"{name}.png"
    page.screenshot(path=str(out), full_page=False)
    print(f"  [ok] {out.name}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport=VIEWPORT,
            device_scale_factor=DEVICE_SCALE,
            is_mobile=True,
            has_touch=True,
            locale="en-US",
        )

        # Pre-seed localStorage: skip welcome+onboarding AND force EN locale.
        # LS_LANG = 'upg.lang' is what detectInitialLang reads first; setting it
        # to 'en' bypasses the URL/browser-locale detection chain.
        ctx.add_init_script("""
            try {
              localStorage.setItem('upg.welcome.seen.v1', '1');
              localStorage.setItem('upg.onboard.seen.v1', '1');
              localStorage.setItem('upg.lang', 'en');
              localStorage.setItem('upg.user', JSON.stringify({
                id: 'guest_demo',
                nickname: 'demo',
                is_guest: true,
                avatarGlyph: '★',
                createdAt: new Date().toISOString(),
                theme: 'light'
              }));
            } catch (e) {}
        """)

        page = ctx.new_page()

        # Boot in EN
        print("-> boot (EN)")
        page.goto(f"{BASE}/?fakemobile=1&l=en", wait_until="domcontentloaded")
        page.wait_for_selector('.cluster-card', state='visible', timeout=15000)
        page.wait_for_timeout(1500)

        # 1. HOME
        print("-> 01 home")
        shoot(page, "01_home_en", wait_ms=500)

        # 2. CLUSTER — Movies (was Кино in RU)
        # In EN, cluster names are translated via the cluster.<RuName> i18n
        # keys. openCluster() takes the original Russian name as ID though,
        # since clusters are stored RU-side; rendering localizes via
        # localizedCluster().
        print("-> 02 cluster (Movies)")
        page.evaluate("openCluster('Кино')")
        try:
            page.wait_for_selector('.toc-row', state='visible', timeout=5000)
        except Exception:
            pass
        shoot(page, "02_cluster_en", wait_ms=800)

        # 3. BATTLE — Hollywood actors (recognizable to EN audience)
        print("-> 03 battle (hollywood actors)")
        page.evaluate("startTournament('hollywood_actors_50plus')")
        try:
            page.wait_for_selector('#cardA .name', state='visible', timeout=5000)
        except Exception:
            pass
        shoot(page, "03_battle_en", wait_ms=1500)

        # 4. PROFILE
        print("-> 04 profile")
        page.evaluate("showScreen('profile'); renderProfile();")
        shoot(page, "04_profile_en", wait_ms=1500)

        # 5. SUBMIT
        print("-> 05 submit")
        page.evaluate("showScreen('submit')")
        shoot(page, "05_submit_en", wait_ms=1200)

        # 6. RESULT — play through 16-item tournament with deterministic A-clicks
        print("-> 06 result (play-through)")
        page.evaluate("setLang('en'); showScreen('home'); renderHome();")
        page.wait_for_timeout(800)
        page.evaluate("startTournament('hollywood_actors_50plus')")
        try:
            page.wait_for_selector('#cardA', state='visible', timeout=5000)
        except Exception:
            pass
        for i in range(20):
            on_result = page.evaluate("document.getElementById('screen-result').classList.contains('active')")
            if on_result:
                break
            try:
                page.locator('#cardA').click(timeout=2000)
                page.wait_for_timeout(180)
            except Exception:
                break
        page.wait_for_timeout(2500)
        # Dismiss the first-result celebration if it appeared
        page.evaluate("""
            try {
              const rp = document.getElementById('registerPrompt');
              if (rp) rp.style.display = 'none';
            } catch (e) {}
        """)
        shoot(page, "06_result_en", wait_ms=500)

        ctx.close()
        browser.close()
        print()
        print(f"Saved EN set to: {OUT}")


if __name__ == "__main__":
    main()
