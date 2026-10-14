from engine import place, place_pin, snap, Port, Note, SIDE, GR
from helpers import *
import math

def P(s, net, x, y, d, ltype='hier'):
    """explicit port: label text extends toward d (L/R/U/D); wires arrive from the opposite side."""
    s.ports.append(Port(net, x, y, SIDE[d], ltype))

def flagtp(s, items, x, y, dx=7.62):
    """FLAG/TP parts in a row with pins pointing down at y."""
    for it in items:
        place_pin(it, '1', x, y); x += dx
    return x

def caps_on(caps, x, y, net, step=None, direction=1):
    """vertical caps hanging from a horizontal line at y (top tips on the line)."""
    for i, c in enumerate(caps):
        vpart(c, x, y, net)
        nxt = caps[i + 1] if (direction < 0 and i + 1 < len(caps)) else c
        st = step or max(7.62, math.ceil((fw(nxt) + 5.5) / 2.54) * 2.54)
        x += st * direction
    return x

def pullup_on(r, x, y, rail):
    """vertical pull-up/down whose signal tip sits on a horizontal line at y; rail end away from the line."""
    sig = other_net(r, rail)
    if rail == 'GND':
        vpart(r, x, y, sig)
    else:
        place_pin(r, pinkey(r, sig), x, y, 'D')
    return r

def outrow(s, b, rail, lx, xend, y, members):
    """rail bus from inductor output lx to past the caps; PWR_FLAG + TP + rail symbol (pointing right) at the end."""
    s.bus(rail, [(lx, y), (xend + 30.48, y)])
    place_pin(b['flag'], '1', xend + 7.62, y); place_pin(b['tp'], '1', xend + 15.24, y)
    s.cluster(rail, members + [b['flag'], b['tp']], at=(xend + 30.48, y, 'R'))

def lm_buck(s, b, ux, uy, vout, y_in, x_in):
    """LM61460 block. y_in: +12V input bus y; x_in: left x of the input bus."""
    U = place(b['U'], ux, uy)
    vin = tip(U, '8'); en = tip(U, '7'); rt = tip(U, '6'); sw = tip(U, '10'); fb = tip(U, '4'); vcc = tip(U, '2'); pg = tip(U, '5')
    s.bus('+12V', [(x_in, y_in), (vin[0] - 2.54, y_in), (vin[0] - 2.54, vin[1])])
    # boot network above the chip
    hpart(b['Rb'], ux + 17.78, uy - 30.48, b['Rb'].groups[0]['net']); b['Rb'].fstyle = 'above'
    hpart(b['Cb'], ux + 30.48, uy - 30.48, b['Cb'].groups[0]['net']); b['Cb'].fstyle = 'above2'
    hpart(b['L'], sw[0] + 33.02, sw[1], b['L'].groups[0]['net']); b['L'].fstyle = 'above2'
    U.fstyle = 'belowleft'
    lx = right(b['L'])
    xd = lx + 7.62
    vpart(b['Rfb1'], xd, fb[1] - 2.54 - 7.62, vout)
    vpart(b['Rfb2'], xd, fb[1] + 2.54, b['Rfb2'].groups[0]['net'])
    if 'Cff' in b: vpart(b['Cff'], xd + 12.7, fb[1] - 2.54 - 7.62, vout)
    xe = caps_on([b['Cbias']] + b['Cout'], xd + 25.4, sw[1], vout)
    xend = xe - 5.08
    outrow(s, b, vout, lx, xend, sw[1], [b['U'], b['L'], b['Rfb1'], b['Cbias']] + ([b['Cff']] if 'Cff' in b else []) + b['Cout'])
    hpart(b['Cvcc'], vcc[0] + 2.54, vcc[1], other_net(b['Cvcc'], 'GND')); b['Cvcc'].fstyle = 'above2'
    pullup_on(b['Rpg'], pg[0] + 25.4, pg[1], '+3V3')
    # left side
    hpart(b['Rrt'], rt[0] - 12.7, rt[1], 'GND'); b['Rrt'].fstyle = 'tb'
    return xend, vin, en, pg

ROOT_PAPER = 'A1'
ROOT_LAYOUT = {
    'power_input.kicad_sch': (40.64, 60.96, 76.2),
    'pcie_switch.kicad_sch': (228.6, 60.96, 83.82),
    'usb_hub.kicad_sch': (228.6, 431.8, 83.82),
    'slot1.kicad_sch': (469.9, 60.96, 81.28),
    'slot2.kicad_sch': (469.9, 210.82, 81.28),
    'slot3.kicad_sch': (469.9, 360.68, 81.28),
    'control.kicad_sch': (701.04, 60.96, 81.28),
    'wwan_power.kicad_sch': (701.04, 360.68, 81.28),
}
def _pg(n): return [f'SLOT{n}_PCIE_TX_P', f'SLOT{n}_PCIE_TX_N', f'SLOT{n}_PCIE_RX_P', f'SLOT{n}_PCIE_RX_N', f'SLOT{n}_REFCLK_P', f'SLOT{n}_REFCLK_N', f'SLOT{n}_CLKREQ_N']
def _ug(n): return [f'SLOT{n}_USB2_DP', f'SLOT{n}_USB2_DM', f'SLOT{n}_USB3_TX_P', f'SLOT{n}_USB3_TX_N', f'SLOT{n}_USB3_RX_P', f'SLOT{n}_USB3_RX_N']
def _cg(n): return [f'SLOT{n}_FCPO_N', f'SLOT{n}_PCIE_EN', f'SLOT{n}_PCIE_SEL', f'SLOT{n}_RESET', f'SLOT{n}_WAKE_N', f'SLOT{n}_WDIS']
_PGN = ['PG_3V3', 'PG_0V95', 'PG_1V8', 'PG_1V2']
_WG = ['SLOT1_PWR_EN', 'SLOT1_PG', 'SLOT2_PWR_EN', 'SLOT2_PG', 'SLOT3_PWR_EN', 'SLOT3_PG']
ROOT_SEQ = {
    'power_input.kicad_sch': {'R': _PGN},
    'pcie_switch.kicad_sch': {'L': ['I2C_SCL', 'I2C_SDA'], 'R': ['PCIE_PERST_N'] + _pg(1) + [None] + _pg(2) + [None] + _pg(3)},
    'usb_hub.kicad_sch': {'L': ['I2C_SCL', 'I2C_SDA', 'HUB_RESET_N'], 'R': _ug(1) + [None] + _ug(2) + [None] + _ug(3)},
    'control.kicad_sch': {'L': _PGN + [None, 'I2C_SCL', 'I2C_SDA', 'HUB_RESET_N', None] + _cg(1) + [None] + _cg(2) + [None] + _cg(3) + [None] + _WG},
    'wwan_power.kicad_sch': {'L': _WG[::-1]},
}
for _n in (1, 2, 3):
    ROOT_SEQ[f'slot{_n}.kicad_sch'] = {'L': ['PCIE_PERST_N'] + _pg(_n) + [None] + _ug(_n), 'R': _cg(_n)}

