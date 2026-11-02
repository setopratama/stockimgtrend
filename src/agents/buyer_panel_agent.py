"""Ten-persona buyer panel for commercial stock-image demand validation."""

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


BUYER_PROFILES = [
    "Creative Director at a global advertising agency",
    "Content lead at a B2B SaaS company",
    "Healthcare communications manager",
    "ESG and sustainability campaign strategist",
    "HR and DEI employer-branding manager",
    "Editorial and publishing art director",
    "E-commerce growth marketer",
    "Education and e-learning content producer",
    "Social media content studio producer",
    "Small business owner with limited creative budget",
]


class BuyerPanelAgent:
    """Ask one reasoning model to simulate ten distinct stock-image buyers."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_REASONING_MODEL")
        self.reasoning_effort = os.getenv("OPENROUTER_REASONING_EFFORT", "high")
        self.enabled = bool(self.api_key and self.model)
        self.client = None
        if self.enabled:
            from openai import OpenAI
            self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.api_key)

    def evaluate(self, research: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "status": "NOT_CONFIGURED",
                "model": None,
                "expected_buyer_count": len(BUYER_PROFILES),
                "buyer_count": 0,
                "panel_verdict": "UNVERIFIED",
                "confidence": 0.0,
            }

        profiles = "\n".join(f"{idx + 1}. {profile}" for idx, profile in enumerate(BUYER_PROFILES))
        prompt = f"""You are running a buyer-panel simulation for a commercial stock-image research pipeline.
Evaluate the COMPLETE research package below from ten different buyer profiles. Do not invent sales,
budgets, downloads, or conversion rates. Treat Google Trends as normalized interest, Adobe counts as
Tavily estimates, and platform snippets as evidence with limited coverage.

Buyer profiles:
{profiles}

For EACH buyer, independently assess all available evidence and return:
- demand_score (0-100)
- purchase_intent (0-100)
- likely_asset_use_case
- what_visual_asset_they_would_buy
- strongest_evidence
- objection_or_missing_evidence
- verdict (BUY_NOW|CONSIDER|PASS)
- confidence (0-1)

Then calculate a panel-level decision. Use arithmetic over the ten scores; do not let one profile
dominate. Highlight disagreement and segments where the opportunity is strongest. Return ONLY valid
JSON with this shape:
{{
  "status": "COMPLETED",
  "model": "...",
  "buyers": [
    {{"profile": "...", "demand_score": 0, "purchase_intent": 0, "likely_asset_use_case": "...", "what_visual_asset_they_would_buy": "...", "strongest_evidence": "...", "objection_or_missing_evidence": "...", "verdict": "BUY_NOW|CONSIDER|PASS", "confidence": 0.0}}
  ],
  "panel_summary": "...",
  "average_demand_score": 0.0,
  "average_purchase_intent": 0.0,
  "buy_now_votes": 0,
  "consider_votes": 0,
  "pass_votes": 0,
  "strongest_buyer_segments": ["..."],
  "disagreement_summary": "...",
  "panel_verdict": "STRONG_BUYER_SIGNAL|SELECTIVE_BUYER_SIGNAL|WEAK_BUYER_SIGNAL|NO_SIGNAL",
  "confidence": 0.0
}}

Research package:
{json.dumps(research, ensure_ascii=False, default=str)}
"""
        request = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return only strict JSON. Simulate each buyer independently and be conservative."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.15,
            "max_tokens": 5000,
            "response_format": {"type": "json_object"},
            "reasoning_effort": self.reasoning_effort,
        }
        try:
            try:
                response = self.client.chat.completions.create(**request)
            except Exception:
                request.pop("reasoning_effort", None)
                request.pop("response_format", None)
                response = self.client.chat.completions.create(**request)
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            result = json.loads(raw.strip())
            if not isinstance(result, dict):
                raise ValueError("buyer panel response is not an object")
            result["status"] = "COMPLETED"
            result["model"] = self.model
            buyers = result.get("buyers", [])
            if not isinstance(buyers, list):
                raise ValueError("buyer panel JSON field 'buyers' is not a list")
            result["expected_buyer_count"] = len(BUYER_PROFILES)
            result["buyer_count"] = len(buyers)
            if len(buyers) < len(BUYER_PROFILES):
                result["status"] = "INCOMPLETE"
                result["error"] = f"Expected {len(BUYER_PROFILES)} buyers, received {len(buyers)}"
            return result
        except Exception as exc:
            logger.warning("Buyer panel reasoning failed: %s", exc)
            return {
                "status": "ERROR",
                "model": self.model,
                "expected_buyer_count": len(BUYER_PROFILES),
                "buyer_count": 0,
                "panel_verdict": "UNVERIFIED",
                "confidence": 0.0,
                "error": str(exc),
            }
