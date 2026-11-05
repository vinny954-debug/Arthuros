#!/usr/bin/env python3
"""The desktop, and the editor that lets people rearrange it.

Writes Home.xml, Includes_Home.xml and five custom windows:
  1120 Customise desktop  grid size, reset, and the tiles in order
  1121 Tile              what one tile opens, its icon, name and place
  1122 Choose            a catalogue of menus, direct items, shortcuts, add-ons
  1123 Choose an icon    every icon in the skin
  1124 (invisible)       applies an add-on picked with Skin.SetAddon
  1125 Reset desktop     asks first

A tile lives in skin strings tile.N.<field>, N = 1..36:
  id      a section with a submenu (movies, music ...); empty = opens directly
  lid     a Kodi/skin string id for its name
  pre     a section string id shown before the name ("Movies - Genres")
  name    a name the user typed, or an add-on's title (wins over lid)
  icon    an icon name from media/icons*/
  image   a picture file or an add-on's icon (wins over icon)
  action  the builtin a direct tile runs
  addon   the add-on id, for tiles that run an add-on
Names are looked up from lid at display time, so switching between English
(UK) and English (US) renames the tiles too.

Kodi facts this relies on (checked against the Kodi 21 source):
* onclick strings are resolved ($INFO, $ESCINFO, $VAR, $LOCALIZE) one at a
  time, just before each runs, so a key like tile.$INFO[Skin.String(edit.slot)].icon
  names the slot being edited;
* all conditions of one onclick/onload list are evaluated BEFORE the first
  action runs, so conditions always see the state from before the click;
* a window reloads when the value of one of its <include condition=...>
  changes, so the grid follows home.layout without a skin reload.
"""
import glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
XML = os.path.join(HERE, "skin.arthuros", "xml")
MEDIA = os.path.join(HERE, "skin.arthuros", "media")
sys.path.insert(0, HERE)
import genwindows as gw

# FONTXL: the Extra large fontsets (tile icons shrink to leave room for text)
# XLC: taller rows, for Extra large fonts and for Touch mode
FONTXL = "String.StartsWith(Skin.Font,ExtraLarge)"
XLC = "[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]"
SLOTS = 36
FIELDS = ("id", "lid", "pre", "name", "icon", "image", "action", "addon")
# A static item property called "icon" (or label, label2, thumb) is not a
# property to Kodi: CGUIStaticItem::UpdateProperties turns it into the item's
# art, so ListItem.Property(ico) kept its first value forever. The item
# property for tile.N.icon is therefore "ico".
PROP = {"icon": "ico"}
H = '<?xml version="1.0" encoding="UTF-8"?>\n'

# ------------------------------------------------------------------ catalogue
# section id: (name lid, icon, caption lid, submenu entries)
# entry: (lid, icon, action)
# No ",return": Kodi then fills in the folders above the one opened, so Back
# climbs to the parent menus (My add-ons -> the add-on browser's own menu,
# Movies -> the video library) instead of jumping straight to the desktop.
def vid(path): return f"ActivateWindow(Videos,{path})"
def mus(path): return f"ActivateWindow(Music,{path})"
def pic(path): return f"ActivateWindow(Pictures,{path})"
def prg(path): return f"ActivateWindow(Programs,{path})"
def add(path): return f"ActivateWindow(AddonBrowser,{path})"

LIBREELEC = "System.HasAddon(service.libreelec.settings)"
# On plain Linux (Raspberry Pi OS and the like) there is no LibreELEC
# settings add-on, so the skin's own Network & Bluetooth script stands in.
NETBT = "!System.HasAddon(service.libreelec.settings) + System.Platform.Linux + !System.Platform.Android"
NETBT_ACTION = "RunScript(special://skin/scripts/netbt.py)"

SECTIONS = [
 ("movies", 342, "movies", 31931, [
   (369, "movies_titles", vid("videodb://movies/titles/")),
   (20386, "movies_recent", vid("videodb://recentlyaddedmovies/")),
   (135, "movies_genres", vid("videodb://movies/genres/")),
   (20434, "movies_sets", vid("videodb://movies/sets/")),
   (652, "movies_years", vid("videodb://movies/years/"))]),
 ("tvshows", 20343, "tvshows", 31932, [
   (369, "tvshows_titles", vid("videodb://tvshows/titles/")),
   (20387, "tvshows_recent", vid("videodb://recentlyaddedepisodes/")),
   (626, "tvshows_inprogress", vid("videodb://inprogresstvshows/")),
   (135, "tvshows_genres", vid("videodb://tvshows/genres/"))]),
 ("music", 2, "music", 31933, [
   (133, "music_artists", mus("musicdb://artists/")),
   (132, "music_albums", mus("musicdb://albums/")),
   (134, "music_songs", mus("musicdb://songs/")),
   (135, "music_genres", mus("musicdb://genres/")),
   (136, "playlist_music", mus("special://musicplaylists/")),
   (1038, "addons_music", mus("addons://sources/audio/"))]),
 ("videos", 3, "video", 31934, [
   (744, "video_files", vid("sources://video/")),
   (136, "playlist_video", vid("special://videoplaylists/")),
   (1037, "addons_video", vid("addons://sources/video/")),
   (1036, "favourites", "ActivateWindow(favouritesbrowser)")]),
 ("pictures", 1, "pictures", 31935, [
   (744, "pictures_files", pic("sources://pictures/")),
   (1039, "addons_pictures", pic("addons://sources/image/"))]),
 ("livetv", 31977, "livetv", 31955, [
   (19019, "pvr_channels", "ActivateWindow(TVChannels)"),
   (22020, "pvr_guide", "ActivateWindow(TVGuide)"),
   (19017, "pvr_recordings", "ActivateWindow(TVRecordings)"),
   (19040, "pvr_timers", "ActivateWindow(TVTimers)"),
   (137, "pvr_search", "ActivateWindow(TVSearch)"),
   (19021, "pvr_radio", "ActivateWindow(RadioChannels)")]),
 ("addons", 24001, "addons", 31936, [
   (10040, "addons", "ActivateWindow(AddonBrowser)"),
   (24998, "addons_user", add("addons://user/")),
   (24033, "addons_repo", add("addons://repos/")),
   (137, "addons_search", add("addons://search/")),
   (24041, "addons_zip", "InstallFromZip"),
   (24043, "addons_updates", add("addons://outdated/")),
   (24004, "addons_recent", add("addons://recently_updated/")),
   (24034, "addons_check", "UpdateAddonRepos"),
   (35049, "addons_game", add("addons://sources/game/"))]),
 ("myaddons", 24998, "addons_user", 31937, [
   (593, "addons_all", add("addons://user/all/")),
   (1037, "addons_video", vid("addons://sources/video/")),
   (1038, "addons_music", mus("addons://sources/audio/")),
   (1039, "addons_pictures", pic("addons://sources/image/")),
   (1043, "addons_program", prg("addons://sources/executable/"))]),
 ("programs", 0, "program", 31938, [
   (1043, "addons_program", prg("addons://sources/executable/")),
   (744, "programs_files", prg("sources://programs/"))]),
 ("files", 7, "harddisk", 31941, [
   (7, "harddisk", "ActivateWindow(FileManager)"),
   (1036, "favourites", "ActivateWindow(favouritesbrowser)")]),
 ("settings", 5, "settings", 31942, [
   (13000, "system", "ActivateWindow(SystemSettings)"),
   (14206, "interface", "ActivateWindow(InterfaceSettings)"),
   (14200, "player", "ActivateWindow(PlayerSettings)"),
   (14211, "media", "ActivateWindow(MediaSettings)"),
   (20077, "skin", "ActivateWindow(SkinSettings)"),
   (10007, "info", "ActivateWindow(SystemInfo)"),
   (31992, "settings", "ActivateWindow(Settings)"),
   (14036, "services", "ActivateWindow(ServiceSettings)"),
   (19020, "pvr_client", "ActivateWindow(PVRSettings)", 5),
   (15016, "controllers", "ActivateWindow(GameSettings)", 5),
   (13200, "user", "ActivateWindow(Profiles)"),
   (14111, "events", "ActivateWindow(EventLog)"),
   (31993, "tools", "RunAddon(service.libreelec.settings)", None, LIBREELEC),
   (31996, "network", NETBT_ACTION, None, NETBT),
   (31953, "desktop_edit", "ActivateWindow(1120)")]),
 # every top-level menu Estuary and Confluence offer, in one list
 ("all", 31990, "file_list", 31991, [
   (342, "movies", vid("videodb://movies/titles/")),
   (20343, "tvshows", vid("videodb://tvshows/titles/")),
   (20389, "musicvideos", vid("videodb://musicvideos/titles/")),
   (14022, "video_cover", vid("library://video/"), 3),
   (744, "video_files", vid("sources://video/"), 3),
   (136, "playlist_video", vid("special://videoplaylists/"), 3),
   (14022, "music", mus("library://music/"), 2),
   (744, "music_files", mus("sources://music/"), 2),
   (136, "playlist_music", mus("special://musicplaylists/"), 2),
   (1, "pictures", "ActivateWindow(Pictures)"),
   (19019, "pvr_channels", "ActivateWindow(TVChannels)", 19020),
   (22020, "pvr_guide", "ActivateWindow(TVGuide)", 19020),
   (19017, "pvr_recordings", "ActivateWindow(TVRecordings)", 19020),
   (19040, "pvr_timers", "ActivateWindow(TVTimers)", 19020),
   (19021, "pvr_radio", "ActivateWindow(RadioChannels)"),
   (15016, "games", "ActivateWindow(Games)"),
   (10040, "addons", "ActivateWindow(AddonBrowser)"),
   (24998, "addons_user", add("addons://user/")),
   (0, "program", "ActivateWindow(Programs)"),
   (1036, "favourites", "ActivateWindow(favouritesbrowser)"),
   (8, "weather", "ActivateWindow(Weather)"),
   (7, "harddisk", "ActivateWindow(FileManager)"),
   (5, "settings", "ActivateWindow(Settings)"),
   (20077, "skin", "ActivateWindow(SkinSettings)"),
   (10007, "info", "ActivateWindow(SystemInfo)"),
   (14111, "events", "ActivateWindow(EventLog)"),
   (13200, "user", "ActivateWindow(Profiles)"),
   (31993, "tools", "RunAddon(service.libreelec.settings)", None, LIBREELEC),
   (31996, "network", NETBT_ACTION, None, NETBT),
   (31953, "desktop_edit", "ActivateWindow(1120)"),
   (31976, "power", "ActivateWindow(ShutdownMenu)")]),
]
SEC = {s[0]: s for s in SECTIONS}

