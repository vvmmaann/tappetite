# Mobile build pipeline — Tappetite

Capacitor wrapper around the live PWA. Phase B / Phase 7 of the launch plan.

## What's here

- **Hybrid bundle architecture:** the app loads `https://isverifiedby.me`
  primary (auto-updates without store re-review). Bundled `www/index.html`
  serves as offline fallback ("no internet" page with retry).
- **Native plugin integration in `game.html`:** filesystem download for
  data-export, native share sheet, haptic taps, status-bar theming, no SW.
  All wrapped in `Native.*` helpers that no-op on web.
- **iOS + Android projects pre-configured.** Xcode and Android Studio can
  open them directly. Just need build accounts + a Mac (iOS only) to ship.
- **Icons + splash auto-generated** from `assets/` masters.
  Replace masters with designer art before store submission.

## Prerequisites (when you're ready to build)

| Need | Where | Cost |
|---|---|---|
| Apple Developer account | https://developer.apple.com/programs/ | $99/year |
| Google Play Developer account | https://play.google.com/console | $25 once |
| Mac with Xcode 15+ | for iOS .ipa build | hardware |
| Android Studio Hedgehog+ + JDK 17+ | for Android .aab build | free, any OS |
| Node 20+ + npm 10+ | already have (24.x) | free |

If you don't have a Mac, alternatives for iOS:
- **MacInCloud.com** rental ($30-40/month)
- **Codemagic / Bitrise** cloud CI (free tier sufficient for our scale)
- **GitHub Actions macOS runner** (paid but minimal for occasional builds)
- **Borrow a friend's Mac** for the one-time submission

## Project structure

```
mobile/
├── capacitor.config.json    # hybrid mode: server.url + bundled fallback
├── package.json + lock      # 11 npm packages
├── www/                     # offline fallback (≤100 KB total)
│   ├── index.html          # "no internet" page with retry button
│   ├── icon.svg, manifest.json
├── assets/                  # icon + splash MASTERS (1024 / 2732)
│   ├── generate_masters.py # script to regenerate from existing icon.svg
│   ├── icon-only.png        1024×1024
│   ├── icon-foreground.png  1024×1024 (Android adaptive)
│   ├── icon-background.png  1024×1024 (Android adaptive)
│   ├── splash.png           2732×2732 (light)
│   └── splash-dark.png      2732×2732 (dark)
├── ios/                     # Xcode project (open in Xcode on Mac)
│   └── App/App/Info.plist, AppDelegate.swift, Assets.xcassets/, ...
├── android/                 # Android Studio project
│   └── app/src/main/AndroidManifest.xml, java/, res/, ...
└── store-metadata/          # store listing copy + answers (RU + EN)
    ├── description-ru.md, description-en.md
    ├── app-store-listing.md, google-play-listing.md
    ├── age-rating.md
    ├── privacy-nutrition-label.md
    ├── data-safety.md
    └── screenshots-spec.md
```

## Workflow when accounts are bought

### Step 1 — replace placeholder assets

Current icon/splash is a placeholder cream-bg + italic "P" + terracotta dot.
Designer should make the master 1024×1024 + 2732×2732 PNGs in `assets/`.
Then regenerate all platform sizes:

```bash
cd mobile
npx capacitor-assets generate --android --ios
```

### Step 2 — set the final app name

Currently `appName: "Tappetite"` (set 2026-05-09). To change later, edit:

1. `capacitor.config.json` → `appName`
2. `ios/App/App/Info.plist` → `CFBundleDisplayName`
3. `android/app/src/main/res/values/strings.xml` → `app_name`

⚠️ **Bundle ID** (`me.isverifiedby.pickgame`) is harder to change after first
store submission. Pick the final ID before submitting.

### Step 3 — build Android (any OS)

Install **JDK 17+** and **Android Studio**. Set ANDROID_HOME env var.

```bash
cd mobile
npx cap sync android       # copy web assets + apply config
npx cap open android       # opens Android Studio

# In Android Studio:
#   Build → Generate Signed Bundle → Android App Bundle (.aab)
#   Create new keystore on first build (save it — need same key for updates!)
#   Output: android/app/build/outputs/bundle/release/app-release.aab
```

Upload the `.aab` to https://play.google.com/console (Internal testing first,
then Production).

### Step 4 — build iOS (requires Mac)

```bash
cd mobile
npx cap sync ios
npx cap open ios          # opens Xcode

# In Xcode:
#   1. Select team in Signing & Capabilities (your Apple Developer account)
#   2. Set Bundle Identifier matches App Store Connect listing
#   3. Build for Distribution: Product → Archive
#   4. Distribute App → App Store Connect → Upload
```

Then in https://appstoreconnect.apple.com → fill listing → submit for review.

### Step 5 — fill store listings

See `store-metadata/` for ready-made copy:
- `description-ru.md` + `description-en.md` — copy into store dashboards
- `keywords.md` — App Store keyword field (max 100 chars)
- `age-rating.md` — answers to age-rating questionnaires
- `privacy-nutrition-label.md` — Apple's privacy form (mandatory since 2020)
- `data-safety.md` — Google's data form (mandatory since 2022)
- `screenshots-spec.md` — what to capture and at what resolution

## Local dev / testing

Capacitor's web preview is just our existing live site:
```bash
# Just go to https://isverifiedby.me — that's what the app loads
```

To test in an Android emulator:
```bash
cd mobile
npx cap sync
npx cap run android        # runs in connected device/emulator
```

To test in an iOS simulator (Mac only):
```bash
npx cap run ios
```

## Updating the web app post-launch

Because of `server.url` in hybrid mode, **most app updates don't need store
re-review**. Just deploy `game.html` to https://isverifiedby.me/ as usual,
and all installed apps load the new version on next launch.

When DO you need a store update:
- Adding/removing native plugins
- Changing Capacitor version or platform native code
- Icon/splash changes
- App name / bundle ID changes
- Permissions changes (Info.plist / AndroidManifest)

## Troubleshooting

**"npx cap sync" fails:** delete `node_modules/` and run `npm install` again.

**Android build fails with JDK error:** verify `java -version` shows 17+.
Older JDK = Capacitor won't build.

**iOS Xcode "code signing" error:** you need a paid Apple Developer account
linked in Xcode's Preferences → Accounts.

**Status bar wrong color in app:** check `applyTheme()` is calling
`Native.setStatusBarStyle()` — patched in game.html line ~8270.

**App won't load anything in production:** check `capacitor.config.json` has
correct `server.url`. If you forgot the `https://` prefix, native shell
treats it as local file and breaks.

## Rollback

If a Capacitor build is bad, just stop pushing the .ipa/.aab. The PWA at
isverifiedby.me keeps working independently. The native app falls back to
last-cached state (or the offline page if no cache).
