#!/usr/bin/env python3
"""carrierctl - control the WWAN carrier rev 0.3 (Sierra EM9291 / Telit FN990A28 M.2 cards) from the FRDM-IMX95 (or any Linux host on J801).

*** UNTESTED SKELETON. No carrier hardware exists yet. Review before running on a board with modules fitted. ***

Implements the procedures in docs/power-reset-sequencing.md.  Pin positions come from carrier_map.json, which is
GENERATED from the KiCad netlist by tools/gen_interface.py - never hard-code bit numbers here.

Two back-ends:
  --backend gpiod  (default if the pca953x driver owns the expanders, i.e. the DT overlay is applied)
                   uses libgpiod v2 Python bindings and the gpio-line-names from the overlay.
  --backend smbus  talks to the TCA6416A registers directly with smbus2 (no DT overlay; the i2c-dev
                   bus number is given with --bus).  Refuses to run if a kernel driver is bound to 0x20/0x21.
  --dry-run        smbus back-end against an in-memory fake expander; prints every register write.

Examples
  carrierctl.py --backend smbus --bus 3 init
  carrierctl.py status
  carrierctl.py slot on 1
  carrierctl.py slot cycle 2
  carrierctl.py hub-reset && carrierctl.py --bus 3 hub-attach
"""
import argparse, glob, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(HERE, 'carrier_map.json')

# ---------------- timings (seconds) - see docs/power-reset-sequencing.md section 3 for sources ----------------
# Union of Sierra EM92XX PTS Rev 5 [EM92] and Telit FN990 HDG Rev 3 [FN990] so one sequence works for either card in any slot.
T_PG_TIMEOUT = 0.050   # PWR_EN -> SLOTn_PG                         UNVERIFIED (engineering margin)
T_PERST_DELAY = 0.200  # SLOTn_PG (power valid) -> PCIE_EN=1        EM92 Table 4-8 T_pvpgl >= 150 ms; FN990 Fig. 4 UNVERIFIED
T_ENUM_FIRST = 1.0     # PERST# release -> first pci rescan          UNVERIFIED
T_ENUM_MAX = 10.0      # keep rescanning (1 s period) up to this     UNVERIFIED
T_SD_MAX = 5.0         # optional AT+CFUN=0 -> OK cap               UNVERIFIED for these cards (both shut down via FCPO#)
T_SHUTDOWN = 15.0      # FCPO# low -> remove power                   EM92 Table 4-8 T_pwr_off_seq max 12 s (+margin); FN990 Fig. 6 UNVERIFIED
                       #   (rev 0.3 has no PLA_S2_N / VREG_L6B_1P8 monitor - fixed wait, OI-27)
T_OFF = 1.0            # rail off -> rail on again                   UNVERIFIED (no active discharge on the 3.7 V bucks)
T_RESET_PULSE = 1.2    # RESET# low (emergency hardware reset)       FN990 6.2.3.1 > 1 s; EM92 Table 2-9 >= 450 ms
T_HUB_RST = 0.005      # HUB_RESET_N low (trstia + 1 ms RC)          USB5744 DS00001855J Table 10-7, unit VERIFY
T_HUB_STRAP = 0.010    # after HUB_RESET_N high (tcsh 1 ms + RC)     USB5744 Table 10-7
T_SLOT_STAGGER = 2.0   # between slots on `slot on all`              UNVERIFIED (inrush/peak-current spreading)

USB5744_ADDR = 0x2D    # VERIFY (Linux binding example)
USB5744_CMD_ATTACH = (0xAA, 0x0056)   # SMBus write-word; same as Linux onboard_usb_dev.c
# Qualcomm SDX65-class MHI endpoints (mhi_pci_generic): EM929x sub 18d7:0301, FN990 sub 1c5d:2010. 0x0309 = SDX72 (future cards).
MODEM_IDS = {('0x17cb', '0x0308'), ('0x17cb', '0x0309')}
SLOT_SWITCH_PORT = None  # filled from carrier_map.json: {slot: PI7C port number}

REG_IN, REG_OUT, REG_POL, REG_CFG = 0x00, 0x02, 0x04, 0x06


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def load_map():
    with open(MAP_PATH) as f:
        m = json.load(f)
    lines = {}
    for e in m['expanders']:
        for l in e['lines']:
            lines[l['name']] = dict(l, addr=e['addr'])
    return m, lines


