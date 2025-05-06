"""The WhatPulse integration."""
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.discovery import load_platform

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

    # Set up each platform for this config entry
    for platform in PLATFORMS:
        # Only set up button if client API is enabled
        if platform == "button" and entry.data.get(CONF_API_TYPE) not in [API_TYPE_CLIENT, API_TYPE_BOTH]:
            continue

        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    # Set up services if client API is enabled
    if entry.data.get(CONF_API_TYPE) in [API_TYPE_CLIENT, API_TYPE_BOTH]:
        setup_services(hass, entry.data)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
