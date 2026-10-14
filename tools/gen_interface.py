#!/usr/bin/env python3
"""Generate the hardware/software interface description from the KiCad netlist.

Inputs
  hardware/kicad/wwan-carrier.net   KiCad 9 netlist (refreshed by tools/regen_hardware.sh)
  SEMANTICS / ADDRESSES below       human knowledge the netlist cannot carry (meaning, polarity, addresses)

Outputs (all GENERATED - do not edit by hand)
  docs/hw-sw-interface.md                    the interface document
  software/tools/carrier_map.json            machine-readable map used by carrierctl.py
  software/dts/carrier-gpio-line-names.dtsi  gpio-line-names for the device-tree overlay

Everything that *can* be read from the netlist is read from it (expander pin -> net, pull resistors and
therefore reset defaults, what each line drives, I2C bus members, PCIe/USB port mapping, LEDs, test points,
host-header pinout).  The script fails loudly if the netlist no longer matches the semantic table, so a
schematic change cannot silently desynchronise the docs.

Usage:  python3 tools/gen_interface.py [--check]
  --check   regenerate into memory and exit 1 if any generated file differs from the committed one.
"""
import json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
NETLIST = os.path.join(ROOT, 'hardware/kicad/wwan-carrier.net')
OUT_MD = os.path.join(ROOT, 'docs/hw-sw-interface.md')
OUT_JSON = os.path.join(ROOT, 'software/tools/carrier_map.json')
OUT_DTSI = os.path.join(ROOT, 'software/dts/carrier-gpio-line-names.dtsi')
RAILS = {'+12V', '+3V3', '+0V95', '+1V8', '+1V2', '+3V7_S1', '+3V7_S2', '+3V7_S3', 'GND'}

# ----------------------------------------------------------------------------------------------
# Human-maintained semantics.  Keys are net base names ({n} = slot number 1..3).
# dir: out = expander drives it, in = expander reads it, spare = unused.
# active: logic level that means "asserted" for the function in `meaning`.
# safe: value firmware should write to the output register BEFORE switching the pin to output.
# ----------------------------------------------------------------------------------------------
SEMANTICS = {
    'SLOT{n}_PWR_EN':  dict(dir='out', active='high', safe=0, line='slot{n}-pwr-en',
                            meaning='Enable for slot {n} 3.7 V buck (LM61460 EN). 1 = slot rail on.'),
    'SLOT{n}_FCPO_N':  dict(dir='out', active='low', safe=0, line='slot{n}-fcpo-n',
                            meaning='M.2 FULL_CARD_POWER_OFF# (module pin 6), driven directly. 0 = module held off, 1 = module allowed to run. '
                                    'Drive 0 before removing +3V7 (avoid back-powering the module from the expander).'),
    'SLOT{n}_RESET':   dict(dir='out', active='high', safe=0, line='slot{n}-reset',
                            meaning='Gate of 2N7002 that pulls module RESET# (pin 67) low (open drain only - EM92 RESET_N / FN990 SYS_RESIN_N forbid pull-ups). '
                                    '1 = module held in reset. Pulse >= 1 s (FN990 needs > 1 s, EM92 >= 450 ms); emergency use only.'),
    'SLOT{n}_WDIS':    dict(dir='out', active='high', safe=0, line='slot{n}-wdis',
                            meaning='Gate of 2N7002 that pulls W_DISABLE1# (pin 8) low. 1 = radio disabled (RF off).'),
    'SLOT{n}_PCIE_EN': dict(dir='out', active='high', safe=0, line='slot{n}-pcie-en',
                            meaning='Gates host PERST# into slot {n} (SN74LVC1G08 AND). 0 = slot PERST# held asserted (default during power-up; release >= 150 ms '
                                    'after the slot rail is valid, EM92 T_pvpgl). Does NOT select the host interface - see SLOT{n}_PCIE_SEL. '
                                    'Jumper JUMPER (fitted) forces 0 regardless of the expander.'),
    'SLOT{n}_PCIE_SEL': dict(dir='out', active='high', safe=1, line='slot{n}-pcie-sel',
                            meaning='Gate of 2N7002 on M.2 pin 20 (rev 0.3). 1 = pin 20 LOW = PCIe host interface (Telit FN990 USB_PCIE_SWITCH low; '
                                    'Sierra EM92 PCIE_DIS low). 0 = pin 20 released: FN990 boots USB-only (internal 10k PU); EM92 boots USB only if the '
                                    'DNP 10k pin-20 pull-up to +1V8 is fitted. Sampled at module boot: set before FCPO# goes high. 10k PU = PCIe by default.'),
    'HUB_RESET_N':     dict(dir='out', active='low', safe=1, line='hub-reset-n',
                            meaning='USB5744 RESET_N. 0 = hub held in reset (standby). Hub straps re-latch on the rising edge.'),
    'SLOT{n}_PG':      dict(dir='in', active='high', line='slot{n}-pg',
                            meaning='Slot {n} 3.7 V buck PGOOD (open drain). 1 = rail in regulation.'),
    'SLOT{n}_WAKE_N':  dict(dir='in', active='low', line='slot{n}-wake-n',
                            meaning='M.2 PEWAKE# (module pin 54). 0 = module requests wake. Not routed to the PCIe switch.'),
    'PG_3V3':          dict(dir='in', active='high', line='pg-3v3',
                            meaning='+3V3 system buck PGOOD. Also enables the +0V95/+1V8/+1V2 regulators (hardware sequencing).'),
    'PG_0V95':         dict(dir='in', active='high', line='pg-0v95', meaning='+0V95 (PCIe switch core) PGOOD.'),
    'PG_1V8':          dict(dir='in', active='high', line='pg-1v8', meaning='+1V8 (PCIe switch I/O, EEPROM) PGOOD.'),
    'PG_1V2':          dict(dir='in', active='high', line='pg-1v2', meaning='+1V2 (USB5744 core) PGOOD.'),
    'USER_LED{n}':     dict(dir='out', active='high', safe=0, line='user-led{n}', meaning='User LED {n} (yellow, 1 k to LED to GND). 1 = on.'),
    'EXP_SPARE{n}':    dict(dir='spare', active='-', line='spare{n}', meaning='Spare expander pin, brought to a test point only.'),
}

