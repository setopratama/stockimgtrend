"""SQLite Database Utility for saving, querying, and updating research results."""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_DIR = Path("data")
DB_PATH = DB_DIR / "stockimgtrend.db"


def get_db_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get a SQLite connection and ensure database directory and tables exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH):
    """Initialize the research table schema and apply migrations."""
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trend_researches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_score REAL,
                recommendation TEXT,
                recommendation_label TEXT,
                trend_score REAL,
                market_score REAL,
                stock_gap_score REAL,
                indexed_assets INTEGER,
                title_suggestion TEXT,
                prompt_recipe TEXT,
                nanobanana_prompt TEXT,
                asset_types TEXT,
                keywords_list TEXT,
                report_file TEXT,
                raw_json TEXT
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trend_keyword ON trend_researches(keyword);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_trend_created_at ON trend_researches(created_at);
        """)

        # Migration: Add nanobanana_prompt column if table already existed without it
        cursor = conn.execute("PRAGMA table_info(trend_researches);")
        columns = [row["name"] for row in cursor.fetchall()]
        if "nanobanana_prompt" not in columns:
            conn.execute("ALTER TABLE trend_researches ADD COLUMN nanobanana_prompt TEXT;")

    conn.close()


def save_research_to_db(data: dict, db_path: Path = DB_PATH) -> int:
    """Save the pipeline research result into the SQLite database."""
    init_db(db_path)
    conn = get_db_connection(db_path)

    topic = data.get("topic", "")
    scoring = data.get("scoring", {})
    breakdown = scoring.get("breakdown", {})
    brief = data.get("actionable_brief", {})

    total_score = scoring.get("total_score", 0.0)
    recommendation = scoring.get("recommendation", "")
    recommendation_label = scoring.get("recommendation_label", "")

    trend_score = breakdown.get("trend_score", 0.0)
    market_score = breakdown.get("tavily_score", 0.0)
    stock_gap_score = breakdown.get("stock_gap_score", 0.0)
    indexed_assets = breakdown.get("indexed_assets", 0)

    title_suggestion = brief.get("title_suggestion", "")
    prompt_recipe = brief.get("prompt_recipe", "")
    nanobanana_prompt = json.dumps(data.get("nanobanana_master", {}), ensure_ascii=False) if data.get("nanobanana_master") else ""
    asset_types = json.dumps(brief.get("recommended_asset_types", []))
    keywords_list = json.dumps(brief.get("keywords", []))
    report_file = data.get("exported_file", "")
    raw_json = json.dumps(data, ensure_ascii=False)

    with conn:
        cursor = conn.execute("""
            INSERT INTO trend_researches (
                keyword,
                total_score,
                recommendation,
                recommendation_label,
                trend_score,
                market_score,
                stock_gap_score,
                indexed_assets,
                title_suggestion,
                prompt_recipe,
                nanobanana_prompt,
                asset_types,
                keywords_list,
                report_file,
                raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            topic,
            total_score,
            recommendation,
            recommendation_label,
            trend_score,
            market_score,
            stock_gap_score,
            indexed_assets,
            title_suggestion,
            prompt_recipe,
            nanobanana_prompt,
            asset_types,
            keywords_list,
            report_file,
            raw_json
        ))
        record_id = cursor.lastrowid

    conn.close()
    return record_id


def update_nanobanana_prompt(record_id: int, nanobanana_data: dict, db_path: Path = DB_PATH):
    """Update nanobanana master prompt for an existing record."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    with conn:
        conn.execute("""
            UPDATE trend_researches
            SET nanobanana_prompt = ?
            WHERE id = ?
        """, (json.dumps(nanobanana_data, ensure_ascii=False), record_id))
    conn.close()


def update_buyer_panel(record_id: int, buyer_panel: dict, db_path: Path = DB_PATH):
    """Persist a buyer-panel review into the existing raw JSON record."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    row = conn.execute("SELECT raw_json FROM trend_researches WHERE id = ?", (record_id,)).fetchone()
    if not row:
        conn.close()
        return
    try:
        raw = json.loads(row["raw_json"] or "{}")
    except json.JSONDecodeError:
        raw = {}
    raw["buyer_panel"] = buyer_panel
    with conn:
        conn.execute(
            "UPDATE trend_researches SET raw_json = ? WHERE id = ?",
            (json.dumps(raw, ensure_ascii=False), record_id),
        )
    conn.close()


def list_recent_researches(limit: int = 15, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve recent research records from SQLite."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.execute("""
        SELECT id, keyword, created_at, total_score, recommendation, recommendation_label,
               trend_score, market_score, stock_gap_score, indexed_assets,
               title_suggestion, report_file, nanobanana_prompt, raw_json
        FROM trend_researches
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_past_keywords(limit: int = 30, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Get list of past analyzed keywords and their scores to avoid redundant research."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.execute("""
        SELECT keyword, total_score, recommendation, indexed_assets, created_at
        FROM trend_researches
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
