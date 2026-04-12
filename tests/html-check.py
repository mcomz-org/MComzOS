#!/usr/bin/env python3
"""
MComzOS dashboard static analysis — runs locally against src/dashboard/index.html.
No network, no hardware. Use this before building an image to catch regressions.

Usage:
    python3 tests/html-check.py
    python3 tests/html-check.py path/to/index.html   # custom path

Exit code 0 = all checks passed.
"""

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Load file
# ---------------------------------------------------------------------------
html_path = Path(sys.argv[1]) if len(sys.argv) > 1 else \
            Path(__file__).parent.parent / "src" / "dashboard" / "index.html"

if not html_path.exists():
    print(f"ERROR: {html_path} not found")
    sys.exit(2)

src = html_path.read_text()

# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------
_results = []
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


def has_id(id_val):
    return bool(re.search(rf'\bid=["\']' + re.escape(id_val) + r'["\']', src))


def has_text(text):
    return text in src


def has_fn(name):
    """Check that a JS function is defined (function X or X = function or arrow)."""
    return bool(re.search(
        rf'function\s+{re.escape(name)}\s*\(|'
        rf'{re.escape(name)}\s*=\s*function\s*\(|'
        rf'{re.escape(name)}\s*=\s*\(',
        src
    ))


# ---------------------------------------------------------------------------
# Structure — required IDs
# ---------------------------------------------------------------------------
section("HTML Structure — required element IDs")

for id_val in [
    "clock", "status-grid", "mcomz-version",
    "wifi-btn", "wifi-overlay", "wifi-panel", "wifi-current",
    "wifi-networks", "wifi-saved", "wifi-connect-form",
    "ap-btn",
    "mesh-detail", "radio-detail",
    "library-overlay", "library-panel", "library-grid",
    "books-overlay", "books-panel", "books-installed",
    "books-url", "books-dl-status", "books-recommended",
    "https-warn",
]:
    check(f"id={id_val!r} exists", has_id(id_val))

# ---------------------------------------------------------------------------
# Required section IDs for inline Mesh guards
# ---------------------------------------------------------------------------
section("Mesh guard section IDs")

check("id='meshtastic-section' exists", has_id("meshtastic-section"))
check("id='meshcore-section' exists", has_id("meshcore-section"))

# ---------------------------------------------------------------------------
# JavaScript functions
# ---------------------------------------------------------------------------
section("JavaScript functions defined")

for fn in [
    "tick", "renderStatus", "fetchStatus",
    "toggleMesh", "toggleRadio",
    "guardMeshService",
    "openWifi", "closeWifi", "loadWifiStatus", "scanNetworks",
    "selectNetwork", "submitConnect", "cancelConnect", "doConnect",
    "loadSavedNetworks", "forgetNetwork", "toggleAP",
    "openLibrary", "closeLibrary", "loadLibrary",
    "openBooks", "closeBooks", "loadBooks", "renderRecommended",
    "fetchMComzUrl", "startDownload", "removeBook",
    "togglePowerMenu", "closePowerMenu",
    "confirmShutdown", "confirmReboot",
    "esc",
]:
    check(f"function {fn}() defined", has_fn(fn))

# ---------------------------------------------------------------------------
# Key JS variables
# ---------------------------------------------------------------------------
section("JavaScript variables")

check("lastStatus variable declared", bool(re.search(r'\blet\s+lastStatus\b', src)))
check("lastStatus assigned in renderStatus",
      bool(re.search(r'lastStatus\s*=\s*data', src)))
check("apActive variable declared", bool(re.search(r'\blet\s+apActive\b', src)))
check("_pollTimer variable declared", bool(re.search(r'\blet\s+_pollTimer\b', src)))
check("RECOMMENDED_ZIMS constant declared",
      bool(re.search(r'\bconst\s+RECOMMENDED_ZIMS\b', src)))
check("MComzLibrary ZIMs in RECOMMENDED_ZIMS",
      "mcomz-org/MComzLibrary" in src and "zimPattern" in src)

# ---------------------------------------------------------------------------
# Card content
# ---------------------------------------------------------------------------
section("Dashboard card content")

check("Offline Library card present", "Offline Library" in src)
check("Open Library button calls openLibrary()", "openLibrary()" in src)
check("Manage Books button present", "openBooks()" in src)

