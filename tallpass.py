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
  control. Only things that can use more height grow: containers, images,
  scrollbars and wrapping labels that cross the middle of the body or fill
  down to its bottom. A one-line label, a button or a slider never grows -
  a 198 px label centres its line 100 px away from its neighbours (L-1).
  Anything starting below the body moves down; anything else stays, so a
  stack of lines beside or inside the body stays together. A window with
  columns (a category list beside a text panel) has a body per column: a
  control is measured against the body it overlaps horizontally.
Dialogs centred with <centertop>50%</centertop> and dialogs hung from the
bottom edge (<bottom>0</bottom>: the OSDs, seek bar, bookmarks) need
nothing: Kodi places them against the 768 screen by itself.

Special cases, each checked by `tallpass.py --check NAME` from audit.sh:
* TALL_GENERATORS: dialogs whose generator draws them for 768 itself (the
  on-screen keyboard: bigger keys, not just a bigger box);
* context_menu(): the context menu's list and background grow, 999 stays
  at 0,0 (Kodi positions that window itself);
* TALLER_CELLS: panels whose cells grow so the rows fill the panel (the
  Settings hub).
"""
import copy, glob, os, re, shutil, subprocess, sys, tempfile
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = os.path.join(HERE, "skin.arthuros")
SRC = os.path.join(SKIN, "xml")
DST = os.path.join(SKIN, "xml768")
STAGE = os.path.join(HERE, "build768")      # Home.xml + Includes_Home.xml from home.py
H0, H1 = 600, 768
DY = H1 - H0

# windows whose generator draws a 768 version itself (a parameter h): their
# 600 geometry can't simply be stretched - the keyboard's keys must grow, not
# the gaps between them (L-3). Run through the same palette and size passes
# as xml/, then laid out like any other window.
TALL_GENERATORS = {"DialogKeyboard": "keyboard_window"}

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

# what may take extra height. Everything else (label, fadelabel, button,
# radiobutton, togglebutton, edit, spincontrolex, progress, slider ...) draws
# one line or one bar and only gets emptier: a label is <aligny>center</aligny>
# by default (Defaults.xml), so a stretched one floats away from its stack.
GROWABLE = SCROLLERS | GROUPS | {"image", "multiimage", "scrollbar", "videowindow",
                                 "visualisation", "gamewindow"}
FILL = 12       # a growable control ending this close to the body's bottom fills down with it

def growable(c):
    if c.get("type") in GROWABLE:
        return True
    return c.get("type") == "label" and (c.findtext("wrapmultiline") or "").strip() == "true"

def span(c):
    l, w = geti(c, "left"), geti(c, "width")
    return (l, l + w) if isinstance(l, int) and isinstance(w, int) else None

def bodies(controls, H):
    """The body of a column: the tallest scroller, else the tallest control,
    between a quarter and 95% of the container. A window with a category
    list beside a text panel has two columns, each with its own body, so a
    control is measured against the body it sits over or under (horizontal
    overlap), else against the tallest body of all. Returns a function giving
    (middle, top, bottom) - from the 600 geometry, read before anything is
    grown; with no body at all all three are the container's middle."""
    cand = []
    for c in controls:
        t, h = geti(c, "top"), geti(c, "height")
        if isinstance(t, int) and isinstance(h, int) and 0.25 * H <= h < 0.95 * H:
            cand.append((c.get("type") in SCROLLERS, t, h, span(c)))
    def pick(cs):
        sc = [b for b in cs if b[0]]
        return max(sc or cs, key=lambda b: b[2]) if cs else None
    overall = pick(cand)
    def line(body):
        if body is None:
            return H / 2, H / 2, H / 2
        _, t, h, _ = body
        return t + h / 2, t, t + h
    def body_for(c=None):
        sp = span(c) if c is not None else None
        if sp is not None:
            over = [b for b in cand if b[3] and b[3][0] < sp[1] and sp[0] < b[3][1]]
            if over:
                return line(pick(over))
        return line(overall)
    return body_for

def grow(container, H, dy, screen=False):
    """container is H tall and is about to be dy taller."""
    controls = kids(container)
    body_for = bodies(controls, H)
    S = body_for()[0]
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
            mid, BT, BB = body_for(c)
            if h >= 0.95 * H:
                action = "grow"
            elif growable(c) and (top < mid < top + h or
                                  BT <= top < BB <= top + h + FILL):
                action = "grow"
            elif top >= BB:
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