# I2C addresses: what the netlist cannot tell us.  `src` = citation, `verify` = not yet confirmed on hardware.
ADDRESSES = {
    'TCA6416A': dict(addr=None, src='TI SCPS194F Table 8-3: ADDR=L -> 0x20, ADDR=H -> 0x21 (derived from the ADDR pin net)', verify=False),
    'USB5744': dict(addr=0x2D, src='Linux DT binding microchip,usb5744.yaml example (usb-hub@2d); not stated in DS00001855J text', verify=True),
    'PI7C9X3G606GP': dict(addr=0x6F, src='Diodes DS43484 Rev 5-2 sec. I2C: default 1101111b (0x6F), programmable at cfg offset 318h. '
                                          'The same section\'s example tables show 68h - confirm with i2cdetect', verify=True),
}
# PI7C9X3G606GP lane -> port in PORTCFG[2:0]=101 (6-port/6-lane), DS43484 Table 5-4 (as captured in the schematic note)
PI7C_LANE_TO_PORT = {0: 0, 1: 1, 2: 4, 3: 5, 4: 6, 5: 7}
SLOT_CONN = {1: 'J401', 2: 'J501', 3: 'J601'}
# Expander pins whose nets are unnamed in the schematic (KiCad auto names).  Each alias is checked against the
# netlist: `expect` must be found on the net (directly or one resistor away) or the generator aborts.
PIN_ALIASES = {
    ('U802', 'P12'): dict(name='USER_LED1', expect='D808'),
    ('U802', 'P13'): dict(name='USER_LED2', expect='D809'),
}

# ----------------------------------------------------------------------------------------------
def parse_sexpr(text):
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack = [[]]
    for t in tok:
        if t == '(':
            stack.append([])
        elif t == ')':
            e = stack.pop(); stack[-1].append(e)
        else:
            stack[-1].append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return stack[0][0]

def find(node, key):
    return [e for e in node if isinstance(e, list) and e and e[0] == key]

def first(node, key, default=None):
    r = find(node, key)
    return r[0] if r else default

