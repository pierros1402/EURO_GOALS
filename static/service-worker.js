self.addEventListener("install", e => {
  console.log("⚽ EURO_GOALS Service Worker εγκαταστάθηκε");
  e.waitUntil(
    caches.open("eurogoals-cache").then(cache => {
      return cache.addAll(["/", "/static/manifest.json"]);
    })
  );
});

self.addEventListener("fetch", e => {
  e.respondWith(
    caches.match(e.request).then(resp => resp || fetch(e.request))
  );
});

self.addEventListener("activate", e => {
  console.log("✅ Service Worker ενεργό");
});
