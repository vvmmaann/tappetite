"""Batch 3: Музыка / Music — 10 cats, ~184 items."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

TRANSLATIONS = {
    "kpop_boys": {
        "name_en": "K-pop boy bands",
        "blurb_en": "BTS, EXO, ATEEZ and 13 more groups across all generations",
        "items": {
            "bts":       ("BTS",          "BIGHIT · debut 2013 · 7 members"),
            "exo":       ("EXO",          "SM · debut 2012 · 9 members"),
            "seventeen": ("SEVENTEEN",    "PLEDIS · debut 2015 · 13 members"),
            "nct127":    ("NCT 127",      "SM · debut 2016 · 9 members"),
            "ateez":     ("ATEEZ",        "KQ · debut 2018 · 8 members"),
            "txt":       ("TXT",          "BIGHIT · debut 2019 · 5 members"),
            "enhypen":   ("ENHYPEN",      "BELIFT · debut 2020 · 7 members"),
            "straykids": ("Stray Kids",   "JYP · debut 2018 · 8 members"),
            "treasure":  ("TREASURE",     "YG · debut 2020 · 10 members"),
            "zb1":       ("ZEROBASEONE",  "WAKEONE · debut 2023 · 9 members"),
            "bigbang":   ("BIGBANG",      "YG · debut 2006 · 4 members"),
            "suju":      ("Super Junior", "SM · debut 2005 · 9 members"),
            "shinee":    ("SHINee",       "SM · debut 2008 · 4 members"),
            "tvxq":      ("TVXQ",         "SM · debut 2003 · 2 members"),
            "got7":      ("GOT7",         "JYP · debut 2014 · 7 members"),
            "monstax":   ("MONSTA X",     "STARSHIP · debut 2015 · 6 members"),
        },
    },
    "music_camp": {
        "name_en": "Your music camp",
        "blurb_en": "16 genres and scenes. Which one is really you right now",
        "items": {
            "sad_indie":     ("Sad-girl indie",     "Phoebe Bridgers and lonely evenings"),
            "hyperpop":      ("Hyperpop",           "100 gecs · the aesthetic of maximum"),
            "old_rap":       ("Old-school rap",     "the '90s · vinyl samples · NY style"),
            "lofi":          ("Lo-fi & focus",      "background for studying and work"),
            "house90":       ("'90s house",         "clubs · Chicago and Detroit"),
            "k_rb":          ("Korean R&B",         "IU · DEAN · soft soul"),
            "ru_rap":        ("Russian rap",        "2015-2020 · beat and lyric"),
            "grunge":        ("'90s grunge",        "Nirvana · flannel · 1992"),
            "acid_jazz":     ("Acid jazz",          "Jamiroquai · funk · '70s pastiche"),
            "emo":           ("2000s emo",          "MCR · teenage pain · 2007"),
            "phonk":         ("Phonk",              "Russian phonk · sticky bass · TikTok 2022"),
            "electroclash":  ("Electroclash",       "Peaches · 2003 · new-wave retro"),
            "ambient":       ("Ambient",            "Brian Eno · background sound"),
            "italo_disco":   ("Italo disco",        "space disco · Italy · '80s"),
            "trap":          ("Trap",               "Atlanta · 808 · modern mainstream"),
            "bardic":        ("Bard song",          "Okudzhava · the '60s · kitchen songs"),
        },
    },
    "kpop_girls": {
        "name_en": "K-pop girl groups",
        "blurb_en": "BLACKPINK, NewJeans, TWICE and 13 more groups across generations",
        "items": {
            "blackpink": ("BLACKPINK",         "YG · debut 2016 · 4 members"),
            "twice":     ("TWICE",             "JYP · debut 2015 · 9 members"),
            "newjeans":  ("NewJeans",          "ADOR · debut 2022 · 5 members"),
            "aespa":     ("aespa",             "SM · debut 2020 · 4 members"),
            "ive":       ("IVE",               "Starship · debut 2021 · 6 members"),
            "gidle":     ("(G)I-DLE",          "Cube · debut 2018 · 5 members"),
            "itzy":      ("ITZY",              "JYP · debut 2019 · 5 members"),
            "redvelvet": ("Red Velvet",        "SM · debut 2014 · 5 members"),
            "sserafim":  ("LE SSERAFIM",       "HYBE · debut 2022 · 5 members"),
            "mamamoo":   ("MAMAMOO",           "RBW · debut 2014 · 4 members"),
            "snsd":      ("Girls' Generation", "SM · debut 2007 · 8 members"),
            "twone":     ("2NE1",              "YG · debut 2009 · 4 members"),
            "stayc":     ("STAYC",             "High Up · debut 2020 · 6 members"),
            "sistar":    ("SISTAR",            "Starship · 2010-2017 · 4 members"),
            "fx":        ("f(x)",              "SM · 2009-2019 · 5 members"),
            "nmixx":     ("NMIXX",             "JYP · debut 2022 · 6 members"),
        },
    },
    "your_2007": {
        "name_en": "Your 2007",
        "blurb_en": "Who do you go back to that legendary era with?",
        "items": {
            "my-chemical-romance":      ("My Chemical Romance",     "New Jersey · emo opera · The Black Parade · 2006"),
            "avril-lavigne":            ("Avril Lavigne",           "Canada · Sk8er Boi · the punk princess of the '00s"),
            "tokio-hotel":              ("Tokio Hotel",             "Germany · Bill Kaulitz · Durch den Monsun · 2005"),
            "blink-182":                ("Blink-182",               "San Diego · pop-punk · All the Small Things"),
            "green-day":                ("Green Day",               "Berkeley · American Idiot · punk rock opera · 2004"),
            "him":                      ("HIM",                     "Finland · love metal · Ville Valo · the heartagram"),
            "linkin-park":              ("Linkin Park",             "Los Angeles · nu metal · Hybrid Theory · 2000"),
            "evanescence":              ("Evanescence",             "Arkansas · gothic rock · Amy Lee · Bring Me to Life"),
            "fall-out-boy":             ("Fall Out Boy",            "Chicago · pop-punk · Pete Wentz · Sugar We're Goin Down"),
            "paramore":                 ("Paramore",                "Tennessee · Hayley Williams · Misery Business · 2007"),
            "panic-at-the-disco":       ("Panic! at the Disco",     "Las Vegas · baroque pop-punk · I Write Sins · 2005"),
            "30-seconds-to-mars":       ("30 Seconds to Mars",      "Hollywood · Jared Leto · A Beautiful Lie · 2005"),
            "simple-plan":              ("Simple Plan",             "Montreal · pop-punk · I'm Just a Kid · teen anthem"),
            "the-used":                 ("The Used",                "Utah · post-hardcore · Bert McCracken · In Love and Death"),
            "bullet-for-my-valentine":  ("Bullet for My Valentine", "Wales · metalcore · Tears Don't Fall · The Poison · 2006"),
            "the-all-american-rejects": ("The All-American Rejects","Oklahoma · pop-punk · Swing Swing · Move Along"),
            "yellowcard":               ("Yellowcard",              "Jacksonville · pop-punk · Ocean Avenue · violin in punk"),
            "placebo":                  ("Placebo",                 "London · alternative · Brian Molko · Every You Every Me"),
            "afi":                      ("AFI",                     "California · gothic punk · Sing the Sorrow · Miss Murder"),
            "marilyn-manson":           ("Marilyn Manson",          "Ohio · shock rock · Beautiful People · the '00s provocateur"),
            "nickelback":               ("Nickelback",              "Canada · post-grunge · How You Remind Me · '00s radio"),
            "amatory":                  ("Amatory",                 "St. Petersburg · metalcore · Russian '00s cult"),
            "stigmata":                 ("Stigmata",                "St. Petersburg · alternative · Nebo Zdes · Russian rock"),
            "slott":                    ("Slot",                    "Moscow · industrial rock · Tebya Zdes Net · CIS scene"),
        },
    },
    "your_2007_pop_rnb": {
        "name_en": "Your 2007: Pop / R&B",
        "blurb_en": "Pick who you go back to the era with",
        "items": {
            "beyonce":          ("Beyoncé",           "Irreplaceable · Lemonade · Queen B"),
            "rihanna":          ("Rihanna",           "Umbrella · Barbados · 2007 was the peak"),
            "lady-gaga":        ("Lady Gaga",         "Just Dance · the meat dress · art provocateur"),
            "britney-spears":   ("Britney Spears",    "Gimme More · 2007 crisis · the comeback"),
            "fergie":           ("Fergie",            "Fergalicious · Black Eyed Peas · solo breakout"),
            "justin-timberlake":("Justin Timberlake", "SexyBack · FutureSex/LoveSounds · NSYNC → solo"),
            "gwen-stefani":     ("Gwen Stefani",      "Sweet Escape · No Doubt · Hollywood glam"),
            "amy-winehouse":    ("Amy Winehouse",     "Rehab · 5 Grammys 2008 · the voice of an era"),
            "nelly-furtado":    ("Nelly Furtado",     "Maneater · Timbaland · pop rebirth"),
            "timbaland":        ("Timbaland",         "The Way I Are · producer of the decade · 2007 beats"),
            "kanye-west":       ("Kanye West",        "Stronger · Graduation · Daft Punk sample"),
            "alicia-keys":      ("Alicia Keys",       "No One · piano · #1 all of 2007"),
            "ciara":            ("Ciara",             "Like a Boy · dance · R&B choreography"),
            "chris-brown":      ("Chris Brown",       "Kiss Kiss · dancer · debut at the top"),
            "t-pain":           ("T-Pain",            "Buy U a Drank · auto-tune icon · 2007"),
            "akon":             ("Akon",              "Don't Matter · Senegal · the chart-topper voice"),
        },
    },
    "your_2007_rap_hiphop": {
        "name_en": "Your 2007: Rap / Hip-Hop",
        "blurb_en": "Pick who you go back to the era with",
        "items": {
            "50-cent":     ("50 Cent",          "Curtis · 2007 · album battle with Kanye"),
            "jay-z":       ("Jay-Z",            "American Gangster · 2007 · Roc-A-Fella"),
            "kanye-west":  ("Kanye West",       "Graduation · 2007 · battle with 50 Cent"),
            "lil-wayne":   ("Lil Wayne",        "Da Drought 3 · 2007 · best rapper of the year"),
            "t-i":         ("T.I.",             "T.I. vs T.I.P. · 2007 · ATL"),
            "nas":         ("Nas",              "Hip Hop Is Dead · 2006-07 · New York"),
            "eminem":      ("Eminem",           "Detroit · on hiatus · the king of the '00s"),
            "common":      ("Common",           "Finding Forever · 2007 · Chicago"),
            "basta":       ("Basta",            "Moi Kraya · 2007 · Rostov · breakthrough"),
            "kasta":       ("Kasta",            "Rostov · Shym · cult Russian underground"),
            "legalize":    ("Legalize",         "Mnogotochie · Moscow · '00s rhymes"),
            "smoki-mo":    ("Smoki Mo",         "Triada · Moscow · classic Runet rapper"),
            "noggano":     ("Noggano",          "Basta's alter ego · trash rap · cult"),
            "timati":      ("Timati",           "Black Star · 2007 · debut album"),
            "snoop-dogg":  ("Snoop Dogg",       "Tha Blue Carpet · 2006 · G-Funk · Compton"),
            "pharrell":    ("Pharrell Williams","N.E.R.D. · In My Mind · 2006 · producer"),
        },
    },
    "music_vibe_2020s": {
        "name_en": "Your 2020s music vibe",
        "blurb_en": "The genre you live in right now",
        "items": {
            "music_vibe_2020s-hyperpop":     ("Hyperpop",           "100 gecs · chaotic sugar"),
            "music_vibe_2020s-phonk":        ("Phonk",              "Memphis-style · filtered bass"),
            "music_vibe_2020s-kpop":         ("K-pop",              "production · choreography"),
            "music_vibe_2020s-indie-alt":    ("Indie / alternative","Arctic Monkeys, FKA twigs"),
            "music_vibe_2020s-rap-global":   ("Rap",                "Russian and global"),
            "music_vibe_2020s-techno":       ("Techno / electronic","Berlin · club · 4-on-the-floor"),
            "music_vibe_2020s-sad-pop":      ("Sad pop",            "Billie · Olivia Rodrigo"),
            "music_vibe_2020s-jersey-club":  ("Jersey club",        "running rhythms · TikTok"),
            "music_vibe_2020s-afrobeats":    ("Afrobeats",          "Burna Boy · Wizkid"),
            "music_vibe_2020s-rnb":          ("R&B",                "Frank Ocean · SZA"),
            "music_vibe_2020s-lofi":         ("Lo-fi · chill",      "study · work · cozy"),
            "music_vibe_2020s-hardstyle":    ("Hardstyle",          "Q-dance · 150 BPM+"),
            "music_vibe_2020s-trap":         ("Trap",               "808 · hi-hats"),
            "music_vibe_2020s-bedroom-pop":  ("Bedroom pop",        "Clairo · Cuco · cozy"),
            "music_vibe_2020s-country-2020s":("Country revival",    "Beyoncé · Zach Bryan"),
            "music_vibe_2020s-drill":        ("Drill",              "UK · NY · RU drill"),
        },
    },
    "ru_music_2020s": {
        "name_en": "Russian music of the 2020s",
        "blurb_en": "Who's playing in your headphones most",
        "items": {
            "ru_music_2020s-morgen":         ("Morgenshtern",       "provocation · performance"),
            "ru_music_2020s-bigbabytape":    ("Big Baby Tape",      "trap · auto-tune"),
            "ru_music_2020s-skriptonit":     ("Skriptonit",         "head-nodding verses · Gazgolder"),
            "ru_music_2020s-anna-asti":      ("ANNA ASTI",          "pop hits after Artik & Asti"),
            "ru_music_2020s-instasamka":     ("INSTASAMKA",         "pop-rap · TikTok"),
            "ru_music_2020s-macan":          ("Macan",              "'Tyolki' · summer hit"),
            "ru_music_2020s-xhos":           ("HHOS",               "phonk scene"),
            "ru_music_2020s-slava-marlow":   ("Slava Marlow",       "producer · pop-rap"),
            "ru_music_2020s-platina":        ("Platina",            "hip-hop leader"),
            "ru_music_2020s-pyrokinesis":    ("Pyrokinesis",        "dark rap · poetry"),
            "ru_music_2020s-kishlak":        ("Kishlak",            "underground · aggression"),
            "ru_music_2020s-tima-belorus":   ("Tima Belorusskih",   "lyrical pop-rap"),
            "ru_music_2020s-lida":           ("Lida",               "drill scene"),
            "ru_music_2020s-icegergert":     ("ICEGERGERT",         "phonk · viral tracks"),
            "ru_music_2020s-hammali-navai":  ("HammAli & Navai",    "pop hits · nostalgia"),
            "ru_music_2020s-zemfira":        ("Zemfira",            "the legend · still relevant"),
        },
    },
    "mood_artist": {
        "name_en": "Best artist for your mood",
        "blurb_en": "Not 'the greatest' — the one that hits your vibe",
        "items": {
            "mood_artist-billie":        ("Billie Eilish",      "whisper · sadness · Finneas production"),
            "mood_artist-taylor":        ("Taylor Swift",       "all-rounder · pop historian"),
            "mood_artist-the-weeknd":    ("The Weeknd",         "night · regret · synthwave"),
            "mood_artist-drake":         ("Drake",              "R&B/rap · mainstream"),
            "mood_artist-frank":         ("Frank Ocean",        "meditation · albums as poems"),
            "mood_artist-sza":           ("SZA",                "R&B · vulnerability"),
            "mood_artist-bad-bunny":     ("Bad Bunny",          "Latin · reggaeton"),
            "mood_artist-lana":          ("Lana Del Rey",       "melancholy · California"),
            "mood_artist-tyler":         ("Tyler, the Creator", "chaos · production"),
            "mood_artist-kendrick":      ("Kendrick Lamar",     "thought · narrative"),
            "mood_artist-travis":        ("Travis Scott",       "high · stadium trap"),
            "mood_artist-doja":          ("Doja Cat",           "play · pop weirdness"),
            "mood_artist-olivia":        ("Olivia Rodrigo",     "Gen Z drama"),
            "mood_artist-beyonce":       ("Beyoncé",            "power · icon"),
            "mood_artist-adele":         ("Adele",              "catharsis · vocals"),
            "mood_artist-arctic":        ("Arctic Monkeys",     "British rock · romance"),
            "mood_artist-the1975":       ("The 1975",           "2010s vibe · synths"),
            "mood_artist-ariana":        ("Ariana Grande",      "pop · pastel"),
            "mood_artist-bieber":        ("Justin Bieber",      "mainstream pop"),
            "mood_artist-post-malone":   ("Post Malone",        "pop-trap · melancholy"),
            "mood_artist-bigbabytape":   ("Big Baby Tape",      "RU trap"),
            "mood_artist-morgen":        ("Morgenshtern",       "RU provocation"),
            "mood_artist-zemfira":       ("Zemfira",            "RU legend"),
            "mood_artist-skriptonit":    ("Skriptonit",         "RU hip-hop"),
            "mood_artist-anna-asti":     ("ANNA ASTI",          "RU pop"),
            "mood_artist-macan":         ("Macan",              "RU pop-rap 2024"),
            "mood_artist-phonk-art":     ("The phonk wave",     "Kordhell · ICEGERGERT"),
            "mood_artist-bts":           ("BTS",                "K-pop icon"),
            "mood_artist-blackpink":     ("BLACKPINK",          "K-pop power"),
            "mood_artist-newjeans":      ("NewJeans",           "K-pop new gen"),
            "mood_artist-radiohead":     ("Radiohead",          "alt rock · philosophy"),
            "mood_artist-coldplay":      ("Coldplay",           "stadium · emotion"),
        },
    },
    "rodnye_00e": {
        "name_en": "The familiar 2000s (RU)",
        "blurb_en": "Who defines your noughties vibe?",
        "items": {
            "tatu":             ("t.A.T.u.",                 "edgy schoolgirls · Ya soshla s uma · Nas ne dogonyat"),
            "alsu":             ("Alsou",                    "bright pop fairy tale · Zimnij Son · Inogda"),
            "diskoteka_avariya":("Diskoteka Avariya",        "rowdy DJs · Pej Pivo · Novogodnyaya"),
            "ruki_vverh":       ("Ruki Vverh",               "dancefloor and tears · Kroshka Moya · 18 mne uzhe"),
            "ivanushki":        ("Ivanushki International",  "boys-next-door · Topolinyj Pukh · Kukla"),
            "gubin":            ("Andrey Gubin",             "autumn romantic · Milaya Moya · Zima-Kholoda"),
            "korni":            ("Korni",                    "first Fabrika season · Plakala Beryoza · Ty Uznaesh Eyo"),
            "serebro":          ("Serebro",                  "sexy rebels · Song #1 · Mama Lyuba"),
            "via_gra":          ("VIA Gra",                  "lavish trio · Popytka No 5 · Ne Ostavlyaj Menya"),
            "leningrad":        ("Leningrad",                "gop-punk with profanity · WWW · Dachniki"),
            "zemfira":          ("Zemfira",                  "fragile protest · Iskala · Romashki"),
            "smash":            ("Smash!!",                  "two pretty boys · Belle · Molitva"),
            "t_killah":         ("Timati",                   "stardom swagger · Ne Skhodi S Uma · V Klube"),
            "fabrika":          ("Fabrika",                  "ironic girls · Pro Lyubov · Devushki Fabrichnye"),
            "dima_bilan":       ("Dima Bilan",               "million-dollar smile · Never Let You Go · Nochnoj Khuligan"),
            "nak":              ("Kraski",                   "sweet simplicity · Starshij Brat · Oranzhevoe Solntse"),
        },
    },
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats_by_id = {c.get("id"): c for c in raw}
    cats_done, items_done, items_missing = 0, 0, 0
    for cat_id, tr in TRANSLATIONS.items():
        cat = cats_by_id.get(cat_id)
        if cat is None:
            print(f"  [skip] {cat_id} not found"); continue
        cat["name_en"] = tr["name_en"]; cat["blurb_en"] = tr["blurb_en"]
        items_tr = tr.get("items", {}); n = 0
        for it in cat.get("items", []):
            iid = it.get("id")
            if iid in items_tr:
                it["name_en"], it["ctx_en"] = items_tr[iid]; n += 1
            else:
                items_missing += 1; print(f"    [warn] {cat_id}/{iid}")
        cats_done += 1; items_done += n
        print(f"  ✓ {cat_id}: {n}/{len(cat.get('items', []))}")
    print(f"\nCats: {cats_done}, items: {items_done}, missing: {items_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.batch3.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
