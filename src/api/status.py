#!/usr/bin/env python3
"""MComzOS Status + WiFi Management API — stdlib only, runs on localhost:9000.
Proxied by nginx at /api/. Runs as root so nmcli/ip/systemctl work without sudo."""

import json
import os
import socket
import ssl
import subprocess
import threading
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer

SERVICES = {
    "hostapd":          {"label": "WiFi Access Point",       "path": None},
    "dnsmasq":          {"label": "DHCP / DNS",              "path": None},
    "avahi-daemon":     {"label": "mDNS (.local)",           "path": None},
    "mumble-server":    {"label": "Voice & Text (Mumble)",   "path": "/mumble/"},
    "mcomz-mumble-ws":  {"label": "Mumble WebSocket Bridge", "path": None},
    "meshtasticd":      {"label": "Meshtastic",              "path": "/meshtastic/"},
    "mcomz-meshcore":   {"label": "MeshCore",                "path": "/meshcore/"},
    "kiwix-serve":      {"label": "Offline Library",         "path": "/library/"},
    "pat":              {"label": "Winlink Email (Pat)",      "path": None},
    "direwolf":         {"label": "APRS (Direwolf)",         "path": None},
    "ardopcf":          {"label": "HF Modem (ardopcf)",      "path": None},
    "mcomz-vnc":        {"label": "Remote Desktop",          "path": "/vnc/"},
    "mcomz-novnc":      {"label": "VNC WebSocket Bridge",    "path": None},
    "nginx":            {"label": "Web Server",              "path": None},
}

WIFI_IFACE = "wlan0"
AP_IP = "192.168.4.1"
ZIMS_DIR = "/var/mcomz/zims"
LIBRARY_XML = "/var/mcomz/library.xml"
_download_status = {}  # filename -> {"status": "downloading"|"done"|"error", "error": "..."}


