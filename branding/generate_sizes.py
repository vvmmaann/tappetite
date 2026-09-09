"""Generate all derivative brand asset sizes from the 3 source PNGs.

Source files (in same dir):
  wordmark_serif.png      2172x724  — full lockup, used at large sizes only
  app_icon_t.png          1254x1254 — square: serif "t" with "1" circle
  mark_circle_1.png       1254x1254 — square: standalone "1" in circle

Outputs (written to branding/dist/):
  favicon.ico             multi-size 16/32/48 from mark_circle_1
  favicon-16.png
  favicon-32.png
  favicon-48.png
  apple-touch-icon.png    180x180  iOS Add to Home (uses app_icon_t)
  apple-touch-icon-152.png 152x152 older iPad
  apple-touch-icon-167.png 167x167 iPad Pro
  pwa-192.png             192x192  Android home screen
  pwa-256.png             256x256
  pwa-384.png             384x384
  pwa-512.png             512x512  Android splash
  android-chrome-432.png  432x432  Android adaptive icon
  og-default.png          1200x630 OpenGraph share image (wordmark on cream)

Usage:
  cd branding/
  python generate_sizes.py

Requires: Pillow (`pip install Pillow`)
"""
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

HERE = Path(__file__).parent
DIST = HERE / "dist"
DIST.mkdir(exist_ok=True)

# Source files — must exist
SRC_WORDMARK = HERE / "wordmark_serif.png"
SRC_APP_T = HERE / "app_icon_t.png"
SRC_MARK = HERE / "mark_circle_1.png"

# Brand cream — matches `--bg` and theme-color in game.html (#FAF6F0)
CREAM_BG = (250, 246, 240)


def make_square(src_path: Path, out_path: Path, size: int) -> None:
    """Resize a square source to (size, size) with high-quality LANCZOS."""
    img = Image.open(src_path).convert("RGB")
    img = img.resize((size, size), Image.LANCZOS)
    img.save(out_path, format="PNG", optimize=True)
    print(f"  {out_path.name:<28} {size}x{size}")


def make_favicon_ico(src_path: Path, out_path: Path) -> None:
    """Produce a multi-size .ico containing 16/32/48 from a square source.

    .ico is the legacy format browsers expect at /favicon.ico. Modern browsers
    also use the explicit <link rel="icon" type="image/png" sizes="..."> tags,
    but the .ico fallback is still important for old IE / RSS readers / etc.
    """
    img = Image.open(src_path).convert("RGBA")
    sizes = [(16, 16), (32, 32), (48, 48)]
    img.save(out_path, format="ICO", sizes=sizes)
    print(f"  {out_path.name:<28} multi-size: 16, 32, 48")


def make_og_image(src_wordmark: Path, out_path: Path) -> None:
    """Render OpenGraph share image: wordmark centered on cream 1200x630.

    1200x630 is the OpenGraph standard (used by Twitter, Facebook, LinkedIn,
    iMessage, Telegram, etc. when somebody shares the link).
    """
    canvas = Image.new("RGB", (1200, 630), CREAM_BG)
    wm = Image.open(src_wordmark).convert("RGBA")
    # Scale wordmark to ~70% of canvas width while preserving aspect ratio
    target_w = int(1200 * 0.7)
    ratio = target_w / wm.size[0]
    target_h = int(wm.size[1] * ratio)
    wm = wm.resize((target_w, target_h), Image.LANCZOS)
    # Center it
    offset_x = (1200 - target_w) // 2
    offset_y = (630 - target_h) // 2
    canvas.paste(wm, (offset_x, offset_y), wm if wm.mode == "RGBA" else None)
    canvas.save(out_path, format="PNG", optimize=True)
    print(f"  {out_path.name:<28} 1200x630 (wordmark on cream)")


def main() -> None:
    # Sanity check — all three sources must exist
    for src in (SRC_WORDMARK, SRC_APP_T, SRC_MARK):
        if not src.exists():
            print(f"ERROR: missing source file: {src}", file=sys.stderr)
            sys.exit(1)

    print(f"Generating brand asset sizes -> {DIST}/")
    print()

    print("== Favicons (from mark_circle_1.png) ==")
    make_favicon_ico(SRC_MARK, DIST / "favicon.ico")
    make_square(SRC_MARK, DIST / "favicon-16.png", 16)
    make_square(SRC_MARK, DIST / "favicon-32.png", 32)
    make_square(SRC_MARK, DIST / "favicon-48.png", 48)
    print()

    print("== iOS touch icons (from app_icon_t.png) ==")
    make_square(SRC_APP_T, DIST / "apple-touch-icon.png", 180)
    make_square(SRC_APP_T, DIST / "apple-touch-icon-152.png", 152)
    make_square(SRC_APP_T, DIST / "apple-touch-icon-167.png", 167)
    print()

    print("== PWA / Android icons (from app_icon_t.png) ==")
    make_square(SRC_APP_T, DIST / "pwa-192.png", 192)
    make_square(SRC_APP_T, DIST / "pwa-256.png", 256)
    make_square(SRC_APP_T, DIST / "pwa-384.png", 384)
    make_square(SRC_APP_T, DIST / "pwa-512.png", 512)
    make_square(SRC_APP_T, DIST / "android-chrome-432.png", 432)
    print()

    print("== OpenGraph share image (from wordmark_serif.png) ==")
    make_og_image(SRC_WORDMARK, DIST / "og-default.png")
    print()

    # Inventory
    print(f"Done. {sum(1 for _ in DIST.iterdir())} files in {DIST}/")


if __name__ == "__main__":
    main()
