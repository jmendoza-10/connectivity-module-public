import os, sys, json
import engine, symbols
from engine import Sheet, Design

D = Design('WWAN Carrier - 3x Fibocom FM350-GL, PCIe Gen3 switch + USB3 hub')
FP = dict(R0402='Resistor_SMD:R_0402_1005Metric', R0603='Resistor_SMD:R_0603_1608Metric',
          C0201='Capacitor_SMD:C_0201_0603Metric', C0402='Capacitor_SMD:C_0402_1005Metric', C0603='Capacitor_SMD:C_0603_1608Metric',
          C0805='Capacitor_SMD:C_0805_2012Metric', C1206='Capacitor_SMD:C_1206_3216Metric', C1210='Capacitor_SMD:C_1210_3225Metric',
          LED='LED_SMD:LED_0603_1608Metric', TP='TestPoint:TestPoint_Pad_D1.0mm', FB0603='Inductor_SMD:L_0603_1608Metric')

def R(s, a, b, val, fp='R0402', dnp=False, note=None, mpn=None):
    f = {}
    if note: f['Notes'] = note
    if mpn: f['MPN'] = mpn
    return s.part('Device:R', {'1': a, '2': b}, value=val, rot_=90, footprint=FP[fp], dnp=dnp, fields=f)
def C(s, a, b, val, fp='C0402', dnp=False, note=None, mpn=None):
    f = {}
    if note: f['Notes'] = note
    if mpn: f['MPN'] = mpn
    return s.part('Device:C', {'1': a, '2': b}, value=val, rot_=90, footprint=FP.get(fp, fp), dnp=dnp, fields=f)
def CP(s, a, b, val, fp, mpn=None, note=None):
    f = {}
    if mpn: f['MPN'] = mpn
    if note: f['Notes'] = note
    return s.part('Device:C_Polarized', {'1': a, '2': b}, value=val, rot_=90, footprint=fp, fields=f)
def Lind(s, a, b, val, fp, mpn):
    return s.part('Device:L', {'1': a, '2': b}, value=val, rot_=90, footprint=fp, fields={'MPN': mpn})
def FB(s, a, b, mpn='BLM18PG221SN1D'):
    return s.part('Device:FerriteBead_Small', {'1': a, '2': b}, value=mpn, rot_=90, footprint=FP['FB0603'], fields={'MPN': mpn, 'Notes': 'VERIFY bead choice/DCR'})
def LED(s, a, k, color='green', mpn='LTST-C191KGKT'):
    return s.part('Device:LED', {'2': a, '1': k}, value=color, footprint=FP['LED'], fields={'MPN': mpn})
def TP(s, net):
    return s.part('Connector:TestPoint', {'1': net}, value=net, footprint=FP['TP'], prefix='TP', in_bom=False)
def FLAG(s, net):
    return s.part('power:PWR_FLAG', {'1': net}, ref=f'#FLG0{len(FLAGS) + 1:03d}', in_bom=False) if not FLAGS.append(net) else None
FLAGS = []
def NMOS_SIG(s, g, d, src='GND'):
    return s.part('Transistor_FET:2N7002', {'1': g, '3': d, '2': src}, value='2N7002', footprint='Package_TO_SOT_SMD:SOT-23',
                  fields={'MPN': '2N7002-7-F (or 2N7002K-Q AEC)'})
def BYP(s, net, vals, fp='C0402'):
    for v in vals: C(s, net, 'GND', v, fp)

# ======================= Sheet 1: 12V input + system rails =======================
s = D.add(Sheet('power_input.kicad_sch', 'Power input: 12V protection + system rails', 2, 100))
s.note('12V INPUT PROTECTION (LM74800-Q1, common-drain back-to-back NFETs, per TI LM7480-Q1 DS SNOSD95C Fig.10-1)\n'
       '- Q1 (DGATE) = ideal diode / reverse-battery; Q2 (HGATE) = overvoltage cut-off.\n'
       '- OV cut-off = 1.231V x (470k+39k)/39k = ~16.1V (protects TPS568230 18V / TPS62130 17V abs-max downstream).\n'
       '- UVLO rising = 1.231V x (220k+40.2k)/40.2k = ~8.0V.\n'
       '- LM7480 exposed pad (RTN) must be left FLOATING - do not tie to GND copper (DS Table 6-1).\n'
       '- Fuse/TVS/FET MPNs are proposals - VERIFY ratings and inrush (3x(2x220uF)+bulk) before ordering.\n'
       'SYSTEM RAILS\n'
       '- +3V3: LM61460-Q1 (substitute for backordered LMQ61460-Q1; same RJR-14 pinout per both TI datasheets), Vout=1V x (1+100k/43.2k)=3.31V, 400kHz.\n'
       '- +0V95 (PI7C9X3G606GP VDDC/VP/C_VDDC, worst ~3.3A @Tj80C per DS Table 12-12): TPS568230, Vref 0.6V, 5.62k/9.53k -> 0.954V, FCCM 800kHz.\n'
       '- +1V8 (PI7C VDDR/VPH/C_VDDR ~0.25A + EEPROM + PCA9306): TPS62130, 150k/120k -> 1.80V.\n'
       '- +1V2 (USB5744 VDD12, 688mA typ with 4 SS ports per DS Table 10-3): TPS62130, 75k/150k -> 1.20V.\n'
       '- Low-voltage regulators enabled by PG_3V3 (simple sequencing; PI7C requires PERST# held until rails+REFCLK stable).')
J = s.part('Connector_Generic:Conn_01x02', {'1': '+12V_RAW', '2': 'GND'}, value='12V IN', footprint='Connector_Molex:Molex_Micro-Fit_3.0_43650-0200_1x02_P3.00mm_Horizontal',
           fields={'MPN': 'Molex 43650-0200'})
s.part('Device:Fuse', {'1': '+12V_RAW', '2': '+12V_FUSED'}, value='7A', rot_=90, footprint='Fuse:Fuse_1206_3216Metric',
       fields={'MPN': 'Littelfuse 0466007.NR (VERIFY I2t vs inrush)'})
s.part('Device:D_TVS', {'1': '+12V_FUSED', '2': 'GND'}, value='SMBJ33CA', footprint='Diode_SMD:D_SMB', fields={'MPN': 'SMBJ33CA (bidirectional, per TI app)'})
C(s, '+12V_FUSED', 'GND', '100nF/50V', 'C0603')
s.part('wwan_carrier:NMOS_LFPAK56', {'4': 'DGATE', '5': 'VS_CD', '1': '+12V_FUSED'}, fields={'MPN': 'Nexperia BUK7Y4R8-60E (60V, AEC-Q101) VERIFY'})
s.part('wwan_carrier:NMOS_LFPAK56', {'4': 'HGATE', '5': 'VS_CD', '1': '+12V'}, fields={'MPN': 'Nexperia BUK7Y4R8-60E (60V, AEC-Q101) VERIFY'})
s.part('wwan_carrier:LM74800-Q1', {'2': '+12V_FUSED', '12': 'VS_CD', '10': 'VS_CD', '11': 'LM_CAP', '1': 'DGATE', '8': 'HGATE', '9': '+12V',
                                   '3': 'VS_CD', '4': 'LM_SW', '5': 'LM_OV', '6': 'LM_EN', '7': 'GND', '13': 'NC'})
