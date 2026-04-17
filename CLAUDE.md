# MComzOS — Claude / Vibe Briefing

## What This Project Is

MComzOS is an off-grid emergency communications hub. An Ansible playbook (`site.yml`) builds a bootable image targeting Raspberry Pi 4/5 (ARM64) and 64-bit PCs (x86_64) running Debian 12 Bookworm. Images are built by GitHub Actions on version tag push and released as `.img.xz` files.

Current status: **pre-alpha**. Hardware-tested on RPi 5. All releases use `prerelease: true`.

---

## Key Files

| File | Purpose |
|------|---------|
| `site.yml` | Entire Ansible provisioning playbook (~1400 lines) |
| `src/dashboard/index.html` | Single-page dashboard UI (vanilla JS, dark theme) |
| `src/api/status.py` | stdlib-only Python API on `localhost:9000` — systemctl polling, WiFi management, kiwix book management |
| `.github/workflows/build-image.yml` | CI: builds RPi + x86 images on version tag push |
| `README.md` | Public-facing project description |
| `STACK.md` | Reference: every service, its port, and its role |
| `tests/MANUAL-TESTS.md` | Hands-on hardware test checklist — work through this after every flash |
| `tests/smoke-test.py` | Automated network checks — run from a laptop on the same LAN |
| `tests/html-check.py` | Static analysis of `index.html` — also runs in CI before each build |
| `scripts/generate-release-notes.sh` | Called by CI to generate release notes from conventional commits |
| `.claude/tasks/todo.md` | Full history of decisions, completed work, and outstanding items |
| `.claude/feedback/hardware-test-results.md` | Verbatim hardware test feedback per release |
| `.claude/fixes/` | Fix-attempt log — one file per non-trivial fix, tracking hypothesis, confidence, test plan, and outcome |

---

## Architecture

- **Target OS**: Debian 12 Bookworm — Raspberry Pi OS Lite (ARM64) or standard Debian (amd64)
- **Provisioning**: Ansible runs in a chroot during CI build — no live system needed
- **`deb_arch`**: Ansible variable set to `arm64` or `amd64` by CI; handles arch-specific URLs
- **`build_mode: true`**: Skips tasks that need live hardware (raspi-config, overlayfs on RPi)
- **`mcomzos_version`**: Passed from CI as `github.ref_name`; written to `/etc/mcomzos-version`
- **Fake systemctl**: CI stubs out `systemctl` in chroot; all service enables use `file: state=link` directly into `multi-user.target.wants/` — do not use `systemd: enabled: yes`
- **nginx**: Serves dashboard on HTTP (port 80) and HTTPS (port 443). HTTP is intentional — iOS Safari rejects self-signed certs, so redirecting to HTTPS makes the hub unreachable on iOS.

### Service Port Map

| Service | Port / Path | Notes |
|---------|-------------|-------|
| nginx dashboard | :80 and :443 | HTTP intentional for iOS Safari |
| Status API | localhost:9000 → `/api/` | Python stdlib, runs as root |
| Kiwix offline library | localhost:8888 → `/library/` | `--urlRootLocation /library` |
| Mumble voice server | :64738 | Native client port |
| Mumble websockify | localhost:64737 → `/mumble/ws` | WebSocket bridge for mumble-web |
| mumble-web static | `/mumble/` | Served by nginx alias |
| Meshtastic web UI | localhost:8080 → `/meshtastic/` | Built into meshtasticd |
| MeshCore dashboard | localhost:8000 → `/meshcore/` | pyMC_Repeater |
| noVNC static | `/vnc/` | nginx alias to /usr/share/novnc/ |
| noVNC websockify | localhost:6080 → `/vnc/websockify` | Bridges browser to VNC |
| TigerVNC (Xvnc) | localhost:5901 | Headless; JS8Call runs inside |
| Pat Winlink | localhost:18081 → :8081 (HTTPS) | Separate nginx server block |

---

## What Is Currently Working (as of v0.0.2-pre-alpha.17)

- **Dashboard**: version display, system status grid with standby notes, reboot/shutdown buttons
- **WiFi panel**: scan, connect, forget, AP toggle with reconnect polling
- **Hotspot / AP fallback**: manual toggle works; 5-minute auto-fallback if no LAN
- **Offline Library (Kiwix)**: ZIMs load with search and full-text index; Manage Books panel for downloading/removing ZIMs post-install
- **Voice & Text (Mumble)**: browser voice + text via mumble-web; collapsible how-to guide
- **Licensed Radio card**: Pat, JS8Call, FreeDATA collapsed into single expandable card
- **Mesh card**: Meshtastic + MeshCore with inline offline guard (no 502 page)
- **Kiosk mode**: physical monitor auto-boots to full-screen Chromium dashboard
- **iOS Safari**: dashboard accessible over HTTP without certificate issues

## What Needs Hardware Verification (fixes shipped, not yet confirmed)

