"""Archetype EN backfill — batch 12: Cinema part 2 (memorable_characters + actors_without_oscar)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "memorable_characters": {
        "Хаос обаяния": ("The chaos of charm",
            "Ledger's Joker, Phoenix's Joker, Alex DeLarge, Pennywise. You love villains who are contagious. They destroy, but you can't look away — because in their chaos there's some truth about freedom.\n\n"
            "This works because you have a dark curiosity. You understand each of us has the desire to break the system, and these characters live that desire to its extreme.\n\n"
            "People sometimes worry: \"are you romanticizing evil?\". Not romanticizing — studying. Different categories.\n\n"
            "What's worth knowing: chaotic villains are psychologically dangerous for the viewer who doesn't tell themselves apart from them. Keep distance. Watching them — fine. Identifying with them — already a question. Bring back to yourself: you're a viewer, not a participant."),
        "Холодные психопаты": ("Cold psychopaths",
            "Anton Chigurh, Hannibal Lecter, Patrick Bateman, Norman Bates. You love villains who do their work without emotion. Not from rage; from calculation or indifference.\n\n"
            "This works because they're scarier than all the rest. The emotional villain is understandable; the cold one is something beyond ordinary evil.\n\n"
            "People sometimes can't take it: \"they have no soul\". Exactly. And in that emptiness — real horror.\n\n"
            "What's worth knowing: fascination with cold antagonists sometimes reflects your own desire to be \"unreachable\". Understand the pull. Cold defense is attractive as image, but as a way of life — it's a prison. Use the films, don't import their style."),
        "Великолепные злодеи": ("Magnificent villains",
            "Hans Landa, Darth Vader, Voldemort, Nurse Ratched. You love villains who have style. Not just \"bad guys\" — strong characters whose lines and gestures stay in memory for years.\n\n"
            "This works because you respect craft. A great villain in a film isn't \"the screenwriter wrote him\" — it's \"the actor played him\", and you value the performance.\n\n"
            "People sometimes are surprised: \"you love Vader?\". Not Vader the person — Vader the role. Big difference.\n\n"
            "What's worth knowing: beautiful villains are often aesthetics. Sometimes the scariest are those without aesthetics, just everyday evil. Learn to see both — the magnificent ones in the cinema, and the dull ones who do real damage in life."),
        "Современная жестокость": ("Modern cruelty",
            "Amy Dunne, Patrick Bateman, Alex DeLarge, Norman Bates. The psychological monsters of the present are closer to you — those who live among us, indistinguishable from outside.\n\n"
            "This works because you understand: real horror isn't Darth Vader in a black cloak, it's the neighbor who does something terrible in an ordinary apartment. These characters are about that.\n\n"
            "People sometimes don't share it: \"but she looks normal\". Exactly. And that's scarier than any dragons.\n\n"
            "What's worth knowing: \"evil among us\" as a theme is both warning and paranoia. Learn to separate. Cinema doesn't mean a Bateman sits in everyone you know. Most people are just people. The films sharpen perception, not turn it into surveillance."),
        "Архетипы зла": ("Archetypes of evil",
            "Darth Vader, Thanos, Voldemort, Pennywise. You like villains of mythic scale. Not \"an ordinary bad person\" — but the embodiment of evil in pure form.\n\n"
            "This works because you value myth. Modern cinema often avoids archetypes; you love it when they're there.\n\n"
            "People sometimes call this \"childish\": \"Thanos is from Marvel\". And Marvel has mythology too, and it doesn't become less valuable because it has special effects.\n\n"
            "What's worth knowing: archetypes simplify, and that's both strength and weakness. Strength — they're accessible to everyone. Weakness — they lose psychological complexity. Learn to value psychologically deep antagonists too — they speak about reality, where archetypes speak about the universal."),
        "Историческое зло": ("Historical evil",
            "Hans Landa, Amon Göth, Darth Vader, Voldemort. You're interested in villains in whom real historical evil reads. They speak about totalitarianism, about war, about how ordinary people can become monsters.\n\n"
            "This works because you have an interest in history. Through cinematic villains you analyze real mechanisms of evil.\n\n"
            "People sometimes don't share it: \"it's just a movie\". A movie through which you understand 20th-century events better.\n\n"
            "What's worth knowing: historical evil on screen simplifies. Real evil is often less \"effective\" — it's everyday and systemic. Learn to see that aspect too. Otherwise you look for villainy with a face, while real damage often comes from faceless mass cooperation."),
        "Философия монстра": ("Philosophy of the monster",
            "Roy Batty, Hannibal Lecter, Anton Chigurh, Phoenix's Joker. You're closer to antagonists who have philosophy. They're not just \"bad\" — they explain why the world is built the way they see it.\n\n"
            "This works because you love when evil reflects. It lifts a film from the level of \"entertainment\" to \"thought\".\n\n"
            "People sometimes are surprised: \"do you agree with Lecter?\". I don't agree — I hear. Different things.\n\n"
            "What's worth knowing: philosophizing villains are dangerous because sometimes they tell the truth. And that doesn't make them less evil; just real. Learn to perceive complexly. Evil that thinks becomes a mirror — you see yourself in it. That's a useful experience as long as you stay outside the frame."),
        "_default": ("Your own set",
            "You don't have one type of favorite antagonists. You love chaos and the cold ones and the philosophers and the archetypes. Evil in all its forms interests you.\n\n"
            "This works because you have a deep interest in human nature. And in villains it's often more visible than in heroes.\n\n"
            "People sometimes don't get your focus. That's normal.\n\n"
            "What's worth knowing: wide range is wealth, but sometimes worth digging deeper into one. The full filmography of a director specializing in antagonists can give more than 20 films with different villains. Depth beats breadth — for understanding, not for collection."),
    },
    "actors_without_oscar": {
        "Культ молодёжи 90-х": ("Cult of '90s youth",
            "Johnny Depp, Keanu Reeves, Jim Carrey, Edward Norton. You love actors who grew up in the '90s and still work. They have a special style — ironic, charismatic, not fitting modern templates.\n\n"
            "This works because you caught them in their best years. These faces are part of the cultural memory of your generation.\n\n"
            "People sometimes say: \"he hasn't been in hits for a long time\". Not in hits — but in cinema. And every role is interesting.\n\n"
            "What's worth knowing: '90s nostalgia is good as long as it doesn't block the modern. Learn to watch new actors too. Otherwise you're a captive of the past, and the past keeps shrinking while the present passes you by."),
        "Британская старая школа": ("Old British school",
            "Alan Rickman, Ralph Fiennes, Peter O'Toole, Richard Burton. What grabs you is the great British theatrical tradition transplanted to cinema. Voice, diction, the precision of every gesture.\n\n"
            "This works because you value technique. These actors are masters of craft; not \"improvisers of inspiration\", but craftsmen of the highest class.\n\n"
            "People sometimes call this \"theatrical\". Theatrical in the positive sense. Not all theatrical is bad.\n\n"
            "What's worth knowing: the British school is fading now. Modern young Britons play differently, closer to the American style. Learn to value the old school while it's still accessible. Once it's gone, only recordings remain — and some of these masters never made enough recordings."),
        "Голливудские легенды": ("Hollywood legends",
            "Tom Cruise, Harrison Ford, Donald Sutherland, Josh Brolin. You love actors who hold the level for years. They're not \"trendy\", they're eternal. Every film — built on craft.\n\n"
            "This works because you respect the long game. These actors proved themselves for decades, and every role rests on reliability, not experiment.\n\n"
            "People sometimes call them \"boring\": \"he always plays the same thing\". Not the same — he plays himself in different contexts. And it works.\n\n"
            "What's worth knowing: legends are reliable, but sometimes worth stepping outside the frame. These actors give comfort; the young give surprise. Learn to value both. A diet of only legends — and modern cinema starts to feel foreign."),
        "Драматическая мощь": ("Dramatic power",
            "Jake Gyllenhaal, Michael Fassbender, Edward Norton, Bradley Cooper. You like actors who really work in every role. Not \"playing the star\" — transforming.\n\n"
            "This works because you value the giving. Most actors do what they're good at; these do what challenges them.\n\n"
            "People sometimes are surprised how they change so much each time. They train — for years.\n\n"
            "What's worth knowing: dramatic intensity is great, but sometimes becomes its own goal. Learn to tell \"he's working\" from \"he's showing he's working\". The first — real. The second — a game inside a game. Quiet transformation often beats demonstrative one."),
        "Эксцентричные мастера": ("Eccentric masters",
            "Johnny Depp, Jim Carrey, Steve Buscemi, Alan Rickman. What grabs you are actors with a strong own voice. Not \"all-rounders\" who can do everything; specialists in the strange, the unusual.\n\n"
            "This works because you love individuality. Actors who \"fit in\" bore you; you need those with a signature, recognizable from the first second.\n\n"
            "People sometimes are surprised: \"he's strangely played in every role\". Strangeness is his signature. And that's exactly why you love him.\n\n"
            "What's worth knowing: eccentric actors sometimes can't play \"normally\". That's both strength and limitation. Value the signature, but don't make a role for them where it doesn't fit — even great talent breaks against the wrong material."),
        "Преданные камео": ("Devoted character actors",
            "Steve Buscemi, Donald Sutherland, Peter O'Toole, Harrison Ford. You like supporting actors who in every film become the event. They're not \"stars\", but without them the film is poorer.\n\n"
            "This works because you have an eye for the ensemble. Most people watch only the main hero; you notice who in three minutes of screen time creates miracles.\n\n"
            "People sometimes don't remember them by name: \"who was that?\". That's a great actor who isn't a star, but a master.\n\n"
            "What's worth knowing: these actors are often more interesting in small roles than in big ones. Value the niche. And remember: a cameo is often harder work than the lead — you have to make a character work in three minutes, not three hours."),
        "Молодая школа без Оскара": ("Young school without an Oscar",
            "Bradley Cooper, Jake Gyllenhaal, Michael Fassbender, Josh Brolin. These actors are still working, and the Oscar is ahead of them. You value them precisely because they're on the way.\n\n"
            "This works because you love the living. Most classics are end-of-career; these are mid-career. And you grow with them as a viewer.\n\n"
            "People sometimes say: \"they didn't get an Oscar\". Yet. And they don't have to — that doesn't undo anything.\n\n"
            "What's worth knowing: \"no Oscar\" is sometimes a compliment. Many greats never got one (Peter O'Toole was nominated 8 times). Don't confuse absence of award with absence of talent. The Academy has its blind spots; you don't have to share them."),
        "_default": ("Your own choice",
            "You don't have one type of \"underrated\". You love eccentric, legendary, and dramatic. The only thing uniting them — the Academy didn't mark them.\n\n"
            "This works because you don't trust only awards. You evaluate actors yourself, not letting statuettes decide for you.\n\n"
            "People sometimes refer to Oscars: \"but he's not a winner\". And you smile. Not an argument.\n\n"
            "What's worth knowing: \"not a laureate\" isn't the same as \"underrated\". Learn to tell. Some great actors just don't fit academic criteria — that doesn't make them worse. Others really are underrated. Different things. The award scene is a flawed map; don't mistake it for the territory."),
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
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch12.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
