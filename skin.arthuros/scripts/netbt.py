# -*- coding: utf-8 -*-
"""ArthurOS: Network & Bluetooth settings for Kodi on plain Linux.

Run with:
    RunScript(special://skin/scripts/netbt.py)           main menu
    RunScript(special://skin/scripts/netbt.py,wifi)      straight to Wi-Fi
    RunScript(special://skin/scripts/netbt.py,bt)        straight to Bluetooth
    RunScript(special://skin/scripts/netbt.py,audio)     audio output picker

Uses NetworkManager (nmcli) and BlueZ (bluetoothctl), so nothing extra has
to be installed on Raspberry Pi OS. NetworkManager's default polkit rules
only let an active local login session change networks. Kodi run as a
systemd service has no such session, so the user it runs as needs a polkit
rule (/etc/polkit-1/rules.d/50-arthuros-nm.rules, which install-arthuros.sh
offers to add).
"""

import json
import os
import pwd
import re
import select
import shutil
import subprocess
import sys
import time

import xbmc
import xbmcgui

HEADING = "Network & Bluetooth"
WIFI_HEADING = "Wi-Fi"
BT_HEADING = "Bluetooth"
AUDIO_HEADING = "Audio output"

ENV = dict(os.environ, LC_ALL="C", LANG="C")
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|[\x01\x02\r]")
MAC = re.compile(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$", re.I)

dialog = xbmcgui.Dialog()


# ---------------------------------------------------------------- helpers

def log(msg):
    xbmc.log("ArthurOS netbt: %s" % msg, xbmc.LOGINFO)


def run(args, timeout=30):
    """Run a command; return (returncode, stdout, stderr). Never raises."""
    log("run: %s" % " ".join(a if "password" not in prev else "****"
                             for prev, a in zip([""] + args, args)))
    try:
        p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           env=ENV, timeout=timeout)
        out = p.stdout.decode("utf-8", "replace")
        err = p.stderr.decode("utf-8", "replace")
        return p.returncode, ANSI.sub("", out), ANSI.sub("", err)
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    except OSError as e:
        return 127, "", str(e)


def split_terse(line):
    """Split one line of `nmcli -t` output: ':' separates, '\\:' and '\\\\' escape."""
    fields, cur, i = [], [], 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line):
            cur.append(line[i + 1])
            i += 2
            continue
        if c == ":":
            fields.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    fields.append("".join(cur))
    return fields


def busy(on):
    xbmc.executebuiltin("ActivateWindow(busydialognocancel)" if on
                        else "Dialog.Close(busydialognocancel)")


def notify(msg, ms=4000):
    dialog.notification(HEADING, msg, xbmcgui.NOTIFICATION_INFO, ms)


def first_line(text):
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


# ---------------------------------------------------------------- Wi-Fi

NM_DENIED = ("not authorized", "insufficient privileges", "permission denied")


def nm_denied(err):
    e = err.lower()
    return any(s in e for s in NM_DENIED)


def show_nm_denied():
    try:
        user = pwd.getpwuid(os.getuid()).pw_name   # who Kodi really runs as
    except Exception:
        user = "the Kodi user"
    dialog.ok(WIFI_HEADING,
              "NetworkManager refused the change: user '%s' (Kodi) isn't "
              "allowed to manage networks.[CR][CR]Fix it once: run "
              "install-arthuros.sh again and let it add the polkit rule "
              "/etc/polkit-1/rules.d/50-arthuros-nm.rules for '%s', "
              "then try again." % (user, user))


def wifi_iface():
    rc, out, _ = run(["nmcli", "-t", "-f", "DEVICE,TYPE", "device", "status"])
    for line in out.splitlines():
        f = split_terse(line)
        if len(f) >= 2 and f[1] == "wifi":
            return f[0]
    return None


def wifi_radio_on():
    rc, out, _ = run(["nmcli", "radio", "wifi"])
    return out.strip() == "enabled"


def wifi_status(iface):
    """Return (state, connection name) for the Wi-Fi device."""
    rc, out, _ = run(["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION",
                      "device", "status"])
    for line in out.splitlines():
        f = split_terse(line)
        if len(f) >= 3 and f[0] == iface:
            return f[1], f[2]
    return "unavailable", ""


