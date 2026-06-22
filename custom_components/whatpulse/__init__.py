"""The WhatPulse integration."""
import logging

from homeassistant import config_entries
from homeassistant.const import CONF_PLATFORM, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    CONF_API_TYPE,
    CONF_API_TOKEN,
    CONF_CLIENT_API_URL,
    CONF_SENSORS,
    CONF_USERID,
    DEFAULT_API_TYPE,
    DEFAULT_CLIENT_API_URL,
    DEFAULT_SENSORS,
    API_TYPE_CLIENT,
    API_TYPE_BOTH,
    API_TYPE_PUBLIC,
)
from .services import setup_services

_LOGGER = logging.getLogger(__name__)

# List of platforms to support
PLATFORMS = ["sensor", "button"]

async def async_setup(hass: HomeAssistant, config):
    """Set up the WhatPulse component from YAML."""
    sensor_configs = [
        entry
        for entry in config.get("sensor", [])
        if entry.get(CONF_PLATFORM) == DOMAIN
    ]
    button_configs = [
        entry
        for entry in config.get("button", [])
        if entry.get(CONF_PLATFORM) == DOMAIN
    ]

    if not sensor_configs and not button_configs:
        return True

    _LOGGER.info(
        "Legacy WhatPulse YAML detected (sensor entries: %s, button entries: %s). Starting automatic import to config entry.",
        len(sensor_configs),
        len(button_configs),
    )

    if len(sensor_configs) > 1 or len(button_configs) > 1:
        _LOGGER.warning(
            "Multiple legacy WhatPulse YAML platform entries found; only the first sensor/button entry is auto-imported."
        )

    sensor_config = sensor_configs[0] if sensor_configs else {}
    button_config = button_configs[0] if button_configs else {}

    api_type = sensor_config.get(CONF_API_TYPE, DEFAULT_API_TYPE)
    if button_config and api_type == API_TYPE_PUBLIC:
        api_type = API_TYPE_BOTH
    elif not sensor_config and button_config:
        api_type = API_TYPE_CLIENT

    import_data = {
        CONF_API_TYPE: api_type,
        CONF_USERID: sensor_config.get(CONF_USERID, ""),
        CONF_USERNAME: sensor_config.get(CONF_USERNAME, ""),
        CONF_API_TOKEN: sensor_config.get(CONF_API_TOKEN, ""),
        CONF_CLIENT_API_URL: sensor_config.get(
            CONF_CLIENT_API_URL,
            button_config.get(CONF_CLIENT_API_URL, DEFAULT_CLIENT_API_URL),
        ),
        CONF_SENSORS: sensor_config.get(CONF_SENSORS, DEFAULT_SENSORS),
    }

    _LOGGER.debug(
        "Preparing WhatPulse YAML import (api_type=%s, userid_set=%s, username_set=%s, client_api_url=%s, sensors=%s)",
        import_data.get(CONF_API_TYPE),
        bool(import_data.get(CONF_USERID)),
        bool(import_data.get(CONF_USERNAME)),
        import_data.get(CONF_CLIENT_API_URL),
        len(import_data.get(CONF_SENSORS, [])),
    )

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=import_data,
        )
    )

    _LOGGER.info("Triggered WhatPulse YAML import flow.")

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
