# ArthurOS — a Kodi 21 skin

An Acorn *Arthur 1.2* desktop for Kodi 21 (Omega), built natively for a
1024×600 panel, with a 1024×768 layout for 4:3 screens (an iPad 3 panel at
2×), and driven by remote, keyboard, mouse or touch.

Hard 1px outlines, chunky bevels, no gradients, no animations — everything
snaps. Text is Tamzen, a bitmap font used only at its native pixel sizes.

**Current version: 0.9.9** — the menu bar shows the running version, so one
glance tells you which build is installed.

---

## Install

### The quick way, from your computer

`install-arthuros.sh` copies the newest zip to the box over SSH, installs it
for the user Kodi runs as, and restarts Kodi. It works on LibreELEC (root, no
sudo) and Raspberry Pi OS, keeps the old version until the new one is in
place, and starts Kodi again if anything fails.

```sh
bash install-arthuros.sh root@<pi-address>     # LibreELEC
bash install-arthuros.sh pi@pi4b.local         # Raspberry Pi OS
```

On a first install it also switches the skin on in Kodi's add-on database,
provided Kodi has run on that box before. On Raspberry Pi OS it offers to
add the polkit rule that Wi-Fi changes need (below).

### On the Pi (LibreELEC), by hand

For **updates**, dropping the folder in is more reliable than Kodi's zip
installer and does not need "Unknown sources" turned on.

```sh
unzip skin.arthuros-0.9.9.zip
scp -r skin.arthuros root@<pi-address>:/storage/.kodi/addons/
ssh root@<pi-address> systemctl restart kodi
```

Then **Settings → Interface → Skin → Skin → ArthurOS**.

**First install:** Kodi adds a folder it finds on disk as a *disabled*
add-on, so ArthurOS is not in the skin list yet. Enable it once in
**Add-ons → My add-ons → Look and feel → Skin → ArthurOS → Enable**, then
pick it as above. (Kodi's zip installer enables it by itself;
`install-arthuros.sh` does it for you when Kodi has run before.)

### On Raspberry Pi OS (Kodi from apt), by hand

```sh
unzip skin.arthuros-0.9.9.zip
rm -rf ~/.kodi/addons/skin.arthuros && mv skin.arthuros ~/.kodi/addons/
```

Use the `.kodi` of the user Kodi runs as (`install-arthuros.sh` prints it as
"Kodi runs as '...'"). Restart Kodi, then pick ArthurOS as above. On a first
install, enable it under **Add-ons → My add-ons → Look and feel → Skin →
ArthurOS → Enable** first, as for LibreELEC.

With no LibreELEC settings add-on, **Settings → Network & Bluetooth**
handles Wi-Fi, Bluetooth pairing and the sound output. Kodi run as a
service has no login session, so NetworkManager refuses its Wi-Fi changes
unless a polkit rule allows the user Kodi runs as. `install-arthuros.sh`
offers to write it. By hand, as root, create
`/etc/polkit-1/rules.d/50-arthuros-nm.rules` (replace `KODIUSER`):

```js
polkit.addRule(function(action, subject) {
  if (action.id.indexOf("org.freedesktop.NetworkManager.") == 0 && subject.user == "KODIUSER")
    return polkit.Result.YES;
});
```

polkit reads it at once; no reboot or restart is needed.

### On a 4:3 screen (iPad 3 panel, 2048×1536)

Nothing to choose: Kodi picks the skin's 4:3 layout (1024×768) whenever the
screen is closer to 4:3 than 16:9, and on 2048×1536 every skin pixel is
exactly 2×2 screen pixels.

1. **Settings → System → Display → Resolution**: 2048×1536.
2. **Settings → Interface → Skin → Zoom**: 0 %. Any other zoom value spoils
   the 2× scaling and blurs the bitmap font.
3. If **System → Display** shows **Limit GUI size** (Expert level), set it
   to no limit. Otherwise Kodi draws the GUI at 1080 lines and scales it up.
4. For a touchscreen, turn on **Skin settings → Touch mode**.

Kodi run as a service draws straight to the screen, so the Raspberry Pi OS
desktop's own scaling has no effect on it.

