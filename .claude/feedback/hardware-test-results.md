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

## v0.0.2-pre-alpha.22 — RPi 5, 2026-04-17

### Smoke test: 72/73 (automated, mcomz.local)

Only failure: **WikiMed ZIM not yet registered** — `mcomz-wikimed-download.service` is running on first boot. The `Restart=on-failure` + `RestartSec=30` fix (shipped this session) should handle DNS-not-ready failures automatically. Expect the check to pass ~2–5 minutes after first boot once DNS is up and download completes.

### Confirmed working (automated smoke test)

| Area | Result |
|------|--------|
| HTTP + HTTPS dashboard | ✅ Both 200, full dashboard content |
| All services present in /api/status | ✅ |
| Kiwix slug routing (S-4) | ✅ All 3 MComz ZIMs registered with correct slugs; content fetches by slug all 200 |
| Kiwix ZIM titles | ✅ `mcomz-survival \| Mcomz Survival \| 181785593` etc. (filename-derived titles working) |
| OPDS catalog | ✅ 200 + Atom XML |
| MeshCore offline flasher | ✅ `/meshcore-flash/` returns 200 with flasher content |
| noVNC page | ✅ 200 with "noVNC" content |
| Xvnc port 5901 | ✅ Accepting connections |
| websockify WebSocket upgrade | ✅ 101 Switching Protocols |
| Pat HTTPS :8081 | ✅ 200 (302→200) |
| Mumble-web static | ✅ 200 |
| Mumble WebSocket | ✅ 405 (endpoint present) |
| WiFi/AP APIs | ✅ |
| System control endpoints | ✅ |
| FreeDATA `freedata_installed` field | ✅ API returns `false` on ARM64 — section hidden in dashboard |
| RECOMMENDED_ZIMS catalog names | ✅ All 4 resolve on kiwix.org |

### Issues found / still pending

| # | Area | Symptom | Status |
|---|------|---------|--------|
| 1 | WikiMed download | Not yet registered at smoke-test time | ⏳ Expected — awaiting first-boot download completion |
| 2 | SSH password auth | `ssh-copy-id` fails — `Permission denied (publickey,password)` on new image | 🔍 Unknown — playbook may have hardened sshd; needs investigation |
| 3 | meshtasticd | Status `failed` without hardware → shows `err` badge (not `std`) | ⬜ renderStatus checks `failed` before `HW_SVCS` — hardware-absent services show scary red badge. Low priority. |
| 4 | direwolf | Status `activating` without sound hardware | ⬜ Expected — B-3 diagnostic still pending |
| 5 | VNC spinner | noVNC stuck on spinner — VncAuth password dialog hidden behind loading overlay | ✅ Fixed live: SecurityTypes None; noVNC auto-connects. See fix log `2026-04-17-9869880-vnc-no-auth.md` |
| 6 | JS8Call in VNC | JS8Call process confirmed running (`js8call` + `/usr/bin/js8` in VNC cgroup); window visibility unconfirmed | ⏳ Needs user to open noVNC and confirm |
| 7 | Pat send/receive | UI confirmed reachable; full send/receive on real radio not tested | ⏳ Needs real-radio test |
| 8 | Mumble mic | `getUserMedia` requires HTTPS — mic still unusable over HTTP | ⬜ Known/won't fix without HTTPS trust story |

---

## v0.0.2-pre-alpha.21 — RPi 5, 2026-04-16

### Confirmed working

| # | Area | Result |
|---|------|--------|
| 1 | Mumble text | Login and messaging work in Safari Mac ✅ |
| 2 | Pat/Winlink | UI loads; reaches NOCALL callsign setup window ✅ |
| 3 | VNC/noVNC | Loads and connects; Xvnc fix confirmed ✅ |

### Issues found

