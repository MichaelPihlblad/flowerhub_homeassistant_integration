# FlowerHub Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

This integration allows you to integrate your FlowerHub powergrid battery balancing system with Home Assistant, providing real-time monitoring of your system status.

## Features

- **Real-time Monitoring**: Get live data from your FlowerHub system
- **Sensor Entities**: Monitor inverter power, battery status, and system health
- **Automatic Updates**: Data refreshes periodically using Home Assistant's DataUpdateCoordinator
- **Secure Authentication**: Uses your FlowerHub credentials securely

## Installation

### Option 1: HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance.
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations
   - Click the three dots (⋮) → Custom repositories
   - Add `https://github.com/MichaelPihlblad/flowerhub_homeassistant_integration` as a repository URL
   - Select "Integration" as the category
3. Search for "FlowerHub" in HACS and install it.
4. Restart Home Assistant.

### Option 2: Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/MichaelPihlblad/flowerhub_homeassistant_integration/releases).
2. Extract the contents to `config/custom_components/flowerhub/` in your Home Assistant configuration directory.
3. Restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for "FlowerHub" and select it.
3. Enter your FlowerHub username and password.
4. Click **Submit** to complete the setup.

### Configuration Options

- **Username**: Your FlowerHub portal account username
- **Password**: Your FlowerHub portal account password

## Entities

The integration creates the following sensor entities:

- **FlowerHub System Status**: Overall system status
- **Inverter Power**: Current power output (W)
- **Battery SOC**: Battery state of charge (%)
- **Battery Energy**: Available battery energy (kWh)

## Requirements

- Home Assistant 2023.6.0 or later
- [FlowerHub portal](https://portal.flowerhub.se) account
- `flowerhub-portal-api-client` library (automatically installed)

## Troubleshooting

### Cannot Connect
- Verify your username and password are correct
- Check your internet connection
- Ensure your FlowerHub account is active

### Missing Library
- The integration requires the `flowerhub-portal-api-client` library
- If installation fails, try restarting Home Assistant after installation

### No Data
- Check that your FlowerHub system is online
- Verify the integration is configured correctly
- Check Home Assistant logs for errors

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- [GitHub Issues](https://github.com/MichaelPihlblad/flowerhub_homeassistant_integration/issues)
- [Home Assistant Community Forums](https://community.home-assistant.io/)