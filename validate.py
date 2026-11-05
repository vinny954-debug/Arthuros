#!/usr/bin/env python3
"""Static checks that catch the things Kodi only complains about at runtime."""
import os, re, glob, sys, collections
import xml.etree.ElementTree as ET

SKIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skin.arthuros")
XML, MEDIA = os.path.join(SKIN,os.environ.get("RES","xml")), os.path.join(SKIN,"media")
errors, warns = [], []
VALID_TYPES = {"button","colorbutton","edit","epggrid","fadelabel","fixedlist","gamecontroller",
 "gamecontrollerlist","gamewindow","group","grouplist","image","label","list","mover","multiimage",
 "panel","progress","radiobutton","ranges","renderaddon","resize","rss","scrollbar","slider",
 "sliderex","spincontrol","spincontrolex","textbox","togglebutton","videowindow","visualisation",
 "wraplist"}

media_files = set()
for r, _, fs in os.walk(MEDIA):
    for f in fs:
        media_files.add(os.path.relpath(os.path.join(r,f), MEDIA).replace(os.sep,"/"))

colors = {c.get("name") for c in ET.parse(os.path.join(SKIN,"colors/defaults.xml")).getroot()}
fonts  = set()
for fs in ET.parse(os.path.join(XML,"Font.xml")).getroot():
    for f in fs.findall("font"): fonts.add(f.findtext("name"))

includes, windows = {}, {}
for p in sorted(glob.glob(os.path.join(XML,"*.xml"))):
    try: root = ET.parse(p).getroot()
    except ET.ParseError as e:
        errors.append(f"{os.path.basename(p)}: XML parse error: {e}"); continue
    if root.tag == "includes":
        for i in root.findall("include"):
            if i.get("name"):
                if i.get("name") in includes:
                    errors.append(f"duplicate include name {i.get('name')}")
                includes[i.get("name")] = i
    elif root.tag == "window":
        windows[os.path.basename(p)[:-4]] = root
    elif root.tag == "fonts":
        pass
    else:
        warns.append(f"{os.path.basename(p)}: unexpected root <{root.tag}>")

# chained include files must actually be referenced
chained = {i.get("file") for i in ET.parse(os.path.join(XML,"Includes.xml")).getroot().findall("include") if i.get("file")}
for p in glob.glob(os.path.join(XML,"*.xml")):
    b = os.path.basename(p)
    root = ET.parse(p).getroot()
    if root.tag == "includes" and b not in chained and b not in ("Includes.xml","Defaults.xml"):
        errors.append(f"{b} defines includes but is not chained from Includes.xml")

def resolve(el, params=None, depth=0, chain=()):
    """Yield concrete controls with params substituted."""
    if depth > 14: return
    for ch in list(el):
        if ch.tag == "include":
            name = ch.get("content") or (ch.text.strip() if ch.text else None)
            if name is None: continue
            # Kodi substitutes parameters into attributes before resolving a
            # nested include, so <include content="Win_Boxes_$PARAM[boxes]"> works
            for k, pv in (params or {}).items(): name = name.replace(f"$PARAM[{k}]", pv)
            if name not in includes:
                errors.append(f"unknown include '{name}' (via {' > '.join(chain) or 'window'})")
                continue
            inc = includes[name]
            p = {pd.get("name"): pd.get("default","") for pd in inc.findall("param")}
            for pu in ch.findall("param"):
                v = pu.get("value","")
                if params:
                    for k, pv in params.items(): v = v.replace(f"$PARAM[{k}]", pv)
                p[pu.get("name")] = v
            body = inc.find("definition")
            # a conditional include is a branch: Kodi loads it or it doesn't, so
            # ids may repeat across branches that exclude each other
            tag = name + ("?" + ch.get("condition") if ch.get("condition") else "")
            yield from resolve(body if body is not None else inc, p, depth+1, chain+(tag,))
            continue
        yield (ch, params, chain)
        yield from resolve(ch, params, depth+1, chain)

def sub(t, params):
    if not t: return t
    if params:
        for k, v in params.items(): t = t.replace(f"$PARAM[{k}]", v)
    return t

