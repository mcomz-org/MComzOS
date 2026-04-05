#!/usr/bin/env python3
"""MComzOS Status API — serves JSON service health on localhost:9000.
Proxied by nginx at /api/. No third-party dependencies; stdlib only."""

import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

SERVICES = {
    "hostapd":          {"label": "WiFi Access Point",       "path": None},
    "dnsmasq":          {"label": "DHCP / DNS",              "path": None},
    "avahi-daemon":     {"label": "mDNS (.local)",           "path": None},
    "mumble-server":    {"label": "Voice & Text (Mumble)",   "path": "/mumble/"},
    "meshtasticd":      {"label": "Meshtastic",              "path": "/meshtastic/"},
    "mcomz-meshcore":   {"label": "MeshCore",                "path": "/meshcore/"},
    "kiwix-serve":      {"label": "Offline Library",         "path": "/library/"},
    "pat":              {"label": "Winlink Email (Pat)",      "path": "/pat/"},
    "direwolf":         {"label": "APRS (Direwolf)",         "path": None},
    "ardopcf":          {"label": "HF Modem (ardopcf)",      "path": None},
    "mcomz-vnc":        {"label": "Remote Desktop",          "path": "/vnc/"},
    "nginx":            {"label": "Web Server",              "path": None},
}


def service_status(name):
    result = subprocess.run(
        ["systemctl", "is-active", name],
        capture_output=True, text=True
    )
    return result.stdout.strip()


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/status"):
            statuses = {
                name: {"status": service_status(name), **info}
                for name, info in SERVICES.items()
            }
            body = json.dumps(statuses, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress per-request noise in journald


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9000), StatusHandler)
    server.serve_forever()
