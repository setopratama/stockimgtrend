#!/usr/bin/env bash

# ==============================================================================
# stockimgtrend — Launcher Script
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  File .env belum ditemukan!"
    if [ -f ".env.example" ]; then
        echo "📝 Membuat .env dari .env.example..."
        cp .env.example .env
        echo "❗ Silakan isi TAVILY_API_KEY dan OPENROUTER_API_KEY di file .env terlebih dahulu."
        exit 1
    fi
fi

# Check if virtualenv exists, if not create it
if [ ! -d ".venv" ]; then
    echo "📦 Membuat virtual environment Python (.venv)..."
    python3 -m virtualenv .venv || python3 -m venv .venv
    echo "📥 Menginstal dependensi..."
    .venv/bin/pip install -r requirements.txt
fi

# Run the TUI application directly with any arguments passed
exec .venv/bin/python "$SCRIPT_DIR/main.py" "$@"
