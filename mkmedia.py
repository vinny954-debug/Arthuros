#!/usr/bin/env python3
"""Generate every PNG texture for skin.arthuros."""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skin.arthuros", "media")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- palette
K  = (0x00,0x00,0x00)      # black
W  = (0xFF,0xFF,0xFF)      # white
w1 = (0xEE,0xEE,0xEE)      # near white
w2 = (0xDD,0xDD,0xDD)      # face  (Arthur grey1)
g1 = (0xBB,0xBB,0xBB)      # chrome
g2 = (0x99,0x99,0x99)
g3 = (0x77,0x77,0x77)      # shadow
g4 = (0x55,0x55,0x55)
g5 = (0x33,0x33,0x33)
R  = (0xCC,0x1A,0x1F)      # arthur red
r2 = (0x88,0x10,0x14)
B  = (0x00,0x44,0xCC)      # arthur blue
b2 = (0x00,0x22,0x77)
b3 = (0x44,0x88,0xEE)
C  = (0x22,0xAA,0xDD)      # cyan
c2 = (0x11,0x66,0x99)
Y  = (0xEE,0xDD,0x00)      # yellow
y2 = (0xB0,0xA0,0x00)
G  = (0x22,0xBB,0x44)      # green
g6 = (0x11,0x77,0x2A)
O  = (0xEE,0x88,0x22)      # orange
o2 = (0xA0,0x55,0x10)
P  = (0x93,0x58,0xD9)      # purple
p2 = (0x5E,0x33,0x92)
M  = (0xDD,0x66,0xCC)      # pink
m2 = (0x99,0x3D,0x8C)
T  = None                  # transparent

def save(img, name):
    p = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p, "PNG", optimize=True)

def rgba(c, a=255):
    return (c[0], c[1], c[2], a) if c else (0,0,0,0)

# ---------------------------------------------------------------- bevels
def bevel(face, tl, br, outline=K, n=24, b=2, name=None):
    """9-slice bevel: ring0 = outline (1px), ring1 = tl/br highlight (1px),
    everything inside = flat face.

    n must stay comfortably larger than 2*b. Kodi samples 9-slice quads with
    bilinear filtering, so a centre only a couple of texels wide bleeds the
    highlight and shadow rows inwards and the "flat" face renders as a
    gradient. A 20-texel centre keeps the bleed under a pixel."""
    im = Image.new("RGBA", (n, n))
    px = im.load()
    for y in range(n):
        for x in range(n):
            ring = min(x, y, n-1-x, n-1-y)
            if outline is not None and ring == 0:
                c = outline
            elif ring < b:
                c = br if (x >= n-1-ring or y >= n-1-ring) else tl
            else:
                c = face
            px[x, y] = rgba(c)
    if name: save(im, name)
    return im

def flat(c, name, n=8, a=255):
    save(Image.new("RGBA", (n, n), rgba(c, a)), name)

# solid fills (use with colordiffuse for anything else)
flat(W,  "fill.png")
flat(K,  "fill_black.png")
for nm, c in [("red",R),("blue",B),("grey",g2),("dgrey",g4),("face",w2),
              ("chrome",g1),("white",W),("yellow",Y),("green",G),("purple",P),
              ("cyan",C),("orange",O),("pink",M)]:
    flat(c, "bar_%s.png" % nm)

# translucent black for dimming behind dialogs
flat(K, "dim.png", a=168)

# raised / sunken panels
bevel(w2, W,  g3, name="panel_raised.png")
bevel(g1, W,  g3, name="panel_chrome.png")
bevel(W,  g3, W,  name="panel_sunken.png")
bevel(w2, g3, W,  name="panel_sunken_grey.png")
bevel(g1, g3, W,  name="panel_sunken_chrome.png")
bevel(w2, W,  g3, name="button_up.png")
bevel(g1, g3, W,  name="button_down.png")
bevel(B,  b3, b2, name="button_focus.png")
bevel(R,  (0xEE,0x66,0x66), r2, name="button_focus_red.png")
bevel(w2, W,  g3, outline=None, n=16, b=1, name="bevel_thin.png")
# selection bar for lists: hard blue block, black outline
bevel(B,  B,  B,  name="list_focus.png")
bevel(w2, w2, w2, name="list_hover.png")
bevel(W,  W,  W,  outline=K, name="outline_white.png")
bevel(g1, g1, g1, outline=K, name="outline_chrome.png")