class Netlist:
    def __init__(self, path):
        root = parse_sexpr(open(path).read())
        self.comps = {}
        for c in find(first(root, 'components'), 'comp'):
            ref = first(c, 'ref')[1]
            lib = first(c, 'libsource')
            fields = {}
            fl = first(c, 'fields')
            if fl:
                for f in find(fl, 'field'):
                    fields[f[1][1]] = f[2] if len(f) > 2 else ''
            props = {p[1][1]: (p[2][1] if len(p) > 2 else '') for p in find(c, 'property')}
            self.comps[ref] = dict(ref=ref, value=first(c, 'value')[1], part=first(lib, 'part')[1], lib=first(lib, 'lib')[1],
                                   fields=fields, dnp='dnp' in props, sheet=props.get('Sheetfile', ''))
        self.nets = {}
        self.pin_net = {}
        for n in find(first(root, 'nets'), 'net'):
            full = first(n, 'name')[1]
            base = full.split('/')[-1]
            nodes = []
            for nd in find(n, 'node'):
                d = {k[0]: k[1] for k in nd[1:]}
                nodes.append(d)
                self.pin_net[(d['ref'], d['pin'])] = base
            self.nets.setdefault(base, []).extend(nodes)

    def by_part(self, part):
        return sorted([c for c in self.comps.values() if c['part'] == part], key=lambda c: natkey(c['ref']))

    def pins_of(self, ref):
        return [(nd, net) for net, nds in self.nets.items() for nd in nds if nd['ref'] == ref]

    def two_pin_other(self, ref, net):
        nets = [self.pin_net.get((ref, p)) for p in ('1', '2')]
        if net not in nets: return None
        return nets[1] if nets[0] == net else nets[0]

    def pulls(self, net, depth=1, via=None):
        """Resistors from `net` to a rail; follows one series resistor (e.g. 1k into a pulled node)."""
        out = []
        for nd in self.nets.get(net, []):
            c = self.comps[nd['ref']]
            if c['part'] != 'R' or c['dnp']:
                continue
            other = self.two_pin_other(c['ref'], net)
            if other in ('+3V3', '+1V8', '+3V7_S1', '+3V7_S2', '+3V7_S3', '+12V'):
                out.append(dict(kind='pull-up', ref=c['ref'], value=c['value'], to=other, via=via))
            elif other == 'GND':
                out.append(dict(kind='pull-down', ref=c['ref'], value=c['value'], to='GND', via=via))
            elif depth > 0 and other and other not in RAILS:
                out += self.pulls(other, depth - 1, via=f"{c['ref']} ({c['value']}) -> {other}")
        return out

    def loads(self, net, exclude=()):
        res = []
        for nd in self.nets.get(net, []):
            if nd['ref'] in exclude: continue
            c = self.comps[nd['ref']]
            fn = nd.get('pinfunction', nd['pin'])
            res.append(f"{nd['ref']}.{fn} ({c['value']})")
        return sorted(res, key=natkey)

# Header nets that KiCad leaves auto-named (no label at the header).  Checked: the pin must exist.
HEADER_ALIASES = {('J801', '5'): 'EXP_INT_N', ('J801', '6'): 'EXP_RESET_N', ('J801', '8'): 'CARRIER_3V3_SENSE'}

def display_name(nl, net):
    """Human name for a net: the label if it has one, else a test-point value or header alias."""
    if not net or not net.startswith('Net-('):
        return net
    for (ref, pin), alias in HEADER_ALIASES.items():
        if nl.pin_net.get((ref, pin)) == net:
            return alias
    tps = [nl.comps[nd['ref']]['value'] for nd in nl.nets.get(net, []) if nl.comps[nd['ref']]['part'] == 'TestPoint']
    tps = [v for v in tps if not v.startswith('TP')]
    return tps[0] if tps else net

def logical_net_any(nl, net):
    for (ref, pname), a in PIN_ALIASES.items():
        for nd in nl.nets.get(net, []):
            if nd['ref'] == ref and nd.get('pinfunction') == pname:
                return a['name']
    return net

def logical_name(nl, ref, pname, net):
    a = PIN_ALIASES.get((ref, pname))
    if a:
        reach = {nd['ref'] for nd in nl.nets[net]}
        for r in list(reach):
            if nl.comps[r]['part'] == 'R':
                o = nl.two_pin_other(r, net)
                reach |= {nd['ref'] for nd in nl.nets.get(o, [])}
        if a['expect'] not in reach:
            raise SystemExit(f"{ref} {pname}: alias {a['name']} expects {a['expect']} on net {net} - netlist changed?")
        return a['name']
    tps = [nl.comps[nd['ref']]['value'] for nd in nl.nets[net] if nl.comps[nd['ref']]['part'] == 'TestPoint']
    tps = [v for v in tps if not v.startswith('TP')]
    if tps:
        return tps[0]
    return net

