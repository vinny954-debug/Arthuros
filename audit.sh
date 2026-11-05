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
chk "T-2 now playing picks game/video/music once" 'B=$(grep -A8 "id=\"9101\"" $S/xml/Includes_Chrome.xml); echo "$B" | grep -q "condition=\"Player.HasGame\">ActivateWindow(FullscreenGame)" && echo "$B" | grep -q "condition=\"Player.HasVideo + !Player.HasGame\">ActivateWindow(FullscreenVideo)" && ! echo "$B" | grep -q "<onclick>ActivateWindow"'
chk "T-3 dialogs carry a touch Back at the task bar" 'grep -A30 "<include name=\"Dialog_Dim\">" $S/xml/Includes_Dialogs.xml | grep -q "id=\"9108\"" && (for f in $(grep -l "<include>Dialog_Dim</include>" $S/xml/*.xml); do grep -q "id=\"9108\"" $S/xml768/$(basename $f) || exit 1; done) && grep -B12 "id=\"9108\"" $S/xml768/DialogConfirm.xml | grep -q "<top>736</top>"'
chk "T-4 text viewer scrolls (pagecontrol 60, default 60)" 'grep -q "<pagecontrol>60</pagecontrol>" $S/xml/DialogTextViewer.xml && grep -q "<defaultcontrol>60</defaultcontrol>" $S/xml/DialogTextViewer.xml && grep -q "<pagecontrol>60</pagecontrol>" $S/xml768/DialogTextViewer.xml'
chk "T-5 confirm text scrolls and has a scrollbar" 'grep -q "<pagecontrol>61</pagecontrol>" $S/xml/DialogConfirm.xml && grep -q "type=\"scrollbar\" id=\"61\"" $S/xml/DialogConfirm.xml && grep -q "<autoscroll [^>]*>!Control.HasFocus(61)</autoscroll>" $S/xml/DialogConfirm.xml'
chk "T-5 textbox scrollbars widen in touch mode" 'grep -A3 "type=\"scrollbar\" id=\"60\"" $S/xml/DialogTextViewer.xml | grep -q "content=\"Size_Width\" condition=\"\[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)\]\"><param name=\"v\" value=\"30\""'
chk "T-6 every task-bar button has a full-bar hit rect" 'test $(sed -n "/<include name=\"Chrome_Taskbar\">/,/<include name=\"Chrome_BackFace\">/p" $S/xml/Includes_Chrome.xml | grep -c "<hitrect ") -ge 7'
chk "T-6 touch title-bar boxes are wide, spaced, with hit rects" '(for n in 1 2 3; do grep -A2 "<include name=\"WinBox_${n}_Touch\">" $S/xml/Includes_Chrome.xml | grep -q "<hitrect " || exit 1; done) && test $(grep -c "<include content=\"WinBox\">" $S/xml/Includes_Chrome.xml) -ge 6'
chk "T-6 dialog button rows grow in touch mode" 'grep -q "DialogButton_XL" $S/xml/Includes_Dialogs.xml && grep -q "ConfirmRow_Top_XL" $S/xml/DialogConfirm.xml'
chk "T-7 every spin and settings slider grows in touch mode" '(for f in $S/xml/*.xml; do python3 -c "import sys,xml.etree.ElementTree as E;r=E.parse(sys.argv[1]).getroot();need={\"spincontrol\":\"SpinSize_XL\",\"spincontrolex\":\"SpinSize_XL\",\"sliderex\":\"SliderSize_XL\"};sys.exit(any(c.get(\"type\") in need and not any(i.get(\"content\")==need[c.get(\"type\")] for i in c.findall(\"include\")) for c in r.iter(\"control\")))" $f || exit 1; done) && grep -q "<include name=\"SpinSize_XL\">" $S/xml/Includes_Size.xml && grep -q "<include name=\"SliderSize_XL\">" $S/xml/Includes_Size.xml'
chk "T-7 text viewer / confirm textboxes are paged by a real scrollbar" '(for w in DialogTextViewer DialogConfirm; do for d in xml xml768; do python3 -c "import sys,xml.etree.ElementTree as E;r=E.parse(sys.argv[1]).getroot();sb={c.get(\"id\") for c in r.iter(\"control\") if c.get(\"type\")==\"scrollbar\"};tb=[c for c in r.iter(\"control\") if c.get(\"type\")==\"textbox\"];sys.exit(not tb or any((t.findtext(\"pagecontrol\") or \"\").strip() not in sb for t in tb))" $S/$d/$w.xml || exit 1; done; done)'
chk "T-9 context menu scrolls with a scrollbar" 'grep -q "<pagecontrol>997</pagecontrol>" $S/xml/DialogContextMenu.xml && grep -q "type=\"scrollbar\" id=\"997\"" $S/xml/DialogContextMenu.xml && grep -A1 "id=\"999\"" $S/xml/DialogContextMenu.xml | grep -q "<height>568</height>"'
chk "T-11 dialog fullscreen box closes dialogs first, never over a player" 'grep -A12 "<include name=\"WinBox_Max\">" $S/xml/Includes_Chrome.xml | grep -q "condition=\"\$PARAM\[close\]\">Dialog.Close(all,true)" && grep -A40 "<include name=\"Win_Boxes_dialog\">" $S/xml/Includes_Chrome.xml | grep -q "<param name=\"close\" value=\"true\" />" && grep -q "<expression name=\"ArthurCanShowPlayer\">Player.HasMedia + !Window.IsActive(fullscreenvideo)" $S/xml/Variables.xml && ! grep -q "<expression " $S/xml/Includes_Chrome.xml'
chk "T-12 touch Back floats when the task bar is hidden" 'grep -B2 "id=\"9107\"" $S/xml/Includes_Chrome.xml | grep -q "Skin.HasSetting(touchmode) + Skin.HasSetting(hidetaskbar)" || grep -B8 "id=\"9107\"" $S/xml/Includes_Chrome.xml | grep -q "Skin.HasSetting(touchmode) + Skin.HasSetting(hidetaskbar)"'
chk "D-1 task bar Power button in the nav chain, next to Start" 'grep -A8 "id=\"9106\"" $S/xml/Includes_Chrome.xml | grep -q "ActivateWindow(ShutdownMenu)" && grep -A8 "id=\"9100\"" $S/xml/Includes_Chrome.xml | grep -q "<onright>9106</onright>" && grep -A8 "id=\"9106\"" $S/xml/Includes_Chrome.xml | grep -q "<onleft>9100</onleft><onright>9101</onright>" && grep -A8 "id=\"9101\"" $S/xml/Includes_Chrome.xml | grep -q "<onleft>9106</onleft>" && grep -q "id=\"9106\"" $S/xml768/Home.xml'
chk "D-8 every clock label honours hideclock" 'python3 -c "import sys,xml.etree.ElementTree as E;r=E.parse(sys.argv[1]).getroot();sys.exit(any(\"System.Time\" in (c.findtext(\"label\") or \"\") and \"hideclock\" not in (c.findtext(\"visible\") or \"\") for c in r.iter(\"control\")))" $S/xml/Includes_Chrome.xml'
chk "D-9 _ only parks windows it can bring back" 'test $(grep -c "<onclick condition=\"\$EXP\[ArthurParkable\]\">Skin.SetString(arthur.min" $S/xml/Includes_Chrome.xml) -eq 4 && python3 -c "import re,sys;s=open(sys.argv[1]).read();a=re.findall(r\"<value condition=.Window.IsActive\((\w+)\).>\w+</value>\",s.split(\"name=\\\"ArthurWindowIcon\\\"\")[0]);e=re.findall(r\"Window.IsActive\((\w+)\)\",re.search(r\"<expression name=.ArthurParkable.>(.*?)</expression>\",s).group(1));sys.exit(not(a==e and \"musicplaylisteditor\" in a and \"screencalibration\" in a))" $S/xml/Variables.xml'
chk "V-7 settings sliders have textures" 'grep -A20 "default type=\"sliderex\"" $S/xml/Defaults.xml | grep -q "<texturesliderbar" && grep -A20 "default type=\"sliderex\"" $S/xml/Defaults.xml | grep -q "<textureslidernib "'
chk "V-13 task-bar mini player is not called Playlists" '! grep -A20 "id=\"9102\"" $S/xml/Includes_Chrome.xml | grep -q "LOCALIZE\[136\]" && grep -A20 "id=\"9102\"" $S/xml/Includes_Chrome.xml | grep -q "LOCALIZE\[31907\]"'
chk "C-6 toggle buttons show state, edit fields show focus" '! grep -A14 "default type=\"togglebutton\"" $S/xml/Defaults.xml | grep -q "<usealttexture>true" && grep -A14 "default type=\"togglebutton\"" $S/xml/Defaults.xml | grep -q "<alttexturenofocus" && grep -A12 "default type=\"edit\"" $S/xml/Defaults.xml | grep -q "<texturefocus border=\"2\" colordiffuse=\"select\">"'
chk "S-8 now-playing text and icon follow the media" '! grep -q "\] - \$INFO\[MusicPlayer" $S/xml/Variables.xml $S/xml/Includes_Chrome.xml && grep -q "\$INFO\[MusicPlayer.Artist,, - \]" $S/xml/Variables.xml && grep -A2 "name=\"NowPlayingVar\"" $S/xml/Variables.xml | grep -q "Player.HasGame" && grep -q "\$VAR\[NowPlayingIconVar\]" $S/xml/Includes_Chrome.xml'
chk "T-5 confirm scrollbar never navigates to a hidden button only" 'B=$(grep -A12 "type=\"scrollbar\" id=\"61\"" $S/xml/DialogConfirm.xml); (for d in left right down; do echo "$B" | grep -q "<on$d condition=\"Control.IsVisible(11)\">11</on$d><on$d condition=\"!Control.IsVisible(11)\">10</on$d>" || exit 1; done) && ! echo "$B" | grep -q "<on[a-z]*>11</on" && grep -q "<param name=\"up\" value=\"61\" />" $S/xml/DialogConfirm.xml && grep -A8 "<include name=\"Dialog_ButtonRow\">" $S/xml/Includes_Dialogs.xml | grep -q "<onup>\$PARAM\[up\]</onup>"'
chk "T-3/T-12 touch-only Back buttons can be left with the remote" 'grep -A8 "id=\"9108\"" $S/xml/Includes_Dialogs.xml | grep -q "<onup>\$PARAM\[up\]</onup><onleft>\$PARAM\[up\]</onleft>" && grep -A12 "<include name=\"Dialog_Dim\">" $S/xml/Includes_Dialogs.xml | grep -q "<param name=\"up\" default=\"9903\" />" && grep -A6 "id=\"9107\"" $S/xml/Includes_Chrome.xml | grep -q "<onup>\$PARAM\[up\]</onup><onleft>\$PARAM\[up\]</onleft>"'
chk "T-9 normal context menu keeps 360 px rows" 'grep -A5 "id=\"1000\"" $S/xml/DialogContextMenu.xml | grep -q "condition=\"!\[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)\]\"><param name=\"v\" value=\"360\""'
chk "D-1 Power sits next to Start, the player buttons after it" 'grep -B2 "id=\"9106\"" $S/xml/Includes_Chrome.xml | grep -q "<left>112</left>" && grep -B3 "id=\"9101\"" $S/xml/Includes_Chrome.xml | grep -q "<left>216</left>" && grep -B3 "id=\"9102\"" $S/xml/Includes_Chrome.xml | grep -q "<left>420</left>"'
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