### On a desktop, for quicker testing

**Settings → Add-ons → Install from zip file**, with **Settings → System →
Add-ons → Unknown sources** switched on first. Size the window to exactly
1024×600 (or 1024×768 for the 4:3 layout) — the skin scales to anything, but the bitmap font is only crisp at
1:1.

---

## Using it

| | |
|---|---|
| **Desktop** | Twelve tiles to start with, and yours to rearrange (below). Arrow keys move between them. On a menu tile (Movies, Music...), **Enter** or a click moves you into the panel on the right; scroll and press Enter again to open something. Left, or Back, returns to the tiles. Every other tile (Weather, Favorites, an add-on, a single shortcut) opens straight away. |
| **Browsers** | Up from the top of a list reaches the toolbar — Up, View, Sort, Order, Filter, Options. Down past the last row drops onto the task bar. |
| **Task bar** | Start returns to the desktop. While something plays, the now-playing button brings it back fullscreen, and Playlists opens the player controls. A window you minimised gets its own button, which takes you back to the folder it was showing. Up always returns to the window above. |
| **While playing** | Tap the screen or press OK for the controls. The bottom row, **Settings:**, opens Kodi's Video settings (picture, and **Video stream**: the resolutions a streaming add-on such as YouTube offers), Audio (audio track, boost, delay), Subtitles and Bookmarks. **Add-on** opens the settings of the add-on that's playing, e.g. YouTube's default quality. Games get Save / Load, Reset, Filter, Stretch, Rotation, Volume and Advanced (the emulator's own options). |
| **Inside an add-on** | The toolbar gains **Add-on settings** — sign-in, quality, subtitles and whatever else that add-on offers. **Options** still has the add-on's own context menu. |
| **Settings** | The **Settings level** button, bottom left under the categories, steps through Basic, Standard, Advanced and Expert. Each level shows more of Kodi's settings. |
| **Title bars** | The boxes are for the mouse. On a window, **_** parks it on the task bar and shows the desktop, and **×** closes it. On a dialog, **_** closes every dialog, and **×** closes that one. **▫** goes fullscreen to whatever is playing, and is greyed out when nothing is. The desktop's own panel can't be minimised or closed, so its **_** and **×** are greyed out. The keyboard never lands on the boxes, so they can't trap you. |

---

## Customise desktop

**Settings → Customise desktop…** (also in Skin settings).

- **Grid size** — 3×3, 4×3, 4×4, 5×4, 5×5, 6×5 or 6×6. The panel on the right
  gets wider or narrower to fill what the grid leaves. Big grids get smaller
  icons and captions; 3-row grids get 80-pixel icons. Long names wrap onto
  two or three lines.
- **Tiles, in order** — every tile the grid can hold. Pick one to change it:
  - **Choose what it opens…**
    - a whole menu: Movies, TV shows, Music, Videos, Pictures, Live TV,
      Add-ons, My add-ons, Programs, File manager, Settings
    - something that opens directly: Weather, Favorites, Power menu,
      Customise desktop
    - **Everything**: a menu with every top-level menu Estuary and Confluence
      have (libraries, files, playlists, Live TV, games, the add-on browser,
      all of Settings, events, profiles, power)
    - one shortcut from any menu, such as Install from zip file, Install from
      repository, Movie genres or System settings
    - **An add-on…**: any video, music or program add-on, such as YouTube or
      Plex. The tile takes the add-on's name and an ArthurOS-style icon for
      its kind: online video, media server (Plex, Jellyfin, Emby), game
      launcher, radio, or system tool.
  - **Choose an icon…** — any of the skin's 187 icons.
  - **Add-on's own picture** — use the add-on's own artwork instead.
  - **Use a picture file…** — any image instead.
  - **Rename…**
  - **Move earlier / Move later** — tiles fill the grid left to right, then
    top to bottom.
  - **Clear this tile**
- **Reset desktop** puts the original twelve tiles back in a 4×3 grid,
  after asking.

Tiles keep their names in step with Kodi's language, so a Favourites tile
becomes Favorites when you switch to English (US). Names you type yourself
stay as you typed them.

### Backing up

