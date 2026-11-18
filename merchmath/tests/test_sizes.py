import pytest

import merchmath as mm

CORE = ["S", "M", "L", "XL"]


def test_size_availability_is_share_of_core_sizes_in_stock():
    assert mm.size_availability({"S": 0, "M": 3, "L": 2, "XL": 1}, CORE) == pytest.approx(0.75)


def test_size_availability_treats_a_missing_size_as_out_of_stock():
    assert mm.size_availability({"M": 3, "L": 2}, CORE) == pytest.approx(0.50)


def test_size_availability_ignores_sizes_outside_the_core_run():
    assert mm.size_availability({"S": 1, "M": 1, "L": 1, "XL": 1, "XXL": 0}, CORE) == pytest.approx(1.0)


def test_size_availability_rejects_empty_core_run():
    with pytest.raises(ValueError, match="core_sizes"):
        mm.size_availability({"M": 3}, [])


def test_option_is_broken_when_a_core_size_is_missing_but_stock_remains():
    assert mm.is_broken({"S": 0, "M": 3, "L": 2, "XL": 1}, CORE) is True


def test_option_is_not_broken_when_every_core_size_is_in_stock():
    assert mm.is_broken({"S": 1, "M": 3, "L": 2, "XL": 1}, CORE) is False


def test_sold_out_option_is_not_broken():
    assert mm.is_broken({"S": 0, "M": 0, "L": 0, "XL": 0}, CORE) is False
