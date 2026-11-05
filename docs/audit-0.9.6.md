# ArthurOS 0.9.6 audit

Date: 2026-11-05. Covers the 0.9.6 source as uploaded; no skin files were changed.

## How this was checked

- Ten reviewers each took one area: video OSD, other playback, touch-only use, text and strings, the control ids Kodi depends on, links and references, layout, desktop, browsers, and scripts and tooling.
- Every claim about Kodi behaviour was checked against the Kodi **Omega** source on GitHub and Estuary, not from memory.
- Every finding then went to a skeptical verifier whose job was to refute it. High and critical findings got two verifiers. A completeness pass then looked for anything missed.
- Layout was checked with `preview.py` renders only. **Nothing here has been tested on the Pi.** Items that depend on hardware say so.

**Result: 92 findings stand** (critical 2, high 21, medium 33, low 33, cosmetic 3). Two were refuted (see the end).

Severity: **critical** = the feature is unusable or you get stuck; **high** = an important function is missing or broken; **medium** = it works but is wrong or confusing; **low** = minor.

## Your three reports

| You saw | Cause | Finding |
|---|---|---|
| No volume control while a video plays | The video and music OSDs have no volume control. The menu-bar volume only displays the level. The volume bar is a readout Kodi opens only after a key press. The one touch path is OSD > Audio > Volume, and its slider is invisible (a 16 px strip with no texture). | V-2, V-7 |
| A tap during a video puts the play bar in the middle of the screen | `genwindows.osd_window()` builds the OSD with the generic `dialog()`, which always centres it at 50%/50%. | V-3 |
| Hard to close it | The OSD is a modal dialog, so a tap on the picture is swallowed. Only a long-press or two-finger tap closes it. Its **Close** button runs `Action(FullScreen)`, which leaves playback and drops you into the menus. The title-bar boxes are 22 px. | V-3, T-3 |

## Playback: video, music, games, pictures, live TV

| # | Sev | Problem |
|---|---|---|
| V-1 | critical | Slideshow / picture viewer covers every picture with an opaque grey full-screen image |
| V-2 | high | No touch-usable volume control anywhere: the video and music OSDs have no volume slider or mute button, and the menu-bar volume can only be looked at |
| V-3 | high | Video/Music/Game OSD pops up as a modal box in the middle of the picture, can't be closed by tapping the picture, 'Close' leaves playback, the title-bar fullscreen box is dead and touch targets are tiny |
| V-4 | high | Rewind / Fast-forward buttons pause playback instead of seeking (video and music OSD) |
| V-5 | high | No way to seek by touch: video and music OSD show a passive progress bar, not a seek slider |
| V-6 | high | DialogSeekBar never appears (no window-level <visible>) - no feedback for seeking, FF/RW speed or pause |
| V-7 | high | Settings sliders are invisible in the OSD settings dialogs (volume, audio/subtitle delay, zoom, brightness...) |
| V-8 | high | Video bookmarks window: three blank buttons (one silently wipes bookmarks AND the resume point), raw title 'VideoOSDBookmarks', and an opaque desktop covering the video |
| V-9 | high | Live TV / PVR radio in the OSD: no Channels, Guide, Teletext or RDS buttons; Record shown when not recordable and has no state; progress ignores timeshift |
| V-10 | high | TV guide 'Navigate' dialog (DialogPVRGuideControls) is six blank radio buttons that do nothing, replacing Kodi's working fallback |
| V-11 | high | Slideshow has no on-screen way to exit, pause or change picture by touch |
| V-12 | medium | OSD transport icons: Play never shows Pause, icon radiobuttons flip dim/bright on each tap, Record/Menu show a meaningless checkbox, shuffle/repeat show no state, Previous/Next shown in games |
| V-13 | medium | 'Playlists' buttons (OSD 87 and task bar 9102) open the PlayerControls transport box, not a playlist; the real play queue is unreachable by tap |
| V-14 | medium | Info dialogs are empty boxes and unreachable by touch: Full-screen info, Player process info and PVR radio RDS info |
| V-15 | medium | Dialog title bars left blank (OSDs, Player controls, seek bar, power menu, PVR dialogs, info dialogs) or showing raw/wrong names: TITLES is ignored by dialog() |
| V-16 | medium | PVR channel list OSD has a blank title, an always-empty info box and no channel number or programme |
| V-17 | medium | Game OSD has no Controllers, Ports or Players entries |
| V-18 | medium | Background-task progress (library scan, EPG import) dims the whole screen and sits in the middle, even over playback |
| V-19 | medium | Music visualisation screen is black when no visualisation add-on is set, and shows ' - ' for streams without artist/album |
| V-20 | low | Zoom / view-mode feedback never shown: VideoFullScreen labels 10-12 gated by Player.ShowCodec, removed in Kodi 17 |
| V-21 | low | No buffering indicator in fullscreen video |
| V-22 | low | Redundant videowindow inside VideoFullScreen swallows mouse/touch in DVD/Blu-ray menus |
| V-23 | low | OSD default focus not forced: remote/keyboard Enter re-presses the last button (e.g. Stop) |
| V-24 | low | Game OSD opens with the game paused at launch and gives no explanation (help text and 'controllers only' notice missing) |
| V-25 | low | Busy dialog shows a progress bar bound to a property Kodi never sets, and offers no Cancel by touch |
| V-26 | low | Game picture dialogs (filter/stretch/rotation/saves): no title, filter descriptions never shown, the 'Save' tile is blank |

### V-1 [critical] Slideshow / picture viewer covers every picture with an opaque grey full-screen image

**What you see:** Opening any photo or slideshow shows a plain grey screen instead of the picture.

**Where:** `skin.arthuros/xml/SlideShow.xml:4-7`; `skin.arthuros/xml768/SlideShow.xml:4-7`; `genwindows.py:1404-1415 slideshow() (image at 1404-1407)`

**Why (evidence):** SlideShow.xml's first control is <image> 0,0,1024x600 (768: 1024x768) texture bar_dgrey.png with no colordiffuse; the PNG is opaque RGBA(85,85,85,255). Kodi Omega CGUIWindowSlideShow::Render() (GUIWindowSlideShow.cpp l.677-721): gfxCtx.Clear(0xff000000); m_Image[...]->Render() (or the video layer); RenderErrorMessage(); then CGUIWindow::Render() last, which draws the skin's child controls via CGUIControlGroup::Render (GUIControlGroup.cpp:106-122) - so the opaque image is painted on top of the picture. The generator comment 'Kodi renders the picture itself' is true, but it is rendered underneath the skin. Estuary's SlideShow.xml has no full-screen image. The same window is used for 'view picture' from MyPics.

**Proposed fix:** In genwindows.py slideshow(), delete the first `<control type="image">` (lines 1405-1407: the full-screen image at 0,0, 1024x600, with bar_dgrey.png). Kodi already clears to black before drawing the picture. Keep the caption group. Re-run build.sh so genwindows.py rewrites xml/SlideShow.xml and tallpass.py regenerates xml768/SlideShow.xml. Add a check to audit.sh, e.g. `grep -q bar_dgrey "$S/xml/SlideShow.xml" "$S/xml768/SlideShow.xml" && fail "SlideShow has opaque full-screen background"`. Optionally, following Estuary's SlideShow.xml, add a touch-sized back or close button so a touch-only user can leave the viewer. That should be handled as a separate finding if one exists.

### V-2 [high] No touch-usable volume control anywhere: the video and music OSDs have no volume slider or mute button, and the menu-bar volume can only be looked at

**What you see:** While a video or music is playing there is no way to turn the sound up, down or off by touch. The speaker and bar on the menu bar only show the level; tapping them does nothing. The only route is buried in OSD > Audio settings, where the volume row shows just a number.

**Where:** `skin.arthuros/xml/VideoOSD.xml:44-186 (rows 201/202/203: transport, Playlists/Record/Menu/Find subtitles/Close, Settings: Video/Audio/Subtitles/Bookmarks/Add-on; no volume or mute)`; `skin.arthuros/xml768/VideoOSD.xml (same controls)`; `skin.arthuros/xml/MusicOSD.xml:148-160 (row 203: only Audio / Add-on)`; `skin.arthuros/xml/MusicVisualisation.xml:1-22`; `skin.arthuros/xml/PlayerControls.xml:41-110 (transport only)`; `skin.arthuros/xml/DialogVolumeBar.xml:5-28 (progress, display only, no slider)`; `skin.arthuros/xml/Includes_Chrome.xml:49-65 (menu-bar volume icon + progress + Muted label, not interactive; not drawn in fullscreen video)`; `skin.arthuros/xml768/Includes_Chrome.xml:49-65`; `genwindows.py:332-339 OSD_BUTTONS`; `genwindows.py:437-467 osd_extras (music row2 = [SETTINGS, AUDIO, ADDON]; only the game OSD gets 13376 Volume -> GameVolume)`; `genwindows.py:469-510 osd_window`; `genwindows.py:1436 player_controls()`

**Why (evidence):** grep for SetVolume/VolumeUp/VolumeDown/Mute/<action>volume</action> over skin.arthuros/xml finds nothing; the only interactive volume entry is GameOSD 'Volume' (ActivateWindow(GameVolume)). Kodi only changes volume from actions: CApplication::OnAction (xbmc/application/Application.cpp ~l.1369 ACTION_MUTE, ~l.1392 ACTION_VOLUME_UP/DOWN/SET), which a touch-only user never generates (touchscreen.xml FullScreenVideo/global map no gesture to volume). CGUIDialogVolumeBar (GUIDialogVolumeBar.cpp) is MODELESS and opened only by CApplicationVolumeHandling::ShowVolumeBar after a volume action (ApplicationVolumeHandling.cpp:66-75), so it is a readout, not a control. The menu-bar cluster (Chrome_Menubar: $VAR[VolumeIconVar] image, <progress> on Player.Volume, Muted label) cannot take focus or clicks. The only touch path is OSD > Settings: Audio > 'Volume' (CGUIDialogAudioSettings::InitializeSettings, GUIDialogAudioSettings.cpp l.258 AddSlider SETTING_AUDIO_VOLUME, 13376), two levels down, and that sliderex bar is invisible in this skin and defaults to a 150x16 hit area (GUIControlFactory.cpp sliderWidth=150, sliderHeight=16). Kodi supports what is needed: CGUISliderControl has a built-in 'volume' action (GUISliderControl.cpp l.28: {'volume','SetVolume({:2f})',PLAYER_VOLUME,fireOnDrag=true}); OnMouseEvent (l.705) handles a tap via SetFromPosition and drag via ACTION_GESTURE_PAN. Mute and SetVolume builtins exist (ApplicationBuiltins.cpp:96-106, 215-217). Player.Muted / Player.Volume (PlayerGUIInfo.cpp l.365, l.414). Action(VolumeUp) from a button only steps 1/volumesteps (default 90 -> ~1.1% per tap, Application.cpp l.1400-1421), so +/- buttons alone are not a usable substitute. Games already have this (GameOSD 9975 -> GameVolume).

**Proposed fix:** 1. Video and music OSDs: in genwindows.py osd_extras/osd_window (kinds "video" and "music"), add two controls.
   - A Mute button (id 9981): <onclick>Mute</onclick>, glyph $VAR[VolumeIconVar], or a radiobutton with <selected>Player.Muted</selected>.
   - A touch-size slider (id 9982): <control type="slider"><action>volume</action><info>Player.Volume</info>, width about 220, height 32-44, <enable>!Player.Passthrough</enable>, with a $LOCALIZE[13376] caption label beside it.
   - Put both in a row that the 201/202/203 onup/ondown/onleft/onright navigation reaches, and regenerate for xml and xml768.
   - The slider default in Defaults.xml already supplies the bar and nib textures.

2. PlayerControls.xml: add the same slider and mute button in genwindows.player_controls() (l.1436).

3. Optional, menu bar: in hand-maintained Includes_Chrome.xml (and the xml768 copy), make the volume cluster tappable. Either:
   - put a transparent button over the icon and gauge that opens PlayerControls, or
   - make the speaker icon a button with <onclick>Mute</onclick>.
   Keep it out of keyboard navigation.

4. Audio settings dialog: in Defaults.xml <default type="sliderex">, which is hand-maintained, add texturesliderbar, textureslidernib and textureslidernibfocus. Also set sliderwidth/sliderheight to touch size (for example 260/24) in the DialogSettings.xml sliderex id 13, in that file's generator. This makes the existing Volume row in Audio settings, and every other settings slider, visible and tappable.

5. audit.sh: add checks that grep for '<action>volume</action>' in xml/VideoOSD.xml and xml/MusicOSD.xml, and for '<onclick>Mute</onclick>' in xml/VideoOSD.xml.

### V-3 [high] Video/Music/Game OSD pops up as a modal box in the middle of the picture, can't be closed by tapping the picture, 'Close' leaves playback, the title-bar fullscreen box is dead and touch targets are tiny

**What you see:** Tapping the screen during a video brings up a box right in the middle of the picture. Tapping the picture again doesn't close it; the 'Close' button actually takes you out of the video to the menus while it keeps playing (and in a game it switches window and pauses the game). The square box in the title bar does nothing, the real close box is tiny, and the buttons are small for a finger.

**Where:** `skin.arthuros/xml/VideoOSD.xml:5-7 (<centerleft>50%</centerleft><centertop>50%</centertop>, 892x288)`; `skin.arthuros/xml/VideoOSD.xml:139-149 (button 9951 'Close' = Dialog.Close(all,true)+Action(FullScreen))`; `skin.arthuros/xml/VideoOSD.xml:40-43 (Player.Progress is a <progress>)`; `skin.arthuros/xml/VideoOSD.xml:44-186 (transport 86x36 with 16px glyphs; text rows 30 px)`; `skin.arthuros/xml768/VideoOSD.xml:6, :80 (9902 Action(FullScreen)), :251, :255`; `skin.arthuros/xml/MusicOSD.xml:6-7, :136-140`; `skin.arthuros/xml/GameOSD.xml:6-7, :135-139`; `skin.arthuros/xml768/MusicOSD.xml (button 9951)`; `skin.arthuros/xml768/GameOSD.xml (button 9951)`; `skin.arthuros/xml/Includes_Chrome.xml:453-520 Win_Boxes_dialog (9901 _ = Dialog.Close(all,true)+ActivateWindow(Home); 9902 = Action(FullScreen); 9903 x = Action(Back), 22x22 px)`; `genwindows.py:93-121 dialog() (line 105 hard-codes 50%/50% centring)`; `genwindows.py:332-339, 379-467 (transport/rows helpers; osd_transport 86x36, osd_buttons height 30)`; `genwindows.py:430 CLOSE`; `genwindows.py:469-510 osd_window (calls dialog())`; `skin.arthuros/language/resource.language.en_gb/strings.po (new 31800 block)`

**Why (evidence):** osd_window() builds every OSD with the generic dialog(), which always emits centerleft/centertop 50%; tallpass leaves percent-centred dialogs untouched, so the 892x288 box sits at y 156-444 of 600 and y 240-528 of 768 (preview renders scratchpad/layout/xml-n/VideoOSD.png, xml768-n/VideoOSD.png). Opening: CGUIWindowFullScreen::OnAction (GUIWindowFullScreen.cpp l.93-109) - ACTION_MOUSE_MOVE or ACTION_MOUSE_LEFT_CLICK (touch tap) -> TriggerOSD(): SetAutoClose(3000)+Open(); CGUIDialogVideoOSD::FrameMove (l.35-53) re-arms the timer while InputManager.IsMouseActive() (MouseStat.h MOUSE_ACTIVE_LENGTH 5000 ms), so it lingers ~5-8 s after the last touch. VideoOSD/MusicOSD/GameOSD are MODAL CGUIDialogs (GUIDialog.cpp/GUIDialog.h:39 default); CGUIWindowManager::HandleAction (GUIWindowManager.cpp:1162-1201) gives the topmost modal dialog the action and returns false if unhandled, and inside the OSD CGUIWindow::OnMouseEvent (GUIWindow.cpp l.520-527) only closes on RIGHT_CLICK, so a tap on the picture is swallowed. Only long-press / 2-finger tap (RightClick) or 2-finger swipe-left (Back) close it. 'Close' (9951 / CLOSE): Dialog.Close(all,true) then Action(FullScreen)=ACTION_SHOW_GUI (ActionTranslator.cpp l.45); SwitchToFullScreen() returns false when FULLSCREEN_VIDEO is active, then CGUIWindowFullScreen::OnAction ACTION_SHOW_GUI -> PreviousWindow(): video keeps playing but user is dropped to the menus. Same in Visualisation (GUIWindowVisualisation.cpp ACTION_SHOW_GUI -> PreviousWindow). In a game the active window is WINDOW_FULLSCREEN_GAME; SwitchToFullScreen falls to the IsPlayingVideo branch (RetroPlayer HasVideo() returns true) and activates WINDOW_FULLSCREEN_VIDEO, and CGUIPlaybackControl::FrameMove then pauses the game. Title box 9902 Action(FullScreen) while the modal OSD is open: ignored -> dead button. The only real 'close' is the 22x22 x box (Action(Back) -> CGUIDialog::OnBack). Because the box sits where the finger just tapped, a second dismiss tap lands on Stop/Find subtitles/Close. Touch sizes: no Height_N_XL / XLC in VideoOSD.xml, so Touch mode changes nothing; rows are 30 px (~4.5 mm on the 7" 1024x600, ~5.8 mm on the 9.7"), the x box 22 px (~3.3/4.2 mm), glyphs 16 px. Estuary solves this with a transparent full-screen 'background close area' button <onclick>Action(close)</onclick> as first control and a bottom-anchored panel; GameWindowFullScreen::TriggerOSD opens the game OSD with no auto-close.

**Proposed fix:** All changes go in genwindows.py, plus the hand-maintained Includes_Chrome.xml and strings.po if a box set or new strings are added.

1. **Stop calling dialog() from osd_window().** Either give dialog() an `anchor` parameter, or have osd_window write its own window, with the panel group at `<centerleft>50%</centerleft><bottom>0</bottom>` (or left 0 / bottom 0, full width).
   - If an absolute top is used instead, use top 410 at 600 so that tallpass moves it to the bottom at 768. Check that tallpass really does this before relying on it.

