DOMAIN = "flowerhub"
DEFAULT_NAME = "Flowerhub"
PLATFORMS = ["sensor"]
SCAN_INTERVAL_MIN = 5
SCAN_INTERVAL_MAX = 86400

# Sensor availability staleness threshold multiplier
# Sensors are considered unavailable if no successful update occurred
# within this multiplier times the update interval
STALENESS_THRESHOLD_MULTIPLIER = 3.0
