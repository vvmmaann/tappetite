"""Batch 6: Интернет / Internet — 9 cats, 144 items."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

TRANSLATIONS = {
    "internet_vibe": {
        "name_en": "Your main internet vibe",
        "blurb_en": "What you actually are online",
        "items": {
            "internet_vibe-chronically-online": ("Chronically online", "live online 24/7"),
            "internet_vibe-quiet-luxury":       ("Quiet luxury",       "quiet taste, no logos"),
            "internet_vibe-npc-mode":           ("NPC mode",           "on autopilot, all by script"),
            "internet_vibe-main-character":     ("Main character",     "centered in your own story"),
            "internet_vibe-dark-academia":      ("Dark academia",      "coffee, library, manuscripts"),
            "internet_vibe-soft-online":        ("Soft online",        "pastel, tenderness, aesthetics"),
            "internet_vibe-clean-online":       ("Clean online",       "minimal, sport, clarity"),
            "internet_vibe-y2k-online":         ("Y2K online",         "the noughties with metallic finish"),
            "internet_vibe-vibe-shift-catcher": ("Vibe-shift catcher", "you catch the mood changes"),
            "internet_vibe-doomscroller":       ("Doomscroller",       "scrolling to infinity"),
            "internet_vibe-cottagecore-online": ("Cottagecore online", "cozy, farm, nature"),
            "internet_vibe-trader-online":      ("Crypto/markets trader","charts, tickers, trades"),
            "internet_vibe-nostalgic-2010s":    ("Nostalgic 2010s",    "Vine, Tumblr, the meme era"),
            "internet_vibe-dark-mode-only":     ("Dark mode only",     "no light on the screen"),
            "internet_vibe-creator-wannabe":    ("Creator wannabe",    "streams, videos, editing"),
            "internet_vibe-lurker-forever":     ("Lurker forever",     "see everything, write nothing"),
        },
    },
    "your_social_network": {
        "name_en": "Which social network is really yours",
        "blurb_en": "Where you feel at home",
        "items": {
            "your_social_network-tiktok":    ("TikTok",     "short videos · the algorithm"),
            "your_social_network-telegram":  ("Telegram",   "channels and chats · no algorithm"),
            "your_social_network-instagram": ("Instagram",  "photos · stories · reels"),
            "your_social_network-youtube":   ("YouTube",    "video of any length"),
            "your_social_network-x-twitter": ("X (Twitter)","text · arguments · news"),
            "your_social_network-reddit":    ("Reddit",     "interest forums"),
            "your_social_network-vk":        ("VK",         "Russian network · audio · communities"),
            "your_social_network-pinterest": ("Pinterest",  "moodboards · aesthetics"),
            "your_social_network-discord":   ("Discord",    "voice · servers · gaming"),
            "your_social_network-whatsapp":  ("WhatsApp",   "family · work · groups"),
            "your_social_network-threads":   ("Threads",    "Meta's X alternative"),
            "your_social_network-twitch":    ("Twitch",     "streams in real time"),
            "your_social_network-snapchat":  ("Snapchat",   "vanishing messages"),
            "your_social_network-bereal":    ("BeReal",     "spontaneous photo of the day"),
            "your_social_network-tumblr":    ("Tumblr",     "old-school · blog culture"),
            "your_social_network-linkedin":  ("LinkedIn",   "career network"),
        },
    },
    "messaging_style": {
        "name_en": "Your messaging style",
        "blurb_en": "How they recognize you in ten seconds of chat",
        "items": {
            "messaging_style-voice-long":       ("Voice notes longer than a minute","typing is for the weak"),
            "messaging_style-video-circles":    ("Video circles instead of text",   "face is more alive"),
            "messaging_style-one-word-spam":    ("One word = one message",          "20 in a row"),
            "messaging_style-text-walls":       ("Walls of text",                   "a thought or nothing"),
            "messaging_style-dry-ok-norm":      ("Dry 'ok', 'fine'",                "no emotion"),
            "messaging_style-stickers-only":    ("Stickers instead of words",       "packs for every occasion"),
            "messaging_style-memes-instead":    ("Memes instead of an answer",      "the picture says it all"),
            "messaging_style-ahaha-no-feel":    ("'haha' without the feeling",      "an autoresponder"),
            "messaging_style-emoji-overload":   ("Emoji and exclamations",          "maximum expressiveness"),
            "messaging_style-perfect-grammar":  ("Perfect punctuation",             "even in chat"),
            "messaging_style-answer-in-day":    ("Reply in a day",                  "wasn't around"),
            "messaging_style-answer-instant":   ("Reply instantly",                 "phone always in hand"),
            "messaging_style-ghost-reader":     ("Read but don't reply",            "just took a look"),
            "messaging_style-rewriter":         ("Rewrite 5 times",                 "perfectionism"),
            "messaging_style-schya-disappear":  ("'1 sec' — and disappear",         "always like that"),
            "messaging_style-link-no-context":  ("Send links without words",        "they'll figure it out"),
        },
    },
    "content_format_2020s": {
        "name_en": "Best content format right now",
        "blurb_en": "What you consume the world through",
        "items": {
            "content_format_2020s-tiktok-vert":     ("TikTok video",         "vertical · 15-60 sec"),
            "content_format_2020s-yt-shorts":       ("YouTube Shorts",       "vertical from YouTube"),
            "content_format_2020s-yt-longreads":    ("YouTube video essays", "20+ minutes of depth"),
            "content_format_2020s-podcasts":        ("Podcasts",             "conversation · in headphones"),
            "content_format_2020s-streams":         ("Streams",              "Twitch, Kick · live"),
            "content_format_2020s-reels":           ("Instagram Reels",      "Meta's vertical"),
            "content_format_2020s-tg-channels":     ("Telegram channels",    "post · comments · reactions"),
            "content_format_2020s-tg-chats":        ("Telegram chats",       "group banter"),
            "content_format_2020s-x-threads":       ("X threads",            "a thought across 20 tweets"),
            "content_format_2020s-reddit-discuss":  ("Reddit discussions",   "subreddits · threads"),
            "content_format_2020s-longreads":       ("Long reads",           "Substack · magazines"),
            "content_format_2020s-meme-channels":   ("Meme channels",        "groups and channels"),
            "content_format_2020s-dzen-vk-blogs":   ("Dzen / VK blogs",      "Russian blogging"),
            "content_format_2020s-discord-servers": ("Discord servers",      "interest communities"),
            "content_format_2020s-audio-rooms":     ("Audio rooms",          "Spotify Greenroom · X Spaces"),
            "content_format_2020s-forums-fanfic":   ("Forums and fanfic",    "niche · text · lore"),
        },
    },
    "tiktok_persona": {
        "name_en": "Who you are on TikTok/Reels",
        "blurb_en": "Your role in the fastest feed in the world",
        "items": {
            "tiktok_persona-silent-scroll":   ("Silently scroll for hours",       "no reaction"),
            "tiktok_persona-save-all":        ("Save everything",                 "the collection grows"),
            "tiktok_persona-send-friends":    ("Send to friends",                 "this needs to be seen"),
            "tiktok_persona-comments-fight":  ("Argue in comments",               "the truth matters more than sleep"),
            "tiktok_persona-silent-likes":    ("Silently like",                   "support without words"),
            "tiktok_persona-filming-self":    ("Film your own videos",            "want to make For You"),
            "tiktok_persona-trends-jumper":   ("Jump on every trend",             "viral for everyone"),
            "tiktok_persona-serious-only":    ("Only serious content",            "no dancing"),
            "tiktok_persona-anti-algorithm":  ("Boycott the algorithm",           "For You ≠ yours"),
            "tiktok_persona-friends-only":    ("Subscribed only to friends",      "not bloggers"),
            "tiktok_persona-block-spam":      ("Block in bulk",                   "feed cleanup"),
            "tiktok_persona-report-toxic":    ("Report toxic content",            "the internet's medic"),
            "tiktok_persona-duet-stitch":     ("Duet and stitch",                 "answer with a video"),
            "tiktok_persona-niche-tags":      ("Stay in your niche",              "narrow feed"),
            "tiktok_persona-rewatch-3x":      ("Watch every clip 3x",             "need to understand"),
            "tiktok_persona-month-off":       ("Forget the app for a month",      "and come back"),
        },
    },
    "meme_archetype": {
        "name_en": "Your meme archetype",
        "blurb_en": "The filter you see the internet through",
        "items": {
            "meme_archetype-sarcastic":      ("Sarcastic",            "everything through biting humor"),
            "meme_archetype-toxic-positive": ("Toxic-nice",           "smile with a knife"),
            "meme_archetype-dead-inside":    ("Dead inside",          "sad-funny"),
            "meme_archetype-vibey":          ("Vibey",                "positive vibes only"),
            "meme_archetype-dushnila":       ("The over-explainer (dushnila)","spell every meaning out"),
            "meme_archetype-chaotic":        ("Chaotic neutral",      "zero logic, all good"),
            "meme_archetype-observer":       ("Observer",             "silent, reading everyone"),
            "meme_archetype-ironic":         ("Ironic",               "everything through irony"),
            "meme_archetype-emo-joke":       ("Emo joker",            "sadness + laughter"),
            "meme_archetype-sigma":          ("Sigma",                "loner on chill"),
            "meme_archetype-alt-vibes":      ("Alt girl / alt boy",   "dark aesthetics"),
            "meme_archetype-normie":         ("Normie",               "everything that's popular"),
            "meme_archetype-collector":      ("Meme collector",       "an archive of terabytes"),
            "meme_archetype-family-spam":    ("Family-chat reposter", "boomer folklore"),
            "meme_archetype-memetic":        ("Memetic",              "you make your own memes"),
            "meme_archetype-troller":        ("Troll",                "live for the reaction"),
        },
    },
    "ru_classic_memes": {
        "name_en": "Russian-language memes that will outlive everything",
        "blurb_en": "The phrases you hear and say more than the rest",
        "items": {
            "ru_classic_memes-zhiza":        ("Zhiza",         "that's so true to life"),
            "ru_classic_memes-baza":         ("Baza",          "you said it right"),
            "ru_classic_memes-krinzh":       ("Cringe",        "ashamed to watch"),
            "ru_classic_memes-sigma-meme":   ("Sigma",         "lone alpha"),
            "ru_classic_memes-skuf":         ("Skuf",          "an average dude over 30"),
            "ru_classic_memes-altushka":     ("Altushka",      "girl with dark aesthetics"),
            "ru_classic_memes-ded-inside":   ("Dead inside",   "sad meme vibe"),
            "ru_classic_memes-dushnila":     ("Dushnila",      "tedious pedant"),
            "ru_classic_memes-chushpan":     ("Chushpan",      "weakling · from 'Slovo Patsana'"),
            "ru_classic_memes-chiki-briki":  ("Chiki-briki",   "audio meme · S.T.A.L.K.E.R."),
            "ru_classic_memes-kamon-bro":    ("C'mon bro",     "addressing the in-group"),
            "ru_classic_memes-eto-drugoe":   ("'That's different'","typical argument move"),
            "ru_classic_memes-zumer-cringe": ("Zoomer cringe", "mocking Gen Z"),
            "ru_classic_memes-boomer":       ("Boomer",        "the older generation"),
            "ru_classic_memes-kripovyi":     ("Creepy",        "spooky, weird"),
            "ru_classic_memes-nu-takoe":     ("'Eh, so-so'",   "vague evaluation"),
        },
    },
    "you_in_comments": {
        "name_en": "What you're like in comments",
        "blurb_en": "Pick your comment-section style",
        "items": {
            "silent-liker": ("Silently like",                "see everything · write nothing · ghost"),
            "argue":        ("Argue",                        "can't walk past · have to reply"),
            "baza":         ("Type 'baza'",                  "agree · short · no extra words"),
            "meme-reply":   ("Reply with a meme",            "no words needed · the picture speaks for you"),
            "first":        ("Type 'first'",                 "made it · matters · tradition"),
            "long-comment": ("Write a wall of text",         "have things to say · spell out the thought · no one asked"),
            "heart-react":  ("Drop a heart",                 "support · no words · warmth"),
            "irony":        ("Be ironic",                    "kind of a joke · kind of not · take it as you will"),
            "tag-friend":   ("Tag a friend",                 "this is about you · look · found you here"),
            "correct":      ("Correct the facts",            "actually · source · technically"),
            "lurker":       ("Read others' arguments",       "watching · not joining · with popcorn"),
            "plus-one":     ("Write 'same here'",            "in agreement · not alone · supporting"),
            "question":     ("Ask a question",               "want to understand · clarify · sincerely"),
            "compliment":   ("Praise the author",            "fire · legend · keep it up"),
            "one-word":     ("One symbol or emoji",          "💀 · 🔥 · ??? · all said"),
            "deleted":      ("Type and delete",              "wrote it · thought · no · erased"),
        },
    },
    "your_creator_type": {
        "name_en": "Your creator type",
        "blurb_en": "What's your content style?",
        "items": {
            "vlog":         ("Vlogger",                  "camera in your life · a day from inside · no filters"),
            "edutainment":  ("Educational content",      "explains the complex simply · useful · facts"),
            "humor":        ("Comedy and memes",         "funny · viral · you recognize yourself"),
            "aesthetic":    ("Aesthetic content",        "beautiful · atmosphere · planned to the frame"),
            "review":       ("Reviewer",                 "tests · honest opinion · helps you choose"),
            "storytelling": ("Storyteller",              "stories from life · pulls you in · can't quit"),
            "podcast":      ("Podcaster",                "voice · conversation · listen as background and absorb"),
            "shorts":       ("Shorts master",            "60 seconds · hooks at frame one · doomscroll"),
            "travel":       ("Travel blogger",           "new countries · camera everywhere · want to repeat"),
            "food":         ("Food blogger",             "cooks · tastes · shoots so your mouth waters"),
            "commentary":   ("Commentator and analyst",  "breaks down events · own stance · think along"),
            "challenger":   ("Challenge participant",    "trends · first to try · pulls others in"),
            "gaming":       ("Gaming streamer",          "plays live · reactions · community"),
            "lifestyle":    ("Lifestyle blogger",        "routine · hauls · how they live · you want the same"),
            "motivator":    ("Motivational speaker",     "inspires · personal growth · come out different"),
            "art-creator":  ("Art creator",              "draws · films · creates · content as art"),
        },
    },
}


def main():
    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    cats_by_id = {c.get("id"): c for c in raw}
    cats_done, items_done, items_missing = 0, 0, 0
    for cat_id, tr in TRANSLATIONS.items():
        cat = cats_by_id.get(cat_id)
        if cat is None: print(f"  [skip] {cat_id} not found"); continue
        cat["name_en"] = tr["name_en"]; cat["blurb_en"] = tr["blurb_en"]
        items_tr = tr.get("items", {}); n = 0
        for it in cat.get("items", []):
            iid = it.get("id")
            if iid in items_tr:
                it["name_en"], it["ctx_en"] = items_tr[iid]; n += 1
            else: items_missing += 1; print(f"    [warn] {cat_id}/{iid}")
        cats_done += 1; items_done += n
        print(f"  ✓ {cat_id}: {n}/{len(cat.get('items', []))}")
    print(f"\nCats: {cats_done}, items: {items_done}, missing: {items_missing}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.batch6.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
