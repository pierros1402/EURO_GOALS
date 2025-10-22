// =========================================================
// EURO_GOALS v7.9c – Alert History JS (Export + Filters)
// =========================================================

async function fetchLeagues() {
  const sel = document.getElementById("filter-league");
  sel.innerHTML = `<option value="">All Leagues</option>`;
  try {
    const res = await fetch("/api/alerts/leagues");
    const data = await res.json();
    if (data.leagues) {
      data.leagues.forEach(lg => {
        const opt = document.createElement("option");
        opt.value = lg;
        opt.textContent = lg;
        sel.appendChild(opt);
      });
    }
  } catch (e) {
    console.error("Leagues fetch error:", e);
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
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; opacity:.6;">No alerts found</td></tr>`;
      return;
    }
    data.forEach(a => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${a.timestamp}</td>
        <td>${a.type || "-"}</td>
        <td>${a.league || "-"}</td>
        <td>${a.message || ""}</td>`;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error:", err);
    tbody.innerHTML = `<tr><td colspan="4" style="color:#ff6b6b;">Error loading alerts</td></tr>`;
  }
}

async function exportToExcel() {
  const type = document.getElementById("filter-type").value;
  const league = document.getElementById("filter-league").value;
  const from = document.getElementById("filter-from").value;
  const to = document.getElementById("filter-to").value;
  let url = `/api/alerts/export?`;
  if (type) url += `type=${encodeURIComponent(type)}&`;
  if (league) url += `league=${encodeURIComponent(league)}&`;
  if (from) url += `date_from=${from}&`;
  if (to) url += `date_to=${to}&`;

  try {
    const a = document.createElement("a");
    a.href = url;
    a.download = "EURO_GOALS_ALERTS.xlsx";
    a.click();
  } catch (err) {
    console.error("Export error:", err);
    alert("Export failed.");
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
document.getElementById("export-btn").addEventListener("click", exportToExcel);

window.addEventListener("DOMContentLoaded", async () => {
  await fetchLeagues();
  await loadAlerts();
});
