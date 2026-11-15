---
license: cc-by-4.0
language:
  - tr
  - en
multilinguality:
  - multilingual
task_categories:
  - text-classification
  - token-classification
task_ids:
  - intent-classification
tags:
  - retail
  - merchandising
  - fashion-retail
  - inventory
  - intent-classification
  - slot-filling
  - cross-lingual
  - synthetic
pretty_name: "merch-tr-intent: Retail Merchandising Intent & Slot Dataset (Turkish + English)"
size_categories:
  - 1K<n<10K
configs:
  - config_name: tr
    default: true
    data_files:
      - split: train
        path: data/tr/train.jsonl
      - split: test
        path: data/tr/test.jsonl
  - config_name: en
    data_files:
      - split: train
        path: data/en/train.jsonl
      - split: test
        path: data/en/test.jsonl
---

# merch-tr-intent

**English** · [Türkçe](#türkçe)

An intent-classification and slot-filling dataset for **retail merchandising and planning questions**, in **Turkish and English** with one shared schema.

```json
{"text": "how many chinos did menswear sell last week", "intent": "sales",
 "slots": {"gender": "MEN", "product_group": "CHINO", "period": "LAST_WEEK"}, "lang": "en"}
{"text": "erkek chino geçen hafta kaç sattı", "intent": "sales",
 "slots": {"gender": "MEN", "product_group": "CHINO", "period": "LAST_WEEK"}, "lang": "tr"}
```

## Why

Merchandisers, planners and allocators ask the same questions every day: *how much did it sell, how many weeks of cover, which stores have broken sizes, when does the order land*. Text-to-SQL models answer these by writing SQL and can return wrong numbers. This dataset supports a safer design: a model only decides **which question type** and **which parameters**; a pre-approved query template computes the number. Wrong-number risk drops to zero; the model's job is routing.

As far as we found, no public intent dataset covers the retail-merchandising domain. General assistant datasets such as [MASSIVE](https://huggingface.co/datasets/AmazonScience/massive) (51 languages, alarm/music/weather) and retail text-to-SQL benchmarks exist, but nothing for merchandising intents.

## Contents (v0.2)

| config | train | test | note |
|---|---|---|---|
| `tr` (default) | 2,091 | 519 | Turkish |
| `en` | 2,108 | 502 | English |

Test splits are **template-held-out**: test templates never appear in training, so scores measure generalisation, not memorisation. The two languages share intents, slots and canonical slot values; templates were written independently per language (schema-parallel, not sentence-parallel).

Each record: `id`, `text`, `intent`, `slots` (dict, may be empty), `lang`.

### Intents (18)

| intent | question type |
|---|---|
| `sales` | sales revenue / units |
| `growth` | change vs last year / plan / budget |
| `stock` | stock on hand (store, DC) |
| `cover` | weeks of cover |
| `sell_through` | sell-through rate |
| `top_sellers` | best sellers |
| `worst_sellers` | worst sellers, dead stock |
| `broken_sizes` | broken size curves, size replenishment |
| `shipment_status` | dispatch, in-transit, reserved |
| `transfer` | store-to-store transfer suggestions |
| `price_discount` | discount rate, price, ASP, full-price share |
| `margin` | gross margin, markup, GMROI |
| `budget_otb` | open-to-buy, budget achievement, buy plan |
| `store_ranking` | store performance ranking |
| `order_eta` | open orders, ETA, intake |
| `returns` | return rate, return collection |
| `capacity` | store capacity, fill rate, option count |
| `out_of_scope` | small talk / unrelated |

### Slots (9, canonical values in English for both languages)

| slot | values |
|---|---|
| `gender` | MEN, WOMEN, BOYS, GIRLS, KIDS, BABY, ALL |
| `product_group` | COAT, OVERCOAT, OUTERWEAR, KNITWEAR, SWEATER, SHIRT, TSHIRT, POLO, CHINO, JEANS, TROUSERS, SHOES, SOCKS, BAG, UNDERWEAR … (41 values, see `data/schema.json`) |
| `period` | TODAY, THIS_WEEK, LAST_WEEK, LAST_4_WEEKS, THIS_MONTH, MONTH:01–12, WEEK:nn, THIS_SEASON, SEASON:WINTER/SUMMER, SEASON_TO_DATE, YTD … |
| `store` | free text (city / district or 4-digit code); list if more than one |
| `channel` | STORES, ECOMMERCE, OUTLET, WHOLESALE, CONCESSION, MARKETPLACE, FULL_PRICE_STORES, ALL |
| `measure` | REVENUE, UNITS, MARGIN |
| `comparison` | LY, PLAN, BUDGET, LAST_WEEK |
| `n` | integer (top-N) |
| `season` | WINTER, SUMMER, SPRING, AUTUMN, NEW, OLD |

## Baseline

Frozen `intfloat/multilingual-e5-small` embeddings + nearest centroid, intent accuracy on the template-held-out test sets (`baseline.py`):

| train → test | accuracy |
|---|---|
| tr → tr | 0.726 |
| en → en | 0.590 |
| en → tr | 0.634 |
| tr → en | 0.486 |

The hard pairs are deliberate: `broken_sizes` vs `transfer`, `transfer` vs `stock`, `order_eta` vs `shipment_status`, `top_sellers` vs `worst_sellers`. Separating them is the assistant's real job. A trained classifier or a small LLM fine-tune (LoRA) is the expected next step; cross-lingual transfer is an open question this dataset makes measurable.

## How it was made

Fully **synthetic**: hand-written templates per intent and language, filled from a generic retail vocabulary (`uret.py`), with surface variation (greetings, polite suffixes, casing). Store names are city / district names or random 4-digit codes. **No company data, real store identifiers, product codes or sales figures.**

Limitations (v0.2): template-based, so natural variety is limited; single-intent questions only (no "sales and cover" combos); slots are canonical values, not character spans; English and Turkish are not sentence-aligned.

## Usage

```python
from datasets import load_dataset
tr = load_dataset("gokhanustaosmanoglu/merch-tr-intent", "tr")
en = load_dataset("gokhanustaosmanoglu/merch-tr-intent", "en")
print(en["train"][0])
```

Source and generator: https://github.com/gokhanustaosmanoglu/merch-tr-intent

## Changelog

- **v0.2** (2026-11): English config added; intents, slot names and canonical values switched to English for both languages (breaking change from v0.1); `lang` field; cross-lingual baseline.
- **v0.1** (2026-11): Turkish only, Turkish labels.

## License and citation

CC-BY-4.0. See `CITATION.cff`.

---

## Türkçe

Perakende **merchandising / planlama** sorularını yapılandırılmış sorguya çeviren asistanlar için intent sınıflandırma ve slot çıkarma veri seti; **Türkçe ve İngilizce**, tek ortak şema.

Amaç: "chino bu hafta kaç sattı, cover kaç?" gibi günlük soruları bir dil modeline SQL yazdırmadan, önceden onaylı sorgu şablonlarına yönlendirmek. Model yalnız **soru tipi** ve **parametreler** kararını verir; rakamı veri kaynağı hesaplar. Yanlış rakam riski sıfırlanır.

- `tr` (varsayılan) ve `en` olmak üzere iki yapılandırma; her birinde ~2.100 eğitim, ~500 test kaydı.
- Test bölmesi **şablon düzeyinde ayrık**: test şablonları eğitimde hiç görülmez.
- Intent, slot adları ve kanonik değerler iki dilde de İngilizcedir (v0.2'de değişti); bu sayede Türkçe ve İngilizce aynı sorgu şablonlarına bağlanır.
- Tamamen sentetik; hiçbir şirkete ait veri, mağaza, ürün kodu ya da rakam içermez.
- Taban çizgisi yukarıdaki tabloda; Türkçe-Türkçe %72,6, İngilizceden Türkçeye aktarım %63,4.