def root_wires(root, pp):
    B = root.bus
    PC, HB, CT, WP, PI = 'pcie_switch.kicad_sch', 'usb_hub.kicad_sch', 'control.kicad_sch', 'wwan_power.kicad_sch', 'power_input.kicad_sch'
    SL = lambda n: f'slot{n}.kicad_sch'
    # PCIe switch -> slot1 straight; PERST# trunk to all slots
    for net in _pg(1):
        B(net, [pp[(PC, net)], pp[(SL(1), net)]])
    XP = 322.58
    a = pp[(PC, 'PCIE_PERST_N')]
    B('PCIE_PERST_N', [a, pp[(SL(1), 'PCIE_PERST_N')]])
    B('PCIE_PERST_N', [(XP, a[1]), (XP, pp[(SL(3), 'PCIE_PERST_N')][1]), pp[(SL(3), 'PCIE_PERST_N')]])
    B('PCIE_PERST_N', [(XP, pp[(SL(2), 'PCIE_PERST_N')][1]), pp[(SL(2), 'PCIE_PERST_N')]])
    def lane(net, s0, s1, xl):
        p, q = pp[(s0, net)], pp[(s1, net)]
        B(net, [p, (xl, p[1]), (xl, q[1]), q])
    # PCIe switch -> slots 2/3 (downward: upper wires turn further right)
    for m, net in enumerate(_pg(2) + _pg(3)):
        lane(net, PC, SL(2 if m < 7 else 3), 375.92 - 2.54 * m)
    # USB hub -> slots (upward: lower wires turn further right)
    for m, net in enumerate(_ug(1) + _ug(2) + _ug(3)):
        lane(net, HB, SL(1 if m < 6 else 2 if m < 12 else 3), 391.16 + 2.54 * m)
    # slots -> control
    for m, net in enumerate(_cg(1)):
        lane(net, SL(1), CT, 584.2 - 2.54 * m)
    for m, net in enumerate(_cg(2) + _cg(3)):
        lane(net, SL(2 if m < len(_cg(2)) else 3), CT, 596.9 + 2.54 * m)
    # power_input PG -> control over the top
    for i, net in enumerate(_PGN):
        p, q = pp[(PI, net)], pp[(CT, net)]
        xa, ya, xd = 127.0 + 2.54 * i, 22.86 + 2.54 * i, 690.88 - 2.54 * i
        B(net, [p, (xa, p[1]), (xa, ya), (xd, ya), (xd, q[1]), q])
    # control -> I2C (pcie + hub) and HUB_RESET_N over the top, trunks left of the pcie/hub blocks
    for i, net in enumerate(['I2C_SCL', 'I2C_SDA', 'HUB_RESET_N']):
        c = pp[(CT, net)]; h = pp[(HB, net)]
        xl, yt, xt = 670.56 - 5.08 * i, 33.02 + 2.54 * i, 210.82 + 5.08 * i
        B(net, [c, (xl, c[1]), (xl, yt), (xt, yt), (xt, h[1]), h])
        if (PC, net) in pp:
            B(net, [(xt, pp[(PC, net)][1]), pp[(PC, net)]])
    # control <-> wwan_power (nested U, top source -> bottom target)
    for m, net in enumerate(_WG):
        p, q = pp[(CT, net)], pp[(WP, net)]
        xl = 640.08 + 2.54 * m
        B(net, [p, (xl, p[1]), (xl, q[1]), q])

ROOT_HINT = {'seq': ROOT_SEQ, 'wires': root_wires}
def root_notes():
    return [Note('Root sheet = wired system block diagram: every wire here is a hierarchical sheet pin connection (no global labels for signals).\n'
                 'Power rails (+12V, +3V3, +0V95, +1V8, +1V2, +3V7_S1..3) are distributed as power symbols inside the sheets.\n'
                 'PCIe: switch DS ports -> slots (Gen3 x1 + REFCLK + CLKREQ#), PERST# fan-out.  USB: USB5744 DS ports 1-3 -> slots (USB2 + USB3).\n'
                 'Control: TCA6416A expanders -> slot FCPO#/RESET/W_DISABLE/PCIE_EN/PCIE_SEL(M.2 pin 20)/WAKE#, buck enables / PGOOD; host I2C to hub + PCIe switch.',
                 40.64, 520.7)]

def lay_power_input(h):
    s = h['s']; s.paper = 'A2'
    MAIN = 45.72
    J = h['J']; J.mirror = True
    place_pin(J, '1', 25.4, MAIN)
    s.stub(J, '2', 3, 'D')
    place_pin(h['flags'][0], '1', 33.02, MAIN)     # +12V_RAW flag, tip on the line
    place_pin(h['tps'][1], '1', 40.64, MAIN)        # +12V_RAW TP
    hpart(h['F'], 53.34, MAIN, '+12V_RAW'); h['F'].fstyle = 'tb'
    vpart(h['TVS'], 66.04, MAIN, '+12V_FUSED'); h['TVS'].fstyle = 'right'
    vpart(h['Cf'], 81.28, MAIN, '+12V_FUSED')
    Q1, Q2 = h['Q1'], h['Q2']; LM = h['LM']
    place_pin(Q1, '1', 99.06, MAIN); place_pin(Q2, '5', tip(Q1, '5')[0] + 5.08, MAIN)
    Q1.fstyle = Q2.fstyle = 'above2'; LM.fstyle = 'inside'; LM.fdy = 8.5
    gx = tip(Q1, '4')[0]
    place_pin(LM, '1', gx, 71.12)
    vs = tip(LM, '12')
    YB = 63.5
    s.bus('VS_CD', [tip(Q1, '5'), (vs[0], MAIN), (vs[0], YB), (vs[0] + 55.88, YB)])
    s.bus('VS_CD', [(vs[0], MAIN), tip(Q2, '5')])
    a = tip(LM, '2'); sw = tip(LM, '4'); ov = tip(LM, '5')
    vpart(h['Rov1'], sw[0] - 12.7, sw[1] + 2.54, 'LM_SW')
    vpart(h['Rov2'], sw[0] - 12.7, ov[1] + 2.54, 'LM_OV')
    h['Rov1'].fstyle = h['Rov2'].fstyle = 'left'
    cap = tip(LM, '11'); en = tip(LM, '6'); out = tip(LM, '9')
    vpart(h['Ccap'], cap[0] + 7.62, YB, 'VS_CD')
    vpart(h['Ren1'], cap[0] + 22.86, en[1] - 2.54 - 7.62, 'VS_CD')
    vpart(h['Ren2'], cap[0] + 22.86, en[1] + 2.54, 'LM_EN')
    vpart(h['Cvs'], cap[0] + 35.56, YB, 'VS_CD')
    place_pin(h['flags'][2], '1', vs[0] + 55.88, YB)
    # +12V bulk on main line
    x = caps_on([h['Cb1'], h['Cb2'], h['Cb3']], tip(Q2, '1')[0] + 45.72, MAIN, '+12V')
    vpart(h['Rled'], x, MAIN, '+12V'); vpart(h['Dled'], x, MAIN + 10.16, 'LED12_A')
    place_pin(h['flags'][3], '1', x + 12.7, MAIN)
    place_pin(h['tps'][0], '1', x + 20.32, MAIN)
    xr = x + 33.02
    place_pin(h['flags'][1], '1', 25.4, 71.12)   # GND flag + GND test points
    place_pin(h['tps'][2], '1', 35.56, 71.12); place_pin(h['tps'][3], '1', 45.72, 71.12)
    s.bus('+12V', [tip(Q2, '1'), (xr, MAIN)])
    # ---- +3V3 buck ----
    b = h['b3v3']
    ux, uy = 375.92, 99.06
    Y3 = 71.12
    xe, vin, en3, pg3 = lm_buck(s, b, ux, uy, '+3V3', Y3, xr + 30.48)
    s.bus('+12V', [(xr, MAIN), (xr + 30.48, MAIN), (xr + 30.48, Y3)])
    caps_on(b['Cin'], vin[0] - 38.1, Y3, '+12V', direction=-1)
    vpart(b['Ren1'], en3[0] - 22.86, en3[1] - 2.54 - 7.62, '+12V'); vpart(b['Ren2'], en3[0] - 22.86, en3[1] + 2.54, 'EN_3V3')
    b['Ren1'].fstyle = b['Ren2'].fstyle = 'left'
    P(s, 'PG_3V3', pg3[0] + 55.88, pg3[1], 'R')
    place_pin(b['tppg'], '1', pg3[0] + 35.56, pg3[1])
    YPG = 170.18 - 12.7
    s.bus('PG_3V3', [pg3, (pg3[0] + 55.88, pg3[1])])
    s.bus('PG_3V3', [(pg3[0] + 45.72, pg3[1]), (pg3[0] + 45.72, YPG), (93.98, YPG)])
    # ---- band 2: +12V trunk ----
    TR = 170.18
    s.bus('+12V', [(xr, MAIN), (xr, TR - 25.4), (30.48, TR - 25.4)])
    # +0V95 TPS568230
    b = h['b0v95']; ux, uy = 109.22, 205.74
    U = place(b['U'], ux, uy)
    vin = tip(U, '2'); pgd = tip(U, '9'); vcc = tip(U, '17'); mode = tip(U, '15'); bst = tip(U, '1'); swp = tip(U, '6'); fbp = tip(U, '14')
    s.bus('+12V', [(30.48, TR - 25.4), (30.48, TR), (vin[0] - 2.54, TR), (vin[0] - 2.54, vin[1])])
    caps_on(b['Cin'], vin[0] - 22.86, TR, '+12V', direction=-1)
    vpart(b['Cvcc'], vcc[0] - 7.62, vcc[1], 'VCC_0V95')
    vpart(b['Rm1'], vcc[0] - 25.4, vcc[1] + 2.54, 'VCC_0V95'); vpart(b['Rm2'], vcc[0] - 25.4, mode[1] + 2.54, 'MODE_0V95')
    b['Cvcc'].fstyle = b['Rm1'].fstyle = b['Rm2'].fstyle = 'left'
    pullup_on(b['Rpg'], pgd[0] - 33.02, pgd[1], '+3V3'); b['Rpg'].fstyle = 'left'
    P(s, 'PG_0V95', pgd[0] - 45.72, pgd[1], 'L')
    hpart(b['Cb'], bst[0] + 7.62, bst[1] - 7.62, 'BST_0V95'); b['Cb'].fstyle = 'above'
    hpart(b['L'], swp[0] + 25.4, swp[1], 'SW_0V95'); b['L'].fstyle = 'above2'
    lx = right(b['L']); xd = lx + 7.62
    vpart(b['Rfb1'], xd, fbp[1] - 2.54 - 7.62, '+0V95'); vpart(b['Rfb2'], xd, fbp[1] + 2.54, 'FB_0V95')
    xe = caps_on(b['Cout'], xd + 15.24, swp[1], '+0V95')
    outrow(s, b, '+0V95', lx, xe - 5.08, swp[1], [b['L'], b['Rfb1']] + b['Cout'])
    U.fstyle = 'inside'
    # TPS62130 x2
    for key, ux, rail in (('b1v8', 302.26, '+1V8'), ('b1v2', 467.36, '+1V2')):
        b = h[key]; uy = 205.74
        U = place(b['U'], ux, uy)
        vin = tip(U, '10'); ss = tip(U, '9'); swp = tip(U, '1'); vos = tip(U, '14'); fbp = tip(U, '5'); pgp = tip(U, '4')
        s.bus('+12V', [(vin[0] - 50.8, TR), (vin[0], TR)])
        caps_on(b['Cin'], vin[0] - 20.32, TR, '+12V', direction=-1)
        vpart(b['Css'], ss[0] - 7.62, ss[1] + 2.54, b['Css'].groups[0]['net']); b['Css'].fstyle = 'left'
        hpart(b['L'], swp[0] + 7.62, swp[1], b['L'].groups[0]['net']); b['L'].fstyle = 'above2'
        lx = right(b['L']); xd = lx + 7.62
        vpart(b['Rfb1'], xd, fbp[1] - 2.54 - 7.62, rail); vpart(b['Rfb2'], xd, fbp[1] + 2.54, b['Rfb2'].groups[0]['net'])
        xe = caps_on(b['Cout'], xd + 15.24, swp[1], rail)
        outrow(s, b, rail, lx, xe - 5.08, swp[1], [b['U'], b['L'], b['Rfb1']] + b['Cout'])
        U.fstyle = 'belowleft'
        pullup_on(b['Rpg'], pgp[0] + 7.62, pgp[1] + 10.16, '+3V3')
        P(s, 'PG_' + rail[1:], xd + 12.7, pgp[1] + 10.16, 'R')
    s.bus('+12V', [(xr, TR - 25.4), (tip(h['b1v2']['U'], '10')[0] - 50.8, TR - 25.4)])
    for key in ('b1v8', 'b1v2'):
        vin = tip(h[key]['U'], '10')
        s.bus('+12V', [(vin[0] - 50.8, TR - 25.4), (vin[0] - 50.8, TR)])
    s.cluster('+12V', [it for it in s.items if any(g['net'] == '+12V' for g in it.groups)], at=(xr, MAIN, 'U'))
    h['note'].x, h['note'].y = 20.32, 285.0

