#!/usr/bin/env python3
"""Taller rows for the Extra large fontsets.

Extra large doubles the content text (mkfonts.py), which no longer fits the
24-34px rows the skin is drawn with. This pass gives every text row a second,
taller version that Kodi picks only while an Extra large fontset is active:

* list containers: an extra itemlayout/focusedlayout pair, placed first, with
  condition="<XL>" (Kodi uses the first layout whose condition passes);
* shared row includes (Arthur_ItemLayout ...): an _XL twin, scaled;
* settings templates, context-menu entries and grouplist rows: their fixed
  <height> becomes a pair of conditional includes;
* spin controls and settings sliders get bigger arrows / bar (SpinSize_XL,
  SliderSize_XL), and a scrollbar that pages a textbox gets 12 px wider,
  into the textbox (Size_Left / Size_Width pairs) - a textbox can only be
  scrolled through its scrollbar;
* Touch mode only: buttons under 30 px in a horizontal button strip (the
  media toolbar) get a 34 px hit rect (Size_Hit), their face unchanged.

Changing the font makes Kodi reload the skin, so include conditions are
re-evaluated then. Idempotent; run after genwindows.py on every build.
"""
import copy, glob, os, re
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
XML = os.environ.get("XMLDIR") or os.path.join(HERE, "skin.arthuros", "xml")
STAGED = bool(os.environ.get("XMLDIR"))   # build768: rows only, the includes live in xml
# taller rows: for the Extra large fontsets, and for Touch mode (Skin settings)
XLC = "[String.StartsWith(Skin.Font,ExtraLarge) | Skin.HasSetting(touchmode)]"
ROW_INCLUDES = {"Arthur_ItemLayout": 24, "Arthur_FocusedLayout": 24}
TEMPLATE_IDS = {"7", "8", "9", "10", "12", "13", "14", "15", "20", "1000"}

def grow(h):
    return h + 16

def num(el, tag):
    t = el.findtext(tag)
    return int(t) if t and re.fullmatch(r"-?\d+", t.strip()) else None

def setnum(el, tag, v):
    el.find(tag).text = str(v)

