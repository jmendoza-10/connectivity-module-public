from engine import make_symbol
from pi7c_pins import P as PI7C

def T(num, nm, typ='passive'): return (str(num), nm, typ)
def S(nums, nm, typ='passive'): return [T(n, nm, typ) for n in nums]   # stacked pins (same net)

# ---- TI LM74800-Q1 (LM7480x-Q1 DS SNOSD95C, Table 6-1, DRR-12) ----
make_symbol('LM74800-Q1', 'U', 'LM74800QDRRRQ1', [dict(
    left=[T(2, 'A'), None, None, T(4, 'SW'), None, None, None, None, T(5, 'OV', 'input')],
    right=[T(11, 'CAP'), None, None, T(6, 'EN/UVLO', 'input'), None, None, T(9, 'OUT')],
    top=[T(1, 'DGATE', 'output'), None, None, None, [T(12, 'C'), T(10, 'VS', 'power_in'), T(3, 'VSNS')], None, None, None, T(8, 'HGATE', 'output')],
    bottom=[T(7, 'GND', 'power_in'), None, T(13, 'RTN', 'passive')])],
    footprint='Package_SON:WSON-12-1EP_3x3mm_P0.5mm_EP1.5x2.5mm', datasheet='https://www.ti.com/lit/ds/symlink/lm7480-q1.pdf',
    descr='Ideal diode + load-dump/OV controller, back-to-back NFET, AEC-Q100',
    fields={'FP_VERIFY': 'Land pattern vs TI DRR0012A; EP (RTN) must float'})

# ---- TI LM61460-Q1 / LMQ61460-Q1 (pin-compatible; DS SNVSB70F Table 7-1, RJR0014A) ----
make_symbol('LM61460-Q1', 'U', 'LM61460AASQRJRRQ1', [dict(
    left=[S((8, 12), 'VIN', 'power_in'), None, None, T(7, 'EN/SYNC', 'input'), None, None, T(6, 'RT')],
    right=[T(13, 'RBOOT'), None, T(14, 'CBOOT'), None, T(10, 'SW'), None, T(1, 'BIAS'), None, None, T(4, 'FB', 'input'), None, None, T(2, 'VCC'), None, None, T(5, 'PGOOD', 'open_collector')],
    bottom=[S((3, 9, 11), 'GND', 'power_in')])],
    footprint='', datasheet='https://www.ti.com/lit/ds/symlink/lm61460-q1.pdf',
    descr='36V 6A sync buck, AEC-Q100 (drop-in for LMQ61460-Q1)', fields={'FP_TODO': 'TI RJR0014A VQFN-HR-14 4x3.5mm - create footprint from TI land pattern'})

# ---- Diodes PI7C9X3G606GP (DS43484 Rev 5-2, FCA144 ball map) ----
def pi(b): n, t = PI7C[b]; return (b, n, t)
byname = {}
for b, (n, t) in PI7C.items(): byname.setdefault(n, []).append(b)
def pn(n): return pi(byname[n][0])
def stack(n): return [pi(b) for b in byname[n]]
uA_left = [pn('REFCLKP0'), pn('REFCLKN0'), None, pn('PERP0'), pn('PERN0'), None, pn('PETP0'), pn('PETN0'), None, None,
           pn('REFCLKP1'), pn('REFCLKN1'), None, pn('RESREF')]
uA_right = []
for lane, ck in ((1, 1), (2, 4), (3, 5)):
    uA_right += [pn(f'PETP{lane}'), pn(f'PETN{lane}'), None, pn(f'PERP{lane}'), pn(f'PERN{lane}'), None, pn(f'REFCLKOP{ck}'), pn(f'REFCLKON{ck}'), None, None]
uA_right += [pn('PETP4'), pn('PETN4'), pn('PERP4'), pn('PERN4'), pn('PETP5'), pn('PETN5'), pn('PERP5'), pn('PERN5'),
             pn('REFCLKOP6'), pn('REFCLKON6'), pn('REFCLKOP7'), pn('REFCLKON7')]
