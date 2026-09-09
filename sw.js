// Tappetite · service worker · v4 (audit-9 P1.b: self-hosted html2canvas)
// Conservative strategy:
//   - Cache our own /assets/fonts/*.woff2 and /assets/vendor/*.js
//     (immutable per URL because filename includes version/hash)
//   - Never cache our own HTML/JS/CSS — always fetch fresh, so the next
//     deploy is instantly visible
//   - This means no full offline support yet
//   - Versioned cache name `tappetite-cdn-v4` — bump on each policy change
//     so old caches get evicted by the activate handler.
//   - Audit-9 P1.b: cdnjs entirely removed from third-party hosts. We
//     no longer fetch ANY third-party resource pre-consent.

const CACHE = 'tappetite-cdn-v4';
// No third-party CDN hosts at all — everything is same-origin now.
const CDN_HOSTS = new Set([]);

self.addEventListener('install', (event) => {
  // Take over immediately on first install
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    // Drop any old cache versions
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    // Claim all open clients so next nav uses this SW
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  let url;
  try { url = new URL(req.url); } catch (e) { return; }

  // Audit-6 H1 + audit-9 P1.b: cache same-origin immutable assets.
  // Both /assets/fonts/* (woff2 filenames include Google Fonts content
  // hashes) and /assets/vendor/* (versioned filenames like
  // html2canvas-1.4.1.min.js) are stable per-URL, so cache-first is safe.
  const isOwnImmutable = url.origin === self.location.origin
                  && (url.pathname.startsWith('/assets/fonts/')
                      || url.pathname.startsWith('/assets/vendor/'));

  if (CDN_HOSTS.has(url.hostname) || isOwnImmutable) {
    // Cache-first for immutable same-origin assets
    event.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const cached = await cache.match(req);
      if (cached) return cached;
      try {
        const resp = await fetch(req);
        if (resp.ok) cache.put(req, resp.clone());
        return resp;
      } catch (e) {
        // CDN unreachable AND not cached: re-throw so browser shows network error
        throw e;
      }
    })());
  }
  // Other requests (our own HTML/JS/etc): pass through to network. No SW interception.
});

// ─── WEB PUSH (2026-05-11) ─────────────────────────────────────────
// The browser delivers push messages here even when the tab is closed.
// Server-side, send_push_to_user() POSTs an encrypted JSON payload via
// VAPID to the push service; the service wakes this SW; we display a
// system notification.
//
// Payload contract (matches what the backend send_push_to_subscription emits):
//   { title, body, url?, tag?, icon?, badge?, requireInteraction? }
//
// Falls back gracefully when fields are missing — empty title is replaced
// with a generic 'Tappetite' so the notification doesn't render blank.
self.addEventListener('push', (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch (e) {
    // Non-JSON payload (rare, would be a server bug) — treat as plain text body
    try { payload = { body: event.data && event.data.text ? event.data.text() : '' }; }
    catch (_) { payload = {}; }
  }
  const title = payload.title || 'Tappetite';
  const options = {
    body: payload.body || '',
    icon: payload.icon || '/assets/icons/icon-192.png',
    badge: payload.badge || '/assets/icons/badge-72.png',
    // tag groups notifications: same-tag pushes replace the previous one
    // on screen instead of stacking. Useful for "@nick прошёл турнир X"
    // where multiple plays in the same theme shouldn't spam separate banners.
    tag: payload.tag || undefined,
    // requireInteraction makes the banner stay until user dismisses it
    // (desktop only — mobile auto-dismisses regardless). Only set for
    // genuinely important pushes (challenge received), not daily reminders.
    requireInteraction: !!payload.requireInteraction,
    // data is passed to the click handler below — we stash the URL there.
    data: { url: payload.url || '/', ts: Date.now() },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

// User clicked a notification. Focus the existing tab if the app is already
// open, otherwise open a new tab on the payload's url (default '/').
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil((async () => {
    const allClients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    // Try to find an existing tab on our origin and navigate it.
    for (const client of allClients) {
      try {
        const u = new URL(client.url);
        if (u.origin === self.location.origin) {
          await client.focus();
          if (client.url !== self.location.origin + targetUrl) {
            await client.navigate(targetUrl).catch(() => {});
          }
          return;
        }
      } catch (e) { /* ignore */ }
    }
    // No existing tab — open a new one
    await self.clients.openWindow(targetUrl);
  })());
});

// pushsubscriptionchange fires when the browser unilaterally invalidates
// the subscription (e.g. user uninstalled the PWA, browser cleared data).
// We can't re-subscribe from inside SW without user gesture in most cases,
// but we CAN tell the server to forget the old endpoint so it stops
// trying to deliver. Note: this event is unreliable across browsers, so
// the primary "dead subscription" cleanup happens server-side when send
// returns 410 Gone.
self.addEventListener('pushsubscriptionchange', (event) => {
  event.waitUntil((async () => {
    const oldSub = event.oldSubscription;
    if (!oldSub) return;
    try {
      await fetch('/api/push/unsubscribe', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: oldSub.endpoint,
          p256dh: '',  // backend doesn't need keys for delete-by-endpoint
          auth: '',
        }),
      });
    } catch (e) { /* offline — server will reap via 410 Gone */ }
  })());
});