for wname, root in sorted(windows.items()):
    seen_ids = collections.Counter()
    nav_refs, ctrl_ids = [], set()
    for el, params, chain in resolve(root):
        if el.tag == "control":
            cid = sub(el.get("id"), params)
            if cid:
                if not re.fullmatch(r"\d+", cid):
                    errors.append(f"{wname}: non-numeric control id '{cid}'")
                else:
                    branch = next((c for c in chain if "?" in c), None)
                    seen_ids[(cid, branch)] += 1; ctrl_ids.add(cid)
            ct = el.get("type")
            if not ct:
                errors.append(f"{wname}: <control> with no type")
            elif ct not in VALID_TYPES:
                errors.append(f"{wname}: invalid control type '{ct}'")
        if el.tag == "texture":
            t = sub((el.text or "").strip(), params)
            if t and t != "-" and "$" not in t and t not in media_files:
                errors.append(f"{wname}: missing texture '{t}'" + (f" (in {chain[-1]})" if chain else ""))
        if el.tag in ("texturefocus","texturenofocus","texturesliderbar","texturesliderbackground",
                      "texturesliderbarfocus","midtexture","texturebg","textureup","texturedown",
                      "textureupfocus","texturedownfocus","textureradioonfocus","textureradioonnofocus",
                      "textureradioofffocus","textureradiooffnofocus","textureslidernib","textureslidernibfocus"):
            t = sub((el.text or "").strip(), params)
            if t and t != "-" and "$" not in t and t not in media_files:
                errors.append(f"{wname}: missing texture '{t}' in <{el.tag}>")
        if el.tag == "font":
            f = sub((el.text or "").strip(), params)
            if f and "$" not in f and f not in fonts:
                errors.append(f"{wname}: unknown font '{f}'")
        if el.tag in ("textcolor","focusedcolor","disabledcolor","selectedcolor","shadowcolor",
                      "invalidcolor","colordiffuse"):
            c = sub((el.text or "").strip(), params)
            if c and c != "-" and "$" not in c and c not in colors and not re.fullmatch(r"[0-9A-Fa-f]{8}", c):
                errors.append(f"{wname}: unknown colour '{c}' in <{el.tag}>")
        cd = el.get("colordiffuse")
        if cd is not None:
            cd = sub(cd, params)
            if cd and "$" not in cd and cd not in colors and not re.fullmatch(r"[0-9A-Fa-f]{8}", cd):
                errors.append(f"{wname}: colordiffuse '{cd}' is not a defined colour on <{el.tag}>")
        if el.tag in ("onleft","onright","onup","ondown"):
            v = sub((el.text or "").strip(), params)
            if re.fullmatch(r"\d+", v): nav_refs.append((el.tag, v))
    for (cid, branch), n in seen_ids.items():
        if n > 1:
            errors.append(f"{wname}: control id {cid} defined {n} times" + (f" in {branch.split('?')[0]}" if branch else ""))
        elif branch and seen_ids.get((cid, None)):
            errors.append(f"{wname}: control id {cid} is both unconditional and in {branch.split('?')[0]}")
    for tag, v in nav_refs:
        if v not in ctrl_ids and v not in ("9100","9101","9102","9103","9000","9010","9011","9490","9500","9600"):
            warns.append(f"{wname}: <{tag}> points at id {v} which is not in this window")
    # containers must declare their own layouts now that Defaults.xml has none
    for el, params, chain in resolve(root):
        if el.tag == "control" and el.get("type") in ("list","panel","fixedlist","wraplist"):
            cid = sub(el.get("id"), params) or "?"
            # layouts may also arrive through an include (Home's grid sizes)
            got = {c.tag for c in el} | {c.tag for c, _, _ in resolve(el)}
            if "itemlayout" not in got:
                errors.append(f"{wname}: {el.get('type')} id {cid} has no <itemlayout>")
            if "focusedlayout" not in got and el.get("type") != "wraplist":
                errors.append(f"{wname}: {el.get('type')} id {cid} has no <focusedlayout>")

    # Kodi only shows/hides containers named in <views>. Any other container
    # in the 50-59 view range stays visible forever and covers the live one.
    vs_ids = {v.strip() for v in (root.findtext("views") or "").split(",") if v.strip()}
    if vs_ids:
        for el, params, chain in resolve(root):
            if el.tag == "control" and el.get("type") in ("list","panel","fixedlist","wraplist"):
                cid = sub(el.get("id"), params)
                if cid and cid.isdigit() and 50 <= int(cid) <= 59 and cid not in vs_ids:
                    errors.append(f"{wname}: container {cid} is not in <views> - it will never be hidden and will cover the active view")

    dc = root.findtext("defaultcontrol")
    if dc and dc.strip() and dc.strip() not in ctrl_ids:
        errors.append(f"{wname}: defaultcontrol {dc.strip()} does not exist")
    vs = (root.findtext("views") or "").strip()
    for v in [x for x in vs.split(",") if x.strip()]:
        if v.strip() not in ctrl_ids:
            errors.append(f"{wname}: <views> lists {v} but no such control")