g = lambda n: pn(n)
uB_left = [g('PERST_L'), None, None, g('CHIPMODE1'), None, g('CHIPMODE0'), None, g('PORTCFG2'), None, g('PORTCFG1'), None, g('PORTCFG0'), None,
           g('CKMODE'), None, g('TEST'), None, g('TMS'), None, g('TRST_L'), None, g('JTAG_SEL_L'), None, g('FATAL_ERR_L/HOT_PLUG_EN_L'), None,
           g('INTA_L/PM_L11_EN_L'), None, None, g('EECK'), None, g('EEDI'), None, g('EEDO'), None, g('EECS_L'), None, None,
           g('SCL_I2C'), None, g('SDA_I2C'), None, g('SHCL_I2C'), None, g('SHDA_I2C'), None, g('SHPCINT_L'), None, None, g('TCK'), g('TDI'), g('TDO')]
gp = [b for b, (n, t) in PI7C.items() if n.startswith('GPIO')]
clk = {'GPIO9/CLKREQ_L1': 1, 'GPIO12/CLKREQ_L4': 4, 'GPIO13/CLKREQ_L5': 5, 'GPIO8/CLKREQ_L0': 0}
gpu = [b for b in gp if not any(PI7C[b][0].startswith(k) for k in clk)]
gpc = [b for k in ('GPIO8/CLKREQ_L0', 'GPIO9/CLKREQ_L1', 'GPIO12/CLKREQ_L4', 'GPIO13/CLKREQ_L5') for b in gp if PI7C[b][0].startswith(k)]
gpu.sort(key=lambda b: int(PI7C[b][0].split('/')[0][4:]))
uB_right = []
for b in gpc: uB_right += [pi(b), None]
uB_right += [None]
for i in (0, 1, 4, 5): uB_right += [pn(f'PORTGOOD_L{i}'), None]
for i in (1, 4, 5): uB_right += [pn(f'PDC_L{i}'), None]
uB_right += [pn('PORTGOOD_L6'), pn('PORTGOOD_L7'), pn('PDC_L6'), pn('PDC_L7')] + [pi(b) for b in gpu] + [pi(b) for b in byname['NC']]
pw_left = [stack('VDDC') + stack('VP')] + [None] * 7 + [stack('C_VDDC')] + [None] * 7 + [stack('VDDR')] + [None] * 7 + [stack('C_VDDR')] + [None] * 7 + [stack('VPH')]
pw = dict(left=pw_left, bottom=[stack('VSS')])
allb = [e for u in (uA_left, uA_right, uB_left, uB_right) for e in u if e] + [x for e in pw_left if e for x in e] + stack('VSS')
assert len(allb) == 144 and len({e[0] for e in allb}) == 144, len(allb)
make_symbol('PI7C9X3G606GP', 'U', 'PI7C9X3G606GP', [dict(left=uA_left, right=uA_right), dict(left=uB_left, right=uB_right), pw],
            footprint='Package_BGA:LFBGA-144_10x10mm_Layout12x12_P0.8mm', datasheet='https://www.diodes.com/assets/Datasheets/PI7C9X3G606GP.pdf',
            descr='PCIe Gen3 packet switch 6-port/6-lane, FCA144 10x10 0.8mm BGA (GPQ = AEC-Q100 Gr3)',
            fields={'FP_VERIFY': 'Generic LFBGA-144 0.8mm; verify ball/pad size vs Diodes FCA144 package drawing'})

