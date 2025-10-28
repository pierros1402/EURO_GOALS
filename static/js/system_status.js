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

    ver.textContent = `Version: ${j.version || '-'}`;
    if (j.last_health_ok_at){
      const dt = new Date(j.last_health_ok_at);
      lastHealth.textContent = `Last health: ${dt.toLocaleString()}`;
    } else if (j.last_health_error){
      lastHealth.textContent = `Last health error: ${j.last_health_error}`;
    } else {
      lastHealth.textContent = 'Last health: —';
    }

    // ΝΕΟ: Module & League Badges
    const cont = document.getElementById('modules-container');
    cont.innerHTML = '';
    if (j.modules){
      Object.entries(j.modules).forEach(([name, state])=>{
        const el = document.createElement('div');
        el.style.display='flex';
        el.style.alignItems='center';
        el.style.gap='4px';
        el.style.border='1px solid #1f2a44';
        el.style.background= state ? '#142a18':'#2a1414';
        el.style.color='#dfe9f6';
        el.style.borderRadius='12px';
        el.style.padding='4px 8px';
        el.style.fontSize='13px';
        el.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:${state?'#23d18b':'#ff5757'};display:inline-block"></span>${name}`;
        cont.appendChild(el);
      });
    }

  }catch(e){
    console.error('status fetch error', e);
  }
}

egFetchStatus();
setInterval(egFetchStatus, 10000);
