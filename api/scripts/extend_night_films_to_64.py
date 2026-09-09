"""
Расширение night_films с 32 до 64. Добавляем 32 фильма-классики разных
настроений (страшное, экшн, гик-приключения, умные комедии, романтика,
большая жизнь). Создаём 12 новых архетипов — по паре на каждое настроение.
Плюс точечно расширяем 3 существующих архетипа, где новые items органично
вписываются.

Все новые items и архетипы — двуязычные (RU + EN).
Категория получает name_en и обновлённый blurb (без устаревшего "16 фильмов")
плюс blurb_en.

Атомарная запись с timestamped backup.
"""
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

# ─────────────────────────────────────────────────────────────────
# CATEGORY-LEVEL FIELDS (added/updated)
# ─────────────────────────────────────────────────────────────────
# Старый blurb говорил "16 фильмов" — устарело. Обновляем.
NEW_BLURB_RU = "Великое кино, которое лучше заходит после полуночи"
NEW_NAME_EN = "Late-night cinema"
NEW_BLURB_EN = "Great films that land better after midnight"

# ─────────────────────────────────────────────────────────────────
# 32 NEW ITEMS (RU + EN)
# ─────────────────────────────────────────────────────────────────
NEW_ITEMS = [
    # ─── Страшное / Horror ─────────────────────────────────────────
    {"id": "exorcist",      "name": "Изгоняющий дьявола",                   "name_en": "The Exorcist",
     "ctx":  "1973 · Фридкин · одержимая девочка",                          "ctx_en":  "1973 · Friedkin · the possessed girl"},
    {"id": "psycho",        "name": "Психо",                                "name_en": "Psycho",
     "ctx":  "1960 · Хичкок · мотель и душевая",                            "ctx_en":  "1960 · Hitchcock · motel and shower"},
    {"id": "alien",         "name": "Чужой",                                "name_en": "Alien",
     "ctx":  "1979 · Скотт · в космосе тебя слышат",                        "ctx_en":  "1979 · Scott · in space, no one hears"},
    {"id": "halloween",     "name": "Хэллоуин",                             "name_en": "Halloween",
     "ctx":  "1978 · Карпентер · Майкл Майерс возвращается",                "ctx_en":  "1978 · Carpenter · Michael Myers returns"},
    {"id": "getout",        "name": "Прочь",                                "name_en": "Get Out",
     "ctx":  "2017 · Пил · ужас в гостях у родителей",                      "ctx_en":  "2017 · Peele · horror at the in-laws'"},
    # ─── Экшн / мачо · Action / macho ──────────────────────────────
    {"id": "godfather",     "name": "Крёстный отец",                        "name_en": "The Godfather",
     "ctx":  "1972 · Коппола · мафия как семья",                            "ctx_en":  "1972 · Coppola · mafia as family"},
    {"id": "pulpfiction",   "name": "Криминальное чтиво",                   "name_en": "Pulp Fiction",
     "ctx":  "1994 · Тарантино · нелинейные истории",                       "ctx_en":  "1994 · Tarantino · nonlinear stories"},
    {"id": "madmax",        "name": "Безумный Макс: Дорога ярости",         "name_en": "Mad Max: Fury Road",
     "ctx":  "2015 · Миллер · постапокалипсис в пыли",                      "ctx_en":  "2015 · Miller · post-apocalypse in dust"},
    {"id": "johnwick",      "name": "Джон Уик",                             "name_en": "John Wick",
     "ctx":  "2014 · Стахельски · ему убили собаку",                        "ctx_en":  "2014 · Stahelski · they killed his dog"},
    {"id": "diehard",       "name": "Крепкий орешек",                       "name_en": "Die Hard",
     "ctx":  "1988 · МакТирнан · небоскрёб и террористы",                   "ctx_en":  "1988 · McTiernan · skyscraper and terrorists"},
    # ─── Гик / приключения · Geek / adventure ──────────────────────
    {"id": "matrix",        "name": "Матрица",                              "name_en": "The Matrix",
     "ctx":  "1999 · Вачовски · красная или синяя",                         "ctx_en":  "1999 · Wachowskis · red pill or blue"},
    {"id": "empire",        "name": "Звёздные войны: Империя наносит ответный удар",  "name_en": "Star Wars: The Empire Strikes Back",
     "ctx":  "1980 · Кершнер · «я твой отец»",                              "ctx_en":  "1980 · Kershner · \"I am your father\""},
    {"id": "lotr",          "name": "Властелин колец: Возвращение короля",  "name_en": "The Lord of the Rings: The Return of the King",
     "ctx":  "2003 · Джексон · одно кольцо в Мордор",                       "ctx_en":  "2003 · Jackson · one ring to Mordor"},
    {"id": "backtofuture",  "name": "Назад в будущее",                      "name_en": "Back to the Future",
     "ctx":  "1985 · Земекис · ДеЛореан и парадоксы",                       "ctx_en":  "1985 · Zemeckis · DeLorean and paradoxes"},
    {"id": "darkknight",    "name": "Тёмный рыцарь",                        "name_en": "The Dark Knight",
     "ctx":  "2008 · Нолан · Бэтмен против Джокера",                        "ctx_en":  "2008 · Nolan · Batman vs the Joker"},
    {"id": "spiritedaway",  "name": "Унесённые призраками",                 "name_en": "Spirited Away",
     "ctx":  "2001 · Миядзаки · мир духов",                                 "ctx_en":  "2001 · Miyazaki · the spirit world"},
    {"id": "gladiator",     "name": "Гладиатор",                            "name_en": "Gladiator",
     "ctx":  "2000 · Скотт · «отомщу при жизни или после»",                 "ctx_en":  "2000 · Scott · \"in this life or the next\""},
    # ─── Умные комедии · Smart comedies ───────────────────────────
    {"id": "lebowski",      "name": "Большой Лебовски",                     "name_en": "The Big Lebowski",
     "ctx":  "1998 · Коэны · Дюдя, ковёр, боулинг",                         "ctx_en":  "1998 · Coens · the Dude, the rug, bowling"},
    {"id": "knivesout",     "name": "Достать ножи",                         "name_en": "Knives Out",
     "ctx":  "2019 · Джонсон · детектив-фарс",                              "ctx_en":  "2019 · Johnson · detective farce"},
    {"id": "hotfuzz",       "name": "Типа крутые легавые",                  "name_en": "Hot Fuzz",
     "ctx":  "2007 · Райт · экшн-пародия в деревне",                        "ctx_en":  "2007 · Wright · action parody in a village"},
    {"id": "somelikeit",    "name": "В джазе только девушки",               "name_en": "Some Like It Hot",
     "ctx":  "1959 · Уайлдер · парни в женском оркестре",                   "ctx_en":  "1959 · Wilder · guys in a women's band"},
    # ─── Романтика · Romance ──────────────────────────────────────
    {"id": "casablanca",    "name": "Касабланка",                           "name_en": "Casablanca",
     "ctx":  "1942 · Кёртиц · «вот смотрю на тебя, малыш»",                 "ctx_en":  "1942 · Curtiz · \"here's looking at you, kid\""},
    {"id": "beforesunrise", "name": "Перед рассветом",                      "name_en": "Before Sunrise",
     "ctx":  "1995 · Линклейтер · одна ночь в Вене",                        "ctx_en":  "1995 · Linklater · one night in Vienna"},
    {"id": "lalaland",      "name": "Ла-Ла Ленд",                           "name_en": "La La Land",
     "ctx":  "2016 · Шазел · джаз и мечта в Лос-Анджелесе",                 "ctx_en":  "2016 · Chazelle · jazz and a dream in LA"},
    {"id": "princessbride", "name": "Принцесса-невеста",                    "name_en": "The Princess Bride",
     "ctx":  "1987 · Райнер · сказка с фехтованием",                        "ctx_en":  "1987 · Reiner · fairy tale with fencing"},
    {"id": "citylights",    "name": "Огни большого города",                 "name_en": "City Lights",
     "ctx":  "1931 · Чаплин · бродяга и слепая девушка",                    "ctx_en":  "1931 · Chaplin · the tramp and the blind girl"},
    # ─── Большая жизнь · A whole life ─────────────────────────────
    {"id": "forrest",       "name": "Форрест Гамп",                         "name_en": "Forrest Gump",
     "ctx":  "1994 · Земекис · «жизнь как коробка конфет»",                 "ctx_en":  "1994 · Zemeckis · \"life is like a box of chocolates\""},
    {"id": "shawshank",     "name": "Побег из Шоушенка",                    "name_en": "The Shawshank Redemption",
     "ctx":  "1994 · Дарабонт · 20 лет молотком",                           "ctx_en":  "1994 · Darabont · 20 years with a hammer"},
    {"id": "greenmile",     "name": "Зелёная миля",                         "name_en": "The Green Mile",
     "ctx":  "1999 · Дарабонт · великан в камере смертников",               "ctx_en":  "1999 · Darabont · a giant on death row"},
    {"id": "rocky",         "name": "Рокки",                                "name_en": "Rocky",
     "ctx":  "1976 · Эвилдсен · парень из Филадельфии",                     "ctx_en":  "1976 · Avildsen · the kid from Philly"},
    {"id": "socialnetwork", "name": "Социальная сеть",                      "name_en": "The Social Network",
     "ctx":  "2010 · Финчер · как делают Фейсбук",                          "ctx_en":  "2010 · Fincher · how Facebook gets made"},
    {"id": "schindlerslist","name": "Список Шиндлера",                      "name_en": "Schindler's List",
     "ctx":  "1993 · Спилберг · одна жизнь спасает мир",                    "ctx_en":  "1993 · Spielberg · one life saves the world"},
]

