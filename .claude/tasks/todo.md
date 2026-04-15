# MComzOS TODO

## Completed
- ✅ Multi-architecture support (deb_arch variable for arm64/amd64)
- ✅ XMPP replaced with Mumble browser voice+text (mumble-web + websockify)
- ✅ Meshtastic integration (meshtasticd + built-in web UI on port 8080)
- ✅ MeshCore integration (pyMC_Repeater + web dashboard on port 8000)
- ✅ ardopcf build (build-essential + libasound2-dev, make, install to PATH)
- ✅ Mercury Python dependencies installed
- ✅ Headless display fixed (TigerVNC + noVNC, replaced broken Wayland + RustDesk)
- ✅ Fix ardopcf repo URL typo (pflrr → pflarue)
- ✅ Pat and FreeDATA URLs made architecture-aware
- ✅ WiFi AP + captive portal (hostapd, dnsmasq, avahi, static IP, hostname)

## Outstanding

> **Key:** `[vibe]` = code changes to index.html / status.py / site.yml — use a vibe session.
> `[claude]` = test infrastructure, research, git ops, curl/diagnostic work — do directly in Claude Code.

---

### Bugs confirmed in v0.0.2-pre-alpha.19 (RPi 5, 2026-04-12)

#### Vibe tasks

- ✅ **iOS Safari broken (regression)** — nginx port 443 root `/` now returns a minimal static HTML page directing users to `http://mcomz.local` instead of the full dashboard. The full dashboard still served on HTTP (port 80). All other HTTPS locations (`/api/`, `/mumble/ws`, `/library/`, etc.) remain functional. Needs hardware verification.

- [ ] **VNC / JS8Call and FreeDATA — Connect button loops** — Fix shipped. Three causes fixed: (1) removed `-localhost` from Xvnc which can bind to `::1` only on Bookworm, making `127.0.0.1:5901` unreachable; (2) replaced `sleep 1.5` with a `/dev/tcp` port-ready loop (waits up to 15s); (3) added `Wants=mcomz-vnc.service` to novnc unit. **Needs hardware verification.**

- ✅ **Kiwix ZIM reader URLs wrong** — Library panel now uses `b.id` (UUID from library.xml) as the kiwix-serve reader path: `/library/A/<uuid>/`. The UUID stored by the playbook is the one kiwix-serve assigns, so reader links are correct.

- ✅ **Kiwix.org recommended URLs are directory listings, not .zim files** — Added `fetchKiwixUrl(kiwixName)` which queries `https://library.kiwix.org/catalog/v2/entries?lang=eng&name=<name>`, parses OPDS Atom XML via `DOMParser`, strips `.meta4` to get the direct ZIM URL, and populates the download field. All community ZIMs in RECOMMENDED_ZIMS updated to use `kiwixName`.

- ✅ **Installed books appear in recommended list** — `renderRecommended(books)` now accepts the installed books list and filters entries whose `zimPattern` or `kiwixName` matches any installed filename. `openBooks()` does a single `/api/kiwix/books` fetch and passes the result to both the installed list and the recommended panel.

- ✅ **Licensed Radio card before Mesh card (wrong order)** — Mesh Communication card now appears before Licensed Radio in index.html.

- ✅ **Tooltip delay** — Replaced `title=` on svc-badge with `data-tip=` + CSS `::after` pseudo-element tooltip (0.08s fade-in, no browser delay). Works on hover; doesn't require JS.

- ✅ **WiFi icon clipped at top** — SVG viewBox expanded from `0 0 22 16` to `0 -2 22 18`, giving the top arc 2px headroom above the stroke.

- ✅ **Offline MeshCore flasher for Heltec v4** — `git clone --depth=1 meshcore-dev/flasher.meshcore.io` into `/var/www/html/meshcore-flash/` during provisioning; Python patch script rewrites absolute paths for subpath serving; GitHub API downloads all Heltec V3/V4 `.bin` firmware assets; nginx alias at `/meshcore-flash/`. Dashboard Flash button replaced with `openMeshFlasher()` — probes `flasher.meshcore.co.uk` with 3s timeout, routes to online flasher or local bundle. Needs hardware verification.

