#!/bin/sh
# Confirms fixes actually reached the shipping tree. Twice now a fix was made by
# hand in a file that genwindows.py regenerates, and was silently undone.
S="$(dirname "$0")/skin.arthuros"
fail=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "  OK   $1"; else echo "  FAIL $1"; fail=1; fi; }
chk "Pointer has cursor ids 1-4"     'test $(grep -c "type=\"image\" id=\"[1-4]\"" $S/xml/Pointer.xml) -eq 4'
chk "pointer_click.png exists"       'test -f $S/media/pointer_click.png'
chk "no Window(Busy)"                '! grep -rq "Window(Busy)" $S/xml/'
chk "no ActivateWindow(Favourites)"  '! grep -rq "ActivateWindow(Favourites)" $S/xml/'
chk "image aspectratio is stretch"   'grep -A1 "<default type=\"image\">" $S/xml/Defaults.xml | grep -q stretch'
chk "no container defaults"          '! grep -qE "^  <default type=\"(list|panel|fixedlist|wraplist)\">" $S/xml/Defaults.xml'
chk "bevels are 24x24"               'python3 -c "from PIL import Image;import sys;sys.exit(0 if Image.open(\"'"$S"'/media/button_up.png\").size==(24,24) else 1)"'
chk "Font.xml idloc resolves"        'grep -q "idloc=\"13278\"" $S/xml/Font.xml'
chk "Large fontset present"          'grep -q "fontset id=\"Large\"" $S/xml/Font.xml'
chk "addon info has Open (id 12)"    'grep -q "id=\"12\"" $S/xml/DialogAddonInfo.xml'
chk "weather uses Kodi-filled controls" 'grep -q "type=\"label\" id=\"23\"" $S/xml/MyWeather.xml && ! grep -q "Property(Day0" $S/xml/MyWeather.xml'
chk "home has 36 tile slots"          'test $(grep -c "<item id=" $S/xml/Home.xml) -eq 36'
chk "seven desktop grid sizes"        'test $(grep -c "<include name=\"Home_Panel_" $S/xml/Includes_Home.xml) -eq 7'
chk "desktop editor windows ship"     'test $(ls $S/xml/Custom_112*.xml | wc -l) -eq 7'
chk "Customise desktop in Skin settings" 'grep -q "ActivateWindow(1120)" $S/xml/SkinSettings.xml'
chk "settings level button (id 20)"   'grep -q "type=\"button\" id=\"20\"" $S/xml/SettingsCategory.xml'
# the <?xml?> declaration also has version=, so match the indented addon attribute
VER=$(sed -n 's/^[[:space:]]*version="\([0-9.]*\)".*/\1/p' "$S/addon.xml" | head -1)
echo "  ..   addon.xml version: $VER"
chk "menu bar stamp matches version"    'grep -q "(v$VER)" $S/xml/Includes_Chrome.xml'
chk "skin settings stamp matches"       'grep -q "v$VER  -  1024x600" $S/xml/SkinSettings.xml'
chk "menu tiles focus the panel"        'test $(grep -c "SetFocus(9010,0)" $S/xml/Home.xml) -eq 36'
chk "Weather ships as a direct tile"    'grep -q "Skin.SetString(tile.10.action,\"ActivateWindow(Weather)\")" $S/xml/Home.xml'
chk "task bar takes an up target"       'grep -q "param name=.up." $S/xml/Includes_Chrome.xml'
chk "all Kodi fallback icons present" 'test $(ls $S/media/Default*.png | wc -l) -ge 113'
chk "vintage pointer is 28x44"        'python3 -c "from PIL import Image;import sys;sys.exit(0 if Image.open(\"'"$S"'/media/pointer.png\").size==(28,44) else 1)"'
chk "power menu is hand-built"        'grep -q "Powerdown()" $S/xml/DialogButtonMenu.xml'
chk "file browser ids are right"      'grep -q "id=\"450\"" $S/xml/FileBrowser.xml && grep -q "type=\"label\" id=\"411\"" $S/xml/FileBrowser.xml'
BROWSERS="MyVideoNav MyMusicNav MyPics MyPrograms AddonBrowser MyFavourites MyPlaylist MyGames MyPVRChannels MyPVRRecordings MyPVRSearch MyPVRTimers"
chk "every media browser manages 3 views" 'for b in $BROWSERS; do grep -q "<views>50,51,52</views>" $S/xml/$b.xml || exit 1; done'
chk "radio circles inside their buttons"  '! grep -q "<radioposx>-" $S/xml/Defaults.xml'
chk "five colour palettes ship"           'test $(ls $S/colors/*.xml | grep -vc defaults.xml) -ge 5'
chk "seven fontsets"                      'test $(grep -c "<fontset " $S/xml/Font.xml) -eq 7'
chk "title-bar boxes are live buttons"    'grep -q "type=\"button\" id=\"9903\"" $S/xml/Includes_Chrome.xml'
chk "system info sections are labelled"   'grep -q "LOCALIZE\[20037\]" $S/xml/SettingsSystemInfo.xml'
chk "install from zip on the desktop"     'grep -q "<onclick>InstallFromZip</onclick>" $S/xml/Home.xml'
chk "pointer style is selectable"         'grep -q "VAR\[PointerTex\]" $S/xml/Pointer.xml'
chk "no baked title-bar colours left"     '! grep -rq ">bar_\(red\|blue\|grey\)\.png<" $S/xml/'
chk "My add-ons has its own icon"       'test -f $S/media/icons64/addons_user.png'
chk "no bare Chrome_Taskbar include"    '! grep -l "<include>Chrome_Taskbar</include>" $S/xml/*.xml'
chk "Startup hands over on load"       'grep -q "<onload>ReplaceWindow(\$INFO\[System.StartupWindow\])</onload>" $S/xml/Startup.xml'
chk "Startup has no clickable boxes"   '! grep -q "Dialog_Box\|Win_Title" $S/xml/Startup.xml'
chk "four title-bar box modes"         'test $(grep -c "<include name=\"Win_Boxes_" $S/xml/Includes_Chrome.xml) -eq 4'
chk "_ parks windows on the task bar"  'grep -q "arthur.minwin" $S/xml/Includes_Chrome.xml && grep -q "id=\"9104\"" $S/xml/Includes_Chrome.xml'
chk "now-playing recall kept"          'grep -A6 "id=\"9101\"" $S/xml/Includes_Chrome.xml | grep -q "ActivateWindow(Visualisation)"'
chk "icon registry wired in"           'test -f $S/media/icons64/power.png && test -f $S/media/DefaultAddonsZip.png'
chk "box glyphs follow the text colour" 'grep -q "colordiffuse=\"text\">wc_min_g.png" $S/xml/Includes_Chrome.xml'
chk "skin settings heading has an id"  'grep -q "type=\"label\" id=\"105\"" $S/xml/SkinSettings.xml'
chk "add-on settings show their pages"   'grep -A1 "type=\"grouplist\" id=\"3\"" $S/xml/DialogAddonSettings.xml | grep -q "<left>16</left>"'
chk "skin settings backup script ships"  'test -f $S/scripts/backup.py && grep -q "scripts/backup.py,restore" $S/xml/SkinSettings.xml'
chk "tile captions wrap (textbox)"        'grep -q "<control type=\"textbox\"><left>4</left>" $S/xml/Includes_Home.xml'
chk "add-on tile icons ship"              'test -f $S/media/icons80/addon_stream.png && test -f $S/media/icons80/addon_server.png'
chk "touch mode: Back button and pointer rule" 'grep -q "id=\"9105\"" $S/xml/Includes_Chrome.xml && grep -q "arthuros.mouse" $S/xml/Variables.xml && test -f $S/scripts/mousewatch.py'
chk "touch mode grows rows"               'grep -q "Skin.HasSetting(touchmode)\]" $S/xml/Includes_Size.xml $S/xml/SkinSettings.xml'
chk "OSD offers video/audio/subtitle settings" 'grep -q "ActivateWindow(OSDVideoSettings)" $S/xml/VideoOSD.xml && grep -q "ActivateWindow(OSDAudioSettings)" $S/xml/VideoOSD.xml && grep -q "ActivateWindow(OSDSubtitleSettings)" $S/xml/VideoOSD.xml'
chk "music OSD offers audio settings"   'grep -q "ActivateWindow(OSDAudioSettings)" $S/xml/MusicOSD.xml'
chk "game OSD offers game settings"     'grep -q "ActivateWindow(GameVideoFilter)" $S/xml/GameOSD.xml && grep -q "ActivateWindow(InGameSaves)" $S/xml/GameOSD.xml'
chk "game picture dialogs have their panel" 'grep -q "type=\"panel\" id=\"10811\"" $S/xml/DialogSelect.xml && grep -q "type=\"gamewindow\"" $S/xml/DialogSelect.xml'
chk "add-on settings on the toolbar"    'grep -q "Addon.OpenSettings(\$INFO\[Container.PluginName\])" $S/xml/Includes_Media.xml'
chk "browsers tell the OSD the add-on"  'for b in $BROWSERS; do grep -q "arthuros.plugin" $S/xml/$b.xml || exit 1; done'
chk "4:3 layout declared in addon.xml"   'grep -q "folder=\"xml768\"" $S/addon.xml'
chk "xml768 has every file xml has"     'test "$(ls $S/xml)" = "$(ls $S/xml768)"'
chk "xml768 task bar sits at 736"       'grep -q "<top>736</top>" $S/xml768/Home.xml'
chk "xml768 desktop panel is 702 high"  'grep -q "<height>702</height>" $S/xml768/Includes_Home.xml'
chk "xml768 skin settings say 1024x768" 'grep -q "v$VER  -  1024x768" $S/xml768/SkinSettings.xml'
chk "xml768 version stamp matches"      'grep -q "(v$VER)" $S/xml768/Home.xml'
# ===== P1 video/music/game OSD =====
:
:
# ===== P2 other playback =====
:
:
# ===== P3 generic windows & text =====
:
:
# ===== P4 TV guide =====
:
:
# ===== P5 touch chrome & controls =====
:
:
# ===== P6 desktop & skin settings =====
:
:
# ===== P7 browsers & info =====
chk "C-3 info dialogs focus the button row 9001, not a button Kodi may hide" '(for d in xml xml768; do for f in DialogVideoInfo DialogMusicInfo DialogPVRInfo; do grep -q "<defaultcontrol always=\"true\">9001</defaultcontrol>" $S/$d/$f.xml && grep -q "type=\"grouplist\" id=\"9001\"" $S/$d/$f.xml || exit 1; done; done)'
chk "B-1 status marks are not offered as desktop tile icons" '! grep -q "status_" $S/xml/Custom_1123_DesktopIcon.xml && ! grep -q "status_" $S/xml768/Custom_1123_DesktopIcon.xml'
chk "K-3 add-on folders fill the second row (Refresh / start page)" '(for d in xml xml768; do python3 -c "import lxml.etree as E,sys; r=E.parse(\"$S/$d/Includes_Media.xml\"); sys.exit(0 if all(r.xpath(\"//include[@name=\x27%s\x27]/control[@id=\x27%s\x27][contains(visible,\x27Container.PluginName\x27)]\"%(n,i)) for n in (\"Media_Extras_VideoNav\",\"Media_Extras_MusicNav\") for i in (\"9503\",\"9504\")) else 1)" || exit 1; done; grep -q "Container.Update(plugin://\$INFO\[Container.PluginName\]/)" $S/xml/Includes_Media.xml)'
chk "K-3 PVR channels/recordings show Kodi header 29 (Hidden / Deleted) in the title" '(for d in xml xml768; do python3 -c "import lxml.etree as E,sys; r=E.parse(\"$S/$d/Includes_Media.xml\"); sys.exit(0 if all(r.xpath(\"//include[@name=\x27%s\x27]/control[@id=\x2729\x27][@type=\x27label\x27]\"%n) for n in (\"Media_Extras_PVRChannels\",\"Media_Extras_PVRRecordings\")) else 1)" || exit 1; grep -q "Control.GetLabel(29)" $S/$d/Includes_Media.xml && grep -q "value=\"\$PARAM\[label2\]\"" $S/$d/Includes_Media.xml || exit 1; for w in MyPVRChannels MyPVRRecordings; do grep -q "Media_PVRTitle2Var" $S/$d/$w.xml || exit 1; done; done)'
chk "T-1 Options focuses the view before ContextMenu" '(for f in $S/xml768/My*.xml $S/xml768/AddonBrowser.xml; do grep -q "id=\"9501\"" $f || continue; grep -A6 "id=\"9501\"" $f | tr -d "\n " | grep -q "SetFocus(50)</onclick><onclick>Action(ContextMenu)" || exit 1; done)'
chk "S-7 sort order button shows Container.SortOrder" 'grep -A2 "type=\"button\" id=\"4\"" $S/xml/Includes_Media.xml | grep -q "VAR.MediaSortOrderVar" && grep -A1 "name=\"MediaSortOrderVar\"" $S/xml/Includes_Media.xml | grep -q "INFO.Container.SortOrder"'
chk "S-7 every view names itself (viewtype)" 'grep -q "<viewtype label=\"535\">list" $S/xml/View_50_List.xml && grep -q "<viewtype label=\"20021\">icon" $S/xml/View_51_Poster.xml && grep -q "<viewtype label=\"536\">bigicon" $S/xml/View_52_IconWall.xml'
chk "S-7 file browser Mirror image (416) is labelled" 'grep -A1 "id=\"416\"" $S/xml/FileBrowser.xml | grep -q "LOCALIZE\[749\]" && grep -A1 "id=\"416\"" $S/xml768/FileBrowser.xml | grep -q "LOCALIZE\[749\]"'
chk "B-6 item count label has no id 12 (Kodi overwrites it)" '! grep -q "type=\"label\" id=\"12\"" $S/xml/Includes_Media.xml && grep -q "VAR\[MediaCountVar\]" $S/xml/Includes_Media.xml'
chk "B-6 empty list says so" 'grep -B3 "Integer.IsEqual(Container.NumItems,0) + !Container.IsUpdating" $S/xml/Includes_Media.xml | grep -q "LOCALIZE\[2080\]"'
chk "B-1 list rows show watched/resume/playing" '(for k in ListItem.PlayCount ListItem.IsResumable ListItem.IsPlaying status_watched.png status_resume.png status_playing.png; do grep -q "$k" $S/xml/Includes_Lists.xml || exit 1; done; test -f $S/media/icons24/status_watched.png -a -f $S/media/icons24/status_resume.png -a -f $S/media/icons24/status_playing.png)'
chk "B-1 poster and icon tiles show the status badge" 'grep -q "Arthur_TileStatus" $S/xml/View_51_Poster.xml && grep -q "Arthur_TileStatus" $S/xml/View_52_IconWall.xml && grep -q "ListItem.PercentPlayed" $S/xml/Includes_Lists.xml'
chk "B-2 tiles use Kodi icon chain, no DefaultFolder/DefaultVideo fallback" '! grep -qE "fallback=.Default(Folder|Video).png.>.INFO.ListItem.Art.(poster|thumb)" $S/xml/View_51_Poster.xml $S/xml/View_52_IconWall.xml $S/xml/Includes_Media.xml && grep -q "VAR.PosterArtVar" $S/xml/View_51_Poster.xml'
chk "B-3 info dialogs pick art by type" 'grep -q "VAR\[VideoInfoArtVar\]" $S/xml/DialogVideoInfo.xml && grep -q "VAR\[MusicInfoArtVar\]" $S/xml/DialogMusicInfo.xml && grep -q "VAR\[MusicInfoArtVar\]" $S/xml768/DialogMusicInfo.xml && grep -q "type=\"list\" id=\"50\"" $S/xml/DialogMusicInfo.xml'
chk "B-4 video info hides Trailer/Director/Versions/Extras when n/a" '(for d in xml xml768; do for i in 11 13 14 15; do grep "type=\"button\" id=\"$i\"" $S/$d/DialogVideoInfo.xml | grep -q "<visible>" || exit 1; done; grep "type=\"button\" id=\"8\"" $S/$d/DialogVideoInfo.xml | grep -q InfoPlayLabelVar || exit 1; done)'
chk "C-3 recording info hides the guide-only buttons" '(for d in xml xml768; do for i in 10 5 6 9 11; do grep "type=\"button\" id=\"$i\"" $S/$d/DialogPVRInfo.xml | grep -q "Window.IsActive(PVRGuideInfo)" || exit 1; done; ! grep "type=\"button\" id=\"[0-9]*\"><width>212" $S/$d/DialogPVRInfo.xml | grep -qv "<label>" || exit 1; done)'
chk "T-5 info plot and add-on text scroll by touch (pagecontrol 61)" '(for d in xml xml768; do for f in DialogVideoInfo DialogMusicInfo DialogPVRInfo DialogAddonInfo; do grep -q "<pagecontrol>61</pagecontrol>" $S/$d/$f.xml && grep -q "type=\"scrollbar\" id=\"61\"" $S/$d/$f.xml || exit 1; done; done)'
chk "B-7 tile titles are textboxes (labels in layouts never wrap)" '(for f in View_51_Poster View_52_IconWall Includes_Lists Includes_Media; do python3 -c "import lxml.etree as E,sys; r=E.parse(\"$S/xml/$f.xml\"); sys.exit(1 if r.xpath(\"//itemlayout//wrapmultiline|//focusedlayout//wrapmultiline\") else 0)" || exit 1; done; grep -q "type=\"textbox\"" $S/xml/View_51_Poster.xml)'
chk "B-8 play queue title icon follows video/music" 'grep -q "name=\"icon\" value=\"\$VAR\[ArthurWindowIcon\]\"" $S/xml/MyPlaylist.xml && grep -q "ArthurWindowIcon" $S/xml768/MyPlaylist.xml'
chk "K-3 window-specific buttons exist (Kodi ids)" 'python3 -c "
import lxml.etree as E,sys
need={\"MyPlaylist\":\"20 21 22 26\",\"MyVideoNav\":\"8 10 16 20\",\"MyMusicNav\":\"8 16 20\",\"MyPics\":\"6 7 9\",\"MyPVRChannels\":\"28 6\",\"MyPVRRecordings\":\"5 7 10\",\"MyPVRTimers\":\"8\",\"MyPVRSearch\":\"29 30\"}
radio={\"MyPVRChannels\":\"6\",\"MyPVRRecordings\":\"7 5\",\"MyPlaylist\":\"20\"}
for w,ids in need.items():
  r=E.parse(\"$S/xml768/%s.xml\"%w)
  for i in ids.split():
    c=r.xpath(\"//control[@id=\x27%s\x27]\"%i)
    if not c or c[0].getparent().get(\"id\")!=\"9491\": sys.exit(1)
    if c[0].get(\"type\")!=\"label\" and not c[0].findtext(\"label\"): sys.exit(1)
  for i in radio.get(w,\"\").split():
    if r.xpath(\"//control[@id=\x27%s\x27]\"%i)[0].get(\"type\")!=\"radiobutton\": sys.exit(1)
"'
chk "T-13 file browser picture view (451) has touch-height rows" 'grep -q "focusedlayout height=\"42\" width=\"848\" condition=\"\[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)\]\"" $S/xml/FileBrowser.xml'
chk "C-1 focused rows keep textinv when marked (file browser, music info)" 'test $(grep -c "textinv</textcolor><selectedcolor>textinv" $S/xml/FileBrowser.xml) -ge 4 && grep -q "<selectedcolor>textinv</selectedcolor>" $S/xml/DialogMusicInfo.xml'
:
:
# ===== P8 4:3 layout =====
:
:
# ===== P9 scripts & tooling =====
:
:
# ===== P10 fonts =====
:
:
[ $fail -eq 0 ] && echo "all good" || echo "AUDIT FAILED"
exit $fail