# =================================== back-ends ===================================
class FakeBus:
    """In-memory TCA6416A pair for --dry-run.  PG inputs follow PWR_EN so sequencing logic can be exercised."""
    def __init__(self, lines):
        self.lines = lines
        self.regs = {a: {REG_IN: 0xFF, REG_IN + 1: 0xFF, REG_OUT: 0xFF, REG_OUT + 1: 0xFF,
                         REG_POL: 0, REG_POL + 1: 0, REG_CFG: 0xFF, REG_CFG + 1: 0xFF} for a in (0x20, 0x21)}

    def _update_inputs(self):
        for n in (1, 2, 3):
            en = self.lines[f'slot{n}-pwr-en']; pg = self.lines[f'slot{n}-pg']
            on = (self.regs[en['addr']][REG_OUT + en['port']] >> en['bit']) & 1 and \
                not (self.regs[en['addr']][REG_CFG + en['port']] >> en['bit']) & 1
            r = self.regs[pg['addr']]
            r[REG_IN + pg['port']] = (r[REG_IN + pg['port']] & ~(1 << pg['bit'])) | (int(on) << pg['bit'])

    def read_byte_data(self, addr, reg):
        self._update_inputs()
        return self.regs[addr][reg]

    def write_byte_data(self, addr, reg, val):
        print(f'    i2c w 0x{addr:02x} reg 0x{reg:02x} = 0x{val:02x}')
        self.regs[addr][reg] = val

    def write_word_data(self, addr, cmd, val):
        print(f'    i2c w-word 0x{addr:02x} cmd 0x{cmd:02x} = 0x{val:04x}')


class SmbusBackend:
    def __init__(self, bus, lines, dry_run=False, hub_only=False):
        self.lines = lines
        if dry_run:
            self.bus = FakeBus(lines)
        else:
            for a in (() if hub_only else (0x20, 0x21)):
                drv = glob.glob(f'/sys/bus/i2c/devices/{bus}-00{a:02x}/driver')
                if drv:
                    sys.exit(f'0x{a:02x} on i2c-{bus} is owned by a kernel driver; use --backend gpiod')
            from smbus2 import SMBus  # pip install smbus2
            self.bus = SMBus(bus)

    def init(self, m):
        """Safe init: OUTPUT registers first, then CONFIG (TCA6416A outputs default to 1)."""
        for e in m['expanders']:
            a = e['addr']
            for p in (0, 1):
                self.bus.write_byte_data(a, REG_OUT + p, e['init_output'][p])
            for p in (0, 1):
                self.bus.write_byte_data(a, REG_POL + p, 0x00)
            for p in (0, 1):
                self.bus.write_byte_data(a, REG_CFG + p, e['init_config'][p])

    def _check_configured(self, l):
        cfg = self.bus.read_byte_data(l['addr'], REG_CFG + l['port'])
        if l['dir'] == 'out' and (cfg >> l['bit']) & 1:
            sys.exit(f"{l['name']} is still an input - run `carrierctl.py init` first")

    def set(self, name, val):
        l = self.lines[name]
        assert l['dir'] == 'out', name
        self._check_configured(l)
        reg = REG_OUT + l['port']
        cur = self.bus.read_byte_data(l['addr'], reg)
        new = (cur | (1 << l['bit'])) if val else (cur & ~(1 << l['bit']) & 0xFF)
        if new != cur:
            self.bus.write_byte_data(l['addr'], reg, new)

    def get(self, name):
        l = self.lines[name]
        reg = (REG_IN if l['dir'] != 'out' else REG_OUT) + l['port']
        return (self.bus.read_byte_data(l['addr'], reg) >> l['bit']) & 1

    def hub_attach(self):
        cmd, val = USB5744_CMD_ATTACH
        self.bus.write_word_data(USB5744_ADDR, cmd, val)


