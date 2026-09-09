"""Archetype EN backfill — batch 18: Music part 2 (your_2007_pop_rnb + your_2007_rap_hiphop + music_vibe_2020s)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "your_2007_pop_rnb": {
        "Голос десятилетия": ("Voice of the decade",
            "What grabs you isn't dancers, but singers. Those whose voice matters more than image: Beyoncé, Alicia Keys, Amy Winehouse, Adele... 2007 was an era when vocalists could still walk on stage with one piano and hold a stadium. And you listened to exactly them.\n\n"
            "This works because you have an ear for technique. You don't confuse autotune with a real voice, don't consider \"good\" what's only loud. You need real talent behind a note, and you recognize it instantly.\n\n"
            "People sometimes don't share it: \"well Beyoncé, that's mainstream\". You smile. She became mainstream precisely because she's better than most. That's not a flaw, it's a pattern.\n\n"
            "What's worth knowing: focus on vocals closes off genres where the voice matters less. Electronic, experimental, hip-hop — different criteria here. Learn to hear music wider than \"is there a good voice\". Sometimes there's brilliant music with no vocals at all, and it deserves attention too."),
        "Поп-перерождение 2007": ("Pop rebirth 2007",
            "What grabbed you weren't debutantes, but artists who in 2007 lived through a second wave. Britney in crisis and out of it; Gwen Stefani after No Doubt; Fergie after Black Eyed Peas; Nelly Furtado after Loose. All were reborn, and you watched.\n\n"
            "This works because you're interested not in the star herself, but in her drama. How a career develops, breaks, rises from ashes — that's a series for you, and you watched it in real time, through the top charts.\n\n"
            "People sometimes don't understand: \"what did you find in Britney? She had a fall\". Not a fall — drama. And the return from there was more powerful than the rise itself. That's real pop — not \"everything's easy\", but \"everything through\".\n\n"
            "What's worth knowing: focus on star drama sometimes prevents listening to music as music. If you listen to Britney \"because she lived through...\" rather than because the track itself is good, that's no longer music, it's a tabloid. Learn to separate one from the other. Then your perception of 2007 will be deeper."),
        "Танцпол 2007": ("Dancefloor 2007",
            "For you, 2007 is summer in a club. Rihanna with Umbrella, Ciara with dances, Akon with a verse, T-Pain with autotune. You turn this on now and immediately return to that summer: bad smell of hookah, leather jacket, first love, first fight.\n\n"
            "This works because you have a strong connection of music with memories. Every track is a small time machine. You hit play and you're back at 18.\n\n"
            "People sometimes say: \"that's just dance music, simple\". You don't argue. Simple — yes. But exactly because it's simple, it works: it grabs the body instantly, without thought. Not all music has to make you think.\n\n"
            "What's worth knowing: dancefloor nostalgia is a powerful feeling, but also dangerous. If you live in 2007 music only, you have no sounds that will enter your memories of 2025. Learn to at least periodically add something new — otherwise in 30 years you'll listen only to the same things you listened to at 18, and that's sad."),
        "Ритм-секция Тимбалэнда": ("Timbaland's rhythm section",
            "You heard the producer's hand. Timbaland in 2006-2007 sounded everywhere: Timberlake's Justified, Furtado's Loose, Kanye West tracks, Crazy In Love. You recognized his beats by the first second, and that grabbed you — more than the artists themselves.\n\n"
            "This works because you hear not the voice, but the machine. Most are caught by the star's face; you're caught by the construction of the track. That's another level of listening, and it's rare.\n\n"
            "People sometimes are surprised: \"how did you know it was Timbaland?\". And you didn't \"know\" — you heard. His sound was so recognizable that any next track for you was like a signature in the corner of a painting.\n\n"
            "What's worth knowing: interest in producers is great depth, but sometimes deprives you of pleasure from singing. If you only hear \"ah, that's autotune from so-and-so\", music for you turns into a technical school. Learn to sometimes turn off the analyst and just feel. Otherwise you're an expert, but not a viewer."),
        "Драма-икона": ("Drama icon",
            "Britney in crisis. Amy Winehouse, whose life was falling apart before your eyes. Lady Gaga, who wasn't yet Lady Gaga but was already heading toward her. You followed these stories not as a gossip, but as a viewer at an opera whose lead heroine is a pop icon.\n\n"
            "This works because you understand: real stars aren't those for whom everything is even, but those whose life is a plot. Their music acquires an additional layer precisely because of their drama. Without it these would just be good tracks. With it — mythology.\n\n"
            "People sometimes judge: \"again about Amy, leave her in peace\". And you don't disturb the peace — you remember her. That's the best memory: continuing to listen to those who are no longer here.\n\n"
            "What's worth knowing: admiration of tragic fates sometimes turns into romanticization. And then you subconsciously think talent = suffering. That's a harmful idea. Most great ones lived normally, and suffered no more than others. Learn to separate biography from music. Then you love art, not unhappiness."),
        "Новая мужская волна": ("New male wave",
            "Timberlake after NSYNC, Kanye before his everything, Akon before global success, Chris Brown at the moment of debut. 2007 was the year when the male pop/r&b scene was being reborn, and you followed each one.\n\n"
            "This works because you have an ear for \"the moment\". You understood these guys were becoming who they would become right now. In a year Timberlake won't be the same Timberlake, Kanye — different. You caught the moment.\n\n"
            "People sometimes are surprised: \"you have a 2007 playlist?\". Not a playlist — a starting point. From it you can track how they evolved, and how much they changed.\n\n"
            "What's worth knowing: fixation on the \"debut moment\" sometimes prevents seeing the mature. Kanye in 2024 is a different Kanye, and not worse than the one who was. Learn to see an artist as a process, not as a photograph. Then your love for 2007 won't close off 2017 and 2027 from you."),
        "_default": ("2007 in full",
            "You don't have one favorite artist, not one focus. You listened to everything: pop, r&b, dancefloor, dramatic ballads. For you, 2007 is the era as a whole, not separate names.\n\n"
            "This works because you have wide taste. You didn't close yourself in one genre, but let everything that was a hit pass through you. And so your memory of that year is the richest.\n\n"
            "People sometimes are surprised by your memory: \"you remember this? And this? And this?\". You remember. Because you listened.\n\n"
            "What's worth knowing: a wide range is your wealth, but also the risk of remembering nothing deeply. If you have 200 tracks of 2007 in your playlist, and you listened to each once, you have not one \"yours\" among them. Learn to sometimes return to a chosen few — listen to them hundreds of times, until automatic. Only then does a track become yours."),
    },
    "your_2007_rap_hiphop": {
        "Битва альбомов 2007": ("Battle of albums 2007",
            "September 2007: Kanye releases Graduation, 50 Cent — Curtis. A battle that rewrote the industry. You followed it not as a fan of one side, but as a historian — because you understood that at this moment rap was changing course.\n\n"
            "This works because you perceive rap as a cultural event, not just music. You remember Kanye won, and that after this 50 Cent was never the same. And the industry followed the winner — toward intellectual, producer rap.\n\n"
            "People sometimes don't remember: \"a battle, so what\". They don't understand that modern rap began precisely with this battle — without its outcome, there'd be no Drake, no Kendrick in their current forms.\n\n"
            "What's worth knowing: the mythology of battles sometimes overshadows the music. Both Curtis and Graduation are albums, and each is listenable today. Learn to separate \"a historical moment\" from \"sound that reaches you now\". Sometimes a 2007 track sounds better than a 2024 one, and vice versa. Let the criterion be \"do I like it\", not \"is it significant\"."),
        "Большой нью-йоркский лагерь": ("Big New York camp",
            "What grabbed you were the masters of the word from New York. Jay-Z, Nas, Eminem (though from Detroit, but in the New York tradition), Common (though from Chicago, but the same school). It's rap where the word matters more than the beat, where technique matters more than image.\n\n"
            "This works because you value rap as a form of poetry. \"A cool bass\" isn't enough for you — you need rhymes, plot, layers. And you recognized those who did this by the second line.\n\n"
            "People sometimes tease you: \"you're like a boomer: only old school\". You smile. Old school isn't age, it's quality. Contemporaries can do it too — fewer of them, but they exist.\n\n"
            "What's worth knowing: focus on technique can make you deaf to other merits. Sometimes a track is brilliant without complex rhymes, simply because the beat is perfect, or because the vibe catches. Learn to hear not only \"how it's written\", but \"how it sounds\". Then your rap taste becomes fuller."),
        "Юг и Атланта": ("South and Atlanta",
            "What grabbed you was the southern scene. T.I., Lil Wayne, Snoop Dogg in his late form, Pharrell with N.E.R.D. Atlanta and the South defined the sound of the late noughties, and you dissolved into it.\n\n"
            "This works because you have a different sensitivity. Northern rap is about the word; southern — about bodily rhythm. You need a track to rock you, not just make you think. And you found this with the southerners.\n\n"
            "People sometimes don't understand: \"the South is simplistic\". That's superficial. The South isn't simplistic — it has different depth, through sound, not through text. And this depth is no less than the New York one, just structured differently.\n\n"
            "What's worth knowing: preferring the bodily over the textual works in funks, but sometimes deprives you of what the word gives. Learn to combine: sometimes in the playlist listen to narrative, sometimes pure rhythm. Music is both body and head, and one side without the other robs."),
        "Отечественный андеграунд": ("Domestic underground",
            "You listened to Kasta, Basta before he went pop, Smoki Mo, Legalize. It was early Russian rap — without budgets, without glamour, with the real word and the street. You remember how it was before everything became an industry.\n\n"
            "This works because you value originality. You understand this era in Russian rap was the only one when nobody was looking back at the West yet — everyone was making their own school, their own vocabulary, their own vibe. And since then there hasn't been that level of independence.\n\n"
            "People sometimes don't remember these names: \"Smoki Mo? Who's that?\". You nod sadly. That's the problem — real founders are forgotten quickly, and today's scene is built on their shoulders, not realizing.\n\n"
            "What's worth knowing: preserving memory of roots is honorable, but sometimes becomes a refusal of the present. If you say \"everything after 2010 isn't rap\" — you're a captive of nostalgia. Today's guys also do strong work, just in another language. Learn to hear across eras. Roots + trunk + branches — that's one tree."),
        "Ростов-Москва ось": ("Rostov-Moscow axis",
            "You heard Kasta and Basta from Rostov, Smoki Mo and Legalize from Moscow, Timati when he was just starting. It was a scene that physically lived between two cities, and you were part of this geography — even if you lived in a third place.\n\n"
            "This works because you understand: places give birth to sound. Not every rap can be made in any city. The Rostov ones had their own intonation, the Moscow ones — another, and you heard this difference.\n\n"
            "People sometimes don't think about geography. You don't care. You have a map in your head showing where each school was born.\n\n"
            "What's worth knowing: geo-attachment is a great analytical tool, but the world globalizes. Now a rapper in Yakutsk can sound like Atlanta, and vice versa. Learn to track these sound migrations. Geo isn't the predictor it once was."),
        "Мейнстрим-эпоха": ("Mainstream era",
            "Kanye, Lil Wayne, Eminem, Snoop. These guys in 2007 were at the peak of mass popularity. You liked that rap had come out of the underground and become the main music of the era. You weren't ashamed to love mainstream — because mainstream then was good.\n\n"
            "This works because 2007 was an unusual year — mass rap didn't drop in quality, it grew. Loving the top charts wasn't \"cheap\"; in the charts stood albums today considered classics.\n\n"
            "People sometimes confuse you with a modern mainstream fan: \"you listened to mass stuff\". You don't argue. Only the mass of that time was on a different level than the mass of now.\n\n"
            "What's worth knowing: \"the golden mainstream era\" is a rare phenomenon. Now the mass is often weak, and loving it is something else. Learn to hear today's mainstream tracks honestly: something weaker, something at the level of 2007. Sometimes pearls exist now too. Don't reject outright."),
        "Эра альбомов": ("Era of albums",
            "For you, 2007 is the era when the album still mattered. Graduation, American Gangster, Hip Hop Is Dead, Finding Forever — these weren't \"collections of singles\" but whole artistic statements. You listened to an album from start to finish and understood it was a journey.\n\n"
            "This works because you have patience. Most now don't listen to an album past the first three tracks. You — listen. And in this listening, what the artist intended opens up — not what made it into TikTok.\n\n"
            "People sometimes don't understand: \"why listen to all of it if you only like one track?\". Because one track isn't the whole song. The song is the album. That's how it was once intended, and for you it's still true.\n\n"
            "What's worth knowing: the era of albums has ended. That's sad, but reality. Today artists often don't make whole records — only \"track drops\". Learn to accept this. And sometimes return to old albums like a novel you reread — to remember how it was, and why it mattered."),
        "_default": ("Full 2007 in rap",
            "You don't have one favorite — you have the whole era. You listened to everything: Kanye, 50 Cent, Kasta, Timati. You didn't pick a camp because you understood they together formed the picture of the year.\n\n"
            "This is rare maturity. Most people in 2007 were in one camp (Kanye vs 50 Cent, or South vs North, or Western vs Russian). You — no. You listened to everyone, and so today you have the fullest map of the era.\n\n"
            "People sometimes are surprised: \"you really listened to both Timati and Eminem?\". Really. It's different sound, different aesthetics, but the same time. And each of them is part of the portrait of 2007.\n\n"
            "What's worth knowing: eclecticism is your plus, but also a risk. If you listened to everyone a little, you have no \"cult\" thing — the one you know by heart. Sometimes worth picking one album and listening to it hundreds of times, to automatic. That'll give depth that wide range can't. Then your 2007 will be not only wide, but also deep."),
    },
    "music_vibe_2020s": {
        "TikTok-генерируемое": ("TikTok-generated",
            "You hear how the algorithm shapes the sound. Hyperpop, Jersey club, phonk, drill — all these genres took off thanks to short videos. You don't resist, you live in this — and sometimes you like it, sometimes not, but you're aware.\n\n"
            "This works because you understand: today's music is made not for albums, but for 30-second hooks. And an artist who doesn't understand this doesn't survive. You adapted to the new reality and listen by its rules.\n\n"
            "People sometimes call this \"not music\": \"that's just noise for TikToks\". Not just. Behind every viral track stands a person who understood something about sound — and that understanding deserves attention.\n\n"
            "What's worth knowing: TikTok music is often short-lived — took off in a month, three months later already outdated. If you live only in current trends, you have nothing permanent. Learn to select what will outlive the moment. Sometimes even \"TikTok\" tracks turn out to be classics 5 years later — but not all. Learn to tell."),
        "Глобал-стадион": ("Global stadium",
            "You listen to what blows up world charts. K-pop, Sad pop of Billie and Olivia, Country revival with Beyoncé and Zach Bryan, Afrobeats by Burna Boy and Wizkid. \"Mass\" doesn't scare you — because mass now is often good.\n\n"
            "This works because globalization made the charts more diverse. Earlier \"mass\" meant sterile Western pop. Now in the tops can stand Nigerian afrobeats, K-pop, country with fusion elements. You're glad about this.\n\n"
            "People sometimes tease you: \"you're like everyone else\". You're not like everyone else — you understood that \"like everyone\" now means \"global and diverse\", and that's a plus, not a minus.\n\n"
            "What's worth knowing: top charts are a narrow window. Now what's in there is cool, but tomorrow weaker tracks may end up there. Learn not to attach only to the charts. In parallel, dig niches — there are often future stars before the algorithm picks them up."),
        "Альт и инди": ("Alt and indie",
            "You're drawn to alternative. Indie / alternative, bedroom pop, lo-fi, R&B like Frank Ocean and SZA. This is music not for stadiums — for headphones. And you prefer it precisely because it's for one person, not for a crowd.\n\n"
            "This works because you have introverted sensitivity. You need an artist to speak quietly, for you alone. Stadium delivery exhausts you — even if technically it's good.\n\n"
            "People sometimes don't understand: \"that's boring, nothing's happening\". It is happening — just inside. Alternative music works on nuances, on texture, on what isn't immediately visible.\n\n"
            "What's worth knowing: alternative sometimes becomes a refuge for snobs. If you only listen to it and despise mass — that's not taste, that's a pose. Learn to mix: in the evening Frank Ocean for depth, in the morning Beyoncé for energy. Good music is everywhere; genre boundaries are often false."),
        "Танец и клуб": ("Dance and club",
            "You need the body. Techno, hardstyle, jersey club, hyperpop — this is music for movement, not for listening. You don't sit under it in headphones; you walk under it, dance, lose yourself in the rhythm.\n\n"
            "This works because you have a strong connection with the body. You understand that music isn't only thought and emotion, it's also a physical phenomenon. The bass beating in the chest is another way to learn something about yourself.\n\n"
            "People sometimes don't share it: \"that's noise, how can you do that for hours?\". Not for hours — that's another experience of time. On the dancefloor an hour flies in a minute, and you leave from there as if you've gone through transformation.\n\n"
            "What's worth knowing: dance music works best in a live context. At home in headphones techno often sounds flat. Learn to separate: what to listen to alone, what — only in a club. And take care of clubs — that's a disappearing experience, and there are no substitutes for it."),
        "Хип-хоп волна": ("Hip-hop wave",
            "Rap for you is the main food. Global, local, trap, drill, phonk — you're aware of all currents. It's your musical language, and you've spoken it for years.\n\n"
            "This works because hip-hop now is the most diverse genre. Inside it there's everything: intellectual (Kendrick), dance (drill), atmospheric (phonk), stadium (Drake). It's enough for you.\n\n"
            "People sometimes are surprised: \"you only have rap?\". Not only, but it's the foundation. And there are so many subtypes that one person doesn't have time for everything in a lifetime.\n\n"
            "What's worth knowing: mono-genre listening narrows the picture of the world. If you have only rap, you miss a huge layer of music being made in parallel. Learn to at least periodically step outside boundaries — sometimes listen to classical, sometimes indie, sometimes dance. Not to \"develop taste\", but for fresh hearing in your own genre."),
        "Уют и спальня": ("Coziness and bedroom",
            "Lo-fi, bedroom pop, sad pop, indie alt — your niche. Music is quiet, low-intensity, perfect for work, for rain, for solitude. You don't look to \"light a fire\" — you look to \"calm\".\n\n"
            "This works because modern life is already too loud. Notifications, calls, ads, city noise. Music for you is an island of silence, not another source of noise.\n\n"
            "People sometimes tease you: \"you only have sad music\". Not sad — calm. Different things. Calm doesn't make you unhappy, it restores you.\n\n"
            "What's worth knowing: quiet music is wonderful, but sometimes the body demands the loud too. If you're only in lo-fi, you lose connection with the instinct to \"move\". Learn to add something rhythmic and loud sometimes — even if for 30 minutes once a week. The body will be grateful."),
        "Глобал-новая волна": ("Global new wave",
            "You hear how the global map is changing. Afrobeats from Nigeria, country revival with Beyoncé, K-pop, global rap — all these waves are happening simultaneously now, and you swim in them.\n\n"
            "This works because you understand: the era of dominance of the American-British pop scene is over. Music has become truly global, and you don't cling to the past.\n\n"
            "People sometimes can't keep up: \"that's not in English, how to listen?\". You smile. Music doesn't require translation. A good track grabs regardless of language, and you know this.\n\n"
            "What's worth knowing: globalism — powerful, but also superficial. If you listen to Afrobeats only because it's in the charts, you don't know its history and context. Learn to dig deeper into at least one of these new genres — learn the roots, key artists, evolution. Then your listening turns from tourism into real love."),
        "_default": ("Your own 2020s music mix",
            "You don't have one signature genre. Today phonk, tomorrow lo-fi, the day after K-pop. You switch by mood, by context, by moment — and don't consider this indecision.\n\n"
            "This is a rare quality. Most people get hooked on one — and often grow old together with that genre. You're more flexible, and so always in current sound, whoever you are.\n\n"
            "People sometimes are surprised: \"your playlist is schizophrenia\". Not schizophrenia, variety. And you're proud of it.\n\n"
            "What's worth knowing: flexibility is good up to a limit. If you have no \"own\" genre, you listen to everything a little and nothing deeply. Sometimes worth picking one and going deep: one artist for a month, study his discography fully. That'll give depth inaccessible to wide range. Then your mix will be not \"everything in a row\", but \"a lot, but with one serious love\"."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch18.{ts}")
    shutil.copy2(CATEGORIES_JSON, bak)
    print(f"backup: {bak}")

    touched = 0
    skipped = 0
    missing = []

    for cat in cats:
        cid = cat.get("id")
        if cid not in T:
            continue
        mapping = T[cid]
        archs = cat.get("archetypes") or []
        for a in archs:
            name = (a.get("name") or "").strip()
            if name in mapping:
                en_name, en_body = mapping[name]
                a["name_en"] = en_name
                a["body_en"] = en_body
                touched += 1
            else:
                if not a.get("body_en") and a.get("body"):
                    skipped += 1
                    missing.append(f"{cid}: {name}")

        d = cat.get("defaultArchetype") or {}
        if "_default" in mapping and d:
            en_name, en_body = mapping["_default"]
            d["name_en"] = en_name
            d["body_en"] = en_body
            touched += 1

    tmp = CATEGORIES_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON)

    print(f"touched: {touched}")
    print(f"skipped (no body_en, no mapping): {skipped}")
    if missing:
        print("missing:")
        for m in missing:
            print(f"  - {m}")

if __name__ == "__main__":
    main()
