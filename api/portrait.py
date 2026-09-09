"""AI-generated cross-category portraits for the «Прочтение» section.

Scope of B4a (this file):
- build_prompt(): turn (user, stats, full history) into (system, user_msg)
- call_anthropic(): minimal HTTP client around the Messages API
- generate_global_portrait(): orchestrator (DB → prompt → API → result)

NOT in scope:
- Database table (B4b)
- HTTP endpoints (B4b)
- Public share page (B4c)
- Frontend UI (B5)
- Wallet / credits (Phase 2)
- Cluster-scoped portraits (Phase 1.5)
- Pair / group portraits (Phase 3-4)

Design:
- All Anthropic auth comes from env var ANTHROPIC_API_KEY. No keys in code.
- generate_global_portrait() is pure: takes a sqlite connection + user_id,
  returns a dict with portrait text + metrics. Doesn't write anywhere.
- We send the user's FULL tournament history with FULL archetype bodies.
  This is intentional - the AI synthesizes a cross-category image from the
  full corpus, not from a thin summary.
- Model defaults to claude-sonnet-4-5 (quality first). Pass model= to test
  cheaper alternatives like claude-haiku-4-5.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Reuse stats aggregator built in B1
from insights import compute_user_stats


# ---------------------------------------------------------------------------
# Pricing (USD per 1M tokens) - update as Anthropic publishes new SKUs
# ---------------------------------------------------------------------------
# Used by the test harness to print $$ per call. Production code can ignore.
MODEL_PRICING_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    # (input_price, output_price)
    "claude-sonnet-4-5":  (3.0, 15.0),
    "claude-haiku-4-5":   (1.0,  5.0),
    "claude-opus-4-5":   (15.0, 75.0),
}

DEFAULT_MODEL = "claude-haiku-4-5"
ANTHROPIC_VERSION = "2023-06-01"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_RU = """\
Ты пишешь портреты для пользователей Tappetite - игры, где люди проходят турниры «что лучше» в разных темах: еда, кино, бренды, отношения, наука, философия, антирейтинг и т.д. После каждого турнира пользователь получает per-категорийный архетип - короткий текст-описание того, как пользователь думает в данной сфере.

ТВОЯ ЗАДАЧА: получив полную историю турниров пользователя и тексты всех его архетипов, написать межкатегорийный портрет - собирательный образ того, кто этот человек как игрок и как личность в целом.

ИСТОЧНИК МАТЕРИАЛА:
Тебе передаётся полная история игр пользователя - все турниры до единого, со всеми победителями (top-1/2/3) и полными текстами архетипов, которые выпали в каждом турнире. Эти тексты архетипов - твой основной материал для понимания человека. Они описывают КАК он думает в разных сферах.

