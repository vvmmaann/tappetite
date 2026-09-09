"""Archetype EN backfill — batch 26: Otnosheniya part 4 (red_flag_others + attraction_type + how_you_flirt)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "red_flag_others": {
        "Понты и грубость": ("Showing off and rudeness",
            "Rudeness to waiters, showing off, control, jealousy without reason. These are your stop signals. Each shows the person doesn't respect others.\n\n"
            "This works because you have a strong sense for character. These signs are visible from the first minute, and you read them.\n\n"
            "People sometimes reproach: \"you're strict with people\". Strict. Because time on bad people is wasted.\n\n"
            "What's worth knowing: these signs sometimes coincide with ordinary nervousness on a first meeting. Learn to tell pattern from case. One episode of rudeness can be a bad day; systematically — character."),
        "Скудная личность": ("Scant personality",
            "No hobbies, dullness, no self-irony, contempt for others' tastes. These are your stops. These people are boring, and you understand right away.\n\n"
            "This works because you yourself have depth. You're bored with those who don't.\n\n"
            "People sometimes say: \"maybe they didn't have time for hobbies\". Maybe. And that's already information.\n\n"
            "What's worth knowing: \"no hobbies\" sometimes means \"haven't found yet\". Learn to tell emptiness from search. One — a flag; the other — a stage of life."),
        "Враньё и контроль": ("Lies and control",
            "Lies about small things, control, jealousy without reason, gossip about exes. This is a pattern. Any one of these traits is a flag; all together is the profile of a toxic partner.\n\n"
            "This works because you have an analytical sense. You notice not single episodes, but patterns.\n\n"
            "People sometimes don't believe: \"but they love you\". Maybe. But love doesn't excuse control.\n\n"
            "What's worth knowing: these signs are often disguised as \"care\". \"I just worry about you\" = \"I want to know where you are\". Learn to tell. Real care doesn't require access to your phone."),
        "Хаос и непунктуальность": ("Chaos and unpunctuality",
            "Chaos without plans, constant lateness, ignoring, dullness. This is about disrespect for time. Someone else's time.\n\n"
            "This works because you value time. Lateness \"sometimes\" doesn't anger you; the habit of it does.\n\n"
            "People sometimes reproach: \"you're a stickler\". Not a stickler — respecting time. Different things.\n\n"
            "What's worth knowing: some people live in chaos and can't otherwise. This isn't malicious intent — it's neurochemistry. Learn to tell. If a person really tries, and is late 10 minutes instead of an hour — they're growing. If they don't change at all — that's not for you."),
        "Эмоциональный груз": ("Emotional burden",
            "Whining, jealousy without reason, no self-irony, control. This is about people who turn every interaction into emotional energy exchange — and not in your direction.\n\n"
            "This works because you have a boundary. You understand — your nervous system isn't for someone else's eternal \"everything's bad\".\n\n"
            "People sometimes say: \"you're indifferent\". Not indifferent — protecting my own.\n\n"
            "What's worth knowing: sometimes whining is just a bad period. Learn to tell \"moment\" from \"character\". Some complain for a week and then return to normal; some — for years. These are different people."),
        "Нарушение границ": ("Boundary violation",
            "Disrespect for boundaries, rudeness to waiters, contempt for others' tastes, gossip about exes. This is about people for whom another is a tool, not a personality.\n\n"
            "This works because you have a clear understanding of boundaries. Not everyone sees them; you do.\n\n"
            "People sometimes don't share it: \"they're just joking\". Joking — but at others' expense. And that's not a joke, it's contempt in the wrapping of a joke.\n\n"
            "What's worth knowing: people with poor boundaries are often the same with everyone, not just you. Learn to observe how they communicate with waiters, parents, strangers. This gives a full portrait."),
        "Жадность и мелочность": ("Greed and pettiness",
            "Greed, lies about trifles, no hobbies, showing off. This is about people whose values are upside down. Money is more important than people; the external more important than the internal.\n\n"
            "This works because you have a mature relation to money and status. And you feel bad with those who don't.\n\n"
            "People sometimes reproach: \"you condemn him for thrift?\". Thrift isn't greed. Thrift is respect for money. Greed is fear.\n\n"
            "What's worth knowing: greed is often disguised as \"practicality\". Learn to tell. A really practical person spends money on the important. The greedy don't spend on anything except insurance against loss."),
        "Прошлое тащит": ("Drags the past",
            "Gossip about exes, lies about trifles, no self-irony, dullness. This is about people who haven't closed the past and drag it into every new relationship.\n\n"
            "This works because you have a sense of stage. You understand — everyone has a past, but not everyone lives in it.\n\n"
            "People sometimes don't understand: \"they're sharing\". Sharing — 30 minutes about an ex on a first date? That's not \"sharing\", that's \"stuck\".\n\n"
            "What's worth knowing: an unsurvived past partner in someone else's head is your rival. And you'll always lose, because in memories that one is more ideal than any real person. Learn to leave."),
        "_default": ("Your own set of flags",
            "You don't have one main red flag in others. You notice different things — rudeness, showing off, whining, control. And depending on what set a specific person has, you draw conclusions.\n\n"
            "This works because you have wide observation. Most people focus on one; you see a pattern.\n\n"
            "People sometimes are surprised: \"how do you decide so quickly?\". Quickly — because I see the full portrait, not one stroke.\n\n"
            "What's worth knowing: \"many flags\" sometimes becomes paranoia. If you see red flags in everyone, the problem isn't in people, it's in your filter. Learn to tell real signals from ordinary human imperfections. No one is perfect."),
    },
    "attraction_type": {
        "Тебя притягивает ум": ("You're attracted by the mind",
            "What grabs you is the head. From the first minute of conversation you hear how a person thinks — and if they think interestingly, you're gone. Not face, not status, not wit — but the ability to see the world subtly.\n\n"
            "This works because you yourself live this way. You need people next to whom you yourself become smarter. And you recognize them right away — by speech tempo, by unexpected connections, by questions that wouldn't have occurred to you.\n\n"
            "People sometimes don't understand: \"but they look boring\". Boring-looking — for them. For you — a treasure trove you'll keep returning to for years.\n\n"
            "What's worth knowing: mind without emotional maturity is a dry place. There are very smart people, around whom there's emptiness for the heart. Learn to feel right away — does this mind have a warm part? If yes — protect them. If no — move on, however captivating it is to talk."),
        "Тебя цепляет дерзость": ("You're caught by audacity",
            "What lights you up is courage. When a person does what others don't dare. When they say what others think but are afraid to say. When they're first to step where others stomp.\n\n"
            "This works because you yourself have fire inside, and you need a person of the same scale. You're bored with the timid — they slow you down. With the audacious — you fly.\n\n"
            "People sometimes warn you: \"such people are unreliable\". And you know — reliability comes from those who've never risked. That's not reliability, that's inertia. You need a person whose risk is part of character, and at the same time who can carry responsibility for their decisions.\n\n"
            "What's worth knowing: audacity without maturity is just adrenaline, and it gets old quickly. Learn to tell courage with a goal from courage for the sake of sensations. The first leads somewhere. The second burns brightly and burns out fast. You need the first."),
        "Тебя успокаивает спокойствие": ("Calmness calms you",
            "What attracts you are the quiet ones. Those who don't fuss, don't panic, don't need constant attention. They have some anchor inside, and next to them you also become an anchor. This is a rare quality, and you recognize it right away.\n\n"
            "This works because your own life is already saturated. You don't need a partner who'll add storms to it. You need one who'll bring silence, and from this silence you'll be able to do what matters.\n\n"
            "People sometimes don't understand: \"they're boring\". This is a superficial view. Calmness isn't absence of depth, it's depth that doesn't need to be demonstrated.\n\n"
            "What's worth knowing: calmness sometimes masks detachment. There are quiet people because they just don't care. Learn to tell \"calm + involved\" from \"calm + cold\". The first — a treasure. The second — a trap in which you'll feel lonely even when nearby."),
        "Тебя зажигает лёгкость": ("Lightness lights you up",
            "What grabs you is laughter and play. When a person is funny not \"theatrically\", but really — sees absurdity where others miss it. When they can turn any heaviness into a joke without devaluing it.\n\n"
            "This works because you understood: life is short, and spending it in tension is a crime. You look for people next to whom you want to live, not survive. Creative, playful, adventurous — yours.\n\n"
            "People sometimes call you \"unserious\". You don't care. Seriousness isn't equal to quality of life. Many very serious people are deeply unhappy. Many light ones are deeply free.\n\n"
            "What's worth knowing: lightness is sometimes used as defense from intimacy. If a person responds to any serious topic with a joke, they're not free — they're hiding. Learn to tell real lightness from defensive. The first opens. The second closes behind a fun screen."),
        "Тебя интригует загадка": ("Mystery intrigues you",
            "What attracts you are those who can't be \"read\" at first glance. They have layers, and they don't rush to open them. For you this is a promise of a process that'll last for years. Simple and clear people quickly become boring.\n\n"
            "This works because you love not the result \"fully learned\", but the motion of learning. The ideal partner for you is a person with layers that open slowly. This turns every day into a small discovery.\n\n"
            "People sometimes say: \"you love the complicated, that's why you suffer\". This is superficial. You don't suffer from complexity — you grow from it.\n\n"
            "What's worth knowing: mystery comes in two kinds. The first — real depth worth exploring. The second — absence of content disguised as silence. Learn to tell. If in half a year the mystery doesn't open — there's nothing there. Move on."),
        "Тебя греет забота": ("Care warms you",
            "What grabs you is attention to small things. When a person remembers what you love, asks \"how are you?\" and listens to the answer, notices when you're tired. This isn't \"care for show\", this is a natural quality — they just see you.\n\n"
            "This is a rare quality in an era when everyone looks at their screens. When you find a person who really is present — that's another level of closeness. Not the quantity of shared hours, but the quality of attention in those hours.\n\n"
            "People sometimes don't understand: \"they don't do anything special\". And they do — the hardest thing: see. This is harder than giving gifts or saying loud words.\n\n"
            "What's worth knowing: care is a gift, but also a risk of tiring. If a person constantly \"cares for you\", you can start to feel they have no own life — it's all in you. Learn to feel healthy care (from fullness) from compensatory (from emptiness). The first enriches both. The second drains."),
        "Тебя притягивает свобода": ("Freedom attracts you",
            "What grabs you are the independent. Those who have their own life, their own projects, their own worlds — and you're not the center in them, but an interesting visitor. For you this is the most attractive.\n\n"
            "This works because you yourself are built this way. You need space — and a partner who won't eat this space. With clingy ones it's hard for you, however sweet they are.\n\n"
            "People sometimes don't understand: \"you don't need each other?\". We do, but not in a suffocating way. This is a rare model of relationships, and it requires two very whole people.\n\n"
            "What's worth knowing: independence sometimes turns into emotional distance. There are independent people next to whom you feel lonely, because they're so free they don't invest. Learn to tell \"free + involved\" from \"free + detached\". The first — your person. The second — your pain in a year."),
        "_default": ("You're caught by the ensemble",
            "You don't have one decisive factor of attraction. What matters to you is the combination: mind, calmness, care, and a bit of mystery. One trait doesn't close the question — a complete person is needed.\n\n"
            "This is both good and complicated. Good — because you won't be charmed by one trait. Complicated — because such complete people are few, and sometimes you wait for an ideal too long instead of seeing the wonderful in the real.\n\n"
            "People sometimes don't understand your selectivity. They think you \"want too much\". You don't want a lot — you want it whole.\n\n"
            "What's worth knowing: wholeness is your compass, hold it. But distinguish \"complete person\" from \"perfect\". Complete is with different facets, sometimes imperfect. Perfect is fantasy. Learn to tell. Otherwise you can pass by those who were for you — because they weren't flawless."),
    },
    "how_you_flirt": {
        "Через юмор": ("Through humor",
            "Your main tool is laughter. Memes as love letters, teasing, humor, unexpected playlists. You understand that making a person laugh is the most direct path to their heart. And you use this constantly.\n\n"
            "This works because you have a sharp sense of humor and quick reaction. You don't \"prepare jokes\"; they come on their own, and usually to the point. And from this a feeling is created that you're a lively person, interesting, with whom it's not boring.\n\n"
            "People sometimes don't understand it's flirting: \"they're just funny\". And you know — for you this is exactly the way to show interest. You're not \"just funny\", you're purposefully cheerful with those you like.\n\n"
            "What's worth knowing: humor as flirting works as long as the partner understands it. With a person who has a different sense of humor, your style just doesn't reach — they think you're superficial. Learn to feel the audience. And sometimes after long teasing worth saying something direct — so the partner doesn't write you off into the \"just a friend\" category."),
        "Через заботу": ("Through care",
            "Your flirting is attention to small things. You remember what a person loves. Ask if they ate. Make small gifts no one expects. Help when not asked. This is your way of saying \"you matter to me\" — not in words, but in action.\n\n"
            "This works because you have deep empathy. You notice what isn't obvious to others — that a person is tired, that they forgot to eat, that they're cold. And you react before they ask.\n\n"
            "People sometimes don't understand it's flirting: \"they're just a caring person\". And you know you don't care like this for everyone, but for specific ones. This is your selective attention, and it's your main signal.\n\n"
            "What's worth knowing: care as flirting works as long as the partner notices it. With an inattentive person, your care is taken for granted, and the signal doesn't reach. Learn to sometimes say aloud: \"I'm doing this because I like you\". Otherwise your language stays untranslated."),
        "Прямота": ("Directness",
            "You don't play riddles. If a person appeals to you, you say it aloud. Direct compliments, direct gaze, sometimes direct touch, direct invitation. You're bored playing yourself, and to the partner you offer real communication right away.\n\n"
            "This works because you have courage. Most people circle because they fear rejection. You understand rejection is part of life, and quick clarity is better than long uncertainty.\n\n"
            "People sometimes are surprised by you: \"you're fast\". Not fast — precise. I know what I want, and I see no point hiding it under layers of play.\n\n"
            "What's worth knowing: directness works with confident people. With shy ones you can scare them — they're used to subtle signals, and you're dumping the truth at once. Learn to regulate the tempo. Sometimes worth sending a subtle signal first, and only if it's not read — switching to direct."),
        "Намёки в сети": ("Hints online",
            "Your flirting is on social networks. Stories posted specifically for one. Likes on old photos. Reactions on each of their posts. Playlists that \"accidentally\" reflect what's between you. You lead a dance online before it transitions offline.\n\n"
            "This works because you understand modern communication. Today's flirting starts online — and often ends without reaching offline. You're a master of this stage, and can show interest without a word, through actions.\n\n"
            "People sometimes don't guess: \"they just sit on social networks actively\". Not just. Every move is thought through, every like purposeful.\n\n"
            "What's worth knowing: online flirting works at the start, but doesn't replace real meetings. If you're stuck at the \"likes and stories\" stage for months, most likely it's no longer flirting, it's a form of avoidance. Learn to transition offline before the algorithms eat all your potential."),
        "Тонкие касания": ("Subtle touches",
            "Your flirting is on the body level. Random touches. A gaze longer than necessary. Long silence side by side, in which you can hear something is between you. Compliments not in words, but in attentiveness.\n\n"
            "This works because you have a strong connection with the physical. You understand the body knows before the mind, and so you communicate on the body level with a person who understands this language.\n\n"
            "People sometimes don't guess: \"is something between you?\". Everything is between us. You just don't see, because there are no words.\n\n"
            "What's worth knowing: tactile flirting works with tactile people. With those who read text and words, your style just doesn't reach. Learn to tell. With the tactile — continue in this register. With the verbal — switch to words, otherwise they won't even guess."),
        "Игра загадок": ("Game of riddles",
            "Your flirting is in understatement. You post stories that may or may not have a hint. You like old photos — let them guess. You're silent nearby, and your gaze speaks. You prefer intrigue to direct statement.\n\n"
            "This works because you have a mystifier's instinct. You understand too obvious interest gets devalued; but unclear what's happening here — that holds a person in tension, and tension is the beginning of love.\n\n"
            "People sometimes accuse you: \"you're playing with people\". Not playing — dancing. Different things.\n\n"
            "What's worth knowing: a riddle works if a person can solve it. With a straightforward partner your intrigue just bounces off — they read nothing, and at some moment get tired and leave. Learn to tell. And remember: even the most complex dance ends with one of the partners taking an obvious step. Don't stay forever at the riddle stage."),
        "Через активность": ("Through activity",
            "You invite somewhere. Know interesting places. Help fix things, explain, give rides. Tease and ask to draw the person into conversation. Your flirting is in action, not in words.\n\n"
            "This works because you're an active person. Sitting and waiting for \"it to happen\" isn't yours. You create an occasion, and in this occasion something is already growing between you.\n\n"
            "People sometimes are surprised: \"you invited them on purpose?\". On purpose. So what? This isn't manipulation — it's initiative. You understand that without initiative nothing will happen.\n\n"
            "What's worth knowing: active flirting works with reactive people. If the partner is also active, you can have competition \"who'll invite who first\". Learn to alternate: sometimes you, sometimes them. Otherwise one of you always feels like a \"guest\", and the other — a \"host\", and over time this creates asymmetry."),
        "_default": ("Your own cocktail of flirting",
            "You don't have one signature move. With one person you tease, with another care, with a third speak directly, with a fourth play riddles. You adapt to each individually.\n\n"
            "This works because you have flexible feel for people. You understand flirting isn't \"I have one style and let them adjust\", but \"I speak in a language you understand\". And so you're more effective than those with a fixed approach.\n\n"
            "People sometimes can't classify you. With one — you're funny, with another — caring, with a third — direct. This isn't two-faced, these are different facets.\n\n"
            "What's worth knowing: flexibility works as long as it stays sincere. If you switch styles just to please, you lose your core. Learn to feel: am I flirting this way because it's close to me, or because I'm \"putting on\" the form needed for this person? The first — wonderful. The second — will end with you not knowing who you are."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch26.{ts}")
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
