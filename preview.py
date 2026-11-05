#!/usr/bin/env python3
"""Approximate renderer for skin.arthuros XML. Not Kodi - just enough to see
layout, overlaps and off-screen controls before deploying."""
import os, re, sys, glob
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

SKIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skin.arthuros")
MEDIA = os.path.join(SKIN, "media")
RES = os.environ.get("RES", "xml")            # RES=xml768 previews the 4:3 layout
W, H = 1024, (768 if RES == "xml768" else 600)

# ---------------------------------------------------------------- resources
COLORS = {}
for c in ET.parse(os.path.join(SKIN, "colors/defaults.xml")).getroot():
    COLORS[c.get("name")] = c.text.strip()

PALETTE = os.environ.get("PALETTE")
if PALETTE:
    for c in ET.parse(os.path.join(SKIN, "colors", PALETTE + ".xml")).getroot():
        COLORS[c.get("name")] = c.text.strip()

FONTS = {}
for fs in ET.parse(os.path.join(SKIN, RES, "Font.xml")).getroot():
    for f in fs.findall("font"):
        FONTS[f.findtext("name")] = (f.findtext("filename"), int(f.findtext("size")))

_fc = {}
def pilfont(name):
    fn, sz = FONTS.get(name, FONTS.get("normal", ("Tamzen8x16r.ttf", 16)))
    if (fn, sz) not in _fc:
        _fc[(fn, sz)] = ImageFont.truetype(os.path.join(SKIN, "fonts", fn), sz)
    return _fc[(fn, sz)]

STRINGS = {}
po = os.path.join(SKIN, "language/resource.language.en_gb/strings.po")
if os.path.exists(po):
    for m in re.finditer(r'msgctxt "#(\d+)"\nmsgid "(.*?)"', open(po).read()):
        STRINGS[int(m.group(1))] = m.group(2)
KODIPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "kodi", "strings.po")
if os.path.exists(KODIPO):
    for m in re.finditer(r'msgctxt "#(\d+)"\nmsgid "(.*?)"\nmsgstr', open(KODIPO, encoding="utf-8").read()):
        STRINGS.setdefault(int(m.group(1)), m.group(2))

def rgb(name):
    h = COLORS.get(name, name)
    h = h.strip().upper()
    if re.fullmatch(r"[0-9A-F]{8}", h):
        return (int(h[2:4],16), int(h[4:6],16), int(h[6:8],16), int(h[0:2],16))
    if re.fullmatch(r"[0-9A-F]{6}", h):
        return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16), 255)
    return (255, 0, 255, 255)

# ---------------------------------------------------------------- includes
INCLUDES, DEFAULTS = {}, {}
def load_includes():
    for path in glob.glob(os.path.join(SKIN, RES, "*.xml")):
        base = os.path.basename(path)
        if base in ("Font.xml",) or base.startswith("Dialog") or base.startswith("My") or base == "Home.xml":
            if base not in ("Home.xml",):
                pass
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if root.tag != "includes":
            continue
        for inc in root.findall("include"):
            n = inc.get("name")
            if n: INCLUDES[n] = inc
        for d in root.findall("default"):
            DEFAULTS[d.get("type")] = d
        for v in root.findall("variable"):
            VARS[v.get("name")] = v

XL = bool(os.environ.get("XL"))   # XL=1 previews the Extra large fontsets

# ---------------------------------------------------------------- state
# Skin strings/bools the preview pretends are set. SET="home.layout=3x3;edit.slot=5"
STATE = {}
for kv in filter(None, (os.environ.get("SET") or "").split(";")):
    k, _, v = kv.partition("=")
    STATE[k.strip().lower()] = v.strip()
VARS = {}
WINDOW = {"root": None, "focus": {}}

def infoval(e, item=None):
    """Value of an info label, or None when the preview cannot know it."""
    e = e.strip()
    m = re.fullmatch(r"Skin\.String\((.+)\)", e, re.I)
    if m: return STATE.get(resolve_text(m.group(1), item).lower(), "")
    if e.lower() == "skin.font": return "ExtraLarge" if XL else "Default"
    m = re.fullmatch(r"(?:Container\((\d+)\)\.)?ListItem\.(Property\((\w+)\)|Label|Icon)", e, re.I)
    if m:
        it = focused_item(m.group(1)) if m.group(1) else item
        if it is None: return None
        if m.group(3): return it["props"].get(m.group(3).lower(), "")
        return it["label"] if m.group(2).lower() == "label" else it["icon"]
    if e.lower() in STATE: return STATE[e.lower()]     # SET="Container.PluginName=x"
    return None

