"""Entity-registry helpers for openHAB."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_BASE_URL, DOMAIN, LOGGER
from .filtering import prefixes_from_options
from .utils import strip_ip


async def async_disable_filtered_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> int:
    """Disable existing registry entities matching configured item prefixes.

    Only currently enabled entities owned by this config entry are changed.
    User-disabled entities and entities from other integrations are untouched.
    """
    prefixes = prefixes_from_options(entry.options)
    if not prefixes:
        return 0

    registry = er.async_get(hass)
    host = strip_ip(entry.data[CONF_BASE_URL]).lower()
    unique_id_prefix = f"{DOMAIN}_{host}_"
    changed = 0

    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        unique_id = (registry_entry.unique_id or "").lower()
        if not unique_id.startswith(unique_id_prefix):
            continue

        item_name = unique_id[len(unique_id_prefix):]
        if not any(item_name.startswith(prefix) for prefix in prefixes):
            continue

        if registry_entry.disabled_by is not None:
            continue

        registry.async_update_entity(
            registry_entry.entity_id,
            disabled_by=er.RegistryEntryDisabler.INTEGRATION,
        )
        changed += 1

    LOGGER.info(
        "Disabled %s existing openHAB entities matching configured prefixes for %s",
        changed,
        host,
    )
    return changed
