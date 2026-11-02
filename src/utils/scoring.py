"""Utility module for calculating the Opportunity Score.

Formula:
Opportunity Score = (S_trend * 0.4) + (S_tavily * 0.3) + (G_stock * 0.3)
"""

def calculate_stock_gap_score(asset_count: int) -> float:
    """Calculate the stock competition gap score (G_stock) based on indexed asset volume.
    
    Low indexed asset count = high opportunity gap (90-100).
    Moderate asset count = moderate opportunity (60-80).
    Over-saturated asset count = low opportunity (<40).
    """
    if asset_count <= 0:
        return 95.0
    elif asset_count < 500:
        return 95.0
    elif asset_count < 1500:
        return 88.0
    elif asset_count < 5000:
        return 78.0
    elif asset_count < 15000:
        return 65.0
    elif asset_count < 50000:
        return 48.0
    else:
        return max(20.0, 40.0 - ((asset_count - 50000) / 100000) * 10)


def calculate_opportunity_score(
    trend_score: float,
    tavily_score: float,
    asset_count: int
) -> dict:
    """Compute overall Opportunity Score and recommendation level.
    
    Weights:
    - Google Trends (S_trend): 40%
    - Tavily Market Intel (S_tavily): 30%
    - Adobe Stock Gap (G_stock): 30%
    """
    # Clamp inputs between 0 and 100
    s_trend = max(0.0, min(100.0, float(trend_score)))
    s_tavily = max(0.0, min(100.0, float(tavily_score)))
    g_stock = calculate_stock_gap_score(asset_count)

    total_score = round((s_trend * 0.4) + (s_tavily * 0.3) + (g_stock * 0.3), 1)

    if total_score >= 80.0:
        recommendation = "HIGH OPPORTUNITY"
        recommendation_label = "Peluang Sangat Tinggi (Prioritas Produksi)"
    elif total_score >= 65.0:
        recommendation = "MODERATE OPPORTUNITY"
        recommendation_label = "Peluang Bagus (Diferensiasi Diperlukan)"
    else:
        recommendation = "LOW OPPORTUNITY"
        recommendation_label = "Peluang Rendah / Pasar Jenuh"

    return {
        "total_score": total_score,
        "recommendation": recommendation,
        "recommendation_label": recommendation_label,
        "breakdown": {
            "trend_score": s_trend,
            "trend_weight": 0.4,
            "tavily_score": s_tavily,
            "tavily_weight": 0.3,
            "stock_gap_score": g_stock,
            "stock_gap_weight": 0.3,
            "indexed_assets": asset_count
        }
    }
