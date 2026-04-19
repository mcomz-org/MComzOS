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
    "freedata-section",
    "diag-overlay", "diag-badge",
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
    "fetchMComzUrl", "fetchKiwixUrl", "startDownload", "removeBook",
    "togglePowerMenu", "closePowerMenu",
    "confirmShutdown", "confirmReboot",
    "openMeshFlasher",
    "dismissDiag",
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
check("Mumble join URL uses dynamic port (not hardcoded 443)", "port=443/mumble" not in src)

check("Licensed Radio card present", "Licensed Radio" in src)
check("toggleRadio in Licensed Radio button",
      bool(re.search(r'onclick=["\']toggleRadio\(', src)))
check("Winlink/Pat section present inside radio-detail",
      "Winlink" in src and "Pat" in src)
check("JS8Call section present", "JS8Call" in src)
check("FreeDATA section present", "FreeDATA" in src)
check("VNC URL in Licensed Radio",
      "/vnc/vnc.html?path=websockify&autoconnect=true" in src)
check("VNC links use HTTPS (not bare href — VNC auth requires HTTPS)",
      bool(re.search(r"'https://'\s*\+\s*location\.hostname.*vnc/vnc\.html", src)))

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

# MeshCore offline flasher — openMeshFlasher() probes live URL, falls back to local bundle
check("openMeshFlasher references live flasher URL",
      "flasher.meshcore.co.uk" in src)
check("openMeshFlasher references local offline bundle path",
      "/meshcore-flash/" in src)
check("openMeshFlasher uses timeout-based connectivity probe",
      "AbortSignal.timeout" in src or "AbortController" in src)

# Pat button must use literal https:// — not location.protocol (port 8081 is HTTPS-only)
check("Pat button uses literal https:// (not location.protocol)",
      bool(re.search(r"'https://'\s*\+\s*location\.hostname.*8081", src)) and
      not bool(re.search(r"location\.protocol.*8081", src)))

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
check("HW_SVCS checked before failed (no spurious err badge without hardware)",
      src.index("HW_SVCS.has(name)") < src.index("st === 'failed'"))
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

# FreeDATA section must be conditionally hidden based on freedata_installed API field
check("renderStatus filters non-service keys (typeof svc.status)",
      "typeof svc.status === 'string'" in src)
check("renderStatus hides freedata-section when freedata_installed is false",
      "freedata_installed" in src and "freedata-section" in src)

# Diagnostics mode splash
check("diagnostics_mode read from status API in renderStatus",
      "data.diagnostics_mode" in src)
check("dismissDiag stores sessionStorage key",
      "sessionStorage.setItem" in src and "diag-dismissed" in src)
check("diag-overlay shown only when not already dismissed",
      "sessionStorage.getItem('diag-dismissed')" in src)
check("diag-badge toggled on diagnostics_mode",
      "diag-badge" in src and "diagnostics_mode" in src)

# Kiwix viewer must use b.name (slug) not b.id (UUID) — UUID-based URLs return 404
check("Kiwix viewer link uses b.name slug (not b.id UUID)",
      "b.name" in src and "/library/viewer#" in src and "b.id" not in src.split("/library/viewer")[1][:30],
      "viewer link should use b.name slug — check index.html around /library/viewer#")

# RECOMMENDED_ZIMS regression guard — these names do not exist in the Kiwix catalog
for bad_name in ("wikipedia_en_medicine_mini", "wikimed_en_all_mini", "wikipedia_en_all_mini"):
    check(f"RECOMMENDED_ZIMS does not contain obsolete name {bad_name!r}",
          bad_name not in src)

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
# Theme CSS — shared token file and Kiwix overrides
# ---------------------------------------------------------------------------
section("Theme CSS — shared tokens and Kiwix overrides")

theme_dir = html_path.parent.parent / "theme"

check("@import url('/theme/mcomz-theme.css') in dashboard <style>",
      "@import url(\"/theme/mcomz-theme.css\")" in src,
      "index.html must import the shared token file — CSS variables are defined there")