def entry(e):
    """(lid, icon, action[, pre[, visible]]) -> dict. pre: a string id shown
    before the name ("Videos - Library"); visible: an extra condition."""
    e = tuple(e) + (None,) * (5 - len(e))
    return dict(lid=e[0], icon=e[1], action=e[2], pre=e[3], vis=e[4])

def entry_label(d, section_lid=None):
    pre = d["pre"] if d["pre"] not in (None, section_lid) else None
    return (f"$LOCALIZE[{pre}] - " if pre is not None else "") + f"$LOCALIZE[{d['lid']}]"

# things a tile can open straight away: (lid, icon, action, caption lid)
DIRECT = [
 (8, "weather", "ActivateWindow(Weather)", 31940),
 (1036, "favourites", "ActivateWindow(favouritesbrowser)", 31939),
 (31976, "power", "ActivateWindow(ShutdownMenu)", 31951),
 (31954, "desktop_edit", "ActivateWindow(1120)", 31951),
]

# shortcut names that only make sense with their section in front
GENERIC = {369, 135, 652, 744, 136, 20434, 593, 13000, 14206, 14200, 14211,
           137, 19019, 22020, 19017, 19040}

# the desktop as it ships: 12 tiles, 4 x 3
DEFAULTS = [("sec", "movies"), ("sec", "tvshows"), ("sec", "music"),
            ("sec", "videos"), ("sec", "pictures"), ("sec", "addons"),
            ("sec", "myaddons"), ("sec", "programs"), ("dir", 1036),
            ("dir", 8), ("sec", "files"), ("sec", "settings")]

LAYOUTS = [("3x3", 3, 3), ("4x3", 4, 3), ("4x4", 4, 4), ("5x4", 5, 4),
           ("5x5", 5, 5), ("6x5", 6, 5), ("6x6", 6, 6)]
DEFAULT_LAYOUT = "4x3"
CAP = {n: c * r for n, c, r in LAYOUTS}

def lcond(name):
    if name == DEFAULT_LAYOUT:   # also covers an empty or unknown value
        return " + ".join(f"!String.IsEqual(Skin.String(home.layout),{n})"
                          for n, _, _ in LAYOUTS if n != DEFAULT_LAYOUT)
    return f"String.IsEqual(Skin.String(home.layout),{name})"

def fits(n):
    """Condition: slot n is inside the current grid."""
    small = [name for name, cap in CAP.items() if cap < n]
    if not small:
        return ""
    if DEFAULT_LAYOUT in small:   # then only the bigger grids hold it
        return "[" + " | ".join(lcond(name) for name, cap in CAP.items() if cap >= n) + "]"
    return " + ".join("!" + lcond(name) for name in small)

# rows = 3..6 -> cell size and how a tile is drawn in it
# ARTHUR_H=768 builds the 4:3 desktop (1024x768, folder xml768): same
# widths, taller rows, bigger icons. tallpass.py does the other windows.
SCREEN_H = int(os.environ.get("ARTHUR_H", "600"))
DY = SCREEN_H - 600
if DY == 0:
    CELL = {3: (150, 175), 4: (113, 131), 5: (90, 105), 6: (75, 87)}
    TILE = {  # icon, icon at XL, title-bar height, font, window boxes
     3: dict(icon=80, iconxl=64, bar=16, font="tilebig", boxes=True),
     4: dict(icon=48, iconxl=32, bar=12, font="tilesmall", boxes=True),
     5: dict(icon=32, iconxl=32, bar=6, font="tilesmall", boxes=False),
     6: dict(icon=32, iconxl=32, bar=6, font="tiletiny", boxes=False),
    }
elif DY == 168:
    CELL = {3: (150, 231), 4: (113, 173), 5: (90, 138), 6: (75, 115)}
    TILE = {
     3: dict(icon=96, iconxl=80, bar=16, font="tilebig", boxes=True),
     4: dict(icon=64, iconxl=48, bar=12, font="tilesmall", boxes=True),
     5: dict(icon=48, iconxl=32, bar=8, font="tilesmall", boxes=False),
     6: dict(icon=48, iconxl=32, bar=6, font="tiletiny", boxes=False),
    }
else:
    raise SystemExit(f"home.py: no desktop layout for height {SCREEN_H}")
ICONDIR = {32: "icons24", 48: "icons", 64: "icons64", 80: "icons80", 96: "icons96"}
PANEL_TOP, PANEL_H = 30, 534 + DY

def geometry(cols, rows):
    cw, ch = CELL[rows]
    pw = cols * cw + 8
    rx = 6 + pw + 6
    return cw, ch, pw, rx, 1018 - rx

# ------------------------------------------------------------------ helpers
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def oc(action, cond=None, tag="onclick"):
    c = f' condition="{cond}"' if cond else ""
    return f"<{tag}{c}>{esc(action)}</{tag}>"

def ind(lines, n):
    return "".join(" " * n + l + "\n" for l in lines)

SLOTKEY = "tile.$INFO[Skin.String(edit.slot)]"