# ---- Microchip USB5744 (DS00001855J, 56-VQFN) ----
u = lambda n, nm, t='bidirectional': T(n, nm, t)
make_symbol('USB5744', 'U', 'USB5744/2G9 (verify ordering suffix)', [dict(
    left=[u(46, 'USB2UP_DM'), u(45, 'USB2UP_DP'), None, u(47, 'USB3UP_TXDP', 'output'), u(48, 'USB3UP_TXDM', 'output'), None, u(50, 'USB3UP_RXDP', 'input'), u(51, 'USB3UP_RXDM', 'input'), None, None,
          u(54, 'XTALI/CLK_IN', 'input'), None, None, u(53, 'XTALO', 'output'), None, None, u(56, 'RBIAS', 'passive'), None, u(52, 'ATEST', 'passive'), None, None,
          u(42, 'RESET_N', 'input'), None, u(37, 'VBUS_DET', 'input'), None, None, u(38, 'SPI_CLK/SMCLK'), None, u(39, 'SPI_DO/SMDAT'), None, u(40, 'SPI_DI/CFG_BC_EN'), None, u(41, 'SPI_CE_N/CFG_NON_REM'), None, None,
          u(36, 'PRT_CTL1'), u(35, 'PRT_CTL2'), u(34, 'PRT_CTL3'), u(32, 'PRT_CTL4/GANG_PWR')],
    right=[u(1, 'USB2DN_DP1/PRT_DIS_P1'), u(2, 'USB2DN_DM1/PRT_DIS_M1'), None, u(3, 'USB3DN_TXDP1', 'output'), u(4, 'USB3DN_TXDM1', 'output'), None, u(6, 'USB3DN_RXDP1', 'input'), u(7, 'USB3DN_RXDM1', 'input'), None, None, None,
           u(8, 'USB2DN_DP2/PRT_DIS_P2'), u(9, 'USB2DN_DM2/PRT_DIS_M2'), None, u(10, 'USB3DN_TXDP2', 'output'), u(11, 'USB3DN_TXDM2', 'output'), None, u(13, 'USB3DN_RXDP2', 'input'), u(14, 'USB3DN_RXDM2', 'input'), None, None, None,
           u(17, 'USB2DN_DP3/PRT_DIS_P3'), u(18, 'USB2DN_DM3/PRT_DIS_M3'), None, u(19, 'USB3DN_TXDP3', 'output'), u(20, 'USB3DN_TXDM3', 'output'), None, u(22, 'USB3DN_RXDP3', 'input'), u(23, 'USB3DN_RXDM3', 'input'), None, None, None,
           u(24, 'USB2DN_DP4/PRT_DIS_P4'), None, u(25, 'USB2DN_DM4/PRT_DIS_M4'), None, u(26, 'USB3DN_TXDP4', 'output'), u(27, 'USB3DN_TXDM4', 'output'), u(29, 'USB3DN_RXDP4', 'input'), u(30, 'USB3DN_RXDM4', 'input')],
    top=[S((16, 31, 44, 55), 'VDD33', 'power_in'), None, None, None, S((5, 12, 15, 21, 28, 33, 43, 49), 'VDD12', 'power_in')],
    bottom=[T(57, 'VSS(EP)', 'power_in')])],
    footprint='Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm_ThermalVias', datasheet='https://ww1.microchip.com/downloads/en/DeviceDoc/USB5744-Data-Sheet-DS00001855J.pdf',
    descr='USB 3.2 Gen1 4-port hub controller', fields={'FP_VERIFY': 'EP size not confirmed vs Microchip 56-VQFN drawing'})

# ---- TI HD3SS3220 (SLLSES1E, RNH WQFN-30) ----
b_ = 'bidirectional'
make_symbol('HD3SS3220', 'U', 'HD3SS3220RNHR', [dict(
    left=[T(2, 'CC1', b_), T(1, 'CC2', b_), None, None, None, None, None, None, T(14, 'RX1n', b_), T(15, 'RX1p', b_), None, T(16, 'TX1n', b_), T(17, 'TX1p', b_), None,
          T(18, 'RX2n', b_), T(19, 'RX2p', b_), None, T(20, 'TX2n', b_), T(21, 'TX2p', b_), None, T(5, 'VBUS_DET', 'input'), None, None, T(22, 'ADDR', 'input'), T(3, 'CURRENT_MODE', 'input')],
    right=[T(6, 'TXp', b_), T(7, 'TXn', b_), None, T(9, 'RXp', b_), T(10, 'RXn', b_), None, None, T(11, 'DIR', 'open_collector'), None, T(27, 'ID', 'open_collector'),
           T(23, 'INT_N/OUT3', 'open_collector'), T(24, 'VCONN_FAULT_N', 'open_collector'), T(25, 'SDA/OUT1', b_), T(26, 'SCL/OUT2', b_)],
    top=[T(30, 'VDD5', 'power_in'), None, None, T(8, 'VCC33', 'power_in')],
    bottom=[S((13, 28, 31), 'GND', 'power_in'), None, T(4, 'PORT', 'input'), None, T(29, 'ENn_CC', 'input'), None, T(12, 'ENn_MUX', 'input')])],
    footprint='Package_DFN_QFN:Texas_RNH0030A_WQFN-30-1EP_2.5x4.5mm_P0.4mm_EP1.2x3.2mm', datasheet='https://www.ti.com/lit/ds/symlink/hd3ss3220.pdf',
    descr='USB-C DRP port controller + SS 2:1 mux')