def lay_wwan_power(h):
    s = h['s']; s.paper = 'A2'
    XT = 63.5
    allin = []
    for n in (1, 2, 3):
        b = h[n]
        ux, uy = 165.1, 81.28 + (n - 1) * 101.6
        y_in = uy - 38.1
        xe, vin, en, pg = lm_buck(s, b, ux, uy, f'+3V7_S{n}', y_in, XT)
        caps_on(b['Cin'], vin[0] - 30.48, y_in, '+12V', direction=-1)
        pullup_on(b['Ren'], en[0] - 30.48, en[1], 'GND'); b['Ren'].fstyle = 'left'
        P(s, f'SLOT{n}_PWR_EN', XT - 12.7, en[1], 'L')
        P(s, f'SLOT{n}_PG', pg[0] + 45.72, pg[1], 'R')
        if n > 1:
            s.bus('+12V', [(XT, y_in - 101.6), (XT, y_in)])
        allin += [it for it in s.items if any(g['net'] == '+12V' for g in it.groups)]
    s.bus('+12V', [(XT, 25.4), (XT, 81.28 - 38.1)])
    s.cluster('+12V', list(dict.fromkeys(allin)), at=(XT, 25.4, 'U'))
    h['note'].x, h['note'].y = 20.32, 330.0

