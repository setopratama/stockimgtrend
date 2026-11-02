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
    platform_trends = data.get("sources", {}).get("platform_trends", {})
    brief = data.get("actionable_brief", {})
    verification = data.get("verification", {})
    trend_audit = verification.get("trend_audit", {})
    competition_audit = verification.get("competition_audit", {})
    demand = verification.get("commercial_demand", {})
    forecast = verification.get("commercial_forecast", {})
    buyer_panel = data.get("buyer_panel", {})

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
- **Periode Data**: `{gtrends.get('timeframe', 'Tidak tersedia')}`
- **Perbandingan**: `{gtrends.get('comparison_period', 'Tidak tersedia')}`
- **Rata-rata Recent / Baseline**: `{gtrends.get('recent_average', 'N/A')} / {gtrends.get('baseline_average', 'N/A')}`
- **Volume Absolut**: `{'Tersedia' if gtrends.get('absolute_volume_available') else 'Tidak tersedia — indeks Google Trends bersifat relatif'}`
- **Kualitas Data**: `{gtrends.get('data_quality', 'unknown')}`
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
- **Tipe Nilai**: `{stock.get('value_type', 'ESTIMATE')}`
- **Kualitas Estimasi**: `{stock.get('estimate_quality', 'unknown')}`
- **Confidence**: `{stock.get('confidence', 0):.2f}`
- **Audit Katalog Langsung**: `{'Ya' if stock.get('catalog_directly_verified') else 'Tidak — hanya indeks Tavily'}`
- **Temuan Celah Konten (*Content Gap*)**:  
  {stock.get('gap_analysis', 'Masih terdapat celah untuk konten dengan gaya modern dan realistis.')}

---

## 5. Evidence Audit & Prediksi Demand (Model Tambahan)

- **Status Audit**: `{verification.get('status', 'NOT_CONFIGURED')}`
- **Model Reasoning**: `{verification.get('model', 'Belum dikonfigurasi')}`
- **Verdict**: **{verification.get('final_verdict', 'UNVERIFIED')}**
- **Confidence Keseluruhan**: `{verification.get('confidence', 0):.2f}`

### Audit Tren

- **Validitas Klaim**: `{trend_audit.get('validity', 'UNVERIFIED')}`
- **Penilaian Periode**: {trend_audit.get('period_assessment', 'Belum diaudit.')}
- **Volume Absolut Tersedia**: `{trend_audit.get('absolute_volume_available', False)}`
- **Alasan**: {trend_audit.get('reason', 'Belum ada audit model tambahan.')}
- **Confidence**: `{trend_audit.get('confidence', 0):.2f}`

### Audit Kompetisi

- **Tipe Nilai**: `{competition_audit.get('value_type', stock.get('value_type', 'ESTIMATE'))}`
- **Kualitas Metode**: `{competition_audit.get('method_quality', 'UNVERIFIED')}`
- **Katalog Terverifikasi Langsung**: `{competition_audit.get('catalog_directly_verified', False)}`
- **Alasan**: {competition_audit.get('reason', stock.get('estimate_note', 'Belum diaudit.'))}

### Demand & Forecast Komersial

- **Buyer Need**: `{demand.get('buyer_need', 'UNVERIFIED')}`
- **Unmet Visual Angle**: {demand.get('unmet_visual_angle', 'Belum tersedia.')}
- **Base Case**: {forecast.get('base_case', 'Belum tersedia.')}
- **Upside Case**: {forecast.get('upside_case', 'Belum tersedia.')}
- **Downside Case**: {forecast.get('downside_case', 'Belum tersedia.')}
- **Prediksi Penjualan Pasti**: `{forecast.get('sales_prediction_allowed', False)}`

> Forecast adalah skenario demand berbasis evidence, bukan jaminan penjualan. Pipeline tidak memiliki data download, conversion rate, atau histori penjualan Adobe Stock.

---

## 6. Supplemental Platform Signals

> Data dikumpulkan melalui Tavily Cloud. Tidak ada scraping langsung ke Shutterstock atau Pinterest dari komputer lokal.

