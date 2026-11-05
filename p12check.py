#!/usr/bin/env python3
"""Regression checks for the 0.9.7 final-verification fixes (audit.sh "P12").

    python3 p12check.py NAME      exit 0 when the check holds, else print why

Each check reads the shipped xml/ and xml768/ folders (and the sources where
that is the point). Kept out of audit.sh's one-liners because most of them
walk the XML.
"""
import glob, os, re, sys
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.join(HERE, "skin.arthuros")
DIRS = ("xml", "xml768")
XLC = "[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]"
OSDS = ("VideoOSD", "MusicOSD", "GameOSD")

def tree(d, name):
    return etree.parse(os.path.join(SKIN, d, name + ".xml")).getroot()

def ctl(root, cid):
    return root.find(f".//control[@id='{cid}']")

def txt(el, tag):
    return (el.findtext(tag) or "").strip() if el is not None else ""

def num(el, tag):
    t = txt(el, tag)
    return int(t) if re.fullmatch(r"-?\d+", t) else None

def includes(el):
    return [(i.get("content") or (i.text or "").strip(), i.get("condition") or "") for i in el.findall("include")]

def has_xl(el, prefix):
    return any(c.startswith(prefix) and XLC in cond for c, cond in includes(el))

def onclicks(el):
    return [(o.text or "").strip() for o in el.findall("onclick")]

def strings():
    po = open(os.path.join(SKIN, "language", "resource.language.en_gb", "strings.po")).read()
    return {int(m.group(1)): m.group(2) for m in re.finditer(r'msgctxt "#(\d+)"\nmsgid "(.*)"', po)}

bad = []
def need(ok, why):
    if not ok:
        bad.append(why)

# ---------------------------------------------------------------- the OSD
def menus():
    """1/30: Menus (9952) in every OSD: close all, then ACTION_SHOW_GUI straight
    to the full-screen window (PreviousWindow; playback keeps running)."""
    win = {"VideoOSD": "FullscreenVideo", "MusicOSD": "Visualisation", "GameOSD": "FullscreenGame"}
    for d in DIRS:
        for o in OSDS:
            b = ctl(tree(d, o), 9952)
            need(b is not None and onclicks(b) == ["Dialog.Close(all,true)", f"Action(FullScreen,{win[o]})"]
                 and txt(b, "label") == "$LOCALIZE[31897]", f"{d}/{o}: Menus 9952")
            need(b is not None and b.find("hitrect") is not None, f"{d}/{o}: Menus hit rect")
    need(strings().get(31897) == "Menus", "string 31897")

def live_pair():
    """3: Previous/Next show together on live TV and radio."""
    for d in DIRS:
        for o, live in (("VideoOSD", "VideoPlayer"), ("MusicOSD", "MusicPlayer")):
            r = tree(d, o)
            term = f"[Player.SeekEnabled + {live}.Content(LiveTV)]"
            for cid in (600, 607):
                v = txt(ctl(r, cid), "visible")
                need(term in v and "PVR.IsTimeShift" not in v, f"{d}/{o} {cid}: {v}")
        r = tree(d, "VideoOSD")
        need(txt(ctl(r, 600), "visible") == txt(ctl(r, 607), "visible"), f"{d}/VideoOSD 600/607 differ")

def osd_nav():
    """37/38: the volume slider passes Left/Right on when disabled; row 202
    wraps at both ends."""
    for d in DIRS:
        for o in OSDS + ("PlayerControls",):
            r = tree(d, o)
            s = ctl(r, 9983)
            need(txt(s, "onleft") == "9982" and txt(s, "onright") in ("9951", "201"), f"{d}/{o} 9983 left/right")
        for o in OSDS:
            g = ctl(tree(d, o), 202)
            need(g.find("onright") is None and g.find("onleft") is None, f"{d}/{o} 202 has onleft/onright")

def preview():
    """31: live TV channel preview drawn, and switchable by touch."""
    for d in DIRS:
        r = tree(d, "VideoFullScreen")
        g = [c for c in r.iter("control") if "Player.ChannelPreviewActive" in txt(c, "visible")
             and c.get("type") == "group"]
        need(len(g) == 1 and all(c.get("id") not in (None, "0") for c in g[0].iter("control")),
             f"{d}/VideoFullScreen preview group (every child needs a non-zero id)")
        b = ctl(tree(d, "VideoOSD"), 9953)
        need(b is not None and onclicks(b) == ["Dialog.Close(VideoOSD,true)", "Action(Select)"]
             and "Player.ChannelPreviewActive" in txt(b, "visible"), f"{d}/VideoOSD 9953")

