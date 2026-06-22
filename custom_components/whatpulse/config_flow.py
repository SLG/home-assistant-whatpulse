"""Config flow for WhatPulse integration."""
from __future__ import annotations

import logging
import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_USERID,
    CONF_API_TOKEN,
    CONF_API_TYPE,
    CONF_CLIENT_API_URL,
    CONF_SENSORS,
    API_TYPE_PUBLIC,
    API_TYPE_CLIENT,
    API_TYPE_BOTH,
    DEFAULT_API_TYPE,
    DEFAULT_CLIENT_API_URL,
    DEFAULT_SENSORS,
    PUBLIC_API_URL,
    SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)


def _validate_public_api(userid: str | None, username: str | None, api_token: str) -> dict:
    """Validate the public API credentials by making a test request."""
    identifier = userid if userid else username
    url = f"{PUBLIC_API_URL}{identifier}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 401:
            return {"base": "invalid_auth"}
        if response.status_code == 404:
            return {"base": "user_not_found"}
        if response.status_code != 200:
            return {"base": "cannot_connect"}
        data = response.json()
        if "user" not in data:
            return {"base": "invalid_response"}
    except requests.exceptions.ConnectionError:
        return {"base": "cannot_connect"}
    except Exception:  # pylint: disable=broad-except
        return {"base": "unknown"}
    return {}


def _validate_client_api(client_api_url: str) -> dict:
    """Validate the client API by making a test request."""
    url = f"{client_api_url}/v1/all-stats"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return {"base": "client_cannot_connect"}
    except requests.exceptions.ConnectionError:
        return {"base": "client_cannot_connect"}
    except Exception:  # pylint: disable=broad-except
        return {"base": "unknown"}
    return {}


class WhatPulseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WhatPulse."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict = {}

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step – choose API type."""
        errors: dict = {}

        if user_input is not None:
            self._data[CONF_API_TYPE] = user_input[CONF_API_TYPE]

            api_type = user_input[CONF_API_TYPE]
            if api_type in [API_TYPE_PUBLIC, API_TYPE_BOTH]:
                return await self.async_step_public_config()
            # Client-only: go straight to client config
            return await self.async_step_client_config()

        schema = vol.Schema(
            {
                vol.Required(CONF_API_TYPE, default=DEFAULT_API_TYPE): vol.In(
                    {
                        API_TYPE_PUBLIC: "Public API only",
                        API_TYPE_CLIENT: "Local client API only",
                        API_TYPE_BOTH: "Both public & local client API",
                    }
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_public_config(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the public API configuration step."""
        errors: dict = {}

        if user_input is not None:
            userid = user_input.get(CONF_USERID, "").strip() or None
            username = user_input.get(CONF_USERNAME, "").strip() or None
            api_token = user_input.get(CONF_API_TOKEN, "").strip()

            if not userid and not username:
                errors["base"] = "missing_identifier"
            elif not api_token:
                errors[CONF_API_TOKEN] = "required"
            else:
                errors = await self.hass.async_add_executor_job(
                    _validate_public_api, userid, username, api_token
                )

            if not errors:
                self._data[CONF_USERID] = userid or ""
                self._data[CONF_USERNAME] = username or ""
                self._data[CONF_API_TOKEN] = api_token

                api_type = self._data[CONF_API_TYPE]
                if api_type == API_TYPE_BOTH:
                    return await self.async_step_client_config()

                # Public-only: done
                return self._create_entry()

        schema = vol.Schema(
            {
                vol.Optional(CONF_USERID, default=""): cv.string,
                vol.Optional(CONF_USERNAME, default=""): cv.string,
                vol.Required(CONF_API_TOKEN): cv.string,
            }
        )

        return self.async_show_form(
            step_id="public_config",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "public_api_docs": "https://whatpulse.org/settings/api"
            },
        )

    async def async_step_client_config(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the local client API configuration step."""
        errors: dict = {}

        if user_input is not None:
            client_api_url = user_input.get(CONF_CLIENT_API_URL, DEFAULT_CLIENT_API_URL).rstrip("/")

            errors = await self.hass.async_add_executor_job(
                _validate_client_api, client_api_url
            )

            if not errors:
                self._data[CONF_CLIENT_API_URL] = client_api_url
                return self._create_entry()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CLIENT_API_URL, default=DEFAULT_CLIENT_API_URL
                ): cv.string,
            }
        )

        return self.async_show_form(
            step_id="client_config",
            data_schema=schema,
            errors=errors,
        )

    def _create_entry(self) -> config_entries.FlowResult:
        """Create the config entry."""
        api_type = self._data[CONF_API_TYPE]

        # Build a human-readable title
        if api_type == API_TYPE_PUBLIC:
            identifier = self._data.get(CONF_USERID) or self._data.get(CONF_USERNAME) or "WhatPulse"
            title = f"WhatPulse ({identifier})"
        elif api_type == API_TYPE_CLIENT:
            title = f"WhatPulse Client ({self._data.get(CONF_CLIENT_API_URL, DEFAULT_CLIENT_API_URL)})"
        else:
            identifier = self._data.get(CONF_USERID) or self._data.get(CONF_USERNAME) or "WhatPulse"
            title = f"WhatPulse ({identifier})"

        return self.async_create_entry(title=title, data=self._data)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> WhatPulseOptionsFlow:
        """Return an options flow handler."""
        return WhatPulseOptionsFlow(config_entry)


class WhatPulseOptionsFlow(config_entries.OptionsFlow):
    """Handle WhatPulse options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        errors: dict = {}
        current_data = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            # Validate public API settings if applicable
            api_type = current_data.get(CONF_API_TYPE, DEFAULT_API_TYPE)
            if api_type in [API_TYPE_PUBLIC, API_TYPE_BOTH]:
                userid = user_input.get(CONF_USERID, "").strip() or None
                username = user_input.get(CONF_USERNAME, "").strip() or None
                api_token = user_input.get(CONF_API_TOKEN, "").strip()

                if not userid and not username:
                    errors["base"] = "missing_identifier"
                elif not api_token:
                    errors[CONF_API_TOKEN] = "required"
                else:
                    errors = await self.hass.async_add_executor_job(
                        _validate_public_api, userid, username, api_token
                    )

            if not errors:
                if api_type in [API_TYPE_CLIENT, API_TYPE_BOTH]:
                    client_api_url = user_input.get(CONF_CLIENT_API_URL, DEFAULT_CLIENT_API_URL).rstrip("/")
                    errors = await self.hass.async_add_executor_job(
                        _validate_client_api, client_api_url
                    )

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        api_type = current_data.get(CONF_API_TYPE, DEFAULT_API_TYPE)
        fields: dict = {}

        if api_type in [API_TYPE_PUBLIC, API_TYPE_BOTH]:
            fields[vol.Optional(CONF_USERID, default=current_data.get(CONF_USERID, ""))] = cv.string
            fields[vol.Optional(CONF_USERNAME, default=current_data.get(CONF_USERNAME, ""))] = cv.string
            fields[vol.Required(CONF_API_TOKEN, default=current_data.get(CONF_API_TOKEN, ""))] = cv.string

        if api_type in [API_TYPE_CLIENT, API_TYPE_BOTH]:
            fields[vol.Required(
                CONF_CLIENT_API_URL,
                default=current_data.get(CONF_CLIENT_API_URL, DEFAULT_CLIENT_API_URL),
            )] = cv.string

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