R(s, 'LM_SW', 'LM_OV', '470k'); R(s, 'LM_OV', 'GND', '39k')
R(s, 'VS_CD', 'LM_EN', '220k'); R(s, 'LM_EN', 'GND', '40.2k')
C(s, 'LM_CAP', 'VS_CD', '100nF/50V', 'C0603'); C(s, 'VS_CD', 'GND', '100nF/50V', 'C0603')
C(s, '+12V', 'GND', '10uF/50V', 'C1210'); C(s, '+12V', 'GND', '10uF/50V', 'C1210')
CP(s, '+12V', 'GND', '100uF/35V', 'Capacitor_SMD:CP_Elec_6.3x7.7', mpn='Panasonic EEE-FK1V101P (AEC-Q200) VERIFY')
R(s, '+12V', 'LED12_A', '4.7k'); LED(s, 'LED12_A', 'GND')
for n in ('+12V_RAW', 'GND', 'VS_CD', '+12V'): FLAG(s, n)
for n in ('+12V', '+12V_RAW', 'GND', 'GND'): TP(s, n)
s.brk()
# +3V3
s.part('wwan_carrier:LM61460-Q1', {'8': '+12V', '12': '+12V', '7': 'EN_3V3', '6': 'RT_3V3', '1': '+3V3', '3': 'GND', '9': 'GND', '11': 'GND',
                                   '10': 'SW_3V3', '14': 'CB_3V3', '13': 'RB_3V3', '2': 'VCC_3V3', '4': 'FB_3V3', '5': 'PG_3V3'},
       fields={'MPN': 'LM61460AASQRJRRQ1', 'Notes': 'Sub for LMQ61460AASQRJRRQ1 (backordered)'})
R(s, '+12V', 'EN_3V3', '100k'); R(s, 'EN_3V3', 'GND', '20k')
R(s, 'RT_3V3', 'GND', '33.2k', note='400 kHz')
C(s, '+12V', 'GND', '10uF/50V', 'C1210'); C(s, '+12V', 'GND', '10uF/50V', 'C1210'); C(s, '+12V', 'GND', '100nF/50V'); C(s, '+12V', 'GND', '100nF/50V')
R(s, 'RB_3V3', 'CB_3V3', '0'); C(s, 'CB_3V3', 'SW_3V3', '100nF/16V')
C(s, 'VCC_3V3', 'GND', '1uF/16V'); C(s, '+3V3', 'GND', '1uF/16V')
Lind(s, 'SW_3V3', '+3V3', '3.3uH', 'Inductor_SMD:L_Coilcraft_XAL7070-XXX', 'XAL7070-332MEB')
R(s, '+3V3', 'FB_3V3', '100k'); R(s, 'FB_3V3', 'GND', '43.2k'); C(s, '+3V3', 'FB_3V3', '22pF', dnp=True, note='Cff option')
for _ in range(4): C(s, '+3V3', 'GND', '22uF/10V', 'C1210')
R(s, '+3V3', 'PG_3V3', '10k', note='PG_3V3 also drives EN of 3 regulators (internal EN pull-downs)')
FLAG(s, '+3V3'); TP(s, '+3V3'); TP(s, 'PG_3V3')
s.brk()
# +0V95
s.part('Regulator_Switching:TPS568230', {'2': '+12V', '12': 'PG_3V3', '9': 'PG_0V95', '15': 'MODE_0V95', '7': 'GND', '14': 'FB_0V95',
                                         '17': 'VCC_0V95', '11': 'NC', '10': 'NC', '13': 'GND', '6': 'SW_0V95', '1': 'BST_0V95'},
       value='TPS568230RJER', fields={'MPN': 'TPS568230RJER'})
C(s, '+12V', 'GND', '10uF/25V', 'C1206'); C(s, '+12V', 'GND', '10uF/25V', 'C1206'); C(s, '+12V', 'GND', '100nF/50V')
C(s, 'BST_0V95', 'SW_0V95', '100nF/16V'); C(s, 'VCC_0V95', 'GND', '1uF/10V')
R(s, 'VCC_0V95', 'MODE_0V95', '75k', note='FCCM 800kHz (DS Table 1)'); R(s, 'MODE_0V95', 'GND', '51k')
Lind(s, 'SW_0V95', '+0V95', '1.0uH', 'Inductor_SMD:L_Coilcraft_XAL5030-XXX', 'XAL5030-102MEB')
R(s, '+0V95', 'FB_0V95', '5.62k'); R(s, 'FB_0V95', 'GND', '9.53k')
for _ in range(4): C(s, '+0V95', 'GND', '47uF/6.3V', 'C1206')
R(s, '+3V3', 'PG_0V95', '100k')
FLAG(s, '+0V95'); TP(s, '+0V95')
s.brk()
for rail, top, bot, tag in (('+1V8', '150k', '120k', '1V8'), ('+1V2', '75k', '150k', '1V2')):
    s.part('Regulator_Switching:TPS62130', {'10': '+12V', '13': 'PG_3V3', '9': f'SS_{tag}', '8': 'GND', '7': 'GND', '6': 'GND',
                                            '1': f'SW_{tag}', '14': rail, '4': f'PG_{tag}', '5': f'FB_{tag}'},
           value='TPS62130RGTR', fields={'MPN': 'TPS62130RGTR (TPS62130AQRGTRQ1 = AEC option)'})
    C(s, '+12V', 'GND', '10uF/25V', 'C0805'); C(s, '+12V', 'GND', '100nF/50V'); C(s, f'SS_{tag}', 'GND', '3.3nF')
    Lind(s, f'SW_{tag}', rail, '2.2uH', 'Inductor_SMD:L_Coilcraft_XAL4020-XXX', 'XAL4020-222MEB')
    R(s, rail, f'FB_{tag}', top); R(s, f'FB_{tag}', 'GND', bot)
    C(s, rail, 'GND', '22uF/6.3V', 'C0805'); C(s, rail, 'GND', '22uF/6.3V', 'C0805')
    R(s, '+3V3', f'PG_{tag}', '100k')
    FLAG(s, rail); TP(s, rail)

