#!/usr/bin/env python3
"""Make every chrome texture follow the palette.

Idempotent: run it after genwindows.py on every build. Baked-colour textures
are swapped for neutral ones plus a colordiffuse naming a palette colour, and
every bevel gets colordiffuse="facetint" so palettes can tint the chrome.
Formatting and comments are preserved - this edits text, not a parsed tree."""
import glob, re, sys

import os
XML = os.environ.get("XMLDIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "skin.arthuros", "xml")   # XMLDIR=build768 for the 4:3 desktop

SWAP = {  # baked colour -> (neutral texture, palette colour)
    "bar_red.png":            ("fill.png",         "accent1"),
    "bar_blue.png":           ("fill.png",         "select"),
    "bar_grey.png":           ("fill.png",         "desktop"),
    "list_focus.png":         ("fill.png",         "select"),
    "button_focus.png":       ("select_bevel.png", "select"),
    "button_focus_red.png":   ("select_bevel.png", "accent1"),
    "progress_fill.png":      ("select_bevel.png", "select"),
    "focus_ring.png":         ("select_ring.png",  "select"),
    "focus_ring_red.png":     ("select_ring.png",  "accent1"),
}
TINT = {  # neutral chrome -> tinted by facetint
    "panel_raised.png","panel_sunken.png","panel_sunken_grey.png","panel_chrome.png",
    "panel_sunken_chrome.png","button_up.png","button_down.png","sb_back.png","sb_nub.png",
    "progress_back.png","bevel_thin.png","outline_white.png","outline_chrome.png",
    "sb_up.png","sb_down.png","sb_left.png","sb_right.png",
    "wc_face.png",
}
TAG = re.compile(r'<((?:alt)?texture\w*|midtexture)((?:\s+[a-z]+="[^"]*")*)\s*>([^<]+)</\1>')

def fix(m):
    tag, attrs, val = m.group(1), m.group(2) or "", m.group(3).strip()
    if 'colordiffuse=' in attrs:
        return m.group(0)
    if val in SWAP:
        new, colour = SWAP[val]
        return f'<{tag}{attrs} colordiffuse="{colour}">{new}</{tag}>'
    if val in TINT:
        return f'<{tag}{attrs} colordiffuse="facetint">{val}</{tag}>'
    return m.group(0)

changed = 0
for p in sorted(glob.glob(XML + "/*.xml")):
    s = open(p).read()
    n = TAG.sub(fix, s)
    if n != s:
        open(p, "w").write(n); changed += 1

# every window's title bar shows its own icon (iconset.WINDOW_ICONS)
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iconset
ICON_PARAM = re.compile(r'(<param name="icon" value=")([^"]*)(" />)')
for p in sorted(glob.glob(XML + "/*.xml")):
    w = os.path.basename(p)[:-4]
    want = iconset.WINDOW_ICON_EXPR.get(w) or (
        f"icons24/{iconset.WINDOW_ICONS[w]}.png" if w in iconset.WINDOW_ICONS else None)
    if not want:
        continue
    s = open(p).read()
    n = ICON_PARAM.sub(lambda m: m.group(1) + want + m.group(3), s, count=1)
    if n != s:
        open(p, "w").write(n); changed += 1

# anything still pointing at a baked-colour bar is a miss worth knowing about
left = []
for p in sorted(glob.glob(XML + "/*.xml")):
    for m in re.finditer(r">(bar_(?!dgrey)[a-z]+\.png)<", open(p).read()):
        left.append(f"{p.split('/')[-1]}: {m.group(1)}")
print(f"themepass: {changed} files updated")
if left:
    print("  still baked:", ", ".join(sorted(set(left))[:12]))