def set_fields(key, values):
    """Actions that make tile `key` hold exactly `values` (others emptied)."""
    out = []
    for f in FIELDS:
        v = values.get(f)
        if v in (None, ""):
            out.append(f"Skin.Reset({key}.{f})")
        else:
            out.append(f'Skin.SetString({key}.{f},"{v}")' if f == "action" else
                       f"Skin.SetString({key}.{f},{v})")
    return out

def sec_values(sid):
    _, lid, icon, _, _ = SEC[sid]
    return {"id": sid, "lid": lid, "icon": icon}

def dir_values(lid):
    for d in DIRECT:
        if d[0] == lid:
            return {"lid": lid, "icon": d[1], "action": d[2]}
    raise KeyError(lid)

def default_values():
    out = []
    for kind, v in DEFAULTS:
        out.append(sec_values(v) if kind == "sec" else dir_values(v))
    return out

ALL_LIDS = []
for s in SECTIONS:
    ALL_LIDS.append(s[1])
    ALL_LIDS += [e[0] for e in s[4]]
ALL_LIDS += [d[0] for d in DIRECT]
ALL_LIDS = list(dict.fromkeys(ALL_LIDS))
PRE_LIDS = list(dict.fromkeys([s[1] for s in SECTIONS] +
                              [entry(e)["pre"] for s in SECTIONS for e in s[4] if entry(e)["pre"] is not None]))

# ---------------------------------------------------------------- variables
def name_vars(var, ctx):
    """$VAR[var] = the display name of the tile item `ctx` points at."""
    p = lambda f: f"{ctx}.Property({f})"
    v = [f'  <variable name="{var}">',
         f'    <value condition="!String.IsEmpty({p("name")})">$INFO[{p("name")}]</value>',
         f'    <value condition="String.IsEmpty({p("lid")})">$LOCALIZE[31961]</value>',
         f'    <value condition="!String.IsEmpty({p("pre")})">$VAR[{var}Pre] - $VAR[{var}Lid]</value>',
         f'    <value>$VAR[{var}Lid]</value>',
         "  </variable>",
         f'  <variable name="{var}Lid">']
    v += [f'    <value condition="String.IsEqual({p("lid")},{l})">$LOCALIZE[{l}]</value>' for l in ALL_LIDS]
    v += ["  </variable>", f'  <variable name="{var}Pre">']
    v += [f'    <value condition="String.IsEqual({p("pre")},{l})">$LOCALIZE[{l}]</value>' for l in PRE_LIDS]
    v += ["  </variable>"]
    return v

def variables():
    v = []
    v += name_vars("HomeTileName", "ListItem")
    v += name_vars("HomeFocusName", "Container(9000).ListItem")
    v += name_vars("EditTileName", "Container(1150).ListItem")
    f = "Container(9000).ListItem.Property"
    for size, d in ((24, "icons24"), (64, "icons64")):
        v += [f'  <variable name="HomeTileIcon{size}">',
              f'    <value condition="!String.IsEmpty({f}(image))">$INFO[{f}(image)]</value>',
              f'    <value condition="!String.IsEmpty({f}(ico))">{d}/$INFO[{f}(ico)].png</value>',
              "    <value></value>", "  </variable>"]
    v += ['  <variable name="HomeCaptionVar">']
    v += [f'    <value condition="String.IsEqual({f}(id),{s[0]})">$LOCALIZE[{s[3]}]</value>' for s in SECTIONS]
    v += [f'    <value condition="String.IsEqual({f}(lid),{d[0]})">$LOCALIZE[{d[3]}]</value>'
          for d in DIRECT if d[3] != 31951]
    v += ["    <value>$LOCALIZE[31951]</value>", "  </variable>"]
    return v

# ------------------------------------------------------------ tile drawing
def tile_body(rows, xl, focused):
    """Controls for one tile, drawn as a miniature Arthur window."""
    cw, ch = CELL[rows]
    t = TILE[rows]
    w, h, b = cw - 4, ch - 4, t["bar"]
    s = t["iconxl"] if xl else t["icon"]
    d = ICONDIR[s]
    L = []
    def img(l, tp, wd, ht, tex, extra=""):
        L.append(f'<control type="image"><left>{l}</left><top>{tp}</top><width>{wd}</width>'
                 f'<height>{ht}</height>{extra}<texture{tex}</texture></control>')
    img(0, 0, w, h, ' border="2" colordiffuse="facetint">panel_raised.png')
    for c in ("accent1", "accent2"):
        img(3, 3, w - 6, b, f' colordiffuse="{c}">fill.png',
            f"<visible>String.IsEqual(ListItem.Property(bar),{c})</visible>")
    img(3, 3 + b - 1, w - 6, 1, ">fill_black.png")
    if t["boxes"]:
        bs = b - 7
        for k in range(3):
            img(w - 9 - bs - (2 - k) * (bs + 3), 3 + (b - bs) // 2, bs, bs,
                ' border="1" colordiffuse="facetint">outline_white.png')
    gap = 3 if rows <= 4 else 2          # small tiles need every row for text
    yi = 3 + b + gap
    img((w - s) // 2, yi, s, s, f">{d}/$INFO[ListItem.Property(ico)].png",
        "<visible>String.IsEmpty(ListItem.Property(image))</visible>")
    img((w - s) // 2, yi, s, s, ">$INFO[ListItem.Property(image)]",
        "<aspectratio>keep</aspectratio><visible>!String.IsEmpty(ListItem.Property(image))</visible>")
    ly = yi + s + gap - 1
    lh = h - (4 if rows <= 4 else 3) - ly
    if focused:
        img(2, ly, w - 4, lh, ' colordiffuse="select">fill.png')
        img(0, 0, w, h, ' border="4" colordiffuse="select">select_ring.png')
    # a textbox, not a label: labels inside list layouts are CGUIListLabel,
    # which never wraps, so long names ended in "..."
    L.append(f'<control type="textbox"><left>4</left><top>{ly}</top><width>{w - 8}</width>'
             f'<height>{lh}</height><font>{t["font"]}</font>'
             f'<textcolor>{"textinv" if focused else "text"}</textcolor>'
             f"<align>center</align><aligny>center</aligny>"
             f"<label>$VAR[HomeTileName]</label></control>")
    return L

def panel_include(name, cols, rows):
    cw, ch, pw, rx, rw = geometry(cols, rows)
    L = [f'<include name="Home_Panel_{name}">',
         f"  <left>10</left><top>{PANEL_TOP + 4}</top><width>{cols * cw}</width><height>{rows * ch}</height>"]
    for xl in (True, False):
        cond = f' condition="{FONTXL}"' if xl else ""
        for kind, foc in (("itemlayout", False), ("focusedlayout", True)):
            L.append(f'  <{kind} width="{cw}" height="{ch}"{cond}>')
            L.append("    <control type=\"group\"><left>2</left><top>2</top>")
            L += ["      " + x for x in tile_body(rows, xl, foc)]
            L.append("    </control>")
            L.append(f"  </{kind}>")
    L.append("</include>")
    return L

