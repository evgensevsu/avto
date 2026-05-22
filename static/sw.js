// Service Worker for ChinAuto Service PWA
const CACHE_NAME = 'chinauto-v1';
const STATIC_ASSETS = [
  '/',
  '/static/manifest.json',
  '/static/icon.svg',
];

// Install: cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: network-first for API/auth, cache-first for static
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Skip non-GET and API/auth routes — always go to network
  if (event.request.method !== 'GET') return;
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/login') ||
      url.pathname.startsWith('/logout') ||
      url.pathname.startsWith('/register') ||
      url.pathname.startsWith('/admin')) {
    return; // browser handles these natively
  }

  // Static assets: cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then(cached =>
        cached || fetch(event.request).then(resp => {
          if (resp.ok) {
            caches.open(CACHE_NAME).then(c => c.put(event.request, resp.clone()));
          }
          return resp;
        })
      )
    );
    return;
  }

  // Pages: network-first with cache fallback
  event.respondWith(
    fetch(event.request)
      .then(resp => {
        if (resp.ok) {
          caches.open(CACHE_NAME).then(c => c.put(event.request, resp.clone()));
        }
        return resp;
      })
      .catch(() => caches.match(event.request))
  );
});
