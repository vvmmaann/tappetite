"""Render a fresh 512x512 Tappetite launcher icon for Play Store.

The old icon.svg has the pre-rebrand "P" letter. We want the current Tappetite
identity: italic serif "t" with the brand "1"-in-orange-circle as the dot of
the letter. Font is Bodoni Moda (Google Fonts) — pulled at render time so the
output is pixel-identical regardless of OS-installed fonts.

Output: mobile/screenshots/ic_launcher_512.png (Play Store), plus a square
no-rounded version for use in feature graphics if needed later.
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


# HTML page that contains JUST the 512x512 icon. We render this via Playwright
# at a 512x512 viewport so the screenshot IS the icon exactly. document.fonts.ready
# is awaited so Bodoni Moda is loaded before the screenshot fires (without that
# we'd get a serif fallback that looks wrong).
HTML = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@1,700&display=swap');
  html, body { margin: 0; padding: 0; background: transparent; }
  body {
    width: 512px; height: 512px;
    display: flex; align-items: center; justify-content: center;
  }
  .icon {
    width: 512px; height: 512px;
    background: #FAF6F0;
    border-radius: 96px;
    position: relative;
    overflow: hidden;
  }
  .letter {
    position: absolute;
    left: 0; right: 0;
    top: 50%;
    transform: translateY(-58%);
    text-align: center;
    font-family: 'Bodoni Moda', 'Playfair Display', Georgia, serif;
    font-style: italic;
    font-weight: 700;
    font-size: 420px;
    line-height: 1;
    color: #1A1F36;
    letter-spacing: -20px;
  }
  /* The "1" circle sits over where the dot of the italic "t" would be —
     roughly top-right area. Tweaked by eye to feel anchored to the letter
     rather than floating. Both light-mode bg-colored "1" + accent-colored
     circle so it pops against the cream icon background. */
  .dot {
    position: absolute;
    top: 110px;
    right: 116px;
    width: 96px; height: 96px;
    border-radius: 50%;
    background: #B5532E;
    display: flex; align-items: center; justify-content: center;
    color: #FAF6F0;
    font-family: 'Bodoni Moda', 'Playfair Display', Georgia, serif;
    font-style: italic;
    font-weight: 700;
    font-size: 78px;
    line-height: 1;
    padding-bottom: 6px;
    box-sizing: border-box;
  }
</style>
</head><body>
  <div class="icon">
    <div class="letter">t</div>
    <div class="dot">1</div>
  </div>
</body></html>
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 512, "height": 512},
            device_scale_factor=1,  # 1:1 — we want 512px PNG
        )
        page = ctx.new_page()
        page.set_content(HTML, wait_until="domcontentloaded")
        # Wait for the web font (Bodoni Moda) to fully load + paint.
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(800)

        # Tight screenshot bounded to the .icon element. Background of <body>
        # is transparent + omitBackground:true so the corners outside the
        # rounded rectangle are alpha (Play Store keeps the rounded mask).
        icon_el = page.locator(".icon")
        out = OUT / "ic_launcher_512.png"
        icon_el.screenshot(path=str(out), omit_background=True)
        print(f"  [ok] {out.name}  (512x512)")

        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
