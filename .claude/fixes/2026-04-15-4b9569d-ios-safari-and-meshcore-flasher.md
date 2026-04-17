# iOS Safari HTTPS loop + offline MeshCore flasher — `4b9569d`

**Date:** 2026-04-15
**Commit:** `4b9569d` — `fix(site,dashboard): iOS Safari HTTPS loop + offline MeshCore flasher`
**Files changed:** `site.yml` (+105 lines), `src/dashboard/index.html` (+23 lines), `.claude/tasks/todo.md`
**Related:** hardware test pre-alpha.19 (items #7 and #12); supersedes pre-alpha.16 item #8 (previous Safari attempt — serve dashboard on HTTP too)
**Status:** shipped — awaiting hardware verification

This commit bundles two independent fixes. Each is tracked separately below.

---

# Fix A — iOS Safari HTTPS redirect loop

## Problem

iOS Safari 18 on iPhone cannot open the MComzOS dashboard. User report, pre-alpha.19:

> "I am unable to connect to MComzOS using Safari again, the Visit Website button after the warning, just takes you back to the 'This Connection Is Not Private' screen. iOS Chrome seems to work."

Severity: blocks primary user journey (dashboard access) on the most common phone platform Safari is the only browser with WebRTC mic access on iOS, so this also blocks Mumble voice.

## Reproduction

1. Flash pre-alpha.19 image; boot RPi.
2. On an iPhone running iOS 18, open Safari and go to `mcomz.local`.
3. Safari auto-upgrades to `https://mcomz.local/`.
4. Cert warning appears; tap "Visit Website".
5. Cert warning re-appears immediately. No dashboard ever loads.

## Hypothesis (root cause)

iOS 15+ silently upgrades bare hostnames to HTTPS. Once on HTTPS, Safari serves the dashboard HTML but then re-evaluates each sub-resource (`fetch('/api/status')`, CSS, JS) against the self-signed cert and re-blocks them individually. The initial "Visit Website" exception only covers the top-level document, not sub-requests. The user sees the warning bounce back because Safari is presenting it for the first blocked `fetch()`, not for the page itself.

The fix doesn't need to make HTTPS work — it needs to get the user off HTTPS entirely. A page with no sub-resources and a plain HTTP link will let them tap through once and never return.

## Alternatives considered

- **Add a real cert via Let's Encrypt** — rejected; requires internet and public DNS, neither of which an offline hub has.
- **Install a self-signed CA on each device** — rejected; requires per-device setup, defeats "just connect and go".
- **Redirect HTTPS → HTTP at the nginx level** — rejected; browsers (Safari included) refuse to follow a 301/302 from HTTPS to HTTP for security reasons.
- **Serve the dashboard on HTTP only** (what pre-alpha.16 attempted) — partial; kept HTTPS available for Mumble mic but Safari still auto-upgrades bare hostnames, so the problem returned.
- **Minimal HTML redirect page at HTTPS `/`** (chosen) — Safari will cert-warn once on the HTTPS document, the user taps through, the page has no sub-resources for Safari to re-block, and the link drops them to HTTP for everything real.

## Fix

`site.yml` — in the nginx server block for port 443, `location /` replaced:

```diff
- location / {
-     try_files $uri $uri/ /index.html;
- }
+ location / {
+     default_type text/html;
+     return 200 '<!DOCTYPE html>…<a href="http://mcomz.local/">Open Dashboard</a>…';
+ }
```

All other HTTPS locations (`/api/`, `/mumble/ws`, `/library/`, `/meshcore-flash/`, etc.) are untouched — they remain available for clients that have already trusted the cert (macOS / Linux browsers, Mumble on iOS Safari).

## Expected outcome

- iPhone Safari shows cert warning once; tapping "Visit Website" lands on the redirect page.
- The redirect page has no `fetch()`, no CSS/JS, no images — so Safari has nothing to re-block.
- Tapping the `http://mcomz.local/` link opens the full dashboard with no further cert interaction.
- If we still see the warning bounce back, the hypothesis about sub-resource re-blocking was wrong and the real cause is something else (likely HSTS cache, see below).

## Confidence

**Medium-high.** The mechanism is sound; static HTML with a single plain link is the simplest page Safari can render and there is nothing for its TLS policy to object to on the document itself. Invalidating evidence would be: the warning still bouncing back on a fresh iPhone that has never seen this hostname (implies the root cause is something other than sub-resource blocking).

## Risks / failure modes

- **Stale HSTS cache on the test device** — if a previous build sent `Strict-Transport-Security`, Safari would refuse to follow the HTTP link. The playbook has never emitted an HSTS header, so new devices should be clean; a device that was used against earlier builds may need Safari website data cleared.
- **iOS caching the old cert warning state** — "Visit Website" is session-scoped; the user may need to tap it once per Safari launch.
- **Regression: users who currently land on `https://mcomz.local/` and expect the full dashboard (e.g. macOS Safari with cert trusted) now get a redirect page instead.** Acceptable: the link on the page still gets them to the dashboard, and HTTP works for everyone.

## Test plan

Preconditions: freshly flashed image, iPhone running iOS 18, Safari website data cleared for `mcomz.local`.

1. On iPhone Safari, navigate to `mcomz.local`. Expect auto-upgrade to HTTPS and a cert warning.
2. Tap "Visit Website". **Pass:** dark redirect page with heading "MComzOS" and a visible link to `http://mcomz.local/`.
3. Tap the link. **Pass:** full dashboard loads, all status tiles populate, no further cert warning.
4. Force-close Safari. Reopen `mcomz.local`. **Pass:** Safari goes directly to `http://mcomz.local/` without looping back through HTTPS.
5. **Regression check — macOS Chrome:** `https://mcomz.local/mumble/` still loads the Mumble web UI (non-root HTTPS still serves).
6. **Regression check — macOS Chrome:** `http://mcomz.local/` still loads the full dashboard.
7. **Regression check — iOS Chrome:** still works as before.

## Rollback

`git revert 4b9569d` restores the `try_files` directive. Rollback has no data impact; just requires a rebuild and reflash.

## Outcome

- Verified on: RPi 5, pre-alpha.21, 2026-04-16
- Result: **Working ✅** — fix confirmed.
- What actually happened: Fresh Safari session (all mcomz.local tabs closed, no saved website data found). Navigating to `mcomz.local` triggered the cert warning. User tapped "Show Details" → "visit the website" (Safari cert exception) → "Visit Website" (link on redirect page) → full dashboard loaded. Two-tap sequence matches the intended redirect-page flow exactly.
- Follow-up: None — fix validated. Minor caveat: user said "appears to enter MComz as I would expect" rather than explicitly describing the redirect page; if doubt arises, confirm HTTPS root serves the minimal redirect HTML and not the full dashboard.

---

# Fix B — Offline MeshCore firmware flasher

## Problem

User report, pre-alpha.19:

> "In hotspot mode Flash MeshCore takes us to https://flasher.meshcore.co.uk/ which fails without internet. It is good to go there when internet is available but can we at least have the Heltec v4 repeater and node flashers available offline when there is no internet access?"

Severity: blocks a core offline-hub use case (flashing a spare radio from the Pi when no other internet is around).

## Reproduction

1. Put MComzOS into hotspot/AP mode (no internet).
2. Connect a phone to the `MComzOS` SSID.
3. Open the dashboard and click "Flash MeshCore" on the MeshCore card.
4. Browser tries to load `https://flasher.meshcore.co.uk/` and fails with DNS / connection error.

## Hypothesis (root cause)

The dashboard button is a plain link to an internet-hosted flasher. There is no offline fallback and no connectivity detection. To fix, we need (a) a local copy of the flasher app and firmware, (b) a way for the dashboard to decide at click-time whether the internet copy is reachable, and (c) the local copy must actually work when served from a subpath under nginx.

## Alternatives considered

- **Always use the live flasher** (current behaviour) — rejected; breaks offline.
- **Always use a local copy** — rejected; live flasher gets updates, and online users should get the latest.
- **Dashboard probes on page load and picks a link** — rejected; connectivity can change between load and click (user could start/stop hotspot), and page load should not block on an external fetch.
- **Dashboard probes on click with short timeout** (chosen) — 3 s is long enough to succeed on a slow uplink but short enough not to feel broken.
- **Download firmware binaries at first boot rather than build time** — rejected; first boot may have no internet.

## Fix

`site.yml` — new Ansible block (wrapped in `rescue:` so GitHub unavailability doesn't break the build):

1. Shallow-clone `meshcore-dev/flasher.meshcore.io` into `/var/www/html/meshcore-flash/`.
2. Python patch script rewrites absolute paths (`/lib/`, `/css/`, `/config.json`) to `/meshcore-flash/`-prefixed equivalents so nginx `alias` serves correctly.
3. Query GitHub releases API for the latest MeshCore release; download every asset with `heltec` in its name into `/var/www/html/meshcore-flash/firmware/`.
4. Patch `config.json` `staticPath` to `/meshcore-flash/firmware`.
5. nginx `alias /var/www/html/meshcore-flash/` at `/meshcore-flash/` on port 80.

`src/dashboard/index.html` — Flash button wired to new `openMeshFlasher()`:

```js
fetch('https://flasher.meshcore.co.uk/', { signal: AbortSignal.timeout(3000) })
  .then(() => window.open('https://flasher.meshcore.co.uk/', '_blank'))
  .catch(() => window.open('/meshcore-flash/', '_blank'));
```

## Expected outcome

- Online: click Flash → live flasher opens as before.
- Offline / hotspot: click Flash → local flasher opens at `/meshcore-flash/`, lists Heltec V3/V4 firmware, completes a flash over WebSerial with no internet needed.
- If the local flasher loads but firmware dropdown is empty, the GitHub release-asset download step silently failed during build (check CI log for rescue-block message).
- If the local flasher loads but a JS fetch 404s, the regex path-rewrite missed a dynamically constructed URL (likely needs a second-pass patch).

## Confidence

**Medium.** Several independent steps have to all work end-to-end:

| Step | Confidence | Why it could fail |
|------|-----------|-------------------|
| Git clone during build | High | GitHub reachable from CI; `rescue:` block handles failure |
| Regex path rewrite | Medium | Covers `<script src>`, `<link href>`, `<img src>`, `config.json`; dynamic `fetch('/…')` in the flasher's JS would be missed |
| GitHub releases asset download | Medium | Depends on asset naming containing `heltec`; unauthenticated API calls are rate-limited |
| Connectivity probe (3 s timeout) | High | Standard `AbortSignal.timeout`; reliable |
| WebSerial flash actually completing | Medium | Web-serial apps are sensitive to subpath rewrites; unverified until hardware test |

Invalidating evidence: local flasher opens but fails to flash, or firmware list is empty despite build logs showing downloads succeeded.

## Risks / failure modes

- **Silent degradation via `rescue:`** — if the provisioning step fails (GitHub down, rate-limited, clone error), the build succeeds but `/meshcore-flash/` is absent. The dashboard will still fall back to opening a broken `/meshcore-flash/` path. Mitigation: CI log should be checked for the rescue-block message "MeshCore offline flasher could not be provisioned".
- **Upstream flasher app updates** — if `flasher.meshcore.io` restructures its asset paths, the patch regex will stop covering everything. Bundled version will silently lag.
- **Firmware naming changes** — if MeshCore renames releases so assets no longer match `heltec`, no firmware is downloaded.
- **Regression surface** — none expected on the dashboard side (button was previously a plain anchor; now a JS handler); other cards untouched.

## Test plan

### Online mode
1. Hub connected to normal WiFi with internet.
2. Click Flash MeshCore. **Pass:** new tab opens `https://flasher.meshcore.co.uk/`.

### Offline / hotspot mode
1. Enable MComzOS hotspot; verify no upstream internet.
2. Connect phone or laptop to `MComzOS` SSID.
3. Open `http://mcomz.local/`, click Flash MeshCore.
4. **Pass:** new tab opens `http://mcomz.local/meshcore-flash/`, flasher UI renders.
5. Check firmware selector — **pass:** lists Heltec V3 and V4 entries.
6. Connect a Heltec V3 (or V4) over USB; pick Repeater or Node firmware; run flash.
7. **Pass:** flash completes; radio reboots; basic MeshCore functionality confirmed.

### Build verification (CI)
- `gh run view <ID> --log` — confirm "Download Heltec V3/V4 MeshCore firmware binaries" step ran and had changed items. If instead the rescue-block debug message appears, firmware is not bundled and the offline feature will be non-functional despite the dashboard linking to it.

## Rollback

`git revert 4b9569d` removes the provisioning block and restores the original Flash button (plain link to live URL). Leaves `/var/www/html/meshcore-flash/` on already-deployed hubs — harmless, cleared on next reflash.

## Outcome

- Verified on: RPi 5, pre-alpha.21, 2026-04-16
- Result: **Two bugs confirmed** — online routing broken; `/meshcore-flash/` itself 403.
- What actually happened:
  1. **Online routing always falls back to local.** Hub is internet-connected; clicking Flash MeshCore opens `https://mcomz.local/meshcore-flash/` instead of `https://flasher.meshcore.co.uk/`. Root cause: `fetch('https://flasher.meshcore.co.uk/')` issued from an HTTP dashboard page fails with a CORS error (flasher site has no CORS headers), not a network error. Browser still fires `.catch()`, so the probe always routes to the offline fallback regardless of connectivity.
  2. **`/meshcore-flash/` returns 403.** Git clone of the flasher repo failed during the CI build (likely GitHub rate-limit); the rescue block ran silently; the directory exists but is empty. No `index.html` → nginx `alias` + `index index.html` returns 403.
- Follow-up: Fix connectivity probe to use `fetch(..., {mode: 'no-cors'})` or a HEAD request (CORS-free); fix build to either retry clone or emit a clearly visible CI failure rather than silently continuing via rescue.
