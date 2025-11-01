// EURO_GOALS NextGen v8.9n – PWA Cache Handler
const CACHE_NAME = "eurogoals-v8.9n";
const URLS_TO_CACHE = ["/", "/static/manifest.json", "/static/icons/eurogoals_192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(URLS_TO_CACHE)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((names) => Promise.all(names.map((n) => n !== CACHE_NAME && caches.delete(n))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then((resp) => resp || fetch(e.request))
  );
});
