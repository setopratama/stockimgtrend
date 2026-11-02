"""btop-style Terminal UI Dashboard for Stock Image Trend Research Pipeline.

Uses Rich for high-contrast neon modular panels, progress gauges,
and real-time analysis streaming.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional

from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live

console = Console()

def render_gauge(value: float, max_val: float = 100.0, length: int = 15, color: str = "cyan") -> str:
    """Render a btop-style ASCII progress gauge bar."""
    filled = int((value / max_val) * length)
    filled = max(0, min(length, filled))
    bar = "█" * filled + "░" * (length - filled)
    return f"[{color}][{bar}][/] [bold white]{value:.0f}%[/]"

class BtopDashboard:
    def __init__(self, keyword: str):
        self.keyword = keyword
        self.status = "INITIALIZING"
        self.log_messages = ["Pipeline siap dieksekusi..."]
        self.gtrends_data = {}
        self.tavily_data = {}
        self.adobe_data = {}
        self.final_result = {}
        self.start_time = datetime.now()

    def add_log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {msg}")
        if len(self.log_messages) > 4:
            self.log_messages.pop(0)

    def on_progress(self, stage: str, message: str, data: Optional[Dict[str, Any]] = None):
        self.add_log(message)
        if stage == "GTRENDS":
            self.status = "FETCHING TRENDS"
        elif stage == "GTRENDS_DONE" and data:
            self.gtrends_data = data
            self.status = "ANALYZING MARKET"
        elif stage == "TAVILY":
            self.status = "RESEARCHING TAVILY"
        elif stage == "TAVILY_DONE" and data:
            self.tavily_data = data
            self.status = "INSPECTING ADOBE STOCK"
        elif stage == "ADOBESTOCK":
            self.status = "CHECKING COMPETITION"
        elif stage == "ADOBESTOCK_DONE" and data:
            self.adobe_data = data
            self.status = "AI SYNTHESIS"
        elif stage == "SYNTHESIS":
            self.status = "GENERATING BRIEF"
        elif stage == "SYNTHESIS_DONE" and data:
            self.final_result = data
            self.status = "EXPORTING"
        elif stage == "EXPORT_DONE":
            self.status = "SAVING TO DB"
        elif stage == "DB_SAVED":
            self.status = "COMPLETED"

    def render(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="metrics", size=11),
            Layout(name="matrix", size=7),
            Layout(name="brief", size=10),
            Layout(name="footer", size=5)
        )

        # Header
        current_time = datetime.now().strftime("%H:%M:%S")
        status_color = "green" if self.status == "COMPLETED" else "yellow"
        header_text = Text.from_markup(
            f" [bold magenta]stockimgtrend[/] ─ "
            f"[[bold {status_color}]{self.status}[/]] ─ "
            f"Target: [bold cyan]\"{self.keyword}\"[/] ─ "
            f"Time: [dim]{current_time}[/]"
        )
        layout["header"].update(Panel(header_text, style="bold bright_blue"))

        # Metrics (3 Columns: Google Trends, Tavily Intel, Adobe Stock)
        layout["metrics"].split_row(
            Layout(name="col_gt"),
            Layout(name="col_tav"),
            Layout(name="col_stock")
        )

        # 1. Google Trends Panel
        gt_score = self.gtrends_data.get("trend_score", 0.0)
        gt_growth = self.gtrends_data.get("growth_percentage", "Menunggu...")
        rising = self.gtrends_data.get("rising_queries", [])
        rising_str = ", ".join(rising[:3]) if rising else "Mencari query..."
        gt_body = Group(
            Text.from_markup(f"Velocity : {render_gauge(gt_score, color='green')}"),
            Text.from_markup(f"Growth   : [bold yellow]{gt_growth}[/]"),
            Text.from_markup(f"Region   : [cyan]{self.gtrends_data.get('region', 'Global')}[/]"),
            Text.from_markup(f"Queries  : [dim]{rising_str[:38]}[/]")
        )
        layout["metrics"]["col_gt"].update(
            Panel(gt_body, title="[bold green]📈 GOOGLE TRENDS[/]", border_style="green")
        )

        # 2. Tavily Panel
        tav_score = self.tavily_data.get("tavily_score", 0.0)
        tav_refs = self.tavily_data.get("total_references", 0)
        tav_summary = self.tavily_data.get("summary", "Menghubungi Tavily API...")[:95]
        tav_body = Group(
            Text.from_markup(f"Market   : {render_gauge(tav_score, color='cyan')}"),
            Text.from_markup(f"Sources  : [bold white]{tav_refs}[/] artikel industri"),
            Text.from_markup(f"Insights : [dim]{tav_summary}...[/]")
        )
        layout["metrics"]["col_tav"].update(
            Panel(tav_body, title="[bold cyan]🌐 TAVILY MARKET INTEL[/]", border_style="cyan")
        )

        # 3. Adobe Stock Panel
        stock_assets = self.adobe_data.get("total_results", 0)
        stock_level = self.adobe_data.get("competition_level", "Memeriksa...")
        scoring_data = self.final_result.get("scoring", {}).get("breakdown", {})
        gap_score = scoring_data.get("stock_gap_score", 0.0)
        stock_body = Group(
            Text.from_markup(f"Gap Score: {render_gauge(gap_score, color='magenta')}"),
            Text.from_markup(f"Indexed  : [bold white]~{stock_assets:,}[/] aset"),
            Text.from_markup(f"Saturation: [bold yellow]{stock_level}[/]"),
            Text.from_markup(f"Security  : [bold green]100% Tavily Cloud Proxy[/]")
        )
        layout["metrics"]["col_stock"].update(
            Panel(stock_body, title="[bold magenta]📦 ADOBE STOCK (via Tavily)[/]", border_style="magenta")
        )

        # Opportunity Score Matrix Table
        matrix_table = Table(expand=True, box=None)
        matrix_table.add_column("Keyword Target", style="bold cyan")
        matrix_table.add_column("G-Trends (40%)", justify="center", style="green")
        matrix_table.add_column("Market (30%)", justify="center", style="cyan")
        matrix_table.add_column("Gap (30%)", justify="center", style="magenta")
        matrix_table.add_column("TOTAL SCORE", justify="center", style="bold white")
        matrix_table.add_column("Verdict", style="bold yellow")

        if self.final_result:
            sc = self.final_result.get("scoring", {})
            total = sc.get("total_score", 0.0)
            score_star = "⭐ " if total >= 80 else "✨ "
            matrix_table.add_row(
                self.keyword,
                f"{gt_score:.1f}",
                f"{tav_score:.1f}",
                f"{gap_score:.1f}",
                f"[bold green]{score_star}{total}[/]",
                f"[bold cyan]{sc.get('recommendation', 'N/A')}[/]"
            )
        else:
            matrix_table.add_row(
                self.keyword,
                f"{gt_score:.1f}" if gt_score else "...",
                f"{tav_score:.1f}" if tav_score else "...",
                "...",
                "Analisis Berjalan...",
                "Menghitung..."
            )

        layout["matrix"].update(
            Panel(matrix_table, title="[bold bright_white]🎯 OPPORTUNITY SCORE MATRIX[/]", border_style="bright_blue")
        )

        # Actionable Brief & Prompt Recipe Preview
        brief = self.final_result.get("actionable_brief", {})
        title_sug = brief.get("title_suggestion", "Sedang disusun oleh OpenRouter AI...")
        prompt_rec = brief.get("prompt_recipe", "Menunggu resep prompt visual...")
        types = ", ".join(brief.get("recommended_asset_types", ["Photo", "Generative AI"]))
        brief_body = Group(
            Text.from_markup(f"[bold yellow]Commercial Title :[/] [white]{title_sug}[/]"),
            Text.from_markup(f"[bold yellow]Asset Formats    :[/] [cyan]{types}[/]"),
            Text.from_markup(f"[bold yellow]AI Prompt Recipe :[/] [dim italic]{prompt_rec[:140]}...[/]")
        )
        layout["brief"].update(
            Panel(brief_body, title="[bold bright_yellow]🎨 ACTIONABLE CREATIVE BRIEF (AI PREVIEW)[/]", border_style="yellow")
        )

        # Footer & Log stream
        log_text = "\n".join(self.log_messages)
        exported = self.final_result.get("exported_file", "")
        db_id = self.final_result.get("db_id")
        export_status = f"[bold green]✔ Laporan: {exported}[/]" if exported else "[dim]Menyimpan otomatis ke docs/reports/...[/]"
        db_status = f"[bold cyan]💾 SQLite: data/stockimgtrend.db (ID #{db_id})[/]" if db_id else "[dim]Menyimpan ke SQLite...[/]"
        footer_group = Group(
            Text.from_markup(f"[bold dim]ACTIVITY LOG:[/]\n{log_text}"),
            Text.from_markup(f"[bold magenta]OUTPUT:[/] {export_status} | {db_status}")
        )
        layout["footer"].update(Panel(footer_group, border_style="dim"))

        return layout
