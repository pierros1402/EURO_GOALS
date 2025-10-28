async function egFetchStatus(){
  try{
    const r = await fetch('/api/status', {cache:'no-store'});
    const j = await r.json();

    const renderDot = document.getElementById('st-render-dot');
    const renderTxt = document.getElementById('st-render-txt');
    const lastHealth = document.getElementById('st-last-health');

    const db = document.getElementById('st-db');
    const routerDot = document.getElementById('st-router-dot');
    const router = document.getElementById('st-router');
    const uptime = document.getElementById('st-uptime');
    const ver = document.getElementById('st-version');

    // Render status
    const online = !!j.render_online;
    renderDot.classList.remove('ok','bad');
    renderDot.classList.add(online ? 'ok' : 'bad');
    renderTxt.textContent = online ? 'Online' : 'Offline';

    // DB
    db.textContent = j.db_in_use || '—';

    // Router
    const active = !!j.feeds_router_active;
    routerDot.classList.remove('ok','bad');
    routerDot.classList.add(active ? 'ok' : 'bad');
    router.textContent = active ? 'Feeds Active' : 'Idle';

    // Uptime
    const secs = Number(j.uptime_seconds || 0);
    const hh = Math.floor(secs/3600).toString().padStart(2,'0');
    const mm = Math.floor((secs%3600)/60).toString().padStart(2,'0');
    const ss = (secs%60).toString().padStart(2,'0');
    uptime.textContent = `${hh}:${mm}:${ss}`;

    // Version & last health
    ver.textContent = `Version: ${j.version || '-'}`;
    if (j.last_health_ok_at){
      const dt = new Date(j.last_health_ok_at);
      lastHealth.textContent = `Last health: ${dt.toLocaleString()}`;
    } else if (j.last_health_error){
      lastHealth.textContent = `Last health error: ${j.last_health_error}`;
    } else {
      lastHealth.textContent = 'Last health: —';
    }
  }catch(e){
    console.error('status fetch error', e);
  }
}

egFetchStatus();
setInterval(egFetchStatus, 10000);
