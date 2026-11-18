"""VAT-aware margin measures.

Shelf prices include VAT; margin is earned on the price net of VAT. Every
function that takes a shelf price therefore requires ``vat_rate`` by keyword,
with no default, so the VAT basis is always stated at the call site.
"""

from __future__ import annotations

from ._check import non_negative, ratio, share


def net_of_vat(gross_price: float, *, vat_rate: float) -> float:
    """Price excluding VAT: gross / (1 + vat_rate)."""
    non_negative(vat_rate, "vat_rate")
    return gross_price / (1 + vat_rate)


def intake_margin(gross_price: float, cost: float, *, vat_rate: float) -> float:
    """Intake margin at full price: (net price - cost) / net price."""
    net = net_of_vat(gross_price, vat_rate=vat_rate)
    return ratio(net - cost, net, "gross_price")


def markup(gross_price: float, cost: float, *, vat_rate: float) -> float:
    """Profit as a multiple of cost: (net price - cost) / cost."""
    net = net_of_vat(gross_price, vat_rate=vat_rate)
    return ratio(net - cost, cost, "cost")


def gross_margin(net_sales: float, cost_of_sales: float) -> float:
    """Achieved margin: (net sales - cost of sales) / net sales."""
    return ratio(net_sales - cost_of_sales, net_sales, "net_sales")


def margin_after_discount(
    gross_price: float, cost: float, discount: float, *, vat_rate: float
) -> float:
    """Margin once a discount is taken off the shelf price.

    The discount applies to the VAT-inclusive price; VAT is removed afterwards.
    Negative when the discounted net price falls below cost.
    """
    share(discount, "discount")
    return intake_margin(gross_price * (1 - discount), cost, vat_rate=vat_rate)


def breakeven_discount(gross_price: float, cost: float, *, vat_rate: float) -> float:
    """Deepest discount before margin turns negative: 1 - cost * (1 + vat) / gross."""
    non_negative(vat_rate, "vat_rate")
    return 1 - ratio(cost * (1 + vat_rate), gross_price, "gross_price")


def gmroi(gross_margin_value: float, average_stock_at_cost: float) -> float:
    """Gross margin earned per unit of currency held in stock at cost."""
    return ratio(gross_margin_value, average_stock_at_cost, "average_stock_at_cost")