# progress bar
bevel(g1, g3, W, name="progress_back.png")
bevel(B,  b3, b2, name="progress_fill.png")

# scrollbar pieces
bevel(g1, g3, W,  name="sb_back.png")
bevel(w2, W,  g3, name="sb_nub.png")

def arrow(direction, n=16, face=K, bg=w2):
    im = Image.new("RGBA", (n, n))
    d = ImageDraw.Draw(im)
    for y in range(n):
        for x in range(n):
            ring = min(x, y, n-1-x, n-1-y)
            if ring == 0: im.putpixel((x,y), rgba(K))
            elif ring == 1: im.putpixel((x,y), rgba(W if (x<n-2 and y<n-2) else g3))
            else: im.putpixel((x,y), rgba(bg))
    # triangle, 7px wide
    cx, cy = n//2, n//2
    for i in range(4):
        half = i
        for j in range(-half, half+1):
            if direction == "up":    p = (cx+j, cy-2+i)
            elif direction == "down":p = (cx+j, cy+2-i)
            elif direction == "left":p = (cx-2+i, cy+j)
            else:                    p = (cx+2-i, cy+j)
            if 2 <= p[0] < n-2 and 2 <= p[1] < n-2:
                im.putpixel(p, rgba(face))
    return im

for dname in ("up","down","left","right"):
    save(arrow(dname), "sb_%s.png" % dname)

# ---------------------------------------------------------------- pixel art
KEY = {'.':T,'K':K,'W':W,'w':w2,'l':w1,'g':g2,'h':g1,'d':g3,'D':g4,'E':g5,
       'R':R,'r':r2,'B':B,'b':b3,'n':b2,'C':C,'c':c2,'Y':Y,'y':y2,
       'G':G,'e':g6,'O':O,'o':o2,'P':P,'p':p2,'M':M,'m':m2}

def grid(rows, scale=3, name=None, pad=0):
    h = len(rows); wd = max(len(r) for r in rows)
    im = Image.new("RGBA", (wd, h))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            im.putpixel((x, y), rgba(KEY[ch]))
    if scale != 1:
        im = im.resize((wd*scale, h*scale), Image.NEAREST)
    if pad:
        bg = Image.new("RGBA", (im.width+pad*2, im.height+pad*2))
        bg.paste(im, (pad, pad)); im = bg
    if name: save(im, name)
    return im

ICONS = {}

ICONS["folder"] = [
"................",
"..KKKKK.........",
".KYYYYYK........",
"KYYYYYYYKKKKKKK.",
"KYYYYYYYYYYYYYK.",
"KYYYYYYYYYYYYYK.",
"KYWWWWWWWWWWWYK.",
"KYYYYYYYYYYYYYK.",
"KYYYYYYYYYYYYYK.",
"KYYYYYYYYYYYYYK.",
"KYyyyyyyyyyyyYK.",
"KYyyyyyyyyyyyYK.",
"KyyyyyyyyyyyyyK.",
".KKKKKKKKKKKKK..",
"................",
"................",
]

def recolour(rows, a, b):
    tr = str.maketrans(a, b)
    return [r.translate(tr) for r in rows]

ICONS["folder_blue"]   = recolour(ICONS["folder"], "Yy", "Bn")
ICONS["folder_green"]  = recolour(ICONS["folder"], "Yy", "Ge")
ICONS["folder_purple"] = recolour(ICONS["folder"], "Yy", "Pp")
ICONS["folder_pink"]   = recolour(ICONS["folder"], "Yy", "Mm")
ICONS["folder_cyan"]   = recolour(ICONS["folder"], "Yy", "Cc")
ICONS["folder_orange"] = recolour(ICONS["folder"], "Yy", "Oo")
ICONS["folder_red"]    = recolour(ICONS["folder"], "Yy", "Rr")

# "My add-ons" needs to read differently from "Add-ons" at a glance, so the
# installed-add-ons box is amber rather than green.
ICONS["addons_user"] = None  # filled in after ICONS["addons"] is defined

