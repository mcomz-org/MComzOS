#!/usr/bin/env python3
"""
MComzOS smoke-test — run from a laptop on the same LAN as the hub after flashing.

Usage:
    python3 tests/smoke-test.py [host]          # default host: mcomz.local
    python3 tests/smoke-test.py 192.168.4.1     # use IP address

Covers TEST-PROCEDURES.md sections 1, 2, 3, 5, 6 and API-level checks.
WiFi panel, hotspot, kiosk, voice, and shutdown require manual testing.
Exit code 0 = all checks passed.
"""

import json
import ssl
import subprocess
import sys
import urllib.request
import urllib.error
from urllib.parse import urlencode

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HOST = sys.argv[1] if len(sys.argv) > 1 else "mcomz.local"
TIMEOUT = 10

# Self-signed cert context — expected on a fresh hub
_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE

# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------
_results = []   # (section, label, passed, detail)
_section = ""


def section(name):
    global _section
    _section = name
    print(f"\n── {name} {'─' * max(0, 60 - len(name))}")


def check(label, passed, detail=""):
    _results.append((_section, label, passed, detail))
    mark = "✅" if passed else "❌"
    line = f"  {mark} {label}"
    if detail:
        line += f"  ({detail})"
    print(line)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
def get(path="/", use_ssl=False, port=None, expect_codes=(200,)):
    """Return (status_code, body_bytes) or (None, None) on error."""
    scheme = "https" if use_ssl else "http"
    port_str = f":{port}" if port else ""
    full = f"{scheme}://{HOST}{port_str}{path}"
    ctx = _SSL if use_ssl else None
    try:
        req = urllib.request.Request(full)
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return None, str(e).encode()


def get_json(path, use_ssl=False, port=None, params=None):
    """Return parsed JSON or None on failure."""
    full_path = path
    if params:
        full_path += "?" + urlencode(params)
    code, body = get(use_ssl=use_ssl, port=port, path=full_path)
    if code != 200:
        return None
    try:
        return json.loads(body)
    except Exception:
        return None


