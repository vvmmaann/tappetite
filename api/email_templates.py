"""Email body templates for transactional sends.

Conventions:
  - All templates return {subject, html, text} dicts
  - Single-language per email (caller decides lang via Accept-Language or
    explicit override). Default lang = 'ru' (our predominantly-Russian audience).
  - Brand: Tappetite (cream #FAF6F0 background, serif wordmark in accent
    #B5532E, primary CTA in same accent)
  - HTML uses inline styles only (Gmail/Outlook strip <style> blocks)
  - Fonts use SYSTEM fallbacks only — most email clients don't load Google
    Fonts. Wordmark uses Didot/Bodoni 72 (macOS) → Georgia (universal). Body
    uses Helvetica/Arial. Two families max for visual cohesion.
  - Plaintext fallback always provided (improves deliverability + accessibility)

Functions:
  password_reset_email(reset_url, nickname='', lang='ru')
"""
import html as _html
from typing import Optional

# Brand color tokens (mirror game.html CSS tokens)
CREAM_BG = "#FAF6F0"
CARD_BG = "#FFFCF7"
RULE = "#E5DDD0"
TEXT_PRIMARY = "#1A1F36"
TEXT_TERTIARY = "#6B5C4A"
TEXT_MUTED = "#8A7A6A"
ACCENT = "#B5532E"
BRAND_DOMAIN = "isverifiedby.me"

# Font stacks. Wordmark uses Didot/Bodoni from macOS for the closest match
# to our brand serif (Apple Mail will render these correctly). Falls back
# to Georgia (universal) on Windows/Android/Outlook. Body text uses safe
# sans-serif everywhere for max consistency.
FONT_WORDMARK = "Didot, 'Bodoni 72', 'Bodoni Moda', Georgia, 'Times New Roman', serif"
FONT_BODY = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def password_reset_email(reset_url: str,
                          nickname: Optional[str] = None,
                          lang: str = "ru") -> dict:
    """Render the password-reset email in the requested language.

    Args:
      reset_url: full HTTPS URL the user clicks, e.g.
                 https://isverifiedby.me/#reset=abc123-token
                 (audit-10 P1: fragment, not query — secret stays
                 client-side only, never reaches server logs)
      nickname: optional username; if present, used in greeting line
      lang: 'ru' or 'en'. Defaults to 'ru'. Anything else → 'ru'.

    Returns:
      {subject, html, text} dict ready for mailer.send_email()
    """
    lang = (lang or "ru").lower()
    if lang not in ("ru", "en"):
        lang = "ru"

    # Audit M10: HTML-escape nickname before inlining into the email body.
    # Today the server's NICK_RE strips to [A-Za-z0-9_.-] so injection is
    # already blocked, but this is defence in depth in case validation ever
    # loosens (e.g. allowing emoji glyph). Two forms: nick_clean (plain,
    # for greeting line shared with text/plain) and nick_html (escaped,
    # used wherever we know we're inlining into HTML).
    nick_clean = (nickname or "").strip()
    nick_html = _html.escape(nick_clean, quote=True)

    # greeting_html = HTML-safe (escaped nickname); greeting_text = plain
    if lang == "ru":
        greeting_html = f"Привет, {nick_html}!" if nick_html else "Привет!"
        greeting_text = f"Привет, {nick_clean}!" if nick_clean else "Привет!"
        subject = "Сброс пароля · Tappetite"
        eyebrow_label = "сброс пароля"
        intro = ("Кто-то (наверное, ты) запросил сброс пароля для аккаунта "
                 "Tappetite. Нажми кнопку, чтобы задать новый. Ссылка действует "
                 "<strong>1 час</strong>.")
        cta_text = "Восстановить пароль"
        fallback_label = "Если кнопка не работает — скопируй ссылку в браузер:"
        ignore_note = ("Если ты не запрашивал сброс — просто проигнорируй это "
                       "письмо. Твой пароль не изменится.")
        text_intro = ("Кто-то (наверное, ты) запросил сброс пароля для "
                      "аккаунта Tappetite.\n"
                      "Перейди по ссылке, чтобы задать новый пароль "
                      "(действует 1 час):")
        text_ignore = ("Если ты не запрашивал — просто проигнорируй это письмо.\n"
                       "Твой пароль не изменится.")
    else:  # en
        greeting_html = f"Hi {nick_html}," if nick_html else "Hi,"
        greeting_text = f"Hi {nick_clean}," if nick_clean else "Hi,"
        subject = "Password reset · Tappetite"
        eyebrow_label = "password reset"
        intro = ("Someone (probably you) requested a password reset for your "
                 "Tappetite account. Click the button to set a new one. The "
                 "link is valid for <strong>1 hour</strong>.")
        cta_text = "Reset password"
        fallback_label = "If the button doesn't work, copy this link into your browser:"
        ignore_note = ("If you didn't request this, just ignore this email. "
                       "Your password won't change.")
        text_intro = ("Someone (probably you) requested a password reset for "
                      "your Tappetite account.\n"
                      "Click the link to set a new password (valid for 1 hour):")
        text_ignore = ("If you didn't request this, just ignore this email.\n"
                       "Your password won't change.")

    # Single-language HTML. Table-based layout for max email-client
    # compatibility (Outlook still ignores flexbox/grid as of 2026).
    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:{CREAM_BG};font-family:{FONT_BODY};color:{TEXT_PRIMARY};-webkit-font-smoothing:antialiased;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{CREAM_BG};padding:40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="520" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;background:{CARD_BG};border:1px solid {RULE};border-radius:14px;padding:42px 38px;">
          <tr>
            <td style="text-align:center;padding-bottom:32px;">
              <div style="font-family:{FONT_WORDMARK};font-size:38px;font-weight:400;color:{ACCENT};letter-spacing:0.005em;line-height:1;">tappetite</div>
              <div style="margin-top:12px;font-family:{FONT_BODY};font-size:10px;font-weight:600;color:{TEXT_MUTED};letter-spacing:0.22em;text-transform:uppercase;">{eyebrow_label}</div>
            </td>
          </tr>
          <tr>
            <td style="font-family:{FONT_BODY};font-size:15px;line-height:1.6;color:{TEXT_PRIMARY};">

              <p style="margin:0 0 16px 0;">{greeting_html}</p>
              <p style="margin:0 0 26px 0;">{intro}</p>

              <p style="margin:0 0 28px 0;text-align:center;">
                <a href="{reset_url}" style="display:inline-block;background:{ACCENT};color:{CREAM_BG};text-decoration:none;padding:14px 36px;border-radius:100px;font-weight:600;font-size:14px;letter-spacing:0.04em;font-family:{FONT_BODY};">{cta_text}</a>
              </p>

              <p style="margin:0 0 8px 0;font-size:13px;color:{TEXT_TERTIARY};">{fallback_label}</p>
              <p style="margin:0 0 26px 0;font-size:12px;color:{TEXT_TERTIARY};word-break:break-all;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;">{reset_url}</p>

              <p style="margin:0;font-size:13px;color:{TEXT_TERTIARY};">{ignore_note}</p>

            </td>
          </tr>
        </table>
        <p style="margin:18px 0 0 0;font-family:{FONT_BODY};font-size:10px;color:{TEXT_MUTED};letter-spacing:0.18em;text-transform:uppercase;font-weight:600;">tappetite · {BRAND_DOMAIN}</p>
      </td>
    </tr>
  </table>
