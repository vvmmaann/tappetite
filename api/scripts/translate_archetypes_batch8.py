"""Archetype EN backfill — batch 8: Travel (4 cats, ~34 archetypes)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "ideal_city": {
        "Европейский урбанист": ("European urbanist",
            "A city ten times older than you. Bicycle, café and tram — the basis of life."),
        "Азиатский технократ": ("Asian technocrat",
            "Delivery in 15 minutes, metro till morning, efficiency as religion. The future is already there."),
        "Средиземноморская душа": ("Mediterranean soul",
            "Sea, wine, dinner at 22:00, life on the street. You need the rhythm of the south."),
        "Европейский классик": ("European classic",
            "Big capitals with history, museums and culture as oxygen."),
        "Двух-Америк гражданин": ("Two-Americas citizen",
            "Noise, density, the melting pot. You charge from energy, not from silence."),
        "Постсоветский исследователь": ("Post-Soviet explorer",
            "Between Europe and Asia — where cultural borders are still open to the new."),
        "Любитель края мира": ("Edge-of-world lover",
            "The further from the center, the more interesting. Nature beats infrastructure."),
        "Гость восточных культур": ("Guest of Eastern cultures",
            "What grabs you is a different rhythm of life — medinas, bazaars, the muezzin or temples."),
        "_default": ("Nomad without a flag",
            "You don't have one capital — you assemble yourself across different points of the globe."),
    },
    "ny_destinations": {
        "Огни мегаполисов": ("Megacity lights",
            "New York with the ball drop on Times Square, Sydney with fireworks at the opera, Dubai at the Burj Khalifa, Rio at carnival. You need New Year's as an event — massive, loud, with millions of witnesses.\n\n"
            "This works because you have the energy for it. Most people are afraid of crowds; you aren't, and you get a high from the mass scale.\n\n"
            "People sometimes ask: \"you're flying for 30 seconds of fireworks?\". Not for 30 seconds — for the feeling \"I was in this moment, in this place, among these people\".\n\n"
            "What's worth knowing: megacity New Year's is also stress. Crowds, queues, packed hotels. If you don't book months in advance, you'll pay double for half the experience."),
        "Уют и близкие": ("Cozy and close ones",
            "Home with olivier salad and TV shows, in the mountains by a fire, in Prague, in Amsterdam. You need New Year's as an intimate moment — close people, warm light, no noise.\n\n"
            "This works because you understand: the main value of New Year's is who, not where. And you choose by people, not by scenery.\n\n"
            "People sometimes are surprised: \"home again?\". Again. And every time it's the best decision of the year.\n\n"
            "What's worth knowing: cozy New Year's works if you have someone. If you plan \"home with close ones\" but they aren't around — that's not coziness, it's loneliness. Be honest with yourself. Sometimes accepting an invitation beats forcing the cozy plan."),
        "Тропики и побег": ("Tropics and escape",
            "Bali, Maldives, Bangkok, Dubai. You need New Year's without winter. While everyone freezes — you're on the beach, with a cocktail, in shorts.\n\n"
            "This works because you have a healthy relationship with traditions. No one said New Year's must be winter. You break the mold.\n\n"
            "People sometimes don't get it: \"what tree on the beach?\". None. And that's the whole point — a holiday without mandatory props.\n\n"
            "What's worth knowing: tropics on New Year's is also escapism. Sometimes people leave to avoid being with close ones, and then feel sad. Learn to tell \"I'm choosing warmth\" from \"I'm running from something\". The first — great. The second — needs a different solution."),
        "Снег и тишина": ("Snow and silence",
            "A ski resort, Reykjavik with the northern lights, Edinburgh with Hogmanay, mountains by a fire. You need New Year's with real winter — snow, cold, northern traditions.\n\n"
            "This works because you have a romance for the north. The Moscow olivier scene bores you; you need something more atmospheric, with nature.\n\n"
            "People sometimes say: \"but it's expensive\". Expensive. But the impression of the northern lights doesn't compare to anything else.\n\n"
            "What's worth knowing: northern destinations require preparation. Cold, weather, sometimes flight delays. Plan ahead. A spontaneous Reykjavik trip in December can end badly."),
        "Европейская классика": ("European classic",
            "Prague, Barcelona, Amsterdam, Edinburgh. You like New Year's in beautiful European cities. Not \"the event of the century\", just a beautiful backdrop for a small celebration.\n\n"
            "This works because you have a sense of measure. You don't need to fly to Sydney; a beautiful European capital for the weekend will do.\n\n"
            "People sometimes are surprised: \"how many times can you go to Prague?\". Endlessly. Each time it's different.\n\n"
            "What's worth knowing: European classics also mean overcrowded hotels at New Year's. Prices triple. Plan ahead. Booking in August for December is normal."),
        "Восток и культура": ("East and culture",
            "Tokyo in silence, Istanbul on two continents, Bangkok with temples, Dubai. The Eastern New Year's is closer to you — different aesthetics, different traditions, different tempo.\n\n"
            "This works because you're curious about other cultures. Western New Year's tradition is already familiar to you; you need to expand the horizon.\n\n"
            "People sometimes don't get it: \"Tokyo doesn't celebrate New Year like we do\". Not like that. But in their own way — and that's interesting.\n\n"
            "What's worth knowing: Eastern New Year's is a different culture. If you expect from Tokyo a noisy Times Square party — you'll be disappointed. Learn to accept local traditions, not to fit them to your template."),
        "Особый момент": ("Special moment",
            "Northern lights in Reykjavik, two continents in Istanbul, the silence of Tokyo, home with close ones. What matters is that New Year's isn't \"like everyone's\" but with a unique experience.\n\n"
            "This works because you have a desire to collect special moments. Not for Instagram — for your own memory. In 30 years you'll remember exactly these New Year's.\n\n"
            "People sometimes don't get it: \"you're flying so far for one night?\". For one night I'll remember my whole life. Different categories.\n\n"
            "What's worth knowing: \"special moments\" sometimes don't happen. The lights didn't appear, the fireworks were canceled, the weather turned. Learn to accept it. The trip itself is the experience, even if the climax falls through."),
        "_default": ("Your own New Year's format",
            "You don't have one signature place. Each year — a new format: home, beach, mountains. This isn't indecision — it's curiosity.\n\n"
            "This works because you understand: New Year's is both ritual and adventure. And every year you choose by mood, not by habit.\n\n"
            "People sometimes can't predict where you'll be this December.\n\n"
            "What's worth knowing: variety is good, but sometimes worth creating your own tradition. Those who always go to the same place for New Year's have a deep tie to that place — they know it across years. Sometimes worth coming back to feel that depth."),
    },
    "traveler_type": {
        "Исследователь без карты": ("Explorer without a map",
            "Small streets, backpacker, local experience, travel solo. Tourist routes bore you; you need to discover your own.\n\n"
            "This works because you have curiosity. Most people go where \"you have to go\"; you — where you find interesting.\n\n"
            "People sometimes are surprised: \"in this neighborhood?\". This one. And there was the best café of all.\n\n"
            "What's worth knowing: exploration requires preparation for risk. You enter areas a guide won't go. Learn to read situations. And have a plan B in case \"locals\" turn out not so local."),
        "Гастро-турист": ("Gastro-tourist",
            "For food to any country, local experience, beach lounger, luxury tourist. You need to eat. Every trip is first of all a map of restaurants and local markets.\n\n"
            "This works because you have a strong sense of taste. Not \"check off the Eiffel Tower\"; you need to feel the country through its taste.\n\n"
            "People sometimes don't get it: \"you went for the food\". For the food. What's wrong with that? Food is culture.\n\n"
            "What's worth knowing: gastro-tourism is expensive. Good restaurants, Michelin stars, exclusive tours. Learn to balance the budget. And remember: street food is often tastier and more authentic than starred ones."),
        "Музей и культура": ("Museum and culture",
            "Museums, galleries, photographer, slow traveler. You need culture. Not \"relax\" — but learn, immerse, see.\n\n"
            "This works because you have intellectual passion. Travel for you is education, not rest.\n\n"
            "People sometimes get tired: \"three museums today already\". Three. And another tomorrow.\n\n"
            "What's worth knowing: cultural tourism takes physical endurance. Hours of walking in museums wear you out. Plan pauses. And don't try to cover everything — better deep in one museum than shallow in ten."),
        "Расслабиться у моря": ("Relax by the sea",
            "Lounger with a book, lux, shopping, slow traveler. You need rest. Not adventures, not culture. Lying, reading, doing nothing.\n\n"
            "This works because your life is intense already. Travel for you is a pause, not a stuffing.\n\n"
            "People sometimes accuse: \"in Paris you only saw the hotel?\". Yes. I was tired and needed to lie by the pool.\n\n"
            "What's worth knowing: beach rest works while it stays conscious. If you \"didn't make it to anything interesting\", that's on you. You can combine — lie in the morning, walk in the evening. That's not \"laziness\", it's different tempo at different times."),
        "Экстремал": ("Extreme",
            "Mountains, trekking, diving, backpacker, travel solo, photographer. You need adventure. Not \"rest\"; not \"culture\". Adrenaline, difficulty, a test.\n\n"
            "This works because you have a strong nervous system. Most people on vacation want peace; you need to break out of routine grayness through extreme conditions.\n\n"
            "People sometimes worry: \"Nepal alone?\". Alone. And it was the best thing I did.\n\n"
            "What's worth knowing: extreme travel is also serious risk. Don't neglect insurance, guides, local rules. The most experienced travelers die in mountains they thought they knew."),
        "Спонтанный или плановик": ("Spontaneous or planner",
            "Spontaneous tickets, planner, lux, shopping. You're at one extreme: either \"bought a ticket — flying tomorrow\" or \"every hour scheduled\".\n\n"
            "This works because you have a clear style. Most people are in the middle — plan some things, not others, and end up in chronic chaos. You're either one or the other.\n\n"
            "People sometimes don't get it: \"how can you go without a plan?\" — or: \"how can you live by such a rigid schedule?\". Depending on your style.\n\n"
            "What's worth knowing: both styles have weaknesses. Spontaneous often overpay (last-minute tickets are pricier); planners sometimes miss the best (what's not on the plan). Learn from the other camp at least a little."),
        "Городской": ("Urban",
            "Only big cities, shopping, photographer, museums. Nature bores you. You need neighborhoods, culture, motion.\n\n"
            "This works because you have a passion for human life. Nature is for rest; the city is for impressions.\n\n"
            "People sometimes don't share it: \"you don't love mountains?\". I don't. The city is closer.\n\n"
            "What's worth knowing: urban tourism exhausts. Constant noise, crowds, packed streets. If you only do cities, you come back more tired than when you left. At least once a year drag yourself out into nature for a reset."),
        "Мечтатель и медленный": ("Dreamer and slow",
            "I want to but don't go; slow traveler; beach lounger; local experience. You dream about travel more than you actually go. And when you go — slowly, without rush.\n\n"
            "This works because you have a deep relationship with travel. \"Checkmark marathon\" bores you; you need to settle in, and that takes time.\n\n"
            "People sometimes say: \"but you don't go\". I don't. But I dream — that's a kind of travel too, through maps, films, books.\n\n"
            "What's worth knowing: chronic \"want to but don't\" is a form of anxiety. Ask yourself: what's holding me back? Money, time, fear? Each can be solved. Otherwise the dream stays a dream forever."),
        "_default": ("Your own travel style",
            "You don't have one signature style. Sometimes urban, sometimes extreme, sometimes beach, sometimes cultural. Every trip is different.\n\n"
            "This works because you have flexibility. Most people pick one type of rest and fixate; you understand different periods of life need different things.\n\n"
            "People sometimes can't predict where you'll go next.\n\n"
            "What's worth knowing: variety is wealth. But sometimes worth returning to the same place several times. That gives a different depth — you learn it as a local, not as a tourist."),
    },
    "beach_countries": {
        "Доступная классика": ("Accessible classics",
            "Turkey, Egypt, Thailand, Sri Lanka. You pick beach rest not as \"premium\" but as normal — where there's sea, sand, warmth, and it doesn't break the bank.\n\n"
            "This works because you have a mature approach to rest. You don't need to pay for status; you need to actually relax.\n\n"
            "People sometimes get snobby: \"Turkey is basic\". Basic. And I'm comfortable there.\n\n"
            "What's worth knowing: mass tourism has a price — packed beaches, all-inclusive hotels with monotonous food. Learn to pick locations within a popular country. Turkey has quiet places too, not just Antalya."),
        "Премиум-острова": ("Premium islands",
            "Maldives, Bora-Bora, Seychelles, UAE. You need lux. Not \"villa on the beach\" but \"bungalow over water\". This is a different relationship with rest and different money.\n\n"
            "This works because you have both means and understanding of value. These places aren't \"rich-person flexing\"; they're a different type of ocean experience.\n\n"
            "People sometimes accuse: \"for that money you could go to Turkey three times\". You could. But one Maldives trip leaves more memories than three average ones.\n\n"
            "What's worth knowing: premium islands require long planning and a serious budget. Plan ahead. And remember — these are places to go for impression, not for the standard week. Save up and go thoughtfully."),
        "Средиземноморский шик": ("Mediterranean chic",
            "Spain, Italy, Greece, Portugal. You love southern Europe. Not \"islands\" — a whole culture: food, history, architecture plus the sea.\n\n"
            "This works because you have a request for the full package. \"Just beach\" bores you; you need to also do museums, restaurants, walking around.\n\n"
            "People sometimes don't get it: \"why Greece, you can do Turkey\". You can do Turkey. You want Greece.\n\n"
            "What's worth knowing: Mediterranean rest is more expensive than mass-market. But the impressions are different. Invest in longer trips — 7 days in Greece gives more than 3 days on a tour."),
        "Тропический рай": ("Tropical paradise",
            "Bali, Mexico, Cuba, Thailand. You need tropics — real ones, with palms, bungalows, warm ocean. Not European sea; Caribbean or Indian.\n\n"
            "This works because you have a passion for the exotic. Europe is already familiar; you need something further.\n\n"
            "People sometimes worry: \"so far to fly\". Far. And every time — worth it.\n\n"
            "What's worth knowing: tropics are also a serious time-zone and climate change. If you fly for 7 days, half goes to recovery. Plan trips of at least 10 days — otherwise you don't fully enjoy."),
        "Океаны и серф": ("Oceans and surf",
            "Australia, Portugal, Indonesia, Sri Lanka. You pick places with big water. Not enclosed sea; ocean with waves and its own character.\n\n"
            "This works because you love big water. \"Lying on the beach\" bores you; you need something to do with the water.\n\n"
            "People sometimes don't get it: \"you're a surfer?\". Not pro. But I love the ocean, and these places have the best.\n\n"
            "What's worth knowing: \"ocean\" places often don't have all-inclusive. You organize yourself. Accept it. It's a different rest format — more motion, less pool-lounging."),
        "Карибская свобода": ("Caribbean freedom",
            "Mexico, Cuba, Bora-Bora, Seychelles. You need the Caribbean atmosphere — relaxedness, music, colors. This isn't Europe; this is a different mentality.\n\n"
            "This works because you have a request for \"a different rhythm\". European structured rest feels tight; you need \"let it be as it is\".\n\n"
            "People sometimes worry: \"there's risk there\". Sometimes. And sometimes worth it. Life without risk isn't quite that.\n\n"
            "What's worth knowing: Caribbean countries vary in safety and infrastructure. Research the specific place. Cuba and the Maldives are different worlds, both in the tropics."),
        "Восточная экзотика": ("Eastern exotic",
            "Thailand, Sri Lanka, Indonesia, Maldives. You love the East — different culture, food, traditions, plus tropical ocean.\n\n"
            "This works because you have cultural curiosity. \"Lying around\" isn't enough; you need to settle into the unfamiliar.\n\n"
            "People sometimes are surprised: \"Asia again?\". Again. And every time it's different.\n\n"
            "What's worth knowing: Asian destinations require adaptation. Food, climate, sometimes language — all different. If first time, don't try to \"see everything\". Better deep in one place than shallow in three."),
        "_default": ("Your own beach mix",
            "You don't have one signature destination. This year — Turkey, last year — Bali, the year before — Greece. Each year different.\n\n"
            "This works because you have curiosity. Most people return to one place; you try.\n\n"
            "People sometimes are surprised by your travel map.\n\n"
            "What's worth knowing: variety is good, but sometimes worth returning. A place you come back to gains depth — you learn it as a local, not as a tourist. Sometimes better to know one deeply than ten shallowly."),
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
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch8.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
