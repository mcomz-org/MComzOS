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

### P2 — Important but not blocking basic functionality

- [ ] **OverlayFS on non-Pi hardware** (site.yml line 313)
  - `raspi-config nonint enable_overlayfs` only works on Raspberry Pi
  - Need conditional task or alternative for x86_64 (e.g. overlayroot package)

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
