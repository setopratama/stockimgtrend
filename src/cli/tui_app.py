"""Interactive btop-style Fullscreen TUI Application powered by Textual.

Features true btop aesthetics:
- Live process animations (braille spinners, frequency wave bars, pulsating indicators).
- 100% keyboard-driven UI (no clumsy desktop block buttons).
- Modular neon borders and real-time telemetry gauges.
- Shortcuts:
  [a]: Auto Discovery
  [k]: Ketik Keyword (sleek modal prompt)
  [g]: Gen Nanobanana Master Prompt
  [h]: Riwayat SQLite (keyboard-navigated viewer)
  [c]: Clear Log
  [q]: Quit
"""

import os
import sys
import json
import itertools
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Header,
    Footer,
    Static,
    Input,
    DataTable,
    RichLog,
    Label
)
from rich.text import Text

from src.pipelines.trend_pipeline import TrendPipeline
from src.utils.db import list_recent_researches

# Animation frame sets for btop-style telemetry
BRAILLE_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
BRAILLE_WAVE = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
AUDIO_WAVE = [" ▂▃", "▂▃▄", "▃▄▅", "▄▅▆", "▅▆▇", "▆▇█", "▇█▇", "█▇▆", "▇▆▅", "▆▅▄", "▅▄▃", "▄▃▂", "▃▂ "]


# --- MODAL SCREEN: SLEEK KEYWORD INPUT DIALOG ---
class KeywordModal(ModalScreen[Optional[str]]):
    """Pure keyboard-driven minimal dialog for entering a custom target keyword."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Batal", priority=True),
    ]

    DEFAULT_CSS = """
    KeywordModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.7);
    }
    #modal-container {
        width: 68;
        height: auto;
        border: round #00f0ff;
        background: #111827;
        padding: 1 2;
    }
    #modal-title {
        text-align: center;
        text-style: bold;
        color: #00f0ff;
        margin-bottom: 1;
    }
    #keyword-input {
        background: #1f2937;
        border: tall #374151;
        color: #ffffff;
        margin-bottom: 1;
    }
    #modal-footer {
        text-align: center;
        color: #9ca3af;
        text-style: italic;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Label("┌─ 🎯 INPUT TARGET KEYWORD ─────────────────────────────────┐", id="modal-title")
            yield Input(
                placeholder="Ketik topik visual... (misal: bio architecture urban, agritech robot)",
                id="keyword-input"
            )
            yield Static("[bold cyan][Enter][/] Mulai Analisis  •  [bold red][Esc][/] Batal", id="modal-footer")

    def on_mount(self) -> None:
        self.query_one("#keyword-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        self.dismiss(val if val else None)

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)


# --- MODAL SCREEN: KEYBOARD-DRIVEN SQLITE HISTORY VIEWER ---
class HistoryModal(ModalScreen[None]):
    """Pure keyboard-driven viewer displaying research records stored in SQLite."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Tutup", priority=True),
        Binding("q", "dismiss_modal", "Tutup", priority=True),
        Binding("enter", "dismiss_modal", "Pilih", priority=True),
    ]

    DEFAULT_CSS = """
    HistoryModal {
        align: center middle;
        background: rgba(0, 0, 0, 0.75);
    }
    #history-box {
        width: 90%;
        height: 82%;
        border: round #a855f7;
        background: #0f141c;
        padding: 1 2;
    }
    #history-title {
        text-align: center;
        text-style: bold;
        color: #c084fc;
        margin-bottom: 1;
    }
    #history-table {
        height: 1fr;
        background: #090d13;
        border: solid #27272a;
    }
    #history-footer {
        text-align: center;
        color: #a1a1aa;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="history-box"):
            yield Label("┌─ 📚 RIWAYAT RISET STOCK IMAGE (SQLite: data/stockimgtrend.db) ─┐", id="history-title")
            yield DataTable(id="history-table")
            yield Static(
                "[bold cyan][↑ / ↓][/] Navigasi Baris  •  [bold yellow][Enter / Esc / q][/] Tutup Viewer",
                id="history-footer"
            )

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Keyword", "Total Skor", "Rekomendasi", "Aset Indeks", "Nanobanana", "Waktu Riset")
        
        records = list_recent_researches(limit=35)
        for r in records:
            nano = "✔ Siap" if r.get("nanobanana_prompt") else "—"
            table.add_row(
                str(r.get("id", "")),
                str(r.get("keyword", "")),
                f"{r.get('total_score', 0):.1f}",
                str(r.get("recommendation", "")),
                f"{r.get('indexed_assets', 0):,}",
                nano,
                str(r.get("created_at", ""))[:16]
            )
        table.focus()

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)


