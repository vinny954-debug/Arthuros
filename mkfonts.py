#!/usr/bin/env python3
"""Write xml/Font.xml and fonts/Unicode.xml.

Tamzen is a bitmap font drawn as outlines: at its native sizes (12, 14, 16,
20) one font pixel is one screen pixel, and at exactly twice those sizes one
font pixel is a crisp 2x2 block. Every size below is one of those, so no
fontset ever blurs.

Two families of names:
  content - tiny, small, normal, bold, big, bigbold, caps, bigcaps, tight
  chrome  - chrome, chromebold, chromesmall: menu bar, task bar, title bars.
The chrome names never grow past 20px, so the extra-large fontsets can double
the content without the fixed 26px bars overflowing.

Tamzen covers Latin-1 only (U+0020-00FF). Kodi has no per-glyph fallback
(GUIFontTTF looks every letter up in the one face), so anything else - curly
quotes, dashes, ellipsis, Polish, Greek, Cyrillic, CJK - draws as nothing.
The extra "Unicode" fontset maps every name onto Kodi's own arial.ttf (DejaVu
Sans plus a CJK fallback). The skin does not ship it: GUIFontManager::LoadTTF
looks for a font file in the skin's fonts/ folder, then special://home/media/
Fonts, then special://xbmc/media/Fonts, where every Kodi build has arial.ttf
(LibreELEC: upstream's; Debian / Raspberry Pi OS: their own DejaVu Sans +
Droid Sans Fallback build). A font that fails to load also falls back to it.

That fontset lives in its own file, fonts/Unicode.xml: Kodi lists and loads
fontsets from every .xml in the skin's fonts/ folder after Font.xml's
(GUIFontManager::LoadFonts, CSkinInfo::SettingOptionsSkinFontsFiller). One file
serves both layouts (both are 1024 wide, and Font.xml is the same in xml/ and
xml768/). textfit.py and preview.py read only Font.xml, so they never measure
it - they could not, the font is not in the skin. Its sizes give each arial
size the line height of the Tamzen size it replaces. Omega ignores the
fontset "unicode" attribute (nothing reads it, and nothing switches fontset by
language): the user picks the fontset in Settings > Interface > Skin > Fonts.
"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "skin.arthuros", "xml", "Font.xml")
OUT_UNI = os.path.join(HERE, "skin.arthuros", "fonts", "Unicode.xml")

def f(px, bold=False):
    cell = {12: "6x12", 14: "7x14", 16: "8x16", 20: "10x20",
            24: "6x12", 28: "7x14", 32: "8x16", 40: "10x20"}[px]
    return (f"Tamzen{cell}{'b' if bold else 'r'}.ttf", px)

# Tamzen size -> arial.ttf size with about the same line height. Kodi's line
# height is (hhea ascender - descender) / upem * size: 2384/2048 * size for
# arial.ttf, exactly `size` for Tamzen.
UNI = {12: 10, 14: 12, 16: 14, 20: 17, 24: 20, 28: 24, 32: 27, 40: 34}

# id, idloc, comment, content sizes, chrome sizes, all-bold
SETS = [
 ("Default",    13278, "Arthur's own sizes.",
  dict(tiny=12, small=14, normal=16, big=20), dict(chrome=16, chromesmall=14), False),
 ("Large",      31923, "One step up everywhere.",
  dict(tiny=14, small=16, normal=20, big=20), dict(chrome=20, chromesmall=16), False),
 ("LargeBold",  31945, "Large, heavy weight throughout.",
  dict(tiny=14, small=16, normal=20, big=20), dict(chrome=20, chromesmall=16), True),
 ("ExtraLarge", 31946, "Content at twice the bitmap size, for low vision. Lists "
  "and settings switch to taller rows (sizepass.py) while this is active.",
  dict(tiny=24, small=24, normal=28, big=32), dict(chrome=20, chromesmall=16), False),
 ("ExtraLargeBold", 31947, "Extra large, heavy weight throughout.",
  dict(tiny=24, small=24, normal=28, big=32), dict(chrome=20, chromesmall=16), True),
 ("Compact",    31929, "One size down everywhere - more rows per list.",
  dict(tiny=12, small=12, normal=14, big=16), dict(chrome=14, chromesmall=12), False),
 ("Bold",       31930, "Default sizes, heavy weight throughout - easier across a room.",
  dict(tiny=12, small=14, normal=16, big=20), dict(chrome=16, chromesmall=14), True),
]

# Desktop tile captions: 3 rows of tiles, 4 rows, and 5 or 6 rows.
TILE = {"Default": (20, 16, 12), "Large": (20, 16, 14), "LargeBold": (20, 16, 14),
        "ExtraLarge": (28, 20, 16), "ExtraLargeBold": (28, 20, 16),
        "Compact": (16, 14, 12), "Bold": (20, 16, 12)}

def line(name, px, bold, upper=False, extra="", uni=False):
    if uni:
        # one face for everything; Kodi emboldens the outline for style bold
        fn, size = "arial.ttf", UNI[px]
        styles = (["bold"] if bold else []) + (["uppercase"] if upper else [])
    else:
        fn, size = f(px, bold)
        styles = ["uppercase"] if upper else []
    st = f"<style>{' '.join(styles)}</style>" if styles else ""
    return f"    <font><name>{name}</name><filename>{fn}</filename><size>{size}</size>{st}{extra}</font>\n"

def fonts(fid, c, ch, B, uni=False):
    """Every font name the skin uses, for one fontset."""
    L = lambda name, px, bold, upper=False, extra="": line(name, px, bold, upper, extra, uni)
    # names Kodi itself falls back to
    return [L("font10", c["tiny"], B), L("font12", c["small"], B),
            L("font13", c["normal"], B), L("font14", c["normal"], True),
            L("font16", c["big"], B), L("font36", c["big"], True),
            L("font45", c["big"], True),
            L("tiny", c["tiny"], B), L("small", c["small"], B),
            L("normal", c["normal"], B), L("bold", c["normal"], True),
            L("big", c["big"], B), L("bigbold", c["big"], True),
            L("caps", c["normal"], True, True),
            L("bigcaps", c["big"], True, True),
            L("tight", c["normal"], B, extra="<linespacing>1.0</linespacing>"),
            L("chrome", ch["chrome"], B), L("chromebold", ch["chrome"], True),
            L("chromesmall", ch["chromesmall"], B),
            L("tilebig", TILE[fid][0], True), L("tilesmall", TILE[fid][1], True),
            L("tiletiny", TILE[fid][2], True)]

out = ['<?xml version="1.0" encoding="UTF-8"?>\n',
       "<!-- GENERATED by mkfonts.py - edit that, not this. Every size is a native\n"
       "     Tamzen size (12, 14, 16, 20) or exactly double one, so text stays crisp. -->\n",
       "<fonts>\n"]
for fid, idloc, note, c, ch, allbold in SETS:
    out.append(f"\n  <!-- {note} -->\n")
    out.append(f'  <fontset id="{fid}" idloc="{idloc}" unicode="true">\n')
    out += fonts(fid, c, ch, allbold)
    out.append("  </fontset>\n")
out.append("\n</fonts>\n")
open(OUT, "w").write("".join(out))

# The Unicode fontset: Default's layout, every name on Kodi's own arial.ttf.
fid, idloc, note, c, ch, allbold = SETS[0]
uni = ['<?xml version="1.0" encoding="UTF-8"?>\n',
       "<!-- GENERATED by mkfonts.py - edit that, not this. Kodi lists the fontsets in\n"
       "     the skin's fonts/*.xml after Font.xml's. arial.ttf is Kodi's own font\n"
       "     (special://xbmc/media/Fonts) and is not shipped with the skin. -->\n",
       "<fonts>\n\n",
       "  <!-- Every alphabet: arial.ttf (DejaVu Sans + CJK) at Default's line heights. -->\n",
       '  <fontset id="Unicode" idloc="31895" unicode="true">\n']
uni += fonts(fid, c, ch, allbold, uni=True)
uni.append("  </fontset>\n\n</fonts>\n")
open(OUT_UNI, "w").write("".join(uni))
print(f"fonts: {len(SETS)} fontsets written, + Unicode (fonts/Unicode.xml)")
