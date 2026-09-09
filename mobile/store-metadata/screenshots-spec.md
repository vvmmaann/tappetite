# Screenshots — what to capture and at what size

Both stores require screenshots before publishing. Capture once, resize as needed.
Updated 2026-05-10. Added Welcome screen + "Мои согласия" / consent
management as recommended captures (these are part of the launch story).

## Capture strategy

Easiest workflow: open https://isverifiedby.me in **Chrome desktop with mobile
viewport emulation** (DevTools → Toggle device toolbar → "iPhone 16 Pro Max"
preset = 430×932 viewport, 1290×2796 actual pixels with 3x DPR).

For Android: use the installed APK on a real phone + adb screencap, OR
the emulator. Real device is easier and the screenshots come out at
exact device resolution (1080×2340 typical for Android phones).

Sweet spot: **5-6 strong screenshots** beats 10 mediocre ones. Apple
recommends ≥4, max 10. Google Play requires ≥2, max 8.

## Recommended sequence (in display order on store page)

### 1. Battle screen — the binary choice
- Mid-tournament, two options visible
- Pick a category with recognizable items (e.g. cinema, music) so the
  reviewer/user instantly understands what they'd be picking between
- **Why first:** core gameplay = first thing user wants to see. Sells
  the app in 1 second.

### 2. Result — top-3 + archetype
- After completing a tournament
- Show top 1, 2, 3 + archetype name + opening of body
- **Why:** the payoff. Shows there's a meaningful outcome.

### 3. Home — cluster grid
- Scroll to top so masthead + first cluster row visible
- Best with a couple of cluster cards stacked, glimpse of 4-6 themes
- **Why:** demonstrates breadth (112 themes / 17 clusters)

### 4. Profile — taste overview
- Logged-in user with some history (use the demo account!)
- Show "тяга к [cluster]", "открыто N%", recent results
- **Why:** shows the long-term reward, why an account is worth it

### 5. Welcome screen (mobile-only) OR Privacy controls
- Either:
  - **Welcome:** "Привет. Как тебя зовут?" with name input + consent
    checkbox + "Войти через Apple/Google" buttons. Shows we respect
    privacy + have native sign-in.
  - **Profile → Мои согласия:** the toggle list. Shows granular
    consent control = trustworthy app.
- **Why:** differentiator vs random quiz apps. Privacy-first is a
  marketing angle worth using.

### 6. Share card — magazine-style result
- Tap "Share" on result screen → shows the magazine-cover format with
  user's nickname, top-3, archetype
- **Why:** demonstrates social/share angle, which drives WOM growth

### Optional 7-8 (only if you want a longer carousel)

- Dark theme variant of any prior shot — shows polish + theme support
- "Submit a theme" form — demonstrates UGC + community angle

## Required sizes

### Apple App Store (iPhone)

Mandatory: **6.9" (iPhone 16 Pro Max)** = `1320 × 2868` portrait.

Optional but recommended: 6.5" (iPhone 11 Pro Max) = `1242 × 2688`

Apple auto-scales down for smaller phones, so capturing only the largest is
OK. Min 3 screenshots per device size, max 10.

If supporting iPad, also: **iPad Pro 13"** = `2064 × 2752` portrait.

### Google Play (phone)

Required: at least 2, max 8.
Min: 1080×1920 portrait.

For tablets (optional for our use case): 7" + 10" classes, both
1080×1920 minimum.

### Google Play (feature graphic)

**Mandatory.** `1024×500` PNG, displayed at top of store listing on Android.
Should show app name + brand visual + value prop. Designer to make.

## Tools

- **Chrome DevTools** mobile-emulation — easy capture in correct ratio
- **Apple's "Xcode Simulator"** — actual device-accurate screenshots (Mac only)
- **Online resizers** like https://www.appicon.co/ for resizing once captured

## Annotations / overlays

You CAN add text overlays / arrows on screenshots in store listings — it's
common and increases install rates. Useful captions to consider:
- On Battle screen: "Один тап — твой выбор" / "One tap, your pick"
- On Result screen: "Финал — твой портрет вкуса" / "The finish: your taste"
- On Profile: "Сравни с друзьями" (if friends preview visible) / "Compare with friends"

Keep overlays simple — Apple sometimes rejects screenshots that look like
ads more than the actual app.

## Capture flow (suggested sequence)

```
1. Set DevTools to iPhone 16 Pro Max
2. Open https://isverifiedby.me in incognito (clean cookies)
3. Pick "Curious? Tap" or any cluster → start a tournament
4. Make a few picks → screenshot battle screen
5. Finish tournament → screenshot result screen
6. Tap Share → screenshot share card
7. Logout → re-login as a test account with history → go to Profile
8. Screenshot profile (with achievements, history previews)
9. Open dark theme → repeat key shots
10. Open Submit tab → screenshot the form (empty + populated)
```

Total time: ~30 minutes for first version. Iterate based on store conversion
rates after launch.
