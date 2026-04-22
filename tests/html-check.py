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
# S-11: WikiMed entry must declare zimPattern: "wikimed" so the installed-on-disk
# filename (wikimed-mini.zim) matches and the entry is hidden from the recommended
# list once installed. Without this, the filter falls back to "wikipedia_en_medicine"
# which never appears in the renamed on-disk file.
check("WikiMed entry has zimPattern: \"wikimed\" (S-11 hide-when-installed)",
      bool(re.search(r'kiwixName:\s*"wikipedia_en_medicine".*?zimPattern:\s*"wikimed"',
                     src, re.DOTALL)),
      "WikiMed entry will stay in recommended list after install — add zimPattern: \"wikimed\"")
# S-15 Kiwix library browse/search UI inside the Manage Books panel
check("S-15: kiwix-search-input element present (browse UI)",
      'id="kiwix-search-input"' in src or "id='kiwix-search-input'" in src,
      "missing — Kiwix library browse search box not present")
check("S-15: kiwix-search-results container present",
      'id="kiwix-search-results"' in src,
      "missing — search results container not present")
check("S-15: onKiwixSearchInput handler defined",
      has_fn("onKiwixSearchInput"),
      "missing — debounced search input handler not defined")
check("S-15: kiwixSearch function defined",
      has_fn("kiwixSearch"),
      "missing — kiwixSearch function not defined")
check("S-15: search hits library.kiwix.org/catalog/v2/entries?q=",
      "library.kiwix.org/catalog/v2/entries?q=" in src,
      "missing — search must query the OPDS catalog with ?q=")
# S-16: mobile first-run tips card with localStorage gating
check("S-16: #mobile-tips card present",
      'id="mobile-tips"' in src,
      "missing — mobile tips card not in DOM")
check("S-16: dismissMobileTips function defined",
      has_fn("dismissMobileTips"),
      "missing — dismiss handler not defined")
check("S-16: localStorage key mcomz_mobile_tips_seen referenced",
      "mcomz_mobile_tips_seen" in src,
      "missing — gating key not referenced; tips will reappear every load")
check("S-16: matchMedia narrow-screen check (max-width: 700px)",
      "matchMedia('(max-width: 700px)')" in src or 'matchMedia("(max-width: 700px)")' in src,
      "missing — tips will appear on desktop too")

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
# S-12: service ordering — MeshCore before Meshtastic, JS8Call before Pat
check("S-12: meshcore-section appears before meshtastic-section",
      src.find("meshcore-section") != -1 and src.find("meshtastic-section") != -1
      and src.find("meshcore-section") < src.find("meshtastic-section"),
      "MeshCore must appear above Meshtastic in the mesh card")
# JS8Call/Pat ordering inside #radio-detail
_radio_open = src.find('id="radio-detail"')
_radio_close = src.find("</div>", _radio_open + 200) if _radio_open != -1 else -1
_radio_block = src[_radio_open:src.find('<!-- SERVICE STATUS', _radio_open)] if _radio_open != -1 else ""
check("S-12: JS8Call appears before 'Open Pat' inside #radio-detail",
      _radio_block and _radio_block.find("JS8Call") != -1
      and _radio_block.find("Open Pat") != -1
      and _radio_block.find("JS8Call") < _radio_block.find("Open Pat"),
      "JS8Call section must come above Pat inside the radio card")
check("VNC URL in Licensed Radio",
      "/vnc/vnc.html?path=websockify&autoconnect=true" in src)
check("VNC links use HTTPS (not bare href — VNC auth requires HTTPS)",
      bool(re.search(r"'https://'\s*\+\s*location\.hostname.*vnc/vnc\.html", src)))
# S-14: noVNC URLs must include resize=remote so the VNC desktop adopts the
# browser viewport via RandR, and reconnect=true so transient drops auto-recover.
check("S-14: noVNC URLs include resize=remote (server-side RandR)",
      "resize=remote" in src,
      "missing — VNC desktop will be letterboxed at fixed resolution")
check("S-14: noVNC URLs include reconnect=true",
      "reconnect=true" in src,
      "missing — transient drops won't auto-recover")
# Both JS8Call and FreeDATA buttons must use the upgraded URL — guard against
# someone updating one and forgetting the other.
check("S-14: noVNC URL with resize=remote appears at least twice (JS8Call + FreeDATA)",
      src.count("resize=remote") >= 2,
      f"only found {src.count('resize=remote')} occurrence(s) — both JS8Call and FreeDATA buttons must be upgraded")

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
check("guardMeshService called for mcomz-meshcore-gui",
      "guardMeshService('mcomz-meshcore-gui'" in src)

