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

> All S-1 through S-6 shipped in pre-alpha.22 (2026-04-17) and confirmed by smoke test. See §2 for remaining hardware verification items.

### ~~S-2. MeshCore CORS probe fix~~ — COMPLETE

`fetch(..., {method:'HEAD'})` fails with a CORS error even when online because `flasher.meshcore.co.uk` has no CORS headers. Adding `mode:'no-cors'` makes the probe succeed on a reachable server without requiring CORS headers. **Shipped this session** — needs hardware verify: click Flash MeshCore when online → should open `flasher.meshcore.co.uk`.

### S-3. JS8Call `.config` ownership — `site.yml:289`

`/home/mcomz/.config/` was created by Ansible as `root:root`; `mcomz` user could not create `JS8Call.ini`, causing immediate fatal crash on launch. Added explicit `.config` directory creation task with `owner: mcomz`. **Live-fixed on Pi and shipped in playbook** — confirmed working this session. Needs reflash to verify the playbook fix persists.

### S-1. Smoke test: add individual ZIM checks + /meshcore-flash/ + VNC/FreeDATA coverage

Pre-alpha.21 hardware test revealed four smoke test gaps:

1. **All 3 MComzOS ZIMs individually** — current check passes if any one keyword (`survival`/`literature`/`scripture`) is present; need three separate checks. Also add a content-fetch for each registered ZIM by **slug** (not UUID — see S-4) — not just the first book.
2. **WikiMed** — current check is keyword-only; add a slug content-fetch once registered.
3. **`/meshcore-flash/`** — not checked at all; add a check that it returns 200 (not 403/404).
4. **FreeDATA on ARM64** — add a check that on ARM64 the FreeDATA card is either absent or clearly flagged unavailable (HTML-check.py).

VNC/JS8Call auth cannot be automated (needs a WebSocket VNC client); add to MANUAL-TESTS.md instead.

Coverage rule: tests must cover the new behaviour, not just pass because they don't know about it.

### S-4. Kiwix routing: switch dashboard + smoke test from UUID to slug `[claude+vibe]`

**Root cause (pre-alpha.21):** kiwix-serve's `/library/content/<X>/` route expects the **slug** (the `name=` attribute on `<book>` in `library.xml`), not the UUID. The dashboard download path (`status.py:262`) writes books with `id=` and `path=` only — no `name=` — so kiwix auto-derives a slug from the filename. UUID lookups always 404. This is the real cause of the pre-alpha.21 "Kiwix UUID 404" symptom (B-4 in §3 — likely resolved by this fix without needing the full diagnostic).

**Edits:**

- `src/api/status.py:214-227 kiwix_books()` — replace `library.xml` parsing with a query against kiwix-serve's own catalog (it is the source of truth for which slugs it actually serves):
  ```python
  with urllib.request.urlopen("http://127.0.0.1:8888/catalog/v2/entries?count=200", timeout=3) as r:
      tree = ET.fromstring(r.read())
  # parse OPDS Atom; for each <entry>: id (UUID), name (slug), title, summary, length
  ```
  Return per book: `{ "id", "name", "title", "size", "language" }`. On exception (kiwix not yet up), fall back to the current `library.xml` parser so the API still responds during boot.
- `src/dashboard/index.html:747` — change `\`/library/viewer#${encodeURIComponent(b.id)}\`` → `\`/library/viewer#${encodeURIComponent(b.name)}\``.
- `tests/smoke-test.py:255` — change `/library/content/<uuid>/` → `/library/content/<slug>/`. Loop over **every** book, not just the first.
- `tests/html-check.py` — assert the viewer href uses `b.name` (regression guard).

**Acceptance:** smoke-test passes against a Pi with both MComz and downloaded ZIMs; clicking a book in the dashboard library list opens the viewer and content renders.

### S-5. MeshCore offline flasher CI hardening `[vibe]`

**Root cause (pre-alpha.21):** `site.yml:1347` git clone fails in CI; `rescue:` block at line 1425 swallows the failure with a `debug:` message — build still ships green, image arrives with a missing `/var/www/html/meshcore-flash/` directory and the dashboard falls back to a 403/404.

**Edits:**

- `site.yml:1347` (Clone MeshCore web flasher) — add `register: clone_result`, `until: clone_result.rc == 0`, `retries: 3`, `delay: 10`.
- `site.yml:1425-1428` (rescue block) — replace the `debug:` task with `fail: msg="MeshCore offline flasher provisioning failed; build aborted to avoid shipping a broken image"`.
- `.github/workflows/build-image.yml` — add a post-Ansible CI step: `test -s "$MNT/var/www/html/meshcore-flash/index.html" || (echo "meshcore-flash missing" && exit 1)`. Same for both arm64 and x86 jobs.
- `tests/smoke-test.py` — add: GET `/meshcore-flash/`; assert HTTP 200 and body contains `flasher` or `MeshCore` (catches future 403/404 silently).

