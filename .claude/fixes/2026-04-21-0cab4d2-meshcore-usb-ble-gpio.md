# MeshCore: swap SPI-HAT repeater for USB/BLE NiceGUI app — `0cab4d2`

**Date:** 2026-04-21
**Commit:** TBD — `feat: MeshCore USB/BLE support via meshcore-gui`
**Files changed:** `site.yml`, `src/api/status.py`, `src/dashboard/index.html`, `tests/html-check.py`, `tests/smoke-test.py`, `STACK.md`, `CLAUDE.md`
**Related:** Laura's vibe handover (`Laura Handover.rtf`), supersedes `.claude/fixes/2026-04-17-7a89d34-js8call-config-and-meshcore-cors.md` for the MeshCore side, hardware test pre-alpha.29
**Status:** shipped, awaiting hardware verification

---

## Problem

`pyMC_Repeater` (the previous MeshCore backend) is SPI-only — it assumes a
MeshCore LoRa HAT sitting on the Pi's GPIO header. Users with the much more
common USB-serial MeshCore radios (Heltec V3/V4, LilyGo T-Beam, generic
ESP32 + SX126x boards) or BLE-only radios had no way to connect through the
hub. The `/meshcore/` dashboard tile was effectively dead unless the user
owned the niche HAT.

Severity: user-journey blocker for the mesh card on any non-HAT hardware,
which is the majority of MeshCore deployments in the wild.

## Reproduction

Before the fix, on any Pi with a MeshCore USB radio (e.g. Heltec V4) plugged
in:

1. Flash pre-alpha.29 image.
2. Boot Pi, wait for services.
3. Open dashboard, click MeshCore tile → `/meshcore/`.
4. Page loads but the repeater cannot see the radio — there is no SPI HAT.
5. `systemctl status mcomz-meshcore` shows the service running against a
   device that does not exist on this hardware.

## Hypothesis (root cause)

The backend selection was wrong, not the front-end wiring. `pyMC_Repeater`
is a good fit for a dedicated repeater node with a HAT, but the hub's
primary use case is "plug a USB MeshCore radio into the hub and use it from
a browser." That needs a different backend that speaks USB serial and BLE
to the radio, and exposes a browser UI.

## Alternatives considered

- **Keep pyMC_Repeater, add USB-serial support upstream.** Rejected:
  upstream is SPI-focused; forking to add USB would be a significant
  maintenance burden and would still miss BLE.
- **Write a minimal custom MeshCore bridge in `src/api/status.py`.**
  Rejected: reinventing a protocol client we'd then have to chase as
  MeshCore evolves.
- **Ship no MeshCore support until upstream has a canonical web UI.**
  Rejected: we already advertise the card; degrading it now hurts more
  than shipping a working alternative.
- **`pe1hvh/meshcore-gui` (chosen):** NiceGUI (FastAPI + Socket.IO) web app
  that already supports both USB serial and BLE, actively maintained, and
  written against the same `meshcoredecoder` library the ecosystem
  converges on.

## Fix

1. **site.yml** — add `mcomz` user to `dialout` and `bluetooth` groups;
   install BlueZ and enable `bluetooth.service`; drop a D-Bus policy at
   `/etc/dbus-1/system.d/meshcore-ble.conf` so a non-root user can do BLE
   scanning/pairing; drop `/etc/udev/rules.d/99-mcomz-serial.rules` with
   the common MeshCore USB VID/PIDs (CP210x `10c4:ea60`, CH340/341
   `1a86:7523`/`1a86:55d4`, FTDI `0403:*`, Espressif CDC `303a:*`,
   Prolific `067b:*`).
2. Clone `pe1hvh/meshcore-gui` to `/opt/meshcore-gui`; create a venv at
   `/opt/mcomz/meshcore-gui-venv`; pip-install `nicegui`,
   `meshcoredecoder`, `bleak`, `dbus-fast` + upstream requirements.
   Wrap in Ansible `block`/`rescue` so a qemu pip failure doesn't break
   the whole build.
3. Ship a wrapper `/opt/mcomz/meshcore-gui-start.sh` that scans USB first
   and falls back to a BLE address stored at
   `/etc/mcomz/meshcore-ble-address`.
4. Add a systemd unit `mcomz-meshcore-gui.service` bound to port 8002,
   enabled via symlink into `multi-user.target.wants/` (the project rule —
   do not use `systemd: enabled: yes` under fake-systemctl).
5. Patch nginx HTTP and HTTPS server blocks: `/meshcore/` now proxies to
   `127.0.0.1:8002`; add `/_nicegui/` and `/socket.io/` proxy blocks with
   `Upgrade`/`Connection` headers so NiceGUI's websocket works on a
   sub-path.
6. **status.py** — add `mcomz-meshcore-gui` with label "MeshCore" and path
   `/meshcore/`; demote `mcomz-meshcore` (the SPI HAT repeater) to a
   non-proxied entry labelled "MeshCore (SPI HAT)".