# film strip / movies
ICONS["movies"] = [
"................",
".KKKKKKKKKKKKKK.",
".KEKKEKKEKKEKKK.",
".KWKKWKKWKKWKKK.",
".KEKKEKKEKKEKKK.",
".KKKKKKKKKKKKKK.",
".KbbbbbbbbbbbbK.",
".KbCCCCCCCCCCbK.",
".KbCCCCCCCCCCbK.",
".KbbbbbbbbbbbbK.",
".KKKKKKKKKKKKKK.",
".KEKKEKKEKKEKKK.",
".KWKKWKKWKKWKKK.",
".KEKKEKKEKKEKKK.",
".KKKKKKKKKKKKKK.",
"................",
]

# TV set
ICONS["tvshows"] = [
"................",
"......K...K.....",
".......K.K......",
"........K.......",
"..KKKKKKKKKKKK..",
"..KpppppppppdK..",
"..KpWWWWWWWpdK..",
"..KpWWWWWWWpdK..",
"..KpWWWWWWWpdK..",
"..KpWWWWWWWpdK..",
"..KpppppppppdK..",
"..KPPPPPPPPPdK..",
"..KKKKKKKKKKKK..",
"...K........K...",
"..KKK......KKK..",
"................",
]

# music note
ICONS["music"] = [
"................",
".........KKKKK..",
".........KYYYK..",
".........KYYYK..",
".......KKKYYYK..",
".......KYYYYYK..",
".......KYYYKKK..",
".......KYYYK....",
".......KYYYK....",
"..KKKK.KYYYK....",
".KYYYYKKYYYK....",
"KYYYYYYKYYYK....",
"KYYYYYYKKKK.....",
"KYYYYYK.........",
".KKKKK..........",
"................",
]

# picture / photo
ICONS["pictures"] = [
"................",
".KKKKKKKKKKKKKK.",
".KCCCCCCCCCCCCK.",
".KCCCWWCCCCCCCK.",
".KCCWWWWCCCCCCK.",
".KCCCWWCCCCCCCK.",
".KCCCCCCCCKCCCK.",
".KCCCCCCCKeKCCK.",
".KCCCCCCKeeeKCK.",
".KCCCCCKeeeeeKK.",
".KCCKCKeeeeeeeK.",
".KCKeKeeeeeeeeK.",
".KKeeKeeeeeeeeK.",
".KeeeeeeeeeeeeK.",
".KKKKKKKKKKKKKK.",
"................",
]

# add-ons: open box
ICONS["addons"] = [
"................",
"....KKKKKKKK....",
"...KGGGGGGGGK...",
"..KGGGGGGGGGGK..",
".KKKKKKKKKKKKKK.",
".KGGGGGKKGGGGGK.",
".KGGGGGKKGGGGGK.",
".KGGGGGKKGGGGGK.",
".KeeeeeKKeeeeeK.",
".KeeeeeKKeeeeeK.",
".KeeeeeKKeeeeeK.",
".KeeeeeKKeeeeeK.",
".KeeeeeKKeeeeeK.",
".KKKKKKKKKKKKKK.",
"................",
"................",
]

ICONS["addons_user"] = None  # placeholder replaced below

# settings gear
ICONS["settings"] = [
"................",
"......KKKK......",
"......KggK......",
"......KggK......",
"....KKKggKKK....",
"....KggggggK....",
".KKKggKKKKggKKK.",
".KggggKWWKggggK.",
".KggggKWWKggggK.",
".KKKggKKKKggKKK.",
"....KggggggK....",
"....KKKggKKK....",
"......KggK......",
"......KggK......",
"......KKKK......",
"................",
]

# weather sun + cloud
ICONS["weather"] = [
"................",
"..K.........K...",
"...KK.KKK..KK...",
".....KYYYK......",
"....KYYYYYK.....",
"KKKKKYYYYYKKKK..",
"....KYYYYYK.....",
"....KYYYYYK.....",
"...KK.KKK.KK....",
"..K....KKKKK.K..",
"....KKKWWWWWKK..",
"..KKWWWWWWWWWKK.",
".KWWWWWWWWWWWWWK",
".KWWWWWWWWWWWWWK",
".KhhhhhhhhhhhhhK",
"..KKKKKKKKKKKKK."
]

