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
    elif root.tag in ("fonts", "timers"):
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
        # a container layout scopes its control ids per item: mark the chain
        nxt = chain + ("@layout",) if ch.tag.endswith("layout") else chain
        yield from resolve(ch, params, depth+1, nxt)

def sub(t, params):
    if not t: return t
    if params:
        for k, v in params.items(): t = t.replace(f"$PARAM[{k}]", v)
    return t

NONFOCUS = {"image", "label", "fadelabel", "progress", "textbox", "rss", "multiimage",
            "visualisation", "videowindow", "gamewindow", "ranges"}
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
                    # Duplicate ids only matter for controls that take focus or
                    # are addressed as one (groups, containers, buttons...). Kodi
                    # keeps ids inside container layouts per item, and
                    # non-focusable controls may share an id on purpose (e.g.
                    # VideoFullScreen's buffering box: every child id 1, so the
                    # BLUE_BAR id-0 broadcast never hides it - as in Estuary).
                    in_layout = "@layout" in chain
                    if not in_layout and el.get("type") not in NONFOCUS:
                        seen_ids[(cid, branch)] += 1
                    ctrl_ids.add(cid)
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
    # every target must be a control this window really has (resolve() expands
    # Chrome_Taskbar, Home's panel and the toolbar, so their ids count only
    # where they are actually pulled in - no fixed whitelist)
    for tag, v in nav_refs:
        if v not in ctrl_ids:
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

