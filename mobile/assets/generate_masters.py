"""Generate icon + splash master images for @capacitor/assets.

Source of truth: ../../branding/app_icon_t.png — the final Tappetite mark
(serif lowercase 't' with the small circled '1' above it).

Outputs (in this directory, picked up by `npx capacitor-assets generate`):
  - icon-only.png         1024×1024  (full icon for iOS + Android legacy)
  - icon-foreground.png   1024×1024  (t-mark only, transparent — for Android adaptive)
  - icon-background.png   1024×1024  (cream bg only — for Android adaptive)
  - splash.png            2732×2732  (light theme splash, t-mark centered)
  - splash-dark.png       2732×2732  (dark theme splash, t-mark on coffee bg)

Adaptive-icon mechanics (Android):
  Android renders foreground+background through a system mask (circle, square,
  squircle...) so the icon must look right under any clip. The plugin specs:
   - Total canvas 108dp × 108dp
   - Visible "safe zone" only the centre 66dp × 66dp circle
   - We inset the mark to ~66% so it survives every system mask.
"""
from PIL import Image
from pathlib import Path

HERE = Path(__file__).parent
BRAND = HERE.parent.parent / 'branding' / 'app_icon_t.png'

CREAM       = (250, 246, 240, 255)   # #FAF6F0 light bg
DARK_BG     = (31, 27, 22, 255)      # #1F1B16 dark bg (Coffee theme)
TRANSPARENT = (0, 0, 0, 0)


def load_brand_master():
    """Load the branding PNG. Resize to 1024 if needed."""
    if not BRAND.exists():
        raise FileNotFoundError(f'Brand master not found: {BRAND}')
    img = Image.open(BRAND).convert('RGBA')
    if img.size != (1024, 1024):
        img = img.resize((1024, 1024), Image.LANCZOS)
    return img


def extract_foreground(img: Image.Image, bg=CREAM, threshold=30) -> Image.Image:
    """Make pixels close to bg colour transparent, keep the mark.
    Threshold 30 keeps anti-alias edges; 0 = exact match only.
    Operates per-pixel (slow for very large images, fine at 1024)."""
    w, h = img.size
    out = Image.new('RGBA', (w, h), TRANSPARENT)
    src = img.load()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            # Distance from bg colour (Manhattan, fast enough for 1024²)
            d = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            if d > threshold:
                dst[x, y] = (r, g, b, a)
    return out


def trim_to_content(img: Image.Image, alpha_threshold=8) -> Image.Image:
    """Crop to the smallest box that contains all non-transparent pixels.
    Used to strip the embedded whitespace baked into the source brand PNG so
    we can re-inset the mark with controlled padding for adaptive icons."""
    bbox = img.getbbox() if img.mode == 'RGBA' else None
    if not bbox:
        return img
    return img.crop(bbox)


def make_icon_only(brand: Image.Image) -> Image.Image:
    """Full legacy icon (Android <8, iOS): brand image as-is — already has
    correct framing for non-adaptive launcher use."""
    return brand.copy()


def make_icon_foreground(brand: Image.Image, size=1024, safe_ratio=0.80) -> Image.Image:
    """Foreground for Android adaptive: t-mark only on transparent.

    Steps: extract mark (drop cream bg) → trim away source whitespace →
    fit into a square preserving aspect ratio → inset into safe-zone.

    safe_ratio=0.80 leaves enough margin for any system mask (circle, round
    square, squircle, hex) — the t-mark is vertical and narrow, so it
    survives even an aggressive circle clip. Earlier value (0.66) was too
    conservative + the source itself had ~12% baked-in whitespace, so the
    mark looked tiny vs. the PWA shortcut version on the home screen.
    """
    fg_clean = extract_foreground(brand, bg=CREAM, threshold=30)
    fg_trimmed = trim_to_content(fg_clean)

    # Fit trimmed mark into a square inner area, preserving aspect ratio.
    inner = int(size * safe_ratio)
    tw, th = fg_trimmed.size
    scale = min(inner / tw, inner / th)
    new_w = max(1, int(tw * scale))
    new_h = max(1, int(th * scale))
    fg_resized = fg_trimmed.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new('RGBA', (size, size), TRANSPARENT)
    pad_x = (size - new_w) // 2
    pad_y = (size - new_h) // 2
    canvas.paste(fg_resized, (pad_x, pad_y), fg_resized)
    return canvas


def make_icon_background(size=1024) -> Image.Image:
    """Background for Android adaptive: solid cream."""
    return Image.new('RGBA', (size, size), CREAM)


def make_splash(brand: Image.Image, size=2732, dark=False) -> Image.Image:
    """Splash screen: t-mark centred on full canvas at ~28% of canvas height.
    Light variant uses cream bg + dark mark (use brand image as-is).
    Dark variant uses coffee bg + we paste the extracted foreground (mark on
    transparent), keeping the original ink colour so the mark stays legible."""
    bg = DARK_BG if dark else CREAM
    canvas = Image.new('RGBA', (size, size), bg)
    mark_size = int(size * 0.28)
    if dark:
        # Use foreground (transparent bg) so coffee colour shows through.
        # Mark stays its original (dark) colour — readable on coffee thanks
        # to the warmth contrast. If we ever want a true inverted mark, we'd
        # need a separately drawn cream-on-coffee master.
        mark_src = extract_foreground(brand, bg=CREAM, threshold=30)
    else:
        mark_src = brand
    mark = mark_src.resize((mark_size, mark_size), Image.LANCZOS)
    pad = (size - mark_size) // 2
    canvas.paste(mark, (pad, pad), mark)
    return canvas


def main():
    brand = load_brand_master()
    print(f'Brand master loaded: {BRAND.name} {brand.size}')

    masters = {
        'icon-only.png':       make_icon_only(brand),
        'icon-foreground.png': make_icon_foreground(brand, 1024),
        'icon-background.png': make_icon_background(1024),
        'splash.png':          make_splash(brand, 2732, dark=False),
        'splash-dark.png':     make_splash(brand, 2732, dark=True),
    }
    for name, img in masters.items():
        out = HERE / name
        img.save(out, 'PNG', optimize=True)
        print(f'  wrote {name}: {img.size[0]}x{img.size[1]} ({out.stat().st_size // 1024} KB)')

    print()
    print(f'All masters written to {HERE}')
    print('Next: cd ../ && npx capacitor-assets generate')


if __name__ == '__main__':
    main()
