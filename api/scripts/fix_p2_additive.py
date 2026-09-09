# -*- coding: utf-8 -*-
"""Chunk 3: make archetype P2 (the paragraph the synthesizer splices into
blended portraits) additive + self-contained, so 2-3 of them read as one
coherent person instead of contradicting each other.

Fixes two breakers found by scan:
  - backref openings ("За этим стоит...") that dangle when P2 is shown alone
  - absolute/exclusive claims ("единственная честная шкала", "не описывает
    опыт") that directly contradict sibling archetypes in a blend

Only P2 (paragraph index 1) is replaced; P1/P3/P4 untouched. RU + EN.
Run: python3 fix_p2_additive.py [--apply]
"""
import json, shutil, sys
from datetime import datetime

CATEGORIES_PATH = '/opt/untitled-pick-game-api/data/categories.json'

# (cid, archetype_name) -> {p2, p2_en}
NEW_P2 = {
    ('football_goat', 'В граните'): {
        'p2': "Тебе важен измеримый след. Ощущения у всех разные - зато рекорды одинаковы для каждого. Количество наград, голы в решающих матчах, стабильность на протяжении полутора десятка лет - для тебя это честная опора в любом споре о величии. Статистика хотя бы не подстраивается под то, кому ты симпатизируешь.",
        'p2_en': "What matters to you is a measurable trail. Feelings differ for everyone - records are the same for everyone. Number of awards, goals in decisive matches, consistency across fifteen-plus years - for you that's an honest anchor in any argument about greatness. Statistics, at least, don't shift to suit whoever you happen to like.",
    },
    ('football_goat', 'Живой огонь'): {
        'p2': "Тебя цепляет то, что не влезает в таблицу. Когда болельщики противоположных команд несут одного игрока на руках после матча - это не субъективщина, а по-своему измеримый факт. Воздействие на зрителя так же реально как рекорд в таблице - просто труднее оцифровать.",
        'p2_en': "What grips you is the thing that doesn't fit the table. When fans of opposing teams carry one player off the pitch on their shoulders - that isn't subjectivity, it's a measurable fact in its own way. Impact on the viewer is as real as a record on the table - just harder to quantify.",
    },
    ('football_goat', 'До нас'): {
        'p2': "Величие нужно судить в условиях своего времени - это твоя опорная мысль. Три «Золотых мяча» подряд в эпоху когда восточная Европа практически не имела доступа к западному голосованию - это другой вес чем тот же приз сегодня. Голы в финале чемпионата мира и чемпионата Европы в один год - невозможный сегодня формат. Победа спустя катастрофу которую не должен был пережить никто - часть истории, а не сноска. Контекст для тебя - часть аргумента, а не смягчающее обстоятельство.",
        'p2_en': "Greatness must be judged in the conditions of its own time - that's your anchoring thought. Three Ballons d'Or in a row in an era when Eastern Europe had almost no access to Western voting carries a different weight than the same prize today. Goals in the World Cup final AND the European Championship final in one year - a format impossible today. Victory after a disaster no one should have survived - part of history, not a footnote. Context, for you, is part of the argument, not a mitigating circumstance.",
    },
    ('football_clubs', 'Хрустальный зал'): {
        'p2': "Для тебя история - лучший судья. Национальные чемпионства зависят от конкуренции внутри страны. Еврокубки - нет: там все против всех. Клуб который победил пятнадцать раз доказал состоятельность пятнадцать раз против всей Европы. Для тебя это не цифра, это аргумент.",
        'p2_en': "For you, history is the best judge. National titles depend on how competitive the country is. European cups don't - everyone comes there. A club that won fifteen times proved its quality fifteen times against all of Europe. For you that's not a statistic. It's an argument.",
    },
    ('football_clubs', 'Железный занавес'): {
        'p2': "Ты ценишь преемственность. Московский клуб начала 90-х, державшийся на своей школе. Киевская династия легендарного тренера, опередившая эпоху научным подходом к игре. Команда с востока, за двадцать лет ставшая доминирующей силой своей страны. Всё это истории долгого строительства в условиях которые западные клубы никогда не переживали. Тебе важна эта контекстуальность.",
        'p2_en': "You value continuity. A Moscow side of the early 90s that held together on its own school. A Kyiv dynasty under a legendary coach who was ahead of his era with a scientific approach to the game. A club from the east that became its country's dominant force over twenty years. All these are stories of long construction under conditions Western clubs never experienced. That contextuality matters to you.",
    },
    ('football_clubs', 'Горячее море'): {
        'p2': "Для тебя мировой футбол больше чем пять западноевропейских лиг. Африканский гранд, бравший свой континентальный кубок чемпионов десять раз - это не «другой уровень», это другое измерение. Турецкие и греческие клубы поднимали над головой европейские трофеи - Кубок УЕФА, Суперкубок, Лигу конференций. Эти клубы существуют не в тени, а в своём собственном свете.",
        'p2_en': "For you, world football is larger than five western European leagues. An African giant that won its continental champions cup ten times - that's not «a different level,» it's a different dimension. Turkish and Greek clubs have lifted European trophies over their heads - the UEFA Cup, the Super Cup, the Conference League. These clubs don't exist in someone's shadow - they have their own light.",
    },
}


def replace_p2(text, new_p2):
    if not text:
        return text
    sep = '\n\n' if '\n\n' in text else '\n'
    ps = [p for p in text.split(sep) if p.strip()]
    if len(ps) < 2:
        return text  # no P2 to replace
    ps[1] = new_p2
    return '\n\n'.join(ps)


def main():
    dry_run = '--apply' not in sys.argv
    with open(CATEGORIES_PATH, encoding='utf-8') as f:
        cats = json.load(f)
    by_id = {c.get('id'): c for c in cats}

    applied = []
    missing = []
    for (cid, aname), fields in NEW_P2.items():
        c = by_id.get(cid)
        if not c:
            missing.append(f'cat {cid}')
            continue
        a = next((x for x in c.get('archetypes', []) if x.get('name') == aname), None)
        if not a:
            missing.append(f'[{cid}] «{aname}»')
            continue
        a['body'] = replace_p2(a.get('body', ''), fields['p2'])
        a['body_en'] = replace_p2(a.get('body_en', ''), fields['p2_en'])
        applied.append(f'  [{cid}] «{aname}»: P2 RU {len(fields["p2"])} / EN {len(fields["p2_en"])}')

    print(f'P2 REPLACEMENTS: {len(applied)}')
    for line in applied:
        print(line)
    if missing:
        print(f'MISSING: {len(missing)}')
        for line in missing:
            print(f'  {line}')

    if dry_run:
        print('\n=== DRY RUN - run with --apply ===')
        sys.exit(0)

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = CATEGORIES_PATH + f'.bak.p2_additive.{ts}'
    shutil.copy(CATEGORIES_PATH, backup_path)
    print(f'\nBackup: {backup_path}')
    with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    print('Saved')


if __name__ == '__main__':
    main()