def split_args(a):
    out, depth, cur = [], 0, ""
    for ch in a:
        if ch == "," and depth == 0:
            out.append(cur); cur = ""; continue
        depth += (ch == "(") - (ch == ")")
        cur += ch
    out.append(cur)
    return out

def atom(t, item):
    """True/False, or None when unknown."""
    t = t.strip()
    neg = t.startswith("!")
    if neg: t = t[1:].strip()
    r = None
    m = re.fullmatch(r"(String\.\w+|Skin\.HasSetting)\((.*)\)", t, re.S)
    if m:
        fn, args = m.group(1).lower(), split_args(m.group(2))
        if fn == "skin.hassetting":
            r = STATE.get(args[0].strip().lower()) == "true"
        else:
            a = infoval(args[0], item)
            b = args[1].strip() if len(args) > 1 else None
            if b is not None:
                bv = infoval(b, item)
                b = bv if bv is not None else b
            if a is not None:
                if fn == "string.isempty": r = a == ""
                elif fn == "string.isequal": r = a.lower() == (b or "").lower()
                elif fn == "string.startswith": r = a.lower().startswith((b or "").lower())
                elif fn == "string.contains": r = (b or "").lower() in a.lower()
    elif t.lower() in ("true", "false"):
        r = t.lower() == "true"
    elif t.lower() in STATE:                              # SET="Player.HasMedia=true"
        r = STATE[t.lower()] == "true"
    if r is None: return None
    return (not r) if neg else r

def cond_ok(expr, item=None):
    """Evaluate a Kodi boolean: ! + | [ ]. Unknown parts count as true."""
    if not expr or not expr.strip(): return True
    toks, cur, depth = [], "", 0
    for i, ch in enumerate(expr):
        if depth == 0 and ch in "+|[]":
            if ch == "[" and cur.strip() == "!":
                toks.append("!["); cur = ""; continue
            if cur.strip(): toks.append(cur)
            toks.append(ch); cur = ""; continue
        depth += (ch == "(") - (ch == ")")
        cur += ch
    if cur.strip(): toks.append(cur)
    pos = [0]
    def peek(): return toks[pos[0]].strip() if pos[0] < len(toks) else None
    def take(): pos[0] += 1; return toks[pos[0]-1].strip()
    def prim():
        t = take()
        if t.replace(" ", "") in ("[", "!["):
            v = orx()
            if peek() == "]": take()
            return (not v) if t.startswith("!") else v
        v = atom(t, item)
        return True if v is None else v
    def andx():
        v = prim()
        while peek() == "+":
            take(); v = prim() and v
        return v
    def orx():
        v = andx()
        while peek() == "|":
            take(); v = orx() or v
        return v
    try:
        return orx()
    except Exception:
        return True

def run_onloads(root):
    """Apply a window's simple onload Skin.SetString/SetBool (first-run defaults)."""
    for ol in root.findall("onload"):
        if not cond_ok(ol.get("condition")):
            continue
        a = (ol.text or "").strip()
        m = re.fullmatch(r"Skin\.SetString\(([^,]+),(.*)\)", a)
        if m: STATE.setdefault(m.group(1).lower(), m.group(2).strip().strip('"'))
        m = re.fullmatch(r"Skin\.SetBool\((.+)\)", a)
        if m: STATE.setdefault(m.group(1).lower(), "true")

def make_item(el, item=None):
    it = {"label": "", "icon": "", "props": {}}
    it["props"] = {pr.get("name").lower(): resolve_text(pr.text or "", item) for pr in el.findall("property")}
    it["label"] = resolve_text(el.findtext("label") or "", it)
    it["icon"] = resolve_text(el.findtext("icon") or "", it)
    it["vis"] = el.findtext("visible")
    return it

def find_control(root_els, cid):
    for c in root_els:
        if c.tag != "control": continue
        if c.get("id") == cid: return c
        r = find_control(expand(c), cid)
        if r is not None: return r
    return None

