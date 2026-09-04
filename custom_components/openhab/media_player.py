"""Media Player platform for openHAB."""

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ITEMS_MAP, MEDIA_PLAYER
from .device_classes_map import MEDIA_PLAYER_DEVICE_CLASS_MAP
from .entity import OpenHABEntity

SUPPORT_OPENHAB = (
    MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.VOLUME_SET
)

PLAYBACK_DICT = {
    "PLAYING": MediaPlayerState.PLAYING,
    "PAUSED": MediaPlayerState.PAUSED,
    "STOPPED": MediaPlayerState.IDLE,
    "NULL": MediaPlayerState.IDLE,
    "UNDEF": MediaPlayerState.IDLE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup media player platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        OpenHABPlayer(hass, coordinator, item)
        for item in coordinator.data.values()
        if item.type_ == ITEMS_MAP[MEDIA_PLAYER]
    )


class OpenHABPlayer(OpenHABEntity, MediaPlayerEntity):
    """openHAB Player class."""

    _attr_device_class_map = MEDIA_PLAYER_DEVICE_CLASS_MAP

    async def async_update(self) -> None:
        """Update openHAB Player entity."""
        await self.coordinator.async_request_refresh()

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def state(self):
        """Return the state of the player."""
        if not self.item._state:
            return MediaPlayerState.OFF
        return PLAYBACK_DICT.get(self.item._state, MediaPlayerState.IDLE)

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MediaType.MUSIC

    @property
    def supported_features(self):
        """Return the supported features."""
        return SUPPORT_OPENHAB

    async def async_media_play(self) -> None:
        """Play."""
        await self.hass.async_add_executor_job(self.item.play)
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        """Pause."""
        await self.hass.async_add_executor_job(self.item.pause)
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self.hass.async_add_executor_job(self.item.next)
        await self.coordinator.async_request_refresh()

    async def async_media_previous_track(self) -> None:
        """Send the previous track command."""
        await self.hass.async_add_executor_job(self.item.previous)
        await self.coordinator.async_request_refresh()
