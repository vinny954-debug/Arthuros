# ArthurOS: diagnosed faults and their causes (0.1 – 0.7.2)

This is a running list of what actually went wrong and how each cause was proven, so none of it has to be argued over again. Each entry was checked against the Kodi 21 Omega source, the crash logs, or pixels measured in a screenshot.

## v0.1.0 → v0.2.0

**The whole layout collapsed into a centred column.** `Defaults.xml` set `<aspectratio>keep</aspectratio>` on every image. All the bevel and fill textures are square, so each one was letterboxed into a centred square. Kodi's own default is `stretch`.

**Add-ons had no Open button.** `DialogAddonInfo` needs 6 install, 7 enable, 8 update, 9 settings, 10 dependencies, **12 select/open**, 13 auto-update, 14 versions. Only 7 was laid out.

**`ActivateWindow(Favourites)` did nothing.** The window's name is `favouritesbrowser`.

## v0.2.0 → v0.3.0

- **Flat panels showed as gradients.** The 6x6 bevels bled under bilinear filtering. They are 24x24 now.
- **The font picker had a blank row.** `idloc` pointed at a string that doesn't exist.

## v0.3.0 → v0.3.1

**The process failure: no cursor for three releases.** The Pointer fix was hand-applied to a generated file, and the generator wiped it out twice. `build.sh`, `audit.sh` and validator rules now prevent this. Container layouts were removed from `Defaults.xml`, because `SetDefaults` appends them unconditionally.

## v0.5.0 → v0.6.0

- **Empty lists.** Some browsers listed only a subset of their views in `<views>`. The unlisted containers were never hidden and covered the live list. The validator now rejects this.
- **System information was empty.** The contract comes from `GUIWindowSystemInfo.cpp`: the focused button (94–101) picks the section, heading 40, lines 2–13, build labels 52/53.
- **Radio circles hung off the left edge.** Kodi measures `radioposx` from the control's left edge, and any non-zero value overrides right-alignment.
- **Labels truncated to "S…".** `textoffsetx` pads button text on both sides. `textfit.py` now measures every fixed label.
- **Palettes.** Chrome uses a neutral texture plus a `colordiffuse` palette name. `themepass.py` applies this on every build.

## v0.6.0 → v0.7.0

**The stuck "Please wait" screen was the skin's fault.** `Startup.xml` had no `<onload>ReplaceWindow($INFO[System.StartupWindow])</onload>`. When Startup is the first window, `Application.cpp` leaves `uiInitializationFinished` false until Startup deinits; its deinit sends `GUI_MSG_UI_READY`. Until that happens:

- `m_bInitializing` stays true, so `ReloadSkin()` returns early and Colour and Font changes are silently refused.
- Peripherals, CEC included, wait on `m_guiReadyEvent`.
- `CGUIWindowStartup::OnAction` swallows every mouse action.
- The splash window isn't deleted.

The fix is Estuary's one-line Startup, and `validate.py` and `audit.sh` enforce it.

**The 0.6.0 crash was not the skin.** SIGSEGV in `__dynamic_cast` ← `CGUIInfoManager::GetMultiInfoLabel` ← `xbmc.getInfoLabel` on the YouTube add-on's service thread (YouTube 7.4.4), while the main thread rebuilt `addons://user/all`. `getInfoLabel` takes no GUI lock (`ModuleXbmc.cpp`): a thread race in Kodi. Older crashes under Confluence included `CAddonInstaller::InstallFromZip` (line 432 indexes `items[0]` even when the zip listing is empty, so any unreadable zip crashes Kodi 21).

**Title-bar boxes.** Each title bar includes `Win_Boxes_{window,dialog,home,none}`, chosen with `<include content="Win_Boxes_$PARAM[boxes]">` (Kodi substitutes params into attributes before resolving a nested include, `ResolveParametersForNode`).

- **Window:** _ stores `$VAR[ArthurWindowName]`, `$ESCINFO[Container.FolderPath]`, `System.CurrentWindow` and an icon in `Skin.String(arthur.min*)`, then goes Home. Task-bar button 9104 restores the window. × goes Home.
- **Dialog:** _ runs `Dialog.Close(all,true)` and goes Home. × sends `Action(Back)`.
- **Max (▫):** enabled only while `Player.HasMedia`; otherwise a stippled greyed glyph covers it.
- **Home:** _ and × greyed out. **No boxes:** busy, progress, seek, notification. **Login screen:** mode `none`.

Onclick builtins resolve `$VAR`, `$INFO` and `$ESCINFO` when they run (`ExecuteXBMCAction` → `CGUIInfoLabel::GetLabel`).

**Unique icons.** `iconset.py` is the only registry: each icon is a base drawing, optionally with a 9x9 corner emblem. `DEFAULT_MAP` maps Kodi's 125 fallbacks, `ALIASES` holds five deliberate synonym pairs. `iconcheck.py` fails the build on identical pixels, undeclared shared fallbacks, stray files, or a repeated icon within a menu. `themepass.py` applies `WINDOW_ICONS` to title bars.

## v0.7.0 → v0.7.1

**Grouplist navigation stopped at id-less controls.** `CGUIControlGroupList::AddControl` chains each child's up/down (or left/right) to its neighbour's id. A child with no id has id 0, and `CGUIWindow::OnMove` treats 0 as "no target". `validate.py` now rejects any id-less child of a grouplist (labels included — put captions outside the grouplist).

**Box glyphs lost in dark palettes.** Box split into `wc_face.png` (tinted `facetint`), `wc_*_g.png` (tinted `text`/`titletext`) and `wc_*_dg.png` (stippled, `textdim`).

## v0.7.1 → v0.7.2

**Weather flashed raw values on refresh** (the addon writes raw values into the same `Window(Weather)` properties before Kodi converts them). Fix: use the control ids Kodi fills from `CWeatherManager::m_info`: 10 location, 11 last updated, 21 icon, 22–28 current conditions, 31–35 plus 10 per day, 2 refresh. Next location only when `Window(Weather).Property(Locations)` > 1.

**Context menu opened off screen.** `CGUIDialogContextMenu::PositionAtCurrentFocus` centres background 999 on the focused control, clamped only against right/bottom. 999 must be top-level at 0,0, no dim. `validate.py` enforces this.

**Marked list items had invisible text.** `CLabelInfo::selectedColor` defaults to 0 (transparent). Default `<selectedcolor>marked</selectedcolor>` with palette colour `marked`.

**File manager has no Home folder** — Kodi behaviour (`CGUIWindowFileManager` lists only "files" sources, special://profile and removable drives). Workaround: add `/storage/` and `/` as file sources (README).

## Environment issues on Vince's boxes (not skin bugs)

- Overscan once scaled the GUI to 91.4%.
- Screenshots come out black during playback (only the GUI plane is captured).