def service_status(name):
    result = subprocess.run(
        ["systemctl", "is-active", name],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def port_open(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _nmcli_parse(line):
    """Split an nmcli --terse output line on unescaped colons."""
    fields, cur = [], []
    i = 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line) and line[i + 1] == ":":
            cur.append(":"); i += 2
        elif line[i] == ":":
            fields.append("".join(cur)); cur = []; i += 1
        else:
            cur.append(line[i]); i += 1
    fields.append("".join(cur))
    return fields


def wifi_networks(rescan=False):
    if rescan:
        subprocess.run(
            ["nmcli", "device", "wifi", "rescan", "ifname", WIFI_IFACE],
            capture_output=True, timeout=15
        )
    r = subprocess.run(
        ["nmcli", "--terse", "--fields", "IN-USE,SSID,SIGNAL,SECURITY",
         "device", "wifi", "list"],
        capture_output=True, text=True, timeout=10
    )
    best = {}  # ssid -> entry; deduplicate, keep highest signal / in-use
    for line in r.stdout.strip().split("\n"):
        if not line:
            continue
        parts = _nmcli_parse(line)
        if len(parts) < 3:
            continue
        in_use = parts[0].strip() == "*"
        ssid = parts[1]
        signal = int(parts[2]) if parts[2].isdigit() else 0
        security = bool(":".join(parts[3:]).strip()) if len(parts) > 3 else False
        if not ssid:
            continue
        entry = {"ssid": ssid, "signal": signal, "security": security, "in_use": in_use}
        if ssid not in best or in_use or signal > best[ssid]["signal"]:
            best[ssid] = entry

    networks = sorted(best.values(), key=lambda n: (-n["in_use"], -n["signal"]))
    ap_active = service_status("hostapd") == "active"
    return {"networks": networks, "ap_active": ap_active}


def wifi_known():
    r = subprocess.run(
        ["nmcli", "--terse", "--fields", "NAME,TYPE", "connection", "show"],
        capture_output=True, text=True, timeout=10
    )
    networks = []
    for line in r.stdout.strip().split("\n"):
        if not line:
            continue
        parts = _nmcli_parse(line)
        if len(parts) >= 2 and "802-11-wireless" in parts[1]:
            networks.append({"name": parts[0]})
    return {"networks": networks}


def wifi_connect(ssid, password=""):
    if not ssid:
        return {"ok": False, "error": "No SSID specified"}
    cmd = ["nmcli", "device", "wifi", "connect", ssid, "ifname", WIFI_IFACE]
    if password:
        cmd += ["password", password]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return {"ok": True}
        return {"ok": False, "error": (r.stderr or r.stdout).strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Connection timed out"}


def wifi_forget(name):
    if not name:
        return {"ok": False, "error": "No network name specified"}
    r = subprocess.run(
        ["nmcli", "connection", "delete", name],
        capture_output=True, text=True, timeout=10
    )
    return {"ok": r.returncode == 0,
            "error": r.stderr.strip() if r.returncode != 0 else ""}


def ap_start():
    """Disconnect from WiFi, release interface from NetworkManager, then start the AP.
    Explicit disconnect before releasing avoids a race where hostapd tries to bind
    to an interface still held in station mode by the driver."""
    # Graceful disconnect first — best-effort, may fail if not connected
    subprocess.run(["nmcli", "device", "disconnect", WIFI_IFACE],
                   capture_output=True, timeout=10)
    # Release from NetworkManager
    subprocess.run(["nmcli", "device", "set", WIFI_IFACE, "managed", "no"],
                   capture_output=True, timeout=10)
    # Give the driver a moment to exit station mode before hostapd takes over
    time.sleep(1)
    # Configure AP interface
    for cmd in [
        ["ip", "addr", "flush", "dev", WIFI_IFACE],
        ["ip", "addr", "add", f"{AP_IP}/24", "dev", WIFI_IFACE],
        ["ip", "link", "set", WIFI_IFACE, "up"],
    ]:
        subprocess.run(cmd, capture_output=True, timeout=10)
    # Start AP services — capture hostapd result so failures are visible in logs
    r = subprocess.run(["systemctl", "start", "hostapd"],
                       capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        # hostapd failed — the user is already offline; log the error and return it
        # so it appears in journald (mcomz-status service) for debugging
        import sys
        print(f"hostapd start failed: {r.stderr.strip()}", file=sys.stderr, flush=True)
        return {"ok": False, "error": f"hostapd failed to start: {r.stderr.strip() or 'check journalctl -u hostapd'}"}
    subprocess.run(["systemctl", "start", "dnsmasq"], capture_output=True, timeout=10)
    return {"ok": True}


def system_poweroff():
    """Initiate an immediate system shutdown. Uses Popen so the JSON response
    returns before the system actually powers off (~2 seconds later)."""
    subprocess.Popen(["shutdown", "-h", "now"])
    return {"ok": True}


def system_reboot():
    """Initiate an immediate system reboot."""
    subprocess.Popen(["shutdown", "-r", "now"])
    return {"ok": True}


def ap_stop():
    """Stop the hotspot and poll until NetworkManager reconnects (up to 30 s).

    Returns {"ok": true, "reconnected": true} on clean reconnect, or
    {"ok": true, "reconnected": false, "hint": "..."} if NM hasn't finished
    within the timeout — the user can still reach the hub at mcomz.local once
    NM reconnects on its own."""
    for cmd in [
        ["systemctl", "stop", "hostapd"],
        ["systemctl", "stop", "dnsmasq"],
        ["nmcli", "device", "set", WIFI_IFACE, "managed", "yes"],
        ["nmcli", "device", "connect", WIFI_IFACE],
    ]:
        subprocess.run(cmd, capture_output=True, timeout=10)

    # Poll until wlan0 is connected or 30 s elapse.
    for _ in range(15):
        time.sleep(2)
        r = subprocess.run(
            ["nmcli", "-t", "-f", "STATE", "device", "show", WIFI_IFACE],
            capture_output=True, text=True, timeout=5
        )
        if "connected" in r.stdout.lower():
            # Restart avahi so it re-announces mcomz.local on the rejoined interface.
            subprocess.run(["systemctl", "restart", "avahi-daemon"],
                           capture_output=True, timeout=10)
            return {"ok": True, "reconnected": True}

    return {
        "ok": True,
        "reconnected": False,
        "hint": "Open http://mcomz.local or reboot if MComzOS doesn't reappear.",
    }


def kiwix_books():
    ATOM = "http://www.w3.org/2005/Atom"
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8888/library/catalog/v2/entries?count=200", timeout=3
        ) as r:
            root = ET.fromstring(r.read())
        books = []
        for entry in root.findall(f"{{{ATOM}}}entry"):
            uid = entry.findtext(f"{{{ATOM}}}id", "").replace("urn:uuid:", "")
            title = entry.findtext(f"{{{ATOM}}}title", "") or ""
            href = ""
            for link in entry.findall(f"{{{ATOM}}}link"):
                if link.get("type") == "text/html":
                    href = link.get("href", "")
                    break
            name = href.rstrip("/").rsplit("/", 1)[-1] if href else ""
            if not title and name:
                title = name.replace("-", " ").title()
            books.append({"id": uid, "name": name, "title": title, "path": "", "size": 0})
        # Enrich with file paths and sizes from library.xml
        try:
            by_id = {b.get("id"): b.get("path", "")
                     for b in ET.parse(LIBRARY_XML).getroot().findall("book")}
            for book in books:
                path = by_id.get(book["id"], "")
                book["path"] = path
                if path and os.path.exists(path):
                    book["size"] = os.path.getsize(path)
                if not book["title"] and path:
                    book["title"] = path.rsplit("/", 1)[-1].replace(".zim", "").replace("-", " ").replace("_", " ").title()
        except Exception:
            pass
        return {"books": books}
    except Exception:
        pass
    # Fallback: parse library.xml directly (used during boot before kiwix-serve is up)
    try:
        books = []
        for b in ET.parse(LIBRARY_XML).getroot().findall("book"):
            path = b.get("path", "")
            filename = path.rsplit("/", 1)[-1].replace(".zim", "")
            name = filename.lower()
            books.append({
                "id": b.get("id", ""),
                "name": name,
                "title": b.get("title", "") or filename,
                "path": path,
                "size": os.path.getsize(path) if path and os.path.exists(path) else 0,
            })
        return {"books": books}
    except Exception as e:
        return {"books": [], "error": str(e)}


def kiwix_download(url):
    filename = url.rstrip("/").split("/")[-1].split("?")[0]
    if not filename.endswith(".zim"):
        return {"ok": False, "error": "URL must point to a .zim file"}
    dest = os.path.join(ZIMS_DIR, filename)
    if _download_status.get(filename, {}).get("status") == "downloading":
        return {"ok": False, "error": "Already downloading"}

    def _run():
        _download_status[filename] = {"status": "downloading"}
        try:
            os.makedirs(ZIMS_DIR, exist_ok=True)
            # Disable SSL cert verification: the Pi's clock may lag behind the
            # cert notBefore date on first boot (no GPS/NTP sync yet), causing
            # standard urlretrieve to raise CERTIFICATE_VERIFY_FAILED.
            _no_verify = ssl.create_default_context()
            _no_verify.check_hostname = False
            _no_verify.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(url, context=_no_verify) as r, \
                 open(dest, "wb") as f:
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            # Add to library.xml
            try:
                tree = ET.parse(LIBRARY_XML)
                root = tree.getroot()
            except Exception:
                root = ET.Element("library", version="20110515")
                tree = ET.ElementTree(root)
            ET.SubElement(root, "book", id=str(uuid.uuid4()), path=dest)
            tree.write(LIBRARY_XML, xml_declaration=True, encoding="UTF-8")
            subprocess.run(["systemctl", "restart", "kiwix-serve"],
                           capture_output=True, timeout=15)
            _download_status[filename] = {"status": "done"}
        except Exception as e:
            _download_status[filename] = {"status": "error", "error": str(e)}
            if os.path.exists(dest):
                os.remove(dest)

    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "filename": filename}


def kiwix_download_status(filename):
    return _download_status.get(filename, {"status": "idle"})


def kiwix_remove(path):
    try:
        tree = ET.parse(LIBRARY_XML)
        root = tree.getroot()
        for b in root.findall("book"):
            if b.get("path") == path:
                root.remove(b)
                break
        tree.write(LIBRARY_XML, xml_declaration=True, encoding="UTF-8")
    except Exception as e:
        return {"ok": False, "error": str(e)}
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    subprocess.run(["systemctl", "restart", "kiwix-serve"],
                   capture_output=True, timeout=15)
    return {"ok": True}


class StatusHandler(BaseHTTPRequestHandler):

    def _json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        qs = self.path[len(path) + 1:] if "?" in self.path else ""
        params = dict(kv.split("=", 1) for kv in qs.split("&") if "=" in kv)

        if path == "/api/status":
            result = {}
            for name, info in SERVICES.items():
                st = service_status(name)
                # websockify restarts on connection errors; if port 64737 is
                # listening the bridge is healthy regardless of transient state.
                if name == "mcomz-mumble-ws" and st != "active" and port_open("127.0.0.1", 64737):
                    st = "active"
                result[name] = {"status": st, **info}
            result["freedata_installed"] = os.path.exists("/usr/local/bin/freedata")
            self._json(result)
        elif path == "/api/version":
            try:
                with open("/etc/mcomzos-version") as f:
                    self._json({"version": f.read().strip()})
            except Exception:
                self._json({"version": "unknown"})
        elif path == "/api/wifi/networks":
            try:
                self._json(wifi_networks(rescan=params.get("scan") == "1"))
            except Exception as e:
                self._json({"error": str(e)}, 500)
        elif path == "/api/wifi/known":
            try:
                self._json(wifi_known())
            except Exception as e:
                self._json({"error": str(e)}, 500)
        elif path == "/api/kiwix/books":
            self._json(kiwix_books())
        elif path == "/api/kiwix/download/status":
            self._json(kiwix_download_status(params.get("file", "")))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        try:
            body = self._read_json()
        except Exception:
            body = {}

        if self.path == "/api/wifi/connect":
            self._json(wifi_connect(body.get("ssid", ""), body.get("password", "")))
        elif self.path == "/api/wifi/forget":
            self._json(wifi_forget(body.get("name", "")))
        elif self.path == "/api/wifi/ap/start":
            self._json(ap_start())
        elif self.path == "/api/wifi/ap/stop":
            self._json(ap_stop())
        elif self.path == "/api/system/poweroff":
            self._json(system_poweroff())
        elif self.path == "/api/system/reboot":
            self._json(system_reboot())
        elif self.path == "/api/kiwix/download":
            self._json(kiwix_download(body.get("url", "")))
        elif self.path == "/api/kiwix/remove":
            self._json(kiwix_remove(body.get("path", "")))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress per-request noise in journald


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9000), StatusHandler)
    server.serve_forever()
