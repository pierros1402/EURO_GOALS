/* EURO_GOALS v7.9e – Frontend Notifications + Sound */

(function () {
  const STATE = {
    swRegistration: null,
    permission: Notification?.permission || 'default',
    enabled: JSON.parse(localStorage.getItem('eg_notify_enabled') || 'true'),
    soundEnabled: JSON.parse(localStorage.getItem('eg_sound_enabled') || 'true'),
    audio: null,
  };

  function ensureAudio() {
    if (STATE.audio) return STATE.audio;
    try {
      const a = new Audio('/static/sounds/alert.mp3');
      a.preload = 'auto';
      STATE.audio = a;
      return a;
    } catch (e) {
      return null;
    }
  }

  async function registerSW() {
    if (!('serviceWorker' in navigator)) return null;
    try {
      const reg = await navigator.serviceWorker.register('/service-worker.js');
      STATE.swRegistration = reg;
      return reg;
    } catch (e) {
      console.warn('[EG] SW registration failed', e);
      return null;
    }
  }

  async function ensurePermission() {
    if (!('Notification' in window)) return 'denied';
    if (Notification.permission === 'granted') return 'granted';
    try {
      const res = await Notification.requestPermission();
      STATE.permission = res;
      return res;
    } catch (e) {
      return 'denied';
    }
  }

  async function showSWNotification(payload) {
    if (!STATE.swRegistration) await registerSW();
    const sw = STATE.swRegistration?.active || navigator.serviceWorker.controller;
    if (!sw) {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(payload.title || 'EURO_GOALS', {
          body: payload.body || '',
          icon: payload.icon || '/static/icons/ball.png',
          tag: payload.tag || undefined,
        });
      }
      return;
    }
    sw.postMessage({ type: 'SHOW_NOTIFICATION', payload });
  }

  async function notifyEUROGoals(payload) {
    if (!STATE.enabled) return;
    const perm = await ensurePermission();
    if (perm !== 'granted') return;
    await showSWNotification(payload || {});
    if (STATE.soundEnabled) {
      const a = ensureAudio();
      if (a) { try { a.currentTime = 0; a.play(); } catch (_) {} }
    }
  }

  function injectToggle() {
    if (document.getElementById('eg-notify-toggle')) return;
    const box = document.createElement('div');
    box.id = 'eg-notify-toggle';
    box.style.position = 'fixed';
    box.style.right = '14px';
    box.style.bottom = '14px';
    box.style.zIndex = '9999';
    box.style.padding = '10px 12px';
    box.style.borderRadius = '12px';
    box.style.boxShadow = '0 4px 14px rgba(0,0,0,0.2)';
    box.style.background = 'rgba(20,22,26,0.9)';
    box.style.color = '#fff';
    box.style.font = '500 13px system-ui, -apple-system, Segoe UI, Roboto';
    box.style.display = 'flex';
    box.style.gap = '10px';
    box.style.alignItems = 'center';

    const chk = document.createElement('input');
    chk.type = 'checkbox';
    chk.checked = !!STATE.enabled;
    chk.title = 'Enable browser notifications';

    const label = document.createElement('span');
    label.textContent = 'Notifications';

    const sound = document.createElement('input');
    sound.type = 'checkbox';
    sound.checked = !!STATE.soundEnabled;
    sound.title = 'Enable sound';

    const soundLbl = document.createElement('span');
    soundLbl.textContent = 'Sound';

    box.appendChild(chk);
    box.appendChild(label);
    box.appendChild(sound);
    box.appendChild(soundLbl);

    chk.addEventListener('change', async () => {
      STATE.enabled = chk.checked;
      localStorage.setItem('eg_notify_enabled', JSON.stringify(STATE.enabled));
      if (STATE.enabled) await ensurePermission();
    });

    sound.addEventListener('change', () => {
      STATE.soundEnabled = sound.checked;
      localStorage.setItem('eg_sound_enabled', JSON.stringify(STATE.soundEnabled));
      if (STATE.soundEnabled) ensureAudio();
    });

    document.body.appendChild(box);
  }

  window.addEventListener('load', async () => {
    await registerSW();
    if (STATE.enabled) await ensurePermission();
    injectToggle();
  });

  window.notifyEUROGoals = notifyEUROGoals;
})();
