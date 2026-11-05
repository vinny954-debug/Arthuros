#!/usr/bin/env python3
"""Control ids/types each Kodi window needs, with the reference skin's
includes expanded so nothing hides inside them."""
import os, glob, json
import xml.etree.ElementTree as ET

# needs a checkout of Kodi's Estuary skin: ESTUARY=/path/to/xbmc/addons/skin.estuary/xml
EST = os.environ.get("ESTUARY") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "kodi", "skin.estuary", "xml")
INC = {}
for p in glob.glob(os.path.join(EST, "*.xml")):
    try: root = ET.parse(p).getroot()
    except ET.ParseError: continue
    if root.tag != "includes": continue
    for i in root.findall("include"):
        if i.get("name"): INC[i.get("name")] = i

def walk(el, out, depth=0, seen=None, params=None):
    """Includes are expanded WITH their parameters: Estuary passes many
    control ids in as $PARAM[id], and skipping those hid whole button rows."""
    if depth > 12: return
    seen = seen or set()
    params = params or {}
    def sub(t):
        for k, v in params.items():
            t = t.replace(f"$PARAM[{k}]", v)
        return t
    for ch in list(el):
        if ch.tag == "include":
            name = ch.get("content") or (ch.text.strip() if ch.text else None)
            if name and name in INC and name not in seen:
                inc = INC[name]
                p = {d.get("name"): sub(d.get("default", "")) for d in inc.findall("param")}
                for u in ch.findall("param"):
                    p[u.get("name")] = sub(u.get("value", u.text or ""))
                body = inc.find("definition")
                walk(body if body is not None else inc, out, depth+1, seen | {name}, p)
            continue
        if ch.tag == "control":
            cid, ct = ch.get("id"), ch.get("type")
            if cid and ct:
                try:
                    n = int(sub(cid))
                    if n < 1000: out.setdefault(n, ct)
                except ValueError: pass
        walk(ch, out, depth+1, seen, params)

inv = {}
for p in sorted(glob.glob(os.path.join(EST, "*.xml"))):
    base = os.path.basename(p)[:-4]
    try: root = ET.parse(p).getroot()
    except ET.ParseError: continue
    if root.tag != "window": continue
    found = {}
    walk(root, found)
    inv[base] = {"ids": dict(sorted(found.items())),
                 "views": (root.findtext("views") or "").strip(),
                 "default": (root.findtext("defaultcontrol") or "").strip()}
json.dump(inv, open("inventory.json","w"), indent=1)
print(len(inv), "windows")
for k in ["DialogConfirm","DialogSelect","DialogContextMenu","DialogBusy","DialogVolumeBar",
          "DialogMediaSource","DialogAddonSettings","DialogSubtitles","FileManager","Settings",
          "DialogAddonInfo","DialogMusicInfo","SettingsSystemInfo","LoginScreen","MyPlaylist"]:
    if k in inv: print(f"{k:24s} {inv[k]['ids']}")
