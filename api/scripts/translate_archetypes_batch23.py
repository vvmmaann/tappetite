"""Archetype EN backfill — batch 23: Otnosheniya part 1 (romantic_archetype + dating_taste + relationship_values)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "romantic_archetype": {
        "Любишь словами": ("You love through words",
            "For you, love is voice. Words of compliments, long messages, late-night conversations about important things. When you say \"I love you\", that isn't a duty phrase — it's a specific gesture in a specific moment, and you wait for the same in return.\n\n"
            "This works because words for you are the most direct way to convey what's inside. Gestures can be misread, deeds can be wrongly interpreted, but words are concrete. So you say often and want to hear often.\n\n"
            "People sometimes are surprised: \"writing him again?\". And you don't understand how else. If a person matters, they need to be told. Now. And tomorrow. And in a year — also.\n\n"
            "What's worth knowing: a partner for whom words aren't the main thing can hear your love as \"too much\". They need other signals. Learn to say less and listen too. The scariest thing is when your speech becomes background, not gift. The value of words is that there are few of them."),
        "Любишь делами": ("You love through deeds",
            "For you, love is action. Words are cheap, deeds are honest. You won't say how strongly you love — you'll cook breakfast, fix a shelf, pick him up from work in the rain. That's love. Without announcement.\n\n"
            "This works because you understand: anyone can talk, few can do. And so your deeds weigh more than the most beautiful confessions. Love is measured by deeds, period.\n\n"
            "People sometimes don't read you right away. They need words. They wait for \"I love you\" while you're washing his car. It seems obvious to you, not to him. And this sometimes costs relationships.\n\n"
            "What's worth knowing: a partner who grew up on words may not understand for months that you love them. Learn to speak aloud at least occasionally. It's nothing terrible that for you it's \"extra\". For him it's what you don't show through deeds. Just translate to his language. Deeds + words isn't double work, it's the full set."),
        "Через прикосновение": ("Through touch",
            "For you, love is the body. Hugs, a hand on the back, head on the shoulder. Without it, a relationship for you is two people next to each other but not together. Touch is your main language, and without it you're physically unwell.\n\n"
            "This is deeply biological. Oxytocin is released through skin, not through words. So you literally can't feel a connection with a partner if it isn't there in physical contact. This isn't a whim; this is how your brain is built.\n\n"
            "People sometimes don't understand: \"you live together anyway\". And you understand that \"living together\" doesn't equal \"feeling together\". Without daily touches, you sense the partner as a roommate.\n\n"
            "What's worth knowing: not all partners are equally open to the physical. Some have their reasons (childhood, traumas, culture), and they need more time for trust. Learn to tell \"doesn't love\" from \"can't yet\". The first is reason to leave. The second is reason to be patient and tender."),
        "Слоу-бёрн": ("Slow burn",
            "You love slowly. Not \"don't love\" and not \"cautiously\" — but at the right speed. You need time to truly open up, and you wait for the same tempo from a partner. Storms from the first night aren't for you.\n\n"
            "You understood that a deep connection isn't built in a week. First — friends, then close friends, then something more. Each stage has its right to be lived through fully, without skipping.\n\n"
            "People sometimes push: \"so when are you finally together?\". And you've been together for a long time — just not in the form they're used to. Your relationship isn't a status, it's a process.\n\n"
            "What's worth knowing: slow burn is wonderful, but requires a partner of the same tempo. If the other person lives at lightning speed, your slowness reads as coldness. Learn to voice your rhythm from the start: \"I'm slow, I like it that way, check — is it comfortable for you?\". This saves from mutual misunderstanding."),
        "Авантюрист в любви": ("Adventurer in love",
            "For you, love is a shared adventure. Trips, risks, the new together. You don't understand people who \"sit at home and watch a series every evening\" — because for you love requires movement, discoveries, shared stories to tell in 30 years.\n\n"
            "You understood that relationships die from routine faster than from anything else. And so in your relationships there should be no routine. Every few months — something new, unexpected, requiring you to be on the edge.\n\n"
            "People sometimes get tired looking at your plans: \"are you going somewhere again?\". They don't understand that for you \"not going\" isn't \"resting\", it's \"dying\".\n\n"
            "What's worth knowing: adventure requires energy and money. If a partner has less of either, they'll feel bad in your life — even if they agree to everything. Learn to alternate big adventures with quiet pauses. Otherwise your love becomes physically unbearable for most people."),
        "Дом и ритуалы": ("Home and rituals",
            "For you, love is small traditions. The morning coffee you make for him, and he for you — taking turns. Sunday runs. The same series you rewatch once a year. This isn't boring — this is love.\n\n"
            "You understood that relationships hold on repeats. Big moments happen once a year, and small ones — every day. And exactly in these daily small things lies the real fabric of love, not in solemn occasions.\n\n"
            "People sometimes call this \"petty bourgeois\". You don't care. You know that when you're 70, you won't remember the wedding toast, but how the two of you drank tea in the mornings for 40 years in a row.\n\n"
            "What's worth knowing: rituals are strength, but also a risk. They can become a prison if they stop bringing joy. Once a year review: which of our traditions are still dear to us, and which are just habit? Don't be afraid to let go of the outdated. The best traditions are those you return to with anticipation, not by inertia."),
        "Свобода в паре": ("Freedom in the pair",
            "You love without merging. You should have separate worlds: his friends, her hobby, your trips alone. And this doesn't mean you're not together — it means both of you exist outside \"we\". And exactly because of this, the \"we\" is strong.\n\n"
            "You understood the paradox: the less you try to hold a partner, the tighter they hold on. Freedom gives space for each to grow, and so you're with a person who keeps becoming more interesting, not shrinking under your supervision.\n\n"
            "People sometimes don't believe. \"What — he went away for a month alone, and you're calm?\". Calm. Because you're not the kind who measures love by hours spent together.\n\n"
            "What's worth knowing: freedom in a pair requires two very whole people. If one of you has attachment anxiety, your style can destroy them. Learn to feel the boundary: where is healthy freedom, and where are you just distancing. Freedom isn't equal to absence of care. Freedom is \"I trust you and don't control\", but this needs to be shown through deeds, not only theory."),
        "_default": ("Your own love cocktail",
            "You don't have one signature love language. You mix: sometimes you say, sometimes you do, sometimes you hug, sometimes you give an unexpected gift. This isn't indecision — it's understanding that different moments require different expressions.\n\n"
            "Most people live in one language: either \"I do everything with words\" or \"I do everything with gifts\". You're more flexible. This gives you a huge advantage: different partners read different things, and you adjust.\n\n"
            "People — especially the partner themselves — sometimes can't predict what you'll be like today. This is confusing, but also makes things interesting.\n\n"
            "What's worth knowing: flexibility works as long as it stays sincere. If you switch the love language by the partner's \"mood\", you stop being yourself. Learn to feel: am I in this style now because I want it that way, or because it's expected of me? The first — healthy adaptation. The second — losing yourself in others' expectations."),
    },
    "dating_taste": {
        "Падаешь от ума": ("You fall for the mind",
            "What grabs you is the head. Not appearance, not status, not ability to joke beautifully — but how a person thinks. When depth is visible in the interlocutor, you hear it immediately: it's a different speech tempo, different questions, a different ability to hold the complex.\n\n"
            "You understand appearance will change, wit gets old, and the mind remains. With a person who has a head, you won't be bored in a year, in five, in twenty. This is an investment, not a flash.\n\n"
            "People sometimes don't understand your selectivity. \"He's handsome\" isn't an argument for you. \"She's successful\" — also. You wait for something more subtle. And this is sometimes long.\n\n"
            "What's worth knowing: mind without warmth is a dry place. There are very smart people, around whom it's cold. Learn to feel right away whether there's a heart behind the intellect. If yes — protect them. If not — move on, however interesting it is to talk."),
        "Драйв и искра": ("Drive and spark",
            "What grabs you is energy. When a person walks into a room, and it comes alive. When they speak — you want to listen. When they look — it gets hot. You don't confuse this with loudness; we're talking about the inner spark visible right away.\n\n"
            "This works because you yourself are a lively person. You need a partner of the same level — otherwise you'll quickly get bored and start dragging the relationship yourself. And you don't want to drag — you want to walk together.\n\n"
            "People sometimes envy you. Your relationships, when you're in them, look like cinema: emotions, passion, nothing gray. But they don't see that a gray day next to a sparkling partner can be unbearably hard.\n\n"
            "What's worth knowing: fire requires fuel and burns through it quickly. The brightest relationships often end with an explosion, not a sunset. Learn to tell \"a spark because of chemistry\" from \"a spark because the person really is like that\". The first — brief. The second — forever."),
        "Тёплый дом": ("Warm home",
            "What grabs you isn't flashes, but warmth. When with a person it's quiet and good, no need to talk, no need to prove. Just nearby. For you this is the main sign of \"yours\". Didn't ignite, didn't catch fire, but warmed.\n\n"
            "You understand passion comes and goes, but the ability to make it cozy nearby is a rare skill, and it shows the maturity of a person. Those who can create warmth have usually gone through the cold and now value what they have.\n\n"
            "People sometimes don't understand why you choose \"the quiet ones\". They seem boring to them. To you — calm. These are two different things, and you've long distinguished them.\n\n"
            "What's worth knowing: warmth sometimes gets confused with passivity. There are quiet people because nothing is happening inside. Learn to feel the difference between \"quiet because deep\" and \"quiet because empty\". The first — a treasure. The second — will weigh on you in a year."),
        "Стильная амбиция": ("Stylish ambition",
            "What grabs you is the combination: taste + goal. When a person has both aesthetics (how they're dressed, what they listen to, where they live) and direction (knows what they want, where they're going). One without the other isn't enough for you — appearance without essence or goal without form looks incomplete.\n\n"
            "This is because you yourself live this way. It matters to you that the external reflects the internal. So a partner for you isn't just a person, but a wholeness visible from the first meeting.\n\n"
            "People sometimes reproach you for \"snobbery\". And this isn't snobbery — it's demandingness. You're not better than others; you just don't compromise where others do.\n\n"
            "What's worth knowing: external wholeness is sometimes deceptive. There are very stylish and very ambitious people who are empty inside. Learn to look deeper than first impressions. Style is a tool. Ambition is direction. But what a person does with these tools is another question, and it takes more time."),
        "Загадка и открытие": ("Mystery and discovery",
            "What grabs you is what isn't immediately understood. When a person doesn't lay everything out at the first meeting, leaves things unsaid, you have a desire to learn more. Simple and clear people quickly become boring to you.\n\n"
            "This is a form of love for the process. You love not the result \"fully learned\", but the very motion of learning. So your ideal partner is a person with layers that open over years.\n\n"
            "People sometimes tease you: \"you love complicated people, that's why you suffer\". This is a superficial reading. You don't suffer from complexity — you grow from it. The simple puts you to sleep.\n\n"
            "What's worth knowing: mystery comes in two kinds. The first — real depth worth exploring. The second — absence of content, disguised as silence. Learn to tell from the first months. If in half a year the mystery doesn't open even an inch — there's nothing there. Move on."),
        "Лёгкость в воздухе": ("Lightness in the air",
            "What grabs you is lightness. When with a person you don't have to strain to \"build a relationship\", when laughter comes on its own, when there's no heaviness of \"need to discuss serious topics\". This doesn't mean superficial — it means the serious happens on its own, without effort.\n\n"
            "You understand a relationship is mostly days, not moments. And if every day requires tension, the relationship won't survive. So you look for the one with whom days are light by themselves.\n\n"
            "People sometimes call you \"unserious\". And you just understood seriousness isn't in puffing cheeks. Seriousness is in making the partner happy every day. And often this is done through a joke, through a warm touch, through a light glance.\n\n"
            "What's worth knowing: lightness should be mutual. If you're light and the partner is heavy, your lightness for them looks like \"don't take me seriously\". Learn to adapt: sometimes you need to become heavier so the partner doesn't feel like a lonely drama in your frivolous life."),
        "_default": ("You're caught by the totality",
            "You don't have one decisive factor. What catches you is the ensemble: mind, warmth, ambition, and lightness. One trait won't close the question — a complete person is needed.\n\n"
            "This is both good and complicated. Good — because you won't be charmed by a single trait and miss toxicity behind its facade. Complicated — because such complete people are few, and sometimes you wait for the ideal too long instead of seeing the wonderful in the real.\n\n"
            "People sometimes don't understand your selectivity. They think you \"want too much\". You don't want a lot — you want it whole. Different things.\n\n"
            "What's worth knowing: wholeness is your compass, hold it. But distinguish \"complete person\" from \"perfect\". Complete — with different facets, sometimes imperfect. Perfect — fantasy. Learn to tell them apart. Otherwise you can pass by those who were for you — because they weren't flawless."),
    },
    "relationship_values": {
        "Фундамент доверия": ("Foundation of trust",
            "For you, relationships start with trust and end with it. Trust, honesty, faithfulness, unconditional acceptance — these aren't a \"pleasant bonus\", these are the base without which the rest has no meaning. Fire, romance, common goals — all bonuses on top of the foundation, not substitutes for it.\n\n"
            "This works because you have a clear understanding of hierarchy. Many people confuse strong passion with strong relationships. You know passion fades, and trust is the only thing that withstands time.\n\n"
            "People sometimes call you \"too serious in relationships\". You're not serious — you're foundational. Different things. You understand a relationship is the infrastructure of life, and infrastructure must withstand the load.\n\n"
            "What's worth knowing: foundation matters, but without fire the building is cold. If you focus on reliability so much you forget about passion and play, the relationship becomes a partnership without pleasure. Learn to add lightness and risk sometimes. Trust is the floor, not the whole room."),
        "Тёплая забота": ("Warm care",
            "For you, love is small gestures. Coffee in the morning, a blanket in the evening, being there when it hurts. Not loud confessions, not beautiful dates — but everyday soft care. This is your main love language.\n\n"
            "This works because you understand: relationships are mostly days, not moments. And in these days care matters more than beauty. A partner who remembers your small things is more valuable than one who gives a huge bouquet once a year.\n\n"
            "People sometimes say \"you have too warm a notion of relationships\". Not too warm. Others just haven't yet understood that the warm is the real. You understood earlier.\n\n"
            "What's worth knowing: care is the most underrated love language. But it can be taken to suffocation. If you constantly \"care\" for the partner, not letting them be self-sufficient, care becomes control in soft wrapping. Learn to tell. Real care gives strength; compensatory care takes it."),
        "Свобода в паре": ("Freedom in the pair",
            "For you, relationships are two independent people who chose to be together. Freedom, personal space, respect for difference, growth of each — that's your set. Without it you suffocate, and the partner knows.\n\n"
            "This works because you understood the paradox: the less you try to hold the partner, the tighter they hold on. Freedom gives space for each to grow, and so you have a relationship with a person who keeps becoming more interesting, not shrinking under your supervision.\n\n"
            "People sometimes don't believe: \"what — he went away for a month alone, and you're calm?\". Calm. Because you're not the kind who measures love by hours spent together.\n\n"
            "What's worth knowing: freedom in a pair requires two very whole people. If one of you has attachment anxiety, your style can destroy them. Learn to feel the boundary: where is healthy freedom, and where are you just distancing. Freedom isn't equal to absence of care. Freedom is \"I trust you and don't control\", but this needs to be shown through deeds."),
        "Огонь и приключение": ("Fire and adventure",
            "For you, relationships are motion. Passion, shared adventures, humor every day, constant growth. If a relationship has become routine — that's an alarm signal, not comfort. You don't seek a \"calm harbor\"; you seek a ship on which you sail further.\n\n"
            "This works because you have high inner liveliness. You need a partner of the same tempo — otherwise you'll quickly get bored and start feeling that your life is going on without you.\n\n"
            "People sometimes envy you, sometimes get tired. Envy — your energy. Tired — because you set a high bar of tempo, and not everyone can keep up.\n\n"
            "What's worth knowing: fire requires fuel and burns through it quickly. The brightest relationships often end with an explosion, not a sunset. Learn to tell \"the rhythm of a couple\" from \"a constant race\". The first — healthy motion. The second — no one withstands long. Sometimes relationships also need quiet days so there's energy for adventure again."),
        "Стабильный якорь": ("Stable anchor",
            "For you, relationships are a place where you can exhale. Stability, faithfulness, support, trust — your supports. You don't love the swings of \"now we love, now we fight\". You need even warmth that you can rely on.\n\n"
            "This works because you have enough events outside the relationship: work, friends, projects, concerns. You don't need additional shocks from the partner. You need a quiet harbor — and you build it consciously.\n\n"
            "People sometimes call this \"boring\". Not boring — sustainable. Different categories. Boring is when nothing happens. Sustainable is when the main thing happens, and around it there's no chaos.\n\n"
            "What's worth knowing: stability as an ideal — wonderful. Stability as fear of any change — a prison. Learn to tell. If you avoid any changes in the relationship from fear \"everything will fall apart\", you freeze healthy development. The anchor is needed so the ship isn't carried away, not so it doesn't move."),
        "Команда с курсом": ("Team with a course",
            "For you, relationships are a union with a common mission. Common goals, shared growth, support along the way, common adventures. You don't \"just love\" — you build something with a person, and this common construction is the main thing for you.\n\n"
            "This works because you have a strong sense of direction. It's hard for you to be with someone who lives \"as it goes\". You need a partner who's also moving somewhere, and then your motion merges into one.\n\n"
            "People sometimes are surprised: \"you're like a business project\". Yeah, in some sense. Just a 50-year project, and the product is shared life.\n\n"
            "What's worth knowing: \"team with a course\" is a powerful model, but it forgets about feelings. If you focus too much on \"where we're going\", you can miss that the partner is tired, that something inside is off. Learn to alternate strategic conversations with just-conversations. The course matters, but not more than the live people on the team."),
        "Лёгкий вайб": ("Light vibe",
            "For you, relationships are lightness. Humor every day, quiet closeness without words, freedom to be yourself, passion when it's there. You don't need to \"decide\", \"build\", \"invest in the relationship\". You want them to happen on their own, like good weather.\n\n"
            "This works because you have no anxiety in relationships. Many people constantly \"work on the relationship\". You just live with the person, and that's already work in itself. Additional isn't needed.\n\n"
            "People sometimes don't understand: \"what about serious conversations?\". You shrug. Serious conversations happen on their own when there's a need. Forcing them is creating a problem to solve.\n\n"
            "What's worth knowing: lightness works with a similar partner. If the other person lives in a more serious mode, your lightness for them is \"don't take me seriously\". Learn to read the partner. Sometimes worth turning on seriousness, even if it's not your native register. Not for life — for a specific moment when it matters to the other."),
        "_default": ("Your own mix of values",
            "You don't have one main value in relationships. What matters to you is both stability and freedom; both passion and care; both common goals and personal space. You understand mature relationships hold not on one thread, but on a network of many.\n\n"
            "This is rare. Most people pick one axis as \"the main\" and underestimate the rest. You understood this is a simplification, and work with the full palette.\n\n"
            "People sometimes are surprised: \"you have no priorities?\". I do. There are just many of them, and they balance each other. This isn't absence of priorities — this is a system.\n\n"
            "What's worth knowing: a wide set of values is your wealth, but sometimes prevents choosing. In a critical moment a partner can ask: \"what matters more to you — freedom or stability?\" — and you'll freeze. Learn to understand which values are core for you and which can shift. Without this hierarchy in crises you'll thrash."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch23.{ts}")
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
