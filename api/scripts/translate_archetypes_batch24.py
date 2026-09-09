"""Archetype EN backfill — batch 24: Otnosheniya part 2 (first_date_pay + dating_2025 + phone_on_date + first_date_redflag)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "first_date_pay": {
        "Классический жест": ("Classic gesture",
            "The old school is closer to you. Whoever invited pays. Or the man pays on the first, then they agree. Or just whoever first reached for the card. This isn't patriarchy — it's about the nobility of the moment: invited a person to spend the evening with you, pay for that evening.\n\n"
            "This works because you have a sense of ritual. A date isn't \"a meeting of two adults\", it's a small theater with rules. And in this theater the gesture with payment has its place.\n\n"
            "People sometimes call you \"unmodern\". You don't argue. Unmodern in the sense of \"respecting form\"? Maybe. But this form works, and it's still pleasant for many — even those who, in words, are for \"equality\".\n\n"
            "What's worth knowing: the classic gesture works when both agree to the rules. If the partner thinks differently, your \"noble gesture\" can read as \"he thinks I can't pay for myself\". Learn to read the partner. And on the second date already worth asking aloud — what format is comfortable."),
        "Равенство и ясность": ("Equality and clarity",
            "Strict 50/50 or a prior agreement without surprises is closer to you. You don't want to either accept gestures or make them with money. A date is a meeting of two adults, and each pays for themselves. Period.\n\n"
            "This works because you have a strong sense of autonomy. Any financial inequality in a relationship for you is a potential lever of power, and you don't want it to exist. Better everything clean from the start.\n\n"
            "People sometimes don't understand: \"let it go, the person is paying\". That's not the point. The point is that after payment, an unspoken debt arises, and you don't want to start a relationship with a debt, even a small one.\n\n"
            "What's worth knowing: equality as principle is wonderful, but sometimes deprives a relationship of the warmth of a gift. If on a date everything is \"strict 50/50\", without gestures in either direction, it becomes mechanistic. Learn to allow exceptions sometimes while staying true to the principle. \"50/50 on average\" works softer than \"50/50 in every episode\"."),
        "Прагматичная договорённость": ("Pragmatic agreement",
            "For you, the main thing is for it to be clear. Whoever earns more pays; or they agree in advance; or just decide not to think about it, the main thing being a good evening. You don't cling to form — you need functionality.\n\n"
            "This works because you have a realistic view of relationships. You understand financial situations of people are different, and applying one scheme blindly to all is foolish.\n\n"
            "People sometimes are surprised by your openness: \"you're really ready to discuss money before a date?\". Ready. It'll save you both awkwardness in the moment of the bill.\n\n"
            "What's worth knowing: pragmatism works, but sometimes kills the magic. If on every date you discuss financial details in advance, the evening starts with a financial topic instead of a romantic one. Learn to feel when a money conversation is needed, and when it's better to trust the moment. Not every date requires a contract."),
        "Игра жестами": ("Game of gestures",
            "You love when payment is a gesture. Not a rule, but a signal. Whoever first reached for the card pays. Woman pays as a pleasant gesture — once, in the right place. You like when people surprise each other with small things.\n\n"
            "This works because you have a playful relation to relationships. A date for you isn't \"an exchange of resources\", but a small dance in which every step means something. Who pays is part of this dance, not its financial bottom line.\n\n"
            "People sometimes don't catch your lightness: \"you're ready to give the card on the first date?\". Ready, if the moment seems right. And this is a rare skill — to feel the moment.\n\n"
            "What's worth knowing: a game of gestures requires a partner of the same tempo. If the other person is a pragmatist, your \"game\" is confusion for them. Learn to feel who's in front of you. With players play, with pragmatists be clear. Otherwise your gesture lands on a person who doesn't read it."),
        "_default": ("Adaptive approach",
            "You don't have one rule. With one person you'll make a gesture, with another ask for 50/50, with a third calmly hand over the card, with a fourth discuss in advance. Depends on the person, situation, mood.\n\n"
            "This is rare maturity. Most people cling to one scheme and apply it to all partners. You understand different people have different ideas, and imposing one scheme is violence, not \"principles\".\n\n"
            "People sometimes can't predict your position. That's normal — you don't know yourself until you meet the specific person.\n\n"
            "What's worth knowing: adaptability works as long as it stays sincere. If you adjust \"just to please\", you lose yourself. If — because you respect another's approach — that's healthy. Once a year ask yourself: am I adjusting from love or from anxiety? The first — wonderful. The second — a reason to return your position."),
    },
    "dating_2025": {
        "Цифровой охотник": ("Digital hunter",
            "You live where most live now — in apps. Tinder, Bumble, Hinge, Telegram chats, Instagram DM. You don't consider this \"not real dating\". For you it's just a new way to meet a person, just as legitimate as any other.\n\n"
            "This works because you have no nostalgia for \"chance meetings in cafes\". You understood in the modern world such meetings are rare, and waiting for them is wasting time. Better use the tools that exist.\n\n"
            "People sometimes pity you: \"you're on apps, how sad\". And you don't grieve — you just act. And in your experience, normal people were found through apps, no worse than \"through mutual friends\".\n\n"
            "What's worth knowing: digital dating has its patterns. Swipes train the reflex to reject based on the first photo. Learn to look deeper, read profiles in full, give a second chance. And remember — everything a person showed about themselves in the app is marketing. You'll see the real person only offline, and worth looking at them, not the profile."),
        "Случай и судьба": ("Chance and fate",
            "You don't use apps, don't write first. You believe a person should appear themselves — on the street, in a queue, at an event. This isn't laziness or passivity; it's a choice: to meet only in a live environment, not through an algorithm.\n\n"
            "This works because you have patience. Most people can't withstand without active actions — they take apps, go on blind dates, just so something is happening. You can wait, and from this your rare meetings have a different weight.\n\n"
            "People sometimes worry: \"you'll never meet anyone\". Possibly. But apps don't guarantee anyone anything either. Everyone has their own path.\n\n"
            "What's worth knowing: betting on chance works if you're in places where chance is possible. If you sit at home and wait for \"him/her to appear\" — fate finds it hard to help. Learn to at least go out — to events, new places, environments with many new faces. Fate is a lottery, and in it you need to buy tickets."),
        "Через своих": ("Through your own",
            "You trust only verified channels. Through mutual friends, through work or studies, through events in your circle. Blind dates don't suit you — you need a recommendation, context, some connection before the meeting.\n\n"
            "This works because you have a strong sense of belonging to an environment. You understand: a person known to your friends can't suddenly turn out to be a nightmare, because there's a social cost for bad behavior. From apps there's no such protection.\n\n"
            "People sometimes complain: \"your circle is limited, few new people\". That's true. But in this limited circle there's more trust from the start, and that's more valuable than a huge pool of strangers.\n\n"
            "What's worth knowing: dating through your own works as long as your circle is diverse. If all your friends are from one school and one office, you won't meet anyone new there. Learn to expand the circle — through hobbies, through professional events, through distant acquaintances. That's \"through your own\", just on a larger scale."),
        "Не ищу специально": ("Not searching specifically",
            "You're not \"looking for a relationship\". You live your life, and if someone appears — great. If not — also not bad. This isn't posturing; it's calm trust in the process: what should happen will happen, without your forcing.\n\n"
            "This works because you have full self-sufficiency. You don't \"wait for love to become happy\". You're already happy, and love will be an addition, not a salvation. And this changes everything in your energy.\n\n"
            "People sometimes don't believe: \"everyone's looking, are you special?\". Not special — just not in that phase. You're good now, and you don't want to change it just because \"that's how it's done\".\n\n"
            "What's worth knowing: \"not searching\" works if at the same time you're open to meetings. If \"not searching\" means \"refusing any attempts to meet\", that's no longer philosophy — it's fear of intimacy in the mask of wisdom. Learn to tell. Not searching doesn't mean closing off. You can live your life and at the same time be ready for a meeting when it happens."),
        "_default": ("Open to everything",
            "You're not closed on any path. You can dive into an app, try through friends, and just be on the street at the right time in the right place. The main thing is openness, the method is secondary.\n\n"
            "This works because you understand: the only \"right path\" is the one that works in your case. And you don't know in advance which one it is. So you try them all.\n\n"
            "People sometimes are surprised by your breadth: \"you're on apps and through friends at the same time?\". Yes. This isn't \"desperation\", it's rationality.\n\n"
            "What's worth knowing: openness to all paths requires energy. If you're in each tool at 30%, you won't get a good result in any. Learn to concentrate: a season of apps, then events, then rest. Cycles are better than activity smeared in all directions at once."),
    },
    "phone_on_date": {
        "Полный лок": ("Full lock",
            "On a date your phone is either screen-down all evening, or in the pocket altogether. It's easier for you that way: if you don't see, you're not pulled. And you believe the person across deserves your full attention.\n\n"
            "This works because you have respect for the moment. You understand modern life scatters attention constantly, and a date is a rare chance to focus on one person. Not using it is foolish.\n\n"
            "People sometimes are surprised by your discipline: \"how do you go a whole evening without the phone?\". Easily. After three minutes you forget it even exists. The main thing is the first three minutes.\n\n"
            "What's worth knowing: full lock works if you have no real urgent matters. If you're waiting for an important call from a relative in the hospital — it's foolish to ignore it for the sake of \"date rules\". Learn to tell. And remember: warning in advance \"I might have a call, sorry\" isn't a breach of etiquette, it's respect."),
        "Прозрачно и открыто": ("Transparent and open",
            "You honestly say at the start of the evening if you're expecting a call or message. \"Sorry, my mom might call — she's in the hospital\". This short sentence removes all questions and awkwardness, and now when the phone rings, no one will think you're inattentive.\n\n"
            "This works because you have strong communication. Most people either ignore the urgent (and pay later), or get distracted without explanation (and ruin the impression). You choose a third path — transparency, which solves both problems.\n\n"
            "People love this in you. No need to guess what's with your phone. Everything is clear from the start.\n\n"
            "What's worth knowing: transparency is good when justified. If every date you start with \"I might get a call...\", it becomes awkward — it seems you're looking for excuses in advance. Use honest warning only when really expecting something. On ordinary days — better phone in the pocket and forget."),
        "Контент с первого": ("Content from the first",
            "For you a date is also joint content creation. Selfies, stories, little videos of moments. Not \"I'll post as proof\", but \"let's remember this evening together\". And you quickly understand whether the partner is ready for this or not.\n\n"
            "This works with a similar type of person. If the other also loves making stories, you immediately have a common language. Every first date turns into a small series of photos that's pleasant to revisit later.\n\n"
            "People sometimes don't understand: \"how, the phone on a date, you're getting distracted!\". Not getting distracted — on the contrary, fixing. A selfie takes 30 seconds, and the memory stays for a long time.\n\n"
            "What's worth knowing: content from the first is a great way to learn how a partner relates to publicity. If they're ready right away — you matched. If not — learn to accept. Not everyone wants to be in stories on a first meeting, and this doesn't mean \"a cold person\". It means a different rhythm of publicity, and worth respecting."),
        "Игровое правило": ("Game rule",
            "You have a fun rule: the first who pulls out a phone pays for the evening. This turns the question \"can I?\" into a small game, and usually works great: phones don't come out, and payment is agreed.\n\n"
            "This works because you have creativity. Most people approach a date seriously: \"need to make an impression\". You introduce a playful element, and from this the evening immediately becomes freer.\n\n"
            "People sometimes are surprised by you: \"you're an inventor\". And it's not invention — it's a tool. And it works: tested on dozens of dates.\n\n"
            "What's worth knowing: game rules work when both participants are playing. If a partner takes it literally — that you really want to catch them — the game breaks, and only a strange feeling remains. Learn to feel who's playing and who isn't. With the first introduce the rule playfully. With the second — forget it, and behave normally."),
        "Зависит от человека": ("Depends on the person",
            "You have no rigid rule. With one person you put away the phone completely, with another it's on the table because you both got used to it. You adapt to the partner and the dynamics of the specific evening.\n\n"
            "This works because you have no dogmatism. You understand different people live in different modes with the phone, and imposing yours is inflexibility, not principle.\n\n"
            "People sometimes demand clarity: \"how do you yourself consider it right?\". I consider it right — to hear the partner. My own mode is \"phone down\", but I don't consider it law for everyone.\n\n"
            "What's worth knowing: flexibility works as long as it stays conscious. If you \"adapt\" because you fear offending the partner, leaving the phone on the table — that's no longer flexibility, it's concession. Learn to tell \"I adjust because I'm comfortable\" from \"I adjust because I'm scared to say my own\". The first — maturity. The second — dissolution."),
        "_default": ("Your own approach to the phone",
            "You have no rigid rule, but you have a basic thought: on a date the person across matters more than notifications. Specific actions change — somewhere the phone is down, somewhere you warn about a call, somewhere you take a selfie together. But the principle is one.\n\n"
            "This works because you understand the hierarchy: real person > digital contact. And it's visible in your behavior, even without explicit rules.\n\n"
            "People feel this. The partner knows you're with them, not with the screen. And this matters more than any declarative \"date rule\".\n\n"
            "What's worth knowing: a flexible approach works as long as you yourself know your principle. If you \"do as it goes\", you'll sometimes get distracted inappropriately — and the partner will remember this. Learn to formulate for yourself — what principle you have at the base. Then specific decisions are made automatically."),
    },
    "first_date_redflag": {
        "Время и уважение": ("Time and respect",
            "What immediately throws you off is when a person is late without warning, looks at the phone, interrupts, is rude to the waiter. These are the main signals for you, because they show basic respect for others, and if it's not there in simple things, it won't be in complex ones either.\n\n"
            "This works because you understand: a first date is the best showcase. A person performs at the maximum of impression. And if even at the maximum they're late, rude, interrupting — imagine how it'll be on an ordinary day.\n\n"
            "People sometimes accuse you of strictness: \"so what, he was late\". So what. That's already a signal. And from a multitude of such signals a portrait forms.\n\n"
            "What's worth knowing: focus on \"respect\" is a great filter, but sometimes becomes perfectionism. All people sometimes are late, get distracted, react not perfectly. Learn to tell a pattern from a case. One slip isn't a red flag. A series — yes. And remember: you're not perfect either, and the partner is also noting something about you."),
        "Эго на броне": ("Ego in armor",
            "You're instantly turned off when a person talks only about themselves, can't laugh at themselves, gets offended at trifles, or lies about trivial things. All this is a sign of ego defending emptiness, and you tire from it quickly.\n\n"
            "This works because you have a mature attitude toward yourself. You understand: a confident person can joke about themselves, admit mistakes, not puff up at the slightest poke. And one who can't, deep down probably isn't confident — and their ego will be paid for many times.\n\n"
            "People sometimes don't understand the sharpness of your reaction: \"he was just talking about himself\". Too much. And too smoothly. This isn't \"sharing\" — it's a performance with no place left for you.\n\n"
            "What's worth knowing: ego exists in everyone, and sometimes a first date is a nervous moment when it crawls out unusually. Give a person a second chance before closing the door. Sometimes what you read as \"ego\" is just nervousness in an unfamiliar situation. But if the pattern repeats — yes, move on."),
        "Прошлое с собой": ("Past brought along",
            "You're alarmed when a person talks too much about exes, compares you to someone, or the whole evening revolves around their problems. For you this is a signal: this person's past isn't closed, and any relationship with them will be with the shadow of the past.\n\n"
            "This works because you understand: to start something new, you need to close the old. And if on a first date the old is still actively present, that's not \"sharing with me\" — it's \"hasn't yet exited the previous chapter\".\n\n"
            "People sometimes accuse: \"you don't let the person tell about themselves?\". Letting them tell — yes. But not turning the first evening into therapy about exes — different things.\n\n"
            "What's worth knowing: some people mention exes as biographical facts — that's normal and healthy. Others — it's an emotional storm that hasn't yet subsided. Learn to tell. The first can be maturity. The second — definitely a red flag, and you won't be wrong if you leave."),
        "Границы — и сразу нет": ("Boundaries — and right away no",
            "You're instantly turned off by boundary violation. Asks about salary right away, violates physical space, talks about a shared apartment on the first, or drinks noticeably more than normal. All this is ignoring how it should be on a first date.\n\n"
            "This works because you have a strong sense of norm. You understand: a first date is an introduction, not a job interview or a contract signing. And if a person already on it doesn't respect boundaries, in deeper relationships boundaries won't exist at all.\n\n"
            "People sometimes accuse you: \"you're rigid\". Not rigid — attentive. I noticed, and that was information I used.\n\n"
            "What's worth knowing: focus on boundaries is great, but sometimes becomes paranoia. Not every rough moment on a first date is a boundary violation. Sometimes it's just nervousness or cultural difference. Learn to tell a real violation from accidental awkwardness. And remember: boundaries are your side, and some of them are your private ones, not universal."),
        "Поведение в моменте": ("Behavior in the moment",
            "You attentively watch how a person behaves now. Are they rude to the waiter. Do they complain about food, weather, the place. Do they drink more than normal. Do they lie about small things you can verify. For you this is a real testimony, not what a person says about themselves.\n\n"
            "This works because you have an analytical eye. You understand: people say one thing about themselves, and do another. And the first time, the most informative is to watch, not listen.\n\n"
            "People sometimes are surprised: \"he made a complaint — that's already a red flag?\". Depends. A justified complaint — no. About trifles — yes. That's a marker of how a person handles the world.\n\n"
            "What's worth knowing: attention to detail is your superpower, but sometimes becomes paranoia. You can start seeing red flags where there are none, simply because you're nervous. Learn to tell \"I noticed something in the person\" from \"I'm looking for an excuse to flee\". The first — healthy reading. The second — your fear of intimacy in the mask of criticism."),
        "Открытое неуважение": ("Open disrespect",
            "You'll be instantly turned off if on a first date a person demonstratively flirts with others, or is so egocentric they ignore you, or complains about everything around. All this is open signals \"I don't care about you\", and you read them right away.\n\n"
            "This works because you have self-respect. You don't excuse another's behavior with \"maybe they're nervous\". If a person on a first date shows you disrespect — they show who they are.\n\n"
            "People sometimes call for softness: \"give a chance, maybe he had a bad day\". Maybe. But a bad day doesn't excuse bad behavior. And if you forgive now, you'll have to forgive always.\n\n"
            "What's worth knowing: tough filters save time, but can also cut off good people in a bad moment. In one in 10 cases you might be cutting off someone who really was just nervous. That's your right, but consider the price. And maybe sometimes worth saying aloud: \"I noticed something is off, are you okay?\". Maybe the person comes to themselves."),
        "Прелюдия катастрофы": ("Prelude to catastrophe",
            "You're scared when on a first date a person already talks about the serious — about shared housing, about a wedding, about kids. Or asks about finances with future intent. Or too much about exes, or gets offended at innocent things. All this for you is alarm signals: you're shown the future, and it's heavy.\n\n"
            "This works because you have a sense of normal tempo. You understand: closeness is built gradually, and serious topics come at their own moment. If they come right away — that's not \"depth\", it's either the partner's anxiety or manipulation.\n\n"
            "People sometimes are surprised: \"but they're open, sharing\". Not open — rushing. And usually behind this rush stands \"I urgently need a relationship\", not \"I found my other half\".\n\n"
            "What's worth knowing: sometimes \"too serious right away\" isn't a red flag, but a different culture of closeness. Some people really immediately share everything — that's their norm. Learn to tell \"open and mature\" from \"urgently need a relationship\". The first — a rare treasure. The second — a future catastrophe."),
        "_default": ("Your own set of signals",
            "You don't have one main red flag — you have a list of small things, and you watch all of them. Late + phone + interrupting + complaining = enough. One of these signs — no, but their combination — yes.\n\n"
            "This works because you have multi-level attention. You don't react to single signals, you look for a pattern. And this is a rare ability — not to close off from the first small slip, but also not to ignore accumulating ones.\n\n"
            "People sometimes don't understand how you decide: \"he did such-and-such, do you have a table?\". No table, but in your head there is. You count signals automatically.\n\n"
            "What's worth knowing: your approach is the best possible, but requires trust in your own intuition. If you constantly doubt your assessments, you lose confidence in reading the situation. Learn to trust your observations. This isn't \"paranoia\" — this is counting data. And usually you're right, just not always immediately visible."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch24.{ts}")
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
    print(f"touched: {touched}\nskipped: {skipped}")
    if missing:
        for m in missing: print(f"  - {m}")

if __name__ == "__main__":
    main()
