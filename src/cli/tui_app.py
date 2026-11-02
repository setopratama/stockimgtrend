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
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
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
from src.utils.db import list_recent_researches, update_buyer_panel

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
class HistoryModal(ModalScreen[Optional[Dict[str, Any]]]):
    """Pure keyboard-driven viewer displaying research records stored in SQLite."""

    BINDINGS = [
        Binding("escape", "dismiss_modal", "Tutup", priority=True),
        Binding("q", "dismiss_modal", "Tutup", priority=True),
        Binding("enter", "select_record", "Review Buyer", priority=True),
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
        table.add_columns("ID", "Keyword", "Total Skor", "Rekomendasi", "Aset Indeks", "Nanobanana", "Buyer Panel", "Waktu Riset")
        
        self.records = list_recent_researches(limit=35)
        for r in self.records:
            nano = "✔ Siap" if r.get("nanobanana_prompt") else "—"
            try:
                buyer_panel = json.loads(r.get("raw_json") or "{}").get("buyer_panel", {})
                buyer = f"{buyer_panel.get('buyer_count', 0)}/10" if buyer_panel else "Review"
            except json.JSONDecodeError:
                buyer = "Review"
            table.add_row(
                str(r.get("id", "")),
                str(r.get("keyword", "")),
                f"{r.get('total_score', 0):.1f}",
                str(r.get("recommendation", "")),
                f"{r.get('indexed_assets', 0):,}",
                nano,
                buyer,
                str(r.get("created_at", ""))[:16]
            )
        table.focus()

    def action_dismiss_modal(self) -> None:
        self.dismiss(None)

    def action_select_record(self) -> None:
        table = self.query_one("#history-table", DataTable)
        if 0 <= table.cursor_row < len(self.records):
            self.dismiss(self.records[table.cursor_row])


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
    /* Bloomberg-inspired surface: dense, calm, and information-first. */
    Screen {
        background: #050b14;
        color: #cbd5e1;
    }
    Header {
        background: #071321;
        color: #67e8f9;
        height: 1;
    }
    Footer {
        background: #071321;
        color: #94a3b8;
    }
    #top-status-bar {
        height: 2;
        background: #0a1726;
        border-bottom: solid #164e63;
        padding: 0 1;
        content-align: left middle;
        text-overflow: ellipsis;
    }
    #body-container {
        height: 1fr;
        width: 100%;
    }
    #left-pane, #right-pane {
        width: 50%;
        min-width: 0;
        height: 100%;
        padding: 0 1;
        scrollbar-color: #155e75;
        scrollbar-background: #071321;
        overflow-x: hidden;
    }
    #left-pane {
        border-right: solid #1e3a5f;
    }
    .column-scroll {
        height: 1fr;
        overflow-y: auto;
        scrollbar-color: #155e75;
    }
    .section-heading {
        height: 1;
        color: #67e8f9;
        text-style: bold;
        padding: 0 1;
        background: #0b1b2b;
    }
    .section-heading.market { color: #86efac; }
    .section-heading.signal { color: #fbbf24; }
    .section-heading.ai { color: #c4b5fd; }
    .terminal-panel {
        background: #081421;
        border: solid #1e4866;
        padding: 0 1;
        margin-bottom: 1;
        height: auto;
    }
    .terminal-panel.compact { border-left: solid #0891b2; }
    .terminal-panel.positive { border-left: solid #16a34a; }
    .terminal-panel.warning { border-left: solid #d97706; }
    .terminal-panel.ai-panel { border-left: solid #8b5cf6; }
    .metric-copy { height: auto; min-height: 3; }
    #matrix-table {
        height: 9;
        min-height: 6;
        background: #06101b;
        border: solid #155e75;
        margin-bottom: 1;
    }
    #activity-log {
        height: 1fr;
        min-height: 10;
        background: #030811;
        border: solid #1e3a5f;
        padding: 0 1;
        scrollbar-color: #0e7490;
    }
    #research-feed-panel {
        height: 1fr;
        min-height: 18;
    }
    #prompt-display {
        height: 18;
        min-height: 12;
        overflow-y: auto;
        color: #e2e8f0;
    }
    #generation-history, #pipeline-status, #agent-activity {
        min-height: 3;
    }
    #studio-status { min-height: 2; color: #c4b5fd; }
    .io-label { color: #64748b; text-style: bold; }
    .io-graph {
        height: 1;
        color: #67e8f9;
        background: #030b14;
        padding: 0;
        margin: 0;
        text-style: bold;
    }
    #studio-download { color: #86efac; }
    #studio-queue { color: #fbbf24; min-height: 2; }
    DataTable { background: #06101b; color: #cbd5e1; }
    DataTable > .datatable--header { background: #0e2a3c; color: #67e8f9; }
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
        self.ranking_has_placeholder = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        # Top Live Telemetry Bar
        yield Static(id="top-status-bar")

        with Horizontal(id="body-container"):
            with VerticalScroll(id="left-pane", classes="column-scroll"):
                yield Static("MARKET INTEL  /  LIVE", classes="section-heading market")
                with Container(classes="terminal-panel positive", id="card-gt"):
                    yield Static("TREND MOMENTUM", classes="section-heading", id="lbl-gt")
                    yield Static("Menunggu perintah riset...", classes="metric-copy", id="content-gt")
                with Container(classes="terminal-panel compact", id="card-tav"):
                    yield Static("MARKET DEMAND", classes="section-heading", id="lbl-tav")
                    yield Static("Menunggu perintah riset...", classes="metric-copy", id="content-tav")
                with Container(classes="terminal-panel warning", id="card-stock"):
                    yield Static("SUPPLY GAP  /  ADOBE", classes="section-heading", id="lbl-stock")
                    yield Static("Menunggu perintah riset...", classes="metric-copy", id="content-stock")
                with Container(classes="terminal-panel compact"):
                    yield Static("OPPORTUNITY RANKING", classes="section-heading signal")
                    yield DataTable(id="matrix-table")
                with Container(classes="terminal-panel compact"):
                    yield Static("TRENDING KEYWORDS", classes="section-heading")
                    yield Static("Rising queries akan tampil setelah riset dimulai.", id="trending-keywords")
                with Container(classes="terminal-panel warning"):
                    yield Static("MARKET SIGNALS", classes="section-heading signal")
                    yield Static("[dim]Cloud-only research guard: active[/]", id="market-signals")
                with Container(classes="terminal-panel ai-panel"):
                    yield Static("GENERATION STATUS", classes="section-heading ai")
                    yield Static("[yellow]IDLE[/]  ·  awaiting creative brief", id="generation-status")
                with Container(classes="terminal-panel ai-panel"):
                    yield Static("AGENT ACTIVITY", classes="section-heading ai")
                    yield Static("Pipeline agents standing by.", id="agent-activity")
                with Container(classes="terminal-panel ai-panel"):
                    yield Static("GENERATION HISTORY", classes="section-heading ai")
                    yield Static("Recent Nanobanana generations appear after completion.", id="generation-history")
                with Container(classes="terminal-panel ai-panel"):
                    yield Static("AI PIPELINE STATUS", classes="section-heading ai")
                    yield Static("[green]●[/] Trends  [green]●[/] Tavily  [green]●[/] Synthesis  [green]●[/] Export", id="pipeline-status")
                with Container(classes="terminal-panel ai-panel"):
                    yield Static("PROMPT WORKSPACE", classes="section-heading ai")
                    yield Static(
                        "[dim]Belum ada prompt aktif. Hasil prompt master, negative prompt, audit, dan tags akan tampil di sini.[/]",
                        id="prompt-display"
                    )

            with VerticalScroll(id="right-pane", classes="column-scroll"):
                yield Static("AI WORKSTATION  /  CONTROL", classes="section-heading ai")
                with Container(classes="terminal-panel ai-panel"):
                    yield Static("MODEL I/O TELEMETRY", classes="section-heading ai", id="lbl-nano")
                    yield Static("[dim]Tekan [a] Auto Discovery, [k] Keyword Research, atau [g] Generate.[/]", id="studio-status")
                    yield Static("", classes="io-graph", id="studio-upload")
                    yield Static("", classes="io-graph", id="studio-download")
                    yield Static("QUEUE  ·  model idle", id="studio-queue")
                with Container(classes="terminal-panel compact", id="research-feed-panel"):
                    yield Static("RESEARCH FEED  /  PROCESS TIMELINE", classes="section-heading")
                    yield RichLog(id="activity-log", highlight=True, markup=True, wrap=True)

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#matrix-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("TOPIC", "TR", "MK", "GAP", "SCORE", "VIEW")

        # Keep the ranking useful on startup by restoring recent persisted research.
        recent = list_recent_researches(limit=8)
        for record in sorted(recent, key=lambda item: item.get("total_score") or 0, reverse=True):
            self._add_opportunity_record(record)
        if not recent:
            table.add_row("NO RESEARCH YET", "—", "—", "—", "—", "PRESS A / K")
            self.ranking_has_placeholder = True
        
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

        # Keep animation confined to telemetry text; panel geometry stays stable.
        if self.is_busy:
            self.query_one("#generation-status", Static).update(
                f"[yellow]{spin} PROCESSING[/]  ·  [cyan]{self.current_stage}[/]  ·  activity {audio}"
            )
            self.query_one("#agent-activity", Static).update(
                f"[cyan]{wave}[/] {self.current_stage}  ·  target [white]{self.current_keyword}[/]"
            )
        self._update_studio_telemetry()

    def _update_studio_telemetry(self) -> None:
        """Render local btop-style pipeline I/O telemetry without network calls."""
        width = 34
        upload_seed = self.anim_tick * 3 + (11 if self.is_busy else 2)
        download_seed = self.anim_tick * 2 + (19 if self.is_busy else 5)
        upload_chars = " .·∙⠂⠆⠖⠦⠴⠸⠇"
        download_chars = " .·∙⠂⠆⠖⠦⠴⠸⠇"
        upload = "".join(upload_chars[(upload_seed + idx * 3) % len(upload_chars)] for idx in range(width))
        download = "".join(download_chars[(download_seed + idx * 5) % len(download_chars)] for idx in range(width))
        state = "ACTIVE" if self.is_busy else "IDLE"
        queue = "[yellow]QUEUE[/] 1 active job" if self.is_busy else "[dim]QUEUE[/] 0 active jobs · ready"
        self.query_one("#studio-upload", Static).update(f"[cyan]UP [/][cyan]{upload}[/]  {state}")
        self.query_one("#studio-download", Static).update(f"[green]DOWN[/][green]{download}[/]  {state}")
        self.query_one("#studio-queue", Static).update(queue)

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
        def handle_review(record: Optional[Dict[str, Any]]) -> None:
            if record:
                self.start_buyer_review_worker(record)

        self.push_screen(HistoryModal(), handle_review)

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
        self.log_msg(f"[bold cyan]{stage}[/]  {msg}")

        if stage == "GTRENDS_DONE" and data:
            gt_text = (
                f"[bold green]Velocity :[/] [bold white]{data.get('trend_score', 0):.0f}%[/] "
                f"([bold yellow]{data.get('growth_percentage', '')}[/])\n"
                f"[bold green]Region   :[/] {data.get('region', 'Global')}\n"
                f"[bold green]Rising   :[/] [dim]{', '.join(data.get('rising_queries', [])[:3])}[/]"
            )
            self.query_one("#content-gt", Static).update(gt_text)
            self.query_one("#trending-keywords", Static).update(
                "\n".join(f"[green]↑[/] {item}" for item in data.get("rising_queries", [])[:6]) or "No rising query returned."
            )
            self.log_msg(
                f"[green]TREND SNAPSHOT[/] velocity={data.get('trend_score', 0):.0f}%  "
                f"growth={data.get('growth_percentage', 'n/a')}  "
                f"rising={', '.join(data.get('rising_queries', [])[:3]) or 'none'}"
            )

        elif stage == "TAVILY_DONE" and data:
            summary = data.get("summary", "")[:130]
            tav_text = (
                f"[bold cyan]Market   :[/] [bold white]{data.get('tavily_score', 0):.0f}%[/] "
                f"([bold white]{data.get('total_references', 0)} sumber industri[/])\n"
                f"[bold cyan]Insights :[/] [dim]{summary}...[/]"
            )
            self.query_one("#content-tav", Static).update(tav_text)
            self.query_one("#market-signals", Static).update(
                f"[green]●[/] Buyer relevance [bold cyan]{data.get('tavily_score', 0):.0f}[/]/100\n"
                f"[cyan]●[/] Industry references [bold white]{data.get('total_references', 0)}[/]\n"
                "[green]●[/] Tavily cloud proxy active"
            )
            self.log_msg(
                f"[cyan]MARKET SNAPSHOT[/] relevance={data.get('tavily_score', 0):.0f}/100  "
                f"references={data.get('total_references', 0)}  "
                f"summary={summary}"
            )

        elif stage == "ADOBESTOCK_DONE" and data:
            stock_text = (
                f"[bold magenta]Indeks Aset  :[/] [bold white]~{data.get('total_results', 0):,}[/] aset\n"
                f"[bold magenta]Tingkat Jenuh:[/] [bold yellow]{data.get('competition_level', '')}[/]\n"
                f"[bold magenta]Keamanan     :[/] [bold green]100% Zero Local Scraping via Tavily[/]"
            )
            self.query_one("#content-stock", Static).update(stock_text)
            self.query_one("#market-signals", Static).update(
                f"[yellow]◆[/] Supply saturation: [bold yellow]{data.get('competition_level', 'unknown')}[/]\n"
                f"[green]●[/] Indexed assets: [bold white]~{data.get('total_results', 0):,}[/]\n"
                "[green]●[/] Zero local scraping"
            )
            self.log_msg(
                f"[yellow]SUPPLY SNAPSHOT[/] indexed=~{data.get('total_results', 0):,}  "
                f"saturation={data.get('competition_level', 'unknown')}  "
                "source=site-search via Tavily"
            )

        self.query_one("#pipeline-status", Static).update(
            f"[green]●[/] Trends  [green]●[/] Tavily  [yellow]◐[/] {stage}  [dim]○[/] Export"
        )

    def _handle_analysis_complete(self, result: Dict[str, Any]):
        self.active_result = result
        self._add_opportunity_row(result)
        sc = result.get("scoring", {})
        self.query_one("#generation-history", Static).update(
            f"[green]LATEST[/]  {result.get('topic', self.current_keyword)}\n"
            f"Score [bold cyan]{sc.get('total_score', 0):.1f}[/]/100  ·  {sc.get('recommendation', '—')}\n"
            f"Export [dim]{result.get('exported_file', 'pending')}[/]"
        )
        self.log_msg(f"[bold green]✔ Riset selesai! Laporan: {result.get('exported_file', '')}[/]")
        self.notify(f"Analisis selesai: Skor {sc.get('total_score')}/100", title="stockimgtrend")
        
        # Automatically generate Nanobanana master prompt
        self.start_nanobanana_worker()

    def _add_opportunity_row(self, result: Dict[str, Any]) -> None:
        """Render one scored research result in the compact opportunity ranking."""
        table = self.query_one("#matrix-table", DataTable)
        if self.ranking_has_placeholder:
            table.clear()
            self.ranking_has_placeholder = False
        sc = result.get("scoring", {})
        breakdown = sc.get("breakdown", {})
        total = float(sc.get("total_score", 0) or 0)
        star = "⭐ " if total >= 75 else "✨ "
        table.add_row(
            str(result.get("topic", result.get("keyword", "—")))[:28],
            f"{float(breakdown.get('trend_score', 0) or 0):.1f}",
            f"{float(breakdown.get('tavily_score', 0) or 0):.1f}",
            f"{float(breakdown.get('stock_gap_score', 0) or 0):.1f}",
            f"[bold green]{star}{total:.1f}[/]",
            str(sc.get("recommendation", "—"))[:12]
        )

    def _add_opportunity_record(self, record: Dict[str, Any]) -> None:
        """Render a persisted SQLite record in the opportunity ranking."""
        total = float(record.get("total_score", 0) or 0)
        star = "⭐ " if total >= 75 else "✨ "
        self.query_one("#matrix-table", DataTable).add_row(
            str(record.get("keyword", "—"))[:28],
            f"{float(record.get('trend_score', 0) or 0):.1f}",
            f"{float(record.get('market_score', 0) or 0):.1f}",
            f"{float(record.get('stock_gap_score', 0) or 0):.1f}",
            f"[bold green]{star}{total:.1f}[/]",
            str(record.get("recommendation", "—"))[:12]
        )

    def _render_opportunity_rows(self, results: List[Dict[str, Any]]) -> None:
        """Replace the ranking with the latest autonomous discovery candidates."""
        table = self.query_one("#matrix-table", DataTable)
        table.clear()
        self.ranking_has_placeholder = False
        for result in results[:3]:
            self._add_opportunity_row(result)

    @work(thread=True)
    def start_auto_discovery_worker(self):
        self.is_busy = True
        self.current_stage = "DISCOVERY"
        self.app.call_from_thread(self.log_msg, "[bold yellow]🚀 Memulai Autonomous Discovery: Mengecek database & merumuskan topik 2026...[/]")

        def on_prog(stage: str, msg: str, data=None):
            self.app.call_from_thread(self._handle_pipeline_progress, stage, msg, data)

        try:
            results = self.pipeline.autonomous_discovery(count=5, on_progress=on_prog)
            if results:
                best = results[0]
                self.active_result = best
                self.app.call_from_thread(self._render_opportunity_rows, results)
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

    @work(thread=True)
    def start_buyer_review_worker(self, record: Dict[str, Any]):
        """Review an existing history record with the ten-buyer DeepSeek panel."""
        if self.is_busy:
            self.app.call_from_thread(self.notify, "Tunggu proses aktif selesai sebelum review buyer.", severity="warning")
            return
        try:
            research = json.loads(record.get("raw_json") or "{}")
        except json.JSONDecodeError:
            research = {"topic": record.get("keyword", ""), "scoring": {}}
        self.is_busy = True
        self.current_keyword = research.get("topic", record.get("keyword", "—"))
        self.current_stage = "BUYER_PANEL_HISTORY"
        self.app.call_from_thread(self.log_msg, f"[bold yellow]Buyer review dimulai:[/] {self.current_keyword}")
        try:
            panel = self.pipeline.buyer_panel_agent.evaluate(research)
            update_buyer_panel(record.get("id"), panel)
            self.app.call_from_thread(self._render_buyer_review, panel, self.current_keyword)
        except Exception as exc:
            self.app.call_from_thread(self.log_msg, f"[bold red]Buyer review error:[/] {exc}")
        finally:
            self.is_busy = False
            self.current_stage = "IDLE"

    def _render_buyer_review(self, panel: Dict[str, Any], topic: str) -> None:
        count = panel.get("buyer_count", 0)
        verdict = panel.get("panel_verdict", "UNVERIFIED")
        self.query_one("#generation-history", Static).update(
            f"[green]BUYER REVIEW[/]  {topic}\n"
            f"Personas [bold cyan]{count}/10[/]  ·  verdict [bold yellow]{verdict}[/]\n"
            f"Demand [bold cyan]{panel.get('average_demand_score', 0)}[/]  ·  intent [bold cyan]{panel.get('average_purchase_intent', 0)}[/]\n"
            f"[dim]{panel.get('error', panel.get('panel_summary', 'Review tersimpan ke SQLite.'))}[/]"
        )
        self.log_msg(
            f"[bold green]✔ Buyer review selesai:[/] {count}/10 persona · {verdict} · "
            f"demand={panel.get('average_demand_score', 0)} intent={panel.get('average_purchase_intent', 0)}"
        )
        self.notify(f"Buyer review: {count}/10 persona", title="stockimgtrend")

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
        self.query_one("#studio-status", Static).update(
            f"[green]● READY[/]  ·  [bold white]{title}[/]  ·  audit {audit.get('verdict_status', 'APPROVED') if audit else 'PENDING'}"
        )
        self.query_one("#generation-status", Static).update("[green]● COMPLETE[/]  ·  prompt saved to SQLite")
        self.query_one("#pipeline-status", Static).update(
            "[green]●[/] Trends  [green]●[/] Tavily  [green]●[/] Synthesis  [green]●[/] Export  [green]●[/] SQLite"
        )


def launch_tui(keyword: Optional[str] = None):
    """Launch the interactive Textual TUI dashboard."""
    pipeline = TrendPipeline(
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_model=os.getenv("OPENROUTER_MODEL"),
        reasoning_model=os.getenv("OPENROUTER_REASONING_MODEL"),
        output_dir="docs/reports"
    )
    app = StockImgTrendApp(pipeline=pipeline, initial_keyword=keyword)
    app.run()


if __name__ == "__main__":
    launch_tui()
