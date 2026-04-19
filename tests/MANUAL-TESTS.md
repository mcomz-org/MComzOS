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

- [ ] **Without LoRa hardware** — clicking Meshtastic or MeshCore shows the inline "not connected" warning rather than navigating to a 502 page
- [ ] **With LoRa hardware** (if available) — Meshtastic and MeshCore UIs load correctly
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

## 13. Diagnostics Mode (diagnostics builds only)

Only applies when the image was built with `diagnostics_mode=true` (currently all builds).

- [ ] **Splash screen appears** — open `http://mcomz.local/`; a full-screen orange-bordered warning modal appears explaining SSH credentials and risks
- [ ] **Dismiss persists** — click "Understood — Dismiss"; modal closes and does not reappear on page refresh within the same browser session
- [ ] **DIAG badge visible** — after dismissing the splash, a small orange `⚠ DIAG` badge is visible in the header; clicking it re-shows the modal
- [ ] **SSH key access** — from the development machine: `ssh -i .claude/diagnostics/mcomzos_diag mcomz@mcomz.local` — logs in without a password prompt
- [ ] **SSH password access** — `ssh mcomz@mcomz.local` (password `mcomzdiag`) — logs in successfully
- [ ] **API readable over HTTP** — `curl http://mcomz.local/api/status` returns JSON with `"diagnostics_mode": true`
- [ ] **Disable diagnostics** — `sudo rm /etc/mcomzos-diagnostics && sudo reboot`; after reboot, splash does not appear and DIAG badge is absent; SSH password auth still works until next image flash

---

## 14. x86 Image (if testing PC build)

- [ ] Flash `mcomzos-x86_64.img.xz` to USB, boot a PC from USB
- [ ] Repeat sections 1–12 above

---

## Known Limitations (do not raise as bugs)

| Item | Notes |
|------|-------|
| PDF books on iOS Chrome | iOS Chrome cannot display inline PDFs — platform limitation |
| Mumble microphone on HTTP | `getUserMedia` requires HTTPS — use HTTPS or accept the cert |
| Mumble microphone on iOS Chrome | Apple restricts WebRTC to Safari only on iOS |
| FreeDATA ARM64 | No upstream AppImage — skipped silently if unavailable |
| Self-signed cert warning | Expected on first HTTPS visit — accept once per browser |
