#!/usr/bin/env python3
"""Prove that every icon ArthurOS shows is unique.

1. Registry: no two icon names in iconset.py draw the same pixels.
2. Kodi fallbacks: two Default*.png names share an icon only when they are
   declared synonyms in iconset.ALIASES.
3. Files: every icon PNG on disk is hashed; identical files must come from
   the same registry name (catches stale or hand-copied art).
4. Menus: within one tile panel or one submenu, no two entries use the same
   icon.
Exits non-zero on any failure, so build.sh stops.
"""
import collections, glob, hashlib, os, re, sys
import xml.etree.ElementTree as ET
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.join(HERE, "skin.arthuros")
MEDIA = os.path.join(SKIN, "media")
sys.path.insert(0, HERE)
import iconset

errors = []

# ---------------------------------------------------------------- registry
# rebuild the registry from the same inputs mkmedia uses
import importlib.util, types
src = open(os.path.join(HERE, "mkmedia.py")).read()
icons_src = src[src.index("ICONS = {}"):src.index("ICONS = {k: v for k, v in ICONS.items()")]
ns = {}
exec("def recolour(rows, a, b):\n    tr = str.maketrans(a, b)\n    return [r.translate(tr) for r in rows]\n" + icons_src, ns)
icons = {k: v for k, v in ns["ICONS"].items() if v is not None}
reg = iconset.build(icons)

by_pixels = collections.defaultdict(list)
for name, rows in reg.items():
    by_pixels["\n".join(rows)].append(name)
for names in by_pixels.values():
    if len(names) > 1:
        errors.append("icons draw identical pixels: " + ", ".join(sorted(names)))

# ------------------------------------------------------------ Kodi fallbacks
alias_sets = set(iconset.ALIASES)
groups = collections.defaultdict(set)
for kodi, name in iconset.DEFAULT_MAP.items():
    if name not in reg:
        errors.append(f"{kodi} points at unknown icon '{name}'")
    groups[name].add(kodi)
for name, kodis in groups.items():
    if len(kodis) > 1 and frozenset(kodis) not in alias_sets:
        errors.append(f"{', '.join(sorted(kodis))} share icon '{name}' "
                      "but are not declared synonyms in iconset.ALIASES")
for a in alias_sets:
    used = {iconset.DEFAULT_MAP.get(k) for k in a}
    if len(used) != 1:
        errors.append(f"ALIASES entry {sorted(a)} no longer shares one icon")

# ------------------------------------------------------------------ files
def digest(p):
    im = Image.open(p).convert("RGBA")
    # compare at 16x16 so the 32, 48 and 64 px copies of one icon match
    return hashlib.sha1(im.resize((16, 16), Image.NEAREST).tobytes()).hexdigest()

owner = {}
for size in ("icons", "icons24", "icons64", "icons80", "icons96"):
    for p in glob.glob(os.path.join(MEDIA, size, "*.png")):
        owner[p] = os.path.splitext(os.path.basename(p))[0]
for p in glob.glob(os.path.join(MEDIA, "Default*.png")):
    k = os.path.splitext(os.path.basename(p))[0]
    owner[p] = iconset.DEFAULT_MAP.get(k, "?" + k)

glyphs = {os.path.splitext(os.path.basename(p))[0]
          for p in glob.glob(os.path.join(MEDIA, "icons16", "*.png"))}
files = collections.defaultdict(set)
for p, name in owner.items():
    if name in glyphs and "icons24" in p:
        continue                      # transport glyphs are checked below
    if name not in reg:
        errors.append(f"unregistered icon file {os.path.relpath(p, SKIN)}")
        continue
    files[digest(p)].add(name)
for names in files.values():
    if len(names) > 1:
        errors.append("icon files are identical: " + ", ".join(sorted(names)))

g = collections.defaultdict(list)
for p in glob.glob(os.path.join(MEDIA, "icons16", "*.png")):
    g[digest(p)].append(os.path.basename(p))
for names in g.values():
    if len(names) > 1:
        errors.append("transport glyphs are identical: " + ", ".join(sorted(names)))

# ------------------------------------------------------------------ menus
ICON_RE = re.compile(r"icons(?:24|64|80|96)?/([a-z0-9_]+)\.png")
checked = 0
for path in glob.glob(os.path.join(SKIN, "xml", "*.xml")):
    root = ET.parse(path).getroot()
    for content in root.iter("content"):
        panels = collections.defaultdict(list)
        for item in content.findall("item"):
            vis = (item.findtext("visible") or "").strip()
            # group submenu entries by their parent tile; other conditions
            # (an add-on being installed, say) do not start a new menu
            pm = re.search(r"ListItem\.Property\(id\),(\w+)\)", vis)
            vis = pm.group(0) if pm else ""
            icon = item.findtext("icon") or item.findtext("thumb") or ""
            m = ICON_RE.search(icon)
            if m:
                panels[vis].append((m.group(1), item.findtext("label") or "?"))
        for vis, entries in panels.items():
            checked += 1
            seen = {}
            for icon, label in entries:
                if icon in seen:
                    where = re.sub(r".*,(\w+)\).*", r"\1", vis) or "tiles"
                    errors.append(f"{os.path.basename(path)} [{where}]: '{label}' and "
                                  f"'{seen[icon]}' both use icon {icon}")
                else:
                    seen[icon] = label

if errors:
    print("iconcheck: FAILED")
    for e in errors:
        print("  " + e)
    sys.exit(1)
print(f"iconcheck: {len(reg)} icons, all unique; {len(iconset.DEFAULT_MAP)} Kodi "
      f"fallbacks ({len(iconset.ALIASES)} declared synonym pairs); "
      f"{checked} menus with no repeated icon")