def fullscreen():
    """7/8: zoom readout full width and scrolling; info has a progress bar."""
    for d in DIRS:
        r = tree(d, "VideoFullScreen")
        for cid in (10, 11, 12):
            c = ctl(r, cid)
            need(num(c, "width") >= 992 and txt(c, "scroll") == "true", f"{d}/VideoFullScreen {cid}")
        r = tree(d, "DialogFullScreenInfo")
        need(any(c.get("type") == "progress" and txt(c, "info") == "Player.Progress" for c in r.iter("control")),
             f"{d}/DialogFullScreenInfo progress")

def slideshow():
    """4: the strip is pointer/touch only - no dead onleft/onright."""
    for d in DIRS:
        r = tree(d, "SlideShow")
        for cid in range(9801, 9806):
            c = ctl(r, cid)
            need(c is not None and c.find("onleft") is None and c.find("onright") is None, f"{d}/SlideShow {cid}")

def pvr_titles():
    """5/6: channel OSD title names the group (TV or radio); the channel guide
    is titled Guide and names the channel."""
    v = open(os.path.join(SKIN, "xml", "Variables.xml")).read()
    need("MusicPlayer.ChannelGroup" in v and "MusicPlayer.ChannelName" in v, "Variables PVRGroupVar/PVRChannelVar")
    for d in DIRS:
        a = open(os.path.join(SKIN, d, "DialogPVRChannelsOSD.xml")).read()
        need("$LOCALIZE[19019]$VAR[PVRGroupVar]" in a, f"{d}/DialogPVRChannelsOSD title")
        b = open(os.path.join(SKIN, d, "DialogPVRChannelGuide.xml")).read()
        need("$LOCALIZE[19069]$VAR[PVRChannelVar]" in b, f"{d}/DialogPVRChannelGuide title")

# ---------------------------------------------------------------- touch sizes
def dialog_files(d):
    for p in sorted(glob.glob(os.path.join(SKIN, d, "*.xml"))):
        s = open(p).read()
        if "Dialog_Box" in s or "Win_Boxes_dialog" in s:
            yield os.path.basename(p)[:-4], etree.parse(p).getroot()

HIT_EXEMPT = {
    # (window, id): why a <=34 px button needs no touch size
}

def small_buttons():
    """9/32: every on-screen button 34 px high or less in a dialog has a
    height that grows under XLC, or a hit rect (own or Size_Hit)."""
    for d in DIRS:
        for name, r in dialog_files(d):
            for c in r.iter("control"):
                if c.get("type") not in ("button", "radiobutton", "togglebutton"):
                    continue
                if (num(c, "left") or 0) <= -1000:
                    continue                        # parked off screen (a stub Kodi needs)
                anc = [a for a in c.iterancestors("control")]
                if any((num(a, "left") or 0) <= -1000 for a in anc):
                    continue
                if c.get("id") in ("9901", "9902", "9903") or any(a.get("id") in ("9900",) for a in anc):
                    continue                        # title-bar boxes: Win_Boxes_* (touch variants)
                h = num(c, "height")
                if h is None or h > 34 or txt(c, "visible") == "false":
                    continue
                ok = (c.find("hitrect") is not None or has_xl(c, "Height_")
                      or any(n == "Size_Hit" for n, _ in includes(c)))
                need(ok or (name, c.get("id")) in HIT_EXEMPT,
                     f"{d}/{name}:{c.sourceline}: {c.get('type')} {c.get('id')} is {h} px with no touch size")

def scrollbars():
    """10: every visible scrollbar is 30 px under XLC (Size_Width / its info
    include) or has a 30 px hit rect."""
    for d in DIRS:
        for p in sorted(glob.glob(os.path.join(SKIN, d, "*.xml"))):
            r = etree.parse(p).getroot()
            for sb in r.iter("control"):
                if sb.get("type") != "scrollbar" or (num(sb, "left") or 0) <= -1000:
                    continue
                if "$PARAM[id]" in (sb.get("id") or ""):
                    continue                        # an unused include template
                if os.path.basename(p) == "Home.xml":
                    continue                        # the desktop's bar: home.py sizes it per grid (Home_Scroll_*)
                incs = includes(sb)
                ok = (any(n in ("Size_Width", "Size_Hit") and XLC in cond for n, cond in incs)
                      or any(n.startswith("Media_SBWidth") and XLC in cond for n, cond in incs)
                      or sb.find("hitrect") is not None)
                need(ok, f"{d}/{os.path.basename(p)}: scrollbar {sb.get('id')} stays 18 px")