# ─────────────────────────────────────────────────────────────────
# Trigger additions to existing archetypes (where new items fit)
# Existing archetypes will get name_en/body_en backfilled by a separate script.
# ─────────────────────────────────────────────────────────────────
TRIGGER_ADDITIONS = {
    "Холодный сай-фай":    ["matrix", "alien"],
    "Тёмная психология":   ["darkknight"],
    "Сюжет-головоломка":   ["pulpfiction", "getout"],
}

# ─────────────────────────────────────────────────────────────────
# 12 NEW ARCHETYPES — pair per genre. Each has full RU + EN body.
# Body: 4 paragraphs (\n\n separated): who you are / what it means /
# how others see you / what to know.
# ─────────────────────────────────────────────────────────────────
NEW_ARCHETYPES = [
    # ─── Страшное × 2 ──────────────────────────────────────────────
    {
        "name": "Психологический ужас",
        "name_en": "Psychological dread",
        "body": (
            "Тебя пугает не монстр в шкафу, а голос за дверью, которому ты не можешь "
            "поверить. «Психо» в душевой; гипноз у вежливой матери в «Прочь». Ты любишь, "
            "когда страх растёт медленно и логично, и в финале выясняется, что монстр — "
            "это обычный человек в обычной комнате.\n\n"
            "Это работает потому, что ты доверяешь идее больше, чем спецэффекту. Ужас, "
            "построенный на правдоподобной психологии, остаётся с тобой надолго: ты "
            "ловишь себя на том, что неделю смотришь на улыбающихся людей и думаешь, "
            "что они скрывают. Хороший хоррор для тебя — это сомнение, а не вздрагивание.\n\n"
            "Окружающие иногда говорят: «там же ничего страшного не происходит». Для "
            "тебя — наоборот, страшнее всего тогда, когда ещё ничего не произошло. "
            "Ожидание, разговор за чаем, вежливый сосед — вот настоящий хоррор. Кровь и "
            "крики тебя скорее отвлекают от того, что делает фильм действительно жутким.\n\n"
            "Что стоит знать: твой жанр требует терпения. Если ставишь Хичкока на фоне, "
            "ничего не сработает — он построен на тишине и точных паузах. Дай ему всё "
            "внимание. И не путай психологический ужас с медлительностью: это разные вещи."
        ),
        "body_en": (
            "What scares you is not the monster in the closet — it's the voice on the "
            "other side of the door that you can't quite trust. \"Psycho\" in the shower; "
            "the polite mother performing hypnosis in \"Get Out\". You love when fear "
            "grows slowly and logically, and the monster turns out to be an ordinary "
            "person in an ordinary room.\n\n"
            "This works because you trust an idea more than a special effect. Horror "
            "built on credible psychology stays with you: you catch yourself for a week "
            "looking at smiling people, wondering what they're hiding. Good horror, for "
            "you, is doubt — not a startle.\n\n"
            "Other people sometimes say: \"but nothing scary even happens\". For you it's "
            "the opposite — the scariest moment is the one before anything happens. "
            "The waiting, the polite tea conversation, the friendly neighbor — that's "
            "the real horror. Blood and screams actually distract you from what makes a "
            "film truly disturbing.\n\n"
            "What's worth knowing: your genre needs patience. If you put Hitchcock on in "
            "the background, nothing works — he is built on silence and exact pauses. "
            "Give him your full attention. And don't confuse psychological dread with "
            "slowness: those are different things."
        ),
        "triggers": ["psycho", "getout"]
    },
    {
        "name": "Монстр под кроватью",
        "name_en": "Monster under the bed",
        "body": (
            "Тебе нужен страх с телом. Не «возможно, кто-то на чердаке», а конкретный "
            "кто-то — с зубами, дыханием, поступью. Майкл Майерс молча идёт по улице; "
            "«Чужой» вылупляется в столовой; девочка в «Изгоняющем» поворачивает голову "
            "на 180 градусов. Это и есть твоё кино — где ужас явный.\n\n"
            "Это работает потому, что для тебя страх — физическое переживание. Ты "
            "любишь, когда тело откликается: руки сжимают подлокотники, дыхание "
            "сбивается, ты буквально подпрыгиваешь. После такого фильма ты чувствуешь "
            "себя живее, чем после тихого артхауса. Это адреналин в чистом виде.\n\n"
            "Окружающие удивляются: «как ты можешь это смотреть, мне даже от трейлера "
            "страшно». Для тебя в этом и смысл — ты хочешь именно сильную реакцию. И ты "
            "понимаешь разницу между качественным жанром и дешёвым гором: тебе нужен "
            "страх, а не отвращение.\n\n"
            "Что стоит знать: лучшие фильмы этой категории работают в темноте, со "
            "звуком, на большом экране. Не порти впечатление светом и паузами. И смотри "
            "их с теми, кто тоже любит — иначе вместо общего ужаса будут чьи-то жалобы."
        ),
        "body_en": (
            "You want fear with a body. Not \"maybe someone's in the attic\" but a "
            "specific someone — with teeth, breathing, footsteps. Michael Myers walking "
            "silently down the street; the \"Alien\" hatching in the dining room; the "
            "girl in \"The Exorcist\" turning her head 180 degrees. That's your cinema — "
            "where horror is visible.\n\n"
            "This works because for you fear is physical. You love when the body "
            "responds: hands gripping armrests, breathing knocked out, an actual jump in "
            "the seat. After a film like that you feel more alive than after quiet "
            "arthouse. It's pure adrenaline.\n\n"
            "Other people are amazed: \"how can you watch this, I'm scared just from the "
            "trailer\". For you that's the point — you want a strong reaction. And you "
            "know the difference between a quality genre piece and cheap gore: you want "
            "fear, not disgust.\n\n"
            "What's worth knowing: the best films of this category work in the dark, "
            "with sound, on a big screen. Don't ruin them with light and pauses. And "
            "watch with people who also love the genre — otherwise instead of shared "
            "horror you'll get someone's complaints."
        ),
        "triggers": ["exorcist", "halloween", "alien"]
    },
    # ─── Экшн × 2 ──────────────────────────────────────────────────
    {
        "name": "Кодекс героя",
        "name_en": "A hero's code",
        "body": (
            "Ты любишь героев, у которых есть правила. Не «хороший парень», а конкретный "
            "кодекс — что можно, что нельзя, и что бывает с тем, кто этот кодекс "
            "нарушает. Дон Корлеоне со своим «никогда не отказывай в просьбе на свадьбе»; "
            "Джон Уик со своими отелями-нейтралами; Джон Макклейн с упрямством «я просто "
            "полицейский».\n\n"
            "Это работает потому, что для тебя кино с кодексом — это карта, как "
            "держаться. Когда вокруг хаос, у героя есть своя ось — и фильм показывает, "
            "что эта ось выдерживает. Ты сам носишь похожие правила: что-то делаешь "
            "всегда, что-то — никогда. Хорошо, когда мир кино подтверждает: можно жить "
            "по правилам.\n\n"
            "Окружающие иногда не видят разницы между «боевиком» и «фильмом про "
            "человека с принципами в боевом мире». Для тебя это разные жанры. Тебе "
            "скучно смотреть стрельбу без стержня; интересно — когда стрельба обоснована "
            "логикой героя.\n\n"
            "Что стоит знать: ты можешь идеализировать кодекс. В кино он работает "
            "безотказно; в жизни — иногда нет, и упрямое следование принципу обходится "
            "дороже, чем гибкость. Учись отличать момент, когда твоя ось — спасение, от "
            "момента, когда она мешает увидеть, что мир изменился."
        ),
        "body_en": (
            "You love heroes who have rules. Not \"good guy\" but a specific code — "
            "what's allowed, what isn't, and what happens to the one who breaks it. "
            "Don Corleone with his \"never refuse a request on a wedding day\"; John "
            "Wick with his neutral-ground hotels; John McClane with the stubborn \"I'm "
            "just a cop\".\n\n"
            "This works because for you a film with a code is a map of how to hold "
            "yourself together. When everything around is chaos, the hero has an axis — "
            "and the film proves that axis holds. You carry similar rules yourself: some "
            "things you always do, some things never. It feels good when cinema confirms: "
            "you can live by rules.\n\n"
            "Other people sometimes don't see the difference between \"an action movie\" "
            "and \"a film about a man with principles in a violent world\". For you "
            "those are different genres. Shooting without a backbone bores you; shooting "
            "justified by the hero's logic interests you.\n\n"
            "What's worth knowing: you can idealize the code. In cinema it always works; "
            "in life sometimes it doesn't, and stubborn principle costs more than "
            "flexibility. Learn to tell apart the moment when your axis saves you from "
            "the moment when it blocks you from seeing the world has changed."
        ),
        "triggers": ["godfather", "johnwick", "diehard"]
    },
    {
        "name": "Хаос со стилем",
        "name_en": "Chaos with style",
        "body": (
            "Тебе нужна анархия с хорошим монтажом. Тарантино прыгает между сценами, "
            "как ему хочется, а ты следишь и не пропускаешь; Миллер гонит через пустыню "
            "в одну линию, и каждый кадр выглядит как обложка журнала. Тебя цепляет "
            "именно сочетание: безумие на содержании и точность на форме.\n\n"
            "Это работает потому, что ты видишь кино как искусство ритма. Не «что "
            "произошло», а «как это срежиссировано». «Криминальное чтиво» — это не "
            "сюжет, это плейлист сцен; «Дорога ярости» — это не история, это балет с "
            "грузовиками. Тебя впечатляет ремесло, а не нравоучение.\n\n"
            "Окружающие иногда жалуются: «слишком быстро, слишком громко, слишком "
            "странно». Для тебя — это и есть удовольствие. Ты любишь, когда кино "
            "уверено в себе и не просит прощения за то, что выбрало именно такой темп. "
            "Это тренированный вкус, и ты знаешь, что он развивается только на "
            "радикальных фильмах.\n\n"
            "Что стоит знать: твой жанр требует свежей головы. Не ставь Тарантино под "
            "выпивку и сериалы — детали пройдут мимо. И помни, что стиль ради стиля без "
            "идеи быстро надоедает; ищи режиссёров, у которых хаос упакован вокруг "
            "чего-то."
        ),
        "body_en": (
            "You want anarchy with good editing. Tarantino jumps between scenes however "
            "he likes, and you track every cut without losing the thread; Miller drives "
            "through the desert in a single line, and every frame looks like a magazine "
            "cover. What gets you is exactly that combination: madness in content, "
            "precision in form.\n\n"
            "This works because you see cinema as the art of rhythm. Not \"what happened\" "
            "but \"how it was directed\". \"Pulp Fiction\" isn't a plot — it's a playlist "
            "of scenes; \"Fury Road\" isn't a story — it's a ballet with trucks. You're "
            "impressed by craft, not moral.\n\n"
            "Other people sometimes complain: \"too fast, too loud, too weird\". For you "
            "that's exactly the pleasure. You love when cinema is confident in itself "
            "and doesn't apologize for choosing this pace. It's a trained taste, and you "
            "know it only develops on radical films.\n\n"
            "What's worth knowing: your genre needs a fresh head. Don't put Tarantino on "
            "with drinks and side conversation — the details slip past. And remember: "
            "style for style's sake without an idea gets boring fast; look for directors "
            "whose chaos is packaged around something."
        ),
        "triggers": ["pulpfiction", "madmax"]
    },
    # ─── Гик × 2 ───────────────────────────────────────────────────
    {
        "name": "Эпос и пророчество",
        "name_en": "Epic and prophecy",
        "body": (
            "Тебя цепляют истории большого формата. Не «один день из жизни», а "
            "тысячелетняя сага: судьба колец, империй, городов. Тебе важна мифология — "
            "устойчивая вселенная с пророчествами, родословными, древним злом. После "
            "«Властелина колец» или «Гладиатора» ты выходишь с чувством, что что-то "
            "закрылось правильно.\n\n"
            "Это работает потому, что эпос даёт твоей жизни вертикаль. Ты живёшь среди "
            "обедов и метро, но фильм напоминает: бывают истории, в которых одно "
            "решение решает судьбу всех. Тебе нужна эта высота — иначе мир кажется "
            "плоским. Эпос — это твой кислород для воображения, а не баловство.\n\n"
            "Окружающие иногда говорят: «слишком пафосно». Для тебя — это нужный "
            "регистр. Когда история действительно большая, маленькие интонации не "
            "работают: нужно именно «по полной». Ты ценишь, когда фильм не стесняется "
            "своей серьёзности.\n\n"
            "Что стоит знать: эпос плохо переваривает повседневный фон. Не смотри его "
            "урывками — теряет вес. Найди вечер, тёмную комнату, длинный заход. И не "
            "извиняйся, что такое кино «для подростков»: лучшие эпосы взрослее многих "
            "драм."
        ),
        "body_en": (
            "What grabs you are stories at scale. Not \"a day in the life\" but a "
            "thousand-year saga: the fate of rings, empires, cities. Mythology matters "
            "to you — a coherent universe with prophecies, bloodlines, ancient evil. "
            "After \"The Lord of the Rings\" or \"Gladiator\" you come out with the "
            "feeling that something closed properly.\n\n"
            "This works because epic gives your life a vertical. You live among lunches "
            "and subways, but the film reminds: there are stories where one decision "
            "settles everyone's fate. You need that altitude, otherwise the world feels "
            "flat. Epic is oxygen for your imagination, not a guilty pleasure.\n\n"
            "Other people sometimes say: \"too pompous\". For you that's the correct "
            "register. When a story is genuinely big, small intonations don't work — "
            "you need the full volume. You appreciate when a film isn't ashamed of its "
            "seriousness.\n\n"
            "What's worth knowing: epic doesn't digest well as background. Don't watch "
            "in bits — it loses weight. Find an evening, a dark room, a long sit. And "
            "don't apologize that such cinema is \"for teenagers\": the best epics are "
            "more adult than half the dramas."
        ),
        "triggers": ["lotr", "gladiator", "empire", "darkknight"]
    },
    {
        "name": "Изобретательный мир",
        "name_en": "An inventive world",
        "body": (
            "Тебе нравится, когда фильм играет с правилами реальности. Что если мы все "
            "в симуляции? Что если можно вернуться на 30 лет назад и встретить "
            "родителей? Что если за тоннелем — мир духов? Тебя цепляет не фэнтези само "
            "по себе, а изобретательность сценария: как режиссёр придумал и удержал "
            "систему.\n\n"
            "Это работает потому, что ты — головоломщик. «Матрица», «Назад в будущее», "
            "Миядзаки — это не «приключения», это конструкции. Тебе важно, что у мира "
            "есть свои законы и фильм им следует. Когда сценарий ленивый и решает «потому "
            "что магия» — тебя это бесит, даже если визуал красивый.\n\n"
            "Окружающие иногда не понимают, почему «Матрица» для тебя серьёзный фильм. "
            "Для них это «про драки в кожаных плащах». Ты видишь дальше: за плащами — "
            "вопрос об устройстве мира, и фильм этот вопрос реально задаёт. Хороший "
            "гик-фильм под сладкой обёрткой провозит большую идею.\n\n"
            "Что стоит знать: твой жанр стареет в плане эффектов. Старые гик-фильмы "
            "выглядят дёшево — но если идея жива, их всё ещё стоит смотреть. Учись "
            "прощать старую графику ради старой мысли. И не путай оригинал с ремейком."
        ),
        "body_en": (
            "You like when a film plays with reality's rules. What if we're all in a "
            "simulation? What if you could go back 30 years and meet your parents? What "
            "if behind the tunnel there's a spirit world? What grabs you isn't fantasy "
            "for its own sake but the inventiveness of the script: how the director "
            "designed a system and kept it consistent.\n\n"
            "This works because you're a puzzle-mind. \"The Matrix\", \"Back to the "
            "Future\", Miyazaki — these aren't \"adventure films\", they are "
            "constructions. What matters to you is that the world has laws and the film "
            "obeys them. When a script gets lazy and waves \"because magic\", you're "
            "annoyed — even if the visuals are beautiful.\n\n"
            "Other people sometimes don't understand why \"The Matrix\" is a serious "
            "film for you. For them it's \"about leather-coat fights\". You see further: "
            "behind the coats sits a question about the structure of reality, and the "
            "film genuinely asks it. A good geek film smuggles a big idea inside a "
            "sweet wrapper.\n\n"
            "What's worth knowing: your genre ages on effects. Old geek films look "
            "cheap — but if the idea is alive, they're still worth watching. Learn to "
            "forgive old graphics for the sake of old thought. And don't confuse the "
            "original with the remake."
        ),
        "triggers": ["matrix", "backtofuture", "spiritedaway"]
    },
    # ─── Комедии × 2 ───────────────────────────────────────────────
    {
        "name": "Слой за слоем",
        "name_en": "Layer by layer",
        "body": (
            "Тебе нравятся комедии-конструкции. «Лебовски» с десятком персонажей, у "
            "которых каждый ведёт свою линию; «Достать ножи» с детективом-обманкой, где "
            "ты пересматриваешь свою версию каждые десять минут. Ты любишь, когда юмор "
            "не одноразовый, а собирается в систему — и работает на всех уровнях.\n\n"
            "Это работает потому, что тебе скучно от прямой шутки. Тебе нужен подтекст, "
            "ирония, ссылка на сцену тридцатиминутной давности. Ты пересматриваешь "
            "такие фильмы не потому, что забыл сюжет, а потому что во второй раз они "
            "становятся другими — ты начинаешь видеть, как всё было собрано.\n\n"
            "Окружающие иногда смеются на других местах, чем ты. Это нормально — ты "
            "смеёшься на конструкции, они на гэгах. Хорошие комедии этого типа любят "
            "те, кто потом цитирует диалоги и спорит, что было в кадре «на самом деле».\n\n"
            "Что стоит знать: первое впечатление от такой комедии часто слабое. "
            "«Лебовски» в первый раз — нормальный фильм; на третий — гениальный. Не "
            "суди после одного просмотра и не показывай тем, кто ждёт быстрых смешков."
        ),
        "body_en": (
            "You like comedy-as-construction. \"The Big Lebowski\" with a dozen "
            "characters, each carrying their own thread; \"Knives Out\" with its bait-"
            "and-switch detective story where you revise your theory every ten minutes. "
            "You love when humor isn't disposable but assembles into a system, working "
            "on every level.\n\n"
            "This works because plain jokes bore you. You need subtext, irony, a "
            "callback to a scene from thirty minutes ago. You rewatch these films not "
            "because you forgot the plot but because the second time around they become "
            "different — you start to see how everything was put together.\n\n"
            "Other people sometimes laugh at different moments than you. That's normal — "
            "you laugh at the construction, they laugh at the gags. Good comedies of "
            "this kind are loved by people who later quote the dialogue and argue about "
            "what was \"really\" happening on screen.\n\n"
            "What's worth knowing: first impressions of such comedies are often weak. "
            "\"Lebowski\" the first time is a fine film; the third time it's a "
            "masterpiece. Don't judge after one watch, and don't show it to people who "
            "want quick laughs."
        ),
        "triggers": ["lebowski", "knivesout"]
    },
    {
        "name": "Глупость с классом",
        "name_en": "Class-act silliness",
        "body": (
            "Ты любишь, когда комедия не боится быть глупой — но делает это "
            "профессионально. «В джазе только девушки» с двумя парнями в платьях; «Типа "
            "крутые легавые» с перестрелками в английской деревне. Это абсурд, "
            "поставленный на серьёзном уровне ремесла. Ты ценишь именно эту вилку: тема "
            "дурацкая, исполнение виртуозное.\n\n"
            "Это работает потому, что для тебя смех — это разрешение. Когда у "
            "профессионала хватает смелости снять «глупое», ты получаешь сигнал: можно "
            "расслабиться, не всё должно быть «значимым». Хороший фарс лечит лучше "
            "многих умных фильмов именно потому, что временно отменяет необходимость "
            "быть серьёзным.\n\n"
            "Окружающие иногда стесняются признаваться, что любят такие фильмы. Ты — "
            "нет. Ты понимаешь, что снять хороший фарс труднее, чем драму: один неверный "
            "тон — и комедия превращается в кривлянье. Лучшие из них держат тонкую "
            "линию, и ты ценишь именно мастерство держать.\n\n"
            "Что стоит знать: твой жанр плохо переносит трезвый разбор. Не объясняй "
            "другим, почему «Типа крутые легавые» гениальны: либо они смеются, либо "
            "нет. И не ставь такие фильмы тем, кто пришёл «обсудить кино» — они для "
            "другого вечера."
        ),
        "body_en": (
            "You love when comedy isn't afraid to be silly — but does it "
            "professionally. \"Some Like It Hot\" with two guys in dresses; \"Hot Fuzz\" "
            "with shootouts in an English village. This is absurdity staged at a serious "
            "level of craft. You appreciate exactly that fork: dumb premise, virtuoso "
            "execution.\n\n"
            "This works because for you laughter is permission. When a professional has "
            "the courage to make something silly, you get the signal: you can relax, "
            "not everything has to be \"meaningful\". A good farce heals better than "
            "many smart films precisely because it temporarily lifts the duty of being "
            "serious.\n\n"
            "Other people are sometimes embarrassed to admit they love these films. You "
            "are not. You understand that making a good farce is harder than making a "
            "drama: one wrong note and comedy becomes mugging. The best ones walk a "
            "thin line, and you appreciate the skill of walking it.\n\n"
            "What's worth knowing: your genre survives sober analysis poorly. Don't "
            "explain to others why \"Hot Fuzz\" is brilliant — either they laugh or they "
            "don't. And don't put on such films for people who came to \"discuss "
            "cinema\": these are for a different evening."
        ),
        "triggers": ["hotfuzz", "somelikeit"]
    },
    # ─── Романтика × 2 ─────────────────────────────────────────────
    {
        "name": "Случайная встреча",
        "name_en": "A chance meeting",
        "body": (
            "Тебя цепляют фильмы, где всё держится на одной встрече. Двое в поезде в "
            "Вене; пианист и актриса в Лос-Анджелесе; мужчина и женщина в баре "
            "Касабланки. Тебе важен момент, когда два разных человека вдруг говорят на "
            "одном языке — и понимают, что это редкость, которая может больше не "
            "повториться.\n\n"
            "Это работает потому, что в твоей карте мира любовь начинается в реальном "
            "моменте, а не «случайно проснулась через год». Тебе важна точка контакта: "
            "как именно произошло. Ты любишь смотреть на жесты, разговоры, "
            "недосказанное — потому что сам ценишь, когда люди по-настоящему встречаются "
            "друг с другом.\n\n"
            "Окружающие иногда говорят: «нудно, они просто разговаривают». Для тебя "
            "именно разговор — драма. Ты различаешь, когда диалог настоящий и когда "
            "писатель его выдумал. И когда настоящий — фильм работает, даже если в нём "
            "ничего «не происходит».\n\n"
            "Что стоит знать: твой жанр требует тишины и присутствия. Не смотри его в "
            "шуме и под уведомления — пропустишь именно то, ради чего он сделан. И не "
            "пытайся пересказать его потом: слова не передают, надо смотреть."
        ),
        "body_en": (
            "What grabs you are films that hinge on a single meeting. Two people on a "
            "train in Vienna; a pianist and an actress in Los Angeles; a man and a "
            "woman in a Casablanca bar. What matters is the moment when two different "
            "people suddenly speak the same language — and realize this is rare and may "
            "not happen again.\n\n"
            "This works because in your map of the world love begins in a real moment, "
            "not \"accidentally appears a year later\". The point of contact matters to "
            "you: how exactly it happened. You love watching gestures, conversations, "
            "things left unsaid — because you yourself value when people genuinely meet "
            "each other.\n\n"
            "Other people sometimes say: \"boring, they just talk\". For you the talk "
            "is the drama. You can tell when dialogue is real and when a writer made it "
            "up. When it's real, the film works even if \"nothing happens\".\n\n"
            "What's worth knowing: your genre needs silence and presence. Don't watch "
            "with noise and notifications — you'll miss exactly what the film was made "
            "for. And don't try to retell it afterwards: words don't carry it, you have "
            "to watch."
        ),
        "triggers": ["beforesunrise", "lalaland", "casablanca"]
    },
    {
        "name": "Сказка про любовь",
        "name_en": "A love fairytale",
        "body": (
            "Тебе нужна романтика с приподнятым тоном. Не «две жизни пересеклись», а "
            "«жил-был принц, и встретил он принцессу». «Принцесса-невеста» с фехтованием "
            "и пиратами; чаплинский бродяга, спасающий слепую цветочницу. Ты любишь, "
            "когда фильм не стесняется быть нежным.\n\n"
            "Это работает потому, что для тебя в романтике главное — добро. Не страсть, "
            "не конфликт, не сложная психология, а простая идея, что любовь делает мир "
            "лучше. Тебя не оскорбляет «слащавость»; наоборот, ты считаешь, что "
            "современное кино слишком стесняется этой ноты, и от этого мы все теряем.\n\n"
            "Окружающие иногда называют такие фильмы «детскими». Для тебя в их детскости "
            "и сила. Лучшие сказки про любовь говорят взрослым правду через простую "
            "форму: что доброта — выбор, что верность — сила, что нежность — не "
            "слабость, а основа.\n\n"
            "Что стоит знать: твой жанр стареет хуже остальных по форме (старые цвета, "
            "старая графика), но лучше остальных по содержанию. Не цепляйся за «выглядит "
            "наивно»; смотри на то, что фильм говорит. Чаплин 1931 года живее многих "
            "драм 2024-го."
        ),
        "body_en": (
            "You want romance with an elevated tone. Not \"two lives intersected\" but "
            "\"once upon a time there was a prince, and he met a princess\". \"The "
            "Princess Bride\" with fencing and pirates; Chaplin's tramp rescuing a "
            "blind flower girl. You love when a film isn't ashamed of being tender.\n\n"
            "This works because for you the heart of romance is goodness. Not passion, "
            "not conflict, not complex psychology, but the simple idea that love makes "
            "the world better. \"Sappy\" doesn't offend you; on the contrary, you think "
            "modern cinema is too embarrassed of this note, and we all lose because of "
            "it.\n\n"
            "Other people sometimes call such films \"childish\". For you, the "
            "childishness is exactly the strength. The best love fairytales tell adults "
            "the truth through simple form: that kindness is a choice, that loyalty is "
            "power, that tenderness is not weakness but foundation.\n\n"
            "What's worth knowing: your genre ages worse than most on form (old colors, "
            "old visuals) but better than most on content. Don't get hung up on \"looks "
            "naive\"; look at what the film says. Chaplin from 1931 is more alive than "
            "many dramas from 2024."
        ),
        "triggers": ["princessbride", "citylights"]
    },
    # ─── Большая жизнь × 2 ─────────────────────────────────────────
    {
        "name": "Путь упрямого",
        "name_en": "The stubborn path",
        "body": (
            "Тебя зажигают истории, в которых герой долго бьётся в стену — и однажды "
            "она падает. Рокки, бегущий по утрам и поднимающийся в финале; Энди в "
            "Шоушенке, двадцать лет ковыряющий стену молотком; Форрест, который просто "
            "бежал и пробежал Америку. Тебе нужен сюжет упрямства — и финал, в котором "
            "это упрямство оправдалось.\n\n"
            "Это работает потому, что ты сам так живёшь. Ты не ищешь талантов и удачи; "
            "ты ищешь дисциплины и времени. Тебе важно видеть в кино подтверждение: "
            "если делать каждый день, будет результат. Не магический, не быстрый — но "
            "будет. Это твоё кино-вдохновение, и ты возвращаешься к нему в трудные "
            "периоды.\n\n"
            "Окружающие иногда думают, что такие фильмы «слишком американские», "
            "«слишком простые». Для тебя простота — преимущество. Ты не нуждаешься в "
            "сложной структуре, чтобы понять, что упорство работает. Тебе нужна именно "
            "прямая, ясная история — как письмо самому себе.\n\n"
            "Что стоит знать: после такого фильма хочется в спортзал, в офис, на учёбу. "
            "Это нормальная реакция, но действуй на следующий день, не сразу. Решения, "
            "принятые на пике эмоции, часто не доживают до утра. Используй заряд тонко: "
            "не для одного действия, а для серии."
        ),
        "body_en": (
            "What lights you up are stories where the hero pounds against a wall for a "
            "long time — and one day it falls. Rocky running in the mornings and rising "
            "in the final round; Andy in Shawshank chipping the wall with a hammer for "
            "twenty years; Forrest who just kept running and ran across America. You "
            "need the plot of stubbornness — and a finale where the stubbornness paid "
            "off.\n\n"
            "This works because you live this way yourself. You don't look for talent "
            "and luck; you look for discipline and time. You need cinema to confirm: if "
            "you do it every day, there will be a result. Not magical, not fast — but "
            "real. This is your inspiration cinema, and you come back to it in hard "
            "periods.\n\n"
            "Other people sometimes think such films are \"too American\", \"too "
            "simple\". For you simplicity is the advantage. You don't need complex "
            "structure to understand that perseverance works. You need precisely the "
            "direct, clear story — like a letter to yourself.\n\n"
            "What's worth knowing: after such a film you want to go to the gym, the "
            "office, the classroom. That's a normal reaction, but act the next day, not "
            "immediately. Decisions made at peak emotion often don't survive until "
            "morning. Use the charge thinly — not for one action but for a series."
        ),
        "triggers": ["rocky", "shawshank", "forrest", "socialnetwork"]
    },
    {
        "name": "Свет в темноте",
        "name_en": "Light in the dark",
        "body": (
            "Ты любишь фильмы, где доброта проявляется в самых тёмных обстоятельствах. "
            "Шиндлер в нацистской Польше спасает 1100 человек; Джон Кофи в коридоре "
            "смертников лечит чужую боль. Это не оптимизм, это сложнее: когда вокруг "
            "ад, и кто-то всё равно делает выбор в сторону жизни. Этот выбор — твой "
            "жанр.\n\n"
            "Это работает потому, что для тебя кино — этический эксперимент. Не «как "
            "интересно», а «как правильно». Ты тестируешь героев и себя одновременно: "
            "что бы я сделал в такой ситуации? Был бы я тем, кто отвернулся, или тем, "
            "кто рискнул? Лучшие фильмы этого типа дают честный, тяжёлый ответ.\n\n"
            "Окружающие иногда говорят: «слишком давит, не для вечера». Для тебя — "
            "наоборот, это и есть кино для вечера, когда нужно перезагрузиться от "
            "мелкого. После «Списка Шиндлера» обычные жалобы кажутся смешными, и ты на "
            "пару дней живёшь иначе. Это полезное напоминание о масштабе.\n\n"
            "Что стоит знать: такие фильмы нельзя смотреть часто и нельзя на полглаза. "
            "Один раз в год по-настоящему — лучше, чем десять раз бегло. И не путай "
            "тяжесть с занудством: лучшие фильмы этого жанра динамичны, но эмоционально "
            "плотны. Это разные вещи."
        ),
        "body_en": (
            "You love films where kindness shows up in the darkest circumstances. "
            "Schindler in Nazi Poland saving 1,100 lives; John Coffey in death row "
            "healing other people's pain. This isn't optimism, it's harder: hell is all "
            "around, and someone still chooses life. That choice is your genre.\n\n"
            "This works because for you cinema is an ethical experiment. Not \"how "
            "interesting\" but \"how is it right\". You test the heroes and yourself at "
            "the same time: what would I have done in that situation? Would I be the "
            "one who turned away, or the one who took the risk? The best films of this "
            "kind give an honest, heavy answer.\n\n"
            "Other people sometimes say: \"too heavy, not for an evening\". For you the "
            "opposite is true — this is exactly the cinema for an evening when you need "
            "to reset from the trivial. After \"Schindler's List\" ordinary complaints "
            "feel ridiculous, and you live differently for a few days. That's a useful "
            "reminder of scale.\n\n"
            "What's worth knowing: such films can't be watched often and can't be "
            "watched half-attention. Once a year done properly is better than ten times "
            "skimmed. And don't confuse heaviness with tedium: the best films of this "
            "genre are dynamic, but emotionally dense. Those are different things."
        ),
        "triggers": ["schindlerslist", "greenmile"]
    },
]


