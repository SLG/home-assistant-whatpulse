"""Sensor for Upload from Whatpulse"""
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from datetime import timedelta

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)

class WhatpulseUploadSensor(Entity):
    def __init__(self, api):
        self._attributes = {
            "Last Pulse": "",
            "Rank": 0,
        }
        self._state = None
        self._api = api

    @property
    def name(self):
        return "Whatpulse Upload Sensor"

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return "MB"

    @property
    def device_state_attributes(self):
        return self._attributes

    @property
    def icon(self):
        return "mdi:upload"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        data = self._api._update_data()

        self._attributes["Last Pulse"] = data.find("LastPulse").text
        self._attributes["Rank"] = data.find("Ranks").find("Upload").text

        self._state = data.find("UploadMB").text