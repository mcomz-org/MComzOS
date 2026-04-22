# MComzOS Manual Tests

Hands-on hardware checklist — covers only what requires eyes, ears, or physical interaction. Run `tests/smoke-test.py` first; if it passes 100%, everything it covers can be assumed green and the items below are all that remain.

Record pass/fail and notes against the release version in `.claude/feedback/hardware-test-results.md`.

---

## 0. Setup

- [ ] Flash `mcomzos-rpi.img.xz` to SD card using Raspberry Pi Imager
- [ ] Insert SD card, connect ethernet to a router, power on
- [ ] Wait ~60 s for first boot to complete

---

## 1. Basic Connectivity

- [ ] **iOS Safari (HTTP)** — open `http://mcomz.local` on iPhone/iPad — dashboard loads without any certificate prompt
- [ ] **iOS Safari (HTTPS)** — open `https://mcomz.local` on iPhone/iPad — Safari shows a cert warning; tap "Visit Website" (or "Continue"); the full dashboard loads. **Known limitation:** Safari's HTTPS-first upgrade can still send users here; the recommended URL remains `http://mcomz.local/`
- [ ] **Version display** — System Status card shows the correct release version with a link
- [ ] **S-16 Mobile first-run tips** — open dashboard on iPhone in Safari with site data cleared (Settings → Safari → Clear) → "📱 First-time tips (mobile)" card visible at top → tap **Dismiss** → reload page → card hidden
- [ ] **S-16 Desktop unaffected** — open dashboard on a >700px desktop browser → tips card NOT visible regardless of localStorage state

---

## 2. System Status Card

- [ ] **Standby notes** — hostapd and dnsmasq show "(standby — activates with hotspot)" in the UI
- [ ] **Auto-refresh** — status badges visibly update every ~15 seconds (watch for flicker)

---

## 3. Offline Library (Kiwix)

- [ ] Each ZIM shows a title and thumbnail (not a `?` square)
- [ ] **Search** — type a word in the Kiwix search box; results appear (not empty)
- [ ] **Language/Category dropdowns** — not empty; show at least one option
- [ ] Open a book from MComz-Literature — HTML content loads correctly
- [ ] Open a book from MComz-Scriptures — HTML content loads correctly
- [ ] **Arabian Nights** — confirm title is "The Arabian Nights" (Andrew Lang), not "The Wheels of Chance"
- [ ] **WikiMed Mini** — search for a medical term (e.g. "fracture") inside WikiMed — results appear
- [ ] **iOS Chrome** — open a HTML book on iPhone — renders correctly
- [ ] **PDF note** — PDF-only books show a note about downloading rather than an inline render failure

### Manage Books panel
- [ ] Remove a book — it disappears from the list and from Kiwix after reload
- [ ] Add by URL — paste a valid .zim URL, click Download & Add, progress updates, book appears when done
- [ ] "Use this URL" buttons on recommended ZIMs fill the URL field correctly
- [ ] **S-15 Browse Kiwix Library** — type "appropedia" in the new search box → at least one result appears within ~1s → click "Get URL" → URL field populates → Download & Add proceeds normally
- [ ] **S-15 Offline graceful failure** — disable internet → search returns "Search failed — are you online?" rather than spinning forever

---

## 4. Voice & Text Chat (Mumble)

- [ ] **Join Channel** button opens mumble-web in browser
- [ ] Enter a name, leave password blank, press Connect — connects without error
- [ ] "How to use" collapsible expands and collapses
- [ ] **macOS Chrome** — Mumble controls are not greyed out
- [ ] **Voice** — microphone works on HTTPS; voice-activated audio transmits to another connected client
- [ ] **Text** — type a message, press Enter, message appears in chat
- [ ] **iOS note** — how-to says to use Safari (Chrome blocks mic on iOS)

---

## 5. Licensed Radio (collapsed card)

