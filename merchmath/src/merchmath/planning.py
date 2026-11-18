"""Open-to-buy and the weekly sales, stock and intake (WSSI) roll-forward."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


def open_to_buy(
    *,
    planned_sales: float,
    planned_markdowns: float,
    planned_closing_stock: float,
    opening_stock: float,
    on_order: float,
) -> float:
    """Budget still free to commit for the period.

    planned sales + planned markdowns + planned closing stock
    - opening stock - on order.

    All inputs on one valuation (retail value is the usual choice). A negative
    result means the period is already overbought.
    """
    return planned_sales + planned_markdowns + planned_closing_stock - opening_stock - on_order


@dataclass(frozen=True)
class WssiWeek:
    week: int
    opening: float
    intake: float
    sales: float
    closing: float
    cover: Optional[float]


def wssi(
    opening_stock: float,
    *,
    sales: Sequence[float],
    intake: Sequence[float],
    cover_weeks: int = 4,
) -> list[WssiWeek]:
    """Roll stock forward week by week: closing = opening + intake - sales.

    ``cover`` is closing stock over the average sales of the following
    ``cover_weeks`` weeks (fewer near the end of the plan). It is ``None`` when
    no week follows or the following weeks plan no sales. A negative closing
    stock is kept as it is: it shows the shortage the plan has to fix.
    """
    if len(sales) != len(intake):
        raise ValueError(
            f"sales and intake must have the same length, got {len(sales)} and {len(intake)}"
        )
    if cover_weeks <= 0:
        raise ValueError(f"cover_weeks must be a positive integer, got {cover_weeks}")

    weeks: list[WssiWeek] = []
    opening = opening_stock
    for i, (sold, received) in enumerate(zip(sales, intake)):
        closing = opening + received - sold
        ahead = sales[i + 1 : i + 1 + cover_weeks]
        average_ahead = sum(ahead) / len(ahead) if ahead else 0
        cover = closing / average_ahead if average_ahead > 0 else None
        weeks.append(WssiWeek(i + 1, opening, received, sold, closing, cover))
        opening = closing
    return weeks
