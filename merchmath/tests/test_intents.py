import merchmath as mm

# Intent names of the retail-merch-intent dataset (v0.3), minus out_of_scope.
DATASET_INTENTS = {
    "sales", "growth", "stock", "cover", "sell_through", "top_sellers",
    "worst_sellers", "broken_sizes", "shipment_status", "transfer",
    "price_discount", "margin", "budget_otb", "store_ranking", "order_eta",
    "returns", "capacity",
}


def test_every_dataset_intent_has_an_entry():
    assert set(mm.INTENTS) == DATASET_INTENTS


def test_every_mapped_function_is_a_public_callable():
    for intent, spec in mm.INTENTS.items():
        for name in spec.functions:
            assert callable(getattr(mm, name)), f"{intent} -> {name}"


def test_calc_intents_name_at_least_one_function():
    for intent, spec in mm.INTENTS.items():
        if spec.kind == "calc":
            assert spec.functions, intent


def test_lookup_and_planned_intents_name_no_function():
    for intent, spec in mm.INTENTS.items():
        if spec.kind in ("lookup", "planned"):
            assert spec.functions == (), intent


def test_kinds_are_limited_to_three_values():
    assert {spec.kind for spec in mm.INTENTS.values()} <= {"calc", "lookup", "planned"}


def test_margin_intent_routes_to_the_vat_aware_margin_functions():
    assert "intake_margin" in mm.INTENTS["margin"].functions
    assert "margin_after_discount" in mm.INTENTS["margin"].functions


def test_budget_otb_intent_routes_to_open_to_buy():
    assert "open_to_buy" in mm.INTENTS["budget_otb"].functions
