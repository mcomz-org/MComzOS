# MComzOS

## Project Overview
Off-grid emergency communications hub. Ansible playbook (`site.yml`) builds a master image targeting Raspberry Pi (ARM64) and x86_64 PCs running Debian Bookworm.

## Key Files
- `site.yml` — Main Ansible playbook (all provisioning)
- `src/dashboard/index.html` — Hub web dashboard (currently static HTML)
- `README.md` — Public-facing project spec

## Architecture
- Target OS: Debian 12 (Bookworm) — Raspberry Pi OS or standard Debian
- Primary arch: ARM64 (aarch64), secondary: x86_64 (amd64)
- `deb_arch` Ansible variable handles arch-specific download URLs

## Current Task Roadmap
See [.claude/tasks/2026-04-05-buildable-playbook.md](.claude/tasks/2026-04-05-buildable-playbook.md) for full status of outstanding work.

**Next priorities:**
1. WiFi AP + captive portal (hostapd, dnsmasq, avahi) — P0, hub is useless without it
2. Kiwix systemd service + ZIM content — P1
3. Missing systemd units (Direwolf, ardopcf, Pat, Kiwix) — P1
4. Dashboard backend (replace static mockup with live data) — P1
