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

- ✅ **Mumble HTTPS for microphone access**: Self-signed cert generated via openssl (`/etc/ssl/mcomz/`); nginx serves HTTPS on 443 for Mumble mic access; HTTP on 80 serves the dashboard directly (no redirect — avoids iOS Safari cert loop); HTTPS root shows redirect-to-HTTP page

### P1 — Chroot build reliability (v0.0.2-pre-alpha series)

#### Phase A: Get the build green (use `ignore_errors` as scaffolding)

- [ ] **Fix meshtasticd enable** — same chroot failure as avahi-daemon (package-installed unit, no init script). Add `ignore_errors: yes` with comment.
- [ ] **Add `ignore_errors: yes` to ALL `daemon_reload: yes` service enable tasks** — in chroot builds the fake systemctl makes daemon_reload meaningless; the unit files are on disk and systemd picks them up on real boot. This eliminates the entire class of "service not found in chroot" failures.
- [ ] **Add `ignore_errors: yes` to Meshtastic OBS repo tasks** — external third-party repo is outside our control; if download.opensuse.org is unavailable the build shouldn't die.
- [ ] **Add timeout to `npm install -g mumble-web`** — webpack postinstall under qemu ARM64 emulation can stall; default npm timeout may exceed GitHub Actions step limits.

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

### P1 — Runtime/UX bugs (dashboard and nginx)

#### Bug 1: VNC "Connect" button loops without showing password dialog

**Status:** ✅ Fixed (2026-04-14)

**Root cause:** Dashboard links (`index.html:236,243`) used `path=websockify` but the nginx WebSocket proxy lives at `/vnc/websockify`. noVNC's `path` parameter is a full URL path (no leading slash), so it tried `ws://host/websockify` — no matching nginx location — and retried in a loop with `autoconnect=true`.

**What was NOT wrong:** Xvnc binding (localhost:5901 ✓), websockify target (localhost:5901 ✓), service ordering (`After=`/`Requires=` mcomz-vnc.service ✓), rfbport (default 5901 for display :1 ✓).

**Fix:** Changed `path=websockify` → `path=vnc/websockify` in both VNC links.

#### Bug 2: iOS Safari HTTPS loop with self-signed cert

**Status:** ✅ Fixed (2026-04-14)

**Root cause:** nginx port 80 returned `301 https://`. iOS Safari auto-upgrades bare hostnames to HTTPS. With a self-signed cert, Safari shows "This Connection Is Not Private" — and even after tapping "Visit Website", subsequent fetch() calls to `/api/status` etc. can re-trigger the block, causing a loop.

**Tension:** Mumble needs HTTPS for `getUserMedia()` (microphone), but the dashboard should be accessible without cert hassle.

**Fix:**
- Port 80: serves the full dashboard and all service proxies directly (no redirect)
- Port 443: root `/` returns a minimal HTML page redirecting to HTTP; all other locations (`/api/`, `/mumble/`, `/library/`, etc.) remain functional for HTTPS-dependent features
- Dashboard Mumble link changed to explicit `https://` for microphone access
- HTTPS warning banner updated to explain the HTTP/HTTPS split and link to HTTPS Mumble

#### Bug 3: MeshCore flasher requires internet (offline unusable)

**Status:** ✅ Fixed (2026-04-15)

**Problem:** "Flash MeshCore" button linked to `flasher.meshcore.co.uk` which requires internet. In hotspot/offline mode (the primary use case), this fails.

**Research findings:**
- The MeshCore flasher (`meshcore-dev/flasher.meshcore.io`) is a self-contained static Vue.js app (no build step needed) with its own bundled esptool-js wrapper, config.json manifest, and `/lib/` JS dependencies.
- It is NOT using esptool-js or esp-web-tools directly — it's a custom Vue app that wraps `esp32.js` (a bundled esptool-js build).
- `config.json` (148 KB) controls device types, firmware roles, and version metadata. Key field: `staticPath` sets the firmware binary base URL.
- Firmware binaries live at `github.com/meshcore-dev/MeshCore/releases`, filtered by `heltec` in asset name.
- The flasher uses absolute URL paths (`/lib/`, `/css/`, `/config.json`) so direct subpath serving would break without path patching.

**Fix (site.yml + index.html):**
1. **Provisioning:** `git clone --depth=1 meshcore-dev/flasher.meshcore.io` into `/var/www/html/meshcore-flash/`. Python patch script rewrites absolute paths in `index.html` and `flasher.js` to `/meshcore-flash/`-prefixed versions; sets `staticPath` to `/meshcore-flash/firmware` in `config.json`. GitHub API resolves and downloads all Heltec V3/V4 firmware `.bin` assets. Entire block is in block/rescue so build doesn't fail if GitHub is slow.
2. **nginx:** Added `location /meshcore-flash/` alias to both HTTP and HTTPS server blocks.
3. **Dashboard:** Flash button replaced with `openMeshFlasher()` JS function — probes `flasher.meshcore.co.uk/favicon.ico` with 3s timeout (using `navigator.onLine` as quick gate); routes to online or local flasher accordingly. Button shows "Checking connection…" while probing.

**Known limitation:** If the flasher app uses any absolute path not covered by the regex patch (e.g. dynamic paths constructed in Vue components), those would 404. Needs validation on first flash.

#### Phase C: First flash and hardware validation

- [ ] Flash RPi image, boot, verify `http://mcomz.local` loads (HTTP, not HTTPS)
- [ ] Dashboard: all service status dots showing correct state
- [ ] WiFi panel: scan, connect, forget, AP mode toggle
- [ ] Each service link: Kiwix, Pat, VNC (JS8Call), Mumble voice (via HTTPS)
- [ ] iOS Safari: verify no HTTPS redirect loop, Mumble mic works after cert accept
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
| Nginx (dashboard + offline flasher) | 80 | ✅ Configured |
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

## Key Decisions Made
- TigerVNC + noVNC chosen over Wayland + RustDesk (lighter, browser-native, battle-tested)
- Mumble chosen over XMPP (voice + ephemeral text in one tool; persistent chat not needed for emergency comms)
- websockify used for Mumble bridge instead of mumble-web-proxy (avoids Rust compilation on Pi, already in apt)
- meshtasticd from OBS repo (official apt package, includes bundled web UI)
- pyMC_Repeater for MeshCore (Python, runs on Pi with LoRa HAT, has web dashboard)
