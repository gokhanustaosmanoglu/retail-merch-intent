import pytest

import merchmath as mm


def test_sell_through_is_units_sold_over_units_received():
    assert mm.sell_through(300, 1000) == pytest.approx(0.30)


def test_sell_through_from_stock_uses_sold_plus_closing_stock_as_base():
    assert mm.sell_through_from_stock(300, 700) == pytest.approx(0.30)


def test_sell_through_rejects_zero_received():
    with pytest.raises(ValueError, match="units_received"):
        mm.sell_through(10, 0)


def test_growth_is_change_versus_base():
    assert mm.growth(1150, 1000) == pytest.approx(0.15)


def test_growth_is_negative_when_actual_is_below_base():
    assert mm.growth(900, 1000) == pytest.approx(-0.10)


def test_return_rate_is_returned_units_over_sold_units():
    assert mm.return_rate(30, 600) == pytest.approx(0.05)


def test_asp_is_revenue_per_unit():
    assert mm.asp(55_000, 100) == pytest.approx(550)


def test_discount_rate_is_share_taken_off_the_original_price():
    assert mm.discount_rate(1000, 700) == pytest.approx(0.30)


def test_full_price_share_is_full_price_sales_over_total_sales():
    assert mm.full_price_share(600, 1000) == pytest.approx(0.60)


def test_capacity_fill_is_stock_over_capacity():
    assert mm.capacity_fill(4500, 5000) == pytest.approx(0.90)


def test_top_n_returns_highest_values_first():
    assert mm.top_n({"A": 5, "B": 9, "C": 1}, 2) == [("B", 9), ("A", 5)]


def test_bottom_n_returns_lowest_values_first():
    assert mm.bottom_n({"A": 5, "B": 9, "C": 1}, 2) == [("C", 1), ("A", 5)]


def test_top_n_breaks_ties_by_key_so_output_is_deterministic():
    assert mm.top_n({"Z": 7, "A": 7, "M": 7}, 2) == [("A", 7), ("M", 7)]


def test_top_n_rejects_non_positive_n():
    with pytest.raises(ValueError, match="n"):
        mm.top_n({"A": 1}, 0)
