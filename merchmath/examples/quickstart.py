"""Run: python examples/quickstart.py"""

import merchmath as mm

VAT = 0.10  # pass your own rate; the library has no default

print("sell-through      ", round(mm.sell_through(300, 1000), 4))
print("weeks of cover    ", round(mm.weeks_of_cover(1200, 150), 2))
print("forward cover     ", round(mm.forward_cover(1000, [300, 300, 300, 300]), 2))

print("intake margin     ", round(mm.intake_margin(1100, 400, vat_rate=VAT), 4))
print("  VAT-inclusive shortcut would say", round((1100 - 400) / 1100, 4))
print("margin at 30% off ", round(mm.margin_after_discount(1100, 400, 0.30, vat_rate=VAT), 4))
print("breakeven discount", round(mm.breakeven_discount(1100, 400, vat_rate=VAT), 4))

otb = mm.open_to_buy(
    planned_sales=500,
    planned_markdowns=50,
    planned_closing_stock=800,
    opening_stock=700,
    on_order=200,
)
print("open-to-buy       ", otb)

print("\nweek  opening  intake  sales  closing  cover")
for w in mm.wssi(1000, sales=[100, 120, 150, 130], intake=[0, 200, 0, 0]):
    cover = "-" if w.cover is None else f"{w.cover:.2f}"
    print(f"{w.week:>4}  {w.opening:>7}  {w.intake:>6}  {w.sales:>5}  {w.closing:>7}  {cover:>5}")

stock = {"S": 0, "M": 3, "L": 2, "XL": 1}
print("\nsize availability ", mm.size_availability(stock, ["S", "M", "L", "XL"]))
print("broken            ", mm.is_broken(stock, ["S", "M", "L", "XL"]))

spec = mm.INTENTS["margin"]
print("\nintent 'margin' ->", spec.kind, spec.functions)
