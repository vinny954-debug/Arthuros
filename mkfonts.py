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

Tamzen covers Latin-1 only (U+0020-00FF, minus a few signs). Kodi has no
per-glyph fallback (GUIFontTTF looks every letter up in the one face), so
anything else draws as nothing. This script therefore also patches the shipped
Tamzen*.ttf in place (idempotent, see patch_face): curly quotes, dashes,
ellipsis and bullet now draw in every Tamzen fontset. Polish, Greek, Cyrillic,
CJK still need the extra "Unicode" fontset, which maps every name onto
Kodi's own arial.ttf (DejaVu Sans plus a CJK fallback). The skin does not ship it: GUIFontManager::LoadTTF
looks for a font file in the skin's fonts/ folder, then special://home/media/
Fonts, then special://xbmc/media/Fonts, where every Kodi build has arial.ttf
(LibreELEC: upstream's; Debian / Raspberry Pi OS: their own DejaVu Sans +
Droid Sans Fallback build). A font that fails to load also falls back to it.

That fontset lives in its own file, fonts/Unicode.xml: Kodi lists and loads
fontsets from every .xml in the skin's fonts/ folder after Font.xml's
(GUIFontManager::LoadFonts, CSkinInfo::SettingOptionsSkinFontsFiller). One file
serves both layouts (both are 1024 wide, and Font.xml is the same in xml/ and
xml768/). preview.py reads only Font.xml; textfit.py also measures this
fontset, from arial.ttf's advance widths in vendor/kodi/arial-advances.json
(the font itself is not in the skin). Its sizes and linespacing give each
arial font at most the line height of the Tamzen size it replaces. Omega
ignores the fontset "unicode" attribute (nothing reads it, and nothing switches fontset by
language): the user picks the fontset in Settings > Interface > Skin > Fonts.
"""
import os, struct, glob
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "skin.arthuros", "xml", "Font.xml")
OUT_UNI = os.path.join(HERE, "skin.arthuros", "fonts", "Unicode.xml")
FONTDIR = os.path.join(HERE, "skin.arthuros", "fonts")

# ---------------------------------------------------------------------------
# Typographic punctuation in the Tamzen faces (patched in place, idempotent).
#
# Online titles (YouTube, Plex, EPG) are full of ’ “ ” – — … that Tamzen does
# not have; Kodi maps a missing code point to glyph 0, which is empty, so
# "Don’t – Part 1…" drew as "Dont  Part 1". Each code point below is added to
# the cmap of every face that lacks it, pointing at an existing Tamzen glyph
# (so it stays pixel-exact at every size), and two glyphs are drawn as pixel
# rectangles: … (three dots in one cell) and • (a square dot on the hyphen's
# centre line). Kodi shapes with HarfBuzz on the face's own cmap and looks
# glyphs up with FT_Get_Char_Index (GUIFontTTF.cpp), so a cmap entry is all it
# takes. Pure struct code: the build needs nothing beyond Pillow and lxml.
ALIAS = {}
for cp in (0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2015, 0x2212):
    ALIAS[cp] = "-"                      # hyphens, dashes, minus
for cp in (0x2018, 0x2019, 0x201B, 0x2032, 0x00B4):
    ALIAS[cp] = "'"                      # single quotes, prime, acute
for cp in (0x201C, 0x201D, 0x201E, 0x201F, 0x2033):
    ALIAS[cp] = '"'                      # double quotes, double prime
ALIAS.update({0x201A: ",", 0x2039: "<", 0x203A: ">", 0x2016: "|", 0x2017: "_",
              0x2002: " ", 0x2003: " ", 0x2009: " ", 0x202F: " "})
DRAWN = {0x2026: "uni2026", 0x2022: "uni2022"}   # drawn below
DRAWN_ALIAS = {0x00B7: 0x2022}                    # middle dot -> bullet glyph

def _tables(data):
    n = struct.unpack(">H", data[4:6])[0]
    t = {}
    for i in range(n):
        tag, _, off, ln = struct.unpack(">4sIII", data[12 + 16 * i:28 + 16 * i])
        t[tag.decode("latin-1")] = bytearray(data[off:off + ln])
    return t

def _cmap4(cm):
    """code point -> glyph id, from the first format-4 subtable."""
    for i in range(struct.unpack(">H", cm[2:4])[0]):
        o = struct.unpack(">I", cm[8 + 8 * i:12 + 8 * i])[0]
        if struct.unpack(">H", cm[o:o + 2])[0] == 4:
            break
    s = cm[o:]
    n = struct.unpack(">H", s[6:8])[0] // 2
    ends = struct.unpack(f">{n}H", s[14:14 + 2 * n])
    starts = struct.unpack(f">{n}H", s[16 + 2 * n:16 + 4 * n])
    deltas = struct.unpack(f">{n}h", s[16 + 4 * n:16 + 6 * n])
    ro = 16 + 6 * n
    ranges = struct.unpack(f">{n}H", s[ro:ro + 2 * n])
    m = {}
    for i in range(n):
        for cp in range(starts[i], ends[i] + 1):
            if cp == 0xFFFF:
                continue
            if ranges[i] == 0:
                g = (cp + deltas[i]) & 0xFFFF
            else:
                a = ro + 2 * i + ranges[i] + 2 * (cp - starts[i])
                g = struct.unpack(">H", s[a:a + 2])[0]
                g = (g + deltas[i]) & 0xFFFF if g else 0
            if g:
                m[cp] = g
    return m

def _build_cmap(m):
    """One format-4 subtable (delta segments only) shared by (0,3) and (3,1)."""
    segs = []
    for cp in sorted(m):
        if segs and cp == segs[-1][1] + 1 and m[cp] == m[segs[-1][1]] + 1:
            segs[-1][1] = cp
        else:
            segs.append([cp, cp])
    segs.append([0xFFFF, 0xFFFF])
    n = len(segs)
    es = 1 << (n.bit_length() - 1)
    sub = struct.pack(">HHHHHHH", 4, 0, 0, 2 * n, 2 * es, es.bit_length() - 1, 2 * n - 2 * es)
    sub += struct.pack(f">{n}H", *[e for _, e in segs]) + b"\0\0"
    sub += struct.pack(f">{n}H", *[s for s, _ in segs])
    sub += struct.pack(f">{n}h", *[((m[s] - s + 0x8000) & 0xFFFF) - 0x8000 if s != 0xFFFF else 1
                                   for s, _ in segs])
    sub += struct.pack(f">{n}H", *[0] * n)
    sub = bytearray(sub)
    struct.pack_into(">H", sub, 2, len(sub))
    return bytearray(struct.pack(">HHHHIHHI", 0, 2, 0, 3, 20, 3, 1, 20)) + sub

def _glyph(t, gid):
    loca = t["loca"]
    a, b = struct.unpack(">II", loca[4 * gid:4 * gid + 8])
    return t["glyf"][a:b]

def _adv(t, gid):
    return struct.unpack(">H", t["hmtx"][4 * gid:4 * gid + 2])[0]

def _rects_glyph(rects):
    """A simple TrueType glyph made of axis-aligned rectangles (font units)."""
    xs, ys, ends = [], [], []
    for x0, y0, x1, y1 in rects:          # clockwise, y up: outer contours
        xs += [x0, x0, x1, x1]
        ys += [y0, y1, y1, y0]
        ends.append(len(xs) - 1)
    g = struct.pack(">hhhhh", len(rects), min(xs), min(ys), max(xs), max(ys))
    g += struct.pack(f">{len(ends)}H", *ends) + struct.pack(">H", 0)
    g += bytes([1] * len(xs))               # on-curve, long coordinates
    g += struct.pack(f">{len(xs)}h", *[b - a for a, b in zip([0] + xs, xs)])
    g += struct.pack(f">{len(ys)}h", *[b - a for a, b in zip([0] + ys, ys)])
    return g + b"\0" * (-len(g) % 4), min(xs)

def _draw(t, m, upem, cellh):
    """Rectangles for the drawn glyphs, sized from this face's own . and -"""
    px = upem // cellh                       # Tamzen: 100 units per pixel
    adv = _adv(t, m[ord(".")])               # monospaced: one cell
    W = adv // px
    def box(ch):
        g = _glyph(t, m[ord(ch)])
        x0, y0, x1, y1 = struct.unpack(">hhhh", g[2:10])
        return x0 // px, y0 // px, x1 // px, y1 // px
    pa, pb, pc, pd = box(".")
    pw, ph = pc - pa, pd - pb
    dw = pw
    while dw > 1 and 3 * dw + 2 > W:
        dw -= 1
    dh = ph if dw == pw else dw
    x = (W - (3 * dw + 2)) // 2
    ell = [((x + i * (dw + 1)) * px, pb * px, (x + i * (dw + 1) + dw) * px, (pb + dh) * px)
           for i in range(3)]
    ha, hb, hc, hd = box("-")
    b = pw + (pw - (hd - hb)) % 2           # same parity as the hyphen: centred
    bx, by = (W - b) // 2, hb - (b - (hd - hb)) // 2
    bul = [(bx * px, by * px, (bx + b) * px, (by + b) * px)]
    return {0x2026: ell, 0x2022: bul}

