from engine import make_symbol
from pi7c_pins import P as PI7C

def T(num, nm, typ='passive'): return (str(num), nm, typ)

# ---- TI LM74800-Q1 (LM7480x-Q1 DS SNOSD95C, Table 6-1, DRR-12) ----
make_symbol('LM74800-Q1', 'U', 'LM74800QDRRRQ1', [dict(
    left=[T(2, 'A'), T(3, 'VSNS'), T(4, 'SW'), T(5, 'OV', 'input'), T(6, 'EN/UVLO', 'input'), None, T(7, 'GND', 'power_in'), T(13, 'RTN(EP_float)', 'passive')],
    right=[T(12, 'C'), T(10, 'VS', 'power_in'), T(11, 'CAP'), T(1, 'DGATE', 'output'), T(8, 'HGATE', 'output'), T(9, 'OUT')])],
    footprint='Package_SON:WSON-12-1EP_3x3mm_P0.5mm_EP1.5x2.5mm', datasheet='https://www.ti.com/lit/ds/symlink/lm7480-q1.pdf',
    descr='Ideal diode + load-dump/OV controller, back-to-back NFET, AEC-Q100')

# ---- TI LM61460-Q1 / LMQ61460-Q1 (pin-compatible; DS SNVSB70F Table 7-1, RJR0014A) ----
make_symbol('LM61460-Q1', 'U', 'LM61460AASQRJRRQ1', [dict(
    left=[T(8, 'VIN1', 'power_in'), T(12, 'VIN2', 'power_in'), T(7, 'EN/SYNC', 'input'), T(6, 'RT'), T(1, 'BIAS'), None, T(3, 'AGND', 'power_in'), T(9, 'PGND1', 'power_in'), T(11, 'PGND2', 'power_in')],
    right=[T(10, 'SW'), T(14, 'CBOOT'), T(13, 'RBOOT'), T(2, 'VCC'), T(4, 'FB', 'input'), T(5, 'PGOOD', 'open_collector')])],
    footprint='', datasheet='https://www.ti.com/lit/ds/symlink/lm61460-q1.pdf',
    descr='36V 6A sync buck, AEC-Q100 (drop-in for LMQ61460-Q1)', fields={'FP_TODO': 'TI RJR0014A VQFN-HR-14 4x3.5mm - create footprint from TI land pattern'})

# ---- Diodes PI7C9X3G606GP (DS43484 Rev 5-2, FCA144 ball map) ----
def pi(b): n, t = PI7C[b]; return (b, n, t)
byname = {}
for b, (n, t) in PI7C.items(): byname.setdefault(n, []).append(b)
def pn(n): return pi(byname[n][0])
uA_left = [pn('REFCLKP0'), pn('REFCLKN0'), pn('REFCLKP1'), pn('REFCLKN1'), None] + \
          sum([[pn(f'PERP{i}'), pn(f'PERN{i}')] for i in range(6)], []) + [None, pn('RESREF')]
uA_right = sum([[pn(f'PETP{i}'), pn(f'PETN{i}')] for i in range(6)], []) + [None] + \
          sum([[pn(f'REFCLKOP{i}'), pn(f'REFCLKON{i}')] for i in (1, 4, 5, 6, 7)], [])
ctrl_names = ['PERST_L', 'CHIPMODE1', 'CHIPMODE0', 'PORTCFG2', 'PORTCFG1', 'PORTCFG0', 'CKMODE', 'FATAL_ERR_L/HOT_PLUG_EN_L',
              'INTA_L/PM_L11_EN_L', 'TEST', None, 'EECK', 'EEDI', 'EEDO', 'EECS_L', 'SCL_I2C', 'SDA_I2C', None, 'SHCL_I2C', 'SHDA_I2C', 'SHPCINT_L',
              None, 'JTAG_SEL_L', 'TCK', 'TDI', 'TDO', 'TMS', 'TRST_L']
uB_left = [pn(n) if n else None for n in ctrl_names]
gp = [b for b, (n, t) in PI7C.items() if n.startswith('GPIO')]
gp.sort(key=lambda b: -int(PI7C[b][0].split('/')[0][4:]))
uB_right = [pi(b) for b in gp] + [None] + [pn(f'PORTGOOD_L{i}') for i in (0, 1, 4, 5, 6, 7)] + [None] + \
           [pn(f'PDC_L{i}') for i in (1, 4, 5, 6, 7)] + [None] + [pi(b) for b in byname['NC']]
pw_left = [pi(b) for b in byname['VDDC']] + [pn('C_VDDC'), None] + [pi(b) for b in byname['VP']] + [None] + \
          [pi(b) for b in byname['VDDR']] + [pn('C_VDDR'), None] + [pi(b) for b in byname['VPH']]
