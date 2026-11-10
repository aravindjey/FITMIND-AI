"""Pure deterministic unit conversion engine."""


def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds."""
    if kg < 0:
        raise ValueError("Weight cannot be negative.")
    return round(kg * 2.20462, 2)


def lbs_to_kg(lbs: float) -> float:
    """Convert pounds to kilograms."""
    if lbs < 0:
        raise ValueError("Weight cannot be negative.")
    return round(lbs / 2.20462, 2)


def cm_to_inches(cm: float) -> float:
    """Convert centimeters to inches."""
    if cm < 0:
        raise ValueError("Height cannot be negative.")
    return round(cm / 2.54, 2)


def inches_to_cm(inches: float) -> float:
    """Convert inches to centimeters."""
    if inches < 0:
        raise ValueError("Height cannot be negative.")
    return round(inches * 2.54, 2)
