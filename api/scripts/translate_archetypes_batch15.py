"""Archetype EN backfill — batch 15: Internet part 2 (content_format_2020s + tiktok_persona + meme_archetype)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "content_format_2020s": {
        "Короткое и быстрое": ("Short and fast",
            "You live in vertical videos. TikTok, YouTube Shorts, Reels — your environment. Content longer than a minute is a whole episode for you, requiring effort. And you don't see this as a problem; you see it as the evolution of attention.\n\n"
            "This works because in a world with so much information, filtering through the short is the fastest way. In 30 seconds you understand whether you need to go deeper. Most things — you don't.\n\n"
            "People sometimes accuse you: \"you have clip thinking\". You don't argue. It's true. And it's not the worst quality in the era of an information storm. Better clip-like and precise than linear and outdated.\n\n"
            "What's worth knowing: short formats poorly carry the complex. If you only consume them, the ability to hold large concepts is lost over time. Learn to balance: short for scanning, long for the deep. Otherwise the world shrinks for you to the level of a TikTok video, and a lot of important things don't fit there."),
        "Глубокое и длинное": ("Deep and long",
            "You need 20 minutes, an hour, two — to enter a topic. Podcasts, long video essays, longreads — that's your format. The short for you is bait, not food. Food is the deep.\n\n"
            "This works because you understand: real value is in the nuances. And nuances don't fit in 60 seconds. Any serious topic requires context, unfolding, contradictions. You're willing to spend that time.\n\n"
            "People sometimes are surprised: \"you really watched all of that?\". Yes, really. And remember it, and thought it through. You have more nuances in your head than those who live on short clips — and it shows in conversations.\n\n"
            "What's worth knowing: long formats are a great source, but they too can be a drug. If you listen to podcasts 4 hours a day, you have no time for your own thoughts. Learn to alternate: consumption + reflection. Otherwise you're an erudite without your own voice. Voice matters more than erudition."),
        "Текстовые обсуждения": ("Text discussions",
            "You need places where people write and discuss. Telegram channels with comments, X threads, Reddit subreddits, Dzen blogs. Not one isolated \"opinion\", but a living conversation of many.\n\n"
            "This works because you understand: real truth is usually in the middle of disagreements. One post is one point of view. But a post + 200 comments is a map of reality.\n\n"
            "People sometimes say: \"why do you read comments, there's only anger there\". Not only. There — real people with their own angles of view. And if you learn to filter the noise, comments often have more meaning than the post itself.\n\n"
            "What's worth knowing: reading comments is a great analytical skill, but also an emotional load. In heated discussions it's easy to take on someone else's anger. Learn to tell \"informative debate\" from \"toxic dump\". The first — worth reading. The second — pass by. Without this filter, comments will eat your nervous system."),
        "Сообщества": ("Communities",
            "What matters to you are places where people really talk. Telegram chats, Discord servers, specialized forums. This isn't \"content\" in the usual sense — it's a living pack of people you joined.\n\n"
            "This works because your social brain works on close groups, not on a wide audience. You're not interested in \"what millions say\", you're interested in \"what those 30 people who know me say\".\n\n"
            "People sometimes don't understand that for you, leaving a favorite Discord chat is like moving to another city. It's not an \"app\", it's your social place.\n\n"
            "What's worth knowing: strong communities are huge value, but they're fragile. A fight, conflict, the admin leaves — and the place can collapse in a day. Learn not to invest your whole social life in one place. Build something else in parallel. If the main one falls, you're left with anchors."),
        "Стримы и аудио": ("Streams and audio",
            "You like live broadcasts. Streams on Twitch, audio rooms, real-time podcasts. What grabs you is exactly the \"now\" — what's happening while you listen, and you're part of that moment.\n\n"
            "This works because the broadcast has a quality the recorded doesn't: unpredictability. The recording is edited, smoothed. The broadcast is alive, with slips, with moments of truth.\n\n"
            "People sometimes are surprised: \"you really listen to streams for 4 hours?\". Yes, and for you it's a full social activity. You're not alone — you're with others, just in another format.\n\n"
            "What's worth knowing: broadcasts are a strong attention drug. The streamer says \"don't leave, something interesting is coming\" — and you stay, even though you planned for 30 minutes. Learn to set a timer. And remember: if your main socializing is with streamers who don't know you — that's a simulation of relationships, not relationships."),
        "Ниша и старая школа": ("Niche and old school",
            "You read what almost nobody reads. Narrowly specialized forums, fanfic communities, themed longreads on Substack or Dzen. You need depth that the mass audience doesn't reach.\n\n"
            "This works because you understood: interesting things are rarely in the top. In the top — what reaches many. And you usually need what reaches few, but precisely. And that requires digging.\n\n"
            "People sometimes are surprised: \"where do you know this from?\". The answer — from places they haven't heard of. These places don't market themselves; people who are searching come to them.\n\n"
            "What's worth knowing: the niche is a strength and a trap. Strength — depth. Trap — isolation. If you live only in narrow communities, you lose the sense of the mainstream, and sometimes you're surprised that ordinary people don't know what seems obvious to you. Learn to at least superficially track the mass — otherwise you miss the context of conversations with non-niche people."),
        "_default": ("Your own set of formats",
            "You're not tied to one format. In the morning you scroll TikTok, at lunch you listen to a podcast, in the evening you read a long post on Telegram. Each mood — its own register.\n\n"
            "This is a rare quality. Most people get stuck in one format and don't notice how their picture of the world narrows. You don't. In your information stream, fast sources work (for the pulse), and slow ones (for depth), and conversational ones (for emotion).\n\n"
            "People sometimes don't understand how you have time. You don't have time — you choose. And what you choose, you finish completely.\n\n"
            "What's worth knowing: variety requires management. If you have no internal filter, you can fragment your attention across 20 sources and get value from none. Once a month do an audit: where did I spend the most time? Was it valuable? If not — reorient. The information stream is your resource, not your master."),
    },
    "tiktok_persona": {
        "Тихий зритель": ("Silent viewer",
            "You scroll for hours without a trace. Don't like, don't comment, don't share. Just watch, pass by. You have no digital footprint on TikTok — you're like an invisible person.\n\n"
            "This works because you're on TikTok for relaxation, not participation. It's enough for you to see, and you don't feel the need to react. For the algorithm this creates difficulty — it doesn't understand what you like — but you didn't come for the algorithm.\n\n"
            "People sometimes don't believe you: \"how do you sit so many hours and not like anything?\". And you're not sitting — you're flowing through videos. It's meditation, not social activity.\n\n"
            "What's worth knowing: silent consumption is harmless as long as it stays under control. When you notice that 2 hours have passed and you don't remember what you saw — that's an alarming signal. That's no longer rest, it's dissociation. Learn to leave the app before the brain shuts off. And remember: the feed is infinite, time isn't."),
        "Активист и боец": ("Activist and fighter",
            "You're on TikTok not just for watching. You're at war. Against toxic content, against spam, against the algorithm. You report, block, argue in comments. You believe the feed is shared, and everyone should defend it a little.\n\n"
            "This works because you're not a passive consumer. You have agency — you influence what's around, even when it's \"just an app\". And for that you deserve respect, because 99% of those next to you just float.\n\n"
            "People sometimes surprise you: \"why are you climbing into the comments again, let it go\". And you can't let it go. If you see injustice or lies, it pulls at you.\n\n"
            "What's worth knowing: fighting in TikTok comments is bailing out the ocean with a spoon. The algorithm fundamentally rewards the controversial and emotional, so your \"educational work\" only fuels what you're fighting. Learn to choose battles. For most toxic stuff, the best tactic is ignoring, so the algorithm doesn't boost it."),
        "Куратор для своих": ("Curator for your own",
            "You don't share posts with the world, you send them to specific people. This video — to Masha. This — to Oleg. Every clip gets an addressee from you, and through you they get what will land for them.\n\n"
            "This works because you're attentive. You remember who likes what, and seeing content, you instantly understand — for whom. It's a form of caring — not \"I thought of you\", but \"I thought of you and found something specific\".\n\n"
            "People love this in you. From you come not random links, but hits. You're like a personal TikTok concierge for friends.\n\n"
            "What's worth knowing: the curator works as long as it stays sincere. If you start sharing videos to mark attention rather than because it really grabbed you — close ones will feel it. They'll value five videos sent from the heart higher than fifty sent out of duty."),
        "Создатель": ("Creator",
            "You don't just watch — you film. You make your own videos, jump on trends, duet and stitch. Sometimes you dream of getting on the for-you page. You understood that in an era where platforms search for creators, your chance to be heard has never been higher.\n\n"
            "This works because you have courage. Most sit and consume; you decided to create. And that already separates you from 99% of users, even if the views are still modest.\n\n"
            "People sometimes tease you: \"and how many followers do you have there?\". You don't care. You do it not for the numbers, but because you want to. And sometimes the numbers come on their own when you stop thinking about them.\n\n"
            "What's worth knowing: creating content is a marathon, not a sprint. Most give up after 20 videos without virality. Those who reach 200 usually start to understand something about their audience. Main rule: do it regularly, not perfectly. The perfect isn't needed at all."),
        "Фильтратор серьёзного": ("Filterer of the serious",
            "No dancing, no jokes. You have only serious content on TikTok: education, politics, business analytics, science. You trained the algorithm to filter everything empty, and it took time, but it worked.\n\n"
            "This works because you understood: TikTok isn't entertainment, it's a medium. You can use it as fast food, you can — as an educational channel. Most choose the first; you — the second.\n\n"
            "People sometimes are surprised: \"you have everything about economics and philosophy? Where are the jokes?\". There are no jokes. They put me to sleep. I need the feed to invigorate, not dissolve.\n\n"
            "What's worth knowing: a serious feed works, but it too is exhausting. If you only have heavy topics, the brain doesn't rest in this app at all — and you leave it more depleted than you entered. Learn to add at least 20% light: nature, animals, harmless humor. Not from lowering standards, but from caring for your nervous system."),
        "Циклы возвращения": ("Cycles of return",
            "You don't sit on TikTok constantly. You go in for a couple of weeks, immerse, then delete the app or forget about it for a month or two. Then return again. This is your healthy rhythm.\n\n"
            "This works because you feel when the app starts eating you. Most don't notice this and sit forever; you notice and leave. This is a rare ability for self-regulation.\n\n"
            "People sometimes are surprised: \"you deleted TikTok again?\". Yes, and I'll install it again later when I want to. This isn't \"I can't handle myself\", this is \"I choose my own tempo\".\n\n"
            "What's worth knowing: cycles work if in the breaks you do something valuable. If you just replace TikTok with YouTube or Reels, that's not a break, it's switching bottles. Learn to use breaks for the non-network: books, walks, real meetings. Then the cycles give real recovery."),
        "Внимательный смотрящий": ("Attentive watcher",
            "You rewatch every clip three times. Not from being slow — but because the first time you missed details, the second time you saw more, the third time you understood. You don't \"consume\" content — you process it.\n\n"
            "This works because you have deep attention. Most on TikTok glide on the surface; you dig. And so from the same videos you extract three times more.\n\n"
            "People sometimes don't understand: \"you really watched this meme three times?\". Seriously. Because there was a structure built into it that you saw only on the third pass. And now you understand it.\n\n"
            "What's worth knowing: attention to detail is your superpower, but it eats time. If you rewatch every video, you don't get out of TikTok for hours. Learn to tell \"this is worth rewatching\" from \"this is just a habit\". Not every clip deserves your deep attention. Most are one-time."),
        "_default": ("Your own TikTok mode",
            "You don't have one signature behavior. Sometimes you watch silently, sometimes comment, sometimes film, sometimes delete the app for a month. This isn't a contradiction, these are different moods.\n\n"
            "Most people on TikTok behave the same way always — either always scrolling, always creating, or always running from it. You're more flexible, and so your relationship with this platform is more balanced.\n\n"
            "People sometimes can't predict what you'll be like today. That's normal — you don't always know yourself.\n\n"
            "What's worth knowing: flexibility works as long as it stays conscious. If you're \"however it goes\" — you're reactive, not free. Once a month check: what's in my TikTok now? How much time do I spend there? Does it give me something? Regular check-ins save from invisibly slipping into a mode you didn't choose."),
    },
    "meme_archetype": {
        "Острая ирония": ("Sharp irony",
            "Your humor is biting. Through sarcasm, irony, trolling, you say truths that can't be said directly. This isn't anger; it's a form of precision. Direct speech is often impermissible — and irony breaks through.\n\n"
            "This works because you sharply see mismatch. Between what people say and what they do. Between how it looks and how it is. And when you ironize, you hit exactly that crack.\n\n"
            "People either adore you or fear you. Those who can read irony enjoy it. Those who read literally get offended. You sometimes abuse this, and sometimes unfairly.\n\n"
            "What's worth knowing: irony is a powerful tool, but also a defense. If you only ironize — you're hiding from direct speech. And from direct closeness. Learn to tell \"I ironize because it's more precise\" from \"I ironize because it's scary to speak seriously\". The first — style. The second — a wall that gets in your own way."),
        "Грустный шутник": ("Sad joker",
            "Your humor is soaked in sadness. Dead inside, emo jokes, gloomy-funny. You laugh at what makes others want to cry — and often cry at what others find funny.\n\n"
            "This works because you have a deep sense of the world. You see the finiteness in any joy, the layer of loneliness in any joke. And that's your style: laughter through sadness, and sadness through laughter.\n\n"
            "People sometimes don't understand: \"you're joking, but I'm scared\". That's normal. Your jokes require a certain level of inner experience. Those who've gone through it recognize their pain in your humor and laugh from relief.\n\n"
            "What's worth knowing: melancholy as style — beautiful. Melancholy as a way of life — heavy. If you notice you can't be glad without a layer of bitterness, that any good news in your head immediately turns into \"but soon it'll be bad\" — that's no longer a style, that's a symptom. Learn to tell them apart. And don't be afraid to ask for help if the line blurred."),
        "Хаос-нейтрал": ("Chaotic neutral",
            "Logic isn't for you. Your humor is chaos: absurd, nonsense, memes without reason and context. You repost what others find delirium, and you understand why it's funny.\n\n"
            "This works because you freed yourself from the need to \"understand\" every joke. Sometimes a thing is funny not \"because of\" but \"despite\". And if you sink into this, a whole layer of internet humor opens up that's inaccessible to literal thinkers.\n\n"
            "People split in two. Some cry from laughter at your reposts. Others look with empty eyes. Whether a person matches you on a sense of chaos — that's for you one of the main tests of closeness.\n\n"
            "What's worth knowing: chaotic neutral works in the group of your own. With strangers your humor can read as \"is everything okay with his head?\". Learn to filter who to show what. And remember: chaos is style; mess in real life is something else. Don't confuse the first with permission for the second."),
        "Позитивный вибро-кит": ("Positive vibe whale",
            "Your feed is sunny. Cats, people's successes, kind memes, motivation. You don't \"avoid negativity\" — you consciously curate what gets to you. And you understood that mood depends on the feed, and you don't surrender it to the algorithm.\n\n"
            "This works because you understood: attention is the most valuable resource, and it should be spent on what charges you. Most people think they're \"just scrolling\" and it doesn't affect them. You know — it does.\n\n"
            "People sometimes call you \"naive\". That's a surface reading. You're not naive — you're chosen. Knowing the bad world doesn't stop you from purposefully keeping the good in your field of view.\n\n"
            "What's worth knowing: positivity as mode works, but has a price — you can miss something important and negative. Wars, crises, real dangers. Learn to spend at least 10% of time on complex topics — not for pleasure, for the fullness of the picture. Otherwise your sunny world will one day collide with reality, and the blow will be disproportionate."),
        "Архивист культуры": ("Culture archivist",
            "You have terabytes of memes in your saved. You don't post them, you collect. You have memes from the 2010s in your collection that most have already forgotten. You're an invisible librarian of the internet era.\n\n"
            "This works because you understand: memes are a slice of culture. Through them you see what a generation lived by, what it found funny, what it found shameful. In 30 years, scholars will study this era through what you collect today.\n\n"
            "People sometimes don't understand: \"why so many?\". And when the perfect meme is needed for a situation, they come to you — and you find exactly what's needed.\n\n"
            "What's worth knowing: collecting is a hobby, but sometimes becomes an attempt to replace participation. If you only collect but never share — your collection is dead. Learn to sometimes post, even your favorites. Sharing the best is a form of generosity. Keeping it alone is loss."),
        "Альт-сцена": ("Alt scene",
            "Your humor is from a dark aesthetic. Alt, sigma, gothic, esoteric. You don't sit in the general internet — you sit in your corners, where your set of images and jokes has gathered, inaccessible to the mainstream.\n\n"
            "This works because you have your own identity, and it doesn't fit into mass templates. You're not \"alone against everyone\", you're just part of a subculture most don't see. And you're warm there.\n\n"
            "People sometimes call this \"strange\". You don't care. You have your own people, and they laugh at the same things, and that weighs more than the crowd's understanding.\n\n"
            "What's worth knowing: subculture is a great zone, but it has its own trends and its own pressure of conformism. Sometimes \"alternativeness\" becomes not freedom but another form of imitation (just fewer people imitating). Learn to tell \"I chose this because it's close to me\" from \"I chose this so as not to be like everyone\". The first — selfhood. The second — reaction."),
        "Создатель мемов": ("Meme creator",
            "You don't just consume — you create. You spot moments others miss and turn them into memes. Sometimes yours hits wide circulation; sometimes stays in a narrow circle. But you create.\n\n"
            "This works because you have a rare ability to see the structure of humor. Most \"laugh at the funny\", and you understand why it's funny. And thanks to this, you can construct the funny from nothing.\n\n"
            "People sometimes fear you: \"I don't joke around you, because you immediately see how flat it is\". And you're not a critic — you're just a high standard. And thanks to you, the company laughs more precisely.\n\n"
            "What's worth knowing: creating memes is a creative practice, and it requires constant flow. If you stop for a year — the skill can't work at full strength. Learn to maintain the practice even when uninspired. One or two memes a week, minimum. That keeps the muscle, and it stays sharp for the moment a golden idea comes."),
        "Двуликий улыбатель": ("Two-faced smiler",
            "Your humor is a smile with a blade. Outside everything is sweet, kind, positive. And inside — a precise slap reaching the recipient a second later. You've mastered the art of toxic-kind, and you do it better than most.\n\n"
            "This works because you have a fine sense of social norms. You see that direct criticism isn't received, and you found a workaround — pack it in a form of support so it slips under the radar. That's exactly your superpower.\n\n"
            "People sometimes don't understand right away. \"Oh, thanks, you said it so sweetly\". An hour later — \"wait, that was actually pointed\". That's how it should be. That's your style.\n\n"
            "What's worth knowing: toxic-kind is a powerful tool, but has a high price in closeness. If people don't know when you're sincere, they stop believing even the kind words. Learn to alternate: sometimes — a direct compliment without needles, sometimes — direct criticism without smiles. Otherwise your style turns into permanent defensive armor."),
        "_default": ("Your own meme mix",
            "You don't have one signature humor. With some people you're ironic, with others — gloomy-funny, with a third group — kind-vibey. You switch registers under the audience, and it comes naturally.\n\n"
            "Most people are stuck in one tone. They're funny with one group and dead with another, because they can't adapt. You're more flexible, and so your own everywhere.\n\n"
            "People sometimes are surprised: \"you're different with everyone?\". Not different — flexible. You have one core, but different wrappings.\n\n"
            "What's worth knowing: flexibility works as long as it stays conscious. If you adjust your humor \"to please\" — that's loss of self. If — \"to be understood\" — that's respect for the interlocutor. Once a month check: do I adjust from love for them or from fear of not being liked? The first — wonderful. The second — energy-draining."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch15.{ts}")
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