pw_right = [pi(b) for b in byname['VSS']]
allb = [e for u in (uA_left, uA_right, uB_left, uB_right, pw_left, pw_right) for e in u if e]
assert len(allb) == 144 and len({e[0] for e in allb}) == 144, len(allb)
make_symbol('PI7C9X3G606GP', 'U', 'PI7C9X3G606GP', [dict(left=uA_left, right=uA_right), dict(left=uB_left, right=uB_right),
            dict(left=pw_left, right=pw_right)],
            footprint='Package_BGA:LFBGA-144_10x10mm_Layout12x12_P0.8mm', datasheet='https://www.diodes.com/assets/Datasheets/PI7C9X3G606GP.pdf',
            descr='PCIe Gen3 packet switch 6-port/6-lane, FCA144 10x10 0.8mm BGA (GPQ = AEC-Q100 Gr3)',
            fields={'FP_VERIFY': 'Generic LFBGA-144 0.8mm; verify ball/pad size vs Diodes FCA144 package drawing'})

# ---- Microchip USB5744 (DS00001855J, 56-VQFN) ----
u = lambda n, nm, t='bidirectional': T(n, nm, t)
make_symbol('USB5744', 'U', 'USB5744/2G9 (verify ordering suffix)', [dict(
    left=[u(45, 'USB2UP_DP'), u(46, 'USB2UP_DM'), u(47, 'USB3UP_TXDP', 'output'), u(48, 'USB3UP_TXDM', 'output'), u(50, 'USB3UP_RXDP', 'input'), u(51, 'USB3UP_RXDM', 'input'), None,
          u(54, 'XTALI/CLK_IN', 'input'), u(53, 'XTALO', 'output'), u(56, 'RBIAS', 'passive'), u(52, 'ATEST', 'passive'), None,
          u(42, 'RESET_N', 'input'), u(37, 'VBUS_DET', 'input'), u(38, 'SPI_CLK/SMCLK'), u(39, 'SPI_DO/SMDAT'), u(40, 'SPI_DI/CFG_BC_EN'), u(41, 'SPI_CE_N/CFG_NON_REM'), None,
          u(36, 'PRT_CTL1'), u(35, 'PRT_CTL2'), u(34, 'PRT_CTL3'), u(32, 'PRT_CTL4/GANG_PWR'), None,
          T(16, 'VDD33', 'power_in'), T(31, 'VDD33', 'power_in'), T(44, 'VDD33', 'power_in'), T(55, 'VDD33', 'power_in'), None,
          T(5, 'VDD12', 'power_in'), T(12, 'VDD12', 'power_in'), T(15, 'VDD12', 'power_in'), T(21, 'VDD12', 'power_in'),
          T(28, 'VDD12', 'power_in'), T(33, 'VDD12', 'power_in'), T(43, 'VDD12', 'power_in'), T(49, 'VDD12', 'power_in'), None, T(57, 'VSS(EP)', 'power_in')],
    right=[u(1, 'USB2DN_DP1/PRT_DIS_P1'), u(2, 'USB2DN_DM1/PRT_DIS_M1'), u(3, 'USB3DN_TXDP1', 'output'), u(4, 'USB3DN_TXDM1', 'output'), u(6, 'USB3DN_RXDP1', 'input'), u(7, 'USB3DN_RXDM1', 'input'), None,
           u(8, 'USB2DN_DP2/PRT_DIS_P2'), u(9, 'USB2DN_DM2/PRT_DIS_M2'), u(10, 'USB3DN_TXDP2', 'output'), u(11, 'USB3DN_TXDM2', 'output'), u(13, 'USB3DN_RXDP2', 'input'), u(14, 'USB3DN_RXDM2', 'input'), None,
           u(17, 'USB2DN_DP3/PRT_DIS_P3'), u(18, 'USB2DN_DM3/PRT_DIS_M3'), u(19, 'USB3DN_TXDP3', 'output'), u(20, 'USB3DN_TXDM3', 'output'), u(22, 'USB3DN_RXDP3', 'input'), u(23, 'USB3DN_RXDM3', 'input'), None,
           u(24, 'USB2DN_DP4/PRT_DIS_P4'), u(25, 'USB2DN_DM4/PRT_DIS_M4'), u(26, 'USB3DN_TXDP4', 'output'), u(27, 'USB3DN_TXDM4', 'output'), u(29, 'USB3DN_RXDP4', 'input'), u(30, 'USB3DN_RXDM4', 'input')])],
    footprint='Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm_ThermalVias', datasheet='https://ww1.microchip.com/downloads/en/DeviceDoc/USB5744-Data-Sheet-DS00001855J.pdf',
    descr='USB 3.2 Gen1 4-port hub controller', fields={'FP_VERIFY': 'EP size not confirmed vs Microchip 56-VQFN drawing'})