class GpiodBackend:
    """libgpiod v2.  Lines are held requested for the life of the process.
    NOTE (UNVERIFIED): when the process exits the lines are released; pca953x keeps the last direction/value,
    but that is driver behaviour, not an ABI guarantee. For production use run as a daemon that keeps the request."""
    def __init__(self, lines, m):
        import gpiod  # libgpiod >= 2.0 python bindings
        from gpiod.line import Direction, Value
        self.gpiod, self.Direction, self.Value = gpiod, Direction, Value
        self.lines, self.reqs = lines, {}
        self.chips = {}
        for path in sorted(glob.glob('/dev/gpiochip*')):
            try:
                with gpiod.Chip(path) as c:
                    for name in lines:
                        try:
                            off = c.line_offset_from_id(name)
                        except (OSError, ValueError):
                            continue
                        self.chips[name] = (path, off)
            except OSError:
                pass
        missing = [n for n in lines if n not in self.chips and not n.startswith('spare')]
        if missing:
            sys.exit(f'gpio lines not found (overlay applied?): {", ".join(missing)}')

    def _req(self, name, out=None):
        if name in self.reqs:
            return self.reqs[name]
        path, off = self.chips[name]
        if out is None:
            s = self.gpiod.LineSettings(direction=self.Direction.INPUT)
        else:
            s = self.gpiod.LineSettings(direction=self.Direction.OUTPUT,
                                        output_value=self.Value.ACTIVE if out else self.Value.INACTIVE)
        r = self.gpiod.request_lines(path, consumer='carrierctl', config={off: s})
        self.reqs[name] = (r, off)
        return self.reqs[name]

    def init(self, m):
        # request every output with its documented safe value (value is applied before direction by the driver)
        for name, l in self.lines.items():
            if l['dir'] == 'out':
                self._req(name, out=l['init'])

    def set(self, name, val):
        if name not in self.reqs:
            self._req(name, out=val)
        r, off = self.reqs[name]
        r.set_value(off, self.Value.ACTIVE if val else self.Value.INACTIVE)

    def get(self, name):
        if self.lines[name]['dir'] == 'out' and name in self.reqs:
            r, off = self.reqs[name]
        else:
            r, off = self._req(name)
        return 1 if r.get_value(off) == self.Value.ACTIVE else 0

    def hub_attach(self):
        sys.exit('hub-attach needs raw I2C: run with --backend smbus --bus N (USB5744 is not owned by pca953x)')


# =================================== PCI / modem helpers ===================================
def pcie_port_number(bridge_dir):
    """Physical port number from Link Capabilities[31:24] of a switch downstream port (needs root)."""
    try:
        cfg = open(os.path.join(bridge_dir, 'config'), 'rb').read()
    except OSError:
        return None
    ptr = cfg[0x34] if len(cfg) > 0x34 else 0
    while ptr and ptr + 0x10 <= len(cfg):
        if cfg[ptr] == 0x10:  # PCI Express capability
            lnkcap = int.from_bytes(cfg[ptr + 0x0C:ptr + 0x10], 'little')
            return lnkcap >> 24
        ptr = cfg[ptr + 1]
    return None


def find_modems():
    """Return {switch_port: pci_device_dir} for Qualcomm MHI modem endpoints.  Port numbers via LNKCAP (VERIFY PI7C reports P1/P4/P5)."""
    out = {}
    for d in glob.glob('/sys/bus/pci/devices/*'):
        try:
            vid = open(f'{d}/vendor').read().strip(); did = open(f'{d}/device').read().strip()
        except OSError:
            continue
        if (vid, did) in MODEM_IDS:
            parent = os.path.dirname(os.path.realpath(d))
            out[pcie_port_number(parent)] = os.path.realpath(d)
    return out


def slot_pci_dev(slot):
    return find_modems().get(SLOT_SWITCH_PORT[slot])


def wwan_at_port(pcidev):
    for w in glob.glob(f'{pcidev}/wwan/wwan*'):
        n = os.path.basename(w)
        at = f'/dev/{n}at0'
        if os.path.exists(at):
            return at
    return None


def at_command(dev, cmd, timeout):
    """Minimal AT exchange on a wwan AT char device. Returns True on OK."""
    fd = os.open(dev, os.O_RDWR | os.O_NONBLOCK)
    try:
        os.write(fd, (cmd + '\r').encode())
        buf, t0 = b'', time.time()
        while time.time() - t0 < timeout:
            try:
                buf += os.read(fd, 256)
            except BlockingIOError:
                time.sleep(0.05)
            if b'OK' in buf:
                return True
            if b'ERROR' in buf:
                return False
        return False
    finally:
        os.close(fd)


def pci_rescan():
    log('pci rescan')
    open('/sys/bus/pci/rescan', 'w').write('1')


