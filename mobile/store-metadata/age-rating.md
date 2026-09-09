# Age rating — both stores

**Updated 2026-05-10.** Originally targeted 4+/Everyone, but during the
GDPR compliance pass we set the policy minimum at **16+** (data processing
without parental consent requirement). Age content is still 4+/Everyone,
but the **data-processing minimum age is 16** — both must be communicated.

Practically: store rating questionnaires care about CONTENT (which is
benign), so they'll output 4+/Everyone naturally. Our privacy policy +
welcome screen state the 16+ requirement separately.

## Apple App Store rating questionnaire (4+ target)

Apple's form has ~20 yes/no questions. Answer **No** to all except:

| Question | Answer | Why |
|---|---|---|
| Cartoon or fantasy violence | **No** | We're a tap-tournament, no violence depicted |
| Realistic violence | **No** | Same |
| Prolonged graphic or sadistic realistic violence | **No** | |
| Profanity or crude humor | **No** | Editorial archetype text is curated, no profanity |
| Mature/suggestive themes | **No (with note)** | Some categories ask about dating preferences ("digital red flag", "your flirt style") but content is character-of-user not sexual content |
| Horror/fear themes | **No** | |
| Medical/treatment information | **No** | |
| Alcohol, tobacco, or drug use or references | **No** | |
| Gambling | **No** | |
| Sexual content or nudity | **No** | |
| Graphic sexual content and nudity | **No** | |
| Frequent/intense mature themes | **No** | |
| Frequent/intense horror | **No** | |
| Unrestricted web access | **No** (we control the loaded URL) | |
| Gambling and contests | **No** | |
| User-generated content | **YES** | Theme submissions — see UGC notes below |

**Result:** should land at **4+**. If the reviewer notices dating categories
and pushes to 9+ or 12+, accept it.

### UGC requirements (Apple 5.3 / 1.2)

App Store mandates these for any app with UGC. We comply via:

| Requirement | Our implementation | Status |
|---|---|---|
| Method to filter objectionable content | Admin queue: every theme submission AND item submission requires moderator approval. Item approvals now run through `_validate_category_for_publish()` (audit-5 H1 fix) so broken/non-bilingual content can't slip through | ✅ |
| Mechanism for users to report offensive content | **STILL GAP** — no per-theme "report" button. Mitigation: pre-moderation means no public objectionable content can appear; the "Feedback" form in profile is the de-facto report channel and is always accessible | ⚠️ Document as "pre-moderation + feedback channel" in App Review notes |
| Ability to block abusive users | **STILL GAP** — friend-request decline exists, but no "block forever" feature. Mitigation: friendship model is mutual-only — declining a request prevents future requests from same user (server-side enforced); no public messaging/comments anywhere | ⚠️ Document in App Review notes |
| Published contact info | Privacy page lists support@isverifiedby.me | ✅ |

**Decision needed before submission:**
- **Option A**: implement minimal report-content + block-user flows (~1 session)
- **Option B**: explicitly state in App Review notes "all UGC pre-moderated by
  admins, no public discoverability of unpublished content" — Apple may accept

## Google Play rating questionnaire (Everyone target)

Google uses IARC questionnaire. Similar form. Answers:

| Category | Answer |
|---|---|
| Violence | None |
| Sexuality | None |
| Profanity | None |
| Drugs/Alcohol/Tobacco | None |
| Gambling | None |
| User-generated content | **Yes** (with moderation) |
| Crude humor | None |
| Horror/fear | None |
| Sensitive themes (discrimination, bullying) | None |
| Personal information sharing | None (we collect own data only) |
| Location sharing | No |
| Communication features | Yes (friend requests, light) |

**Result:** should land at **Everyone**.

## Key talking points if reviewer asks

> "The app is a tournament-style preferences quiz. User picks one of two
> contestants in each round; at the end they get a short personality portrait
> based on their picks. There is no displayed media (no images, no audio); only
> textual references to public figures, films, music, places, etc. for context.
> All user-submitted themes are pre-moderated by human admins before becoming
> public. Users can delete their account and download their data anytime
> in-app."

If reviewer asks specifically about dating categories:

> "These categories are about the USER's own personality and preference style
> in relationships (e.g. 'how do you flirt?', 'what's your digital red flag?').
> They are not a dating service, do not connect users romantically, and do not
> contain sexual content. Same age-appropriate as a personality magazine quiz."
