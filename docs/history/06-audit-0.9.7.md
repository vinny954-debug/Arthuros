# 0.9.7 — the 0.9.6 audit, implemented

Vince asked for a full check of the skin ("menus with no text, broken links,
no volume while playing a video, the play bar pops up in the middle when I
touch the screen, and it's not obvious how to close it; touch alone must
work as well as a keyboard"). `docs/audit-0.9.6.md` is the result: 92 findings
across ten areas, each verified against the Kodi Omega source by a separate
reviewer, with 2 refuted.

Root causes of his three reports:
- Volume: no tappable volume control anywhere. The menu-bar gauge was display
  only, DialogVolumeBar opens only after a volume key, and the sliderex in
  OSD > Audio had no textures.
- OSD in the middle: `genwindows.dialog()` always centred; the OSD is now a
  bottom bar (`anchor="bottom"`).
- Hard to close: the OSD is modal, so a tap on the picture went to it and did
  nothing; "Close" ran Action(FullScreen), which leaves playback. Now a
  full-screen tap catcher and Hide close it, and Menus leaves on purpose.

How it was built: 9 parallel packages in wave 1 and 8 in wave 2, each owning
disjoint files (git worktrees), each reviewed, then merged. A final pass
verified every finding (87 fixed, 6 partly by design) and ran touch-only and
remote walkthroughs; their 39 follow-ups were fixed. New regression checks:
labelcheck.py, logincheck.py, p12check.py and a much stricter validate.py
(Kodi tables in vendor/kodi/).

Partly fixed by design: info-dialog button faces stay 30 px (hit rects 34 px);
scrollbars beside panels/grouplists keep the 18 px look; context-menu bottom
margin; calibration art (Kodi rescales it); a long localized "Group: <name>"
can still be cut; other alphabets need the Unicode fontset.