# --- invariants that have bitten before -------------------------------------

# Kodi selects the mouse cursor by control id (MOUSE_STATE_NORMAL = 1 ...).
# Without ids 1-4 there is simply no cursor, and nothing is logged.
if "Pointer" in windows:
    pids = {sub(el.get("id"), p) for el, p, _ in resolve(windows["Pointer"])
            if el.tag == "control" and el.get("id")}
    missing = {"1","2","3","4"} - pids
    if missing:
        errors.append(f"Pointer: missing cursor control id(s) {sorted(missing)} - there will be no mouse cursor")
else:
    errors.append("Pointer.xml is missing - there will be no mouse cursor")

# A fontset idloc pointing at a string that does not exist yields a blank row
# in Kodi's font picker, with no error anywhere.
KODI_PO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "kodi", "strings.po")
kodi_ids = set()
if os.path.exists(KODI_PO):
    kodi_ids = {int(m) for m in re.findall(r'msgctxt "#(\d+)"', open(KODI_PO, encoding="utf-8").read())}
SKIN_PO = os.path.join(SKIN, "language/resource.language.en_gb/strings.po")
skin_ids = {int(m) for m in re.findall(r'msgctxt "#(\d+)"', open(SKIN_PO).read())} if os.path.exists(SKIN_PO) else set()
for fs in ET.parse(os.path.join(XML, "Font.xml")).getroot().findall("fontset"):
    il = fs.get("idloc")
    if il and int(il) not in kodi_ids and int(il) not in skin_ids:
        errors.append(f"Font.xml: fontset '{fs.get('id')}' idloc={il} is not a defined string (blank row in Kodi's font picker)")

# Every $LOCALIZE in the skin's own 31xxx range must actually be defined.
for p2 in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    for n in re.findall(r"\$LOCALIZE\[(\d+)\]", open(p2).read()):
        n = int(n)
        if 31000 <= n <= 31999 and n not in skin_ids:
            errors.append(f"{os.path.basename(p2)}: $LOCALIZE[{n}] is not defined in strings.po")
        elif n < 31000 and kodi_ids and n not in kodi_ids:
            errors.append(f"{os.path.basename(p2)}: $LOCALIZE[{n}] is not a Kodi string")

# The busy dialog's window name is 'busydialog'; 'Busy' silently does nothing.
for p2 in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    if "Window(Busy)" in open(p2).read():
        errors.append(f"{os.path.basename(p2)}: Window(Busy) is not a window name - use busydialog")

# A palette may only override names defaults.xml defines - a misspelt name in a
# palette is silently ignored by Kodi and the colour just never changes.
for pf in sorted(glob.glob(os.path.join(SKIN, "colors", "*.xml"))):
    if pf.endswith("defaults.xml"): continue
    for c in ET.parse(pf).getroot():
        if c.get("name") not in colors:
            errors.append(f"colors/{os.path.basename(pf)}: '{c.get('name')}' is not a colour defaults.xml defines")
        if not re.fullmatch(r"[0-9A-Fa-f]{8}", (c.text or "").strip()):
            errors.append(f"colors/{os.path.basename(pf)}: '{c.get('name')}' value '{c.text}' is not AARRGGBB")

# A grouplist chains its children's up/down (or left/right) by control id
# (CGUIControlGroupList::AddControl). A child with no id has id 0, and Kodi
# treats navigation to 0 as "nowhere", so the keyboard stops dead at it.
# Headings and dividers inside a grouplist therefore need an id too.
for wname, root in sorted(windows.items()):
    for el, params, chain in resolve(root):
        if el.tag == "control" and el.get("type") == "grouplist":
            kids = [k for k in el if k.tag == "control"]
            focusable = [k for k in kids if k.get("type") not in ("label", "image", "fadelabel", "textbox", "group")]
            if len(focusable) < 2:
                continue
            for k in kids:
                if not sub(k.get("id"), params):
                    errors.append(f"{wname}: {k.get('type')} inside a grouplist has no id - "
                                  "keyboard navigation stops at it")

