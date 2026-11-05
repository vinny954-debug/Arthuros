# ArthurOS: is a mouse plugged in?
#
# Touch mode hides the pointer, because Kodi shows it after every tap. With a
# real mouse attached you still want it, so this checks every few seconds and
# sets Window(Home).Property(arthuros.mouse) to "1" while one is present.
# Variables.xml (PointerTex) reads that property.
#
# A mouse is any input device reporting relative X and Y motion (REL_X,
# REL_Y). Touchscreens report absolute positions instead, so they don't
# count; neither do keyboards or remotes. Keyboards with a built-in
# touchpad do count, which is what you'd want. Many USB touch controllers
# also register a "mouse" interface of their own: a REL device with the same
# vendor and product as a touchscreen is ignored. A wireless receiver with no
# mouse paired still looks like a mouse, which is what the override is for.
#
# Skin settings can override it: Skin.HasSetting(touch.pointer.hide) keeps the
# pointer hidden, Skin.HasSetting(touch.pointer.show) keeps it shown. The
# decision, and the device that made it, goes to kodi.log when it changes.
#
# Started from Startup (whatever window Kodi starts in), from Home (after a
# skin reload) and from Skin settings when Touch mode is turned on; only one
# copy runs, and it stops when Kodi quits, Touch mode is turned off, or
# another skin is chosen.
import xbmc
import xbmcgui

HOME = xbmcgui.Window(10000)
RUNNING = "arthuros.mousewatch"
MOUSE = "arthuros.mouse"

ABS_MT_POSITION_X = 0x35
INPUT_PROP_DIRECT = 0x1


def mask(line, prefix):
    """A /proc/bus/input/devices bitmap ("B: ABS=3 0" ...) as one integer.
    The kernel prints it in longs, highest first, without leading zero
    longs. ABS and REL fit in one 64-bit long, and in at most two 32-bit
    ones, so joining the words as 32-bit is right on both."""
    words = line[len(prefix):].split()
    try:
        if len(words) == 1:
            return int(words[0], 16)
        return sum(int(w, 16) << (32 * i) for i, w in enumerate(reversed(words)))
    except ValueError:
        return 0


def devices():
    with open("/proc/bus/input/devices") as f:
        text = f.read()
    for block in text.split("\n\n"):
        d = {"name": "?", "id": None, "rel": 0, "abs": 0, "prop": 0}
        for line in block.splitlines():
            if line.startswith("I: "):
                f = dict(w.split("=", 1) for w in line[3:].split() if "=" in w)
                if f.get("Vendor", "0000") != "0000" or f.get("Product", "0000") != "0000":
                    d["id"] = (f.get("Vendor"), f.get("Product"))
            elif line.startswith("N: Name="):
                d["name"] = line[8:].strip().strip('"')
            elif line.startswith("B: REL="):
                d["rel"] = mask(line, "B: REL=")
            elif line.startswith("B: ABS="):
                d["abs"] = mask(line, "B: ABS=")
            elif line.startswith("B: PROP="):
                d["prop"] = mask(line, "B: PROP=")
        if any(line.strip() for line in block.splitlines()):
            yield d


def mouse_present():
    """(present, why) - why names the device, for kodi.log."""
    try:
        devs = list(devices())
    except OSError:
        return True, "can't read /proc/bus/input/devices"   # can't tell: keep the pointer
    touch = {d["id"] for d in devs if d["id"] and (
        d["abs"] >> ABS_MT_POSITION_X & 1 or
        (d["prop"] >> INPUT_PROP_DIRECT & 1 and d["abs"] & 0x3 == 0x3))}
    for d in devs:
        if d["rel"] & 0x3 == 0x3:                            # REL_X | REL_Y
            if d["id"] in touch:
                continue        # the touch controller's own mouse interface
            return True, "'%s' moves like a mouse" % d["name"]
    return False, "no mouse among the input devices"


def override():
    if xbmc.getCondVisibility("Skin.HasSetting(touch.pointer.show)"):
        return True, "Skin settings: always show the pointer"
    if xbmc.getCondVisibility("Skin.HasSetting(touch.pointer.hide)"):
        return False, "Skin settings: always hide the pointer"
    return None


def main():
    if HOME.getProperty(RUNNING):
        return
    HOME.setProperty(RUNNING, "1")
    monitor = xbmc.Monitor()
    last = None
    try:
        while not monitor.abortRequested():
            if xbmc.getSkinDir() != "skin.arthuros" or \
                    not xbmc.getCondVisibility("Skin.HasSetting(touchmode)"):
                break
            now, why = override() or mouse_present()
            if now != last:
                HOME.setProperty(MOUSE, "1" if now else "")
                xbmc.log("ArthurOS mousewatch: pointer %s (%s)"
                         % ("shown" if now else "hidden", why), xbmc.LOGINFO)
                last = now
            if monitor.waitForAbort(3):
                break
    finally:
        HOME.clearProperty(RUNNING)
        HOME.clearProperty(MOUSE)


main()