| # | Area | Symptom | Diagnosis | Status |
|---|------|---------|-----------|--------|
| 1 | Mumble WebSocket Bridge | Status grid shows `err` despite text chat working | Health check may be hitting the wrong endpoint or a timing issue; not a full outage | ⬜ Investigate |
| 2 | Mumble microphone | `NotSupportedError: MediaStreamError` on Safari Mac | Known limitation — `getUserMedia` requires HTTPS; HTTP dashboard can't grant mic access | ⬜ Known / won't fix without HTTPS trust story |
| 3 | All 3 MComzOS ZIMs | Dashboard shows "Not Found" for all three | mcomz-wikimed-download.service was still running during test (Appropedia downloading); Kiwix may not have indexed ZIMs yet | ⬜ Recheck after service completes |
| 4 | Kiwix content UUID 404 | Smoke test hits `/library/content/<uuid>/` → 404 for all books | Root cause diagnosed via SSH: kiwix-serve serves content at `/library/content/<slug>/` (slug derived from ZIM filename), not UUID. Slug URLs return 302→200. Smoke test and dashboard both use wrong URL pattern. Secondary issue: all ZIM metadata (title, language, article count) empty in OPDS — MComz ZIMs not built with internal metadata | 🔴 Code fix needed: status API + smoke test + dashboard |
| 5 | MeshCore flash — online routing | Hub is online; clicking Flash MeshCore routes to local `/meshcore-flash/` instead of `flasher.meshcore.co.uk` | `fetch(...favicon.ico, {method:'HEAD'})` fails due to CORS even when online; `.catch()` always fires → always routes offline. Fix: add `mode:'no-cors'` to probe. **Fixed in this session** (`index.html:702`) | ✅ Fixed — needs reflash to verify |
| 6 | /meshcore-flash/ | Returns `403 Forbidden nginx` | Git clone of web flasher failed during CI build; rescue block ran silently; empty directory, no `index.html` | 🔴 Build provisioning — check CI logs |
| 7 | JS8Call in noVNC | VNC password prompt never appeared on HTTP; JS8Call crashed with `Cannot access /home/mcomz/.config/JS8Call.ini for writing` | Two issues found via SSH: (a) VNC only works on HTTPS (over HTTP the auth flow fails silently); (b) `/home/mcomz/.config/` owned by `root:root` — mcomz user can't create JS8Call.ini. **Both fixed this session**: `.config` chowned live + playbook fix at `site.yml:289`. JS8Call confirmed loading after fix | ✅ Fixed — needs reflash to confirm playbook fix |
| 8 | FreeDATA | Connect button loops, no "unavailable" message | ARM64: no AppImage, service skipped by playbook; UI still shows the button. No change this session | ⬜ UI should indicate unavailability on ARM64 |

### Smoke test gaps identified

| Gap | Impact |
|---|--------|
| All 3 MComzOS ZIMs not individually checked | "at least one" check passes even if two are missing |
| WikiMed checked only by keyword, not UUID content | ZIM can be registered but content can 404 without smoke test failing |
| `/meshcore-flash/` not checked | 403 undetected by automated test |
| JS8Call / noVNC auth not exercised | Can't detect auth-popup regression |
| FreeDATA ARM64 skip not verified | No check that ARM64 build gracefully hides the UI |

### §2 verification results (from this session)

| §2 item | Outcome |
|---------|---------|
| MeshCore offline flasher 403 → recursive www-data chown (`site.yml:1381-1389`) | ❌ Still 403 — root cause was not permissions but missing files (git clone failed in CI, rescue fired) |
| RECOMMENDED_ZIMS + first-boot WikiMed — real catalog names | ❌ Partial — ZIMs downloading but Kiwix content endpoint returning 404 on registered UUID; all 3 MComz ZIMs show Not Found |
| VNC websockify upgrade — smoke test added | ✅ Smoke test passes; WebSocket upgrade confirmed live |
| VNC Connect button — Requires=/StartLimit/port-ready loop | ❌ noVNC connects but VNC auth dialog never appears; JS8Call window not visible |

---

## v0.0.2-pre-alpha.19 — RPi 5, 2026-04-12

**Verbatim feedback:**

