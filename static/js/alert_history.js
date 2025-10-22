// =========================================================
// EURO_GOALS v7.9b – Alert History JS (Advanced Filters)
// =========================================================

async function fetchLeagues() {
  try {
    const res = await fetch("/api/alerts/leagues");
    const data = await res.json();
    const sel = document.getElementById("filter-league");
    // καθάρισε τυχόν προηγούμενα
    sel.innerHTML = `<option value="">All Leagues</option>`;
    if (data && Array.isArray(data.leagues)) {
      data.leagues.forEach(lg => {
        const opt = document.createElement("option");
        opt.value = lg;
        opt.textContent = lg;
        sel.appendChild(opt);
      });
    }
  } catch (e) {
    console.error("Failed to load leagues:", e);
  }
}

async function loadAlerts() {
  const type = document.getElementById("filter-type").value;
  const league = document.getElementById("filter-league").value;
  const from = document.getElementById("filter-from").value;
  const to = document.getElementById("filter-to").value;

  let url = `/api/alerts?`;
  if (type) url += `type=${encodeURIComponent(type)}&`;
  if (league) url += `league=${encodeURIComponent(league)}&`;
  if (from) url += `date_from=${from}&`;
  if (to) url += `date_to=${to}&`;

  const tbody = document.querySelector("#alerts-table tbody");
  tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; opacity:.7;">Loading...</td></tr>`;

  try {
    const res = await fetch(url);
    const data = await res.json();

    tbody.innerHTML = "";
    if (!Array.isArray(data) || data.length === 0) {
      const empty = document.createElement("tr");
      empty.innerHTML = `<td colspan="4" style="text-align:center; opacity:.6;">No alerts found</td>`;
      tbody.appendChild(empty);
      return;
    }

    data.forEach(a => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${a.timestamp}</td>
        <td>${a.type || "-"}</td>
        <td>${a.league || "-"}</td>
        <td>${a.message || ""}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading alerts:", err);
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#ff6b6b;">Error loading alerts</td></tr>`;
  }
}

document.getElementById("filter-btn").addEventListener("click", loadAlerts);

document.getElementById("clear-btn").addEventListener("click", () => {
  document.getElementById("filter-type").value = "";
  document.getElementById("filter-league").value = "";
  document.getElementById("filter-from").value = "";
  document.getElementById("filter-to").value = "";
  loadAlerts();
});

window.addEventListener("DOMContentLoaded", async () => {
  await fetchLeagues();
  await loadAlerts();
});
