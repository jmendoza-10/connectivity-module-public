import math, uuid, copy, re
from sexp import parse, dump, q, find, name

PROJECT = "wwan-carrier"
NS = uuid.UUID('6b3f6a3e-1d2c-4a5b-9c8d-7e6f5a4b3c2d')
_uc = {}
def U(key):
    n = _uc.get(key, 0); _uc[key] = n + 1
    return str(uuid.uuid5(NS, f"{key}#{n}"))

G = 2.54
def snap(v): return round(round(v / 1.27) * 1.27, 4)

# ---------------- symbol library handling ----------------
_stock = {}
def stock_lib(lib):
    if lib not in _stock:
        t = parse(open(f'/usr/share/kicad/symbols/{lib}.kicad_sym').read())[0]
        _stock[lib] = {name(s): s for s in find(t, 'symbol')}
    return _stock[lib]

def flatten(lib, sym):
    syms = stock_lib(lib)
    s = copy.deepcopy(syms[sym])
    ext = find(s, 'extends')
    if not ext:
        return s
    parent = flatten(lib, ext[0][1][1])
    pname = name(parent)
    out = [e for e in parent if not (isinstance(e, list) and e and e[0] in ('property', 'symbol'))]
    out[1] = ('S', sym)
    # properties: child overrides parent
    props = {p[1][1]: p for p in find(parent, 'property')}
    for p in find(s, 'property'):
        props[p[1][1]] = p
    body = list(props.values())
    for u in find(parent, 'symbol'):
        u = copy.deepcopy(u)
        u[1] = ('S', sym + name(u)[len(pname):])
        body.append(u)
    # insert props & units after header tokens
    return out + body

class SymDef:
    """Pin geometry for placing an instance."""
    def __init__(self, lib_id, sexpr):
        self.lib_id = lib_id
        self.sexpr = sexpr
        self.pins = []   # (unit, num, name, type, x, y, angle, hidden)
        base = name(sexpr).split(':')[-1]
        for u in find(sexpr, 'symbol'):
            m = re.match(r'.*_(\d+)_(\d+)$', name(u))
            unit, style = int(m.group(1)), int(m.group(2))
            if style not in (0, 1):
                continue
            for p in find(u, 'pin'):
                at = find(p, 'at')[0]
                nm = find(p, 'name')[0][1][1]; nu = find(p, 'number')[0][1][1]
                hidden = ('hide' in p) or any(isinstance(e, list) and e[:2] == ['hide', 'yes'] for e in p)
                self.pins.append((unit, nu, nm, p[1], float(at[1]), float(at[2]), int(float(at[3])), hidden))
        self.units = sorted({p[0] for p in self.pins if p[0] > 0}) or [1]
        self.power = bool(find(sexpr, 'power'))
    def unit_pins(self, unit):
        return [p for p in self.pins if p[0] in (0, unit)]

_defs = {}
CUSTOM = {}   # name -> sexpr (wwan_carrier lib)
def symdef(lib_id):
    if lib_id in _defs: return _defs[lib_id]
    lib, sym = lib_id.split(':')
    if lib == 'wwan_carrier':
        sx = copy.deepcopy(CUSTOM[sym])
    else:
        sx = flatten(lib, sym)
    sx[1] = ('S', lib_id)
    d = SymDef(lib_id, sx); _defs[lib_id] = d
    return d

# ---------------- custom symbol builder ----------------
def font(): return ['effects', ['font', ['size', '1.27', '1.27']]]
def fonth(): return ['effects', ['font', ['size', '1.27', '1.27']], ['hide', 'yes']]

