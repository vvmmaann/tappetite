# Google Play Console — listing fields

Fill in https://play.google.com/console after building first .aab.
Updated 2026-05-10. Previous version had outdated 13+ target audience
(now 16+ for GDPR), no Sign in with Google/Apple, no PostHog/Resend
disclosure. Submitting old text would mismatch Data Safety form.

## Main store listing

| Field | Value | Notes |
|---|---|---|
| App name | Tappetite | 30 chars max. Final brand. |
| Short description | Турниры выбора. Профиль вкуса. (RU) / Tap-tournaments. Taste profile (EN) | 80 chars max each. |
| Full description | (paste from `description-ru.md` / `description-en.md`) | 4000 chars max each. |
| App icon | 512×512 PNG | Use `branding/dist/pwa-512.png` (already correct Tappetite "t" mark). NOT the auto-generated mipmap one — that's foreground-only. |
| Feature graphic | 1024×500 PNG | Required. Cream bg + italic "t" mark + tagline "Профиль вкуса" / "Taste profile". TODO: design (~1 hr in Figma) |
| Phone screenshots | 1080×1920 portrait | At least 2, max 8. See `screenshots-spec.md`. |
| 7-inch tablet screenshots | optional | Skip for v1 (no tablet-specific UX). |
| 10-inch tablet | optional | Skip for v1. |

## App category

- Application type: **Apps** (not Games — we have light gamification but no
  traditional game mechanics)
- Category: **Lifestyle** (matches App Store category for consistency)
- Tags (up to 5): taste, personality, quiz, tournament, lifestyle

## Contact details

| Field | Value |
|---|---|
| Email | support@isverifiedby.me |
| Website | https://isverifiedby.me |
| Privacy policy URL | https://isverifiedby.me/privacy.html |

## Translations

Add **Russian (ru)** alongside default English. Paste corresponding
sections from `description-ru.md`. App is bilingual at runtime — the
store listing in both languages will help discoverability in both
markets.

## Pricing & distribution

- **Free**, available in: Russia + Kazakhstan + EN-speaking countries
  (US, UK, Canada, Australia, Ireland, NZ) initially. Expand after
  first reviews.
- Contains ads: **No**
- In-app purchases: **No** (for v1; potential future paid tier)
- Content rating: see `age-rating.md`. Should come out **Teen / 13+** on
  Google's questionnaire (no violence/profanity/drugs), but our actual
  app policy is **16+** for GDPR data-processing reasons. Document in
  the listing description.
- Designed for families: **No** (not targeting kids)

## Production release setup

| Stage | Track | Notes |
|---|---|---|
| 1 | Internal testing | Up to 100 testers (gmail addresses), no review needed, instant. Use this for first 1-2 weeks of Tappetite testing on real Android devices. |
| 2 | Closed testing (Alpha) | Up to 100 testers per email list. Review takes ~hours. Optional. |
| 3 | Open testing (Beta) | Anyone with link can install. Optional public beta. |
| 4 | Production | Full release. Review takes 1-7 days for first submission. |

Recommended path: Internal → straight to Production once happy. Skip
Closed/Open unless you specifically want broader beta first.

## App content questionnaire

Google asks several content questions before publishing:

| Question | Answer | Notes |
|---|---|---|
| Target audience | **16+** | Matches GDPR data-processing minimum. |
| News app | No | |
| COVID-19 contact tracing | No | |
| Data safety | (see `data-safety.md`) | PostHog/Resend/Google/Apple/Cloudflare disclosed |
| Government app | No | |
| Financial features | No | |
| Health-related | No | |
| Ads | **No** | We do not show ads |
| In-app messaging | No | Friendships are graph relations, no chat |
| User-generated content | **Yes — moderated** | Theme submissions + item submissions go through admin moderation queue. Approval requires bilingual content + validator pass. |
| Permissions justification | INTERNET only | No camera/mic/location/contacts |
| Data deletion request | **Yes — in-app + email** | Profile → Опасная зона + support@isverifiedby.me |

## Bundle size

Capacitor 8 baseline: ~5 MB AAB. Our web assets bundled: ~530 KB
(offline fallback game.html). Total app size on device: ~10-15 MB.
Well under 150 MB AAB limit.

## App signing

Google Play App Signing is **required** for new apps. When you upload
your first .aab, Google asks you to opt-in (default). You keep the
upload key, Google holds the signing key. **Don't lose the upload key
— needed for all future updates.**

```bash
# Generate upload key (one-time, done locally before first .aab build):
keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 \
  -validity 10000 -alias upload
# Save the .jks file securely (1Password / Bitwarden + offline backup
# in two physical locations). Without it you can't ship updates.
# Reference it in android/app/build.gradle signingConfigs.release block.
```

## Specific things our app needs to declare

Because of the work we did in audit rounds 1-5, document these explicitly
when filling the Play Console form (will save back-and-forth with reviewers):

1. **PostHog analytics is opt-in**, opted-out by default until consent
   gesture (welcome / register / login checkbox)
2. **All data deletable** in-app via DELETE /api/me with anonymization
   of residual rows (errors, feedback, challenges)
3. **Granular consent** management lives in Profile → Мои согласия
4. **No ad SDK, no crash SDK** — own backend for both
5. **Bilingual UI** + bilingual store listings
6. **Sign in with Apple offered alongside Google** per Apple rule 4.8 (relevant if Apple version asked about; Google Play doesn't enforce this but it's a nice-to-mention)

## Submission checklist

- [ ] Upload key generated and backed up (TWO secure locations)
- [ ] AAB built with release signing config (`./gradlew bundleRelease`)
- [ ] AAB tested locally with `bundletool` (install on real device)
- [ ] App icon 512×512 ready (cream bg, NOT transparent)
- [ ] Feature graphic 1024×500 ready
- [ ] At least 2 phone screenshots ready (1080×1920 portrait)
- [ ] EN + RU descriptions pasted
- [ ] Data Safety form filled per `data-safety.md`
- [ ] Content rating questionnaire completed
- [ ] Privacy Policy URL set: https://isverifiedby.me/privacy.html
- [ ] Contact email set: support@isverifiedby.me
- [ ] Submit for review