# ======================= Sheet 2: 3x 3.7V slot bucks =======================
s = D.add(Sheet('wwan_power.kicad_sch', 'WWAN slot supplies: 3x 3.7V 6A switchable bucks', 3, 200))
s.note('3x LM61460-Q1 (6A) - one per M.2 slot. FM350-GL: VCC 3.135-4.4V (typ 3.3V), peak >3.5A, ripple <300mV (HW guide 3.1).\n'
       'Vout = 1.0V x (1 + 100k/36.5k) = 3.74V (headroom for connector/trace drop). fsw 400kHz (RT 33.2k), L = 3.3uH XAL7070.\n'
       'EN driven by TCA6416A (control sheet); 100k pull-down keeps slot OFF at power-up. PGOOD -> expander + PG LED.\n'
       'Slot bulk (2x220uF low-ESR + HF caps per FM350 guide) is on each slot sheet next to the connector.\n'
       'NOTE: no active output discharge - after EN low allow bleed-down before re-enable (power-cycle = sysfs remove -> EN off -> wait -> EN on -> rescan).')
for n in (1, 2, 3):
    t = f'S{n}'
    s.part('wwan_carrier:LM61460-Q1', {'8': '+12V', '12': '+12V', '7': f'SLOT{n}_PWR_EN', '6': f'RT_{t}', '1': f'+3V7_S{n}', '3': 'GND', '9': 'GND', '11': 'GND',
                                       '10': f'SW_{t}', '14': f'CB_{t}', '13': f'RB_{t}', '2': f'VCC_{t}', '4': f'FB_{t}', '5': f'SLOT{n}_PG'},
           fields={'MPN': 'LM61460AASQRJRRQ1', 'Notes': 'Sub for LMQ61460AASQRJRRQ1 (backordered)'})
    R(s, f'SLOT{n}_PWR_EN', 'GND', '100k', note='default OFF')
    R(s, f'RT_{t}', 'GND', '33.2k')
    C(s, '+12V', 'GND', '10uF/50V', 'C1210'); C(s, '+12V', 'GND', '10uF/50V', 'C1210'); C(s, '+12V', 'GND', '100nF/50V'); C(s, '+12V', 'GND', '100nF/50V')
    R(s, f'RB_{t}', f'CB_{t}', '0'); C(s, f'CB_{t}', f'SW_{t}', '100nF/16V')
    C(s, f'VCC_{t}', 'GND', '1uF/16V'); C(s, f'+3V7_S{n}', 'GND', '1uF/16V')
    Lind(s, f'SW_{t}', f'+3V7_S{n}', '3.3uH', 'Inductor_SMD:L_Coilcraft_XAL7070-XXX', 'XAL7070-332MEB')
    R(s, f'+3V7_S{n}', f'FB_{t}', '100k'); R(s, f'FB_{t}', 'GND', '36.5k')
    for _ in range(4): C(s, f'+3V7_S{n}', 'GND', '22uF/10V', 'C1210')
    R(s, '+3V3', f'SLOT{n}_PG', '100k')
    FLAG(s, f'+3V7_S{n}'); TP(s, f'+3V7_S{n}')
    s.brk()

# ======================= Sheet 3: PCIe switch =======================
s = D.add(Sheet('pcie_switch.kicad_sch', 'PCIe Gen3 switch PI7C9X3G606GP + x1 edge input', 4, 300))
PIREF = s.ref('U')  # reserve U301 for the switch
s.note('PI7C9X3G606GP (Diodes DS43484 Rev5-2) - ball map transcribed from section 3; all 144 balls placed.\n'
       'PORTCFG[2:0]=101 -> 6-port/6-lane mode (Table 5-1). Lane map (Table 5-4): L0=P0 upstream, L1=P1, L2=P4, L3=P5, L4=P6, L5=P7.\n'
       'Slot1 = lane1/P1 (REFCLKO1, CLKREQ_L1), Slot2 = lane2/P4 (REFCLKO4, CLKREQ_L4), Slot3 = lane3/P5 (REFCLKO5, CLKREQ_L5). P6/P7 unused (NC).\n'
       'CKMODE=0 (BASE): REFCLK0 from host via edge; REFCLKP/N1 tied to GND (Table 5-5).\n'
       'Straps: CHIPMODE=00 (330R PD), CKMODE 330R PD, TEST 330R PD, TMS/TRST_L 330R PD, HOT_PLUG_EN_L=1 (5.1k PU), PM_L11_EN_L=1 (L1.1 off; 330R PD option DNP).\n'
       'Edge connector (add-in-card side, fed from ADT-Link M41 M.2->x1 riser): B14/B15 = host TX -> switch RX (no caps); switch TX -> 220nF -> A16/A17.\n'
       'Edge +12V/+3.3V/3.3Vaux NOT used (carrier is powered from its own 12V input). SMBus/JTAG/WAKE# on edge left open.\n'
       'PERST# from edge -> 74LVC1G07 (VCC 1.8V, 5V-tolerant input) -> PERST_L; also fans out (3.3V) to per-slot AND gates.\n'
       'VERIFY: HCSL termination (series 0R + DNP 49.9R shunts placed), PDC_L behaviour with hot-plug disabled (DNP 0R to GND option),\n'
       'unused SerDes lane handling, decoupling/bead values - Diodes HW design guide / eval board schematic not public: request from Diodes FAE.\n'
       'I2C slave (default addr 0x6F) behind PCA9306 (1.8V <-> 3.3V). SPI EEPROM optional config (EEPROM signature 0x1516).')
edge = {'B14': 'UP_RX_P', 'B15': 'UP_RX_N', 'A16': 'UP_TX_P_AC', 'A17': 'UP_TX_N_AC', 'A13': 'PCIE_REFCLK_P', 'A14': 'PCIE_REFCLK_N',
        'A11': 'PCIE_PERST_N', 'A1': 'PRSNT', 'B17': 'PRSNT'}
for p in ('B11', 'B12', 'B5', 'B6', 'A5', 'A6', 'A7', 'A8', 'B9', 'B1', 'B2', 'B3', 'A2', 'A3', 'B8', 'A9', 'A10', 'B10'): edge[p] = 'NC'
for p in ('A4', 'A12', 'A15', 'A18', 'B4', 'B7', 'B13', 'B16', 'B18'): edge[p] = 'GND'
s.part('wwan_carrier:PCIe_x1_Edge_AddIn', edge, fields={'Notes': 'PCB edge fingers (bevel/hard gold); mates ADT-Link M41 x1 slot'})
C(s, 'UP_TX_P', 'UP_TX_P_AC', '220nF', 'C0201'); C(s, 'UP_TX_N', 'UP_TX_N_AC', '220nF', 'C0201')
R(s, 'PCIE_REFCLK_P', 'GND', '49.9', dnp=True, note='HCSL term option'); R(s, 'PCIE_REFCLK_N', 'GND', '49.9', dnp=True, note='HCSL term option')
R(s, 'PCIE_PERST_N', 'GND', '100k')
s.part('74xGxx:74LVC1G07', {'2': 'PCIE_PERST_N', '5': '+1V8', '3': 'GND', '1': 'NC', '4': 'SW_PERST_N'}, footprint='Package_TO_SOT_SMD:SOT-353_SC-70-5',
       value='74LVC1G07GW', fields={'MPN': '74LVC1G07GW,125 (or SN74LVC1G07DCKR)'})
