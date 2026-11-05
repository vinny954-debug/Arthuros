#!/usr/bin/env python3
"""Captions and titles of the windows Kodi drives by id (audit.sh runs it).

Kodi labels only some of a window's controls itself; the rest show whatever
caption the skin gives them. Several windows used to be columns of blank
buttons, a numeric keypad showed Kodi menu names (a bare-number <label> is
a string id), and title bars were left empty or showed the window's file
name. This fails on any of that, in xml/ and xml768/:

1. a visible pressable control in one of WINDOWS with no <label>, unless
   Kodi labels that id itself (genwindows.KODI_LABELLED);
2. a <label>/<label2>/<altlabel> that is a bare number, in any window;
3. id 799 (Estuary's touch Back button, which no Kodi window drives);
4. a Kodi list that must be seen parked off screen (MUST_SHOW);
5. a mover/resize without both textures (they draw nothing else);
6. a Dialog_Box with no title, no Dialog_Heading and no label on the title
   bar, or a title that is just the window's file name.
Exits non-zero on failure.
"""
import glob, os, re, sys
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import genwindows as gw

SKIN = os.environ.get("SKINDIR") or os.path.join(HERE, "skin.arthuros")
PRESSY = gw.PRESSY
WINDOWS = ["DialogPVRChannelManager", "DialogPVRGroupManager", "DialogPVRGuideSearch",
           "SmartPlaylistEditor", "SmartPlaylistRule", "MyMusicPlaylistEditor", "LoginScreen",
           "DialogColorPicker", "DialogVideoManager", "EventLog", "SettingsProfile",
           "DialogNumeric", "DialogKeyboard", "DialogSlider", "DialogMediaSource",
           "SettingsScreenCalibration"]
MUST_SHOW = {"MyMusicPlaylistEditor": {50, 100}, "DialogPVRGroupManager": {11, 12, 13},
             "DialogPVRGuideSearch": set(range(9, 32)),
             "LoginScreen": {52}, "DialogVideoManager": {50}}
CHROME = set(range(9100, 9200)) | set(range(9900, 10000))   # task bar / title-bar boxes

errors = []

def offscreen(c):
    l = c.findtext("left")
    return l is not None and l.strip().startswith("-")

def in_layout(c):
    return any(a.tag in ("itemlayout", "focusedlayout", "content") for a in c.iterancestors())

for res in ("xml", "xml768"):
    for path in sorted(glob.glob(os.path.join(SKIN, res, "*.xml"))):
        name = os.path.splitext(os.path.basename(path))[0]
        txt = open(path, encoding="utf-8").read()
        root = etree.fromstring(txt.encode("utf-8"))
        where = f"{res}/{name}"
        for tag in ("label", "label2", "altlabel"):
            for el in root.iter(tag):
                if (el.text or "").strip().isdigit():
                    errors.append(f"{where}: <{tag}>{el.text.strip()}</{tag}> is read as string id "
                                  f"{el.text.strip()} - use $LOCALIZE[...] or $NUMBER[...]")
        if root.tag != "window":
            continue
        ctrls = [c for c in root.iter("control") if c.get("id")]
        if any(c.get("id") == "799" for c in ctrls):
            errors.append(f"{where}: id 799 (Estuary's TouchBackButton) is drawn but nothing drives it")
        for c in root.iter("control"):
            if c.get("type") in ("mover", "resize") and not offscreen(c):
                if c.find("texturefocus") is None or c.find("texturenofocus") is None:
                    errors.append(f"{where}: {c.get('type')} {c.get('id')} has no textures (invisible)")
        if name in WINDOWS:
            kodi = gw.KODI_LABELLED.get(name, set())
            for c in ctrls:
                cid = int(c.get("id"))
                if c.get("type") not in PRESSY or offscreen(c) or in_layout(c) or cid in CHROME:
                    continue
                if cid in kodi:
                    continue
                if not (c.findtext("label") or "").strip():
                    errors.append(f"{where}: {c.get('type')} {cid} has no caption and Kodi does not label it")
        for cid in sorted(MUST_SHOW.get(name, ())):
            found = [c for c in ctrls if c.get("id") == str(cid)]
            if not found:
                errors.append(f"{where}: Kodi control {cid} is missing")
            elif all(offscreen(c) for c in found):
                errors.append(f"{where}: Kodi control {cid} is parked off screen")
        # titles (xml/ only: xml768 has the includes expanded)
        if res == "xml" and 'content="Dialog_Box"' in txt:
            m = re.search(r'<param name="title" value="([^"]*)"', txt)
            title = m.group(1) if m else ""
            on_bar = re.search(r"<left>29</left><top>3</top>", txt)
            if not title and 'content="Dialog_Heading"' not in txt and not on_bar:
                errors.append(f"{where}: dialog title bar is left blank (no title, no Dialog_Heading, "
                              "no label Kodi writes on the title bar)")
        if res == "xml":
            for m in re.finditer(r'<param name="(?:title|label)" value="([^"]*)"', txt):
                if m.group(1) == name:
                    errors.append(f"{where}: title bar shows the file name '{name}'")

if errors:
    print("labelcheck: FAILED")
    for e in errors:
        print("  " + e)
    sys.exit(1)
print(f"labelcheck: captions, titles and Kodi ids fine in {len(WINDOWS)} windows (xml, xml768)")
