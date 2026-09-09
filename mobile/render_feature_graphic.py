"""Render the 1024x500 feature graphic for Play Store listing.

2026-05-13 — second pass after the first attempt was rejected as cluttered.
Approach this time: ONE central typographic moment. The Tappetite mark (italic
serif "t" with the brand "1" circle as its dot) blown up to fill the banner.
Cream background, navy letter, terracotta accent — same palette as the icon.
No supporting cards, no decorative lines, no scattered glyphs. Just the brand.
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


HTML = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@1,400;1,700;1,900&display=swap');

  html, body { margin: 0; padding: 0; }
  body {
    width: 1024px; height: 500px;
    background: #FAF6F0;
    position: relative;
    overflow: hidden;
  }

  /* The Tappetite mark — italic serif "t" rendered at hero scale, with
     a "1"-in-thin-circle hanging above the stem as its decorative dot.
     Same composition as the app icon, scaled and balanced for landscape.
     One element, generous negative space, brand identity carries the
     whole banner. */
  .mark {
    position: absolute;
    left: 50%;
    top: 52%;
    transform: translate(-50%, -50%);
    display: flex;
    align-items: flex-start;
    /* Width sized to hold the t comfortably with breathing room */
    width: 360px;
    height: 460px;
  }

  /* The "1" circle. Thin outlined dark navy, sits above the t-stem like
     the dot of an italic "i". Slightly offset right because Bodoni Moda
     italic leans forward; matching the icon. */
  .one {
    position: absolute;
    left: 138px;
    top: 0;
    width: 70px; height: 70px;
    border: 3px solid #1A1F36;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Bodoni Moda', serif;
    font-style: italic;
    font-weight: 700;
    font-size: 44px;
    color: #1A1F36;
    line-height: 1;
    padding-bottom: 4px;
    box-sizing: border-box;
  }

  /* The italic "t" itself. Bodoni Moda 900 italic at ~480px gives the
     dramatic editorial weight characteristic of magazine display type.
     No transform or kerning hacks — just one large letter. */
  .t {
    position: absolute;
    left: 0;
    top: 30px;
    width: 360px;
    text-align: center;
    font-family: 'Bodoni Moda', serif;
    font-style: italic;
    font-weight: 900;
    font-size: 460px;
    line-height: 0.95;
    color: #1A1F36;
    /* slight tracking to compensate for tight italic */
    letter-spacing: -8px;
  }
</style>
</head><body>
  <div class="mark">
    <div class="t">t</div>
    <div class="one">1</div>
  </div>
</body></html>
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1024, "height": 500},
            device_scale_factor=1,
        )
        page = ctx.new_page()
        page.set_content(HTML, wait_until="domcontentloaded")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(800)

        out = OUT / "feature_graphic_1024x500.png"
        page.screenshot(path=str(out), full_page=False, omit_background=False)
        import os
        print(f"  [ok] {out.name}  ({os.path.getsize(out)} bytes)")
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
