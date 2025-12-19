# Changelog

All notable changes to this project will be documented in this file.
## [0.3.1] - 2025-12-19
### Changed
- Use short names for sensors in UI Dashboards (via `_attr_has_entity_name`).
- Refactored sensors to use `SensorEntityDescription` and a shared base class.

### Added
- Translation keys for all sensors; UI names now localized.
- Swedish translations (`sv.json`) for sensors and config/options flows.

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
