# ArthurOS: findings for 0.9.0 – 0.9.2

## 0.9.2: the Everything menu, and Back through Kodi's menus

**Hardware note (at the time).** Vince moved from the Pi 3B+ to a ROC-RK3328-CC running LibreELEC 12.2.1 64-bit (hostname ROKbox, 192.168.68.63; old Pi at 192.168.68.65). Moving `.kodi` across brought the Pi's 32-bit binary add-ons (vfs.libarchive, inputstream.*, game.libretro, genplus), and `addons/packages` held cached zips Kodi reinstalls from when the version matches. Fix: clear `addons/packages`, delete add-ons whose `.so*` has ELF class byte 1, reinstall from the repo. The Internet Archive Game Launcher crash came from the missing vfs.libarchive.

**Everything section.** Section `all` (string 31990, icon `file_list`, caption 31991), 30 entries: libraries/files/playlists for video and music, pictures, TV, radio, games, add-on browser root and My add-ons, programs, favourites, weather, file manager, settings hub, skin settings, system info, events, profiles, LibreELEC settings (only with `System.HasAddon(service.libreelec.settings)`), Customise desktop, power menu.

**Entry format.** Section entries are `(lid, icon, action[, pre[, visible]])`. `pre` is a string id shown in front of the name ("Videos - Library"), omitted when equal to the section's own name. `PRE_LIDS` drives the name variables.

**Back behaviour.** Every `ActivateWindow(...,return)` made Back jump straight to Home. `vid()`, `mus()`, `pic()`, `prg()`, `add()` no longer add `return`; Kodi's `SetHistoryForPath` fills in parent folders so Back climbs a level at a time. Tile actions stored with `return` are rewritten once by invisible dialog 1126, which Home opens while `!Skin.HasSetting(home.v092)` (1190 conditional onloads, ~280 KB, loaded once).

## 0.9.1: what Vince saw, and why

1. **Editor icons didn't update / moved tile took the icon of its new place.** `CGUIStaticItem::UpdateProperties` treats properties named `label`, `label2`, `thumb`, `icon` as the item's labels and art, so `ListItem.Property(icon)` kept its load-time value. Item property is now `ico` (skin string still `tile.N.icon`).
2. **Tile numbers showed words.** `CGUIControlFactory::GetInfoLabelFromElement` turns a bare number into a localized string (`3` → "Videos"). Use `$NUMBER[3]`. `validate.py` rejects both problems.
3. **Tile names ended in "...".** Labels inside list layouts are `CGUIListLabel`, which never wraps. Captions are `textbox` (wraps, honours align/aligny in layouts). Icons a size smaller: `icons80` on 3-row grids, 48 on 4 rows, 32 on 5 and 6.
4. **Stylized add-on icons.** No brand logos — original pictures: `addon_stream`, `addon_server`, `addon_arcade`, `addon_radio`, `addon_config`. Dialog 1124 picks by add-on id: plex/jellyfin/emby → server; game/iagl/retro/emulat → arcade; libreelec/settings/service. → config; plugin.audio. → radio; plugin.video. → stream; plugin.image. → pictures; else program. Field `tile.N.addon` holds the id; "Add-on's own picture" button (1139) brings back the add-on art.

## Skin settings backup (0.9.1)

`scripts/backup.py` via `RunScript(special://skin/scripts/backup.py,backup|restore)` (RunScript takes a file path). Buttons 111/112 in Skin settings.
- Backup reads `special://profile/addon_data/skin.arthuros/settings.xml` after 1 s (Kodi saves skin settings 500 ms after a change), plus `lookandfeel.skincolors`, `font`, `skintheme`, `skinzoom` via JSON-RPC. Writes `arthuros-settings-YYYY-MM-DD-HHMM.xml` (default `addon_data/skin.arthuros/backups/`). Leaves out working values: edit.slot, pick.addon, home.flip, swap.*, arthur.min*.
- Restore asks first, applies only differences with `Skin.SetString/SetBool/Reset` (not a file copy: `UnloadSkin` saves in-memory settings over it), toggles home.flip, sets look-and-feel last (they reload the skin).

## How the desktop is stored

Each tile is a set of skin strings `tile.N.{id,lid,pre,name,icon,image,action,addon}`, N = 1..36.

| Field | Meaning |
|---|---|
| `id` | A section with a submenu. Empty means the tile runs `action` directly. |
| `lid` | String id for the tile's name. |
| `pre` | Section name shown in front ("Movies - Genres"). |
| `name` | User-typed name or add-on title; wins over `lid`. |
| `icon` | Icon name from the registry. |
| `image` | Picture file or add-on icon; wins over `icon`. |
| `action` | Builtin a direct tile runs. |
| `addon` | Add-on id, for tiles that run an add-on. |

- Names come from `lid` via HomeTileName, HomeFocusName, EditTileName, so switching to US English renames tiles.
- `home.layout` ∈ 3x3, 4x3 (default, also when empty/unknown), 4x4, 5x4, 5x5, 6x5, 6x6.
- Home.xml has one panel 9000, list 9010, scrollbar 9011; geometry and layouts come from `<include condition=...>` blocks.
- First run: Home's onload writes the 12 default tiles.

## Kodi facts checked in the source

- Static list properties refresh only every 1000 ms and nothing refreshes them on re-init. Workaround: editor onunload toggles home.flip; Home has an include condition on it, so Home reloads.
- `CGUIAction::ExecuteActions` evaluates every condition first, then runs actions in order, synchronously; `$INFO/$ESCINFO/$VAR` resolve just before each. Load/unload actions are synchronous.
- Every `Skin.SetString/SetBool/Reset` also saves guisettings.xml. `Skin.SetBool(name,false)` is supported.
- `System.AddonTitle`/`System.AddonIcon` take any single info label as parameter.
- Custom windows: files `custom*.xml`, window id = file id + 10000; a dialog without `<visible>` is modal.

## Watch for on the box

- 1124 and 1126 close themselves from their own onload (least-tested piece).
- How long the Tile dialog (~500 KB) takes to open.
- On 5x5 and 6x6, very long names still lose their last line.
