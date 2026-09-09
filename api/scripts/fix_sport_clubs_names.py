# -*- coding: utf-8 -*-
"""Remove specific club/team/player/coach names from archetype bodies of
football_clubs and basketball_teams. Same leak class as football_goat: the
hybrid synthesizer splices archetype paragraphs by the user's top-3, so any
proper name inside a body surfaces in portraits where it doesn't belong.

Strategy: replace the WHOLE body (RU + EN) per affected archetype, keeping
untouched paragraphs verbatim and rewriting only the name-bearing ones into
vivid-but-generic descriptions. Then convert all em-dashes to regular dashes
(user preference: no em dash).

football_clubs (8): Южный огонь, Иберийское сердце, Северный порядок,
    Железный занавес, Большой театр, Горячее море, Крепкие корни, Другой меридиан
basketball_teams (7): Тринадцатый раунд, Своя крепость, Родные цвета,
    Вечный болельщик, Одна звезда, Большая сцена, Европейский паркет

Run: python3 fix_sport_clubs_names.py [--apply]
"""
import json, shutil, sys
from datetime import datetime

CATEGORIES_PATH = '/opt/untitled-pick-game-api/data/categories.json'

REWRITES = {
    'football_clubs': {
        'Южный огонь': {
            'body': (
                "«Это не просто футбол — это всё» — говорят про южноамериканские клубы, и ты понимаешь что это не "
                "преувеличение. Там игра устроена иначе: она ближе к идентичности, к кварталу, к тому кем ты "
                "являешься за пределами стадиона.\n\n"
                "Тебя цепляет другое измерение страсти. В Европе болельщики любят клуб. В Латинской Америке клуб "
                "и болельщики — часть одного организма. Дерби на переполненном южноамериканском стадионе в день "
                "большого матча — не игра, это событие которое помнят всю жизнь вне зависимости от счёта. Именно "
                "эта температура делает эти клубы для тебя особенными.\n\n"
                "Окружающие говорят: «Но там же другой уровень игры». Ты слышишь это и возражаешь: эти клубы брали "
                "главный континентальный кубок ещё тогда, когда Европа смотрела на них свысока. Они десятилетиями "
                "продают лучших игроков за океан — и всё равно остаются великими. Уровень отличается, но величие — "
                "не только про уровень.\n\n"
                "Риск — романтизация атмосферы может закрыть глаза на реальные проблемы: безопасность, насилие между "
                "группировками, организация. Страсть и хаос иногда ходят рядом. Это не повод отрицать величие — но "
                "честный взгляд требует видеть и то и другое."
            ),
            'body_en': (
                "«It's not just football — it's everything» — that's what they say about South American clubs, and "
                "you understand that it's not an exaggeration. The game is structured differently there: it's closer "
                "to identity, to neighborhood, to who you are outside the stadium.\n\n"
                "What grips you is a different dimension of passion. In Europe, fans love the club. In Latin America, "
                "the club and its supporters are part of one organism. A derby at a packed South American stadium on "
                "a big night isn't a match — it's an event people remember their whole lives regardless of the "
                "scoreline. That temperature is what makes these clubs feel distinct to you.\n\n"
                "People say: «But the level of play is different.» You hear it and push back: these clubs were "
                "winning the main continental trophy back when Europe still looked down on them. They've sold their "
                "best players overseas for decades — and remain great anyway. The level differs, but greatness isn't "
                "only about the level.\n\n"
                "The risk: romanticizing the atmosphere can close your eyes to real problems — safety, violence "
                "between factions, organization. Passion and chaos sometimes walk together. That's not a reason to "
                "deny the greatness — but honest engagement means seeing both."
            ),
        },
        'Иберийское сердце': {
            'body': (
                "Красота и жёсткость. Тотальный футбол и прагматизм. Ты замечаешь что тебя цепляют клубы где эти "
                "противоположности сосуществуют — не выбирая между ними, а используя оба в зависимости от момента. "
                "Именно это ты считаешь взрослым пониманием игры.\n\n"
                "Иберийский футбол для тебя — отдельная культура внутри европейской. На одном полуострове уживаются "
                "почти противоположные философии: клуб тотального паса и клуб лобового давления, и оба по-своему "
                "убедительны. Одна школа выигрывала чемпионат мира комбинаторикой — и та же страна превратила "
                "оборонительную злость в искусство. Соседняя страна десятилетиями экспортирует и звёзд мировой "
                "величины, и тренерскую мысль. Там умеют в разные стили.\n\n"
                "Окружающие говорят: «Ты болеешь за разные клубы смотря по настроению». Ты исправляешь: не по "
                "настроению — по стилю игры. Сегодня хочется созидания, завтра — интенсивности. Тут есть и то, "
                "и другое.\n\n"
                "Риск — широкая симпатия к региону иногда маскирует то что конкретные клубы переживают разные "
                "периоды. Клуб с великой историей может сейчас строить что-то новое после кризиса. Региональная "
                "лояльность — хорошая точка входа, но не замена анализу текущего состояния."
            ),
            'body_en': (
                "Beauty and grit. Total football and pragmatism. You notice that what grips you are clubs where "
                "these opposites coexist — not choosing between them but deploying both depending on the moment. "
                "You consider that a mature understanding of the game.\n\n"
                "Iberian football is a distinct culture within European football for you. On a single peninsula, "
                "near-opposite philosophies coexist: the club of total passing and the club of head-on pressure, "
                "and both are convincing on their own terms. One school won the World Cup through combination play — "
                "and the same country turned defensive fury into an art. The neighboring country has exported "
                "world-class stars and coaching thought alike for decades. They know how to operate in different "
                "registers.\n\n"
                "People say: «You root for different clubs depending on your mood.» You correct them: not mood — "
                "playing style. Today you want creation, tomorrow intensity. Here you can find both.\n\n"
                "The risk: broad sympathy for a region sometimes masks that specific clubs go through different "
                "periods. A club with a great history might currently be rebuilding after a crisis. Regional loyalty "
                "is a good entry point, but it doesn't substitute for looking at what's actually happening now."
            ),
        },
        'Северный порядок': {
            'body': (
                "Не вспышки гениальности — долгосрочные результаты. Не один блестящий сезон — десятилетие на вершине. "
                "Тебе ближе клубы которые побеждают системно, и ты умеешь это видеть там где другие видят «скучный» "
                "футбол.\n\n"
                "Для тебя немецкий и нидерландский футбол — это демонстрация что результат не случаен. Академии "
                "которые производят игроков а не покупают их. Тренерские штабы построенные как институции а не "
                "набранные под один проект. Финансовая устойчивость как принцип. Ты находишь в этом свою эстетику — "
                "не несмотря на системность, а именно благодаря ей.\n\n"
                "Окружающие говорят: «Это же не интересно». Ты слышишь в этом обратное: интересным кажется хаос, а "
                "это — дисциплина. Один из этих клубов недавно прошёл целый сезон без единого поражения. Другой "
                "когда-то взял три европейских кубка за пять лет на собственных воспитанниках. Системность — это "
                "тоже достижение, и немалое.\n\n"
                "Риск — чрезмерная оценка организации иногда приводит к недооценке индивидуальности. Клуб может иметь "
                "идеальную структуру и всё равно не побеждать из-за отсутствия одного нужного игрока в нужный момент. "
                "Наблюдай за тем где заканчивается система и начинается человеческий фактор — именно там обычно и "
                "решается всё."
            ),
            'body_en': (
                "Not flashes of genius — long-term results. Not one brilliant season — a decade at the top. You're "
                "drawn to clubs that win systematically, and you know how to see this where others see «boring» "
                "football.\n\n"
                "For you, German and Dutch football is a demonstration that success isn't accidental. Academies that "
                "produce players rather than buying them. Coaching staffs built as institutions rather than assembled "
                "for one project. Financial sustainability as a principle. You find your own aesthetic here — not "
                "despite the systematicness, but because of it.\n\n"
                "People say: «It's just not interesting.» You hear the reverse in that: what seems interesting is "
                "chaos, and this is discipline. One of these clubs recently went a whole season without a single "
                "defeat. Another once won three European Cups in five years with its own academy products. "
                "Systematicness is also an achievement — and a significant one.\n\n"
                "The risk: over-valuing organization sometimes leads to undervaluing individual talent. A club can "
                "have a perfect structure and still fail to win because of one missing player at one crucial moment. "
                "Watch for where the system ends and the human factor begins — that's usually where everything "
                "actually gets decided."
            ),
        },
        'Железный занавес': {
            'body': (
                "Трибуны другие. Температура другая — и не только на улице. Восточноевропейский футбол строится на "
                "другом отношении к игре, и именно это тебя в нём держит — ощущение что ты смотришь что-то что не "
                "для всех, что требует отдельного знания.\n\n"
                "За этим стоит ценность преемственности. Московский клуб начала 90-х, державшийся на своей школе. "
                "Киевская династия легендарного тренера, опередившая эпоху научным подходом к игре. Команда с "
                "востока, за двадцать лет ставшая доминирующей силой своей страны. Всё это истории долгого "
                "строительства в условиях которые западные клубы никогда не переживали. Ты ценишь эту "
                "контекстуальность.\n\n"
                "Окружающие говорят: «Там же слабее уровень». Ты слышишь неточность: лучшая из этих команд в свои "
                "годы входила в тройку сильнейших в Европе, а другие играли в континентальных финалах. Уровень "
                "циклический — и именно этот цикл тебе интересен не меньше чем любой постоянно топовый клуб.\n\n"
                "Риск — ностальгическая линза увеличивает прошлые достижения и уменьшает текущие проблемы. "
                "Восточноевропейский клуб сегодня — это часто не то что восточноевропейский клуб двадцать лет назад. "
                "Смотри на то что происходит сейчас: в каком состоянии академия, есть ли у клуба направление, что "
                "нового он предлагает игре."
            ),
            'body_en': (
                "The stands are different. The temperature is different — and not just outside. Eastern European "
                "football is built on a different relationship with the game, and that's what keeps you there — the "
                "feeling of watching something that isn't for everyone, that requires separate knowledge.\n\n"
                "Behind this is a value for continuity. A Moscow side of the early 90s that held together on its own "
                "school. A Kyiv dynasty under a legendary coach who was ahead of his era with a scientific approach "
                "to the game. A club from the east that became its country's dominant force over twenty years. All "
                "these are stories of long construction under conditions Western clubs never experienced. You value "
                "that contextuality.\n\n"
                "People say: «The level is weaker there.» You hear an inaccuracy: the best of these teams ranked "
                "among Europe's top three in its prime, while others played in continental finals. Level is cyclical "
                "— and that cycle is as interesting to you as any constantly elite club.\n\n"
                "The risk: the nostalgic lens magnifies past achievements and minimizes current problems. An Eastern "
                "European club today is often very different from what that same club was twenty years ago. Look at "
                "what's happening now: what state is the academy in, does the club have a direction, what new is it "
                "offering the game."
            ),
        },
        'Большой театр': {
            'body': (
                "Финальный свисток — и ты думаешь не только о счёте, а о том что напишут завтра. Как этот матч войдёт "
                "в историю клуба. Какие слова подберут журналисты. Именно этот слой — нарративный, почти литературный "
                "— тебя интересует не меньше игры.\n\n"
                "Для тебя клуб — это история которую рассказывают сезон за сезоном. Столичный клуб с вечным ожиданием "
                "титула. Гранд, взявший требл и тут же сорвавшийся вниз. Команда, навсегда оставшаяся единственным "
                "чемпионом Европы в своей стране. Клуб, чей тренер однажды переписал тактику всего континента. Эти "
                "клубы производят нарратив в промышленных масштабах.\n\n"
                "Окружающие говорят: «Ты смотришь футбол как кино». Ты не возражаешь. Великий матч и есть кино — с "
                "персонажами, ставками, неожиданными поворотами и финалом который помнят десятилетиями. Атлетический "
                "результат — одно. Эмоциональная история вокруг него — другое.\n\n"
                "Риск — нарратив иногда больше реального. Клуб может быть красиво рассказан — и при этом посредственно "
                "выступать. Следи за тем чтобы восхищение историей не подменяло понимание что происходит прямо сейчас. "
                "Хорошая история — не индульгенция за плохой сезон."
            ),
            'body_en': (
                "The final whistle — and you're thinking not just about the scoreline, but about what they'll write "
                "tomorrow. How this match will enter the club's history. What words the journalists will find. That "
                "layer — narrative, almost literary — interests you as much as the game itself.\n\n"
                "For you a club is a story told season by season. A capital-city side with its eternal wait for a "
                "title. A giant that won the treble and then plunged straight back down. A team that remains, forever, "
                "its country's only European champion. A club whose coach once rewrote the tactics of an entire "
                "continent. These clubs produce narrative on an industrial scale.\n\n"
                "People say: «You watch football like cinema.» You don't argue. A great match is cinema — with "
                "characters, stakes, unexpected turns, and an ending remembered for decades. The athletic result is "
                "one thing. The emotional story around it is another.\n\n"
                "The risk: narrative can be larger than reality. A club can be beautifully told — and simultaneously "
                "perform at a mediocre level. Watch for the moment when admiration for the story stops you from seeing "
                "what's actually happening right now. A good story isn't an indulgence for a bad season."
            ),
        },
        'Горячее море': {
            'body': (
                "Тебя цепляет не размер бюджета, а температура трибун. Клуб с десятками чемпионств в своей лиге для "
                "тебя не менее значим, чем тот у кого пятнадцать Лиг чемпионов. Доминирование в своём контексте — "
                "тоже форма величия, и ты это видишь там где другие пожимают плечами.\n\n"
                "За этим стоит убеждённость что мировой футбол больше чем пять западноевропейских лиг. Африканский "
                "гранд, бравший свой континентальный кубок чемпионов десять раз — это не «другой уровень», это другое "
                "измерение. Турецкие и греческие клубы поднимали над головой европейские трофеи — Кубок УЕФА, "
                "Суперкубок, Лигу конференций. Эти клубы существуют не в тени, а в своём собственном свете.\n\n"
                "Окружающие говорят: «Но это же не топ-уровень». Ты слышишь в этом провинциализм. Футбол планеты — "
                "это не только пара богатейших лиг. Ты ценишь способность видеть шире и замечать где горит настоящий "
                "огонь а не только телевизионный прожектор.\n\n"
                "Риск — увлечённость аутентичностью может привести к переоценке. Не все клубы за пределами «топ-5» "
                "одинаково интересны. Честный интерес требует понимания: ты ценишь конкретный клуб за конкретные "
                "причины, или просто за то что он не мейнстримный?"
            ),
            'body_en': (
                "What grips you isn't budget size — it's the temperature of the stands. A club with dozens of "
                "championships in its own league is no less significant to you than one with fifteen UCL titles. "
                "Dominating within your own context is also a form of greatness, and you see it where others "
                "shrug.\n\n"
                "Behind this is a conviction that world football is larger than five western European leagues. An "
                "African giant that won its continental champions cup ten times — that's not «a different level,» "
                "it's a different dimension. Turkish and Greek clubs have lifted European trophies over their heads — "
                "the UEFA Cup, the Super Cup, the Conference League. These clubs don't exist in someone's shadow — "
                "they have their own light.\n\n"
                "People say: «It's not top-level football.» You hear provincialism in that. The planet's football is "
                "not just a couple of the richest leagues. You value the ability to look wider and notice where real "
                "fire burns, not just where the television spotlight points.\n\n"
                "The risk: enthusiasm for authenticity can lead to overvaluation. Not all clubs outside the top 5 are "
                "equally interesting. Honest engagement requires a real question: do you value a specific club for "
                "specific reasons, or just because it isn't mainstream?"
            ),
        },
        'Крепкие корни': {
            'body': (
                "Клуб может не доминировать в Лиге чемпионов — и всё равно быть великим. Для тебя этот тезис не "
                "компромисс, не утешительный приз. Это позиция: величие клуба не тождественно его трансферному "
                "бюджету.\n\n"
                "Тебя привлекает идентичность как самостоятельная ценность. Шотландский клуб, выигравший Кубок Европы "
                "составом целиком из местных парней, рождённых в радиусе нескольких миль от стадиона. Балканский "
                "гранд, поднявший главный европейский трофей и вернувшийся с ним домой. Португальская академия, "
                "воспитавшая мировую суперзвезду и выжившая без неё. Клуб с полусотней чемпионств, существующий в "
                "системе где деньги распределены иначе — и всё равно великий именно потому что велик в своей "
                "системе.\n\n"
                "Окружающие говорят: «Это же слабые лиги». Ты спокойно отвечаешь: тот самый Кубок Европы взяла "
                "команда из «слабой» лиги, а не один из грандов-фаворитов. Уровень лиги и величие клуба — не одно и "
                "то же. Некоторые клубы существуют в своём пространстве и этот масштаб — их честный масштаб.\n\n"
                "Риск — апелляция к идентичности иногда становится защитным экраном от честного взгляда на сегодняшний "
                "уровень. Великое прошлое реально. Но что клуб делает прямо сейчас — тоже важно. Цени историю и "
                "одновременно смотри честно на настоящее."
            ),
            'body_en': (
                "A club can fail to dominate the Champions League — and still be great. For you that isn't a "
                "compromise, not a consolation prize. It's a position: a club's greatness isn't identical to its "
                "transfer budget.\n\n"
                "What draws you is identity as a value in itself. A Scottish club that won the European Cup with a "
                "squad made up entirely of local lads born within a few miles of the ground. A Balkan giant that "
                "lifted the main European trophy and brought it home. A Portuguese academy that produced a global "
                "superstar and survived without him. A club with fifty-odd titles that exists in a system where money "
                "is distributed differently — and remains great precisely because it is great within its own "
                "system.\n\n"
                "People say: «Those are weaker leagues.» You answer calmly: that very European Cup was won by a team "
                "from a «weak» league, not by one of the favored giants. League level and club greatness aren't the "
                "same thing. Some clubs exist in their own space, and that scale is their honest scale.\n\n"
                "The risk: appeals to identity can become a protective screen from honest appraisal of today's level. "
                "A great past is real. But what the club is doing right now also matters. Value the history and "
                "simultaneously look honestly at the present."
            ),
        },
        'Другой меридиан': {
            'body': (
                "Ты называешь клуб — и в ответ иногда тишина или «а, это который?». Это не смущает тебя. Это часть "
                "позиции: великое распределено по миру неравномерно, и именно там где другие не смотрят часто лежит "
                "что-то интересное.\n\n"
                "Тебя захватывает зазор между реальным достижением клуба и его публичным признанием. Французский клуб, "
                "взявший семь чемпионств подряд — национальный рекорд, о котором говорят меньше чем он заслуживает. "
                "Южноамериканские гранды, бравшие главный континентальный кубок по пять и по три раза. Это не "
                "маленькие достижения, просто они не переведены на язык большого нарратива.\n\n"
                "Окружающие говорят: «Ты специально берёшь не очевидных». Не специально — ты просто замечаешь разрыв "
                "между тем что есть и тем что видят. Когда этот разрыв большой, хочется его закрыть.\n\n"
                "Честный риск: проверь мотив. Ты ценишь этот клуб за конкретные причины — или приятно занимать позицию "
                "меньшинства? Оба варианта существуют. В первом случае ты можешь объяснить через конкретные матчи и "
                "факты. Во втором — только настаивать. Разница между этими двумя позициями существенная и для тебя "
                "самого."
            ),
            'body_en': (
                "You name a club — and sometimes you get silence in response, or «which one is that?» This doesn't "
                "bother you. It's part of the position: greatness is distributed unevenly across the world, and "
                "exactly where others aren't looking is often where something interesting lives.\n\n"
                "What grips you is the gap between a club's real achievement and its public recognition. A French club "
                "that won seven league titles in a row — a national record discussed far less than it deserves. South "
                "American giants that took the main continental cup five times and three times over. These aren't "
                "small achievements — they just haven't been translated into the language of big narrative.\n\n"
                "People say: «You deliberately pick non-obvious clubs.» Not deliberately — you just notice the gap "
                "between what exists and what people see. When that gap is large, you want to close it.\n\n"
                "Honest risk: check the motive. Do you value this club for specific reasons — or is it pleasant to "
                "occupy the minority position? Both exist. In the first case you can explain through specific matches "
                "and facts. In the second, you can only insist. The difference between those two positions matters to "
                "you too."
            ),
        },
    },
    'basketball_teams': {
        'Тринадцатый раунд': {
            'body': (
                "Ты помнишь точно где был когда это случилось. Не конкретный бросок в финале — именно момент когда "
                "всё казалось потеряно и вдруг оказалось нет. Это «вдруг оказалось нет» разблокирует в тебе что-то "
                "чего ровное доминирование никогда не разблокирует.\n\n"
                "Тебя цепляет победа вопреки — не победа сильного. Команды которые выиграли когда никто не верил — "
                "без единой суперзвезды, на одной командной защите; с полусломанным лидером, тащившим на "
                "морально-волевых; перевернув безнадёжную серию со счёта 1-3 — они доказывают про природу команды "
                "то, что готовый суперклуб не может доказать по определению.\n\n"
                "Окружающие говорят: «Ты специально ищешь андердогов». Не специально — просто когда побеждает тот кто "
                "не должен был, ты понимаешь игру иначе. Это не злорадство. Это про то что баскетбол непредсказуем, "
                "и именно в этой непредсказуемости его ценность.\n\n"
                "Пересмотр «невозможных побед» иногда скрывает закономерность. Андердог редко берёт титул случайно — "
                "за чудом обычно стоит лучшая защита лиги или ростер, оказавшийся глубже в нужный месяц. Не "
                "романтизируй хаос — изучай механику чуда. Восхищение станет богаче."
            ),
            'body_en': (
                "You remember exactly where you were when it happened. Not a specific finals shot — the moment "
                "everything seemed lost and then it wasn't. That «and then it wasn't» unlocks something in you that "
                "steady dominance never reaches.\n\n"
                "What grips you is winning against — not winning as the expected winner. Teams that took it all when "
                "nobody believed — without a single superstar, on team defense alone; with a half-broken leader "
                "dragging them by sheer will; flipping a hopeless 1-3 series — they prove something about what a team "
                "can be that an assembled superclub simply cannot.\n\n"
                "People say: «You deliberately look for underdogs.» Not deliberately — it's just that when the wrong "
                "team wins, you understand the game differently. Not schadenfreude. It's that basketball is "
                "unpredictable, and that unpredictability is where its real value lives.\n\n"
                "Revisiting «impossible wins» sometimes hides the pattern beneath them. An underdog rarely takes the "
                "title by accident — behind the miracle there's usually the league's best defense or a roster that "
                "turned out deeper at the right month. Don't romanticize chaos — study the mechanics of the miracle. "
                "Your admiration will get richer."
            ),
        },
        'Своя крепость': {
            'body': (
                "Чем меньше твой город на баскетбольной карте, тем важнее команда для него. В маленьком баскетбольном "
                "городе не говорят «болею за клуб» — просто говорят «болею за наших». Разница маленькая, но она про "
                "что-то совсем другое, чем поддержка клуба.\n\n"
                "Ты ценишь верность как отдельную валюту. Игрок который мог уйти в большой рынок и остался — для тебя "
                "дороже любого приглашённого рекрута. Звезда, проведшая полтора десятка лет в одном маленьком городе "
                "вместо переезда за титулом — это не решение по контракту, это позиция. Именно такие истории тебе "
                "важнее любых чемпионств в других командах.\n\n"
                "Окружающие говорят: «Но они же никогда не выиграют кольцо с этим ростером». Ты слышишь это как "
                "мнение — не как аргумент. Кольцо одно на тридцать команд, а болельщиков тридцать раз по тысячам. "
                "Кто-то должен болеть за своих просто потому что они свои.\n\n"
                "Верность иногда переходит в отрицание реальности. Если команда годами топчется на месте — стоит "
                "смотреть честно: это процесс с перспективой или организация без направления? Верность клубу не должна "
                "мешать задавать жёсткие вопросы менеджменту. Это тоже форма уважения."
            ),
            'body_en': (
                "The smaller your city on the basketball map, the more the team matters to it. In a small basketball "
                "town, people don't say «I root for the club» — they say «I root for ours.» A small difference, but "
                "it's about something entirely different from club support.\n\n"
                "You value loyalty as its own currency. A player who could have gone to a big market and stayed is "
                "worth more to you than any recruited star. A star who spent fifteen years in one small city instead "
                "of chasing a ring elsewhere — that isn't a contract decision, it's a statement. Stories like that "
                "matter more to you than championships in other teams.\n\n"
                "People say: «But they'll never win a ring with this roster.» You hear that as an opinion. Not an "
                "argument. There's one ring for thirty teams, and thirty times thousands of fans. Someone has to root "
                "for their team simply because it's theirs.\n\n"
                "Loyalty can cross into denial of reality. If a franchise has been stagnant for years — it's worth "
                "looking honestly: is this a process with a direction, or an organization going nowhere? Loyalty to a "
                "club shouldn't get in the way of asking hard questions of management. That's also a form of respect."
            ),
        },
        'Родные цвета': {
            'body': (
                "Клубный баскетбол ты можешь выбрать — национальный нет. Сборная это не предпочтение, это "
                "принадлежность. Когда выходит твоя страна или команда с которой ты себя отождествляешь — тебя не "
                "спрашивают болеешь ли. Просто болеешь.\n\n"
                "За национальной командой ты следишь иначе: каждый игрок несёт не только себя, но и нарратив откуда "
                "он пришёл. Один — отлаженную европейскую школу больших, умеющих пасовать. Другой — уличную злость "
                "своего континента, где за мяч бьются как за жизнь. Третий — балканское чувство игры, где пас важнее "
                "эффектности. В сборных читается культура, и именно это делает каждый матч тяжелее клубного.\n\n"
                "Окружающие иногда удивляются: «Ты вообще следишь за клубным баскетболом?». Следишь. Но когда "
                "чемпионат мира или Олимпиада — ты превращаешься в другого болельщика. Интенсивность другая, ставки "
                "другие. Это про что-то большее чем спорт — про идентичность которую команда несёт на площадку.\n\n"
                "Национальный баскетбол — редкое событие. Между Олимпиадами и чемпионатами мира два-четыре года. Если "
                "ты почти не следишь за клубным баскетболом в промежутке — ты пропускаешь большую часть жизни игры. "
                "Попробуй найти клуб который был бы тебе важен и в межсезонье сборной."
            ),
            'body_en': (
                "Club basketball is something you can choose. National basketball isn't. A national team isn't a "
                "preference — it's a belonging. When your country or the team you identify with takes the floor, "
                "nobody asks whether you're rooting. You just are.\n\n"
                "You follow national teams differently: every player carries not just himself but the narrative of "
                "where he came from. One brings a polished European school of passing big men. Another brings the "
                "street fury of his continent, where they fight for the ball like it's life. A third brings a Balkan "
                "feel for the game, where the pass matters more than the flash. In national teams you read culture, "
                "and that's what makes each game feel heavier than a club match.\n\n"
                "People sometimes ask: «Do you even follow club basketball?» You do. But when the World Cup or "
                "Olympics arrives, you become a different fan. The intensity is different, the stakes are different. "
                "It's about something larger than sport — an identity the team carries onto the floor.\n\n"
                "National basketball is an infrequent event. Between Olympics and World Cups, it's two to four years. "
                "If you barely follow club basketball in between, you're missing most of the game's life. Try finding "
                "a club that would matter to you during the national team's offseason too."
            ),
        },
        'Вечный болельщик': {
            'body': (
                "«Когда же они наконец выиграют?» — тебе об этом говорят регулярно. У тебя есть ответ, но ты его "
                "давно перестал озвучивать — потому что объяснить почему болеешь за команду которая страдает сложнее, "
                "чем объяснить почему не бросаешь. Это разные вопросы.\n\n"
                "Болеть за вечного аутсайдера — особое умение. Ты выработал способность находить смысл в отдельных "
                "моментах сезона, а не только в его финале. Великолепный четвёртый квартал в проходном матче может "
                "быть важнее для тебя чем финальная игра команды которая «должна» побеждать. У тебя другая шкала "
                "ценности.\n\n"
                "Окружающие говорят: «Переходи на большой клуб который реально берёт титулы». Ты слышишь этот совет "
                "уже много лет. За ним стоит идея что поддержка команды — инвестиция которая должна окупаться. Для "
                "тебя это не инвестиция. Это что-то другое — ближе к идентичности которая не меняется от "
                "результата.\n\n"
                "Терпение — добродетель, но оно может маскировать низкие ожидания: и от команды, и от болельщицкого "
                "опыта. Если твой клуб годами не развивается в правильном направлении — стоит понять: это честный "
                "rebuild или плохой менеджмент? Верность не исключает критики руководства. Настоящая верность её "
                "требует."
            ),
            'body_en': (
                "«When are they finally going to win?» — people ask you this regularly. You have an answer, but you "
                "stopped voicing it a long time ago. Explaining why you root for a suffering team is harder than "
                "explaining why you haven't quit. Those are different questions.\n\n"
                "Rooting for a perennial outsider is a specific skill. You've developed the ability to find meaning "
                "in individual moments of the season, not just in the final outcome. A brilliant fourth quarter in a "
                "throwaway game can matter more to you than the championship series of a team that's «supposed to» "
                "win. You work on a different scale of value.\n\n"
                "People say: «Switch to a big club that actually wins titles.» You've been getting this advice for "
                "years. Behind it is the idea that rooting for a team is an investment that should pay off. For you it "
                "isn't an investment. It's something different — closer to an identity that doesn't change with the "
                "standings.\n\n"
                "Patience is a virtue, but it can mask low expectations — both of the team and of the fan experience. "
                "If your club hasn't been moving in the right direction for years — it's worth distinguishing: is "
                "this an honest rebuild, or bad management? Loyalty doesn't exclude criticizing leadership. True "
                "loyalty actually requires it."
            ),
        },
        'Одна звезда': {
            'body': (
                "Когда обсуждают команду — ты всё равно говоришь про человека. Как он движется, что делает за две "
                "секунды до броска, какой у него игровой интеллект — это для тебя и есть баскетбол в первую очередь. "
                "Команда — контекст. Звезда — причина включать трансляцию.\n\n"
                "Тебя захватывает индивидуальное мастерство как отдельный вид искусства. Элитный скорер с мячом в "
                "пике формы — это хореография. Большой, накрывающий всю площадку в защите — страсть в движении. "
                "Атлет, разгоняющийся через всю краску — физика на пределе. Ты ищешь одного человека за которым "
                "хочется следить весь сезон, и команда вокруг — его рамка.\n\n"
                "Окружающие говорят: «Ты болеешь за игрока, а не за команду». Да, и ты не считаешь это упрёком. Когда "
                "суперзвезда переходит в другой клуб — ты сталкиваешься с честным вопросом: ты болельщик города или "
                "болельщик человека? У тебя был ответ. Ты шёл за человеком.\n\n"
                "Привязка к суперзвезде делает тебя уязвимым к межсезонью. Когда любимый игрок уходит или получает "
                "травму — это как прощание. Учись смотреть на команду шире: второй и третий номер определяют исходы "
                "чаще, чем кажется. Тогда ты меньше зависишь от одного контракта."
            ),
            'body_en': (
                "When people talk about the team, you talk about the person. How he moves, what he does two seconds "
                "before the shot, what his basketball IQ looks like — that's basketball first, for you. The team is "
                "context. The star is the reason to turn on the broadcast.\n\n"
                "Individual mastery grips you as its own art form. An elite scorer with the ball at his peak — that's "
                "choreography. A big man blanketing the whole floor on defense — passion in motion. An athlete "
                "accelerating through the entire paint — physics at its limit. You're looking for one person you want "
                "to watch for an entire season, and the team around him is the frame.\n\n"
                "People say: «You root for the player, not the team.» Yes, and you don't take that as criticism. When "
                "a superstar moves to another club, you face an honest question: are you a fan of the city or a fan "
                "of the person? You had an answer. You went with the person.\n\n"
                "Being attached to a superstar makes you vulnerable to the offseason. When the player you love leaves "
                "or gets hurt, it feels like a farewell. Learn to look at teams more broadly: the second and third "
                "options determine outcomes more often than it seems. Then you depend less on a single contract."
            ),
        },
        'Большая сцена': {
            'body': (
                "Составление команды для тебя почти интереснее самой игры. Когда начинается летний рынок свободных "
                "агентов — ты следишь за ним как за политическими выборами. Кто куда перейдёт, кто откажет, кто "
                "согласится за меньше — это тоже баскетбол, просто без мяча.\n\n"
                "Тебе нужны не просто победы — тебе нужны истории. Три суперзвезды под одной крышей, большой переезд, "
                "скандальный трейд — это жанр который ты любишь независимо от финального результата. Процесс сборки "
                "команды для тебя самостоятельный нарратив, а не просто прелюдия к сезону.\n\n"
                "Окружающие говорят: «Ты болеешь за бренд, а не за команду». Честно — немного да. Но ты бы добавил: "
                "крупные рынки создают самые важные нарративы в лиге, и это не случайность. Легендарная арена в "
                "центре мегаполиса — это не просто трибуны. Это контекст в котором история звучит иначе.\n\n"
                "Суперкоманды рассыпаются быстрее ожиданий. Максимальный потенциал без химии — это красивый "
                "питч-документ, не чемпионство. Если тебя каждый раз накрывает когда коллектив распадается — это "
                "нормально, но замечай: иногда ты влюблён в идею команды больше чем в реальный коллектив."
            ),
            'body_en': (
                "Roster construction is almost more interesting to you than the games themselves. When the free "
                "agency period starts in summer, you follow it like a political election. Who goes where, who turns "
                "down the offer, who agrees to less — that's basketball too, just without the ball.\n\n"
                "You need more than wins — you need stories. Three superstars under one roof, a dramatic move, a "
                "controversial trade — that's the genre you love regardless of what ultimately happens in June. The "
                "building of the team is its own narrative, not just a warm-up act.\n\n"
                "People say: «You root for the brand, not the team.» Honestly, a little bit yes. But you'd add: large "
                "markets generate the most important storylines in the league, and that's not an accident. A "
                "legendary arena in the heart of a megacity isn't just stands. It's a context where the story sounds "
                "different.\n\n"
                "Superteams collapse faster than expected. Maximum potential without chemistry is a beautiful pitch "
                "deck, not a championship. If the dissolution of a roster hits you every time — that's normal, but "
                "notice: sometimes you've fallen for the idea of the team more than the actual group of people."
            ),
        },
        'Европейский паркет': {
            'body': (
                "Когда американские друзья засыпают — для тебя начинается игра. Евролига стартует в другое время, с "
                "другим темпом и другой тактической культурой. Ты смотришь не потому что нет НБА. Ты смотришь потому "
                "что это другой баскетбол — и тебя устраивают оба.\n\n"
                "Европейский клубный баскетбол заточен на систему, а не на суперзвезду. Одна звезда там не решает — "
                "решают ротация, командная защита, тренерская читаемость ситуации. Для тебя это ближе к чистой форме "
                "командной игры. Финал четырёх — твой аналог Мартовского безумия, только тактически плотнее.\n\n"
                "Окружающие говорят: «Это же не настоящий баскетбол». Ты спокойно отвечаешь: лучшие европейские "
                "разыгрывающие и снайперы последних десятилетий были бы звёздами в НБА. Просто они выбрали другое. "
                "Некоторые — потому что в Европе они могли быть первым номером, а не ролевым.\n\n"
                "Евролига нишевая — сложно найти кому обсудить конкретный матч. Если тебе важно делиться впечатлениями "
                "— ищи комьюнити фанатов именно этого жанра. Одиночный просмотр обедняет опыт. Твой вкус заслуживает "
                "аудитории которая его разделяет."
            ),
            'body_en': (
                "When your American friends are asleep, your games are starting. EuroLeague tips off at a different "
                "hour, at a different pace, with a different tactical culture. You don't watch because there's no NBA "
                "on. You watch because it's a different kind of basketball — and you're fine with both.\n\n"
                "European club basketball is built around the system, not the superstar. One star doesn't decide "
                "games there — rotations, team defense, and the coach's read of the situation do. For you this is "
                "closer to the pure form of team play. The Final Four is your March Madness equivalent, just "
                "tactically denser.\n\n"
                "People say: «That's not real basketball.» You answer calmly: the best European point guards and "
                "shooters of the last few decades would have been stars in the NBA. They just chose differently. Some "
                "because in Europe they could be the first option, not a role player.\n\n"
                "EuroLeague is niche — it's hard to find someone to break down a specific game with. If sharing what "
                "you watch matters to you, find a community of fans who follow the same product. Watching alone "
                "cheapens the experience. Your taste deserves an audience that shares it."
            ),
        },
    },
}


