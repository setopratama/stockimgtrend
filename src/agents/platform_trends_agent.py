"""Platform trend intelligence through Tavily Cloud.

The project intentionally does not scrape Shutterstock or Pinterest locally.
Tavily is used as the cloud retrieval layer and every result is labelled as
platform evidence, not as a full catalog audit.
"""

import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PlatformTrendsAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY tidak ditemukan di environment variables.")
        from tavily import TavilyClient
        self.client = TavilyClient(api_key=self.api_key)

    def _search_platform(self, keyword: str, platform: str, domain: str, query: str) -> Dict[str, Any]:
        try:
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_domains=[domain],
                include_answer=True,
            )
        except Exception as exc:
            logger.error("Platform trend search failed for %s: %s", platform, exc)
            response = {}

        results = response.get("results", [])
        references: List[Dict[str, str]] = []
        for item in results:
            references.append({
                "title": item.get("title", "Platform trend result"),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:500],
            })

        return {
            "platform": platform,
            "keyword": keyword,
            "source_url": "https://www.shutterstock.com/id/trends" if platform == "Shutterstock" else "https://trends.pinterest.com/",
            "method": "tavily_cloud_search",
            "query": query,
            "answer": response.get("answer", ""),
            "references": references,
            "indexed_result_count": len(results),
            "data_type": "platform_indexed_evidence",
            "direct_catalog_audit": False,
            "confidence": 0.55 if results else 0.10,
        }

    def research(self, keyword: str) -> Dict[str, Any]:
        """Collect platform signals for the target keyword via Tavily only."""
        shutterstock = self._search_platform(
            keyword,
            "Shutterstock",
            "shutterstock.com",
            f'site:shutterstock.com/id/trends "{keyword}" stock image trends demand growth results',
        )
        pinterest = self._search_platform(
            keyword,
            "Pinterest",
            "trends.pinterest.com",
            f'site:trends.pinterest.com "{keyword}" Pinterest Trends search interest',
        )
        return {
            "method": "Tavily Cloud only; no local platform scraping",
            "sources": {
                "shutterstock_trends": shutterstock,
                "pinterest_trends": pinterest,
            },
            "source_urls": [shutterstock["source_url"], pinterest["source_url"]],
            "confidence": round((shutterstock["confidence"] + pinterest["confidence"]) / 2, 2),
        }
