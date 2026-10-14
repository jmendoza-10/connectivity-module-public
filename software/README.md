# software/

**Everything here is an UNTESTED skeleton** - written before any hardware exists. Review against
[docs/power-reset-sequencing.md](../docs/power-reset-sequencing.md) before running on a board with modules fitted.

| Path | What |
|---|---|
| `dts/frdm-imx95-wwan-carrier.dtso` | Overlay skeleton: two `ti,tca6416` nodes with gpio-line-names, optional USB5744 node (disabled). Placeholders for I2C bus / GPIOs (see open issue OI-01). Syntax-checked with dtc only |
| `dts/carrier-gpio-line-names.dtsi` | GENERATED line names (tools/gen_interface.py) |
| `tools/carrierctl.py` | CLI: expander init, status, slot on/off/cycle/warm-reset/rf-off, USB fallback power-on, hub reset/attach, user LEDs. Back-ends: libgpiod v2 (with the overlay) or smbus2 (raw registers). `--dry-run` uses a fake expander |
| `tools/carrier_map.json` | GENERATED pin map consumed by carrierctl.py |
| `tools/requirements.txt` | Python deps |

Only `--dry-run` has been executed (on a development box, no hardware).