# MeshCore BLE setup panel — scan/set/clear flow, visible regardless of service state
check("MeshCore BLE setup details element present",
      'id="meshcore-ble-setup"' in src)
check("MeshCore BLE current-config display element present",
      'id="meshcore-ble-current"' in src)
check("MeshCore BLE devices list element present",
      'id="meshcore-ble-devices"' in src)
check("MeshCore BLE manual MAC input present",
      'id="meshcore-ble-mac"' in src)
check("meshcoreBleLoadCurrent function defined",
      "function meshcoreBleLoadCurrent" in src or "async function meshcoreBleLoadCurrent" in src)
check("meshcoreBleScan function defined",
      "function meshcoreBleScan" in src or "async function meshcoreBleScan" in src)
check("meshcoreBleSet function defined",
      "function meshcoreBleSet" in src or "async function meshcoreBleSet" in src)
check("meshcoreBleClear function defined",
      "function meshcoreBleClear" in src or "async function meshcoreBleClear" in src)
check("BLE guard message mentions BLE setup option",
      "Configure BLE radio" in src)
check("BLE MAC format regex present in manual-set validation",
      bool(re.search(r"\[0-9A-Fa-f\]\{2\}", src)))

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
# S-13: WiFi icon must match iOS pattern — 1 dot + 2 arcs (was 1 dot + 3 arcs).
# Outermost path d="M0 3.5..." was the visually-mismatched arc and is removed.
_wifi_match = re.search(
    r'id=["\']wifi-btn["\'][^>]*>\s*<svg[^>]*>(.*?)</svg>', src, re.DOTALL)
if _wifi_match:
    _wifi_svg = _wifi_match.group(1)
    check("S-13: WiFi SVG has exactly 1 <circle>",
          _wifi_svg.count("<circle") == 1,
          f"got {_wifi_svg.count('<circle')} circles")
    check("S-13: WiFi SVG has exactly 2 <path> arcs (outermost arc removed)",
          _wifi_svg.count("<path") == 2,
          f"got {_wifi_svg.count('<path')} paths — should be dot + 2 arcs (iOS pattern)")
else:
    check("S-13: WiFi SVG block locatable", False, "couldn't extract <svg>…</svg> from #wifi-btn")
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
# S-6: gate must be === false specifically — using !data.freedata_installed
# would also hide the section on legacy status payloads missing the field.
check("S-6: freedata gate uses strict === false (not falsy check)",
      "freedata_installed === false" in src,
      "found freedata_installed reference but not the strict `=== false` comparison "
      "— risks hiding FreeDATA on legacy payloads that don't yet carry the field")

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
# S-11 — WikiMed recommended entry must have zimPattern to match on-disk filename
# ---------------------------------------------------------------------------
section("S-11 — WikiMed zimPattern")

check("WikiMed RECOMMENDED_ZIMS entry has zimPattern field",
      bool(re.search(r'kiwixName:\s*["\']wikipedia_en_medicine["\']', src)) and
      bool(re.search(r'zimPattern:\s*["\']wikimed["\']', src)),
      "zimPattern: 'wikimed' missing from WikiMed entry — "
      "installed wikimed-mini.zim will never be filtered from the recommended list")

# ---------------------------------------------------------------------------
# S-13 — WiFi icon has exactly 1 circle + 2 arc paths (dot + 2 arcs, like iOS)
# ---------------------------------------------------------------------------
section("S-13 — WiFi SVG arc count")

wifi_svg_match = re.search(
    r'id=["\']wifi-btn["\'][^>]*>.*?</button>', src, re.DOTALL
)
if wifi_svg_match:
    wifi_svg = wifi_svg_match.group(0)
    circle_count = len(re.findall(r'<circle\b', wifi_svg))
    path_count   = len(re.findall(r'<path\b', wifi_svg))
    check("WiFi SVG has exactly 1 circle (dot)", circle_count == 1,
          f"found {circle_count} — expected 1 dot")
    check("WiFi SVG has exactly 2 arc paths (iOS-style: dot + 2 arcs)",
          path_count == 2,
          f"found {path_count} — remove outermost arc to match iOS icon")
else:
    check("WiFi button SVG found", False, "wifi-btn button not found in HTML")

# ---------------------------------------------------------------------------
# S-14 — VNC URLs contain resize=remote for dynamic viewport resizing
# ---------------------------------------------------------------------------
section("S-14 — VNC remote resize")

check("JS8Call noVNC URL contains resize=remote",
      bool(re.search(r"vnc\.html[^'\"]*resize=remote", src)),
      "resize=remote missing — VNC will open letterboxed, not full-viewport")
