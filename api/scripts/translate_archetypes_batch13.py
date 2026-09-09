"""Archetype EN backfill — batch 13: Cinema part 3 (female_power_films + my_film_genre + movie_character_like_you)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "female_power_films": {
        "Карьера без извинений": ("Career without apology",
            "The Devil Wears Prada, Working Girl, Nine to Five, Morning Glory. You're inspired by heroines who work and don't apologize. No tears about \"how hard it is to balance\"; they just build careers and live.\n\n"
            "This works because you have your own attitude toward work. Films where \"a woman suffers from the choice between family and career\" bore you; you need something about action.\n\n"
            "People sometimes call it \"not feminist\": \"well where's the feminism?\". And feminism is exactly \"doing without needing to defend your right to do\".\n\n"
            "What's worth knowing: career films sometimes miss complexity. Real life often holds more compromise than screen ones admit. Use them as inspiration, not as a checklist. The heroine on screen has a screenwriter on her side; you have only yourself."),
        "Реальные истории силы": ("Real stories of power",
            "Erin Brockovich, Hidden Figures, Norma Rae, Silkwood. You like films based on true events. Real women, real fight, real victory (or the price for it).\n\n"
            "This works because you have respect for the actual. Fictional stories are wonderful, but sometimes the addition \"based on true events\" changes the whole perception — you understand it happened.\n\n"
            "People sometimes are surprised: \"you hooked on truth?\". On truth. And that's not bad.\n\n"
            "What's worth knowing: \"based on true events\" is usually heavily dramatized. The real Erin Brockovich in life isn't as heroic as in the film. Learn to keep this in mind. Cinematic truth and biographical truth are different genres. Inspiration — yes. Literal copying of the heroine — careful."),
        "Подъём к равенству": ("Rise to equality",
            "The Help, Hidden Figures, Mona Lisa Smile, Norma Rae. What grabs you are stories about eras when women and minorities fought for their basic rights. And you know — without these women there wouldn't be the world we live in.\n\n"
            "This works because you have historical consciousness. You understand the current norm is a victory, and it isn't yet everywhere.\n\n"
            "People sometimes say: \"that was 50 years ago\". Yes. And the consequences live on. And the fight too.\n\n"
            "What's worth knowing: historical films inspire, but sometimes become a way to say \"everything's fine now, thanks\". The real fight continues. Learn to see modern struggle too. Otherwise you live in a museum of victories while the front line is still active."),
        "Бунт и побег": ("Rebellion and escape",
            "Thelma & Louise, Mad Max: Fury Road, Promising Young Woman, Wonder Woman. You like heroines who don't submit. They either break the system or run from it. And in both cases — they win.\n\n"
            "This works because you have a protest sense. You understand that sometimes \"correct behavior\" is part of the problem, and you have to break it.\n\n"
            "People sometimes worry: \"they're romanticizing violence\". Not violence — justice. Sometimes they coincide.\n\n"
            "What's worth knowing: rebellion films are catharsis, not a behavior model. Thelma and Louise don't survive in the finale; Max went through many circles of hell. Learn to take from them the energy, not the road map. The screen forgives mistakes; reality doesn't."),
        "Лёгкий феминизм": ("Light feminism",
            "Legally Blonde, The Devil Wears Prada, Working Girl, Nine to Five. You love when a strong heroine is shown with a smile. Not \"a heroic feat\"; just a smart girl who does the work and has fun doing it.\n\n"
            "This works because you understand: propaganda through seriousness works worse than propaganda through lightness. Many more people will see feminism through Elle Woods than through heavy drama.\n\n"
            "People sometimes devalue it: \"that's just pop\". Pop that changed more minds than the Manifesto.\n\n"
            "What's worth knowing: \"light\" feminism works in combination with serious. If you watch only the light, you risk thinking everything's already solved. The serious films remind you of the price of these victories. Both registers — together."),
        "Героиня в одиночку": ("Heroine alone",
            "Contact, Mad Max, Wonder Woman, Silkwood. What grabs you are stories where a woman is alone against the world. Not \"a team\" — but a solo path where you either win or perish.\n\n"
            "This works because you have an interest in solo heroism. Most films now are about teams; you love when the focus is on one figure.\n\n"
            "People sometimes are surprised: \"but a team is stronger\". In cinema — yes. In reality often not. Great women often went alone, and that's an interesting archetype.\n\n"
            "What's worth knowing: \"the loner\" as ideal is sometimes a refusal of help. In reality even the strongest women rely on networks — friends, mentors, allies. Learn to value solo cinema and collaborative life. The screen heroine carries everything herself; you don't have to."),
        "Тёмная справедливость": ("Dark justice",
            "Promising Young Woman, Thelma & Louise, Silkwood, Mad Max. You're closer to films where female power isn't bright. It's revenge, anger, fight to the last, sometimes with a tragic finale.\n\n"
            "This works because you have a mature attitude toward justice. Not \"everything will end well\"; sometimes you have to win at a high cost, and cinema is honest about it.\n\n"
            "People sometimes can't take it: \"why such a dark ending?\". Because sometimes life is like that. And lying in cinema isn't respect for the viewer.\n\n"
            "What's worth knowing: dark justice is wonderful, but sometimes becomes a fetish. If you love only the dark, you stop seeing victories that come without bloodshed. Learn to value bright stories too. Real change often happens quietly, not dramatically."),
        "_default": ("Your own set of power",
            "You don't have one type of \"film about female power\". You love the light and the dark and real stories and fantasy. The main thing is a strong woman at the center.\n\n"
            "This works because you have a wide view. Most people fixate on one genre; you understand female power is multi-faceted.\n\n"
            "People sometimes say: \"you have a strange list\". And in it — not one type. And that's strength.\n\n"
            "What's worth knowing: wide range is good, but sometimes worth studying one specific theme deeper. For example, all of Kathryn Bigelow's films or the whole corpus about real women scientists. That gives a different understanding of the phenomenon. Breadth — for taste, depth — for understanding."),
    },
    "my_film_genre": {
        "Серьёзная глубина": ("Serious depth",
            "Drama, history, war, documentary. You don't \"entertain\" yourself at the cinema; you get an experience. You need a film to leave a trace — not \"that was fun\", but \"now I'm thinking\".\n\n"
            "This works because you have a mature attitude toward art. Most people go to the cinema to distract themselves; you — to immerse.\n\n"
            "People sometimes don't share it: \"you're watching something heavy again?\". Again. And I need it.\n\n"
            "What's worth knowing: serious depth is wonderful, but it requires resource. If you're in a bad state, a heavy film can deepen it. Learn to alternate — not from lowering standards, but from caring for yourself. The film won't go anywhere; your inner state needs to be ready for the encounter."),
        "Адреналин": ("Adrenaline",
            "Action, thriller, crime, war. You need a film to drive you. You don't sit calmly; you're clutching the chair, you're breathing fast, and that charges you.\n\n"
            "This works because you have a need for stress as a game. Real stress — bad; cinematic — a controlled dose, and it releases you.\n\n"
            "People sometimes are surprised: \"you're tensing up\". Tensing up and enjoying it.\n\n"
            "What's worth knowing: adrenaline cinema is great, but not the only kind. If you only watch this, you get used to one type of nervous system. Learn to alternate with the slow. Otherwise quiet films start to feel \"empty\", and you lose access to half of cinema. Both modes — together."),
        "Ум и логика": ("Mind and logic",
            "Detective, mystery, sci-fi, thriller. You need a film to make you solve something. You don't just watch; you're working.\n\n"
            "This works because you have an analytical mind. Most films feel too \"direct\" for you; you need something to untangle.\n\n"
            "People sometimes get tired: \"why are you rewatching it again?\". I haven't understood it all yet.\n\n"
            "What's worth knowing: intellectual films are wonderful, but sometimes become an end in themselves. The strongest are the ones where the solution gives an emotion, not just satisfaction. Learn to value the films where you cried after the answer, not just nodded. Reason and feeling — best together."),
        "Фантастические миры": ("Fantastical worlds",
            "Fantasy, sci-fi, adventure, mystery. You love when a film carries you away. Not the modern world, but another — with different rules, different beings, different physics.\n\n"
            "This works because you have a strong imagination. The real world feels cramped to you; you need wider worlds.\n\n"
            "People sometimes don't get it: \"that's just escapism\". Yes. So what? Escapism is a normal human need.\n\n"
            "What's worth knowing: fantastical worlds are beautiful, but sometimes become a refuge. If you're only in them, you lose connection with the present. Learn to alternate. Otherwise your mind becomes a tourist, not a resident. Other worlds — to visit. This world — to live in."),
        "Лёгкость и улыбка": ("Lightness and a smile",
            "Comedy, romcom, adventure, fantasy. You need a film to lift your mood. Not \"to teach you life\", not \"to break your view of reality\" — just to please.\n\n"
            "This works because you have a mature attitude toward your own emotions. You understand sometimes you need exactly lightness, and you don't feel embarrassed choosing comedy.\n\n"
            "People sometimes get snobby: \"you're not watching anything serious\". Not always. But when I watch — pure joy.\n\n"
            "What's worth knowing: light genres also have different depths. Not all comedies are equal. Learn to tell the witty from the flat. The best comedies are serious literature in disguise. Keep choosing lightness, but raise the bar — light doesn't have to mean dumb."),
        "Тьма": ("Darkness",
            "Horror, mystery, thriller, crime. You're not afraid of the scary. You go there consciously — because there's a thrill in fear, and revelations in dark stories.\n\n"
            "This works because you have a strong nervous system. Most people avoid the unpleasant; you can endure it and even love it.\n\n"
            "People sometimes are surprised: \"how do you watch this?\". The same way you watch what bores me. Everyone has their own.\n\n"
            "What's worth knowing: dark cinema is a dialogue with your own fears. If you're in a bad state right now, it can amplify them. Learn to feel when the dark is catharsis, and when it's submersion. The first heals; the second deepens. Reading your own state is part of the genre."),
        "Эпос и история": ("Epic and history",
            "History, western, war, drama. You like when a film is an epic. Big events, big fates, big canvas of history.\n\n"
            "This works because you have a sense of scale. Chamber stories about \"I had problems at the office\" bore you; you need something on a large scale.\n\n"
            "People sometimes are surprised: \"you like the long ones?\". Long. Epic requires time.\n\n"
            "What's worth knowing: epic cinema is powerful, but requires patience. If you're in fast-dopamine mode, the epic won't land. Learn to set aside time. You watch the epic not \"in between things\", but as an event. Light a candle, turn off the phone, let the canvas open. That's the only way it works."),
        "_default": ("Your own genre mix",
            "You don't have one signature genre. Today drama, tomorrow comedy, the day after horror. You choose by mood, not by belonging to one school.\n\n"
            "This works because you have wide taste. Most people get stuck in one genre; you understand different moods require different forms.\n\n"
            "People sometimes can't predict what you'll put on today. That's normal.\n\n"
            "What's worth knowing: wide range is good, but sometimes depth is lost. If you watch a little of everything, you don't become an expert in anything. Learn to dig deeper into at least one genre — collect the classics, understand the evolution. Breadth — for everyday use, depth — for love. One genre that you know inside out makes you a different viewer in all the others."),
    },
    "movie_character_like_you": {
        "Доверчивая искренность": ("Trusting sincerity",
            "Forrest Gump, Amelie, Hermione, Jo March. You're grabbed by heroes who don't lose faith in people. They can be naive, but that naivety is their strength, not weakness.\n\n"
            "This works because you have the ability to see the best in people. In a world where the cynical view is considered intelligent, you choose sincerity — and that's a rare maturity.\n\n"
            "People sometimes are surprised: \"are you like Forrest?\". In some sense yes. And what's wrong with that?\n\n"
            "What's worth knowing: trust is your strength, but sometimes becomes vulnerability. Learn to tell faith in people in general from faith in a specific person right now. The first — wonderful. The second — requires verification. Forrest is loved by the screenwriter; in real life, not everyone deserves your innocence."),
        "Чувак-философ": ("The Dude philosopher",
            "The Dude (Big Lebowski), Walter Mitty, Andy Dufresne. You're a hero who doesn't rush. Life goes on, and you don't fuss. And in that unhurried pace there's much more wisdom than in others' race.\n\n"
            "This works because you have your own tempo. In an era where everyone hurries to \"succeed\", you chose to live.\n\n"
            "People sometimes call it \"laziness\". Not laziness — choice of tempo.\n\n"
            "What's worth knowing: \"not rushing\" is wonderful as long as it stays conscious. If you don't rush because you don't want to act at all — that's no longer philosophy, that's paralysis. The Dude in the film has a screenwriter who carries him through plot; you have only yourself. Slow with attention — yes. Slow with avoidance — careful."),
        "Гений-аутсайдер": ("Outsider genius",
            "Sherlock Holmes, Tony Stark, Hermione, Andy Dufresne. You recognize yourself in geniuses who are too smart for their ordinary environment. They're not \"showing off\" — they just see more, and because of this it's harder for them to live with ordinary people.\n\n"
            "This works because you have a sense of your own non-standardness. You're not \"ordinary\"; you understand that, and sometimes it's lonely.\n\n"
            "People sometimes don't share it: \"you're a genius?\". Not a genius — different. That's different.\n\n"
            "What's worth knowing: \"outsider genius\" is a tempting archetype, but sometimes becomes an excuse for not wanting to fit in. Learn to tell real unusualness from a pose. The first — yes, hard, deserves respect. The second — laziness in a beautiful wrapper. Genuine difference shows in work, not in complaints about ordinary people."),
        "Авантюрист": ("Adventurer",
            "Indiana Jones, Ethan Hunt, Lara Croft, Tony Stark. You love heroes who don't have boring days. They're forever in motion, in risk, in discoveries.\n\n"
            "This works because you yourself have a hunger for adventure inside. Sitting in one place is torture; you need to move, learn, risk.\n\n"
            "People sometimes get tired of your energy: \"just relax\". And I'm comfortable in motion.\n\n"
            "What's worth knowing: adventure is great motivation, but sometimes becomes flight from yourself. If you're constantly in motion, you can fail to understand who you are. Learn to stop sometimes. Indiana Jones in the film doesn't have an inner life between adventures; you do, and it deserves attention. Run — yes. Run from yourself — no."),
        "Бунтарь": ("Rebel",
            "Tyler Durden, Katniss, Scarlett O'Hara, Lara Croft. You're grabbed by heroes who don't submit to the system. They either break it or build their own.\n\n"
            "This works because you yourself have a streak of protest. You're not the kind who accepts \"as is\" without questions.\n\n"
            "People sometimes worry: \"you're not Tyler though\". Not Tyler. But there's something in him I understand.\n\n"
            "What's worth knowing: rebels in cinema usually lose. Learn to tell healthy resistance from self-destruction. Not every \"no\" to the world is strength; sometimes it's just anger in bad packaging. The screen rebel has a screenwriter polishing his lines; in life, the same gesture often comes off as a tantrum. Aim where it changes things, not where it just blows up."),
        "Стратег": ("Strategist",
            "Michael Corleone, Sherlock Holmes, Andy Dufresne, Ethan Hunt. You're like a hero who thinks three steps ahead. Not reactive — strategic.\n\n"
            "This works because you have a smart plan for everything. Most people live reactively; you — proactively.\n\n"
            "People sometimes are surprised: \"you calculated all of this?\". Calculated. And usually it works.\n\n"
            "What's worth knowing: strategy is wonderful as long as it stays flexible. If you hold the plan too rigidly, reality will outplay you. Learn to adapt. The best strategists are the ones who change the plan in real time. The screen strategist always wins because the screenwriter sides with him; in life, even the best plan meets weather, traffic, other people's moods. Plan — yes. Worship the plan — no."),
        "Сильная женщина": ("Strong woman",
            "Jo March, Katniss, Scarlett O'Hara, Amelie. You're grabbed by heroines with clear inner strength. Not \"victims\", not \"sweethearts\" — but women who walk on their own.\n\n"
            "This works because you value agency. Heroines who \"happen to things\" bore you; you need ones who act.\n\n"
            "People sometimes call this \"too feminist\". Not feminist — normal. A woman's strength is normal strength, not a special category.\n\n"
            "What's worth knowing: every \"strong woman\" in cinema is a simplification. Real strong women are often weaker than they appear, and that's also normal. Learn to value more complex images too — the ones where strength coexists with doubt, fatigue, grief. Strength without cracks is a poster; strength through cracks is a person."),
        "_default": ("Your own hero mix",
            "You recognize yourself in different heroes. Sometimes in Sherlock, sometimes in The Dude, sometimes in Katniss. That's not indecisiveness — that's the richness of your inner palette.\n\n"
            "This works because you have many facets. Most people identify with one hero; you — with different ones depending on the situation.\n\n"
            "People sometimes don't get it: \"you can't be both Hermione and Tyler\". I can. In different contexts.\n\n"
            "What's worth knowing: multiplicity is your wealth, but sometimes worth choosing one \"main\". Not all sides are equal; there's the one that shows up more often. Knowing it is understanding yourself. The full range stays — you don't lose Sherlock by admitting The Dude is closer most days. The default isn't a cage; it's a center of gravity."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch13.{ts}")
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
        seen_names = set()
        for a in archs:
            name = (a.get("name") or "").strip()
            seen_names.add(name)
            if name in mapping:
                en_name, en_body = mapping[name]
                a["name_en"] = en_name
                a["body_en"] = en_body
                touched += 1
            else:
                if not a.get("body_en"):
                    skipped += 1
                    missing.append(f"{cid}: {name}")

        # default archetype (key is camelCase in this dataset)
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
