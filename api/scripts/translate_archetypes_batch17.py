"""Archetype EN backfill — batch 17: Music part 1 (kpop_boys + music_camp + kpop_girls + your_2007).

Note: kpop_boys, music_camp, your_2007 have shorter Russian bodies (1-2 paragraphs)
than the standard 4-paragraph format. We mirror the Russian length where appropriate.
"""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "kpop_boys": {
        "Mainstream-стан": ("Mainstream stan",
            "You're comfortable that millions agree. The charts are your compass, and that's not bad."),
        "Четвёртое поколение навсегда": ("Fourth gen forever",
            "You listened to them when only the TWT thread and fan cafe knew about them. The word \"underrated\" pulses inside you."),
        "Олд-скул верность": ("Old-school loyalty",
            "The third generation raised your ear. You remember when \"concepts\" weren't yet an industry."),
        "SM/JYP-консерватор": ("SM/JYP conservative",
            "You trust only the old labels and believe vocal skills can't be overrated."),
        "_default": ("Eclectic fan",
            "You don't have a favorite company or era — you choose by track, not by brand."),
    },
    "music_camp": {
        "Меланхоличная утренняя": ("Melancholic morning",
            "You need music that hugs. Warm, slow, with space — like a cup of coffee in the rain."),
        "Уличная энергия": ("Street energy",
            "Rhythm, bass, audacity. You choose tracks under which you want to walk faster than necessary."),
        "Эстетика максимума": ("Aesthetic of the maximum",
            "You're not afraid to go loud. The brighter, more overloaded and emotional — the more honest."),
        "Танцпол ретро": ("Retro dancefloor",
            "You love when music asks the body to move. And when an 80s bassline sounds better than any new release."),
        "Эмоциональная глубина": ("Emotional depth",
            "You need lyrics that mean something, and voices that aren't perfect. Sincerity matters more than technique."),
        "_default": ("Eclectic listener",
            "You're not tied to a genre or scene — you choose by mood, and yours changes daily."),
    },
    "kpop_girls": {
        "Глобал-стадион": ("Global stadium",
            "What grabs you is K-pop that fills stadiums worldwide. You choose groups that crossed the niche and became mass culture. Not for refined concept, but for what they have — scale, production, undeniable hits.\n\n"
            "This works because you value a finished top-grade product. These groups invest huge resources in every video, every choreography, every comeback. And you get what you bargain for — without surprises, but with guaranteed quality.\n\n"
            "People sometimes are surprised: \"how can you love mainstream?\". And you don't \"love mainstream\" — you love specific groups that happened to be mainstream. That's a different thing.\n\n"
            "What's worth knowing: global groups give everything at once — and so they sometimes get boring quickly. The most interesting in K-pop is often beyond the top charts: concept albums, underground groups, less popular teams. It's worth periodically stepping out of the stadium zone and looking for something less obvious."),
        "Y2K-новая волна": ("Y2K new wave",
            "What grabs you are groups that set today's tone. NewJeans, IVE, STAYC, NMIXX — those who grew up on old K-pop but rewrote it for fresh sound and aesthetic. Y2K style, soft beats, a new type of girl-group delivery.\n\n"
            "This works because you have a nose for trends. You don't just listen to what plays now, you understand where the industry is moving. And so you invest in groups that shape tomorrow, not yesterday.\n\n"
            "People sometimes don't catch up: \"but BLACKPINK is cooler\". You don't care. BLACKPINK is for the past decade. These — for the next. In three years it'll be clear who was right.\n\n"
            "What's worth knowing: the new wave is vulnerable — a concept can age faster than for the proven. If you bet only on the fresh, in a couple of years your playlist may end up packaged with departing fashion. Learn to keep both stable and experimental in your collection. Then you don't depend on the swings of trends."),
        "Концепт-эксперимент": ("Concept experiment",
            "What matters to you is that the group does something non-standard. aespa with its virtual avatars, (G)I-DLE with self-authoring, f(x) with their strange beats, NMIXX with mix-pop approach. What grabs you isn't the song, but the idea behind the song.\n\n"
            "This works because you hear not only the sound but the concept. Most K-pop fans focus on the members and the hits. You add a third layer to that — who and why made this, what thought is inside the product.\n\n"
            "People sometimes tease you: \"you're like a critic\". You're not a critic — you're an attentive listener. And so you get more from the same industry than the average fan.\n\n"
            "What's worth knowing: conceptuality is strength but also the risk of becoming a snob. If you reject everything \"too ordinary\", you miss the joy of a simple good song. Learn to alternate: days of a deep concept album + days of a simple ear-catching hit. Snobbery closes off half of K-pop."),
        "Гёрл-краш": ("Girl crush",
            "What lights you up are groups with the energy of rebellion. 2NE1, MAMAMOO, (G)I-DLE, ITZY — those without a \"cute\" delivery, but with power, provocation, sometimes anger. It's feminine fierce style, and you recognize something of your own in it.\n\n"
            "This works because you yourself have fire inside, and you need idols of the same fuel. Cute pop groups bore you — they're for those who need calming. You need feeding.\n\n"
            "People sometimes don't share it: \"they're aggressive\". You smile. They confuse aggression with self-confidence. Girl crush isn't anger, it's precise knowledge of one's own strength.\n\n"
            "What's worth knowing: fierce aesthetics are wonderful, but shouldn't be the only thing. Sometimes your nervous system needs the soft and tender. Learn to alternate. Constantly fueling yourself with adrenaline through music is the path to burnout, even for the strongest. Strength requires periods of rest too — including in the playlist."),
        "Старая школа": ("Old school",
            "You remember where it all started. Girls' Generation, 2NE1, f(x), SISTAR — the generation that laid the foundation for everything we see now. They did alone what today's groups do on ready-made rails.\n\n"
            "This works because you have historical perspective. You understand NewJeans didn't appear from a vacuum; behind them stands a decade of genre development. And respect for the roots is your position.\n\n"
            "People sometimes don't understand: \"but they're from 2009, what's there to listen to?\". And you listen — because in those tracks there's sincerity and experiment that's rare in sterile modern K-pop.\n\n"
            "What's worth knowing: nostalgia is a powerful feeling, but sometimes prevents seeing the present. If you're only in the past, you miss what's shaping the future right now. Learn to keep one foot in the roots, the other in the new. Only then do you hear the full picture of the genre, not its half."),
        "Перфектный продакшн": ("Perfect production",
            "What grabs you is the level of execution. SM, HYBE, BIG3 — big labels invest millions in production, and it's audible in every note. Aespa, LE SSERAFIM, Red Velvet, Girls' Generation — groups whose even bad song sounds perfect.\n\n"
            "This works because you're raised on quality. It's hard for you to listen to \"raw\" — even if the idea is wonderful. You need the full package: vocals, production, video, choreography, all at maximum.\n\n"
            "People sometimes call this \"cold\": \"too even, no soul\". You disagree. These groups have soul — just packaged in perfect form. That doesn't make it less real.\n\n"
            "What's worth knowing: focus on production can close off groups with raw but powerful messaging. Sometimes an \"unfinished\" song grabs harder than a perfect one — because in its imperfection a person is audible. Learn to tell \"technically weak\" from \"technically rough but emotionally strong\"."),
        "Иконы 2010-х": ("Icons of the 2010s",
            "Your love is the golden generation. SISTAR, f(x), MAMAMOO, Girls' Generation in their peak years. It was the era when K-pop wasn't yet a global machine, and every group had a personality.\n\n"
            "This works because you hear the difference between then and now. Today's groups are polished by a single template. And in the 2010s every group was its own — one had Hwasa's voice, another Amber's experiment, a third the power of Soyou from SISTAR. They were people, not products.\n\n"
            "People sometimes tease you: \"you're like an old-timer K-pop fan\". You shrug. Better an old-timer in a quality era than fashionable in a superficial one.\n\n"
            "What's worth knowing: the golden era is golden precisely because it ended. If you live only in 2014, you have no connection to the current K-pop conversation. Learn to accept that times change. And sometimes — something new also becomes gold, just not noticed right away."),
        "_default": ("Your own K-pop mix",
            "You don't have one favorite group — you listen to different ones. Today the Y2K vibe of NewJeans, tomorrow the aggression of (G)I-DLE, the day after nostalgia for f(x). This isn't indecision — this is rich K-pop taste.\n\n"
            "Most fans fixate on one group and don't leave it for years. You're not like that. You understand K-pop is a huge industry with different schools, and limiting yourself to one — robbing yourself.\n\n"
            "People sometimes are surprised: \"you don't have any ults at all?\". You do, and not just one. You just don't reduce love to monogamy.\n\n"
            "What's worth knowing: a wide range is wonderful, but sometimes worth going deeper into one group. Just listening is the surface. Fully knowing the members' history, lore, concept, evolution — that's another level of pleasure. Try periodically: pick one group for a month and go fully into its world. Then you can scatter again. But the experience of depth — is worth it."),
    },
    "your_2007": {
        "Тёмный романтик": ("Dark romantic",
            "You lived at the junction of pain and beauty. Black eyeliner, a poetry diary, and music that understood you better than people."),
        "Панк-бунтарь": ("Punk rebel",
            "It mattered to you to be loud. Three chords, sneakers, not caring about rules — you were more alive than anyone alive."),
        # 'Дитя сцены' has empty body — skip
        "Тяжёлый фронт": ("Heavy front line",
            "You needed a charge — powerful, angry, with a guitar drop. You listened not with your ears but with your chest."),
        "Свой среди своих": ("One of your own",
            "While the whole class listened to Western, you found your own — Russian-language underground that sang straight to the soul."),
        "_default": ("Child of 2007",
            "You didn't just listen to music — you lived it. These bands weren't background, they were personality."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch17.{ts}")
    shutil.copy2(CATEGORIES_JSON, bak)
    print(f"backup: {bak}")

    touched = 0
    skipped = 0
    missing = []

    for cat in cats:
        cid = cat.get("id")
        if cid not in T:
            continue
        mapping = T[cid]
        archs = cat.get("archetypes") or []
        for a in archs:
            name = (a.get("name") or "").strip()
            if name in mapping:
                en_name, en_body = mapping[name]
                a["name_en"] = en_name
                a["body_en"] = en_body
                touched += 1
            else:
                if not a.get("body_en") and a.get("body"):
                    skipped += 1
                    missing.append(f"{cid}: {name}")

        d = cat.get("defaultArchetype") or {}
        if "_default" in mapping and d:
            en_name, en_body = mapping["_default"]
            d["name_en"] = en_name
            d["body_en"] = en_body
            touched += 1

    tmp = CATEGORIES_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON)

    print(f"touched: {touched}")
    print(f"skipped (no body_en, no mapping): {skipped}")
    if missing:
        print("missing:")
        for m in missing:
            print(f"  - {m}")

if __name__ == "__main__":
    main()
