# -*- coding: utf-8 -*-
"""Stage 2: replace massive_tv_show archetypes with 15 "superlux" viewer-type
archetypes covering all 74 series. Additive + self-contained (S1-S5 standard),
NO series named in bodies, bilingual. Regular dashes (no em dash).
Run: python3 add_series_archetypes.py [--apply]
"""
import json, shutil, sys
from datetime import datetime
CATEGORIES_PATH = '/opt/untitled-pick-game-api/data/categories.json'

A = [
 {
  'name':'Престол и меч','name_en':'The throne and the sword',
  'triggers':['game_of_thrones','house_of_dragon','witcher','spartacus','mandalorian'],
  'body':(
   "Тебе мало истории про людей - нужен целый мир, со своими домами, законами и ценой за власть. Карта в начальных титрах для тебя не украшение, а обещание: здесь всё взаправду, и за трон платят кровью.\n\n"
   "Тебя притягивает масштаб, где личное вплетено в судьбу государств. Когда у саги есть вес - родословные, интриги, мир, который живёт по своим правилам, - тебе интересно не «кто победит», а «какой ценой». Большая форма даёт то, чего не даёт камерная драма: ставка больше одной жизни.\n\n"
   "Окружающие говорят: «Это же просто драконы и мечи». Ты не споришь - ты знаешь, что под латами идёт разговор про власть, верность и предательство, такой же старый, как сама история. Просто тебе удобнее думать о нём через большой холст.\n\n"
   "Что стоит знать: большой мир легко полюбить за антураж и упустить того, кто держит его живым, - конкретного человека внутри. Когда тебя цепляет только размах, спроси: есть ли тут хоть один герой, за которого по-настоящему страшно? Если да - это великая история. Если нет - красивая декорация."
  ),
  'body_en':(
   "A story about people isn't enough for you - you need a whole world, with its own houses, laws and a price on power. The map in the opening titles isn't decoration; it's a promise: everything here is real, and the throne is paid for in blood.\n\n"
   "You're pulled by scale where the personal is woven into the fate of nations. When a saga has weight - bloodlines, intrigue, a world that runs by its own rules - what interests you isn't «who wins» but «at what cost». The big form gives what a chamber drama can't: the stakes are bigger than one life.\n\n"
   "People say: «It's just dragons and swords». You don't argue - you know that under the armor runs a conversation about power, loyalty and betrayal as old as history itself. You just find it easier to hold it on a large canvas.\n\n"
   "What's worth knowing: a big world is easy to love for its trappings and easy to lose the one who keeps it alive - the specific person inside it. When only the scope grips you, ask: is there a single character here you're genuinely afraid for? If yes - it's a great story. If no - beautiful scenery."
  ),
 },
 {
  'name':'Тёмная сторона','name_en':'The dark side',
  'triggers':['breaking_bad','better_call_saul','sopranos','peaky_blinders','the_wire'],
  'body':(
   "Хороший парень тебе скучен. Тебя держит у экрана человек, который медленно переходит черту - и сам почти не замечает, в какой момент стал тем, кого раньше презирал.\n\n"
   "Тебе важна моральная серая зона, где нет чистых и виноватых, а есть выбор и его цена. Ты следишь не за сюжетом, а за эрозией - как обстоятельства, гордость и одна маленькая уступка лепят из обычного человека что-то страшное. Это честнее сказки про добро и зло.\n\n"
   "Окружающие говорят: «Как можно болеть за такого мерзавца?». Ты отвечаешь, что не болеешь - наблюдаешь. Понять, почему человек стал чудовищем, - не то же самое, что его оправдать. Но многим проще навесить ярлык, чем заглянуть внутрь.\n\n"
   "Что стоит знать: у обаяния зла есть побочный эффект - начинаешь принимать стиль за глубину. Не каждый антигерой в красивом пальто что-то говорит о человеке; иногда это просто поза. Спрашивай себя, после какой истории тебе стало не по себе от узнавания, а не просто красиво."
  ),
  'body_en':(
   "The good guy bores you. What keeps you watching is a person slowly crossing a line - barely noticing the moment they became the very thing they used to despise.\n\n"
   "You care about the moral grey zone, where there are no clean and guilty, only choices and their cost. You follow not the plot but the erosion - how circumstance, pride and one small concession sculpt an ordinary person into something monstrous. It's more honest than a fable of good and evil.\n\n"
   "People say: «How can you root for a creep like that?». You answer that you don't root - you watch. Understanding why a man became a monster isn't the same as excusing him. But it's easier for many to slap on a label than to look inside.\n\n"
   "What's worth knowing: the charm of evil has a side effect - you start mistaking style for depth. Not every antihero in a sharp coat says something about people; sometimes it's just a pose. Ask yourself which story left you uneasy with recognition, not just with how good it looked."
  ),
 },
 {
  'name':'После титров - тишина','name_en':'After the credits, silence',
  'triggers':['dark','black_mirror','chernobyl','handmaids_tale','true_detective'],
  'body':(
   "Финал, после которого ты не идёшь спать, а сидишь в тишине. Не из-за ужаса на экране - из-за мысли, которую история оставила внутри и которую теперь не выключить.\n\n"
   "Тебе нужно искусство, которое неудобно. Когда сериал ставит вопрос без ответа - про природу человека, про то, как легко привычное превращается в кошмар, - ты не отворачиваешься, а наклоняешься ближе. Дискомфорт для тебя признак того, что задело по-настоящему.\n\n"
   "Окружающие говорят: «Зачем смотреть такую тяжесть, жизни мало?». Ты слышишь это и не соглашаешься: именно тяжёлое чаще всего и остаётся. Лёгкое забывается к утру, а вещь, от которой стало не по себе, иногда меняет, как ты смотришь на мир.\n\n"
   "Что стоит знать: у любви к мраку есть ловушка - можно начать путать безысходность с глубиной. Не всё, что давит, что-то значит; иногда это просто давит. Цени то, что после тишины оставляет не пустоту, а новую мысль."
  ),
  'body_en':(
   "The kind of ending after which you don't go to bed - you sit in silence. Not because of the horror on screen, but because of the thought the story left inside you, the one you now can't switch off.\n\n"
   "You need art that's uncomfortable. When a show asks a question with no answer - about human nature, about how easily the familiar turns into a nightmare - you don't look away, you lean closer. Discomfort, for you, is the sign it truly landed.\n\n"
   "People say: «Why watch something so heavy, life is short?». You hear it and disagree: the heavy is usually what stays. The light is forgotten by morning, but the thing that unsettled you sometimes changes how you see the world.\n\n"
   "What's worth knowing: loving the dark has a trap - you can start mistaking hopelessness for depth. Not everything that weighs on you means something; sometimes it just weighs. Value what leaves not emptiness after the silence, but a new thought."
  ),
 },
 {
  'name':'Ещё одну серию','name_en':'Just one more episode',
  'triggers':['money_heist','prison_break','squid_game','you_show','dexter'],
  'body':(
   "«Ладно, последняя» - говоришь ты в час ночи, прекрасно зная, что это ложь. Хороший клиффхэнгер для тебя не раздражение, а наркотик: пока не узнаешь, чем кончится, спать ты не будешь.\n\n"
   "Тебя заводит механика напряжения - план, который вот-вот рухнет, тиканье часов, секрет, который держат на ниточке. Ты ценишь сериал, который умеет не отпускать: где каждая серия заканчивается так, что рука сама тянется к следующей. Это чистый драйв, и ты не стыдишься его любить.\n\n"
   "Окружающие говорят: «Это же попкорн, не искусство». Ты пожимаешь плечами: удержать человека у экрана семь часов подряд - это тоже мастерство, и не такое частое, как кажется. Не всякая «серьёзная» вещь умеет то, что умеет хороший триллер.\n\n"
   "Что стоит знать: у залипания есть похмелье - наутро от ловко закрученной истории иногда не остаётся ничего, кроме «как они меня провели». Это нормально. Но иногда выбирай то, что держит не только за нерв, но и за что-то внутри - тогда драйв ещё и запомнится."
  ),
  'body_en':(
   "«Okay, last one» you say at 1 a.m., knowing perfectly well it's a lie. A good cliffhanger isn't an annoyance to you, it's a drug: until you know how it ends, you're not sleeping.\n\n"
   "You're hooked by the mechanics of tension - a plan about to collapse, a ticking clock, a secret held by a thread. You value a show that knows how not to let go: where every episode ends so your hand reaches for the next on its own. It's pure drive, and you're not ashamed to love it.\n\n"
   "People say: «That's popcorn, not art». You shrug: holding a person to the screen for seven hours straight is a craft too, and a rarer one than it looks. Not every «serious» thing can do what a good thriller does.\n\n"
   "What's worth knowing: the binge has a hangover - by morning a cleverly twisted story sometimes leaves nothing but «how did they get me». That's fine. But now and then pick what holds you by more than the nerve - then the rush sticks around too."
  ),
 },
 {
  'name':'Свои в эфире','name_en':'Family on the screen',
  'triggers':['friends','the_office','himym','brooklyn_99','scrubs'],
  'body':(
   "Ты включаешь это не чтобы узнать, чем кончится, - ты и так знаешь наизусть. Ты включаешь, чтобы вернуться к людям, рядом с которыми тепло, как к старым друзьям, которые всегда дома.\n\n"
   "Тебе важен сериал как место, а не как сюжет. Когда персонажи становятся компанией, к которой возвращаешься в плохой день, - это не зависимость, это уют. Хороший ситком лечит не шутками, а ощущением, что есть стол, за которым тебе всегда рады.\n\n"
   "Окружающие говорят: «Ты что, опять его пересматриваешь?». Да, опять - и не потому, что нет нового, а потому, что новое не греет так же. Ты не ищешь сюрприза, ты ищешь возвращения. Это разные удовольствия, и второе недооценивают.\n\n"
   "Что стоит знать: у уютного есть тихий риск - превратить экран в одеяло, под которым прячешься от своей реальной компании. Пусть знакомый смех будет добавкой к живым людям, а не заменой им. Тогда тепло с экрана становится тренировкой тепла вокруг."
  ),
  'body_en':(
   "You don't put this on to find out how it ends - you know it by heart. You put it on to come back to people you feel warm beside, like old friends who are always home.\n\n"
   "You value a show as a place, not a plot. When the characters become the company you return to on a bad day, that's not addiction, it's comfort. A good sitcom heals not with jokes but with the feeling that there's a table where you're always welcome.\n\n"
   "People say: «You're rewatching it AGAIN?». Yes, again - not because there's nothing new, but because the new doesn't warm you the same way. You're not after surprise, you're after return. Those are different pleasures, and the second is underrated.\n\n"
   "What's worth knowing: the cozy has a quiet risk - turning the screen into a blanket you hide under, away from your real company. Let the familiar laughter be a supplement to living people, not a substitute. Then the warmth from the screen becomes practice for the warmth around you."
  ),
 },
 {
  'name':'Школьный двор','name_en':'The schoolyard',
  'triggers':['euphoria','wednesday','riverdale','teen_wolf','heartstopper'],
  'body':(
   "Первая любовь, первое предательство, первое чувство, что мир рушится из-за одного сообщения. Ты тянешься к историям, где всё на максимуме, - потому что в юности так и есть, всё впервые и всё навсегда.\n\n"
   "Тебе важна эта температура - возраст, когда эмоции ещё не научились быть умеренными. Когда сериал помнит, каково это: дружить взахлёб, влюбляться до катастрофы, искать себя на ощупь, - ты узнаёшь себя, нынешнего или прошлого. Большое чувство по мелкому поводу для тебя не глупость, а правда.\n\n"
   "Окружающие говорят: «Это же подростковая драма, несерьёзно». Ты слышишь снисхождение и не покупаешься: то, что переживается впервые, переживается сильнее всего. Взрослые просто разучились так чувствовать и называют это зрелостью.\n\n"
   "Что стоит знать: у жанра про юность есть соблазн - спутать накал с глубиной и застрять в вечном «всё драма». Цени те истории, которые не только бередят, но и взрослеют вместе с героем. Тогда школьный двор остаётся местом, откуда выходят, а не где живут."
  ),
  'body_en':(
   "First love, first betrayal, first feeling that the world is ending over a single text. You reach for stories where everything is at maximum - because in youth it really is, all for the first time and all forever.\n\n"
   "You care about that temperature - the age when emotions haven't yet learned to be moderate. When a show remembers what it's like to befriend headlong, to fall in love to the point of catastrophe, to find yourself by feel - you recognize yourself, present or past. A huge feeling over a small cause isn't silly to you, it's true.\n\n"
   "People say: «It's just a teen drama, not serious». You hear the condescension and don't buy it: what's lived for the first time is lived hardest. Adults simply forgot how to feel that way and call it maturity.\n\n"
   "What's worth knowing: the coming-of-age genre has a temptation - to mistake intensity for depth and get stuck in eternal «everything is drama». Value the stories that don't just sting but grow up alongside the hero. Then the schoolyard stays a place you leave, not one you live in."
  ),
 },
 {
  'name':'Полночный сеанс','name_en':'The midnight screening',
  'triggers':['supernatural','vampire_diaries','true_blood','lucifer','ahs'],
  'body':(
   "Что-то есть в историях, где за гранью обычного мира начинается другой - с вампирами, демонами, проклятыми домами. Ты любишь, когда привычное даёт трещину и оттуда тянет холодком.\n\n"
   "Тебя притягивает мифология тьмы - правила, по которым живёт нечисть, цена за бессмертие, романтика опасного. Это не про страх ради страха; это способ поговорить про желание, смерть и запретное так, как не получается в реалистичной драме. Метафора в клыках иногда честнее прямого слова.\n\n"
   "Окружающие говорят: «Ну это же несерьёзно, мистика для подростков». Ты улыбаешься: люди рассказывают истории про чудовищ с тех пор, как научились говорить, - потому что чудовище всегда про нас самих. Просто под клыками удобнее обсуждать то, что страшно назвать прямо.\n\n"
   "Что стоит знать: у жанра про нечисть есть мель - бесконечные сезоны, где интрига давно высохла, а ритуал остался. Не путай преданность миру с привычкой к нему. Лучшая мистика всё ещё про живое чувство под маской, а не про маску ради маски."
  ),
  'body_en':(
   "There's something in stories where, just past the ordinary world, another one begins - with vampires, demons, cursed houses. You love it when the familiar cracks and a cold draft comes through.\n\n"
   "You're drawn to the mythology of darkness - the rules the undead live by, the price of immortality, the romance of the dangerous. It isn't fear for fear's sake; it's a way to talk about desire, death and the forbidden in a way realistic drama can't. A metaphor with fangs is sometimes more honest than a plain word.\n\n"
   "People say: «It's not serious, supernatural stuff for teens». You smile: people have told monster stories since they learned to speak - because the monster is always about us. It's just easier, under the fangs, to discuss what's frightening to name directly.\n\n"
   "What's worth knowing: the genre has a shallows - endless seasons where the intrigue dried up long ago and only the ritual remains. Don't confuse devotion to a world with mere habit of it. The best of it is still about a living feeling under the mask, not the mask for its own sake."
  ),
 },
 {
  'name':'Бархат и эпоха','name_en':'Velvet and era',
  'triggers':['the_crown','bridgerton','mad_men','outlander','anne_with_e'],
  'body':(
   "Тебя уносит фактура времени - покрой платья, тон обоев, манера держать сигарету. Ты смотришь не только сюжет, ты живёшь внутри эпохи, и чем точнее воссоздан мир, тем глубже погружение.\n\n"
   "Тебе важна красота как отдельный смысл. Когда история одета в свою эпоху до последней пуговицы, ты читаешь сквозь неё про людей: как они любили под другими правилами, что считалось скандалом, чего стоило держать спину прямо. Стиль для тебя не фон, а язык.\n\n"
   "Окружающие говорят: «Красиво, но ничего же не происходит». Ты не соглашаешься: происходит, просто медленно и под кожей. Один взгляд через бальный зал бывает громче перестрелки - если уметь его читать. Ты умеешь.\n\n"
   "Что стоит знать: у любви к эпохе есть риск - залюбоваться витриной и не заметить, живые ли там люди. Платья и интерьеры стареют быстро, если под ними нет настоящего чувства. Цени то, где роскошь служит героям, а не заменяет их."
  ),
  'body_en':(
   "You're carried off by the texture of a time - the cut of a dress, the tone of the wallpaper, the way a cigarette is held. You don't just watch the plot, you live inside the era, and the more precisely the world is rebuilt, the deeper you sink in.\n\n"
   "You value beauty as a meaning of its own. When a story is dressed in its era down to the last button, you read people through it: how they loved under different rules, what counted as scandal, what it cost to keep your back straight. Style, for you, isn't backdrop but language.\n\n"
   "People say: «Beautiful, but nothing happens». You disagree: it happens, just slowly and under the skin. A single look across a ballroom can be louder than a shootout - if you know how to read it. You do.\n\n"
   "What's worth knowing: loving an era has a risk - to admire the window display and miss whether the people inside are alive. Dresses and interiors age fast when there's no real feeling beneath them. Value the kind where the luxury serves the characters rather than replacing them."
  ),
 },
 {
  'name':'Ком в горле','name_en':'A lump in the throat',
  'triggers':['this_is_us','modern_family','greys_anatomy','desperate_housewives','good_doctor'],
  'body':(
   "Ты не стыдишься плакать над сериалом. Наоборот - история, которая нашла, чем тебя пробить, сделала свою работу. Ты приходишь к экрану, чтобы что-то почувствовать, и не извиняешься за это.\n\n"
   "Тебе важно живое чувство - семья, утрата, прощение, маленькие победы обычных людей. Когда драма умеет про близость без фальши, ты откликаешься всем телом: узнаёшь своих, свою боль, свои примирения. Эмоция для тебя не манипуляция, а смысл, ради которого всё и затевалось.\n\n"
   "Окружающие говорят: «Это же мыло, давит на слезу специально». Иногда да - и всё равно работает, потому что бьёт по настоящему. Ты отличаешь дешёвый трюк от честного удара; и когда удар честный, сопротивляться ему - не сила, а защита.\n\n"
   "Что стоит знать: у слезовыжималки есть нечестный приём - убивать любимого героя вместо того, чтобы рассказать про него. Цени те истории, где чувство заработано, а не выпрошено. Тогда ком в горле - не от трюка, а от правды, и он остаётся с тобой."
  ),
  'body_en':(
   "You're not ashamed to cry over a show. The opposite - a story that found a way to break through has done its job. You come to the screen to feel something, and you don't apologize for it.\n\n"
   "You value a living feeling - family, loss, forgiveness, the small victories of ordinary people. When a drama can do closeness without fakery, you respond with your whole body: you recognize your own people, your own pain, your own reconciliations. Emotion, for you, isn't manipulation but the very point of the whole thing.\n\n"
   "People say: «It's soap, it tugs at the tears on purpose». Sometimes yes - and it still works, because it hits something real. You can tell a cheap trick from an honest blow; and when the blow is honest, resisting it isn't strength, it's armor.\n\n"
   "What's worth knowing: the tearjerker has a dishonest move - killing a beloved character instead of telling you about them. Value the stories where the feeling is earned, not begged for. Then the lump in your throat comes from truth, not a trick, and it stays with you."
  ),
 },
 {
  'name':'Игры взрослых','name_en':'The grown-ups’ games',
  'triggers':['succession','house_of_cards','white_lotus','the_boys','oitnb'],
  'body':(
   "Тебя завораживает, как устроена власть изнутри - кто кого, за чей счёт и какой ценой. Ты смотришь на сильных мира сего без зависти и без гнева, а с холодным любопытством энтомолога: интересно, как именно они едят друг друга.\n\n"
   "Тебе важна острая оптика на тех, кто наверху. Когда сериал не воспевает богатых и не клеймит их, а препарирует - показывает пустоту за блеском, страх за хамством, - ты узнаёшь правду, которую обычно прячут. Сатира для тебя честнее восхищения.\n\n"
   "Окружающие говорят: «Зачем смотреть про этих мерзких людей?». Ты отвечаешь: чтобы понять систему, в которой живёшь. Эти истории не про то, как стать таким, а про то, как это работает - и почему так трудно выйти из игры, однажды в неё войдя.\n\n"
   "Что стоит знать: у циничного взгляда есть побочка - начинаешь верить, что все одинаково гнилы, и это удобная анестезия. Не вся власть пуста, не каждый наверху чудовище. Цени истории, которые злы, но не глухи к тому, что человек в этой машине всё ещё человек."
  ),
  'body_en':(
   "You're mesmerized by how power works from the inside - who beats whom, at whose expense, and at what cost. You look at the mighty without envy and without anger, with the cold curiosity of an entomologist: it's interesting, exactly how they devour each other.\n\n"
   "You value a sharp lens on the people at the top. When a show neither worships the rich nor brands them but dissects them - showing the emptiness behind the gloss, the fear behind the rudeness - you catch a truth usually hidden. Satire, for you, is more honest than admiration.\n\n"
   "People say: «Why watch these vile people?». You answer: to understand the system you live in. These stories aren't about how to become that, but about how it works - and why it's so hard to leave the game once you've entered it.\n\n"
   "What's worth knowing: the cynical gaze has a side effect - you start believing everyone is equally rotten, and that's a convenient anesthetic. Not all power is empty, not everyone at the top is a monster. Value stories that are cruel but not deaf to the fact that the human in the machine is still human."
  ),
 },
 {
  'name':'Сигнал из будущего','name_en':'A signal from the future',
  'triggers':['westworld','doctor_who','sense8','big_bang_theory','umbrella_academy'],
  'body':(
   "«А что, если?» - твой любимый вопрос. Что, если машины проснутся, время сложится, у людей появится способность, которой нет. Ты включаешь фантастику не ради спецэффектов, а ради идеи, которая чешет мозг.\n\n"
   "Тебе важна игра ума - концепция, правила выдуманного мира, логика, которую интересно разгадывать. Когда история строит механизм и честно играет по своим законам, ты получаешь удовольствие, близкое к решению головоломки. Воображение для тебя - не побег от реальности, а способ посмотреть на неё под новым углом.\n\n"
   "Окружающие говорят: «Это же гиковщина, слишком заумно». Ты не обижаешься: да, нужно включить голову, и в этом весь кайф. Не всем хочется думать на отдыхе - тебе именно этого и хочется. Разные мозги отдыхают по-разному.\n\n"
   "Что стоит знать: у любви к концепции есть ловушка - увлечься идеей и простить истории, что её герои картонные. Самая хитрая механика мертва без живого человека внутри. Цени фантастику, где за большой мыслью всё ещё бьётся чьё-то сердце."
  ),
  'body_en':(
   "«What if?» is your favorite question. What if the machines wake up, time folds, people gain an ability that doesn't exist. You put on sci-fi not for the effects but for the idea that scratches the brain.\n\n"
   "You value the play of the mind - a concept, the rules of an invented world, a logic that's fun to unravel. When a story builds a mechanism and plays fair by its own laws, you get a pleasure close to solving a puzzle. Imagination, for you, isn't an escape from reality but a way to see it from a new angle.\n\n"
   "People say: «That's geeky, too cerebral». You don't take offense: yes, you have to switch your head on, and that's the whole thrill. Not everyone wants to think while relaxing - you want exactly that. Different brains rest differently.\n\n"
   "What's worth knowing: loving a concept has a trap - getting carried away with the idea and forgiving a story for its cardboard people. The cleverest mechanism is dead without a living human inside. Value the sci-fi where a heart still beats behind the big thought."
  ),
 },
 {
  'name':'Кто это сделал','name_en':'Whodunit',
  'triggers':['sherlock','house_md','htgawm','law_and_order','fargo'],
  'body':(
   "Загадка на столе - и ты уже наклонился вперёд. Тебе нравится не развязка сама по себе, а дорога к ней: как из обрывков, оговорок и мелочей складывается ответ, который был на виду с самого начала.\n\n"
   "Тебе важен ум как зрелище - человек, который видит то, что не видят остальные, и логика, которую можно проследить. Ты смотришь, соревнуясь: успею ли разгадать раньше? Хорошая загадка уважает тебя, играет честно и прячет ключ на виду. Это удовольствие отдельного сорта.\n\n"
   "Окружающие говорят: «Опять твои детективы, всё же по шаблону». Ты усмехаешься: шаблон - это рамка, а кайф в том, как мастер внутри неё удивляет. Сонату тоже пишут по правилам; вопрос в том, кто играет.\n\n"
   "Что стоит знать: у любви к разгадке есть холодок - можно начать ценить только трюк и не замечать людей, ради которых он закручен. Лучшая тайна не только обманывает, но и что-то говорит о том, кто и почему лжёт. Цени ту, где ответ не только умный, но и человеческий."
  ),
  'body_en':(
   "A riddle on the table - and you've already leaned forward. What you like isn't the solution itself but the road to it: how scraps, slips and trifles add up to an answer that was in plain sight from the start.\n\n"
   "You value the mind as spectacle - a person who sees what others miss, and a logic you can trace. You watch as a contest: can I crack it first? A good mystery respects you, plays fair, and hides the key in the open. It's a pleasure of its own kind.\n\n"
   "People say: «Your detectives again, all by the formula». You smirk: the formula is a frame, and the joy is in how a master surprises you within it. A sonata is written to rules too; the question is who's playing.\n\n"
   "What's worth knowing: loving the solve has a chill - you can start valuing only the trick and miss the people it's wound around. The best mystery doesn't just deceive but says something about who lies and why. Value the one where the answer is not only clever but human."
  ),
 },
 {
  'name':'Когда всё рухнуло','name_en':'When everything collapsed',
  'triggers':['walking_dead','last_of_us','the_100','lost'],
  'body':(
   "Привычный мир кончился - и вот тут начинается самое интересное: кем человек оказывается, когда сняты все правила. Тебя притягивают истории на руинах, где выживание обнажает то, что в сытой жизни спрятано.\n\n"
   "Тебе важен этот эксперимент над людьми - что останется от морали, дружбы, любви, когда за них надо платить кровью каждый день. Ты смотришь не на монстров снаружи, а на тех, кем становятся люди внутри. Самое страшное в таких историях - всегда не зомби, а сосед.\n\n"
   "Окружающие говорят: «Сколько можно про апокалипсис, это же чернуха». Ты не соглашаешься: это не про смерть, это про то, ради чего стоит жить, когда всё остальное отняли. Крайность лучше любой лекции показывает, что в человеке настоящее.\n\n"
   "Что стоит знать: у жанра про выживание есть усталость - бесконечная безнадёга притупляет, и ужас становится фоном. Цени истории, где среди руин кто-то ещё держится за человечность, а не только за патроны. Без этого апокалипсис - просто шум."
  ),
  'body_en':(
   "The familiar world has ended - and that's where it gets interesting: who a person turns out to be once all the rules are off. You're drawn to stories on the ruins, where survival lays bare what a comfortable life keeps hidden.\n\n"
   "You value this experiment on people - what's left of morality, friendship, love when you pay for them in blood every day. You watch not the monsters outside but who people become inside. The scariest thing in such stories is never the zombie - it's the neighbor.\n\n"
   "People say: «How much apocalypse can you take, it's just bleakness». You disagree: it isn't about death, it's about what's worth living for when everything else has been taken. An extreme shows what's real in a person better than any lecture.\n\n"
   "What's worth knowing: the survival genre has a fatigue - endless hopelessness dulls you, and horror becomes wallpaper. Value the stories where, among the ruins, someone still holds onto their humanity, not just their ammo. Without that, the apocalypse is just noise."
  ),
 },
 {
  'name':'Блеск большого города','name_en':'The big-city shine',
  'triggers':['gossip_girl','sex_and_city','glee','suits','two_half_men'],
  'body':(
   "Дорогие квартиры, острые костюмы, разговоры на бегу и жизнь, в которой всё немного ярче, чем за окном. Ты любишь сериалы-витрины - не потому что наивен, а потому что иногда хочется красивой мечты, рассказанной с шиком.\n\n"
   "Тебе важен глянец как удовольствие - стиль, остроумие, ритм большого города, где даже драма выглядит элегантно. Это не пустота; это эскапизм со вкусом. Ты получаешь от формы ровно то, что она обещает: блеск, лёгкость и ощущение, что жизнь может быть праздником.\n\n"
   "Окружающие говорят: «Это же фантик, ненастоящая жизнь». Ты не споришь: конечно, ненастоящая - в том и смысл. Не всё надо смотреть, чтобы страдать; иногда красивое - это просто отдых, и в умении отдыхать нет ничего стыдного.\n\n"
   "Что стоит знать: у глянца есть сахарная ловушка - если питаться только им, реальная жизнь начинает казаться тусклой по сравнению. Пусть блеск с экрана будет десертом, а не основным блюдом. Тогда он радует, а не обесценивает то, что у тебя есть."
  ),
  'body_en':(
   "Pricey apartments, sharp suits, conversations on the move and a life where everything is a little brighter than outside your window. You love showcase shows - not because you're naive, but because sometimes you want a beautiful dream told with flair.\n\n"
   "You value gloss as a pleasure - style, wit, the rhythm of a big city where even drama looks elegant. It isn't emptiness; it's escapism with taste. You get from the form exactly what it promises: shine, lightness, and the sense that life can be a celebration.\n\n"
   "People say: «It's a wrapper, not real life». You don't argue: of course it isn't real - that's the point. You don't have to watch in order to suffer; sometimes the beautiful is just rest, and there's nothing shameful in knowing how to rest.\n\n"
   "What's worth knowing: gloss has a sugar trap - if you live on it alone, real life starts to look dull by comparison. Let the shine from the screen be dessert, not the main course. Then it delights you instead of devaluing what you already have."
  ),
 },
 {
  'name':'Свой шифр','name_en':'Your own code',
  'triggers':['stranger_things','cobra_kai','malcolm_middle','bates_motel','sons_of_anarchy'],
  'body':(
   "Тебя не уложить в одну полку. Список твоих любимых сериалов выглядит как чужой плейлист - ничего общего, кроме того, что каждый зацепил именно тебя по своей, никому не очевидной причине.\n\n"
   "Тебе важна не категория, а попадание. Один сериал берёт ностальгией, другой - неожиданным поворотом жанра, третий - героем, в котором ты узнал что-то своё. Ты не выбираешь по ярлыку «драма» или «комедия»; ты выбираешь по тому, отозвалось или нет. Это более тонкий вкус, чем кажется.\n\n"
   "Окружающие говорят: «У тебя вообще нет системы». Есть - просто она внутренняя. Ты собираешь не жанр, а частоту: вещи, которые звучат на твоей волне. Чужому глазу это хаос, тебе - точная настройка.\n\n"
   "Что стоит знать: у эклектики есть риск - спутать «разное» с «всеядным» и хватать всё подряд. Время от времени спроси себя, что общего у вещей, которые тебя по-настоящему держат. В ответе и спрятан твой настоящий вкус - тот самый шифр."
  ),
  'body_en':(
   "You can't be filed on one shelf. Your list of favorite shows looks like someone else's playlist - nothing in common, except that each one hooked you for its own reason, obvious to no one but you.\n\n"
   "You value not the category but the hit. One show gets you by nostalgia, another by an unexpected genre twist, a third by a character in whom you recognized something of your own. You don't pick by the label «drama» or «comedy»; you pick by whether it resonated. That's a finer taste than it looks.\n\n"
   "People say: «You have no system at all». You do - it's just internal. You collect not a genre but a frequency: things that sound on your wavelength. To an outside eye it's chaos; to you, precise tuning.\n\n"
   "What's worth knowing: eclecticism has a risk - mistaking «varied» for «omnivorous» and grabbing everything in reach. Now and then, ask what the things that truly hold you have in common. The answer hides your real taste - that very code."
  ),
 },
]

