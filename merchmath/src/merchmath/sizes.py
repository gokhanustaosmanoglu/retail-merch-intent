"""Size-run health."""

from __future__ import annotations

from typing import Mapping, Sequence


def size_availability(stock_by_size: Mapping[str, float], core_sizes: Sequence[str]) -> float:
    """Share of core sizes that still have stock. Sizes outside the core run are ignored."""
    if not core_sizes:
        raise ValueError("core_sizes must name at least one size")
    in_stock = sum(1 for size in core_sizes if stock_by_size.get(size, 0) > 0)
    return in_stock / len(core_sizes)


def is_broken(stock_by_size: Mapping[str, float], core_sizes: Sequence[str]) -> bool:
    """Whether an option's size run is broken.

    RULE (a business decision, change it to match how you trade): an option is
    broken when at least one core size is out of stock while another core size
    still has stock. A fully sold-out option is not broken, it is sold out.
    """
    availability = size_availability(stock_by_size, core_sizes)
    return 0 < availability < 1