def make_symbol(sym, ref, value, units, footprint='', datasheet='', descr='', fields=None, unit_names=None):
    """units: list of dict(left=[...], right=[...]); entries: None (gap) or (num,name,type) or list of such (stacked)."""
    out = ['symbol', ('S', sym), ['pin_names', ['offset', '1.016']], ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes']]
    out.append(['property', ('S', 'Reference'), ('S', ref), ['at', '0', '2.54', '0'], font()])
    out.append(['property', ('S', 'Value'), ('S', value), ['at', '0', '0', '0'], font()])
    out.append(['property', ('S', 'Footprint'), ('S', footprint), ['at', '0', '0', '0'], fonth()])
    out.append(['property', ('S', 'Datasheet'), ('S', datasheet), ['at', '0', '0', '0'], fonth()])
    out.append(['property', ('S', 'Description'), ('S', descr), ['at', '0', '0', '0'], fonth()])
    for k, v in (fields or {}).items():
        out.append(['property', ('S', k), ('S', v), ['at', '0', '0', '0'], fonth()])
    for ui, u in enumerate(units, 1):
        L, R = u.get('left', []), u.get('right', [])
        n = max(len(L), len(R), 1)
        def maxlen(lst):
            m = 0
            for e in lst:
                if e is None: continue
                if isinstance(e, tuple): e = [e]
                m = max(m, len(e[0][1]))
            return m
        half = math.ceil(((maxlen(L) + maxlen(R)) * 1.05 + 5) / 2 / G) * G
        top = math.ceil((n - 1) / 2) * G
        body = ['symbol', ('S', f'{sym}_{ui}_1'),
                ['rectangle', ['start', f'{-half:g}', f'{top + G:g}'], ['end', f'{half:g}', f'{top - n * G:g}'],
                 ['stroke', ['width', '0.254'], ['type', 'default']], ['fill', ['type', 'background']]]]
        for side, lst in (('L', L), ('R', R)):
            for i, e in enumerate(lst):
                if e is None: continue
                if isinstance(e, tuple): e = [e]
                y = top - i * G
                x = -half - G if side == 'L' else half + G
                ang = '0' if side == 'L' else '180'
                for k, (num, nm, typ) in enumerate(e):
                    pin = ['pin', typ, 'line', ['at', f'{x:g}', f'{y:g}', ang], ['length', '2.54']]
                    if k > 0: pin.append(['hide', 'yes'])
                    pin += [['name', ('S', nm), font()], ['number', ('S', str(num)), font()]]
                    body.append(pin)
        out.append(body)
    out.append(['embedded_fonts', 'no'])
    CUSTOM[sym] = out
    return out

# ---------------- schematic sheet ----------------
PAPERS = [('A3', 420, 297), ('A2', 594, 420), ('A1', 841, 594), ('A0', 1189, 841)]
STUB = 2.54

def rot(x, y, r):
    a = math.radians(r)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))

DIRV = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}

class Item:
    pass

