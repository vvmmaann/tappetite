"""
Batch 1: cluster Кино / Films — 9 categories, 146 items.
Перевод name + blurb для категории + name + ctx для каждого item.
Архетипы НЕ переводим в этом batch (этап B позже).
Атомарная запись с timestamped backup.
"""
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

# Each entry: cat_id -> {name_en, blurb_en, items: {item_id: (name_en, ctx_en)}}
TRANSLATIONS = {
    "hollywood_actors_50plus": {
        "name_en": "Hollywood actors · 50+",
        "blurb_en": "Pacino, De Niro, Hopkins and 13 more names from the New Hollywood era",
        "items": {
            "pacino":     ("Al Pacino",         "1940 · 1 Oscar · 'Scarface'"),
            "deniro":     ("Robert De Niro",    "1943 · 2 Oscars · 'Taxi Driver'"),
            "hopkins":    ("Anthony Hopkins",   "1937 · 2 Oscars · 'The Silence of the Lambs'"),
            "freeman":    ("Morgan Freeman",    "1937 · 1 Oscar · 'The Shawshank Redemption'"),
            "nicholson":  ("Jack Nicholson",    "1937 · 3 Oscars · 'The Shining'"),
            "eastwood":   ("Clint Eastwood",    "1930 · 2 Oscars · 'Dirty Harry'"),
            "hoffman":    ("Dustin Hoffman",    "1937 · 2 Oscars · 'Tootsie'"),
            "caine":      ("Michael Caine",     "1933 · 2 Oscars · 'The Dark Knight'"),
            "mckellen":   ("Ian McKellen",      "1939 · 0 Oscars · 'The Lord of the Rings'"),
            "stallone":   ("Sylvester Stallone","1946 · 0 Oscars · 'Rocky'"),
            "ford":       ("Harrison Ford",     "1942 · 0 Oscars · 'Blade Runner'"),
            "kingsley":   ("Ben Kingsley",      "1943 · 1 Oscar · 'Gandhi'"),
            "denzel":     ("Denzel Washington", "1954 · 2 Oscars · 'Training Day'"),
            "hanks":      ("Tom Hanks",         "1956 · 2 Oscars · 'Forrest Gump'"),
            "samjackson": ("Samuel L. Jackson", "1948 · 0 Oscars · 'Pulp Fiction'"),
            "costner":    ("Kevin Costner",     "1955 · 2 Oscars · 'Dances with Wolves'"),
            "hollywood_actors_50plus-dzhordzh-kluni": ("George Clooney", "1961 · 1 Oscar · 'Syriana'"),
            "hollywood_actors_50plus-bred-pitt":      ("Brad Pitt",      "1963 · 1 Oscar · 'Once Upon a Time in Hollywood'"),
        },
    },
    "hollywood_actresses_50plus": {
        "name_en": "Hollywood actresses · 50+",
        "blurb_en": "Streep, Mirren, Foster and 13 more names from the era",
        "items": {
            "streep":      ("Meryl Streep",         "1949 · 3 Oscars · 'Sophie's Choice'"),
            "mirren":      ("Helen Mirren",         "1945 · 1 Oscar · 'The Queen'"),
            "sarandon":    ("Susan Sarandon",       "1946 · 1 Oscar · 'Dead Man Walking'"),
            "field":       ("Sally Field",          "1946 · 2 Oscars · 'Norma Rae'"),
            "foster":      ("Jodie Foster",         "1962 · 2 Oscars · 'The Silence of the Lambs'"),
            "weaver":      ("Sigourney Weaver",     "1949 · 0 Oscars · 'Alien'"),
            "pfeiffer":    ("Michelle Pfeiffer",    "1958 · 0 Oscars · 'Batman Returns'"),
            "hunter":      ("Holly Hunter",         "1958 · 1 Oscar · 'The Piano'"),
            "rosselini":   ("Isabella Rossellini",  "1952 · 0 Oscars · 'Blue Velvet'"),
            "zetajones":   ("Catherine Zeta-Jones", "1969 · 1 Oscar · 'Chicago'"),
            "macdowell":   ("Andie MacDowell",      "1958 · 0 Oscars · 'Groundhog Day'"),
            "glennclose":  ("Glenn Close",          "1947 · 0 Oscars · 'Dangerous Liaisons'"),
            "huston":      ("Anjelica Huston",      "1951 · 1 Oscar · 'Prizzi's Honor'"),
            "demimoore":   ("Demi Moore",           "1962 · 0 Oscars · 'Ghost'"),
            "sharonstone": ("Sharon Stone",         "1958 · 0 Oscars · 'Basic Instinct'"),
            "keaton":      ("Diane Keaton",         "1946 · 1 Oscar · 'Annie Hall'"),
        },
    },
    "hollywood_actors_30_50": {
        "name_en": "Hollywood actors · 30-50",
        "blurb_en": "Gosling, Driver, Chalamet and 13 more names defining cinema right now",
        "items": {
            "gosling":  ("Ryan Gosling",         "'Drive' · 'La La Land' · 'Barbie'"),
            "hardy":    ("Tom Hardy",            "'Mad Max: Fury Road' · 'Inception'"),
            "cmurphy":  ("Cillian Murphy",       "'Peaky Blinders' · 'Oppenheimer'"),
            "driver":   ("Adam Driver",          "'Marriage Story' · 'Star Wars'"),
            "oisaac":   ("Oscar Isaac",          "'Ex Machina' · 'Dune'"),
            "mbjordan": ("Michael B. Jordan",    "'Creed' · 'Black Panther'"),
            "garfield": ("Andrew Garfield",      "'The Social Network' · 'Tick, Tick... Boom!'"),
            "jgyl":     ("Jake Gyllenhaal",      "'Donnie Darko' · 'Nightcrawler'"),
            "chalamet": ("Timothée Chalamet",    "'Call Me By Your Name' · 'Dune'"),
            "keoghan":  ("Barry Keoghan",        "'Saltburn' · 'The Banshees of Inisherin'"),
            "mescal":   ("Paul Mescal",          "'Aftersun' · 'Normal People'"),
            "butler":   ("Austin Butler",        "'Elvis' · 'Dune: Part Two'"),
            "efron":    ("Zac Efron",            "'The Iron Claw' · 'High School Musical'"),
            "edgerton": ("Taron Egerton",        "'Rocketman' · 'Kingsman'"),
            "patel":    ("Dev Patel",            "'Slumdog Millionaire' · 'The Green Knight'"),
            "teller":   ("Miles Teller",         "'Whiplash' · 'Top Gun: Maverick'"),
        },
    },
    "hollywood_actresses_30_50": {
        "name_en": "Hollywood actresses · 30-50",
        "blurb_en": "Stone, Robbie, Zendaya and 13 more names defining cinema right now",
        "items": {
            "estone":    ("Emma Stone",         "'La La Land' · 'Poor Things'"),
            "portman":   ("Natalie Portman",    "'Black Swan' · 'Léon'"),
            "jlaw":      ("Jennifer Lawrence",  "'Silver Linings Playbook' · 'The Hunger Games'"),
            "mrobbie":   ("Margot Robbie",      "'I, Tonya' · 'Barbie'"),
            "fpugh":     ("Florence Pugh",      "'Midsommar' · 'Little Women'"),
            "zendaya":   ("Zendaya",            "'Euphoria' · 'Dune'"),
            "anad":      ("Ana de Armas",       "'Knives Out' · 'Blade Runner 2049'"),
            "sronan":    ("Saoirse Ronan",      "'Lady Bird' · 'Brooklyn'"),
            "atjoy":     ("Anya Taylor-Joy",    "'The Queen's Gambit' · 'Furiosa'"),
            "gadot":     ("Gal Gadot",          "'Wonder Woman'"),
            "larson":    ("Brie Larson",        "'Room' · 'Captain Marvel'"),
            "ridley":    ("Daisy Ridley",       "'Star Wars: The Force Awakens'"),
            "knightley": ("Keira Knightley",    "'Pride & Prejudice' · 'Atonement'"),
            "mcadams":   ("Rachel McAdams",     "'The Notebook' · 'Spotlight'"),
            "lnyongo":   ("Lupita Nyong'o",     "'12 Years a Slave' · 'Us'"),
            "vikander":  ("Alicia Vikander",    "'Ex Machina' · 'The Danish Girl'"),
        },
    },
    "memorable_characters": {
        "name_en": "Most memorable movie characters",
        "blurb_en": "16 characters who stole the spotlight - or became the show themselves",
        "items": {
            "jokerledger": ("Joker · Heath Ledger",     "'The Dark Knight' 2008"),
            "jokerphoen":  ("Joker · Joaquin Phoenix",  "'Joker' 2019"),
            "lecter":      ("Hannibal Lecter",          "'The Silence of the Lambs' 1991"),
            "chigurh":     ("Anton Chigurh",            "'No Country for Old Men' 2007"),
            "landa":       ("Hans Landa",               "'Inglourious Basterds' 2009"),
            "bateman":     ("Patrick Bateman",          "'American Psycho' 2000"),
            "amydunne":    ("Amy Dunne",                "'Gone Girl' 2014"),
            "vader":       ("Darth Vader",              "'Star Wars' 1977+"),
            "thanos":      ("Thanos",                   "'Infinity War' 2018"),
            "voldemort":   ("Voldemort",                "'Harry Potter' 2001+"),
            "pennywise":   ("Pennywise",                "'It' 2017"),
            "ratched":     ("Nurse Ratched",            "'One Flew Over the Cuckoo's Nest' 1975"),
            "normanbates": ("Norman Bates",             "'Psycho' 1960"),
            "alex":        ("Alex DeLarge",             "'A Clockwork Orange' 1971"),
            "goeth":       ("Amon Göth",                "'Schindler's List' 1993"),
            "roybatty":    ("Roy Batty",                "'Blade Runner' 1982"),
        },
    },
    "actors_without_oscar": {
        "name_en": "Best actors without an Oscar",
        "blurb_en": "Snubbed by the Academy but loved by us",
        "items": {
            "johnny-depp":         ("Johnny Depp",         "Edward Scissorhands · Captain Jack Sparrow · no statuette"),
            "keanu-reeves":        ("Keanu Reeves",        "The Matrix · John Wick · zero nominations"),
            "bradley-cooper":      ("Bradley Cooper",      "A Star Is Born · Silver Linings Playbook · 9 Oscar nominations"),
            "alan-rickman":        ("Alan Rickman",        "Snape · Hans Gruber · the Oscar passed him by"),
            "jim-carrey":          ("Jim Carrey",          "Eternal Sunshine · The Truman Show · zero nominations"),
            "tom-cruise":          ("Tom Cruise",          "Magnolia · Interview with the Vampire · no Oscar"),
            "harrison-ford":       ("Harrison Ford",       "Indiana Jones · Han Solo · 1 nomination"),
            "edward-norton":       ("Edward Norton",       "Fight Club · The Illusionist · 2 nominations"),
            "ralph-fiennes":       ("Ralph Fiennes",       "Schindler's List · Voldemort · 2 nominations"),
            "jake-gyllenhaal":     ("Jake Gyllenhaal",     "Brokeback Mountain · Zodiac · zero Oscar nominations"),
            "donald-sutherland":   ("Donald Sutherland",   "M*A*S*H · Ordinary People · never got the Oscar"),
            "peter-otoole":        ("Peter O'Toole",       "Lawrence of Arabia · 8 nominations · 0 wins"),
            "richard-burton":      ("Richard Burton",      "7 nominations · Hamlet on Broadway · no Oscar"),
            # NB: id 'joaquin-phoenix-pre' has Russian name 'Джош Бролин' — preserved as Josh Brolin.
            "joaquin-phoenix-pre": ("Josh Brolin",         "No Country for Old Men · Mystic River · no Oscar"),
            "michael-fassbender":  ("Michael Fassbender",  "Shame · 12 Years a Slave · 1 nomination · no win"),
            "steve-buscemi":       ("Steve Buscemi",       "Scorsese regular · Pulp Fiction · The Sopranos"),
        },
    },
    "female_power_films": {
        "name_en": "Films of female strength",
        "blurb_en": "Which film inspires and motivates you most?",
        "items": {
            "legally-blonde":        ("Legally Blonde",            "2001 · Reese Witherspoon · Harvard · stereotypes"),
            "devil-wears-prada":     ("The Devil Wears Prada",     "2006 · Meryl Streep · fashion · career"),
            "erin-brockovich":       ("Erin Brockovich",           "2000 · Oscar for Roberts · true story · court"),
            "morning-glory":         ("Morning Glory",             "2010 · Rachel McAdams · producer · saves the show"),
            "the-help":              ("The Help",                  "2011 · Viola Davis & Emma Stone · US South · 1960s"),
            "hidden-figures":        ("Hidden Figures",            "2016 · NASA · three Black women mathematicians"),
            "thelma-louise":         ("Thelma & Louise",           "1991 · Ridley Scott · escape · freedom"),
            "norma-rae":             ("Norma Rae",                 "1979 · Best Actress Oscar · union · working class"),
            "mona-lisa-smile":       ("Mona Lisa Smile",           "2003 · Julia Roberts · 1950s · feminism"),
            "contact":               ("Contact",                   "1997 · Jodie Foster · science · first contact"),
            "mad-max-fury-road":     ("Mad Max: Fury Road",        "2015 · Charlize Theron · post-apocalypse · revolt"),
            "promising-young-woman": ("Promising Young Woman",     "2020 · Oscar for Mulligan · revenge · feminism"),
            "nine-to-five":          ("9 to 5",                    "1980 · Fonda · Tomlin · Parton · office revolt"),
            "working-girl":          ("Working Girl",              "1988 · Melanie Griffith · Wall Street · career"),
            "wonder-woman":          ("Wonder Woman",              "2017 · Gal Gadot · DC · female superhero"),
            "silkwood":              ("Silkwood",                  "1983 · Meryl Streep · nuclear plant · truth"),
        },
    },
    "my_film_genre": {
        "name_en": "Your film genre for life",
        "blurb_en": "Genre sets the mood",
        "items": {
            "drama":       ("Drama",        "emotion · fates · serious view"),
            "comedy":      ("Comedy",       "laughter · funny situations · ease"),
            "thriller":    ("Thriller",     "nerves · tension · sudden twist"),
            "sci_fi":      ("Sci-Fi",       "space · technology · the future"),
            "romcom":      ("Rom-com",      "smiles · dating · happy ending"),
            "horror":      ("Horror",       "fear · blood · sleepless nights"),
            "action":      ("Action",       "chases · explosions · muscle"),
            "detective":   ("Detective",    "puzzle · clues · whodunit"),
            "western":     ("Western",      "cowboys · the Old West · duels"),
            "crime":       ("Crime",        "gangsters · money · the law"),
            "adventure":   ("Adventure",    "treasure hunts · maps · danger"),
            "mystery":     ("Mystery",      "the supernatural · secrets · darkness"),
            "military":    ("War film",     "war · heroism · trenches"),
            "history":     ("Historical",   "the past · kings · costumes"),
            "fantasy":     ("Fantasy",      "magic · elves · dragons"),
            "documentary": ("Documentary",  "reality · facts · no varnish"),
        },
    },
    "movie_character_like_you": {
        "name_en": "The movie character you're most like",
        "blurb_en": "Not by looks - by behavior and choices",
        "items": {
            "forrest-gump":     ("Forrest Gump",        "moves forward · doesn't ask many questions"),
            "the-dude":         ("The Dude",            "(The Big Lebowski) · stays chill · things work themselves out"),
            "jo-march":         ("Jo March",            "Little Women · writes · doesn't fit in · own path"),
            "tony-stark":       ("Tony Stark",          "Iron Man · solves with brains · ego"),
            "indiana-jones":    ("Indiana Jones",       "walks into the unknown · improvises · makes it"),
            "walter-mitty":     ("Walter Mitty",        "dreams · one day decides · goes"),
            "sherlock":         ("Sherlock Holmes",     "sees more than others · logic · solitude"),
            "am-lie":           ("Amélie",              "lives in her own world · helps quietly"),
            "michael-corleone": ("Michael Corleone",    "The Godfather · stays silent · then settles everything"),
            "katniss":          ("Katniss Everdeen",    "The Hunger Games · protects her own · carries the weight"),
            "hermione":         ("Hermione Granger",    "prepares · knows the rules · still breaks them"),
            "tyler-durden":     ("Tyler Durden",        "Fight Club · revolt · doesn't accept the system"),
            "scarlett-ohara":   ("Scarlett O'Hara",     "Gone with the Wind · survives · takes what she wants"),
            "andy-dufresne":    ("Andy Dufresne",       "The Shawshank Redemption · endures · plans · free"),
            "ethan-hunt":       ("Ethan Hunt",          "Mission: Impossible · takes the lead · doesn't ask for help"),
            "lara-croft":       ("Lara Croft",          "handles it alone · doesn't wait for rescue · in motion"),
        },
    },
}