def lay_slot(h, n):
    s = h['s']; s.paper = 'A2'
    J = h['J']; V = f'+3V7_S{n}'
    X0, Y0 = 260.35, 139.7
    place(J, X0, Y0); J.fstyle = 'belowright'
    L = X0 - 22.86; Rt = X0 + 22.86
    jy = lambda net: tip(J, net)[1]
    # ---- left: high-speed + sideband hierarchical ports ----
    for net in (f'SLOT{n}_PCIE_TX_P', f'SLOT{n}_PCIE_TX_N', f'SLOT{n}_PCIE_RX_P', f'SLOT{n}_PCIE_RX_N', f'SLOT{n}_REFCLK_P', f'SLOT{n}_REFCLK_N',
                f'SLOT{n}_CLKREQ_N', f'SLOT{n}_USB2_DP', f'SLOT{n}_USB2_DM', f'SLOT{n}_USB3_TX_P', f'SLOT{n}_USB3_TX_N',
                f'SLOT{n}_USB3_RX_P', f'SLOT{n}_USB3_RX_N'):
        P(s, net, L - 25.4, jy(net), 'L')
    # WAKE#: pull-up hangs below the line, left of the USB port labels
    yw = jy(f'SLOT{n}_WAKE_N')
    place_pin(h['Rwake'], f'SLOT{n}_WAKE_N', L - 50.8, yw, 'U'); h['Rwake'].fstyle = 'right'
    P(s, f'SLOT{n}_WAKE_N', L - 58.42, yw, 'L')
    # PERST#: AND gate (PCIE_PERST_N & PCIE_EN_L)
    yp = jy(f'SLOT{n}_PERST_N')
    Ua = h['Uand']; Ua.fstyle = 'belowright'
    place_pin(Ua, f'SLOT{n}_PERST_N', L - 96.52, yp)
    place_pin(h['tps'][f'SLOT{n}_PERST_N'], '1', L - 60.96, yp)
    a_in = tip(Ua, 'PCIE_PERST_N'); b_in = tip(Ua, f'S{n}_PCIE_EN_L'); vcc = tip(Ua, '+3V3')
    P(s, 'PCIE_PERST_N', a_in[0] - 5.08, a_in[1] - 12.7, 'U')
    s.bus('+3V3', [vcc, (vcc[0], vcc[1] - 5.08), (vcc[0] + 17.78, vcc[1] - 5.08)])
    vpart(h['Cand'], vcc[0] + 17.78, vcc[1] - 5.08, '+3V3')
    s.cluster('+3V3', [Ua, h['Cand']], at=(vcc[0], vcc[1] - 5.08, 'U'))
    xn = b_in[0]
    vpart(h['Renpu'], xn - 30.48, b_in[1], f'SLOT{n}_PCIE_EN'); h['Renpu'].fstyle = 'right'
    vpart(h['JP'], xn - 5.08, b_in[1], f'S{n}_PCIE_EN_L'); h['JP'].fstyle = 'belowleft'
    hpart(h['Ren'], xn - 27.94, b_in[1], f'SLOT{n}_PCIE_EN'); h['Ren'].fstyle = 'above2'
    P(s, f'SLOT{n}_PCIE_EN', xn - 33.02, b_in[1], 'L')
    # ---- left-lower: FCPO#, RESET (FET), W_DISABLE (FET), LED ----
    yl = jy(f'S{n}_LED_K'); Dl = h['Dled']; Dl.mirror = True
    place_pin(Dl, f'S{n}_LED_K', L - 7.62, yl); Dl.fstyle = 'below2'
    hpart(h['Rled'], L - 25.4, yl, '+3V3'); h['Rled'].fstyle = 'below2'
    s.bus(f'S{n}_LED_A', [tip(h['Rled'], f'S{n}_LED_A'), tip(Dl, f'S{n}_LED_A')])
    yd = jy(f'S{n}_WDIS1_N'); Q = h['Qwd']
    place_pin(Q, f'S{n}_WDIS1_N', L - 55.88, yd); Q.fstyle = 'right'
    g = tip(Q, f'SLOT{n}_WDIS')
    vpart(h['Rwd'], g[0] - 5.08, g[1], f'SLOT{n}_WDIS'); h['Rwd'].fstyle = 'left'
    P(s, f'SLOT{n}_WDIS', g[0] - 15.24, g[1], 'L')
    yr = jy(f'S{n}_RESET_N'); Q = h['Qrst']
    place_pin(Q, f'S{n}_RESET_N', L - 101.6, yr); Q.fstyle = 'right'
    g = tip(Q, f'SLOT{n}_RESET')
    vpart(h['Rrst'], g[0] - 5.08, g[1], f'SLOT{n}_RESET'); h['Rrst'].fstyle = 'left'
    P(s, f'SLOT{n}_RESET', g[0] - 15.24, g[1], 'L')
    yf = jy(f'SLOT{n}_FCPO_N')
    vpart(h['Rfcpo'], L - 142.24, yf, f'SLOT{n}_FCPO_N'); h['Rfcpo'].fstyle = 'right'
    P(s, f'SLOT{n}_FCPO_N', L - 152.4, yf, 'L')
    # ---- top: +3V7 rail bulk/decoupling right at the socket ----
    YB = Y0 - 71.12 - 15.24
    caps = h['Cbulk'] + h['Cdec']
    xe = caps_on(caps, X0 + 30.48, YB, V)
    place_pin(h['tps'][V], '1', xe, YB)
    s.bus(V, [tip(J, V), (X0, YB), (xe + 15.24, YB)])
    s.cluster(V, [J, h['tps'][V]] + caps, at=(xe + 15.24, YB, 'R'))
    # ---- right: pin 22 / pin 28 test points, pin-22 Sierra VBUS_SENSE option (DNP), hanging below the pin-22 row ----
    y22 = jy(f'S{n}_M2_GPIO6')
    place_pin(h['tps'][f'S{n}_M2_GPIO6'], '1', Rt + 7.62, y22)
    place_pin(h['tps'][f'S{n}_M2_GPIO8'], '1', Rt + 12.7, jy(f'S{n}_M2_GPIO8'))
    vpart(h['Rvbus'], Rt + 33.02, jy(f'S{n}_M2_IFSEL') + 7.62, f'S{n}_M2_GPIO6'); h['Rvbus'].fstyle = 'right'
    # ---- right: SIM bundle -> filter caps / ESD -> holder ----
    xs = Rt + 40.64
    yc = jy(f'SIM{n}_CD') + 5.08
    sc = [h['Csim'][0], h['Csim'][1], h['Cf']['RST'], h['Cf']['CLK'], h['Cf']['IO']]
    for c in sc:
        vpart(c, xs, yc); c.fstyle = 'right'; xs += 15.24
    E = h['ESD']; E.fstyle = 'belowright'
    place_pin(E, f'SIM{n}_VCC', xs + 7.62, yc + 12.7)
    SIM = h['SIM']; SIM.fstyle = 'right'
    place_pin(SIM, f'SIM{n}_VCC', xs + 63.5, jy(f'SIM{n}_VCC'))
    place(h['H'], X0 + 63.5, Y0 + 60.96)
    place(h['H42'], X0 + 88.9, Y0 + 60.96)
    # ---- pin 20 host-interface select: NFET (gate = S_PCIE_EN_L) + Sierra DNP pull-up to +1V8; pin 20 net drawn with labels ----
    Qs = h['Qsel']; Qs.fstyle = 'right'
    place_pin(Qs, f'SLOT{n}_PCIE_SEL', xn - 40.64, b_in[1] + 27.94)
    g_ = tip(Qs, f'SLOT{n}_PCIE_SEL')
    pullup_on(h['Rselpu'], g_[0] - 7.62, g_[1], '+3V3'); h['Rselpu'].fstyle = 'left'
    P(s, f'SLOT{n}_PCIE_SEL', g_[0] - 17.78, g_[1], 'L')
    y20 = jy(f'S{n}_M2_IFSEL')
    pullup_on(h['Rsel'], Rt + 12.7, y20 + 15.24, '+1V8'); h['Rsel'].fstyle = 'right'
    h['note'].x, h['note'].y = 20.32, 300.0

def fan(s, rows, side, x0, step=2.54):
    """rows: list of (net, (px,py), ty, xend). Draw non-crossing fan-out buses from pin tips to target rows.
    side 'R': pins on the right edge going right; 'L': going left."""
    sg = 1 if side == 'R' else -1
    rows = sorted(rows, key=lambda r: r[1][1])
    ups = [r for r in rows if r[2] < r[1][1] - 0.01]
    dns = [r for r in rows if r[2] > r[1][1] + 0.01][::-1]
    turn = {}
    for i, r in enumerate(ups): turn[r[0]] = x0 + sg * step * i
    for i, r in enumerate(dns): turn[r[0]] = x0 + sg * step * i
    for net, (px, py), ty, xend in rows:
        if net in turn:
            xt = turn[net]
            s.bus(net, [(px, py), (xt, py), (xt, ty), (xend, ty)])
        else:
            s.bus(net, [(px, py), (xend, ty)])

def spread(n_or_gaps, yc):
    """gaps list -> absolute ys centred on yc"""
    ys = [0.0]
    for g in n_or_gaps: ys.append(ys[-1] + g)
    off = snap(yc - ys[-1] / 2)
    return [snap(off + y) for y in ys]

