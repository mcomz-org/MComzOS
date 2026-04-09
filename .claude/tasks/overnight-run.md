# MComzOS Overnight Optimisation Run

This file is a task brief for a Claude Code session running autonomously overnight on the
MComzOS repository. Read everything in this file before touching a single line of code.

---

## What This Project Is

MComzOS is an off-grid emergency communications hub. An Ansible playbook (`site.yml`) builds
a bootable image targeting Raspberry Pi 4/5 (ARM64) and 64-bit PCs (x86_64/amd64) on
Debian 12 Bookworm. The image is built by GitHub Actions on every version tag push and
released as `.img.xz` files.

The codebase is at an early pre-alpha stage. The goal of this run is to **remove all
remaining `ignore_errors` SCAFFOLD markers** from `site.yml`, replacing each with a proper
chroot-safe alternative, so that future builds either succeed cleanly or fail loudly with a
meaningful error — never silently with hidden `ignored=N` counts.

---

## Read These First (in order)

1. `CLAUDE.md` — key files, architecture overview
2. `.claude/tasks/todo.md` — full history of what has been done and why; study Phase A/B/C
3. `site.yml` — the main Ansible playbook (~870 lines)
4. `.github/workflows/build-image.yml` — CI pipeline that builds the images
5. `git log --oneline -20` — recent commits so you understand what has changed

---

## Current State

Latest tag: `v0.0.2-pre-alpha.10`

There are **9 SCAFFOLD `ignore_errors` markers** remaining in `site.yml`. They were added
deliberately as Phase A scaffolding — see todo.md Phase A/B for full context. Your job is
to replace them all with proper fixes (Phase B) without breaking the build.

The grep command to find them all:

```
grep -n "SCAFFOLD" site.yml
```

Expected output (9 lines):
- Line ~395: Pat GitHub API — `failed_when: false`
- Line ~417: ardopcf binary download — `ignore_errors: yes`
- Line ~605: mumble-web npm install — `ignore_errors: yes`
- Lines ~647, ~654, ~663, ~671, ~680: Meshtastic OBS repo tasks (5 tasks)
- Line ~692: meshtasticd config.d write — `ignore_errors: yes`

---

## Fix Specification for Each SCAFFOLD

Work through these in order. Each fix should be committed separately with a clear message.

### 1. Meshtastic OBS repo block (5 SCAFFOLD markers — fix together)

**Lines ~647–692.** Five tasks currently have `ignore_errors: yes`:
- Add Debian Bookworm main archive
- Add Meshtastic apt GPG key download
- Install Meshtastic apt GPG key
- Add Meshtastic apt repository
- Install meshtasticd

**Problem:** Five separate `ignore_errors` means a failure at step 2 causes step 3 to run
with no key file, producing a misleading error, and so on. Better to fail/skip as a unit.

**Correct fix:** Wrap the entire Meshtastic block in an Ansible `block:` / `rescue:` so a
failure in any step (GPG key unavailable, OBS repo down, etc.) causes the whole block to be
skipped cleanly and a single warning is printed. The meshtasticd config.d write (line ~692)
is already guarded with `when: meshtasticd_install is succeeded` — move it inside the block
too so it only runs when the install succeeded.

```yaml
- name: Install Meshtastic (meshtasticd from OBS)
  block:
    - name: Add Debian Bookworm main archive ...
      # (no ignore_errors)
    - name: Add Meshtastic apt repository GPG key ...
      # (no ignore_errors)
    - name: Install Meshtastic apt repository GPG key ...
      # (no ignore_errors)
    - name: Add Meshtastic apt repository ...
      # (no ignore_errors)
    - name: Install meshtasticd ...
      register: meshtasticd_install
      # (no ignore_errors)
    - name: Enable meshtasticd built-in web server ...
      # (no ignore_errors, no when: meshtasticd_install check needed — rescue handles it)
  rescue:
    - name: Warn that Meshtastic install was skipped
      debug:
        msg: "Meshtastic install skipped (OBS repo or Debian main unavailable). LoRa hardware will need manual setup after first boot."
  when: not (minimal_build | default(false))
```

Remove `when: not (minimal_build | default(false))` from the individual tasks inside the
block (put it only on the block itself). Remove `when: meshtasticd_install is succeeded`
from the config.d task since rescue handles the failure path.

