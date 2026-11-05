# ArthurOS: findings for 0.8.0

## v0.7.2 → v0.8.0

**The inventory tool missed ids passed as `$PARAM[id]`.** `inventory.py` expanded Estuary's includes but never substituted their parameters, so controls whose id came in as `$PARAM[id]` were dropped: video info buttons (Play 8, Resume 9, Trailer 11...), OK/Cancel in smart-playlist editor and rule dialogs (20/21, 18/19), VideoManager 21–28, VideoOSDBookmarks 2–4, EventLog 20/21, game-controller 17–22. The walk now substitutes parameters.

Info dialogs use Kodi's own contracts: `GUIDialogVideoInfo.cpp` 6–15, `GUIDialogMusicInfo.cpp` 6, 7, 8, 10, 12, `GUIDialogPVRGuideInfo.cpp` 4–11. Button 5 (Cast/Plot) is deliberately left out; when absent, Kodi leaves textarea 4 and list 50 visibility to the skin.

**Game controllers came up empty.** `DialogGameControllers.xml` is loaded by controllers, ports and agents; ids clash (3 is a grouplist in one and a list in another). Layout selected with `<include condition="Window.IsDialogTopMost(gamecontrollers|gameports|gameagents)">`. Controllers: Kodi clones template 10 into grouplist 3, templates 7/8/9 into grouplist 5; 31 is the `gamecontroller`, 32 the description. `validate.py` treats conditional-include branches separately when counting duplicate ids.

**Subtitle search.** 150 service list, 120 subtitles, 100/110 service name and logo, 140 status, 130 "exists" indicator, 160 manual search.

**Add-on details.** Kodi 21 uses `ListItem.Addon*` labels (Name, Version, Creator, Summary, Description, Disclaimer, News, Origin, Size, Type, LifecycleDesc, Broken). `ListItem.Property(Addon.*)` is always empty; `validate.py` rejects it.

**Spin arrows.** `GUISpinControlEx.cpp` places arrows at `right - 2*spinwidth - spinposx`. `spinposx` is 8; negative values are rejected.

**Extra-large fonts.** Tamzen TTFs render crisp at exactly twice native sizes (24, 28, 32, 40). `Skin.Font` returns the fontset id. `sizepass.py` adds taller rows while an XL fontset is active:
- list containers get extra `itemlayout`/`focusedlayout` pairs, placed first, with the XL condition;
- row includes get `_XL` twins;
- settings templates and vertical-grouplist rows get height from conditional includes `Height_N` / `Height_N_XL`.

A font change reloads the skin, so include conditions are re-evaluated. Chrome text uses chrome/chromebold/chromesmall fonts, capped at 20px.

**Palettes.** `palettecheck.py` computes WCAG ratios using facetint-multiplied surfaces. Every palette meets AA (4.5:1), High-Contrast palettes 7:1.

**Home editor design (implemented in 0.9.0):** one layout per grid size via `<include condition="String.IsEqual(Skin.String(home.layout),NxM)">`. `CGUIWindow::NeedLoad` reloads Home when an include condition changes value, so the editor is a full window that returns to Home. Tiles are slot strings set to defaults on first run; add-on pick uses `Skin.SetAddon`; moving swaps a slot's strings with its neighbour's through `$INFO` (each onclick resolves at execution).
