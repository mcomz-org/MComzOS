# MComzOS

## Project Overview
Off-grid emergency communications hub. Ansible playbook (`site.yml`) builds a master image targeting Raspberry Pi (ARM64) and x86_64 PCs running Debian Bookworm.

## Key Files
- `site.yml` — Main Ansible playbook (all provisioning)
- `src/dashboard/index.html` — Hub web dashboard (live service status, links to all services)
- `src/api/status.py` — stdlib-only Python status API (systemctl health polling)
- `README.md` — Public-facing project spec

## Architecture
- Target OS: Debian 12 (Bookworm) — Raspberry Pi OS or standard Debian
- Primary arch: ARM64 (aarch64), secondary: x86_64 (amd64)
- `deb_arch` Ansible variable handles arch-specific download URLs
- Images built by GitHub Actions on version tag push → released as `mcomzos-rpi.img.xz` / `mcomzos-x86_64.img.xz`

## Current Task Roadmap
See [.claude/tasks/2026-04-05-buildable-playbook.md](.claude/tasks/2026-04-05-buildable-playbook.md) for full status of outstanding work.

**Next priorities (P2):**
1. OverlayFS on non-Pi hardware — `raspi-config` only works on RPi; x86 needs `overlayroot` package
2. FreeDATA ARM64 AppImage — may 404; needs verification or build-from-source fallback
3. Mumble HTTPS — browsers require HTTPS for microphone (`getUserMedia`); needs self-signed TLS in nginx
