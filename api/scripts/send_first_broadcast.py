"""One-shot script: send the first broadcast email via /api/admin/broadcast.

Run on the server (where it can reach the local API + read the admin password
from systemd env). Uses requests for clean JSON handling — no shell escaping
nightmares with embedded HTML.

Usage:
  cd /opt/untitled-pick-game-api
  set -a && source /etc/untitled-pick-game-api.env && set +a
  python3 scripts/send_first_broadcast.py [--dry-run]

By default does a live send. Pass --dry-run to just preview recipients.
"""
import os
import sys
import json
import urllib.request
import urllib.parse

API_BASE = "http://127.0.0.1:8001/api"
DRY_RUN = "--dry-run" in sys.argv

ADMIN_PASS = os.environ.get("UPG_ADMIN_PASS")
if not ADMIN_PASS:
    print("ERROR: UPG_ADMIN_PASS not in env. Run: set -a && source /etc/...env && set +a")
    sys.exit(1)


# ─── EMAIL CONTENT ─────────────────────────────────────────────────

SUBJECT = "Спасибо. И что у нас впереди."

BODY_TEXT = """Привет.

Хочу сказать спасибо — за то, что ты в самой ранней истории Tappetite. Когда ничего не понятно, всё ломается, имени нормального ещё нет.

Сегодня — ровно неделя с того дня (4 мая), как залил первую версию в сеть. За эти шесть дней:

— Появилось имя. Tappetite — игра на «аппетит», немного журнальная, немного дегустационная. С серифным логотипом и тёплой неоновой подписью на главной.

— Заработала почта. Восстановление пароля. Аналитика чтобы я понимал что у юзеров на самом деле происходит.

— Закрылись несколько раундов внешнего аудита — нашли и поправили дыры, переписали архетипы так, чтобы они звучали как про тебя, а не как пересказ твоего выбора.

— Подкрутил онбординг и кучу мелочей по фидбеку.

Это не было бы возможно без твоих наблюдений и подсказок. Каждое «шрифт здесь кривой» или «непонятно зачем» — реально помогало. Спасибо.

Что впереди. Сборка iOS- и Android-приложений, подача в App Store и Google Play. Дальше, если зайдёт, — закрытые комнаты для семьи и друзей: играете в одни турниры, потом смотрите кто с кем совпал, и в чём вы разные. Это то, ради чего всё затевалось.

Если есть возможность — позови ещё одного человека. Только того, кому реально подойдёт. Формат «выбираешь из двух, в финале остаётся один, получаешь свой типаж» — не для всех, и это нормально. Просто если кого-то вспомнишь — дай ему ссылку, потом расскажи мне как зашло.

Ещё раз — спасибо. Это правда важно.

— Uncle
https://isverifiedby.me
"""


# Brand colors (mirror email_templates.py + game.html tokens)
ACCENT = "#B5532E"
TEXT_PRIMARY = "#1A1F36"
TEXT_SECONDARY = "#4A4035"
RULE = "#E5DDD0"
FONT_SERIF = "Didot, 'Bodoni 72', 'Bodoni Moda', Georgia, serif"

def bullet(text):
    """Hanging-indent paragraph with accent-colored em-dash leading."""
    return (
        f'<p style="margin:0 0 14px 0;padding-left:22px;text-indent:-22px;">'
        f'<span style="color:{ACCENT};font-weight:700;">—</span>&nbsp;{text}'
        f'</p>'
    )

