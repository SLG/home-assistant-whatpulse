"""The WhatPulse integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    CONF_API_TYPE,
    CONF_CLIENT_API_URL,
    API_TYPE_CLIENT,
    API_TYPE_BOTH
)
from .services import setup_services

_LOGGER = logging.getLogger(__name__)

# List of platforms to support
PLATFORMS = ["sensor", "button"]

async def async_setup(hass: HomeAssistant, config):
    """Set up the WhatPulse component from YAML."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up WhatPulse from a config entry."""
    # Store entry data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    api_type = entry.data.get(CONF_API_TYPE)

    # Determine which platforms to load
    platforms_to_load = ["sensor"]
    if api_type in [API_TYPE_CLIENT, API_TYPE_BOTH]:
        platforms_to_load.append("button")

    hass.data[DOMAIN][entry.entry_id + "_platforms"] = platforms_to_load

    await hass.config_entries.async_forward_entry_setups(entry, platforms_to_load)

    # Set up services if client API is enabled
    if api_type in [API_TYPE_CLIENT, API_TYPE_BOTH]:
        setup_services(hass, entry.data)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    platforms_to_unload = hass.data[DOMAIN].get(entry.entry_id + "_platforms", PLATFORMS)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, platforms_to_unload)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        hass.data[DOMAIN].pop(entry.entry_id + "_platforms", None)

    return unload_ok