- ✅ **Installed ZIM sizes** — `kiwix_books()` in status.py now uses `os.path.getsize(path)` to return actual file size in bytes. The Manage Books panel already renders it as `(N MB)`.

- ✅ **WikiMed Mini provisioning (recurring)** — Moved to a `ConditionPathExists=!` first-boot systemd oneshot (`mcomz-wikimed-download.service`). Runs on first boot after `network-online.target`; restarts kiwix-serve when done. Build-time download tasks removed. Will not time out in qemu since it never runs in the chroot.

#### Claude tasks

- ✅ **Fix smoke-test.py: misleading detail + OPDS catalog check** `[claude]` — Detail strings now only passed on failure. Added OPDS catalog check: fetches `/library/catalog/v2/entries`, verifies HTTP 200 + Atom XML + at least one `<entry>`. Also fixed download-status detail string same way.

- ✅ **Add VNC/noVNC connection check to smoke-test.py** `[claude]` — TCP connect to `HOST:5901`, verify `RFB` banner. Directly detects the noVNC connect-loop class of failure.

---

### Unverified fixes (shipped in code, awaiting hardware confirmation)

- [ ] **VNC Connect button** — All fixes applied (removed Requires=, StartLimitIntervalSec=0, removed -localhost, port-ready loop, Wants=). **Needs hardware verification in next flash.**

- [ ] **Mumble controls greyed on macOS Chrome** `[vibe]` — `mcomz-mumble-ws` added to status dict; `server_hostname='localhost'` added to websockify SSL patch. **Needs hardware verification.**

- [ ] **Mumble microphone on iOS** `[vibe]` — "Use Safari on iPhone/iPad" note added to dashboard. **Tied to iOS Safari regression above — verify once Safari access is restored.**

- [ ] **SSL cert verify on ZIM download** `[vibe]` — Switched from `urlretrieve` to `urlopen` with `CERT_NONE` context. **Needs hardware verification.**

---

### P0 — Bugs found during first hardware test (v0.0.2-pre-alpha.11, RPi 5, 2026-04-09)

- ✅ **Kiwix CSS/images broken** — `--urlRootLocation /library` added to kiwix-serve ExecStart so all internal URL paths are prefixed correctly.

- ✅ **Pat fails to start — wrong user** — `mcomz_user=pi` removed from both CI extra-vars; playbook default `mcomz_user: mcomz` now used for all service files.

- ✅ **mumble-web WebSocket bridge fails** — Fixed in two parts:
  1. npm install path: `creates:` guard and websockify ExecStart updated to use `/usr/local/lib/node_modules/` (actual npm global path on Debian).
  2. WebSocket routing: websockify runs TCP-only (no `--web` flag); nginx serves mumble-web static files via `alias /usr/local/lib/node_modules/mumble-web/dist/` at `/mumble/`; WebSocket-only endpoint at `/mumble/ws`; dashboard button URL updated to `port=443/mumble/ws`.

- ✅ **AP hotspot button stuck on "Starting..."** — AbortController with 4s timeout added to `toggleAP()`; connection drop treated as success; manual state update and reconnect guidance shown; no longer freezes.
  - Note: actual hostapd/dnsmasq startup on hardware needs verification in next flash test.

- ✅ **nginx does not start on first boot** — Root cause: `deb-systemd-helper` detects chroot build and defers enables instead of creating symlinks. Fix: explicit `multi-user.target.wants/nginx.service` symlink deployed by Ansible, same as all custom services.

### P0 — Bugs found during second hardware test (v0.0.2-pre-alpha.13, RPi 5, 2026-04-09)

- ✅ **Safari iOS refuses to open HTTPS** — Self-signed cert was 3650 days; iOS Safari hard-blocks any cert with validity > 398 days since iOS 14. Fixed: cert regenerated with 397-day validity.

- ✅ **Kiwix returns `/libraryINVALID URL` 404** — nginx `proxy_pass http://127.0.0.1:8888/` stripped the `/library/` prefix, but kiwix with `--urlRootLocation /library` expects to receive the full `/library/...` path. Fixed: `proxy_pass http://127.0.0.1:8888/library/` (preserves prefix).

- [ ] **VNC Connect button does nothing** — mcomz-novnc has `Requires=mcomz-vnc`. If VNC server restarts during boot (it does — `Restart=on-failure`), novnc is stopped by systemd and never restarted. Fixed in code: removed `Requires=`, added `StartLimitIntervalSec=0`. **Needs hardware verification.**

- [ ] **Mumble controls greyed on macOS Chrome** — `mcomz-mumble-ws` (websockify bridge) was not in the SERVICES dict so its status was invisible. Added to dashboard. Also fixed websockify SSL patch to pass `server_hostname='localhost'` to `wrap_socket()` (Python 3.12 compatibility). **Root cause of greyed controls unknown until websockify status is confirmed on device.**

- [ ] **Mumble microphone on iOS** — iOS Chrome cannot access microphone (Apple restricts WebRTC to Safari only on iOS). Added "use Safari on iPhone/iPad" note to dashboard. Safari iOS also had the cert validity issue (now fixed above).

- ✅ **Meshtastic / MeshCore 502 Bad Gateway** — Both links now open in a new tab (`target="_blank"`). If the service is known inactive (from status API), an inline warning is shown: "not connected — attach your LoRa radio and reload." No raw nginx 502 navigation.

- ✅ **hostapd / dnsmasq showing "off" in status** — fixed: "off" badge now shows "(standby — activates with hotspot)" inline note in renderStatus().

- [ ] **Manage Books: ZIM download fails with SSL CERTIFICATE_VERIFY_FAILED** — Pi clock may lag behind cert notBefore on first boot (no GPS/NTP sync yet). `kiwix_download` used `urlretrieve` which does cert verification. Fixed in code (pre-alpha.18): switched to `urlopen` with `CERT_NONE` context. **Needs hardware verification.**

- ✅ **Manage Books: MComzLibrary ZIMs not in recommended list** — Added Survival, Literature, Scriptures entries to RECOMMENDED_ZIMS with "Get Download URL" button that fetches the latest release from the GitHub API (mcomz-org/MComzLibrary) and populates the URL field.

- ✅ **meshtasticd shows 'failed' in status** — renderStatus now distinguishes: `active` → green "on", `failed` → orange "error", standby svcs inactive → grey "standby", hardware svcs inactive → grey "standby (requires hardware)", core svcs inactive → red "off". Red is now reserved for services that should be running but aren't.

- ✅ **direwolf/mcomz-meshcore show 'activating'** — added `ConditionPathExists=/dev/snd` to direwolf unit and `ConditionPathExists=/dev/spidev0.0` to mcomz-meshcore unit. Services stay inactive (not stuck activating/restarting) when required hardware is absent.

### P0 — Hub is non-functional without these

