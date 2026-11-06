#!/usr/bin/env bash
# Copies the newest ArthurOS skin zip to the Pi and installs it for the user
# Kodi runs as, then restarts Kodi.
#
# Run it on your computer (where the zip is), in a normal terminal, not inside
# the SSH session:
#   bash install-arthuros.sh                       # pi4b.local, same username as here
#   bash install-arthuros.sh pi@pi4b.local         # a different username
#   bash install-arthuros.sh root@192.168.68.63    # LibreELEC (root, no sudo)
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

# LibreELEC logs in as root and has no sudo; Raspberry Pi OS needs it.
SUDO=sudo; [ "$(id -u)" -eq 0 ] && SUDO=

# Who runs Kodi? Its skins live in that user's ~/.kodi/addons.
KUSER=$(ps -eo user=,comm= 2>/dev/null | awk '$2 ~ /^kodi/ {print $1; exit}' || true)
# exact names first: LibreELEC also has kodi-autostart.service and friends
SVC=
for u in kodi.service kodi-gbm.service kodi-standalone.service; do
  systemctl cat "$u" >/dev/null 2>&1 && { SVC=$u; break; }
done
if [ -z "$SVC" ]; then
  SVC=$(systemctl list-units --type=service --all --no-legend --plain 2>/dev/null \
        | awk '{print $1}' | grep -iE '^kodi(-gbm|-standalone)?(@[^.]*)?\.service$' | head -1 || true)
fi
if [ -z "$KUSER" ] && [ -n "$SVC" ]; then
  KUSER=$(systemctl show -p User --value "$SVC" 2>/dev/null || true)
fi
ME=$(id -un)
KUSER=${KUSER:-$ME}
KHOME=$(getent passwd "$KUSER" | cut -d: -f6)
ADDONS="$KHOME/.kodi/addons"
DB="$KHOME/.kodi/userdata/Database"
echo "== Kodi runs as '$KUSER'; the skin goes in $ADDONS"
[ -n "$SVC" ] && echo "== Kodi service: $SVC"

as_kodi() {
  if [ "$KUSER" = "$ME" ]; then "$@"
  elif [ "$(id -u)" -eq 0 ]; then su -s /bin/sh "$KUSER" -c "$(printf '%q ' "$@")"
  else sudo -u "$KUSER" "$@"; fi
}
# Kodi's home can be 0700 (Raspberry Pi OS Bookworm), so every look inside it
# runs as Kodi's user too, never as the SSH user
ver() { as_kodi cat "$1" 2>/dev/null | sed -n 's/^[[:space:]]*version="\([0-9.]*\)".*/\1/p' | head -1 || true; }

# Whatever happens from here on: put the old skin back if the new one isn't in
# place, and start Kodi again if we stopped it (exactly once, success or not).
WAS_ACTIVE=no BK= TMP= STAGE=
restore() {
  rc=$?
  if [ -n "$BK" ] && ! as_kodi test -e "$ADDONS/skin.arthuros" && as_kodi test -d "$BK"; then
    echo "== Something failed: putting the old skin back"
    as_kodi mv "$BK" "$ADDONS/skin.arthuros" || true
  fi
  if [ "$WAS_ACTIVE" = yes ]; then
    echo "== Starting $SVC"
    $SUDO systemctl start "$SVC" || rc=1
  fi
  if [ -n "$STAGE" ]; then as_kodi rm -rf "$STAGE" || true; fi
  if [ -n "$TMP" ]; then rm -rf "$TMP"; fi
  rm -f "$ZIP" /tmp/arthuros-install.sh
  exit $rc
}
trap restore EXIT

# unpack and sanity-check before touching anything
TMP=$(mktemp -d)
if command -v unzip >/dev/null; then unzip -q "$ZIP" -d "$TMP"
else python3 -m zipfile -e "$ZIP" "$TMP"; fi
[ -f "$TMP/skin.arthuros/addon.xml" ] || { echo "That zip isn't the ArthurOS skin."; exit 1; }
[ -d "$TMP/skin.arthuros/xml768" ] && echo "== Includes the 4:3 (1024x768) layout"
chmod -R a+rX "$TMP"
NEW=$(ver "$TMP/skin.arthuros/addon.xml")

# copy it beside addons first (outside it, so Kodi never sees two copies):
# a copy that fails leaves the installed skin alone
as_kodi mkdir -p "$ADDONS"
STAGE="$KHOME/arthuros-new"
as_kodi rm -rf "$STAGE"
as_kodi cp -r "$TMP/skin.arthuros" "$STAGE"

# stop Kodi so it isn't reading the skin while it's replaced
if [ -n "$SVC" ] && systemctl is-active --quiet "$SVC"; then
  echo "== Stopping $SVC"
  $SUDO systemctl stop "$SVC"; WAS_ACTIVE=yes
elif ps -eo comm= 2>/dev/null | grep -q '^kodi'; then
  read -rp "Kodi is running but not as a service I can find. Quit Kodi, then press Enter... " _
fi

