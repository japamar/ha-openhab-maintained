# ha-openhab-maintained

Maintained fork of [kubawolanin/ha-openhab](https://github.com/kubawolanin/ha-openhab) for current Home Assistant versions.

This repository exists because the original integration uses several Home Assistant APIs that were removed or deprecated in recent releases. The current branch contains compatibility fixes tested with Home Assistant 2026 and openHAB 5.2.

## Current status

The integration is loading successfully and importing openHAB items into Home Assistant.

Compatibility changes currently include:

- migration from `async_forward_entry_setup()` to `async_forward_entry_setups()`
- current `device_tracker` source type API
- current light `ColorMode` API
- current media-player enums and feature flags
- fixes for blocking/synchronous openHAB calls used from Home Assistant async code
- corrected dimmer brightness conversion

Further work is planned around entity cleanup and disabling openHAB metadata/helper items by default.

## Installation with HACS

1. Open HACS.
2. Add this repository as a custom repository of type **Integration**:
   `https://github.com/japamar/ha-openhab-maintained`
3. Install **openHAB**.
4. Restart Home Assistant.
5. Add the **openHAB** integration from **Settings → Devices & services**.

## Manual installation

Copy:

`custom_components/openhab/`

to:

`/config/custom_components/openhab/`

and restart Home Assistant.

## Attribution

This project is based on the original [ha-openhab](https://github.com/kubawolanin/ha-openhab) integration by Kuba Wolanin (@kubawolanin).

The original project is distributed under the MIT License. The original copyright and license notice are preserved in this repository.

## License

MIT. See [LICENSE](LICENSE).
