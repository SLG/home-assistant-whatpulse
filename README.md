[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

# WhatPulse Component for Home Assistant

This is a custom component for Home Assistant (https://home-assistant.io) that provides sensors and controls for WhatPulse statistics and functionality, so you can create a dashboard of WhatPulse statistics and control the WhatPulse client from within Home Assistant.

## About

[WhatPulse](https://whatpulse.org/) is an application that measures your keyboard/mouse usage, down- & uploads, uptime, and more. This component queries the WhatPulse API for a configured user and gets the values for those statistics. This component supports both the public WhatPulse API for any user's stats and the Client API for real-time data from your local WhatPulse client.

## Installation

### HACS - Recommended
- Have [HACS](https://hacs.xyz) installed, this will allow you to easily manage and track updates.
- Search for 'WhatPulse'.
- Click Install below the found integration.
- Configure using the configuration instructions below.
- Restart Home Assistant.

### Manual installation
- Copy directory `custom_components/whatpulse` to your `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home Assistant.

## Configuration

### Basic Configuration

To use this component in your installation, add the following to your HA `configuration.yaml` file:

```yaml
# Example configuration.yaml entry with public API
sensor:
  - platform: whatpulse
    userid: your_user_id  # preferred over username
    api_type: public  # Options: public, client, both
    sensors:
      - Keys
      - Clicks
      - RankKeys
      - RankClicks
```

### Advanced Configuration

For more advanced usage including client API and buttons:

```yaml
# Full configuration example
sensor:
  - platform: whatpulse
    userid: "12345"          # Preferred over username
    username: an_user_name   # Used if userid is not provided
    api_type: client         # Options: public, client, both
    client_api_url: "http://192.168.1.100:3490"  # WhatPulse client API URL
    sensors:
      - Keys
      - Clicks
      - Download
      - Upload
      - UptimeSeconds
      - RealtimeKeys
      - RealtimeClicks
      - UnpulsedKeys

# Add button entities for client control
button:
  - platform: whatpulse
    client_api_url: "http://192.168.1.100:3490"
    api_type: both
```

### Configuration Options

#### Sensor Platform
- username (Optional): The username for the WhatPulse account
- userid (Optional, preferred): The numeric user ID for the WhatPulse account
- api_type (Optional, default: public): The API type to use - public, client, or both
- client_api_url (Optional, default: http://localhost:3490): URL for the client API
- sensors (Optional): List of sensors to enable (see Available Sensors below)

#### Button Platform
- client_api_url (Required): URL for the client API

#### Available Sensors

**Public API Sensors**
- Keys: Total number of keys pressed
- Clicks: Total number of mouse clicks
- Scrolls: Total number of mouse scrolls
- Download: Total download formatted (MB, GB, etc.)
- Upload: Total upload formatted (MB, GB, etc.)
- DownloadMB: Total download in megabytes
- UploadMB: Total upload in megabytes
- UptimeSeconds: Total computer uptime in seconds
- UptimeShort: Short formatted uptime string
- UptimeLong: Long formatted uptime string
- DistanceInMiles: Mouse cursor movement distance
- Pulses: Number of pulses sent
- AvKeysPerPulse: Average keys per pulse
- AvClicksPerPulse: Average clicks per pulse
- AvKPS: Average keys per second
- AvCPS: Average clicks per second
- RankKeys: Ranking position for keys
- RankClicks: Ranking position for clicks
- RankDownload: Ranking position for download
- RankUpload: Ranking position for upload
- RankUptime: Ranking position for uptime
- RankScrolls: Ranking position for scrolls
- RankDistance: Ranking position for mouse distance

**Client API Sensors**
- RealtimeKeys: Current keys per second
- RealtimeClicks: Current clicks per second
- RealtimeDownload: Current download speed
- RealtimeUpload: Current upload speed
- UnpulsedKeys: Keys since last pulse
- UnpulsedClicks: Clicks since last pulse
- UnpulsedScrolls: Scrolls since last pulse
- UnpulsedDownload: Download since last pulse
- UnpulsedUpload: Upload since last pulse
- UnpulsedUptime: Uptime since last pulse

#### Button Controls
When the client API is enabled, you'll have access to these buttons:

- WhatPulse Pulse: Trigger a manual pulse
- WhatPulse Open Client: Open the WhatPulse client window

#### Services
The integration provides the following services when the client API is enabled:

- Activate Profile: Activates a specific WhatPulse time tracking profile.

```yaml
service: whatpulse.activate_profile
data:
  profile_id: 1  # The numeric ID of the profile
  client_api_url: "http://192.168.1.100:3490"  # Optional override
```

### Setting Up the Client API
To use the Client API features, you need to:

1. Open WhatPulse client
2. Go to Settings > Client API
3. Enable "Enable Client API"
4. Set a port (default is 3490)
5. Add your Home Assistant IP to allowed IPs (or empty it to allow all)

Detailed instructions can be found in the [WhatPulse documentation](https://whatpulse.org/help/docs/software/settings/enabling-the-client-api).

### Automations Example

```yaml
# Example to activate gaming profile
automation:
  - alias: 'Gaming profile when Steam opens'
    trigger:
      - platform: state
        entity_id: sensor.steam_status
        to: 'online'
    action:
      - service: whatpulse.activate_profile
        data:
          profile_id: 2  # Your gaming profile ID
```