</body>
</html>"""

    # Plaintext fallback (single language, matches HTML lang)
    text = f"""{eyebrow_label.upper()}
{'=' * len(eyebrow_label)}

{greeting_text}

{text_intro}

{reset_url}

{text_ignore}

--
tappetite · {BRAND_DOMAIN}
"""

    return {"subject": subject, "html": html, "text": text}


def broadcast_email(subject: str, body_html: str, body_text: str) -> dict:
    """Wrap a custom message body in the branded Tappetite email layout.

    Used by admin broadcasts (announcements / updates / personal letters).
    Brand chrome (wordmark header, footer line) matches password_reset_email
    so all our outbound mail looks consistent.

    Args:
      subject: subject line shown in inbox. We HTML-escape it before inlining
               into <title> (audit H8 — defence in depth even though it's
               admin-only, in case a moderator account is ever compromised).
               Newlines/CRs are stripped to prevent SMTP-header injection.
      body_html: raw HTML for the message body. Inserted as-is into the card.
                 Caller (admin UI) is trusted; if the admin endpoint is ever
                 exposed beyond authenticated owners, sanitize this with
                 bleach or similar before passing in.
      body_text: plaintext fallback. Sent as `text` to email clients that don't
                 render HTML (and improves deliverability).

    Returns:
      {subject, html, text} dict ready for mailer.send_email()
    """
    # Sanitize subject: strip control chars (newline/CR break SMTP headers
    # → header injection) and HTML-escape for safe inlining into <title>.
    safe_subject_raw = "".join(c for c in (subject or "") if ord(c) >= 0x20)
    safe_subject = _html.escape(safe_subject_raw, quote=True)
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_subject}</title>
</head>
<body style="margin:0;padding:0;background:{CREAM_BG};font-family:{FONT_BODY};color:{TEXT_PRIMARY};-webkit-font-smoothing:antialiased;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{CREAM_BG};padding:40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;background:{CARD_BG};border:1px solid {RULE};border-radius:14px;padding:42px 38px;">
          <tr>
            <td style="text-align:center;padding-bottom:32px;">
              <div style="font-family:{FONT_WORDMARK};font-size:38px;font-weight:400;color:{ACCENT};letter-spacing:0.005em;line-height:1;">tappetite</div>
            </td>
          </tr>
          <tr>
            <td style="font-family:{FONT_BODY};font-size:15px;line-height:1.65;color:{TEXT_PRIMARY};">
{body_html}
            </td>
          </tr>
        </table>
        <p style="margin:18px 0 0 0;font-family:{FONT_BODY};font-size:10px;color:{TEXT_MUTED};letter-spacing:0.18em;text-transform:uppercase;font-weight:600;">tappetite · {BRAND_DOMAIN}</p>
      </td>
    </tr>
  </table>
</body>
</html>"""

    text = f"""{body_text}

--
tappetite · {BRAND_DOMAIN}
"""

    # SMTP subject header: control chars stripped (CR/LF prevent header
    # injection) but NOT HTML-escaped — recipient's mail client renders
    # the header as plain text.
    return {"subject": safe_subject_raw, "html": html, "text": text}


# ─── CLI preview (run module directly to see the rendered HTML) ─────
if __name__ == "__main__":
    import sys
    nickname = sys.argv[1] if len(sys.argv) > 1 else None
    lang = sys.argv[2] if len(sys.argv) > 2 else "ru"
    out = password_reset_email(
        # Audit-10 P1: production reset links use #reset= (URL fragment)
        # so the bearer token never reaches HTTP server logs. Keep the
        # preview helper consistent so anyone copy-pasting from here gets
        # the right pattern.
        "https://isverifiedby.me/#reset=test-token-abc123",
        nickname=nickname,
        lang=lang,
    )
    print(f"Lang: {lang}")
    print(f"Subject: {out['subject']}")
    print(f"HTML length: {len(out['html'])} chars")
    print(f"Text length: {len(out['text'])} chars")
    print()
    print("=== TEXT ===")
    print(out["text"])
