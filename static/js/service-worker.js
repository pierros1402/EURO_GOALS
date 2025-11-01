/* =====================================================
   EURO_GOALS v8.9m NextGen – Unified Service Worker
   Combines: Notifications + PWA offline caching
   ===================================================== */

const CACHE_NAME = "eurogoals-cache-v8_9m";
const urlsToCache = [
  "/",
  "/static/icons/eurogoals_192.png",
  "/static/icons/eurogoals_512.png",
  "/static/manifest.json"
];

/* --- INSTALL --- */
self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("📦 Caching essential files...");
      return cache.addAll(urlsToCache);
    })
  );
});

/* --- ACTIVATE --- */
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("🧹 Deleting old cache:", key);
            return caches.delete(key);
          }
        })
      )
    )
  );
  return self.clients.claim();
});

/* --- FETCH --- */
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return (
        response ||
        fetch(event.request).catch(() => new Response("⚠️ Offline mode"))
      );
    })
  );
});

/* --- NOTIFICATIONS --- */
self.addEventListener("message", (event) => {
  const data = event?.data || {};
  if (data.type === "SHOW_NOTIFICATION") {
    const { title, body, icon, url, tag } = data.payload || {};
    self.registration.showNotification(title || "EURO_GOALS", {
      body: body || "",
      icon: icon || "/static/icons/eurogoals_192.png",
      tag: tag || undefined,
      requireInteraction: false,
      data: { url: url || "/" }
    });
  }
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const dest = event.notification?.data?.url || "/";
  event.waitUntil((async () => {
    const allClients = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const client of allClients) {
      if ("focus" in client) {
        client.focus();
        client.navigate(dest);
        return;
      }
    }
    await self.clients.openWindow(dest);
  })());
});
