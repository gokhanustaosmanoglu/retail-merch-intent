import csv
from collections import defaultdict
from dataclasses import replace

import pytest

import merchdb as db

# Canonical slot values of the retail-merch-intent dataset (v0.3).
GENDERS = {"ALL", "BABY", "BOYS", "GIRLS", "KIDS", "MEN", "WOMEN"}
CHANNELS = {"ALL", "CONCESSION", "ECOMMERCE", "FULL_PRICE_STORES", "MARKETPLACE", "OUTLET", "STORES", "WHOLESALE"}
SEASONS = {"AUTUMN", "NEW", "OLD", "SPRING", "SUMMER", "WINTER"}
PRODUCT_GROUPS = {
    "ACCESSORIES", "BAG", "BASIC_TSHIRT", "BEANIE", "BELT", "BLOUSE", "BOOTS", "BOXERS", "CARDIGAN",
    "CHINO", "COAT", "DRESS", "FRAGRANCE", "HAT", "JACKET", "JEANS", "KNITWEAR", "LUGGAGE", "OUTERWEAR",
    "OVERCOAT", "POLO", "PYJAMAS", "SCARF", "SHIRT", "SHOES", "SHORTS", "SKIRT", "SLIPPERS", "SNEAKERS",
    "SOCKS", "SWEATER", "SWEATSHIRT", "SWIMWEAR", "TRACKSUIT", "TRENCH_COAT", "TROUSERS", "TSHIRT",
    "TUNIC", "UNDERWEAR", "VEST", "WALLET",
}
TABLES = {"calendar", "stores", "products", "skus", "orders", "dc_stock", "weekly", "plan"}


def small():
    return db.Config(n_stores=5, n_outlets=1, options_per_season=6)


@pytest.fixture(scope="module")
def t():
    return db.generate(small())


@pytest.fixture(scope="module")
def sku_option(t):
    return {r["sku_id"]: r["option_id"] for r in t["skus"]}


@pytest.fixture(scope="module")
def by_key(t):
    """weekly rows per (store, sku), in week order."""
    out = defaultdict(list)
    for r in t["weekly"]:
        out[(r["store_id"], r["sku_id"])].append(r)
    for rows in out.values():
        rows.sort(key=lambda r: r["week_id"])
    return out


def test_generate_returns_every_table_with_rows(t):
    assert set(t) == TABLES
    assert all(len(rows) > 0 for rows in t.values())


def test_same_seed_gives_identical_tables(t):
    assert db.checksum(t) == db.checksum(db.generate(small()))


def test_different_seed_gives_different_tables(t):
    assert db.checksum(t) != db.checksum(db.generate(replace(small(), seed="another-seed")))


def test_weekly_closing_stock_follows_the_stock_identity(t):
    for r in t["weekly"]:
        assert r["closing_stock"] == r["opening_stock"] + r["intake_units"] - r["sales_units"] + r["returns_units"]


def test_weekly_quantities_are_never_negative(t):
    for r in t["weekly"]:
        for col in ("opening_stock", "intake_units", "sales_units", "returns_units", "closing_stock"):
            assert r[col] >= 0, (col, r)


def test_sales_never_exceed_stock_available_in_the_week(t):
    for r in t["weekly"]:
        assert r["sales_units"] <= r["opening_stock"] + r["intake_units"]


def test_opening_stock_continues_from_previous_closing_stock(t, by_key):
    index = {r["week_id"]: r["week_index"] for r in t["calendar"]}
    for rows in by_key.values():
        assert rows[0]["opening_stock"] == 0
        for prev, cur in zip(rows, rows[1:]):
            if index[cur["week_id"]] == index[prev["week_id"]] + 1:
                assert cur["opening_stock"] == prev["closing_stock"]
            else:  # a gap is only allowed while the shelf was empty
                assert prev["closing_stock"] == 0 and cur["opening_stock"] == 0


def test_dc_closing_stock_follows_the_stock_identity_and_stays_non_negative(t):
    for r in t["dc_stock"]:
        assert r["closing_stock"] == r["opening_stock"] + r["received_units"] - r["shipped_units"]
        assert r["closing_stock"] >= 0


def test_dc_shipments_equal_store_intake_every_week(t):
    shipped = {(r["week_id"], r["sku_id"]): r["shipped_units"] for r in t["dc_stock"]}
    intake = defaultdict(int)
    for r in t["weekly"]:
        intake[(r["week_id"], r["sku_id"])] += r["intake_units"]
    for key, units in intake.items():
        assert shipped.get(key, 0) == units, key
    assert sum(shipped.values()) == sum(intake.values())