**Skin settings → Back up skin settings…** saves one small file with the
desktop, grid size, pointer, bar and clock choices, and the skin's colors,
fonts and zoom. It offers the skin's own backups folder first; pick a USB
stick or network share to keep a copy off the Pi.

**Restore skin settings…** asks before it replaces anything, changes only
the settings that differ, and reloads the desktop. LibreELEC's own backup
(LibreELEC settings → System → Backup) also includes skin settings, along
with everything else.

---

## Making it yours

| Setting | Where | Choices |
|---|---|---|
| **Colors** | Settings → Interface → Skin → Colors | Skin default (Arthur red and blue), Acorn, Paper, Amber, Phosphor, Midnight, **Colorblind-Safe**, **Colorblind-Safe-Dark**, **High-Contrast-Light**, **High-Contrast-Dark** |
| **Fonts** | Settings → Interface → Skin → Fonts | Default, Large, **Large bold**, **Extra large**, **Extra large bold**, Compact, Bold |
| **Pointer** | Skin settings | Arthur (cyan and red), Classic, Inverse |
| **Touch mode** | Skin settings | Taller rows for fingers, a Back button on the task bar, and no pointer unless a mouse is plugged in |
| **Menu bar, task bar, clock** | Skin settings | show or hide each |
| **US or UK spelling** | Settings → Interface → Regional → Language | English (US) gives Colors, Favorites, Program; English (UK) gives Colours, Favourites, Programme |

Skin settings also has a **Colors, fonts and theme…** button that jumps to
the right page of Kodi's settings.

### For eyesight and color vision

- **Extra large** fonts draw text at twice the bitmap size, so it stays
  pixel-sharp rather than blurring. While one is active, lists, settings and
  menus switch to taller rows. You see fewer rows per screen, but nothing
  overlaps. The menu bar, task bar and title bars stop at the Large size so
  they keep their shape.
- **Colorblind-Safe** uses the Okabe–Ito blue and vermillion pair, which
  stays distinct for red–green and blue–yellow color blindness. Nothing
  anywhere in the skin tells things apart by red against green. The My
  add-ons icon now carries a heart, so it no longer relies on being orange
  rather than green.
- **High-Contrast** palettes meet 7:1 contrast (WCAG AAA) on every pairing:
  text, selections, title bars and the menu and task bars. Every other palette
  meets 4.5:1 (AA). `palettecheck.py` measures this on every build.

### Spelling

The skin follows Kodi's own interface language. Most of the words on screen
are Kodi's, such as Favourites, Colours and Programme, and Kodi switches them
all when you pick **English (US)**. The first time you do that, Kodi downloads
the language. ArthurOS ships US English versions of its own words to match.

Changing Colors or Fonts makes Kodi reload the skin, which takes a moment.

Kodi's **Theme** setting stays at "Skin default". A Kodi theme is a compiled
texture bundle, and ArthurOS gets its variety from palettes instead — they
recolour the whole skin, including title bars, selections, focus rings, the
desktop, and every bevel.

---

## Changing things

The skin is plain Kodi XML you can open and edit. For anything bigger, use the
build: it regenerates, recolours, and checks everything in the correct order.

```sh
./build.sh          # regenerate and check everything
./package.sh        # build, then zip to dist/skin.arthuros-<version>.zip
```

Needs Python 3 with Pillow and lxml (`pip install pillow lxml`).

Which runs, in order:

| Step | Script | Does |
|---|---|---|
| textures | `mkmedia.py` | draws every PNG from pixel grids |
| windows | `genwindows.py` | writes the ~55 generated windows |
| fonts | `mkfonts.py` | writes Font.xml: seven fontsets, all at native or doubled sizes |
| language | `mklang.py` | writes the US English strings from the UK English ones |
| desktop | `home.py` | writes the desktop, its seven grid sizes, and the Customise desktop windows; with `ARTHUR_H=768`, the 4:3 desktop into `build768/` |
| palette | `themepass.py` | makes every chrome texture follow the palette (`XMLDIR=build768` for the 4:3 desktop) |
| sizes | `sizepass.py` | adds the taller Extra large rows (`XMLDIR=build768` likewise) |
| 4:3 layout | `tallpass.py` | writes `xml768/`: every window stretched from 600 to 768 high, the desktop from `build768/` |
| validate | `validate.py` | static checks — see below (`RES=xml768` checks the 4:3 folder) |
| contrast | `palettecheck.py` | measures every palette's text contrast |
| icons | `iconcheck.py` | proves every icon is unique — see below |
| text fit | `textfit.py` | measures every fixed label, in every fontset |
| audit | `audit.sh` | confirms each past fix is still present |

