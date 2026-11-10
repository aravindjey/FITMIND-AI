"""Pure deterministic weight trend moving average engine."""
from typing import List


def calculate_ema_weight_trend(weights: List[float], alpha: float = 0.25) -> List[float]:
    """Calculates Exponential Moving Average (EMA) for weight series.
    EMA_t = (Weight_t * alpha) + (EMA_{t-1} * (1 - alpha))
    """
    if not weights:
        return []

    ema_series = []
    current_ema = weights[0]
    ema_series.append(round(current_ema, 2))

    for w in weights[1:]:
        current_ema = (w * alpha) + (current_ema * (1.0 - alpha))
        ema_series.append(round(current_ema, 2))

    return ema_series


def calculate_rate_of_change(weights: List[float], window_days: int = 7) -> float:
    """Calculates weight change (kg/week) over window."""
    if len(weights) < 2:
        return 0.0

    trend = calculate_ema_weight_trend(weights)
    start_val = trend[0]
    end_val = trend[-1]
    days = max(1, len(weights) - 1)

    # Convert to weekly rate of change
    weekly_change = ((end_val - start_val) / days) * 7.0
    return round(weekly_change, 2)