check(":root { --bg } block removed from index.html (tokens live in mcomz-theme.css)",
      "--bg: #121212" not in src,
      "--bg: #121212 still present in index.html; remove it (it belongs in mcomz-theme.css)")

theme_css = theme_dir / "mcomz-theme.css"
if theme_css.exists():
    theme_src = theme_css.read_text()
    check("mcomz-theme.css exists at src/theme/mcomz-theme.css", True)
    check("mcomz-theme.css defines --bg", "--bg:" in theme_src)
    check("mcomz-theme.css defines --panel", "--panel:" in theme_src)
    check("mcomz-theme.css defines --text", "--text:" in theme_src)
    check("mcomz-theme.css defines --blue", "--blue:" in theme_src)
    check("mcomz-theme.css has balanced braces",
          theme_src.count("{") == theme_src.count("}"),
          f"{{ count={theme_src.count('{')} }} count={theme_src.count('}')}")
else:
    check("mcomz-theme.css exists at src/theme/mcomz-theme.css", False,
          f"not found at {theme_css}")

kiwix_css = theme_dir / "kiwix-overrides.css"
if kiwix_css.exists():
    kiwix_src = kiwix_css.read_text()
    check("kiwix-overrides.css exists at src/theme/kiwix-overrides.css", True)
    check('kiwix-overrides.css first statement is @import of mcomz-theme.css',
          kiwix_src.lstrip().startswith('@import url("/theme/mcomz-theme.css")'),
          "@import must be the first non-whitespace statement")
    check("kiwix-overrides.css has balanced braces",
          kiwix_src.count("{") == kiwix_src.count("}"),
          f"{{ count={kiwix_src.count('{')} }} count={kiwix_src.count('}')}")
    check("kiwix-overrides.css contains .ui-widget-header rule (S-8 jQuery UI coverage)",
          ".ui-widget-header" in kiwix_src,
          "missing — S-8 toolbar fix not present")
    check("kiwix-overrides.css contains filter:none rule for /catalog/v2/illustration/ (S-8 cover guard)",
          "/catalog/v2/illustration/" in kiwix_src and "filter: none" in kiwix_src,
          "missing — cover illustration anti-invert guard not present")
    check("kiwix-overrides.css does NOT have unscoped 'img { filter: invert' rule",
          not re.search(r"^\s*img\s*\{[^}]*filter\s*:\s*invert", kiwix_src, re.MULTILINE),
          "unscoped img filter would mangle book covers — scope the filter narrowly")
    # S-9 specificity-matched selectors — viewer toolbar
    check("kiwix-overrides.css targets .kiwix #kiwixtoolbar button (S-9 specificity match)",
          ".kiwix #kiwixtoolbar button" in kiwix_src,
          "missing — kiwix's own 0-1-1-1 button rule will win the !important tie")
    check("kiwix-overrides.css targets .kiwix #kiwixtoolbar #kiwixsearchform input (S-9 search input)",
          ".kiwix #kiwixtoolbar #kiwixsearchform input" in kiwix_src,
          "missing — viewer search input will stay light")
    # S-9 library-index page coverage
    check("kiwix-overrides.css covers .kiwixButton (S-9 library index)",
          "body .kiwixButton" in kiwix_src,
          "missing — library-index buttons will stay light")
    # S-9 cache-bust-safe icon selector
    check("kiwix-overrides.css uses [src*=\".svg\"] (cache-bust-safe icon match)",
          '[src*=".svg"]' in kiwix_src,
          'missing — [src$=".svg"] would miss URLs with ?cacheid= query strings')
    # S-9 broken-cover size cap
    check("kiwix-overrides.css caps illustration img max-width (S-9 broken-glyph guard)",
          "max-width: 128px" in kiwix_src,
          "missing — broken-image glyph will scale to fill its container")
else:
    check("kiwix-overrides.css exists at src/theme/kiwix-overrides.css", False,
          f"not found at {kiwix_css}")

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
