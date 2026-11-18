import pytest

import merchmath as mm


def test_open_to_buy_is_planned_need_minus_stock_and_commitments():
    otb = mm.open_to_buy(
        planned_sales=500,
        planned_markdowns=50,
        planned_closing_stock=800,
        opening_stock=700,
        on_order=200,
    )
    assert otb == pytest.approx(450)


def test_open_to_buy_is_negative_when_overbought():
    otb = mm.open_to_buy(
        planned_sales=500,
        planned_markdowns=0,
        planned_closing_stock=800,
        opening_stock=1200,
        on_order=300,
    )
    assert otb == pytest.approx(-200)


def test_wssi_rolls_stock_forward_week_by_week():
    weeks = mm.wssi(1000, sales=[100, 120, 150, 130], intake=[0, 200, 0, 0])
    assert [w.opening for w in weeks] == [1000, 900, 980, 830]
    assert [w.closing for w in weeks] == [900, 980, 830, 700]


def test_wssi_numbers_weeks_from_one():
    weeks = mm.wssi(1000, sales=[100, 120], intake=[0, 0])
    assert [w.week for w in weeks] == [1, 2]


def test_wssi_cover_is_closing_stock_over_average_of_following_weeks_sales():
    weeks = mm.wssi(1000, sales=[100, 120, 150, 130], intake=[0, 200, 0, 0])
    assert weeks[0].cover == pytest.approx(900 / ((120 + 150 + 130) / 3))
    assert weeks[1].cover == pytest.approx(980 / 140)
    assert weeks[2].cover == pytest.approx(830 / 130)


def test_wssi_cover_looks_ahead_only_cover_weeks():
    weeks = mm.wssi(1000, sales=[100, 100, 200, 900], intake=[0, 0, 0, 0], cover_weeks=2)
    assert weeks[0].cover == pytest.approx(900 / 150)


def test_wssi_last_week_has_no_cover_because_nothing_follows():
    weeks = mm.wssi(1000, sales=[100, 120], intake=[0, 0])
    assert weeks[-1].cover is None


def test_wssi_keeps_negative_closing_stock_as_a_shortage_signal():
    weeks = mm.wssi(100, sales=[150], intake=[0])
    assert weeks[0].closing == -50


def test_wssi_rejects_sales_and_intake_of_different_lengths():
    with pytest.raises(ValueError, match="same length"):
        mm.wssi(1000, sales=[100, 120], intake=[0])
