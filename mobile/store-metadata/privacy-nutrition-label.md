# Apple Privacy Nutrition Label (App Privacy)

Mandatory since Dec 2020. Filled in App Store Connect → App Privacy.
Updated 2026-05-10 to reflect actual code (PostHog, Resend, Sign in with
Apple/Google added). The previous version of this file was inaccurate —
do not reuse old wording.

For each data type, Apple asks 3 things:
1. Is data collected?
2. Is it linked to user identity?
3. Is it used for tracking across other apps/sites?

## Tracking (Apple's specific definition)

Apple defines "tracking" narrowly: linking user/device data from this app
to data from OTHER apps/websites for advertising or measurement, OR sharing
data with data brokers.

Our app: **NO tracking**.
- PostHog is first-party product analytics inside our own org. We don't
  link distinct_id to any external data source.
- We don't have ad SDKs, no fingerprinting, no IDFA usage.
- We don't sell or share data with brokers.

Answer in App Store Connect: "**No, we do not track**" → no IDFA permission
prompt required.

## Data linked to user identity

For each "Yes" below, the answer to "Used for" is the second column.

| Data type | Collected? | Used for | Notes |
|---|---|---|---|
| **Name** (nickname) | Yes | App Functionality | User-chosen, can be changed in profile. |
| **Email Address** | Yes (required for email reg, optional for social) | App Functionality, Customer Support | Used for auth, password reset, optional marketing if user opts in. |
| **User ID** | Yes | App Functionality, Analytics | Internal numeric ID + PostHog distinct_id (only after consent). |
| **Device ID** | Yes (post-consent only) | Analytics | PostHog device_id, in `ph_*` localStorage. Set ONLY after explicit user consent. Wiped on logout/delete. |
| **Other User Content** | Yes | App Functionality, Analytics | Tournament picks, top-3 results, taste archetype derived from picks. |
| **Other User Content (free text)** | Yes | App Functionality, Customer Support | Feedback messages, theme/item submission descriptions. |
| **Customer Support** | Yes | Customer Support | Email-for-reply on feedback (optional). |
| **Crash Data** | Yes | App Functionality | Captured in our own backend `errors` table — error message, stack trace, URL, user-agent. NOT sent to any third-party crash service. Anonymized on account deletion. |
| **Performance Data** | No | — | We do not collect launch times, hang rates, or hardware metrics. |
| **Other Diagnostic Data** | No | — | |
| **Product Interaction (Analytics)** | Yes (post-consent only) | Analytics | PostHog events: app_loaded, screen_open, tournament_start, tournament_completed, registration_completed, login_completed. NO autocapture, NO session recording. Disabled until consent. |
| **Coarse Location** | No | — | We do not request location. |
| **Precise Location** | No | — | |
| **Contacts** | No | — | |
| **Photos / Videos** | No | — | (We use Filesystem plugin to save the share-card PNG to Documents — local only, not uploaded.) |
| **Audio** | No | — | |
| **Browsing History** | No | — | |
| **Search History** | No | — | |
| **Health & Fitness** | No | — | |
| **Financial Info** | No | — | No payments in v1. |
| **Sensitive Info** | No | — | No religion, politics, race, sexuality, biometrics. |
| **Other Data** | No | — | |

## Data NOT linked to user identity

| Data type | Collected? | Used for | Notes |
|---|---|---|---|
| **Diagnostic / Performance / Crash (aggregate)** | No | — | Crash data is linked (above), no separate anonymous channel. |

## "Used for" — full purpose mapping (for Apple's checkboxes)

For each data type marked "Yes", Apple asks which purposes apply. Tick:

- ☑ **App Functionality** — auth, results storage, social features
- ☑ **Analytics** — PostHog events + linked distinct_id (post-consent only)
- ☑ **Customer Support** — feedback messages, support emails
- ☐ **Product Personalization** — we don't personalize ad-style; results
  shown back are user's own. Recommendation engine on our roadmap will
  flip this to ☑.
- ☐ **Developer's Advertising or Marketing** — we send transactional and
  (post-opt-in) newsletter emails through Resend. Apple defines this
  category narrowly as "user data used to deliver ads"; transactional
  email + opt-in newsletter is "Customer Support" / "App Functionality".
  Re-evaluate if we ever push promo screens inside the app.
- ☐ **Third-Party Advertising** — none.
- ☐ **Other Purposes** — none.

## Third-party processors (disclose-but-not-tracking)

These processors handle our user data for us. They are NOT third-party
tracking under Apple's definition because they don't combine our data
with data from other apps/sites for advertising:

| Processor | Role | Data flow | Disclosed in privacy.html §04 |
|---|---|---|---|
| PostHog (EU) | Product analytics | Anonymous events + distinct_id (post-consent only) | ✓ |
| Resend (US) | Transactional email | Email address + body of password reset / newsletter | ✓ |
| Google | OAuth provider | Sign-in only; we receive ID token + email | ✓ |
| Apple | OAuth provider | Sign-in only; we receive ID token + email (or relay) | ✓ |
| Hosting (EU) | Server infrastructure | Active database | ✓ |
| Cloudflare | CDN/DNS | HTTP request headers transit (no decryption) | ✓ |

## Data Retention

- Account + linked data (results, friends, achievements): until user
  deletes the account; backups up to 30 days.
- Sessions: 30 days inactivity → expire.
- Error logs: 90 days, then deleted.
- PostHog events: up to 7 years (per PostHog policy); link to account
  severed on account deletion via `posthog.reset(true)`.
- Database backups: 30 days.
- Consent audit log: while account exists, deleted with it (CASCADE).

## Privacy Policy URL

```
https://isverifiedby.me/privacy.html
```

## Account Deletion confirmation (App Store requirement since June 2022)

✅ Implemented. User flow: Profile → Опасная зона → "Удалить аккаунт
навсегда" → confirmation prompts → DELETE /api/me. Server response wipes
account, anonymizes residual rows (errors, feedback, challenges), and
client-side `revokePostHogConsent()` severs the PostHog identity link
including device_id. No customer support contact required to delete.

## Sign in with Apple (App Store rule 4.8)

✅ Offered. If we offer Google / Facebook / etc. social sign-in we MUST
also offer Sign in with Apple (rule 4.8 since iOS 13). We do — both via
the @capgo/capacitor-social-login plugin with a single consent gate.

## What if Apple asks "Do you process children's data"?

Answer: **No, app is intended for users 16+**. Privacy.html §09 documents
this. We do not have age verification beyond the registration prompt.
If Apple wants COPPA-tier safeguards, we'd need separate kids-mode logic.