2. **Add a picture close area as the first control.** Use a top-level button id 9990 at left 0, top 0, width 100%, height = the area above the panel.
   - Give it empty texturefocus/texturenofocus and an empty label, and leave it out of all onup/ondown/onleft/onright chains.
   - Clicks:
     - VideoOSD: `<onclick>Dialog.Close(VideoOSD)</onclick>`
     - MusicOSD: `<onclick>Dialog.Close(MusicOSD)</onclick>`
     - GameOSD: `<onclick>Action(Back)</onclick>` (CDialogGameOSD's own back handling resumes the game). Estuary's equivalent is `Action(close)`.
   - Keep `<defaultcontrol always="true">602</defaultcontrol>` so keyboard and remote focus never lands on 9990.

3. **Fix the close button.** Change CLOSE (genwindows.py ~430) so it closes only the OSD: Dialog.Close(VideoOSD)/Dialog.Close(MusicOSD) per kind, or Action(Back) for game. Pass the window name into osd_extras so it can pick the right one.
   - If a "Back to menus" button is wanted, add it separately with a new string (31800+). For video/music it keeps Dialog.Close(all,true)+Action(FullScreen). For game it should use ActivateWindow(Home) rather than Action(FullScreen), which would switch the game into FULLSCREEN_VIDEO.

4. **Remove the dead title-bar box.** Either drop Dialog_Box/Win_Boxes from the OSDs, or add BOXES entries {"VideoOSD","MusicOSD","GameOSD": "osd"} with a new Win_Boxes_osd include in Includes_Chrome.xml.
   - That include should have no 9902, and its x box should be at least 44x44 with the window-specific Dialog.Close.

5. **Make the controls finger-sized.**
   - Transport buttons about 64x56 with 24 px glyphs; text rows 44 px. Update osd_transport, icon_radio/icon_button sizes and osd_buttons heights.
   - Or apply the existing Touch-mode XL includes, as SkinSettings/DialogContextMenu do.

6. **Verify the change.**
   - Preview with RES=xml768 XL=1 SET="touchmode=true" and with the default xml layout; run textfit at Extra large.
   - Add audit.sh checks:
     - no 'centertop>50%' in xml*/VideoOSD.xml, MusicOSD.xml or GameOSD.xml
     - id="9990" present in all three
     - no Action(FullScreen) on the 9951 button
   - On the Pi, test that a tap on the picture closes the bar while the video keeps playing, and that the game OSD background tap resumes the game.

### V-4 [high] Rewind / Fast-forward buttons pause playback instead of seeking (video and music OSD)

**What you see:** Tapping rewind or fast-forward on the OSD just pauses the video or song instead of skipping through it.

**Where:** `skin.arthuros/xml/VideoOSD.xml:59-70 (601: PlayerControl(Play) then PlayerControl(Rewind))`; `skin.arthuros/xml/VideoOSD.xml:94-105 (606: PlayerControl(Play) then PlayerControl(Forward))`; `skin.arthuros/xml768/VideoOSD.xml:176, :211`; `skin.arthuros/xml/MusicOSD.xml:62-73 (601), :97-108 (606)`; `skin.arthuros/xml768/MusicOSD.xml (601/606)`; `genwindows.py:332-339 OSD_BUTTONS (601 at :334, 606 at :337)`; `genwindows.py:342-357 icon_radio`

**Why (evidence):** PlayerBuiltins.cpp PlayerControl(): 'play' = play/pause toggle - if speed != 1 it resets speed to 1, else appPlayer->Pause() (l.131-141). 'rewind'/'forward' only act when IsPlaying() && !IsPaused() (l.161-185). Both onclicks run in sequence (CGUIAction), so at normal speed a tap first pauses, then Rewind/Forward is ignored. For music, PAPlayer::Pause() -> SetSpeed(0) updates CDataCacheCore synchronously and CApplicationPlayer::IsPaused() is GetPlaySpeed()==0, so the same happens. When already at 2x, Play resets to 1x and Forward sets 2x again, so FF never goes past 2x. Estuary (VideoOSD.xml / MusicOSD.xml ids 601/606) uses <onclick condition="Player.Paused">PlayerControl(Play)</onclick><onclick condition="!Player.Paused">PlayerControl(Rewind)</onclick>; CGUIAction evaluates all conditions before running anything.

**Proposed fix:** Fix it in genwindows.py, not in the shipped XML.
1. Let OSD_BUTTONS actions be either a plain string or a (condition, action) tuple.
2. Change entry 601 to [("Player.Paused","PlayerControl(Play)"), ("!Player.Paused","PlayerControl(Rewind)")]. Change entry 606 the same way, with Forward in place of Rewind.
3. In icon_radio() (and icon_button(), so both handle the same shape), output `<onclick condition="...">...</onclick>` for tuples. Put the condition through XML escaping; "!" is fine as written.
4. Optionally add a fifth "visible" field to OSD_BUTTONS and give 601/606 `<visible>Player.SeekEnabled + !VideoPlayer.Content(livetv)</visible>`, as Estuary does. If you do, check that the grouplist layout in osd_transport still looks right, using preview.py.
5. Rebuild with build.sh so xml/ and xml768/ VideoOSD, MusicOSD and GameOSD are all regenerated.
6. Add to audit.sh, for each OSD in xml and xml768: grep -q 'condition="!Player.Paused">PlayerControl(Rewind)' and grep -q 'condition="!Player.Paused">PlayerControl(Forward)'. Also make it fail when an unconditional `<onclick>PlayerControl(Play)</onclick>` sits directly before `<onclick>PlayerControl(Rewind|Forward)</onclick>`.

### V-5 [high] No way to seek by touch: video and music OSD show a passive progress bar, not a seek slider

**What you see:** You can see how far through a video or song you are, but you can't tap or drag the bar to jump to another point.

**Where:** `skin.arthuros/xml/VideoOSD.xml:40-43 (<control type="progress"><info>Player.Progress</info>)`; `skin.arthuros/xml768/VideoOSD.xml:147`; `skin.arthuros/xml/MusicOSD.xml:43-46 (<control type="progress">)`; `genwindows.py:494-500 (progress in osd_window body)`

**Why (evidence):** A progress control is display-only. Kodi's slider has built-in seek actions: GUISliderControl.cpp l.26-27 {'seek','PlayerControl(SeekPercentage({:2f}))',PLAYER_PROGRESS} and {'pvr.seek','PVR.SeekPercentage({:2f})',PVR_TIMESHIFT_PROGRESS_PLAY_POS}; CGUISliderControl::OnMouseEvent (l.705) seeks on a tap anywhere on the bar and handles ACTION_MOUSE_DRAG. Estuary's VideoOSD uses <control type="slider"><info>Player.Progress</info><action>seek</action> and a pvr.seek variant for LiveTV. Touch seek otherwise exists only as hidden gestures in touchscreen.xml <FullScreenVideo>/<Visualisation> (swipe = StepBack/StepForward), which work only while the OSD is closed and give no feedback (DialogSeekBar never shows - separate finding); with the RW/FF defect there is no visible seek at all.

**Proposed fix:** Make the change in genwindows.py `osd_window()`, in the shared body.

1. **Replace the progress control for video and music.** Remove the `<control type="progress">` at 146/96/730x18 and add `<control type="slider" id="9980">` instead:
   - Geometry: left 146, top ~90, width 730, height 30. Give it a large nib texture (e.g. 30px) so it is easy to hit with a finger.
   - Content: `<info>Player.Progress</info><action>seek</action>`.
   - Visibility: `<visible>Player.SeekEnabled + !VideoPlayer.Content(LiveTV)</visible>`.
   - Navigation: `<onup>203</onup><ondown>201</ondown>`.

2. **Add a LiveTV slider.** Add a second slider (id 9981) at the same position with `<info>PVR.TimeshiftProgressPlayPos</info><action>pvr.seek</action>` and `<visible>VideoPlayer.Content(LiveTV) + Player.SeekEnabled</visible>`.

3. **Keep the plain progress where seeking is not possible.** Keep the existing progress control, now with `<visible>!Player.SeekEnabled</visible>`. Also use it for kind == "game".

4. **Update navigation.** Change grouplist 201's `<onup>` (osd_transport) from 203 to 9980. Change 203's `<ondown>` (the osd_buttons call in osd_extras) from 201 to 9980. That keeps the order 9980 -> 201 -> 202 -> 203 -> 9980 for remote and keyboard users.

5. **Check the generated 4:3 files.** tallpass.py makes xml768 from xml/, so it needs no direct edit. After the rebuild, check that tallpass moves and scales the new sliders the same way it moved the progress control (xml768/VideoOSD.xml ~l.147). Then run validate.py, and preview.py with RES=xml768.

6. **Add audit checks.** In audit.sh, add `grep -q '<action>seek</action>'` for xml/VideoOSD.xml and xml/MusicOSD.xml.

Optional extra: the time / duration label at top 68 could be split into Player.Time on the left and Player.Duration on the right, under the bar. This is a nicety, not part of the defect.

### V-6 [high] DialogSeekBar never appears (no window-level <visible>) - no feedback for seeking, FF/RW speed or pause

**What you see:** When you pause, skip or fast-forward a video nothing appears on screen to show where you are, how fast it is going or that it is paused.

**Where:** `skin.arthuros/xml/DialogSeekBar.xml:1-35 (window has <zorder> but no <visible>; centred 892x134 box)`; `skin.arthuros/xml768/DialogSeekBar.xml`; `genwindows.py:922-936 (body + dialog('DialogSeekBar', 892, 134, ..., zorder=3); dialog() cannot emit a window-level <visible>)`

**Why (evidence):** CGUIDialogSeekBar is LOAD_ON_GUI_INIT and MODELESS (GUIDialogSeekBar.cpp:25-29) and Kodi never opens WINDOW_DIALOG_SEEK_BAR from code: the id appears only in GUIDialogSeekBar.cpp, WindowIDs.h, WindowTranslator.cpp, GUIWindowManager.cpp and PlayerGUIInfo.cpp l.495 (confirmed with a GitHub code search). It is shown only via CGUIDialog::UpdateVisibility() (GUIDialog.cpp l.126-134) from the window's <visible> registered in CGUIWindow::Load (GUIWindow.cpp:214). Estuary's DialogSeekBar.xml lines 3-5 carry three window <visible> lines (Window.IsActive(fullscreenvideo)|visualisation; Player.Seeking | Player.HasPerformedSeek(3) | [Player.Paused + !Player.Caching] | Player.Forwarding | Player.Rewinding | Player.ShowInfo | Player.ShowTime | ...). ArthurOS has none, so the dialog is never opened. Render of what would show: scratchpad/layout/xml-n/DialogSeekBar.png.

**Proposed fix:** In genwindows.py, add a `visible=None` parameter to `dialog()`. It should accept a string or a list, and write one `  <visible>...</visible>\n` line per entry right after the `<zorder>` line. Kodi joins multiple window `<visible>` tags with AND (GUIWindow.cpp:210-214 via GetConditionalVisibility).

For DialogSeekBar, pass:
1. `[Window.IsActive(fullscreenvideo) | Window.IsActive(visualisation)] + !Window.IsVisible(videoosd) + !Window.IsVisible(musicosd) + !Window.IsActive(sliderdialog)`
2. `Player.Seeking | Player.HasPerformedSeek(3) | [Player.Paused + !Player.Caching] | Player.Forwarding | Player.Rewinding | Player.ShowInfo | Player.ShowTime | !String.IsEmpty(Player.SeekNumeric)`

Replace the run-together time label with two labels:
- `$INFO[Player.SeekTime]` with `<visible>Player.Seeking | !String.IsEmpty(Player.SeekNumeric)</visible>`
- `$INFO[Player.Time]` with `<visible>!Player.Seeking + String.IsEmpty(Player.SeekNumeric)</visible>`

Add a state label:
- `Paused` when Player.Paused
- `$INFO[Player.PlaySpeed]x` when Player.Forwarding | Player.Rewinding

Optionally, build the dialog as a dedicated bottom strip instead of the centred Dialog_Box: full width, top about 530 in the 600-high xml layout (scale for xml768), no dim. That keeps the middle of the picture clear.

Add an audit.sh check: `grep -q 'Player.HasPerformedSeek' skin.arthuros/xml/DialogSeekBar.xml`.

Then rebuild, so that both xml/ and xml768/ are regenerated.

### V-7 [high] Settings sliders are invisible in the OSD settings dialogs (volume, audio/subtitle delay, zoom, brightness...)

**What you see:** In the OSD Audio, Video and Subtitle settings the Volume, delay and zoom rows show only a number, with no bar or knob to drag, so they look like plain text and are hard to adjust by touch.

**Where:** `skin.arthuros/xml/DialogSettings.xml:78-82 (sliderex template id 13 with no slider textures)`; `skin.arthuros/xml768/DialogSettings.xml:188`; `skin.arthuros/xml/Defaults.xml:157-167 (<default type="sliderex"> has no texturesliderbar/textureslidernib/textureslidernibfocus)`; `genwindows.py:154-190 SETTING_TEMPLATES (sliderex id 13 at l.177)`

**Why (evidence):** CGUIControlFactory::Create for GUICONTROL_SETTINGS_SLIDER (GUIControlFactory.cpp l.1455-1460) builds CGUISettingsSliderControl from texturesliderbar / textureslidernib / textureslidernibfocus read at l.1062-1065; with none given the textures are empty, so CGUISettingsSliderControl::Render (GUISettingsSliderControl.cpp l.80-84) draws only the button face and the value label - no bar, no nib. The defaults for type 'slider' (Defaults.xml l.149-155) do not apply to 'sliderex'. OSD Audio settings' first row is the Volume slider (GUIDialogAudioSettings.cpp l.258), so the only existing volume control shows as text ('-12.0 dB') with an invisible 150x16 hit area (default sliderWidth/Height, GUIControlFactory.cpp l.852).

**Proposed fix:** 1. Hand-edit skin.arthuros/xml/Defaults.xml, inside `<default type="sliderex">`, to add:
   `<sliderwidth>300</sliderwidth><sliderheight>24</sliderheight>`
   `<texturesliderbar border="2" colordiffuse="facetint">progress_back.png</texturesliderbar>`
   `<textureslidernib colordiffuse="text">button_up.png</textureslidernib>` (a contrasting colour, so the nib shows against the bar)
   `<textureslidernibfocus colordiffuse="select">select_bevel.png</textureslidernibfocus>`
   Keep `aspectratio stretch` on images, as CLAUDE.md requires. Then rebuild so tallpass regenerates xml768/Defaults.xml.

2. For touch, change genwindows.py SETTING_TEMPLATES (sliderex id 13, l.177-180) so the XL/touch condition gives a bigger slider, for example `<sliderheight>36</sliderheight><sliderwidth>360</sliderwidth>`. Use the same include/condition mechanism as Height_30_XL, because only the slider rectangle responds to taps (GUISliderControl::HitTest).

3. Run textfit.py and preview.py on DialogSettings to check that the value label (it takes the space left of the slider) still fits in the 846-wide row.

4. Add an audit.sh guard: `grep -A15 'default type="sliderex"' skin.arthuros/xml/Defaults.xml | grep -q texturesliderbar`.

### V-8 [high] Video bookmarks window: three blank buttons (one silently wipes bookmarks AND the resume point), raw title 'VideoOSDBookmarks', and an opaque desktop covering the video

**What you see:** Opening Bookmarks from the video menu hides the video behind the desktop, the title reads 'VideoOSDBookmarks', and the three buttons are blank. One of them silently deletes all bookmarks and the resume point with no warning.

**Where:** `skin.arthuros/xml/VideoOSDBookmarks.xml:4-7 (backgroundcolor desktop + Chrome_Desktop + Chrome_Menubar over the video)`; `skin.arthuros/xml/VideoOSDBookmarks.xml:19 (<param name="label" value="VideoOSDBookmarks" />)`; `skin.arthuros/xml/VideoOSDBookmarks.xml:32-46 (buttons 2,3,4 with no <label>)`; `skin.arthuros/xml768/VideoOSDBookmarks.xml:99, :188-198`; `skin.arthuros/xml/VideoOSD.xml:178 (ActivateWindow(VideoBookmarks))`; `genwindows.py:20-33 TITLES (no VideoOSDBookmarks entry)`; `genwindows.py:80 fullwindow() falls back to TITLES.get(name, name)`; `genwindows.py:1479-1560 generic() (l.1507 emits press buttons without labels)`; `genwindows.py:1834-1840 main() ('as_dialog = name.startswith("Dialog")'; VideoOSDBookmarks falls through to generic())`

**Why (evidence):** CGUIDialogVideoBookmarks (GUIDialogVideoBookmarks.cpp l.46-50) uses CONTROL_ADD_BOOKMARK 2, CONTROL_CLEAR_BOOKMARKS 3, CONTROL_ADD_EPISODE_BOOKMARK 4, CONTROL_THUMBS 11 and never sets their labels; the skin must (Estuary: $LOCALIZE[294] 'Create bookmark', [296] 'Clear bookmarks', [20406] 'Set episode bookmark', plus an empty-list message). ClearBookmarks() (l.378-390) deletes STANDARD, RESUME and EPISODE bookmarks with no confirmation. The window is a generic() placeholder; generic() picks dialog vs full window from the 'Dialog' file-name prefix, so this CGUIDialog got fullwindow(): opaque Chrome_Desktop (Includes_Chrome.xml:11-16), menu bar and task bar hide the video being bookmarked, and with no TITLES entry the raw window name is the title. The same prefix misclassification applies to SmartPlaylistEditor and SmartPlaylistRule. Preview render: scratchpad/layout/xml-n/VideoOSDBookmarks.png shows three empty buttons under the title 'VideoOSDBookmarks'.

**Proposed fix:** All changes go in genwindows.py, since the XML is generated.

1. **New bookmarks_dialog() builder**, registered in main() next to `written["DialogSubtitles"] = subtitles_dialog()`. It should build a compact dialog with no Chrome_Desktop, menu bar or task bar, and a light dim or none, so the video stays visible. Contents:
   - Title $LOCALIZE[298] (Bookmarks).
   - A grouplist with buttons:
     - id 2, label $LOCALIZE[294] (Create bookmark)
     - id 3, label $LOCALIZE[296] (Clear bookmarks)
     - id 4, label $LOCALIZE[20406] (Set episode bookmark), with `<visible>Control.IsEnabled(4)</visible>`
   - A list or panel id 11 showing ListItem.Art(thumb) or Icon, Label, and Label2 (the time).
   - An empty-state label (Estuary uses $LOCALIZE[31155], or a new skin string) with `<visible>Integer.IsEqual(Container(11).NumItems,0)</visible>`.
   - Touch-sized rows in xml768.

2. **Confirmation before clearing.** Kodi deletes the resume point without asking. Optionally, make the visible "Clear bookmarks" control a non-id button that does `<onclick>` with a YesNo confirmation and then SendClick(3), with real button 3 hidden. Otherwise at least move button 3 away from button 2 and give it a distinct warning colour.

3. **Dialog choice by class, not file name.** In main(), replace `as_dialog = name.startswith("Dialog")` with `as_dialog = name.startswith("Dialog") or name in DIALOG_CLASSES`, where `DIALOG_CLASSES = {"VideoOSDBookmarks", "SmartPlaylistEditor", "SmartPlaylistRule"}` (the same set BOXES already marks as "dialog").

4. **No internal names as titles.** Make fullwindow() and dialog() fall back to "" rather than `name` when TITLES has no entry.

5. **Checks.**
   - audit.sh: `grep -q 'LOCALIZE\[296\]' xml/VideoOSDBookmarks.xml && ! grep -q '>VideoOSDBookmarks<\|value="VideoOSDBookmarks"' xml/VideoOSDBookmarks.xml && ! grep -q Chrome_Desktop xml/VideoOSDBookmarks.xml`
   - validate.py: a rule that no window title label equals a window file name.

### V-9 [high] Live TV / PVR radio in the OSD: no Channels, Guide, Teletext or RDS buttons; Record shown when not recordable and has no state; progress ignores timeshift

**What you see:** Watching live TV or listening to radio, there's no button to open the channel list, the TV guide, teletext or radio text, and the Record button doesn't show whether it's recording.

**Where:** `skin.arthuros/xml/VideoOSD.xml:127-132 (608 visible [PVR.IsPlayingTV | PVR.IsPlayingRadio], no <selected>)`; `skin.arthuros/xml/VideoOSD.xml:40-43 (Player.Progress only)`; `skin.arthuros/xml/MusicOSD.xml:124-141 (row 202)`; `genwindows.py:398 LIVE`; `genwindows.py:451-458 osd_extras row1 (kind != game)`

**Why (evidence):** Estuary VideoOSD shows 70040 Channels (Dialog.Close(VideoOSD)+ActivateWindow(PVROSDChannels), visible VideoPlayer.Content(livetv)), 70041 Guide (ActivateWindow(pvrchannelguide), + VideoPlayer.HasEPG), 70045 Teletext (VideoPlayer.HasTeletext), Record visible PVR.CanRecordPlayingChannel with <selected>, and a pvr.seek slider on PVR.TimeshiftProgressPlayPos; Estuary MusicOSD has PVROSDChannels, PVRChannelGuide and PVRRadioRDSInfo (RDS.HasRadiotext). CGUIDialogVideoOSD::FrameMove already keeps the OSD alive while PVR_OSD_CHANNELS / PVR_CHANNEL_GUIDE / OSD_TELETEXT are open (GUIDialogVideoOSD.cpp l.46-48). PVR.CanRecordPlayingChannel and PVR.IsRecordingPlayingChannel exist (GUIInfoManager.cpp docs l.8134/8143). No ArthurOS XML references PVROSDChannels, PVRChannelGuide or PVRRadioRDSInfo (grep). Kodi reaches them only from keymaps (keyboard.xml FullscreenRadio c/g/long-enter); touch users get only a 2-finger tap (FullScreenVideo <tap pointers="2">Playlist</tap>) and swipe up/down to change channel.

**Proposed fix:** Change genwindows.py `osd_extras()`, which generates skin.arthuros/xml/VideoOSD.xml and MusicOSD.xml. Do not edit the XML.

**Visibility conditions.** Define:
- `LIVE_V = "VideoPlayer.Content(LiveTV)"`
- `LIVE_M = "MusicPlayer.Content(LiveTV)"`

**Video row 1.** Add these buttons (they need new free ids):
- Channels ($LOCALIZE[19019]): `ActivateWindow(PVROSDChannels)`, visible LIVE_V.
- Guide ($LOCALIZE[19069]): `ActivateWindow(PVRChannelGuide)`, visible `LIVE_V + VideoPlayer.HasEPG`.
- Teletext ($LOCALIZE[23050], or the existing teletext string): `ActivateWindow(Teletext)`, visible `VideoPlayer.HasTeletext`.

To keep the row within 879px, give 9950 Find subtitles the visibility `!VideoPlayer.Content(LiveTV)`. Do the same for 9964 Bookmarks in row 2.

**Music row 1.** Add:
- Channels, visible LIVE_M.
- Guide, visible `LIVE_M + VideoPlayer.HasEPG`.
- RDS ($LOCALIZE[29900] or another label): `ActivateWindow(PVRRadioRDSInfo)`, visible `LIVE_M + RDS.HasRadiotext`.

**Record button (608).**
- Change its visibility to `PVR.CanRecordPlayingChannel`.
- Teach `osd_buttons()` to emit an optional 6th tuple field as `<selected>`, and pass `PVR.IsRecordingPlayingChannel` for 608. Check the skin's radiobutton on/off texture meaning; do not copy Estuary's inverted condition blindly.

**Closing the OSD.** Either put `Dialog.Close(VideoOSD)` / `Dialog.Close(MusicOSD)` before the ActivateWindow in each new button, or give the OSD's main group `!Window.IsVisible(PVROSDChannels) + !Window.IsVisible(PVRChannelGuide)` as Estuary does (VideoOSD.xml l.22). Without one of these the centred OSD covers the dialog.

**Progress bar (optional, low).** In `osd_window()`, add a second progress control on `PVR.TimeshiftProgressPlayPos`, visible LIVE_V / LIVE_M, and hide the Player.Progress one for LiveTV.

**After the change.** Rebuild, then check that the row text still fits at XL with textfit.py.

### V-10 [high] TV guide 'Navigate' dialog (DialogPVRGuideControls) is six blank radio buttons that do nothing, replacing Kodi's working fallback

**What you see:** In the TV guide, choosing 'Navigate' opens a box of six empty buttons that do nothing.

**Where:** `skin.arthuros/xml/DialogPVRGuideControls.xml:21-58 (radiobuttons 600-605: no label, no onclick)`; `skin.arthuros/xml/DialogPVRGuideControls.xml:57-63 (grouplists 201/202/203 left empty)`; `skin.arthuros/xml768/DialogPVRGuideControls.xml:139-164`; `genwindows.py:1479-1512 generic() (reached via the loop at genwindows.py:1835-1840; fed by inventory.json ids 600-605)`; `inventory.py:43 (`if n < 1000` drops Estuary's channel/group buttons 70040-70045)`

**Why (evidence):** CGUIWindowPVRGuideBase::OnContextButtonNavigate / OnContextButton (GUIWindowPVRGuide.cpp ~l.655-668) uses DialogPVRGuideControls when g_SkinInfo->HasSkinFile("DialogPVRGuideControls.xml"), and only otherwise falls back to its own working context-menu navigation; keyboard.xml TVGuide also maps 'n' to ActivateWindow(PVRGuideControls). CGUIDialogPVRGuideControls is an empty CGUIDialog with no ids, labels or OnMessage, so all behaviour must come from the skin. Estuary's version: 600-605 PVR.EpgGridControl(FirstProgramme / -12 / CurrentProgramme / +12 / LastProgramme / SelectDate) and 70040-70045 (FirstChannel / PlayingChannel / LastChannel / PreviousGroup / NextGroup / SelectGroup). PVR.EpgGridControl is a real Omega builtin (PVRBuiltins.cpp). inventory.py copies only bare ids (dropping >= 1000) so generic() writes six empty radiobuttons and three empty grouplists (preview confirms six empty rows). Note: with no real epggrid in MyPVRGuide (separate finding), these builtins would call GotoBegin() etc. on a null grid (PVRBuiltins.cpp:99-150 -> GUIWindowPVRGuide.cpp:767+).

**Proposed fix:** In genwindows.py, add a dedicated writer pvr_guide_controls() and register it before the generic loop, for example `written["DialogPVRGuideControls"] = pvr_guide_controls()` next to subtitles_dialog() around l.1833. The 768 pipeline then carries it through as it does other dialogs.

Layout: a Dialog_Box with three labelled sections. Each button gets a <label> and an <onclick>.
- Programme ($LOCALIZE[19222] or a new skin string): 600 First programme (19063) -> PVR.EpgGridControl(FirstProgramme); 601 (19317) -> PVR.EpgGridControl(-12); 602 (19070) -> PVR.EpgGridControl(CurrentProgramme); 603 (19318) -> PVR.EpgGridControl(+12); 604 (19064) -> PVR.EpgGridControl(LastProgramme); 605 (19288) -> PVR.EpgGridControl(SelectDate).
- Channels: 70040 (19322) FirstChannel; 70041 (19323) PlayingChannel, visible only when PVR.IsPlayingTV | PVR.IsPlayingRadio | PVR.IsPlayingEpgTag; 70042 (19324) LastChannel.
- Groups: 70043 (19319) PreviousGroup; 70044 (19320) NextGroup; 70045 (19321) SelectGroup.

Use plain buttons rather than radiobuttons, sized at the touch height (Height_30_XL). Add a visible close button with <onclick>Action(close)</onclick>, because touch users have no Esc key. Set defaultcontrol to 602, matching Kodi's fallback, which preselects 'Current programme'.

Ship this together with the real epggrid fix in MyPVRGuide. Until the grid is on screen, the alternative is to remove the dialog. That means deleting skin.arthuros/xml/DialogPVRGuideControls.xml and its xml768 counterpart from inside genwindows.py and the 768 step, not just leaving them out of generation, so that HasSkinFile() is false and Kodi uses its built-in context-menu navigation.

Add an audit.sh check: if DialogPVRGuideControls.xml exists in xml/ and xml768/, every button or radiobutton must have a non-empty <label> and an <onclick>, and all twelve EpgGridControl arguments must be present.

### V-11 [high] Slideshow has no on-screen way to exit, pause or change picture by touch

**What you see:** Once a picture or slideshow is open, there's no button to close it, pause it or go to the next or previous picture; you have to know hidden long-press and multi-finger gestures.

**Where:** `skin.arthuros/xml/SlideShow.xml:1-17`; `genwindows.py:1404-1415`

**Why (evidence):** The window has no controls you can tap. Per touchscreen.xml <SlideShow>, a 1-finger tap falls through to global LeftClick, which CGUIWindowSlideShow::OnMouseEvent ignores (it only handles gestures). Exiting needs a long-press (Back), pausing a 2-finger tap, info a 3-finger tap. None of this is shown on screen. Estuary SlideShow.xml adds TouchBackSlideshowButton (Includes.xml) under Skin.HasSetting(touchmode). CGUIWindowSlideShow is a CGUIDialog whose default OnAction goes to CGUIDialog::OnAction, so mouse events reach skin buttons. Its OnAction handles ACTION_PREV_PICTURE, ACTION_NEXT_PICTURE, ACTION_PAUSE, ACTION_SHOW_INFO and ACTION_STOP (closes); the action names previouspicture, nextpicture, pause, info and stop are in ActionTranslator.cpp. The caption shows on '!Slideshow.IsPaused + Player.ShowInfo', but slideshow never sets Player.ShowInfo, so the caption follows whatever state the last player left. Label id 10 (LABEL_ROW1), which RenderErrorMessage() needs to show 'unable to load', is also missing.

**Proposed fix:** Make every change in genwindows.py slideshow() (lines 1404-1415), then rebuild with build.sh so xml/ and xml768/ are regenerated.

1. **Remove the full-screen bar_dgrey.png image control.** Kodi already clears the screen to black and draws the picture underneath the skin controls, so this image can only hide the photo.

2. **Add an always-visible corner toggle button**, like Estuary's TouchBackSlideshowButton.
   - Size: at least 72x72 in the 1024-wide coordinates.
   - Position: top-right, semi-transparent.
   - Visible on `!Window.IsVisible(PictureInfo)`.
   - Behaviour: `<onclick condition="String.IsEmpty(Window(Home).Property(ArthurSlideBar))">SetProperty(ArthurSlideBar,1,home)</onclick>` and `<onclick condition="!String.IsEmpty(Window(Home).Property(ArthurSlideBar))">ClearProperty(ArthurSlideBar,home)</onclick>`.
   - Do not use System.IdleTime here: touch input (XBMC_TOUCH) never resets the idle timer, so it would not react to taps.

3. **Add a bottom toolbar group** visible on `!String.IsEmpty(Window(Home).Property(ArthurSlideBar))`, with large buttons:
   - Previous: `Action(PreviousPicture)`
   - Play/Pause: `Action(Pause)`, with a label or icon depending on Slideshow.IsPaused
   - Next: `Action(NextPicture)`
   - Info: `Action(Info)`
   - Close: `ClearProperty(ArthurSlideBar,home)` then `Action(Stop)`

4. **Reset the toolbar property when the window opens.** Add `<onload>ClearProperty(ArthurSlideBar,home)</onload>` to the window.

5. **Fix the caption.** Show it on `Slideshow.IsPaused | !String.IsEmpty(Window(Home).Property(ArthurSlideBar))` instead of `!Slideshow.IsPaused + Player.ShowInfo`.

6. **Add Kodi's error label.** Add `<control type="label" id="10">` with a font and an empty label, sized 0x0 or kept off-screen, so RenderErrorMessage() can draw Kodi's "unable to load" text in that font.

Make sure the toolbar sits above the bottom caption so they do not overlap, and render it with preview.py at both layouts (xml768 and xml).

### V-12 [medium] OSD transport icons: Play never shows Pause, icon radiobuttons flip dim/bright on each tap, Record/Menu show a meaningless checkbox, shuffle/repeat show no state, Previous/Next shown in games

**What you see:** The play button always shows a play symbol even while playing, the other buttons randomly look dimmed or bright depending on how many times you've tapped them, Record and Menu show a pointless tick circle, shuffle and repeat never show whether they're on, and games show Previous/Next buttons that do nothing.

**Where:** `skin.arthuros/xml/VideoOSD.xml:48-116 (radiobuttons 600,601,603,606,607 with textureradiooffnofocus colordiffuse=textdim, no <selected>)`; `skin.arthuros/xml/VideoOSD.xml:71-82 (602 always icons16/play.png)`; `skin.arthuros/xml/VideoOSD.xml:127-138 (608 Record, 804 Menu radiobuttons, no <selected>)`; `skin.arthuros/xml/MusicOSD.xml:51-120, :31 (fallback DefaultVideo.png)`; `skin.arthuros/xml/GameOSD.xml:51-120, :31`; `skin.arthuros/xml/PlayerControls.xml:44-110 (607 shuffle radiobutton, 704 repeat plain button - no state; 602 at :55-64)`; `skin.arthuros/media/icons16/pause.png (exists, referenced by no window)`; `skin.arthuros/language/resource.language.en_gb/strings.po #31913-31916 Previous / Play / Pause / Stop / Next (unused)`; `genwindows.py:332-339 OSD_BUTTONS (602 at :335)`; `genwindows.py:342-376 icon_radio / icon_button`; `genwindows.py:379-392, 419 (608/804 forced to radiobutton), 483-485`; `genwindows.py:1462-1467 player_controls (icon_radio(602, 'play', ...) at :1466)`

**Why (evidence):** CGUIRadioButtonControl::OnAction (GUIRadioButtonControl.cpp l.118-124) toggles m_bSelected on every ACTION_SELECT_ITEM; it is only driven by state when a <selected> condition (m_toggleSelect, l.93-103) exists. With none, prev/rew/stop/ffwd/next are drawn with the dimmed 'off' texture until tapped once, then bright, then dim again, and VideoOSD is KEEP_IN_MEMORY (GUIDialogVideoOSD.cpp l.30) so the random state persists. 608/804 inherit radio_on/radio_off.png from Defaults.xml l.80-83, so Record shows a circle that toggles regardless of PVR.IsRecordingPlayingChannel (preview RES=xml768 shows the circles). Shuffle/repeat in PlayerControls never reflect Playlist.IsRandom / IsRepeat / IsRepeatOne. `grep -l pause.png skin.arthuros/xml/*.xml` finds nothing; 602 draws play.png unconditionally and no window uses Player.Paused. Transport controls have empty labels; skin strings 31913-31916 were evidently written for them but nothing references them. 600/607 (PlayerControl(Previous/Next)) appear in GameOSD where there is no playlist; Estuary hides them on MusicPlayer.HasPrevious/HasNext, sets <selected>!PVR.IsRecordingPlayingChannel</selected> on 608 and uses $VAR[PlayerControlsPlayImageVar] for play/pause. The OSD art fallback is DefaultVideo.png for music and games.

**Proposed fix:** All changes go in genwindows.py; the OSD and PlayerControls XML files are generated from it.

(a) Change icon_radio() so it does not dim the 'off' state: drop colordiffuse="textdim" from textureradiooffnofocus. Add an optional `selected=None` argument that emits `<selected>…</selected>`, and only dim 'off' when a `selected` condition is given. Generate the plain transport buttons (600/601/603/606/607 in OSD_BUTTONS; 600/603/605 in player_controls) with icon_button(), or with icon_radio and no dimming.

(b) Play/Pause glyph:
- Add `<variable name="PlayPauseGlyphVar"><value condition="Player.Paused | Player.Forwarding | Player.Rewinding">icons16/play.png</value><value>icons16/pause.png</value></variable>` to the variables generator. Check CLAUDE.md for which script writes Variables.xml.
- Let icon_button() take a texture string, so 602 can use $VAR[PlayPauseGlyphVar] in osd_transport.
- In player_controls, replace icon_radio(602, 'play', …) with icon_button(602, '$VAR[PlayPauseGlyphVar]'-style).
- pause.png already exists, so iconset/mkmedia need no change.

(c) In osd_buttons():
- Make 804 a plain button.
- Give 608 Estuary-style record textures with `<selected>PVR.IsRecordingPlayingChannel</selected>`, or make it a plain button whose label is a variable (Record / Stop recording).
- Set 608's visible condition to `PVR.CanRecordPlayingChannel` instead of LIVE.

(d) In player_controls:
- Use icon_radio(607, 'shuffle', …, selected='Playlist.IsRandom').
- 704 repeat: there is only one repeat glyph today. Either add repeat_one and repeat_off glyphs to iconset.py (iconcheck.py must pass) and pick between them with a variable on Playlist.IsRepeatOne / Playlist.IsRepeat, or make 704 a radiobutton with `<selected>Playlist.IsRepeat | Playlist.IsRepeatOne</selected>` plus a small 'one' emblem/label.

(e) In osd_transport(kind):
- Skip 600/607 when kind == 'game'. Estuary's GameOSD has no transport row; keep Stop and Play/Pause there.
- For video, add `<visible>Player.ChapterCount | Integer.IsGreater(Playlist.Length(video),1) | Player.HasSceneMarkers</visible>` to 600/607.
- For music, use MusicPlayer.HasPrevious / MusicPlayer.HasNext.
- Keep in mind the grouplist will collapse the hidden slots.

(f) In osd_window(), choose the fallback by kind: DefaultVideo.png for video, DefaultAudio.png for music, DefaultAddonGame.png for game.

(g) Either show 31913-31916 as small captions under the glyphs in Touch mode, or remove them from strings.po.

(h) Separate fix: give 601/606 conditional onclicks: `<onclick condition="Player.Paused">PlayerControl(Play)</onclick>` and `<onclick condition="!Player.Paused">PlayerControl(Rewind|Forward)</onclick>`, as in Estuary's VideoOSD.xml.

Afterwards, run validate.py and iconcheck.py.

### V-13 [medium] 'Playlists' buttons (OSD 87 and task bar 9102) open the PlayerControls transport box, not a playlist; the real play queue is unreachable by tap

**What you see:** Tapping 'Playlists' on the video menu, music menu or task bar opens a second small box of play/stop buttons instead of the list of what's queued. There's no button anywhere to see the current playlist.

**Where:** `skin.arthuros/xml/VideoOSD.xml:114-126 (id 87, $LOCALIZE[136] 'Playlists', ActivateWindow(PlayerControls))`; `skin.arthuros/xml/MusicOSD.xml:125-129 (87)`; `skin.arthuros/xml/Includes_Chrome.xml:154-180 (task bar 9102: label $LOCALIZE[136], icon playlist.png, ActivateWindow(PlayerControls)) - hand-maintained`; `skin.arthuros/xml768/Includes_Chrome.xml:162`; `skin.arthuros/xml/PlayerControls.xml:1-114`; `genwindows.py:451 osd_extras() row1 entry (87, 150, '$LOCALIZE[136]', ['ActivateWindow(PlayerControls)'])`; `genwindows.py:1436-1474 player_controls()`

**Why (evidence):** String 136 is 'Playlists' (vendor/kodi/strings.po:590), but PlayerControls (WINDOW_DIALOG_PLAYER_CONTROLS, Kodi string 10114 'Player controls'; the skin itself titles it 31907 'Now playing', genwindows.py:29) is an empty CGUIDialog (GUIDialogPlayerControls.cpp) whose skin XML offers only prev/play/stop/next/shuffle/repeat behind a full Dialog_Dim - all already on the OSD - and no seek or volume (render scratchpad/layout/xml-n/PlayerControls.png). The skin has no ActivateWindow(VideoPlaylist) or ActivateWindow(MusicPlaylist) anywhere. Kodi's own route is ACTION_SHOW_PLAYLIST (GUIWindowFullScreen.cpp l.153-163: PVR channel -> PVROSDChannels, video -> VideoPlaylist), reachable by touch only through the hidden 2-finger tap (touchscreen.xml FullScreenVideo <tap pointers="2">Playlist</tap>). Estuary's OSD playlist button: Dialog.Close(all,true) + ActivateWindow(videoplaylist) visible Integer.IsGreater(Playlist.Length(video),1); MusicOSD: ActivateWindow(musicplaylist) visible Playlist.Length(music)>0. MusicOSD also lacks direct shuffle/repeat and the visualisation controls GUIDialogMusicOSD.cpp handles (CONTROL_VIS_BUTTON 500 chooser, CONTROL_LOCK_BUTTON 501 lock preset; FrameMove allows VIS_SETTINGS / VIS_PRESET_LIST).

**Proposed fix:** 1. genwindows.py osd_extras() row1: replace entry 87 with a real playlist button labelled $LOCALIZE[136]. The video kind gets onclick ["Dialog.Close(all,true)", "ActivateWindow(VideoPlaylist)"] with visible "Integer.IsGreater(Playlist.Length(video),1)". The music kind gets ["Dialog.Close(all,true)", "ActivateWindow(MusicPlaylist)"] with visible "Integer.IsGreater(Playlist.Length(music),0)". For live TV, a Channels button opening ActivateWindow(PVROSDChannels) and visible on PVR.IsPlayingTV can replace it. Keep id 87 or use a free id; GUIDialogVideoOSD does not handle 87.

2. Hand-maintained skin.arthuros/xml/Includes_Chrome.xml (and xml768 via the build): keep 9102 opening PlayerControls, since it is the desktop mini-player. Relabel both label controls to $LOCALIZE[31907] ("Now playing", which already exists in the en_gb strings.po) and change the icon to icons24/player.png, the icon the shipped dialog already uses. No new string is needed.

3. genwindows.py player_controls(): add a Playlist button that opens VideoPlaylist when Player.HasVideo and MusicPlaylist when Player.HasAudio. Optionally add <selected>Playlist.IsRandom</selected> on 607 and a repeat-state indicator.

4. Rebuild, then run textfit.py and iconcheck.py. Add an audit.sh check that fails if any button labelled $LOCALIZE[136] has ActivateWindow(PlayerControls) as its onclick, and that VideoOSD.xml and MusicOSD.xml each contain ActivateWindow(VideoPlaylist) or ActivateWindow(MusicPlaylist) respectively.

5. File the MusicOSD visualisation controls (500/501, VisualisationPresetList) as a separate finding.

### V-14 [medium] Info dialogs are empty boxes and unreachable by touch: Full-screen info, Player process info and PVR radio RDS info

**What you see:** The 'info' screens for the playing video, the playback technical details and radio text all open as empty grey boxes, and there's no on-screen button to get to the video info by touch.

**Where:** `skin.arthuros/xml/DialogFullScreenInfo.xml:1-33 (dim + 900x500 box, empty heading id 1, one unlabelled button 999)`; `skin.arthuros/xml/DialogPlayerProcessInfo.xml:1-18 (dim + empty box, empty heading only)`; `skin.arthuros/xml/DialogPVRRadioRDSInfo.xml:16-31 (empty heading + one unlabelled radiobutton 799; grouplist navigates to nonexistent 9100)`; `skin.arthuros/xml768/DialogPVRRadioRDSInfo.xml`; `inventory.json (DialogPlayerProcessInfo ids {}, DialogFullScreenInfo {999}, DialogPVRRadioRDSInfo {799})`; `genwindows.py:1479-1560 generic(..., as_dialog=True)`; `genwindows.py:1834-1840 (all fall through to generic())`

**Why (evidence):** CGUIDialogFullScreenInfo and CGUIDialogPlayerProcessInfo contain no content code (no SET_CONTROL_LABEL; only Close() on ACTION_SHOW_INFO / ACTION_PLAYER_PROCESS_INFO), so all text must come from skin infolabels (VideoPlayer.Title/Plot/Genre, Player.Process(videodecoder|pixformat|videowidth|videoheight|videofps|audiodecoder|audiochannels|deintmethod), System.CpuUsage). GUIDialogPVRRadioRDSInfo.cpp expects CONTROL_BTN_OK 10, SPIN_CONTROL_INFO 21, TEXT_INFO 22, CONTROL_INFO_LIST 70, CONTROL_NEXT_PAGE 60; Estuary builds the content from RDS.* labels (RDS.GetLine(0..3), RDS.InfoNews, RDS.InfoWeather...). generic() found no ids with a payload and emitted empty frames (xml768 preview: empty 900x500 grey box with blank title). Fullscreen Info opens via CGUIWindowFullScreen::OnAction ACTION_SHOW_INFO (l.126-136) - keyboard 'i' or mouse right-click; with touch a long-press becomes ACTION_MOUSE_RIGHT_CLICK -> OnMouseEvent -> ACTION_SHOW_GUI (l.251-254), i.e. it leaves the video. There is no Info button on the OSD (Estuary has 70043).

**Proposed fix:** All changes go in genwindows.py. Register dedicated builders in main() next to subtitles_dialog() and game_controllers() so these windows no longer fall through to generic().

1) `fullscreen_info()`:
   - Use a panel docked at the bottom, without the full Dialog_Dim, so the video stays visible.
   - Show the poster (`VideoPlayer.Cover` or `Player.Art(thumb)`).
   - Give the heading id 1 the label `$INFO[VideoPlayer.Title]`.
   - Add `VideoPlayer.Year` / `Genre` / `Duration`, and a Plot textbox with autoscroll.
   - Add `Player.Time` / `Player.Duration` and a progress bar.
   - Make a labelled Close button, `onclick Dialog.Close(FullscreenInfo)` ($LOCALIZE[15067]), the default control. Touch-only users need it, because back/right-click are not available.
   - Drop 999 and the 9100 links.

2) `process_info()`:
   - Use a heading string (not a blank label).
   - Add label/value rows for:
     - `Player.Process(videodecoder)`, `(pixformat)`, `(deintmethod)`
     - `(videowidth)` x `(videoheight)`, `(videofps)`, `(videodar)`
     - `(audiodecoder)`, `(audiochannels)`, `(audiosamplerate)`, `(audiobitspersample)`
     - `Player.CacheLevel`
     - `System.CpuUsage`
   - Add a Close button.

3) `pvr_rds_info()`:
   - Use a fixed heading.
   - Add a textbox with `RDS.GetLine(0..3)`, `RDS.ProgStation` and `RDS.Title` / `Artist`.
   - Add a group id 70 containing spin id 21 and textbox id 22 (Kodi shows and hides 70 itself), plus button id 10 for Close.
   - Drop 799 and 9100.

4) In `osd_window()`, add touch buttons:
   - video OSD: Info, `onclick Dialog.Close(VideoOSD)` + `Action(Info,FullscreenVideo)`, or `ActivateWindow(FullscreenInfo)`
   - video OSD: Process info, `Action(PlayerProcessInfo)`
   - music OSD: RDS, `ActivateWindow(PVRRadioRDSInfo)`, visible only with `RDS.HasRDS`

Then rebuild both layouts.

### V-15 [medium] Dialog title bars left blank (OSDs, Player controls, seek bar, power menu, PVR dialogs, info dialogs) or showing raw/wrong names: TITLES is ignored by dialog()

**What you see:** Many pop-up boxes (the video menu, player controls, power menu, TV channel tools and others) have an empty coloured title bar, one shows the internal name 'VideoOSDBookmarks', and the TV guide is titled 'Channel'.

**Where:** `genwindows.py:21-33 TITLES (VideoOSD/MusicOSD/GameOSD/PlayerControls -> $LOCALIZE[31907], never used by dialog())`; `genwindows.py:80 fullwindow() (falls back to raw window name)`; `genwindows.py:93-121 dialog() (uses only its title= argument)`; `genwindows.py:508 osd_window() dialog(..., heading=False)`; `genwindows.py:1074-1076 button_menu() heading=False, no title`; `genwindows.py:1472 player_controls()`; `skin.arthuros/xml/VideoOSD.xml:7-15, MusicOSD.xml, GameOSD.xml, PlayerControls.xml:9-15, DialogSeekBar.xml, DialogButtonMenu.xml:9`; `skin.arthuros/xml768/VideoOSD.xml:41 (<label></label> in title bar)`; `skin.arthuros/xml/DialogPVRChannelManager.xml, DialogPVRGroupManager.xml, DialogPVRGuideSearch.xml, DialogPVRGuideControls.xml, DialogPVRChannelsOSD.xml, DialogPVRChannelGuide.xml, DialogPVRRadioRDSInfo.xml, DialogPictureInfo.xml, DialogPlayerProcessInfo.xml, DialogFullScreenInfo.xml, DialogExtendedProgressBar.xml, DialogSlider.xml (Dialog_Heading id 1 that Kodi never fills)`; `skin.arthuros/xml/VideoOSDBookmarks.xml:19 (raw 'VideoOSDBookmarks')`; `skin.arthuros/xml/MyPVRGuide.xml (title $LOCALIZE[19029] = 'Channel')`

