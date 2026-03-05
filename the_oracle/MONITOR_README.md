# THE ORACLE - Monitor & Auto-Restart System

## 🔄 Monitorizare Automată

Sistemul verifică la fiecare oră dacă THE ORACLE rulează și îl repornește automat dacă s-a oprit.

---

## 📁 Fișiere

| Fișier | Descriere |
|--------|-----------|
| `monitor.py` | Script Python de monitorizare |
| `monitor.bat` | Batch file pentru Windows Task Scheduler |
| `output/monitor.log` | Log cu toate verificările |
| `oracle.pid` | File cu PID-ul procesului activ |

---

## ⚙️ Cum Funcționează

### 1. Verificare Proces
- Caută procese Python care rulează `orchestrator.py --continuous`
- Verifică dacă procesul răspunde (nu e blocat)
- Loghează statusul în `monitor.log`

### 2. Auto-Restart
**Dacă botul NU rulează:**
- ⚠️ Loghează alertă
- 🔄 Încearcă restart automat
- ✅ Confirmă dacă restartul a reușit
- ❌ Raportează eroare dacă nu

**Dacă botul rulează:**
- ✅ Confirmă status OK
- 📊 Loghează CPU și memorie
- 🕐 Așteaptă următoarea verificare

---

## 📅 Frecvență Verificări

| Tip | Frecvență | Acțiune |
|-----|-----------|---------|
| **Health Check** | La fiecare oră | Verifică dacă rulează + restart dacă e nevoie |
| **Status Report** | 08:00 și 20:00 | Raport sumar zilnic |

---

## 📊 Log-uri

**Locație:** `the_oracle/output/monitor.log`

**Format:**
```
[2026-03-03 23:00:00] ========================================
[2026-03-03 23:00:00] THE ORACLE - MONITOR CHECK STARTED
[2026-03-03 23:00:00] ========================================
[2026-03-03 23:00:01] [OK] THE ORACLE is RUNNING (PID: 12345)
[2026-03-03 23:00:02] [HEALTH] CPU: 2.5%, Memory: 45.3 MB
[2026-03-03 23:00:02] ========================================
[2026-03-03 23:00:02] MONITOR CHECK COMPLETED
[2026-03-03 23:00:02] ========================================
```

---

## 🚨 Scenarii

### ✅ Scenariul 1: Totul OK
```
[OK] THE ORACLE is RUNNING (PID: 12345)
[HEALTH] CPU: 1.2%, Memory: 42.1 MB
```
**Acțiune:** Niciuna, continuă monitorizarea

### ⚠️ Scenariul 2: Bot Oprit
```
[ALERT] THE ORACLE is NOT RUNNING!
[ACTION] Attempting restart...
[RESTART] THE ORACLE restarted with PID: 12346
[SUCCESS] Restart completed successfully
```
**Acțiune:** Restart automat executat

### ❌ Scenariul 3: Restart Eșuat
```
[ALERT] THE ORACLE is NOT RUNNING!
[ACTION] Attempting restart...
[ERROR] Restart failed: [detalii eroare]
[FAILED] Restart attempt failed
```
**Acțiune:** Va reîncerca la următoarea verificare (în 1 oră)

---

## 🔧 Comenzi Manuale

### Verificare manuală:
```bash
cd C:\Users\Claw\.openclaw\workspace
python the_oracle\monitor.py
```

### Verificare status MT5:
```bash
cd C:\Users\Claw\.openclaw\workspace
python mt5_trader\_check_mt5.py
```

### Restart manual:
```bash
cd C:\Users\Claw\.openclaw\workspace
python the_oracle\orchestrator.py --continuous --interval 15
```

---

## 📱 Notificări

**Vei primi notificare automat când:**
- ⚠️ Botul se oprește
- 🔄 Se execută un restart
- ❌ Restartul eșuează după multiple încercări
- ✅ Trade-uri sunt executate

---

## 🎯 Garantii

**NU există garanție 100%**, dar sistemul oferă:
- ✅ Verificare la fiecare oră
- ✅ Restart automat
- ✅ Log-uri complete
- ✅ Monitorizare resurse (CPU/memorie)

**Factori externi care pot afecta:**
- PC-ul A6 se închide sau intră în sleep
- MT5 se deconectează de la server
- Probleme de rețea
- Erori API (rare)

---

## 📞 Troubleshooting

**Q: Botul nu pornește după restart automat**
**A:** Verifică manual:
```bash
python the_oracle/orchestrator.py --continuous
```

**Q: Monitorul nu găsește botul deși rulează**
**A:** Verifică în Task Manager dacă există proces Python cu orchestrator.py

**Q: Vreau să opresc monitorizarea**
**A:** Șterge fișierul `.openclaw/cron/oracle.yaml` sau dezactivează din OpenClaw

---

*Ultima actualizare: 2026-03-03*
*THE ORACLE v4.0*
