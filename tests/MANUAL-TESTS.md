# MComzOS Manual Tests

Hands-on hardware checklist for validating each release. Flash the image, boot, and work through every section in order. Record pass/fail and any notes against the release version in `.claude/feedback/hardware-test-results.md`.

---

## 0. Setup

- [ ] Flash `mcomzos-rpi.img.xz` to SD card using Raspberry Pi Imager
- [ ] Insert SD card, connect ethernet to a router, power on
- [ ] Wait ~60 s for first boot to complete

---

## 1. Basic Connectivity

- [ ] **mDNS** — from a laptop on the same network, `ping mcomz.local` responds
- [ ] **HTTP dashboard** — `http://mcomz.local` loads the MComz dashboard in browser (no certificate warning)
- [ ] **HTTPS dashboard** — `https://mcomz.local` loads (browser shows cert warning; accept it once)
- [ ] **iOS Safari** — open `http://mcomz.local` on iPhone/iPad — dashboard loads without any certificate prompt
- [ ] **Version display** — System Status card shows "(v0.0.2-pre-alpha.X)" with link to releases

---

## 2. System Status Card

- [ ] All services show a status badge (green "on" or red "off") — no stuck "…" spinner
- [ ] **hostapd** and **dnsmasq** show "off" with "(standby — activates with hotspot)" note
- [ ] **nginx** shows "on"
- [ ] **avahi-daemon** shows "on"
- [ ] Status refreshes automatically every 15 seconds (watch for badge flicker)

---

## 3. Offline Library (Kiwix)

- [ ] **Open Library** button loads Kiwix at `/library/`
- [ ] At least 3 ZIMs listed (MComz-Survival, MComz-Literature, MComz-Scriptures)
- [ ] Each ZIM shows a title and thumbnail (not a `?` square)
- [ ] **Search** — type a word in the Kiwix search box; results appear (not empty)
- [ ] **Language/Category dropdowns** — not empty; show at least one option
- [ ] Open a book from MComz-Literature — HTML content loads correctly
- [ ] Open a book from MComz-Scriptures — HTML content loads correctly
- [ ] **Arabian Nights** — confirm title is "The Arabian Nights" (Andrew Lang), not "The Wheels of Chance"
- [ ] **WikiMed Mini** — listed in Kiwix; search for a medical term (e.g. "fracture") returns results
- [ ] **iOS Chrome** — open a HTML book on iPhone — renders correctly
- [ ] **PDF note** — PDF-only books show a note about downloading rather than inline render failure

### Manage Books panel
- [ ] "＋ Manage Books" button opens slide-in panel
- [ ] Installed books list shows the ZIMs that are installed
- [ ] Remove a book — it disappears from the list and from Kiwix after reload
- [ ] Add by URL — paste a valid .zim URL, click Download & Add, progress status updates, book appears when done
- [ ] "Use this URL" buttons on recommended ZIMs fill the URL field correctly

---

## 4. Voice & Text Chat (Mumble)

- [ ] **Join Channel** button opens mumble-web in browser
- [ ] Enter a name, leave password blank, press Connect — connects without error
- [ ] "How to use" collapsible expands and collapses
- [ ] **macOS Chrome** — Mumble controls are not greyed out (websockify bridge running)
- [ ] **Voice** — microphone works on HTTPS; voice-activated audio transmits to another connected client
- [ ] **Text** — type a message, press Enter, message appears in chat
- [ ] **iOS** — note in how-to says to use Safari (Chrome blocks mic on iOS)

---

## 5. Licensed Radio (collapsed card)

- [ ] "📻 Licensed Radio" card is present with "Show Radio Capabilities" button
- [ ] Button expands to reveal Pat, JS8Call, and FreeDATA sub-sections
- [ ] "Hide Radio Capabilities" collapses it again

### Pat (Winlink Email)
- [ ] "Open Pat — Winlink Email" opens the Pat web UI (port 8081)
- [ ] Pat UI loads without nginx error

