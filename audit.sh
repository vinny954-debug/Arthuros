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
OSDS="VideoOSD MusicOSD GameOSD"
chk "OSD is a bar on the bottom edge (V-3)"     'for r in xml xml768; do for f in $OSDS; do ! grep -q "centertop>50%" $S/$r/$f.xml && grep -q "<bottom>0</bottom>" $S/$r/$f.xml || exit 1; done; done'
chk "tap on the picture closes the OSD (V-3)"  'for f in $OSDS; do grep -A6 "id=\"9990\"" $S/xml/$f.xml | grep -q "Dialog.Close($f)" || exit 1; done'
chk "OSD Hide never leaves playback (V-3)"     'for r in xml xml768; do for f in $OSDS; do grep -A4 "id=\"9951\"" $S/$r/$f.xml | grep -q "Dialog.Close($f)" && ! grep -q "Action(FullScreen)" $S/$r/$f.xml || exit 1; done; done'
chk "OSD rewind/forward seek, not pause (V-4)" 'for f in VideoOSD MusicOSD; do grep -q "condition=\"!Player.Paused\">PlayerControl(Rewind)" $S/xml/$f.xml && grep -q "condition=\"!Player.Paused\">PlayerControl(Forward)" $S/xml/$f.xml && ! grep -A1 "<onclick>PlayerControl(Play)</onclick>" $S/xml/$f.xml | grep -q "PlayerControl(Rewind)\|PlayerControl(Forward)" || exit 1; done'
chk "OSD seek slider, timeshift too (V-5)"     'for f in VideoOSD MusicOSD PlayerControls; do grep -q "<action>seek</action>" $S/xml/$f.xml || exit 1; done && grep -q "<action>pvr.seek</action>" $S/xml/VideoOSD.xml'
chk "sliders are horizontal (Kodi default is vertical)" 'for r in xml xml768; do for f in VideoOSD MusicOSD GameOSD PlayerControls DialogSeekBar; do test $(grep -c "type=\"slider\"" $S/$r/$f.xml) -eq $(grep -A2 "type=\"slider\"" $S/$r/$f.xml | grep -c "<orientation>horizontal") || exit 1; done; done'
chk "OSD mute + volume slider (V-2)"           'for f in VideoOSD MusicOSD GameOSD PlayerControls; do grep -q "<action>volume</action>" $S/xml/$f.xml && grep -q "<onclick>Mute</onclick>" $S/xml/$f.xml || exit 1; done'
chk "seek bar opens by itself, not over the OSD (V-6)" 'grep -q "^  <visible>.*Player.HasPerformedSeek(3)" $S/xml/DialogSeekBar.xml && grep -q "^  <visible>!\[Window.IsVisible(videoosd) | Window.IsVisible(musicosd)" $S/xml/DialogSeekBar.xml && grep -q "type=\"slider\" id=\"401\"" $S/xml768/DialogSeekBar.xml'
chk "bookmarks: labelled, Clear asks, video visible (V-8)" 'f=$S/xml/VideoOSDBookmarks.xml; grep -q "LOCALIZE\[294\]" $f && grep -q "SendClick(videobookmarks,3)" $f && grep -q "type=\"panel\" id=\"11\"" $f && ! grep -q "Chrome_Desktop\|value=\"VideoOSDBookmarks\"\|>VideoOSDBookmarks<" $f'
chk "live TV: channels, guide, teletext, RDS, record state (V-9)" 'f=$S/xml/VideoOSD.xml; grep -q "ActivateWindow(PVROSDChannels)" $f && grep -q "ActivateWindow(PVRChannelGuide)" $f && grep -q "ActivateWindow(Teletext)" $f && grep -q "PVR.CanRecordPlayingChannel" $f && grep -q "ActivateWindow(PVRRadioRDSInfo)" $S/xml/MusicOSD.xml && grep -q "PVR.IsRecordingPlayingChannel" $S/xml/Variables.xml'
chk "Play/Pause shows its state, glyphs never dim (V-12)" 'for f in VideoOSD MusicOSD GameOSD PlayerControls; do grep -A12 "type=\"radiobutton\" id=\"602\"" $S/xml/$f.xml | grep -q "icons24/pause.png" && ! grep -q "colordiffuse=\"textdim\">icons" $S/xml/$f.xml || exit 1; done && grep -q "<selected>Playlist.IsRandom</selected>" $S/xml/PlayerControls.xml'
chk "OSD transport keeps keyboard navigation (no button-in-group)" 'for f in $OSDS PlayerControls; do ! grep -q "type=\"group\" id=\"960[0-7]\"" $S/xml/$f.xml || exit 1; done'
chk "OSD Playlist opens the play queue (V-13)" '! grep -q "ActivateWindow(PlayerControls)" $S/xml/VideoOSD.xml $S/xml/MusicOSD.xml && grep -q "ActivateWindow(VideoPlaylist)" $S/xml/VideoOSD.xml && grep -q "ActivateWindow(MusicPlaylist)" $S/xml/MusicOSD.xml && grep -q "ActivateWindow(MusicPlaylist)" $S/xml/PlayerControls.xml'
chk "info dialogs have content and Close (V-14)" 'grep -q "VideoPlayer.Plot" $S/xml/DialogFullScreenInfo.xml && grep -q "Dialog.Close(FullscreenInfo)" $S/xml/DialogFullScreenInfo.xml && grep -q "Player.Process(videodecoder)" $S/xml/DialogPlayerProcessInfo.xml && for i in 10 21 22 70; do grep -q "id=\"$i\"" $S/xml/DialogPVRRadioRDSInfo.xml || exit 1; done && grep -q "ActivateWindow(FullscreenInfo)" $S/xml/VideoOSD.xml'
chk "game OSD: controllers, ports, players (V-17)" 'f=$S/xml/GameOSD.xml; grep -q "ActivateWindow(GameControllers)" $f && grep -q "ActivateWindow(GamePorts)" $f && grep -q "ActivateWindow(GameAgents)" $f'
chk "fullscreen video: zoom readout, buffering, no videowindow (V-20-22)" 'for r in xml xml768; do f=$S/$r/VideoFullScreen.xml; ! grep -q "Player.ShowCodec\|videowindow" $f && grep -q "Control.IsVisible(10)" $f && grep -q "Player.Caching + Integer.IsGreater(Player.CacheLevel,0)" $f || exit 1; done'
chk "OSD default focus forced to Play (V-23)"  'for f in $OSDS; do grep -q "<defaultcontrol always=\"true\">602</defaultcontrol>" $S/xml/$f.xml || exit 1; done'
chk "game OSD explains the pause (V-24)"       'grep -q "id=\"1101\"" $S/xml/GameOSD.xml && grep -q "LOCALIZE\[35236\]" $S/xml/GameOSD.xml'
chk "OSD add-on settings find the add-on (B-5)" 'test -f $S/scripts/addonsettings.py && grep -q "RunScript(special://skin/scripts/addonsettings.py)" $S/xml/VideoOSD.xml && grep -q "String.StartsWith(Player.FilenameAndPath,plugin://)" $S/xml/MusicOSD.xml'
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