# files / generic document
ICONS["file"] = [
"................",
"...KKKKKKKKK....",
"...KWWWWWWKKK...",
"...KWWWWWWKWK...",
"...KWWWWWWKWK...",
"...KWWWWWWKKK...",
"...KWKKKKWWWK...",
"...KWWWWWWWWK...",
"...KWKKKKKKWK...",
"...KWWWWWWWWK...",
"...KWKKKKKWWK...",
"...KWWWWWWWWK...",
"...KWWWWWWWWK...",
"...KKKKKKKKKK...",
"................",
"................",
]

# playlist
ICONS["playlist"] = [
"................",
"..KK.KKKKKKKKK..",
"..KK.KwwwwwwwK..",
"..KK.KKKKKKKKK..",
"................",
"..KK.KKKKKKKKK..",
"..KK.KwwwwwwwK..",
"..KK.KKKKKKKKK..",
"................",
"..KK.KKKKK.KKKK.",
"..KK.KwwwK.KYYK.",
"..KK.KKKKK.KYYK.",
"...........KYYK.",
"........KKKKKK..",
"........KYYYYK..",
".........KKKK...",
]

# favourites star
ICONS["favourites"] = [
"................",
".......KK.......",
"......KYYK......",
"......KYYK......",
".....KYYYYK.....",
"KKKKKKYYYYKKKKKK",
"KYYYYYYYYYYYYYYK",
".KYYYYYYYYYYYYK.",
"..KYYYYYYYYYYK..",
"...KYYYYYYYYK...",
"..KYYYYKKYYYYK..",
".KYYYYK..KYYYYK.",
"KYYYYK....KYYYK.",
"KYYK........KYK.",
".KK..........KK.",
"................",
]

# hard disk
ICONS["harddisk"] = [
"................",
".KKKKKKKKKKKKKK.",
".KhhhhhhhhhhhhK.",
".KhWWWWWWWWWWhK.",
".KhWddddddddWhK.",
".KhWdKKKKKKdWhK.",
".KhWdKWWWWKdWhK.",
".KhWdKWWWWKdWhK.",
".KhWdKKKKKKdWhK.",
".KhWddddddddWhK.",
".KhWWWWWWWWWWhK.",
".KhhhhhhhhhhhhK.",
".KhhGhhhhhhhhhK.",
".KKKKKKKKKKKKKK.",
"................",
"................",
]

# network globe
ICONS["network"] = [
"................",
".....KKKKKK.....",
"...KKbbbbbbKK...",
"..KbbKbbbbKbbK..",
".KbbbKbbbbKbbbK.",
".KbbbKbbbbKbbbK.",
"KKKKKKKKKKKKKKKK",
"KBBBBKBBBBKBBBBK",
"KBBBBKBBBBKBBBBK",
"KKKKKKKKKKKKKKKK",
".KBBBKBBBBKBBBK.",
".KBBBKBBBBKBBBK.",
"..KBBKBBBBKBBK..",
"...KKBBBBBBKK...",
".....KKKKKK.....",
"................",
]

# program / exe
ICONS["program"] = [
"................",
".KKKKKKKKKKKKKK.",
".KRRRRRRRRRRRRK.",
".KRKKKKKKKKKKRK.",
".KRKWWWWWWWWKRK.",
".KRKWKKKKKKWKRK.",
".KRKWKWWWWKWKRK.",
".KRKWKWWWWKWKRK.",
".KRKWKKKKKKWKRK.",
".KRKWWWWWWWWKRK.",
".KRKKKKKKKKKKRK.",
".KRRRRRRRRRRRRK.",
".KKKKKKKKKKKKKK.",
"................",
"................",
"................",
]

# audio / speaker
ICONS["audio"] = [
"................",
"..........KK....",
".......KKKKK....",
"......KOOOKK.K..",
"....KKOOOOKK.K..",
"...KOOOOOOK.K.K.",
"...KOOOOOOK.K.K.",
"...KOOOOOOK.K.K.",
"...KOOOOOOK.K.K.",
"....KKOOOOKK.K..",
"......KOOOKK.K..",
".......KKKKK....",
"..........KK....",
"................",
"................",
"................",
]

# optical disc
ICONS["disc"] = [
"................",
".....KKKKKK.....",
"...KKhhhhhhKK...",
"..KhhWWWWWWhhK..",
".KhhWWWWWWWWhhK.",
".KhWWWKKKKWWWhK.",
"KhhWWK.WW.KWWhhK",
"KhWWK..WW..KWWhK",
"KhWWK..WW..KWWhK",
"KhhWWK.WW.KWWhhK",
".KhWWWKKKKWWWhK.",
".KhhWWWWWWWWhhK.",
"..KhhWWWWWWhhK..",
"...KKhhhhhhKK...",
".....KKKKKK.....",
"................",
]

