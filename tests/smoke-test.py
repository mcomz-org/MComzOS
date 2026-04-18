#!/usr/bin/env python3
"""
MComzOS smoke-test — run from a laptop on the same LAN as the hub after flashing.

Usage:
    python3 tests/smoke-test.py [host]          # default host: mcomz.local
    python3 tests/smoke-test.py 192.168.4.1     # use IP address

Checks: HTTP/HTTPS reachability, mDNS, version and status APIs, all expected
services, Kiwix library and books API, Pat/VNC/Mumble routes, mesh 502 guards,
WiFi management API structure, system control route wiring, and Manage Books
write-endpoint sanity. Does not cover voice, hotspot, kiosk, or destructive ops.
Exit code 0 = all checks passed.
"""

import json
import socket
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
section("Basic Connectivity")

code, body = get(path="/")
check("HTTP dashboard responds", code == 200,
      f"HTTP {code}" if code else "no response")

check("HTTP dashboard is MComz", code == 200 and b"MComz" in body,
      "body does not contain 'MComz'" if code == 200 and b"MComz" not in body else "")

code_s, body_s = get(path="/", use_ssl=True)
check("HTTPS dashboard responds", code_s == 200,
      f"HTTP {code_s}" if code_s else "no response")
if code_s == 200:
    check("HTTPS / serves full dashboard (not redirect page)",
          b"MComz" in body_s and b"status-grid" in body_s,
          "HTTPS / returned unexpected content — port-443 location / may be misconfigured"
          if not (b"MComz" in body_s and b"status-grid" in body_s) else "")

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
section("System Status")

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
section("Offline Library (Kiwix)")

code, body = get(path="/library/")
check("Kiwix /library/ responds", code == 200, f"HTTP {code}")

books_data = get_json("/api/kiwix/books")
check("Kiwix books API responds", books_data is not None)

if books_data:
    books = books_data.get("books", [])
    check("At least one ZIM registered", len(books) >= 1,
          "" if len(books) >= 1 else f"found {len(books)} book(s)")
    check("ZIM paths are strings", all(isinstance(b.get("path"), str) for b in books))

    # ZIM entries must have a name (slug) field — added in status.py OPDS rewrite
    names_present = all(isinstance(b.get("name"), str) and b.get("name") for b in books)
    check("ZIM entries have name (slug) field", names_present,
          "name field missing — status.py kiwix_books() may not have been updated"
          if not names_present else "")

    # ZIM entries should include a size field (bytes, from os.path.getsize in status.py)
    sizes_present = all(isinstance(b.get("size"), int) for b in books)
    check("ZIM entries have size field", sizes_present,
          "size field missing or non-integer" if not sizes_present else "")

    # Individual MComzLibrary ZIM checks — all three ship in the base image
    for slug_kw, label in [
        ("survival",   "MComz Survival"),
        ("literature", "MComz Literature"),
        ("scriptures", "MComz Scriptures"),
    ]:
        zim = next((b for b in books
                    if slug_kw in b.get("name", "").lower()
                    or slug_kw in b.get("path", "").lower()), None)
        check(f"{label} ZIM registered", zim is not None,
              f"no book with '{slug_kw}' in name/path" if zim is None else "")
        if zim and zim.get("name"):
            slug_path = f"/library/content/{urllib.parse.quote(zim['name'])}/"
            code_sl, _ = get(path=slug_path)
            check(f"{label} ZIM content responds",
                  code_sl in (200, 301, 302),
                  f"HTTP {code_sl} for {slug_path!r}" if code_sl not in (200, 301, 302) else "")

    # WikiMed — downloaded on first boot via mcomz-wikimed-download.service
    wikimed = next((b for b in books
                    if any(kw in (b.get("name", "") + b.get("path", "")).lower()
                           for kw in ("wikimed", "medicine"))), None)
    check("WikiMed ZIM registered (first-boot download)", wikimed is not None,
          "not yet registered — mcomz-wikimed-download.service may still be running"
          if wikimed is None else "")
    if wikimed and wikimed.get("name"):
        wm_path = f"/library/content/{urllib.parse.quote(wikimed['name'])}/"
        code_wm, _ = get(path=wm_path)
        check("WikiMed ZIM content responds", code_wm in (200, 301, 302),
              f"HTTP {code_wm}" if code_wm not in (200, 301, 302) else "")

# OPDS catalog — verifies kiwix-serve is exposing its library
code_opds, body_opds = get(path="/library/catalog/v2/entries")
check("Kiwix OPDS catalog responds", code_opds == 200,
      f"HTTP {code_opds}" if code_opds else "no response")
if code_opds == 200:
    check("OPDS catalog is Atom XML", b"<feed" in body_opds or b"<?xml" in body_opds,
          "unexpected response body")
    check("OPDS catalog has at least one entry", b"<entry" in body_opds,
          "no <entry> elements — library may be empty or kiwix-serve not yet indexed ZIMs")

# Kiwix reader — /library/viewer page must load; content slugs must serve
if books_data:
    books = books_data.get("books", [])
    if books:
        code_viewer, _ = get(path="/library/viewer")
        check("Kiwix /library/viewer page responds", code_viewer == 200,
              f"HTTP {code_viewer}" if code_viewer else "no response")

# Manage Books API endpoints
dl_status = get_json("/api/kiwix/download/status", params={"file": "test.zim"})
check("Download status API responds", dl_status is not None)
if dl_status:
    check("Download status returns idle for unknown file",
          dl_status.get("status") == "idle",
          "" if dl_status.get("status") == "idle" else f"got {dl_status.get('status')!r}")