DEFAULT = {
  'name':'Свой эфир','name_en':'Your own channel',
  'body':(
   "У тебя нет одного любимого жанра - есть сериал на это настроение, на тот вечер, на конкретный момент жизни. Ты заходишь в сезон без обязательств и выходишь с новыми привязанностями. Это не всеядность, это свобода.\n\n"
   "Тебя притягивает само разнообразие - сегодня хочется напряжения, завтра тепла, послезавтра загадки. Ты ценишь сериалы за то, что они дают разное, и не пытаешься уложить свой вкус в одну формулу. Для тебя экран - это набор разных дверей, и ты выбираешь по тому, что нужно сейчас.\n\n"
   "Окружающие спрашивают: «Ну какой у тебя любимый?» - и видят, как ты зависаешь. Любимого-одного нет, и это не пустота, а широта. Ты держишь несколько вкусов параллельно, и каждый честный.\n\n"
   "Что стоит знать: у широты есть тихий риск - распыляться и ни во что не влюбляться до конца. Иногда стоит дать одной истории забрать тебя целиком, без переключения. Тогда к разнообразию добавляется глубина - и вкус становится не только широким, но и твоим."
  ),
  'body_en':(
   "You don't have one favorite genre - you have a show for this mood, that evening, a specific moment of life. You enter a season with no commitments and leave with new attachments. That's not being omnivorous, it's freedom.\n\n"
   "You're drawn to variety itself - today you want tension, tomorrow warmth, the day after a riddle. You value shows for giving you different things, and you don't try to fit your taste into one formula. The screen, for you, is a set of different doors, and you choose by what you need right now.\n\n"
   "People ask: «So which is your favorite?» - and watch you freeze. There's no single favorite, and that isn't emptiness but breadth. You hold several tastes in parallel, and each is honest.\n\n"
   "What's worth knowing: breadth has a quiet risk - to scatter and never fall fully in love with anything. Sometimes it's worth letting one story take you completely, with no channel-flipping. Then depth joins the variety - and the taste becomes not just wide, but yours."
  ),
}


