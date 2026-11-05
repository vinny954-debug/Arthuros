#!/usr/bin/env python3
"""Emit the remaining Kodi windows in Arthur chrome.

Every window Kodi can open gets a real file carrying the control ids Kodi
requires (taken from inventory.json), so nothing errors out or opens blank.
The layout is ours; only the id/type contract is borrowed.
"""
import json, os, textwrap

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skin.arthuros", "xml")
INV = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.json")))

# windows written by hand - never touch these
HAND = {
 "Home","MyVideoNav","MyMusicNav","MyPics","MyPrograms","AddonBrowser","MyFavourites",
 "MyPlaylist","MyGames","MyPVRChannels","MyPVRRecordings","MyPVRSearch","MyPVRTimers",
 "DialogConfirm","DialogSelect","SkinSettings","Settings",
}
SKIP_PREFIX = ("Custom_", "View_", "Includes", "Defaults", "Font", "Variables")

TITLES = {
 "FileManager":"$LOCALIZE[7]", "MyWeather":"$LOCALIZE[8]", "Settings":"$LOCALIZE[5]",
 "SettingsCategory":"$LOCALIZE[5]", "SkinSettings":"$LOCALIZE[20077]",
 "SettingsSystemInfo":"$LOCALIZE[10007]", "SettingsProfile":"$LOCALIZE[13200]",
 "SettingsScreenCalibration":"$LOCALIZE[214]", "EventLog":"$LOCALIZE[14111]",
 "LoginScreen":"$LOCALIZE[20096]", "MyMusicPlaylistEditor":"$LOCALIZE[10503]",
 # SmartPlaylistEditor: Kodi writes its heading into label 2 (21432)
 "SmartPlaylistRule":"$LOCALIZE[21422]",
 "MyPVRGuide":"$LOCALIZE[19029]", "Timers":"$LOCALIZE[19040]",
 "PlayerControls":"$LOCALIZE[31907]", "VideoOSD":"$LOCALIZE[31907]",
 "MusicOSD":"$LOCALIZE[31907]", "MusicVisualisation":"$LOCALIZE[31907]",
 "SlideShow":"$LOCALIZE[108]", "GameOSD":"$LOCALIZE[31907]",
 "DialogAddonSettings":"$LOCALIZE[10004]", "DialogSettings":"$LOCALIZE[5]",
 # dialogs Kodi gives no heading (no id 1 written by their C++ class)
 "DialogButtonMenu":"$LOCALIZE[31976]", "DialogSeekBar":"$LOCALIZE[31907]",
 "VideoOSDBookmarks":"$LOCALIZE[298]",
 "DialogPVRChannelManager":"$LOCALIZE[19199]$INFO[Container(20).NumItems, (,)]",
 "DialogPVRGroupManager":"$LOCALIZE[19205]",
 "DialogPVRGuideSearch":"$LOCALIZE[19142]", "DialogPVRGuideControls":"$LOCALIZE[19222]",
 "DialogPVRChannelsOSD":"$LOCALIZE[19019]", "DialogPVRChannelGuide":"$LOCALIZE[19019]",
 "DialogPictureInfo":"$LOCALIZE[13406]", "DialogPlayerProcessInfo":"$LOCALIZE[14116]",
 "DialogFullScreenInfo":"$LOCALIZE[14116]", "DialogPVRRadioRDSInfo":"$LOCALIZE[29900]",
}
TITLES["MyPVRGuide"] = "$LOCALIZE[19069]"   # 19029 is "Channel"
TITLES["PlayerControls"] = "$LOCALIZE[16003]"

H = '<?xml version="1.0" encoding="UTF-8"?>\n'

def w(name, body):
    open(os.path.join(OUT, name + ".xml"), "w").write(body)

def ctrl(kind, cid, l, t, wd, ht, extra="", label=None, indent=6):
    sp = " " * indent
    s  = f'{sp}<control type="{kind}"' + (f' id="{cid}"' if cid else "") + ">\n"
    s += f"{sp}  <left>{l}</left><top>{t}</top><width>{wd}</width><height>{ht}</height>\n"
    if label is not None:
        s += f"{sp}  <label>{label}</label>\n"
    if extra:
        s += textwrap.indent(extra.rstrip("\n"), sp + "  ") + "\n"
    s += f"{sp}</control>\n"
    return s

FRAME = """    <control type="group">
      <left>6</left><top>30</top><width>1012</width><height>534</height>
      <include content="Win_Frame">
        <param name="width" value="1012" /><param name="height" value="534" />
      </include>
      <control type="group">
        <left>3</left><top>3</top>
        <include content="Win_Title">
          <param name="width" value="1006" />
          <param name="colour" value="{colour}" />
          <param name="icon" value="{icon}" />
          <param name="label" value="{title}" />
          <param name="down" value="{down}" />
          <param name="boxes" value="{boxes}" />
        </include>
      </control>
{body}    </control>
"""

# Title-bar box set for full-screen windows that are not ordinary windows:
# Kodi opens these as dialogs, or (the login screen) must not be skippable.
BOXES = {"LoginScreen": "none", "SmartPlaylistEditor": "dialog",
         "SmartPlaylistRule": "dialog", "VideoOSDBookmarks": "dialog",
         # overlays that come and go by themselves: nothing to minimise or close
         "DialogBusy": "none", "DialogExtendedProgressBar": "none",
         "DialogVolumeBar": "none", "DialogSeekBar": "none"}

# Dialogs Kodi can open on top of the login screen: the power menu (its
# Shutdown button), and the keyboard / numeric pad that ask for a locked
# profile's password or the master code. Their title bar must not offer a
# way past the login: Win_Boxes_dialog's _ box runs ActivateWindow(Home),
# and CGUIWindowManager::ActivateWindow_Internal only checks CheckMenuLock,
# which does not cover Home. These get Win_Boxes_none from Dialog_Box and
# their own copy of the dialog boxes (login_safe_boxes) instead.
LOGIN_SAFE = {"DialogButtonMenu", "DialogKeyboard", "DialogNumeric"}
NOT_AT_LOGIN = "!Window.IsVisible(loginscreen)"

def login_safe_boxes(wd, down):
    """Win_Boxes_dialog, read from Includes_Chrome.xml so it keeps whatever
    look that file gives it, with _ (9901) hidden while the login screen is
    up - a greyed _ is drawn in its place, as on the desktop's own panel -
    and every ActivateWindow in it conditional as well. Placed where
    Dialog_Box puts the title bar (3,3, width wd-6)."""
    from lxml import etree
    import copy, re
    src = os.path.join(OUT, "Includes_Chrome.xml")
    root = etree.parse(src).getroot()
    inc = root.xpath("include[@name='Win_Boxes_dialog']")[0]
    group = copy.deepcopy(inc.find("definition").find("control"))
    for el in group.iter():
        if el.text and "$PARAM[down]" in el.text:
            el.text = el.text.replace("$PARAM[down]", down)
    for oc in group.iter("onclick"):
        if "ActivateWindow" in (oc.text or ""):
            c = oc.get("condition")
            oc.set("condition", f"{NOT_AT_LOGIN} + [{c}]" if c else NOT_AT_LOGIN)
    for c in group.iter("control"):
        if c.get("id") == "9901":
            v = etree.SubElement(c, "visible"); v.text = NOT_AT_LOGIN
        elif c.get("type") == "image" and "9901" in (c.findtext("visible") or ""):
            v = c.find("visible"); v.text = f"{v.text} + {NOT_AT_LOGIN}"
    b9901 = [c for c in group.iter("control") if c.get("id") == "9901"][0]
    # geometry: plain right/top/width/height, or the WinBox include that
    # gives the boxes their Touch-mode size (Includes_Chrome.xml)
    pos = "".join(etree.tostring(e, with_tail=False).decode().strip() for e in b9901
                  if e.tag in ("left", "right", "top", "width", "height")
                  or (e.tag == "include" and (e.get("content") or "").startswith("WinBox")))
    assert pos, "login_safe_boxes: no geometry found on 9901"
    grey = (f'<control type="image">{pos}<texture colordiffuse="facetint">wc_face.png</texture>'
            f'<visible>Window.IsVisible(loginscreen)</visible></control>'
            f'<control type="image">{pos}<texture colordiffuse="textdim">wc_min_dg.png</texture>'
            f'<visible>Window.IsVisible(loginscreen)</visible></control>')
    for el in reversed(etree.fromstring(f"<x>{grey}</x>")):
        group.insert(0, el)
    for el in group.iter():
        el.tail = None
        if el.text is not None and not el.text.strip():
            el.text = None
    body = etree.tostring(group, pretty_print=True).decode()
    body = re.sub(r"(?<=[^\s])/>", " />", body)
    return ("      <!-- the dialog boxes, login-safe (LOGIN_SAFE) -->\n"
            "      <control type=\"group\">\n"
            f"        <left>3</left><top>3</top><width>{wd - 6}</width><height>26</height>\n"
            + textwrap.indent(body, "        ") + "      </control>\n")

def fullwindow(name, body, default="", views="", colour="accent2",
               icon="icons24/folder.png", title=None):
    title = title if title is not None else TITLES.get(name, "")
    s  = H + "<window>\n"
    if default: s += f"  <defaultcontrol always=\"false\">{default}</defaultcontrol>\n"
    if views:   s += f"  <views>{views}</views>\n"
    s += "  <backgroundcolor>desktop</backgroundcolor>\n  <controls>\n"
    s += "    <include>Chrome_Desktop</include>\n    <include>Chrome_Menubar</include>\n"
    s += FRAME.format(colour=colour, icon=icon, title=title, body=body, down=default or "",
                      boxes=BOXES.get(name, "window"))
    up = default if default else "9100"
    s += f'    <include content="Chrome_Taskbar"><param name="up" value="{up}" /></include>\n'
    s += "  </controls>\n</window>\n"
    return s

# dialogs whose heading Kodi writes into their own label (id 2) on the title bar
KODI_HEADED = {"DialogSettings", "DialogAddonSettings"}

def dialog(name, wd, ht, body, default="", icon="icons24/file.png",
           colour="accent2", heading=True, dim=True, zorder=None, title=None,
           anchor="center", visible=(), default_always=False, pre=""):
    """title: a fixed title-bar label, for dialogs Kodi gives no heading (id 1).
    Without one, a dialog with heading=False takes its TITLES entry.
    anchor: "center" (default) or "bottom" (sits on the bottom edge, centred
    horizontally - tallpass keeps it on the bottom edge at 768).
    visible: window-level <visible> conditions (Kodi opens modeless dialogs
    such as DialogSeekBar only through these, CGUIDialog::UpdateVisibility).
    pre: controls placed before the dialog box (e.g. a full-screen tap catcher)."""
    inner = wd - 6
    if title is None and not heading and name not in KODI_HEADED:
        title = TITLES.get(name)
    if title:
        heading = False
    s  = H + "<window>\n"
    for v in visible:
        s += f"  <visible>{v}</visible>\n"
    if zorder: s += f"  <zorder>{zorder}</zorder>\n"
    if default:
        al = ' always="true"' if default_always else ""
        s += f"  <defaultcontrol{al}>{default}</defaultcontrol>\n"
    s += "  <controls>\n"
    if dim: s += "    <include>Dialog_Dim</include>\n"
    s += pre
    s += "    <control type=\"group\">\n"
    if anchor == "bottom":
        s += "      <centerleft>50%</centerleft><bottom>0</bottom>\n"
    else:
        s += "      <centerleft>50%</centerleft><centertop>50%</centertop>\n"
    s += f"      <width>{wd}</width><height>{ht}</height>\n"
    s += f'      <include content="Dialog_Box">\n'
    s += f'        <param name="width" value="{wd}" /><param name="height" value="{ht}" />\n'
    s += f'        <param name="innerwidth" value="{inner}" />\n'
    s += f'        <param name="icon" value="{icon}" /><param name="colour" value="{colour}" />\n'
    s += f'        <param name="down" value="{default}" />\n'
    boxes = "none" if name in LOGIN_SAFE else BOXES.get(name, "dialog")
    s += f'        <param name="boxes" value="{boxes}" />\n'
    if title:
        s += f'        <param name="title" value="{title}" />\n'
    s += "      </include>\n"
    if heading:
        s += f'      <include content="Dialog_Heading"><param name="width" value="{inner-100}" /></include>\n'
    s += body
    if name in LOGIN_SAFE:
        s += login_safe_boxes(wd, default)
    s += "    </control>\n  </controls>\n</window>\n"
    return s

# ====================================================================== parts
def list_block(cid, sb, l, t, wd, ht, rowh=28, onleft="9490", ondown="9100"):
    iw = wd - 24
    return f"""      <control type="image">
        <left>{l}</left><top>{t}</top><width>{wd}</width><height>{ht}</height>
        <texture border="2">panel_sunken.png</texture>
      </control>
      <control type="list" id="{cid}">
        <left>{l+3}</left><top>{t+3}</top><width>{iw}</width><height>{ht-6}</height>
        <onleft>{onleft}</onleft><onright>{sb}</onright>
        <onup>{cid}</onup><ondown>{ondown}</ondown>
        <pagecontrol>{sb}</pagecontrol>
        <itemlayout height="{rowh}" width="{iw}">
          <include content="Arthur_ItemLayout"><param name="width" value="{iw-8}" /></include>
        </itemlayout>
        <focusedlayout height="{rowh}" width="{iw}">
          <include content="Arthur_FocusedLayout"><param name="width" value="{iw}" /></include>
        </focusedlayout>
      </control>
      <control type="scrollbar" id="{sb}">
        <left>{l+wd-21}</left><top>{t+3}</top><width>18</width><height>{ht-6}</height>
        <onleft>{cid}</onleft><onright>{onleft}</onright>
      </control>
"""

def well(l, t, wd, ht, tex="panel_sunken.png", indent=6):
    sp = " " * indent
    return (f"{sp}<control type=\"image\">\n"
            f"{sp}  <left>{l}</left><top>{t}</top><width>{wd}</width><height>{ht}</height>\n"
            f"{sp}  <texture border=\"2\">{tex}</texture>\n{sp}</control>\n")

# ====================================================== settings family
SETTING_TEMPLATES = """
      <!-- Templates. Kodi clones these into grouplist 5; they are never
           shown where they sit, only their size and styling matter. -->
      <control type="button" id="7">
        <left>-2000</left><top>0</top><width>600</width><height>30</height>
        <align>left</align><textoffsetx>12</textoffsetx>
      </control>
      <control type="radiobutton" id="8">
        <left>-2000</left><top>0</top><width>600</width><height>30</height>
        <align>left</align><textoffsetx>12</textoffsetx>
      </control>
      <control type="spincontrolex" id="9">
        <left>-2000</left><top>0</top><width>600</width><height>30</height>
        <align>left</align><textoffsetx>12</textoffsetx>
      </control>
      <control type="image" id="11">
        <left>-2000</left><top>0</top><width>600</width><height>2</height>
        <texture>fill_black.png</texture>
      </control>
      <control type="edit" id="12">
        <left>-2000</left><top>0</top><width>600</width><height>30</height>
        <align>left</align><textoffsetx>12</textoffsetx>
      </control>
      <control type="sliderex" id="13">
        <left>-2000</left><top>0</top><width>600</width><height>30</height>
        <align>left</align><textoffsetx>12</textoffsetx>
      </control>
      <control type="label" id="14">
        <left>-2000</left><top>0</top><width>600</width><height>30</height>
        <font>bold</font><align>left</align>
      </control>
      <control type="colorbutton" id="15">
        <left>-2000</left><top>0</top><width>600</width><height>30</height>
        <align>left</align><textoffsetx>12</textoffsetx>
      </control>
"""

def settings_window(name, categories=True):
    body  = ""
    if categories:
        body += well(6, 34, 300, 494, "panel_sunken_grey.png")
        body += """      <control type="button" id="10">
        <left>-2000</left><top>0</top><width>288</width><height>32</height>
        <align>left</align><textoffsetx>12</textoffsetx>
      </control>
      <control type="grouplist" id="3">
        <left>12</left><top>40</top><width>288</width><height>404</height>
        <orientation>vertical</orientation><itemgap>2</itemgap>
        <onleft>3</onleft><onright>5</onright>
        <onup>20</onup><ondown>20</ondown>
      </control>
      <!-- Settings level: Kodi's own button 20 (GUIWindowSettingsCategory.cpp).
           Kodi only writes Basic / Standard / Advanced / Expert on it; the
           onclick sends ACTION_SETTINGS_LEVEL_CHANGE, which OnAction handles
           (a click on 20 itself is ignored by Kodi). -->
      <!-- hung from the bottom, so the taller Touch mode / Extra large button
           (50 px, sizepass.py) still ends inside the panel -->
      <control type="label">
        <left>14</left><bottom>48</bottom><width>284</width><height>20</height>
        <font>chromesmall</font><textcolor>textdim</textcolor>
        <label>$LOCALIZE[31950]</label>
        <visible>![String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]</visible>
      </control>
      <control type="label">
        <left>14</left><bottom>64</bottom><width>284</width><height>20</height>
        <font>chromesmall</font><textcolor>textdim</textcolor>
        <label>$LOCALIZE[31950]</label>
        <visible>[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]</visible>
      </control>
      <control type="button" id="20">
        <left>12</left><bottom>12</bottom><width>288</width><height>34</height>
        <align>center</align>
        <onclick>SettingsLevelChange</onclick>
        <onup>3</onup><ondown>9100</ondown><onright>5</onright>
      </control>
"""
        gx, gw = 312, 694
    else:
        gx, gw = 6, 1000

    left = "3" if categories else "5"
    body += well(gx, 34, gw, 400, "panel_sunken.png")
    body += f"""      <control type="label" id="2">
        <left>{gx+10}</left><top>38</top><width>{gw-40}</width><height>26</height>
        <font>bigbold</font>
      </control>
      <control type="grouplist" id="5">
        <left>{gx+10}</left><top>68</top><width>{gw-44}</width><height>360</height>
        <orientation>vertical</orientation><itemgap>3</itemgap>
        <onleft>{left}</onleft><onright>60</onright>
        <onup>9100</onup><ondown>9100</ondown>
        <pagecontrol>60</pagecontrol>
      </control>
      <control type="scrollbar" id="60">
        <left>{gx+gw-24}</left><top>68</top><width>18</width><height>360</height>
        <onleft>5</onleft><onright>{left}</onright>
      </control>
"""
    body += well(gx, 442, gw, 86, "panel_sunken_grey.png")
    body += f"""      <control type="textbox" id="6">
        <left>{gx+8}</left><top>448</top><width>{gw-16}</width><height>74</height>
        <font>small</font><textcolor>textdim</textcolor>
      </control>
"""
    body += SETTING_TEMPLATES
    return fullwindow(name, body, default="3" if categories else "5",
                      icon="icons24/settings.png", colour="accent1")

def settings_dialog(name):
    """GUIDialogSettingsBase: Kodi clones button 10 into grouplist 3, one per
    settings category (an add-on's "pages" - YouTube has several), and the
    templates 7-15 into grouplist 5 for the chosen category. 2 is the heading,
    6 the description, 28/29/30 OK, Cancel and Defaults.

    Until 0.8.2 the category grouplist sat off screen, so an add-on with
    several pages only ever showed its first. Add-on settings now get a page
    list on the left. The other settings dialogs (audio, video, subtitle
    options...) only ever have one category, so they keep the full width."""
    cats = name == "DialogAddonSettings"
    body = f"""      <control type="label" id="2">
        <left>29</left><top>3</top><width>790</width><height>26</height>
        <font>chromebold</font><textcolor>titletext</textcolor><aligny>center</aligny>
      </control>
"""
    if cats:
        body += well(10, 36, 230, 320, "panel_sunken_grey.png", indent=6)
        body += """      <control type="grouplist" id="3">
        <left>16</left><top>42</top><width>218</width><height>308</height>
        <orientation>vertical</orientation><itemgap>3</itemgap>
        <onright>5</onright><onleft>5</onleft><ondown>9001</ondown><onup>9001</onup>
      </control>
      <control type="button" id="10">
        <left>-2000</left><top>0</top><width>218</width><height>30</height>
        <align>left</align><textoffsetx>10</textoffsetx>
      </control>
"""
        sx, sw = 256, 606
    else:
        body += """      <control type="grouplist" id="3">
        <left>-2000</left><top>0</top><width>200</width><height>300</height>
        <orientation>vertical</orientation>
      </control>
      <control type="button" id="10">
        <left>-2000</left><top>0</top><width>200</width><height>30</height>
      </control>
"""
        sx, sw = 20, 846
    body += well(sx - 10, 36, 890 - (sx - 10), 320, "panel_sunken.png", indent=6)
    body += f"""      <control type="grouplist" id="5">
        <left>{sx}</left><top>44</top><width>{sw}</width><height>304</height>
        <orientation>vertical</orientation><itemgap>3</itemgap>
        <onright>60</onright><onleft>{3 if cats else 5}</onleft>
        <ondown>9001</ondown><onup>9001</onup>
        <pagecontrol>60</pagecontrol>
      </control>
      <control type="scrollbar" id="60">
        <left>870</left><top>44</top><width>18</width><height>304</height>
        <onleft>5</onleft><onright>{3 if cats else 5}</onright>
      </control>
"""
    body += well(10, 364, 880, 70, "panel_sunken_grey.png", indent=6)
    body += """      <control type="textbox" id="6">
        <left>18</left><top>370</top><width>864</width><height>58</height>
        <font>small</font><textcolor>textdim</textcolor>
      </control>
"""
    body += SETTING_TEMPLATES.replace("<width>600</width>", f"<width>{sw}</width>")
    XLC = "[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]"
    # the bottom row: 30 px, 46 in Touch mode / Extra large (Height_30_XL,
    # sizepass.py). Hung from the bottom edge, so the taller row grows up
    # into the gap above it instead of out of the dialog.
    hgt = (f'<include content="Height_30_XL" condition="{XLC}" />'
           f'<include content="Height_30" condition="!{XLC}" />')
    btn = lambda cid, extra="": (f'        <control type="button" id="{cid}"><width>180</width>{hgt}'
                                 f'<align>center</align>{extra}</control>\n')
    body += (f"""      <control type="grouplist" id="9001">
        <left>13</left><bottom>6</bottom><width>874</width>{hgt}
        <orientation>horizontal</orientation><align>center</align><itemgap>8</itemgap>
        <onup>5</onup><ondown>{3 if cats else 5}</ondown>
""" + btn(28) + btn(29) + btn(30)
             + (("        <!-- settings level: Kodi labels it (GUIDialogAddonSettings.cpp CONTROL_BTN_LEVELS) -->\n"
                 + btn(20, "<onclick>SettingsLevelChange</onclick>")) if cats else "")
             + "      </control>\n")
    return dialog(name, 900, 486, body, default="3" if cats else "5",
                  icon="icons24/settings.png", colour="accent1", heading=False)

# ====================================================== player / OSD family
# The video, music and game OSDs are one touch-first bar along the bottom
# edge, like Arthur's icon bar. Nothing is dimmed, and a tap on the picture
# above the bar closes it (Kodi swallows a tap on a modal dialog otherwise).
# Every size here is already a touch size, so nothing has to grow for Extra
# large or Touch mode: rows are 36-48 px, text uses the chrome fonts (never
# more than 20 px) and the glyphs are 24 px.
BOXES.update({"VideoOSD": "none", "MusicOSD": "none", "GameOSD": "none",
              # these carry their own Close button; over playback the title
              # bar's minimise / full-screen boxes would leave or do nothing
              "DialogFullScreenInfo": "none", "DialogPlayerProcessInfo": "none",
              "DialogPVRRadioRDSInfo": "none", "VideoOSDBookmarks": "none"})

OSD_W = 1024
SEEK_T, SEEK_H = 32, 36       # time | seek slider | duration (game: help text)
TR_T, TR_H = 74, 48           # transport | mute + volume | Hide
TX_T, TX_H = 128, 44          # text buttons
OSD_H = TX_T + TX_H + 8
TR_W = 60                     # a transport button: 60x48 with a 24 px glyph
VOL_W, HIDE_W = 220, 110
HIDE_L = OSD_W - 8 - HIDE_W
VOL_L = HIDE_L - 8 - VOL_W
MUTE_L = VOL_L - 6 - TR_W

LIVE_V = "VideoPlayer.Content(LiveTV)"
LIVE_M = "MusicPlayer.Content(LiveTV)"
LIVE = f"[{LIVE_V} | {LIVE_M}]"
OSD_LIVE = {"video": LIVE_V, "music": LIVE_M}