> "the smoke-test.py needs to be fixed as it is not detecting that all three MComz ZIMs are unaccessible. System Status (v0.0.2-pre-alpha.19) — std WiFi Access Point / std DHCP/DNS / on mDNS (.local) / on Voice & Text (Mumble) / on Mumble WebSocket Bridge / err Meshtastic / std MeshCore / on Offline Library / on Winlink Email (Pat) / act APRS (Direwolf) / std HF Modem (ardopcf) / on Remote Desktop / on VNC WebSocket Bridge / on Web Server — this is a big improvement but while the cursor changes to ? over the traffic light text it takes a very long time for the tooltip to appear, to the extent that I thought it wasn't appearing for most.
>
> Books that are already installed should not appear in the recommended list until you uninstall them. It would be useful to include the installed size of all installed ZIMs. All recommended ZIMs now give 'URL must point to a .zim file' errors bar the MComz ZIMs which apparently can be installed — compare https://download.kiwix.org/zim/wikipedia/ with https://github.com/mcomz-org/MComzLibrary/releases/download/v2026.04.11/MComz-Survival.zim
>
> I am unable to connect to MComzOS using Safari again, the Visit Website button after the warning, just takes you back to the 'This Connection Is Not Private' screen. iOS Chrome seems to work. Can we have the Licensed radio capabilities after the mesh capabilities? JS8Call used to at least open with this, but it is now consistently just looping from connect button to connect button without ever showing the log in modal. Same with FreeDATA. Can we include these in the smoke-test.py? Pat seems to work as usual. The WiFi icon is clipped at the top.
>
> Hotspot selection now works, well done, but in hotspot mode Flash MeshCore takes us to https://flasher.meshcore.co.uk/ which fails without internet. It is good to go there when internet is available but can we at least have the Heltec v4 repeater and node flashers available offline when there is no internet access?"

### Issues found

| # | Area | Symptom | Diagnosis | Fix target |
|---|------|---------|-----------|------------|
| 1 | smoke-test | "At least one MComzLibrary ZIM present" shows ✅ but detail says "none found" | Detail string always shown regardless of pass/fail; also smoke-test doesn't verify ZIM reader URLs are accessible, only that ZIMs are registered | Claude fix |
| 2 | System Status | Tooltip delay — cursor shows ? but tooltip takes very long to appear | CSS/JS tooltip timing (likely `title` attribute with long hover delay) | Vibe |
| 3 | Library panel | All 3 MComz ZIMs inaccessible from new library panel | Panel generates `/library/A/<filename>/` but kiwix-serve uses UUIDs, not filenames | Vibe |
| 4 | Library — Manage Books | Installed books appear in recommended list | No filter comparing installed paths/titles against RECOMMENDED_ZIMS | Vibe |
| 5 | Library — Manage Books | All kiwix.org recommended ZIMs give "URL must point to a .zim file" | Recommended entries use directory URLs (e.g. `.../zim/wikipedia/`), not direct dated `.zim` file URLs | Vibe |
| 6 | Library — Manage Books | No installed ZIM sizes shown | API may not return size field, or UI not rendering it | Vibe |
| 7 | iOS Safari | "Visit Website" after cert warning loops back to same warning | Possible HSTS cached from previous session, or iOS Safari HTTPS-upgrade feature; iOS Chrome (same WebKit) works fine; nginx has no redirect or HSTS header in config | Vibe/investigate |
| 8 | Dashboard layout | Licensed Radio card appears before Mesh card | Wrong order in HTML | Vibe |
| 9 | VNC / JS8Call | Connect button loops without ever showing VNC auth modal | Regression — used to at least show auth dialog; Xvnc fix in .17 may not have landed correctly | Vibe |
| 10 | VNC / FreeDATA | Same looping behaviour as JS8Call | Same root cause | Vibe (same fix) |
| 11 | WiFi icon | Icon clipped at top of button | CSS overflow/padding issue | Vibe |
| 12 | Hotspot mode | "Flash MeshCore" links to flasher.meshcore.co.uk — fails without internet | URL is always the live flasher; needs offline fallback | Vibe + site.yml |
| 13 | WikiMed Mini | Still not provisioned (smoke-test ❌) | Download during chroot build still timing out or failing | Vibe (site.yml) |
| 14 | Hotspot stop | Hub didn't reconnect to router WiFi after AP stop | Existing known bug — reconnect logic needs improvement | Vibe (carried from .16) |
| 15 | Pat | Works as usual ✅ | — | — |
| 16 | Hotspot start | Works ✅ | — | — |
| 17 | Mumble | Not explicitly tested this session | — | — |

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
