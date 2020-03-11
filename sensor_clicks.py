"""Sensor for Keys from Whatpulse"""
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from datetime import timedelta

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=120)

def class WhatpulseClicksSensor(Entity):
    def __init__(self, api):
        self._attributes = {
            "Last Pulse": "",
            "Rank": 0,
        }
        self._state = None
        self._api = api

    @property
    def name(self):
        return "Whatpulse Clicks Sensor"

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return "Clicks"

    @property
    def device_state_attributes(self):
        return self._attributes

    @property
    def icon(self):
        return "mdi:mouse"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        data = self._api._update_data()

        self._attributes["Last Pulse"] = data.find("LastPulse").text
        self._attributes["Rank"] = data.find("Ranks").find("Clicks").text

        self._state = data.find("Clicks").text