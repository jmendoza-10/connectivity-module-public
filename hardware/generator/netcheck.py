"""rev 0.3 netlist sanity checks (vendor-neutral M.2 slots + supply-chain rule). Usage: netcheck.py wwan-carrier.net
Exit code 1 on any failure. Checks are on the exported KiCad netlist, i.e. what ERC/PCB actually see."""
import sys, re
from sexp import parse, find

t = parse(open(sys.argv[1]).read())[0]
comps = {}
for c in find(find(t, 'components')[0], 'comp'):
    ref = find(c, 'ref')[0][1][1]
    d = {'value': find(c, 'value')[0][1][1], 'fp': (find(c, 'footprint') or [[None, ('S', '')]])[0][1][1], 'props': {}}
    for p in find(c, 'property'):
        nm = find(p, 'name')[0][1][1]; v = find(p, 'value')
        d['props'][nm] = v[0][1][1] if v else ''
    comps[ref] = d
pin2net = {}; nets = {}
for n in find(find(t, 'nets')[0], 'net'):
    nm = find(n, 'name')[0][1][1].split('/')[-1]
    nodes = [(find(x, 'ref')[0][1][1], find(x, 'pin')[0][1][1]) for x in find(n, 'node')]
    nets[nm] = nodes
    for rp in nodes: pin2net[rp] = nm
fails = []
def ok(cond, msg):
    print(('  ok   ' if cond else '  FAIL ') + msg)
    if not cond: fails.append(msg)
def net(ref, pin): return pin2net.get((ref, str(pin)), 'unconnected')
def dnp(ref): return 'dnp' in comps[ref]['props'] or comps[ref]['props'].get('DNP') is not None

# --- supply-chain: no Nexperia / PRC-brand part numbers anywhere in value or MPN ---
BANNED = re.compile(r'nexperia|BUK7|LVC1G0\dGW|quectel|fibocom|meig|sunsea|simcom|neoway|lcsc|jlc|ti?anma|wingtech|ampleon', re.I)
bad = [(r, d['value'], d['props'].get('MPN', '')) for r, d in comps.items() if BANNED.search(d['value'] + ' ' + d['props'].get('MPN', ''))]
ok(not bad, f'no Nexperia/PRC-brand values or MPNs ({bad[:3]})')
for q in ('Q101', 'Q102'):
    ok(comps[q]['value'] == 'NVMFS5C646NL' and 'NVMFS5C646NLAFT1G' in comps[q]['props'].get('MPN', '') and comps[q]['fp'] == 'Package_SO:ONSemi_SO-8FL_488AA', f'{q} = onsemi NVMFS5C646NL on SO-8FL 488AA footprint')
lm = [r for r, d in comps.items() if d['value'].startswith('LM74800')][0]
ok(net('Q101', 5) == net('Q102', 5) and (lm, '12') in nets[net('Q101', 5)] and (lm, '1') in nets[net('Q101', 4)] and (lm, '8') in nets[net('Q102', 4)]
   and net('Q102', 1) == '+12V', f'Q101/Q102 common drain on pad 5 (= {lm} VS), DGATE/HGATE to gates, Q102 source = +12V')
ok(comps['U302']['value'] == 'SN74LVC1G07DCKR', 'U302 PERST# buffer = TI SN74LVC1G07DCKR')
generic = [r for r, d in comps.items() if r[0] in 'RC' and not d['props'].get('MPN')]
ok(not generic, f'every R/C carries a named maker in MPN ({generic[:5]})')