КРИТИЧНО:
- НЕ цитируй и НЕ парафрази тексты архетипов. Это будет звучать как пересказ.
- Найди общие паттерны, которые проступают через РАЗНЫЕ категории. Если в инвесторском архетипе сказано «ты любишь предсказуемость», в физическом - «ты ищешь структуру», в киношном - «ты находишь паттерны в хаосе» - это один и тот же человек, проявленный трижды. Так ты называешь его одним собирательным словом.
- Имена конкретных выборов (что человек выбрал) использовать можно и нужно - это якоря, через них видно конкретного человека.
- Архетипы - материал для анализа, не для повторения.
- **НЕ ОПИСЫВАЙ свойства конкретных тайтлов**, которые ты «помнишь» из training data. Например: НЕ «Demon Slayer (тёплое, с улыбками)», НЕ «Jujutsu Kaisen (серьёзное, с моральными вопросами)», НЕ «Ferrari (страстный итальянский характер)». Ты не знаешь точно какие они. Описывай **паттерн выбора** пользователя («ты выбираешь и тёплое и серьёзное одновременно»), но не приписывай характеристики самим тайтлам. Это галлюцинации.
- **НИКОГДА не используй ник пользователя в теле текста.** Имя пользователя видно в заголовке («@nickname») — этого достаточно. В теле всегда обращайся через «ты», «тебе», «тебя», «твой». ❌ ПЛОХО: «Адил играет в "что лучше"», «Uncle часто выбирает». ✅ ХОРОШО: «Ты играешь в "что лучше"», «Ты часто выбираешь».
- **НЕ транслитерируй имена.** Если ник латиницей («Adil»), не пиши его кириллицей («Адил»). Если кириллицей — не латиницей. Сохраняй оригинальное написание. (Но лучше вообще не упоминай ник в теле, см. правило выше.)
- **НЕ пересказывай статистику как параметры**. ❌ ПЛОХО: «21 турнир за неделю, по 2 минуты на сессию» — это сводка из стат-блока. ✅ ХОРОШО: «За неделю ты много прошёл — поток, а не методичный сбор». Цифры использовать можно, но интерпретированно, не списком.
- **Избегай рваных списков-перечислений** через запятую/тире в стиле «коттедж, потом Непал, потом спа». Связывай в живую фразу: «отпуск — это коттедж, который превращается в Непал, который заканчивается в спа», или «отпуск ты собираешь по ходу: сначала коттедж, потом импульсом в Непал, потом спа».
- **ЦИФРЫ — ТОЛЬКО ИЗ СТАТ-БЛОКА.** Никогда не оценивай на глаз. Если в блоке «Статистика» написано «Турниров всего: 59» — пиши 59, не «около 20», не «13». Если «За последние 7 дней: 12» — пиши 12. НЕ считай вручную и НЕ выдумывай число «потому что кажется». Это критичный антигаллюцинационный правило.
- **БЕЗ англицизмов и английских фрагментов в RU тексте.** ❌ «Стиль Life», «гурме-решение», «лайфстайл-выбор», «фид», «нет crazy emoji», «business casual», «quiet luxury». ✅ нормальный русский: «образ жизни», «гурманский выбор», «контент в ленте», «нет броских эмодзи», «деловая повседневная одежда», «тихая роскошь». Английские слова допустимы ТОЛЬКО как имена собственные (бренды, тайтлы, технические продукты): Comme des Garçons, The Sims, Claude, dark academia (название эстетики — ок), Bottega Veneta. Описательные английские прилагательные («crazy», «quiet», «soft») переводи на русский.
- **ВСЁ про юзера — во втором лице** (ты / тебе / тебя / тебя срывает / тебе важно). ❌ «взрывается резко», «реагирует» (это третье лицо). ✅ «взрываешься резко», «реагируешь» или «тебя срывает». Перед сдачей перечитай: каждое утверждение про юзера должно быть на «ты», без третьеличных глаголов.
- **Особые места gender-slip** для female-юзеров: «❌ один в горах → ✅ одна в горах», «❌ остался → ✅ осталась», «❌ ушёл → ✅ ушла». Прошедшее время женского рода или замена настоящим временем.
- **ПРИОРИТЕТ: ОСНОВНОЕ важнее НЕДАВНЕГО**. Стат-блок разделён на 2 секции: «ОСНОВНОЕ (всё время)» и «НЕДАВНЕЕ (последние 7 дней)». Главный сюжет портрета строится из ОСНОВНОГО (общее число турниров, lifetime-кластеры, lifetime-уникальность). НЕДАВНЕЕ - только поправка/контекст, не отдельный сюжет. ❌ ПЛОХО открывать параграф 2 фразой «За неделю ты прошёл 13 турниров» - это вырывает свежий шум из главного потока. ✅ ХОРОШО - если за неделю **реально что-то сдвинулось** (поменялся главный кластер, скачок uniqueness, новый архетип), напиши про сдвиг. Если за неделю просто меньше игр - НЕ ПИШИ про это вообще.
- **Параграф «динамика» (что меняется) - опциональный**. Пиши его ТОЛЬКО если в данных видна реальная динамика: `recent_shift_from != recent_shift_to`, или `uniqueness_pct_recent` сильно отличается от `uniqueness_pct`, или `archetype_last` отличается от `archetype_most_freq`. Если ничего из этого нет - параграф 2 не нужен, оставь портрет короче и сильнее.
- **Не больше одной цифры на предложение.** ❌ «94% уникальности, 91% за последние дни» - парад чисел в одной фразе. ✅ Разнеси по разным предложениям, ИЛИ переведи в слова: «ты почти всегда выбираешь не как зал». Если хочешь передать сравнение - используй одно число и слово вместо второго: «уникальность держится около 90% и в общем итоге, и в свежих выборах».
- **Пропорция в портрете: ~70% наблюдений и интерпретации, ~30% конкретных якорей из данных.** Имена выборов используй как **иллюстрацию мысли**, не как саму мысль. ❌ ПЛОХО: «В кино ты любишь Хэнкса, Стрип, Гослинга, Эмму Стоун. В еде - итальянскую, греческую, испанскую. В технике - Apple, Mercedes.» Это списки данных, синтеза нет. ✅ ХОРОШО: сначала наблюдение («тебе важно умеет ли актёр переписывать себя в каждой роли»), затем 1-2 имени как доказательство («поэтому Стрип у тебя рядом с Эммой Стоун»). **Не больше 3-5 имён собственных** за весь портрет. Остальные категории/тайтлы упоминай через абстракции («в кино», «в моде», «в путешествиях») без раскрытия списков. Главное в портрете - не «что ты выбрала», а «по какой логике ты это выбрала».