# ------------------------------------------------------------- special cases
def context_menu(root):
    """The context menu (T-9). Kodi moves the whole window so that image 999
    is centred on the focused control and stays on screen, and sizes 999 to
    the entries it adds: XML height - 996's XML height + 996's content
    height (CGUIDialogContextMenu::SetupButtons, ::SetPosition). So 999 must
    stay at 0,0, and making 999, grouplist 996 and its scrollbar 997 DY
    taller lets a long menu use the 768 screen down to the task bar while a
    short one still comes out short."""
    for cid in ("999", "996", "997"):
        c = root.find(f".//control[@id='{cid}']")
        if c is None or not isinstance(geti(c, "height"), int):
            raise RuntimeError(f"context menu: control {cid} has no plain height")
        seti(c, "height", geti(c, "height") + DY)
    bg = root.find(".//control[@id='999']")
    if geti(bg, "left") != 0 or geti(bg, "top") != 0:
        raise RuntimeError("context menu: 999 must sit at 0,0")

# panels whose cells grow instead of leaving a band under the last row: the
# Settings hub's 5 x 3 tiles (15 items at most) left 168 px empty at 768
# Settings hub (9200): its tile layouts now come from home.py per resolution
# (Settings_HubLayouts in Includes_Home.xml / build768), so nothing to grow.
TALLER_CELLS = {}
ICON = 64       # the hub icon at 768: icons64 drawn at its own size

def taller_cells(root, pid):
    """Grow the cells of panel pid so its rows fill its 768 height. Above the
    icon nothing moves; the icon becomes ICON px (the 600 hub draws a 64 px
    picture at 48); what sits under the icon (the name, its focus fill) is
    spread over the space left under it; full-cell frames grow. The items
    already name icons64 pictures in xml (the 600 hub scales them to 48);
    the <icon> pass below only makes sure each has an icons{ICON} file."""
    panel = root.find(f".//control[@id='{pid}']")
    ph = geti(panel, "height")
    lays = [l for l in panel if l.tag in ("itemlayout", "focusedlayout")]
    ih0 = int(lays[0].get("height"))
    rows = (ph - DY) // ih0
    ih1 = ph // rows
    for lay in lays:
        if int(lay.get("height")) != ih0:
            raise RuntimeError(f"{pid}: layouts of different heights")
        lay.set("height", str(ih1))
        cw = int(lay.get("width"))
        ctl = [c for c in lay if c.tag == "control"]
        icons = [c for c in ctl if c.findtext("texture", "").strip() == "$INFO[ListItem.Icon]"]
        if len(icons) != 1:
            raise RuntimeError(f"{pid}: expected one $INFO[ListItem.Icon] image per layout")
        ic = icons[0]
        it, ih = geti(ic, "top"), geti(ic, "height")
        nt = round(it * ih1 / ih0)
        seti(ic, "top", nt); seti(ic, "height", ICON)
        seti(ic, "width", ICON); seti(ic, "left", (cw - ICON) // 2)
        b0, b1 = it + ih, nt + ICON          # under the icon, old and new
        k = (ih1 - b1) / (ih0 - b0)
        for c in ctl:
            if c is ic:
                continue
            t, h = geti(c, "top"), geti(c, "height")
            if t + h >= ih0 - 6:             # a frame or ring around the cell
                seti(c, "height", h + ih1 - ih0)
            elif t >= b0:
                top, bot = b1 + round((t - b0) * k), b1 + round((t + h - b0) * k)
                seti(c, "top", top); seti(c, "height", bot - top)
    media = os.path.join(SKIN, "media", f"icons{ICON}")
    for icon in panel.iter("icon"):
        m = re.fullmatch(r"icons\d*/([a-z0-9_]+\.png)", (icon.text or "").strip())
        if not m or not os.path.exists(os.path.join(media, m.group(1))):
            raise RuntimeError(f"{pid}: no icons{ICON} picture for {icon.text}")
        icon.text = f"icons{ICON}/{m.group(1)}"

# ------------------------------------------------------------- windows
def convert(src_path, dst_path):
    tree = etree.parse(src_path)
    root = tree.getroot()
    expand(root, {})
    coords = root.find("coordinates")
    controls = root.find("controls")
    if controls is not None:
        # windows placed with <coordinates> (the context menu) are positioned
        # by Kodi itself; only the context menu's list grows (context_menu)
        if coords is None:
            grow(controls, H0, DY, screen=True)
        elif root.find(".//control[@id='996']") is not None:
            context_menu(root)
    name = os.path.splitext(os.path.basename(dst_path))[0]
    if name in TALLER_CELLS:
        taller_cells(root, TALLER_CELLS[name])
    for lab in root.iter("label"):         # the version line in Skin settings
        if lab.text and "1024x600" in lab.text:
            lab.text = lab.text.replace("1024x600", f"1024x{H1}")
    tree.write(dst_path, encoding="UTF-8", xml_declaration=True)

def tall_sources():
    """{file name: path} of the 768 versions drawn by their own generators."""
    sys.path.insert(0, HERE)
    import genwindows
    tmp = tempfile.mkdtemp(prefix="tallpass-")
    for name, fn in TALL_GENERATORS.items():
        with open(os.path.join(tmp, name + ".xml"), "w") as f:
            f.write(getattr(genwindows, fn)(h=H1))
    env = dict(os.environ, XMLDIR=tmp)
    for step in ("themepass.py", "sizepass.py"):
        subprocess.run([sys.executable, os.path.join(HERE, step)], env=env, check=True,
                       stdout=subprocess.DEVNULL)
    return tmp, {n + ".xml": os.path.join(tmp, n + ".xml") for n in TALL_GENERATORS}

def main():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)
    staged = {os.path.basename(p): p for p in glob.glob(os.path.join(STAGE, "*.xml"))}
    tmp, tall = tall_sources()
    staged.update(tall)
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
    shutil.rmtree(tmp)
    print(f"tallpass: {n} windows laid out for 1024x768 in xml768"
          f" ({', '.join(sorted(TALL_GENERATORS))} drawn for {H1} by their generators)")