| Platform | Indexed Evidence | Confidence | Direct Catalog Audit |
| :--- | :---: | :---: | :---: |
| Shutterstock Trends | {platform_trends.get('sources', {}).get('shutterstock_trends', {}).get('indexed_result_count', 0)} hasil Tavily | {platform_trends.get('sources', {}).get('shutterstock_trends', {}).get('confidence', 0):.2f} | Tidak |
| Pinterest Trends | {platform_trends.get('sources', {}).get('pinterest_trends', {}).get('indexed_result_count', 0)} hasil Tavily | {platform_trends.get('sources', {}).get('pinterest_trends', {}).get('confidence', 0):.2f} | Tidak |

### Shutterstock Trends Evidence

{chr(10).join([f"- [{item.get('title', 'Reference')}]({item.get('url', '#')}) — {item.get('snippet', '')}" for item in platform_trends.get('sources', {}).get('shutterstock_trends', {}).get('references', [])]) or '- Tidak ada hasil terindeks.'}

### Pinterest Trends Evidence

{chr(10).join([f"- [{item.get('title', 'Reference')}]({item.get('url', '#')}) — {item.get('snippet', '')}" for item in platform_trends.get('sources', {}).get('pinterest_trends', {}).get('references', [])]) or '- Tidak ada hasil terindeks.'}

---

## 7. Ten-Buyer Demand Panel

> Simulasi panel buyer berbasis evidence. Ini bukan data penjualan aktual atau wawancara buyer nyata.

- **Status**: `{buyer_panel.get('status', 'NOT_CONFIGURED')}`
- **Model**: `{buyer_panel.get('model', 'Belum dikonfigurasi')}`
- **Jumlah Persona**: `{buyer_panel.get('buyer_count', 0)}`
- **Target Persona**: `{buyer_panel.get('expected_buyer_count', 10)}`
- **Average Demand Score**: `{buyer_panel.get('average_demand_score', 0)}` / 100
- **Average Purchase Intent**: `{buyer_panel.get('average_purchase_intent', 0)}` / 100
- **Votes BUY NOW / CONSIDER / PASS**: `{buyer_panel.get('buy_now_votes', 0)} / {buyer_panel.get('consider_votes', 0)} / {buyer_panel.get('pass_votes', 0)}`
- **Panel Verdict**: **{buyer_panel.get('panel_verdict', 'UNVERIFIED')}**
- **Confidence**: `{buyer_panel.get('confidence', 0):.2f}`
- **Diagnostic**: `{buyer_panel.get('error', buyer_panel.get('note', 'Tidak ada error.'))}`

### Aggregate Buyer Reasoning

- **Summary**: {buyer_panel.get('panel_summary', 'Belum tersedia.')}
- **Strongest Segments**: {', '.join(buyer_panel.get('strongest_buyer_segments', [])) or 'Belum tersedia.'}
- **Disagreement**: {buyer_panel.get('disagreement_summary', 'Belum tersedia.')}

### Per-Buyer Evaluation

| Buyer Profile | Demand | Intent | Verdict | Confidence | Purchase Use Case |
| :--- | :---: | :---: | :---: | :---: | :--- |
{chr(10).join([f"| {b.get('profile', 'Unknown')} | {b.get('demand_score', 0)} | {b.get('purchase_intent', 0)} | {b.get('verdict', 'UNVERIFIED')} | {b.get('confidence', 0):.2f} | {b.get('likely_asset_use_case', '')} |" for b in buyer_panel.get('buyers', [])]) or '| Belum ada data buyer panel | — | — | UNVERIFIED | 0.00 | — |'}

---

## 8. Actionable Creative Brief (Panduan Produksi Kontributor)

### Rekomendasi Judul Komersial (Commercial Title)
> **"{brief.get('title_suggestion', topic)}"**

### Tipe Aset yang Disarankan
{chr(10).join([f"- **{t}**" for t in brief.get('recommended_asset_types', ['Photo', 'Generative AI'])])}

### Resep Prompt AI Generation (Midjourney / Flux / Adobe Firefly)
```text
{brief.get('prompt_recipe', 'Professional commercial stock photography...')}
```

---

## 9. Daftar 30–50 Keyword Siap Pakai (Tags)

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
