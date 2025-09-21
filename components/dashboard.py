from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from coaching import strategies
from utils.graduation import check_graduation  # NEW

console = Console()

def render_dashboard(report: dict):
    """
    Render the Smart Options Dashboard.
    Shows expectancy, discipline, risks, instructions, graduation, and best strategy.
    """
    console.clear()
    console.rule("[bold cyan]Smart Options Dashboard — L53.5 Analytics")

    # -------------------------------
    # Graduation Gate (Phase 13 lock)
    # -------------------------------
    grad_status = check_graduation()
    grad_msg = grad_status["message"]
    grad_color = "green" if grad_status["graduated"] else "bold red blink"

    console.print(Panel.fit(
        f"[{grad_color}]{grad_msg}[/]\n\n"
        "What this means:\n"
        "- You must prove consistency before funding LIVE.\n"
        "- Requirements: ≥25 trades, ≥15 clean sessions, Expectancy > 0, Win Rate ≥ 55%, ≤2 consecutive losers.\n"
        "- This cockpit will remain locked until these are met.",
        title="🎓 Graduation Lock"
    ))

    # -------------------------------
    # Expectancy Report Table
    # -------------------------------
    table = Table(title="Expectancy Report (Weighted Rolling)")
    table.add_column("Symbol")
    table.add_column("Expectancy")
    table.add_column("Realized")
    table.add_column("Discipline Gap")
    table.add_column("Status")

    violation_detected = False

    for sym, data in report["expectancy_report"].items():
        status_style = "green"
        if data["status"] == "block_new":
            status_style = "bold red blink"
            violation_detected = True
        table.add_row(
            sym,
            str(data["expectancy"]),
            str(data["realized"]),
            str(data["discipline_gap"]),
            f"[{status_style}]{data['status']}[/]"
        )
    console.print(table)

    # -------------------------------
    # Discipline Score
    # -------------------------------
    score_color = "green" if report['discipline_score'] >= 80 else "bold red blink"
    if report['discipline_score'] < 80:
        violation_detected = True
    console.print(Panel.fit(
        f"Discipline Score: [bold {score_color}]{report['discipline_score']}[/]",
        title="📊 Discipline"
    ))

    # -------------------------------
    # Risk Heatmap
    # -------------------------------
    risks = "\n".join(report["risk_report"].get("details", [])) or "No major risks detected."
    if report["risk_report"].get("over_concentration") or report["risk_report"].get("expiration_cluster"):
        violation_detected = True
        risks = f"[bold red blink]{risks}[/]"
    console.print(Panel.fit(risks, title="⚠️ Risk Heatmap"))

    # -------------------------------
    # Trade Instructions
    # -------------------------------
    instr = "\n".join(report["instructions"])
    console.print(Panel.fit(instr, title="📝 Trade Instructions"))

    # -------------------------------
    # Best Strategy Suggestion
    # -------------------------------
    strat = strategies.best_strategy(
        report["expectancy_report"],
        report.get("portfolio", []),
        report.get("marketdata", {}),
        report.get("preferences", {})
    )
    console.print(Panel.fit(
        f"[bold green]{strat['coaching']}[/]",
        title="📈 Best Strategy"
    ))

    # -------------------------------
    # Alerts
    # -------------------------------
    if violation_detected or not grad_status["graduated"]:
        console.print("[bold red reverse blink] 🚨 DISCIPLINE ALERT: Action Required 🚨 [/]")
        print("\a")  # terminal beep

    console.rule("[bold cyan]End of Report")