def test_units_are_conserved_for_every_sku(t, by_key):
    received = defaultdict(int)
    for o in t["orders"]:
        if o["status"] == "RECEIVED":
            received[o["sku_id"]] += o["units"]
    dc_left = {}
    for r in sorted(t["dc_stock"], key=lambda r: r["week_id"]):
        dc_left[r["sku_id"]] = r["closing_stock"]
    in_stores, net_sold = defaultdict(int), defaultdict(int)
    for (_, sku), rows in by_key.items():
        in_stores[sku] += rows[-1]["closing_stock"]
        net_sold[sku] += sum(r["sales_units"] - r["returns_units"] for r in rows)
    assert received
    for sku, units in received.items():
        assert units == dc_left.get(sku, 0) + in_stores[sku] + net_sold[sku], sku


def test_foreign_keys_resolve(t):
    weeks = {r["week_id"] for r in t["calendar"]}
    stores = {r["store_id"] for r in t["stores"]}
    options = {r["option_id"] for r in t["products"]}
    skus = {r["sku_id"] for r in t["skus"]}
    assert all(r["option_id"] in options for r in t["skus"])
    assert all(r["week_id"] in weeks and r["store_id"] in stores and r["sku_id"] in skus for r in t["weekly"])
    assert all(r["week_id"] in weeks and r["sku_id"] in skus for r in t["dc_stock"])
    assert all(r["sku_id"] in skus and r["order_week_id"] in weeks for r in t["orders"])
    assert all(r["week_id"] in weeks for r in t["plan"])


def test_primary_keys_are_unique(t):
    def unique(rows, *cols):
        keys = [tuple(r[c] for c in cols) for r in rows]
        return len(keys) == len(set(keys))

    assert unique(t["calendar"], "week_id")
    assert unique(t["stores"], "store_id")
    assert unique(t["products"], "option_id")
    assert unique(t["skus"], "sku_id")
    assert unique(t["orders"], "order_id")
    assert unique(t["weekly"], "week_id", "store_id", "sku_id")
    assert unique(t["dc_stock"], "week_id", "sku_id")
    assert unique(t["plan"], "week_id", "gender", "product_group")


def test_slot_columns_use_the_intent_datasets_canonical_values(t):
    assert {r["gender"] for r in t["products"]} <= GENDERS
    assert {r["product_group"] for r in t["products"]} <= PRODUCT_GROUPS
    assert {r["season"] for r in t["products"]} <= SEASONS
    assert {r["season"] for r in t["calendar"]} <= SEASONS
    assert {r["channel"] for r in t["stores"]} <= CHANNELS
    assert {r["gender"] for r in t["plan"]} <= GENDERS
    assert {r["product_group"] for r in t["plan"]} <= PRODUCT_GROUPS


def test_each_product_group_fills_its_genders_in_order_so_adult_ranges_come_first(t):
    """A group with k options in a season uses the first k genders it is sold in (MEN, WOMEN, then kids)."""
    seen = defaultdict(list)
    for p in t["products"]:
        seen[(p["season"], p["season_year"], p["product_group"])].append(p["gender"])
    for (_, _, group), genders in seen.items():
        allowed = db.GROUPS[group][4]
        assert genders == [allowed[k % len(allowed)] for k in range(len(genders))], group


def test_store_ids_are_four_digit_codes(t):
    assert all(len(r["store_id"]) == 4 and r["store_id"].isdigit() for r in t["stores"])


def test_every_channel_type_is_present(t):
    assert {r["channel"] for r in t["stores"]} == {"STORES", "ECOMMERCE", "OUTLET"}


def test_sales_gross_is_units_times_discounted_shelf_price(t, sku_option):
    price = {r["option_id"]: r["price_gross"] for r in t["products"]}
    for r in t["weekly"]:
        expected = r["sales_units"] * price[sku_option[r["sku_id"]]] * (1 - r["discount_rate"])
        assert r["sales_gross"] == pytest.approx(expected, abs=0.006)


def test_discount_is_one_of_the_markdown_steps(t):
    assert {r["discount_rate"] for r in t["weekly"]} <= {0.0, 0.3, 0.5}