def lay_pcie(h):
    s = h['s']; s.paper = 'A1'
    UA, UB, UC, J = h['UA'], h['UB'], h['UC'], h['J']
    place(UA, 251.46, 170.18); place(J, 76.2, 160.02)
    UA.fstyle = 'big'
    t = lambda it, n: tip(it, n)
    # ---------- upstream: edge -> switch ----------
    s.bus('PCIE_REFCLK_P', [t(J, 'PCIE_REFCLK_P'), t(UA, 'PCIE_REFCLK_P')])
    vpart(h['Rclk'][0], 106.68, t(J, 'PCIE_REFCLK_P')[1], 'PCIE_REFCLK_P'); h['Rclk'][0].fstyle = 'right'
    vpart(h['Rclk'][1], 124.46, t(J, 'PCIE_REFCLK_N')[1], 'PCIE_REFCLK_N'); h['Rclk'][1].fstyle = 'right'
    xs = 205.74
    for net in ('PCIE_REFCLK_N', 'UP_RX_P', 'UP_RX_N'):
        a = t(J, net); b = t(UA, net)
        s.bus(net, [a, (xs, a[1]), (xs, b[1]), b]); xs += 2.54
    for i, (c, xl) in enumerate(((h['Cup'][0], 129.54), (h['Cup'][1], 152.4))):
        acn = 'UP_TX_P_AC' if i == 0 else 'UP_TX_N_AC'; dcn = 'UP_TX_P' if i == 0 else 'UP_TX_N'
        y = t(J, acn)[1]
        hpart(c, xl, y, acn); c.fstyle = 'above2' if i == 0 else 'below2'
        s.bus(acn, [t(J, acn), (xl, y)])
        b = t(UA, dcn)
        s.bus(dcn, [(xl + 7.62, y), (xs, y), (xs, b[1]), b]); xs += 2.54
    rr = t(UA, 'RESREF'); vpart(h['Rresref'], rr[0] - 7.62, rr[1], 'RESREF'); h['Rresref'].fstyle = 'left'
    # ---------- downstream: switch -> AC caps / 0R -> slot ports ----------
    rows = []
    G = [60.96, 116.84, 172.72]
    XA, XB = 299.72, 312.42
    for n in (1, 2, 3):
        g = G[n - 1]; d = h['dn'][n]
        spec = [(f'SW_TX{n}_P', g, XA), (f'SW_TX{n}_N', g + 5.08, XB), (f'SLOT{n}_PCIE_TX_P', g + 12.7, 360.68), (f'SLOT{n}_PCIE_TX_N', g + 15.24, 360.68),
                (f'SW_CLK{n}_P', g + 22.86, XA), (f'SW_CLK{n}_N', g + 35.56, XB)]
        for net, ty, xe in spec:
            rows.append((net, t(UA, net), ty, xe))
        hpart(d['Ctx'][0], XA, g, f'SW_TX{n}_P'); d['Ctx'][0].fstyle = 'above2'
        hpart(d['Ctx'][1], XB, g + 5.08, f'SW_TX{n}_N'); d['Ctx'][1].fstyle = 'below2'
        hpart(d['Rck'][0], XA, g + 22.86, f'SW_CLK{n}_P'); d['Rck'][0].fstyle = 'above2'
        hpart(d['Rck'][1], XB, g + 35.56, f'SW_CLK{n}_N'); d['Rck'][1].fstyle = 'above2'
        vpart(d['Rterm'][0], 332.74, g + 22.86, f'SLOT{n}_REFCLK_P'); d['Rterm'][0].fstyle = 'right'
        vpart(d['Rterm'][1], 345.44, g + 35.56, f'SLOT{n}_REFCLK_N'); d['Rterm'][1].fstyle = 'right'
        for net, y in ((f'SLOT{n}_PCIE_RX_P', g), (f'SLOT{n}_PCIE_RX_N', g + 5.08), (f'SLOT{n}_REFCLK_P', g + 22.86), (f'SLOT{n}_REFCLK_N', g + 35.56),
                       (f'SLOT{n}_PCIE_TX_P', g + 12.7), (f'SLOT{n}_PCIE_TX_N', g + 15.24)):
            P(s, net, 360.68, y, 'R')
    fan(s, rows, 'R', 271.78)
    # ---------- unit B: straps / EEPROM / I2C (left), CLKREQ / PORTGOOD / PDC (right) ----------
    UBX, UBY = 251.46, 398.78
    place(UB, UBX, UBY); UB.fstyle = 'big'
    left = [tt for tt in UB.tips() if tt['o'] == (-1, 0) and tt['net'] != 'NC']
    left.sort(key=lambda tt: tt['y'])
    ys = spread([12.7] * (len(left) - 1), UBY)
    XS = 180.34
    lrows = []
    rowy = {}
    for tt, ty in zip(left, ys):
        net = tt['net']; rowy[net] = ty
        lrows.append((net, (tt['x'], tt['y']), ty, 160.02 if net not in ('SW_PERST_N',) else 160.02))
    # per-row elements
    for net, R_ in h['Rpd'].items():
        vpart(R_, XS, rowy[net], net); R_.fstyle = 'right'
    for net, R_ in h['Rpu'].items():
        if net in rowy:
            place_pin(R_, net, XS - 10.16, rowy[net], 'D'); R_.fstyle = 'right'
    place_pin(h['tps']['SW_FATAL_N'], '1', XS - 30.48, rowy['SW_FATAL_N'])
    place_pin(h['tps']['SW_INTA_N'], '1', XS - 30.48, rowy['SW_INTA_N'])
    vpart(h['Rl11'], XS - 40.64, rowy['SW_INTA_N'], 'SW_INTA_N'); h['Rl11'].fstyle = 'right'
    place_pin(h['Rbuf'], 'SW_PERST_N', XS, rowy['SW_PERST_N'], 'D'); h['Rbuf'].fstyle = 'right'
    # trim rows: straps end at XS-?, EE/PCA rows run further left
    ends = {}
    for net, *_ in lrows:
        ends[net] = XS if net in h['Rpd'] else XS - 10.16
    for net in ('SW_FATAL_N',): ends[net] = XS - 30.48
    for net in ('SW_INTA_N',): ends[net] = XS - 40.64
    for net in ('EE_SCK', 'EE_SI', 'EE_SO', 'EE_CS_N', 'SW_SCL_1V8', 'SW_SDA_1V8'): ends[net] = XS - 10.16
    ends['SW_PERST_N'] = 160.02
    lrows = [(n_, p_, ty, ends[n_]) for n_, p_, ty, _ in lrows]
    fan(s, lrows, 'L', 218.44)
    # PERST buffer on the SW_PERST_N row
    Ub = h['Ubuf']; Ub.fstyle = 'belowright'
    place_pin(Ub, 'SW_PERST_N', 160.02, rowy['SW_PERST_N'])
    ib = t(Ub, 'PCIE_PERST_N'); vb = t(Ub, '+1V8')
    pj = t(J, 'PCIE_PERST_N')
    s.bus('PCIE_PERST_N', [pj, (99.06, pj[1]), (99.06, ib[1]), ib])
    s.bus('PCIE_PERST_N', [(86.36, ib[1]), (99.06, ib[1])])
    P(s, 'PCIE_PERST_N', 86.36, ib[1], 'L')
    vpart(h['Rperst'], 106.68, ib[1], 'PCIE_PERST_N'); h['Rperst'].fstyle = 'right'
    place_pin(h['tpperst'], '1', 116.84, ib[1]); h['tpperst'].fstyle = 'above2'
    s.bus('+1V8', [vb, (vb[0], vb[1] - 5.08), (vb[0] + 25.4, vb[1] - 5.08)])
    vpart(h['Cbuf'], vb[0] + 25.4, vb[1] - 5.08, '+1V8'); h['Cbuf'].fstyle = 'right'
    s.cluster('+1V8', [Ub, h['Cbuf']], at=(vb[0], vb[1] - 5.08, 'U'))
    # EEPROM + PCA9306 further left
    EE = h['EE']; EE.fstyle = 'belowright'
    place_pin(EE, 'EE_SI', 132.08, rowy['EE_SI'])
    e8 = t(EE, '8')
    vpart(h['Cee'], e8[0] - 17.78, e8[1] - 10.16, '+1V8'); h['Cee'].fstyle = 'right'
    PCA = h['PCA']; PCA.mirror = True; PCA.fstyle = 'belowright'
    place_pin(PCA, 'SW_SCL_1V8', 101.6, rowy['SW_SCL_1V8'] + 12.7)
    i2 = t(PCA, 'I2C_SCL'); i3 = t(PCA, 'I2C_SDA')
    P(s, 'I2C_SCL', i2[0] - 12.7, i2[1], 'L'); P(s, 'I2C_SDA', i3[0] - 12.7, i3[1] + 5.08, 'L')
    vr = t(PCA, '7')
    place_pin(h['Rvref'], 'PCA_VREF2', vr[0], vr[1] - 10.16, 'D'); h['Rvref'].fstyle = 'right'
    s.bus('PCA_VREF2', [vr, (vr[0], vr[1] - 10.16)])
    s.bus('PCA_VREF2', [(vr[0], vr[1] - 5.08), (vr[0] - 17.78, vr[1] - 5.08)])
    vpart(h['Cvref'], vr[0] - 17.78, vr[1] - 5.08, 'PCA_VREF2'); h['Cvref'].fstyle = 'left'
    place_pin(h['fvref'], '1', vr[0] - 10.16, vr[1] - 5.08)
    # ---------- unit B right side ----------
    right = [tt for tt in UB.tips() if tt['o'] == (1, 0) and tt['net'] != 'NC']
    right.sort(key=lambda tt: tt['y'])
    gaps = []
    for a_, b_ in zip(right, right[1:]):
        gaps.append(12.7 if 'CLKREQ' in a_['net'] or 'CLKREQ' in b_['net'] else 10.16)
    ys = spread(gaps, UBY - 12.7)
    rrows = []
    for tt, ty in zip(right, ys):
        net = tt['net']
        if 'CLKREQ' in net:
            place_pin(h['Rpu'][net], net, 309.88, ty, 'D'); h['Rpu'][net].fstyle = 'right'
            if net == 'UP_CLKREQ_N':
                place_pin(h['tps']['UP_CLKREQ_N'], '1', 325.12, ty); xe = 325.12
            else:
                P(s, net, 330.2, ty, 'R'); xe = 330.2
        elif net.startswith('PORTGOOD'):
            p = net[8]
            Rl, Dl = h['pg'][p]
            hpart(Dl, 304.8, ty, net); Dl.fstyle = 'above2'
            hpart(Rl, 317.5, ty, f'PGLED{p}_A'); Rl.fstyle = 'above2'
            xe = 304.8
        else:
            i = ('PDC1_N', 'PDC4_N', 'PDC5_N').index(net)
            hpart(h['Rpdc'][i], 304.8, ty, net); h['Rpdc'][i].fstyle = 'above2'
            xe = 304.8
        rrows.append((net, (tt['x'], tt['y']), ty, xe))
    fan(s, rrows, 'R', 284.48)
    # ---------- unit C: supply rails with decoupling combs ----------
    place(UC, 800.1, 200.66); UC.fstyle = 'belowright'
    def row(net, caps, extra_x=None):
        p = t(UC, net)
        x = caps_on(caps, p[0] - 15.24, p[1], net, step=17.78 if len(caps) > 4 else None, direction=-1)
        return x, p
    x, p = row('+0V95', h['c095'])
    s.bus('+0V95', [p, (x, p[1])])
    s.cluster('+0V95', [UC] + h['c095'], at=(x, p[1], 'L'))
    for net, caps, fb, rail in (('+0V95_CLK', h['c095c'], h['fb095'], '+0V95'), ('+1V8_CLK', h['c18c'], h['fb18c'], '+1V8'),
                                ('+1V8_VPH', h['c18v'], h['fb18v'], '+1V8')):
        x, p = row(net, caps)
        place_pin(h['flags'][net], '1', p[0] - 7.62, p[1])
        hpart(fb, x - 7.62, p[1], rail); fb.fstyle = 'above2'
        s.bus(net, [p, (x, p[1])])
    x, p = row('+1V8', h['c18'])
    s.bus('+1V8', [p, (x - 5.08, p[1])])
    s.cluster('+1V8', [UC] + h['c18'], at=(x - 5.08, p[1], 'L'))
    h['note'].x, h['note'].y = 400.0, 470.0