def wifi_scan(iface):
    """Return a list of networks, strongest first, one entry per SSID."""
    base = ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY",
            "device", "wifi", "list", "ifname", iface]
    rc, out, err = run(base + ["--rescan", "yes"], timeout=40)
    if rc != 0:  # e.g. "Scanning not allowed immediately following previous scan"
        rc, out, err = run(base + ["--rescan", "no"], timeout=20)
    nets = {}
    for line in out.splitlines():
        f = split_terse(line)
        if len(f) < 4 or not f[1]:
            continue  # hidden networks have no SSID
        try:
            signal = int(f[2])
        except ValueError:
            signal = 0
        net = {"ssid": f[1], "signal": signal,
               "secure": f[3] not in ("", "--"),
               "security": f[3], "active": f[0].strip() == "*"}
        old = nets.get(net["ssid"])
        if old is None or net["active"] or (signal > old["signal"] and not old["active"]):
            nets[net["ssid"]] = net
    return sorted(nets.values(), key=lambda n: (not n["active"], -n["signal"]))


def wifi_saved():
    """Return {ssid: connection name} for saved Wi-Fi profiles."""
    rc, out, _ = run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"])
    names = [split_terse(l) for l in out.splitlines()]
    names = [f[0] for f in names if len(f) >= 2 and f[1] == "802-11-wireless"]
    saved = {}
    for name in names:
        rc, out, _ = run(["nmcli", "-t", "-g", "802-11-wireless.ssid",
                          "connection", "show", "id", name])
        ssid = out.strip() or name
        saved[ssid] = name
    return saved


def bars(signal):
    n = 4 if signal >= 75 else 3 if signal >= 50 else 2 if signal >= 25 else 1
    return "|" * n + "." * (4 - n)


def wifi_explain(err):
    e = err.lower()
    if "secrets were required" in e or "802-1x" in e or "psk" in e and "invalid" in e:
        return "The password was wrong, or the network rejected it."
    if "no network with ssid" in e:
        return "That network isn't in range any more."
    if "timed out" in e or "timeout" in e:
        return "The network didn't respond in time."
    return first_line(err) or "Unknown error."


def wifi_connect(iface, net, saved):
    ssid = net["ssid"]
    if ssid in saved:
        busy(True)
        rc, out, err = run(["nmcli", "--wait", "30", "connection", "up",
                            "id", saved[ssid], "ifname", iface], timeout=45)
        busy(False)
        if rc == 0:
            notify("Connected to %s" % ssid)
            return True
        if nm_denied(err):
            show_nm_denied()
            return False
        if not net.get("secure"):
            dialog.ok(WIFI_HEADING, "Couldn't connect to %s.[CR]%s" % (ssid, wifi_explain(err)))
            return False
        # Saved password may be stale: offer to enter it again.
        if not dialog.yesno(
                WIFI_HEADING, "Couldn't connect to %s.[CR]%s[CR][CR]"
                "Enter the password again?" % (ssid, wifi_explain(err))):
            return False
        run(["nmcli", "connection", "delete", "id", saved[ssid]])
        del saved[ssid]

    args = ["nmcli", "--wait", "30", "device", "wifi", "connect", ssid,
            "ifname", iface]
    if net.get("hidden"):
        args += ["hidden", "yes"]
    if net.get("secure", True):
        pw = dialog.input("Password for %s" % ssid,
                          type=xbmcgui.INPUT_ALPHANUM,
                          option=xbmcgui.ALPHANUM_HIDE_INPUT)
        if not pw:
            return False
        args[7:7] = ["password", pw]  # after the SSID, before "ifname"

    busy(True)
    rc, out, err = run(args, timeout=45)
    busy(False)
    if rc == 0:
        notify("Connected to %s" % ssid)
        return True
    # A failed attempt can leave a half-made profile behind; remove it so
    # the next try asks for the password afresh.
    run(["nmcli", "connection", "delete", "id", ssid])
    if nm_denied(err):
        show_nm_denied()
    else:
        dialog.ok(WIFI_HEADING, "Couldn't connect to %s.[CR]%s" % (ssid, wifi_explain(err)))
    return False


