# OTA Updates — A/B Partition Design (RAUC)
_Researched 2026-04-21_

## Summary verdict

MComzOS should adopt **A/B rootfs partitioning** with **RAUC** (Robust Auto-Update Controller) as the update engine. This gives atomic, signed, rollback-capable updates that cover the 100% case Martin asked for — including kernel, bootloader, and system services — without cutting data storage in half. Typical storage overhead on a 64 GB SD is ~12–15% (two 6 GB rootfs slots; everything else stays shared). Does require a one-time reflash for existing installs, and meaningful pre-alpha image-build + CI work.

---

## Goals / non-goals

**Goals:**
1. Updates that cover the full OS — kernel, systemd services, apt-installed packages, dashboard, API, site.yml-derived config.
2. Atomic: an update either fully succeeds or leaves the previous working OS bootable.
3. Automatic rollback if the new slot fails to boot (firmware-level for Pi 5, GRUB-level for x86_64).
4. Works offline for the install phase — the hub itself may be the only WAN gateway a user has, so the update UX can't assume internet at apply time. (Download requires internet; once downloaded, apply is offline.)
5. Signed bundles — users can't be tricked into installing a malicious bundle posing as a release.
6. Dashboard surfaces update availability, triggers apply, and shows progress + rollback status.

**Non-goals (v1):**
- Delta updates (full bundle download each time — ~200–400 MB, acceptable for a pre-alpha).
- In-place patching of the running OS (we're going A/B-only; no "soft" shortcut path).
- Factory reset from the dashboard (future; RAUC supports it but out of scope here).
- Multi-user update auth (admin login is already on the post-alpha todo).

---

## Status quo (what exists today)

**RPi ARM64 image** (from `.github/workflows/build-image.yml`):
- Starts from Raspberry Pi OS Lite ARM64.
- Layout: `p1` = FAT32 `/boot/firmware` (512 MB), `p2` = ext4 root (fills card).
- CI truncates +5 GB, resizes `p2` to 100%, provisions via Ansible chroot.

**x86_64 image:**
- GPT, `p1` = 512 MB ESP, `p2` = ext4 root (fills 10 GB image).
- Debootstrap + Ansible chroot; GRUB EFI installed via `grub-install`.

**Update mechanism:** none. Users reflash on every release. No OTA, no rollback, no signing. Pre-alpha releases are manually tagged and built by CI.

---

## Proposed architecture

### Partition layout

**Both architectures get the same conceptual layout:**

| Slot | Purpose | Size | Notes |
|---|---|---|---|
| `boot` / `ESP` | Firmware, kernel, initrd, bootloader config | 512 MB | FAT32 on both; on Pi this is `/boot/firmware` |
| `rootfs.0` (A) | OS slot 0 | 6 GB | ext4, read-only at runtime (see below) |
| `rootfs.1` (B) | OS slot 1 | 6 GB | ext4, identical layout to slot 0 |
| `data` | `/data` bind-mounted into `/var/lib/kiwix`, `/var/spool/pat`, `/etc/mcomzos-state`, etc. | remaining card | ext4, shared between slots, **never** touched by updates |

On a 64 GB card: 512 MB + 2×6 GB + ~57 GB data = 88% usable for data. On a 32 GB card: 512 MB + 2×6 GB + ~19 GB = 60% usable. 32 GB is the practical floor; we should mark it as such in docs and RPi Imager.

**Rootfs size decision — 6 GB:** current `site.yml` fully-installed rootfs measures roughly 4.1 GB on a recent build (from Ansible log spot-checks). 6 GB gives ~50% headroom for future packages (JS8Call data, Kiwix indexers, etc.) without having to repartition and reflash. If we hit 5+ GB usage in practice we bump to 8 GB and require a reflash before that release — painful but survivable pre-beta.

**Data partition content (strict allow-list):**
- `/var/lib/kiwix` — ZIMs (user-downloaded)
- `/var/spool/pat` — Winlink mailbox
- `/etc/mcomz-state/` — WiFi connections, hotspot SSID, meshcore-ble-address, admin credentials once we add them
- `/var/log/mcomz-persistent/` — selected logs we want to survive updates
- `/home/mcomz/` — user data if any accumulates there

Everything else (`/etc`, `/opt`, `/usr`, `/var` except the above) lives in the rootfs slot and is replaced wholesale by an update.

### Read-only rootfs + overlayfs (optional, recommended)

RAUC works with read-write rootfs, but the best-practice pattern is:
- Mount rootfs read-only at boot.
- Mount a tmpfs overlay on top for runtime writes to `/etc`, `/var`, etc.
- Persist only the allow-listed paths via bind mounts into `/data`.

This prevents runtime drift (the user's slot 0 won't accumulate state that slot 1 doesn't have) and catches "I wrote a file during an update but didn't put it in the playbook" bugs during development, not in production.

**Cost:** some services (dbus, systemd-journald) need their writable paths explicitly bind-mounted. Well-trodden territory — Raspberry Pi's own `initramfs-tools` overlay mode can be used, or we hand-roll a small systemd-tmpfiles + fstab setup.

**Recommendation:** ship v1 with RW rootfs to reduce scope. Add RO+overlay in a follow-up release once A/B mechanics are verified on hardware.

### Boot selection mechanism

**Raspberry Pi 4/5 — `tryboot` (firmware-level):**
- `/boot/firmware/autoboot.txt` contains:
  ```
  [all]
  tryboot_a_b=1
  boot_partition=2
  [tryboot]
  boot_partition=3
  ```
- RAUC sets a "try slot B" flag; firmware boots slot B *once*. If slot B sets `BOOT_SUCCESS` via a systemd service during boot, firmware makes it sticky. If it doesn't (crash, watchdog, bootloop), next power cycle falls back to slot A.
- Requires `rpi-eeprom` ≥ 2023-05-11 (Pi 4) or current Pi 5 firmware (standard on Bookworm). Pi 3 does **not** support tryboot → Pi 3 is out of scope for OTA (existing users reflash).

**x86_64 — GRUB + `grub-reboot`:**
- GRUB config has two menu entries: `rootfs-a`, `rootfs-b`.
- `grub-reboot rootfs-b` sets a one-shot next-boot override.
- GRUB has `save_env` + fallback logic: if the booted slot sets `grub-editenv - set boot_ok=1` within ~60 s of boot, it sticks. Otherwise next boot falls back.
- This is a solved pattern; RAUC ships a `u-boot`/`grub` backend that wires it up.

**Common mechanism — RAUC's `rauc-mark-good` service:**
- RAUC installs a systemd unit that, once post-boot health checks pass (dashboard reachable, status API responsive, nginx running), calls `rauc status mark-good` to confirm the slot. We define what "healthy" means via a small shell script.

### RAUC slots and bundles

**Slot config (`/etc/rauc/system.conf`):**

```ini
[system]
compatible=mcomzos-rpi         # or mcomzos-x86 — arch-specific, prevents cross-flashing
bootloader=rpi                 # or grub on x86
data-directory=/data/rauc      # RAUC state storage (tracks which slot is good)

[keyring]
path=/etc/rauc/keyring.pem     # public key baked into image; verifies bundle signatures

[slot.rootfs.0]
device=/dev/mmcblk0p2
type=ext4
bootname=a

[slot.rootfs.1]
device=/dev/mmcblk0p3
type=ext4
bootname=b

[slot.boot.0]
device=/dev/mmcblk0p1
type=vfat
bootname=a
parent=rootfs.0
```

(We'd also version `/boot` per-slot for kernel updates — Pi 5 tryboot supports dual boot partitions; adds ~500 MB. Worth it for firmware/kernel updates.)

**Bundle format (`.raucb`):**
- A squashfs archive containing the rootfs image + a manifest + a detached signature.
- Manifest declares `compatible` (arch), version, slot images, hooks (pre/post install scripts).
- Verified against the in-image keyring before any write happens — tampered bundles are rejected before touching the inactive slot.

**Signing:**
- Generate an offline-held signing key (`openssl genpkey -algorithm RSA -out mcomzos-ota.key`).
- Public cert (`mcomzos-ota.cert.pem`) is baked into every image at `/etc/rauc/keyring.pem`.
- CI holds the *private* key in a GitHub Actions secret; the bundle-build step signs each release.
- Key rotation is a pain (requires re-issuing an image bundle signed with the old key that installs the new public cert) — worth generating once and guarding carefully.

### Update flow end-to-end

1. **Device state**: booted from slot A, `rauc status` shows `good|active` for A and `good|inactive` for B.
2. **Dashboard polls** (configurable, default daily) the releases endpoint on GitHub: `GET /repos/mcomz-org/MComzOS/releases/latest`. Compares `tag_name` vs `/etc/mcomzos-version`.
3. **Update available** → dashboard shows a banner: "Update to v0.0.2-pre-alpha.30 available (12 MB download)" (or whatever). Martin has a single-click "Download & install" button.
4. **Download**: dashboard streams `.raucb` from the release into `/data/rauc/pending-bundle.raucb`. Progress surfaced in UI.
5. **Verify**: `rauc info pending-bundle.raucb` — checks signature + compatibility. If invalid, UI shows "Update rejected: invalid signature" and aborts.
6. **Install**: `rauc install pending-bundle.raucb` — writes rootfs image to the inactive slot (B). Status streamed via D-Bus; dashboard shows progress bar.
7. **Reboot prompt**: "Install complete. Reboot now to switch to v0.0.2-pre-alpha.30?" → `rauc status mark-active other` → `systemctl reboot`. Firmware boots slot B via tryboot.
8. **Post-boot health check**: `mcomz-mark-good.service` runs after `multi-user.target`, waits ~60 s, checks that nginx, status API, and meshcore-gui all respond. On success → `rauc status mark-good`. On failure → service exits non-zero, watchdog reboots, firmware falls back to slot A.
9. **Rollback visibility**: if the device came back on slot A after trying B, dashboard shows "Update to vN failed health check — rolled back to vN-1. Details at /var/log/mcomz-update.log."

### What triggers a rollback

| Trigger | Level | Detection window |
|---|---|---|
| Bootloader can't load kernel | firmware / GRUB | immediate (next boot) |
| Kernel panics, no userspace | kernel watchdog + firmware retry limit (tryboot) | 1 boot cycle |
| systemd fails to reach `multi-user.target` in 5 min | `systemd`, kernel watchdog | ~5 min |
| Dashboard/API don't respond after 60 s post-boot | `mcomz-mark-good.service` (our custom check) | ~2 min post-boot |
| User manually forces rollback from dashboard | `rauc status mark-active other` + reboot | immediate |

The custom health check is where we define "working" — adding a failing nginx or failing meshcore-gui to it means a future bad release gets rolled back automatically.

### Data persistence during updates

`/data` is **never** written by RAUC. A release that changes the schema of something stored in `/data` (e.g. a new WiFi config format) needs:
- A migration script, packaged in the rootfs, that runs once post-boot, detects old-format data, upgrades in place.
- Idempotency (safe to run twice if the migration succeeds but the boot later fails).
- The migration logs to `/data/rauc/migrations.log` so the next boot knows it's already run.

This is a real ongoing discipline — every PR that touches stored state needs a migration entry. Worth calling out in `CLAUDE.md` alongside the coverage rule.

---

## Implementation plan

### Phase 1 — Image layout + RAUC install (biggest chunk of work)

**site.yml** changes:
- Install `rauc` + `rauc-service` apt packages (ARM64 and amd64 both in bookworm-backports; check availability).
- Deploy `/etc/rauc/system.conf` per arch (Jinja template — `bootloader` and `device` paths differ).
- Deploy `/etc/rauc/keyring.pem` from `src/ota/keyring.pem` in the repo (this is the *public* cert — safe to commit).
- Deploy `mcomz-mark-good.service` (systemd unit + shell script that checks dashboard health and calls `rauc status mark-good`).
- Create `/data` mount point and bind-mount dirs (fstab entries, systemd `.mount` units).

**CI changes to `build-image.yml`:**
- **RPi**: change partition table to: boot (512 MB) + rootfs.0 (6 GB) + rootfs.1 (6 GB) + data (remainder, created but mostly empty). Replace the current `truncate -s +5G` + `parted resizepart 2 100%` with a custom `parted` script that creates all four partitions to exact sizes. Only provision into slot 0; leave slot 1 as a placeholder (zero-filled or copy-of-slot-0 so first boot has a fallback).
- **x86**: similar — currently GPT with ESP + single root. Change to ESP + rootfs.0 + rootfs.1 + data.
- Adjust `fstab` generation to mount `/dev/disk/by-label/mcomzos-a` as the rootfs, and the data partition as `/data`.
- Add tryboot/autoboot.txt configuration for RPi; add GRUB menu entries for x86 with `grub-reboot` support.

**One-time signing-key setup (manual, before first OTA release):**
- Generate `mcomzos-ota.key` (private, 4096-bit RSA, kept offline or in a GH secret named `OTA_SIGNING_KEY`).
- Generate `mcomzos-ota.cert.pem` (self-signed cert, 10-year validity) — committed to repo as `src/ota/keyring.pem`.

### Phase 2 — CI bundle build step

New job `build-bundle-rpi` + `build-bundle-x86`:
- Takes the rootfs image produced by the main build.
- Extracts rootfs partition via `debugfs` or by mounting and tarring.
- Wraps it in a RAUC bundle with `rauc bundle --cert=... --key=... manifest.raucm`.
- Manifest includes `compatible=mcomzos-rpi`, version from tag, image sha256.
- Signs with private key from secret.
- Uploads `mcomzos-rpi-${TAG}.raucb` to the release.
- Updates `os-list.json` on gh-pages with a new `latest_bundle_url` field the dashboard can poll.

### Phase 3 — Dashboard UX + status API

**`src/api/status.py`:**
- New `GET /api/update/status` returning: current version, slot info (`rauc status` parsed), available-update info (cached poll of GitHub releases).
- New `POST /api/update/check` forcing a refresh poll.
- New `POST /api/update/download` streaming the bundle to `/data/rauc/pending.raucb`.
- New `POST /api/update/install` calling `rauc install /data/rauc/pending.raucb`, streaming progress via Server-Sent Events.
- New `POST /api/update/rollback` — manually reverts to the other slot.

**`src/dashboard/index.html`:**
- New "System" card (or extend the existing header) with: current version, available update banner, install button, rollback button (shown only if the current slot is "tried but not confirmed good" or if user digs into settings).
- Progress UI during download + install.
- Success/failure banner after reboot.

### Phase 4 — Migration from current fleet

Existing installs can't be A/B'd via OTA (there's no second slot to write to yet). Options:
1. **Reflash required once**: release notes say "This release changes partition layout. Reflash using RPi Imager — your data will be lost." Acceptable pre-alpha, obviously bad post-beta.
2. **Data-preserving reflash script**: user downloads a script to their laptop that reads `/data`-equivalent paths off the old SD card image, writes new image, restores data. More work but far less painful for users with ZIMs already downloaded.

**Recommendation**: pre-alpha, option 1. Document it loudly. Offer option 2 as a "migrate your v0.0.2 hub to v0.0.3" tool if and when we cross the threshold of users-with-data worth preserving.

---

## Risks / open questions

1. **`rauc` package availability on bookworm**: bookworm ships `rauc` 1.9 (released 2024). That's current enough. `rauc-service` systemd unit may need hand-building — worth verifying in the first Ansible dry-run.
2. **Pi 4 firmware support for tryboot**: tryboot landed in `rpi-eeprom` in mid-2023. All Pi 4/5 devices that have been online and taken updates since then have it. Pi 4 devices that have been sitting in a drawer with 2022 firmware need an eeprom update before tryboot works — we should detect and warn in the first-boot firstrun script.
3. **Bundle download size**: a full rootfs is ~4–6 GB uncompressed. Squashfs with zstd gets that down to ~500–800 MB. Full-bundle download every release is heavy for users on cellular/sat. Delta updates (RAUC's "casync" mode) cut this to ~10–50 MB per release. Worth implementing in a v2 if bandwidth becomes a real constraint.
4. **First-run behaviour**: on first boot of a freshly flashed image, slot A is "good", slot B is identical but marked inactive. RAUC needs to know this initial state. A small oneshot `rauc-first-boot.service` handles it.
5. **Key compromise**: if the signing key is leaked, every existing device accepts malicious bundles. Mitigation: public cert has a 10-year validity; we can issue a revocation bundle that updates the in-image keyring if compromise is detected. Needs thought but not a v1 blocker.
6. **Storage headroom**: a 32 GB card with 2×6 GB slots + 512 MB boot + overhead leaves ~19 GB for data. Wikipedia Mini is 155 MB, WikiMed Mini is 300 MB, but the full English Wikipedia ZIM is ~100 GB. 32 GB is the practical minimum; 64 GB+ recommended. Document prominently.
7. **Dashboard update during install**: the user is interacting with the dashboard that's being replaced. Need graceful handling: after `rauc install` succeeds, show a full-page "Reboot now" banner that blocks interaction, so the user isn't mid-click when nginx restarts.
8. **Install-in-progress interruption**: power loss during `rauc install` — should be fine (writes to inactive slot, active slot untouched). Power loss during *reboot into new slot* — firmware falls back on retry limit. Covered.
9. **What about `/boot`?** — kernel updates mean `/boot/firmware` needs to be versioned too. Pi 5 supports dual `boot` partitions for tryboot. x86 GRUB can load different kernels from the ESP per slot. Both solvable; adds ~500 MB to boot-partition size.

---

## Decision log

| Decision | Reason |
|---|---|
| RAUC over Mender | BSD license, no SaaS dep, actively maintained, works offline, integrates cleanly with systemd + tryboot/GRUB |
| Separate `/data` partition | preserves Kiwix ZIMs + Pat mailbox across updates; avoids bloating bundle size |
| 6 GB rootfs slots | fits current 4.1 GB rootfs + 50% headroom; works on 32 GB cards |
| No delta updates in v1 | full bundles are ~500–800 MB compressed — acceptable for pre-alpha; delta is a v2 optimization |
| Read-write rootfs in v1 | read-only + overlay is the right target but adds scope; can switch in v2 without breaking the OTA pipeline |
| One-time reflash for migration | no way to A/B an existing non-A/B install in place; user pain is bounded and acceptable pre-alpha |
| 10-year cert validity | long enough we don't churn; short enough we force a rotation cadence |
| Dashboard-driven update UI | matches the rest of the hub's management model; no separate admin CLI to learn |
| Tryboot (RPi) + grub-reboot (x86) | both are firmware/bootloader-native — no third-party bootloader to maintain |
| Pi 3 not supported | tryboot unavailable; users reflash or stay on current release |

---

## Rough effort estimate

- Phase 1 (image layout + RAUC install in playbook): ~2–3 days focused work, mostly in `site.yml` and the CI workflow, plus a lot of build-and-flash iterations to validate the partition table and boot selection on real hardware.
- Phase 2 (CI bundle step, signing): ~1 day.
- Phase 3 (dashboard UX + status API): ~1–2 days, roughly half of that in the JS.
- Phase 4 (migration docs + one-time-reflash tooling): ~0.5 day.
- **Total:** ~5–7 days of dedicated work, plus real-hardware test cycles between phases.

This is a meaningful chunk of work but the payoff is that every subsequent MComzOS change ships as an OTA bundle — no more "flash to test a typo fix" overhead, and the field-robustness story is in place before the first alpha users arrive.
