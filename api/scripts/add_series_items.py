# -*- coding: utf-8 -*-
"""Stage 1: expand massive_tv_show ("Сериал, что пошёл в народ") with 58 popular
series (the 55 from the user's grid that weren't already there + 3 iconic ones
the grid missed: The Wire, Fargo, Chernobyl). Keeps existing 16. Total -> 74.
Bilingual items (KinoPoisk-standard RU titles). Sets recommended_tournament_size=74.

Archetypes are replaced in a SEPARATE Stage-2 script.
Run: python3 add_series_items.py [--apply]
"""
import json, shutil, sys
from datetime import datetime
CATEGORIES_PATH = '/opt/untitled-pick-game-api/data/categories.json'

# (id, name_ru, name_en, ctx_ru, ctx_en)
NEW = [
 ('the_boys','Пацаны','The Boys','2019 · Amazon · супергерои-отморозки','2019 · Amazon · superheroes gone rotten'),
 ('malcolm_middle','Малкольм в центре внимания','Malcolm in the Middle','2000 · ситком · гений в хаос-семье','2000 · sitcom · a genius in a chaos family'),
 ('westworld','Мир Дикого Запада','Westworld','2016 · HBO · андроиды и парк','2016 · HBO · androids and the park'),
 ('glee','Хор','Glee','2009 · муз-драма · школьный хор','2009 · musical · the show choir'),
 ('htgawm','Как избежать наказания за убийство','How to Get Away with Murder','2014 · юр-триллер · Виола Дэвис','2014 · legal thriller · Viola Davis'),
 ('brooklyn_99','Бруклин 9-9','Brooklyn Nine-Nine','2013 · ситком · полицейский участок','2013 · sitcom · the precinct'),
 ('vampire_diaries','Дневники вампира','The Vampire Diaries','2009 · подростки · вампиры Мистик-Фоллс','2009 · teen · vampires of Mystic Falls'),
 ('sons_of_anarchy','Сыны анархии','Sons of Anarchy','2008 · байкеры · клуб SAMCRO','2008 · bikers · the SAMCRO club'),
 ('euphoria','Эйфория','Euphoria','2019 · HBO · подростки и зависимости','2019 · HBO · teens and addiction'),
 ('bridgerton','Бриджертоны','Bridgerton','2020 · Netflix · регентство и романы','2020 · Netflix · Regency romance'),
 ('black_mirror','Чёрное зеркало','Black Mirror','2011 · антология · технологии-кошмары','2011 · anthology · tech nightmares'),
 ('spartacus','Спартак','Spartacus','2010 · пеплум · кровь и арена','2010 · sword-and-sandal · blood and arena'),
 ('house_md','Доктор Хаус','House M.D.','2004 · меддрама · гений-мизантроп','2004 · medical · the misanthrope genius'),
 ('handmaids_tale','Рассказ служанки','The Handmaid’s Tale','2017 · антиутопия · Галаад','2017 · dystopia · Gilead'),
 ('scrubs','Клиника','Scrubs','2001 · ситком · молодые врачи','2001 · sitcom · young doctors'),
 ('prison_break','Побег','Prison Break','2005 · триллер · побег из тюрьмы','2005 · thriller · the breakout'),
 ('suits','Форс-мажоры','Suits','2011 · юр-драма · юрист без диплома','2011 · legal · the fraud lawyer'),
 ('you_show','Ты','You','2018 · триллер · обаятельный сталкер','2018 · thriller · the charming stalker'),
 ('doctor_who','Доктор Кто','Doctor Who','1963 · фантастика · Повелитель времени','1963 · sci-fi · the Time Lord'),
 ('lucifer','Люцифер','Lucifer','2016 · дьявол-детектив в Лос-Анджелесе','2016 · the devil solves crime in LA'),
 ('umbrella_academy','Академия «Амбрелла»','The Umbrella Academy','2019 · супергерои-сироты','2019 · superhero misfits'),
 ('oitnb','Оранжевый — хит сезона','Orange Is the New Black','2013 · женская тюрьма','2013 · the women’s prison'),
 ('house_of_cards','Карточный домик','House of Cards','2013 · политика · Фрэнк Андервуд','2013 · politics · Frank Underwood'),
 ('anne_with_e','Энн','Anne with an E','2017 · рыжая сирота на ферме','2017 · the red-haired orphan'),
 ('sense8','Восьмое чувство','Sense8','2015 · восемь связанных разумов','2015 · eight linked minds'),
 ('gossip_girl','Сплетница','Gossip Girl','2007 · элита Манхэттена','2007 · Manhattan elite'),
 ('cobra_kai','Кобра Кай','Cobra Kai','2018 · карате 30 лет спустя','2018 · karate, 30 years later'),
 ('mad_men','Безумцы','Mad Men','2007 · реклама 60-х · Дон Дрейпер','2007 · 60s ad men · Don Draper'),
 ('supernatural','Сверхъестественное','Supernatural','2005 · братья охотятся на нечисть','2005 · brothers hunt monsters'),
 ('friends','Друзья','Friends','1994 · ситком · шестеро в Нью-Йорке','1994 · sitcom · six in New York'),
 ('greys_anatomy','Анатомия страсти','Grey’s Anatomy','2005 · меддрама · бесконечная','2005 · medical · the endless one'),
 ('riverdale','Ривердэйл','Riverdale','2017 · подростки-нуар по комиксу','2017 · teen noir from the comic'),
 ('dexter','Декстер','Dexter','2006 · серийный убийца убийц','2006 · the serial killer of killers'),
 ('better_call_saul','Лучше звоните Солу','Better Call Saul','2015 · приквел · адвокат Джимми','2015 · prequel · lawyer Jimmy'),
 ('modern_family','Американская семейка','Modern Family','2009 · мокьюментари-семья','2009 · the mockumentary family'),
 ('bates_motel','Мотель Бейтсов','Bates Motel','2013 · приквел «Психо»','2013 · the Psycho prequel'),
 ('desperate_housewives','Отчаянные домохозяйки','Desperate Housewives','2004 · тайны Вистерия-лейн','2004 · Wisteria Lane secrets'),
 ('heartstopper','Сердцестопор','Heartstopper','2022 · подростковая квир-романтика','2022 · the teen queer romance'),
 ('white_lotus','Белый лотос','The White Lotus','2021 · сатира на богачей-курортников','2021 · resort-rich satire'),
 ('money_heist','Бумажный дом','Money Heist','2017 · ограбление в красных комбинезонах','2017 · the red-jumpsuit heist'),
 ('big_bang_theory','Теория большого взрыва','The Big Bang Theory','2007 · ситком · физики-гики','2007 · sitcom · the nerd physicists'),
 ('good_doctor','Хороший доктор','The Good Doctor','2017 · хирург с аутизмом','2017 · the autistic surgeon'),
 ('true_detective','Настоящий детектив','True Detective','2014 · антология · два детектива','2014 · anthology · two detectives'),
 ('the_100','Сотня','The 100','2014 · постапокалипсис · подростки','2014 · post-apocalypse · the teens'),
 ('himym','Как я встретил вашу маму','How I Met Your Mother','2005 · ситком · долгая история','2005 · sitcom · the long story'),
 ('the_office','Офис','The Office','2005 · мокьюментари · Дандер-Миффлин','2005 · mockumentary · Dunder Mifflin'),
 ('two_half_men','Два с половиной человека','Two and a Half Men','2003 · ситком · холостяки','2003 · sitcom · the bachelors'),
 ('sex_and_city','Секс в большом городе','Sex and the City','1998 · четыре подруги в Нью-Йорке','1998 · four friends in NY'),
 ('teen_wolf','Волчонок','Teen Wolf','2011 · подросток-оборотень','2011 · the teen werewolf'),
 ('ahs','Американская история ужасов','American Horror Story','2011 · антология ужасов','2011 · the horror anthology'),
 ('outlander','Чужестранка','Outlander','2014 · попаданка в Шотландию XVIII в.','2014 · time-slip to 1700s Scotland'),
 ('sopranos','Клан Сопрано','The Sopranos','1999 · мафия и психотерапия','1999 · the mob and therapy'),
 ('this_is_us','Это мы','This Is Us','2016 · семейная драма-таймлайн','2016 · the family timeline drama'),
 ('true_blood','Настоящая кровь','True Blood','2008 · вампиры юга и синтекровь','2008 · Southern vampires'),
 ('law_and_order','Закон и порядок','Law & Order','1990 · процедурал · преступление и суд','1990 · procedural · crime and court'),
 ('the_wire','Прослушка','The Wire','2002 · HBO · Балтимор без прикрас','2002 · HBO · raw Baltimore'),
 ('fargo','Фарго','Fargo','2014 · антология · криминал по Коэнам','2014 · anthology · Coen-style crime'),
 ('chernobyl','Чернобыль','Chernobyl','2019 · HBO · катастрофа 1986-го','2019 · HBO · the 1986 disaster'),
]


