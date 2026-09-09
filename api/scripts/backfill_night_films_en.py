"""
Backfill EN-локализации для существующих 32 items и 8 архетипов night_films,
которые были созданы до того, как ввели двуязычную схему.

Items: 16 оригинальных (fightclub, memento, ...) + 16 из первого батча
       (taxi, sevenfilm, ...) — итого 32.
Архетипы: 7 оригинальных + 1 «Город не спит» из первого батча — итого 8.

Идемпотентен: если поле _en уже выставлено, не трогаем (можно гонять повторно).
"""
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

# ─────────────────────────────────────────────────────────────────
# 32 EXISTING ITEMS — name_en + ctx_en
# ─────────────────────────────────────────────────────────────────
ITEM_EN = {
    # ─── Original 16 ───────────────────────────────────────────────
    "fightclub":  {"name_en": "Fight Club",                 "ctx_en": "1999 · Fincher · \"the first rule...\""},
    "memento":    {"name_en": "Memento",                    "ctx_en": "2000 · Nolan · memory in reverse"},
    "inception":  {"name_en": "Inception",                  "ctx_en": "2010 · Nolan · dreams within dreams"},
    "requiem":    {"name_en": "Requiem for a Dream",        "ctx_en": "2000 · Aronofsky · spiral into addiction"},
    "eternal":    {"name_en": "Eternal Sunshine of the Spotless Mind",
                                                            "ctx_en": "2004 · Gondry · erase the ex"},
    "mulholland": {"name_en": "Mulholland Drive",           "ctx_en": "2001 · Lynch · surreal noir"},
    "gonegirl":   {"name_en": "Gone Girl",                  "ctx_en": "2014 · Fincher · marriage and the media"},
    "blackswan":  {"name_en": "Black Swan",                 "ctx_en": "2010 · Aronofsky · ballet and psychosis"},
    "oldboy":     {"name_en": "Oldboy",                     "ctx_en": "2003 · Park Chan-wook · 15 years in a room"},
    "arrival":    {"name_en": "Arrival",                    "ctx_en": "2016 · Villeneuve · language and time"},
    "exmachina":  {"name_en": "Ex Machina",                 "ctx_en": "2014 · Garland · AI and the Turing test"},
    "annihil":    {"name_en": "Annihilation",               "ctx_en": "2018 · Garland · the mutating zone"},
    "mother":     {"name_en": "Mother!",                    "ctx_en": "2017 · Aronofsky · allegory"},
    "lighthouse": {"name_en": "The Lighthouse",             "ctx_en": "2019 · Eggers · b/w, madness, gulls"},
    "silverlake": {"name_en": "Under the Silver Lake",      "ctx_en": "2018 · Mitchell · LA paranoia"},
    "joker":      {"name_en": "Joker",                      "ctx_en": "2019 · Phillips · descent into the dark"},
    # ─── First batch (16 from earlier today) ────────────────────────
    "taxi":         {"name_en": "Taxi Driver",              "ctx_en": "1976 · Scorsese · a lonely New York"},
    "sevenfilm":    {"name_en": "Se7en",                    "ctx_en": "1995 · Fincher · seven sins"},
    "losthwy":      {"name_en": "Lost Highway",             "ctx_en": "1997 · Lynch · a double in a dream"},
    "shining":      {"name_en": "The Shining",              "ctx_en": "1980 · Kubrick · hotel and madness"},
    "prestige":     {"name_en": "The Prestige",             "ctx_en": "2006 · Nolan · trick and obsession"},
    "sixthsense":   {"name_en": "The Sixth Sense",          "ctx_en": "1999 · Shyamalan · a boy and ghosts"},
    "truman":       {"name_en": "The Truman Show",          "ctx_en": "1998 · Weir · world as a set"},
    "usualsuspects":{"name_en": "The Usual Suspects",       "ctx_en": "1995 · Singer · who is Keyser Söze"},
    "br2049":       {"name_en": "Blade Runner 2049",        "ctx_en": "2017 · Villeneuve · desert and memory"},
    "underskin":    {"name_en": "Under the Skin",           "ctx_en": "2013 · Glazer · a predator in Glasgow"},
    "solaris":      {"name_en": "Solaris",                  "ctx_en": "1972 · Tarkovsky · the mirror-ocean"},
    "lobster":      {"name_en": "The Lobster",              "ctx_en": "2015 · Lanthimos · the singles' hotel"},
    "antichrist":   {"name_en": "Antichrist",               "ctx_en": "2009 · von Trier · grief and chaos"},
    "melancholia":  {"name_en": "Melancholia",              "ctx_en": "2011 · von Trier · end of the world"},
    "lostintrans":  {"name_en": "Lost in Translation",      "ctx_en": "2003 · Coppola · sleepless Tokyo"},
    "drive":        {"name_en": "Drive",                    "ctx_en": "2011 · Refn · neon Los Angeles"},
}