C(s, '+1V8', 'GND', '100nF')
R(s, '+1V8', 'SW_PERST_N', '5.1k')
TP(s, 'PCIE_PERST_N')
s.brk()
uA = {'A6': 'PCIE_REFCLK_P', 'A5': 'PCIE_REFCLK_N', 'L6': 'GND', 'L7': 'GND', 'A10': 'UP_RX_P', 'A9': 'UP_RX_N',
      'A8': 'SLOT1_PCIE_TX_P', 'A7': 'SLOT1_PCIE_TX_N', 'M3': 'SLOT2_PCIE_TX_P', 'M4': 'SLOT2_PCIE_TX_N', 'M5': 'SLOT3_PCIE_TX_P', 'M6': 'SLOT3_PCIE_TX_N',
      'M7': 'NC', 'M8': 'NC', 'M9': 'NC', 'M10': 'NC', 'C6': 'RESREF',
      'C10': 'UP_TX_P', 'C9': 'UP_TX_N', 'C8': 'SW_TX1_P', 'C7': 'SW_TX1_N', 'K3': 'SW_TX2_P', 'K4': 'SW_TX2_N', 'K5': 'SW_TX3_P', 'K6': 'SW_TX3_N',
      'K7': 'NC', 'K8': 'NC', 'K9': 'NC', 'K10': 'NC',
      'A2': 'SW_CLK1_P', 'A1': 'SW_CLK1_N', 'A4': 'SW_CLK2_P', 'A3': 'SW_CLK2_N', 'B3': 'SW_CLK3_P', 'C3': 'SW_CLK3_N', 'B2': 'NC', 'C2': 'NC', 'C1': 'NC', 'D1': 'NC'}
# sanity: lane mapping vs datasheet names
from pi7c_pins import P as PI
assert PI['A8'][0] == 'PERP1' and PI['M3'][0] == 'PERP2' and PI['M5'][0] == 'PERP3' and PI['C8'][0] == 'PETP1' and PI['K3'][0] == 'PETP2' and PI['K5'][0] == 'PETP3'
assert PI['A2'][0] == 'REFCLKOP1' and PI['A4'][0] == 'REFCLKOP4' and PI['B3'][0] == 'REFCLKOP5' and PI['A6'][0] == 'REFCLKP0'
s.part('wwan_carrier:PI7C9X3G606GP', uA, ref=PIREF, unit=1, fields={'MPN': 'PI7C9X3G606GPAEX (GPQ = AEC-Q100 option)'})
R(s, 'RESREF', 'GND', '200R 1%', mpn='100ppm/C or better')
for n in (1, 2, 3):
    C(s, f'SW_TX{n}_P', f'SLOT{n}_PCIE_RX_P', '220nF', 'C0201'); C(s, f'SW_TX{n}_N', f'SLOT{n}_PCIE_RX_N', '220nF', 'C0201')
    R(s, f'SW_CLK{n}_P', f'SLOT{n}_REFCLK_P', '0'); R(s, f'SW_CLK{n}_N', f'SLOT{n}_REFCLK_N', '0')
    R(s, f'SLOT{n}_REFCLK_P', 'GND', '49.9', dnp=True); R(s, f'SLOT{n}_REFCLK_N', 'GND', '49.9', dnp=True)
s.brk()
assert PI['E4'][0].startswith('GPIO9/CLKREQ_L1') and PI['D3'][0].startswith('GPIO12/CLKREQ_L4') and PI['C4'][0].startswith('GPIO13/CLKREQ_L5') and PI['E3'][0].startswith('GPIO8/CLKREQ_L0')
uB = {'A12': 'SW_PERST_N', 'G9': 'CHIPMODE1', 'F9': 'CHIPMODE0', 'D11': 'PORTCFG2', 'C11': 'PORTCFG1', 'B11': 'PORTCFG0', 'D9': 'CKMODE',
      'E9': 'SW_FATAL_N', 'E1': 'SW_INTA_N', 'E2': 'SW_TEST', 'K12': 'EE_SCK', 'L11': 'EE_SI', 'J12': 'EE_SO', 'M11': 'EE_CS_N',
      'L12': 'SW_SCL_1V8', 'M12': 'SW_SDA_1V8', 'L1': 'SH_SCL', 'M1': 'SH_SDA', 'M2': 'SH_INT_N', 'A11': 'JTAG_SEL_N',
      'H9': 'NC', 'J10': 'NC', 'J11': 'NC', 'H10': 'SW_TMS', 'J9': 'SW_TRST_N',
      'E4': 'SLOT1_CLKREQ_N', 'D3': 'SLOT2_CLKREQ_N', 'C4': 'SLOT3_CLKREQ_N', 'E3': 'UP_CLKREQ_N',
      'E10': 'PORTGOOD1_N', 'E11': 'PORTGOOD0_N', 'G11': 'PORTGOOD4_N', 'F10': 'PORTGOOD5_N', 'G10': 'NC', 'H11': 'NC',
      'J2': 'PDC1_N', 'J1': 'PDC4_N', 'H1': 'PDC5_N', 'G1': 'NC', 'F2': 'NC', 'H2': 'NC', 'H4': 'NC', 'K1': 'NC', 'L2': 'NC'}
for b, (nm, t) in PI.items():
    if nm.startswith('GPIO') and b not in uB: uB[b] = 'NC'
s.part('wwan_carrier:PI7C9X3G606GP', uB, ref=PIREF, unit=2)
for n in ('CHIPMODE1', 'CHIPMODE0', 'PORTCFG1', 'CKMODE', 'SW_TEST', 'SW_TMS', 'SW_TRST_N'): R(s, n, 'GND', '330')
for n in ('PORTCFG2', 'PORTCFG0', 'SW_FATAL_N', 'SW_INTA_N', 'EE_SCK', 'EE_CS_N', 'SW_SCL_1V8', 'SW_SDA_1V8', 'SH_SCL', 'SH_SDA', 'SH_INT_N',
          'JTAG_SEL_N', 'SLOT1_CLKREQ_N', 'SLOT2_CLKREQ_N', 'SLOT3_CLKREQ_N', 'UP_CLKREQ_N'):
    R(s, '+1V8', n, '5.1k')
R(s, 'SW_INTA_N', 'GND', '330', dnp=True, note='fit to enable PM L1.1 (PM_L11_EN_L=0)')
for n in ('PDC1_N', 'PDC4_N', 'PDC5_N'): R(s, n, 'GND', '0', dnp=True, note='present-detect option - VERIFY')
for p in ('0', '1', '4', '5'):
    R(s, '+3V3', f'PGLED{p}_A', '680'); LED(s, f'PGLED{p}_A', f'PORTGOOD{p}_N', 'red', 'APHHS1005SURCK (low Vf red) VERIFY')
