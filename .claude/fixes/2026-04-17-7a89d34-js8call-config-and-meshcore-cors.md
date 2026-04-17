---
name: JS8Call .config ownership + MeshCore CORS probe
date: 2026-04-17
commit: uncommitted
files: site.yml, src/dashboard/index.html
status: live-verified, awaiting reflash for playbook fix
---

# Fix A — JS8Call fatal crash on launch (`/home/mcomz/.config/` root-owned)

## Problem

JS8Call crashes immediately on launch inside the VNC session with:

> `Fatal error: Cannot access "/home/mcomz/.config/JS8Call.ini" for writing`

The user sees 4 blank Openbox desktops. This has been a regression for many releases.

## Root cause

Ansible's `file: state=directory` task for `/home/mcomz/.config/openbox` implicitly creates the parent `/home/mcomz/.config/` if it doesn't exist — but as `root:root`, not `mcomz:mcomz`. The `mcomz` user cannot create files in it. JS8Call tries to write its config on first launch and fails immediately.

## Fix

Added an explicit task before the openbox directory task (`site.yml:289`):

```yaml
- name: Create .config directory for mcomz user
  file:
    path: /home/{{ mcomz_user }}/.config
    state: directory
    owner: "{{ mcomz_user }}"
    group: "{{ mcomz_user }}"
    mode: '0755'
```

Also applied live on the Pi: `sudo chown mcomz:mcomz /home/mcomz/.config/`

## Confidence

**High.** Root cause confirmed by `ls -la`; fix confirmed working by live test (JS8Call loaded in VNC session after chown + service restart).

## Outcome

- Verified on: RPi 5, pre-alpha.21, 2026-04-17 (live fix)
- Result: ✅ JS8Call loads and is visible in the VNC session
- Follow-up: Reflash with next image to confirm playbook fix persists

---

# Fix B — MeshCore online probe always routes offline (CORS)

## Problem

Clicking "Flash MeshCore" on the dashboard always opens the local `/meshcore-flash/` fallback, even when the hub has internet. This means users never reach the live flasher at `flasher.meshcore.co.uk`.

## Root cause

`openMeshFlasher()` probes connectivity with a `HEAD` fetch to `flasher.meshcore.co.uk`. The flasher site has no CORS headers, so any `fetch()` from an HTTP page without `mode:'no-cors'` throws a CORS network error regardless of actual connectivity. The `.catch()` fires and the function routes to the offline fallback.

## Fix

One-line change in `src/dashboard/index.html:702` — added `mode: 'no-cors'`:

```diff
- await fetch('https://flasher.meshcore.co.uk/favicon.ico',
-     {method: 'HEAD', cache: 'no-store', signal: AbortSignal.timeout(3000)});
+ await fetch('https://flasher.meshcore.co.uk/favicon.ico',
+     {method: 'HEAD', mode: 'no-cors', cache: 'no-store', signal: AbortSignal.timeout(3000)});
```

`mode:'no-cors'` makes the browser send the request without requiring CORS headers in the response. The fetch resolves successfully if the server responds at all; it rejects only on genuine network failure (DNS error, timeout, no route).

## Confidence

**High.** CORS behaviour is well-specified. The only risk is if the flasher server rate-limits or blocks HEAD requests — in that case the probe would fail even online, but this is unlikely for a public web app.

## Outcome

- Verified on: not yet — needs reflash + online hardware test
- Expected: click Flash MeshCore when online → opens `flasher.meshcore.co.uk`
