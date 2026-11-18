"""Synthetic fashion-retail planning database generator.

Builds eight related tables (calendar, stores, products, skus, orders,
dc_stock, weekly, plan) from a seed. Pure standard library.

Randomness comes from a hash of (seed, key), never from a stateful generator,
so a value does not depend on the order in which rows are produced.

    python merchdb.py --out data
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist

FIRST_YEAR = 2025
WEEKS_PER_YEAR = 52
N_WEEKS = 104  # two trading years
AS_OF = N_WEEKS - 1  # index of the last calendar week; order status is as of this week
VAT_RATE = 0.10  # a parameter of this synthetic world, not tax advice
BASE_RATE = 5.0  # units an average option sells per week in a grade-B store at peak
ELASTICITY = 2.0  # demand uplift per unit of discount: 30% off -> x1.6
MARKDOWN_CHECKS = {10: 0.40, 14: 0.60}  # life week -> sell-through needed to stay at the current price
CLEARANCE_WEEK, CLEARANCE_SELL_THROUGH = 18, 0.85
NO_REPLENISHMENT_LAST_WEEKS = 4
SHIPPING_WEEKS = 3

# (season, year, index of the season's first selling week)
SEASONS = [
    ("SUMMER", 2025, 8),
    ("WINTER", 2025, 34),
    ("SUMMER", 2026, 60),
    ("WINTER", 2026, 86),
    ("SUMMER", 2027, 112),  # next season: ordered, not yet on sale
]

ALL4 = ("MEN", "WOMEN", "BOYS", "GIRLS")
# product_group: (seasons it sells in, size type, shelf price, popularity, genders)
GROUPS = {
    "TSHIRT": ("S", "alpha", 499, 1.4, ALL4),
    "BASIC_TSHIRT": ("SW", "alpha", 299, 1.6, ALL4),
    "POLO": ("S", "alpha", 799, 1.0, ("MEN", "BOYS")),
    "SHIRT": ("SW", "alpha", 999, 1.0, ALL4),
    "SHORTS": ("S", "alpha", 699, 0.9, ALL4),
    "SWIMWEAR": ("S", "alpha", 599, 0.6, ALL4),
    "DRESS": ("S", "alpha", 1299, 1.1, ("WOMEN", "GIRLS")),
    "BLOUSE": ("SW", "alpha", 899, 0.9, ("WOMEN",)),
    "SKIRT": ("S", "alpha", 899, 0.7, ("WOMEN", "GIRLS")),
    "CHINO": ("SW", "alpha", 1199, 0.9, ("MEN", "BOYS")),
    "JEANS": ("SW", "alpha", 1299, 1.2, ALL4),
    "TROUSERS": ("SW", "alpha", 1099, 0.9, ALL4),
    "SWEATSHIRT": ("W", "alpha", 999, 1.2, ALL4),
    "SWEATER": ("W", "alpha", 1199, 1.0, ALL4),
    "KNITWEAR": ("W", "alpha", 1399, 0.9, ("MEN", "WOMEN")),
    "CARDIGAN": ("W", "alpha", 1299, 0.7, ("MEN", "WOMEN", "GIRLS")),
    "JACKET": ("W", "alpha", 2499, 0.7, ALL4),
    "COAT": ("W", "alpha", 3999, 0.6, ALL4),
    "OVERCOAT": ("W", "alpha", 4499, 0.4, ("MEN", "WOMEN")),
    "TRACKSUIT": ("W", "alpha", 1499, 0.7, ALL4),
    "SNEAKERS": ("SW", "shoe", 1999, 0.8, ALL4),
    "BOOTS": ("W", "shoe", 2799, 0.5, ALL4),
    "SOCKS": ("SW", "one", 99, 1.8, ALL4),
    "BAG": ("SW", "one", 1499, 0.4, ("WOMEN",)),
    "BELT": ("SW", "one", 399, 0.4, ("MEN",)),
    "SCARF": ("W", "one", 399, 0.5, ("MEN", "WOMEN")),
    "BEANIE": ("W", "one", 249, 0.6, ALL4),
}

SIZE_RUNS = {
    ("alpha", "MEN"): ["S", "M", "L", "XL", "XXL"],
    ("alpha", "WOMEN"): ["XS", "S", "M", "L", "XL"],
    ("alpha", "KIDS"): ["4-5", "6-7", "8-9", "10-11", "12-13"],
    ("shoe", "MEN"): ["40", "41", "42", "43", "44"],
    ("shoe", "WOMEN"): ["36", "37", "38", "39", "40"],
    ("shoe", "KIDS"): ["28", "30", "32", "34", "36"],
}
DEMAND_CURVE = [0.12, 0.28, 0.30, 0.20, 0.10]  # what customers ask for
BUY_CURVE = [0.15, 0.25, 0.28, 0.20, 0.12]  # what gets bought: flatter, so middle sizes break first

PLACES = [
    ("İstanbul", "Kadıköy"), ("İstanbul", "Ümraniye"), ("İstanbul", "Bakırköy"), ("Ankara", "Çankaya"),
    ("İzmir", "Karşıyaka"), ("Bursa", "Nilüfer"), ("Antalya", "Muratpaşa"), ("Adana", "Seyhan"),
    ("Konya", "Selçuklu"), ("Gaziantep", "Şahinbey"), ("Kayseri", "Melikgazi"), ("Mersin", "Yenişehir"),
    ("Eskişehir", "Tepebaşı"), ("Samsun", "İlkadım"), ("Trabzon", "Ortahisar"), ("Denizli", "Pamukkale"),
    ("Diyarbakır", "Kayapınar"), ("Kocaeli", "İzmit"), ("Sakarya", "Adapazarı"), ("Muğla", "Bodrum"),
]
OUTLET_PLACES = [("İstanbul", "Esenyurt"), ("Ankara", "Etimesgut"), ("İzmir", "Torbalı")]
CHANNEL_FACTOR = {"ECOMMERCE": 3.0, "OUTLET": 0.6}
GRADE_FACTOR = {"A": 1.3, "B": 1.0, "C": 0.7}
RETURN_RATE = {"STORES": 0.04, "OUTLET": 0.03, "ECOMMERCE": 0.18}


@dataclass(frozen=True)
class Config:
    seed: str = "retail-merch-db/0.1"
    n_stores: int = 20
    n_outlets: int = 2
    options_per_season: int = 40
    life_weeks: int = 26  # seasons start 26 weeks apart, so ranges overlap instead of leaving empty weeks


def week_id(index: int) -> str:
    return f"{FIRST_YEAR + index // WEEKS_PER_YEAR}-W{index % WEEKS_PER_YEAR + 1:02d}"


def _u(seed: str, *key) -> float:
    """Uniform number in [0, 1) that depends only on (seed, key)."""
    text = "|".join([seed, *map(str, key)]).encode("utf-8")
    return int.from_bytes(hashlib.blake2b(text, digest_size=8).digest(), "big") / 2**64


def _poisson(lam: float, u: float) -> int:
    """Poisson draw from one uniform number (inverse CDF; normal approximation when large)."""
    if lam <= 0:
        return 0
    if lam > 30:
        z = NormalDist().inv_cdf(min(max(u, 1e-12), 1 - 1e-12))
        return max(0, round(lam + z * math.sqrt(lam)))
    p = math.exp(-lam)
    cdf, k = p, 0
    while u > cdf and k < 200:
        k += 1
        p *= lam / k
        cdf += p
    return k


def _lifecycle(t: int) -> float:
    """Share of peak demand in life week t: two-week ramp, then a slow decline."""
    return min(1.0, 0.6 + 0.2 * t) * max(0.35, 1 - 0.035 * max(0, t - 3))


def _planned_discount(t: int) -> float:
    return 0.0 if t < 14 else (0.3 if t < 18 else 0.5)


def _calendar() -> list[dict]:
    rows = []
    for i in range(N_WEEKS):
        week_no = i % WEEKS_PER_YEAR + 1
        rows.append({
            "week_id": week_id(i),
            "week_index": i,
            "year": FIRST_YEAR + i // WEEKS_PER_YEAR,
            "week_no": week_no,
            "season": "SUMMER" if 9 <= week_no <= 34 else "WINTER",
        })
    return rows


def _stores(cfg: Config) -> list[dict]:
    """Store rows plus a private '_factor' (demand multiplier), removed before output."""
    rows = []
    for i in range(cfg.n_stores):
        city, district = PLACES[i % len(PLACES)]
        suffix = "" if i < len(PLACES) else f" {i // len(PLACES) + 1}"
        rows.append({
            "store_id": str(1000 + 17 * (i + 1)), "name": district + suffix, "city": city,
            "channel": "STORES", "grade": "ABBC"[i % 4],
        })
    rows.append({"store_id": "8000", "name": "ONLINE", "city": "", "channel": "ECOMMERCE", "grade": "A"})
    for j in range(cfg.n_outlets):
        city, district = OUTLET_PLACES[j % len(OUTLET_PLACES)]
        suffix = "" if j < len(OUTLET_PLACES) else f" {j // len(OUTLET_PLACES) + 1}"
        rows.append({
            "store_id": str(9000 + 10 * (j + 1)), "name": district + " Outlet" + suffix, "city": city,
            "channel": "OUTLET", "grade": "C",
        })
    for r in rows:
        base = CHANNEL_FACTOR.get(r["channel"], GRADE_FACTOR[r["grade"]])
        r["_factor"] = base * (0.85 + 0.30 * _u(cfg.seed, "store", r["store_id"]))
        r["capacity_units"] = 0  # set after the simulation, from peak stock
    return rows


def _sizes(size_type: str, gender: str) -> list[str]:
    if size_type == "one":
        return ["STD"]
    return SIZE_RUNS[(size_type, gender if gender in ("MEN", "WOMEN") else "KIDS")]


def _options(cfg: Config) -> list[dict]:
    """One dict per option, holding its public columns and private simulation inputs."""
    options = []
    for season_no, (season, year, start) in enumerate(SEASONS):
        eligible = sorted(g for g, spec in GROUPS.items() if season[0] in spec[0])
        options_in_group = defaultdict(int)
        for i in range(cfg.options_per_season):
            oid = f"{season[0]}{year % 100}-{i + 1:03d}"
            group = eligible[(i * 5 + season_no * 3) % len(eligible)]
            _, size_type, base_price, popularity, genders = GROUPS[group]
            # Fill genders in order, so common adult ranges (men's jeans, women's dresses) always exist.
            gender = genders[options_in_group[group] % len(genders)]
            options_in_group[group] += 1
            kids = gender in ("BOYS", "GIRLS")
            step = (0.8, 1.0, 1.2)[int(_u(cfg.seed, "price", oid) * 3)]
            price = max(50, round(base_price * (0.6 if kids else 1.0) * step / 50) * 50) - 0.01
            imu = 0.55 + 0.13 * _u(cfg.seed, "imu", oid)
            sizes = _sizes(size_type, gender)
            if len(sizes) == 1:
                demand_curve, buy_curve = [1.0], [1.0]
            else:
                tilt = (_u(cfg.seed, "tilt", oid) - 0.5) * 0.08
                raw = [max(0.03, d + tilt * (z - 2) / 2) for z, d in enumerate(DEMAND_CURVE)]
                demand_curve, buy_curve = [x / sum(raw) for x in raw], BUY_CURVE
            options.append({
                "option_id": oid, "gender": gender, "product_group": group, "season": season,
                "season_year": year, "price_gross": round(price, 2),
                "cost": round(price / (1 + VAT_RATE) * (1 - imu), 2),
                "index": i, "launch": start + int(_u(cfg.seed, "launch", oid) * 4),
                "popularity": popularity, "sizes": sizes,
                "demand_curve": demand_curve, "buy_curve": buy_curve,
                "hit": 0.45 + 1.5 * _u(cfg.seed, "hit", oid) ** 1.5,
                "buy_factor": 0.85 + 0.40 * _u(cfg.seed, "buy", oid),
            })
    return options


def _order_lines(cfg: Config, opt: dict, buy_by_size: list[int]) -> list[dict]:
    """Two drops per size: 70% before launch, 30% in life week 5. Next season: first drop only."""
    future = opt["launch"] > AS_OF
    early = future and opt["index"] % 3 == 0  # some next-season stock ships early
    lines = []
    for drop, share_of_buy in ((1, 0.7), (2, 0.3)):
        eta = (AS_OF + 2) if (drop == 1 and early) else opt["launch"] + (-1 if drop == 1 else 5)
        placed = max(0, eta - 12)
        if placed > AS_OF:
            continue  # not ordered yet
        delay = (0, 0, 0, 1, 2)[int(_u(cfg.seed, "delay", opt["option_id"], drop) * 5)]
        received = eta + (min(delay, 1) if early else delay)
        if received <= AS_OF:
            status = "RECEIVED"
        elif received - SHIPPING_WEEKS <= AS_OF:
            status = "IN_TRANSIT"
        else:
            status = "OPEN"
        for z, size in enumerate(opt["sizes"]):
            first = round(buy_by_size[z] * 0.7)
            units = first if drop == 1 else buy_by_size[z] - first
            if units <= 0:
                continue
            lines.append({
                "order_id": f"PO-{opt['option_id']}-{drop}-{size}",
                "sku_id": f"{opt['option_id']}-{size}",
                "units": units,
                "order_week_id": week_id(placed),
                "eta_week_id": week_id(eta),
                "received_week_id": week_id(received) if status == "RECEIVED" else "",
                "status": status,
                "_z": z, "_eta": eta, "_received": received,
            })
    return lines


def generate(cfg: Config = Config()) -> dict[str, list[dict]]:
    """Build every table. Same config, same rows."""
    seed = cfg.seed
    stores = _stores(cfg)
    options = _options(cfg)
    n_stores = len(stores)

    skus, orders, dc_rows, weekly = [], [], [], []
    plan = defaultdict(lambda: [0.0, 0.0, 0])  # (week, gender, group) -> units, gross, intake
    store_stock = defaultdict(int)  # (store_id, week index) -> closing units

    for opt in options:
        oid, sizes, launch, price = opt["option_id"], opt["sizes"], opt["launch"], opt["price_gross"]
        n_sizes = len(sizes)
        skus.extend({"sku_id": f"{oid}-{s}", "option_id": oid, "size": s} for s in sizes)
        rate = BASE_RATE * opt["popularity"]
        plan_key = lambda idx: (week_id(idx), opt["gender"], opt["product_group"])  # noqa: E731

        def discount_for(store: dict, discount: float) -> float:
            return max(discount, 0.3) if store["channel"] == "OUTLET" else discount

        # Plan and buy: expected demand of an average option over the whole life.
        planned_total = 0.0
        for t in range(cfg.life_weeks):
            for s in stores:
                d = discount_for(s, _planned_discount(t))
                units = rate * s["_factor"] * _lifecycle(t) * (1 + ELASTICITY * d)
                planned_total += units
                if launch + t <= AS_OF:
                    row = plan[plan_key(launch + t)]
                    row[0] += units
                    row[1] += units * price * (1 - d)
        buy_by_size = [max(1, round(planned_total * opt["buy_factor"] * c)) for c in opt["buy_curve"]]
        buy_total = sum(buy_by_size)

        lines = _order_lines(cfg, opt, buy_by_size)
        for line in lines:
            if 0 <= line["_eta"] <= AS_OF:
                plan[plan_key(line["_eta"])][2] += line["units"]
        orders.extend({k: v for k, v in line.items() if not k.startswith("_")} for line in lines)
        if launch > AS_OF:
            continue  # next season: nothing has happened in stores yet

        dc = [0] * n_sizes
        on_hand = [[0] * n_sizes for _ in stores]
        last_sales = [[0] * n_sizes for _ in stores]
        discount, sold_net = 0.0, 0

        for idx in range(launch - 1, min(launch + cfg.life_weeks, N_WEEKS)):
            t = idx - launch
            wid = week_id(idx)
            dc_open = dc[:]
            received = [0] * n_sizes
            for line in lines:
                if line["_received"] == idx:
                    received[line["_z"]] += line["units"]
                    dc[line["_z"]] += line["units"]
            shipped = [0] * n_sizes

            if t >= 0:
                sell_through = sold_net / buy_total
                if t in MARKDOWN_CHECKS and sell_through < MARKDOWN_CHECKS[t]:
                    discount = 0.3 if discount == 0 else 0.5
                if t == CLEARANCE_WEEK and sell_through < CLEARANCE_SELL_THROUGH:
                    discount = 0.5
                replenish = t < cfg.life_weeks - NO_REPLENISHMENT_LAST_WEEKS
                for k in range(n_stores):
                    si = (k + idx) % n_stores  # rotate who is served first when the DC runs short
                    store = stores[si]
                    sid, channel = store["store_id"], store["channel"]
                    d = discount_for(store, discount)
                    week_rate = rate * store["_factor"] * _lifecycle(t) * (1 + ELASTICITY * d)
                    for z in range(n_sizes):
                        opening = on_hand[si][z]
                        intake = 0
                        if replenish and dc[z] > 0:
                            expected = week_rate * opt["buy_curve"][z]
                            target = math.ceil((3 if t <= 1 else 2) * max(expected, 1.2 * last_sales[si][z]))
                            if t < 12:
                                target = max(target, 1)
                            intake = min(max(0, target - opening), dc[z])
                            dc[z] -= intake
                            shipped[z] += intake
                        lam = week_rate * opt["demand_curve"][z] * opt["hit"]
                        sales = min(_poisson(lam, _u(seed, "demand", oid, sid, z, idx)), opening + intake)
                        returns = min(
                            last_sales[si][z],
                            _poisson(RETURN_RATE[channel] * last_sales[si][z], _u(seed, "return", oid, sid, z, idx)),
                        )
                        closing = opening + intake - sales + returns
                        if opening or intake or sales or returns:
                            weekly.append({
                                "week_id": wid, "store_id": sid, "sku_id": f"{oid}-{sizes[z]}",
                                "opening_stock": opening, "intake_units": intake, "sales_units": sales,
                                "returns_units": returns, "closing_stock": closing, "discount_rate": d,
                                "sales_gross": round(sales * price * (1 - d), 2),
                            })
                            store_stock[(sid, idx)] += closing
                        on_hand[si][z] = closing
                        last_sales[si][z] = sales
                        sold_net += sales - returns

            for z in range(n_sizes):
                if dc_open[z] or received[z] or shipped[z]:
                    dc_rows.append({
                        "week_id": wid, "sku_id": f"{oid}-{sizes[z]}", "opening_stock": dc_open[z],
                        "received_units": received[z], "shipped_units": shipped[z], "closing_stock": dc[z],
                    })

    peak = defaultdict(int)
    for (sid, _), units in store_stock.items():
        peak[sid] = max(peak[sid], units)
    for s in stores:
        headroom = 1.5 if s["channel"] == "ECOMMERCE" else 0.9 + 0.3 * _u(seed, "capacity", s["store_id"])
        s["capacity_units"] = math.ceil(peak[s["store_id"]] * headroom / 100) * 100

    public = ("option_id", "gender", "product_group", "season", "season_year")
    products = [
        {**{k: o[k] for k in public}, "launch_week_id": week_id(o["launch"]),
         "price_gross": o["price_gross"], "cost": o["cost"], "vat_rate": VAT_RATE}
        for o in options
    ]
    plan_rows = [
        {"week_id": w, "gender": g, "product_group": pg, "planned_sales_units": round(v[0]),
         "planned_sales_gross": round(v[1], 2), "planned_intake_units": v[2]}
        for (w, g, pg), v in sorted(plan.items())
    ]
    return {
        "calendar": _calendar(),
        "stores": [{k: v for k, v in s.items() if not k.startswith("_")} for s in stores],
        "products": products,
        "skus": skus,
        "orders": orders,
        "dc_stock": dc_rows,
        "weekly": weekly,
        "plan": plan_rows,
    }


def checksum(tables: dict[str, list[dict]]) -> str:
    """SHA-256 of all rows, for checking that a rebuild is identical."""
    return hashlib.sha256(json.dumps(tables, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def write_csv(tables: dict[str, list[dict]], out_dir) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        with open(out / f"{name}.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="data")
    parser.add_argument("--seed", default=Config.seed)
    args = parser.parse_args()
    tables = generate(Config(seed=args.seed))
    write_csv(tables, args.out)
    for name, rows in tables.items():
        print(f"{name:<9} {len(rows):>8} rows")
    print("sha256", checksum(tables))


if __name__ == "__main__":
    main()
