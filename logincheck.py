#!/usr/bin/env python3
"""The login screen must not be a way round the login.

Kodi runs the login screen as the master profile, and skin onclicks are not
filtered by CGUIWindowLoginScreen::OnAction; CGUIWindowManager::
ActivateWindow_Internal only checks CheckMenuLock, which does not cover Home.
So no control on the login screen, or in a dialog it can lead to - the power
menu (DialogButtonMenu), and the keyboard / numeric pad Kodi opens for a
locked profile's password or the master code - may run ActivateWindow()
for anything but the power menu, unless that action (or its control) is
conditional on the login screen not being visible.

Includes are expanded the way Kodi does (with $PARAM substitution, so
Win_Boxes_$PARAM[boxes] resolves), for xml/ and xml768/.

DialogConfirm.xml and DialogSelect.xml (hand-maintained, also reachable:
the incorrect-password OK box, the profile choice) are checked too. They
take their title-bar boxes from Win_Boxes_dialog in Includes_Chrome.xml,
whose 9901 box still runs an unguarded ActivateWindow(Home); until that
include guards it, those two are listed in KNOWN (reported, not failed).
Any other hole, or a known one in a new place, fails.
"""
import copy, glob, os, re, sys
from lxml import etree

S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skin.arthuros")
WINDOWS = ["LoginScreen", "DialogButtonMenu", "DialogKeyboard", "DialogNumeric",
           "DialogConfirm", "DialogSelect"]
GUARD = "!Window.IsVisible(loginscreen)"
ALLOWED = {"shutdownmenu"}
# Win_Boxes_dialog's 9901 (Includes_Chrome.xml, another package's file):
# fix there with <onclick condition="!Window.IsVisible(loginscreen)"> and
# the same in 9901's <visible>, then empty this set.
KNOWN = {f"{d}/{w}.xml: <onclick>ActivateWindow(Home)</onclick> is reachable from the login screen"
         for d in ("xml", "xml768") for w in ("DialogConfirm", "DialogSelect")}

def definitions(d):
    defs = {}
    for p in glob.glob(os.path.join(S, d, "Includes*.xml")):
        for inc in etree.parse(p).getroot().iter("include"):
            if inc.get("name"):
                defs[inc.get("name")] = inc
    return defs

def subst(el, params):
    pat = re.compile(r"\$PARAM\[(\w+)\]")
    f = lambda t: pat.sub(lambda m: params.get(m.group(1), ""), t) if t else t
    for e in el.iter():
        if not isinstance(e.tag, str):
            continue
        e.text = f(e.text); e.tail = f(e.tail)
        for k, v in e.attrib.items():
            e.set(k, f(v))

def expand(el, defs, depth=0):
    if depth > 40:
        raise SystemExit("include recursion")
    for inc in list(el.iter("include")):
        if inc.getparent() is None or inc.get("file"):
            continue
        name = inc.get("content") or (inc.text or "").strip()
        d = defs.get(name)
        if d is None:
            continue
        params = {p.get("name"): p.get("default", "") for p in d.findall("param")}
        params.update({p.get("name"): p.get("value", "") for p in inc.findall("param")})
        body = d.find("definition")
        body = body if body is not None else d
        kids = [copy.deepcopy(k) for k in body if isinstance(k.tag, str) and k.tag != "param"]
        holder = etree.Element("x")
        for k in kids:
            holder.append(k)
        subst(holder, params)
        expand(holder, defs, depth + 1)
        parent = inc.getparent()
        i = list(parent).index(inc)
        parent.remove(inc)
        for k in reversed(list(holder)):
            parent.insert(i, k)

def guarded(action):
    if GUARD.lower() in (action.get("condition") or "").replace(" ", "").lower():
        return True
    c = action.getparent()
    while c is not None:
        if c.tag == "control":
            for v in c.findall("visible"):
                if GUARD.lower() in (v.text or "").replace(" ", "").lower():
                    return True
        c = c.getparent()
    return False

bad = []
for d in ("xml", "xml768"):
    defs = definitions(d)
    for w in WINDOWS:
        p = os.path.join(S, d, w + ".xml")
        root = etree.parse(p).getroot()
        expand(root, defs)
        for a in root.iter():
            if not isinstance(a.tag, str) or not a.tag.startswith("on"):
                continue
            for m in re.finditer(r"(?:ActivateWindow|ReplaceWindow)\(\s*([^,)]+)", a.text or "", re.I):
                if m.group(1).strip().lower() in ALLOWED or guarded(a):
                    continue
                bad.append(f"{d}/{w}.xml: <{a.tag}>{a.text.strip()}</{a.tag}> is reachable from the login screen")
known = [b for b in bad if b in KNOWN]
bad = [b for b in bad if b not in KNOWN]
for k in sorted(set(known)):
    print("known (Win_Boxes_dialog 9901, see KNOWN):", k)
for k in sorted(KNOWN - set(known)):
    print("fixed, remove from KNOWN in logincheck.py:", k)
if bad:
    print("\n".join(bad))
    sys.exit(1)
print(f"logincheck: {len(WINDOWS)} windows x 2 layouts, nothing else gets past the login screen")
