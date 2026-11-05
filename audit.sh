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
chk "Kodi-driven windows have captions and titles (labelcheck)" 'python3 "$(dirname "$0")/labelcheck.py"'
chk "numeric keypad shows digits, not string ids" 'grep -q "<label>\$LOCALIZE\[12317\]</label>" $S/xml/DialogNumeric.xml && ! grep -qE "<label>(OK|[0-9]+)</label>" $S/xml/DialogNumeric.xml'
chk "media source Browse/Add/Remove captioned"  'grep -q "id=\"11\"><width>210</width>.*LOCALIZE\[1024\]" $S/xml/DialogMediaSource.xml && grep -q "LOCALIZE\[15019\]" $S/xml/DialogMediaSource.xml && grep -q "LOCALIZE\[1210\]" $S/xml/DialogMediaSource.xml'
chk "keyboard heading 311 on the title bar"      'grep -A1 "type=\"label\" id=\"311\"" $S/xml/DialogKeyboard.xml | grep -q "<left>29</left>" && ! grep -q "content=\"Dialog_Heading\"" $S/xml/DialogKeyboard.xml'
chk "slider dialog has working - and + buttons"  'grep -q "Action(Left)</onclick><onclick>SetFocus(13)" $S/xml/DialogSlider.xml && grep -q "Action(Right)</onclick><onclick>SetFocus(14)" $S/xml/DialogSlider.xml'
chk "power menu master mode says Enter/Leave"    '! grep -q "LOCALIZE\[20043\]" $S/xml/DialogButtonMenu.xml && grep -q "LOCALIZE\[20045\]" $S/xml/DialogButtonMenu.xml && grep -q "LOCALIZE\[20046\]" $S/xml/DialogButtonMenu.xml'
chk "settings level buttons send SettingsLevelChange" 'grep -q SettingsLevelChange $S/xml/SettingsCategory.xml && grep -q SettingsLevelChange $S/xml/DialogAddonSettings.xml'
chk "music playlist editor shows the playlist (100)" 'grep -A1 "type=\"list\" id=\"100\"" $S/xml/MyMusicPlaylistEditor.xml | grep -vq "<left>-"'
chk "calibration markers have textures, no chrome" 'test $(grep -c "<texturenofocus>calibrate/cal_" $S/xml/SettingsScreenCalibration.xml) -eq 5 && ! grep -q "Chrome_" $S/xml/SettingsScreenCalibration.xml'
chk "calibration: no skin button (drawn scaled, hit unscaled)" 'for d in xml xml768; do ! grep -qE "type=\"(button|togglebutton|radiobutton)\"" $S/$d/SettingsScreenCalibration.xml || exit 1; done && grep -q "31834" $S/xml/SettingsScreenCalibration.xml'
chk "calibration markers are not desktop tile icons" '! ls $S/media/icons*/cal_* >/dev/null 2>&1 && test -f $S/media/calibrate/cal_reset.png'
chk "colour picker rows show the colour"          'grep -q "<colordiffuse>\$INFO\[ListItem.Label2\]</colordiffuse>" $S/xml/DialogColorPicker.xml'
chk "generic dialogs navigate to real controls (no 9100)" 'for d in xml xml768; do for f in $(grep -l "Dialog_Box" $S/$d/*.xml); do grep -q Chrome_Taskbar $f && continue; ! grep -q "<on[a-z]*>9100</on[a-z]*>" $f || { echo $f; exit 1; }; done; done'
chk "generic dialog without a list: Right stays put" 'for f in DialogPVRGuideControls DialogFullScreenInfo; do ! grep -q "<onright>9903</onright>" $S/xml/$f.xml || exit 1; done'
chk "login screen cannot reach Home or Settings" 'for d in xml xml768; do ! grep -qE "ActivateWindow\((Home|Settings)\)" $S/$d/LoginScreen.xml || exit 1; done && grep -q "ActivateWindow(ShutdownMenu)" $S/xml/LoginScreen.xml'
chk "nothing reachable from the login screen gets past it (includes expanded)" 'python3 "$(dirname "$0")/logincheck.py"'
chk "login Shutdown is a 40 px row, not a strip button" 'grep -A1 "type=\"grouplist\" id=\"9000\"" $S/xml/LoginScreen.xml | grep -q "<height>40</height>" && ! grep -q "<top>568</top>" $S/xml/LoginScreen.xml'
chk "settings dialog buttons 30 px, taller in Touch/XL" 'grep -A1 "type=\"grouplist\" id=\"9001\"" $S/xml/DialogSettings.xml | grep -q "Height_30_XL" && grep -A1 "type=\"grouplist\" id=\"9001\"" $S/xml/DialogAddonSettings.xml | grep -q "Height_30_XL"'
chk "profiles: Auto login shows the chosen profile" 'grep -q "<label2>\$INFO\[System.ProfileAutoLogin\]</label2>" $S/xml/SettingsProfile.xml'
chk "channel manager shows hidden, locked, changed"  'for p in ActiveChannel ParentalLocked Changed Icon; do grep -q "ListItem.Property($p)" $S/xml/DialogPVRChannelManager.xml || exit 1; done'
chk "no Estuary-only blank buttons (799, 501)"   '! grep -lE "id=\"(799|501)\"" $S/xml/EventLog.xml $S/xml/LoginScreen.xml $S/xml/SettingsProfile.xml $S/xml/MyMusicPlaylistEditor.xml'
chk "TV guide is titled Guide, not Channel"      '! grep -q "LOCALIZE\[19029\]" $S/xml/MyPVRGuide.xml'
chk "no unused skin strings"                     'for i in $(sed -n "s/^msgctxt \"#\([0-9]*\)\"/\1/p" $S/language/resource.language.en_gb/strings.po); do case $i in 3191[3-6]) continue;; esac; grep -rqs "$i" $S/xml $S/scripts $S/addon.xml || { echo "unused $i"; exit 1; }; done'
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
