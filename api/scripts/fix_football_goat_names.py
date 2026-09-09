# -*- coding: utf-8 -*-
"""Rewrite 3 archetypes of football_goat to remove specific player names
from body text. User reported hybrid synthesis surfaced "Бекхэм" and "Мбаппе"
in their portrait even though they picked Zidane/Ronaldinho/Henry. Root cause:
each archetype body called its trigger players by name; the hybrid synthesizer
splices paragraphs together and leaks non-chosen names.

Long-term: prompt rule added 2026-06-08 forbids name mentions in body.
Short-term: rewrite the 3 archetypes a real user hit (Zidane→Живой огонь,
Ronaldinho→Прожектор, Henry→В граните). Other 5 archetypes left as-is —
flagged for separate sweep.

Run: python3 fix_football_goat_names.py [--apply]
"""
import json, shutil, sys
from datetime import datetime

CATEGORIES_PATH = '/opt/untitled-pick-game-api/data/categories.json'

REWRITES = {
    'В граните': {
        'body': (
            "Когда начинается спор о величии - ты уже знаешь свой ответ. Не потому что не думал. "
            "Именно потому что думал: восемь «Золотых мячей» - это не везение и не рекламная кампания, "
            "это документ. Ты читаешь статистику как судья читает показания - взвешивает и выносит приговор.\n\n"
            "За этим стоит убеждённость что в спорте объективность возможна. Ощущения у всех разные - "
            "зато рекорды одинаковы для каждого. Количество наград, голы в решающих матчах, стабильность на "
            "протяжении полутора десятка лет - для тебя это единственная честная шкала. Статистика не "
            "подстраивается под то кому ты симпатизируешь.\n\n"
            "Окружающие говорят: «Ты просто болеешь за победителей». Ты мог бы обидеться - но не обижаешься. "
            "Потому что болеть за трофеи и болеть за историю это разные вещи. Один следит за чемпионами "
            "этого сезона. Ты следишь за теми кто переопределил что значит быть лучшим в своём деле - "
            "на протяжении поколения, а не одного яркого года.\n\n"
            "Риск - зависнуть на одном аргументе и перестать слышать остальные. Главный приз зависит от состава "
            "жюри, от доступности клуба к медиа, от того насколько звёздными были конкретные годы. Оставь один "
            "честный вопрос без ответа: если бы тот же игрок родился на тридцать лет раньше - что было бы иначе? "
            "Не чтобы изменить свой ответ - чтобы он стал точнее."
        ),
        'body_en': (
            "When the GOAT debate starts - you already know your answer. Not because you haven't thought about it. "
            "Precisely because you have: eight Ballons d'Or isn't luck and isn't marketing - it's a document. "
            "You read statistics the way a judge reads testimony - weighs it and rules.\n\n"
            "Behind this is the conviction that objectivity in sport is possible. Feelings differ for everyone - "
            "records are the same for everyone. Number of awards, goals in decisive matches, consistency across "
            "fifteen-plus years - for you this is the only honest scale. Statistics don't shift to suit whoever "
            "you happen to like.\n\n"
            "People say: «You just root for winners». You could take offense - you don't. Because rooting for "
            "trophies and rooting for history are different things. One person follows this season's champions. "
            "You follow the ones who redefined what being the best at your craft means - across a generation, "
            "not just one bright year.\n\n"
            "The risk - to lock onto one argument and stop hearing the rest. The biggest prize depends on the jury, "
            "on how much media access the club had, on how stellar a given year's competition was. Leave one honest "
            "question unanswered: if the same player had been born thirty years earlier - what would be different? "
            "Not to change your answer - to make it more precise."
        ),
    },
    'Живой огонь': {
        'body': (
            "Четвёртый повтор - и ты всё равно не можешь объяснить как это физически возможно. Мяч полетел "
            "не так, тело прошло там где пространства не было. Именно это ощущение - что видишь невозможное "
            "прямо сейчас - ты ищешь как доказательство. Не цифры. Это.\n\n"
            "Ты убеждён что статистика описывает результат но не описывает опыт. Когда болельщики противоположных "
            "команд несут одного игрока на руках после матча - это не субъективщина, это измеримый факт. "
            "Воздействие на зрителя так же реально как любой рекорд в таблице - просто труднее оцифровать.\n\n"
            "«Это субъективно» - говорят тебе. Ты соглашаешься и добавляешь: одно мнение субъективно. Но когда "
            "миллионы людей в разных странах говорят «я видел и не мог поверить глазам» про одно и то же движение - "
            "это уже данные, а не вкусовщина. Финал, который помнишь по одному движению. Штрафной, в который "
            "никто не поверил. Ты знаешь эти моменты потому что их знают все.\n\n"
            "Художники иногда выигрывают меньше тех кто эффективнее - это честная цена. Риск в другом: если "
            "оценивать всех только через зрелищность, легко недооценить того кто делает одно дело безупречно "
            "сезон за сезоном. Монотонная надёжность тоже форма величия. Просто менее фотогеничная."
        ),
        'body_en': (
            "Fourth replay - and you still can't explain how it's physically possible. The ball moved wrong, "
            "the body went where space wasn't. That feeling - that you're watching the impossible right now - "
            "is what you look for as proof. Not numbers. This.\n\n"
            "You're convinced statistics describe the result but don't describe the experience. When fans of "
            "opposing teams carry one player off the pitch on their shoulders - that isn't subjectivity, it's "
            "a measurable fact. Impact on the viewer is as real as any record on a table - just harder to "
            "quantify.\n\n"
            "«That's subjective» - people tell you. You agree, then add: one opinion is subjective. But when "
            "millions of people in different countries say «I saw it and couldn't believe my eyes» about the same "
            "single movement - that's data, not taste. The final you remember by one touch. The free kick no one "
            "believed in. You know those moments because everyone knows them.\n\n"
            "Artists sometimes win less than the more efficient ones - that's the honest price. The risk is "
            "elsewhere: if you measure everyone only by spectacle, it's easy to undervalue someone who does one "
            "thing flawlessly season after season. Monotonous reliability is also a form of greatness. Just less "
            "photogenic."
        ),
    },
    'Жёлтая майка': {
        'body': (
            "Клубный чемпионат - это работа. Чемпионат мира - это личное. На стадионе два миллиарда человек "
            "смотрят в экраны, у тебя один шанс раз в четыре года, и никакая клубная слава это не заменит. "
            "Ты убеждён: именно здесь проверяется то что нельзя купить трансфером.\n\n"
            "Для тебя высшее достижение - то которое нельзя организовать деньгами. В клуб можно собрать "
            "суперкоманду. За сборную играешь с теми с кем родился в одной стране. Пять чемпионских звёзд на "
            "груди и целые поколения игроков выросших на идее что футбол должен быть и красивым и результативным "
            "одновременно - для тебя не случайность, а доказательство.\n\n"
            "Окружающие говорят: «Ты предвзят к одной стране». Ты пожимаешь плечами. Страна с пятью чемпионствами "
            "мира и традицией производить нападающих мирового уровня каждые десять лет - это не предвзятость, "
            "это статистика которую сложно игнорировать.\n\n"
            "Честный риск - Кубок мира во многом вопрос поколения и жеребьёвки. Один гений в крепкой но не "
            "выдающейся сборной перевешивает - и берёт трофей. Другой игрок мирового класса не выигрывает "
            "никогда, потому что вокруг не сложилось. Если убрать страну происхождения из уравнения и оставить "
            "только то что игрок делал на поле - ответ может оказаться тем же, а может стать другим. "
            "Оба варианта честные."
        ),
        'body_en': (
            "Club football is a job. The World Cup is personal. Two billion people watching screens, you get one "
            "shot every four years, and no club glory replaces it. You're convinced: this is where you measure "
            "what can't be bought with a transfer.\n\n"
            "For you the highest achievement is the one that can't be organized with money. You can assemble a "
            "superteam at a club. For the national team you play with the ones you were born sharing a country "
            "with. Five world-championship stars on the chest and entire generations of players raised on the "
            "idea that football should be beautiful AND effective at the same time - to you that's not an "
            "accident, that's proof.\n\n"
            "People say: «You're biased toward one country». You shrug. A nation with five World Cup titles and "
            "a tradition of producing world-class forwards every ten years - that isn't bias, it's a statistic "
            "hard to ignore.\n\n"
            "Honest risk - the World Cup is largely a question of generation and the draw. One genius in a solid "
            "but not outstanding national side tips the balance - and lifts the trophy. Another world-class player "
            "never wins because the surroundings never line up. If you remove country of origin from the equation "
            "and leave only what the player did on the pitch - the answer might be the same, or it might change. "
            "Both versions are honest."
        ),
    },
    'Железный занавес': {
        'body': (
            "Матч вратаря о котором все молчат после - потому что говорить не о чем. Он вышел, отстоял, ушёл. "
            "Ноль. Газеты пишут про тех кто забил. Для тебя в этом парадоксе спрятана отдельная форма величия: "
            "защищать так, чтобы разговор шёл про других.\n\n"
            "Тебя интересует то что труднее всего измерить - гол который не случился. Атака которую прочитали "
            "до того как она началась. Игрок выходил против лучших нападающих мира двадцать пять лет и выигрывал "
            "это противостояние чаще чем проигрывал. Без хайлайтов, без нарезок - просто потому что был точнее. "
            "Это требует другого вида внимания чем большинство готово отдать.\n\n"
            "«Но защитник не может быть величайшим» - слышишь иногда. Ты понимаешь логику и не соглашаешься. "
            "Это та же логика которая говорит что дирижёр не может быть важнее солиста. Оркестр - система. "
            "Команда - тоже. Тот кто не даёт забить так же меняет исход как тот кто забивает.\n\n"
            "Честный риск: защитников действительно труднее сравнивать через эпохи - правила менялись, скорость "
            "игры менялась, роли менялись. Вратарь шестидесятых и современный вратарь - разные позиции с одним "
            "названием. Это не обесценивает величие - но требует осторожности когда ставишь прямой знак равенства "
            "между эпохами."
        ),
        'body_en': (
            "The goalkeeper match no one talks about afterwards - because there's nothing to say. He came out, "
            "kept the sheet clean, left. Zero. The papers write about who scored. For you in this paradox is "
            "hidden a separate form of greatness: to defend in a way that the conversation goes about others.\n\n"
            "You're interested in what's hardest to measure - the goal that didn't happen. The attack read before "
            "it started. A defender who came out against the world's best strikers for twenty-five years and won "
            "that battle more often than he lost. Without highlights, without compilations - just because he was "
            "more precise. That requires a different kind of attention than most are willing to give.\n\n"
            "«But a defender can't be the greatest» - you sometimes hear. You understand the logic and disagree. "
            "It's the same logic that says a conductor can't be more important than a soloist. An orchestra is a "
            "system. A team is too. The one who doesn't let a goal in changes the outcome as much as the one "
            "who scores.\n\n"
            "Honest risk: defenders are genuinely harder to compare across eras - rules changed, speed of play "
            "changed, roles changed. A goalkeeper from the sixties and a modern goalkeeper - different positions "
            "with the same name. That doesn't cheapen greatness - but it requires care when you put a direct "
            "equals sign between eras."
        ),
    },
    'До нас': {
        'body': (
            "«Ты видел его живьём?» - нет. «Тогда откуда ты знаешь что он великий?» - вот здесь ты останавливаешься. "
            "Потому что ответ сложнее чем кажется: из хроники, из слов тех кто видел, из контекста эпохи. Для тебя "
            "это не менее убедительно чем YouTube-нарезка.\n\n"
            "За этим стоит убеждённость: величие нужно судить в условиях своего времени. Три «Золотых мяча» подряд "
            "в эпоху когда восточная Европа практически не имела доступа к западному голосованию - это другой "
            "вес чем тот же приз сегодня. Голы в финале чемпионата мира и чемпионата Европы в один год - "
            "невозможный сегодня формат. Победа спустя катастрофу которую не должен был пережить никто - часть "
            "истории, а не сноска. Контекст - часть аргумента, а не смягчающее обстоятельство.\n\n"
            "Окружающие говорят: «Раньше уровень был другой». Возможно. Но тогда и нынешние лучшие не забивали "
            "бы столько - поля, мячи, физическая подготовка и медицина были другими для всех. Сравнение через "
            "эпохи всегда сложнее чем кажется. Упрощать его в одну сторону нечестно по отношению к обеим.\n\n"
            "Главный риск - романтизировать прошлое только потому что оно прошлое. Не каждый кто называется "
            "легендой был по-настоящему великим. Тест: если убрать ауру эпохи и оставить только то что игрок "
            "делал на поле - за что конкретно ты его уважаешь? Чем конкретнее ответ - тем честнее позиция."
        ),
        'body_en': (
            "«Did you see him live?» - no. «Then how do you know he was great?» - this is where you stop. "
            "Because the answer is more complicated than it seems: from footage, from the words of those who did "
            "see, from the context of the era. For you that's no less convincing than a YouTube compilation.\n\n"
            "Behind that is a conviction: greatness must be judged in the conditions of its own time. Three "
            "Ballons d'Or in a row in an era when Eastern Europe had almost no access to Western voting carries "
            "a different weight than the same prize today. Goals in the World Cup final AND the European "
            "Championship final in one year - a format impossible today. Victory after a disaster no one should "
            "have survived - part of history, not a footnote. Context is part of the argument, not a mitigating "
            "circumstance.\n\n"
            "People say: «The level used to be different». Maybe. But then today's best wouldn't score that much "
            "either - the pitches, the balls, the conditioning and the medicine were different for everyone. "
            "Comparing across eras is always more complex than it seems. Simplifying it in one direction is "
            "unfair to both.\n\n"
            "The main risk - to romanticize the past just because it's the past. Not everyone called a legend "
            "was truly great. The test: if you strip away the aura of the era and leave only what the player did "
            "on the pitch - what exactly do you respect him for? The more concrete the answer - the more honest "
            "the position."
        ),
    },
    'Другой список': {
        'body': (
            "Один и тот же список. Одни и те же имена. Ты их уважаешь - и всё равно думаешь что список намного "
            "длиннее. Не из желания спорить. Из наблюдения: зазор между реальным влиянием игрока и его нынешней "
            "репутацией иногда очень большой - и тебе интересно почему.\n\n"
            "Для тебя видимость - отдельная переменная которую не всегда учитывают. Семь сезонов на абсолютной "
            "вершине пока травма не оборвала карьеру в 28 лет - это могло быть началом другой истории. "
            "Доминирование без алгоритмов которые разносили бы голы в каждый телефон - другая эпоха внимания. "
            "Решающий гол на 88-й минуте финала Лиги чемпионов - и пенальти после - то что не повторится в одной "
            "карьере дважды. Это задокументированные факты - просто о них говорят реже.\n\n"
            "Окружающие говорят: «Ты специально берёшь не очевидных». Не специально. Ты просто видишь разрыв "
            "между тем что было и тем что помнят. Когда этот разрыв большой - хочется его закрыть. Не ради "
            "спора - ради точности.\n\n"
            "Честный риск: проверь мотив. Ты реально считаешь этого игрока великим по конкретным критериям - или "
            "тебе приятно занимать позицию меньшинства? Это разные вещи. В первом случае ты можешь объяснить "
            "через конкретные матчи и числа. Во втором - только настаивать. Разница важна и для тебя самого."
        ),
        'body_en': (
            "The same list. The same names. You respect them - and still think the list is much longer. Not "
            "from a desire to argue. From observation: the gap between a player's real influence and their current "
            "reputation is sometimes very large - and you're interested in why.\n\n"
            "For you visibility is a separate variable that isn't always accounted for. Seven seasons at the "
            "absolute top before injury cut a career off at 28 - that could've been the start of a different "
            "story. Dominance without algorithms blasting goals into every phone - a different era of attention. "
            "A deciding goal in the 88th minute of a Champions League final - and the penalty after - the kind of "
            "thing that won't repeat twice in one career. These are documented facts - just talked about less.\n\n"
            "People say: «You deliberately pick the non-obvious ones». Not deliberately. You just see the gap "
            "between what was and what's remembered. When that gap is large - you want to close it. Not for the "
            "argument - for the precision.\n\n"
            "Honest risk: check your motive. Do you really consider this player great by concrete criteria - or "
            "do you enjoy taking the minority position? Those are different things. In the first case you can "
            "explain it through specific matches and numbers. In the second - only insist. The difference matters "
            "for you too."
        ),
    },
    'Прожектор': {
        'body': (
            "В зале 80 000 человек. Мяч у него. Стадион замолкает за секунду до того как что-то случится - "
            "потому что все уже знают что что-то случится. Именно это коллективное ожидание ты считаешь отдельным "
            "видом власти над игрой. Не результат - момент до него.\n\n"
            "Для тебя футбол это одновременно спорт и культура. Игрок, который изменил что значит быть футболистом "
            "в мире за пределами поля - расширил саму профессию. Молодое лицо, на которое в финале чемпионата мира "
            "ложится груз больше чем большинство несут за всю карьеру - это тоже часть истории. Влияние таких людей "
            "выходит за пределы таблицы - и ты считаешь это частью их величия, а не отдельной историей.\n\n"
            "Окружающие говорят: «Стиль без содержания». Ты не согласен с постановкой вопроса. Стиль который "
            "заставляет людей смотреть футбол - это содержание. Если игрок делает стадион вставать - это "
            "измеримый эффект, а не украшение к настоящей игре. Аудитория тоже часть аргумента.\n\n"
            "Яркий игрок иногда получает завышенную оценку в пиковые годы - и ею заслоняются те кто брал другим. "
            "Спроси себя: кого из тех кого ты выбираешь ты помнишь через двадцать лет - и за что именно? "
            "Конкретный ответ на конкретный вопрос честнее чем общее восхищение вспышкой."
        ),
        'body_en': (
            "80,000 people in the stands. He has the ball. The stadium goes silent a second before something "
            "happens - because everyone already knows something will happen. That collective anticipation is what "
            "you consider a separate kind of power over the game. Not the result - the moment before it.\n\n"
            "For you football is both sport and culture. A player who changed what being a footballer means in the "
            "world beyond the pitch expanded the profession itself. A young face carrying, in a World Cup final, "
            "a weight bigger than most carry across an entire career - that's also part of the story. The influence "
            "of such people goes beyond the table - and you consider that part of their greatness, not a separate "
            "story.\n\n"
            "People say: «Style without substance». You disagree with the framing. Style that makes people watch "
            "football - is substance. If a player makes the stadium stand up - that's a measurable effect, not "
            "decoration on the real game. The audience is also part of the argument.\n\n"
            "A flashy player sometimes gets overrated in peak years - and overshadows those who won other ways. "
            "Ask yourself: of those you pick, who do you still remember twenty years later - and for what exactly? "
            "A concrete answer to a concrete question is more honest than a general admiration for a flash."
        ),
    },
}


def main():
    dry_run = '--apply' not in sys.argv
    with open(CATEGORIES_PATH, encoding='utf-8') as f:
        cats = json.load(f)

    cat = next((c for c in cats if c.get('id') == 'football_goat'), None)
    if not cat:
        print('football_goat NOT FOUND')
        sys.exit(1)

    changes = []
    for a in cat.get('archetypes', []):
        name = a.get('name', '')
        if name in REWRITES:
            new = REWRITES[name]
            a['body'] = new['body']
            a['body_en'] = new['body_en']
            changes.append(f'  «{name}»: body ({len(new["body"])} chars) + body_en ({len(new["body_en"])} chars)')

    print(f'REWRITES: {len(changes)}')
    for c in changes:
        print(c)

    if dry_run:
        print('\n=== DRY RUN - run with --apply ===')
        sys.exit(0)

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = CATEGORIES_PATH + f'.bak.football_goat_names.{ts}'
    shutil.copy(CATEGORIES_PATH, backup_path)
    print(f'\nBackup: {backup_path}')
    with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    print(f'Saved')


if __name__ == '__main__':
    main()