- ✅ **WiFi AP + captive portal** (site.yml)
  - hostapd: WPA2-PSK AP on wlan0, SSID "MComzOS", configurable via vars
  - dnsmasq: DHCP 192.168.4.10-100, captive-portal DNS (address=/#/) on wlan0 only
  - avahi-daemon: broadcasts mcomz.local via mDNS
  - Static IP 192.168.4.1/24 via /etc/network/interfaces.d/
  - hostname set to mcomz; NetworkManager excluded from wlan0
  - rfkill unblock wifi to ensure radio is available

### P1 — Features described in README but not yet working

- ✅ **Kiwix ZIM content + systemd service** (site.yml)
  - kiwix-serve systemd unit on port 8888
  - Empty library.xml created so service starts with no ZIMs
  - Proxied by nginx at /library/
  - Note: actual ZIM files must still be added manually or via kiwix-manage

- ✅ **Missing systemd units** (site.yml)
  - `kiwix-serve` — port 8888, enabled
  - `direwolf` — /etc/direwolf.conf + systemd unit, AGWPORT 8010, KISSPORT 8011
  - `ardopcf` — TCP daemon on port 8515, after sound.target
  - `pat` — HTTP gateway on port 8081, config at ~/.config/pat/config.json

- ✅ **Dashboard backend** (src/dashboard/)
  - src/api/status.py: stdlib-only Python, polls systemctl is-active for all services
  - mcomz-status systemd service on localhost:9000
  - nginx proxies /api/ to status service
  - Dashboard HTML fully rewritten: live status dots, correct service links via /path/, UTC clock
  - MeshCore flash button links to flasher.meshcore.co.uk
  - All services accessible via nginx proxy paths — no port numbers exposed to users

### P1 (also) — Image build pipeline (needed for v0.1.0 release)

- ✅ **Raspberry Pi Imager repository JSON** (.github/workflows/build-image.yml)
  - `mcomzos-rpi-imager.json` generated during build with correct extract_size, extract_sha256, download_size, download_sha256
  - Users paste the release asset URL into Raspberry Pi Imager → Custom OS → enter URL → APPLY & RESTART works
  - JSON generated via python3 (avoids heredoc indentation issues in YAML)
  - Uploaded to GitHub Release alongside the .img.xz file

- ✅ **GitHub Actions image build workflow** (.github/workflows/build-image.yml)
  - Triggered on version tag push (pairs with existing auto-version.yml)
  - RPi ARM64: downloads official RPi OS Lite arm64, mounts via loop + qemu-user-static chroot, runs ansible
  - x86_64: debootstrap Debian Bookworm into GPT image (EFI), installs grub-efi, runs ansible
  - Both use fake systemctl + policy-rc.d to suppress service starts during build
  - `build_mode=true` extra-var skips raspi-config/overlayfs (which requires live Pi hardware)
  - `deb_arch` overridden per-arch via extra-vars (no ansible_architecture fact needed)
  - Artifacts named `mcomzos-rpi.img.xz` and `mcomzos-x86_64.img.xz`, published to GitHub Release
  - Note: site.yml also patched — raspi-config task guarded with `when: ansible_architecture == 'aarch64' and not (build_mode | default(false))`

### P1 — JS8Call headless operation (broken, needs fixes)

- ✅ **Missing `~/.vnc/xstartup`** — Deploy xstartup launching `openbox-session`; add `openbox` to apt installs

- ✅ **`mcomz-vnc.service` Type=forking without PIDFile** — Switched to `Type=simple` + `vncserver -fg`; `ExecStartPre=-` for graceful stale-lock cleanup

- ✅ **No JS8Call autostart inside VNC session** — Deploy `~/.config/openbox/autostart` starting `js8call &`; pi user added to `audio` group

- ✅ **noVNC nginx: split static files from WebSocket** — nginx `alias /usr/share/novnc/` at `/vnc/`; only `/vnc/websockify` proxied to websockify (no `--web`); dashboard link updated to `/vnc/vnc.html?path=vnc/websockify`

- ✅ **No D-Bus session in xstartup** — see blocker below; original `dbus-launch` fix was wrong

- ✅ **BLOCKER: `dbus-launch` not installed** — replaced with `dbus-run-session` (from `dbus-daemon`, always present via systemd dep)

- ✅ **noVNC does not autoconnect** — added `autoconnect=true` to dashboard URL

- ✅ **VNC password not documented for users** — added "VNC password: mcomz" hint on dashboard

- Note: `js8call` apt concern was a false alarm — package is in Debian Bookworm main (both amd64 and arm64)
- Note: `vncserver` Perl wrapper still functional in Bookworm but deprecated upstream; future Debian releases may require migration to `vncsession` / `tigervncserver@.service` template

### P1 — Bare-metal bootstrap blockers (build fails without these)

- ✅ **Ghost user — ARM64 build crash** (Phase 2): RPi OS Lite 2022+ has no `pi` user; `Create VNC password` fails with `invalid user: pi:pi`
  - Fix: add `user:` task in Phase 1 to ensure `mcomz_user` exists before Phase 2

- ✅ **Missing `git` — both builds crash** (Phase 3): `git` not in any apt install; `Clone ardopcf` and `Clone Mercury` fail
  - Fix: added `git` to Phase 1 base tools

- ✅ **Missing `python3-apt` — both builds crash** (Phase 4): Ansible `apt_repository` module requires `python3-apt`; absent from minimal images
  - Fix: added `python3-apt` to Phase 1 base tools

- ✅ **Missing `/opt/mcomz` dir — both builds crash** (MeshCore phase): `python3 -m venv /opt/mcomz/meshcore-venv` fails because `/opt/mcomz` doesn't exist
  - Fix: added `file: path=/opt/mcomz state=directory` task before venv creation

- ✅ **FreeDATA AppImage 404 — both builds crash** (Phase 3): FreeDATA does not publish AppImages; URL always 404s
  - Fix: added `ignore_errors: yes` — FreeDATA download is best-effort only

- ✅ **Mercury pip install crash — both builds** (Phase 3): `python3-pip` first installed in Phase 4 MeshCore section, but needed in Phase 3; also Debian Bookworm PEP 668 blocks bare pip installs
  - Fix: moved `python3-pip` to Phase 1 base tools; added `extra_args: --break-system-packages` to Mercury pip task; removed redundant `python3-pip` from Phase 4

- ✅ **Pat .deb URL wrong — both builds crash** (site.yml line 284): Pat releases use versioned filenames (`pat_0.19.2_linux_amd64.deb`), but URL uses `pat_linux_{{ deb_arch }}.deb` (no version). The `apt: deb:` task will 404 and abort.
  - Fix option A: Use GitHub API to dynamically resolve the latest .deb URL:
    ```yaml
    - name: Get Pat latest release URL
      shell: |
        curl -s https://api.github.com/repos/la5nta/pat/releases/latest \
          | python3 -c "import sys,json; assets=json.load(sys.stdin)['assets']; \
            print(next(a['browser_download_url'] for a in assets \
              if 'linux_{{ deb_arch }}.deb' in a['name']))"
      register: pat_deb_url
    - name: Install Pat (Winlink)
      apt:
        deb: "{{ pat_deb_url.stdout }}"
    ```
  - Fix option B: Hardcode a known-good version (e.g. `pat_0.19.2_linux_{{ deb_arch }}.deb`) and update manually on upgrades

- ✅ **Fake systemctl restored in both chroot builds**: `/usr/bin/systemctl` replaced with `exit 0` stub before Ansible runs; real binary saved as `systemctl.real` and restored in teardown. x86 stub installed after all `apt-get` steps to prevent dpkg overwriting it.

- ✅ **`ignore_errors: yes` on Phase 0 service enablement**: Removed `daemon_reload: yes` from enable/disable tasks (daemon reload not needed for symlink operations, was the chroot failure cause); `ignore_errors` no longer needed.

- ✅ **`ignore_errors: yes` on FreeDATA download** — replaced with `when: not (minimal_build | default(false))` (pre-alpha.5)

- ✅ **Pat service command wrong — runtime failure**: `ExecStart=/usr/bin/pat http` (port from config.json `http_addr`)

### P2 — x86 build (do not revisit until RPi builds cleanly with no error suppression)

- ✅ **gnupg missing on x86 debootstrap**: Added `gnupg` to Phase 1 base tools

- ✅ **OverlayFS on non-Pi hardware**: `overlayroot` package + `/etc/overlayroot.conf` with `overlayroot="tmpfs"` + `update-initramfs` handler; guarded by `ansible_architecture == 'x86_64'`

- ✅ **Re-enable x86 build**: `if: false` removed from `build-x86` job

### P2 — Other important but not blocking basic functionality

- ✅ **FreeDATA AppImage availability**: GitHub API probe replaces hardcoded URL; download task skipped gracefully if no AppImage published for arch

- ✅ **Mumble HTTPS for microphone access**: Self-signed cert generated via openssl (`/etc/ssl/mcomz/`); nginx now serves HTTPS on 443 and redirects HTTP→HTTPS; dashboard shows warning banner if loaded over HTTP

### P1 — Chroot build reliability (v0.0.2-pre-alpha series)

#### Phase A: Get the build green (use `ignore_errors` as scaffolding)

- ✅ **Fix meshtasticd enable** — uses `file: state=link` symlink pattern (same as all other services); no `ignore_errors` needed.
- ✅ **All service enables** — all use `file: state=link` to multi-user.target.wants; no daemon_reload tasks remain.
- ✅ **Meshtastic OBS repo tasks** — entire Meshtastic block wrapped in `block/rescue`; OBS unavailability prints a warning and continues build.
- ✅ **npm install timeout** — `shell: timeout 600 npm install -g mumble-web` with `block/rescue` for stall protection.

**High-risk tasks to monitor in build logs (may need fixes):**
- `npm install -g mumble-web` — webpack build under qemu emulation (~30-40% failure)
- `make` ardopcf — C compilation under qemu ARM64 (now fails loudly instead of skipping; may need to restore a retry)
- MeshCore `pip install` — `pymc_core[hardware]` native extensions under qemu ARM64 (still wrapped in `ignore_errors`)
- Pat GitHub API URL resolution — rate limiting risk even with token
- Meshtastic OBS repo availability

#### Phase A.5: Findings from v0.0.2-pre-alpha.7 build log (2026-04-08)

Build reported green (`ok=82 changed=58 failed=0 ignored=15`) but the `ignored=15` was hiding real problems. RPi job: 1h 36m. x86_64 job: 14m. Full log: run 24131314223.

**Service enable failures in chroot (9 units, all `Could not find the requested service … : host`):**
- avahi-daemon, mcomz-apmode-fallback, ardopcf, direwolf, pat, mcomz-mumble-ws, meshtasticd, mcomz-meshcore, kiwix-serve (plus mcomz-status, mcomz-vnc, mcomz-novnc that were already skirted with ignore_errors)
- Root cause: Ansible `service`/`systemd` module can't enumerate units inside a chroot mount.
- ✅ **Fixed:** replaced every `systemd: enabled=yes` with `file: state=link` creating the symlink directly in `/etc/systemd/system/multi-user.target.wants/`. This is exactly what `systemctl enable` does for simple `WantedBy=multi-user.target` units, and it works identically inside the chroot and on live systems. All 12 enable tasks are now chroot-safe with no `ignore_errors`.
- ✅ **Fixed** the cosmetic hostapd/dnsmasq init-script warnings the same way — disable is just `file: state=absent` on the wants symlink.

**Real bugs masked by `ignore_errors`:**
- ✅ **ardopcf repo URL wrong** — `https://github.com/pflarue/ardopcf.git` returns 404; the real repo is `pflarue/ardop` (binary built is named `ardopcf`). The clone was failing with `terminal prompts disabled` (GitHub's 401 response, masked as a credential prompt), `ignore_errors` swallowed it, and the downstream build/install tasks skipped silently. Fixed the URL and removed all `ignore_errors` / `is succeeded` guards from the ardopcf clone/build/install chain — failures will now surface.
- ✅ **FreeDATA skip** — confirmed working as designed (no ARM64 AppImage upstream; the API probe skips cleanly).
- ✅ **MeshCore install** — pyMC_Repeater has no `requirements.txt`; it uses `pyproject.toml` with entry point `repeater.main:main`. Rewrote as: `pip install file:///opt/meshcore-repeater` into the venv, deploy `/etc/pymc_repeater/config.yaml` (minimal SX1262 starter config), update systemd unit to `python -m repeater.main --config …`, create `/var/lib/pymc_repeater` storage dir. **Also gated the entire MeshCore block on `ansible_architecture == 'aarch64'`** — it's a LoRa HAT daemon with SPI/GPIO deps that has no use on x86 hardware. `ignore_errors` kept on the pip install itself since hardware extras (`pymc_core[hardware]`) can fail to build under qemu; the unit file and config still ship so users can finish the install on real hardware.
- ✅ **Mercury removed entirely** — the build was failing with `pulse/pulseaudio.h: No such file or directory` (missing libpulse-dev). Upstream only ships an apt repo for Debian 13 Trixie; Bookworm requires building from source, and the main consumer (FreeDATA) has no ARM64 build anyway. Left an inline comment pointing at `debian.hermes.radio` for when MComzOS moves to Trixie or FreeDATA ARM64 lands.

**Cosmetic / low priority:**
- ✅ **Node.js 20 deprecation** — bumped `actions/checkout@v4` → `v6` (Node 24) in both workflows. `softprops/action-gh-release` is still on Node 20 upstream (v2.6.1 has not yet migrated); leave as-is until upstream upgrades.
- ✅ hostapd/dnsmasq init-script warnings silenced by the symlink pattern above.

**Time hotspots (for future optimization, not urgent):**
- "Install hardware multiplexing and time-sync tools": 23 min (biggest single task, likely chrony + gpsd + i2c deps under qemu)
- Murmur install: 7 min
- meshtasticd install: 5 min
- Mercury build: 5 min → 0 min (removed)
- TigerVNC/noVNC/Openbox: 4 min

**Net effect:** expected alpha.8 build should install ardopcf correctly, install MeshCore cleanly on RPi, skip MeshCore on x86, enable all 12 services at boot (no more silent `ignored=15`), and not attempt Mercury. The build should either be truly green or fail loudly — no more hidden skips.

#### Phase B: Replace `ignore_errors` with proper chroot-safe patterns

Once the build is green and tested, systematically remove every `ignore_errors`:

- [ ] **Service enables**: Replace `systemd: enabled: yes` + `ignore_errors` with direct symlink creation (`file: state=link`) for chroot builds, guarded by `when: build_mode`. Keep the `systemd:` task for live installs. This is the correct fix — `systemctl enable` just creates symlinks, so we can do it without systemd running.
- [ ] **Meshtastic OBS repo**: Add a verification step that checks the repo is reachable before adding it; skip the entire Meshtastic block (repo + install + enable) if unavailable, rather than failing mid-sequence.
- [ ] **avahi-daemon enable**: Same symlink pattern as above; remove `ignore_errors`.
- [ ] **meshtasticd enable**: Same symlink pattern as above; remove `ignore_errors`.
- [ ] **Audit**: Confirm zero `ignore_errors` remain in site.yml. Every task either succeeds or fails the build intentionally.

#### Phase C: First flash and hardware validation

- [ ] Flash RPi image, boot, verify `https://mcomz.local` loads
- [ ] Dashboard: all service status dots showing correct state
- [ ] WiFi panel: scan, connect, forget, AP mode toggle
- [ ] Each service link: Kiwix, Pat, VNC (JS8Call), Mumble voice
- [ ] AP fallback: unplug router, wait 5 min, verify `MComzOS` hotspot appears
- [ ] x86: flash to USB, boot on a PC, same checks

## Post-v0.0.2 Roadmap

### WAN Remote Access (WireGuard VPN)
Currently the hub is LAN-only. WireGuard is the recommended approach (fully open source, aligns with "no closed ecosystems" philosophy).

- **Why:** "Internet is up but I'm not home" use case — access the dashboard, relay messages, check service status remotely.
- **Approach:** WireGuard peer config generated at provision time; hub is a peer, user devices are peers, a VPS or home router acts as the relay endpoint. Key generation and `wg0.conf` deployed by Ansible.
- **Alternatives considered:** Tailscale (coordination server is closed), Headscale (fully open, more complex to self-host), ZeroTier (similar trade-off to Tailscale).
- **Not a priority** when internet is down (core use case) — but valuable for pre-positioned hubs managed remotely.

### FreeDATA ARM64 Support
No ARM64 AppImage exists upstream (v0.17.8 only ships Windows + Ubuntu x86 binaries). FreeDATA is Python + Vue.js and can be built from source; the blocker is a bundled x86 `libcodec2.so` that needs replacing with the ARM64 system library (`/usr/lib/aarch64-linux-gnu/libcodec2.so.1.2`).

- **Correct fix:** Upstream PR to DJ2LS/FreeDATA adding ARM64 to their GitHub Actions build matrix.
- **Do not** work around this in MComzOS — the fix belongs in their repo.
- **Current behaviour:** Playbook silently skips FreeDATA if no AppImage found for the arch.

### APRS Map Viewer
Direwolf decodes APRS packets but there is no map UI. README updated to reflect this. A future release could add Xastir or a lightweight web-based APRS viewer.

## Service Port Map

| Service | Port | Status |
|---------|------|--------|
| Nginx (dashboard) | 80 | ✅ Configured |
| noVNC (JS8Call etc.) | 6080 | ✅ Configured |
| Mumble voice+text | 64737 | ✅ Configured |
| Meshtastic web UI | 8080 | ✅ Configured |
| MeshCore dashboard | 8000 | ✅ Configured |
| Murmur (native client) | 64738 | ✅ Installed |
| Meshtastic TCP API | 4403 | ✅ Installed |
| Kiwix | 8888 → /library/ | ✅ Running |
| Pat HTTP gateway | 8081 → /pat/ | ✅ Running |
| Direwolf APRS | 8010 (AGWPORT), 8011 (KISS) | ✅ Running |
| ardopcf HF modem | 8515 (TCP) | ✅ Running |
| Status API | 9000 → /api/ | ✅ Running |

## Post-v0.0.2 Dashboard Features (requested 2026-04-09)

### Inline service guides (offline-friendly)
- [ ] Mumble: inline "How to connect" guide on the dashboard card (don't rely on external docs link which requires internet). Cover: enter any username, leave password blank, allow microphone when prompted, push-to-talk vs voice-activated.
- [ ] JS8Call: brief inline guide covering the #MCOMZ net schedule and how to send a message
- [ ] Pat: inline guide covering callsign setup and sending a Winlink check-in

### Radio Communications tab
- [ ] Add a "Radio Communications" tab to the dashboard alongside "Mesh Communications"
- [ ] Gate licenced-radio features behind a question: "Do you have an Amateur Radio licence and a radio?"
  - If No: show explanation of what a licence enables, link to licensing info
  - If Yes: reveal JS8Call (VNC), Pat (Winlink), ardopcf, Direwolf APRS, FreeDATA (when available)
- [ ] Unlicenced LoRa hardware (Meshtastic, MeshCore) stays visible without the gate

### Admin login / protected functions
- [ ] Add a login screen protecting admin-only functions (simple password, stored locally — no internet auth)
- [ ] Protected functions include: power off / reboot RPi, WiFi settings panel, add Kiwix books, any action that could impact other users on the network
- [ ] Non-admin users can use all comms features without logging in

### Kiwix library onboarding
- [ ] Flash screen on first login (or if library is empty) suggesting the user adds at least WikiMed Medical Encyclopedia
- [ ] "Add Books" button in the Library section — requires login
- [ ] Recommended books list with variants (full / no-pic / mini) and approximate sizes:
  - Wikipedia (full, mini)
  - Wikipedia 0.8 (English simplified)
  - WikiMed Medical Encyclopedia
  - Appropedia (appropriate technology / survival)
  - Wikisource "The Free Library" (Bible, Shakespeare, etc.)
- [ ] Clicking a recommended book triggers a kiwix-manage download on the Pi (requires kiwix-manage integration in status.py API)

## Key Decisions Made
- TigerVNC + noVNC chosen over Wayland + RustDesk (lighter, browser-native, battle-tested)
- Mumble chosen over XMPP (voice + ephemeral text in one tool; persistent chat not needed for emergency comms)
- websockify used for Mumble bridge instead of mumble-web-proxy (avoids Rust compilation on Pi, already in apt)
- meshtasticd from OBS repo (official apt package, includes bundled web UI)
- pyMC_Repeater for MeshCore (Python, runs on Pi with LoRa HAT, has web dashboard)
