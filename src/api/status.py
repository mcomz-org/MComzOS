#!/usr/bin/env python3
"""MComzOS Status + WiFi Management API — stdlib only, runs on localhost:9000.
Proxied by nginx at /api/. Runs as root so nmcli/ip/systemctl work without sudo."""

import json
import subprocess
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


def service_status(name):
    result = subprocess.run(
        ["systemctl", "is-active", name],
        capture_output=True, text=True
    )
    return result.stdout.strip()


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
    """Mirror the mcomz-apmode-fallback activation sequence."""
    for cmd in [
        ["nmcli", "device", "set", WIFI_IFACE, "managed", "no"],
        ["ip", "addr", "flush", "dev", WIFI_IFACE],
        ["ip", "addr", "add", f"{AP_IP}/24", "dev", WIFI_IFACE],
        ["ip", "link", "set", WIFI_IFACE, "up"],
        ["systemctl", "start", "hostapd"],
        ["systemctl", "start", "dnsmasq"],
    ]:
        subprocess.run(cmd, capture_output=True, timeout=10)
    return {"ok": True}


def ap_stop():
    """Stop the hotspot and let NetworkManager reconnect."""
    for cmd in [
        ["systemctl", "stop", "hostapd"],
        ["systemctl", "stop", "dnsmasq"],
        ["nmcli", "device", "set", WIFI_IFACE, "managed", "yes"],
        ["nmcli", "device", "connect", WIFI_IFACE],
    ]:
        subprocess.run(cmd, capture_output=True, timeout=10)
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
            self._json({
                name: {"status": service_status(name), **info}
                for name, info in SERVICES.items()
            })
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
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress per-request noise in journald


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9000), StatusHandler)
    server.serve_forever()
