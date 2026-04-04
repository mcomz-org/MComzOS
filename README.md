# MComzOS: Project Specification (v0.0.1)

## Philosophy
MComzOS turns any computer* into an off-grid emergency communications hub. It is designed to be:

1. **Completely accessible** to users with zero IT or radio experience, yet
2. **a force multiplier** for IT professionals and licensed radio operators, unlocking their full potential in a crisis.

Even if you have zero interest in emergency communications, if you have a spare computer, we encourage you to spend 30 minutes setting it up today. Should the internet ever fail, you can then reach `http://mcomz.local` on any device and learn what to do next.

## Core Capabilities
Once deployed, your MComzOS hub provides:

- **With just a computer:**
  - **Offline Library:** Offline MComz guide and optional Wikipedia, survival guides, medical manuals, and any other books you would like to provide over your local WiFi network using [Kiwix](https://kiwix.org/).
  - **Offline Mobile Communications:** Browser-based voice and text chat that works on any smartphone without downloading an app, powered by [MiroTalk](https://mirotalk.com/).

- Add **licence-free LoRa Radio(s):**
  - **Neighborhood Mesh Communications:** Monitor and communicate with the public [Meshtastic](https://meshtastic.org/) network, and/or
  - **Tactical Mesh:** Send and receive secure, multi-hop text messages over the [MeshCore](https://meshcore.co.uk/) network. AND let other LoRa users within WiFi range flash MeshCore to their devices and join, should the Meshtastic net become overwhelmed.

- And if you are (or have access to) a **licensed radio operator** you can add:
  - **HF radio:**
    - **Extreme Weak-Signal Paging:** Join us on the #MCOMZ net (currently 1500Z Sundays) using [JS8Call](http://js8call.com/).
    - **Internet-Free Email:** Automated global email via [Pat](https://getpat.io).
    - **Peer-to-Peer File Transfer:** Share files directly over the air with [FreeDATA](https://freedata.app/).
    - **Automated Data Sync:** Maintain and update your MComzOS autonomously, powered by [Rhizomatica](https://www.rhizomatica.org/)'s HERMES v2 Mercury.
  - **VHF/UHF radio:**
    - **Tactical Radar:** Decode APRS telemetry using [Direwolf](https://github.com/wb2osz/direwolf) to visually plot local emergency responders and mobile units on an offline map.
    - **Regional Email:** Connect to local Winlink gateways over VHF packet radio for robust, mid-range message delivery.

MComzOS is strictly open-source. No proprietary licenses, no internet-dependent authentication, and no closed ecosystems. If the global internet falls, MComzOS survives.

---

### Hardware Requirements
*By "any computer," we mean almost** any modern PC, Mac, or Raspberry Pi. As long as it's less than 15 years old, has at least 2GB of RAM, and can boot from a USB drive or SD card, it is a candidate for your hub. Optimal use requires external radios and licenses, but the hub provides significant local benefit even without them.

**Specifically, it must support a 64-bit architecture (x86_64 for Intel/AMD PCs and Macs, or ARM64 for Raspberry Pi 3/4/5). 32-bit processors and first-generation Raspberry Pis are not supported.

---

## 1. The Neighborhood Hub (Unlicensed & Zero-Skill)
You do not need a radio license to use the core features of MComzOS. In a grid-down scenario, MComzOS acts as a standalone community command center for anyone with a standard smartphone.

* **Zero-App Dashboard:** A captive portal hosts the MComz Web UI. Anyone connecting to the MComz Wi-Fi bubble can view offline resources or send messages via their mobile browser—no app installations required.
* **The Offline Library (Kiwix):** Pre-loaded with `MComz.zim`, containing a localized Wikipedia slice, survival medicine manuals, and emergency operating procedures.
* **Local Voice (Murmur):** An offline VoIP server. Volunteers with smartphones can use the free Mumble app to turn the MComz Wi-Fi bubble into an encrypted, push-to-talk tactical voice network.

---

## 2. The Local Mesh (Dual-Network Architecture)
MComzOS uses a dual-node LoRa strategy. It bridges the massive, pre-existing civilian off-grid community with the high-performance tactical networks required by emergency response teams.

* **Civilian Monitoring (Meshtastic):** By connecting a standard Meshtastic node via USB, the Web Dashboard provides a secure, read-only feed of public `LongFast` traffic. This allows your basecamp to monitor the community and receive SOS broadcasts.
* **Tactical Operations (MeshCore):** This is the operational standard for MComz. MeshCore provides the high-bandwidth, strict channel discipline, and routing efficiency required for basecamp logistics.
* **The Local Forge (Offline Flasher):** Every MComzOS deployment natively includes the "Local Forge." Any civilian can connect to the Wi-Fi, click "Flash," and convert their jammed Meshtastic radio to the encrypted MComz MeshCore standard directly from their web browser in under 60 seconds.

---

## 3. The Tactical Radio Suite (Licensed Operators)
For licensed Amateur Radio operators, MComzOS unlocks an automated global communication stack.

* **P2P File Transfer (FreeDATA):** The human-facing HF tool. Uses modern Codec2 OFDM to provide an error-corrected chat and file-transfer GUI.
* **The Heartbeat (JS8Call):** Runs continuously in the background for extreme weak-signal global paging and automated grid-status reporting.
* **Legacy Internet Gateway (Pat + ardopcf):** A web-based email client using the ARDOP protocol to bridge HF radio into the existing global Winlink infrastructure.
* **High-Speed M2M Sync (Mercury / HERMES v2):** The background workhorse. Acts as a TCP/IP bridge over HF radio to automatically pull cryptographically signed `git diff` software updates without user intervention.
* **Tactical VHF (Direwolf):** A software TNC running in the background to decode APRS telemetry and visually plot local emergency responders on an offline map.

---

## 4. Under the Hood (Core Infrastructure & System Resilience)
MComzOS is built on a rock-solid foundation of Debian 64-bit and heavily hardened for field deployments.

* **Read-Only File System (OverlayFS):** The core OS is locked down. Users can suddenly pull the power cord in a panic without corrupting the drive.
* **Headless Wayland (`labwc`):** Utilizes a modern software-only Wayland compositor (`WLR_BACKENDS=headless`), guaranteeing remote desktop access works flawlessly without HDMI dummy plugs.
* **Remote Field Command (RustDesk + Headscale):** Fully encrypted, internet-free remote desktop access allowing commanders to manage the OS via tablet over local IP mesh networks.
* **Hardware Multiplexing:** Uses **PipeWire** and **Hamlib/rigctld** so multiple digital modems can share a single radio without crashing.
* **Offline Time Sync:** Uses **`gpsd`** and **`chrony`** with a standard USB GPS dongle to maintain atomic clock synchronization.
