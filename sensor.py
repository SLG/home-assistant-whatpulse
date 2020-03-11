"""Sensor for Whatpulse"""

from datetime import time
from datetime import datetime
from datetime import timedelta

import logging
import voluptuous as vol
import requests

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_USERNAME
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

from xml.etree import ElementTree

DATA_URL = "http://api.whatpulse.org/user.php?user="

_LOGGER = logging.getLogger(__name__)

REFRESH_RATE = 120
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
})

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    username = config.get(CONF_USERNAME)
    api = WhatpulseAPI(username)
    async_add_devices([
        WhatpulseSensor(api, "Keys", "Keys", "mdi:keyboard"),
        WhatpulseSensor(api, "Clicks", "Clicks", "mdi:mouse"),
        WhatpulseSensor(api, "DownloadMB", "Download", "mdi:download"),
        WhatpulseSensor(api, "UploadMB", "Upload", "mdi:upload"),
        WhatpulseSensor(api, "UptimeSeconds", "Uptime", "mdi:clock"),
    ], True)

class WhatpulseAPI(object):
    def __init__(self, user, refresh_rate=REFRESH_RATE):
        self._user = user
        self._data = {}
        self._last_refresh = None
        self._refresh_rate = refresh_rate

    def _update(self):
        current_time = int(time.time())
        last_refresh = 0 if self._last_refresh is None else self._last_refresh

        if current_time >= (last_refresh + self._refresh_rate):
            self._update_data()
            self._last_refresh = int(time.time())

    def _update_data(self):
        data = self._request_update(DATA_URL + self._user)
        if data is False:
            _LOGGER.info("Received no data")
            return
        _LOGGER.info(data)
        return data

    def _request_update(self, url):
        response = requests.request("GET", url)

        if response.status_code != 200:
            _LOGGER.error("Unable to perform request " + str(response.content))
            return False

        return ElementTree.fromstring(response.content)


class WhatpulseSensor(Entity):
    def __init__(self, api, type, rank, icon):
        self._attributes = {
            "Last Pulse": "",
            "Rank": 0,
        }
        self._state = None
        self._api = api
        self._type = type
        self._rank = rank
        self._icon = icon

    @property
    def name(self):
        return "Whatpulse " + self._type + " Sensor"

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return self._type

    @property
    def device_state_attributes(self):
        return self._attributes

    @property
    def icon(self):
        return self._icon

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        data = self._api._update_data()

        self._attributes["Last Pulse"] = data.find("LastPulse").text
        self._attributes["Rank"] = data.find("Ranks").find(self._rank).text

        self._state = data.find(self._type).text