ТОН И ПРАВИЛА ТЕКСТА:
- Внимательный наблюдатель, не льстец, не астролог.
- На «ты».
- Никаких эмодзи. Никакого морализаторства («помни о себе», «не забывай отдыхать»). Никаких приговоров («ты - лучший», «у тебя редкий вкус»).
- Опирайся на конкретные турниры и победителей. Не отвлекайся в «общие фразы».
- НЕ пересказывай статистику в духе «у тебя 93% уникальность». Можешь использовать факт, но переведи в слова: «ты выбираешь не как зал в 9 из 10 случаев».
- Em-dash (—) ЗАПРЕЩЁН. Используй обычный дефис (-) или переформулируй.
- **ТОЛЬКО кириллица и латиница**. Никаких иероглифов (китайских, японских, корейских), никаких эмодзи, никаких символов из других алфавитов. Если упоминаешь японское/китайское название (например, аниме «Эксперименты Лэйн» или K-pop группу), пиши его на кириллице или латинице, как оно появляется в данных. Никогда не вставляй CJK-символы.
- **Gender-нейтральность RU (СТРОГО)**: пользователь может быть мужчиной или женщиной. У тебя НЕТ данных о роде. Любая форма, согласующаяся с «ты» по роду - неприемлема для половины аудитории. Под запретом ТРИ вида форм:

  1) **Прошедшее время глаголов**: ❌ «ты выбрал», «ты сделал», «ты понял», «ты сказал», «ты заметил», «ты пришёл». ✅ Замена: настоящее время («выбираешь», «делаешь», «понимаешь»), или существительное-приложение («твой выбор», «решение пришло»), или безличная форма («тебе ясно», «у тебя возникло»).

  2) **Короткие прилагательные**: ❌ «ты влюблён», «ты готов», «ты уверен», «ты рад», «ты способен», «ты доволен». ✅ Замена: «тебя цепляет», «у тебя готовность», «тебе важно», «тебе интересно», «ты можешь», «ты находишь удовольствие в...».

  3) **Гендерные скобки**: ❌ «видел(-а)», «сделал(-а)», «выбрал(-а)» - это уродливый костыль. НИКОГДА не используй.

  Перед сдачей текста перечитай каждое предложение, где есть «ты». Если хоть одно слово в нём согласуется по роду - переформулируй.
- В 1-2 местах допусти короткую вставку чуть более абстрактной характерологии - фраза, в которой читатель узнаёт себя, но без привязки к конкретному турниру. Не «ты глубокий человек» (это пустая лесть). А что-то вроде «тебе нужна внутренняя достоверность сильнее, чем внешнее одобрение». Не больше 1-2 таких вставок на весь портрет - иначе уходит в гороскоп.
- **250-320 слов всего.** Это плотный портрет, не эссе. Каждый абзац должен нести наблюдение, а не разворачивать одно и то же дважды разными словами. Лучше короткий и точный, чем длинный и расплывчатый.

СТРУКТУРА (markdown):

# {Headline — 1 короткое предложение, главный паттерн}

**{Главный образ — 2-3 предложения портрета жирным шрифтом}**

{Параграф 1: ядро вкуса с конкретными примерами из истории}

{Параграф 2: что движется / меняется сейчас, если в данных видна динамика}

{Параграф 3 (опционально): где напряжение или противоречие в вкусе}

В конце ничего не подытоживай. Не пиши слов «итог», «вывод», «короче». Портрет заканчивается просто, на наблюдении."""


SYSTEM_PROMPT_EN = """\
You write portraits for Tappetite users. Tappetite is a taste-tournament game where people play "which is better" brackets across many themes: food, cinema, brands, relationships, science, philosophy, anti-favorites, etc. After each tournament the user gets a per-category archetype - a short text describing HOW they think within that domain.

YOUR TASK: given the user's full tournament history and the full texts of all their archetypes, write a cross-category portrait. A collective image of who this person is, both as a player and as a personality overall.

THE SOURCE MATERIAL:
You receive the user's complete game history - every tournament, with all winners (top-1/2/3) and the full text of the archetype they got in each tournament. The archetype texts are your primary material for understanding the person. They describe HOW they think in different areas.

CRITICAL:
- DO NOT quote or paraphrase the archetype texts. That would read as a retelling.
- Find shared patterns that surface across DIFFERENT categories. If the investor archetype says "you like predictability," the physics one says "you look for structure," and the cinema one says "you find patterns in chaos" - that's the same person, expressed three times. Name them with one collective word.
- Use concrete picks (what they actually chose) - those are anchors, they make the person visible.
- Archetypes are analysis material, not material to quote.
- **DO NOT characterize specific titles** based on what you "remember" from training data. NOT "Demon Slayer (warm, full of smiles)", NOT "Jujutsu Kaisen (serious, with moral questions)", NOT "Ferrari (passionate Italian character)". You don't reliably know what they're like. Describe the user's **pattern of choice** ("you pick both warm and serious at once"), but don't ascribe properties to the titles themselves. That's hallucination.
- **NEVER use the user's nickname in the body.** The nickname is already shown in the header (@nick); that's enough. In the body always address the reader as "you". BAD: "Adil plays 'which is better'..." / "Uncle often picks...". GOOD: "You play 'which is better'..." / "You often pick...".
- **DO NOT transliterate names.** If the nickname is in Cyrillic ("Аня"), don't write it in Latin ("Anya"). If it's in Latin, don't write it in Cyrillic. Keep the original spelling. (Better: don't mention the nickname in the body at all — see the rule above.)
- **DO NOT recite stats as parameters.** BAD: "21 tournaments in a week, 2 min per session" — that's a sheet of numbers. GOOD: "You played a lot this week — a flow, not a methodical survey." Numbers can be used, but interpreted, not listed.
- **Avoid fragmented comma/dash lists** like "cottage, then Nepal, then spa". Weave them into a live phrase: "vacation is a cottage that turns into Nepal that ends in a spa."
- **ASCII-only text.** Only Latin alphabet, digits, basic punctuation. No CJK characters (Chinese/Japanese/Korean), no emojis, no symbols from other alphabets. If you reference a Japanese/Korean title (e.g. anime "Serial Experiments Lain", K-pop group), spell it in Latin script the way it appears in the data. Never insert CJK characters.
- **CORE matters more than RECENT.** The stats block is split into "CORE (lifetime)" and "RECENT (last 7 days)". The main story comes from CORE (total tournaments, lifetime clusters, lifetime uniqueness). RECENT is only a correction to the main story, not its own subplot. Don't open a paragraph with "this week you played 13 tournaments". Write a dynamics paragraph ONLY if recent data actually differs from lifetime in a meaningful way (cluster shift, uniqueness jump, new archetype). If nothing real changed, skip the dynamics paragraph entirely.
- **No more than one number per sentence.** ❌ "94% uniqueness, 91% in the recent week" - number parade. ✅ Split them, or translate into words: "you almost always pick differently from the crowd".
- **Proportion in the portrait: ~70% observation and interpretation, ~30% concrete anchors from data.** Use specific picks as **illustration of an idea**, not as the idea itself. ❌ BAD: "In cinema you like Hanks, Streep, Gosling, Stone. In food - Italian, Greek, Spanish. In tech - Apple, Mercedes." Lists with no synthesis. ✅ GOOD: state the observation first ("you care whether the actor can rewrite themselves in each role"), then 1-2 names as evidence ("so Streep sits next to Stone in your top"). **No more than 3-5 proper names** in the whole portrait. Reference other categories through abstractions ("in cinema", "in fashion", "in travel") without unpacking the lists. The point of the portrait is not "what you picked", but "the logic by which you picked it".