# ---- TI HD3SS3220 (SLLSES1E, RNH WQFN-30) ----
make_symbol('HD3SS3220', 'U', 'HD3SS3220RNHR', [dict(
    left=[T(2, 'CC1', 'bidirectional'), T(1, 'CC2', 'bidirectional'), None, T(4, 'PORT', 'input'), T(22, 'ADDR', 'input'), T(3, 'CURRENT_MODE', 'input'),
          T(5, 'VBUS_DET', 'input'), T(29, 'ENn_CC', 'input'), T(12, 'ENn_MUX', 'input'), None, T(11, 'DIR', 'open_collector'), T(27, 'ID', 'open_collector'),
          T(23, 'INT_N/OUT3', 'open_collector'), T(24, 'VCONN_FAULT_N', 'open_collector'), T(25, 'SDA/OUT1', 'bidirectional'), T(26, 'SCL/OUT2', 'bidirectional'), None,
          T(30, 'VDD5', 'power_in'), T(8, 'VCC33', 'power_in'), T(13, 'GND', 'power_in'), T(28, 'GND', 'power_in'), T(31, 'GND(EP)', 'power_in')],
    right=[T(6, 'TXp', 'bidirectional'), T(7, 'TXn', 'bidirectional'), T(9, 'RXp', 'bidirectional'), T(10, 'RXn', 'bidirectional'), None,
           T(17, 'TX1p', 'bidirectional'), T(16, 'TX1n', 'bidirectional'), T(15, 'RX1p', 'bidirectional'), T(14, 'RX1n', 'bidirectional'),
           T(21, 'TX2p', 'bidirectional'), T(20, 'TX2n', 'bidirectional'), T(19, 'RX2p', 'bidirectional'), T(18, 'RX2n', 'bidirectional')])],
    footprint='Package_DFN_QFN:Texas_RNH0030A_WQFN-30-1EP_2.5x4.5mm_P0.4mm_EP1.2x3.2mm', datasheet='https://www.ti.com/lit/ds/symlink/hd3ss3220.pdf',
    descr='USB-C DRP port controller + SS 2:1 mux')

# ---- TI TCA6416A (SCPS194F, TSSOP-24 PW) ----
make_symbol('TCA6416A', 'U', 'TCA6416APWR', [dict(
    left=[T(2, 'VCCI', 'power_in'), T(24, 'VCCP', 'power_in'), None, T(22, 'SCL', 'input'), T(23, 'SDA', 'bidirectional'), T(1, 'INT', 'open_collector'),
          T(3, 'RESET', 'input'), T(21, 'ADDR', 'input'), None, T(12, 'GND', 'power_in')],
    right=[T(4 + i, f'P0{i}', 'bidirectional') for i in range(8)] + [T(13 + i, f'P1{i}', 'bidirectional') for i in range(8)])],
    footprint='Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm', datasheet='https://www.ti.com/lit/ds/symlink/tca6416a.pdf',
    descr='16-bit I2C GPIO expander, dual supply (TCA6416A-Q1 AEC option)')

# ---- M.2 Key-B socket, pin names per Fibocom FM350-GL HW guide (pin definition table, pages 13-16) ----
fm = {1: 'CONFIG_3', 2: '+3.3V', 3: 'GND', 4: '+3.3V', 5: 'GND', 6: 'FULL_CARD_POWER_OFF#', 7: 'USB_D+', 8: 'W_DISABLE1#', 9: 'USB_D-', 10: 'LED1#',
      11: 'GND', 20: 'GPIO', 21: 'CONFIG_0', 22: 'UART_TX', 23: 'WOWWAN#', 24: 'ANT_TUNER_1V8', 25: 'DPR', 26: 'W_DISABLE2#', 27: 'GND', 28: 'UART_RX',
      29: 'USB3_TX-', 30: 'UIM_RESET', 31: 'USB3_TX+', 32: 'UIM_CLK', 33: 'GND', 34: 'UIM_DATA', 35: 'USB3_RX-', 36: 'UIM_PWR', 37: 'USB3_RX+', 38: 'NC',
      39: 'GND', 40: 'I2C_SCL', 41: 'PETn0', 42: 'I2C_SDA', 43: 'PETp0', 44: 'I2C_IRQ#', 45: 'GND', 46: 'NC', 47: 'PERn0', 48: 'NC', 49: 'PERp0', 50: 'PERST#',
      51: 'GND', 52: 'CLKREQ#', 53: 'REFCLKN', 54: 'PEWAKE#', 55: 'REFCLKP', 56: 'RFFE_SCLK', 57: 'GND', 58: 'RFFE_SDATA', 59: 'ANTCTL0', 60: 'COEX3',
      61: 'ANTCTL1', 62: 'COEX_RXD', 63: 'ANTCTL2', 64: 'COEX_TXD', 65: 'ANTCTL3', 66: 'SIM1_DETECT', 67: 'RESET#', 68: 'NC', 69: 'CONFIG_1', 70: '+3.3V',
      71: 'GND', 72: '+3.3V', 73: 'VIO_CFG', 74: '+3.3V', 75: 'CONFIG_2'}
