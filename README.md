[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)  [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/slgeertsema/)

# Whatpulse Sensor Component
This is a Custom Component for Home-Assistant (https://home-assistant.io) that has sensors for various stats from Whatpulse.

## About
[Whatpulse](https://whatpulse.org/) is a application that measures your keyboard/mouse usage, down- & uploads and your uptime.
This component queries the Whatpulse API for a configured user and gets the values for those statistics.

## Installation

### HACS - Recommended
- Have [HACS](https://hacs.xyz) installed, this will allow you to easily manage and track updates.
- Search for 'Whatpulse'.
- Click Install below the found integration.
- Configure using the configuration instructions below.
- Restart Home-Assistant.

### Manual
- Copy directory `custom_components/whatpulse` to your `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

## Usage
To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry

sensor:
  - platform: whatpulse
    username: an_user_name
```

Configuration variables:

- **username** (*Required*): The username for which you want to get the statistics. This data is open, so you can get data for any user.

## Donation
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/slgeertsema/)