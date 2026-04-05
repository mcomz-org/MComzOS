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

- [ ] **Kiwix ZIM content + systemd service** (site.yml)
  - Deploy a `kiwix-serve` systemd unit pointing at `/var/mcomz/library/`
  - Download at minimum the MComz guide ZIM (needs a URL or build step)
  - Add nginx proxy rule so Kiwix is accessible from the dashboard
  - Consider optional Wikipedia/survival guide ZIM downloads

- [ ] **Missing systemd units** (site.yml)
  - `kiwix-serve` — not started as a daemon
  - `direwolf` — installed but no unit, no config (audio device, APRS port)
  - `ardopcf` — built but needs to run as a TCP modem daemon for Pat
  - `pat` — gateway/HTTP mode needs a unit for browser access

- [ ] **Dashboard backend** (src/dashboard/)
  - Current HTML is a static mockup with fake data
  - Needs: live Meshtastic feed (meshtasticd API on port 4403 or web on 8080)
  - Needs: real service status checks (systemd D-Bus or simple HTTP health)
  - Needs: actual links to running services (correct ports for Pat, FreeDATA, etc.)
  - The "Flash Radio to MeshCore" button needs ESP Web Tools integration or link to flasher.meshcore.co.uk
  - Consider: lightweight Python/Node backend, or pure JS polling from browser

### P1 (also) — Image build pipeline (needed for v0.1.0 release)

- [ ] **GitHub Actions image build workflow** (.github/workflows/build-image.yml)
  - Triggered on version tag push (pairs with existing auto-version.yml)
  - RPi: use `pi-gen` or `pi-gen-action` to produce `mcomzos-rpi.img.xz`
  - x86_64: use `live-build` or `packer` to produce `mcomzos-x86_64.img.xz`
  - Both images built from `site.yml` playbook
  - Artifacts attached to GitHub Release automatically
  - Filename must match exactly what RPi Imager and Etcher expect (`.img.xz`)
  - RPi Imager is strict about filenames — must be `*.img.xz`, `*.img.gz`, or `*.zip`

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
| Kiwix | TBD | ❌ No unit |
| Pat HTTP gateway | TBD | ❌ No unit |
| Direwolf APRS | TBD | ❌ No unit |

## Key Decisions Made
- TigerVNC + noVNC chosen over Wayland + RustDesk (lighter, browser-native, battle-tested)
- Mumble chosen over XMPP (voice + ephemeral text in one tool; persistent chat not needed for emergency comms)
- websockify used for Mumble bridge instead of mumble-web-proxy (avoids Rust compilation on Pi, already in apt)
- meshtasticd from OBS repo (official apt package, includes bundled web UI)
- pyMC_Repeater for MeshCore (Python, runs on Pi with LoRa HAT, has web dashboard)