# ---- TI TCA6416A (SCPS194F, TSSOP-24 PW) ----
make_symbol('TCA6416A', 'U', 'TCA6416APWR', [dict(
    left=[T(22, 'SCL', 'input'), T(23, 'SDA', 'bidirectional'), None, T(1, 'INT', 'open_collector'), None, T(3, 'RESET', 'input'), None, T(21, 'ADDR', 'input')],
    right=sum([[T(4 + i, f'P0{i}', 'bidirectional'), None] for i in range(8)], []) + sum([[T(13 + i, f'P1{i}', 'bidirectional'), None] for i in range(8)], [])[:-1],
    top=[T(2, 'VCCI', 'power_in'), None, None, T(24, 'VCCP', 'power_in')], bottom=[T(12, 'GND', 'power_in')])],
    footprint='Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm', datasheet='https://www.ti.com/lit/ds/symlink/tca6416a.pdf',
    descr='16-bit I2C GPIO expander, dual supply (TCA6416A-Q1 AEC option)')

# ---- M.2 Key-B socket (generic WWAN, PCI-SIG M.2 Socket 2 Key-B naming; vendor-specific use in brackets) ----
# Cross-checked against Sierra EM92XX PTS Rev 5 (Jan 2025) Table 2-1 and Telit FN990 HDG 1VV0301752 Rev 3 pin tables.
# EM92XX: 20=PCIE_DIS, 22=VBUS_SENSE, 24/38/68=optional VCC, 28=PLA_S2_N, 56/58=RFFE, 66=SIM1_DETECT, 73=GND.
# FN990 : 20=USB_PCIE_SWITCH, 22/24/28/62/64/68=TGPIO (1.8V), 40-48=UIM2, 56/58=I2C, 65=VREG_L6B_1P8, 66=UIM1_PRESENT, 73=GND.
fm = {1: 'CONFIG_3', 2: '+3.3V', 3: 'GND', 4: '+3.3V', 5: 'GND', 6: 'FULL_CARD_POWER_OFF#', 7: 'USB_D+', 8: 'W_DISABLE1#', 9: 'USB_D-', 10: 'LED1#',
      11: 'GND', 20: 'GPIO5[IF_SEL]', 21: 'CONFIG_0', 22: 'GPIO6[VBUS_SNS]', 23: 'WAKE_ON_WWAN#', 24: 'GPIO7[VCC_OPT]', 25: 'DPR', 26: 'W_DISABLE2#', 27: 'GND',
      28: 'GPIO8[PLA_S2#]', 29: 'USB3_TX-', 30: 'UIM_RESET', 31: 'USB3_TX+', 32: 'UIM_CLK', 33: 'GND', 34: 'UIM_DATA', 35: 'USB3_RX-', 36: 'UIM_PWR', 37: 'USB3_RX+',
      38: 'DEVSLP[VCC_OPT]', 39: 'GND', 40: 'GPIO0[UIM2_DET]', 41: 'PETn0', 42: 'GPIO1[UIM2_DAT]', 43: 'PETp0', 44: 'GPIO2[UIM2_CLK]', 45: 'GND', 46: 'GPIO3[UIM2_RST]',
      47: 'PERn0', 48: 'GPIO4[UIM2_PWR]', 49: 'PERp0', 50: 'PERST#', 51: 'GND', 52: 'CLKREQ#', 53: 'REFCLKN', 54: 'PEWAKE#', 55: 'REFCLKP', 56: 'RFFE_SCLK[I2C]',
      57: 'GND', 58: 'RFFE_SDATA[I2C]', 59: 'ANTCTL0', 60: 'COEX3', 61: 'ANTCTL1', 62: 'COEX_RXD', 63: 'ANTCTL2', 64: 'COEX_TXD', 65: 'ANTCTL3[1V8_REF]',
      66: 'SIM_DETECT', 67: 'RESET#', 68: 'SUSCLK[VCC_OPT]', 69: 'CONFIG_1', 70: '+3.3V', 71: 'GND', 72: '+3.3V', 73: 'GND', 74: '+3.3V', 75: 'CONFIG_2'}
