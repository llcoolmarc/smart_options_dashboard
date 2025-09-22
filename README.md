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
