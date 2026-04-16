# MComzOS TODO

> **How to use this file**
> - **§1 Sonnet-actionable now** — code-only changes with file:line refs, exact target code, and the test that must pass. No hardware needed.
> - **§2 Awaiting reflash to verify** — fixes already in `main`; flash next image and run `tests/MANUAL-TESTS.md` + `tests/smoke-test.py`. Update `.claude/fixes/` outcome sections after.
> - **§3 Blocked: needs hardware logs** — diagnose-then-fix items. The exact commands to run on the Pi are in each entry; paste the output into `.claude/feedback/hardware-test-results.md` under the named heading and Sonnet/Claude can take it from there.
> - **§4 Won't fix / external** — out of scope.
> - **§5 Roadmap** — post-v0.0.2 features.
> - **§6 Historical record** — preserved for audit; do not edit.
>
> Key: `[vibe]` = code changes — use vibe. `[claude]` = test infra, research, diagnostic work — do directly.
> Coverage rule (CLAUDE.md): every behavioural change ships with a test in the same commit.

---

## §1 — Sonnet-actionable now

*(No items — all actionable fixes have been shipped. See §2 for hardware verification queue.)*

---

## §2 — Awaiting reflash to verify (no code work needed, just hardware test)

These fixes are in `main` already. The next image build (v0.0.2-pre-alpha.21 or later) needs to be flashed, then the listed tests run. After verification, fill in the **Outcome** section of the corresponding `.claude/fixes/` entry.

| Fix | Where | Verify with |
|---|---|---|
| iOS Safari HTTPS — full dashboard restored on `https://` | `site.yml:1552-1554` | iOS Safari → `https://mcomz.local/` should cert-warn once, "Visit Website", then load the full dashboard. Force-close, reopen — should not loop. |
| `https-warn` global banner removed | `index.html` (no matches) | HTTP load shows no orange banner; Mumble card still has its inline mic/HTTPS note. |
| Pat button uses literal `https://` | `index.html:308`, asserted in `html-check.py:184-187` | From dashboard on HTTP, click "Open Pat" → opens `https://mcomz.local:8081/` (no 400). |
| Kiwix book reader URL → `/library/viewer#<uuid>` | `index.html:747` | Click any installed book in the library list — viewer opens, content renders. |
| MeshCore offline flasher 403 → recursive www-data chown | `site.yml:1381-1389` | In hotspot mode (no internet), click Flash MeshCore — opens `/meshcore-flash/` and serves all assets without 403. |
| VNC websockify upgrade — smoke test added | `tests/smoke-test.py:303-327` | Run `python3 tests/smoke-test.py mcomz.local` from a LAN laptop. Look for "websockify WebSocket upgrade succeeds (101 Switching Protocols)" — pass means the chain is alive. |
| iOS Safari + MeshCore flasher fix log | `.claude/fixes/2026-04-15-4b9569d-ios-safari-and-meshcore-flasher.md` | After hardware test, fill in **Outcome** for both Fix A and Fix B. |
| RECOMMENDED_ZIMS + first-boot WikiMed — real catalog names | `site.yml:1069`, `index.html RECOMMENDED_ZIMS`, fix log `2026-04-16-f1f26e7` | Manage Books panel: all four Kiwix titles show download URLs (no "Not found"). First boot downloads wikimed-mini.zim successfully. |

### Older unverified fixes (still pending hardware confirmation)

| Fix | Source ref | Verify |
|---|---|---|
| VNC Connect button — Requires=/StartLimit/-localhost/port-ready loop/Wants= | pre-alpha.19 fix in main | Click Open JS8Call → noVNC connects, password prompt appears, JS8Call window visible. |
| Mumble controls greyed on macOS Chrome — `mcomz-mumble-ws` in status dict + `server_hostname='localhost'` SSL fix | site.yml `mcomz-mumble-ws` block + websockify SSL patch | macOS Chrome → Mumble controls active (not greyed), connect succeeds. |
| Mumble microphone on iOS — "use Safari" note | dashboard Mumble card | iOS Safari → mic prompt appears (depends on iOS Safari fix above). |
| ZIM download SSL CERT_NONE — `urlopen` w/ unverified context | `src/api/status.py kiwix_download` | Manage Books → download a small ZIM (e.g. MComz Scriptures); succeeds without `CERTIFICATE_VERIFY_FAILED`. |

---

## §3 — Blocked: needs hardware diagnostic logs

For each item below: SSH to the Pi (or open a terminal locally), run the listed commands, paste the full output into `.claude/feedback/hardware-test-results.md` under the named heading. Once that's done, the next code session can diagnose and write the fix.

### B-1. JS8Call / FreeDATA "Connect button just flashes"
The websockify smoke-test now confirms the chain is reachable, but click-time behaviour fails. Need:

```sh
sudo journalctl -u mcomz-novnc -n 200 --no-pager
sudo journalctl -u mcomz-vnc  -n 200 --no-pager
sudo systemctl status mcomz-novnc mcomz-vnc
ss -lntp | grep -E '5901|6080'
curl -i -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: dGVzdA==" -H "Sec-WebSocket-Version: 13" \
     http://localhost/vnc/websockify
```
And from the browser: DevTools → Network → filter `websockify` → click Open JS8Call → screenshot the failed frame headers (request and response).