# The context menu is positioned by Kodi, which moves the whole window so that
# control 999 lands next to the focused control. 999 must therefore be a
# top-level control at the window origin, with nothing else offset.
cm = os.path.join(XML, "DialogContextMenu.xml")
if os.path.exists(cm):
    croot = ET.parse(cm).getroot().find("controls")
    top = [c for c in croot if c.tag == "control"]
    bg = [c for c in top if c.get("id") == "999"]
    if not bg or (bg[0].findtext("left") or "0") != "0" or (bg[0].findtext("top") or "0") != "0":
        errors.append("DialogContextMenu: image 999 must be a top-level control at left 0, top 0 - Kodi positions the window by it")
    if any(i.text and "Dialog_Dim" in i.text for i in croot.iter("include")):
        errors.append("DialogContextMenu: a full-screen dim moves with the menu - leave it out")

# spinposx is measured in from the right edge (GUISpinControlEx.cpp), so a
# negative value pushes the arrows outside the control.
for p2 in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    for n in re.findall(r"<spinposx>(-?\d+)</spinposx>", open(p2).read()):
        if int(n) < 0:
            errors.append(f"{os.path.basename(p2)}: spinposx {n} puts spin arrows past the right edge")

# Static list items: Kodi's CGUIControlFactory reads a property that is a
# bare number as a string id (<property name="slot">3</property> = "Videos"),
# and CGUIStaticItem::UpdateProperties turns properties named icon, thumb,
# label or label2 into the item's art/labels, so ListItem.Property(icon)
# never updates. Both bit the desktop editor in 0.9.0.
for p2 in glob.glob(os.path.join(XML, "*.xml")):
    try:
        r2 = ET.parse(p2).getroot()
    except ET.ParseError:
        continue
    for it in r2.iter("item"):
        for pr in it.findall("property"):
            nm = (pr.get("name") or "").lower()
            if nm in ("icon", "thumb", "label", "label2"):
                errors.append(f"{os.path.basename(p2)}: static item property named '{nm}' - Kodi treats it as art/label, use another name")
            if re.fullmatch(r"\d+", (pr.text or "").strip()):
                errors.append(f"{os.path.basename(p2)}: static item property '{nm}' is a bare number, which Kodi reads as a string id - use $NUMBER[n]")

# Kodi 21 has no ListItem.Property(Addon.*) - those names are always empty.
for p2 in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    if "Property(Addon." in open(p2).read():
        errors.append(f"{os.path.basename(p2)}: ListItem.Property(Addon.*) is always empty in Kodi 21 - use ListItem.Addon*")

# Startup.xml is part of Kodi's own start-up: until it hands over, the UI is
# never "ready" (skin reloads are refused, CEC waits, the mouse is ignored).
# It must replace itself with the start window on load, as Estuary's does.
st = os.path.join(XML, "Startup.xml")
if os.path.exists(st):
    ol = [o.text or "" for o in ET.parse(st).getroot().findall("onload")]
    if not any("ReplaceWindow($INFO[System.StartupWindow])" in o for o in ol):
        errors.append("Startup.xml: no <onload>ReplaceWindow($INFO[System.StartupWindow])</onload> - Kodi would sit on it forever")

# Title-bar box modes must name an include that exists.
for p2 in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    for mode in re.findall(r'<param name="boxes" (?:value|default)="([^"$]*)"', open(p2).read()):
        if f"Win_Boxes_{mode}" not in includes:
            errors.append(f"{os.path.basename(p2)}: title-bar boxes mode '{mode}' has no Win_Boxes_{mode} include")

print(f"{len(windows)} windows, {len(includes)} includes, {len(media_files)} textures")
if errors:
    print(f"\n{len(errors)} ERRORS")
    for e in errors[:60]: print("  ✗", e)
else:
    print("\nno errors")
if warns:
    print(f"\n{len(warns)} warnings")
    for x in warns[:30]: print("  ·", x)
sys.exit(1 if errors else 0)
