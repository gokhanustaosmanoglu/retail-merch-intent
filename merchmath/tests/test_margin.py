import pytest

import merchmath as mm

VAT = 0.10  # example rate only; the library never assumes one


def test_net_of_vat_strips_vat_from_a_vat_inclusive_price():
    assert mm.net_of_vat(1100, vat_rate=VAT) == pytest.approx(1000)


def test_intake_margin_is_measured_on_the_vat_exclusive_price():
    assert mm.intake_margin(1100, 400, vat_rate=VAT) == pytest.approx(0.60)


def test_intake_margin_differs_from_the_vat_inclusive_shortcut():
    naive = (1100 - 400) / 1100
    assert mm.intake_margin(1100, 400, vat_rate=VAT) < naive


def test_vat_rate_must_be_passed_by_keyword():
    with pytest.raises(TypeError):
        mm.intake_margin(1100, 400, VAT)


def test_markup_is_profit_over_cost():
    assert mm.markup(1100, 400, vat_rate=VAT) == pytest.approx(1.5)


def test_gross_margin_is_profit_over_net_sales():
    assert mm.gross_margin(1000, 400) == pytest.approx(0.60)


def test_margin_after_discount_applies_discount_before_removing_vat():
    # 1100 -> 770 after 30% off -> 700 net of VAT -> (700 - 400) / 700
    assert mm.margin_after_discount(1100, 400, 0.30, vat_rate=VAT) == pytest.approx(300 / 700)


def test_margin_after_discount_goes_negative_below_cost():
    assert mm.margin_after_discount(1100, 400, 0.70, vat_rate=VAT) < 0


def test_breakeven_discount_is_where_margin_reaches_zero():
    d = mm.breakeven_discount(1100, 400, vat_rate=VAT)
    assert d == pytest.approx(0.60)
    assert mm.margin_after_discount(1100, 400, d, vat_rate=VAT) == pytest.approx(0.0)


def test_discount_must_be_between_zero_and_one():
    with pytest.raises(ValueError, match="discount"):
        mm.margin_after_discount(1100, 400, 30, vat_rate=VAT)


def test_negative_vat_rate_is_rejected():
    with pytest.raises(ValueError, match="vat_rate"):
        mm.net_of_vat(1100, vat_rate=-0.1)


def test_gmroi_is_margin_value_over_average_stock_at_cost():
    assert mm.gmroi(600_000, 200_000) == pytest.approx(3.0)
