"""Archetype EN backfill — batch 19: Music part 3 (ru_music_2020s + mood_artist + rodnye_00e). Last Music batch."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "ru_music_2020s": {
        "Провокация и шоу": ("Provocation and show",
            "What grabs you are those who make not music but performance. Morgenshtern, INSTASAMKA, Macan, Slava Marlow — these aren't \"performers\", they're characters who sell their story in the form of tracks.\n\n"
            "This works because you understand the modern Russian scene: here it's not the sound that wins, but the narrative. Whoever knows how to create a myth around themselves is in the charts. Music is just packaging for the show.\n\n"
            "People sometimes condemn: \"that's not music, that's clowning\". And you don't argue. It shouldn't be \"music\" in the classical sense. It's a mix of pop-art performance and audio, and it's interesting to follow.\n\n"
            "What's worth knowing: characters age quickly. The scandal that makes a star today looks vulgar tomorrow. If you only listen to provocateurs, your playlist updates every six months. Learn to add something that will outlive scandal — artists with a real musical base, not only marketing."),
        "Тёмная сцена": ("Dark scene",
            "Pyrokinesis, Kishlak, Lida, KhKhOS — your territory. Dark rap, anxious lyrics, aggressive sound. You're not looking for \"the light\" — on the contrary, it matters to you that music reflects what's dark inside you.\n\n"
            "This works because you have unprocessed emotions, and ordinary pop can't handle them. You need artists who don't smooth over but amplify. Then your pain becomes understandable — it has a soundtrack.\n\n"
            "People sometimes worry: \"you're listening to something too dark, are you ok?\". Sometimes okay, sometimes not. But music isn't the cause here — it's the mirror. And taking the mirror from you is foolish.\n\n"
            "What's worth knowing: dark music reflects the dark, but doesn't heal. If you're in a bad state and listen only to aggressive rap, you can amplify your state, not work through it. Learn to alternate: sometimes reflection of pain, sometimes something light for contrast. Otherwise you get stuck in one emotional tone, and it's hard to leave."),
        "Phonk-волна РФ": ("RU phonk wave",
            "KhKhOS, ICEGERGERT, Kishlak — you're at the center of the Russian phonk scene. It's a unique phenomenon: a genre born in Memphis was reflashed by Russian producers into something recognizably ours. And you hear this specificity.\n\n"
            "This works because you have an ear for the new. You didn't wait for phonk to become a global trend — you heard it in 2020-2021 when it was still a niche. And you still distinguish who's doing the \"real thing\" from who's chasing hype.\n\n"
            "People sometimes don't understand: \"that's just bass and slurred words\". And you hear that inside there's structure, schools, authors. It's not homogeneous noise — it's a scene with history, even if short.\n\n"
            "What's worth knowing: the phonk scene is quickly commercializing. What was underground in 2021 now plays in TikTok clips. Learn to track which artists keep authenticity and which sold themselves to the algorithm. That's real loyalty to the genre — following its evolution, not only consuming the top."),
        "Поп-короли 2020-х": ("Pop kings of the 2020s",
            "ANNA ASTI, HammAli & Navai, Tima Belorusskikh, Slava Marlow — that's your soundtrack. Lyrical pop-rap with catchy choruses, romance without extra philosophy, exactly what you want to hear in the morning marshrutka.\n\n"
            "This works because you understand: sometimes you need exactly simple music. Not \"deep\", not \"conceptual\", but the kind that goes in without explanations and stays with you for weeks.\n\n"
            "People sometimes condemn: \"that's pop\". And you don't feel embarrassed. Pop is actually a complex genre; making a chorus that catches millions of people is a rare skill, and these artists have it.\n\n"
            "What's worth knowing: pop hits are passing. What now grabs the whole country, in two years will be awkward to hum. That's not bad — pop has that nature. But if you have a playlist of only current hits, you have no \"eternal tracks\" to return to in ten years. Learn to add the durable too, not only the fashionable."),
        "Лирический рэп": ("Lyrical rap",
            "Pyrokinesis with poetry, Tima Belorusskikh with stories, Skriptonit with verses, HammAli with romance. It matters to you that there's a word behind the rap — real work with language, not just rhymes over a beat.\n\n"
            "This works because you have an ear for text. Most listen to rap for the sound, you — for what's said. And so from the same tracks you extract three times more meaning.\n\n"
            "People sometimes are surprised at your ability to quote whole verses. You didn't \"learn\" them — you just listened attentively, and the text stuck to memory itself, because it was well-written.\n\n"
            "What's worth knowing: focus on the word sometimes overshadows sound. If an artist writes brilliantly but sounds average, you can overrate them. Learn to hold both filters: text OR sound — that's half; text AND sound — that's the full thing. The best artists are strong in both, and worth keeping the bar."),
        "Качовый рэп": ("Pumping rap",
            "Big Baby Tape, Skriptonit, Platina, Lida — your territory. You need verses that pump, beats that hit the chest, and delivery from which the body moves.\n\n"
            "This works because you have a physical connection with music. You don't sit and \"analyze\" — you move. And so artists who make pumping music matter more to you than those who make \"smart\" music.\n\n"
            "People sometimes don't understand: \"nothing's said in the track\". And you didn't come for \"said\". You came for the body to respond to sound. And when it responds — that's full communication, without words.\n\n"
            "What's worth knowing: pumping music is great fuel, but bad company in long moments. Morning before work — yes. An evening with a friend — yes. But for a quiet evening at home or for a complex emotional moment — no. Learn to tell situations apart. Then your playlist always works."),
        "Земфира как маяк": ("Zemfira as a lighthouse",
            "Zemfira isn't an artist, it's an era. You listened to her in the 2000s, in the 2010s, and in the 2020s she's still relevant. That's a rare phenomenon on the Russian scene — where most stars burn out in 5-7 years, and she's been shining for 25.\n\n"
            "This works because Zemfira makes not \"Russian pop\", but her own tradition. Fashion doesn't touch her, trends don't touch her. And so when everything around ages, she remains.\n\n"
            "People sometimes are surprised: \"you're like the elderly\". You smile. Zemfira isn't \"old\", she's eternal. Different categories.\n\n"
            "What's worth knowing: lighthouses are wonderful, but they're alone. If you only have Zemfira, you have no connection with what's happening now on the Russian scene. Learn to combine: Zemfira as foundation + contemporaries as pulse. Then your sense of Russian music is full, not museum-like."),
        "_default": ("Your own RU 2020s mix",
            "You have the Russian scene of the 2020s in its full spectrum in your headphones. Today ANNA ASTI, tomorrow Skriptonit, the day after Pyrokinesis, then Zemfira again. You're not tied to one camp.\n\n"
            "This is rare. Most people choose one side: either \"pop\", or \"real rap\", or \"eternal Zemfira\", and despise the rest. You understood these categories are a trap, and listen by track, not by camp.\n\n"
            "People sometimes don't believe: \"you have both Morgenshtern and Zemfira in your playlist?\". Yes. They're both about modern Russia, just speaking different languages. And both truths are real.\n\n"
            "What's worth knowing: the breadth of taste is your strength, but sometimes becomes a hindrance when picking \"yours\". If you don't have a favorite artist of this era, you'll have nothing to tell about it in 20 years. Learn to choose one or two you return to regularly. That's your personal connection with the era."),
    },
    "mood_artist": {
        "Меланхолия и атмосфера": ("Melancholy and atmosphere",
            "You need artists who sound like fog over the city at night. Billie Eilish with her whisper, Lana Del Rey with Californian sadness, Frank Ocean with slow albums, The Weeknd with synthwave regret.\n\n"
            "This works because you have an ear for nuance. Most need loud emotion to feel something. For you, silence and one long note are enough — and you're already there, in the right mood.\n\n"
            "People sometimes worry: \"did something happen to you?\". Nothing happened. This is just your native music. You don't suffer in it, you live in it.\n\n"
            "What's worth knowing: atmospheric music is wonderful, but sometimes becomes a small world that's hard to leave. If you only listen to it, you get used to one register of emotion — muted. And active joys in your life can start to feel like \"too much\". Learn to alternate: melancholy + sometimes something brightly alive."),
        "Поп-универсалы": ("Pop universalists",
            "Taylor Swift, Ariana Grande, Beyoncé, Justin Bieber — artists who can do everything. Their tracks play at weddings, in gyms, in headphones, in supermarkets. They are the common currency of pop music, and you're friendly with it.\n\n"
            "This works because you're not embarrassed by mainstream. These artists aren't in the charts by accident — they did everything to be there. And when you need \"just a good song\", you go to them.\n\n"
            "People sometimes accuse you: \"you have no taste, you listen to what everyone listens to\". You don't argue. Sometimes \"what everyone listens to\" is exactly the best. Not all mainstream is deserved, but these earned it.\n\n"
            "What's worth knowing: pop universalists are a safe choice, but safety is boring. If you only have Taylor and Ariana in your playlist, you miss a huge layer of less mass but sometimes more interesting music. Learn to spend at least 20% of time on something less obvious. That keeps your ear in fresh shape."),
        "Драма поколения Z": ("Gen Z drama",
            "Olivia Rodrigo, Billie Eilish, Lana Del Rey, early Taylor — artists who translated into music what young people feel. Love disasters as the end of the world, disappointments as philosophy, anxiety as a vibe.\n\n"
            "This works because in their tracks you hear your own life. Most \"adult\" artists sing about things that don't touch you. And these — about what you're going through now, and from this you feel you're not alone.\n\n"
            "People sometimes devalue: \"that's teenage drama\". Well yeah. You have it now, and music about it isn't shame, it's support. What adults call \"teenage\" is often the most important.\n\n"
            "What's worth knowing: dramatic music intensifies feelings. If you're in stress, it deepens you into stress. Learn to distinguish: when you need \"feel with me\" (then drama helps), and when \"get out of this\" (then something else is needed — energy, lightness, distraction)."),
        "Хип-хоп интеллектуалы": ("Hip-hop intellectuals",
            "Kendrick Lamar with narrative, Frank Ocean with meditation, Tyler with production, SZA with vulnerability. This isn't \"rap for pumping\" — it's rap for thinking. And you spend hours with it, not minutes.\n\n"
            "This works because you hear rap as modern literature. These artists have a story, image, idea in every track. And listening to them superficially means missing three-quarters of the value.\n\n"
            "People sometimes are surprised: \"how do you find so much in one track?\". You don't \"find\" — it's there. Most just don't listen carefully.\n\n"
            "What's worth knowing: intellectual rap is wonderful, but requires attention. If you listen to it as background at work — you lose the meaning. Learn to separate: this music — separately, in headphones, without multitasking. Otherwise you consume it without tasting. And then you're surprised why \"I think I heard it but don't remember\"."),
        "Трэп-стадион": ("Trap stadium",
            "Drake, Travis Scott, Post Malone, Bad Bunny — artists whose tracks rumble from any phone on the street. This is music for mainstream vibe, it's everywhere, and you're on the road with it.\n\n"
            "This works because you have no snobbery. If a track grabs, you don't care that millions listen to it. You don't try to stand out by taste — you just listen to what you like.\n\n"
            "People sometimes call you out: \"Drake is mass, you'd find something more interesting\". You shrug. Mass — because good. That's not always true, but in the case of these guys — often yes.\n\n"
            "What's worth knowing: trap stadium dominates now, but it won't always be that way. When the wave changes, your playlist may turn out outdated. Learn to at least periodically track what's coming next. Not to change taste, but to understand the sound landscape. Then you have both the favorite and the general map."),
        "Альт и инди": ("Alt and indie",
            "Arctic Monkeys, The 1975, Radiohead, Coldplay — for you the British/alternative scene remains the main one. Guitars, lyrics, conceptual albums. You didn't move with the pop wave to trap — you stayed in guitar music, and it feeds you.\n\n"
            "This works because you have an ear for classical instruments. In a world with more and more synthesizers and autotune, you need live guitars and a real drum kit. It's a different feeling — more grounded.\n\n"
            "People sometimes tease you: \"you're stuck in 2010?\". Not stuck — chosen. Different things. You understand a lot is happening in indie and alt now too, just not in the charts.\n\n"
            "What's worth knowing: guitar music indeed left the mainstream, but that doesn't mean it died. It just moved to a niche. Learn to dig niches — that's where real indie lives now, more interesting than stadium Coldplay. If you stay only with old heroes, you'll miss the live scene."),
        "Латино-карнавал": ("Latin carnival",
            "Bad Bunny, Doja Cat, Post Malone on the Latin side, sometimes Ariana with her Spanish elements. What grabs you is music that has heat, rhythm, the voice of carnival. This isn't \"calm music\" — it's a celebration.\n\n"
            "This works because you have inner liveliness. You need a track to fire you up, not calm you. The Latin wave dominates globally now, and you're at its center.\n\n"
            "People sometimes don't understand: \"you don't speak Spanish, how do you listen?\". And you don't need to speak. Music isn't about words, it's about vibe. And the Latin vibe is recognizable without translation.\n\n"
            "What's worth knowing: an eternal celebration tires. If you only have fiery music in your playlist, you don't let the nervous system rest. Learn to alternate: Latin in the morning for energy, something calm in the evening for relaxation. Otherwise you're constantly ready to dance — and lose the ability to just rest."),
        "Русские иконы": ("Russian icons",
            "Zemfira, Skriptonit, ANNA ASTI, Morgenshtern — your Russian scene. You don't ignore the local in favor of the global; for you Russian music is an equal part of your listening.\n\n"
            "This works because you understand: the language of your life is Russian, and emotions in it land deeper. An English track is interesting. A Russian one is about you.\n\n"
            "People sometimes are surprised: \"nothing interesting is being made in Russia\". You smile. They just don't listen. Skriptonit did more for Russian rap than most Western rappers did for their genre. Zemfira is one of a kind.\n\n"
            "What's worth knowing: love for the Russian scene is wonderful, but sometimes limits. These artists themselves grew on Western ones, and hearing their roots is another level of understanding. Learn to dig the Western too. Not to break from the native, but to deepen it."),
        "Русский трэп и phonk": ("Russian trap and phonk",
            "Big Baby Tape, the phonk wave (Kordhell, ICEGERGERT), Macan, Morgenshtern — the Russian side of modern aggressive music. You're at the center of a genre that exploded more powerfully in Russia than anywhere else.\n\n"
            "This works because Russian trap and phonk aren't a copy of Western. They have their own intonation, their own slang, their own delivery. You hear this specificity and value it.\n\n"
            "People sometimes don't share it: \"that's just noise\". Not noise. It's a scene with history that began only 5 years ago and produced several bright names in that time. You caught everything from the very start.\n\n"
            "What's worth knowing: young scenes commercialize quickly. What was fresh in 2020, by 2025 is already mass-copied. Learn to track which artists keep authenticity. Otherwise in a couple of years you'll find yourself in an imitative wave that's loud but says nothing new."),
        "K-pop сторона": ("K-pop side",
            "BTS, BLACKPINK, NewJeans — K-pop in your playlist. This isn't \"a teenage hobby\" — for you it's another full scene, just as serious as any Western one.\n\n"
            "This works because K-pop now is one of the most diverse scenes in the world. Inside it there's everything: stadium power of BTS, conceptual explosion of aespa, retro vibe of NewJeans. You're not \"a fan of K-pop in general\", you listen to specific groups for specific things.\n\n"
            "People sometimes tease you: \"you're a Korean fan?\". Yeah. So what? The same scene as the Western one, just in another language.\n\n"
            "What's worth knowing: K-pop is an industry that works on intense cycles. Groups take off quickly, age quickly, new ones come constantly. If you don't follow updates, your playlist will age in a year. Learn to either accept this tempo and update, or pick one or two eternal groups as anchors."),
        "Стадионный катарсис": ("Stadium catharsis",
            "Coldplay, Adele, Beyoncé, Taylor Swift — artists whose concerts are 70 thousand people crying simultaneously. You need artists-cathartists who can gather a stadium into one emotional explosion.\n\n"
            "This works because you have a strong sense of the collective. Music for you isn't only personal experience; also shared. And the strongest moments are when thousands sing one line with you simultaneously.\n\n"
            "People sometimes don't understand: \"Coldplay is banal\". And you know banality is exactly what unites. Because banal is shared, and shared is human. And in this is strength, not weakness.\n\n"
            "What's worth knowing: stadium music works in the stadium. In headphones it often sounds \"too much\". If you only have epic in your playlist, you get used to one intensity and lose sensitivity to the subtle. Learn to alternate: epic for big moments + chamber for everyday. Otherwise everything turns to noise."),
        "_default": ("Your own music cocktail",
            "You don't have one signature artist. You listen by mood — today Billie, tomorrow Skriptonit, the day after NewJeans, then Coldplay. You have a playlist that doesn't fit any genre.\n\n"
            "This works because you have a flexible ear. Most people get stuck in one sound and don't leave for years. You — no. You understand different moods need different music, and under each you have your own hero.\n\n"
            "People sometimes can't predict what's in your headphones today. With you there's always a surprise.\n\n"
            "What's worth knowing: flexibility is wonderful, but sometimes deprives of depth. If you listen to everyone a little, you have no \"yours\" — an artist you return to in any mood. Learn to choose one or two you really invest in: know the discography, read interviews, understand the evolution. That gives another level of closeness to music, inaccessible to the wide listener."),
    },
    "rodnye_00e": {
        "Тёмный буст": ("Dark boost",
            "t.A.T.u., Leningrad, early Zemfira, Timati — the energy of rebellion and provocation lives in your 00s playlist. You remember these artists weren't just \"the pop of that time\" — they shocked, pushed, broke rules.\n\n"
            "This works because you have memory of how fresh it was. t.A.T.u. — two girls playing at a romance, and the whole world discussed them. Leningrad with profanity that was banned on air. Zemfira with songs that seemed \"too much\". In the 00s it was all new.\n\n"
            "People sometimes don't understand how important it was: \"t.A.T.u. and t.A.T.u.\". And you remember the whole world looked at Russia through them then. It was our first global pop story.\n\n"
            "What's worth knowing: nostalgia for the 00s rebellion sometimes prevents seeing the 20s rebellion. There are provocateurs now too, just in another language. If you're only in the past, you miss the live troublemakers of the present. Learn to hear across eras. Rebellion is an eternal genre, and each decade has its own heroes."),
        "Танцпольные хиты": ("Dancefloor hits",
            "Diskoteka Avariya, Ruki Vverh, Dima Bilan, Smash!! — your soundtrack of graduations, school discos, early clubs. This isn't \"deep music\", it's music of the body and the moment.\n\n"
            "This works because these tracks are wired in you at a reflex level. You turn it on — and you don't \"listen\", you're immediately there. On the parquet, for the first time, with those you no longer talk to but remember to this day.\n\n"
            "People sometimes get snobby: \"that's primitive pop\". You smile. Primitive — yes, but what an effect! This primitive pop does to you what the most complex albums won't — instantly returns you to age 15.\n\n"
            "What's worth knowing: 00s dance pop works only with those who lived it. Young people now hear \"cringe\" in it, and that's normal. Don't try to convince — it's yours, and it stays yours. Just keep it as a capsule: for your moments, for your company."),
        "Лиричный поп": ("Lyrical pop",
            "Alsou, Andrey Gubin, Korni, Smash!! — your lyrical side of the 00s. What mattered to you were songs that have a story, a feeling, a light sadness. Not \"light up the dancefloor\", but \"listen to in headphones, looking out the bus window\".\n\n"
            "This works because in the 00s the Russian pop scene still knew how to be lyrical without ironic break. Just direct pop, without irony and without hype. Now there's almost nothing like that left.\n\n"
            "People sometimes are surprised: \"you listen to Gubin?\". Yes. And you're surprised that at 25 he wrote lyrics deeper than many modern \"deep\" artists at 35.\n\n"
            "What's worth knowing: 00s lyrical pop has its own subtlety that's hard to convey to a new listener. If you try to \"sell\" Gubin to a friend — they may hear only the arrangement, not the text, and say \"pop is pop\". Learn to value silently. Not every pleasure requires sharing."),
        "Девичий гламур": ("Girl glamour",
            "Serebro, VIA Gra, Fabrika, Kraski — your female pop glamour of the 00s. These were the years when Russia started seriously making girl groups, and you caught this generation in its peak form.\n\n"
            "This works because you have an ear for the industry. You understand Serebro and VIA Gra weren't \"random teams\", they were producer projects with a thought-out concept. And you're interested in following how it worked.\n\n"
            "People sometimes devalue: \"glamour pop, girls in dresses\". Not only. Behind every such group stood real work: vocals, choreography, image. It was the first school of Russian girl groups, and K-pop hadn't even appeared with us yet.\n\n"
            "What's worth knowing: glamour pop ages quickly visually. When you watch 00s clips now, the dating is visible. But it often still sounds good. Learn to separate one from the other: visual is the film of an era, the soundtrack — can be more eternal than it seems."),
        "Мальчишеские бренды": ("Boy bands and heartthrobs",
            "Ivanushki International, Smash!!, Korni, Dima Bilan — boy bands and solo heartthrobs of the 00s in your memory. Those who filled female dreams and posters on the walls of teenage rooms.\n\n"
            "This works because you have a specific connection with this aesthetic. Maybe you were a fan, maybe your friends were, maybe it was the background of your childhood. In any case you remember what these guys meant.\n\n"
            "People sometimes laugh: \"Ivanushki International, seriously?\". Seriously. They were an industry. Then there weren't \"three main boy bands of the world\"; in Russia Ivanushki were the peak of this genre.\n\n"
            "What's worth knowing: 00s boy brands often sound awkward today. That's normal. The aesthetic was different, and don't try to defend it before skeptics — they won't hear it. Just enjoy in solitude, for your own pleasure."),
        "Бунт и ирония": ("Rebellion and irony",
            "Leningrad with profanity, t.A.T.u. with provocation, Fabrika with irony toward girl glamour, Timati with young insolence. Ironic energy lives in your 00s playlist — toward yourself, toward the era, toward pop as such.\n\n"
            "This works because you understood back then: not everything popular needs to be taken seriously. And artists who didn't take themselves seriously seemed smarter to you than those who pulled serious faces.\n\n"
            "People sometimes don't tell rebellion from just hype. You distinguish. Leningrad is musical satire with a real school. t.A.T.u. is global provocation with a thought-out strategy. And behind each stood not \"random scandalousness\" but intelligence.\n\n"
            "What's worth knowing: irony in music ages unevenly. What was fresh in 2003 may seem flat in 2024. Learn to listen to the ironic with attention to context. And remember: the ironic genre demands complex work from you — to hear how much is irony and how much is just \"crude or vulgar\". Not everyone manages this equally well."),
        "Хрупкость и протест": ("Fragility and protest",
            "Early Zemfira, lyrical Gubin, Alsou with her fairy-tale purity, Korni with teenage tenderness. You listened to what was fragile and honest in the noisy 00s.\n\n"
            "This works because you knew how to hear the quiet in the loud. The 00s were years of provocation and dancefloor; and in this stream only real fragility survived, because it was the opposite of the whole era. And you defended it with your own listening.\n\n"
            "People sometimes are surprised by your taste: \"you have Alsou and Zemfira at the same time?\". Yes. They're two sides of one fragility — one fairy-tale, the other rebellious. And both about what was hard to keep in an era of mass noise.\n\n"
            "What's worth knowing: fragile music requires silence around to be heard. In a noisy life it gets lost, and over time you can stop hearing it. Learn to regularly create silence — an hour without notifications, headphones, a window — and in it listen to those who write subtly. Otherwise the subtle dies from your own busyness."),
        "_default": ("00s in all layers",
            "You don't have one signature 00s hero. You listened to everything: dancefloor, lyrics, rebellion, glamour. For you, the noughties are an era as a whole, and each layer of it has its right to be in your playlist.\n\n"
            "This works because you have wide taste. Most people in the 00s were in one camp: \"I only listen to Zemfira\", \"I only listen to Ivanushki\". You understood these camps were artificial, and listened by track, not by belonging.\n\n"
            "People sometimes are surprised: \"you have t.A.T.u., and Alsou, and Leningrad?\". Yes. It's all one time, one country, one youth. And each of them is part of the portrait of that decade.\n\n"
            "What's worth knowing: a wide range of an era is wealth, but also the risk of becoming a \"collector of memories\" instead of a live listener. If you're only in the 00s, you don't perceive what's happening now. Learn to at least periodically come out of nostalgia. Today's also worth hearing — even if it doesn't deliver the same warmth."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch19.{ts}")
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
