"""Self-host Google Fonts (audit-6 H1).

Fetches Google Fonts CSS with a modern browser UA → distills .woff2 URLs →
downloads each → rewrites URLs to local paths → combines into a single
/assets/fonts.css that game.html / admin.html / privacy.html / terms.html
will load instead of the live Google Fonts CDN.

Run once. Re-run if font set changes.
"""
import urllib.request
import re
import pathlib
from urllib.request import Request

# Google Fonts CSS URLs with the FULL set of weights + italics actually
# used across game.html / admin.html / privacy.html / terms.html. Each
# request asks for latin + cyrillic subsets so RU text renders properly.
URLS = {
    "onest": "https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700;800&display=swap",
    "jbmono": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap",
    "bodoni": "https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@0,500;0,600;0,700;1,500;1,600;1,700&display=swap",
}

# Modern browser UA — Google Fonts checks it to decide whether to serve
# .woff2 (modern) or fall back to .woff/.ttf. Without a modern UA you get
# bigger, slower fonts.
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

REPO_ROOT = pathlib.Path(__file__).parent.parent
OUT_FONTS_DIR = REPO_ROOT / "assets" / "fonts"
OUT_CSS_PATH = REPO_ROOT / "assets" / "fonts.css"
OUT_FONTS_DIR.mkdir(parents=True, exist_ok=True)

combined_css_chunks = []

for family_key, css_url in URLS.items():
    print(f"\n=== {family_key} ===")
    req = Request(css_url, headers={"User-Agent": UA})
    css_text = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

    # Find all woff2 URLs in the CSS
    woff_urls = sorted(set(re.findall(
        r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)",
        css_text,
    )))
    print(f"  found {len(woff_urls)} woff2 files")

    for woff_url in woff_urls:
        # Filename: prefix with family_key for uniqueness across families
        # (different fonts may have same auto-generated hash)
        original_name = woff_url.split("/")[-1]
        local_name = f"{family_key}-{original_name}"
        local_path = OUT_FONTS_DIR / local_name
        if not local_path.exists():
            print(f"  downloading {original_name}")
            urllib.request.urlretrieve(woff_url, local_path)
        # Rewrite URL in CSS to local path
        css_text = css_text.replace(woff_url, f"/assets/fonts/{local_name}")

    combined_css_chunks.append(f"/* {family_key} */\n{css_text}")

combined = "\n\n".join(combined_css_chunks)
OUT_CSS_PATH.write_text(combined, encoding="utf-8")

print(f"\n--- DONE ---")
print(f"Fonts dir: {OUT_FONTS_DIR}")
print(f"Combined CSS: {OUT_CSS_PATH}")
print(f"Total fonts: {len(list(OUT_FONTS_DIR.glob('*.woff2')))}")
total_size = sum(p.stat().st_size for p in OUT_FONTS_DIR.glob("*.woff2"))
print(f"Total size:  {total_size // 1024} KB")
