// =========================================================
// EURO_GOALS v7.9 – Alert History JS
// =========================================================
// Φόρτωση & φιλτράρισμα ειδοποιήσεων (alerts)
// =========================================================

async function loadAlerts() {
  const type = document.getElementById("filter-type").value;
  const league = document.getElementById("filter-league").value;
  const from = document.getElementById("filter-from").value;
  const to = document.getElementById("filter-to").value;

  // Δημιουργία URL με παραμέτρους φίλτρου
  let url = `/api/alerts?`;
  if (type) url += `type=${encodeURIComponent(type)}&`;
  if (league) url += `league=${encodeURIComponent(league)}&`;
  if (from) url += `date_from=${from}&`;
  if (to) url += `date_to=${to}&`;

  // Φόρτωση δεδομένων από API
  try {
    const res = await fetch(url);
    const data = await res.json();
    const tbody = document.querySelector("#alerts-table tbody");
    tbody.innerHTML = "";

    if (!Array.isArray(data) || data.length === 0) {
      const empty = document.createElement("tr");
      empty.innerHTML = `<td colspan="4" style="text-align:center; opacity:0.6;">No alerts found</td>`;
      tbody.appendChild(empty);
      return;
    }

    data.forEach(alert => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${alert.timestamp}</td>
        <td>${alert.type}</td>
        <td>${alert.league || "-"}</td>
        <td>${alert.message}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.error("Error loading alerts:", err);
  }
}

// ---------------------------------------------------------
// Κουμπιά φίλτρου & καθαρισμού
// ---------------------------------------------------------
document.getElementById("filter-btn").addEventListener("click", loadAlerts);

document.getElementById("clear-btn").addEventListener("click", () => {
  document.getElementById("filter-type").value = "";
  document.getElementById("filter-league").value = "";
  document.getElementById("filter-from").value = "";
  document.getElementById("filter-to").value = "";
  loadAlerts();
});

// ---------------------------------------------------------
// Αυτόματη φόρτωση με το άνοιγμα της σελίδας
// ---------------------------------------------------------
window.addEventListener("DOMContentLoaded", loadAlerts);
