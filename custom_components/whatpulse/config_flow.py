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


def _build_unique_id(data: dict) -> str | None:
    """Build a stable unique ID for config entries."""
    api_type = data.get(CONF_API_TYPE, DEFAULT_API_TYPE)
    userid = (data.get(CONF_USERID) or "").strip()
    username = (data.get(CONF_USERNAME) or "").strip()
    client_api_url = (data.get(CONF_CLIENT_API_URL) or DEFAULT_CLIENT_API_URL).rstrip("/").lower()

    identifier = userid or username

    if api_type == API_TYPE_CLIENT:
        return f"client:{client_api_url}"

    if api_type == API_TYPE_BOTH:
        if identifier:
            return f"both:{identifier.lower()}@{client_api_url}"
        return f"both:{client_api_url}"

    if identifier:
        return f"public:{identifier.lower()}"

    return None


def _build_entry_title(data: dict) -> str:
    """Build a human-readable config entry title."""
    api_type = data[CONF_API_TYPE]

    if api_type == API_TYPE_PUBLIC:
        identifier = data.get(CONF_USERID) or data.get(CONF_USERNAME) or "WhatPulse"
        return f"WhatPulse ({identifier})"

    if api_type == API_TYPE_CLIENT:
        return f"WhatPulse Client ({data.get(CONF_CLIENT_API_URL, DEFAULT_CLIENT_API_URL)})"

    identifier = data.get(CONF_USERID) or data.get(CONF_USERNAME) or "WhatPulse"
    return f"WhatPulse ({identifier})"


def _is_client_only_sensor(sensor_info: dict) -> bool:
    """Return True if sensor is only available from the local client API."""
    client_path = sensor_info.get("client_path")
    return client_path is not None and client_path[0] in ["realtime", "unpulsed"]


def _sensor_options_for_api_type(api_type: str) -> dict:
    """Build options list for sensors supported by selected API type."""
    options = {}
    for sensor_key, sensor_info in SENSOR_TYPES.items():
        if api_type == API_TYPE_PUBLIC and _is_client_only_sensor(sensor_info):
            continue
        if api_type == API_TYPE_CLIENT and sensor_info.get("client_path") is None:
            continue

        # Use key in label to avoid ambiguity between similarly named sensors.
        options[sensor_key] = f"{sensor_info['name']} ({sensor_key})"

    return options


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

    async def async_step_import(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Import configuration from legacy YAML."""
        if not user_input:
            _LOGGER.warning("WhatPulse YAML import called without data; aborting.")
            return self.async_abort(reason="unknown")

        self._data = {
            CONF_API_TYPE: user_input.get(CONF_API_TYPE, DEFAULT_API_TYPE),
            CONF_USERID: (user_input.get(CONF_USERID) or "").strip(),
            CONF_USERNAME: (user_input.get(CONF_USERNAME) or "").strip(),
            CONF_API_TOKEN: (user_input.get(CONF_API_TOKEN) or "").strip(),
            CONF_CLIENT_API_URL: (user_input.get(CONF_CLIENT_API_URL) or DEFAULT_CLIENT_API_URL).rstrip("/"),
            CONF_SENSORS: user_input.get(CONF_SENSORS, DEFAULT_SENSORS),
        }

        unique_id = _build_unique_id(self._data)
        _LOGGER.debug(
            "Processing WhatPulse YAML import (unique_id=%s, api_type=%s)",
            unique_id,
            self._data.get(CONF_API_TYPE),
        )
        if unique_id:
            for entry in self._async_current_entries():
                if entry.unique_id == unique_id:
                    # Keep existing installs in sync when YAML import changes.
                    self.hass.config_entries.async_update_entry(entry, data=self._data)
                    _LOGGER.info(
                        "Updated existing WhatPulse config entry from YAML import (entry_id=%s, unique_id=%s).",
                        entry.entry_id,
                        unique_id,
                    )
                    return self.async_abort(reason="already_configured")
            await self.async_set_unique_id(unique_id)

        _LOGGER.info("Creating WhatPulse config entry from YAML import.")
        return self.async_create_entry(title=_build_entry_title(self._data), data=self._data)

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
                return await self._create_entry()

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
                return await self._create_entry()

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

    async def _create_entry(self) -> config_entries.FlowResult:
        """Create the config entry."""
        unique_id = _build_unique_id(self._data)
        if unique_id:
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

        _LOGGER.info(
            "Creating WhatPulse config entry from user flow (api_type=%s, unique_id=%s).",
            self._data.get(CONF_API_TYPE),
            unique_id,
        )
        return self.async_create_entry(
            title=_build_entry_title(self._data),
            data=self._data,
        )

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
            user_input = dict(user_input)

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
                    user_input[CONF_CLIENT_API_URL] = client_api_url

            if not errors:
                sensor_options = _sensor_options_for_api_type(api_type)
                selected_sensors = list(user_input.get(CONF_SENSORS, []))
                invalid_selection = [sensor for sensor in selected_sensors if sensor not in sensor_options]
                if invalid_selection:
                    errors["base"] = "invalid_sensors"
                else:
                    user_input[CONF_SENSORS] = selected_sensors

            if not errors:
                return self.async_create_entry(title="", data=user_input)

        api_type = current_data.get(CONF_API_TYPE, DEFAULT_API_TYPE)
        sensor_options = _sensor_options_for_api_type(api_type)
        default_sensors = [
            sensor
            for sensor in current_data.get(CONF_SENSORS, DEFAULT_SENSORS)
            if sensor in sensor_options
        ]

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

        fields[
            vol.Optional(
                CONF_SENSORS,
                default=default_sensors,
            )
        ] = cv.multi_select(sensor_options)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