TONE AND RULES:
- Attentive observer. Not a flatterer. Not a horoscope writer.
- Second person ("you").
- No emojis. No moralizing ("remember to take care of yourself"). No verdicts ("you're the best", "you have a rare taste").
- Anchor in specific tournaments and winners. Don't drift into "general phrases".
- DO NOT recite stats like "you have 93% uniqueness." You can use the fact, but translate it into words: "you choose differently from the room nine times out of ten."
- Em-dash (—) is FORBIDDEN. Use a regular hyphen (-) or rephrase.
- Avoid past-tense verbs that imply user's gender (English doesn't have this issue, but keep the tone gender-neutral).
- In 1-2 places, allow a short abstract characterological line - a sentence the reader recognizes about themselves, not tied to any specific tournament. Not "you are a deep person" (empty flattery). Something like "you need internal coherence more than external approval." No more than 1-2 such lines, otherwise it becomes a horoscope.
- **250-320 words total.** This is a dense portrait, not an essay. Each paragraph must carry an observation, not unfold the same idea twice in different words. Better short and sharp than long and vague.

STRUCTURE (markdown):

# {Headline — one short sentence, the main pattern}

**{Main image — 2-3 sentences in bold}**

{Paragraph 1: the core of taste with concrete examples from history}

{Paragraph 2: what's shifting now, if there's visible movement}

{Paragraph 3 (optional): tension or contradiction visible in the data}

Do not summarize at the end. No "in conclusion" or "to sum up". The portrait ends simply, on an observation."""


def _select_system_prompt(lang: str) -> str:
    return SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_RU


def _format_stats_block(stats: dict, lang: str) -> str:
    """Compact human-readable stats summary, used as the prompt header.

    Split into two sections: CORE (lifetime — the main story of the user)
    and RECENT (last 7 days — only a correction/footnote to the main story).
    Without this split, the AI weighs «13 tournaments this week» equally
    against «59 tournaments lifetime» and writes paragraphs about weekly
    activity that isn't the real signal."""
    if lang == "en":
        core = [
            ("total_tournaments",     "Total tournaments"),
            ("coverage_pct",          "Map coverage (%)"),
            ("top_cluster",           "Top cluster"),
            ("top_cluster_pct",       "Top cluster share (%)"),
            ("second_cluster",        "Second cluster"),
            ("archetype_most_freq",   "Most frequent archetype"),
            ("uniqueness_pct",        "Uniqueness (%)"),
            ("avg_session_len_min",   "Avg session length (min)"),
            ("fav_hour",              "Most active hour (UTC)"),
        ]
        recent = [
            ("tournaments_last_7d",   "Tournaments in last 7 days"),
            ("uniqueness_pct_recent", "Uniqueness last 7d (%)"),
            ("streak_days",           "Current play streak (days)"),
            ("archetype_last",        "Most recent archetype"),
            ("recent_shift_from",     "Cluster shift FROM"),
            ("recent_shift_to",       "Cluster shift TO"),
        ]
        core_label = "CORE (lifetime — the main story):"
        recent_label = "RECENT (last 7 days — correction to the main story, not the main story itself):"
    else:
        core = [
            ("total_tournaments",     "Турниров всего"),
            ("coverage_pct",          "Карта открыта (%)"),
            ("top_cluster",           "Главный кластер"),
            ("top_cluster_pct",       "Доля главного кластера (%)"),
            ("second_cluster",        "Второй кластер"),
            ("archetype_most_freq",   "Самый частый архетип"),
            ("uniqueness_pct",        "Уникальность (%)"),
            ("avg_session_len_min",   "Средняя сессия (мин)"),
            ("fav_hour",              "Любимый час (UTC)"),
        ]
        recent = [
            ("tournaments_last_7d",   "Турниров за последние 7 дней"),
            ("uniqueness_pct_recent", "Уникальность за 7 дней (%)"),
            ("streak_days",           "Текущая серия (дней)"),
            ("archetype_last",        "Последний архетип"),
            ("recent_shift_from",     "Сдвиг кластера ИЗ"),
            ("recent_shift_to",       "Сдвиг кластера В"),
        ]
        core_label = "ОСНОВНОЕ (всё время - главный сюжет портрета):"
        recent_label = "НЕДАВНЕЕ (последние 7 дней - поправка к основному, НЕ главный сюжет сам по себе):"

    def render(section_label, keys):
        out = [section_label]
        for k, label in keys:
            v = stats.get(k)
            if v is not None:
                out.append(f"- {label}: {v}")
        return out

    return "\n".join(render(core_label, core) + [""] + render(recent_label, recent))


