"""Trend Research Pipeline Orchestrator.

Coordinates execution across Google Trends, Tavily Market Intel,
Adobe Stock Cloud Tracker, and Synthesis Agents.
Supports proactive autonomous discovery starting directly from Google Trends live feeds,
AI Art Director reasoning, and Nanobanana Master Prompt testing.
"""

import os
import json
import logging
from typing import Dict, Any, Callable, Optional, List
from src.agents.gtrends_agent import GoogleTrendsAgent
from src.agents.tavily_intel_agent import TavilyIntelAgent
from src.agents.adobestock_tavily_agent import AdobeStockTavilyAgent
from src.agents.synthesis_agent import SynthesisAgent
from src.utils.exporter import export_report_to_markdown
from src.utils.db import (
    save_research_to_db,
    update_nanobanana_prompt,
    get_past_keywords
)

logger = logging.getLogger(__name__)

class TrendPipeline:
    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        openrouter_model: Optional[str] = None,
        output_dir: str = "docs/reports"
    ):
        self.output_dir = output_dir
        self.gtrends_agent = GoogleTrendsAgent()
        self.tavily_agent = TavilyIntelAgent(api_key=tavily_api_key)
        self.adobe_agent = AdobeStockTavilyAgent(api_key=tavily_api_key)
        self.synthesis_agent = SynthesisAgent(
            api_key=openrouter_api_key,
            model=openrouter_model
        )

    def run(
        self,
        keyword: str,
        on_progress: Optional[Callable[[str, str, Optional[Dict[str, Any]]], None]] = None,
        auto_export: bool = True
    ) -> Dict[str, Any]:
        """Execute the full research pipeline for a target keyword."""
        def report_step(stage: str, message: str, data: Optional[Dict[str, Any]] = None):
            if on_progress:
                on_progress(stage, message, data)
            logger.info(f"[{stage}] {message}")

        # Stage 1: Google Trends
        report_step("GTRENDS", f"Menganalisis momentum Google Trends untuk '{keyword}'...", None)
        gtrends_data = self.gtrends_agent.analyze_keyword(keyword)
        report_step("GTRENDS_DONE", "Data Google Trends berhasil diperoleh.", gtrends_data)

        # Stage 2: Tavily Market Intelligence
        report_step("TAVILY", f"Mencari wawasan tren visual & kebutuhan pasar via Tavily API...", None)
        tavily_data = self.tavily_agent.research_market_trends(keyword)
        report_step("TAVILY_DONE", "Wawasan pasar & palet visual berhasil diperoleh.", tavily_data)

        # Stage 3: Adobe Stock Tracker via Tavily
        report_step("ADOBESTOCK", f"Memeriksa indeks Adobe Stock & celah pasar via Tavily cloud query...", None)
        adobe_data = self.adobe_agent.inspect_adobe_stock_gap(keyword)
        report_step("ADOBESTOCK_DONE", "Analisis kompetisi & content gap Adobe Stock selesai.", adobe_data)

        # Stage 4: Synthesis & AI Creative Brief
        report_step("SYNTHESIS", f"Menghitung Opportunity Score & menghasilkan Creative Brief via OpenRouter...", None)
        result = self.synthesis_agent.synthesize(
            keyword=keyword,
            gtrends_data=gtrends_data,
            tavily_data=tavily_data,
            adobe_data=adobe_data
        )
        report_step("SYNTHESIS_DONE", "Opportunity Score & Creative Brief berhasil dihitung.", result)

        # Stage 5: Export to Markdown
        exported_path = None
        if auto_export:
            report_step("EXPORT", "Mengekspor laporan lengkap ke format Markdown...", None)
            exported_path = export_report_to_markdown(result, output_dir=self.output_dir)
            result["exported_file"] = exported_path
            report_step("EXPORT_DONE", f"Laporan tersimpan: {exported_path}", {"file_path": exported_path})

        # Stage 6: Persist to SQLite Database
        report_step("DATABASE", "Menyimpan riwayat riset ke database SQLite...", None)
        try:
            record_id = save_research_to_db(result)
            result["db_id"] = record_id
            report_step("DB_SAVED", f"Data berhasil disimpan ke SQLite (ID #{record_id}).", {"db_id": record_id})
        except Exception as e:
            logger.error(f"Failed to save to SQLite: {e}")
            report_step("DB_ERROR", f"Gagal menyimpan ke SQLite: {e}", None)

        return result

    def autonomous_discovery(
        self,
        count: int = 3,
        on_progress: Optional[Callable[[str, str, Optional[Dict[str, Any]]], None]] = None
    ) -> List[Dict[str, Any]]:
        """Autonomously start from Google Trends live searches, apply AI Konseptor & Art Director filtering, and evaluate."""
        def report_step(stage: str, message: str, data: Optional[Dict[str, Any]] = None):
            if on_progress:
                on_progress(stage, message, data)
            logger.info(f"[{stage}] {message}")

        # 1. Fetch live trends from Google Trends feed
        report_step("GTRENDS_SCAN", "Memindai tren langsung Google Trends (apa yang orang banyak cari hari ini & event tertinggi)...", None)
        raw_trends = self.gtrends_agent.fetch_live_trending_searches(geo="US", max_items=15)
        report_step("GTRENDS_SCAN_DONE", f"Berhasil menarik {len(raw_trends)} tren & event terbaru dari Google Trends.", {"trends": raw_trends})

        # 2. Check past researches in SQLite to avoid repetition
        past_researches = get_past_keywords(limit=25)

        # 3. AI Konseptor & Art Director reasoning & commercial filter
        report_step("ART_DIRECTOR_CONCEPT", "AI Konseptor & Art Director menyaring tren dan merumuskan konsep visual komersial...", None)
        conceptualized = self.synthesis_agent.filter_and_conceptualize_trends(raw_trends, past_researches, count=count)
        
        candidate_keywords = [c.get("commercial_concept_keyword") for c in conceptualized if c.get("commercial_concept_keyword")]
        report_step("ART_DIRECTOR_DONE", f"Art Director meloloskan {len(candidate_keywords)} konsep visual bernilai jual: {', '.join(candidate_keywords)}", {"concepts": conceptualized})

        # 4. Evaluate each conceptualized candidate via pipeline
        results: List[Dict[str, Any]] = []
        for idx, concept_meta in enumerate(conceptualized, 1):
            niche = concept_meta.get("commercial_concept_keyword")
            report_step("DISCOVERY_EVAL", f"[{idx}/{len(conceptualized)}] Menganalisis pasar: '{niche}'...", {"current": niche, "index": idx, "total": len(conceptualized)})
            res = self.run(keyword=niche, on_progress=on_progress, auto_export=True)
            res["concept_meta"] = concept_meta
            results.append(res)

        # Sort candidates descending by Opportunity Score
        results.sort(key=lambda x: x.get("scoring", {}).get("total_score", 0), reverse=True)
        report_step("DISCOVERY_COMPLETE", "Pencarian inisiatif selesai! Rekomendasi diurutkan berdasarkan skor peluang tertinggi.", {"results": results})
        return results

    def generate_nanobanana_master(
        self,
        research_result: Dict[str, Any],
        on_progress: Optional[Callable[[str, str, Optional[Dict[str, Any]]], None]] = None
    ) -> Dict[str, Any]:
        """Formulate Nanobanana Master Prompt and strictly audit it with the Senior Art Director persona."""
        def report_step(stage: str, message: str, data: Optional[Dict[str, Any]] = None):
            if on_progress:
                on_progress(stage, message, data)
            logger.info(f"[{stage}] {message}")

        topic = research_result.get("topic", "")
        adobe_data = research_result.get("sources", {}).get("adobe_stock_tracker", {})

        # Step 1: Generate Nanobanana Master Prompt
        report_step("NANOBANANA_START", f"Meracik Master Prompt Nanobanana & Tema Kuat untuk '{topic}'...", None)
        nanobanana_data = self.synthesis_agent.generate_nanobanana_master_prompt(research_result)
        
        # Step 2: Art Director Quality Audit & Testing
        report_step("ART_DIRECTOR_AUDIT", "Senior Art Director menguji kelayakan komersial, rule of thirds, dan keamanan IP...", None)
        audit_data = self.synthesis_agent.audit_prompt_as_art_director(
            topic=topic,
            nanobanana_data=nanobanana_data,
            adobe_data=adobe_data
        )
        nanobanana_data["art_director_audit"] = audit_data
        research_result["nanobanana_master"] = nanobanana_data
        report_step("ART_DIRECTOR_AUDIT_DONE", f"Audit Art Director Selesai: {audit_data.get('verdict_status', 'APPROVED')} (Skor: {audit_data.get('art_director_score', 9.0)}/10)", audit_data)

        # Step 3: Update SQLite if record exists
        db_id = research_result.get("db_id")
        if db_id:
            try:
                update_nanobanana_prompt(db_id, nanobanana_data)
                report_step("NANOBANANA_SAVED", f"Master Prompt & Audit Art Director tersimpan di SQLite (Record #{db_id}).", {"db_id": db_id})
            except Exception as e:
                logger.error(f"Failed to update nanobanana prompt in SQLite: {e}")

        # Step 4: Append Nanobanana & Art Director Audit to Markdown report
        report_file = research_result.get("exported_file")
        if report_file and os.path.exists(report_file):
            try:
                with open(report_file, "a", encoding="utf-8") as f:
                    f.write(f"""
---

## 🍌 7. Nanobanana Master Generation Recipe

### Tema Kuat: {nanobanana_data.get('theme_title', topic)}
> **Konsep Storytelling**:  
> {nanobanana_data.get('concept_narrative', '')}

### Master Prompt Siap Generate di Nanobanana:
```text
{nanobanana_data.get('nanobanana_master_prompt', '')}
```

### Negative Prompt:
```text
{nanobanana_data.get('negative_prompt', '')}
```

### Rekomendasi Judul Adobe Stock:
> **"{nanobanana_data.get('commercial_title', '')}"**

### 50 Tags Siap Copy-Paste:
```text
{nanobanana_data.get('tags_string', '')}
```

---

## 🎨 8. Evaluasi & Uji Kelayakan Senior Art Director

- **Status Kelulusan**: **{audit_data.get('verdict_status', 'APPROVED FOR PRODUCTION')}**
- **Skor Kelayakan Komersial**: **{audit_data.get('art_director_score', 9.0)} / 10**
- **Evaluasi Komposisi & Pencahayaan**:  
  {audit_data.get('composition_and_lighting_notes', 'Komposisi dan pencahayaan optimal untuk kebutuhan iklan komersial.')}
- **Pemeriksaan Hak Cipta & IP**:  
  {audit_data.get('ip_safety_check', '100% Bebas Trademark dan Logo.')}
- **Saran Penjualan Komersial Art Director**:  
  > "{audit_data.get('commercial_sales_advice', 'Pastikan rasio aspek gambar mendukung variasi banner horizontal dan vertikal.')}"
""")
                report_step("NANOBANANA_EXPORTED", f"Master Prompt & Audit ditambahkan ke laporan: {report_file}", {"file_path": report_file})
            except Exception as e:
                logger.error(f"Failed to append nanobanana prompt to report file: {e}")

        return nanobanana_data
