#!/usr/bin/env python3
"""Does every fixed label fit its box in EVERY fontset?

Kodi truncates overflowing text to "S..." without complaint. This measures
each static label (plain text or $LOCALIZE) with the real Tamzen TTF at the
real size, against the space its control actually leaves for text:
  label        -> width
  button       -> width - 2*textoffsetx   (Kodi pads both sides)
  radiobutton  -> the same, minus the radio and its gap
Labels driven by $INFO/$VAR are runtime text and cannot be checked here."""
import os, re, glob, sys
import xml.etree.ElementTree as ET
from PIL import ImageFont

SKIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skin.arthuros")
XML = os.path.join(SKIN, os.environ.get("RES", "xml"))
KODI_PO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "kodi", "strings.po")

STR = {}
for po in (os.path.join(SKIN, "language/resource.language.en_gb/strings.po"), KODI_PO):
    if os.path.exists(po):
        for m in re.finditer(r'msgctxt "#(\d+)"\nmsgid "(.*)"\nmsgstr', open(po, encoding="utf-8").read()):
            STR.setdefault(int(m.group(1)), m.group(2))

FONTSETS = {}
for fs in ET.parse(os.path.join(XML, "Font.xml")).getroot().findall("fontset"):
    FONTSETS[fs.get("id")] = {f.findtext("name"): (f.findtext("filename"), int(f.findtext("size")),
                                                  (f.findtext("style") or "")) for f in fs.findall("font")}
# Extra fontsets in fonts/*.xml (mkfonts.py: "Unicode" on Kodi's own arial.ttf,
# which the skin does not ship). Kodi's width is the sum of per-glyph advances,
# each rounded to whole pixels at the loaded size (GUIFontTTF CacheCharacter,
# GetTextWidthInternal); style bold widens each by size/24 (SetGlyphStrength).
# vendor/kodi/arial-advances.json holds arial.ttf's advance widths.
import json, math
for p in sorted(glob.glob(os.path.join(SKIN, "fonts", "*.xml"))):
    for fs in ET.parse(p).getroot().findall("fontset"):
        FONTSETS[fs.get("id")] = {f.findtext("name"): (f.findtext("filename"), int(f.findtext("size")),
                                                      (f.findtext("style") or "")) for f in fs.findall("font")}
_ADV = json.load(open(os.path.join(os.path.dirname(KODI_PO), "arial-advances.json")))
def measure_kodi(text, size, bold):
    adv, upem = _ADV["adv"], _ADV["upem"]
    worst = 0
    for s in (1, 1.2, 1.8, 2, 3.6):     # the GUI scales mkfonts.py plans for
        ppem = round(size * s)
        extra = (ppem * 64 // 24) / 64 if bold else 0
        w = sum(math.floor(math.floor(adv.get(str(ord(ch)), _ADV["max"]) * ppem / upem + 0.5)
                           + extra + 0.5) for ch in text)
        worst = max(worst, w / s)
    return worst
_cache = {}
def measure(fontset, name, text):
    fn, size, style = FONTSETS[fontset].get(name) or FONTSETS[fontset]["font13"]
    if "uppercase" in style: text = text.upper()
    if not os.path.exists(os.path.join(SKIN, "fonts", fn)):
        return measure_kodi(text, size, "bold" in style)
    key = (fn, size)
    if key not in _cache: _cache[key] = ImageFont.truetype(os.path.join(SKIN, "fonts", fn), size)
    return _cache[key].getlength(text)

INC, DEF = {}, {}
for p in glob.glob(os.path.join(XML, "*.xml")):
    try: r = ET.parse(p).getroot()
    except ET.ParseError: continue
    if r.tag != "includes": continue
    for i in r.findall("include"):
        if i.get("name"): INC[i.get("name")] = i
    for d in r.findall("default"):
        DEF[d.get("type")] = d

def sub(t, params):
    if t and params:
        for k, v in params.items(): t = t.replace(f"$PARAM[{k}]", v)
    return t

def walk(el, params=None, depth=0):
    if depth > 14: return
    for ch in list(el):
        if ch.tag == "include":
            name = ch.get("content") or (ch.text.strip() if ch.text else None)
            inc = INC.get(name)
            if inc is None: continue
            p = {pd.get("name"): pd.get("default", "") for pd in inc.findall("param")}
            for pu in ch.findall("param"):
                p[pu.get("name")] = sub(pu.get("value", ""), params)
            body = inc.find("definition")
            yield from walk(body if body is not None else inc, p, depth + 1)
            continue
        if ch.tag in ("itemlayout", "focusedlayout", "content"):
            continue            # row templates carry runtime text
        yield ch, params
        yield from walk(ch, params, depth + 1)

def get(c, tag, params, fallback=None):
    v = c.findtext(tag)
    if v is None and c.get("type") in DEF:
        v = DEF[c.get("type")].findtext(tag)
    v = sub(v, params)
    return v.strip() if v else fallback

def resolve_text(t):
    t = re.sub(r"\$LOCALIZE\[(\d+)\]", lambda m: STR.get(int(m.group(1)), "?" * 8), t)
    return t.replace("&lt;", "<").replace("&gt;", ">")

issues = []
for p in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    wname = os.path.basename(p)[:-4]
    try: root = ET.parse(p).getroot()
    except ET.ParseError: continue
    if root.tag != "window": continue
    for c, params in walk(root):
        if c.tag != "control": continue
        ct = c.get("type")
        if ct not in ("label", "button", "togglebutton", "radiobutton"): continue
        raw = sub(c.findtext("label") or "", params)
        if not raw.strip() or "$INFO" in raw or "$VAR" in raw or "$PARAM" in raw: continue
        if (get(c, "wrapmultiline", params) or "") == "true": continue
        if (get(c, "scroll", params) or "") == "true": continue
        w = get(c, "width", params)
        if not w or not re.fullmatch(r"-?\d+", w): continue
        avail = int(w)
        if ct != "label":
            off = int(get(c, "textoffsetx", params, "0") or 0)
            avail -= 2 * off
            if ct == "radiobutton" and not get(c, "radioposx", params):
                # Kodi: radio sits at (right edge - 8 - radiowidth)
                avail -= int(get(c, "radiowidth", params, "18") or 18) + 8
        text = resolve_text(raw)
        font = get(c, "font", params, "font13")
        for fsid in FONTSETS:
            need = measure(fsid, font, text)
            if need > avail + 0.5:
                issues.append((fsid, wname, ct, text, int(need), avail))

if not issues:
    print("textfit: every fixed label fits in every fontset")
    sys.exit(0)
# group: one line per label, listing the fontsets it breaks in
groups = {}
for fsid, wname, ct, text, need, avail in issues:
    g = groups.setdefault((ct, text, avail), {"windows": set(), "sets": {}})
    g["windows"].add(wname)
    g["sets"][fsid] = need
print(f"textfit: {len(groups)} label(s) overflow")
for (ct, text, avail), g in sorted(groups.items(), key=lambda kv: kv[0][1]):
    sets = ", ".join(f"{k} {v}px" for k, v in sorted(g["sets"].items()))
    where = sorted(g["windows"])
    where = where[0] if len(where) == 1 else f"{len(where)} windows"
    print(f"  ✗ {ct} '{text}' has {avail}px - needs: {sets}  [{where}]")
sys.exit(1)