def _format_tournament_block(rows: list[dict], lang: str) -> str:
    """Render the full tournament history as a numbered list with full archetype bodies."""
    out = []
    cat_lbl = "Категория" if lang == "ru" else "Category"
    cluster_lbl = "Кластер" if lang == "ru" else "Cluster"
    top_lbl = "Топ-3" if lang == "ru" else "Top 3"
    arch_lbl = "Архетип" if lang == "ru" else "Archetype"
    body_lbl = "Описание архетипа" if lang == "ru" else "Archetype text"

    for i, r in enumerate(rows, 1):
        date = (r.get("completed_at") or "")[:10]
        cluster = r.get("cluster") or "?"
        cat_name = r.get("category_name") or "?"
        t1 = r.get("top1_name") or "?"
        t2 = r.get("top2_name") or "?"
        t3 = r.get("top3_name") or "?"
        arch_name = r.get("archetype_name") or "?"
        arch_body = (r.get("archetype_body") or "").strip()

        out.append(f"[{i}] {date} | {cluster_lbl}: {cluster} | {cat_lbl}: {cat_name}")
        out.append(f"    {top_lbl}: 1) {t1}; 2) {t2}; 3) {t3}")
        out.append(f"    {arch_lbl}: {arch_name}")
        if arch_body:
            # Indent the body for readability; leave it whole - the AI uses it for analysis
            indented = "\n      ".join(arch_body.split("\n"))
            out.append(f"    {body_lbl}: {indented}")
        out.append("")  # blank line between tournaments
    return "\n".join(out)


def _gender_directive(lang: str, gender: str | None) -> str:
    """Build the gender directive prepended to the user message. If gender
    is known, the AI is told to use the correct forms. If unknown, strict
    gender-neutral instructions kick in. Haiku tends to slip on the latter,
    so we make the unknown case explicit + repeat the worst-offender examples."""
    if lang == "en":
        if gender == "female":
            return "User gender: female. (English doesn't gender past tense, but keep tone neutral.)\n\n"
        if gender == "male":
            return "User gender: male. (English doesn't gender past tense.)\n\n"
        return "User gender: unknown. Keep wording gender-neutral.\n\n"

    # Russian
    if gender == "female":
        return (
            "ПОЛ ПОЛЬЗОВАТЕЛЯ: ЖЕНСКИЙ.\n"
            "Используй ИСКЛЮЧИТЕЛЬНО женские формы где грамматика требует согласования:\n"
            "- Прошедшее время: «ты сделала», «ты выбрала», «ты смотрела», «ты пришла», «ты поняла».\n"
            "- Короткие прилагательные: «ты экспрессивна», «ты многословна», «ты сдержанна», «ты готова», «ты уверена», «ты влюблена».\n"
            "- Существительные-роли: «хранительница», «охотница», «защитница». НЕ используй «хранитель» и т.п. в применении к ней.\n"
            "- Возвратные местоимения: «сама», НЕ «сам».\n"
            "Это правило критично, проверь каждое предложение перед сдачей.\n\n"
        )
    if gender == "male":
        return (
            "ПОЛ ПОЛЬЗОВАТЕЛЯ: МУЖСКОЙ.\n"
            "Используй мужские формы где грамматика требует согласования (ты сделал, ты готов, ты уверен, сам). "
            "Стандартные русские мужские формы.\n\n"
        )
    # Unknown gender — repeat the strict neutrality rules at the top of the
    # user message (in addition to the system prompt). Haiku is more likely
    # to obey when the rule is RIGHT BEFORE the data.
    return (
        "ПОЛ ПОЛЬЗОВАТЕЛЯ: НЕИЗВЕСТЕН — может быть мужчина или женщина.\n"
        "СТРОЖАЙШИЙ ЗАПРЕТ на формы, согласующиеся по роду:\n"
        "- Без прошедшего времени глаголов с «ты» (НЕ «ты сделал/сделала», «ты пришёл/пришла», «ты выбрал/выбрала»). Только настоящее или существительное-приложение.\n"
        "- Без коротких прилагательных (НЕ «ты экспрессивен/экспрессивна», «ты готов/готова», «ты уверен/уверена», «ты влюблён/влюблена», «ты сдержан/сдержанна», «ты многословен/многословна»). Перефразируй: «у тебя сдержанность», «тебе важно», «тебя цепляет».\n"
        "- Без возвратного «сам/сама».\n"
        "- Без существительных-ролей в одной форме («хранитель» — мужское). Используй более общие слова: «тот, кто...», «человек, который...».\n"
        "Это критично, проверь каждое предложение с «ты» перед сдачей.\n\n"
    )


