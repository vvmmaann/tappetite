"""Archetype EN backfill — batch 21: Estetika part 2 (your_aesthetic + your_mood_color + your_avatar_style)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "your_aesthetic": {
        "Y2K и нулевые": ("Y2K and the noughties",
            "Y2K, soft grunge, mob wife, blokecore. What grabs you is everything that refers to the noughties and early 2010s. Not from nostalgia — you have an eye for the era returning, and you're on its wave.\n\n"
            "This works because you have a sensitive feeling for cycle. Most people live in the current; you see how the old becomes new again.\n\n"
            "People sometimes don't understand: \"are those baggy jeans?\". Yes, and metal glasses, and a leopard fur coat. It's all on purpose.\n\n"
            "What's worth knowing: the return of an aesthetic works as long as irony or rethinking is preserved. If you copy the noughties literally, you're not \"fashionable\" — you're stuck. Learn to add modernity over the retro. Then your Y2K is style, not cosplay."),
        "Чистый шик": ("Clean chic",
            "Clean girl/boy, minimal, old money, coquette. What grabs you is visual cleanness. Simple palettes, nothing extra, fabric instead of logos, groomed instead of makeup.\n\n"
            "This works because you have a mature sense of style. You understood cleanness is itself the highest class. Most people try to add; you — to subtract. And you win from this.\n\n"
            "People sometimes call this \"boring\": \"where's the character?\". Character is in quality. And it's visible if you look closely.\n\n"
            "What's worth knowing: clean chic requires upkeep. It's an aesthetic without decor, so there's nothing to hide behind — every item is visible. Cheap fabric looks cheap, a poorly pressed shirt — wrinkled. Learn to invest in quality. Without this, clean quickly turns into 'ordinary'."),
        "Тёмная академия": ("Dark academia",
            "Dark academia, soft grunge, goblincore. Leather, tweed, libraries, gloom and autumn melancholy with a hint of strangeness. You live in an aesthetic that refers to scholar's rooms and mysterious plots.\n\n"
            "This works because you have deep intellectual taste. Sterile modernity bores you; you want something around with history and character.\n\n"
            "People sometimes are surprised: \"you're like from Harry Potter\". Almost. And what's wrong with that?\n\n"
            "What's worth knowing: dark academia is beautiful but requires authenticity. If books on the shelf are for beauty, not for reading, the aesthetic falls apart. If the leather on the jacket is artificial — also visible. Learn to invest in real materials. This is an aesthetic that doesn't tolerate fakery."),
        "Кибер-будущее": ("Cyber future",
            "Cyber, acubi, maximalism. Neon, techno, Balkan internet 2024, experiment over aesthetics. You live not in the past or in the present — in the future that's only forming.\n\n"
            "This works because you have a nose for the new. Most catch trends a year after their peak; you — at the start.\n\n"
            "People sometimes don't understand at all: \"what kind of style is this?\". And there's no such style in the mainstream yet. You're on the crest.\n\n"
            "What's worth knowing: aesthetics on the crest are risky. If the wave doesn't reach the mainstream, you stay in your niche. Learn to combine the cutting-edge with the base — then even if the trend doesn't fire, you stay beautiful in any case."),
        "Природа и уют": ("Nature and coziness",
            "Cottagecore, tradwife, goblincore. Farm, pastoral, cookies, return to roots, light strangeness of nature. You create a visual world that refers to life before the internet.\n\n"
            "This works because you have longing for the simple. Modern life is too fast and sterile; you need something slow and warm.\n\n"
            "People sometimes don't share it: \"you're like from the 19th century\". And what's wrong with the 19th century? They had air, time, crafts. We're missing a lot of that now.\n\n"
            "What's worth knowing: the aesthetic of returning to roots is beautiful, but sometimes becomes a form of escapism. If in 2026 you live in a visual simulation of 1850, you miss what's happening now. Learn to keep one foot in the warm past, the other in reality. Otherwise you're a tourist in your own life."),
        "Девичья нежность": ("Girlish tenderness",
            "Coquette, tradwife, clean girl. Bows, pastel colors, tenderness, groomed. You're not \"fashionable\" in the modern aggressive sense; you create your soft world and live in it.\n\n"
            "This works because you have the courage to refuse \"strong\" delivery in an era when everyone tries to be tough. Tenderness is your form of strength, and it's rare.\n\n"
            "People sometimes call this \"infantile\". Not infantile — soft. Different things. You can be adult and tender; that's not a contradiction.\n\n"
            "What's worth knowing: tender aesthetics are beautiful, but sometimes become a cage. If you don't allow yourself a single \"strong\" element, your image becomes one-faced. Learn to add contrast sometimes — and tenderness is revealed brighter."),
        "Авангард-эксперимент": ("Avant-garde experiment",
            "Maximalism, acubi, mob wife, office siren. You need an image to surprise. Not \"fashionable\" — expressive. So that every day looks like a painting, not a uniform.\n\n"
            "This works because you have an artistic gaze. You don't dress, you create a work. And every morning is a new canvas.\n\n"
            "People sometimes get lost: \"you're extra\". And you're not \"extra\" — you're at 100%. It's a rare state, and most are afraid to approach it.\n\n"
            "What's worth knowing: experiment works if there's taste behind it. Without it it's \"strangeness\". Learn to tell when you're \"avant-garde\" and when \"strange without reason\". The first is style. The second is loss of compass."),
        "_default": ("Aesthetic hybrid",
            "You don't have one signature aesthetic — you mix. Today coquette, tomorrow goth, the day after minimal. This isn't indecision, this is understanding aesthetics are tools, not identities.\n\n"
            "This works because you have flexible visual sense. Most people choose one aesthetic and hold to it, even when they've long been bored. You switch when you feel.\n\n"
            "People sometimes can't classify you. And that's wonderful — you don't fit in one cell.\n\n"
            "What's worth knowing: flexibility works as long as you have some \"base\". If you're without a recognizable core, your style reads as \"undecided\". Once a year ask the question: what element remains, whatever I wear? That's your core. And it should be there."),
    },
    "your_mood_color": {
        "Глубокая тишина": ("Deep silence",
            "Deep blue, smoky green, dark green. You're now in a mode of calm and concentration. Not \"everything's bad\" — but \"everything's in balance, and extra outbursts aren't needed\".\n\n"
            "This works because you understood the value of silence. In a world of constant noise, choosing calm is already wisdom. And your color speaks of this.\n\n"
            "People sometimes don't understand: \"are you sad?\". Not sad. Just don't need constant fury and brightness.\n\n"
            "What's worth knowing: deep tones are great, but sometimes become a familiar background in which emotions also become muted. Learn to add bright accents sometimes — even if it seems \"not needed\". This supports your liveliness, even when you're in calm."),
        "Энергия движения": ("Energy of motion",
            "Red, orange, neon blue, gold. You're now in a phase of activity — you want to do, talk, move. Energy is high, and you feel it.\n\n"
            "This works because you have a clear direction now. Bright-colored periods happen to people when something inside has crystallized. You're on this wave.\n\n"
            "People sometimes get tired: \"you're winding things up\". Maybe. But I'm not doing it on purpose — just this is the mood now, and it requires an outlet.\n\n"
            "What's worth knowing: energy in waves is normal. Energy 24/7 is burnout. Learn to track when a bright-colored period passes into a non-resting rhythm. And don't be afraid to return to calmer tones when the body asks."),
        "Сила тишины": ("Strength of silence",
            "Black, white, gray, ice blue. You're now in a mode of closedness and control. Nothing extra, no emotions outward. This is a form of strength, not weakness.\n\n"
            "This works because you understood: sometimes you need to turn off extra signals. When much is happening inside, you don't need to additionally demonstrate this to the world. And your neutral color is about this.\n\n"
            "People sometimes worry: \"you seem cold\". Not cold — collected. Different things.\n\n"
            "What's worth knowing: neutral tones are great for discipline, but if you're stuck in them long, connection with emotions is lost. Learn to allow yourself color at least once a week. This isn't \"weakness\" — it's maintaining a healthy emotional life."),
        "Тёплая ностальгия": ("Warm nostalgia",
            "Dusty rose, mustard, terracotta, burgundy. You're now in a phase of warm melancholy and mature feeling. Not bright joy, not deep sadness — but the calm warmth of autumn aesthetics.\n\n"
            "This works because you have the ability to value nuances. You don't need extremes — you live in beautiful half-tones, and this is a rare skill.\n\n"
            "People sometimes don't read this palette: \"you're dressed strangely\". And you're in the palette of your feelings — precisely. And there's depth in this.\n\n"
            "What's worth knowing: warm nostalgia is a wonderful state, but sometimes passes into constant slight sadness. Learn to tell. If you've been in this palette for months and without exits to the bright, worth checking whether something is going into depression through aesthetics."),
        "Мечтательность": ("Dreaminess",
            "Lilac, dusty rose, ice blue. You're now in a phase of fantasy. Thinking about something else, not the here-and-now. Maybe dreaming, maybe immersed in a project, maybe just floating.\n\n"
            "This works because you have a rich imagination. While others live in flat reality, you have parallel worlds, and they feed you.\n\n"
            "People sometimes shake you: \"come back to earth!\". And you were just in a much more interesting place, and thanks, no.\n\n"
            "What's worth knowing: dreaminess is the engine of creativity, but sometimes becomes flight. If you're constantly \"not here\", in real life unsolved tasks accumulate for you. Learn to come out of dreaminess when you need to act. This isn't betrayal of fantasy — it's its preservation, because too long dreaminess wears it down."),
        "Землистое": ("Earthy",
            "Terracotta, mustard, burgundy, dark green. You're now in a phase of rooting. Something real, material, connected with soil and hands. Not empty thoughts — but the concrete.\n\n"
            "This works because you have bodily wisdom. You understand that sometimes you need to return to the simple: to the material, to the routine, to the craft.\n\n"
            "People sometimes don't share it: \"you're all in autumn tones\". My whole life right now is about autumn. And I'm good in this.\n\n"
            "What's worth knowing: earthy tones are a great anchor, but sometimes become immobility. Learn to tell \"I'm rooted and calm\" from \"I'm stuck and not moving\". The first is wisdom. The second is stagnation under the mask of wisdom."),
        "Нейтральная пауза": ("Neutral pause",
            "Gray, white, black, ice blue. You're now in \"neither here nor there\" mode. Not bad, not good — just a pause in which there are no accents. This isn't a bad state.\n\n"
            "This works because you have the ability not to panic in neutral periods. Most people fear the \"gray\" phase, because they consider it a sign of depression. You understood this is just a pause between bright stages, and it's also needed.\n\n"
            "People sometimes worry: \"is everything okay?\". Okay. Just nothing to tell now.\n\n"
            "What's worth knowing: a pause is a healthy state, but if it stretches for months, that's no longer a pause. Learn to tell. Once every two weeks ask yourself: am I in calm or in stop? If in stop — what's needed to start feeling again?"),
        "_default": ("Palette in motion",
            "You don't have one signature mood color. Today you're dark blue, tomorrow gold, the day after dusty rose. The palette changes quickly, and this isn't indecision — it's living emotional life.\n\n"
            "This works because you have a rich emotional spectrum. Most people live in 2-3 states; you have 10. This is rare.\n\n"
            "People sometimes can't keep up: \"yesterday you were bright red, today in black\". Yes. And this isn't a contradiction, this is wealth.\n\n"
            "What's worth knowing: changing the palette is normal. The complete inability to settle on one even for a day can be an alarming signal. Learn to tell living change from internal instability. The first is wonderful. The second is worth understanding what fluctuates so strongly inside."),
    },
    "your_avatar_style": {
        "Открытое лицо": ("Open face",
            "Real photo, art portrait, AI portrait. On your avatar you're visible — recognizably, directly. You don't hide; you believe it's logical to show your face on social networks.\n\n"
            "This works because you have no anxiety around publicity. You live an open life, and the avatar is its natural extension.\n\n"
            "People sometimes are surprised: \"your face really is everywhere?\". Really. What's wrong with that?\n\n"
            "What's worth knowing: openness is normal but requires understanding that you're publicly recognizable. Strangers may strike up a conversation in a cafe, exes or colleagues can find you. Learn to accept this. If openness becomes discomfort — worth thinking what to show on the avatar instead."),
        "Загадка и анонимность": ("Mystery and anonymity",
            "Silhouette, black screen, photo from behind. You don't show your face. Not from shyness — from choice. You believe social networks are a public stage, and the face is private, and shouldn't stand next to it.\n\n"
            "This works because you have a boundary between \"public me\" and \"private me\". Most people lost this boundary long ago; you preserved it consciously.\n\n"
            "People sometimes look suspiciously: \"are you hiding something?\". Not hiding — keeping for myself. Different things.\n\n"
            "What's worth knowing: anonymity is a great right, but sometimes becomes a form of avoidance. If you hide your face because you don't like yourself — that's no longer a choice, it's defense. Learn to tell. If you ever feel you want to show your face — try. It can be liberating."),
        "Лица замены": ("Face replacement",
            "Anime avatar, cartoon avatar, film character, AI portrait. You're on the avatar — but in another form. Not by face, but through an image that's closer to you than what the mirror reflects.\n\n"
            "This works because you have symbolic thinking. You understand the face is just a shell, and identity can be conveyed through a character more precisely than through a photo.\n\n"
            "People sometimes don't understand: \"are you drawn?\". In some sense yes. This character says more about me than a photo.\n\n"
            "What's worth knowing: characters as avatars are powerful, but sometimes become a way to escape from yourself. If you choose an idealized character because you don't love your face — that's no longer a creative choice. Learn to tell. The perfect avatar is the one in whom you recognize yourself, not the one you want to look like."),
        "Юмор и ирония": ("Humor and irony",
            "Meme, photo of a pet. You don't take the avatar seriously. Social networks aren't a place for strict portraits, they're a place for life, and your avatar reflects your mood, not a \"professional image\".\n\n"
            "This works because you have lightness. Most people approach the avatar like a passport photoshoot; you approach it like a meme. And there's also sincerity in this.\n\n"
            "People sometimes don't take you seriously: \"they have a cat as an avatar\". Yeah. So what? The cat is the best representative of my values.\n\n"
            "What's worth knowing: an ironic avatar works in informal contexts. On LinkedIn a cat as a profile pic is already incompatible with job hunting. Learn to feel the platform. You can have a cat in Telegram and a normal photo on LinkedIn — that's not two-faced, it's adaptation."),
        "Эстетика без лица": ("Aesthetics without a face",
            "Aesthetic photo, landscape, logo. You replaced the face with an image — and not for hiding, but for aesthetics. The atmosphere says more about you than your face at moment X.\n\n"
            "This works because your visual world is more interesting than your specific face on a single day. And you offer the world exactly that.\n\n"
            "People sometimes ask the question: \"where are you yourself?\". I'm everywhere in this photo. This is me — my view of the world.\n\n"
            "What's worth knowing: an aesthetic avatar is wonderful, but sometimes becomes a distance. With a person whose avatar is mountains, it's harder to feel a live connection. Learn to alternate: sometimes — mountains, sometimes — the face. This gives depth of contact, not just an aesthetic facade."),
        "Ностальгия": ("Nostalgia",
            "Old photo, film photo, artistic portrait. You prefer a vintage look. Not \"here I was yesterday\", but \"here I am in some special moment\". This gives depth and atmosphere.\n\n"
            "This works because you have a sense of time. You understand a moment from a grainy film has different weight than a glossy modern photo.\n\n"
            "People sometimes are surprised: \"were you photographed in the 19th century?\". Almost. And this look is closer to me than today's.\n\n"
            "What's worth knowing: a vintage avatar works as long as it stays a choice, not flight. If you don't love modern photos of yourself and so go to film — that's aesthetics as defense. Learn to tell. The perfect vintage avatar is when you like both film and the modern photo; just film you like more."),
        "Меняющийся": ("Changing",
            "Seasonal update, mood meme. Your avatar isn't static — it changes. Every month or season you update, and that's part of your relation to public identity: you're alive, and the avatar should reflect this.\n\n"
            "This works because you have no fixed image. You understand a person changes, and shouldn't freeze in one photo from 2018.\n\n"
            "People sometimes get lost: \"another different avatar?\". Another. That's normal.\n\n"
            "What's worth knowing: frequent avatar change is good up to a limit. If it's every 3 days, your face on social networks isn't memorized, and it's hard for people to \"see\" you. Learn to find a rhythm — once a month, once a season. This gives both motion and recognizability."),
        "_default": ("Your own approach to avatars",
            "You don't have a fixed avatar style. Sometimes face, sometimes character, sometimes meme, sometimes black screen. Depends on platform, mood, life phase.\n\n"
            "This works because you have an adaptive approach to public identity. Most people have one avatar everywhere; you — several, and each for its own.\n\n"
            "People sometimes confuse you: \"is that you in Telegram or you in Instagram?\". I'm everywhere. Just in different forms.\n\n"
            "What's worth knowing: flexibility works but requires consciousness. If you have different \"me\" everywhere, and none is the main one, you yourself can lose which of these images is real. Learn to keep one more or less stable version at least in personal contexts. Otherwise you're many facades, and not one door inside."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch21.{ts}")
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
