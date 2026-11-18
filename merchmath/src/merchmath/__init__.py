"""merchmath: tested retail merchandising formulas."""

from .intents import INTENTS, IntentSpec
from .margin import (
    breakeven_discount,
    gmroi,
    gross_margin,
    intake_margin,
    margin_after_discount,
    markup,
    net_of_vat,
)
from .planning import WssiWeek, open_to_buy, wssi
from .rates import (
    asp,
    bottom_n,
    capacity_fill,
    discount_rate,
    full_price_share,
    growth,
    return_rate,
    sell_through,
    sell_through_from_stock,
    top_n,
)
from .sizes import is_broken, size_availability
from .stock import average_stock, forward_cover, stock_turn, weeks_of_cover

__version__ = "0.1.0"

__all__ = [
    "INTENTS",
    "IntentSpec",
    "WssiWeek",
    "asp",
    "average_stock",
    "bottom_n",
    "breakeven_discount",
    "capacity_fill",
    "discount_rate",
    "forward_cover",
    "full_price_share",
    "gmroi",
    "gross_margin",
    "growth",
    "intake_margin",
    "is_broken",
    "margin_after_discount",
    "markup",
    "net_of_vat",
    "open_to_buy",
    "return_rate",
    "sell_through",
    "sell_through_from_stock",
    "size_availability",
    "stock_turn",
    "top_n",
    "weeks_of_cover",
    "wssi",
]
