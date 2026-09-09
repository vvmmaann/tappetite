# Notes for the App Store Review team

Paste this verbatim into App Store Connect → App Review Information →
Notes when submitting. Apple reviewers read this BEFORE testing — clear,
short, technical, polite copy here saves rejections.

---

## ENGLISH (paste this; Apple reviews in English)

```
Tappetite is a hybrid Capacitor app that wraps a web PWA hosted at
https://isverifiedby.me. The native shell loads the same web build as
the production site; offline fallback is bundled in mobile/www.

Core mechanic: a tap-tournament. The user is shown two options at a
time and picks the favorite; the loser drops out. After 16/32/64 picks
the user gets a personal "taste profile" derived from their picks.

KEY THINGS TO TEST:
1. First-launch Welcome screen with nickname picker. Privacy/Terms
   checkbox MUST be ticked before "Готово →" / "Done →" enables.
2. Sign in with Apple (offered alongside Google per rule 4.8). Tap
   "у меня уже есть аккаунт" / "I already have an account" → consent
   checkbox → "Войти через Apple" / "Sign in with Apple".
3. Optional email registration: profile → "регистрация" / "register".
4. Account deletion: profile → "Опасная зона" / "Danger zone" →
   "удалить аккаунт навсегда" / "delete account permanently". This
   wipes the server account immediately (BEGIN IMMEDIATE transaction)
   and severs the PostHog identity link locally. Tested working.
5. Data export: profile → "Мои данные" / "My data" → "скачать мои
   данные" / "download my data". Returns a JSON of everything we hold.

DEMO ACCOUNT (pre-populated with results):
  Email:    apple_review@isverifiedby.me
  Password: ReviewerDemo2026!

PRIVACY/CONSENT:
- PostHog product analytics is fully disabled until the user actively
  consents (welcome / register / login checkbox). No /decide, no
  capture, no localStorage writes pre-consent.
- All third-party processors disclosed in privacy.html §04 (PostHog EU,
  Resend US, Google, Apple, hosting EU, Cloudflare).

CONTENT:
- Item names (films, actors, songs, dishes etc.) are reference points
  for personal choice, not media playback. We do not display copyrighted
  audio/video. Rights-holder takedowns honored via support@.
- User-generated content (theme suggestions, item suggestions, feedback)
  goes through admin moderation queue before appearing.
- Reporting / blocking other users: friends-only model, no public
  comments/messaging. Friend requests can be declined.

CONTACT:
  support@isverifiedby.me  —  responds within 14 days
```

## RUSSIAN (mirror, in case reviewer is RU-region)

```
Tappetite — гибридное приложение на Capacitor, оборачивающее веб-PWA на
https://isverifiedby.me. Нативная оболочка грузит ту же веб-сборку, что
и продакшн-сайт; offline-fallback забандлен в mobile/www.

Базовая механика: турнир-выбор. Пользователю показываются два варианта,
он выбирает любимый; проигравший выбывает. После 16/32/64 выборов
получает персональный «профиль вкуса» на основе своих выборов.

ВАЖНОЕ ДЛЯ ПРОВЕРКИ:
1. Первый запуск — Welcome с выбором ника. Чекбокс согласия с
   Privacy/Terms ОБЯЗАТЕЛЕН перед активацией кнопки «Готово →».
2. Sign in with Apple (предлагается вместе с Google по правилу 4.8).
   Тап «у меня уже есть аккаунт» → чекбокс согласия → «Войти через Apple».
3. Опциональная email-регистрация: профиль → «регистрация».
4. Удаление аккаунта: профиль → «Опасная зона» → «удалить аккаунт
   навсегда». Удаляет серверную учётную запись немедленно (одна
   транзакция BEGIN IMMEDIATE) и разрывает связь с PostHog identity
   локально. Проверено в работе.
5. Экспорт данных: профиль → «Мои данные» → «скачать мои данные».
   Возвращает JSON со всем, что у нас на тебя есть.

ДЕМО-АККАУНТ (с заполненной историей):
  Email:    apple_review@isverifiedby.me
  Пароль:   ReviewerDemo2026!

ПРИВАТНОСТЬ/СОГЛАСИЯ:
- PostHog отключён полностью до активного согласия пользователя
  (чекбокс на welcome/registration/login). До согласия не идут запросы
  /decide, не пишется в localStorage.
- Все процессоры третьих сторон описаны в privacy.html §04 (PostHog EU,
  Resend US, Google, Apple, хостинг EU, Cloudflare).

КОНТЕНТ:
- Имена элементов (фильмы, актёры, песни, блюда и т.д.) — точки выбора,
  не медиаконтент. Мы не воспроизводим защищённое аудио/видео.
  Правообладатели могут отправить запрос на удаление через support@.
- UGC (предложения тем, элементов, обратная связь) проходит модерацию
  перед публикацией.
- Жалоба/блокировка пользователей: модель только-друзья, публичных
  комментариев нет. Запросы дружбы можно отклонять.

КОНТАКТ:
  support@isverifiedby.me — отвечаем в течение 14 дней
```

## Pre-submission checklist (so you actually have these before Apple opens the build)

- [ ] Demo account exists and you can log into it
- [ ] At least one tournament is completed under demo account so the
      "profile" screen has content
- [ ] support@isverifiedby.me actually receives email (test from outside)
- [ ] privacy.html and terms.html return 200 from the live URL
- [ ] App icon at 1024×1024 has NO alpha channel and NO rounded corners
      (Apple does the rounding itself; transparency causes rejection)
- [ ] App version (CFBundleShortVersionString) is 1.0.0 for first release
- [ ] CFBundleVersion (build number) is 1 for first upload (increment for each)
