"""Evidence and demand verification using a second OpenRouter model.

This agent does not replace the deterministic Opportunity Score. It audits the
quality of the evidence and produces explicitly labelled commercial scenarios.
"""

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


class VerificationAgent:
    """Use an optional second model to challenge research assumptions."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_REASONING_MODEL")
        self.reasoning_effort = os.getenv("OPENROUTER_REASONING_EFFORT", "high")
        self.enabled = bool(self.api_key and self.model)
        self.client = None
        if self.enabled:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )

    def verify(self, research: Dict[str, Any]) -> Dict[str, Any]:
        """Audit evidence and return a conservative, structured forecast."""
        if not self.enabled:
            return {
                "status": "NOT_CONFIGURED",
                "model": None,
                "final_verdict": "UNVERIFIED",
                "confidence": 0.0,
                "note": "Set OPENROUTER_REASONING_MODEL to enable the second-model audit.",
            }

        prompt = f"""You are a senior, skeptical market-intelligence reviewer for commercial stock imagery.
Perform a deep evidence reconciliation over the research JSON below. Do not invent absolute search
volume, Adobe Stock catalog counts, sales, downloads, or conversion rates. Google Trends values are
normalized indices unless explicit absolute volume evidence is present. Adobe Stock counts obtained
through Tavily are estimates and may represent indexed snippets rather than the full catalog.

Use this internal workflow before producing the JSON:
1. Build an evidence register: claim, source, observation, time period, and evidence quality.
2. Separate observed facts, derived metrics, heuristic estimates, and forecasts.
3. Cross-check Google Trends against Shutterstock Trends, Pinterest Trends, Tavily market articles,
   and Adobe Stock snippets. Note agreement, mismatch, stale evidence, and missing measurements.
4. Test whether a growth claim has a valid baseline and whether demand is buyer intent or merely
   consumer attention. Penalize evidence that is only a search snippet or a generic article.
5. Assess supply-gap confidence separately from demand confidence. Never treat low indexing as proof
   of low competition or high sales potential.
6. Produce three conservative demand scenarios and a final verdict. The final output must be useful
   for a production decision while clearly stating uncertainty.

Return ONLY valid JSON with exactly these top-level keys:
{{
  "trend_audit": {{
    "claim": "...",
    "period_assessment": "...",
    "absolute_volume_available": false,
    "validity": "VALID|PARTIAL|UNVERIFIED",
    "reason": "...",
    "confidence": 0.0
  }},
  "competition_audit": {{
    "value_type": "ESTIMATE|OBSERVED_SNIPPET|UNVERIFIED",
    "method_quality": "WEAK|MODERATE|STRONG",
    "catalog_directly_verified": false,
    "reason": "...",
    "confidence": 0.0
  }},
  "commercial_demand": {{
    "buyer_need": "LOW|MEDIUM|HIGH",
    "evidence": ["..."],
    "source_agreement": "STRONG|MIXED|WEAK|NONE",
    "unmet_visual_angle": "...",
    "confidence": 0.0
  }},
  "commercial_forecast": {{
    "base_case": "...",
    "upside_case": "...",
    "downside_case": "...",
    "sales_prediction_allowed": false,
    "confidence": 0.0
  }},
  "recommended_next_checks": ["..."],
  "evidence_register": [
    {{"claim": "...", "source": "...", "type": "OBSERVED|DERIVED|ESTIMATE|FORECAST", "quality": "HIGH|MEDIUM|LOW", "note": "..."}}
  ],
  "conflicts_and_caveats": ["..."],
  "decision_summary": "Short rationale, maximum 3 sentences; do not reveal hidden chain-of-thought.",
  "final_verdict": "PROMISING_BUT_UNVERIFIED|PROMISING_WITH_EVIDENCE|WEAK_EVIDENCE|REJECT",
  "confidence": 0.0
}}

Research JSON:
{json.dumps(research, ensure_ascii=False, default=str)}
"""
        try:
            request = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Return only strict JSON. Be conservative and evidence-based."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 2200,
                "response_format": {"type": "json_object"},
                "reasoning_effort": self.reasoning_effort,
            }
            try:
                response = self.client.chat.completions.create(**request)
            except Exception:
                # Some OpenRouter providers may not expose reasoning_effort or JSON mode.
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
            parsed = json.loads(raw.strip())
            if not isinstance(parsed, dict):
                raise ValueError("verification response is not an object")
            parsed["status"] = "COMPLETED"
            parsed["model"] = self.model
            return parsed
        except Exception as exc:
            logger.warning("Second-model verification failed: %s", exc)
            return {
                "status": "ERROR",
                "model": self.model,
                "final_verdict": "UNVERIFIED",
                "confidence": 0.0,
                "error": str(exc),
            }
