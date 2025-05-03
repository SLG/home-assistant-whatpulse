"""WhatPulse services."""
import logging
import voluptuous as vol
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall

from .const import (
    DOMAIN,
    CONF_CLIENT_API_URL,
    CONF_API_TYPE,
    API_TYPE_CLIENT,
    API_TYPE_BOTH,
)

_LOGGER = logging.getLogger(__name__)

PROFILE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("profile_id"): cv.positive_int,
        vol.Optional("client_api_url"): cv.string,
    }
)

def setup_services(hass: HomeAssistant, config_entry):
    """Set up services for the WhatPulse integration."""
    client_api_url = config_entry.get(CONF_CLIENT_API_URL)
    api_type = config_entry.get(CONF_API_TYPE)

    if api_type not in [API_TYPE_CLIENT, API_TYPE_BOTH]:
        return

    async def activate_profile(call: ServiceCall):
        """Activate a specific profile."""
        profile_id = call.data["profile_id"]
        url = call.data.get("client_api_url", client_api_url)

        if not url:
            _LOGGER.error("No client API URL provided")
            return

        try:
            response = requests.post(
                f"{url}/v1/profiles/activate",
                json={"profile_id": profile_id},
                timeout=10
            )

            if response.status_code != 200:
                _LOGGER.error(f"Failed to activate profile {profile_id}: {response.status_code}, {response.text}")
                return

            _LOGGER.info(f"Successfully activated profile ID: {profile_id}")

        except Exception as ex:
            _LOGGER.error(f"Error activating profile {profile_id}: {ex}")

    # Register the service
    hass.services.register(
        DOMAIN,
        "activate_profile",
        activate_profile,
        schema=PROFILE_SERVICE_SCHEMA
    )