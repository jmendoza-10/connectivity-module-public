# Linux bring-up - FRDM-IMX95 + WWAN carrier rev 0.3 (Sierra EM9291 / Telit FN990A28)

Status: **plan, not executed.** No step below has been run on hardware. Items marked **VERIFY** need confirmation on the
target BSP; items marked **TODO** need a decision.

Related: [hw-sw-interface.md](hw-sw-interface.md) (pins/addresses, generated), [power-reset-sequencing.md](power-reset-sequencing.md),
[bringup-test-plan.md](bringup-test-plan.md), [open-issues.md](open-issues.md).

## 1. Kernel

Rev 0.3 cards (Sierra EM9291, Telit FN990A28) are Qualcomm SDX65-class modems. On PCIe they use the **MHI** stack
(`mhi_pci_generic` + `mhi_wwan_ctrl` + `mhi_wwan_mbim` / `mhi_net`); on USB they use `option` + `cdc_mbim` / `qmi_wwan`.
The MediaTek `mtk_t7xx` path of rev 0.2 (FM350-GL) is no longer used.

| Item | Requirement | Why |
|---|---|---|
| Base | NXP Linux Factory BSP for i.MX 95 (lf-6.12.y or newer) **or** mainline >= 6.12 with FRDM-IMX95 DTS | i.MX 95 PCIe (pci-imx6). **VERIFY** which tree has working PCIe on the FRDM M.2 Key-M |
| MHI PCI IDs | `drivers/bus/mhi/host/pci_generic.c` must contain: `PCI_DEVICE_SUB(QCOM, 0x0308, 0x1c5d, 0x2010)` "Telit FN990" and `PCI_DEVICE_SUB(QCOM, 0x0308, 0x18d7, 0x0301)` "EM929x (sdx65), use the same configuration as EM919x" (both present in mainline master, checked 2026-10-10) | Without a subsystem match the card still binds through the generic `PCI_DEVICE(QCOM, 0x0308)` (qcom-sdx65m) entry, but with the wrong channel set (no Telit DUN2/NMEA, different ring sizes). **VERIFY** the BSP kernel has both entries (`git log -S 0x0301 -- drivers/bus/mhi/host/pci_generic.c`) and backport if not |
| Telit FN990**A28** subsystem ID | assumed 1c5d:2010 like FN990; FE990A is 1c5d:2015 | **UNVERIFIED** for the A28 SKU - read `lspci -nnv` on the first card |
| Sierra EM9291 USB | `option.c` has `SIERRA_PRODUCT_EM9291 0x90e3` (serial ports, mainline) | USB fallback AT/diag ports |
| Telit FN990A USB | `option.c` 1bc7:1070-1079 (rmnet/MBIM/RNDIS/ECM compositions); `qmi_wwan.c` 1bc7:1070/1077 (rmnet) | USB fallback |

### Kernel config

