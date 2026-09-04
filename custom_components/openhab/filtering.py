"""Helpers for filtering noisy openHAB items."""
from __future__ import annotations

from .const import CONF_EXCLUDED_ITEM_NAMES, CONF_EXCLUDED_ITEM_PREFIXES


def _parse_csv(value: str | None) -> tuple[str, ...]:
    """Parse a comma-separated option into normalized values."""
    if not value:
        return ()
    return tuple(value.strip().lower() for value in value.split(",") if value.strip())


def prefixes_from_options(options: dict) -> tuple[str, ...]:
    """Return configured item-name prefixes."""
    return _parse_csv(options.get(CONF_EXCLUDED_ITEM_PREFIXES, ""))


def names_from_options(options: dict) -> tuple[str, ...]:
    """Return configured exact item names."""
    return _parse_csv(options.get(CONF_EXCLUDED_ITEM_NAMES, ""))


def item_is_excluded(
    item_name: str,
    prefixes: tuple[str, ...],
    names: tuple[str, ...] = (),
) -> bool:
    """Return True when an item matches an exact name or configured prefix."""
    name = item_name.lower()
    return name in names or any(name.startswith(prefix) for prefix in prefixes)
