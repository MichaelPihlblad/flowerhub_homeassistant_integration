# Changelog

All notable changes to this project will be documented in this file.

## [0.4.1] - 2025-12-20
### Fixed
- Removed test-only `sensor.flowerhub_status` creation from the integration init to prevent a duplicate non-device-associated status entity.

### Changed


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
