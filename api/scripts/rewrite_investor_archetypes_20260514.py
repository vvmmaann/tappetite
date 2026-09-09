"""Rewrite first paragraph of each archetype in 'investor_type' category.

Reason: existing п1 paragraphs make universal proclamations ("Лучшая
инвестиция — это ты", "Крипта — воздух, квартира — бетон") that violate
the new H8 rule (added today to admin.html buildCategoryPrompt). When the
hybrid composition splices two such п1s together, the result reads as
shizofrenia — direct factual contradictions.

This script replaces ONLY paragraph 1 (split on \\n\\n, replace index [0],
rejoin). Paragraphs 2-4 describe behavior/social/risk and don't carry the
universal claims, so they're left intact. Names, triggers, and ids are
unchanged — same matching logic, same archetype wins for same top-3.

Run on server:
    cd /opt/untitled-pick-game-api
    python3 scripts/rewrite_investor_archetypes_20260514.py
    systemctl restart untitled-pick-game-api

Backs up categories.json with timestamp before writing.
"""
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = Path("/opt/untitled-pick-game-api/data/categories.json")
CATEGORY_ID = "investor_type"

# arch_name (RU) -> (new_para1_ru, new_para1_en)
# Keyed by RU name (which is a stable identifier within the category)
NEW_PARA1 = {
    "Хранитель очага": (
        "Вечером ты листаешь банковское приложение, видишь свой процент по вкладу — и в груди становится ровно. "
        "Не от жадности, а от мысли «у меня есть запас на любой случай». "
        "Накопления для тебя — это не цифра дохода, а лекарство от тревоги.",
        "In the evening you scroll through your banking app, see your deposit rate, and feel something settle in your chest. "
        "Not greed — relief. "
        "Your savings aren't a number you're chasing, they're a medicine for the anxiety of not knowing what tomorrow brings."
    ),
    "Системный игрок": (
        "Утро начинается не с кофе, а с биржевых сводок — и это не невроз, а ритуал. "
        "У тебя есть стратегия, и она не зависит от того, что вчера сказал блогер. "
        "Регулярность тебе ближе, чем озарение: лучше скучный план, который работает 10 лет, чем красивая ставка на месяц.",
        "Your morning starts not with coffee but with market updates — and that's not anxiety, it's ritual. "
        "You have a strategy that doesn't depend on what some blogger said yesterday. "
        "Routine is more your speed than insight: a boring plan that works for 10 years beats a brilliant bet for a month."
    ),
    "Охотник за алмазами": (
        "Тебя цепляют истории, где можно поймать редкий взлёт. "
        "Где есть шанс на х10, а не +5%. Скучная стабильная доходность тебя усыпляет; "
        "ты приходишь за тем, чтобы ставка либо ничего не стоила, либо изменила год жизни.",
        "You're drawn to the stories where someone catches a rare upswing. "
        "Places where there's a chance of 10x, not +5%. A boring stable yield puts you to sleep; "
        "you show up for the bets that either cost nothing or change your year."
    ),
    "Тактильный капиталист": (
        "Тебе важно, чтобы инвестицию можно было потрогать. "
        "Ключи в кармане, картина на стене, метраж в документах — это не про статус, это про другую природу владения. "
        "Цифры в портфеле тебе кажутся хрупкими; то, что стоит на земле, ощущается как настоящее.",
        "For you, an investment has to be something you can touch. "
        "Keys in your pocket, a painting on the wall, square meters on the deed — not about status, about a different kind of ownership. "
        "Numbers in a portfolio feel fragile to you; what stands on the ground feels real."
    ),
    "Сам себе брокер": (
        "Тебе ближе вкладывать в свои навыки и здоровье, чем в чужие компании. "
        "Своё образование, своё дело, своё тело — ты хотя бы видишь и понимаешь. "
        "Где зарабатывают другие, остаётся для тебя загадкой; где зарабатываешь ты сам — там понятно, на что тратится каждый час.",
        "You'd rather invest in your own skills and health than in someone else's company. "
        "Your education, your business, your body — at least you can see and understand them. "
        "How others make money stays a mystery; how you make money — there, every hour spent has a clear destination."
    ),
    "Цифровой кочевник": (
        "Когда ты выбираешь, куда вложиться, страна для тебя не главный фильтр — главное, где сейчас идёт рост. "
        "Покупаешь американские акции, азиатские ETF, индексы на весь мир. "
        "Ощущаешь себя гражданином рынка раньше, чем гражданином географии.",
        "When you choose where to put money, the country isn't your main filter — what matters is where the growth is happening right now. "
        "You buy US stocks, Asian ETFs, global index funds. "
        "You feel like a citizen of the market before you feel like a citizen of any geography."
    ),
}


def main():
    if not SRC.exists():
        print(f"[err] not found: {SRC}", file=sys.stderr)
        sys.exit(1)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = SRC.with_suffix(f".json.bak.{ts}")
    shutil.copy2(SRC, backup)
    print(f"[ok] backup: {backup}")

    data = json.loads(SRC.read_text(encoding="utf-8"))
    cats = data if isinstance(data, list) else data.get("categories", [])

    target = next((c for c in cats if c.get("id") == CATEGORY_ID), None)
    if not target:
        print(f"[err] category '{CATEGORY_ID}' not found", file=sys.stderr)
        sys.exit(1)

    found, missing = [], set(NEW_PARA1)
    for arch in target.get("archetypes", []) or []:
        name = arch.get("name", "")
        if name in NEW_PARA1:
            new_ru, new_en = NEW_PARA1[name]

            # RU body — split on \n\n, replace [0]
            old_body = arch.get("body", "") or ""
            paras = old_body.split("\n\n")
            old_p1 = paras[0] if paras else ""
            paras[0] = new_ru
            arch["body"] = "\n\n".join(paras)

            # EN body — same
            old_body_en = arch.get("body_en", "") or ""
            paras_en = old_body_en.split("\n\n")
            old_p1_en = paras_en[0] if paras_en else ""
            paras_en[0] = new_en
            arch["body_en"] = "\n\n".join(paras_en)

            found.append((name, old_p1, new_ru, old_p1_en, new_en))
            missing.discard(name)

    print(f"\n[ok] applied to {len(found)}/{len(NEW_PARA1)} archetypes:")
    for name, old_ru, new_ru, old_en, new_en in found:
        print(f"\n--- {name} ---")
        print(f"  old п1 (RU): {old_ru[:120]}…")
        print(f"  new п1 (RU): {new_ru[:120]}…")
        print(f"  old п1 (EN): {old_en[:120]}…")
        print(f"  new п1 (EN): {new_en[:120]}…")

    if missing:
        print(f"\n[warn] not found in '{CATEGORY_ID}': {sorted(missing)}")
        print("       (check archetype names — they may have changed)")

    SRC.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[ok] wrote: {SRC}")
    print("Next: systemctl restart untitled-pick-game-api")


if __name__ == "__main__":
    main()
