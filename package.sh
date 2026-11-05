#!/bin/sh
# Build, then zip the skin as skin.arthuros-<version>.zip in dist/.
set -e
cd "$(dirname "$0")"
./build.sh
VER=$(sed -n 's/^[[:space:]]*version="\([0-9.]*\)".*/\1/p' skin.arthuros/addon.xml | head -1)
mkdir -p dist
find skin.arthuros -name __pycache__ -prune -exec rm -rf {} +
rm -f "dist/skin.arthuros-$VER.zip"
zip -qr "dist/skin.arthuros-$VER.zip" skin.arthuros
echo "dist/skin.arthuros-$VER.zip"
