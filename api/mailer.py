"""Transactional email wrapper using Resend.

This is the transport layer. Templates and bilingual wording for
verification / password-reset flows live in their respective endpoints
in main.py (added in chunks 5 and 6).

Why Resend (not SMTP / SendGrid / Mailgun):
  - Generous free tier: 3000/mo, 100/day, no credit card required
  - Modern HTTP API (no SMTP wrangling)
  - Y Combinator backed, good reputation
  - Already verified domain isverifiedby.me with DKIM/SPF/DMARC

Environment:
  RESEND_API_KEY: Resend API key (required)
    Set in /etc/untitled-pick-game-api.env on the production server.
    Loaded via systemd EnvironmentFile= directive.

Usage:
  from mailer import send_email, EmailSendError

  try:
      result = send_email(
          to="user@example.com",
          subject="Подтверди почту",
          html="<p>Привет!</p>",
          text="Привет!",  # plaintext fallback recommended for deliverability
      )
      log.info("sent email id=%s", result["id"])
  except EmailSendError as e:
      log.error("email failed: %s", e)
      # caller decides: retry later, surface to user, queue, etc.

CLI self-test:
  python3 mailer.py recipient@example.com
"""
import os
import time
import logging
from typing import Optional

import httpx

log = logging.getLogger(__name__)

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()
RESEND_API_URL = "https://api.resend.com/emails"

# Default sender. Recipients see this string in their "From:" column.
# Format: "Display Name <email@domain>".
# Brand name: Tappetite (play on "appetite" — double "p", "-ite" ending).
# Local part `tappetite` matches the brand. Domain stays isverifiedby.me
# until/unless we register tappetite.com (planned post-launch).
DEFAULT_FROM = "Tappetite <tappetite@isverifiedby.me>"


class EmailSendError(Exception):
    """Raised when Resend rejects the request or all retries are exhausted.

    Caller should treat this as a transient operational failure (log + maybe
    retry from a queue), NOT as a programming error. Email infra is fragile
    by nature — Resend can be down, rate-limited, etc.
    """
    pass


def send_email(
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None,
    from_addr: Optional[str] = None,
    reply_to: Optional[str] = None,
    timeout: float = 10.0,
    retries: int = 2,
) -> dict:
    """Send a transactional email via Resend.

    Args:
      to: recipient email address
      subject: subject line (plain text, no HTML)
      html: HTML body. Resend extracts a plaintext fallback from this if
            `text` is not provided, but explicit `text` is recommended for
            deliverability (some spam filters ding HTML-only emails).
      text: optional plaintext fallback
      from_addr: override the default From header
      reply_to: optional Reply-To header (e.g. "support@isverifiedby.me")
      timeout: per-attempt HTTP timeout in seconds
      retries: number of retry attempts on transient failures (5xx, 429,
               network errors). Total attempts = retries + 1.
               Backoff is exponential: 1s, 2s, 4s.

    Returns:
      Resend response dict, e.g. {"id": "abc-123-..."}. The `id` can be used
      later to query delivery status via Resend's API or webhooks.

    Raises:
      EmailSendError on:
        - missing RESEND_API_KEY
        - 401 Unauthorized (bad key — won't get better with retries)
        - 422 validation error (malformed payload — won't get better)
        - other 4xx (don't retry)
        - all retries exhausted on 5xx / 429 / network
    """
    if not RESEND_API_KEY:
        raise EmailSendError(
            "RESEND_API_KEY env var not set. "
            "Add it to /etc/untitled-pick-game-api.env and restart the service."
        )

    payload: dict = {
        "from": from_addr or DEFAULT_FROM,
        "to": to,
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    if reply_to:
        payload["reply_to"] = reply_to

    last_err: Optional[str] = None
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.post(
                    RESEND_API_URL,
                    headers={
                        "Authorization": f"Bearer {RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

            if r.status_code == 200:
                data = r.json()
                log.info(
                    "email_sent id=%s to=%s subject=%r attempt=%d/%d",
                    data.get("id"), to, subject, attempt + 1, retries + 1,
                )
                return data

            # Permanent failures — no retry
            if r.status_code == 401:
                raise EmailSendError(
                    "Resend rejected API key (401 Unauthorized). "
                    "Key may be revoked or wrong."
                )
            if r.status_code == 422:
                raise EmailSendError(
                    f"Resend validation error (422): {r.text[:300]}"
                )
            if 400 <= r.status_code < 500 and r.status_code != 429:
                raise EmailSendError(
                    f"Resend HTTP {r.status_code}: {r.text[:300]}"
                )

            # Transient failures (5xx, 429) — retry with exp backoff
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
            log.warning(
                "email_transient_fail attempt=%d/%d to=%s err=%s",
                attempt + 1, retries + 1, to, last_err,
            )

        except httpx.RequestError as e:
            # Network-layer failure (DNS, connect timeout, read timeout, ...)
            last_err = f"network: {type(e).__name__}: {e}"
            log.warning(
                "email_network_fail attempt=%d/%d to=%s err=%s",
                attempt + 1, retries + 1, to, last_err,
            )

        if attempt < retries:
            time.sleep(2 ** attempt)  # 1s, 2s, 4s

    raise EmailSendError(
        f"Failed after {retries + 1} attempts: {last_err}"
    )


# ─── CLI self-test ────────────────────────────────────────────────────
# Run on the server to verify end-to-end sending works:
#   python3 /opt/untitled-pick-game-api/mailer.py recipient@example.com
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if len(sys.argv) < 2:
        print("usage: python3 mailer.py <recipient-email>")
        print("requires: RESEND_API_KEY env var")
        sys.exit(1)

    recipient = sys.argv[1]
    print(f"sending test email to {recipient} ...")
    try:
        result = send_email(
            to=recipient,
            subject="mailer.py self-test",
            html=(
                "<p>This is a test from <code>mailer.py</code>.</p>"
                "<p>If you got this, the sending pipeline works end-to-end:</p>"
                "<ul>"
                "<li>RESEND_API_KEY is loaded from env</li>"
                "<li>Resend API accepted the request</li>"
                "<li>DKIM signed the message</li>"
                "<li>Recipient's mail server accepted the delivery</li>"
                "</ul>"
            ),
            text=(
                "This is a test from mailer.py.\n"
                "If you got this, the sending pipeline works end-to-end:\n"
                "  - RESEND_API_KEY is loaded from env\n"
                "  - Resend API accepted the request\n"
                "  - DKIM signed the message\n"
                "  - Recipient's mail server accepted the delivery\n"
            ),
        )
        print(f"OK: sent id={result.get('id')}")
    except EmailSendError as e:
        print(f"FAIL: {e}")
        sys.exit(2)