**Why (evidence):** fullwindow() reads TITLES.get(name, name) (genwindows.py:80), but dialog() writes <param name="title"> only when title= is passed and never consults TITLES; every TITLES entry for the OSD family goes through dialog(), which is why 31907 is defined but used nowhere. Kodi writes no id 1 in any of the listed dialogs: grep for CONTROL_HEADING / SET_CONTROL_LABEL(1 in GUIDialogPVRChannelManager.cpp, GUIDialogPVRGroupManager.cpp, GUIDialogPVRGuideSearch.cpp, GUIDialogPVRChannelsOSD.cpp, GUIDialogPVRRadioRDSInfo.cpp, GUIDialogPictureInfo.cpp, GUIDialogPlayerProcessInfo.cpp, GUIDialogExtendedProgressBar.cpp (uses 30/31), GUIDialogFullScreenInfo.cpp and GUIDialogSlider.cpp (uses 10) returns 0; GUIDialogVideoOSD/PlayerControls have no label code; GUIDialogButtonMenu.cpp only knows 3100 (Estuary passes header_label 31072 for the power menu and 16003 for PlayerControls). 19029 is 'Channel' (vendor/kodi/strings.po:9718); the guide is 19069 'Guide'. Renders: scratchpad/layout/xml-n/VideoOSD.png, PlayerControls.png, grid/xml768-n-02.png (power menu), xml-n/VideoOSDBookmarks.png all show empty blue bars or the raw name.

**Proposed fix:** All changes go in genwindows.py. The XML files are all generated by it; xml768 then follows via tallpass.

1. dialog(): add `if title is None and not heading: title = TITLES.get(name)` before the `if title:` check. Never override a dialog where Kodi does fill id 1 (heading=True dialogs like progress or ok).

2. generic(name, meta, as_dialog=True):
   - Look up `t = TITLES.get(name)`.
   - If it is set, pass title=t to dialog() and do not emit Dialog_Heading. Id 1 is not required anywhere Kodi does not write it; only GroupManager lists id 1 in inventory.json, and Kodi's GUIDialogPVRGroupManager never writes it.
   - Otherwise keep the current behaviour.

3. Add or change TITLES entries:
   - DialogButtonMenu: $LOCALIZE[31976] (the skin's "Power menu" string)
   - PlayerControls: $LOCALIZE[16003] ("Player"), or keep 31907
   - DialogSeekBar: $LOCALIZE[31907]
   - VideoOSDBookmarks: $LOCALIZE[298]
   - DialogPVRChannelManager: $LOCALIZE[19199]$INFO[Container(20).NumItems, (,)]
   - DialogPVRGroupManager: $LOCALIZE[19205]
   - DialogPVRGuideSearch: $LOCALIZE[19142] ("Search guide"; better than 137)
   - DialogPVRGuideControls: $LOCALIZE[19222]
   - DialogPVRChannelsOSD and DialogPVRChannelGuide: $LOCALIZE[19019]
   - DialogPictureInfo: $LOCALIZE[13406]
   - DialogPlayerProcessInfo and DialogFullScreenInfo: $LOCALIZE[14116]
   - DialogPVRRadioRDSInfo: a radio/RDS string, verify the id in strings.po
   - DialogSlider: $INFO[Control.GetLabel(10)], or leave the bar blank, since id 10 already shows the heading in the body
   - DialogExtendedProgressBar: same choice, with id 30
   - MyPVRGuide: change to $LOCALIZE[19069]

4. fullwindow(): change the fallback from TITLES.get(name, name) to TITLES.get(name, ""), so an internal name can never reach the screen.

5. Add an audit.sh check that fails if any Win_Title or Dialog_Box title equals the file's basename, or if a Dialog_Box has an empty title and no Dialog_Heading.

If the VideoOSD is redesigned as a bottom bar without a title bar, the VideoOSD part of this goes away.

### V-16 [medium] PVR channel list OSD has a blank title, an always-empty info box and no channel number or programme

**What you see:** The channel list you get while watching TV has no title, an empty box at the bottom, and doesn't show channel numbers or what's on now.

**Where:** `skin.arthuros/xml/DialogPVRChannelsOSD.xml:16 (Dialog_Heading id 1)`; `skin.arthuros/xml/DialogPVRChannelsOSD.xml:21-37 (list 11 using Arthur_ItemLayout)`; `skin.arthuros/xml/DialogPVRChannelsOSD.xml:42-50 (well + label id 2)`; `genwindows.py:1479-1560 (generic())`

**Why (evidence):** Kodi does not set heading id 1 for this dialog (GUIDialogPVRChannelsOSD.cpp / GUIDialogPVRItemsViewBase.cpp only bind CONTROL_LIST 11). Label id 2 is filled by Estuary from $VAR[BreadcrumbsPVRChannelsOSDVar] and Kodi never writes it, so the 94 px footer well is always empty. Arthur_ItemLayout shows ListItem.Icon at 16x16, ListItem.Label and ListItem.Label2, so there is no channel number (ListItem.ChannelNumberLabel) and no current programme (ListItem.Title / ListItem.Progress).

**Proposed fix:** In genwindows.py, add a dedicated builder `pvr_channels_osd()` and register it in the main block next to the other builders, for example `written["DialogPVRChannelsOSD"] = pvr_channels_osd()` near lines 1820-1833. Registering it stops the generic() fallback from producing this dialog.

The builder should do four things:
1. Call dialog("DialogPVRChannelsOSD", 900, 500, body, default="11", icon="icons24/pvr_channels.png", title="$LOCALIZE[19019] - $INFO[VideoPlayer.ChannelGroup]"). Passing title= drops the empty Dialog_Heading and uses the Dialog_Box title param. If Dialog_Box puts the title param inside a `<label>`, check that it accepts $INFO.
2. Give list 11 its own channel row in both itemlayout and focusedlayout, plus an XL/touch row at least 44 px tall. Each row shows $INFO[ListItem.ChannelNumberLabel] in a narrow column, the ListItem.Icon logo at about 40x40 with aspectratio keep, $INFO[ListItem.Label], and $INFO[ListItem.Title] in a dimmer colour on the right or on a second line. Add a thin progress bar with `<info>ListItem.Progress</info>`.
3. Keep label id 2 but give it a text: $INFO[Container(11).ListItem.Title]. Add a second label: $INFO[Container(11).ListItem.StartTime]$INFO[Container(11).ListItem.EndTime, - ,]. Add a progress bar with `<info>Container(11).ListItem.Progress</info>` in the footer well. Kodi never writes id 2, so a skin label is safe there. Alternatively, remove the well and make the list taller.
4. Keep scrollbar 60, and keep onleft/onright going to 11/60.

Then rebuild both layouts with build.sh and check the result with preview.py for xml and xml768.

### V-17 [medium] Game OSD has no Controllers, Ports or Players entries

**What you see:** During a game there's no way to set up or check controllers, ports or players from the game menu.

**Where:** `skin.arthuros/xml/GameOSD.xml:123-177 (rows 202/203)`; `genwindows.py:440-449 (osd_extras game branch)`

**Why (evidence):** The game rows are Save/Load, Reset, Close and Filter, Stretch, Rotation, Volume, Advanced. Estuary GameOSD.xml also has Players (ActivateWindow(GameAgents), 35172), and its game settings list (Custom_1101_SettingsList.xml) has Controllers (ActivateWindow(GameControllers), 35234) and Ports (ActivateWindow(GamePorts), 35110). ArthurOS already ships layouts for all three in Includes_Games.xml (Arthur_GameControllers/Ports/Agents), but nothing reaches them during a game.

**Proposed fix:** Change genwindows.py osd_extras(kind == "game"), not the shipped XML. In row1, insert three buttons before CLOSE:
- (9977, 120, "$LOCALIZE[35234]", ["ActivateWindow(GameControllers)"], None)  # "Controls"
- (9978, 90, "$LOCALIZE[35110]", ["ActivateWindow(GamePorts)"], None)
- (9979, 110, "$LOCALIZE[35172]", ["ActivateWindow(GameAgents)"], None)

Row 202 then totals about 810 of 866 at the base font. Check that IDs 9977-9979 are not already used in GameOSD. Rebuild, then run textfit.py and validate.py. If the XL font overflows, narrow the Save/Load button (180 is generous) or move Close to the end of row 203. Optionally also add a "Controllers" entry to the game section of the Settings/Games hub so controllers can be set up outside a game.

### V-18 [medium] Background-task progress (library scan, EPG import) dims the whole screen and sits in the middle, even over playback

**What you see:** Whenever Kodi does something in the background (updating the library or TV guide), the whole screen goes dim with a box in the middle, even over a video you're watching.

**Where:** `skin.arthuros/xml/DialogExtendedProgressBar.xml:3-8 (Dialog_Dim + centred group)`; `skin.arthuros/xml768/DialogExtendedProgressBar.xml:4-7`; `genwindows.py:972-973 (dialog(..., dim default True))`

**Why (evidence):** GUIDialogExtendedProgressBar.cpp builds the dialog as DialogModalityType::MODELESS, and GetHandle() opens it for any background job (EPG import, scans, add-on installs). Input still reaches the window below, but ArthurOS draws Dialog_Dim (a full-screen dim.png) plus a 572x142 box at screen centre. Estuary draws a 60x60 indicator in the top-right corner and slides it away over FullscreenVideo/FullscreenGame.

**Proposed fix:** Change genwindows.py, not the shipped XML (tallpass.py regenerates xml768). Two ways to do it:

1. Add a `pos=None` parameter to dialog(). When it is given, emit it in place of the centerleft/centertop line. Then build the dialog as `dialog("DialogExtendedProgressBar", 572, 142, body, icon=..., heading=True, dim=False, pos="<right>10</right><bottom>40</bottom>")`.
2. Or write the window by hand, the same way DialogNotification is written.

Either way:
- Use a smaller panel, about 360x96: heading (id 1), label 30, and progress 32 at full width. Label 31 can be dropped or kept on a single line.
- Anchor it bottom-right above the taskbar, or top-right with top of about 136 so it sits below the notification panel (right 10, top 34, height 96). It must not use the same right 10 / top 34 rectangle as the notification.
- Add `<animation effect="fade" end="0" time="200" condition="Window.IsActive(fullscreenvideo) | Window.IsActive(visualisation) | Window.IsActive(fullscreengame)">Conditional</animation>` to the group, or a slide off-screen like Estuary's, so it never covers a video. Because the dialog is modeless and closes itself, hiding it has no side effects.
- Keep it non-dimming so the screen underneath stays usable by touch.

Rebuild, then check with RES=xml768 preview.py.

### V-19 [medium] Music visualisation screen is black when no visualisation add-on is set, and shows ' - ' for streams without artist/album

**What you see:** Playing music full screen often shows just a black screen, and radio streams show a stray ' - '.

**Where:** `skin.arthuros/xml/MusicVisualisation.xml:4-6`; `skin.arthuros/xml/MusicVisualisation.xml:9,16-17`; `genwindows.py:1417-1434 (music_vis())`

**Why (evidence):** The window has only the visualisation control and an info panel visible on Player.ShowInfo. CGUIWindowVisualisation::FrameMove hides the panel after m_songInfoDuration unless SETTING_MYMUSIC_SONGTHUMBINVIS is set. There is no background for !Visualisation.Enabled, and the info is not shown while the OSD is open. Estuary shows Player.Art(fanart) and keeps the info visible on [Player.ShowInfo | Window.IsActive(musicosd)]. The label '$INFO[MusicPlayer.Artist] - $INFO[MusicPlayer.Album]' leaves a bare ' - ' for internet/PVR radio.

**Proposed fix:** Change music_vis() in genwindows.py. The xml768 copy comes from the same build, so it updates too.
1. Add `<backgroundcolor>` set to the skin's desktop colour token (or a full-screen image using the skin's background texture). Then add a full-screen image `$INFO[Player.Art(fanart)]` with aspectratio scale and background="true", faded to 50% under the condition Visualisation.Enabled.
2. Add a large centred cover image `$INFO[MusicPlayer.Cover]` with fallback DefaultAudio.png, visible on `!Visualisation.Enabled + String.IsEmpty(Player.Art(fanart))`.
3. Change the info group's visibility to `Player.ShowInfo | !Visualisation.Enabled`, so it does not time out when the screen would otherwise be empty. Adding Window.IsActive(musicosd) is optional: MusicOSD already shows now-playing info, so check for overlap with the OSD panel first.
4. Change the label to `$INFO[MusicPlayer.Artist]$INFO[MusicPlayer.Album, - ]`. With no artist this still gives a leading " - "; to avoid that, use a $VAR with conditions (Artist+Album, Artist only, Album only).

### V-20 [low] Zoom / view-mode feedback never shown: VideoFullScreen labels 10-12 gated by Player.ShowCodec, removed in Kodi 17

**What you see:** When you change zoom or aspect ratio during a video, nothing on screen tells you which mode you've picked.

**Where:** `skin.arthuros/xml/VideoFullScreen.xml:4, 9-16 (empty group id 0; labels 10-12 inside <visible>Player.ShowCodec</visible> at :11)`; `skin.arthuros/xml768/VideoFullScreen.xml:11`; `genwindows.py:1389-1402 fullscreen_video (l.1397)`

**Why (evidence):** GUIInfoManager.cpp l.9896-9902 lists Player.ShowCodec under 'Kodi v17 (Krypton) Removed Boolean Conditions' and it is in no infomap table (player_conditions l.~885-960 has caching, seekbar, seeking, showinfo, muted... but no showcodec), so TranslateSingleString returns 0 and GetBool(0) returns false (l.10884-10910): the group is never visible. GUIWindowFullScreenDefines.h: BLUE_BAR 0, LABEL_ROW1 10, ROW2 11, ROW3 12. CGUIWindowFullScreen::FrameMove (l.290-359) fills 10-12 with view mode, sizing (string 245) and output resolution after ACTION_ASPECT_RATIO and toggles them with SET_CONTROL_VISIBLE/HIDDEN for 2.5 s.

**Proposed fix:** In genwindows.py fullscreen_video(), replace the empty `<control type="group" id="0">` line and the separate Player.ShowCodec group with one group:

```xml
<control type="group" id="0">
  <left>6</left><top>6</top><width>620</width><height>84</height>
  <include content="Win_Frame">...</include>
  <!-- labels 10, 11, 12 unchanged -->
</control>
```

- Drop `<visible>Player.ShowCodec</visible>` entirely and keep the group after the videowindow so it draws on top.
- Kodi's FrameMove shows and hides id 0 (BLUE_BAR) together with labels 10-12, so the frame appears only for the 2.5 s the info is shown, as in Estuary.

Then rebuild so both xml/ and xml768/ are regenerated.

Optional: add an audit.sh/validate.py check that rejects `Player.ShowCodec` and other infobools Kodi has removed.

Related, separate issue: to make this reachable by touch, give the VideoOSD a zoom/aspect button that sends Action(AspectRatio). Note that it only cycles the mode while the info is already showing, so the button needs a double send or should open the video settings dialog instead.

### V-21 [low] No buffering indicator in fullscreen video

**What you see:** If a stream stalls to buffer, the picture just freezes with no sign that it's loading.

**Where:** `skin.arthuros/xml/VideoFullScreen.xml:5 (group id 1 is empty)`; `genwindows.py:1389-1402 fullscreen_video`

**Why (evidence):** Player.Caching and Player.CacheLevel exist (GUIInfoManager.cpp l.890, l.898). Estuary's VideoFullScreen.xml uses group id 1 visible Player.Caching + Integer.IsGreater(Player.CacheLevel,0) showing $INFO[Player.CacheLevel]. ArthurOS shows nothing; and since DialogSeekBar never appears, nothing at all indicates a stall.

**Proposed fix:** Make the change in genwindows.py fullscreen_video() (line 1392), not in the generated XML; tallpass.py then carries it into xml768. Replace the empty group id 1 with a centred box like this:

`<control type="group" id="1"><left>412</left><top>255</top><width>200</width><height>90</height><visible>Player.Caching + Integer.IsGreater(Player.CacheLevel,0)</visible><animation effect="fade" delay="300" time="200">Visible</animation>` + the Win_Frame include (width 200, height 90) + `<control type="label"><left>10</left><top>8</top><width>180</width><height>28</height><font>small</font><align>center</align><label>$LOCALIZE[15107] $INFO[Player.CacheLevel]%</label></control>` + `<control type="progress"><left>16</left><top>50</top><width>168</width><height>22</height><info>Player.CacheLevel</info></control></control>`.

Put the group after the videowindow control in the file so it draws on top. The visible condition must stay so the box does not show during normal playback. After the build, run textfit.py to confirm the label fits in every fontset.

### V-22 [low] Redundant videowindow inside VideoFullScreen swallows mouse/touch in DVD/Blu-ray menus

**What you see:** In DVD or Blu-ray menus, tapping a menu item on screen may not work.

**Where:** `skin.arthuros/xml/VideoFullScreen.xml:6-8`; `genwindows.py:1393-1394`

**Why (evidence):** CGUIWindowFullScreen::Render already renders the video (GUIWindowFullScreen.cpp l.378-386). CGUIVideoControl::CanFocusFromPoint returns IsVisible() && HitTest() and OnMouseEvent handles ACTION_MOUSE_LEFT_CLICK (sends GUI_MSG_FULLSCREEN, returns HANDLED) (xbmc/guilib/GUIVideoControl.cpp). In a disc menu CGUIWindowFullScreen::OnAction lets left clicks fall through (l.104-110, IsInMenu), so the full-screen videowindow eats them before CApplication passes the action to the player (Application.cpp l.1212 appPlayer->OnAction, after the window manager). It also triggers a second Render/Clear pass each frame. Estuary's VideoFullScreen has no videowindow.

**Proposed fix:** In `genwindows.py` `fullscreen_video()`, delete the two lines that output the videowindow control (the `"    <control type=\"videowindow\">\n"` line and the `"      <left>0</left>...<height>600</height>\n    </control>\n"` line, about l.1393-1394). Rebuild so both `xml/VideoFullScreen.xml` and `xml768/VideoFullScreen.xml` lose it. Keep the empty groups with id 0 and 1 and the codec-info group. To check the fix, play a DVD ISO with menus and tap a menu item: it should activate. Outside menus, tapping should still bring up the OSD.

### V-23 [low] OSD default focus not forced: remote/keyboard Enter re-presses the last button (e.g. Stop)

**What you see:** With a remote or keyboard, opening the video menu and pressing OK can repeat whatever button you last used, such as Stop.

**Where:** `skin.arthuros/xml/VideoOSD.xml:3 (<defaultcontrol>602</defaultcontrol> without always)`; `genwindows.py:102 dialog() defaultcontrol emission`

**Why (evidence):** CGUIWindow::OnInitWindow restores m_lastControlID when !m_defaultAlways (GUIWindow.cpp l.921-934); VideoOSD is KEEP_IN_MEMORY. keyboard.xml FullscreenVideo maps Enter/Return to OSD, so after the OSD last closed with focus on Stop, Enter then Enter stops playback. Estuary uses <defaultcontrol always="true">602</defaultcontrol>.

**Proposed fix:** In genwindows.py:
1. Add a keyword parameter `default_always=False` to dialog().
2. At line 101, emit the tag like this: `if default: s += f"  <defaultcontrol{' always=\"true\"' if default_always else ''}>{default}</defaultcontrol>\n"`.
3. In osd_window(), around line 508, pass `default_always=True`: `return dialog(name, 892, 288, body, default="602", default_always=True, ...)`.

This fixes VideoOSD, MusicOSD and GameOSD in both xml/ and xml768/. Then rebuild with build.sh.

### V-24 [low] Game OSD opens with the game paused at launch and gives no explanation (help text and 'controllers only' notice missing)

**What you see:** Starting a game without a controller opens the game menu with the game paused, and nothing explains why or how to carry on.

**Where:** `skin.arthuros/xml/GameOSD.xml:1-179 (no control id 1101)`; `genwindows.py:469-510`

**Why (evidence):** GameWindowFullScreen.cpp OnInitWindow() calls TriggerOSD() when ShowOSDHelp() is set, and also when !appPlayer->HasGameAgent() (no controller connected, the touch-only case), so the OSD opens on every launch. CGUIPlaybackControl::FrameMove keeps the game at speed 0 while it is open. DialogGameOSDHelp.cpp writes 'Press {combo} to open the in-game menu' (35235) into control 1101, and CDialogGameOSD::OnAction uses IsVisible(1101) to dismiss the help first. Estuary shows a help group on System.GetBool(gamesgeneral.showosdhelp) with 35236 'In this release, only controllers can be used to play games.' ArthurOS has no 1101 and no notice.

**Proposed fix:** In genwindows.py, in osd_window() for kind == 'game', add these controls in the free band between the progress bar (bottom at about y=114) and the transport row (y=166). For example, left 146, top 120, width 730, height 40:
(a) A label with $LOCALIZE[35236], font small, textcolor textdim, wrapmultiline, visible on System.GetBool(gamesgeneral.showosdhelp). Optionally show it always for kind=='game', since touch can never drive a game.
(b) Optionally, a textbox id="1101" with the same visibility condition, for parity with Estuary (Kodi fills it with 35235). Tie it to the same condition so Back dismisses it on the first press.
Do not add a separate Resume button: control 602 (PlayerControl(Play)) already resumes and closes the OSD through CRetroPlayer::SetSpeed(1.0) and CloseOSD(). Giving 602 a text label such as $LOCALIZE[35224] or 208 (Play) would make that clearer.
Separately, for kind == 'game', replace the shared CLOSE tuple's actions ["Dialog.Close(all,true)", "Action(FullScreen)"] with ["Dialog.Close(gameosd)"] (or PlayerControl(Play)), so Close goes back to the game rather than leaving it through ACTION_SHOW_GUI and PreviousWindow. Then regenerate xml/ and xml768/ with build.sh.

### V-25 [low] Busy dialog shows a progress bar bound to a property Kodi never sets, and offers no Cancel by touch

**What you see:** The 'busy' box shows an empty progress bar that never moves, and there's no Cancel button to tap.

**Where:** `skin.arthuros/xml/DialogBusy.xml:20-23 (progress at :21)`; `skin.arthuros/xml768/DialogBusy.xml:66`; `genwindows.py:871-890 (out['DialogBusy'], <info>Window(busydialog).Property(Busy.Progress)</info> at :888)`

**Why (evidence):** GUIDialogBusy.cpp/.h (Omega) contain no SetProperty, label or progress API; the dialog only opens, runs ProcessRenderLoop and closes (WaitOnEvent). GUIDialogBusyNoCancel.cpp loads the same DialogBusy.xml. Window(busydialog).Property(Busy.Progress) is always empty, so the bar stays at 0. Estuary shows only a spinner. Cancelling is supported: CGUIDialogBusy::OnBack sets m_cancelled, which WaitOnEvent(allowCancel) honours; but boxes=none removes the x box, so a touch user can only cancel with a long-press (RightClick -> CGUIWindow::OnMouseEvent -> ACTION_PREVIOUS_MENU).

**Proposed fix:** Edit out["DialogBusy"] in genwindows.py, then rebuild so xml/ and xml768/ are regenerated.
(a) Remove the progress control. In its place put a static clock icon (the dialog already uses icons24/clock.png) or simply centre the $LOCALIZE[20186] "Please wait" label vertically.
(b) Make the group taller (for example 120 to 170, and update the Dialog_Box width/height params to match). Add a button control about 48px tall in the skin's normal button style, with:
`<label>$LOCALIZE[222]</label><onclick>Action(Back)</onclick><visible>Window.IsActive(busydialog)</visible>`
and give it `<defaultcontrol>` focus.
The visible condition matters: busydialognocancel shares this XML, and Back there only closes the dialog without stopping the work.
Optionally, also hide the Dialog_Dim image while Window.IsVisible(fullscreenvideo), as Estuary does, so the screen does not darken over playing video.

### V-26 [low] Game picture dialogs (filter/stretch/rotation/saves): no title, filter descriptions never shown, the 'Save' tile is blank

**What you see:** In the game picture and save menus the title is empty, filters have no description, and the 'new save' tile is a blank box.

**Where:** `skin.arthuros/xml/DialogSelect.xml:16 (Dialog_Heading id 1 left empty in game dialogs)`; `skin.arthuros/xml/DialogSelect.xml:201-205 (10810)`; `skin.arthuros/xml/DialogSelect.xml:206-277 (10811 item layouts)`; `skin.arthuros/xml/DialogSelect.xml:281-285 (10812 fixed label savestate.caption)`

**Why (evidence):** DialogGameVideoSelect.cpp sets the heading on 10810 (SET_CONTROL_LABEL(CONTROL_VIDEO_HEADING)), so the title bar (id 1) stays empty. OnDescriptionChange() sends the description to CONTROL_VIDEO_THUMBS rather than 10812, and 10812's static label only shows savestate.caption, so filter dialogs never show a description. DialogGameVideoFilter.cpp sets Label2 (category) and the property game.videofilterdescription, but the panel layouts show only ListItem.Label. DialogInGameSaves.cpp CreateNewSaveItem() uses path NO_PIXEL_DATA ('won't render any pixels') and art icon DefaultAddSource.png. The layout shows the gamewindow whenever screenshot art is empty, so the 'Save' tile is a blank box.

**Proposed fix:** Edit skin.arthuros/xml/DialogSelect.xml by hand. It is hand-maintained; xml768/ is regenerated from it by tallpass.py at the next build.
1. Description: change the 10812 label to $INFO[Container(10811).ListItem.Property(savestate.caption)]$INFO[Container(10811).ListItem.Property(game.videofilterdescription)]. Only one of the two is ever set at a time.
2. Label2: in both the 10811 itemlayout and focusedlayout, show Label2. Either shrink the name label and add a second small textdim label below it with $INFO[ListItem.Label2], or use one label with $INFO[ListItem.Label]$INFO[ListItem.Label2, · ,] and scroll in the focused layout. The tile has room if the image area is cut by about 14px or the itemlayout height goes from 150 to 164.
3. Title (cosmetic, optional): in game mode, give the title bar the heading. Add a second label at the id 1 position with <label>$INFO[Control.GetLabel(10810)]</label>, visible only in the four game windows. Keep 10810 as a hidden or zero-size label, because Kodi still writes to it.
4. Leave the gamewindow/screenshot logic alone. It does not set <pixels>, so the "Save" tile already shows the live game.
5. Add an audit.sh check that the 10812 label contains game.videofilterdescription and that the 10811 layouts reference ListItem.Label2.

## Using it by touch alone

| # | Sev | Problem |
|---|---|---|
| T-1 | high | Media toolbar 'Options' button (9501) does nothing: Action(ContextMenu) goes to the focused button, not the list |
| T-2 | high | Task-bar 'Now playing' button runs both ActivateWindow(FullscreenVideo) and ActivateWindow(Visualisation): during a video it lands on the music visualisation, and games go wrong |
| T-3 | high | While any dialog is open the task-bar Back button is dead; the only visible close is a 22x22 box |
| T-4 | high | DialogTextViewer text can't be scrolled at all: textbox 5 has no pagecontrol, scrollbar 60 is unlinked |
| T-5 | medium | Long info texts (plot, privacy policy, confirm text, skin help) can't be scrolled by touch and are cut off at Extra-large fonts |
| T-6 | medium | Touch mode doesn't enlarge the chrome hit targets: title-bar boxes 22 px, task-bar buttons 24 px, media toolbar 26 px, horizontal button rows 30 px |
| T-7 | medium | Spin arrows (18x18), slider bars (150x16) and scrollbars (18 px) keep mouse sizes in Touch mode |
| T-8 | medium | On-screen keyboard never shows what it is asking for: Kodi writes the heading to label 311, which is parked off-screen, and title-bar id 1 stays empty |
| T-9 | medium | Context menu shows at most 8 entries in Touch mode, the rest clipped with no scrollbar (also in the 768 layout) |
| T-10 | medium | Skin settings list overflows in Touch mode with no scrollbar; Customise desktop, Back up, Restore and Defaults sit below the fold |
| T-11 | low | Title-bar 'fullscreen' box is dead in every dialog |
| T-12 | low | Touch mode with 'Hide the task bar' on removes the only Back button and leaves Down navigation pointing at hidden controls |
| T-13 | low | File browser thumbnail view (451) keeps 26 px rows in Touch mode |
| T-14 | low | mousewatch.py starts only from Home: if Kodi starts in another window, the pointer stays hidden with a mouse attached |

### T-1 [high] Media toolbar 'Options' button (9501) does nothing: Action(ContextMenu) goes to the focused button, not the list

**What you see:** The 'Options' button on library and add-on screens does nothing when tapped, so the item menu (mark watched, add to favourites, etc.) is only reachable by a hidden long-press.

**Where:** `skin.arthuros/xml/Includes_Media.xml:43-47 (button 9501, <onclick>Action(ContextMenu)</onclick>) - hand-maintained`; `skin.arthuros/xml768/MyVideoNav.xml:217-221 (and every media browser in xml768)`

**Why (evidence):** A tap first gives the button focus. The Action builtin (GUIBuiltins.cpp) sends TMSG_GUI_ACTION -> CGUIWindowManager::OnApplicationMessage (GUIWindowManager.cpp:1050-1056) -> CApplication::OnAction -> CGUIWindow::OnAction (GUIWindow.cpp:419-433), which offers ACTION_CONTEXT_MENU only to the focused chain: button 9501, then grouplist 9490. CGUIButtonControl::OnAction (GUIButtonControl.cpp:208-216) handles only ACTION_SELECT_ITEM; neither CGUIWindow's own switch (l.443-477) nor CGUIMediaWindow::OnAction (GUIMediaWindow.cpp:183-225) nor Application.cpp handles ACTION_CONTEXT_MENU. The media-window context menu opens only from GUI_MSG_CLICKED sent by the focused view container (CGUIBaseContainer::OnClick, GUIBaseContainer.cpp:475, 869-905 -> GUIMediaWindow.cpp:306-313 OnPopupMenu). Applies to video, music, pictures, programs, add-on and PVR windows. Long-press on an item does work (touchscreen.xml <longpress>RightClick</longpress>), but nothing tells the user.

**Proposed fix:** In skin.arthuros/xml/Includes_Media.xml (hand-maintained source), change button 9501 to:
  <onclick>SetFocus(50)</onclick>
  <onclick>Action(ContextMenu)</onclick>
In these media windows, CGUIMediaWindow::OnMessage(GUI_MSG_SETFOCUS) sends a SetFocus on any view id (50/51/52) to whichever view is current. That container then gets ACTION_CONTEXT_MENU, and CGUIBaseContainer::OnClick sends GUI_MSG_CLICKED, which opens OnPopupMenu for the selected item. The proposed conditional SetFocus(50)/(51)/(52) version also works but is not needed. Then rebuild so tallpass.py regenerates xml768. Add an audit.sh check that every id="9501" button in xml/ and xml768/ has a SetFocus(5x) onclick before Action(ContextMenu). Vince should test on the box: on each media screen (videos, music, add-ons, PVR), select an item, tap Options, and check that the context menu opens for that item.

### T-2 [high] Task-bar 'Now playing' button runs both ActivateWindow(FullscreenVideo) and ActivateWindow(Visualisation): during a video it lands on the music visualisation, and games go wrong

**What you see:** Tapping the 'Now playing' button on the task bar while a video plays takes you to a black music visualisation screen instead of back to the video; with a game it goes to the wrong window.

**Where:** `skin.arthuros/xml/Includes_Chrome.xml:126-137 (button 9101, two unconditional onclicks; image always icons24/audio.png at 134-137) - hand-maintained`; `skin.arthuros/xml768/Includes_Chrome.xml:131-132`; `skin.arthuros/xml768/Home.xml:1079-1086`; `audit.sh:51 (asserts that the buggy ActivateWindow(Visualisation) line exists)`

**Why (evidence):** Both onclicks are unconditional and run in order (CGUIAction::ExecuteActions, synchronous). ActivateWindow calls CGUIWindowManager::ActivateWindow_Internal (GUIWindowManager.cpp:792-802), which sends GUI_MSG_WINDOW_INIT with param1 = currentWindow (here FULLSCREEN_VIDEO). CGUIWindowVisualisation::OnMessage (GUIWindowVisualisation.cpp:153-163) only backs out when param1 == WINDOW_INVALID && !IsPlayingAudio(), so with a video playing it stays on the visualisation with the video hidden (MusicVisualisation.xml has no videowindow). CGUIWindowFullScreen::OnMessage likewise only backs out on WINDOW_INVALID (l.204), so with music it briefly opens fullscreen video first; for a game, FullscreenVideo then Visualisation. Kodi's own choice is CGUIWindowManager::SwitchToFullScreen (GUIWindowManager.cpp:962-985: game, then video, then audio), reached with Action(FullScreen) (ACTION_SHOW_GUI, Application.cpp:933-944), which title-bar box 9902 already uses.

**Proposed fix:** Edit skin.arthuros/xml/Includes_Chrome.xml (hand-maintained) and replace the two onclicks of button 9101 with a single `<onclick>Action(FullScreen)</onclick>`. Kodi's SwitchToFullScreen then picks FullscreenGame, FullscreenVideo or Visualisation. Make the same change in xml768/Includes_Chrome.xml if that file is hand-copied. Otherwise regenerate xml768 via build.sh/tallpass.py, which also refreshes the expanded copy in xml768/Home.xml. Do not hand-edit xml768/Home.xml.

Optional: make the icon conditional. Use two images, icons24/video.png with `<visible>Player.HasVideo</visible>` and icons24/audio.png with `<visible>!Player.HasVideo</visible>`, or a $VAR texture. Add a game icon under Player.HasGame if one exists in media.

Update audit.sh:51 to `grep -A6 'id="9101"' $S/xml/Includes_Chrome.xml | grep -q "Action(FullScreen)"`. Also add a check that neither ActivateWindow(FullscreenVideo) nor ActivateWindow(Visualisation) appears in the 9101 block.

### T-3 [high] While any dialog is open the task-bar Back button is dead; the only visible close is a 22x22 box

**What you see:** When a pop-up box is open, the Back button on the task bar stops working, and the only close button is a tiny x right next to a button that throws you back to the desktop.

**Where:** `skin.arthuros/xml/Includes_Chrome.xml:247-273 (Back 9105, task bar of the underlying window)`; `skin.arthuros/xml/Includes_Chrome.xml:454-525 (Win_Boxes_dialog: 9901/9902/9903 all 22x22, 2 px apart)`; `skin.arthuros/xml/Includes_Dialogs.xml:8-13 (Dialog_Dim, full-screen image only)`; `skin.arthuros/xml/DialogTextViewer.xml, DialogVideoInfo.xml, DialogMusicInfo.xml, DialogPVRInfo.xml, DialogAddonInfo.xml, DialogPictureInfo.xml, DialogPlayerProcessInfo.xml, PlayerControls.xml (no Close/Cancel button of their own)`

**Why (evidence):** CGUIWindowManager::HandleAction (GUIWindowManager.cpp:1162-1201) hands every action, taps included, to the topmost modal dialog and returns false when that dialog doesn't handle it, so the underlying window's task bar never sees the tap, though it is still drawn dimmed under Dialog_Dim. A tap on empty dialog space is ignored too (CGUIWindow::OnMouseEvent handles only RIGHT_CLICK). Hidden alternatives: a long-press of at least 500 ms (TOUCH_HOLD_TIMEOUT, GenericTouchInputHandler.cpp:24) maps to RightClick (touchscreen.xml <longpress>), which CGUIWindow::OnMouseEvent turns into ACTION_PREVIOUS_MENU, which CGUIDialog::OnBack turns into Close(); a two-finger swipe left maps to Back (touchscreen.xml). Neither is shown or mentioned in the skin's help text (strings.po 31922). The visible close box is 22x22 px, about 3.3 mm on the 7" 1024x600 panel (169 ppi) and 4.2 mm on the 9.7" panel. It sits 2 px from the '_' box, whose action is Dialog.Close(all,true) + ActivateWindow(Home) (Includes_Chrome.xml:463-464), so a slightly-off tap throws away every open dialog and goes to the desktop.

**Proposed fix:** 1) Includes_Dialogs.xml, Dialog_Dim (hand-maintained), after the dim image: add a touch-only Back hotspot over the task-bar Back button.
   - A group at right 4, top 568, 116x32, with `<visible>Skin.HasSetting(touchmode) + !Skin.HasSetting(hidetaskbar)</visible>`.
   - Inside it, a button with an empty label and `<onclick>Action(Back)</onclick>`, plus the icons24/parent.png image at 8,8 16x16 and a 31994 label. Copy the geometry from Includes_Chrome.xml:247-273.
   - tallpass then moves it to top 736 in xml768. Give it no navigation (no onup/ondown) so remote focus never lands on it.
   - Check that DialogContextMenu still has no Dialog_Dim (validate.py:244 already enforces this).
2) Includes_Chrome.xml, Win_Boxes_dialog (hand-maintained): under Skin.HasSetting(touchmode), draw a larger × at the right edge (for example 40x26) and widen the gap between × and ▫ (9902).
   - Shrinking or hiding _ is optional. It is not the box next to ×.
   - Re-run textfit.py so title labels that lose width still fit.
3) strings.po 31922 (generated from en_gb by mklang.py, so edit the en_gb source): add that in a pop-up, a long-press or two-finger tap acts as Back, and that a two-finger swipe left also goes Back.
4) audit.sh: check that every expanded dialog in xml/ and xml768/ that includes Dialog_Dim has the Action(Back) hotspot at the task-bar position (568 in xml, 736 in xml768).

### T-4 [high] DialogTextViewer text can't be scrolled at all: textbox 5 has no pagecontrol, scrollbar 60 is unlinked

**What you see:** Long text windows (changelogs, add-on descriptions, logs) only show the first screenful; there's no way to scroll down to read the rest.

**Where:** `skin.arthuros/xml/DialogTextViewer.xml:3 (defaultcontrol 5), 21-27`; `skin.arthuros/xml768/DialogTextViewer.xml:135-139`; `genwindows.py:937-944`

**Why (evidence):** The textbox has no <pagecontrol>. CGUITextBox scrolls only through GUI_MSG_PAGE_CHANGE from its m_pageControl (GUITextBox.cpp OnMessage: 'if (message.GetSenderId() == m_pageControl)'). It has no OnAction and no OnMouseEvent, so neither keys, the mouse wheel nor touch pan (ACTION_GESTURE_*) move it, unlike containers and grouplists (GUIBaseContainer.cpp:805-860, GUIControlGroupList.cpp:571-588). Estuary's DialogTextViewer links them: textbox 5 <pagecontrol>3000</pagecontrol>. A link check over xml768 confirms scrollbar 60 in DialogTextViewer is referenced by no pagecontrol. With defaultcontrol 5, the keyboard can't reach the scrollbar either.

**Proposed fix:** Change genwindows.py around lines 937-944 (the DialogTextViewer body). Don't hand-edit the XML.

1. Textbox 5: add `<pagecontrol>60</pagecontrol>`.
2. Scrollbar 60: add `<onup>9902</onup>` so a keyboard or remote can reach the close button. `onleft`/`onright` 60 are harmless but not needed.
3. In the `dialog()` call, change `default="5"` to `default="60"`. This sets `<defaultcontrol>60</defaultcontrol>` and makes the chrome buttons' `ondown` point at 60. Then Up/Down pages through the text.
4. Touch: make scrollbar 60 a larger target. For example, widen it to about 30 px under the Touch-mode condition, or add an invisible wider hit area, and narrow the textbox to match (806 to about 794). Wheel, drag and pan all work on the scrollbar once it is linked.
5. Optional: add an audit.sh check that every `type="textbox"` with a sibling `type="scrollbar"` (at least DialogTextViewer.xml) has a `<pagecontrol>`. Then rebuild both xml and xml768.

### T-5 [medium] Long info texts (plot, privacy policy, confirm text, skin help) can't be scrolled by touch and are cut off at Extra-large fonts

**What you see:** Long descriptions such as film plots, the privacy policy, confirm messages and the skin's own help text get cut off and can't be scrolled with a finger; with large fonts you never see the Touch mode explanation.

**Where:** `skin.arthuros/xml/DialogVideoInfo.xml:54-58 (plot textbox 244 px, no pagecontrol)`; `skin.arthuros/xml/DialogMusicInfo.xml:54`; `skin.arthuros/xml/DialogPVRInfo.xml:54`; `genwindows.py:544-548 (shared info-dialog textbox)`; `skin.arthuros/xml/SettingsSystemInfo.xml:129-132 (textbox 30, privacy policy)`; `genwindows.py:1261-1264`; `skin.arthuros/xml/DialogConfirm.xml:37-40 (textbox 9)`; `skin.arthuros/xml/SkinSettings.xml:167-171 (help textbox 356x376, no pagecontrol, no autoscroll)`; `skin.arthuros/xml/Defaults.xml:36 (default autoscroll only when Skin.HasSetting(autoscroll))`

