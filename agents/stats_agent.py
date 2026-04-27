"""Statistical analysis agent: trend, correlation, and outlier detection on SQL results."""
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats


def _analyze_column(series: pd.Series, col: str) -> dict:
    # Computes descriptive stats, linear trend, and outlier count for one numeric column
    clean = series.dropna()
    if clean.empty:
        return {}

    mean = round(float(clean.mean()), 2)
    std = round(float(clean.std()), 2)
    mn = round(float(clean.min()), 2)
    mx = round(float(clean.max()), 2)

    # Linear trend over row index
    x = np.arange(len(clean))
    slope, _, r_value, _, _ = scipy_stats.linregress(x, clean.values)
    trend = "up" if slope >= 0 else "down"
    r_squared = round(float(r_value ** 2), 3)

    # Outliers: z-score > 2.5
    z_scores = np.abs(scipy_stats.zscore(clean.values))
    outlier_count = int((z_scores > 2.5).sum())

    return {
        "mean": mean,
        "std": std,
        "min": mn,
        "max": mx,
        "trend": trend,
        "r_squared": r_squared,
        "outliers": outlier_count,
    }


def stats_node(state: dict) -> dict:
    # Analyses up to 3 numeric columns; returns empty dict on any error or missing data
    results = state.get("sql_results", [])
    if not results:
        return {"stats": {}}

    try:
        df = pd.DataFrame(results)
        num_cols = df.select_dtypes("number").columns.tolist()[:3]
        findings = {}
        for col in num_cols:
            col_stats = _analyze_column(df[col], col)
            if col_stats:
                findings[col] = col_stats
        return {"stats": findings}
    except Exception:
        return {"stats": {}}