FRESH=yes
if as_kodi test -d "$ADDONS/skin.arthuros"; then
  FRESH=no
  OLD=$(ver "$ADDONS/skin.arthuros/addon.xml")
  BK="$KHOME/arthuros-backup-${OLD:-old}"
  echo "== Moving v${OLD:-?} to $BK (outside addons, so Kodi ignores it)"
  as_kodi rm -rf "$BK"
  as_kodi mv "$ADDONS/skin.arthuros" "$BK"
fi
# mv into an existing folder would nest the new skin inside the old one (and
# busybox mv may not know -T), so make sure the name is free first
if as_kodi test -e "$ADDONS/skin.arthuros"; then
  echo "== $ADDONS/skin.arthuros is still there, not installing over it"; exit 1
fi
echo "== Installing v$NEW"
as_kodi mv "$STAGE" "$ADDONS/skin.arthuros"
STAGE=

# Kodi enters an add-on it finds on disk with no database row as *disabled*
# (CAddonDatabase::SyncInstalled), so a copied skin would not be in the skin
# list. Mark it enabled while Kodi is stopped.
ENABLED=no
if as_kodi sh -c 'ls "$1"/Addons[0-9]*.db' _ "$DB" >/dev/null 2>&1; then
  if as_kodi python3 - "$DB" <<'EOF'
import glob, re, sqlite3, sys
dbs = sorted(glob.glob(sys.argv[1] + "/Addons[0-9]*.db"),
             key=lambda p: int(re.search(r"Addons(\d+)\.db$", p).group(1)))
con = sqlite3.connect(dbs[-1])
con.execute("INSERT OR IGNORE INTO installed(addonID, enabled, installDate) "
            "VALUES('skin.arthuros', 1, datetime('now'))")
con.execute("UPDATE installed SET enabled=1, disabledReason=0 WHERE addonID='skin.arthuros'")
con.commit()
print("== Enabled skin.arthuros in " + dbs[-1].rsplit("/", 1)[-1])
EOF
  then ENABLED=yes
  else echo "== Couldn't mark the skin enabled in Kodi's add-on database"; fi
fi

# Screen calibration by touch: Kodi maps a one-finger tap there to
# NextCalibration and sends a long press only as a mouse right-click, which
# the calibration window may never turn into Back. A user keymap (Kodi loads
# every userdata/keymaps/*.xml; a window section beats <global>) makes a long
# press or a two-finger tap plain Back there. Ours alone: rewritten each time.
KEYMAPS="$KHOME/.kodi/userdata/keymaps"
if as_kodi sh -c 'mkdir -p "$1" && cat > "$1/arthuros-touch.xml"' _ "$KEYMAPS" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!-- Written by install-arthuros.sh (ArthurOS skin). Safe to delete. -->
<keymap>
  <ScreenCalibration>
    <touch>
      <longpress>Back</longpress>
      <tap pointers="2">Back</tap>
    </touch>
  </ScreenCalibration>
</keymap>
EOF
then echo "== Touch keymap: $KEYMAPS/arthuros-touch.xml (long press = Back in screen calibration)"
else echo "== Couldn't write the touch keymap (not needed for the skin itself)"; fi

# Skin settings > Network & Bluetooth (netbt.py) changes Wi-Fi through
# NetworkManager. Kodi run as a service has no login session, so polkit refuses
# it unless a rule names the user Kodi runs as. Offer to add one (asked on each
# install until it exists; LibreELEC has its own settings add-on). rules.d is
# 0700 polkitd, so only sudo can see whether the rule is there.
RULE=/etc/polkit-1/rules.d/50-arthuros-nm.rules
if command -v nmcli >/dev/null && [ -d /etc/polkit-1/rules.d ] && [ "$KUSER" != root ] \
   && [ -t 0 ] && ! $SUDO test -e "$RULE"; then
  read -rp "Let '$KUSER' (Kodi) change Wi-Fi from Skin settings? Adds $RULE [y/N] " A || A=
  case "$A" in
    [yY]*)
      printf '%s\n' "// ArthurOS: let Kodi (running as a service, no login session) manage networks" \
        "polkit.addRule(function(action, subject) {" \
        "  if (action.id.indexOf(\"org.freedesktop.NetworkManager.\") == 0 && subject.user == \"$KUSER\")" \
        "    return polkit.Result.YES;" \
        "});" | $SUDO tee "$RULE" >/dev/null && echo "== Added $RULE" ;;
  esac
fi

echo
echo "Done: ArthurOS v$NEW is installed."
if [ "$ENABLED" = no ] && [ "$FRESH" = yes ]; then
  echo "First install: Kodi has to see the skin once. Enable it in"
  echo "Add-ons > My add-ons > Look and feel > Skin > ArthurOS > Enable,"
  echo "then pick it in Settings > Interface > Skin > Skin."
else
  echo "If it isn't your skin yet: Settings > Interface > Skin > Skin > ArthurOS."
fi
echo "On the 2048x1536 screen Kodi uses the 4:3 layout by itself; set"
echo "Settings > Interface > Skin > Zoom to 0% and turn on Skin settings > Touch mode."
PI

scp -q "${SSHO[@]}" "$ZIP" "$HOST:/tmp/skin.arthuros.zip"
scp -q "${SSHO[@]}" "$REMOTE" "$HOST:/tmp/arthuros-install.sh"
ssh -t "${SSHO[@]}" "$HOST" 'bash /tmp/arthuros-install.sh'
