#!/bin/bash
# render single sheet file: rs.sh file.kicad_sch outpng [dpi]
kicad-cli sch export pdf -o /tmp/rs.pdf $1 >/dev/null 2>&1
pdftoppm -f 1 -l 1 -r ${3:-60} -png -singlefile /tmp/rs.pdf ${2%.png}
