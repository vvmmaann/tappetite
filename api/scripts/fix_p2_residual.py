# -*- coding: utf-8 -*-
"""Residual P2 fixes after the bulk connector strip: 4 crypto_exchanges
"За этим стоит…" backrefs + 3 absolute/exclusive claims. P2-only, RU+EN,
additive + self-contained, regular dashes.
Run: python3 fix_p2_residual.py [--apply]
"""
import json, shutil, sys
from datetime import datetime
CATEGORIES_PATH = '/opt/untitled-pick-game-api/data/categories.json'

NEW = {
 ('crypto_exchanges','Ранний сигнал'): {
  'p2':"Самая большая доходность в крипте приходит не от биткоина на пике нарратива, а от монеты, которую ты находишь до нарратива. Ты принял риск как плату за потенциал - осознанно, а не случайно. И это честная сделка, если ты понимаешь, что именно покупаешь.",
  'p2_en':"The biggest returns in crypto don't come from buying Bitcoin at the top of a narrative. They come from finding the coin before the narrative forms. You've accepted risk as the price of upside - deliberately, not accidentally. That's a fair deal, as long as you actually know what you're buying.",
 },
 ('crypto_exchanges','Один логин'): {
  'p2':"У тебя системное мышление. Хаотичная инфраструктура ведёт к хаотичным решениям. Один логин, один P&L, одна история сделок - это не просто удобство, это контроль. Ты управляешь капиталом как операционной системой: всё должно быть видно из одной точки.",
  'p2_en':"You think in systems. A chaotic infrastructure leads to chaotic decisions. One login, one P&L, one trade history - that's not just convenience, it's control. You manage capital the way you'd run an operating system: everything visible from a single point.",
 },
 ('crypto_exchanges','По следу'): {
  'p2':"Ты рассуждаешь рационально: в любой сложной области использовать экспертизу других лучше, чем воспроизводить её без фундамента. Ты понимаешь, что новичок с графиком не обгонит трейдера с пятью годами на рынке - и не пытаешься строить такую иллюзию.",
  'p2_en':"Your reasoning is rational: in any complex field, leveraging someone else's skill beats simulating it without the foundation. You understand that a beginner with a chart isn't going to outperform a trader with five years of market experience - and you're not going to pretend otherwise.",
 },
 ('crypto_exchanges','Карта в кармане'): {
  'p2':"У тебя конкретная позиция: ты хочешь, чтобы цифровые активы работали в реальном мире, а не только на графиках. Стейкинг, кэшбэк, карта с лимитами - ты строишь финансовый слой поверх обычного быта, а не параллельную вселенную с отдельными правилами.",
  'p2_en':"You have a specific stance: you want digital assets to work in everyday life, not just on charts. Staking, cashback, a card with spending limits - you're building a financial layer over ordinary life, not a parallel universe with its own separate rules.",
 },
 ('ideal_vacation','Тишина и восстановление'): {
  'p2':"У тебя нет проблемы «нечего делать», у тебя проблема «никогда не останавливаешься». В обычной жизни тебя несёт поток - работа, дела, обязательства, и даже формально свободные часы заняты обязательствами. Отпуск без расписания для тебя - лучший способ дать мозгу шанс просто быть, без целей.",
  'p2_en':"You don't have a \"nothing to do\" problem, you have a \"you never stop\" problem. In ordinary life, the flow carries you - work, things, obligations - and even formally free hours are occupied with commitments. A vacation without a schedule is, for you, the best way to give the brain a chance to just be, without goals.",
 },
 ('what_is_success','Спокойное море'): {
  'p2':"Твоя потребность - ресурсное состояние. Без него тебе сложно радоваться деньгам, путешествиям и признанию. Ты проще откажешься от премии, чем от восьми часов сна. Ты хорошо знаешь: высокая зарплата не лечит выгорание. Здоровье и покой для тебя - база, на которой всё остальное только и держится.",
  'p2_en':"Your need is a state of having resources. Without it, it's hard to enjoy money, travel, or recognition. You'd sooner skip a bonus than eight hours of sleep. You know well: a high salary doesn't cure burnout. For you, health and peace are the foundation everything else stands on.",
 },
 ('literary_hero','Несломленный'): {
  'p2':"Жизнь проверила на прочность. Ты выдержал. Тёмный герой внутри - не культ страдания, а знание: ты уже пережил худшее, и многое после этого кажется мельче. Андердог заставляет доказывать снова и снова. Себя не жалеешь - это было бы слишком скучно.",
  'p2_en':"Life has tested your limits. You held. The dark hero inside isn't a cult of suffering - it's knowing you've survived the worst, and much of what comes after feels smaller. The underdog keeps proving yourself again and again. You don't feel sorry for yourself - that would be too boring.",
 },
}

def replace_p2(text, new_p2):
    if not text: return text
    sep='\n\n' if '\n\n' in text else '\n'
    ps=[p for p in text.split(sep) if p.strip()]
    if len(ps)<2: return text
    ps[1]=new_p2
    return '\n\n'.join(ps)

def main():
    dry='--apply' not in sys.argv
    with open(CATEGORIES_PATH,encoding='utf-8') as f: cats=json.load(f)
    byid={c.get('id'):c for c in cats}
    applied=[]; missing=[]
    for (cid,aname),fields in NEW.items():
        c=byid.get(cid)
        if not c: missing.append(cid); continue
        a=next((x for x in c.get('archetypes',[]) if x.get('name')==aname),None)
        if not a: missing.append(f'{cid}/{aname}'); continue
        a['body']=replace_p2(a.get('body',''),fields['p2'])
        a['body_en']=replace_p2(a.get('body_en',''),fields['p2_en'])
        applied.append(f'  [{cid}] {aname}')
    print(f'RESIDUAL P2 FIXES: {len(applied)}')
    for l in applied: print(l)
    if missing: print('MISSING:',missing)
    if dry:
        print('\n=== DRY RUN - add --apply ==='); return
    ts=datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy(CATEGORIES_PATH, CATEGORIES_PATH+f'.bak.p2_residual.{ts}')
    with open(CATEGORIES_PATH,'w',encoding='utf-8') as f: json.dump(cats,f,ensure_ascii=False,indent=2)
    print('Saved')

if __name__=='__main__': main()
