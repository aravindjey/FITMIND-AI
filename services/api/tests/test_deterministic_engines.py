import pytest
from app.engines.conversions import kg_to_lbs, lbs_to_kg, cm_to_inches, inches_to_cm
from app.engines.one_rep_max import epley_1rm, brzycki_1rm, estimate_1rm
from app.engines.weight_trend import calculate_ema_weight_trend, calculate_rate_of_change


def test_unit_conversions():
    assert kg_to_lbs(100.0) == 220.46
    assert lbs_to_kg(220.46) == 100.0
    assert cm_to_inches(178.0) == 70.08
    assert inches_to_cm(70.08) == 178.0

    with pytest.raises(ValueError):
        kg_to_lbs(-5.0)


def test_1rm_calculations():
    # 1 rep at 100kg should return 100kg
    assert epley_1rm(100.0, 1) == 100.0
    assert brzycki_1rm(100.0, 1) == 100.0

    # 100kg for 10 reps
    # Epley: 100 * (1 + 10/30) = 133.33 kg
    assert epley_1rm(100.0, 10) == 133.33
    # Brzycki: 100 / (1.0278 - 0.278) = 133.37 kg
    assert brzycki_1rm(100.0, 10) == 133.37

    assert estimate_1rm(100.0, 10, formula="epley") == 133.33
    assert estimate_1rm(100.0, 10, formula="brzycki") == 133.37


def test_weight_trend_calculations():
    weights = [80.0, 80.5, 79.8, 80.2, 79.5, 79.4, 79.0]
    ema = calculate_ema_weight_trend(weights, alpha=0.25)
    assert len(ema) == len(weights)
    assert ema[0] == 80.0
    # Values should decrease smoothly
    assert ema[-1] < weights[0]

    rate = calculate_rate_of_change(weights, window_days=7)
    assert rate < 0.0  # Overall downward weight trend
