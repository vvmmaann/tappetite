"""Archetype EN backfill — batch 4: Philosophy (3 cats, ~25 archetypes)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "your_philosophy": {
        "Тихий капитан": ("The quiet captain",
            "When the storm hits, you don't shout and don't run — you just keep doing what needs to be done. This scares people. They're used to a person in crisis being a person in emotion. You become more precise in crisis.\n\n"
            "It isn't coldness. It's understanding that your emotions are the last place to look for solutions. So you postpone them. Sometimes for an hour. Sometimes for years. And keep rowing.\n\n"
            "People love you for the reliability and at the same time slightly fear you. They fear because they sense intuitively that there's a zone inside you where no one is allowed in. Not even yourself.\n\n"
            "What's worth knowing: locked-up emotions don't disappear, they accumulate. The captain who never lets himself feel ends up running on empty. Find at least one person, one place, one time when you can not be the captain. Otherwise the ship eventually breaks the captain."),
        "Тростник": ("The reed",
            "You bend, and so you don't break. This isn't about weakness — quite the opposite. It's the most underrated form of strength: the ability not to resist where resistance is useless.\n\n"
            "When others have a catastrophe, you have a change of weather. When others cling to what's leaving, you're already packing for what's coming. Not because you don't care — because you understood something simple: trying to stop a river costs more energy than building a boat.\n\n"
            "People around you sometimes mistake this for indifference. Especially those used to measuring love by tension. It's hard for them to believe you can hold something dear and let go of it at the same time.\n\n"
            "What's worth knowing: there's a danger in always bending — you can stop noticing where you actually stand. Sometimes hold ground, even if it costs more. Otherwise flexibility quietly becomes formlessness, and you forget your own shape."),
        "Утренний человек": ("The morning person",
            "You're not one of those who lives by the calendar. Not \"once summer comes I'll be happy\", not \"after I finish the project I'll rest\". You're happy now, because now there's always something concrete: the smell of coffee, the sound of rain, a conversation that isn't rushed.\n\n"
            "This doesn't mean you don't make plans. It's just that for you, plans are background, not finish lines. The finish line is already here, in today. Every today.\n\n"
            "Other people sometimes don't get how you manage to feel so much. The answer is simple: you don't manage. You don't skip. Different things. Those who hurry don't lose time — they lose taste.\n\n"
            "What's worth knowing: your strength is also a risk. If you live entirely in the moment, the future may catch you off guard. Some planning isn't a betrayal of the present — it's care for it. Build a frame; the picture lives inside it."),
        "Автор себя": ("Author of yourself",
            "You don't search for meaning — you write it. For you, life isn't a script someone handed out, but a blank notebook. That's frightening, but doesn't paralyze. The opposite — it frees.\n\n"
            "You realized early there's no \"right path\" — there's the path you decided to call right. So you don't get angry at life when things don't go to plan. You just rewrite the plan. Sometimes a chapter. Sometimes the whole book.\n\n"
            "People are either charmed by you or quietly envy. They envy not the result — you can have failures and crises like everyone. They envy the freedom. You're not a victim of circumstances, even when circumstances are harsh.\n\n"
            "What's worth knowing: writing yourself is great power, but also exhausting. Not everyone needs to constantly invent themselves. Sometimes accept what is. Even authors take days off."),
        "Антихрупкий": ("The antifragile one",
            "A blow doesn't break you — it builds you up. You noticed this trait long ago: every failure, breakup, firing, defeat — turned out to be not a stop but a springboard. Not right away. But sooner or later — yes.\n\n"
            "You don't love chaos — you've made peace with it. Realized a plan never survives contact with reality, and so you build not a plan, but yourself. So that whatever happens — you're ready.\n\n"
            "People sometimes see too much motion in you. \"Never sit still\", \"always changing things\", \"never look back\". They're right and wrong at the same time. You move not from restlessness — from curiosity. Different motions.\n\n"
            "What's worth knowing: antifragility is great, but the body is fragile. Don't take it as a license for endless reckless choices. Some experiments do break you. Learn to tell those that strengthen from those that just damage."),
        "Свой компас": ("Your own compass",
            "You're not the kind to take things on faith. Not instructions, not authorities, not \"this is how it's done\". Not from contrariness — from honesty. You need to understand why precisely so, and not otherwise. And if the explanation doesn't add up — you go your own way, even when it's inconvenient.\n\n"
            "This sometimes irritates people, especially those used to being asked, not doubted. But you don't scare them on purpose. You just don't know how to be otherwise. It's easier for you to lose on your terms than to win on someone else's.\n\n"
            "The paradox is that your freedom is stricter than the disciplined ones'. They follow external rules. You follow internal ones, and yours are harder to dodge.\n\n"
            "What's worth knowing: your own compass is great until it becomes proudly closed. Listen to others — not as authorities, but as data. Sometimes they see what your compass missed."),
        "Якорь": ("The anchor",
            "You're the one people call at three in the morning. And you pick up. Not from duty — because you know: somewhere there has to be a fixed point. And you agreed to be that point.\n\n"
            "It's not passivity. It's a conscious choice — to be reliability in a world where reliability is increasingly rare. Friends, family, colleagues — all of them lean on you, often without realizing. You're the foundation that isn't visible, but without which the building falls.\n\n"
            "People sometimes forget to say thanks. To them you're \"always like that\". They think you chose this position, so it must not be hard on you. But it is hard sometimes. You just don't show it, because that's not your role.\n\n"
            "What's worth knowing: anchors that never get pulled up rust. Ask for help yourself sometimes. Not from weakness, but from understanding: even the foundation needs maintenance. Otherwise you crack quietly, and no one notices."),
        "Меньше шума": ("Less noise",
            "You understood something most don't reach even by old age: happiness isn't quantity. Not the number of things, trips, friends, achievements. It's the quality of attention you spend on one thing. On one conversation. On one book. On one morning.\n\n"
            "You're not an ascetic — you can have things and trips. But they're chosen. Not accumulated. And so each one means something, instead of hanging in the background. This is sometimes called minimalism, sometimes taste. You'd just call it common sense.\n\n"
            "People around you sometimes find it strange. They're used to noise as life's background and don't get how you don't need to constantly listen to something, scroll something, plan something.\n\n"
            "What's worth knowing: less noise is great, but watch you don't slip into avoidance. \"I just need silence\" sometimes hides \"I'm afraid to feel\". Silence as choice — strong. Silence as escape — different."),
        "_default": ("Your own cocktail",
            "You don't fit one label — and that's not disarray, it's maturity. Most people pick one convenient system and hold to it because it's easier. That doesn't suit you. You assemble your philosophy from pieces — and it works, because it's assembled for you.\n\n"
            "In a crisis you turn on discipline; in joy you let yourself loose; in an argument you listen to the opposite view; in tiredness you let go. This isn't contradiction. It's a toolkit. Different tasks — different tools, and you understood that.\n\n"
            "People sometimes are surprised they can't predict you. \"You seemed serious — but yesterday you were laughing\". Both — true. You're a different version in a different situation, and all of them are honest.\n\n"
            "What's worth knowing: a flexible system needs a center. Otherwise it's not flexibility, it's drift. Find at least one principle that doesn't change with context. With it, your cocktail has a base. Without it, just floating."),
    },
    "adult_truth": {
        "Прагматик с кошельком": ("Pragmatist with a wallet",
            "You moved past the \"money is evil\" stage somewhere around 25. And realized — money isn't evil and isn't the goal. Money is fuel. Without it, freedom turns to stress, dreams to fantasies, and connections to rare visits because of plane tickets.\n\n"
            "You don't worship money, but you don't pretend it's \"not the main thing\" either. It's a tool, and an important one. The earlier you learned to handle it, the less time you wasted on meaningless illusions.\n\n"
            "People sometimes call this cynical. Especially those tight on money who somehow take pride in it. You don't argue — everyone has their reality.\n\n"
            "What's worth knowing: pragmatism without soul leads to a hollow life. Money is fuel, but you still have to know where you're driving. Without an answer, even the wealthiest become lost."),
        "Спокойствие выше победы": ("Calm over winning",
            "You understood that proving things to people is the most pointless waste of energy. Most won't hear anyway, and those who will already know. So you chose calm, and that turned out to matter more than being proven right.\n\n"
            "It didn't come at once. At 20 you probably argued, shouted, proved. At 30 you noticed that after winning the argument it was empty inside. At 40 you realized: better a calm soul than a \"correct\" reputation.\n\n"
            "People sometimes read this as indifference. \"Say something, he's talking nonsense!\". And you stay silent, because you know — he's talking nonsense, and in a month it'll be obvious to everyone without you.\n\n"
            "What's worth knowing: calm is great, but watch it doesn't slip into avoidance of important conflicts. There are things worth speaking up about. The ability to choose battles is a skill — not the absence of battles."),
        "Себя не предать": ("Don't betray yourself",
            "You understood the central adult truth: you can lose anything — work, relationships, money — but if you lose yourself, you don't come back. So your main task is to stay yourself, even when the world demands otherwise.\n\n"
            "It isn't stubbornness or non-conformism for its own sake. It's a conscious selection: which compromises you'll make for the external, and which — not. And the \"not\" list is short but absolute.\n\n"
            "People sometimes don't get it: \"just bend a little, what's the problem?\". You know — the problem is that bending once, you bend a second time more easily, and a third even more. And in 20 years you don't recognize who you became.\n\n"
            "What's worth knowing: \"don't betray yourself\" is great, but be careful not to confuse self-loyalty with rigidity. Sometimes the \"yourself\" of 20 years ago shouldn't run today's life. Self-loyalty is to the present you, not the past one."),
        "Хорошо — это уже много": ("Good is already a lot",
            "You understood that life doesn't have to be perfect to be good. Most people chase \"better\" their whole lives and end up missing the \"good\" that's already there. You aren't one of them.\n\n"
            "This truth usually arrives after some loss or crisis. When it gets really bad, you realize in retrospect — things were good before, and you didn't notice, because you were measuring against an even higher standard. Since then you measure differently.\n\n"
            "People sometimes call this \"lowering the bar\". It isn't lowering — it's calibrating. Most have their bar set by the advertising industry, not by reality. You set your own.\n\n"
            "What's worth knowing: \"good is enough\" is great, but watch it doesn't become acceptance of the unacceptable. Some things shouldn't be tolerated as \"good for you\". The line between content and resigned is yours to keep clear."),
        "Деньги, дисциплина, связи": ("Money, discipline, connections",
            "You understood the trio that decides almost everything in adult life. Not talent, not luck, not \"the right moment\" — three boring things: financial sobriety, execution discipline, and who-you-know.\n\n"
            "It's not a comfortable knowledge. Romantically it's nicer to believe talent will break through on its own. Reality — no, it won't. The most talented kids from your school now work for 50K because they didn't have discipline and connections. And you, average in talent, are far ahead exactly because those three things are in order.\n\n"
            "People sometimes call you cynical. You don't care. You know cynicism is just discomfort renamed. They're uncomfortable with the truth, so they label the messenger.\n\n"
            "What's worth knowing: the trio works, but it isn't all of life. Without meaning behind the money, the discipline becomes treadmill, and connections become transactional. Add a fourth element: why."),
        "Один — это нормально": ("Alone is okay",
            "You understood that solitude isn't a catastrophe. Sometimes it's the best gift to yourself: silence in which you hear yourself, time for what matters, no need to please anyone.\n\n"
            "This knowledge usually comes after failed attempts to \"not be alone\". When you realize that being alone in bad company is worse than being alone alone. And then you become selective about company.\n\n"
            "People sometimes feel sorry for you: \"alone, what about you?\". You smile. They don't know you chose this consciously, and it's good here. Their pity is about their fear of solitude, not about your reality.\n\n"
            "What's worth knowing: \"alone is okay\" is great, but watch it doesn't slide into isolation. Humans are social. A few real connections aren't a luxury — they're nutrition. Solitude as choice — strong; solitude as wall — costly."),
        "Своё, не лучшее": ("Yours, not the best",
            "The hardest adult truth you absorbed: choose not what's best by objective criteria but what's yours by internal ones. And between \"successful by other people's standards\" and \"yours\" you pick the second, even when the first sparkles.\n\n"
            "It isn't a rebellion against success. It's understanding that other people's standards are about other people's lives. Your parent, your colleague, your Instagram friend — each has their own definition of \"right\". And you should have yours. And no one but you can define it.\n\n"
            "People sometimes tap their forehead: \"you could've had a career, but went into this\". You smile. They don't know that \"career\" is their fantasy, not your task.\n\n"
            "What's worth knowing: \"yours\" is hard to identify when noise is loud. Carve out time for silence — without phones, without people, without their voices in your head. In silence, what's truly yours surfaces. Without it — only what's been taught."),
        "_default": ("Your own set of truths",
            "You don't have one signature truth about adult life. You collected your set from different sources: some from practice, some from Stoicism, some from your own experience. This isn't fuzziness, it's the eclecticism of an adult mind.\n\n"
            "Most people pick one philosophy and hold to it, even when it stops working. You're not like that. You understood different situations need different truths, and that's your strength.\n\n"
            "People sometimes can't predict you. Today you say \"money decides everything\", tomorrow \"money isn't the main thing\". They see contradiction. You see context.\n\n"
            "What's worth knowing: flexibility is great, but it requires honesty. If you're switching truths to dodge inconvenient ones, that's a problem. Make sure your eclecticism is wisdom, not avoidance."),
    },
    "biggest_future_fear": {
        "Страх потеряться": ("Fear of losing yourself",
            "Your biggest fear is one day waking up and not recognizing yourself. Not understanding what you want, what you live by, what you believe in. This fear isn't about a specific event — it's about losing your bearings, finding it empty inside.\n\n"
            "It's a meaningful fear. You've seen people around you who \"lost themselves\" — usually slowly, bit by bit, without loud events. They just looked in the mirror one day and didn't recognize what they saw. And that's scarier than any external catastrophe.\n\n"
            "People sometimes don't get it: \"you're successful, what are you afraid of?\". You know success and self-preservation are different things. You can be very successful and absolutely empty. That's exactly your fear.\n\n"
            "What's worth knowing: the fear is healthy as long as it stays a fear and doesn't become paralysis. Use it as a signal to check in with yourself — \"am I still recognizable?\". If yes — go on. If you're starting to drift — stop and recalibrate."),
        "Страх разочаровать": ("Fear of disappointing",
            "What you fear most is failing to meet expectations. Your own, your parents', other people's. This fear stands in the background of your decisions — and sometimes dictates them more than you'd like to admit.\n\n"
            "The root is usually in childhood, where love was conditional: \"we love you when you're a good kid\". You absorbed that unmet expectations = loss of love. And you carry that into adult life, sometimes without noticing.\n\n"
            "People sometimes surprise you: \"be proud of yourself!\". And you can't, because deep down sits the feeling \"not enough\". Whatever you do — too little. And it's exhausting.\n\n"
            "What's worth knowing: the fear of disappointing is impossible to eliminate, but you can change your relationship to it. Notice when you're choosing for yourself vs. for the imaginary judges. The judges are usually not even paying attention. The fear is yours, not theirs."),
        "Страх упустить": ("Fear of missing out",
            "What you fear most is years going the wrong way. Choosing the wrong profession, the wrong partner, the wrong city — and at 50 looking back at a chain of decisions that seemed right in the moment but in sum led to a life that wasn't yours.\n\n"
            "This fear is the flip side of the freedom of choice. In the last century people had less choice: born here — live here, parents that way — you that way. Today freedom is total, and every choice means missing all the others. That paralyzes.\n\n"
            "People sometimes dismiss it: \"just pick something\". They don't understand it's not \"can't choose\" — it's \"afraid to choose wrong\".\n\n"
            "What's worth knowing: most life paths self-correct over time. A wrong choice today isn't the end — usually it's a detour. Rather than agonizing for years before deciding, decide and adjust as you go. Action gives more information than analysis."),
        "Страх изоляции": ("Fear of isolation",
            "What you fear most is ending up alone. Not \"alone in the moment\" but \"alone overall\" — without close ones, without a partner, without people you genuinely matter to. It's an ancient fear, and it sits deep.\n\n"
            "The root is in biology: humans are social animals, and isolation registers in our brain as danger. Long ago an outcast literally didn't survive. Today they survive, but the brain doesn't know it and keeps panicking.\n\n"
            "People sometimes don't get it: \"you're sociable, you have plenty of friends\". They see quantity. You count quality. And in that quality you sometimes have anxiety — which of them will still be around in 20 years?\n\n"
            "What's worth knowing: the fear is real, but the answer isn't \"have more friends\". The answer is to build a few real connections deeply enough that they survive time. Quality over quantity is the actual antidote — but it requires investment, not just presence."),
        "Страх материального дна": ("Fear of hitting bottom",
            "What you fear most is being left without money. Not \"not getting rich\", but literally — ending up in a situation where you can't afford to live. This fear often forms in childhood, if the family had periods of need, and it doesn't go away even when the situation has changed dramatically.\n\n"
            "It isn't \"greed\". It's memory of helplessness. When you have no money, you can't decide to leave, to move, to buy time for yourself. Money = freedom, and the fear of not having it = the fear of losing freedom.\n\n"
            "People sometimes don't understand: \"you're fine, what's the worry?\". They don't know the script in your head: \"and what if tomorrow it all collapses\". The script doesn't reflect reality, but it runs anyway.\n\n"
            "What's worth knowing: the fear feeds on absence of buffers. Build a real safety net — savings, plan B, skills you can use anywhere. With a buffer the fear quiets down. Without one, no income is enough — the script will find the gap."),
        "Страх потерять огонь": ("Fear of losing the fire",
            "What you fear most is interest going out one day. That what lights you up now — work, hobbies, relationships — turns gray. And you'll live without feeling alive. Just functioning.\n\n"
            "This fear belongs to those who remember the feeling of fire. Most people live in moderate gray and don't know it can be otherwise. You know, and so you fear losing the knowledge.\n\n"
            "People sometimes don't get it: \"you have so much going on, what's wrong\". They don't know you live from inspiration to inspiration, and the gaps between are empty, and that emptiness feels unbearable to you.\n\n"
            "What's worth knowing: the fire isn't a constant. It cycles — comes, fades, returns. The empty periods aren't a sign you've lost it forever; they're recovery time. Learn to honor them rather than panic. The fire returns to those who can wait it out without setting fires inside themselves."),
        "Страх остановиться": ("Fear of stopping",
            "What you fear most is \"settling down\". That comfort will lead you off the path, that you'll agree to a \"normal life\", and in 30 years you'll look back and see you did nothing significant. Just lived.\n\n"
            "This fear shapes you as an engine. You're constantly in motion because stopping equals defeat to you. It gives huge energy but also drains — because you don't know how to rest without guilt.\n\n"
            "People around you are sometimes amazed and sometimes exhausted. They don't understand how you do so much. They don't know that under it is fear. Not ambition — avoidance of stopping.\n\n"
            "What's worth knowing: motion-from-fear and motion-from-passion look the same from outside but feel very different inside. Honestly check yourself: are you running toward something, or away? The first makes you. The second exhausts you. The path is the same; the fuel matters."),
        "_default": ("Your own set of fears",
            "You don't have one main fear — you have several mid-sized ones. Sometimes you fear losing yourself, sometimes missing out, sometimes ending up alone. None dominates, but together they shape your anxiety about the future.\n\n"
            "This is both good and hard. Good — because you don't fixate on one fear and you see many dimensions. Hard — because sometimes there are so many fears you don't know which to address first.\n\n"
            "People sometimes are surprised how you live with such a palette of anxieties. The answer: you got used to it. Over time anxiety becomes background, and you learn to act on top of it.\n\n"
            "What's worth knowing: many fears require a strategy of priorities. Pick one — the loudest right now — and address it. The others stay, but quieter. Trying to fix them all at once gets you nowhere. One at a time."),
    },
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats_by_id = {c.get("id"): c for c in raw}
    arch_done, arch_skip, arch_missing = 0, 0, 0
    for cat_id, tr in T.items():
        cat = cats_by_id.get(cat_id)
        if cat is None: print(f"  [skip] cat {cat_id} not found"); continue
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
            else: arch_missing += 1; print(f"    [warn] {cat_id}/_default")
        print(f"  ✓ {cat_id}")
    print(f"\nArchetypes: done={arch_done}, skipped={arch_skip}, missing={arch_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch4.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
