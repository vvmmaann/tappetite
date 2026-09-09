"""Archetype EN backfill — batch 16: Internet part 3 (ru_classic_memes + you_in_comments + your_creator_type)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "ru_classic_memes": {
        "Жизненный реалист": ("Lived realist",
            "Your favorite memes are about reality. \"Zhiza\" (life-truth), \"baza\" (the base), \"nu takoye\" (meh), \"eto drugoye\" (that's different) — that's your dictionary. You don't like artificial jokes; you need a real situation behind a meme, one you yourself have been in.\n\n"
            "This works because you're grounded. You have life experience, and humor for you is a way to recognize it in someone else's telling. When you see the right meme, your reaction is \"oh, exactly, same with me\".\n\n"
            "People love you for this. With you no need to explain context — you immediately hit the tone. And the memes you repost are always \"on topic\", not random.\n\n"
            "What's worth knowing: realism is a great filter, but sometimes becomes cynicism. If all memes are about \"meh, everything's nonsense\" — over time you start to feel that way too. Humor is a mirror, and you see yourself in it. Learn to add at least a little of the bright. Otherwise in a year only a bitter chuckle at everything will remain of you."),
        "Диванный критик": ("Couch critic",
            "Cringe, dushnila (the dry, tedious one), creepy — your vocabulary. You sharply see when something is fake, and don't stay silent about it. Your style is criticism through memes: precise, cutting, sometimes cruel.\n\n"
            "This works because you don't buy the shiny. You see a cheap move in a film — you'll mark it as cringe. You see a tedious blogger — you'll call them dushnila. You can't be fooled, and so your circle of communication respects this.\n\n"
            "People sometimes fear you a bit: \"it's scary to joke around you, you'll immediately tear it apart\". You won't tear it apart — you'll mark it. That's different. But they don't fully believe it.\n\n"
            "What's worth knowing: criticism is a great skill, but also dangerous. If everything is always \"cringe\" or \"dushnila\" for you — you're no longer a critic, you're background of denial. Over time this destroys the ability to feel joy. Learn to tell real failures from just \"not mine\". Not every \"not mine\" deserves your strike."),
        "Самоархетипажник": ("Self-archetyper",
            "Sigma, skuf (the slipping middle-aged guy), altushka (the alt girl), dead inside — you recognize yourself in these labels. Not seriously, but with self-irony. \"Yeah, I'm exactly a skuf\" — and you're even glad. The chance to put a label on yourself gives you a feeling of belonging.\n\n"
            "This works because memes have become a tool of self-definition. Earlier people defined themselves through Jung's questions, now — through TikTok archetypes. This isn't superficial; it's just a new language for an old thing.\n\n"
            "People sometimes tease you: \"you're really a typical sigma\". You smile. They don't understand that for you, \"being a typical sigma\" is neither an insult nor a compliment, just stating belonging to a tribe.\n\n"
            "What's worth knowing: labels are a convenient language, but they simplify. If you describe yourself only through them, you lose the nuances of your personality. The same person can be sigma, skuf, and emo at once — depending on mood. Don't cling to a label as identity. It's a hat, not a head."),
        "Поколенческий пограничник": ("Generational borderlander",
            "Boomer, zoomer, skuf, altushka — you use these terms as a map of the world. You understand which generation you belong to, and you see how other generations differ. And you ironize on both sides of the border.\n\n"
            "This works because you see generations as different cultures. They have different language, different values, different ideas of what's proper. And not \"right-wrong\", but \"different\". This interests you.\n\n"
            "People sometimes accuse you of ageism: \"you discriminate against boomers\". And you don't discriminate — you study them anthropologically. Through memes. That's quite a tool.\n\n"
            "What's worth knowing: generational division is convenient but crude. Within a generation there are also different people, and sometimes a zoomer with a boomer is closer to each other than with their \"peers\". Learn to see a person not as a representative of a generation, but as a person. Otherwise you're a captive of labels and miss interesting people on the other side."),
        "Фольклорист": ("Folklorist",
            "Chiki-briki, c'mon bro, chushpan, baza — you have a folklore collection. These words aren't from textbooks; they're from internet basements, from subcultures, from unexpected sources. And you know how to relate to them — not from above, but as part of cultural heritage.\n\n"
            "This works because for you, internet folklore is the folk art of the 21st century. Earlier people passed each other ditties, now — memes and phrases. It's the same culture, just in a new wrapper.\n\n"
            "People sometimes don't understand how you remember all these words and where they came from. You don't remember — you live among them. It's not \"collecting\", it's \"ordinary language\".\n\n"
            "What's worth knowing: folklore is a great environment, but it ages quickly. What was the base two years ago — now is cringe. Learn to feel when your vocabulary is fresh and when — already grandma's (by internet standards). Refreshing the dictionary is part of life in a living culture."),
        "Тёмный эстет": ("Dark aesthete",
            "Creepy, dead inside, altushka, cringe — your set of words is concentrated in a dark palette. You can see the eerie in the ordinary and the ordinary in the eerie. Your humor is at the junction of gothic and meme.\n\n"
            "This works because you have a different sensitivity. Most want \"the light, bright, kind\". You choose \"the strange, uncomfortable, real\". And in this — most of the art that survives centuries.\n\n"
            "People sometimes shy away: \"you're kind of eerie\". You smile. They got used to sterilized culture, and any roughness seems dangerous to them. And you in it — at home.\n\n"
            "What's worth knowing: dark aesthetic is style and risk. Style — because depth and character. Risk — because it's easy to slip into when you want not art, but just a bad mood. Learn to tell: am I choosing this because it's beautiful, or because it's hard for me right now and I want to surround myself with my pain? The first — aesthetic. The second — a reason to take care of yourself."),
        "Тонкий язык": ("Subtle language",
            "\"That's different\", \"meh\", \"the base\", \"dushnila\" — you use these short expressions instead of long arguments. Each contains a whole semantic block, and natives understand you without decoding.\n\n"
            "This works because you've mastered high language density. \"That's different\" isn't three words, it's a whole rhetorical position that in academic style would require a paragraph. You economize, and that's not laziness — it's mastery.\n\n"
            "People sometimes don't catch up: \"what does 'baza' mean?\". You don't get angry; you remember that once you didn't know either. Just different subcultures — different codes.\n\n"
            "What's worth knowing: your language works among your own and translates badly. If you try to explain something to your parents through \"that's different\" and \"baza\", they won't hear you. Learn to switch: with the young — your code, with others — ordinary language. Flexibility of registers is respect, not selling out."),
        "_default": ("Your own RU-meme mix",
            "You don't have one signature meme that describes you. You use different ones — sometimes life-real, sometimes dark, sometimes generational. Depends on mood and company.\n\n"
            "This is rare maturity in an era where everyone wants to define themselves immediately: \"I'm sigma\", \"I'm altushka\". You understood that a person is bigger than any label, and don't limit yourself to one.\n\n"
            "People sometimes can't classify you precisely. With some you look like one type, with others — like another. And you're not contradictory — you're multi-faceted.\n\n"
            "What's worth knowing: flexibility works as long as you yourself know what you are at this moment. If labels switch automatically depending on company — that's no longer freedom, that's adaptation. Regularly ask: who am I in solitude, without the mirror of others' expectations? That's the real you."),
    },
    "you_in_comments": {
        "Молчун-наблюдатель": ("Silent observer",
            "You silently like, read others' arguments, write and delete, drop a heart. You're present in the comments but not visible. You read everything, react silently.\n\n"
            "This works because you have a healthy distance. Most climb into every argument; you understand that comments on the internet are rarely productive dialogue.\n\n"
            "People sometimes don't even guess you're here at all. And that's your strategy — to be present without leaving a trace.\n\n"
            "What's worth knowing: silent audience is critically important for content. If everyone is silent, authors feel they're not seen. Learn to at least occasionally drop a like — that's support without engagement. A small gesture from your side can be the difference between an author burning out and continuing."),
        "Боец комментариев": ("Comment fighter",
            "You argue, correct facts, ironize, write walls of text. You can't pass by. If someone is wrong, you must answer — even on a random stranger's post.\n\n"
            "This works because you have a civic sense. It matters to you that lies don't go unanswered.\n\n"
            "People sometimes get tired: \"you're in an argument again\". Again. Someone has to.\n\n"
            "What's worth knowing: arguing in comments is rarely productive. Algorithms love conflict and promote it. The more you write, the more you feed what you fight. Learn to choose battles. Sometimes the best reaction is ignoring. Your energy is a finite resource — spend it where it actually changes something."),
        "Поддержка тёплая": ("Warm support",
            "Hearts, plus-one, compliments to the author, \"baza\". You in the comments are a warm flame. You support, thank, say thank you.\n\n"
            "This works because you have sincere gratitude. In a world where everyone criticizes, you choose to be the one who says thank you.\n\n"
            "People sometimes are surprised: \"you're a real sunshine\". Sunshine. And what's wrong with that?\n\n"
            "What's worth knowing: \"always supporting\" sometimes becomes automatism. If you write \"fire!\" under every post, your support gets devalued. Learn to write support pointedly — where it's truly important to you. A precise thank-you weighs more than a hundred reflexive ones."),
        "Сленг и ирония": ("Slang and irony",
            "\"Baza\", memes instead of replies, irony, one symbol. You write in modern language. Not \"hello, thanks for the post\"; but \"baza\" and the 💀 emoji.\n\n"
            "This works because you live in modern internet culture. Most people over 35 don't understand this language; you do.\n\n"
            "People sometimes don't catch up: \"what does baza mean?\". Agreement. Briefly.\n\n"
            "What's worth knowing: internet slang ages quickly. What's cool in 2024, in 2026 will look old. Learn to accept this. Don't cling to one slang — it'll go away on its own. The fluency stays; the specific words rotate."),
        "Вопрошающий": ("Questioner",
            "You ask questions, correct facts, write walls of text, support. You use comments as a way to find out. Not criticism, not praise — but a question.\n\n"
            "This works because you have curiosity. It's not enough for you to read a post; you need to understand the author, their motives, their context.\n\n"
            "People sometimes are surprised: \"you have a question for every post?\". Not for every. But if I have a sincere question, I ask it.\n\n"
            "What's worth knowing: sincere questions are a rare thing in comments. Most \"questions\" are disguised criticism. Learn to formulate so the author hears exactly the interest. That'll give you more answers than you'd expect. Real curiosity is felt — and it's rewarded."),
        "Тегатель": ("Tagger",
            "You tag a friend, memes instead of replies, compliments to the author, \"first\". You use comments as a social tool. Calling a friend, marking, uniting people.\n\n"
            "This works because you have social thinking. It's not enough for you to just read a post; you need to share this with specific people.\n\n"
            "People love you for this. From you come posts they'd like, and they appreciate this.\n\n"
            "What's worth knowing: tagging too often = turning into spam. If you tag Masha under every third post, she'll stop reacting. Learn to dose. One precise tag a week works ten times stronger than ten random ones. Restraint sharpens the gesture."),
        "Минималист реакций": ("Minimalist of reactions",
            "One symbol, silent like, heart, you write and delete. You in comments are compressed to the minimum. 💀, 🔥, ??? — that's enough.\n\n"
            "This works because you understand: an emoji can contain a whole comment. No need for five sentences; one reaction says it all.\n\n"
            "People sometimes don't distinguish: \"you only put an emoji?\". Yep. That's a complete thought.\n\n"
            "What's worth knowing: minimalism works with those who understand it. With the older generation, \"💀\" under their post is \"are you mocking?\". Learn to adapt. Minimalism isn't a universal language. Save it for those fluent in the same code."),
        "_default": ("Your own reaction style",
            "You don't have one signature mode in comments. Sometimes you argue, sometimes tag a friend, sometimes write at length, sometimes silently like. Depends on the post, mood, topic.\n\n"
            "This works because you have a flexible social mind. Most people react the same way everywhere; you switch.\n\n"
            "People sometimes don't understand: \"you both argued and praised under this post?\". Yep. Different parts of the post — different reactions.\n\n"
            "What's worth knowing: variety of reactions is wealth, but sometimes worth holding the line. If in one chat you're a \"debater\", in another a \"silent one\" — that's normal. Within one post — reactions should be consistent. Otherwise the author can't read whether you're with them or against."),
    },
    "your_creator_type": {
        "Влогер жизни": ("Life vlogger",
            "Vlogger, lifestyle blogger, travel blogger, food blogger. You make content about your life. Not \"about a topic\"; but about how you live.\n\n"
            "This works because you have an audience interested in exactly you. Not your knowledge, but you yourself.\n\n"
            "People sometimes reproach you: \"you're putting your life on display\". I am. It's work, and it's my space.\n\n"
            "What's worth knowing: lifestyle content drains privacy. In 3-5 years you may feel that nothing personal is left. Learn to keep something private even in a fully open life. Without this you burn out. The audience doesn't need everything; you need somewhere to come back to that no one is watching."),
        "Образовательный": ("Educational",
            "Edutainment, podcast, analytics, reviews. You make content that teaches. Not \"entertains\"; but leaves something new in the head.\n\n"
            "This works because you have a passion for knowledge and the ability to explain it. That's a rare combination.\n\n"
            "People sometimes say: \"that's boring\". Boring — for those who want only the light. For me and my viewers — the opposite.\n\n"
            "What's worth knowing: educational content has lower virality than humor, but more sustainable growth. Learn to accept this. And don't give up — in the fifth year of the channel you sometimes find you have a loyal audience that pays for courses. The slow build compounds; the fast one usually breaks."),
        "Юмор и тренды": ("Humor and trends",
            "Comedy and memes, shorts master, challenge participant, analyst. You're in the TikTok era. Short video format, trends, instant response.\n\n"
            "This works because you have a sense for trends. Most people notice trends after 2 weeks; you — at the start.\n\n"
            "People sometimes don't take you seriously: \"those are just jokes\". Jokes. That collect millions of views.\n\n"
            "What's worth knowing: humor is the hardest genre for sustainability. A joke ages in a week; to stay relevant you have to constantly invent. Learn to take care of yourself — comedians often burn out. The audience demands always-on; the creator is human and needs off-time."),
        "Эстетический": ("Aesthetic",
            "Aesthetic content, art creator, food blogger, travel. You make visually polished content. Every frame is thought through to composition.\n\n"
            "This works because you have an eye and patience. Most vloggers shoot \"however it comes out\"; you make little films.\n\n"
            "People sometimes are surprised: \"you spent an hour on one frame?\". An hour. And that one frame works for 100 random ones.\n\n"
            "What's worth knowing: aesthetic content is slow in production and in growth. If you don't have patience for years, you'll give up. Learn to accept the tempo. Quality always wins in the long run. Fast and ugly outperforms in week one; slow and beautiful outperforms across years."),
        "Сторителлер": ("Storyteller",
            "Storyteller, podcaster, motivator, analyst. You tell stories. Not \"information\"; but narratives that hold attention.\n\n"
            "This works because you have a skill. Most people tell flatly; you can do it coherently, with intrigue, with a finale.\n\n"
            "People sometimes say: \"with you it's like a book\". That's the best compliment I've gotten.\n\n"
            "What's worth knowing: storytelling requires practice. You can't become a good storyteller in a month. Learn regularity. Telling something every day — even just to a friend — is training. The skill stays sharp only if used; sharing-aloud is the gym for it."),
        "Гейминг и стримы": ("Gaming and streams",
            "Gamer-streamer, shorts, challenges, vlogger. You live in gaming content. Streams, reactions, game reviews — that's your niche.\n\n"
            "This works because you have a passion for games and a community sense. Most gamers play silently; you share.\n\n"
            "People sometimes don't understand: \"what kind of work do gamers have?\". A lot. It's both playing, entertaining viewers, and running a community simultaneously.\n\n"
            "What's worth knowing: gaming content is brutal on burnout. An 8-hour-a-day stream is a load on the nervous system. Learn to schedule. And don't fixate on one game — its audience will die before you do. Diversification of titles is survival, not betrayal."),
        "Арт и творчество": ("Art and creativity",
            "Art creator, aesthetic, food blogger, lifestyle. You make art in content format. Paintings, drawings, cooking as creativity, space as art.\n\n"
            "This works because you have an artistic language. It's not enough for you to \"just show\"; it needs to be visually beautiful.\n\n"
            "People sometimes are surprised: \"you don't earn from this\". Not yet. In a few years, maybe — no. That's not the main thing.\n\n"
            "What's worth knowing: art on social media rarely monetizes quickly. Learn to build the \"commercial\" side in parallel — orders, courses, selling reproductions. Without this, art will stay only a hobby. The art is the soul; the business model is the body that lets it keep walking."),
        "_default": ("Your own content mix",
            "You don't have one signature format. Sometimes a vlog, sometimes a meme, sometimes a podcast. You adapt to the platform and the idea.\n\n"
            "This works because you have flexibility. Most creators get stuck in one format; you experiment.\n\n"
            "People sometimes can't predict what you'll post tomorrow.\n\n"
            "What's worth knowing: variety is good for experiment but bad for growth. Algorithms love certainty — \"a channel about X\". If you have \"a channel about everything\", building an audience is hard. Learn to at least periodically return to one format. The experiments stay; the spine of the channel needs a recognizable shape."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch16.{ts}")
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
