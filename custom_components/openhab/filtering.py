"""Helpers for filtering noisy openHAB items."""
from __future__ import annotations

from .const import CONF_EXCLUDED_ITEM_PREFIXES


def parse_excluded_prefixes(value: str | None) -> tuple[str, ...]:
    """Parse a comma-separated list of openHAB item prefixes."""
    if not value:
        return ()
    return tuple(
        prefix.strip().lower()
        for prefix in value.split(",")
        if prefix.strip()
    )


def item_is_excluded(item_name: str, prefixes: tuple[str, ...]) -> bool:
    """Return True when an openHAB item matches a configured prefix."""
    name = item_name.lower()
    return any(name.startswith(prefix) for prefix in prefixes)


def prefixes_from_options(options: dict) -> tuple[str, ...]:
    """Return configured prefixes from config-entry options."""
    return parse_excluded_prefixes(options.get(CONF_EXCLUDED_ITEM_PREFIXES, ""))