# ─────────────────────────────────────────────────────────────────
# 8 EXISTING ARCHETYPES — name_en + body_en
# ─────────────────────────────────────────────────────────────────
ARCHETYPE_EN = {
    "Тёмная психология": {
        "name_en": "Dark psychology",
        "body_en": (
            "You're drawn to films that climb inside the broken parts of a mind. Not "
            "the violence itself but the structure underneath it: how someone arrives "
            "at the place they end up. Tyler Durden, the man with the polaroids in "
            "\"Memento\", the disintegrating ballerina, the late-stage Joker. You want "
            "to understand the wiring.\n\n"
            "This works because for you cinema is a tool for studying the human limit. "
            "Not from above (\"how could they\") but from inside (\"what would I do "
            "in that position\"). You don't romanticize the dark; you respect that it "
            "exists and want to know it well enough to recognize it in yourself early.\n\n"
            "Other people sometimes worry — \"why do you watch such heavy stuff\". For "
            "you it's not heaviness, it's information. The films don't depress you, "
            "they sharpen attention. After a strong dark-psychology film you actually "
            "feel calmer: the world is more legible, your own quiet parts less mysterious.\n\n"
            "What's worth knowing: there's a difference between a film that "
            "investigates darkness and one that just wallows. Look for craft: a clear "
            "view of the character, not just shock value. Skipping the second kind "
            "saves your evenings."
        ),
    },
    "Сюжет-головоломка": {
        "name_en": "Puzzle-plot",
        "body_en": (
            "What grabs you isn't \"who did it\" but \"how is the film structured\". "
            "\"Memento\" runs backward; \"Inception\" stacks layers; \"Gone Girl\" "
            "swaps a narrator on you halfway through. You watch as much for "
            "construction as for character — and you're often the one who notices "
            "the trick a beat before everyone else.\n\n"
            "This works because your brain treats a film as a system. You enjoy "
            "watching pieces lock into place; the satisfaction is geometric, almost "
            "mathematical. A good twist for you isn't a surprise — it's a confirmation "
            "that the design held all along.\n\n"
            "Other people sometimes complain that puzzle-films are \"too clever\" or "
            "\"emotionally cold\". You don't see it — for you the cleverness is the "
            "emotion. When a structure is honest and earned, it has a beauty no "
            "linear story can match.\n\n"
            "What's worth knowing: you can over-value the twist and undervalue the "
            "people. A great puzzle-film holds both — clean structure and a heart at "
            "the center. Practice noticing when a film is just a clockwork without a "
            "pulse: it's the cheap version of your favorite genre."
        ),
    },
    "Сюрреализм и сны": {
        "name_en": "Surreal and dreamlike",
        "body_en": (
            "You love films that don't pretend to be \"realistic\". Lynch sets the bar: "
            "you're inside a dream, the rules are local, and asking \"what does it mean\" "
            "is part of the wrong vocabulary. You also love the surreal moments inside "
            "more grounded films — the corridor in \"Mother!\", the night turn in "
            "\"Eternal Sunshine\", the LA paranoia in \"Silver Lake\".\n\n"
            "This works because for you cinema is closest to dream when it's most "
            "honest. Realism is a convention; the actual texture of consciousness is "
            "weirder, more associative, more emotional. Surreal films don't disorient "
            "you — they remind you of how reality already feels from the inside.\n\n"
            "Other people sometimes give up: \"I didn't get it\". You don't try to "
            "\"get\" Lynch the way you'd \"get\" a thriller. You sit with the film, "
            "let it work on you, and return to it later. Meaning shows up sideways — "
            "if it shows up at all — and that's the point.\n\n"
            "What's worth knowing: the surreal lives or dies on tone. A confident "
            "filmmaker who genuinely believes in the dream-logic carries you through; "
            "a pretender just looks like they're trying. Trust your instinct on which "
            "is which — and don't apologize when a film hits you and you can't say why."
        ),
    },
    "Холодный сай-фай": {
        "name_en": "Cold sci-fi",
        "body_en": (
            "You love science fiction that thinks before it explodes. \"Arrival\" "
            "asking how language shapes time; \"Ex Machina\" testing the Turing test "
            "from both sides; \"Annihilation\" letting biology turn dreamlike. The "
            "register is cool, considered, sometimes outright icy — and that's "
            "exactly your temperature.\n\n"
            "This works because for you the best science fiction is philosophy in "
            "costume. A film that takes one premise seriously and follows it cleanly "
            "is more useful than ten thrillers. You're patient with quiet pacing — "
            "you know the slow scenes are where the idea actually lives.\n\n"
            "Other people sometimes find your taste sterile: \"there's no warmth\". "
            "You disagree — there's exactly the right amount, dialed back so the idea "
            "can be heard. Warmth turned up too high in sci-fi often hides that the "
            "premise is thin. You prefer the discipline.\n\n"
            "What's worth knowing: cold doesn't mean indifferent. The best films of "
            "this genre are quietly devastating — Villeneuve's endings sit on your "
            "chest for days. Don't watch them tired; the slow build needs your "
            "attention from minute one to land in the final shot."
        ),
    },
    "Глубокая боль": {
        "name_en": "Deep ache",
        "body_en": (
            "You love films that don't soften the hard parts. \"Requiem\" doesn't pull "
            "back from the bottom; \"Oldboy\" earns its ending through full pain; "
            "\"Black Swan\" lets the breakdown be a breakdown. You don't want comfort — "
            "you want truth, and you accept the cost.\n\n"
            "This works because in your map of the world unprocessed pain is more "
            "dangerous than visible pain. A film that goes all the way through grief, "
            "addiction, obsession actually relieves something in you — it confirms that "
            "the experience can be looked at, named, survived. Catharsis is a real "
            "transaction, not a cliché.\n\n"
            "Other people sometimes call you a masochist: \"why subject yourself\". "
            "You don't see it that way. These films aren't punishment, they're "
            "permission to feel what you already half-feel. After a serious one you're "
            "lighter, not heavier — that's the test of whether the film did its job.\n\n"
            "What's worth knowing: this genre needs space around it. Don't watch "
            "back-to-back, don't rush to a conversation afterward. Give the film "
            "and yourself an evening of quiet. And don't confuse depth with "
            "wallowing — a film that just shows misery without arc is the cheap "
            "version of what you actually want."
        ),
    },
    "Артхаус с шоком": {
        "name_en": "Arthouse with shock",
        "body_en": (
            "You love films that shake the viewer on purpose. Aronofsky, Park Chan-wook, "
            "Eggers, late Lynch — directors who don't make polite cinema and don't "
            "pretend to. You want the kind of film where you sit silent for two minutes "
            "after the credits, trying to figure out what just happened to you.\n\n"
            "This works because for you cinema at its best is closer to ritual than to "
            "entertainment. A film that genuinely disturbs leaves a mark the way a "
            "neat story doesn't. You're willing to risk discomfort for the chance of a "
            "real impression.\n\n"
            "Other people sometimes can't follow you: \"that wasn't enjoyable\". For "
            "you that's the wrong measure. You don't watch these films to enjoy them; "
            "you watch to be affected. A film that leaves you intact — even a good one — "
            "doesn't pass your highest bar.\n\n"
            "What's worth knowing: shock without craft is just provocation. You're "
            "good at telling the difference, but watch the calibration: when the "
            "shocks get bigger but the films get hollower, your favorite directors "
            "are slipping. Don't stay loyal past the work."
        ),
    },
    "Тревога и крах": {
        "name_en": "Anxiety and collapse",
        "body_en": (
            "You're drawn to films where something is unraveling and the camera stays "
            "to watch. The husband becoming the bomber; the marriage rotting from "
            "inside; the addict losing the last thing; the comedian finally cracking. "
            "Not catastrophe at the start, but the long, accurate descent.\n\n"
            "This works because for you collapse is the most honest form of story. "
            "Most fictions hide that things end; you prefer films that don't. They "
            "don't make you anxious — they put you in the company of people who took "
            "anxiety seriously enough to stage it carefully. That's a kind of relief.\n\n"
            "Other people sometimes ask: \"why such depressive movies\". For you "
            "they're the opposite. After a film that names a fear precisely, the fear "
            "loosens. The cinema does work that ordinary conversation can't, because "
            "ordinary conversation skips the dark scenes too quickly.\n\n"
            "What's worth knowing: this genre wants pacing in your life around it. "
            "Don't binge — one a week is plenty. And don't romanticize the descent: "
            "the films are valuable because they show how it actually feels, not "
            "because that feeling is desirable."
        ),
    },
    "Город не спит": {
        "name_en": "The city doesn't sleep",
        "body_en": (
            "You love it when the city is the main character. Not as a backdrop but as "
            "a living part of the story: the neon reflection in the puddle, the hum of "
            "an air conditioner in the window, a sleepless taxi driver at an empty "
            "intersection. Atmosphere of time and place matters to you — not just the "
            "plot.\n\n"
            "This works because for you cinema is meditation. Not \"what will happen\" "
            "but \"how does this feel\". You often remember not the ending but the "
            "moment: a heroine's face in the glass, the flicker of a sign, a chance "
            "conversation in a hotel bar. You enter a film like a stranger's room — "
            "to sit a while.\n\n"
            "Other people sometimes don't get it: \"but nothing's happening\". For you "
            "the opposite is true — what matters is happening. You appreciate pauses, "
            "silence, slow takes. You're bored when a plot races forward without "
            "letting the viewer just be in the world.\n\n"
            "What's worth knowing: your cinema needs mood and time. Don't put it on "
            "in the background — it merges with noise. And don't judge films by "
            "\"dynamic\": sometimes the most important moment is the three minutes "
            "where the heroine just stands by the window."
        ),
    },
}