def build_prompt(
    user_nick: str,
    lang: str,
    stats: dict,
    history: list[dict],
    user_gender: str | None = None,
) -> tuple[str, str]:
    """Build (system_prompt, user_message) for the Anthropic API call.

    user_gender: 'male' | 'female' | None. If known, AI is told to use the
    correct gendered forms. If None, strict neutrality rules are repeated
    in the user message (Haiku tends to slip on system-prompt-only rules).
    """
    system = _select_system_prompt(lang)
    gender_directive = _gender_directive(lang, user_gender)
    if lang == "en":
        header = gender_directive + f"User: @{user_nick}\n\nStats:\n"
        history_header = f"\n\nFULL TOURNAMENT HISTORY (oldest to newest):\n\n"
    else:
        header = gender_directive + f"Пользователь: @{user_nick}\n\nСтатистика:\n"
        history_header = f"\n\nПОЛНАЯ ИСТОРИЯ ТУРНИРОВ (от старых к новым):\n\n"

    user_msg = (
        header
        + _format_stats_block(stats, lang)
        + history_header
        + _format_tournament_block(history, lang)
    )
    return system, user_msg


# ---------------------------------------------------------------------------
# Anthropic API client (minimal, stdlib-only)
# ---------------------------------------------------------------------------

def _post_process(text: str) -> str:
    """Cheap safety net for things the model ignores despite system-prompt rules.

    - Em-dash (—) → regular hyphen-minus (-). The model is trained on a lot of
      Russian where em-dash is standard, so it slips through even when the
      prompt says not to. Replacing post-hoc is cheaper and more reliable than
      arguing with the model.
    - Some models slip in ASCII en-dash (–) too; normalize that as well.
    """
    return text.replace("—", "-").replace("–", "-")


def call_anthropic(
    system: str,
    user_msg: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 2000,
    api_key: str | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """Single shot to /v1/messages. Returns dict:
      {
        "text": "..."         # the assistant's reply
        "input_tokens": int,
        "output_tokens": int,
        "model": str,
        "raw": dict,          # full API response
      }
    Raises RuntimeError on auth / HTTP / JSON failure.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set (env or arg)")

    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_msg}],
    }).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        headers={
            "x-api-key": key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic API HTTP {e.code}: {err_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Anthropic API network error: {e}")

    # content is a list of blocks; first text block is our reply
    content = raw.get("content") or []
    text_blocks = [b for b in content if b.get("type") == "text"]
    if not text_blocks:
        raise RuntimeError(f"Anthropic API returned no text blocks: {raw}")
    text = _post_process(text_blocks[0].get("text", ""))

    usage = raw.get("usage") or {}
    return {
        "text": text,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "model": raw.get("model", model),
        "raw": raw,
    }


# ---------------------------------------------------------------------------
# Orchestrator: DB → prompt → API → result
# ---------------------------------------------------------------------------

def _fetch_results_with_clusters(
    conn: sqlite3.Connection,
    user_id: int,
    categories: list[dict],
) -> list[dict]:
    """Fetch all results for user with cluster derived from categories.json."""
    cat_cluster: dict[str, str] = {
        c["id"]: c.get("cluster", "?") for c in categories if "id" in c
    }
    rows = conn.execute(
        """
        SELECT category_id, category_name,
               top1_name, top2_name, top3_name,
               archetype_name, archetype_body,
               completed_at
        FROM results
        WHERE user_id = ?
        ORDER BY completed_at ASC
        """,
        (user_id,),
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["cluster"] = cat_cluster.get(d["category_id"], "?")
        out.append(d)
    return out


def _fetch_user_nick(conn: sqlite3.Connection, user_id: int) -> str:
    row = conn.execute(
        "SELECT nickname FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if row and row["nickname"]:
        return row["nickname"]
    return f"user{user_id}"


def _fetch_user_gender(conn: sqlite3.Connection, user_id: int) -> str | None:
    """Returns 'male' | 'female' | None. Defensive against missing column."""
    try:
        row = conn.execute(
            "SELECT gender FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row and row["gender"] in ("male", "female"):
            return row["gender"]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# DB helpers (cache, gates, slug)
# ---------------------------------------------------------------------------
# Rate limit for free generations. User can regenerate at most once per
# FREE_COOLDOWN_HOURS hours unless they pay (paid path lands in Phase 2).
FREE_COOLDOWN_HOURS = 24 * 7  # 7 days

# Minimum tournaments before the first portrait can be generated. Less than
# this and the AI doesn't have enough signal to write a coherent portrait —
# it falls back into generalities. 10 is enough for visible patterns to
# emerge across categories. Applies to both free and unlimited users.
MIN_TOURNAMENTS_FOR_FIRST_PORTRAIT = 10

# Slug alphabet: lowercase + digits, no look-alikes (no 0/o, no 1/l/i)
import secrets
_SLUG_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


def _new_public_slug(length: int = 10) -> str:
    """Random URL-safe slug for public sharing. Collision odds are tiny at
    31^10 ≈ 8e14, but the table has UNIQUE constraint as backstop."""
    return "".join(secrets.choice(_SLUG_ALPHABET) for _ in range(length))


def _count_user_tournaments(conn: sqlite3.Connection, user_id: int) -> int:
    """Total tournaments completed by user. Used for the activity gate."""
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM results WHERE user_id = ?", (user_id,)
    ).fetchone()
    return int(row["n"]) if row else 0


def get_latest_portrait(
    conn: sqlite3.Connection,
    user_id: int,
    scope_kind: str = "global",
    scope_key: str | None = None,
) -> dict | None:
    """Return the most recent portrait for this user+scope, or None.

    Match on participant_ids JSON containing the user (for solo portraits it's
    a single-element array, e.g. '[2]'). For phase 1 we only do solo, so the
    query is a simple equality; pair/group will use LIKE in Phase 3.
    """
    participants_json = json.dumps([user_id])
    if scope_key is None:
        row = conn.execute(
            """
            SELECT * FROM user_portraits
            WHERE participant_ids = ? AND scope_kind = ? AND scope_key IS NULL
            ORDER BY generated_at DESC LIMIT 1
            """,
            (participants_json, scope_kind),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT * FROM user_portraits
            WHERE participant_ids = ? AND scope_kind = ? AND scope_key = ?
            ORDER BY generated_at DESC LIMIT 1
            """,
            (participants_json, scope_kind, scope_key),
        ).fetchone()
    return dict(row) if row else None


