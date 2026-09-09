"""
Расширение категории night_films с 16 до 32 items.
Добавляем популярные стоящие фильмы в стиле "ночного просмотра",
расширяем triggers существующих 7 архетипов, добавляем 8-й архетип
"Город не спит" для атмосферных neo-noir / медитативных лент.

Атомарная запись с backup.
"""
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

CATEGORIES_JSON = Path('/opt/untitled-pick-game-api/data/categories.json')

NEW_ITEMS = [
    {"id": "taxi",          "name": "Таксист",                "ctx": "1976 · Скорсезе · одинокий нью-йорк"},
    {"id": "sevenfilm",     "name": "Семь",                   "ctx": "1995 · Финчер · семь грехов"},
    {"id": "losthwy",       "name": "Шоссе в никуда",         "ctx": "1997 · Линч · двойник во сне"},
    {"id": "shining",       "name": "Сияние",                 "ctx": "1980 · Кубрик · отель и безумие"},
    {"id": "prestige",      "name": "Престиж",                "ctx": "2006 · Нолан · фокус и одержимость"},
    {"id": "sixthsense",    "name": "Шестое чувство",         "ctx": "1999 · Шьямалан · мальчик и духи"},
    {"id": "truman",        "name": "Шоу Трумана",            "ctx": "1998 · Уир · мир как декорация"},
    {"id": "usualsuspects", "name": "Подозрительные лица",    "ctx": "1995 · Сингер · кто такой Кейзер Созе"},
    {"id": "br2049",        "name": "Бегущий по лезвию 2049", "ctx": "2017 · Вильнёв · пустыня и память"},
    {"id": "underskin",     "name": "Под кожей",              "ctx": "2013 · Глейзер · хищница в Глазго"},
    {"id": "solaris",       "name": "Солярис",                "ctx": "1972 · Тарковский · океан-зеркало"},
    {"id": "lobster",       "name": "Лобстер",                "ctx": "2015 · Лантимос · отель одиночек"},
    {"id": "antichrist",    "name": "Антихрист",              "ctx": "2009 · фон Триер · горе и хаос"},
    {"id": "melancholia",   "name": "Меланхолия",             "ctx": "2011 · фон Триер · конец света"},
    {"id": "lostintrans",   "name": "Трудности перевода",     "ctx": "2003 · Коппола · бессонный Токио"},
    {"id": "drive",         "name": "Драйв",                  "ctx": "2011 · Рефн · неоновый Лос-Анджелес"},
]

# Расширения triggers по именам существующих архетипов
TRIGGER_ADDITIONS = {
    "Тёмная психология":   ["taxi", "sevenfilm", "shining"],
    "Сюжет-головоломка":   ["prestige", "sixthsense", "truman", "usualsuspects"],
    "Сюрреализм и сны":    ["losthwy"],
    "Холодный сай-фай":    ["br2049", "underskin", "solaris", "lobster"],
    "Глубокая боль":       ["melancholia"],
    "Артхаус с шоком":     ["antichrist"],
}

NEW_ARCHETYPE = {
    "name": "Город не спит",
    "body": (
        "Ты любишь, когда город — главный герой. Не «фоном», а живой частью истории: "
        "неоновое отражение в луже, гул кондиционера в окне, бессонный таксист "
        "на пустом перекрёстке. Тебе важна атмосфера времени и места, а не только сюжет.\n\n"
        "Это работает потому, что для тебя кино — медитация. Не «что произойдёт», "
        "а «как это ощущается». Ты часто помнишь не финал, а момент: лицо героини "
        "в стекле, мерцание вывески, случайный разговор в баре отеля. Ты заходишь "
        "в фильм как в чужую комнату — посидеть.\n\n"
        "Окружающие иногда не понимают: «но там же ничего не происходит». Для тебя — "
        "наоборот, происходит главное. Ты ценишь паузы, тишину, медленные кадры. "
        "Тебе скучно, когда сюжет несётся вперёд, не давая зрителю просто быть в этом мире.\n\n"
        "Что стоит знать: твоё кино требует настроения и времени. Не ставь его на фон — "
        "оно сольётся в шум. И не суди фильмы по динамике: иногда самый важный момент — "
        "в трёх минутах, когда героиня просто стоит у окна."
    ),
    "triggers": ["drive", "lostintrans", "br2049", "underskin"],
}


def main() -> int:
    if not CATEGORIES_JSON.exists():
        print(f"ERROR: {CATEGORIES_JSON} not found")
        return 1

    raw = json.loads(CATEGORIES_JSON.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        print(f"ERROR: expected list at root, got {type(raw).__name__}")
        return 1

    target = next((c for c in raw if c.get("id") == "night_films"), None)
    if target is None:
        print("ERROR: night_films category not found")
        return 1

    print(f"Found: {target.get('name')}")
    print(f"  before: {len(target.get('items', []))} items, "
          f"{len(target.get('archetypes', []))} archetypes, "
          f"size={target.get('recommended_tournament_size')}")

    # 1. Append new items (skip duplicates by id)
    existing_ids = {it["id"] for it in target.get("items", [])}
    added = 0
    for it in NEW_ITEMS:
        if it["id"] in existing_ids:
            print(f"  SKIP existing item: {it['id']}")
            continue
        target.setdefault("items", []).append(it)
        added += 1
    print(f"  added {added} new items")

    # 2. Bump tournament size to 32
    target["recommended_tournament_size"] = 32

    # 3. Extend triggers on existing archetypes
    arch_by_name = {a.get("name"): a for a in target.get("archetypes", [])}
    for arch_name, new_trigs in TRIGGER_ADDITIONS.items():
        if arch_name not in arch_by_name:
            print(f"  WARN: archetype '{arch_name}' not found, skipping")
            continue
        cur = set(arch_by_name[arch_name].get("triggers", []))
        for tid in new_trigs:
            if tid not in cur:
                arch_by_name[arch_name].setdefault("triggers", []).append(tid)
        print(f"  extended '{arch_name}': now {len(arch_by_name[arch_name]['triggers'])} triggers")

    # 4. Append new archetype
    if NEW_ARCHETYPE["name"] not in arch_by_name:
        target.setdefault("archetypes", []).append(NEW_ARCHETYPE)
        print(f"  added new archetype: {NEW_ARCHETYPE['name']}")
    else:
        print(f"  archetype '{NEW_ARCHETYPE['name']}' already exists, skipping")

    # 5. Coverage validator: every item id must appear in at least one trigger list
    all_trigs = set()
    for a in target.get("archetypes", []):
        all_trigs.update(a.get("triggers", []))
    item_ids = [it["id"] for it in target.get("items", [])]
    missing = [iid for iid in item_ids if iid not in all_trigs]
    if missing:
        print(f"  ERROR: items not covered by any archetype: {missing}")
        return 1

    print(f"  AFTER: {len(target['items'])} items, "
          f"{len(target['archetypes'])} archetypes, "
          f"size={target['recommended_tournament_size']}")
    print(f"  coverage OK: all {len(item_ids)} items covered")

    # 6. Atomic write with timestamped backup
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + f".bak.night_films.{stamp}")
    shutil.copy2(CATEGORIES_JSON, backup)
    print(f"  backup: {backup}")

    tmp = CATEGORIES_JSON.with_name(CATEGORIES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CATEGORIES_JSON)
    print(f"  wrote: {CATEGORIES_JSON}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