def headings():
    """11: no title-bar heading (left 29, top 3) in a dialog with Win_Boxes_dialog
    runs under the Touch-mode boxes (135 px from the right edge)."""
    for d in DIRS:
        for name, r in dialog_files(d):
            for c in r.iter("control"):
                if c.get("type") not in ("label", "fadelabel") or num(c, "left") != 29 or num(c, "top") != 3:
                    continue
                par = c.getparent()
                pw = num(par, "width")
                w = num(c, "width")
                if pw is None or w is None:
                    continue                        # Dialog_Heading_Width / _Touch pair
                if 'value="dialog"' not in etree.tostring(par).decode() and "Win_Boxes_dialog" not in etree.tostring(par).decode():
                    continue
                need(29 + w <= pw - 138, f"{d}/{name}: heading {c.get('id')} 29+{w} reaches the boxes ({pw})")

def settings_gap():
    """12: the settings dialogs grow 16 px with the taller button row."""
    for d in DIRS:
        for n in ("DialogSettings", "DialogAddonSettings"):
            s = open(os.path.join(SKIN, d, n + ".xml")).read().replace('"/>', '" />')
            need(f'<include content="Size_Height" condition="{XLC}"><param name="v" value="502" />' in s
                 and f'<include content="Dialog_Box" condition="{XLC}">' in s, f"{d}/{n}: no 502 px box")

def context_menu():
    """13: the outside catchers are Touch mode only; entries cover the gaps."""
    for d in DIRS:
        r = tree(d, "DialogContextMenu")
        for cid in range(9971, 9975):
            need(txt(ctl(r, cid), "visible") == "Skin.HasSetting(touchmode)", f"{d}: catcher {cid}")
        need(sum(1 for n, _ in includes(ctl(r, 1000)) if n == "Size_Hit") == 2, f"{d}: 1000 hit rects")

def media_source():
    """14: the path list shows its scrollbar."""
    for d in DIRS:
        r = tree(d, "DialogMediaSource")
        need(txt(ctl(r, 10), "pagecontrol") == "60" and (num(ctl(r, 60), "top") or 0) > 0
             and txt(ctl(r, 10), "onright") == "60", f"{d}: DialogMediaSource 60")

def calibration():
    """15/19: the hint says tap/swipe; the textures are not stretched art."""
    need(not strings().get(31834, "Drag").startswith("Drag"), "31834 still says Drag")
    from PIL import Image
    need(Image.open(os.path.join(SKIN, "media", "calibrate", "cal_sub.png")).size == (380, 90), "cal_sub 380x90")
    for d in DIRS:
        c = ctl(tree(d, "SettingsScreenCalibration"), 11)
        need(c.find("texturenofocus").get("border") and c.find("texturefocus").get("border"), f"{d}: 11 border")

def numeric():
    """16/36: number pad 20/22 are plain buttons; every row chains Up/Down."""
    for d in DIRS:
        r = tree(d, "DialogNumeric")
        for cid in (20, 22):
            need(ctl(r, cid).get("type") == "button", f"{d}: DialogNumeric {cid}")
        rows = [g for g in r.iter("control") if g.get("type") == "grouplist"]
        need(len(rows) == 5 and all(g.find("onup") is not None and g.find("ondown") is not None for g in rows),
             f"{d}: DialogNumeric rows")

def keyboard():
    """24/35: keyboard rows chain Up/Down; 600 keys grow under XLC, box fits."""
    for d in DIRS:
        r = tree(d, "DialogKeyboard")
        rows = [g for g in r.iter("control") if g.get("type") == "grouplist"]
        need(len(rows) == 6 and all(g.get("id") and g.find("onup") is not None and g.find("ondown") is not None
                                    for g in rows), f"{d}: DialogKeyboard rows")
    k = ctl(tree("xml", "DialogKeyboard"), 100)
    need(has_xl(k, "Height_40"), "xml keyboard keys: no XLC height")
    s = open(os.path.join(SKIN, "xml", "DialogKeyboard.xml")).read()
    m = re.search(rf'<include content="Size_Height" condition="{re.escape(XLC)}"><param name="v" value="(\d+)"', s)
    need(m and int(m.group(1)) <= 534, "xml keyboard box under XLC")

