#!/bin/bash
# usage: render.sh outdir page [dpi]
cd $1 && kicad-cli sch export pdf -o /tmp/r.pdf wwan-carrier.kicad_sch >/dev/null 2>&1
rm -f /tmp/pg-*.png; pdftoppm -f $2 -l $2 -r ${3:-70} -png /tmp/r.pdf /tmp/pg
ls /tmp/pg-*.png
