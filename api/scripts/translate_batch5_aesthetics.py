"""Batch 5: Эстетика / Aesthetics — 10 cats, 160 items."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

TRANSLATIONS = {
    "aesthetic_vibe": {
        "name_en": "What's your vibe",
        "blurb_en": "16 social-media aesthetics. Find which one is closest to you",
        "items": {
            "old_money":    ("Old money",      "quiet luxury · cashmere · nothing new"),
            "cottagecore":  ("Cottagecore",    "linen dresses · baking bread · escape from the city"),
            "y2k":          ("Y2K",            "pink shine · cyber chic · 2000s nostalgia"),
            "dark_academia":("Dark academia",  "tweed · libraries · gothic architecture"),
            "soft_girl":    ("Soft girl",      "pastels · hearts · tenderness as armor"),
            "cyber":        ("Cyber",          "tech · chrome · urban night"),
            "indie_sleaze": ("Indie sleaze",   "blurry selfies · chaos · 2014 parties"),
            "streetwear":   ("Streetwear",     "silhouette · sneakers · the urban vertical"),
            "minimal":      ("Minimalism",     "monochrome · proportions · nothing extra"),
            "boho":         ("Boho",           "layers of fabric · ethnic · wind in your hair"),
            "preppy":       ("Preppy",         "polo · tennis · picnic blanket"),
            "gothic":       ("Gothic",         "black · lace · melancholy as a style"),
            "grunge":       ("Grunge",         "flannel · Doc Martens · 1992"),
            "sport_chic":   ("Sport chic",     "leggings · technical fabrics · the city's rhythm"),
            "business_cas": ("Business casual","suit without a tie · confidence"),
            "kawaii":       ("Kawaii",         "pink · cute · childhood forever"),
        },
    },
    "clothing_style": {
        "name_en": "Your clothing style",
        "blurb_en": "16 styles: from minimal to streetwear. Which one is really you",
        "items": {
            "cl_minimal": ("Minimalism",                "basics, neutral tones"),
            "cl_street":  ("Streetwear",                "sneakers, oversize, hoodies"),
            "cl_oldmoney":("Old Money / Quiet Luxury",  "quiet, expensive, no logos"),
            "cl_y2k":     ("Y2K / 2000s",               "low-rise, shine"),
            "cl_dark":    ("Dark Academia",             "coats, books, autumn"),
            "cl_grunge":  ("Grunge",                    "ripped jeans, leather, chaos"),
            "cl_cottage": ("Cottagecore",               "linen, flowers, nature"),
            "cl_athl":    ("Athleisure",                "training wear as the base"),
            "cl_biz":     ("Business Casual",           "between office and life"),
            "cl_boho":    ("Boho",                      "freedom, layers, ethnic"),
            "cl_preppy":  ("Preppy",                    "polo, plaid, lake"),
            "cl_hype":    ("Hypebeast",                 "limiteds, logos, queues"),
            "cl_vintage": ("Vintage / Thrift",          "secondhand, spirit of an era"),
            "cl_scand":   ("Scandinavian minimalism",   "clean, practical, function"),
            "cl_avant":   ("Avant-garde",               "confusing, but it's art"),
            "cl_casual":  ("Casual without strategy",   "just comfortable, that's it"),
        },
    },
    "room_aesthetic": {
        "name_en": "Your room aesthetic",
        "blurb_en": "16 takes on space: cozy, minimal, chaotic, vintage, neon",
        "items": {
            "ra_min":     ("Minimalism",                  "white walls, emptiness, order"),
            "ra_hygge":   ("Hygge / cozy",                "candles, blankets, warm light"),
            "ra_dark":    ("Dark Academia",               "books, wood, lamps"),
            "ra_botanic": ("Botanical",                   "lots of plants, light"),
            "ra_vintage": ("Vintage / antique",           "old furniture, history"),
            "ra_loft":    ("Industrial loft",             "brick, metal, high ceilings"),
            "ra_wabi":    ("Japanese / Wabi-sabi",        "emptiness, nature, imperfection"),
            "ra_gamer":   ("Gamer room",                  "neon, RGB, screens"),
            "ra_scand":   ("Scandinavian",                "light wood, function"),
            "ra_max":     ("Maximalist",                  "everything at once, textures and colors"),
            "ra_midcent": ("Mid-century modern",          "retro-futurism of the '50s-'60s"),
            "ra_coastal": ("Coastal",                     "blue, white, wood"),
            "ra_morocco": ("Moroccan / Eastern",          "ornaments, arches, copper"),
            "ra_art":     ("Artistic mess",               "canvas, paints, collages"),
            "ra_bw":      ("Black-and-white minimalism",  "no compromises"),
            "ra_home":    ("Just a home",                 "yours, cozy, alive"),
        },
    },
    "current_fashion_style": {
        "name_en": "Your fashion style right now",
        "blurb_en": "How you want to be read",
        "items": {
            "current_fashion_style-streetwear":          ("Streetwear",       "street casual · oversize"),
            "current_fashion_style-minimal":             ("Minimal",          "two colors · clean lines"),
            "current_fashion_style-old-money":           ("Old money",        "expensive without logos"),
            "current_fashion_style-gorpcore":            ("Gorpcore",         "technical outdoor"),
            "current_fashion_style-darkwear":            ("Darkwear",         "Rick Owens · techno-black"),
            "current_fashion_style-clean-girl-boy":      ("Clean girl/boy",   "sport + cleanness"),
            "current_fashion_style-sport-casual":        ("Sport casual",     "sneakers · hoodies"),
            "current_fashion_style-y2k-fashion":         ("Y2K",              "the noughties · low-rise"),
            "current_fashion_style-coquette":            ("Coquette",         "bows · lace · tenderness"),
            "current_fashion_style-vintage-thrift":      ("Vintage thrift",   "secondhand mix"),
            "current_fashion_style-techwear":            ("Techwear",         "functional sci-fi"),
            "current_fashion_style-preppy":              ("Preppy",           "shirts · academic"),
            "current_fashion_style-goth-alt":            ("Goth / alt",       "black · chains · boots"),
            "current_fashion_style-normcore":            ("Normcore",         "basic without aesthetics"),
            "current_fashion_style-athleisure":          ("Athleisure",       "expensive sportswear"),
            "current_fashion_style-cottagecore-fashion": ("Cottagecore",      "pastoral · little flowers"),
        },
    },
    "your_aesthetic": {
        "name_en": "Which aesthetic is closer to you",
        "blurb_en": "The visual world you live in",
        "items": {
            "your_aesthetic-y2k":            ("Y2K",                 "the noughties · metallic · low-rise"),
            "your_aesthetic-clean-girl-boy": ("Clean girl/boy",      "sport · cleanness · nothing extra"),
            "your_aesthetic-dark-academia":  ("Dark academia",       "leather · tweed · libraries"),
            "your_aesthetic-cyber":          ("Cyber / cyberpunk",   "neon · techno · the future"),
            "your_aesthetic-cottagecore":    ("Cottagecore",         "farm · cozy · cookies"),
            "your_aesthetic-blokecore":      ("Blokecore",           "football · '90s casual"),
            "your_aesthetic-coquette":       ("Coquette",            "bows · tenderness · girlish"),
            "your_aesthetic-minimal":        ("Minimal",             "white · beige · lines"),
            "your_aesthetic-old-money":      ("Old money",           "quiet chic · yachts · canvas"),
            "your_aesthetic-goblincore":     ("Goblincore",          "chaos · moss · oddities"),
            "your_aesthetic-soft-grunge":    ("Soft grunge",         "fleece · flannel · the '90s"),
            "your_aesthetic-tradwife":       ("Tradwife",            "homestead · back to roots"),
            "your_aesthetic-acubi":          ("Acubi",               "Balkan internet 2024"),
            "your_aesthetic-mob-wife":       ("Mob wife",            "'90s gangster gf · leopard"),
            "your_aesthetic-office-siren":   ("Office siren",        "work · sensual"),
            "your_aesthetic-maximalism":     ("Maximalism",          "colors · patterns · layers"),
        },
    },
    "your_mood_color": {
        "name_en": "Your mood color",
        "blurb_en": "The palette of your current state",
        "items": {
            "deep-blue":     ("Deep blue",     "calm · depth · everything under control"),
            "red":           ("Red",           "energy · passion · now or never"),
            "sage-green":    ("Sage green",    "quiet · nature · in balance with yourself"),
            "black":         ("Black",         "closed off · power · nothing extra"),
            "dusty-pink":    ("Dusty pink",    "tenderness · nostalgia · slightly melancholy"),
            "orange":        ("Orange",        "warmth · motion · you want to talk to people"),
            "white":         ("White",         "emptiness · a clean slate · haven't decided yet"),
            "mustard":       ("Mustard",       "warm tiredness · cozy · autumn light"),
            "lilac":         ("Lilac",         "dreamy · soft · somewhere not here"),
            "grey":          ("Grey",          "neutrality · pause · neither here nor there"),
            "electric-blue": ("Electric blue", "charged up · sharp · you want to act"),
            "forest-green":  ("Forest green",  "shelter · seriousness · need silence"),
            "gold":          ("Gold",          "confidence · shine · on the rise"),
            "terracotta":    ("Terracotta",    "earth · warmth · something real"),
            "ice-blue":      ("Ice blue",      "detachment · clarity · keeping distance"),
            "burgundy":      ("Burgundy",      "deep feeling · maturity · a lot going on inside"),
        },
    },
    "your_avatar_style": {
        "name_en": "Your profile pic style",
        "blurb_en": "What's on your profile photo?",
        "items": {
            "real-photo":      ("Real photo of your face",     "open · recognizable · nothing to hide"),
            "anime-avatar":    ("An anime character",          "style · culture · face not required"),
            "silhouette":      ("Silhouette or shadow",        "mystery · there · but not visible"),
            "meme":             ("Meme or funny picture",      "not serious · a mood · this is me today"),
            "aesthetic-photo": ("Aesthetic photo without face","nature · details · atmosphere instead of face"),
            "pet":             ("Photo of your pet",           "cat · dog · they represent me better"),
            "cartoon-avatar":  ("Cartoon avatar",              "drawn character · style · not a photo"),
            "ai-generated":    ("AI portrait",                 "neural net · idealized · trendy · almost me"),
            "black-screen":    ("Empty or black screen",       "anonymous · nothing extra · none of your business"),
            "film-character":  ("Movie or TV character",       "hero · identification · speaks for me"),
            "landscape":       ("Landscape or place",          "favorite spot · sea · mountains · I want to be there"),
            "logo-symbol":     ("Logo or symbol",              "brand · sign · minimal · no explanation needed"),
            "old-photo":       ("Old or film photo",           "nostalgia · grain · another time"),
            "art-portrait":    ("Art or illustration",         "drawn by an artist · unique · not generic"),
            "back-of-head":    ("Photo from behind / no face", "there · but I don't show · intrigue"),
            "seasonal-update": ("Updates with my mood",        "changing · alive · different every month"),
        },
    },
    "your_background": {
        "name_en": "What background suits you",
        "blurb_en": "Pick the setting where you feel at home",
        "items": {
            "night-city":   ("The night city",              "lights · rain · anonymity in the crowd"),
            "sea":          ("The sea",                     "horizon · waves · your head clears"),
            "library":      ("A library",                   "silence · the smell of books · time slows down"),
            "club":         ("A club",                      "darkness · loud music · everyone's a stranger and yours"),
            "forest":       ("A forest",                    "no one · trees · breathing differently"),
            "rooftop":      ("A rooftop",                   "above everyone · wind · the city under your feet"),
            "cozy-cafe":    ("A cozy café",                 "warmth · coffee · noise as background · room to think"),
            "studio":       ("A creative studio",           "mess · process · something is being made"),
            "mountains":    ("Mountains",                   "altitude · silence · scale changes you"),
            "train":        ("A train in transit",          "the window · things flicker by · between two points"),
            "home":         ("Your home at night",          "lamp · blanket · no one bothering you"),
            "empty-street": ("An empty street at dawn",     "quiet · only you · the city still asleep"),
            "gallery":      ("A gallery or museum",         "white walls · silence · you look and think"),
            "beach-night":  ("Beach at night",              "waves · darkness · stars · no one"),
            "airport":      ("An airport",                  "transit · everyone going somewhere · feeling free"),
            "old-district": ("Old district of a foreign city","unknown streets · lost · and that's fine"),
        },
    },
    "your_stories_style": {
        "name_en": "Your stories style",
        "blurb_en": "What's most often in your stories?",
        "items": {
            "minimal":         ("Minimal",                     "one detail · silence in the frame · nothing extra"),
            "chaos":           ("Chaos",                       "everything at once · no filters · stream of consciousness"),
            "food":            ("Food",                        "before eating · always · without fail"),
            "sunsets":         ("Sunsets",                     "the sky changes · you shoot every time · can't help it"),
            "no-stories":      ("Don't post any",              "I observe · I don't show · life isn't for stories"),
            "memes-reposts":   ("Memes and reposts",           "found one · this is me · let everyone see"),
            "music":           ("Track of the day",            "title card + cover · a mood in one song"),
            "aesthetic-film":  ("Film aesthetic",              "grain · warm tones · like another era"),
            "text-only":       ("Text only",                   "a thought · a quote · a flat background · no photo"),
            "travel":          ("Travel",                      "new place · straight to stories · gotta show it"),
            "polls-questions": ("Polls and questions",         "engaging · wanting reactions · interactive"),
            "selfie":          ("Selfie",                      "this is how I look today · a mood · just because"),
            "events":          ("Events and parties",          "concert · meeting · I was there · documented"),
            "nature":          ("Nature and details",          "leaves · puddles · light in a window · noticing little things"),
            "work-process":    ("Work process",                "what you're doing · a project · life behind the scenes"),
            "archive-only":    ("Only in archive",             "you film · you don't post · for yourself"),
        },
    },
    "life_cover_vibe": {
        "name_en": "Your life-cover vibe",
        "blurb_en": "What dresses your world from the outside?",
        "items": {
            "vinyl_cover":        ("A vinyl record",            "warm sound · 12 inches · art object"),
            "movie_poster":       ("A movie poster",            "Hollywood blockbuster · Oscar · handmade"),
            "magazine_cover":     ("A magazine cover",          "glossy · cult figure · special issue"),
            "comic_book":         ("A comic book",              "superhero · Marvel · first issue"),
            "artbook":            ("An artbook",                "concept art · the making-of of a game · limited edition"),
            "book_cover_classic": ("A classic book",            "hardback · ribbon bookmark · embossed spine"),
            "cd_case":            ("A CD case",                 "the '90s · the booklet · the disc"),
            "game_box":           ("A game box",                "PC · big box · floppy · manual"),
            "dvd_cover":          ("A DVD cover",               "home cinema · bonus tracks · scene selection"),
            "calendar":           ("A wall calendar",           "cats · landscapes · monthly tear-off"),
            "postcard":           ("A postcard",                "sent by hand · greetings from Crimea · Soviet style"),
            "digipak":            ("A digipak",                 "eco-cardboard · embossing · indie music"),
            "steelbook":          ("A steelbook",               "metal case · embossed · collector's"),
            "paperback":          ("A paperback book",          "pocket size · type that bleeds · supermarket"),
            "puzzle_box":         ("A puzzle box",              "cardboard · a piece of the future · gift wrap"),
            "tour_poster":        ("A tour poster",             "concert print · dates and cities · DIY design"),
        },
    },
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats_by_id = {c.get("id"): c for c in raw}
    cats_done, items_done, items_missing = 0, 0, 0
    for cat_id, tr in TRANSLATIONS.items():
        cat = cats_by_id.get(cat_id)
        if cat is None: print(f"  [skip] {cat_id} not found"); continue
        cat["name_en"] = tr["name_en"]; cat["blurb_en"] = tr["blurb_en"]
        items_tr = tr.get("items", {}); n = 0
        for it in cat.get("items", []):
            iid = it.get("id")
            if iid in items_tr:
                it["name_en"], it["ctx_en"] = items_tr[iid]; n += 1
            else: items_missing += 1; print(f"    [warn] {cat_id}/{iid}")
        cats_done += 1; items_done += n
        print(f"  ✓ {cat_id}: {n}/{len(cat.get('items', []))}")
    print(f"\nCats: {cats_done}, items: {items_done}, missing: {items_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.batch5.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
