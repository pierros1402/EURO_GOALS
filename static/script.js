// ==============================
// EURO_GOALS v6f - UI Controller
// ==============================

// 🟢 Εμφάνιση κατάστασης Render online/offline
async function checkServerStatus() {
    try {
        const res = await fetch("/");
        const data = await res.json();
        document.getElementById("status").textContent = data.message || "Online";
    } catch (err) {
        document.getElementById("status").textContent = "Offline ❌";
    }
}

// ⚽ Φόρτωση αγώνων (δοκιμαστική λειτουργία)
async function loadMatches() {
    const league = document.getElementById("league").value;
    const tbody = document.querySelector("#matchesTable tbody");

    tbody.innerHTML = "<tr><td colspan='4'>🔄 Φόρτωση αγώνων...</td></tr>";

    try {
        const res = await fetch(`/odds_bundle/${league}`);
        const data = await res.json();

        if (data.status === "ok") {
            tbody.innerHTML = "";
            data.data.slice(0, 10).forEach((m) => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${m.home_team || "-"}</td>
                    <td>${m.away_team || "-"}</td>
                    <td>${m.odds?.h2h?.[0] || "-"}</td>
                    <td>${m.odds?.h2h?.[1] || "-"}</td>
                    <td>${m.odds?.h2h?.[2] || "-"}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = `<tr><td colspan='4'>⚠️ ${data.message}</td></tr>`;
        }
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan='4'>❌ Σφάλμα φόρτωσης: ${err.message}</td></tr>`;
    }
}

// 📊 Εξαγωγή σε Excel (μελλοντικά)
function exportExcel() {
    alert("📁 Η εξαγωγή σε Excel θα ενεργοποιηθεί στην επόμενη έκδοση!");
}

// 🔄 Εκκίνηση
document.addEventListener("DOMContentLoaded", () => {
    checkServerStatus();
});