### JS8Call (Remote Desktop / VNC)
- [ ] "Open JS8Call" opens noVNC at `/vnc/vnc.html?path=vnc/websockify&autoconnect=true`
- [ ] noVNC connects and **VNC password dialog appears** (password: `mcomz`)
- [ ] After entering password, JS8Call desktop loads inside the browser window
- [ ] JS8Call application is running (visible in Openbox session)

### FreeDATA
- [ ] "Open FreeDATA" opens same noVNC URL
- [ ] Note about AppImage availability is shown if FreeDATA not installed

---

## 6. Mesh Communication (collapsed card)

- [ ] "📡 Mesh Communication" card present; "Show Mesh Capabilities" expands it
- [ ] **Without LoRa hardware** — clicking Meshtastic or MeshCore shows inline warning "not connected — attach your LoRa radio and reload" rather than navigating to a 502 page
- [ ] **With LoRa hardware** (if available) — Meshtastic and MeshCore UIs load correctly

---

## 7. WiFi Panel

- [ ] "📶 WiFi" button in header opens slide-in panel
- [ ] Current connection status shown correctly (connected SSID or "not connected")
- [ ] **Scan** — "Scan" button triggers scan; nearby networks appear in list
- [ ] **Connect** — tap a network, enter password, hub connects and status updates
- [ ] **Forget** — saved networks list shows known networks; Forget button removes one

---

## 8. WiFi Hotspot (AP Mode)

- [ ] **Start Hotspot** — click "Start Hotspot (AP Mode)"; page shows guidance to connect to "MComzOS" network
- [ ] From a phone: connect to WiFi network "MComzOS", password "mcomzos1"
- [ ] From phone browser: `http://mcomz.local` or `http://192.168.4.1` loads dashboard
- [ ] **Stop Hotspot** — click "Stop Hotspot"; button shows "Stopping…"; within 30 s shows either "reconnected to WiFi" or reconnect guidance
- [ ] After stopping hotspot: hub reconnects to router; `http://mcomz.local` accessible again from laptop

---

## 9. AP Auto-Fallback (5-minute timer)

- [ ] Disconnect ethernet from hub (or disconnect from all known WiFi networks)
- [ ] Wait 5+ minutes
- [ ] Verify "MComzOS" WiFi hotspot appears on a phone
- [ ] Connect to it and load `http://192.168.4.1` — dashboard loads

---

## 10. Reboot & Shutdown

- [ ] **Reboot** — click "↺ Reboot" in System Status; confirm dialog appears; hub reboots; after ~60 s dashboard is accessible again
- [ ] **Shutdown** — click "⏻ Shut Down"; confirm dialog appears; hub powers off (green LED goes off or activity stops)

---

## 11. Kiosk Mode (physical display)

- [ ] Connect HDMI monitor, USB keyboard and mouse; power on hub
- [ ] Hub boots to full-screen Chromium showing MComz dashboard — no login prompt visible
- [ ] Dashboard is interactive with mouse/keyboard
- [ ] Screen does not blank within 5 minutes (blanking disabled)
- [ ] Cursor hides after 5 s of inactivity (unclutter)

---

## 12. x86 Image (if testing PC build)

- [ ] Flash `mcomzos-x86_64.img.xz` to USB drive
- [ ] Boot a PC from USB
- [ ] Repeat sections 1–11 above

---

## Known Limitations (do not raise as bugs)

| Item | Notes |
|------|-------|
| PDF books on iOS Chrome | iOS Chrome cannot display inline PDFs — expected, platform limitation |
| Mumble microphone on HTTP | `getUserMedia` requires HTTPS — use HTTPS or accept the cert |
| Mumble microphone on iOS Chrome | Apple restricts WebRTC to Safari only on iOS |
| FreeDATA ARM64 | No upstream AppImage — skipped silently if unavailable |
| Self-signed cert warning | Expected on first HTTPS visit — accept once per browser |
