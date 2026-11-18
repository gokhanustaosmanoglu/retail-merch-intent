"""Input checks shared by the formula modules."""

from __future__ import annotations


def ratio(numerator: float, denominator: float, denominator_name: str) -> float:
    """Divide, refusing a zero or negative base instead of returning nonsense."""
    if denominator <= 0:
        raise ValueError(f"{denominator_name} must be greater than zero, got {denominator}")
    return numerator / denominator


def share(value: float, name: str) -> float:
    """Require a rate written as a fraction (0.30), not a percentage (30)."""
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")
    return value


def non_negative(value: float, name: str) -> float:
    if value < 0:
        raise ValueError(f"{name} must not be negative, got {value}")
    return value
