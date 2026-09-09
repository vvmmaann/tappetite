"""
Archetype EN backfill — batch 1: small clusters.
Categories: weird_animals, supercars, name_the_game (default only),
anime_essential, childhood_cartoons, cult_90s_series, your_sport.
~45 archetypes.

Translations matched by archetype name (RU). If name not found, skip with warning.
"""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

# Per-cat: list of {ru_name -> (name_en, body_en)}; defaults under "_default"
TRANSLATIONS = {
    "weird_animals": {
        "Любитель эволюционных тупиков": (
            "Lover of evolutionary dead ends",
            "You root for the ones nature didn't bother polishing. The more absurd the anatomy — the dearer the creature."
        ),
        "Поклонник кротких гигантов": (
            "Fan of gentle giants",
            "Big herbivores are your quiet passion. You think \"weird\" isn't about teeth — it's about calm."
        ),
        "Океан-наблюдатель": (
            "Ocean observer",
            "The deep is your unexplored continent. You know we still haven't seen 80% of the planet."
        ),
        "Поклонник ночных приматов": (
            "Fan of night primates",
            "What hooks you are the ones whose eyes take up half the head. The smaller the animal and the bigger the pupil — the closer to your heart."
        ),
        "_default": (
            "Zoo eclectic",
            "You don't pick land or ocean — biodiversity itself is your hobby."
        ),
    },
    "supercars": {
        "Итальянский романтик": (
            "Italian romantic",
            "V12 is your religion, design is your language. The sound of the engine matters more than lap times."
        ),
        "Немецкая школа": (
            "The German school",
            "You only trust those who test on the Nürburgring. Emotions are nice, but numbers are better."
        ),
        "Британский элегант": (
            "British elegant",
            "Speed should wear a tuxedo. Carbon doesn't brag — it works."
        ),
        "Перфекционист гипер-класса": (
            "Hyper-class perfectionist",
            "A thousand horsepower shouldn't be the peak — it should be the starting point. Numbers for the sake of numbers."
        ),
        "Адепт нестандартного": (
            "Adept of the unconventional",
            "You root for those who went against the grain — a Japanese V10 or a cheap mid-engine American."
        ),
        "_default": (
            "Cosmopolitan petrolhead",
            "Your garage has no homeland. A great engine is a great engine, regardless of the flag."
        ),
    },
    "name_the_game": {
        "_default": (
            "Vote counted",
            "Thanks. The winner of this tournament will become the game's real brand. Tell your friends — their vote counts too."
        ),
    },
    "anime_essential": {
        "Шёнен-эпопея": (
            "Shonen epic",
            "One Piece, Naruto, Hunter x Hunter, Demon Slayer. You need epic stories of friendship and growth. Not \"a few episodes\"; hundreds, where you grow up alongside the heroes.\n\n"
            "This works because you have patience and love for big narrative. Most people want \"quick\"; you understand that an epic takes time.\n\n"
            "Other people are sometimes amazed: \"a thousand episodes, really?\". A thousand. And every important one matters.\n\n"
            "What's worth knowing: long shonens have slumps. Sometimes 100 episodes of filler in a row. Learn to read episode lists and skip what doesn't matter. Otherwise you'll quit during filler before reaching the best arcs."
        ),
        "Тёмная философия": (
            "Dark philosophy",
            "Attack on Titan, Death Note, Evangelion, Code Geass. You don't want \"entertainment anime\" — you want a serious work. With philosophy, morality, no happy endings.\n\n"
            "This works because you treat anime as a grown-up medium. Most people see it as \"kids' cartoons\"; you know it's something else.\n\n"
            "Other people sometimes don't believe you: \"what philosophy could there be in a cartoon?\". Plenty. And often deeper than the average Hollywood film.\n\n"
            "What's worth knowing: dark anime needs digesting after a watch. Stack several in a row and you can spiral into depression. Learn to alternate them with lighter things, no matter how much the genre pulls you."
        ),
        "Сёнен с глубиной": (
            "Shonen with depth",
            "Fullmetal Alchemist, Hunter x Hunter, Jujutsu Kaisen, Vinland Saga. You love shonens that have real thought under the action. Not \"fight, win\"; questions of morality, choice, the price of victory.\n\n"
            "This works because you have a quality bar. Pure action bores you; you need something behind it.\n\n"
            "Other people sometimes shrug: \"shonen is just shonen\". Not just shonen. Good ones have a layer you have to grow into.\n\n"
            "What's worth knowing: \"deep shonens\" are rare. Many start that way and slide into ordinary action. Learn to tell them apart. If season 2 is just power-grinding with nothing new, those aren't the ones you came for."
        ),
        "Kyoto и красота": (
            "Kyoto and beauty",
            "Violet Evergarden, Your Lie in April, Made in Abyss, FMA Brotherhood. What grabs you are anime with stunning animation and emotional depth. Kyoto Animation, ufotable, the very best work — that's for you.\n\n"
            "This works because you have aesthetic sensitivity. Story matters, but so does form; they should be at the same level.\n\n"
            "Other people sometimes are surprised: \"you cried at an anime?\". Yes. It's the best anime drama of the last few years.\n\n"
            "What's worth knowing: the best visually-driven anime are rare. Most have limited budgets. Learn to value the good when you find it. And support the studios that take risks — without you, they won't make the next one."
        ),
        "Меха и психология": (
            "Mecha and psychology",
            "Evangelion, Code Geass, Attack on Titan, Steins;Gate. You like sci-fi with a psychological tilt. Not \"giant robots\" — humans in a crisis of technology.\n\n"
            "This works because you're interested in the human edge. Mecha is itself a metaphor for that edge: the body amplified by tech, the psyche unchanged.\n\n"
            "Other people sometimes don't get it: \"mecha is for teens\". So it seemed. Actually these are the most complex genre works in animation.\n\n"
            "What's worth knowing: mecha-psychology needs context. Without understanding postwar Japanese culture, a lot is lost. Learn at least the basics — it'll triple what you get from these works."
        ),
        "Лёгкое и душевное": (
            "Light and warm",
            "Spy x Family, Your Lie in April, Demon Slayer, Jujutsu Kaisen. You want balance — between the serious and the warm. Not pure drama, not pure comedy; something that hugs you and makes you smile.\n\n"
            "This works because you have an adult relationship with entertainment. You understand that \"light\" doesn't mean \"empty\"; sometimes it goes deeper than drama.\n\n"
            "Other people sometimes don't believe you: \"Spy x Family is for kids\". For everyone. And it's impossible to watch it without smiling.\n\n"
            "What's worth knowing: light anime is easily over- or under-rated. Learn to watch without snobbery. Sometimes the favorite work isn't the \"deep, serious\" one — it's the one that brings you joy on a Sunday evening."
        ),
        "Магический эксперимент": (
            "The magical experiment",
            "Steins;Gate, Made in Abyss, FMA, Evangelion. What grabs you are anime where the experiment with reality is the spine of the story. Time machines, strange worlds, alchemy.\n\n"
            "This works because you love concepts. \"Just a normal story\" isn't enough; you need a strange world with its own rules to be offered.\n\n"
            "Other people sometimes can't take it: \"Made in Abyss, really?\". Yes, Made in Abyss. And I know it hits harder than many films.\n\n"
            "What's worth knowing: these anime often turn cute into shocking. If you don't like sharp emotional swings, don't start Made in Abyss or Madoka Magica. Otherwise — buckle up."
        ),
        "_default": (
            "Your own anime mix",
            "You don't have one signature genre. You love epic shonens, dark psychologicals, sweet rom-coms — each for its own mood.\n\n"
            "This works because you understand: anime isn't one genre, it's a medium. And it contains everything.\n\n"
            "Other people sometimes wonder: \"how do you have both One Piece and Evangelion in the same playlist?\". They don't contradict. They're just different moods.\n\n"
            "What's worth knowing: a wide range is good, but sometimes it's worth digging into one genre. Going through everything by one director (Miyazaki, Shinkai) gives a depth that random viewing can't reach."
        ),
    },
    "childhood_cartoons": {
        "Постсоветский ностальгик": (
            "Post-Soviet nostalgic",
            "Nu, pogodi!, Smeshariki, Scooby-Doo, Chip 'n Dale. You grew up on a mix of Soviet and Western. And you remember both worlds — the cunning wolf from Soyuzmultfilm and the carefree Rescue Rangers.\n\n"
            "This works because you have a cultural duality. Most people are either \"only ours\" or \"only Western\"; you understand the best is the combination.\n\n"
            "Other people sometimes are surprised: \"you watch Smeshariki even now?\". Sometimes. They still hold up.\n\n"
            "What's worth knowing: Soviet animation had a depth modern works rarely touch. If you have kids, don't deprive them of it. They'll appreciate it, even if it doesn't look as polished as Pixar."
        ),
        "Disney и приключения": (
            "Disney and adventure",
            "DuckTales, Chip 'n Dale, Gravity Falls, Avatar: The Last Airbender. What grabbed you were cartoons with real plots. Not \"gags\"; stories with heroes, a world, growth.\n\n"
            "This works because you love narrative. Even as a kid, \"funny\" wasn't enough; you needed a story.\n\n"
            "Other people sometimes are surprised: \"you still love Avatar?\". Still. It's one of the best animated series of all time.\n\n"
            "What's worth knowing: the best animated series survive a rewatch decades later. Watching Gravity Falls at 30 is different from watching it at 12. Learn to come back. It gives a second understanding."
        ),
        "Сатира взрослого": (
            "Grown-up satire",
            "The Simpsons, South Park, Futurama, Rick and Morty. You love animated series that aren't for kids. Sharp social criticism, absurdity, moral ambiguity.\n\n"
            "This works because you have critical thinking. These cartoons aren't \"entertainment\" — they're a commentary on the era.\n\n"
            "Other people sometimes don't share it: \"South Park is just edgy\". Edgy. And smart. And accurate. Those are different things.\n\n"
            "What's worth knowing: these series age unevenly. The Simpsons of the '90s — genius; the modern ones — flat. Learn to watch by season, not back to back. The strongest episodes are usually in the first 5 seasons of any of them."
        ),
        "Магия и приключения": (
            "Magic and adventure",
            "Avatar, Gravity Falls, Adventure Time, Pokémon. What grabbed you were cartoons with magic. Not \"the real world with funny situations\"; another world with its own rules.\n\n"
            "This works because you love fantasy. A purely realistic plot was boring to you; you needed magic.\n\n"
            "Other people sometimes don't get it: \"Pokémon is primitive\". Maybe. But the world of Pokémon is huge, and many adults find it pleasant to come back to.\n\n"
            "What's worth knowing: fantasy cartoons for kids often hold serious adult themes. Avatar is about genocide, imperialism, forgiveness. Learn to see those layers. They're there even if the heroes are cute."
        ),
        "Старая школа": (
            "Old school",
            "Tom and Jerry, Scooby-Doo, Nu pogodi!, DuckTales. You love the classics. Not modern cartoons; the ones your parents watched too — the ones that keep working across decades.\n\n"
            "This works because you understand: a real classic is one that survives generations. And these cartoons are exactly that.\n\n"
            "Other people sometimes are surprised: \"Tom and Jerry has no words\". No words. And that's the genius — a universal language.\n\n"
            "What's worth knowing: old cartoons often hold dated jokes or images. Learn to accept it. It's part of history, and not every moment has to meet today's standards. The art remains."
        ),
        "Безумие и абсурд": (
            "Madness and absurdity",
            "SpongeBob, Adventure Time, Rick and Morty, Futurama. What grabbed you were cartoons that didn't follow logic. The more absurd, the better.\n\n"
            "This works because you love the irrational. Too-logical stories bore you; you need the unexpected.\n\n"
            "Other people sometimes tap their forehead: \"how can you watch SpongeBob?\". I watch. And I laugh.\n\n"
            "What's worth knowing: \"absurd\" cartoons often turn out deeper than they seem. Adventure Time is a post-apocalyptic world, and its absurdity is a mask for philosophy. Learn to look deeper."
        ),
        "Боевики детства": (
            "Childhood action",
            "Teenage Mutant Ninja Turtles, Pokémon, Avatar, DuckTales. What grabbed you were cartoons with action. Battles, adventures, saving the world. This was your school of bravery.\n\n"
            "This works because you have a request for the heroic. Not passive stories; you need the hero to act.\n\n"
            "Other people sometimes are surprised: \"you still watch Turtles?\". Sometimes. And I watch with my kids — let them see too.\n\n"
            "What's worth knowing: action cartoons often simplify morality to \"good vs evil\". Learn to see the simplification. The real world is more complex — and the best modern cartoons (Avatar) understand that."
        ),
        "_default": (
            "Your own childhood mix",
            "You don't have one signature cartoon from childhood. You loved Tom and Jerry, Avatar, the Simpsons — each for its own age and mood.\n\n"
            "This works because you have a wide memory. Most people remember 2-3 cartoons; you remember dozens.\n\n"
            "Other people sometimes are amazed by your encyclopedic recall.\n\n"
            "What's worth knowing: nostalgia for cartoons is a powerful feeling, but sometimes it blocks you from seeing the modern. Kids today watch things that would seem strange to you. Learn not to judge. They have their own childhood, no worse than yours."
        ),
    },
    "your_sport": {
        "Контактный бой": (
            "Contact combat",
            "Boxing, MMA, judo, BJJ, tennis, basketball. You need direct contact with an opponent. Not \"one on one with nature\" — a game where reaction, speed, and technique matter against another human.\n\n"
            "This works because you have a competitive nature. Training without a live opponent bores you; you need to measure, to test.\n\n"
            "Other people sometimes worry: \"what about injuries?\". They happen. But I know what I'm signing up for.\n\n"
            "What's worth knowing: contact sports require discipline and a good coach. Without them — injuries. Don't cheap out on the trainer. And remember: recovery is half the success. Without it, you don't grow — you just break down."
        ),
        "Командная динамика": (
            "Team dynamics",
            "Basketball, volleyball, dance, tennis. You need people next to you. Not solo exercise; rhythm with others, synchronization, a shared goal.\n\n"
            "This works because you have social energy. Sport without people turns into a gym for you — and that's boring.\n\n"
            "Other people sometimes say: \"you could go alone\". I could. But I need the moment when we're together — and then I train longer and better.\n\n"
            "What's worth knowing: team sports require a schedule and people. Without a regular group, you don't grow. Learn to invest in the team, not just in your own form."
        ),
        "Вода и тишина": (
            "Water and silence",
            "Swimming, diving, rowing, surfing. You need water. Underwater the sounds quiet down, on the water the rhythm is steady, in the wave — connection with nature.\n\n"
            "This works because you have a meditative side. Most sports are about tension; water is about relaxation through motion.\n\n"
            "Other people sometimes are amazed: \"how can you spend hours in the pool?\". Hours. It's a different relationship with time.\n\n"
            "What's worth knowing: water sports require consistency. Skip two weeks and your form drops faster than in the gym. Learn regularity. And take care of your ears, sinuses — typical problems for those who spend a lot of time in water."
        ),
        "Природа и движение": (
            "Nature and motion",
            "Hiking, climbing, cycling, rowing. You need fresh air and beautiful places. The gym bores you; you need landscape as part of the workout.\n\n"
            "This works because you have a deep connection with nature. City life doesn't give you oxygen; you compensate with active outdoor time.\n\n"
            "Other people sometimes don't get it: \"why drag yourself uphill for 5 hours?\". Because at the top is what I live for.\n\n"
            "What's worth knowing: nature doesn't forgive mistakes. Learn to pack right, check weather, have a plan B. The most beautiful routes can become dangerous when you're underprepared."
        ),
        "Снег": (
            "Snow",
            "Skiing, snowboarding, winter climbing, snow hiking. You need winter sport. The cold doesn't scare you; you understand there's a special pleasure in snow that no other season offers.\n\n"
            "This works because you love winter. Most people endure winter; you wait for it.\n\n"
            "Other people sometimes are surprised: \"Courchevel?\". Courchevel. And Gudauri, and Sölden. Wherever the slopes are.\n\n"
            "What's worth knowing: winter sports are also a serious investment. Gear, trips, lodging. Learn to plan the season ahead, otherwise prices bite. And insurance is mandatory — injuries in the mountains are serious."
        ),
        "Тело + дыхание": (
            "Body + breath",
            "Yoga, swimming, dance, running. What matters to you isn't \"victory\" but connection with your own body. Through breath, through rhythm, through movement in flow.\n\n"
            "This works because you have a request for integration. Most workouts are about separating \"I am the head, the body is the tool\"; you're looking for where they meet.\n\n"
            "Other people sometimes say: \"yoga isn't a sport\". It's a sport. And one of the hardest, because there's nothing to \"defeat\" — only yourself.\n\n"
            "What's worth knowing: integral practices work on regularity, not intensity. An hour of yoga every day gives more than three hours once a week. Learn to prioritize daily practice over the perfect session."
        ),
        "Дальняя дистанция": (
            "Long distance",
            "Marathon, cycling, hiking, long-distance swimming. You need endurance, not speed. Hour after hour, at your own pace.\n\n"
            "This works because you have patience. Sprinting bores you; you need the challenge to last long.\n\n"
            "Other people sometimes don't understand: \"you do hours of one motion?\". Hours. And every hour is a different landscape inside me.\n\n"
            "What's worth knowing: distance sports require slow building. If you suddenly start a marathon without prep, injuries are guaranteed. Learn gradualness. And remember — recovery matters more than it seems. Not every day a long workout."
        ),
        "Серф и волна": (
            "Surf and wave",
            "Surfing, diving, swimming, rowing. You need water in its wild form. Not the pool — the ocean. Not swimming — interaction with waves.\n\n"
            "This works because you have a deep love for big water. And you understand: the ocean isn't a \"backdrop\", it's an active force you dance with.\n\n"
            "Other people sometimes are afraid: \"what if you drown?\". I won't. I know the water.\n\n"
            "What's worth knowing: the ocean is dangerous. Learn local conditions — every spot has its own logic of currents and waves. Without a local guide in a new spot, don't go in. The most experienced surfers die in unfamiliar water."
        ),
        "_default": (
            "Your own activity mix",
            "You don't have one signature sport. Today the gym, tomorrow the pool, the day after the mountains. This isn't \"undecided\" — it's a multi-sided active life.\n\n"
            "This works because you love motion as a principle. Not \"I run\" or \"I swim\" — \"I move\".\n\n"
            "Other people sometimes can't predict where you're training today.\n\n"
            "What's worth knowing: variety is good but sometimes blocks mastery. If you're at 30% everywhere, you don't reach the level anywhere. Learn to have at least one as \"yours\" — where you grow regularly — and the rest as variety."
        ),
    },
    "cult_90s_series": {
        "Ситком и улыбка": (
            "Sitcom and a smile",
            "Friends, ALF, Married... with Children, Beavis and Butt-Head. Sitcoms of the '90s are closer to you. Simple structure, beloved characters, daily laughter.\n\n"
            "This works because you love comfort. After a hard day you need Joey, not Twin Peaks.\n\n"
            "Other people sometimes get snobby: \"Friends is basic\". Basic. And wonderful.\n\n"
            "What's worth knowing: Friends in 2024 is a different show than in 1994. Modern viewers see \"toxic\" elements. Learn to watch in the era's context. Don't judge what was made 30 years ago by today's standards."
        ),
        "Мистика и тайны": (
            "Mystery and secrets",
            "Twin Peaks, The X-Files, Buffy, Friends. What grabbed you were series with a mystery. Not \"ordinary drama\"; something strange around the corner.\n\n"
            "This works because you love puzzles. A straight narrative bores you; you need something to unravel.\n\n"
            "Other people sometimes don't get it: \"Twin Peaks is weird\". Weird. And beautiful.\n\n"
            "What's worth knowing: '90s mystery series often don't have \"normal\" finales. If you expect Lynch to explain — you'll be disappointed. Learn to accept the mystery as part of the work."
        ),
        "Сатира и ирония": (
            "Satire and irony",
            "The Simpsons, Beavis and Butt-Head, Married... with Children, ALF. You love series that laugh at reality. Not \"entertain\"; criticize.\n\n"
            "This works because you have critical thinking. Just laughing isn't enough; the laughter has to be smart.\n\n"
            "Other people sometimes don't share it: \"Beavis is dumb\". Dumb? It was one of the sharpest satires on American youth.\n\n"
            "What's worth knowing: '90s satire often seems \"insufficiently politically correct\" today. Learn to read cultural context. What was funny in 1995 may have aged; what was accurate stayed accurate."
        ),
        "Подростковая эра": (
            "The teen era",
            "Beverly Hills 90210, Melrose Place, Buffy, Friends. You loved '90s teen dramas. School, love, friendship, crises — everything that defined your generation.\n\n"
            "This works because you have memory of teenage life. These series aren't \"fantasy\"; this is your life packaged into episodes.\n\n"
            "Other people sometimes are surprised: \"you still watch?\". Sometimes. And it's a different experience — watching as an adult what you loved as a teenager.\n\n"
            "What's worth knowing: '90s teen series often romanticize reality. Learn to tell the difference. Real school was closer to pain than to 90210. That's normal — fiction makes things prettier."
        ),
        "Латиноамериканские страсти": (
            "Latin American passions",
            "Santa Barbara, Wild Angel, Tropikanka, Melrose Place. You grew up on \"soap operas\". Endless plots, passions, love, hate, betrayals.\n\n"
            "This works because you love big drama. Restrained European series bore you; you need it bright.\n\n"
            "Other people sometimes get snobby: \"Santa Barbara, really…\". Really. It's an era. And I'm at home in it.\n\n"
            "What's worth knowing: Latin series often run for years and lose quality. If you got stuck in one — that's normal. Not every series has to be \"finished\"; some stay with you just as background."
        ),
        "Российские бандитские": (
            "Russian gangster series",
            "Streets of Broken Lights, Agent of National Security, Santa Barbara, Wild Angel. You grew up on the Russian '90s. Cops, gangsters, gangster Petersburg — that was the background of childhood.\n\n"
            "This works because you have cultural memory. These series aren't \"entertainment\" — they're a document of an era.\n\n"
            "Other people sometimes don't understand: \"those cop shows?\". Those cop shows. They tell more about Russia in the '90s than a textbook.\n\n"
            "What's worth knowing: the '90s now get romanticized (or demonized). Learn to watch these series as ethnographic document. They show a reality that's gone, and the further away it gets, the more valuable they are."
        ),
        "Драма и медицина": (
            "Drama and medicine",
            "ER, Twin Peaks, The X-Files, Buffy. You loved serious dramas. Not comedies and not teen shows; series with real stakes.\n\n"
            "This works because you have a grown-up relationship with TV. Just being entertained isn't enough; the show has to be art.\n\n"
            "Other people sometimes are surprised: \"ER, really?\". Of course. It was the best medical drama of its time.\n\n"
            "What's worth knowing: ER of the '90s is the benchmark for medical drama. Modern shows (House, Grey's Anatomy) are its descendants. Learn to watch the classics. Without them, modern shows make less sense."
        ),
        "_default": (
            "Your own '90s mix",
            "You don't have one signature '90s series. Sitcoms, dramas, Latin, Russian. Each for its own mood.\n\n"
            "This works because you have wide memory of the era. Most people remember 2-3 series; you — dozens.\n\n"
            "Other people sometimes are surprised: \"you were just a kid\". I was. And I watched all of it with my parents.\n\n"
            "What's worth knowing: the '90s came back as a trend. Learn to tell true love from fashion. If you \"remembered\" you loved Friends because everyone's talking about it now — that's fashion. If you always loved it — that's memory."
        ),
    },
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats_by_id = {c.get("id"): c for c in raw}
    arch_done, arch_skip, arch_missing = 0, 0, 0
    for cat_id, tr in TRANSLATIONS.items():
        cat = cats_by_id.get(cat_id)
        if cat is None:
            print(f"  [skip] cat {cat_id} not found"); continue
        # Translate regular archetypes
        for a in cat.get("archetypes", []):
            ru_name = a.get("name")
            t = tr.get(ru_name)
            if not t:
                arch_missing += 1
                print(f"    [warn] {cat_id}/{ru_name!r} no translation in script"); continue
            if a.get("body_en") and a.get("name_en"):
                arch_skip += 1; continue
            a["name_en"], a["body_en"] = t
            arch_done += 1
        # Translate default archetype
        da = cat.get("defaultArchetype")
        if da:
            t = tr.get("_default")
            if t:
                if not (da.get("body_en") and da.get("name_en")):
                    da["name_en"], da["body_en"] = t
                    arch_done += 1
                else:
                    arch_skip += 1
            else:
                arch_missing += 1
                print(f"    [warn] {cat_id}/_default no translation")
        print(f"  ✓ {cat_id}: archetypes processed")
    print(f"\nArchetypes done={arch_done}, skipped={arch_skip}, missing={arch_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch1.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