```
# PCIe host + switch
CONFIG_PCI=y
CONFIG_PCI_IMX6_HOST=y            # i.MX 95 PCIe RC (pci-imx6); symbol name VERIFY on the BSP
CONFIG_PCIEPORTBUS=y
CONFIG_PCIEAER=y
CONFIG_PCIEASPM=y
CONFIG_HOTPLUG_PCI=y
CONFIG_HOTPLUG_PCI_PCIE=y
# WWAN over PCIe (Qualcomm MHI)
CONFIG_WWAN=y
CONFIG_MHI_BUS=m
CONFIG_MHI_BUS_PCI_GENERIC=m      # module mhi_pci_generic (EM929x, FN990)
CONFIG_MHI_WWAN_CTRL=m            # /dev/wwanNmbim0, wwanNat0 (DUN), wwanNqmi0 (EM9291), wwanNqcdm0, wwanNnmea0 (FN990)
CONFIG_MHI_WWAN_MBIM=m            # FN990 data: channel IP_HW0_MBIM -> MBIM netdev (mhi_wwan_mbim)
CONFIG_MHI_NET=m                  # EM929x data: channel IP_HW0 -> mhi_net raw-IP netdev (control via MBIM or QMI port)
# WWAN over USB (fallback / debug)
CONFIG_USB_NET_CDC_MBIM=m
CONFIG_USB_NET_QMI_WWAN=m         # FN990A rmnet compositions (1bc7:1070/1077)
CONFIG_USB_SERIAL=m
CONFIG_USB_SERIAL_OPTION=m        # AT/diag ports: EM9291 1199:90e3, FN990A 1bc7:107x
CONFIG_USB_SERIAL_QUALCOMM=m      # qcserial (QDL/firmware recovery modes)
CONFIG_USB_WDM=m
# USB host + hub
CONFIG_USB_XHCI_HCD=y
CONFIG_USB_DWC3=y                 # i.MX 95 USB3 controller (VERIFY glue on the BSP)
CONFIG_TYPEC=y                    # if the FRDM USB-C port is behind a TCPC (VERIFY board)
CONFIG_USB_ONBOARD_DEV=y
CONFIG_USB_ONBOARD_DEV_USB5744=y
# I2C + GPIO expanders
CONFIG_I2C_IMX_LPI2C=y
CONFIG_I2C_CHARDEV=y
CONFIG_GPIO_PCA953X=y
CONFIG_GPIO_PCA953X_IRQ=y
CONFIG_GPIO_CDEV=y
# Bonding experiments
CONFIG_MPTCP=y
CONFIG_MPTCP_IPV6=y
CONFIG_WIREGUARD=m
CONFIG_NET_SCH_FQ_CODEL=y
```

Quick checks after boot:

```sh
zcat /proc/config.gz | grep -E 'MHI|WWAN|PCA953X|ONBOARD_DEV|MPTCP|CDC_MBIM|QMI_WWAN'
modinfo mhi_pci_generic | grep -iE 'alias:.*0308'      # expect sv000018D7sd00000301 and sv00001C5Dsd00002010
```

## 2. Device tree

Skeleton overlay: [`software/dts/frdm-imx95-wwan-carrier.dtso`](../software/dts/frdm-imx95-wwan-carrier.dtso) (**UNTESTED**).
`gpio-line-names` come from the generated `carrier-gpio-line-names.dtsi`, so `gpioinfo` names match hw-sw-interface.md.

What the overlay must describe:

| Node | Content | Status |
|---|---|---|
| `&lpi2cX` | The LPI2C instance routed to the FRDM expansion header pins used for J801 SCL/SDA; `clock-frequency = <100000>` initially (USB5744 SMBus and PCA9306 are fine at 100 k; go to 400 k after T2 passes) | **TODO**: pick header pins and LPI2C instance; pinctrl must select the I2C function with open-drain |
| `gpio@20` | `compatible = "ti,tca6416"`, `reg = <0x20>`, `gpio-controller`, `#gpio-cells = <2>`, `interrupt-controller`, `#interrupt-cells = <2>`, `interrupts-extended = <&gpioN M IRQ_TYPE_LEVEL_LOW>` (shared EXP_INT_N), `reset-gpios = <&gpioN K GPIO_ACTIVE_LOW>` (EXP_RESET_N), `gpio-line-names` | U801 |
| `gpio@21` | same, `reg = <0x21>`; same interrupt line (wired-OR, open drain, level-low) | U802 |
| `usb-hub@2d` (optional) | `compatible = "microchip,usb5744"`, `reg = <0x2d>` on the same bus, plus the two `usb424,2744`/`usb424,5744` child nodes under the FRDM USB controller node with `i2c-bus = <&hub>`, `peer-hub` | Optional. Needs the exact USB controller node of the FRDM Type-C port. Until then use `carrierctl hub-attach`. Address **VERIFY** |
| PCIe | No change expected: the switch and modems are discovered by enumeration. Possibly `pci=realloc` / bridge window reservation, see section 6 | **VERIFY** |

Shared interrupt / reset notes (checked against mainline `drivers/gpio/gpio-pca953x.c`, Oct 2026):
- The driver requests its IRQ with `IRQF_ONESHOT | IRQF_SHARED`, so both expanders can list the same level-low interrupt.
  **VERIFY** the NXP BSP copy has the same flags.