def patch_face(path):
    data = open(path, "rb").read()
    t = _tables(data)
    m = _cmap4(t["cmap"])
    new = dict(m)
    upem = struct.unpack(">H", t["head"][18:20])[0]
    cellh = int(os.path.basename(path)[6:-5].split("x")[1])
    drawn = _draw(t, m, upem, cellh)
    ng = struct.unpack(">H", t["maxp"][4:6])[0]
    nhm = struct.unpack(">H", t["hhea"][34:36])[0]
    assert nhm == ng and struct.unpack(">h", t["head"][50:52])[0] == 1, path
    for cp, name in DRAWN.items():
        if cp in new:
            continue
        g, lsb = _rects_glyph(drawn[cp])
        adv = _adv(t, m[ord(".")])
        end = struct.unpack(">I", t["loca"][4 * ng:4 * ng + 4])[0]
        t["glyf"] = t["glyf"][:end] + g
        t["loca"] = t["loca"][:4 * ng + 4] + struct.pack(">I", len(t["glyf"]))
        t["hmtx"] = t["hmtx"][:4 * ng] + struct.pack(">Hh", adv, lsb)
        p = t["post"]                        # format 2.0: add a glyph name
        assert struct.unpack(">I", p[0:4])[0] == 0x20000, path
        idx = list(struct.unpack(f">{ng}H", p[34:34 + 2 * ng]))
        names = p[34 + 2 * ng:]
        count, i = 0, 0
        while i < len(names):
            count, i = count + 1, i + 1 + names[i]
        idx.append(258 + count)
        t["post"] = (p[:32] + struct.pack(f">H{ng + 1}H", ng + 1, *idx) + names
                     + bytes([len(name)]) + name.encode())
        new[cp] = ng
        ng += 1
        struct.pack_into(">H", t["maxp"], 4, ng)
        struct.pack_into(">H", t["hhea"], 34, ng)
    for cp, ch in ALIAS.items():
        if cp not in new and ord(ch) in m:
            new[cp] = m[ord(ch)]
    for cp, src in DRAWN_ALIAS.items():
        if cp not in new:
            new[cp] = new[src]
    if new == m:
        return False
    t["cmap"] = _build_cmap(new)
    struct.pack_into(">HH", t["OS/2"], 64, min(new), min(max(new), 0xFFFF))
    struct.pack_into(">I", t["head"], 8, 0)
    # write the sfnt back: same tables, recomputed offsets and checksums
    def csum(b):
        b = bytes(b) + b"\0" * (-len(b) % 4)
        return sum(struct.unpack(f">{len(b) // 4}I", b)) & 0xFFFFFFFF
    tags = sorted(t)
    n = len(tags)
    es = 1 << (n.bit_length() - 1)
    out = bytearray(data[0:4] + struct.pack(">HHHH", n, 16 * es, es.bit_length() - 1, 16 * n - 16 * es))
    off = 12 + 16 * n
    body = bytearray()
    for tag in tags:
        out += struct.pack(">4sIII", tag.encode("latin-1"), csum(t[tag]), off + len(body), len(t[tag]))
        body += t[tag] + b"\0" * (-len(t[tag]) % 4)
    out += body
    hoff = off + sum(len(t[x]) + (-len(t[x]) % 4) for x in tags[:tags.index("head")])
    struct.pack_into(">I", out, hoff + 8, (0xB1B0AFBA - csum(out)) & 0xFFFFFFFF)
    open(path, "wb").write(out)
    return True

