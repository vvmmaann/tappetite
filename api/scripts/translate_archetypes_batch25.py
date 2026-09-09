"""Archetype EN backfill — batch 25: Otnosheniya part 3 (first_move + relationship_persona + green_flag_others)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "first_move": {
        "Прямое заявление": ("Direct statement",
            "You prefer directness. Write first in DM. Say aloud \"I like you\". No hints, no theater, no \"try and guess\". It's easier for you, and you believe it's also more respectful to the partner than a week of riddles.\n\n"
            "This works because you have courage. Most people circle around because they fear rejection. You understand rejection is a normal part of life, and a quick refusal is better than dragged-out uncertainty.\n\n"
            "People sometimes are surprised: \"you're bold\". Not bold — honest. Different things. Boldness is breaking norms; honesty is just absence of games.\n\n"
            "What's worth knowing: directness works in environments that value it. With a person used to subtle signals, your \"I like you\" can sound \"too fast\". Learn to feel the partner. Sometimes worth starting with the subtle, and only if they don't read — switching to direct."),
        "Тонкие сигналы": ("Subtle signals",
            "You prefer subtle. Look longer in the eyes. Like on social networks. Gradual flirting waiting for a return reaction. It matters to you that interest grows slowly, and each step is confirmed by the partner's response.\n\n"
            "This works because you have a sense of rhythm. You understand attraction is a dance, and in a dance both should move. If you take too big a step — the partner gets lost. If they don't take theirs — the dance stops.\n\n"
            "People sometimes don't understand your slowness: \"say something already!\". And you're not silent — you're talking, just in another language. Whoever can read — hears. Whoever can't — well, not my fault.\n\n"
            "What's worth knowing: subtle signals can pass by those who aren't used to them. And then you get offended \"they didn't notice\", while the partner sincerely understood nothing. Learn to feel who's in front of you. With the subtle — play subtly. With the direct — switch to the direct. Otherwise your style breaks against their deafness."),
        "Окольные пути": ("Roundabout ways",
            "You prefer roundabout maneuvers. A hint through mutual friends. A like on social networks. To call together under a neutral pretext — like \"just coffee\". This gives you the chance to retreat if interest isn't mutual, without losing face.\n\n"
            "This works because you have a careful relation to your own ego. A direct rejection for you is a blow you're not ready to take without preparation. Roundabout ways give the chance for everything to happen \"as if by chance\", and to preserve dignity.\n\n"
            "People sometimes tease you: \"you're like in school\". And what's wrong with the school approach? It works. Just it's not about boldness — it's about diplomacy.\n\n"
            "What's worth knowing: roundabout ways work with people who can read them. With straightforward ones, your \"neutral pretext\" sounds literal, and you won't get the answer you need. Learn to feel the partner. Sometimes after two-three roundabouts worth saying aloud — otherwise you're losing time on a game the other isn't playing."),
        "Создать ситуацию": ("Create the situation",
            "You don't \"make a step\" — you create a situation. Invite together, arrange for you both to be alone, start flirting gradually. Not \"declaring\" interest, but building an environment in which interest can show itself.\n\n"
            "This works because you have a strategic mind. You understand direct steps scare, and an environment doesn't. If a person ends up with you in the right place at the right time, much of what comes next happens on its own.\n\n"
            "People sometimes are surprised by your cunning: \"you thought it all through\". Yeah. This isn't manipulation — it's organization. You don't force — you provide an opportunity.\n\n"
            "What's worth knowing: \"creating a situation\" works on confident people. With unconfident ones — your plan will collapse, because they won't take a step even in a perfect situation. Learn to feel the partner. If they don't take a step even in the environment you created, the matter isn't in the environment, it's in their state. And worth either saying directly or letting go."),
        "Жду шаг другого": ("Waiting for the other's step",
            "You prefer the partner to make the first step. Let them feel that you're also interested — a glance, a smile, openness — but the decision should come from them. For you that's a sign of sincere interest; if a person really wants, they'll overcome the fear.\n\n"
            "This works because you have self-respect. You understand: chasing a person isn't love, it's anxiety. And you don't want to start a relationship with this. Better wait and get a normal step than beg for attention.\n\n"
            "People sometimes pity you: \"you'll never be liked, you have to act\". I do act — with a glance, a smile, openness. I just leave the final step to the other, and it works more often than it seems.\n\n"
            "What's worth knowing: waiting works with confident people. With shy ones you'll wait forever, because they'll never take a step themselves. Learn to feel. If you clearly appeal to a shy person, sometimes worth giving them a very-very small but clear signal — like \"you can write first, I'm not against\". Micro-permission works wonders."),
        "_default": ("Adaptive step",
            "You don't have one signature method. With one person you're direct, with another subtle, with a third you wait for their step. Depends on the vibe, situation, your feeling.\n\n"
            "This works because you have flexibility. Most people live in one mode and apply it to everyone — hence the misses. You choose for the person.\n\n"
            "People sometimes can't predict how you'll approach a specific person. And that's normal — you don't know yourself until you meet.\n\n"
            "What's worth knowing: adaptability is good as long as it stays sincere. If you \"choose an approach\" just to please, you lose yourself trying to accommodate. Learn to tell — am I adjusting because I want to honestly meet this person, or because I'm afraid my usual form won't fit? The first — wonderful. The second — losing in the starting position."),
    },
    "relationship_persona": {
        "Сердце нараспашку": ("Heart wide open",
            "You love so it's visible in the room. Romance, care, demonstrativeness — you have no \"feelings in reserve\". If you've chosen someone, that person knows about it every day, in a post, in a gift, in a letter, in an unexpected hug.\n\n"
            "This isn't \"theater\". This is your honesty: a feeling can't be kept inside, it requires an outlet. Letters, flowers, joint photos on social networks, declaring love in front of others — these aren't poses, this is your \"I'm here, and I'm with you\".\n\n"
            "People sometimes tease you: \"too much, calmer\". You don't understand — why calmer? Life is short, the person nearby is the only guarantee of happiness. If you can show, you should show.\n\n"
            "What's worth knowing: intensity is beautiful, but requires a partner who accepts it. If the person nearby is more closed, your demonstrativeness can overload them — they'll feel they don't \"answer\" enough. Learn to feel the other's tempo. Love isn't a marathon of loudness, it's a shared rhythm."),
        "Спокойный фон": ("Calm background",
            "You're an even person in a relationship. You don't disturb, don't push, don't demand constant proof. The partner near you seems to exhale — next to you life doesn't storm. This is a rare and valuable quality.\n\n"
            "You don't need constant drama to be sure of love. You understand a relationship isn't a fire, but the temperature of a room. The main thing is that it's warm, not that something explodes every day.\n\n"
            "People sometimes think you're \"not very involved\". This is a misperception. You're deeply involved, just not loudly. For you, love is reliability, not a show.\n\n"
            "What's worth knowing: calmness is your gift to the partner, but sometimes they need confirmations you consider \"extra\". Not everyone can read your silence as love. Sometimes worth saying aloud: \"I'm happy you're with me\". Words don't cancel silence — they amplify it."),
        "Тревожная привязанность": ("Anxious attachment",
            "You love strongly — and this sometimes scares you. You re-check messages, look for confirmations, see signs where there might be none. Not because you're paranoid, but because love for you is too important a thing to relate to it relaxedly.\n\n"
            "This often roots in childhood — somewhere inside sits the knowledge that good can end, and so you constantly need to check whether everything is still good. This isn't weakness. This is the heart's vigilance.\n\n"
            "People sometimes perceive this as jealousy or pressure. Actually it's fear of losing what you value most. The partner with you can be both warm and heavy at the same time — because you love intensely and sometimes anxiously.\n\n"
            "What's worth knowing: your anxiety is real. But it isn't always the truth. Learn to tell \"I'm scared\" from \"there's a real threat\". These are two different things, and they require different reactions. And remember: a partner who really loves you gives calm through deeds, not words. Learn to trust deeds."),
        "Лёгкость во плоти": ("Lightness in the flesh",
            "You love without suffocating. The partner for you isn't \"the other half\" with philosophical undertones, but a cool person with whom it's fun and you don't have to report where you are, what you are, with whom. Freedom for you is a mandatory condition of love, not its opposite.\n\n"
            "This works because you love not from deficit. You don't need a partner to \"close emptiness\" — you don't have any. You choose them because you want to, not because you're scared alone.\n\n"
            "People sometimes read this as \"not serious enough\". This is a superficial view. Seriousness isn't equal to non-freedom. You can be devoted and at the same time not hang on the partner — this is a rare and mature mix.\n\n"
            "What's worth knowing: lightness is a talent, but sometimes the other person perceives it as detachment. They might think you \"aren't investing\". Learn to show involvement in ways your partner reads. Freedom is your value; make sure it's a value for two."),
        "Тихая глубина": ("Quiet depth",
            "You're not the kind who opens up at the first meeting. You need time, trust, a reason — and then you start showing the real self. Until then you're polite, warm, but behind a wall. Not everyone sees this wall; those who see don't always find the door.\n\n"
            "This isn't fear of intimacy. This is respect for yourself and the interlocutor: you don't scatter what's inside. What's valuable deserves careful transfer. So your love is slow, but deep.\n\n"
            "People sometimes don't guess how deeply you love. Outside you have an even mask. Inside — storms, tenderness, fears, hopes. The one you opened to gets a huge world that very few know exists.\n\n"
            "What's worth knowing: your closedness is defense, and it works. But if there's too much of it, even the one you trust may never understand the scale of what you feel for them. Sometimes worth taking small steps outward — not to break the wall, but to open the door more often than you're used to."),
        "Опора": ("The support",
            "You're the one who can be relied on in a relationship. Partner is sick — you're there. Partner feels bad — you're there. Partner yells at you for no reason — you're there, waiting until it passes, and not leaving. This is a rare type in an era when people scatter from the first inconvenience.\n\n"
            "This isn't from self-sacrifice. This is from understanding that a close person is the only thing that has meaning. Career, success, status — all temporary. But \"being there when needed\" is love, not in words but in deeds.\n\n"
            "People sometimes underestimate you. Support is noticed only when it disappears. A partner can receive your care for years and consider it background — until one day they wonder: \"can I be like this?\".\n\n"
            "What's worth knowing: being the support is wonderful, but the support also needs support. Don't turn the relationship into a one-way street. Learn to ask for support, give the partner a chance to be for you what you are for them. Otherwise over time imperceptible fatigue accumulates."),
        "Контролёр в любви": ("Controller in love",
            "You love strongly — and so you want to know everything. Where the partner is, with whom, what they feel, what they plan. Not from distrust of them specifically, but because uncertainty in a relationship is too anxious for you.\n\n"
            "This often comes from responsibility: you believe relationships require management like a project. If something goes wrong, better learn earlier and fix. So you keep your hand on the pulse.\n\n"
            "People — especially the partner — sometimes feel you know too much and decide too much. They may seem to have less freedom than they'd like. This isn't always so — but perception matters more than fact.\n\n"
            "What's worth knowing: control and love aren't synonyms, though they often go together. The more you try to hold, the more the partner may try to break free. The paradoxical rule: the less you control, the less the partner wants to do something secretly. Learn to let go in small things — this strengthens in big."),
        "_default": ("Your own format",
            "Your style in relationships doesn't fit one type. You combine — you can be both a romantic and calm; both caring and free; both open and closed depending on the partner, moment, mood. This isn't messiness — this is adaptability.\n\n"
            "Most people live on one note: either eternal romantic, or eternal rationalist. You hear what's needed from you now and adjust the register. This is a rare and valuable skill.\n\n"
            "People find you hard to understand the first time. The partner can think you're one type, and it turns out — another. You yourself are sometimes surprised how quickly you change inside the relationship.\n\n"
            "What's worth knowing: flexibility works as long as you stay honest with yourself. If you adjust \"just so there's no conflict\", you lose your face. Adaptability is good when you choose the register, not when the register chooses you. Regularly ask: am I now flexible or dissolved?"),
    },
    "green_flag_others": {
        "Влюбляешься в честность": ("You fall for honesty",
            "What grabs you is when a person says the truth to your face — even uncomfortable, even about you. This is a rare trait in an era where everyone knows how to package words, and you value it above beauty, wit, or status.\n\n"
            "This isn't masochism. This is understanding: with a person who can speak truth, you always know where you stand. No need to guess, no need to decode hints, no need to worry about hidden meanings. This is a huge saving of your inner resources.\n\n"
            "It matters to you that a person keeps promises and holds their word — because a word you can lean on is such a rarity in the modern world that it turns into a luxury. Reliability for you is a form of love.\n\n"
            "What's worth knowing: your love for honesty sometimes works against you. Not everyone can tell honesty from rudeness. Learn to feel the difference between when truth is told from love, and when from self-aggrandizement. The first — your green flag. The second — boorishness disguised as directness. Don't confuse them."),
        "Падаешь от ума": ("You fall for intelligence",
            "What turns you on is thought. When a person speaks interestingly — tells about something with depth, sees connections, asks questions you didn't think to ask — something inside you responds. Appearance, status, humor without intellect don't catch you.\n\n"
            "This is a form of hunger: all your life you need people next to whom you yourself become smarter. Not teachers, not gurus — just equal interlocutors with whom an hour-and-a-half conversation feels like a minute. This is a rare feeling, and you recognize it immediately.\n\n"
            "Curiosity also turns you on — when a person is interested in the world, asks questions, climbs into topics they don't understand. This is the opposite of one who has \"already understood everything\". With such a person you want to go somewhere else.\n\n"
            "What's worth knowing: intellect without empathy is a dry place. There are very smart people with whom you'll be interested talking for half a year — and empty all the other six months. Learn to feel right away whether there's a warm part behind the mind. If yes — protect them. If no — move on, however interesting it is to talk."),
        "Ценишь спокойных": ("You value the calm",
            "What attracts you are people who don't panic. When there's noise around, crisis, everyone has a fire in their hair — and they calmly decide what to do. Not because they don't care, but because they have a stable nervous system.\n\n"
            "For you this is a sign of maturity. Most adults inside remain children who get lost in stress. And ones like this — withstood something in the past, and now any new stress seems to them less than the past. This is desperately calming.\n\n"
            "Empathy in such a person usually exists too — because a person who's gone through their own feels another's deeper. You see they're not just strong, but warm. This is a rare combination, and you value it.\n\n"
            "What's worth knowing: calmness sometimes masks detachment. Not everyone who \"doesn't panic\" is truly involved. It happens that a person seems calm because they just don't care. Learn to tell \"calm + involved\" from \"calm + detached\". The first — a treasure. The second — coldness."),
        "Тебе нужны амбициозные": ("You need the ambitious",
            "What turns you on are people who know what they want. Not \"wherever it carries\", but \"here's my goal, I'm going to it\". They can be wrong, can change course, but there's always direction, and in this direction they move.\n\n"
            "For you this is a sign of an inner core. Most people live reactively: what happened is what they did. And with such — you feel they're authors of their life, not passengers. And this inspires — because next to an author you yourself become more author, less passenger.\n\n"
            "Hobbies and passions also catch you — when a person really burns about something, not for a checkmark in a questionnaire, but because they can't otherwise. With such people there's always something to talk about, and they're never empty.\n\n"
            "What's worth knowing: ambition without empathy turns into selfishness. There are very purposeful people for whom you're background or a step. Learn to tell ambition next to which you grow from ambition that uses you. The first inspires. The second drains."),
        "Заботливое сердце": ("Caring heart",
            "What grabs you is when a person values close people more than career. When it's visible they care for mom, remember friends' birthdays, refuse a work meeting for a sick child. This isn't sentimentality — these are correctly arranged priorities.\n\n"
            "In a world where it's accepted to brag about deeds and achievements, care for the close is quiet. They don't write about it on LinkedIn. And exactly because of this, when you notice it, it weighs more than any status.\n\n"
            "Empathy in such a person is usually deep — they feel what another needs, without words. With them you're safe, because they notice when you're feeling bad, even before you understand it yourself.\n\n"
            "What's worth knowing: care for the close sometimes becomes a way to avoid one's own life. There are people so busy helping everyone they forget themselves. This isn't a green flag — it's burning out. Learn to tell healthy care from compensatory. Healthy gives strength; compensatory pulls it out."),
        "Самоирония — твоё всё": ("Self-irony is everything",
            "What grabs you is when a person can laugh at themselves. Not self-deprecatingly, but lightly: \"yeah, I'm funny in this, so what\". For you this is a sign of inner freedom. A person who doesn't cling to their image is always more interesting than one holding it with all their might.\n\n"
            "Humor for you is a separate depth. Not just \"makes me laugh well\" — but sees the funny in the ordinary, notices absurdity where others miss it. This is another level of attention to life, and it's very rare.\n\n"
            "When a person has both humor and self-irony, it's impossible to be tense next to them. Any of your mistakes stops being a catastrophe; any silliness turns into a shared joke. This is very healing for relationships.\n\n"
            "What's worth knowing: sometimes humor is used as defense from intimacy. If a person responds to any serious question with a joke, they're not free — they're hiding. Learn to feel when humor is play and when it's a wall. The first brings closer. The second separates, under a beautiful shell."),
        "_default": ("You're caught by the totality",
            "You don't have one signature green flag you fall for right away. What matters to you is the totality: that the person be honest, smart, warm, with taste. One trait won't close the question — an ensemble is needed.\n\n"
            "This is both good and complicated. Good — because you won't be charmed by one trait and miss toxicity behind its facade. Complicated — because such complete people are few, and sometimes you wait for an ideal too long instead of seeing the wonderful in the real.\n\n"
            "People sometimes don't understand your selectivity. They think you \"want too much\". You don't want a lot — you want it whole. Different things.\n\n"
            "What's worth knowing: wholeness is your compass, hold it. But distinguish \"complete person\" from \"perfect\". Complete is with different facets, sometimes imperfect. Perfect is a fantasy that doesn't exist. Learn to tell. Otherwise you can pass by those who were for you — because they weren't flawless."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch25.{ts}")
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
