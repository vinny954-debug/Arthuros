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
 "LoginScreen":"$LOCALIZE[20096]", "MyMusicPlaylistEditor":"$LOCALIZE[136]",
 "SmartPlaylistEditor":"$LOCALIZE[136]", "SmartPlaylistRule":"$LOCALIZE[136]",
 "MyPVRGuide":"$LOCALIZE[19029]", "Timers":"$LOCALIZE[19040]",
 "PlayerControls":"$LOCALIZE[31907]", "VideoOSD":"$LOCALIZE[31907]",
 "MusicOSD":"$LOCALIZE[31907]", "MusicVisualisation":"$LOCALIZE[31907]",
 "SlideShow":"$LOCALIZE[108]", "GameOSD":"$LOCALIZE[31907]",
 "DialogAddonSettings":"$LOCALIZE[10004]", "DialogSettings":"$LOCALIZE[5]",
 # dialogs Kodi gives no heading (no id 1 written by their C++ class)
 "DialogButtonMenu":"$LOCALIZE[31976]", "DialogSeekBar":"$LOCALIZE[31907]",
 "VideoOSDBookmarks":"$LOCALIZE[298]",
 "DialogPVRChannelManager":"$LOCALIZE[19199]", "DialogPVRGroupManager":"$LOCALIZE[19205]",
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
    s += f'        <param name="boxes" value="{BOXES.get(name, "dialog")}" />\n'
    if title:
        s += f'        <param name="title" value="{title}" />\n'
    s += "      </include>\n"
    if heading:
        s += f'      <include content="Dialog_Heading"><param name="width" value="{inner-100}" /></include>\n'
    s += body
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
           Kodi writes Basic / Standard / Advanced / Expert on it and cycles
           the level when it is clicked. -->
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
    body += f"""      <control type="grouplist" id="9001">
        <left>13</left><top>444</top><width>874</width><height>30</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>8</itemgap>
        <onup>5</onup><ondown>{3 if cats else 5}</ondown>
        <control type="button" id="28"><width>180</width><height>30</height><align>center</align></control>
        <control type="button" id="29"><width>180</width><height>30</height><align>center</align></control>
        <control type="button" id="30"><width>180</width><height>30</height><align>center</align></control>
      </control>
"""
    return dialog(name, 900, 486, body, default="3" if cats else "5",
                  icon="icons24/settings.png", colour="accent1", heading=False)

# ====================================================== player / OSD family
OSD_BUTTONS = [
  (600, "radiobutton", "prev",  ["PlayerControl(Previous)"]),
  (601, "radiobutton", "rew",   ["PlayerControl(Play)", "PlayerControl(Rewind)"]),
  (602, "button",      "play",  ["PlayerControl(Play)"]),
  (603, "radiobutton", "stop",  ["PlayerControl(Stop)"]),
  (606, "radiobutton", "ffwd",  ["PlayerControl(Play)", "PlayerControl(Forward)"]),
  (607, "radiobutton", "next",  ["PlayerControl(Next)"]),
]


def icon_radio(cid, glyph, w, h, clicks, indent=8):
    """A transport button whose radio texture is the glyph. radioposx is
    measured from the control's left edge (GUIRadioButtonControl.cpp), so
    (w-16)/2 centres it. 'Off' is drawn dimmed so toggles like shuffle show
    their state."""
    sp = " " * indent
    x, y = (w - 16) // 2, (h - 16) // 2
    ons = "".join(f"\n{sp}  <onclick>{c}</onclick>" for c in clicks)
    return (f'{sp}<control type="radiobutton" id="{cid}">\n'
            f'{sp}  <width>{w}</width><height>{h}</height>\n'
            f'{sp}  <label></label>\n'
            f'{sp}  <textureradioonfocus>icons16/{glyph}.png</textureradioonfocus>\n'
            f'{sp}  <textureradioonnofocus>icons16/{glyph}.png</textureradioonnofocus>\n'
            f'{sp}  <textureradioofffocus>icons16/{glyph}.png</textureradioofffocus>\n'
            f'{sp}  <textureradiooffnofocus colordiffuse="textdim">icons16/{glyph}.png</textureradiooffnofocus>\n'
            f'{sp}  <radiowidth>16</radiowidth><radioheight>16</radioheight>\n'
            f'{sp}  <radioposx>{x}</radioposx><radioposy>{y}</radioposy>{ons}\n'
            f'{sp}</control>\n')

def icon_button(cid, glyph, w, h, clicks, indent=8):
    """Plain buttons have no radio texture, so the glyph rides in a group."""
    sp = " " * indent
    ons = "".join(f"\n{sp}    <onclick>{c}</onclick>" for c in clicks)
    # the group needs an id of its own: a grouplist chains navigation by
    # child id, and an id-less child (id 0) stops the keyboard dead
    return (f'{sp}<control type="group" id="{9000 + int(cid)}">\n'
            f'{sp}  <width>{w}</width><height>{h}</height>\n'
            f'{sp}  <control type="button" id="{cid}">\n'
            f'{sp}    <left>0</left><top>0</top><width>{w}</width><height>{h}</height>\n'
            f'{sp}    <label></label>{ons}\n'
            f'{sp}  </control>\n'
            f'{sp}  <control type="image">\n'
            f'{sp}    <left>{(w-16)//2}</left><top>{(h-16)//2}</top><width>16</width><height>16</height>\n'
            f'{sp}    <texture>icons16/{glyph}.png</texture>\n'
            f'{sp}  </control>\n'
            f'{sp}</control>\n')