7. **index.html** — `guardMeshService` now guards against
   `mcomz-meshcore-gui` instead of `mcomz-meshcore`, so the inline
   "service offline" message matches what the user actually needs running.
8. **tests/html-check.py** — update the guard-call assertion.
9. **tests/smoke-test.py** — add `mcomz-meshcore-gui` to
   `EXPECTED_SERVICES`; add 502 checks for `/_nicegui/` and `/socket.io/`
   so a missing NiceGUI proxy block is caught in CI-adjacent smoke tests.
10. **STACK.md** and **CLAUDE.md** — split the MeshCore entry into
    GUI (USB/BLE) and SPI repeater rows so future contributors understand
    why both services exist.

## Expected outcome

- On success: plug a Heltec V4 (or equivalent USB MeshCore radio) into the
  Pi, boot, open `/meshcore/` in a browser, see the NiceGUI device-picker,
  select the USB port, see radio status + message log. Toggling BLE path:
  write a MAC into `/etc/mcomz/meshcore-ble-address`, restart the service,
  it connects without USB.
- If `/meshcore/` returns 502 but `/library/` works: the service didn't
  start — check `journalctl -u mcomz-meshcore-gui` for pip/venv issues in
  the qemu build (rescue block may have swallowed a real error).
- If the page loads but websocket never connects: `/_nicegui/` or
  `/socket.io/` proxy block is missing or missing `Upgrade` headers.
- If USB radio isn't detected: udev rules not loaded — `ls -l /dev/ttyUSB*`
  and `getent group dialout` on the live Pi.

## Confidence

**Medium.** The plumbing (services, nginx, groups, udev, D-Bus) is
mechanical and follows a well-trodden path. The uncertainty is in the
qemu/chroot pip install for `dbus-fast` and `bleak` (both have C
extensions), and in whether `meshcore-gui` upstream will start cleanly
under systemd without a TTY. Both need real hardware to confirm.

On pre-alpha.29 the service was observed restart-looping on a Pi with a
Heltec V4 attached — we don't yet know whether the cause is (a) the radio
not enumerating at all on this board, (b) a meshcore-gui bug when the
configured device is absent, or (c) a missing env var. Diagnosis deferred
to the next hardware test cycle.

## Risks / failure modes

- **Pip install fails silently in chroot.** `block`/`rescue` will print a
  warning and carry on, leaving the service present but broken. Mitigated
  by the smoke-test check that `mcomz-meshcore-gui` is in
  `EXPECTED_SERVICES`.
- **udev rules too permissive.** Adding wide FTDI/Prolific/Espressif VIDs
  means any random USB-serial device lands in `dialout`. Acceptable on a
  single-purpose appliance; worth revisiting if we ever multi-tenant.
- **BlueZ D-Bus policy.** We grant `org.bluez` access to the `bluetooth`
  group. Low risk on this appliance but a hardening target later.
- **Breaks existing SPI HAT users.** The repeater service still ships and
  still runs; it's just not proxied. A HAT user can still reach it on
  localhost:8000 and we could proxy it on a different path later.
- **NiceGUI sub-path bugs.** NiceGUI is known to be quirky under a
  reverse-proxy sub-path; upstream fixes land often. Pin an upstream
  version later if drift becomes a problem.

## Test plan

**Automated (run before commit):**
- `python3 tests/html-check.py` — passes, including the new
  `guardMeshService('mcomz-meshcore-gui'` assertion.
- `tests/smoke-test.py` requires a live device; skip until next flash.

**Hardware (next pre-alpha flash):**
1. Plug Heltec V4 into Pi USB before boot.
2. Boot, wait 60 s, then `systemctl status mcomz-meshcore-gui` on the
   live Pi — expect `active (running)`.
3. `ls -l /dev/ttyUSB0` — expect `crw-rw----` owned by `root:dialout`.
4. Open `http://mcomz.local/meshcore/` on a LAN laptop — expect NiceGUI
   device picker, not 502.
5. Select USB device, verify radio status shows up and messages can be
   sent and received against a known peer MeshCore node.
6. Stop service (`systemctl stop mcomz-meshcore-gui`) and reload dashboard
   — expect inline offline guard message, not 502 page.
7. BLE path: write peer MAC to `/etc/mcomz/meshcore-ble-address`, unplug
   USB, restart service — expect connection via BLE.
8. Regression: Meshtastic tile (`/meshtastic/`) still works; Kiwix,
   Mumble, VNC unaffected.

## Rollback

`git revert <sha>` restores the SPI-HAT-only configuration. The
`/opt/meshcore-gui` checkout and venv will remain on any already-flashed
images — harmless but can be removed with
`rm -rf /opt/meshcore-gui /opt/mcomz/meshcore-gui-venv` if desired.

## Outcome

*(Filled in after hardware verification.)*

- Verified on: TBD
- Result: TBD
- What actually happened:
- Follow-up:
