# MComzOS Tech Stack

Every component is open-source. No proprietary software, no internet-dependent licensing.

---

## Provisioning

| Tool | Role |
|------|------|
| [Ansible](https://www.ansible.com/) | Automated provisioning — the `site.yml` playbook builds the full hub image |

---

## Core Infrastructure

| Tool | Role |
|------|------|
| [Nginx](https://nginx.org/) | Web server and reverse proxy — serves the hub dashboard and proxies to local services |
| [PipeWire](https://pipewire.org/) | Audio multiplexing — allows multiple radio apps to share the sound card |
| [GPSd](https://gpsd.gitlab.io/gpsd/) | GPS daemon — feeds location and precise time to the hub |
| [Chrony](https://chrony-project.org/) | Time synchronisation — uses GPS as a reference clock for accurate offline timekeeping |
| [RTL-SDR](https://www.rtl-sdr.com/) | Software-defined radio driver — enables USB SDR dongles for signal monitoring |
| [Hamlib](https://hamlib.github.io/) | Radio control library — standardised CAT/CI-V control for connected transceivers |
| [TigerVNC](https://tigervnc.org/) + [noVNC](https://novnc.com/) + [websockify](https://github.com/novnc/websockify) | Headless VNC server + browser remote desktop — runs GUI radio apps (JS8Call, FreeDATA) accessible from any browser on the LAN |
| [OverlayFS](https://www.kernel.org/doc/html/latest/filesystems/overlayfs.html) | Read-only root filesystem — protects the SD card from corruption on power loss |
| [Chromium](https://www.chromium.org/) + [Openbox](http://openbox.org/) | Kiosk display — auto-launches full-screen dashboard when a monitor is connected |

---

## Voice & Text (Offline LAN)

| Tool | Role |
|------|------|
| [Mumble](https://www.mumble.info/) / [Murmur](https://github.com/mumble-voip/mumble) | Low-latency voice and text server — the hub's offline comms backbone |
| [mumble-web](https://github.com/johni0702/mumble-web) | HTML5 Mumble client — browser-based access, no app install required |

---

## Offline Library

| Tool | Role |
|------|------|
| [Kiwix](https://kiwix.org/) | Offline content server — serves ZIM archives (MComzLibrary survival/literature/scriptures, WikiMed, and user-added books) over WiFi |

---

## Licence-Free Mesh Radio (LoRa)

| Tool | Role |
|------|------|
| [Meshtastic](https://meshtastic.org/) / [meshtasticd](https://meshtastic.org/docs/software/linux/) | Civilian LoRa mesh — Linux daemon that runs a full Meshtastic node and serves a browser UI |
| [MeshCore](https://meshcore.co.uk/) / [meshcore-gui](https://github.com/pe1hvh/meshcore-gui) | Tactical encrypted mesh — NiceGUI web app that connects to a MeshCore radio over USB serial or BLE |
| [MeshCore](https://meshcore.co.uk/) / [pyMC_Repeater](https://github.com/rightup/pyMC_Repeater) | Tactical encrypted mesh — Python repeater daemon for an SPI LoRa HAT (installed but not proxied by default) |

---

## HF Radio (Licensed Operators)

| Tool | Role |
|------|------|
| [JS8Call](http://js8call.com/) | Weak-signal keyboard-to-keyboard messaging over HF using JS8 protocol |
| [Pat](https://getpat.io) | Winlink email client and gateway — internet-free email over HF and VHF, with built-in web UI |
| [ardopcf](https://github.com/pflarue/ardop) | ARDOP HF modem — active fork; provides the soundcard modem Pat uses for HF connections |
| [FreeDATA](https://freedata.app/) | Peer-to-peer HF file transfer — direct data exchange without infrastructure (ARM64 AppImage pending upstream) |

---

## VHF/UHF Radio (Licensed Operators)

| Tool | Role |
|------|------|
| [Direwolf](https://github.com/wb2osz/direwolf) | Software TNC — decodes APRS telemetry from VHF for tactical situational awareness |
