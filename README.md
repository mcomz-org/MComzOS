# MComzOS: Master Specification (v0.0.1)

## The Philosophy
MComzOS is a highly curated, hyper-resilient Emergency Communications (EmComm) appliance. It is designed with a "Zero-Skill" user experience in mind, turning complex digital radio and mesh software into an invisible backend managed by a simple Web Dashboard.

MComzOS is strictly open-source. It relies on no proprietary licenses, no internet-dependent authentication, and no closed ecosystems. If the global internet falls, MComzOS survives, syncs, and operates autonomously over local mesh and global radio frequencies.

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
