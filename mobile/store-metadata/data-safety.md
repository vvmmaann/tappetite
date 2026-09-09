# Google Play Data Safety form

Mandatory since July 2022. Filled in Play Console → App content → Data safety.
Updated 2026-05-10. Previous version was inaccurate — claimed "no third
parties, no analytics, no social login" while we now have PostHog, Resend,
Sign in with Google + Sign in with Apple. Submitting old text would
trigger a Play Store rejection or post-launch enforcement action.

## Section 1: Data collection and security

| Question | Answer |
|---|---|
| Does your app collect or share any required user data types? | **Yes** |
| Is all data collected encrypted in transit? | **Yes** (HTTPS/TLS end-to-end via Cloudflare) |
| Do you provide a way for users to request data deletion? | **Yes** (in-app: Profile → Опасная зона → Удалить аккаунт. Server endpoint: `DELETE /api/me`. Atomic transaction wipes account + anonymizes residual rows.) |

## Section 2: Data types

For each data type below, indicate **Collected**, **Shared**,
**Optional/Required**, **Encrypted**, **Purpose**.

### Personal info
| Data | Collected | Shared | Optional? | Purpose |
|---|---|---|---|---|
| Name | ✅ | ❌ | Required (nickname is mandatory) | App functionality |
| Email address | ✅ | ❌ | Optional (only required for email reg; social-auth users may have email auto-filled from token) | Account management, customer support, optional marketing if user opts in |
| User IDs | ✅ | Shared with PostHog (anonymized analytics, post-consent) | Required | App functionality, Analytics |
| Address | ❌ | | | |
| Phone number | ❌ | | | |
| Race and ethnicity | ❌ | | | |
| Political or religious beliefs | ❌ | | | |
| Sexual orientation | ❌ | | | |
| Other personal info | ❌ | | | |

### Financial info
**None collected.**

### Health and fitness
**None collected.**

### Messages
**None collected** (friendships are graph relations, not message threads).

### Photos and videos
**None collected** (Filesystem plugin saves the share-card PNG locally to user's Documents — never uploaded back).

### Audio files
**None collected.**

### Files and docs
**None collected** (the JSON export endpoint outputs to the user's device only).

### Calendar
**None.**

### Contacts
**None.**

### Location
**None** (no Coarse, no Precise — we don't request location permission).

### App activity
| Data | Collected | Shared | Optional? | Purpose |
|---|---|---|---|---|
| App interactions (tournament picks, results) | ✅ | Shared with PostHog (event names + counts, no individual pick details, post-consent) | Required (after starting tournament) | App functionality, Analytics |
| In-app search history | ❌ | | | |
| Installed apps | ❌ | | | |
| Other user-generated content (theme/item submissions, feedback messages) | ✅ | ❌ | Optional | App functionality, customer support |
| Other actions (achievements, friend requests) | ✅ | ❌ | Required | App functionality |

### Web browsing
**None collected.**

### App info and performance
| Data | Collected | Shared | Optional? | Purpose |
|---|---|---|---|---|
| Crash logs | ✅ | ❌ | Required (auto-collected, server-side only, our own `errors` table — no Sentry/Crashlytics) | App debugging |
| Diagnostics | ❌ | | | |
| Other app performance | ❌ | | | |

### Device or other IDs
| Data | Collected | Shared | Optional? | Purpose |
|---|---|---|---|---|
| Device or other IDs | ✅ (PostHog device_id, post-consent only, in `ph_*` localStorage) | Shared with PostHog | Optional (revoked on logout/delete via `posthog.reset(true)`) | Analytics |

We do NOT read IMEI, ANDROID_ID, advertising ID (AAID), or do device
fingerprinting. PostHog's device_id is its own randomly-generated value
scoped to the app, not a system identifier.

## Section 3: Security practices

| Question | Answer |
|---|---|
| Data is encrypted in transit? | **Yes** (TLS 1.2+ via Cloudflare; backend behind nginx with HSTS header) |
| Users can request data deletion? | **Yes** (in-app + via support@isverifiedby.me) |
| Committed to Google Play Families Policy? | **Not applicable** (app is for users 16+ per GDPR) |
| Independent security review? | **No** (we run rigorous internal audits — 5 rounds documented — but no external paid audit yet) |

## Section 4: Data sharing with third parties

**Yes, we share limited data with the following processors.** None of them
are advertising networks or data brokers. All disclosed in our privacy
policy at https://isverifiedby.me/privacy.html §04:

| Processor | Country | What's shared | Purpose | When |
|---|---|---|---|---|
| **PostHog** | EU (eu.i.posthog.com) | Anonymous events + distinct_id (hashed user ID if signed in) + device_id | Product analytics | Only after explicit user consent |
| **Resend** | USA (Delaware) | Email address + transactional email body | Email delivery (password reset, opt-in newsletters) | When user requests password reset or opts into marketing |
| **Google** | USA / EU | Account email + Google ID | OAuth sign-in only | Only if user chooses Sign in with Google |
| **Apple** | USA / EU | Account email (real or relay) + Apple ID | OAuth sign-in only | Only if user chooses Sign in with Apple |
| **Cloudflare** | USA (with EU PoPs) | HTTP request headers (IP, user-agent) | CDN, DDoS mitigation, DNS | Always (TLS-terminated; doesn't see request bodies) |
| **Hosting provider** | EU | Active database | Server infrastructure | Always |

## Section 5: User control over data

| Capability | Available? | Where |
|---|---|---|
| View data we hold | ✅ | Profile → Мои данные → "скачать мои данные" — JSON export |
| Delete account | ✅ | Profile → Опасная зона → "удалить аккаунт навсегда" |
| Manage marketing consents | ✅ | Profile → Мои согласия → toggle email/push marketing |
| Withdraw analytics consent | ✅ | Logout (revokes PostHog identity + device_id) or delete account |
| Change password | ✅ | Profile or "Forgot password" flow |

## Recap statement (for the form's "About data safety" section)

```
Tappetite collects what's needed to run the app: your nickname (required),
your email (optional unless you sign up with email), and your tournament
picks and results (so you can see your history).

We use PostHog (EU) for product analytics ONLY after you explicitly
consent — opted out by default. We use Resend (US) to send password-reset
emails and (only if you opt in) marketing newsletters. Sign in with
Google / Apple is optional and only sees your sign-in event.

You can manage every consent granularly in your profile, download all
your data with one tap, or permanently delete your account in-app.
Full disclosure: https://isverifiedby.me/privacy.html
```
