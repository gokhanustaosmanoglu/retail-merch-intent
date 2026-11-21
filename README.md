---
license: cc-by-4.0
language:
  - tr
  - en
multilinguality:
  - multilingual
task_categories:
  - text-classification
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
pretty_name: "retail-merch-intent: Retail Merchandising Intent & Slot Dataset (Turkish + English)"
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

# retail-merch-intent

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

## Contents (v0.3)

| config | train | test | test templates | note |
|---|---|---|---|---|
| `tr` (default) | 2,100 | 510 | 51 | Turkish |
| `en` | 2,078 | 532 | 49 | English |

Test splits are **template-held-out** for every intent, `out_of_scope` included: test templates never appear in training, so scores measure generalisation, not memorisation. Read the test size honestly: ~500 rows come from ~50 templates (2–3 per intent), so a single split can move by a few points. Every row carries a `template_id`; use it as the group key for grouped cross-validation over train + test if you need a variance estimate. The two languages share intents, slots and canonical slot values; templates were written independently per language (schema-parallel, not sentence-parallel).

Each record: `id`, `text`, `intent`, `slots` (dict, may be empty), `lang`, `template_id`.

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
| `period` | TODAY, THIS_WEEK, LAST_WEEK, LAST_4_WEEKS, THIS_MONTH, MONTH:01–12, WEEK:01–52, THIS_SEASON, SEASON:WINTER/SUMMER, SEASON_TO_DATE, YTD … |
| `store` | free text (city / district or 4-digit code); list if more than one |
| `channel` | STORES, ECOMMERCE, OUTLET, WHOLESALE, CONCESSION, MARKETPLACE, FULL_PRICE_STORES, ALL |
| `measure` | REVENUE (net sales value, excluding VAT), UNITS, MARGIN |
| `comparison` | LY, PLAN, BUDGET, LAST_WEEK |
| `n` | integer (top-N) |
| `season` | WINTER, SUMMER, SPRING, AUTUMN, NEW, OLD |

### Labelling policy

A slot is labelled when the text names it explicitly, whether the word came from a placeholder or is written in the template ("ne kadar **ciro** yaptı" → `measure: REVENUE`, "**online** return rate" → `channel: ECOMMERCE`). A sales question with no measure word means **units**: "kaç sattı", "ne kadar sattı" and "how many chinos did we sell" are all `measure: UNITS`; revenue is always asked for by name ("ciro"). Inside the `margin` intent no `measure` is written: the intent already says it. Known gap: that intent mixes different figures (gross margin %, gross profit, markup, GMROI) with no slot to tell them apart; a `metric` slot is planned for v0.4. The same principle applies to `budget_otb`: "bütçeye göre", "plan vs actual" do not add a `comparison`, because the intent already is the budget / plan question. Two more known gaps, also left for v0.4: stock location ("depo stoğu" vs "mağaza stoğu", warehouse / DC) has no slot, and LFL / like-for-like is a store-set filter with no slot. The rules live in `IMPLIED` in `uret.py`.

## Baseline

> The numbers below were measured on the **v0.2** data and have not been re-run on v0.3 yet (`python baseline.py`).

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

Limitations (v0.3): template-based, so natural variety is limited; single-intent questions only (no "sales and cover" combos); slots are canonical values, not character spans; English and Turkish are not sentence-aligned; `out_of_scope` is small (26 templates, 11 test rows per language), so out-of-scope detection is under-measured.

Regenerate and test:

```bash
pip install -r requirements.txt
python uret.py
python -m pytest -q
```

## Usage

```python
from datasets import load_dataset
tr = load_dataset("gokhanustaosmanoglu/retail-merch-intent", "tr")
en = load_dataset("gokhanustaosmanoglu/retail-merch-intent", "en")
print(en["train"][0])
```

Source and generator: https://github.com/gokhanustaosmanoglu/retail-merch-intent

## Changelog

- **v0.3** (2026-11): data-quality release, all rows regenerated (ids changed). `out_of_scope` is now template-held-out like every other intent (in v0.2 its test sentences also appeared in train); new `template_id` field; Turkish-aware casing (no more `i̇zmir` with a combining dot, store values like `ÜMRANİYE` instead of `ÜMRANIYE`); no repeated words ("top top 20") or contradictions ("worst top 20"); week numbers cover 01–52 instead of five fixed weeks; explicit measure / channel words in templates are labelled, and sales questions with no measure word are labelled `UNITS` (see Labelling policy); `REVENUE` defined as net of VAT; " today" no longer appended as decoration; generator no longer aborts on non-UTF-8 consoles; tests added. `token-classification` removed from the card until span annotations exist.
- **v0.2** (2026-11): renamed from `merch-tr-intent` to `retail-merch-intent` (old URLs redirect); English config added; intents, slot names and canonical values switched to English for both languages (breaking change from v0.1); `lang` field; cross-lingual baseline.
- **v0.1** (2026-11): Turkish only, Turkish labels.

## License and citation

CC-BY-4.0. See `CITATION.cff`.

---

## Türkçe

Perakende **merchandising / planlama** sorularını yapılandırılmış sorguya çeviren asistanlar için intent sınıflandırma ve slot çıkarma veri seti; **Türkçe ve İngilizce**, tek ortak şema.

Amaç: "chino bu hafta kaç sattı, cover kaç?" gibi günlük soruları bir dil modeline SQL yazdırmadan, önceden onaylı sorgu şablonlarına yönlendirmek. Model yalnız **soru tipi** ve **parametreler** kararını verir; rakamı veri kaynağı hesaplar. Yanlış rakam riski sıfırlanır.

- `tr` (varsayılan) ve `en` olmak üzere iki yapılandırma; her birinde ~2.100 eğitim, ~500 test kaydı.
- Test bölmesi **şablon düzeyinde ayrık** (`out_of_scope` dahil): test şablonları eğitimde hiç görülmez. ~500 test satırı ~50 şablondan gelir; varyans ölçmek için `template_id` alanıyla gruplu çapraz doğrulama yapılabilir.
- Intent, slot adları ve kanonik değerler iki dilde de İngilizcedir (v0.2'de değişti); bu sayede Türkçe ve İngilizce aynı sorgu şablonlarına bağlanır.
- Tamamen sentetik; hiçbir şirkete ait veri, mağaza, ürün kodu ya da rakam içermez.
- Taban çizgisi yukarıdaki tabloda (v0.2 verisiyle ölçüldü, v0.3 için henüz yeniden koşulmadı); Türkçe-Türkçe %72,6, İngilizceden Türkçeye aktarım %63,4.
