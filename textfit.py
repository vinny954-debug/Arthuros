#!/usr/bin/env python3
"""Does every fixed label fit its box in EVERY fontset?

Kodi truncates overflowing text to "S..." without complaint. This measures
each static label (plain text or $LOCALIZE) with the real Tamzen TTF at the
real size, against the space its control actually leaves for text:
  label        -> width
  button       -> width - 2*textoffsetx   (Kodi pads both sides)
  radiobutton  -> the same, minus the radio and its gap
  static list item <label> -> the layout control showing ListItem.Label
                  (a textbox: every word fits, and the wrapped lines fit
                  its height)
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
_cache = {}
def measure(fontset, name, text):
    fn, size, style = FONTSETS[fontset].get(name) or FONTSETS[fontset]["font13"]
    if "uppercase" in style: text = text.upper()
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

# Static list items (<content><item><label>): the desktop catalogue, the
# Settings hub, the power menu. Their text lands in the layout control that
# shows ListItem.Label, so measure it there. A layout with an XL/touch
# condition is used with any fontset (touch mode), the plain one only with the
# fontsets that condition does not catch.
def kids(el, params, depth=0):
    """Direct children, with includes expanded in place."""
    for ch in list(el):
        if ch.tag == "include" and depth < 14:
            name = ch.get("content") or (ch.text.strip() if ch.text else None)
            inc = INC.get(name)
            if inc is None: continue
            p = {pd.get("name"): pd.get("default", "") for pd in inc.findall("param")}
            for pu in ch.findall("param"):
                p[pu.get("name")] = sub(pu.get("value", ""), params)
            body = inc.find("definition")
            yield from kids(body if body is not None else inc, p, depth + 1)
        else:
            yield ch, params

def label_controls(layout, params):
    for c in layout.iter("control"):
        if c.get("type") not in ("label", "textbox"): continue
        src = (sub(c.findtext("label") or "", params) or "") + (c.findtext("info") or "")
        if re.search(r"ListItem\.Label(?!2)\b", src) and not re.search(r"\$VAR|ListItem\.Label2", src):
            yield c

def fontsets_for(cond, siblings):
    if cond:
        if "touchmode" in cond or "ExtraLarge" not in cond:
            return list(FONTSETS)
        return [f for f in FONTSETS if f.startswith("ExtraLarge")]
    if any(s and "ExtraLarge" in s for s in siblings):
        return [f for f in FONTSETS if not f.startswith("ExtraLarge")]
    return list(FONTSETS)

n_items = 0
for p in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    wname = os.path.basename(p)[:-4]
    try: root = ET.parse(p).getroot()
    except ET.ParseError: continue
    if root.tag != "window": continue
    for c, params in walk(root):
        if c.tag != "control" or c.get("type") not in ("list", "panel", "fixedlist", "wraplist"):
            continue
        ch = list(kids(c, params))
        layouts = [(l, pp) for l, pp in ch if l.tag in ("itemlayout", "focusedlayout")]
        items = [it for cont, _ in ch if cont.tag == "content" for it in cont.findall("item")]
        conds = [l.get("condition") for l, _ in layouts]
        for it in items:
            raw = (it.findtext("label") or "").strip()
            if not raw or "$INFO" in raw or "$VAR" in raw or "$PARAM" in raw or "$ESCINFO" in raw:
                continue
            text = resolve_text(raw)
            n_items += 1
            for l, pp in layouts:
                for lc in label_controls(l, pp):
                    if (get(lc, "scroll", pp) or "") == "true": continue
                    w = get(lc, "width", pp)
                    if not w or not re.fullmatch(r"\d+", w): continue
                    font = get(lc, "font", pp, "font13")
                    for fsid in fontsets_for(l.get("condition"), conds):
                        if lc.get("type") == "label" and (get(lc, "wrapmultiline", pp) or "") != "true":
                            need = measure(fsid, font, text)
                            if need > int(w) + 0.5:
                                issues.append((fsid, wname, "item", text, int(need), int(w)))
                        else:   # textbox: each word must fit, and the wrapped lines the height
                            words = text.split()
                            wide = [x for x in words if measure(fsid, font, x) > int(w) + 0.5]
                            lines, cur = 1, ""
                            for x in words:
                                t = (cur + " " + x).strip()
                                if cur and measure(fsid, font, t) > int(w) + 0.5:
                                    lines, cur = lines + 1, x
                                else:
                                    cur = t
                            h = get(lc, "height", pp)
                            lh = FONTSETS[fsid].get(font, FONTSETS[fsid]["font13"])[1]
                            if wide:
                                issues.append((fsid, wname, "item word", text,
                                               int(max(measure(fsid, font, x) for x in wide)), int(w)))
                            elif h and h.isdigit() and lines * lh > int(h):
                                issues.append((fsid, wname, "item height", text, lines * lh, int(h)))

if not issues:
    print(f"textfit: every fixed label fits in every fontset ({n_items} static list items too)")
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