# add a source: folder with a plus
ICONS["addsource"] = [
"................",
"..KKKKK.........",
".KGGGGGK........",
"KGGGGGGGKKKKKKK.",
"KGGGGGGGGGGGGGK.",
"KGGGGGGWWGGGGGK.",
"KGGGGGGWWGGGGGK.",
"KGGGWWWWWWWWGGK.",
"KGGGWWWWWWWWGGK.",
"KGGGGGGWWGGGGGK.",
"KGeeeeeWWeeeeeK.",
"KGeeeeeeeeeeeeK.",
"KeeeeeeeeeeeeeK.",
".KKKKKKKKKKKKK..",
"................",
"................",
]

# up / parent folder
ICONS["parent"] = [
"................",
"..KKKKK.........",
".KwwwwwK........",
"KwwwwwwwKKKKKKK.",
"KwwwKwwwwwwwwwK.",
"KwwKKKwwwwwwwwK.",
"KwKKKKKwwwwwwwK.",
"KwwwKwwwwwwwwwK.",
"KwwwKwwwwwwwwwK.",
"KwwwKwwwwwwwwwK.",
"KwwwKwwwwwwwwwK.",
"KhhhhhhhhhhhhhK.",
"KhhhhhhhhhhhhhK.",
".KKKKKKKKKKKKK..",
"................",
"................",
]

# My add-ons: the add-ons box in orange, with a heart on its front. The heart
# is what tells it apart for anyone who can't separate orange from green.
_u = [list(r) for r in recolour(ICONS["addons"], "Ge", "Oo")]
for dy, row in enumerate([".WW.WW.", "WWWWWWW", "WWWWWWW", ".WWWWW.", "..WWW..", "...W..."]):
    for dx, ch in enumerate(row):
        _u[6 + dy][4 + dx] = "W" if ch == "W" else ("o" if 6 + dy >= 8 else "O")
ICONS["addons_user"] = ["".join(r) for r in _u]
ICONS = {k: v for k, v in ICONS.items() if v is not None}

# ------------------------------------------- the icon registry (iconset.py)
# Every icon is generated from one registry so iconcheck.py can prove that no
# two different icons share a picture. Stale files from older builds are
# removed first, so nothing unregistered can linger in media/.
import glob, shutil
import iconset
for d in ("icons", "icons24", "icons64", "icons80", "icons96", "icons128"):
    shutil.rmtree(os.path.join(OUT, d), ignore_errors=True)
for f in glob.glob(os.path.join(OUT, "Default*.png")):
    os.remove(f)
REGISTRY = iconset.build(ICONS)
for nm, rows in REGISTRY.items():
    grid(rows, scale=3, name="icons/%s.png" % nm)      # 48x48
    grid(rows, scale=2, name="icons24/%s.png" % nm)    # 32x32
    grid(rows, scale=4, name="icons64/%s.png" % nm)    # 64x64
    # big desktop tiles: drawn at exactly the size they are shown, so Kodi
    # never has to scale (and blur) the pixel art
    grid(rows, scale=5, name="icons80/%s.png" % nm)    # 80x80
    grid(rows, scale=6, name="icons96/%s.png" % nm)    # 96x96

# Kodi's Default*.png fallbacks, each pointing at a registry icon
for dst, src in iconset.DEFAULT_MAP.items():
    grid(REGISTRY[src], scale=3, name="%s.png" % dst)

# --------------------------------------------------- window control boxes
def wcbox(glyph, face=True, ink=K):
    """A title-bar box. The face and the glyph are separate textures, so the
    skin can tint the face with the palette's face colour and the glyph with
    its text colour: a dark palette gets a dark box with a light glyph
    instead of a black glyph lost on a dark square."""
    rows = ["KKKKKKKKKKK","KWWWWWWWWWK","KWwwwwwwwWK","KWwwwwwwwWK",
            "KWwwwwwwwWK","KWwwwwwwwWK","KWwwwwwwwWK","KWwwwwwwwWK",
            "KWwwwwwwwWK","KWdddddddWK","KKKKKKKKKKK"]
    im = grid(rows, scale=2) if face else Image.new("RGBA", (22, 22))
    d = ImageDraw.Draw(im)
    if glyph == "min":
        d.rectangle([6,14,15,17], fill=rgba(ink))
    elif glyph == "max":
        d.rectangle([5,4,16,17], outline=rgba(ink), width=2)
        d.rectangle([5,4,16,7], fill=rgba(ink))
    elif glyph == "close":
        for i in range(9):
            for o in (0,1):
                d.point((5+i+o, 5+i), fill=rgba(ink))
                d.point((13-i+o, 5+i), fill=rgba(ink))
    return im
