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
- Add the integration via **Settings -> Devices & Services -> Add Integration -> WhatPulse**.
- Restart Home Assistant.

## ⚠️ Breaking Changes in v3.0

**Version 3.0 introduces breaking changes for the public API configuration:**

The WhatPulse public API has been updated to use authentication tokens. You'll need to:

1. **Get your API token**: Visit your WhatPulse dashboard to generate an API token (https://whatpulse.org/dashboard/my/api)
2. **Update your configuration**: Add `api_token`

**Old configuration:**
```yaml
sensor:
  - platform: whatpulse
    username: your_username
    api_type: public
```

**New configuration (v3.0+):**
```yaml
sensor:
  - platform: whatpulse
    username: your_username    # Either username or userid required
    userid: your_user_id       # Either username or userid required
    api_token: your_api_token
    api_type: public
```

## Configuration

### UI Setup (Config Flow)

This integration now supports Home Assistant's UI config flow. You no longer need to add YAML for normal setup.

1. Go to **Settings -> Devices & Services**.
2. Click **Add Integration**.
3. Search for **WhatPulse**.
4. Choose an API type:
   - `public`: WhatPulse cloud API (requires `api_token` + `username` or `userid`)
   - `client`: local WhatPulse client API only
   - `both`: combine public + local client data
5. Fill in the requested fields for the selected mode.

#### Public API values
- `userid` or `username`
- `api_token`

#### Client API values
- `client_api_url` (default: `http://localhost:3490`)

### Updating Existing Configuration

If you previously used YAML, the integration now attempts to auto-import your first legacy WhatPulse `sensor`/`button` platform configuration into a config entry on startup.

After Home Assistant starts:

1. Check **Settings -> Devices & Services** for the imported WhatPulse entry.
2. Verify entities are present and updating.
3. Remove old YAML blocks for `sensor:`, `button:`, and WhatPulse platform entries to avoid duplicate entities.

If you have multiple legacy WhatPulse YAML entries, only the first `sensor` and first `button` entry are auto-imported.

### Options Flow

After setup, you can update credentials/URL from:

**Settings -> Devices & Services -> WhatPulse -> Configure**

You can also select which sensor entities should be enabled from the same options screen.

### Legacy YAML (optional)

YAML examples are kept below for advanced/manual scenarios.

```yaml
# Example configuration.yaml entry with public API
sensor:
  - platform: whatpulse
    userid: your_user_id       # Either username or userid required
    api_token: your_api_token  # Required for public API
    api_type: public           # Options: public, client, both
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
    userid: "12345"          # Either username or userid required for public API
    api_token: "your_bearer_token"  # Required for public API
    username: an_user_name   # Alternative to userid
    api_type: both           # Options: public, client, both
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
- userid (Optional): The numeric user ID for the WhatPulse account (alternative to username)
- api_token (Required for public API): Your WhatPulse API bearer token
- api_type (Optional, default: public): The API type to use - public, client, or both
- client_api_url (Optional, default: http://localhost:3490): URL for the client API
- sensors (Optional): List of sensors to enable (see Available Sensors below)

**Note**: For public API, you must provide either `username` or `userid` along with `api_token`.

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
- UptimeShort: Short formatted uptime string (e.g., "6y 46w 1d 17h 44m")
- UptimeLong: Long formatted uptime string (e.g., "6 years, 46 weeks, 1 day, 17 hours, 44 minutes, 51 seconds")
- DistanceInMiles: Mouse cursor movement distance in miles
- Pulses: Number of pulses sent to WhatPulse
- AvKeysPerPulse: Average keys per pulse
- AvClicksPerPulse: Average clicks per pulse
- AvKPS: Average keys per second (calculated from total keys / uptime)
- AvCPS: Average clicks per second (calculated from total clicks / uptime)
- RankKeys: Global ranking position for keys
- RankClicks: Global ranking position for clicks
- RankDownload: Global ranking position for download
- RankUpload: Global ranking position for upload
- RankUptime: Global ranking position for uptime
- RankScrolls: Global ranking position for scrolls
- RankDistance: Global ranking position for mouse distance

**Client API Sensors** *(Requires WhatPulse client with API enabled)*
- RealtimeKeys: Current keys per second
- RealtimeClicks: Current clicks per second
- RealtimeDownload: Current download speed (formatted)
- RealtimeUpload: Current upload speed (formatted)
- UnpulsedKeys: Keys pressed since last pulse
- UnpulsedClicks: Clicks made since last pulse
- UnpulsedScrolls: Scrolls made since last pulse
- UnpulsedDownload: Bytes downloaded since last pulse
- UnpulsedUpload: Bytes uploaded since last pulse
- UnpulsedUptime: Uptime seconds since last pulse

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