**Paste under heading:** `## v0.0.2-pre-alpha.21 — VNC connect diagnostic`.

### B-2. Meshtastic showing `err` ("Service crashed, check journalctl")

```sh
sudo journalctl -u meshtasticd -n 200 --no-pager
sudo systemctl status meshtasticd
ls -l /dev/serial/by-id/ 2>/dev/null
ls /dev/i2c-* /dev/spidev* 2>/dev/null
cat /etc/meshtasticd/config.yaml 2>/dev/null | head -60
```
**Paste under heading:** `## v0.0.2-pre-alpha.21 — Meshtastic crash diagnostic`.

### B-3. APRS / direwolf stuck `activating`

```sh
sudo journalctl -u direwolf -n 200 --no-pager
sudo systemctl status direwolf
aplay -l 2>&1
arecord -l 2>&1
ls /dev/snd 2>/dev/null
```
**Paste under heading:** `## v0.0.2-pre-alpha.21 — APRS/direwolf diagnostic`.

---

## §4 — Won't fix / external

- **Kiwix download speed** — server-side throughput / Pi uplink. No code lever.
- **FreeDATA ARM64** — no upstream AppImage; correct fix is a PR to `DJ2LS/FreeDATA` adding ARM64 to its release matrix. Playbook already skips gracefully.
- **PDF books inline on iOS Chrome** — platform limitation.
- **Mumble mic on iOS Chrome** — Apple restricts WebRTC to Safari only on iOS.

---

## §5 — Post-v0.0.2 Roadmap

### WAN Remote Access (WireGuard VPN)
LAN-only today. WireGuard is the recommended approach (fully open source, aligns with "no closed ecosystems").
- **Why:** "Internet is up but I'm not home" — access dashboard, relay messages, check status remotely.
- **Approach:** WireGuard peer config generated at provision time; hub is a peer, user devices are peers, a VPS or home router acts as relay endpoint. Key generation and `wg0.conf` deployed by Ansible.
- **Alternatives considered:** Tailscale (closed coordination server), Headscale (open but more complex to self-host), ZeroTier (similar trade-off to Tailscale).
- Not a priority when internet is down (core use case) — but valuable for pre-positioned hubs managed remotely.

### APRS Map Viewer
Direwolf decodes APRS but no map UI. Future release could add Xastir or a lightweight web-based APRS viewer.

### Dashboard features (requested 2026-04-09)

**Inline service guides (offline-friendly):**
- Mumble: inline "How to connect" guide on the dashboard card. Cover: enter any username, leave password blank, allow microphone when prompted, push-to-talk vs voice-activated. *(Mumble guide already shipped — verify and tick off.)*
- JS8Call: brief inline guide covering #MCOMZ net schedule and how to send a message.
- Pat: inline guide covering callsign setup and sending a Winlink check-in.

**Radio Communications tab:**
- Add a "Radio Communications" tab alongside "Mesh Communications".
- Gate licenced-radio features behind: "Do you have an Amateur Radio licence and a radio?"
  - No → show explanation of what a licence enables, link to licensing info.
  - Yes → reveal JS8Call (VNC), Pat (Winlink), ardopcf, Direwolf APRS, FreeDATA (when available).
- Unlicenced LoRa hardware (Meshtastic, MeshCore) stays visible without the gate.

**Admin login / protected functions:**
- Login screen protecting admin-only functions (simple password, stored locally — no internet auth).
- Protected: power off / reboot, WiFi panel, add Kiwix books, anything that affects other users on the network.
- Non-admin users can use all comms features without logging in.

**Kiwix library onboarding:**
- Flash screen on first login (or if library is empty) suggesting at least WikiMed.
- "Add Books" button in the Library section — requires login.
- Recommended books list with size variants (uses §1.A real catalog names).

---

## §6 — Historical record (do not edit)

### Key Decisions Made
- TigerVNC + noVNC chosen over Wayland + RustDesk (lighter, browser-native, battle-tested)
- Mumble chosen over XMPP (voice + ephemeral text in one tool; persistent chat not needed for emergency comms)
- websockify used for Mumble bridge instead of mumble-web-proxy (avoids Rust compilation on Pi, already in apt)
- meshtasticd from OBS repo (official apt package, includes bundled web UI)
- pyMC_Repeater for MeshCore (Python, runs on Pi with LoRa HAT, has web dashboard)

### Service Port Map (snapshot)

