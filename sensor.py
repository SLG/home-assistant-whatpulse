"""Sensor for Whatpulse"""

from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_NAME,
    CONF_USERNAME
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

import requests
from xml.etree import ElementTree

DATA_URL = "http://api.whatpulse.org/user.php?user="

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Information provided by Whatpulse"

DEFAULT_NAME = "Whatpulse stats"

ICON = "mdi:podium-gold"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)

REFRESH_RATE = 120

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
})

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the Whatpulse sensor platform"""

    username = config.get(CONF_USERNAME)
    api = Whatpulse_API(username)
    async_add_devices([WhatpulseSensor(api)], True)

class Whatpulse_API(object):
    """ Interface class for the Greenchoice Boks API """

    def __init__(self, user, refresh_rate=REFRESH_RATE):
        """ Constructor """
        self._user = user
        self._data = {}
        self._last_refresh = None
        self._refresh_rate = refresh_rate

    def _update(self):
        """ Update the cache """
        current_time = int(time.time())
        last_refresh = 0 if self._last_refresh is None else self._last_refresh

        if current_time >= (last_refresh + self._refresh_rate):
            self._update_data()
            self._last_refresh = int(time.time())

    def _update_data(self):
        """ Retrieve data """
        data = self._request_update(DATA_URL + self._user)
        if data is False:
            print
            return
        _LOGGER.info(data)
        return data

    def _request_update(self, url):
        """ Perform a request to update information """
        response = requests.request("GET", url)

        if response.status_code != 200:
            _LOGGER.error("Unable to perform request " + str(response.content))
            return False

        return ElementTree.fromstring(response.content)

class WhatpulseSensor(Entity):
    """Representation of a Whatpulse sensor."""

    def __init__(self, api):
        """Initialize the Whatpulse sensor."""
        self._attributes = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "last_pulse": "",
            "pulses": 0,
            "clicks": 0,
            "download_mb": 0.0,
            "upload_mb": 0.0,
            "uptime_seconds": 0.0,
            "rank_keys": 0,
            "rank_clicks": 0,
            "rank_download": 0,
            "rank_upload": 0,
            "rank_upload": 0
        }
        self._state = None
        self._api = api

    @property
    def name(self):
        """Return the name of the sensor."""
        return DEFAULT_NAME

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return "Keys"

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def icon(self):
        """Icon to use in the frontend."""
        return ICON

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update device state."""
        data = self._api._update_data()

        self._attributes["last_pulse"] = data.find("LastPulse").text
        self._attributes["pulses"] = data.find("Pulses").text
        self._attributes["clicks"] = data.find("Clicks").text
        self._attributes["download_mb"] = data.find("DownloadMB").text
        self._attributes["upload_mb"] = data.find("UploadMB").text
        self._attributes["uptime_seconds"] = data.find("UptimeSeconds").text
        
        ranks = data.find("Ranks")
        self._attributes["rank_keys"] = ranks.find("Keys").text
        self._attributes["rank_clicks"] = ranks.find("Clicks").text
        self._attributes["rank_download"] = ranks.find("Download").text
        self._attributes["rank_upload"] = ranks.find("Upload").text
        self._attributes["rank_uptime"] = ranks.find("Uptime").text

        self._state = data.find("Keys").text