def main():
    dry = '--apply' not in sys.argv
    with open(CATEGORIES_PATH, encoding='utf-8') as f:
        cats = json.load(f)
    c = next((c for c in cats if c.get('id') == 'massive_tv_show'), None)
    if not c:
        print('massive_tv_show NOT FOUND'); sys.exit(1)

    existing_ids = {it.get('id') for it in c.get('items', [])}
    existing_names = {(it.get('name') or '').lower() for it in c.get('items', [])}
    added, skipped = [], []
    for iid, nm, nm_en, ctx, ctx_en in NEW:
        if iid in existing_ids or nm.lower() in existing_names:
            skipped.append(iid); continue
        c['items'].append({'id': iid, 'name': nm, 'name_en': nm_en, 'ctx': ctx, 'ctx_en': ctx_en})
        added.append(iid)

    c['recommended_tournament_size'] = len(c['items'])

    print(f'ADDED: {len(added)}  SKIPPED(existing): {len(skipped)}')
    print(f'TOTAL items now: {len(c["items"])}  ·  recommended_tournament_size = {c["recommended_tournament_size"]}')
    if skipped:
        print('  skipped:', ', '.join(skipped))

    if dry:
        print('\n=== DRY RUN - add --apply ==='); return
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(CATEGORIES_PATH, CATEGORIES_PATH + f'.bak.series_items.{ts}')
    with open(CATEGORIES_PATH, 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)
    print('Saved')


if __name__ == '__main__':
    main()