**The 4:3 folder is generated, never edited.** `tallpass.py` copies every
window from `xml/`, inlines its includes, and gives the extra 168 px to
whatever fills the window: the tallest list, panel or text box in each window
grows, and anything below it moves down with the task bar. Dialogs centred on
the screen are unchanged. Fix layouts in `xml/` (or the generators) and
rebuild. `preview.py` takes `RES=xml768` to draw the 4:3 version.

The build stops at the first failure. **Don't hand-edit a file the generator
writes** — the next build replaces it. That mistake cost two releases' worth
of mouse cursor. `genwindows.py` has a `HAND` set listing the hand-built
windows it leaves alone.

**What `validate.py` catches without launching Kodi:** missing textures,
unknown fonts and colour names (including colour *attributes*), invalid control
types, duplicate ids in a window, `<views>` naming missing controls — or view
containers it forgot to name, which never get hidden and cover the live list —
`defaultcontrol` pointing at nothing, dead navigation, window names Kodi does
not recognise, containers with no layouts, a pointer without cursor ids 1–4,
fontset or `$LOCALIZE` strings that don't exist, and palette files naming
colours that don't exist.

**How icons stay unique.** Every icon comes from one registry,
`iconset.py`. Each entry is either its own drawing or a drawing plus a corner
badge. For example, Movies, Recently added movies and Movie genres are the same
film strip with no badge, a star, and a tag. `iconcheck.py` fails the build
if:

- two different icon names draw the same pixels;
- two of Kodi's fallback icons (`Default*.png`) share a picture without being
  listed in `iconset.ALIASES` as meaning the same thing;
- any file in `media/` duplicates another or isn't in the registry;
- any tile panel or submenu uses the same icon twice.

To add an icon, add it to `SPEC` (base plus badge) or `BASES` (new art) in
`iconset.py` and build. If it collides with an existing one, the build says
which.

**What `textfit.py` catches:** any fixed label that Kodi would cut short to
"S…". It measures with the real font at the real size against the space the
control really leaves for text, in all four fontsets.

`preview.py` renders a window to PNG for checking geometry. Set `PALETTE=Amber`
(or any palette name) to render in that palette, `XL=1` for the Extra large
fonts, and `SET="home.layout=5x4;edit.slot=3"` to pretend skin settings are
set. It works out skin strings, list items, variables and simple
`<visible>` conditions. Anything it can't know, like what's playing, counts
as true. It's an approximation, not Kodi.

### Before you edit

- **Font sizes are 12, 14, 16 or 20, or exactly double one of those.** Edit `mkfonts.py`,
  not Font.xml. Any other size resamples the bitmap font.
- **Palette colours live in `colors/`.** `defaults.xml` holds every name;
  a palette file overrides only the ones it changes. The themeable names are
  `accent1`, `accent2`, `select`, `desktop`, `facetint` (multiplies every
  bevel), plus the text colours.
- **Bevels are 24×24 nine-slice PNGs used with `border="2"`.** Smaller ones
  bleed under Kodi's texture filtering and flat panels come out as gradients.
- **`Defaults.xml` must not contain `<itemlayout>` or `<focusedlayout>`.** Kodi
  appends default blocks unconditionally, so they stack on top of each list's
  own layouts.

---

## Honest state

**Designed properly:** the desktop, the title-bar boxes and task bar, the media browsers, Settings, Skin
settings, System information, file manager, file browser, source editor,
weather, keyboard, number pad, power menu, confirm, select, context menu,
notifications, busy, volume, seek, the OSDs and player controls, add-on and
media info.

Also designed properly as of 0.8.0: game controller setup, subtitle search,
and the video, music and TV info screens with all of Kodi's buttons.

