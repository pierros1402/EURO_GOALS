/* ============================================================
   EURO_GOALS NextGen – Notification Service Worker
   (based on v7.9e, adapted for coexistence with PWA caching)
   ============================================================ */

self.addEventListener("install", event => {
  console.log("📢 [NotifySW] Installed");
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  console.log("✅ [NotifySW] Activated");
  event.waitUntil(self.clients.claim());
});

/* 🔔 Λήψη μηνυμάτων για εμφάνιση ειδοποιήσεων */
self.addEventListener("message", event => {
  const data = event?.data || {};
  if (data && data.type === "SHOW_NOTIFICATION") {
    const { title, body, icon, url, tag } = data.payload || {};
    self.registration.showNotification(title || "EURO_GOALS", {
      body: body || "",
      icon: icon || "/static/icons/eurogoals_192.png",
      tag: tag || "eurosignal",
      requireInteraction: false,
      data: { url: url || "/" }
    });
  }
});

/* 🖱️ Όταν ο χρήστης κάνει κλικ στην ειδοποίηση */
self.addEventListener("notificationclick", event => {
  event.notification.close();
  const destination = event.notification?.data?.url || "/";
  event.waitUntil((async () => {
    const allClients = await self.clients.matchAll({
      type: "window",
      includeUncontrolled: true
    });
    for (const client of allClients) {
      if ("focus" in client) {
        client.focus();
        client.navigate(destination);
        return;
      }
    }
    await self.clients.openWindow(destination);
  })());
});