def osd_transport(top):
    """Icon buttons: each is a group holding the button plus its glyph, so the
    grouplist still lays them out one per slot."""
    s = f"""      <control type="grouplist" id="201">
        <left>13</left><top>{top}</top><width>560</width><height>36</height>
        <orientation>horizontal</orientation><itemgap>6</itemgap>
        <onup>203</onup><ondown>202</ondown>
"""
    for cid, kind, glyph, acts in OSD_BUTTONS:
        if kind == "radiobutton":
            s += icon_radio(cid, glyph, 86, 36, acts)
        else:
            s += icon_button(cid, glyph, 86, 36, acts)
    s += "      </control>\n"
    return s

# Set by every media browser as it closes (onunload), so the OSD knows which
# add-on is playing: a plugin's resolved stream path no longer names it.
PLUGIN_PROP = "Window(Home).Property(arthuros.plugin)"
LIVE = "[PVR.IsPlayingTV | PVR.IsPlayingRadio]"

def osd_buttons(gid, top, buttons, onup, ondown):
    """A row of text buttons: (id or None, width, label, [actions], visible).
    A leading ("caption", ...) entry becomes a label in front of the row; it
    stays outside the grouplist, where a label would stop keyboard focus."""
    s, left = "", 13
    if buttons and buttons[0][0] == "caption":
        _, w, label, _, _ = buttons[0]
        buttons = buttons[1:]
        s += (f"      <control type=\"label\">\n        <left>{left}</left><top>{top}</top>"
              f"<width>{w}</width><height>30</height>\n"
              f"        <font>chromesmall</font><textcolor>textdim</textcolor><aligny>center</aligny>\n"
              f"        <label>{label}</label>\n      </control>\n")
        left += w + 6
    s += f"""      <control type="grouplist" id="{gid}">
        <left>{left}</left><top>{top}</top><width>{879 - left}</width><height>30</height>
        <orientation>horizontal</orientation><itemgap>6</itemgap>
        <onup>{onup}</onup><ondown>{ondown}</ondown>
"""
    for cid, w, label, acts, vis in buttons:
        kind = "radiobutton" if cid in (608, 804) else "button"
        idattr = f' id="{cid}"' if cid else ""
        s += f'        <control type="{kind}"{idattr}>\n'
        s += f"          <width>{w}</width><height>30</height>\n"
        s += f"          <label>{label}</label>\n"
        s += "".join(f"          <onclick>{x}</onclick>\n" for x in acts)
        if vis:
            s += f"          <visible>{vis}</visible>\n"
        s += "        </control>\n"
    return s + "      </control>\n"

CLOSE = (9951, 140, "$LOCALIZE[15067]", ["Dialog.Close(all,true)", "Action(FullScreen)"], None)
SETTINGS = ("caption", 110, "$LOCALIZE[5]:", [], None)
# short labels, so a row still fits at the Extra large font sizes
ADDON = (9960, 120, "$LOCALIZE[24000]", [f"Addon.OpenSettings($INFO[{PLUGIN_PROP}])"],
         f"!String.IsEmpty({PLUGIN_PROP})")
AUDIO = (9962, 100, "$LOCALIZE[292]", ["ActivateWindow(OSDAudioSettings)"], None)

def osd_extras(top, kind="video"):
    """Two rows under the transport: player actions, then the settings Kodi
    keeps for the thing playing (Estuary's OSD offers the same set)."""
    if kind == "game":
        row1 = [(9970, 180, "$LOCALIZE[35249]", ["ActivateWindow(InGameSaves)"], None),
                (9971, 140, "$LOCALIZE[13007]", ["PlayerControl(Reset)"], None),
                CLOSE]
        row2 = [SETTINGS,
                (9972, 110, "$LOCALIZE[587]", ["ActivateWindow(GameVideoFilter)"], None),
                (9973, 130, "$LOCALIZE[31997]", ["ActivateWindow(GameStretchMode)"], None),
                (9974, 140, "$LOCALIZE[35227]", ["ActivateWindow(GameVideoRotation)"], None),
                (9975, 120, "$LOCALIZE[13376]", ["ActivateWindow(GameVolume)"], None),
                (9976, 140, "$LOCALIZE[10038]", ["ActivateWindow(GameAdvancedSettings)"], None)]
    else:
        row1 = [(87, 150, "$LOCALIZE[136]", ["ActivateWindow(PlayerControls)"], None),
                (608, 150, "$LOCALIZE[264]", ["PVR.ToggleRecordPlayingChannel"], LIVE)]
        if kind == "video":
            row1 += [(804, 170, "$LOCALIZE[33061]", ["PlayerControl(ShowVideoMenu)"], "VideoPlayer.HasMenu"),
                     (9950, 220, "$LOCALIZE[31998]", ["ActivateWindow(SubtitleSearch)"], None)]
        row1 += [CLOSE]
        if kind == "video":
            row2 = [SETTINGS,
                    (9961, 100, "$LOCALIZE[291]", ["ActivateWindow(OSDVideoSettings)"], None),
                    AUDIO,
                    (9963, 150, "$LOCALIZE[287]", ["ActivateWindow(OSDSubtitleSettings)"], None),
                    (9964, 150, "$LOCALIZE[298]", ["ActivateWindow(VideoBookmarks)"], None),
                    ADDON]
        else:
            row2 = [SETTINGS, AUDIO, ADDON]
    return (osd_buttons(202, top, row1, 201, 203)
            + osd_buttons(203, top + 36, row2, 202, 201))

