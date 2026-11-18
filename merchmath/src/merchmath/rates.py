"""Sales, price and ranking ratios."""

from __future__ import annotations

from typing import Mapping

from ._check import ratio


def sell_through(units_sold: float, units_received: float) -> float:
    """Share of received units that sold: sold / received."""
    return ratio(units_sold, units_received, "units_received")


def sell_through_from_stock(units_sold: float, closing_stock: float) -> float:
    """Sell-through when intake is unknown: sold / (sold + closing stock)."""
    return ratio(units_sold, units_sold + closing_stock, "units_sold + closing_stock")


def growth(actual: float, base: float) -> float:
    """Change versus a base (last year, plan, budget): actual / base - 1."""
    return ratio(actual, base, "base") - 1


def return_rate(units_returned: float, units_sold: float) -> float:
    """Returned units as a share of sold units."""
    return ratio(units_returned, units_sold, "units_sold")


def asp(revenue: float, units: float) -> float:
    """Average selling price: revenue / units. Keep revenue on one VAT basis."""
    return ratio(revenue, units, "units")


def discount_rate(original_price: float, sold_price: float) -> float:
    """Share taken off the original price: 1 - sold / original."""
    return 1 - ratio(sold_price, original_price, "original_price")


def full_price_share(full_price_sales: float, total_sales: float) -> float:
    """Share of sales made at full price."""
    return ratio(full_price_sales, total_sales, "total_sales")


def capacity_fill(stock_units: float, capacity_units: float) -> float:
    """Stock as a share of store capacity. Above 1 means overstocked."""
    return ratio(stock_units, capacity_units, "capacity_units")


def _ranked(values: Mapping[str, float], n: int, highest_first: bool) -> list[tuple[str, float]]:
    if n <= 0:
        raise ValueError(f"n must be a positive integer, got {n}")
    sign = -1 if highest_first else 1
    return sorted(values.items(), key=lambda kv: (sign * kv[1], kv[0]))[:n]


def top_n(values: Mapping[str, float], n: int) -> list[tuple[str, float]]:
    """The n highest entries, highest first; ties ordered by key."""
    return _ranked(values, n, highest_first=True)


def bottom_n(values: Mapping[str, float], n: int) -> list[tuple[str, float]]:
    """The n lowest entries, lowest first; ties ordered by key."""
    return _ranked(values, n, highest_first=False)