def main() -> int:
    if not CATEGORIES_JSON.exists():
        print(f"ERROR: {CATEGORIES_JSON} not found")
        return 1

    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        print("ERROR: expected list at root")
        return 1

    cats_by_id = {c.get("id"): c for c in raw}
    total_cats_done = 0
    total_items_done = 0
    total_items_missing = 0

    for cat_id, tr in TRANSLATIONS.items():
        cat = cats_by_id.get(cat_id)
        if cat is None:
            print(f"  [skip] {cat_id} — not found in JSON")
            continue
        cat["name_en"] = tr["name_en"]
        cat["blurb_en"] = tr["blurb_en"]
        items_tr = tr.get("items", {})
        items_done_for_cat = 0
        for it in cat.get("items", []):
            iid = it.get("id")
            if iid in items_tr:
                name_en, ctx_en = items_tr[iid]
                it["name_en"] = name_en
                it["ctx_en"] = ctx_en
                items_done_for_cat += 1
            else:
                total_items_missing += 1
                print(f"    [warn] {cat_id}/{iid} — no translation in script")
        total_cats_done += 1
        total_items_done += items_done_for_cat
        print(f"  ✓ {cat_id}: name+blurb + {items_done_for_cat}/{len(cat.get('items', []))} items")

    print()
    print(f"Categories translated: {total_cats_done}")
    print(f"Items translated:      {total_items_done}")
    if total_items_missing:
        print(f"Items missing:         {total_items_missing}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.films_en.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak)
    print(f"Backup: {bak.name}")

    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON)
    print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
