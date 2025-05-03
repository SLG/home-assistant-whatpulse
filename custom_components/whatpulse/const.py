"""Constants for the WhatPulse integration."""

from datetime import timedelta

# API URLs
PUBLIC_API_URL = "https://api.whatpulse.org/user.php?"
DEFAULT_CLIENT_API_URL = "http://localhost:3490"  # Default client API URL

# Refresh rates
PUBLIC_REFRESH_RATE = 3600  # 60 minutes for public API
CLIENT_REFRESH_RATE = 30   # 30 seconds for client API
MIN_TIME_BETWEEN_UPDATES_PUBLIC = timedelta(seconds=PUBLIC_REFRESH_RATE)
MIN_TIME_BETWEEN_UPDATES_CLIENT = timedelta(seconds=CLIENT_REFRESH_RATE)

# Configuration constants
DOMAIN = "whatpulse"
CONF_USERID = "userid"
CONF_API_TYPE = "api_type"
CONF_SENSORS = "sensors"
CONF_CLIENT_API_URL = "client_api_url"

# API types
API_TYPE_PUBLIC = "public"
API_TYPE_CLIENT = "client"
API_TYPE_BOTH = "both"
DEFAULT_API_TYPE = API_TYPE_PUBLIC

# Available sensors with their attributes
SENSOR_TYPES = {
    # Common sensors - available in both public and client API
    "Keys": {
        "name": "Keys",
        "icon": "mdi:keyboard",
        "unit": "keys",
        "rank_key": "Keys",
        "client_path": ["account-totals", "keys"],
    },
    "Clicks": {
        "name": "Clicks",
        "icon": "mdi:mouse",
        "unit": "clicks",
        "rank_key": "Clicks",
        "client_path": ["account-totals", "clicks"],
    },
    "Scrolls": {
        "name": "Scrolls",
        "icon": "mdi:mouse-scroll-wheel",
        "unit": "scrolls",
        "rank_key": "Scrolls",
        "client_path": ["account-totals", "scrolls"],
    },
    "Download": {
        "name": "Download",
        "icon": "mdi:download",
        "unit": "",
        "rank_key": "Download",
        "client_path": None,
    },
    "DownloadMB": {
        "name": "Download",
        "icon": "mdi:download",
        "unit": "MB",
        "rank_key": "Download",
        "client_path": ["account-totals", "download"],
    },
    "Upload": {
        "name": "Upload",
        "icon": "mdi:upload",
        "unit": "",
        "rank_key": "Upload",
        "client_path": None,
    },
    "UploadMB": {
        "name": "Upload",
        "icon": "mdi:upload",
        "unit": "MB",
        "rank_key": "Upload",
        "client_path": ["account-totals", "upload"],
    },
    "UptimeSeconds": {
        "name": "Uptime",
        "icon": "mdi:clock-outline",
        "unit": "seconds",
        "rank_key": "Uptime",
        "client_path": ["account-totals", "uptime"],
    },
    "UptimeShort": {
        "name": "Uptime",
        "icon": "mdi:clock-outline",
        "unit": "",
        "rank_key": "Uptime",
        "client_path": None,
    },
    "UptimeLong": {
        "name": "Uptime",
        "icon": "mdi:clock-outline",
        "unit": "",
        "rank_key": "Uptime",
        "client_path": None,
    },
    "DistanceInMiles": {
        "name": "Distance",
        "icon": "mdi:map-marker-distance",
        "unit": "miles",
        "rank_key": "Distance",
        "client_path": ["account-totals", "distance_miles"],
    },
    "Pulses": {
        "name": "Pulses",
        "icon": "mdi:pulse",
        "unit": "pulses",
        "rank_key": None,
        "client_path": None,
    },
    "AvKeysPerPulse": {
        "name": "Average Keys Per Pulse",
        "icon": "mdi:keyboard-settings-outline",
        "unit": "keys/pulse",
        "rank_key": None,
        "client_path": None,
    },
    "AvClicksPerPulse": {
        "name": "Average Clicks Per Pulse",
        "icon": "mdi:gesture-tap",
        "unit": "clicks/pulse",
        "rank_key": None,
        "client_path": None,
    },
    "AvKPS": {
        "name": "Average Keys Per Second",
        "icon": "mdi:keyboard",
        "unit": "keys/sec",
        "rank_key": None,
        "client_path": None,
    },
    "AvCPS": {
        "name": "Average Clicks Per Second",
        "icon": "mdi:mouse",
        "unit": "clicks/sec",
        "rank_key": None,
        "client_path": None,
    },
    # Add these new sensor types to the SENSOR_TYPES dictionary
  "RankKeys": {
      "name": "Rank Keys",
      "icon": "mdi:trophy",
      "unit": "",
      "rank_key": "Keys",
      "client_path": ["account-totals", "ranks", "rank_keys"],
      "is_rank": True,
  },
  "RankClicks": {
      "name": "Rank Clicks",
      "icon": "mdi:trophy",
      "unit": "",
      "rank_key": "Clicks",
      "client_path": ["account-totals", "ranks", "rank_clicks"],
      "is_rank": True,
  },
  "RankDownload": {
      "name": "Rank Download",
      "icon": "mdi:trophy",
      "unit": "",
      "rank_key": "Download",
      "client_path": ["account-totals", "ranks", "rank_download"],
      "is_rank": True,
  },
  "RankUpload": {
      "name": "Rank Upload",
      "icon": "mdi:trophy",
      "unit": "",
      "rank_key": "Upload",
      "client_path": ["account-totals", "ranks", "rank_upload"],
      "is_rank": True,
  },
  "RankUptime": {
      "name": "Rank Uptime",
      "icon": "mdi:trophy",
      "unit": "",
      "rank_key": "Uptime",
      "client_path": ["account-totals", "ranks", "rank_uptime"],
      "is_rank": True,
  },
  "RankScrolls": {
      "name": "Rank Scrolls",
      "icon": "mdi:trophy",
      "unit": "",
      "rank_key": "Scrolls",
      "client_path": ["account-totals", "ranks", "rank_scrolls"],
      "is_rank": True,
  },
  "RankDistance": {
      "name": "Rank Distance",
      "icon": "mdi:trophy",
      "unit": "",
      "rank_key": "Distance",
      "client_path": ["account-totals", "ranks", "rank_distance"],
      "is_rank": True,
  },
    # Client-only sensors
    "UnpulsedKeys": {
        "name": "Unpulsed Keys",
        "icon": "mdi:keyboard",
        "unit": "keys",
        "rank_key": None,
        "client_path": ["unpulsed", "keys"],
    },
    "UnpulsedClicks": {
        "name": "Unpulsed Clicks",
        "icon": "mdi:mouse",
        "unit": "clicks",
        "rank_key": None,
        "client_path": ["unpulsed", "clicks"],
    },
    "UnpulsedScrolls": {
        "name": "Unpulsed Scrolls",
        "icon": "mdi:mouse-scroll-wheel",
        "unit": "scrolls",
        "rank_key": None,
        "client_path": ["unpulsed", "scrolls"],
    },
    "UnpulsedDownload": {
        "name": "Unpulsed Download",
        "icon": "mdi:download",
        "unit": "bytes",
        "rank_key": None,
        "client_path": ["unpulsed", "download"],
    },
    "UnpulsedUpload": {
        "name": "Unpulsed Upload",
        "icon": "mdi:upload",
        "unit": "bytes",
        "rank_key": None,
        "client_path": ["unpulsed", "upload"],
    },
    "UnpulsedUptime": {
        "name": "Unpulsed Uptime",
        "icon": "mdi:clock-outline",
        "unit": "seconds",
        "rank_key": None,
        "client_path": ["unpulsed", "uptime"],
    },
    "RealtimeKeys": {
        "name": "Realtime Keys",
        "icon": "mdi:keyboard",
        "unit": "keys/s",
        "rank_key": None,
        "client_path": ["realtime", "keys"],
    },
    "RealtimeClicks": {
        "name": "Realtime Clicks",
        "icon": "mdi:mouse",
        "unit": "clicks/s",
        "rank_key": None,
        "client_path": ["realtime", "clicks"],
    },
    "RealtimeDownload": {
        "name": "Realtime Download",
        "icon": "mdi:download",
        "unit": "",
        "rank_key": None,
        "client_path": ["realtime", "download"],
    },
    "RealtimeUpload": {
        "name": "Realtime Upload",
        "icon": "mdi:upload",
        "unit": "",
        "rank_key": None,
        "client_path": ["realtime", "upload"],
    },
}

DEFAULT_SENSORS = ["Keys", "Clicks", "Download", "Upload", "UptimeShort", "RealtimeDownload", "RealtimeUpload"]