"""Archetype EN backfill — batch 7: Games (3 cats, ~28 archetypes)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "comeback_games": {
        "Эпос RPG": ("RPG epic",
            "You come back to big RPGs. Witcher, Skyrim, Mass Effect, God of War. Games where you live for forty hours, and every character becomes familiar.\n\n"
            "This works because you love long stories. Running through a plot in two evenings isn't enough; you need time to settle in, inhabit the world, explore.\n\n"
            "People sometimes don't get it: \"how can you spend so much time on one game?\". I don't \"spend\" — I live. Two different things.\n\n"
            "What's worth knowing: epic RPGs are an investment of dozens of hours. If you come back to them, you have to be ready for that immersion. Otherwise the game becomes a weight."),
        "Атмосферный артхаус": ("Atmospheric arthouse",
            "Disco Elysium, Journey, Hollow Knight, Nier: Automata. You like games that work as art. Not \"entertain\" but leave a trace — a mood, a thought, an image.\n\n"
            "This works because you see games as a medium for serious ideas. Most don't believe in that potential; you do.\n\n"
            "People sometimes don't share it: \"that's boring, nothing happens\". It happens — inside.\n\n"
            "What's worth knowing: arthouse games need a different tempo. If you're used to shooters, the meditative Journey will read as \"nothing\". Learn to switch modes — it's a different genre of experience."),
        "Сложно и красиво": ("Hard and beautiful",
            "Dark Souls, Hollow Knight, Nier, Hades. You need games that don't hold your hand. You fall, get up, study the system, and win not from cheats but from mastery.\n\n"
            "This works because you have pleasure from overcoming. Most modern games try \"not to frustrate\"; these — the opposite, demand pain, and that's their high.\n\n"
            "People sometimes don't get it: \"why play if it's so hard?\". Because after winning you feel what easy games simply don't have.\n\n"
            "What's worth knowing: the genre takes time. If you don't have 30+ hours for one game, don't start. Better to delay than to abandon mid-way."),
        "Постапок и дикий запад": ("Post-apoc and wild west",
            "Red Dead Redemption 2, The Last of Us, GTA: San Andreas, God of War. You like worlds on the edge — after catastrophe, on the frontier, in eras of chaos. And you live in those worlds.\n\n"
            "This works because you have an interest in extreme states of society. Calm plots bore you; you need something around you to be falling apart or not yet built.\n\n"
            "People sometimes are surprised: \"you're always in these dark worlds\". Not dark — real. There's more life in them than in the sterile ones.\n\n"
            "What's worth knowing: post-apoc games carry emotional weight. After Last of Us you need to switch. Learn to alternate with lighter ones — otherwise the heaviness accumulates."),
        "Уют и творчество": ("Cozy and creative",
            "Minecraft, Stardew Valley, Undertale, Journey. Games you return to not for adrenaline but for peace. Where you can build, grow, explore without pressure.\n\n"
            "This works because you have a request for slow games. Modern life is fast already; in games you look for pause, not acceleration.\n\n"
            "People sometimes say: \"those are kids' games\". Not kids' — simple. And in simplicity there's a depth most people miss.\n\n"
            "What's worth knowing: cozy games are great rest but not a challenge. If you only play them, you never grow as a gamer. Learn to alternate with ones that throw you a challenge."),
        "Roguelike и метроидвания": ("Roguelike and metroidvania",
            "Hades, Hollow Knight, Undertale, Dark Souls. You like games where you have to do it again. Not \"once and done\"; mechanics and narrative reveal through repetition.\n\n"
            "This works because you have patience. Most people want to finish in one run; you understand repetition holds different depth.\n\n"
            "People sometimes don't get it: \"you died again? and starting over?\". Again. And every time I know a little more.\n\n"
            "What's worth knowing: \"again and again\" is a special temperament. If you're impatient by nature, these games will break you. Learn to tell — is this your school, or just a trend? For some, the genre's loop is meditative; for others, torture."),
        "Открытый мир": ("Open world",
            "Witcher, Skyrim, GTA: San Andreas, RDR 2. You like games where you can go where you want. The plot is one line; around it — a whole life, and you dive into it.\n\n"
            "This works because you love freedom of exploration. One route isn't enough; you need turn-offs, and to take them productively.\n\n"
            "People sometimes get tired of your tempo: \"two hours in one village?\". Two. There's a lot interesting there.\n\n"
            "What's worth knowing: open world can become a trap. If you're constantly distracted by side quests, the main plot you may not finish for years. Learn to balance the wandering with progressing — otherwise the freedom becomes a cage of incompletion."),
        "_default": ("Your own gaming mix",
            "You don't have one signature genre to come back to. Sometimes RPG, sometimes a cozy farm, sometimes metroidvania. Games for the mood, not for school loyalty.\n\n"
            "This works because you have wide taste. Most gamers fixate on one genre; you don't, and you get more from it.\n\n"
            "People sometimes can't predict what you'll launch today.\n\n"
            "What's worth knowing: variety is your wealth, but sometimes it's worth digging deeper into one genre. Fully going through the whole Souls series, or all of one director's filmography — gives a different relationship, unavailable to the broad player."),
    },
    "addictive_game": {
        "Соревновательный шутер": ("Competitive shooter",
            "CS2, Valorant, Apex, Overwatch 2. You return to shooters for competition. Not \"shoot bots\"; you need live opponents, ranking, growth.\n\n"
            "This works because you have a sports instinct. In games you look for the same as in sport — measurable progress.\n\n"
            "People sometimes don't get it: \"why are you back there?\". Because I'm growing.\n\n"
            "What's worth knowing: competitive shooters quickly become work. If you spend hours on \"grinding\" without enjoyment — it's no longer a game. Learn to track."),
        "Battle royale": ("Battle royale",
            "Fortnite, PUBG, Apex, Valorant. You love mass battles. 100 players, one survives. Each match — a separate story.\n\n"
            "This works because you crave adrenaline. In battle royale tension builds, and every winning moment is a small triumph.\n\n"
            "People sometimes get tired of your stories: \"another last-game story\". But it really was interesting.\n\n"
            "What's worth knowing: battle royale eats hours one match at a time. Each match 20-30 minutes, they glue into hours. Learn to set timers. Otherwise your day disappears."),
        "MOBA-волна": ("MOBA wave",
            "Dota 2, League of Legends, Mobile Legends, Hearthstone. You're in MOBAs or card strategies. Deep games that take years to master.\n\n"
            "This works because you have endurance. MOBA isn't \"play for an hour\"; it's years of accumulated knowledge.\n\n"
            "People sometimes don't get it: \"you have 5000 hours already\". Yes, and still far from mastery.\n\n"
            "What's worth knowing: MOBA communities are often toxic. Learn to tune out the chat. Otherwise the game you love becomes a stress source."),
        "RPG-эпос": ("RPG epic",
            "Witcher 3, Cyberpunk 2077, Baldur's Gate 3, Elden Ring. You return to big RPGs for the stories. Long, dense, with serious plot.\n\n"
            "This works because you love to play like reading a book. Not \"a quick session\" — deep immersion.\n\n"
            "People sometimes are surprised: \"100 hours in one game?\". A hundred, and still not enough. There are many layers.\n\n"
            "What's worth knowing: RPG epics take time, and many abandon mid-way. Be honest — do you have the resource for 80 hours? If not, postpone. Better in a year than half-finished."),
        "Открытый мир": ("Open world",
            "GTA V, RDR 2, Cyberpunk, Witcher 3. You need games where you can live. Not \"mission after mission\" — a space where you choose what to do.\n\n"
            "This works because you love freedom. Linear games are a cage; open world is a field.\n\n"
            "People sometimes don't get it: \"you spent two hours on one square?\". Two. There's life there.\n\n"
            "What's worth knowing: open world can become an infinite trap. If you're constantly distracted by side quests, the main story passes you by. Learn to balance."),
        "Уют и ферма": ("Cozy and farm",
            "Stardew Valley, Animal Crossing, Sims 4, Terraria. In games you look for peace. Not battles; a farm, a home, slow life.\n\n"
            "This works because your real life is already intense. In games you don't want more stress; you need the opposite.\n\n"
            "People sometimes don't get it: \"that's boring\". Not boring — calm. Different things.\n\n"
            "What's worth knowing: cozy games are great rest but no challenge. Learn to alternate. Only peace without trial is another form of burnout, through boredom."),
        "Песочница и крафт": ("Sandbox and crafting",
            "Minecraft, Terraria, Roblox, Sims 4. You love when a game gives tools, not goals. What to build, what to turn the world into — your choice.\n\n"
            "This works because you have a creative streak. Going through someone else's plot isn't enough; you need to create your own.\n\n"
            "People sometimes are surprised: \"you play Roblox?\". Roblox. All the kids are there now, and among them are brilliant creators.\n\n"
            "What's worth knowing: sandboxes can become time-sinks. Without goals you can play forever and finish nothing. Learn to set yourself tasks. Otherwise the game becomes idleness."),
        "Метроидвания и Souls": ("Metroidvania and Souls",
            "Hollow Knight, Elden Ring, Stray, Baldur's Gate 3. You love hard solo games with depth. Not \"easy clearance\"; you want it to break your head.\n\n"
            "This works because you have patience for the difficult. Most people don't last; you get pleasure precisely from overcoming.\n\n"
            "People sometimes look at you like a masochist. Not a masochist — I just have a different threshold.\n\n"
            "What's worth knowing: Souls games can become an obsession. If you're stuck on one and trying every evening, doing nothing else — that's no longer love, it's stubbornness. Sometimes a pause is needed."),
        "Карточки и дека": ("Cards and decks",
            "Hearthstone, Clash Royale, Brawl Stars, Mobile Legends. You love short sessions. Card games, mobile strategies, instant matches.\n\n"
            "This works because your time is limited. 3 minutes in line, in a café, in the bathroom — everywhere you can play. And you do.\n\n"
            "People sometimes accuse: \"you're always on your phone\". Not always — short sessions. Different things.\n\n"
            "What's worth knowing: \"short sessions\" accumulate. Ten three-minute ones is half an hour a day. Learn to track. Sometimes worth knowing how much you actually play."),
        "MMO эпоха": ("MMO era",
            "WoW, Path of Exile, Genshin Impact, Honkai Star Rail. You live in MMOs. Not \"play\" — constantly with friends in one virtual world, and that world is a real social environment for you.\n\n"
            "This works because you have real friends there. MMO isn't a game, it's a meeting territory.\n\n"
            "People sometimes don't get it: \"you have friends from a game?\". Yes. And these are real friends, just living in another country.\n\n"
            "What's worth knowing: MMOs eat enormous hours. And interest fades, friends remain — but the game is no longer interesting. Learn to separate \"playing this\" from \"talking to these people\". If only the friendship — you can move it elsewhere."),
        "Социальная дедукция и веселье": ("Social deduction and fun",
            "Among Us, Rocket League, Brawl Stars, Fortnite. You love playing with friends. Not \"solo grind\"; laughter in Discord, and an absurd situation in every match.\n\n"
            "This works because for you the game is social glue. You don't \"escape into a virtual world\"; you play to be with friends more vividly.\n\n"
            "People sometimes are surprised: \"you play Among Us?\". Yes. And in the evening with friends there too. It's the best communication possible.\n\n"
            "What's worth knowing: social games work when you have someone to play with. Without friends they quickly become uninteresting. Learn to value this infrastructure of friendship."),
        "_default": ("Your own gaming mix",
            "You don't have one signature game to return to. Today RPG, tomorrow shooter, the day after — farm. This isn't indecision, it's flexibility.\n\n"
            "This works because you have wide taste. Most gamers get stuck in one genre; you understand different moods need different games.\n\n"
            "People sometimes can't predict what you'll launch today.\n\n"
            "What's worth knowing: variety is good, but sometimes worth picking one game and finishing it. Otherwise you have dozens started and none completed. Learn to finish. It's a different feeling than \"started something else again\"."),
    },
    "gaming_style": {
        "Соло и фарм": ("Solo and grind",
            "Solo grinder, collector, speedrunner, modder. You play alone. You don't need teams; you need your personal goal — collect everything, finish faster, modify to your taste.\n\n"
            "This works because you have internal motivation. You don't need someone next to you pushing you; you're your own coach.\n\n"
            "People sometimes don't get it: \"why play alone if you can with friends?\". Because I need silence and focus. With friends — that's a different pleasure.\n\n"
            "What's worth knowing: solo games work as long as you're in focus. If you're grinding without joy, that's no longer love, it's habit. Learn to track."),
        "Командное": ("Team-based",
            "Teammate, esports pro, streamer, toxic carry. You're in a team. Not \"alone in the field\"; you need people next to you, and you're part of the machinery.\n\n"
            "This works because you have a social need. Games for you are a place of communication, not solitude.\n\n"
            "People sometimes are surprised at your involvement: \"you've been with these people for three years?\". Three. And they're closer to me than some offline acquaintances.\n\n"
            "What's worth knowing: team games are an emotional risk. If your team has a bad day, you'll suffer together. Learn to separate — sometimes worth muting voice and playing solo, to not burn out from others' emotions."),
        "Творцы и моддеры": ("Creators and modders",
            "Builder, modder, peaceful player, explorer. In games you don't \"win\"; you create. Bases, mods, worlds, routes — all that is your creativity.\n\n"
            "This works because you have a creative nature. Games for you are a palette, not an arena.\n\n"
            "People sometimes are surprised: \"you spent an hour in Minecraft just building?\". An hour. And another hour. I have a whole castle there.\n\n"
            "What's worth knowing: creative gaming is a rare school. Many gaming communities don't get it; they're about competition. Learn to find your tribe — other builders, modders, peaceful players."),
        "Лор и философия": ("Lore and philosophy",
            "Lore guru, RPG philosopher, explorer, peaceful. What matters to you isn't the gameplay side but the meaning. Who are these characters, why are they, what is the game saying.\n\n"
            "This works because you have a deep relationship with narrative. Most players run through the plot; you live in it.\n\n"
            "People sometimes are surprised: \"you read all the NPC dialogue?\". All of it. Between the lines, so much is said that without it the game is half.\n\n"
            "What's worth knowing: focus on lore sometimes slows your gaming life. Learn to balance — sometimes run the plot for fun, sometimes dig deep. Not every game requires a doctorate in its universe."),
        "Стратег и тактик": ("Strategist and tactician",
            "Tactician, esports pro, speedrunner, lore guru. You play with your head. Not \"reaction and adrenaline\" — plan, calculation, optimization.\n\n"
            "This works because you have an analytical mind. In games you look for the same pleasures as in chess — wins through foresight.\n\n"
            "People sometimes call you a \"nerd\": \"you're calculating odds again\". I am. And I win because of it.\n\n"
            "What's worth knowing: strategists sometimes lose the feeling of play. If you're constantly \"optimizing\", you can forget that the main thing is enjoyment. Learn to sometimes play \"non-optimally\", just for emotion."),
        "Эмоциональный игрок": ("Emotional player",
            "Kinesthete, casual, streamer, toxic carry. You play emotionally. Not \"cold strategy\"; you need it to be vivid, fun, alive.\n\n"
            "This works because you have a lively nervous system. Games for you are an emotional session, not an intellectual one.\n\n"
            "People sometimes worry: \"why are you shouting?\". I'm not shouting — I'm living.\n\n"
            "What's worth knowing: emotional gaming exhausts. If every match for you is swings from rapture to rage, you're burning yourself. Learn to regulate. Not every game requires the emotional max."),
        "Профи и турниры": ("Pro and tournaments",
            "Esports pro, speedrunner, tactician, streamer. You don't \"play for fun\"; you train. For hours, daily, with a goal.\n\n"
            "This works because you have an athletic mode. Most people play to relax; you — to grow.\n\n"
            "People sometimes don't get it: \"you don't earn from this\". Not yet. And not necessarily. I just want to do one thing well.\n\n"
            "What's worth knowing: \"I'm not a pro but I play like one\" is a dangerous state. If you have no real tournaments and contract but you live like a player, you have neither balance nor income. Be honest with yourself — am I an enthusiast hobbyist, or am I drifting?"),
        "_default": ("Your own gaming mix",
            "You don't have one signature gaming style. With one game you're a solo grinder, with another a team tactician, with a third a lore guru. This isn't sloppiness, it's adaptability.\n\n"
            "This works because you have a flexible relationship with games. Different games need different approaches, and you switch for each.\n\n"
            "People sometimes are surprised: \"you have different styles in different games?\". Yes. Each game requires its own.\n\n"
            "What's worth knowing: flexibility is wealth, but sometimes you don't reach deep mastery in any style. Learn to sometimes pick one game and go deep — that gives a different feeling of mastery."),
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
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch7.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
