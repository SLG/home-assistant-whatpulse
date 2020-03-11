"""Sensor for Whatpulse"""

from datetime import time
from datetime import datetime
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_USERNAME

import homeassistant.helpers.config_validation as cv

import requests
from xml.etree import ElementTree

from sensor_keys import WhatpulseKeysSensor
from sensor_clicks import WhatpulseClicksSensor
from sensor_download import WhatpulseDownloadSensor
from sensor_upload import WhatpulseUploadSensor
from sensor_uptime import WhatpulseUptimeSensor

DATA_URL = "http://api.whatpulse.org/user.php?user="

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Information provided by Whatpulse"

REFRESH_RATE = 120

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
})

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the Whatpulse sensor platform"""

    username = config.get(CONF_USERNAME)
    api = WhatpulseAPI(username)
    async_add_devices([
    WhatpulseKeysSensor(api),
    WhatpulseClicksSensor(api),
    WhatpulseDownloadSensor(api),
    WhatpulseUploadSensor(api),
    WhatpulseUptimeSensor(api),
    ], True)

class WhatpulseAPI(object):
    """ Interface class for the Whatpulse API """

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
            _LOGGER.info("Received no data")
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