# ------------------------------------------------------------- checks
# `tallpass.py --check NAME` tests the shipped xml768 against xml (audit.sh).
ONE_LINE = {"label", "fadelabel", "button", "radiobutton", "togglebutton", "edit",
            "spincontrolex", "progress", "slider"}

def _windows(folder):
    for p in sorted(glob.glob(os.path.join(SKIN, folder, "*.xml"))):
        root = etree.parse(p).getroot()
        if root.tag == "window":
            yield os.path.basename(p), root

def _expanded(name):
    root = etree.parse(os.path.join(SRC, name)).getroot()
    expand(root, {})
    return root

def check_lines():
    """L-1: no single-line control is taller in xml768 than the same control
    is in the same window's expanded xml, unless it covers the whole screen
    (a tap catcher). Controls are paired in document order, so anonymous
    labels (the Weather '/' labels) are checked one by one, not against a
    pool of heights seen anywhere."""
    bad = []
    for name, b in _windows("xml768"):
        if not os.path.exists(os.path.join(SRC, name)):
            bad.append(f"{name}: in xml768 but not in xml")
            continue
        if os.path.splitext(name)[0] in TALL_GENERATORS:
            continue        # drawn for 768 by its generator (check_keyboard)
        ca, cb = list(_expanded(name).iter("control")), list(b.iter("control"))
        if [(c.get("type"), c.get("id")) for c in ca] != [(c.get("type"), c.get("id")) for c in cb]:
            bad.append(f"{name}: controls differ from xml, cannot pair them")
            continue
        for x, y in zip(ca, cb):
            h0, h = geti(x, "height"), geti(y, "height")
            if (y.get("type") in ONE_LINE and isinstance(h, int) and h > 60 and h != H1
                    and (y.findtext("wrapmultiline") or "").strip() != "true"
                    and h != h0):
                bad.append(f"{name}: {y.get('type')} id={y.get('id')} height {h0} -> {h}")
    return bad

def check_stack():
    """L-1: System information's lines 2-13 sit over its text panel; at 768
    they keep their 600 places (a stack, not spread over the taller panel)."""
    a = _expanded("SettingsSystemInfo.xml")
    b = etree.parse(os.path.join(DST, "SettingsSystemInfo.xml")).getroot()
    bad = []
    for i in range(2, 14):
        ca, cb = a.find(f".//control[@id='{i}']"), b.find(f".//control[@id='{i}']")
        if (geti(ca, "top"), geti(ca, "height")) != (geti(cb, "top"), geti(cb, "height")):
            bad.append(f"label {i}: {geti(ca, 'top')}/{geti(ca, 'height')} -> "
                       f"{geti(cb, 'top')}/{geti(cb, 'height')}")
    return bad

def _bottoms(root):
    out = []
    controls = root.find("controls")
    for c in kids(controls) if controls is not None else []:
        if c.find("bottom") is not None and c.find("top") is None:
            out.append((c.get("type"), c.get("id"), c.findtext("bottom").strip()))
    return sorted(out, key=str)