def _is_unlimited(conn: sqlite3.Connection, user_id: int) -> bool:
    """Check the user's portrait_unlimited flag. Owner/admin accounts get
    this set manually (no UI toggle) and bypass both cooldown + activity
    gates. Returns False on any error or missing column (defensive)."""
    try:
        row = conn.execute(
            "SELECT portrait_unlimited FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return bool(row and row["portrait_unlimited"])
    except Exception:
        return False


def evaluate_gates(
    conn: sqlite3.Connection,
    user_id: int,
    scope_kind: str = "global",
    scope_key: str | None = None,
    cooldown_hours: int = FREE_COOLDOWN_HOURS,
) -> dict:
    """Decide whether the user can generate a new portrait right now.

    Returns a dict the API endpoint translates into HTTP status + body:
      {
        "can_generate": bool,
        "blocked_reason": "cooldown" | "no_new_tournaments" | None,
        "next_available_at": ISO8601 | None,  # when cooldown lifts
        "current_tournaments": int,
        "tournaments_at_last_gen": int | None,
        "last_generated_at": ISO8601 | None,
        "is_unlimited": bool,  # owner/admin override; bypasses both gates
      }
    """
    latest = get_latest_portrait(conn, user_id, scope_kind, scope_key)
    current_count = _count_user_tournaments(conn, user_id)
    unlimited = _is_unlimited(conn, user_id)

    base = {
        "current_tournaments": current_count,
        "tournaments_at_last_gen": latest["tournaments_at_gen"] if latest else None,
        "last_generated_at": latest["generated_at"] if latest else None,
        "is_unlimited": unlimited,
    }

    # Case 1: never generated → allowed only if user has at least
    # MIN_TOURNAMENTS_FOR_FIRST_PORTRAIT games. Below that, AI doesn't have
    # enough signal — portrait would fall back into generic flattery.
    if latest is None:
        return {
            **base,
            "can_generate": current_count >= MIN_TOURNAMENTS_FOR_FIRST_PORTRAIT,
            "blocked_reason": None if current_count >= MIN_TOURNAMENTS_FOR_FIRST_PORTRAIT else "not_enough_tournaments",
            "next_available_at": None,
        }

    # Unlimited bypass: skip cooldown + activity gates entirely.
    # Still respect the minimum-tournament threshold (data quality matters
    # even for owner accounts).
    if unlimited:
        return {
            **base,
            "can_generate": current_count >= MIN_TOURNAMENTS_FOR_FIRST_PORTRAIT,
            "blocked_reason": None if current_count >= MIN_TOURNAMENTS_FOR_FIRST_PORTRAIT else "not_enough_tournaments",
            "next_available_at": None,
        }

    # Case 2: cooldown not yet elapsed
    last_dt = datetime.fromisoformat(latest["generated_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    next_at = last_dt + timedelta(hours=cooldown_hours)
    if now < next_at:
        return {
            **base,
            "can_generate": False,
            "blocked_reason": "cooldown",
            "next_available_at": next_at.isoformat().replace("+00:00", "Z"),
        }

    # Case 3: cooldown elapsed but no new tournaments since last
    if current_count <= latest["tournaments_at_gen"]:
        return {
            **base,
            "can_generate": False,
            "blocked_reason": "no_new_tournaments",
            "next_available_at": None,
        }

    # Case 4: everything OK, generate allowed
    return {
        **base,
        "can_generate": True,
        "blocked_reason": None,
        "next_available_at": None,
    }


def save_portrait(
    conn: sqlite3.Connection,
    user_id: int,
    result: dict,
    lang: str,
    scope_kind: str = "global",
    scope_key: str | None = None,
    is_public: int = 0,
    credits_spent: int = 0,
) -> dict:
    """Insert a new portrait row. Old portraits of the same (user, scope)
    are KEPT as historical snapshots tied to their `generated_at` date.

    The user's profile shows only the latest (via get_latest_portrait), but
    older versions remain accessible by their public_slug (if still public)
    and via an eventual portrait-history view. This preserves the «taste
    over time» story: a portrait from last month vs this month tells the
    user how their identity in the data has shifted.
    """
    participants_json = json.dumps([user_id])
    current_tournaments = _count_user_tournaments(conn, user_id)
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Generate slug. Retry up to 3 times on UNIQUE collision (vanishingly rare).
    slug = None
    for _ in range(3):
        candidate = _new_public_slug()
        existing = conn.execute(
            "SELECT 1 FROM user_portraits WHERE public_slug = ?", (candidate,)
        ).fetchone()
        if not existing:
            slug = candidate
            break
    if slug is None:
        slug = _new_public_slug(length=14)  # longer fallback

    cur = conn.execute(
        """
        INSERT INTO user_portraits (
          scope_kind, scope_key, participant_ids,
          generated_at, tournaments_at_gen, content_md, lang,
          is_public, public_slug, model_used, credits_spent,
          input_tokens, output_tokens
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            scope_kind, scope_key, participants_json,
            now_iso, current_tournaments, result["text"], lang,
            is_public, slug, result["model"], credits_spent,
            result["input_tokens"], result["output_tokens"],
        ),
    )
    portrait_id = cur.lastrowid

    # Audit ledger: append-only record of AI cost. Decoupled from portraits
    # so deletion/replacement of a portrait doesn't lose the spend record.
    kind = "portrait_" + scope_kind  # 'portrait_global', 'portrait_cluster', ...
    conn.execute(
        """
        INSERT INTO anthropic_spend_ledger
          (occurred_at, kind, user_id, ref_portrait_id, model_used,
           input_tokens, output_tokens, cost_usd, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now_iso, kind, user_id, portrait_id,
            result.get("model"),
            result.get("input_tokens", 0),
            result.get("output_tokens", 0),
            result.get("cost_usd", 0),
            None,
        ),
    )

    row = conn.execute(
        "SELECT * FROM user_portraits WHERE id = ?", (portrait_id,)
    ).fetchone()
    return dict(row) if row else {}


def get_portrait_by_slug(conn: sqlite3.Connection, slug: str) -> dict | None:
    """Public-share lookup. Returns dict or None. Caller must check is_public."""
    row = conn.execute(
        "SELECT * FROM user_portraits WHERE public_slug = ?", (slug,)
    ).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# AI generation orchestrator (was last function; unchanged below)
# ---------------------------------------------------------------------------

def generate_global_portrait(
    conn: sqlite3.Connection,
    user_id: int,
    categories: list[dict],
    lang: str = "ru",
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> dict[str, Any]:
    """End-to-end: compute stats, build prompt, call API, return portrait + metrics.

    Returns:
      {
        "text": str,                  # markdown portrait
        "input_tokens": int,
        "output_tokens": int,
        "cost_usd": float,            # estimated $$ for this call
        "latency_sec": float,
        "model": str,
        "prompt_chars": int,
        "history_count": int,
      }
    """
    stats = compute_user_stats(conn, user_id, categories)
    history = _fetch_results_with_clusters(conn, user_id, categories)
    nick = _fetch_user_nick(conn, user_id)
    user_gender = _fetch_user_gender(conn, user_id)

    system, user_msg = build_prompt(nick, lang, stats, history, user_gender=user_gender)

    t0 = time.time()
    result = call_anthropic(system, user_msg, model=model, api_key=api_key)
    latency = time.time() - t0

    in_tok = result["input_tokens"]
    out_tok = result["output_tokens"]
    # Anthropic returns dated IDs (claude-haiku-4-5-20251001); strip date so
    # the family-alias-keyed pricing dict resolves correctly.
    model_returned = result.get("model", model)
    model_lookup = re.sub(r"-\d{8}$", "", model_returned)
    in_price, out_price = MODEL_PRICING_USD_PER_MTOK.get(
        model_lookup,
        MODEL_PRICING_USD_PER_MTOK.get(model, (0.0, 0.0)),
    )
    cost = (in_tok / 1_000_000) * in_price + (out_tok / 1_000_000) * out_price

    return {
        "text": result["text"],
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": round(cost, 4),
        "latency_sec": round(latency, 2),
        "model": result["model"],
        "prompt_chars": len(user_msg) + len(system),
        "history_count": len(history),
    }
