"""Adobe Stock Tracker Agent (via Tavily Cloud Proxy).

Validates competition, indexed asset volume, and content gaps in Adobe Stock
WITHOUT direct local scraping (100% cloud queries through Tavily).
"""

import os
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AdobeStockTavilyAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY tidak ditemukan di environment variables.")
        from tavily import TavilyClient
        self.client = TavilyClient(api_key=self.api_key)

    def _extract_asset_count_from_text(self, text: str) -> int:
        """Parse asset count from Adobe Stock titles or snippets like 'Browse 1,387,285 Stock Photos'."""
        patterns = [
            r"browse\s+([\d,]+)\s+stock",
            r"([\d,]+)\s+stock\s+photos",
            r"([\d,]+)\s+results",
            r"over\s+([\d,]+)\s+royalty-free"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_number = match.group(1).replace(",", "")
                try:
                    return int(raw_number)
                except ValueError:
                    continue
        return 0

    def inspect_adobe_stock_gap(self, keyword: str) -> Dict[str, Any]:
        """Track keyword competition on Adobe Stock safely via Tavily site search."""
        query = f'site:stock.adobe.com "{keyword}"'
        logger.info(f"Querying Tavily for Adobe Stock index: '{query}'")

        try:
            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=6,
                include_domains=["stock.adobe.com"]
            )
        except Exception as e:
            logger.error(f"Error querying Adobe Stock via Tavily: {e}")
            response = {}

        results = response.get("results", [])
        estimated_assets = 0
        snippets: List[str] = []
        parsed_exact_count = False

        for r in results:
            title = r.get("title", "")
            content = r.get("content", "")
            snippets.append(f"{title}: {content[:180]}")

            # Try to parse asset count from title first, then content
            count_from_title = self._extract_asset_count_from_text(title)
            if count_from_title > estimated_assets:
                estimated_assets = count_from_title
                parsed_exact_count = True
            
            count_from_content = self._extract_asset_count_from_text(content)
            if count_from_content > estimated_assets:
                estimated_assets = count_from_content
                parsed_exact_count = True

        # Fallback estimation if exact number wasn't explicitly mentioned in snippets
        if estimated_assets == 0:
            if len(results) >= 5:
                estimated_assets = 4500  # Moderate indexed volume
            elif len(results) > 0:
                estimated_assets = 850   # Low volume / Blue ocean
            else:
                estimated_assets = 250   # Rare / Unmet demand

        estimate_quality = "observed_snippet" if parsed_exact_count else "heuristic_result_count"
        confidence = 0.55 if parsed_exact_count else (0.25 if results else 0.10)

        # Determine competition level
        if estimated_assets < 1000:
            competition_level = "Sangat Rendah (Blue Ocean)"
            gap_analysis = f"Sangat sedikit aset terindeks untuk '{keyword}'. Peluang emas bagi kontributor untuk mendominasi halaman pertama."
        elif estimated_assets < 10000:
            competition_level = "Moderat (Peluang Bagus)"
            gap_analysis = f"Terdapat sekitar {estimated_assets:,} aset. Masih ada ruang besar untuk visual otentik dengan variasi gaya terkini."
        else:
            competition_level = "Tinggi / Jenuh"
            gap_analysis = f"Pasar sudah memiliki {estimated_assets:,} aset. Disarankan membuat konsep turunan (long-tail) atau sudut pandang visual yang unik."

        return {
            "keyword": keyword,
            "method": "tavily_site_search",
            "search_query": query,
            "total_results": estimated_assets,
            "value_type": "ESTIMATE",
            "catalog_directly_verified": False,
            "estimate_quality": estimate_quality,
            "confidence": confidence,
            "indexed_result_count": len(results),
            "estimate_note": "Tavily-indexed estimate; not a direct audit of the full Adobe Stock catalog.",
            "competition_level": competition_level,
            "gap_analysis": gap_analysis,
            "sample_snippets": snippets[:3]
        }