# ---------------------------------------------------------------------------
# Section 4 — Theme (shared CSS tokens + Kiwix dark-mode injection)
# ---------------------------------------------------------------------------
section("Theme — shared CSS + Kiwix dark-mode injection")

code_tc, body_tc = get(path="/theme/mcomz-theme.css")
check("/theme/mcomz-theme.css serves", code_tc == 200,
      f"HTTP {code_tc}" if code_tc else "no response")
if code_tc == 200:
    check("mcomz-theme.css contains --bg token",
          b"--bg:" in body_tc,
          "token missing — mcomz-theme.css may not have been deployed")
    check("mcomz-theme.css contains #121212 (dark background value)",
          b"#121212" in body_tc,
          "expected dark background value missing")

code_ko, body_ko = get(path="/theme/kiwix-overrides.css")
check("/theme/kiwix-overrides.css serves", code_ko == 200,
      f"HTTP {code_ko}" if code_ko else "no response")
if code_ko == 200:
    check('kiwix-overrides.css imports mcomz-theme.css',
          b'@import url("/theme/mcomz-theme.css")' in body_ko,
          "first line must be @import — token sharing is broken without it")

# Verify sub_filter fired: /library/ HTML must contain the injected link tag.
# Only checked if kiwix-serve is already confirmed up (code from earlier fetch).
code_lib, body_lib = get(path="/library/")
if code_lib == 200:
    check("/library/ HTML contains injected theme link (sub_filter active)",
          b"/theme/kiwix-overrides.css" in body_lib,
          "link tag not found — sub_filter may not be active (nginx-core lacks sub_module; "
          "check nginx -V for http_sub_module); or kiwix response is still gzip-encoded")

# ---------------------------------------------------------------------------
# Section 5 — Licensed Radio
# ---------------------------------------------------------------------------
section("Licensed Radio")

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

# Xvnc TCP port — websockify proxies to localhost:5901; confirm Xvnc is actually up
try:
    with socket.create_connection((HOST, 5901), timeout=3) as s:
        banner = s.recv(32)
    vnc_up = banner.startswith(b"RFB")
    check("Xvnc is accepting connections on port 5901",
          vnc_up, "" if vnc_up else f"unexpected banner: {banner!r}")
except Exception as e:
    check("Xvnc is accepting connections on port 5901", False,
          f"TCP connect failed: {e} — mcomz-vnc may not be running")

# websockify WebSocket upgrade — raw HTTP/1.1 Upgrade to confirm the chain is alive
# (nginx → websockify → Xvnc). A plain GET returns 400/426; a real Upgrade gets 101.
try:
    import hashlib, base64, os as _os
    ws_key = base64.b64encode(_os.urandom(16)).decode()
    upgrade_req = (
        f"GET /vnc/websockify HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        f"Upgrade: websocket\r\n"
        f"Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {ws_key}\r\n"
        f"Sec-WebSocket-Version: 13\r\n"
        f"\r\n"
    )
    with socket.create_connection((HOST, 80), timeout=5) as ws_sock:
        ws_sock.sendall(upgrade_req.encode())
        resp_line = ws_sock.recv(64).split(b"\r\n")[0].decode(errors="replace")
    ws_upgraded = resp_line.startswith("HTTP/1.1 101")
    check("websockify WebSocket upgrade succeeds (101 Switching Protocols)",
          ws_upgraded,
          f"got {resp_line!r} — websockify or nginx proxy may be broken"
          if not ws_upgraded else "")
except Exception as e:
    check("websockify WebSocket upgrade succeeds (101 Switching Protocols)", False,
          f"socket error: {e}")

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
section("Mesh Communication")

# Offline MeshCore firmware flasher — provisioned at build time into /meshcore-flash/
code_mf, body_mf = get(path="/meshcore-flash/")
check("/meshcore-flash/ responds (offline flasher provisioned)", code_mf == 200,
      f"HTTP {code_mf}" if code_mf else
      "no response — flasher may not have been provisioned (check CI log for rescue-block message)")
if code_mf == 200:
    check("/meshcore-flash/ contains flasher content",
          b"MeshCore" in body_mf or b"meshcore" in body_mf.lower(),
          "unexpected body — flasher app may not have cloned or path-patched correctly"
          if not (b"MeshCore" in body_mf or b"meshcore" in body_mf.lower()) else "")

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
section("WiFi Management API")

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
section("System control endpoints (non-destructive)")

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
section("Manage Books — write endpoint sanity")

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
# Section 11 — Kiwix catalog name validation (online-only, warn not fail)
# ---------------------------------------------------------------------------
section("RECOMMENDED_ZIMS catalog names (online check)")

_RECOMMENDED_KIWIX_NAMES = [
    "wikipedia_en_medicine",
    "wikipedia_en_top",
    "appropedia_en_all",
    "wikisource_en_all",
]

try:
    for kiwix_name in _RECOMMENDED_KIWIX_NAMES:
        catalog_url = f"https://library.kiwix.org/catalog/v2/entries?name={kiwix_name}"
        try:
            with urllib.request.urlopen(catalog_url, timeout=10) as r:
                body_cat = r.read()
            found = b"<entry>" in body_cat
            check(f"Kiwix catalog resolves {kiwix_name!r}", found,
                  "name not found in catalog" if not found else "")
        except Exception as e:
            # Warn only — smoke-test must pass on an offline LAN
            print(f"  ⚠  catalog check skipped for {kiwix_name!r}: {e}")
except Exception as e:
    print(f"  ⚠  RECOMMENDED_ZIMS catalog section skipped: {e}")

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