**Acceptance:** if GitHub is unreachable or the clone fails 3× in a row, CI fails loudly. Reflashed image always serves `/meshcore-flash/`.

### S-6. FreeDATA arch-aware UI `[vibe]`

**Pre-alpha.21:** dashboard always renders the FreeDATA Connect button even on ARM64, where there is no AppImage and the button does nothing.

**Edits:**

- `src/api/status.py` — extend the `/api/status` payload with `"freedata_installed": bool`. True iff the AppImage exists at the path used by `site.yml` (confirm by grepping the FreeDATA install task — typically `/opt/freedata/FreeDATA-<ver>.AppImage` or wherever `Pat and FreeDATA URLs made architecture-aware` deposits it).
- `src/dashboard/index.html:316-320` — read `status.freedata_installed`. If false, replace the `mesh-section` content with: "FreeDATA is not yet available on this device (no ARM64 AppImage published upstream — see [DJ2LS/FreeDATA](https://github.com/DJ2LS/FreeDATA))."
- `tests/html-check.py` — assert the FreeDATA section gates on `freedata_installed`.

**Acceptance:** ARM64 hub no longer shows a dead Connect button; x86 hub (where the AppImage installs) is unchanged.

---

## §2 — Awaiting reflash to verify (no code work needed, just hardware test)

### Verified in pre-alpha.22 (2026-04-17)

| Fix | Outcome |
|---|---|
| S-1: Smoke test ZIM gaps (individual ZIM checks, slug content-fetches, /meshcore-flash/) | ✅ All 3 MComz ZIMs individually checked by slug; content-fetches all 200; /meshcore-flash/ 200 ✅ |
| S-2: MeshCore CORS probe (`mode:'no-cors'`) | ✅ Flasher provisioned and responding; online-routing needs manual verify on connected hub |
| S-4: Kiwix slug routing (OPDS catalog, b.name in dashboard) | ✅ All 3 ZIMs with correct slugs; content fetches by slug all pass; titles via filename fallback working |
| S-5: MeshCore CI hardening (retry + rescue→fail + CI verify step) | ✅ /meshcore-flash/ serves correctly in pre-alpha.22 — CI step passed |
| S-6: FreeDATA arch-aware UI (`freedata_installed` field) | ✅ API returns `false` on ARM64; section hidden; html-check.py 120/120 |
| VNC stack: Xvnc, noVNC, websockify | ✅ All confirmed by smoke test (5901 open, websockify 101, noVNC page) |
| JS8Call `.config` ownership | ✅ Playbook fix confirmed — /home/mcomz/.config is mcomz-owned in new image |
| WikiMed `Restart=on-failure` + `RestartSec=30` | ⏳ Shipped — WikiMed not yet registered at smoke-test time (first-boot download in progress); retry logic should complete it |

### Verified in pre-alpha.21 (2026-04-16)

| Fix | Outcome |
|---|---|
| VNC websockify upgrade — smoke test added | ✅ Smoke test passes; WebSocket upgrade confirmed live |
| iOS Safari + MeshCore flasher fix log: Fix A (iOS Safari) | ✅ Confirmed working — cert warning → redirect page → dashboard loads, 2026-04-17 |

### Still awaiting hardware confirmation

| Fix | Where | Verify with |
|---|---|---|
| VNC HTTPS links — JS8Call/FreeDATA onclick now forces `https://` | `index.html:313,318` | Click "Open JS8Call" — should open noVNC over HTTPS, VNC auth prompt appears, JS8Call window visible |
| WikiMed registered after first-boot retry | `mcomz-wikimed-download.service` | ~5 min after boot: smoke-test WikiMed check passes; book appears in library panel |
| Pat send/receive | — | Real-radio test: send a Winlink check-in, confirm it arrives |
| Mumble voice | — | iOS Safari with HTTPS: mic prompt appears, voice connects |
| MeshCore online routing | `index.html:702` | On internet-connected hub: click Flash MeshCore → opens `flasher.meshcore.co.uk` (not local bundle) |

---

## §3 — Blocked: needs hardware diagnostic logs

For each item below: SSH to the Pi (or open a terminal locally), run the listed commands, paste the full output into `.claude/feedback/hardware-test-results.md` under the named heading. Once that's done, the next code session can diagnose and write the fix.

### B-8. SSH password auth rejected on new image