def frame_include(name, cols, rows):
    """Everything on the desktop that is not a control you can focus."""
    cw, ch, pw, rx, rw = geometry(cols, rows)
    return f"""<include name="Home_Frame_{name}">
  <control type="image">
    <left>6</left><top>{PANEL_TOP}</top><width>{pw}</width><height>{PANEL_H}</height>
    <texture border="2" colordiffuse="facetint">panel_sunken_grey.png</texture>
  </control>
  <control type="group">
    <left>{rx}</left><top>{PANEL_TOP}</top><width>{rw}</width><height>{PANEL_H}</height>
    <include content="Win_Frame">
      <param name="width" value="{rw}" />
      <param name="height" value="{PANEL_H}" />
    </include>
    <control type="group">
      <left>3</left><top>3</top>
      <include content="Win_Title">
        <param name="width" value="{rw - 6}" />
        <param name="colour" value="accent2" />
        <param name="icon" value="$VAR[HomeTileIcon24]" />
        <param name="label" value="$VAR[HomeFocusName]" />
        <param name="down" value="9010" />
        <param name="boxes" value="home" />
      </include>
    </control>
    <control type="image">
      <left>12</left><top>40</top><width>64</width><height>64</height>
      <aspectratio>keep</aspectratio>
      <texture>$VAR[HomeTileIcon64]</texture>
    </control>
    <control type="label">
      <left>88</left><top>44</top><width>{rw - 100}</width><height>26</height>
      <font>bigbold</font><textcolor>text</textcolor>
      <label>$VAR[HomeFocusName]</label>
    </control>
    <control type="label">
      <left>88</left><top>72</top><width>{rw - 100}</width><height>24</height>
      <font>small</font><textcolor>textdim</textcolor>
      <label>$VAR[HomeCaptionVar]</label>
    </control>
    <control type="image">
      <left>6</left><top>112</top><width>{rw - 12}</width><height>1</height>
      <texture>fill_black.png</texture>
    </control>
    <control type="image">
      <left>6</left><top>118</top><width>{rw - 12}</width><height>{410 + DY}</height>
      <texture border="2" colordiffuse="facetint">panel_sunken.png</texture>
    </control>
  </control>
</include>""".split("\n")

def list_include(name, cols, rows):
    cw, ch, pw, rx, rw = geometry(cols, rows)
    lw = rw - 36
    L = [f'<include name="Home_List_{name}">',
         f"  <left>{rx + 9}</left><top>{PANEL_TOP + 121}</top><width>{lw}</width><height>{404 + DY}</height>"]
    for xl, hgt in ((True, 44), (False, 28)):
        cond = f' condition="{XLC}"' if xl else ""
        for kind, foc in (("itemlayout", "false"), ("focusedlayout", "true")):
            L.append(f'  <{kind} height="{hgt}" width="{lw}"{cond}>')
            L.append(f'    <include content="Home_SubItem"><param name="width" value="{lw}" />'
                     f'<param name="height" value="{hgt}" /><param name="icon" value="{32 if xl else 16}" />'
                     f'<param name="focused" value="{foc}" /><param name="plain" value="{"false" if foc == "true" else "true"}" /></include>')
            L.append(f"  </{kind}>")
    L.append("</include>")
    L.append(f'<include name="Home_Scroll_{name}">')
    L.append(f"  <left>{rx + rw - 24}</left><top>{PANEL_TOP + 121}</top><width>18</width><height>{404 + DY}</height>")
    L.append("</include>")
    return L

SUBITEM = """<include name="Home_SubItem">
  <param name="width" default="370" />
  <param name="height" default="28" />
  <param name="icon" default="16" />
  <param name="focused" default="false" />
  <param name="plain" default="true" />
  <definition>
    <control type="image">
      <left>0</left><top>0</top><width>$PARAM[width]</width><height>$PARAM[height]</height>
      <texture colordiffuse="select">fill.png</texture>
      <visible>$PARAM[focused]</visible>
    </control>
    <control type="image">
      <left>5</left><centertop>50%</centertop><width>$PARAM[icon]</width><height>$PARAM[icon]</height>
      <texture>$INFO[ListItem.Icon]</texture>
    </control>
    <control type="label">
      <left>44</left><right>6</right><top>0</top><height>$PARAM[height]</height>
      <font>normal</font><textcolor>text</textcolor>
      <align>left</align><aligny>center</aligny>
      <label>$INFO[ListItem.Label]</label>
      <visible>$PARAM[plain]</visible>
    </control>
    <control type="label">
      <left>44</left><right>6</right><top>0</top><height>$PARAM[height]</height>
      <font>bold</font><textcolor>textinv</textcolor>
      <align>left</align><aligny>center</aligny>
      <label>$INFO[ListItem.Label]</label>
      <visible>$PARAM[focused]</visible>
    </control>
  </definition>
</include>""".split("\n")

def tile_items(onclick, extra_vis=None, indent=8, bar=True, fit=True):
    """The 36 slot items. onclick(n) -> list of <onclick> lines."""
    out = []
    for n in range(1, SLOTS + 1):
        k = f"tile.{n}"
        vis = [f"[!String.IsEmpty(Skin.String({k}.name)) | !String.IsEmpty(Skin.String({k}.lid))]"]
        if extra_vis:
            vis = [extra_vis(n)] if extra_vis(n) is not None else []
        f = fits(n) if fit else ""
        if f:
            vis.append(f)
        lines = [f'<item id="{n}">',
                 f"  <label>$INFO[Skin.String({k}.name)]</label>",
                 # a bare number would be read as a string id ($LOCALIZE[3] = "Videos")
                 f'  <property name="slot">$NUMBER[{n}]</property>']
        for fld in FIELDS:
            lines.append(f'  <property name="{PROP.get(fld, fld)}">$INFO[Skin.String({k}.{fld})]</property>')
        if bar:
            lines.append(f'  <property name="bar">{"accent1" if n % 3 == 1 else "accent2"}</property>')
        lines += ["  " + x for x in onclick(n)]
        if vis:
            lines.append(f"  <visible>{' + '.join(vis)}</visible>")
        lines.append("</item>")
        out += lines
    return out

# ------------------------------------------------------------------ Home.xml
def home_xml():
    defaults = []
    for n, vals in enumerate(default_values(), 1):
        for f in FIELDS:
            v = vals.get(f)
            if v not in (None, ""):
                defaults.append(f'Skin.SetString(tile.{n}.{f},"{v}")' if f == "action"
                                else f"Skin.SetString(tile.{n}.{f},{v})")
    defaults.append("Skin.SetBool(home.init)")
    L = [H.strip(), "<window>",
         '  <defaultcontrol always="true">9000</defaultcontrol>',
         "  <backgroundcolor>desktop</backgroundcolor>",
         "  <!-- first run (or after Reset skin settings): lay out the shipped desktop -->"]
    L += ["  " + oc(a, "!Skin.HasSetting(home.init)", "onload") for a in defaults]
    L += ["  <!-- Touch mode: watch for a mouse, so the pointer shows only when one is plugged in -->",
          "  " + oc("RunScript(special://skin/scripts/mousewatch.py)",
                    "Skin.HasSetting(touchmode) + String.IsEmpty(Window(Home).Property(arthuros.mousewatch))", "onload")]
    L += ["  <!-- the add-on the OSD offers settings for (media browsers set it as they close) -->",
          "  " + oc("ClearProperty(arthuros.plugin,home)", "!Player.HasMedia", "onload")]
    L += ["  <!-- once, after upgrading from 0.9.1: update shortcut tiles (see migrate_dialog) -->",
          "  " + oc("ActivateWindow(1126)", f"!Skin.HasSetting({MIGRATED})", "onload")]
    L += ["  <controls>", "    <include>Chrome_Desktop</include>", "    <include>Chrome_Menubar</include>", "",
          "    <!-- the frames for the chosen grid size (Customise desktop) -->"]
    L += [f'    <include condition="{lcond(n)}">Home_Frame_{n}</include>' for n, _, _ in LAYOUTS]
    L += ["    <!-- Customise desktop flips home.flip when it closes: a changed include",
          "         condition makes Kodi reload this window, so the tiles are read afresh",
          "         instead of showing their old names for a second -->",
          '    <include condition="Skin.HasSetting(home.flip)">Home_Refresh</include>']
    L += ["", "    <!-- left: the program filer window -->",
          '    <control type="panel" id="9000">']
    L += [f'      <include condition="{lcond(n)}">Home_Panel_{n}</include>' for n, _, _ in LAYOUTS]
    L += ["      <onleft>9000</onleft>", "      <onright>9010</onright>", "      <ondown>9100</ondown>",
          '      <scrolltime tween="linear">0</scrolltime>', "      <pagecontrol>-</pagecontrol>",
          "      <content>"]
    def click(n):
        k = f"tile.{n}"
        return [oc("SetFocus(9010,0)", f"!String.IsEmpty(Skin.String({k}.id))"),
                oc(f"$INFO[Skin.String({k}.action)]", f"String.IsEmpty(Skin.String({k}.id))")]
    L += ind(tile_items(click), 8).rstrip("\n").split("\n")
    L += ["      </content>", "    </control>", "",
          "    <!-- right: the context panel for the focused tile -->",
          '    <control type="list" id="9010">']
    L += [f'      <include condition="{lcond(n)}">Home_List_{n}</include>' for n, _, _ in LAYOUTS]
    L += ["      <onleft>9000</onleft>", "      <onright>9011</onright>", "      <ondown>9010</ondown>",
          "      <onup>9010</onup>", "      <onback>9000</onback>", "      <pagecontrol>9011</pagecontrol>",
          '      <scrolltime tween="linear">0</scrolltime>', "      <content>"]
    # a tile that opens directly still gets one entry, for the pointer
    L += ["        <item><label>$LOCALIZE[31952]</label><icon>$VAR[HomeTileIcon24]</icon>",
          "          <onclick>SetFocus(9000)</onclick><onclick>Action(Select)</onclick>",
          "          <visible>String.IsEmpty(Container(9000).ListItem.Property(id))</visible></item>"]
    for sid, lid, icon, cap, entries in SECTIONS:
        L.append(f"        <!-- {sid} -->")
        for e in map(entry, entries):
            vis = f"String.IsEqual(Container(9000).ListItem.Property(id),{sid})"
            if e["vis"]:
                vis += f" + {e['vis']}"
            L += [f"        <item><label>{entry_label(e, lid)}</label><icon>icons24/{e['icon']}.png</icon>",
                  f"          <onclick>{esc(e['action'])}</onclick>",
                  f"          <visible>{vis}</visible></item>"]
    L += ["      </content>", "    </control>",
          '    <control type="scrollbar" id="9011">']
    L += [f'      <include condition="{lcond(n)}">Home_Scroll_{n}</include>' for n, _, _ in LAYOUTS]
    L += ["      <onleft>9010</onleft>", "      <onright>9000</onright>", "    </control>", "",
          '    <include content="Chrome_Taskbar"><param name="up" value="9000" /></include>',
          "  </controls>", "</window>"]
    return "\n".join(L) + "\n"

