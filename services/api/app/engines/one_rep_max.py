"""Pure deterministic 1RM estimation engine."""


def epley_1rm(weight_kg: float, reps: int) -> float:
    """Calculate 1RM using Epley Formula: 1RM = weight * (1 + reps / 30)."""
    if weight_kg <= 0 or reps <= 0:
        return 0.0
    if reps == 1:
        return round(weight_kg, 2)
    return round(weight_kg * (1.0 + reps / 30.0), 2)


def brzycki_1rm(weight_kg: float, reps: int) -> float:
    """Calculate 1RM using Brzycki Formula: 1RM = weight / (1.0278 - 0.0278 * reps)."""
    if weight_kg <= 0 or reps <= 0 or reps >= 37:
        return 0.0
    if reps == 1:
        return round(weight_kg, 2)
    return round(weight_kg / (1.0278 - 0.0278 * reps), 2)


def estimate_1rm(weight_kg: float, reps: int, formula: str = "epley") -> float:
    """Estimate 1RM using specified formula."""
    if formula.lower() == "brzycki":
        return brzycki_1rm(weight_kg, reps)
    return epley_1rm(weight_kg, reps)