### JS8Call (Remote Desktop / VNC)
- [ ] "Open JS8Call" opens noVNC; noVNC connects and JS8Call desktop loads inside the browser window (no password dialog — VNC runs without auth)
- [ ] **S-14 Remote Resizing** — VNC desktop fills the browser viewport on connect (no black letterbox bars); resizing the browser window resizes the desktop within ~1s
- [ ] **S-14 Fullscreen hint** — small "Press F for fullscreen · click to dismiss" banner visible at the bottom of the noVNC page; pressing **F** enters browser fullscreen; clicking the banner removes it
- [ ] **With radio hardware** — JS8Call decodes an incoming JS8 frame and transmits successfully

### Pat (Winlink Email)
- [ ] "Open Pat — Winlink Email" opens the Pat web UI and it loads without error
- [ ] **With radio hardware (after JS8Call verified)** — send and receive a Winlink message over the air

### FreeDATA
- [ ] "Open FreeDATA" opens noVNC (or shows "may not be installed" note if unavailable)
- [ ] **S-14 Remote Resizing** — same checks as JS8Call (resize, fullscreen banner)

---

## 6. Mesh Communication (collapsed card)

- [ ] **Without LoRa hardware** — clicking MeshCore shows the inline warning mentioning BLE setup ("attach a USB radio, or expand 'Configure BLE radio' below…"); clicking Meshtastic shows the simpler "attach your LoRa radio" warning
- [ ] **With LoRa hardware** (if available) — Meshtastic and MeshCore UIs load correctly
- [ ] **MeshCore USB radio** — plug a MeshCore USB radio (e.g. Heltec V4) into the Pi, wait ~20 s, reload dashboard; MeshCore Dashboard link opens the NiceGUI UI (not a 502)
- [ ] **MeshCore BLE setup — scan** — on a Pi with BlueZ running, expand "Configure BLE radio", click "Scan for BLE radios"; after ~8 s a list of nearby BLE devices appears (MeshCore radios should show with recognisable names)
- [ ] **MeshCore BLE setup — connect** — click Connect on a MeshCore BLE radio; "Current BLE radio: AA:BB…" appears; within ~20 s the MeshCore service restarts and `/meshcore/` loads the NiceGUI UI
- [ ] **MeshCore BLE setup — manual MAC** — expand "Enter MAC manually", type a valid MAC, click Set; saves successfully. Type an invalid MAC → alert "MAC must be in the form AA:BB:CC:DD:EE:FF"
- [ ] **MeshCore BLE setup — clear** — with a BLE radio configured, click "Clear BLE config", confirm the prompt; "No BLE radio configured" appears, service restarts
- [ ] **Flash MeshCore (online)** — with normal WiFi active, click "Flash MeshCore"; browser opens `https://flasher.meshcore.co.uk/` (live flasher)
- [ ] **Flash MeshCore (offline)** — enable hotspot (no internet), click "Flash MeshCore"; browser opens `http://mcomz.local/meshcore-flash/`; flasher UI loads; Heltec V3/V4 firmware options appear in the selector; if a Heltec radio is available, complete a flash and confirm it boots

---

## 7. WiFi Panel

- [ ] **Scan** — "Scan" button triggers scan; nearby networks appear in list
- [ ] **Connect** — tap a network, enter password, hub connects and status updates
- [ ] **Forget** — saved networks list shows known networks; Forget button removes one

---

## 8. WiFi Hotspot (AP Mode)

- [ ] **Start Hotspot** — hub creates "MComzOS" WiFi network; page shows connection guidance
- [ ] From a phone: connect to "MComzOS" (password: `mcomzos1`); `http://192.168.4.1` loads dashboard
- [ ] **Stop Hotspot** — hub reconnects to router within 30 s; `http://mcomz.local` accessible again from laptop

---

## 9. AP Auto-Fallback (5-minute timer)

- [ ] Disconnect hub from all networks
- [ ] Wait 5+ minutes — "MComzOS" hotspot appears
- [ ] Connect and load `http://192.168.4.1` — dashboard loads

---

## 10. Reboot & Shutdown

- [ ] **Reboot** — confirm dialog appears; hub reboots; dashboard accessible again after ~60 s
- [ ] **Shutdown** — confirm dialog appears; hub powers off

---

## 11. Kiosk Mode (physical display)

