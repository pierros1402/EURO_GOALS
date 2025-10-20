# ⚽ EURO_GOALS v6f – Smart Money Update

## 🔍 Overview
**EURO_GOALS v6f** είναι η πιο πρόσφατη έκδοση του project με πλήρη σύνδεση backend–frontend και νέο module:
**Smart Money Detector (asian_reader.py)**, που ανιχνεύει έντονες μεταβολές αποδόσεων στις ασιατικές αγορές.

---

## 🧩 Modules
| Αρχείο | Περιγραφή |
|--------|------------|
| `EURO_GOALS_v6f_debug.py` | Κύριο backend (FastAPI server + UI routes) |
| `asian_reader.py` | Smart Money Detector με αυτόματη ανανέωση (κάθε 5’ λεπτά) |
| `/templates/index.html` | Web UI (κουμπί 💰 Smart Money + πίνακας + ώρα τελευταίας ενημέρωσης) |
| `/static/` | CSS, εικόνες, icons (προαιρετικά) |

---

## 🚀 Features
- 💰 Smart Money Live Table  
- 🔁 Αυτόματη ανανέωση κάθε 5 λεπτά (background thread)  
- 🕒 Εμφάνιση “Τελευταίας ενημέρωσης” στο UI  
- ✅ Έτοιμο για Render deployment (FastAPI + Jinja2)  
- 📊 Εξαγωγή αγώνων σε Excel  
- 🌍 Πλήρως συμβατό με GitHub και Render free plan  

---

## ⚙️ Run Locally
```bash
uvicorn EURO_GOALS_v6f_debug:app --reload