### 2. meshtasticd config.d (line ~692)

This is already addressed by the Meshtastic block/rescue above. Once the block is in place
this SCAFFOLD is gone.

### 3. ardopcf binary download (line ~417)

**Problem:** `ignore_errors: yes` on the `get_url` task means a 404 or network error
silently produces a build with no `ardopcf` binary. The downstream systemd unit and service
enable still run.

**Correct fix:** Remove `ignore_errors: yes` and guard the download using `failed_when`
with a meaningful condition, or use a `block:`/`rescue:` pair that warns but skips the
ardopcf service enable if the binary is absent:

```yaml
- name: Download ardopcf pre-built binary
  block:
    - name: Download ardopcf binary from pflarue/ardop releases
      get_url:
        url: "https://github.com/pflarue/ardop/releases/latest/download/ardopcf_{{ 'arm_Linux_64' if deb_arch == 'arm64' else 'amd64_Linux_64' }}"
        dest: /usr/local/bin/ardopcf
        mode: '0755'
  rescue:
    - name: Warn ardopcf download failed
      debug:
        msg: "ardopcf binary download failed (GitHub unavailable or no release for this arch). HF modem (ARDOP) will not work until manually installed."
  when: not (minimal_build | default(false))
```

The ardopcf systemd unit deploy and service enable tasks that follow can stay as-is — the
unit file on disk doesn't harm anything if the binary isn't present, and on first boot
the user can install manually.

### 4. mumble-web npm install (line ~605)

**Problem:** `ignore_errors: yes` masks genuine npm failures. The stall risk under ARM64
qemu is real, but the fix is a timeout + block/rescue, not silent failure.

**Correct fix:** Add a timeout to the npm install task and wrap in block/rescue:

```yaml
- name: Install mumble-web browser client via npm
  block:
    - name: Install mumble-web via npm (with timeout)
      npm:
        name: mumble-web
        global: yes
      async: 600   # 10-minute budget; webpack can be slow under qemu ARM64
      poll: 30
  rescue:
    - name: Warn mumble-web install failed
      debug:
        msg: "mumble-web npm install failed (webpack stall or npm registry unavailable). Browser voice client won't work until manually installed: npm install -g mumble-web"
  when: not (minimal_build | default(false))
```

Note: Ansible's `npm` module may not support `async`/`poll` directly. If it doesn't,
replace with a `shell: npm install -g mumble-web` wrapped in `timeout 600` and block/rescue.

### 5. Pat `failed_when: false` (line ~395)

**Problem:** `failed_when: false` makes the URL resolution task always appear to succeed,
even if curl completely fails (network error, not just a rate-limit). The downstream
`Install Pat` task is already guarded with `pat_deb_url.rc == 0 and stdout length > 0`
which means a silent curl failure just skips Pat installation with no warning.

**Correct fix:** Change `failed_when: false` to a condition that fails loudly on a genuine
curl error but treats a GitHub API error response (rate limit, auth issue) as a soft failure
that skips Pat installation with a warning:

```yaml
      register: pat_deb_url
      changed_when: false
      failed_when: pat_deb_url.rc != 0  # network error = hard failure; API errors handled below
      environment:
        GITHUB_TOKEN: "{{ lookup('env', 'GITHUB_TOKEN') }}"
```

Then add a `debug` task after it that warns if `pat_deb_url.stdout` is empty (API returned
an error response but curl itself succeeded):

```yaml
    - name: Warn if Pat release URL could not be resolved
      debug:
        msg: "Pat release URL could not be resolved (GitHub API error or rate limit). Pat (Winlink) will not be installed."
      when:
        - not (minimal_build | default(false))
        - pat_deb_url.rc == 0
        - pat_deb_url.stdout | default('') | trim | length == 0
```

This way: curl failure = hard build failure (something is wrong with the runner network);
GitHub API rate-limit or schema change = clean skip with visible warning.

---

## Build/Test Cycle

**RPi ARM64 builds take ~90 minutes.** x86_64 builds take ~15 minutes. Plan accordingly.

### How to trigger a build

Push a version tag:
```bash
git tag v0.0.2-pre-alpha.N
git push origin v0.0.2-pre-alpha.N
```

