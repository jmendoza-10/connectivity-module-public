#!/bin/bash
# crop.sh file.kicad_sch out.png x0 y0 x1 y1 (mm) [dpi]
kicad-cli sch export pdf -o /tmp/cr.pdf $1 >/dev/null 2>&1
D=${7:-150}
pdftoppm -f 1 -l 1 -r $D -png -singlefile /tmp/cr.pdf /tmp/cr_full
python3 -c "
from PIL import Image; im=Image.open('/tmp/cr_full.png'); k=$D/25.4
im.crop((int($3*k),int($4*k),int($5*k),int($6*k))).save('$2')"