# --- Kodi tables: builtins, actions, windows, info labels --------------------
# Taken from the Omega sources by vendor/kodi/mktables.py. Anything Kodi does
# not know fails silently on the box (a button that does nothing, a condition
# that is always false), so check every name against them.
HERE = os.path.dirname(os.path.abspath(__file__))
def table(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        errors.append(f"{name} is missing - run python3 vendor/kodi/mktables.py"); return []
    return [l.rstrip("\n").split("\t") for l in open(p) if l.strip() and not l.startswith("#")]
BUILTINS = {r[0]: int(r[1]) for r in table("vendor/kodi/builtins.txt")}
ACTIONS = {r[0] for r in table("vendor/kodi/actions.txt")}
WIN_IDS = {r[0]: int(r[1]) for r in table("vendor/kodi/windowids.txt")}
WIN_NAMES = {r[0] for r in table("windownames.txt")}
INFO = collections.defaultdict(set)
for r in table("vendor/kodi/infolabels.txt"):
    c, _, p = r[0].partition("."); INFO[c].add(p)
if set(WIN_IDS) != WIN_NAMES:
    errors.append("windownames.txt and vendor/kodi/windowids.txt disagree - rerun vendor/kodi/mktables.py")
# skin windows with their own id (Custom_1120_... = <window id="1120">); Kodi
# adds 10000 to an id below 9999 both here and in ActivateWindow(1120)
SKIN_WIN_IDS = set()
for p2 in glob.glob(os.path.join(XML, "Custom_*.xml")):
    i = ET.parse(p2).getroot().get("id")
    if i and i.isdigit():
        SKIN_WIN_IDS.add(int(i) + 10000 if int(i) < 9999 else int(i))
KODI_WIN_ID_SET = set(WIN_IDS.values())
XML_NAMES = {os.path.basename(p)[:-4].lower() for p in glob.glob(os.path.join(XML, "*.xml"))}

def window_ok(w, cond=False):
    """CWindowTranslator::TranslateWindow, plus 'foo.xml' in conditions."""
    w = w.strip().strip('"').lower()
    if not w or "$" in w:
        return True
    if cond and w.endswith(".xml"):
        return w[:-4] in XML_NAMES
    if w.endswith(".xml"): w = w[:-4]
    if len(w) > 6 and w.startswith("window"): w = w[6:]
    if w.startswith("my"): w = w[2:]
    if w.isdigit():
        n = int(w); n = n if n > 9999 else 10000 + n
        return n in KODI_WIN_ID_SET or n in SKIN_WIN_IDS
    return w in WIN_NAMES

def split_params(s):
    """CUtil::SplitParams: commas split unless inside (), "" or $INFO[...]."""
    out, cur, depth, sq, q = [], "", 0, 0, False
    for ch in s:
        if q:
            q = ch != '"'
        elif ch == '"': q = True
        elif ch == "(": depth += 1
        elif ch == ")": depth = max(0, depth - 1)
        elif ch == "[": sq += 1
        elif ch == "]": sq = max(0, sq - 1)
        elif ch == "," and not depth and not sq:
            out.append(cur.strip()); cur = ""; continue
        cur += ch
    if cur.strip() or out: out.append(cur.strip())
    return [p[1:-1] if len(p) > 1 and p[0] == p[-1] == '"' else p for p in out]

def split_exec(a):
    """SplitExecFunction: function before the first '(', params up to the last ')'."""
    i, j = a.find("("), a.rfind(")")
    if i >= 0 and j > i:
        return a[:i].strip().lower(), split_params(a[i + 1:j])
    return a.strip().lower(), []

ACTION_TAGS = ("onclick", "onfocus", "onunfocus", "onload", "onunload", "onback",
               "onup", "ondown", "onleft", "onright", "onnext", "onprev", "oninfo")
WINDOW_BUILTINS = ("activatewindow", "replacewindow", "activatewindowandfocus",
                   "replacewindowandfocus", "dialog.close")
SKIN_DIR = SKIN
n_checked = collections.Counter()
def check_action(where, a):
    n_checked["actions"] += 1
    a = a.strip()
    if not a or a == "-" or re.fullmatch(r"\d+", a) or a.startswith("$"):
        return
    fn, params = split_exec(a)
    if "$" in fn:
        return
    if "(" not in a and fn in ACTIONS:
        return
    if fn not in BUILTINS:
        errors.append(f"{where}: '{a}' is neither a Kodi builtin nor an action name - it does nothing")
        return
    if BUILTINS[fn] and len(params) < BUILTINS[fn]:
        errors.append(f"{where}: {fn} needs {BUILTINS[fn]} parameter(s), '{a}' has {len(params)} - Kodi ignores it")
    if fn == "action" and params and "$" not in params[0] and \
            params[0].lower() not in ACTIONS and not params[0].isdigit():
        errors.append(f"{where}: Action({params[0]}) is not a Kodi action name")
    if fn in WINDOW_BUILTINS and params and not (fn == "dialog.close" and params[0].lower() == "all"):
        if not window_ok(params[0]):
            errors.append(f"{where}: '{params[0]}' in {a} is not a window name in windownames.txt")
    if fn in ("runscript", "runaddon") and params:
        p = params[0]
        if p.startswith("special://skin/") and "$" not in p:
            if not os.path.isfile(os.path.join(SKIN_DIR, p[len("special://skin/"):])):
                errors.append(f"{where}: {p} does not exist in the skin")

COND_TAGS = ("visible", "enable", "selected", "usealttexture", "onclick", "hidden",
             "expression", "info", "info2")
SEG = r"[A-Za-z][A-Za-z0-9_]*"
INFO_NAME = re.compile(rf"{SEG}(?:\([^()]*\)(?=\.))?(?:\.{SEG}(?:\([^()]*\)(?=\.))?)+")
def info_names(text, out):
    """Collect Category[(...)].property names from a condition or label, the
    way TranslateSingleString splits them. Arguments are only followed where
    Kodi reads them as info labels: String.*() first argument, Integer.*()."""
    i, n = 0, len(text)
    while i < n:
        m = INFO_NAME.match(text, i)
        if not m or (i and (text[i - 1].isalnum() or text[i - 1] in "_.$")):
            i += 1; continue
        name = m.group(0); i = m.end()
        args = ""
        if i < n and text[i] == "(":
            d, j = 0, i
            while j < n:
                d += text[j] == "("; d -= text[j] == ")"
                if d == 0: break
                j += 1
            args, i = text[i + 1:j], j + 1
        out.append(name)
        cat = name.lower().split(".")[0]
        ps = split_params(args)
        if cat == "string" and ps:
            info_names(ps[0], out)
        elif cat == "integer":
            for p in ps: info_names(p, out)

def check_info(where, name):
    n_checked["info names"] += 1
    parts = [re.sub(r"\(.*?\)", "", p).lower() for p in name.split(".")]
    cat = parts[0]
    if cat not in INFO or len(parts) < 2:
        return                      # not an info category (a literal like plugin.video.x)
    if len(parts) == 2:
        if parts[1] not in INFO[cat]:
            warns.append(f"{where}: {name} is not an info label/bool Kodi 21 knows - always empty/false")
    elif cat == "container" and parts[1].startswith("listitem") and len(parts) == 3:
        if parts[2] not in INFO["listitem"]:
            warns.append(f"{where}: {name} is not a ListItem label Kodi 21 knows")

# $VAR / $EXP must name a <variable>/<expression> some includes file defines
variables, expressions = set(), set()
for p2 in glob.glob(os.path.join(XML, "*.xml")):
    r2 = ET.parse(p2).getroot()
    if r2.tag == "includes":
        variables |= {v.get("name") for v in r2.iter("variable")}
        expressions |= {v.get("name") for v in r2.iter("expression")}

for p2 in sorted(glob.glob(os.path.join(XML, "*.xml"))):
    b = os.path.basename(p2)[:-4]
    txt = open(p2).read()
    for v in re.findall(r"\$VAR\[([^\]$]+)\]", txt):
        if v not in variables:
            errors.append(f"{b}: $VAR[{v}] is not a defined <variable>")
    for v in re.findall(r"\$EXP\[([^\]$]+)\]", txt):
        if v not in expressions:
            errors.append(f"{b}: $EXP[{v}] is not a defined <expression>")
    r2 = ET.parse(p2).getroot()
    if r2.tag not in ("window", "includes"):
        continue
    for el in r2.iter():
        t = (el.text or "").strip()
        if el.tag in ACTION_TAGS and t and "$PARAM" not in t.split("(")[0]:
            check_action(b, t)
        conds = []
        if el.get("condition"): conds.append(el.get("condition"))
        if el.tag in COND_TAGS and el.tag not in ACTION_TAGS and t: conds.append(t)
        for c in conds:
            if "$PARAM" in c: continue
            names = []
            info_names(c, names)
            for nm in names: check_info(b, nm)
            for w in re.findall(r"Window\.Is(?:Active|Visible|Topmost|DialogTopmost|ModalDialogTopmost)\(([^()]*)\)", c, re.I):
                if not window_ok(w, cond=True):
                    errors.append(f"{b}: Window.Is...({w}) - not a window name in windownames.txt")
        for lab in re.findall(r"\$(?:ESC)?INFO\[([^\],\]]+)", t):
            if "$PARAM" not in lab:
                names = []; info_names(lab, names)
                for nm in names: check_info(b, nm)
        for w in re.findall(r"Window\(([^()]*)\)\.Property", t + " " + (el.get("condition") or "")):
            if not window_ok(w, cond=True):
                errors.append(f"{b}: Window({w}).Property - not a window name in windownames.txt")

# Per window: focus targets in actions/conditions must be controls this window
# has; Kodi's own ids must exist in the hand-made windows; and a focusable
# control with no label, no action and no id Kodi fills is a dead blank box.
# (Window-scoped, so they run on the window with its includes expanded.)
REQUIRED = {   # #defines in the Omega window classes; a missing one hides a feature
 "MyPlaylist": ({"20","21","22","26"}, "GUIWindowMusicPlaylist.cpp/GUIWindowVideoPlaylist.cpp: shuffle, save, clear, repeat"),
 "MyPVRChannels": ({"28","6"}, "GUIWindowPVRBase.h: channel groups, show hidden"),
 "MyPVRRecordings": ({"28","7"}, "GUIWindowPVRBase.h: channel groups, show deleted"),
 "MyPVRTimers": ({"28"}, "GUIWindowPVRBase.h: channel groups"),
 "MyVideoNav": ({"8","20"}, "GUIWindowVideoNav.cpp: search, update library"),
 "MyMusicNav": ({"8","20"}, "GUIWindowMusicNav.cpp: search, update library"),
}
FOCUS_RE = re.compile(r"(?i)\b(?:control\.setfocus|setfocus|control\.move|control\.message|"
                      r"control\.setvisible|control\.sethidden)\((\d+)")
COND_ID_RE = re.compile(r"(?i)\b(?:control\.(?:hasfocus|isvisible|isenabled|getlabel)|"
                        r"controlgroup)\((\d+)\)|\bcontainer\((\d+)\)")
for wname, root in sorted(windows.items()):
    ids, focus_refs, cond_refs = set(), set(), set()
    for el, params, chain in resolve(root):
        if el.tag == "control" and sub(el.get("id"), params):
            ids.add(sub(el.get("id"), params))
        t = sub((el.text or "").strip(), params) or ""
        if el.tag in ACTION_TAGS:
            focus_refs |= set(FOCUS_RE.findall(t))
        cs = [sub(el.get("condition") or "", params)]
        if el.tag in COND_TAGS: cs.append(t)
        for c in cs:
            for a, b2 in COND_ID_RE.findall(c or ""):
                cond_refs.add(a or b2)
    for v in sorted(focus_refs - ids, key=int):
        errors.append(f"{wname}: SetFocus/Control.*({v}) targets a control this window does not have")
    for v in sorted(cond_refs - ids, key=int):
        errors.append(f"{wname}: Control/Container({v}) in a condition names a control this window does not have")
    if wname in REQUIRED:
        need, why = REQUIRED[wname]
        if need - ids:
            warns.append(f"{wname}: missing Kodi control id(s) {sorted(need - ids, key=int)} ({why})")
    for el, params, chain in resolve(root):
        if el.tag == "control" and el.get("type") in ("button", "radiobutton", "togglebutton"):
            lab = sub(el.findtext("label") or "", params).strip()
            acts = [c for c in el if c.tag in ("onclick", "onfocus") and (c.text or "").strip()]
            cid = sub(el.get("id"), params)
            if not lab and not acts and not cid:
                errors.append(f"{wname}: {el.get('type')} with no id, no label and no onclick - a dead blank box")

# Warnings are allowed only if they are known. A new one (a dead onup/ondown
# target, an info label Kodi doesn't have, a missing Kodi id) fails the build:
# fix it, or add it here with a reason. Fixed ones are only reported, so a
# package that fixes one doesn't break the build until this list is trimmed.
KNOWN_WARNINGS = {
    # Dialog_Dim's tap catcher defaults up/left to the title bar (9903); the
    # busy spinner has no title bar and nothing to focus - Kodi ignores it.
    "DialogBusy: <onup> points at id 9903 which is not in this window",
    "DialogBusy: <onleft> points at id 9903 which is not in this window",
    # MyPVRRecordings keeps no channel-group button (decided 0.9.7): only
    # GUIWindowPVRBase handles 28, and the recordings list ignores the
    # group (GUIWindowPVRRecordings::GetDirectoryPath builds the path from
    # deleted/radio only), so the button would change nothing on screen.
    # Estuary's MyPVRRecordings.xml has no 28 either.
    "MyPVRRecordings: missing Kodi control id(s) ['28'] (GUIWindowPVRBase.h: channel groups, show deleted)",
    # MyPVRTimers keeps no channel-group button: timers are not grouped by
    # channel group in the UI (Estuary has none either)
    "MyPVRTimers: missing Kodi control id(s) ['28'] (GUIWindowPVRBase.h: channel groups)",
}
for x in warns:
    if x not in KNOWN_WARNINGS:
        errors.append(f"{x}  [new warning: fix it, or list it in KNOWN_WARNINGS in validate.py]")
gone = sorted(KNOWN_WARNINGS - set(warns))
warns = [x for x in warns if x in KNOWN_WARNINGS]

print(f"{len(windows)} windows, {len(includes)} includes, {len(media_files)} textures, "
      f"{n_checked['actions']} actions, {n_checked['info names']} info names")
if errors:
    print(f"\n{len(errors)} ERRORS")
    for e in errors[:60]: print("  ✗", e)
else:
    print("\nno errors")
if warns:
    print(f"\n{len(warns)} warnings")
    for x in warns[:80]: print("  ·", x)
if gone:
    print(f"\n{len(gone)} known warning(s) no longer seen - remove from KNOWN_WARNINGS in validate.py")
    for x in gone: print("  -", x)
sys.exit(1 if errors else 0)
