#!/usr/bin/env python3
"""Taller rows for the Extra large fontsets.

Extra large doubles the content text (mkfonts.py), which no longer fits the
24-34px rows the skin is drawn with. This pass gives every text row a second,
taller version that Kodi picks only while an Extra large fontset is active:

* list containers: an extra itemlayout/focusedlayout pair, placed first, with
  condition="<XL>" (Kodi uses the first layout whose condition passes);
* shared row includes (Arthur_ItemLayout ...): an _XL twin, scaled;
* settings templates, context-menu entries and grouplist rows: their fixed
  <height> becomes a pair of conditional includes.

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
inc.append("</includes>\n")
open(os.path.join(XML, "Includes_Size.xml"), "w").write("".join(inc))

# chain it
p = os.path.join(XML, "Includes.xml")
s = open(p).read()
if "Includes_Size.xml" not in s:
    s = s.replace("</includes>", '  <include file="Includes_Size.xml" />\n</includes>')
    open(p, "w").write(s)
print(f"sizepass: {len(changed)} files given Extra large rows; heights {sorted(heights)}")