def includes_xml():
    L = [H.strip(), "<!-- GENERATED by home.py: the desktop's grids, tiles and names. -->", "<includes>"]
    L += ["  " + x for x in SUBITEM]
    for n, c, r in LAYOUTS:
        L.append(f"  <!-- {n}: {c} across, {r} down -->")
        for part in (frame_include(n, c, r), panel_include(n, c, r), list_include(n, c, r)):
            L += ["  " + x for x in part]
    L += ["  " + x for x in edit_box_includes()]
    L += ['  <include name="Home_Refresh">',
          '    <control type="image"><left>0</left><top>0</top><width>1</width><height>1</height>'
          "<texture>fill.png</texture><visible>false</visible></control>",
          "  </include>"]
    L += variables()
    L.append("</includes>")
    return "\n".join(L) + "\n"

# ----------------------------------------------------------- custom windows
def custom(xml, wid, kind):
    root = f'<window type="dialog" id="{wid}">' if kind == "dialog" else f'<window id="{wid}">'
    return xml.replace("<window>", root, 1)

def ctl(kind, cid, l, t, w, h, body=""):
    i = f' id="{cid}"' if cid else ""
    return (f'      <control type="{kind}"{i}>\n'
            f"        <left>{l}</left><top>{t}</top><width>{w}</width><height>{h}</height>\n"
            + "".join(f"        {b}\n" for b in body if b) + "      </control>\n")

def row_layouts(width, hgt, hxl, body):
    """itemlayout/focusedlayout pairs, XL first. body(h, focused) -> lines."""
    s = ""
    for xl, h in ((True, hxl), (False, hgt)):
        cond = f' condition="{XLC}"' if xl else ""
        for kind, foc in (("itemlayout", False), ("focusedlayout", True)):
            s += f'        <{kind} width="{width}" height="{h}"{cond}>\n'
            if foc:
                s += (f'          <control type="image"><left>0</left><top>0</top><width>{width}</width>'
                      f'<height>{h}</height><texture colordiffuse="select">fill.png</texture></control>\n')
            s += "".join(f"          {b}\n" for b in body(h, foc, xl))
            s += f"        </{kind}>\n"
    return s

def lbl(l, t, w, h, text, foc, font="normal", extra=""):
    return (f'<control type="label"><left>{l}</left><top>{t}</top><width>{w}</width><height>{h}</height>'
            f'<font>{font if not foc else "bold"}</font><textcolor>{"textinv" if foc else "text"}</textcolor>'
            f"<aligny>center</aligny>{extra}<label>{text}</label></control>")

def sunken(l, t, w, h):
    return (f'      <control type="image"><left>{l}</left><top>{t}</top><width>{w}</width><height>{h}</height>'
            f'<texture border="2" colordiffuse="facetint">panel_sunken.png</texture></control>\n')

def heading(l, t, w, sid):
    return (f'      <control type="label"><left>{l}</left><top>{t}</top><width>{w}</width><height>26</height>'
            f"<font>bold</font><textcolor>text</textcolor><label>$LOCALIZE[{sid}]</label></control>\n")

EDIT_ICON = "icons24/desktop_edit.png"

def editor_window():
    """1120: the whole desktop at a glance."""
    b = heading(16, 40, 220, 31956)
    b += '      <control type="grouplist" id="300">\n'
    b += "        <left>16</left><top>70</top><width>220</width><height>450</height>\n"
    b += "        <orientation>vertical</orientation><itemgap>4</itemgap>\n"
    b += "        <onright>320</onright><onup>300</onup><ondown>9100</ondown>\n"
    for i, (n, c, r) in enumerate(LAYOUTS):
        sel = lcond(n) if n != DEFAULT_LAYOUT else \
            f"[String.IsEmpty(Skin.String(home.layout)) | String.IsEqual(Skin.String(home.layout),{n})]"
        b += f'        <control type="radiobutton" id="{301 + i}">\n'
        b += "          <width>220</width><height>34</height>\n"
        b += f"          <label>{c} x {r}  ({c * r})</label>\n"
        b += f"          <onclick>Skin.SetString(home.layout,{n})</onclick>\n"
        b += f"          <selected>{sel}</selected>\n"
        b += "        </control>\n"
    b += ('        <control type="button" id="310">\n'
          "          <width>220</width><height>34</height>\n"
          "          <label>$LOCALIZE[31957]</label>\n"
          "          <onclick>ActivateWindow(1125)</onclick>\n"
          "        </control>\n"
          '        <control type="button" id="311">\n'
          "          <width>220</width><height>34</height>\n"
          "          <label>$LOCALIZE[31958]</label>\n"
          "          <onclick>ActivateWindow(Home)</onclick>\n"
          "        </control>\n"
          "      </control>\n")

    b += heading(256, 40, 400, 31959)
    b += sunken(256, 70, 436, 450)
    lw = 406
    def body(h, foc, xl):
        s = 32
        return [lbl(8, 0, 40, h, "$INFO[ListItem.Property(slot)].", foc, extra="<align>right</align>"),
                f'<control type="image"><left>56</left><top>{(h - s) // 2}</top><width>{s}</width><height>{s}</height>'
                "<texture>icons24/$INFO[ListItem.Property(ico)].png</texture>"
                "<visible>String.IsEmpty(ListItem.Property(image))</visible></control>",
                f'<control type="image"><left>56</left><top>{(h - s) // 2}</top><width>{s}</width><height>{s}</height>'
                "<aspectratio>keep</aspectratio><texture>$INFO[ListItem.Property(image)]</texture>"
                "<visible>!String.IsEmpty(ListItem.Property(image))</visible></control>",
                lbl(98, 0, lw - 104, h, "$VAR[HomeTileName]", foc)]
    lst = ("        <onleft>300</onleft><onright>321</onright><ondown>9100</ondown>\n"
           "        <pagecontrol>321</pagecontrol>\n"
           '        <scrolltime tween="linear">0</scrolltime>\n')
    lst += row_layouts(lw, 38, 48, body)
    def click(n):
        return [oc(f"Skin.SetString(edit.slot,{n})"), oc("ActivateWindow(1121)")]
    lst += "        <content>\n" + ind(tile_items(click, extra_vis=lambda n: None, bar=False), 10) + "        </content>\n"
    b += f'      <control type="list" id="320">\n        <left>259</left><top>73</top><width>{lw}</width><height>444</height>\n' + lst + "      </control>\n"
    b += ctl("scrollbar", 321, 668, 73, 18, 444, ["<onleft>320</onleft>", "<onright>300</onright>"])
    b += sunken(708, 70, 288, 450)
    b += ctl("textbox", None, 720, 80, 264, 430, ["<font>small</font>", "<label>$LOCALIZE[31960]</label>"])
    gw.BOXES["Custom_1120_DesktopEditor"] = "dialog"
    x = gw.fullwindow("Custom_1120_DesktopEditor", b, default="320", icon=EDIT_ICON,
                      title="$LOCALIZE[31954]")
    x = custom(x, 1120, "window")
    return x.replace('<window id="1120">', '<window id="1120">\n  <onunload>Skin.ToggleSetting(home.flip)</onunload>', 1)

