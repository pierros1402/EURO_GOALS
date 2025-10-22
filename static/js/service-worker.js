/* EURO_GOALS v7.9e – Service Worker for Notifications */

self.addEventListener('install', (event) => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

self.addEventListener('message', (event) => {
  const data = event?.data || {};
  if (data && data.type === 'SHOW_NOTIFICATION') {
    const { title, body, icon, url, tag } = data.payload || {};
    self.registration.showNotification(title || 'EURO_GOALS', {
      body: body || '',
      icon: icon || '/static/icons/ball.png',
      tag: tag || undefined,
      requireInteraction: false,
      data: { url: url || '/' }
    });
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const dest = event.notification?.data?.url || '/';
  event.waitUntil((async () => {
    const allClients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of allClients) {
      if ('focus' in client) {
        client.focus();
        client.navigate(dest);
        return;
      }
    }
    await self.clients.openWindow(dest);
  })());
});