def focused_item(cid):
    if cid in WINDOW["focus"]: return WINDOW["focus"][cid]
    WINDOW["focus"][cid] = None
    c = find_control(expand(WINDOW["root"]), cid) if WINDOW["root"] is not None else None
    if c is not None:
        content = next((e for e in expand(c) if e.tag == "content"), None)
        for el in (expand(content) if content is not None else []):
            if el.tag != "item": continue
            it = make_item(el)
            if cond_ok(it["vis"]):
                WINDOW["focus"][cid] = it
                break
    return WINDOW["focus"][cid]

def font_ok(cond, item=None):
    return cond_ok(cond, item)

def expand(el, params=None):
    """Return a list of resolved child elements, inlining <include>."""
    out = []
    for ch in list(el):
        if ch.tag == "include":
            if not font_ok(ch.get("condition")):
                continue
            name = ch.get("content") or (ch.text.strip() if ch.text else None)
            for k, v in (params or {}).items():
                name = name.replace("$PARAM[%s]" % k, v) if name else name
            inc = INCLUDES.get(name)
            if inc is None:
                continue
            p = {}
            for pd in inc.findall("param"):
                if pd.get("default") is not None:
                    p[pd.get("name")] = pd.get("default")
            for pu in ch.findall("param"):
                p[pu.get("name")] = pu.get("value")
            body = inc.find("definition")
            body = body if body is not None else inc
            out.extend(expand(body, p))
        else:
            out.append(subst(ch, params))
    return out

def subst(el, params):
    if not params:
        return el
    def rep(t):
        if not t: return t
        for k, v in params.items():
            t = t.replace("$PARAM[%s]" % k, v)
        return t
    new = ET.Element(el.tag, {k: rep(v) for k, v in el.attrib.items()})
    new.text = rep(el.text)
    for ch in el:
        if ch.tag == "include":
            # nested include: substitute into its param values, like Kodi does
            ni = ET.Element("include", {k: rep(v) for k, v in ch.attrib.items()})
            ni.text = rep(ch.text)
            for pp in ch.findall("param"):
                ET.SubElement(ni, "param", {k: rep(v) for k, v in pp.attrib.items()})
            new.append(ni)
        else:
            new.append(subst(ch, params))
    return new

def tint(im, colour, params=None):
    """Multiply a texture by a palette colour, like Kodi's colordiffuse."""
    if not isinstance(im, Image.Image) or not colour or "$" in colour:
        return im
    r, g, b, a = rgb(colour)
    if (r, g, b, a) == (255, 255, 255, 255):
        return im
    from PIL import ImageChops
    solid = Image.new("RGBA", im.size, (r, g, b, a))
    return ImageChops.multiply(im, solid)

# ---------------------------------------------------------------- textures
_tex = {}
def texture(path, w, h, border=0):
    if not path or path in ("-",) or "$INFO" in path or "$VAR" in path:
        return None
    f = os.path.join(MEDIA, path)
    if not os.path.exists(f):
        return "MISSING"
    key = (path, w, h, border)
    if key in _tex: return _tex[key]
    src = Image.open(f).convert("RGBA")
    w, h = max(1, int(w)), max(1, int(h))
    if border and src.width > 2*border and src.height > 2*border:
        b = border
        out = Image.new("RGBA", (w, h))
        sw, sh = src.width, src.height
        parts = {
          "tl": (0,0,b,b), "t": (b,0,sw-b,b), "tr": (sw-b,0,sw,b),
          "l": (0,b,b,sh-b), "c": (b,b,sw-b,sh-b), "r": (sw-b,b,sw,sh-b),
          "bl": (0,sh-b,b,sh), "bo": (b,sh-b,sw-b,sh), "br": (sw-b,sh-b,sw,sh)}
        cw, chh = max(1, w-2*b), max(1, h-2*b)
        out.paste(src.crop(parts["tl"]), (0,0))
        out.paste(src.crop(parts["tr"]), (w-b,0))
        out.paste(src.crop(parts["bl"]), (0,h-b))
        out.paste(src.crop(parts["br"]), (w-b,h-b))
        out.paste(src.crop(parts["t"]).resize((cw,b), Image.NEAREST), (b,0))
        out.paste(src.crop(parts["bo"]).resize((cw,b), Image.NEAREST), (b,h-b))
        out.paste(src.crop(parts["l"]).resize((b,chh), Image.NEAREST), (0,b))
        out.paste(src.crop(parts["r"]).resize((b,chh), Image.NEAREST), (w-b,b))
        out.paste(src.crop(parts["c"]).resize((cw,chh), Image.NEAREST), (b,b))
    else:
        out = src.resize((w, h), Image.NEAREST)
    _tex[key] = out
    return out

