"""Archetype EN backfill — batch 20: Estetika part 1 (aesthetic_vibe + clothing_style + room_aesthetic + current_fashion_style)."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "aesthetic_vibe": {
        "Старая школа элегантности": ("Old school elegance",
            "You don't trust logos and trends. Fabric quality, silhouette, and silence are your language."),
        "Вечная вечеринка": ("Eternal party",
            "You know fashion is cyclical, and you take the maximum from each decade. The brighter, the more honest."),
        "Мрачный интеллектуал": ("Gloomy intellectual",
            "Black suits you. Melancholy isn't a diagnosis, it's an aesthetic decision. A book in your pocket — required."),
        "Романтик деревни": ("Country romantic",
            "The city is noise. You want to bake bread, wear linen, and wake up to birdsong."),
        "Городской уличный": ("Urban street",
            "Sneakers decide everything. You move fast, dress pragmatically, and don't confuse fashion with a wardrobe."),
        "_default": ("Eclectic stylist",
            "You don't have one fundamental vibe — you mix, and that's your superpower."),
    },
    "clothing_style": {
        "Чистая линия": ("Clean line",
            "What grabs you is minimalism. Basic items in neutral tones, Scandinavian functionality, business casual without excess. In your wardrobe everything can combine with everything — because that's your principle of dressing.\n\n"
            "This works because you understood: real style isn't the quantity of things, but their consistency. Minimalism gives you the freedom not to think every morning about what to wear.\n\n"
            "People sometimes call it \"boring\". Not boring — assembled. Different things. Boring is when nothing means anything. Assembled is when each detail is chosen.\n\n"
            "What's worth knowing: minimalism can become a form of fear. If you avoid the bright because \"it doesn't suit\" — that's not taste, it's defense. Sometimes worth wearing something contrasting. Not every day, but sometimes. It keeps your style alive."),
        "Уличный кэжуал": ("Street casual",
            "Streetwear, sneakers, oversize, athleisure, hypebeast — your territory. You understood comfort and style don't contradict, and dress so the body is free and the eye is caught.\n\n"
            "This works because you have a lively life rhythm. You don't sit in an office for eight hours — you move, ride, meet. And clothes should match: allow, not restrict, while serving you well visually.\n\n"
            "People sometimes call this \"unserious\". Seriousness isn't in slacks with creases. Seriousness is in how you do the work. And street style doesn't get in the way of work, on the contrary.\n\n"
            "What's worth knowing: streetwear ages quickly. Limiteds and hypebeasts lose value in a year. Learn to separate the eternal base (good sneakers, quality hoodie) from fashion noise. Otherwise in two years half your wardrobe will be irrelevant."),
        "Тихая роскошь": ("Quiet luxury",
            "Old money, quiet luxury, preppy, business casual without logos. You understood real expensiveness isn't display, it's fabric. Cashmere nobody recognizes but that's felt. A cut that fits perfectly without loud labels.\n\n"
            "This works because you have a mature attitude toward status. You don't need to prove anything to anyone through a brand on the chest. You understand those who can see will see, even without a logo.\n\n"
            "People sometimes don't appreciate it: \"so what, a gray coat\". And the coat is real cashmere for a good amount. And only those who know recognize this. Perfect.\n\n"
            "What's worth knowing: quiet luxury works with those who notice. With others you're just \"a person in boring clothes\". Learn to accept that not every effort will be read. Style is for those who understand it, not for everyone."),
        "Тёмная сторона": ("Dark side",
            "Dark academia, grunge, avant-garde — your territory. Black, leather, torn, autumn shades, sometimes unclear \"what is this even\". You don't dress \"beautifully\" by conventional standards — you dress how you feel.\n\n"
            "This works because you have your own aesthetic, and it's deeper than fashion for you. You don't follow trends — you live in your own visual universe, which stays with you for years.\n\n"
            "People sometimes don't understand: \"why so gloomy?\". This isn't \"gloomy\" — it's serious. Dark tones carry gravity light ones can't.\n\n"
            "What's worth knowing: dark aesthetics are beautiful, but require precision. Black should be perfectly black, not faded. Leather — real. Torn — thought-out. Otherwise you don't look conceptual, you look unkempt. The standard is high, and it must be held."),
        "Y2K-возвращенец": ("Y2K returner",
            "Low waist, metallic shine, vintage, ripped jeans. You bring the noughties back to the 2020s, and you're good with it. Not \"in costume\", but really living in this aesthetic.\n\n"
            "This works because you have a sense of cycle. You understand fashion turns, and Y2K now isn't \"the past\", it's relevant again.\n\n"
            "People sometimes don't catch up: \"that's from 2003?\". From 2003 and now simultaneously. Good things return, and you wear them.\n\n"
            "What's worth knowing: Y2K quickly turns into a caricature. If you're hung from head to toe with shiny and low-rise — that's no longer aesthetics, that's a costume. Learn to dose: one Y2K element in a modern outfit works ten times stronger than a total look."),
        "Природа и нежность": ("Nature and tenderness",
            "Cottagecore, boho, vintage thrift — your niche. Linen, flowers, layers, second-hand with a story. You don't \"dress fashionably\" — you create a visual world around yourself in which you're calm.\n\n"
            "This works because you have a strong connection with nature and with the past. Modern clothing is often sterile and disposable. And you need a story, fabric, or craft to stand behind every item.\n\n"
            "People sometimes call this \"unmodern\". And you smile. Modernity is exactly this polarization: either you're in synthetic mass market, or in something living and chosen.\n\n"
            "What's worth knowing: this aesthetic is beautiful, but not always practical. Linen wrinkles, vintage requires care, layers are harder in heat. Learn to alternate — sometimes more practical days. Otherwise your style becomes tiring even for yourself."),
        "_default": ("Your own mix",
            "You don't have one signature style. In the wardrobe both minimalism, and streetwear, and a vintage find. You dress by mood, not by school.\n\n"
            "This works because you have a flexible sense of clothing. Most people choose one style and hold to it; you understood different days require different forms.\n\n"
            "People sometimes can't classify you: \"now you're in minimalism, now in vintage\". This isn't a contradiction. It's range.\n\n"
            "What's worth knowing: a mix works as long as there's basic logic. If you assemble looks randomly, that's no longer eclectic — it's chaos. Learn to feel a common palette or a common form. Then your mix reads as style, not \"what was clean\"."),
    },
    "room_aesthetic": {
        "Чистая пустота": ("Clean emptiness",
            "Minimalism, Scandinavian, black-and-white. There's nothing extra in your room. Every thing has a function or meaning; everything that doesn't is gone. You dress your room as you dress yourself — without excess.\n\n"
            "This works because you have a clear head, and you need a clear environment around. Chaos in the room = chaos in the head, and you don't want this.\n\n"
            "People sometimes call your room \"cold\": \"like in a hospital\". Not like in a hospital — like in a gallery. Different things. In a gallery there are also few objects, but that doesn't make it cold — it makes it focused.\n\n"
            "What's worth knowing: minimalism requires discipline. If you don't watch, in a year you'll find your \"empty room\" has accumulated things, and the aesthetic is destroyed. Regularly do an audit: what's gone from function? Without this work, minimalism slowly turns into ordinary disorder with white walls."),
        "Тепло уюта": ("Warmth of coziness",
            "Hygge, botanical, \"just home\". Candles, blankets, plants, warm light. Your room is the place where you come to recover. And every element in it remembers this.\n\n"
            "This works because you understand: home isn't \"where you sleep\", it's \"where you live\". And in it should be everything you need for life — not for guests.\n\n"
            "People sometimes are surprised by the number of candles: \"how many can there be\". As many as I want. That's the criterion — not \"as accepted\", but \"as I need\".\n\n"
            "What's worth knowing: coziness is an aesthetic that can become a trap. If your room is too warm and pleasant, you stop leaving. Learn to make home a recovery, not a refuge. The line between these two states is thin, and it's important to track it."),
        "Тёмная академия": ("Dark academia",
            "Dark academia, vintage, industrial loft. Wood, leather, books, dark tones, ceiling beams. Your room is a place where you want to write a novel.\n\n"
            "This works because you have a deep connection with the past and with intellect. You're not \"a modern person in a modern apartment\" — you live in an environment that refers to centuries, to thought, to craft.\n\n"
            "People sometimes don't understand: \"do you live in a library?\". Almost. And it suits me very well.\n\n"
            "What's worth knowing: dark academia requires care for details. If books on the shelf are for beauty, not for reading — that's posing, not style. If a leather chair is cracked not from long use but from poor quality — that also shows. This aesthetic works only with authentic things."),
        "Японская простота": ("Japanese simplicity",
            "Wabi-sabi, minimalism, botanical. Emptiness, nature, imperfect beauty. You understood the Japanese idea — that there's depth in understatement, more meaning in a few objects than in a full room.\n\n"
            "This works because you have a meditative relation to space. You understand a room isn't a container for things, but an organism that lives by its own rules.\n\n"
            "People sometimes call this \"empty\": \"you have nothing\". Not nothing — nothing extra. Different categories.\n\n"
            "What's worth knowing: wabi-sabi requires subtle taste. If you copy the Japanese without understanding, it comes out as a \"poor room\" instead of a \"deep\" one. Learn the difference between minimalism from principle and minimalism from laziness. The first is beautiful. The second is just scarcity."),
        "Maximalist": ("Maximalist",
            "Everything at once, textures, colors, ornaments. Art mess, Moroccan, industrial with bright accents. You're not afraid of \"too much\"; you believe there's more meaning in a large amount of the real than in emptiness.\n\n"
            "This works because you have living emotion. In a minimalist room you're bored. You need the gaze to find something everywhere, every corner to be an adventure.\n\n"
            "People sometimes get lost: \"how do you even orient yourself here?\". Wonderfully. Everything has its place, and I know where. It just doesn't match others' ideas of order.\n\n"
            "What's worth knowing: maximalism isn't \"throw a bunch of things together\". It's curated abundance, and it requires experience. Learn to tell: am I adding this thing because it complements, or because I can't stop? The first is craft. The second is already hoarding syndrome."),
        "Геймер-комната": ("Gamer room",
            "RGB neon, screens, industrial loft with techno accents. This isn't \"a room where you sleep\" — it's your command center. And you take pride that you don't have \"cozy IKEA\" but functional and atmospheric.\n\n"
            "This works because you have a digital life as the main, not additional one. And the room should support this. Light — RGB. Sound — system. Chair — gaming.\n\n"
            "People sometimes are surprised: \"but you sleep here too\". I sleep sometimes. But mainly I live here — and this life requires its environment.\n\n"
            "What's worth knowing: a gamer room often looks teenage. If you want it to look adult, learn balance. Not the whole wall in RGB; not all surfaces are screens. One or two strong elements surrounded by a neutral base — that's already an adult environment. Total neon is the bedroom of a 16-year-old."),
        "Ретро-волны": ("Retro waves",
            "Mid-century modern, marine, Moroccan, vintage. You love when a room refers to eras. Not one — several at once. And from this mix your own style emerges.\n\n"
            "This works because you have an eye for design. You understand each era had its own rhythm, and you can combine the best from different ones in one space.\n\n"
            "People sometimes are surprised: \"is everything from a flea market?\". Not from a flea market — from different eras, chosen. And these are different things.\n\n"
            "What's worth knowing: a mix of eras works as long as there's a common thread. Without it it's just \"a dump of good things\". Learn to find this thread — maybe a common palette, or one country, or one material. Then your vintage mix turns into a style, not a collection."),
        "_default": ("Hybrid room",
            "There's no one strict aesthetic in your room. Something from minimalism, something from coziness, something from vintage. This isn't lack of taste; it's that you have a life, and it doesn't fit into one scheme.\n\n"
            "Most people try to \"make a room in style X\", and often it comes out photogenic but not alive. With you it's the opposite. Not perfect for photo, perfect for life.\n\n"
            "People sometimes can't describe your aesthetic: \"you have it kind of... your own\". Your own. That's the best there can be.\n\n"
            "What's worth knowing: \"your own\" isn't \"random\". If you don't choose consciously but just accumulate what came along — that's no longer style, that's inertia. Once a year do a review: what's truly yours in your room, and what just got stuck from an old version of you? Without this work, the room slowly stops being home."),
    },
    "current_fashion_style": {
        "Чистый минимал": ("Pure minimal",
            "Right now what grabs you is purity. Minimal, normcore, clean girl/boy — a style where the main thing is absence. No decor, no logos, no \"accents\". Just good fabric, perfect cut, clean palette.\n\n"
            "This works because in an era of visual noise, simplicity reads as luxury. You understood this faster than many and dress accordingly.\n\n"
            "People sometimes don't appreciate: \"are you in athleisure?\". Not in athleisure — in a perfectly chosen base set. Big difference.\n\n"
            "What's worth knowing: pure minimal requires quality. A cheap basic item looks like \"nothing\". A good basic — like \"expensive\". The line is thin, and it's in the materials. Don't economize on the foundation. Otherwise your style looks like the absence of style."),
        "Богатый шик": ("Rich chic",
            "Old money, preppy, quiet minimalism. You want to be read as a wealthy person who doesn't need to prove it through logos. It's a very specific signal — and only those who understand it get it.\n\n"
            "This works because you understand the hierarchy of visual codes. A loud brand is for those breaking through. Quiet expensiveness is for those already in place.\n\n"
            "People sometimes don't read it right away. That's normal. Quiet expensiveness is for one's own. Not for the masses.\n\n"
            "What's worth knowing: this aesthetic works only with quality. If you try to assemble it from mass market, it's immediately visible. Learn to invest in few but real things. Better three impeccable than thirty \"as good as can be\"."),
        "Тёмное и техно": ("Dark and techno",
            "Darkwear, techwear, goth/alt. Black, chains, boots, technical fabrics, sci-fi elements. You dress as if you live in a film about the near future — and you're good with it.\n\n"
            "This works because you have visual sense at the edge of reality. You don't dress \"like everyone\"; you create the image of a character from your own narrative.\n\n"
            "People sometimes shy away: \"are you a non-conformist?\". Not a non-conformist — a different school. Just fewer people see this school.\n\n"
            "What's worth knowing: techno aesthetic is wonderful, but in ordinary life sometimes becomes a barrier. If you come to the office in full Rick Owens, you don't \"make an impression\", you cause discomfort. Learn to adapt. One strong element in an ordinary outfit works much more precisely than a total look in an unsuitable environment."),
        "Y2K и винтаж": ("Y2K and vintage",
            "Y2K is returning, and you're on this wave. Vintage from second-hand, coquette with bows, nostalgia for the noughties. You assemble your image from the past, reflashing it into the present.\n\n"
            "This works because you have an eye for the cycle. You understand Y2K now isn't imitating the past, it's recognizing that the noughties had their own taste, which has become relevant again.\n\n"
            "People sometimes don't catch up: \"your mom dressed like that\". Maybe. So what? Good things return.\n\n"
            "What's worth knowing: vintage requires curation. Not every old thing is cool. Learn to select. And remember: Y2K is good in dosed form. A total noughties costume on a 2026 street looks like a caricature; one Y2K element in a modern outfit — like style."),
        "Уличный спорт": ("Street sport",
            "Streetwear, sport casual, athleisure. Sneakers, hoodie, expensive sport. You dress as if at any moment you could run — and you like this vibe of readiness.\n\n"
            "This works because your life rhythm requires mobility. You don't \"make an impression with a suit\"; you live, and clothes support you in this.\n\n"
            "People sometimes reproach: \"you're in athleisure again\". Again. And I'm comfortable in it. Argument exhausted.\n\n"
            "What's worth knowing: athleisure is a powerful genre, but requires quality. Cheap sport looks like \"went to take out trash\". Expensive — like a conscious choice. Learn to tell. And don't wear the same thing day after day — even in sport style there's variety."),
        "Нежность природы": ("Nature's tenderness",
            "Coquette, cottagecore, vintage thrift. Bows, lace, floral prints, tenderness. You're not a \"fashionable person\" in the conventional sense; you create your pastel world, and clothes are part of it.\n\n"
            "This works because you have a strong inner visual universe. Most dress \"as accepted\"; you — \"as you feel\". And this is rare.\n\n"
            "People sometimes are surprised: \"you're like a princess\". Not like a princess — like a person who has inner vision. Big difference.\n\n"
            "What's worth knowing: tender aesthetics are wonderful, but sometimes become a cage. If you don't allow yourself a single \"rough\" element, your style becomes one-faced. Learn to add contrast sometimes — a leather jacket over a lace dress, heavy boots under a light dress. This gives depth."),
        "Технический аутдор": ("Technical outdoor",
            "Gorpcore, techwear, athleisure. Functional fabrics, pockets in all places, mountain shoes in the city. You dress as if at any moment you could climb a peak or walk 20 km.\n\n"
            "This works because you have respect for function. You don't choose clothes \"beautiful\" — you choose working. And in this there's also its own beauty, recognized today by the wide fashion environment.\n\n"
            "People sometimes are surprised: \"are you going hiking?\". No. Just this jacket really is waterproof, and in case of rain I'll stay dry. That's the advantage.\n\n"
            "What's worth knowing: gorpcore looks cool only in the right places. On a date in a restaurant, you in a technical jacket isn't style, it's off-key. Learn to tell situations apart. Morning in the city, in a park, on a walk — yes. At a dinner with the parents of your girlfriend/boyfriend — no."),
        "_default": ("Your current mix",
            "You don't have one signature style right now. You're trying different things, mixing, sometimes switching during the week. This isn't messiness — it's experiment with your identity.\n\n"
            "It's a normal phase. Most people at some point in life go through \"I don't know how to dress\" — and in this period they either freeze in one style, or search. You're searching.\n\n"
            "People sometimes can't classify you. And that's okay — you yourself aren't classified yet.\n\n"
            "What's worth knowing: searching isn't an eternal stage. In a year or two some picture should form. If it doesn't — maybe you're not searching, just sliding on trend. Learn to tell. And remember: there's no \"right\" style. There's yours, which forms when you listen to yourself, not TikTok."),
    },
}

def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats = raw.get("categories") if isinstance(raw, dict) else raw
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(f"categories.json.bak.batch20.{ts}")
    shutil.copy2(CATEGORIES_JSON, bak)
    print(f"backup: {bak}")
    touched = 0; skipped = 0; missing = []
    for cat in cats:
        cid = cat.get("id")
        if cid not in T: continue
        mapping = T[cid]
        archs = cat.get("archetypes") or []
        for a in archs:
            name = (a.get("name") or "").strip()
            if name in mapping:
                en_name, en_body = mapping[name]
                a["name_en"] = en_name; a["body_en"] = en_body; touched += 1
            else:
                if not a.get("body_en") and a.get("body"):
                    skipped += 1; missing.append(f"{cid}: {name}")
        d = cat.get("defaultArchetype") or {}
        if "_default" in mapping and d:
            en_name, en_body = mapping["_default"]
            d["name_en"] = en_name; d["body_en"] = en_body; touched += 1
    tmp = CATEGORIES_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON)
    print(f"touched: {touched}\nskipped (no body_en, no mapping): {skipped}")
    if missing:
        for m in missing: print(f"  - {m}")

if __name__ == "__main__":
    main()