# =================================== procedures ===================================
class Carrier:
    def __init__(self, be, dry_run):
        self.be, self.dry = be, dry_run

    def sleep(self, t, why):
        log(f'  wait {t * 1000:.0f} ms ({why})')
        if not self.dry:
            time.sleep(t)

    def s(self, n, what, v):
        name = f'slot{n}-{what}'
        log(f'  {name} = {v}')
        self.be.set(name, v)

    def wait_enumeration(self, n):
        """rescan until the slot's endpoint appears (switch hot-plug is disabled, so no automatic detection)."""
        if self.dry:
            log(f'  (dry run) pci rescan every 1 s up to {T_ENUM_MAX:.0f} s'); return
        time.sleep(T_ENUM_FIRST)
        t0 = time.time()
        while True:
            pci_rescan()
            if slot_pci_dev(n):
                log(f'  slot {n}: endpoint {os.path.basename(slot_pci_dev(n))} present'); return
            if time.time() - t0 > T_ENUM_MAX:
                log(f'  slot {n}: no endpoint after {T_ENUM_MAX:.0f} s - check PERST#/REFCLK/pin 20 (power-reset-sequencing.md 5)'); return
            time.sleep(1.0)

    def slot_on(self, n, pcie=True):
        log(f'slot {n}: power on ({"PCIe" if pcie else "USB host interface"})')
        if self.be.get(f'slot{n}-pwr-en') and self.be.get(f'slot{n}-fcpo-n'):
            log('  already on (host interface is latched at boot - use `slot cycle` to change it)'); return
        # step 1: PERST# held, host interface selected BEFORE the card boots (pin 20 is sampled at boot), RESET# released
        self.s(n, 'pcie-en', 0); self.s(n, 'pcie-sel', 1 if pcie else 0)
        self.s(n, 'reset', 0); self.s(n, 'wdis', 0); self.s(n, 'fcpo-n', 0)
        # step 2: rail
        self.s(n, 'pwr-en', 1)
        t0 = time.time()
        while not self.be.get(f'slot{n}-pg'):
            if time.time() - t0 > T_PG_TIMEOUT:
                self.s(n, 'pwr-en', 0); self.s(n, 'pcie-sel', 1)
                sys.exit(f'slot {n}: SLOT{n}_PG did not assert within {T_PG_TIMEOUT * 1000:.0f} ms - rail turned off')
            time.sleep(0.002)
        t_pg = time.time()
        log(f'  SLOT{n}_PG ok (power valid)')
        # step 3: card boots
        self.s(n, 'fcpo-n', 1)
        if pcie:
            # step 4: PERST# release >= 150 ms after power valid (EM92 T_pvpgl)
            rem = T_PERST_DELAY - (0 if self.dry else time.time() - t_pg)
            self.sleep(max(rem, 0), 'T_pvpgl (power valid -> PERST#)')
            self.s(n, 'pcie-en', 1)
            self.wait_enumeration(n)
            log(f'slot {n}: up; card needs up to ~53 s (EM92 max) / >= 50 s (FN990) to reach MBIM/AT ready')
        else:
            log(f'slot {n}: up in USB mode (PERST# held); expect enumeration on hub port {n} '
                '(Sierra needs Rx08/Rx09 fitted - power-reset-sequencing.md 8)')

    def slot_off(self, n, graceful=True):
        log(f'slot {n}: power off ({"graceful" if graceful else "hard"})')
        dev = None if self.dry else slot_pci_dev(n)
        if graceful and dev:
            at = wwan_at_port(dev)
            if at:
                ok = at_command(at, 'AT+CFUN=0', T_SD_MAX)
                log(f'  AT+CFUN=0 on {at}: {"OK" if ok else "no OK - continuing with FCPO# shutdown"}')
            else:
                log('  no AT port found; relying on FCPO# graceful shutdown')
        if dev:
            log(f'  pci remove {dev}')
            open(os.path.join(dev, 'remove'), 'w').write('1')
        self.s(n, 'pcie-en', 0)                      # PERST# low first (EM92 T_rst_poff >= 0)
        self.s(n, 'fcpo-n', 0)                       # graceful shutdown trigger on both cards
        if graceful:
            self.sleep(T_SHUTDOWN, 'card shutdown (EM92 T_pwr_off_seq max 12 s; no PLA_S2_N monitor)')
        self.s(n, 'pwr-en', 0)
        self.s(n, 'pcie-sel', 1)                     # pin-20 FET on: no 1.8 V pull-up current into the unpowered card
        self.s(n, 'reset', 0); self.s(n, 'wdis', 0)
        log(f'slot {n}: off')

    def slot_cycle(self, n):
        was_on = self.be.get(f'slot{n}-pwr-en')
        pcie = bool(self.be.get(f'slot{n}-pcie-sel')) if was_on else True  # keep the current host interface
        self.slot_off(n)
        self.sleep(T_OFF, 'off time (rail bleed-down)')
        self.slot_on(n, pcie=pcie)

    def slot_warm_reset(self, n):
        """Emergency hardware reset (both vendors: only when the host interface is unresponsive)."""
        dev = None if self.dry else slot_pci_dev(n)
        if dev:
            open(os.path.join(dev, 'remove'), 'w').write('1')
        self.s(n, 'reset', 1); self.sleep(T_RESET_PULSE, 'RESET# pulse (FN990 > 1 s, EM92 >= 450 ms)'); self.s(n, 'reset', 0)
        if self.be.get(f'slot{n}-pcie-en'):
            self.wait_enumeration(n)

    def hub_reset(self):
        log('hub reset pulse')
        self.be.set('hub-reset-n', 0); self.sleep(T_HUB_RST, 'trstia + RC')
        self.be.set('hub-reset-n', 1); self.sleep(T_HUB_STRAP, 'tcsh + RC')

    def status(self, lines):
        rows = []
        for name in sorted(lines, key=lambda x: (lines[x]['addr'], lines[x]['port'], lines[x]['bit'])):
            l = lines[name]
            if l['dir'] == 'spare':
                continue
            try:
                v = self.be.get(name)
            except SystemExit:
                raise
            except Exception as e:  # noqa
                v = f'err {e}'
            rows.append(f"  0x{l['addr']:02x} P{l['port']}{l['bit']} {name:15s} {l['dir']:4s} = {v}")
        print('\n'.join(rows))
        if not self.dry:
            mods = find_modems()
            for slot, port in SLOT_SWITCH_PORT.items():
                dev = mods.get(port)
                sub = ''
            if dev:
                try:
                    sub = open(f'{dev}/subsystem_vendor').read().strip() + ':' + open(f'{dev}/subsystem_device').read().strip()
                except OSError:
                    pass
            print(f'  slot {slot} (switch P{port}): ' + (f'{os.path.basename(dev)} sub={sub} at={wwan_at_port(dev)}' if dev else 'no PCI device'))


