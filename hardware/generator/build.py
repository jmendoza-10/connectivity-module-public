STOCK_LIBS = ['74xGxx', 'Connector', 'Connector_Generic', 'Device', 'Diode', 'Interface', 'Jumper', 'Mechanical', 'Memory_EEPROM', 'Power_Protection', 'Transistor_FET', 'power']
import os, sys, json, importlib, tempfile
import engine
from engine import PAPERS, place, snap, tw, build_root, Note
import circuit
from circuit import D, H, RAILS
import layout

def autoplace(s, x0=20, y0=20):
    W, Hh = PAPERS[s.paper]
    x, y, colw = x0, y0, 0
    for it in s.items:
        if it.X is not None: continue
        place(it, 0, 0)
        b = it.bbox(); w = b[2] - b[0] + 14; hgt = b[3] - b[1] + 8
        if y + hgt > Hh - 50:
            x += colw + 6; y = y0; colw = 0
        place(it, x - b[0] + 3, y - b[1] + 3)
        y += hgt; colw = max(colw, w)

def main(out, only=None):
    D.classify(RAILS)
    layout.place_all(D, H, only)
    for s in D.sheets:
        if any(it.X is None for it in s.items):
            autoplace(s, 330 if s.fname in (only or []) else 20, 20)
        for n in s.notes:
            if n.x is None: n.x, n.y = 15, PAPERS[s.paper][1] - 80
    docs = {}
    sheets = [s for s in D.sheets if not only or s.fname in only]
    for s in sheets:
        terms = D.build(s)
        D.route_sheet(s, terms)
        D.emit_wires(s)
        docs[s.fname] = D.write_sheet(s, out)
    if only and 'ROOT' not in only:
        os.makedirs(out, exist_ok=True)
        for s in sheets:
            open(f'{out}/{s.fname}', 'w').write(engine.dump(docs[s.fname] + [['embedded_fonts', 'no']]) + '\n')
            lint = D.lint(s)
            print(f'{s.fname:24s} wires={s.nwires} fails={len(s.fails)} lint={len(lint)}')
            for f in s.fails: print('   FAIL', f)
            if os.environ.get('V'):
                for l in lint: print('   LINT', l)
        return
    root, rdoc = build_root(D, layout.ROOT_LAYOUT, layout.ROOT_PAPER, layout.root_notes(), layout.ROOT_HINT)
    os.makedirs(out, exist_ok=True)
    if only:
        open(f'{out}/{engine.PROJECT}.kicad_sch', 'w').write(engine.dump(rdoc) + '\n')
        lint = D.lint(root)
        print(f'ROOT wires={getattr(root, "nwires", 0)} fails={len(root.fails)} lint={len(lint)}')
        for f in root.fails: print('   FAIL', f)
        for l in lint: print('   LINT', l)
        return
    for s in D.sheets:
        open(f'{out}/{s.fname}', 'w').write(engine.dump(docs[s.fname] + [['embedded_fonts', 'no']]) + '\n')
    open(f'{out}/{engine.PROJECT}.kicad_sch', 'w').write(engine.dump(rdoc) + '\n')
    lib = ['kicad_symbol_lib', ['version', '20241209'], ['generator', ('S', 'kicad_symbol_editor')], ['generator_version', ('S', '9.0')]] + \
          [engine.CUSTOM[k] for k in engine.CUSTOM]
    open(f'{out}/wwan_carrier.kicad_sym', 'w').write(engine.dump(lib) + '\n')
    # Project-level table: custom lib + every stock KiCad lib the design uses, so ERC passes on a
    # clean machine (CI, teammates) without relying on a global sym-lib-table.
    stock = sorted({u.lib_id.split(':')[0] for s in D.sheets + [root] for u in getattr(s, 'symbols', [])
                    if hasattr(u, 'lib_id')} - {'wwan_carrier'}) or STOCK_LIBS
    rows = ['  (lib (name "wwan_carrier")(type "KiCad")(uri "${KIPRJMOD}/wwan_carrier.kicad_sym")(options "")(descr "WWAN carrier custom symbols"))']
    rows += [f'  (lib (name "{l}")(type "KiCad")(uri "${{KICAD9_SYMBOL_DIR}}/{l}.kicad_sym")(options "")(descr "KiCad stock library"))' for l in stock]
    open(f'{out}/sym-lib-table', 'w').write('(sym_lib_table\n  (version 7)\n' + '\n'.join(rows) + '\n)\n')
    # report
    for s in D.sheets + [root]:
        lint = D.lint(s)
        print(f'{s.fname:24s} paper={s.paper} wires={getattr(s, "nwires", 0):4d} fails={len(s.fails)} lint={len(lint)}')
        if os.environ.get('V'):
            for f in s.fails: print('   FAIL', f)
            for l in lint: print('   LINT', l)
    json.dump({s.fname: {'fails': s.fails, 'lint': D.lint(s)} for s in D.sheets + [root]}, open(os.path.join(tempfile.gettempdir(), 'lint.json'), 'w'), indent=1)

if __name__ == '__main__':
    main(sys.argv[1], os.environ.get('ONLY', '').split(',') if os.environ.get('ONLY') else None)