M2_WWAN = fm
def fp(n): return T(n, fm[n])
L = [43, 41, None, 49, 47, None, 55, 53, None, 50, None, 52, None, 54, None, None, 7, 9, None, 31, 29, None, 37, 35, None, None,
     6, None, 67, None, 8, None, 10, None, None, 26, 25, 1, 21, 69, 75]
R = [36, None, 30, None, 32, None, 34, None, 66, None, None, 22, None, 28, None, None, 20, 23, 24, 40, 42, 44, 56, 58, 59, 61, 63, 65, 60, 62, 64, 38, 46, 48, 68]
GNDP = (3, 5, 11, 27, 33, 39, 45, 51, 57, 71, 73)
used = [x for x in L + R if x] + [2, 4, 70, 72, 74] + list(GNDP)
assert sorted(used) == sorted(fm), set(fm) ^ set(used)
make_symbol('M.2_KeyB_WWAN', 'J', 'M.2 Key-B 3052 WWAN socket', [dict(
    left=[fp(n) if n else None for n in L], right=[fp(n) if n else None for n in R],
    top=[S((2, 4, 70, 72, 74), '+3.3V(x5)', 'passive')], bottom=[S(GNDP, 'GND(x11)', 'passive')])],
    footprint='', datasheet='PCI-SIG M.2 Socket 2 Key-B (WWAN); Sierra EM92XX PTS 41114313 Rev 5; Telit FN990 HDG 1VV0301752 Rev 3',
    descr='M.2 Key-B socket, 75 positions (12-19 key), generic WWAN pin names; [] = vendor-specific use',
    fields={'FP_TODO': 'M.2 Key-B socket footprint (LOTES APCI0026-P001A, stack height TBD) + 3042/3052 standoffs - not in KiCad libs'})

# ---- Nano-SIM holder with card-detect (CUI NSIM-2-C) ----
make_symbol('NanoSIM_CD', 'J', 'NSIM-2-C', [dict(
    left=[T(1, 'VCC(C1)'), None, T(2, 'RST(C2)'), None, T(3, 'CLK(C3)'), None, T(7, 'I/O(C7)'), None, T('CD', 'CD(NO_to_GND)'), None, T(6, 'VPP(C6)')],
    bottom=[T(5, 'GND(C5)'), None, T('SH', 'SHIELD')])],
    footprint='Connector_Card:nanoSIM_Hinged_CUI_NSIM-2-C', datasheet='https://www.cuidevices.com/product/resource/nsim-2-c.pdf',
    descr='Hinged nano-SIM holder with card-detect switch')

# ---- N-MOSFET in onsemi DFN5 5x6 / SO-8FL (case 488AA, style 1: pins 1-3 S, 4 G, 5 D = exposed pad); two pin-side variants ----
make_symbol('NMOS_SO8FL', 'Q', 'NVMFS5C646NLAFT1G', [dict(left=[S((1, 2, 3), 'S')], right=[T(5, 'D')], bottom=[T(4, 'G', 'input')])],
            footprint='Package_SO:ONSemi_SO-8FL_488AA', datasheet='https://www.onsemi.com/pdf/datasheet/nvmfs5c646nl-d.pdf',
            descr='N-ch power MOSFET 60V 4.7mOhm AEC-Q101, onsemi SO-8FL (488AA)', width=10.16)
make_symbol('NMOS_SO8FL_DS', 'Q', 'NVMFS5C646NLAFT1G', [dict(left=[T(5, 'D')], right=[S((1, 2, 3), 'S')], bottom=[T(4, 'G', 'input')])],
            footprint='Package_SO:ONSemi_SO-8FL_488AA', datasheet='https://www.onsemi.com/pdf/datasheet/nvmfs5c646nl-d.pdf',
            descr='N-ch power MOSFET 60V 4.7mOhm AEC-Q101, onsemi SO-8FL (488AA), drain drawn left', width=10.16)