- [ ] Connect HDMI monitor, USB keyboard and mouse; power on
- [ ] Hub boots to full-screen Chromium showing dashboard — no login prompt
- [ ] Dashboard is interactive; screen does not blank within 5 minutes; cursor hides after 5 s idle

---

## 12. Theme — Kiwix dark-mode viewer

- [ ] **Dashboard unchanged** — `http://mcomz.local/` renders identically to pre-alpha.22: dark background, dark cards, no visual regression
- [ ] **Kiwix index dark** — click any ZIM in the library panel → `http://mcomz.local/library/` shows: dark `#121212` background, dark book tiles, no grey 1995-era header bar
- [ ] **Search bar style** — search input inside Kiwix is a rounded pill (border-radius ~999px), not a square box; placeholder text is grey
- [ ] **Home/random icons** — toolbar icons are white/light (inverted), not dark-on-grey
- [ ] **Viewer chrome dark** — open `https://mcomz.local/library/viewer#mcomz-scriptures/berean-standard-bible.html`; top toolbar is dark (no light grey `#F4F6FB` bar), text is legible
- [ ] **Viewer toolbar colour** — DevTools computed style on `#kiwixtoolbar.ui-widget-header` shows `background-color: rgb(30, 30, 30)` — confirms `var(--panel)` won over jQuery UI gradient
- [ ] **Viewer search input dark (S-9)** — DevTools on `#kiwixsearchbox` shows `background-color: rgb(34, 34, 34)`; visually a dark pill, not a white box
- [ ] **Viewer home/random buttons dark (S-9)** — DevTools on `#kiwix_serve_taskbar_library_button button` shows `background-color: rgb(34, 34, 34)`; emoji visible against dark background
- [ ] **Language-selector icon inverted (S-9)** — `#uiLanguageSelectorButton` icon appears light/inverted, not dark-on-light
- [ ] **No giant broken-image glyph (S-9)** — book header card on `/library/viewer#…` shows no broken-image glyph wider than 128px (illustration endpoint 404s on MComzLibrary ZIMs)
- [ ] **Library index filter dropdowns (S-9)** — visit `/library/`; the language/category select dropdowns at the top render dark, not light
- [ ] **Icons crisp** — small icons in the viewer toolbar are crisp (not artifacted, not squashed, not blurry); jQuery UI sprite appears as light/white icons on dark background
- [ ] **jQuery UI buttons** — Home / random / fullscreen buttons render as dark pills; hover feedback visible (slightly lighter on hover)
- [ ] **Home button works** — click home icon in viewer → returns to `/library/` book list (still dark)
- [ ] **iOS Safari dark mode** — open `http://mcomz.local/library/` on iPhone; no flash of grey/white on load; background is dark
- [ ] **Responsive** — resize browser narrow → search bar doesn't overflow header

---

## 13. VNC Remote Resize + Fullscreen (S-14)

- [ ] Click "Open JS8Call" → noVNC opens in a new tab
- [ ] After VNC connects, the remote desktop **resizes to fill the browser viewport** (no black bars) — confirms `resize=remote` is active
- [ ] A dark dismissable banner appears at the bottom: "Press **F** for fullscreen · click to dismiss"
- [ ] Press **F** — browser enters fullscreen; VNC fills the screen
- [ ] Click the banner — it disappears and does not reappear until the next page load
- [ ] Same behaviour for "Open FreeDATA" button (on x86 where FreeDATA is installed)

---

## 14. Kiwix Catalog Browse (S-15)

- [ ] Open Manage Books panel (＋ Manage Books button)
- [ ] A "Browse Kiwix library" search box is visible above the Recommended list
- [ ] **Online:** type "appropedia" → after a short pause, results appear showing Appropedia entries with sizes and "Get URL" buttons
- [ ] **Get URL:** click "Get URL" on any result → URL field fills; Download & Add works normally
- [ ] **Offline:** disconnect hub from internet; type a query → "Search failed — are you online?" message appears (graceful failure, no crash)
- [ ] Short queries (< 3 chars) show no results and no error

---

## 15. Mobile First-Run Tips (S-16)

