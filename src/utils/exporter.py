"""Exporter utility for generating Markdown reports from research results."""

import os
import re
from datetime import datetime
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """Sanitize keyword or category string for safe filename usage."""
    clean = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "_", clean)


def export_report_to_markdown(data: dict, output_dir: str = "docs/reports") -> str:
    """Export the structured research data into a comprehensive Markdown report.
    
    Returns the absolute path to the generated file.
    """
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    topic = data.get("topic", "trend_report")
    date_str = datetime.now().strftime("%Y-%m-%d")
    clean_topic = sanitize_filename(topic)
    filename = f"{date_str}_{clean_topic}_report.md"
    file_path = target_dir / filename

    scoring = data.get("scoring", {})
    total_score = scoring.get("total_score", 0.0)
    rec_label = scoring.get("recommendation_label", "N/A")
    breakdown = scoring.get("breakdown", {})

    gtrends = data.get("sources", {}).get("google_trends", {})
    tavily = data.get("sources", {}).get("tavily_intel", {})
    stock = data.get("sources", {}).get("adobe_stock_tracker", {})
    brief = data.get("actionable_brief", {})

    keywords = brief.get("keywords", [])
    keywords_formatted = ", ".join(keywords)

    md_content = f"""# Laporan Riset Tren Visual: {topic}

> Tanggal Pembuatan: **{datetime.now().strftime("%d %B %Y, %H:%M:%S")}**  
> Sumber Data: Google Trends & Tavily Web Intelligence (Cloud Proxy Mode)

---

## 1. Ringkasan Eksekutif & Opportunity Score

| Metrik | Nilai | Evaluasi |
| :--- | :--- | :--- |
| **Total Opportunity Score** | **{total_score} / 100** | **{rec_label}** |
| Google Trends Velocity (40%) | {breakdown.get('trend_score', 0)} / 100 | Momentum lonjakan pencarian |
| Market Buyer Demand (30%) | {breakdown.get('tavily_score', 0)} / 100 | Relevansi komersial & kebutuhan buyer |
| Adobe Stock Gap Score (30%) | {breakdown.get('stock_gap_score', 0)} / 100 | Estimasi indeks aset: ~{breakdown.get('indexed_assets', 0):,} |

---

## 2. Analisis Google Trends

- **Keyword Terkait**: `{gtrends.get('keyword', topic)}`
- **Search Momentum / Growth**: `{gtrends.get('growth_percentage', '+0%')}`
- **Wilayah Utama**: `{gtrends.get('region', 'Global')}`
- **Insight Tren**: {gtrends.get('summary', 'Pencarian menunjukkan peningkatan minat komersial.')}

---

## 3. Konteks Riset Pasar Visual (Tavily Intelligence)

- **Ringkasan Tren Pasar**:  
  {tavily.get('summary', 'Data tren pasar belum tersedia.')}

- **Elemen Visual Kunci & Gaya yang Diminati**:
{chr(10).join([f"  - {elem}" for elem in tavily.get('key_elements', [])]) if tavily.get('key_elements') else "  - Konsep visual natural dan relevan untuk kebutuhan korporat/lifestyle."}

- **Referensi Sumber & Artikel Industri**:
{chr(10).join([f"  - [{ref.get('title', 'Artikel Referensi')}]({ref.get('url', '#')})" for ref in tavily.get('reference_urls', [])]) if tavily.get('reference_urls') else "  - Laporan tren industri visual dan mikrostock global."}

---

## 4. Validasi Kompetisi Adobe Stock (via Tavily Cloud)

- **Metode Pelacakan**: `Tavily site:stock.adobe.com search` (100% aman tanpa scraping IP lokal)
- **Tingkat Kejenuhan**: `{stock.get('competition_level', 'Sedang')}`
- **Estimasi Jumlah Aset Terindeks**: `~{stock.get('total_results', 0):,}` aset
- **Temuan Celah Konten (*Content Gap*)**:  
  {stock.get('gap_analysis', 'Masih terdapat celah untuk konten dengan gaya modern dan realistis.')}

---

## 5. Actionable Creative Brief (Panduan Produksi Kontributor)

### Rekomendasi Judul Komersial (Commercial Title)
> **"{brief.get('title_suggestion', topic)}"**

### Tipe Aset yang Disarankan
{chr(10).join([f"- **{t}**" for t in brief.get('recommended_asset_types', ['Photo', 'Generative AI'])])}

### Resep Prompt AI Generation (Midjourney / Flux / Adobe Firefly)
```text
{brief.get('prompt_recipe', 'Professional commercial stock photography...')}
```

---

## 6. Daftar 30–50 Keyword Siap Pakai (Tags)

> Siap disalin langsung ke Adobe Stock Contributor Portal:

```text
{keywords_formatted}
```

---
*Laporan otomatis dibuat oleh stockimgtrend AI Pipeline.*
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return str(file_path.resolve())
