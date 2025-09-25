
# 🚀 Going LIVE Checklist — Defined‑Risk Options Spreads Cockpit

> Keep this one‑pager in your repo root as `GOING_LIVE_CHECKLIST.md`. Use it **every time** before flipping `USE_LIVE=true`.

---

## 0) Policy Gates (must all be true)
- [ ] Trades ≥ **25** (journaled)
- [ ] Clean sessions ≥ **15**
- [ ] Expectancy **> 0**
- [ ] Discipline score **≥ 70**
- [ ] No **HIGH‑severity** Alerts in the last session
- [ ] CI green (tests/lint/security) on `main`

> If any box is unchecked → **stay in SIM/SANDBOX**.

---

## 1) Environment & Secrets
- `.env` (never committed) contains only **non‑rotated** secrets. If this file was ever shared or zipped, **rotate**.
- Required keys:
  ```env
  # Mode & safety
  USE_LIVE=false
  ALWAYS_DRY_RUN=true

  # Sandbox creds (preferred for tests)
  TT_SANDBOX_USER=...
  TT_SANDBOX_PASS=...

  # Live creds (for step 5+ only; do NOT use until gates pass)
  TT_LIVE_USER=...
  TT_LIVE_PASS=...

  # API endpoints (defaults exist; override only if needed)
  TASTY_BASE_URL_SANDBOX=https://api.cert.tastytrade.com
  TASTY_BASE_URL_LIVE=https://api.tastytrade.com
  ```

- Verify `.gitignore` includes:
  ```gitignore
  .env
  data/*token*.json
  data/logs/
  ```

---

## 2) CI / Local Pre‑flight
- [ ] Install dev deps: `python -m pip install -U pytest black flake8 bandit`
- [ ] Run tests: `pytest -q`
- [ ] Lint/format: `black --check . && flake8`
- [ ] Security scan: `bandit -q -r .`
- [ ] Manual smoke (no creds required): `python app_dash.py` then visit `http://127.0.0.1:8050/`

---

## 3) Graduation Proof in UI
Open the cockpit → verify these cards:
- **Graduation**: shows eligible / sandbox passed (or reasons).
- **Expectancy**: positive value.
- **Discipline**: ≥ 70 (no violations).
- **Alerts**: none at HIGH severity.
- **Export**: click **Export Compliance CSV** → `data/export/compliance_snapshot.csv` is created.

Keep the CSV with your session notes.

---

## 4) SANDBOX Validation (read‑write path with dry‑run on)
1. Ensure `.env`:
   ```env
   USE_LIVE=false
   ALWAYS_DRY_RUN=true
   ```
2. Launch cockpit and simulate an order (it will be **blocked** by dry‑run).
3. Confirm coaching/scaling/filters react as expected and no errors appear in the UI/logs.

---

## 5) First LIVE Connection (NO orders)
1. Flip in `.env`:
   ```env
   USE_LIVE=true
   ALWAYS_DRY_RUN=true
   ```
2. Relaunch cockpit. **Broker** card should read *LIVE (dry‑run)* or be **forced to SANDBOX** if gates not met.
3. Verify accounts/positions fetch without placing orders.

> If downgraded to SANDBOX, fix the gate reasons and repeat.

---

## 6) First LIVE Order (tiny, defined‑risk)
1. Keep `USE_LIVE=true` but set:
   ```env
   ALWAYS_DRY_RUN=false
   ```
2. Place **one** minimal‑size defined‑risk spread, within ladder limits.
3. Verify fill, exposure, and Alerts remain green.
4. Export a new compliance CSV.

---

## 7) Observation Window (48–72h)
- [ ] Maintain smallest size; max **2** concurrent spreads; diversify across **2–3** tickers.
- [ ] If any **HIGH** alert triggers → **halt new entries 24h**, remediate root cause, export CSV.

---

## 8) Ramp Rules (only after clean stability)
- Week 1 → 1× smallest unit, ≤2 concurrent spreads.
- Week 2 → If expectancy still **> 0** and discipline **≥ 80**, then 2× units.
- Never exceed ladder caps or 20% per‑symbol open risk.

---

## 9) Rollback Triggers (flip back to dry‑run immediately)
- Expectancy turns **negative** over last 10 trades.
- Discipline score **< 70**.
- ≥ 2 **HIGH** alerts in a single session.
- Any auth or order‑placement anomaly.

**Rollback sequence:** Close risk per exit plan → `ALWAYS_DRY_RUN=true` → resume SANDBOX until metrics recover.

---

## 10) Documentation & Audit
- Keep `GOING_LIVE_CHECKLIST.md` in the repo root.
- Attach the latest `data/export/compliance_snapshot.csv` to your session notes.
- README sections: Architecture overview, Env keys, “Going LIVE Checklist”, Rollback protocol.

---

## Notes
- **Broker guard** in `utils/broker.py` *forces SANDBOX* if graduation/sandbox checks fail, even when `USE_LIVE=true`.
- **Alerts vs Discipline AI** separation prevents duplicate noise: Alerts = HIGH only; AI = non‑critical notes + Action Plan.