def lay_hub(h):
    s = h['s']; s.paper = 'A2'
    J, HD, U = h['J'], h['HD'], h['U']
    t = lambda it, n: tip(it, n)
    place(J, 50.8, 223.52); place(HD, 152.4, 233.68); place(U, 294.64, 246.38)
    HD.fstyle = 'belowright'; U.fstyle = 'big'; J.fstyle = 'above2'
    # connector -> mux: straight lines (CC + SS pairs)
    for net in ('CC1', 'CC2', 'C_RX1_N', 'C_RX1_P', 'C_TX1_N', 'C_TX1_P', 'C_RX2_N', 'C_RX2_P', 'C_TX2_N', 'C_TX2_P'):
        s.bus(net, [t(J, net), t(HD, net)])
    # ESD arrays hang below the bundle
    E1, E2, E3 = h['E1'], h['E2'], h['E3']
    for E, x in ((E3, 86.36), (E1, 106.68), (E2, 127.0)):
        E.fstyle = 'belowright'
    place(E1, 99.06, 284.48); place(E2, 99.06, 317.5); place(E3, 99.06, 350.52)
    # USB2 D+/D- : up and over the mux to the hub
    dm = [tt for tt in J.tips() if tt['net'] == 'USBC_DM']; dp = [tt for tt in J.tips() if tt['net'] == 'USBC_DP']
    dm.sort(key=lambda q: -q['y']); dp.sort(key=lambda q: -q['y'])
    s.bus('USBC_DM', [(dm[0]['x'], dm[0]['y']), (71.12, dm[0]['y']), (71.12, 162.56), (259.08, 162.56), (259.08, t(U, 'USBC_DM')[1]), t(U, 'USBC_DM')])
    s.bus('USBC_DM', [(dm[1]['x'], dm[1]['y']), (71.12, dm[1]['y'])])
    s.bus('USBC_DP', [(dp[0]['x'], dp[0]['y']), (73.66, dp[0]['y']), (73.66, 165.1), (261.62, 165.1), (261.62, t(U, 'USBC_DP')[1]), t(U, 'USBC_DP')])
    s.bus('USBC_DP', [(dp[1]['x'], dp[1]['y']), (73.66, dp[1]['y'])])
    # VBUS rail line
    vb = t(J, 'VBUS_C'); YV = 177.8
    fb = h['FB5']; hpart(fb, 104.14, YV, 'VBUS_C'); fb.fstyle = 'above2'
    s.bus('VBUS_C', [vb, (68.58, vb[1]), (68.58, YV), (104.14, YV)])
    vpart(h['TVS'], 78.74, YV, 'VBUS_C'); h['TVS'].fstyle = 'right'
    vpart(h['Cvbus'], 93.98, YV, 'VBUS_C'); h['Cvbus'].fstyle = 'right'
    place_pin(h['fvbus'], '1', 86.36, YV)
    v5 = t(HD, 'HD_VDD5')
    s.bus('HD_VDD5', [(109.22, YV), (v5[0], YV), v5])
    vpart(h['C5'][0], 121.92, YV, 'HD_VDD5'); h['C5'][0].fstyle = 'right'
    vpart(h['C5'][1], 137.16, YV, 'HD_VDD5'); h['C5'][1].fstyle = 'right'
    place_pin(h['f5'], '1', 129.54, YV)
    c3 = t(HD, '+3V3')
    vpart(h['C33'], c3[0] + 17.78, c3[1] - 5.08, '+3V3'); h['C33'].fstyle = 'right'
    # VBUS detect for the mux (910k) at the mux pin
    vd = t(HD, 'HD_VBUS_DET')
    hpart(h['Rvd'], vd[0] - 25.4, vd[1] + 0, 'VBUS_C'); h['Rvd'].fstyle = 'below2'
    # shield
    sh = t(J, 'SHIELD_C')
    s.bus('SHIELD_C', [sh, (sh[0], sh[1] + 10.16), (sh[0] + 27.94, sh[1] + 10.16)])
    vpart(h['Rsh'], sh[0] + 12.7, sh[1] + 10.16, 'SHIELD_C'); h['Rsh'].fstyle = 'right'
    vpart(h['Csh'], sh[0] + 27.94, sh[1] + 10.16, 'SHIELD_C'); h['Csh'].fstyle = 'right'
    # mux -> hub upstream (TX AC caps)
    for i, (c, xl) in enumerate(((h['Cup'][0], 182.88), (h['Cup'][1], 200.66))):
        ac = 'HUB_UP_TX_P_AC' if i == 0 else 'HUB_UP_TX_N_AC'; dc = 'HUB_UP_TX_P' if i == 0 else 'HUB_UP_TX_N'
        y = t(HD, ac)[1]
        hpart(c, xl, y, ac); c.fstyle = 'above' if i == 0 else 'below'
        s.bus(ac, [t(HD, ac), (xl, y)]); s.bus(dc, [(xl + 7.62, y), t(U, dc)])
    for net in ('HUB_UP_RX_P', 'HUB_UP_RX_N'):
        s.bus(net, [t(HD, net), t(U, net)])
    # DIR pull-up + TP
    dr = t(HD, 'HD_DIR')
    place_pin(h['tpdir'], '1', dr[0] + 5.08, dr[1]); h['tpdir'].fstyle = 'below2'
    place_pin(h['Rdir'], 'HD_DIR', dr[0] + 15.24, dr[1], 'U'); h['Rdir'].fstyle = 'right'
    # crystal (vertical) on XI/XO, load caps horizontal to GND, 1M across
    xi = t(U, 'HUB_XI'); xo = t(U, 'HUB_XO')
    Y = h['Y']; Y.rot = 90
    place_pin(Y, 'HUB_XI', 248.92, xi[1], 'U'); Y.fstyle = 'right'
    hpart(h['Cx'][0], 223.52, xi[1], 'GND'); h['Cx'][0].fstyle = 'above2'
    hpart(h['Cx'][1], 223.52, xo[1], 'GND'); h['Cx'][1].fstyle = 'below2'
    place_pin(h['Rx'], 'HUB_XI', 238.76, xi[1], 'U'); h['Rx'].fstyle = 'left'
    s.bus('HUB_XI', [(231.14, xi[1]), xi]); s.bus('HUB_XO', [(231.14, xo[1]), xo])
    # lower-left pins fanned to 12.7mm rows
    names = ['HUB_RBIAS', 'HUB_RESET_N', 'HUB_VBUS_DET', 'I2C_SCL', 'I2C_SDA', 'HUB_CFG_BC', 'HUB_CFG_NONREM']
    ys = [t(U, 'HUB_RBIAS')[1] + 2.54 + 12.7 * i for i in range(len(names))]
    ys[0] = t(U, 'HUB_RBIAS')[1]
    rows = []
    XC = 236.22
    for net, y in zip(names, ys):
        xe = {'HUB_RBIAS': 233.68, 'HUB_RESET_N': 205.74, 'HUB_VBUS_DET': 218.44, 'I2C_SCL': 213.36, 'I2C_SDA': 213.36,
              'HUB_CFG_BC': XC, 'HUB_CFG_NONREM': XC}[net]
        rows.append((net, t(U, net), y, xe))
    fan(s, rows, 'L', 261.62)
    ry = dict((n_, y_) for n_, _, y_, _ in rows)
    hpart(h['Rbias'], 226.06, ry['HUB_RBIAS'], 'GND'); h['Rbias'].fstyle = 'below2'
    place_pin(h['Rrst'], 'HUB_RESET_N', XC, ry['HUB_RESET_N'], 'D'); h['Rrst'].fstyle = 'right'
    vpart(h['Crst'], XC - 12.7, ry['HUB_RESET_N'], 'HUB_RESET_N'); h['Crst'].fstyle = 'right'
    place_pin(h['tprst'], '1', XC - 22.86, ry['HUB_RESET_N']); h['tprst'].fstyle = 'above2'
    P(s, 'HUB_RESET_N', 205.74, ry['HUB_RESET_N'], 'L')
    vpart(h['Rvb'][1], XC, ry['HUB_VBUS_DET'], 'HUB_VBUS_DET'); h['Rvb'][1].fstyle = 'right'
    hpart(h['Rvb'][0], 218.44 - 7.62, ry['HUB_VBUS_DET'], 'VBUS_C'); h['Rvb'][0].fstyle = 'above2'
    for i, net in enumerate(('I2C_SCL', 'I2C_SDA')):
        place_pin(h['Rsm'][i], net, XC - 7.62, ry[net], 'D'); h['Rsm'][i].fstyle = 'right'
        P(s, net, 213.36, ry[net], 'L')
    vpart(h['Rbc'], XC, ry['HUB_CFG_BC'], 'HUB_CFG_BC'); h['Rbc'].fstyle = 'right'
    place_pin(h['Rnr'], 'HUB_CFG_NONREM', XC - 7.62, ry['HUB_CFG_NONREM'], 'D'); h['Rnr'].fstyle = 'right'
    # downstream: USB2 + USB3 to slot ports, hub TX through AC caps
    XA, XB, XP = 335.28, 350.52, 375.92
    for n in (1, 2, 3):
        for net in (f'SLOT{n}_USB2_DP', f'SLOT{n}_USB2_DM', f'SLOT{n}_USB3_TX_P', f'SLOT{n}_USB3_TX_N'):
            P(s, net, XP, t(U, net)[1], 'R')
        cp, cn = h['Cdn'][n]
        yp_ = t(U, f'HUB_DN{n}_TX_P')[1]; yn_ = t(U, f'HUB_DN{n}_TX_N')[1]
        hpart(cp, XA, yp_, f'HUB_DN{n}_TX_P'); cp.fstyle = 'above'
        hpart(cn, XB, yn_, f'HUB_DN{n}_TX_N'); cn.fstyle = 'below'
        P(s, f'SLOT{n}_USB3_RX_P', XP, yp_, 'R'); P(s, f'SLOT{n}_USB3_RX_N', XP, yn_, 'R')
    for i, net in enumerate(('PRT_DIS_P4', 'PRT_DIS_M4')):
        hpart(h['Rp4'][i], 335.28, t(U, net)[1], net); h['Rp4'][i].fstyle = 'above'
    # supply decoupling above the hub
    p3 = t(U, '+3V3'); p12 = t(U, '+1V2')
    y3, y12 = p3[1] - 25.4, p3[1] - 12.7
    x = caps_on(h['c33'], p3[0] + 22.86, y3, '+3V3')
    s.bus('+3V3', [p3, (p3[0], y3), (x, y3)])
    s.cluster('+3V3', [U] + h['c33'], at=(x, y3, 'R'))
    x = caps_on(h['c12'], p12[0] + 12.7, y12, '+1V2')
    s.bus('+1V2', [p12, (p12[0], y12), (x, y12)])
    s.cluster('+1V2', [U] + h['c12'], at=(x, y12, 'R'))
    h['note'].x, h['note'].y = 20.32, 382.0