def tint(im, colour, params=None):
    """Multiply a texture by a palette colour, like Kodi's colordiffuse."""
    if not isinstance(im, Image.Image) or not colour or "$" in colour:
        return im
    r, g, b, a = rgb(colour)
    if (r, g, b, a) == (255, 255, 255, 255):
        return im
    from PIL import ImageChops
    solid = Image.new("RGBA", im.size, (r, g, b, a))
    return ImageChops.multiply(im, solid)

# ---------------------------------------------------------------- text
def resolve_text(t, item=None, depth=0):
    if not t: return ""
    t = re.sub(r"\$LOCALIZE\[(\d+)\]", lambda m: STRINGS.get(int(m.group(1)), "#"+m.group(1)), t)
    t = re.sub(r"\$NUMBER\[(\d+)\]", r"\1", t)
    def var(m):
        v = VARS.get(m.group(1))
        if v is None or depth > 6: return "<var>"
        for val in v.findall("value"):
            if cond_ok(val.get("condition"), item):
                return resolve_text(val.text or "", item, depth+1)
        return ""
    t = re.sub(r"\$VAR\[([^\]]+)\]", var, t)
    def info(m):
        a = split_args(m.group(1))
        v = infoval(a[0], item)
        if v is None: return "<"+a[0].split(".")[-1]+">"
        return (a[1] if len(a) > 1 and v else "") + v + (a[2] if len(a) > 2 and v else "")
    t = re.sub(r"\$(?:ESC)?INFO\[((?:[^\[\]]|\[[^\]]*\])+?)\]", info, t)
    return t

# ---------------------------------------------------------------- render
MISSING = set()
def num(el, tag, default=None):
    v = el.findtext(tag)
    if v is None: return default
    v = v.strip()
    try: return int(float(v))
    except ValueError: return default

def pct(el, tag, span):
    v = el.findtext(tag)
    if v is None: return None
    v = v.strip()
    try:
        return int(float(v[:-1]) * span / 100.0) if v.endswith("%") else int(float(v))
    except ValueError: return None

def geom(c, px, py, pw, ph):
    w = num(c, "width"); h = num(c, "height")
    cl = pct(c, "centerleft", pw); ct_ = pct(c, "centertop", ph)
    if cl is not None and w: return px + cl - w//2, py + ((ct_ - h//2) if (ct_ is not None and h) else (num(c,"top") or 0)), w, h
    if ct_ is not None and h:
        l0 = num(c, "left")
        if l0 is None:
            r0 = num(c, "right")
            l0 = (pw - r0 - w) if (r0 is not None and w) else 0
        return px + l0, py + ct_ - h//2, w, h
    l = num(c, "left"); t = num(c, "top")
    r = num(c, "right"); b = num(c, "bottom")
    if l is None and r is not None and w is not None: l = pw - r - w
    elif l is None and r is not None and w is None: l, w = 0, pw - r
    if l is None: l = 0
    if t is None and b is not None and h is not None: t = ph - b - h
    elif t is None and b is not None and h is None: t, h = 0, ph - b
    if t is None: t = 0
    if w is None: w = pw - l
    if h is None: h = ph - t
    return px + l, py + t, w, h

def defaulted(c, tag, fallback=None):
    v = c.findtext(tag)
    if v is not None: return v.strip()
    d = DEFAULTS.get(c.get("type"))
    if d is not None:
        v = d.findtext(tag)
        if v is not None: return v.strip()
    return fallback

