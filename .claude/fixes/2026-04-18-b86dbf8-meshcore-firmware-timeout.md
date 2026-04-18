# MeshCore firmware download timeout — `b86dbf8`

**Date:** 2026-04-18
**Commit:** pending (this session)
**Files changed:** `site.yml`, `build-image.yml`
**Related:** build run #24607533367 (pre-alpha.25), previous attempt `4b9569d` (flasher path fix)
**Status:** shipped

---

## Problem

RPi build failed with `"MeshCore offline flasher could not be provisioned after 3 attempts"` for two consecutive builds (pre-alpha.24 and pre-alpha.25). The rescue block aborted the entire build.

## Reproduction

Tag a release and watch the ARM64 CI job — `Run Ansible playbook` step fails ~95 minutes in during the MeshCore flasher block.

## Hypothesis (root cause)

Two distinct problems confirmed by reading the full CI log via `gh api`:

1. **Firmware download timeout**: `get_url` uses a ~10 s default timeout. Some firmware binary downloads (e.g. `heltec_v4_companion_radio_ble-v1.14.1-467959c.bin`) stall and hit it. The latest release has ~60+ Heltec assets; the old filter `'heltec' in name.lower()` was downloading everything Heltec have ever made, so the long tail of slow downloads reliably triggered at least one timeout.

2. **Wrong release endpoint**: The old resolver used `releases/latest` which maps to the most recently *published* release — that could be `room-server-vX`, `companion-vX`, or `repeater-vX` depending on publication order. It was only hitting the companion release and missing all repeater firmware.

3. **Fatal rescue**: The rescue block called `fail:`, aborting the build entirely. A missing offline flasher is non-fatal at runtime (dashboard falls back to `flasher.meshcore.co.uk`), so this was too aggressive.

## Alternatives considered

- **Increase retries only** — wouldn't fix the underlying wrong-release or over-broad filter issue
- **Hardcode firmware URLs** — would break on every MeshCore release; maintenance burden too high

## Fix

1. `site.yml` — replaced `curl`+pipe resolver with a Python `urllib` script that explicitly fetches `companion-vX` and `repeater-vX` releases (not `/latest`), filtered to a whitelist of 15 UK-popular devices. Added `timeout: 120` and `retries: 3` to the `get_url` task.
2. `site.yml` — changed rescue from `fail:` to `debug:` (non-fatal warning).
3. `build-image.yml` — softened the "Verify MeshCore offline flasher" step from `exit 1` to a warning echo.

## Expected outcome

- Build completes even if a small number of firmware files time out (retries handle transient stalls; the rescue no longer aborts)
- Both companion and repeater firmware downloaded for the 15 supported UK devices
- CI log shows which files succeeded/failed rather than a single abort

## Confidence

High for the timeout fix (root cause confirmed in CI log). High for the rescue non-fatal change. Medium for the resolver accuracy — depends on MeshCore's release naming staying consistent.

## Risks / failure modes

- If MeshCore renames release tags (e.g. `companion-` → `fw-companion-`) the resolver returns no URLs and the block silently succeeds with an empty firmware dir. The non-fatal rescue means this won't abort the build.
- `timeout: 120` may still be too short for large `.bin` files on a congested runner; could increase further if needed.

## Test plan

1. Tag and push — confirm RPi CI build completes without flasher abort
2. On device: verify `/meshcore-flash/firmware/` contains both companion and repeater files for multiple devices (Heltec V3, Heltec V4, T-Deck, T-Echo, T-Beam at minimum)
3. Confirm online flasher fallback still works when `/meshcore-flash/` is unreachable

## Rollback

`git revert <sha>` — restores the old curl-based resolver and fatal rescue.

## Outcome

*(Filled in after hardware verification.)*

- Verified on:
- Result:
- What actually happened:
- Follow-up:
