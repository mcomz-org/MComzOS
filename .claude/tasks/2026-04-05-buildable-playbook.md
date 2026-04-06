# MComzOS: Road to Buildable Playbook

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

- [ ] **Fake systemctl removed — `daemon_reload` tasks may fail in chroot** (build-image.yml): Gemini removed the fake systemctl stub, relying on real systemctl behaviour. Phase 0 service enablement has `ignore_errors: yes` but all other `systemd: daemon_reload: yes` tasks (VNC, ardopcf, direwolf, pat, mumble, meshtasticd, meshcore, kiwix, mcomz-status) do not. **v0.0.1-pre-alpha.5 build passed with warning "Target is a chroot or systemd is offline"** — daemon_reload tasks appear to have succeeded or been skipped (minimal_build). Monitor full build logs when minimal_build=false. If daemon-reload fails, the correct fix is restoring the fake stub — NOT adding more `ignore_errors`.

- [ ] **`ignore_errors: yes` on Phase 0 service enablement** (site.yml line ~129): Added by Gemini to suppress SysV init warnings. Should be replaced with a proper fix once the root cause is understood (likely systemctl not finding a running D-Bus in chroot). Not acceptable long-term.

- ✅ **`ignore_errors: yes` on FreeDATA download** — replaced with `when: not (minimal_build | default(false))` (pre-alpha.5)

- [ ] **Pat service command wrong — runtime failure** (site.yml line 431): `ExecStart=/usr/bin/pat --listen :8081 http` — Pat has no `--listen` flag; HTTP address comes from config.json `http_addr`. Won't fail the build but Pat service will not start at runtime.
  - Fix: Change to `ExecStart=/usr/bin/pat http`

### P2 — x86 build (do not revisit until RPi builds cleanly with no error suppression)

- [ ] **gnupg missing on x86 debootstrap** (site.yml line 493): `gpg --dearmor` for Meshtastic key requires `gnupg`; debootstrap installs only `gpgv`. RPi OS Lite has gnupg pre-installed.
  - Fix: Add `gnupg` to Phase 1 base tools

- [ ] **OverlayFS on non-Pi hardware** (site.yml)
  - `raspi-config nonint enable_overlayfs` only works on Raspberry Pi
  - Need conditional task or alternative for x86_64 (e.g. overlayroot package)

- [ ] **Re-enable x86 build** (build-image.yml): Disabled with `if: false`. Re-enable only after RPi builds cleanly and all `ignore_errors` are removed.
  - Fix: Remove `if: false` from `build-x86` job

### P2 — Other important but not blocking basic functionality

- [ ] **FreeDATA ARM64 AppImage availability**
  - FreeDATA may not publish ARM64 AppImages — URL may 404
  - Needs verification or alternative install method (build from source, Docker)

- [ ] **Mumble HTTPS for microphone access**
  - Browsers require HTTPS for `getUserMedia()` (microphone)
  - Need self-signed TLS cert generation task in site.yml
  - nginx TLS config to terminate HTTPS for mumble-web and noVNC

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

## Key Decisions Made
- TigerVNC + noVNC chosen over Wayland + RustDesk (lighter, browser-native, battle-tested)
- Mumble chosen over XMPP (voice + ephemeral text in one tool; persistent chat not needed for emergency comms)
- websockify used for Mumble bridge instead of mumble-web-proxy (avoids Rust compilation on Pi, already in apt)
- meshtasticd from OBS repo (official apt package, includes bundled web UI)
- pyMC_Repeater for MeshCore (Python, runs on Pi with LoRa HAT, has web dashboard)
