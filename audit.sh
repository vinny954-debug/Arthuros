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
chk "D-1 power menu in the Settings hub"      'grep -q "<onclick>ActivateWindow(ShutdownMenu)</onclick>" $S/xml/Settings.xml'
chk "D-1 power menu in the desktop Settings"  'grep -A2 "icons24/power.png" $S/xml/Home.xml | grep -q "Property(id),settings)"'
chk "D-2 skin reset asks first"               '! grep -q "<onclick>Skin.ResetSettings</onclick>" $S/xml/SkinSettings.xml $S/xml768/SkinSettings.xml && grep -q "backup.py,reset" $S/xml/SkinSettings.xml && grep -q "yesnocustom" $S/scripts/backup.py && grep -q "KEEP_ON_RESET" $S/scripts/backup.py'
chk "D-3 rename never stores (empty)"         'grep -qF "Property(name)) + !String.IsEmpty(Container(1150).ListItem.Property(lid))" $S/xml/Custom_1121_DesktopTile.xml'
chk "D-3 name-only slots stay off the desktop" 'grep -qF "<visible>[!String.IsEmpty(Skin.String(tile.1.id)) | !String.IsEmpty(Skin.String(tile.1.action))]" $S/xml/Home.xml'
chk "D-4 tile group list has a scrollbar"     'grep -A4 "type=\"list\" id=\"200\"" $S/xml/Custom_1122_DesktopChoose.xml | grep -q "<pagecontrol>201</pagecontrol>" && grep -q "type=\"scrollbar\" id=\"201\"" $S/xml/Custom_1122_DesktopChoose.xml'
chk "D-5 autoscroll setting says what it does" 'grep -A1 "\"#31910\"" $S/language/resource.language.en_gb/strings.po | grep -q "Scroll long descriptions"'
chk "D-6 backup/restore recognise Cancel"     'grep -q "same_path(path, BACKUPS)" $S/scripts/backup.py && grep -q "Dialog().select(L(31981)" $S/scripts/backup.py'
chk "D-7 parked-window state is transient"    'grep -q "TRANSIENT_PREFIX = (\"swap.\", \"arthur.min\")" $S/scripts/backup.py && grep -q "startswith(TRANSIENT_PREFIX)" $S/scripts/backup.py'
chk "T-10 skin settings list scrolls"         'for d in xml xml768; do grep -A4 "type=\"grouplist\" id=\"99\"" $S/$d/SkinSettings.xml | grep -q "<pagecontrol>98</pagecontrol>" && grep -q "type=\"scrollbar\" id=\"98\"" $S/$d/SkinSettings.xml || exit 1; done'
chk "T-5 skin help text scrolls"              'grep -q "<pagecontrol>97</pagecontrol>" $S/xml/SkinSettings.xml && grep -q "type=\"scrollbar\" id=\"97\"" $S/xml/SkinSettings.xml'
chk "touch pointer choice in skin settings"   'grep -q "Skin.SetBool(touch.pointer.show)" $S/xml/SkinSettings.xml && grep -q "Skin.SetBool(touch.pointer.hide)" $S/xml/SkinSettings.xml && grep -q "name=\"TouchPointerVar\"" $S/xml/Includes_Home.xml'
chk "D-2 reset button label fits 130 px at XL"  'grep -A1 "\"#31867\"" $S/language/resource.language.en_gb/strings.po | grep -q "msgid \"Back up\"$"'
chk "backup names an unreadable settings file" 'grep -A3 "if settings is None" $S/scripts/backup.py | grep -q "L(31871)" && grep -A1 "\"#31871\"" $S/language/resource.language.en_gb/strings.po | grep -q "could not be read"'
chk "L-2 Customise desktop rows fit at XL"    'test $(grep -c "Height_30_XL" $S/xml/Custom_1120_DesktopEditor.xml) -eq 9 && ! grep -q "Height_34" $S/xml/Custom_1120_DesktopEditor.xml'
chk "L-4 icon picker cells fill the well"     'grep -q "itemlayout width=\"74\" height=\"68\"" $S/xml/Custom_1123_DesktopIcon.xml && grep -q "<left>763</left>" $S/xml/Custom_1123_DesktopIcon.xml'
:
:
# ===== P7 browsers & info =====
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