def adapt(parent, h, H):
    """Stretch full-height controls to the new row height and centre the rest."""
    for ch in parent:
        if not isinstance(ch.tag, str):
            continue
        if ch.tag == "include":
            name = ch.get("content") or (ch.text or "").strip()
            if name in ROW_INCLUDES:
                if ch.get("content"):
                    ch.set("content", name + "_XL")
                else:
                    ch.text = name + "_XL"
            continue
        if ch.tag != "control":
            continue
        ht, top = num(ch, "height"), num(ch, "top")
        if ht == h:
            setnum(ch, "height", H)
            if ch.get("type") == "group":
                adapt(ch, h, H)
        elif top is not None:
            setnum(ch, "top", top + (H - h) // 2)

changed = set()

TOUCH_SIZES = {"spincontrol": "SpinSize_XL", "spincontrolex": "SpinSize_XL", "sliderex": "SliderSize_XL"}
SB_GROW = 12        # scrollbar 18 -> 30 with taller rows
TOUCH = "Skin.HasSetting(touchmode)"
TOUCH_HIT = 34      # hit height for short strip buttons in Touch mode
HIT_TYPES = ("button", "radiobutton", "togglebutton")

def conditional_param(ctrl, tag, inc, normal, xl):
    """<tag>normal</tag> becomes the XLC pair <include content=inc> with the
    value as a parameter (no per-value includes, so build768 needs none)."""
    el = ctrl.find(tag)
    idx = list(ctrl).index(el)
    a = etree.Element("include", content=inc, condition=XLC)
    etree.SubElement(a, "param", name="v", value=str(xl))
    b = etree.Element("include", content=inc, condition=f"!{XLC}")
    etree.SubElement(b, "param", name="v", value=str(normal))
    b.tail = el.tail; a.tail = el.tail
    ctrl.remove(el)
    ctrl.insert(idx, b); ctrl.insert(idx, a)

def save(tree, p):
    """Write with the house style the other passes' regexes expect:
    double-quoted declaration and a space before every '/>'."""
    txt = etree.tostring(tree, encoding="UTF-8", xml_declaration=True).decode("utf-8")
    txt = txt.replace("<?xml version='1.0' encoding='UTF-8'?>", '<?xml version="1.0" encoding="UTF-8"?>', 1)
    txt = re.sub(r'(?<=[^\s])/>', ' />', txt)
    txt = re.sub(r'-->(<window>|<includes>)', r'-->\n\1', txt)
    open(p, "w").write(txt if txt.endswith("\n") else txt + "\n")

# ---------------------------------------------------- shared row includes
if not STAGED:
    p = os.path.join(XML, "Includes_Lists.xml")
    tree = etree.parse(p)
    root = tree.getroot()
    for old in root.xpath("include[substring(@name, string-length(@name)-2)='_XL']"):
        root.remove(old)
    for name, h in ROW_INCLUDES.items():
        src = root.xpath(f"include[@name='{name}']")[0]
        twin = copy.deepcopy(src)
        twin.set("name", name + "_XL")
        body = twin.find("definition")
        adapt(body if body is not None else twin, h, grow(h))
        src.addnext(twin)
    save(tree, p)
    changed.add("Includes_Lists.xml")

# ------------------------------------------------ height includes (generated)
heights = set()

def conditional_height(ctrl):
    hel = ctrl.find("height")
    h = int(hel.text)
    heights.add(h)
    idx = list(ctrl).index(hel)
    a = etree.Element("include", content=f"Height_{h}_XL", condition=XLC)
    b = etree.Element("include", content=f"Height_{h}", condition=f"!{XLC}")
    a.tail = hel.tail; b.tail = hel.tail
    ctrl.remove(hel)
    ctrl.insert(idx, b); ctrl.insert(idx, a)

for p in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    base = os.path.basename(p)
    if base.startswith("Includes_Size"):
        continue
    tree = etree.parse(p)
    root = tree.getroot()
    touched = False

    # containers with text rows
    for c in root.iter("control"):
        if c.get("type") not in ("list", "fixedlist", "wraplist"):
            continue
        if (c.findtext("orientation") or "vertical").strip() == "horizontal":
            continue
        layouts = [l for l in c if l.tag in ("itemlayout", "focusedlayout")]
        if any(XLC in (l.get("condition") or "") for l in layouts):
            continue
        rows = [l for l in layouts if re.fullmatch(r"\d+", l.get("height", "")) and int(l.get("height")) <= 60]
        if not rows:
            continue
        first = layouts[0]
        for l in rows:
            h = int(l.get("height"))
            x = copy.deepcopy(l)
            x.set("height", str(grow(h)))
            cond = l.get("condition")
            x.set("condition", f"{XLC} + [{cond}]" if cond else XLC)
            adapt(x, h, grow(h))
            first.addprevious(x)
        touched = True

    # settings templates, context menu entries, grouplist rows
    is_settings = any(g.get("id") in ("5", "996") for g in root.iter("control") if g.get("type") == "grouplist")
    for c in root.iter("control"):
        h = num(c, "height")
        if h is None or not (26 <= h <= 34):
            continue
        parent = c.getparent()
        in_vgl = (parent is not None and parent.tag == "control" and parent.get("type") == "grouplist"
                  and (parent.findtext("orientation") or "vertical").strip() == "vertical")
        tmpl = is_settings and c.get("id") in TEMPLATE_IDS and c.get("type") != "image"
        if (in_vgl and c.get("type") not in ("image", "group")) or tmpl:
            conditional_height(c)
            touched = True
    # spin arrows and settings sliders: Kodi only reacts to a tap ON the
    # arrows (CGUISpinControl::OnMouseEvent) or ON the bar
    # (CGUISliderControl::OnMouseEvent), so they grow with the row. The
    # control's own tags win over Defaults.xml (SetDefaults appends at the
    # end and Kodi reads the first), so normal mode keeps Defaults' sizes.
    for c in root.iter("control"):
        inc = TOUCH_SIZES.get(c.get("type"))
        if not inc or any(i.get("content") == inc for i in c.findall("include")):
            continue
        x = etree.Element("include", content=inc, condition=XLC)
        hel = c.find("height")
        if hel is None:
            hel = next((i for i in c.findall("include") if (i.get("content") or "").startswith("Height_")), None)
        if hel is not None:
            x.tail = hel.tail
            hel.addnext(x)
        else:
            x.tail = "\n"
            c.insert(0, x)
        touched = True

    # a textbox moves only through its scrollbar (CGUITextBox has no gesture
    # or wheel handling), so with taller rows that scrollbar gets 12 px wider,
    # into the textbox, which gets 12 px narrower and re-wraps
    bars = {c.get("id"): c for c in root.iter("control") if c.get("type") == "scrollbar" and c.get("id")}
    for t in root.iter("control"):
        if t.get("type") != "textbox":
            continue
        sb = bars.get((t.findtext("pagecontrol") or "").strip())
        if sb is None or sb.getparent() is not t.getparent():
            continue
        sl, sw, tl, tw = num(sb, "left"), num(sb, "width"), num(t, "left"), num(t, "width")
        if None in (sl, sw, tl, tw) or sw != 18 or tl + tw > sl:
            continue
        conditional_param(sb, "left", "Size_Left", sl, sl - SB_GROW)
        conditional_param(sb, "width", "Size_Width", sw, sw + SB_GROW)
        conditional_param(t, "width", "Size_Width", tw, tw - SB_GROW)
        touched = True

    # Touch mode: buttons in a horizontal button strip that are drawn lower
    # than a finger (the media toolbar 9490, 26 px) keep their face but get
    # a hit rect TOUCH_HIT px high, centred on it, reaching half the item gap
    # to each side, so neighbouring rects meet without overlapping. A
    # grouplist places its children at 0,0 (CGUIControlGroupList::AddControl)
    # and hit-tests them in their own coordinates, beyond its own bounds, so
    # the rect may stick out above and below the strip.
    for g in root.iter("control"):
        if g.get("type") != "grouplist" or (g.findtext("orientation") or "").strip() != "horizontal":
            continue
        half = (num(g, "itemgap") or 0) // 2
        for c in g:
            if c.tag != "control" or c.get("type") not in HIT_TYPES:
                continue
            h, w = num(c, "height"), num(c, "width")
            if h is None or w is None or h >= TOUCH_HIT - 4 or c.find("hitrect") is not None \
                    or any(i.get("content") == "Size_Hit" for i in c.findall("include")):
                continue
            x = etree.Element("include", content="Size_Hit", condition=TOUCH)
            for k, v in (("x", -half), ("y", -((TOUCH_HIT - h) // 2)), ("w", w + 2 * half), ("h", TOUCH_HIT)):
                etree.SubElement(x, "param", name=k, value=str(v))
            hel = c.find("height")
            x.tail = hel.tail
            hel.addnext(x)
            touched = True

    if touched:
        save(tree, p)
        changed.add(base)

# heights already converted on earlier runs still need their includes
for p in glob.glob(os.path.join(XML, "*.xml")):
    for h in re.findall(r'content="Height_(\d+)(?:_XL)?"', open(p).read()):
        heights.add(int(h))

if STAGED:
    print(f"sizepass: {len(changed)} staged files given Extra large rows; heights {sorted(heights)}")
    raise SystemExit(0)
inc = ['<?xml version="1.0" encoding="UTF-8"?>\n<!-- GENERATED by sizepass.py -->\n<includes>\n']
for h in sorted(heights):
    inc.append(f'  <include name="Height_{h}"><height>{h}</height></include>\n')
    inc.append(f'  <include name="Height_{h}_XL"><height>{grow(h)}</height></include>\n')
# Touch mode / Extra large: spin arrows at exactly 2x their 16 px art, a
# bigger settings slider (its knob is as tall as the bar), and the
# value-carrying includes the textbox/scrollbar pass uses
inc.append('  <include name="SpinSize_XL"><spinwidth>32</spinwidth><spinheight>32</spinheight></include>\n')
inc.append('  <include name="SliderSize_XL"><sliderwidth>240</sliderwidth><sliderheight>32</sliderheight></include>\n')
for tag in ("Left", "Width"):
    inc.append(f'  <include name="Size_{tag}"><param name="v" default="0" />'
               f'<definition><{tag.lower()}>$PARAM[v]</{tag.lower()}></definition></include>\n')
# Touch mode hit rect for short strip buttons (Kodi resolves $PARAM in
# attribute values: CGUIIncludes::ResolveParametersForNode)
inc.append('  <include name="Size_Hit">' + "".join(f'<param name="{k}" default="0" />' for k in "xywh")
           + '<definition><hitrect x="$PARAM[x]" y="$PARAM[y]" w="$PARAM[w]" h="$PARAM[h]" /></definition></include>\n')
inc.append("</includes>\n")
open(os.path.join(XML, "Includes_Size.xml"), "w").write("".join(inc))

# chain it
p = os.path.join(XML, "Includes.xml")
s = open(p).read()
if "Includes_Size.xml" not in s:
    s = s.replace("</includes>", '  <include file="Includes_Size.xml" />\n</includes>')
    open(p, "w").write(s)
print(f"sizepass: {len(changed)} files given Extra large rows; heights {sorted(heights)}")