def osd_window(name, kind="video"):
    video = kind == "video"
    body  = f"""      <control type="group" id="200">
        <left>0</left><top>0</top><width>892</width><height>240</height>
      </control>
      <control type="group" id="698">
        <left>0</left><top>0</top><width>892</width><height>240</height>
      </control>
"""
    if not video:
        body += """      <control type="group" id="699">
        <left>0</left><top>0</top><width>892</width><height>240</height>
      </control>
"""
    body += """      <control type="image">
        <left>13</left><top>36</top><width>120</width><height>120</height>
        <texture border="2">panel_raised.png</texture>
      </control>
      <control type="image">
        <left>19</left><top>42</top><width>108</width><height>108</height>
        <texture fallback="DefaultVideo.png">$INFO[Player.Art(thumb)]</texture>\n        <aspectratio>keep</aspectratio>
      </control>
      <control type="label">
        <left>146</left><top>38</top><width>730</width><height>26</height>
        <font>bigbold</font>
        <label>$VAR[NowPlayingVar]</label>
      </control>
      <control type="label">
        <left>146</left><top>68</top><width>730</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$INFO[Player.Time] / $INFO[Player.Duration]</label>
      </control>
      <control type="progress">
        <left>146</left><top>96</top><width>730</width><height>18</height>
        <info>Player.Progress</info>
      </control>
"""
    body += osd_transport(166)
    body += osd_extras(210, kind)
    return dialog(name, 892, 288, body, default="602", icon="icons24/audio.png",
                  dim=False, heading=False)

# ====================================================== info dialogs
def info_dialog(name, ids=None):
    body  = well(10, 36, 500, 260, "panel_sunken_grey.png")
    body += """      <control type="image">
        <left>20</left><top>46</top><width>150</width><height>220</height>
        <texture border="2">panel_raised.png</texture>
      </control>
      <control type="image">
        <left>26</left><top>52</top><width>138</width><height>208</height>
        <texture fallback="DefaultVideo.png">$INFO[ListItem.Art(poster)]</texture>\n        <aspectratio>keep</aspectratio>
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
    body += well(520, 36, 370, 260, "panel_sunken.png")
    body += """      <control type="textbox">
        <left>528</left><top>44</top><width>354</width><height>244</height>
        <font>small</font>
        <label>$INFO[ListItem.Plot]$INFO[ListItem.Comment]</label>
      </control>
"""
    body += well(10, 304, 880, 120, "panel_sunken.png")
    body += """      <control type="panel" id="50">
        <left>16</left><top>310</top><width>868</width><height>108</height>
        <onup>9001</onup><ondown>9001</ondown>
        <itemlayout height="108" width="90">
          <control type="image">
            <left>4</left><top>2</top><width>80</width><height>80</height>
            <texture fallback="DefaultActor.png">$INFO[ListItem.Icon]</texture>\n            <aspectratio>keep</aspectratio>
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
            <texture fallback="DefaultActor.png">$INFO[ListItem.Icon]</texture>\n            <aspectratio>keep</aspectratio>
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
    # GUIDialogPVRGuideInfo.cpp / RecordingInfo.cpp). Kodi hides or disables the
    # ones that don't apply; hidden ones drop out of the grouplist row.
    # Button 5 (Cast/Plot toggle) is left out on purpose: without it Kodi lets
    # the skin keep the plot and the cast list both on screen.
    rows = INFO_BUTTONS[name]
    chunks = [rows[i:i + 4] for i in range(0, len(rows), 4)]
    def row(gid, items, top, up, down):
        s = (f"      <control type=\"grouplist\" id=\"{gid}\">\n"
             f"        <left>13</left><top>{top}</top><width>874</width><height>30</height>\n"
             "        <orientation>horizontal</orientation><align>center</align><itemgap>6</itemgap>\n"
             f"        <onup>{up}</onup><ondown>{down}</ondown>\n")
        for cid, sid in items:
            lab = f"<label>$LOCALIZE[{sid}]</label>" if sid else ""
            # chrome font: these rows stay one line high in every fontset
            s += (f"        <control type=\"button\" id=\"{cid}\"><width>212</width><height>30</height>"
                  f"<font>chrome</font><textoffsetx>4</textoffsetx><align>center</align>{lab}</control>\n")
        return s + "      </control>\n"
    gids = [9001 + i for i in range(len(chunks))]
    for i, items in enumerate(chunks):
        up = gids[i - 1] if i else 50
        down = gids[i + 1] if i + 1 < len(gids) else 50
        body += row(gids[i], items, 434 + 34 * i, up, down)
    ids = {k: v for k, v in (ids or {}).items() if int(k) < 100 or int(k) == 140}
    body += stubs(ids, {1, 50} | {c for c, _ in rows})
    return dialog(name, 900, 440 + 34 * len(chunks), body, default=str(rows[0][0]),
                  icon="icons24/movies.png", title="$VAR[InfoTitleVar]")

