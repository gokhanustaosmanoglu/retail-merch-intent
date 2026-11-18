import math

import pytest

import merchmath as mm


def test_weeks_of_cover_is_stock_over_average_weekly_sales():
    assert mm.weeks_of_cover(1200, 150) == pytest.approx(8.0)


def test_weeks_of_cover_rejects_zero_sales_rate():
    with pytest.raises(ValueError, match="average_weekly_sales"):
        mm.weeks_of_cover(1200, 0)


def test_forward_cover_counts_whole_weeks_plus_fraction_of_the_last():
    assert mm.forward_cover(1000, [300, 300, 300, 300]) == pytest.approx(3 + 100 / 300)


def test_forward_cover_walks_through_zero_sales_weeks():
    assert mm.forward_cover(100, [0, 0, 200]) == pytest.approx(2.5)


def test_forward_cover_is_zero_when_there_is_no_stock():
    assert mm.forward_cover(0, [300, 300]) == 0.0


def test_forward_cover_is_infinite_when_stock_outlasts_the_forecast():
    assert mm.forward_cover(1000, [100, 100]) == math.inf


def test_forward_cover_counts_a_week_that_ends_exactly_at_zero_stock():
    assert mm.forward_cover(600, [300, 300, 300]) == pytest.approx(2.0)


def test_forward_cover_rejects_negative_forecast():
    with pytest.raises(ValueError, match="forecast_sales"):
        mm.forward_cover(100, [50, -10])


def test_average_stock_includes_opening_and_every_closing_position():
    assert mm.average_stock(100, [120, 80, 100]) == pytest.approx(100)


def test_stock_turn_is_sales_over_average_stock():
    assert mm.stock_turn(1200, 300) == pytest.approx(4.0)
