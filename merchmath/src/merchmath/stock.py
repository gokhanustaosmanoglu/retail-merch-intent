"""Cover and stock-turn measures."""

from __future__ import annotations

import math
from typing import Sequence

from ._check import non_negative, ratio


def weeks_of_cover(stock: float, average_weekly_sales: float) -> float:
    """Backward-looking cover: stock / average weekly sales."""
    return ratio(stock, average_weekly_sales, "average_weekly_sales")


def forward_cover(stock: float, forecast_sales: Sequence[float]) -> float:
    """Weeks the stock lasts against a week-by-week sales forecast.

    Whole weeks are counted as they are consumed; the week in which stock runs
    out counts as the fraction of it that was covered. Returns ``math.inf``
    when the stock outlasts the whole forecast.
    """
    remaining = non_negative(stock, "stock")
    weeks = 0.0
    for sales in forecast_sales:
        if sales < 0:
            raise ValueError(f"forecast_sales must not contain negatives, got {sales}")
        if remaining == 0:
            return weeks
        if sales >= remaining:
            return weeks + remaining / sales
        remaining -= sales
        weeks += 1
    return weeks if remaining == 0 else math.inf


def average_stock(opening_stock: float, closing_stocks: Sequence[float]) -> float:
    """Average of the opening position and every period's closing position."""
    return (opening_stock + sum(closing_stocks)) / (len(closing_stocks) + 1)


def stock_turn(sales: float, average_stock: float) -> float:
    """Sales / average stock. Use the same valuation (cost or retail) for both."""
    return ratio(sales, average_stock, "average_stock")
