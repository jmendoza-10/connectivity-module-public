#!/usr/bin/env bash
# Regenerate the KiCad schematic from hardware/generator, then refresh every derived artefact
# (netlist, ERC report, PDF, BOM, generated docs). Run from the repo root.
#   Requires: KiCad 9 (kicad-cli + stock symbol libs in /usr/share/kicad/symbols), python3.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=$(mktemp -d)
cd "$ROOT/hardware/generator"
# fixed hash seed: the generator iterates sets/dicts of strings, so output is only reproducible with a fixed seed
PYTHONHASHSEED=0 python3 build.py "$OUT" > "$OUT/build.log"
grep -E "paper=" "$OUT/build.log"
if grep -q "FAIL" "$OUT/build.log"; then echo "router fallbacks present (see $OUT/build.log)"; fi
cp "$OUT"/*.kicad_sch "$OUT"/wwan_carrier.kicad_sym "$OUT"/sym-lib-table "$ROOT/hardware/kicad/"
cd "$ROOT/hardware/kicad"
kicad-cli sch export netlist -o wwan-carrier.net wwan-carrier.kicad_sch >/dev/null
# make the netlist path-independent so diffs stay clean
sed -i -E 's|\(source "[^"]*/([^/"]+)"\)|(source "\1")|; s|\(date "[^"]*"\)|(date "")|' wwan-carrier.net
sed -i -E 's|\(uri "/[^"]*/(wwan_carrier.kicad_sym)"\)|(uri "${KIPRJMOD}/\1")|' wwan-carrier.net
kicad-cli sch erc --severity-all -o ../wwan-carrier-erc.rpt wwan-carrier.kicad_sch | tail -1
sed -i -E "s|from /[^ ]*/(wwan-carrier.kicad_sch)|from \1|" ../wwan-carrier-erc.rpt
sed -i -E "1s/\(20[0-9T:-]+, /(/" ../wwan-carrier-erc.rpt   # drop timestamp for clean diffs
grep "ERC messages" ../wwan-carrier-erc.rpt
kicad-cli sch export pdf -o ../wwan-carrier-schematic-rev0.3.pdf wwan-carrier.kicad_sch >/dev/null
kicad-cli sch export bom -o ../wwan-carrier-bom.csv \
  --fields 'Reference,Value,Footprint,MPN,${QUANTITY},${DNP},Notes,FP_TODO,FP_VERIFY' \
  --labels 'Refs,Value,Footprint,MPN / maker,Qty,DNP,Notes,Footprint TODO,Footprint VERIFY' \
  --group-by 'Value,Footprint,MPN,${DNP}' --ref-range-delimiter '' wwan-carrier.kicad_sch >/dev/null
# connectivity vs the frozen rev 0.2 netlist: rev 0.3 is intentionally DIFFERENT (generic M.2 pin names, pin 20 FET,
# pin 22/20 DNP options, pin 73 -> GND, 3042 standoff, renamed pin-22/28 nets). Review the OLD/NEW lines on every regen.
python3 "$ROOT/hardware/generator/cmpnet.py" "$ROOT/hardware/generator/rev0.2_reference.net" wwan-carrier.net | grep -E "^(components|nets|named|RESULT)"
python3 "$ROOT/hardware/generator/netcheck.py" wwan-carrier.net
cd "$ROOT"
python3 tools/gen_interface.py
echo "done - review 'git diff' and commit"