def preview_items():
    """1150: the edited tile only, drawn big; also what EditTileName reads."""
    def none(n):
        return []
    items = tile_items(none, extra_vis=lambda n: f"String.IsEqual(Skin.String(edit.slot),{n})", bar=False, fit=False)
    return ind(items, 10)

def lastslot():
    return " + ".join(f"![{lcond(n)} + String.IsEqual(Skin.String(edit.slot),{CAP[n]})]"
                      for n, _, _ in LAYOUTS) + " + !String.IsEqual(Skin.String(edit.slot),36)"

def swap(delta):
    """onclick lines that swap slot edit.slot with its neighbour."""
    out = []
    for n in range(1, SLOTS + 1):
        m = n + delta
        if not 1 <= m <= SLOTS:
            continue
        here = f"String.IsEqual(Skin.String(edit.slot),{n})"
        for f in FIELDS:
            a, bb = f"tile.{n}.{f}", f"tile.{m}.{f}"
            ea, eb = f"String.IsEmpty(Skin.String({a}))", f"String.IsEmpty(Skin.String({bb}))"
            # keep this slot's value, then pull the neighbour's in, then push ours out
            out.append(oc(f"Skin.SetString(swap.{f},$ESCINFO[Skin.String({a})])", f"{here} + !{ea}"))
            out.append(oc(f"Skin.SetString({a},$ESCINFO[Skin.String({bb})])", f"{here} + !{eb}"))
            out.append(oc(f"Skin.Reset({a})", f"{here} + {eb} + !{ea}"))
            out.append(oc(f"Skin.SetString({bb},$ESCINFO[Skin.String(swap.{f})])", f"{here} + !{ea}"))
            out.append(oc(f"Skin.Reset({bb})", f"{here} + {ea} + !{eb}"))
        out.append(oc(f"Skin.SetString(edit.slot,{m})", here))
    return out

def tile_dialog():
    """1121: one tile."""
    W = 640
    k = SLOTKEY
    b = ""
    # preview
    b += sunken(16, 44, 220, 250)
    b += '      <control type="list" id="1150">\n        <left>19</left><top>47</top><width>214</width><height>244</height>\n'
    b += "        <enable>false</enable>\n"
    pv = ['<control type="image"><left>59</left><top>12</top><width>96</width><height>96</height>'
          "<texture>icons96/$INFO[ListItem.Property(ico)].png</texture>"
          "<visible>String.IsEmpty(ListItem.Property(image))</visible></control>",
          '<control type="image"><left>59</left><top>12</top><width>96</width><height>96</height>'
          "<aspectratio>keep</aspectratio><texture>$INFO[ListItem.Property(image)]</texture>"
          "<visible>!String.IsEmpty(ListItem.Property(image))</visible></control>",
          '<control type="textbox"><left>6</left><top>116</top><width>202</width><height>120</height>'
          "<font>bigbold</font><textcolor>text</textcolor><align>center</align><aligny>top</aligny>"
          "<label>$VAR[HomeTileName]</label></control>"]
    for kind in ("itemlayout", "focusedlayout"):
        b += f'        <{kind} width="214" height="244">\n' + "".join(f"          {x}\n" for x in pv) + f"        </{kind}>\n"
    b += "        <content>\n" + preview_items() + "        </content>\n      </control>\n"

    buttons = [
     (1131, 31963, [f"ActivateWindow(1122)"], None),
     (1132, 31964, [f"ActivateWindow(1123)"], None),
     (1133, 31965, [f"Skin.SetImage({k}.image)"], None),
     (1139, 31987, [f"Skin.SetString({k}.image,$ESCINFO[System.AddonIcon(Container(1150).ListItem.Property(addon))])"],
      "!String.IsEmpty(Container(1150).ListItem.Property(addon))"),
     (1134, 31966, None, None),
     (1135, 31967, None, "!String.IsEqual(Skin.String(edit.slot),1)"),
     (1136, 31968, None, lastslot()),
     (1137, 31969, [f"Skin.Reset({k}.{f})" for f in FIELDS], None),
     (1138, 31958, ["Dialog.Close(1121)"], None),
    ]
    b += '      <control type="grouplist" id="1130">\n'
    b += f"        <left>252</left><top>44</top><width>{W - 268}</width>\n"
    b += '        <include content="Home_EditH" condition="!' + XLC + '" />\n'
    b += '        <include content="Home_EditH_XL" condition="' + XLC + '" />\n'
    b += "        <orientation>vertical</orientation><itemgap>4</itemgap>\n"
    for cid, sid, acts, enable in buttons:
        b += f'        <control type="button" id="{cid}">\n'
        b += f"          <width>{W - 268}</width><height>34</height>\n"
        b += "          <align>left</align><textoffsetx>12</textoffsetx>\n"
        b += f"          <label>$LOCALIZE[{sid}]</label>\n"
        if enable:
            b += f"          <enable>{enable}</enable>\n"
        if cid == 1134:   # start the keyboard from the name the tile shows now
            acts_x = [oc(f"Skin.SetString({k}.name,$ESCVAR[EditTileName])",
                         "String.IsEmpty(Container(1150).ListItem.Property(name))"),
                      oc(f"Skin.SetString({k}.name)")]
        elif cid == 1135:
            acts_x = swap(-1)
        elif cid == 1136:
            acts_x = swap(+1)
        else:
            acts_x = [oc(a) for a in acts]
        b += "".join(f"          {a}\n" for a in acts_x)
        b += "        </control>\n"
    b += "      </control>\n"
    # written out here rather than with gw.dialog(): the frame's height follows
    # the font size (Home_EditBox / _XL), which a fixed Dialog_Box cannot do
    x = (H + '<window type="dialog" id="1121">\n  <defaultcontrol>1130</defaultcontrol>\n  <controls>\n'
         "    <include>Dialog_Dim</include>\n    <control type=\"group\">\n"
         f"      <centerleft>50%</centerleft><centertop>50%</centertop><width>{W}</width>\n"
         f'      <include condition="!{XLC}">Home_EditBox</include>\n'
         f'      <include condition="{XLC}">Home_EditBox_XL</include>\n'
         + b + "    </control>\n  </controls>\n</window>\n")
    return x


def pick_actions(values, close="Dialog.Close(1122)"):
    return set_fields(SLOTKEY, values) + [close]

