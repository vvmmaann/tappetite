"""Capture Play Store phone screenshots from the live Tappetite app.

Outputs to mobile/screenshots/ (1080x1920, 9:16 per Play Store reqs).
Headless Chromium via Playwright. Uses page.evaluate() to call internal
JS functions directly (showScreen, startTournament) rather than clicking,
which is more reliable than DOM selectors that change between revisions.
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
            locale="ru-RU",
        )

        ctx.add_init_script("""
            try {
              localStorage.setItem('upg.welcome.seen.v1', '1');
              localStorage.setItem('upg.onboard.seen.v1', '1');
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

        # Boot
        print("-> boot")
        page.goto(f"{BASE}/?fakemobile=1", wait_until="domcontentloaded")
        page.wait_for_selector('.cluster-card', state='visible', timeout=15000)
        page.wait_for_timeout(1500)  # let async fetches settle

        # ─── 1. HOME ────────────────────────────────────────────
        print("-> 01 home")
        shoot(page, "01_home", wait_ms=500)

        # ─── 2. CLUSTER ─────────────────────────────────────────
        # openCluster('Кино') jumps to that cluster directly.
        print("-> 02 cluster (Кино)")
        page.evaluate("openCluster('Кино')")
        try:
            page.wait_for_selector('.toc-row', state='visible', timeout=5000)
        except Exception as e:
            print(f"  [warn] toc-row not found: {type(e).__name__}")
        shoot(page, "02_cluster", wait_ms=800)

        # ─── 3. BATTLE ──────────────────────────────────────────
        # startTournament('hollywood_actors_50plus') puts us straight on battle.
        # Could also be 'car_type', 'spirit_animal' etc. Hollywood actors has
        # recognizable names which makes a good demo.
        print("-> 03 battle (hollywood actors)")
        page.evaluate("startTournament('hollywood_actors_50plus')")
        try:
            page.wait_for_selector('#cardA .name', state='visible', timeout=5000)
        except Exception as e:
            print(f"  [warn] cardA not found: {type(e).__name__}")
        shoot(page, "03_battle", wait_ms=1500)

        # ─── 4. PROFILE ─────────────────────────────────────────
        print("-> 04 profile")
        page.evaluate("showScreen('profile'); renderProfile();")
        shoot(page, "04_profile", wait_ms=1500)

        # ─── 5. SUBMIT ──────────────────────────────────────────
        print("-> 05 submit")
        page.evaluate("showScreen('submit')")
        shoot(page, "05_submit", wait_ms=1200)

        # ─── 6. RESULT — play through a real tournament ────────
        # tournament is `let` in game.html so we can't set it via evaluate.
        # Just play through: 16-item tournament = 15 battles + 3rd-place match.
        # Click cardA each time (deterministic — same item wins every match).
        print("-> 06 result (play-through)")
        # Switch back to RU for consistency with other shots
        page.evaluate("setLang('ru'); showScreen('home'); renderHome();")
        page.wait_for_timeout(800)
        # Start a clean tournament
        page.evaluate("startTournament('hollywood_actors_50plus')")
        try:
            page.wait_for_selector('#cardA', state='visible', timeout=5000)
        except Exception:
            pass
        # Click cardA up to 20 times. Each click triggers pickWinner. Stop when
        # we land on the result screen (#screen-result becomes active).
        for i in range(20):
            on_result = page.evaluate("document.getElementById('screen-result').classList.contains('active')")
            if on_result:
                print(f"  [info] reached result after {i} clicks")
                break
            try:
                page.locator('#cardA').click(timeout=2000)
                page.wait_for_timeout(180)  # let pickWinner + renderBattle finish
            except Exception as e:
                print(f"  [warn] click {i}: {type(e).__name__}")
                break
        # Wait for result content to fully render (archetype takes ~1s)
        page.wait_for_timeout(2500)
        # Close the registration prompt if it appeared (guest first-result)
        page.evaluate("""
            try {
              const rp = document.getElementById('registerPrompt');
              if (rp) rp.style.display = 'none';
            } catch (e) {}
        """)
        shoot(page, "06_result", wait_ms=500)

        # ─── 7. HOME EN ─────────────────────────────────────────
        print("-> 07 home EN")
        # Switch lang + return to home
        page.evaluate("setLang('en'); showScreen('home'); renderHome();")
        shoot(page, "07_home_en", wait_ms=1500)

        ctx.close()
        browser.close()
        print()
        print(f"Saved to: {OUT}")


if __name__ == "__main__":
    main()
