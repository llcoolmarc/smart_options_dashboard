"""
utils/compliance.py

Compliance reporting utilities for Defined-Risk Spreads Cockpit.
Exports CSV summary of session-level violations including gatekeeper blocks.
"""

import csv
import os
from utils.journal import load_journal


def export_compliance_csv(path: str = "compliance_report.csv", journal_path: str = "trade_journal.json"):
    """
    Export compliance summary across all sessions into a CSV file.
    Columns: timestamp, mode, graduated, status, reason, scaling_violations,
             profitability_violations, total_violations
    """
    sessions = load_journal(journal_path)
    if not sessions:
        print("No journal entries found.")
        return None

    fieldnames = [
        "timestamp",
        "mode",
        "graduated",
        "status",
        "reason",
        "scaling_violations",
        "profitability_violations",
        "total_violations"
    ]

    try:
        with open(path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for session in sessions:
                audit = session.get("session_audit", {})
                row = {
                    "timestamp": session.get("timestamp"),
                    "mode": session.get("mode"),
                    "graduated": session.get("graduated"),
                    "status": session.get("status", "completed"),
                    "reason": session.get("reason", ""),
                    "scaling_violations": audit.get("scaling_violations", 0),
                    "profitability_violations": audit.get("profitability_violations", 0),
                    "total_violations": audit.get("total_violations", 0),
                }
                writer.writerow(row)

        print(f"✅ Compliance report exported to {path}")
        return path
    except Exception as e:
        print(f"❌ Failed to export compliance CSV: {e}")
        return None


def summarize_compliance(journal_path: str = "trade_journal.json"):
    """
    Quick console summary of compliance performance across sessions.
    """
    sessions = load_journal(journal_path)
    if not sessions:
        return "No sessions found."

    total = len(sessions)
    clean = sum(1 for s in sessions if s.get("session_audit", {}).get("total_violations", 0) == 0 and s.get("status") not in ["blocked_entry", "practice_violation"])
    scaling = sum(1 for s in sessions if s.get("session_audit", {}).get("scaling_violations", 0) > 0)
    profit = sum(1 for s in sessions if s.get("session_audit", {}).get("profitability_violations", 0) > 0)
    blocked = sum(1 for s in sessions if s.get("status") == "blocked_entry")
    practice = sum(1 for s in sessions if s.get("status") == "practice_violation")

    return (
        f"Total sessions: {total}\n"
        f"✅ Clean sessions: {clean} ({clean/total:.0%})\n"
        f"🚨 Scaling violations: {scaling} ({scaling/total:.0%})\n"
        f"🚨 Profitability violations: {profit} ({profit/total:.0%})\n"
        f"🚨 Gatekeeper blocks: {blocked} ({blocked/total:.0%})\n"
        f"⚠️ SIM practice oversize: {practice} ({practice/total:.0%})"
    )