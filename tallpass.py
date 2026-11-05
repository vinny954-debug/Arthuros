#!/usr/bin/env python3
"""Make the 4:3 layout (1024x768, folder xml768) from the 16:9 one (1024x600).

Kodi picks the skin folder whose aspect ratio is closest to the screen's
(CSkinInfo::Start, closestRes). A 4:3 screen such as an iPad 3 panel
(2048x1536) gets xml768, at exactly 2x, so the pixel art stays sharp; a
1024x600 panel keeps xml. Width is the same, so only the vertical layout
changes: the extra 168 px go to the parts that can use them.

Each window is written out with its includes expanded (their parameters
filled in), because an include's numbers only make sense in the place it is
used. Conditional includes are left as they are: their contents (row
heights, the desktop grids) are either size-independent or, for the
desktop, generated for 768 by home.py itself.

The rule, applied to every container that grows:
* at the screen level, anything at least 85% of the screen tall grows with
  it, anything starting in the lower half moves down with the task bar, and
  the rest stays;
* inside a growing container, the main body is the tallest scrolling
  control (list, panel, textbox, grouplist), or failing that the tallest
  control. Anything crossing the middle of that body grows, anything below
  it moves down, anything above stays.
Dialogs centred with <centertop>50%</centertop> need nothing.
"""
import copy, glob, os, re, shutil, sys
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.join(HERE, "skin.arthuros")
SRC = os.path.join(SKIN, "xml")
DST = os.path.join(SKIN, "xml768")
STAGE = os.path.join(HERE, "build768")      # Home.xml + Includes_Home.xml from home.py
H0, H1 = 600, 768
DY = H1 - H0

SCROLLERS = {"list", "panel", "fixedlist", "wraplist", "textbox", "grouplist", "epggrid"}
GROUPS = {"group"}

# ------------------------------------------------------------- includes
includes = {}
_staged = {os.path.basename(p): p for p in glob.glob(os.path.join(STAGE, "*.xml"))}
for p in glob.glob(os.path.join(SRC, "*.xml")):
    root = etree.parse(_staged.get(os.path.basename(p), p)).getroot()
    if root.tag == "includes":
        for inc in root.findall("include"):
            if inc.get("name"):
                includes[inc.get("name")] = inc

PARAM = re.compile(r"\$PARAM\[([A-Za-z0-9_]+)\]")

def sub(text, params):
    if not text or "$PARAM[" not in text:
        return text
    return PARAM.sub(lambda m: params.get(m.group(1), ""), text)

def subst_tree(el, params):
    """Copy of el with $PARAM[...] filled in, in text, tails and attributes."""
    new = copy.deepcopy(el)
    for e in new.iter():
        if not isinstance(e.tag, str):
            continue
        e.text = sub(e.text, params)
        e.tail = sub(e.tail, params)
        for k, v in list(e.attrib.items()):
            e.set(k, sub(v, params))
    return new

def expand(parent, params, depth=0):
    """Replace every unconditional <include> under parent, in place."""
    if depth > 20:
        raise RuntimeError("include nesting too deep")
    for ch in list(parent):
        if not isinstance(ch.tag, str):
            continue
        if ch.tag == "include" and not ch.get("condition") and not ch.get("file"):
            name = ch.get("content") or (ch.text or "").strip()
            inc = includes.get(name)
            if inc is None:
                raise KeyError(f"unknown include {name!r}")
            p = {d.get("name"): d.get("default", "") for d in inc.findall("param")}
            for u in ch.findall("param"):
                p[u.get("name")] = u.get("value", "")
            body = inc.find("definition")
            body = body if body is not None else inc
            idx = list(parent).index(ch)
            tail = ch.tail
            parent.remove(ch)
            # expand inside a holder first, so an include at the top of a
            # definition is replaced by its own pieces
            holder = etree.Element("x")
            for b in body:
                if not isinstance(b.tag, str) or b.tag == "param":
                    continue
                holder.append(subst_tree(b, p))
            expand(holder, p, depth + 1)
            pieces = list(holder)
            for k, piece in enumerate(pieces):
                parent.insert(idx + k, piece)
            if pieces:
                pieces[-1].tail = tail
            continue
        if ch.tag == "include":
            # conditional: keep it, but fill outer parameters into it
            continue
        expand(ch, params, depth)

