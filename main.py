"""Main entry point for stockimgtrend.

Directly launches the unified btop-style interactive Textual TUI Dashboard.
All operations (Auto Discovery, Keyword Input, Nanobanana Generation, History)
can be executed directly inside the TUI with single-key shortcuts:
- [a]: Auto Discovery
- [k]: Input Keyword
- [g]: Generate Nanobanana Master Prompt
- [h]: View SQLite History
- [q]: Quit
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir))

# Explicitly load .env file
dotenv_path = root_dir / ".env"
load_dotenv(dotenv_path=dotenv_path)

from rich.console import Console
from rich.table import Table
from src.pipelines.trend_pipeline import TrendPipeline
from src.cli.tui_app import StockImgTrendApp
from src.utils.db import list_recent_researches

console = Console()

def parse_args():
    parser = argparse.ArgumentParser(
        description="stockimgtrend — Unified btop TUI Dashboard & Nanobanana Studio"
    )
    parser.add_argument(
        "-k", "--keyword",
        type=str,
        default=None,
        help="Keyword target untuk langsung dianalisis di dalam TUI"
    )
    parser.add_argument(
        "-a", "--auto",
        action="store_true",
        help="Langsung jalankan Autonomous Discovery di dalam TUI"
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help="Model OpenRouter (default: google/gemma-4-26b-a4b-it atau dari .env)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="docs/reports",
        help="Folder output untuk laporan Markdown (default: docs/reports)"
    )
    parser.add_argument(
        "-H", "--history",
        action="store_true",
        help="Tampilkan riwayat riset SQLite di terminal (mode non-TUI)"
    )
    return parser.parse_args()


def display_history():
    records = list_recent_researches(limit=20)
    if not records:
        console.print("[yellow]Belum ada data riset yang tersimpan di SQLite.[/]")
        return

    table = Table(title="📚 Riwayat Riset Tren Stock Image (SQLite: data/stockimgtrend.db)", style="bold bright_blue")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Keyword", style="bold cyan")
    table.add_column("Skor", justify="center", style="bold green")
    table.add_column("Rekomendasi", style="yellow")
    table.add_column("Aset Indeks", justify="right", style="white")
    table.add_column("Nanobanana", justify="center", style="magenta")
    table.add_column("Waktu Riset", style="dim")

    for r in records:
        nano = "✔ Siap" if r.get("nanobanana_prompt") else "Belum"
        table.add_row(
            str(r["id"]),
            r["keyword"],
            f"{r['total_score']:.1f}",
            r["recommendation"],
            f"{r['indexed_assets']:,}",
            nano,
            str(r["created_at"])[:16]
        )
    console.print(table)


def main():
    args = parse_args()

    # Plain history flag without launching full TUI
    if args.history:
        display_history()
        return

    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        console.print("[bold red]Error:[/] TAVILY_API_KEY tidak ditemukan di file .env!", style="red")
        sys.exit(1)

    pipeline = TrendPipeline(
        tavily_api_key=tavily_key,
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_model=args.model or os.getenv("OPENROUTER_MODEL"),
        output_dir=args.output_dir
    )

    # Launch Fullscreen Textual TUI Application
    try:
        app = StockImgTrendApp(pipeline=pipeline, initial_keyword=args.keyword)
        app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Aplikasi ditutup oleh pengguna.[/]")
        sys.exit(0)


if __name__ == "__main__":
    main()
