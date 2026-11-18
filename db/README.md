---
license: cc-by-4.0
language:
  - en
tags:
  - retail
  - merchandising
  - fashion-retail
  - inventory
  - planning
  - synthetic
  - tabular
pretty_name: "retail-merch-db: Synthetic Fashion Retail Planning Database"
size_categories:
  - 100K<n<1M
configs:
  - config_name: weekly
    default: true
    data_files: data/weekly.csv
  - config_name: dc_stock
    data_files: data/dc_stock.csv
  - config_name: orders
    data_files: data/orders.csv
  - config_name: plan
    data_files: data/plan.csv
  - config_name: products
    data_files: data/products.csv
  - config_name: skus
    data_files: data/skus.csv
  - config_name: stores
    data_files: data/stores.csv
  - config_name: calendar
    data_files: data/calendar.csv
---

# retail-merch-db

**English** · [Türkçe](#türkçe)

A synthetic fashion-retail planning database: two trading years of weekly sales, stock, intake, markdowns, purchase orders and plan, down to store × size. Eight CSV tables, 333,255 weekly fact rows, built from a seed by one standard-library Python file.

## Why

Public retail datasets are sales logs. They rarely carry what a planner works with: stock by size, deliveries, a warehouse, open orders, a plan to compare against. This database has those tables, so the usual merchandising questions (sell-through, cover, broken sizes, open-to-buy, margin after markdown) can be answered from it.

It uses the same vocabulary as [retail-merch-intent](https://huggingface.co/datasets/gokhanustaosmanoglu/retail-merch-intent): `gender`, `product_group`, `channel` and `season` hold that dataset's canonical slot values, so a classified question maps straight onto a filter.

## Tables

| table | rows | grain | columns |
|---|---|---|---|
| `calendar` | 104 | week | `week_id` (2025-W01 … 2026-W52), `week_index`, `year`, `week_no`, `season` |
| `stores` | 23 | store | `store_id` (4-digit code), `name`, `city`, `channel`, `grade`, `capacity_units` |
| `products` | 200 | option | `option_id`, `gender`, `product_group`, `season`, `season_year`, `launch_week_id`, `price_gross`, `cost`, `vat_rate` |
| `skus` | 832 | option × size | `sku_id`, `option_id`, `size` |
| `orders` | 1,496 | purchase-order line | `order_id`, `sku_id`, `units`, `order_week_id`, `eta_week_id`, `received_week_id`, `status` |
| `dc_stock` | 13,637 | week × sku | `opening_stock`, `received_units`, `shipped_units`, `closing_stock` |
| `weekly` | 333,255 | week × store × sku | `opening_stock`, `intake_units`, `sales_units`, `returns_units`, `closing_stock`, `discount_rate`, `sales_gross` |
| `plan` | 3,372 | week × gender × product group | `planned_sales_units`, `planned_sales_gross`, `planned_intake_units` |

20 full-price stores, 1 e-commerce store and 2 outlets. Four seasons on sale (summer 2025 to winter 2026, 40 options each) and one next season (summer 2027) that has orders but no sales yet. Prices include VAT; `sales_gross` is VAT-inclusive.

## What the data looks like

Measured on the default build:

| measure | value |
|---|---|
| sell-through, all options | 75% (by option: 29% to 100%, median 78%) |
| units sold at full price | 60% |
| achieved margin, net of VAT | 54.6% |
| options never marked down / to 30% / to 50% (full-price stores) | 33 / 3 / 124 |
| store-option-weeks with a broken size run | 16% |
| units by channel | stores 83%, e-commerce 11%, outlet 6% |
| actual vs planned units | 91% |
| purchase-order lines | 1,328 received, 58 in transit, 110 open |

## Rules that always hold

Checked by the tests on every build:

- `closing_stock = opening_stock + intake_units − sales_units + returns_units` in every store row, and the next week opens where the last one closed.
- The warehouse ships exactly what stores receive, week by week.
- For every SKU: units received = units left in the warehouse + units left in stores + units sold net of returns.
- Sales never exceed the stock available that week; nothing is ever negative.
- A discount never goes back up; outlets are always at 30% off or deeper.
- Same seed, same rows. SHA-256 of the default build: `a52487c479c0d60c15d43bb09c0aec25648742549a908e1a32af67dd943f4682`.

## How it was made

Each option gets a popularity, a hidden hit factor and a buy quantity planned for an average seller. Stock arrives at the warehouse in two drops (70% before launch, 30% in week 5, sometimes late). Stores pull two weeks of cover each week. Demand follows a life-cycle curve and a size curve, and the buy is flatter across sizes than the demand, so middle sizes sell out first. An option that misses its sell-through target at week 10 or 14 is marked down, and whatever is under 85% at week 18 goes to 50%. Random numbers come from a hash of the seed and the row's key, not from a running generator, so a value never depends on the order rows are produced in.

**Fully synthetic.** No company data, real store codes, product codes or sales figures. City and district names are ordinary place names.

## Use

The CSV files are not stored in the GitHub repository (the weekly table alone is 15 MB). Build them first; it takes about ten seconds and needs nothing beyond Python:

```bash
python merchdb.py --out data
```

```python
import pandas as pd
weekly = pd.read_csv("data/weekly.csv", dtype={"store_id": str})
```

`examples/answer.py` answers six questions with [merchmath](https://github.com/gokhanustaosmanoglu/retail-merch-intent/tree/main/merchmath) (`pip install ../merchmath`), each from an intent and its slots:

```
"erkek jean bu sezon sell-through kaç?"
  intent=sell_through  slots={gender: MEN, product_group: JEANS, period: THIS_SEASON}
  -> 94.8%

"Kadıköy'de kırık bedenli ürünler hangileri?"
  intent=broken_sizes  slots={store: Kadıköy}
  -> 14 of 40 options in stock, e.g. S26-001, S26-005, S26-014, S26-016

"kadın bu hafta plana göre nasıl?"
  intent=growth  slots={gender: WOMEN, comparison: PLAN, period: THIS_WEEK}
  -> 1146 units vs plan 1658: -30.9%
```

Rebuild and test:

```bash
python merchdb.py --out data
python -m pytest -q
```

## Limits (v0.1)

- Trading starts in 2025-W09; the first eight weeks of the calendar have no sales.
- Stores only pull stock, so slow sellers leave 17% of the buy in the warehouse. A real retailer would push it out or transfer it.
- No store-to-store transfers, no promotions outside the markdown steps, no price changes other than markdowns.
- One VAT rate (10%) and one currency. The rate is a parameter of this synthetic world, not tax guidance.
- Stock left at the end of an option's 26-week life stays in its last row; it is not carried into later weeks.
- The plan is the expected demand of an average option, so it has no budget rounds or re-forecasts.
- The demand model is deliberately simple (Poisson around a life-cycle curve). Do not use it to benchmark forecasting methods.

## Licence

Data: CC-BY-4.0. Code: MIT.

---

## Türkçe

Sentetik bir moda perakendesi planlama veritabanı: iki yıllık haftalık satış, stok, sevkiyat, indirim, sipariş ve plan verisi; mağaza × beden kırılımında. Sekiz CSV tablosu, 333.255 haftalık satır; tek bir standart kütüphane Python dosyası bir seed'den üretir.

- Açık perakende veri setleri çoğunlukla satış kaydıdır. Burada planlamacının çalıştığı tablolar var: beden bazında stok, depo, açık siparişler ve plan.
- `gender`, `product_group`, `channel` ve `season` kolonları [retail-merch-intent](https://huggingface.co/datasets/gokhanustaosmanoglu/retail-merch-intent) veri setinin kanonik slot değerlerini kullanır; sınıflandırılmış bir soru doğrudan filtreye dönüşür.
- Stok kimliği, depo-mağaza dengesi ve SKU bazında adet korunumu her üretimde testlerle doğrulanır.
- Tamamen sentetik: hiçbir şirkete ait veri, mağaza kodu, ürün kodu ya da rakam içermez.
- Sınırlar yukarıdaki listede; en önemlisi mağazalar arası transfer olmaması ve yavaş satanların stokunun depoda kalması.
