#!/usr/bin/env bash
# Copies the newest ArthurOS skin zip to the Pi and installs it for the user
# Kodi runs as, then restarts Kodi.
#
# Run it on your computer (where the zip is), in a normal terminal, not inside
# the SSH session:
#   bash install-arthuros.sh                       # pi4b.local, same username as here
#   bash install-arthuros.sh pi@pi4b.local         # a different username
#   bash install-arthuros.sh pi@pi4b.local some/skin.arthuros-0.9.5.zip
set -euo pipefail

HOST=${1:-pi4b.local}
DIR="$(cd "$(dirname "$0")" && pwd)"
# newest zip by version, from dist/ (package.sh) or next to this script
ZIP=${2:-$( { ls -1 "$DIR"/dist/skin.arthuros-*.zip "$DIR"/skin.arthuros-*.zip 2>/dev/null || true; } \
            | awk -F/ '{print $NF "\t" $0}' | sort -V | tail -1 | cut -f2)}
[ -n "$ZIP" ] && [ -f "$ZIP" ] || { echo "No skin.arthuros-*.zip found next to this script."; exit 1; }
echo "== Installing $(basename "$ZIP") on $HOST"

# one SSH connection for all three steps, so the password is asked only once
SSHO=(-o ControlMaster=auto -o "ControlPath=/tmp/arthuros-ssh-%r@%h:%p" -o ControlPersist=60)

REMOTE=$(mktemp)
trap 'rm -f "$REMOTE"' EXIT
cat > "$REMOTE" <<'PI'
set -euo pipefail
ZIP=/tmp/skin.arthuros.zip

# Who runs Kodi? Its skins live in that user's ~/.kodi/addons.
KUSER=$(ps -eo user=,comm= | awk '$2 ~ /^kodi/ {print $1; exit}')
SVC=$(systemctl list-units --type=service --all --no-legend --plain 2>/dev/null \
      | awk '{print $1}' | grep -i '^kodi' | head -1 || true)
if [ -z "$KUSER" ] && [ -n "$SVC" ]; then
  KUSER=$(systemctl show -p User --value "$SVC" 2>/dev/null || true)
fi
ME=$(id -un)
KUSER=${KUSER:-$ME}
KHOME=$(getent passwd "$KUSER" | cut -d: -f6)
ADDONS="$KHOME/.kodi/addons"
echo "== Kodi runs as '$KUSER'; the skin goes in $ADDONS"
[ -n "$SVC" ] && echo "== Kodi service: $SVC"

as_kodi() { if [ "$KUSER" = "$ME" ]; then "$@"; else sudo -u "$KUSER" "$@"; fi; }
ver() { sed -n 's/^[[:space:]]*version="\([0-9.]*\)".*/\1/p' "$1" | head -1; }

# unpack and sanity-check before touching anything
TMP=$(mktemp -d)
if command -v unzip >/dev/null; then unzip -q "$ZIP" -d "$TMP"
else python3 -m zipfile -e "$ZIP" "$TMP"; fi
[ -f "$TMP/skin.arthuros/addon.xml" ] || { echo "That zip isn't the ArthurOS skin."; exit 1; }
[ -d "$TMP/skin.arthuros/xml768" ] && echo "== Includes the 4:3 (1024x768) layout"
chmod -R a+rX "$TMP"
NEW=$(ver "$TMP/skin.arthuros/addon.xml")

# stop Kodi so it isn't reading the skin while it's replaced
WAS_ACTIVE=no
if [ -n "$SVC" ] && systemctl is-active --quiet "$SVC"; then
  echo "== Stopping $SVC"
  sudo systemctl stop "$SVC"; WAS_ACTIVE=yes
elif ps -eo comm= | grep -q '^kodi'; then
  read -rp "Kodi is running but not as a service I can find. Quit Kodi, then press Enter... " _
fi

as_kodi mkdir -p "$ADDONS"
if [ -d "$ADDONS/skin.arthuros" ]; then
  OLD=$(ver "$ADDONS/skin.arthuros/addon.xml")
  BK="$KHOME/arthuros-backup-${OLD:-old}"
  echo "== Moving v${OLD:-?} to $BK (outside addons, so Kodi ignores it)"
  as_kodi rm -rf "$BK"
  as_kodi mv "$ADDONS/skin.arthuros" "$BK"
fi
echo "== Installing v$NEW"
as_kodi cp -r "$TMP/skin.arthuros" "$ADDONS/"
rm -rf "$TMP" "$ZIP" /tmp/arthuros-install.sh

if [ "$WAS_ACTIVE" = yes ]; then
  echo "== Starting $SVC"
  sudo systemctl start "$SVC"
fi
echo
echo "Done: ArthurOS v$NEW is installed."
echo "If it isn't your skin yet: Settings > Interface > Skin > Skin > ArthurOS."
echo "On the 2048x1536 screen Kodi uses the 4:3 layout by itself; set"
echo "Settings > Interface > Skin > Zoom to 0% and turn on Skin settings > Touch mode."
PI

scp -q "${SSHO[@]}" "$ZIP" "$HOST:/tmp/skin.arthuros.zip"
scp -q "${SSHO[@]}" "$REMOTE" "$HOST:/tmp/arthuros-install.sh"
ssh -t "${SSHO[@]}" "$HOST" 'bash /tmp/arthuros-install.sh'
