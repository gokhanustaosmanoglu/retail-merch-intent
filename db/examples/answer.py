"""Answer merchandising questions from the CSV tables with merchmath.

A classifier trained on retail-merch-intent would produce the (intent, slots)
pairs at the bottom; here they are written by hand. Each intent is answered by
a fixed query plus a merchmath formula, so no model ever computes a number.

    python merchdb.py --out data
    pip install ../merchmath
    python examples/answer.py
"""

import csv
from collections import defaultdict
from pathlib import Path

import merchmath as mm

DATA = Path(__file__).resolve().parent.parent / "data"
AS_OF = "2026-W30"  # "this week" for the questions below


def load(name):
    with open(DATA / f"{name}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


products = {r["option_id"]: r for r in load("products")}
skus = load("skus")
option_of = {r["sku_id"]: r["option_id"] for r in skus}
store_id = {r["name"]: r["store_id"] for r in load("stores")}
weekly = [r for r in load("weekly") if r["week_id"] <= AS_OF]
orders = load("orders")
plan = load("plan")
weeks = sorted({r["week_id"] for r in weekly})


def options(**slots):
    return {o for o, p in products.items() if all(p[k] == str(v) for k, v in slots.items())}


def sell_through(**slots):
    wanted = options(**slots)
    sold = sum(int(r["sales_units"]) - int(r["returns_units"]) for r in weekly if option_of[r["sku_id"]] in wanted)
    received = sum(
        int(o["units"]) for o in orders
        if option_of[o["sku_id"]] in wanted and o["received_week_id"] and o["received_week_id"] <= AS_OF
    )
    return mm.sell_through(sold, received)


def cover(store):
    sid, last4 = store_id[store], weeks[-4:]
    stock = sum(int(r["closing_stock"]) for r in weekly if r["store_id"] == sid and r["week_id"] == AS_OF)
    sales = sum(int(r["sales_units"]) for r in weekly if r["store_id"] == sid and r["week_id"] in last4)
    return mm.weeks_of_cover(stock, sales / len(last4))


def broken_sizes(store):
    sid = store_id[store]
    core = defaultdict(list)
    for s in skus:
        core[s["option_id"]].append(s["size"])
    stock = defaultdict(dict)
    for r in weekly:
        if r["store_id"] == sid and r["week_id"] == AS_OF:
            option, size = option_of[r["sku_id"]], r["sku_id"].split("-", 2)[2]
            stock[option][size] = int(r["closing_stock"])
    return sorted(o for o, by_size in stock.items() if mm.is_broken(by_size, core[o])), len(stock)


def margin(**slots):
    wanted = options(**slots)
    rows = [r for r in weekly if option_of[r["sku_id"]] in wanted]
    vat = float(next(iter(products.values()))["vat_rate"])
    net_sales = sum(mm.net_of_vat(float(r["sales_gross"]), vat_rate=vat) for r in rows)
    cost_of_sales = sum(int(r["sales_units"]) * float(products[option_of[r["sku_id"]]]["cost"]) for r in rows)
    return mm.gross_margin(net_sales, cost_of_sales)


def top_sellers(n):
    units = defaultdict(int)
    for r in weekly:
        if r["week_id"] == AS_OF:
            units[option_of[r["sku_id"]]] += int(r["sales_units"])
    return mm.top_n(units, n)


def growth_vs_plan(gender):
    actual = sum(
        int(r["sales_units"]) for r in weekly
        if r["week_id"] == AS_OF and products[option_of[r["sku_id"]]]["gender"] == gender
    )
    planned = sum(int(r["planned_sales_units"]) for r in plan if r["week_id"] == AS_OF and r["gender"] == gender)
    return actual, planned, mm.growth(actual, planned)


if __name__ == "__main__":
    print(f"as of {AS_OF}\n")

    print('"erkek jean bu sezon sell-through kaç?"')
    print("  intent=sell_through  slots={gender: MEN, product_group: JEANS, period: THIS_SEASON}")
    st = sell_through(gender="MEN", product_group="JEANS", season="SUMMER", season_year=2026)
    print(f"  -> {st:.1%}\n")

    print('"Kadıköy kaç hafta cover\'da?"')
    print("  intent=cover  slots={store: Kadıköy}")
    print(f"  -> {cover('Kadıköy'):.1f} weeks\n")

    print('"Kadıköy\'de kırık bedenli ürünler hangileri?"')
    print("  intent=broken_sizes  slots={store: Kadıköy}")
    broken, ranged = broken_sizes("Kadıköy")
    print(f"  -> {len(broken)} of {ranged} options in stock, e.g. {', '.join(broken[:4])}\n")

    print('"geçen kış montların marjı neydi?"')
    print("  intent=margin  slots={product_group: COAT, period: SEASON:WINTER}")
    print(f"  -> {margin(product_group='COAT', season='WINTER', season_year=2025):.1%}\n")

    print('"bu hafta en çok satan 3 ürün?"')
    print("  intent=top_sellers  slots={n: 3, period: THIS_WEEK}")
    print("  -> " + ", ".join(f"{o} ({u} units, {products[o]['product_group']})" for o, u in top_sellers(3)) + "\n")

    print('"kadın bu hafta plana göre nasıl?"')
    print("  intent=growth  slots={gender: WOMEN, comparison: PLAN, period: THIS_WEEK}")
    actual, planned, g = growth_vs_plan("WOMEN")
    print(f"  -> {actual} units vs plan {planned}: {g:+.1%}")
