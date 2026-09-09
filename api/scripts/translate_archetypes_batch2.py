"""Archetype EN backfill — batch 2: Tech (2 cats) + Books (2) + Social (3) = 7 cats / ~57 archetypes."""
import json, shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

T = {
    "ai_tool_2020s": {
        "Текстовые универсалы": ("Text generalists",
            "ChatGPT, Claude, Gemini, Perplexity. You use AI as a text helper. Not for photos, not for video; you need words — generation, translation, analysis, search.\n\n"
            "This works because your life lives in text. Documents, emails, notes. And AI cuts the work down by an order of magnitude.\n\n"
            "Other people sometimes don't believe it: \"so a neural net writes for you?\". Doesn't write — helps. That's different.\n\n"
            "What's worth knowing: text AI is a tool, not a replacement. If you stop writing yourself and just use it, the skill atrophies. Learn to alternate with your own writing."),
        "Образ и видео": ("Image and video",
            "Midjourney, Sora, DALL-E, Stable Diffusion. You live in visual AI. Pictures, video, concept art — all of it can be generated, and you do.\n\n"
            "This works because you have visual thinking. Faster to show than to say; AI gives you the chance to create visuals without art school.\n\n"
            "Other people sometimes object: \"but it's not real art\". Maybe. But it's a tool, and I use it as craft.\n\n"
            "What's worth knowing: AI pictures replace the execution but not the idea. If you have no idea of your own, AI won't make one. Learn to think first. Without an idea AI gives you generic output."),
        "Код и продуктивность": ("Code and productivity",
            "Copilot, Cursor, v0/Bolt, Claude. You use AI for code or product design. This is no longer a \"helper\"; it's part of your daily toolkit.\n\n"
            "This works because your job needs code, and AI here isn't \"trendy\" — it really speeds you up by multiples.\n\n"
            "Other people sometimes doubt: \"but AI writes wrong code\". Sometimes. My job is to fix that. AI handles the rough work.\n\n"
            "What's worth knowing: AI in code requires understanding code. If you're not a developer, AI won't make you one. Learn the fundamentals. Without them AI just speeds up your misunderstanding."),
        "Музыка и голос": ("Music and voice",
            "Suno, ElevenLabs, Runway, Sora. You use AI for sound and video. Music generation, voice cloning, editing — that's yours.\n\n"
            "This works because you have a creative request for media that AI now makes accessible. You can produce things that used to require a studio.\n\n"
            "Other people sometimes can't believe it: \"you made the music yourself?\". With AI — yes. And that help doesn't make it less mine.\n\n"
            "What's worth knowing: AI music and voice are evolving fast but still detectable. Use as a draft, then polish. That makes the work yours, not AI-generated."),
        "Встроенные помощники": ("Built-in assistants",
            "Copilot in Office, Notion AI, Perplexity in search, Gemini in Google. You don't \"go to AI\" — it lives inside your familiar tools, working next to the task.\n\n"
            "This works because you have a healthy relationship with AI. You don't summon it like a magical genie; you use it where it already shows up in your workflow.\n\n"
            "Other people sometimes are surprised: \"you use Notion AI?\". I do. It writes summaries for me, well.\n\n"
            "What's worth knowing: built-in AI is often weaker than dedicated tools. ChatGPT is usually smarter than Notion AI; Claude smarter than Copilot. Sometimes step out of the convenience for the better tool."),
        "Open source и специфика": ("Open source and specifics",
            "Stable Diffusion, Cursor, v0/Bolt, Claude. You like tools that are either open source or very specialized. Control and flexibility matter to you, not a \"convenient service\".\n\n"
            "This works because you have a geek's nature. You don't like depending on a cloud provider; you want to be able to run locally, modify, use without an account.\n\n"
            "Other people sometimes don't get it: \"but ChatGPT is more convenient\". More convenient. And less free.\n\n"
            "What's worth knowing: open source AI usually trails the best closed models. That's the price of freedom. Sometimes it's worth working with a 70%-as-good model for the flexibility."),
        "Локальные и российские": ("Local and Russian",
            "YandexGPT, GigaChat, ChatGPT, Claude. You use both Western and Russian AI. Not out of patriotism, but practice: different models have different strengths, and sometimes the local one knows context better than the global one.\n\n"
            "This works because you have a pragmatic approach. You're not a \"loyal fan of one company\"; you use what works for the task.\n\n"
            "Other people sometimes are surprised: \"YandexGPT, really?\". Yes. For Russian-language content it's often more accurate.\n\n"
            "What's worth knowing: local AI is improving faster than it seems. Track updates. What was weak a year ago can be on par with global ones today."),
        "_default": ("Your own AI mix",
            "You don't have one signature AI. ChatGPT for text, Midjourney for pictures, Cursor for code, Suno for music. The tool fits the task.\n\n"
            "This works because you understand: different AIs are good at different things. Most people get stuck on one and try to do everything with it; you saw that's silly.\n\n"
            "Other people sometimes are surprised by how many subscriptions you have.\n\n"
            "What's worth knowing: many subscriptions is also a cost. Once a quarter, audit: which AIs do you actually use, which are you forgetting? Not every one needs a subscription. Sometimes 2-3 key ones are enough; the rest by single requests."),
    },
    "what_i_ask_ai": {
        "Текст и контент": ("Text and content",
            "You write with AI. Posts, emails, essays, resumes, jokes. AI is a co-author, not a replacement. You bring the idea; it helps formulate it faster.\n\n"
            "This works because your life writes a lot. Dozens of texts a week; without AI it would be hours. With it — minutes.\n\n"
            "Other people sometimes object: \"but then it's not your text\". It's mine. AI helps, but the idea and the final choice are mine.\n\n"
            "What's worth knowing: AI assistance sometimes makes texts \"correct but generic\". Learn to add your voice. Without editing, AI text is recognizably sterile."),
        "Понимание и решение": ("Understanding and solving",
            "You need to explain, break down, solve, find. AI for you is tutor, analyst, search engine in one. And it quickly turns \"unclear\" into \"clear\".\n\n"
            "This works because you have the habit of figuring things out. Most people skip what's unclear; you don't.\n\n"
            "Other people sometimes are amazed: \"how do you know so much?\". I don't know — I ask. That's different.\n\n"
            "What's worth knowing: AI is a great explainer, but sometimes oversimplifies or errs. Verify important facts. And remember: figuring it out with AI isn't memorizing it. Learn to consolidate."),
        "Креатив и идеи": ("Creative and ideas",
            "You use AI for brainstorming. Ideas, pictures, design, jokes — your creative lab. AI generates, you select.\n\n"
            "This works because you have a filter. AI outputs a lot of garbage. But your strength is sorting gems from the pile.\n\n"
            "Other people sometimes don't get it: \"but it thought of all of it\". Not all. I set the direction, picked the best, refined. That's work, just a different kind.\n\n"
            "What's worth knowing: AI creativity is often standard. The best ideas come when you think first and then check with AI. Not the other way around. Otherwise you get an averaged solution."),
        "Работа кода": ("Working with code",
            "You're a developer, and AI is a pair of extra hands. Write a function, fix a bug, refactor, format. Work speed grows 3-5x.\n\n"
            "This works because you understand what you're doing. AI accelerates those who already can. And you use that multiplier.\n\n"
            "Other people sometimes are afraid: \"AI will replace developers\". It won't. It will amplify. Only those who learn to work with it.\n\n"
            "What's worth knowing: AI writes code fast but not always correctly. And sometimes the correctness only shows through tests. Don't trust AI code without verification. And remember: AI can't be entrusted with architecture. That's still human work."),
        "Учёба и подготовка": ("Study and prep",
            "You use AI for prep. For an interview, exam, presentation, project. It helps structure, generate questions, find material.\n\n"
            "This works because you take prep seriously. Most people show up unprepared; you arrive with homework done, and you win because of it.\n\n"
            "Other people sometimes ask: \"so AI helps you in interviews?\". Helps in prep. In the interview — me. That's different.\n\n"
            "What's worth knowing: AI prepares you well for standard scenarios. But real interviews or exams can go off-script. Prepare wider than you think. AI is the base; reality requires improv too."),
        "Бытовая помощь": ("Everyday help",
            "Translate, format, help me decide, write something simple. You don't ask AI for the big things; you use it for small daily tasks, and that saves you hours a week.\n\n"
            "This works because you don't have inflated expectations. Many people wait for AI miracles; you use it as a calculator for text. And that's enough.\n\n"
            "Other people sometimes don't believe: \"such a small thing, you can't do it yourself?\". I can. But AI is faster.\n\n"
            "What's worth knowing: everyday AI use is the most mature level. No hype, no expectations. Just a tool. Protect this attitude. Many people slowly start \"believing in\" AI and then get disappointed."),
        "Эмоциональное": ("Emotional use",
            "You sometimes talk to AI like a conversation partner. Not \"solve a task\" — \"help me sort out my feelings\", \"listen\", \"give an outside view\". That's a different level of AI use.\n\n"
            "This works because AI doesn't judge. With a friend, you can feel them thinking; with AI, you don't. And sometimes that's a great relief — to talk without someone else's reaction.\n\n"
            "Other people sometimes worry: \"AI instead of a therapist?\". Not instead. In addition.\n\n"
            "What's worth knowing: AI isn't a therapist, and serious problems should be discussed with a real specialist. Learn to tell the difference. AI is good for sorting out a current situation; a real therapist works with patterns over time."),
        "_default": ("Your AI mix",
            "You use AI for very different tasks. Today code, tomorrow text, the day after emotional sorting. AI is a multi-purpose tool for you.\n\n"
            "This works because you have flexibility. Most people get stuck on one application; you use AI broadly.\n\n"
            "Other people sometimes are surprised: \"you have AI everywhere?\". Everywhere it's faster than me.\n\n"
            "What's worth knowing: broad use requires being able to formulate requests. If you can't \"prompt\" well, AI works at 30% capacity. Learn to. A good prompt is half the result."),
    },
    "essential_books": {
        "Русская классика": ("Russian classics",
            "Master and Margarita, Crime and Punishment, War and Peace, Lolita. You're in the Russian tradition. Not the school program; living reading where these books are still relevant.\n\n"
            "This works because you have a deep relationship with language. Russian prose has its own density, and you feel it.\n\n"
            "Other people sometimes are amazed: \"Dostoevsky for fun?\". For fun. What's wrong with that?\n\n"
            "What's worth knowing: Russian classics need context. Without understanding the era, much is lost. Learn history in parallel. And don't rush — better to read one 600-page book slowly than three quickly."),
        "Антиутопии и предупреждения": ("Dystopias and warnings",
            "1984, Fahrenheit 451, The Shining, The Master and Margarita. What grabs you are books that warn. Not \"entertainment reading\"; serious reflection on the world and the human.\n\n"
            "This works because you have civic instincts. Most people read for pleasure; you — to understand where society is heading.\n\n"
            "Other people sometimes say: \"you're gloomy\". Not gloomy — attentive. These books aren't written by accident.\n\n"
            "What's worth knowing: dystopias hit hard. Read several in a row and you start feeling \"it's all over\". Learn to alternate with more positive literature. Reality is more complex, and books are part of the picture, not the whole."),
        "Фэнтези-эпопеи": ("Fantasy epics",
            "Harry Potter, Lord of the Rings, A Game of Thrones, Dune. You need big worlds. Not \"one book\"; a series you live in for years.\n\n"
            "This works because you have patience and love for worlds. Many books feel cramped; you need something to live inside.\n\n"
            "Other people sometimes don't get it: \"how many times have you reread Harry Potter?\". As many as needed. It's home.\n\n"
            "What's worth knowing: series often sag. Five Martin books — three brilliant, two weak. Check fan ratings before each next one. And don't be afraid to drop a series that lost quality."),
        "Магический реализм": ("Magical realism",
            "One Hundred Years of Solitude, The Master and Margarita, The Little Prince, Lolita. You like books where reality is blurred. Not pure \"fantasy\"; prose where dream and reality are woven together.\n\n"
            "This works because you have a poetic perception. Pure realism bores you; you need something with a different texture.\n\n"
            "Other people sometimes don't share it: \"One Hundred Years of Solitude is just nonsense\". Nonsense is exactly Marquez's genius. Literature can be illogical, and only stronger for it.\n\n"
            "What's worth knowing: magical realism needs attention. If you read Marquez on the subway between notifications, you lose half. Carve out quiet time."),
        "Американская классика": ("American classics",
            "The Great Gatsby, To Kill a Mockingbird, The Catcher in the Rye, The Shining. You love 20th-century American literature. Not \"mass culture\"; serious prose that defined an era.\n\n"
            "This works because you're interested in American culture. Through these books you understand the country deeper than through any movie.\n\n"
            "Other people sometimes ask: \"you read in English?\". Sometimes. Translation loses a lot.\n\n"
            "What's worth knowing: American classics are often culturally specific. If you don't understand the American South, To Kill a Mockingbird reads at 50% depth. Learn parallel history."),
        "Путь и взросление": ("Path and growing up",
            "The Catcher in the Rye, The Little Prince, To Kill a Mockingbird, One Hundred Years of Solitude. You need books about a person's growth. Not \"adventures\"; the inner transformation of the hero.\n\n"
            "This works because you have your own request for growth. Through books you look for patterns to apply to yourself.\n\n"
            "Other people sometimes are surprised: \"you read it as self-help?\". Not as self-help. As a mirror.\n\n"
            "What's worth knowing: coming-of-age books work best at \"the right age\". Catcher in the Rye at 16 is a different book than at 36. Learn to come back to them. Re-reading gives a different depth."),
        "Научная фантастика": ("Science fiction",
            "Dune, Fahrenheit 451, 1984, The Shining. You like literature that explores possible worlds. Not \"fantasy\"; science and technology as a philosophical problem.\n\n"
            "This works because you have intellectual sensitivity. You need a book to ask questions, not just tell a story.\n\n"
            "Other people sometimes don't get it: \"sci-fi is for geeks\". Maybe. But many of the best 20th-century books are sci-fi. And they're about the present more than many realistic novels.\n\n"
            "What's worth knowing: sci-fi requires patience. Dune is 800 pages of complex terminology. Learn to accept it. And don't give up after the first 100 pages — the best parts often come after the introduction."),
        "_default": ("Your own book mix",
            "You don't have one signature genre. Dostoevsky, Martin, Marquez, King — all on the shelf. Each book for its own mood.\n\n"
            "This works because you have wide taste. Most people fixate on one genre; you understand: great literature is everywhere.\n\n"
            "Other people sometimes are surprised: \"you have War and Peace AND Harry Potter?\". And both. They don't contradict.\n\n"
            "What's worth knowing: wide range is a richness, but sometimes it's worth digging into one author. Reading all of Dostoevsky is a different relationship than \"I read three of his books\". Depth gives what breadth can't."),
    },
    "best_dystopia_novel": {
        "Тоталитарное государство": ("The totalitarian state",
            "1984, Brave New World, Fahrenheit 451, We. The dystopias closer to you are about the state controlling thought and behavior. Big Brother, the Ministry of Truth, numbers instead of names.\n\n"
            "This works because you have sensitivity to freedom. These books aren't fiction — they're warnings, and you hear them.\n\n"
            "Other people sometimes say: \"you're paranoid\". Not paranoid — informed. Different things.\n\n"
            "What's worth knowing: 20th-century totalitarian dystopias often feel \"not about us\". But many of their warnings are now more relevant than they seemed. Learn to see parallels. Not for panic — for understanding."),
        "Контроль через счастье": ("Control through happiness",
            "Brave New World, This Perfect Day, The Machine Stops, Never Let Me Go. The dystopias closer to you aren't about repression but about a too-comfortable system. Where happiness itself is the instrument of enslavement.\n\n"
            "This works because you have a mature view. Many think a bad state is \"cruel\"; you understand the worst is perfect comfort that leaves you no choice.\n\n"
            "Other people sometimes don't get it: \"but in Brave New World everyone is happy\". Everyone. And that's the whole horror.\n\n"
            "What's worth knowing: these dystopias are more relevant than the totalitarian ones. Huxley in 1932 described modern society more accurately than Orwell. Learn to see this — current threats are usually \"comfortable\", not \"jackbooted\"."),
        "Женщины как ресурс": ("Women as resource",
            "The Handmaid's Tale, Parable of the Sower, Never Let Me Go, Lord of the Flies. Gender and social justice in dystopia matter to you. These books are about how society turns people into means.\n\n"
            "This works because you have a critical view of hierarchy. Dystopia for you isn't \"about the state\" but about how any system can dehumanize.\n\n"
            "Other people sometimes accuse: \"you're at it again with feminism\". Not about feminism — about morality.\n\n"
            "What's worth knowing: these dystopias often get adapted to screen. The Handmaid's Tale series is a different work than the book. Learn to tell them apart. And remember: the book author is usually deeper than the showrunner."),
        "Принудительное насилие": ("Forced violence",
            "A Clockwork Orange, The Hunger Games, Lord of the Flies, The Road. What grabs you are dystopias of bodily violence. Not \"thought control\"; real physical cruelty as systemic.\n\n"
            "This works because you have the willingness to look at the truth. Many readers can't take such books; you can.\n\n"
            "Other people sometimes can't take it: \"A Clockwork Orange is just…\". It's literature. Brutal, but necessary.\n\n"
            "What's worth knowing: these books are hard to read in a row. Three \"hard\" dystopias in a month and you carry it emotionally. Learn to alternate."),
        "Постапокалипсис": ("Post-apocalypse",
            "The Road, The Drowned World, Parable of the Sower, The Hunger Games. The dystopias closer to you are after the end. Not \"society that turned bad\"; society already destroyed.\n\n"
            "This works because you have a survival instinct. These books are about what remains when everything's gone, and that's where your interest lies.\n\n"
            "Other people sometimes worry: \"are you preparing for the end of the world?\". Not preparing — studying. Different things.\n\n"
            "What's worth knowing: post-apocalyptic books rarely offer hope. Read only those and you develop a black view of the future. Balance with books about possible better worlds."),
        "Технологическая дистопия": ("Tech dystopia",
            "The Machine Stops, Player Piano, This Perfect Day, Never Let Me Go. The dystopias that grab you are about technology. Not \"the state\"; technological progress as a threat.\n\n"
            "This works because you have a critical view of progress. Most see only benefit in tech; you understand every innovation has a dark side.\n\n"
            "Other people sometimes call you a \"luddite\". Not a luddite. Just understand technology isn't neutral.\n\n"
            "What's worth knowing: tech dystopias often turn out to be predictions. The Machine Stops (1909) is today's society in caricature. Learn to read them as a map of the future, not as fiction."),
        "Олигархия и сила": ("Oligarchy and power",
            "The Iron Heel, The Hunger Games, Parable of the Sower, The Handmaid's Tale. What grabs you are dystopias about the power of a small group over the majority. Not \"one dictator\"; a class system that reproduces itself.\n\n"
            "This works because you have a social instinct. These books are about the persistence of inequality, and that's close to reality.\n\n"
            "Other people sometimes accuse: \"you're a leftist\". Not a leftist — a realist.\n\n"
            "What's worth knowing: books about class struggle often radicalize. Learn to separate the literary from the political. Good dystopia is both warning and art, not propaganda."),
        "Климат и катастрофа": ("Climate and catastrophe",
            "The Drowned World, Parable of the Sower, The Road, The Machine Stops. Ecological dystopia matters to you. Not \"social\"; how nature becomes enemy or victim.\n\n"
            "This works because you have a deep instinct for nature. Most people don't yet believe in the climate crisis; you do.\n\n"
            "Other people sometimes say: \"you're an alarmist\". Alarmist. And literature shows the alarm is justified.\n\n"
            "What's worth knowing: climate dystopias are increasingly relevant. Read them in the context of current events. Each year a new heat record makes Ballard's Drowned World (1962) closer to us."),
        "_default": ("Your own warning mix",
            "You don't have one signature dystopia. Totalitarian, climate, tech — you love them all. All these books are different angles on one theme: what could go wrong.\n\n"
            "This works because you have a wide view. Most people focus on one fear; you keep several in mind.\n\n"
            "Other people sometimes say: \"you're a pessimist\". Not a pessimist — an observer.\n\n"
            "What's worth knowing: dystopia is a powerful genre but not the only view of the future. Read utopias too. Otherwise your worldview becomes one-sided and heavy."),
    },
    "world_cuisine": {
        "Юго-восточный любитель": ("Southeast Asia lover",
            "Spicy and sour are your native tongue. You teach others how to balance the five tastes."),
        "Средиземноморский романтик": ("Mediterranean romantic",
            "You appreciate few ingredients on a plate, each visible. Olive oil to you is a staple, not a seasoning."),
        "Латино-исследователь": ("Latin explorer",
            "Spicy sauces and corn bases. You don't confuse a burrito with a taco."),
        "Спец-вегетарианец": ("Spice-and-veg specialist",
            "You don't need meat for a dish to be the main event. Spices and bread do the work."),
        "Региональный гик": ("Regional geek",
            "You know \"Chinese cuisine\" is 8 schools, and you can explain the difference between Megrelian and Imeretian khachapuri."),
        "_default": ("Cosmopolitan eater",
            "No homeland on your plate — every country gets a fair shot."),
    },
    "comfort_food": {
        "Простое и тёплое": ("Simple and warm",
            "Borscht, plov, pelmeni, potatoes. Your comfort is post-Soviet cuisine. Simple, filling, warm. The kind grandma could make, that warms the soul any time of year.\n\n"
            "This works because you have a deep tie to childhood. These dishes aren't \"food\" — they're memory. The smell and taste send you back to something warm.\n\n"
            "Other people sometimes are surprised: \"you don't love anything more refined?\". I do. But on a bad day I need borscht, not omakase.\n\n"
            "What's worth knowing: nostalgic dishes are often better at grandma's than at restaurants. Learn to cook them at home. Without that skill you're stuck chasing \"the right one\" outside, and never finding it."),
        "Итальянские базы": ("Italian basics",
            "Pasta, pizza, mac & cheese, eggs. Your comfort is simple Italian and Italian-American. A few ingredients, and something always comes out.\n\n"
            "This works because you love the \"timeless\". These dishes don't depend on fashion; they were and will be good.\n\n"
            "Other people sometimes say: \"pasta is just pasta\". Pasta. And the strength is in the simplicity.\n\n"
            "What's worth knowing: the \"simplicity\" of Italian cuisine is an illusion. A good carbonara takes understanding. Learn the basics. Without them, your \"homemade pasta\" is just spaghetti with jarred sauce, and that's different."),
        "Азиатская комфортность": ("Asian comfort",
            "Ramen, sushi, tom yum, fried chicken. Your comfort is Asian food. Not \"trying something new\"; tastes that became home.\n\n"
            "This works because you grew up in the era of globalization. Asian cuisine isn't \"exotic\" to you, it's part of the everyday.\n\n"
            "Other people sometimes ask: \"you don't eat borscht?\". I do. But on a bad day I need tom yum.\n\n"
            "What's worth knowing: real Asian cuisine in Russia is often adapted. If you love it, try going to the country. Real ramen in Japan and \"ramen\" at a Moscow sushi bar are different dishes."),
        "Сладкое и быстрое": ("Sweet and fast",
            "Blini, chocolate, eggs, khachapuri. Your comfort is what cooks in 10 minutes. Not \"an hour at the stove\"; quick joy.\n\n"
            "This works because you're time-limited. Long preparations are for weekends; on weekdays you need fast and tasty.\n\n"
            "Other people sometimes get snobby: \"blini with condensed milk again?\". Again. What's wrong with that?\n\n"
            "What's worth knowing: fast meals often become \"the default\" and that makes them boring. Vary them — even a simple breakfast can be done differently. Otherwise blini stop being a treat in a year."),
        "Уличная еда": ("Street food",
            "Burger, fried chicken, sushi, pizza. You like food you can eat with your hands. Not \"dinner with cutlery\"; fast, juicy, satisfying.\n\n"
            "This works because you have no pretension. You don't care what's \"proper\"; you eat what brings pleasure.\n\n"
            "Other people sometimes say: \"a burger is fast food\". And great fast food. Not every \"expensive restaurant\" is better than a good burger.\n\n"
            "What's worth knowing: street food is a health question. Every day, there will be consequences. Learn to alternate. And remember — the best burgers are usually not at chains, but at niche spots."),
        "Хлеб и сыр": ("Bread and cheese",
            "Khachapuri, pizza, mac & cheese, pasta. Your comfort is bread with melted cheese in any form. It's basic and works in any culture.\n\n"
            "This works because you have a simple relationship with food. You don't need elaborate combinations; you need it filling and warm.\n\n"
            "Other people sometimes say: \"you're monotonous\". Monotonous and content. Different things.\n\n"
            "What's worth knowing: \"bread with cheese\" is also a serious load on the gut. If you eat it every day, problems show up over time. Learn to balance with greens, protein, vegetables."),
        "Тёплый суп": ("Warm soup",
            "Borscht, ramen, tom yum, plov. You need soup. Not \"a main with a side\"; hot broth that warms you from the inside.\n\n"
            "This works because you have a deep relationship with temperature. Cold food feels half-eaten to you; you need heat.\n\n"
            "Other people sometimes are surprised: \"soup in summer too?\". In summer too. Tom yum in summer is the best option.\n\n"
            "What's worth knowing: soup is also an investment of time. Good borscht takes 4 hours. Either invest, or find a place that makes it right. Pre-packaged soups are not the same food."),
        "_default": ("Your own comfort food set",
            "You don't have one signature comfort food. Today borscht, tomorrow ramen, the day after pasta. Depends on the day and your state.\n\n"
            "This works because you have wide taste. Most people cling to one childhood dish; you assembled your set from different cultures.\n\n"
            "Other people sometimes can't predict your preference.\n\n"
            "What's worth knowing: flexibility is wealth, but sometimes you should know what really calms you down. In a crisis you should have \"that one dish\" — otherwise in a bad moment you don't know what to cook."),
    },
    "world_desserts": {
        "Итальянский шик": ("Italian flair",
            "Tiramisu, panna cotta, éclairs, Black Forest cake. You're closer to the Italian and Western European dessert tradition. Complex layered cakes, creams, muscat and coffee.\n\n"
            "This works because you love the classics. A good tiramisu is haute cuisine in dessert.\n\n"
            "Other people sometimes say: \"every café has tiramisu\". Yes. And in most — bad. Good is hard to find.\n\n"
            "What's worth knowing: Italian desserts depend heavily on quality. Bad mascarpone ruins any tiramisu. Learn to tell the difference. And don't be afraid to send back — a dessert without pleasure isn't paid for."),
        "Французская изящность": ("French elegance",
            "Macarons, éclairs, crème brûlée, churros. You need the French pastry tradition. This isn't food; it's a work of art.\n\n"
            "This works because you have aesthetics. A macaron isn't a \"treat\" — it's math and aesthetics in one.\n\n"
            "Other people sometimes get snobby: \"you're a gourmand\". Gourmand. And what's wrong with getting pleasure from something beautiful and tasty?\n\n"
            "What's worth knowing: French pastry is expensive. Good macarons cost. Either invest, or find a real French pâtissier in your city. They exist, you just have to look."),
        "Восточная сладость": ("Eastern sweetness",
            "Baklava, mochi, dondurma, matcha cake. The desserts that grab you are Eastern. Japanese, Middle Eastern, Asian — different aesthetics, a different logic of sweetness.\n\n"
            "This works because you have a taste for the exotic. European desserts you already know; you need something with a different temperament.\n\n"
            "Other people sometimes don't get it: \"how can you eat mochi, it's like rubber\". Not rubber — bouncy. And it's a different sensation than European cakes.\n\n"
            "What's worth knowing: Eastern desserts often need context. Matcha cake without understanding the Japanese tea ceremony is just a strange green pie. Learn the history. It changes how the food tastes."),
        "Российская классика": ("Russian classics",
            "Medovik, Napoleon, éclairs, tiramisu. What grabs you are layered cakes. Not \"light mousses\"; serious multi-layered constructions with cream.\n\n"
            "This works because you love the craft. A good medovik is hours of work, and it shows in every layer.\n\n"
            "Other people sometimes are surprised: \"you prefer old cakes\". Old. And they deserve it.\n\n"
            "What's worth knowing: the best layered cakes are homemade or from specialty bakeries. Chains often simplify the recipe. Learn to tell. And don't be afraid to look for \"grandma's recipe\" — it's usually better than any restaurant's."),
        "Шоколадная мощь": ("Chocolate power",
            "Brownie, Black Forest, churros, éclairs. You need chocolate in its most concentrated form. Not \"a hint of chocolate\"; a piece of dense, dark.\n\n"
            "This works because you have a deep relationship with chocolate. Not a \"tea-time sweet\"; a standalone food.\n\n"
            "Other people sometimes are surprised: \"one brownie is enough?\". Enough. One good brownie is more than several mediocre ones.\n\n"
            "What's worth knowing: chocolate quality is the foundation. Cheap chocolate in a brownie gives a \"chemical\" taste. Invest in good chocolate. And remember — a real good brownie is almost liquid inside. Overdone — it's not it."),
        "Чай и тонкость": ("Tea and subtlety",
            "Matcha, mochi, panna cotta, cheesecake. You need delicate, non-aggressive desserts. Not a \"chocolate bomb\"; subtle work with flavors.\n\n"
            "This works because you have a mature palate. Sweet-on-sweet bores you; you need a note, a nuance, an aftertaste.\n\n"
            "Other people sometimes don't get it: \"where's the kick?\". You don't need a kick. You need a symphony.\n\n"
            "What's worth knowing: subtle desserts require mastery. A good matcha cake is both quality of tea and technique. Learn to find true masters. Most \"Japanese dessert cafés\" make European interpretations, not authentic ones."),
        "Хрусткая радость": ("Crunchy joy",
            "Strudel, churros, brownie, baklava. You need desserts with texture. Crispy crust, dense center, contrast between layers.\n\n"
            "This works because you have tactile sensitivity to food. Not just taste — also how it crunches/melts in your mouth.\n\n"
            "Other people sometimes don't tell them apart: \"it's the same thing\". Not the same. A good strudel has thin, transparent dough; a bad one — thick and greasy.\n\n"
            "What's worth knowing: textural desserts go soft fast. If a strudel sat in the fridge for a day, its texture is gone. Eat fresh. And remember — the best of this type are made to order, not in mass production."),
        "_default": ("Your own dessert set",
            "You don't have one signature dessert. Different moments — different. Tiramisu for one, baklava for another, medovik for a third.\n\n"
            "This works because you have wide taste. Most people cling to one \"favorite\"; you understand different moods need different desserts.\n\n"
            "Other people sometimes are surprised: \"you love everything?\". Not everything. Just know how to tell good from bad, and don't fixate on one genre.\n\n"
            "What's worth knowing: variety is wealth, but sometimes it's worth picking \"your signature\". When you have one dessert you make well at home — that's a gift to those around you. Learn to choose, not just collect."),
    },
    "friend_role": {
        "Капитан вечера": ("Captain of the evening",
            "There are no parties without you. Not because you say so — without you, no one really gathers. You're the one who texts \"shall we?\", suggests the place, coordinates the time, drags the rest along.\n\n"
            "This is invisible work. Most people think \"evenings happen\". You know evenings get organized, and usually by you. Without a captain, the ship stays at the dock.\n\n"
            "People love you for it but sometimes take it for granted. They got used to you taking initiative — and over time stop suggesting things themselves. You become the only engine of the group.\n\n"
            "What's worth knowing: don't burn out. Sometimes step back deliberately and see who picks up the role. If no one — start delegating consciously."),
        "Душа без слов": ("The wordless soul",
            "You don't talk much, but without you something is missing. You sit, listen, sometimes smile — and everyone feels warmer. Your presence is your contribution.\n\n"
            "It's a rare role. Most people think you have to constantly \"contribute\" to conversation — talk, joke, initiate. You know sometimes the most valuable thing is just being there and being yourself. It doesn't work for everyone, but for those it works for, you're irreplaceable.\n\n"
            "Others may not get your role at first. If they're used to loud groups, you can seem \"unnoticed\". But those who read subtly see you immediately.\n\n"
            "What's worth knowing: protect this skill. The pressure to \"speak more\" can break it. You don't owe a group your noise — your presence is enough."),
        "Голос правды": ("Voice of truth",
            "People come to you with problems. Not because you're \"a therapist\" — because you can listen without judgment and tell the truth without cruelty. It's a rare mix, and people instinctively feel it.\n\n"
            "You understand: advice isn't \"tell them what to do\". Advice is \"help the person see their situation differently\". So you ask questions instead of giving answers. That works ten times better than wise advice.\n\n"
            "People see you as one of the most reliable in their lives. That's weight. They share things with you they share with no one else. You hold a lot of other people's secrets.\n\n"
            "What's worth knowing: it's heavy. Make sure you have your own person to talk to. Otherwise you become a sponge for others' pain with no one to wring it out to."),
        "Острый язык": ("Sharp tongue",
            "You love throwing in a topic that makes everyone explode. Not from anger but from curiosity: it's interesting to see how everyone reacts. You know conflict sometimes enlivens an evening more than smooth conversation.\n\n"
            "It takes finesse. The line between \"a provocateur who's fun\" and \"a provocateur who's tiring\" is thin. You usually feel that line, but sometimes step over it — and the evening becomes yours alone.\n\n"
            "People either adore you or periodically tire of you. Those who love — for the spark. Those who tire — because sometimes they want to spend an evening without intellectual landmines.\n\n"
            "What's worth knowing: pay attention to fatigue cues. Even great provocation needs to know when to stop. The best version of you is the one who reads the room."),
        "Мама группы": ("Group mom/dad",
            "You watch to make sure everyone's okay. Noticed someone got sad — went over. Noticed they forgot to tell you something important — asked. Without you the group would be colder, and everyone knows it, even if they don't say so.\n\n"
            "It's a form of love that's hard to explain. You don't invest \"because you should\" — you just see when investment is needed and can't help doing it. It's automatic.\n\n"
            "People love you for the warmth but sometimes forget you're a person with your own problems. They got used to your caring role and sometimes don't think to ask \"and how are you?\". Not from indifference — the role is too steady.\n\n"
            "What's worth knowing: ask for care explicitly. People aren't psychic. If you say \"I'm having a hard time\" — they'll show up. They just don't notice on their own."),
        "Хроника вечера": ("Chronicler",
            "You're the group's photographer. In your phone is the whole history of your meetings over recent years. Without you many moments would be forgotten — but they're alive, in photos, videos, memes in the shared chat.\n\n"
            "This isn't a \"hobby for photography\". It's understanding: life forgets faster than it seems, and the one who records makes a huge gift to everyone. Five years from now you'll come back to these photos and realize: those were the best times. And you'll be thanked.\n\n"
            "People sometimes don't appreciate your work in the moment. \"Filming again\" is the usual reaction. But years later, those same people will post your photos on birthdays.\n\n"
            "What's worth knowing: protect the archive. A phone can break. Make backups. Otherwise, the whole memory of the group is in a fragile device."),
        "Загадочный гость": ("Mysterious guest",
            "You appear in groups irregularly — always with them for a while, then disappear for a month or two, then come back like nothing happened. It's not disrespect or ghosting — it's your rhythm. You periodically need solitude, and you take it.\n\n"
            "Most people can't do this — they're either \"always in the group\" or \"gone forever\". You found a third way: show up when you have the resource, be absent when you don't. That's rare maturity.\n\n"
            "People sometimes don't get it. \"Where were you?\" is the usual question on return. You don't always know how to explain that you just \"needed to be alone\". They hear it as offense.\n\n"
            "What's worth knowing: explain your rhythm to the close ones. Once. Then they won't take your absence personally — they'll know it's how you work."),
        "_default": ("Universal player",
            "You're not tied to one role in the group. With one group you're the organizer, with another the listener, with a third the provocateur. Each circle sees one of your facets, no one sees the full spectrum.\n\n"
            "This isn't insincerity. It's understanding that different groups open different parts of you. With loud companies you're lively, with quiet ones — thoughtful. You're the sum of all your contexts, and no single group will reveal it.\n\n"
            "People sometimes are surprised hearing about you from others. \"You're loud at Masha's? I thought you were quiet\". And both — true.\n\n"
            "What's worth knowing: universality is your strength, but also a risk. If you constantly adapt, you can lose the central thread. Keep at least one space where you're fully yourself, without adjusting."),
    },
    "chat_style": {
        "Голос важнее текста": ("Voice over text",
            "You record voice notes. Not from laziness, but from understanding: text won't carry your tone. What you'd say in a minute turns into five minutes of typing and ten minutes of decoding. Voice is more logical.\n\n"
            "It works in close chats where they hear your rhythm and know you. Words without tone often read wrong — voice gives the full palette: from irony to tenderness.\n\n"
            "People split into two camps. One adores it: with your voice notes you're really there. Others rage: \"can't listen at work, type it out!\". You understand them but sometimes forget.\n\n"
            "What's worth knowing: voice notes — wonderful, but only with consent. If a person prefers text, switch. Otherwise even the close ones will start avoiding your messages."),
        "Краткий и сухой": ("Short and dry",
            "\"OK\". \"Got it\". \"Fine\". This is your style. Not from disrespect — from efficiency. Why three sentences when you can say it in one? You don't like fluff and don't see the need to add it.\n\n"
            "It works in business chats. There brevity is politeness, and you're respected for it. Most people pour water out of anxiety \"not to seem rude\" and end up clogging the feed. You're different.\n\n"
            "People sometimes get hurt: \"you reply so dryly, are you mad?\". Not mad. You talk that way to everyone. It's your native register, not a marker of attitude.\n\n"
            "What's worth knowing: dryness works with people who know you. With strangers, add one warm word. Otherwise you build a wall before they even get close."),
        "Мемно-эмодзи": ("Meme and emoji",
            "Why write \"sad\" when there's a sad meme? Why \"thanks\" when there's a curtsy sticker? You live in a world where emoji and memes are a full language, and you've mastered it better than letters.\n\n"
            "This works because emoji carry tone in one symbol. With text you have to write \"need to think\"; a sticker says it once and everyone gets it. More efficient.\n\n"
            "People sometimes don't share it. Older relatives: \"what kind of pictures are these?\". They didn't grow up in this language, and for them emoji are decoration, not the meaning. You translate by context.\n\n"
            "What's worth knowing: meme-language works in compatible groups. If the other person doesn't reply with emoji — switch. Forcing them to \"learn your dialect\" is rude. Match the register."),
        "Призрак переписки": ("Chat ghost",
            "Read it, decided \"I'll reply later\", and disappeared. For a day, a week, sometimes a month. Not from malice — the reply needed thought, and you didn't have the energy. So you sit with the unread like a weight.\n\n"
            "This is the curse of modern chat. No one can answer everything immediately, because every message needs context. So it piles up. And the more it piles up, the scarier it is to open — because now sending a reply without an explanation is awkward.\n\n"
            "People sometimes get hurt. They don't know you're not ignoring them — you're stuck. To them it feels deliberate. To you it's just that the right moment never came.\n\n"
            "What's worth knowing: send a one-line \"sorry, will reply properly later\" right away. That changes everything. Silence reads as disrespect; a brief acknowledgement reads as humanity."),
        "Профессиональный регистр": ("Professional register",
            "You write only during work hours and only on business. No \"hi, how are you?\" at midnight. You have a clear line: work chats live in work hours, and you defend that.\n\n"
            "This works because you understood: blurred boundaries are the main energy killer. If work can come to you at 11 PM, you never fully rest. So you turn off notifications and don't apologize.\n\n"
            "People sometimes complain: \"answer me, I called you\". They're not used to anyone having work hours. Over time they get used to it and start respecting it.\n\n"
            "What's worth knowing: clear boundaries are great, but sometimes they read as cold. In emergencies (real ones — not \"super urgent\" by their standards) be available. Otherwise the line becomes a wall."),
        "Долгий писатель": ("Long-form writer",
            "You write \"walls\". Not because you love a lot of text, but because you have six thoughts at once in your head and you want to deliver them precisely. To shorten is to lose nuance. You won't lose nuance.\n\n"
            "This works with people willing to read. They get your full picture in one go. No need to ask back, clarify, fill in.\n\n"
            "People sometimes complain: \"another wall, I just asked how you were\". You smile. They wanted \"normally\", to you it seemed — if asked, they wanted to know. Different things.\n\n"
            "What's worth knowing: your style works in close relationships where they have time. With everyone else, learn to summarize. \"Long version on request\" — and they ask if needed."),
        "Реакция-лайк": ("Reaction-like",
            "You often reply not with words but with a reaction: thumbs-up, heart, fire. Got a message — put an emoji. That's the answer. Not from laziness — from understanding: sometimes words aren't needed, just confirmation \"saw and got it\".\n\n"
            "This works in group chats with lots of noise. If everyone wrote \"oh, cool!\", the feed becomes mush. A reaction is compact, clean, and clearly carries \"I heard you\".\n\n"
            "People sometimes don't get it: \"that's it, just a heart?\". They want words. You translate to their register in important moments; in ordinary ones — keep your economy.\n\n"
            "What's worth knowing: reactions are great for short, but for serious topics — write words. People on the receiving end of grief or news need to feel addressed personally, not just acknowledged."),
        "_default": ("Your own variable style",
            "You don't have one signature messaging style. You write differently with different people: voice notes with one, dry with another, long walls with a third. This isn't two-faced — it's adaptation.\n\n"
            "Most people write the same way to everyone. Convenient but doesn't work — different people understand different registers. You chose variability.\n\n"
            "People sometimes are surprised hearing about you from other chats: \"with me you always do short replies, with him you send 15-minute voice notes!\". Both true.\n\n"
            "What's worth knowing: flexibility works while it stays conscious. If you adjust the register to please, you lose yourself. Adjusting to communicate better is fine. Adjusting to disappear is not."),
    },
    "conflict_persona": {
        "Молчун, который помнит": ("The silent rememberer",
            "In conflict you go silent, but you don't surrender. You don't argue out loud — you just remember. And in an hour, a day, a year, it'll surface. Not from revenge; just because grievances don't dissolve in you, they get archived.\n\n"
            "This works because you don't like hot scenes. They feel empty and unproductive. Better to calmly gather facts and then, when emotions settle, lay them out in one precise letter.\n\n"
            "People sometimes read your silence as \"all is well\". They walk away thinking \"it blew over\". A month later they get a precise breakdown of how they were wrong — and they're shocked.\n\n"
            "What's worth knowing: archived grievances build pressure. If you only release them after a year, the explosion is destructive. Learn to bring up smaller things sooner. The big precision letter should be the exception, not the norm."),
        "Уходящий": ("The leaver",
            "When conflict heats up, you leave. Physically or emotionally. It's not cowardice — it's self-defense. You understand at a hot moment you'll bring nothing useful, better to step out, cool down, return (or not).\n\n"
            "This works in short fights: after a pause you'll come back to the conversation more grown-up. But in long conflicts your departure is sometimes read as \"he's giving up\" — and the partner feels their pain doesn't matter.\n\n"
            "People sometimes get angry at you for it. \"You ran away again!\". They don't get that you didn't run — you stepped out of a zone where you couldn't help. They don't care.\n\n"
            "What's worth knowing: explain the rhythm. \"I'm leaving because I'll do harm here, not because I don't care. I'll come back\". With that frame, departures stop being abandonments."),
        "Миротворец": ("Peacemaker",
            "You hate conflicts and smooth them at any cost. Humor, diplomacy, compromise — all in your arsenal. The main thing is everyone leaves happy, even if it meant ignoring your own position.\n\n"
            "This works because you understand: most conflicts are about emotions, not facts. And if you defuse the emotions, the facts often turn out less important than they seemed. So your first move is lowering the temperature.\n\n"
            "People love you for it. Companies don't fall apart from petty fights around you. You're the glue, and many groups wouldn't survive without you.\n\n"
            "What's worth knowing: peacemaking has a cost. If you always smooth, your own position gets erased. Learn to draw a line: \"I'll smooth most things, but here I have a stake\". Otherwise you become invisible to the people you're saving."),
        "Прямой удар": ("Direct hit",
            "You say it as it is. Head-on, no filter, sometimes harshly. Not from anger — from conviction that directness is respect. If a person gets the truth, they're respected as an adult. If it's wrapped in cotton, they're treated like a child.\n\n"
            "This works because facts usually stand behind your words. You don't \"shout emotions\", you state. So your arguments — even harsh ones — usually hold up over time.\n\n"
            "People either adore you or fear you. Those who adore — because you don't have to guess. Those who fear — because you can't relax around you, anything can land at any moment.\n\n"
            "What's worth knowing: directness is great, but tone matters. The same truth said gently lands; said harshly, it bounces. Learn the gentle version. The truth doesn't get weaker if you wrap it kindly."),
        "Стратег ожидания": ("Waiting strategist",
            "In conflict you don't react immediately. You listen, observe, wait. When the other has let off steam and exposed their position, you step in — precisely and with evidence. This isn't passivity, it's positional play.\n\n"
            "You understood that in the hot moment arguments don't work — only volume does. So you don't dive into the noise; you wait for it to die down, then say your line — calmly, and it carries weight.\n\n"
            "People sometimes get hurt: \"say something!\". And you're silent because the moment isn't right. And often your silent presence speaks louder than anyone's shouting.\n\n"
            "What's worth knowing: strategists are sometimes seen as cold. Make sure your patience reads as care, not detachment. A warm look, a hand — they tell the other you're with them, even if you're not arguing back yet."),
        "Адвокат другой стороны": ("Devil's advocate",
            "A strange quality of yours: even when you should be on \"your\" side, you suddenly see the opponent's logic. And — sometimes — you defend it. Not from contrariness; you honestly see the other has an argument.\n\n"
            "This works because you have the rare ability to look at a situation from all participants' eyes at once. Most people get stuck in one perspective. You don't. And that's a huge edge in any negotiation.\n\n"
            "People sometimes get hurt: \"so you're not on my side?\". You're for the truth, not for sides. And sometimes that's very lonely — both sides see you as a traitor.\n\n"
            "What's worth knowing: in close relationships, this can really wound. Sometimes a partner needs you on their side first, advice second. Learn to read which is needed. The truth-seeker and the supporter aren't always the same role."),
        "Жертва обстоятельств": ("Victim of circumstance",
            "In conflict you often feel like the one always at the receiving end. Not as a role, but as an experience: \"I'm in this situation again\", \"why does this happen to me\". And you freeze, don't act, wait for it to pass on its own.\n\n"
            "The roots are usually in childhood, where you couldn't influence the situation, and the only strategy was to become invisible and wait it out. That worked then. Now it works poorly, but the habit remains.\n\n"
            "People sometimes don't notice you're suffering. You don't show, don't protest, don't demand — so they walk on, not knowing they hurt you. Over time resentment builds: they stop seeing you altogether.\n\n"
            "What's worth knowing: the freeze reaction is unlearnable. Therapy helps — not because something is \"broken\" but because the old strategy needs an update. Until you upgrade it, the same situations will keep finding you."),
        "_default": ("No template",
            "You don't have one signature conflict style. Sometimes silent, sometimes attacking, sometimes leaving, sometimes peacemaking. This isn't disarray — it's adaptation to the situation.\n\n"
            "Most people in conflict run the same reaction automatically: always fight, or always silence, or always smooth. You pick a strategy by the task. That's rare maturity.\n\n"
            "People can't predict you. With one conflict you're quiet, with another loud. With one direct, with another diplomatic. That throws them off, and sometimes blocks them from understanding what you want.\n\n"
            "What's worth knowing: flexibility works while you choose consciously. If the choice is reactive — \"adjusting because afraid\" — that's a different reaction wearing flexibility's clothes. Learn to tell the difference."),
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
    bak = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.arch2.{stamp}")
    shutil.copy2(CATEGORIES_JSON, bak); print(f"Backup: {bak.name}")
    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON); print(f"Wrote: {CATEGORIES_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