check("Voice & Text card present", "Voice" in src and "Mumble" in src)
check("Mumble join URL uses /mumble/ws path", "/mumble/ws" in src)

check("Licensed Radio card present", "Licensed Radio" in src)
check("toggleRadio in Licensed Radio button",
      bool(re.search(r'onclick=["\']toggleRadio\(', src)))
check("Winlink/Pat section present inside radio-detail",
      "Winlink" in src and "Pat" in src)
check("JS8Call section present", "JS8Call" in src)
check("FreeDATA section present", "FreeDATA" in src)
check("VNC URL in Licensed Radio",
      "/vnc/vnc.html?path=vnc/websockify&autoconnect=true" in src)

check("Mesh Communication card present", "Mesh Communication" in src)
check("toggleMesh in Mesh button",
      bool(re.search(r'onclick=["\']toggleMesh\(', src)))

# ---------------------------------------------------------------------------
# Security / correctness
# ---------------------------------------------------------------------------
section("Security and correctness")

# Meshtastic/MeshCore links must open in new tab
check("Meshtastic link uses target=_blank",
      bool(re.search(r'/meshtastic/[^"]*"[^>]*target=["\']_blank["\']|'
                     r'target=["\']_blank["\'][^>]*/meshtastic/', src)))
check("MeshCore link uses target=_blank",
      bool(re.search(r'/meshcore/[^"]*"[^>]*target=["\']_blank["\']|'
                     r'target=["\']_blank["\'][^>]*/meshcore/', src)))

# guardMeshService called on both mesh links
check("guardMeshService called for meshtasticd",
      "guardMeshService('meshtasticd'" in src)
check("guardMeshService called for mcomz-meshcore",
      "guardMeshService('mcomz-meshcore'" in src)

# HTTPS warning banner
check("HTTPS warning banner present", "https-warn" in src)
check("HTTPS protocol check present",
      "location.protocol" in src and "https:" in src)

# AbortController for AP toggle
check("AbortController used in toggleAP",
      "AbortController" in src)

# Header controls
check("WiFi button uses SVG icon (no button text)",
      bool(re.search(r'id=["\']wifi-btn["\'][^>]*>\s*<svg', src)))
check("Power menu dropdown present", "power-menu" in src and "power-btn" in src)
check("System Status heading has 15-second tooltip",
      "Refreshes every 15 seconds" in src and 'title=' in src)

# AP stop uses longer timeout (35 s) for Python poll
check("35 s AbortController timeout for AP stop",
      "35000" in src)

# Standby / hardware badge logic in renderStatus
check("STANDBY_SVCS set defined (hostapd/dnsmasq get grey badge)",
      "STANDBY_SVCS" in src and "standby" in src)
check("HW_SVCS set defined (hardware services get grey badge)",
      "HW_SVCS" in src and "attach hardware" in src)
check("failed state gets err badge", "'err'" in src and "st === 'failed'" in src)
check("activating state gets act badge", "'act'" in src and "st === 'activating'" in src)
check("unknown/disconnected state gets dis badge", "'dis'" in src)

# 15-second status refresh interval
check("Status polling interval is 15 s",
      bool(re.search(r'setInterval\s*\(\s*fetchStatus\s*,\s*15000\s*\)', src)))

# Mumble section must mention Safari (getUserMedia requires HTTPS on Safari)
check("Safari usage note present in Mumble section",
      "Safari" in src)

# FreeDATA note — may not be installed on all builds
check("FreeDATA 'may not be installed' caveat present",
      bool(re.search(r'FreeDATA.{0,120}(may not|not.*installed|install)', src, re.IGNORECASE | re.DOTALL)))

# ---------------------------------------------------------------------------
# API routes referenced in JS
# ---------------------------------------------------------------------------
section("API routes referenced in JS")

for route in [
    "/api/status",
    "/api/version",
    "/api/wifi/networks",
    "/api/wifi/known",
    "/api/wifi/connect",
    "/api/wifi/forget",
    "/api/wifi/ap/start",
    "/api/wifi/ap/stop",
    "/api/system/poweroff",
    "/api/system/reboot",
    "/api/kiwix/books",
    "/api/kiwix/download",
    "/api/kiwix/download/status",
    "/api/kiwix/remove",
]:
    check(f"route {route!r} referenced", route in src)

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
