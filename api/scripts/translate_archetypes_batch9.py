"""Archetype EN backfill — batch 9: Character (5 cats, ~37 archetypes)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "core_values": {
        "Природный авантюрист": ("Natural adventurer",
            "Cages, schedules, and \"the way it's done\" enrage you. You live as if you owe nothing to anyone tomorrow."),
        "Хранитель очага": ("Hearth-keeper",
            "You build, maintain, defend. Systems and rituals are love in action, not boredom."),
        "Мыслитель-аналитик": ("Thinker-analyst",
            "You don't trade clarity. Better an awkward conversation today than a beautiful illusion for weeks."),
        "Эмпат-чувствительный": ("Sensitive empath",
            "You catch what others don't say, and weigh your words. That's not weakness — it's your superpower."),
        "Профессионал-одиночка": ("Solitary professional",
            "You value your space, and work is your main language. Your best work happens without witnesses."),
        "_default": ("Inner balance",
            "You don't have one dominant value — you hold several in equilibrium, and that's rare."),
    },
    "red_flag": {
        "Призрак": ("Ghost",
            "When things get hard, you disappear. Don't reply right away, can vanish for a day, a week, a month — then resurface as if nothing happened. Not malice; your main defense mechanism. If you can't handle it — you exit contact.\n\n"
            "It works in the moment: you feel relief. No need to explain, invest, feel anything uncomfortable. Just a pause.\n\n"
            "People around pay a high price. They sit in unknowing, invent explanations, feel unwanted. You don't see this because at the moment of disappearing you're physically out of their reality.\n\n"
            "What's worth knowing: ghosting is a temporary fix that destroys trust over time. Even one line — \"I need a break, will be back in a week\" — changes everything. Silence reads as abandonment; even a brief signal reads as humanity."),
        "Хронический Я-в-порядке": ("Chronic I'm-fine",
            "To \"how are you?\" you automatically reply \"fine\", even with a storm inside. Not a polite lie — a habit not to burden others, not to show weakness, not to be \"the one dragging everyone down\".\n\n"
            "The roots usually go to childhood, where you quickly learned to keep your feelings to yourself. It worked then, and the habit stayed. Now it often works against you — because close ones can't help with what they don't know.\n\n"
            "People sometimes are surprised: \"but you said it was fine!\". Then you explode, or get sick, or sink into depression — and they're shocked because you'd given no warning.\n\n"
            "What's worth knowing: \"I'm fine\" is a survival reflex from a different era. The skill of saying \"actually, not great\" needs to be relearned. Start small — to one trusted person, in one moment. The rest will follow."),
        "Поезд опоздавший": ("Always-late train",
            "You're always late. To meetings, to work, to dates, even to your own things. Not \"sometimes it works out that way\" — your stable pattern. And you know it, and tried to fight it, and it didn't work.\n\n"
            "The root isn't disrespect — perception of time. You sincerely think you'll get there in 15 minutes when really it's 25. Every time. Not math, psychology: you plan for the ideal scenario, but the ideal scenario happens once in ten.\n\n"
            "People read this as disrespect even when you don't mean it. Every late arrival is a message \"my time is more important than yours\", even when not intended.\n\n"
            "What's worth knowing: chronic lateness needs a system, not willpower. Set the meeting in your calendar 30 minutes before its actual time. Treat that as the deadline. With a buffer, the pattern breaks. Without one — it never will."),
        "3 утра и серьёзные вопросы": ("3 AM and big questions",
            "It hits you at night. By day everything's under control; at three AM all the questions arrive at once: about meaning, relationships, the past, the future. And you can't keep it inside — you write close ones long messages that demand a response.\n\n"
            "Not malice. Just the moment when defenses are down and you really feel what was pushed away in daylight. And it seems to you it has to be discussed now, because by day it'll slip back under the everyday.\n\n"
            "People sometimes are lost: got a long emotional message at 3 AM and don't know what to do with it. Sleep or reply? Urgent or can wait? Sometimes it strains the relationship.\n\n"
            "What's worth knowing: 3-AM messages are honest but heavy. Try to write them but not send. By morning, decide if the topic still matters. Often the urgency was night talking, not the topic itself."),
        "Угодник": ("Pleaser",
            "You rarely say \"no\". Someone asks — you do it. Not because you want to — because it's awkward to refuse. So half your life you live by other people's plans, then wonder why you're tired and unhappy.\n\n"
            "The root is fear of rejection. Somewhere inside sits the thought that if you refuse, you'll be loved less. So you agree — and avoid being unloved. Only the paradox is, a person without \"no\" inspires not love but use.\n\n"
            "People quickly figure out you can be approached for anything. You rarely refuse, so they come to you more than to others. Over time you become \"convenient\" — and \"convenient\" is the opposite of \"loved\".\n\n"
            "What's worth knowing: \"no\" is a skill. Practice on small things first — refuse to take an extra task at work. Then gradually scale up. The goal isn't to become rude; it's to stop being optional to your own life."),
        "Ревность из ниоткуда": ("Jealousy from nowhere",
            "You're jealous without cause. The partner smiled at a waitress, liked someone's post, stayed late at a meeting — and in your head there's already an affair scenario. You yourself understand it's irrational, but you can't manage the feeling.\n\n"
            "The root isn't distrust of this partner specifically — it's something from before. Maybe you were betrayed before. Maybe you grew up in a family where trust wasn't free. Now that experience activates automatically, even when there's no real threat.\n\n"
            "People around — especially the partner — get tired. Feeling that you constantly have to prove your innocence is exhausting. Over time the partner pulls away, often to where the trust really is gone.\n\n"
            "What's worth knowing: jealousy from nowhere usually requires therapy, not willpower. The pattern is older than this relationship; you can't fix it by \"calming down\". Investing in working with a specialist is more effective than apologizing to the partner each time."),
        "Вкладок 47": ("47 tabs",
            "You have 47 tabs open at once, 12 projects started, 8 books read to halfway, and nothing finished. You know it and are mad at yourself — but every time you see something new and interesting, you start again.\n\n"
            "Not laziness — opposite, you're a person of huge energy. That energy just works better at the start, in the inspiration stage, than at the finish, in the polishing stage. Finishing is boring. Starting is high.\n\n"
            "People over time learn not to believe your plans. When you say \"I'll start studying X\" — they nod, but in their head: \"remember Y you also started three months ago?\". Disappointing.\n\n"
            "What's worth knowing: it's a known pattern called \"high openness, low conscientiousness\". The cure isn't \"to start less\". It's to add a strict closing rule: don't start a new big thing until one current one is finished. Painful at first, freeing later."),
        "_default": ("Mix of small things",
            "You don't have one signature red flag — you have a set of small ones that surface in different situations. With one person — ghosting, with another — long messages instead of a call, with a third — sudden jealousy. A bit of everything.\n\n"
            "Both good and bad. Good — because no single behavior catastrophically destroys relationships. Bad — because people around never know which \"you\" will switch on now.\n\n"
            "People gradually learn to live with your unpredictability. They love you, but sometimes get tired that they can't predict which defense mechanism will fire this time.\n\n"
            "What's worth knowing: a mix of small red flags is harder to fix than one big one — there's no single thing to work on. Start by tracking which one fires when. Patterns become visible over time, and visible patterns become workable."),
    },
    "green_flag": {
        "Активный слушатель": ("Active listener",
            "I really listen, I remember the small things, I can be silent next to someone, I honestly answer \"how are you\". Your green flag — attention to the other. Not \"nodding while thinking my own thoughts\"; really involved.\n\n"
            "This works because you have the rare ability to be present. Most people in conversation are already thinking what they'll say; you're thinking about the other person.\n\n"
            "People love this in you: \"you can be talked to\". And that's probably the best compliment.\n\n"
            "What's worth knowing: active listening exhausts. If you listen to everyone every day, there's no space for your own feelings. Take care of yourself — sometimes worth saying: \"right now I'm not in a state to listen\". That's not selfish — it's keeping the skill from breaking."),
        "Честность и принципы": ("Honesty and principles",
            "I tell the truth even when uncomfortable, I keep my word, I apologize first, I can say \"I was wrong\". Your green flag — built-in honesty. No exceptions.\n\n"
            "This works because you have an inner spine. Most people bend the truth for convenience; you don't, and you're respected for it.\n\n"
            "People sometimes say: \"you're straight as an arrow\". Straight. And I sleep at night.\n\n"
            "What's worth knowing: hard honesty sometimes wounds. Learn to tell \"the truth needs to be said\" from \"the truth needs to be said this way\". Form matters. The same truth, delivered gently, is still truth — but doesn't destroy."),
        "Уважение к другому": ("Respect for the other",
            "I respect another's \"no\", I don't judge for different views, I don't gossip about close ones, I help without expectation. Your green flag — real respect for boundaries.\n\n"
            "This works because you have mature social ethics. Most people don't think about boundaries; for you it's baseline behavior.\n\n"
            "People feel safe near you. And that's a rare feeling in the modern world.\n\n"
            "What's worth knowing: respect for others' boundaries sometimes becomes ignoring your own. Learn to tell. Respect is mutual. Don't let others violate your boundaries just because you don't violate theirs."),
        "Эмоциональная зрелость": ("Emotional maturity",
            "I laugh at myself, I'm glad for friends' successes, I don't seek to blame, I apologize first. Your green flag — adult emotions. No drama, no resentment, no envy.\n\n"
            "This works because you have processed feelings. Most people live on emotional swings; you keep balance.\n\n"
            "People sometimes are surprised at your calm: \"how can you be glad she got the promotion, not you?\". I can. Her joy isn't my loss.\n\n"
            "What's worth knowing: emotional maturity requires constant work. Not \"I have it, that's all\"; daily practice. Don't let the muscle weaken. Without work, envy, resentment, and drama return — they're the default state."),
        "Тихая поддержка": ("Quiet support",
            "I support without advice, I can be silent next to someone, I help without expectation, I really listen. Your green flag — presence, not action.\n\n"
            "This works because you understand: sometimes \"to help\" isn't \"to solve the problem\" but \"to be there\".\n\n"
            "People love you for it. When they feel bad, they come to you — because you won't immediately advise.\n\n"
            "What's worth knowing: quiet support sometimes reads as \"you have no opinion\". Learn to feel. When the other really needs advice — give it. When they need to just be heard — be silent. Different skills, both valuable."),
        "Не лжёт даже в мелочах": ("Doesn't lie even in small things",
            "I tell the truth, I can say \"I was wrong\", I don't seek to blame, I apologize first. Your green flag — integrity even in small things. Where others wriggle out, you say it as is.\n\n"
            "This works because you have your own dignity. A liar constantly tracks what they told whom; you don't.\n\n"
            "People sometimes are surprised: \"you really said it like that?\". Like that. Living with myself matters more than living with their approval.\n\n"
            "What's worth knowing: \"always the truth\" sometimes becomes a relationship test. If you're not loved for honesty, that's not about you — that's about their unreadiness for it. Accept it. And not all truths must be said immediately — timing is also wisdom."),
        "Радость за чужое": ("Joy for others' wins",
            "I'm sincerely glad for friends' successes, I support without advice, I help without expectation, I don't judge. Your green flag — absence of envy.\n\n"
            "This works because you have your own self-sufficiency. Someone else's success doesn't threaten you; you're in your own truth.\n\n"
            "People sometimes don't believe: \"you don't envy?\". I don't. Their success is theirs. Mine is ahead, or already happened.\n\n"
            "What's worth knowing: \"glad for others\" is also a skill. If it comes automatically, wonderful. If you have to strain — worth understanding why. Envy is a normal feeling; working with it is adult practice."),
        "_default": ("Your own set of maturity",
            "You don't have one signature green flag — you have several. Honesty, empathy, respect, maturity.\n\n"
            "This works because you have a developed personality. Most people focus on one \"best quality\"; you understand maturity is a combination.\n\n"
            "People sometimes can't describe you in one word: \"you're just a good person\". The best thing I could hear.\n\n"
            "What's worth knowing: \"a lot of good\" sometimes makes it harder for others to appreciate you — they don't know what to highlight. Accept it. You don't need to be \"known for one trait\"; being a whole person is better."),
    },
    "decision_style": {
        "Калькулятор": ("The calculator",
            "Before an important choice you gather data. Make a table, build pros-and-cons columns, read reviews, ask experts. By decision time you have the full picture — and so you rarely regret your choice.\n\n"
            "Not from fear of mistake. From self-respect. You understand any serious decision affects a year ahead minimum, and spending an extra two hours on analysis is investment, not delay.\n\n"
            "People sometimes get tired of your thoroughness. They want to pick a restaurant already, you're reading two more ratings. They call it \"nerdy\". You call it \"doing things properly\".\n\n"
            "What's worth knowing: analysis paralysis is a real risk. At some point more data stops adding signal — only delays. Set a limit: two hours of research, then decide. Otherwise the calculator becomes a cage."),
        "Внутренний голос": ("Inner voice",
            "You trust intuition — and are often right. Not because mysticism, but because intuition isn't magic — it's the brain's high-speed pattern-recognition trained on lots of experience. You accumulated it, and now your \"feeling\" is actually very fast analysis.\n\n"
            "Most people don't trust intuition because they can't justify it. They need reasons. You understand reasons sometimes come later — and a decision has to be made now. So you decide.\n\n"
            "People sometimes are surprised at your speed: \"how did you decide so fast?\". Not fast — you processed in a second what others process in a day. Just unconsciously.\n\n"
            "What's worth knowing: intuition works in fields where you have experience. In new fields it's just guessing. Learn to tell where the intuition is trained data and where it's a hunch. The first is precise; the second can be very wrong."),
        "Голос мудрых": ("Voice of the wise",
            "Before a serious choice you go to close ones. Not so they decide — to hear another perspective, test yours on someone else's ear. After the talk you decide alone, but the decision is firmer.\n\n"
            "A rare type in an era of \"no one understands me\". You understand another person often sees your situation more clearly than you do — they don't have your fears and ego in the task. An outside view is a form of vision you can't get without it.\n\n"
            "People love you for it. When you come for advice, they feel respected — your choice depends on their words. That's a closeness that builds over time.\n\n"
            "What's worth knowing: choose your council wisely. The same advice from a panicked person and from a steady one is different advice. Two or three calm, sober people — that's enough. A whole crowd just confuses."),
        "Бросок в воду": ("Dive in",
            "You don't like long thinking. See an opportunity — grab it, figure it out as you go. Not lightness, an understanding: reality is always more complex than any preparation, and experience gives more than planning. Better to do and adjust than to plan and not do.\n\n"
            "Most people get stuck in \"not ready\": one more book, one more course, one more month to think. You understood readiness doesn't exist — only risk and accepting it. And you accept.\n\n"
            "People sometimes tap their forehead: \"you can't do it on the fly\". And you're already halfway there and seeing what they can't from shore. Speed is your tool, and it works in many situations.\n\n"
            "What's worth knowing: \"dive in\" works in reversible decisions. In irreversible ones (marriage, big move, surgery) the same speed becomes recklessness. Learn to tell — is this experiment, or is this fate? The first deserves speed; the second deserves a calculator."),
        "Тёмная лошадка": ("Dark horse",
            "You postpone decisions till the last. Not from laziness or fear — but because you noticed: if a task has a deadline, the brain itself will solve it at the right moment, without hours of agony in advance. The deadline is your ally, not enemy.\n\n"
            "Paradoxically it works: instead of spending a week wavering, you live a normal life, and on day X you simply make the decision. And it often turns out better than what you'd have invented over a week.\n\n"
            "People sometimes get nervous around you: \"just decide!\". They don't understand you have a different rhythm. You're not stalling — you're waiting for it to ripen.\n\n"
            "What's worth knowing: the strategy works on solo decisions. With teams it doesn't — others need to plan around you. Learn to either decide earlier when others depend on you, or to pre-warn that the decision is coming on day X. Otherwise you frustrate people who need to act before you."),
        "Долгая перспектива": ("Long perspective",
            "Before choosing you ask yourself: \"what will I regret in 10 years?\". This changes everything. Most decisions look different from a distance, and you can already look from there now.\n\n"
            "It gives you a rare advantage: you don't react to the immediate. When others chase \"a good offer right now\", you ask — will it look this attractive in a year? Often the answer is \"no\", and then you don't go. So you avoid huge numbers of traps.\n\n"
            "People sometimes don't get it: \"take it, it won't be there later\". You silently know that often \"it won't be there later\" is marketing, not reality.\n\n"
            "What's worth knowing: long perspective sometimes paralyzes the present. If you measure every choice by 10 years, you skip joys that won't matter long-term but matter today. Learn to switch — small choices by joy, big ones by perspective."),
        "_default": ("Your own algorithm",
            "You don't use one method for all decisions. Different tasks — different approaches. Small you decide intuitively, big by analysis, emotional after advice, operational by diving in. You have a whole toolkit in your head, and pick the right tool for the task.\n\n"
            "Most people live on one algorithm: always fast, always slow, always with advice, always solo. Convenient, but loses to flexibility. You chose flexibility.\n\n"
            "People sometimes can't predict how you'll decide a specific question. That's strength in negotiation — you're hard to corner. That's weakness in stability — being near you, no one is sure what you'll decide.\n\n"
            "What's worth knowing: flexibility requires meta-awareness. You need to know which tool to pick when. If the choice is reactive — \"happens to use this one\" — that's not flexibility, that's drift. Make sure your toolkit is conscious."),
    },
    "argument_style": {
        "Острый клинок": ("Sharp blade",
            "You don't argue to find truth — you argue to win. And often win. Not because you're right, but because you don't retreat when others tire. Arguments are blows for you, and each one you place precisely on the opponent's weak spot.\n\n"
            "Not love of pain. Pleasure of precision — finding a contradiction in the opponent so fast they don't see it themselves yet. \"Everyone agrees\" bores you. You need resistance to feel something.\n\n"
            "People fear you in office debates and family fights. They intuitively know: enter an argument with you — leave with a loss, even if you were right. Many simply stop arguing — but that's not victory either. You wanted real engagement; you got silence.\n\n"
            "What's worth knowing: winning every argument means losing every relationship. Sometimes lose deliberately to keep the connection. Truth isn't always worth the cost. Learn to choose which battles are real and which are ego."),
        "Переговорщик": ("Negotiator",
            "What matters more is that everyone leaves satisfied than that you \"won\". You listen first, answer second. See common ground where others see war. If hopeless — switch to humor or just leave. Not from weakness — from understanding that shouting at a wall is meaningless.\n\n"
            "A rare skill in an era where everyone rushes to speak. You go against the current: pause before answering, attempt to see the other's position. That gives you an edge — you have time to think while others react.\n\n"
            "People love you for the fact you can be talked to. Not scary to voice a dumb thought — you won't shred it. Not scary to reveal weakness — you won't use it.\n\n"
            "What's worth knowing: peacemaking has a price. If you always smooth, your own position gets erased. Learn to draw a line: \"I'll smooth most things, but here I have a stake\". Otherwise you become invisible to the people you're saving."),
        "Сократ": ("Socrates",
            "For you an argument isn't war but a tool. You seek truth, not victory. If the opponent turns out right — you calmly switch positions, because the goal was \"to understand how it is\", not \"to prove mine\". A rare type in an era where arguments are immediately about ego.\n\n"
            "You can persist if it matters — but persist not for yourself, for the topic. It shows: you don't get angry when corrected. You're grateful — because now your worldview is one pixel sharper.\n\n"
            "People sometimes are surprised at your ease in admitting mistakes. To them it seems like weakness — to you it's strength. You don't cling to a position because you don't identify with it.\n\n"
            "What's worth knowing: Socratic style works with people open to dialogue. With those convinced of being right, the same approach reads as endless questions and gets exhausting. Learn to recognize when you have a partner in dialogue and when you don't. With the latter, the conversation is a different game."),
        "Эмоциональный вихрь": ("Emotional storm",
            "You argue with the heart, not the head. You don't need tables — you need belief in what you're saying. And that belief is contagious: you persuade not by argument but by intensity. When you speak, it seems your words carry the whole world.\n\n"
            "It works because emotion is the most honest language. Logic is always suspect (it can be picked); passion isn't. When you're truly indignant or inspired, it shows from a kilometer away, and that moves many faster than an hour of facts.\n\n"
            "People are either charmed by you or slightly afraid. Arguing with you is like standing in a storm. Logical counter-arguments drown in your wave of feeling. Some adore it; others can't take it.\n\n"
            "What's worth knowing: emotional power is a great influence, but a poor decision-tool. When you're in storm, you also can't think clearly. Learn to recognize when you're moving people and when you're being moved by your own feelings. The second is a trap."),
        "Внутренний дебатчик": ("Internal debater",
            "You don't argue out loud — you argue inside. While others shout, in your head a dissertation unfolds: what they said, what they meant, where the weakness, what you'd reply. Only you don't reply.\n\n"
            "Not fear and not weakness. Understanding that speaking aloud is often a waste of energy. Most arguments resolve nothing except raised temperature. And you already know the ending, because you calculated it in the first 30 seconds.\n\n"
            "People sometimes read your silence as agreement. That's a mistake. You don't agree — you just decided the fight isn't worth the candle. Internally you've already broken them on every point; they just don't know.\n\n"
            "What's worth knowing: the strategy saves energy but builds invisibility. People can't engage what they don't see. Sometimes voice the silent debate — once, briefly — so they know you weren't agreeing, you were observing. Otherwise your stance becomes ghostly."),
        "Несгибаемый": ("Unbendable",
            "You don't surrender positions even when it gets hard. Not stubbornness — understanding some things can't be ceded. If you believe in something, you'll hold it even if everyone's against. A rare trait in an era where \"agree to get through\" became normal.\n\n"
            "It works like this: inside you have several inviolable principles. On everything else you can negotiate, compromise, admit mistakes. But when it's a principle — you don't move. And it shows from the first seconds: people test you, understand, stop trying.\n\n"
            "People feel that with you they can't play manipulations. That builds trust, but also distance. Some people use principle-people as anchors; others avoid them as inflexible.\n\n"
            "What's worth knowing: keep the list of principles short. Five inviolable things — anchors. Fifty inviolable things — a wall. Make sure each principle is genuinely yours and genuinely matters. Otherwise inflexibility becomes a personality."),
        "Молчаливый наблюдатель": ("Silent observer",
            "You rarely enter arguments — but when you enter, it's serious. Most discussions around you seem like noise: people fight about nothing, raise voices over emptiness. You listen, don't interfere, filter. Engage only when something real is touched.\n\n"
            "Energy economy, not indifference. You understand opinion is currency, and if you spend it on every triviality, in the important moment it has no weight. So you wait, and so your word means more than someone who talks constantly.\n\n"
            "People read you interestingly: on one side calmness, on the other a sharp gaze. Everyone knows you see and process — and many become more careful around you because of it.\n\n"
            "What's worth knowing: silent observation is power, but it can read as detachment. Sometimes voice your noticing — in a single line. \"I see it differently, but it's not my fight\" — and they know you're with them, just not at war."),
        "_default": ("Flexible strategist",
            "You don't have one signature argument style — you switch registers depending on the situation. With one, logic; with another, emotion; with a third, silence. Not sloppiness — understanding different people understand different languages.\n\n"
            "Unlike those who always \"cut the truth\" or always \"diplomatically smooth\", you pick the tool for the task. That gives a huge advantage — you can negotiate where others get stuck in one mode.\n\n"
            "People can't predict you. Sometimes you're quiet and listening, sometimes passionate and principled. That throws them off — and disarms them: they don't know which version of you to defend against, so often they don't defend at all.\n\n"
            "What's worth knowing: flexibility works with self-awareness. Without it you become someone who shifts to please. The line between adapting to communicate and adapting to disappear is thin — keep it visible."),
    },
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats_by_id = {c.get("id"): c for c in raw}
    arch_done, arch_skip, arch_missing = 0, 0, 0
    for cat_id, tr in T.items():
        cat = cats_by_id.get(cat_id)
        if cat is None: print(f"  [skip] cat {cat_id}"); continue
        for a in cat.get("archetypes", []):
            ru = a.get("name"); pair = tr.get(ru)
            if not pair: arch_missing += 1; print(f"    [warn] {cat_id}/{ru!r}"); continue
            if a.get("body_en") and a.get("name_en"): arch_skip += 1; continue
            a["name_en"], a["body_en"] = pair; arch_done += 1
        da = cat.get("defaultArchetype")
        if da:
            pair = tr.get("_default")
            if pair:
                if not (da.get("body_en") and da.get("name_en")):
                    da["name_en"], da["body_en"] = pair; arch_done += 1
                else: arch_skip += 1
        print(f"  ✓ {cat_id}")
    print(f"\nArchetypes: done={arch_done}, skipped={arch_skip}, missing={arch_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch9.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