# ------------------------------------------------------------- geometry
def geti(el, tag):
    t = el.findtext(tag)
    if t is None:
        return None
    t = t.strip()
    return int(t) if re.fullmatch(r"-?\d+", t) else "x"

def seti(el, tag, v):
    el.find(tag).text = str(v)

def cond_height(c):
    """Height set by conditional includes (Height_34 / Height_34_XL), the
    larger one; None when there is none."""
    hs = []
    for inc in c.findall("include"):
        if not inc.get("condition"):
            continue
        d = includes.get(inc.get("content") or (inc.text or "").strip())
        if d is None:
            continue
        body = d.find("definition")
        body = body if body is not None else d
        v = body.findtext("height")
        if v and re.fullmatch(r"\d+", v.strip()):
            hs.append(int(v))
    return max(hs) if hs else None

def kids(container):
    return [c for c in container if isinstance(c.tag, str) and c.tag == "control"]

def body_line(controls, H):
    def fits(c):
        t, h = geti(c, "top"), geti(c, "height")
        return isinstance(t, int) and isinstance(h, int) and 0.25 * H <= h < 0.95 * H
    cand = [c for c in controls if c.get("type") in SCROLLERS and fits(c)]
    if not cand:
        cand = [c for c in controls if fits(c)]
    if not cand:
        return H / 2
    c = max(cand, key=lambda c: geti(c, "height"))
    return geti(c, "top") + geti(c, "height") / 2

def grow(container, H, dy, screen=False):
    """container is H tall and is about to be dy taller."""
    controls = kids(container)
    S = body_line(controls, H)
    for c in controls:
        kind = c.get("type")
        t, h, b = geti(c, "top"), geti(c, "height"), geti(c, "bottom")
        ct = c.findtext("centertop")
        if ct is not None:
            ct = ct.strip()
            if re.fullmatch(r"-?\d+", ct) and int(ct) > (H / 2 if screen else S):
                c.find("centertop").text = str(int(ct) + dy)
            continue
        if t == "x" or h == "x" or b == "x":
            continue                      # an unresolved value: leave it alone
        if t is None and b is not None:
            continue                      # hangs from the bottom: moves by itself
        fixed = False
        if h is None and cond_height(c) is not None:
            h, fixed = cond_height(c), True     # can be moved, never grown
        if h is None:
            # no height: it fills down to the parent's bottom, so it grows by
            # itself; its own children still need the rule
            if kind in GROUPS:
                inner = H - (t or 0) - (b or 0)
                grow(c, inner, dy)
            continue
        top = t or 0
        if screen:
            if h >= 0.85 * H:
                action = "grow"
            elif top >= 0.5 * H:
                action = "move"
            else:
                action = "stay"
        else:
            if h >= 0.95 * H or top < S < top + h:
                action = "grow"
            elif top >= S:
                action = "move"
            else:
                action = "stay"
        if action == "grow" and fixed:
            action = "stay"
        if action == "grow":
            seti(c, "height", h + dy)
            if kind in GROUPS:
                grow(c, h, dy)
        elif action == "move":
            if t is None:
                etree.SubElement(c, "top").text = str(dy)
            else:
                seti(c, "top", t + dy)

# ------------------------------------------------------------- windows
def convert(src_path, dst_path):
    tree = etree.parse(src_path)
    root = tree.getroot()
    expand(root, {})
    coords = root.find("coordinates")
    controls = root.find("controls")
    if controls is not None:
        # windows placed with <coordinates> (the context menu) are positioned
        # by Kodi itself; leave their insides alone
        if coords is None:
            grow(controls, H0, DY, screen=True)
    for lab in root.iter("label"):         # the version line in Skin settings
        if lab.text and "1024x600" in lab.text:
            lab.text = lab.text.replace("1024x600", f"1024x{H1}")
    tree.write(dst_path, encoding="UTF-8", xml_declaration=True)

def main():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)
    staged = {os.path.basename(p): p for p in glob.glob(os.path.join(STAGE, "*.xml"))}
    n = 0
    for p in sorted(glob.glob(os.path.join(SRC, "*.xml"))):
        name = os.path.basename(p)
        src = staged.get(name, p)
        root = etree.parse(src).getroot()
        if root.tag == "window":
            convert(src, os.path.join(DST, name))
            n += 1
        else:
            shutil.copy(src, os.path.join(DST, name))
    print(f"tallpass: {n} windows laid out for 1024x768 in xml768")

if __name__ == "__main__":
    main()