| Service | Port | Status |
|---------|------|--------|
| Nginx (dashboard) | 80 / 443 | ✅ |
| noVNC (JS8Call etc.) | 6080 → /vnc/ | ✅ |
| Mumble voice+text | 64737 → /mumble/ws | ✅ |
| Meshtastic web UI | 8080 → /meshtastic/ | ✅ |
| MeshCore dashboard | 8000 → /meshcore/ | ✅ |
| Murmur (native client) | 64738 | ✅ |
| Meshtastic TCP API | 4403 | ✅ |
| Kiwix | 8888 → /library/ | ✅ |
| Pat HTTP gateway | 18081 → :8081 (HTTPS) | ✅ |
| Direwolf APRS | 8010 (AGWPORT), 8011 (KISS) | ✅ |
| ardopcf HF modem | 8515 (TCP) | ✅ |
| Status API | 9000 → /api/ | ✅ |

### Major completed milestones (audit log)

- ✅ Multi-architecture support (deb_arch variable for arm64/amd64)
- ✅ XMPP replaced with Mumble browser voice+text (mumble-web + websockify)
- ✅ Meshtastic integration (meshtasticd + built-in web UI on port 8080)
- ✅ MeshCore integration (pyMC_Repeater + web dashboard on port 8000)
- ✅ ardopcf build (build-essential + libasound2-dev, make, install to PATH)
- ✅ Headless display fixed (TigerVNC + noVNC, replaced broken Wayland + RustDesk)
- ✅ Pat and FreeDATA URLs made architecture-aware
- ✅ WiFi AP + captive portal (hostapd, dnsmasq, avahi, static IP, hostname)
- ✅ Kiwix ZIM content + systemd service (port 8888, library.xml, nginx /library/ proxy)
- ✅ Missing systemd units: kiwix-serve, direwolf, ardopcf, pat
- ✅ Dashboard backend: stdlib-only Python status API on :9000, nginx proxies /api/
- ✅ Raspberry Pi Imager repository JSON published with each release
- ✅ GitHub Actions image build workflow (RPi ARM64 + x86_64), build_mode skips raspi-config
- ✅ Fake systemctl restored in both chroot builds; enable via `file: state=link` symlinks
- ✅ JS8Call headless: openbox xstartup, dbus-run-session, autoconnect, password hint
- ✅ Bare-metal bootstrap: ghost user, git, python3-apt, /opt/mcomz, FreeDATA 404, Mercury pip, Pat .deb URL via GitHub API
- ✅ x86 build: gnupg, OverlayFS via overlayroot, build re-enabled
- ✅ Mumble HTTPS for microphone access (self-signed cert)
- ✅ Phase A: build green with ignore_errors as scaffolding
- ✅ Phase A.5: ignore_errors removed; ardopcf URL fixed; MeshCore install rewritten; Mercury removed
- ✅ Phase B: every service enable uses `file: state=link` symlink — no ignore_errors remain

### Pre-alpha.11–.13 hardware-test fixes (P0)

- ✅ Kiwix CSS/images broken — `--urlRootLocation /library`
- ✅ Pat fails to start — `mcomz_user=pi` removed; default `mcomz` used
- ✅ mumble-web WebSocket bridge — global npm path corrected; websockify TCP-only; nginx alias for static
- ✅ AP hotspot button stuck — AbortController 4s timeout
- ✅ nginx not starting on first boot — explicit multi-user.target.wants symlink
- ✅ Safari iOS refuses HTTPS — cert validity reduced to 397 days
- ✅ Kiwix `/libraryINVALID URL` — proxy_pass preserves `/library/` prefix
- ✅ Meshtastic / MeshCore 502 — open in new tab + inline offline guard
- ✅ hostapd / dnsmasq "off" badge → "(standby — activates with hotspot)" inline note
- ✅ Manage Books: MComzLibrary entries with GitHub-API URL fetch
- ✅ meshtasticd `failed` status — distinct error/standby/off badges
- ✅ direwolf/mcomz-meshcore `activating` — `ConditionPathExists=` on /dev/snd, /dev/spidev0.0

### Pre-alpha.19 hardware-test fixes

- ✅ iOS Safari HTTPS-redirect-page approach (later reverted in pre-alpha.20 — see §2)
- ✅ Kiwix ZIM reader URLs use `b.id` UUID
- ✅ Kiwix.org recommended URLs via OPDS catalog (`fetchKiwixUrl(kiwixName)`)
- ✅ Installed books filtered out of recommended list
- ✅ Mesh card before Licensed Radio
- ✅ Tooltip delay — `data-tip=` + CSS `::after`
- ✅ WiFi icon clipped — viewBox expanded
- ✅ Offline MeshCore flasher for Heltec v4 — local clone + GitHub firmware download
- ✅ Installed ZIM sizes — `os.path.getsize`
- ✅ WikiMed Mini moved to first-boot oneshot (note: catalog name still wrong — see §1.A)
- ✅ smoke-test.py: misleading detail strings + OPDS catalog check
- ✅ smoke-test.py: VNC/noVNC TCP banner check

### Pre-alpha.20 hardware-test fixes (all in §2 above pending verify)

- ✅ iOS Safari revert — full dashboard on HTTPS
- ✅ Removed global "Not using HTTPS" banner
- ✅ Pat button literal `https://`
- ✅ Kiwix viewer URL `/library/viewer#<uuid>`
- ✅ /meshcore-flash/ 403 — recursive www-data chown
- ✅ websocket-upgrade smoke test
