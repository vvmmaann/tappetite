"""Archetype EN backfill — batch 6: Career (3 cats, ~29 archetypes)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "student_persona": {
        "Дедлайнер": ("Deadliner",
            "You're a master of the last night. Calm before the deadline, then a switch flips and you do in 6 hours what others do in two weeks. And often the result is no worse — sometimes better.\n\n"
            "This works because adrenaline is your main fuel. Without pressure you can't focus; everything feels low-stakes. With pressure — sharp and precise. It's not laziness, it's a different neurochemical profile.\n\n"
            "People sometimes judge: \"there you go again, dragging it out\". They don't get that you weren't \"dragging\" — you were waiting for the right state. And in that state you're more effective than they are with their \"proper planning\".\n\n"
            "What's worth knowing: deadliner mode works on small projects. On big ones it breaks. Learn to chunk big tasks into a chain of small deadlines — each with its own pressure point."),
        "Отличник": ("Top of the class",
            "You need it to be \"the best\". Not \"pass\", but \"know better than everyone\". Studying for you isn't an obligation but a way to prove to yourself and the world that you're capable. And you prove it.\n\n"
            "This works because you have an internal standard. For most people that standard is set by school, parents, the boss. Yours is internal. So you give it your all even where no one's checking.\n\n"
            "People sometimes call you a \"nerd\". You don't take offense. They don't know that at 40 you'll be doing what you love and getting paid well for it, and they won't. It's a long game.\n\n"
            "What's worth knowing: top-of-the-class is great but exhausting if it's about external validation. Make sure your standard is yours, not your parents'. Otherwise success feels empty."),
        "Тихий гений": ("The quiet genius",
            "You don't answer first. Don't raise your hand. Sometimes sit at the back. And yet you know the subject deeper than many of the talkers.\n\n"
            "It's a form of intellectual modesty. You don't like demonstrating intelligence — that feels vulgar. If you know — you know, no need to announce it. But when asked directly — your answer is precise and unexpectedly deep.\n\n"
            "People sometimes underestimate you: \"he's quiet, probably not great\". This lasts until the exam or hard problem comes. Then they're shocked: \"how do you know this?\". You always knew.\n\n"
            "What's worth knowing: silence is great in academia, less so in many careers later. Learn to make your voice audible when it matters. Not to brag — to be heard. Otherwise smarter ideas lose to louder ones."),
        "Импровизатор": ("Improviser",
            "You study on charisma. Pass the exam on the fly, knowing 30%, but with 200% confidence. The professor gives you a \"good\", because you spoke as if you knew deeply. When really you just know how to tell the story.\n\n"
            "It's a special talent. Most people, even knowing the material, mumble and lose. You — the opposite. Not knowing — you deliver so convincingly that you believe yourself. It's not deception, it's communicative force.\n\n"
            "People sometimes envy: \"how do you do it?\". And you don't fully understand yourself — it just works. Compensation for the fact that detailed memorization bores you, and the brain went down a different path.\n\n"
            "What's worth knowing: improvisation works in academia and short interviews. In real work where you're tested over time, it cracks. Learn to back up your charisma with real depth in at least one area."),
        "Жонглёр": ("Juggler",
            "You have studies, work, family, sometimes several projects all at once. And you manage. Not because there are 36 hours in your day, but because you have a different time-management approach: you do in parallel what others do sequentially.\n\n"
            "This works because of your skill in separating \"important\" from \"detailed\". You're satisfied with 70% effort where others give 100%. And those freed-up 30% you spend on the next task.\n\n"
            "People look at you like an alien. \"How do you do it all?\". The answer: you don't \"do it all\", you choose. And you let a lot go. The \"let go\" stuff just isn't visible from outside.\n\n"
            "What's worth knowing: juggling has a price — depth. You're often great in breadth and shallow somewhere specific. Learn to identify one or two areas where you go deep. Otherwise you become a \"jack of all\" and never master one."),
        "Стратег-халявщик": ("Strategic shortcut-taker",
            "You figured out the system. That ready answers exist, that every subject has \"tickets\" you submit rather than learn. And you don't waste effort on what won't be needed in real life. Only on what matters.\n\n"
            "It's not stupidity or laziness. It's rationality. Most of the curriculum is formality, and you understood this early. So your strategy: pass the formality with minimum effort, invest serious effort in what's actually interesting.\n\n"
            "People sometimes judge: \"you're a cheater\". You shrug. If the system is built so ready answers are accessible and the professor knows it — that's not on you, that's the system.\n\n"
            "What's worth knowing: strategic shortcuts work in academia. In a job, the same approach reads as \"avoiding work\". Learn to switch — academia is a game with known rules, real work isn't."),
        "Скептик с задней парты": ("Back-row skeptic",
            "You don't believe this education will be useful. And often you're right. So you go for the diploma but don't invest. What matters more is what happens outside the classroom.\n\n"
            "It's not from stupidity or laziness. It's from clear vision: 80% of what's taught isn't needed in real work, and what's needed isn't taught. So you study in reality — through internships, projects, reading, people. The diploma is just a formality.\n\n"
            "People around, especially parents, are shocked: \"but education!\". They think in '80s categories, when a diploma got you a job. You think in today, when work comes from skill, network, and portfolio — and the diploma is increasingly secondary.\n\n"
            "What's worth knowing: skepticism is healthy as long as it doesn't slip into cynicism. Some education really is useful — the question is how to find it. Don't dismiss the whole system; dismiss the parts that genuinely don't work."),
        "_default": ("My own way of learning",
            "You don't have a signature study style. Sometimes top of the class, sometimes deadliner, sometimes improviser. Depends on the subject, professor, mood. This isn't sloppiness — it's adaptation to different academic situations.\n\n"
            "Most people get stuck in one mode (always excellent or always shortcut) and that mode fails in unsuitable conditions. You're more flexible — and so you survive different academic environments better.\n\n"
            "People sometimes can't predict how you'll approach a particular course. Sometimes you go all in like a maniac, sometimes you do the minimum. You have your own filtering system.\n\n"
            "What's worth knowing: adaptive style is great, but make sure your filter is clear to you. If you can't articulate why you're investing in this and not that — the choice is reactive, not strategic. Learn to name your criteria."),
    },
    "career_vibe": {
        "Стартап-драйв": ("Startup drive",
            "Startup, own business, freelance, blogging. You're not for the big corporation. You need risk, speed, growth. Stability for you is the death of motivation.\n\n"
            "This works because you have an appetite for uncertainty. Most people fear it; you draw energy from it.\n\n"
            "People sometimes worry: \"and if the startup fails?\". It will fail. I'll launch the next one. In my head it's a game, not a tragedy.\n\n"
            "What's worth knowing: startup mode exhausts. After 5-10 years many burn out. Learn to plan recovery. And remember: 95% of startups fail. Without a financial cushion for those years you'll be forced into a corporate job at the worst possible moment."),
        "Стабильность корпорации": ("Corporate stability",
            "Corporation, public sector, finance, marketing. You need stability. A big organization, clear processes, predictable career path.\n\n"
            "This works because you have an understanding of the value of durability. Most young people now rush to startups; you understood that for the long game stability matters more.\n\n"
            "People sometimes say: \"working in government is boring\". Boring. And calm. And the mortgage gets paid, and the kids are okay.\n\n"
            "What's worth knowing: corporate stability works as long as you grow within it. If you're stuck in one role for years, stability turns into a trap. Set yourself a horizon: every 3-5 years either move up, or move out."),
        "Креатив и контент": ("Creative and content",
            "Design, creative industries, blogging, freelance. You're in a creative profession. Not \"producing a product\"; creating meaning, image, brand.\n\n"
            "This works because you have an artistic nature. Strict number-work bores you; you need an idea behind the result.\n\n"
            "People sometimes are surprised: \"where's the stable income?\". It'll come. Just differently.\n\n"
            "What's worth knowing: creative industries are wave-like. Sometimes orders flow, sometimes empty. Learn to plan finances around the waves. And don't confuse \"creative\" with \"irregular\" — the best creatives are disciplined."),
        "IT-волна": ("The IT wave",
            "IT development, design, startup, science. You're in the tech sector. It's not just work — it's an era, and you're in it.\n\n"
            "This works because you have technical thinking. Most people fear code; you're at home with it.\n\n"
            "People sometimes envy IT salaries. You understand the work is also different — constant learning, new frameworks, no stability in the technologies themselves.\n\n"
            "What's worth knowing: IT is high return but also high burnout risk. Every 2-3 years you have to retrain or you become outdated. Accept this as part of the industry. And take care of your nervous system — impostor syndrome is the occupational disease here."),
        "Польза другим": ("Helping others",
            "Public sector, medicine, teaching, sports coaching. You need work to have meaning beyond the salary. To help, heal, teach — that's your format.\n\n"
            "This works because you have deep motivation. Money is nice but not the main thing; what matters is what you did in someone's life.\n\n"
            "People sometimes don't get it: \"working in government for that money?\". For that money. And for caring about going to work in the morning.\n\n"
            "What's worth knowing: \"helping\" professions often come with emotional burnout. Teachers, doctors, therapists — all on the edge. Learn to protect yourself. Without your own resources you can't help others."),
        "Своё дело": ("Your own thing",
            "Own business, freelance, blogging, an unusual creative path. You're not for the office. You need to work for yourself, by your rules, at your pace.\n\n"
            "This works because you have independence. Submitting to others' rules is hard for you; with your own you can self-discipline.\n\n"
            "People sometimes don't believe: \"just go to an office like everyone\". I'm not like everyone. And I have my own path.\n\n"
            "What's worth knowing: \"own thing\" means \"everything on you\". Accounting, marketing, sales, product — all you. If you're not ready for that volume, you'll quit. Learn to delegate as soon as you can afford to."),
        "Цифры и анализ": ("Numbers and analysis",
            "Finance, marketing, science, IT development. You need numbers. Analysis, reports, patterns — your element.\n\n"
            "This works because you have an analytical mind. Most people don't want to dig into numbers; you're at home with them.\n\n"
            "People sometimes call this \"nerdy\". Not nerdy — precise. And it's well paid.\n\n"
            "What's worth knowing: analytical professions sometimes pull you away from real people. If your whole day is Excel and graphs, you gradually lose emotional communication skills. Balance — after work, real people, not more spreadsheets."),
        "Особый путь": ("A special path",
            "An unusual creative path, creative industries, blogging, freelance. You don't fit standard boxes. Your profession is \"what I do\", and it doesn't yet have a clean name.\n\n"
            "This works because you have the courage to go where others don't. Most people pick from ready options; you create your own.\n\n"
            "People sometimes can't explain to their parents what you do. That's normal. In 5 years your \"strange profession\" might be mainstream.\n\n"
            "What's worth knowing: \"your own path\" is also loneliness. You don't have \"colleagues in the field\" in the usual sense. Learn to find people in similar situations — even from different fields. The peer group matters even when you're a pioneer."),
        "_default": ("Your own career path",
            "You don't have one signature career type. You've been in startups, freelance, corporate, your own thing. This isn't \"undecided\" — it's life in motion.\n\n"
            "This works because you have flexibility. Most people get stuck in one field for decades and suffer; you transition.\n\n"
            "People sometimes can't describe what you do. That's normal.\n\n"
            "What's worth knowing: transitions between fields reset expertise. If you change industries every two years, you don't become an expert in any. Learn to at least transfer skills. Management, communication, analytics — those are portable. Build a transferable spine; the surface can change."),
    },
    "your_real_profession": {
        "Tech-делатель": ("Tech maker",
            "Product Manager, Software Developer, UX Designer, Game Developer. You're on a product tech team. Not \"servicing IT\" — building product.\n\n"
            "This works because you have both technical and product thinking. Can dig into code and think about the user.\n\n"
            "People sometimes are surprised: \"you have both?\". Both. And the combination is exactly what they pay for.\n\n"
            "What's worth knowing: tech roles require constant learning. What was current 3 years ago is outdated now. Stay current, or your salary stops growing."),
        "Креатив-делатель": ("Creative maker",
            "Graphic Designer, Content Creator, Photographer, Filmmaker. You're in visual creative. Make content people see.\n\n"
            "This works because you have an artistic eye and technical execution. Most have only one; you combine.\n\n"
            "People sometimes don't believe: \"you're not at a big studio\". And I don't need to be. I have my client and my style.\n\n"
            "What's worth knowing: creative professions often get overpaid at the start and underpaid later. Learn to raise prices. And invest in portfolio — it works for you 24/7."),
        "Творческий нарратор": ("Creative narrator",
            "Writer, Journalist, Musician, Artist. You're a maker of meaning. Not \"making a product\"; creating a work — text, song, painting, story.\n\n"
            "This works because you have a deep inner life. Most people live reactively; you live to express.\n\n"
            "People sometimes say: \"you can't make money on this\". Maybe. But I'm not in it for money — for voice.\n\n"
            "What's worth knowing: creative professions are also serious economic risk. Learn to combine with more stable income. Many great writers worked as editors all their lives so they could afford to write."),
        "Цифры и стратегия": ("Numbers and strategy",
            "Data Analyst, Marketing Manager, Investment Banker, Consultant. You work with numbers and strategies. Analysis, frameworks, recommendations — yours.\n\n"
            "This works because you have a structured mind. Work without clear metrics bores you; you need something measurable.\n\n"
            "People sometimes are surprised: \"you live in Excel?\". In Excel and PowerPoint. And I'm comfortable there.\n\n"
            "What's worth knowing: these professions are high return, high load. Hours often go off the chart. Learn to defend boundaries. If you work 70 hours a week for years — burnout is inevitable."),
        "Старт и риск": ("Start-and-risk",
            "Founder, Content Creator, Sales Rep, Investment Banker. You need risk as part of your profession. Not \"stable salary\"; big upside and big possibility of failure.\n\n"
            "This works because you have a strong appetite for achievement. Without risk you're bored; you need every day to be a bet.\n\n"
            "People sometimes worry: \"and if it doesn't work out?\". It won't work, then the next thing will. I'm not the type that freezes after failure.\n\n"
            "What's worth knowing: risk professions are emotional swings. Today on top, tomorrow in a hole. Learn not to identify with short-term outcomes. Otherwise your self-esteem rides the same swings, and that's exhausting."),
        "Помощь людям": ("Helping people",
            "Doctor, Therapist, Teacher, HR Specialist. You're in a helping profession. Your work is people and their states, and you find meaning in it.\n\n"
            "This works because you have empathy as a resource. Most people burn out from others' problems; you have the capacity to hold them.\n\n"
            "People sometimes are surprised: \"how do you handle it?\". I handle it. It's my calling, and the capacity is there.\n\n"
            "What's worth knowing: helping professions are #1 for burnout. Without supervision, personal therapy, rest — you'll burn out in 10 years. Self-care is part of professionalism here, not \"weakness\"."),
        "Точная инженерия": ("Precise engineering",
            "Engineer, Architect, Researcher, Pilot. You're in a profession that requires precision. There's no \"approximately\" — there's \"right\" and \"wrong\".\n\n"
            "This works because you have an engineer's mind. Work with vague results bores you; you need something concrete at the end.\n\n"
            "People sometimes are surprised: \"you're a pedant\". Pedant. But my pedantry saves lives / builds buildings / advances science.\n\n"
            "What's worth knowing: precise professions are often slow in progress. One project can take years. Learn to accept long horizons. Without that patience you'll feel \"stagnant\"."),
        "Слова и убеждение": ("Words and persuasion",
            "Lawyer, Journalist, Sales Rep, PR Specialist. Your tool is the word. You persuade, sell, defend, explain.\n\n"
            "This works because you have a talent for communication. Most people can't articulate clearly; you do it professionally.\n\n"
            "People sometimes don't get it: \"how many words a day?\". Thousands. And each one carries weight.\n\n"
            "What's worth knowing: word professions also carry moral load. Sometimes you'll have to defend or sell something you don't like. Learn to separate. And remember — ethics matters more than short-term gain; reputation builds for years, falls in a day."),
        "Особый артистизм": ("Particular artistry",
            "Chef, Musician, Artist, Photographer. You create not with words and not with code — with another material. Food, sound, paint, light.\n\n"
            "This works because you have a deep connection to a specific medium. Words are too narrow for you; you need physical execution.\n\n"
            "People sometimes don't believe: \"you're a chef?\". Yes. And every day is a performance.\n\n"
            "What's worth knowing: these professions exhaust the body. Chef on feet 12 hours; musician touring; photographer hauling gear. Take care of the body. Without it the career is over."),
        "Мост культур": ("Bridge of cultures",
            "Translator, Diplomat, Journalist, Teacher. You work between worlds. Between languages, between countries, between different audiences.\n\n"
            "This works because you can see from different points. Most people live in one bubble; you move between several.\n\n"
            "People sometimes are surprised: \"what's your native language?\". Several. And not one is fully native.\n\n"
            "What's worth knowing: \"between worlds\" is also loneliness. You don't fully belong to any side. Learn to find \"yours\" — other in-betweeners. The community of bilinguals, diplomats, translators — that's your group."),
        "Спорт и тело": ("Sport and body",
            "Athlete, Chef, Doctor, Pilot. Your profession requires physical fitness. Not \"office work\" — active, on your feet, with real load.\n\n"
            "This works because you have body literacy. Many work only with the head; you understand the body is a tool that needs care.\n\n"
            "People sometimes are surprised: \"you're going down a mine?\". No. My work just isn't at a desk.\n\n"
            "What's worth knowing: physical professions have a shelf life. Athlete — to about 35; chef — to about 60; pilot — to 65. Plan the next stage. What will you do after? Better to ask at 30 than at 50."),
        "_default": ("Your own professional mix",
            "You don't have one signature profession. You've done different things — IT, creative, sales, teaching. Your \"profession\" is a combination of all your skills.\n\n"
            "This works because you have a wide background. Most people specialize and lose the ability to see widely; you don't.\n\n"
            "People sometimes can't describe you in one word. That's normal.\n\n"
            "What's worth knowing: \"a lot of different things\" sometimes reads as \"nothing specific\". Learn to formulate your identity. Not \"specialist in X\" but \"a person who can combine X and Y, because that gives a unique angle\". That's a narrative that works for you."),
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
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch6.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