def wifi_forget(saved):
    if not saved:
        dialog.ok(WIFI_HEADING, "No Wi-Fi networks are saved.")
        return
    ssids = sorted(saved, key=str.lower)
    i = dialog.select("Forget which network?", ssids)
    if i < 0:
        return
    if not dialog.yesno(WIFI_HEADING, "Forget %s?[CR]You'll need its password "
                        "to join it again." % ssids[i]):
        return
    rc, out, err = run(["nmcli", "connection", "delete", "id", saved[ssids[i]]])
    if rc == 0:
        notify("Forgot %s" % ssids[i])
    elif nm_denied(err):
        show_nm_denied()
    else:
        dialog.ok(WIFI_HEADING, first_line(err))


def wifi_menu():
    if not shutil.which("nmcli"):
        dialog.ok(WIFI_HEADING, "NetworkManager (nmcli) isn't installed on this system.")
        return
    iface = wifi_iface()
    if not iface:
        dialog.ok(WIFI_HEADING, "No Wi-Fi adapter was found.")
        return
    while True:
        if not wifi_radio_on():
            if not dialog.yesno(WIFI_HEADING, "Wi-Fi is turned off. Turn it on?"):
                return
            rc, out, err = run(["nmcli", "radio", "wifi", "on"])
            if rc != 0:
                if nm_denied(err):
                    show_nm_denied()
                else:
                    dialog.ok(WIFI_HEADING, "Couldn't turn Wi-Fi on.[CR]%s[CR][CR]"
                              "If it stays off, it may be blocked: run "
                              "sudo rfkill unblock wifi over SSH." % first_line(err))
                return
            xbmc.sleep(3000)

        busy(True)
        state, conn = wifi_status(iface)
        nets = wifi_scan(iface)
        saved = wifi_saved()
        busy(False)

        items, actions = [], []
        for n in nets:
            label = "%s  %s" % (bars(n["signal"]), n["ssid"])
            tags = []
            if n["active"]:
                tags.append("connected")
            elif n["ssid"] in saved:
                tags.append("saved")
            if n["secure"]:
                tags.append("secured")
            if tags:
                label += "   (" + ", ".join(tags) + ")"
            items.append(label)
            actions.append(("net", n))
        items += ["Other network...", "Forget a saved network...",
                  "Refresh", "Turn Wi-Fi off"]
        actions += [("hidden", None), ("forget", None), ("refresh", None), ("off", None)]

        if state.startswith("connected"):
            title = "Wi-Fi: connected to %s" % conn
        else:
            title = "Wi-Fi: not connected"
        i = dialog.select(title, items)
        if i < 0:
            return
        kind, net = actions[i]
        if kind == "net":
            if net["active"]:
                if dialog.yesno(WIFI_HEADING, "Disconnect from %s?" % net["ssid"]):
                    run(["nmcli", "device", "disconnect", iface])
                continue
            wifi_connect(iface, net, saved)
        elif kind == "hidden":
            ssid = dialog.input("Network name (SSID)", type=xbmcgui.INPUT_ALPHANUM)
            if ssid:
                secure = dialog.yesno(WIFI_HEADING, "Does %s need a password?" % ssid)
                wifi_connect(iface, {"ssid": ssid, "secure": secure, "hidden": True}, saved)
        elif kind == "forget":
            wifi_forget(saved)
        elif kind == "off":
            if dialog.yesno(WIFI_HEADING, "Turn Wi-Fi off?[CR]If this box has no "
                            "network cable, it will go offline."):
                run(["nmcli", "radio", "wifi", "off"])
                return


# ---------------------------------------------------------------- Bluetooth

def bt_devices(which=None):
    """Return [(mac, name)]. which: None for all known, or 'Paired'."""
    args = ["bluetoothctl", "devices"] + ([which] if which else [])
    rc, out, err = run(args, timeout=15)
    if which and rc != 0:  # older BlueZ without the filter
        return [d for d in bt_devices() if bt_info(d[0]).get("paired") == "yes"]
    devs = []
    for line in out.splitlines():
        parts = line.strip().split(" ", 2)
        if len(parts) >= 2 and parts[0] == "Device" and MAC.match(parts[1]):
            devs.append((parts[1].upper(), parts[2] if len(parts) > 2 else parts[1]))
    return devs