def catalogue_dialog():
    """1122: everything a tile can open."""
    W, Hh = 780, 500
    groups = [("menus", 31971, "folder"), ("direct", 31972, "file_shortcut"),
              ("addon", 31973, "addons_program")]
    groups += [(s[0], s[1], s[2]) for s in SECTIONS]
    b = sunken(16, 44, 246, Hh - 60)
    def gbody(h, foc, xl):
        s = 32 if xl else 16
        return [f'<control type="image"><left>6</left><top>{(h - s) // 2}</top><width>{s}</width><height>{s}</height>'
                "<texture>$INFO[ListItem.Icon]</texture></control>",
                lbl(s + 14, 0, 240 - s - 20, h, "$INFO[ListItem.Label]", foc)]
    g = ('      <control type="list" id="200">\n'
         f"        <left>19</left><top>47</top><width>240</width><height>{Hh - 66}</height>\n"
         "        <onright>210</onright><onleft>200</onleft>\n"
         '        <scrolltime tween="linear">0</scrolltime>\n')
    g += row_layouts(240, 28, 44, gbody)
    g += "        <content>\n"
    for gid, sid, icon in groups:
        g += f'          <item><label>$LOCALIZE[{sid}]</label><icon>icons24/{icon}.png</icon>\n'
        g += f'            <property name="id">{gid}</property>\n'
        if gid == "addon":
            g += ("            <onclick>Skin.Reset(pick.addon)</onclick>\n"
                  "            <onclick>Skin.SetAddon(pick.addon,xbmc.python.pluginsource,xbmc.python.script)</onclick>\n"
                  "            <onclick>ActivateWindow(1124)</onclick>\n")
        else:
            g += "            <onclick>SetFocus(210,0)</onclick>\n"
        g += "          </item>\n"
    g += "        </content>\n      </control>\n"
    b += g
    rw = W - 278 - 16 - 24
    b += sunken(276, 44, rw + 6 + 24, Hh - 60)
    items = []
    def item(label, icon, gid, acts, vis=None):
        s = f"          <item><label>{label}</label><icon>icons24/{icon}.png</icon>\n"
        s += "".join(f"            {oc(a)}\n" for a in acts)
        cond = f"String.IsEqual(Container(200).ListItem.Property(id),{gid})" + (f" + {vis}" if vis else "")
        s += f"            <visible>{cond}</visible></item>\n"
        items.append(s)
    for sid, lid, icon, cap, entries in SECTIONS:
        item(f"$LOCALIZE[{lid}]", icon, "menus", pick_actions(sec_values(sid)))
    for lid, icon, act, cap in DIRECT:
        item(f"$LOCALIZE[{lid}]", icon, "direct", pick_actions({"lid": lid, "icon": icon, "action": act}))
    for sid, slid, sicon, cap, entries in SECTIONS:
        for e in map(entry, entries):
            v = {"lid": e["lid"], "icon": e["icon"], "action": e["action"]}
            if e["pre"] is not None:
                v["pre"] = e["pre"]
            elif e["lid"] in GENERIC and sid != "all":
                v["pre"] = slid
            item(entry_label(e), e["icon"], sid, pick_actions(v), e["vis"])
    def ibody(h, foc, xl):
        s = 32 if xl else 16
        return [f'<control type="image"><left>6</left><top>{(h - s) // 2}</top><width>{s}</width><height>{s}</height>'
                "<texture>$INFO[ListItem.Icon]</texture></control>",
                lbl(s + 14, 0, rw - s - 20, h, "$INFO[ListItem.Label]", foc)]
    r = ('      <control type="list" id="210">\n'
         f"        <left>279</left><top>47</top><width>{rw}</width><height>{Hh - 66}</height>\n"
         "        <onleft>200</onleft><onright>211</onright>\n"
         "        <pagecontrol>211</pagecontrol>\n"
         '        <scrolltime tween="linear">0</scrolltime>\n')
    r += row_layouts(rw, 28, 44, ibody)
    r += "        <content>\n" + "".join(items) + "        </content>\n      </control>\n"
    b += r
    b += ctl("scrollbar", 211, 279 + rw + 3, 47, 18, Hh - 66, ["<onleft>210</onleft>", "<onright>200</onright>"])
    x = gw.dialog("Custom_1122_DesktopChoose", W, Hh, b, default="200", icon=EDIT_ICON,
                  title="$LOCALIZE[31970]", dim=False)
    return custom(x, 1122, "dialog")

def icon_dialog():
    """1123: pick any icon the skin draws."""
    W, Hh = 800, 520
    names = sorted(os.path.splitext(os.path.basename(p))[0]
                   for p in glob.glob(os.path.join(MEDIA, "icons", "*.png")))
    import iconset
    names = [n for n in names if n not in iconset.NON_TILE]
    k = SLOTKEY
    b = sunken(16, 44, W - 32, Hh - 100)
    pw = W - 32 - 6 - 24
    cols = pw // 68
    pw = cols * 68
    b += ('      <control type="panel" id="400">\n'
          f"        <left>19</left><top>47</top><width>{pw}</width><height>{(Hh - 106) // 68 * 68}</height>\n"
          "        <onright>401</onright><onleft>400</onleft><ondown>400</ondown>\n"
          "        <pagecontrol>401</pagecontrol>\n"
          '        <scrolltime tween="linear">0</scrolltime>\n')
    for kind, foc in (("itemlayout", False), ("focusedlayout", True)):
        b += f'        <{kind} width="68" height="68">\n'
        if foc:
            b += ('          <control type="image"><left>2</left><top>2</top><width>64</width><height>64</height>'
                  '<texture border="4" colordiffuse="select">select_ring.png</texture></control>\n')
        b += ('          <control type="image"><left>10</left><top>10</top><width>48</width><height>48</height>'
              "<texture>$INFO[ListItem.Icon]</texture></control>\n")
        b += f"        </{kind}>\n"
    b += "        <content>\n"
    for n in names:
        b += (f"          <item><label>{n.replace('_', ' ')}</label><icon>icons/{n}.png</icon>"
              f"{oc(f'Skin.SetString({k}.icon,{n})')}{oc(f'Skin.Reset({k}.image)')}"
              f"{oc('Dialog.Close(1123)')}</item>\n")
    b += "        </content>\n      </control>\n"
    b += ctl("scrollbar", 401, 19 + pw + 4, 47, 18, (Hh - 106) // 68 * 68,
             ["<onleft>400</onleft>", "<onright>400</onright>"])
    b += ctl("label", None, 16, Hh - 48, W - 32, 30,
             ["<font>normal</font>", "<textcolor>text</textcolor>", "<align>center</align>",
              "<label>$INFO[Container(400).ListItem.Label]</label>"])
    x = gw.dialog("Custom_1123_DesktopIcon", W, Hh, b, default="400", icon=EDIT_ICON,
                  title="$LOCALIZE[31975]", dim=False)
    return custom(x, 1123, "dialog"), len(names)

MIGRATED = "home.v092"

def migrate_dialog():
    """1126: invisible, runs once. Up to 0.9.1 every library and add-on
    shortcut ended in ",return", so Back skipped the parent menus. Tiles
    store their action, so rewrite the ones that still carry it. Matching is
    on the folder path (no commas, which conditions can't hold); a path that
    is part of a longer one excludes the longer ones."""
    new = {}
    for sid, slid, sicon, cap, entries in SECTIONS:
        for e in map(entry, entries):
            m = re.search(r"ActivateWindow\((\w+),([^,()]+)\)$", e["action"])
            if m:
                new[m.group(2)] = e["action"]
    L = [H.strip(), '<window type="dialog" id="1126">',
         "  <!-- no controls to show: it only updates stored tile actions -->"]
    for n in range(1, SLOTS + 1):
        a = f"Skin.String(tile.{n}.action)"
        for path, act in sorted(new.items()):
            cond = [f"String.Contains({a},return)", f"String.Contains({a},{path})"]
            cond += [f"!String.Contains({a},{q})" for q in new if q != path and path in q]
            L.append("  " + oc(f'Skin.SetString(tile.{n}.action,"{act}")', " + ".join(cond), "onload"))
    L += ["  " + oc(f"Skin.SetBool({MIGRATED})", tag="onload"),
          "  " + oc("Dialog.Close(1126)", tag="onload"),
          "  <controls>",
          '    <control type="image"><left>0</left><top>0</top><width>1</width><height>1</height>'
          "<texture>fill.png</texture><visible>false</visible></control>",
          "  </controls>", "</window>"]
    return "\n".join(L) + "\n"