FM350 = fm
L = [2, 4, 70, 72, 74, None, 41, 43, 47, 49, 53, 55, None, 50, 52, 54, None, 7, 9, 29, 31, 35, 37, None, 3, 5, 11, 27, 33, 39, 45, 51, 57, 71]
R = [6, 67, 8, 26, 25, 10, None, 30, 32, 34, 36, 66, None, 1, 21, 69, 75, 73, None, 20, 22, 28, 23, 24, 40, 42, 44, 56, 58, 59, 61, 63, 65, 60, 62, 64, None, 38, 46, 48, 68]
assert sorted(x for x in L + R if x) == sorted(fm), set(fm) - set(x for x in L + R if x)
make_symbol('M.2_KeyB_FM350', 'J', 'M.2 Key-B 3052 socket (LOTES APCI0026-P001A)', [dict(
    left=[T(n, fm[n]) if n else None for n in L], right=[T(n, fm[n]) if n else None for n in R])],
    footprint='', datasheet='Fibocom FM350-GL Hardware Guide (FCC ID ZMOFM350GL exhibit)',
    descr='M.2 Key-B socket, 75 positions (12-19 key), pins named per FM350-GL', fields={'FP_TODO': 'M.2 Key-B socket footprint (LOTES APCI0026-P001A, 3.2mm? stack height) + 3052 standoff - not in KiCad libs'})

# ---- Nano-SIM holder with card-detect (CUI NSIM-2-C) ----
make_symbol('NanoSIM_CD', 'J', 'NSIM-2-C', [dict(
    left=[T(1, 'VCC(C1)'), T(2, 'RST(C2)'), T(3, 'CLK(C3)'), T(7, 'I/O(C7)'), T(6, 'VPP(C6)'), T(5, 'GND(C5)')],
    right=[T('CD', 'CD(NO_to_GND)'), None, T('SH', 'SHIELD')])],
    footprint='Connector_Card:nanoSIM_Hinged_CUI_NSIM-2-C', datasheet='https://www.cuidevices.com/product/resource/nsim-2-c.pdf',
    descr='Hinged nano-SIM holder with card-detect switch')

# ---- N-MOSFET in LFPAK56 (pads 1-3 S, 4 G, 5 D tab) ----
make_symbol('NMOS_LFPAK56', 'Q', 'BUK7Y4R8-60E', [dict(
    left=[T(4, 'G', 'input')], right=[T(5, 'D'), [T(1, 'S'), T(2, 'S'), T(3, 'S')]])],
    footprint='Package_TO_SOT_SMD:LFPAK56', descr='N-ch power MOSFET, LFPAK56 (verify MPN/rating)')

# ---- PCIe x1 CEM add-in-card edge (gold fingers), names per PCIe CEM (host-referenced), all passive ----
make_symbol('PCIe_x1_Edge_AddIn', 'J', 'PCIe x1 edge fingers', [dict(
    left=[T('B14', 'PETp0(hostTX)'), T('B15', 'PETn0(hostTX)'), T('A16', 'PERp0(hostRX)'), T('A17', 'PERn0(hostRX)'), None,
          T('A13', 'REFCLK+'), T('A14', 'REFCLK-'), None, T('A11', 'PERST#'), T('B11', 'WAKE#'), T('B12', 'RSVD/CLKREQ#'), T('B5', 'SMCLK'), T('B6', 'SMDAT'), None,
          T('A1', 'PRSNT1#'), T('B17', 'PRSNT2#'), None, T('A5', 'TCK'), T('A6', 'TDI'), T('A7', 'TDO'), T('A8', 'TMS'), T('B9', 'TRST#')],
    right=[T('B1', '+12V'), T('B2', '+12V'), T('B3', '+12V'), T('A2', '+12V'), T('A3', '+12V'), T('B8', '+3.3V'), T('A9', '+3.3V'), T('A10', '+3.3V'), T('B10', '3.3Vaux'), None,
           T('A4', 'GND'), T('A12', 'GND'), T('A15', 'GND'), T('A18', 'GND'), T('B4', 'GND'), T('B7', 'GND'), T('B13', 'GND'), T('B16', 'GND'), T('B18', 'GND')])],
    footprint='Connector_PCBEdge:BUS_PCIexpress_x1', descr='PCIe x1 add-in card edge connector (card side)')