def main():
    global SLOT_SWITCH_PORT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--backend', choices=['gpiod', 'smbus'], default='gpiod')
    ap.add_argument('--bus', type=int, help='i2c-dev bus number (smbus backend, hub-attach)')
    ap.add_argument('--dry-run', action='store_true', help='fake expander, print register writes, no sleeps/sysfs')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('init', help='safe expander init (outputs first, then direction)')
    sub.add_parser('status', help='all expander lines + modem PCI mapping')
    sp = sub.add_parser('slot'); sp.add_argument('action', choices=['on', 'on-usb', 'off', 'hard-off', 'cycle', 'warm-reset', 'rf-off', 'rf-on'])
    sp.add_argument('slot', help='1, 2, 3 or all')
    sub.add_parser('hub-reset'); sub.add_parser('hub-attach')
    lp = sub.add_parser('led'); lp.add_argument('n', type=int, choices=[1, 2]); lp.add_argument('state', choices=['on', 'off'])
    a = ap.parse_args()

    m, lines = load_map()
    SLOT_SWITCH_PORT = {p['slot']: p['switch_port'] for p in m['pcie']}
    if a.dry_run:
        a.backend = 'smbus'
    if a.backend == 'smbus' or a.cmd == 'hub-attach':
        if a.bus is None and not a.dry_run:
            sys.exit('--bus is required for the smbus backend / hub-attach')
        be = SmbusBackend(a.bus, lines, dry_run=a.dry_run, hub_only=(a.cmd == 'hub-attach' and a.backend == 'gpiod'))
    else:
        be = GpiodBackend(lines, m)
    c = Carrier(be, a.dry_run)

    if a.dry_run or a.cmd == 'init':
        log('expander init (output regs first)'); be.init(m)
    if a.cmd == 'status':
        c.status(lines)
    elif a.cmd == 'slot':
        slots = [1, 2, 3] if a.slot == 'all' else [int(a.slot)]
        for i, n in enumerate(slots):
            if a.action in ('on', 'on-usb'):
                if i:
                    c.sleep(T_SLOT_STAGGER, 'inter-slot stagger')
                c.slot_on(n, pcie=(a.action == 'on'))
            elif a.action == 'off':
                c.slot_off(n)
            elif a.action == 'hard-off':
                c.slot_off(n, graceful=False)
            elif a.action == 'cycle':
                c.slot_cycle(n)
            elif a.action == 'warm-reset':
                c.slot_warm_reset(n)
            elif a.action in ('rf-off', 'rf-on'):
                c.s(n, 'wdis', 1 if a.action == 'rf-off' else 0)
    elif a.cmd == 'hub-reset':
        c.hub_reset()
    elif a.cmd == 'hub-attach':
        log(f'USB5744 SMBus attach -> 0x{USB5744_ADDR:02x} (address VERIFY)'); be.hub_attach()
    elif a.cmd == 'led':
        be.set(f'user-led{a.n}', 1 if a.state == 'on' else 0)


if __name__ == '__main__':
    main()