def addon_apply():
    """1124: invisible; runs once Skin.SetAddon has returned."""
    k = SLOTKEY
    ok = "!String.IsEmpty(Skin.String(pick.addon))"
    acts = [f"Skin.SetString({k}.name,$ESCINFO[System.AddonTitle(Skin.String(pick.addon))])",
            f"Skin.SetString({k}.addon,$ESCINFO[Skin.String(pick.addon)])",
            f'Skin.SetString({k}.action,"RunAddon($INFO[Skin.String(pick.addon)])")',
            f"Skin.Reset({k}.id)", f"Skin.Reset({k}.lid)", f"Skin.Reset({k}.pre)",
            f"Skin.Reset({k}.image)"]
    L = [H.strip(), '<window type="dialog" id="1124">',
         "  <!-- no controls to show: it only applies the add-on picked in 1122 -->"]
    L += ["  " + oc(a, ok, "onload") for a in acts]
    # an ArthurOS-style icon chosen from what kind of add-on it is; the
    # add-on's own picture is one button away in the Tile dialog
    pa = "Skin.String(pick.addon)"
    rules = [("addon_server", " | ".join(f"String.Contains({pa},{w})" for w in ("plex", "jellyfin", "emby"))),
             ("addon_arcade", " | ".join(f"String.Contains({pa},{w})" for w in ("game", "iagl", "retro", "emulat"))),
             ("addon_config", " | ".join(f"String.Contains({pa},{w})" for w in ("libreelec", "settings", "service."))),
             ("addon_radio", f"String.StartsWith({pa},plugin.audio.)"),
             ("addon_stream", f"String.StartsWith({pa},plugin.video.)"),
             ("addons_pictures", f"String.StartsWith({pa},plugin.image.)")]
    earlier = []
    for icon, cond in rules:
        L.append("  " + oc(f"Skin.SetString({k}.icon,{icon})",
                           " + ".join([ok, f"[{cond}]"] + [f"![{e}]" for e in earlier]), "onload"))
        earlier.append(cond)
    L.append("  " + oc(f"Skin.SetString({k}.icon,addons_program)",
                       " + ".join([ok] + [f"![{e}]" for e in earlier]), "onload"))
    L.append("  " + oc("Dialog.Close(1122)", ok, "onload"))
    L += ["  " + oc("Dialog.Close(1124)", tag="onload"),
          "  <controls>",
          '    <control type="image"><left>0</left><top>0</top><width>1</width><height>1</height>'
          "<texture>fill.png</texture><visible>false</visible></control>",
          "  </controls>", "</window>"]
    return "\n".join(L) + "\n"

def reset_dialog():
    """1125: put the shipped desktop back, after asking."""
    W, Hh = 480, 200
    # every Skin.SetString/Reset makes Kodi write guisettings.xml, so only
    # clear fields that hold something and that the defaults won't overwrite
    acts = []
    given = {(n, f) for n, vals in enumerate(default_values(), 1) for f, v in vals.items() if v not in (None, "")}
    for n in range(1, SLOTS + 1):
        for f in FIELDS:
            if (n, f) not in given:
                acts.append(oc(f"Skin.Reset(tile.{n}.{f})", f"!String.IsEmpty(Skin.String(tile.{n}.{f}))"))
    for n, vals in enumerate(default_values(), 1):
        acts += [oc(a) for a in set_fields(f"tile.{n}", vals) if not a.startswith("Skin.Reset")]
    acts += [oc("Skin.Reset(home.layout)"), oc("Skin.SetBool(home.init)"), oc("Dialog.Close(1125)")]
    b = ctl("textbox", None, 20, 44, W - 40, 80, ["<font>normal</font>", "<label>$LOCALIZE[31978]</label>"])
    b += '      <control type="grouplist" id="1126">\n'
    b += f"        <left>20</left><top>{Hh - 50}</top><width>{W - 40}</width><height>34</height>\n"
    b += "        <orientation>horizontal</orientation><align>center</align><itemgap>12</itemgap>\n"
    b += '        <control type="button" id="1127">\n          <width>150</width><height>34</height>\n'
    b += "          <align>center</align><label>$LOCALIZE[107]</label>\n"
    b += "".join(f"          {a}\n" for a in acts)
    b += "        </control>\n"
    b += '        <control type="button" id="1128">\n          <width>150</width><height>34</height>\n'
    b += "          <align>center</align><label>$LOCALIZE[106]</label>\n"
    b += "          <onclick>Dialog.Close(1125)</onclick>\n        </control>\n"
    b += "      </control>\n"
    x = gw.dialog("Custom_1125_DesktopReset", W, Hh, b, default="1128", icon=EDIT_ICON,
                  title="$LOCALIZE[31957]")
    return custom(x, 1125, "dialog")

def edit_box_includes():
    """Tile dialog frame: 8 buttons of 34px (50px with Extra large fonts)."""
    L = []
    for suffix, row in (("", 38), ("_XL", 54)):
        gh = 9 * row
        hh = 44 + gh + 16
        L += [f'<include name="Home_EditH{suffix}"><height>{gh}</height></include>',
              f'<include name="Home_EditBox{suffix}">',
              f"  <height>{hh}</height>",
              '  <include content="Dialog_Box">',
              f'    <param name="width" value="640" /><param name="height" value="{hh}" />',
              '    <param name="innerwidth" value="634" />',
              f'    <param name="icon" value="{EDIT_ICON}" /><param name="colour" value="accent2" />',
              '    <param name="down" value="1130" /><param name="boxes" value="dialog" />',
              '    <param name="title" value="$LOCALIZE[31962] $INFO[Skin.String(edit.slot)]" />',
              "  </include>",
              "</include>"]
    return L

def main():
    if DY:
        # only the desktop itself; tallpass.py copies and stretches the rest
        out = os.path.join(HERE, f"build{SCREEN_H}")
        os.makedirs(out, exist_ok=True)
        open(os.path.join(out, "Home.xml"), "w").write(home_xml())
        open(os.path.join(out, "Includes_Home.xml"), "w").write(includes_xml())
        print(f"home: desktop for 1024x{SCREEN_H} in {os.path.basename(out)}")
        return
    open(os.path.join(XML, "Home.xml"), "w").write(home_xml())
    inc = includes_xml()
    open(os.path.join(XML, "Includes_Home.xml"), "w").write(inc)
    for old in glob.glob(os.path.join(XML, "Custom_11*.xml")):
        os.remove(old)
    files = {"Custom_1120_DesktopEditor": editor_window(),
             "Custom_1121_DesktopTile": tile_dialog(),
             "Custom_1122_DesktopChoose": catalogue_dialog(),
             "Custom_1124_DesktopAddon": addon_apply(),
             "Custom_1126_DesktopUpdate": migrate_dialog(),
             "Custom_1125_DesktopReset": reset_dialog()}
    files["Custom_1123_DesktopIcon"], nicons = icon_dialog()
    for name, xml in files.items():
        open(os.path.join(XML, name + ".xml"), "w").write(xml)
    print(f"home: {len(LAYOUTS)} grid sizes, {SLOTS} tile slots, {len(ALL_LIDS)} names, "
          f"{sum(len(s[4]) for s in SECTIONS)} shortcuts, {nicons} icons to choose from")

if __name__ == "__main__":
    main()
