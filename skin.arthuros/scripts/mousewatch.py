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
# touchpad do count, which is what you'd want.
#
# Started from Home (and from Skin settings when Touch mode is turned on);
# only one copy runs, and it stops when Kodi quits, Touch mode is turned off,
# or another skin is chosen.
import xbmc
import xbmcgui

HOME = xbmcgui.Window(10000)
RUNNING = "arthuros.mousewatch"
MOUSE = "arthuros.mouse"


def mouse_present():
    try:
        with open("/proc/bus/input/devices") as f:
            text = f.read()
    except OSError:
        return True          # can't tell: keep the pointer
    for block in text.split("\n\n"):
        for line in block.splitlines():
            if line.startswith("B: REL="):
                words = line[7:].split()
                if words and int(words[-1], 16) & 0x3 == 0x3:   # REL_X | REL_Y
                    return True
    return False


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
            now = mouse_present()
            if now != last:
                HOME.setProperty(MOUSE, "1" if now else "")
                last = now
            if monitor.waitForAbort(3):
                break
    finally:
        HOME.clearProperty(RUNNING)
        HOME.clearProperty(MOUSE)


main()
