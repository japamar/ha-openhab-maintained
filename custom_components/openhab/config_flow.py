"""Adds config flow for openHAB."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .api import OpenHABApiClient
from .const import (
    AUTH_TYPES,
    CONF_AUTH_TOKEN,
    CONF_AUTH_TYPE,
    CONF_AUTH_TYPE_BASIC,
    CONF_AUTH_TYPE_TOKEN,
    CONF_BASE_URL,
    CONF_EXCLUDED_ITEM_NAMES,
    CONF_EXCLUDED_ITEM_PREFIXES,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    LOGGER,
    PLATFORMS,
)
from .filtering import normalize_csv
from .registry import async_reconcile_filtered_entities
from .utils import strip_ip


class OpenHABFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for openHAB."""

    VERSION = 1
    data = None

    async def async_step_user(
        self,
        user_input: dict[str, str] | None = None,
    ):
        """Handle a flow initialized by the user."""
        errors = {}

        LOGGER.info(user_input)

        if user_input is not None:
            self.data = user_input
            return await self.async_step_credentials(user_input)

        user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BASE_URL,
                        default=user_input.get(CONF_BASE_URL, "http://"),
                    ): str,
                    vol.Required(
                        CONF_AUTH_TYPE,
                        default=user_input.get(CONF_AUTH_TYPE, CONF_AUTH_TYPE_TOKEN),
                    ): vol.In(AUTH_TYPES),
                }
            ),
            errors=errors,
        )

    async def async_step_credentials(
        self,
        user_input: dict[str, str] | None = None,
    ):
        """Handle credential entry."""
        errors = {}
        user_input = user_input or {}

        user_input[CONF_BASE_URL] = self.data[CONF_BASE_URL]
        user_input[CONF_AUTH_TYPE] = self.data[CONF_AUTH_TYPE]

        if CONF_AUTH_TOKEN in user_input or CONF_USERNAME in user_input:
            if await self._test_credentials(
                user_input[CONF_BASE_URL],
                user_input[CONF_AUTH_TYPE],
                user_input.get(CONF_AUTH_TOKEN, ""),
                user_input.get(CONF_USERNAME, ""),
                user_input.get(CONF_PASSWORD, ""),
            ):
                return self.async_create_entry(
                    title=strip_ip(user_input[CONF_BASE_URL]),
                    data=user_input,
                )
            errors["base"] = "auth"

        if user_input[CONF_AUTH_TYPE] == CONF_AUTH_TYPE_BASIC:
            schema = {
                vol.Optional(
                    CONF_USERNAME,
                    default=user_input.get(CONF_USERNAME, ""),
                ): cv.string,
                vol.Optional(
                    CONF_PASSWORD,
                    default=user_input.get(CONF_PASSWORD, ""),
                ): cv.string,
            }
        else:
            schema = {
                vol.Required(
                    CONF_AUTH_TOKEN,
                    default=user_input.get(CONF_AUTH_TOKEN, ""),
                ): cv.string,
            }

        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OpenHABOptionsFlowHandler()

    async def _test_credentials(
        self,
        base_url: str,
        auth_type: str,
        auth_token: str,
        username: str,
        password: str,
    ):
        """Return true if credentials are valid."""
        client = OpenHABApiClient(
            self.hass,
            base_url,
            auth_type,
            auth_token,
            username,
            password,
        )
        await client.async_get_version()
        return True


class OpenHABOptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """openHAB options flow handler."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            old_options = dict(self.config_entry.options)
            new_options = dict(user_input)
            new_options[CONF_EXCLUDED_ITEM_PREFIXES] = normalize_csv(
                new_options.get(CONF_EXCLUDED_ITEM_PREFIXES, "")
            )
            new_options[CONF_EXCLUDED_ITEM_NAMES] = normalize_csv(
                new_options.get(CONF_EXCLUDED_ITEM_NAMES, "")
            )

            await async_reconcile_filtered_entities(
                self.hass,
                self.config_entry,
                old_options,
                new_options,
            )
            return self.async_create_entry(data=new_options)

        current = dict(self.config_entry.options)

        schema = {
            vol.Required(x, default=current.get(x, True)): bool
            for x in sorted(PLATFORMS)
        }
        schema[
            vol.Optional(
                CONF_EXCLUDED_ITEM_PREFIXES,
                default=current.get(CONF_EXCLUDED_ITEM_PREFIXES, ""),
            )
        ] = cv.string
        schema[
            vol.Optional(
                CONF_EXCLUDED_ITEM_NAMES,
                default=current.get(CONF_EXCLUDED_ITEM_NAMES, ""),
            )
        ] = cv.string

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
