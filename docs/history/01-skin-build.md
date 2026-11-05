# ArthurOS skin for Kodi — build notes (written at 0.2.0)

Target then: Kodi 21.3 Omega on a Pi 3B+, LibreELEC 12.2.1, 1024x600 @60Hz.
Look: Acorn Arthur 1.2 desktop (per Vince's reference mock-up).

## Decisions made

- **From scratch**, not a fork of Estuary. Hand-built core + a generator for
  the long tail, with `xml/Defaults.xml` as a global safety net.
- **Both remote/d-pad and mouse.** Navigation is explicit, not geometric-only.
- Delivery: zip into the `Kodi work` folder; Vince copies to the box.

## Key technical facts (verified against Kodi source, not guessed)

- Omega needs `<import addon="xbmc.gui" version="5.17.0"/>`.
- `<res width="1024" height="600" aspect="16:9" default="true" folder="xml"/>`.
  Kodi stretches skin coords to screen; it does not letterbox.
- Font: **Tamzen**, native sizes **12 / 14 / 16 / 20** only.
- Kodi falls back to `font13`, so it must exist in Font.xml.
- Media windows: ids **2** view, **3** sort by, **4** sort order, **19** filter,
  **12** item count, **50+** views.
- Dialog box base: heading **1**, lines **2/3/4**, textbox **9**, buttons
  **10** no / **11** yes / **12** custom, progress **20**.
- Keyboard keys: `id = row*20 + col + 100`, 4 rows.
- **Settings hub (`Settings.xml`) is NOT populated by Kodi** — the skin lists
  the sections. `SettingsCategory.xml` *is*, via grouplist 3 + grouplist 5 with
  template controls 7/8/9/11/12/13/14/15/20 that Kodi clones.
- **Pointer.xml needs control ids 1/2/3/4** (normal, focus, drag, click). One
  unidentified image = no mouse cursor at all.
- **DialogAddonInfo buttons**: 6 install, 7 enable, 8 update, 9 settings,
  10 dependencies, **12 select/open**, 13 auto-update, 14 versions. Kodi hides
  the inapplicable ones, but they must all exist and be visible.
- **Window names are not free-form.** `Favourites` is invalid; it is
  `favouritesbrowser`. `Busy` is `busydialog`. Full table in
  `windownames.txt` (from `xbmc/input/WindowTranslator.cpp`).
- `addons://user/all/` = installed minus dependency modules.
  `addons://sources/{video,audio,image,executable}/` = launchable content
  add-ons by type. No built-in "exclude bundled" filter exists.
- `slideshow` is not a valid control type; Kodi draws slides itself.

## The v0.1.0 post-mortem — worth remembering

The skin loaded with **zero errors in kodi.log** and still looked wrong. Cause:
`<default type="image"><aspectratio>keep</aspectratio></default>`. Every bevel
and fill texture is square, so Kodi letterboxed each into a centred square and
full-width panels collapsed into a column down the middle. Kodi's own default
is `stretch`.

Lessons that shaped the tooling:
1. **A clean log proves nothing about appearance.** A valid-but-wrong attribute
   value never reaches the log. Screenshots are the only check.
2. `preview.py` missed it because it ignored `aspectratio`. It now honours it.
3. Global defaults have global blast radius — audit them hardest.

## Tools

- `mkmedia.py` — all PNGs from pixel grids + bevel maths
- `inventory.py` / `inventory.json` — control-id contract per window
- `genwindows.py` — emits the ~55 generated windows
- `validate.py` — static checks
- `preview.py` — approximate XML renderer to PNG
- `windownames.txt` — Kodi's valid ActivateWindow targets

Vince's Kodi once had skin Zoom at **-2%** — reset it to 0 when judging pixel
alignment.
