"""Mass rewrite of paragraph 1 (п1) across 17 archetypes that violate H8 rule.

Same approach as today's investor_type fix — replace ONLY the first paragraph
(split on \\n\\n, swap index [0]). Names, triggers, ids, archetype matching
logic, and paragraphs 2-4 are all unchanged. So users who already played any
of these categories will see the same archetype winner for the same top-3,
just with the new H8-compliant п1.

Plus 2 EN-only tweaks where the RU has a hedging phrase ("ты считаешь",
"для тебя") that the English translation dropped — restoring the hedge.

Source of bug list: _h8_audit_report_20260514.md (full audit run today).

Run on server:
    cd /opt/untitled-pick-game-api
    python3 scripts/rewrite_h8_violations_20260514.py
    systemctl restart untitled-pick-game-api
"""
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = Path("/opt/untitled-pick-game-api/data/categories.json")

# (cat_id, arch_name_ru) -> (new_p1_ru OR None to skip RU, new_p1_en OR None)
REWRITES = {

    ("fitness_mode", "Природный фанат"): (
        "Тебе ближе тренироваться там, где есть горизонт — лес, горы, парк, берег реки. "
        "Кислород и вид важнее железа и зеркал; повторения и пульс ты считаешь по ощущениям, "
        "а не по экрану. Это не спорт ради цифры, это движение ради себя самого в большом пространстве.",

        "You'd rather train where there's a horizon — forest, mountains, park, riverbank. "
        "Oxygen and a view matter to you more than iron weights and mirrors; reps and heart rate "
        "you measure by feel, not by screen. It's not sport for the number, it's movement for its own sake in open space.",
    ),

    ("fitness_mode", "Домашний лекарь"): (
        "Коврик расстелен, за окном утро, никто не смотрит. "
        "Ты двигаешься медленно, вслушиваешься в тело — йога, пилатес, танцы, воркаут на турниках во дворе. "
        "Тебе важнее спокойствие и отсутствие чужих глаз, чем структура занятия и команда рядом. В одиночку слышишь себя лучше.",

        "Mat unrolled, morning outside, no one watching. "
        "You move slowly, listening to your body — yoga, Pilates, dance, calisthenics on outdoor bars. "
        "Calm and the absence of watching eyes matter to you more than structure or a team beside you. Alone, you hear yourself better.",
    ),

    ("brand_reflects_style", "Тишина дороже шума"): (
        "Тебя цепляет вещь без логотипа на груди. "
        "Не из принципа, а потому что чужой бренд на тебе чувствуется как одолженная фраза. "
        "Тебе ближе качество, которое видно только когда трогаешь, чем то, которое орёт издалека.",

        "You're drawn to a piece without a logo on the chest. "
        "Not on principle — but because someone else's brand on you feels like a borrowed sentence. "
        "Quality that's only visible when you touch it appeals to you more than quality that shouts from across the room.",
    ),

    ("your_philosophy", "Тростник"): (
        "Ты гнёшься, и потому не ломаешься — это не про слабость, скорее наоборот. "
        "Тебе ближе подстраиваться под обстоятельства, чем биться головой о стену; "
        "ты раньше других замечаешь, когда поток уже выбрал направление, "
        "и просто перенаправляешь свои силы вместо того, чтобы спорить с течением.",

        "You bend, and so you don't break — this isn't about weakness, rather the opposite. "
        "You'd rather adapt to circumstances than ram your head into a wall; "
        "you notice sooner than most when the current has already chosen its direction, "
        "and you redirect your effort instead of arguing with the river.",
    ),

    ("argument_style", "Несгибаемый"): (
        "Ты не сдаёшь позиции, даже когда становится тяжело. "
        "Не из упрямства — у тебя в голове несколько вещей, которыми ты для себя не торгуешь. "
        "И когда дискуссия касается одной из них, ты держишь это, даже если все против. "
        "В эпоху «согласиться, чтобы пройти» — редкая черта.",

        "You don't surrender positions even when it gets hard. "
        "Not stubbornness — there are a handful of things in your head that you don't trade. "
        "And when the discussion touches one of them, you hold it, even if everyone's against. "
        "In an era of 'agree to get through' — a rare trait.",
    ),

    ("literary_hero", "Одиночка"): (
        "Тебе работается лучше всего в тишине, когда никто не стоит над душой и не ждёт промежуточного отчёта. "
        "Это не мизантропия — ты вообще не против людей, просто твоя голова собирается долго "
        "и шумная компания каждый раз эту сборку разваливает. Поэтому сложные задачи ты бережёшь для одиночества.",

        "You work best in silence, when no one stands over your shoulder waiting for a status update. "
        "This isn't misanthropy — you have no problem with people in general; "
        "it's just that your head takes a long time to assemble and a noisy room dismantles that assembly each time. "
        "So you save the complex work for solitude.",
    ),

    ("hard_day_coping", "Страус в одеяле"): (
        "Телефон на беззвучном, шторы задёрнуты, ты в пижаме смотришь в стену. "
        "Когда снаружи слишком много, тебе ближе закрыться и переждать, чем разруливать в моменте. "
        "Не убегаешь — экономишь, чтобы потом разобраться с ясной головой.",

        "Phone on silent, curtains drawn, you're in pajamas staring at the wall. "
        "When there's too much outside, you'd rather shut down and wait it out than handle things in the moment. "
        "Not running away — conserving energy so you can deal with it later, with a clearer head.",
    ),

    ("relationship_values", "Лёгкий вайб"): (
        "Тебе ближе отношения, в которых много воздуха — юмор каждый день, тихая близость без слов, "
        "свобода быть собой, страсть когда она сама приходит. "
        "Постоянное «решать, строить, разбирать» тебя сковывает; "
        "ты предпочитаешь, чтобы хорошее случалось само, как погода в правильный день.",

        "You're drawn to relationships with plenty of air — daily humor, quiet closeness without words, "
        "freedom to be yourself, passion that arrives on its own. "
        "Constant 'deciding, building, processing' feels constricting to you; "
        "you'd rather good things happen by themselves, like the weather on a right day.",
    ),

    ("first_date_pay", "Классический жест"): (
        "Тебе ближе старая школа. Кто пригласил — тот и платит, или мужчина на первом, "
        "или кто первый потянулся к карточке. Для тебя в этом не патриархат, "
        "а форма гостеприимства: позвал человека провести вечер — закрой этот вечер сам, "
        "в этом есть свой ритуал и приятная определённость.",

        "Old school is closer to you. Whoever invited pays, or the man pays on the first date, "
        "or whoever reaches for the card first takes it. For you it isn't about patriarchy — "
        "it's a form of hospitality: you invited someone for the evening, so you cover that evening. "
        "There's a ritual to it, and a pleasant clarity.",
    ),

    ("first_date_pay", "Прагматичная договорённость"): (
        "Тебе ближе ясность. Кто больше зарабатывает — тот и платит; "
        "или договариваются заранее; или просто решают не заморачиваться, "
        "потому что вечер сам по себе важнее. "
        "Ты не цепляешься за форму, ты ищешь, чтобы сценарий вечера никому не натирал.",

        "You're drawn to clarity. Whoever earns more pays, or you agree in advance, "
        "or you decide not to overthink it because the evening itself matters more. "
        "You don't cling to form — you're looking for the evening's script to not rub anyone the wrong way.",
    ),

    ("hollywood_actors_50plus", "Верный Новому Голливуду"): (
        "Эпоха кокаина и длинных монологов в твоей крови. "
        "Тебя цепляют актёры с послужным списком, где есть хотя бы пара картин Скорсезе или Копполы — "
        "для тебя это знак, что человек прошёл школу, а не просто красивый кастинг.",

        "The age of cocaine and long monologues runs in your veins. "
        "You're drawn to actors with a couple of Scorsese or Coppola films on their résumé — "
        "for you, it's a sign someone went through the school of the craft, not just a good casting.",
    ),

    ("aesthetic_vibe", "Старая школа элегантности"): (
        "Логотипы и тренды для тебя — фоновый шум, не аргумент. "
        "Ты слышишь вещь по-другому: качество ткани, точная посадка, ровная линия плеча. "
        "Это и есть твой язык — и он работает в любую эпоху, не привязан к сезонной картинке.",

        "Logos and trends are background noise to you, not arguments. "
        "You read a piece differently: fabric quality, precise fit, a clean shoulder line. "
        "That's your language — and it works in any era, not tied to a seasonal picture.",
    ),

    ("ideal_vacation", "Друзья и природа"): (
        "Тебе ближе отдыхать с теми, кого ты сам собрал, и в месте, где не ловит сеть. "
        "Костёр, тишина, вечерний разговор без диктата таймера — этого тебе хватает, "
        "чтобы вернуться в себя за выходные.",

        "You're drawn to vacationing with the people you've chosen yourself, in a place with no signal. "
        "A bonfire, silence, an evening conversation without the dictate of a timer — "
        "that's enough for you to come back to yourself in a weekend.",
    ),

    ("ru_music_2020s", "Поп-короли 2020-х"): (
        "Утро в маршрутке, припев сам цепляется за память — и ты не сопротивляешься. "
        "Тебе ближе поп-рэп без лишней философии, но с точным хуком: "
        "песня, которая входит без объяснений и остаётся в голове на пару недель.",

        "Morning in a minibus, the chorus sticks by itself — and you don't resist. "
        "You're drawn to pop-rap without extra philosophy, with a perfect hook: "
        "a song that goes in without explanations and stays in your head for a couple of weeks.",
    ),

    ("current_fashion_style", "Чистый минимал"): (
        "Сейчас тебя цепляет чистота — minimal, normcore, clean girl/boy. "
        "Тебе ближе вещи, которые не пытаются сразу что-то сообщить о тебе: "
        "без декора, без лого, без громких акцентов. "
        "Хорошая ткань, точный покрой, чистая палитра — и тебе уже комфортно.",

        "Right now what grabs you is purity — minimal, normcore, clean girl/boy. "
        "You're drawn to pieces that don't try to announce something about you immediately: "
        "no decor, no logos, no loud 'accents'. "
        "Good fabric, precise cut, clean palette — and you're already comfortable.",
    ),

    ("gaming_genre", "Пауза в реальность"): (
        "Ты садишься перед экраном и выдыхаешь — без опасности, без таймера, без счётчика жизней. "
        "Тебе ближе игры, где можно час переставлять мебель в виртуальном доме или собирать пазл; "
        "в этом для тебя есть медитативная функция, которой нет у остальных способов отдохнуть.",

        "You sit down in front of the screen and exhale — no danger, no timer, no life counter. "
        "You're drawn to games where you can spend an hour rearranging virtual furniture or solving a puzzle; "
        "for you there's a meditative function in this that other ways of unwinding don't quite reach.",
    ),

    ("anime_hype_new_wave", "За кулисами"): (
        "Тебя цепляет аниме, которое заглядывает за кулисы — "
        "индустрия изнутри, тёмная сторона того, что снаружи выглядит красиво. "
        "Истории про механику шоу-бизнеса или про тихого человека, оказавшегося в центре внимания против воли, "
        "для тебя честнее, чем глянцевая поверхность той же темы.",

        "You're drawn to anime that looks behind the scenes — "
        "the industry from the inside, the dark side of what looks beautiful from the outside. "
        "Stories about the mechanics of show-business, or about a quiet person who ends up at the center of attention against their will, "
        "feel more honest to you than the glossy surface of the same subject.",
    ),

    # car_type — RU also tweaked (last sentence had universal claim too)
    ("car_type", "Адмирал флота"): (
        "Ты открываешь дверь, и начинается посадка. "
        "Дети с рюкзаками, сумка для спорта, пакеты из магазина — "
        "всё заполняет багажник, второй ряд, нишу под полом. "
        "Ты смотришь в зеркало и видишь не дорогу, а свой отряд. "
        "Машина для тебя — не про скорость, а про логистику.",

        "You open the door, and boarding begins. "
        "Kids with backpacks, a gym bag, grocery sacks — "
        "everything fills the trunk, the second row, the underfloor storage. "
        "You look in the mirror and see not the road but your squad. "
        "A car, for you, isn't about speed — it's about logistics.",
    ),

    # weird_animals — EN-only hedge restoration. RU is fine ("Ты считаешь что")
    # so we pass None for RU to leave it unchanged.
    ("weird_animals", "Поклонник кротких гигантов"): (
        None,  # leave RU as-is
        "Big herbivores are your quiet passion. "
        "You'd say \"weird\" isn't about teeth — it's about calm.",
    ),
}


