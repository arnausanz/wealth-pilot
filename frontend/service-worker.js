// WealthPilot Service Worker — Vite/React build
// Estratègia: Network-first per API, Cache-first per assets estàtics (immutables)

const CACHE_VERSION = 'v2';
const CACHE_NAME = `wealthpilot-${CACHE_VERSION}`;

// Assets que sempre pre-cachegem (immutables — servits per Vite amb hash al nom)
const PRECACHE_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/icons/apple-touch-icon.png',
];

// ─── Install ──────────────────────────────────────────────────────────────────

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Pre-cache els assets crítics (silenciem errors individuals)
      return Promise.allSettled(
        PRECACHE_ASSETS.map((url) =>
          cache.add(url).catch(() => {/* ignora si falla algun asset */})
        )
      );
    })
  );
  // Activa immediatament sense esperar que es tanquin tabs antics
  self.skipWaiting();
});

// ─── Activate ────────────────────────────────────────────────────────────────

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k.startsWith('wealthpilot-') && k !== CACHE_NAME)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ─── Fetch ────────────────────────────────────────────────────────────────────

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 1. Ignora peticions que no siguin HTTP(S)
  if (!url.protocol.startsWith('http')) return;

  // 2. API calls → Network-only (mai cache per dades financeres)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request).catch(() =>
        new Response(
          JSON.stringify({ error: 'Sense connexió', offline: true }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        )
      )
    );
    return;
  }

  // 3. Vite assets amb hash al nom (/_assets/, /assets/) → Cache-first (immutables)
  if (url.pathname.match(/\/(assets|_assets)\//)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok) {
            caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()));
          }
          return response;
        });
      })
    );
    return;
  }

  // 4. Icones i manifest → Cache-first
  if (url.pathname.startsWith('/icons/') || url.pathname === '/manifest.json') {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request))
    );
    return;
  }

  // 5. Navegació (HTML) → Network-first, fallback a / en cas offline
  if (request.mode === 'navigate' || request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Desa la resposta actualitzada
          if (response.ok) {
            caches.open(CACHE_NAME).then((cache) => cache.put(request, response.clone()));
          }
          return response;
        })
        .catch(() =>
          caches.match('/index.html').then(
            (cached) =>
              cached ||
              new Response('<h1>WealthPilot</h1><p>Sense connexió</p>', {
                headers: { 'Content-Type': 'text/html' },
              })
          )
        )
    );
    return;
  }

  // 6. Resta → Network-first
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});