**Why (evidence):** CGUITextBox has no gesture or wheel handling and scrolls only through a pagecontrol (GUITextBox.cpp). None of these textboxes has one. The default <autoscroll> applies only when 'Scroll list labels' (Skin.HasSetting(autoscroll), SkinSettings.xml:82) is on, and even then the user can't control it. Kodi fills SettingsSystemInfo textbox 30 with the privacy policy (GUIWindowSystemInfo.cpp CONTROL_TB_POLICY 30). Estuary links it: <pagecontrol>60</pagecontrol> plus <autoscroll>!Control.HasFocus(60)</autoscroll>. With the ExtraLarge fontset ('small' = 24 px) the SkinSettings $LOCALIZE[31922] help stops after 'The bitmap font is only crisp'; the paragraph explaining Touch mode is never shown (render scratchpad/layout/xml-xl/SkinSettings.png).

**Proposed fix:** 1) genwindows.py info_dialog() (~544-548):
   - Narrow the plot textbox to about width 326, so a scrollbar fits inside the 520..890 well.
   - Add a scrollbar with id 61 at left 858, top 44, height 244, width 24. Widen it to 30 when touchmode or ExtraLarge is on, using the existing Height_32_XL style conditional includes or a width include.
   - Add <pagecontrol>61</pagecontrol> and <autoscroll delay="6000" time="4000" repeat="8000">!Control.HasFocus(61)</autoscroll> to the textbox.
   - Wire key navigation: onleft/onright of 61 to 9001, so keyboard users can reach it.
   - Optionally, like Estuary, put an invisible button over the plot that does SetProperty(TextViewer_Text,$ESCINFO[ListItem.Plot],home) and then ActivateWindow(1102), with DialogTextViewer showing that property. Only do this once fix 3 is in.

2) genwindows.py ~1261 (SettingsSystemInfo):
   - Add <pagecontrol>60</pagecontrol> and <autoscroll ...>!Control.HasFocus(60)</autoscroll> to textbox 30.
   - Make it about 30 px narrower and add scrollbar 60 beside it, visible only while textbox 30 is visible (Control.IsVisible(30)).

3) genwindows.py ~939-944 (DialogTextViewer, missed by the finding): add <pagecontrol>60</pagecontrol> to textbox 5. Make scrollbar 60 wider in touch/XL mode and point the defaultcontrol at it (textbox 5 cannot take focus).

4) Hand-maintained files:
   - DialogConfirm.xml: give textbox 9 <autoscroll time="3000" delay="4000" repeat="5000">true</autoscroll>, as Estuary does. A scrollbar plus pagecontrol is optional.
   - SkinSettings.xml: add a scrollbar plus <pagecontrol> to the help textbox, or at least <autoscroll delay="6000" time="4000" repeat="8000">true</autoscroll>, so the Touch mode paragraph can be reached in ExtraLarge.

5) audit.sh: flag every on-screen textbox taller than about 100 px, or with a long/dynamic label, that has neither <pagecontrol> nor an <autoscroll> that is not tied to a setting. Also flag any scrollbar id that no control's <pagecontrol> references. This would have caught the DialogTextViewer bug.

6) Optional: fix preview.py so XL=1 loads only the ExtraLarge fontset; today the last fontset in Font.xml wins.

Vince should test on the Pi with ExtraLarge fonts and touch mode on: drag the new scrollbars with a finger in System info > Privacy policy, a long film plot, and an add-on changelog in the text viewer.

### T-6 [medium] Touch mode doesn't enlarge the chrome hit targets: title-bar boxes 22 px, task-bar buttons 24 px, media toolbar 26 px, horizontal button rows 30 px

**What you see:** Even with Touch mode on, the task-bar buttons, the window close/minimise boxes and the library toolbar stay mouse-sized and are easy to miss with a finger.

**Where:** `skin.arthuros/xml/Includes_Chrome.xml:86-101,126-128,157-159,189-190,219-221 (task bar buttons 9100-9104 height 24 in a 32 px bar)`; `skin.arthuros/xml/Includes_Chrome.xml:381-448 (Win_Boxes_window 9901-9903, 22x22)`; `skin.arthuros/xml/Includes_Chrome.xml:458-522 (Win_Boxes_dialog)`; `skin.arthuros/xml/Includes_Media.xml:14-58 (toolbar grouplist 9490 and buttons 9500/2/3/4/19/9501/9502, height 26)`; `skin.arthuros/xml768/MyVideoNav.xml:188-230`; `skin.arthuros/xml/VideoOSD.xml:111-167 (rows 202/203 at 30 px)`; `genwindows.py:400-435 osd_buttons()`; `genwindows.py:1468-1473 player_controls()`; `sizepass.py (only list rows and vertical Height_N grouplist rows get the XLC +16; does not grow grouplist 9490)`

**Why (evidence):** Measured from the shipped XML with touchmode=true (preview of Home, MyVideoNav, SettingsCategory, SkinSettings; render scratchpad/layout/xml-tm/Home.png): only list and grouplist rows get taller. Task-bar buttons 9100-9104 are 24 px high (only Back 9105 is 32), the toolbar is 26 px, boxes are 22x22 with 2 px gaps, OSD/dialog button rows 30 px; tallpass keeps these sizes in xml768. Physical size: 7" 1024x600 is about 169 ppi, so 22/24/26 px is 3.3/3.6/3.9 mm; on the 9.7" 2048x1536 panel one skin px is 0.19 mm, so 4.2/4.6/5.0 mm - well under a 7-9 mm finger target. sizepass.py:113 handles list/fixedlist/wraplist; Includes_Size.xml has only Height_28..34. The x box (9903 ActivateWindow(Home) / Action(Back)) is the main way out of windows and dialogs by touch. Kodi accepts a <hitrect x y w h> on any control (GUIControlFactory.cpp:575-592), so hit areas can grow without changing the drawing. CLAUDE.md already lists 'Toolbar buttons are 26 px high - small for touch' as a known gap.

**Proposed fix:** 1. Includes_Chrome.xml (hand-maintained; edit directly, xml768 comes from tallpass). In Chrome_Taskbar, give 9100-9104 a full-bar hit area with `<hitrect x="0" y="-4" w="W" h="32"/>`, where W is each button's own width. This changes nothing visually and is safe to apply always. Alternatively, add a touchmode-conditional variant that draws them at top 0, height 32, like 9105.

2. Win_Boxes_window and Win_Boxes_dialog. Add a Skin.HasSetting(touchmode) variant that spaces the boxes 34 px apart (right 4/38/72 with 30x26 hit rects via `<hitrect>`), keeping the 22 px glyph centred. Leave at least a 6-10 px dead gap between minimise (9901) and close (9903), or hide 9901/9902 in touch mode and keep one wider close box.

3. Includes_Media.xml Media_Toolbar. Add touchmode conditional height includes for 9490 and its buttons, either 40 px or a hitrect of h=34. Shift the views group, label 12 and Media_InfoPanel down with conditional `<top>`. MyVideoNav and the other nav windows that place content under the toolbar need the same shift.

4. VideoOSD and PlayerControls (generated). In genwindows.py osd_buttons()/player_controls(), emit taller rows, or `<hitrect>` padding, under the XLC condition.

5. Optionally, have sizepass.py emit Height_N/Height_N_XL for horizontal grouplist rows too. It currently skips them.

6. Add an audit.sh check that the 9900-series boxes, the task-bar buttons and 9490 have touch-mode heights or hitrects. Then run textfit and preview.py with SET=touchmode=true in both layouts. Vince should confirm on both panels that close and minimise are no longer hit by mistake.

### T-7 [medium] Spin arrows (18x18), slider bars (150x16) and scrollbars (18 px) keep mouse sizes in Touch mode

**What you see:** In settings screens the little up/down arrows and slider bars are tiny, so changing a value by touch takes several attempts; tapping the rest of the row does nothing.

**Where:** `skin.arthuros/xml/Defaults.xml:108-132 (spincontrolex spinwidth/spinheight 18)`; `skin.arthuros/xml/Defaults.xml:157-167 (sliderex: no sliderwidth/sliderheight, so Kodi's 150x16)`; `skin.arthuros/xml/Defaults.xml:178-188 and Includes_Chrome.xml:601-615 (scrollbar width 18)`; `skin.arthuros/xml/DialogSettings.xml:64-82 (spincontrolex 9 / sliderex 13 templates used by every OSD and add-on settings dialog)`; `skin.arthuros/xml/SettingsCategory.xml (same templates)`

**Why (evidence):** CGUISpinControl::OnMouseEvent (GUISpinControl.cpp:1012-1020) changes the value only when the click hits m_imgspinUpFocus or m_imgspinDownFocus. Tapping anywhere else on the row is swallowed (returns HANDLED). Those two images are the 18x18 spinwidth/spinheight from Defaults, side by side. CGUISliderControl::OnMouseEvent reacts to a click only when m_guiBackground->HitTest(point) (GUISliderControl.cpp:705); for sliderex the bar defaults to sliderWidth=150, sliderHeight=16 (GUIControlFactory.cpp:852), and Defaults sets neither. Touch mode grows the row to 46 px through Height_30_XL but leaves the arrows and bar at their mouse sizes. Scrollbars are 18 px everywhere. Lists and grouplists can be dragged, but a textbox can only be moved by its scrollbar.

**Proposed fix:** In sizepass.py, next to conditional_height(), add a pass for every control of type spincontrol, spincontrolex or sliderex, in both XMLDIR=xml and XMLDIR=build768. It appends two includes: content="SpinSize_XL" condition=XLC and content="SpinSize" condition="!XLC" (and SliderSize_XL / SliderSize for sliderex).

Write those include definitions to Includes_Size.xml from the same generator:
- SpinSize: 18x18
- SpinSize_XL: 34x34
- SliderSize: 150x16
- SliderSize_XL: about 240x28, so the label and value text still fit in the 600-wide SettingsCategory row (check with textfit.py).

This works because Kodi gives the control's own tags priority over Defaults, and Defaults.xml stays unconditional. Spinposx 8 still holds, since the arrows start at right - 2*spinwidth - spinposx.

Do not just widen textbox scrollbars. First have genwindows.py (DialogTextViewer, DialogVideoInfo, DialogMusicInfo, DialogAddonInfo, DialogPVR*Info and the other textbox-plus-scrollbar pairs) and the hand-maintained windows emit <pagecontrol>ID</pagecontrol> on each textbox that has a scrollbar beside it; file this as a separate high-severity finding. Then make Arthur_Scrollbar and the generated scrollbars 30 wide under XLC through a sizepass include (Width_18 / Width_18_XL), and adjust the textbox width to match.

Add audit.sh checks for:
- the SpinSize and SliderSize includes on every spin and slider template
- every textbox that has an adjacent scrollbar declaring a pagecontrol

### T-8 [medium] On-screen keyboard never shows what it is asking for: Kodi writes the heading to label 311, which is parked off-screen, and title-bar id 1 stays empty

**What you see:** When the on-screen keyboard pops up (to type a Wi-Fi password, a search, a name), it never says what you're supposed to type.

**Where:** `skin.arthuros/xml/DialogKeyboard.xml:16 (Dialog_Heading = label id 1, never set)`; `skin.arthuros/xml/DialogKeyboard.xml:20-23 (label 311 at left -3000)`; `skin.arthuros/xml768/DialogKeyboard.xml:135`; `genwindows.py:726-733 keyboard_window()`; `genwindows.py:775 dialog(..., heading defaults True)`

**Why (evidence):** xbmc/dialogs/GUIDialogKeyboardGeneric.cpp:60 #define CTL_LABEL_HEADING 311; OnInitWindow (l.204-209) does SET_CONTROL_LABEL(CTL_LABEL_HEADING, m_strHeading); SET_CONTROL_VISIBLE/HIDDEN(CTL_LABEL_HEADING). Nothing in the class writes control 1, so the Dialog_Heading label on the title bar stays empty and the real heading is drawn at x=-3000. Estuary shows 311 as the visible heading. Key sizes themselves are fine for touch (62x40 letter keys, 34-36 px function keys, 900x354 centred).

**Proposed fix:** In genwindows.py keyboard_window(), replace the off-screen 311 block with an on-screen title-bar label:
  <control type="label" id="311"><left>29</left><top>3</top><width>794</width><height>26</height><font>chromebold</font><textcolor>titletext</textcolor><align>left</align><aligny>center</aligny></control>
Put it after the Dialog_Box include so it draws above the title bar. Then call dialog("DialogKeyboard", 900, modrow + 86, body, default="300", icon="icons24/file.png", heading=False) so the empty id-1 label is no longer emitted. Rebuild so that both xml/ and xml768/ are regenerated.
Also correct the comment in Includes_Dialogs.xml:44 (or the generator that produces it): the keyboard uses 311, not id 1.
Optionally, add an audit.sh check that fails if label 311 in DialogKeyboard.xml has <left>-3000.

### T-9 [medium] Context menu shows at most 8 entries in Touch mode, the rest clipped with no scrollbar (also in the 768 layout)

**What you see:** In Touch mode the options menu for an item shows only the first eight choices, with no sign that more exist below.

**Where:** `skin.arthuros/xml/DialogContextMenu.xml:19-26 (grouplist 996 height 392, no pagecontrol/scrollbar)`; `skin.arthuros/xml768/DialogContextMenu.xml:119-121 (still 392)`; `genwindows.py:823-845 (small_dialogs DialogContextMenu)`

**Why (evidence):** CGUIDialogContextMenu::SetupButtons (dialogs/GUIDialogContextMenu.cpp:114-170) clones the template button into grouplist 996 and sizes background 999 to m_backgroundImageSize - Size() + GetHeight(). CGUIControlGroupList::GetHeight clamps to m_height (GUIControlGroupList.cpp:357-361), so the menu stops at 392 px. In Touch mode the rows are 46+2 px (Height_30_XL), so 8 entries fit. Library and add-on context menus regularly have more. The grouplist can be dragged (GUIControlGroupList.cpp:571-588), but nothing shows that more entries exist. tallpass leaves <coordinates> windows alone, so the 768 layout gets no extra room either.

**Proposed fix:** Change genwindows.py small_dialogs() (DialogContextMenu), not the shipped XML:
1. Raise grouplist 996 and image 999 to fill most of the screen. For the 600 layout use 996 height 520 (999 height 568 = 38 + 520 + 10). CGUIDialogContextMenu::SetupButtons shrinks 999 back down to fit short menus, so small menus keep their size. For xml768, tallpass.py skips <coordinates> windows, so add a narrow special case there for DialogContextMenu: add DY (168) to the heights of 996 and 999 only. Leave every left/top unchanged, because 999 must stay at 0,0 as validate.py requires.
2. Add a vertical scrollbar, id 997, at left W-22 (about 358), top 38, width 14, height matching 996. Narrow 996 and the template button 1000 to about W-34 (346), and add <pagecontrol>997</pagecontrol> to 996. CGUIControlGroupList::Process sends GUI_MSG_LABEL_RESET/ITEM_SELECT to the page control, so the scrollbar fills and moves with the list. Give it <visible>Control.IsVisible(997)</visible> or rely on the scrollbar's own auto-hide (showonepage false) so it only appears when the list overflows.
3. Rebuild, then check with preview.py (SET="touchmode", for both RES=xml and RES=xml768) and on the device with a long library context menu.

### T-10 [medium] Skin settings list overflows in Touch mode with no scrollbar; Customise desktop, Back up, Restore and Defaults sit below the fold

**What you see:** In Touch mode the Skin settings page cuts off halfway; Customise desktop, Back up, Restore and Defaults are hidden below the bottom with nothing showing you can scroll.

**Where:** `skin.arthuros/xml/SkinSettings.xml:48-161 (grouplist height 396, 14 rows, no pagecontrol)`; `skin.arthuros/xml768/SkinSettings.xml:206-317 (grouplist height 564)`

**Why (evidence):** The grouplist holds 14 rows (ids 100-113 and label 105). In Touch mode rows use Height_32_XL=48 and Height_28_XL=44 (Includes_Size.xml:5,9): 13x48 + 44 + 13 gaps x 4 = 720 px against 396 px (600) or 564 px (768). Preview (SET=touchmode=true; scratchpad touch/SkinSettings.png) shows only the first ~7 rows, cut after the second pointer option. At 768, Back up (offset 568), Restore (620) and Defaults (672) are fully below the visible area; hidden rows include Customise desktop (110), Backup/Restore (111/112) and Defaults (104). CGUIControlGroupList::OnMouseEvent (GUIControlGroupList.cpp:546-590) scrolls on ACTION_GESTURE_PAN, but nothing on screen shows there is more.

**Proposed fix:** Edit skin.arthuros/xml/SkinSettings.xml by hand; it is hand-maintained, and tallpass rebuilds xml768.