# the empty box, tinted by facetint
save(wcbox(None), "wc_face.png")
for gname in ("min","max","close"):
    # the glyph alone, in white, tinted by text / titletext / textdisabled
    save(wcbox(gname, face=False, ink=W), "wc_%s_g.png" % gname)
    # unavailable: the same glyph stippled, the classic greyed-out look. It
    # reads as "off" by its texture, so it can keep enough contrast to stay
    # visible on dark palettes instead of fading into the box.
    im = wcbox(gname, face=False, ink=W)
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if (x + y) % 2:
                px[x, y] = (0, 0, 0, 0)
    save(im, "wc_%s_dg.png" % gname)

# --------------------------------------------------- check / radio
def checkbox(on):
    n = 18
    im = Image.new("RGBA", (n,n))
    for y in range(n):
        for x in range(n):
            ring = min(x,y,n-1-x,n-1-y)
            if ring == 0:   c = K
            elif ring == 1: c = g3 if (x < n-2 and y < n-2) else W
            else:           c = W
            im.putpixel((x,y), rgba(c))
    if on:
        d = ImageDraw.Draw(im)
        for i in range(4):
            d.rectangle([4+i, 9+i, 5+i, 10+i], fill=rgba(g6))
        for i in range(7):
            d.rectangle([7+i, 12-i, 8+i, 13-i], fill=rgba(g6))
    return im
save(checkbox(True),  "check_on.png")
save(checkbox(False), "check_off.png")

def radio(on):
    n = 18
    im = Image.new("RGBA", (n,n))
    d = ImageDraw.Draw(im)
    d.ellipse([0,0,n-1,n-1], fill=rgba(W), outline=rgba(K), width=2)
    d.arc([2,2,n-3,n-3], 100, 280, fill=rgba(g3), width=2)
    if on: d.ellipse([5,5,n-6,n-6], fill=rgba(B))
    return im
save(radio(True),  "radio_on.png")
save(radio(False), "radio_off.png")

# --------------------------------------------------- mouse pointer
# A 1-bit era arrow: hard black outline, flat white fill, visible stair-steps.
# Drawn on a 14x22 grid and doubled, so every "pixel" is two screen pixels and
# the staircase reads as deliberate rather than as aliasing.
POINTER = [
"K.............",
"KK............",
"KWK...........",
"KWWK..........",
"KWWWK.........",
"KWWWWK........",
"KWWWWWK.......",
"KWWWWWWK......",
"KWWWWWWWK.....",
"KWWWWWWWWK....",
"KWWWWWWWWWK...",
"KWWWWWWWWWWK..",
"KWWWWWWWWWWWK.",
"KWWWWWWKKKKKKK",
"KWWWKWWK......",
"KWWKKWWK......",
"KWK..KWWK.....",
"KK...KWWK.....",
"K.....KWWK....",
"......KWWK....",
".......KWK....",
".......KK.....",
]

grid(POINTER, scale=2, name="pointer.png")
POINTER_CLICK = [r.replace("W","K") for r in POINTER]
grid(POINTER_CLICK, scale=2, name="pointer_click.png")

# Arthur: the 16-colour pointer. Cyan body, a white bevel highlight down the
# leading edge, and a red tail - the same bright palette as the title bars.
POINTER_ARTHUR = [
"K.............",
"KK............",
"KWK...........",
"KWCK..........",
"KWCCK.........",
"KWCCCK........",
"KWCCCCK.......",
"KWCCCCCK......",
"KWCCCCCCK.....",
"KWCCCCCCCK....",
"KWCCCCCCCCK...",
"KWCCCCCCCCCK..",
"KWCCCCCCCCCCK.",
"KWCCCCCKKKKKKK",
"KWCCKCCK......",
"KWCKKCRK......",
"KWK..KRRK.....",
"KK...KRRK.....",
"K.....KRRK....",
"......KRRK....",
".......KRK....",
".......KK.....",
]
grid(POINTER_ARTHUR, scale=2, name="pointer_arthur.png")
# pressed: the body drops to dark blue, like a button going down
grid([r.replace("C","n").replace("W","B") for r in POINTER_ARTHUR], scale=2,
     name="pointer_arthur_click.png")
