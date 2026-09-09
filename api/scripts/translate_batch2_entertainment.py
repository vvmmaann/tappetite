"""Batch 2: Сериалы (1) + Аниме (1) + Мультфильмы (1) + Игры (3) = 6 cats, 96 items."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

TRANSLATIONS = {
    "cult_90s_series": {
        "name_en": "Cult '90s TV series",
        "blurb_en": "Which series did you fight for the remote over?",
        "items": {
            "twin_peaks":            ("Twin Peaks",                           "mystery · the owls aren't what they seem · Agent Cooper"),
            "friends":               ("Friends",                              "six friends · Central Perk · how you doin'"),
            "x_files":               ("The X-Files",                          "files · the truth is out there · Mulder & Scully"),
            "alf":                   ("ALF",                                  "alien · loves cats · sarcasm"),
            "beverly_hills":         ("Beverly Hills, 90210",                 "rich kids · school · Brandon and Kelly"),
            "santa_barbara":         ("Santa Barbara",                        "soap opera · twists of fate · Cruz and Eden"),
            "wild_angel":            ("Wild Angel (Muñeca brava)",            "Argentine passion · Ivo and Milagros · Cholito"),
            "buffy":                 ("Buffy the Vampire Slayer",             "vampire-slaying girl · Sunnydale High · the Chosen One"),
            "er":                    ("ER",                                   "medical drama · Chicago hospital · George Clooney"),
            "melrose_place":         ("Melrose Place",                        "90210 spin-off · apartment block · scandals"),
            "simpsons":              ("The Simpsons",                         "yellow family · Springfield · d'oh"),
            "married_with_children": ("Married... with Children",             "Al Bundy · socks · brutal sitcom"),
            "beavis":                ("Beavis and Butt-Head",                 "two teens · MTV · uh huh huh"),
            "ulitsy_razbityh_fonarey":("Streets of Broken Lights",            "Russian cops · Captain Larin · gangster Petersburg"),
            "agent_natbez":          ("Agent of National Security",           "Lyokha Nikolayev · Russian secret service · '90s Petersburg"),
            "tropikanka":            ("Tropikanka",                           "Brazilian passion · the estate · love and hate"),
        },
    },
    "anime_essential": {
        "name_en": "Anime actually worth watching",
        "blurb_en": "16 titles to start with - or come back to",
        "items": {
            "aot":        ("Attack on Titan",                  "2013 · MAPPA · darkness and philosophy"),
            "deathnote":  ("Death Note",                       "2006 · Madhouse · cat and mouse"),
            "fmab":       ("Fullmetal Alchemist: Brotherhood", "2009 · Bones · alchemy and brotherhood"),
            "hxh":        ("Hunter x Hunter",                  "2011 · Madhouse · shonen with depth"),
            "steins":     ("Steins;Gate",                      "2011 · White Fox · time machine"),
            "violet":     ("Violet Evergarden",                "2018 · Kyoto Animation · letters and feelings"),
            "vinland":    ("Vinland Saga",                     "2019 · Wit Studio · vikings and revenge"),
            "jjk":        ("Jujutsu Kaisen",                   "2020 · MAPPA · curses"),
            "spyfamily":  ("Spy x Family",                     "2022 · Wit · spy family"),
            "codegeass":  ("Code Geass",                       "2006 · Sunrise · mecha and intrigue"),
            "mia":        ("Made in Abyss",                    "2017 · Kinema Citrus · cute and terrifying"),
            "klms":       ("Your Lie in April",                "2014 · A-1 · music and tears"),
            "demonslay":  ("Demon Slayer",                     "2019 · ufotable · sword and demons"),
            "evangelion": ("Neon Genesis Evangelion",          "1995 · Gainax · mecha and psychology"),
            "onepiece":   ("One Piece",                        "1999 · Toei · the endless voyage"),
            "naruto":     ("Naruto: Shippuden",                "2007 · Pierrot · ninja and friendship"),
        },
    },
    "childhood_cartoons": {
        "name_en": "Best cartoon series from childhood",
        "blurb_en": "16 cartoons that shaped a generation's taste, humor, and traumas",
        "items": {
            "tomjerry":  ("Tom and Jerry",                              "1940+ · Hanna-Barbera · cat and mouse"),
            "wolfhare":  ("Nu, pogodi!",                                "1969 · Soyuzmultfilm · Soviet classic"),
            "spongebob": ("SpongeBob SquarePants",                      "1999 · Nickelodeon · absurd"),
            "simpsons":  ("The Simpsons (early seasons)",               "1989 · Fox · satire of America"),
            "tmnt":      ("Teenage Mutant Ninja Turtles",               "1987 · CBS · pizza and battle"),
            "pokemon":   ("Pokémon",                                    "1997 · TV Tokyo · 'gotta catch 'em all'"),
            "smesh":     ("Smeshariki (Kikoriki)",                      "2003 · Russia · philosophy for the small"),
            "avatar":    ("Avatar: The Last Airbender",                 "2005 · Nickelodeon · the elements"),
            "gravity":   ("Gravity Falls",                              "2012 · Disney · weirdness"),
            "adventime": ("Adventure Time",                             "2010 · CN · post-apoc and magic"),
            "scooby":    ("Scooby-Doo",                                 "1969 · Hanna-Barbera · detective"),
            "ducktales": ("DuckTales",                                  "1987 · Disney · treasures"),
            "chipdale":  ("Chip 'n Dale: Rescue Rangers",               "1989 · Disney · little heroes"),
            "southpark": ("South Park",                                 "1997 · CC · uncompromising satire"),
            "futurama":  ("Futurama",                                   "1999 · Fox · sci-fi satire"),
            "rickmorty": ("Rick and Morty",                             "2013 · Adult Swim · the multiverse"),
        },
    },
    "comeback_games": {
        "name_en": "Games you want to come back to",
        "blurb_en": "16 games that still live in your memory",
        "items": {
            "witcher3":    ("The Witcher 3: Wild Hunt",       "2015 · CDPR · open-world RPG"),
            "rdr2":        ("Red Dead Redemption 2",          "2018 · Rockstar · western"),
            "lou":         ("The Last of Us",                 "2013 · Naughty Dog · post-apoc"),
            "darksouls":   ("Dark Souls",                     "2011 · FromSoftware · hard and beautiful"),
            "minecraft":   ("Minecraft",                      "2011 · Mojang · blocks and creation"),
            "skyrim":      ("The Elder Scrolls V: Skyrim",    "2011 · Bethesda · fantasy open-world"),
            "gtasa":       ("GTA: San Andreas",               "2004 · Rockstar · the '90s and Los Santos"),
            "masseffect2": ("Mass Effect 2",                  "2010 · BioWare · space RPG"),
            "hollow":      ("Hollow Knight",                  "2017 · Team Cherry · metroidvania"),
            "stardew":     ("Stardew Valley",                 "2016 · ConcernedApe · farm and calm"),
            "discoelys":   ("Disco Elysium",                  "2019 · ZA/UM · detective and prose"),
            "hades":       ("Hades",                          "2020 · Supergiant · roguelike myths"),
            "gow2018":     ("God of War (2018)",              "2018 · Santa Monica · father and son"),
            "nier2":       ("Nier: Automata",                 "2017 · Platinum · philosophy and androids"),
            "undertale":   ("Undertale",                      "2015 · Toby Fox · meta and choice"),
            "journey":     ("Journey",                        "2012 · thatgamecompany · poetic"),
        },
    },
    "addictive_game": {
        "name_en": "Best game to get hooked on",
        "blurb_en": "The one you keep coming back to",
        "items": {
            "addictive_game-minecraft":     ("Minecraft",            "blocks · world · infinity"),
            "addictive_game-roblox":        ("Roblox",               "thousands of mini-games"),
            "addictive_game-fortnite":      ("Fortnite",             "battle royale · skins"),
            "addictive_game-valorant":      ("Valorant",             "tactical shooter · agents"),
            "addictive_game-cs2":           ("CS2",                  "tactical shooter · esports"),
            "addictive_game-dota2":         ("Dota 2",               "MOBA · 5v5 · deep"),
            "addictive_game-lol":           ("League of Legends",    "MOBA · mainstream"),
            "addictive_game-genshin":       ("Genshin Impact",       "open-world · gacha"),
            "addictive_game-ml":            ("Mobile Legends",       "MOBA on phone"),
            "addictive_game-pubg":          ("PUBG",                 "battle royale · realistic"),
            "addictive_game-wow":           ("World of Warcraft",    "MMORPG · the legend"),
            "addictive_game-hearthstone":   ("Hearthstone",          "card game · Blizzard"),
            "addictive_game-clash-royale":  ("Clash Royale",         "card strategy"),
            "addictive_game-brawl-stars":   ("Brawl Stars",          "arena · 3v3"),
            "addictive_game-stardew":       ("Stardew Valley",       "farm · cozy"),
            "addictive_game-hollow-knight": ("Hollow Knight",        "metroidvania · beautiful"),
            "addictive_game-elden-ring":    ("Elden Ring",           "open-world Souls"),
            "addictive_game-witcher3":      ("The Witcher 3",        "RPG · story · Geralt"),
            "addictive_game-gta5":          ("GTA V",                "open-world · chaos"),
            "addictive_game-rdr2":          ("Red Dead Redemption 2","cowboys · cinematic"),
            "addictive_game-cyberpunk":     ("Cyberpunk 2077",       "Night City · RPG"),
            "addictive_game-baldurs":       ("Baldur's Gate 3",      "RPG · D&D · story"),
            "addictive_game-among-us":      ("Among Us",             "social deduction"),
            "addictive_game-apex":          ("Apex Legends",         "battle royale + heroes"),
            "addictive_game-overwatch2":    ("Overwatch 2",          "team shooter · heroes"),
            "addictive_game-rocket-league": ("Rocket League",        "soccer with cars"),
            "addictive_game-animal-cross":  ("Animal Crossing",      "cozy · island"),
            "addictive_game-sims4":         ("The Sims 4",           "life simulator"),
            "addictive_game-honkai-rail":   ("Honkai: Star Rail",    "gacha · story"),
            "addictive_game-poe":           ("Path of Exile",        "ARPG · hardcore"),
            "addictive_game-terraria":      ("Terraria",             "2D Minecraft · crafting"),
            "addictive_game-stray":         ("Stray",                "cat · cyberpunk · beautiful"),
        },
    },
    "gaming_style": {
        "name_en": "Your gaming style",
        "blurb_en": "How you behave in the virtual world",
        "items": {
            "gaming_style-solo-grinder":     ("Solo grinder",       "I play alone · grinding"),
            "gaming_style-teammate":         ("Team player",        "comfortable in a squad"),
            "gaming_style-toxic-carry":      ("Toxic carry",        "I carry and rage"),
            "gaming_style-builder":          ("Builder",            "farm · bases · megacities"),
            "gaming_style-explorer":         ("Explorer",           "I open the map"),
            "gaming_style-collector":        ("Collector",          "achievements · skins"),
            "gaming_style-speedrunner":      ("Speedrunner",        "against the clock · optimization"),
            "gaming_style-casual":           ("Casual",             "an hour a week"),
            "gaming_style-pro-esports":      ("Pro / esports",      "training · tournaments"),
            "gaming_style-modder":           ("Modder",             "I change the game"),
            "gaming_style-lore-guru":        ("Lore guru",          "I read everything about the game"),
            "gaming_style-streamer":         ("Streamer",           "Twitch · YouTube"),
            "gaming_style-emotional":        ("Emotional player",   "I play on feelings"),
            "gaming_style-tactician":        ("Tactician",          "strategy · plan"),
            "gaming_style-peaceful":         ("Peaceful",           "Civ · I kill no one"),
            "gaming_style-rpg-philosopher":  ("RPG philosopher",    "lore > combat · dialogue"),
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
            print(f"  [skip] {cat_id} not found")
            continue
        cat["name_en"] = tr["name_en"]
        cat["blurb_en"] = tr["blurb_en"]
        items_tr = tr.get("items", {})
        n = 0
        for it in cat.get("items", []):
            iid = it.get("id")
            if iid in items_tr:
                it["name_en"], it["ctx_en"] = items_tr[iid]
                n += 1
            else:
                items_missing += 1
                print(f"    [warn] {cat_id}/{iid} no translation")
        cats_done += 1; items_done += n
        print(f"  ✓ {cat_id}: {n}/{len(cat.get('items', []))}")
    print(f"\nCats: {cats_done}, items: {items_done}, missing: {items_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.batch2.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak)
    print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON)
    print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