1. Give the grouplist an id, e.g. 99, and add `<pagecontrol>98</pagecontrol>`.
2. Narrow the grouplist and its 14 children from 560 to 536 px.
3. Add `<include content="Arthur_Scrollbar"><param name="id" value="98"/></include>` at left 562, top 116, height 396 (the grouplist's height), with onleft 100 and onup/ondown 9100. Make it 30 px wide in Touch mode, e.g. a conditional width, as other touch scrollbars in the skin do. Also add onright 98 to the grouplist.

This matters in normal mode at 600 as well, not only in Touch mode, because the list is 496 px against a 396 px box. A simpler alternative is to move Back up, Restore and Defaults (111/112/104) out of the grouplist into a short button row under the help textbox (left 600), so the list fits: 11 rows x48 + 44 + gaps is about 612 in Touch mode, so the scrollbar is still needed there, but normal mode at 600 would then fit. After the change, check that the xml768 output has the scrollbar stretched to 564. Add an audit.sh check that the SkinSettings grouplist declares a pagecontrol whose id exists in the window.

### T-11 [low] Title-bar 'fullscreen' box is dead in every dialog

**What you see:** The square 'full screen' box in pop-up title bars looks usable while something is playing, but tapping it does nothing.

**Where:** `skin.arthuros/xml/Includes_Chrome.xml:478-488 (Win_Boxes_dialog 9902: enable Player.HasMedia, onclick Action(FullScreen))`

**Why (evidence):** Action(FullScreen) is ACTION_SHOW_GUI. In CApplication::OnAction, SwitchToFullScreen picks the player window and calls ActivateWindow(windowID) (GUIWindowManager.cpp:980-987). ActivateWindow_Internal then refuses because a modal dialog is open ('Activate of window ... refused because there are active modal dialogs', GUIWindowManager.cpp after the IsDialog branch). Only the video/music info dialogs are closed first (SwitchToFullScreen:938-960). Over fullscreen video (the OSDs), SwitchToFullScreen returns false and the modal OSD ignores the action. The box is drawn enabled whenever something plays.

**Proposed fix:** Edit the hand-maintained skin.arthuros/xml/Includes_Chrome.xml (Win_Boxes_dialog, button 9902 and its three icon images), then rebuild so xml768 is regenerated:
- Define a condition `[Player.HasMedia + !Window.IsActive(fullscreenvideo) + !Window.IsActive(visualisation) + !Window.IsActive(fullscreengame) + !Window.IsActive(slideshow)]`.
- Use it as the button's `<enable>`.
- Use it in the visibility of the normal (non-focused) wc_max_g image, in place of `Player.HasMedia`. Use its negation for the dim wc_max_dg image, in place of `!Player.HasMedia`.
- Change the onclick to `<onclick>Dialog.Close(all,true)</onclick><onclick>Action(FullScreen)</onclick>`.

With this condition the box is disabled in VideoOSD, MusicOSD, GameOSD, DialogFullScreenInfo, PlayerControls and the other dialogs over a player window. Without it, closing the OSD and then sending FullScreen would hit CGUIWindowFullScreen::OnAction ACTION_SHOW_GUI, call PreviousWindow() and drop the user out of the video. Over normal windows the box closes the dialogs, then switches to the player window.

Add an audit.sh check that Win_Boxes_dialog 9902 carries Dialog.Close(all,true) and the !Window.IsActive(fullscreenvideo) guard.

### T-12 [low] Touch mode with 'Hide the task bar' on removes the only Back button and leaves Down navigation pointing at hidden controls

**What you see:** If you turn on both Touch mode and 'Hide the task bar', there's no Back button left on screen.

**Where:** `skin.arthuros/xml/Includes_Chrome.xml:84 (<visible>!Skin.HasSetting(hidetaskbar)</visible> on the whole task bar, Touch-mode Back 9105 at 244-273 included)`; `skin.arthuros/xml/SkinSettings.xml:61-68 (radiobutton 101 'Hide the task bar'), radiobutton 113 'Touch mode'`

**Why (evidence):** Back 9105 (Action(Back), described in string 31922 as the Touch-mode Back button) lives inside the task-bar group hidden by hidetaskbar. The two settings are independent toggles, and SkinSettings gives no warning. Every window's <ondown>9100</ondown> then points at a hidden control. The remaining exits are the 22x22 close box (which goes Home, Includes_Chrome.xml:435) and the undocumented long-press.

**Proposed fix:** Edit the hand-maintained skin.arthuros/xml/Includes_Chrome.xml, then run build.sh so xml768 is regenerated.

Do not re-show the whole task bar in Touch mode. That would quietly override the user's hidetaskbar choice. Instead, add a stand-alone Back control after the Chrome_Taskbar group, inside the same include definition but outside the hidden group:

`<control type="group"><right>4</right><top>568</top><width>116</width><height>32</height><visible>Skin.HasSetting(touchmode) + Skin.HasSetting(hidetaskbar)</visible>`
- a panel_chrome.png background image
- `<control type="button" id="9106">` with `<onclick>Action(Back)</onclick>` and `<onup>$PARAM[up]</onup>`
- the parent.png icon and the 31994 label, with the same focus/unfocus label pair as 9105

Use a new id (9106), not 9105, because the two can exist in the same window.

Also, in skin.arthuros/xml/SkinSettings.xml, give radiobutton 101 a label2 or hint so it is clear that Touch mode keeps a floating Back button. Disabling 101 while Touch mode is on is an acceptable alternative, but it is a worse experience.

Optionally, update string 31922 in language/resource.language.en_gb/strings.po to mention long-press on empty space = Back. Add an audit.sh check that a touchmode+hidetaskbar Back control exists in Includes_Chrome.xml.

### T-13 [low] File browser thumbnail view (451) keeps 26 px rows in Touch mode

**What you see:** When picking a picture file (e.g. a custom tile image), the file list rows stay small in Touch mode.

**Where:** `skin.arthuros/xml/FileBrowser.xml:113-140 (panel 451, itemlayout/focusedlayout height 26, no XL pair)`; `genwindows.py:1095 (file browser views)`; `sizepass.py:113 (only list/fixedlist/wraplist get the XL layout pair)`

**Why (evidence):** CGUIDialogFileBrowser switches to CONTROL_THUMBS 451 when browsing for images (dialogs/GUIDialogFileBrowser.cpp:443: m_browsingForImages && CAutoSwitch::ByFileCount, then CONTROL_THUMBS). Panel 451 is a single-column 848x26 layout that sizepass skips because its type is 'panel'. It is the only on-screen container without a touch-height layout (row-height scan of xml/).

**Proposed fix:** Fix this in sizepass.py, the script that adds the XL layout pairs. Do not hand-edit FileBrowser.xml.

In the container loop, also accept a vertical panel when its row layouts span the whole width, for example:

```python
t = c.get("type")
if t not in ("list","fixedlist","wraplist") and not (t == "panel" and all(l.get("width") == c.findtext("width") for l in c if l.tag in ("itemlayout","focusedlayout"))):
    continue
```

This only matches FileBrowser 451 today. Rebuild afterwards so build768/xml768 pick it up.

Alternative: give the 450/451 template in genwindows.py file_browser() an explicit XLC itemlayout/focusedlayout of height 42, placed first. The sizepass rule is more general.

### T-14 [low] mousewatch.py starts only from Home: if Kodi starts in another window, the pointer stays hidden with a mouse attached

**What you see:** If Kodi is set to start somewhere other than the desktop, a plugged-in mouse has no visible pointer until you visit the desktop.

**Where:** `skin.arthuros/xml/Home.xml:44 (only automatic start of mousewatch.py)`; `skin.arthuros/xml/Startup.xml:3`; `skin.arthuros/xml/Variables.xml:30-43 (PointerTex empty while touchmode + arthuros.mouse empty)`; `skin.arthuros/scripts/mousewatch.py`

**Why (evidence):** PointerTex/PointerClickTex return no texture while Skin.HasSetting(touchmode) and Window(Home).Property(arthuros.mouse) is empty. Only mousewatch.py sets that property, and it is started from Home's onload or the Skin settings toggle (SkinSettings.xml:91). Startup.xml goes straight to ReplaceWindow($INFO[System.StartupWindow]), so with a start-up window other than Home (Settings > Interface > Startup window) the script never runs until Home is visited. The script itself is sound: it reads REL_X|REL_Y bits from the last word of 'B: REL=', and its guard and cleanup look right.

**Proposed fix:** In genwindows.py (the out["Startup"] string around line 1004), add this line before the existing ReplaceWindow onload: "  <onload condition=\"Skin.HasSetting(touchmode) + String.IsEmpty(Window(Home).Property(arthuros.mousewatch))\">RunScript(special://skin/scripts/mousewatch.py)</onload>\n". The resulting `<window>` block reads:

  <onload condition="Skin.HasSetting(touchmode) + String.IsEmpty(Window(Home).Property(arthuros.mousewatch))">RunScript(special://skin/scripts/mousewatch.py)</onload>
  <onload>ReplaceWindow($INFO[System.StartupWindow])</onload>

Keep the Home.xml onload in home.py, because Startup does not run again after ReloadSkin. Also update the mousewatch.py header comment ("Started from Home ...") to mention Startup.

## Missing or wrong text

| # | Sev | Problem |
|---|---|---|
| S-1 | high | Numeric keypad keys show Kodi menu names ("Programs", "Pictures" ... "Kodi media center") instead of the digits 0-9 |
| S-2 | high | Add/Edit media source dialog: Browse, Add, Remove and Set content buttons are blank and the Name field has no caption |
| S-3 | high | generic() emits caption-less buttons: PVR Channel/Group manager, Guide search, Smart playlist editor/rule, Profiles, Event log, Login screen, Video versions manager, TV guide toolbar are columns of blank buttons (some off-screen) |
| S-4 | medium | inventory.py copies Estuary's own controls as Kodi ids, so generic windows get dead blank buttons (TouchBackButton 799, LoginScreen power 20, EventLog 501, PVR quick-nav 100-105/302, unused PVR toggles) |
| S-5 | medium | Slider dialog (audio/subtitle delay, amplification) has two blank buttons that do nothing |
| S-6 | low | Power menu shows "Lock settings" for the master-mode toggle |
| S-7 | low | Toolbar sort Order button never shows Ascending/Descending, both panel views read 'View: Icons', long sort names are cut off, and the file browser 'Mirror image' toggle (416) is blank |
| S-8 | low | Now-playing text shows a dangling ' - Title' with no artist and is blank for games/many streams; task-bar now-playing button always shows the speaker icon |
| S-9 | cosmetic | TV guide window titled "Channel"; hard-coded English "Start" and "OK"; unused skin strings |

### S-1 [high] Numeric keypad keys show Kodi menu names ("Programs", "Pictures" ... "Kodi media center") instead of the digits 0-9

**What you see:** The number pad used for PINs, times and dates shows words like 'Programs', 'Pictures', 'Music' on its keys instead of the numbers 0-9.

**Where:** `skin.arthuros/xml/DialogNumeric.xml:30-82 (<label>7</label> ... <label>0</label>)`; `skin.arthuros/xml768/DialogNumeric.xml:144-196`; `genwindows.py:787 numeric_window() labels = {10:"0",11:"1",...}`; `validate.py / textfit.py / preview.py (treat bare numeric labels as literal text)`

**Why (evidence):** Kodi Omega xbmc/guilib/GUIControlFactory.cpp CGUIControlFactory::GetInfoLabelFromElement(): `if (StringUtils::IsNaturalNumber(label)) label = g_localizeStrings.Get(atoi(label.c_str()));`, so <label>7</label> becomes string #7. In vendor/kodi/strings.po: #0 Programs, #1 Pictures, #2 Music, #3 Videos, #4 TV guide, #5 Settings, #6 Kodi GIT, #7 File manager, #8 Weather, #9 Kodi media center. GUIDialogNumeric.cpp only writes heading id 1 and input label 4. It never relabels keys 10-19, so the skin's text is what shows. preview.py draws the digits, which is why the bug went unnoticed. textfit.py also measures "7" rather than "File manager", and "Kodi media center" in font big does not fit a 100 px key.

**Proposed fix:** In genwindows.py numeric_window() (around line 787), change the digit labels to match Estuary: `labels = {10+n: f"$LOCALIZE[{12310+n}]" for n in range(10)}`, plus `21:"$LOCALIZE[186]"` and `23:"&lt;-"`. Writing `f"$NUMBER[{n}]"` works just as well. Then rerun build.sh so both xml/ and xml768/ DialogNumeric.xml are regenerated.

Extend validate.py's bare-number check (currently line 270, item properties only) to every `<label>`, `<label2>` and `<altlabel>` element. Any whose stripped text passes str.isdigit() should be an error saying "bare number is read as a string id - use $NUMBER[n] or $LOCALIZE[id]". Update CLAUDE.md:140 so the rule covers labels as well as item properties.

textfit.py and preview.py should resolve a bare-number label through strings.po, the same way Kodi does, so the previews show what Kodi actually displays.

### S-2 [high] Add/Edit media source dialog: Browse, Add, Remove and Set content buttons are blank and the Name field has no caption

**What you see:** When adding a video or music folder, the Browse, Add, Remove and 'Set content' buttons are blank and the name box has no caption, so you have to guess what each does.

**Where:** `skin.arthuros/xml/DialogMediaSource.xml:68-76 (buttons 11,13,14 empty; edit 12 no label; button 20 empty)`; `skin.arthuros/xml768/DialogMediaSource.xml:178-186`; `genwindows.py:1197-1209 media_source()`

**Why (evidence):** xbmc/dialogs/GUIDialogMediaSource.cpp defines CONTROL_PATH_BROWSE 11, CONTROL_NAME 12, CONTROL_PATH_ADD 13, CONTROL_PATH_REMOVE 14 and CONTROL_CONTENT 20 (l.49-52, 85-90). Its only label writes are SET_CONTROL_LABEL2(CONTROL_NAME, m_name) (l.474) and the heading 2 (l.546), so 11/13/14/20 never get text and the edit shows only its value. Estuary labels them $LOCALIZE[1024] Browse, [15019] Add, [1210] Remove, [1022] 'Enter a name for this media source.', [20333] Set content, plus caption [1021] above the paths. Preview (xml768; grid/xml768-n-04.png) shows three blank buttons, a blank edit and a blank full-width button.

**Proposed fix:** In genwindows.py media_source():
1. Add labels to the three buttons:
   - `<control type="button" id="11">…<label>$LOCALIZE[1024]</label></control>`
   - `<control type="button" id="13">…<label>$LOCALIZE[15019]</label></control>`
   - `<control type="button" id="14">…<label>$LOCALIZE[1210]</label></control>`
2. Do not give control 20 a label. Kodi always hides it (GUIDialogMediaSource::UpdateButtons, SET_CONTROL_HIDDEN(CONTROL_CONTENT)). Delete it, or move it off-screen and keep it only as a navigation stub. Then point edit 12's ondown and the OK/Cancel grouplist's onup straight at 18 and 12.
3. Use the 32px slot freed by removing 20 to add a caption for the name field, as Estuary does:
   - A caption label `<control type="label"><left>13</left><top>286</top><width>654</width><height>26</height><font>small</font><label>$LOCALIZE[1022]</label></control>`.
   - Move edit 12 down to about top 318.
   - Alternatively, give edit 12 a short left label of `<label>$LOCALIZE[551]</label>` ("Name"); Kodi writes the value into label2.
4. Optional, if the height allows: add a caption label $LOCALIZE[1021] above the path list, either by shrinking the list well by about 26px or by putting it in the heading row.
5. Re-run build.sh so the xml/ and xml768/ outputs (including the touch itemlayout variants added after generation) are regenerated.
6. Add an audit.sh check that DialogMediaSource buttons 11, 13 and 14 have a non-empty <label>.

### S-3 [high] generic() emits caption-less buttons: PVR Channel/Group manager, Guide search, Smart playlist editor/rule, Profiles, Event log, Login screen, Video versions manager, TV guide toolbar are columns of blank buttons (some off-screen)

**What you see:** Many screens (TV channel and group managers, guide search, smart playlist editor, profiles, event log, video versions) are just columns of empty buttons with no words on them, some options are off the bottom of the screen, and several buttons do nothing.

**Where:** `genwindows.py:1479-1559 generic() (l.1507-1511 writes press controls with width/height only, never a label; 'for cid, ct in sorted(press)[:18]' truncation; only sorted(lists)[0] placed, other lists stubbed at 1552)`; `skin.arthuros/xml/DialogPVRChannelManager.xml:25-90 (4,5,6,7,8,9,12,13,14,30,31,34,35 unlabelled)`; `skin.arthuros/xml/DialogPVRGroupManager.xml:25-55 (25-29,34,35 unlabelled), :103-112 (lists 12 and 13 at left -3000)`; `skin.arthuros/xml/DialogPVRGuideSearch.xml:25-115 (9-26 no captions; 27-31 at -3000, :124-136)`; `skin.arthuros/xml/SmartPlaylistEditor.xml:25-80 (12,16-24; 20 OK, 21 Cancel at :57/:62)`; `skin.arthuros/xml/SmartPlaylistRule.xml:42-60 (17,18 OK,19 Cancel,20 Browse)`; `skin.arthuros/xml/SettingsProfile.xml:32-42 (4,5; dead 799)`; `skin.arthuros/xml/LoginScreen.xml:32-41 (20, 799; Kodi labels 2/3 absent)`; `skin.arthuros/xml/EventLog.xml:33-62 (4,20,501,799)`; `skin.arthuros/xml/DialogVideoManager.xml:25-64 (21-28, no labels, no visibility conditions)`; `skin.arthuros/xml/MyPVRGuide.xml:37-102 (4,5,6,7,8,10,31)`; `skin.arthuros/xml/DialogPVRGuideControls.xml:25-54`

**Why (evidence):** In each window the Kodi source writes no caption on these ids. GUIDialogPVRChannelManager.cpp:50-64: OK 4, Apply 5, Cancel 6, Active 7, Name 8 (only LABEL2, l.788), Logo 9, Use EPG 12, EPG source 13 (values only), Parental lock 14, Group manager 30, New channel 31, TV/Radio 34, Refresh logos 35. GUIDialogPVRGroupManager.cpp:44-56 labels only 20/21/22 (l.616-622); lists 11/12/13 must all be on screen but generic() stubs 12 and 13. GUIDialogPVRGuideSearch.cpp:31-53 only sets values/label2/selected; generic() caps press controls at 18 so 27 (ignore recordings), 28 Defaults, 29 Save, 30, 31 are off-screen, and 18 rows of 46 px overflow the 408 px grouplist. GUIDialogSmartPlaylistEditor.cpp:33-48 only LABEL2 on 12/16-19/22/23 and heading 2; OK 20/Cancel 21 blank. GUIDialogSmartPlaylistRule.cpp:32-37 labels 15/16 only; 18/19/20 blank. GUIWindowSettingsProfile.cpp:32-34,154-170: 4 login screen, 5 auto login unlabelled. GUIWindowEventLog.cpp labels 21/22 only, not 20 Clear. GUIWindowLoginScreen.cpp sets header 2 and profile 3, which ArthurOS lacks. GUIDialogVideoManager*.cpp: 21 play, 22 add version, 23 add extra, 24 rename, 25 set default, 26 remove, 27 choose art, 28 rename extra; only label 2 set; Estuary labels them 208/40014/40015/40004/40023/15015/13511/118 and shows version vs extras buttons only in their own window. GUIWindowPVRBase.h 5/6/7/8/10/31 unlabelled except 28. Estuary supplies all captions. A scan of xml768 for buttons with empty <label> and no sibling label found 120+ such controls. Renders: scratchpad/layout/grid/xml768-n-06.png (channel/group manager: 13 identical empty buttons), xml768-n-07.png (guide search), xml-n-18.png (smart playlist), xml768-n-10.png (video versions, events). Also SmartPlaylistEditor/Rule are CGUIDialogs generated as full windows because of the name-prefix test.

**Proposed fix:** All changes go in genwindows.py, because these windows are generated.

1. Add a LABELS = {window: {id: '$LOCALIZE[n]' or (label, altlabel)}} table. generic() emits <label>, plus <altlabel> for togglebuttons, for every placed pressable. For radiobutton, edit and spincontrolex the <label> is the caption and Kodi fills in the value. Core string ids:
   - ChannelManager: 4=186, 5=14070, 6=222, 7=19074, 8=19201, 9=19202, 12=19206, 13=19200, 14=19267, 30=19205, 31=19204, 34=19023/alt 19024, 35=19041
   - GroupManager: 25=19289, 29=186, 34=19174/alt 19173, 35=13315. 26/27/28 need new skin strings ("New group", "Rename group", "Delete group") in language/resource.language.en_gb/strings.po.
   - GuideSearch: 9=19133, 10=19134, 11=19135, 12=19130, 13=19131, 14=19128, 15=19129, 16=19126, 17=19127, 18=515, 19=19121, 20=19132, 21=19141, 22=19123, 23=19148, 24=19124, 27=19125, 30=19339, 31=19340, 25=222, 26=137, 28=13007, 29=190
   - SmartPlaylistEditor: 12=21433, 16=21424, 17=21427, 18=21429, 20=186, 21=222, 22=467, 23=21458
   - SmartPlaylistRule: 18=186, 19=222, 20=1024
   - EventLog: 20=192
   - SettingsProfile: 4=20096, plus a skin string for 5 (auto login)
   - VideoManager: 21=208, 22=40014, 23=40015, 24=40004, 25=40023, 26=15015, 27=13511, 28=118

2. In VideoManager, add <visible>Window.IsActive(managevideoversions)</visible> on 22/24/25 and Window.IsActive(managevideoextras) on 23/28.

3. Generate DialogPVRGuideControls with its own function, not generic(): icon buttons with onclick PVR.EpgGridControl(FirstProgramme / -12 / CurrentProgramme / +12 / LastProgramme), as in Estuary.

4. LoginScreen: add label controls 2 and 3.

5. Write dedicated layouts for these windows:
   - GroupManager: lists 11, 12 and 13 side by side, under labels 20, 21 and 22.
   - GuideSearch: two columns, with Cancel 25, Search 26, Reset 28 and Save 29 in a fixed bottom row.
   - ChannelManager and SmartPlaylistEditor: a proper layout for each.
   Remove the silent [:18] truncation, or raise an error when more pressables would be cut off.

6. Add an audit.sh/validate.py check that fails on any visible pressable with an empty <label>, unless its id is on a per-window list of ids that Kodi labels itself (checked against the C++).

7. Separately: add 'epggrid' handling so the MyPVRGuide grid 50-53 is placed on screen and listed in <views>.

### S-4 [medium] inventory.py copies Estuary's own controls as Kodi ids, so generic windows get dead blank buttons (TouchBackButton 799, LoginScreen power 20, EventLog 501, PVR quick-nav 100-105/302, unused PVR toggles)

**What you see:** Several screens (log-in, event log, playlist editor, profiles, TV guide, picture info, radio info) show extra blank buttons that do nothing when tapped.

**Where:** `inventory.py:39-43 (every Estuary id below 1000 recorded as Kodi-owned)`; `inventory.json ('799': 'radiobutton' etc.)`; `genwindows.py:1479-1512 generic() (renders every PRESSY id as a visible button with no label/onclick)`; `skin.arthuros/xml/EventLog.xml:53 (501), :58 (799)`; `skin.arthuros/xml/LoginScreen.xml:32-41 (20 and 799, no label, no onclick)`; `skin.arthuros/xml/MyMusicPlaylistEditor.xml:48`; `skin.arthuros/xml/MyPVRGuide.xml:42-117 (blank 4,5,6,7,8,10,31,100-105,302,799)`; `skin.arthuros/xml/SettingsProfile.xml:42`; `skin.arthuros/xml/DialogPictureInfo.xml:25`; `skin.arthuros/xml/DialogPVRRadioRDSInfo.xml:21-30`; `skin.arthuros/xml768/ same files (e.g. xml768/MyPVRGuide.xml:271, xml768/DialogPVRRadioRDSInfo.xml:139)`

**Why (evidence):** 799 is Estuary's TouchBackButton include (addons/skin.estuary/xml/Includes.xml ~l.1556/1578: radiobutton 799 with onclick Action(Back) or Dialog.Close(all,true)+Action(FullScreen)); no Kodi C++ window uses it. LoginScreen 20 is Estuary's power button ($LOCALIZE[31072], ActivateWindow(ShutdownMenu)); GUIWindowLoginScreen.cpp only defines 2, 3, 52. GUIWindowEventLog.cpp defines only 20/21/22. 100-105 are Estuary's PVRQuickNavItemsCommon and 302 its 'Go to playlist' (Includes_MediaMenu.xml ~l.90-115, l.206). The guide window class uses only 2/3/4, 11 and 28 (GUIWindowPVRGuide.cpp l.291, l.555-557; GUIWindowPVRBase.cpp l.292-295, l.609); 5/6/7/8/10/31 are read only by Channels/Recordings/Timers subclasses. CGUIDialogPVRRadioRDSInfo uses 10/21/60/70 (GUIDialogPVRRadioRDSInfo.cpp l.24-28); ArthurOS's copy has only 799. Checker scratchpad links-refs/blank.py lists these as visible pressables with an id, no label and no onclick.

**Proposed fix:** Target genwindows.py. inventory.json cannot be regenerated without an Estuary checkout, which vendor/ lacks.

1. In genwindows.py, near PRESSY (l.1477), add a whitelist taken from the C++ #defines:
   KODI_PRESS = {"LoginScreen": set(), "EventLog": {4,20,21,22}, "MyPVRGuide": {3,4,28}, "SettingsProfile": {4,5}, "DialogPictureInfo": set(), "DialogPVRRadioRDSInfo": {10}, "MyMusicPlaylistEditor": {6,7,8}, ...}
   Fill it in for every generic window. In generic(), build press = [(i,t) for i,t in ids.items() if t in PRESSY and i in KODI_PRESS.get(name, KODI_PRESS_DEFAULT)]. At minimum, always drop 799 and 501, and drop 5,6,7,8,10,31,100-105,302 for MyPVRGuide.
2. Add a LABELS map for Kodi-handled ids that Kodi never labels, and emit <label> for each:
   - EventLog 20 -> $LOCALIZE[192]
   - MyMusicPlaylistEditor 6/7/8 -> $LOCALIZE[183]/$LOCALIZE[190]/$LOCALIZE[192]
   - SettingsProfile 4/5 -> the login-screen and auto-login strings Estuary uses
   Check each string id in vendor/kodi/strings.po.
3. Optional LoginScreen power button: emit id 20 with <label>$LOCALIZE[13005]</label> (or whatever shutdown string strings.po gives) and <onclick>ActivateWindow(ShutdownMenu)</onclick>. Touch users at the login screen have only the list and the taskbar.
4. Rebuild, then add a check to audit.sh/validate.py: no generated window has id="799", and every visible pressable in a generic window has a <label> or is an id Kodi labels itself (e.g. EventLog 21/22, PVR 3/28).

### S-5 [medium] Slider dialog (audio/subtitle delay, amplification) has two blank buttons that do nothing

**What you see:** When adjusting audio or subtitle delay, two empty buttons appear under the slider and do nothing; they should be the - and + buttons for touch.

**Where:** `skin.arthuros/xml/DialogSlider.xml:31-32`; `skin.arthuros/xml768/DialogSlider.xml:145-146`; `genwindows.py:958-959 small_dialogs()`

**Why (evidence):** GUIDialogSlider.cpp defines only CONTROL_HEADING 10, CONTROL_SLIDER 11 and CONTROL_LABEL 12. Buttons 13/14 come from Estuary DialogSlider.xml, where they are touch minus/plus buttons: `<onclick>SetFocus(11)</onclick><onclick>Left</onclick><onclick>SetFocus(13)</onclick>` and the same with Right. ArthurOS emits `<control type="button" id="13"><width>200</width><height>30</height></control>` with no label and no onclick. Preview shows two empty buttons under the slider.

**Proposed fix:** Make the change in genwindows.py small_dialogs() (the DialogSlider body, around lines 946-961), then rebuild. Do not edit xml/ or xml768/ directly.

Replace the empty 13/14 buttons with real minus/plus buttons:

- **Button 13 (minus):**
  - `<label>-</label>`
  - `<onclick>SetFocus(11)</onclick><onclick>Action(Left)</onclick><onclick>SetFocus(13)</onclick>`
- **Button 14 (plus):**
  - `<label>+</label>`
  - `<onclick>SetFocus(11)</onclick><onclick>Action(Right)</onclick><onclick>SetFocus(14)</onclick>`

Use Action(Left)/Action(Right) rather than bare Left/Right; it is the explicit form and behaves the same.

**Layout:** either keep them in the centred grouplist below the slider, or follow Estuary and put them either side of the slider (shrink slider 11 to leave room). Either way:
- Give them a real touch size, at least 44 px high when XLC is true, not 30. If they get taller, raise the dialog height above 158.
- Narrow them from 200 px to about 60-80 px, since they only hold - and +.

**Navigation:**
- Add `<onup>11</onup>` on buttons 13 and 14.
- Add `<ondown>13</ondown>` on slider 11, so keyboard/remote users can reach them.

**Visibility:** do not hide them on `!System.GetBool(input.enablemouse)` the way Estuary does. Vince is touch-only, so they should always show; they do no harm with a remote.

### S-6 [low] Power menu shows "Lock settings" for the master-mode toggle

**What you see:** If a master lock is set, the power menu shows 'Lock settings' for a button that actually enters or leaves master mode.

**Where:** `skin.arthuros/xml/DialogButtonMenu.xml:139`; `skin.arthuros/xml768/DialogButtonMenu.xml:249`; `genwindows.py:1029 button_menu() ("$LOCALIZE[20043]", "masterlock", "mastermode", "System.HasLocks")`

**Why (evidence):** vendor/kodi/strings.po: #20043 "Lock settings", #20045 "Enter master mode", #20046 "Leave master mode". The item runs the builtin `mastermode`, which toggles master mode. Estuary DialogButtonMenu.xml uses $VAR[MasterModeLabel] (20045/20046 chosen on System.IsMaster, a real infobool: GUIInfoManager.cpp {"ismaster", SYSTEM_ISMASTER}).

**Proposed fix:** Make the change in genwindows.py button_menu(), not in the shipped XML.

Option A (no extra file):
- Replace the single masterlock tuple with two tuples:
  ("$LOCALIZE[20045]", "masterlock", "mastermode", "System.HasLocks + !System.IsMaster")
  ("$LOCALIZE[20046]", "masterlock", "mastermode", "System.HasLocks + System.IsMaster")

Option B (matches Estuary):
- In genwindows.py, change the label to "$VAR[MasterModeLabel]".
- Add this variable to the hand-maintained skin.arthuros/xml/Variables.xml:
  <variable name="MasterModeLabel"><value condition="!System.IsMaster">$LOCALIZE[20045]</value><value>$LOCALIZE[20046]</value></variable>

Either way:
- Rebuild so that xml/ and xml768/ DialogButtonMenu.xml are regenerated.
- Add an audit.sh check that fails if DialogButtonMenu.xml pairs $LOCALIZE[20043] with mastermode.

### S-7 [low] Toolbar sort Order button never shows Ascending/Descending, both panel views read 'View: Icons', long sort names are cut off, and the file browser 'Mirror image' toggle (416) is blank

**What you see:** The sort Order button never tells you whether it's ascending or descending, the Poster and Icon views both say 'View: Icons', long sort names are cut off, and the file picker has a blank, mostly greyed-out button.

**Where:** `skin.arthuros/xml/Includes_Media.xml:27-38 (button 3 sort, button id 4 label $LOCALIZE[31904]) - hand-maintained`; `skin.arthuros/xml/View_51_Poster.xml:12`; `skin.arthuros/xml/View_52_IconWall.xml:12`; `skin.arthuros/xml/FileBrowser.xml:168 (togglebutton 416 with no label)`; `skin.arthuros/xml768/FileBrowser.xml:278`; `genwindows.py:1153 file_browser()`

**Why (evidence):** CGUIMediaWindow::UpdateButtons sends SET_CONTROL_SELECTED for button 4 when descending (GUIMediaWindow.cpp:597-600) and never a label; a plain button stores m_bSelected but draws nothing different (GUIButtonControl.cpp:237-249), so it always reads 'Order'. Estuary uses a togglebutton with $LOCALIZE[584] Ascending / altlabel $LOCALIZE[585] Descending. The views have no <viewtype label=...>, so CGUIControlFactory gives both panels the default label 536 'Icons' and the list 535 'List' (GUIControlFactory.cpp:1176-1192); GUIViewControl::UpdateViewAsControl (GUIViewControl.cpp:312-332) then shows 'View: Icons' for two different views. Button 3 is relabelled 'Sort by: <method>' (GUIMediaWindow.cpp:612-614); at 190 px with textoffsetx 10 and the Large/XL chrome font only ~17 characters fit, so 'Sort by: Date added', 'Last played', 'Play count', 'Production code', 'Track number' are truncated. GUIDialogFileBrowser.cpp CONTROL_FLIP 416 (l.53, 254, 513-517) is enabled only for image browsing and never labelled; Estuary gives it $LOCALIZE[749] 'Mirror image' and visible Control.IsEnabled(416), and also hides 415 (New folder) when disabled.

**Proposed fix:** Includes_Media.xml (hand-maintained; tallpass copies it to xml768):
- Keep id 4 as a plain button and set `<label>$INFO[Container.SortOrder]</label>`. Container.SortOrder gives localized 584 "Ascending" or 585 "Descending" and the label updates every frame. Widen id 4 from 110 to 120 px so "Descending" fits in the 10 px fonts.
- Widen id 3 from 190 to 230 px. That gives 21 characters, so "Sort by: Last played" fits.
- Leave View (150) and Filter (100) alone. View at 150 px still fits a 13-character "View: Posters".
- With these widths the toolbar ends at about 806 px, so move the item-count label id 12 from left 770 / width 236 to left 816 / width 190. With the plugin button 9502 visible, the row totals about 994 px, which is under the 1000 px limit.

View_50_List.xml, View_51_Poster.xml, View_52_IconWall.xml (hand-maintained):
- View_50: add `<viewtype label="535">list</viewtype>`.
- View_51: add `<viewtype label="31800">icon</viewtype>`, with a new string 31800 "Posters" in en_gb strings.po (31800 is the next free block per CLAUDE.md).
- View_52: add `<viewtype label="31801">bigicon</viewtype>` (or `icon`), with new string 31801 "Icons" or "Icon wall".

genwindows.py file_browser():
- Emit 416 as `<control type="togglebutton" id="416"><width>200</width><height>32</height><label>$LOCALIZE[749]</label><usealttexture></usealttexture><alttexturefocus border="2" colordiffuse="select">select_bevel.png</alttexturefocus><alttexturenofocus border="2" colordiffuse="facetint">button_down.png</alttexturenofocus><visible>Control.IsEnabled(416)</visible></control>`.
- The empty `<usealttexture>` element is found before the appended Defaults tag, so Register("") returns null and the button toggles normally.
- Add `<visible>Control.IsEnabled(415)</visible>` to 415.

Better still, fix Defaults.xml (hand-maintained): replace the togglebutton default `<usealttexture>true</usealttexture>` with alttexturefocus `select_bevel.png` (colordiffuse select) and alttexturenofocus `button_down.png` (colordiffuse facetint). Every togglebutton then works without per-control overrides.

Finally, add audit.sh checks that id 4 contains Container.SortOrder, that each view file has `<viewtype`, that 416 has `$LOCALIZE[749]`, and that Defaults.xml has no `usealttexture>true`. Run textfit.py on the new widths.

### S-8 [low] Now-playing text shows a dangling ' - Title' with no artist and is blank for games/many streams; task-bar now-playing button always shows the speaker icon

**What you see:** The 'now playing' text shows a stray ' - ' before the title for radio and many streams, shows nothing for games, and the task-bar button always shows a speaker even for videos.

**Where:** `skin.arthuros/xml/Variables.xml:23-27 NowPlayingVar ($INFO[MusicPlayer.Artist] - $INFO[MusicPlayer.Title] at :25) - hand-maintained`; `skin.arthuros/xml/Includes_Chrome.xml:131-134 (9101 image icons24/audio.png for video too) - hand-maintained`

**Why (evidence):** NowPlayingVar returns VideoPlayer.Title for Player.HasVideo and 'MusicPlayer.Artist - MusicPlayer.Title' for Player.HasAudio, else empty. The literal ' - ' sits outside the $INFO, so it renders even when MusicPlayer.Artist is empty - common for internet radio, PVR radio, YouTube audio and untagged files. There is no Player.HasGame branch and no fallback to Player.Title or Player.Filename. CGUIInfoLabel supports the prefix/postfix form $INFO[MusicPlayer.Artist,, - ] (only emitted when non-empty). The task-bar button's texture is fixed to icons24/audio.png while it also covers video playback.

**Proposed fix:** Order the branches so games come first (RetroPlayer also reports Player.HasVideo):
<variable name="NowPlayingVar">
  <value condition="Player.HasGame">$INFO[Player.Title]</value>
  <value condition="Player.HasVideo + !String.IsEmpty(VideoPlayer.Title)">$INFO[VideoPlayer.Title]</value>
  <value condition="Player.HasAudio + !String.IsEmpty(MusicPlayer.Title)">$INFO[MusicPlayer.Artist,, - ]$INFO[MusicPlayer.Title]</value>
  <value condition="Player.HasMedia">$INFO[Player.Title]</value>
  <value></value>
</variable>

Add a NowPlayingIconVar to Variables.xml (Player.HasGame -> icons24/games.png, Player.HasVideo -> icons24/video.png, otherwise icons24/audio.png). Use it as `<texture>$VAR[NowPlayingIconVar]</texture>` in Includes_Chrome.xml for the 9101 image; tallpass then rebuilds xml768 by running build.sh. In genwindows.py, change the MusicVisualisation label to `$INFO[MusicPlayer.Artist]$INFO[MusicPlayer.Album, - ]`. Add an audit.sh check that fails if `"] - $INFO[MusicPlayer` appears anywhere in the skin XML.

### S-9 [cosmetic] TV guide window titled "Channel"; hard-coded English "Start" and "OK"; unused skin strings

**What you see:** The TV guide's title bar says 'Channel'; a few words are fixed in English and some skin text is never used.

**Where:** `genwindows.py:28 TITLES "MyPVRGuide":"$LOCALIZE[19029]" -> skin.arthuros/xml/MyPVRGuide.xml title`; `skin.arthuros/xml/Includes_Chrome.xml:110,116 (<label>Start</label>) - hand-maintained`; `genwindows.py:787-788 numeric_window() 21:"OK"`; `skin.arthuros/language/resource.language.en_gb/strings.po #31900 Current library, #31905 Search, #31908 Desktop, #31909 Nothing selected, #31911 Close, #31974 Shortcuts (no reference in xml/, scripts/ or addon.xml)`

**Why (evidence):** Kodi #19029 is "Channel". The window is the TV/Radio guide, for which Kodi has #22020 "Guide" (already used on the desktop) and #4 "TV guide". "Start" and "OK" are literal English, while the rest of the skin is localized and Kodi has #186 OK. A grep for each id over skin.arthuros/xml, scripts and addon.xml finds no use of the listed strings. (31907 and 31913-31916 are covered in other findings.)

**Proposed fix:** - **Guide title:** in genwindows.py, set TITLES["MyPVRGuide"] = "$LOCALIZE[22020]". This matches the desktop tile label.
- **OK button:** in genwindows.py numeric_window(), change the label for key 21 to "$LOCALIZE[186]".
- **Start button:** in the hand-maintained skin.arthuros/xml/Includes_Chrome.xml lines 110 and 116, either use a new skin string "Start" or leave the literal and accept it as branding. Per CLAUDE.md, 31999 is the last free id in the 319xx block. One of the unused ids (e.g. 31908 "Desktop") could be re-purposed instead.
- **Unused strings:** remove 31900, 31905, 31908, 31909, 31911 and 31974 from skin.arthuros/language/resource.language.en_gb/strings.po (hand-maintained), or use them where they fit. 31911 "Close" and 31905 "Search" could replace equivalent literals. Then rerun mklang.py through the build.
- **audit.sh checks:** add one check that fails when a strings.po id is not referenced in xml/, scripts/ or addon.xml. Add another that greps the shipped xml for <label> values that are plain alphabetic literals, with an allowlist.

## Functions Kodi expects but the skin does not wire up

| # | Sev | Problem |
|---|---|---|
| K-1 | critical | TV/Radio Guide has no EPG grid: epggrid 50-53 are off-screen stubs with no layouts, <views> is dropped, the window shows the channel-group list and 16 blank buttons, and some code paths can crash on the null grid |
| K-2 | high | Settings level button does nothing; add-on settings have no level button |
| K-3 | high | Media windows lack Kodi's window-specific buttons: playlist Shuffle/Save/Clear/Repeat, PVR channel group and filters, library Search/Watched filter/Party mode/Update library, picture slideshow |
| K-4 | high | Music playlist editor: the playlist being built (list 100) is off-screen and Load/Save/Clear buttons are blank |
| K-5 | medium | Screen calibration markers are invisible (movers/resize have no textures) and the calibration window is covered by chrome |
| K-6 | low | Music visualisation control has no id 2, so preset next/previous/lock actions are dropped |
| K-7 | low | Colour picker lists colour names without a swatch |
| K-8 | low | Generic dialogs send Up/Down to task-bar id 9100, which does not exist in dialogs |
| K-9 | low | validate.py / textfit.py gaps: builtins, action names, window names, RunScript targets, $VAR/$EXP, SetFocus/Container ids, infobool names, Kodi-required ids and static item labels are never checked |

### K-1 [critical] TV/Radio Guide has no EPG grid: epggrid 50-53 are off-screen stubs with no layouts, <views> is dropped, the window shows the channel-group list and 16 blank buttons, and some code paths can crash on the null grid

**What you see:** Opening the TV guide shows no programme grid at all, just a list of channel group names beside a column of blank buttons. Waking the box from sleep with the guide open may crash Kodi.

**Where:** `skin.arthuros/xml/MyPVRGuide.xml:1-6 (no <views>)`; `skin.arthuros/xml/MyPVRGuide.xml:19 (title $LOCALIZE[19029] = 'Channel')`; `skin.arthuros/xml/MyPVRGuide.xml:32-119 (buttons/radiobuttons 3,4,5,6,7,8,10,28,31,100-105,302,799 with no <label>)`; `skin.arthuros/xml/MyPVRGuide.xml:122 (list id 11 = channel-group list shown as main list)`; `skin.arthuros/xml/MyPVRGuide.xml:163-174 (epggrid 50-53 at left -3000, 200x24, no layouts)`; `skin.arthuros/xml768/MyPVRGuide.xml:99, 281, 400`; `genwindows.py:28 TITLES MyPVRGuide = 19029`; `genwindows.py:707-723 stubs()`; `genwindows.py:1476 LISTY (no 'epggrid')`; `genwindows.py:1479-1559 generic() (1558 'live = [...] if int(v) in placed' drops all views)`

**Why (evidence):** inventory.json lists MyPVRGuide views '50,51,52,53' and epggrids 50-53. generic() only places LISTY types {list,panel,fixedlist,wraplist}, so the epggrids become -3000 stubs with no channel/ruler/programme layouts and all four views are filtered out of <views> (the other 14 media windows keep theirs). Fixedlist 11 is placed as the main list; in Kodi it is CONTROL_LSTCHANNELGROUPS (GUIWindowPVRBase.h:27), so the window lists group names. CGUIMediaWindow::Load (GUIMediaWindow.cpp:132-157) adds views only from <views>, so m_viewControl is empty and CGUIWindowPVRGuideBase::GetGridControl() (GUIWindowPVRGuide.cpp:73-76) returns nullptr. InitEpgGridControl null-checks, but GotoBegin/GotoEnd/GotoCurrentProgramme/GotoDate/GotoFirstChannel/GotoLastChannel/GotoPlayingChannel/OnInputDone (l.767-875) dereference it unchecked; they are reached from GUI_MSG_SYSTEM_WAKE (l.600-602, waking from suspend with the guide open), channel-number entry, and PVR.EpgGridControl (PVRBuiltins.cpp:99-150) - a possible Kodi crash. Kodi labels only 3 (Sort by) and 28 (Group: X, GUIWindowPVRBase::UpdateButtons l.609); 100-105, 302, 700, 799 are Estuary side-blade ids. 19029 is 'Channel'; 'Guide' is 19069/19222/22020. Renders: scratchpad/layout/xml768-n/MyPVRGuide.png and scratchpad/media/guide768.png (plain list of <Label> rows + 16-18 empty buttons). Estuary ships <views>50,51,52,53</views> with real epggrid layouts.

**Proposed fix:** The proposed fix is right. Additions and refinements:

1. Write `guide_window()` in genwindows.py and register it in main() as `written['MyPVRGuide'] = guide_window()` before the generic() loop. Keep it a generated file, since CLAUDE.md lists it as one.
   - Use `<views>50</views>` and `<defaultcontrol always="false">50</defaultcontrol>`.
   - Put one epggrid id=50 on screen inside the frame (right of the button strip), modelled on Estuary's MyPVRGuide.xml:
     - timeblocks and rulerunit
     - channellayout / focusedchannellayout (ListItem.Icon logo plus ListItem.ChannelName)
     - rulerdatelayout / rulerlayout
     - programmelayout / focusedprogrammelayout (ListItem.Label plus a start-end time)
     - progresstexture
     - pagecontrol pointing at scrollbar 60
   - Size channel and programme rows with the XLC Height_ includes, so rows are at least 44px in touch mode.
   - Make sure tallpass.py stretches the grid's height for xml768 (tallpass already mentions epggrid, so check that it handles this control).
   - Keep stubs for 51-53 so SET_CONTROL_* calls still land, but leave them out of <views>.

2. Toolbar:
   - Keep list 11 as a slim, visible channel-group strip. Kodi fills it, and tapping a group switches to it.
   - Keep button 28 (Kodi labels it "Group: X").
   - Keep 3/4 only if wanted. CGUIMediaWindow labels 3; give 4 a static label.
   - Give every remaining visible button a static <label>.
   - Remove the Estuary-only ids 5-8, 10, 31, 100-105, 302 and 799 from the visible strip. Stub them only if Kodi sends them messages.
   - Add touch-friendly navigation buttons: <onclick>PVR.EpgGridControl(firstprogramme / currentprogramme / lastprogramme / -12 / +12 / selectdate)</onclick>. These are safe once grid 50 exists. Do the same for the generated DialogPVRGuideControls, which currently has no EpgGridControl calls.
   - Add an Options button that sends the context menu (Action(ContextMenu)), so touch users can reach Navigate... and Record.

3. Set `TITLES['MyPVRGuide']` to `$LOCALIZE[19069]` (or 22020).

4. Add an audit.sh check for both xml/ and xml768/MyPVRGuide.xml:
   - <views> contains 50
   - an epggrid with id 50 exists with left >= 0
   - that epggrid has a programmelayout and a channellayout
   - the title is not 19029

### K-2 [high] Settings level button does nothing; add-on settings have no level button

**What you see:** The 'Basic / Standard / Advanced / Expert' settings level button does nothing when tapped, so advanced Kodi settings stay hidden; add-on settings have no level button at all.

**Where:** `skin.arthuros/xml/SettingsCategory.xml:56-61 (button 20, no onclick)`; `skin.arthuros/xml768/SettingsCategory.xml:215`; `genwindows.py:205-226 (settings_window: button 20 and comment 'cycles the level when it is clicked')`; `genwindows.py:260+ settings_dialog() (DialogAddonSettings has no id 20)`

**Why (evidence):** xbmc/settings/windows/GUIWindowSettingsCategory.cpp only sets the label of id 20 (lines 144, 181). The level changes only on ACTION_SETTINGS_LEVEL_CHANGE in OnAction (line 129+). OnMessage has no GUI_MSG_CLICKED case for 20, and CGUIDialogSettingsBase::OnMessage (GUIDialogSettingsBase.cpp:189-214) handles only 28/29 and setting controls. Estuary's SettingsCategory.xml:146-152 uses <onclick>SettingsLevelChange</onclick>. No default keymap in system/keymaps binds settingslevelchange (ActionTranslator.cpp:199 defines the action). CGUIDialogAddonSettings uses the same id 20 and the same action (GUIDialogAddonSettings.cpp:36, 92-110, 431); ArthurOS's DialogAddonSettings has no id 20.

**Proposed fix:** 1. In genwindows.py settings_window(), add <onclick>SettingsLevelChange</onclick> to the button id="20" block. Correct the comment to say: Kodi only labels id 20, and the onclick sends ACTION_SETTINGS_LEVEL_CHANGE, which GUIWindowSettingsCategory::OnAction handles.
2. In genwindows.py settings_dialog(), when cats is true (DialogAddonSettings only), add <control type="button" id="20"><width>180</width><height>30</height><align>center</align><onclick>SettingsLevelChange</onclick></control> to grouplist 9001 next to 28, 29 and 30. Four 180 px buttons plus gaps take 744 px, which fits the 874 px row. Kodi fills in the label (GUIDialogAddonSettings.cpp ~431).
   Do not add it to the other settings dialogs. Their classes (audio, video, subtitle and similar) do not handle the action.
3. Rebuild so tallpass.py regenerates xml768/.
4. Make the audit.sh check stronger: grep -q SettingsLevelChange in both $S/xml/SettingsCategory.xml and $S/xml/DialogAddonSettings.xml.

### K-3 [high] Media windows lack Kodi's window-specific buttons: playlist Shuffle/Save/Clear/Repeat, PVR channel group and filters, library Search/Watched filter/Party mode/Update library, picture slideshow

**What you see:** There's no button to clear, save, shuffle or repeat the play queue, no way to switch TV channel groups or show hidden channels/deleted recordings by touch, and no Search, 'show watched/unwatched' or 'update library' button in the video and music libraries.

**Where:** `skin.arthuros/xml/Includes_Media.xml:13-60 (Media_Toolbar shared by every media window: only 9500,2,3,4,19,9501,9502) - hand-maintained`; `skin.arthuros/xml/MyPlaylist.xml:1-20 (only Media_Window)`; `skin.arthuros/xml768/MyPlaylist.xml`; `skin.arthuros/xml/MyPVRChannels.xml:1-20, MyPVRRecordings.xml:1-20, MyPVRTimers.xml:1-20, MyPVRSearch.xml (only Media_Window)`; `skin.arthuros/xml/MyVideoNav.xml:1-20, MyMusicNav.xml:1-20`; `skin.arthuros/xml/MyPics.xml (only Media_Window)`; `skin.arthuros/language/resource.language.en_gb/strings.po:32-34 (31905 'Search' defined, used nowhere)`; `validate.py (no check of HAND windows against Kodi ids)`

**Why (evidence):** Playlist: MyPlaylist.xml is loaded by both CGUIWindowVideoPlaylist and CGUIWindowMusicPlaylist (GUIWindowVideoPlaylist.cpp l.52, GUIWindowMusicPlaylist.cpp l.55), which act on 20 shuffle, 21 save, 22 clear, 23 play, 24 next, 25 previous, 26 repeat (GUIWindowMusicPlaylist.cpp:45-52, 136-205; 26 labelled 'Repeat: ...' l.444); their context menus (l.550-569 / Video l.495-513) offer only move/remove/party mode, so clear/save/shuffle are reachable only through these buttons. PVR: GUIWindowPVRBase.h:19-33 defines 28 channel-group button (opens group picker GUIWindowPVRBase.cpp:288-306, labelled 'Group: X' l.609), 5 group items, 6 show hidden, 7 show deleted, 8 hide disabled timers, 10 show mode, 11 group list, 31 filter, header labels 29/30; Channels uses 6/31 (GUIWindowPVRChannels.cpp:226-246), Recordings 5/7/10 (GUIWindowPVRRecordings.cpp:387-413), Timers 8 (GUIWindowPVRTimersBase.cpp:155), Search 29/30 (l.380-387). The only other way to change group is ACTION_PREVIOUS/NEXT_CHANNELGROUP (l.193-199), which no touch gesture produces; deleted recordings (trash) are reachable only via 7. Library: GUIWindowVideoNav.cpp:56-68, 181-231 handles 8 OnSearch, 10 watched-mode cycle (labelled 16100+mode l.560), 14 show all, 16 party mode, 20 scan/stop library (enabled outside plugins l.566); GUIWindowMusicNav.cpp:63-69, 130-175 handles 8 search, 16 party mode, 20 update library. grep finds no VideoLibrary.Search, UpdateLibrary or PartyMode builtin in the skin or home.py. Pictures: CGUIWindowPictures acts on 6/7/9 (slideshow, recursive, shuffle; l.53-55, 111-119), though its context menu offers slideshow. None of these ids exists in the shipped windows (idcmp.py vs inventory.json). Estuary's Includes_MediaMenu.xml:45-199 provides all of them. Note the id clash: 20 means Shuffle in playlists but Update library in nav windows, so they cannot share one toolbar.

**Proposed fix:** All target files are hand-maintained, so edit them directly, then rebuild so xml768 is regenerated.

1. Includes_Media.xml: add a second toolbar row so the new buttons don't overflow.
   - Give Media_Window an optional param, e.g. `<param name="extras" default="Media_NoExtras"/>`.
   - Inside the window group, add a grouplist id 9491 at about top 34+30 that contains `<include>$PARAM[extras]</include>`.
   - Shift the views and Media_InfoPanel down about 30px only when the row is used. Simplest: pass a param `rowtop`. Alternative: put the extras at the right end of row 1 and hide label 12 in those windows.
   - Every new control needs an explicit id.
   - Do NOT put the window-specific buttons in the shared Media_Toolbar. Id 20 means Shuffle in MyPlaylist but Update library in the Nav windows.

2. Per-window extras includes, all in Includes_Media.xml:
   - MyPlaylist: togglebutton/radiobutton 20 $LOCALIZE[191], button 21 $LOCALIZE[190], button 22 $LOCALIZE[192], button 26 (Kodi sets the 'Repeat: ...' label). Optionally 23/24/25.
   - MyPVRChannels: button 28 (Kodi sets the 'Group: X' label), radiobutton 6 $LOCALIZE[19051], radiobutton 31 $LOCALIZE[587].
   - MyPVRRecordings: 28, radiobutton 5 $LOCALIZE[19270], radiobutton 7 $LOCALIZE[19184], button 10 (Kodi sets the label).
   - MyPVRTimers: 28, radiobutton 8 $LOCALIZE[19077].
   - MyPVRSearch: labels 29/30 (cosmetic).
   - MyVideoNav: button 8 $LOCALIZE[137], button 10 (Kodi labels it), radiobutton 16 $LOCALIZE[589], button 20 $LOCALIZE[653] with visible String.IsEmpty(Container.PluginName).
   - MyMusicNav: 8, 16, 20, same as video.
   - MyPics: radiobutton 9 shuffle. 6 and 7 are optional because the context menu already has the slideshows.

3. Check the 1024 width with textfit.py, and render with preview.py at RES=xml768 as well.

4. Add an audit.sh/validate.py check that maps each HAND window to its required Kodi ids and fails if one is missing: MyPlaylist 20/21/22/26; MyPVRChannels/Recordings/Timers 28; MyPVRChannels 6; MyPVRRecordings 7; MyVideoNav/MyMusicNav 8/20.

### K-4 [high] Music playlist editor: the playlist being built (list 100) is off-screen and Load/Save/Clear buttons are blank

**What you see:** In the music playlist editor you can't see the playlist you're building, and the Load, Save and Clear buttons are blank.

**Where:** `skin.arthuros/xml/MyMusicPlaylistEditor.xml:30-52 (buttons 6,7,8 and radiobutton 799 without labels)`; `skin.arthuros/xml/MyMusicPlaylistEditor.xml:83-87 (fixedlist 100 at left -3000 with empty layouts)`; `skin.arthuros/xml768/MyMusicPlaylistEditor.xml:192, 320`; `genwindows.py:1479-1559 generic() (1517-1525 places only sorted(lists)[0] = 50)`

**Why (evidence):** CGUIWindowMusicPlaylistEditor (GUIWindowMusicPlaylistEditor.cpp:31-39) uses CONTROL_LOAD_PLAYLIST 6, SAVE 7, CLEAR 8, source list 50, CONTROL_PLAYLIST 100 (the playlist being edited, clicks handled l.65, 129) and CONTROL_LABEL_PLAYLIST 101. It labels only 12 and 101 (l.219-227, 305), never 6/7/8. generic() places only the lowest list id and stubs fixedlist 100 off-screen with empty itemlayout/focusedlayout, so the songs you add can't be seen. 799 is an Estuary-only radiobutton with no action.

**Proposed fix:** In genwindows.py, add a dedicated music_playlist_editor() writer and dispatch it before the generic() fallback (around line 1840), the way subtitles_dialog() does:

1. Left column (the narrow grey well): a vertical grouplist with:
   - button 6, label $LOCALIZE[502] (Open)
   - button 7, label $LOCALIZE[190] (Save)
   - button 8, label $LOCALIZE[192] (Clear)
   - label 12 (Kodi sets the item count in UpdateButtons)
   - optionally a small textbox hint saying "Long-press a song to add it".
2. Middle well: list 50, the source browser, built with list_block() and scrollbar 60.
3. Right well: list 100, the playlist being built.
   - Use real Arthur_ItemLayout and Arthur_FocusedLayout layouts, plus the _XL variants under the same font/touchmode condition that sizepass applies.
   - Make it a list, or keep fixedlist only with a proper focusposition.
   - Give it pagecontrol 61, with a visible scrollbar 61 beside it.
   - Put label 101 above it (Kodi fills it with "N items").
4. Navigation: 50 onright points to 100, 100 onleft points to 50, and the buttons onright point to 50.
5. Keep <views>50</views>. Leave grouplist 700 and radiobutton 799 as off-screen stubs; 799 is not handled in Kodi's playlist editor code.
6. Optionally add ids 12 and 101 (label) to the MyMusicPlaylistEditor entry in inventory.json so stubs() and the audit know about them.
7. Add an audit.sh check: a pressy control with no <label> in a generic window should fail, and so should a list id handled in C++ that sits at left -3000.

Rebuild so that both xml/ and xml768/ are regenerated.

### K-5 [medium] Screen calibration markers are invisible (movers/resize have no textures) and the calibration window is covered by chrome

**What you see:** Settings > Display > Calibrate screen shows an empty grey box; the corner and subtitle markers you're supposed to move are invisible.

**Where:** `skin.arthuros/xml/SettingsScreenCalibration.xml:38-53 (mover 8,9,10,12 and resize 11: stubs at -3000 with no texturefocus/texturenofocus)`; `genwindows.py:701-724 STUB_EXTRA/stubs()`; `genwindows.py:1477 PRESSY (no mover/resize)`

**Why (evidence):** GUIWindowSettingsScreenCalibration.cpp:38-46 uses 8 top-left, 9 bottom-right, 10 subtitles, 11 pixel ratio, 12 reset, 20 video. Kodi repositions and resizes them itself with SetPosition/SetLimits (l.325-415), so the off-screen position doesn't matter, but CGUIMoverControl and CGUIResizeControl draw only their focus/nofocus textures; the stubs have none and Defaults.xml has no <default type="mover"> or "resize". The window also draws the menu bar, frame and task bar over the area being calibrated. Render: scratchpad/layout/xml768-n/SettingsScreenCalibration.png (an empty grey frame). (Finding #108 also notes DialogPlayerProcessInfo and DialogPVRRadioRDSInfo render as empty boxes - covered by the info-dialogs group.)

**Proposed fix:** In genwindows.py, add a dedicated calibration() generator and route SettingsScreenCalibration to it instead of generic().

What the window should contain:
- A full-screen background only: no Chrome_Desktop body, menu bar, Win_Frame or Chrome_Taskbar.
- A centred title label using $LOCALIZE[214].
- Labels 2, 3 and 4 centred near the top, as in Estuary.
- A small visible touch button labelled $LOCALIZE[186] (or a Done string) with <onclick>Back</onclick>. Put it mid-screen, away from the corners, so touch-only users can leave.

Movers 8, 9, 10 and 12 and resize 11 each need:
- <texturefocus colordiffuse="select"> and <texturenofocus> textures.
- A <movingspeed acceleration="180" maxvelocity="300" resettimeout="200" delta="1"> block:
  - 8 and 9: eventconfig for up, down, left and right.
  - 10: eventconfig for up and down.
  - 11: eventconfig for left and right.
  - 12: none.

Sizes: about 128x128 for 8 and 9, 380x90 for 10 (with 40px of transparent space above and below the bar, as Estuary notes), 500x500 for 11 and 100x100 for 12.

Draw the textures in mkmedia.py or iconset.py:
- calibrate/cal_tl.png and calibrate/cal_br.png: corner arrows.
- calibrate/cal_sub.png: the subtitle bar.
- calibrate/cal_ratio.png: the pixel-ratio square or circle.
- calibrate/reset.png: the reset marker.

Also, as a safety net:
- Add STUB_EXTRA entries for "mover" and "resize" in stubs(), with fill.png textures and a full movingspeed block, so no future stub renders invisible or immovable.
- Add an audit.sh check that every mover or resize in the generated xml/ and xml768/ has both textures and a <movingspeed>.

Control id 20 is optional.

### K-6 [low] Music visualisation control has no id 2, so preset next/previous/lock actions are dropped

**What you see:** Changing or locking the music visualisation preset with the remote or keymap does nothing.

**Where:** `skin.arthuros/xml/MusicVisualisation.xml:4`; `skin.arthuros/xml768/MusicVisualisation.xml:4`; `genwindows.py:1417-1421 music_vis()`

**Why (evidence):** GUIWindowVisualisation.cpp:31 #define CONTROL_VIS 2. OnAction (l.118-121) passes visualisation actions (ACTION_VIS_PRESET_NEXT/PREV/RANDOM/LOCK, rate) through GetControl(CONTROL_VIS)->OnAction; OnMessage forwards GUI_MSG_GET_VISUALISATION / VISUALISATION_RELOAD / PLAYBACK_STARTED the same way (l.134-136). With no control 2, GetControl returns null and actions fall through to CGUIWindow::OnAction. Broadcast messages still reach an id-0 control through CGUIControlGroup::OnMessage's controlId==0 loop (GUIControlGroup.cpp:241-249), so only actions are affected; CGUIDialogVisualisationPresetList gets the vis through GUI_MSG_GET_VISUALISATION (l.87-89). Estuary uses id 2.

**Proposed fix:** In genwindows.py music_vis() (l.1419), change `<control type=\"visualisation\">` to `<control type=\"visualisation\" id=\"2\">`. Then rebuild with build.sh so tallpass.py regenerates xml768/MusicVisualisation.xml from xml/. Don't hand-edit either XML.

Optionally, add an audit.sh check that MusicVisualisation.xml's visualisation control carries id="2". If touch users should be able to change presets, add on-screen buttons separately (e.g. in MusicOSD, ActivateWindow(VisualisationPresetList)). Those buttons would also rely on id 2 for the preset list to find the visualisation.

### K-7 [low] Colour picker lists colour names without a swatch

**What you see:** When picking a colour (e.g. for subtitles) you see only colour names and hex codes, not the colour itself.

**Where:** `skin.arthuros/xml/DialogColorPicker.xml:34-52 (list 6 uses Arthur_ItemLayout)`; `genwindows.py:1479-1559 generic()`

**Why (evidence):** GUIDialogColorPicker.cpp:170-172 builds items with label = colour name and Label2 = ARGB hex. The skin has to draw the swatch (Estuary uses colordiffuse="$INFO[ListItem.Label2]"). Arthur_ItemLayout (Includes_Lists.xml:9-31) shows only Icon, Label and Label2 text.

**Proposed fix:** Fix this in genwindows.py, not in the shipped XML. Add an optional parameter, list_block(..., swatch=False). When it is true, add a swatch image inside both the <itemlayout> and the <focusedlayout>, after the Arthur_* include so it draws over the empty icon slot:
<control type="image"><left>4</left><top>4</top><width>16</width><height>16</height><texture>fill.png</texture><colordiffuse>$INFO[ListItem.Label2]</colordiffuse></control>
Use the <colordiffuse> element, as Estuary does. GUIControlFactory.cpp:977 parses that element with the list's parentID, so the ListItem info resolves per item. The texture attribute form at line 407 parses with context 0, so it may not resolve per item. Then make generic() pass swatch=True when name == "DialogColorPicker". After that, either make sure the sizepass step that adds the XL item and focused layouts (44px rows) copies the extra control with top 12, or emit the XL layouts with the swatch directly. Optionally make the swatch wider, around 40x16, and move the label right so the colour is easy to see on the touch panels. Rebuild, then check the result in xml/ and xml768/.

### K-8 [low] Generic dialogs send Up/Down to task-bar id 9100, which does not exist in dialogs

**What you see:** With a remote or keyboard, pressing Up or Down in some dialogs does nothing.

**Where:** `skin.arthuros/xml/DialogColorPicker.xml:24, DialogFullScreenInfo.xml:24, DialogPVRChannelManager.xml:24, DialogPVRGroupManager.xml:24, DialogPVRGuideControls.xml:24, DialogPVRGuideSearch.xml:24, DialogPVRRadioRDSInfo.xml:24, DialogPictureInfo.xml:24, DialogVideoManager.xml:24`; `genwindows.py:1506 generic() (hard-coded `<onup>9100</onup><ondown>9100</ondown>` even when as_dialog)`; `validate.py:137 (9100 is whitelisted, so the warning is suppressed)`

**Why (evidence):** 9100 is the Start button inside Chrome_Taskbar (Includes_Chrome.xml l.96), which only full windows include. My checker (links-refs/check.py) expands every window with its includes and finds no control 9100 in these 9 dialogs (xml and xml768). A move to a missing id does nothing (CGUIAction::GetNavigation just returns the id; the window has no such control). list_block() already uses `ondown=str(cid) if as_dialog` (genwindows.py l.1524), but the grouplist line was missed.

**Proposed fix:** In genwindows.py generic(), build the grouplist navigation from as_dialog the way list_block already does. For example: `gl_up = '9901' if as_dialog else '9100'` (9901 is the dialog close box from Win_Boxes_dialog in Includes_Chrome.xml, and it exists in both xml and xml768). Then `gl_down = (str(sorted(lists)[0][0]) if lists else str(sorted(press)[0][0])) if as_dialog else '9100'`. When there is no list, Down from the last button wraps to the first button. Emit `<onup>{gl_up}</onup><ondown>{gl_down}</ondown>`. Re-run build.sh so tallpass.py regenerates xml768. In validate.py (~l.137), only exempt 9100-9103 when the resolved window actually contains the Chrome_Taskbar ids (check that they are in ctrl_ids) rather than whitelisting them for every window, so this class of dead link gets flagged.

### K-9 [low] validate.py / textfit.py gaps: builtins, action names, window names, RunScript targets, $VAR/$EXP, SetFocus/Container ids, infobool names, Kodi-required ids and static item labels are never checked

**What you see:** Not visible on the box, but the skin's checking scripts would let several kinds of broken buttons and labels slip into a release.

**Where:** `validate.py:27-41 (includes chain but no <variable>/<expression> table)`; `validate.py:85-160 (per-window loop: textures, fonts, colours, numeric on* only)`; `validate.py:137 (hard-coded whitelist hides dead 9100/9000/9490/... targets)`; `textfit.py:65-66 (skips everything under itemlayout/focusedlayout/content)`; `windownames.txt (read by no script)`

**Why (evidence):** An ad-hoc lxml checker (scratchpad links-refs/check.py, check2.py, infocheck.py, icocheck.py, idcmp.py, blank.py) expanding every window Kodi-style for xml and xml768 confirmed the static layer is clean today: no undefined include/$VAR/$EXP, no missing or case-mismatched texture, no unknown colour, fonts identical in all 7 fontsets, all ActivateWindow/ReplaceWindow/Dialog.Close/Window(...) names in windownames.txt (matches WindowTranslator.cpp, 137 names) or Custom 1120-1126, all RunScript paths exist, all builtins exist, Skin.String/HasSetting consistent, no clashing focusable duplicate ids, no missing SetFocus/Container(n) targets apart from 9100 (EditTileName defined but unused). But nothing in the tooling would catch a regression: CLAUDE.md says 'Window names must come from windownames.txt' yet `grep -l windownames *.py *.sh` finds nothing, and validate.py has no builtin/action table, no infobool table, no check of HAND windows against Kodi ids, and whitelists 9100. The real defects found (ParentDir semantics, Player.ShowCodec, blank Estuary-private ids, missing Kodi ids in HAND windows, the PVR guide-controls dialog, 9100 in dialogs) all passed. textfit.py's docstring promises 'every fixed label fits' but static <item><label> captions (desktop catalogue, Settings hub, power menu) are never measured.

**Proposed fix:** The proposed fix is right; these changes refine it. Edit the hand-maintained tools directly, since they are not generated.

**validate.py**
1. Index `<variable name>` and `<expression name>` from every includes file. Report any `$VAR[...]` or `$EXP[...]` that is not defined.
2. Gather the action strings from onclick, onfocus, onunfocus, onload, onunload, onback, onup/ondown/onleft/onright text and `<item><onclick>`. For each one:
   - Check the builtin name before `(` against a table taken from the Omega files xbmc/interfaces/builtins/*.cpp. Store the table as vendor/kodi/builtins.txt so it can be regenerated.
   - Check bare words against ActionTranslator names.
   - Check window arguments to ActivateWindow, ReplaceWindow, ActivateWindowAndFocus, Dialog.Close, Window.IsActive/IsVisible/IsTopmost and Window(...) against windownames.txt (lower-cased), numeric ids, or the shipped Custom_NNNN files.
   - Check that every `RunScript(special://skin/...)` path exists.
3. Delete the fixed whitelist. Instead, add 9100-9105 and 9000/9010/9011 to the known ids only when the window actually pulls in Chrome_Taskbar or Home's panel. Check SetFocus, Control.SetFocus, Container(n) and Control.*(n) targets the same way as numeric navigation.
4. Add a small deny-list of infobools that do not exist in Kodi 21, starting with Player.ShowCodec. Later this can become a full table parsed from GUIInfoManager.cpp.
5. For HAND windows, check per-window required ids taken from the C++ #defines.
6. Flag focusable controls with no label, no onclick and no Kodi-filled id.

**textfit.py**
Walk `<content><item><label>` entries that have no $INFO, and measure each one against the first label or textbox width in the container's itemlayout.

**audit.sh**
Add one line that runs validate.py and textfit.py for both RES=xml and RES=xml768, so these checks run on every build.

## Layout (1024x600, 1024x768, XL / Touch mode)

| # | Sev | Problem |
|---|---|---|
| L-1 | medium | 4:3 layout stretches single-line labels: System information and Weather forecast text floats in big gaps |
| L-2 | low | Customise desktop: 'Done' button cut off and untappable at 1024x600 in Extra-large / Touch mode |
| L-3 | low | 4:3 (768) dialogs keep their 600-era sizes, leaving touch-critical dialogs small and screens half-empty |
| L-4 | cosmetic | Icon picker leaves a 63 px dead strip right of its scrollbar |

### L-1 [medium] 4:3 layout stretches single-line labels: System information and Weather forecast text floats in big gaps

**What you see:** On the 4:3 (9.7") screen, the System information page and the weather forecast have lines of text floating in large empty gaps, away from the things they belong to.

**Where:** `skin.arthuros/xml768/SettingsSystemInfo.xml (label id 8: top 268 height 198; labels 9-13 pushed to 468-596)`; `skin.arthuros/xml/SettingsSystemInfo.xml:111-113 (label 8 is 30 high)`; `skin.arthuros/xml768/MyWeather.xml (hi/low temperature labels 32,33,42,43... and the '/' labels: height 26 -> 194)`; `skin.arthuros/xml/MyWeather.xml:118-129`; `tallpass.py:151-210 grow() (line 187: 'if h >= 0.95 * H or top < S < top + h: action = "grow"' applies to any control type)`

**Why (evidence):** In grow(), any control that crosses the body midline S grows by 168 px, labels included. SettingsSystemInfo has no scroller, so S is the well's centre and info line 8 (one of the Kodi-filled lines 2-13) becomes 198 px tall. The label default is <aligny>center</aligny> (Defaults.xml:19), so its text draws about 100 px below line 7, and lines 9-13 move down 168 px. In MyWeather each day's 'hi / lo' labels become 194 px, so the temperatures float mid-column, far from the day name and icon above and the outlook text moved to y 482. A scan of xml768 finds 16 such single-line controls taller than 90 px, all in these two windows. Renders: /tmp/claude-0/-home-user-Arthuros/e9c89b88-ae6d-5721-b445-85ee9d9a514f/scratchpad/layout/xml768-xl/MyWeather.png, /tmp/claude-0/-home-user-Arthuros/e9c89b88-ae6d-5721-b445-85ee9d9a514f/scratchpad/layout/xml768-n/SettingsSystemInfo.png

**Proposed fix:** Change two things in tallpass.py grow(), non-screen branch.

1. The grow action:
   - Let body = the control body_line() chose. Have body_line return (S, body_top, body_bottom).
   - Only the body itself, groups, images and scrollers may take action "grow". A label, fadelabel, button, radiobutton, togglebutton, edit, spincontrolex, progress or slider must never grow; a label with wrapmultiline may.

2. The move action, for controls that do not grow:
   - "move" only when top >= body_bottom (they sit below the body).
   - Anything whose top lies inside [body_top, body_bottom) stays put.

Result with this rule:
- SettingsSystemInfo: labels 2-13 (all inside the textbox span 76-466) stay as a contiguous stack. Textbox 30 grows to 558, and labels 52/53 (482 >= 466) move to 650/672.
- MyWeather: each tile's day name, icon, hi '/' lo and outlook stay together at 186-384. The tile well grows to 382 tall, and the location/updated well moves down.

For weather, also give weather() in genwindows.py 768-specific tile geometry so the taller tile is filled (for example a 128-px icon and the outlook given more lines), or have tallpass leave the tile well its 600 height and give the extra space to the bottom well.

Then:
- Rebuild and diff xml768 against the current output to make sure no other window changes unexpectedly.
- Add an audit.sh check that flags any non-wrapping label, fadelabel or button in xml768 that is taller than 60 px.

Vince should check the System information page and the Weather page on the 9.7" panel after the rebuild.

### L-2 [low] Customise desktop: 'Done' button cut off and untappable at 1024x600 in Extra-large / Touch mode

**What you see:** On the 7" screen with Touch mode or large fonts, the 'Done' button in Customise desktop is half cut off and doesn't respond to taps.

**Where:** `skin.arthuros/xml/Custom_1120_DesktopEditor.xml:25-29,85 (grouplist 300 height 450; button 311 Done)`; `home.py:659 (editor_window: grouplist height 450)`

**Why (evidence):** With XLC, sizepass turns the nine 34 px rows into Height_34_XL=50 (Includes_Size.xml:11): 9x50 + 8x4 = 482 px against 450 px visible, so Done (offset 432) shows only 18 of its 50 px. CGUIControlGroupList::Render clips to the grouplist rect (GUIControlGroupList.cpp:100-102); IsControlOnScreen (l.509-512) requires a child to fit entirely and SendMouseEvent (l.412) only sends taps to children that fit, so the half-drawn Done ignores taps until the list is panned. Render: scratchpad/layout/xml-xl/Custom_1120_DesktopEditor.png. The 768 build is fine (height 618).

**Proposed fix:** Change home.py editor_window() (both the layout radiobutton loop and buttons 310/311) so that nine XL rows fit in the 450 px list:
- Simplest fix: use `<height>30</height>` instead of `<height>34</height>` for all nine children. sizepass then emits Height_30 / Height_30_XL (30 / 46 px). The XL total becomes 9x46 + 8x4 = 446, which fits in 450, and the normal total is 302.
- Cleaner fix for touch: take buttons 310 and 311 out of grouplist 300 and put them in a fixed row of two buttons below it. Shrink the grouplist so it ends above that row, then rewire onup/ondown/onright between the list and the new buttons.

Either way, rebuild and check the xl render for 1024x600. Optionally, add a check to audit.sh or textfit.py that sums each vertical grouplist's children (XL heights plus itemgaps) and compares the total with the grouplist's height.

### L-3 [low] 4:3 (768) dialogs keep their 600-era sizes, leaving touch-critical dialogs small and screens half-empty

**What you see:** On the 4:3 screen the on-screen keyboard, icon picker and Settings page stay the size they were designed for the smaller screen, leaving keys small and empty space below.

**Where:** `skin.arthuros/xml768/DialogKeyboard.xml (keys 62x40, same as 600)`; `skin.arthuros/xml768/VideoOSD.xml (892x288, same as 600)`; `skin.arthuros/xml768/Custom_1123_DesktopIcon.xml (800x520, 6 icon rows; same as 600)`; `skin.arthuros/xml768/Settings.xml (3 tile rows, about 170 px empty band at the bottom)`; `tallpass.py:24 ('Dialogs centred with <centertop>50%</centertop> need nothing')`; `genwindows.py keyboard_window()`; `home.py icon_dialog():885-920`

**Why (evidence):** tallpass only regrows screen-level groups and never touches centred dialogs. Renders: /tmp/claude-0/-home-user-Arthuros/e9c89b88-ae6d-5721-b445-85ee9d9a514f/scratchpad/layout/grid/xml768-n-04.png (keyboard), /tmp/claude-0/-home-user-Arthuros/e9c89b88-ae6d-5721-b445-85ee9d9a514f/scratchpad/layout/grid/xml768-n-01.png (icon picker), /tmp/claude-0/-home-user-Arthuros/e9c89b88-ae6d-5721-b445-85ee9d9a514f/scratchpad/layout/xml768-n/Settings.png (hub). CLAUDE.md lists this as a known gap; the on-screen keyboard matters most because without a keyboard it is the only way to type.

**Proposed fix:** Keep the fix in the generators, not in tallpass.

1. Keyboard: in genwindows.py keyboard_window(), read a target height (for example `H = int(os.environ.get("ARTHUR_H", 600))`, the same variable home.py uses). When H == 768, use key height 56, row pitch 60, mode/action rows 44, and a box of about 900x470. Then do one of two things: have build.sh run a 768 pass of genwindows.py into build768/ (tallpass already prefers files from build768/ through `_staged`), or give tallpass a small `DIALOG_OVERRIDES` map that swaps in the 768 keyboard. The first option matches how Home.xml is already produced.

2. Separately, consider making the keys taller in Touch mode on both layouts, because the 7" panel has the physically smallest keys. That belongs to the sizepass.py / Includes_Size touch-row mechanism.

3. Settings hub: produce the 768 tile height (654/3, about 210) from whichever generator writes Settings.xml under the same ARTHUR_H switch, so 3 rows fill the panel.

4. Custom_1123 icon picker: in home.py icon_dialog(), grow the box and panel 400 by 168 px when ARTHUR_H == 768. home.py already runs with ARTHUR_H=768 into build768/, so this only needs the height parameter used there.

VideoOSD sits at the bottom anyway, so its size there can wait.

### L-4 [cosmetic] Icon picker leaves a 63 px dead strip right of its scrollbar

**What you see:** The 'Choose an icon' box has an odd empty white strip down its right side.

**Where:** `skin.arthuros/xml/Custom_1123_DesktopIcon.xml:16-20,219-220 (well 16..784, panel 19..699, scrollbar at 703)`; `home.py:891-915 icon_dialog() (pw rounded down to cols*68, scrollbar placed at 19+pw+4)`

**Why (evidence):** Rounding the panel width down to 10 x 68 = 680 puts the scrollbar at x 703-721 inside a well that runs to x 784, leaving an empty white strip on the right. Render: /tmp/claude-0/-home-user-Arthuros/e9c89b88-ae6d-5721-b445-85ee9d9a514f/scratchpad/layout/grid/xml768-n-01.png

**Proposed fix:** Make the change in home.py icon_dialog(). Pick one of these two options.

(a) Keep the dialog at 800 wide and stretch the cells to fill the well.
- Compute `cols = (W - 32 - 6 - 22) // 68` (gives 10) and `cw = (W - 32 - 6 - 22) // cols` (gives 74).
- Set `pw = cols * cw` (gives 740).
- Emit `<itemlayout width="{cw}" height="68">` and `<focusedlayout width="{cw}" height="68">`.
- Centre the images horizontally: the 48-px icon at left `(cw-48)//2`, and the 64-px select ring at left `(cw-64)//2`.
- The scrollbar stays at 19+pw+4 = 763 and ends at 781, flush with the inner edge of the well.

(b) Shrink the dialog to fit the rounded panel.
- After rounding pw, set `W = pw + 6 + 4 + 18 + 32` (gives 740).
- Compute the well, label and gw.dialog width from this W, so the box is tight around the panel and scrollbar.

Then rebuild, so the generator rewrites both xml/ and xml768/Custom_1123_DesktopIcon.xml. Do not hand-edit those XML files.

## Desktop, editors and skin settings

| # | Sev | Problem |
|---|---|---|
| D-1 | high | The shipped desktop has no way to reach the power menu by touch (no Shut down or Reboot) |
| D-2 | medium | 'Defaults' in Skin settings erases the whole desktop and Touch mode with one tap and no confirmation |
| D-3 | medium | Rename on an empty tile slot creates a dead '(empty)' tile; cancelling Rename freezes a tile's name |
| D-4 | medium | 'Choose what this tile opens': group list cut off in Touch mode with no scrollbar (Programs, Files, Settings, Everything hidden) |
| D-5 | medium | 'Scroll list labels' setting doesn't scroll list labels; it only turns on text-box auto-scroll |
| D-6 | low | Back up / Restore: Cancel isn't recognised (Restore shows an error, Back up saves anyway) |
| D-7 | low | backup.py backs up and restores the parked-window state (arthur.min*) because the 'arthur.min' transient prefix never matches |
| D-8 | low | 'Hide the date and clock' leaves the task-bar clock showing |
| D-9 | low | The minimise '_' box on some windows just closes them and drops the previously parked window |

### D-1 [high] The shipped desktop has no way to reach the power menu by touch (no Shut down or Reboot)

**What you see:** Out of the box there's no button to shut down or restart the box by touch; you'd need a keyboard or to add a Power tile yourself first.

**Where:** `skin.arthuros/xml/Includes_Chrome.xml:79-290 (Chrome_Taskbar: Start, Now playing, Playlists, parked window, Settings, Back; no power button)`; `home.py:179-185 (DEFAULTS: the 12 shipped tiles, none of them power)`; `home.py:128-143 (the 'settings' section has no ShutdownMenu entry)`; `home.py:191-196 (DIRECT: power exists only as an optional tile)`; `skin.arthuros/xml/Home.xml:963 (the only ShutdownMenu reference on the desktop, inside the 'Everything' menu, which is not on the default desktop)`; `skin.arthuros/xml/Settings.xml:103-153 (Settings hub: no power item)`

**Why (evidence):** grep for ShutdownMenu/Powerdown/Reboot/Quit across xml/ finds only DialogButtonMenu.xml itself and Home.xml:963 (section 'all', which is not in DEFAULTS). Kodi's system/keymaps/touchscreen.xml (Omega) <global><touch> maps only tap=LeftClick, longpress/2-finger tap=RightClick, pan, swipes (Back, Menu, SwitchPlayer, PlayerControls). No gesture opens ShutdownMenu. So the power menu can only be reached with a keyboard (S key) or after building a Power tile in Customise desktop. changelog 0.9.2 confirms: 'Add it with Customise desktop -> ... -> Everything'.

**Proposed fix:** The proposed fix is right; these points refine it.

1. **Taskbar button** in skin.arthuros/xml/Includes_Chrome.xml (hand-maintained), Chrome_Taskbar:
   - Add a group at left=470, top=4, width=100, height=24 with no visibility condition, so the button always shows.
   - Inside it put button id 9106: onclick ActivateWindow(ShutdownMenu), icon icons24/power.png, label $LOCALIZE[31976]. Copy the focused/unfocused label pair the neighbouring buttons use.
   - Set 9106 onleft=9102 and onright=9104.
   - Change 9102 onright from 9104 to 9106, and 9104 onleft from 9102 to 9106.
   - Run textfit.py to confirm the label fits in 68 px in every fontset, including XL. If it doesn't, use the icon alone with a wider hit area.
   - Rebuild so tallpass.py regenerates xml768.

2. **Desktop fallback in home.py.** Add (31976, "power", "ActivateWindow(ShutdownMenu)") to the 'settings' SECTIONS entry, so it's still reachable when Skin.HasSetting(hidetaskbar) hides the taskbar. Then run build.sh and iconcheck.py; power.png isn't used elsewhere in that menu.

3. **Settings hub.** Add a matching Power item to Settings.xml's hub list (hand-maintained), checking that the panel still fits.

4. **Regression check in audit.sh.** Check that Chrome_Taskbar in xml/Includes_Chrome.xml contains ActivateWindow(ShutdownMenu), and that home.py's settings section lists it.

5. **Changelog.** Bump the version and note the change in changelog.txt.

### D-2 [medium] 'Defaults' in Skin settings erases the whole desktop and Touch mode with one tap and no confirmation

**What you see:** One accidental tap on 'Defaults' in Skin settings wipes your whole custom desktop and turns Touch mode off, with no 'are you sure?'.

**Where:** `skin.arthuros/xml/SkinSettings.xml:154-160 (button 104, label $LOCALIZE[409] 'Defaults', onclick Skin.ResetSettings)`; `skin.arthuros/xml768/SkinSettings.xml:317`

**Why (evidence):** SkinBuiltins.cpp SkinResetAll (line 451) calls CSkinSettings::GetInstance().Reset() and saves straight away, with no prompt. That clears every tile.N.*, home.layout, touchmode, pointer, hide* and home.init. The label is Kodi's string 409 'Defaults', which doesn't say what it resets. Customise desktop's own Reset asks first (Custom_1125, default focus on No).

**Proposed fix:** Both files to change are hand-maintained: skin.arthuros/scripts/backup.py and skin.arthuros/xml/SkinSettings.xml. Edit them directly and let tallpass regenerate xml768.

1. In backup.py, add a `reset()` mode:
   - Ask with `xbmcgui.Dialog().yesno(L(<new id>), L(<new id>), nolabel=..., yeslabel=...)`. The question should say: "This puts back the shipped desktop and turns off Touch mode and every other skin option. Fonts and colours are kept. Make a backup first?" Offer three outcomes: back up first, reset now, or cancel. You can do this with a yesno followed by a second confirm, or with `Dialog().select`.
   - Remember `xbmc.getCondVisibility('Skin.HasSetting(touchmode)')` before resetting.
   - Run `xbmc.executebuiltin('Skin.ResetSettings', True)`.
   - If touch mode was on, put it back with `Skin.SetBool(touchmode)`. A touch-only user would otherwise struggle with the smaller rows.
   - Run `Skin.ToggleSetting(home.flip)` so the desktop reloads its tiles, as `restore()` already does.
   - Add `elif mode == "reset": reset()` to `__main__`.

2. In xml/SkinSettings.xml, change button 104:
   - Set `onclick` to `RunScript(special://skin/scripts/backup.py,reset)`.
   - Give it a new label. Open a new string block at 31800 in en_gb strings.po, for example 31800 "Reset all skin settings...", and put the dialog text at 31801 and up.

3. Add an audit.sh check that SkinSettings.xml no longer contains a bare `<onclick>Skin.ResetSettings</onclick>`, and that it does contain `backup.py,reset`.

4. Rebuild with build.sh so xml768/SkinSettings.xml picks up the change.

### D-3 [medium] Rename on an empty tile slot creates a dead '(empty)' tile; cancelling Rename freezes a tile's name

**What you see:** Tapping Rename on an empty tile spot (even if you cancel) puts a blank '(empty)' tile on the desktop that does nothing; cancelling a rename on a normal tile still changes it behind the scenes.

**Where:** `skin.arthuros/xml/Custom_1121_DesktopTile.xml:529-536 (button 1134)`; `skin.arthuros/xml768/Custom_1121_DesktopTile.xml:532`; `home.py:790-794 (cid == 1134 branch of tile_dialog)`; `home.py:510 (tile visibility in tile_items)`; `skin.arthuros/xml/Home.xml:93-95 (tile 1 onclick/visible; same for 2..36)`

**Why (evidence):** 1134 first runs Skin.SetString(tile.N.name,$ESCVAR[EditTileName]) when Property(name) is empty, then Skin.SetString(tile.N.name), which opens the keyboard. For an empty slot, EditTileName returns $LOCALIZE[31961] '(empty)' (name_vars, home.py: String.IsEmpty(lid) -> 31961), so name becomes '(empty)' before the keyboard opens. SkinBuiltins.cpp SetString (363-382) leaves the value unchanged on cancel. A Home tile is visible when name or lid is non-empty (home.py:510), so the slot appears on the desktop with no icon and no action. Its onclick $INFO[Skin.String(tile.N.action)] runs an empty string. On normal tiles the pre-fill copies the localized label ('Movies - Genres') into name even when he cancels, so the tile stops following the UK/US language and its lid/pre lookup.

**Proposed fix:** All changes go in home.py; then rebuild.

1. tile_dialog(), the cid == 1134 branch (about line 790). Make the pre-fill depend on lid as well:
   `oc(f"Skin.SetString({k}.name,$ESCVAR[EditTileName])", "String.IsEmpty(Container(1150).ListItem.Property(name)) + !String.IsEmpty(Container(1150).ListItem.Property(lid))")`
   Also add an enable condition to 1134 in the buttons list:
   `"![String.IsEmpty(Container(1150).ListItem.Property(id)) + String.IsEmpty(Container(1150).ListItem.Property(action))]"`
   so an empty slot cannot be renamed until "Choose what it opens" has been used.
2. tile_items(), line 510. Change the default Home visibility to
   `[!String.IsEmpty(Skin.String({k}.id)) | !String.IsEmpty(Skin.String({k}.action))]`
   so a slot that holds only a name, which existing installs may already have, stays hidden. Every real tile type sets id or action: sections set id, direct items set action (dir_values), add-ons set action (addon_apply).
3. Do not try a "temp string, then conditional copy-back" approach. CGUIAction::ExecuteActions evaluates every condition before the keyboard opens, so it cannot detect a cancel. If the frozen localized name on normal tiles matters, the only clean option is to drop the pre-fill for lid tiles (the keyboard opens empty; confirming blank keeps the lid label). Accepting the current behaviour is reasonable, since any re-pick resets the name.
4. Optional: add an audit.sh check that the 1134 pre-fill condition contains `Property(lid)`.

### D-4 [medium] 'Choose what this tile opens': group list cut off in Touch mode with no scrollbar (Programs, Files, Settings, Everything hidden)

**What you see:** When choosing what a desktop tile opens in Touch mode, the list of groups is cut off; Programs, Files, Settings and Everything are hidden with no sign you can scroll.

**Where:** `skin.arthuros/xml/Custom_1122_DesktopChoose.xml:17 (list 200, height 434)`; `skin.arthuros/xml768/Custom_1122_DesktopChoose.xml:123`; `home.py:829-835 (catalogue_dialog: list 200 built without pagecontrol or scrollbar)`

**Why (evidence):** List 200 has 15 groups (3 kinds + 12 SECTIONS). Touch-mode rows are 44 px (row_layouts(240, 28, 44, ...)), so 660 px against 434 px visible, at both 600 and 768 because dialogs keep their 600 size. The rendered preview (SET=touchmode=true) shows only Menus ... Live TV (9 rows). List 210 next to it gets <pagecontrol>211</pagecontrol> and a scrollbar; list 200 gets neither. Lists do pan (GUIBaseContainer.cpp:805-845), but nothing shows there is more.

**Proposed fix:** In home.py catalogue_dialog():
- Narrow list 200 from 240 to 216 px. Pass 216 to row_layouts, and change gbody's label width to 216 - s - 20 and its focus fill to 216.
- Add <pagecontrol>201</pagecontrol> to list 200. Keep <onright>210</onright> on the list.
- After list 200, add a scrollbar the same way 211 is built: ctl("scrollbar", 201, 19 + 216 + 3, 47, 18, Hh - 66, ["<onleft>200</onleft>", "<onright>210</onright>"]). It lands at x 238-256, inside the 16-262 sunken frame.
- Then rerun build.sh so xml/ and xml768/ (tallpass.py) are regenerated.

Alternative: in touch mode, fold the 12 SECTIONS entries under one group so the left list fits in 434 px. That is a larger change to how the right list is filtered.

### D-5 [medium] 'Scroll list labels' setting doesn't scroll list labels; it only turns on text-box auto-scroll

**What you see:** Turning on 'Scroll list labels' doesn't make long names in lists scroll; it only changes how long descriptions behave.

**Where:** `skin.arthuros/xml/SkinSettings.xml:77-84 (radiobutton 103, label 31910 'Scroll list labels', toggles autoscroll)`; `skin.arthuros/xml/Defaults.xml:9-21 (label default <scroll>false</scroll>)`; `skin.arthuros/xml/Defaults.xml:32-37 (the only reader: textbox <autoscroll>Skin.HasSetting(autoscroll)</autoscroll>)`

**Why (evidence):** The only Skin.HasSetting(autoscroll) reader is the textbox default. <autoscroll> belongs to CGUITextBox (xbmc/guilib/GUITextBox.cpp:363). Label scrolling is <scroll>, read as a plain boolean (GUIControlFactory.cpp:1134, XMLUtils::GetBoolean), so a setting can't switch it, and it is false for every label.

**Proposed fix:** Every file involved is hand-maintained (CLAUDE.md lines 100-106); there is no generator to change.

**Option A (smallest fix):** in `language/resource.language.en_gb/strings.po`, change msgid #31910 to "Scroll long descriptions". The en_us copy is generated from en_gb by the build.

**Option B (make the label true):**
1. In each list's focusedlayout title label in `Includes_Lists.xml` and `View_50_List.xml` / `View_51_Poster.xml` / `View_52_IconWall.xml`, add two includes:
   - `<include content="ListLabelScroll" condition="Skin.HasSetting(autoscroll)"/>`
   - `<include content="ListLabelNoScroll" condition="!Skin.HasSetting(autoscroll)"/>`
2. Define those includes in `Includes.xml`, one with `<scroll>true</scroll>` and one with `<scroll>false</scroll>`.

Make sure each label ends up with exactly one `<scroll>`. `SetDefaults` (GUIIncludes.cpp) appends the default `<scroll>false</scroll>` after the label's own tags, so test that the include's value is the one Kodi uses. If it is not, drop `<scroll>` from the label default and set it explicitly where needed.

The include condition is checked only when a window loads, so the change applies the next time a media window opens.

With either option, add an `audit.sh` check, for example that string 31910's text matches what the `autoscroll` setting actually controls.

### D-6 [low] Back up / Restore: Cancel isn't recognised (Restore shows an error, Back up saves anyway)

**What you see:** Cancelling Restore shows a confusing 'not an ArthurOS backup' error, and cancelling Back up saves a backup anyway.

**Where:** `skin.arthuros/scripts/backup.py:72-74 (backup: browse(3, ..., BACKUPS); if not folder: return)`; `skin.arthuros/scripts/backup.py:102-111 (restore: browse(1, ..., BACKUPS); if not path: return)`

**Why (evidence):** xbmc/interfaces/legacy/Dialog.cpp Dialog::browseSingle (216-250) sets value = defaultt and returns value unchanged when the browser is cancelled (CGUIDialogFileBrowser::ShowAndGetFile only writes path when confirmed, GUIDialogFileBrowser.cpp:703-708). So Cancel returns BACKUPS, which is never empty. In restore, read_xml(BACKUPS) on a directory gives empty data, so root is None and the 'That file is not an ArthurOS backup.' error (31985) appears. In backup, a file is written to the default folder and 'Skin settings saved' is shown.

**Proposed fix:** Change skin.arthuros/scripts/backup.py by hand (not generated).

restore(): after the browse() call, add:
`if not path or path.endswith(("/", "\\")) or xbmcvfs.translatePath(path).rstrip("/\\") == xbmcvfs.translatePath(BACKUPS).rstrip("/\\"): return`
Because the browser only offers .xml files, a confirmed pick is always a file and never the folder, so this test only matches Cancel. Optionally also return when `not xbmcvfs.exists(path)`.

backup(): Cancel cannot be told apart from pressing OK in the default folder, because both return the same BACKUPS path. So first ask with `xbmcgui.Dialog().select(L(31981), [<"ArthurOS backups folder">, <"Choose a folder...">])`. A result of -1 means cancel, so return. 0 uses BACKUPS. 1 calls `browse(3, ..., defaultt="")` and returns if the result is empty, which is reliable because the default is now empty. The two option labels need new string IDs in strings.po.

Simpler alternative: call browse(3) with defaultt="" so that Cancel returns "". The catch is that the browser then opens at the list of sources instead of the backups folder.

### D-7 [low] backup.py backs up and restores the parked-window state (arthur.min*) because the 'arthur.min' transient prefix never matches

**What you see:** Restoring a backup can bring back an old 'minimised window' button on the task bar from when the backup was made.

**Where:** `skin.arthuros/scripts/backup.py:30 (TRANSIENT = (..., "swap.", "arthur.min"))`; `skin.arthuros/scripts/backup.py:37-38 (transient(): prefix match only for entries ending in '.')`; `skin.arthuros/xml/Includes_Chrome.xml:188-212`; `skin.arthuros/xml/Includes_Chrome.xml:386-389`

**Why (evidence):** transient() treats an entry as a prefix only when it ends with '.', so 'arthur.min' matches only a setting literally named arthur.min, which is never used. The real settings are arthur.minwin, arthur.minpath, arthur.mintitle and arthur.minicon, set by the title-bar '_' box (Includes_Chrome.xml:386-389). Running the function: transient('arthur.minwin') returns False, and the same for the other three. So a backup taken while a window is parked records that window and its folder path; restoring sets them again with Skin.SetString and Includes_Chrome.xml:188 shows the parked-window button again (visible when arthur.minwin is not empty).

**Proposed fix:** Change TRANSIENT in skin.arthuros/scripts/backup.py (hand-maintained, not generated) so "arthur.min" gets prefix matching. Two ways to do it:
- Keep the trailing-dot rule and add a separate prefix tuple:
  TRANSIENT = ("edit.slot", "pick.addon", "home.flip")
  TRANSIENT_PREFIX = ("swap.", "arthur.min")
  def transient(name): return name in TRANSIENT or name.startswith(TRANSIENT_PREFIX)
- Or list the four names explicitly: "arthur.minwin", "arthur.minpath", "arthur.mintitle", "arthur.minicon".

Optional hardening in the same file: catch ET.ParseError from read_xml(SETTINGS) inside current_settings(). On error, show xbmcgui.Dialog().ok(L(31979)/L(31980), L(31985)) and stop, instead of letting Python raise an error dialog.

### D-8 [low] 'Hide the date and clock' leaves the task-bar clock showing

**What you see:** Turning on 'Hide the date and clock' still leaves a clock in the corner of the task bar.

**Where:** `skin.arthuros/xml/Includes_Chrome.xml:67-73 (menu-bar clock honours hideclock)`; `skin.arthuros/xml/Includes_Chrome.xml:276-287 (tray clock: visible only on !touchmode, ignores hideclock)`; `skin.arthuros/xml768/Includes_Chrome.xml:286`

**Why (evidence):** Skin.HasSetting(hideclock) is read only at Includes_Chrome.xml:72. The tray label $INFO[System.Time] at 281-287 has <visible>!Skin.HasSetting(touchmode)</visible> only.

**Proposed fix:** Edit only the hand-maintained skin.arthuros/xml/Includes_Chrome.xml, in the Chrome_Taskbar tray block (about lines 276-287):
- On the tray label (`$INFO[System.Time]`), change the visible condition to `<visible>!Skin.HasSetting(touchmode) + !Skin.HasSetting(hideclock)</visible>`.
- Give the tray sunken-well image (panel_sunken_chrome.png) the same condition. Otherwise an empty well is left behind.

Then run build.sh so xml768/Includes_Chrome.xml is regenerated; do not hand-edit xml768. As CLAUDE.md requires, add an audit.sh check that every `System.Time` label in xml/Includes_Chrome.xml carries a hideclock condition.

### D-9 [low] The minimise '_' box on some windows just closes them and drops the previously parked window

**What you see:** Pressing minimise on the music playlist editor or screen calibration just closes it, and also loses any other window you had minimised.

**Where:** `skin.arthuros/xml/Variables.xml:48-85 (ArthurWindowName list)`; `skin.arthuros/xml/Includes_Chrome.xml:381-393 (9901 sets arthur.minwin from $VAR[ArthurWindowName])`; `skin.arthuros/xml/MyMusicPlaylistEditor.xml, SettingsScreenCalibration.xml (use boxes=window via genwindows.BOXES default)`

**Why (evidence):** genwindows.py:87 gives full windows boxes='window' by default. MyMusicPlaylistEditor (musicplaylisteditor) and SettingsScreenCalibration (screencalibration) are not in ArthurWindowName, so its fallback value is 'home'. 9901 then sets arthur.minwin=home, which overwrites any parked window, and the task-bar button is hidden (Includes_Chrome.xml:188 excludes 'home') before ActivateWindow(Home).

**Proposed fix:** 1) Variables.xml is hand-maintained, so edit it directly. In ArthurWindowName, add `<value condition="Window.IsActive(musicplaylisteditor)">musicplaylisteditor</value>`. In ArthurWindowIcon, add `<value condition="Window.IsActive(musicplaylisteditor)">icons24/playlist_music.png</value>`. Both icons are the ones the windows' own title bars already use.

2) Screen calibration: there is little point in parking it, so in genwindows.py set `BOXES["SettingsScreenCalibration"] = "dialog"` (close box only). Alternatively, add `screencalibration` with `icons24/calibration.png` to both variables.

3) Includes_Chrome.xml is hand-maintained. In Win_Boxes_window button 9901, add `condition="!String.IsEqual($VAR[ArthurWindowName],home)"` to the four Skin.SetString onclicks. Any window not in the list then just goes Home and leaves the already-parked window alone. Leave ActivateWindow(Home) without a condition.

4) audit.sh: add a check that, for every xml/*.xml containing `name="boxes" value="window"`, that window's Kodi name appears in ArthurWindowName. Include the Includes_Media users by listing which window names use them. Also check that each 9901 SetString carries the home guard.

## Library and add-on browsers, info dialogs

| # | Sev | Problem |
|---|---|---|
| B-1 | medium | No watched, resume or now-playing indicator in any list, poster or icon view |
| B-2 | medium | Poster wall and icon wall pick the wrong art: video icon for anything without a poster, folder icon for files |
| B-3 | medium | Info dialogs only show Art(poster): album and artist covers never appear, and episodes and add-on videos show a video icon |
| B-4 | medium | Video info: Trailer, Director, Manage versions and Extras always show even when they don't apply; Play stays 'Play' for TV shows and seasons |
| B-5 | low | Add-on settings in the player misses or clears the add-on: favourites, desktop tiles and audio play from add-ons |
| B-6 | low | No empty-state message, and the item count is overwritten by Kodi and hidden inside add-ons |
| B-7 | low | Poster and icon-wall titles never wrap, so long names lose everything after the first line |
| B-8 | cosmetic | Music playlist window shows the video-playlist icon |

### B-1 [medium] No watched, resume or now-playing indicator in any list, poster or icon view

**What you see:** In film and episode lists you can't tell which ones you've already watched, which are half-watched, or which is playing now.

**Where:** `skin.arthuros/xml/Includes_Lists.xml:9-111 (Arthur_ItemLayout/_XL/FocusedLayout/_XL)`; `skin.arthuros/xml/View_51_Poster.xml:20-62`; `skin.arthuros/xml/View_52_IconWall.xml:20-62`

**Why (evidence):** grep over xml/ finds no use of ListItem.PlayCount, ListItem.Overlay, ListItem.IsResumable, ListItem.PercentPlayed or ListItem.IsPlaying outside VideoOSD/MusicOSD, and media/ has no overlay textures. Each row has only icon, Label and Label2 (Includes_Lists.xml:12-27). Kodi exposes these per item: LISTITEM_OVERLAY returns item->GetOverlayImage() (GUIInfoManager.cpp:11351-11352). Watched state and resume points are also kept for plugin items by path.

**Proposed fix:** Hand-edit `skin.arthuros/xml/Includes_Lists.xml`, the source file, not the generated `xml768/` copy. In all four row layouts, add a 16x16 status image at the right edge:
- `left = $PARAM[width]-18`
- top 4 in the 24px rows, 12 in the XL rows

Use three images with mutually exclusive visibility conditions:
- Playing: `ListItem.IsPlaying`, using `icons24/play.png`, which already exists.
- Half-watched: `ListItem.IsResumable`, using a new `icons24/resume` half-filled circle.
- Watched: `Integer.IsGreater(ListItem.PlayCount,0) + !ListItem.IsResumable + !ListItem.IsPlaying`, using a new `icons24/watched` tick.

In the same layouts:
- Move the Label2 label's right edge in by 20px. Either give it width `$PARAM[width]-20`, or keep the width and add a 20px offset param.
- Optionally add a 3px progress control at the row bottom: `<info>ListItem.PercentPlayed</info>`, visible on `ListItem.IsResumable`.

In `View_51_Poster.xml` and `View_52_IconWall.xml`, add the same images as a corner badge, top-right of the art, in both itemlayout and focusedlayout. Optionally add the progress bar under the art.

Draw the new glyphs, `watched` and `resume`, in `iconset.py` so that `mkmedia` emits them and `iconcheck.py` stays green.

Rebuild so that `tallpass` regenerates `xml768/`. Add an `audit.sh` check that greps `Includes_Lists.xml` for `ListItem.PlayCount` and `ListItem.IsResumable`.

Do not rely on `ListItem.Overlay` unless you also ship `OverlayWatched.png` and `OverlayUnwatched.png` from `mkmedia.py`.

### B-2 [medium] Poster wall and icon wall pick the wrong art: video icon for anything without a poster, folder icon for files

**What you see:** In the Poster view, episodes, add-on items and files show a generic video icon instead of their picture, and in the Icon view files and add-on items often show a folder icon.

**Where:** `skin.arthuros/xml/View_51_Poster.xml:28, 46`; `skin.arthuros/xml/View_52_IconWall.xml:28, 46`; `skin.arthuros/xml/Includes_Media.xml:83`; `skin.arthuros/xml768/MyVideoNav.xml:381, 399, 446, 464, 503`

**Why (evidence):** CGUIListItem::GetArt (GUIListItem.cpp:132-145) returns '' when the requested type is missing and no explicit fallback is set. The only fallbacks VideoThumbLoader sets are fanart->tvshow.fanart and tvshow.thumb->tvshow.poster (VideoThumbLoader.cpp:446-449), never poster. So episodes, files, pictures, add-ons, '..' and plugin items that set only thumb/icon all get Art(poster)='' and draw DefaultVideo.png in the poster view. Kodi's own fallback chain is ListItem.Icon: thumb, then the item's 'icon' art (DefaultFolder/DefaultFolderBack/DefaultVideo/DefaultPicture… set by Kodi) (GUIInfoManager.cpp:11340-11348). The icon wall and the info panel instead use Art(thumb) with fallback DefaultFolder.png, so a video file, a '..' item or a plugin folder that sets only 'icon' shows a folder.

**Proposed fix:** 1. In the hand-maintained `skin.arthuros/xml/Variables.xml`, add:

```xml
<variable name="PosterArtVar">
  <value condition="!String.IsEmpty(ListItem.Art(poster))">$INFO[ListItem.Art(poster)]</value>
  <value condition="!String.IsEmpty(ListItem.Art(tvshow.poster))">$INFO[ListItem.Art(tvshow.poster)]</value>
  <value>$INFO[ListItem.Icon]</value>
</variable>
```

2. In `View_51_Poster.xml` (both layouts, lines 28 and 46), use `<texture fallback="DefaultFile.png">$VAR[PosterArtVar]</texture>`. Use `aspectratio keep` so square icons and thumbs are not stretched into the 2:3 tile.

3. In `View_52_IconWall.xml` (lines 28 and 46) and `Includes_Media.xml:83`, replace `$INFO[ListItem.Art(thumb)]` with `$INFO[ListItem.Icon]` and change the fallback to `DefaultFile.png`. Kodi's own `icon` art then supplies the correct DefaultVideo, DefaultAudio, DefaultFolderBack and similar icons.

4. Rebuild so tallpass regenerates xml768 (MyVideoNav and the others).

5. Add an `audit.sh` check that fails if any panel or info texture in View_51, View_52 or Includes_Media uses a bare `ListItem.Art(poster)` or `ListItem.Art(thumb)` with a hard-coded DefaultVideo or DefaultFolder fallback.

### B-3 [medium] Info dialogs only show Art(poster): album and artist covers never appear, and episodes and add-on videos show a video icon

**What you see:** Album and artist info screens never show the cover art, episode and add-on info show a generic video icon, and album track names are cut off after a few letters.

**Where:** `skin.arthuros/xml/DialogVideoInfo.xml:27`; `skin.arthuros/xml/DialogMusicInfo.xml:27`; `skin.arthuros/xml768/DialogVideoInfo.xml:136`; `skin.arthuros/xml768/DialogMusicInfo.xml:136`; `genwindows.py:518-521 (info_dialog image block)`

**Why (evidence):** info_dialog() hard-codes <texture fallback="DefaultVideo.png">$INFO[ListItem.Art(poster)]</texture> for every info dialog. Music albums and artists carry 'thumb' (the cover) and 'fanart', never 'poster'; CGUIDialogMusicInfo itself sets art 'thumb' (GUIDialogMusicInfo.cpp:530, 781, 856). Episodes and plugin videos have no poster fallback (VideoThumbLoader.cpp:439-458; GetArt returns '' per GUIListItem.cpp:132-145). The music info dialog also binds the album's tracks or the artist's albums to list 50 (GUIDialogMusicInfo.cpp:541, 550), which this layout draws as 80x80 'actor' tiles with 88 px labels (DialogMusicInfo.xml:63-94), so track titles are cut off after a few characters.

**Proposed fix:** 1. In home.py variables(), which generates Variables.xml for both xml/ and xml768/, add two variables. Variables.xml is generated, so do not hand-edit it. (a) VideoInfoArtVar, whose values are tried in order:
  - Art(poster) when !String.IsEmpty(ListItem.Art(poster))
  - Art(tvshow.poster) when String.IsEqual(ListItem.DBType,episode) + !String.IsEmpty(ListItem.Art(tvshow.poster))
  - Art(season.poster) when !String.IsEmpty(ListItem.Art(season.poster))
  - Art(thumb) when !String.IsEmpty(ListItem.Art(thumb))
  - $INFO[ListItem.Icon] as the last value.

(b) MusicInfoArtVar, modelled on Estuary:
  - Art(thumb) when !String.IsEmpty(ListItem.Art(thumb))
  - DefaultArtist.png when String.IsEqual(ListItem.DBType,artist)
  - DefaultAlbumCover.png when String.IsEqual(ListItem.DBType,album)
  - DefaultAudio.png otherwise.

2. In genwindows.py info_dialog(name, ...), choose the art by name. Use `$VAR[MusicInfoArtVar]` with fallback DefaultAlbumCover.png when name == "DialogMusicInfo". Otherwise use `$VAR[VideoInfoArtVar]` with fallback DefaultVideo.png.

3. Also in genwindows.py info_dialog(), when name == "DialogMusicInfo", give list 50 different layouts from the cast panel:
  - Songs (condition Container.Content(songs)): a full-width row (about 868x30) showing $INFO[ListItem.TrackNumber] and $INFO[ListItem.Label], with $INFO[ListItem.Duration] right-aligned. Use a vertical list or a single-column panel so touch scrolling works.
  - Artist discography (albums): keep thumbnail tiles, but use ListItem.Art(thumb) with fallback DefaultAlbumCover.png, and either widen the tile or set <scroll>true</scroll> on the focused label.

4. Rebuild with build.sh so xml/ and xml768/ are regenerated.

### B-4 [medium] Video info: Trailer, Director, Manage versions and Extras always show even when they don't apply; Play stays 'Play' for TV shows and seasons

**What you see:** Film and TV info screens show Trailer, Director, Versions and Extras buttons even when there's nothing behind them, plus greyed-out buttons, and 'Play' on a TV show actually opens its episode list.

**Where:** `skin.arthuros/xml/DialogVideoInfo.xml:99-119`; `skin.arthuros/xml768/DialogVideoInfo.xml:207-228`; `genwindows.py:611-618 (INFO_BUTTONS) and 589-607 (row())`

**Why (evidence):** GUIDialogVideoInfo::OnInitWindow/Update (GUIDialogVideoInfo.cpp:265-301, 529-535) enable or disable only Refresh(6), Get thumb(10), User rating(7), Fanart(12) and Resume(9). Trailer(11), Director(13), Versions(14) and Extras(15) are always enabled, and Kodi expects the skin to hide them. Estuary DialogVideoInfo.xml:546 uses !String.IsEmpty(ListItem.Trailer) for 11, :616 !String.IsEmpty(ListItem.Director) for 13, and :630/:636 String.IsEqual(ListItem.DBType,movie) for 14/15. Play() on a tvshow or season browses to its episodes (GUIDialogVideoInfo.cpp:774-799), yet the label is always $LOCALIZE[208] 'Play'; Estuary switches the label to Browse. The disabled buttons (Rating for plugins, Fanart for episodes) remain visible as greyed tiles.

**Proposed fix:** In `genwindows.py`:

1. Let `INFO_BUTTONS` entries take an optional third element, a visible condition. Make the label accept either a number (written as `$LOCALIZE[n]`) or a string starting with `$` (written as-is). In `row()`, add `<visible>{cond}</visible>` to the button when a condition is given.

2. Set these entries in `DialogVideoInfo`:
   - `(8, "$VAR[InfoPlayLabelVar]")`
   - `(9, 13404, "Control.IsEnabled(9)")`
   - `(11, 20410, "!String.IsEmpty(ListItem.Trailer)")`
   - `(13, 20339, "!String.IsEmpty(ListItem.Director)")`
   - `(14, 40001, "String.IsEqual(ListItem.DBType,movie)")`
   - `(15, 40211, "String.IsEqual(ListItem.DBType,movie)")`
   - `(6, 184, "Control.IsEnabled(6)")`
   - `(10, 13511, "Control.IsEnabled(10)")`
   - `(12, 20413, "Control.IsEnabled(12)")`
   - `(7, 38023, "Control.IsEnabled(7) | !String.IsEmpty(ListItem.UserRating)")`

3. Order the list so the buttons that are always present (8, 9, 6 and the ones most likely to be visible) come first.

4. In `row()`, give each grouplist row after the first a visible condition that is the OR of its buttons' conditions, so an empty row is never shown. Make the `onup` / `ondown` chain safe when a row is hidden: point to the next-but-one row with a fallback. Kodi skips a hidden target only if the skin routes around it.

5. Add `InfoPlayLabelVar` to the hand-maintained `skin.arthuros/xml/Variables.xml`:
   - `$LOCALIZE[1024]` when `String.IsEqual(ListItem.DBType,tvshow) | String.IsEqual(ListItem.DBType,season) | String.IsEqual(ListItem.DBType,set)`
   - `$LOCALIZE[208]` otherwise

6. Add an `audit.sh` check that buttons 11, 13, 14 and 15 in `xml/` and `xml768/` `DialogVideoInfo.xml` each have a `<visible>` tag, and that button 8's label uses `InfoPlayLabelVar`.

### B-5 [low] Add-on settings in the player misses or clears the add-on: favourites, desktop tiles and audio play from add-ons

**What you see:** The 'Add-on' settings button on the video menu disappears or doesn't work when you started playback from a favourite, a desktop tile, or an add-on playing music.

**Where:** `skin.arthuros/xml/MyFavourites.xml:5`; `skin.arthuros/xml/MyVideoNav.xml:5 (and every other browser :5)`; `skin.arthuros/xml/Home.xml:46`; `home.py:549-550`; `skin.arthuros/xml/VideoOSD.xml:183-184 (consumer)`

**Why (evidence):** The onunload runs in CGUIWindow::OnDeinitWindow (GUIWindow.cpp:569-574). The window manager closes the old window while it is still the active window (GUIWindowManager.cpp:877-890), so $INFO[Container.PluginName] resolves through GetMediaWindow(DEFAULT_CONTEXT) to that browser (GUIInfoHelper.cpp:92-136; GUIControlsGUIInfo.cpp:78-90). The video case therefore works when you play from inside YouTube or Plex and Kodi switches to fullscreen (CGUIWindowManager::SwitchToFullScreen, GUIWindowManager.cpp:962-986). The gaps: (a) CGUIWindowFavourites (path favourites://, GUIWindowFavourites.cpp:248) runs the favourite's PlayMedia(plugin://…) action (lines 120-150); when playback deactivates it, its own onunload writes Container.PluginName = '' and clears the value. (b) A desktop tile with PlayMedia/RunAddon starts playback with no media window unloading, and Home.xml:46 has just cleared the property on load. (c) Music played from an add-on doesn't leave the browser (SwitchToFullScreen only moves to Visualisation if the user starts it), so the property is unset while it plays.

**Proposed fix:** Leave MyFavourites.xml's onunload in place; removing it would leave an old add-on behind. Make no changes to home.py.

In genwindows.py, change the ADDON tuple at lines 433-434. The tuple feeds both VideoOSD and MusicOSD, so one change covers both.
- Visibility: `String.StartsWith(Player.FilenameAndPath,plugin://) | !String.IsEmpty(Window(Home).Property(arthuros.plugin))`
- Action: `RunScript(special://skin/scripts/addonsettings.py)`

Add a new hand-written script, skin.arthuros/scripts/addonsettings.py:
```python
import xbmc
from urllib.parse import urlparse

p = xbmc.getInfoLabel('Player.FilenameAndPath')
aid = urlparse(p).netloc if p.startswith('plugin://') else ''
aid = aid or xbmc.getInfoLabel('Window(Home).Property(arthuros.plugin)')
if aid:
    xbmc.executebuiltin('Addon.OpenSettings(%s)' % aid)
```

Keep the browsers' onunload property as the fallback for add-ons that call Player().play() directly. Update the CLAUDE.md note: the resolved dynamic path does not name the plugin, but Player.FilenameAndPath does. Rebuild with build.sh so xml768 is regenerated.

### B-6 [low] No empty-state message, and the item count is overwritten by Kodi and hidden inside add-ons

**What you see:** An empty folder or add-on page just shows a blank area with no 'nothing here' message, and the item count is missing inside add-ons.

**Where:** `skin.arthuros/xml/Includes_Media.xml:52-58`; `skin.arthuros/xml/Variables.xml:10-13 (ItemCountVar)`

**Why (evidence):** CGUIMediaWindow::UpdateButtons runs SET_CONTROL_LABEL(CONTROL_LABELFILES 12, "N Objects") (GUIMediaWindow.cpp:617-619), and CGUILabelControl::SetLabel replaces the info label (GUILabelControl.cpp:152-165, 204-207). So $VAR[ItemCountVar] and its 'Empty list' value never show after the first update. The label is also hidden whenever Container.PluginName is set, to make room for Add-on settings. Nothing else in the window reacts to an empty container (no Container.NumItems / IsEmpty checks in any browser).

**Proposed fix:** Both files are hand-maintained (CLAUDE.md), so edit them directly and add an audit.sh check:

(a) Includes_Media.xml, Media_Toolbar: give the count label a different id, or none, so Kodi's SET_CONTROL_LABEL(12) cannot overwrite it. CGUIWindow::OnMessage simply finds no control with id 12, so removing it is harmless. Do not keep an off-screen id-12 stub: it adds nothing. Then $VAR[ItemCountVar] stays live and its "Empty list" branch works.

(b) Show the count inside add-ons too. Either drop the `String.IsEmpty(Container.PluginName)` visibility and narrow the label (for example, left 820, width 186, to clear button 9502), or move the count into the title bar label2.

(c) Optionally, in Media_Window inside the views area, add a centred textdim label `$LOCALIZE[2080]` with `<visible>Integer.IsEqual(Container.NumItems,0) + !Container.IsUpdating</visible>`. Container.NumItems already leaves out the ".." item.

(d) Add an audit.sh check that no `type="label"` control in Includes_Media.xml uses id 12 together with a $VAR/$INFO label.

### B-7 [low] Poster and icon-wall titles never wrap, so long names lose everything after the first line

**What you see:** Long titles under posters and icons are cut off after about 20 letters even though there's room for a second line.

**Where:** `skin.arthuros/xml/View_51_Poster.xml:30-37, 52-58`; `skin.arthuros/xml/View_52_IconWall.xml:30-37, 52-58`

**Why (evidence):** The labels are 44/32 px high with <wrapmultiline>true</wrapmultiline>, but labels inside list layouts are CGUIListLabel and never wrap (a Kodi fact recorded and verified in CLAUDE.md). The second line of each tile is therefore always empty, and YouTube or episode titles are truncated at about 19-23 characters.

**Proposed fix:** These are hand-maintained files, so edit skin.arthuros/xml/View_51_Poster.xml and skin.arthuros/xml/View_52_IconWall.xml directly; xml768 is regenerated by the build.

1. In both files, in both the itemlayout and the focusedlayout, replace the `<control type="label">` holding `$INFO[ListItem.Label]` with a textbox:
`<control type="textbox"><left>4</left><top>174</top><width>112</width><height>44</height><font>tiny</font><textcolor>text</textcolor><align>center</align><aligny>top</aligny><label>$INFO[ListItem.Label]</label></control>`
   - Use 4/114/142/32 for the icon wall.
   - Use textcolor textinv in the focusedlayout.
   - Drop `<wrapmultiline>`.
   - Leave out `<autoscroll>`. The textbox clips to its height, so text past 2-3 lines is cut off. That is acceptable.

2. Optionally, also add `<scroll>true</scroll>` behaviour for the selected tile. The simplest way is to keep a label control with `<scroll>true</scroll>` only in the focusedlayout, so the full title scrolls when the tile is selected. Use textbox in both layouts if wrapping is preferred.

3. Fix textfit.py:93 so it no longer skips wrapmultiline labels that sit inside an itemlayout or focusedlayout. These are CGUIListLabel per GUIControlFactory.cpp and never wrap, so textfit should flag them.

4. Add an audit.sh check that fails when `<wrapmultiline>` appears inside an `<itemlayout>` or `<focusedlayout>` in any skin.arthuros/xml/*.xml.

### B-8 [cosmetic] Music playlist window shows the video-playlist icon

**What you see:** The music playlist window shows a video icon in its title bar.

**Where:** `skin.arthuros/xml/MyPlaylist.xml:14`; `skin.arthuros/xml768/MyPlaylist.xml:94`

**Why (evidence):** Both WINDOW_MUSIC_PLAYLIST and WINDOW_VIDEO_PLAYLIST load MyPlaylist.xml (GUIWindowMusicPlaylist.cpp:55, GUIWindowVideoPlaylist.cpp:52). The title-bar icon param is fixed to icons24/playlist_video.png, while Variables.xml ArthurWindowIcon already uses playlist_music.png for musicplaylist.

**Proposed fix:** In iconset.py, add the window to WINDOW_ICON_EXPR, the dict for windows whose title icon depends on what they show:
```
WINDOW_ICON_EXPR = {
 "SettingsCategory": "$VAR[ArthurWindowIcon]",
 "MyPlaylist": "$VAR[ArthurWindowIcon]",
}
```
Keep the `"MyPlaylist": "playlist_video"` entry in WINDOW_ICONS so iconcheck's registry stays complete. themepass checks WINDOW_ICON_EXPR first, so the new entry takes over. Then rebuild. themepass writes the $VAR into xml/MyPlaylist.xml, and tallpass carries it into xml768/MyPlaylist.xml. Do not edit MyPlaylist.xml by hand, because themepass would overwrite it.

## Scripts, install and build tooling

| # | Sev | Problem |
|---|---|---|
| X-1 | medium | build.sh does not stop when the first half of an '&&' step fails, so a broken 1024x600 layout can be built and packaged |
| X-2 | medium | First install by folder copy (install-arthuros.sh or the README method) leaves the skin disabled, so it is not in the skin list |
| X-3 | low | netbt.py: a saved open (no-password) Wi-Fi network that fails to connect gives no message at all (ask Vince first) |
| X-4 | low | netbt.py: the 'not allowed to manage networks' fix names the SSH user, not the user Kodi runs as, and the docstring assumes a login session (ask Vince first) |
| X-5 | low | install-arthuros.sh fails on LibreELEC (no sudo) and leaves Kodi stopped with the skin removed if a later step fails |
| X-6 | low | audit.sh does not check the changelog and README version stamps that CLAUDE.md says it checks |
| X-7 | low | mousewatch counts any device with REL_X/REL_Y as a mouse, and Touch mode has no override, so the pointer can stay on forever on a touch-only box |

### X-1 [medium] build.sh does not stop when the first half of an '&&' step fails, so a broken 1024x600 layout can be built and packaged

**What you see:** Not visible directly, but a broken version of the skin for the 7" screen could be built and installed without any warning.

**Where:** `build.sh:10`; `build.sh:11`; `build.sh:12`; `build.sh:14`; `package.sh:5`

**Why (evidence):** build.sh uses `set -e` and chains steps with &&, for example line 14 `python3 validate.py && RES=xml768 python3 validate.py`. Under POSIX sh, -e is ignored for every command in an AND-OR list except the last one. I checked this with dash, which is /bin/sh here: `sh -c 'set -e; false && true; echo continued'` prints 'continued' and exits 0. So if any of these fail, the build carries on: `python3 home.py` (600 desktop), `python3 themepass.py` (xml), `python3 sizepass.py` (xml, which also writes Includes_Size.xml), and, worst of all, `python3 validate.py` for xml/, the default layout used on the 7" panel. Only the xml768 half of each pair can stop the build. If home.py (600) fails, ARTHUR_H=768 home.py never runs either. tallpass.py then quietly uses the stale build768/Home.xml from the last good run. package.sh line 5 (`./build.sh`) trusts build.sh's exit code, so it zips the result. CLAUDE.md says the build 'stops at first failure', which is not true for these four steps.

**Proposed fix:** In /home/user/Arthuros/build.sh (a hand-maintained file), split every `&&` pair into separate commands so `set -e` covers each one, for example `echo "== desktop"; rm -rf build768; python3 home.py; ARTHUR_H=768 python3 home.py`, and do the same for the themepass, sizepass and validate pairs. If a pair should stay on one line, write it as `{ a && b; } || exit 1`. Fix the "stops at first failure" claim in CLAUDE.md, or keep it once it is true. Optionally, add a check to audit.sh that fails when a line in build.sh contains `&&` without a following `|| exit`.

### X-2 [medium] First install by folder copy (install-arthuros.sh or the README method) leaves the skin disabled, so it is not in the skin list

**What you see:** On a brand-new box, after copying the skin over, ArthurOS won't appear in Kodi's skin list until it's switched on under My add-ons.

**Where:** `install-arthuros.sh:63-84`; `README.md:17-37`

**Why (evidence):** Kodi Omega, xbmc/addons/AddonManager.cpp CAddonMgr::FindAddons() calls m_database->SyncInstalled(installed, m_systemAddons, m_optionalSystemAddons). In xbmc/addons/AddonDatabase.cpp CAddonDatabase::SyncInstalled, any add-on found on disk with no DB row is inserted with `enable = 0` unless it is a system or optional-system add-on: `INSERT INTO installed(addonID, enabled, installDate) VALUES('%s', %d, '%s')`. CAddonDatabase::GetDisabled reads `... FROM installed WHERE enabled=0`. The skin picker in xbmc/addons/gui/GUIWindowAddonBrowser.cpp SelectAddonID uses GetAddons(typeAddons, type), and AddonManager.cpp:364-366 makes that OnlyEnabled::CHOICE_YES. Upgrades are fine because the DB row for skin.arthuros already exists, which is why the Pi 4 works. On a new box, for example the 7" 1024x600 panel or a reinstalled SD card, the installer's closing line 82 'Settings > Interface > Skin > Skin > ArthurOS' and README lines 26 and 36 point at a list where ArthurOS will not appear. README line 19 also says copying the folder is 'more reliable' than the zip installer.

**Proposed fix:** The fix goes in install-arthuros.sh (hand-maintained) and README.md. No generator is involved.

(a) In the remote heredoc, set FRESH=yes when "$ADDONS/skin.arthuros" did not exist before the copy. After the copy, and while Kodi is still stopped, run this as $KUSER: `as_kodi python3 - "$KHOME/.kodi/userdata/Database" <<'EOF'`. The script picks the highest-numbered Addons*.db (Addons33.db on Kodi 21) and runs `INSERT OR IGNORE INTO installed(addonID,enabled,installDate) VALUES('skin.arthuros',1,datetime('now')); UPDATE installed SET enabled=1 WHERE addonID='skin.arthuros'`. This survives SyncInstalled, which only inserts ids that are missing. Use python3's sqlite3 module rather than the sqlite3 CLI.

(b) If no Addons DB exists (Kodi never started on this box), print: "First install: Kodi has to see the skin once. Enable it in Add-ons > My add-ons > Look and feel > Skin > ArthurOS > Enable, then pick it in Settings > Interface > Skin." An alternative is to start Kodi and run `kodi-send --action="EnableAddon(skin.arthuros)"`. Per AddonBuiltins.cpp EnableAddon, that pops a Yes/No dialog, which is tappable on the touch panel.

(c) In README.md, add the same "first install: enable under My add-ons" note to both the LibreELEC and the Raspberry Pi OS sections. Change "more reliable than Kodi's zip installer" so it applies to updates only, and say that on a first install the zip installer enables the skin by itself while a folder copy leaves it disabled.

### X-3 [low] netbt.py: a saved open (no-password) Wi-Fi network that fails to connect gives no message at all (ask Vince first)

**What you see:** If a saved Wi-Fi network without a password fails to connect, nothing tells you; the list just reappears.

**Where:** `skin.arthuros/scripts/netbt.py:197-214`

**Why (evidence):** In wifi_connect(), for a network in `saved`, when `nmcli connection up` fails and nm_denied(err) is false, line 209 runs `if not net.get("secure") or not dialog.yesno(...): return False`. For an open network, net['secure'] is False, so the function returns at once. The dialog.ok with wifi_explain(err) that the not-saved path shows (line 240) never runs. The busy dialog is already closed (line 201), so the list just comes back.

**Proposed fix:** In skin.arthuros/scripts/netbt.py, wifi_connect(), replace the single line-209 condition with:

```
if not net.get("secure"):
    dialog.ok(WIFI_HEADING, "Couldn't connect to %s.[CR]%s" % (ssid, wifi_explain(err)))
    return False
if not dialog.yesno(WIFI_HEADING, "Couldn't connect to %s.[CR]%s[CR][CR]"
                    "Enter the password again?" % (ssid, wifi_explain(err))):
    return False
```

No generator or build step is involved, because this is a hand-maintained script.

### X-4 [low] netbt.py: the 'not allowed to manage networks' fix names the SSH user, not the user Kodi runs as, and the docstring assumes a login session (ask Vince first)

**What you see:** If the box refuses to change Wi-Fi settings, the fix it suggests may name the wrong user account, so following it may not help.

**Where:** `skin.arthuros/scripts/netbt.py:10-12`; `skin.arthuros/scripts/netbt.py:107-112`; `README.md:39-40`

**Why (evidence):** The docstring (lines 10-12) says 'Kodi runs in the local login session, which NetworkManager's default polkit rules allow'. On Vince's Pi 4, Kodi runs as a systemd service with no logind seat session (CLAUDE.md, 'Vince's setup'), so polkit's allow_active rules do not apply. Every nmcli change then depends on a group rule. When NetworkManager refuses, show_nm_denied() (lines 107-112) tells him to run `sudo usermod -aG netdev $USER` over SSH. $USER there is whoever logged in over SSH, not necessarily the account the Kodi service runs as; install-arthuros.sh lines 30-37 exist precisely because they can differ. The message also asks for a reboot, when restarting the Kodi service would pick up the new group. README line 40 repeats the same `$USER` command. CLAUDE.md already lists 'polkit may refuse NetworkManager for a service user' as untested.

**Proposed fix:** Ask Vince first, since this is his script. Edit the hand-maintained skin.arthuros/scripts/netbt.py; it is not generated.

1. Rewrite the docstring at lines 10-12 to say: "If Kodi runs as a systemd service with no login session, NetworkManager's polkit defaults (and Debian's netdev/sudo rule, which needs an active local session) do not apply, so a polkit rule for the Kodi user is needed."

2. Change show_nm_denied() so it names the real account and the fix that works for a sessionless service. Use `import getpass` and `user = getpass.getuser()`, then show:
"NetworkManager refused the change: user '%s' isn't allowed to manage networks.[CR]Fix it once over SSH: create /etc/polkit-1/rules.d/50-arthuros-nm.rules allowing org.freedesktop.NetworkManager.* for subject.user == '%s', then restart Kodi."
Keep it short enough to fit the OK dialog. You can also suggest the netdev group, but only for a Kodi that runs in a desktop or login session.

3. Make the same change in README.md:39-40. Give the rule file contents:
polkit.addRule(function(action, subject) { if (action.id.indexOf("org.freedesktop.NetworkManager.") == 0 && subject.user == "KODIUSER") return polkit.Result.YES; });
Name it as "the user Kodi runs as" (install-arthuros.sh prints it as "Kodi runs as '...'"), not $USER. Optionally have install-arthuros.sh offer to install this rule for $KUSER.

### X-5 [low] install-arthuros.sh fails on LibreELEC (no sudo) and leaves Kodi stopped with the skin removed if a later step fails

**What you see:** The install script won't work on the LibreELEC boxes, and if it fails partway it can leave Kodi switched off and the skin missing.

**Where:** `install-arthuros.sh:43`; `install-arthuros.sh:57-79`

**Why (evidence):** The remote script always calls `sudo systemctl stop/start` (lines 59 and 78), and as_kodi uses `sudo -u` whenever KUSER differs from ME. LibreELEC (his ROKbox and Pi 3B+, per CLAUDE.md) logs in as root and has no sudo binary, so line 59 fails with 'sudo: command not found'. Under `set -euo pipefail` the install aborts. Separately, nothing restarts Kodi on error. If `as_kodi cp -r` (line 73) fails after line 59 stopped the service and line 69 moved the old skin to $BK, the script exits with Kodi stopped and no skin.arthuros in addons. When Kodi is next started, the missing skin makes it fall back to Estuary.

**Proposed fix:** Edit only the remote script part of install-arthuros.sh (the text between `<<'PI'` and `PI`).
(a) Run commands without sudo when already root: `SUDO=sudo; [ "$(id -u)" -eq 0 ] && SUDO=`. Use `$SUDO systemctl stop/start "$SVC"`. Change as_kodi to: `as_kodi() { if [ "$KUSER" = "$ME" ]; then "$@"; elif [ "$(id -u)" -eq 0 ]; then su -s /bin/sh "$KUSER" -c "$(printf '%q ' "$@")"; else sudo -u "$KUSER" "$@"; fi; }`. When root, running the commands directly and then `chown -R "$KUSER"` also works.
(b) Pick the right service. Try exact names first and fall back to the old search: `for u in kodi.service kodi-gbm.service kodi-standalone.service; do systemctl cat "$u" >/dev/null 2>&1 && { SVC=$u; break; }; done`. Otherwise keep the current search, but filter out the helper units, e.g. `grep -iE '^kodi(-gbm|-standalone)?\.service$'`. Without this, LibreELEC gets kodi-autostart.service.
(c) After `WAS_ACTIVE=yes`, add `restore() { rc=$?; if [ ! -d "$ADDONS/skin.arthuros" ] && [ -n "${BK:-}" ] && [ -d "$BK" ]; then as_kodi mv "$BK" "$ADDONS/skin.arthuros"; fi; [ "$WAS_ACTIVE" = yes ] && $SUDO systemctl start "$SVC"; rm -rf "${TMP:-}"; exit $rc; }; trap restore EXIT`. Then remove the plain start at lines 76-79. The trap runs the start on success too, so Kodi is started exactly once.
(d) Better still, copy to `$ADDONS/skin.arthuros.new` first and only then `mv`, so a failed copy never removes the old skin.

### X-6 [low] audit.sh does not check the changelog and README version stamps that CLAUDE.md says it checks

**What you see:** Not visible on the box; a future release could ship with an out-of-date version number in the changelog or README.

**Where:** `audit.sh:17-21`; `audit.sh:66-70`; `CLAUDE.md:143-146`

**Why (evidence):** CLAUDE.md lists the stamps to bump (addon.xml, xml/SkinSettings.xml, xml/Includes_Chrome.xml, changelog.txt, README.md) and says 'audit.sh checks the stamps match'. audit.sh only compares the addon.xml version with Includes_Chrome.xml, SkinSettings.xml and the xml768 copies (lines 19-21 and 69-70). changelog.txt's first line (currently 'v0.9.6') and README.md's 'Current version' line and unzip examples (lines 10, 23, 33) are never checked. Today they match.

**Proposed fix:** Add these lines to audit.sh after the VER line (audit.sh is hand-maintained, not generated):

R="$(dirname "$0")/README.md"
chk "changelog leads with this version" 'head -1 $S/changelog.txt | grep -qx "v$VER"'
chk "README names this version"         'grep -q "Current version: $VER\*\*" "$R" && test $(grep -c "skin.arthuros-$VER.zip" "$R") -ge 2 && ! grep -q "skin.arthuros-[0-9.]*\.zip" "$R" -e x 2>/dev/null; grep -o "skin.arthuros-[0-9][0-9.]*[0-9]\.zip" "$R" | grep -qvx "skin.arthuros-$VER.zip" && exit 1 || exit 0'

A simpler and safer version of the README check:

chk "README names this version" 'grep -q "Current version: $VER\*\*" "$R" && ! grep -o "skin.arthuros-[0-9][0-9.]*[0-9]\.zip" "$R" | grep -vqx "skin.arthuros-$VER.zip"'

This checks that the Current version line matches VER, including the closing ** of the bold markup. It also fails if any zip name with a concrete version number names a different version. The generic `<version>` placeholder on README line 185 is not matched, because the pattern needs a digit right after "skin.arthuros-".

### X-7 [low] mousewatch counts any device with REL_X|REL_Y as a mouse, and Touch mode has no override, so the pointer can stay on forever on a touch-only box *(verifier: uncertain - needs a test on the box)*

**What you see:** On a touch screen with no mouse, the mouse pointer may stay visible all the time in Touch mode, and there's no setting to hide it.

**Where:** `skin.arthuros/scripts/mousewatch.py:24-36`; `skin.arthuros/xml/Variables.xml:32`; `skin.arthuros/xml/Variables.xml:39`; `skin.arthuros/xml/SkinSettings.xml:85-93`

**Why (evidence):** mouse_present() returns True if any block in /proc/bus/input/devices has a `B: REL=` mask with bits 0 and 1 set. It never looks at which device it is. Many USB touch controllers expose a second HID 'Mouse' interface alongside the multitouch digitizer, and 2.4 GHz keyboard dongles and Logitech receivers always register a mouse node even when no mouse is paired. Any of these makes the script set Window(Home).Property(arthuros.mouse)=1 permanently. Variables.xml:32/39 then never blanks the pointer texture. Touch mode has no setting to force the pointer on or off. The parsing itself is correct: the lowest word is words[-1], `&` binds tighter than `==`, and /proc/bus/input/devices is world-readable, so this works for a systemd service user. Whether Vince's two touch controllers expose such a node is unverified; one `cat /proc/bus/input/devices` on each box settles it.

**Proposed fix:** In mousewatch.py, parse each block's `I: Bus= Vendor= Product=` line and its `B: ABS=` mask. Ignore a REL device when the same Vendor/Product also has a block with ABS_MT_POSITION_X, bit 0x35 of the ABS mask. That is the touch controller's own mouse interface. Optionally also require a `mouse` entry in `H: Handlers=`. Add a skin setting `touch.pointer` (Auto / Always hide / Always show) in SkinSettings.xml, which is hand-maintained. Have Variables.xml PointerTex check it before Window(Home).Property(arthuros.mouse), and have mousewatch skip detection when it is not Auto. Log the device name that made it decide 'mouse present' (xbmc.log at LOGINFO when the value changes), so a false positive can be diagnosed from kodi.log.

## Found by the completeness pass

| # | Sev | Problem |
|---|---|---|
| C-1 | medium | Every settings choice list opens with the current value unreadable: dark-red text on the blue selection bar (contrast 1.03:1) |
| C-2 | medium | Login screen's task bar and menu let anyone skip the profile login (Start opens Home as the master profile) |
| C-3 | medium | Recording info shows five guide-only buttons that do nothing, one of them blank |
| C-4 | medium | Subtitle search and game Ports/Players dialogs: the highlighted row in the list without focus turns white on white |
| C-5 | medium | Text outside Latin-1 disappears everywhere: Tamzen fonts have only 189 glyphs, so ' – … and any Cyrillic, Greek, Polish or CJK title are dropped |
| C-6 | low | Defaults.xml: focused edit fields look the same as unfocused, and every togglebutton draws no button face or state |

### C-1 [medium] Every settings choice list opens with the current value unreadable: dark-red text on the blue selection bar (contrast 1.03:1)

**What you see:** Tap any list setting (audio output, resolution, skin colours, language, subtitle language...). The popup opens with the highlighted row on the current choice, and that row's text is almost invisible: dark red on blue. In multi-select lists you can't read the row you just ticked.

**Where:** `skin.arthuros/xml/DialogSelect.xml:54-74 (list 3 XL focusedlayout: labels textcolor textinv, no <selectedcolor>)`; `skin.arthuros/xml/DialogSelect.xml:96-118 (list 3 normal focusedlayout)`; `skin.arthuros/xml/DialogSelect.xml:141-160, 176-195 (list 6 focusedlayouts, same)`; `skin.arthuros/xml/Defaults.xml:16 (label default <selectedcolor>marked</selectedcolor>, which lands on every label without its own)`; `skin.arthuros/xml768/DialogSelect.xml:169, 211, 256, 291 (tallpass copy)`; `skin.arthuros/xml/View_51_Poster.xml:39, skin.arthuros/xml/View_52_IconWall.xml:39, skin.arthuros/xml/FileBrowser.xml:54,91,135 (same gap for the playing/marked item when it has focus)`; `palettecheck.py:50-51 (checks 'marked on panel' and 'textinv on select', never 'marked on select')`

**Why (evidence):** Kodi marks the current value as selected and then focuses it. xbmc/settings/windows/GUIControlSettings.cpp GetFileItem(): `if (selectedValues.find(value) != selectedValues.end()) item->Select(true);`. xbmc/dialogs/GUIDialogSelect.cpp OnInitWindow(): `m_viewControl.SetSelectedItem(std::max(GetSelectedItem(), 0));`. A selected item's labels draw in selectedcolor: xbmc/guilib/GUIListLabel.cpp SetSelected() `m_label.SetColor(selected ? CGUILabel::COLOR_SELECTED : CGUILabel::COLOR_TEXT)`, and GUIListItemLayout.cpp:89 `m_group.SetState(item->IsSelected() || m_isPlaying, m_focused)`. Defaults reach labels inside layouts because xbmc/guilib/GUIIncludes.cpp Resolve() runs SetDefaults() on every child <control> recursively. Includes_Lists.xml:72,79,101,108 sets selectedcolor textinv for this reason, but DialogSelect's hand-written layouts don't. Contrast of marked against select, computed from colors/*.xml: default 1.03:1, Colorblind-Safe 1.06, High-Contrast-Light 1.12, High-Contrast-Dark 1.17, Paper 1.20, Phosphor 1.21, Amber 1.52, Acorn 1.59. Multi-select lists use the same colour as the only 'ticked' mark, so a focused ticked row is also unreadable there.

**Proposed fix:** The proposed fix is right; these are the exact places to change.

1. **DialogSelect.xml (hand-maintained).** In skin.arthuros/xml/DialogSelect.xml, add `<selectedcolor>textinv</selectedcolor>` next to `<textcolor>textinv</textcolor>` on all 9 focused labels: lines 66, 72, 108, 114, 152, 157, 187, 192 and the panel 10811 label at 261.
2. **Tick image.** In each item and focused layout of lists 3 and 6, add an image control with `<visible>ListItem.IsSelected</visible>`, using an existing radio/check texture, so the ticked state doesn't depend on colour alone. The labels' left offset has room for it.
3. **xml768.** Don't edit it by hand. Rebuild with build.sh so tallpass regenerates xml768/DialogSelect.xml.
4. **Same fix elsewhere.**
   - View_51_Poster.xml and View_52_IconWall.xml (hand-maintained): add `<selectedcolor>textinv</selectedcolor>` to the focusedlayout label.
   - FileBrowser.xml is generated: change the label strings in genwindows.py `file_browser()` (lines 66/72, 103/109 and 147/153 of the output) to add the same tag.
5. **palettecheck.py.** Add the pair `"marked on select": ratio(P["marked"], P["select"])`. Either report it as informational, or assert that no textinv label lacks a selectedcolor. Every palette fails 4.5:1 for this pair by design, so it shouldn't become a hard target.
6. **audit.sh.** Add a check that every `<control type="label">` inside a `<focusedlayout>` whose textcolor is textinv also has a `<selectedcolor>`.

### C-2 [medium] Login screen's task bar and menu let anyone skip the profile login (Start opens Home as the master profile)

**What you see:** If profiles with a login screen are ever turned on (e.g. a locked kids' profile), anyone can tap Start on the login screen and get the master profile's desktop and media without the password.

**Where:** `skin.arthuros/xml/LoginScreen.xml:6-7 (Chrome_Desktop + Chrome_Menubar)`; `skin.arthuros/xml/LoginScreen.xml:70 (<include content="Chrome_Taskbar">: Start 9100 = ActivateWindow(Home), Settings 9103 = ActivateWindow(Settings), Touch-mode Back 9105)`; `skin.arthuros/xml/Includes_Chrome.xml:96-101, 219-225 (the Start and Settings onclicks)`; `genwindows.py:78-91 fullwindow() (always emits Chrome_Taskbar, including for LoginScreen)`; `skin.arthuros/xml768/LoginScreen.xml`

**Why (evidence):** xbmc/profiles/ProfileManager.cpp Load(): 'the login screen runs as the master profile' then `if (m_usingLoginScreen) SetCurrentProfileId(0);`. xbmc/application/Application.cpp Initialize(): `if (profileManager->UsingLoginScreen()) ActivateWindow(WINDOW_LOGIN_SCREEN)`. CGUIWindowLoginScreen::OnAction (xbmc/windows/GUIWindowLoginScreen.cpp) blocks only keymap ACTION_BUILT_IN_FUNCTION ('don't allow built in actions to act here except shutdown related ones'). A skin button's onclick never passes through it: xbmc/guilib/GUIAction.cpp ExecuteActions() posts GUI_MSG_EXECUTE, and CApplication::OnMessage case GUI_MSG_EXECUTE runs it straight away (ExecuteXBMCAction). The only window-level gate, CGUIWindowManager::ActivateWindow_Internal, calls g_passwordManager.CheckMenuLock(), and that doesn't cover Home. The profile password is checked only when a profile is picked in list 52 (IsProfileLockUnlocked).

**Proposed fix:** Change genwindows.py only, so both xml/ and xml768/ (made by tallpass.py) pick it up. The proposed fix is right but misses the navigation targets:
1. Give fullwindow() a `taskbar=True` parameter. When it is False, don't write the Chrome_Taskbar include and point `up` at the window's default control rather than 9100. At genwindows.py:1559, pass `taskbar=(name != "LoginScreen")`.
2. For LoginScreen, add a touch-sized Power button (for example id 9100, so the existing onup/ondown="9100" on grouplist and list 52 still land on a real control; otherwise rewrite those targets in the generated body). Use `<onclick>ActivateWindow(ShutdownMenu)</onclick>`, placed in the bottom 32px strip (or under the profile list) where the taskbar used to be, using the same Height_30_XL/touchmode sizing as the other buttons. The skin onclick reaches it through GUI_MSG_EXECUTE, so OnAction doesn't block it, and ShutdownMenu holds only power, LogOff and master-mode items, which are safe.
3. Add an audit.sh check that skin.arthuros/xml/LoginScreen.xml and xml768/LoginScreen.xml contain no `ActivateWindow(Home)` or `ActivateWindow(Settings)`.
Then rerun build.sh.

### C-3 [medium] Recording info shows five guide-only buttons that do nothing, one of them blank

**What you see:** Open a recording's info and you get 'Play programme', 'Switch to channel', a blank button, 'Add timer' and 'Set reminder' as well as Play/Find similar/OK. Tapping any of those five does nothing.

**Where:** `skin.arthuros/xml/DialogPVRInfo.xml:99-111 (buttons 10 Play programme, 5 Switch, 6 [no label], 9 Add timer, 11 Reminder: no <visible>)`; `skin.arthuros/xml768/DialogPVRInfo.xml:208-218`; `genwindows.py:615 ("DialogPVRInfo": [(10,19190),(8,19687),(5,19000),(6,None),(9,19061),...] passed to info_dialog() at 1829 with no per-window visibility)`

**Why (evidence):** DialogPVRInfo.xml is shared by two dialogs. xbmc/pvr/dialogs/GUIDialogPVRRecordingInfo.cpp loads 'DialogPVRInfo.xml', and its OnMessage handles only CONTROL_BTN_OK (7), CONTROL_BTN_PLAY_RECORDING (8) and CONTROL_BTN_FIND (4); it never hides or labels anything else. Only GUIDialogPVRGuideInfo.cpp sets the label of button 6 (19059/19060/264) and hides 8/10/6/9/11 when they don't apply. Estuary's DialogPVRInfo.xml gates 5, 10, 6, 9 and 11 with Window.IsActive(PVRGuideInfo), and 8 and 4 with PVRGuideInfo | PVRRecordingInfo.

**Proposed fix:** In genwindows.py:
1. Let INFO_BUTTONS rows carry an optional third element, a visible condition. Set G = "Window.IsActive(PVRGuideInfo)" and make the DialogPVRInfo row [(10,19190,G),(8,19687),(5,19000,G),(6,264,G),(9,19061,G),(11,826,G),(4,19003),(7,186)]. Button 6's 264 (Record) is only a fallback. Kodi overwrites it in GUIDialogPVRGuideInfo::OnInitWindow and hides the button when it doesn't apply.
2. In info_dialog()'s row(), change the loop to `for cid, sid, *vis in items:` and append `<visible>{vis[0]}</visible>` when vis is set.
3. Change the stubs() set at about line 606 to `{c for c, *_ in rows}`.

Then rebuild. The recording dialog will show 8 in row 9001 and 4 and 7 in row 9002. Both grouplists are centre-aligned and still navigate to each other.

Optionally, add an audit.sh check that every DialogPVRInfo button other than 4, 7 and 8 has a <visible>, and that no button there lacks a <label>.

### C-4 [medium] Subtitle search and game Ports/Players dialogs: the highlighted row in the list without focus turns white on white

**What you see:** In 'Find subtitles' the first result looks like an empty row until you tap into the results list. The service name goes blank as soon as you move to the results. In the game Ports and Players dialogs the selected controller row vanishes whenever a button has focus.

**Where:** `skin.arthuros/xml/DialogSubtitles.xml:37-40, 46-49 (list 150: fill only <visible>Control.HasFocus(150)</visible>, label always textinv)`; `skin.arthuros/xml/DialogSubtitles.xml:77-80, 86-89 (list 120 results, same pattern, on white panel_sunken)`; `skin.arthuros/xml/DialogSubtitles.xml:3 (<defaultcontrol>150</defaultcontrol>: focus starts on the service list)`; `skin.arthuros/xml/Includes_Games.xml:126-128, 135-137 (ports list 3) and 188-189, 195-196 (players list 7)`; `genwindows.py:1586-1588, 1615-1617 subtitles_dialog(); genwindows.py:1742-1744, 1779-1780 game_controllers()`; `skin.arthuros/xml768/DialogSubtitles.xml, skin.arthuros/xml768/Includes_Games.xml`

**Why (evidence):** A container draws its focusedlayout for the selected item even when another control has focus. The skin hides only the blue fill in that case and keeps the labels textinv (white). media/panel_sunken.png's centre pixel is (255,255,255) and panel_sunken_grey.png's is (221,221,221), so the label is white on white (1:1) or white on light grey. Kodi's GUIDialogSubtitles.cpp fills CONTROL_SUBLIST 120 while focus stays on CONTROL_SERVICELIST 150, the default control. GUIAgentWindow / Arthur_GameAgents open with defaultcontrol 3 (a button), so list 7's selected row starts invisible.

**Proposed fix:** Change genwindows.py subtitles_dialog() (about lines 1580-1620, both the touch/ExtraLarge 44px focusedlayout and the 28px one) and game_controllers() (about lines 1735-1785, ports list 3 and agents list 7, both 50px and 34px layouts). Leave every list label in the focusedlayout at its normal colour (text, or textdim for the secondary/Label2 label, matching the itemlayout). Then add a second copy with textinv and `<visible>Control.HasFocus(N)</visible>`, with the normal copy gated on `!Control.HasFocus(N)`. A simpler equivalent: keep one label and switch only its colour, using two labels or a `$VAR` colour if the generator has a helper.

Optionally draw an unfocused marker so the user can still see the current choice, for example the fill with `colordiffuse="textdisabled"` and `<visible>!Control.HasFocus(N)</visible>` behind normal-coloured text.

Rebuild so both xml/ and xml768/ are regenerated. Add an audit.sh check that flags any focusedlayout whose fill is HasFocus-gated while its textinv label is not.

Drop the subtitles-results part of the impact: Kodi auto-focuses list 120 when results arrive (GUIDialogSubtitles::Process). The real symptoms are the blank service row in list 150 after a search, the invisible selected row in Players list 7 when the dialog opens (defaultcontrol 3), and the invisible Ports row when Close or Reset has focus.

### C-5 [medium] Text outside Latin-1 disappears everywhere: Tamzen fonts have only 189 glyphs, so ' – … and any Cyrillic, Greek, Polish or CJK title are dropped

**What you see:** YouTube and Plex titles lose apostrophes, dashes and '...'. Anything in another alphabet (Russian, Greek, Japanese, Polish...) shows as a blank row or blank tile, even though the item is there.

**Where:** `skin.arthuros/fonts/Tamzen8x16r.ttf (and the other 7 Tamzen*.ttf: 189-190 code points each, highest U+00FF)`; `skin.arthuros/xml/Font.xml:7-31 (every font in every fontset is a Tamzen file; same in the other 6 fontsets)`; `mkfonts.py:21, 58 (writes only Tamzen faces)`; `skin.arthuros/xml768/Font.xml`

**Why (evidence):** Parsing the cmap of every shipped TTF gives 189-190 code points, all <= U+00FF. Missing: U+2018/2019/201C/201D curly quotes, U+2013/2014 dashes, U+2026 ellipsis, U+2022, U+2122, U+20AC, Latin Extended-A (Ł), Greek, Cyrillic, CJK, symbols. Kodi has no per-glyph fallback: xbmc/guilib/GUIFontTTF.cpp shapes with HarfBuzz on the one m_face and looks up glyphs with `FT_Get_Char_Index(m_face, letter)` (line 879). A missing code point maps to glyph 0, which in Tamzen is empty: PIL renders U+2019 as a 0x0 mask, so "Don’t – Part 1…" draws as "Dont  Part 1". Kodi's own en_gb strings are all Latin-1, so the skin's own menus pass textfit.py. The damage is to content: YouTube/Plex/Internet Archive titles, EPG data, add-on names and descriptions, notifications, and native-script keyboard layout names.

**Proposed fix:** 1. Add a font build step, mkttf.py, using fontTools, run before mkfonts.py in build.sh and listed in CLAUDE.md. For each Tamzen face, copy in glyphs for a fixed set of code points and write the result over the shipped TTFs, or to new files that mkfonts.py f() points at:
   - Tier 1, required in all 8 faces: U+2010-2015, 2018-201F, 2022, 2026, 2032-2033, 20AC, 2122. These are about 20 simple glyphs, so draw them by hand in each Tamzen cell size in a small Python table. Simplest form: alias them to existing Latin-1 shapes (’ to ', “” to ", – — to -, … to a 3-dot glyph). That keeps every size crisp.
   - Tier 2: Latin Extended-A, Greek and Cyrillic. Copy them from GNU Unifont (GPL-2.0+ or OFL-1.1) natively into the 8x16 faces and at exactly 2x into the 32 px faces. For the 6x12, 7x14 and 10x20 faces, take them from a bitmap font drawn at those sizes, such as Terminus (OFL), which covers Latin Ext, Greek and Cyrillic at 12, 14 and 20. Do not scale Unifont by a non-integer factor.
2. Alternative if merging is too much work: have mkfonts.py add an extra fontset ("Unicode") whose content fonts use Unifont at 16 and 32, for users who browse non-Latin content.
3. Add a check to audit.sh: parse each TTF named in xml/Font.xml and fail if any Tier 1 code point is missing (with Tier 2 too, if adopted). Also extend textfit.py so it does not count a missing glyph as zero width.

### C-6 [low] Defaults.xml: focused edit fields look the same as unfocused, and every togglebutton draws no button face or state

**What you see:** With a remote or keyboard, focus seems to vanish when it lands on a text field in Settings or add-on settings. Toggle buttons (event log level, PVR managers, file browser) show as bare text with no button and no on/off state.

**Where:** `skin.arthuros/xml/Defaults.xml:134-147 (edit: texturefocus == texturenofocus panel_sunken.png, focusedcolor text == textcolor)`; `skin.arthuros/xml/Defaults.xml:55-69 (togglebutton: <usealttexture>true</usealttexture> with no alttexturefocus/alttexturenofocus)`; `skin.arthuros/xml/SettingsCategory.xml:111, skin.arthuros/xml/DialogSettings.xml:73, skin.arthuros/xml/DialogAddonSettings.xml:79 (edit templates 12 that inherit it)`; `skin.arthuros/xml/EventLog.xml:33, DialogPVRChannelManager.xml:80, DialogPVRGroupManager.xml:50, FileBrowser.xml:168 (togglebuttons)`; `skin.arthuros/xml768/Defaults.xml:55, 134`

**Why (evidence):** CGUIEditControl derives from CGUIButtonControl and draws texturefocus when focused. Here texturefocus and texturenofocus are the same image and the text colour doesn't change, so a focused edit row (Kodi clones template 12 for every 'edit' setting: device name, web-server user/password, proxy, add-on text settings, PVR search fields) has no visible focus. For togglebuttons, xbmc/guilib/GUIControlFactory.cpp:1026 reads usealttexture into toggleSelect. In xbmc/guilib/GUIToggleButtonControl.cpp Process(), `m_bSelected = m_toggleSelect->Get()` is then always true, and Render() draws only m_selectButton, built from the (empty) alt textures. So the button never shows a face, a focus highlight or Kodi's SET_CONTROL_SELECTED state.

**Proposed fix:** In the hand-maintained skin.arthuros/xml/Defaults.xml, togglebutton default:
- Delete `<usealttexture>true</usealttexture>`. Kodi's own SET_CONTROL_SELECTED then drives the state.
- Add `<alttexturefocus border="2" colordiffuse="select">select_bevel.png</alttexturefocus>`.
- Add `<alttexturenofocus border="2" colordiffuse="facetint">button_down.png</alttexturenofocus>`.
- Result: "selected" shows as a pressed face, and the focused label (textinv) always sits on the select colour.

Edit default:
- Change texturefocus to `<texturefocus border="2" colordiffuse="select">select_bevel.png</texturefocus>`, or keep panel_sunken.png with colordiffuse="select".
- Set `<focusedcolor>textinv</focusedcolor>` to match button and spincontrolex.

Then rebuild so tallpass regenerates xml768/Defaults.xml.

Add audit.sh checks:
- Fail if any togglebutton default or control has usealttexture equal to true without alttexturefocus.
- Fail if the edit default's texturefocus equals its texturenofocus.

## Refuted (no change needed)

- **Toolbar 'Up' button runs bare 'ParentDir', which does not reliably go up one folder (at the start folder it closes the window or does nothing; can go past a desktop tile's start folder)**: refuted: I checked the Omega source. The finding's main claims are wrong, and its proposed fix would cause the very bug it describes.  1. Where the button is. skin.arthuros/xml/Includes_Media.xml:22-26 (hand-maintained) has button 9500 with label $LOCALIZE[31901] and `<onclick>ParentDir</onclick>`. The generated xml768 copies are Includes_Media.xml:25 and line 199 of AddonBrowser, MyFavourites, MyGames, MyMusicNav, MyPVR*, MyPics, MyPlaylist, MyPrograms and MyVideoNav.  2. ParentDir is not a builtin. I fetched all 16 Omega xbmc/interfaces/builtins/*.cpp tables and none contains "parentdir" or "parentfolder". So CApplication::ExecuteXBMCAction (Application.cpp l.3095-3122) passes it to CActio
- **package.sh zips whatever is in skin.arthuros/ with no exclude list and no check of the result**: refuted: The facts in the finding are correct, but it does not describe a defect, so I'm refuting it.  What I checked: - `/home/user/Arthuros/package.sh` does what the finding says. Lines 8-10 delete `__pycache__` folders under `skin.arthuros`, delete any old zip, then run `zip -qr "dist/skin.arthuros-$VER.zip" skin.arthuros`. There is no exclude list and no check of the finished zip. - The zip comes out in the right shape: one top-level `skin.arthuros/` folder with `addon.xml` inside it. - `skin.arthuros/addon.xml` asks for `xbmc.gui` 5.17.0 and declares `res` entries for the `xml` and `xml768` folders. - The skin folder is clean today. It holds 1354 files on disk and git tracks exactly 135