def bt_info(mac):
    rc, out, _ = run(["bluetoothctl", "info", mac], timeout=15)
    info = {}
    for line in out.splitlines():
        if ":" in line and line.startswith(("\t", " ")):
            k, v = line.strip().split(":", 1)
            k = k.strip().lower()
            if k not in info:
                info[k] = v.strip()
    return info


def bt_powered():
    rc, out, err = run(["bluetoothctl", "show"], timeout=15)
    if rc != 0 or "No default controller" in out + err:
        return None
    return "Powered: yes" in out


def bt_explain(err):
    e = err.lower()
    if "profile-unavailable" in e:
        return ("This device needs software the system doesn't have running "
                "(for speakers and headphones: PipeWire's Bluetooth support).")
    if "page-timeout" in e or "host is down" in e:
        return ("The device didn't answer. Make sure it's switched on, nearby, "
                "and not connected to a phone or computer.")
    if "authentication" in e or "auth" in e and "fail" in e:
        return "Pairing was refused. Put the device back in pairing mode and try again."
    if "already exists" in e:
        return "It's already paired."
    if "inprogress" in e or "in progress" in e:
        return "Bluetooth is busy. Wait a moment and try again."
    if "blocked" in e or "not ready" in e:
        return ("Bluetooth is switched off at system level. Over SSH, run "
                "sudo rfkill unblock bluetooth.")
    return first_line(err) or "Unknown error."


def bt_cmd(args, timeout=30):
    rc, out, err = run(["bluetoothctl"] + args, timeout=timeout)
    text = out + "\n" + err
    ok = rc == 0 and not re.search(r"Failed|not available|Error", text)
    # bluetoothctl sometimes exits 0 after printing a failure.
    for l in text.splitlines():
        if "successful" in l.lower() or "changing" in l.lower() and "succeeded" in l.lower():
            ok = True
    return ok, text


def bt_connect(mac, name):
    busy(True)
    ok, text = bt_cmd(["connect", mac], timeout=40)
    busy(False)
    if ok:
        notify("Connected to %s" % name)
    else:
        dialog.ok(BT_HEADING, "Couldn't connect to %s.[CR]%s" % (name, bt_explain(text)))
    return ok


def bt_pair(mac, name):
    """Pair with an agent so passkeys and PINs can be shown or typed."""
    try:
        p = subprocess.Popen(["bluetoothctl"], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             env=ENV)
    except OSError as e:
        dialog.ok(BT_HEADING, str(e))
        return False
    fd = p.stdout.fileno()
    os.set_blocking(fd, False)

    def send(cmd):
        try:
            p.stdin.write((cmd + "\n").encode())
            p.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    send("agent KeyboardDisplay")
    send("default-agent")
    send("pair %s" % mac)

    prog = xbmcgui.DialogProgress()
    prog.create(BT_HEADING, "Pairing with %s..." % name)
    buf, pos, result, error = "", 0, None, ""
    deadline = time.time() + 60
    try:
        while result is None and time.time() < deadline:
            if prog.iscanceled():
                result, error = False, "cancelled"
                break
            r, _, _ = select.select([fd], [], [], 0.3)
            if r:
                try:
                    chunk = os.read(fd, 4096)
                except BlockingIOError:
                    chunk = b""
                if not chunk and p.poll() is not None:
                    break
                buf += ANSI.sub("", chunk.decode("utf-8", "replace"))
            while "\n" in buf[pos:] or re.search(r"\(yes/no\):\s*$|PIN code:\s*$|passkey[^\n]*:\s*$", buf[pos:], re.I):
                nl = buf.find("\n", pos)
                line = buf[pos:nl] if nl >= 0 else buf[pos:]
                pos = nl + 1 if nl >= 0 else len(buf)
                low = line.lower()
                m = re.search(r"passkey:?\s*(\d{4,6})", line, re.I)
                if "confirm passkey" in low and m:
                    prog.close()
                    yes = dialog.yesno(BT_HEADING, "Does %s show this number?[CR][CR]"
                                       "[B]%s[/B]" % (name, m.group(1)))
                    send("yes" if yes else "no")
                    prog.create(BT_HEADING, "Pairing with %s..." % name)
                elif m and "passkey" in low:
                    prog.update(50, "Type [B]%s[/B] on %s, then press Enter."
                                % (m.group(1), name))
                elif "enter pin code" in low or "enter passkey" in low:
                    prog.close()
                    pin = dialog.input("PIN for %s" % name, type=xbmcgui.INPUT_NUMERIC)
                    send(pin or "0000")
                    prog.create(BT_HEADING, "Pairing with %s..." % name)
                elif "authorize service" in low or "request authorization" in low:
                    send("yes")
                elif "pairing successful" in low:
                    result = True
                elif "failed to pair" in low or "not available" in low:
                    result, error = False, line
    finally:
        prog.close()
        send("quit")
        try:
            p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill()

    if result:
        return True
    if error == "cancelled":
        return False
    if result is None and not error:
        error = "timed out"
    dialog.ok(BT_HEADING, "Couldn't pair with %s.[CR]%s" % (name, bt_explain(error)))
    return False