for n in ('SW_FATAL_N', 'SW_INTA_N', 'UP_CLKREQ_N'): TP(s, n)
s.part('Memory_EEPROM:AT25xxx', {'1': 'EE_CS_N', '2': 'EE_SO', '3': '+1V8', '7': '+1V8', '8': '+1V8', '4': 'GND', '6': 'EE_SCK', '5': 'EE_SI'},
       value='25AA640A', footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', fields={'MPN': '25AA640A-I/SN (1.8V, 2-byte addr) VERIFY vs switch EEPROM format'})
C(s, '+1V8', 'GND', '100nF')
s.part('Interface:PCA9306DC', {'3': 'SW_SCL_1V8', '4': 'SW_SDA_1V8', '2': '+1V8', '1': 'GND', '7': 'PCA_VREF2', '8': 'PCA_VREF2', '6': 'I2C_SCL', '5': 'I2C_SDA'},
       value='PCA9306DCUR', footprint='Package_SO:VSSOP-8_2.3x2mm_P0.5mm', fields={'MPN': 'PCA9306DCUR'})
R(s, '+3V3', 'PCA_VREF2', '200k'); C(s, 'PCA_VREF2', 'GND', '100nF'); FLAG(s, 'PCA_VREF2')
s.brk()
pw = {}
for b, (nm, t) in PI.items():
    if nm == 'VDDC' or nm == 'VP': pw[b] = '+0V95'
    elif nm == 'C_VDDC': pw[b] = '+0V95_CLK'
    elif nm == 'VDDR': pw[b] = '+1V8'
    elif nm == 'C_VDDR': pw[b] = '+1V8_CLK'
    elif nm == 'VPH': pw[b] = '+1V8_VPH'
    elif nm == 'VSS': pw[b] = 'GND'
s.part('wwan_carrier:PI7C9X3G606GP', pw, ref=PIREF, unit=3)
BYP(s, '+0V95', ['100nF'] * 12, 'C0201'); BYP(s, '+0V95', ['10uF/6.3V'] * 3, 'C0603'); BYP(s, '+0V95', ['22uF/6.3V'], 'C0805')
FB(s, '+0V95', '+0V95_CLK'); BYP(s, '+0V95_CLK', ['100nF', '1uF'])
BYP(s, '+1V8', ['100nF', '100nF', '10uF/6.3V'])
FB(s, '+1V8', '+1V8_CLK'); BYP(s, '+1V8_CLK', ['100nF', '1uF'])
FB(s, '+1V8', '+1V8_VPH'); BYP(s, '+1V8_VPH', ['100nF', '100nF', '10uF/6.3V'])
for n in ('+0V95_CLK', '+1V8_CLK', '+1V8_VPH'): FLAG(s, n)

# ======================= Sheets 4-6: M.2 slots =======================
fm = symbols.FM350
for n in (1, 2, 3):
    s = D.add(Sheet(f'slot{n}.kicad_sch', f'M.2 Key-B slot {n} (Fibocom FM350-GL) + nano-SIM', 4 + n, 100 * (3 + n)))
    s.note(f'SLOT {n}: M.2 3052 Key-B, pinout per Fibocom FM350-GL Hardware Guide pin table (pp.13-16).\n'
           f'PCIe Gen3 x1 to switch port {"1 (lane1)" if n == 1 else "4 (lane2)" if n == 2 else "5 (lane3)"}; USB2 + USB3 to USB5744 port {n}.\n'
           'Module TX AC caps are on the module (M.2 convention); host-TX caps are on the switch/hub sheets.\n'
           'FULL_CARD_POWER_OFF#: driven directly by TCA6416A (3.3V OK, pin level 3.3/1.8V), 47k PD -> module held off by default.\n'
           '  Firmware: drive FCPO# LOW before removing +3V7 (avoid back-powering the module through the expander output).\n'
           'RESET# (1.8V domain, 350k internal PU) and W_DISABLE1# are pulled low by 2N7002 open-drain (gate high = asserted).\n'
           'PCIe-disable / force-USB: PERST# to the slot = PCIE_PERST_N AND SLOTn_PCIE_EN (74LVC1G08). Fit JP to hold PERST# low.\n'
           '  VERIFY with Fibocom: that FM350 enumerates on USB3/USB2 when PERST# is held low (USB3 is "reserved" in the HW guide).\n'
           'SIM: CUI NSIM-2-C (card-detect NO-to-GND) -> SIM1_DETECT. Module default is active-high detect: set active-low by AT cmd,\n'
           '  or disable hot-plug (AT+MSMPD=0). eSIM is internal: AT+GTDUALSIM selects. ESD + 22pF filters near holder per HW guide 3.5.\n'
           'Bulk: 2x220uF low-ESR + 1uF + 100nF + 33/18/10/6.8pF per HW guide Table (Power supply filter caps).\n'
           'Unused: CONFIG_0..3, VIO_CFG (NC => 1.8/3.3V sideband), DPR, W_DISABLE2#, I2C, RFFE, ANTCTL, COEX, GPIO, WOWWAN#. UART on TPs (1.8V).')
    V = f'+3V7_S{n}'
    m = {}
    for p, nm in fm.items():
        if nm == '+3.3V': m[str(p)] = V
        elif nm == 'GND': m[str(p)] = 'GND'
        else: m[str(p)] = 'NC'
    m.update({'6': f'SLOT{n}_FCPO_N', '67': f'S{n}_RESET_N', '8': f'S{n}_WDIS1_N', '10': f'S{n}_LED_K',
              '7': f'SLOT{n}_USB2_DP', '9': f'SLOT{n}_USB2_DM', '31': f'SLOT{n}_USB3_TX_P', '29': f'SLOT{n}_USB3_TX_N',
              '37': f'SLOT{n}_USB3_RX_P', '35': f'SLOT{n}_USB3_RX_N', '43': f'SLOT{n}_PCIE_TX_P', '41': f'SLOT{n}_PCIE_TX_N',
              '49': f'SLOT{n}_PCIE_RX_P', '47': f'SLOT{n}_PCIE_RX_N', '55': f'SLOT{n}_REFCLK_P', '53': f'SLOT{n}_REFCLK_N',
              '50': f'SLOT{n}_PERST_N', '52': f'SLOT{n}_CLKREQ_N', '54': f'SLOT{n}_WAKE_N',
              '30': f'SIM{n}_RST', '32': f'SIM{n}_CLK', '34': f'SIM{n}_IO', '36': f'SIM{n}_VCC', '66': f'SIM{n}_CD',
              '22': f'S{n}_UART_TX', '28': f'S{n}_UART_RX'})
    s.part('wwan_carrier:M.2_KeyB_FM350', m, fields={'MPN': 'LOTES APCI0026-P001A (VERIFY height)'})
    s.part('Mechanical:MountingHole_Pad', {'1': 'GND'}, value='M.2 standoff', footprint='MountingHole:MountingHole_2.2mm_M2_Pad_Via', prefix='H',
           fields={'Notes': '3052 module screw position (30 x 52 mm) - verify against connector datum'})
    CP(s, V, 'GND', '220uF/6.3V', 'Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D', mpn='KEMET T520D227M006ATE015 (low ESR polymer) VERIFY')
    CP(s, V, 'GND', '220uF/6.3V', 'Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D', mpn='KEMET T520D227M006ATE015 (low ESR polymer) VERIFY')
    BYP(s, V, ['1uF/10V', '100nF', '33pF', '18pF', '10pF', '6.8pF'])
    s.brk()
    R(s, f'SLOT{n}_FCPO_N', 'GND', '47k')
    NMOS_SIG(s, f'SLOT{n}_RESET', f'S{n}_RESET_N'); R(s, f'SLOT{n}_RESET', 'GND', '100k')
    NMOS_SIG(s, f'SLOT{n}_WDIS', f'S{n}_WDIS1_N'); R(s, f'SLOT{n}_WDIS', 'GND', '100k')
    R(s, '+3V3', f'S{n}_LED_A', '1k'); LED(s, f'S{n}_LED_A', f'S{n}_LED_K', 'green')
    R(s, '+3V3', f'SLOT{n}_WAKE_N', '10k')
    s.part('74xGxx:74LVC1G08', {'1': 'PCIE_PERST_N', '2': f'S{n}_PCIE_EN_L', '5': '+3V3', '3': 'GND', '4': f'SLOT{n}_PERST_N'},
           footprint='Package_TO_SOT_SMD:SOT-353_SC-70-5', value='74LVC1G08GW', fields={'MPN': '74LVC1G08GW,125 (or SN74LVC1G08DCKR)'})
    C(s, '+3V3', 'GND', '100nF')
    R(s, f'SLOT{n}_PCIE_EN', f'S{n}_PCIE_EN_L', '1k', note='limits current if JP fitted while GPIO drives high')
    R(s, '+3V3', f'S{n}_PCIE_EN_L', '10k', note='default PCIe enabled')
    s.part('Jumper:Jumper_2_Open', {'1': f'S{n}_PCIE_EN_L', '2': 'GND'}, value='PCIe OFF (force USB)', footprint='Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical', prefix='JP')
    for t in (f'S{n}_UART_TX', f'S{n}_UART_RX', f'SLOT{n}_PERST_N', V): TP(s, t)
    s.brk()
    s.part('wwan_carrier:NanoSIM_CD', {'1': f'SIM{n}_VCC', '2': f'SIM{n}_RST', '3': f'SIM{n}_CLK', '7': f'SIM{n}_IO', '6': 'NC', '5': 'GND',
                                       'CD': f'SIM{n}_CD', 'SH': 'GND'}, fields={'MPN': 'CUI NSIM-2-C'})
    s.part('Power_Protection:TPD4E05U06DQA', {'1': f'SIM{n}_VCC', '2': f'SIM{n}_RST', '4': f'SIM{n}_CLK', '5': f'SIM{n}_IO', '3': 'GND',
                                               '10': 'NC', '9': 'NC', '7': 'NC', '6': 'NC'}, value='TPD4E05U06DQAR', fields={'MPN': 'TPD4E05U06DQAR'})
    C(s, f'SIM{n}_VCC', 'GND', '1uF'); C(s, f'SIM{n}_VCC', 'GND', '100nF')
    for t in ('RST', 'CLK', 'IO'): C(s, f'SIM{n}_{t}', 'GND', '22pF')

# ======================= Sheet 7: USB hub =======================
s = D.add(Sheet('usb_hub.kicad_sch', 'USB3 hub USB5744 + USB-C upstream (HD3SS3220)', 8, 700))
s.note('USB5744 (Microchip DS00001855J): SMBus slave mode (10k PU on SMCLK/SMDAT, sec 3.4.1), CFG_NON_REM 10k PU = ports 1-3 non-removable,\n'
       'CFG_BC_EN 200k PD = no battery charging, port 4 disabled (PRT_DIS_P4/M4 to 3.3V). VBUS_DET via 49.9k/100k divider (detachable upstream).\n'
       'VDD12 from +1V2 buck (688mA typ, 4 SS ports). RBIAS 12k 1%. 25MHz crystal. PRT_CTLx unused (slot power is switched by the 3.7V bucks).\n'
       'Upstream USB-C (UFP only): HD3SS3220 PORT=GND (UFP), ADDR=NC (GPIO mode), ENn_CC/ENn_MUX=GND; it presents Rd and muxes SS by plug orientation.\n'
       '  VDD5 is taken from VBUS (UFP-only design; VERIFY with TI that VBUS-powered VDD5 is acceptable - else add a 5V rail).\n'
       'Hub upstream TX AC caps 100nF between hub and mux; hub downstream TX caps 100nF on this sheet (slot RX).\n'
       'ESD: TPD4EUSB30 on SS pairs + D+/D-/CC at the connector; SMAJ5.0A on VBUS.')
s.part('Connector:USB_C_Receptacle', {'S1': 'SHIELD_C', 'A1': 'GND', 'A4': 'VBUS_C', 'A5': 'CC1', 'B5': 'CC2', 'A7': 'USBC_DM', 'B7': 'USBC_DM',
                                      'A6': 'USBC_DP', 'B6': 'USBC_DP', 'B10': 'C_RX1_N', 'B11': 'C_RX1_P', 'A3': 'C_TX1_N', 'A2': 'C_TX1_P',
                                      'A10': 'C_RX2_N', 'A11': 'C_RX2_P', 'B3': 'C_TX2_N', 'B2': 'C_TX2_P', 'A8': 'NC', 'B8': 'NC'},
       value='USB-C (USB3.2 Gen1, UFP)', footprint='Connector_USB:USB_C_Receptacle_Amphenol_12401610E4-2A', fields={'MPN': 'Amphenol 12401610E4#2A'})
R(s, 'SHIELD_C', 'GND', '1M', 'R0603'); C(s, 'SHIELD_C', 'GND', '4.7nF/100V', 'C0603')
s.part('Diode:SMAJ5.0A', {'1': 'VBUS_C', '2': 'GND'}, value='SMAJ5.0A', footprint='Diode_SMD:D_SMA', fields={'MPN': 'SMAJ5.0A (unidirectional, pin1=K to VBUS)'})
C(s, 'VBUS_C', 'GND', '1uF/16V')
s.part('Power_Protection:TPD4EUSB30', {'1': 'C_TX1_P', '2': 'C_TX1_N', '4': 'C_RX1_P', '5': 'C_RX1_N', '3': 'GND', '10': 'NC', '9': 'NC', '7': 'NC', '6': 'NC'},
       value='TPD4EUSB30DQAR', footprint='Package_SON:USON-10_2.5x1.0mm_P0.5mm', fields={'MPN': 'TPD4EUSB30DQAR'})
s.part('Power_Protection:TPD4EUSB30', {'1': 'C_TX2_P', '2': 'C_TX2_N', '4': 'C_RX2_P', '5': 'C_RX2_N', '3': 'GND', '10': 'NC', '9': 'NC', '7': 'NC', '6': 'NC'},
       value='TPD4EUSB30DQAR', footprint='Package_SON:USON-10_2.5x1.0mm_P0.5mm', fields={'MPN': 'TPD4EUSB30DQAR'})
s.part('Power_Protection:TPD4EUSB30', {'1': 'USBC_DP', '2': 'USBC_DM', '4': 'CC1', '5': 'CC2', '3': 'GND', '10': 'NC', '9': 'NC', '7': 'NC', '6': 'NC'},
       value='TPD4EUSB30DQAR', footprint='Package_SON:USON-10_2.5x1.0mm_P0.5mm', fields={'MPN': 'TPD4EUSB30DQAR'})
FLAG(s, 'VBUS_C')
s.brk()
s.part('wwan_carrier:HD3SS3220', {'2': 'CC1', '1': 'CC2', '4': 'GND', '22': 'NC', '3': 'NC', '5': 'HD_VBUS_DET', '29': 'GND', '12': 'GND',
                                  '11': 'HD_DIR', '27': 'NC', '23': 'NC', '24': 'NC', '25': 'NC', '26': 'NC', '30': 'HD_VDD5', '8': '+3V3',
                                  '13': 'GND', '28': 'GND', '31': 'GND', '6': 'HUB_UP_TX_P_AC', '7': 'HUB_UP_TX_N_AC', '9': 'HUB_UP_RX_P', '10': 'HUB_UP_RX_N',
                                  '17': 'C_TX1_P', '16': 'C_TX1_N', '15': 'C_RX1_P', '14': 'C_RX1_N', '21': 'C_TX2_P', '20': 'C_TX2_N', '19': 'C_RX2_P', '18': 'C_RX2_N'},
       fields={'MPN': 'HD3SS3220RNHR'})
R(s, 'VBUS_C', 'HD_VBUS_DET', '910k', note='DS: 900k required')
R(s, '+3V3', 'HD_DIR', '200k'); TP(s, 'HD_DIR')
FB(s, 'VBUS_C', 'HD_VDD5', 'BLM18PG221SN1D'); C(s, 'HD_VDD5', 'GND', '1uF/16V'); C(s, 'HD_VDD5', 'GND', '100nF')
C(s, '+3V3', 'GND', '100nF')
C(s, 'HUB_UP_TX_P', 'HUB_UP_TX_P_AC', '100nF', 'C0201'); C(s, 'HUB_UP_TX_N', 'HUB_UP_TX_N_AC', '100nF', 'C0201')
FLAG(s, 'HD_VDD5')
s.brk()
hub = {'45': 'USBC_DP', '46': 'USBC_DM', '47': 'HUB_UP_TX_P', '48': 'HUB_UP_TX_N', '50': 'HUB_UP_RX_P', '51': 'HUB_UP_RX_N',
       '54': 'HUB_XI', '53': 'HUB_XO', '56': 'HUB_RBIAS', '52': 'GND', '42': 'HUB_RESET_N', '37': 'HUB_VBUS_DET',
       '38': 'I2C_SCL', '39': 'I2C_SDA', '40': 'HUB_CFG_BC', '41': 'HUB_CFG_NONREM', '36': 'NC', '35': 'NC', '34': 'NC', '32': 'NC',
       '24': 'PRT_DIS_P4', '25': 'PRT_DIS_M4', '26': 'NC', '27': 'NC', '29': 'NC', '30': 'NC', '57': 'GND'}
for p in ('16', '31', '44', '55'): hub[p] = '+3V3'
for p in ('5', '12', '15', '21', '28', '33', '43', '49'): hub[p] = '+1V2'
for n, (dp, dm, tp, tn, rp, rn) in zip((1, 2, 3), (('1', '2', '3', '4', '6', '7'), ('8', '9', '10', '11', '13', '14'), ('17', '18', '19', '20', '22', '23'))):
    hub.update({dp: f'SLOT{n}_USB2_DP', dm: f'SLOT{n}_USB2_DM', tp: f'HUB_DN{n}_TX_P', tn: f'HUB_DN{n}_TX_N', rp: f'SLOT{n}_USB3_TX_P', rn: f'SLOT{n}_USB3_TX_N'})
s.part('wwan_carrier:USB5744', hub, fields={'MPN': 'USB5744-I/2G (industrial) VERIFY suffix'})
for n in (1, 2, 3):
    C(s, f'HUB_DN{n}_TX_P', f'SLOT{n}_USB3_RX_P', '100nF', 'C0201'); C(s, f'HUB_DN{n}_TX_N', f'SLOT{n}_USB3_RX_N', '100nF', 'C0201')
R(s, 'HUB_RBIAS', 'GND', '12k 1%')
s.part('Device:Crystal_GND24', {'1': 'HUB_XI', '3': 'HUB_XO', '2': 'GND', '4': 'GND'}, value='25MHz', footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
       fields={'MPN': 'ABM8-25.000MHZ-B2-T (VERIFY CL vs load caps)'})
C(s, 'HUB_XI', 'GND', '18pF'); C(s, 'HUB_XO', 'GND', '18pF'); R(s, 'HUB_XI', 'HUB_XO', '1M', dnp=True)
R(s, '+3V3', 'HUB_RESET_N', '10k'); C(s, 'HUB_RESET_N', 'GND', '100nF')
R(s, 'VBUS_C', 'HUB_VBUS_DET', '49.9k'); R(s, 'HUB_VBUS_DET', 'GND', '100k')
R(s, '+3V3', 'I2C_SCL', '10k', note='SMBus-mode strap'); R(s, '+3V3', 'I2C_SDA', '10k', note='SMBus-mode strap')
R(s, 'HUB_CFG_BC', 'GND', '200k', note='no BC'); R(s, '+3V3', 'HUB_CFG_NONREM', '10k', note='ports 1-3 non-removable')
R(s, '+3V3', 'PRT_DIS_P4', '10k'); R(s, '+3V3', 'PRT_DIS_M4', '10k')
BYP(s, '+3V3', ['100nF'] * 4 + ['10uF/6.3V'], 'C0402'); BYP(s, '+1V2', ['100nF'] * 8 + ['10uF/6.3V', '10uF/6.3V'], 'C0402')
TP(s, 'HUB_RESET_N')

# ======================= Sheet 8: control =======================
s = D.add(Sheet('control.kicad_sch', 'Control: I2C GPIO expanders, host header, PG and status LEDs', 9, 800))
s.note('Host header J801 (2x5 2.54mm) to FRDM-IMX95 3.3V I2C (VERIFY host header voltage is 3.3V; bus also hosts USB5744 SMBus and PCA9306->PI7C).\n'
       'U801 TCA6416A @0x20 (ADDR=GND): outputs - per-slot PWR_EN, FCPO#, RESET (active-high to NFET), WDIS (active-high to NFET), PCIE_EN; HUB_RESET_N.\n'
       'U802 TCA6416A @0x21 (ADDR=VCCP): inputs - slot PG, slot WAKE#, rail PGs; outputs - 2 user LEDs. P14-P17 spare (test pads).\n'
       'All TCA6416A pins are inputs after POR -> board pull-ups/pull-downs define safe defaults (slots OFF, modules held in FCPO#).\n'
       'Other I2C addresses: USB5744 SMBus (default 0x2D, VERIFY), PI7C switch 0x6F (via PCA9306). HD3SS3220 I2C disabled (GPIO mode).\n'
       'Bus pull-ups: 10k on hub sheet (strap); 4.7k here DNP (host board normally provides).\n'
       'PG LEDs: 2N7002 driven from each open-drain PG net (LED on = rail good).')
s.part('Connector_Generic:Conn_02x05_Odd_Even', {'1': 'GND', '2': 'GND', '3': 'I2C_SCL', '4': 'I2C_SDA', '5': 'EXP_INT_N', '6': 'EXP_RESET_N',
                                                  '7': 'NC', '8': 'CARRIER_3V3_SENSE', '9': 'GND', '10': 'GND'},
       value='HOST I2C/CTRL', footprint='Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical')
R(s, '+3V3', 'CARRIER_3V3_SENSE', '1k', note='host can sense carrier powered')
R(s, '+3V3', 'I2C_SCL', '4.7k', dnp=True); R(s, '+3V3', 'I2C_SDA', '4.7k', dnp=True)
R(s, '+3V3', 'EXP_INT_N', '10k'); R(s, '+3V3', 'EXP_RESET_N', '10k')
for t in ('I2C_SCL', 'I2C_SDA', 'EXP_INT_N'): TP(s, t)
s.brk()
o = ['SLOT1_PWR_EN', 'SLOT1_FCPO_N', 'SLOT1_RESET', 'SLOT1_WDIS', 'SLOT1_PCIE_EN', 'SLOT2_PWR_EN', 'SLOT2_FCPO_N', 'SLOT2_RESET',
     'SLOT2_WDIS', 'SLOT2_PCIE_EN', 'SLOT3_PWR_EN', 'SLOT3_FCPO_N', 'SLOT3_RESET', 'SLOT3_WDIS', 'SLOT3_PCIE_EN', 'HUB_RESET_N']
i2 = ['SLOT1_PG', 'SLOT2_PG', 'SLOT3_PG', 'SLOT1_WAKE_N', 'SLOT2_WAKE_N', 'SLOT3_WAKE_N', 'PG_3V3', 'PG_0V95', 'PG_1V8', 'PG_1V2',
      'USER_LED1', 'USER_LED2', 'EXP_SPARE4', 'EXP_SPARE5', 'EXP_SPARE6', 'EXP_SPARE7']
for addr, lst in (('GND', o), ('+3V3', i2)):
    m = {'2': '+3V3', '24': '+3V3', '22': 'I2C_SCL', '23': 'I2C_SDA', '1': 'EXP_INT_N', '3': 'EXP_RESET_N', '21': addr, '12': 'GND'}
    pins = [str(4 + i) for i in range(8)] + [str(13 + i) for i in range(8)]
    m.update(dict(zip(pins, lst)))
    s.part('wwan_carrier:TCA6416A', m, fields={'MPN': 'TCA6416APWR (TCA6416ATPWRQ1 = AEC option, VERIFY)'})
    C(s, '+3V3', 'GND', '100nF'); C(s, '+3V3', 'GND', '100nF')
for t in ('EXP_SPARE4', 'EXP_SPARE5', 'EXP_SPARE6', 'EXP_SPARE7'): TP(s, t)
s.brk()
for net in ('PG_3V3', 'PG_0V95', 'PG_1V8', 'PG_1V2', 'SLOT1_PG', 'SLOT2_PG', 'SLOT3_PG'):
    tag = net.replace('PG_', '').replace('_PG', '')
    R(s, '+3V3', f'LEDA_{tag}', '1k'); LED(s, f'LEDA_{tag}', f'LEDK_{tag}', 'green'); NMOS_SIG(s, net, f'LEDK_{tag}')
for u in ('USER_LED1', 'USER_LED2'):
    R(s, u, f'{u}_A', '1k'); LED(s, f'{u}_A', 'GND', 'yellow', 'LTST-C191KSKT')
for i in range(4):
    s.part('Mechanical:MountingHole', {}, value='M3', footprint='MountingHole:MountingHole_3.2mm_M3', prefix='H')

# ======================= finalize / write =======================
if os.environ.get("KEEP"): D.sheets=[s_ for s_ in D.sheets if s_.fname.split(".")[0] in os.environ["KEEP"].split(",")]
D.finalize()
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for sh in D.sheets: D.write_sheet(sh, out)
D.write_root(out, 'WWAN CARRIER rev 0.1 (spin-1 bench prototype) - hierarchical schematic, generated from datasheet pin tables.\n'
             'Host: NXP FRDM-IMX95 -> M.2 Key-M -> ADT-Link M41 riser (PCIe x1) -> this board\'s x1 gold finger; USB-C upstream to dev board.\n'
             'Sheets: 2 power input/system rails, 3 slot 3.7V bucks, 4 PCIe switch, 5-7 M.2 slots 1-3, 8 USB hub, 9 control.\n'
             'Cross-sheet connectivity uses global labels (no sheet pins). See per-sheet notes for assumptions and VERIFY items.')
# custom library
lib = ['kicad_symbol_lib', ['version', '20241209'], ['generator', ('S', 'kicad_symbol_editor')], ['generator_version', ('S', '9.0')]] + \
      [engine.CUSTOM[k] for k in engine.CUSTOM]
open(f'{out}/wwan_carrier.kicad_sym', 'w').write(engine.dump(lib) + '\n')
open(f'{out}/sym-lib-table', 'w').write('(sym_lib_table\n  (version 7)\n  (lib (name "wwan_carrier")(type "KiCad")(uri "${KIPRJMOD}/wwan_carrier.kicad_sym")(options "")(descr "WWAN carrier custom symbols"))\n)\n')
# net report
pins = {}
for sh in D.sheets:
    for it in sh.items:
        if it.kind != 'sym': continue
        for c in it.conns:
            if c['net'] in ('NC',): continue
            pins.setdefault(c['net'], []).append((sh.fname, it.ref, '/'.join(p[0] for p in c['pins'])))
json.dump({k: v for k, v in sorted(pins.items())}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'netlist_report.json'), 'w'), indent=1)
single = {k: v for k, v in pins.items() if len(v) < 2}
print('sheets:', [(sh.fname, sh.paper[0]) for sh in D.sheets])
print('nets:', len(pins), 'single-connection nets:', single)
