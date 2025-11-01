const CACHE_NAME = "eurogoals-nextgen-cache-v1";
const FILES_TO_CACHE = [
  "/",
  "/static/icons/eurogoals_192.png",
  "/static/icons/eurogoals_512.png"
];

// Εγκατάσταση και caching
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(FILES_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Φόρτωση από cache ή δίκτυο
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});

// Αυτόματη ανανέωση cache όταν αλλάζει έκδοση
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});