def post_json(path, payload, use_ssl=False, port=None):
    """POST JSON, return (status_code, parsed_response_or_None)."""
    scheme = "https" if use_ssl else "http"
    port_str = f":{port}" if port else ""
    full = f"{scheme}://{HOST}{port_str}{path}"
    ctx = _SSL if use_ssl else None
    data = json.dumps(payload).encode()
    req = urllib.request.Request(full, data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            body = r.read()
            try:
                return r.status, json.loads(body)
            except Exception:
                return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, None


# ---------------------------------------------------------------------------
# Section 1 — Basic Connectivity
# ---------------------------------------------------------------------------
section("§1 Basic Connectivity")

code, body = get(path="/")
check("HTTP dashboard responds", code == 200,
      f"HTTP {code}" if code else "no response")

check("HTTP dashboard is MComz", code == 200 and b"MComz" in body,
      "body does not contain 'MComz'" if code == 200 and b"MComz" not in body else "")

code_s, _ = get(path="/", use_ssl=True)
check("HTTPS dashboard responds", code_s in (200, 301, 302),
      f"HTTP {code_s}" if code_s else "no response")

# mDNS resolution — only meaningful when HOST is a .local name
if HOST.endswith(".local"):
    try:
        r = subprocess.run(
            ["ping", "-c", "1", "-W", "3", HOST],
            capture_output=True, timeout=5
        )
        check("mDNS resolves and host is reachable (ping)", r.returncode == 0,
              "ping failed — avahi-daemon may be down or mDNS blocked on this LAN")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        check("mDNS resolves and host is reachable (ping)", False, str(e))

data = get_json("/api/version")
check("Version API responds", data is not None, "no JSON response")
if data:
    ver = data.get("version", "")
    check("Version string present", bool(ver) and ver != "unknown",
          f"version={ver!r}")

# ---------------------------------------------------------------------------
# Section 2 — System Status Card
# ---------------------------------------------------------------------------
section("§2 System Status")

EXPECTED_SERVICES = [
    "hostapd", "dnsmasq", "avahi-daemon", "mumble-server",
    "mcomz-mumble-ws", "meshtasticd", "mcomz-meshcore", "kiwix-serve",
    "pat", "direwolf", "ardopcf", "mcomz-vnc", "mcomz-novnc", "nginx",
]

status = get_json("/api/status")
check("Status API responds", status is not None, "no JSON response")

if status:
    missing = [s for s in EXPECTED_SERVICES if s not in status]
    check("All expected services present", not missing,
          f"missing: {missing}" if missing else "")

    for svc in EXPECTED_SERVICES:
        if svc in status:
            s = status[svc].get("status")
            check(f"  {svc} has status field", isinstance(s, str),
                  f"got {s!r}")

    # Services that must be active on a healthy booted hub
    for must_be_on in ("nginx", "avahi-daemon", "kiwix-serve"):
        if must_be_on in status:
            active = status[must_be_on].get("status") == "active"
            check(f"  {must_be_on} is active", active,
                  status[must_be_on].get("status"))

    # Services that should be standby (no LoRa hardware in typical test)
    for standby in ("hostapd", "dnsmasq"):
        if standby in status:
            s = status[standby].get("status")
            check(f"  {standby} is standby (not active)", s != "active",
                  f"unexpectedly active" if s == "active" else s)

# ---------------------------------------------------------------------------
# Section 3 — Kiwix / Offline Library
# ---------------------------------------------------------------------------
section("§3 Offline Library (Kiwix)")

code, body = get(path="/library/")
check("Kiwix /library/ responds", code == 200, f"HTTP {code}")

books_data = get_json("/api/kiwix/books")
check("Kiwix books API responds", books_data is not None)

if books_data:
    books = books_data.get("books", [])
    check("At least one ZIM registered", len(books) >= 1,
          f"found {len(books)} book(s)")
    check("ZIM paths are strings", all(isinstance(b.get("path"), str) for b in books))

    # Check for expected content keywords in titles/paths
    all_text = " ".join(
        (b.get("title", "") + " " + b.get("path", "")).lower()
        for b in books
    )
    # Spot-check for at least one MComzLibrary ZIM (any of the three is fine —
    # the literature ZIM can be deleted by the user and reinstalled via Manage Books)
    any_mcomz = any(kw in all_text for kw in ("survival", "literature", "scripture"))
    check("At least one MComzLibrary ZIM present", any_mcomz,
          "none of survival/literature/scripture found in titles/paths")

    # WikiMed Mini — downloaded during provisioning
    any_wikimed = any(kw in all_text for kw in ("wikimed", "wikipedia_en_medicine", "medicine"))
    check("WikiMed Mini ZIM present", any_wikimed,
          "wikimed/medicine not found in titles/paths — provisioning may have failed")

# Manage Books API endpoints
dl_status = get_json("/api/kiwix/download/status", params={"file": "test.zim"})
check("Download status API responds", dl_status is not None)
if dl_status:
    check("Download status returns idle for unknown file",
          dl_status.get("status") == "idle", f"got {dl_status.get('status')!r}")

# ---------------------------------------------------------------------------
# Section 5 — Licensed Radio
# ---------------------------------------------------------------------------
section("§5 Licensed Radio")

# Pat — nginx proxies port 8081 with HTTPS
code_pat, _ = get(path="/", use_ssl=True, port=8081)
check("Pat port 8081 (HTTPS) responds", code_pat in (200, 301, 302),
      f"HTTP {code_pat}" if code_pat else "no response")

# noVNC HTML file
code_vnc, body_vnc = get(path="/vnc/vnc.html")
check("noVNC HTML serves at /vnc/vnc.html", code_vnc == 200,
      f"HTTP {code_vnc}")
if code_vnc == 200:
    check("noVNC HTML contains 'noVNC'", b"noVNC" in body_vnc or b"novnc" in body_vnc.lower())

# VNC websockify endpoint — plain GET returns 400/405/426 (WebSocket-only); that's correct
code_ws, _ = get(path="/vnc/websockify")
check("VNC websockify endpoint exists (nginx route present)",
      code_ws in (200, 400, 405, 426),
      f"HTTP {code_ws}" if code_ws else "no response — nginx route missing")

# Mumble static files
code_mum, body_mum = get(path="/mumble/")
check("Mumble-web static files serve at /mumble/", code_mum == 200,
      f"HTTP {code_mum}")

# Mumble WS endpoint — plain GET returns 400/405/426 (WebSocket-only); that's correct
code_mws, _ = get(path="/mumble/ws")
check("Mumble WebSocket endpoint exists",
      code_mws in (200, 400, 405, 426),
      f"HTTP {code_mws}" if code_mws else "no response — nginx route missing")

# ---------------------------------------------------------------------------
# Section 6 — Mesh Communication
# ---------------------------------------------------------------------------
section("§6 Mesh Communication")

# Without LoRa hardware these should return 502
code_mesh, _ = get(path="/meshtastic/")
check("Meshtastic /meshtastic/ returns 502 (no LoRa hardware, as expected)",
      code_mesh == 502, f"HTTP {code_mesh}")

code_mc, _ = get(path="/meshcore/")
check("MeshCore /meshcore/ returns 502 (no LoRa hardware, as expected)",
      code_mc == 502, f"HTTP {code_mc}")

if status:
    mesh_status = status.get("meshtasticd", {}).get("status")
    check("meshtasticd shows inactive in status API",
          mesh_status != "active",
          f"status={mesh_status!r}")

# ---------------------------------------------------------------------------
# Section 7 — WiFi Management API (read-only endpoints)
# ---------------------------------------------------------------------------
section("§7 WiFi Management API")

wifi_net = get_json("/api/wifi/networks")
check("WiFi networks API responds", wifi_net is not None, "no JSON response")
if wifi_net:
    check("WiFi networks response has 'networks' key", "networks" in wifi_net,
          f"keys: {list(wifi_net.keys())}")
    check("WiFi ap_active field present", "ap_active" in wifi_net,
          f"keys: {list(wifi_net.keys())}")

wifi_known = get_json("/api/wifi/known")
check("WiFi known networks API responds", wifi_known is not None, "no JSON response")
if wifi_known:
    check("WiFi known response has 'networks' key", "networks" in wifi_known,
          f"keys: {list(wifi_known.keys())}")

# ---------------------------------------------------------------------------
# Section 10 — System control endpoints (existence check, non-destructive)
# ---------------------------------------------------------------------------
section("§10 System control endpoints (non-destructive)")

# A GET to a POST-only route returns 404 from the Python handler if nginx
# successfully proxied the request — proves the route is wired up end-to-end.
# (A 502 or connection error would mean nginx can't reach the backend.)
for endpoint in ("/api/system/poweroff", "/api/system/reboot"):
    code_ep, _ = get(path=endpoint)
    check(f"{endpoint} route reachable (nginx → backend)", code_ep == 404,
          f"HTTP {code_ep} — expected 404 (GET on POST-only route); "
          "502 = nginx can't reach backend; None = no response")

# ---------------------------------------------------------------------------
# Section 3 (continued) — Manage Books write endpoints (non-destructive checks)
# ---------------------------------------------------------------------------
section("§3 Manage Books — write endpoint sanity")

# POST a bogus URL — should return ok=False, not a 500
code_b, resp_b = post_json("/api/kiwix/download", {"url": "https://example.com/not-a-zim.txt"})
check("Download rejects non-.zim URL", code_b == 200 and resp_b and not resp_b.get("ok"),
      f"code={code_b} ok={resp_b.get('ok') if resp_b else '?'}")

# POST remove with a path that doesn't exist — should return ok=True (nothing to remove)
# or ok=False — just verify it doesn't 500
code_r, resp_r = post_json("/api/kiwix/remove", {"path": "/nonexistent/path.zim"})
check("Remove nonexistent path does not 500", code_r == 200,
      f"HTTP {code_r}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total = len(_results)
passed = sum(1 for r in _results if r[2])
failed = total - passed

print(f"\n{'═' * 62}")
print(f"  {passed}/{total} checks passed", end="")
if failed:
    print(f"  — {failed} FAILED")
    print()
    print("  Failed checks:")
    for sec, label, ok, detail in _results:
        if not ok:
            d = f" ({detail})" if detail else ""
            print(f"    ❌ [{sec}] {label}{d}")
else:
    print("  — all passed ✅")
print(f"{'═' * 62}")

sys.exit(0 if failed == 0 else 1)