# --- per-slot M.2 checks ---
for n in (1, 2, 3):
    J = f'J{3 + n}01'; b = 100 * (3 + n)
    print(f'slot {n} ({J}):')
    ok(comps[J]['value'] == 'M.2 Key-B WWAN', f'{J} generic M.2 Key-B WWAN symbol')
    for p in (24, 38, 68): ok(net(J, p).startswith('unconnected'), f'pin {p} NC')
    ok(net(J, 73) == 'GND', 'pin 73 = GND (EM92 + FN990)')
    for p in (2, 4, 70, 72, 74): ok(net(J, p) == f'+3V7_S{n}', f'pin {p} = +3V7_S{n}')
    s20 = net(J, 20); members = {r for r, _ in nets.get(s20, [])}
    q = [r for r in members if r.startswith('Q')]
    ok(s20 == f'S{n}_M2_IFSEL' and len(q) == 1, f'pin 20 net {s20} has one NFET drain')
    if q:
        Q = q[0]
        ua = [r for r in comps if r.startswith('U') and comps[r]['props'].get('Sheetfile') == f'slot{n}.kicad_sch' and '1G08' in comps[r]['value']][0]
        jp = [r for r in comps if r.startswith('JP') and comps[r]['props'].get('Sheetfile') == f'slot{n}.kicad_sch'][0]
        g = nets[net(Q, 1)]
        ok(net(Q, 3) == s20 and net(Q, 2) == 'GND' and net(Q, 1) == f'SLOT{n}_PCIE_SEL' and any(r == 'U802' for r, _ in g)
           and any(r.startswith('R') for r, _ in g), f'{Q}: D=pin20, S=GND, G=SLOT{n}_PCIE_SEL (U802 + 10k PU), separate from PERST# gating')
        ok((ua, '2') in nets[net(jp, 1)] and (Q, '1') not in nets[net(jp, 1)], f'PCIE_EN/JP only gate PERST# ({ua}.B)')
        ok('Diodes' in comps[Q]['props'].get('MPN', '') or 'onsemi' in comps[Q]['props'].get('MPN', ''), f'{Q} MPN non-Nexperia ({comps[Q]["props"].get("MPN")})')
    rs = [r for r in members if r.startswith('R')]
    ok(len(rs) == 1 and dnp(rs[0]) and {net(rs[0], 1), net(rs[0], 2)} == {s20, '+1V8'}, f'pin 20 Sierra option: DNP 10k to +1V8 ({rs})')
    s22 = net(J, 22); m22 = {r for r, _ in nets.get(s22, [])}
    r22 = [r for r in m22 if r.startswith('R')]
    ok(any(r.startswith('TP') for r in m22) and any(comps[r]['value'] == f'S{n}_M2_GPIO6' for r in m22 if r.startswith('TP')), f'pin 22 -> TP S{n}_M2_GPIO6')
    ok(len(r22) == 1 and dnp(r22[0]) and comps[r22[0]]['value'] == '10k' and {net(r22[0], 1), net(r22[0], 2)} == {s22, f'+3V7_S{n}'},
       f'pin 22 Sierra VBUS_SENSE option: DNP 10k to slot rail ({r22})')
    s28 = net(J, 28)
    ok(len(nets[s28]) == 2 and any(comps[r]['value'] == f'S{n}_M2_GPIO8' for r, _ in nets[s28] if r.startswith('TP')), f'pin 28 -> TP S{n}_M2_GPIO8 only')
    ua = [r for r in comps if r.startswith('U') and comps[r]['props'].get('Sheetfile') == f'slot{n}.kicad_sch' and '1G08' in comps[r]['value']][0]
    ok((ua, '4') in nets[net(J, 50)] and net(J, 6) == f'SLOT{n}_FCPO_N', 'PERST# from AND gate, FCPO# from expander net')
    rst = nets[net(J, 67)]
    ok(not any(r.startswith('R') for r, _ in rst) and any(r.startswith('Q') and p == '3' for r, p in rst), 'RESET# open-drain NFET only, no pull-up (both vendors)')
    holes = [r for r, d in comps.items() if r.startswith('H') and d['props'].get('Sheetfile') == f'slot{n}.kicad_sch']
    ok(len(holes) == 2 and {comps[h]['value'] for h in holes} == {'3052 standoff', '3042 standoff'}, f'3052 + 3042 standoffs ({holes})')
    u = sorted(comps[r]['value'] for r in comps if r.startswith('U') and comps[r]['props'].get('Sheetfile') == f'slot{n}.kicad_sch')
    ok(u == ['SN74LVC1G08DCKR', 'TPD4E05U06DQAR'], f'slot ICs = TI SN74LVC1G08DCKR (PERST# gate) + TI TPD4E05U06DQAR ({u})')
print('NETCHECK:', 'PASS' if not fails else f'{len(fails)} FAIL')
sys.exit(1 if fails else 0)