def xattr(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")

def onclicks(acts, sp):
    """<onclick> lines; an action may be (condition, action). CGUIAction
    evaluates every condition before it runs anything."""
    out = ""
    for a in acts:
        if isinstance(a, tuple):
            out += f'{sp}<onclick condition="{xattr(a[0])}">{a[1]}</onclick>\n'
        else:
            out += f"{sp}<onclick>{a}</onclick>\n"
    return out

def navs(sp, **dirs):
    """<onup>... lines. A value is an id, or a list of (condition, id) tried in
    order (CGUIAction::GetNavigation takes the first whose condition holds)."""
    out = ""
    for d in ("up", "down", "left", "right"):
        v = dirs.get(d)
        if v is None:
            continue
        for cond, tgt in (v if isinstance(v, list) else [(None, v)]):
            c = f' condition="{xattr(cond)}"' if cond else ""
            out += f"{sp}<on{d}{c}>{tgt}</on{d}>\n"
    return out

def glyph_tex(glyph, size):
    return glyph if ("/" in glyph or "$" in glyph) else f"icons{size}/{glyph}.png"

def hitrect(sp, x, y, w, h, pad, pady=None):
    """T-6: a <hitrect> `pad` px larger than the control on every side, so a
    finger landing in the gap between two buttons still hits one. The rect
    is in the PARENT's coordinates (GUIControlFactory::GetHitRect parses x/y
    like <left>/<top>); a grouplist child sits at 0,0 and Kodi moves the
    rect with it (CGUIControl::SetPosition). Pads must stay within half of
    the gap to the neighbour, or two controls would claim the same tap."""
    pady = pad if pady is None else pady
    return (f'{sp}<hitrect x="{x - pad}" y="{y - pady}" w="{w + 2 * pad}" h="{h + 2 * pady}" />\n'
            if pad else "")

OSD_HIT = 3      # half the 6 px itemgap / row gap of the OSD and mini-player

def icon_radio(cid, glyph, w, h, clicks, indent=8, size=16, selected=None,
               glyph_on=None, visible=None, nav=None, pos=None, hit=0):
    """A glyph button that is a single focusable control: the radio texture is
    the glyph (radioposx is measured from the left edge,
    GUIRadioButtonControl.cpp). It keeps keyboard navigation inside a
    grouplist, which a group holding a button and an image does not (Kodi
    navigates from the button, which has no actions of its own).
    Without `selected` both states draw the same glyph, so a tap never flips
    its look. With it, the state follows the condition (m_toggleSelect):
    `glyph_on` while it holds, `glyph` otherwise (Play/Pause, Mute)."""
    sp = " " * indent
    x, y = (w - size) // 2, (h - size) // 2
    off = glyph_tex(glyph, size)
    on = glyph_tex(glyph_on, size) if glyph_on else off
    s = f'{sp}<control type="radiobutton" id="{cid}">\n'
    if pos:
        s += f"{sp}  <left>{pos[0]}</left><top>{pos[1]}</top>"
    else:
        s += f"{sp}  "
    s += f"<width>{w}</width><height>{h}</height>\n"
    s += hitrect(sp + "  ", *(pos or (0, 0)), w, h, hit)
    s += f"{sp}  <label></label>\n"
    for state, tex in (("on", on), ("off", off)):
        for f in ("focus", "nofocus", "disabled"):
            s += f"{sp}  <textureradio{state}{f}>{tex}</textureradio{state}{f}>\n"
    s += f"{sp}  <radiowidth>{size}</radiowidth><radioheight>{size}</radioheight>\n"
    s += f"{sp}  <radioposx>{x}</radioposx><radioposy>{y}</radioposy>\n"
    if selected:
        s += f"{sp}  <selected>{selected}</selected>\n"
    s += onclicks(clicks, sp + "  ")
    if nav:
        s += navs(sp + "  ", **nav)
    if visible:
        s += f"{sp}  <visible>{visible}</visible>\n"
    return s + f"{sp}</control>\n"

def icon_button(cid, glyph, w, h, clicks, indent=8, size=16):
    """Plain buttons have no radio texture, so the glyph rides in a group.
    (Kept for callers outside the OSD; inside a grouplist prefer icon_radio,
    whose single control keeps keyboard navigation.)"""
    sp = " " * indent
    ons = "".join(f"\n{sp}    <onclick>{c}</onclick>" for c in clicks)
    return (f'{sp}<control type="group" id="{9000 + int(cid)}">\n'
            f'{sp}  <width>{w}</width><height>{h}</height>\n'
            f'{sp}  <control type="button" id="{cid}">\n'
            f'{sp}    <left>0</left><top>0</top><width>{w}</width><height>{h}</height>\n'
            f'{sp}    <label></label>{ons}\n'
            f'{sp}  </control>\n'
            f'{sp}  <control type="image">\n'
            f'{sp}    <left>{(w-size)//2}</left><top>{(h-size)//2}</top><width>{size}</width><height>{size}</height>\n'
            f'{sp}    <texture>{glyph_tex(glyph, size)}</texture>\n'
            f'{sp}  </control>\n'
            f'{sp}</control>\n')

def slider(cid, l, t, wd, ht, action, info, visible=None, enable=None, nav=None, indent=6):
    """A touch slider: a tap jumps, a drag follows the finger
    (CGUISliderControl::OnMouseEvent). <action> seek / pvr.seek / volume are
    Kodi's own (GUISliderControl.cpp). The nib is the bevel texture scaled to
    the control height, so it is a ht x ht square. Kodi's default slider
    orientation is vertical, hence the explicit horizontal."""
    sp = " " * indent
    s = (f'{sp}<control type="slider" id="{cid}">\n'
         f"{sp}  <left>{l}</left><top>{t}</top><width>{wd}</width><height>{ht}</height>\n"
         f"{sp}  <orientation>horizontal</orientation>\n")
    if info:
        s += f"{sp}  <info>{info}</info>\n"
    if action:
        s += f"{sp}  <action>{action}</action>\n"
    if enable:
        s += f"{sp}  <enable>{enable}</enable>\n"
    if nav:
        s += navs(sp + "  ", **nav)
    if visible:
        s += f"{sp}  <visible>{visible}</visible>\n"
    return s + f"{sp}</control>\n"

# (id, glyph, onclick actions, {kind: visible condition}) - a kind that is not
# listed does not get the button. Rewind/forward resume first when paused:
# PlayerControl(Play) then Rewind would pause and the Rewind be ignored
# (PlayerBuiltins.cpp: rewind/forward only act while playing).
PREV_V = ("Player.HasSceneMarkers | Player.ChapterCount | Integer.IsGreater(Playlist.Length(video),1)"
          f" | [Player.SeekEnabled + {LIVE_V}]")
NEXT_V = ("Player.HasSceneMarkers | Player.ChapterCount | Integer.IsGreater(Playlist.Length(video),1)"
          " | PVR.IsTimeShift")
PREV_M = f"Player.ChapterCount | MusicPlayer.HasPrevious | [Player.SeekEnabled + {LIVE_M}]"
NEXT_M = "Player.ChapterCount | MusicPlayer.HasNext | PVR.IsTimeShift"
OSD_BUTTONS = [
  (600, "prev", ["PlayerControl(Previous)"], {"video": PREV_V, "music": PREV_M}),
  (601, "rew",  [("Player.Paused", "PlayerControl(Play)"), ("!Player.Paused", "PlayerControl(Rewind)")],
                {"video": f"Player.SeekEnabled + !{LIVE_V}", "music": f"Player.SeekEnabled + !{LIVE_M}"}),
  (602, "play", ["PlayerControl(Play)"], {"video": None, "music": None, "game": None}),
  (603, "stop", ["PlayerControl(Stop)"], {"video": None, "music": None, "game": None}),
  (606, "ffwd", [("Player.Paused", "PlayerControl(Play)"), ("!Player.Paused", "PlayerControl(Forward)")],
                {"video": f"Player.SeekEnabled + !{LIVE_V}", "music": f"Player.SeekEnabled + !{LIVE_M}"}),
  (607, "next", ["PlayerControl(Next)"], {"video": NEXT_V, "music": NEXT_M}),
]
# Play/Pause shows Pause while playing at normal speed (Estuary's rule)
PLAYING = "!Player.Paused + !Player.Forwarding + !Player.Rewinding"

def seek_targets(kind):
    """Where Up from the transport row (and Down from the text row) lands."""
    if kind == "game":
        return []
    live = OSD_LIVE[kind]
    return [(f"Player.SeekEnabled + !{live}", "9980"), (f"Player.SeekEnabled + {live}", "9981")]

# K-6: the music OSD's visualisation preset buttons sit in the transport
# row, right of the longest possible transport (6 x 60 + 5 x 6 = 390 px from
# x 8, so grouplist 201 is VIS_L - 8 - 6 = 390 wide: CGUIControlGroupList
# only hands mouse/touch to children that fit whole inside its width, and
# clips the rest). Only while the visualisation has presets to pick from.
VIS_L, VIS_W = 404, 196
VIS_ON = "Visualisation.HasPresets"
VIS_IF = "Control.IsVisible(203)"

def osd_transport(kind="video", top=TR_T):
    """Grouplist 201: big glyph buttons. Hidden ones collapse (the grouplist
    lays out visible children only)."""
    up = seek_targets(kind) + [(None, "202")]
    right = [(VIS_IF, "203"), (None, "9982")] if kind == "music" else "9982"
    s = (f'      <control type="grouplist" id="201">\n'
         f"        <left>8</left><top>{top}</top><width>{VIS_L - 14 if kind == 'music' else MUTE_L - 16}</width><height>{TR_H}</height>\n"
         f"        <orientation>horizontal</orientation><itemgap>6</itemgap>\n"
         + navs("        ", up=up, down="202", left="9951", right=right))
    for cid, glyph, acts, vis in OSD_BUTTONS:
        if kind not in vis:
            continue
        if cid == 602:
            s += icon_radio(cid, "play", TR_W, TR_H, acts, size=24, selected=PLAYING,
                            glyph_on="pause", visible=vis[kind], hit=OSD_HIT)
        else:
            s += icon_radio(cid, glyph, TR_W, TR_H, acts, size=24, visible=vis[kind], hit=OSD_HIT)
    s += "      </control>\n"
    return s

# Set by every media browser as it closes (onunload), so the OSD knows which
# add-on is playing when the stream path does not say.
PLUGIN_PROP = "Window(Home).Property(arthuros.plugin)"

def osd_buttons(gid, top, buttons, onup, ondown, onright=None, left=8, width=None, h=TX_H,
                hit=OSD_HIT, onleft=None, visible=None):
    """A row of text buttons: (id, width, label, [actions], visible[, selected]).
    With `selected` the entry is a radiobutton, whose circle shows the state
    (shuffle). Chrome font: at most 20 px, so the row fits every fontset."""
    width = width or (OSD_W - 2 * left)
    s = (f'      <control type="grouplist" id="{gid}">\n'
         f"        <left>{left}</left><top>{top}</top><width>{width}</width><height>{h}</height>\n"
         f"        <orientation>horizontal</orientation><itemgap>6</itemgap>\n"
         + navs("        ", up=onup, down=ondown, left=onleft, right=onright)
         + (f"        <visible>{visible}</visible>\n" if visible else ""))
    for b in buttons:
        cid, w, label, acts, vis = b[:5]
        sel = b[5] if len(b) > 5 else None
        kind = "radiobutton" if sel else "button"
        s += f'        <control type="{kind}" id="{cid}">\n'
        s += f"          <width>{w}</width><height>{h}</height>\n"
        s += hitrect("          ", 0, 0, w, h, hit)
        s += f"          <font>chrome</font><label>{label}</label>\n"
        if sel:
            s += f"          <selected>{sel}</selected>\n"
        s += onclicks(acts, "          ")
        if vis:
            s += f"          <visible>{vis}</visible>\n"
        s += "        </control>\n"
    return s + "      </control>\n"

# Settings dialogs stay over the bar (Kodi closes audio/subtitle settings when
# the OSD goes); windows that need the picture close the bar first.
AUDIO = (9962, 70, "$LOCALIZE[292]", ["ActivateWindow(OSDAudioSettings)"], None)
# The add-on that is playing: plugin:// paths name it; otherwise the browser
# it was started from recorded it (scripts/addonsettings.py).
# Never during live TV/radio: the path is pvr://, so only a stale recorded
# plugin could show it, and the row would run out of room (below).
def addon_button(live):
    return (9960, 170, "$LOCALIZE[10140]", ["RunScript(special://skin/scripts/addonsettings.py)"],
            f"!{live} + [String.StartsWith(Player.FilenameAndPath,plugin://) | !String.IsEmpty({PLUGIN_PROP})]")

def live_buttons(name, live):
    """Channels, Guide (and the radio's RDS text): close the bar first, so it
    does not sit over them. CGUIDialogVideoOSD keeps itself alive for these
    otherwise (GUIDialogVideoOSD.cpp FrameMove)."""
    return [(9966, 100, "$LOCALIZE[19019]", [f"Dialog.Close({name})", "ActivateWindow(PVROSDChannels)"], live),
            (9967, 70, "$LOCALIZE[19069]", [f"Dialog.Close({name})", "ActivateWindow(PVRChannelGuide)"],
             f"{live} + VideoPlayer.HasEPG")]

def record_button(live):
    return (608, 160, "$VAR[OSDRecordLabelVar]", ["PVR.ToggleRecordPlayingChannel"],
            f"{live} + PVR.CanRecordPlayingChannel")

def vis_presets():
    """K-6, music only: Preset opens Kodi's preset list (CGUIDialogVisualisation
    PresetList finds the visualisation through control id 2 of the
    visualisation window, which music_vis() gives it); 501 is Kodi's own
    lock button (GUIDialogMusicOSD.cpp CONTROL_LOCK_BUTTON sends
    ACTION_VIS_PRESET_LOCK), shown as a radiobutton that follows
    Visualisation.Locked. CGUIDialogMusicOSD::FrameMove keeps the bar up
    while the preset list is open."""
    up = seek_targets("music") + [(None, "202")]
    return osd_buttons(203, TR_T, [
        (9986, 80, "$LOCALIZE[13388]", ["ActivateWindow(VisualisationPresetList)"], None),
        (501, 110, "$LOCALIZE[20166]", [], None, "Visualisation.Locked"),
    ], up, "202", onright="9982", left=VIS_L, width=VIS_W, h=TR_H,
       onleft="201", visible=VIS_ON)

def osd_rows(name, kind):
    """The text-button row (grouplist 202), 1008 px. Widths are what each
    label needs at Extra large (10 px a glyph + 2x10 textoffsetx). The video
    row's guards keep its widest possible set inside 1008 (every gap 6):
    Teletext and the disc Menu never show together (a disc has no teletext),
    and Add-on settings never with the live TV buttons. The music row's
    widest sets: 790 px (shuffle, repeat, audio, queue, visualisation,
    add-on) and 806 px live (audio, queue, visualisation, channels, guide,
    RDS, record)."""
    if kind == "game":
        return [(9970, 130, "$LOCALIZE[35249]", ["ActivateWindow(InGameSaves)"], None),
                (9971, 70, "$LOCALIZE[13007]", ["PlayerControl(Reset)"], None),
                (9977, 100, "$LOCALIZE[35234]", ["ActivateWindow(GameControllers)"], None),
                (9978, 70, "$LOCALIZE[35110]", ["ActivateWindow(GamePorts)"], None),
                (9979, 90, "$LOCALIZE[35172]", ["ActivateWindow(GameAgents)"], None),
                (9972, 80, "$LOCALIZE[587]", ["ActivateWindow(GameVideoFilter)"], None),
                (9973, 90, "$LOCALIZE[31997]", ["ActivateWindow(GameStretchMode)"], None),
                (9974, 100, "$LOCALIZE[35227]", ["ActivateWindow(GameVideoRotation)"], None),
                (9976, 100, "$LOCALIZE[10038]", ["ActivateWindow(GameAdvancedSettings)"], None)]
    if kind == "video":
        L = LIVE_V
        return [(9963, 110, "$LOCALIZE[287]", ["ActivateWindow(OSDSubtitleSettings)"],
                 f"!{L} | VideoPlayer.HasSubtitles"),
                (9950, 160, "$LOCALIZE[31998]", ["ActivateWindow(SubtitleSearch)"], f"!{L}"),
                AUDIO,
                (9961, 70, "$LOCALIZE[291]", ["ActivateWindow(OSDVideoSettings)"], None),
                (9964, 110, "$LOCALIZE[298]", [f"Dialog.Close({name})", "ActivateWindow(VideoBookmarks)"], f"!{L}"),
                (9965, 60, "$LOCALIZE[29915]", [f"Dialog.Close({name})", "ActivateWindow(FullscreenInfo)"], None),
                (804, 60, "$LOCALIZE[33061]", ["PlayerControl(ShowVideoMenu)"], "VideoPlayer.HasMenu"),
                # the play queue (Kodi's own Playlist action opens the same window)
                (87, 100, "$LOCALIZE[559]", ["Dialog.Close(all,true)", "ActivateWindow(VideoPlaylist)"],
                 "Integer.IsGreater(Playlist.Length(video),1)"),
                *live_buttons(name, L),
                (9968, 100, "$LOCALIZE[10550]", [f"Dialog.Close({name})", "ActivateWindow(Teletext)"],
                 "VideoPlayer.HasTeletext + !VideoPlayer.HasMenu"),
                record_button(L),
                addon_button(L)]
    L = LIVE_M
    not_live = f"![{L} | MusicPartyMode.Enabled]"
    return [(9984, 130, "$LOCALIZE[191]", ["PlayerControl(Random)"], not_live, "Playlist.IsRandom"),
            (9985, 140, "$VAR[OSDRepeatLabelVar]", ["PlayerControl(Repeat)"], not_live),
            AUDIO,
            (87, 100, "$LOCALIZE[559]", ["Dialog.Close(all,true)", "ActivateWindow(MusicPlaylist)"],
             "Integer.IsGreater(Playlist.Length(music),0)"),
            # K-6: Kodi's visualisation chooser (GUIDialogMusicOSD.cpp
            # CONTROL_VIS_BUTTON 500: pick an add-on, or None, and reload)
            (500, 150, "$LOCALIZE[250]", [], None),
            *live_buttons(name, L),
            (9969, 120, "$LOCALIZE[31801]", [f"Dialog.Close({name})", "ActivateWindow(PVRRadioRDSInfo)"],
             f"{L} + RDS.HasRDS"),
            record_button(L),
            addon_button(L)]

def osd_window(name, kind="video"):
    up = seek_targets(kind) + [(None, "202")]
    T, H_ = SEEK_T, SEEK_H
    # a tap on the picture above the bar closes the bar and nothing else
    # (Estuary's "background close area"); never reached by the keyboard
    pre = (f'    <control type="button" id="9990">\n'
           f"      <left>0</left><top>0</top><width>{OSD_W}</width><bottom>{OSD_H}</bottom>\n"
           f"      <texturefocus />\n      <texturenofocus />\n      <label></label>\n"
           f"      <onclick>Dialog.Close({name})</onclick>\n"
           + navs("      ", up="602", down="602", left="602", right="602")
           + "    </control>\n")
    body = ""
    for gid in (200, 698) + ((699,) if kind != "video" else ()):
        # ids Kodi skins traditionally carry; empty here
        body += (f'      <control type="group" id="{gid}">\n'
                 f"        <left>0</left><top>0</top><width>1</width><height>1</height>\n      </control>\n")
    # play state on the right of the title bar, where the window boxes would
    # be: right of x 921, where Win_Title's title label stops (right 100), so
    # a long title never runs under it. chromesmall: "Buffering..." is 96 px
    # at Extra large.
    body += ("      <control type=\"label\">\n"
             "        <left>922</left><top>3</top><width>96</width><height>26</height>\n"
             "        <font>chromesmall</font><textcolor>titletext</textcolor>\n"
             "        <align>right</align><aligny>center</aligny>\n"
             "        <label>$VAR[OSDStateVar]</label>\n      </control>\n")
    if kind == "game":
        # V-24: Kodi opens the game menu at launch when no controller is
        # connected, with the game paused; say why. Kodi writes the
        # "Press ... to open the in-game menu" text into 1101 and lets Back
        # dismiss it first while it is visible (DialogGameOSDHelp.cpp).
        help_ = "System.GetBool(gamesgeneral.showosdhelp)"
        body += (f'      <control type="label" id="1101">\n'
                 f"        <left>12</left><top>{T}</top><width>500</width><height>{H_}</height>\n"
                 f"        <font>chromesmall</font><aligny>center</aligny>\n"
                 f"        <visible>{help_}</visible>\n      </control>\n"
                 f'      <control type="label">\n'
                 f"        <left>12</left><top>{T}</top><width>500</width><height>{H_}</height>\n"
                 f"        <font>chrome</font><aligny>center</aligny>\n"
                 f"        <label>$INFO[Player.Time]</label>\n"
                 f"        <visible>!{help_}</visible>\n      </control>\n"
                 f'      <control type="label">\n'
                 f"        <left>520</left><top>{T}</top><width>{OSD_W - 520 - 12}</width><height>{H_}</height>\n"
                 f"        <font>chromesmall</font><textcolor>textdim</textcolor>\n"
                 f"        <align>right</align><aligny>center</aligny>\n"
                 f"        <label>$LOCALIZE[35236]</label>\n      </control>\n")
    else:
        live = OSD_LIVE[kind]
        sl, sw = 112, OSD_W - 2 * 112
        body += (f'      <control type="label">\n'
                 f"        <left>8</left><top>{T}</top><width>96</width><height>{H_}</height>\n"
                 f"        <font>chrome</font><align>right</align><aligny>center</aligny>\n"
                 f"        <label>$INFO[Player.Time]</label>\n      </control>\n"
                 f'      <control type="label">\n'
                 f"        <left>{OSD_W - 104}</left><top>{T}</top><width>96</width><height>{H_}</height>\n"
                 f"        <font>chrome</font><aligny>center</aligny>\n"
                 f"        <label>$INFO[Player.Duration]</label>\n      </control>\n")
        # V-5: drag or tap to seek; live TV seeks the timeshift buffer
        nav = {"up": "202", "down": "201"}
        body += slider(9980, sl, T, sw, H_, "seek", "Player.Progress",
                       visible=f"Player.SeekEnabled + !{live}", nav=nav)
        body += slider(9981, sl, T, sw, H_, "pvr.seek", "PVR.TimeshiftProgressPlayPos",
                       visible=f"Player.SeekEnabled + {live}", nav=nav)
        body += (f'      <control type="progress">\n'
                 f"        <left>{sl}</left><top>{T + 8}</top><width>{sw}</width><height>{H_ - 16}</height>\n"
                 f"        <info>Player.Progress</info>\n"
                 f"        <visible>!Player.SeekEnabled</visible>\n      </control>\n")
    body += osd_transport(kind)
    if kind == "music":
        body += vis_presets()
    # V-2: mute and volume, by touch. Tap or drag the slider (fireOnDrag:
    # the volume follows the finger); not while the receiver decodes.
    left = [(VIS_IF, "203"), (None, "201")] if kind == "music" else "201"
    body += icon_radio(9982, "audio", TR_W, TR_H, ["Mute"], indent=6, size=24,
                       selected="Player.Muted", glyph_on="audio_muted", pos=(MUTE_L, TR_T),
                       nav={"up": up, "down": "202", "left": left, "right": "9983"},
                       hit=OSD_HIT)
    body += slider(9983, VOL_L, TR_T + 6, VOL_W, TR_H - 12, "volume", "Player.Volume",
                   enable="!Player.Passthrough",
                   nav={"up": up, "down": "202"})
    # V-3: Hide closes the bar only; playback carries on underneath
    body += (f'      <control type="button" id="9951">\n'
             f"        <left>{HIDE_L}</left><top>{TR_T}</top><width>{HIDE_W}</width><height>{TR_H}</height>\n"
             # 8 px to the volume slider and to the frame edge: 4 sideways
             + hitrect("        ", HIDE_L, TR_T, HIDE_W, TR_H, 4, OSD_HIT)
             + f"        <font>chromebold</font><label>$LOCALIZE[31800]</label>\n"
             f"        <onclick>Dialog.Close({name})</onclick>\n"
             + navs("        ", up=up, down="202", left="9983", right="201")
             + "      </control>\n")
    body += osd_buttons(202, TX_T, osd_rows(name, kind), "201",
                        seek_targets(kind) + [(None, "201")], onright="9951")
    title = "$INFO[Player.Title]" if kind == "game" else "$VAR[NowPlayingVar]"
    # V-23: a remote's OK must not re-press whatever was focused last (Stop)
    return dialog(name, OSD_W, OSD_H, body, default="602", icon="icons24/audio.png",
                  dim=False, heading=False, title=title, anchor="bottom",
                  default_always=True, pre=pre)


# ---- player overlays and the dialogs the OSD opens ------------------------
def tap_close(name, above, cid=9990, focus="9012"):
    """A transparent full-width button over the picture above a bottom panel:
    a tap there closes the dialog (Kodi would swallow it: a modal dialog only
    closes on a right click, GUIWindow.cpp OnMouseEvent)."""
    return (f'    <control type="button" id="{cid}">\n'
            f"      <left>0</left><top>0</top><width>{OSD_W}</width><bottom>{above}</bottom>\n"
            f"      <texturefocus />\n      <texturenofocus />\n      <label></label>\n"
            f"      <onclick>Dialog.Close({name})</onclick>\n"
            + navs("      ", up=focus, down=focus, left=focus, right=focus)
            + "    </control>\n")

def kv_rows(l, t, rows, keyw=156, valw=300, rowh=26, indent=6):
    """label: value lines, the key dimmed. rows: (key label, value label)."""
    sp = " " * indent
    s = ""
    for i, (k, v) in enumerate(rows):
        y = t + i * rowh
        s += (f'{sp}<control type="label">\n'
              f"{sp}  <left>{l}</left><top>{y}</top><width>{keyw}</width><height>{rowh}</height>\n"
              f"{sp}  <font>chromesmall</font><textcolor>textdim</textcolor><aligny>center</aligny>\n"
              f"{sp}  <label>{k}</label>\n{sp}</control>\n"
              f'{sp}<control type="label">\n'
              f"{sp}  <left>{l + keyw + 6}</left><top>{y}</top><width>{valw}</width><height>{rowh}</height>\n"
              f"{sp}  <font>chrome</font><aligny>center</aligny>\n"
              f"{sp}  <label>{v}</label>\n{sp}</control>\n")
    return s

def heading_label(l, t, w, label, indent=6):
    sp = " " * indent
    return (f'{sp}<control type="label">\n'
            f"{sp}  <left>{l}</left><top>{t}</top><width>{w}</width><height>26</height>\n"
            f"{sp}  <font>chromebold</font><aligny>center</aligny>\n"
            f"{sp}  <label>{label}</label>\n{sp}</control>\n")

def seek_bar():
    """V-6: Kodi never opens DialogSeekBar itself; it shows while its window
    <visible> conditions hold (CGUIDialog::UpdateVisibility; Kodi ANDs them,
    GUIWindow.cpp). A thin strip on the bottom edge, never together with the
    OSD bar or a dialog the OSD opened. 401/403 are filled by Kodi with the
    seek target (GUIDialogSeekBar.cpp FrameMove)."""
    over = ("videoosd", "musicosd", "sliderdialog", "pvrosdchannels", "pvrchannelguide",
            "fullscreeninfo", "playerprocessinfo", "videobookmarks", "osdvideosettings",
            "osdaudiosettings", "osdsubtitlesettings", "pvrradiordsinfo",
            "teletext", "subtitlesearch", "osdcmssettings")
    vis = ["[Window.IsActive(fullscreenvideo) | Window.IsActive(visualisation)]",
           "![" + " | ".join(f"Window.IsVisible({w})" for w in over) + "]",
           "Player.Seeking | Player.HasPerformedSeek(3) | [Player.Paused + !Player.Caching] | "
           "Player.Forwarding | Player.Rewinding | Player.ShowTime | !String.IsEmpty(Player.SeekNumeric)"]
    Hs = 44
    sl = 8 + 120 + 6 + 96 + 8
    sw = OSD_W - sl - 8 - 96 - 8
    s = H + "<window>\n" + "".join(f"  <visible>{v}</visible>\n" for v in vis)
    s += "  <zorder>3</zorder>\n  <controls>\n"
    s += (f"    <control type=\"group\">\n"
          f"      <left>0</left><bottom>0</bottom><width>{OSD_W}</width><height>{Hs}</height>\n"
          f"      <include content=\"Win_Frame\"><param name=\"width\" value=\"{OSD_W}\" />"
          f"<param name=\"height\" value=\"{Hs}\" /></include>\n"
          f"      <control type=\"label\">\n"
          f"        <left>12</left><top>0</top><width>120</width><height>{Hs}</height>\n"
          f"        <font>chromebold</font><aligny>center</aligny>\n"
          f"        <label>$VAR[OSDStateVar]</label>\n      </control>\n")
    for lab, v in (("$INFO[Player.SeekTime]", "Player.Seeking"),
                   ("$INFO[Player.SeekNumeric]", "!Player.Seeking + !String.IsEmpty(Player.SeekNumeric)"),
                   ("$INFO[Player.Time]", "!Player.Seeking + String.IsEmpty(Player.SeekNumeric)")):
        s += (f"      <control type=\"label\">\n"
              f"        <left>{8 + 120 + 6}</left><top>0</top><width>96</width><height>{Hs}</height>\n"
              f"        <font>chrome</font><align>right</align><aligny>center</aligny>\n"
              f"        <label>{lab}</label>\n        <visible>{v}</visible>\n      </control>\n")
    s += slider(401, sl, 8, sw, Hs - 16, None, None, visible="!VideoPlayer.Content(LiveTV)")
    s += slider(403, sl, 8, sw, Hs - 16, None, None,
                visible="VideoPlayer.Content(LiveTV)")
    s += (f"      <control type=\"label\">\n"
          f"        <left>{OSD_W - 8 - 96}</left><top>0</top><width>96</width><height>{Hs}</height>\n"
          f"        <font>chrome</font><aligny>center</aligny>\n"
          f"        <label>$INFO[Player.Duration]</label>\n      </control>\n")
    s += "    </control>\n  </controls>\n</window>\n"
    return s

def bookmarks_dialog():
    """V-8. GUIDialogVideoBookmarks.cpp: 2 create, 3 clear, 4 episode bookmark
    (Kodi enables it only for episodes), 11 the bookmarks and chapters (a tap
    jumps there; a long press offers Remove). Kodi sets none of the labels.
    Clear also wipes the resume point with no question asked (ClearBookmarks),
    so the visible Clear asks first: the first tap arms it, the second clicks
    the real 3. A bottom panel, so the picture being bookmarked stays in view."""
    W, Hh = OSD_W, 250
    armed = "String.IsEqual(Window(Home).Property(arthuros.clearbm),1)"
    # T-6: each button's hit rect covers half of the 4 px gap above and below
    body = well(8, 34, 244, Hh - 42, "panel_sunken_grey.png")
    body += (f'      <control type="grouplist" id="9000">\n'
             f"        <left>16</left><top>42</top><width>228</width><height>{Hh - 58}</height>\n"
             f"        <orientation>vertical</orientation><itemgap>4</itemgap>\n"
             f"        <onright>11</onright>\n"
             f'        <control type="button" id="2">\n'
             f"          <width>228</width><height>44</height>\n"
             f"          <hitrect x=\"0\" y=\"-2\" w=\"228\" h=\"48\" />\n"
             f"          <font>chrome</font><label>$LOCALIZE[294]</label>\n        </control>\n"
             f'        <control type="button" id="4">\n'
             f"          <width>228</width><height>44</height>\n"
             f"          <hitrect x=\"0\" y=\"-2\" w=\"228\" h=\"48\" />\n"
             f"          <font>chrome</font><label>$LOCALIZE[20406]</label>\n"
             f"          <visible>Control.IsEnabled(4)</visible>\n        </control>\n"
             f'        <control type="button" id="9993">\n'
             f"          <width>228</width><height>44</height>\n"
             f"          <hitrect x=\"0\" y=\"-2\" w=\"228\" h=\"48\" />\n"
             f"          <font>chrome</font><label>$VAR[BookmarkClearLabelVar]</label>\n"
             f"          <onclick condition=\"!{armed}\">SetProperty(arthuros.clearbm,1,home)</onclick>\n"
             f"          <onclick condition=\"{armed}\">ClearProperty(arthuros.clearbm,home)</onclick>\n"
             f"          <onclick condition=\"{armed}\">SendClick(videobookmarks,3)</onclick>\n"
             f"        </control>\n"
             f'        <control type="button" id="9994">\n'
             f"          <width>228</width><height>44</height>\n"
             f"          <hitrect x=\"0\" y=\"-2\" w=\"228\" h=\"48\" />\n"
             f"          <font>chrome</font><label>$LOCALIZE[106]</label>\n"
             f"          <onclick>ClearProperty(arthuros.clearbm,home)</onclick>\n"
             f"          <onclick>SetFocus(9993)</onclick>\n"
             f"          <visible>{armed}</visible>\n        </control>\n"
             # no title-bar boxes over playback (BOXES), so Close lives here;
             # while Clear is armed, Cancel takes its place
             f'        <control type="button" id="9995">\n'
             f"          <width>228</width><height>44</height>\n"
             f"          <hitrect x=\"0\" y=\"-2\" w=\"228\" h=\"48\" />\n"
             f"          <font>chrome</font><label>$LOCALIZE[15067]</label>\n"
             f"          <onclick>Dialog.Close(VideoBookmarks)</onclick>\n"
             f"          <visible>!{armed}</visible>\n        </control>\n"
             f"      </control>\n")
    # the real Clear: only ever clicked by 9993's second tap
    body += ('      <control type="button" id="3">\n'
             "        <left>-3000</left><top>0</top><width>10</width><height>10</height>\n"
             "        <label></label>\n      </control>\n")
    pw = W - 260 - 8
    body += well(260, 34, pw, Hh - 42, "panel_sunken.png")
    body += (f'      <control type="label">\n'
             f"        <left>276</left><top>34</top><width>{pw - 32}</width><height>{Hh - 42}</height>\n"
             f"        <font>chrome</font><textcolor>textdim</textcolor><align>center</align><aligny>center</aligny>\n"
             f"        <label>$LOCALIZE[31802]</label>\n"
             f"        <visible>Integer.IsEqual(Container(11).NumItems,0) + !{armed}</visible>\n      </control>\n"
             f'      <control type="label">\n'
             f"        <left>276</left><top>34</top><width>{pw - 32}</width><height>{Hh - 42}</height>\n"
             f"        <font>chromebold</font><textcolor>marked</textcolor><align>center</align><aligny>center</aligny>\n"
             f"        <label>$LOCALIZE[31803]</label>\n"
             f"        <visible>{armed}</visible>\n      </control>\n")
    iw, ih = 156, Hh - 54
    item = lambda focus: (
        (f'          <control type="image">\n'
         f"            <left>0</left><top>0</top><width>{iw - 6}</width><height>{ih}</height>\n"
         f'            <texture border="2" colordiffuse="select">select_bevel.png</texture>\n'
         f"          </control>\n" if focus else "")
        + f'          <control type="image">\n'
          f"            <left>6</left><top>6</top><width>{iw - 18}</width><height>{ih - 64}</height>\n"
          f'            <texture fallback="DefaultVideo.png">$INFO[ListItem.Art(thumb)]</texture>\n'
          f"            <aspectratio>keep</aspectratio>\n          </control>\n"
          f'          <control type="label">\n'
          f"            <left>6</left><top>{ih - 54}</top><width>{iw - 18}</width><height>26</height>\n"
          f"            <font>chromebold</font><align>center</align>"
          f"<textcolor>{'textinv' if focus else 'text'}</textcolor>\n"
          f"            <label>$INFO[ListItem.Label]</label>\n          </control>\n"
          f'          <control type="label">\n'
          f"            <left>6</left><top>{ih - 28}</top><width>{iw - 18}</width><height>22</height>\n"
          f"            <font>chromesmall</font><align>center</align>"
          f"<textcolor>{'textinv' if focus else 'textdim'}</textcolor>\n"
          f"            <label>$INFO[ListItem.Label2]</label>\n          </control>\n")
    body += (f'      <control type="panel" id="11">\n'
             f"        <left>266</left><top>40</top><width>{pw - 12}</width><height>{ih + 2}</height>\n"
             f"        <orientation>horizontal</orientation>\n"
             f"        <onleft>9000</onleft><onup>9000</onup><ondown>9000</ondown>\n"
             f"        <visible>!{armed}</visible>\n"
             f'        <itemlayout width="{iw}" height="{ih}">\n{item(False)}        </itemlayout>\n'
             f'        <focusedlayout width="{iw}" height="{ih}">\n{item(True)}        </focusedlayout>\n'
             f"      </control>\n")
    s = dialog("VideoOSDBookmarks", W, Hh, body, default="2", icon="icons24/bookmarks.png",
               dim=False, heading=False, title="$LOCALIZE[298]", anchor="bottom",
               pre=tap_close("VideoBookmarks", Hh, focus="2"))
    # a half-done Clear never survives the dialog closing
    return s.replace("<window>\n", "<window>\n  <onload>ClearProperty(arthuros.clearbm,home)</onload>\n", 1)

def fullscreen_info():
    """V-14. CGUIDialogFullScreenInfo writes nothing (it only closes itself on
    Info), so everything comes from infolabels. Bottom panel, picture kept."""
    W, Hh = OSD_W, 238
    body = ('      <control type="image">\n'
            "        <left>8</left><top>34</top><width>120</width><height>196</height>\n"
            '        <texture border="2">panel_raised.png</texture>\n      </control>\n'
            '      <control type="image">\n'
            "        <left>14</left><top>40</top><width>108</width><height>184</height>\n"
            '        <texture fallback="DefaultVideo.png">$INFO[Player.Art(thumb)]</texture>\n'
            "        <aspectratio>keep</aspectratio>\n      </control>\n"
            '      <control type="label">\n'
            "        <left>136</left><top>34</top><width>880</width><height>26</height>\n"
            "        <font>chrome</font><textcolor>textdim</textcolor><aligny>center</aligny>\n"
            "        <label>$INFO[VideoPlayer.ChannelName,,   ]$INFO[VideoPlayer.Year,,   ]$INFO[VideoPlayer.Genre]</label>\n"
            "      </control>\n")
    body += well(136, 62, 880, 118, "panel_sunken.png")
    body += ('      <control type="textbox">\n'
             "        <left>144</left><top>68</top><width>842</width><height>106</height>\n"
             "        <font>small</font><pagecontrol>61</pagecontrol>\n"
             "        <label>$INFO[VideoPlayer.Plot]</label>\n      </control>\n"
             '      <control type="scrollbar" id="61">\n'
             "        <left>992</left><top>65</top><width>20</width><height>112</height>\n"
             "        <onleft>9013</onleft><onright>9013</onright><ondown>9013</ondown><onup>9013</onup>\n"
             "      </control>\n"
             '      <control type="label">\n'
             "        <left>136</left><top>186</top><width>300</width><height>44</height>\n"
             "        <font>chrome</font><aligny>center</aligny>\n"
             "        <label>$INFO[Player.Time] / $INFO[Player.Duration]</label>\n      </control>\n")
    body += osd_buttons(9013, 186, [
        (9011, 150, "$LOCALIZE[31806]", ["Dialog.Close(FullscreenInfo)", "ActivateWindow(PlayerProcessInfo)"], None),
        (9012, 110, "$LOCALIZE[15067]", ["Dialog.Close(FullscreenInfo)"], None),
    ], "61", "61", left=W - 8 - 266, width=266)
    return dialog("DialogFullScreenInfo", W, Hh, body, default="9012", default_always=True,
                  icon="icons24/info.png", dim=False, heading=False,
                  title="$INFO[VideoPlayer.Title]", anchor="bottom",
                  pre=tap_close("FullscreenInfo", Hh))

def process_info():
    """V-14. CGUIDialogPlayerProcessInfo writes nothing either: decoder, picture
    and audio details are Player.Process(...) infolabels."""
    W, Hh = OSD_W, 242
    cw = (W - 24) // 2
    body = ""
    for x, head, rows in (
        (8, "$LOCALIZE[291]", [
            ("$LOCALIZE[31804]", "$INFO[Player.Process(videodecoder)]"),
            ("$LOCALIZE[31805]", "$INFO[Player.Process(pixformat)]"),
            ("$LOCALIZE[169]", "$INFO[Player.Process(videowidth)]$INFO[Player.Process(videoheight),x,]"
                               "$INFO[Player.Process(videofps), @ , fps]$INFO[Player.Process(videodar),  (,)]"),
            ("$LOCALIZE[16038]", "$INFO[Player.Process(deintmethod)]")]),
        (16 + cw, "$LOCALIZE[292]", [
            ("$LOCALIZE[31804]", "$INFO[Player.Process(audiodecoder)]"),
            ("$LOCALIZE[21444]", "$INFO[Player.Process(audiochannels)]"),
            ("$LOCALIZE[613]", "$INFO[Player.Process(audiosamplerate),, Hz]"),
            ("$LOCALIZE[612]", "$INFO[Player.Process(audiobitspersample)]")])):
        body += well(x, 34, cw, 148, "panel_sunken_grey.png")
        body += heading_label(x + 10, 38, cw - 20, head)
        body += kv_rows(x + 10, 66, rows, keyw=156, valw=cw - 20 - 162)
    body += ('      <control type="label">\n'
             "        <left>12</left><top>190</top><width>860</width><height>44</height>\n"
             "        <font>chrome</font><aligny>center</aligny>\n"
             "        <label>$LOCALIZE[140] $INFO[System.CpuUsage]     $LOCALIZE[439]: "
             "$INFO[Player.CacheLevel,,%]     $INFO[System.ScreenResolution]</label>\n      </control>\n"
             '      <control type="button" id="9012">\n'
             f"        <left>{W - 8 - 110}</left><top>190</top><width>110</width><height>44</height>\n"
             "        <font>chrome</font><label>$LOCALIZE[15067]</label>\n"
             "        <onclick>Dialog.Close(PlayerProcessInfo)</onclick>\n      </control>\n")
    return dialog("DialogPlayerProcessInfo", W, Hh, body, default="9012", default_always=True,
                  icon="icons24/process_info.png", dim=False, heading=False,
                  title="$LOCALIZE[10116]", anchor="bottom",
                  pre=tap_close("PlayerProcessInfo", Hh))

def rds_info():
    """V-14. GUIDialogPVRRadioRDSInfo.cpp: 10 close, 21 a spin of the info
    pages the station sends (news, sport, weather...), 22 the page text, 70
    the group holding them (Kodi shows it only when a page exists). The rest
    is RDS.* infolabels."""
    W, Hh = 900, 452
    cw = (W - 24) // 2
    body = ""
    for x, head, rows in (
        (8, "$LOCALIZE[179]", [
            ("$LOCALIZE[556]", "$INFO[RDS.Title]"), ("$LOCALIZE[557]", "$INFO[RDS.Artist]"),
            ("$LOCALIZE[29901]", "$INFO[RDS.Band]"), ("$LOCALIZE[558]", "$INFO[RDS.Album]"),
            ("$LOCALIZE[29903]", "$INFO[RDS.Composer]"), ("$LOCALIZE[29905]", "$INFO[RDS.Conductor]")]),
        (16 + cw, "$LOCALIZE[29908]", [
            ("$LOCALIZE[19148]", "$INFO[RDS.ProgStation]"), ("$LOCALIZE[19030]", "$INFO[RDS.ProgNow]"),
            ("$LOCALIZE[19031]", "$INFO[RDS.ProgNext]"), ("$LOCALIZE[29906]", "$INFO[RDS.ProgHost]"),
            ("$LOCALIZE[29902]", "$INFO[RDS.ProgStyle]"), ("$LOCALIZE[29914]", "$INFO[RDS.ProgHomepage]")])):
        body += well(x, 34, cw, 184, "panel_sunken_grey.png")
        body += heading_label(x + 10, 38, cw - 20, head)
        body += kv_rows(x + 10, 66, rows, keyw=110, valw=cw - 20 - 116, rowh=24)
    body += well(8, 224, W - 16, 112, "panel_sunken.png")
    body += heading_label(18, 228, W - 36, "$LOCALIZE[31801]")
    for i in range(4):
        body += ('      <control type="label">\n'
                 f"        <left>18</left><top>{254 + i * 20}</top><width>{W - 36}</width><height>20</height>\n"
                 f"        <font>chromesmall</font><label>$INFO[RDS.GetLine({i})]</label>\n      </control>\n")
    body += ('      <control type="group" id="70">\n'
             f"        <left>8</left><top>342</top><width>{W - 16}</width><height>56</height>\n"
             '        <control type="spincontrol" id="21">\n'
             "          <left>0</left><top>8</top><width>220</width><height>40</height>\n"
             "          <font>chrome</font>\n"
             "          <onright>10</onright><onleft>10</onleft><onup>10</onup><ondown>10</ondown>\n"
             "        </control>\n"
             '        <control type="textbox" id="22">\n'
             f"          <left>228</left><top>4</top><width>{W - 16 - 236}</width><height>48</height>\n"
             "          <font>small</font>\n        </control>\n"
             "      </control>\n"
             '      <control type="button" id="10">\n'
             f"        <left>{W - 8 - 110}</left><top>404</top><width>110</width><height>40</height>\n"
             "        <font>chrome</font><label>$LOCALIZE[15067]</label>\n"
             "        <onup>21</onup><ondown>21</ondown><onleft>21</onleft><onright>21</onright>\n"
             "      </control>\n")
    return dialog("DialogPVRRadioRDSInfo", W, Hh, body, default="10", default_always=True,
                  icon="icons24/rds.png", dim=False, heading=False, title="$LOCALIZE[29900]")


# ====================================================== info dialogs
INFO_XLC = "[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]"

def info_sb_width(indent=8):
    """A scrollbar width that grows for a finger (Media_SBWidth* live in
    Includes_Media.xml)."""
    sp = " " * indent
    return (f'{sp}<include content="Media_SBWidth_XL" condition="{INFO_XLC}" />\n'
            f'{sp}<include content="Media_SBWidth" condition="!{INFO_XLC}" />\n')

def info_label(sid):
    """INFO_BUTTONS label: a Kodi/skin string id, a ready-made $VAR/$INFO
    label, or None (Kodi writes the label itself)."""
    if sid is None:
        return ""
    if isinstance(sid, str):
        return f"<label>{sid}</label>"
    return f"<label>$LOCALIZE[{sid}]</label>"

def info_dialog(name, ids=None):
    music = name == "DialogMusicInfo"
    # art: Kodi gives albums and artists 'thumb', never 'poster'; episodes
    # and add-on videos often have neither (VideoInfoArtVar falls back to
    # the show's poster, the thumb, then Kodi's own icon)
    art, fb = (("$VAR[MusicInfoArtVar]", "DefaultAlbumCover.png") if music
               else ("$VAR[VideoInfoArtVar]", "DefaultVideo.png"))
    rows = INFO_BUTTONS[name]
    chunks = [rows[i:i + 4] for i in range(0, len(rows), 4)]
    gids = [9001 + i for i in range(len(chunks))]
    body  = well(10, 36, 500, 260, "panel_sunken_grey.png")
    body += f"""      <control type="image">
        <left>20</left><top>46</top><width>150</width><height>220</height>
        <texture border="2">panel_raised.png</texture>
      </control>
      <control type="image">
        <left>26</left><top>52</top><width>138</width><height>208</height>
        <texture fallback="{fb}">{art}</texture>
        <aspectratio>keep</aspectratio>
      </control>
      <control type="label">
        <left>184</left><top>46</top><width>316</width><height>52</height>
        <font>bigbold</font><wrapmultiline>true</wrapmultiline>
        <label>$VAR[InfoTitleVar]</label>
      </control>
      <control type="label">
        <left>184</left><top>104</top><width>316</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$INFO[ListItem.Year]  $INFO[ListItem.Duration]</label>
      </control>
      <control type="label">
        <left>184</left><top>128</top><width>316</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$INFO[ListItem.Genre]</label>
      </control>
      <control type="label">
        <left>184</left><top>152</top><width>316</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$INFO[ListItem.Rating]  $INFO[ListItem.Studio]$INFO[ListItem.Artist]</label>
      </control>
"""
    # the plot: a textbox scrolls only through a pagecontrol, so give it a
    # scrollbar a finger can drag; it still scrolls by itself, except while
    # the scrollbar has the focus
    body += well(520, 36, 370, 260, "panel_sunken.png")
    body += f"""      <control type="textbox">
        <left>528</left><top>44</top><width>322</width><height>244</height>
        <font>small</font>
        <pagecontrol>61</pagecontrol>
        <autoscroll delay="6000" time="4000" repeat="8000">!Control.HasFocus(61)</autoscroll>
        <label>$INFO[ListItem.Plot]$INFO[ListItem.Comment]</label>
      </control>
      <control type="scrollbar" id="61">
        <right>14</right><top>44</top><height>244</height>
{info_sb_width()}        <onup>{gids[-1]}</onup><ondown>50</ondown>
        <onleft>50</onleft><onright>50</onright>
      </control>
"""
    body += well(10, 304, 880, 120, "panel_sunken.png")
    if music:
        # album: its songs; artist: the discography. Full-width rows so a
        # title is not cut off after a few letters (GUIDialogMusicInfo binds
        # either list to 50; any container type works)
        def mrow(tag, focused):
            col = "textinv" if focused else "text"
            dim = "textinv" if focused else "textdim"
            sel = "<selectedcolor>textinv</selectedcolor>" if focused else ""
            bar = ("""          <control type="image">
            <left>0</left><top>0</top><width>838</width><height>26</height>
            <texture colordiffuse="select">fill.png</texture>
          </control>
""" if focused else "")
            return f"""        <{tag} height="26" width="838">
{bar}          <control type="label">
            <left>8</left><top>0</top><width>720</width><height>26</height>
            <font>{'bold' if focused else 'normal'}</font><textcolor>{col}</textcolor>{sel}
            <aligny>center</aligny>
            <label>$INFO[ListItem.TrackNumber,,.  ]$INFO[ListItem.Label]</label>
          </control>
          <control type="label">
            <left>0</left><top>0</top><width>830</width><height>26</height>
            <font>small</font><textcolor>{dim}</textcolor>{sel}
            <align>right</align><aligny>center</aligny>
            <label>$INFO[ListItem.Label2]</label>
          </control>
        </{tag}>
"""
        body += f"""      <control type="list" id="50">
        <left>16</left><top>310</top><width>838</width><height>108</height>
        <onup>61</onup><ondown>9001</ondown><onright>62</onright>
        <pagecontrol>62</pagecontrol>
        <scrolltime tween="linear">0</scrolltime>
{mrow("itemlayout", False)}{mrow("focusedlayout", True)}      </control>
      <control type="scrollbar" id="62">
        <right>14</right><top>310</top><height>108</height>
{info_sb_width()}        <onleft>50</onleft><onright>50</onright>
        <onup>61</onup><ondown>9001</ondown>
      </control>
"""
    else:
        body += """      <control type="panel" id="50">
        <left>16</left><top>310</top><width>868</width><height>108</height>
        <onup>61</onup><ondown>9001</ondown>
        <itemlayout height="108" width="90">
          <control type="image">
            <left>4</left><top>2</top><width>80</width><height>80</height>
            <texture fallback="DefaultActor.png">$INFO[ListItem.Icon]</texture>
            <aspectratio>keep</aspectratio>
          </control>
          <control type="label">
            <left>0</left><top>84</top><width>88</width><height>22</height>
            <font>tiny</font><align>center</align>
            <label>$INFO[ListItem.Label]</label>
          </control>
        </itemlayout>
        <focusedlayout height="108" width="90">
          <control type="image">
            <left>0</left><top>0</top><width>88</width><height>106</height>
            <texture border="4">focus_ring.png</texture>
          </control>
          <control type="image">
            <left>4</left><top>2</top><width>80</width><height>80</height>
            <texture fallback="DefaultActor.png">$INFO[ListItem.Icon]</texture>
            <aspectratio>keep</aspectratio>
          </control>
          <control type="label">
            <left>0</left><top>84</top><width>88</width><height>22</height>
            <font>tiny</font><align>center</align>
            <label>$INFO[ListItem.Label]</label>
          </control>
        </focusedlayout>
      </control>
"""
    # Buttons by Kodi's own ids (GUIDialogVideoInfo.cpp, GUIDialogMusicInfo.cpp,
    # GUIDialogPVRGuideInfo.cpp / RecordingInfo.cpp). Kodi hides some itself;
    # the rest carry a <visible> so buttons that do nothing never show.
    # Hidden ones drop out of the grouplist row; a row whose buttons are all
    # conditional is hidden with them, and Up/Down pass through a hidden row
    # (CGUIWindow::OnMove follows the hidden control's own navigation).
    # Button 5 (Cast/Plot toggle) is left out on purpose in video info:
    # without it Kodi lets the skin keep the plot and the cast list both on
    # screen.
    def row(gid, items, top, up, down):
        conds = list(dict.fromkeys(v[0] if v else None for _, _, *v in items))
        rowvis = ("" if None in conds else
                  "        <visible>" + " | ".join(f"[{c}]" for c in conds) + "</visible>\n")
        s = (f"      <control type=\"grouplist\" id=\"{gid}\">\n"
             f"        <left>13</left><top>{top}</top><width>874</width><height>30</height>\n"
             "        <orientation>horizontal</orientation><align>center</align><itemgap>6</itemgap>\n"
             f"        <onup>{up}</onup><ondown>{down}</ondown>\n" + rowvis)
        for (cid, sid, *vis) in items:
            v = f"<visible>{vis[0]}</visible>" if vis else ""
            # chrome font: these rows stay one line high in every fontset
            s += (f"        <control type=\"button\" id=\"{cid}\"><width>212</width><height>30</height>"
                  f"<font>chrome</font><textoffsetx>4</textoffsetx><align>center</align>"
                  f"{info_label(sid)}{v}</control>\n")
        return s + "      </control>\n"
    for i, items in enumerate(chunks):
        up = gids[i - 1] if i else 50
        down = gids[i + 1] if i + 1 < len(gids) else 61
        body += row(gids[i], items, 434 + 34 * i, up, down)
    ids = {k: v for k, v in (ids or {}).items() if int(k) < 100 or int(k) == 140}
    body += stubs(ids, {1, 50, 61, 62} | {c for c, *_ in rows})
    # default focus: the first button row, never one button. Kodi hides
    # buttons itself (10 in recording info via <visible>, 10 in guide info,
    # 8 for artist info); a hidden default control leaves the dialog with
    # nothing focused and a remote cannot reach any button. A grouplist
    # passes the focus to its first child that can take it
    # (CGUIControlGroup GUI_MSG_SETFOCUS -> GetFirstFocusableControl).
    return dialog(name, 900, 440 + 34 * len(chunks), body, default=str(gids[0]),
                  default_always=True,
                  icon="icons24/movies.png", title="$VAR[InfoTitleVar]")

# (id, label[, visible]): label is a string id, a ready-made label, or None
# when Kodi writes the label itself. Kodi only enables/disables 6, 7, 9, 10
# and 12 in video info (GUIDialogVideoInfo::Update); 11, 13, 14 and 15 are
# always enabled and must be hidden by the skin when they do not apply
# (as Estuary does).
PVR_GUIDE = "Window.IsActive(PVRGuideInfo)"
INFO_BUTTONS = {
 "DialogVideoInfo": [(8, "$VAR[InfoPlayLabelVar]"), (9, 13404, "Control.IsEnabled(9)"),
                     (6, 184, "Control.IsEnabled(6)"), (7, 38023, "Control.IsEnabled(7)"),
                     (11, 20410, "!String.IsEmpty(ListItem.Trailer)"),
                     (13, 20339, "!String.IsEmpty(ListItem.Director)"),
                     (14, 40001, "String.IsEqual(ListItem.DBType,movie)"),
                     (15, 40211, "String.IsEqual(ListItem.DBType,movie)"),
                     (10, 13511, "Control.IsEnabled(10)"), (12, 20413, "Control.IsEnabled(12)")],
 "DialogMusicInfo": [(8, None), (6, None), (7, None), (10, None), (12, None)],
 # DialogPVRInfo.xml is shared by the guide and the recording info dialog;
 # the recording dialog acts only on 4, 7 and 8, the guide dialog labels 6
 # (Record / Delete timer...) and hides what does not apply
 "DialogPVRInfo":   [(10, 19190, PVR_GUIDE), (8, 19687), (5, 19000, PVR_GUIDE),
                     (6, 264, PVR_GUIDE), (9, 19061, PVR_GUIDE), (11, 826, PVR_GUIDE),
                     (4, 19003), (7, 186)],
}

def addon_info_dialog():
    """Kodi hides whichever of these do not apply, but every one of them has to
    EXIST and be visible, or the add-on has no Open / Install / Configure
    button at all. Ids are Kodi's: 6 install, 7 enable, 8 update, 9 settings,
    10 dependencies, 12 select/open, 13 auto-update, 14 versions."""
    body  = well(10, 36, 880, 170, "panel_sunken_grey.png")
    body += """      <control type="image">
        <left>20</left><top>46</top><width>150</width><height>150</height>
        <texture border="2">panel_raised.png</texture>
      </control>
      <control type="image">
        <left>26</left><top>52</top><width>138</width><height>138</height>
        <texture fallback="DefaultAddon.png">$INFO[ListItem.Art(thumb)]</texture>
        <aspectratio>keep</aspectratio>
      </control>
      <control type="label">
        <left>186</left><top>46</top><width>690</width><height>30</height>
        <font>bigbold</font>
        <label>$INFO[ListItem.AddonName]</label>
      </control>
      <control type="label">
        <left>186</left><top>80</top><width>690</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$INFO[ListItem.AddonVersion]$INFO[ListItem.AddonCreator,  -  ]</label>
      </control>
      <control type="label">
        <left>186</left><top>104</top><width>690</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$INFO[ListItem.AddonSummary]</label>
      </control>
      <control type="label">
        <left>186</left><top>128</top><width>690</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$INFO[ListItem.AddonOrigin]$INFO[ListItem.AddonLastUpdated,  -  ]</label>
      </control>
      <control type="label">
        <left>186</left><top>160</top><width>690</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$INFO[ListItem.AddonType]$INFO[ListItem.AddonSize,  -  ]$INFO[ListItem.AddonLifecycleDesc,  -  ]$INFO[ListItem.AddonBroken,  -  ]</label>
      </control>
"""
    body += well(10, 212, 880, 150, "panel_sunken.png")
    # description, disclaimer and news: a textbox scrolls only through a
    # pagecontrol, so a scrollbar a finger can drag (it still scrolls by
    # itself, except while the scrollbar has the focus)
    body += """      <control type="textbox">
        <left>18</left><top>220</top><width>830</width><height>134</height>
        <font>small</font>
        <pagecontrol>61</pagecontrol>
        <autoscroll delay="6000" time="2500" repeat="6000">!Control.HasFocus(61)</autoscroll>
        <!-- Kodi 21 exposes add-on details as ListItem.Addon* info labels;
             the old Addon.* item properties are always empty. -->
        <label>$INFO[ListItem.AddonDescription]$INFO[ListItem.AddonDisclaimer,[CR][CR]]$INFO[ListItem.AddonNews,[CR][CR]]</label>
      </control>
      <control type="scrollbar" id="61">
        <right>14</right><top>220</top><height>134</height>
""" + info_sb_width() + """        <onup>9</onup><ondown>12</ondown>
        <onleft>12</onleft><onright>12</onright>
      </control>
      <control type="grouplist">
        <left>13</left><top>370</top><width>874</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>6</itemgap>
        <onup>61</onup><ondown>9</ondown>
        <control type="button" id="12"><width>210</width><height>32</height><label>$LOCALIZE[502]</label></control>
        <control type="button" id="6"><width>210</width><height>32</height><label>$LOCALIZE[24038]</label></control>
        <control type="button" id="7"><width>210</width><height>32</height><label>$LOCALIZE[24022]</label></control>
        <control type="button" id="8"><width>210</width><height>32</height><label>$LOCALIZE[24138]</label></control>
      </control>
      <control type="grouplist">
        <left>13</left><top>408</top><width>874</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>6</itemgap>
        <onup>12</onup><ondown>61</ondown>
        <control type="button" id="9"><width>210</width><height>32</height><label>$LOCALIZE[24020]</label></control>
        <control type="button" id="14"><width>210</width><height>32</height><label>$LOCALIZE[24069]</label></control>
        <control type="button" id="10"><width>210</width><height>32</height><label>$LOCALIZE[39024]</label></control>
        <control type="radiobutton" id="13"><width>210</width><height>32</height><label>$LOCALIZE[21340]</label></control>
      </control>
      <control type="panel" id="50">
        <left>-3000</left><top>0</top><width>200</width><height>100</height>
        <itemlayout height="20" width="100"/><focusedlayout height="20" width="100"/>
      </control>
      <control type="radiobutton" id="20">
        <left>-3000</left><top>0</top><width>200</width><height>24</height>
      </control>
"""
    return dialog("DialogAddonInfo", 900, 452, body, default="12",
                  icon="icons24/addons.png", title="$INFO[ListItem.AddonName]")

# ====================================================== stubs
STUB_EXTRA = {
 "list":   "<itemlayout height=\"20\" width=\"100\"/><focusedlayout height=\"20\" width=\"100\"/>",
 "panel":  "<itemlayout height=\"20\" width=\"100\"/><focusedlayout height=\"20\" width=\"100\"/>",
 "fixedlist": "<itemlayout height=\"20\" width=\"100\"/><focusedlayout height=\"20\" width=\"100\"/>",
 "wraplist":  "<itemlayout height=\"20\" width=\"100\"/><focusedlayout height=\"20\" width=\"100\"/>",
 # CGUIMoverControl / CGUIResizeControl draw nothing but these two textures
 "mover":  ("<texturefocus colordiffuse=\"select\">fill.png</texturefocus><texturenofocus>fill.png</texturenofocus>"
            "<movingspeed acceleration=\"180\" maxvelocity=\"300\" resettimeout=\"200\" delta=\"1\">"
            "<eventconfig type=\"up\" /><eventconfig type=\"down\" /><eventconfig type=\"left\" />"
            "<eventconfig type=\"right\" /></movingspeed>"),
 "resize": ("<texturefocus colordiffuse=\"select\">fill.png</texturefocus><texturenofocus>fill.png</texturenofocus>"
            "<movingspeed acceleration=\"140\" maxvelocity=\"300\" resettimeout=\"180\" delta=\"1\">"
            "<eventconfig type=\"left\" /><eventconfig type=\"right\" /></movingspeed>"),
}
def stubs(ids, placed):
    ids = {int(k): v for k, v in ids.items()}
    """Every id Kodi may talk to must exist with the right type. Anything the
    layout did not place gets an off-screen stub so SET_CONTROL_* still lands."""
    out = ""
    placed = {int(p) for p in placed}
    for cid, ct in sorted(ids.items()):
        if cid in placed: continue
        if ct in ("group",):
            out += f'      <control type="group" id="{cid}"><left>-3000</left><top>0</top><width>10</width><height>10</height></control>\n'
            continue
        extra = STUB_EXTRA.get(ct, "")
        out += (f'      <control type="{ct}" id="{cid}">\n'
                f'        <left>-3000</left><top>0</top><width>200</width><height>24</height>\n'
                + (f"        {extra}\n" if extra else "") +
                f'      </control>\n')
    return out

# ====================================================== keypads
def keyboard_window(h=600):
    """h: the layout's screen height. 600 is xml/; tallpass.py calls this with
    768 for xml768/, where a logical pixel is also physically larger (9.7"
    4:3 against 7" 16:9), so the keys grow from 40 to 56 px: the only way to
    type on a touch-only box. Same ids, order and navigation in both."""
    tall = h >= 768
    key, pitch = (56, 60) if tall else (40, 44)       # letter keys
    mod, act = (44, 44) if tall else (36, 34)          # Shift/... row, Done/... row
    ew = 54 if tall else 46                           # the text field's well
    rows = [range(100,113), range(120,133), range(140,153), range(160,173)]
    body  = well(10, 36, 880, ew, "panel_sunken.png")
    # Kodi writes the heading into label 311 (GUIDialogKeyboardGeneric.cpp
    # CTL_LABEL_HEADING), never into id 1, so 311 sits on the title bar.
    body += f"""      <control type="label" id="311">
        <left>29</left><top>3</top><width>770</width><height>26</height>
        <font>chromebold</font><textcolor>titletext</textcolor>
        <align>left</align><aligny>center</aligny>
      </control>
      <control type="edit" id="312">
        <left>16</left><top>42</top><width>868</width><height>{ew - 12}</height>
        <font>big</font>
      </control>
      <control type="label" id="313"><left>-3000</left><top>0</top><width>200</width><height>24</height></control>
      <control type="label" id="314"><left>-3000</left><top>0</top><width>200</width><height>24</height></control>
"""
    top = 36 + ew + 10
    for r, ids in enumerate(rows):
        body += f"""      <control type="grouplist">
        <left>14</left><top>{top + r*pitch}</top><width>876</width><height>{key}</height>
        <orientation>horizontal</orientation><itemgap>4</itemgap>
"""
        for cid in ids:
            body += f"""        <control type="button" id="{cid}">
          <width>62</width><height>{key}</height>
          <font>big</font><align>center</align><textoffsetx>0</textoffsetx>
        </control>
"""
        body += "      </control>\n"
    modrow = top + 4*pitch
    actrow = modrow + mod + 6
    body += f"""      <control type="grouplist">
        <left>14</left><top>{modrow}</top><width>876</width><height>{mod}</height>
        <orientation>horizontal</orientation><itemgap>4</itemgap>
        <control type="radiobutton" id="302"><width>104</width><height>{mod}</height><font>chromebold</font><textoffsetx>4</textoffsetx><label>$LOCALIZE[20178]</label></control>
        <control type="radiobutton" id="303"><width>136</width><height>{mod}</height><font>chromebold</font><textoffsetx>4</textoffsetx><label>$LOCALIZE[20179]</label></control>
        <control type="radiobutton" id="304"><width>118</width><height>{mod}</height><font>chromebold</font><textoffsetx>4</textoffsetx><label>$LOCALIZE[20180]</label></control>
        <control type="button" id="32"><width>160</width><height>{mod}</height><label>$LOCALIZE[31912]</label></control>
        <control type="button" id="8"><width>96</width><height>{mod}</height><label>&lt;-</label></control>
        <control type="button" id="305"><width>56</width><height>{mod}</height><label>&lt;</label></control>
        <control type="button" id="306"><width>56</width><height>{mod}</height><label>&gt;</label></control>
      </control>
      <control type="grouplist">
        <left>14</left><top>{actrow}</top><width>876</width><height>{act}</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>8</itemgap>
        <control type="button" id="300"><width>170</width><height>{act}</height><label>$LOCALIZE[20177]</label></control>
        <control type="button" id="301"><width>170</width><height>{act}</height><label>$LOCALIZE[222]</label></control>
        <control type="button" id="308"><width>170</width><height>{act}</height><label>$LOCALIZE[192]</label></control>
        <control type="button" id="309"><width>170</width><height>{act}</height><label>$LOCALIZE[31917]</label></control>
        <control type="button" id="310"><width>120</width><height>{act}</height><label>$LOCALIZE[31918]</label></control>
      </control>
      <control type="button" id="307"><left>-3000</left><top>0</top><width>100</width><height>30</height></control>
"""
    return dialog("DialogKeyboard", 900, actrow + act + 10, body, default="300",
                  icon="icons24/file.png", heading=False)

def numeric_window():
    body  = well(10, 36, 340, 44, "panel_sunken.png")
    body += """      <control type="label" id="4">
        <left>18</left><top>40</top><width>324</width><height>36</height>
        <font>big</font><align>center</align>
      </control>
"""
    keys = [(10+i) for i in range(10)]
    grid = [[17,18,19],[14,15,16],[11,12,13],[23,10,21]]
    # Kodi reads a bare-number <label> as a string id (GUIControlFactory:
    # IsNaturalNumber -> g_localizeStrings.Get), so <label>7</label> showed
    # string #7, "File manager". 12310-12319 are Kodi's own "0".."9".
    labels = {10 + n: f"$LOCALIZE[{12310 + n}]" for n in range(10)}
    labels.update({21: "$LOCALIZE[186]", 23: "&lt;-"})
    top = 92
    for r, row in enumerate(grid):
        body += f"""      <control type="grouplist">
        <left>22</left><top>{top + r*54}</top><width>320</width><height>50</height>
        <orientation>horizontal</orientation><itemgap>6</itemgap>
"""
        for cid in row:
            body += f"""        <control type="button" id="{cid}">
          <width>100</width><height>50</height><font>big</font><align>center</align><textoffsetx>0</textoffsetx>
          <label>{labels.get(cid,'')}</label>
        </control>
"""
        body += "      </control>\n"
    body += f"""      <control type="grouplist">
        <left>22</left><top>{top + 4*54}</top><width>320</width><height>34</height>
        <orientation>horizontal</orientation><itemgap>6</itemgap>
        <control type="radiobutton" id="20"><width>155</width><height>34</height><label>&lt;&lt;</label></control>
        <control type="radiobutton" id="22"><width>155</width><height>34</height><label>&gt;&gt;</label></control>
      </control>
"""
    return dialog("DialogNumeric", 360, top + 4*54 + 50, body, default="21",
                  icon="icons24/file.png")

# ====================================================== the small dialogs
def small_dialogs():
    out = {}

    # Kodi places this dialog itself: it centres the background image (999)
    # on the focused control and keeps it on screen by moving the WINDOW
    # origin (CGUIDialogContextMenu::PositionAtCurrentFocus). So 999 must sit
    # at the window origin and nothing may be offset from it - a centred
    # group or a full-screen dim would be shifted by the same amount and end
    # up off screen. It also resizes 999 to fit however many entries there are:
    # 999 = its XML height - 996's XML height + 996's content height, capped
    # at 996's XML height (CGUIDialogContextMenu::SetupButtons,
    # CGUIControlGroupList::GetHeight). So both are drawn as tall as the
    # screen allows and short menus still come out short. A long menu
    # scrolls (drag, wheel or keys) and scrollbar 997 shows that there is
    # more; it hides itself when everything fits (showonepage false).
    # tallpass leaves <coordinates> windows alone, so the 768 layout keeps
    # these heights.
    W, GL = 380, 520
    XLC = "[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]"
    def xl_pair(inc, normal, xl, ind):
        return (f"{ind}<include content=\"{inc}\" condition=\"{XLC}\"><param name=\"v\" value=\"{xl}\" /></include>\n"
                f"{ind}<include content=\"{inc}\" condition=\"!{XLC}\"><param name=\"v\" value=\"{normal}\" /></include>\n")
    # Normal mode keeps the full 360 px rows: the 18 px bar only exists
    # while the menu overflows (GUIScrollBarControl::IsVisible) and then
    # lies over the rows' right end - it is drawn after 996 and gets taps
    # first (CGUIControlGroup::SendMouseEvent runs last-rendered first).
    # Taller rows (XLC) give the 30 px bar a column of its own.
    BW, BWX, SBL = W - 20, W - 54, W - 28   # rows 10..370 / 10..336, bar 352..370 / 340..370
    out["DialogContextMenu"] = (H + "<window>\n  <defaultcontrol>996</defaultcontrol>\n"
      "  <coordinates><left>0</left><top>0</top></coordinates>\n  <controls>\n"
      f"    <control type=\"image\" id=\"999\">\n"
      f"      <left>0</left><top>0</top><width>{W}</width><height>{38 + GL + 10}</height>\n"
      "      <texture border=\"2\">panel_raised.png</texture>\n"
      "    </control>\n"
      "    <control type=\"group\">\n"
      "      <left>3</left><top>3</top>\n"
      "      <include content=\"Win_Title\">\n"
      f"        <param name=\"width\" value=\"{W-6}\" />\n"
      "        <param name=\"colour\" value=\"accent1\" />\n"
      "        <param name=\"icon\" value=\"icons24/settings.png\" />\n"
      "        <param name=\"label\" value=\"$LOCALIZE[31906]\" />\n"
      "      </include>\n"
      "    </control>\n"
      "    <control type=\"grouplist\" id=\"996\">\n"
      f"      <left>10</left><top>38</top><height>{GL}</height>\n"
      + xl_pair("Size_Width", BW, BWX, "      ") +
      "      <orientation>vertical</orientation><itemgap>2</itemgap>\n"
      "      <pagecontrol>997</pagecontrol>\n"
      "      <onright>997</onright>\n"
      "      <control type=\"button\" id=\"1000\">\n"
      f"        <height>30</height>\n"
      + xl_pair("Size_Width", BW, BWX, "        ") +
      "        <align>left</align><textoffsetx>12</textoffsetx>\n"
      "      </control>\n"
      "    </control>\n"
      "    <control type=\"scrollbar\" id=\"997\">\n"
      f"      <top>38</top><height>{GL}</height>\n"
      + xl_pair("Size_Left", SBL, SBL - 12, "      ")
      + xl_pair("Size_Width", 18, 30, "      ") +
      "      <showonepage>false</showonepage>\n"
      "      <onleft>996</onleft>\n"
      "    </control>\n  </controls>\n</window>\n")

    out["DialogNotification"] = (H + "<window>\n  <zorder>6</zorder>\n  <controls>\n"
      "    <control type=\"group\">\n"
      "      <right>10</right><top>34</top><width>440</width><height>96</height>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"440\" /><param name=\"height\" value=\"96\" /></include>\n"
      "      <control type=\"group\">\n"
      "        <left>3</left><top>3</top>\n"
      "        <include content=\"Win_Title\">\n"
      "          <param name=\"width\" value=\"434\" /><param name=\"colour\" value=\"accent2\" />\n"
      "          <param name=\"boxes\" value=\"none\" />\n"
      "          <param name=\"label\" value=\"$INFO[Control.GetLabel(401)]\" />\n"
      "        </include>\n"
      "      </control>\n"
      "      <control type=\"image\" id=\"400\">\n"
      "        <left>12</left><top>38</top><width>48</width><height>48</height>\n"
      "      </control>\n"
      "      <control type=\"fadelabel\" id=\"401\">\n"
      "        <left>-3000</left><top>0</top><width>300</width><height>22</height>\n"
      "      </control>\n"
      "      <control type=\"fadelabel\" id=\"402\">\n"
      "        <left>70</left><top>38</top><width>356</width><height>48</height>\n"
      "        <font>small</font>\n"
      "      </control>\n"
      "    </control>\n  </controls>\n</window>\n")

    # GUIDialogBusy.cpp has no label or progress API at all: it opens, runs
    # the render loop and closes. Its OnBack sets m_cancelled, which
    # WaitOnEvent(allowCancel) honours - so a Cancel button that sends Back
    # is all a touch user needs. busydialognocancel loads this same file and
    # ignores the flag (its Back just closes it), so it gets the box without
    # the button. Window.Is() tests the window evaluating the condition
    # (WINDOW_IS uses the control's context window, GUIControlsGUIInfo.cpp),
    # so each instance picks its own box even while both are open; only the
    # topmost of the two renders at all (CGUIDialogBusy*::DoProcess/Render).
    # No default focus: a second OK pressed while a listing loads must not
    # land on Cancel. Touch and mouse press it without focus; a remote has
    # Back, which does the same.
    def busy_box(cancel):
        ht = 148 if cancel else 92
        s  = "    <control type=\"group\">\n"
        s += f"      <visible>{'' if cancel else '!'}Window.Is(busydialog)</visible>\n"
        s += "      <centerleft>50%</centerleft><centertop>50%</centertop>\n"
        s += f"      <width>360</width><height>{ht}</height>\n"
        s += "      <include content=\"Dialog_Box\">\n"
        s += f"        <param name=\"width\" value=\"360\" /><param name=\"height\" value=\"{ht}\" />\n"
        s += "        <param name=\"innerwidth\" value=\"354\" /><param name=\"icon\" value=\"icons24/clock.png\" />\n"
        s += "        <param name=\"title\" value=\"$LOCALIZE[503]\" />\n"
        s += "        <param name=\"boxes\" value=\"none\" />\n"
        s += "      </include>\n"
        s += "      <control type=\"image\">\n"
        s += "        <left>20</left><top>44</top><width>32</width><height>32</height>\n"
        s += "        <texture>icons24/clock.png</texture>\n"
        s += "      </control>\n"
        s += "      <control type=\"label\">\n"
        s += "        <left>62</left><top>40</top><width>278</width><height>40</height>\n"
        s += "        <aligny>center</aligny><font>bold</font><label>$LOCALIZE[20186]</label>\n"
        s += "      </control>\n"
        if cancel:
            s += "      <control type=\"button\" id=\"9810\">\n"
            s += "        <left>90</left><top>90</top><width>180</width><height>44</height>\n"
            s += "        <align>center</align><label>$LOCALIZE[222]</label>\n"
            s += "        <onclick>Action(Back)</onclick>\n"
            s += "        <onup>9810</onup><ondown>9810</ondown><onleft>9810</onleft><onright>9810</onright>\n"
            s += "      </control>\n"
        return s + "    </control>\n"
    out["DialogBusy"] = (H + "<window>\n  <zorder>5</zorder>\n  <controls>\n"
      "    <!-- no dimming over a playing video (Estuary does the same) -->\n"
      "    <control type=\"group\">\n"
      "      <visible>!Window.IsVisible(fullscreenvideo) + !Window.IsVisible(fullscreengame)</visible>\n"
      "      <!-- no title bar here: Up/Left from the touch Back go to Cancel -->\n"
      "      <include content=\"Dialog_Dim\"><param name=\"up\" value=\"9810\" /></include>\n"
      "    </control>\n"
      + busy_box(True) + busy_box(False) +
      "  </controls>\n</window>\n")

    # Kodi reports volume as decibels (Player.Volume as a label is "-31.4 dB"),
    # which reads as a strange negative number and was cut off under the larger
    # fonts. Show the bar alone - Player.Volume as a progress is 0-100 - with a
    # plain "Muted" when muted. Text uses chrome fonts, capped at 20px.
    out["DialogVolumeBar"] = (H + "<window>\n  <zorder>4</zorder>\n  <controls>\n"
      "    <control type=\"group\">\n"
      "      <centerleft>50%</centerleft><top>34</top><width>400</width><height>72</height>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"400\" /><param name=\"height\" value=\"72\" /></include>\n"
      "      <control type=\"image\">\n"
      "        <left>12</left><top>20</top><width>32</width><height>32</height>\n"
      "        <texture>$VAR[VolumeIconVar]</texture>\n"
      "      </control>\n"
      "      <control type=\"label\">\n"
      "        <left>56</left><top>8</top><width>330</width><height>22</height>\n"
      "        <font>chromebold</font><aligny>center</aligny>\n"
      "        <label>$LOCALIZE[13376]</label>\n"
      "      </control>\n"
      "      <control type=\"progress\">\n"
      "        <left>56</left><top>36</top><width>330</width><height>22</height>\n"
      "        <info>Player.Volume</info>\n"
      "        <visible>!Player.Muted</visible>\n"
      "      </control>\n"
      "      <control type=\"label\">\n"
      "        <left>56</left><top>36</top><width>330</width><height>22</height>\n"
      "        <font>chromebold</font><textcolor>marked</textcolor><aligny>center</aligny>\n"
      "        <label>$LOCALIZE[31949]</label>\n"
      "        <visible>Player.Muted</visible>\n"
      "      </control>\n"
      "    </control>\n  </controls>\n</window>\n")

    # playback overlays (V-6, V-8, V-14): built in the player / OSD section
    out["DialogSeekBar"] = seek_bar()
    out["VideoOSDBookmarks"] = bookmarks_dialog()
    out["DialogFullScreenInfo"] = fullscreen_info()
    out["DialogPlayerProcessInfo"] = process_info()
    out["DialogPVRRadioRDSInfo"] = rds_info()

    # A textbox scrolls only through its page control (CGUITextBox reacts to
    # GUI_MSG_PAGE_CHANGE from m_pageControl; it has no key, wheel or gesture
    # handling), and it cannot take focus. So the scrollbar is linked and is
    # the default control: Up/Down page through the text (GUIScrollBarControl
    # ::OnAction), and a finger drags it - sizepass widens it in Touch mode.
    body = (well(10, 36, 840, 380, "panel_sunken.png")
            + "      <control type=\"textbox\" id=\"5\">\n"
              "        <left>18</left><top>44</top><width>806</width><height>364</height>\n"
              "        <font>small</font>\n        <pagecontrol>60</pagecontrol>\n      </control>\n"
              "      <control type=\"scrollbar\" id=\"60\">\n"
              "        <left>828</left><top>44</top><width>18</width><height>364</height>\n"
              "        <onup>9903</onup>\n      </control>\n")
    out["DialogTextViewer"] = dialog("DialogTextViewer", 860, 430, body, default="60",
                                     icon="icons24/file.png")

    # GUIDialogSlider.cpp uses only 10 (heading), 11 (slider) and 12 (value).
    # Kodi's slider default is VERTICAL (CGUIControlFactory::Create:
    # ORIENTATION orientation = VERTICAL), and a vertical slider ignores
    # Left/Right (CGUISliderControl::OnAction moves only on Up/Down then), so
    # the - and + buttons below would do nothing without the explicit
    # horizontal.
    # The heading goes on the title bar (Kodi never writes id 1 here). 13/14
    # are skin buttons - Estuary's touch minus/plus: focus the slider, step
    # it, and keep focus on the button so it can be tapped again.
    body = ("      <control type=\"label\" id=\"10\">\n"
            "        <left>29</left><top>3</top><width>400</width><height>26</height>\n"
            "        <font>chromebold</font><textcolor>titletext</textcolor>\n"
            "        <align>left</align><aligny>center</aligny>\n      </control>\n"
            "      <control type=\"label\" id=\"12\">\n"
            "        <left>16</left><top>38</top><width>500</width><height>26</height>\n"
            "        <font>bold</font><align>center</align><aligny>center</aligny>\n      </control>\n"
            "      <control type=\"button\" id=\"13\">\n"
            "        <left>16</left><top>70</top><width>64</width><height>44</height>\n"
            "        <font>bigbold</font><align>center</align><aligny>center</aligny><textoffsetx>0</textoffsetx>\n"
            "        <label>-</label>\n"
            "        <onclick>SetFocus(11)</onclick><onclick>Action(Left)</onclick><onclick>SetFocus(13)</onclick>\n"
            "        <onup>11</onup><onright>14</onright><onleft>14</onleft>\n      </control>\n"
            "      <control type=\"slider\" id=\"11\">\n"
            "        <left>88</left><top>78</top><width>356</width><height>28</height>\n"
            "        <orientation>horizontal</orientation>\n"
            "        <ondown>13</ondown><onup>13</onup>\n      </control>\n"
            "      <control type=\"button\" id=\"14\">\n"
            "        <left>452</left><top>70</top><width>64</width><height>44</height>\n"
            "        <font>bigbold</font><align>center</align><aligny>center</aligny><textoffsetx>0</textoffsetx>\n"
            "        <label>+</label>\n"
            "        <onclick>SetFocus(11)</onclick><onclick>Action(Right)</onclick><onclick>SetFocus(14)</onclick>\n"
            "        <onup>11</onup><onleft>13</onleft><onright>13</onright>\n      </control>\n")
    out["DialogSlider"] = dialog("DialogSlider", 532, 128, body, default="11",
                                 icon="icons24/settings.png", heading=False)

    # CGUIDialogExtendedProgressBar is MODELESS (input carries on below it)
    # and opens for any background job - library scans, EPG import, add-on
    # installs - even during playback. Kodi fills 30 (job), 31 (step) and 32
    # (progress) only. So no dimming and no centred box: a small window in the
    # bottom-right corner above the task bar, out of the way of the
    # notification (top right), and hidden over full-screen video, games,
    # the visualisation and the picture viewer. Hiding it is harmless: it is
    # modeless and closes itself.
    out["DialogExtendedProgressBar"] = (H + "<window>\n  <controls>\n"
      "    <control type=\"group\">\n"
      "      <right>10</right><bottom>40</bottom><width>380</width><height>88</height>\n"
      "      <visible>![Window.IsVisible(fullscreenvideo) | Window.IsVisible(fullscreengame) | Window.IsVisible(visualisation) | Window.IsVisible(slideshow)]</visible>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"380\" /><param name=\"height\" value=\"88\" /></include>\n"
      "      <control type=\"group\">\n"
      "        <left>3</left><top>3</top>\n"
      "        <include content=\"Win_Title\">\n"
      "          <param name=\"width\" value=\"374\" /><param name=\"colour\" value=\"accent2\" />\n"
      "          <param name=\"icon\" value=\"icons24/download.png\" />\n"
      "          <param name=\"boxes\" value=\"none\" />\n"
      "          <param name=\"label\" value=\"$INFO[Control.GetLabel(30)]\" />\n"
      "        </include>\n"
      "      </control>\n"
      "      <control type=\"label\" id=\"30\">\n"
      "        <left>-3000</left><top>0</top><width>300</width><height>22</height>\n"
      "      </control>\n"
      "      <control type=\"label\" id=\"31\">\n"
      "        <left>12</left><top>34</top><width>356</width><height>24</height>\n"
      "        <font>small</font><aligny>center</aligny>\n"
      "      </control>\n"
      "      <control type=\"progress\" id=\"32\">\n"
      "        <left>12</left><top>62</top><width>356</width><height>16</height>\n"
      "      </control>\n"
      "    </control>\n  </controls>\n</window>\n")

    # Kodi picks the cursor by CONTROL ID, not by order: MOUSE_STATE_NORMAL = 1,
    # FOCUS 2, DRAG 3, CLICK 4 (xbmc/input/mouse/MouseStat.h). OnWindowLoaded
    # hides every child, then SetPointer(state) shows GetControl(state). A
    # control without one of those ids is never made visible, so the cursor
    # simply never appears. No animation here either - it delays the cursor.
    out["Pointer"] = (H + "<window>\n  <controls>\n"
      "    <control type=\"image\" id=\"1\">\n"
      "      <description>Pointer</description>\n"
      "      <left>0</left><width>24</width><height>34</height>\n"
      "      <texture>$VAR[PointerTex]</texture>\n    </control>\n"
      "    <control type=\"image\" id=\"2\">\n"
      "      <description>Pointer over a control</description>\n"
      "      <left>0</left><width>24</width><height>34</height>\n"
      "      <texture>$VAR[PointerTex]</texture>\n    </control>\n"
      "    <control type=\"image\" id=\"3\">\n"
      "      <description>Pointer dragging</description>\n"
      "      <left>0</left><width>24</width><height>34</height>\n"
      "      <texture>$VAR[PointerTex]</texture>\n    </control>\n"
      "    <control type=\"image\" id=\"4\">\n"
      "      <description>Pointer clicking</description>\n"
      "      <left>0</left><width>24</width><height>34</height>\n"
      "      <texture>$VAR[PointerClickTex]</texture>\n    </control>\n"
      "  </controls>\n</window>\n")

    # Kodi treats Startup as part of its own initialisation: until this
    # window hands over, the UI is not "ready" - skin reloads are refused,
    # peripherals (CEC) wait, and the window ignores the mouse. It must
    # replace itself at once with the configured start window, exactly as
    # Estuary's does. It shows only the desktop so the hand-over does not flash.
    # T-14: Touch mode's mouse detection starts on Home's load (home.py), so
    # a start window other than Home (Settings > Interface > Startup window)
    # would leave a plugged-in mouse without a pointer. Start it here then;
    # with Home (10000, WINDOW_HOME) as start window Home's own onload does
    # it, and two copies started a few ms apart could both pass
    # mousewatch.py's "already running" test. A profile login screen never
    # loads Startup (CApplication::Initialize), Home starts it after login.
    out["Startup"] = (H + "<window>\n"
      "  <onload condition=\"Skin.HasSetting(touchmode) + !String.IsEqual(System.StartupWindow,10000)"
      " + String.IsEmpty(Window(Home).Property(arthuros.mousewatch))\">"
      "RunScript(special://skin/scripts/mousewatch.py)</onload>\n"
      "  <onload>ReplaceWindow($INFO[System.StartupWindow])</onload>\n"
      "  <backgroundcolor>desktop</backgroundcolor>\n"
      "  <controls>\n"
      "    <include>Chrome_Desktop</include>\n"
      "  </controls>\n</window>\n")

    return out


# ====================================================== everyday dialogs
def button_menu():
    """The power menu. Kodi does not fill this - the skin supplies the items,
    each gated on whether the platform can actually do it."""
    items = [
      ("$LOCALIZE[13016]", "power",           "Powerdown()",                       "System.CanPowerDown"),
      ("$LOCALIZE[13011]", "power_suspend",   "Dialog.Close(shutdownmenu)</onclick><onclick>Suspend()", "System.CanSuspend"),
      ("$LOCALIZE[13010]", "power_hibernate", "Dialog.Close(shutdownmenu)</onclick><onclick>Hibernate()", "System.CanHibernate"),
      ("$LOCALIZE[13013]", "power_reboot",    "Reset()",                           "System.CanReboot"),
      ("$LOCALIZE[13012]", "exit",            "Quit()",                            "System.ShowExitButton"),
      ("$LOCALIZE[20150]", "clock",           "AlarmClock(shutdowntimer,Shutdown())", "!System.HasAlarm(shutdowntimer)"),
      ("$LOCALIZE[20151]", "timer_cancel",    "CancelAlarm(shutdowntimer)",        "System.HasAlarm(shutdowntimer)"),
      ("$LOCALIZE[13017]", "power_inhibit",   "InhibitIdleShutdown(true)",         "System.HasShutdown + !System.IdleShutdownInhibited"),
      ("$LOCALIZE[13018]", "power_allow",     "InhibitIdleShutdown(false)",        "System.HasShutdown + System.IdleShutdownInhibited"),
      ("$LOCALIZE[20126]", "logoff",          "Dialog.Close(all,true)</onclick><onclick>System.LogOff", "System.HasLoginScreen"),
      # "mastermode" toggles master mode: say which way it goes (20043 is "Lock settings")
      ("$LOCALIZE[20045]", "masterlock",      "mastermode",                        "System.HasLocks + !System.IsMaster"),
      ("$LOCALIZE[20046]", "masterlock_off",  "mastermode",                        "System.HasLocks + System.IsMaster"),
    ]
    rows = "".join(f"""          <item>
            <label>{lab}</label>
            <icon>icons24/{ic}.png</icon>
            <onclick>{act}</onclick>
            <visible>{vis}</visible>
          </item>
""" for lab, ic, act, vis in items)
    body = well(10, 36, 440, 408, "panel_sunken.png")
    body += f"""      <control type="list" id="9000">
        <left>16</left><top>42</top><width>404</width><height>396</height>
        <onleft>9000</onleft><onright>9000</onright>
        <onup>9000</onup><ondown>9000</ondown>
        <scrolltime tween="linear">0</scrolltime>
        <itemlayout height="34" width="404">
          <control type="image">
            <left>6</left><top>9</top><width>16</width><height>16</height>
            <texture>$INFO[ListItem.Icon]</texture>
          </control>
          <control type="label">
            <left>30</left><top>0</top><width>368</width><height>34</height>
            <font>normal</font><textcolor>text</textcolor><aligny>center</aligny>
            <label>$INFO[ListItem.Label]</label>
          </control>
        </itemlayout>
        <focusedlayout height="34" width="404">
          <control type="image">
            <left>0</left><top>0</top><width>404</width><height>34</height>
            <texture>bar_red.png</texture>
          </control>
          <control type="image">
            <left>6</left><top>9</top><width>16</width><height>16</height>
            <texture>$INFO[ListItem.Icon]</texture>
          </control>
          <control type="label">
            <left>30</left><top>0</top><width>368</width><height>34</height>
            <font>bold</font><textcolor>textinv</textcolor><aligny>center</aligny>
            <label>$INFO[ListItem.Label]</label>
          </control>
        </focusedlayout>
        <content>
{rows}        </content>
      </control>
"""
    return dialog("DialogButtonMenu", 460, 456, body, default="9000",
                  icon="icons24/settings.png", colour="accent1",
                  heading=False)


def file_browser():
    """Shown whenever you pick a path or add a source.
    Kodi's ids (GUIDialogFileBrowser.cpp): 450 list, 451 thumb panel,
    411 heading, 412 path, 413 OK, 414 cancel, 415 new folder, 416 flip."""
    body  = """      <control type="label" id="411">
        <left>29</left><top>3</top><width>760</width><height>26</height>
        <font>bold</font><textcolor>titletext</textcolor><aligny>center</aligny>
      </control>
"""
    body += well(10, 36, 880, 26, "panel_sunken_chrome.png")
    body += """      <control type="label" id="412">
        <left>18</left><top>36</top><width>864</width><height>26</height>
        <font>small</font><textcolor>textdim</textcolor><aligny>center</aligny>
      </control>
"""
    body += well(10, 68, 880, 328, "panel_sunken.png")

    def fb_layout(tag, h, focused, cond=None):
        """One row of the file list. h: 26, or 42 for Extra large / Touch
        mode. The focused row's labels carry selectedcolor textinv: Kodi
        draws a marked item's labels in selectedcolor, and the default
        (marked) is unreadable on the selection bar."""
        c = f' condition="{cond}"' if cond else ""
        it = (h - 16) // 2
        s = f'        <{tag} height="{h}" width="848"{c}>\n'
        if focused:
            s += f"""          <control type="image">
            <left>0</left><top>0</top><width>848</width><height>{h}</height>
            <texture>bar_blue.png</texture>
          </control>
"""
        s += f"""          <control type="image">
            <left>4</left><top>{it}</top><width>16</width><height>16</height>
            <texture fallback="DefaultFolder.png">$INFO[ListItem.Icon]</texture>
            <aspectratio>keep</aspectratio>
          </control>
"""
        if focused:
            s += f"""          <control type="label">
            <left>28</left><top>0</top><width>640</width><height>{h}</height>
            <font>bold</font><textcolor>textinv</textcolor><selectedcolor>textinv</selectedcolor>
            <aligny>center</aligny><label>$INFO[ListItem.Label]</label>
          </control>
          <control type="label">
            <left>28</left><top>0</top><width>816</width><height>{h}</height>
            <align>right</align><aligny>center</aligny><font>small</font>
            <textcolor>textinv</textcolor><selectedcolor>textinv</selectedcolor><label>$INFO[ListItem.Label2]</label>
          </control>
"""
        else:
            s += f"""          <control type="label">
            <left>28</left><top>0</top><width>640</width><height>{h}</height>
            <aligny>center</aligny><label>$INFO[ListItem.Label]</label>
          </control>
          <control type="label">
            <left>28</left><top>0</top><width>816</width><height>{h}</height>
            <align>right</align><aligny>center</aligny><font>small</font>
            <textcolor>textdim</textcolor><label>$INFO[ListItem.Label2]</label>
          </control>
"""
        return s + f"        </{tag}>\n"

    for cid, kind in ((450, "list"), (451, "panel")):
        vis = "" if cid == 450 else "        <visible>Control.IsVisible(451)</visible>\n"
        if cid == 450:
            # sizepass.py gives the list its Extra large / Touch rows
            layouts = fb_layout("itemlayout", 26, False) + fb_layout("focusedlayout", 26, True)
        else:
            # 451 is what Kodi shows when you browse for a picture (a tile
            # image, a source thumbnail); sizepass skips panels, so its
            # taller rows are written here, first, as sizepass does for lists
            x = INFO_XLC
            layouts = (fb_layout("itemlayout", 42, False, x) + fb_layout("focusedlayout", 42, True, x)
                       + fb_layout("itemlayout", 26, False, "!" + x)
                       + fb_layout("focusedlayout", 26, True, "!" + x))
        body += f"""      <control type="{kind}" id="{cid}">
        <left>16</left><top>74</top><width>848</width><height>316</height>
        <onleft>413</onleft><onright>60</onright>
        <onup>{cid}</onup><ondown>413</ondown>
        <pagecontrol>60</pagecontrol>
        <scrolltime tween="linear">0</scrolltime>
{layouts}      </control>
"""
    # 415 (New folder) and 416 (Mirror image) are enabled by Kodi only when
    # they apply (416: browsing for pictures); hide them otherwise. 416 is a
    # togglebutton: the empty <usealttexture> keeps the default's
    # always-true condition out, so it toggles and shows its state.
    body += """      <control type="scrollbar" id="60">
        <left>868</left><top>74</top><width>18</width><height>316</height>
        <onleft>450</onleft><onright>413</onright>
      </control>
      <control type="grouplist">
        <left>13</left><top>404</top><width>874</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>6</itemgap>
        <onup>450</onup>
        <control type="button" id="413"><width>200</width><height>32</height><label>$LOCALIZE[186]</label></control>
        <control type="button" id="414"><width>200</width><height>32</height><label>$LOCALIZE[222]</label></control>
        <control type="button" id="415"><width>230</width><height>32</height><label>$LOCALIZE[20309]</label><visible>Control.IsEnabled(415)</visible></control>
        <control type="togglebutton" id="416"><width>200</width><height>32</height><label>$LOCALIZE[749]</label>
          <usealttexture></usealttexture>
          <alttexturefocus border="2" colordiffuse="select">select_bevel.png</alttexturefocus>
          <alttexturenofocus border="2" colordiffuse="facetint">button_down.png</alttexturenofocus>
          <visible>Control.IsEnabled(416)</visible>
        </control>
      </control>
"""
    return dialog("FileBrowser", 900, 452, body, default="450",
                  icon="icons24/harddisk.png", heading=False)

def media_source():
    """Add / edit a source. Ids from GUIDialogMediaSource.cpp: 2 heading,
    10 path list, 11 browse, 12 name, 13 add, 14 remove, 18 OK, 19 cancel,
    20 content."""
    body  = """      <control type="label" id="2">
        <left>29</left><top>3</top><width>560</width><height>26</height>
        <font>bold</font><textcolor>titletext</textcolor><aligny>center</aligny>
      </control>
"""
    # Kodi writes no caption on 11/13/14 and only the value (label2) on 12
    # (GUIDialogMediaSource.cpp), so the skin supplies Estuary's captions.
    body += """      <control type="label">
        <left>13</left><top>36</top><width>654</width><height>22</height>
        <font>chromesmall</font><textcolor>textdim</textcolor><aligny>center</aligny>
        <label>$LOCALIZE[1021]</label>
      </control>
"""
    body += well(10, 60, 660, 180, "panel_sunken.png")
    body += """      <control type="list" id="10">
        <left>16</left><top>66</top><width>648</width><height>168</height>
        <onleft>11</onleft><onright>11</onright>
        <onup>10</onup><ondown>9011</ondown>
        <scrolltime tween="linear">0</scrolltime>
        <itemlayout height="28" width="648">
          <control type="label">
            <left>8</left><top>0</top><width>632</width><height>28</height>
            <aligny>center</aligny><label>$INFO[ListItem.Label]</label>
          </control>
        </itemlayout>
        <focusedlayout height="28" width="648">
          <control type="image">
            <left>0</left><top>0</top><width>648</width><height>28</height>
            <texture>bar_blue.png</texture>
          </control>
          <control type="label">
            <left>8</left><top>0</top><width>632</width><height>28</height>
            <font>bold</font><textcolor>textinv</textcolor>
            <aligny>center</aligny><label>$INFO[ListItem.Label]</label>
          </control>
        </focusedlayout>
      </control>
      <!-- 20 (set content) is always hidden by Kodi (UpdateButtons) -->
      <control type="button" id="20">
        <left>-3000</left><top>0</top><width>200</width><height>30</height>
      </control>
"""
    # The three rows under the path list (Browse/Add/Remove, the name, OK/
    # Cancel) are 34 px, 50 with taller rows (Extra large or Touch mode).
    # They stack in a vertical grouplist, so each row moves down as the one
    # above it grows, and the dialog box grows by the 3 x 16 px. The group
    # keeps the normal height, so the normal dialog stays exactly centred;
    # the taller one reaches 24 px further down (still clear of the task
    # bar at 600). Kodi resolves include conditions once, at load (a font
    # or Touch mode change reloads the skin), so only one Dialog_Box exists.
    # Kodi adds a group to its parent BEFORE loading the group's children
    # (CGUIWindow::LoadControl), and a grouplist overwrites the Up/Down of
    # each control added to it (CGUIControlGroupList::AddControl) while the
    # children only inherit what their row has at that moment. So the outer
    # grouplist wires the rows to each other, and every button names its own
    # Up/Down; Down on OK/Cancel stays put instead of wrapping to the top.
    def hpair(ind):
        return (f'{ind}<include content="Height_34_XL" condition="{INFO_XLC}" />\n'
                f'{ind}<include content="Height_34" condition="!{INFO_XLC}" />\n')
    def btn(cid, wd, sid, up, down):
        return (f'          <control type="button" id="{cid}"><width>{wd}</width>'
                f'<include content="Height_34_XL" condition="{INFO_XLC}" />'
                f'<include content="Height_34" condition="!{INFO_XLC}" />'
                f'<label>$LOCALIZE[{sid}]</label><onup>{up}</onup><ondown>{down}</ondown></control>\n')
    body += ('      <control type="grouplist" id="9010">\n'
             '        <left>13</left><top>248</top><width>654</width><height>166</height>\n'
             '        <orientation>vertical</orientation><itemgap>8</itemgap>\n'
             '        <onup>10</onup>\n'
             '        <control type="grouplist" id="9011">\n'
             '          <width>654</width>\n' + hpair("          ") +
             '          <orientation>horizontal</orientation><align>center</align><itemgap>6</itemgap>\n'
             + btn(11, 210, 1024, 10, 12) + btn(13, 210, 15019, 10, 12) + btn(14, 210, 1210, 10, 12) +
             '        </control>\n'
             '        <control type="edit" id="12">\n'
             '          <width>654</width>\n' + hpair("          ") +
             '          <label>$LOCALIZE[551]</label>\n'
             '        </control>\n'
             '        <control type="grouplist" id="9012">\n'
             '          <width>654</width>\n' + hpair("          ") +
             '          <orientation>horizontal</orientation><align>center</align><itemgap>8</itemgap>\n'
             + btn(18, 280, 186, 12, 18) + btn(19, 280, 222, 12, 19) +
             '        </control>\n'
             '      </control>\n')
    body += """      <control type="scrollbar" id="60"><left>-3000</left><top>0</top><width>18</width><height>100</height></control>
"""
    # themepass sets only the FIRST icon param to the registry's title-bar
    # icon (iconset.WINDOW_ICONS), so both Dialog_Box copies name it here
    out = dialog("DialogMediaSource", 680, 378, body, default="10",
                 icon="icons24/addsource.png", heading=False)
    a = out.index('      <include content="Dialog_Box">\n')
    b = out.index("      </include>\n", a) + len("      </include>\n")
    box = out[a:b]
    tall = box.replace('<include content="Dialog_Box">', f'<include content="Dialog_Box" condition="{INFO_XLC}">', 1)
    tall = tall.replace('<param name="height" value="378" />', '<param name="height" value="426" />', 1)
    norm = box.replace('<include content="Dialog_Box">', f'<include content="Dialog_Box" condition="!{INFO_XLC}">', 1)
    assert tall != box and 'value="426"' in tall
    return out[:a] + tall + norm + out[b:]

def picture_info():
    """S-3/S-4: Picture information (from the picture viewer's OSD or a
    picture's context menu). GUIDialogPictureInfo.cpp fills only list 5:
    one item per known tag, the tag's name as Label and its value as Label2
    (UpdatePictureInfo). It also follows the viewer: next/previous/play/
    pause pass through to the slideshow and FrameMove refreshes the list.
    The picture itself is the current slide (CGUIDialogPictureInfo::
    SetPicture -> CPicturesGUIInfo::SetCurrentSlide), which Slideshow.Path
    (the folder, with a trailing separator) plus Slideshow.Filename name in
    both cases. The dim covers the viewer, so a preview sits beside the
    list. Known limit: Slideshow.Path is CURL(dir).GetWithoutUserDetails()
    (PicturesGUIInfo.cpp), so on a source whose URL carries the login
    (smb://user:pass@..., ftp://user:pass@...) the rebuilt path has no
    credentials and the preview may show the DefaultPicture fallback;
    URL-style paths with options (plugin, http) may be rebuilt wrongly the
    same way. Local and guest/password-manager shares are unaffected. No
    infolabel gives the slide's full path with credentials. Names and values get columns of their own, so a long value (a
    path, a camera model) no longer runs over its name."""
    W, Hh = 900, 466
    body  = well(10, 36, 320, 420, "panel_sunken_grey.png")
    body += """      <control type="image">
        <left>16</left><top>42</top><width>308</width><height>408</height>
        <texture background="true" fallback="DefaultPicture.png">$INFO[Slideshow.Path]$INFO[Slideshow.Filename]</texture>
        <aspectratio>keep</aspectratio>
      </control>
"""
    def layouts(iw):
        kw = 190
        out = ""
        for focused in (False, True):
            tag = "focusedlayout" if focused else "itemlayout"
            out += f'        <{tag} height="28" width="{iw}">\n'
            if focused:
                out += (f'          <control type="image"><left>0</left><top>0</top><width>{iw}</width>'
                        '<height>28</height><texture colordiffuse="select">fill.png</texture></control>\n')
            kcol = "textinv" if focused else "textdim"
            vcol = "textinv" if focused else "text"
            # Long tag names ('Supplemental categories' is ~15 cells of
            # the XL 'small') and long values (the file path, camera
            # models) scroll on the focused row instead of being cut.
            scroll = "<scroll>true</scroll>" if focused else ""
            out += (f'          <control type="label"><left>8</left><top>0</top><width>{kw}</width>'
                    f'<height>28</height><font>small</font><textcolor>{kcol}</textcolor>'
                    f'<aligny>center</aligny>{scroll}<label>$INFO[ListItem.Label]</label></control>\n'
                    f'          <control type="label"><left>{kw + 16}</left><top>0</top><width>{iw - kw - 24}</width>'
                    f'<height>28</height><font>normal</font><textcolor>{vcol}</textcolor>'
                    f'<aligny>center</aligny>{scroll}<label>$INFO[ListItem.Label2]</label></control>\n')
            out += f"        </{tag}>\n"
        return out
    body += xlist(5, 60, 336, 36, 554, 420, {"onup": "5", "ondown": "5", "onleft": "5"},
                  layouts=layouts)
    return dialog("DialogPictureInfo", W, Hh, body, default="5",
                  icon="icons24/pictures_info.png", heading=False)



def system_info():
    """Kodi's contract (GUIWindowSystemInfo.cpp): the focused button 94-101 IS
    the selected section; Kodi writes the section title to 40, up to twelve
    lines to 2-13, app/version to 52, build date to 53, and shows textbox 30
    only for the privacy policy and group 102 only for 'Thank you!' (101).
    The skin supplies the button labels."""
    sections = [(95, 20037, "file"), (94, 13277, "harddisk"), (96, 13279, "network"),
                (97, 13280, "movies"), (98, 13281, "program"), (99, 19191, "tvshows"),
                (100, 12389, "file"), (101, 12396, "favourites")]
    body  = well(6, 34, 300, 494, "panel_sunken_grey.png")
    body += """      <control type="grouplist">
        <left>12</left><top>40</top><width>288</width><height>482</height>
        <orientation>vertical</orientation><itemgap>3</itemgap>
        <onup>9100</onup><ondown>9100</ondown><onright condition="Control.IsVisible(30)">60</onright>
"""
    for cid, sid, ic in sections:
        body += f"""        <control type="button" id="{cid}">
          <width>288</width><height>34</height>
          <label>$LOCALIZE[{sid}]</label>
          <align>left</align><textoffsetx>14</textoffsetx>
        </control>
"""
    body += "      </control>\n"
    body += well(312, 34, 694, 440, "panel_sunken.png")
    # Kodi never writes 40 for 'Thank you!' (FrameMove has no branch for
    # it), so the last section's title would stay up: group 102 has its own.
    body += """      <control type="label" id="40">
        <left>324</left><top>40</top><width>670</width><height>28</height>
        <font>bigbold</font>
        <visible>!Control.IsVisible(102)</visible>
      </control>
      <control type="image">
        <left>324</left><top>70</top><width>670</width><height>1</height>
        <texture>fill_black.png</texture>
      </control>
"""
    for i, cid in enumerate(range(2, 14)):
        body += f"""      <control type="label" id="{cid}">
        <left>324</left><top>{76 + i*32}</top><width>670</width><height>30</height>
      </control>
"""
    # The privacy policy is long, and a textbox moves only through its page
    # control (CGUITextBox has no wheel or gesture handling): scrollbar 60
    # beside it, which a finger can drag (sizepass widens it in Touch mode /
    # Extra large). It scrolls by itself too, except while 60 has the focus.
    # Right from the section buttons reaches 60 only while the policy shows:
    # the buttons inherit the grouplist's conditional <onright> (AddControl
    # copies the whole CGUIAction). It must be conditional and 60 must have
    # no <onright>: CGUIWindow::OnMove walks past a hidden control along its
    # own onright, so an unconditional 60 -> 100 chain would jump from any
    # section straight to the Privacy policy. Focusing 60 keeps the section
    # (Kodi switches only on 94-101).
    body += """      <control type="textbox" id="30">
        <left>324</left><top>76</top><width>640</width><height>390</height>
        <font>small</font>
        <pagecontrol>60</pagecontrol>
        <autoscroll delay="6000" time="4000" repeat="8000">!Control.HasFocus(60)</autoscroll>
      </control>
      <control type="scrollbar" id="60">
        <left>976</left><top>76</top><width>18</width><height>390</height>
        <onleft>100</onleft>
        <visible>Control.IsVisible(30)</visible>
      </control>
      <control type="group" id="102">
        <left>324</left><top>40</top><width>670</width><height>426</height>
        <control type="label">
          <left>0</left><top>0</top><width>670</width><height>28</height>
          <font>bigbold</font><label>$LOCALIZE[12396]</label>
        </control>
        <control type="label">
          <left>0</left><top>36</top><width>670</width><height>28</height>
          <font>bold</font><label>$LOCALIZE[12398]</label>
        </control>
        <control type="textbox">
          <left>0</left><top>72</top><width>670</width><height>200</height>
          <label>$LOCALIZE[12397]</label>
        </control>
      </control>
"""
    body += well(312, 480, 694, 48, "panel_sunken_grey.png")
    body += """      <control type="label" id="52">
        <left>324</left><top>482</top><width>670</width><height>22</height>
        <font>bold</font>
      </control>
      <control type="label" id="53">
        <left>324</left><top>504</top><width>670</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
      </control>
"""
    return fullwindow("SettingsSystemInfo", body, default="95",
                      icon="icons24/program.png", colour="accent1")

# ====================================================== bespoke windows
def filemanager():
    body = ""
    for i, (lst, sb, lbl, cnt, x) in enumerate([(20,60,101,12,6), (21,61,102,13,510)]):
        body += well(x, 34, 498, 30, "panel_sunken_chrome.png")
        body += (f"      <control type=\"label\" id=\"{lbl}\">\n"
                 f"        <left>{x+8}</left><top>34</top><width>420</width><height>30</height>\n"
                 f"        <font>small</font>\n      </control>\n"
                 f"      <control type=\"label\" id=\"{cnt}\">\n"
                 f"        <left>{x+8}</left><top>34</top><width>482</width><height>30</height>\n"
                 f"        <font>small</font><align>right</align><textcolor>textdim</textcolor>\n      </control>\n")
        other = 21 if lst == 20 else 20
        body += list_block(lst, sb, x, 70, 498, 458, rowh=24,
                           onleft=str(other), ondown="9100")
    return fullwindow("FileManager", body, default="20",
                      icon="icons24/harddisk.png", colour="accent1")

def weather():
    """Every value here is a control Kodi fills itself, every frame, from its
    weather manager (GUIWindowWeather::UpdateButtons): 10 location, 11 last
    update, 21 icon, 22-28 current conditions, and 31-35, 41-45 ... for each
    forecast day. Those values change only once a refresh has finished.

    The Window(Weather) properties used before are written twice per refresh:
    first raw by the weather add-on (Celsius, lower case, ISO dates, bare icon
    codes), then converted by Kodi. Reading them showed the raw set for a
    moment on every refresh - that was the "other forecast" flashing up."""
    def cap(l, t, w, sid):
        return f"""      <control type="label">
        <left>{l}</left><top>{t}</top><width>{w}</width><height>24</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$LOCALIZE[{sid}]:</label>
      </control>
"""
    def val(cid, l, t, w, font="small", h=24, align="left"):
        return f"""      <control type="label" id="{cid}">
        <left>{l}</left><top>{t}</top><width>{w}</width><height>{h}</height>
        <font>{font}</font><align>{align}</align>
      </control>
"""
    body  = well(6, 34, 1000, 138, "panel_sunken_grey.png")
    body += """      <control type="image" id="21">
        <left>18</left><top>44</top><width>118</width><height>118</height>
        <aspectratio>keep</aspectratio>
      </control>
"""
    body += val(23, 150, 44, 130, "bigbold", 36)
    body += val(22, 286, 44, 330, "bigbold", 36)
    body += cap(150, 84, 150, 404) + val(26, 302, 84, 330)
    body += cap(150, 108, 150, 406) + val(28, 302, 108, 70)
    body += cap(380, 108, 150, 402) + val(24, 532, 108, 100)
    body += cap(150, 132, 150, 405) + val(27, 302, 132, 70)
    body += cap(380, 132, 150, 403) + val(25, 532, 132, 100)
    body += """      <control type="button" id="2">
        <right>14</right><top>46</top><width>150</width><height>32</height>
        <align>center</align>
        <onleft>20</onleft><onright>20</onright>
        <ondown>9100</ondown><onup>9100</onup>
      </control>
      <control type="button" id="20">
        <right>172</right><top>46</top><width>220</width><height>32</height>
        <align>center</align>
        <label>$LOCALIZE[31944]</label>
        <visible>Integer.IsGreater(Window(Weather).Property(Locations),1)</visible>
        <onclick>Weather.LocationNext</onclick>
        <onleft>2</onleft><onright>2</onright>
        <ondown>9100</ondown><onup>9100</onup>
      </control>
      <control type="label">
        <right>14</right><top>92</top><width>358</width><height>24</height>
        <font>small</font><textcolor>textdim</textcolor><align>right</align>
        <label>$INFO[Window(Weather).Property(WeatherProvider)]</label>
      </control>
      <control type="group" id="567"><left>-3000</left><top>0</top><width>10</width><height>10</height></control>
"""
    # five day tiles; Kodi fills 31+10i .. 35+10i
    for i in range(5):
        x = 8 + i * 200
        c = 31 + 10 * i
        body += well(x, 180, 192, 214, "panel_raised.png")
        body += val(c, x + 6, 186, 180, "bold", 26, "center")
        body += f"""      <control type="image" id="{c+4}">
        <left>{x+64}</left><top>216</top><width>64</width><height>64</height>
        <aspectratio>keep</aspectratio>
      </control>
"""
        body += val(c + 1, x + 6, 286, 80, "bold", 26, "right")
        body += f"""      <control type="label">
        <left>{x+86}</left><top>286</top><width>20</width><height>26</height>
        <font>bold</font><align>center</align><label>/</label>
      </control>
"""
        body += val(c + 2, x + 106, 286, 80, "bold", 26, "left")
        body += f"""      <control type="label" id="{c+3}">
        <left>{x+6}</left><top>314</top><width>180</width><height>70</height>
        <font>small</font><textcolor>textdim</textcolor><align>center</align><aligny>top</aligny>
        <wrapmultiline>true</wrapmultiline>
      </control>
"""
    body += well(6, 402, 1000, 126, "panel_sunken_grey.png")
    body += cap(18, 414, 160, 31943) + val(10, 180, 414, 810, "bold")
    body += """      <control type="label">
        <left>18</left><top>444</top><width>160</width><height>24</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$LOCALIZE[12014]:</label>
      </control>
"""
    body += val(11, 180, 444, 810)
    return fullwindow("MyWeather", body, default="2", icon="icons24/weather.png")

def fullscreen_video():
    """Kodi draws the picture itself (CGUIWindowFullScreen::Render); a
    videowindow here would only take taps meant for DVD/Blu-ray menus (V-22).
    Labels 10-12 are the zoom / view-mode readout Kodi fills and shows for a
    few seconds after a change (FrameMove). FrameMove also sends
    SET_CONTROL_VISIBLE/HIDDEN(0): a message for id 0 is not looked up,
    CGUIControlGroup::OnMessage broadcasts it to every child, recursively,
    and CGUIControl::OnMessage shows/hides every control whose id is 0. So
    group 0 and its id-less frame toggle together with labels 10-12 (V-20),
    and EVERY id-less control anywhere in this window is force-hidden from
    window init until the next zoom change. Hence every child of group 1
    (the buffering box, V-21) carries id 1, as in Estuary; never add an
    id-less control outside group 0 here."""
    return (H + "<window>\n  <controls>\n"
      "    <control type=\"group\" id=\"0\">\n"
      "      <left>6</left><top>6</top><width>620</width><height>84</height>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"620\" /><param name=\"height\" value=\"84\" /></include>\n"
      "      <control type=\"label\" id=\"10\"><left>10</left><top>6</top><width>600</width><height>24</height><font>small</font></control>\n"
      "      <control type=\"label\" id=\"11\"><left>10</left><top>30</top><width>600</width><height>24</height><font>small</font></control>\n"
      "      <control type=\"label\" id=\"12\"><left>10</left><top>54</top><width>600</width><height>24</height><font>small</font></control>\n"
      "    </control>\n"
      "    <control type=\"group\" id=\"1\">\n"
      "      <centerleft>50%</centerleft><centertop>50%</centertop><width>240</width><height>90</height>\n"
      "      <visible>Player.Caching + Integer.IsGreater(Player.CacheLevel,0)</visible>\n"
      "      <control type=\"image\" id=\"1\">\n"
      "        <left>0</left><top>0</top><width>240</width><height>90</height>\n"
      "        <texture border=\"2\" colordiffuse=\"facetint\">panel_raised.png</texture>\n"
      "      </control>\n"
      "      <control type=\"label\" id=\"1\">\n"
      "        <left>10</left><top>10</top><width>220</width><height>28</height>\n"
      "        <font>chromebold</font><align>center</align><aligny>center</aligny>\n"
      "        <label>$LOCALIZE[15107] $INFO[Player.CacheLevel]%</label>\n"
      "      </control>\n"
      "      <control type=\"progress\" id=\"1\">\n"
      "        <left>16</left><top>50</top><width>208</width><height>24</height>\n"
      "        <info>Player.CacheLevel</info>\n"
      "      </control>\n"
      "    </control>\n  </controls>\n</window>\n")

# Skin timers (Kodi 20+, CSkinTimerManager): Timers.xml is read from the
# skin's resolution folder (CSkinInfo::LoadTimers -> GetSkinPath), so
# tallpass copies it into xml768 like any non-window file. A timer whose
# <start reset="true"> condition never holds is started only by
# Skin.TimerStart, which then restarts it from zero (CSkinTimer::Start ->
# StartZero) - exactly a "hide N seconds after the last tap" clock.
SLIDEBAR = "arthur_slidebar"
SLIDEBAR_ON = f"Skin.TimerIsRunning({SLIDEBAR})"

def timers():
    return (H + "<!-- GENERATED by genwindows.py -->\n<timers>\n"
      "  <timer>\n"
      f"    <name>{SLIDEBAR}</name>\n"
      "    <description>Picture viewer: the touch control strip hides itself 5 s after the last tap</description>\n"
      "    <start reset=\"true\">false</start>\n"
      f"    <stop>!Window.IsActive(slideshow) | Window.IsVisible(pictureinfo) | Integer.IsGreaterOrEqual(Skin.TimerElapsedSecs({SLIDEBAR}),5)</stop>\n"
      "  </timer>\n"
      "</timers>\n")

def _slide_button(cid, left, glyphs, clicks, onleft, onright, w=72, h=52):
    """A strip button with a 32 px glyph on it. glyphs: [(texture, visible)].
    The images come after the button so they draw on top of it; an image
    never takes the mouse, so taps still reach the button underneath."""
    s  = f'        <control type="button" id="{cid}">\n'
    s += f"          <left>{left}</left><top>8</top><width>{w}</width><height>{h}</height>\n"
    s += f"          <label></label><onleft>{onleft}</onleft><onright>{onright}</onright>\n"
    s += "".join(f"          <onclick>{c}</onclick>\n" for c in clicks)
    s += "        </control>\n"
    for tex, vis in glyphs:
        s += (f'        <control type="image">\n'
              f"          <left>{left + (w - 32) // 2}</left><top>{8 + (h - 32) // 2}</top><width>32</width><height>32</height>\n"
              f"          <texture>{tex}</texture>\n")
        if vis:
            s += f"          <visible>{vis}</visible>\n"
        s += "        </control>\n"
    return s

def slideshow():
    """CGUIWindowSlideShow (GUIWindowSlideShow.cpp) clears to black, draws the
    picture, then renders the skin's controls ON TOP - so nothing here may
    cover the screen. Its OnAction keeps the arrow keys (previous / next /
    pan) and the keymap turns Select into Rotate, so remote and keyboard never
    reach a skin button; they keep Kodi's own keys. A one-finger tap is a
    LeftClick (touchscreen.xml has no SlideShow tap), which reaches skin
    buttons through CGUIDialog::OnAction -> OnMouseAction; gestures (swipe,
    pinch, pan) fall through any button (CGUIButtonControl::OnMouseEvent
    handles only clicks) to the window's own OnMouseEvent.
    So: an invisible full-screen button shows a small control strip, and the
    strip hides itself again by the arthur_slidebar skin timer."""
    w("Timers", timers())
    restart = f"Skin.TimerStart({SLIDEBAR})"
    stop = f"Skin.TimerStop({SLIDEBAR})"
    playing = "Slideshow.IsActive + !Slideshow.IsPaused"
    # RunSlideShow(paths) opens a plain viewer with m_bPause true and
    # m_bSlideShow false, so IsPaused alone would hold "Paused" up over a
    # single picture: only a running slideshow can be paused.
    paused = "[Slideshow.IsActive + Slideshow.IsPaused]"
    W = 8 + 72 * 5 + 6 * 2 + 18 * 2 + 8     # prev play next | info | close
    x = [8, 86, 164, 254, 344]
    strip = (_slide_button(9801, x[0], [("icons24/prev.png", None)],
                           ["Action(PreviousPicture)", restart], 9805, 9802)
           + _slide_button(9802, x[1], [("icons24/pause.png", playing),
                                        ("icons24/play.png", f"![{playing}]")],
                           ["Action(Pause)", restart], 9801, 9803)
           + _slide_button(9803, x[2], [("icons24/next.png", None)],
                           ["Action(NextPicture)", restart], 9802, 9804)
           + _slide_button(9804, x[3], [("icons24/pictures_info.png", None)],
                           [stop, "Action(Info)"], 9803, 9805)
           + _slide_button(9805, x[4], [("icons24/exit.png", None)],
                           [stop, "Action(Stop)"], 9804, 9801))
    return (H + "<window>\n"
      "  <controls>\n"
      "    <!-- Tap anywhere on the picture: show the strip, or hide it again. -->\n"
      "    <control type=\"button\" id=\"9800\">\n"
      "      <left>0</left><top>0</top><width>1024</width><height>600</height>\n"
      "      <label></label><texturefocus /><texturenofocus />\n"
      f"      <onclick condition=\"!{SLIDEBAR_ON}\">{restart}</onclick>\n"
      f"      <onclick condition=\"{SLIDEBAR_ON}\">{stop}</onclick>\n"
      "    </control>\n"
      "    <!-- Kodi draws its 'unable to load' text in this label's font\n"
      "         (CGUIWindowSlideShow::RenderErrorMessage, LABEL_ROW1). -->\n"
      "    <control type=\"label\" id=\"10\">\n"
      "      <left>-3000</left><top>0</top><width>10</width><height>10</height>\n"
      "      <font>chromebold</font><label></label>\n"
      "    </control>\n"
      "    <!-- caption: with the strip, and whenever the slideshow is paused -->\n"
      "    <control type=\"group\">\n"
      "      <left>4</left><top>4</top><width>1016</width><height>30</height>\n"
      f"      <visible>{SLIDEBAR_ON} | {paused}</visible>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"1016\" /><param name=\"height\" value=\"30\" /></include>\n"
      "      <control type=\"label\">\n"
      "        <left>10</left><top>2</top><width>600</width><height>26</height>\n"
      "        <font>chrome</font><aligny>center</aligny><label>$INFO[Slideshow.Filename]</label>\n"
      "      </control>\n"
      "      <control type=\"label\">\n"
      "        <left>816</left><top>2</top><width>190</width><height>26</height>\n"
      "        <font>chrome</font><align>right</align><aligny>center</aligny>\n"
      "        <label>$INFO[Slideshow.SlideIndex]</label>\n"
      "      </control>\n"
      "      <control type=\"label\">\n"
      "        <left>620</left><top>2</top><width>190</width><height>26</height>\n"
      "        <font>chromebold</font><textcolor>marked</textcolor><align>right</align><aligny>center</aligny>\n"
      f"        <label>$LOCALIZE[112]</label><visible>{paused}</visible>\n"
      "      </control>\n"
      "    </control>\n"
      "    <!-- the strip: previous, play/pause, next | information | close -->\n"
      "    <control type=\"group\">\n"
      f"      <left>{(1024 - W) // 2}</left><bottom>8</bottom><width>{W}</width><height>68</height>\n"
      f"      <visible>{SLIDEBAR_ON}</visible>\n"
      f"      <include content=\"Win_Frame\"><param name=\"width\" value=\"{W}\" /><param name=\"height\" value=\"68\" /></include>\n"
      "      <!-- the strip's frame and the gaps between its buttons: a tap that\n"
      "           just misses a button keeps the strip up instead of falling\n"
      "           through to 9800 and hiding it. Mouse hits go to the last\n"
      "           control first (CGUIControlGroup::SendMouseEvent), so the\n"
      "           buttons below still win. -->\n"
      "      <control type=\"button\" id=\"9806\">\n"
      f"        <left>0</left><top>0</top><width>{W}</width><height>68</height>\n"
      "        <label></label><texturefocus /><texturenofocus />\n"
      f"        <onclick>{restart}</onclick>\n"
      "      </control>\n"
      + strip +
      "    </control>\n"
      "  </controls>\n</window>\n")

def music_vis():
    """CGUIWindowVisualisation passes the preset actions (next/previous/
    random/lock) to control id 2 (CONTROL_VIS, GUIWindowVisualisation.cpp),
    so the visualisation must carry that id. With no visualisation add-on
    chosen (Visualisation.Enabled false) the screen would be black: show the
    desktop, the fanart or a big cover instead, and keep the now-playing
    panel up rather than letting Player.ShowInfo time it out."""
    novis = "!Visualisation.Enabled"
    return (H + "<window>\n  <controls>\n"
      "    <control type=\"group\">\n"
      "      <left>0</left><top>0</top><width>1024</width><height>600</height>\n"
      f"      <visible>{novis}</visible>\n"
      "      <include>Chrome_Desktop</include>\n"
      "      <control type=\"image\">\n"
      "        <left>0</left><top>0</top><width>1024</width><height>600</height>\n"
      "        <texture background=\"true\">$INFO[Player.Art(fanart)]</texture>\n"
      "        <aspectratio>scale</aspectratio>\n"
      "      </control>\n"
      "    </control>\n"
      "    <!-- no fanart either: the cover, large, in an Arthur frame. Centred by\n"
      "         percentage, so the 4:3 layout centres it as well. -->\n"
      "    <control type=\"group\">\n"
      "      <centerleft>50%</centerleft><centertop>45%</centertop><width>312</width><height>312</height>\n"
      f"      <visible>{novis} + String.IsEmpty(Player.Art(fanart))</visible>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"312\" /><param name=\"height\" value=\"312\" /></include>\n"
      "      <control type=\"image\">\n"
      "        <left>6</left><top>6</top><width>300</width><height>300</height>\n"
      "        <texture fallback=\"DefaultAudio.png\" background=\"true\">$INFO[Player.Art(thumb)]</texture>\n"
      "        <aspectratio>keep</aspectratio>\n"
      "      </control>\n"
      "    </control>\n"
      "    <control type=\"visualisation\" id=\"2\">\n"
      "      <left>0</left><top>0</top><width>1024</width><height>600</height>\n    </control>\n"
      "    <control type=\"group\">\n"
      "      <left>6</left><top>472</top><width>1012</width><height>92</height>\n"
      f"      <visible>Player.ShowInfo | {novis}</visible>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"1012\" /><param name=\"height\" value=\"92\" /></include>\n"
      "      <control type=\"image\"><left>6</left><top>6</top><width>80</width><height>80</height>\n"
      "        <texture fallback=\"DefaultAudio.png\">$INFO[Player.Art(thumb)]</texture>\n"
      "        <aspectratio>keep</aspectratio></control>\n"
      "      <control type=\"label\"><left>98</left><top>6</top><width>902</width><height>32</height>\n"
      "        <font>bigbold</font><label>$INFO[MusicPlayer.Title]</label></control>\n"
      "      <!-- artist and album only when there are some: radio and many\n"
      "           streams have neither, and a bare ' - ' is all that showed -->\n"
      "      <control type=\"label\"><left>98</left><top>40</top><width>902</width><height>26</height>\n"
      "        <font>small</font><label>$INFO[MusicPlayer.Artist]$INFO[MusicPlayer.Album, - ]</label>\n"
      "        <visible>!String.IsEmpty(MusicPlayer.Artist)</visible></control>\n"
      "      <control type=\"label\"><left>98</left><top>40</top><width>902</width><height>26</height>\n"
      "        <font>small</font><label>$INFO[MusicPlayer.Album]</label>\n"
      "        <visible>String.IsEmpty(MusicPlayer.Artist)</visible></control>\n"
      "      <control type=\"progress\"><left>98</left><top>70</top><width>902</width><height>16</height>\n"
      "        <info>Player.Progress</info></control>\n"
      "    </control>\n  </controls>\n</window>\n")

def player_controls():
    """The desktop mini-player (task bar): what is playing, seek, transport,
    volume, shuffle/repeat with their state, and the play queue."""
    W, H_ = 660, 256
    seek = [("Player.SeekEnabled", "9980"), (None, "202")]
    body = """      <control type="image">
        <left>13</left><top>36</top><width>100</width><height>100</height>
        <texture border="2">panel_raised.png</texture>
      </control>
      <control type="image">
        <left>19</left><top>42</top><width>88</width><height>88</height>
        <texture fallback="DefaultVideo.png">$INFO[Player.Art(thumb)]</texture>
        <aspectratio>keep</aspectratio>
        <visible>Player.HasVideo</visible>
      </control>
      <control type="image">
        <left>19</left><top>42</top><width>88</width><height>88</height>
        <texture fallback="DefaultAudio.png">$INFO[Player.Art(thumb)]</texture>
        <aspectratio>keep</aspectratio>
        <visible>!Player.HasVideo</visible>
      </control>
      <control type="label">
        <left>126</left><top>38</top><width>520</width><height>26</height>
        <font>chromebold</font><label>$VAR[NowPlayingVar]</label>
      </control>
      <control type="label">
        <left>126</left><top>66</top><width>520</width><height>22</height>
        <font>chromesmall</font><textcolor>textdim</textcolor>
        <label>$INFO[Player.Time] / $INFO[Player.Duration]</label>
      </control>
      <control type="progress" id="23">
        <left>126</left><top>100</top><width>520</width><height>20</height>
        <info>Player.Progress</info>
        <visible>!Player.SeekEnabled</visible>
      </control>
      <control type="group" id="699"><left>-3000</left><top>0</top><width>10</width><height>10</height></control>
"""
    body += slider(9980, 126, 92, 520, 36, "seek", "Player.Progress",
                   visible="Player.SeekEnabled", nav={"up": "202", "down": "201"})
    body += ("      <control type=\"grouplist\" id=\"201\">\n"
             "        <left>13</left><top>146</top><width>270</width><height>48</height>\n"
             "        <orientation>horizontal</orientation><itemgap>6</itemgap>\n"
             + navs("        ", up=seek, down="202", left="9983", right="9982"))
    body += icon_radio(600, "prev", 60, 48, ["PlayerControl(Previous)"], size=24, hit=OSD_HIT)
    body += icon_radio(602, "play", 60, 48, ["PlayerControl(Play)"], size=24,
                       selected=PLAYING, glyph_on="pause", hit=OSD_HIT)
    body += icon_radio(603, "stop", 60, 48, ["PlayerControl(Stop)"], size=24, hit=OSD_HIT)
    body += icon_radio(605, "next", 60, 48, ["PlayerControl(Next)"], size=24, hit=OSD_HIT)
    body += "      </control>\n"
    body += icon_radio(9982, "audio", 60, 48, ["Mute"], indent=6, size=24,
                       selected="Player.Muted", glyph_on="audio_muted", pos=(290, 146),
                       nav={"up": seek, "down": "202", "left": "201", "right": "9983"},
                       hit=OSD_HIT)
    body += slider(9983, 356, 152, 290, 36, "volume", "Player.Volume",
                   enable="!Player.Passthrough", nav={"up": seek, "down": "202"})
    body += osd_buttons(202, 202, [
        (607, 140, "$LOCALIZE[191]", ["PlayerControl(Random)"], None, "Playlist.IsRandom"),
        (704, 150, "$VAR[OSDRepeatLabelVar]", ["PlayerControl(Repeat)"], None),
        (87, 110, "$LOCALIZE[559]", ["Dialog.Close(PlayerControls)",
                                     ("Player.HasVideo", "ActivateWindow(VideoPlaylist)"),
                                     ("!Player.HasVideo", "ActivateWindow(MusicPlaylist)")], None),
        (9951, 100, "$LOCALIZE[15067]", ["Dialog.Close(PlayerControls)"], None),
    ], "201", seek[:1] + [(None, "201")], left=13, width=W - 26)
    return dialog("PlayerControls", W, H_, body, default="602", default_always=True,
                  icon="icons24/audio.png", heading=False, title="$LOCALIZE[31907]")

# ====================================================== generic fallbacks
LISTY   = {"list","panel","fixedlist","wraplist"}
PRESSY  = {"button","togglebutton","radiobutton","spincontrolex","sliderex","edit","colorbutton"}

# Estuary's own controls that inventory.py copied as if Kodi used them: no
# Kodi C++ window drives these ids, so a generic window drew them as dead
# blank buttons. 799 is Estuary's TouchBackButton, LoginScreen 20 its power
# button, EventLog 501 its Settings shortcut, MyPVRGuide 100-105/302 its
# quick-nav and "go to playlist"; the guide class itself uses only 2/3/4,
# 11 and 28 (5-8/10/31 belong to the channel/recording/timer windows).
ESTUARY_ONLY = {
 "*": {799},
 "LoginScreen": {20},
 "EventLog": {501},
 "MyPVRGuide": {5, 6, 7, 8, 10, 31, 100, 101, 102, 103, 104, 105, 302},
}

def kodi_ids(name, meta):
    drop = ESTUARY_ONLY["*"] | ESTUARY_ONLY.get(name, set())
    return {int(k): v for k, v in meta["ids"].items() if int(k) not in drop}

# Captions for Kodi-driven controls Kodi does not label itself (checked in
# each window's C++: it writes only values / label2 / selected state on
# these). A tuple is (label, altlabel) for a togglebutton.
LABELS = {
 # GUIWindowEventLog.cpp labels 21/22 itself; 4 is CGUIMediaWindow's sort
 # direction toggle (selected = descending)
 "EventLog": {4: ("$LOCALIZE[580]: $LOCALIZE[584]", "$LOCALIZE[580]: $LOCALIZE[585]"),
              20: "$LOCALIZE[192]"},
 # GUIWindowSettingsProfile.cpp: 4 toggles the login screen, 5 picks the
 # auto-login profile; neither is labelled by Kodi
 "SettingsProfile": {4: "$LOCALIZE[20096]", 5: "$LOCALIZE[33084]"},
}
# extra markup for those buttons: Kodi writes no label2 on Auto login, so
# the skin shows the chosen profile (as Estuary does); Kodi only reads the
# setting while the login screen is off, so the button is too
EXTRAS = {
 "SettingsProfile": {5: "<label2>$INFO[System.ProfileAutoLogin]</label2>\n"
                        "<enable>!System.HasLoginScreen</enable>"},
}
# Ids each window's C++ labels by itself (SET_CONTROL_LABEL) - used by
# labelcheck.py so a blank caption anywhere else fails the build.
# generic(): width of the button column where its captions need more room
COLUMN_W = {"EventLog": 400}
KODI_LABELLED = {
 "EventLog": {21, 22},
 "DialogColorPicker": {7},
 "SmartPlaylistRule": {15, 16, 17},          # 17: the value field (label2)
 "DialogKeyboard": set(range(100, 173)) | {312},   # the keys, and the text field
}

def caption(label):
    if label is None:
        return ""
    if isinstance(label, tuple):
        return f"<label>{label[0]}</label><altlabel>{label[1]}</altlabel>"
    return f"<label>{label}</label>"

def item(ct, cid, w, h=30, label=None, extra="", align="left", indent=8):
    """One child of a grouplist (no position: the grouplist places it)."""
    sp = " " * indent
    s  = f'{sp}<control type="{ct}" id="{cid}">\n'
    s += f"{sp}  <width>{w}</width><height>{h}</height>\n"
    if align == "left":
        s += f"{sp}  <align>left</align><textoffsetx>12</textoffsetx>\n"
    else:
        s += f"{sp}  <align>center</align>\n"
    if label is not None:
        s += f"{sp}  {caption(label)}\n"
    if extra:
        s += textwrap.indent(extra.rstrip("\n"), sp + "  ") + "\n"
    s += f"{sp}</control>\n"
    return s

def vgroup(gid, l, t, wd, ht, children, nav, sb=None, gap=3):
    """A vertical grouplist. nav: dict of onup/ondown/onleft/onright. With
    sb, a scrollbar (pagecontrol) on its right edge - Touch mode / Extra
    large rows (46 px, sizepass.py) can need more room than it has."""
    gw = wd - (22 if sb else 0)
    s  = f'      <control type="grouplist"' + (f' id="{gid}"' if gid else "") + ">\n"
    s += f"        <left>{l}</left><top>{t}</top><width>{gw}</width><height>{ht}</height>\n"
    s += f"        <orientation>vertical</orientation><itemgap>{gap}</itemgap>\n"
    s += "        " + "".join(f"<{k}>{v}</{k}>" for k, v in nav.items()) + "\n"
    if sb:
        s += f"        <pagecontrol>{sb}</pagecontrol>\n"
    s += children
    s += "      </control>\n"
    if sb:
        s += (f'      <control type="scrollbar" id="{sb}">\n'
              f"        <left>{l + wd - 18}</left><top>{t}</top><width>18</width><height>{ht}</height>\n"
              f"        <onleft>{gid}</onleft><onright>{nav.get('onright', gid)}</onright>\n"
              "      </control>\n")
    return s

ROWH = 40   # fixed (horizontal) button rows: horizontal grouplists do not grow

def hrow(gid, l, t, wd, buttons, nav, bw=180, h=ROWH, gap=8):
    """A centred horizontal row of buttons: (id, label[, extra])."""
    s  = f'      <control type="grouplist"' + (f' id="{gid}"' if gid else "") + ">\n"
    s += f"        <left>{l}</left><top>{t}</top><width>{wd}</width><height>{h}</height>\n"
    s += f"        <orientation>horizontal</orientation><align>center</align><itemgap>{gap}</itemgap>\n"
    s += "        " + "".join(f"<{k}>{v}</{k}>" for k, v in nav.items()) + "\n"
    for b in buttons:
        cid, lab = b[0], b[1]
        extra = b[2] if len(b) > 2 else ""
        ct = b[3] if len(b) > 3 else "button"
        s += item(ct, cid, bw, h, lab, extra, align="center")
    s += "      </control>\n"
    return s

def rows(iw, label="$INFO[ListItem.Label]", label2="$INFO[ListItem.Label2]",
         icon="$INFO[ListItem.Icon]", swatch=False, rowh=28):
    """item/focused layouts drawn here rather than with Arthur_ItemLayout, for
    rows that show something else (channel number, a colour swatch). Text
    controls are rowh tall so sizepass.py stretches them for Extra large."""
    out = ""
    for focused in (False, True):
        tag = "focusedlayout" if focused else "itemlayout"
        out += f'        <{tag} height="{rowh}" width="{iw}">\n'
        if focused:
            out += (f"          <control type=\"image\"><left>0</left><top>0</top><width>{iw}</width>"
                    f"<height>{rowh}</height><texture colordiffuse=\"select\">fill.png</texture></control>\n")
        tx = 26
        if swatch:
            # GUIDialogColorPicker.cpp puts the ARGB value in Label2; the
            # <colordiffuse> element resolves per item (Estuary does the same)
            out += ("          <control type=\"image\"><left>4</left><top>4</top><width>44</width>"
                    "<height>20</height><texture>fill_black.png</texture></control>\n"
                    "          <control type=\"image\"><left>5</left><top>5</top><width>42</width>"
                    "<height>18</height><texture>fill.png</texture>"
                    "<colordiffuse>$INFO[ListItem.Label2]</colordiffuse></control>\n")
            tx = 56
        elif icon:
            out += ("          <control type=\"image\"><left>4</left><top>6</top><width>16</width>"
                    f"<height>16</height><texture>{icon}</texture></control>\n")
        col = "textinv" if focused else "text"
        font = "bold" if focused else "normal"
        out += (f"          <control type=\"label\"><left>{tx}</left><top>0</top><width>{iw - tx - 8}</width>"
                f"<height>{rowh}</height><font>{font}</font><textcolor>{col}</textcolor>"
                f"<aligny>center</aligny><label>{label}</label></control>\n")
        if label2:
            col2 = "textinv" if focused else "textdim"
            out += (f"          <control type=\"label\"><left>0</left><top>0</top><width>{iw - 8}</width>"
                    f"<height>{rowh}</height><font>small</font><textcolor>{col2}</textcolor>"
                    f"<align>right</align><aligny>center</aligny><label>{label2}</label></control>\n")
        out += f"        </{tag}>\n"
    return out

def xlist(cid, sb, l, t, wd, ht, nav, layouts=None, kind="list", sbright=None):
    """A sunken well with a list and its scrollbar. nav: onup/ondown/onleft;
    the list's onright is its scrollbar, the scrollbar's onright sbright."""
    iw = wd - 24
    if layouts is None:
        layouts = (f'        <itemlayout height="28" width="{iw}">\n'
                   f'          <include content="Arthur_ItemLayout"><param name="width" value="{iw-8}" /></include>\n'
                   f'        </itemlayout>\n'
                   f'        <focusedlayout height="28" width="{iw}">\n'
                   f'          <include content="Arthur_FocusedLayout"><param name="width" value="{iw}" /></include>\n'
                   f'        </focusedlayout>\n')
    elif callable(layouts):
        layouts = layouts(iw)
    s  = well(l, t, wd, ht, "panel_sunken.png")
    s += f'      <control type="{kind}" id="{cid}">\n'
    s += f"        <left>{l+3}</left><top>{t+3}</top><width>{iw}</width><height>{ht-6}</height>\n"
    s += "        " + "".join(f"<{k}>{v}</{k}>" for k, v in nav.items()) + f"<onright>{sb}</onright>\n"
    s += f"        <pagecontrol>{sb}</pagecontrol>\n"
    s += layouts
    s += "      </control>\n"
    s += (f'      <control type="scrollbar" id="{sb}">\n'
          f"        <left>{l+wd-21}</left><top>{t+3}</top><width>18</width><height>{ht-6}</height>\n"
          f"        <onleft>{cid}</onleft><onright>{sbright or nav.get('onleft', cid)}</onright>\n"
          "      </control>\n")
    return s

def tlabel(cid, wd=560, label=None):
    """A label Kodi writes the heading into, sitting on the title bar."""
    return (f'      <control type="label"' + (f' id="{cid}"' if cid else "") + ">\n"
            f"        <left>29</left><top>3</top><width>{wd}</width><height>26</height>\n"
            "        <font>chromebold</font><textcolor>titletext</textcolor>\n"
            "        <align>left</align><aligny>center</aligny>\n"
            + (f"        <label>{label}</label>\n" if label else "") +
            "      </control>\n")

def caplabel(l, t, wd, label, cid=None, h=24, font="chromesmall", col="textdim", align="left"):
    return (f'      <control type="label"' + (f' id="{cid}"' if cid else "") + ">\n"
            f"        <left>{l}</left><top>{t}</top><width>{wd}</width><height>{h}</height>\n"
            f"        <font>{font}</font><textcolor>{col}</textcolor><align>{align}</align><aligny>center</aligny>\n"
            + (f"        <label>{label}</label>\n" if label else "") +
            "      </control>\n")

def generic(name, meta, as_dialog=False):
    ids   = kodi_ids(name, meta)
    views = meta.get("views","")
    labels = LABELS.get(name, {})
    title = TITLES.get(name) if as_dialog else None
    placed = set()
    body = ""
    # Dialog_Heading owns id 1 - unless Kodi writes no id 1 here and the
    # title comes from TITLES (dialog() then emits no Dialog_Heading)
    if as_dialog and not title: placed.add(1)

    if as_dialog:
        WD, HT = 900, 500
        ox, oy, aw, ah = 10, 36, 880, 420
    else:
        WD, HT = 1012, 534
        ox, oy, aw, ah = 6, 34, 1000, 494

    press = sorted((i,t) for i,t in ids.items() if t in PRESSY)
    lists = sorted((i,t) for i,t in ids.items() if t in LISTY)
    texts = sorted((i,t) for i,t in ids.items() if t == "textbox")
    labs  = sorted((i,t) for i,t in ids.items() if t in ("label","fadelabel") and i not in placed)
    bars  = sorted((i,t) for i,t in ids.items() if t in ("progress","slider"))
    sbs   = sorted(i for i,t in ids.items() if t == "scrollbar")

    # Up from the button column: the title-bar close box in a dialog (the
    # task bar, 9100, exists only in full windows); Down: the list, or wrap.
    first = str(lists[0][0]) if lists else (str(press[0][0]) if press else "")
    gl_up   = "9903" if as_dialog else "9100"
    gl_down = first if as_dialog else "9100"

    lx, lw = ox, (COLUMN_W.get(name, 300) if lists or texts else aw)
    if press:
        body += well(lx, oy, lw, ah, "panel_sunken_grey.png")
        # every pressable is placed; Touch mode / Extra large rows are 46 px
        # (sizepass.py), so a long column scrolls instead of being cut off
        sb = 9601 if len(press) * 49 > ah - 12 else None
        extras = EXTRAS.get(name, {})
        kids = "".join(item(ct, cid, lw - 16 - (22 if sb else 0), 30, labels.get(cid), extras.get(cid, ""))
                       for cid, ct in press)
        # Right: the list; with no list, nowhere (Right used to land on the
        # close box / Start button, one Select away from leaving)
        nav = {"onup": gl_up, "ondown": gl_down}
        if lists:
            nav["onright"] = first
        body += vgroup(9600 if sb else None, lx + 8, oy + 6, lw - 16, ah - 12, kids, nav, sb=sb)
        placed.update(cid for cid, _ in press)

    rx = ox + lw + 6 if press else ox
    rw = (ox + aw) - rx
    ry, rh = oy, ah

    if lists:
        cid, ct = lists[0]
        sb = sbs[0] if sbs else 9602
        lh = rh if not (texts or labs) else rh - 100
        body += list_block(cid, sb, rx, ry, rw, lh, rowh=28,
                           onleft=str(press[0][0]) if press else str(cid),
                           ondown=str(cid) if as_dialog else "9100")
        placed.add(cid); placed.add(sb)
        ry += lh + 6; rh -= lh + 6

    if texts and rh > 40:
        cid, _ = texts[0]
        body += well(rx, ry, rw, rh, "panel_sunken.png")
        body += (f"      <control type=\"textbox\" id=\"{cid}\">\n"
                 f"        <left>{rx+8}</left><top>{ry+6}</top><width>{rw-16}</width><height>{rh-12}</height>\n"
                 f"        <font>small</font>\n      </control>\n")
        placed.add(cid); ry += rh; rh = 0

    if labs and rh > 24:
        body += well(rx, ry, rw, rh, "panel_sunken_grey.png")
        y = ry + 6
        for cid, ct in labs:
            if y + 24 > ry + rh: break
            body += (f"      <control type=\"{ct}\" id=\"{cid}\">\n"
                     f"        <left>{rx+10}</left><top>{y}</top><width>{rw-20}</width><height>24</height>\n"
                     f"        <font>small</font>\n      </control>\n")
            placed.add(cid); y += 26

    for cid, ct in bars:
        body += (f"      <control type=\"{ct}\" id=\"{cid}\">\n"
                 f"        <left>{ox}</left><top>{oy+ah-24}</top><width>{aw}</width><height>20</height>\n"
                 f"      </control>\n")
        placed.add(cid)

    body += stubs(ids, placed)
    default = first
    if as_dialog:
        return dialog(name, WD, HT, body, default=default, title=title)
    live = [v.strip() for v in views.split(",") if v.strip() and int(v.strip()) in placed]
    return fullwindow(name, body, default=default, views=",".join(live))

# ====================================================== windows Kodi drives by id
# Each of these used to be a generic() column of blank buttons. Ids, and
# which of them Kodi labels, are from the window's C++ (Kodi Omega); the
# captions are Kodi's own strings, as Estuary uses them.

def pvr_channel_manager():
    """GUIDialogPVRChannelManager.cpp: 4 OK, 5 Apply, 6 Cancel, 7 Active,
    8 Name (label2 only), 9 Icon, 12 Use guide, 13 Guide source (values),
    14 Parental lock, 20 channel list, 30 Group manager, 31 New channel,
    34 TV/Radio, 35 Refresh logos. Kodi labels none of them."""
    name = "DialogPVRChannelManager"
    ids = kodi_ids(name, INV[name])
    def chan(iw, rowh=28):
        """Number and name as edited, the backend on the right, and the state
        Kodi keeps per channel (properties, GUIDialogPVRChannelManager.cpp):
        a hidden channel (!ActiveChannel) in the dim colour, a padlock when
        ParentalLocked, a bar in the marked colour on the left edge once
        the channel has unsaved changes (Changed). The picture is the
        channel's Icon property, as edited."""
        name = "$INFO[ListItem.Property(Number),, ]$INFO[ListItem.Property(Name)]"
        out = ""
        for focused in (False, True):
            tag = "focusedlayout" if focused else "itemlayout"
            out += f'        <{tag} height="{rowh}" width="{iw}">\n'
            if focused:
                out += (f'          <control type="image"><left>0</left><top>0</top><width>{iw}</width>'
                        f'<height>{rowh}</height><texture colordiffuse="select">fill.png</texture></control>\n')
            out += ('          <control type="image"><left>0</left><top>0</top><width>4</width>'
                    f'<height>{rowh}</height><texture colordiffuse="marked">fill.png</texture>'
                    '<visible>ListItem.Property(Changed)</visible></control>\n')
            out += ('          <control type="image"><left>8</left><top>6</top><width>16</width><height>16</height>'
                    '<texture fallback="icons24/livetv.png">$INFO[ListItem.Property(Icon)]</texture>'
                    '<aspectratio>keep</aspectratio></control>\n')
            out += ('          <control type="image"><left>28</left><top>6</top><width>16</width><height>16</height>'
                    '<texture>icons24/masterlock.png</texture>'
                    '<visible>ListItem.Property(ParentalLocked)</visible></control>\n')
            font = "bold" if focused else "normal"
            for col, vis in ((("textinv", ""),) if focused else
                             (("text", "<visible>ListItem.Property(ActiveChannel)</visible>"),
                              ("textdim", "<visible>!ListItem.Property(ActiveChannel)</visible>"))):
                out += (f'          <control type="label"><left>48</left><top>0</top><width>{iw - 150}</width>'
                        f'<height>{rowh}</height><font>{font}</font><textcolor>{col}</textcolor>'
                        f'<aligny>center</aligny><label>{name}</label>{vis}</control>\n')
            col2 = "textinv" if focused else "textdim"
            out += (f'          <control type="label"><left>{iw - 98}</left><top>0</top><width>90</width>'
                    f'<height>{rowh}</height><font>small</font><textcolor>{col2}</textcolor>'
                    f'<align>right</align><aligny>center</aligny>'
                    f'<label>$INFO[ListItem.Property(ClientName)]</label></control>\n')
            out += f"        </{tag}>\n"
        return out
    body  = xlist(20, 60, 10, 36, 420, 400,
                  {"onup": "9903", "ondown": "4", "onleft": "9002"},
                  layouts=chan, sbright="9002")
    radio = "String.IsEqual(Window(pvrchannelmanager).Property(IsRadio),true)"
    kids  = item("radiobutton", 7, 420, 30, "$LOCALIZE[19074]")
    kids += item("edit", 8, 420, 30, "$LOCALIZE[19201]")
    kids += item("button", 9, 420, 30, "$LOCALIZE[19202]")
    kids += item("radiobutton", 12, 420, 30, "$LOCALIZE[19206]")
    kids += item("spincontrolex", 13, 420, 30, "$LOCALIZE[19200]")
    kids += item("radiobutton", 14, 420, 30, "$LOCALIZE[19267]")
    kids += item("button", 35, 420, 30, "$LOCALIZE[19041]")
    kids += item("button", 31, 420, 30, "$LOCALIZE[19204]")
    kids += item("button", 30, 420, 30, "$LOCALIZE[19205]")
    # TV/Radio: the toggle shows the list it switches to
    kids += item("togglebutton", 34, 420, 30, ("$LOCALIZE[19024]", "$LOCALIZE[19023]"),
                 f"<usealttexture>{radio}</usealttexture>")
    body += well(438, 36, 452, 400, "panel_sunken_grey.png")
    body += vgroup(9002, 446, 42, 442, 388, kids,
                   {"onup": "9903", "ondown": "4", "onleft": "20", "onright": "20"}, sb=9603)
    body += hrow(9000, 10, 446, 880, [(4, "$LOCALIZE[186]"), (5, "$LOCALIZE[14070]"),
                                      (6, "$LOCALIZE[222]")],
                 {"onup": "20"}, bw=280)
    placed = {4, 5, 6, 7, 8, 9, 12, 13, 14, 20, 30, 31, 34, 35, 60}
    body += stubs(ids, placed)
    return dialog(name, 900, 498, body, default="20", icon="icons24/pvr_manager.png",
                  title=TITLES[name])

def pvr_group_manager():
    """GUIDialogPVRGroupManager.cpp: 13 the groups, 11 channels not in the
    group, 12 channels in it - all three must be on screen; 20/21/22 are
    their headings (Kodi writes them). 25 Hide group, 26 New, 27 Rename,
    28 Delete, 29 OK, 34 TV/Radio, 35 regenerate thumbnails - unlabelled."""
    name = "DialogPVRGroupManager"
    ids = kodi_ids(name, INV[name])
    W = 1000
    cw = (W - 20 - 16) // 3          # three columns, 8 px apart
    xs = [10, 10 + cw + 8, 10 + 2 * (cw + 8)]
    body  = caplabel(xs[0] + 4, 36, cw - 8, "$LOCALIZE[19146]$INFO[Container(13).NumItems, (,)]")
    body += caplabel(xs[1] + 4, 36, cw - 8, None, cid=21)
    body += caplabel(xs[2] + 4, 36, cw - 8, None, cid=22)
    lt, lh = 62, 300
    order = [(13, 73), (11, 71), (12, 72)]
    for k, (cid, sb) in enumerate(order):
        nxt = order[(k + 1) % 3][0]
        prv = order[k - 1][0]
        body += xlist(cid, sb, xs[k], lt, cw, lh,
                      {"onup": "9903", "ondown": "9001", "onleft": str(prv)},
                      layouts=(lambda iw: rows(iw, label2="$INFO[ListItem.Property(ClientName)]")) if cid == 13 else None,
                      sbright=str(nxt))
    radio = "String.IsEqual(Window(pvrgroupmanager).Property(IsRadio),true)"
    bw = (W - 20 - 24) // 4
    body += hrow(9001, 10, 370, W - 20,
                 [(26, "$LOCALIZE[31830]"), (27, "$LOCALIZE[31831]"), (28, "$LOCALIZE[31832]"),
                  (25, "$LOCALIZE[19289]", "", "radiobutton")],
                 {"onup": "13", "ondown": "9002"}, bw=bw)
    body += hrow(9002, 10, 418, W - 20,
                 [(35, "$LOCALIZE[13315]"),
                  (34, ("$LOCALIZE[19174]", "$LOCALIZE[19173]"), f"<usealttexture>{radio}</usealttexture>",
                   "togglebutton"),
                  (29, "$LOCALIZE[186]")],
                 {"onup": "9001"}, bw=(W - 20 - 16) // 3)
    # 20 = the selected group's name; the groups column already shows it
    placed = {11, 12, 13, 21, 22, 25, 26, 27, 28, 29, 34, 35, 71, 72, 73}
    body += stubs(ids, placed)
    return dialog(name, W, 470, body, default="13", icon="icons24/pvr_groups.png",
                  title=TITLES[name])

def pvr_guide_search():
    """GUIDialogPVRGuideSearch.cpp ids 9-31: it only fills values, label2
    and selected states, so every caption is the skin's (Estuary's)."""
    name = "DialogPVRGuideSearch"
    ids = kodi_ids(name, INV[name])
    body  = """      <control type="edit" id="9">
        <left>10</left><top>36</top><width>940</width><height>36</height>
        <label>$LOCALIZE[19133]</label>
        <onup>9903</onup><ondown>5000</ondown>
      </control>
"""
    body += caplabel(14, 74, 932, "$LOCALIZE[19001]", h=22)
    left  = [("radiobutton", 10, 19134), ("radiobutton", 11, 19135), ("edit", 14, 19128),
             ("edit", 15, 19129), ("radiobutton", 30, 19339), ("spincontrolex", 18, 515),
             ("radiobutton", 20, 19132), ("radiobutton", 22, 19123), ("radiobutton", 24, 19124)]
    right = [("spincontrolex", 12, 19130), ("spincontrolex", 13, 19131), ("edit", 16, 19126),
             ("edit", 17, 19127), ("radiobutton", 31, 19340), ("radiobutton", 19, 19121),
             ("spincontrolex", 21, 19141), ("spincontrolex", 23, 19148), ("radiobutton", 27, 19125)]
    gt, gh = 100, 330
    for gid, sb, x, col, other in ((5000, 5001, 10, left, 6000), (6000, 6001, 484, right, 5000)):
        body += well(x, gt, 466, gh, "panel_sunken_grey.png")
        kids = "".join(item(ct, cid, 432, 30, f"$LOCALIZE[{sid}]") for ct, cid, sid in col)
        body += vgroup(gid, x + 6, gt + 6, 454, gh - 12, kids,
                       {"onup": "9", "ondown": "9000", "onleft": str(other), "onright": str(other)}, sb=sb)
    body += hrow(9000, 10, 440, 940, [(26, "$LOCALIZE[137]"), (29, "$LOCALIZE[190]"),
                                      (28, "$LOCALIZE[13007]"), (25, "$LOCALIZE[222]")],
                 {"onup": "5000", "ondown": "9"}, bw=226)
    placed = {cid for _, cid, _ in left + right} | {9, 25, 26, 28, 29}
    body += stubs(ids, placed)
    return dialog(name, 960, 492, body, default="9", icon="icons24/pvr_search.png",
                  title=TITLES[name])

def smartplaylist_editor():
    """GUIDialogSmartPlaylistEditor.cpp (a dialog, despite the file name):
    2 heading (Kodi writes 21432), 10 rules, 12 name, 13 add rule, 14 remove
    rule, 16 match, 17 limit, 18 order, 19 direction, 20 OK, 21 Cancel,
    22 type, 23 group by, 24 mixed groups. Kodi writes only label2/values."""
    name = "SmartPlaylistEditor"
    ids = kodi_ids(name, INV[name])
    body  = tlabel(2, 770)
    kids  = item("button", 22, 400, 30, "$LOCALIZE[467]")
    kids += item("button", 12, 400, 30, "$LOCALIZE[21433]")
    kids += item("button", 16, 400, 30, "$LOCALIZE[21424]")
    kids += item("button", 17, 400, 30, "$LOCALIZE[21427]")
    kids += item("button", 18, 400, 30, "$LOCALIZE[21429]")
    kids += item("button", 19, 400, 30, "$LOCALIZE[580]")
    kids += item("button", 23, 400, 30, "$LOCALIZE[21458]")
    kids += item("radiobutton", 24, 400, 30, "$LOCALIZE[21458]: $LOCALIZE[21459]")
    body += well(10, 36, 440, 388, "panel_sunken_grey.png")
    body += vgroup(500, 16, 42, 428, 376, kids,
                   {"onup": "9903", "ondown": "9000", "onleft": "10", "onright": "10"}, sb=501)
    body += xlist(10, 60, 458, 36, 432, 340,
                  {"onup": "9903", "ondown": "9010", "onleft": "500"}, sbright="500")
    body += hrow(9010, 458, 384, 432, [(13, "$LOCALIZE[15019]"), (14, "$LOCALIZE[1210]")],
                 {"onup": "10", "ondown": "9000"}, bw=200)
    body += hrow(9000, 10, 432, 880, [(20, "$LOCALIZE[186]"), (21, "$LOCALIZE[222]")],
                 {"onup": "500"}, bw=240)
    placed = {2, 10, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 500}
    body += stubs(ids, placed)
    return dialog(name, 900, 484, body, default="22", icon="icons24/smartplaylist.png",
                  heading=False)

def smartplaylist_rule():
    """GUIDialogSmartPlaylistRule.cpp: 15 field and 16 operator (Kodi labels
    both), 17 value (label2), 18 OK, 19 Cancel, 20 Browse."""
    name = "SmartPlaylistRule"
    ids = kodi_ids(name, INV[name])
    kids  = item("button", 15, 664, 30)
    kids += item("button", 16, 664, 30)
    kids += item("edit", 17, 664, 30)
    kids += item("button", 20, 664, 30, "$LOCALIZE[1024]")
    body  = well(10, 36, 680, 212, "panel_sunken_grey.png")
    body += vgroup(9001, 18, 42, 664, 200, kids, {"onup": "9903", "ondown": "9000"})
    body += hrow(9000, 10, 256, 680, [(18, "$LOCALIZE[186]"), (19, "$LOCALIZE[222]")],
                 {"onup": "9001"}, bw=240)
    placed = {15, 16, 17, 18, 19, 20}
    body += stubs(ids, placed)
    return dialog(name, 700, 308, body, default="15", icon="icons24/smartrule.png",
                  title=TITLES[name])

def music_playlist_editor():
    """GUIWindowMusicPlaylistEditor.cpp: 6 Load, 7 Save, 8 Clear (unlabelled),
    50 the source browser, 100 the playlist being built (generic() had
    parked it off screen), 12 / 101 their item counts. Songs go in and out
    through the context menu (long-press), so the window says so."""
    name = "MyMusicPlaylistEditor"
    ids = kodi_ids(name, INV[name])
    body  = well(6, 34, 200, 494, "panel_sunken_grey.png")
    kids  = item("button", 6, 184, 30, "$LOCALIZE[502]")
    kids += item("button", 7, 184, 30, "$LOCALIZE[190]")
    kids += item("button", 8, 184, 30, "$LOCALIZE[192]")
    body += vgroup(9000, 14, 40, 184, 160, kids, {"onup": "9100", "ondown": "9100", "onright": "50"})
    body += f"""      <control type="textbox">
        <left>14</left><top>208</top><width>184</width><height>312</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$LOCALIZE[31833]</label>
      </control>
"""
    body += well(212, 34, 392, 26, "panel_sunken_grey.png")
    body += caplabel(218, 35, 380, None, cid=12)
    body += xlist(50, 60, 212, 64, 392, 464, {"onup": "50", "ondown": "9100", "onleft": "9000"},
                  sbright="100")
    body += well(610, 34, 396, 26, "panel_sunken_grey.png")
    body += caplabel(616, 35, 384, None, cid=101)
    body += xlist(100, 61, 610, 64, 396, 464, {"onup": "100", "ondown": "9100", "onleft": "60"},
                  sbright="9000")
    placed = {6, 7, 8, 12, 50, 60, 61, 100, 101}
    body += stubs(ids, placed)
    return fullwindow(name, body, default="50", views="50", icon="icons24/playlist.png")

def screen_calibration():
    """GUIWindowSettingsScreenCalibration.cpp: movers 8 (top left), 9 (bottom
    right), 10 (subtitles), 12 (reset), resize 11 (pixel ratio); Kodi places
    and sizes them itself, but they draw only their own textures - the
    stubs had none, so nothing was visible. Labels 2/3/4: resolution, what
    the marker does, its value. Full screen, no chrome over the edges being
    calibrated; text centred across 100% width like Estuary's.

    No skin button here on purpose. The window keeps m_needsScaling false
    except inside DoProcess/DoRender, so a skin control is DRAWN scaled
    (skin to screen) but CGUIWindow::OnMouseAction hit-tests it in unscaled
    screen pixels: on the 2048x1536 panel a button showed at twice its
    position and answered taps somewhere else. Any click also sends
    GUI_MSG_CLICKED -> NextControl(), which resets the calibration when the
    reset marker is current. Leaving is Kodi's own: Back, a right click, or
    on touch a long press (touchscreen.xml: longpress = RightClick, which
    CGUIWindow::OnMouseEvent turns into ACTION_PREVIOUS_MENU when no control
    takes it) or a two-finger swipe left (Back). Label 31834 says so."""
    def mover(cid, kind, w, h, tex, events, speed="acceleration=\"180\" maxvelocity=\"300\" resettimeout=\"200\" delta=\"1\""):
        ev = "".join(f'<eventconfig type="{e}" />' for e in events)
        ms = f"\n      <movingspeed {speed}>{ev}</movingspeed>" if events else ""
        return (f'    <control type="{kind}" id="{cid}">\n'
                f"      <left>0</left><top>0</top><width>{w}</width><height>{h}</height>\n"
                f'      <texturefocus colordiffuse="select">{tex}</texturefocus>\n'
                f"      <texturenofocus>{tex}</texturenofocus>{ms}\n"
                "    </control>\n")
    lab = lambda cid, t, font, label="", h=26, wrap=False: (
        f'    <control type="label"' + (f' id="{cid}"' if cid else "") + ">\n"
        f"      <left>0</left><top>{t}</top><width>100%</width><height>{h}</height>\n"
        f"      <font>{font}</font><textcolor>text</textcolor><align>center</align><aligny>center</aligny>\n"
        + ("      <wrapmultiline>true</wrapmultiline>\n" if wrap else "")
        + (f"      <label>{label}</label>\n" if label else "") + "    </control>\n")
    s  = H + "<window>\n  <defaultcontrol>8</defaultcontrol>\n"
    s += "  <backgroundcolor>desktop</backgroundcolor>\n  <controls>\n"
    s += ("    <control type=\"image\">\n      <left>0</left><top>0</top><width>100%</width><height>100%</height>\n"
          "      <texture colordiffuse=\"desktop\">fill.png</texture>\n    </control>\n")
    # sizes: 8/9 are drawn as given; 10-12 Kodi rescales from a 1920x1080
    # design (10 must keep 40 px clear above and below the bar). The
    # textures are media/calibrate/ (mkmedia.py), not registry icons.
    s += mover(8, "mover", 96, 96, "calibrate/cal_tl.png", ("up", "down", "left", "right"))
    s += mover(9, "mover", 96, 96, "calibrate/cal_br.png", ("up", "down", "left", "right"))
    s += mover(11, "resize", 500, 500, "calibrate/cal_ratio.png", ("left", "right"),
               speed="acceleration=\"140\" maxvelocity=\"300\" resettimeout=\"180\" delta=\"1\"")
    s += mover(10, "mover", 380, 90, "calibrate/cal_sub.png", ("up", "down"))
    s += mover(12, "mover", 100, 100, "calibrate/cal_reset.png", ())
    s += lab(None, 40, "bigbold", "$LOCALIZE[214]")
    s += lab(2, 68, "normal")
    s += lab(3, 96, "bold")
    s += lab(4, 124, "normal")
    s += lab(None, 152, "small", "$LOCALIZE[31834]", h=48, wrap=True)
    s += "  </controls>\n</window>\n"
    return s

def login_screen():
    """GUIWindowLoginScreen.cpp: 52 the profiles, 2 heading (20115), 3 the
    selected profile. The login screen runs as the master profile and skin
    onclicks bypass its OnAction filter, so it must not carry the task bar
    (Start = Home, Settings) - only a power button (ShutdownMenu: power,
    log off, master mode). The power button is an ordinary ROWH (40 px)
    dialog row inside the frame, so it is a real touch target in every
    mode; the dialogs it can lead to (power menu, keyboard, numeric pad)
    get login-safe title-bar boxes (LOGIN_SAFE)."""
    name = "LoginScreen"
    ids = kodi_ids(name, INV[name])
    body  = caplabel(16, 38, 980, None, cid=2, h=26, font="bigbold", col="text")
    body += caplabel(16, 66, 980, None, cid=3, h=22, font="small")
    layouts = lambda iw: (
        f'        <itemlayout height="56" width="{iw}">\n'
        f'          <control type="image"><left>6</left><top>4</top><width>48</width><height>48</height>'
        f'<texture fallback="icons/person.png">$INFO[ListItem.Icon]</texture><aspectratio>keep</aspectratio></control>\n'
        f'          <control type="label"><left>66</left><top>4</top><width>{iw-76}</width><height>26</height>'
        f'<font>bigbold</font><textcolor>text</textcolor><aligny>center</aligny><label>$INFO[ListItem.Label]</label></control>\n'
        f'          <control type="label"><left>66</left><top>30</top><width>{iw-76}</width><height>22</height>'
        f'<font>small</font><textcolor>textdim</textcolor><aligny>center</aligny><label>$INFO[ListItem.Label2]</label></control>\n'
        f'        </itemlayout>\n'
        f'        <focusedlayout height="56" width="{iw}">\n'
        f'          <control type="image"><left>0</left><top>0</top><width>{iw}</width><height>56</height>'
        f'<texture colordiffuse="select">fill.png</texture></control>\n'
        f'          <control type="image"><left>6</left><top>4</top><width>48</width><height>48</height>'
        f'<texture fallback="icons/person.png">$INFO[ListItem.Icon]</texture><aspectratio>keep</aspectratio></control>\n'
        f'          <control type="label"><left>66</left><top>4</top><width>{iw-76}</width><height>26</height>'
        f'<font>bigbold</font><textcolor>textinv</textcolor><aligny>center</aligny><label>$INFO[ListItem.Label]</label></control>\n'
        f'          <control type="label"><left>66</left><top>30</top><width>{iw-76}</width><height>22</height>'
        f'<font>small</font><textcolor>textinv</textcolor><aligny>center</aligny><label>$INFO[ListItem.Label2]</label></control>\n'
        f'        </focusedlayout>\n')
    body += xlist(52, 60, 6, 94, 1000, 380, {"onup": "9000", "ondown": "9000", "onleft": "52"},
                  layouts=layouts, sbright="52")
    body += hrow(9000, 6, 482, 1000, [(9100, "$LOCALIZE[13005]",
                                       "<onclick>ActivateWindow(ShutdownMenu)</onclick>")],
                 {"onup": "52", "ondown": "52"}, bw=260)
    body += stubs(ids, {2, 3, 52, 60})
    s  = H + "<window>\n"
    s += "  <defaultcontrol always=\"false\">52</defaultcontrol>\n"
    s += "  <backgroundcolor>desktop</backgroundcolor>\n  <controls>\n"
    s += "    <include>Chrome_Desktop</include>\n    <include>Chrome_Menubar</include>\n"
    s += FRAME.format(colour="accent2", icon="icons24/person.png", title=TITLES[name], body=body,
                      down="52", boxes=BOXES.get(name, "none"))
    s += "  </controls>\n</window>\n"
    return s

def color_picker():
    """GUIDialogColorPicker.cpp: 1 heading, 2 item count, 6 the colours
    (label = name, label2 = ARGB), 7 Cancel - Kodi labels 1, 2 and 7.
    Each row shows the colour itself."""
    name = "DialogColorPicker"
    ids = kodi_ids(name, INV[name])
    body  = xlist(6, 61, 10, 36, 880, 390, {"onup": "9903", "ondown": "7", "onleft": "7"},
                  layouts=lambda iw: rows(iw, swatch=True), sbright="7")
    body += caplabel(16, 434, 400, None, cid=2, h=ROWH)
    body += hrow(None, 430, 434, 460, [(7, None)], {"onup": "6"}, bw=200)
    body += stubs(ids, {1, 2, 6, 7, 61})
    return dialog(name, 900, 486, body, default="6", icon="icons24/skin.png")

def video_manager():
    """GUIDialogVideoManager*.cpp (versions and extras share this file):
    2 title (Kodi writes it), 50 the versions / extras, 21 Play, 26 Remove,
    27 Choose art; versions add 22 Add version, 24 Choose type, 25 Set as
    default; extras add 23 Add extra, 28 Rename. Kodi labels none."""
    name = "DialogVideoManager"
    ids = kodi_ids(name, INV[name])
    ver = "<visible>Window.IsVisible(managevideoversions)</visible>"
    ext = "<visible>Window.IsVisible(managevideoextras)</visible>"
    body  = tlabel(2, 770)
    body += xlist(50, 60, 10, 36, 580, 392, {"onup": "9903", "ondown": "50", "onleft": "101"},
                  sbright="101")
    kids  = item("button", 21, 276, 30, "$LOCALIZE[208]")
    kids += item("button", 22, 276, 30, "$LOCALIZE[40014]", ver)
    kids += item("button", 23, 276, 30, "$LOCALIZE[40015]", ext)
    kids += item("button", 27, 276, 30, "$LOCALIZE[13511]")
    kids += item("button", 24, 276, 30, "$LOCALIZE[40004]", ver)
    kids += item("button", 28, 276, 30, "$LOCALIZE[118]", ext)
    kids += item("button", 26, 276, 30, "$LOCALIZE[15015]")
    kids += item("button", 25, 276, 30, "$LOCALIZE[40023]", ver)
    body += well(598, 36, 292, 392, "panel_sunken_grey.png")
    body += vgroup(101, 606, 42, 276, 380, kids, {"onup": "9903", "ondown": "101", "onleft": "50", "onright": "50"})
    body += caplabel(14, 434, 872, "$INFO[Container(50).ListItem.FileNameAndPath]", h=22)
    body += stubs(ids, {2, 50, 60, 101} | set(range(21, 29)))
    return dialog(name, 900, 466, body, default="50", icon="icons24/movies.png", heading=False)

# ====================================================== subtitle search
def _focus_row(cid, wd, ht, labels, extra=""):
    """Focused-layout body for a list that shares its dialog with other
    focusable controls. Kodi draws the focusedlayout for the selected item
    even while the list itself has no focus; a select-coloured fill with
    textinv labels is right only while it does. Unfocused, the current row
    gets an outline and normal-coloured text, so it stays readable on the
    white well (white on white before). labels: (left, width, attrs, label,
    dim) - attrs are extra tags such as <align>right</align><font>small</font>."""
    on, off = f"Control.HasFocus({cid})", f"!Control.HasFocus({cid})"
    s  = (f'<control type="image"><left>0</left><top>0</top><width>{wd}</width><height>{ht}</height>'
          f'<texture colordiffuse="select">fill.png</texture><visible>{on}</visible></control>\n')
    s += (f'<control type="image"><left>0</left><top>0</top><width>{wd}</width><height>{ht}</height>'
          f'<texture border="4" colordiffuse="select">select_ring.png</texture><visible>{off}</visible></control>\n')
    s += extra
    for l, w, attrs, lab, dim in labels:
        base = (f'<control type="label"><left>{l}</left><top>0</top><width>{w}</width><height>{ht}</height>'
                f'<aligny>center</aligny>{attrs}')
        s += f'{base}<textcolor>textinv</textcolor><selectedcolor>textinv</selectedcolor><label>{lab}</label><visible>{on}</visible></control>\n'
        col = "textdim" if dim else "text"
        s += f'{base}<textcolor>{col}</textcolor><label>{lab}</label><visible>{off}</visible></control>\n'
    return textwrap.indent(s, " " * 10)

def subtitles_dialog():
    """GUIDialogSubtitles.cpp: 150 the subtitle services (add-ons), 120 the
    subtitles the chosen service found, 100/110 that service's name and logo,
    140 a status line, 130 shown when a subtitle already exists, 160 manual
    search. The generic layout had parked the service list off screen, so
    there was nothing to search with."""
    b  = well(10, 36, 280, 420, "panel_sunken_grey.png")
    b += """      <control type="image" id="110">
        <left>18</left><top>44</top><width>40</width><height>40</height>
        <aspectratio>keep</aspectratio>
      </control>
      <control type="label" id="100">
        <left>64</left><top>44</top><width>218</width><height>40</height>
        <font>bold</font><aligny>center</aligny>
      </control>
      <control type="list" id="150">
        <left>18</left><top>92</top><width>264</width><height>312</height>
        <onright>120</onright><onleft>120</onleft><ondown>160</ondown><onup>160</onup>
        <scrolltime tween="linear">0</scrolltime>
        <itemlayout height="28" width="264">
          <control type="image"><left>2</left><top>2</top><width>24</width><height>24</height><texture>$INFO[ListItem.Icon]</texture><aspectratio>keep</aspectratio></control>
          <control type="label"><left>32</left><top>0</top><width>228</width><height>28</height><aligny>center</aligny><label>$INFO[ListItem.Label]</label></control>
        </itemlayout>
        <focusedlayout height="28" width="264">
""" + _focus_row(150, 264, 28, [(32, 228, "", "$INFO[ListItem.Label]", False)],
                 extra='<control type="image"><left>2</left><top>2</top><width>24</width><height>24</height>'
                       '<texture>$INFO[ListItem.Icon]</texture><aspectratio>keep</aspectratio></control>\n') + """        </focusedlayout>
      </control>
      <control type="button" id="160">
        <left>18</left><top>414</top><width>264</width><height>34</height>
        <align>center</align><label>$LOCALIZE[137]</label>
        <onup>150</onup><ondown>150</ondown><onright>120</onright>
      </control>
"""
    b += well(296, 36, 594, 420, "panel_sunken.png")
    b += """      <control type="label" id="140">
        <left>304</left><top>42</top><width>540</width><height>24</height>
        <font>small</font><textcolor>textdim</textcolor>
      </control>
      <control type="image" id="130">
        <left>856</left><top>42</top><width>24</width><height>24</height>
        <texture>icons24/video_subtitles.png</texture>
      </control>
      <control type="list" id="120">
        <left>304</left><top>70</top><width>556</width><height>378</height>
        <onleft>150</onleft><onright>73</onright>
        <pagecontrol>73</pagecontrol><scrolltime tween="linear">0</scrolltime>
        <itemlayout height="28" width="556">
          <control type="label"><left>6</left><top>0</top><width>400</width><height>28</height><aligny>center</aligny><label>$INFO[ListItem.Label2]</label></control>
          <control type="label"><left>410</left><top>0</top><width>140</width><height>28</height><aligny>center</aligny><align>right</align><font>small</font><textcolor>textdim</textcolor><label>$INFO[ListItem.Label]</label></control>
        </itemlayout>
        <focusedlayout height="28" width="556">
""" + _focus_row(120, 556, 28, [(6, 400, "", "$INFO[ListItem.Label2]", False),
                                (410, 140, "<align>right</align><font>small</font>", "$INFO[ListItem.Label]", True)]) + """        </focusedlayout>
      </control>
      <control type="scrollbar" id="73">
        <left>864</left><top>70</top><width>18</width><height>378</height>
        <orientation>vertical</orientation><onleft>120</onleft>
      </control>
"""
    return dialog("DialogSubtitles", 900, 466, b, default="150",
                  icon="icons24/video_subtitles.png", title="$LOCALIZE[24012]")

# ====================================================== live TV channel list
def _channel_row(ht, num_w, logo, f1, h1, f2, h2, focused):
    """One row of the channel list: number, logo, name over what is on now,
    and the programme's progress and times on the right. focused: the
    selected row, filled while the list has focus and outlined while the
    group buttons do (see _focus_row)."""
    on, off = "Control.HasFocus(11)", "!Control.HasFocus(11)"
    y1 = (ht - h1 - h2) // 2
    y2 = y1 + h1
    lx = 8 + num_w + 8
    tx = lx + logo + 8
    def labs(vis, inv):
        c1 = "textinv" if inv else "text"
        c2 = "textinv" if inv else "textdim"
        sel = "<selectedcolor>textinv</selectedcolor>" if inv else ""
        v = f"<visible>{vis}</visible>" if vis else ""
        return (f'<control type="label"><left>4</left><top>0</top><width>{num_w}</width><height>{ht}</height>'
                f'<font>{f1}</font><align>right</align><aligny>center</aligny><textcolor>{c1}</textcolor>{sel}'
                f'<label>$INFO[ListItem.ChannelNumberLabel]</label>{v}</control>\n'
                f'<control type="label"><left>{tx}</left><top>{y1}</top><width>{580 - tx}</width><height>{h1}</height>'
                f'<font>{f1}</font><aligny>center</aligny><textcolor>{c1}</textcolor>{sel}'
                f'<label>$INFO[ListItem.Label]</label>{v}</control>\n'
                f'<control type="label"><left>{tx}</left><top>{y2}</top><width>{580 - tx}</width><height>{h2}</height>'
                f'<font>{f2}</font><aligny>center</aligny><textcolor>{c2}</textcolor>{sel}'
                f'<label>$INFO[ListItem.Title]</label>{v}</control>\n'
                f'<control type="label"><left>596</left><top>{y2}</top><width>250</width><height>{h2}</height>'
                f'<font>{f2}</font><align>right</align><aligny>center</aligny><textcolor>{c2}</textcolor>{sel}'
                f'<label>$INFO[ListItem.StartTime]$INFO[ListItem.EndTime, - ,]</label>{v}</control>\n')
    s = ""
    if focused:
        s += (f'<control type="image"><left>0</left><top>0</top><width>856</width><height>{ht}</height>'
              f'<texture colordiffuse="select">fill.png</texture><visible>{on}</visible></control>\n'
              f'<control type="image"><left>0</left><top>0</top><width>856</width><height>{ht}</height>'
              f'<texture border="4" colordiffuse="select">select_ring.png</texture><visible>{off}</visible></control>\n')
    s += (f'<control type="image"><left>{lx}</left><top>{(ht - logo) // 2}</top><width>{logo}</width><height>{logo}</height>'
          f'<texture fallback="DefaultTVShows.png">$INFO[ListItem.Icon]</texture><aspectratio>keep</aspectratio></control>\n'
          f'<control type="progress"><left>596</left><top>{y1 + (h1 - 12) // 2}</top><width>250</width><height>12</height>'
          f'<info>ListItem.Progress</info><visible>!String.IsEmpty(ListItem.Title)</visible></control>\n')
    if focused:
        s += labs(on, True) + labs(off, False)
    else:
        s += labs(None, False)
    return textwrap.indent(s, " " * 10)

def pvr_channels_osd():
    """The channel list over live TV (GUIDialogPVRChannelsOSD.cpp). Kodi binds
    only list 11 (GUIDialogPVRItemsViewBase CONTROL_LIST) and writes no
    heading and no label 2, so the title, the footer and every row are the
    skin's own: channel number, logo, name, what is on now and how far in.
    ACTION_PREVIOUS/NEXT_CHANNELGROUP switch the group in place (the dialog's
    OnAction); the two footer buttons send them by touch."""
    XLC = "[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]"
    C = "Container(11).ListItem"
    b  = well(10, 36, 880, 352, "panel_sunken.png")
    b += f"""      <control type="list" id="11">
        <left>13</left><top>39</top><width>856</width><height>346</height>
        <onleft>11</onleft><onright>60</onright><onup>11</onup><ondown>11</ondown>
        <pagecontrol>60</pagecontrol><scrolltime tween="linear">0</scrolltime>
        <itemlayout height="64" width="856" condition="{XLC}">
{_channel_row(64, 76, 48, "normal", 30, "small", 28, False)}        </itemlayout>
        <focusedlayout height="64" width="856" condition="{XLC}">
{_channel_row(64, 76, 48, "bold", 30, "small", 28, True)}        </focusedlayout>
        <itemlayout height="44" width="856">
{_channel_row(44, 46, 36, "normal", 20, "small", 20, False)}        </itemlayout>
        <focusedlayout height="44" width="856">
{_channel_row(44, 46, 36, "bold", 20, "small", 20, True)}        </focusedlayout>
      </control>
      <control type="scrollbar" id="60">
        <left>869</left><top>39</top><width>18</width><height>346</height>
        <onleft>11</onleft><onright>9811</onright>
      </control>
"""
    # The footer lines are sized for Extra large (bold 28, small 24 px) so
    # they never touch; at the normal sizes they simply sit a little apart.
    b += well(10, 394, 880, 96, "panel_sunken_grey.png")
    b += f"""      <control type="label" id="2">
        <left>20</left><top>397</top><width>640</width><height>30</height>
        <font>bold</font><aligny>center</aligny><label>$INFO[{C}.Title]</label>
      </control>
      <control type="label">
        <left>20</left><top>428</top><width>640</width><height>26</height>
        <font>small</font><textcolor>textdim</textcolor><aligny>center</aligny>
        <label>$INFO[{C}.StartTime]$INFO[{C}.EndTime, - ,]$INFO[{C}.Label,  -  ,]</label>
      </control>
      <control type="label">
        <left>20</left><top>456</top><width>640</width><height>26</height>
        <font>small</font><aligny>center</aligny>
        <label>$INFO[{C}.NextTitle,$LOCALIZE[19031]: ,]</label>
      </control>
      <control type="progress">
        <left>680</left><top>404</top><width>190</width><height>14</height>
        <info>{C}.Progress</info><visible>!String.IsEmpty({C}.Title)</visible>
      </control>
      <!-- channel group: previous / next (Kodi's own PreviousChannelGroup
           and NextChannelGroup actions) -->
      <control type="button" id="9811">
        <left>680</left><top>430</top><width>48</width><height>48</height>
        <label></label><onclick>Action(PreviousChannelGroup)</onclick>
        <onleft>60</onleft><onright>9812</onright><onup>11</onup><ondown>11</ondown>
      </control>
      <control type="image">
        <left>688</left><top>438</top><width>32</width><height>32</height>
        <texture>icons24/prev.png</texture>
      </control>
      <control type="label">
        <left>730</left><top>430</top><width>90</width><height>48</height>
        <font>small</font><align>center</align><aligny>center</aligny><label>$LOCALIZE[19141]</label>
      </control>
      <control type="button" id="9812">
        <left>822</left><top>430</top><width>48</width><height>48</height>
        <label></label><onclick>Action(NextChannelGroup)</onclick>
        <onleft>9811</onleft><onright>11</onright><onup>11</onup><ondown>11</ondown>
      </control>
      <control type="image">
        <left>830</left><top>438</top><width>32</width><height>32</height>
        <texture>icons24/next.png</texture>
      </control>
"""
    return dialog("DialogPVRChannelsOSD", 900, 500, b, default="11", dim=False,
                  icon="icons24/pvr_channels.png",
                  title="$LOCALIZE[19019]$INFO[VideoPlayer.ChannelGroup, - ,]")

# ====================================================== TV / radio guide
# Taller rows in Extra large fonts or Touch mode (sizepass.XLC). The epggrid is
# not a list, so sizepass leaves it alone: its XL layouts are written here.
XLC = "[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]"
GUIDE_NOW_TEX = os.path.join(os.path.dirname(OUT), "media", "epg_now.png")

def _guide_layouts(cid, chw, row, ruler, cond):
    """One set of epggrid layouts (GUIEPGGridContainer::LoadLayout):
    channellayout / focusedchannellayout - the channel column, chw wide;
    rulerlayout - a time mark (and the date in the top-left corner);
    itemlayout / focusedlayout - a programme.
    Kodi stretches each programme cell to its duration through the controls
    with ids 1-14 (CGUIListGroup::EnlargeWidth; id 1 is also hidden when the
    cell gets too narrow), so whatever must follow the cell's width carries
    such an id. The title label is id 1 in both layouts of both sets: only
    id 1 is hidden when the cell gets narrower than 10 px. Each layout is its
    own CGUIListItemLayout, so the sets can share ids. The ruler bar is drawn behind the grid by guide_window() and the
    channel column has a fixed width, so neither layout needs one."""
    c = f' condition="{cond}"' if cond else ""
    lab, rule, prog = 1, 2, 3        # item: title, bottom rule, progress
    flab, ffill, fprog = 1, 2, 3     # focused: title, fill, progress
    ic = row - 6                                 # channel logo, square
    nw = chw - ic - 12                           # channel name width
    rb = row - 1                                 # programme cell bottom line
    hf = f"Control.HasFocus({cid})"
    chan_label = "$INFO[ListItem.ChannelNumberLabel,,  ]$INFO[ListItem.ChannelName]"
    s  = f"""        <channellayout height="{row}" width="{chw}"{c}>
          <control type="image"><left>0</left><top>0</top><width>{chw-2}</width><height>{row}</height><texture border="2">panel_raised.png</texture></control>
          <control type="image"><left>4</left><top>3</top><width>{ic}</width><height>{ic}</height><aspectratio>keep</aspectratio><texture>$INFO[ListItem.Icon]</texture></control>
          <control type="label"><left>{ic+8}</left><top>0</top><width>{nw}</width><height>{row}</height><font>normal</font><textcolor>text</textcolor><aligny>center</aligny><label>{chan_label}</label></control>
        </channellayout>
        <focusedchannellayout height="{row}" width="{chw}"{c}>
          <control type="image"><left>0</left><top>0</top><width>{chw-2}</width><height>{row}</height><texture border="2">panel_raised.png</texture><visible>!{hf}</visible></control>
          <control type="image"><left>0</left><top>0</top><width>{chw-2}</width><height>{row}</height><texture border="2">button_focus.png</texture><visible>{hf}</visible></control>
          <control type="image"><left>4</left><top>3</top><width>{ic}</width><height>{ic}</height><aspectratio>keep</aspectratio><texture>$INFO[ListItem.Icon]</texture></control>
          <control type="label"><left>{ic+8}</left><top>0</top><width>{nw}</width><height>{row}</height><font>bold</font><textcolor>text</textcolor><aligny>center</aligny><label>{chan_label}</label><visible>!{hf}</visible></control>
          <control type="label"><left>{ic+8}</left><top>0</top><width>{nw}</width><height>{row}</height><font>bold</font><textcolor>textinv</textcolor><aligny>center</aligny><label>{chan_label}</label><visible>{hf}</visible></control>
        </focusedchannellayout>
        <rulerlayout height="{ruler}" width="150"{c}>
          <control type="image"><left>0</left><top>3</top><width>1</width><height>{ruler-6}</height><texture colordiffuse="text">fill.png</texture></control>
          <control type="label"><left>5</left><top>0</top><width>140</width><height>{ruler}</height><font>small</font><textcolor>text</textcolor><aligny>center</aligny><label>$INFO[ListItem.Label]</label></control>
        </rulerlayout>
"""
    # a programme: white cell (the well shows through), 1px rules on the left
    # and bottom so neighbours share one line, a red dot for a timer and a
    # progress bar while it is on air; the selected one is a select-coloured
    # block, as in every other list
    onair = "<visible>Integer.IsGreater(ListItem.Progress,0) + Integer.IsLess(ListItem.Progress,100)</visible>"
    timer = (f'<control type="image"><left>3</left><top>2</top><width>6</width><height>6</height>'
             f'<texture colordiffuse="accent1">fill.png</texture><visible>ListItem.HasTimer | ListItem.IsRecording</visible></control>')
    title = "$INFO[ListItem.Label]"
    s += f"""        <itemlayout height="{row}" width="60"{c}>
          <control type="image"><left>0</left><top>0</top><width>1</width><height>{row}</height><texture colordiffuse="text">fill.png</texture></control>
          <control type="image" id="{rule}"><left>0</left><top>{rb}</top><width>60</width><height>1</height><texture colordiffuse="text">fill.png</texture></control>
          <control type="progress" id="{prog}"><left>4</left><top>{rb-6}</top><width>52</width><height>4</height><info>ListItem.Progress</info>{onair}</control>
          {timer}
          <control type="label" id="{lab}"><left>6</left><top>0</top><width>50</width><height>{rb}</height><font>normal</font><textcolor>text</textcolor><aligny>center</aligny><label>{title}</label></control>
        </itemlayout>
        <focusedlayout height="{row}" width="60"{c}>
          <control type="image" id="{ffill}"><left>0</left><top>0</top><width>60</width><height>{row}</height><texture colordiffuse="select">fill.png</texture></control>
          <control type="progress" id="{fprog}"><left>4</left><top>{rb-6}</top><width>52</width><height>4</height><info>ListItem.Progress</info>{onair}</control>
          {timer}
          <control type="label" id="{flab}"><left>6</left><top>0</top><width>50</width><height>{rb}</height><font>bold</font><textcolor>textinv</textcolor><aligny>center</aligny><label>{title}</label></control>
        </focusedlayout>
"""
    return s

GUIDE_STRIP = [  # id, label, onclick(s); 28 is Kodi's "Group: <name>" button
    (28,   "$LOCALIZE[19141]", []),
    (9481, "$LOCALIZE[19030]", ["PVR.EpgGridControl(CurrentProgramme)"]),
    (9482, "$LOCALIZE[31845]", ["PVR.EpgGridControl(-12)"]),
    (9483, "$LOCALIZE[31846]", ["PVR.EpgGridControl(+12)"]),
    (9484, "$LOCALIZE[552]",   ["PVR.EpgGridControl(SelectDate)"]),
    (9485, "$LOCALIZE[31847]", ["SetFocus(50)", "Action(PageUp)"]),
    (9486, "$LOCALIZE[31848]", ["SetFocus(50)", "Action(PageDown)"]),
    (9487, "$LOCALIZE[19033]", ["SetFocus(50)", "Action(Info)"]),
    (9488, "$LOCALIZE[31906]", ["SetFocus(50)", "Action(ContextMenu)"]),
    (9489, "$LOCALIZE[19326]", ["ActivateWindow(PVRGuideControls)"]),
]

def guide_window():
    """MyPVRGuide.xml - loaded by both the TV and the Radio guide
    (CGUIWindowPVRGuideBase). The window only works through a real epggrid
    named in <views>: CGUIMediaWindow builds its view control from <views>,
    and GetGridControl() is that control. Without one the guide is blank and
    PVR.EpgGridControl / waking from suspend dereference a null grid.

    Kodi itself labels 28 ("Group: <name>") and 29/30 (header labels), binds
    the channel groups to container 11 and drives grid 50. Tapping a
    programme is Kodi's EPG select action, a long-press its context menu
    (touchscreen.xml: longpress = RightClick); dragging pans the grid
    (ACTION_GESTURE_PAN). The strip on the left gives every jump a button,
    because touch has no keys for them."""
    meta = INV["MyPVRGuide"]
    ids = {int(k): v for k, v in meta["ids"].items()}
    CHW, GX, GY, GW, GH = 180, 171, 37, 812, 362     # grid inside its well
    placed = {28, 50, 60}
    b  = well(6, 34, 156, 494, "panel_sunken_grey.png")
    b += ("      <control type=\"grouplist\" id=\"9480\">\n"
          "        <left>12</left><top>40</top><width>144</width><height>482</height>\n"
          "        <orientation>vertical</orientation><itemgap>2</itemgap>\n"
          "        <onup>9100</onup><ondown>9100</ondown><onleft>50</onleft><onright>50</onright>\n")
    for cid, lab, clicks in GUIDE_STRIP:
        b += (f"        <control type=\"button\" id=\"{cid}\">\n"
              f"          <width>144</width><height>30</height><font>chrome</font>\n"
              f"          <align>left</align><textoffsetx>6</textoffsetx>\n"
              f"          <label>{lab}</label>\n"
              + "".join(f"          <onclick>{a}</onclick>\n" for a in clicks) +
              "        </control>\n")
    b += "      </control>\n"
    b += well(GX - 3, GY - 3, GW + 26, GH + 6, "panel_sunken.png")
    for rh, vis in ((40, XLC), (24, "!" + XLC)):      # the time ruler's bar
        b += (f"      <control type=\"image\">\n"
              f"        <left>{GX}</left><top>{GY}</top><width>{GW}</width><height>{rh}</height>\n"
              f"        <texture border=\"2\">bevel_thin.png</texture>\n"
              f"        <visible>{vis}</visible>\n      </control>\n")
    # Keys: left/right move through time and only reach onleft at the start
    # of the guide data, so Up from the first channel is the way to the strip
    # (CGUIEPGGridContainer::OnUp navigates once it cannot move).
    # The price: no Up wrap from the first channel to the last. With a remote,
    # every jump is also in the context menu (Navigate...) and on 'n'.
    b += f"""      <control type="epggrid" id="50">
        <left>{GX}</left><top>{GY}</top><width>{GW}</width><height>{GH}</height>
        <orientation>vertical</orientation>
        <timeblocks>24</timeblocks><rulerunit>6</rulerunit>
        <scrolltime tween="linear">0</scrolltime>
        <pagecontrol>60</pagecontrol>
        <viewtype label="19298">list</viewtype>
        <onleft>9480</onleft><onright>60</onright><onup>9480</onup><ondown>9100</ondown>
"""
    if os.path.exists(GUIDE_NOW_TEX):   # "now" line, once mkmedia draws it
        b += '        <progresstexture border="0,0,4,0" colordiffuse="accent1">epg_now.png</progresstexture>\n'
    # XL set first: Kodi takes the first layout whose condition passes.
    b += _guide_layouts(50, CHW, 50, 40, XLC)
    b += _guide_layouts(50, CHW, 34, 24, None)
    b += f"""      </control>
      <control type="scrollbar" id="60">
        <left>{GX+GW+2}</left><top>{GY}</top><width>18</width><height>{GH}</height>
        <orientation>vertical</orientation>
        <onleft>50</onleft><onright>9480</onright>
      </control>
"""
    # the selected programme, under the grid (ListItem.* is the grid's item:
    # CGUIWindowPVRGuideBase::GetCurrentListItem). Spaced for the XL fonts.
    IY = GY + GH + 6
    b += well(GX - 3, IY, GW + 26, 528 - IY, "panel_sunken_grey.png")
    b += f"""      <control type="image">
        <left>{GX+5}</left><top>{IY+8}</top><width>64</width><height>64</height>
        <aspectratio>keep</aspectratio><texture>$INFO[ListItem.Icon]</texture>
      </control>
      <control type="label">
        <left>{GX+78}</left><top>{IY+6}</top><width>420</width><height>30</height>
        <font>bold</font><textcolor>text</textcolor><aligny>center</aligny>
        <label>$INFO[ListItem.EpgEventTitle]</label>
      </control>
      <control type="label">
        <left>{GX+500}</left><top>{IY+6}</top><width>{GW+16-500}</width><height>30</height>
        <font>small</font><textcolor>textdim</textcolor><align>right</align><aligny>center</aligny>
        <label>$INFO[ListItem.StartDate,,  ]$INFO[ListItem.StartTime]$INFO[ListItem.EndTime, - ]</label>
      </control>
      <control type="label">
        <left>{GX+78}</left><top>{IY+36}</top><width>{GW-62}</width><height>26</height>
        <font>small</font><textcolor>textdim</textcolor><aligny>center</aligny>
        <label>$INFO[ListItem.ChannelName]$INFO[ListItem.Genre,  -  ]$INFO[ListItem.EpisodeName,  -  ]</label>
      </control>
      <control type="textbox">
        <left>{GX+78}</left><top>{IY+64}</top><width>{GW-62}</width><height>{528-IY-70}</height>
        <font>small</font><textcolor>text</textcolor>
        <label>$INFO[ListItem.Plot]</label>
      </control>
"""
    # digits typed on a remote jump to that channel (PVR.ChannelNumberInput)
    b += f"""      <control type="group">
        <left>{GX + GW//2 - 110}</left><top>{GY + 110}</top><width>220</width><height>70</height>
        <visible>!String.IsEmpty(PVR.ChannelNumberInput)</visible>
        <control type="image">
          <left>0</left><top>0</top><width>220</width><height>70</height>
          <texture border="2">panel_raised.png</texture>
        </control>
        <control type="label">
          <left>0</left><top>0</top><width>220</width><height>70</height>
          <font>bigbold</font><textcolor>text</textcolor><align>center</align><aligny>center</aligny>
          <label>$INFO[PVR.ChannelNumberInput]</label>
        </control>
      </control>
"""
    # Off-screen stubs: 11 (Kodi binds the channel groups to it; the Group
    # button 28 is the visible way to switch) and the header labels 29/30.
    # The other ids Kodi may label (2-8, 10, 31: sort, filters) do nothing
    # in the guide and are safely absent - SET_CONTROL_* on a missing id is
    # a no-op - and ids 1-14 are needed by the grid's layouts. Estuary's
    # side-blade ids and grids 51-53 (not in <views>) are left out.
    KODI = {11, 29, 30}
    rest = {i: t for i, t in ids.items() if i in KODI}
    b += stubs(rest, placed)
    s = fullwindow("MyPVRGuide", b, default="50", views="50",
                   icon="icons24/pvr_guide.png")
    # The channel group's name, always readable: button 28's "Group: <name>"
    # (GUIWindowPVRBase::UpdateButtons) is cut off at the strip's width
    # unless it has focus, but Kodi also writes the bare name into label 30
    # (CGUIWindowPVRGuideBase::UpdateButtons), so the title bar's right-hand
    # label shows it.
    lab = '          <param name="label" value="$LOCALIZE[19069]" />\n'
    assert lab in s, "guide title bar"
    return s.replace(lab, lab + '          <param name="label2" value="$INFO[Control.GetLabel(30),$LOCALIZE[19141]: ]" />\n', 1)

def pvr_guide_controls():
    """DialogPVRGuideControls.xml - 'Navigate...' in the guide's context menu
    and 'n' on a keyboard. CGUIDialogPVRGuideControls has no ids of its own:
    every button is the skin's, calling PVR.EpgGridControl on the guide
    window underneath (PVRBuiltins.cpp). Kodi only uses this dialog because
    the file exists (OnContextButtonNavigate, HasSkinFile), so it must offer
    all twelve jumps of Kodi's own fallback menu.

    It sits on the bottom edge, over the programme info and the task bar, as
    Estuary's does, so the grid above stays in view and each jump shows at
    once. No dimming, for the same reason."""
    cols = [  # grouplist id, caption, buttons (id, label, EpgGridControl arg, visible)
        (201, "$LOCALIZE[19325]", [(600, 19063, "FirstProgramme", None),
                                   (601, 19317, "-12", None),
                                   (602, 19070, "CurrentProgramme", None)]),
        (204, "",                 [(603, 19318, "+12", None),
                                   (604, 19064, "LastProgramme", None),
                                   (605, 19288, "SelectDate", None)]),
        (202, "$LOCALIZE[19148]", [(70040, 19322, "FirstChannel", None),
                                   (70041, 19323, "PlayingChannel",
                                    "PVR.IsPlayingTV | PVR.IsPlayingRadio | PVR.IsPlayingEpgTag"),
                                   (70042, 19324, "LastChannel", None)]),
        (203, "$LOCALIZE[19141]", [(70043, 19319, "PreviousGroup", None),
                                   (70044, 19320, "NextGroup", None),
                                   (70045, 19321, "SelectGroup", None)]),
    ]
    CW, GAP, X0, TOP, CLW = 196, 8, 14, 62, 100
    CX = X0 + 4 * (CW + GAP)                 # the Close column
    WD = CX + CLW + X0                       # 944
    CLOSE = 9970
    # Three rows of buttons: 30 px, or 46 px in Extra large / Touch mode
    # (sizepass gives grouplist rows Height_30 / Height_30_XL). The box is
    # sized for each: the frame and the well come in an XLC pair, and the
    # Close button sits beside the rows, not under them, so nothing else
    # has to move.
    sizes = {}                                # cond -> (box height, well height)
    for cond, row in ((XLC, 46), ("!" + XLC, 30)):
        rows = 3 * row + 2 * 3
        sizes[cond] = (TOP + rows + 16, TOP + rows + 8 - 34)
    HT = max(h for h, _ in sizes.values())    # the group: XL size, on the bottom edge
    HN = sizes["!" + XLC][0]
    b = ""
    for cond, (_, wh) in sizes.items():
        b += (f"      <control type=\"image\">\n"
              f"        <left>8</left><top>34</top><width>{WD-16}</width><height>{wh}</height>\n"
              f"        <texture border=\"2\">panel_sunken_grey.png</texture>\n"
              f"        <visible>{cond}</visible>\n      </control>\n")
    b += "      <control type=\"group\" id=\"200\">\n"
    for k, (gid, cap, btns) in enumerate(cols):
        x = X0 + k * (CW + GAP)
        if cap:
            span = 2 * CW + GAP if gid == 201 else CW
            b += (f"        <control type=\"label\">\n"
                  f"          <left>{x}</left><top>38</top><width>{span}</width><height>22</height>\n"
                  f"          <font>chromebold</font><textcolor>text</textcolor><aligny>center</aligny>\n"
                  f"          <label>{cap}</label>\n        </control>\n")
        prev_g = cols[k - 1][0] if k else CLOSE
        next_g = cols[k + 1][0] if k + 1 < len(cols) else CLOSE
        b += (f"        <control type=\"grouplist\" id=\"{gid}\">\n"
              f"          <left>{x}</left><top>{TOP}</top><width>{CW}</width><height>148</height>\n"
              f"          <orientation>vertical</orientation><itemgap>3</itemgap>\n"
              f"          <onleft>{prev_g}</onleft><onright>{next_g}</onright>\n"
              f"          <onup>{CLOSE}</onup><ondown>{CLOSE}</ondown>\n")
        for cid, sid, arg, vis in btns:
            b += (f"          <control type=\"button\" id=\"{cid}\">\n"
                  f"            <width>{CW}</width><height>30</height><font>chrome</font>\n"
                  f"            <align>left</align><textoffsetx>8</textoffsetx>\n"
                  f"            <label>$LOCALIZE[{sid}]</label>\n"
                  f"            <onclick>PVR.EpgGridControl({arg})</onclick>\n"
                  + (f"            <visible>{vis}</visible>\n" if vis else "") +
                  "          </control>\n")
        b += "        </control>\n"
    b += "      </control>\n"
    # touch has no Esc: a real Close button, as tall as a row in touch mode
    b += f"""      <control type="button" id="{CLOSE}">
        <left>{CX}</left><top>{TOP}</top><width>{CLW}</width>
        <include content="Height_30_XL" condition="{XLC}" />
        <include content="Height_30" condition="!{XLC}" />
        <font>chrome</font><label>$LOCALIZE[15067]</label>
        <onclick>Action(close)</onclick>
        <onup>602</onup><ondown>602</ondown><onleft>{cols[-1][0]}</onleft><onright>{cols[0][0]}</onright>
      </control>
"""
    # A tap outside the box closes it, as in Kodi's own skin: four empty
    # buttons around the box (not one under it - a tap on the box's own
    # background would fall through to it and close the dialog). They hang
    # off the box itself, 2048 px each way, so they reach the screen edges in
    # both layouts; CGUIControlGroup passes mouse events to its children
    # without clipping to the group. The bottom one only matters in normal
    # mode, where the frame ends above the screen's bottom edge.
    F = 2048
    for cid, geo, vis in (
            (9971, f"<left>{-F}</left><top>{-F}</top><width>{F}</width><height>{2*F}</height>", None),
            (9972, f"<left>{WD}</left><top>{-F}</top><width>{F}</width><height>{2*F}</height>", None),
            (9973, f"<left>0</left><top>{-F}</top><width>{WD}</width><height>{F}</height>", None),
            (9974, f"<left>0</left><top>{HN}</top><width>{WD}</width><height>{F}</height>", "!" + XLC)):
        b += (f'      <control type="button" id="{cid}">\n        {geo}\n'
              '        <texturefocus>-</texturefocus><texturenofocus>-</texturenofocus>\n'
              '        <label></label>\n        <onclick>Action(close)</onclick>\n'
              '        <onup>602</onup><ondown>602</ondown><onleft>602</onleft><onright>602</onright>\n'
              + (f'        <visible>{vis}</visible>\n' if vis else "") +
              '      </control>\n')
    s = dialog("DialogPVRGuideControls", WD, HT, b, default="602", heading=False,
               icon="icons24/pvr_controls.png", default_always=True, dim=False,
               anchor="bottom")
    # the frame in two heights; Kodi keeps only the include whose condition
    # holds when the window loads (CGUIIncludes), and a font or Touch mode
    # change reloads the skin
    i = s.index('      <include content="Dialog_Box">\n')
    j = s.index("      </include>\n", i) + len("      </include>\n")
    box = s[i:j]
    pair = ""
    for cond, (h, _) in sizes.items():
        pair += (box.replace('<include content="Dialog_Box">', f'<include content="Dialog_Box" condition="{cond}">', 1)
                    .replace(f'<param name="height" value="{HT}" />', f'<param name="height" value="{h}" />', 1))
    return s[:i] + pair + s[j:]

# ====================================================== game controllers
def _game_box(wd, ht, title, body, heading_id=None, boxes="dialog", down="3"):
    """A centred Arthur dialog as a plain group, for use inside an include."""
    inner = wd - 6
    s  = "    <control type=\"group\">\n"
    s += "      <centerleft>50%</centerleft><centertop>50%</centertop>\n"
    s += f"      <width>{wd}</width><height>{ht}</height>\n"
    s += "      <include content=\"Dialog_Box\">\n"
    s += f"        <param name=\"width\" value=\"{wd}\" /><param name=\"height\" value=\"{ht}\" />\n"
    s += f"        <param name=\"innerwidth\" value=\"{inner}\" />\n"
    s += "        <param name=\"icon\" value=\"icons24/controllers.png\" /><param name=\"colour\" value=\"accent2\" />\n"
    s += f"        <param name=\"down\" value=\"{down}\" /><param name=\"boxes\" value=\"{boxes}\" />\n"
    if title:
        s += f"        <param name=\"title\" value=\"{title}\" />\n"
    s += "      </include>\n"
    if heading_id:
        s += (f"      <control type=\"label\" id=\"{heading_id}\">\n"
              f"        <left>29</left><top>3</top><width>{inner-100}</width><height>26</height>\n"
              "        <font>chromebold</font><textcolor>titletext</textcolor><aligny>center</aligny>\n"
              "      </control>\n")
    return s + body + "    </control>\n"

def game_controllers():
    """DialogGameControllers.xml is loaded by THREE windows - controller
    configuration, ports and agents (players) - each with its own control ids,
    some of them clashing (3 is a grouplist in one and a list in another).
    Like Estuary, the file picks its layout with include conditions on which
    dialog is opening.

    Controller configuration (GUIControllerDefines.h): Kodi clones button 10
    into grouplist 3 (one per controller profile) and button 7, label 8 and
    image 9 into grouplist 5 (the buttons of the chosen controller); 31 draws
    the controller, 32 describes it; 17-22 are Help, OK, Reset, Get more,
    Ignore input, Get all. v0.7 had the templates on show and the real
    grouplists parked off screen, so both lists came up empty."""
    well_l = well(10, 60, 300, 330, "panel_sunken_grey.png", 6)
    well_r = well(632, 60, 358, 330, "panel_sunken_grey.png", 6)
    ctl  = f"""      <control type="label">
        <left>14</left><top>36</top><width>292</width><height>24</height>
        <font>bold</font><align>center</align><label>$LOCALIZE[35050]</label>
      </control>
{well_l}      <control type="grouplist" id="3">
        <left>18</left><top>66</top><width>266</width><height>318</height>
        <orientation>vertical</orientation><itemgap>2</itemgap>
        <onright>5</onright><onleft>5</onleft><ondown>9001</ondown><onup>9002</onup>
        <pagecontrol>62</pagecontrol>
      </control>
      <control type="scrollbar" id="62">
        <left>288</left><top>66</top><width>18</width><height>318</height>
        <orientation>vertical</orientation><onleft>3</onleft><onright>5</onright>
      </control>
      <control type="button" id="10">
        <left>-3000</left><top>0</top><width>266</width><height>30</height>
        <align>left</align><textoffsetx>10</textoffsetx>
      </control>
      <control type="gamecontroller" id="31">
        <left>320</left><top>60</top><width>300</width><height>300</height>
      </control>
      <control type="label">
        <left>636</left><top>36</top><width>350</width><height>24</height>
        <font>bold</font><align>center</align><label>$LOCALIZE[35059]</label>
      </control>
{well_r}      <control type="grouplist" id="5">
        <left>640</left><top>66</top><width>320</width><height>318</height>
        <orientation>vertical</orientation><itemgap>2</itemgap>
        <onleft>3</onleft><onright>3</onright><ondown>9001</ondown><onup>9002</onup>
        <pagecontrol>61</pagecontrol>
      </control>
      <control type="scrollbar" id="61">
        <left>966</left><top>66</top><width>18</width><height>318</height>
        <orientation>vertical</orientation><onleft>5</onleft><onright>3</onright>
      </control>
      <control type="button" id="7">
        <left>-3000</left><top>0</top><width>320</width><height>30</height>
        <align>left</align><textoffsetx>10</textoffsetx>
      </control>
      <control type="label" id="8">
        <left>-3000</left><top>0</top><width>320</width><height>28</height>
        <font>bold</font><textcolor>textdim</textcolor><aligny>center</aligny>
      </control>
      <control type="image" id="9">
        <left>-3000</left><top>0</top><width>320</width><height>2</height>
        <texture>fill_black.png</texture>
      </control>
{well(10, 396, 980, 80, "panel_sunken.png", 6)}      <control type="textbox" id="32">
        <left>18</left><top>402</top><width>964</width><height>68</height>
        <font>small</font>
      </control>
      <control type="grouplist" id="9001">
        <left>10</left><top>484</top><width>980</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>10</itemgap>
        <onup>3</onup><ondown>9002</ondown>
        <control type="button" id="18"><width>310</width><height>32</height><align>center</align><label>$LOCALIZE[186]</label></control>
        <control type="button" id="19"><width>310</width><height>32</height><align>center</align><label>$LOCALIZE[13007]</label></control>
        <control type="button" id="20"><width>310</width><height>32</height><align>center</align><label>$LOCALIZE[21452]</label></control>
      </control>
      <control type="grouplist" id="9002">
        <left>10</left><top>520</top><width>980</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>10</itemgap>
        <onup>9001</onup><ondown>3</ondown>
        <control type="button" id="22"><width>310</width><height>32</height><align>center</align><label>$LOCALIZE[35021]</label></control>
        <control type="button" id="17"><width>310</width><height>32</height><align>center</align><label>$LOCALIZE[10043]</label></control>
        <control type="button" id="21"><width>310</width><height>32</height><align>center</align><label>$LOCALIZE[35019]</label></control>
      </control>
"""
    ports = f"""{well(10, 36, 880, 330, "panel_sunken.png", 6)}      <control type="list" id="3">
        <left>18</left><top>42</top><width>840</width><height>318</height>
        <onright>62</onright><ondown>9001</ondown><onup>9001</onup>
        <pagecontrol>62</pagecontrol><scrolltime tween="linear">0</scrolltime>
        <itemlayout height="34" width="840">
          <control type="label"><left>10</left><top>0</top><width>400</width><height>34</height><aligny>center</aligny><label>$INFO[ListItem.Label]</label></control>
          <control type="label"><left>420</left><top>0</top><width>410</width><height>34</height><aligny>center</aligny><align>right</align><font>small</font><textcolor>textdim</textcolor><label>$INFO[ListItem.Label2]</label></control>
        </itemlayout>
        <focusedlayout height="34" width="840">
{_focus_row(3, 840, 34, [(10, 400, "", "$INFO[ListItem.Label]", False),
                         (420, 410, "<align>right</align><font>small</font>", "$INFO[ListItem.Label2]", True)])}        </focusedlayout>
      </control>
      <control type="scrollbar" id="62">
        <left>866</left><top>42</top><width>18</width><height>318</height>
        <orientation>vertical</orientation><onleft>3</onleft>
      </control>
      <control type="grouplist" id="9001">
        <left>10</left><top>376</top><width>880</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>10</itemgap>
        <onup>3</onup><ondown>3</ondown>
        <control type="button" id="18"><width>260</width><height>32</height><align>center</align><label>$LOCALIZE[186]</label></control>
        <control type="button" id="19"><width>260</width><height>32</height><align>center</align><label>$LOCALIZE[13007]</label></control>
      </control>
"""
    agents = f"""      <control type="button" id="3">
        <left>10</left><top>36</top><width>260</width><height>32</height>
        <align>center</align><label>$LOCALIZE[35110]</label>
        <onclick>ActivateWindow(GamePorts)</onclick>
        <onright>7</onright><ondown>7</ondown><onup>18</onup>
      </control>
      <control type="gamecontrollerlist" id="4">
        <left>280</left><top>36</top><width>600</width><height>32</height>
        <orientation>horizontal</orientation>
        <itemlayout width="32" height="32"><control type="gamecontroller"><width>32</width><height>32</height></control></itemlayout>
        <focusedlayout width="32" height="32"><control type="gamecontroller"><width>32</width><height>32</height></control></focusedlayout>
      </control>
{well(10, 76, 880, 290, "panel_sunken.png", 6)}      <control type="list" id="7">
        <left>18</left><top>82</top><width>840</width><height>278</height>
        <onup>3</onup><ondown>18</ondown><onright>61</onright>
        <pagecontrol>61</pagecontrol><scrolltime tween="linear">0</scrolltime>
        <itemlayout height="34" width="840">
          <control type="label"><left>10</left><top>0</top><width>820</width><height>34</height><aligny>center</aligny><label>$INFO[ListItem.Label]</label></control>
        </itemlayout>
        <focusedlayout height="34" width="840">
{_focus_row(7, 840, 34, [(10, 820, "", "$INFO[ListItem.Label]", False)])}        </focusedlayout>
      </control>
      <control type="scrollbar" id="61">
        <left>866</left><top>82</top><width>18</width><height>278</height>
        <orientation>vertical</orientation><onleft>7</onleft>
      </control>
      <control type="button" id="18">
        <left>320</left><top>376</top><width>260</width><height>32</height>
        <align>center</align><label>$LOCALIZE[186]</label>
        <onup>7</onup><ondown>3</ondown>
      </control>
"""
    inc  = H + "<!-- GENERATED by genwindows.py: the three layouts DialogGameControllers.xml picks from -->\n<includes>\n"
    inc += "  <include name=\"Arthur_GameControllers\">\n" + _game_box(1000, 566, "$LOCALIZE[35058]", ctl) + "  </include>\n"
    inc += "  <include name=\"Arthur_GamePorts\">\n" + _game_box(900, 420, None, ports, heading_id=2) + "  </include>\n"
    inc += "  <include name=\"Arthur_GameAgents\">\n" + _game_box(900, 420, "$LOCALIZE[35172]", agents) + "  </include>\n"
    inc += "</includes>\n"
    win  = (H + "<window>\n  <defaultcontrol always=\"true\">3</defaultcontrol>\n  <controls>\n"
            "    <include>Dialog_Dim</include>\n"
            "    <include condition=\"Window.IsDialogTopMost(gamecontrollers)\">Arthur_GameControllers</include>\n"
            "    <include condition=\"Window.IsDialogTopMost(gameports)\">Arthur_GamePorts</include>\n"
            "    <include condition=\"Window.IsDialogTopMost(gameagents)\">Arthur_GameAgents</include>\n"
            "  </controls>\n</window>\n")
    w("Includes_Games", inc)
    return win

# ====================================================== main
def main():
    written = {}
    written.update(small_dialogs())
    written["DialogKeyboard"] = keyboard_window()
    written["DialogNumeric"]  = numeric_window()
    written["FileManager"]    = filemanager()
    written["MyWeather"]      = weather()
    written["VideoFullScreen"]= fullscreen_video()
    written["SlideShow"]      = slideshow()
    written["MusicVisualisation"] = music_vis()
    written["PlayerControls"] = player_controls()
    written["DialogButtonMenu"] = button_menu()
    written["FileBrowser"]      = file_browser()
    written["DialogMediaSource"] = media_source()
    written["DialogPictureInfo"] = picture_info()
    written["SettingsSystemInfo"] = system_info()
    written["VideoOSD"]       = osd_window("VideoOSD", "video")
    written["MusicOSD"]       = osd_window("MusicOSD", "music")
    written["GameOSD"]        = osd_window("GameOSD", "game")
    written["SettingsCategory"] = settings_window("SettingsCategory", categories=True)
    for n in ("DialogAddonSettings","DialogSettings"):
        written[n] = settings_dialog(n)
    for n in ("DialogVideoInfo","DialogMusicInfo","DialogPVRInfo"):
        written[n] = info_dialog(n, INV.get(n, {}).get("ids", {}))
    written["DialogAddonInfo"] = addon_info_dialog()
    written["DialogGameControllers"] = game_controllers()
    written["DialogSubtitles"] = subtitles_dialog()
    written["DialogPVRChannelsOSD"] = pvr_channels_osd()
    written["DialogPVRChannelManager"] = pvr_channel_manager()
    written["DialogPVRGroupManager"] = pvr_group_manager()
    written["DialogPVRGuideSearch"] = pvr_guide_search()
    written["SmartPlaylistEditor"] = smartplaylist_editor()
    written["SmartPlaylistRule"] = smartplaylist_rule()
    written["MyMusicPlaylistEditor"] = music_playlist_editor()
    written["SettingsScreenCalibration"] = screen_calibration()
    written["LoginScreen"] = login_screen()
    written["DialogColorPicker"] = color_picker()
    written["DialogVideoManager"] = video_manager()

    written["MyPVRGuide"] = guide_window()
    written["DialogPVRGuideControls"] = pvr_guide_controls()

    count = 0
    for name, meta in INV.items():
        if name in HAND or name.startswith(SKIP_PREFIX): continue
        if name in written: continue
        as_dialog = name.startswith("Dialog")
        written[name] = generic(name, meta, as_dialog)

    for name, xml in written.items():
        if name in HAND or name.startswith(SKIP_PREFIX): continue
        w(name, xml); count += 1
    print("wrote", count, "windows")

if __name__ == "__main__":
    main()