Tag format: `v0.0.2-pre-alpha.N` where N is the next integer after the current latest
(check with `git tag --sort=-version:refname | head -5`).

### How to check build results

```bash
gh run list --limit 5
gh run view <RUN_ID> --log | python3 -c "
import sys
for line in sys.stdin:
    if any(k in line for k in ['TASK', 'ok=', 'failed=', 'ignored=', 'ERROR', 'FAILED', 'fatal']):
        print(line, end='')
" 2>/dev/null | head -200
```

### Stopping criteria

The build is done when **all of the following are true**:

1. `grep -n "SCAFFOLD" site.yml` returns **zero lines**
2. `grep -n "ignore_errors" site.yml` returns **zero lines** (or only lines inside `rescue:`
   blocks where `ignore_errors` is semantically correct — there should be none)
3. The GitHub Actions build shows `failed=0 ignored=0` on both RPi and x86 jobs
4. Only skips in the build log are legitimate arch/mode guards (FreeDATA on arm64,
   MeshCore on x86, build_mode guards for raspi-config/overlayfs)
5. The Ansible summary line reads something like:
   `ok=N changed=N unreachable=0 failed=0 skipped=N rescued=0 ignored=0`

A `rescued=N` count is acceptable and expected — that means block/rescue caught a
recoverable failure (e.g. OBS repo unavailable). `ignored=N` is not acceptable.

---

## Hard Constraints

These are non-negotiable. Do not violate them.

1. **All GitHub releases must have `prerelease: true`** in both `softprops/action-gh-release`
   steps in `.github/workflows/build-image.yml`. Do not remove this flag.

2. **Tag format**: always `v0.0.2-pre-alpha.N`. Do not start a new minor/patch version.

3. **Commit to `main` only**. Do not create feature branches.

4. **Do not change the MComzOS feature set** — no new services, no removed services, no
   port changes, no config file changes beyond what is needed for the SCAFFOLD removal.

5. **Do not touch `README.md`** unless a fix requires it (it is unlikely to require it).

6. **One commit per SCAFFOLD fix.** Commit message format:
   `fix(site): remove SCAFFOLD from <component> — <what replaces it>`

7. **Do not push any tag until you have committed all your changes for that iteration.**
   Push the commit first, then tag, then push the tag.

---

## State Preservation

After each completed build cycle (push tag → wait for result → analyse), write a brief
status update to `.claude/tasks/overnight-summary.md`. Format:

```markdown
## <tag> — <timestamp>
- Build result: RPi ok=N changed=N failed=N ignored=N rescued=N / x86 ok=N...
- SCAFFOLD markers remaining: N
- What was fixed this iteration: ...
- What failed or needs attention: ...
- Next planned action: ...
```

This file is your persistent memory across context resets. Read it at the start of each
new session to understand where you left off.

---

## Common Pitfalls

- **Do not re-introduce `minimal_build=true`** in `.github/workflows/build-image.yml`.
  It was removed deliberately — it was silently skipping 42 tasks in the RPi build.

- **`actions/checkout@v6` is intentional** — Laura upgraded from v4 for Node 24 support.
  Do not downgrade it.

- **Pat uses pre-release tags**, so `/releases/latest` returns 404. The current code
  correctly uses `/releases?per_page=1`. Do not change this URL.

- **MeshCore pip install** may still emit a non-zero exit code under qemu ARM64 because
  `pymc_core[hardware]` has native extensions. This is handled by the block/rescue pattern
  — ensure the rescue path warns rather than silently swallowing the failure.

- **`systemd: enabled: yes`** does not work inside a chroot (fake systemctl). All service
  enables already use `file: state=link` creating symlinks directly in
  `/etc/systemd/system/multi-user.target.wants/`. Do not revert these to `systemd:` tasks.

- **The RPi build takes ~90 minutes.** If you trigger a build and then start making more
  changes, you will be looking at stale results. Finish all changes for an iteration before
  pushing the tag.

---

## Success Definition

This overnight run is complete when:

- `grep -c "SCAFFOLD" site.yml` outputs `0`
- The most recent GitHub Actions run for both jobs shows `failed=0 ignored=0`
- `overnight-summary.md` documents the final clean build result

Good luck.
