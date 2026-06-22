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
    CONF_API_TOKEN,
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
    vol.Optional(CONF_API_TOKEN): cv.string,
    vol.Optional(CONF_API_TYPE, default=DEFAULT_API_TYPE): vol.In(
        [API_TYPE_PUBLIC, API_TYPE_CLIENT, API_TYPE_BOTH]
    ),
    vol.Optional(CONF_CLIENT_API_URL, default=DEFAULT_CLIENT_API_URL): cv.string,
    vol.Optional(CONF_SENSORS, default=DEFAULT_SENSORS): vol.All(
        cv.ensure_list, [vol.In(list(SENSOR_TYPES.keys()))]
    ),
})

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up WhatPulse sensors from a config entry."""
    data = {**config_entry.data, **config_entry.options}
    username = data.get(CONF_USERNAME)
    userid = data.get(CONF_USERID)
    api_token = data.get(CONF_API_TOKEN)
    api_type = data.get(CONF_API_TYPE, DEFAULT_API_TYPE)
    client_api_url = data.get(CONF_CLIENT_API_URL, DEFAULT_CLIENT_API_URL)
    sensor_types = data.get(CONF_SENSORS, DEFAULT_SENSORS)

    api = WhatPulseAPI(username, userid, api_token, api_type, client_api_url)

    entities = []
    for sensor_type in sensor_types:
        if sensor_type not in SENSOR_TYPES:
            continue
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


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the WhatPulse sensor platform."""
    username = config.get(CONF_USERNAME)
    userid = config.get(CONF_USERID)
    api_token = config.get(CONF_API_TOKEN)
    api_type = config.get(CONF_API_TYPE)
    client_api_url = config.get(CONF_CLIENT_API_URL)
    sensor_types = config.get(CONF_SENSORS)

    # Require username or userid and api_token for public API
    if api_type in [API_TYPE_PUBLIC, API_TYPE_BOTH]:
        if not (username or userid):
            _LOGGER.error("Either username or userid must be provided when using public API")
            return False
        if not api_token:
            _LOGGER.error("API token must be provided when using public API")
            return False

    # Initialize API based on configuration
    api = WhatPulseAPI(username, userid, api_token, api_type, client_api_url)

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

    def __init__(self, username=None, userid=None, api_token=None, api_type=DEFAULT_API_TYPE, client_api_url=DEFAULT_CLIENT_API_URL):
        """Initialize the API."""
        self._username = username
        self._userid = userid
        self._api_token = api_token
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
        if not (self._username or self._userid):
            _LOGGER.error("No username or userid provided for WhatPulse public API")
            return False

        if not self._api_token:
            _LOGGER.error("No API token provided for WhatPulse public API")
            return False

        # Use userid if available, otherwise use username
        identifier = self._userid if self._userid else self._username
        url = f"{PUBLIC_API_URL}{identifier}"
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Accept": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                _LOGGER.error(f"Unable to perform public API request: {response.status_code} - {response.content}")
                return False

            data = response.json()

            # Convert new API format to old API format for backward compatibility, not to break existing sensor configurations
            if "user" in data:
                return self._convert_new_api_format(data["user"])
            else:
                _LOGGER.error("Invalid API response format")
                return False

        except Exception as ex:
            _LOGGER.error(f"Error fetching WhatPulse public API data: {ex}")
            return False

    def _convert_new_api_format(self, user_data):
        """Convert new API format to old API format for backward compatibility."""
        try:
            # Map the new API structure to the old API structure
            converted_data = {
                "UserID": str(user_data["id"]),
                "AccountName": user_data["username"],
                "DateJoined": user_data["date_joined"][:10],
                "LastPulse": user_data["last_pulse_date"][:19].replace("T", " "),
                "Pulses": str(user_data["pulses"]),
                # Map totals
                "Keys": str(user_data["totals"]["keys"]),
                "Clicks": str(user_data["totals"]["clicks"]),
                "Scrolls": str(user_data["totals"]["scrolls"]),
                "DistanceInMiles": str(user_data["totals"]["distance_miles"]),
                # Add both raw MB values AND formatted values
                "DownloadMB": user_data["totals"]["download_mb"],
                "UploadMB": user_data["totals"]["upload_mb"],
                "Download": self._format_bytes(user_data["totals"]["download_mb"] * 1024 * 1024),
                "Upload": self._format_bytes(user_data["totals"]["upload_mb"] * 1024 * 1024),
                "UptimeSeconds": str(user_data["totals"]["uptime_seconds"]),
                "UptimeShort": self._format_uptime_short(user_data["totals"]["uptime_seconds"]),
                "UptimeLong": self._format_uptime_long(user_data["totals"]["uptime_seconds"]),
                # Calculate additional values that are missing from new API
                "AvKeysPerPulse": str(round(user_data["totals"]["keys"] / user_data["pulses"], 2)) if user_data["pulses"] > 0 else "0",
                "AvClicksPerPulse": str(round(user_data["totals"]["clicks"] / user_data["pulses"], 2)) if user_data["pulses"] > 0 else "0",
                # Calculate average per second values based on uptime
                "AvKPS": str(round(user_data["totals"]["keys"] / user_data["totals"]["uptime_seconds"], 4)) if user_data["totals"]["uptime_seconds"] > 0 else "0",
                "AvCPS": str(round(user_data["totals"]["clicks"] / user_data["totals"]["uptime_seconds"], 4)) if user_data["totals"]["uptime_seconds"] > 0 else "0",
                # Map ranks
                "Ranks": {
                    "Keys": str(user_data["ranks"]["keys"]),
                    "Clicks": str(user_data["ranks"]["clicks"]),
                    "Download": str(user_data["ranks"]["download"]),
                    "Upload": str(user_data["ranks"]["upload"]),
                    "Uptime": str(user_data["ranks"]["uptime"]),
                    "Scrolls": str(user_data["ranks"]["scrolls"]),
                    "Distance": str(user_data["ranks"]["distance"]),
                }
            }

            # Add team information if available
            if "team" in user_data and user_data["team"]:
                team = user_data["team"]
                converted_data["Team"] = {
                    "TeamID": str(team["id"]),
                    "Name": team["name"],
                    "Members": str(team["totals"]["members_count"]),
                    "Keys": str(team["totals"]["keys"]),
                    "Clicks": str(team["totals"]["clicks"]),
                    "Scrolls": str(team["totals"]["scrolls"]),
                    "DistanceInMiles": str(team["totals"]["distance_miles"]),
                    "DownloadMB": team["totals"]["download_mb"],
                    "UploadMB": team["totals"]["upload_mb"],
                    "UptimeSeconds": str(team["totals"]["uptime_seconds"]),
                    "Description": team["description"],
                    "DateFormed": team["date_formed"][:19].replace("T", " "),
                    "Ranks": {
                        "Keys": str(team["ranks"]["keys"]),
                        "Clicks": str(team["ranks"]["clicks"]),
                        "Download": str(team["ranks"]["download"]),
                        "Upload": str(team["ranks"]["upload"]),
                        "Uptime": str(team["ranks"]["uptime"]),
                        "Scrolls": str(team["ranks"]["scrolls"]),
                        "Distance": str(team["ranks"]["distance"]),
                    }
                }

            # Add last pulse information if available
            if "last_pulse" in user_data and user_data["last_pulse"]:
                # Convert ISO datetime to Unix timestamp
                import datetime as dt
                converted_data["LastPulseUnixTimestamp"] = str(int(dt.datetime.fromisoformat(user_data["last_pulse_date"].replace("Z", "+00:00")).timestamp()))

            return converted_data

        except Exception as ex:
            _LOGGER.error(f"Error converting new API format: {ex}")
            return False

    def _format_bytes(self, bytes_value):
        """Format bytes into human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    def _format_uptime_short(self, seconds):
        """Format uptime in short format."""
        years = seconds // 31536000  # 365 * 24 * 60 * 60
        seconds %= 31536000
        weeks = seconds // 604800    # 7 * 24 * 60 * 60
        seconds %= 604800
        days = seconds // 86400      # 24 * 60 * 60
        seconds %= 86400
        hours = seconds // 3600      # 60 * 60
        seconds %= 3600
        minutes = seconds // 60

        parts = []
        if years > 0:
            parts.append(f"{years}y")
        if weeks > 0:
            parts.append(f"{weeks}w")
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")

        # Show at least minutes if everything else is 0
        if not parts:
            parts.append("0m")

        return " ".join(parts)

    def _format_uptime_long(self, seconds):
        """Format uptime in long format."""
        years = seconds // 31536000  # 365 * 24 * 60 * 60
        seconds %= 31536000
        weeks = seconds // 604800    # 7 * 24 * 60 * 60
        seconds %= 604800
        days = seconds // 86400      # 24 * 60 * 60
        seconds %= 86400
        hours = seconds // 3600      # 60 * 60
        seconds %= 3600
        minutes = seconds // 60
        secs = seconds % 60

        parts = []
        if years > 0:
            parts.append(f"{years} year{'s' if years != 1 else ''}")
        if weeks > 0:
            parts.append(f"{weeks} week{'s' if weeks != 1 else ''}")
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if secs > 0:
            parts.append(f"{secs} second{'s' if secs != 1 else ''}")

        # Show at least 0 seconds if everything else is 0
        if not parts:
            parts.append("0 seconds")

        return ", ".join(parts)

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
        is_rank = self._sensor_type.startswith("Rank")

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

        # Fall back to public API data if available
        if "public" in data:
            public_data = data["public"]

            # Handle rank sensors specifically
            if is_rank:
                if "Ranks" in public_data and self._rank_key in public_data["Ranks"]:
                    self._state = public_data["Ranks"][self._rank_key]
                    self._attributes["data_source"] = "public"
                    self._attributes["rank"] = self._state  # Set rank attribute for rank sensors
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