**Generic but functional:** about 20 less-travelled windows, most of them
PVR management and smart-playlist editors. Up to 0.7, the tool that lists
which controls each window needs ignored any control whose id is passed in
through an include. That left buttons missing (OK and Cancel in the playlist
editors, the version manager's buttons), and it is why game controllers came
up empty. That is fixed, and those windows now carry every button Kodi
expects, but their layout is still mechanical.

**New in 0.9.2, not yet tried on the box:** the Everything menu and Back
climbing through Kodi's own menus; from 0.9.1, backup and restore, the add-on
icons, and wrapped tile names. The build checks their structure, but the
first real test is yours.

**Next:** the PVR guide grid and channel windows, since live TV gets used
regularly. The guide needs Kodi's `epggrid` control, which has its own
geometry rules.

---

## When something looks wrong

- **Log:** turn on **Settings → System → Logging → debug logging**, reproduce,
  then read `/storage/.kodi/temp/kodi.log` (Raspberry Pi OS: `~/.kodi/temp/kodi.log`
  of the user Kodi runs as). Skin faults name the file. But a
  clean log doesn't mean the skin *looks* right — a valid-but-wrong value never
  gets logged. Screenshots catch those.
- **ArthurOS isn't in the skin list** after a first install by folder copy:
  Kodi added it disabled. **Add-ons → My add-ons → Look and feel → Skin →
  ArthurOS → Enable** (see Install).
- **Titles with letters missing** (Polish, Greek, Cyrillic, Japanese, or
  signs such as € and ½ in YouTube, Plex or guide titles): the bitmap font
  has no such letters, and Kodi never falls back to another font by itself.
  Pick **Settings → Interface → Skin → Fonts → Unicode (all alphabets)**,
  which uses Kodi's own Arial for everything.
- **"NetworkManager refused the change: user '…' (Kodi) isn't allowed to
  manage networks"** from Network & Bluetooth on Raspberry Pi OS: the polkit
  rule for the user Kodi runs as is missing (see Install). Rerun
  `install-arthuros.sh` and answer yes, or write the rule by hand. (An empty
  or short network list right after a scan is not this: NetworkManager
  refuses back-to-back rescans, so the list shown is the last scan's.)
- **Screenshots come out black** while video is playing: Kodi on the Pi only
  captures the menu layer. Stop playback first, or photograph the screen.
- **File manager has no Home folder.** Kodi's file manager only lists your
  file sources, plus the profile folder and any removable drives. To add
  `/storage`, put these two entries inside the `<files>` section of
  `/storage/.kodi/userdata/sources.xml`, then restart Kodi:
  ```xml
  <source><name>Home folder</name><path pathversion="1">/storage/</path><allowsharing>true</allowsharing></source>
  <source><name>Root filesystem</name><path pathversion="1">/</path><allowsharing>true</allowsharing></source>
  ```
  You can also add them from inside Kodi. Turn on **Settings → Media → General
  → Show "Add source" buttons**, then use **Add source → Browse → Home folder**
  in the file manager.
- **Kodi crashes that aren't the skin.** The logs from 0.6.0 show two
  crashes inside Kodi itself. Both are worth knowing about.
  - **Add-on browser and YouTube.** The YouTube add-on's background service
    reads screen information from its own thread. If that happens while the
    Add-on browser is rebuilding its list, Kodi 21 can hang and then crash.
    Updating the YouTube add-on may help. No skin can prevent this.
  - **Install from zip.** If the file you pick isn't a readable add-on zip
    with a single top folder, Kodi 21 crashes instead of showing an error.
    The same crash happened under Confluence on 18 September.
- **Everything looks slightly small and soft:** check **Settings → System →
  Display → Video calibration**. Any overscan makes Kodi draw the whole
  interface at a fractional scale.

---

## Credits

Tamzen font by Suraj N. Kurapati, derived from Tamsyn by Scott Fial, both under
permissive licences (`fonts/LICENSE-Tamzen.txt`). Every texture and icon is
drawn by `tools/mkmedia.py`. Control ids were read from the Kodi 21 source;
no layout or artwork was copied from another skin.
