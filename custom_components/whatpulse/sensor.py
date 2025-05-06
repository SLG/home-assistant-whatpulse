"""Sensor for WhatPulse"""

from datetime import datetime
import json
import logging
import voluptuous as vol
import requests

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
)
from homeassistant.const import CONF_USERNAME
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

from .const import (
    API_TYPE_BOTH,
    API_TYPE_CLIENT,
    API_TYPE_PUBLIC,
    CONF_API_TYPE,
    CONF_CLIENT_API_URL,
    CONF_SENSORS,
    CONF_USERID,
    DEFAULT_API_TYPE,
    DEFAULT_CLIENT_API_URL,
    DEFAULT_SENSORS,
    MIN_TIME_BETWEEN_UPDATES_CLIENT,
    MIN_TIME_BETWEEN_UPDATES_PUBLIC,
    PUBLIC_API_URL,
    CLIENT_REFRESH_RATE,
    PUBLIC_REFRESH_RATE,
    SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)

# Schema for platform configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_USERID): cv.string,
    vol.Optional(CONF_API_TYPE, default=DEFAULT_API_TYPE): vol.In(
        [API_TYPE_PUBLIC, API_TYPE_CLIENT, API_TYPE_BOTH]
    ),
    vol.Optional(CONF_CLIENT_API_URL, default=DEFAULT_CLIENT_API_URL): cv.string,
    vol.Optional(CONF_SENSORS, default=DEFAULT_SENSORS): vol.All(
        cv.ensure_list, [vol.In(list(SENSOR_TYPES.keys()))]
    ),
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the WhatPulse sensor platform."""
    username = config.get(CONF_USERNAME)
    userid = config.get(CONF_USERID)
    api_type = config.get(CONF_API_TYPE)
    client_api_url = config.get(CONF_CLIENT_API_URL)
    sensor_types = config.get(CONF_SENSORS)

    # Require username or userid only for public API
    if api_type in [API_TYPE_PUBLIC, API_TYPE_BOTH] and not (username or userid):
        _LOGGER.error("Either username or userid must be provided when using public API")
        return False

    # Initialize API based on configuration
    api = WhatPulseAPI(username, userid, api_type, client_api_url)

    entities = []
    for sensor_type in sensor_types:
        sensor_info = SENSOR_TYPES[sensor_type]

        # Skip client-only sensors if not using client API
        if api_type == API_TYPE_PUBLIC and sensor_info["client_path"] is not None and sensor_info["client_path"][0] in ["realtime", "unpulsed"]:
            _LOGGER.warning(f"Skipping {sensor_type} as it requires client API access")
            continue

        entities.append(
            WhatPulseSensor(
                api,
                sensor_type,
                sensor_info["name"],
                sensor_info["rank_key"],
                sensor_info["icon"],
                sensor_info["unit"],
                sensor_info["client_path"],
            )
        )

    async_add_entities(entities, True)

class WhatPulseAPI:
    """Class to handle WhatPulse API calls."""

    def __init__(self, username=None, userid=None, api_type=DEFAULT_API_TYPE, client_api_url=DEFAULT_CLIENT_API_URL):
        """Initialize the API."""
        self._username = username
        self._userid = userid
        self._api_type = api_type
        self._client_api_url = client_api_url
        self._data = {}
        self._last_refresh_public = None
        self._last_refresh_client = None
        self._public_refresh_rate = PUBLIC_REFRESH_RATE
        self._client_refresh_rate = CLIENT_REFRESH_RATE

    def _update(self):
        """Update the WhatPulse data."""
        current_time = datetime.now().timestamp()

        # Update public API data if needed
        if self._api_type in [API_TYPE_PUBLIC, API_TYPE_BOTH]:
            last_refresh = 0 if self._last_refresh_public is None else self._last_refresh_public
            if current_time >= (last_refresh + self._public_refresh_rate):
                if self._update_public_data():
                    self._last_refresh_public = current_time

        # Update client API data if needed
        if self._api_type in [API_TYPE_CLIENT, API_TYPE_BOTH]:
            last_refresh = 0 if self._last_refresh_client is None else self._last_refresh_client
            if current_time >= (last_refresh + self._client_refresh_rate):
                if self._update_client_data():
                    self._last_refresh_client = current_time

        return self._data

    def _update_public_data(self):
        """Get the latest data from WhatPulse public API."""
        data = self._request_update_public()
        if data:
            self._data["public"] = data
            return True
        return False

    def _update_client_data(self):
        """Get the latest data from WhatPulse client API."""
        data = self._request_update_client()
        if data:
            self._data["client"] = data
            return True
        return False

    def _request_update_public(self):
        """Request update from public WhatPulse API."""
        # Build the URL based on what we have (userid preferred)
        url = PUBLIC_API_URL

        if self._userid:
            url += f"userid={self._userid}&format=json"
        elif self._username:
            url += f"user={self._username}&format=json"
        else:
            _LOGGER.error("No username or userid provided for WhatPulse public API")
            return False

        try:
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                _LOGGER.error(f"Unable to perform public API request: {response.content}")
                return False

            return response.json()

        except Exception as ex:
            _LOGGER.error(f"Error fetching WhatPulse public API data: {ex}")
            return False

    def _request_update_client(self):
        """Request update from WhatPulse client API."""
        url = f"{self._client_api_url}/v1/all-stats"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                _LOGGER.error(f"Unable to perform client API request: {response.content}")
                return False

            return response.json()

        except Exception as ex:
            _LOGGER.error(f"Error fetching WhatPulse client API data: {ex}")
            return False


class WhatPulseSensor(SensorEntity):
    """Representation of a WhatPulse sensor."""

    def __init__(self, api, sensor_type, name, rank_key, icon, unit, client_path=None):
        """Initialize the WhatPulse sensor."""
        self._api = api
        self._sensor_type = sensor_type
        self._name = name
        self._rank_key = rank_key
        self._icon = icon
        self._unit = unit
        self._client_path = client_path
        self._state = None
        self._attributes = {
            "last_pulse": None,
            "rank": None,
            "data_source": None,
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"WhatPulse {self._name}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        if self._api._userid:
            return f"whatpulse_{self._api._userid}_{self._sensor_type}"
        elif self._api._username:
            return f"whatpulse_{self._api._username}_{self._sensor_type}"
        else:
            # For client-only API without username/userid
            return f"whatpulse_client_{self._sensor_type}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    def _get_nested_value(self, data, path):
        """Get a value from a nested dictionary using a path list."""
        if not path or not data:
            return None

        temp = data
        for key in path:
            if key in temp:
                temp = temp[key]
            else:
                return None
        return temp

    def update(self):
        """Update data from WhatPulse API."""
        data = self._api._update()

        # Check if this is a rank sensor
        is_rank = SENSOR_TYPES[self._sensor_type].get("is_rank", False)

        # Try to get data from client API first if available and applicable
        if "client" in data and self._client_path:
            client_data = data["client"]
            value = self._get_nested_value(client_data, self._client_path)

            if value is not None:
                self._state = value
                self._attributes["data_source"] = "client"

                # For realtime stats, we don't need to check public API
                if self._client_path and self._client_path[0] == "realtime":
                    return

        # Fall back to public API data if available and no client data or realtime
        if "public" in data:
            public_data = data["public"]

            # Handle rank sensors specifically
            if is_rank:
                if "Ranks" in public_data and self._rank_key in public_data["Ranks"]:
                    self._state = public_data["Ranks"][self._rank_key]
                    self._attributes["data_source"] = "public"
                return

            # Update state if no client data or not a client-specific sensor
            if self._state is None and self._sensor_type in public_data:
                self._state = public_data[self._sensor_type]
                self._attributes["data_source"] = "public"

            # Update attributes
            if "LastPulse" in public_data:
                self._attributes["last_pulse"] = public_data["LastPulse"]

            if "LastPulseUnixTimestamp" in public_data:
                self._attributes["last_pulse_timestamp"] = public_data["LastPulseUnixTimestamp"]

            if self._rank_key and "Ranks" in public_data and self._rank_key in public_data["Ranks"]:
                self._attributes["rank"] = public_data["Ranks"][self._rank_key]

            # Add team information if available
            if "Team" in public_data:
                team = public_data["Team"]
                if "Name" in team:
                    self._attributes["team_name"] = team["Name"]

                if "Ranks" in team and self._rank_key and self._rank_key in team["Ranks"]:
                    self._attributes["team_rank"] = team["Ranks"][self._rank_key]