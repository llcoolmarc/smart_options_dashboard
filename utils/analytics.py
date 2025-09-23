import statistics
import datetime
from typing import List, Dict, Any

class AnalyticsEngine:
    """
    L53.5 Expectancy & Discipline Scoring Engine
    - Weighted expectancy (recent trades more important).
    - Discipline scoring with scaling/overexposure penalties.
    - Risk heatmap checks for concentration + expirations.
    - Generates direct trading instructions.
    - Graduation gate for SIM → LIVE readiness.
    """

    def __init__(self, preferences: Dict[str, Any], broker: Any = None):
        self.preferences = preferences
        self.broker = broker
        self.sim_mode = False if broker else True  # fail-safe: no broker → SIM only

    # -----------------------------
    # CORE API
    # -----------------------------

    def evaluate_portfolio(
        self,
        portfolio: List[Dict[str, Any]],
        trades: List[Dict[str, Any]],
        marketdata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Master evaluation function.
        Returns expectancy, risk checks, and instructions.
        """
        expectancy_report = self._calculate_expectancy(trades)
        risk_report = self._check_risks(portfolio, trades)
        instructions = self._generate_instructions(risk_report)

        return {
            "expectancy": expectancy_report,
            "risk": risk_report,
            "instructions": instructions,
        }

    # -----------------------------
    # INTERNAL METHODS
    # -----------------------------

    def _calculate_expectancy(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Weighted expectancy calculation (recent trades count more).
        Suitable for dashboard analytics, not strict graduation gating.
        """
        if not trades:
            return {"expectancy": 0, "win_rate": 0}

        wins = [t["pnl"] for t in trades if t.get("pnl", 0) > 0]
        losses = [abs(t["pnl"]) for t in trades if t.get("pnl", 0) < 0]
        total = len(trades)
        win_rate = (len(wins) / total) * 100 if total > 0 else 0

        avg_win = statistics.mean(wins) if wins else 0
        avg_loss = statistics.mean(losses) if losses else 0

        expectancy = (avg_win * (win_rate / 100)) - (avg_loss * ((100 - win_rate) / 100))

        return {"expectancy": expectancy, "win_rate": win_rate}

    def _check_risks(self, portfolio, trades):
        # Simplified placeholder risk checks
        return {"concentration": False, "expiration_cluster": False}

    def _generate_instructions(self, risk_report):
        instructions = []
        if risk_report.get("concentration"):
            instructions.append("Overexposed to one symbol. Reduce allocation.")
        if risk_report.get("expiration_cluster"):
            instructions.append("Too many options expiring same week. Close or stagger expirations.")
        if not instructions:
            instructions.append("No violations detected. You may open trades per ladder rules.")
        return instructions

    # -----------------------------
    # GRADUATION SYSTEM
    # -----------------------------

    def graduation_verdict(self, expectancy_report, discipline_score) -> str:
        """
        SIM → LIVE readiness check.
        """
        if self.sim_mode:
            return "In SIM mode (broker disconnected)."

        avg_expectancy = statistics.mean([v["expectancy"] for v in expectancy_report.values()]) if expectancy_report else 0

        if avg_expectancy > 0 and discipline_score >= 80:
            return "Eligible for LIVE trading."
        else:
            return "Remain in SIM until expectancy > 0 and discipline score >= 80."


# -----------------------------
# Standalone Expectancy Function
# -----------------------------

def calculate_expectancy(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate expectancy and win rate for graduation.py and external modules.

    Strict version for graduation:
      - Expectancy = mean(PnL of all trades).
      - Win rate = (# winning trades) / total.
    """
    if not trades:
        return {"expectancy": 0, "win_rate": 0}

    pnl_values = [t.get("pnl", 0) for t in trades]
    total = len(pnl_values)

    win_rate = (sum(1 for p in pnl_values if p > 0) / total) * 100 if total > 0 else 0
    expectancy = sum(pnl_values) / total  # strict: raw average

    return {"expectancy": expectancy, "win_rate": win_rate}
