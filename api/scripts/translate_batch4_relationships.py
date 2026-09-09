"""Batch 4: Отношения / Relationships — 16 cats, 224 items."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

TRANSLATIONS = {
    "romantic_archetype": {
        "name_en": "Your romantic archetype",
        "blurb_en": "How you actually love, not how you're supposed to. 16 attachment styles and love languages",
        "items": {
            "words":          ("Love in words",           "compliments · messages · spoken aloud"),
            "actions":        ("Love in actions",         "deeds matter more than words"),
            "time":           ("Love in time",            "quality together · full attention"),
            "gifts":          ("Love in gifts",           "thoughtful little things · tokens of attention"),
            "touch":          ("Love in touch",           "hugs · hands · physical contact"),
            "slow_burn":      ("Slow burn",               "we get to know each other for years · no rush"),
            "lightning":      ("Lightning connection",    "from the first night · everything's clear"),
            "friends_first":  ("Friends first",           "foundation matters more than the spark"),
            "adventures":     ("Shared adventures",       "travel · risk · new things together"),
            "quiet_evenings": ("Quiet evenings at home",  "movies · blanket · silence"),
            "deep_talks":     ("Late-night talks",        "until morning · about heavy stuff"),
            "daily_care":     ("Daily care",              "morning coffee · the small things every day"),
            "support":        ("Career support",          "we build each other up"),
            "playful":        ("Playfulness",             "teasing · flirting · lightness"),
            "rituals":        ("Couple rituals",          "'our' Saturday · traditions"),
            "free_in_pair":   ("Freedom in a pair",       "separate worlds · shared base"),
        },
    },
    "dating_taste": {
        "name_en": "Your dating taste",
        "blurb_en": "16 sympathy scenarios: mind, humor, calm, energy, style, ambition",
        "items": {
            "dt_mind":   ("Mind and depth of conversation", "brains come first"),
            "dt_humor":  ("Humor and lightness",            "laughing together"),
            "dt_calm":   ("Calm and stability",             "no swings"),
            "dt_energy": ("Energy and drive",               "life sparks"),
            "dt_style":  ("Style and aesthetics",           "beauty matters"),
            "dt_amb":    ("Ambition and goals",             "the person has direction"),
            "dt_warm":   ("Tenderness and attention",       "softness is strength"),
            "dt_truth":  ("Honesty even when it hurts",     "no masks"),
            "dt_chem":   ("Chemistry at first sight",       "physics doesn't lie"),
            "dt_val":    ("Shared values",                  "looking the same direction"),
            "dt_indep":  ("Independence",                   "not clingy"),
            "dt_brave":  ("Courage and decisiveness",       "makes the first move"),
            "dt_home":   ("Warmth and home",                "feels like home with you"),
            "dt_myst":   ("Mystery",                        "not easy to read"),
            "dt_grow":   ("Growing together",               "we pull each other up"),
            "dt_quiet":  ("Just nice to be near",           "no words needed"),
        },
    },
    "relationship_values": {
        "name_en": "What matters more in a relationship",
        "blurb_en": "16 values: trust, freedom, care, passion, stability",
        "items": {
            "rv_trust": ("Trust",                       "without it, nothing"),
            "rv_free":  ("Freedom and space",           "don't smother each other"),
            "rv_care":  ("Care in small things",        "morning coffee, evening blanket"),
            "rv_pass":  ("Passion and attraction",      "the spark won't fade"),
            "rv_stab":  ("Stability",                   "predictability heals"),
            "rv_hon":   ("Honesty",                     "truth at any cost"),
            "rv_goal":  ("Shared goals",                "looking the same direction"),
            "rv_humor": ("Humor and ease together",     "laughing together every day"),
            "rv_acc":   ("Unconditional acceptance",    "however you are"),
            "rv_grow":  ("Growing together",            "both growing"),
            "rv_space": ("Personal space",              "not melting into one"),
            "rv_loyal": ("Loyalty",                     "one and only"),
            "rv_sup":   ("Support in hard moments",     "not alone in the fight"),
            "rv_adv":   ("Shared adventures",           "life as a journey"),
            "rv_resp":  ("Respect for difference",      "we're not the same"),
            "rv_quiet": ("Quiet closeness without words","just being near"),
        },
    },
    "first_date_pay": {
        "name_en": "First date — who pays?",
        "blurb_en": "8 takes on one of dating's liveliest debates. Pick what's closest to you",
        "items": {
            "fdp_invite":  ("Whoever invited pays",            "always"),
            "fdp_5050":    ("Strict 50/50",                    "everyone for themselves"),
            "fdp_man":     ("The man pays on the first date",  "after that, they figure it out"),
            "fdp_first":   ("Whoever reaches for the card",    "that one pays"),
            "fdp_pre":     ("Agreed in advance",               "no surprises"),
            "fdp_more":    ("Whoever earns more",              "that one pays"),
            "fdp_gesture": ("The woman pays — a nice gesture", "just once"),
            "fdp_neutral": ("Doesn't matter at all",           "the evening is what counts"),
        },
    },
    "dating_2025": {
        "name_en": "How to meet people in 2025?",
        "blurb_en": "8 ways. Where would you really find your person",
        "items": {
            "d25_apps":   ("Dating apps",                "Tinder, Bumble, Hinge"),
            "d25_irl":    ("In real life",               "chance, fate"),
            "d25_friend": ("Through mutual friends",     "old school"),
            "d25_inst":   ("On Instagram",               "slide into DMs"),
            "d25_event":  ("At an event",                "or through a hobby"),
            "d25_work":   ("At work or school",          "the standard route"),
            "d25_tg":     ("Telegram chats and groups",  "niche communities"),
            "d25_fate":   ("Fate will sort it out",      "I'm not actively looking"),
        },
    },
    "phone_on_date": {
        "name_en": "Phone on a date — your mode",
        "blurb_en": "8 stances. What you actually do with your phone facing a new person",
        "items": {
            "pod_down":  ("Face down all evening",       "period"),
            "pod_pock":  ("In my pocket",                "out of sight, out of mind"),
            "pod_check": ("Check it if I'm waiting",     "I warn the other person"),
            "pod_warn":  ("I say upfront I'm expecting", "right at the start"),
            "pod_cont":  ("We make content together",    "shooting from minute one"),
            "pod_pay":   ("First to grab it pays",       "table rule"),
            "pod_dep":   ("Depends on the person",       "how into them I am"),
            "pod_open":  ("Always in plain sight",       "that's just me"),
        },
    },
    "first_date_redflag": {
        "name_en": "Red flag on a first date",
        "blurb_en": "16 signals. What absolutely won't slip past your attention on the first meeting",
        "items": {
            "rfd_late":    ("Late without warning",            "no respect for time"),
            "rfd_phone":   ("Stares at the phone all evening", "you're basically not there"),
            "rfd_rude":    ("Rude to staff",                   "the real face shows"),
            "rfd_self":    ("Talks only about themselves",     "doesn't ask about you"),
            "rfd_ex":      ("Too much about exes",             "with details"),
            "rfd_space":   ("Invades personal space",          "from the first minutes"),
            "rfd_money":   ("Asks about salary",               "on the first date"),
            "rfd_serious": ("Too quick on serious topics",     "and 'us' talk"),
            "rfd_listen":  ("Doesn't listen — interrupts",     "constantly"),
            "rfd_flirt":   ("Demonstratively flirts",          "with other people"),
            "rfd_comp":    ("Compares you to someone",         "uncomfortable"),
            "rfd_compl":   ("Complains about everything",      "food, place, weather"),
            "rfd_lie":     ("Lies about little things",        "I already noticed"),
            "rfd_drink":   ("Drinks noticeably more than usual","on the first date"),
            "rfd_offend":  ("Gets offended at innocent things", "thin skin"),
            "rfd_humor":   ("Can't laugh at themselves",       "ego in armor"),
        },
    },
    "first_move": {
        "name_en": "Ideal first move of attraction",
        "blurb_en": "8 signals. How you want interest shown — or how you show it yourself",
        "items": {
            "fm_dm":     ("Send a DM first",                  "simple and direct"),
            "fm_friend": ("A hint via mutual friends",        "indirect"),
            "fm_like":   ("A like on social media",           "see for yourself"),
            "fm_invite": ("Invite somewhere together",        "neutral pretext"),
            "fm_say":    ("Say it out loud",                  "'I like you'"),
            "fm_eyes":   ("Hold eye contact longer than usual","no words needed"),
            "fm_flirt":  ("Flirt gradually",                  "and wait for the reaction"),
            "fm_let":    ("Let them feel it themselves",      "and make the move"),
        },
    },
    "relationship_persona": {
        "name_en": "What you're like in a relationship",
        "blurb_en": "How you build close ties",
        "items": {
            "relationship_persona-romantic":      ("Romantic",        "dates · flowers · letters"),
            "relationship_persona-rational":      ("Rational",        "agreements · schedules"),
            "relationship_persona-anxious":       ("Anxious",         "doubts · double-checks"),
            "relationship_persona-free":          ("Free",            "no control"),
            "relationship_persona-caring":        ("Caring",          "everything for the partner"),
            "relationship_persona-jealous":       ("Jealous",         "control through emotion"),
            "relationship_persona-calm":          ("Calm",            "an even background"),
            "relationship_persona-playful":       ("Playful",         "jokes · memes · ease"),
            "relationship_persona-deep":          ("Deep",            "only serious conversations"),
            "relationship_persona-controlling":   ("Controlling",     "knows everything · decides everything"),
            "relationship_persona-closed":        ("Closed off",      "hard to open up"),
            "relationship_persona-open":          ("Open",            "tells everything"),
            "relationship_persona-demonstrative": ("Demonstrative",   "PDA · joint posts"),
            "relationship_persona-private":       ("Private",         "nothing on socials"),
            "relationship_persona-partner":       ("Partner-style",   "everything 50/50"),
            "relationship_persona-supportive":    ("Supportive",      "there in hard moments"),
        },
    },
    "green_flag_others": {
        "name_en": "Your top green flag in people",
        "blurb_en": "The quality you fall for the fastest",
        "items": {
            "green_flag_others-honesty":      ("Honesty",                 "tells the truth to your face"),
            "green_flag_others-humor":        ("Humor",                   "sees the funny in the ordinary"),
            "green_flag_others-calm-stress":  ("Calm under stress",       "doesn't panic"),
            "green_flag_others-ambitions":    ("Ambition",                "knows what they want"),
            "green_flag_others-care":         ("Care for loved ones",     "people matter more than career"),
            "green_flag_others-taste":        ("Taste",                   "style · music · films"),
            "green_flag_others-intelligence": ("Intelligence",            "interesting to talk to"),
            "green_flag_others-reliability":  ("Reliability",             "keeps their word"),
            "green_flag_others-empathy":      ("Empathy",                 "feels other people"),
            "green_flag_others-self-irony":   ("Self-irony",              "laughs at themselves"),
            "green_flag_others-curiosity":    ("Curiosity",               "interested in the world"),
            "green_flag_others-financial":    ("Financial maturity",      "good with money"),
            "green_flag_others-boundaries":   ("Respect for boundaries",  "understands 'no'"),
            "green_flag_others-hobbies":      ("Hobbies and passions",    "loves something"),
            "green_flag_others-listening":    ("The ability to listen",   "doesn't interrupt"),
            "green_flag_others-money-health": ("Healthy attitude to money","no greed and no flexing"),
        },
    },
    "red_flag_others": {
        "name_en": "What pushes you away the fastest",
        "blurb_en": "What kills interest instantly",
        "items": {
            "red_flag_others-rude-waiters":     ("Rude to waiters",                "character shows here"),
            "red_flag_others-dushnost":         ("Tediousness (dushnost')",        "explaining everything to death"),
            "red_flag_others-ponty":            ("Show-off (ponty)",               "bragging · brands"),
            "red_flag_others-ignor":            ("Ignoring",                       "no reply for hours"),
            "red_flag_others-control":          ("Controlling",                    "constant monitoring"),
            "red_flag_others-nyte":             ("Whining",                        "endless complaints"),
            "red_flag_others-chaos":            ("Chaos",                          "zero plans · everything falls apart"),
            "red_flag_others-no-boundary":      ("No respect for boundaries",      "intrudes uninvited"),
            "red_flag_others-late":             ("Constantly late",                "respect is shown through time"),
            "red_flag_others-ex-gossip":        ("Gossip about exes",              "they'll say the same about you"),
            "red_flag_others-no-hobbies":       ("No hobbies · emptiness",         "only work · only content"),
            "red_flag_others-greedy":           ("Greedy",                         "counts every penny"),
            "red_flag_others-jealous-noreason": ("Jealous for no reason",          "drama out of nothing"),
            "red_flag_others-petty-lies":       ("Lies even about small things",   "trust broken"),
            "red_flag_others-disrespect-taste": ("Contempt for taste",             "mocks what you love"),
            "red_flag_others-no-self-irony":    ("No self-irony",                  "everything is dead serious"),
        },
    },
    "attraction_type": {
        "name_en": "Your attraction type",
        "blurb_en": "Who hooks you faster?",
        "items": {
            "calm":        ("Calm ones",        "no fuss · self-assured · quiet strength"),
            "bold":        ("Bold ones",        "speak directly · take risks · a challenge"),
            "smart":       ("Smart ones",       "conversation pulls you in · see the essence · erudition"),
            "caring":      ("Caring ones",      "notice details · ask how you are · warmth"),
            "funny":       ("Funny ones",       "lighten the mood · don't take everything seriously"),
            "mysterious":  ("Mysterious ones",  "don't open up at once · you want to know more"),
            "ambitious":   ("Ambitious ones",   "know what they want · move forward · goals"),
            "creative":    ("Creative ones",    "see the world differently · create · surprise"),
            "sincere":     ("Sincere ones",     "say what they think · no masks · real"),
            "independent": ("Independent ones", "live their own lives · don't need approval"),
            "attentive":   ("Attentive ones",   "remember small things · listen · are present"),
            "confident":   ("Confident ones",   "know their worth · no doubt · charisma"),
            "adventurous": ("Adventurous ones", "drag you somewhere unexpected · live brightly"),
            "deep":        ("Deep ones",        "talk till morning · think about what matters"),
            "playful":     ("Playful ones",     "flirting like a game · ease · charge you up"),
            "reliable":    ("Reliable ones",    "keep their word · there when it's hard · a rock"),
        },
    },
    "how_you_flirt": {
        "name_en": "How you flirt",
        "blurb_en": "Pick your flirting style",
        "items": {
            "memes":           ("With memes",                     "a meme sent means I was thinking of you"),
            "care":            ("With care",                      "did you eat · coffee · blanket · just because"),
            "directness":      ("Directly",                       "head-on · no hints · I like you"),
            "stories":         ("Through stories",                "post for one · waiting for a reaction · hinting"),
            "silence":         ("Silently",                       "just being near · the look says more than words"),
            "humor":           ("With humor",                     "jokes · teasing · making them laugh"),
            "compliments":     ("With compliments",               "noticing details · saying it aloud · sincere"),
            "questions":       ("With questions",                 "wanting to know everything · asking · listening"),
            "touch":           ("With casual touches",            "hand on shoulder · brushing hair · happened by chance"),
            "playlists":       ("With playlists",                 "sending tracks · these songs are about you · a hint"),
            "reactions":       ("With story reactions",           "fire · heart · ball in your court"),
            "teasing":         ("With teasing",                   "ribbing · arguing · poking — means I like you"),
            "invites":         ("With invitations",               "I know a place · come along · just the two of us"),
            "help":            ("With help",                      "fixed it · explained · drove you · just because"),
            "online-activity": ("With likes",                     "a like on a 2019 photo · letting you know"),
            "eye-contact":     ("With eye contact",               "looking longer than needed · smiling with the eyes"),
        },
    },
    "ideal_date_format": {
        "name_en": "Your ideal date format",
        "blurb_en": "Which date format is yours?",
        "items": {
            "coffee":       ("Coffee",                       "cozy · talking · nowhere to rush"),
            "walk":         ("A walk",                       "walking · talking · the city as background"),
            "cinema":       ("Cinema",                       "darkness · shoulder beside you · then you discuss"),
            "night-city":   ("The night city",               "lights · no one around · time stretched out"),
            "dinner":       ("Dinner at a restaurant",       "candles · the menu · looking into eyes"),
            "home-cooking": ("Cooking together at home",     "kitchen · laughing · tasting from the spoon"),
            "exhibition":   ("An exhibition or museum",      "walking slowly · learning each other's tastes · talking meanings"),
            "concert":      ("A concert",                    "loud · the crowd · one moment for the two of you"),
            "park-picnic":  ("A picnic in the park",         "blanket · food · sky overhead"),
            "road-trip":    ("A trip out of town",           "the car · music · wherever the road goes"),
            "bar":          ("A bar or craft place",         "drinks · the noise · it gets easier"),
            "sport":        ("Activity together",            "skating · bowling · tennis · laughing at yourselves"),
            "rooftop":      ("A rooftop or viewing point",   "high up · wind · the city below"),
            "bookshop":     ("Bookshop or vinyl store",      "wandering · showing what you love · learning the person"),
            "home-movie":   ("A movie at home",              "blanket · couch · pause to talk"),
            "spontaneous":  ("Spontaneously, wherever",      "no plan · random places · memorable"),
        },
    },
    "after_argument": {
        "name_en": "How you are after a fight",
        "blurb_en": "How you behave after a conflict",
        "items": {
            "silence":      ("Go silent",                       "withdraw · words run out · silence"),
            "write-first":  ("Write first",                     "can't take it · type · just 'hey'"),
            "joke":         ("Joke",                            "lighten the mood · laughter as peace"),
            "analyze":      ("Analyze",                         "replay in your head · find where it broke"),
            "apologize":    ("Apologize first",                 "doesn't matter who's right · peace matters"),
            "wait":         ("Wait for them to come",           "not first · let them come · holding out"),
            "distract":     ("Distract yourself",               "music · walk · busy your head"),
            "cry":          ("Cry",                             "let the emotion out · feels lighter · honest"),
            "talk-it-out":  ("Want to talk right away",         "don't postpone · better now · all the way"),
            "replay":       ("Replay the words",                "what I said · what I should have · over and over"),
            "act-normal":   ("Pretend everything's fine",       "smiling · not okay inside · holding it"),
            "productive":   ("Throw yourself into work",        "cleaning · working · turn anger into energy"),
            "tell-friend":  ("Tell a friend",                   "need to vent · outside view"),
            "gesture":      ("A gesture without words",         "coffee · headphones · food · instead of an apology"),
            "distance":     ("Take a pause",                    "need to cool down · not now · talk later"),
            "overthink":    ("Stew on it for a long time",      "can't let go · a day · two · still there"),
        },
    },
    "digital_red_flag": {
        "name_en": "Your digital red flag in chat",
        "blurb_en": "What's your top red flag in messaging?",
        "items": {
            "dry-replies":           ("Dry replies",                    "ok · yes · got it · then silence"),
            "long-voice":            ("5-minute voice messages",        "could have typed · but no · listen up"),
            "always-online":         ("Always online but no reply",     "online · reading · silent · a mystery"),
            "read-no-reply":         ("Read it and didn't reply",       "ticks are there · no reply · waiting"),
            "late-reply":            ("Replies a day later",            "saw it yesterday · types today · was busy"),
            "one-word":              ("Single-word answers",            "fine · ok · clear · end of conversation"),
            "disappears":            ("Disappears without warning",     "was there · then gone · then back as if nothing"),
            "no-punctuation":        ("No punctuation at all",          "well it's all clear yes or no I don't know"),
            "screenshots":           ("Screenshots conversations",      "saves them · shows others · leak"),
            "calls-without-warning": ("Calls without warning",          "no 'can I call?' · just a call"),
            "typing-forever":        ("Types forever and doesn't send", "three dots · five minutes · silence · what was that?"),
            "seen-zone":             ("Leaves you in the seen zone",    "online · sees it · no reaction · just deal with it"),
            "double-text":           ("Sends multiple messages in a row","one · then another · and another · doesn't wait"),
            "passive-aggressive":    ("Passive aggression in periods",  "ok. · fine. · clear. · all noted."),
            "ignores-questions":     ("Ignores questions",              "asked · answered everything except the main one"),
            "emoji-only":            ("Replies only with emoji",        "👍 · 😊 · 🙏 · conversation over"),
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
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.batch4.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