class Sheet:
    def __init__(self, fname, title, page, refbase):
        self.fname, self.title, self.page = fname, title, page
        self.refbase = refbase
        self.items = []
        self.counters = {}
        self.uuid = U('sheet:' + fname)
        self.nets = set()
    def ref(self, prefix):
        n = self.counters.get(prefix, 0) + 1; self.counters[prefix] = n
        return f'{prefix}{self.refbase + n}'
    def note(self, text):
        it = Item(); it.kind = 'note'; it.text = text
        lines = text.split('\n')
        it.w = max(len(l) for l in lines) * 1.05 + 4
        it.h = len(lines) * 2.1 + 4
        self.items.append(it); return it
    def brk(self):
        it = Item(); it.kind = 'break'; it.w = it.h = 0; self.items.append(it)
    def part(self, lib_id, nets, value=None, ref=None, prefix=None, unit=1, rot_=0, footprint=None,
             fields=None, dnp=False, in_bom=True, refdes_shared=None):
        d = symdef(lib_id)
        it = Item(); it.kind = 'sym'; it.d = d; it.unit = unit; it.rot = rot_
        props = {p[1][1]: p[2][1] for p in find(d.sexpr, 'property')}
        if ref is None:
            pre = prefix or re.sub(r'[^A-Z#]', '', props.get('Reference', 'U')) or 'U'
            ref = self.ref(pre)
        it.ref = ref
        it.value = value if value is not None else props.get('Value', '')
        it.footprint = footprint if footprint is not None else props.get('Footprint', '')
        it.datasheet = props.get('Datasheet', '')
        it.descr = props.get('Description', '')
        it.fields = fields or {}
        it.dnp = dnp; it.in_bom = in_bom and not d.power
        # group pins by position
        groups = {}
        for (u, num, nm, typ, x, y, ang, hid) in d.unit_pins(unit):
            groups.setdefault((x, y, ang), []).append((num, nm, typ, hid))
        it.conns = []
        used = set()
        for (x, y, ang), pins in groups.items():
            nset = {nets[p[0]] for p in pins if p[0] in nets}
            for p in pins:
                if p[0] in nets: used.add(p[0])
            if not nset:
                # name-based fallback
                nset = {nets[p[1]] for p in pins if p[1] in nets and p[1] not in [q_[0] for q_ in pins]}
                for p in pins:
                    if p[1] in nets: used.add(p[1])
            if len(nset) != 1:
                raise Exception(f'{it.ref} {lib_id}: pins {[p[0] + "/" + p[1] for p in pins]} nets={nset}')
            net = nset.pop()
            rx, ry = rot(x, y, rot_)
            ox, oy = DIRV[(ang + 180 + rot_) % 360]  # outward in y-up coords
            it.conns.append(dict(px=rx, py=-ry, ox=ox, oy=-oy, net=net, pins=pins))
            if net not in ('NC',):
                self.nets.add(net)
        extra = set(nets) - used
        if extra:
            raise Exception(f'{it.ref} {lib_id}: unknown pins in map {extra}')
        # bbox relative to origin
        xs, ys = [0], [0]
        for c in it.conns:
            L = 0 if c['net'] == 'NC' else STUB + (5 if c['net'] == 'GND' else len(c['net']) * 1.1 + 4)
            xs += [c['px'], c['px'] + c['ox'] * L]
            ys += [c['py'], c['py'] + c['oy'] * L]
        it.bx0, it.bx1 = min(xs) - 4, max(xs) + 4
        it.by0, it.by1 = min(ys) - 6, max(ys) + 6
        it.w, it.h = it.bx1 - it.bx0, it.by1 - it.by0
        self.items.append(it)
        return it

    # layout
    def layout(self):
        for pname, W, H in PAPERS:
            ok = True
            x, y, colw = 12.7, 22.86, 0
            ymax = H - 50
            pos = []
            for it in self.items:
                if it.kind == 'break':
                    if colw: x += colw + 5; y = 22.86; colw = 0
                    pos.append(None); continue
                if y + it.h > ymax and y > 22.86 + 1:
                    x += colw + 5; y = 22.86; colw = 0
                pos.append((x, y))
                colw = max(colw, it.w)
                y += it.h + 3
            if x + colw > W - 10:
                ok = False
            if ok:
                self.paper = (pname, W, H)
                for it, p in zip(self.items, pos):
                    if p is None: continue
                    if it.kind == 'sym':
                        it.X = snap(p[0] - it.bx0); it.Y = snap(p[1] - it.by0)
                    else:
                        it.X = snap(p[0]); it.Y = snap(p[1])
                return
        raise Exception('sheet too big ' + self.fname)

