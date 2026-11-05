# ArthurOS — Kodi 21 skin (`skin.arthuros`)

Context for Claude Code. Read this first, then `README.md` (user-facing), then
`docs/history/` when you need the *why* behind something.

## What this is

A from-scratch Kodi 21 (Omega) skin styled after Acorn **Arthur 1.2**: 16-colour
pixel desktop, 1px outlines, chunky bevels, no gradients, no animations, bitmap
font (Tamzen) used only at native or exactly-doubled sizes. Owner: Vince.
Current version: **0.9.6** (see `skin.arthuros/changelog.txt`).

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
```

`preview.py` is *approximate* (no clipping of grouplists, shows both XL and normal
layouts in some dialogs, unknown conditions count as true). Use it to catch
layout mistakes, then confirm on the box. **Screenshots from the real device are
the only proof** — a clean kodi.log proves nothing about appearance.

## Build pipeline (`build.sh`, in order)

| Step | Script | Writes |
|---|---|---|
| textures | `mkmedia.py` (+ `iconset.py` registry) | `media/*.png` — every PNG, from pixel grids |
| fonts | `mkfonts.py` | `xml/Font.xml` (7 fontsets) |
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
| audit | `audit.sh` | regression checks for every past fix |

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
  SmartPlaylistRule, Startup, VideoFullScreen, VideoOSD, VideoOSDBookmarks
- by `home.py`: Home, Includes_Home, Custom_1120…1126
- by `mkfonts.py`: Font.xml · by `sizepass.py`: Includes_Size.xml
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
- **Strings:** skin strings live in en_gb `strings.po`. Used: 31900–31998;
  **31999 is the last free id in that block** — open a new block (e.g. 31800–31899)
  next. Prefer an existing Kodi string id when one says the same thing.
- **Grouplists:** every child needs an `id` (id 0 breaks navigation) — put
  captions/labels outside the grouplist.
- **Static item properties:** never name them `icon`, `thumb`, `label`, `label2`
  (Kodi treats those as art/labels and they never update — use `ico`); never a
  bare number (it gets localized — use `$NUMBER[n]`). `validate.py` enforces both.
- **Desktop tiles** are skin strings `tile.N.{id,lid,pre,name,icon,image,action,addon}`,
  N=1..36, `home.layout` ∈ 3x3, 4x3 (default), 4x4, 5x4, 5x5, 6x5, 6x6.
- **Version stamps** (bump all on release): `addon.xml`, `xml/SkinSettings.xml`
  (`v0.9.6  -  1024x600`), `xml/Includes_Chrome.xml` (`ArthurOS 1.2 (v0.9.6)`),
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

Reference sources in `vendor/kodi/src/` (Skin.cpp, game dialogs) and Estuary
excerpts in `vendor/kodi/estuary-ref/`. For anything else, read the Kodi
**Omega** branch on GitHub (`xbmc/xbmc`, branch `Omega`) rather than guessing.
`inventory.py` (regenerates `inventory.json`) needs a full Estuary checkout:
`ESTUARY=/path/to/xbmc/addons/skin.estuary/xml python3 inventory.py`.

## Scripts that run inside Kodi (`skin.arthuros/scripts/`)

- `backup.py` — skin settings backup/restore (JSON-RPC + Skin.* builtins).
- `mousewatch.py` — Touch mode mouse detection via `/proc/bus/input/devices`.
- `netbt.py` — Wi-Fi/Bluetooth/audio output for Raspberry Pi OS (nmcli,
  bluetoothctl). Vince's own script, shipped verbatim — ask before changing it.

All via `RunScript(special://skin/scripts/<name>.py[,args])`.

## State at handover (0.9.6)

Installed on the Pi 4 at 0.9.5 (confirmed working install). 0.9.6 built and
delivered, **not yet tested on the box**. Untested-on-hardware items:
- 0.9.6 OSD Settings row, Add-on button (does `arthuros.plugin` get set when
  YouTube is started from its own menus / a favourite / a tile?), the
  toolbar Add-on settings button, the game picture dialogs.
- 0.9.5 4:3 layout on the real 2048x1536 panel.
- netbt.py on real hardware (polkit may refuse NetworkManager for a service user).
- Editor dialogs 1124/1126 closing themselves from onload; Tile dialog load time.

Known gaps / candidates:
- Settings hub tile panel doesn't use the extra height at 768.
- Dialogs keep 600-era sizes in 768.
- Toolbar buttons are 26 px high — small for touch.
- PVR guide (`epggrid`) and channel windows deserve a design pass.
- On 5x5/6x6 desktops very long tile names lose their last line.

## Working with Vince

- He reports what he sees on the box (often screenshots/logs). Diagnose from
  Kodi source, fix in the generator, add an audit check, rebuild, package.
- Ship each change as a new version: bump stamps, changelog entry written for
  him (what he'll notice, not internals), `./package.sh`, then he installs with
  `install-arthuros.sh`.
- Say plainly what was verified only in preview vs. on hardware.
