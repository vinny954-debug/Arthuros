# ArthurOS — Kodi 21 skin (`skin.arthuros`)

Context for Claude Code. Read this first, then `README.md` (user-facing), then
`docs/history/` when you need the *why* behind something.

## What this is

A from-scratch Kodi 21 (Omega) skin styled after Acorn **Arthur 1.2**: 16-colour
pixel desktop, 1px outlines, chunky bevels, no gradients, no animations, bitmap
font (Tamzen) used only at native or exactly-doubled sizes. Owner: Vince.
Current version: **0.9.8** (see `skin.arthuros/changelog.txt`).

Two layouts ship:
- `xml/` — 1024x600, 16:9, default (7" panels).
- `xml768/` — 1024x768, 4:3, **generated** from `xml/` (iPad 3 panel 2048x1536 = exact 2x).

Driven by remote, keyboard, mouse, or touch (Skin settings → Touch mode).

## Vince's setup (as stated by him)

- **Main box now:** Raspberry Pi 4B, Raspberry Pi OS, Kodi runs as a systemd
  service (GBM, no desktop), 9.7" iPad 3 LCD (2048x1536) with touch. Host
  `pi4b.local`. (An earlier note from the 0.9.4 work names the Pi 4 host
  `My8PiTV`, user `vinnyg` — confirm the username with him.)
- Also: ROC-RK3328-CC on LibreELEC 12.2.1 (ROKbox, 192.168.68.63), old Pi 3B+
  LibreELEC (192.168.68.65), a 7" 1024x600 touchscreen.
- He works from a MacBook Pro; installs with `install-arthuros.sh` (below).
- Add-ons he uses: YouTube, Plex, Internet Archive Game Launcher, libretro
  emulators, PVR.
- He is technical (Linux admin, embedded, networking). Keep explanations
  short; give exact commands.

## Requirements

Python 3.10+ with **Pillow** and **lxml** (`pip install pillow lxml`), POSIX sh,
`zip`. Nothing else. All paths are relative to this folder.

`vendor/kodi/strings.po` is Kodi 21's own en_gb strings — `validate.py`,
`textfit.py` and `preview.py` need it to resolve `$LOCALIZE[n]` for Kodi ids.

## Commands

```sh
./build.sh                 # regenerate + check everything (stops at first failure)
./package.sh               # build, then dist/skin.arthuros-<version>.zip
bash install-arthuros.sh user@pi4b.local    # copy newest zip to the Pi, install, restart Kodi
python3 preview.py skin.arthuros/xml/Home.xml out.png          # approximate render
RES=xml768 python3 preview.py skin.arthuros/xml768/Home.xml out.png
XL=1 SET="home.layout=3x3;touchmode=true" python3 preview.py ...   # fontset + state
SET="Container.PluginName=plugin.video.youtube" ...            # any infolabel/bool by exact name
RES=xml768 python3 validate.py                                  # validate the 4:3 folder
python3 preview.py --selftest                                   # preview geometry self-check
python3 tallpass.py --check keyboard                            # one 4:3 special case (audit runs all)
python3 vendor/kodi/mktables.py                                 # regenerate vendor/kodi/*.txt from Omega
```

`preview.py` is *approximate*: it clips grouplists and anchors `<bottom>`/`<right>`
like Kodi, but unknown conditions count as true (set states with `SET=`), it draws
no focus state, and it can't draw the Unicode fontset (arial.ttf is not vendored). Use it to catch
layout mistakes, then confirm on the box. **Screenshots from the real device are
the only proof** — a clean kodi.log proves nothing about appearance.

## Build pipeline (`build.sh`, in order)

| Step | Script | Writes |
|---|---|---|
| textures | `mkmedia.py` (+ `iconset.py` registry) | `media/*.png` — every PNG, from pixel grids |
| fonts | `mkfonts.py` | `xml/Font.xml` (7 fontsets) + `fonts/Unicode.xml`; patches extra glyphs (’ “ ” – … • € ™) into `fonts/Tamzen*.ttf` in place, idempotent |
| language | `mklang.py` | `language/resource.language.en_us` from en_gb |
| windows | `genwindows.py` (uses `inventory.json`) | ~55 generic windows in `xml/` |
| desktop | `home.py`, then `ARTHUR_H=768 home.py` | Home.xml, Includes_Home.xml, Custom_1120–1126; 768 desktop into `build768/` |
| palette | `themepass.py` (+ `XMLDIR=build768`) | edits textures to neutral+`colordiffuse`, title-bar icons — in place, idempotent |
| sizes | `sizepass.py` (+ `XMLDIR=build768`) | taller XL/touch rows in place; `Includes_Size.xml` |
| 4:3 layout | `tallpass.py` | `xml768/` (all of it) |
| validate | `validate.py` (both folders) | static checks |
| contrast | `palettecheck.py` | WCAG check of every palette |
| icons | `iconcheck.py` | every icon unique, registry complete |
| text fit | `textfit.py` | every fixed label fits in every fontset |
| audit | `audit.sh` (+ `labelcheck.py`, `logincheck.py`, `p12check.py`) | regression checks for every past fix |

### The one rule: never hand-edit a generated file

The next build silently overwrites it (this cost three releases of mouse cursor).
Fix the generator instead.

**Generated (edit the script):**
- by `genwindows.py`: DialogAddonInfo, DialogAddonSettings, DialogBusy,
  DialogButtonMenu, DialogColorPicker, DialogContextMenu,
  DialogExtendedProgressBar, DialogFullScreenInfo, DialogGameControllers,
  DialogKeyboard, DialogMediaSource, DialogMusicInfo, DialogNotification,
  DialogNumeric, DialogPVR* (all), DialogPictureInfo, DialogPlayerProcessInfo,
  DialogSeekBar, DialogSettings, DialogSlider, DialogSubtitles, DialogTextViewer,
  DialogVideoInfo, DialogVideoManager, DialogVolumeBar, EventLog, FileBrowser,
  FileManager, GameOSD, Includes_Games, LoginScreen, MusicOSD,
  MusicVisualisation, MyMusicPlaylistEditor, MyPVRGuide, MyWeather,
  PlayerControls, Pointer, SettingsCategory, SettingsProfile,
  SettingsScreenCalibration, SettingsSystemInfo, SlideShow, SmartPlaylistEditor,
  SmartPlaylistRule, Startup, Timers (root `<timers>`), VideoFullScreen, VideoOSD,
  VideoOSDBookmarks
- by `home.py`: Home, Includes_Home (also `Settings_HubLayouts`, `SkinFontVar`),
  Custom_1120…1126; `ARTHUR_H=768` writes the 768 desktop, hub layouts and
  icon picker into `build768/`
- by `mkfonts.py`: Font.xml, `fonts/Unicode.xml` · by `sizepass.py`: Includes_Size.xml
- everything in `media/`, `language/resource.language.en_us/`, `xml768/`, `build768/`

**Hand-maintained XML (edit directly; themepass/sizepass still touch them idempotently):**
AddonBrowser, Defaults, DialogConfirm, DialogSelect, Includes, Includes_Chrome,
Includes_Dialogs, Includes_Lists, Includes_Media, MyFavourites, MyGames,
MyMusicNav, MyPVRChannels, MyPVRRecordings, MyPVRSearch, MyPVRTimers, MyPics,
MyPlaylist, MyPrograms, MyVideoNav, Settings, SkinSettings, Variables,
View_50_List, View_51_Poster, View_52_IconWall. (`genwindows.HAND` lists the
windows it must leave alone.) Also hand-maintained: `colors/*.xml` palettes,
`language/resource.language.en_gb/strings.po`, `scripts/*.py`, `addon.xml`,
`changelog.txt`.

When you add a fix, **add an `audit.sh` check** for it so it can't silently
regress.

## Conventions

- **Geometry (1024x600):** menu bar 0–26, window frame top 30 / height 534,
  task bar top 568 / height 32. Dialogs centre with `<centertop>50%</centertop>`.
  In 768 the frame is 702 high and the task bar at 736 — produced by tallpass,
  never by hand.
- **Taller rows** (Extra large fonts *or* Touch mode): condition
  `XLC = [String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]`
  (+16 px). Desktop tiles use the font-only `FONTXL`. List containers get a
  conditional layout pair placed first; fixed heights in vertical grouplists and
  settings templates become `Height_N` / `Height_N_XL` conditional includes.
- **Fonts:** Tamzen at 12/14/16/20 (and exactly 2x for XL). Chrome text uses
  `chrome`, `chromebold`, `chromesmall` (capped at 20 px). Tile fonts:
  `tilebig`, `tilesmall`, `tiletiny`.
- **Colours:** always palette names (`text`, `textdim`, `textinv`, `select`,
  `accent1`, `accent2`, `facetint`, `marked`, `desktop`, `titletext`...), never
  hex in windows. Chrome textures are neutral + `colordiffuse`.
- **Icons:** only from `iconset.py` (base drawing + optional 9x9 emblem). Sizes
  in `media/icons24`, `icons` (48), `icons64`, `icons80`, `icons96`.
  `iconcheck.py` rejects duplicates and repeats within a menu. **No brand
  logos** — add-ons get original ArthurOS pictures (addon_stream, addon_server…).
- **Strings:** skin strings live in en_gb `strings.po`. Blocks: 31900–31999
  (free: 31900, 31905, 31908, 31909, 31911, 31913–31916, 31974, 31999), 31800–31899
  (marked per area with `# ===== Pn strings` comments; many free), and 31700–31769
  (unused, reserved). `audit.sh` fails on an unused skin string. Prefer an existing
  Kodi string id when one says the same thing.
- **Labels:** a bare number in `<label>`/`<label2>`/`<altlabel>`/`<hinttext>` is a
  string id (digits 0–9 are `$LOCALIZE[12310..12319]` or `$NUMBER[n]`);
  `validate.py` rejects it.
- **Transport glyphs** exist only white: `icons16|icons24/w_<name>.png` (play,
  pause, stop, prev, next, rew, ffwd, shuffle, repeat, volume, mute; icons24 are
  32x32). Use them through `genwindows` `glyph_tex`/`icon_radio`/`tinted_glyph`,
  which tint `text` / `textinv` (focused) / `textdisabled`. audit fails on an
  untinted `w_*`. Palette colour `epgnow` is the guide's now line (palettecheck).
- **Touch hit areas:** `<hitrect>` is in the parent's coordinates (a grouplist
  child's slot); pad at most half the item gap. sizepass generates `Size_Hit`,
  `Size_Height`, `Size_Top`, `Size_Left`, `Size_Width` pairs; Touch mode widens
  list scrollbars to 30 px (the list shrinks 12).
- **Chrome ids:** 9100 Start, 9101 Now playing, 9102 mini player, 9103 Settings,
  9104 parked window, 9105 touch Back, 9106 Power, 9107 floating touch Back
  (task bar hidden), 9108 dialog touch Back (`Dialog_TouchBack`), 9109 menu-bar
  volume (opens PlayerControls). `Dialog_Dim` = dim + touch Back;
  `Dialog_DimClose` = a tap on the dim runs Back (only where nothing is lost).
- **genwindows.dialog()** takes `anchor="bottom"` (OSDs, seek bar, bookmarks,
  info), `visible=` window conditions (modeless dialogs such as DialogSeekBar
  open only through these), `pre=` (tap catchers), `default_always`, and falls
  back to `TITLES[name]` when Kodi writes no heading (`KODI_HEADED` excepted).
  `osd_row_worst()` asserts every OSD text row fits 1008 px in every state.
- **Sliders** need `<orientation>horizontal</orientation>` (Kodi's default is
  vertical; Defaults.xml sets it). Kodi-driven sliders/progress have no `<info>`.
- **validate.py** fails on any warning not in `KNOWN_WARNINGS` (now empty) and
  checks builtins, actions, window names, info labels, `$VAR`/`$EXP`, SetFocus /
  Container ids and the Kodi-required ids in `KODI_IDS` (tables in
  `vendor/kodi/*.txt`). Ids inside container layouts and non-focusable controls
  may repeat.
- **Grouplists:** every child needs an `id` (id 0 breaks navigation) — put
  captions/labels outside the grouplist.
- **Static item properties:** never name them `icon`, `thumb`, `label`, `label2`
  (Kodi treats those as art/labels and they never update — use `ico`); never a
  bare number (it gets localized — use `$NUMBER[n]`). `validate.py` enforces both.
- **Desktop tiles** are skin strings `tile.N.{id,lid,pre,name,icon,image,action,addon}`,
  N=1..36, `home.layout` ∈ 3x3, 4x3 (default), 4x4, 5x4, 5x5, 6x5, 6x6.
- **Version stamps** (bump all on release): `addon.xml`, `xml/SkinSettings.xml`
  (`v0.9.8  -  1024x600`), `xml/Includes_Chrome.xml` (`ArthurOS 1.2 (v0.9.8)`),
  `changelog.txt` (newest first), `README.md` (current version + zip names).
  `audit.sh` checks the stamps match.

## Kodi facts that bit us (verified in Kodi source — trust these)

- Skin res folder: `closestRes` picks by aspect ratio first; `GetSkinPath`
  falls back *per file* to the default folder, so `xml768` must be complete.
- `Startup.xml` must `ReplaceWindow($INFO[System.StartupWindow])` on load, or
  Kodi never finishes UI init (skin/font reloads refused, mouse swallowed).
- `Defaults.xml`: images must stay `aspectratio stretch`; no container defaults
  (`SetDefaults` appends them unconditionally).
- Pointer.xml needs image ids 1–4. Window names must come from
  `windownames.txt` (`favouritesbrowser`, not `Favourites`).
- Labels inside list layouts never wrap (`CGUIListLabel`) — use `textbox`.
- Static list properties refresh every 1 s only; Home is forced to reload via an
  include condition on `Skin.HasSetting(home.flip)`.
- `CGUIAction` evaluates all conditions before running any action; `$INFO`,
  `$VAR`, `$ESCINFO` resolve at execution.
- Context menu: background control 999 must be top-level at 0,0
  (`PositionAtCurrentFocus`).
- `textoffsetx` pads both sides; `radioposx` is from the left edge; spin arrows
  at `right - 2*spinwidth - spinposx`.
- Touch taps send `ACTION_MOUSE_MOVE` → pointer shows; nothing tells mouse from
  touch (hence `scripts/mousewatch.py`).
- Game picture dialogs (filter/stretch/rotation/in-game saves) load
  DialogSelect.xml but use ids 10810/10811/10812 (`DialogGameDefines.h`).
- OSD settings dialogs (OSDVideoSettings, OSDAudioSettings, OSDSubtitleSettings)
  load DialogSettings.xml; Video settings' **Video stream** is where streaming
  add-ons expose resolutions.
- A plugin's resolved stream path doesn't name the plugin; browsers record
  `Container.PluginName` into `Window(Home).Property(arthuros.plugin)` on unload.
- `Skin.SetString/SetBool/Reset` save guisettings each time; skin settings save
  500 ms after a change; `UnloadSkin` writes in-memory settings over the file.
- Kodi reuses `addons/packages/*.zip` when the version matches (how 32-bit
  binaries came back after a box migration).
- Fullscreen video: a tap (LeftClick) opens VideoOSD; the OSD is **modal**, so a
  tap on the picture goes to the OSD - a transparent full-screen button behind
  the bar closes it. `Action(FullScreen)` = ACTION_SHOW_GUI leaves playback to
  the menus; `Action(X,<window>)` goes straight to that window's OnAction.
- Built-in slider actions (GUISliderControl.cpp): `seek`, `pvr.seek`, `volume`
  (fireOnDrag). Volume keys step 1/volumesteps (~1 %), so +/- buttons are no
  substitute for a slider.
- Modeless dialogs (DialogSeekBar, DialogExtendedProgressBar, DialogVolumeBar)
  never get input. SlideShow draws skin controls ON TOP of the picture and
  eats the arrow keys. DialogBusy renders only when topmost.
- `Player.FilenameAndPath` keeps `plugin://<id>/` during plugin playback
  (only DynPath is resolved) - `scripts/addonsettings.py` reads it.
- epggrid: programme cells are `itemlayout`/`focusedlayout`; only controls with
  ids 1-14 stretch to a programme's width. `PVR.EpgGridControl(...)` acts on the
  active guide. Kodi opens DialogPVRGuideControls for Navigate... only because
  the file exists.
- The keyboard heading goes to label 311, the slider heading to label 10;
  settings level button 20 needs `<onclick>SettingsLevelChange</onclick>`.
- PVR ids 6 (channels) and 7 (recordings) must be radiobuttons (static_cast).
  Kodi writes "N Objects" into any id 12. id 0 never enters the control lookup.
- Grouplists copy their onup/ondown (with conditions) to each child; Kodi has no
  spatial navigation, so stacked horizontal rows need explicit row navigation
  (`row_nav()`).
- `<usealttexture>` is the togglebutton's *selected* condition (never `true`).
- Font lookup: skin `fonts/` -> special://home/media/Fonts -> special://xbmc/
  media/Fonts, so `arial.ttf` needs no shipping. Omega ignores
  `<fontset unicode=...>`: the user picks Unicode by hand. No per-glyph fallback.
- A folder-copied add-on is inserted disabled (CAddonDatabase::SyncInstalled);
  install-arthuros.sh enables it in Addons33.db while Kodi is stopped.
- Under `set -e`, a failure in `a && b` is ignored unless it is the last command
  (build.sh has one command per line); audit.sh's `chk` runs each check in a
  subshell.

Reference sources in `vendor/kodi/src/` (Skin.cpp, game dialogs) and Estuary
excerpts in `vendor/kodi/estuary-ref/`. For anything else, read the Kodi
**Omega** branch on GitHub (`xbmc/xbmc`, branch `Omega`) rather than guessing.
`inventory.py` (regenerates `inventory.json`) needs a full Estuary checkout:
`ESTUARY=/path/to/xbmc/addons/skin.estuary/xml python3 inventory.py`.

## Scripts that run inside Kodi (`skin.arthuros/scripts/`)

- `backup.py` — skin settings backup/restore/reset (JSON-RPC + Skin.* builtins);
  reset keeps touchmode and the pointer choice.
- `mousewatch.py` — Touch mode mouse detection via `/proc/bus/input/devices`;
  honours `Skin.HasSetting(touch.pointer.show|hide)` (neither = Auto). Started
  from Startup (when the start window isn't Home), Home and Skin settings.
- `addonsettings.py` — opens the settings of the add-on that is playing.
- `netbt.py` — Wi-Fi/Bluetooth/audio output for Raspberry Pi OS (nmcli,
  bluetoothctl). Vince's own script, shipped verbatim — ask before changing it.

All via `RunScript(special://skin/scripts/<name>.py[,args])`.

## State at handover (0.9.8)

0.9.7 is on the box; Vince: "looks pretty good", but the volume slider showed no
level (bar and nib were the same facetint bevel). 0.9.8 fixes that: every OSD /
mini-player slider is a progress fill (same info) under a slider with a blank
bar texture (`media/blank.png`, 24 px so the nib stays ht x ht), and volume is
`genwindows.volume_cluster()`: mute 9982, - 9993, slider 9983, + 9994 (5 % bands
via `vol_steps()`; SetVolume is absolute only), `$INFO[Control.GetLabel(9983)]`
= "NN%". 0.9.8 is untested on the box. Earlier, 0.9.6/0.9.7 were checked in
source and preview only. 0.9.7 implemented the whole 0.9.6 audit
(`docs/audit-0.9.6.md`, 92 findings; final verification: 87 fixed, 6 partly by
design) - checked in Kodi source and preview only. Test first on hardware:
- Video OSD: tap opens the bottom bar; tap the picture / Hide closes it; volume
  slider + mute; seek slider; Menus returns to the browser while playing;
  Rewind/Forward; the seek strip on pause/skip; Bookmarks, Info.
- Touch mode: dialog Back buttons, title-bar boxes, task-bar Power, context menu
  tap-outside, keyboard keys on the 7" panel, scrollbars, Pointer in Touch mode.
- TV guide grid, Navigate..., channel OSD, live-TV preview/switch.
- Slideshow strip; game OSD; music visualisation buttons.
- install-arthuros.sh on Raspberry Pi OS and LibreELEC (enable-in-DB, polkit rule).
- netbt.py polkit message on real hardware; the Unicode fontset.
- Still untested from 0.9.6: the Add-on settings button paths, game picture dialogs,
  the 4:3 layout on the real 2048x1536 panel, editor dialogs 1124/1126 onload.

Known gaps / candidates:
- Info dialogs keep 30 px faces (34 px hit rects); three 46 px rows don't fit at 600.
- Scrollbars beside panels/grouplists/epggrid keep an 18 px look (30 px hit area).
- Weather tiles at 768 keep the 600 icon/day design.
- Calibration art is rescaled by Kodi from 1920x1080 (never pixel-exact).
- On 5x5/6x6 desktops very long tile names lose their last line.
- PVR channel/recording windows could still use a design pass beyond the guide.

## Working with Vince

- He reports what he sees on the box (often screenshots/logs). Diagnose from
  Kodi source, fix in the generator, add an audit check, rebuild, package.
- Ship each change as a new version: bump stamps, changelog entry written for
  him (what he'll notice, not internals), `./package.sh`, then he installs with
  `install-arthuros.sh`.
- Say plainly what was verified only in preview vs. on hardware.
