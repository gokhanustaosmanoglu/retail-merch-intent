# merchmath

**English** · [Türkçe](#türkçe)

Tested formulas for retail merchandising and planning: sell-through, cover, WSSI, open-to-buy, VAT-aware margin, broken sizes. Pure Python, no dependencies.

```bash
pip install ./merchmath      # from the repository root; not on PyPI yet
```

```python
import merchmath as mm

mm.sell_through(300, 1000)                                  # 0.3
mm.forward_cover(1000, [300, 300, 300, 300])                # 3.33 weeks
mm.intake_margin(1100, 400, vat_rate=0.10)                  # 0.6
mm.margin_after_discount(1100, 400, 0.30, vat_rate=0.10)    # 0.4286
mm.breakeven_discount(1100, 400, vat_rate=0.10)             # 0.6
```

## Why

Planners compute these numbers in spreadsheets every week, and the same mistakes come back: margin taken on the VAT-inclusive price, cover divided by the wrong weeks, sell-through on the wrong base. This package writes each formula once, states its convention in the docstring, and pins it with a worked example in the tests.

It is also the calculation side of [retail-merch-intent](https://huggingface.co/datasets/gokhanustaosmanoglu/retail-merch-intent). That dataset trains a model to recognise the question type; `merchmath.INTENTS` names the function that answers it. The model routes, the function computes, and no model ever produces a number.

## VAT

Shelf prices include VAT, margin is earned net of it. Every function that takes a shelf price requires `vat_rate` as a keyword with no default:

```python
mm.intake_margin(1100, 400, vat_rate=0.10)   # 0.6     (1000 net, 400 cost)
(1100 - 400) / 1100                          # 0.6364  the VAT-inclusive shortcut, wrong
mm.intake_margin(1100, 400, 0.10)            # TypeError: say which rate you mean
```

## Functions

| area | function | definition |
|---|---|---|
| sales | `sell_through(sold, received)` | sold / received |
| | `sell_through_from_stock(sold, closing_stock)` | sold / (sold + closing stock) |
| | `growth(actual, base)` | actual / base − 1 |
| | `return_rate(returned, sold)` | returned / sold |
| price | `asp(revenue, units)` | revenue / units |
| | `discount_rate(original, sold)` | 1 − sold / original |
| | `full_price_share(full_price_sales, total_sales)` | full-price sales / total sales |
| stock | `weeks_of_cover(stock, avg_weekly_sales)` | stock / average weekly sales |
| | `forward_cover(stock, forecast)` | weeks the stock lasts against a weekly forecast |
| | `average_stock(opening, closings)` | (opening + Σ closings) / (n + 1) |
| | `stock_turn(sales, average_stock)` | sales / average stock |
| | `capacity_fill(stock, capacity)` | stock / capacity |
| margin | `net_of_vat(gross, vat_rate=)` | gross / (1 + VAT) |
| | `intake_margin(gross, cost, vat_rate=)` | (net − cost) / net |
| | `markup(gross, cost, vat_rate=)` | (net − cost) / cost |
| | `gross_margin(net_sales, cost_of_sales)` | (net sales − cost) / net sales |
| | `margin_after_discount(gross, cost, discount, vat_rate=)` | intake margin on the discounted price |
| | `breakeven_discount(gross, cost, vat_rate=)` | 1 − cost × (1 + VAT) / gross |
| | `gmroi(margin_value, avg_stock_at_cost)` | margin value / average stock at cost |
| planning | `open_to_buy(...)` | planned sales + markdowns + closing stock − opening stock − on order |
| | `wssi(opening, sales=, intake=)` | weekly roll-forward with cover |
| sizes | `size_availability(stock_by_size, core_sizes)` | share of core sizes in stock |
| | `is_broken(stock_by_size, core_sizes)` | a core size is out while another still has stock |
| ranking | `top_n(values, n)`, `bottom_n(values, n)` | ranked entries, ties ordered by key |

Rates are fractions (`0.30`, not `30`). A zero or negative base raises `ValueError` instead of returning a number.

## WSSI

```python
for w in mm.wssi(1000, sales=[100, 120, 150, 130], intake=[0, 200, 0, 0]):
    print(w.week, w.opening, w.intake, w.sales, w.closing, w.cover)
```

```
week  opening  intake  sales  closing  cover
   1     1000       0    100      900   6.75
   2      900     200    120      980   7.00
   3      980       0    150      830   6.38
   4      830       0    130      700      -
```

Cover is closing stock over the average sales of the next `cover_weeks` weeks (default 4, fewer near the end of the plan). A negative closing stock is kept: it is the shortage the plan has to fix.

## Intents

```python
mm.INTENTS["margin"]
# IntentSpec(kind='calc', functions=('intake_margin', 'markup', 'gross_margin',
#            'margin_after_discount', 'breakeven_discount', 'gmroi'))
```

All 17 in-scope intents of retail-merch-intent v0.3 have an entry: 12 are `calc`, 4 are `lookup` (`sales`, `stock`, `shipment_status`, `order_eta`: plain data reads, nothing to compute) and 1 is `planned` (`transfer`: no formula shipped yet).

## Limits (v0.1)

- Single-currency scalars; no pandas helpers yet.
- `is_broken` uses one rule (any core size out). Retailers differ here; the rule sits in one function in `sizes.py`.
- No transfer or allocation logic, no markdown optimisation.
- Formula conventions follow common fashion-retail practice; where conventions differ (sell-through base, cover look-ahead) the docstring states the one used.

## Develop

```bash
pip install -e ".[dev]"
python -m pytest -q
python examples/quickstart.py
```

MIT licence.

---

## Türkçe

Perakende merchandising ve planlama için test edilmiş formüller: sell-through, cover, WSSI, open-to-buy, KDV'ye duyarlı marj, kırık beden. Saf Python, bağımlılık yok.

- Her formül bir kez yazıldı, hangi tanımı kullandığı docstring'de belirtildi, testlerde işlenmiş bir örnekle sabitlendi.
- Etiket fiyatı alan her fonksiyon `vat_rate` parametresini isimle ve varsayılansız ister. Marjı KDV dahil fiyat üzerinden hesaplama hatası (%63,6 yerine doğrusu %60) böylece çağrı satırında görünür olur.
- Oranlar kesir olarak yazılır (`0.30`). Payda sıfır ya da negatifse rakam dönmez, `ValueError` fırlar.
- `merchmath.INTENTS`, [retail-merch-intent](https://huggingface.co/datasets/gokhanustaosmanoglu/retail-merch-intent) veri setindeki 17 kapsam içi intent'i cevaplayan fonksiyona bağlar: model soru tipini seçer, rakamı fonksiyon hesaplar.
- `is_broken` kuralı tek fonksiyondadır (`sizes.py`); kendi kırık beden tanımınıza göre değiştirin.
