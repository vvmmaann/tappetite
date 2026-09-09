"""Archetype EN backfill — batch 22: Estetika part 3 (your_background + your_stories_style + life_cover_vibe). Last Estetika batch."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "your_background": {
        "Город ночью": ("City at night",
            "Night city, rooftop, club, empty street at dawn. The urban night calms you. Lights, rain, anonymity in the crowd.\n\n"
            "This works because you have an urban soul. Nature bores you; you need the movement of concrete and neon.\n\n"
            "People sometimes don't understand: \"how do you rest in the city?\". I rest. The city at night is a different city — quieter and more beautiful.\n\n"
            "What's worth knowing: the night city is also a risk. Fatigue, bad company, dangerous areas. Learn to feel. Not every nighttime place is equally safe. And take care of sleep — constant night life depletes."),
        "Природа": ("Nature",
            "Sea, forest, mountains, beach at night. Nature restores you. Not \"a city park\"; but real nature — where there's no one, where the only sound is the wind.\n\n"
            "This works because you have a deep connection with the natural. The city depletes you; nature returns.\n\n"
            "People sometimes are surprised: \"one week in the mountains a year — that's not enough\". Not enough. There should be more nature, but I do what I can.\n\n"
            "What's worth knowing: nature is also an investment in quality of life. Learn to plan trips in advance so you don't miss them. Without it you burn out. This isn't \"a pleasant bonus\", it's a basic need."),
        "Тихий уголок": ("Quiet corner",
            "Library, cozy cafe, home at night, gallery. You need silence with a background. Not full silence; but where there's a quiet hum, and you can think.\n\n"
            "This works because you have an intellectual nature. Pure silence is hard for you; you need a little background.\n\n"
            "People sometimes are surprised: \"are you in the library all day?\". All day. And there I write best.\n\n"
            "What's worth knowing: \"quiet corners\" are also a niche pleasure. Not every cafe fits, not every library. Learn to find \"your\" places and protect them. Good quiet places are a rarity."),
        "Транзит и движение": ("Transit and motion",
            "Train in motion, airport, empty street, old quarter of a foreign city. What grabs you is the sense of transition. Not \"home\"; but the space between two points.\n\n"
            "This works because you have a love for the temporary. Home is cramped for you; you need motion.\n\n"
            "People sometimes don't understand: \"you love being in airports?\". I love it. Everyone there is going somewhere, and that's freeing.\n\n"
            "What's worth knowing: \"life in transit\" sometimes becomes flight. If you're constantly on the road, you don't have time to settle into any place. Learn to balance. Sometimes worth stopping so you can move again later."),
        "Творчество": ("Creativity",
            "Creative studio, gallery, library, cozy cafe. You need a place of creativity. Not \"work at the desk\"; but a space where ideas are born.\n\n"
            "This works because you have a creative practice. The environment affects what you produce, and you understood this.\n\n"
            "People sometimes are surprised: \"why do you need a studio, work at home\". At home it doesn't work. The environment is part of the process.\n\n"
            "What's worth knowing: creative spaces require investment — money, travel time, organization. Learn to make it pay off. If you have a studio but use it once a week, reconsider the strategy. Maybe a coworking would be enough."),
        "Ночь и одиночество": ("Night and solitude",
            "Night city, beach at night, empty street, home at night. You need night silence. When the world sleeps, your own life begins.\n\n"
            "This works because you have a night nature. Daytime fuss tires you; night is your time.\n\n"
            "People sometimes worry: \"you're not sleeping\". I sleep. Just at different hours.\n\n"
            "What's worth knowing: night life conflicts with society that works during the day. Learn to accept this. And take care of health — night mode without proper sleep hygiene destroys."),
        "Чужой город": ("Foreign city",
            "Old quarter of a foreign city, train, airport, empty street. You need to be \"not at home\". Where no one knows you; where you're an anonymous observer.\n\n"
            "This works because you have a love for freedom from a role. At home you're \"such-and-such\"; in a foreign city — no one, and from this you can be anyone.\n\n"
            "People sometimes don't understand: \"why do you need an unfamiliar city?\". To be free. At home I'm in a role.\n\n"
            "What's worth knowing: this need is real. Learn to plan trips alone at least once a year. Without them you gradually lose connection with yourself. And it's not \"selfish\"; it's self-preservation."),
        "_default": ("Your own set of backgrounds",
            "You don't have one signature background. Sometimes you need nature, sometimes city, sometimes transit, sometimes a quiet corner. Depends on mood and life phase.\n\n"
            "This works because you have flexibility. Most people cling to one \"their place\"; you understand different states require different environments.\n\n"
            "People sometimes can't predict where you need to be now.\n\n"
            "What's worth knowing: flexibility is good, but sometimes worth having a \"base\". One place you return to regularly is an anchor. Without it you're constantly searching."),
    },
    "your_stories_style": {
        "Минималист": ("Minimalist",
            "Minimal, don't post, only to archive, only text. You're \"quiet\" in stories. Don't publish, observe, or post rarely and precisely.\n\n"
            "This works because you have a relation to privacy. Not every moment should be public.\n\n"
            "People sometimes are surprised: \"you're not in stories?\". No. And that doesn't mean I'm not in life.\n\n"
            "What's worth knowing: silence in stories in an era when everyone posts is sometimes read as \"you don't exist\". Learn to accept this. Those who really want to know about you will find ways. The algorithm isn't an indicator of closeness."),
        "Хаотик": ("Chaotic",
            "Chaos, food, memes and reposts, selfies. You post everything in a row. Not \"thought-out content\"; but stream of consciousness in the form of stories.\n\n"
            "This works because you have a lively rhythm. Life happens, and you document it.\n\n"
            "People sometimes get tired: \"50 stories again\". Again. Don't like — mute.\n\n"
            "What's worth knowing: \"everything in a row\" sometimes loses the audience. If you have 50 stories a day and nothing interesting, people start muting. Learn to feel the rhythm — even in chaos there should be energy."),
        "Эстет": ("Aesthete",
            "Film aesthetics, sunsets, nature and details, minimal. You make stories like little films. Color, light, composition — every frame is thought through.\n\n"
            "This works because you have visual taste. \"Selfie in the mirror\" bores you; you need aesthetics.\n\n"
            "People sometimes admire: \"do you have design education?\". No. Just an eye.\n\n"
            "What's worth knowing: aesthetic stories require time. If you spend an hour on one story, that's already work, not communication. Learn to balance. Sometimes a live frame without editing is stronger than a perfect one."),
        "Социальный": ("Social",
            "Events and parties, polls and questions, selfies, memes and reposts. You use stories as a tool for communication. Active polls, reactions, audience engagement.\n\n"
            "This works because you have a social nature. Stories for you aren't \"post and forget\"; it's a conversation.\n\n"
            "People love this in you. Your polls are an event, and many participate.\n\n"
            "What's worth knowing: social stories require constant support. If you've posted a poll and don't react to answers, the audience disperses. Learn to respond. Conversation is a two-way process."),
        "Документатор жизни": ("Life documenter",
            "Travel, work process, food, events. You document what's happening. Not \"staging\"; but real moments that are pleasant to revisit later.\n\n"
            "This works because you have a relation to memory. Stories for you are also an archive, not only publication.\n\n"
            "People sometimes are surprised: \"you film everything?\". Everything. In 10 years I'll watch and remember.\n\n"
            "What's worth knowing: \"document everything\" sometimes prevents \"living everything\". If you're constantly through a lens, you're not in the moment. Learn to turn off the camera sometimes. The strongest memories are those you didn't manage to film."),
        "Творческий": ("Creative",
            "Film aesthetics, work process, track of the day, only text. You post your creative life. Not \"a report\"; but pieces of the process in which others can be inspired.\n\n"
            "This works because you have creative practice. And you understand — showing the process matters more than only the result.\n\n"
            "People sometimes say: \"you post the unfinished\". Unfinished. And that's interesting — to see how something is being born.\n\n"
            "What's worth knowing: creative stories attract creative people. Learn to use this for networking. Your audience is potential collaborators, not just viewers."),
        "Природный": ("Natural",
            "Nature and details, sunsets, travel, film aesthetics. What grabs you is the natural. Sunset, puddles, leaves, light in the window — what most miss.\n\n"
            "This works because you have observation. \"The big picture\" isn't enough for you; you need details.\n\n"
            "People sometimes don't understand: \"why a story with a puddle?\". Because the sky reflects in this puddle beautifully.\n\n"
            "What's worth knowing: natural stories require time and a good eye. If you only post \"I'm here\" without attention to detail, that's not a natural style. Learn to look at your photos as a viewer — is there something there that will catch another?"),
        "_default": ("Your own stories style",
            "You don't have one signature style. Today aesthetics, tomorrow chaos, the day after memes. You post what you feel right now.\n\n"
            "This works because you have a lively nature. Most people fit stories under an \"image\"; you don't.\n\n"
            "People sometimes can't predict you. And that's part of your charm.\n\n"
            "What's worth knowing: \"everything in a row\" sometimes loses consistency. If today you're aesthete, tomorrow chaotic — the audience can't form an expectation. Learn to alternate consciously. Not for the algorithm, for yourself — to be honest, not reactive."),
    },
    "life_cover_vibe": {
        "Музыкальная коллекция": ("Music collection",
            "Vinyl, CD box, digipak, concert poster. Your world is music as an object. Not just streams — but objects you can take in your hands, look over the cover, read the booklet.\n\n"
            "This works because you have a tactile connection with art. Digital is too ephemeral for you; you need something physical that won't disappear when the service shuts down.\n\n"
            "People sometimes don't understand: \"why vinyl, you have Spotify?\". Because vinyl is a different relationship. It's presence in the moment, not background.\n\n"
            "What's worth knowing: collecting is a hobby and a risk. If you have 200 records and don't have time to listen to them, that's no longer a collection — it's a warehouse. Learn to listen to everything you buy. Otherwise love for music turns into love for buying music, and these are different feelings."),
        "Кино-эстетика": ("Cinema aesthetic",
            "Film poster, magazine cover, DVD cover, steelbook. You need big visual delivery, like a real blockbuster or a fashion magazine. Life should be cinematic.\n\n"
            "This works because you have cinematic perception. Most people see their life as a stream of routine; you — as a plot with acts, climaxes, frames.\n\n"
            "People sometimes call you \"dramatic\". Not dramatic — attentive. I just notice in the ordinary frames that deserve to be.\n\n"
            "What's worth knowing: cinematic gaze is wonderful, but sometimes becomes a distance. If you constantly \"film your life\", you don't live it — you film it. Learn to turn off the camera sometimes and just be. The strongest cinema is the one you didn't manage to film."),
        "Книжная любовь": ("Book love",
            "Classical book in hardcover, soft cover, art book. You need the page, the font, the texture of the binding. An e-book for you is a solution to a problem, not the book itself.\n\n"
            "This works because you read not only the text — you read the form. For you the cover, paper, size are part of the work, and without them something is lost.\n\n"
            "People sometimes don't understand: \"is everything in paper for you?\". Not everything, but the most important. If a book matters to me — it's in paper.\n\n"
            "What's worth knowing: paper books are more expensive and heavier. If you have limited space or budget, sometimes worth making choices. Learn to understand which books should be in paper for you and which are okay digital. Not every book deserves a shelf, and that's normal."),
        "Геймерская и графичная": ("Gaming and graphic",
            "Comic, game box, art book. Your worldview is at the junction of cinema, literature, and interactivity. A graphic novel with a superhero, an art book of concept art, a PC game box with a floppy and a manual.\n\n"
            "This works because you grew up on these forms. They're native to you, not niche. And the world for you is structured through their aesthetics.\n\n"
            "People sometimes are surprised: \"you're still a comics fan?\". Still. And what's wrong with that?\n\n"
            "What's worth knowing: this aesthetic is great, but sometimes limits. If you only live in graphic narratives, you miss literature without illustrations, cinema without heroes in cloaks. Learn to step outside your zone. Not to refuse the favorite, but to expand taste."),
        "Тёплая ностальгия": ("Warm nostalgia",
            "Postcard, wall calendar, vinyl, CD. Your world is soaked in warm memory. A grandmother's postcard from Crimea, a Soviet calendar with a cat, a film record from parents.\n\n"
            "This works because you understand: the value of things is often not in their price, but in their history. And you collect objects with a past — even if a short one.\n\n"
            "People sometimes don't share it: \"why do you need an old calendar?\". Because it's alive. It has a life, unlike modern things.\n\n"
            "What's worth knowing: nostalgia is a powerful feeling, but sometimes becomes a form of escapism. If your room only has the past, you have no place for the present. Learn to balance: a couple of warm things from the past + life today. Then nostalgia is your core, not a cage."),
        "Коллекционная редкость": ("Collector's rarity",
            "Steelbook, digipak, vinyl, concert poster. It matters to you not just to have — but to have rare, limited, special editions. You don't just buy; you hunt.\n\n"
            "This works because you have a thrill. Getting what not everyone has isn't \"bragging\", it's sporting satisfaction. And in this you find your high.\n\n"
            "People sometimes don't understand: \"why a steelbook if there's an ordinary disc?\". Because a steelbook isn't a \"medium\", it's an object. And there's the difference.\n\n"
            "What's worth knowing: collecting is a great hobby but dangerous for the budget. If you spend on limited editions more than you can afford — that's no longer love, it's compulsion. Learn to separate. And remember — a rare object is valuable not in itself, but in what you do with it."),
        "Мягкая повседневность": ("Soft everyday",
            "Soft cover of a book, postcard, wall calendar, puzzle box. You're not a hunter for rarities, not a collector of the expensive. You're good with objects that are everyday and accessible, but have soul.\n\n"
            "This works because you have the ability to value the simple. Most people need \"the special\" to be content; for you a warm format of a book in your pocket is enough.\n\n"
            "People sometimes don't share it: \"are all your shelves paperbacks?\". Yes. And they're dear to me.\n\n"
            "What's worth knowing: love for the simple is wonderful, but sometimes becomes a refusal of quality. If you choose only the cheap because \"why pay for an edition\", you miss the beautiful, more quality alternatives. Learn to make exceptions sometimes. A good edition of a favorite book isn't \"bragging\", it's preservation."),
        "_default": ("Mix of covers",
            "Your world is assembled from different formats. Vinyl, comic, old postcard, and steelbook of a favorite film. You're not tied to one form — each has its place.\n\n"
            "This works because you have wide taste. Most people collect one thing; you understood different formats give different experience, and collect along different lines.\n\n"
            "People sometimes can't predict your next purchase. That's normal — you don't know yourself until the last what will catch.\n\n"
            "What's worth knowing: eclecticism is good as long as there's focus. If you buy everything in a row, in 5 years you'll have 200 different objects and not one collection. Learn to at least periodically find a common thread. This gives your hobby form, not blur."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch22.{ts}")
    shutil.copy2(CATEGORIES_JSON, bak)
    print(f"backup: {bak}")
    touched = 0; skipped = 0; missing = []
    for cat in cats:
        cid = cat.get("id")
        if cid not in T: continue
        mapping = T[cid]
        archs = cat.get("archetypes") or []
        for a in archs:
            name = (a.get("name") or "").strip()
            if name in mapping:
                en_name, en_body = mapping[name]
                a["name_en"] = en_name; a["body_en"] = en_body; touched += 1
            else:
                if not a.get("body_en") and a.get("body"):
                    skipped += 1; missing.append(f"{cid}: {name}")
        d = cat.get("defaultArchetype") or {}
        if "_default" in mapping and d:
            en_name, en_body = mapping["_default"]
            d["name_en"] = en_name; d["body_en"] = en_body; touched += 1
    tmp = CATEGORIES_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON)
    print(f"touched: {touched}\nskipped (no body_en, no mapping): {skipped}")
    if missing:
        for m in missing: print(f"  - {m}")

if __name__ == "__main__":
    main()
