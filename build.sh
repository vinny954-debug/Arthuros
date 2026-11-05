#!/bin/sh
# One entry point. Every step, in order, every time - fixes applied by hand to
# generated files were lost twice before this existed.
# One command per line: under `set -e` POSIX sh ignores a failure anywhere in an
# `a && b` list except its last command, so a pair would not stop the build.
set -e
cd "$(dirname "$0")"
echo "== textures";   python3 mkmedia.py
echo "== fonts";      python3 mkfonts.py
echo "== language";   python3 mklang.py
echo "== windows";    python3 genwindows.py
echo "== desktop";    rm -rf build768
                      python3 home.py
                      ARTHUR_H=768 python3 home.py
echo "== palette";    python3 themepass.py
                      XMLDIR=build768 python3 themepass.py
echo "== sizes";      python3 sizepass.py
                      XMLDIR=build768 python3 sizepass.py
echo "== 4:3 layout"; python3 tallpass.py
echo "== validate";   python3 validate.py
                      RES=xml768 python3 validate.py
echo "== contrast";   python3 palettecheck.py
echo "== icons";      python3 iconcheck.py
echo "== text fit";   python3 textfit.py
                      RES=xml768 python3 textfit.py
echo "== audit";      ./audit.sh
