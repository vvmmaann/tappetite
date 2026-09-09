"""Archetype EN backfill — batch 14: Internet part 1 (internet_vibe + your_social_network + messaging_style)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "internet_vibe": {
        "Хронически онлайн": ("Chronically online",
            "You're online 24/7, and that's not an image — it's your reality. The first thing you do in the morning is open the phone. The last thing before sleep — also. Between — constant feed refreshes, tabs, pings, doomscrolls.\n\n"
            "This isn't about addiction in a bad sense. For you, the internet isn't \"another place\", it's the main place of life. There are your friends, your information, your work, your entertainment. The real world is just a break between online sessions.\n\n"
            "People sometimes judge you: \"get off the phone\". They don't understand that for you, network life and real life are equivalent. Their dominant world is just different.\n\n"
            "What's worth knowing: chronically-online mode works in the moment, but has a price. Concentration, sleep, relationships — everything gradually erodes, and you may not notice. Learn to catch body signals (insomnia, fatigue, anxiety) and connect them with screen time. If they grow — the mode needs adjustment."),
        "Тихий вкус": ("Quiet taste",
            "Your online — without logos and without noise. You don't show brands, don't chase trends, don't put crazy emojis in your bio. Your content — muted tones, precise fonts, considered minimalism. Quiet luxury in pure form.\n\n"
            "This isn't performative modesty. This is understanding: real value doesn't need labeling. When you choose something, you choose by essence, not by label. It's visible at first glance — your content has a character that doesn't try to please you.\n\n"
            "People sometimes call this \"boring\". Boring — for those used to shouting. For those who can see the subtle — your style sounds louder than any crazy stuff.\n\n"
            "What's worth knowing: quiet luxury works as long as it stays conscious. If you choose muted because \"it's fashionable\" — you're in fashion, not in your own taste. Regularly check: am I choosing this because I really like it, or because I'm afraid of looking vulgar? The first — style. The second — also fashion, just a different color."),
        "Главный герой": ("Main character",
            "You live your life as a plot in which you're the lead. Not from ego, but from understanding: everyone is the main character of their story, and shrinking yourself into a side role is weakness, not modesty.\n\n"
            "This works because you do, not observe. You go to new places, start new projects, try new things. When you film and post it, it's clear that you have a life, not a repetition of someone else's.\n\n"
            "People sometimes envy you, sometimes get irritated: \"you're at it again with your stories\". Envy — because they'd want to live that way too. Irritation — because they chose to be supporting characters, and your light highlights their choice.\n\n"
            "What's worth knowing: \"main character\" is about you yourself, not about how you look. If you do things for the content, you're not the main character — you're an extra in your own show. Learn to tell living from filming. The best moments often stay unrecorded, and they stay with you."),
        "Эскапист уюта": ("Cozy escapist",
            "Your online is a refuge. Cottagecore, soft pastel aesthetics, pictures with stoves and bread. You run from the world's noise into your corner, where time goes slowly and beautifully.\n\n"
            "This works because you understood: the outside world right now is very aggressive. Wars, crises, anxiety every 15 minutes in the news. Maintaining clarity of mind in this stream is impossible. So you create yourself a different landscape — where there's warm light, lazy mornings, nature.\n\n"
            "People sometimes call this \"escapism\". Yes, so what? Escapism isn't evil. It's self-preservation. When the world demands constant readiness for the bad, the right to sometimes step out of it is healthy.\n\n"
            "What's worth knowing: coziness as a mode is wonderful, but it's worth knowing when it crosses into avoidance. If you can't watch the news, talk about real problems, have an opinion on serious topics — you're not resting, you're hiding. Learn to alternate: coziness for recovery, exit for participation. Otherwise the world will change without you — and not in your favor."),
        "NPC на автопилоте": ("NPC on autopilot",
            "You joke about yourself: \"I'm in NPC mode\". You open an app, scroll, like, close. Don't remember what you saw. Open it again — repeat. Life passes by your attention, and you notice it, but don't know how to stop.\n\n"
            "This isn't laziness or stupidity. It's overload. The modern internet is specifically built so you can't focus: infinite feeds, variable rewards, dopamine traps. Most people in this system are NPCs, you just see it.\n\n"
            "People sometimes judge you: \"pull yourself together\". This isn't about \"yourself\". It's about a system stronger than the average person's will. Acknowledging this is the first step out.\n\n"
            "What's worth knowing: NPC mode is reversible. You don't have to \"delete all social media\", that rarely works. What works: bring slow activities back into your life. Reading a book. A walk without the phone. Cooking with focus. These practices return the taste for real time, and gradually the network anesthesia weakens."),
        "Y2K-возвращенец": ("Y2K returner",
            "You're grabbed by nostalgia. The aesthetic of the 2000s, Tumblr 2014, the metallic textures of Y2K. You were born at the intersection of eras and understood that the best was earlier. Not everything, but a lot.\n\n"
            "This isn't a \"refusal of the present\". It's understanding that each era had its own taste, and some of them left with the era. Today's internet has sterilized everything — the same fonts, the same layouts. Earlier, every place was a character with its own personality.\n\n"
            "People sometimes twirl a finger: \"there you go again about the past\". And you're not \"about the past\", you're about variety. If there were something equally vivid now, you'd be there. But now — gray, and you return to where it was vivid.\n\n"
            "What's worth knowing: nostalgia is a powerful feeling but a bad advisor. The past always looks better than it was — memory distorts. Learn to tell genuine love for an aesthetic from the trap of \"everything was better before\". The first — healthy. The second — depression about the future, disguised as love for the past."),
        "Эпоха графиков": ("Era of charts",
            "Your online is tickers, charts, market news. Crypto, stocks, macro — you watch them like the weather. You don't necessarily trade — but you watch, and you understand more than most.\n\n"
            "This works because you understood: in the modern world, financial literacy is more important than many other things. Money is the infrastructure of freedom. Whoever understands how it moves depends less on accidents.\n\n"
            "People sometimes call this \"boring\". They don't understand that for you, market movement is a plot: with heroes (companies), villains (regulators), drama (crises). You're not bored — you're interested in a grown-up way.\n\n"
            "What's worth knowing: watching the markets is okay, living in them isn't. If you check charts every 30 minutes, you're not an investor — you're a player. Learn to tell them apart. The best portfolios belong to those who look once a quarter, not once an hour. Constant watching steals calm and rarely adds returns."),
        "_default": ("Your own internet mix",
            "You don't have one signature vibe online. Sometimes you're quiet luxury, sometimes chaotic-neutral, sometimes a serious observer. Depends on the platform, on the mood, on the company.\n\n"
            "This is a rare quality. Most people choose one aesthetic and stick to it because it's easier. You understood that's poverty — and so you mix.\n\n"
            "People sometimes can't predict what you'll be like online today. On LinkedIn — serious, in a Telegram chat with friends — meme-y, on Instagram — aesthete. This isn't hypocrisy, these are different sides.\n\n"
            "What's worth knowing: a mix works as long as behind all the faces there's one you. If different platforms turn into different people without a common core — that's no longer a mix, it's fragmentation. Regularly ask: what \"I\" comes through all these images? If there's an answer to that question — you're fine. If not — worth stopping and gathering."),
    },
    "your_social_network": {
        "Видео-наркоман": ("Video addict",
            "You need movement on screen. You'll read text if you absolutely must, but real relaxation is video. Short, long, any. The main thing is someone speaking, something happening.\n\n"
            "This works because your visual perception is stronger than textual. You absorb information faster through face and voice than through letters. And you're not weird — most of the world is moving in this direction, you're just ahead.\n\n"
            "People sometimes shake their heads sadly: \"you've forgotten how to read?\". You haven't forgotten — you just chose the tool that suits you. That's rational, not lazy.\n\n"
            "What's worth knowing: video is a stream, and in a stream it's hard to think. If you only consume video, your capacity for deep reflection is lost — because video leads you, not you it. Learn to balance: video for relaxation and entertainment, text — for serious. Otherwise in 5 years you'll find you can't finish a book."),
        "Текстовый человек": ("Text person",
            "You need the word. Not picture, not video, not voice — text. You live in networks where people write — Telegram channels, X, Reddit, Threads. There people think and formulate, and you're with them on the way.\n\n"
            "This works because you process information fastest through text. You can scan a post in 10 seconds and decide whether it's worth investing more attention. With video you can't — it leads you at its own speed.\n\n"
            "People sometimes call this \"old school\". You don't care. You understand that text is the densest carrier of meaning. Five sentences can contain more than five minutes of video.\n\n"
            "What's worth knowing: text attracts the same kind — and that's wonderful. But in text-based networks, it's easier to slip into arguments and burnout. Learn to filter: subscribe to those who write something interesting, unsubscribe from those who only get angry. Text is a powerful tool, and negativity in it sounds even louder than in video."),
        "Эстет визуала": ("Visual aesthete",
            "What matters to you is how it looks. You sit on Pinterest for hours, you're on Instagram for the aesthetic, not the likes. You need pictures that are beautiful in themselves, not as illustrations of something.\n\n"
            "This is a form of caring for your environment. You understand that what you see shapes what you feel. So you curate your visual feed as carefully as others curate their playlist.\n\n"
            "People sometimes don't understand: \"why do you sit on Pinterest? It's pointless\". And you know — not pointless. That's exactly the point: to accumulate a visual library, from which your own style later emerges.\n\n"
            "What's worth knowing: the visual is powerful, but also escapist. You can get so carried away by beautiful pictures that your own life seems gray. Learn to tell \"I'm getting inspired\" from \"I'm escaping into someone else's moments\". The first pushes you to act. The second replaces action with viewing."),
        "Карьера в сети": ("Career online",
            "You use social networks as a professional tool. LinkedIn, work chats, professional communities in Telegram. You don't \"have fun online\" — you work, develop, network online.\n\n"
            "This works because you understood: in the modern world, careers are built not only in the office. Who knows whom, who writes what, who's interested in what — all this is public, and shapes reputation invisibly.\n\n"
            "People sometimes tease you: \"is everything about work for you?\". Not everything. But more than them — and that gives you an advantage they don't see, until the moment comes.\n\n"
            "What's worth knowing: a professional network requires constant watering. Once a year update the profile, talk to people, post something meaningful occasionally — that's an investment that accumulates. But don't turn it into an obsession. If in a week you have more LinkedIn messages than messages to friends — worth reviewing priorities."),
        "Олд-скул": ("Old school",
            "You remember how it was before. LiveJournal, Tumblr, early VK with audio — you had a real life there. Now many platforms have become different, but you didn't throw them out completely. You still have friends, stories, content there.\n\n"
            "This is a form of loyalty. You don't follow platform fashion; you follow people. If people important to you stayed in an old place, you go there, even if newcomers don't know that place anymore.\n\n"
            "People sometimes are surprised: \"you're still on VK?\". Yes, still. And there — real people, and for you they weigh more than TikTok's algorithmic feed of strangers.\n\n"
            "What's worth knowing: loyalty to the old is wonderful, but it shouldn't be the only strategy. If you sit only on dying platforms, you gradually lose connection with what's happening now. Learn to balance: one or two \"old homes\" + one or two \"new scenes\". Then you keep both history and the present."),
        "Геймер-комьюнити": ("Gamer community",
            "Discord, Twitch, Reddit, YouTube — your environment. These aren't \"social networks for communication\", they're the place where you live a parallel social life — with streamers, clan chats, memes of your subculture.\n\n"
            "This works because you have a deep world that others are just tourists in. You have lore, history, favorite figures, specific jokes. It's a full second life, and it's just as real to you as the regular one.\n\n"
            "People sometimes devalue it: \"those aren't real relationships\". And you know — they're real. Just living in a different context. You can be friends with someone 5000 km away, and that doesn't make the friendship less real.\n\n"
            "What's worth knowing: online communities are strong, but give one specific form of closeness. Without offline contacts it becomes isolation over time. Learn to mix: online friends + at least 2-3 people in the physical world you see in person. Otherwise after 5 years, life is heavily skewed into one register."),
        "Спонтанный момент": ("Spontaneous moment",
            "You like when network life is alive. BeReal, Snapchat, early Threads — where people post right now, without editing, without staging. For you that's much more honest than carefully constructed Instagram.\n\n"
            "This works because you got tired of staged aesthetics. All those perfect shots that are actually fake have worn you out. You want to see a real person in their real moment — even if it's not \"beautiful\".\n\n"
            "People sometimes don't share it: \"that's not tasty, not stylish\". And for you, \"tasty and stylish\" is a synonym for \"fake\". You choose honesty even at the cost of aesthetics.\n\n"
            "What's worth knowing: spontaneous formats pretend they're \"unfiltered\", but they have their own rules too. A BeReal photo at a cafe is also staging, just at another level. Learn to see this. The most honest form of posting is not posting certain moments at all, and living through them without an audience."),
        "_default": ("Your own set of networks",
            "You don't have one main social network. You use several, each for its own: Telegram for work, Instagram for aesthetics, Reddit for deep topics, TikTok for entertainment. None dominates.\n\n"
            "This is a rare maturity. Most people live in one app and don't understand how others work. You didn't get attached — and so the platform didn't hook onto you.\n\n"
            "People sometimes are surprised: \"you're everywhere at once?\". Not everywhere. Just chose the minimum needed in each. This isn't scattered, it's an instrumental approach.\n\n"
            "What's worth knowing: variety requires management. If you don't watch, it turns into chaos — dozens of notifications, no clarity on who wrote what where. Once a quarter do an audit: which networks give me value, which — only noise? Don't be afraid to unsubscribe. Less is better."),
    },
    "messaging_style": {
        "Голос важнее текста": ("Voice over text",
            "Voice messages longer than a minute, video circles, dry \"ok\". You prefer not to type. Voice is faster, the face is livelier, text is for the weak.\n\n"
            "This works because the spoken is your strong side. Text limits you; in voice you're you.\n\n"
            "People sometimes get indignant: \"another 5-minute voice message!\". Another. If reading is inconvenient, listen.\n\n"
            "What's worth knowing: voice messages require the recipient's time. You gifted yourself speed, them — five minutes of listening plus the inability to skim. Learn to feel when voice is fine, when text is better. Especially if it's a request or important fact. Voice is your gift to yourself; text is a gift to them."),
        "Спам коротких": ("Short message spam",
            "One word = one message, twenty in a row. Dry \"ok\", \"haha\" without emotion, \"brb\" and you disappear. It's faster for you to write in pieces than to formulate.\n\n"
            "This works because you have a lively rhythm of thinking. Thoughts come in portions, and you toss them out immediately, without waiting for full shaping.\n\n"
            "People sometimes get tired: \"just finish writing it!\". I finished. Just in parts.\n\n"
            "What's worth knowing: 20 short messages = 20 notifications on the recipient's phone. That's annoying. Learn to at least group them. Ideally — one message that holds your whole stream of thoughts. Your tempo doesn't have to become their interruption."),
        "Простыня и пунктуация": ("Wall of text and punctuation",
            "Walls of text, perfect punctuation, you rewrite five times, emojis and exclamations. You make messages like little documents.\n\n"
            "This works because you have respect for form. Most write \"however it comes out\"; you believe even in chat it's worth writing properly.\n\n"
            "People sometimes are surprised: \"you don't have to use commas in chat\". Don't have to — but I prefer it. And the recipient too, I hope.\n\n"
            "What's worth knowing: perfectionism in chats eats time. If you rewrite a message five times, that's no longer a chat, it's a letter. Learn to let go. Not every message has to be perfect. Some thoughts are best delivered raw — the polish steals the moment."),
        "Через картинки": ("Through pictures",
            "Stickers instead of words, memes instead of replies, video circles, links without context. For you, text is the last tool. First a picture, meme, video, link.\n\n"
            "This works because you have visual thinking. You're faster at \"finding the right meme\" than formulating in words.\n\n"
            "People sometimes don't accept it: \"a sticker isn't an answer\". It's an answer. Just in another language.\n\n"
            "What's worth knowing: visual communication works with those who understand it. With your mom, a sticker instead of \"how are you\" isn't \"modern\", it's \"you're not answering\". Learn to adapt to the recipient. Your favorite language isn't universal; with some people, words are still the way through."),
        "Эмоциональная вата": ("Emotional padding",
            "Emojis and exclamations, \"haha\" without emotion, perfect punctuation, you rewrite five times. Your messages are saturated with emotional markers, even when there's nothing particular inside.\n\n"
            "This works because you understand: text doesn't carry intonation. Without an emoji, the phrase \"ok\" reads as offense; with an emoji, as light agreement.\n\n"
            "People sometimes say: \"why 100 exclamation marks?\". So it's clear I'm not offended, but really agreeing.\n\n"
            "What's worth knowing: \"haha\" without emotion turns into background. If you write it automatically, the recipient stops taking your \"haha\" seriously. Learn to use emotional markers more rarely but more precisely. Saved for the moments that need them, they keep their meaning."),
        "Призрак чата": ("Chat ghost",
            "You read but don't reply, answer a day later, \"brb\" and disappear, link without words. You're unpredictable in messaging. You can be online but not react.\n\n"
            "This works because you have your own tempo. You don't believe you have to answer immediately; that's your freedom.\n\n"
            "People sometimes get offended: \"you saw the message\". I saw it. Not in the mood right now.\n\n"
            "What's worth knowing: silence after reading = worse than no reply. If the other person sees you \"read but stayed silent\", it's interpreted as \"they don't want to talk\". Learn to at least reply briefly: \"saw it, will answer later\". A two-second message saves a relationship from a day of silent doubt."),
        "Постоянно онлайн": ("Always online",
            "You answer instantly, voice messages, spam of short messages, video circles. You live in the messenger. Reply in 30 seconds — normal; in 5 minutes — already a delay.\n\n"
            "This works because your nervous system is tuned to fast communication. You're bored waiting; you need the dynamic of a conversation.\n\n"
            "People sometimes are surprised: \"don't you work?\". I work. Just answer in parallel.\n\n"
            "What's worth knowing: instant reply eats focus. If you're in chat every minute, you're not really working. Learn to turn off notifications at least an hour a day. The best work happens in silence. Your speed is a strength; protecting it from itself is the next level."),
        "_default": ("Your own style",
            "You don't have one signature messaging style. With different people you write differently. With one — voice messages, with another — walls of text, with a third — only memes.\n\n"
            "This works because you adapt. Most people write the same way to everyone; you understand different people understand different registers.\n\n"
            "People sometimes are surprised: \"you always write me briefly, but to him long?\". Yes. That's not two-faced — that's respect for the different.\n\n"
            "What's worth knowing: adaptability is good as long as it stays sincere. If you adjust to please, you lose yourself. Learn to feel: am I adjusting from love or from anxiety? The first — wonderful. The second — a reason to come back to yourself."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch14.{ts}")
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
                if not a.get("body_en"):
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