def guide():
    """18: the guide strip is wide enough for 'Group: <name>'."""
    for d in DIRS:
        b = ctl(tree(d, "MyPVRGuide"), 28)
        need(num(b, "width") >= 178 and txt(b, "font") == "chromesmall", f"{d}: guide 28")

def autoscroll():
    """21/23: long descriptions follow Skin settings > Scroll long
    descriptions; only a confirmation and the skin settings help ignore it."""
    for d in DIRS:
        for p in sorted(glob.glob(os.path.join(SKIN, d, "*.xml"))):
            n = os.path.basename(p)[:-4]
            if n in ("DialogConfirm", "SkinSettings"):
                continue
            for a in etree.parse(p).getroot().iter("autoscroll"):
                t = (a.text or "").strip()
                need(t == "false" or "Skin.HasSetting(autoscroll)" in t, f"{d}/{n}: autoscroll '{t}'")

def selected():
    """26/27: no textinv label without its own selectedcolor (C-1)."""
    for d in DIRS:
        for p in sorted(glob.glob(os.path.join(SKIN, d, "*.xml"))):
            for c in etree.parse(p).getroot().iter("control"):
                if c.get("type") in ("label", "fadelabel", "textbox") and txt(c, "textcolor") == "textinv":
                    need(c.find("selectedcolor") is not None, f"{d}/{os.path.basename(p)}: label {c.get('id')}")

def pvr_info():
    """28: programme / recording info: no empty cast panel, the PVR lines."""
    for d in DIRS:
        r = tree(d, "DialogPVRInfo")
        need(ctl(r, 50) is None, f"{d}: DialogPVRInfo still has 50")
        s = etree.tostring(r).decode()
        for k in ("ListItem.ChannelName", "ListItem.StartTime", "ListItem.EndTime", "ListItem.EpisodeName"):
            need(k in s, f"{d}: DialogPVRInfo lacks {k}")
        need(txt(ctl(r, 9001), "onup") == "61", f"{d}: DialogPVRInfo 9001 onup")

def outside():
    """33: tapping the dimmed picture closes the settings / power / now playing
    dialogs, and only those."""
    for d in DIRS:
        # xml names the include, xml768 has it expanded (tallpass)
        has = lambda r: ctl(r, 9989) is not None or any(n == "Dialog_DimClose" for n, _ in includes(r.find("controls")))
        for n in ("DialogSettings", "DialogButtonMenu", "PlayerControls"):
            need(has(tree(d, n)), f"{d}/{n}: a tap outside does not close it")
        for n in ("DialogKeyboard", "DialogNumeric", "DialogConfirm", "DialogAddonSettings"):
            need(not has(tree(d, n)), f"{d}/{n}: closes on a stray tap")
        b = ctl(tree(d, "DialogSettings"), 9989) if d == "xml768" else None
        need(d == "xml" or (b is not None and onclicks(b) == ["Action(Back)"]), f"{d}: 9989 runs Back")
    inc = etree.parse(os.path.join(SKIN, "xml", "Includes_Dialogs.xml")).getroot().find("include[@name='Dialog_DimClose']")
    b = inc.find(".//control[@id='9989']")
    need(b is not None and onclicks(b) == ["Action(Back)"] and b.find("onup") is not None, "Dialog_DimClose 9989")

def dialogselect():
    """39 + 9: DialogSelect's buttons lead back up to the list and grow."""
    for d in DIRS:
        r = tree(d, "DialogSelect")
        g = ctl(r, 5).getparent()
        ups = [(u.get("condition"), (u.text or "").strip()) for u in g.findall("onup")]
        need(("Control.IsVisible(6)", "6") in ups and (None, "3") in ups, f"{d}: DialogSelect onup {ups}")
        need(has_xl(g, "Size_Top") and has_xl(g, "Height_30"), f"{d}: DialogSelect row XLC")

CHECKS = {f.__name__: f for f in (menus, live_pair, osd_nav, preview, fullscreen, slideshow, pvr_titles,
                                  small_buttons, scrollbars, headings, settings_gap, context_menu,
                                  media_source, calibration, numeric, keyboard, guide, autoscroll,
                                  selected, pvr_info, outside, dialogselect)}

if __name__ == "__main__":
    names = sys.argv[1:] or list(CHECKS)
    for n in names:
        CHECKS[n]()
    for b in bad:
        print("  ", b)
    sys.exit(1 if bad else 0)