def draw_label(img, c, x, y, w, h, forced=None, item=None):
    txt = resolve_text(forced if forced is not None else (c.findtext("label") or ""), item)
    if not txt: return
    fnt = pilfont(defaulted(c, "font", "normal"))
    col = rgb(defaulted(c, "textcolor", "text"))
    align = (defaulted(c, "align", "left") or "left")
    aligny = (defaulted(c, "aligny", "top") or "top")
    d = ImageDraw.Draw(img)
    bb = d.textbbox((0,0), txt, font=fnt)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    tx = x if align == "left" else (x + (w-tw)//2 if align == "center" else x + w - tw)
    ty = y + (h - fnt.size)//2 if aligny == "center" else y
    d.text((tx, ty), txt, font=fnt, fill=col[:3])

def flatten(el, item=None):
    """The control with its own <include>s (geometry, layouts) inlined."""
    if not any(ch.tag == "include" for ch in el):
        return el
    new = ET.Element(el.tag, el.attrib)
    new.text = el.text
    for ch in expand(el):
        new.append(ch)
    return new

def draw_textbox(img, c, x, y, w, h, item=None):
    """Word-wrapped, clipped to whole lines, honouring align and aligny."""
    txt = resolve_text(c.findtext("label") or "", item).replace("[CR]", "\n")
    if not txt: return
    fnt = pilfont(defaulted(c, "font", "normal"))
    col = rgb(defaulted(c, "textcolor", "text"))
    d = ImageDraw.Draw(img)
    lines = []
    for para in txt.split("\n"):
        cur = ""
        for word in para.split(" "):
            t = (cur + " " + word).strip()
            if d.textlength(t, font=fnt) <= w or not cur:
                cur = t
            else:
                lines.append(cur); cur = word
        lines.append(cur)
    lh = fnt.size
    lines = lines[:max(1, h // lh)]
    ty = y + (h - lh * len(lines)) // 2 if defaulted(c, "aligny", "top") == "center" else y
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=fnt)
        al = defaulted(c, "align", "left")
        tx = x + (w - tw) // 2 if al == "center" else (x + w - tw if al == "right" else x)
        d.text((tx, ty + i * lh), ln, font=fnt, fill=col[:3])

def render(img, els, px, py, pw, ph, depth=0, item=None):
    for c in els:
        if c.tag != "control": continue
        c = flatten(c)
        if not cond_ok(c.findtext("visible"), item): continue
        ct = c.get("type")
        x, y, w, h = geom(c, px, py, pw, ph)
        if ct == "group":
            render(img, expand(c), x, y, w, h, depth+1, item)
            continue
        if ct == "grouplist":
            horiz = (c.findtext("orientation") or "vertical").strip() == "horizontal"
            gap = int(c.findtext("itemgap") or 0)
            ox = oy = 0
            for ch in expand(c):
                if ch.tag != "control": continue
                ch = flatten(ch)
                if not cond_ok(ch.findtext("visible"), item): continue
                cw = num(ch, "width", 0) or 0
                chh = num(ch, "height", 0) or 0
                render(img, [ch], (x+ox) if horiz else x, y if horiz else (y+oy),
                       cw or w, chh or h, depth+1, item)
                if horiz: ox += cw + gap
                else: oy += chh + gap
            continue
        if ct == "image":
            tex = c.find("texture")
            path = resolve_text((tex.text or "").strip(), item) if tex is not None else ""
            if "<" in path: path = ""
            border = int(tex.get("border", 0)) if tex is not None and tex.get("border") else 0
            ar = (defaulted(c, "aspectratio", "stretch") or "stretch")
            if ar == "keep" and path and "$" not in path:
                f = os.path.join(MEDIA, path)
                if os.path.exists(f):
                    sw, sh = Image.open(f).size
                    scale = min(w / sw, h / sh)
                    nw, nh = max(1, int(sw*scale)), max(1, int(sh*scale))
                    x += (w - nw)//2; y += (h - nh)//2; w, h = nw, nh
            im = texture(path, w, h, border)
            if tex is not None and tex.get("colordiffuse"):
                im = tint(im, tex.get("colordiffuse"))
            if im == "MISSING":
                MISSING.add(path)
                ImageDraw.Draw(img).rectangle([x,y,x+w-1,y+h-1], outline=(255,0,255), width=2)
            elif im is not None:
                img.alpha_composite(im, (x, y))
            elif path:
                ImageDraw.Draw(img).rectangle([x,y,x+w-1,y+h-1], outline=(0,180,0))
            continue
        if ct in ("button", "togglebutton", "radiobutton", "spincontrolex", "edit", "sliderex"):
            t = defaulted(c, "texturenofocus", "button_up.png")
            el = c.find("texturenofocus")
            border = int(el.get("border", 2)) if el is not None and el.get("border") else 2
            im = texture(t, w, h, border)
            src = el if el is not None else (DEFAULTS.get(ct).find("texturenofocus") if DEFAULTS.get(ct) is not None else None)
            if src is not None and src.get("colordiffuse"):
                im = tint(im, src.get("colordiffuse"))
            if isinstance(im, Image.Image): img.alpha_composite(im, (x, y))
            if ct == "radiobutton":
                rt = c.find("textureradiooffnofocus")
                rpath = (rt.text or "").strip() if rt is not None else defaulted(c, "textureradiooffnofocus", "")
                rw = int(defaulted(c, "radiowidth", "16") or 16); rh = int(defaulted(c, "radioheight", "16") or 16)
                rpx = defaulted(c, "radioposx", None); rpy = defaulted(c, "radioposy", None)
                rx = x + int(rpx) if rpx not in (None, "", "0") else x + w - 8 - rw
                ry = y + int(rpy) if rpy not in (None, "", "0") else y + (h - rh)//2
                ri = texture(rpath, rw, rh, 0)
                if rt is not None and rt.get("colordiffuse"): ri = tint(ri, rt.get("colordiffuse"))
                if isinstance(ri, Image.Image): img.alpha_composite(ri, (rx, ry))
            off = int(defaulted(c, "textoffsetx", "10") or 10)
            al = defaulted(c, "align", "center")
            draw_label(img, c, x+off, y, w-2*off, h, item=item)
            continue
        if ct == "label":
            draw_label(img, c, x, y, w, h, item=item); continue
        if ct in ("scrollbar",):
            im = texture("sb_back.png", w, h, 2)
            if isinstance(im, Image.Image): img.alpha_composite(im, (x, y))
            im = texture("sb_nub.png", w, max(24, h//4), 2)
            if isinstance(im, Image.Image): img.alpha_composite(im, (x, y))
            continue
        if ct in ("list", "panel", "fixedlist", "wraplist"):
            render_list(img, c, x, y, w, h); continue
        if ct == "textbox":
            draw_textbox(img, c, x, y, w, h, item); continue
        ImageDraw.Draw(img).rectangle([x,y,x+w-1,y+h-1], outline=(255,140,0))
        ImageDraw.Draw(img).text((x+3,y+3), ct or "?", font=pilfont("tiny"), fill=(200,80,0))

def render_list(img, c, x, y, w, h):
    kids = expand(c)
    content = next((e for e in kids if e.tag == "content"), None)
    items = [make_item(e) for e in (expand(content) if content is not None else []) if e.tag == "item"]
    items = [it for it in items if cond_ok(it["vis"])]
    def pick(tag, it):
        return next((l for l in kids if l.tag == tag and cond_ok(l.get("condition"), it)), None)
    probe = items[0] if items else None
    il = pick("itemlayout", probe)
    if il is None:
        ImageDraw.Draw(img).rectangle([x,y,x+w-1,y+h-1], outline=(255,0,0)); return
    iw = int(il.get("width", w)); ih = int(il.get("height", 24))
    n_demo = 14 if content is None else len(items)
    cols = max(1, w // iw) if iw < w else 1
    cx = cy = 0
    for i in range(min(n_demo, 60)):
        it = items[i] if i < len(items) else None
        ix, iy = x + cx*iw, y + cy*ih
        if iy + ih > y + h: break
        lay = (pick("focusedlayout", it) if i == 0 else None) or pick("itemlayout", it)
        sub = ET.Element("control"); sub.set("type", "group")
        for e in expand(lay): sub.append(e)
        render(img, expand(sub), ix, iy, iw, ih, 1, it)
        cx += 1
        if cx >= cols: cx, cy = 0, cy+1

def render_window(path, out):
    load_includes()
    root = ET.parse(path).getroot()
    run_onloads(root)
    # every window sees the desktop as it is on first run
    run_onloads(ET.parse(os.path.join(SKIN, RES, "Home.xml")).getroot())
    img = Image.new("RGBA", (W, H), rgb("desktop"))
    ctrls = root.find("controls")
    WINDOW["root"] = ctrls
    if ctrls is None:
        print("no <controls> in", path); return
    render(img, expand(ctrls), 0, 0, W, H)
    img.convert("RGB").save(out)
    if MISSING:
        print("MISSING TEXTURES:", ", ".join(sorted(MISSING)))
    print("wrote", out)

if __name__ == "__main__":
    render_window(sys.argv[1], sys.argv[2])