def main() -> int:
    if not CATEGORIES_JSON.exists():
        print(f"ERROR: {CATEGORIES_JSON} not found")
        return 1

    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        print(f"ERROR: expected list at root")
        return 1

    target = next((c for c in raw if c.get("id") == "night_films"), None)
    if target is None:
        print("ERROR: night_films not found")
        return 1

    print(f"Found: {target.get('name')}")

    # Backfill items
    items_updated = 0
    items_skipped = 0
    items_unknown = 0
    for it in target.get("items", []):
        en_data = ITEM_EN.get(it["id"])
        if en_data is None:
            print(f"  ITEM {it['id']}: no EN translation in this script")
            items_unknown += 1
            continue
        if it.get("name_en") and it.get("ctx_en"):
            items_skipped += 1
            continue
        it["name_en"] = en_data["name_en"]
        it["ctx_en"] = en_data["ctx_en"]
        items_updated += 1
    print(f"  items: updated={items_updated}, already_had_en={items_skipped}, "
          f"missing_translation={items_unknown}")

    # Backfill archetypes
    arch_updated = 0
    arch_skipped = 0
    arch_unknown = 0
    for a in target.get("archetypes", []):
        en_data = ARCHETYPE_EN.get(a.get("name"))
        if en_data is None:
            print(f"  ARCHETYPE '{a.get('name')}': no EN translation in this script")
            arch_unknown += 1
            continue
        if a.get("name_en") and a.get("body_en"):
            arch_skipped += 1
            continue
        a["name_en"] = en_data["name_en"]
        a["body_en"] = en_data["body_en"]
        arch_updated += 1
    print(f"  archetypes: updated={arch_updated}, already_had_en={arch_skipped}, "
          f"missing_translation={arch_unknown}")

    if items_unknown or arch_unknown:
        print("  WARN: some items/archetypes had no EN translation in this script")

    # Atomic write with backup
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.nf_backfill_en.{stamp}")
    shutil.copy2(CATEGORIES_JSON, backup)
    print(f"  backup: {backup}")

    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON)
    print(f"  wrote: {CATEGORIES_JSON}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
