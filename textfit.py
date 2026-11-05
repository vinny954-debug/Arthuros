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
import collections
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
ADV_JSON = os.path.join(os.path.dirname(KODI_PO), "arial-advances.json")
_ADV = json.load(open(ADV_JSON)) if os.path.exists(ADV_JSON) else None
SKIPPED, MEASURED_BY_TABLE = [], []
for p in sorted(glob.glob(os.path.join(SKIN, "fonts", "*.xml"))):
    for fs in ET.parse(p).getroot().findall("fontset"):
        fonts = {f.findtext("name"): (f.findtext("filename"), int(f.findtext("size")),
                                      (f.findtext("style") or "")) for f in fs.findall("font")}
        files = {fn for fn, _, _ in fonts.values()}
        shipped = all(os.path.exists(os.path.join(SKIN, "fonts", fn)) for fn in files)
        if shipped:
            FONTSETS[fs.get("id")] = fonts
        elif files == {"arial.ttf"} and _ADV:
            FONTSETS[fs.get("id")] = fonts
            MEASURED_BY_TABLE.append(fs.get("id"))
        else:   # a face neither shipped nor tabulated: say so rather than guess
            SKIPPED.append(f"{fs.get('id')} ({', '.join(sorted(files))}: no font file or advance table)")
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
    # GUIControlFactory: a label that is a natural number is a string id
    # (<label>7</label> shows "File manager"), so measure what Kodi shows
    if t.strip().isdigit():
        return STR.get(int(t.strip()), "?" * 8)
    t = re.sub(r"\$LOCALIZE\[(\d+)\]", lambda m: STR.get(int(m.group(1)), "?" * 8), t)
    t = re.sub(r"\$NUMBER\[(\d+)\]", r"\1", t)
    return t.replace("&lt;", "<").replace("&gt;", ">")

issues = []
# Wrapmultiline labels in a list layout that are still to be turned into
# textboxes (B-7), per window: the exact <label> of each one (repeats count).
# These are reported, not failed, with what they cut off. Any other one - a
# new label, a different text, one more of the same - fails the build; one
# that was fixed is only reported, so trim the list.
KNOWN_LAYOUT_WRAP = {
    # Settings hub tile captions (hand-maintained Settings.xml), item + focused layout
    "Settings": ("$INFO[ListItem.Label]", "$INFO[ListItem.Label]"),
}
known_cut = []
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
                        # a label in a layout is a CGUIListLabel: one line,
                        # wrapmultiline or not
                        if lc.get("type") == "label":
                            need = measure(fsid, font, text)
                            if need > int(w) + 0.5:
                                hit = (fsid, wname, "item", text, int(need), int(w))
                                if (get(lc, "wrapmultiline", pp) or "") == "true" and \
                                        sub(lc.findtext("label") or "", pp).strip() in KNOWN_LAYOUT_WRAP.get(wname, ()):
                                    known_cut.append(hit)    # fails once the window is fixed
                                else:
                                    issues.append(hit)
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

# B-7: a label inside a container layout is created as a CGUIListLabel
# (GUIControlFactory: GUICONTROL_LABEL becomes GUICONTROL_LISTLABEL inside a
# container), which never wraps - <wrapmultiline> there is a promise Kodi
# doesn't keep and the second line stays empty. Use a textbox. Includes
# are expanded, so a label pulled into a layout by an include counts too.
LAYOUTS = ("itemlayout", "focusedlayout", "channellayout", "focusedchannellayout",
           "rulerlayout", "rulerunit")
layout_wrap = {}
def layout_labels(el, params, depth=0, inside=False):
    if depth > 14: return
    for ch, pp in kids(el, params):
        lay = inside or ch.tag in LAYOUTS
        if lay and ch.tag == "control" and ch.get("type") == "label" \
                and (get(ch, "wrapmultiline", pp) or "") == "true":
            yield ch, pp
        yield from layout_labels(ch, pp, depth + 1, lay)

for p in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    wname = os.path.basename(p)[:-4]
    try: root = ET.parse(p).getroot()
    except ET.ParseError: continue
    if root.tag != "window": continue
    for c, pp in layout_labels(root, None):
        layout_wrap.setdefault(wname, []).append(sub(c.findtext("label") or "", pp).strip())
known_seen, known_gone = [], []
for wname in sorted(set(layout_wrap) | set(KNOWN_LAYOUT_WRAP)):
    have = collections.Counter(layout_wrap.get(wname, []))
    want = collections.Counter(KNOWN_LAYOUT_WRAP.get(wname, ()))
    for lab in sorted((have - want).elements()):   # new: fails
        issues.append(("-", wname, "list-layout label with wrapmultiline (never wraps: use a textbox)",
                       lab, 0, 0))
    if have & want: known_seen.append(wname)
    for lab in sorted((want - have).elements()):   # fixed: just trim the list
        known_gone.append((wname, lab))

def footer():
    sets = [f for f in FONTSETS if f not in MEASURED_BY_TABLE]
    print(f"  fontsets measured: {', '.join(sets)}"
          + (f"; {', '.join(MEASURED_BY_TABLE)} from Kodi's arial.ttf advance table" if MEASURED_BY_TABLE else ""))
    for s_ in SKIPPED:
        print(f"  fontset NOT measured: {s_}")
    for w_ in known_seen:
        n_ = sum((collections.Counter(layout_wrap[w_]) & collections.Counter(KNOWN_LAYOUT_WRAP[w_])).values())
        print(f"  known: {w_} has {n_} wrapmultiline label(s) in a list layout "
              "(they never wrap; KNOWN_LAYOUT_WRAP)")
        cut = {}
        for fsid, wn, _, text, need, avail in known_cut:
            if wn == w_: cut.setdefault((text, avail), {})[fsid] = need
        for (text, avail), sets in sorted(cut.items()):
            print(f"    cut short on one line: '{text}' has {avail}px - needs "
                  + ", ".join(f"{k} {v}px" for k, v in sorted(sets.items())))
    for w_, lab_ in known_gone:
        print(f"  {w_}: wrapmultiline layout label '{lab_}' is gone - remove it from KNOWN_LAYOUT_WRAP")

if not issues:
    print(f"textfit: every fixed label fits in every fontset ({n_items} static list items too)")
    footer()
    sys.exit(0)
# group: one line per label, listing the fontsets it breaks in
groups = {}
for fsid, wname, ct, text, need, avail in issues:
    g = groups.setdefault((ct, text, avail), {"windows": set(), "sets": {}})
    g["windows"].add(wname)
    g["sets"][fsid] = need
print(f"textfit: {len(groups)} label(s) overflow or can't wrap")
for (ct, text, avail), g in sorted(groups.items(), key=lambda kv: kv[0][1]):
    where = sorted(g["windows"])
    where = where[0] if len(where) == 1 else f"{len(where)} windows"
    if "-" in g["sets"]:
        print(f"  ✗ {ct}: '{text}'  [{where}]")
        continue
    sets = ", ".join(f"{k} {v}px" for k, v in sorted(g["sets"].items()))
    print(f"  ✗ {ct} '{text}' has {avail}px - needs: {sets}  [{where}]")
footer()
sys.exit(1)
