# ArthurOS: back up and restore the skin's settings.
#
# Run from Skin settings:
#   RunScript(special://skin/scripts/backup.py,backup)
#   RunScript(special://skin/scripts/backup.py,restore)
#
# A backup is one small XML file holding every skin setting (the desktop
# tiles, grid size, pointer, bars, clock) plus Kodi's look-and-feel choices
# for this skin (colours, fonts, zoom).
#
# Restoring goes through Kodi's own Skin.SetString / Skin.SetBool /
# Skin.Reset, one setting at a time, rather than overwriting settings.xml:
# Kodi holds skin settings in memory and writes them back when the skin
# unloads, so a file copied in underneath it would simply be overwritten.
import json
import sys
import time
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui
import xbmcvfs

SKIN = xbmc.getSkinDir()
SETTINGS = "special://profile/addon_data/%s/settings.xml" % SKIN
BACKUPS = "special://profile/addon_data/%s/backups/" % SKIN
KODI_SETTINGS = ("lookandfeel.skincolors", "lookandfeel.font",
                 "lookandfeel.skintheme", "lookandfeel.skinzoom")
# working values the skin sets while you use it; never backed up or restored
TRANSIENT = ("edit.slot", "pick.addon", "home.flip", "swap.", "arthur.min")


def L(sid):
    return xbmc.getLocalizedString(sid)


def transient(name):
    return any(name == t or (t.endswith(".") and name.startswith(t)) for t in TRANSIENT)


def read_xml(path):
    f = xbmcvfs.File(path)
    try:
        data = bytes(f.readBytes())
    finally:
        f.close()
    return ET.fromstring(data) if data else None


def current_settings():
    """{name: (type, value)} as Kodi last saved them."""
    root = read_xml(SETTINGS)
    out = {}
    if root is None:
        return out
    for s in root.findall("setting"):
        name = s.get("id")
        if name and not transient(name):
            out[name] = (s.get("type", "string"), s.text or "")
    return out


def rpc(method, **params):
    req = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    return json.loads(xbmc.executeJSONRPC(json.dumps(req))).get("result")


def backup():
    # Kodi saves skin settings half a second after the last change
    xbmc.sleep(1000)
    xbmcvfs.mkdirs(BACKUPS)
    folder = xbmcgui.Dialog().browse(3, L(31981), "files", "", False, False, BACKUPS)
    if not folder:
        return
    root = ET.Element("arthuros_backup", version="1", skin=SKIN,
                      created=time.strftime("%Y-%m-%d %H:%M"))
    for sid in KODI_SETTINGS:
        res = rpc("Settings.GetSettingValue", setting=sid)
        if res is not None and "value" in res:
            ET.SubElement(root, "kodi", id=sid).text = json.dumps(res["value"])
    for name, (kind, value) in sorted(current_settings().items()):
        ET.SubElement(root, "setting", id=name, type=kind).text = value
    name = time.strftime("arthuros-settings-%Y-%m-%d-%H%M.xml")
    path = folder.rstrip("/\\") + "/" + name
    f = xbmcvfs.File(path, "w")
    try:
        ok = f.write(bytearray(ET.tostring(root, encoding="utf-8")))
    finally:
        f.close()
    if not ok:
        xbmcgui.Dialog().ok(L(31979), L(31989))
        return
    xbmcgui.Dialog().notification(L(31983), name, xbmcgui.NOTIFICATION_INFO, 4000)


def esc(v):
    return '"%s"' % v.replace("\\", "\\\\").replace('"', '\\"')


def restore():
    xbmcvfs.mkdirs(BACKUPS)
    path = xbmcgui.Dialog().browse(1, L(31982), "files", ".xml", False, False, BACKUPS)
    if not path:
        return
    try:
        root = read_xml(path)
    except ET.ParseError:
        root = None
    if root is None or root.tag != "arthuros_backup":
        xbmcgui.Dialog().ok(L(31980), L(31985))
        return
    if not xbmcgui.Dialog().yesno(L(31980), L(31988)):
        return

    want = {}
    for s in root.findall("setting"):
        name = s.get("id")
        if name and not transient(name):
            want[name] = (s.get("type", "string"), s.text or "")
    have = current_settings()

    # only touch what differs: Kodi writes its settings file on every change
    cmds = []
    for name, (kind, value) in sorted(want.items()):
        if have.get(name) == (kind, value):
            continue
        if kind == "bool":
            cmds.append("Skin.SetBool(%s,%s)" % (name, "true" if value == "true" else "false"))
        elif value:
            cmds.append("Skin.SetString(%s,%s)" % (name, esc(value)))
        else:
            cmds.append("Skin.Reset(%s)" % name)
    for name in sorted(set(have) - set(want)):
        cmds.append("Skin.Reset(%s)" % name)
    cmds.append("Skin.ToggleSetting(home.flip)")   # makes the desktop reload its tiles

    progress = xbmcgui.DialogProgress()
    progress.create(L(31986))
    for i, cmd in enumerate(cmds):
        xbmc.executebuiltin(cmd, True)
        progress.update(int(100 * (i + 1) / len(cmds)))
    progress.close()

    # colours and fonts last: changing them reloads the skin
    for k in root.findall("kodi"):
        try:
            value = json.loads(k.text or "null")
        except ValueError:
            continue
        res = rpc("Settings.GetSettingValue", setting=k.get("id"))
        if res is not None and res.get("value") != value:
            rpc("Settings.SetSettingValue", setting=k.get("id"), value=value)

    xbmcgui.Dialog().notification(L(31984), "", xbmcgui.NOTIFICATION_INFO, 4000)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "backup":
        backup()
    elif mode == "restore":
        restore()
