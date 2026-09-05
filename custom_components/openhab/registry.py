"""Entity-registry helpers for openHAB."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_BASE_URL, DOMAIN, LOGGER
from .filtering import (
    item_is_excluded,
    names_from_options,
    prefixes_from_options,
)
from .utils import strip_ip


def _item_name_from_registry_entry(
    entry: ConfigEntry,
    registry_entry: er.RegistryEntry,
) -> str | None:
    """Extract the openHAB item name from an entity-registry entry."""
    host = strip_ip(entry.data[CONF_BASE_URL]).lower()
    unique_id_prefix = f"{DOMAIN}_{host}_"
    unique_id = (registry_entry.unique_id or "").lower()

    if not unique_id.startswith(unique_id_prefix):
        return None

    return unique_id[len(unique_id_prefix):]


async def async_reconcile_filtered_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    old_options: dict,
    new_options: dict,
) -> tuple[int, int]:
    """Apply changed filters to entities already present in the registry.

    Newly matched entities are disabled by the integration. Entities that
    matched the previous filter but no longer match the new filter are enabled
    again, but only when they were disabled by the integration.
    """
    old_prefixes = prefixes_from_options(old_options)
    old_names = names_from_options(old_options)
    new_prefixes = prefixes_from_options(new_options)
    new_names = names_from_options(new_options)

    registry = er.async_get(hass)
    disabled = 0
    enabled = 0

    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        item_name = _item_name_from_registry_entry(entry, registry_entry)
        if item_name is None:
            continue

        matched_old = item_is_excluded(item_name, old_prefixes, old_names)
        matched_new = item_is_excluded(item_name, new_prefixes, new_names)

        if matched_new and registry_entry.disabled_by is None:
            registry.async_update_entity(
                registry_entry.entity_id,
                disabled_by=er.RegistryEntryDisabler.INTEGRATION,
            )
            disabled += 1
            continue

        if (
            matched_old
            and not matched_new
            and registry_entry.disabled_by == er.RegistryEntryDisabler.INTEGRATION
        ):
            registry.async_update_entity(
                registry_entry.entity_id,
                disabled_by=None,
            )
            enabled += 1

    LOGGER.info(
        "Reconciled openHAB filters: disabled %s entities and re-enabled %s entities",
        disabled,
        enabled,
    )
    return disabled, enabled


async def async_disable_filtered_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> int:
    """Disable existing registry entities matching the current filters.

    This remains available as an advanced/manual recovery action. Normal option
    changes apply the filters automatically.
    """
    prefixes = prefixes_from_options(entry.options)
    names = names_from_options(entry.options)
    if not prefixes and not names:
        return 0

    registry = er.async_get(hass)
    changed = 0

    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        item_name = _item_name_from_registry_entry(entry, registry_entry)
        if item_name is None:
            continue

        if not item_is_excluded(item_name, prefixes, names):
            continue

        if registry_entry.disabled_by is not None:
            continue

        registry.async_update_entity(
            registry_entry.entity_id,
            disabled_by=er.RegistryEntryDisabler.INTEGRATION,
        )
        changed += 1

    LOGGER.info(
        "Disabled %s existing openHAB entities matching the current filters",
        changed,
    )
    return changed
