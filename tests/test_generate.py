# -*- coding: utf-8 -*-
"""Regression tests for the generator (uret.py). Run: python -m pytest -q"""
import random
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import uret  # noqa: E402

SEEDS = {"tr": 20261115, "en": 20261116}


@pytest.fixture(scope="module", params=["tr", "en"])
def data(request):
    lang = request.param
    train, test, _ = uret.generate(lang, SEEDS[lang])
    return lang, train, test


def words(text):
    return re.findall(r"\w+", text.lower())


# ---------- Turkish-aware casing ----------

def test_turkish_lower_has_no_combining_dot():
    assert uret.lower("İzmir AVM", "tr") == "izmir avm"


def test_turkish_lower_maps_dotless_i():
    assert uret.lower("Isparta", "tr") == "ısparta"


def test_turkish_lower_keeps_english_acronyms_ascii():
    assert uret.lower("GMROI kaç", "tr") == "gmroi kaç"


def test_turkish_upper_dots_the_i():
    assert uret.upper("Ümraniye", "tr") == "ÜMRANİYE"
    assert uret.upper("İzmir", "tr") == "İZMİR"


def test_english_casing_is_plain_ascii():
    assert uret.upper("Izmir", "en") == "IZMIR"
    assert uret.lower("Izmir", "en") == "izmir"


def test_no_combining_dot_in_generated_text(data):
    _, train, test = data
    assert [r["text"] for r in train + test if "̇" in r["text"]] == []


def test_turkish_sentence_initial_i_is_dotted(data):
    lang, train, test = data
    if lang != "tr":
        pytest.skip("Turkish only")
    bad = [r["text"] for r in train + test if re.match(r"I[a-zçğıöşü]", r["text"])]
    assert bad == []


def test_turkish_store_values_are_turkish_uppercase(data):
    lang, train, test = data
    if lang != "tr":
        pytest.skip("Turkish only")
    stores = set()
    for r in train + test:
        s = r["slots"].get("store", [])
        stores.update(s if isinstance(s, list) else [s])
    assert stores, "no store slots generated"
    bad = [s for s in stores if re.match(r"(İZMIR|ÜMRANIYE|NIŞANTAŞI|ESKIŞEHIR|DENIZLI)", s)]
    assert bad == []


# ---------- surface quality ----------

def test_no_repeated_word_or_bigram(data):
    _, train, test = data
    bad = []
    for r in train + test:
        w = words(r["text"])
        if any(w[i] == w[i + 1] for i in range(len(w) - 1)) or any(w[i:i + 2] == w[i + 2:i + 4] for i in range(len(w) - 3)):
            bad.append(r["text"])
    assert bad == []


def test_store_suffix_not_doubled_by_template(data):
    _, train, test = data
    assert [r["text"] for r in train + test if re.search(r"mağazası mağaza", r["text"].lower())] == []


def test_worst_sellers_never_say_top_or_best(data):
    _, train, test = data
    bad = [r["text"] for r in train + test
           if r["intent"] == "worst_sellers" and re.search(r"\b(top|best|en iyi|ilk)\b", r["text"].lower())]
    assert bad == []


def test_transfer_between_two_different_stores(data):
    _, train, test = data
    bad = [r["text"] for r in train + test
           if isinstance(r["slots"].get("store"), list) and len(set(r["slots"]["store"])) < len(r["slots"]["store"])]
    assert bad == []


# ---------- split integrity ----------

def test_every_row_has_template_id(data):
    lang, train, test = data
    assert all(r.get("template_id", "").startswith(f"{lang}-{r['intent']}-") for r in train + test)


def test_no_template_shared_between_train_and_test(data):
    _, train, test = data
    shared = {r["template_id"] for r in train} & {r["template_id"] for r in test}
    assert shared == set()


def test_out_of_scope_is_template_held_out_too(data):
    _, train, test = data
    oos_train = {r["template_id"] for r in train if r["intent"] == "out_of_scope"}
    oos_test = {r["template_id"] for r in test if r["intent"] == "out_of_scope"}
    assert oos_test, "test split has no out_of_scope rows"
    assert oos_train & oos_test == set()


def test_generation_is_deterministic(data):
    lang, train, test = data
    train2, test2, _ = uret.generate(lang, SEEDS[lang])
    assert (train, test) == (train2, test2)


def test_main_writes_all_files_on_a_non_utf8_console(tmp_path):
    """Windows consoles default to cp1252; printing Turkish samples must not abort the run half-way."""
    import os
    import subprocess
    root = Path(uret.__file__).resolve().parent
    code = "import pathlib, sys, uret; uret.OUT = pathlib.Path(sys.argv[1]); uret.main()"
    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    p = subprocess.run([sys.executable, "-c", code, str(tmp_path)], cwd=root, env=env, capture_output=True)
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")[-400:]
    written = sorted(f.relative_to(tmp_path).as_posix() for f in tmp_path.rglob("*.json*"))
    assert written == ["en/test.jsonl", "en/train.jsonl", "schema.json", "tr/test.jsonl", "tr/train.jsonl"]


# ---------- slot labels ----------

def test_week_numbers_cover_the_year_not_five_fixed_weeks(data):
    _, train, test = data
    weeks = {r["slots"]["period"] for r in train + test if re.fullmatch(r"WEEK:\d+", str(r["slots"].get("period", "")))}
    assert len(weeks) > 20
    assert all(re.fullmatch(r"WEEK:(0[1-9]|[1-4]\d|5[0-2])", w) for w in weeks)


def test_week_surface_matches_week_label(data):
    _, train, test = data
    for r in train + test:
        m = re.fullmatch(r"WEEK:(\d\d)", str(r["slots"].get("period", "")))
        if m:
            assert re.search(rf"(?<!\d){int(m.group(1))}(?!\d)", r["text"]), r


def test_decoration_never_adds_an_unlabelled_period(data):
    """Prefixes / suffixes are noise only: 'today' or 'bugün' may appear only when period is TODAY."""
    _, train, test = data
    bad = [r["text"] for r in train + test
           if re.search(r"\b(today|bugün)\b", r["text"].lower()) and r["intent"] != "out_of_scope" and r["slots"].get("period") != "TODAY"]
    assert bad == []


@pytest.mark.parametrize("lang,template,slot,value", [
    ("tr", "{u} {d} ne kadar ciro yaptı", "measure", "REVENUE"),
    ("tr", "{m} mağazasında {u} {d} kaç adet satıldı", "measure", "UNITS"),
    ("tr", "{d} e-ticaret iade oranı {u}", "channel", "ECOMMERCE"),
    ("en", "{m} revenue {d}", "measure", "REVENUE"),
    ("en", "{d} {u} units sold", "measure", "UNITS"),
    ("en", "{d} online return rate for {u}", "channel", "ECOMMERCE"),
])
def test_explicit_literal_in_template_is_labelled(lang, template, slot, value):
    random.seed(1)
    _, slots = uret.fill(template, lang)
    assert slots.get(slot) == value


def test_placeholder_value_wins_over_literal_rule():
    random.seed(1)
    seen = {uret.fill("{c} {d} {o} ciro", "tr")[1]["measure"] for _ in range(40)}
    assert "UNITS" in seen, "literal 'ciro' overwrote the measure chosen by the {o} placeholder"