def test_discount_never_decreases_during_an_options_life(by_key):
    for rows in by_key.values():
        rates = [r["discount_rate"] for r in rows]
        assert rates == sorted(rates)


def test_outlet_always_sells_at_thirty_percent_off_or_deeper(t):
    outlets = {r["store_id"] for r in t["stores"] if r["channel"] == "OUTLET"}
    rates = [r["discount_rate"] for r in t["weekly"] if r["store_id"] in outlets]
    assert rates and min(rates) >= 0.3


def test_cost_is_below_the_vat_exclusive_price(t):
    for r in t["products"]:
        assert 0 < r["cost"] < r["price_gross"] / (1 + r["vat_rate"])


def test_order_status_matches_what_has_happened_by_the_last_calendar_week(t):
    as_of = max(r["week_id"] for r in t["calendar"])
    assert {o["status"] for o in t["orders"]} == {"RECEIVED", "IN_TRANSIT", "OPEN"}
    for o in t["orders"]:
        assert o["order_week_id"] <= as_of
        if o["status"] == "RECEIVED":
            assert o["received_week_id"] != "" and o["received_week_id"] <= as_of
        else:
            assert o["received_week_id"] == ""


def test_next_season_has_orders_but_no_sales_yet(t, sku_option):
    as_of = max(r["week_id"] for r in t["calendar"])
    future = {r["option_id"] for r in t["products"] if r["launch_week_id"] > as_of}
    assert future
    assert not any(sku_option[r["sku_id"]] in future for r in t["weekly"])
    assert any(sku_option[o["sku_id"]] in future for o in t["orders"])


def test_plan_exists_for_every_week_and_group_that_sold(t, sku_option):
    product = {r["option_id"]: r for r in t["products"]}
    planned = {(r["week_id"], r["gender"], r["product_group"]) for r in t["plan"]}
    for r in t["weekly"]:
        if r["sales_units"]:
            p = product[sku_option[r["sku_id"]]]
            assert (r["week_id"], p["gender"], p["product_group"]) in planned


def test_plan_values_are_never_negative(t):
    for r in t["plan"]:
        assert r["planned_sales_units"] >= 0 and r["planned_sales_gross"] >= 0 and r["planned_intake_units"] >= 0


def test_data_contains_broken_size_runs(t, sku_option):
    """Some store ends a week with a size at zero while another size of the option has stock."""
    stock = defaultdict(list)
    for r in t["weekly"]:
        stock[(r["week_id"], r["store_id"], sku_option[r["sku_id"]])].append(r["closing_stock"])
    assert any(len(v) > 1 and min(v) == 0 and max(v) > 0 for v in stock.values())


def test_data_contains_marked_down_and_never_marked_down_options(t, sku_option):
    full_price = {r["store_id"] for r in t["stores"] if r["channel"] == "STORES"}
    deepest = defaultdict(float)
    for r in t["weekly"]:
        if r["store_id"] in full_price:
            option = sku_option[r["sku_id"]]
            deepest[option] = max(deepest[option], r["discount_rate"])
    assert 0.0 in deepest.values()
    assert max(deepest.values()) >= 0.3


def test_no_week_is_left_without_sales_once_trading_has_started(t):
    sold = defaultdict(int)
    for r in t["weekly"]:
        sold[r["week_id"]] += r["sales_units"]
    first = min(sold)
    trading_weeks = [r["week_id"] for r in t["calendar"] if r["week_id"] >= first]
    assert all(sold[w] > 0 for w in trading_weeks)


def test_store_capacity_covers_a_plausible_share_of_peak_stock(t):
    peak = defaultdict(int)
    weekly_total = defaultdict(int)
    for r in t["weekly"]:
        weekly_total[(r["store_id"], r["week_id"])] += r["closing_stock"]
    for (store, _), units in weekly_total.items():
        peak[store] = max(peak[store], units)
    for s in t["stores"]:
        assert 0.8 * peak[s["store_id"]] <= s["capacity_units"] <= 1.6 * peak[s["store_id"]] + 100


def test_write_csv_writes_one_file_per_table_with_every_row(t, tmp_path):
    db.write_csv(t, tmp_path)
    for name, rows in t.items():
        with open(tmp_path / f"{name}.csv", encoding="utf-8", newline="") as f:
            read = list(csv.DictReader(f))
        assert len(read) == len(rows)
        assert list(read[0]) == list(rows[0])