- [ ] On an iPhone/iPad in Safari: clear site data for `mcomz.local` (Settings → Safari → Advanced → Website Data), then reload `http://mcomz.local/`
- [ ] A "📱 First-time tips (mobile)" card appears near the top of the dashboard
- [ ] Card lists WiFi, Offline Library, Mumble, Mesh/Radio, and Rotate tips
- [ ] Tap **Dismiss** → card hides immediately
- [ ] Reload the page → card does **not** reappear (localStorage persists the dismissal)
- [ ] On a desktop browser: card is never shown (narrow-screen only, ≤ 700 px wide)

---

## 16. Diagnostics Mode (diagnostics builds only)

Only applies when the image was built with `diagnostics_mode=true` (currently all builds).

- [ ] **Splash screen appears** — open `http://mcomz.local/`; a full-screen orange-bordered warning modal appears explaining SSH credentials and risks
- [ ] **Dismiss persists** — click "Understood — Dismiss"; modal closes and does not reappear on page refresh within the same browser session
- [ ] **DIAG badge visible** — after dismissing the splash, a small orange `⚠ DIAG` badge is visible in the header; clicking it re-shows the modal
- [ ] **SSH key access** — from the development machine: `ssh -i .claude/diagnostics/mcomzos_diag mcomz@mcomz.local` — logs in without a password prompt
- [ ] **SSH password access** — `ssh mcomz@mcomz.local` (password `mcomzdiag`) — logs in successfully
- [ ] **API readable over HTTP** — `curl http://mcomz.local/api/status` returns JSON with `"diagnostics_mode": true`
- [ ] **Disable diagnostics** — `sudo rm /etc/mcomzos-diagnostics && sudo reboot`; after reboot, splash does not appear and DIAG badge is absent; SSH password auth still works until next image flash

---

## 17. Brand Icons (S-19)

- [ ] **Voice & Text Chat card** — Mumble icon visible to the left of "Voice & Text Chat" heading; icon is white/light, not dark
- [ ] **MeshCore sub-heading** — MeshCore wordmark icon visible; white on dark background
- [ ] **Meshtastic sub-heading** — Meshtastic M-PWRD badge visible in **full colour** (green + white badge, not inverted)
- [ ] **JS8Call sub-heading** — JS8Call icon visible; white/light on dark background
- [ ] **Winlink Email (Pat) sub-heading** — Pat logo visible; white/light on dark background
- [ ] **FreeDATA sub-heading** — FreeDATA logo visible; white/light on dark background
- [ ] **No broken image glyphs** — all six icons load without showing a broken-image placeholder; onerror fallback hides any that fail to load (no layout breakage)

---

## 18. x86 Image (if testing PC build)

- [ ] Flash `mcomzos-x86_64.img.xz` to USB, boot a PC from USB
- [ ] Repeat sections 1–12 above

---

## 19. RAUC OTA (phase 1a — install + config only, no A/B partitions yet)

Requires SSH (diagnostics mode). No update flow to test yet — just sanity-check the plumbing landed.

- [ ] `rauc --version` prints RAUC 1.9 or newer
- [ ] `/etc/rauc/system.conf` exists; `compatible=` matches the image arch (`mcomzos-arm64` on Pi, `mcomzos-amd64` on x86)
- [ ] `/etc/rauc/keyring.pem` exists and is readable
- [ ] `systemctl status mcomz-mark-good` → service has run once and is `active (exited)` (the health check should have passed at boot)
- [ ] `journalctl -u mcomz-mark-good -n 5` contains "post-boot health check passed"
- [ ] `rauc status` does **not** fatally crash; on a pre-phase-1b image it will report "no bootable slots" / "slot not mounted" — that's expected until partitions are in place

---

## Known Limitations (do not raise as bugs)

| Item | Notes |
|------|-------|
| PDF books on iOS Chrome | iOS Chrome cannot display inline PDFs — platform limitation |
| Mumble microphone on HTTP | `getUserMedia` requires HTTPS — use HTTPS or accept the cert |
| Mumble microphone on iOS Chrome | Apple restricts WebRTC to Safari only on iOS |
| FreeDATA ARM64 | No upstream AppImage — skipped silently if unavailable |
| Self-signed cert warning | Expected on first HTTPS visit — accept once per browser |
