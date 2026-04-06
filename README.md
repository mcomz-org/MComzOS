# MComzOS: Project Specification (v0.0.1)

_**WARNING INITIAL COMMIT WAS 4 APRIL, THIS IS COMPLETELY UNTESTED: probably better to contact us before you start testing, or wait for v0.1.0, all assistance gratefully received**_

## Philosophy
MComzOS turns any computer* into an off-grid emergency communications hub. It is designed to be:

1. **Completely accessible** to users with zero IT or radio experience, yet
2. **a force multiplier** for IT professionals and licensed radio operators, unlocking their full potential in a crisis.

Even if you have zero interest in emergency communications, if you have a spare computer, we encourage you to spend 30 minutes setting it up today. Should the internet ever fail, you can then reach `http://mcomz.local` on any device and learn what to do next.

## Core Capabilities
Once deployed, your MComzOS hub provides:

- **With just a computer:**
  - **Offline Library:** Offline MComz guide and optional Wikipedia, survival guides, medical manuals, and any other books you would like to provide over your local WiFi network using [Kiwix](https://kiwix.org/).
  - **Offline Voice & Text Chat:** Browser-based voice and text channels that work on any smartphone without downloading an app, powered by [Mumble](https://www.mumble.info/). No internet required — just connect to the hub's WiFi and open your browser.

- Add **licence-free LoRa Radio(s):**
  - **Neighborhood Mesh Communications:** Monitor and communicate with the public [Meshtastic](https://meshtastic.org/) network, and/or
  - **Tactical Mesh:** Send and receive secure, multi-hop text messages over the [MeshCore](https://meshcore.co.uk/) network. AND let other LoRa users within WiFi range flash MeshCore to their devices and join, should the Meshtastic net become overwhelmed.

- And if you are (or have access to) a **licensed radio operator** you can add:
  - **HF radio:**
    - **Extreme Weak-Signal Paging:** Join us on the #MCOMZ net (currently 1500Z Sundays at 7078 MHz) using [JS8Call](http://js8call.com/) — accessible from any browser on your hub's network, no software to install.
    - **Internet-Free Email:** Automated global email via [Pat](https://getpat.io) — browser-based interface included.
    - **Peer-to-Peer File Transfer:** Share files directly over the air with [Pat](https://getpat.io) and, coming soon, [FreeDATA](https://freedata.app/) — accessible from any browser on your hub's network, no software to install.
    - **Automated Data Sync (Coming Soon):** Maintain and update your MComzOS autonomously, following testing this will be powered by [Rhizomatica](https://www.rhizomatica.org/)'s HERMES v2 Mercury, [FreeDATA](https://freedata.app/) or [Pat](https://getpat.io).
  - **VHF/UHF radio:**
    - **Tactical Radar:** Decode APRS telemetry using [Direwolf](https://github.com/wb2osz/direwolf) to visually plot local emergency responders and mobile units on an offline map.
    - **Regional Email:** Connect to local Winlink gateways over VHF packet radio for robust, mid-range message delivery.

MComzOS is strictly open-source. No proprietary licenses, no internet-dependent authentication, and no closed ecosystems. If the global internet falls, MComzOS survives. See [STACK.md](STACK.md) for the full list of open-source tools that make this possible.

## Installation

> **Pre-built images are planned for v0.1.0.** The steps below describe the intended install flow. Until then, see [Manual installation](#manual-installation) below.

### Raspberry Pi — SD card or USB boot

1. Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Open Imager → **Choose OS** → scroll to the bottom → **Use custom** → paste this URL and press Enter:
   ```
   https://github.com/mcomz-org/MComzOS/releases/latest/download/mcomzos-rpi-imager.json
   ```
3. **Choose Storage** → select your SD card or USB drive (16 GB minimum)
4. Click **Next** → configure Wi-Fi / SSH if desired → **Write**

> **Note:** The URL above points to a metadata file that Raspberry Pi Imager understands. If you paste the direct `.img.xz` link instead, the **APPLY & RESTART** button will be greyed out.

### PC, Mac, or any 64-bit computer — USB boot

To keep the setup experience and resulting system identical to the Raspberry Pi version, we use the same flashing tool on all platforms:

1. Download [Balena Etcher](https://etcher.balena.io/) — free, works on Windows, Mac, and Linux
2. Open Etcher → **Flash from URL** → paste:
   ```
   https://github.com/mcomz-org/MComzOS/releases/latest/download/mcomzos-x86_64.img.xz
   ```
3. Select your USB drive (16 GB minimum) and click **Flash**
4. Boot the target computer from the USB drive — usually F12 or Delete to open the boot menu

> **Tip:** Balena Etcher also works for Raspberry Pi if you prefer one tool across all hardware.

### First boot

Once powered on, your hub will broadcast its own WiFi network. Connect any device to that network and open a browser:

```
http://mcomz.local
```

You will see the MComzOS dashboard with all available services listed.

### Manual installation

For developers who want to run MComzOS on top of an existing Debian 12 (Bookworm) system:

```bash
git clone https://github.com/mcomz-org/MComzOS.git
cd MComzOS
ansible-playbook site.yml -i your-host,
```

Requires Ansible 2.10+ on the control machine. The target must be running Debian 12 (Bookworm) on a 64-bit processor (ARM64 or x86_64). See [STACK.md](STACK.md) for everything that will be installed.

---

## Hardware Requirements
*By "any computer," we mean almost** any modern PC, Mac, or Raspberry Pi. As long as it's less than 15 years old, has at least 2GB of RAM, and can boot from a USB drive or SD card, it is a candidate for your hub. Optimal use requires external radios and licenses, but the hub provides significant local benefit even without them.

**Specifically, it must support a 64-bit architecture (x86_64 for Intel/AMD PCs and Macs, or ARM64 for Raspberry Pi 3/4/5). 32-bit processors and first-generation Raspberry Pis are not supported.