def check_bottom():
    """Dialogs hung from the bottom edge in xml (OSDs, seek bar, bookmarks,
    info) are hung from it the same way in xml768."""
    bad = []
    for name, root in _windows("xml768"):
        a, b = _bottoms(_expanded(name)), _bottoms(root)
        if a != b:
            bad.append(f"{name}: bottom-anchored {a} in xml, {b} in xml768")
    return bad

def check_contextmenu():
    a, b = _expanded("DialogContextMenu.xml"), etree.parse(os.path.join(DST, "DialogContextMenu.xml")).getroot()
    bad = []
    for cid in ("999", "996", "997"):
        ca, cb = a.find(f".//control[@id='{cid}']"), b.find(f".//control[@id='{cid}']")
        if geti(cb, "height") != geti(ca, "height") + DY or geti(cb, "top") != geti(ca, "top"):
            bad.append(f"{cid}: height {geti(ca, 'height')} -> {geti(cb, 'height')}")
    bg = b.find(".//control[@id='999']")
    if (geti(bg, "left"), geti(bg, "top")) != (0, 0) or bg.getparent().tag != "controls":
        bad.append("999 is not top-level at 0,0")
    return bad

def check_keyboard():
    a, b = _expanded("DialogKeyboard.xml"), etree.parse(os.path.join(DST, "DialogKeyboard.xml")).getroot()
    ids = lambda r: sorted(c.get("id") for c in r.iter("control") if c.get("id"))
    key = lambda r: geti(r.find(".//control[@id='100']"), "height")
    def key_600(xl):
        # the 600 keys: an XLC Height_N pair (56 px with taller rows)
        k = a.find(".//control[@id='100']")
        for inc in k.findall("include"):
            c = inc.get("condition") or ""
            m = re.fullmatch(r"Height_(\d+)(_XL)?", inc.get("content") or "")
            if m and c.startswith("!") != xl:
                d = includes[m.group(0)]
                return int(d.findtext("height"))
        return None
    box = [c for c in kids(b.find("controls")) if c.findtext("centertop") == "50%"]
    bad = []
    # (the 600 box is a pair of conditional Dialog_Box includes, left
    # unexpanded, so its title-bar ids are only in the 768 tree)
    if not set(ids(a)) <= set(ids(b)) or len(ids(a)) < 70:
        bad.append("different control ids")
    if not (key(b) >= 56 > (key_600(False) or 99) and (key_600(True) or 0) >= 56):
        bad.append(f"keys {key_600(False)}/{key_600(True)} -> {key(b)} px")
    if len(box) != 1 or geti(box[0], "height") > H1 - 32 - 30:
        bad.append("not one centred box clear of the menu and task bars")
    return bad

def check_cells():
    bad = []
    for name, pid in TALLER_CELLS.items():
        a = _expanded(name + ".xml").find(f".//control[@id='{pid}']")
        b = etree.parse(os.path.join(DST, name + ".xml")).getroot().find(f".//control[@id='{pid}']")
        ha, hb = geti(a, "height"), geti(b, "height")
        ia, ib = int(a.find("itemlayout").get("height")), int(b.find("itemlayout").get("height"))
        if ha // ia != hb // ib or hb - (hb // ib) * ib >= 12:
            bad.append(f"{name} {pid}: {ha}/{ia} -> {hb}/{ib}")
        for lay in (l for l in b if l.tag in ("itemlayout", "focusedlayout")):
            for c in lay.iter("control"):
                if (c.findtext("texture") or "").strip() == "$INFO[ListItem.Icon]" and \
                        (geti(c, "width"), geti(c, "height")) != (ICON, ICON):
                    bad.append(f"{name} {pid}: icon {geti(c, 'width')}x{geti(c, 'height')}, not {ICON}x{ICON}")
        media = os.path.join(SKIN, "media", f"icons{ICON}")
        for icon in b.iter("icon"):
            m = re.fullmatch(rf"icons{ICON}/([a-z0-9_]+\.png)", (icon.text or "").strip())
            if not m or not os.path.exists(os.path.join(media, m.group(1))):
                bad.append(f"{name} {pid}: item icon {icon.text} is not an icons{ICON} picture")
    return bad

CHECKS = {"lines": check_lines, "stack": check_stack, "bottom": check_bottom, "contextmenu": check_contextmenu,
          "keyboard": check_keyboard, "cells": check_cells}

if __name__ == "__main__":
    if sys.argv[1:2] == ["--check"]:
        problems = CHECKS[sys.argv[2]]()
        for x in problems:
            print("  ", x)
        sys.exit(1 if problems else 0)
    main()
