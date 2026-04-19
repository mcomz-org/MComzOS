# MComzOS: Project Specification

_**WARNING INITIAL COMMIT WAS 4 APRIL, THIS IS COMPLETELY UNTESTED: probably better to contact us before you start testing, or wait for v0.1.0, all assistance gratefully received**_

## Philosophy
MComzOS turns any computer* into an off-grid emergency communications hub. It is designed to be:

1. **Completely accessible** to users with zero IT or radio experience, yet
2. **a force multiplier** for IT professionals and licensed radio operators, unlocking their full potential in a crisis.

Even if you have zero interest in emergency communications, if you have a spare computer, we encourage you to spend 30 minutes setting it up today. Should the internet ever fail, you can then reach `https://mcomz.local` on any device and learn what to do next.

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
    - **Extreme Weak-Signal Paging:** Join us on the #MCOMZ net (currently 1500Z Sundays at 7078 MHz) using [JS8Call](http://js8call.com/) — accessible from any browser on your hub's network, no software to install. The remote desktop password is `mcomz`.
    - **Internet-Free Email:** Automated global email via [Pat](https://getpat.io) — browser-based interface included.
    - **Peer-to-Peer File Transfer:** Share files directly over the air with [Pat](https://getpat.io) — accessible from any browser on your hub's network, no software to install. [FreeDATA](https://freedata.app/) integration is planned once upstream ships an ARM64 build.
    - **Automated Data Sync (Coming Soon):** Maintain and update your MComzOS autonomously over HF, powered by [Pat](https://getpat.io) (and [FreeDATA](https://freedata.app/) when available on ARM64).
  - **VHF/UHF radio:**
    - **APRS Telemetry:** Decode APRS position and telemetry packets from VHF radio using [Direwolf](https://github.com/wb2osz/direwolf). (Visual map plotting is planned for a future release.)
    - **Regional Email:** Connect to local Winlink gateways over VHF packet radio for robust, mid-range message delivery.

MComzOS is strictly open-source. No proprietary licenses, no internet-dependent authentication, and no closed ecosystems. If the global internet falls, MComzOS survives. See [STACK.md](STACK.md) for the full list of open-source tools that make this possible.

## Installation

You can expect the setup process to take around 15–30 minutes (mostly waiting for the image to write).

Before you begin you'll need:
- A Raspberry Pi 4 or 5, or any 64-bit PC (x86_64 support is experimental from v0.0.2-pre-alpha)
- A blank microSD card or USB drive — **16 GB minimum**, 32 GB recommended
- A suitable power supply for your Raspberry Pi
- A computer with internet access and the ability to write to a microSD card or USB drive

### Step 1 — Install Raspberry Pi Imager

Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) for your operating system (Windows, macOS, or Linux).

### Step 2 — Add the MComzOS repository

Open Raspberry Pi Imager. **Before choosing a device or OS**, click **APP OPTIONS** in the bottom-left corner.

Click **EDIT** next to **Content Repository**.

Select **Use custom URL** and paste:
```
https://mcomz-org.github.io/MComzOS/os-list.json
```

Click **Apply & restart.**

### Step 3 — Choose your Raspberry Pi model

After Imager restarts, select your Raspberry Pi model (in the **Device** tab). Click **NEXT**.

### Step 4 — Choose MComzOS

**MComzOS** should appear at the top of the list (in the **OS** tab). Select it and click **NEXT**.

### Step 5 — Choose your storage device

Select your microSD card or USB drive (in the **Storage** tab).

> **Warning:** Everything on the selected drive will be erased. Double-check you've selected the right device.

Click **NEXT**.

### Step 6 — Configure Wi-Fi and SSH (recommended)

- Set a hostname (e.g. `mcomz`) and click **NEXT**.
- Set your Capital city: (mine is `London (United Kingdom)`), your time zone (mine is `Europe/London`) and keyboard layout (mine is `gb`) and click **NEXT**.
- Set the Username to **`mcomz`** (this is required — MComzOS services run as this user), set and confirm a password for your device twice then click **NEXT**.
- Under SSID enter your Wi-Fi network name and enter your network password twice then click **NEXT**.
- Enable SSH and select your preferred means of authentication then click **NEXT**.

### Step 7 — Write the image

Check the summary then click **WRITE** if it is correct, and confirm when prompted. Writing takes around 5–10 minutes.

Once complete, safely eject the card or drive.

### Step 8 — First boot

Insert the microSD card (or USB drive) into your Raspberry Pi and plug in power. The hub takes around 60–90 seconds to start up on first boot.

Your hub will join your home WiFi (or ethernet) network and be accessible at:

```
https://mcomz.local
```

> **First-visit certificate warning:** MComzOS uses a self-signed HTTPS certificate so that browser microphone access (required for voice chat) works. On first visit your browser will show a security warning — this is expected. Click **Advanced → Proceed** (Chrome/Edge) or **Show Details → visit this website** (Safari) to continue. You only need to do this once per device.

You will see the MComz dashboard with all available services listed.

> **Emergency / no-router mode:** If the hub cannot get a network address within 5 minutes of booting (e.g. your router is down or unavailable), it will automatically fall back to broadcasting its own WiFi hotspot — **SSID: MComzOS**, password: `mcomzos1`. Connect to that network and open `https://mcomz.local` as normal. No configuration is required; this happens automatically.

---

### PC, Mac, or any 64-bit computer — USB boot

> **Note:** x86_64 image builds are re-enabled from v0.0.2-pre-alpha and considered experimental — not yet validated on real hardware. If you test one, please report findings as an issue.

1. Download [Balena Etcher](https://etcher.balena.io/) — free, works on Windows, Mac, and Linux
2. Open Etcher → **Flash from URL** → paste:
   ```
   https://github.com/mcomz-org/MComzOS/releases/latest/download/mcomzos-x86_64.img.xz
   ```
3. Select your USB drive (16 GB minimum) and click **Flash**
4. Boot the target computer from the USB drive — usually F12 or Delete to open the boot menu

### Manual installation (developers)

To run MComzOS on top of an existing Debian 12 (Bookworm) system:

```bash
git clone https://github.com/mcomz-org/MComzOS.git
cd MComzOS
ansible-playbook site.yml -i your-host,
```

Requires Ansible 2.10+ on the control machine. The target must be running Debian 12 (Bookworm) on a 64-bit processor (ARM64 or x86_64). See [STACK.md](STACK.md) for everything that will be installed.

---

## Trademarks and Logos

Brand logos displayed in the MComzOS dashboard are used for nominative identification only — they identify buttons that open the named software. They are the property of their respective owners and MComzOS is not affiliated with or endorsed by any of them.

- Meshtastic® is a registered trademark of Meshtastic LLC. The M-PWRD badge is used per the [Meshtastic community logo policy](https://meshtastic.org/docs/legal/licensing-and-trademark/).
- MeshCore, Mumble, JS8Call, Pat/Winlink, and FreeDATA logos and names are property of their respective owners.

See [`src/dashboard/icons/LICENSES.md`](src/dashboard/icons/LICENSES.md) for full attribution.

---

## Hardware Requirements
*By "any computer," we mean almost** any modern PC, Mac, or Raspberry Pi. As long as it's less than 15 years old, has at least 2GB of RAM, and can boot from a USB drive or SD card, it is a candidate for your hub. Optimal use requires external radios and licenses, but the hub provides significant local benefit even without them.

**Specifically, it must support a 64-bit architecture (x86_64 for Intel/AMD PCs and Macs, or ARM64 for Raspberry Pi 3/4/5). 32-bit processors and first-generation Raspberry Pis are not supported.
