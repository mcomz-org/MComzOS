# MComzOS Session Handover

*Written at end of session ending 2026-04-11. Start a new Claude Code session and read this file first.*

---

## What was just shipped — v0.0.2-pre-alpha.17

Tag pushed, build running at github.com/mcomz-org/MComzOS/actions.

### Fixes in this release
| Area | What changed |
|------|-------------|
| iOS Safari | nginx now serves dashboard on HTTP port 80 (no redirect); iOS Safari can open MComz without any certificate interaction |
| Version display | `/etc/mcomzos-version` written at build time; `/api/version` endpoint; "System Status" heading shows `(v0.0.2-pre-alpha.17)` with link to releases |
| VNC reliability | Replaced `vncserver -fg` Perl wrapper with `/usr/local/bin/mcomz-vnc-start` — runs `Xvnc` directly, cleans stale X locks on startup |
| Hotspot stop | `ap_stop()` now polls `nmcli` for up to 30 s and returns `reconnected: true/false`; dashboard shows feedback rather than silently completing |
| Kiwix search | `--withFullTextIndex` added to `zimwriterfs` in MComzLibrary — fixes empty dropdowns and broken search |
| Arabian Nights | PG #1264 (H.G. Wells) → PG #128 (Andrew Lang) in `download-sources.sh` |
| WikiMed build log | `failed_when: false` download now registers result and emits a `debug:` warning if it fails |
| Licensed Radio card | Pat, JS8Call, FreeDATA collapsed into one "📻 Licensed Radio" card with same expand/collapse pattern as Mesh |
| Kiosk mode | Physical monitor support: auto-login on tty1, `startx` → Chromium `--kiosk http://localhost` |
| Manage Books | Slide-in panel on Library card: list installed ZIMs, download by URL (background thread + 3 s poll), remove books |
| hostapd/dnsmasq | "off" badge now shows "(standby — activates with hotspot)" inline note |

### MComzLibrary changes (also pushed)
- Arabian Nights PG #128
- `--withFullTextIndex` on zimwriterfs

---

## What still needs hardware verification

The pre-alpha.16 hardware test found these; they have code fixes but haven't been tested on device yet:

| # | Issue | Fix shipped |
|---|-------|------------|
| 1 | VNC password dialog never appears | Xvnc wrapper (pre-alpha.17) |
| 2 | JS8Call modal never opens | Same — depends on VNC fix |
| 3 | Hotspot stop — couldn't reconnect | ap_stop() polling (pre-alpha.17) |
| 4 | WikiMed Mini absent from Kiwix | Download may still time out in chroot — watch build log |

---

## Outstanding work (not in pre-alpha.17)

### Functional gaps
- **Pat/Winlink** — user hasn't fully tested it yet; needs a send/receive test
- **Direwolf APRS** — no map UI; service runs but no way to see decoded packets in browser
- **FreeDATA ARM64** — no upstream AppImage; skipped silently. Fix belongs in upstream repo (DJ2LS/FreeDATA)
- **Mumble microphone on iOS** — Apple restricts WebRTC to Safari only; Chrome on iOS will never work

### Dashboard (post-alpha)
- Inline how-to guides for JS8Call and Pat (Mumble already has one)
- Radio Communications tab with amateur licence gate (partially done — single card exists but no licence gate)
- Admin login protecting reboot/shutdown/WiFi/books
- Kiwix onboarding screen when library is empty

### Code quality
- **Phase B** in todo.md: audit and remove remaining `ignore_errors` from site.yml
- **Auto-version workflow**: `anothrNick/github-tag-action` can't parse `v0.0.2-pre-alpha.X` as SemVer; all builds require manual `git tag` + push

### Infrastructure
- OverlayFS on x86 may need verification (was implemented but not hardware-tested)
- WireGuard VPN for remote access (post-v0.0.2 roadmap item)

---

## Key files

| File | Purpose |
|------|---------|
| `site.yml` | Entire Ansible provisioning playbook |
| `src/dashboard/index.html` | Single-page dashboard UI |
| `src/api/status.py` | stdlib Python API on localhost:9000 |
| `.github/workflows/build-image.yml` | CI: builds RPi + x86 images on version tag push |
| `.claude/tasks/todo.md` | Full outstanding work list with history |
| `.claude/feedback/hardware-test-results.md` | Verbatim hardware test feedback per release |
| `TEST-PROCEDURES.md` | Checklist for hardware validation |
| `STACK.md` | Service/port reference |

---

## How to trigger a build

Builds require a manual tag — the auto-version workflow can't parse pre-alpha SemVer:

```bash
git tag v0.0.2-pre-alpha.18
git push origin v0.0.2-pre-alpha.18
```

All GitHub releases use `prerelease: true` — do not mark as latest until past alpha.

---

## Current test hardware

Raspberry Pi 5. Tests conducted by Martin (the user) flashing and running the device.

---

## Vibe session notes

Martin uses a vibe session (separate agentic coding tool) for implementation work alongside Claude Code. When writing vibe prompts:
- Give vibe the **problem to solve**, not pre-written code — let it do the thinking
- Vibe has its own context from previous runs; reference files by path, not by pasting content
- Martin keeps vibe sessions open across multiple Claude prompts to preserve context