def dash(s):
    return s.replace('—', '-')


def main():
    dry = '--apply' not in sys.argv
    with open(CATEGORIES_PATH, encoding='utf-8') as f:
        cats = json.load(f)
    c = next((c for c in cats if c.get('id') == 'massive_tv_show'), None)
    if not c:
        print('NOT FOUND'); sys.exit(1)

    item_ids = {it['id'] for it in c['items']}
    # Coverage validation
    covered = {}
    for a in A:
        for t in a['triggers']:
            covered[t] = covered.get(t, 0) + 1
    missing = sorted(item_ids - set(covered))
    over = sorted([k for k, v in covered.items() if v > 2])
    unknown = sorted(set(covered) - item_ids)
    print(f'Archetypes: {len(A)}  ·  items: {len(item_ids)}')
    print(f'  uncovered items: {len(missing)} {missing if missing else ""}')
    print(f'  items in >2 archetypes: {over if over else "none"}')
    print(f'  trigger ids not in items: {unknown if unknown else "none"}')
    for a in A:
        if not (2 <= len(a['triggers']) <= 5):
            print(f'  !! {a["name"]} has {len(a["triggers"])} triggers (must be 2-5)')

    # normalize em-dashes (no em dash rule)
    new_arch = []
    for a in A:
        new_arch.append({
            'name': a['name'], 'name_en': a['name_en'],
            'body': dash(a['body']), 'body_en': dash(a['body_en']),
            'triggers': a['triggers'],
        })
    c['archetypes'] = new_arch
    c['defaultArchetype'] = {
        'name': DEFAULT['name'], 'name_en': DEFAULT['name_en'],
        'body': dash(DEFAULT['body']), 'body_en': dash(DEFAULT['body_en']),
    }

    if dry:
        print('\n=== DRY RUN - add --apply ==='); return
    if missing or over or unknown:
        print('\nABORT: coverage problems, not saving.'); sys.exit(1)
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(CATEGORIES_PATH, CATEGORIES_PATH + f'.bak.series_arch.{ts}')
    with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    print('Saved')


if __name__ == '__main__':
    main()