- The driver takes `reset-gpios` with `devm_gpiod_get_optional(dev, "reset", GPIOD_OUT_LOW)`, i.e. an **exclusive** request that
  only de-asserts reset. Because EXP_RESET_N is shared by both expanders, put `reset-gpios` on **one** node only (U801 in the
  skeleton); a second exclusive request of the same line would fail with -EBUSY. Emergency all-off via EXP_RESET_N is then a
  userspace action on that SoC GPIO only if it is not claimed by the driver - see OI-13.

Pinctrl for EXP_INT_N should enable the SoC pull-up as well (belt and braces) and must be a 3.3 V pad. **VERIFY** FRDM header I/O voltage.

Build/apply (U-Boot or Yocto `KERNEL_DEVICETREE` overlay):

```sh
cpp -nostdinc -I include -I arch/arm64/boot/dts -undef -x assembler-with-cpp \
    software/dts/frdm-imx95-wwan-carrier.dtso | dtc -@ -I dts -O dtb -o frdm-imx95-wwan-carrier.dtbo -
# U-Boot: fdt apply, or Yocto: add to KERNEL_DEVICETREE / UBOOT overlays per NXP BSP docs
```

Expected after boot:

```sh
gpiodetect                      # two pca953x chips, 16 lines each
gpioinfo | grep -E 'slot|hub|pg-'   # names from carrier-gpio-line-names.dtsi
```

## 3. Userspace packages

| Package | Version | Notes |
|---|---|---|
| ModemManager | **>= 1.22** (1.24 preferred) | MHI/wwan-subsystem ports (mbim, at, qmi) for Qualcomm PCIe modems; Telit and Sierra plugins. **VERIFY** release notes for FN990 PCIe and EM929x |
| libmbim | >= 1.30 | MBIM control on `/dev/wwanNmbim0` (both cards) |
| libqmi | >= 1.34 | QMI control on EM9291 `/dev/wwanNqmi0`; firmware tools (`qmi-firmware-update`) |
| libgpiod | v2.x | carrierctl.py |
| python3-smbus2, i2c-tools, pciutils, usbutils | any | bring-up |
| mptcpd or `ip mptcp` (iproute2 >= 5.15) | - | bonding experiments |

### FCC lock

Some SDX65 cards ship FCC-locked when sold to laptop OEMs; module-maker retail SKUs normally are not. ModemManager ships unlock
helpers under `/usr/share/ModemManager/fcc-unlock.available.d/` named by VID:PID; check for `1c5d:2010`/`17cb:0308` and
`1199:90e3`/`18d7:0301` in the MM version used. **VERIFY** whether the purchased EM9291 / FN990A28 units are locked at all
(`mmcli -m N` shows "FCC locked" / radio refuses `--enable`). Only unlock modules you are authorised to operate.

### Firmware / carrier images

- Sierra EM9291: firmware + carrier PRI via `qmi-firmware-update` (QMI) or Sierra's Linux tools; PCIe firmware download uses the MHI
  SAHARA/FIREHOSE channels. **VERIFY** the procedure in the Sierra Linux integration guide before the first update.
- Telit FN990: firmware update per Telit "FN990 SW user guide" (not reviewed here). **VERIFY**.

## 4. Expected devices (PCIe mode, three cards)

| Thing | Expected | Check |
|---|---|---|
| PCI | 1 switch upstream (12d8:c008), downstream bridges, endpoints 17cb:0308 bound to `mhi-pci-generic` (subsystem 18d7:0301 = EM929x, 1c5d:2010 = FN990) | `lspci -tvnn`, `lspci -k -d 17cb:0308` |
| MHI | `/sys/bus/mhi/devices/mhi0..2` with channel devices (`mhi0_MBIM`, `mhi0_DUN`, ...) | `ls /sys/bus/mhi/devices` |
| WWAN control ports | per card: `wwanNmbim0`, `wwanNat0` (DUN), EM9291 also `wwanNqmi0`, FN990 also `wwanNat1` (DUN2) + `wwanNnmea0`, both `wwanNqcdm0` | `ls /dev/wwan*` |
| Netdevs | FN990: `wwanN` (mhi_wwan_mbim). EM9291: `mhi_hwip0`-style netdev from mhi_net | `ip link` |
| ModemManager | three modems, manufacturer Sierra Wireless / Telit | `mmcli -L` |
| GNSS | FN990: NMEA on `wwanNnmea0`; EM9291: via MBIM/QMI location services (MM `--location-*`) | `mmcli -m N --location-status` |
| GPIO | two `pca953x` gpiochips with names (now incl. `slotN-pcie-sel`) | `gpioinfo` |