# label None: Kodi writes the label itself
INFO_BUTTONS = {
 "DialogVideoInfo": [(8, 208), (9, 13404), (11, 20410), (14, 40001), (15, 40211),
                     (6, 184), (7, 38023), (10, 13511), (12, 20413), (13, 20339)],
 "DialogMusicInfo": [(8, 208), (6, None), (7, None), (10, None), (12, None)],
 "DialogPVRInfo":   [(10, 19190), (8, 19687), (5, 19000), (6, None), (9, 19061),
                     (11, 826), (4, 19003), (7, 186)],
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
    body += """      <control type="textbox">
        <left>18</left><top>220</top><width>864</width><height>134</height>
        <font>small</font>
        <autoscroll delay="6000" time="2500" repeat="6000">true</autoscroll>
        <!-- Kodi 21 exposes add-on details as ListItem.Addon* info labels;
             the old Addon.* item properties are always empty. -->
        <label>$INFO[ListItem.AddonDescription]$INFO[ListItem.AddonDisclaimer,[CR][CR]]$INFO[ListItem.AddonNews,[CR][CR]]</label>
      </control>
      <control type="grouplist">
        <left>13</left><top>370</top><width>874</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>6</itemgap>
        <ondown>9</ondown>
        <control type="button" id="12"><width>210</width><height>32</height><label>$LOCALIZE[502]</label></control>
        <control type="button" id="6"><width>210</width><height>32</height><label>$LOCALIZE[24038]</label></control>
        <control type="button" id="7"><width>210</width><height>32</height><label>$LOCALIZE[24022]</label></control>
        <control type="button" id="8"><width>210</width><height>32</height><label>$LOCALIZE[24138]</label></control>
      </control>
      <control type="grouplist">
        <left>13</left><top>408</top><width>874</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>6</itemgap>
        <onup>12</onup>
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
def keyboard_window():
    rows = [range(100,113), range(120,133), range(140,153), range(160,173)]
    body  = well(10, 36, 880, 46, "panel_sunken.png")
    body += """      <control type="label" id="311">
        <left>-3000</left><top>0</top><width>200</width><height>24</height>
      </control>
      <control type="edit" id="312">
        <left>16</left><top>42</top><width>868</width><height>34</height>
        <font>big</font>
      </control>
      <control type="label" id="313"><left>-3000</left><top>0</top><width>200</width><height>24</height></control>
      <control type="label" id="314"><left>-3000</left><top>0</top><width>200</width><height>24</height></control>
"""
    top = 92
    for r, ids in enumerate(rows):
        body += f"""      <control type="grouplist">
        <left>14</left><top>{top + r*44}</top><width>876</width><height>40</height>
        <orientation>horizontal</orientation><itemgap>4</itemgap>
"""
        for cid in ids:
            body += f"""        <control type="button" id="{cid}">
          <width>62</width><height>40</height>
          <font>big</font><align>center</align><textoffsetx>0</textoffsetx>
        </control>
"""
        body += "      </control>\n"
    modrow = top + 4*44
    body += f"""      <control type="grouplist">
        <left>14</left><top>{modrow}</top><width>876</width><height>36</height>
        <orientation>horizontal</orientation><itemgap>4</itemgap>
        <control type="radiobutton" id="302"><width>104</width><height>36</height><font>chromebold</font><textoffsetx>4</textoffsetx><label>$LOCALIZE[20178]</label></control>
        <control type="radiobutton" id="303"><width>136</width><height>36</height><font>chromebold</font><textoffsetx>4</textoffsetx><label>$LOCALIZE[20179]</label></control>
        <control type="radiobutton" id="304"><width>118</width><height>36</height><font>chromebold</font><textoffsetx>4</textoffsetx><label>$LOCALIZE[20180]</label></control>
        <control type="button" id="32"><width>160</width><height>36</height><label>$LOCALIZE[31912]</label></control>
        <control type="button" id="8"><width>96</width><height>36</height><label>&lt;-</label></control>
        <control type="button" id="305"><width>56</width><height>36</height><label>&lt;</label></control>
        <control type="button" id="306"><width>56</width><height>36</height><label>&gt;</label></control>
      </control>
      <control type="grouplist">
        <left>14</left><top>{modrow+42}</top><width>876</width><height>34</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>8</itemgap>
        <control type="button" id="300"><width>170</width><height>34</height><label>$LOCALIZE[20177]</label></control>
        <control type="button" id="301"><width>170</width><height>34</height><label>$LOCALIZE[222]</label></control>
        <control type="button" id="308"><width>170</width><height>34</height><label>$LOCALIZE[192]</label></control>
        <control type="button" id="309"><width>170</width><height>34</height><label>$LOCALIZE[31917]</label></control>
        <control type="button" id="310"><width>120</width><height>34</height><label>$LOCALIZE[31918]</label></control>
      </control>
      <control type="button" id="307"><left>-3000</left><top>0</top><width>100</width><height>30</height></control>
"""
    return dialog("DialogKeyboard", 900, modrow + 86, body, default="300",
                  icon="icons24/file.png")

def numeric_window():
    body  = well(10, 36, 340, 44, "panel_sunken.png")
    body += """      <control type="label" id="4">
        <left>18</left><top>40</top><width>324</width><height>36</height>
        <font>big</font><align>center</align>
      </control>
"""
    keys = [(10+i) for i in range(10)]
    grid = [[17,18,19],[14,15,16],[11,12,13],[23,10,21]]
    labels = {10:"0",11:"1",12:"2",13:"3",14:"4",15:"5",16:"6",17:"7",18:"8",19:"9",
              21:"OK",23:"&lt;-"}
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
    # up off screen. It also resizes 999 to fit however many entries there are.
    W = 380
    out["DialogContextMenu"] = (H + "<window>\n  <defaultcontrol>996</defaultcontrol>\n"
      "  <coordinates><left>0</left><top>0</top></coordinates>\n  <controls>\n"
      f"    <control type=\"image\" id=\"999\">\n"
      f"      <left>0</left><top>0</top><width>{W}</width><height>440</height>\n"
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
      f"      <left>10</left><top>38</top><width>{W-20}</width><height>392</height>\n"
      "      <orientation>vertical</orientation><itemgap>2</itemgap>\n"
      "      <control type=\"button\" id=\"1000\">\n"
      f"        <width>{W-20}</width><height>30</height>\n"
      "        <align>left</align><textoffsetx>12</textoffsetx>\n"
      "      </control>\n"
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

    out["DialogBusy"] = (H + "<window>\n  <zorder>5</zorder>\n  <controls>\n"
      "    <include>Dialog_Dim</include>\n"
      "    <control type=\"group\">\n"
      "      <centerleft>50%</centerleft><centertop>50%</centertop>\n"
      "      <width>360</width><height>120</height>\n"
      "      <include content=\"Dialog_Box\">\n"
      "        <param name=\"width\" value=\"360\" /><param name=\"height\" value=\"120\" />\n"
      "        <param name=\"innerwidth\" value=\"354\" /><param name=\"icon\" value=\"icons24/program.png\" />\n"
      "        <param name=\"title\" value=\"$LOCALIZE[503]\" />\n"
      "        <param name=\"boxes\" value=\"none\" />\n"
      "      </include>\n"
      "      <control type=\"label\">\n"
      "        <left>12</left><top>40</top><width>336</width><height>26</height>\n"
      "        <align>center</align><font>bold</font><label>$LOCALIZE[20186]</label>\n"
      "      </control>\n"
      "      <control type=\"progress\">\n"
      "        <left>16</left><top>74</top><width>328</width><height>22</height>\n"
      "        <info>Window(busydialog).Property(Busy.Progress)</info>\n"
      "      </control>\n"
      "    </control>\n  </controls>\n</window>\n")

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

    body = ("      <control type=\"label\">\n"
            "        <left>16</left><top>38</top><width>560</width><height>26</height>\n"
            "        <font>bold</font><label>$VAR[NowPlayingVar]</label>\n      </control>\n"
            "      <control type=\"slider\" id=\"401\">\n"
            "        <left>16</left><top>70</top><width>860</width><height>24</height>\n      </control>\n"
            "      <control type=\"slider\" id=\"403\">\n"
            "        <left>-3000</left><top>0</top><width>200</width><height>24</height>\n      </control>\n"
            "      <control type=\"label\">\n"
            "        <left>16</left><top>100</top><width>420</width><height>22</height>\n"
            "        <font>small</font><label>$INFO[Player.SeekTime]$INFO[Player.Time]</label>\n      </control>\n"
            "      <control type=\"label\">\n"
            "        <left>456</left><top>100</top><width>420</width><height>22</height>\n"
            "        <font>small</font><align>right</align><label>$INFO[Player.Duration]</label>\n      </control>\n")
    out["DialogSeekBar"] = dialog("DialogSeekBar", 892, 134, body, icon="icons24/movies.png",
                                  dim=False, heading=False, zorder=3)

    body = (well(10, 36, 840, 380, "panel_sunken.png")
            + "      <control type=\"textbox\" id=\"5\">\n"
              "        <left>18</left><top>44</top><width>806</width><height>364</height>\n"
              "        <font>small</font>\n      </control>\n"
              "      <control type=\"scrollbar\" id=\"60\">\n"
              "        <left>828</left><top>44</top><width>18</width><height>364</height>\n      </control>\n")
    out["DialogTextViewer"] = dialog("DialogTextViewer", 860, 430, body, default="5",
                                     icon="icons24/file.png")

    body = ("      <control type=\"label\" id=\"10\">\n"
            "        <left>16</left><top>40</top><width>500</width><height>26</height>\n"
            "        <font>bold</font>\n      </control>\n"
            "      <control type=\"label\" id=\"12\">\n"
            "        <left>16</left><top>40</top><width>500</width><height>26</height>\n"
            "        <align>right</align>\n      </control>\n"
            "      <control type=\"slider\" id=\"11\">\n"
            "        <left>16</left><top>74</top><width>500</width><height>28</height>\n      </control>\n"
            "      <control type=\"grouplist\">\n"
            "        <left>13</left><top>112</top><width>506</width><height>30</height>\n"
            "        <orientation>horizontal</orientation><align>center</align><itemgap>8</itemgap>\n"
            "        <control type=\"button\" id=\"13\"><width>200</width><height>30</height></control>\n"
            "        <control type=\"button\" id=\"14\"><width>200</width><height>30</height></control>\n"
            "      </control>\n")
    out["DialogSlider"] = dialog("DialogSlider", 532, 158, body, default="11",
                                 icon="icons24/settings.png")

    body = ("      <control type=\"label\" id=\"30\">\n"
            "        <left>16</left><top>40</top><width>540</width><height>26</height>\n"
            "        <font>bold</font>\n      </control>\n"
            "      <control type=\"label\" id=\"31\">\n"
            "        <left>16</left><top>68</top><width>540</width><height>22</height>\n"
            "        <font>small</font><textcolor>textdim</textcolor>\n      </control>\n"
            "      <control type=\"progress\" id=\"32\">\n"
            "        <left>16</left><top>98</top><width>540</width><height>22</height>\n      </control>\n")
    out["DialogExtendedProgressBar"] = dialog("DialogExtendedProgressBar", 572, 142, body,
                                              icon="icons24/program.png", heading=True)

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
    out["Startup"] = (H + "<window>\n"
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
      ("$LOCALIZE[20043]", "masterlock",      "mastermode",                        "System.HasLocks"),
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
    for cid, kind in ((450, "list"), (451, "panel")):
        vis = "" if cid == 450 else "        <visible>Control.IsVisible(451)</visible>\n"
        body += f"""      <control type="{kind}" id="{cid}">
        <left>16</left><top>74</top><width>848</width><height>316</height>
        <onleft>413</onleft><onright>60</onright>
        <onup>{cid}</onup><ondown>413</ondown>
        <pagecontrol>60</pagecontrol>
        <scrolltime tween="linear">0</scrolltime>
        <itemlayout height="26" width="848">
          <control type="image">
            <left>4</left><top>5</top><width>16</width><height>16</height>
            <texture fallback="DefaultFolder.png">$INFO[ListItem.Icon]</texture>
            <aspectratio>keep</aspectratio>
          </control>
          <control type="label">
            <left>28</left><top>0</top><width>640</width><height>26</height>
            <aligny>center</aligny><label>$INFO[ListItem.Label]</label>
          </control>
          <control type="label">
            <left>28</left><top>0</top><width>816</width><height>26</height>
            <align>right</align><aligny>center</aligny><font>small</font>
            <textcolor>textdim</textcolor><label>$INFO[ListItem.Label2]</label>
          </control>
        </itemlayout>
        <focusedlayout height="26" width="848">
          <control type="image">
            <left>0</left><top>0</top><width>848</width><height>26</height>
            <texture>bar_blue.png</texture>
          </control>
          <control type="image">
            <left>4</left><top>5</top><width>16</width><height>16</height>
            <texture fallback="DefaultFolder.png">$INFO[ListItem.Icon]</texture>
            <aspectratio>keep</aspectratio>
          </control>
          <control type="label">
            <left>28</left><top>0</top><width>640</width><height>26</height>
            <font>bold</font><textcolor>textinv</textcolor>
            <aligny>center</aligny><label>$INFO[ListItem.Label]</label>
          </control>
          <control type="label">
            <left>28</left><top>0</top><width>816</width><height>26</height>
            <align>right</align><aligny>center</aligny><font>small</font>
            <textcolor>textinv</textcolor><label>$INFO[ListItem.Label2]</label>
          </control>
        </focusedlayout>
      </control>
"""
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
        <control type="button" id="415"><width>230</width><height>32</height><label>$LOCALIZE[20309]</label></control>
        <control type="togglebutton" id="416"><width>200</width><height>32</height></control>
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
    body += well(10, 36, 660, 200, "panel_sunken.png")
    body += """      <control type="list" id="10">
        <left>16</left><top>42</top><width>648</width><height>188</height>
        <onleft>11</onleft><onright>11</onright>
        <onup>10</onup><ondown>12</ondown>
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
      <control type="grouplist">
        <left>13</left><top>244</top><width>654</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>6</itemgap>
        <onup>10</onup><ondown>12</ondown>
        <control type="button" id="11"><width>210</width><height>32</height></control>
        <control type="button" id="13"><width>210</width><height>32</height></control>
        <control type="button" id="14"><width>210</width><height>32</height></control>
      </control>
      <control type="edit" id="12">
        <left>13</left><top>286</top><width>654</width><height>32</height>
        <onup>11</onup><ondown>20</ondown>
      </control>
      <control type="button" id="20">
        <left>13</left><top>324</top><width>654</width><height>32</height>
        <align>left</align><textoffsetx>12</textoffsetx>
        <onup>12</onup><ondown>18</ondown>
      </control>
      <control type="grouplist">
        <left>13</left><top>366</top><width>654</width><height>32</height>
        <orientation>horizontal</orientation><align>center</align><itemgap>8</itemgap>
        <onup>20</onup>
        <control type="button" id="18"><width>280</width><height>32</height><label>$LOCALIZE[186]</label></control>
        <control type="button" id="19"><width>280</width><height>32</height><label>$LOCALIZE[222]</label></control>
      </control>
      <control type="scrollbar" id="60"><left>-3000</left><top>0</top><width>18</width><height>100</height></control>
"""
    return dialog("DialogMediaSource", 680, 414, body, default="10",
                  icon="icons24/harddisk.png", heading=False)



def system_info():
    """Kodi's contract (GUIWindowSystemInfo.cpp): the focused button 94-101 IS
    the selected section; Kodi writes the section title to 40, up to twelve
    lines to 2-13, app/version to 52, build date to 53, and shows textbox 30
    only for the privacy policy. The skin supplies the button labels."""
    sections = [(95, 20037, "file"), (94, 13277, "harddisk"), (96, 13279, "network"),
                (97, 13280, "movies"), (98, 13281, "program"), (99, 19191, "tvshows"),
                (100, 12389, "file"), (101, 12396, "favourites")]
    body  = well(6, 34, 300, 494, "panel_sunken_grey.png")
    body += """      <control type="grouplist">
        <left>12</left><top>40</top><width>288</width><height>482</height>
        <orientation>vertical</orientation><itemgap>3</itemgap>
        <onup>9100</onup><ondown>9100</ondown>
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
    body += """      <control type="label" id="40">
        <left>324</left><top>40</top><width>670</width><height>28</height>
        <font>bigbold</font>
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
    body += """      <control type="textbox" id="30">
        <left>324</left><top>76</top><width>670</width><height>390</height>
        <font>small</font>
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
    return (H + "<window>\n  <controls>\n"
      "    <control type=\"group\" id=\"0\"><left>0</left><top>0</top><width>1024</width><height>600</height></control>\n"
      "    <control type=\"group\" id=\"1\"><left>0</left><top>0</top><width>1024</width><height>600</height></control>\n"
      "    <control type=\"videowindow\">\n"
      "      <left>0</left><top>0</top><width>1024</width><height>600</height>\n    </control>\n"
      "    <control type=\"group\">\n"
      "      <left>6</left><top>6</top><width>620</width><height>84</height>\n"
      "      <visible>Player.ShowCodec</visible>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"620\" /><param name=\"height\" value=\"84\" /></include>\n"
      "      <control type=\"label\" id=\"10\"><left>10</left><top>6</top><width>600</width><height>24</height><font>small</font></control>\n"
      "      <control type=\"label\" id=\"11\"><left>10</left><top>30</top><width>600</width><height>24</height><font>small</font></control>\n"
      "      <control type=\"label\" id=\"12\"><left>10</left><top>54</top><width>600</width><height>24</height><font>small</font></control>\n"
      "    </control>\n  </controls>\n</window>\n")

def slideshow():
    return (H + "<window>\n  <controls>\n"
      "    <control type=\"image\">\n      <left>0</left><top>0</top><width>1024</width><height>600</height>\n"
      "      <texture>bar_dgrey.png</texture>\n    </control>\n"
      "    <!-- Kodi renders the picture itself; the skin only adds the caption. -->\n"
      "    <control type=\"group\">\n"
      "      <left>6</left><top>568</top><width>1012</width><height>26</height>\n"
      "      <visible>!Slideshow.IsPaused + Player.ShowInfo</visible>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"1012\" /><param name=\"height\" value=\"26\" /></include>\n"
      "      <control type=\"label\"><left>10</left><top>0</top><width>990</width><height>26</height>\n"
      "        <font>small</font><label>$INFO[Slideshow.Filename]</label></control>\n"
      "    </control>\n  </controls>\n</window>\n")

def music_vis():
    return (H + "<window>\n  <controls>\n"
      "    <control type=\"visualisation\">\n"
      "      <left>0</left><top>0</top><width>1024</width><height>600</height>\n    </control>\n"
      "    <control type=\"group\">\n"
      "      <left>6</left><top>480</top><width>1012</width><height>84</height>\n"
      "      <visible>Player.ShowInfo</visible>\n"
      "      <include content=\"Win_Frame\"><param name=\"width\" value=\"1012\" /><param name=\"height\" value=\"84\" /></include>\n"
      "      <control type=\"image\"><left>6</left><top>6</top><width>72</width><height>72</height>\n"
      "        <texture fallback=\"DefaultAudio.png\">$INFO[Player.Art(thumb)]</texture>\n"
      "        <aspectratio>keep</aspectratio></control>\n"
      "      <control type=\"label\"><left>90</left><top>6</top><width>910</width><height>26</height>\n"
      "        <font>bigbold</font><label>$INFO[MusicPlayer.Title]</label></control>\n"
      "      <control type=\"label\"><left>90</left><top>34</top><width>910</width><height>22</height>\n"
      "        <font>small</font><label>$INFO[MusicPlayer.Artist] - $INFO[MusicPlayer.Album]</label></control>\n"
      "      <control type=\"progress\"><left>90</left><top>58</top><width>910</width><height>18</height>\n"
      "        <info>Player.Progress</info></control>\n"
      "    </control>\n  </controls>\n</window>\n")

def player_controls():
    body  = """      <control type="image">
        <left>13</left><top>36</top><width>100</width><height>100</height>
        <texture border="2">panel_raised.png</texture>
      </control>
      <control type="image">
        <left>19</left><top>42</top><width>88</width><height>88</height>
        <texture fallback="DefaultAudio.png">$INFO[Player.Art(thumb)]</texture>
        <aspectratio>keep</aspectratio>
      </control>
      <control type="label">
        <left>126</left><top>38</top><width>420</width><height>26</height>
        <font>bigbold</font><label>$VAR[NowPlayingVar]</label>
      </control>
      <control type="label">
        <left>126</left><top>68</top><width>420</width><height>22</height>
        <font>small</font><textcolor>textdim</textcolor>
        <label>$INFO[Player.Time] / $INFO[Player.Duration]</label>
      </control>
      <control type="progress" id="23">
        <left>126</left><top>96</top><width>420</width><height>18</height>
        <info>Player.Progress</info>
      </control>
      <control type="group" id="699"><left>-3000</left><top>0</top><width>10</width><height>10</height></control>
      <control type="button" id="87"><left>-3000</left><top>0</top><width>100</width><height>30</height>
        <onclick>PlayerControl(Play)</onclick></control>
      <control type="grouplist" id="201">
        <left>13</left><top>146</top><width>546</width><height>36</height>
        <orientation>horizontal</orientation><itemgap>6</itemgap>
""" + icon_radio(600, "prev", 84, 36, ["PlayerControl(Previous)"]) \
    + icon_radio(602, "play", 84, 36, ["PlayerControl(Play)"]) \
    + icon_radio(603, "stop", 84, 36, ["PlayerControl(Stop)"]) \
    + icon_radio(605, "next", 84, 36, ["PlayerControl(Next)"]) \
    + icon_radio(607, "shuffle", 84, 36, ["PlayerControl(Random)"]) \
    + icon_button(704, "repeat", 84, 36, ["PlayerControl(Repeat)"]) + """      </control>
"""
    return dialog("PlayerControls", 572, 200, body, default="602",
                  icon="icons24/audio.png", heading=False)

# ====================================================== generic fallbacks
LISTY   = {"list","panel","fixedlist","wraplist"}
PRESSY  = {"button","togglebutton","radiobutton","spincontrolex","sliderex","edit","colorbutton"}

def generic(name, meta, as_dialog=False):
    ids   = {int(k): v for k, v in meta["ids"].items()}
    views = meta.get("views","")
    placed = set()
    body = ""
    if as_dialog: placed.add(1)   # Dialog_Heading owns id 1

    if as_dialog:
        WD, HT = 900, 500
        ox, oy, aw, ah = 10, 36, 880, 420
    else:
        WD, HT = 1012, 534
        ox, oy, aw, ah = 6, 34, 1000, 494

    press = [(i,t) for i,t in ids.items() if t in PRESSY]
    lists = [(i,t) for i,t in ids.items() if t in LISTY]
    texts = [(i,t) for i,t in ids.items() if t == "textbox"]
    labs  = [(i,t) for i,t in ids.items() if t in ("label","fadelabel") and i not in placed]
    bars  = [(i,t) for i,t in ids.items() if t in ("progress","slider")]
    sbs   = [i for i,t in ids.items() if t == "scrollbar"]

    lx, lw = ox, (300 if lists or texts else aw)
    if press:
        body += well(lx, oy, lw, ah, "panel_sunken_grey.png")
        body += (f"      <control type=\"grouplist\">\n"
                 f"        <left>{lx+8}</left><top>{oy+6}</top><width>{lw-16}</width><height>{ah-12}</height>\n"
                 f"        <orientation>vertical</orientation><itemgap>3</itemgap>\n"
                 f"        <onup>9100</onup><ondown>9100</ondown>\n")
        for cid, ct in sorted(press)[:18]:
            body += (f"        <control type=\"{ct}\" id=\"{cid}\">\n"
                     f"          <width>{lw-16}</width><height>30</height>\n"
                     f"          <align>left</align><textoffsetx>12</textoffsetx>\n        </control>\n")
            placed.add(cid)
        body += "      </control>\n"

    rx = ox + lw + 6 if press else ox
    rw = (ox + aw) - rx
    ry, rh = oy, ah

    if lists:
        cid, ct = sorted(lists)[0]
        sb = sbs[0] if sbs else 9600
        lh = rh if not (texts or labs) else rh - 100
        body += list_block(cid, sb, rx, ry, rw, lh, rowh=28,
                           onleft=str(sorted(press)[0][0]) if press else str(cid),
                           ondown=str(cid) if as_dialog else "9100")
        placed.add(cid); placed.add(sb)
        ry += lh + 6; rh -= lh + 6

    if texts and rh > 40:
        cid, _ = sorted(texts)[0]
        body += well(rx, ry, rw, rh, "panel_sunken.png")
        body += (f"      <control type=\"textbox\" id=\"{cid}\">\n"
                 f"        <left>{rx+8}</left><top>{ry+6}</top><width>{rw-16}</width><height>{rh-12}</height>\n"
                 f"        <font>small</font>\n      </control>\n")
        placed.add(cid); ry += rh; rh = 0

    if labs and rh > 24:
        body += well(rx, ry, rw, rh, "panel_sunken_grey.png")
        y = ry + 6
        for cid, ct in sorted(labs):
            if y + 24 > ry + rh: break
            body += (f"      <control type=\"{ct}\" id=\"{cid}\">\n"
                     f"        <left>{rx+10}</left><top>{y}</top><width>{rw-20}</width><height>24</height>\n"
                     f"        <font>small</font>\n      </control>\n")
            placed.add(cid); y += 26

    for cid, ct in sorted(bars):
        body += (f"      <control type=\"{ct}\" id=\"{cid}\">\n"
                 f"        <left>{ox}</left><top>{oy+ah-24}</top><width>{aw}</width><height>20</height>\n"
                 f"      </control>\n")
        placed.add(cid)

    body += stubs(ids, placed)
    default = ""
    if lists:  default = str(sorted(lists)[0][0])
    elif press: default = str(sorted(press)[0][0])
    if as_dialog:
        return dialog(name, WD, HT, body, default=default)
    live = [v.strip() for v in views.split(",") if v.strip() and int(v.strip()) in placed]
    return fullwindow(name, body, default=default, views=",".join(live))

# ====================================================== subtitle search
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
          <control type="image"><left>0</left><top>0</top><width>264</width><height>28</height><texture colordiffuse="select">fill.png</texture><visible>Control.HasFocus(150)</visible></control>
          <control type="image"><left>2</left><top>2</top><width>24</width><height>24</height><texture>$INFO[ListItem.Icon]</texture><aspectratio>keep</aspectratio></control>
          <control type="label"><left>32</left><top>0</top><width>228</width><height>28</height><aligny>center</aligny><textcolor>textinv</textcolor><label>$INFO[ListItem.Label]</label></control>
        </focusedlayout>
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
          <control type="image"><left>0</left><top>0</top><width>556</width><height>28</height><texture colordiffuse="select">fill.png</texture><visible>Control.HasFocus(120)</visible></control>
          <control type="label"><left>6</left><top>0</top><width>400</width><height>28</height><aligny>center</aligny><textcolor>textinv</textcolor><label>$INFO[ListItem.Label2]</label></control>
          <control type="label"><left>410</left><top>0</top><width>140</width><height>28</height><aligny>center</aligny><align>right</align><font>small</font><textcolor>textinv</textcolor><label>$INFO[ListItem.Label]</label></control>
        </focusedlayout>
      </control>
      <control type="scrollbar" id="73">
        <left>864</left><top>70</top><width>18</width><height>378</height>
        <orientation>vertical</orientation><onleft>120</onleft>
      </control>
"""
    return dialog("DialogSubtitles", 900, 466, b, default="150",
                  icon="icons24/video_subtitles.png", title="$LOCALIZE[24012]")

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
          <control type="image"><left>0</left><top>0</top><width>840</width><height>34</height><texture colordiffuse="select">fill.png</texture><visible>Control.HasFocus(3)</visible></control>
          <control type="label"><left>10</left><top>0</top><width>400</width><height>34</height><aligny>center</aligny><textcolor>textinv</textcolor><label>$INFO[ListItem.Label]</label></control>
          <control type="label"><left>420</left><top>0</top><width>410</width><height>34</height><aligny>center</aligny><align>right</align><font>small</font><textcolor>textinv</textcolor><label>$INFO[ListItem.Label2]</label></control>
        </focusedlayout>
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
          <control type="image"><left>0</left><top>0</top><width>840</width><height>34</height><texture colordiffuse="select">fill.png</texture><visible>Control.HasFocus(7)</visible></control>
          <control type="label"><left>10</left><top>0</top><width>820</width><height>34</height><aligny>center</aligny><textcolor>textinv</textcolor><label>$INFO[ListItem.Label]</label></control>
        </focusedlayout>
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
    inc += "  <include name=\"Arthur_GameAgents\">\n" + _game_box(900, 420, "$LOCALIZE[35110]", agents) + "  </include>\n"
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
