"""KiCad 9 schematic generator v2: explicit placement + orthogonal A* auto-router + hierarchical sheets."""
import math, uuid, copy, re, heapq
from sexp import parse, dump, q, find, name

PROJECT = "wwan-carrier"
NS = uuid.UUID('6b3f6a3e-1d2c-4a5b-9c8d-7e6f5a4b3c2d')
_uc = {}
def U(key):
    n = _uc.get(key, 0); _uc[key] = n + 1
    return str(uuid.uuid5(NS, f"{key}#{n}"))

G = 2.54
GR = 1.27  # routing grid
def snap(v): return round(round(v / GR) * GR, 4)
def gi(v): return int(round(v / GR))
CW = 1.22  # approx char width (mm) for 1.27mm font (measured)
def tw(s): return len(s) * CW + 0.6

# ---------------- symbols ----------------
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
    props = {p[1][1]: p for p in find(parent, 'property')}
    for p in find(s, 'property'):
        props[p[1][1]] = p
    body = list(props.values())
    for u in find(parent, 'symbol'):
        u = copy.deepcopy(u)
        u[1] = ('S', sym + name(u)[len(pname):])
        body.append(u)
    return out + body

def rot(x, y, r):
    r %= 360
    if r == 0: return (x, y)
    if r == 90: return (-y, x)
    if r == 180: return (-x, -y)
    return (y, -x)

DIRV = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}   # symbol coords (y up)

class SymDef:
    def __init__(self, lib_id, sexpr):
        self.lib_id = lib_id
        self.sexpr = sexpr
        self.pins = []   # (unit, num, name, type, x, y, angle, hidden, length)
        self.gfx = {}    # unit -> list of points (symbol coords)
        for u in find(sexpr, 'symbol'):
            m = re.match(r'.*_(\d+)_(\d+)$', name(u))
            unit, style = int(m.group(1)), int(m.group(2))
            if style not in (0, 1):
                continue
            pts = self.gfx.setdefault(unit, [])
            for p in find(u, 'pin'):
                at = find(p, 'at')[0]
                nm = find(p, 'name')[0][1][1]; nu = find(p, 'number')[0][1][1]
                ln = float(find(p, 'length')[0][1])
                hidden = ('hide' in p) or any(isinstance(e, list) and e[:2] == ['hide', 'yes'] for e in p)
                x, y, a = float(at[1]), float(at[2]), int(float(at[3]))
                self.pins.append((unit, nu, nm, p[1], x, y, a, hidden, ln))
                dx, dy = DIRV[a]
                pts += [(x, y), (x + dx * ln, y + dy * ln)]
            for r in find(u, 'rectangle'):
                s_, e_ = find(r, 'start')[0], find(r, 'end')[0]
                pts += [(float(s_[1]), float(s_[2])), (float(e_[1]), float(e_[2]))]
            for pl in find(u, 'polyline') + find(u, 'bezier'):
                for xy in find(find(pl, 'pts')[0], 'xy'):
                    pts.append((float(xy[1]), float(xy[2])))
            for c in find(u, 'circle'):
                cx, cy = float(find(c, 'center')[0][1]), float(find(c, 'center')[0][2]); rr = float(find(c, 'radius')[0][1])
                pts += [(cx - rr, cy - rr), (cx + rr, cy + rr)]
            for a in find(u, 'arc'):
                for k in ('start', 'mid', 'end'):
                    e = find(a, k)
                    if e: pts.append((float(e[0][1]), float(e[0][2])))
        self.units = sorted({p[0] for p in self.pins if p[0] > 0}) or [1]
        self.power = bool(find(sexpr, 'power'))
    def unit_pins(self, unit):
        return [p for p in self.pins if p[0] in (0, unit)]
    def unit_pts(self, unit):
        return self.gfx.get(0, []) + self.gfx.get(unit, [])

_defs = {}
CUSTOM = {}
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

def font(): return ['effects', ['font', ['size', '1.27', '1.27']]]
def fonth(): return ['effects', ['font', ['size', '1.27', '1.27']], ['hide', 'yes']]