# classic: plain 1-bit arrow; inverse: the same with the fills swapped
grid(POINTER, scale=2, name="pointer_classic.png")
grid(POINTER_CLICK, scale=2, name="pointer_classic_click.png")
INVERSE = [r.replace("W","x").replace("K","W").replace("x","K") for r in POINTER]
grid(INVERSE, scale=2, name="pointer_inverse.png")
grid([r.replace("K","g") for r in INVERSE], scale=2, name="pointer_inverse_click.png")

# --------------------------------------------------- logo "A" tile
def logo(size):
    rows = [
    "KKKKKKKKKKKKKKKK",
    "KWWWWWWWWWWWWWWK",
    "KWWWWWWRRWWWWWWK",
    "KWWWWWRRRRWWWWWK",
    "KWWWWWRRRRWWWWWK",
    "KWWWWRRWWRRWWWWK",
    "KWWWWRRWWRRWWWWK",
    "KWWWRRWWWWRRWWWK",
    "KWWWRRRRRRRRWWWK",
    "KWWRRRRRRRRRRWWK",
    "KWWRRWWWWWWRRWWK",
    "KWRRWWWWWWWWRRWK",
    "KWRRWWWWWWWWRRWK",
    "KRRWWWWWWWWWWRRK",
    "KWWWWWWWWWWWWWWK",
    "KKKKKKKKKKKKKKKK",
    ]
    return grid(rows, scale=size//16)
save(logo(32), "logo.png")
save(logo(256).resize((256,256), Image.NEAREST), "../icon.png")

# hollow focus ring: 2px black, 2px blue, transparent centre (border=4)
def ring(n=24, b=4, name=None, c1=K, c2=B):
    im = Image.new("RGBA", (n, n))
    for y in range(n):
        for x in range(n):
            r = min(x, y, n-1-x, n-1-y)
            if r < 2:   im.putpixel((x,y), rgba(c1))
            elif r < b: im.putpixel((x,y), rgba(c2))
    if name: save(im, name)
    return im
ring(name="focus_ring.png")
ring(name="focus_ring_red.png", c2=R)

# transport glyphs for the OSD
TRANSPORT = {
"play": [
"................","....KK..........","....KKKK........","....KKKKKK......",
"....KKKKKKKK....","....KKKKKKKKKK..","....KKKKKKKKKK..","....KKKKKKKK....",
"....KKKKKK......","....KKKK........","....KK..........","................",
"................","................","................","................"],
"pause": [
"................","...KKKK..KKKK...","...KKKK..KKKK...","...KKKK..KKKK...",
"...KKKK..KKKK...","...KKKK..KKKK...","...KKKK..KKKK...","...KKKK..KKKK...",
"...KKKK..KKKK...","...KKKK..KKKK...","...KKKK..KKKK...","................",
"................","................","................","................"],
"stop": [
"................","..KKKKKKKKKKKK..","..KKKKKKKKKKKK..","..KKKKKKKKKKKK..",
"..KKKKKKKKKKKK..","..KKKKKKKKKKKK..","..KKKKKKKKKKKK..","..KKKKKKKKKKKK..",
"..KKKKKKKKKKKK..","..KKKKKKKKKKKK..","..KKKKKKKKKKKK..","..KKKKKKKKKKKK..",
"................","................","................","................"],
"next": [
"................","..KK........KK..","..KKKK......KK..","..KKKKKK....KK..",
"..KKKKKKKK..KK..","..KKKKKKKKKKKK..","..KKKKKKKKKKKK..","..KKKKKKKK..KK..",
"..KKKKKK....KK..","..KKKK......KK..","..KK........KK..","................",
"................","................","................","................"],
"prev": [
"................","..KK........KK..","..KK......KKKK..","..KK....KKKKKK..",
"..KK..KKKKKKKK..","..KKKKKKKKKKKK..","..KKKKKKKKKKKK..","..KK..KKKKKKKK..",
"..KK....KKKKKK..","..KK......KKKK..","..KK........KK..","................",
"................","................","................","................"],
"ffwd": [
"................","..K.......K.....","..KKK.....KKK...","..KKKKK...KKKKK.",
"..KKKKKKK.KKKKKK","..KKKKKKK.KKKKKK","..KKKKK...KKKKK.","..KKK.....KKK...",
"..K.......K.....","................","................","................",
"................","................","................","................"],
"rew": [
"................",".....K.......K..","...KKK.....KKK..",".KKKKK...KKKKK..",
"KKKKKKK.KKKKKKK.","KKKKKKK.KKKKKKK.",".KKKKK...KKKKK..","...KKK.....KKK..",
".....K.......K..","................","................","................",
"................","................","................","................"],
"shuffle": [
"................","..........KKK...","...........KKK..","..KK.....KKKKKK.",
"..KKKK..KKK.KKK.","....KKKKKK..KKK.","......KKK.......","......KKK.......",
"....KKKKKK..KKK.","..KKKK..KKK.KKK.","..KK.....KKKKKK.","...........KKK..",
"..........KKK...","................","................","................"],
"repeat": [
"................","....KKKKKKKK....","...KKKKKKKKKK...","...KK......KKK..",
"...KK.......KK..","...KK.......KK..","................","................",
"..KK.......KK...","..KKK......KK...","..KKKKKKKKKKK...","...KKKKKKKKKK...",
"................","................","................","................"],
}
for nm, rows in TRANSPORT.items():
    grid(rows, scale=2, name="icons24/%s.png" % nm)
    grid(rows, scale=1, name="icons16/%s.png" % nm)


# ------------------------------------------- P3 screen calibration markers
# The movers of SettingsScreenCalibration.xml. Kept out of the icon registry
# (media/icons*) on purpose: home.py offers every registry icon as a desktop
# tile picture, and these are not pictures of anything. Drawn at 6x (96 px).
CAL = {}
CAL["cal_tl"] = [
"KKKKKKKKKK......",
"KWWWWWWWK.......",
"KWWWWWWK........",
"KWWWWWK.........",
"KWWWWWWK........",
"KWWWWWWWK.......",
"KWWWKWWWWK......",
"KWWK.KWWWWK.....",
"KWK...KWWWWK....",
"KK.....KWWWWK...",
"K.......KWWWWK..",
".........KWWWWK.",
"..........KWWK..",
"...........KK...",
"................",
"................",
]
# bottom-right: the same arrow turned round
CAL["cal_br"] = [r[::-1] for r in CAL["cal_tl"][::-1]]
# subtitle position: a bar across the middle, with the transparent space
# above and below that Kodi expects (CONTROL_SUBTITLES_SPACE, 80 of 90 px)
CAL["cal_sub"] = ["." * 16] * 7 + ["WWWWWWWWWWWWWWWW", "KKKKKKKKKKKKKKKK"] + ["." * 16] * 7
# pixel ratio: a ring that is round when the ratio is right
CAL["cal_ratio"] = [
"................",
".....KKKKKK.....",
"...KKWWWWWWKK...",
"..KWWKKKKKKWWK..",
".KWKK......KKWK.",
".KWK........KWK.",
"KWK..........KWK",
"KWK..........KWK",
"KWK..........KWK",
"KWK..........KWK",
".KWK........KWK.",
".KWKK......KKWK.",
"..KWWKKKKKKWWK..",
"...KKWWWWWWKK...",
".....KKKKKK.....",
"................",
]

CAL["cal_reset"] = iconset.badge(CAL["cal_ratio"], "refresh")
shutil.rmtree(os.path.join(OUT, "calibrate"), ignore_errors=True)
for nm, rows in CAL.items():
    grid(rows, scale=6, name="calibrate/%s.png" % nm)

# ---------------------------------------------------------------- themeable
# Neutral textures that colors/*.xml tint at render time via colordiffuse.
# White multiplies to exactly the palette colour; the grey shadow row keeps a
# visible bevel edge whatever colour it is tinted to.
bevel(W, W, (0x88,0x88,0x88), name="select_bevel.png")
ring(name="select_ring.png", c1=K, c2=W)

print("media written to", OUT)