def main():
    dry_run = '--apply' not in sys.argv
    with open(CATEGORIES_PATH, encoding='utf-8') as f:
        cats = json.load(f)
    by_id = {c.get('id'): c for c in cats}

    applied = []
    missing = []
    for cid, arch_map in REWRITES.items():
        c = by_id.get(cid)
        if not c:
            missing.append(f'cat {cid}')
            continue
        for aname, fields in arch_map.items():
            a = next((x for x in c.get('archetypes', []) if x.get('name') == aname), None)
            if not a:
                missing.append(f'[{cid}] archetype «{aname}»')
                continue
            # Convert em-dash -> regular dash (user preference: no em dash)
            a['body'] = fields['body'].replace('—', '-')
            a['body_en'] = fields['body_en'].replace('—', '-')
            applied.append(f'  [{cid}] «{aname}»: body {len(a["body"])} / en {len(a["body_en"])}')

    print(f'REWRITES: {len(applied)}')
    for line in applied:
        print(line)
    if missing:
        print(f'MISSING: {len(missing)}')
        for line in missing:
            print(f'  {line}')

    if dry_run:
        print('\n=== DRY RUN - run with --apply ===')
        sys.exit(0)

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = CATEGORIES_PATH + f'.bak.sport_clubs_names.{ts}'
    shutil.copy(CATEGORIES_PATH, backup_path)
    print(f'\nBackup: {backup_path}')
    with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    print('Saved')


if __name__ == '__main__':
    main()