def main() -> int:
    if not CATEGORIES_JSON.exists():
        print(f"ERROR: {CATEGORIES_JSON} not found")
        return 1

    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        print(f"ERROR: expected list at root")
        return 1

    target = next((c for c in raw if c.get("id") == "night_films"), None)
    if target is None:
        print("ERROR: night_films not found")
        return 1

    print(f"Found: {target.get('name')}")
    print(f"  before: {len(target.get('items', []))} items, "
          f"{len(target.get('archetypes', []))} archetypes, "
          f"size={target.get('recommended_tournament_size')}")

    # 0. Update category-level fields (name_en, blurb, blurb_en)
    target["name_en"] = NEW_NAME_EN
    target["blurb"] = NEW_BLURB_RU
    target["blurb_en"] = NEW_BLURB_EN
    print(f"  category: name_en, blurb, blurb_en set")

    # 1. Append items, skipping any already present (by id)
    existing_ids = {it["id"] for it in target.get("items", [])}
    added_items = 0
    for it in NEW_ITEMS:
        if it["id"] in existing_ids:
            print(f"  SKIP existing item: {it['id']}")
            continue
        target.setdefault("items", []).append(it)
        added_items += 1
    print(f"  added {added_items} items (each with name_en + ctx_en)")

    # 2. Bump tournament size to 64
    target["recommended_tournament_size"] = 64

    # 3. Extend triggers on existing archetypes
    arch_by_name = {a.get("name"): a for a in target.get("archetypes", [])}
    for arch_name, new_trigs in TRIGGER_ADDITIONS.items():
        if arch_name not in arch_by_name:
            print(f"  WARN: existing archetype '{arch_name}' not found")
            continue
        cur = set(arch_by_name[arch_name].get("triggers", []))
        for tid in new_trigs:
            if tid not in cur:
                arch_by_name[arch_name].setdefault("triggers", []).append(tid)
        print(f"  extended '{arch_name}': now {len(arch_by_name[arch_name]['triggers'])} triggers")

    # 4. Append new archetypes (skip if name collision)
    added_arch = 0
    for a in NEW_ARCHETYPES:
        if a["name"] in arch_by_name:
            print(f"  SKIP existing archetype: {a['name']}")
            continue
        target.setdefault("archetypes", []).append(a)
        added_arch += 1
    print(f"  added {added_arch} archetypes (each with name_en + body_en)")

    # 5. Coverage validator
    all_trigs = set()
    for a in target.get("archetypes", []):
        all_trigs.update(a.get("triggers", []))
    item_ids = [it["id"] for it in target.get("items", [])]
    missing = [iid for iid in item_ids if iid not in all_trigs]
    if missing:
        print(f"  ERROR: items not covered: {missing}")
        return 1

    print(f"  AFTER: {len(target['items'])} items, "
          f"{len(target['archetypes'])} archetypes, "
          f"size={target['recommended_tournament_size']}")
    print(f"  coverage OK: all {len(item_ids)} items covered")

    # 6. Atomic write with timestamped backup
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.night_films64.{stamp}")
    shutil.copy2(CATEGORIES_JSON, backup)
    print(f"  backup: {backup}")

    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON)
    print(f"  wrote: {CATEGORIES_JSON}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