def make_symbol(sym, ref, value, units, footprint='', datasheet='', descr='', fields=None, power=False, width=None):
    """units: list of dict(left=[...], right=[...], top=[...], bottom=[...]).
    entries: None (gap) or (num,name,type) or list of such (stacked at one position, extra ones hidden)."""
    out = ['symbol', ('S', sym), ['pin_names', ['offset', '1.016']], ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes']]
    out.append(['property', ('S', 'Reference'), ('S', ref), ['at', '0', '2.54', '0'], font()])
    out.append(['property', ('S', 'Value'), ('S', value), ['at', '0', '0', '0'], font()])
    out.append(['property', ('S', 'Footprint'), ('S', footprint), ['at', '0', '0', '0'], fonth()])
    out.append(['property', ('S', 'Datasheet'), ('S', datasheet), ['at', '0', '0', '0'], fonth()])
    out.append(['property', ('S', 'Description'), ('S', descr), ['at', '0', '0', '0'], fonth()])
    for k, v in (fields or {}).items():
        out.append(['property', ('S', k), ('S', v), ['at', '0', '0', '0'], fonth()])
    def norm(e): return [e] if isinstance(e, tuple) else e
    def maxlen(lst):
        return max([len(norm(e)[0][1]) for e in lst if e is not None] or [0])
    for ui, u in enumerate(units, 1):
        L, R, T_, B = u.get('left', []), u.get('right', []), u.get('top', []), u.get('bottom', [])
        n = max(len(L), len(R), 1)
        half = math.ceil(((maxlen(L) + maxlen(R)) * 1.05 + 4) / 2 / G) * G
        half = max(half, math.ceil((max(len(T_), len(B)) + 1) * G / 2 / G) * G)
        if width: half = max(half, width / 2)
        vt = math.ceil(max(maxlen(T_), maxlen(B)) * 1.05 / G) * G if (T_ or B) else 0
        top = math.ceil((n - 1) / 2) * G + (vt + G if T_ else 0)
        bot = top - (n - 1) * G - (vt + G if T_ else 0) - (vt + G if B else 0)
        ytop, ybot = top + G, bot - G
        if T_: ytop = math.ceil((n - 1) / 2) * G + G + vt + G
        body = ['symbol', ('S', f'{sym}_{ui}_1'),
                ['rectangle', ['start', f'{-half:g}', f'{ytop:g}'], ['end', f'{half:g}', f'{ybot:g}'],
                 ['stroke', ['width', '0.254'], ['type', 'default']], ['fill', ['type', 'background']]]]
        y0 = math.ceil((n - 1) / 2) * G
        def addpin(e, x, y, ang):
            for k, (num, nm, typ) in enumerate(norm(e)):
                pin = ['pin', typ, 'line', ['at', f'{x:g}', f'{y:g}', ang], ['length', '2.54']]
                if k > 0:
                    pin[1] = 'passive' if typ == 'power_in' else typ
                    pin.append(['hide', 'yes'])
                pin += [['name', ('S', nm), font()], ['number', ('S', str(num)), font()]]
                body.append(pin)
        for side, lst in (('L', L), ('R', R)):
            for i, e in enumerate(lst):
                if e is None: continue
                addpin(e, -half - G if side == 'L' else half + G, y0 - i * G, '0' if side == 'L' else '180')
        for side, lst in (('T', T_), ('B', B)):
            k = len(lst)
            for i, e in enumerate(lst):
                if e is None: continue
                x = (i - (k - 1) / 2) * G
                x = round(x / G) * G if k % 2 == 1 else (i - k / 2) * G + G / 2 * 0 + (G if False else 0) + 0
                x = (i - (k // 2)) * G
                addpin(e, x, ytop + G if side == 'T' else ybot - G, '270' if side == 'T' else '90')
        out.append(body)
    out.append(['embedded_fonts', 'no'])
    CUSTOM[sym] = out
    return out

# ---------------- placed items ----------------
SIDE = {'R': (1, 0), 'L': (-1, 0), 'U': (0, -1), 'D': (0, 1)}  # schematic coords (y down)

class Part:
    kind = 'sym'
    def __init__(self, sheet, d, nets, unit, rot_):
        self.sheet = sheet; self.d = d; self.unit = unit; self.rot = rot_
        self.X = self.Y = None
        self.fstyle = None
        self.mirror = False
        groups = {}
        for (u, num, nm, typ, x, y, ang, hid, ln) in d.unit_pins(unit):
            groups.setdefault((x, y, ang), []).append((num, nm, typ, hid))
        self.groups = []
        used = set()
        for (x, y, ang), pins in groups.items():
            nset = {nets[p[0]] for p in pins if p[0] in nets}
            for p in pins:
                if p[0] in nets: used.add(p[0])
            if len(nset) != 1:
                raise Exception(f'{lib_id_of(d)}: pins {[p[0] + "/" + p[1] for p in pins]} nets={nset}')
            self.groups.append(dict(x=x, y=y, ang=ang, net=nset.pop(), pins=pins))
        extra = set(nets) - used
        if extra:
            raise Exception(f'{d.lib_id}: unknown pins in map {extra}')
    # geometry
    def tr(self, x, y):
        rx, ry = rot(x, y, self.rot)
        if self.mirror: rx = -rx
        return (self.X + rx, self.Y - ry)
    def tips(self):
        out = []
        for g in self.groups:
            tx, ty = self.tr(g['x'], g['y'])
            ox, oy = DIRV[(g['ang'] + 180 + self.rot) % 360]
            if self.mirror: ox = -ox
            out.append(dict(net=g['net'], x=snap(tx), y=snap(ty), o=(ox, -oy), g=g))
        return out
    def tip(self, key):
        for t in self.tips():
            if key in [p[0] for p in t['g']['pins']] or key == t['net']:
                return t
        raise KeyError(f'{self.ref}: {key}')
    def bbox(self):
        pts = [self.tr(x, y) for x, y in self.d.unit_pts(self.unit)] or [(self.X, self.Y)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))
    def size(self):
        b = self.bbox(); return b[2] - b[0], b[3] - b[1]

def lib_id_of(d): return d.lib_id

class Port:   # hierarchical / local / global label anchored at a point
    kind = 'port'
    def __init__(self, net, x, y, o, ltype='hier', shape='bidirectional'):
        self.net, self.x, self.y, self.o, self.ltype, self.shape = net, snap(x), snap(y), o, ltype, shape

class Note:
    kind = 'note'
    def __init__(self, text, x, y, size=1.27):
        self.text, self.x, self.y, self.size = text, x, y, size

# ---------------- sheet ----------------
PAPERS = {'A4': (297, 210), 'A3': (420, 297), 'A2': (594, 420), 'A1': (841, 594), 'A0': (1189, 841)}

class Sheet:
    def __init__(self, fname, title, page, refbase, paper='A2'):
        self.fname, self.title, self.page = fname, title, page
        self.refbase = refbase
        self.items = []
        self.counters = {}
        self.uuid = U('sheet:' + fname)
        self.paper = paper
        self.notes = []
        self.ports = []
        self.clusters = []      # (net, [parts]) rail clusters / explicit
        self.labelnets = set()  # nets forced to label style on this sheet
        self.pinstyle = {}      # (part id, pin num) -> 'label'|'pwr'
        self.byref = {}
        self.buses = []
    def stub(self, it, pin, n=2, d='D'):
        self.pinstyle[(id(it), pin)] = (n, d)
    def cluster(self, net, parts, at=None):
        """wire all pins of `net` on `parts` together; one power symbol at `at`=(x,y,dir) (or on the first pin)."""
        self.clusters.append((net, list(parts), at))
    def bus(self, net, pts):
        self.buses.append((net, [(snap(x), snap(y)) for x, y in pts]))
    def ref(self, prefix):
        n = self.counters.get(prefix, 0) + 1; self.counters[prefix] = n
        return f'{prefix}{self.refbase + n}'
    def note(self, text, x=None, y=None, size=1.27):
        n = Note(text, x, y, size); self.notes.append(n); return n
    def part(self, lib_id, nets, value=None, ref=None, prefix=None, unit=1, rot_=0, footprint=None,
             fields=None, dnp=False, in_bom=True, **kw):
        d = symdef(lib_id)
        it = Part(self, d, nets, unit, rot_)
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
        self.items.append(it)
        self.byref[ref + ('' if unit == 1 else f'.{unit}')] = it
        return it
    def nets(self):
        s = set()
        for it in self.items:
            for g in it.groups:
                if g['net'] != 'NC': s.add(g['net'])
        return s

# ---------------- placement helpers ----------------
def place(it, x, y, r=None):
    if r is not None: it.rot = r
    it.X, it.Y = snap(x), snap(y)
    return it

def place_pin(it, key, x, y, side=None):
    """Place so that pin `key` (number or net) has its tip at (x,y) pointing to `side` (R/L/U/D)."""
    if side is not None:
        for r in (0, 90, 180, 270):
            it.rot = r; it.X = it.Y = 0
            if it.tip(key)['o'] == SIDE[side]: break
        else:
            raise Exception(f'{it.ref}: cannot orient {key} to {side}')
    it.X = it.Y = 0
    t = it.tip(key)
    it.X, it.Y = snap(x - t['x']), snap(y - t['y'])
    return it

def tipxy(it, key):
    t = it.tip(key); return t['x'], t['y']

# ---------------- router ----------------
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
BIT = {(1, 0): 1, (-1, 0): 2, (0, 1): 4, (0, -1): 8}
H_ = 3; V_ = 12

class Router:
    def __init__(self, W, H):
        self.nx, self.ny = gi(W), gi(H)
        self.block = set()
        self.term = {}        # cell -> net
        self.tdir = {}        # cell -> outward dir of pin terminals
        self.reserve = {}     # cell -> net (exit cell of a terminal)
        self.sides = {}       # cell -> {net: mask}
        self.junc = set()
        self.cap = 120000
    def add_box(self, x0, y0, x1, y1):
        for i in range(math.ceil(x0 / GR - 1e-6), math.floor(x1 / GR + 1e-6) + 1):
            for j in range(math.ceil(y0 / GR - 1e-6), math.floor(y1 / GR + 1e-6) + 1):
                self.block.add((i, j))
    def foreign(self, c, net):
        s = self.sides.get(c)
        if not s: return 0
        m = 0
        for n, v in s.items():
            if n != net: m |= v
        return m
    def own(self, c, net):
        s = self.sides.get(c); return s.get(net, 0) if s else 0
    def route(self, net, tree, start, sdir, window=None):
        """A* from terminal `start` (cell) leaving in sdir, to any cell in tree (dict cell->True)."""
        tx = [c[0] for c in tree]; ty = [c[1] for c in tree]
        bx0, bx1, by0, by1 = min(tx), max(tx), min(ty), max(ty)
        def h(c):
            dx = bx0 - c[0] if c[0] < bx0 else (c[0] - bx1 if c[0] > bx1 else 0)
            dy = by0 - c[1] if c[1] < by0 else (c[1] - by1 if c[1] > by1 else 0)
            return dx + dy
        if window:
            wx0, wy0, wx1, wy1 = window
        else:
            wx0, wy0, wx1, wy1 = 1, 1, self.nx - 1, self.ny - 1
        best = {}
        cnt = 0
        heap = [(h(start), 0.0, cnt, start, sdir, None)]
        parent = {}
        BEND, CROSS = 3.0, 4.0
        while heap:
            f, g, _, c, d, par = heapq.heappop(heap)
            key = (c, d)
            if key in parent: continue
            parent[key] = par
            # goal test (c reached with incoming direction d)
            if c != start and c in tree:
                path = [c]; k = key
                while parent[k] is not None:
                    k = parent[k]; path.append(k[0])
                return path[::-1]
            fm = self.foreign(c, net)
            for nd in DIRS:
                if c == start and nd != sdir: continue
                if nd == (-d[0], -d[1]): continue
                if c != start and nd != d and (fm or (c in self.term and c not in tree)): continue   # no bend on a crossing / pass-through pin
                n = (c[0] + nd[0], c[1] + nd[1])
                if not (wx0 <= n[0] <= wx1 and wy0 <= n[1] <= wy1): continue
                ng = g + 1.0 + (BEND if (nd != d and c != start) else 0)
                inb = BIT[(-nd[0], -nd[1])]
                if n in tree:
                    om = self.own(n, net)
                    if om & inb: continue
                    ng += 1.0
                    heapq.heappush(heap, (ng + 0, ng, cnt + 1, n, nd, key)); cnt += 1
                    continue
                if n in self.block: continue
                tn = self.term.get(n)
                if tn is not None:
                    od = self.tdir.get(n)
                    if not (tn == net and od is not None and od[0] * nd[0] + od[1] * nd[1] == 0 and not self.own(n, net)):
                        continue
                    ng += 0.5
                rn = self.reserve.get(n)
                if rn is not None and rn != net: continue
                if self.own(n, net): continue
                fmn = self.foreign(n, net)
                if fmn:
                    want = H_ if nd[0] else V_
                    other = V_ if nd[0] else H_
                    if fmn != other: continue   # must be a straight perpendicular pass-through
                    ng += CROSS
                # spacing: discourage running adjacent & parallel to foreign wires
                for pd in ((nd[1], nd[0]), (-nd[1], -nd[0])):
                    a = (n[0] + pd[0], n[1] + pd[1])
                    fa = self.foreign(a, net)
                    if fa & (H_ if nd[0] else V_): ng += 0.6
                    if a in self.term and self.term[a] != net: ng += 0.4
                heapq.heappush(heap, (ng + h(n), ng, cnt + 1, n, nd, key)); cnt += 1
            if cnt > self.cap: break
        return None
    def commit(self, net, path):
        for a, b in zip(path, path[1:]):
            d = (b[0] - a[0], b[1] - a[1])
            sa = self.sides.setdefault(a, {}); sa[net] = sa.get(net, 0) | BIT[d]
            sb = self.sides.setdefault(b, {}); sb[net] = sb.get(net, 0) | BIT[(-d[0], -d[1])]

# ---------------- design / writer ----------------
class Design:
    def __init__(self, title):
        self.title = title
        self.sheets = []
        self.root_uuid = U('root')
        self.pwr_n = 0
        self.report = []
    def add(self, sheet):
        self.sheets.append(sheet); return sheet
    def classify(self, rails):
        cnt = {}
        for s in self.sheets:
            for n in s.nets():
                cnt.setdefault(n, set()).add(s.fname)
        self.rails = set(rails)
        self.inter = {n for n, ss in cnt.items() if len(ss) > 1 and n not in self.rails and n != 'GND'}
        self.net_sheets = cnt

    def title_block(self, s, title=None):
        return ['title_block', ['title', ('S', title or s.title)], ['date', ('S', '2026-10-10')], ['rev', ('S', '0.3')],
                ['company', ('S', 'Jorge Mendoza - WWAN carrier (spin 1 bench prototype)')],
                ['comment', '1', ('S', 'Generated schematic (auto-routed); rails = power symbols; inter-sheet = hier. labels')],
                ['comment', '2', ('S', 'Datasheet-verified pinouts noted per sheet; items marked VERIFY are not yet confirmed')]]

    # ---- per-sheet build: obstacles, terminals, routing ----
    def build(self, s, is_root=False):
        W, H = PAPERS[s.paper]
        R = Router(W, H)
        s.R = R
        s.body = []       # extra sexpr elements (power symbols, labels, nc)
        s.wires = []
        s.boxes = []      # (x0,y0,x1,y1,tag) for lint
        libs = s.libs = {}
        # title block region + border
        R.add_box(W - 190, H - 45, W, H)
        R.add_box(0, 0, W, 8); R.add_box(0, 0, 8, H); R.add_box(W - 8, 0, W, H); R.add_box(0, H - 8, W, H)
        def box(x0, y0, x1, y1, tag, route_block=True):
            s.boxes.append((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), tag))
            if route_block: R.add_box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        terms = {}     # net -> list of terminal dicts
        for it in s.items:
            if it.X is None:
                raise Exception(f'{s.fname}: {it.ref} not placed')
            libs[it.d.lib_id] = it.d.sexpr
            b = it.bbox()
            box(b[0] - 0.3, b[1] - 0.3, b[2] + 0.3, b[3] + 0.3, it.ref)
            self.fields(s, it, box)
            for t in it.tips():
                t['part'] = it
                c = (gi(t['x']), gi(t['y']))
                t['c'] = c
                R.block.discard(c)
                if len(it.groups) <= 4:
                    for pn_ in ((t['o'][1], t['o'][0]), (-t['o'][1], -t['o'][0])):
                        for k_ in range(1, 6):
                            R.block.discard((c[0] + pn_[0] * k_, c[1] + pn_[1] * k_))
                if t['net'] == 'NC':
                    R.term[c] = '__NC__' + it.ref
                    continue
                R.term[c] = t['net']
                R.tdir[c] = t['o']
                terms.setdefault(t['net'], []).append(t)
        s.terms = terms
        # ports (explicit)
        for p in s.ports:
            c = (gi(p.x), gi(p.y))
            terms.setdefault(p.net, []).append(dict(net=p.net, x=p.x, y=p.y, o=p.o, c=c, port=p))
        # notes
        for n in s.notes:
            lines = n.text.split('\n')
            w = max(len(l) for l in lines) * CW * n.size / 1.27 + 2
            h = len(lines) * 2.1 * n.size / 1.27 + 1
            box(n.x - 1, n.y - 1, n.x + w, n.y + h, 'note')
        return terms

    def fields(self, s, it, box):
        if it.d.power:
            it.fpos = None
            if it.d.lib_id.endswith('PWR_FLAG'):
                b = it.bbox(); box(b[0] - 0.3, b[1] - 0.3, b[2] + 0.3, b[3] + 0.3, 'flg')
                box(it.X - 5, it.Y - 4.6, it.X + 5, it.Y - 3.0, 'txt:#flag')
            return
        b = it.bbox()
        cx = (b[0] + b[2]) / 2
        w, h = b[2] - b[0], b[3] - b[1]
        st = it.fstyle
        if st is None:
            small = len(it.groups) <= 3 and max(w, h) < 13
            st = ('right' if h > w else 'tb') if small else 'big'
        rw, vw = tw(it.ref), tw(it.value)
        if st == 'tb':
            pos = [(cx, b[1] - 1.6), (cx, b[3] + 1.6)]
        elif st == 'above':
            tot = rw + vw + 1
            pos = [(cx - tot / 2 + rw / 2, b[1] - 1.6), (cx + tot / 2 - vw / 2, b[1] - 1.6)]
        elif st == 'above2':
            pos = [(cx, b[1] - 3.4), (cx, b[1] - 1.6)]
        elif st == 'inside':
            cy = (b[1] + b[3]) / 2
            dy = getattr(it, 'fdy', 0)
            pos = [(cx, cy + dy - 1.0), (cx, cy + dy + 1.0)]
        elif st in ('belowleft', 'belowright', 'aboveleft', 'aboveright'):
            wmax = max(rw, vw)
            xc = cx - 1.5 - wmax / 2 if st.endswith('left') else cx + 1.5 + wmax / 2
            if st.startswith('below'):
                pos = [(xc, b[3] + 1.6), (xc, b[3] + 3.4)]
            else:
                pos = [(xc, b[1] - 3.4), (xc, b[1] - 1.6)]
        elif st == 'below2':
            pos = [(cx, b[3] + 1.6), (cx, b[3] + 3.4)]
        elif st == 'below':
            tot = rw + vw + 1
            pos = [(cx - tot / 2 + rw / 2, b[3] + 1.6), (cx + tot / 2 - vw / 2, b[3] + 1.6)]
        elif st == 'right':
            cy = (b[1] + b[3]) / 2
            pos = [(b[2] + 0.8 + rw / 2, cy - 1.27), (b[2] + 0.8 + vw / 2, cy + 1.27)]
        elif st == 'left':
            cy = (b[1] + b[3]) / 2
            pos = [(b[0] - 0.8 - rw / 2, cy - 1.27), (b[0] - 0.8 - vw / 2, cy + 1.27)]
        else:  # big IC: ref above left part, value below
            pos = [(b[0] + rw / 2, b[1] - 1.6), (b[0] + vw / 2, b[3] + 1.6)]
        it.fpos = pos
        for (x, y), t in zip(pos, (it.ref, it.value)):
            box(x - tw(t) / 2, y - 0.75, x + tw(t) / 2, y + 0.75, 'txt:' + it.ref)

    def pwr_symbol(self, s, net, x, y, o):
        """Place GND / rail power symbol at (x,y) pointing outward o."""
        if net == 'GND':
            d = symdef('power:GND'); r = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[o]
        else:
            d = symdef('power:+3V3'); r = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}[o]
        s.libs[d.lib_id] = d.sexpr
        self.pwr_n += 1
        ref = f'#PWR0{self.pwr_n:04d}'
        fang = 0 if r in (0, 180) else r
        if net == 'GND':
            vx, vy, hide = x, y, True
            ext = 2.6
        else:
            ext = 2.4
            tl = tw(net)
            if o[1] != 0: vx, vy = x, y + o[1] * 3.6
            else: vx, vy = x + o[0] * (ext + 0.6 + tl / 2), y
            hide = False
        e = ['symbol', ['lib_id', ('S', d.lib_id)], ['at', f'{x:g}', f'{y:g}', str(r)], ['unit', '1'],
             ['exclude_from_sim', 'no'], ['in_bom', 'no'], ['on_board', 'yes'], ['dnp', 'no'], ['uuid', ('S', U('pwr:' + s.fname))],
             ['property', ('S', 'Reference'), ('S', ref), ['at', f'{x:g}', f'{y:g}', '0'], fonth()],
             ['property', ('S', 'Value'), ('S', net), ['at', f'{snap(vx):g}', f'{snap(vy):g}', str(fang)],
              fonth() if hide else font()],
             ['property', ('S', 'Footprint'), ('S', ''), ['at', f'{x:g}', f'{y:g}', '0'], fonth()],
             ['property', ('S', 'Datasheet'), ('S', ''), ['at', f'{x:g}', f'{y:g}', '0'], fonth()],
             ['property', ('S', 'Description'), ('S', ''), ['at', f'{x:g}', f'{y:g}', '0'], fonth()],
             ['pin', ('S', '1'), ['uuid', ('S', U('ppin:' + s.fname))]],
             ['instances', ['project', ('S', PROJECT), ['path', ('S', self.inst_path(s)), ['reference', ('S', ref)], ['unit', '1']]]]]
        s.body.append(e)
        # obstacle
        px, py = -o[1], o[0]
        x1, y1 = x + o[0] * ext, y + o[1] * ext
        bx = (min(x, x1) - 1.1 * abs(px) - 0.1, min(y, y1) - 1.1 * abs(py) - 0.1, max(x, x1) + 1.1 * abs(px) + 0.1, max(y, y1) + 1.1 * abs(py) + 0.1)
        s.boxes.append(bx + ('pwr:' + net,))
        s.R.add_box(*bx)
        s.R.block.discard((gi(x), gi(y)))
        s.R.term.setdefault((gi(x), gi(y)), net)
        if not hide:
            tl = tw(net)
            if o[1] != 0: tb = (vx - tl / 2, vy - 0.75, vx + tl / 2, vy + 0.75)
            else: tb = (vx - tl / 2, vy - 0.75, vx + tl / 2, vy + 0.75)
            s.boxes.append(tb + ('ptxt:' + net,)); s.R.add_box(*tb)

    def inst_path(self, s):
        return f'/{self.root_uuid}/{s.uuid}' if s.fname != 'ROOT' else f'/{self.root_uuid}'

    def label(self, s, net, x, y, o, ltype):
        ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[o]
        just = 'left' if ang in (0, 90) else 'right'
        if ltype == 'hier':
            e = ['hierarchical_label', ('S', net), ['shape', 'bidirectional'], ['at', f'{x:g}', f'{y:g}', str(ang)],
                 ['effects', ['font', ['size', '1.27', '1.27']], ['justify', just]], ['uuid', ('S', U('hl:' + s.fname))]]
            L = tw(net) + 2.6
        elif ltype == 'global':
            e = ['global_label', ('S', net), ['shape', 'passive'], ['at', f'{x:g}', f'{y:g}', str(ang)],
                 ['fields_autoplaced', 'yes'], ['effects', ['font', ['size', '1.27', '1.27']], ['justify', just]],
                 ['uuid', ('S', U('gl:' + s.fname))],
                 ['property', ('S', 'Intersheetrefs'), ('S', '${INTERSHEET_REFS}'), ['at', f'{x:g}', f'{y:g}', '0'],
                  ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left'], ['hide', 'yes']]]]
            L = tw(net) + 3
        else:
            e = ['label', ('S', net), ['at', f'{x:g}', f'{y:g}', str(ang)], ['fields_autoplaced', 'yes'],
                 ['effects', ['font', ['size', '1.27', '1.27']], ['justify', just, 'bottom']], ['uuid', ('S', U('l:' + s.fname))]]
            L = tw(net) + 0.5
        s.body.append(e)
        if o[1] == 0:
            bx = (min(x, x + o[0] * L), y - (1.6 if ltype == 'local' else 1.1), max(x, x + o[0] * L), y + (0.2 if ltype == 'local' else 1.1))
        else:
            bx = (x - (1.6 if ltype == 'local' else 1.1), min(y, y + o[1] * L), x + (0.2 if ltype == 'local' else 1.1), max(y, y + o[1] * L))
        # keep the anchor cell itself out of the block box
        ax, ay = x + o[0] * 0.7, y + o[1] * 0.7
        bx2 = (min(bx[0], bx[2]) if o[0] <= 0 else ax, bx[1] if o[1] <= 0 else ay, bx[2] if o[0] >= 0 else ax, bx[3] if o[1] >= 0 else ay)
        if o[0] < 0: bx2 = (bx[0], bx[1], x - 0.7, bx[3])
        if o[1] < 0: bx2 = (bx[0], bx[1], bx[2], y - 0.7)
        s.boxes.append(bx2 + ('lbl:' + net,)); s.R.add_box(*bx2)

    def route_sheet(self, s, terms):
        R = s.R
        stub = 2.54
        jobs = []
        nlabel = 0
        def pinkey(t): return (id(t.get('part')), t['g']['pins'][0][0]) if 'part' in t else None
        for net, ts in sorted(terms.items()):
            if net == 'NC': continue
            pts = [t for t in ts if not t.get('port')]
            ports = [t for t in ts if t.get('port')]
            rail = (net == 'GND') or (net in self.rails)
            if rail:
                # clusters
                done = set()
                for cnet, parts, at in s.clusters:
                    if cnet != net: continue
                    cl = [t for t in pts if t['part'] in parts and id(t) not in done]
                    for t in cl: done.add(id(t))
                    if not cl: continue
                    if at is None:
                        a = cl[0]
                        self.pwr_symbol(s, net, a['x'], a['y'], a['o'])
                        if len(cl) > 1: jobs.append((net, cl))
                    else:
                        x, y, d = at
                        dv = SIDE[d]
                        c = (gi(x), gi(y))
                        R.block.discard(c)
                        self.pwr_symbol(s, net, snap(x), snap(y), dv)
                        R.term[c] = net
                        jobs.append((net, [dict(net=net, x=snap(x), y=snap(y), o=(-dv[0], -dv[1]), c=c, port=None)] + cl))
                for t in pts:
                    if id(t) in done: continue
                    ps = s.pinstyle.get(pinkey(t))
                    if ps:
                        n_, od = ps   # stub cells, symbol direction
                        cells = [(t['c'][0] + t['o'][0] * k, t['c'][1] + t['o'][1] * k) for k in range(n_ + 1)]
                        R.commit(net, cells)
                        self.pwr_symbol(s, net, cells[-1][0] * GR, cells[-1][1] * GR, SIDE[od])
                        continue
                    self.pwr_symbol(s, net, t['x'], t['y'], t['o'])
                continue
            label_mode = net in s.labelnets
            ltype = 'hier' if net in self.inter else 'local'
            if s.fname == 'ROOT': ltype = 'local'
            if label_mode:
                for t in pts:
                    x2, y2 = t['x'] + t['o'][0] * stub, t['y'] + t['o'][1] * stub
                    s.wires.append(((t['x'], t['y']), (x2, y2)))
                    k_ = max(1, int(round(stub / GR)))
                    R.commit(net, [(t['c'][0] + j * t['o'][0], t['c'][1] + j * t['o'][1]) for j in range(k_ + 1)])
                    self.label(s, net, x2, y2, t['o'], ltype if net in self.inter else 'local')
                continue
            tl = list(pts) + ports
            if net in self.inter and not ports and s.fname != 'ROOT':
                # default port at the first pin's stub end
                a = pts[0]
                x2, y2 = a['x'] + a['o'][0] * stub * (getattr(s, 'portstub', {}).get(net, 1)), a['y'] + a['o'][1] * stub * (getattr(s, 'portstub', {}).get(net, 1))
                p = Port(net, x2, y2, a['o'])
                s.ports.append(p)
                tl.append(dict(net=net, x=p.x, y=p.y, o=(-a['o'][0], -a['o'][1]), c=(gi(p.x), gi(p.y)), port=p, lo=a['o']))
            for t in tl:
                if t.get('port'):
                    p = t['port']
                    lo = t.get('lo', (-p.o[0], -p.o[1]) if 'lo' not in t else t['lo'])
                    if 'lo' not in t:
                        # explicit port: p.o = direction wires arrive from (label text extends opposite)
                        lo = p.o
                        t['o'] = (-p.o[0], -p.o[1])
                    self.label(s, net, p.x, p.y, lo, p.ltype if p.ltype != 'hier' or net in self.inter else 'local')
                    R.term[t['c']] = net
            if len(tl) > 1:
                jobs.append((net, tl))
        # pre-drawn buses
        busc = {}
        for net, pts_ in s.buses:
            cells = []
            for (x0, y0), (x1, y1) in zip(pts_, pts_[1:]):
                a, b = (gi(x0), gi(y0)), (gi(x1), gi(y1))
                n_ = max(abs(b[0] - a[0]), abs(b[1] - a[1]))
                dx = (b[0] > a[0]) - (b[0] < a[0]); dy = (b[1] > a[1]) - (b[1] < a[1])
                seg = [(a[0] + dx * k, a[1] + dy * k) for k in range(n_ + 1)]
                if cells and seg[0] == cells[-1]: seg = seg[1:]
                cells += seg
            for i_, c in enumerate(cells):
                fm_ = R.foreign(c, net)
                if fm_ and 0 < i_ < len(cells) - 1:
                    pa, nb_ = cells[i_ - 1], cells[i_ + 1]
                    straight_h = pa[1] == c[1] == nb_[1]; straight_v = pa[0] == c[0] == nb_[0]
                    if (straight_h and fm_ == V_) or (straight_v and fm_ == H_):
                        fm_ = 0
                if c in R.block or (c in R.term and R.term[c] != net) or fm_:
                    bb = [b_ for b_ in s.boxes if b_[0] - 0.7 <= c[0] * GR <= b_[2] + 0.7 and b_[1] - 0.7 <= c[1] * GR <= b_[3] + 0.7]
                    raise Exception(f'{s.fname}: bus {net} blocked at {c[0]*GR:.2f},{c[1]*GR:.2f} by {bb} term={R.term.get(c)}')
            R.commit(net, cells)
            busc.setdefault(net, []).extend(cells)
        # reserve exit cells
        for net, tl in jobs:
            for t in tl:
                ex = (t['c'][0] + t['o'][0], t['c'][1] + t['o'][1])
                if ex not in R.reserve: R.reserve[ex] = net
        # order: small spans first
        def span(job):
            xs = [t['c'][0] for t in job[1]]; ys = [t['c'][1] for t in job[1]]
            return (max(xs) - min(xs)) + (max(ys) - min(ys))
        jobs.sort(key=lambda j: (getattr(s, 'prio', {}).get(j[0], 0), span(j)))
        fails = []
        seen_bus = set()
        bcomps = {}
        for net_, cells_ in busc.items():
            left_ = set(cells_); comps_ = []
            while left_:
                st_ = [left_.pop()]; comp_ = set(st_)
                while st_:
                    a_ = st_.pop()
                    for d_ in DIRS:
                        b_ = (a_[0] + d_[0], a_[1] + d_[1])
                        if b_ in left_ and (R.own(a_, net_) & BIT[d_]):
                            left_.discard(b_); comp_.add(b_); st_.append(b_)
                comps_.append(comp_)
            bcomps[net_] = comps_
        for net, tl in jobs:
            tree = {tl[0]['c']: True}
            rest = list(tl[1:])
            tcs = {t['c'] for t in tl}
            comps = list(bcomps.get(net, []))
            if sum(1 for n_, _ in jobs if n_ == net) > 1:
                comps = [cp for cp in comps if cp & tcs]
            pending = []
            for cp in comps:
                if tl[0]['c'] in cp:
                    tree.update({c: True for c in cp})
                else:
                    pending.append(cp)
            for cp in pending:
                if not (cp & tcs):
                    # orphan bus piece: connect it from one of its free ends
                    for c in sorted(cp):
                        nb = [d_ for d_ in DIRS if (c[0] + d_[0], c[1] + d_[1]) in cp and (R.own(c, net) & BIT[d_])]
                        if len(nb) == 1:
                            o_ = (-nb[0][0], -nb[0][1])
                            rest.append(dict(net=net, c=c, o=o_, x=c[0] * GR, y=c[1] * GR, port=None, fb=True))
                            break
            first = len(tree) == 1
            while rest:
                rest.sort(key=lambda t: min(abs(t['c'][0] - c[0]) + abs(t['c'][1] - c[1]) for c in tree))
                t = rest.pop(-1 if first else 0)
                first = False
                if t['c'] in tree: continue
                xs = [c[0] for c in tree] + [t['c'][0]]; ys = [c[1] for c in tree] + [t['c'][1]]
                path = None
                for m in (10, 30, None):
                    win = None if m is None else (max(1, min(xs) - m), max(1, min(ys) - m), min(R.nx - 1, max(xs) + m), min(R.ny - 1, max(ys) + m))
                    path = R.route(net, tree, t['c'], t['o'], win)
                    if path: break
                if not path:
                    fails.append((net, t.get('part').ref if t.get('part') else 'port'))
                    # fallback: local label directly on the pin tips (no stub -> cannot short anything)
                    for tt in (t, tl[0]):
                        if tt.get('fb'): continue
                        tt['fb'] = True
                        self.label(s, net, tt['x'], tt['y'], tt['o'], 'local')
                    continue
                R.commit(net, path)
                for c in path: tree[c] = True
                for cp in list(pending):
                    if t['c'] in cp or any(c in cp for c in path):
                        tree.update({c: True for c in cp}); pending.remove(cp)
        s.fails = fails
        self.report.append((s.fname, len(jobs), fails))

    def emit_wires(self, s):
        R = s.R
        out = []
        nets = {}
        for c, d in R.sides.items():
            for n, m in d.items():
                nets.setdefault(n, {})[c] = m
        for n, cells in nets.items():
            # nodes = cells where wire turns / ends / junction / terminal
            def isnode(c):
                m = cells[c]
                if c in R.term: return True
                if m not in (H_, V_): return True
                return False
            for c, m in cells.items():
                k = bin(m).count('1') + (1 if R.term.get(c) == n else 0)
                if k >= 3: R.junc.add((c, n))
            for axis, bit_fw, step in ((0, 1, (1, 0)), (1, 4, (0, 1))):
                seen = set()
                for c in sorted(cells):
                    m = cells[c]
                    if not (m & bit_fw) or c in seen: continue
                    # start only at run starts: previous cell doesn't continue into c, or c is node
                    prev = (c[0] - step[0], c[1] - step[1])
                    if prev in cells and (cells[prev] & bit_fw) and not isnode(c): continue
                    a = c; b = c
                    while True:
                        nb = (b[0] + step[0], b[1] + step[1])
                        b = nb
                        if isnode(b) or not (cells.get(b, 0) & bit_fw): break
                        seen.add(b)
                    out.append((a, b, n))
        for a, b, n in out:
            s.body.append(['wire', ['pts', ['xy', f'{a[0] * GR:g}', f'{a[1] * GR:g}'], ['xy', f'{b[0] * GR:g}', f'{b[1] * GR:g}']],
                           ['stroke', ['width', '0'], ['type', 'default']], ['uuid', ('S', U('w:' + s.fname))]])
        for c, n in R.junc:
            s.body.append(['junction', ['at', f'{c[0] * GR:g}', f'{c[1] * GR:g}'], ['diameter', '0'], ['color', '0', '0', '0', '0'],
                           ['uuid', ('S', U('j:' + s.fname))]])
        s.nwires = len(out)
        s.segs = out

    def sym_instance(self, s, it):
        X, Y, r = it.X, it.Y, it.rot
        e = ['symbol', ['lib_id', ('S', it.d.lib_id)], ['at', f'{X:g}', f'{Y:g}', str(r)]] + ([['mirror', 'y']] if it.mirror else []) + [['unit', str(it.unit)],
             ['exclude_from_sim', 'no'], ['in_bom', 'yes' if it.in_bom else 'no'], ['on_board', 'yes'],
             ['dnp', 'yes' if it.dnp else 'no'], ['uuid', ('S', U('sym:' + s.fname + it.ref + str(it.unit)))]]
        fang = r if r in (90, 270) else 0
        def prop(k, v, x, y, hide=False):
            eff = ['effects', ['font', ['size', '1.27', '1.27']]]
            if hide: eff.append(['hide', 'yes'])
            return ['property', ('S', k), ('S', v), ['at', f'{x:g}', f'{y:g}', str(fang)], eff]
        if it.d.power:
            e.append(prop('Reference', it.ref, X, Y, hide=True))
            e.append(prop('Value', it.value, X, Y - 3.81 if it.d.lib_id.endswith('PWR_FLAG') else Y, hide=not it.d.lib_id.endswith('PWR_FLAG')))
        else:
            (rx, ry), (vx, vy) = it.fpos
            e.append(prop('Reference', it.ref, round(rx, 3), round(ry, 3)))
            e.append(prop('Value', it.value, round(vx, 3), round(vy, 3)))
        e.append(prop('Footprint', it.footprint, X, Y, hide=True))
        e.append(prop('Datasheet', it.datasheet or '', X, Y, hide=True))
        e.append(prop('Description', it.descr or '', X, Y, hide=True))
        for k, v in (it.fields or {}).items():
            e.append(prop(k, v, X, Y, hide=True))
        for p in it.d.unit_pins(it.unit):
            e.append(['pin', ('S', p[1]), ['uuid', ('S', U('pin:' + s.fname + it.ref + p[1]))]])
        e.append(['instances', ['project', ('S', PROJECT), ['path', ('S', self.inst_path(s)), ['reference', ('S', it.ref)], ['unit', str(it.unit)]]]])
        return e

    def write_sheet(self, s, outdir, extra_hdr=None):
        body = []
        for it in s.items:
            body.append(self.sym_instance(s, it))
            for t in it.tips():
                if t['net'] == 'NC':
                    body.append(['no_connect', ['at', f'{t["x"]:g}', f'{t["y"]:g}'], ['uuid', ('S', U('nc:' + s.fname))]])
        for n in s.notes:
            body.append(['text', ('S', n.text), ['exclude_from_sim', 'no'], ['at', f'{n.x:g}', f'{n.y:g}', '0'],
                         ['effects', ['font', ['size', f'{n.size:g}', f'{n.size:g}']], ['justify', 'left', 'top']], ['uuid', ('S', U('txt:' + s.fname))]])
        body += s.body
        hdr = ['kicad_sch', ['version', '20250114'], ['generator', ('S', 'eeschema')], ['generator_version', ('S', '9.0')],
               ['uuid', ('S', s.uuid if s.fname != 'ROOT' else self.root_uuid)], ['paper', ('S', s.paper)], self.title_block(s)] + \
              [['lib_symbols'] + list(s.libs.values())]
        doc = hdr + (extra_hdr or []) + body
        return doc

    # lint: overlapping text/boxes and wires through text
    def lint(self, s):
        probs = []
        bx = [b for b in s.boxes]
        texty = [b for b in bx if b[4].startswith(('txt:', 'ptxt:', 'lbl:', 'note'))]
        allb = bx
        for i, a in enumerate(texty):
            for b in allb:
                if b is a: continue
                if a[4] == 'txt:' + b[4]: continue
                if b[4].startswith('txt:') and a[4] == b[4]: continue
                if a[0] < b[2] - 0.05 and b[0] < a[2] - 0.05 and a[1] < b[3] - 0.05 and b[1] < a[3] - 0.05:
                    key = tuple(sorted((a[4], b[4])))
                    probs.append(key)
        syms = [b for b in bx if not b[4].startswith(('txt:', 'ptxt:', 'lbl:', 'note', 'pwr:'))]
        for i, a in enumerate(syms):
            for b in syms[i + 1:]:
                if a[0] < b[2] - 0.05 and b[0] < a[2] - 0.05 and a[1] < b[3] - 0.05 and b[1] < a[3] - 0.05:
                    probs.append((a[4], b[4]))
        W, H = PAPERS[s.paper]
        for b in bx:
            if b[0] < 8 or b[1] < 8 or b[2] > W - 8 or b[3] > H - 8 or (b[2] > W - 190 and b[3] > H - 45):
                probs.append(('OFFPAGE/TITLE', b[4]))
        return sorted(set(probs))

# ---------------- root sheet (wired block diagram) ----------------
class SheetBlock:
    def __init__(self, s, x, y, w):
        self.s, self.x, self.y, self.w = s, x, y, w

def natkey(n):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', n)]

def build_root(D, layout, paper, notes, order_hint=None, pitch=2.54):
    """layout: fname -> (x, y, w). Pins on sheet edges facing partner sheets; wires auto-routed."""
    root = Sheet('ROOT', D.title, 1, 0, paper)
    root.items = []
    blocks = {s.fname: SheetBlock(s, *layout[s.fname]) for s in D.sheets}
    # pin sides
    pins = {f: {'L': [], 'R': []} for f in blocks}
    for net in sorted(D.inter, key=natkey):
        fs = sorted(D.net_sheets[net])
        for f in fs:
            b = blocks[f]
            others = [blocks[o] for o in fs if o != f]
            cx = sum(o.x + o.w / 2 for o in others) / len(others)
            side = 'R' if cx > b.x + b.w / 2 else 'L'
            if order_hint and (f, net) in order_hint.get('side', {}): side = order_hint['side'][(f, net)]
            cy = sum(o.y for o in others) / len(others)
            pins[f][side].append((cy, natkey(net), net))
    body = []
    R = Router(*PAPERS[paper])
    root.R = R; root.body = []; root.boxes = []; root.libs = {}; root.ports = []; root.clusters = []; root.labelnets = set(); root.pinstyle = {}
    terms = {}
    pinpos = {}
    sheets_sx = []
    W, H = PAPERS[paper]
    R.add_box(W - 190, H - 45, W, H)
    R.add_box(0, 0, W, 8); R.add_box(0, 0, 8, H); R.add_box(W - 8, 0, W, H); R.add_box(0, H - 8, W, H)
    for f, b in blocks.items():
        s = b.s
        L = sorted(pins[f]['L']); Rr = sorted(pins[f]['R'])
        if order_hint and f in order_hint.get('seq', {}):
            sq = order_hint['seq'][f]
            L = [None if n_ is None else (0, 0, n_) for n_ in sq.get('L', [])]
            Rr = [None if n_ is None else (0, 0, n_) for n_ in sq.get('R', [])]
            want = sorted(n_ for side_ in pins[f].values() for (_, _, n_) in side_)
            got = sorted(e_[2] for e_ in L + Rr if e_)
            assert want == got, (f, set(want) ^ set(got))
        elif order_hint and f in order_hint.get('order', {}):
            key = order_hint['order'][f]
            L.sort(key=lambda e: key(e[2])); Rr.sort(key=lambda e: key(e[2]))
        n = max(len(L), len(Rr), 2)
        h = snap((n + 1) * pitch + 2.54)
        b.h = h
        x0, y0 = snap(b.x), snap(b.y)
        spins = []
        for side, lst in (('L', L), ('R', Rr)):
            for i, ent in enumerate(lst):
                if ent is None: continue
                net = ent[2]
                py = y0 + 2.54 + (i + 1) * pitch if True else 0
                py = snap(py)
                px = x0 if side == 'L' else snap(x0 + b.w)
                o = (-1, 0) if side == 'L' else (1, 0)
                spins.append(['pin', ('S', net), 'bidirectional', ['at', f'{px:g}', f'{py:g}', '180' if side == 'L' else '0'],
                              ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left' if side == 'L' else 'right']],
                              ['uuid', ('S', U('sp:' + f + net))]])
                c = (gi(px), gi(py))
                terms.setdefault(net, []).append(dict(net=net, x=px, y=py, o=o, c=c, port=None, sheetpin=True))
                pinpos[(f, net)] = (px, py)
        R.add_box(x0 - 0.3, y0 - 0.3, x0 + b.w + 0.3, y0 + h + 0.3)
        root.boxes.append((x0, y0, x0 + b.w, y0 + h, 'sheet:' + f))
        # title text above / file text below
        R.add_box(x0, y0 - 2.6, x0 + tw(s.title) + 1, y0 - 0.2)
        R.add_box(x0, y0 + h + 0.2, x0 + tw(s.fname) + 1, y0 + h + 2.6)
        root.boxes.append((x0, y0 - 2.6, x0 + tw(s.title), y0 - 0.2, 'stitle:' + f))
        body.append(['sheet', ['at', f'{x0:g}', f'{y0:g}'], ['size', f'{snap(b.w):g}', f'{h:g}'], ['exclude_from_sim', 'no'],
                     ['in_bom', 'yes'], ['on_board', 'yes'], ['dnp', 'no'], ['fields_autoplaced', 'yes'],
                     ['stroke', ['width', '0.1524'], ['type', 'solid']], ['fill', ['color', '255', '255', '225', '1.0000']],
                     ['uuid', ('S', s.uuid)],
                     ['property', ('S', 'Sheetname'), ('S', s.title), ['at', f'{x0:g}', f'{y0 - 0.7112:g}', '0'],
                      ['effects', ['font', ['size', '1.27', '1.27'], ['bold', 'yes']], ['justify', 'left', 'bottom']]],
                     ['property', ('S', 'Sheetfile'), ('S', s.fname), ['at', f'{x0:g}', f'{y0 + h + 0.5:g}', '0'],
                      ['effects', ['font', ['size', '1.27', '1.27']], ['justify', 'left', 'top']]]] + spins +
                    [['instances', ['project', ('S', PROJECT), ['path', ('S', f'/{D.root_uuid}'), ['page', ('S', str(s.page))]]]]])
    for t in [t for ts in terms.values() for t in ts]:
        R.block.discard(t['c']); R.term[t['c']] = t['net']
    for n in notes:
        lines = n.text.split('\n')
        w = max(len(l) for l in lines) * CW * n.size / 1.27 + 2
        hh = len(lines) * 2.1 * n.size / 1.27 + 1
        R.add_box(n.x - 1, n.y - 1, n.x + w, n.y + hh)
        root.boxes.append((n.x - 1, n.y - 1, n.x + w, n.y + hh, 'note'))
        body.append(['text', ('S', n.text), ['exclude_from_sim', 'no'], ['at', f'{n.x:g}', f'{n.y:g}', '0'],
                     ['effects', ['font', ['size', f'{n.size:g}', f'{n.size:g}']], ['justify', 'left', 'top']], ['uuid', ('S', U('roottxt'))]])
    root.prio = {}
    if order_hint and 'wires' in order_hint:
        order_hint['wires'](root, pinpos)
    root.pinpos = pinpos
    D.route_sheet(root, terms)
    D.emit_wires(root)
    doc = ['kicad_sch', ['version', '20250114'], ['generator', ('S', 'eeschema')], ['generator_version', ('S', '9.0')],
           ['uuid', ('S', D.root_uuid)], ['paper', ('S', paper)], D.title_block(root, D.title), ['lib_symbols']] + body + root.body + \
          [['sheet_instances', ['path', ('S', '/'), ['page', ('S', '1')]]], ['embedded_fonts', 'no']]
    root.blocks = blocks
    return root, doc