def natkey(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', str(s))]

def sem_for(net):
    for k, v in SEMANTICS.items():
        pat = '^' + re.escape(k).replace(r'\{n\}', r'(\d)') + '$'
        m = re.match(pat, net)
        if m:
            n = m.group(1) if m.groups() else ''
            d = {kk: (vv.format(n=n) if isinstance(vv, str) else vv) for kk, vv in v.items()}
            return d
    return None

# ----------------------------------------------------------------------------------------------
def build(nl):
    model = dict(expanders=[], i2c=[], pcie=[], usb=[], leds=[], tps=[], header=[], verify=[], warnings=[])
    # ---------------- expanders ----------------
    for c in nl.by_part('TCA6416A'):
        ref = c['ref']
        addr_net = nl.pin_net[(ref, '21')]
        addr = {'GND': 0x20, '+3V3': 0x21}.get(addr_net)
        if addr is None:
            raise SystemExit(f'{ref}: ADDR pin on unexpected net {addr_net}')
        lines = []
        for i in range(16):
            port, bit = divmod(i, 8)
            pin = str(4 + i) if port == 0 else str(13 + bit)
            net = nl.pin_net.get((ref, pin), 'NC')
            phys_net = net
            if net.startswith('Net-('):
                net = logical_name(nl, ref, f'P{port}{bit}', net)
            sem = sem_for(net)
            if sem is None:
                raise SystemExit(f'{ref} P{port}{bit} on net {net}: no SEMANTICS entry - update tools/gen_interface.py')
            pulls = nl.pulls(phys_net)
            if pulls:
                p = pulls[0]
                lvl = 1 if p['kind'] == 'pull-up' else 0
                how = f"{p['kind']} {p['ref']} {p['value']} to {p['to']}" + (f" via {p['via']}" if p['via'] else '')
            else:
                lvl = None
                how = 'no pull (floating while expander pin is an input)'
            loads = nl.loads(phys_net, exclude=(ref,))
            if pulls and pulls[0]['via']:
                vnet = pulls[0]['via'].split('-> ')[-1]
                loads += [x for x in nl.loads(vnet) if not x.startswith(pulls[0]['via'].split(' ')[0] + '.')]
                jp = [x.split('.')[0] for x in nl.loads(vnet) if x.startswith('JP')]
                sem = dict(sem, meaning=sem['meaning'].replace('JUMPER', ' / '.join(jp) or '?'))
            # sanity: an output's documented safe value should equal the hardware default
            if sem['dir'] == 'out' and lvl is not None and sem.get('safe') is not None and lvl != sem['safe']:
                model['warnings'].append(f'{ref} P{port}{bit} {net}: board default {lvl} != documented safe value {sem["safe"]}')
            lines.append(dict(ref=ref, addr=addr, port=port, bit=bit, pin=int(pin), name=f'P{port}{bit}', net=net, dir=sem['dir'],
                              active=sem['active'], meaning=sem['meaning'], line_name=sem['line'], safe=sem.get('safe'),
                              reset_level=lvl, reset_how=how, loads=loads))
        cfg = [0xFF, 0xFF]; outv = [0xFF, 0xFF]
        for l in lines:
            if l['dir'] == 'out':
                cfg[l['port']] &= ~(1 << l['bit']) & 0xFF
                if not l['safe']:
                    outv[l['port']] &= ~(1 << l['bit']) & 0xFF
        model['expanders'].append(dict(ref=ref, addr=addr, addr_net=addr_net, lines=lines, int_net=display_name(nl, nl.pin_net[(ref, '1')]),
                                       reset_net=display_name(nl, nl.pin_net[(ref, '3')]), cfg=cfg, out=outv))
    # ---------------- I2C ----------------
    for bus in ('I2C_SCL',):
        members = set(nd['ref'] for nd in nl.nets[bus])
        for ref in sorted(members, key=natkey):
            c = nl.comps[ref]
            if c['part'] == 'TCA6416A':
                e = [x for x in model['expanders'] if x['ref'] == ref][0]
                model['i2c'].append(dict(ref=ref, part=c['part'], addr=e['addr'], bus='host I2C (3.3 V)',
                                         note=f"ADDR pin on {e['addr_net']} - " + ADDRESSES['TCA6416A']['src'], verify=False))
            elif c['part'] in ADDRESSES:
                a = ADDRESSES[c['part']]
                model['i2c'].append(dict(ref=ref, part=c['part'], addr=a['addr'], bus='host I2C (3.3 V)', note=a['src'], verify=a['verify']))
            elif c['part'].startswith('PCA9306'):
                # follow through the level translator
                for nd in nl.nets[nl.pin_net[(ref, '3')]]:
                    cc = nl.comps[nd['ref']]
                    if cc['part'] in ADDRESSES:
                        a = ADDRESSES[cc['part']]
                        model['i2c'].append(dict(ref=cc['ref'], part=cc['part'], addr=a['addr'], bus=f'host I2C via {ref} PCA9306 (1.8 V side)',
                                                 note=a['src'], verify=a['verify']))
    for c in nl.by_part('HD3SS3220'):
        addr_net = nl.pin_net.get((c['ref'], '22'), '')
        if addr_net.startswith('unconnected'):
            model['i2c'].append(dict(ref=c['ref'], part='HD3SS3220', addr=None, bus='-',
                                     note='ADDR pin unconnected -> GPIO mode, I2C not used (TI SLLSEN5)', verify=False))
    pull_i2c = []
    for net in ('I2C_SCL', 'I2C_SDA'):
        for nd in nl.nets[net]:
            c = nl.comps[nd['ref']]
            if c['part'] == 'R':
                pull_i2c.append(f"{c['ref']} {c['value']} to {nl.two_pin_other(c['ref'], net)}" + (' (DNP)' if c['dnp'] else ''))
    model['i2c_pullups'] = pull_i2c
    # ---------------- PCIe ----------------
    sw = nl.by_part('PI7C9X3G606GP')[0]['ref']
    for n, j in SLOT_CONN.items():
        def jnet(fn):
            for nd, net in nl.pins_of(j):
                if nd.get('pinfunction') == fn: return net
        tx = jnet('PETp0')
        lane = [int(re.search(r'PERP(\d)', nd['pinfunction']).group(1)) for nd in nl.nets[tx] if nd['ref'] == sw][0]
        clk = jnet('CLKREQ#')
        cport = [int(re.search(r'CLKREQ_L(\d)', nd['pinfunction']).group(1)) for nd in nl.nets[clk] if nd['ref'] == sw][0]
        rck = jnet('REFCLKP')
        # REFCLK goes through a 0R: find it
        rport = None
        for nd in nl.nets[rck]:
            c = nl.comps[nd['ref']]
            if c['part'] == 'R' and c['value'] == '0':
                other = nl.two_pin_other(c['ref'], rck)
                for nd2 in nl.nets[other]:
                    if nd2['ref'] == sw:
                        rport = int(re.search(r'REFCLKOP(\d)', nd2['pinfunction']).group(1))
        port = PI7C_LANE_TO_PORT[lane]
        if not (port == cport == rport):
            raise SystemExit(f'slot {n}: PCIe port mismatch lane{lane}->P{port}, CLKREQ P{cport}, REFCLK P{rport}')
        perst = jnet('PERST#')
        model['pcie'].append(dict(slot=n, conn=j, lane=lane, port=port, clkreq=display_name(nl, clk), perst=display_name(nl, perst),
                                  perst_src=nl.loads(perst, exclude=(j,))))
    # ---------------- USB ----------------
    hub = nl.by_part('USB5744')[0]['ref']
    for n, j in SLOT_CONN.items():
        d = {}
        for fn in ('USB_D+', 'USB3_TX+', 'USB3_RX+'):
            net = [net for nd, net in nl.pins_of(j) if nd.get('pinfunction') == fn][0]
            hubpins = [nd['pinfunction'] for nd in nl.nets[net] if nd['ref'] == hub]
            if not hubpins:  # through AC cap
                for nd in nl.nets[net]:
                    c = nl.comps[nd['ref']]
                    if c['part'] == 'C':
                        other = nl.two_pin_other(c['ref'], net)
                        hubpins = [nd2['pinfunction'] for nd2 in nl.nets[other] if nd2['ref'] == hub]
                        if hubpins: hubpins = [hubpins[0] + f' (via {c["ref"]} {c["value"]})']
            d[fn] = hubpins[0] if hubpins else '?'
        port = int(re.search(r'(\d)', d['USB_D+'].split('/')[0][-1]).group(1))
        model['usb'].append(dict(slot=n, conn=j, port=port, pins=d))
    # ---------------- LEDs ----------------
    for c in sorted(nl.comps.values(), key=lambda c: natkey(c['ref'])):
        if c['part'] == 'LED':
            a = nl.pin_net.get((c['ref'], '2')); k = nl.pin_net.get((c['ref'], '1'))
            drv = ''
            kn = {nd['ref']: nd for nd in nl.nets.get(k, [])} if k not in RAILS else {}
            for r, nd in kn.items():
                part = nl.comps[r]['part']
                if part == '2N7002':
                    g = display_name(nl, nl.pin_net.get((r, '1')))
                    drv = f'on when `{g}` = 1 ({r} 2N7002 low-side switch)'
                elif part == 'PI7C9X3G606GP':
                    pf = nd.get('pinfunction', '')
                    drv = (f'switch {pf} (port P{pf[-1]}): off = no link, 1 Hz blink = 2.5 GT/s, 2 Hz blink = 5 GT/s, '
                           f'steady on = 8 GT/s (DS43484 pin table)')
                elif r.startswith('J') and nd.get('pinfunction') == 'LED1#':
                    drv = f'module LED1# ({r} pin 10, open drain): status pattern set by module firmware'
            if not drv and k == 'GND' and a:
                for nd in nl.nets.get(a, []):
                    if nl.comps[nd['ref']]['part'] == 'R':
                        o = nl.two_pin_other(nd['ref'], a)
                        ex = [n2 for n2 in nl.nets.get(o, []) if nl.comps[n2['ref']]['part'] == 'TCA6416A']
                        if ex:
                            al = PIN_ALIASES.get((ex[0]['ref'], ex[0]['pinfunction']), {}).get('name', o)
                            drv = f"on when `{al}` = 1 ({ex[0]['ref']} {ex[0]['pinfunction']} via {nd['ref']} {nl.comps[nd['ref']]['value']})"
                        elif o in RAILS:
                            drv = f'on whenever `{o}` is present'
            a_src = ''
            for nd in nl.nets.get(a, []):
                if nl.comps[nd['ref']]['part'] == 'R':
                    a_src = f"{display_name(nl, logical_net_any(nl, nl.two_pin_other(nd['ref'], a)))} via {nd['ref']} {nl.comps[nd['ref']]['value']}"
            model['leds'].append(dict(ref=c['ref'], color=c['value'], anode=a_src or a, cathode=display_name(nl, k), meaning=drv, sheet=c['sheet']))
        if c['part'] == 'TestPoint':
            model['tps'].append(dict(ref=c['ref'], net=nl.pin_net.get((c['ref'], '1')), label=c['value'], sheet=c['sheet']))
    # ---------------- host header ----------------
    hdr = 'J801'
    for p in range(1, 11):
        net = nl.pin_net.get((hdr, str(p)), 'NC')
        if net.startswith('unconnected'): net = 'NC'
        net = display_name(nl, net)
        extra = ''
        if net == 'CARRIER_3V3_SENSE':
            extra = '1 k from +3V3: reads high when the carrier +3V3 rail is up'
        elif net in ('I2C_SCL', 'I2C_SDA'):
            extra = 'host I2C, 3.3 V. Bus pull-ups 10 k on the hub sheet (SMBus strap), 4.7 k DNP here'
        elif net == 'EXP_INT_N':
            extra = 'open-drain wired-OR INT# of both TCA6416A, 10 k pull-up; connect to a host GPIO with IRQ'
        elif net == 'EXP_RESET_N':
            extra = 'RESET# of both TCA6416A, 10 k pull-up; host GPIO, active low'
        model['header'].append(dict(pin=p, net=net, note=extra))
    # ---------------- VERIFY fields ----------------
    for c in sorted(nl.comps.values(), key=lambda c: natkey(c['ref'])):
        for k, v in c['fields'].items():
            if 'VERIFY' in str(v) or k in ('FP_VERIFY', 'FP_TODO'):
                model['verify'].append(dict(ref=c['ref'], value=c['value'], field=k, text=v))
    return model

# ----------------------------------------------------------------------------------------------
def hx(v): return '-' if v is None else f'0x{v:02X}'

def render_md(m):
    L = []
    w = L.append
    w('<!-- GENERATED by tools/gen_interface.py from hardware/kicad/wwan-carrier.net - DO NOT EDIT BY HAND. -->')
    w('# Hardware / software interface - WWAN carrier rev 0.2')
    w('')
    w('Generated from the KiCad netlist plus the semantic table in `tools/gen_interface.py`. Rerun `python3 tools/gen_interface.py` '
      '(or `tools/regen_hardware.sh`) after any schematic change; CI runs `--check`.')
    w('')
    w('Legend: **VERIFY** = not yet confirmed on hardware or against a primary source. Nothing in this document has been bench-tested '
      '(no boards exist yet).')
    w('')
    if m['warnings']:
        w('> **Generator warnings:**')
        for x in m['warnings']: w(f'> - {x}')
        w('')
    # I2C
    w('## 1. I2C devices')
    w('')
    w('One host I2C bus enters on the host header J801 (3.3 V). The PCIe switch sits behind a PCA9306 level translator (1.8 V side).')
    w('')
    w('| Ref | Device | 7-bit address | Bus | Source / note | Status |')
    w('|---|---|---|---|---|---|')
    for d in m['i2c']:
        w(f"| {d['ref']} | {d['part']} | {hx(d['addr'])} | {d['bus']} | {d['note']} | {'**VERIFY**' if d['verify'] else 'from netlist + datasheet'} |")
    w('')
    w('Bus pull-ups found in the netlist: ' + '; '.join(m['i2c_pullups']) + '.')
    w('')
    w('Notes:')
    w('- USB5744 is strapped for **SMBus slave mode** (10 k pull-ups on SMCLK/SMDAT). In that mode the hub waits **indefinitely** in its SOC_CFG stage '
      'until the host finishes configuration (DS00001855J sec. 5.1.5). Linux `onboard_usb_dev` (`CONFIG_USB_ONBOARD_DEV_USB5744`) sends the '
      'attach command (SMBus write-word, command 0xAA, data 0x0056); `carrierctl.py hub-attach` does the same from userspace. '
      'Until this happens **no slot enumerates over USB**. **VERIFY** on hardware.')
    w('- PI7C9X3G606GP I2C is for configuration/debug only; normal operation needs no I2C traffic (transparent switch).')
    w('')
    # expanders
    w('## 2. TCA6416A GPIO expanders')
    w('')
    for e in m['expanders']:
        w(f"### {e['ref']} - address {hx(e['addr'])} (ADDR -> {e['addr_net']})")
        w('')
        w(f"INT# -> `{e['int_net']}`, RESET# -> `{e['reset_net']}`. Register init (write output regs 0x02/0x03 **first**, then config 0x06/0x07): "
          f"output = `0x{e['out'][0]:02X} 0x{e['out'][1]:02X}`, config = `0x{e['cfg'][0]:02X} 0x{e['cfg'][1]:02X}` (1 = input).")
        w('')
        w('| Port.bit | Pin | Net | Dir | Active | Board default (expander pins are inputs after POR) | Init value | Meaning | Connects to | gpio-line-name |')
        w('|---|---|---|---|---|---|---|---|---|---|')
        for l in e['lines']:
            dflt = ('?' if l['reset_level'] is None else str(l['reset_level'])) + f" ({l['reset_how']})"
            init = '-' if l['dir'] != 'out' else str(l['safe'])
            w(f"| P{l['port']}.{l['bit']} | {l['pin']} | `{l['net']}` | {l['dir']} | {l['active']} | {dflt} | {init} | {l['meaning']} | "
              f"{', '.join(l['loads'])} | `{l['line_name']}` |")
        w('')
    w('TCA6416A facts used above (TI SCPS194F): after power-on reset or RESET# all pins are inputs (config regs 0x06/0x07 = 0xFF) and the '
      'output registers 0x02/0x03 default to 0xFF (sec. 8.6.3). If firmware writes the config register first, every output would '
      'immediately drive **1** (slots powered, FCPO# released, modules in reset, RF disabled). Always write the output registers first. '
      'The expander has no internal pull resistors, so the "board default" column is set by the carrier resistors only.')
    w('')
    # PCIe
    w('## 3. PCIe topology')
    w('')
    w('Host: FRDM-IMX95 M.2 Key-M (PCIe Gen3 x1) -> ADT-Link M41 riser cable -> carrier x1 edge fingers -> PI7C9X3G606GP upstream port 0. '
      'Switch strapped PORTCFG[2:0]=101 (6-port/6-lane), CKMODE=0 (host REFCLK), hot-plug disabled (HOT_PLUG_EN_L=1).')
    w('')
    w('| Slot | Connector | Switch lane | Switch port | REFCLK out | CLKREQ# net | PERST# source |')
    w('|---|---|---|---|---|---|---|')
    for p in m['pcie']:
        w(f"| {p['slot']} | {p['conn']} | {p['lane']} | P{p['port']} | REFCLKO{p['port']} | `{p['clkreq']}` | `{p['perst']}` = host PERST# AND SLOT{p['slot']}_PCIE_EN ({', '.join(p['perst_src'])}) |")
    w('')
    w('Ports P6/P7 are unused (lanes 4/5 NC).')
    w('')
    w('Expected `lspci -tvnn` (bus numbers illustrative; **VERIFY** downstream device numbers and whether unused ports P6/P7 still appear as bridges):')
    w('')
    w('```')
    w('-[0000:00]---00.0-[01-ff]--  i.MX 95 root port')
    w('    \\-[01]---00.0  Pericom/Diodes PI7C9X3G606GP upstream port   [12d8:c008]')
    w('        +-[02] DSP P1 --- 00.0  Qualcomm SDX65 MHI (Telit FN990A28)  [17cb:0308 sub 1c5d:2010]  driver mhi-pci-generic')
    w('        +-[03] DSP P4 --- 00.0  Qualcomm SDX65 MHI (Sierra EM9291)   [17cb:0308 sub 18d7:0301]  driver mhi-pci-generic')
    w('        +-[04] DSP P5 --- 00.0  (any of the above / future NTN M.2 card)')
    w('        +-[05] DSP P6 (no link)')
    w('        \\-[06] DSP P7 (no link)')
    w('```')
    w('')
    w('IDs: switch 12d8:c008 from DS43484 sec. 9.3.1/9.3.2 (vendor 12D8h, device C008h). Module IDs from mainline '
      '`drivers/bus/mhi/host/pci_generic.c` (entries "Telit FN990" 1c5d:2010 and "EM929x (sdx65)" 18d7:0301); the slot assignment above is only an example. '
      '**VERIFY** on hardware that FN990A28 reports subsystem 1c5d:2010 (an unknown subsystem still binds via the generic 17cb:0308 entry).')
    w('')
    # USB
    w('## 4. USB topology')
    w('')
    w('Host USB3 Type-C (FRDM) -> carrier USB-C J701 (UFP) -> HD3SS3220 (orientation mux, GPIO mode) -> USB5744 upstream. '
      'USB5744 port 4 disabled by strap; ports 1-3 non-removable.')
    w('')
    w('| Slot | Connector | USB5744 port | USB2 D+ | Module USB3 TX -> hub | Hub USB3 TX -> module RX |')
    w('|---|---|---|---|---|---|')
    for u in m['usb']:
        w(f"| {u['slot']} | {u['conn']} | {u['port']} | {u['pins']['USB_D+']} | {u['pins']['USB3_TX+']} | {u['pins']['USB3_RX+']} |")
    w('')
    w('USB is always wired. Telit FN990: with pin 20 LOW (PCIe mode) USB is debug-only; with `SLOTn_PCIE_SEL`=0 at boot the card boots '
      'USB-only (USB 3.1 Gen2 / USB 2.0, HDG Table 29). Sierra EM92xx: interfaces are mutually exclusive; USB needs PCIE_DIS driven to 1.8 V '
      '(fit the DNP 10k pin-20 pull-up to +1V8) and normally VBUS_SENSE high on pin 22 (fit the DNP 10k to the slot rail - Sierra only).')
    w('')
    # LEDs
    w('## 5. LEDs')
    w('')
    w('| Ref | Colour | Anode supply | Cathode net | Lit when | Sheet |')
    w('|---|---|---|---|---|---|')
    for l in m['leds']:
        w(f"| {l['ref']} | {l['color']} | `{l['anode']}` | `{l['cathode']}` | {l['meaning']} | {l['sheet']} |")
    w('')
    # TPs
    w('## 6. Test points')
    w('')
    w('| Ref | Label (silkscreen intent) | Netlist net | Sheet |')
    w('|---|---|---|---|')
    for t in m['tps']:
        w(f"| {t['ref']} | {t['label']} | `{t['net']}` | {t['sheet']} |")
    w('')
    # header
    w('## 7. Host header J801 (2x5, 2.54 mm)')
    w('')
    w('| Pin | Net | Notes |')
    w('|---|---|---|')
    for h in m['header']:
        w(f"| {h['pin']} | `{h['net']}` | {h['note']} |")
    w('')
    w('Mapping to FRDM-IMX95 header pins (which LPI2C instance, which GPIO for INT#/RESET#) is **not decided**; see docs/open-issues.md. '
      'Host I/O must be 3.3 V (**VERIFY** the FRDM header voltage).')
    w('')
    # verify list
    w('## 8. Parts flagged VERIFY in the schematic')
    w('')
    w('| Ref | Value | Field | Text |')
    w('|---|---|---|---|')
    seen = set()
    for v in m['verify']:
        key = (v['value'], v['field'], v['text'])
        if key in seen: continue
        seen.add(key)
        same = [x['ref'] for x in m['verify'] if (x['value'], x['field'], x['text']) == key]
        w(f"| {', '.join(same)} | {v['value']} | {v['field']} | {v['text']} |")
    w('')
    return '\n'.join(L) + '\n'

def render_json(m):
    return json.dumps(dict(
        generated_by='tools/gen_interface.py', source='hardware/kicad/wwan-carrier.net',
        expanders=[dict(ref=e['ref'], addr=e['addr'], init_output=e['out'], init_config=e['cfg'],
                        lines=[dict(name=l['line_name'], net=l['net'], port=l['port'], bit=l['bit'], dir=l['dir'], active=l['active'],
                                    init=l['safe']) for l in e['lines']]) for e in m['expanders']],
        i2c={d['part']: d['addr'] for d in m['i2c'] if d['addr'] is not None},
        pcie=[dict(slot=p['slot'], switch_port=p['port'], lane=p['lane']) for p in m['pcie']],
        usb=[dict(slot=u['slot'], hub_port=u['port']) for u in m['usb']],
    ), indent=1) + '\n'

def render_dtsi(m):
    L = ['/* GENERATED by tools/gen_interface.py - DO NOT EDIT. gpio-line-names for the carrier TCA6416A expanders. */']
    for e in m['expanders']:
        names = [l['line_name'] for l in e['lines']]
        L.append(f"#define CARRIER_GPIO_NAMES_{e['addr']:02X} \\")
        L.append('\t' + ', '.join(f'"{n}"' for n in names))
    return '\n'.join(L) + '\n'

def main():
    check = '--check' in sys.argv
    nl = Netlist(NETLIST)
    m = build(nl)
    outs = {OUT_MD: render_md(m), OUT_JSON: render_json(m), OUT_DTSI: render_dtsi(m)}
    bad = 0
    for path, text in outs.items():
        if check:
            cur = open(path).read() if os.path.exists(path) else ''
            if cur != text:
                print(f'OUT OF DATE: {os.path.relpath(path, ROOT)}'); bad = 1
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, 'w').write(text)
            print(f'wrote {os.path.relpath(path, ROOT)}')
    for wmsg in m['warnings']:
        print('WARNING:', wmsg)
    sys.exit(bad)

if __name__ == '__main__':
    main()
