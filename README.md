# 📊 Defined-Risk Options Spreads Cockpit

A **Python + Dash** application that enforces strict risk management, discipline, and profitability before transitioning from **SIM → SANDBOX → LIVE** trading.  
Built for options traders who demand accountability and repeatability.

---

## 🚀 Features

- **Graduation Locks**  
  - ≥ 25 trades  
  - ≥ 15 clean sessions  
  - Expectancy > 0  
  - Win rate ≥ 55%  
  - ≤ 2 consecutive losers  

- **Sandbox Validation**  
  - ≥ 10 SANDBOX trades  
  - Positive expectancy before LIVE unlock  

- **Discipline AI**  
  - Continuous habit scoring and violation logging  

- **Market Filters**  
  - VIX, Fed events, earnings screens  

- **Scaling & Allocation**  
  - Contracts scaled with account size  
  - Risk and allocation gates enforced  

- **Broker Integration**  
  - Tastytrade sandbox / live endpoints  
  - Safe credential management via `.env`  

---

## 🛠️ Installation

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/smart_options_dashboard.git
cd smart_options_dashboard
---

## 🚀 Going LIVE

The cockpit enforces strict gates before allowing `USE_LIVE=true`.  
See [GOING_LIVE_CHECKLIST.md](GOING_LIVE_CHECKLIST.md) for the full pre-flight.

### Environment Keys
Define in `.env` (never commit this file):

```env
# Mode & safety
USE_LIVE=false
ALWAYS_DRY_RUN=true

# Sandbox creds (preferred for tests)
TT_SANDBOX_USER=your_sandbox_username
TT_SANDBOX_PASS=your_sandbox_password

# Live creds (enable only after graduation)
TT_LIVE_USER=your_live_username
TT_LIVE_PASS=your_live_password

# API endpoints (defaults exist; override only if needed)
TASTY_BASE_URL_SANDBOX=https://api.cert.tastytrade.com
TASTY_BASE_URL_LIVE=https://api.tastytrade.com