patched = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(FONTDIR, "Tamzen*.ttf")))
           if patch_face(p)]
if patched:
    print(f"fonts: punctuation added to {len(patched)} Tamzen face(s)")

def f(px, bold=False):
    cell = {12: "6x12", 14: "7x14", 16: "8x16", 20: "10x20",
            24: "6x12", 28: "7x14", 32: "8x16", 40: "10x20"}[px]
    return (f"Tamzen{cell}{'b' if bold else 'r'}.ttf", px)

# Tamzen size -> arial.ttf size with about the same line height. Kodi's line
# height is (hhea ascender - descender) / upem * size: 2384/2048 * size for
# arial.ttf, exactly `size` for Tamzen.
UNI = {12: 10, 14: 12, 16: 14, 20: 17, 24: 20, 28: 24, 32: 27, 40: 34}

# ...but FreeType rounds that line height to whole screen pixels at the size
# Kodi really loads (size x GUI scale, GUIFontManager::RescaleFontSizeAndAspect)
# and arial.ttf asks for integer ppem (head flags bit 3). arial 14 on the
# 2048x1536 panel (xml768, scale 2) is 2384/2048*28 = 32.6 -> 33 px = 16.5
# logical, and CGUITextBox fits floor(height / line height) lines, so a tile
# caption would lose a line. A <linespacing> just under 1 keeps every arial
# line at or below the Tamzen size it replaces, at every common scale:
# 1x (1024x600 / 1024x768), 1.2x (720p), 1.8x (1080p), 2x (iPad panel), 3.6x (4K).
ARIAL_UPEM, ARIAL_HEIGHT = 2048, 1901 + 483      # hhea ascender - descender
UNI_SCALES = (1, 1.2, 1.8, 2, 3.6)
def uni_linespacing(px):
    import math
    fit = min(px * s / math.floor(ARIAL_HEIGHT * round(UNI[px] * s) / ARIAL_UPEM + 0.5)
              for s in UNI_SCALES)
    return min(1.0, math.floor(fit * 100) / 100)

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
        ls = uni_linespacing(px)
        if ls < 1.0:
            extra = f"<linespacing>{ls:.2f}</linespacing>"
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
