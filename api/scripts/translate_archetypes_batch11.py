"""Archetype EN backfill — batch 11: Cinema part 1 (Hollywood actors/actresses, night_films default).
Cats: hollywood_actors_50plus, hollywood_actresses_50plus, hollywood_actors_30_50,
hollywood_actresses_30_50, night_films (only default left). ~28 archetypes."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "hollywood_actors_50plus": {
        "Верный Новому Голливуду": ("Loyal to New Hollywood",
            "The era of cocaine and long monologues runs in your veins. You don't trust an actor without at least three Scorsese pictures."),
        "Английская сдержанность": ("English restraint",
            "You value the precisely-placed line and the intelligent gaze. Loud scenes aren't your genre."),
        "Маскулинная классика": ("Masculine classic",
            "The hero speaks little, shoots rarely — but when he shoots, he hits. That's your Hollywood."),
        "Голливуд большого бюджета": ("Big-budget Hollywood",
            "You trust those the studios put on the first poster. Stardom is quality to you, not a stigma."),
        "_default": ("Eclectic viewer",
            "You don't obey schools — you pick by instinct, and your top usually mixes eras and styles."),
    },
    "hollywood_actresses_50plus": {
        "Адепт серьёзной школы": ("Adept of the serious school",
            "You value actresses who turn each role into a dramatic manifesto. The benefit-night of emotion is your genre."),
        "Европейская элегантность": ("European elegance",
            "Aristocracy and subtle British-European humor. You trust the old school, where beauty doesn't shout."),
        "Икона блокбастеров 90-х": ("'90s blockbuster icon",
            "The nineties taught you that beauty and danger are the same thing. Femme fatale in every role."),
        "Земная сила": ("Earthy strength",
            "You value actresses without excess — character, intelligence, endurance. Spaceship or southern town — same thing."),
        "_default": ("Eclectic viewer",
            "You're not bound to a school or era — you pick by the moment, and your top always surprises."),
    },
    "hollywood_actors_30_50": {
        "Брутальные молчуны": ("Brutal silent ones",
            "You love actors who say less than they feel. Tom Hardy, Cillian Murphy, Adam Driver, Oscar Isaac — more happens on their faces than others manage in a monologue. And you read it all.\n\n"
            "This works because you have a deep way of watching cinema. You don't need explanations; you understand a character through the minimum.\n\n"
            "People sometimes don't catch up: \"he didn't say anything in the film\". And you got everything. That's a different level of perception.\n\n"
            "What's worth knowing: silent ones are intense, but sometimes oversaturate. If all your favorite actors are dark, concentrated, heavy, your cinematic landscape becomes one-note. Sometimes worth letting in someone lighter."),
        "Чувствительные интеллектуалы": ("Sensitive intellectuals",
            "Ryan Gosling, Andrew Garfield, Paul Mescal, Timothée Chalamet. What grabs you are actors with visible vulnerability, but without sloppiness. They know how to play men of a new type — subtle, feeling, not afraid to be weak.\n\n"
            "This works because you value emotional literacy. The old \"tough guy\" bores you; you need complexity.\n\n"
            "People sometimes call them \"too soft\". Not soft — real. Different things.\n\n"
            "What's worth knowing: sensitive actors are the era's answer to toxic masculinity. But they have their own stereotype too. Learn to see the actor, not the \"new ideal\". Otherwise you just swap one cliché for another."),
        "Драматическая интенсивность": ("Dramatic intensity",
            "Jake Gyllenhaal, Austin Butler, Taron Egerton, Miles Teller. You like actors who go full force in every role. Not \"steady\" — every time tearing themselves open.\n\n"
            "This works because you value the work. You need to see that the actor isn't just \"playing himself\" in new makeup, but really transforms.\n\n"
            "People sometimes don't share it: \"he's overplaying\". Not overplaying — going all in. Different categories.\n\n"
            "What's worth knowing: intense actors sometimes don't sustain long careers. Learn to value those who play evenly and precisely too — that's a different school, not worse. Burning bright burns out faster."),
        "Свежая волна": ("Fresh wave",
            "Chalamet, Mescal, Keoghan, Butler. What grabs you are actors who are defining the generation right now. Not \"legends\" — the ones forming a new language of cinema.\n\n"
            "This works because you follow the industry in real time. Most people discover new actors 5 years later; you — at the start of their careers.\n\n"
            "People sometimes can't keep up: \"who is that?\". And you smile: in two years everyone will know.\n\n"
            "What's worth knowing: young actors are a lottery. Of ten hot names today, two or three will remain in ten years. Accept it. Discovering someone early isn't a guarantee they'll become a legend. But it's still wonderful — to be there at the start."),
        "Звёзды с экрана": ("Screen stars",
            "Ryan Gosling, Michael B. Jordan, Zac Efron, Austin Butler. What grabs you is charisma that works for the stadium. These are actors with presence — they hold the camera with one expression.\n\n"
            "This works because you love cinema as spectacle. Not just as art, but as event. And these actors give exactly that.\n\n"
            "People sometimes call this \"pop\". Maybe. But \"pop\" with this charisma is its own art form.\n\n"
            "What's worth knowing: star charisma doesn't equal acting craft. Sometimes a charismatic actor plays mediocrely in a bad film, and you still like it — because you fell for the presence. Learn to tell the two apart, even if you love both."),
        "Глубокая школа": ("Deep school",
            "Gyllenhaal, Michael B. Jordan, Egerton, Dev Patel. What matters to you isn't only charisma but technique. These actors honed their craft for years — and it shows in every role.\n\n"
            "This works because you have a mature relationship with acting. You understand: playing well is years of work, not a natural gift.\n\n"
            "People sometimes don't tell them apart: \"they all play well\". No. Some live the role, others perform it. And you feel the difference.\n\n"
            "What's worth knowing: technique without charisma also doesn't work. The greatest are the combination. Look in both directions. Otherwise you love \"good craftsmen\" but miss the ones with the spark."),
        "Молодой авангард": ("Young avant-garde",
            "Barry Keoghan, Paul Mescal, Timothée Chalamet, Dev Patel. What grabs you are actors who are fundamentally new. They don't repeat old types — they form their own.\n\n"
            "This works because you understand: today's cinema needs different faces. And you recognize them earlier than others.\n\n"
            "People sometimes are surprised: \"you have weird preferences?\". Not weird — fresh. And in a couple of years it'll be mainstream.\n\n"
            "What's worth knowing: \"newness\" as a criterion is double-edged. Some of these actors will stay for the long haul; some won't. Learn to separate \"fresh\" from \"new and important\". Different things. Time will sort it; you don't have to."),
        "_default": ("Your own set",
            "You don't have one signature type. Your favorites come from different schools: sensitive and brutal, legends and fresh names. You're not bound to one type of on-screen masculinity.\n\n"
            "This works because you have wide taste. Most people pick \"theirs\" by one criterion; you understand you can act well in very different ways.\n\n"
            "People sometimes are surprised: \"you have both Hardy and Gosling in your favorites?\". Yes. And both are wonderful, just in different registers.\n\n"
            "What's worth knowing: wide taste is wealth. Sometimes worth deliberately digging into one actor — watching the whole filmography, understanding the trajectory. That gives a depth wide-ranging viewing can't reach."),
    },
    "hollywood_actresses_30_50": {
        "Эмма-сильные": ("Emma-strong",
            "Emma Stone, Jennifer Lawrence, Margot Robbie, Florence Pugh. You like actresses with charisma and pronounced character. Not \"cuties\", not \"ingénues\" — strong, recognizable, with their own face.\n\n"
            "This works because you value real individuality. In Hollywood many actresses look alike; these don't, and you recognize each from the first second.\n\n"
            "People sometimes don't tell them apart: \"they're all redheads/blondes\". No. They differ in character, and character is always stronger than hair color.\n\n"
            "What's worth knowing: bright actresses sometimes overplay. Learn to tell \"played strongly\" from \"played too much\". The greatest are those who can do both — pull back when needed and explode when needed."),
        "Гламурные иконы": ("Glamour icons",
            "Gal Gadot, Margot Robbie, Ana de Armas, Alicia Vikander. Aesthetic presence matters to you. Not only the acting, but beauty as part of the talent. You don't apologize for it; beauty is also art.\n\n"
            "This works because you don't separate \"deep\" and \"beautiful\". Many actresses prove the two combine wonderfully.\n\n"
            "People sometimes accuse: \"you love them for the looks\". And you don't deny it. You add — for the looks plus the acting. Looks don't subtract from talent; they complement it.\n\n"
            "What's worth knowing: focus on glamour sometimes blocks you from seeing less \"striking\" but deeper actresses. Look beyond the cover sometimes. The most interesting acting is often by those who don't lead with appearance."),
        "Артхаус и интенсив": ("Arthouse and intensity",
            "Natalie Portman, Saoirse Ronan, Anya Taylor-Joy, Brie Larson. What grabs you are actresses of the serious school. Their work demands attention; they don't \"entertain\", they engage.\n\n"
            "This works because you love cinema as experience, not as background. And these actresses do the kind of work that leaves you different when you walk out.\n\n"
            "People sometimes don't share it: \"it's boring with them\". Not boring — slow. And there's far more meaning in that slowness.\n\n"
            "What's worth knowing: arthouse intensity demands time from you. If you only love this school, your playlist becomes an emotional marathon. Alternate — otherwise all films start to feel the same heavy weight."),
        "Свежая волна": ("Fresh wave",
            "Zendaya, Florence Pugh, Saoirse Ronan, Anya Taylor-Joy. These actresses are defining today's cinema. They're the voice of their generation, and you follow it.\n\n"
            "This works because you understand: each generation needs its own actors. Those who grew up in the '90s can't speak about the 2020s the way those who grew up in the noughties can.\n\n"
            "People sometimes are surprised at how current you are: \"how do you know them?\". From new films. I just watch.\n\n"
            "What's worth knowing: fresh wave is a lottery. Not all these actresses will stay in big cinema for long. Accept it. Discovering someone early is wonderful, but no guarantee. And nothing wrong if some don't make it — you saw them at their start, that's already an experience."),
        "Британская школа": ("British school",
            "Keira Knightley, Daisy Ridley, Alicia Vikander, Saoirse Ronan. The British acting manner is closer to you — more restrained, more theatrical, with clear diction and measured gestures.\n\n"
            "This works because you value discipline. The Hollywood school is often about emotion through shouting; the British — about emotion through restraint. And you prefer the second.\n\n"
            "People sometimes call this \"cold\". Not cold — precise. Different categories.\n\n"
            "What's worth knowing: the British school is great taste, but sometimes limiting. If you're used only to their manner, emotional American acting feels fake. Learn to separate aesthetic preference from quality assessment. Both schools have their masters."),
        "Драматические артистки": ("Dramatic artists",
            "Natalie Portman, Brie Larson, Lupita Nyong'o, Rachel McAdams. What grabs you are actresses who choose hard roles. Not \"commercial face\" — serious work in every project.\n\n"
            "This works because you value choice. In Hollywood it's easy to be in action films and comedies; harder — to choose dramas where you really have to work.\n\n"
            "People sometimes don't get it: \"why does she take that heavy film?\". To grow. And what you value in an actress is exactly that.\n\n"
            "What's worth knowing: serious roles are work but also risk. Not every drama becomes a masterpiece; some are failures. Learn to see that the actress worked hard, even when the film didn't take off. The effort counts, even when the project doesn't."),
        "Молодые универсалы": ("Young all-rounders",
            "Florence Pugh, Anya Taylor-Joy, Ana de Armas, Saoirse Ronan. What grabs you is that these actresses can do everything. Drama, comedy, action, art. They're not bound to one genre.\n\n"
            "This works because you value acting versatility. In an era where many specialize, these ones do what others fear: they're convincing in any niche.\n\n"
            "People sometimes are surprised: \"is she in all your favorite films?\". Yes. Because she's good in very different ones.\n\n"
            "What's worth knowing: all-rounders sometimes don't leave the strongest single role. Their \"average\" is very high, but no \"peak\", because they're good everywhere. Specialists hit deeper one note; all-rounders cover the spectrum. Different paths, both valid."),
        "_default": ("Your own set",
            "You don't have one type of favorite actress. You love Emma Stone, Natalie Portman, Zendaya, Keira Knightley. Each in her own way, and you value the variety.\n\n"
            "This works because you have a wide view of actresses. Most people fixate on one type; you don't.\n\n"
            "People sometimes don't get it: \"they're all so different\". Yes. And that's the point.\n\n"
            "What's worth knowing: wide taste is wealth, but sometimes focus is lost. If \"all are good\" to you, you don't have \"yours, the most\". Learn to choose. Not for a ranking, but for your own clarity — which of them is really your most important."),
    },
    "night_films": {
        "_default": ("Your own night-film mix",
            "You don't have one signature type of night film. Sometimes a puzzle, sometimes surreal, sometimes pure shock. Depends on the mood.\n\n"
            "This works because you have wide taste. Most people fear night cinema overall; you don't, and depending on the evening you pick the form.\n\n"
            "People sometimes can't predict what you'll put on tonight. That's normal.\n\n"
            "What's worth knowing: variety is good as long as you yourself know what you're looking for. Sometimes worth asking yourself before the film: what do I need right now — puzzle, shock, meditation, psychology? Then the choice is more precise, and the film works stronger."),
    },
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats_by_id = {c.get("id"): c for c in raw}
    arch_done, arch_skip, arch_missing = 0, 0, 0
    for cat_id, tr in T.items():
        cat = cats_by_id.get(cat_id)
        if cat is None: print(f"  [skip] cat {cat_id}"); continue
        for a in cat.get("archetypes", []):
            ru = a.get("name"); pair = tr.get(ru)
            if not pair: arch_missing += 1; print(f"    [warn] {cat_id}/{ru!r}"); continue
            if a.get("body_en") and a.get("name_en"): arch_skip += 1; continue
            a["name_en"], a["body_en"] = pair; arch_done += 1
        da = cat.get("defaultArchetype")
        if da:
            pair = tr.get("_default")
            if pair:
                if not (da.get("body_en") and da.get("name_en")):
                    da["name_en"], da["body_en"] = pair; arch_done += 1
                else: arch_skip += 1
        print(f"  ✓ {cat_id}")
    print(f"\nArchetypes: done={arch_done}, skipped={arch_skip}, missing={arch_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch11.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
