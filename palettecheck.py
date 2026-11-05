#!/usr/bin/env python3
"""Measure every palette's text contrast (WCAG 2 ratios).

Surfaces are computed the way Kodi draws them: a neutral texture multiplied
by the palette's facetint. Accessibility palettes must meet their target on
every pair; the others are reported for information.
"""
import glob, os, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, "skin.arthuros", "colors")
TARGET = {"High-Contrast-Dark": 7.0, "High-Contrast-Light": 7.0,
          "Colorblind-Safe": 4.5, "Colorblind-Safe-Dark": 4.5}

def rgb(v):
    v = v.strip()[-6:]
    return tuple(int(v[i:i+2], 16) for i in (0, 2, 4))

def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = map(ch, c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def mul(c, t):
    return tuple(x * y // 255 for x, y in zip(c, t))

base = {e.get("name"): e.text for e in ET.parse(os.path.join(C, "defaults.xml")).getroot()}
failed = []
rows = []
for p in sorted(glob.glob(os.path.join(C, "*.xml"))):
    name = os.path.basename(p)[:-4]
    if name == "defaults":
        name = "(default)"
    pal = dict(base)
    if name != "(default)":
        pal.update({e.get("name"): e.text for e in ET.parse(p).getroot()})
    P = {k: rgb(v) for k, v in pal.items()}
    tint = P["facetint"]
    face, well, bar = mul((0xDD,) * 3, tint), mul((0xFF,) * 3, tint), mul((0xBB,) * 3, tint)
    pairs = {
        "text on panel": min(ratio(P["text"], face), ratio(P["text"], well)),
        "dim text on panel": min(ratio(P["textdim"], face), ratio(P["textdim"], well)),
        "marked on panel": min(ratio(P["marked"], face), ratio(P["marked"], well)),
        "selected text": ratio(P["textinv"], P["select"]),
        "title bar 1": ratio(P["titletext"], P["accent1"]),
        "title bar 2": ratio(P["titletext"], P["accent2"]),
        "menu/task bar": ratio(P["text"], bar),
        "pointed-at title box": ratio(P["titletext"], P["select"]),
    }
    disabled = ratio(P["textdisabled"], face)
    want = TARGET.get(name, 4.5)   # every palette meets WCAG AA
    worst = min(pairs, key=pairs.get)
    rows.append((name, pairs[worst], worst, disabled))
    if want:
        for k, v in pairs.items():
            if v < want:
                failed.append(f"{name}: {k} is {v:.1f}:1, needs {want}:1")
        if name in TARGET and disabled < 3.0:   # WCAG exempts disabled text; the
                                                 # accessibility palettes keep it legible anyway
            failed.append(f"{name}: disabled text is {disabled:.1f}:1, needs 3:1")

for name, v, worst, dis in rows:
    tag = f"  (target {TARGET.get(name, 4.5)}:1)"
    print(f"  {name:22s} lowest {v:4.1f}:1 ({worst}); disabled {dis:.1f}:1{tag}")
if failed:
    print("palettecheck: FAILED")
    for f in failed:
        print("  " + f)
    sys.exit(1)
print("palettecheck: every palette meets its contrast target (AA 4.5:1; high contrast 7:1)")
