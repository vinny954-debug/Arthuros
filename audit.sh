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
R="$(dirname "$0")/README.md"
chk "changelog leads with this version" 'head -1 $S/changelog.txt | grep -qx "v$VER"'
chk "README names this version"         'grep -q "Current version: $VER\*\*" "$R" && ! grep -o "skin.arthuros-[0-9][0-9.]*[0-9]\.zip" "$R" | grep -vqx "skin.arthuros-$VER.zip"'
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
chk "now-playing recall kept (music branch of 9101)" 'grep -A8 "id=\"9101\"" $S/xml/Includes_Chrome.xml | grep -q "<onclick condition=\"!Player.HasVideo + !Player.HasGame\">ActivateWindow(Visualisation)</onclick>" && grep -A8 "id=\"9101\"" $S/xml768/Home.xml | grep -q "<onclick condition=\"!Player.HasVideo + !Player.HasGame\">ActivateWindow(Visualisation)</onclick>"'
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
chk "buffering box: no id-less child, Kodi hides id 0 at init (V-21)" 'for r in xml xml768; do g=$(sed -n "/<control type=\"group\" id=\"1\">/,/<\/controls>/p" $S/$r/VideoFullScreen.xml); n=$(echo "$g" | grep -c "<control "); test $n -ge 4 && test $(echo "$g" | grep "<control " | grep -c "id=\"1\"") -eq $n && ! echo "$g" | grep -q "<include" || exit 1; done'
chk "bookmarks over playback: no title-bar boxes, own Close" 'grep -q "name=\"boxes\" value=\"none\"" $S/xml/VideoOSDBookmarks.xml && for r in xml xml768; do f=$S/$r/VideoOSDBookmarks.xml; ! grep -q "id=\"990[12]\"\|ActivateWindow(Home)\|Action(FullScreen)" $f && grep -A4 "id=\"9995\"" $f | grep -q "Dialog.Close(VideoBookmarks)" || exit 1; done'
chk "video OSD text row fits 1008 px (teletext/menu, add-on/live)" 'f=$S/xml/VideoOSD.xml; grep -q "VideoPlayer.HasTeletext + !VideoPlayer.HasMenu" $f && grep -A6 "id=\"9960\"" $f | grep -q "!VideoPlayer.Content(LiveTV) + \[" && grep -A6 "id=\"9960\"" $S/xml/MusicOSD.xml | grep -q "!MusicPlayer.Content(LiveTV) + \["'
chk "seek bar stays off teletext / subtitle search / CMS" 'for r in xml xml768; do for w in teletext subtitlesearch osdcmssettings; do grep "^  <visible>!\[" $S/$r/DialogSeekBar.xml | grep -q "Window.IsVisible($w)" || exit 1; done; done'
chk "OSD state label clear of the title (right of x 921)" 'for r in xml xml768; do for f in $OSDS; do grep -B1 -A3 "<left>922</left><top>3</top><width>96</width>" $S/$r/$f.xml | grep -q "OSDStateVar" && ! grep -q "<left>874</left><top>3</top>" $S/$r/$f.xml || exit 1; done; done'
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
chk "fullscreen video: zoom readout, buffering, no videowindow (V-20-22)" 'for r in xml xml768; do f=$S/$r/VideoFullScreen.xml; ! grep -q "Player.ShowCodec\|videowindow" $f && grep -q "type=\"group\" id=\"0\"" $f && grep -q "Player.Caching + Integer.IsGreater(Player.CacheLevel,0)" $f || exit 1; done'
chk "OSD default focus forced to Play (V-23)"  'for f in $OSDS; do grep -q "<defaultcontrol always=\"true\">602</defaultcontrol>" $S/xml/$f.xml || exit 1; done'
chk "game OSD explains the pause (V-24)"       'grep -q "id=\"1101\"" $S/xml/GameOSD.xml && grep -q "LOCALIZE\[35236\]" $S/xml/GameOSD.xml'
chk "OSD add-on settings find the add-on (B-5)" 'test -f $S/scripts/addonsettings.py && grep -q "RunScript(special://skin/scripts/addonsettings.py)" $S/xml/VideoOSD.xml && grep -q "String.StartsWith(Player.FilenameAndPath,plugin://)" $S/xml/MusicOSD.xml'
:
:
# ===== P2 other playback =====
chk "V-1 picture viewer has no full-screen cover" '! grep -q "bar_dgrey" $S/xml/SlideShow.xml $S/xml768/SlideShow.xml'
chk "V-11 picture viewer touch strip + timer" '(for r in xml xml768; do grep -q "Skin.TimerStart(arthur_slidebar)" $S/$r/SlideShow.xml && grep -q "Action(Stop)" $S/$r/SlideShow.xml && grep -q "Action(NextPicture)" $S/$r/SlideShow.xml && grep -q "<name>arthur_slidebar</name>" $S/$r/Timers.xml || exit 1; done)'
chk "V-11 picture viewer error label id 10" '(for r in xml xml768; do grep -q "type=\"label\" id=\"10\"" $S/$r/SlideShow.xml || exit 1; done)'
chk "V-11 strip backstop: near-miss taps keep the strip" '(for r in xml xml768; do grep -q "type=\"button\" id=\"9806\"" $S/$r/SlideShow.xml || exit 1; done)'
chk "V-11 Paused only for a running slideshow" '(for r in xml xml768; do ! grep -q "<visible>Slideshow.IsPaused</visible>\|| Slideshow.IsPaused</visible>" $S/$r/SlideShow.xml && test $(grep -c "\[Slideshow.IsActive + Slideshow.IsPaused\]" $S/$r/SlideShow.xml) -eq 2 || exit 1; done)'
chk "V-16 channel OSD rows show number/programme" '(for r in xml xml768; do f=$S/$r/DialogPVRChannelsOSD.xml; grep -q "ListItem.ChannelNumberLabel" $f && grep -q "<info>ListItem.Progress</info>" $f && grep -q "Action(NextChannelGroup)" $f && ! grep -q "Dialog_Heading" $f || exit 1; done)'
chk "V-16 channel OSD fits Extra large (number column, footer)" '(for r in xml xml768; do f=$S/$r/DialogPVRChannelsOSD.xml; grep -q "<width>76</width><height>64</height>" $f && grep -A1 "type=\"label\" id=\"2\"" $f | grep -q "<height>30</height>" || exit 1; done)'
chk "V-18 background progress: corner, no dim" '(for r in xml xml768; do f=$S/$r/DialogExtendedProgressBar.xml; ! grep -q "Dialog_Dim\|centertop" $f && grep -q "Window.IsVisible(fullscreenvideo)" $f || exit 1; done)'
chk "V-19 visualisation has a no-add-on screen" 'grep -q "!Visualisation.Enabled" $S/xml/MusicVisualisation.xml && grep -q "Player.Art(fanart)" $S/xml/MusicVisualisation.xml'
chk "S-8 visualisation: no bare artist dash" '! grep -qF "] - \$INFO[MusicPlayer" $S/xml/MusicVisualisation.xml $S/xml768/MusicVisualisation.xml'
chk "K-6 visualisation control is id 2" 'grep -q "type=\"visualisation\" id=\"2\"" $S/xml/MusicVisualisation.xml && grep -q "type=\"visualisation\" id=\"2\"" $S/xml768/MusicVisualisation.xml'
chk "V-25 busy dialog: Cancel, no dead progress" '(for r in xml xml768; do f=$S/$r/DialogBusy.xml; ! grep -q "Busy.Progress" $f && grep -q "<onclick>Action(Back)</onclick>" $f || exit 1; done)'
chk "V-25 busy Cancel: per instance, never focused by default" '(for r in xml xml768; do f=$S/$r/DialogBusy.xml; ! grep -q "defaultcontrol\|Window.IsActive(busydialog)" $f && grep -q "<visible>Window.Is(busydialog)</visible>" $f && grep -q "<visible>!Window.Is(busydialog)</visible>" $f || exit 1; done)'
chk "V-26 game pictures: title, description, Label2" '(for r in xml xml768; do f=$S/$r/DialogSelect.xml; grep -q "Control.GetLabel(10810)" $f && grep -q "game.videofilterdescription)\]</label>" $f && test $(sed -n "/<control type=\"panel\" id=\"10811\">/,/<control type=\"textbox\" id=\"10812\">/p" $f | grep -c "<label>\$INFO\[ListItem.Label2\]</label>") -eq 4 || exit 1; done)'
chk "C-1 select tick follows the palette" '(for r in xml xml768; do f=$S/$r/DialogSelect.xml; ! grep -q "check_on.png" $f && test $(grep -c "<texture colordiffuse=\"text\(inv\)\?\">icons24/tick.png</texture>" $f) -eq 8 || exit 1; done) && test -f $S/media/icons24/tick.png'
chk "C-1 select: focused labels keep textinv when selected" 'python3 -c "
import re,sys
s=open(sys.argv[1]).read()
bad=[l for fl in re.findall(r\"<focusedlayout.*?</focusedlayout>\",s,re.S) for l in re.findall(r\"<control type=.label.>.*?</control>\",fl,re.S) if \"textinv\" in l and \"<selectedcolor>textinv\" not in l]
sys.exit(1 if bad or s.count(\"<visible>ListItem.IsSelected</visible>\")<8 else 0)" $S/xml/DialogSelect.xml'
chk "C-1 palettecheck reports marked on select" 'python3 $(dirname $S)/palettecheck.py | grep -q "marked on select"'
chk "C-4 unfocused selected rows stay readable" 'python3 -c "
import re,sys
bad=0
for f in sys.argv[1:]:
  for fl in re.findall(r\"<focusedlayout.*?</focusedlayout>\",open(f).read(),re.S):
    if re.search(r\"fill.png</texture><visible>Control.HasFocus\",fl):
      for l in re.findall(r\"<control type=.label.>.*?</control>\",fl,re.S):
        if \"textinv\" in l and \"Control.HasFocus\" not in l: bad=1
sys.exit(bad)" $S/xml/DialogSubtitles.xml $S/xml/Includes_Games.xml $S/xml/DialogPVRChannelsOSD.xml'
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
chk "no unused skin strings"                     '( for i in $(sed -n "s/^msgctxt \"#\([0-9]*\)\"/\1/p" $S/language/resource.language.en_gb/strings.po); do case $i in 3191[3-6]) continue;; esac; grep -rqs "$i" $S/xml $S/scripts $S/fonts $S/addon.xml || { echo "unused $i"; exit 1; }; done )'
:
:
# ===== P4 TV guide =====
chk "guide has a real epggrid 50 in <views>" 'for d in xml xml768; do python3 -c "
import sys; from lxml import etree
r = etree.parse(sys.argv[1]).getroot()
assert (r.findtext(\"views\") or \"\").strip() == \"50\"
g = r.xpath(\"//control[@type=\\\"epggrid\\\"][@id=\\\"50\\\"]\")[0]
assert int(g.findtext(\"left\")) >= 0 and int(g.findtext(\"top\")) >= 0
for t in (\"channellayout\", \"focusedchannellayout\", \"rulerlayout\", \"itemlayout\", \"focusedlayout\"):
    assert len(g.findall(t)) == 2 and \"touchmode\" in (g.find(t).get(\"condition\") or \"\"), t
assert g.findtext(\"pagecontrol\") == \"60\" and r.xpath(\"//control[@type=\\\"scrollbar\\\"][@id=\\\"60\\\"]\")
assert not r.xpath(\"//control[@type=\\\"epggrid\\\"][@id!=\\\"50\\\"]\")
" $S/$d/MyPVRGuide.xml || exit 1; done'
chk "guide title is Guide, not Channel"  'for d in xml xml768; do grep -q "\$LOCALIZE\[19069\]" $S/$d/MyPVRGuide.xml && ! grep -q "LOCALIZE\[19029\]" $S/$d/MyPVRGuide.xml || exit 1; done'
chk "guide strip: group, now, navigate, options" 'for d in xml xml768; do for a in "id=\"28\"" "EpgGridControl(CurrentProgramme)" "ActivateWindow(PVRGuideControls)" "Action(ContextMenu)" "Action(PageDown)"; do grep -q "$a" $S/$d/MyPVRGuide.xml || exit 1; done; done'
chk "guide shows the channel group name (label 30) in the title bar" 'for d in xml xml768; do grep -q "Control.GetLabel(30)" $S/$d/MyPVRGuide.xml || exit 1; done'
chk "guide programme title is id 1 in every programme layout (hidden in tiny cells)" 'for d in xml xml768; do python3 -c "
import sys; from lxml import etree
g = etree.parse(sys.argv[1]).getroot().xpath(\"//control[@type=\\\"epggrid\\\"]\")[0]
ls = g.findall(\"itemlayout\") + g.findall(\"focusedlayout\")
assert len(ls) == 4
for l in ls:
    assert l.xpath(\"control[@type=\\\"label\\\"][@id=\\\"1\\\"]\"), l.get(\"condition\")
" $S/$d/MyPVRGuide.xml || exit 1; done'
chk "guide controls: on the bottom edge, compact in normal mode, tap catchers reach every screen edge" 'for d in xml xml768; do python3 -c "
import sys; from lxml import etree
r = etree.parse(sys.argv[1]).getroot()
H = 768 if sys.argv[1].endswith(\"xml768/DialogPVRGuideControls.xml\") else 600
box = r.find(\"controls\").find(\"control\")
assert box.findtext(\"bottom\") == \"0\" and box.findtext(\"top\") is None
bh, bw = int(box.findtext(\"height\")), int(box.findtext(\"width\"))
bx, by = (1024 - bw) // 2, H - bh
cs = {c.get(\"id\"): c for c in box.xpath(\"control[@type=\\\"button\\\"]\") if c.get(\"id\", \"\").startswith(\"997\") and c.get(\"id\") != \"9970\"}
assert sorted(cs) == [\"9971\", \"9972\", \"9973\", \"9974\"], sorted(cs)
def rect(c):
    l, t, w, h = (int(c.findtext(k)) for k in (\"left\", \"top\", \"width\", \"height\"))
    return bx + l, by + t, bx + l + w, by + t + h
L, R, T, B = (rect(cs[i]) for i in (\"9971\", \"9972\", \"9973\", \"9974\"))
assert L[0] <= 0 and L[1] <= 0 and L[3] >= H and L[2] == bx
assert R[2] >= 1024 and R[1] <= 0 and R[3] >= H and R[0] == bx + bw
assert T[1] <= 0 and T[3] == by
assert all(c.findtext(\"onclick\") == \"Action(close)\" for c in cs.values())
boxes = box.xpath(\"include[@content=\\\"Dialog_Box\\\"]\")
hs = sorted(int(i.xpath(\"param[@name=\\\"height\\\"]/@value\")[0]) for i in boxes)
assert len(boxes) == 2 and hs[1] == bh and hs[0] < bh - 30, hs
assert B[1] == by + hs[0] and B[3] >= H and \"!\" in cs[\"9974\"].findtext(\"visible\")
" $S/$d/DialogPVRGuideControls.xml || exit 1; done'
chk "guide controls: 12 jumps, every button labelled" 'for d in xml xml768; do python3 -c "
import sys; from lxml import etree
r = etree.parse(sys.argv[1]).getroot()
bs = r.xpath(\"//control[@type=\\\"button\\\" or @type=\\\"radiobutton\\\"][not(starts-with(@id,\\\"99\\\"))]\")
assert len(bs) == 12
for b in bs:
    assert (b.findtext(\"label\") or \"\").strip() and b.findtext(\"onclick\"), b.get(\"id\")
args = {b.findtext(\"onclick\") for b in bs}
want = \"FirstProgramme -12 CurrentProgramme +12 LastProgramme SelectDate FirstChannel PlayingChannel LastChannel PreviousGroup NextGroup SelectGroup\"
assert args == {\"PVR.EpgGridControl(%s)\" % a for a in want.split()}, args
assert r.xpath(\"//onclick[text()=\\\"Action(close)\\\"]\")
" $S/$d/DialogPVRGuideControls.xml || exit 1; done'
:
:
# ===== P5 touch chrome & controls =====
chk "V-2b volume button never traps the remote with the task bar hidden; no stuck pressed look after a tap" 'for d in xml xml768; do F=$S/$d/Includes_Chrome.xml; grep -A12 "type=\"button\" id=\"9100\"" $F | grep -q "<ondown condition=\"Skin.HasSetting(hidetaskbar)\">9107</ondown>" && grep -A8 "type=\"button\" id=\"9107\"" $F | grep -q "<ondown>\$PARAM\[up\]</ondown>" && grep -B6 "type=\"button\" id=\"9109\"" $F | grep -q "<visible>Control.HasFocus(9109) + !\$EXP\[ArthurNoPointer\]</visible>" && grep -A6 "type=\"button\" id=\"9109\"" $F | grep -q "<texturefocus>-</texturefocus>" && grep -q "<expression name=\"ArthurNoPointer\">Skin.HasSetting(touchmode) + !Skin.HasSetting(touch.pointer.show)" $S/$d/Variables.xml || exit 1; done; for w in $(grep -l "<include>Chrome_Menubar</include>" $S/xml/*.xml); do b=$(basename $w); test "$b" = LoginScreen.xml && continue; grep -q "<include content=\"Chrome_Taskbar\"><param name=\"up\" value=\"[0-9]*\" /></include>" $w || exit 1; done'
chk "S-9 task-bar Start uses Kodi's string 335" '! grep -q "<label>Start</label>" $S/xml/Includes_Chrome.xml && test $(grep -c "<label>\$LOCALIZE\[335\]</label>" $S/xml/Includes_Chrome.xml) -eq 2'
chk "V-2 menu-bar volume opens the mini player, not on the login screen" 'B=$(sed -n "/<include name=\"Chrome_Menubar\">/,/<\/include>/p" $S/xml/Includes_Chrome.xml | grep -A10 "type=\"button\" id=\"9109\""); echo "$B" | grep -q "<onclick>ActivateWindow(PlayerControls)</onclick>" && echo "$B" | grep -q "<visible>!Window.IsVisible(loginscreen)</visible>" && echo "$B" | grep -q "<ondown>9100</ondown>" && grep -q "id=\"9109\"" $S/xml768/Home.xml && grep -q "<action>volume</action>" $S/xml/PlayerControls.xml && grep -q "<onclick>Mute</onclick>" $S/xml/PlayerControls.xml'
chk "C-2 dialog _ box cannot open Home over the login screen (DialogConfirm/DialogSelect)" 'grep -A40 "<include name=\"Win_Boxes_dialog\">" $S/xml/Includes_Chrome.xml | grep -q "<onclick condition=\"!Window.IsVisible(loginscreen)\">ActivateWindow(Home)</onclick>" && (for d in xml768; do for w in DialogConfirm DialogSelect; do python3 -c "
import re,sys
from lxml import etree
G=\"!window.isvisible(loginscreen)\"
r=etree.parse(sys.argv[1]).getroot()
def ok(a):
    if G in (a.get(\"condition\") or \"\").replace(\" \",\"\").lower(): return True
    c=a.getparent()
    while c is not None:
        if c.tag==\"control\" and any(G in (v.text or \"\").replace(\" \",\"\").lower() for v in c.findall(\"visible\")): return True
        c=c.getparent()
    return False
bad=[a for a in r.iter() if isinstance(a.tag,str) and a.tag.startswith(\"on\") and re.search(r\"(Activate|Replace)Window\((?!ShutdownMenu)\",a.text or \"\",re.I) and not ok(a)]
sys.exit(1 if bad else 0)" $S/$d/$w.xml || exit 1; done; done)'
chk "X-7 pointer obeys touch.pointer.show/hide at once" 'test $(grep -c "<value condition=\"Skin.HasSetting(touchmode) + !Skin.HasSetting(touch.pointer.show) + \[Skin.HasSetting(touch.pointer.hide) | String.IsEmpty(Window(Home).Property(arthuros.mouse))\]\"></value>" $S/xml/Variables.xml) -eq 2'
chk "V-2 sliders lie flat by default (Kodi defaults to vertical)" 'grep -A8 "<default type=\"slider\">" $S/xml/Defaults.xml | grep -q "<orientation>horizontal</orientation>" && grep -A8 "<default type=\"slider\">" $S/xml768/Defaults.xml | grep -q "<orientation>horizontal</orientation>"'
chk "T-6 media toolbar buttons get a 34 px touch hit rect" 'python3 -c "
import sys
from lxml import etree
r=etree.parse(sys.argv[1]).getroot()
g=r.xpath(\"//control[@type=\x27grouplist\x27][@id=\x279490\x27]\")[0]
b=[c for c in g if c.tag==\"control\"]
sys.exit(not b or any(not c.xpath(\"include[@content=\x27Size_Hit\x27][@condition=\x27Skin.HasSetting(touchmode)\x27]/param[@name=\x27h\x27][@value=\x2734\x27]\") for c in b))" $S/xml/Includes_Media.xml && grep -q "<include name=\"Size_Hit\">.*<hitrect x=\"\$PARAM\[x\]\" y=\"\$PARAM\[y\]\" w=\"\$PARAM\[w\]\" h=\"\$PARAM\[h\]\" />" $S/xml/Includes_Size.xml && grep -q "Size_Hit" $S/xml768/Includes_Media.xml'
chk "T-8 heading comment names the keyboard (311) and slider (10) ids" 'grep -q "label 311" $S/xml/Includes_Dialogs.xml && grep -q "label 10 (CONTROL_HEADING" $S/xml/Includes_Dialogs.xml'
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
chk "T-11 dialog fullscreen box closes dialogs first, never over a player" 'grep -A12 "<include name=\"WinBox_Max\">" $S/xml/Includes_Chrome.xml | grep -q "condition=\"\$PARAM\[close\]\">Dialog.Close(all,true)" && grep -A60 "<include name=\"Win_Boxes_dialog\">" $S/xml/Includes_Chrome.xml | grep -q "<param name=\"close\" value=\"true\" />" && grep -q "<expression name=\"ArthurCanShowPlayer\">Player.HasMedia + !Window.IsActive(fullscreenvideo)" $S/xml/Variables.xml && ! grep -q "<expression " $S/xml/Includes_Chrome.xml'
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
D="$(dirname "$0")"
chk "build.sh: one command per line (set -e sees every step)" '! grep -v "^[[:space:]]*#" $D/build.sh | grep -q "&&"'
chk "build.sh checks both layouts' text fit" 'grep -q "RES=xml768 python3 textfit.py" $D/build.sh'
chk "installer enables a copied skin in Kodi's add-on DB" 'grep -q "UPDATE installed SET enabled=1" $D/install-arthuros.sh && grep -q "My add-ons > Look and feel > Skin" $D/install-arthuros.sh'
chk "installer works without sudo and restarts Kodi on failure" 'grep -q "\[ \"\$(id -u)\" -eq 0 \] && SUDO=" $D/install-arthuros.sh && grep -q "trap restore EXIT" $D/install-arthuros.sh && ! grep -q "sudo systemctl" $D/install-arthuros.sh && grep -q "kodi.service kodi-gbm.service" $D/install-arthuros.sh'
chk "installer copies beside addons before replacing" 'grep -q "arthuros-new" $D/install-arthuros.sh'
chk "netbt: failed open Wi-Fi says why"  'grep -A1 "if not net.get(\"secure\"):" $S/scripts/netbt.py | grep -q "dialog.ok"'
chk "netbt: denied fix names Kodi's user, polkit rule" 'grep -q "pwd.getpwuid(os.getuid())" $S/scripts/netbt.py && grep -q "50-arthuros-nm.rules" $S/scripts/netbt.py $D/install-arthuros.sh && ! grep -q "usermod -aG netdev \$USER" $S/scripts/netbt.py'
chk "mousewatch skips touch controllers' mouse nodes" 'grep -q "ABS_MT_POSITION_X = 0x35" $S/scripts/mousewatch.py && grep -q "INPUT_PROP_DIRECT" $S/scripts/mousewatch.py'
chk "mousewatch honours the touch.pointer.show/hide settings, logs why" 'grep -q "Skin.HasSetting(touch.pointer.show)" $S/scripts/mousewatch.py && grep -q "Skin.HasSetting(touch.pointer.hide)" $S/scripts/mousewatch.py && grep -q "xbmc.LOGINFO" $S/scripts/mousewatch.py'
chk "skin XML uses only the pointer settings mousewatch reads" '! grep -rhoE "touch\.pointer[A-Za-z0-9_.]*" $S/xml/ | grep -vxE "touch\.pointer\.(show|hide)"'
chk "mousewatch header doesn't claim a Startup start that isn't there" 'grep -q "mousewatch.py" $S/xml/Startup.xml || ! grep -q "Started from Startup" $S/scripts/mousewatch.py'
chk "installer probes Kodi's home as Kodi's user (0700 homes)" 'grep -q "if as_kodi test -d \"\$ADDONS/skin.arthuros\"" $D/install-arthuros.sh && grep -q "as_kodi sh -c .ls \"\$1\"/Addons" $D/install-arthuros.sh && grep -q "! as_kodi test -e \"\$ADDONS/skin.arthuros\" && as_kodi test -d \"\$BK\"" $D/install-arthuros.sh && ! grep -qE "^[[:space:]]*(if|elif) \[ !? ?-[de] \"\$(ADDONS|DB|KHOME)" $D/install-arthuros.sh'
chk "installer never moves the new skin into an old folder" 'grep -B4 "^as_kodi mv \"\$STAGE\" \"\$ADDONS/skin.arthuros\"" $D/install-arthuros.sh | grep -q "if as_kodi test -e \"\$ADDONS/skin.arthuros\""'
chk "installer looks for the polkit rule with sudo (rules.d is 0700)" 'grep -q "! \$SUDO test -e \"\$RULE\"" $D/install-arthuros.sh && ! grep -q "\[ ! -e \"\$RULE\" \]" $D/install-arthuros.sh'
chk "validate.py fails on any warning not in KNOWN_WARNINGS" 'grep -q "if x not in KNOWN_WARNINGS:" $D/validate.py && grep -A1 "if x not in KNOWN_WARNINGS:" $D/validate.py | grep -q "errors.append"'
chk "Kodi tables from Omega ship"        'grep -q "^skin.setstring	1$" $D/vendor/kodi/builtins.txt && grep -q "^parentdir$" $D/vendor/kodi/actions.txt && grep -q "^favouritesbrowser	10060$" $D/vendor/kodi/windowids.txt && grep -q "^player.hasmedia$" $D/vendor/kodi/infolabels.txt && test $(wc -l < $D/windownames.txt) -ge 137'
chk "validate.py checks builtins, windows, infos, \$VAR, focus" 'grep -q "builtins.txt" $D/validate.py && grep -q "windownames.txt" $D/validate.py && grep -q "infolabels.txt" $D/validate.py && grep -q "expressions" $D/validate.py && ! grep -q "\"9490\",\"9500\"" $D/validate.py'
chk "validate + textfit pass for both layouts" '(cd "$D" && python3 validate.py && RES=xml768 python3 validate.py && python3 textfit.py && RES=xml768 python3 textfit.py)'
:
:
# ===== P10 fonts =====
chk "Unicode fontset in fonts/Unicode.xml only"  'grep -q "<fontset id=\"Unicode\" idloc=\"31895\"" $S/fonts/Unicode.xml && ! grep -q "id=\"Unicode\"" $S/xml/Font.xml $S/xml768/Font.xml'
chk "Unicode fontset name string 31895 exists"   'grep -A1 "^msgctxt \"#31895\"" $S/language/resource.language.en_gb/strings.po | grep -q "^msgid \"Unicode"'
chk "Unicode fontset uses only Kodi's arial.ttf" 'grep -q "<filename>arial.ttf</filename>" $S/fonts/Unicode.xml && ! grep "<filename>" $S/fonts/Unicode.xml | grep -qv "<filename>arial.ttf</filename>" && ! ls $S/fonts | grep -qi "^arial"'
chk "Unicode fontset has Default's font names"   'test "$(sed -n "/fontset id=\"Default\"/,/<\/fontset>/p" $S/xml/Font.xml | grep -o "<name>[^<]*</name>" | sort)" = "$(grep -o "<name>[^<]*</name>" $S/fonts/Unicode.xml | sort)"'
chk "every font the windows use is in Unicode"   '( for n in $(cat $S/xml/*.xml $S/xml768/*.xml | grep -o "<font>[^<]*</font>" | sed "s/<[^>]*>//g" | sort -u); do grep -q "<name>$n</name>" $S/fonts/Unicode.xml || exit 1; done )'
chk "Tamzen faces draw ’ ‘ “ ” – — … • (C-5)"   'python3 -c "import glob,sys;from PIL import ImageFont as F;fs=glob.glob(\"'"$S"'/fonts/Tamzen*.ttf\");sys.exit(len(fs)!=8 or any(F.truetype(f,s).getmask(c).getbbox() is None or F.truetype(f,s).getlength(c)!=F.truetype(f,s).getlength(\"x\") for f in fs for s in (16,32) for c in \"’‘“”–—…•·\"))"'
chk "Unicode line height <= Tamzen's at 1x and 2x" 'python3 -c "import re,sys;d=dict(re.findall(r\"<name>(\w+)</name><filename>Tamzen[^<]*</filename><size>(\d+)\",open(\"'"$S"'/xml/Font.xml\").read().split(\"</fontset>\")[0]));u=re.findall(r\"<name>(\w+)</name><filename>arial.ttf</filename><size>(\d+)</size>(?:<style>[^<]*</style>)?(?:<linespacing>([\d.]+)</linespacing>)?\",open(\"'"$S"'/fonts/Unicode.xml\").read());sys.exit(len(u)!=len(d) or any(float(l or 1)*int(2384*int(z)*k/2048+.5)/k>int(d[n]) for n,z,l in u for k in (1,2)))"'
chk "textfit measures fonts/*.xml (arial table)"  'grep -q "\"fonts\", \"\*.xml\"" $S/../textfit.py && python3 -c "import json;assert json.load(open(\"'"$S"'/../vendor/kodi/arial-advances.json\"))[\"adv\"][\"87\"]>0"'
chk "fonts help string 31896 names the fontset"  'grep -A1 "^msgctxt \"#31896\"" $S/language/resource.language.en_gb/strings.po | grep -q "Unicode (all alphabets)"'
:
:
[ $fail -eq 0 ] && echo "all good" || echo "AUDIT FAILED"
exit $fail