- **VNC / noVNC**: switched from `vncserver -fg` to direct `Xvnc` wrapper — auth dialog should now appear; unconfirmed
- **JS8Call inside VNC**: depends on VNC fix above
- **Hotspot stop recovery**: polling logic shipped; user previously couldn't reconnect after stopping AP

## Known Limitations (not bugs)

- PDF books can't render inline on iOS Chrome — platform limitation
- Mumble microphone requires HTTPS (`getUserMedia`) — use HTTPS or accept cert once
- Mumble microphone on iOS Chrome — Apple restricts WebRTC to Safari only on iOS
- FreeDATA ARM64 — no upstream AppImage; playbook skips it gracefully
- WikiMed Mini may fail to download in chroot build (155 MB, timeout risk) — warning printed in build log if so

---

## Outstanding Work

See `.claude/tasks/todo.md` for full detail. Current priorities:

### Needs doing before alpha
- **Pat/Winlink** — user hasn't fully tested send/receive; needs a real-radio test
- **VNC + JS8Call** — needs hardware confirmation after Xvnc fix
- **auto-version.yml deleted** — builds now require manual tagging (see Build Process below)

### Post-alpha
- Inline how-to guides for JS8Call and Pat (Mumble already has one)
- Amateur licence gate on Licensed Radio card
- Admin login protecting reboot/shutdown/WiFi/books
- Kiwix onboarding screen when library is empty
- WireGuard VPN for remote access
- APRS map viewer (Direwolf decodes but no UI)

---

## Build Process

**Auto-version is disabled** — `anothrNick/github-tag-action` can't parse `v0.0.2-pre-alpha.N` as SemVer. All builds require a manual tag:

```bash
git tag v0.0.2-pre-alpha.N
git push origin v0.0.2-pre-alpha.N
```

Check the latest tag first: `git tag --sort=-version:refname | head -3`

RPi ARM64 builds take ~90 minutes. x86_64 takes ~15 minutes.

Check build results: `gh run list --limit 5` then `gh run view <ID> --log`

**Never mark a release as latest** — all releases use `prerelease: true` until past alpha.

---

## Testing

After every flash and boot, run through `tests/MANUAL-TESTS.md` in order.

For a quick automated sanity check from a laptop on the same network:
```bash
python3 tests/smoke-test.py          # against mcomz.local
python3 tests/smoke-test.py 192.168.4.1  # when connected via hotspot
```

Before making dashboard changes, run the static checker locally:
```bash
python3 tests/html-check.py
```

### Coverage rule — mandatory

Every change that introduces or modifies user-facing behaviour **must** have a corresponding test added in the same commit. There are no exceptions:

| What changed | Where to add the test |
|---|---|
| New or changed nginx route / API endpoint | `tests/smoke-test.py` |
| New JS function or dashboard element | `tests/html-check.py` |
| Anything requiring eyes, ears, or physical interaction | `tests/MANUAL-TESTS.md` |

If a behaviour genuinely cannot be tested automatically (e.g. voice audio, hotspot start/stop, kiosk display, destructive ops), add it to `MANUAL-TESTS.md` instead — but do not skip it entirely. If a test is being omitted, say so explicitly and state why.

Running `html-check.py` and `smoke-test.py` after a change and seeing them pass is not sufficient — the tests must actually cover the new behaviour, not just pass because they don't know about it yet.

---

## Critical Rules

1. **All releases: `prerelease: true`** in both `softprops/action-gh-release` steps in `build-image.yml`
2. **Never push a tag without explicit user approval**
3. **Tag format**: always `v0.0.2-pre-alpha.N` — do not start a new version
4. **Commit to `main` only** — no feature branches
5. **Service enables**: always `file: state=link` into `multi-user.target.wants/` — never `systemd: enabled: yes` (breaks in chroot)
6. **HTTP on port 80 is intentional** — do not add a redirect to HTTPS

---

## Fix Log

When shipping a non-trivial bug fix — especially one whose correctness can only be confirmed on real hardware — create a fix log entry in `.claude/fixes/` before committing. The template and naming convention are in `.claude/fixes/README.md`.

**When to create an entry:**
- Any fix where hardware behaviour is uncertain (confidence below ~90%)
- Any fix that touches multiple subsystems or has a meaningful regression surface
- Any fix that was already attempted once and shipped (second-attempt entries reference the first)

Skip for typo fixes, pure docs changes, and dependency bumps.

**File naming:** `YYYY-MM-DD-<short-sha>-<slug>.md`

**After hardware verification:** fill in the **Outcome** section of the relevant entry — what actually happened, whether the hypothesis was validated, and any follow-up. Don't leave it blank.

**Before attempting a fix:** check `.claude/fixes/` for prior attempts on the same symptom. If one exists, reference it in the new entry rather than repeating background.

---

## Vibe Session Guidance

When writing prompts for vibe:
- Give vibe the **problem to solve**, not pre-written code — let it do the thinking
- Reference files by path; vibe has its own context window from previous runs
- Vibe sessions can be kept open across multiple Claude turns to preserve context
- After vibe completes, check `git log --oneline -3` and `git status --short` to confirm commits landed cleanly before pushing/tagging