def main():
    if not SRC.exists():
        print(f"[err] not found: {SRC}", file=sys.stderr)
        sys.exit(1)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = SRC.with_suffix(f".json.bak.{ts}")
    shutil.copy2(SRC, backup)
    print(f"[ok] backup: {backup}")

    data = json.loads(SRC.read_text(encoding="utf-8"))
    cats = data if isinstance(data, list) else data.get("categories", [])

    # Build lookup
    cats_by_id = {c.get("id"): c for c in cats}

    found, missing = [], []
    for (cat_id, arch_name), (new_ru, new_en) in REWRITES.items():
        cat = cats_by_id.get(cat_id)
        if not cat:
            missing.append((cat_id, arch_name, "category not found"))
            continue
        arch = next((a for a in (cat.get("archetypes") or []) if a.get("name") == arch_name), None)
        if not arch:
            existing = [a.get("name") for a in (cat.get("archetypes") or [])]
            missing.append((cat_id, arch_name, f"archetype not in {existing}"))
            continue

        old_ru_p1 = ""
        old_en_p1 = ""

        if new_ru is not None:
            paras = (arch.get("body", "") or "").split("\n\n")
            old_ru_p1 = paras[0] if paras else ""
            paras[0] = new_ru
            arch["body"] = "\n\n".join(paras)

        if new_en is not None:
            paras_en = (arch.get("body_en", "") or "").split("\n\n")
            old_en_p1 = paras_en[0] if paras_en else ""
            paras_en[0] = new_en
            arch["body_en"] = "\n\n".join(paras_en)

        found.append((cat_id, arch_name, old_ru_p1, new_ru, old_en_p1, new_en))

    print(f"\n[ok] applied to {len(found)}/{len(REWRITES)} archetypes:")
    for cat_id, name, old_ru, new_ru, old_en, new_en in found:
        print(f"\n--- {cat_id} / {name!r} ---")
        if new_ru is not None:
            print(f"  old RU п1: {old_ru[:120]}…")
            print(f"  new RU п1: {new_ru[:120]}…")
        else:
            print(f"  RU п1: (unchanged)")
        if new_en is not None:
            print(f"  old EN п1: {old_en[:120]}…")
            print(f"  new EN п1: {new_en[:120]}…")
        else:
            print(f"  EN п1: (unchanged)")

    if missing:
        print(f"\n[warn] {len(missing)} not applied:")
        for cat_id, name, reason in missing:
            print(f"  - {cat_id} / {name!r}: {reason}")

    SRC.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[ok] wrote: {SRC}")
    print("Next: systemctl restart untitled-pick-game-api")


if __name__ == "__main__":
    main()
