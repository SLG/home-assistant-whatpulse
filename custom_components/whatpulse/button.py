"""Button platform for WhatPulse integration."""
import logging

import voluptuous as vol
import requests

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_CLIENT_API_URL,
    DEFAULT_CLIENT_API_URL,
    CONF_API_TYPE,
    API_TYPE_CLIENT,
    API_TYPE_BOTH,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the WhatPulse button platform."""
    # Get configuration from either discovery info or direct config
    if discovery_info:
        client_api_url = discovery_info.get(CONF_CLIENT_API_URL, DEFAULT_CLIENT_API_URL)
        api_type = discovery_info.get(CONF_API_TYPE)
    else:
        client_api_url = config.get(CONF_CLIENT_API_URL, DEFAULT_CLIENT_API_URL)
        api_type = config.get(CONF_API_TYPE, API_TYPE_BOTH)  # Default to both if not specified

    # Only proceed if client API is enabled
    if api_type not in [API_TYPE_CLIENT, API_TYPE_BOTH]:
        _LOGGER.warning("WhatPulse buttons require client API to be enabled")
        return

    _LOGGER.info(f"Setting up WhatPulse buttons with client API URL: {client_api_url}")

    buttons = [
        WhatPulseButton(
            client_api_url,
            "pulse",
            "Pulse",
            "mdi:pulse",
            "Trigger a manual pulse",
            "/v1/pulse"
        ),
        WhatPulseButton(
            client_api_url,
            "open_window",
            "Open Client",
            "mdi:window-maximize",
            "Show the WhatPulse client window",
            "/v1/open-window"
        ),
    ]

    async_add_entities(buttons, True)


class WhatPulseButton(ButtonEntity):
    """Representation of a WhatPulse button."""

    def __init__(self, client_api_url, action_id, name, icon, description, endpoint):
        """Initialize the button."""
        self._client_api_url = client_api_url
        self._action_id = action_id
        self._name = name
        self._icon = icon
        self._description = description
        self._endpoint = endpoint
        self._attr_unique_id = f"whatpulse_button_{action_id}"

    @property
    def name(self):
        """Return the name of the button."""
        return f"WhatPulse {self._name}"

    @property
    def icon(self):
        """Return the icon of the button."""
        return self._icon

    @property
    def device_class(self):
        """Return the device class of the button."""
        return None

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        return {"description": self._description}

    async def async_press(self):
        """Press the button."""
        await self.hass.async_add_executor_job(self._perform_action)

    def _perform_action(self):
        """Perform the button action."""
        url = f"{self._client_api_url}{self._endpoint}"

        try:
            # Send empty POST request to the endpoint
            response = requests.post(url, timeout=10)

            if response.status_code != 200:
                _LOGGER.error(f"Failed to {self._action_id}: {response.status_code}, {response.text}")
                return False

            _LOGGER.info(f"Successfully performed action: {self._action_id}")
            return True

        except Exception as ex:
            _LOGGER.error(f"Error performing {self._action_id} action: {ex}")
            return False