`ssh-copy-id` fails with `Permission denied (publickey,password)` on pre-alpha.22. Either the playbook hardens sshd (`PasswordAuthentication no`) or the Pi image defaults to key-only. Needs one-time manual key install from the Pi:

```sh
# From the Pi console or via the user's existing key
sudo -u mcomz mkdir -p /home/mcomz/.ssh
echo "YOUR_PUBLIC_KEY" >> /home/mcomz/.ssh/authorized_keys
sudo chmod 700 /home/mcomz/.ssh && sudo chmod 600 /home/mcomz/.ssh/authorized_keys
```

Or investigate: `grep -i PasswordAuthentication /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf`

### ~~B-1. JS8Call / VNC~~ — RESOLVED this session

Root cause diagnosed and fixed 2026-04-17:
- VNC auth only works over HTTPS (HTTP path has a silent auth failure — acceptable, dashboard links to `https://mcomz.local/vnc/`)
- `/home/mcomz/.config/` was `root:root`; JS8Call couldn't create its ini file and crashed immediately
- Fixed live on Pi + playbook fix at `site.yml:289`
- JS8Call confirmed loading in VNC session

### ~~B-4. Kiwix ZIM content 404 after download~~ — superseded by §1.S-4

Root cause is now known: kiwix-serve's content route expects the **slug**, not the UUID. Plan in §1.S-4 fixes this without further diagnostics. If S-4 is shipped and the bug still occurs, then re-open this entry and run the Pi-side commands below.

<details><summary>Original diagnostic commands (kept in case S-4 doesn't resolve it)</summary>

```sh
curl -s http://localhost:8888/library/catalog/v2/entries | grep -E "<id>|<title>|<name>"
ls -lh /var/lib/kiwix/*.zim 2>/dev/null || find /var/lib -name "*.zim" -ls 2>/dev/null
find /home -name "*.zim" -ls 2>/dev/null
find /opt -name "*.zim" -ls 2>/dev/null
sudo systemctl status kiwix-serve
sudo journalctl -u kiwix-serve -n 100 --no-pager
curl -i "http://localhost:8888/content/171ffc5a-c68a-4f92-8ad1-279170745a3e/"
```
**Paste under heading:** `## v0.0.2-pre-alpha.21 — Kiwix UUID 404 diagnostic` (only if needed).
</details>

### ~~B-5. MeshCore flash CORS bug~~ — RESOLVED by §1.S-2

Already shipped: `index.html:702` adds `mode:'no-cors'` to the connectivity probe. Awaiting hardware verify (§2).

### B-6. WikiMed first-boot download did not produce a ZIM

**Pre-alpha.21 status:** §1.A catalog name fix is in main, but it's still unconfirmed whether the `mcomz-wikimed-download` oneshot actually ran to completion on first boot. Gather:

```sh
sudo systemctl status mcomz-wikimed-download
sudo journalctl -u mcomz-wikimed-download -n 200 --no-pager
ls -lh /var/mcomz/library/
```

**Paste under heading:** `## v0.0.2-pre-alpha.21 — WikiMed first-boot diagnostic`.

### B-7. Mumble websocket bridge shows `err` despite text chat working

The status badge is driven by `systemctl is-active`. If `mcomz-mumble-ws` failed once at boot and `Restart=on-failure` recovered it, `is-active` may still report a stale failed state — or the dashboard's badge mapping treats `activating` as `err`. Need:

```sh
systemctl status mcomz-mumble-ws
sudo journalctl -u mcomz-mumble-ws -n 200 --no-pager
ss -lntp | grep 64737
curl -i http://127.0.0.1:64737/
```

**Paste under heading:** `## v0.0.2-pre-alpha.21 — Mumble websocket status diagnostic`.

Once logs land: code fix in `src/api/status.py` to either treat `active`-or-`activating` as healthy and only `failed`/`inactive` as err, or check port responsiveness on `localhost:64737` for this service rather than relying solely on `is-active`.

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
- **FreeDATA ARM64 (upstream)** — no upstream AppImage; correct fix is a PR to `DJ2LS/FreeDATA` adding ARM64 to its release matrix. Playbook already skips install gracefully. **Dashboard arch-aware UI is in §1.S-6** so pre-alpha.21's "dead Connect button" symptom is addressed in-product even while the upstream gap remains.
- **MComzLibrary ZIM metadata empty (upstream)** — pre-alpha.21 found the MComz ZIMs are missing internal title/language/etc. Fix belongs in the `MComzLibrary` build pipeline (add `--title --description --language --creator --publisher` to whatever wraps `zimwriterfs`). Dashboard already falls back to filename-derived titles, so impact in-product is cosmetic. Action: file an issue on the MComzLibrary repo.
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
