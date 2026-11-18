"""Which formula answers which question type.

Keys are the intent labels of the ``retail-merch-intent`` dataset. A classifier
picks the intent and the slots; this table names the function that computes
the answer, so no model ever produces a number.

kind:
  calc     answered by the listed functions
  lookup   a plain data read (stock on hand, order status); nothing to compute
  planned  needs a formula this version does not ship yet
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentSpec:
    kind: str
    functions: tuple[str, ...] = ()


INTENTS: dict[str, IntentSpec] = {
    "sales": IntentSpec("lookup"),
    "growth": IntentSpec("calc", ("growth",)),
    "stock": IntentSpec("lookup"),
    "cover": IntentSpec("calc", ("weeks_of_cover", "forward_cover")),
    "sell_through": IntentSpec("calc", ("sell_through", "sell_through_from_stock")),
    "top_sellers": IntentSpec("calc", ("top_n",)),
    "worst_sellers": IntentSpec("calc", ("bottom_n",)),
    "broken_sizes": IntentSpec("calc", ("size_availability", "is_broken")),
    "shipment_status": IntentSpec("lookup"),
    "transfer": IntentSpec("planned"),
    "price_discount": IntentSpec("calc", ("discount_rate", "asp", "full_price_share")),
    "margin": IntentSpec(
        "calc",
        (
            "intake_margin",
            "markup",
            "gross_margin",
            "margin_after_discount",
            "breakeven_discount",
            "gmroi",
        ),
    ),
    "budget_otb": IntentSpec("calc", ("open_to_buy", "wssi")),
    "store_ranking": IntentSpec("calc", ("top_n", "bottom_n")),
    "order_eta": IntentSpec("lookup"),
    "returns": IntentSpec("calc", ("return_rate",)),
    "capacity": IntentSpec("calc", ("capacity_fill",)),
}
