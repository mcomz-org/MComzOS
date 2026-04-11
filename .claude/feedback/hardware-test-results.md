# MComzOS Hardware Test Results

Verbatim user feedback per release, followed by issue interpretation.

---

## v0.0.2-pre-alpha.11 — RPi 5, 2026-04-09

**Verbatim feedback:** *(from session context — first live hardware test)*

### Issues found
| # | Service | Symptom | Root cause | Status |
|---|---------|---------|------------|--------|
| 1 | Kiwix | CSS/images broken | `--urlRootLocation /library` missing from kiwix-serve ExecStart | ✅ Fixed pre-alpha.12 |
| 2 | Pat | Fails to start | `mcomz_user=pi` hardcoded in CI extra-vars; service files referenced non-existent `pi` user | ✅ Fixed pre-alpha.12 |
| 3 | Mumble WebSocket bridge | WebSocket fails | npm global path wrong; nginx WebSocket routing missing `--web` separation | ✅ Fixed pre-alpha.12 |
| 4 | AP hotspot button | Stuck on "Starting…" | No timeout — connection drop killed the fetch, leaving button frozen | ✅ Fixed pre-alpha.12 |
| 5 | nginx | Doesn't start on first boot | `deb-systemd-helper` defers enable in chroot; no actual symlink created | ✅ Fixed pre-alpha.12 |

---

## v0.0.2-pre-alpha.13 — RPi 5, 2026-04-09

### Issues found
| # | Service | Symptom | Root cause | Status |
|---|---------|---------|------------|--------|
| 1 | iOS Safari | Refuses to open HTTPS | Self-signed cert was 3650 days; iOS 14+ hard-blocks certs with validity > 398 days | ✅ Fixed pre-alpha.14 (397 days) |
| 2 | Kiwix | `/libraryINVALID URL` 404 | nginx `proxy_pass` stripped `/library/` prefix; kiwix-serve with `--urlRootLocation /library` expects full path | ✅ Fixed pre-alpha.14 |
| 3 | VNC Connect button | Does nothing | `Requires=mcomz-vnc` in mcomz-novnc caused novnc to stop when VNC restarted and never recover | ✅ Fixed in code (needs hardware verification) |
| 4 | Mumble controls greyed on macOS Chrome | Greyed out | `mcomz-mumble-ws` absent from SERVICES dict → status invisible; root cause suspected SSL crash in websockify on Python 3.12 | ✅ Fixed pre-alpha.16 (`server_hostname='localhost'` added) |
| 5 | Meshtastic / MeshCore | 502 Bad Gateway | Services off (no LoRa hardware); dashboard opened page directly | ✅ Fixed pre-alpha.16 (inline guard + `target="_blank"`) |
| 6 | hostapd / dnsmasq | Showing "off" in status | Correct behaviour (AP only activates when needed) but confusing | ⬜ UX — add tooltip/note |

---

## v0.0.2-pre-alpha.16 — RPi 5, 2026-04-11

**Verbatim feedback:**

> "Installed .16 (it would be useful for confirmation to be able to see the current version. Perhaps after the System Status title could come a non-bold (MComzOS vX.Y.Z, with a link to the latest release in the repo). off WiFi Access Point / off DHCP / DNS / on mDNS (.local) / on Voice & Text (Mumble) / on Mumble WebSocket Bridge / off Meshtastic / off MeshCore / on Offline Library / on Winlink Email (Pat) / off APRS (Direwolf) / off HF Modem (ardopcf) / on Remote Desktop / on VNC WebSocket Bridge / on Web Server
>
> KIWIX is working reasonably in macOS Chrome, but I can only see book covers in iOS chrome for the PDF books although the HTML ones work fine, iOS safari still won't open MComzOS. Also it gives '3 book(s)' in its front page and then shows three large squares, each marked only with an identical `?`, these are just our three ZIMs - there is no WikiMed. Its languages and categories dropdowns are empty, and its search functionality doesn't work. Most books in the MComz-Survival.md appear to be PDF only with no HTML or EPUB version that I can see. Error 'Failed to load PDF document' is given by excretia-disposal. MComz-Literature and MComz-Scripture seem to work as HTML versions fine although Arabian Knights is actually `THE WHEELS OF CHANCE; A BICYCLING IDYLL`
>
> Mumble seems to work as before. Winlink email appears to open into an email client which I have yet to fully test. JS8Call and FreeDATA have the same problem as before - the username modal never opens when you click Connect in the noVNC opening screen. Meshtastic and MeshCore gave the usual errors at first, but now give the helpful 'MeshCore is not connected — attach your LoRa radio and reload.' Reboot works then gives an ERR_CONNECTION_REFUSED then works and gets to the front page.
>
> Hotspot worked - well done. On Stop Hotspot I couldn't get back into MComz, still waiting - do I need to reboot?"

### Issues found
| # | Service | Symptom | Root cause | Fix target |
|---|---------|---------|------------|------------|
| 1 | Dashboard | No version shown | Not implemented | pre-alpha.17 |
| 2 | Kiwix | "3 book(s)" with `?` thumbnails | ZIM illustration PNG (48×48 solid blue) not readable by kiwix-serve as book art; metadata display issue | pre-alpha.17 |
| 3 | Kiwix | No WikiMed Mini | Download task ran during build but 155 MB download likely timed out or failed in chroot | pre-alpha.17 — investigate |
| 4 | Kiwix | Empty dropdowns, search broken | ZIMs not built with `--withFullTextIndex` flag (zimwriterfs default does not index) | pre-alpha.17 (MComzLibrary) |
| 5 | Kiwix | "excreta-disposal" PDF error | File present from cached previous build; removed from download script, cache miss will clear it | pre-alpha.17 (source cache will invalidate) |
| 6 | Kiwix | Arabian Nights = Wheels of Chance | Wrong PG number in download script — PG #1264 is H.G. Wells, Andrew Lang's Arabian Nights is PG #128 | pre-alpha.17 (MComzLibrary) |
| 7 | Kiwix | PDFs can't be viewed on iOS Chrome | iOS Chrome cannot display inline PDF; browser limitation — PDFs need download link | ⬜ Low priority / platform limitation |
| 8 | iOS Safari | Cannot open MComzOS at all | HTTP→HTTPS redirect forces Safari onto self-signed cert which iOS rejects; SAN is correct but self-signed certs require manual trust install on iOS | pre-alpha.17 — serve dashboard on HTTP too |
| 9 | VNC / JS8Call | noVNC "Connect" shows but VNC auth dialog never appears | Likely: `vncserver -fg` Perl wrapper not reliable as systemd service; need to run Xvnc directly | pre-alpha.17 |
| 10 | Hotspot stop | Can't reconnect after stopping AP | `ap_stop()` calls `nmcli device connect` but NM needs time to reassociate; no reconnect feedback in UI | pre-alpha.17 |
| 11 | Winlink (Pat) | Untested | Opens email client UI, functional TBC | ⬜ User to test |
| 12 | Mumble | Working ✅ | — | — |
| 13 | Meshtastic / MeshCore offline guard | Working ✅ | — | — |
| 14 | Reboot | Working ✅ (ERR_CONNECTION_REFUSED then recovers) | Expected — brief gap before nginx restarts | — |
| 15 | Hotspot start | Working ✅ | AP button now creates MComzOS SSID reliably | — |