# ---- PCIe x1 CEM add-in-card edge (gold fingers), names per PCIe CEM (host-referenced), all passive ----
make_symbol('PCIe_x1_Edge_AddIn', 'J', 'PCIe x1 edge fingers', [dict(
    right=[T('A13', 'REFCLK+'), None, None, None, None, T('A14', 'REFCLK-'), None, None, None, None,
           T('B14', 'PETp0(hostTX)'), T('B15', 'PETn0(hostTX)'), None, None, T('A16', 'PERp0(hostRX)'), T('A17', 'PERn0(hostRX)'), None, None,
           T('A11', 'PERST#'), None, T('A1', 'PRSNT1#'), None, T('B17', 'PRSNT2#'), None, None,
           T('B11', 'WAKE#'), T('B12', 'RSVD/CLKREQ#'), T('B5', 'SMCLK'), T('B6', 'SMDAT'), T('A5', 'TCK'), T('A6', 'TDI'), T('A7', 'TDO'), T('A8', 'TMS'), T('B9', 'TRST#')],
    left=[T('B1', '+12V'), T('B2', '+12V'), T('B3', '+12V'), T('A2', '+12V'), T('A3', '+12V'), None, T('B8', '+3.3V'), T('A9', '+3.3V'), T('A10', '+3.3V'), T('B10', '3.3Vaux')],
    bottom=[S(('A4', 'A12', 'A15', 'A18', 'B4', 'B7', 'B13', 'B16', 'B18'), 'GND(x9)')])],
    footprint='Connector_PCBEdge:BUS_PCIexpress_x1', descr='PCIe x1 add-in card edge connector (card side)')

# ---- TI TPS568230 (RJE VQFN-HR-18) - pins/stacking identical to KiCad stock symbol, sides rearranged for signal flow ----
make_symbol('TPS568230', 'U', 'TPS568230RJER', [dict(
    left=[S((2, 3, 4, 5), 'VIN', 'power_in'), None, T(12, 'EN', 'input'), None, None, T(9, 'PGOOD', 'open_collector'), None, None, T(17, 'VCC', 'power_out'), None, None, None, None, T(15, 'MODE', 'input'), None, None, T(11, 'SS', 'passive')],
    right=[T(1, 'BST', 'passive'), None, None, S((19, 20, 6), 'SW', 'power_out'), None, None, None, None, T(14, 'FB', 'input')],
    bottom=[S((7, 18, 21, 8), 'GND', 'power_in'), None, T(13, 'AGND', 'power_in'), None, S((10, 16), 'NC', 'passive')])],
    footprint='Package_DFN_QFN:Texas_RJE0020A_VQFN-20-1EP_3x3mm_P0.45mm_EP0.675x0.76mm', datasheet='https://www.ti.com/lit/ds/symlink/tps568230.pdf',
    descr='4.5-18V 8A sync buck, D-CAP3, selectable FCCM/Eco-mode')

# ---- TI TPS62130 (RGT VQFN-16) - pins/stacking identical to KiCad stock symbol, sides rearranged ----
make_symbol('TPS62130', 'U', 'TPS62130RGTR', [dict(
    left=[T(13, 'EN', 'input'), None, None, T(9, 'SS/TR', 'passive'), None, None, T(8, 'DEF', 'input'), T(7, 'FSW', 'input')],
    right=[S((1, 2, 3), 'SW', 'power_out'), None, T(14, 'VOS', 'input'), None, None, T(5, 'FB', 'input'), None, None, T(4, 'PG', 'open_collector')],
    top=[S((10, 11, 12), 'VIN', 'power_in')], bottom=[S((15, 16, 17, 6), 'GND', 'power_in')])],
    footprint='Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm_ThermalVias', datasheet='https://www.ti.com/lit/ds/symlink/tps62130.pdf',
    descr='3-17V 3A step-down converter, DCS-Control')
