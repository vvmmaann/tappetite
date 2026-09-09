# Tappetite

A taste-tournament game. You get a theme ("best world cuisine", "your 2020s music", "brands that match your style"), the game shows two options, you tap the one you like more, the loser drops out. Sixteen taps later you have your top-3, a taste type with an editorial write-up, and, after enough tournaments, an AI-written portrait of your taste. You can compare results with friends and share a card.

Web and Android, Russian and English.

- Web: https://isverifiedby.me
- Google Play: https://play.google.com/store/apps/details?id=me.isverifiedby.pickgame
- Direct APK: https://isverifiedby.me/dl/tappetite.apk
- Hackathon deck: https://isverifiedby.me/hackathon/deck.html

## Clock In (Solana Mobile hackathon), Sept 8 to Oct 8, 2026

This repository was published on 2026-09-09, day two of the hackathon, so the commit history shows what existed before and what is built during the month.

State at the start of the hackathon:

- The game, the content library and the backend are live in production (see "What is live").
- The Android app is a Capacitor shell that loads the web app from the server, plus native push (FCM), haptics, the share sheet and Google sign-in.
- No wallet, no on-chain interaction, no SKR anywhere.

Planned during the hackathon (updated as things land):

- [ ] Wallet sign-in through Mobile Wallet Adapter, as a native Kotlin bridge inside the Capacitor app (Seed Vault, Phantom, Solflare)
- [ ] AI portraits paid in SKR: SPL transfer signed through MWA, verified on-chain by the backend (mint, amount, recipient, memo with order id) before generation
- [ ] Seeker Genesis Token perks: first portrait free, a Seeker achievement, an exclusive tournament
- [ ] Web assets bundled into the APK (offline start), new signing key, dApp Store submission
- [ ] Haptics on every pick, result card through the native share sheet
- [ ] Demo video and final deck

## What is live (September 2026)

- 152 tournaments across 25 clusters, 2,696 items, 1,053 taste types with write-ups, all in RU and EN (`api/data/categories.json`)
- AI portraits generated with Claude (Anthropic), with per-portrait share cards and public pages
- Friends: requests, comparison of results with a per-category fit score
- Daily theme with push notifications (FCM on Android, VAPID web push), comeback and streak pushes
- Achievements, visit streaks, user-suggested themes with a moderation queue
- Admin panel: moderation, content editor, live event stream, error tracker

## Layout

```
game.html                 the whole client (single file, vanilla JS)
admin.html                admin panel (single file)
privacy.html, terms.html  legal pages (RU/EN)
api/main.py               FastAPI backend (auth, results, friends, push, admin)
api/portrait.py           AI portrait generation and share cards
api/insights.py           per-user insights
api/data/categories.json  the content library
api/templates/            OG card SVG templates
api/systemd/              daily push batch timer
api/nginx-*.conf          nginx config used in production
mobile/                   Capacitor project (android/, ios/), store metadata
branding/, assets/        logo, icons, fonts
hackathon/                Clock In deck and images
```

## Running it

Web client: any static server that serves `game.html` as `/`, for example `python -m http.server 8080` in the repo root, then open `http://localhost:8080/game.html`. The client talks to the API at `/api/`, so in development point it at a running backend (nginx config in `api/nginx-isverifiedby.me.conf` shows the production layout).

Backend:

```
cd api
python -m venv venv && . venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8001
```

Configuration is by environment variables, documented in the header of `api/main.py` (admin password, Anthropic key for portraits, VAPID keys for web push, FCM credentials). Nothing secret is in this repository.

Android:

```
cd mobile
npm install
npx cap sync android
cd android && ./gradlew assembleDebug
```

You need your own `mobile/android/app/google-services.json` (Firebase project for push) and, for release builds, `mobile/android/keystore.properties`. Both are gitignored.

## Author

Elmurat Nigmatov, Kazakhstan. Solo project. Source is public for hackathon review; all rights reserved.
