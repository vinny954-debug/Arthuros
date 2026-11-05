# ArthurOS: 0.9.3 – 0.9.6

## 0.9.3 Touch mode

Asked for: a touch-only mode, easier to tap, no pointer without a mouse (then a 7" 1024x600 HDMI touchscreen).

- **Taller rows.** `XLC` in sizepass.py and home.py is `[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]`: Touch mode gets the Extra large row heights (+16 px) with normal text. Desktop tiles use `FONTXL` (font-only), since their icon sizes depend on the font.
- **Back button.** Chrome_Taskbar button 9105 "Back" (31994), `Action(Back)`, full task-bar height, where the clock was (tray hidden in touch mode).
- **Pointer.** Every tap sends `ACTION_MOUSE_MOVE`, and `CApplication::OnAction` calls `SetMouseActive(true)`. No info label tells mouse from touch. `scripts/mousewatch.py` reads `/proc/bus/input/devices` every 3 s (REL_X+REL_Y = mouse) and sets `Window(Home).Property(arthuros.mouse)`. `PointerTex`/`PointerClickTex` (Variables.xml) return no texture while Touch mode is on and the property is empty. Started from Home onload and the Skin settings toggle (id 113, 31995, reloads skin).

## 0.9.4 Network & Bluetooth

Kodi as a service on Raspberry Pi OS has no LibreELEC settings add-on. `scripts/netbt.py` (Vince's script, verbatim): Wi-Fi via nmcli, Bluetooth via bluetoothctl, Kodi audio output. `RunScript(special://skin/scripts/netbt.py[,wifi|bt|audio])`. Entry "Network & Bluetooth" (31996, icon `network`) in Settings.xml, the desktop Settings submenu, Everything, and the Customise desktop catalogue, all under `NETBT = !System.HasAddon(service.libreelec.settings) + System.Platform.Linux + !System.Platform.Android`. Possible first-run issue: polkit refusing NetworkManager changes for a service user → `sudo usermod -aG netdev $USER`, or a polkit rule.

## 0.9.5 4:3 layout (1024x768, folder xml768)

Target: Pi 4 on Raspberry Pi OS, Kodi as a service, iPad 3 panel 2048x1536 with touch (= exact 2x).

- addon.xml declares `xml` 1024x600 16:9 (default) and `xml768` 1024x768 4:3. `closestRes` picks by aspect first. `GetSkinPath` falls back per file to the default folder's coordinates, so xml768 must be complete.
- `ARTHUR_H=768 home.py` writes Home.xml + Includes_Home.xml into `build768/` (panel 702 high; rows 231/173/138/115 for 3/4/5/6 rows; icons 96/64/48/48, XL 80/48/32/32; well/list +168).
- `XMLDIR=build768` runs themepass and sizepass on the staged desktop (sizepass skips Includes_Lists/Includes_Size there).
- `tallpass.py` writes xml768: inlines unconditional includes per window (fills $PARAM); screen level ≥85% height grows, lower-half starts move, rest stays; nested: body = tallest scroller (else tallest control), anything crossing its middle grows, below it moves; heights from conditional Height_NN includes move but never grow; `<coordinates>` windows and percent-centred dialogs untouched; "1024x600" label → "1024x768".
- Fixed: tallpass dropped an include at the top of a definition (now expands inside a holder). SettingsCategory level label/button hang from `<bottom>` with an XL label variant; grouplist 3 is 404 high.
- User setup: resolution 2048x1536, skin zoom 0%, "Limit GUI size" no limit if shown, Touch mode on.
- Known: the Settings hub tile panel keeps fixed item heights (~1/4 empty at 768). Dialogs keep 600-era sizes, centred.

## 0.9.6 Player and add-on settings

Report: in YouTube there was no way to change audio/resolution while playing. The OSDs had only transport + Playlists/Record/Menu/Subtitles/Close.

- OSDs are 892x288 with two rows under the transport (genwindows `osd_extras`/`osd_buttons`); navigation 201→202→203→201.
  - Video row 2 "Settings:": Video (OSDVideoSettings — its **Video stream** entry is where ISA/YouTube list resolutions), Audio (OSDAudioSettings), Subtitles (OSDSubtitleSettings), Bookmarks (VideoBookmarks), Add-on.
  - Video row 1: Record only on `[PVR.IsPlayingTV | PVR.IsPlayingRadio]`, Menu only on `VideoPlayer.HasMenu`, "Find subtitles" (31998).
  - Music row 2: Audio, Add-on.
  - Game: row 1 Save / Load (InGameSaves), Reset (`PlayerControl(Reset)`), Close; row 2 Filter (GameVideoFilter), Stretch (GameStretchMode, 31997), Rotation (GameVideoRotation), Volume (GameVolume), Advanced (GameAdvancedSettings).
  - Labels kept short (Kodi strings 291, 292, 287, 298, 24000, 587, 35227, 13376, 10038) to pass textfit at Extra large. The "Settings:" caption sits outside the grouplist.
- **Which add-on is playing:** a plugin's resolved stream path no longer names it, so the 12 media browsers set `<onunload>SetProperty(arthuros.plugin,$INFO[Container.PluginName],home)</onunload>`; Home onload clears it when `!Player.HasMedia`; the Add-on button shows only while `Window(Home).Property(arthuros.plugin)` is non-empty.
- **Media toolbar:** button 9502 "Add-on settings" (10140), `Addon.OpenSettings($INFO[Container.PluginName])`, visible only inside a plugin; item-count label 12 hides meanwhile; grouplist width 1000.
- **DialogSelect game dialogs:** gamevideofilter / gamestretchmode / gamevideorotation / ingamesaves borrow DialogSelect.xml but use ids from DialogGameDefines.h: 10810 heading, 10811 panel of `gamewindow` previews (videofilter/stretchmode/rotation from `ListItem.Property(game.*)`), 10812 description. Shown under a `Window.IsActive(...)` condition; lists 3/6, scrollbar 61 and buttons hidden meanwhile. Saves: screenshot art if present, else live gamewindow. These dialogs were unusable before.
- preview.py `SET=` overrides any info label or boolean by exact name (`SET="Container.PluginName=x"`, `SET="window.isactive(gamevideofilter)=true"`).
- Untested on the box as of handover.