def bt_scan():
    prog = xbmcgui.DialogProgress()
    prog.create(BT_HEADING, "Looking for devices. Put yours in pairing mode now.")
    try:
        p = subprocess.Popen(["bluetoothctl", "--timeout", "15", "scan", "on"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=ENV)
    except OSError as e:
        prog.close()
        dialog.ok(BT_HEADING, str(e))
        return
    start = time.time()
    while p.poll() is None:
        pct = min(100, int((time.time() - start) * 100 / 15))
        prog.update(pct)
        if prog.iscanceled():
            p.terminate()
            break
        xbmc.sleep(250)
    cancelled = prog.iscanceled()
    prog.close()
    if cancelled:
        return

    paired = {m for m, _ in bt_devices("Paired")}
    found = [(m, n) for m, n in bt_devices() if m not in paired]
    # Devices that only advertise an address are rarely what people want.
    named = [d for d in found if d[1].replace("-", ":").upper() != d[0]]
    unnamed = [d for d in found if d not in named]
    found = sorted(named, key=lambda d: d[1].lower()) + unnamed
    if not found:
        dialog.ok(BT_HEADING, "No new devices found. Check yours is in pairing "
                  "mode and close to this box, then try again.")
        return
    i = dialog.select("Pair which device?",
                      ["%s  (%s)" % (n, m) if (m, n) in named else m for m, n in found])
    if i < 0:
        return
    mac, name = found[i]
    if not bt_pair(mac, name):
        return
    bt_cmd(["trust", mac])
    if bt_connect(mac, name) and bt_info(mac).get("icon", "").startswith("audio"):
        if dialog.yesno(BT_HEADING, "%s is connected. Play Kodi's sound through it?" % name):
            audio_menu(prefer=name)


def bt_device_menu(mac, name, info):
    connected = info.get("connected") == "yes"
    items = ["Disconnect" if connected else "Connect", "Forget this device"]
    i = dialog.select(name, items)
    if i == 0:
        if connected:
            ok, text = bt_cmd(["disconnect", mac])
            notify(("Disconnected %s" % name) if ok else bt_explain(text))
        else:
            if bt_connect(mac, name) and info.get("icon", "").startswith("audio"):
                if dialog.yesno(BT_HEADING, "Play Kodi's sound through %s?" % name):
                    audio_menu(prefer=name)
    elif i == 1:
        if dialog.yesno(BT_HEADING, "Forget %s?[CR]To use it again you'll need "
                        "to pair it again." % name):
            ok, text = bt_cmd(["remove", mac])
            notify(("Forgot %s" % name) if ok else bt_explain(text))


def bt_menu():
    if not shutil.which("bluetoothctl"):
        dialog.ok(BT_HEADING, "BlueZ (bluetoothctl) isn't installed on this system.")
        return
    while True:
        powered = bt_powered()
        if powered is None:
            dialog.ok(BT_HEADING, "No Bluetooth adapter was found, or the "
                      "Bluetooth service isn't running.")
            return
        if not powered:
            if not dialog.yesno(BT_HEADING, "Bluetooth is turned off. Turn it on?"):
                return
            ok, text = bt_cmd(["power", "on"])
            if not ok:
                dialog.ok(BT_HEADING, "Couldn't turn Bluetooth on.[CR]%s" % bt_explain(text))
                return
            continue

        busy(True)
        devs = []
        for mac, name in bt_devices("Paired"):
            info = bt_info(mac)
            devs.append((mac, info.get("alias") or name, info))
        busy(False)
        devs.sort(key=lambda d: (d[2].get("connected") != "yes", d[1].lower()))

        items = ["%s   (%s)" % (n, "connected" if i.get("connected") == "yes"
                                else "not connected") for _, n, i in devs]
        items += ["Pair a new device...", "Turn Bluetooth off"]
        n_conn = sum(1 for d in devs if d[2].get("connected") == "yes")
        title = "Bluetooth: %d paired, %d connected" % (len(devs), n_conn)
        i = dialog.select(title, items)
        if i < 0:
            return
        if i < len(devs):
            bt_device_menu(*devs[i])
        elif i == len(devs):
            bt_scan()
        else:
            if dialog.yesno(BT_HEADING, "Turn Bluetooth off?[CR]Bluetooth "
                            "keyboards and speakers will disconnect."):
                bt_cmd(["power", "off"])
                return


# ---------------------------------------------------------------- audio

def jsonrpc(method, params):
    req = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    return json.loads(xbmc.executeJSONRPC(json.dumps(req)))


def audio_menu(prefer=None):
    res = jsonrpc("Settings.GetSettings",
                  {"level": "expert", "filter": {"section": "system", "category": "audio"}})
    setting = None
    for s in res.get("result", {}).get("settings", []):
        if s.get("id") == "audiooutput.audiodevice":
            setting = s
            break
    if not setting or not setting.get("options"):
        xbmc.executebuiltin("ActivateWindow(systemsettings)")
        return
    opts = setting["options"]
    current = setting.get("value")
    labels = [("[B]%s[/B]  (in use)" % o["label"]) if o["value"] == current else o["label"]
              for o in opts]
    pre = 0
    if prefer:
        for n, o in enumerate(opts):
            if prefer.lower() in o["label"].lower():
                pre = n
                break
    else:
        for n, o in enumerate(opts):
            if o["value"] == current:
                pre = n
    i = dialog.select("Play sound through", labels, preselect=pre)
    if i < 0 or opts[i]["value"] == current:
        return
    jsonrpc("Settings.SetSettingValue",
            {"setting": "audiooutput.audiodevice", "value": opts[i]["value"]})
    notify("Sound now plays through %s" % opts[i]["label"])


# ---------------------------------------------------------------- main

def summary():
    wifi = "Wi-Fi"
    if shutil.which("nmcli"):
        iface = wifi_iface()
        if not iface:
            wifi += ": no adapter"
        elif not wifi_radio_on():
            wifi += ": off"
        else:
            state, conn = wifi_status(iface)
            wifi += (": connected to %s" % conn) if state.startswith("connected") \
                else ": not connected"
    bt = "Bluetooth"
    if shutil.which("bluetoothctl"):
        powered = bt_powered()
        if powered is None:
            bt += ": no adapter"
        elif not powered:
            bt += ": off"
        else:
            devs = bt_devices("Paired")
            n_conn = sum(1 for m, _ in devs if bt_info(m).get("connected") == "yes")
            bt += ": %d paired, %d connected" % (len(devs), n_conn)
    return [wifi, bt, "Audio output..."]


def main(arg):
    if arg == "wifi":
        return wifi_menu()
    if arg == "bt":
        return bt_menu()
    if arg == "audio":
        return audio_menu()
    while True:
        busy(True)
        items = summary()
        busy(False)
        i = dialog.select(HEADING, items)
        if i < 0:
            return
        [wifi_menu, bt_menu, audio_menu][i]()


if __name__ == "__main__":
    try:
        main(sys.argv[1].lower() if len(sys.argv) > 1 else "")
    finally:
        busy(False)