check("FreeDATA noVNC URL contains resize=remote",
      len(re.findall(r"vnc\.html[^'\"]*resize=remote", src)) >= 2,
      "only one VNC link has resize=remote — check FreeDATA button too")

# ---------------------------------------------------------------------------
# S-15 — Kiwix upstream catalog browse (search box + handler)
# ---------------------------------------------------------------------------
section("S-15 — Kiwix catalog browse/search")

check("kiwix-search-input element present", "kiwix-search-input" in src,
      "search input missing — Manage Books panel has no browse capability")
check("onKiwixSearchInput function defined", has_fn("onKiwixSearchInput"),
      "handler missing — search input won't trigger search")
check("kiwixSearch queries library.kiwix.org OPDS (catalog/v2/entries?q=)",
      "library.kiwix.org/catalog/v2/entries?q=" in src,
      "catalog search URL missing — kiwixSearch function may not have been added")

# ---------------------------------------------------------------------------
# S-16 — Mobile first-run tips card
# ---------------------------------------------------------------------------
section("S-16 — Mobile tips card")

check("#mobile-tips element present", has_id("mobile-tips"),
      "mobile-tips card missing from HTML")
check("dismissMobileTips function defined", has_fn("dismissMobileTips"),
      "dismiss handler missing")
check("mcomz_mobile_tips_seen localStorage key used",
      "localStorage.getItem('mcomz_mobile_tips_seen')" in src or
      "localStorage.getItem(\"mcomz_mobile_tips_seen\")" in src,
      "localStorage check missing — tips card will re-appear on every visit")
check("mobile-tips shown only on narrow screens (max-width check)",
      "max-width" in src and "mobile-tips" in src and "700" in src,
      "viewport-width guard missing — tips card might appear on desktop too")

# ---------------------------------------------------------------------------
# S-19 — Brand icons in service card headers
# ---------------------------------------------------------------------------
section("S-19 — Brand icons")

for icon_file, label in [
    ("mumble.svg",           "Mumble (Voice & Text)"),
    ("meshcore.svg",         "MeshCore"),
    ("meshtastic-mpwrd.svg", "Meshtastic M-PWRD"),
    ("js8call.svg",          "JS8Call"),
    ("pat.png",              "Pat/Winlink"),
    ("freedata.png",         "FreeDATA"),
]:
    check(f"S-19: /icons/{icon_file} referenced in HTML ({label})",
          f"/icons/{icon_file}" in src,
          f"brand icon for {label} missing — add <img src=/icons/{icon_file}> to the card header")

icons_dir = html_path.parent / "icons"
check("S-19: icons/ directory exists",
      icons_dir.is_dir(),
      f"expected directory at {icons_dir}")

for icon_file in ("mumble.svg", "meshcore.svg", "meshtastic-mpwrd.svg",
                  "js8call.svg", "pat.png", "freedata.png"):
    check(f"S-19: icons/{icon_file} exists on disk",
          (icons_dir / icon_file).exists(),
          f"file missing — download it and place in src/dashboard/icons/")

check("S-19: LICENSES.md present in icons/ dir",
      (icons_dir / "LICENSES.md").exists(),
      "attribution file missing — add LICENSES.md")

# Invert filter applied to monochrome logos (all except Meshtastic M-PWRD which is full-colour)
_mono_icons = ["mumble.svg", "js8call.svg", "pat.png", "freedata.png"]
for icon_file in _mono_icons:
    _pat = re.escape(icon_file) + r'[^>]*filter\s*:\s*brightness\(0\)\s*invert\(1\)'
    check(f"S-19: {icon_file} has brightness(0) invert(1) filter (light bg → white)",
          bool(re.search(_pat, src)),
          f"missing invert filter on {icon_file} — will render dark on dark background")

# Meshtastic M-PWRD must NOT have the invert filter (it's a full-colour badge)
_mpwrd_ctx = re.search(r'meshtastic-mpwrd\.svg[^>]*>', src)
if _mpwrd_ctx:
    check("S-19: meshtastic-mpwrd.svg does NOT have invert filter (full-colour badge)",
          "invert" not in _mpwrd_ctx.group(0),
          "M-PWRD badge is already full-colour — don't invert it")
else:
    check("S-19: meshtastic-mpwrd.svg img tag present", False, "img tag not found in src")

# All brand icon img tags must have onerror fallback
check("S-19: brand icon img tags have onerror fallback",
      src.count('onerror="this.style.display=') >= 6 or
      src.count("onerror='this.style.display=") >= 6 or
      src.count('onerror="this.style.display=\'none\'"') >= 6,
      "icon <img> tags should include onerror='this.style.display=\"none\"' so missing icons don't break layout")

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
