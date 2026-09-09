"""Archetype EN backfill — batch 3: Brands (3 cats, ~24 archetypes)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "tech_brand": {
        "Эстетика премиума": ("Premium aesthetics",
            "Apple, Dyson, Bose, Nothing. You don't pick \"specs\" — you pick the feeling. These brands don't sell features; they sell experience. And you're willing to pay for it.\n\n"
            "This works because you have a mature relationship with tech. You understood: the spec sheet isn't the whole truth. Build quality, the feel of materials, the sound of the box closing — all part of the product.\n\n"
            "Other people sometimes don't get it: \"why Apple when Samsung is cheaper and faster?\". Because Apple isn't a \"phone\" — it's an ecosystem, a habit, a culture. And I'm comfortable in it.\n\n"
            "What's worth knowing: premium aesthetics costs. Sometimes it's worth checking — are you paying for craft or just for the logo? With the best of these brands the answer is craft. With the worst — only the logo."),
        "Android-волна": ("Android wave",
            "Samsung, OnePlus, Xiaomi, Huawei. You pick Android devices. Not \"cheap instead of Apple\" but a conscious choice: openness, customization, specs, options.\n\n"
            "This works because you have a geek's sensibility. You like that you can change, configure, expand things. Apple is too closed for you.\n\n"
            "Other people sometimes tease: \"still on Android?\". Yes. And there's more freedom here than you'd think.\n\n"
            "What's worth knowing: Android is variety, but also fragmentation. Not all apps have the same quality; updates can be uneven. Learn to choose. Not every Android flagship holds the level of an iPhone — but the best ones do, and they're there if you look."),
        "Microsoft и сервисы": ("Microsoft and services",
            "Microsoft, Amazon, Google, Meta. You're closer to service-companies. Not \"hardware\" — \"cloud\". They give you ecosystem through apps, not through gadgets.\n\n"
            "This works because you understand: the future is in the cloud. Hardware becomes secondary; what matters is data and services, and these companies are strong here.\n\n"
            "Other people sometimes say: \"Apple is cooler\". Apple is great in hardware. In services it often trails Google.\n\n"
            "What's worth knowing: living in cloud ecosystems is convenient, but a risk — your data is theirs, and you're their hostage. Learn to keep copies of important things; don't trust one provider fully. Cloud lock-in is a real cost."),
        "Звук и съёмка": ("Sound and capture",
            "Sony, Bose, DJI, GoPro. You pick gear for a specific purpose: record, film, listen. Not \"all-rounder\" — specialist.\n\n"
            "This works because you have a specific passion. Maybe photography, maybe video, maybe music. And you don't want compromise; you need the best in the niche.\n\n"
            "Other people sometimes don't get it: \"why DJI when your iPhone shoots?\". iPhone shoots. DJI flies. Different things.\n\n"
            "What's worth knowing: specialization needs serious investment. Of money and time. Without regular practice, an expensive GoPro will sit on the shelf. Be honest with yourself: are you really going to use it, or do you just like the idea?"),
        "Бюджетная мудрость": ("Budget wisdom",
            "Xiaomi, OnePlus, Huawei, Amazon. You understood that buying a flagship at flagship prices is silly. You can get 90% of the capability for 50% of the price, and these brands prove it.\n\n"
            "This works because you have a financial instinct. You don't fall for marketing; you look at specs and compare.\n\n"
            "Other people sometimes get snobby: \"you're not on Apple\". Not on Apple. So what? My phone takes better photos than many iPhones, and cost half as much.\n\n"
            "What's worth knowing: budget brands save, but sometimes on materials or support. Learn to tell \"cheap and smart\" from \"cheap and cheap\". The first is a win. The second is a trap that you discover six months later."),
        "Будущее-эксперимент": ("Future-experiment",
            "Tesla, Nothing, Meta, DJI. You like brands doing what no one else has done. Electric cars, transparent phones, VR headsets, drones — all in your focus, because you watch how the world is changing.\n\n"
            "This works because you have a nose for tomorrow. Most people use what's there; you try what just appeared.\n\n"
            "Other people sometimes call you an \"early adopter\". Yes. And yes, you sometimes get burned on raw products. That's the price.\n\n"
            "What's worth knowing: early products are an experiment. If you don't want to be the brand's tester, don't buy the first generation of anything. Wait for v2 — usually most issues are fixed."),
        "Sony-вселенная": ("The Sony universe",
            "Sony — a whole universe. PlayStation, headphones, cameras, TVs. You're not picking one product; you're picking a whole philosophy across all their products.\n\n"
            "This works because you have loyalty to quality. Sony has held the level for years, and you trust it.\n\n"
            "Other people sometimes are surprised: \"is everything you have Sony?\". Not everything. But a lot — yes. And I'm comfortable with them.\n\n"
            "What's worth knowing: Sony is many different teams. Their PlayStation is at one level; their phones at another. Learn to separate. Not every product under the Sony logo reaches their flagship quality."),
        "_default": ("Your own tech mix",
            "You don't have one signature brand. iPhone in your pocket, Samsung laptop, Sony headphones, GoPro for travel. You pick by task, not by loyalty.\n\n"
            "This works because you have a mature relationship with tech. Brand loyalty is an illusion; there's no \"one brand for everything\".\n\n"
            "Other people sometimes accuse: \"you're inconsistent\". I'm consistent in quality, not in logos.\n\n"
            "What's worth knowing: a brand mix means losing the ecosystem. iPhone + Samsung laptop sync worse than iPhone + MacBook. Learn to see where the ecosystem adds real value, and where it doesn't. Don't lose convenience just for the sake of variety."),
    },
    "jewelry_houses": {
        "Французская сказка": ("French fairy tale",
            "Cartier, Van Cleef & Arpels, Chaumet, Piaget. You're in the world of French jewelry. These aren't \"accessories\", they're history — kings, emperors, Parisian ateliers.\n\n"
            "This works because you have a feel for heritage. You understand: a jewel isn't an accessory, it's an artifact.\n\n"
            "Other people sometimes don't tell them apart: \"Cartier is just Cartier\". You know each house has its own signature, legends, collections.\n\n"
            "What's worth knowing: the French school is the peak, but also peak prices. Learn to value more accessible but quality alternatives too. Not every piece needs to be from a French house to be beautiful."),
        "Итальянское барокко": ("Italian baroque",
            "Bvlgari, Buccellati, Pomellato, Damiani. You're in the Italian tradition — where jewelry is expressive, voluminous, with character. Not a \"subtle note\"; full force.\n\n"
            "This works because you love expression. French subtlety bores you; you need passion.\n\n"
            "Other people sometimes are surprised: \"that's a lot\". A lot — and beautiful. Different things.\n\n"
            "What's worth knowing: the Italian school is strong but sometimes goes overboard. Learn to feel the line. A bold piece is beautiful, but in the wrong context, it shouts."),
        "Большие камни": ("Big stones",
            "Graff, Harry Winston, De Beers, Cartier. You value the stones. Not just the piece — a specific diamond or sapphire, with history, weight, legend.\n\n"
            "This works because you have a relationship with the material. What matters is not just \"how it was made\" but \"what from\".\n\n"
            "Other people sometimes are surprised: \"Graff is only for millionaires\". In commercial terms — yes. In understanding — for everyone. Knowing what a real stone is — that's an education, not a purchase.\n\n"
            "What's worth knowing: real big stones are an investment, and not everyone can afford them. Learn to value craft of the cut and rarity, not just size. Carat matters, but a perfectly cut smaller stone can be more beautiful than a clumsy big one."),
        "Японская смелость": ("Japanese boldness",
            "Mikimoto, Tasaki, Buccellati, Piaget. You love when a piece holds subtlety and toughness at once. Japanese pearls with Asian boldness, Italian carving with Japanese precision.\n\n"
            "This works because you have a non-standard view. Classical European tradition bores you; you need something with a different temperament.\n\n"
            "Other people sometimes don't get it: \"Mikimoto is just pearls\". Not just pearls — the start of an entire cultured-pearl industry. It's history.\n\n"
            "What's worth knowing: Eastern houses are less represented abroad. Learn to look. And remember — Mikimoto and Tasaki are best seen in their flagship boutiques, not in tourist outlets."),
        "Голливудский шик": ("Hollywood glamour",
            "Tiffany, Harry Winston, Graff, Chopard. These houses dress stars for the red carpet. You love jewelry with media charm.\n\n"
            "This works because you love glam. You're not embarrassed — you understand that beauty on stage and in film shapes culture.\n\n"
            "Other people sometimes get snobby: \"Tiffany is for teens\". It's for everyone. And their \"blue box\" became a cultural phenomenon for a reason.\n\n"
            "What's worth knowing: Hollywood glam goes mass quickly. Today's Tiffany & Co. isn't the same brand as 30 years ago. Learn to tell classic collections from commercial spinoffs."),
        "Восток и наследие": ("East and heritage",
            "Chow Tai Fook, Mikimoto, Tasaki, Bvlgari. You're closer to the Eastern view. Hong Kong gold, Japanese pearls, Italian ornament — all of it speaks of heritage, tradition, craft passed through generations.\n\n"
            "This works because you love roots. Modern Western brands feel \"soulless\" to you; Eastern ones keep ties to lineage.\n\n"
            "Other people sometimes are surprised: \"Chow Tai Fook? that's Chinese\". Chinese. And one of the most respected jewelry houses in the world.\n\n"
            "What's worth knowing: Eastern houses often work in traditional aesthetics that can seem \"not modern\". That's not a flaw — it's a choice. Learn to see beauty outside the European framework."),
        "Современный люкс": ("Modern luxury",
            "Pomellato, Chopard, Damiani, Van Cleef. You love houses that do the traditional in a modern voice. Not \"classics for grandmothers\" but current collections that hold both history and today.\n\n"
            "This works because you understand: luxury shouldn't be outdated. Houses that don't update lose the young buyer — and with them the future.\n\n"
            "Other people sometimes say: \"you have classical taste\". Not classical — modern. Different things.\n\n"
            "What's worth knowing: modern collections sometimes lose the magic of the classics. Look at both. The best houses keep the dialogue between tradition and now."),
        "_default": ("Your own jewelry taste",
            "You don't have one favorite house. Cartier, Bvlgari, Graff, Tasaki — each for its own mood and occasion. This isn't indecision, it's richness of taste.\n\n"
            "This works because you have an eye. Most people fixate on one brand; you understand each house has its strengths.\n\n"
            "Other people sometimes don't get it: \"you know so many brands\". I do. It's interesting.\n\n"
            "What's worth knowing: wide range needs the means. If you only dream of all houses but own none, learn either to invest in one or two, or to accept that for now this is aesthetic knowledge, not collecting."),
    },
    "recognizable_brands": {
        "Гламур и роскошь": ("Glamour and luxury",
            "Chanel, Louis Vuitton, Ferrari, Mercedes. These are brands that sell not the product — but status and aesthetics. And you understand it. What matters isn't only what the thing does, but what it says about you.\n\n"
            "This works because you have a mature relationship with brands. You don't \"buy Chanel to flex\"; you value the design, the tradition, the quality, and status comes as a bonus.\n\n"
            "Other people sometimes don't get it: \"why Ferrari in Moscow?\". Because Ferrari isn't a car — it's an engineering marvel.\n\n"
            "What's worth knowing: luxury works if it's in your context. A Chanel bag in a student dorm can look out of place, no matter the price. Learn to read the context."),
        "Высокая инженерия": ("High engineering",
            "Mercedes, BMW, Lufthansa, Apple. What grabs you is engineering power. Not \"expensive\" by itself; the certainty that the thing was made with understanding, that there's real complexity inside.\n\n"
            "This works because you have respect for craft. Most people see only the surface; you understand under the hood is years of development.\n\n"
            "Other people sometimes don't tell them apart: \"Mercedes is Mercedes\". You know — there's the S-class, and there are budget Mercedes, and they're different worlds.\n\n"
            "What's worth knowing: engineering power has a price. Maintaining a BMW is more expensive than buying it. Learn to look at total cost of ownership, not just purchase price. The most beautiful machine becomes a burden if you can't sustain it."),
        "Технологические гиганты": ("Tech giants",
            "Apple, Google, Amazon. These are companies shaping our future. You don't just use their products — you understand they're changing the world.\n\n"
            "This works because you have macro vision. Most people see a phone; you see ecosystem, policy, cultural influence.\n\n"
            "Other people sometimes say: \"you really admire them\". Not \"admire\" — analyze. Their influence is too big to ignore.\n\n"
            "What's worth knowing: tech giants are also a concentration risk. The more of you in their ecosystem, the more dependence. Learn to keep freedom — backups, alternative services, the ability to leave. Otherwise you're a hostage to their decisions."),
        "Спорт и драйв": ("Sport and drive",
            "Nike, Red Bull, Ferrari, BMW. These are energy brands. Not for the slow life; for motion, for victory, for everything-now.\n\n"
            "This works because you have an internal drive. You need things that match your tempo.\n\n"
            "Other people sometimes are surprised: \"you're not a pro athlete\". Not pro. But I live like I am.\n\n"
            "What's worth knowing: \"sporty\" brands sometimes become a style without the actual training behind it. If you're all in Nike with no gym days, that's marketing self-deception. Learn to tell."),
        "Еда-напитки массмаркет": ("Mass-market food and drink",
            "McDonald's, Starbucks, Coca-Cola, Red Bull. These are brands of the everyday — what's in every country, every airport, every bad moment when you need a little familiar.\n\n"
            "This works because you have no snobbery. You understand Starbucks isn't \"the best coffee\", but it's standardized everywhere, and that's its strength.\n\n"
            "Other people sometimes accuse: \"you know it's bad for you\". I know. And sometimes I still need it.\n\n"
            "What's worth knowing: mass brands are also a culture and a health system. If you're at McDonald's every day, that's not \"convenience\", it's a habit. Learn to use these brands as occasional pleasure, not the default."),
        "Радость детства": ("Childhood joy",
            "Disney, Coca-Cola, McDonald's, Starbucks. These brands tie to memories. You're not a \"fan\" — you remember: mom took you to McDonald's, the Coca-Cola Christmas tree, Disney films in childhood.\n\n"
            "This works because you have cultural memory. You understand these brands aren't just business; they're shared fabric of an entire generation's childhood.\n\n"
            "Other people sometimes get snobby: \"Disney is for kids\". For kids. And those kids live in us.\n\n"
            "What's worth knowing: nostalgia for these brands is normal. But don't confuse real memories with marketing triggers. Disney professionally sells nostalgia, and sometimes you pay for the feeling, not for what's actually there."),
        "Культурные легенды": ("Cultural legends",
            "Playboy, Disney, Louis Vuitton, Chanel. These aren't just brands — they're cultural institutions. Their logos appear in films, paintings, music. They're part of history.\n\n"
            "This works because you understand the scale. Most people see a logo; you see a century of culture.\n\n"
            "Other people sometimes don't share it: \"Playboy is sexism\". It was. Now it's also cultural archeology and a feminist subject. The brand evolves, and its history is complicated.\n\n"
            "What's worth knowing: cultural brands live long, but not forever. Today's legends can be tomorrow's outdated. Watch which of them keep relevance and which become museum pieces."),
        "_default": ("Your own brand mix",
            "You don't have one signature brand. Apple in pocket, Coca-Cola in fridge, Nike on feet, Disney in childhood memories. Brands are part of your background, not your identity.\n\n"
            "This works because you have a mature relationship. Brands are tools, not flags. You use the ones that work, not the ones that are \"trendy\".\n\n"
            "Other people sometimes are surprised by your mix.\n\n"
            "What's worth knowing: brands are also a cost. The more \"premium\" in your life, the more upkeep. Learn to tell necessary from prestigious. Sometimes a less-known brand is better quality for less money — only your ego needs the famous one."),
    },
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats_by_id = {c.get("id"): c for c in raw}
    arch_done, arch_skip, arch_missing = 0, 0, 0
    for cat_id, tr in T.items():
        cat = cats_by_id.get(cat_id)
        if cat is None: print(f"  [skip] cat {cat_id} not found"); continue
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
            else: arch_missing += 1; print(f"    [warn] {cat_id}/_default")
        print(f"  ✓ {cat_id}")
    print(f"\nArchetypes: done={arch_done}, skipped={arch_skip}, missing={arch_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch3.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
