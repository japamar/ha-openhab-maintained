"""
Custom integration to integrate openHAB with Home Assistant.

Maintained fork:
https://github.com/japamar/ha-openhab-maintained
"""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

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
from .coordinator import OpenHABDataUpdateCoordinator\nfrom .filtering import prefixes_from_options


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
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    enabled_platforms = []

    for platform in PLATFORMS:
        if entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            enabled_platforms.append(platform)

    await hass.config_entries.async_forward_entry_setups(
        entry,
        enabled_platforms,
    )

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