BODY_HTML = f"""
<p style="font-family:{FONT_SERIF};font-style:italic;font-size:24px;font-weight:400;color:{TEXT_PRIMARY};margin:0 0 24px 0;line-height:1.2;">
  Привет.
</p>

<p style="margin:0 0 16px 0;">
  Хочу сказать спасибо — за то, что ты в самой ранней истории Tappetite. Когда ничего не понятно, всё ломается, имени нормального ещё нет.
</p>

<p style="margin:0 0 26px 0;">
  Сегодня — ровно неделя с того дня (4 мая), как залил первую версию в сеть. За эти шесть дней:
</p>

{bullet('Появилось имя. <strong>Tappetite</strong> — игра на «аппетит», немного журнальная, немного дегустационная. С серифным логотипом и тёплой неоновой подписью на главной.')}

{bullet('Заработала почта. Восстановление пароля. Аналитика чтобы я понимал что у юзеров на самом деле происходит.')}

{bullet('Закрылись несколько раундов внешнего аудита — нашли и поправили дыры, переписали архетипы так, чтобы они звучали как про тебя, а не как пересказ твоего выбора.')}

<p style="margin:0 0 30px 0;padding-left:22px;text-indent:-22px;">
  <span style="color:{ACCENT};font-weight:700;">—</span>&nbsp;Подкрутил онбординг и кучу мелочей по фидбеку.
</p>

<p style="margin:0 0 30px 0;">
  Это не было бы возможно без твоих наблюдений и подсказок. Каждое «шрифт здесь кривой» или «непонятно зачем» — реально помогало. Спасибо.
</p>

<hr style="border:none;border-top:1px solid {RULE};width:72px;margin:0 auto 30px auto;">

<p style="margin:0 0 22px 0;">
  <strong>Что впереди.</strong> Сборка iOS- и Android-приложений, подача в App Store и Google Play. Дальше, если зайдёт, — закрытые комнаты для семьи и друзей: играете в одни турниры, потом смотрите кто с кем совпал, и в чём вы разные. Это то, ради чего всё затевалось.
</p>

<p style="margin:0 0 0 0;">
  <strong>Если есть возможность — позови ещё одного человека.</strong> Только того, кому реально подойдёт. Формат «выбираешь из двух, в финале остаётся один, получаешь свой типаж» — не для всех, и это нормально. Просто если кого-то вспомнишь — дай ему ссылку, потом расскажи мне как зашло.
</p>

<div style="text-align:center;margin:40px 0 0 0;">
  <hr style="border:none;border-top:1px solid {RULE};width:72px;margin:0 auto 26px auto;">
  <p style="font-family:{FONT_SERIF};font-style:italic;font-size:19px;color:{TEXT_SECONDARY};margin:0 0 30px 0;line-height:1.45;">
    Ещё раз — спасибо.<br>Это правда важно.
  </p>
  <p style="font-family:{FONT_SERIF};font-style:italic;font-size:19px;color:{TEXT_PRIMARY};margin:0 0 8px 0;">
    — Uncle
  </p>
  <p style="margin:0;">
    <a href="https://isverifiedby.me" style="color:{ACCENT};text-decoration:none;font-weight:600;font-size:12px;letter-spacing:0.06em;">isverifiedby.me</a>
  </p>
</div>
"""


# ─── HTTP helpers (using stdlib urllib to avoid extra deps) ─────────

def login():
    """POST /api/admin/login → returns the session cookie string."""
    data = json.dumps({"password": ADMIN_PASS}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/admin/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
        if not body.get("ok"):
            raise SystemExit(f"login failed: {body}")
        # Extract Set-Cookie
        set_cookie = resp.headers.get("Set-Cookie", "")
        # We just need name=value, drop attributes
        cookie = set_cookie.split(";")[0] if set_cookie else ""
        if not cookie:
            raise SystemExit("no Set-Cookie returned from login")
        return cookie


def broadcast(cookie, dry_run):
    """POST /api/admin/broadcast with the email + recipient filter."""
    payload = {
        "subject": SUBJECT,
        "body_text": BODY_TEXT,
        "body_html": BODY_HTML,
        "dry_run": dry_run,
        "exclude_user_ids": [7],  # another_dan / faked@list.ru — known dead
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/admin/broadcast",
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Cookie": cookie,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


# ─── main ──────────────────────────────────────────────────────────

def main():
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE SEND'}")
    print(f"Subject: {SUBJECT}")
    print(f"HTML body length: {len(BODY_HTML)} chars")
    print()
    print("Logging in as admin...")
    cookie = login()
    print(f"  ok, cookie acquired ({len(cookie)} bytes)")
    print()

    if DRY_RUN:
        print("Calling broadcast with dry_run=true ...")
    else:
        print("CALLING LIVE BROADCAST. Pressing GO ...")
    result = broadcast(cookie, dry_run=DRY_RUN)

    if DRY_RUN:
        print(f"Would send to {result['would_send_count']} recipients:")
        for r in result["would_send"]:
            print(f"  - id={r['id']:<3} {r['nickname']:<14} {r['email']}")
        print(f"Skipped {result['skipped_count']}: {[s['nickname'] for s in result['skipped']]}")
    else:
        print(f"SENT: {result['sent_count']}")
        for r in result["sent"]:
            print(f"  ✓ id={r['id']:<3} {r['email']:<35} resend_id={r['resend_id']}")
        if result["failed_count"]:
            print(f"FAILED: {result['failed_count']}")
            for r in result["failed"]:
                print(f"  ✗ id={r['id']:<3} {r['email']:<35} err={r['error']}")
        if result["skipped_count"]:
            print(f"SKIPPED: {result['skipped_count']}")
            for s in result["skipped"]:
                print(f"  - id={s['id']:<3} {s['nickname']:<14} reason={s['reason']}")


if __name__ == "__main__":
    main()