Mapping wwanN to slots: never rely on wwanN order; use the PCI path (`readlink /sys/class/wwan/wwan0/device`) and the
downstream-port table in hw-sw-interface.md. `carrierctl.py status` prints the mapping (OI-11 for udev rules).

## 5. USB host-interface mode (per slot)

Rev 0.3 selects the card's host interface with **M.2 pin 20** (`SLOTn_PCIE_SEL`, sampled at boot) - see power-reset-sequencing.md
section 8. `carrierctl slot on-usb n` sets `PCIE_SEL=0` and keeps PERST# held, then powers the card.

| Card | Hardware needed | Expected on USB | Drivers |
|---|---|---|---|
| Telit FN990A28 | none (pin 20 floats high via the card's 10 k PU) | 1bc7:107x depending on `AT#USBCFG` composition (`AT#USBCFG`, **VERIFY**; e.g. 1071 = MBIM) | `cdc_mbim` + `option`, or `qmi_wwan` (1070/1077) |
| Sierra EM9291 | fit Rx08 (pin 20 -> +1V8) **and** Rx09 (pin 22 VBUS_SENSE -> slot rail). Never fit Rx09 with Telit | 1199:90e3 | `cdc_mbim` (class match) + `option` (AT/diag); `qmi_wwan` has no 90e3 entry in mainline - add a dynamic ID if an rmnet composition is used (**UNVERIFIED**) |

With pin 20 low (PCIe mode) the FN990 still exposes USB as **debug only** ([FN990] Table 29). The hub must have received the
SMBus attach first (`carrierctl hub-attach`), otherwise nothing appears on USB.

## 6. Known issues / risks

1. **Late-appearing endpoints behind a non-hot-plug switch.** At host boot the slots are off, so the kernel sizes bridge windows for
   empty downstream ports. After powering a slot and `echo 1 > /sys/bus/pci/rescan`, BAR assignment can fail ("BAR 0: no space").
   Options, in order of preference: (a) power the slots before the host enumerates (U-Boot `i2c` commands writing the expander per the
   power-up sequence, then boot Linux); (b) kernel cmdline `pci=realloc` (and, if hot-plug is strapped on in a later rev,
   `pci=hpmemsize=64M,hpbussize=4`); (c) remove the switch upstream port and rescan the root port. **VERIFY** in T4 (OI-12).
2. **MHI remove/rescan robustness.** Test 20 power-cycle loops per slot (T5.3). Recovery path: `modprobe -r mhi_wwan_mbim mhi_net
   mhi_wwan_ctrl mhi_pci_generic && modprobe mhi_pci_generic`. MHI firmware boot takes up to ~53 s (EM92 Table 4-8); do not treat a
   slow `mmcli -L` as a failure before then.
3. **ASPM / L1 substates through the switch.** If links flap or AER errors appear, test with `pcie_aspm=off` first.
4. **USB5744 waits forever in SOC_CFG** without the attach command (by design in SMBus mode). Symptom: no hub on `lsusb -t`.
5. **USB5744 supply order** (VDD33 before VDD12, unchanged in rev 0.3): pulse `HUB_RESET_N` after boot (OI-07).
6. **TCA6416A init order:** any tool that sets direction before value (e.g. `gpioset` on an unrequested line is fine; raw `i2cset 0x06`
   first is not) will power everything at once. Use carrierctl or the pca953x driver only.
7. **Shared expander IRQ/reset** (see section 2): IRQ sharing is supported by mainline pca953x; the reset line can be owned by one node only.
8. **Wrong MHI channel config** if the BSP lacks the EM929x / FN990 subsystem entries (card binds as generic qcom-sdx65m). Check `dmesg | grep mhi`.
9. **MM probing races**: ModemManager may probe AT ports while carrierctl is power-cycling a slot. Inhibit the modem
   (`mmcli -m N --inhibit` in a background shell) or stop MM during cycling tests.
