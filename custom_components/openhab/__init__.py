"""
Custom integration to integrate openHAB with Home Assistant.

Maintained fork:
https://github.com/japamar/ha-openhab-maintained
"""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .api import OpenHABApiClient
from .const import (
    CONF_AUTH_TOKEN,
    CONF_AUTH_TYPE,
    CONF_BASE_URL,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    LOGGER,
    PLATFORMS,
    STARTUP_MESSAGE,
)
from .coordinator import OpenHABDataUpdateCoordinator
from .filtering import names_from_options, prefixes_from_options
from .registry import async_disable_filtered_entities


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up integration-level services."""

    async def handle_disable_filtered_entities(call: ServiceCall) -> None:
        """Disable already-registered entities matching configured prefixes."""
        total = 0
        for config_entry in hass.config_entries.async_entries(DOMAIN):
            total += await async_disable_filtered_entities(hass, config_entry)
        LOGGER.info("openHAB filter migration disabled %s entities in total", total)

    if not hass.services.has_service(DOMAIN, "disable_filtered_entities"):
        hass.services.async_register(
            DOMAIN,
            "disable_filtered_entities",
            handle_disable_filtered_entities,
        )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    LOGGER.info(STARTUP_MESSAGE)
    hass.data.setdefault(DOMAIN, {})

    api_client = OpenHABApiClient(
        hass=hass,
        base_url=entry.data[CONF_BASE_URL],
        auth_type=entry.data[CONF_AUTH_TYPE],
        auth_token=entry.data.get(CONF_AUTH_TOKEN, ""),
        username=entry.data.get(CONF_USERNAME, ""),
        password=entry.data.get(CONF_PASSWORD, ""),
    )

    coordinator = OpenHABDataUpdateCoordinator(hass, api=api_client)
    coordinator.excluded_item_prefixes = prefixes_from_options(entry.options)
    coordinator.excluded_item_names = names_from_options(entry.options)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    enabled_platforms = []
    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            enabled_platforms.append(platform)

    await hass.config_entries.async_forward_entry_setups(entry, enabled_platforms)

    entry.add_update_listener(async_reload_entry)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, [platform for platform in PLATFORMS if platform in coordinator.platforms]
    ):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