# ---------------- writer ----------------
class Design:
    def __init__(self, title):
        self.title = title
        self.sheets = []
        self.root_uuid = U('root')
        self.pwr_n = 0; self.flg_n = 0
    def add(self, sheet):
        self.sheets.append(sheet); return sheet
    def finalize(self):
        cnt = {}
        for s in self.sheets:
            for n in s.nets:
                cnt.setdefault(n, set()).add(s.fname)
        self.global_nets = {n for n, ss in cnt.items() if len(ss) > 1 or n.startswith('+')}
        for s in self.sheets:
            s.layout()

    def title_block(self, s):
        return ['title_block', ['title', ('S', s.title)], ['date', ('S', '2026-10-09')], ['rev', ('S', '0.1')],
                ['company', ('S', 'Jorge Mendoza - WWAN carrier (spin 1 bench prototype)')],
                ['comment', '1', ('S', 'Auto-generated schematic (label-based netlist style); see notes on each sheet')],
                ['comment', '2', ('S', 'Datasheet-verified pinouts noted per sheet; items marked VERIFY are not yet confirmed')]]

    def sym_instance(self, s, it, X, Y, rot_, ref, value, footprint, fields, unit=1, dnp=False, in_bom=True, power=False, hide_ref=False):
        d = it.d if hasattr(it, 'd') else it
        e = ['symbol', ['lib_id', ('S', d.lib_id)], ['at', f'{X:g}', f'{Y:g}', str(rot_)], ['unit', str(unit)],
             ['exclude_from_sim', 'no'], ['in_bom', 'yes' if in_bom else 'no'], ['on_board', 'yes' if not power else 'yes'],
             ['dnp', 'yes' if dnp else 'no'], ['uuid', ('S', U('sym:' + s.fname + ref))]]
        # field positions: ref above, value below
        ys = [c['py'] for c in getattr(it, 'conns', [])] or [0]
        top = min(ys) - 3.81 if not power else -5
        bot = max(ys) + 3.81 if not power else 5
        fang = rot_ if rot_ in (90, 270) and not power else 0
        def prop(k, v, x, y, hide=False):
            eff = ['effects', ['font', ['size', '1.27', '1.27']]]
            if hide: eff.append(['hide', 'yes'])
            return ['property', ('S', k), ('S', v), ['at', f'{snap(x):g}', f'{snap(y):g}', str(fang)], eff]
        e.append(prop('Reference', ref, X, Y + top, hide=hide_ref))
        e.append(prop('Value', value, X, Y + bot))
        e.append(prop('Footprint', footprint, X, Y, hide=True))
        e.append(prop('Datasheet', getattr(it, 'datasheet', '') or '', X, Y, hide=True))
        e.append(prop('Description', getattr(it, 'descr', '') or '', X, Y, hide=True))
        for k, v in (fields or {}).items():
            e.append(prop(k, v, X, Y, hide=True))
        for p in d.unit_pins(unit):
            e.append(['pin', ('S', p[1]), ['uuid', ('S', U('pin:' + s.fname + ref + p[1]))]])
        path = f'/{self.root_uuid}/{s.uuid}'
        e.append(['instances', ['project', ('S', PROJECT), ['path', ('S', path), ['reference', ('S', ref)], ['unit', str(unit)]]]])
        return e

    def write_sheet(self, s, outdir):
        body = []
        libs = {}
        def uselib(d): libs[d.lib_id] = d.sexpr
        gnd = symdef('power:GND')
        for it in s.items:
            if it.kind == 'note':
                body.append(['text', ('S', it.text), ['exclude_from_sim', 'no'], ['at', f'{it.X:g}', f'{it.Y:g}', '0'],
                             ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left', 'top']], ['uuid', ('S', U('txt:' + s.fname))]])
                continue
            if it.kind != 'sym': continue
            uselib(it.d)
            body.append(self.sym_instance(s, it, it.X, it.Y, it.rot, it.ref, it.value, it.footprint,
                                          it.fields, unit=it.unit, dnp=it.dnp, in_bom=it.in_bom, power=it.d.power,
                                          hide_ref=it.d.power))
            for c in it.conns:
                px, py = snap(it.X + c['px']), snap(it.Y + c['py'])
                if c['net'] == 'NC':
                    body.append(['no_connect', ['at', f'{px:g}', f'{py:g}'], ['uuid', ('S', U('nc:' + s.fname))]])
                    continue
                ex, ey = snap(px + c['ox'] * STUB), snap(py + c['oy'] * STUB)
                body.append(['wire', ['pts', ['xy', f'{px:g}', f'{py:g}'], ['xy', f'{ex:g}', f'{ey:g}']],
                             ['stroke', ['width', '0'], ['type', 'default']], ['uuid', ('S', U('w:' + s.fname))]])
                ox, oy = c['ox'], c['oy']
                if c['net'] == 'GND':
                    uselib(gnd)
                    # GND graphic points down at rot 0; rotate to point outward
                    r = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[(round(ox), round(oy))]
                    self.pwr_n += 1
                    g = Item(); g.d = gnd; g.conns = []; g.datasheet = ''; g.descr = ''
                    body.append(self.sym_instance(s, g, ex, ey, r, f'#PWR0{self.pwr_n:03d}', 'GND', '', {}, power=True, in_bom=False, hide_ref=True))
                    continue
                ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(round(ox), round(oy))]
                just = 'left' if ang in (0, 90) else 'right'
                if c['net'] in self.global_nets:
                    body.append(['global_label', ('S', c['net']), ['shape', 'passive'], ['at', f'{ex:g}', f'{ey:g}', str(ang)],
                                 ['fields_autoplaced', 'yes'], ['effects', ['font', ['size', '1.27', '1.27']], ['justify', just]],
                                 ['uuid', ('S', U('gl:' + s.fname))],
                                 ['property', ('S', 'Intersheetrefs'), ('S', '${INTERSHEET_REFS}'), ['at', f'{ex:g}', f'{ey:g}', '0'],
                                  ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left'], ['hide', 'yes']]]])
                else:
                    body.append(['label', ('S', c['net']), ['at', f'{ex:g}', f'{ey:g}', str(ang)], ['fields_autoplaced', 'yes'],
                                 ['effects', ['font', ['size', '1.27', '1.27']], ['justify', just, 'bottom']], ['uuid', ('S', U('l:' + s.fname))]])
        hdr = ['kicad_sch', ['version', '20250114'], ['generator', ('S', 'eeschema')], ['generator_version', ('S', '9.0')],
               ['uuid', ('S', s.uuid)], ['paper', ('S', s.paper[0])], self.title_block(s), ['lib_symbols'] + list(libs.values())]
        doc = hdr + body + [['embedded_fonts', 'no']]
        open(f'{outdir}/{s.fname}', 'w').write(dump(doc) + '\n')

    def write_root(self, outdir, notes):
        body = []
        x, y = 25.4, 50.8
        for i, s in enumerate(self.sheets):
            w, h = 60.96, 20.32
            col, row = i % 4, i // 4
            sx, sy = 25.4 + col * 88.9, 63.5 + row * 50.8
            body.append(['sheet', ['at', f'{sx:g}', f'{sy:g}'], ['size', f'{w:g}', f'{h:g}'], ['exclude_from_sim', 'no'],
                         ['in_bom', 'yes'], ['on_board', 'yes'], ['dnp', 'no'], ['fields_autoplaced', 'yes'],
                         ['stroke', ['width', '0.1524'], ['type', 'solid']], ['fill', ['color', '0', '0', '0', '0.0000']],
                         ['uuid', ('S', s.uuid)],
                         ['property', ('S', 'Sheetname'), ('S', s.title), ['at', f'{sx:g}', f'{sy - 0.7112:g}', '0'],
                          ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left', 'bottom']]],
                         ['property', ('S', 'Sheetfile'), ('S', s.fname), ['at', f'{sx:g}', f'{sy + h + 0.5:g}', '0'],
                          ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left', 'top']]],
                         ['instances', ['project', ('S', PROJECT), ['path', ('S', f'/{self.root_uuid}'), ['page', ('S', str(s.page))]]]]])
        body.append(['text', ('S', notes), ['exclude_from_sim', 'no'], ['at', '25.4', '180', '0'],
                     ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left', 'top']], ['uuid', ('S', U('roottxt'))]])
        doc = ['kicad_sch', ['version', '20250114'], ['generator', ('S', 'eeschema')], ['generator_version', ('S', '9.0')],
               ['uuid', ('S', self.root_uuid)], ['paper', ('S', 'A3')],
               ['title_block', ['title', ('S', self.title)], ['date', ('S', '2026-10-09')], ['rev', ('S', '0.1')],
                ['company', ('S', 'Jorge Mendoza - WWAN carrier (spin 1 bench prototype)')]],
               ['lib_symbols']] + body + [['sheet_instances', ['path', ('S', '/'), ['page', ('S', '1')]]], ['embedded_fonts', 'no']]
        open(f'{outdir}/{PROJECT}.kicad_sch', 'w').write(dump(doc) + '\n')
