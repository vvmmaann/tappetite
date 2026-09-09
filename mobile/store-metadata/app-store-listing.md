# Apple App Store Connect — listing fields

Fill in https://appstoreconnect.apple.com after producing the first signed
.ipa via Codemagic CI. Updated 2026-05-10 to match shipped behaviour.

## App information

| Field | Value | Notes |
|---|---|---|
| App name | Tappetite | 30 chars max. Final brand decision locked. |
| Subtitle (EN) | Tap-tournaments. Taste profile. | 30 chars max. |
| Subtitle (RU) | Турниры вкуса. Профиль. | 30 chars max. |
| Bundle ID | me.isverifiedby.pickgame | Register first in Apple Developer portal under Identifiers. Bundle ID stays as-is — changing later breaks user devices. |
| SKU | tappetite-ios-001 | Internal identifier, anything unique within the team. |
| Primary category | Lifestyle | Personal-taste + social-comparison framing. |
| Secondary category | Entertainment | |
| Content rights | I do not have third-party content rights | We use names of public figures, films, brands etc. as choice-reference points only — no copyrighted media is displayed. Apple typically accepts this for "discussion" / "reference" apps; rights-holder takedowns honoured via support@. |
| Age rating | 16+ | GDPR requires consent at 16+ for personal-data processing without parental consent. Privacy.html §09 documents this. Even though there's no violence/profanity content, the data-processing aspect drives the rating. |

## Localizations

Add **two** localizations: Russian (primary) + English.

- For each, paste from `description-ru.md` / `description-en.md`
- Subtitle, promotional text, description, keywords (per-locale)
- App Store screenshots can also be localized — recommended

## Keywords (App Store: 100 chars max, comma-separated, no spaces around commas)

**EN:**
```
taste,quiz,tournament,bracket,pick,personality,profile,vibe,aesthetic,friends
```
(76 chars)

**RU:** (Apple supports Cyrillic keywords for ru locale)
```
вкус,турнир,выбор,тест,характер,личность,эстетика,вайб,друзья,сравнение
```
(72 chars)

## Pricing & availability

- Tier: Free
- Available in: Russia + Kazakhstan + English-speaking countries initially
  (US, UK, Canada, Australia, Ireland, NZ). Add more after first reviews.
- Pre-orders: No
- Distribution: App Store + (optionally later) TestFlight beta program

## App Privacy (Privacy Nutrition Label)

See `privacy-nutrition-label.md` for the structured answers to copy into
the App Privacy section. Mandatory section since Dec 2020.

## App Review Information

| Field | Value |
|---|---|
| Sign-in required | No (works as guest); optional account via email/password OR Sign in with Apple OR Sign in with Google |
| Demo account | Pre-create `apple_review@isverifiedby.me` / password `ReviewerDemo2026!` with 3-4 saved results so reviewer sees a populated profile. Document in notes-to-reviewer. |
| Notes for reviewer | See `apple-review-notes.md` |
| Contact email | support@isverifiedby.me |
| Phone number | (optional but Apple may call for clarification — provide founder's number) |

## In-App Purchases / Subscriptions

None for v1. Future paid tier (premium personality reports, room-creation
limits, etc.) requires StoreKit + Apple's 30%/15% commission acceptance.
Configure here when ready.

## App Privacy Policy URL

```
https://isverifiedby.me/privacy.html
```

Live since 2026-05-10. Includes processor table (PostHog, Resend, Google,
Apple, hosting, Cloudflare), retention schedule, M&A clause, granular
consent management description.

## Terms of Use (EULA) URL

```
https://isverifiedby.me/terms.html
```

Includes anonymized-data licence (§04.5) and standard liability/usage rules.

## Build settings (Xcode project)

- **Deployment target**: iOS 14.0 (Capacitor 8 minimum)
- **Devices**: iPhone + iPad (universal). iPad uses portrait-only by default.
- **Orientations**: Portrait only (iPhone), all (iPad) — set in Info.plist
- **Bundle Display Name**: Tappetite
- **Bundle Version (CFBundleVersion)**: increment for each TestFlight upload (1, 2, 3...)
- **Marketing Version (CFBundleShortVersionString)**: 1.0.0 for first launch
- **Capabilities to enable in Apple Developer**:
  - Sign in with Apple ✓ (we use it)
  - Push Notifications: NOT for v1
  - Associated Domains: NOT for v1 (no universal links yet)
- **Signing**: Automatic (Codemagic) once Apple Dev account is provisioned

## Capacitor + WebKit settings already locked

- `limitsNavigationsToAppBoundDomains: true` (capacitor.config.json)
- `WKAppBoundDomains` includes `isverifiedby.me` + `www.isverifiedby.me` (Info.plist)
- `ITSAppUsesNonExemptEncryption: false` (export-compliance auto-pass)
- `LSApplicationCategoryType: public.app-category.lifestyle`
- Status bar style: DEFAULT (light bg → dark text)
- Splash background: `#FAF6F0` (cream); auto-hide after 1500ms

## Screenshot specs (mandatory for App Store submission)

iPhone 6.7" Display (iPhone 16 Pro Max, 17 Pro Max): 1290 × 2796 portrait
- Required: minimum 1, recommended 4-6, max 10
iPhone 6.5" Display (iPhone 11 Pro Max, XS Max): 1242 × 2688 portrait OR 1284 × 2778
- Required if you want to support older devices
iPad Pro 12.9" (3rd-6th gen): 2048 × 2732 portrait OR landscape
- Required ONLY if app is iPad-compatible

Take from real device or Xcode simulator. See `screenshots-shotlist.md`
(to be created) for what to capture.

## Submission checklist

- [ ] Demo account provisioned + login tested
- [ ] All 5 screenshot sizes uploaded per locale
- [ ] App icon 1024×1024 (no transparency, no rounded corners — Apple does the rounding)
- [ ] App preview videos (optional, recommended for paid tier later)
- [ ] What's New text for v1.0.0 (free-form, ~4000 chars; for v1 just say "First release")
- [ ] Reviewer notes paste from `apple-review-notes.md`
- [ ] All localizations have title/subtitle/description/keywords
- [ ] Privacy Nutrition Labels filled (App Privacy section)
- [ ] Pricing + availability set
