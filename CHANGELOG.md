# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-01-10
### Added
- Monthly uptime monitoring sensors for current month:
  - **Uptime Ratio Actual (Month)**: Percentage of uptime so far during the month, excluding periods with no data, future time for the rest of the month (main sensor)
  - **Uptime Ratio Total (Month)**: Percentage of uptime including no-data periods as downtime (regular sensor)
  - **Monthly Uptime**: Total uptime duration in seconds (diagnostic)
  - **Monthly Downtime**: Total downtime duration in seconds (diagnostic)
  - Uptime data refresh aligned with main polling interval (controlled by configuration)

### Changed
- Updated to `flowerhub-portal-api-client>=1.0.0,<2.0.0` for new uptime functionality
- Uptime statistics now refresh on every coordinator update (instead of fixed hourly schedule), controlled by user-configured polling interval


## [1.1.0] - 2026-01-08
### Added
- Connection status message as its own sensor
  - to be able to track historical changes of the message
- Possible to change credentials from integration config view
- Repair flow for entering new credentials for re-auth triggered during runtime if credentials invalid.
- Repair error notification without action triggered when failing to fetch data from API
- Range limit to config option for polling interval (5s-24hours)
### Fixed
- Integration config view crashing due to attribute error
- All auth errors triggered setup repair flow to enter new credentials
  - Only invalid credentials trigger the flow now
### Changed
- Default device name set to 'Flowerhub' with lowercase 'h' for name consistency, previously 'FlowerHub'

## [1.0.1] - 2026-01-08
Administrative change - remove filename from hacs.json since intended for HACS default standard integration

## [1.0.0] - 2026-01-06
First major release intended for HACS inclusion
### Added
- Diagnostics.py to easily download integration diagnostic data from Homeassistant
### Changed
- capital H to lowercase in manufacturer string and HACS name to align with Homeassistant brands domain name


## [0.5.0] - 2025-12-23
### Changed
- Require `flowerhub-portal-api-client>=0.4.0` and adapt coordinator to library breaking change, TypedDict responses instead of aiohttp objects.
- Test fixtures updated to return the new TypedDict structures
- Added explicit runtime validation for API result structures in coordinator.
- Enhanced logging around fetch/readout/auth flows to distinguish HTTP errors, parse issues, and missing data.


## [0.4.1] - 2025-12-20
### Fixed
- Removed test-only `sensor.flowerhub_status` , duplicate non-device-associated entity that was added by mistake.
- Improved handling of API errors

### Added
- Connection status sensor now has a `last_updated` attribute with timestamp to get sensor last updated info to reflect API data freshnes, alongside existing diagnostic sensor "Data Last updated".

### Changed
- Renamed device to "Flowerhub", earlier "Flowerhub system". To keep friendly name shorter in UI dashboard
- Set connection status sensor to unavailable when not updated successfuly and aged.

## [0.4.0] - 2025-12-19
### Changed
- Use short names for sensors in UI Dashboards (via `_attr_has_entity_name`).
- Refactored sensors to use `SensorEntityDescription` and a shared base class.
- Expanded coordinator data payload from client asset_info
- Updated device_info to prefer client-exposed properties over raw coordinator data

### Added
- Translation keys for all sensors; UI names now localized.
- Swedish translations (`sv.json`) for sensors and config/options flows.
- Six new diagnostic sensors: inverter manufacturer, battery stacks supported, battery manufacturer, battery max modules, and battery power capacity.
- Flowerhub portal link in config flow description with translations (English and Swedish)
- Integration type set to "hub" in manifest for proper Home Assistant UI categorization

## [0.3.0] - 2025-12-18

### Fixed
- Sensors stopped updating on token expiry
### Changed
- Optimized coordinator to run full readout once initially, then only fetch asset status data on continous polling.
- using official pypi release of flowerhub-portal-api-client python library and bumped mininum version to 0.3.2
### Added
- Added automatic re-authentication and retry on token expiry
- Improved logging.
- Increased test coverage
- Added HACS metadata (hacs.json)
- Added more info to documentation


## [0.2.0]
- Initial public release of the Flowerhub integration skeleton.