# --- MAIN FULLSCREEN TUI APPLICATION ---
class StockImgTrendApp(App):
    """Fullscreen btop-style Stock Image Trend Research & Nanobanana Studio TUI."""

    TITLE = "stockimgtrend"
    SUB_TITLE = "btop Visual Intelligence & Nanobanana Studio"

    BINDINGS = [
        Binding("a", "auto_discovery", "Auto Discovery", priority=True),
        Binding("k", "input_keyword", "Ketik Keyword", priority=True),
        Binding("g", "generate_nanobanana", "Gen Nanobanana", priority=True),
        Binding("h", "show_history", "Riwayat (DB)", priority=True),
        Binding("c", "clear_log", "Clear Log"),
        Binding("q", "quit", "Keluar", priority=True),
        Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
    ]

    CSS = """
    Screen {
        background: #090d16;
        color: #e2e8f0;
    }
    #top-status-bar {
        height: 3;
        background: #0f172a;
        border-bottom: heavy #1e293b;
        padding: 0 1;
        content-align: left middle;
    }
    #body-container {
        height: 1fr;
    }
    #left-pane {
        width: 48%;
        height: 100%;
        border-right: heavy #1e293b;
        padding: 0 1;
    }
    #right-pane {
        width: 52%;
        height: 100%;
        padding: 0 1;
    }
    .btop-card {
        background: #0f172a;
        border: round #38bdf8;
        padding: 1;
        margin-bottom: 1;
        height: auto;
    }
    #card-gt {
        border: round #10b981;
    }
    #card-tav {
        border: round #06b6d4;
    }
    #card-stock {
        border: round #ec4899;
    }
    #card-nano {
        background: #0f172a;
        border: round #eab308;
        padding: 1;
        height: 1fr;
        margin-top: 1;
    }
    .card-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #matrix-table {
        height: 9;
        margin-bottom: 1;
        background: #090d16;
        border: round #3b82f6;
    }
    #activity-log {
        height: 9;
        background: #020617;
        border: solid #1e293b;
        padding: 0 1;
    }
    #prompt-display {
        height: 1fr;
        overflow-y: scroll;
    }
    """

    def __init__(self, pipeline: TrendPipeline, initial_keyword: Optional[str] = None):
        super().__init__()
        self.pipeline = pipeline
        self.initial_keyword = initial_keyword
        self.active_result: Optional[Dict[str, Any]] = None
        self.is_busy = False
        self.current_stage = "IDLE"
        self.current_keyword = initial_keyword or "—"
        self.anim_tick = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        # Top Live Telemetry Bar
        yield Static(id="top-status-bar")

        with Horizontal(id="body-container"):
            # LEFT PANE: 3 Modular btop Telemetry Cards + Activity Log
            with Vertical(id="left-pane"):
                with Container(classes="btop-card", id="card-gt"):
                    yield Label("┌─ 📈 GOOGLE TRENDS DISCOVERY ───────────────────────┐", classes="card-title", id="lbl-gt")
                    yield Static("Menunggu perintah riset...", id="content-gt")

                with Container(classes="btop-card", id="card-tav"):
                    yield Label("┌─ 🌐 TAVILY MARKET INTEL (Cloud Proxy) ─────────────┐", classes="card-title", id="lbl-tav")
                    yield Static("Menunggu perintah riset...", id="content-tav")

                with Container(classes="btop-card", id="card-stock"):
                    yield Label("┌─ 📦 ADOBE STOCK COMPETITION GAP (via Tavily) ──────┐", classes="card-title", id="lbl-stock")
                    yield Static("Menunggu perintah riset...", id="content-stock")

                yield Label("┌─ 💻 REAL-TIME SYSTEM ACTIVITY LOG ──────────────────┐", classes="card-title", id="lbl-log")
                yield RichLog(id="activity-log", highlight=True, markup=True)

            # RIGHT PANE: Opportunity Score Matrix & Nanobanana Studio Card
            with Vertical(id="right-pane"):
                yield Label("┌─ 🎯 OPPORTUNITY SCORE MATRIX / LEADERBOARD ─────────┐", classes="card-title", id="lbl-matrix")
                yield DataTable(id="matrix-table")

                with Container(id="card-nano"):
                    yield Label("┌─ 🍌 NANOBANANA STUDIO: Master Prompt & Tema Kuat ───┐", classes="card-title", id="lbl-nano")
                    yield Static(
                        "[dim]Tekan [bold cyan][a][/] untuk Auto Discovery atau [bold yellow][g][/] untuk meracik prompt Nanobanana dari riset aktif.[/]",
                        id="prompt-display"
                    )

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#matrix-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Target Topic", "Trends", "Market", "Gap", "TOTAL", "Verdict")
        
        log = self.query_one("#activity-log", RichLog)
        log.write("[bold green]✔ stockimgtrend btop TUI initialized![/]")
        log.write("   [bold cyan][a][/] Auto Discovery   [bold cyan][k][/] Ketik Keyword   [bold yellow][g][/] Gen Nanobanana   [bold magenta][h][/] Riwayat")

        # Start 100ms telemetry animation loop
        self.set_interval(0.12, self._tick_animation)

        if self.initial_keyword:
            self.start_analysis_worker(self.initial_keyword)

    def _tick_animation(self) -> None:
        """btop dynamic process animation ticker."""
        self.anim_tick += 1
        spin = BRAILLE_SPINNER[self.anim_tick % len(BRAILLE_SPINNER)]
        wave = BRAILLE_WAVE[self.anim_tick % len(BRAILLE_WAVE)]
        audio = AUDIO_WAVE[self.anim_tick % len(AUDIO_WAVE)]

        # Top status bar animation
        if self.is_busy:
            status_markup = (
                f" [bold red blink]● PROCESSING[/] [bold white]{spin}[/] ─ "
                f"Target: [bold cyan]\"{self.current_keyword}\"[/] ─ "
                f"Stage: [bold yellow]{self.current_stage}[/] ─ "
                f"Activity: [bold green]{audio}[/]"
            )
        else:
            status_markup = (
                f" [bold green]● READY[/] ─ "
                f"Target: [bold white]\"{self.current_keyword}\"[/] ─ "
                f"Stage: [dim]IDLE[/] ─ "
                f"Shortcuts: [bold cyan][a][/] Auto  [bold cyan][k][/] Keyword  [bold yellow][g][/] Nanobanana  [bold magenta][h][/] Riwayat"
            )
        self.query_one("#top-status-bar", Static).update(status_markup)

        # Pulse active panel title with wave animation when working
        if self.is_busy:
            if "GTRENDS" in self.current_stage:
                self.query_one("#lbl-gt", Label).update(f"┌─ 📈 GOOGLE TRENDS [{wave} FETCHING {audio}] ─────────────┐")
            elif "TAVILY" in self.current_stage:
                self.query_one("#lbl-tav", Label).update(f"┌─ 🌐 TAVILY MARKET INTEL [{wave} CRAWLING {audio}] ──────┐")
            elif "ADOBE" in self.current_stage:
                self.query_one("#lbl-stock", Label).update(f"┌─ 📦 ADOBE STOCK GAP [{wave} CHECKING CLOUD {audio}] ────┐")
            elif "SYNTHESIS" in self.current_stage or "NANO" in self.current_stage:
                self.query_one("#lbl-nano", Label).update(f"┌─ 🍌 NANOBANANA STUDIO [{wave} PROMPT TUNING {audio}] ────┐")
        else:
            self.query_one("#lbl-gt", Label).update("┌─ 📈 GOOGLE TRENDS DISCOVERY ───────────────────────┐")
            self.query_one("#lbl-tav", Label).update("┌─ 🌐 TAVILY MARKET INTEL (Cloud Proxy) ─────────────┐")
            self.query_one("#lbl-stock", Label).update("┌─ 📦 ADOBE STOCK COMPETITION GAP (via Tavily) ──────┐")
            self.query_one("#lbl-nano", Label).update("┌─ 🍌 NANOBANANA STUDIO: Master Prompt & Tema Kuat ───┐")

    def log_msg(self, msg: str):
        log = self.query_one("#activity-log", RichLog)
        ts = datetime.now().strftime("%H:%M:%S")
        log.write(f"[dim]{ts}[/] {msg}")

    # --- ACTION HANDLERS ---
    def action_input_keyword(self) -> None:
        """Shortcut [k]: Open sleek dialog to input a keyword."""
        if self.is_busy:
            self.notify("Sistem sedang memproses riset aktif!", severity="warning")
            return

        def handle_keyword(kw: Optional[str]):
            if kw:
                self.start_analysis_worker(kw)

        self.push_screen(KeywordModal(), handle_keyword)

    def action_auto_discovery(self) -> None:
        """Shortcut [a]: Run autonomous market discovery."""
        if self.is_busy:
            self.notify("Sistem sedang memproses riset aktif!", severity="warning")
            return
        self.start_auto_discovery_worker()

    def action_generate_nanobanana(self) -> None:
        """Shortcut [g]: Generate Nanobanana Master Prompt for currently loaded result."""
        if self.is_busy:
            self.notify("Tunggu proses aktif selesai!", severity="warning")
            return
        if not self.active_result:
            self.notify("Belum ada data riset aktif. Tekan [a] atau [k] terlebih dahulu!", severity="warning")
            return
        self.start_nanobanana_worker()

    def action_show_history(self) -> None:
        """Shortcut [h]: Display SQLite database history modal."""
        self.push_screen(HistoryModal())

    def action_clear_log(self) -> None:
        """Shortcut [c]: Clear activity log."""
        self.query_one("#activity-log", RichLog).clear()

    # --- BACKGROUND WORKERS ---
    def start_analysis_worker(self, keyword: str):
        self.is_busy = True
        self.current_keyword = keyword
        self.current_stage = "STARTING"
        self.log_msg(f"[bold cyan]Memulai analisis target:[/] [bold white]\"{keyword}\"[/]")
        self.run_pipeline_worker(keyword)

    @work(thread=True)
    def run_pipeline_worker(self, keyword: str):
        def on_prog(stage: str, msg: str, data=None):
            self.app.call_from_thread(self._handle_pipeline_progress, stage, msg, data)

        try:
            res = self.pipeline.run(keyword=keyword, on_progress=on_prog, auto_export=True)
            self.app.call_from_thread(self._handle_analysis_complete, res)
        except Exception as e:
            self.app.call_from_thread(self.log_msg, f"[bold red]Pipeline Error:[/] {e}")
        finally:
            self.is_busy = False
            self.current_stage = "IDLE"

    def _handle_pipeline_progress(self, stage: str, msg: str, data: Optional[Dict[str, Any]]):
        self.current_stage = stage
        self.log_msg(msg)

        if stage == "GTRENDS_DONE" and data:
            gt_text = (
                f"[bold green]Velocity :[/] [bold white]{data.get('trend_score', 0):.0f}%[/] "
                f"([bold yellow]{data.get('growth_percentage', '')}[/])\n"
                f"[bold green]Region   :[/] {data.get('region', 'Global')}\n"
                f"[bold green]Rising   :[/] [dim]{', '.join(data.get('rising_queries', [])[:3])}[/]"
            )
            self.query_one("#content-gt", Static).update(gt_text)

        elif stage == "TAVILY_DONE" and data:
            summary = data.get("summary", "")[:130]
            tav_text = (
                f"[bold cyan]Market   :[/] [bold white]{data.get('tavily_score', 0):.0f}%[/] "
                f"([bold white]{data.get('total_references', 0)} sumber industri[/])\n"
                f"[bold cyan]Insights :[/] [dim]{summary}...[/]"
            )
            self.query_one("#content-tav", Static).update(tav_text)

        elif stage == "ADOBESTOCK_DONE" and data:
            stock_text = (
                f"[bold magenta]Indeks Aset  :[/] [bold white]~{data.get('total_results', 0):,}[/] aset\n"
                f"[bold magenta]Tingkat Jenuh:[/] [bold yellow]{data.get('competition_level', '')}[/]\n"
                f"[bold magenta]Keamanan     :[/] [bold green]100% Zero Local Scraping via Tavily[/]"
            )
            self.query_one("#content-stock", Static).update(stock_text)

    def _handle_analysis_complete(self, result: Dict[str, Any]):
        self.active_result = result
        sc = result.get("scoring", {})
        bk = sc.get("breakdown", {})
        table = self.query_one("#matrix-table", DataTable)
        
        star = "⭐ " if sc.get("total_score", 0) >= 75 else "✨ "
        table.add_row(
            result.get("topic", ""),
            f"{bk.get('trend_score', 0):.1f}",
            f"{bk.get('tavily_score', 0):.1f}",
            f"{bk.get('stock_gap_score', 0):.1f}",
            f"[bold green]{star}{sc.get('total_score', 0):.1f}[/]",
            sc.get("recommendation", "")
        )
        self.log_msg(f"[bold green]✔ Riset selesai! Laporan: {result.get('exported_file', '')}[/]")
        self.notify(f"Analisis selesai: Skor {sc.get('total_score')}/100", title="stockimgtrend")
        
        # Automatically generate Nanobanana master prompt
        self.start_nanobanana_worker()

    @work(thread=True)
    def start_auto_discovery_worker(self):
        self.is_busy = True
        self.current_stage = "DISCOVERY"
        self.app.call_from_thread(self.log_msg, "[bold yellow]🚀 Memulai Autonomous Discovery: Mengecek database & merumuskan topik 2026...[/]")

        def on_prog(stage: str, msg: str, data=None):
            self.app.call_from_thread(self._handle_pipeline_progress, stage, msg, data)

        try:
            results = self.pipeline.autonomous_discovery(count=3, on_progress=on_prog)
            if results:
                best = results[0]
                self.active_result = best
                self.app.call_from_thread(self.log_msg, f"[bold green]🏆 Rekomendasi Teratas: \"{best.get('topic')}\" (Skor: {best.get('scoring', {}).get('total_score')})[/]")
                nano_data = self.pipeline.generate_nanobanana_master(best)
                self.app.call_from_thread(self._render_nanobanana_result, nano_data)
        except Exception as e:
            self.app.call_from_thread(self.log_msg, f"[bold red]Discovery Error:[/] {e}")
        finally:
            self.is_busy = False
            self.current_stage = "IDLE"

    @work(thread=True)
    def start_nanobanana_worker(self):
        if not self.active_result:
            return
        self.is_busy = True
        self.current_stage = "NANOBANANA"
        self.app.call_from_thread(self.log_msg, "[bold yellow]⚡ Meracik Master Prompt Nanobanana & Tema Kuat...[/]")
        try:
            nano_data = self.pipeline.generate_nanobanana_master(self.active_result)
            self.app.call_from_thread(self._render_nanobanana_result, nano_data)
            self.app.call_from_thread(self.log_msg, "[bold green]✔ Master Prompt Nanobanana berhasil diracik dan disimpan ke SQLite![/]")
        except Exception as e:
            self.app.call_from_thread(self.log_msg, f"[bold red]Nanobanana Gen Error:[/] {e}")
        finally:
            self.is_busy = False
            self.current_stage = "IDLE"

    def _render_nanobanana_result(self, nano_data: Dict[str, Any]):
        title = nano_data.get("theme_title", "Nanobanana Theme")
        narrative = nano_data.get("concept_narrative", "")
        prompt = nano_data.get("nanobanana_master_prompt", "")
        neg = nano_data.get("negative_prompt", "")
        stock_title = nano_data.get("commercial_title", "")
        tags = nano_data.get("tags_string", "")
        audit = nano_data.get("art_director_audit", {})

        audit_text = ""
        if audit:
            verdict = audit.get("verdict_status", "APPROVED")
            score = audit.get("art_director_score", 9.0)
            notes = audit.get("composition_and_lighting_notes", "")
            advice = audit.get("commercial_sales_advice", "")
            audit_text = (
                f"\n\n[bold bright_magenta]🎨 ART DIRECTOR AUDIT:[/] [bold green]{verdict} ({score}/10)[/]\n"
                f"[dim]• Komposisi & Cahaya:[/] [italic cyan]{notes}[/]\n"
                f"[dim]• Tips Penjualan:[/] [italic yellow]\"{advice}\"[/]"
            )

        rendered_text = (
            f"[bold bright_yellow]🏆 TEMA KUAT:[/] [bold bright_white]{title}[/]\n"
            f"[bold cyan]📖 KONSEP & NARRATIVE:[/] [italic white]{narrative}[/]\n\n"
            f"[bold bright_green]🍌 NANOBANANA MASTER PROMPT (Siap Generate):[/]\n"
            f"[bold white on #161b22]{prompt}[/]\n\n"
            f"[bold bright_red]🚫 NEGATIVE PROMPT:[/] [dim red]{neg}[/]\n\n"
            f"[bold magenta]🏷️ ADOBE STOCK TITLE:[/] [underline white]{stock_title}[/]{audit_text}\n\n"
            f"[bold blue]📋 50 KEYWORDS SIAP COPY-PASTE:[/] [dim white]{tags}[/]"
        )
        self.query_one("#prompt-display", Static).update(rendered_text)


def launch_tui(keyword: Optional[str] = None):
    """Launch the interactive Textual TUI dashboard."""
    pipeline = TrendPipeline(
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_model=os.getenv("OPENROUTER_MODEL"),
        output_dir="docs/reports"
    )
    app = StockImgTrendApp(pipeline=pipeline, initial_keyword=keyword)
    app.run()


if __name__ == "__main__":
    launch_tui()
