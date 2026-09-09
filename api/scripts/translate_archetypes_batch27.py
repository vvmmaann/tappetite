"""Archetype EN backfill — batch 27: Otnosheniya part 5 FINAL (ideal_date_format + after_argument + digital_red_flag).

This completes the entire archetype EN translation project.
"""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "ideal_date_format": {
        "Уютная классика": ("Cozy classics",
            "Coffee, walk, dinner at a restaurant, bookstore. You need a classical date format. Not \"creative\"; but proven — where you can talk and be yourself.\n\n"
            "This works because you have a mature relation to dating. \"Impressing\" isn't enough for you; you need to really get to know the person.\n\n"
            "People sometimes say: \"coffee is banal\". Banal. And ideal for a first meeting.\n\n"
            "What's worth knowing: classical formats work if you yourself aren't banal. Coffee with an interesting person is interesting; with a boring one — boring. The place doesn't make the date."),
        "Активные и спорт": ("Active and sport",
            "Sport together, a trip out of town, picnic in the park, exhibition. You need joint action. Not \"sit and talk\"; but do something and through this get to know each other.\n\n"
            "This works because you have a kinesthetic approach. It's hard for you to \"just talk\"; you need action as background.\n\n"
            "People sometimes are surprised: \"bowling on a date right away?\". Right away. You see how a person loses — that's the best test of character.\n\n"
            "What's worth knowing: active dates sometimes put a partner in an awkward position. If they don't like sport, your choice can seem like pressure. Learn to feel. Before suggesting, find out preferences."),
        "Кино и культура": ("Cinema and culture",
            "Cinema, exhibition, concert, bookstore. You need a shared cultural experience. Not \"discuss the weather\"; but get an impression together and then discuss it.\n\n"
            "This works because you have cultural depth. \"A date for the sake of a date\" isn't enough for you; you need the evening itself to be valuable.\n\n"
            "People sometimes say: \"you don't talk in a museum\". Not during — but after. And those are the best conversations.\n\n"
            "What's worth knowing: cultural dates work with those who share your level of interest. If a person goes to the museum \"because you wanted\", they're bored, and it's visible. Learn to feel. Not everyone is your person."),
        "Атмосферно и романтично": ("Atmospheric and romantic",
            "Night city, rooftop, bar, dinner at a restaurant. You need atmosphere. Not \"daytime coffee\"; but something with mood — lights, wind, darkness.\n\n"
            "This works because you have aesthetic sensitivity. It matters to you not only \"with whom\", but also \"where\".\n\n"
            "People sometimes get snobby: \"you're a romantic\". A romantic. And I don't apologize for it.\n\n"
            "What's worth knowing: \"atmospheric\" places are often more expensive. Learn to plan the budget. And not every partner will appreciate it — for some, a warm cafe matters more than a fashionable rooftop."),
        "Дома и интимно": ("Home and intimate",
            "Cooking together at home, movie at home, coffee, walk. You love dates that aren't \"go out\", but \"stay together\". Home for you is intimate territory, and letting in is a serious step.\n\n"
            "This works because you have a deep relation to intimacy. Not \"many dates with different ones\"; but a serious connection with one.\n\n"
            "People sometimes are surprised: \"cooking on a first date?\". Not on a first. But soon after.\n\n"
            "What's worth knowing: home dates work when there's trust. If you invite home too quickly, the partner can read it as pressure. Learn to feel the tempo."),
        "Спонтанность": ("Spontaneity",
            "Spontaneously wherever, a trip out of town, walk, picnic. You need unpredictability. Not \"a scheduled plan\"; but the chance to end up somewhere unexpected.\n\n"
            "This works because you have a love for the moment. The best dates happen when you don't know what'll be.\n\n"
            "People sometimes worry: \"what if nothing works out?\". It'll work out. With me something always works out.\n\n"
            "What's worth knowing: spontaneity works with someone who shares it. If the partner is a planner, your \"spontaneity\" is their horror. Learn to adapt. Sometimes worth preparing a plan B, and spontaneity will work only when both are ready."),
        "Первое впечатление": ("First impression",
            "Coffee, walk, bookstore, sport. The first format matters to you. Something light, without pressure, where you can meet, talk, and without obligations — see if there's a spark.\n\n"
            "This works because you have the wisdom of trial meetings. Not \"dinner for 3 hours right away\"; but a 30-60 minute test.\n\n"
            "People sometimes say: \"you're somehow superficial\". Not superficial — wise. After 30 minutes it's already clear whether to continue.\n\n"
            "What's worth knowing: \"short first dates\" are also a risk. Sometimes people open up at the second hour. Learn to feel. If there's at least some interest after 30 minutes, extend. Maybe the main thing is just beginning."),
        "_default": ("Your own format",
            "You don't have one signature format. With one partner — coffee, with another — concert, with a third — a hike in the mountains. You adapt to the person.\n\n"
            "This works because you have flexibility. Most people go on the same dates with everyone; you don't.\n\n"
            "People sometimes are surprised by the variety of your dates.\n\n"
            "What's worth knowing: flexibility is wealth, but sometimes worth knowing what's ideal for you. If you constantly adapt, you don't know what really suits you. Learn to listen to yourself."),
    },
    "after_argument": {
        "Уход в себя": ("Withdrawal into self",
            "After an argument you slam shut. Not because you want to punish the other — but because there's too much noise inside, and you need silence to figure it out. You can't think aloud at this moment. You can only be silent and process.\n\n"
            "This works as a defense mechanism: until emotions settle, any words risk making it worse. Better nothing than something you'll regret later.\n\n"
            "People — especially the partner — sometimes read this as \"boycott\" or \"coldness\". Actually you're not rejecting, you're processing. They just don't see the process, only the silence.\n\n"
            "What's worth knowing: silence is useful for you, but painful for the partner. Sometimes worth saying \"I need time, I'm not angry, I'm just thinking\" — one sentence that'll save the other from sitting in unknown for hours. This is a small phrase, but it saves many relationships."),
        "Первый шаг": ("First step",
            "It's unbearable for you to be in cold war. After an hour, two, maximum a day — you write first. Not because you're guilty, but because peace is dearer than principle. \"Who's right?\" is a secondary question for you. The main thing is to be on the same wavelength again.\n\n"
            "This isn't weakness, but maturity disguised as softness. Most people can hold a grudge for weeks because of who'll write first. You understand this game is the dumbest possible. So you exit it first.\n\n"
            "People love you for this, but sometimes abuse it. If they know you'll write anyway, they have less incentive to take a step themselves. This is an imperceptible asymmetry that accumulates over time.\n\n"
            "What's worth knowing: your readiness to make peace is a gift to the partner, but also a risk for you. Sometimes worth waiting for the other to take a step. This isn't a game of principles — it's healthy distribution of responsibility. Otherwise you become the only one responsible for the quality of the relationship, and that's a lot."),
        "Аналитик после боя": ("Analyst after battle",
            "The argument ended — and in your head it's just beginning. You replay every word, analyze where it broke, what should have been said differently, how to avoid it next time. This isn't self-eating — this is work on quality.\n\n"
            "You approach conflicts like bugs in code. It happened — so the cause can be understood. Understood the cause — can be fixed. The idea that quarrels \"just happen\" and you have to forget about them is foreign to you. That's irresponsible.\n\n"
            "People sometimes get tired of your debriefings. They want to leave it behind, and you return to it after an hour, day, week. For them this is \"not letting go\". For you — \"not done analyzing yet\".\n\n"
            "What's worth knowing: reflection is your superpower, but in large doses it becomes poison. If every interaction is then analyzed for hours, you stop living and start analyzing. Learn to set a timer on analysis. An hour is normal, a day is a lot, a week is no longer analysis, it's re-living."),
        "Юмор как лом": ("Humor as a crowbar",
            "When tension grows, you turn on a joke. Not from frivolity, but from understanding: laughter is the fastest way to relieve density in the room. If people laugh together, they're no longer enemies.\n\n"
            "This requires subtlety. A joke at the wrong time turns an argument into a catastrophe. A joke at the right time dissolves conflict in a second. You learned to feel the moment, and this is a rare skill. Most either always joke (and that's annoying), or never (and that's stifling).\n\n"
            "People love this in you. After your joke an argument stops seeming deadly. Everyone remembers they're on the same side, not different ones. Sometimes your humor saves relationships you don't even know about.\n\n"
            "What's worth knowing: humor is a great release, but a poor replacement for conversation. If you always translate tension into a joke, serious things never get discussed. They accumulate under the surface and burst out one day without warning. Learn to tell the moment when a joke is needed from when conversation is needed."),
        "Гордое ожидание": ("Proud waiting",
            "You don't write first on principle. If the other offended — let them take the step. You're not vindictive, not vengeful — you just understand your value and won't trade it to make \"everything good again\" through someone else's fault.\n\n"
            "This is a form of self-respect. You set a price on yourself: you can't be treated however and get the previous warmth without effort. This is a healthy boundary, and many people severely lack it.\n\n"
            "People sometimes see this as coldness or stubbornness. Actually you're not closed — you wait for an honest gesture. If it comes, you immediately melt. If it doesn't come, you draw conclusions.\n\n"
            "What's worth knowing: pride is a good servant, but a poor master. Sometimes the other person is also suffering, and doesn't write not because they don't want to, but because they don't know how. If you hold the principle \"let it be him\" for years, you can lose what was important. Learn to tell \"he doesn't take a step\" from \"he doesn't know how to take it\"."),
        "Сила в действии": ("Strength in action",
            "After an argument you don't sit and think — you do. Clean the apartment, go to the gym, immerse in work. Emotion requires an outlet, and you know the best outlet for you is physical, through movement.\n\n"
            "This works brilliantly for you: in an hour of cleaning you calm down more than in ten hours of thinking. The body is your main therapist. Adrenaline and sweat get out what words can't.\n\n"
            "People sometimes are surprised: \"how did you recover so quickly?\". The answer — I didn't. I didn't recover, I melted it down. Through running, through cooking, through anything requiring presence. This is your way of processing.\n\n"
            "What's worth knowing: action is a great way to remove the sharpness, but not a way to solve the cause. If every argument ends with your run and then \"everything's normal\", the unspoken accumulates. Learn to combine: first action to cool down, then conversation to understand. Action cleanses, conversation closes."),
        "Эмоциональный выпуск": ("Emotional release",
            "You cry after arguments — and you do right. Not because you're weak, but because you're honest. The body knows emotion must come out. If you suppress it, it returns as insomnia, headache, or a worse conflict in a week.\n\n"
            "Most people have unlearned to cry. They consider it \"not adult\" or \"not manly\". And it's the most direct path to recovery — tears literally wash stress hormones from the blood. You do this instinctively, and the body is grateful.\n\n"
            "People sometimes get lost: \"don't cry, everything's fine\". They want to help, but don't understand tears are help. Through them you return to yourself faster than any other way.\n\n"
            "What's worth knowing: tears free, but don't explain. After them a conversation about what happened is still needed. Otherwise the next argument will start from the same place as this one. Learn to use the silence after tears — this is the best time for the most important part: a calm honest conversation."),
        "_default": ("Without a template",
            "You don't have one signature way of exiting arguments. Sometimes you're silent, sometimes you write first, sometimes you cry, sometimes you go into chores. It depends on the argument, the partner, your state. You're not tied to one strategy.\n\n"
            "This gives you a huge advantage: each argument gets a reaction that suits it, not a template. Most people exit any conflict the same way, even if it doesn't work. You don't.\n\n"
            "People — especially the partner — sometimes can't predict you. After one argument you write in an hour, after another you're silent for three days. It's hard for them to understand the rules.\n\n"
            "What's worth knowing: flexibility is strength, but without communication it turns into a riddle. It matters to the partner to understand what's expected of them. Sometimes worth saying aloud: \"now I need silence\" or \"let's talk\" — so they don't guess. Adaptability doesn't cancel clarity."),
    },
    "digital_red_flag": {
        "Призрак онлайна": ("Online ghost",
            "Always online but doesn't reply; reads and doesn't react; leaves you in the visibility zone; disappears without warning. This is about people who see you and ignore.\n\n"
            "This works because you have a boundary. You understand — this isn't \"busy\", this is disregard.\n\n"
            "People sometimes don't understand: \"what if they're really busy?\". Being busy doesn't prevent writing \"sorry, busy, will reply later\". That's a second.\n\n"
            "What's worth knowing: \"eternal online without reply\" is a strong signal, but sometimes deceptive. Some people's WhatsApp/Telegram opens automatically. Learn to tell pattern from technical detail."),
        "Минимализм без эмоций": ("Minimalism without emotions",
            "Dry replies \"ok\", one word, emoji, no punctuation. This is about people who economize on words for you. Where others write in full — they write \"k\".\n\n"
            "This works because you have sensitivity to tone. \"Ok\" with a period and \"ok\" without a period are different messages for you.\n\n"
            "People sometimes reproach: \"they're just laconic\". Maybe. And that's a normal style. Or maybe they don't care about you.\n\n"
            "What's worth knowing: some people are really like that — they write briefly with everyone. Learn to observe how they write to others. If with everyone it's \"ok\", that's a style. If only with you — that's about you."),
        "Голос вместо текста": ("Voice instead of text",
            "5-minute voice messages, calls without warning, types forever and doesn't send, replies after a day. This is about people who ignore your comfort in favor of their own.\n\n"
            "This works because you have respect for someone else's space. And you notice who doesn't respect yours in return.\n\n"
            "People sometimes say: \"they just love a different format\". They love. And aren't interested in what's convenient for me.\n\n"
            "What's worth knowing: \"call without warning\" is an especially important signal in 2026. Most modern people prefer to write. If a person constantly calls without \"can I?\", they live in another era, and that's a collision."),
        "Спам коротких": ("Spam of short messages",
            "Writes several in a row, without punctuation, types forever, one word. This is about people who don't respect chat as a space.\n\n"
            "This works because you have a communication standard. 20 notifications an hour is already an attack, not communication.\n\n"
            "People sometimes say: \"they're just lively\". Maybe. But \"lively\" shouldn't mean \"without a sense of measure\".\n\n"
            "What's worth knowing: \"spammers\" sometimes turn out wonderful offline. Learn to separate. Chat style isn't equal to personality. If you love a person — teach them something about messaging. That's normal dialogue."),
        "Пассивная агрессия": ("Passive aggression",
            "Periods in short answers, ignores questions, dry replies, leaves you in visibility zone. This is about people who show displeasure through punctuation and silence.\n\n"
            "This works because you have sensitivity to subtext. You hear not only words, but tone.\n\n"
            "People sometimes say: \"you're imagining it\". Sometimes yes. But usually no — the pattern is recognizable.\n\n"
            "What's worth knowing: passive aggression is a form of communication that needs to be confronted openly. If you notice — ask directly: \"do you have something against me?\". Most passive-aggressive ones can't withstand a direct question."),
        "Нарушение приватности": ("Privacy violation",
            "Screenshots conversations, calls without warning, writes several in a row, replies after a day. This is about people for whom you're material for others.\n\n"
            "This works because you have an understanding of privacy. Chat is intimate space, and it shouldn't be displayed in someone else's groups.\n\n"
            "People sometimes don't understand: \"they showed it to a friend, what's bad?\". Bad is that my personal became public without my consent.\n\n"
            "What's worth knowing: people who screenshot are an alarming signal. They'll tell others about you tomorrow. Learn to trust only those who understand the difference between \"ours\" and \"common\"."),
        "Странное поведение в чате": ("Strange behavior in chat",
            "Types forever and doesn't send, ignores questions, disappears, screenshots. This is about people with anxious or controlling style.\n\n"
            "This works because you have observation. These oddities are visible in chat as in a microscope.\n\n"
            "People sometimes don't share it: \"everyone does that\". Not everyone. And it's more pleasant to communicate with those who don't.\n\n"
            "What's worth knowing: \"strange behavior\" in chat often reflects \"strange behavior\" in life. If a person types for 5 minutes and erases — they doubt in life too, rewrite their reactions. This isn't bad, but it's a signal of insecurity. Learn to understand."),
        "_default": ("Your own set of signals",
            "You don't have one signature digital red flag. You notice different things — dryness, disappearances, spam, passive aggression. And depending on the person you draw conclusions.\n\n"
            "This works because you understand: digital isn't a separate world, it's an extension of character.\n\n"
            "People sometimes say: \"you analyze too much\". I analyze. So as not to waste time.\n\n"
            "What's worth knowing: \"many signals\" sometimes becomes paranoia. Learn to tell a real pattern from a case. One time called without warning — maybe there was an emergency moment. Constantly — that's already a style."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch27.{ts}")
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
