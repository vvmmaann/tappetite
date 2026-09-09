"""Archetype EN backfill — batch 10: Lifestyle remaining (3 cats, ~25 archetypes)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "productivity_mode": {
        "Дедлайнер": ("Deadliner",
            "Deadline → one night, procrastinate then sprint, work intuitively without a system, do only what you like. You work under pressure, not on a schedule. And it's your way.\n\n"
            "This works because adrenaline is your main fuel. Without pressure you can't focus; everything feels low-stakes.\n\n"
            "People sometimes judge: \"there you go again, dragging till the end\". I dragged. And in that last night I did better than two weeks would have.\n\n"
            "What's worth knowing: deadliner mode works in school and small projects. On big ones it breaks. Learn to chunk big tasks into a chain of small deadlines — each with its own pressure point. The brain still gets the adrenaline; you don't get the disaster."),
        "Структурированный планировщик": ("Structured planner",
            "Plan and schedule, Pomodoro 25/5, task list as fetish, morning is sacred. You work by system, and that system is your freedom.\n\n"
            "This works because you understand: without structure you'd drown in chaos. Most people fear a strict schedule; you understood — there's freedom from choice in it.\n\n"
            "People sometimes call you a \"nerd\". Maybe. But I get three times as much done.\n\n"
            "What's worth knowing: rigid systems are good but break under the unexpected. Add buffer. A 100% planned day = stress at the first call from mom. 70% planned — realistic."),
        "Утренний человек": ("Morning person",
            "Morning is sacred, plan and schedule, quiet focus, do it myself. You work till noon — those hours you're unbeatable. After — secondary tasks.\n\n"
            "This works because your circadian rhythm is naturally set this way. Most people try to be productive all day; you understood you have a window and you maximize it.\n\n"
            "People sometimes are surprised: \"you're working at 8 AM?\". And by noon I'm in a café or the gym. Not for everyone.\n\n"
            "What's worth knowing: morning mode works only if you go to bed early. If you try to be both lark and owl, burnout is guaranteed in months."),
        "Ночной режим": ("Night mode",
            "Night sprint, quiet focus, intuitively without a system, deadline. You switch on after 11 PM. When the world sleeps, your life starts.\n\n"
            "This works because your biology is set differently. The noise of the office day bores you; you need night silence.\n\n"
            "People sometimes worry: \"you don't sleep\". I do. Just at a different time.\n\n"
            "What's worth knowing: night mode conflicts with a world that runs by day. If your work demands daytime, you're chronically sleep-deprived. Think: can you shift activities to night without breaking the body?"),
        "Тихий фокус": ("Quiet focus",
            "Quiet focus with headphones, do it myself, Pomodoro, morning. You need silence and solitude. No open space, no noise, no people next to you while you work.\n\n"
            "This works because you have deep concentration. Small things knock you off, so you build an environment without small things.\n\n"
            "People sometimes don't get it: \"you don't socialize at the office?\". I do — but not while working. Different modes.\n\n"
            "What's worth knowing: silence mode works as long as you have the environment. If you work in a noisy open space, you need very good noise-canceling headphones. Don't cheap out — that's your productivity."),
        "Социальная энергия": ("Social energy",
            "In a team and shared energy, in cafés with people, several streams at once, intuitively. You need people around to work. Alone — boring and slow.\n\n"
            "This works because you're a social animal. Other people's rhythm lifts you. When someone nearby is doing — you do too.\n\n"
            "People sometimes are surprised: \"you work in a noisy café?\". Yes. And more efficiently than at home.\n\n"
            "What's worth knowing: social style requires access to places with the right vibe. Not every coworking fits. Find your places — where work flows — and don't ditch them for short-term savings."),
        "Маленькие победы": ("Small wins",
            "Many small tasks, list with checkboxes, Pomodoro, plan. You need a structure of micro-goals. A big task scares you; broken into 20 small ones — easy.\n\n"
            "This works because you have dopamine from closing tasks. Each checkmark is a small win, and the day is built from those wins.\n\n"
            "People sometimes say: \"you could've done one big thing\". Could've. But ten small completed are better for me than one big still unfinished.\n\n"
            "What's worth knowing: sometimes the small-wins strategy keeps you from doing the important. Small tasks are often urgent, not important. Learn to balance. Sometimes worth taking on one big thing and forgoing the daily satisfaction."),
        "Идеалист условий": ("Conditions idealist",
            "Only in ideal conditions, only what I like, morning, quiet focus. You need the right conditions to work. Without them — nothing flows.\n\n"
            "This works because you have high sensitivity. Most people can work in any basement; you need a specific environment, and you build it.\n\n"
            "People sometimes call this \"fussy\". Not fussy — system.\n\n"
            "What's worth knowing: ideal conditions rarely happen. If you wait for them, you do nothing. Learn to work in non-ideal conditions too — otherwise you're a hostage to environment. And remember: \"like\" isn't always the main criterion. Sometimes you have to do what you don't love, and that's also part of growing."),
        "_default": ("Mode by task",
            "You don't have one signature mode. Sometimes hard plan, sometimes deadline-night, sometimes café with people. Depends on task and mood.\n\n"
            "This works because you have flexible thinking. Most people fixate on one system and suffer when it doesn't work; you switch.\n\n"
            "People sometimes can't predict you.\n\n"
            "What's worth knowing: flexibility works as long as you understand what to apply when. If it's \"as it happens\" — that's no longer strategy, that's reactivity. Learn to consciously pick the mode for the task."),
    },
    "ideal_evening": {
        "Дома в покое": ("Home in peace",
            "Home with a TV show, doing nothing, reading a book, cooking dinner. You need the evening at home — without events, without external demands, without obligations.\n\n"
            "This works because your life is intense already. The evening is a pause, a recovery point.\n\n"
            "People sometimes invite: \"come out\". And you're under the blanket. And it's better there than in any bar.\n\n"
            "What's worth knowing: home-evening is great but sometimes becomes isolation. If you're home every evening, you gradually lose social ties. Alternate — sometimes go out, even when you don't feel like it. Especially when you don't feel like it."),
        "Активная социальность": ("Active social",
            "Hangout with friends, gaming with friends, the night city, a concert. You need an evening with people. Lots, loud, vivid.\n\n"
            "This works because you have a social nature. Without people you're bored; you need to charge from shared energy.\n\n"
            "People sometimes get tired of you: \"you're calling somewhere again\". Again. So what? Life is short.\n\n"
            "What's worth knowing: social evenings exhaust, even when they seem to charge you. If you're \"in people\" every evening, you have no time for yourself. Alternate — an hour alone a day is needed even by the most social person."),
        "Романтика и парность": ("Romance and pairs",
            "A date, cooking dinner together, the cinema, a walk. You need an evening with one important person. Not a group; not solo — connection.\n\n"
            "This works because you have a request for intimacy. Most people are either in a group or alone; you look for the third format — two.\n\n"
            "People sometimes don't get it: \"with him/her again?\". With him/her. And every time it's like the first.\n\n"
            "What's worth knowing: pairs are wonderful but shouldn't be the only form of leisure. If you only have \"evenings with the partner\", you lose both friends and yourself. Balance."),
        "Тихий восстановитель": ("Quiet restorer",
            "A walk alone, café with a book, spa, reading. You need an evening with yourself. Not solitude as suffering; silence as resource.\n\n"
            "This works because you have the ability to be alone. Most people run from themselves; you go toward yourself.\n\n"
            "People sometimes don't get it: \"aren't you bored?\". Not bored — calm.\n\n"
            "What's worth knowing: quiet evening is good, but sometimes becomes a habit of avoidance. If you choose \"alone with a book\" because you fear people — that's no longer rest, that's fear. Learn to tell."),
        "Тренировка тела": ("Body training",
            "Gym, walk, cooking, gaming. You need physical motion in the evening. Not \"relax lying down\"; stretch the body after office day.\n\n"
            "This works because you need physical balance. If you sat all day, the evening should be about the body.\n\n"
            "People sometimes are surprised: \"the gym after work?\". The gym. And I come home more tired — but in a good way.\n\n"
            "What's worth knowing: evening workouts can interfere with sleep. If you go to bed at 11 PM but train at 9 PM — high probability of bad sleep. Plan ahead. A workout 3+ hours before sleep — better."),
        "Учиться и расти": ("Learning and growing",
            "Learn something new, read, café with a book, long call to a friend abroad. You need an evening of development. Not rest — forward motion.\n\n"
            "This works because you have constant curiosity. Just sitting bores you; the evening has to add something.\n\n"
            "People sometimes don't get it: \"just relax\". To me this is relaxation — learning something new.\n\n"
            "What's worth knowing: chronic learning mode exhausts. The brain also needs rest, not only new data. Learn to tell \"I'm curious\" from \"I can't stop\". The first is healthy. The second is anxiety in a mask."),
        "Игровой вечер": ("Gaming evening",
            "Gaming with friends, hangout, concert, night city. You need an evening of play — broadly. Virtual, physical, social — but with thrill.\n\n"
            "This works because you have a passion for entertainment. Most people in the evening \"rest passively\"; you need activity.\n\n"
            "People sometimes are surprised: \"4 hours in Discord with friends?\". 4. And every 4 minutes were interesting.\n\n"
            "What's worth knowing: a gaming evening eats time fastest. After it often the feeling \"where did the evening go?\". Set timers. Otherwise the game becomes irresponsible time consumption."),
        "Эстетический поход": ("Aesthetic outing",
            "Cinema, concert, café, night city. You need an evening of impressions. Not \"grab something to eat\"; a ritual — in the right place, with the right backdrop.\n\n"
            "This works because you have aesthetic sensitivity. Just \"spending time\" isn't enough; it has to be beautiful.\n\n"
            "People sometimes don't tell them apart: \"what's the difference what café\". Huge. A café isn't a \"place to eat\", it's atmosphere.\n\n"
            "What's worth knowing: aesthetic outings are also an investment. Good cinema, good place, good company — all costs. You're not paying for \"time\", you're paying for \"quality of experience\"."),
        "_default": ("Your own evening set",
            "You don't have one signature evening scenario. Sometimes home with a show, sometimes friends in a bar, sometimes a workout, sometimes a quiet walk. Each evening different.\n\n"
            "This works because you have flexibility. Most people live by template; you hear what's needed today.\n\n"
            "People sometimes can't predict where you'll be tomorrow evening.\n\n"
            "What's worth knowing: flexibility is good, but sometimes worth creating your own ritual. One evening a week — definitely for yourself. That gives stability in the flow. Otherwise too much freedom turns into chaos."),
    },
    "life_rhythm": {
        "Жаворонок-машина": ("Lark machine",
            "You get up before dawn — and at that hour your best. By 5 AM you've done exercise, read a chapter, written a plan, while others still sleep. The day starts with a win, and the rest of life runs in the plus.\n\n"
            "Not drudgery. Understanding: the quiet morning hours are the only time when the world doesn't bother you. No one writes, calls, demands attention. It's your time, and you don't give it up.\n\n"
            "People sometimes are surprised: \"how do you manage everything?\". No secret — you simply have 4 hours more in your day than someone who gets up at 9. And those 4 hours are the most productive.\n\n"
            "What's worth knowing: an early rise requires going to bed early. If you stay up till midnight then wake at 5, you're sleep-deprived and the gain disappears. The morning machine works only when paired with disciplined evenings."),
        "Ночной охотник": ("Night hunter",
            "Your best switches on after midnight. When the world sleeps, you're just starting — writing, reading, doing what feels impossible by day. At night you get access to a part of the brain that simply isn't there in daylight.\n\n"
            "Not \"that's just me\". Biology: your circadian system is set differently from most, and trying to rebuild it is a war you've lost many times. Better to accept and use it.\n\n"
            "People sometimes don't get it: \"just go to bed earlier\". They don't know that for you \"bed at 11\" means missing your most productive hours. You're not stubborn — you're just different.\n\n"
            "What's worth knowing: night mode works in a flexible career. In rigid 9-to-5, you're chronically tired. Either negotiate the schedule or accept the cost. The body has limits even on willpower."),
        "Хаотичная свобода": ("Chaotic freedom",
            "You have no schedule and you're fine. Yesterday up at 6, today at 12. Worked at night, napped in the day. Any attempt to \"structure\" you sparks an internal revolt — because freedom from schedule is more valuable to you than predictability.\n\n"
            "Not laziness or irresponsibility. Understanding: life is more interesting when its rhythm is dictated by you, not the calendar. You do what's needed when you feel it — and often that's more effective than \"by schedule\".\n\n"
            "People sometimes get nervous around you. They want to know when you'll be free, and can't — because you don't know either. It can irritate them, and sometimes they pull away.\n\n"
            "What's worth knowing: chaotic freedom works for solo work. With teams it costs you — others can't plan around you. Learn to give them at least some predictability — even one fixed time slot a week — otherwise the chaos gradually isolates you."),
        "Спринтер-марафонец": ("Sprinter-marathoner",
            "You live in cycles: a week of furious productivity, then a week of recovery. Sprint — rest — sprint. Not the sawtooth chart of a loser, but a conscious choice: you understood that delivering evenly day after day isn't your way.\n\n"
            "In sprint mode you do more than most do in a month. In rest mode you don't \"laze around\" — you replenish fuel. A week later you're ready for the next push, and so on for years.\n\n"
            "People sometimes don't get the variability. Last week you were unstoppable; this week you're in energy-saving mode. They think you're \"inconsistent\". You're cyclical. Different things.\n\n"
            "What's worth knowing: cycles work as long as the rest week is real rest. If during \"recovery\" you keep pushing, you'll burn out. Make sure the rest is non-negotiable — calendar it, defend it. Otherwise the cycle becomes a chronic sprint."),
        "Завтра-человек": ("Tomorrow person",
            "You've told yourself many times \"starting Monday\". And from Monday you really did start — for three days. Then you broke off, and Monday again. Not laziness or weakness — a pattern you've repeated for years.\n\n"
            "The root is usually perfectionism: you try to start \"properly\", with the big task, with the ready system. So every breakdown is \"didn't get it right\", and you wait for the next Monday to try again.\n\n"
            "People sometimes get tired of hearing your plans. They already know the script: you light up, start, drop, blame yourself, wait, start again. And they nod, but inside they don't believe.\n\n"
            "What's worth knowing: the cure isn't \"more discipline\". It's lower the bar at the start. Don't \"start studying English seriously\" — start \"open the app for 5 minutes today\". Tiny first steps beat big plans every time."),
        "В людях": ("Among people",
            "You can't work at home. You need movement around — café, coworking, shared room. When others nearby do something, you do too. Silence and solitude don't inspire you — they put you to sleep.\n\n"
            "Not dependence on company. Understanding: you're a social animal, and your brain works better in an environment with the rhythm of others. Without it you're in a vacuum, and work freezes.\n\n"
            "People sometimes are surprised how you concentrate in a noisy café. Paradox: you need background noise to enter focus. Full silence for you is — on the contrary — distracting.\n\n"
            "What's worth knowing: your style needs access to the right places. Not every coworking fits. Find your spots and protect access to them. They're as crucial to your productivity as a quiet office is to a focus introvert."),
        "_default": ("Your own rhythm",
            "You don't have one signature mode — your rhythm changes by season, project, mood. Sometimes lark, sometimes owl, sometimes chaos, sometimes discipline. Not instability — adaptability.\n\n"
            "Most people try to fix themselves in one mode and suffer when it doesn't work. You understood: a person isn't a schedule; they're alive, and their needs change. And you account for it.\n\n"
            "People sometimes can't predict when you're \"available\". That demands flexibility from them and communication from you. The closer the people, the more important they understand your current mode.\n\n"
            "What's worth knowing: flexibility is great, but communicate it. People take silent variability personally. \"I'm in sprint mode this week, will reach out next\" — one line — saves relationships."),
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
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch10.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