def lay_control(h):
    s = h['s']; s.paper = 'A2'
    J = h['J']; U1, U2 = h['U']
    t = lambda it, n: tip(it, n)
    place(J, 50.8, 101.6); J.fstyle = 'above2'
    jl = lambda net: t(J, net)
    scl, sda, intn, rst, sen = jl('I2C_SCL'), jl('I2C_SDA'), jl('EXP_INT_N'), jl('EXP_RESET_N'), jl('CARRIER_3V3_SENSE')
    TS, TD, TI, TR = 139.7, 144.78, 149.86, 154.94
    YS, YD, YR, YI = 50.8, 68.58, 86.36, 129.54
    # expanders: U2 (inputs) on top, U1 (outputs) below; left tips at XL
    XL = 172.72
    for U, ysc in ((U2, 154.94), (U1, 312.42)):
        place(U, 200, 200)
        a = t(U, 'I2C_SCL')
        place(U, 200 + XL - a[0], 200 + ysc - a[1])
        U.fstyle = 'belowright'
    yb = t(U1, 'EXP_RESET_N')[1]
    # header -> rows -> vertical trunks -> both expanders
    s.bus('I2C_SCL', [scl, (scl[0] - 5.08, scl[1]), (scl[0] - 5.08, YS), (TS, YS), (TS, t(U1, 'I2C_SCL')[1]), t(U1, 'I2C_SCL')])
    s.bus('I2C_SCL', [(TS, t(U2, 'I2C_SCL')[1]), t(U2, 'I2C_SCL')])
    s.bus('EXP_INT_N', [intn, (intn[0] - 10.16, intn[1]), (intn[0] - 10.16, YI), (TI, YI), (TI, t(U1, 'EXP_INT_N')[1]), t(U1, 'EXP_INT_N')])
    s.bus('EXP_INT_N', [(TI, t(U2, 'EXP_INT_N')[1]), t(U2, 'EXP_INT_N')])
    s.bus('I2C_SDA', [sda, (sda[0] + 5.08, sda[1]), (sda[0] + 5.08, YD), (TD, YD), (TD, t(U1, 'I2C_SDA')[1]), t(U1, 'I2C_SDA')])
    s.bus('I2C_SDA', [(TD, t(U2, 'I2C_SDA')[1]), t(U2, 'I2C_SDA')])
    s.bus('EXP_RESET_N', [rst, (rst[0] + 15.24, rst[1]), (rst[0] + 15.24, YR), (TR, YR), (TR, yb), t(U1, 'EXP_RESET_N')])
    s.bus('EXP_RESET_N', [(TR, t(U2, 'EXP_RESET_N')[1]), t(U2, 'EXP_RESET_N')])
    s.bus('I2C_SCL', [(scl[0] - 5.08, YS), (25.4, YS)]); P(s, 'I2C_SCL', 25.4, YS, 'L')
    s.bus('I2C_SDA', [(sda[0] + 5.08, YD), (25.4, YD)]); P(s, 'I2C_SDA', 25.4, YD, 'L')
    # pull-ups / test points on the header rows
    for r, y in ((h['Ri2c'][0], YS), (h['Ri2c'][1], YD), (h['Rrst'], YR)):
        place_pin(r, other_net(r, '+3V3'), 88.9, y, 'D'); r.fstyle = 'right'
    place_pin(h['Rint'], 'EXP_INT_N', 88.9, YI, 'D'); h['Rint'].fstyle = 'right'
    for net, y in (('I2C_SCL', YS), ('I2C_SDA', YD), ('EXP_INT_N', YI)):
        place_pin(h['tps'][net], '1', 111.76, y); h['tps'][net].fstyle = 'above2'
    s.bus('CARRIER_3V3_SENSE', [sen, (sen[0] + 30.48, sen[1])])
    place_pin(h['Rsense'], 'CARRIER_3V3_SENSE', sen[0] + 30.48, sen[1], 'D'); h['Rsense'].fstyle = 'right'
    # supply decoupling above each expander
    for U, cs in ((U2, h['Cu'][1]), (U1, h['Cu'][0])):
        vi = [tt for tt in U.tips() if tt['net'] == '+3V3' and tt['y'] < U.bbox()[1] + 0.1 + 0]
        tops = sorted([tt for tt in U.tips() if tt['net'] == '+3V3' and abs(tt['y'] - min(q['y'] for q in U.tips())) < 0.1], key=lambda q: q['x'])
        yl = tops[0]['y'] - 12.7
        x = caps_on(cs, tops[-1]['x'] + 10.16, yl, '+3V3')
        s.bus('+3V3', [(tops[0]['x'], tops[0]['y']), (tops[0]['x'], yl), (x, yl)])
        s.bus('+3V3', [(tops[-1]['x'], tops[-1]['y']), (tops[-1]['x'], yl)])
        s.cluster('+3V3', [U] + cs, at=(x, yl, 'R'))
    # U1 outputs: straight to hierarchical ports
    xr1 = t(U1, 'SLOT1_PWR_EN')[0]
    for net in ('SLOT1_PWR_EN', 'SLOT1_FCPO_N', 'SLOT1_RESET', 'SLOT1_WDIS', 'SLOT1_PCIE_EN', 'SLOT2_PWR_EN', 'SLOT2_FCPO_N', 'SLOT2_RESET',
                'SLOT2_WDIS', 'SLOT2_PCIE_EN', 'SLOT3_PWR_EN', 'SLOT3_FCPO_N', 'SLOT3_RESET', 'SLOT3_WDIS', 'SLOT3_PCIE_EN', 'HUB_RESET_N'):
        P(s, net, xr1 + 15.24, t(U1, net)[1], 'R')
    # U2 inputs: fan out to rows; PG rows carry an LED driver
    order = ['SLOT1_PG', 'SLOT2_PG', 'SLOT3_PG', 'SLOT1_WAKE_N', 'SLOT2_WAKE_N', 'SLOT3_WAKE_N', 'PG_3V3', 'PG_0V95', 'PG_1V8', 'PG_1V2',
             'USER_LED1', 'USER_LED2', 'SLOT1_PCIE_SEL', 'SLOT2_PCIE_SEL', 'SLOT3_PCIE_SEL', 'EXP_SPARE7']
    gaps = [30.48, 30.48, 12.7, 5.08, 5.08, 12.7 + 10.16, 30.48, 30.48, 30.48, 15.24, 10.16, 10.16, 7.62, 7.62, 7.62]
    pins = [t(U2, n) for n in order]
    ys = spread(gaps, (pins[0][1] + pins[-1][1]) / 2)
    X0 = pins[0][0] + 40.64
    XJ = X0 + 45.72; XG = XJ + 38.1
    rows = []
    for net, p, y in zip(order, pins, ys):
        if net.endswith('PG') or net.startswith('PG_'):
            xe = XG
        elif 'WAKE' in net or 'PCIE_SEL' in net:
            xe = XJ
        elif net.startswith('USER'):
            xe = XJ - 12.7
        else:
            xe = XJ - 12.7
        rows.append((net, p, y, xe))
    fan(s, rows, 'R', X0)
    ry = dict((r[0], r[2]) for r in rows)
    pgl = dict((e[0], e) for e in h['pg'])
    for net in order:
        y = ry[net]
        if net in pgl:
            _, R_, D_, Q_ = pgl[net]
            s.bus(net, [(XJ, y), (XJ, y + 5.08), (XJ + 2.54, y + 5.08)])
            P(s, net, XJ + 2.54, y + 5.08, 'R')
            place_pin(Q_, net, XG, y); Q_.fstyle = 'right'
            d = [tt for tt in Q_.tips() if tt['net'] != net and tt['net'] != 'GND'][0]
            vpart(D_, d['x'], y - 17.78, other_net(D_, d['net'])); D_.fstyle = 'right'
            hpart(R_, d['x'] - 12.7, y - 17.78, '+3V3'); R_.fstyle = 'above'
        elif 'WAKE' in net or 'PCIE_SEL' in net:
            P(s, net, XJ, y, 'R')
        elif net.startswith('USER'):
            r_, d_ = h['ul'][0 if net.endswith('1') else 1]
            hpart(r_, XJ - 12.7, y, net); r_.fstyle = 'above'
            hpart(d_, XJ + 2.54, y, other_net(d_, 'GND')); d_.fstyle = 'above'
        else:
            tp = h['tpsp'][int(net[-1]) - 7]
            place_pin(tp, '1', XJ - 12.7, y); tp.fstyle = 'right'
    for i, m in enumerate(h['MH']):
        place(m, 30.48 + 15.24 * i, 393.7)
    h['note'].x, h['note'].y = 254.0, 17.78

def place_all(D, H, only):
    if not only or 'power_input.kicad_sch' in only:
        lay_power_input(H['pin'])
    if not only or 'pcie_switch.kicad_sch' in only:
        lay_pcie(H['pcie'])
    for n in (1, 2, 3):
        if not only or f'slot{n}.kicad_sch' in only:
            lay_slot(H[f'slot{n}'], n)
    if not only or 'usb_hub.kicad_sch' in only:
        lay_hub(H['hub'])
    if not only or 'wwan_power.kicad_sch' in only:
        lay_wwan_power(H['wp'])
    if not only or 'control.kicad_sch' in only:
        lay_control(H['ctl'])

