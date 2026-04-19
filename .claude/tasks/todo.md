# MComzOS TODO

> **How to use this file**
> - **§1 Sonnet-actionable now** — code-only changes with file:line refs, exact target code, and the test that must pass. No hardware needed.
> - **§2 Awaiting reflash to verify** — fixes already in `main`; flash next image and run `tests/MANUAL-TESTS.md` + `tests/smoke-test.py`. Update `.claude/fixes/` outcome sections after.
> - **§3 Blocked: needs hardware logs** — diagnose-then-fix items. The exact commands to run on the Pi are in each entry; paste the output into `.claude/feedback/hardware-test-results.md` under the named heading and Sonnet/Claude can take it from there.
> - **§4 Won't fix / external** — out of scope.
> - **§5 Roadmap** — post-v0.0.2 features.
> - **§6 Historical record** — preserved for audit; do not edit.
>
> Key: `[vibe]` = code changes — use vibe. `[claude]` = test infra, research, diagnostic work — do directly.
> Coverage rule (CLAUDE.md): every behavioural change ships with a test in the same commit.

---

## §1 — Sonnet-actionable now

> S-1 through S-8 shipped (S-1–S-7 in pre-alpha.22, S-8 in pre-alpha.27). All §1 items complete. See §2 for remaining hardware verification items.

### ~~S-2. MeshCore CORS probe fix~~ — COMPLETE

`fetch(..., {method:'HEAD'})` fails with a CORS error even when online because `flasher.meshcore.co.uk` has no CORS headers. Adding `mode:'no-cors'` makes the probe succeed on a reachable server without requiring CORS headers. **Shipped this session** — needs hardware verify: click Flash MeshCore when online → should open `flasher.meshcore.co.uk`.

### S-3. JS8Call `.config` ownership — `site.yml:289`

`/home/mcomz/.config/` was created by Ansible as `root:root`; `mcomz` user could not create `JS8Call.ini`, causing immediate fatal crash on launch. Added explicit `.config` directory creation task with `owner: mcomz`. **Live-fixed on Pi and shipped in playbook** — confirmed working this session. Needs reflash to verify the playbook fix persists.

### S-1. Smoke test: add individual ZIM checks + /meshcore-flash/ + VNC/FreeDATA coverage

Pre-alpha.21 hardware test revealed four smoke test gaps:

1. **All 3 MComzOS ZIMs individually** — current check passes if any one keyword (`survival`/`literature`/`scripture`) is present; need three separate checks. Also add a content-fetch for each registered ZIM by **slug** (not UUID — see S-4) — not just the first book.
2. **WikiMed** — current check is keyword-only; add a slug content-fetch once registered.
3. **`/meshcore-flash/`** — not checked at all; add a check that it returns 200 (not 403/404).
4. **FreeDATA on ARM64** — add a check that on ARM64 the FreeDATA card is either absent or clearly flagged unavailable (HTML-check.py).

VNC/JS8Call auth cannot be automated (needs a WebSocket VNC client); add to MANUAL-TESTS.md instead.

Coverage rule: tests must cover the new behaviour, not just pass because they don't know about it.

### S-4. Kiwix routing: switch dashboard + smoke test from UUID to slug `[claude+vibe]`

**Root cause (pre-alpha.21):** kiwix-serve's `/library/content/<X>/` route expects the **slug** (the `name=` attribute on `<book>` in `library.xml`), not the UUID. The dashboard download path (`status.py:262`) writes books with `id=` and `path=` only — no `name=` — so kiwix auto-derives a slug from the filename. UUID lookups always 404. This is the real cause of the pre-alpha.21 "Kiwix UUID 404" symptom (B-4 in §3 — likely resolved by this fix without needing the full diagnostic).

**Edits:**

- `src/api/status.py:214-227 kiwix_books()` — replace `library.xml` parsing with a query against kiwix-serve's own catalog (it is the source of truth for which slugs it actually serves):
  ```python
  with urllib.request.urlopen("http://127.0.0.1:8888/catalog/v2/entries?count=200", timeout=3) as r:
      tree = ET.fromstring(r.read())
  # parse OPDS Atom; for each <entry>: id (UUID), name (slug), title, summary, length
  ```
  Return per book: `{ "id", "name", "title", "size", "language" }`. On exception (kiwix not yet up), fall back to the current `library.xml` parser so the API still responds during boot.
- `src/dashboard/index.html:747` — change `\`/library/viewer#${encodeURIComponent(b.id)}\`` → `\`/library/viewer#${encodeURIComponent(b.name)}\``.
- `tests/smoke-test.py:255` — change `/library/content/<uuid>/` → `/library/content/<slug>/`. Loop over **every** book, not just the first.
- `tests/html-check.py` — assert the viewer href uses `b.name` (regression guard).

**Acceptance:** smoke-test passes against a Pi with both MComz and downloaded ZIMs; clicking a book in the dashboard library list opens the viewer and content renders.

### S-5. MeshCore offline flasher CI hardening `[vibe]`

**Root cause (pre-alpha.21):** `site.yml:1347` git clone fails in CI; `rescue:` block at line 1425 swallows the failure with a `debug:` message — build still ships green, image arrives with a missing `/var/www/html/meshcore-flash/` directory and the dashboard falls back to a 403/404.

**Edits:**

- `site.yml:1347` (Clone MeshCore web flasher) — add `register: clone_result`, `until: clone_result.rc == 0`, `retries: 3`, `delay: 10`.
- `site.yml:1425-1428` (rescue block) — replace the `debug:` task with `fail: msg="MeshCore offline flasher provisioning failed; build aborted to avoid shipping a broken image"`.
- `.github/workflows/build-image.yml` — add a post-Ansible CI step: `test -s "$MNT/var/www/html/meshcore-flash/index.html" || (echo "meshcore-flash missing" && exit 1)`. Same for both arm64 and x86 jobs.
- `tests/smoke-test.py` — add: GET `/meshcore-flash/`; assert HTTP 200 and body contains `flasher` or `MeshCore` (catches future 403/404 silently).

**Acceptance:** if GitHub is unreachable or the clone fails 3× in a row, CI fails loudly. Reflashed image always serves `/meshcore-flash/`.

### S-6. FreeDATA arch-aware UI `[vibe]`

**Pre-alpha.21:** dashboard always renders the FreeDATA Connect button even on ARM64, where there is no AppImage and the button does nothing.

**Edits:**

- `src/api/status.py` — extend the `/api/status` payload with `"freedata_installed": bool`. True iff the AppImage exists at the path used by `site.yml` (confirm by grepping the FreeDATA install task — typically `/opt/freedata/FreeDATA-<ver>.AppImage` or wherever `Pat and FreeDATA URLs made architecture-aware` deposits it).
- `src/dashboard/index.html:316-320` — read `status.freedata_installed`. If false, replace the `mesh-section` content with: "FreeDATA is not yet available on this device (no ARM64 AppImage published upstream — see [DJ2LS/FreeDATA](https://github.com/DJ2LS/FreeDATA))."
- `tests/html-check.py` — assert the FreeDATA section gates on `freedata_installed`.

**Acceptance:** ARM64 hub no longer shows a dead Connect button; x86 hub (where the AppImage installs) is unchanged.

### ~~S-8. Kiwix viewer theme — round 2 (toolbar, cover thumb, icons)~~ — COMPLETE (b86dbf8, pre-alpha.27) `[vibe]`

**Status of S-7 (shipped in 680f36e, pre-alpha.22):** `body`, book tiles, search box, home page all went dark ✅. **But the viewer page (`/library/viewer#<slug>`) is only half-themed** — user screenshots on 2026-04-18 show:

1. **Top toolbar still light.** DevTools confirms: `div#kiwixtoolbar.ui-widget-header` → background `#F4F6FB`, color `#EEDEE0` (near-white text on near-white bg — unreadable), font `10px -apple-system`, padding `5px`. Current `kiwix-overrides.css` lines 16–24 target `header`, `nav`, `#kiwix_serve_taskbar`, `.kiwixHeader` — **none of these match the viewer's jQuery-UI-themed toolbar**. The only selectors that would catch it are `#kiwixtoolbar` (id) or `.ui-widget-header` (jQuery UI class).
2. **Book cover thumbnail renders as browser broken-image glyph** in the header card — the `<img>` the viewer tries to load is either 404ing (illustration endpoint mismatch) or hitting a CSP/CORS issue. Either hide it gracefully or serve a placeholder.
3. **PDF/document icon next to the thumbnail is visibly artifacted / blurry / inverted-then-squashed.** Current CSS line 93–99 applies `filter: invert(1) brightness(1.2)` to `#kiwix_serve_taskbar img, header img, nav img, img.favicon` — on the viewer page that CSS scope is wrong, but the artefact shown is on a small sprite in the toolbar, almost certainly a jQuery UI `.ui-icon` sprite being stretched or an SVG getting hit by an unintended filter. Need to scope filters to **exactly** the raster icons kiwix ships, and handle `.ui-icon` sprite separately.
4. **Background on the viewer is pure `#121212`.** Acceptable but the header "card" wrapping the cover + title is stark white; needs to be `var(--panel)` with `var(--text)`.

The first three are blockers; (4) is the knock-on once (1) is fixed because the `.ui-widget-header` class also paints the header card.

**Reference — verified from the screenshots, not guessed:**

- Top bar element: `<div id="kiwixtoolbar" class="ui-widget-header">` — jQuery UI theme. Kiwix ships jQuery UI's stock stylesheet; `.ui-widget-header` has a very high specificity background-image gradient that our plain `background:` loses to without `!important` on the right selector. Our current CSS has `!important` but on the wrong selectors.
- The book header card immediately below the toolbar also uses jQuery UI `.ui-widget-content` in at least some kiwix-tools versions. Target both.
- The small icon that's mangled lives inside the toolbar — kiwix-tools uses jQuery UI `.ui-icon` sprite (single PNG, `background-position` shifted per icon). Inverting the whole sprite with `filter:` is fine in principle but our current filter rule doesn't match `.ui-icon` (it matches `img` only), so the artefact is something else — probably a `<svg>` or inline `<img src="data:...">` inheriting a wrong size. **Do not guess** — on a running Pi, run `curl -s https://mcomz.local/library/viewer\#mcomz-scriptures/berean-standard-bible.html | sed -n '1,120p'` and read the actual toolbar markup before writing the selector list. If SSH is blocked (see B-8), use `gh run view` logs or `docker run --rm -it kiwix/kiwix-tools kiwix-serve ...` locally to inspect the same HTML offline.

**Edits:**

1. **`src/theme/kiwix-overrides.css` — add jQuery UI coverage.** Append a new block before the existing "Monochromatic icons" rule:

   ```css
   /* jQuery UI — kiwix viewer toolbar uses these classes */
   #kiwixtoolbar,
   .ui-widget-header {
       background: var(--panel) !important;
       background-image: none !important;   /* kill jQuery UI gradient */
       border: none !important;
       border-bottom: 1px solid #333 !important;
       color: var(--text) !important;
       font-family: var(--font-sans) !important;
       font-size: 0.9rem !important;
       padding: 8px 12px !important;
   }
   #kiwixtoolbar a,
   .ui-widget-header a { color: var(--blue) !important; }
   #kiwixtoolbar label,
   .ui-widget-header label { color: var(--text) !important; }

   .ui-widget,
   .ui-widget-content {
       background: var(--panel) !important;
       background-image: none !important;
       color: var(--text) !important;
       border-color: #333 !important;
   }

   /* jQuery UI buttons inside the toolbar (home, random, fullscreen) */
   .ui-button,
   .ui-state-default,
   .ui-widget-content .ui-state-default,
   .ui-widget-header .ui-state-default {
       background: #222 !important;
       background-image: none !important;
       border: 1px solid #444 !important;
       color: var(--text) !important;
   }
   .ui-button:hover,
   .ui-state-hover,
   .ui-widget-content .ui-state-hover,
   .ui-widget-header .ui-state-hover {
       background: #2a2a2a !important;
       border-color: #666 !important;
       color: var(--text) !important;
   }

   /* jQuery UI icon sprite — invert the whole sprite, NOT the whole <img> */
   .ui-icon {
       filter: invert(1) brightness(1.1) !important;
   }
   ```

2. **`src/theme/kiwix-overrides.css` — tighten the raster-icon filter.** Replace lines 93–99 (the `img` filter block) with a scoped version that explicitly lists what to invert and excludes book-cover thumbnails:

   ```css
   /* Monochromatic icons in kiwix chrome — scope narrowly, never hit covers */
   #kiwixtoolbar > img,
   #kiwixtoolbar button img,
   .kiwix-header img.icon,
   img.favicon,
   img[src$=".svg"][src*="skin/"] {
       filter: invert(1) brightness(1.2) !important;
   }
   /* Explicitly DO NOT filter book-cover illustrations */
   img[src*="/catalog/v2/illustration/"],
   img.book-cover,
   .book-cover img { filter: none !important; }
   ```

3. **`src/theme/kiwix-overrides.css` — handle the broken cover thumbnail.** The viewer's book header img is loaded from `/library/catalog/v2/illustration/<uuid>?size=48` (or similar). If the registered ZIM has no illustration in its header, the endpoint returns 404 and the browser shows its generic broken-image glyph. Fix:

   ```css
   /* Hide broken illustration icons instead of showing the browser glyph */
   img[src*="/catalog/v2/illustration/"] {
       background: var(--panel);
       min-width: 48px;
       min-height: 48px;
       color: transparent;              /* hide alt text */
   }
   img[src*="/catalog/v2/illustration/"]:not([src$=".png"]):not([src$=".jpg"]) {
       visibility: hidden;              /* last-resort hide if image errors */
   }
   ```

   Better fix (do this AS WELL) — in `site.yml:1041` change kiwix-serve's launch to pass `--blockExternalLinks --customIndex /var/mcomz/kiwix-index.html` only if a placeholder illustration approach is needed. **Skip this sub-step for now** — CSS hiding is enough. Note as follow-up.

4. **`src/theme/kiwix-overrides.css` — the book-header "card" on viewer pages.** Viewer wraps the book meta in a `<div class="ui-widget-content">` that goes white under stock jQuery UI. Already covered by the `.ui-widget-content` rule in step 1 — confirm by flashing and reopening `/library/viewer#mcomz-scriptures/berean-standard-bible.html`. If the card still renders white, inspect it in DevTools and add the specific selector.

5. **`tests/smoke-test.py` — verify the new selectors are present.** In the existing theme block (added by S-7), add a check that `kiwix-overrides.css` served over HTTPS contains the strings `#kiwixtoolbar`, `.ui-widget-header`, `.ui-icon`, and `/catalog/v2/illustration/`:

   ```python
   r = http_get("/theme/kiwix-overrides.css")
   body = r.read().decode()
   for sel in ("#kiwixtoolbar", ".ui-widget-header", ".ui-icon",
               "/catalog/v2/illustration/"):
       assert sel in body, f"kiwix-overrides.css missing required selector: {sel}"
   ```

   Also: fetch `/library/viewer` (no fragment — the server returns the shell HTML) and assert the response body contains both the injected `<link rel="stylesheet" href="/theme/kiwix-overrides.css">` **and** the string `ui-widget-header` (proves the class we're targeting is really there — regression guard against a kiwix-tools upgrade that renames classes).

6. **`tests/html-check.py` — static checks on the CSS file itself.** Assert `kiwix-overrides.css`:
   - contains `.ui-widget-header` rule (one of the four new required selectors)
   - contains a `filter: none` rule scoped to `/catalog/v2/illustration/` (regression guard against the "mangled cover" bug returning if someone re-adds a broad `img { filter: invert() }`)
   - does NOT contain an unscoped `img { filter: invert` rule

7. **`tests/MANUAL-TESTS.md` — extend section 12 (Kiwix dark-mode) with viewer-specific steps:**
   - Open `https://mcomz.local/library/viewer#mcomz-scriptures/berean-standard-bible.html`
   - Top toolbar is dark (`#1e1e1e` panel), text legible against it
   - No broken-image glyph anywhere in the toolbar or book header
   - Any small icons in the toolbar are crisp (not artifacted, not squashed, not blurry)
   - Home / random / fullscreen jQuery UI buttons render as dark pills with hover feedback
   - Click home icon → returns to `/library/` book list (still dark)

**Acceptance:**

- `#kiwixtoolbar.ui-widget-header` has `background-color: rgb(30, 30, 30)` in computed styles (DevTools) — confirms `var(--panel)` won, jQuery UI's default gradient was overridden
- No broken-image glyph visible on any viewer page for any of the 3 shipped MComz ZIMs
- All smoke-test and html-check additions green; MANUAL-TESTS section 12 updated

**Non-goals:**

- Do not rewrite jQuery UI entirely — we override the handful of classes kiwix actually uses, nothing else
- Do not touch ZIM internal CSS (articles stay as-authored — Appropedia / WikiMed / Bible content)
- Do not add a dark-mode toggle (post-alpha)

**If Sonnet gets stuck:**
- If `!important` rules still lose: the jQuery UI stylesheet is being injected *after* `</head>` (e.g. in the body via JS). Fix: move the `sub_filter` to inject on `</body>` instead, so our stylesheet is last in cascade. Or add `<link>` twice (before `</head>` and before `</body>`).
- If the cover still shows broken: curl the illustration URL directly (`curl -I https://mcomz.local/library/catalog/v2/illustration/<uuid>?size=48`) — a 404 means the ZIM lacks an illustration header (MComzLibrary pipeline bug, §4) and the CSS hide is the correct fix; a 200 with the wrong content-type means kiwix-serve is the problem, not us.
- If `filter: invert()` still mangles an icon: inspect it in DevTools — if it's an `<img>` with a `data:image/svg+xml;base64,...` src, the filter is correct but the SVG's own stroke may be transparent-on-transparent. Switch that one icon to `opacity: 0.85; filter: none;` with a targeted selector.

---

### S-7. Unified dark theme for Kiwix viewer (and proxied apps) — SHIPPED in pre-alpha.22 (partial) `[vibe]`

**Problem (user-reported, 2026-04-18):** Dashboard at `mcomz.local` is dark and modern. Click a ZIM → Kiwix's default chrome appears — light grey header, boxy buttons, 1995-era aesthetic (screenshot: Appropedia ZIM, grey bar with 🏠 / "Appropedia" / 🎲 / "Search 'Appropedia'"). Jarring transition. The iOS Kiwix app does this right: black background, monochromatic icons, rounded search that appears on pull-down. We want the same vibe in-browser, consistently across `/library/` and where possible across `/meshtastic/`, `/meshcore/`, `/mumble/`, `/vnc/`, `/pat/`.

**Approach:** Inject a custom stylesheet into every HTML response served under `/library/` via nginx `sub_filter`. kiwix-serve has no `--customResources` equivalent — CSS injection at the proxy is the only non-fork lever. Same pattern applies (where proxied) to other app chrome.

**Design tokens — lift from `src/dashboard/index.html:8-18`:**

```
--bg: #121212;   --panel: #1e1e1e;   --text: #e0e0e0;   --muted: #888;
--green: #00e676; --blue: #29b6f6; --orange: #ff9800; --red: #ef5350;
font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
radius: 4-8px   button-radius: 4px   card-radius: 8px
```

These must be centralised — any future dashboard tweak should cascade. Extract them into a single file served by nginx: `src/theme/mcomz-theme.css` (new). Both the dashboard and the injected overrides import it via `@import url("/theme/mcomz-theme.css")` so the shared tokens live in one place. Dashboard `<style>` block stays but consumes the tokens via `:root` fallback defined there today.

**Gotcha — nginx module availability:** `sub_filter` lives in `ngx_http_sub_module`, which is NOT in Debian 12's `nginx-core` (what the `nginx` metapackage installs today, `site.yml:1336-1339`). First step before anything else: switch the apt package to `nginx-light` (smallest variant that ships sub_filter). Confirm on the Pi: `nginx -V 2>&1 | tr ' ' '\n' | grep -i sub`.

**Gotcha — gzipped upstream:** kiwix-serve sends `Content-Encoding: gzip` when the client accepts gzip. nginx `sub_filter` only rewrites uncompressed bodies. Fix: `proxy_set_header Accept-Encoding "";` on the `/library/` location so the upstream returns plaintext.

**Gotcha — content-type filtering:** default `sub_filter_types` is just `text/html`. Kiwix also serves XHTML in some ZIMs as `application/xhtml+xml`. Add: `sub_filter_types text/html application/xhtml+xml;`. Use `sub_filter_once off;` so the pattern matches on every page.

**Gotcha — ZIM-internal CSS:** the iframe content inside `/library/viewer` (the actual Appropedia/WikiMed pages) is HTML from inside the ZIM and carries its own stylesheet. We cannot force every ZIM page to be dark — only the *kiwix-serve chrome* (book index, search results, viewer toolbar, welcome page). That is what matters and what the user complained about. Scope explicitly excludes rewriting in-ZIM article styles. A forced-dark filter toggle can be added later under §5.

**Edits:**

1. **`site.yml:1336-1339`** — change package from `nginx` to `nginx-light`. Keep `state: present`. Add a post-install assert task: `command: nginx -V` with `register:` + a `fail:` if the output doesn't contain `http_sub_module`.

2. **New file: `src/theme/mcomz-theme.css`** — design-token CSS variables plus a small reset. Export `:root { --bg, --panel, --text, --muted, --green, --blue, --orange, --red, --pink; --radius-card: 8px; --radius-btn: 4px; --font-sans: -apple-system, ... }`. No component styles here — just the tokens.

3. **New file: `src/theme/kiwix-overrides.css`** — targeted overrides for kiwix-serve's chrome. Inspect kiwix-tools's HTML first with `curl -s http://mcomz.local/library/ | less` and `curl -s http://mcomz.local/library/viewer` to capture the actual class names and IDs (they are stable across kiwix-tools 3.x). Typical targets: `body`, `.kiwixHomePage`, `#kiwix_serve_taskbar`, `.kiwix-header`, `input[type=search]`, book tile cards, pagination. Styles to apply:
   - `body { background: var(--bg); color: var(--text); font-family: var(--font-sans); }`
   - Replace grey top bar with `background: var(--panel); border-bottom: 1px solid #333;`
   - Search box: `background: #222; border: 1px solid #444; color: var(--text); border-radius: 999px; padding: 8px 14px;` — rounded pill like the iOS app
   - Icons: `filter: invert(1) brightness(1.2);` on any raster icons kiwix ships, or swap for inline SVGs using `currentColor` if kiwix exposes a hook
   - Book tiles: `background: var(--panel); border-radius: var(--radius-card); border: none;` on hover `background: #252525`
   - Links: `color: var(--blue)`; visited: `color: #b39ddb`
   - First line of the file must be `@import url("/theme/mcomz-theme.css");` so tokens are shared

4. **`site.yml` — new task block before the dashboard copy (`site.yml:1341`):**
   ```yaml
   - name: Deploy MComz theme CSS (shared tokens + app overrides)
     copy:
       src: "./src/theme/"
       dest: /var/www/html/theme/
       mode: '0644'
   ```
   Exposes `/theme/mcomz-theme.css` and `/theme/kiwix-overrides.css` as static assets served by the existing `location /` block (the `try_files` fallthrough already catches them).

5. **`site.yml` nginx config — modify the `/library/` location (`site.yml:1622-1624`):**
   ```nginx
   location /library/ {
       proxy_pass http://127.0.0.1:8888/library/;
       proxy_set_header Accept-Encoding "";
       sub_filter_once off;
       sub_filter_types text/html application/xhtml+xml;
       sub_filter '</head>' '<link rel="stylesheet" href="/theme/kiwix-overrides.css"></head>';
   }
   ```
   Do the same for `/library/test/success.html` at `site.yml:1536-1538` (captive-portal dummy block) only if it serves HTML — otherwise skip.

6. **`src/dashboard/index.html:7`** — replace the inline `:root { --bg: ... }` block with `@import url("/theme/mcomz-theme.css");` at the top of the `<style>` block. Keep all other dashboard CSS inline (component styles specific to the dashboard stay where they are). This proves the token file is wired in and will catch breakage via html-check.

7. **Stretch — proxied apps (same pattern, optional within this S-7 scope):**
   - `/meshtastic/` at `site.yml:1641-1643` — inspect first; if the Meshtastic web UI ships its own dark theme already, skip
   - `/meshcore/` at `site.yml:1646-1648` — same, inspect first; pyMC_Repeater's UI is known light-grey
   - `/pat/` (inside the separate `:8081` server block — search for `pat` in site.yml) — Pat's inbox UI is light; worth overriding
   - `/mumble/` — we own the static files at `/usr/local/lib/node_modules/mumble-web/dist/`. A post-install sed/patch task to inject our stylesheet link into its `index.html` is simpler than sub_filter since it's nginx `alias`, not `proxy_pass`
   - `/vnc/` — noVNC at `/usr/share/novnc/vnc.html`. Same approach — post-install patch

   For each stretch target: create `src/theme/<app>-overrides.css`, deploy alongside the others, wire up. Do NOT attempt all five in one shot — Kiwix is the priority, everything else is follow-on.

**Tests (coverage rule — mandatory):**

- **`tests/smoke-test.py`** — add checks:
  - `GET /theme/mcomz-theme.css` → 200, content-type `text/css`, body contains `--bg:` and `#121212`
  - `GET /theme/kiwix-overrides.css` → 200, body contains `@import url("/theme/mcomz-theme.css")`
  - `GET /library/` body contains `<link rel="stylesheet" href="/theme/kiwix-overrides.css">` (proves sub_filter fired)
  - `GET /library/viewer#<slug>` for a known slug — same assertion
  - HEAD `/library/` has no `Content-Encoding: gzip` (proves the Accept-Encoding strip worked)

- **`tests/html-check.py`** — add assertions:
  - `index.html` `<style>` block starts with `@import url("/theme/mcomz-theme.css");`
  - The inline `:root { --bg: ...; }` block has been removed (it now lives in the imported file)
  - New per-file static check: `src/theme/mcomz-theme.css` parses as syntactically valid CSS (basic `{` / `}` balance + `:root` present) and exports at least `--bg`, `--panel`, `--text`, `--blue`
  - `src/theme/kiwix-overrides.css` imports the token file as its first statement

- **`tests/MANUAL-TESTS.md`** — add a new section **"Theme — Kiwix viewer"**:
  - Open `https://mcomz.local/` → dashboard is dark (unchanged from pre-alpha.22 baseline)
  - Click any ZIM in the library list → Kiwix index page loads with: dark `#121212` background, rounded pill search bar, no grey header bar
  - Click a book tile → viewer chrome is dark; in-article ZIM content may be light (documented limitation, not a regression)
  - On iOS Safari dark mode: verify no flash of light content on load (FOUC)
  - Resize browser narrow → responsive; search bar doesn't overflow

**Acceptance:**

- `/library/` and `/library/viewer*` pages render with the dashboard's palette — no grey 1995 header
- Book tiles and search bar match the dashboard's card/input style
- Dashboard itself still renders identically to pre-alpha.22 (the `@import` refactor is a no-op visually)
- All three smoke-test additions pass; html-check covers the new files; MANUAL-TESTS entry added

**Non-goals for this ticket (explicit):**

- Do not try to style ZIM article bodies (Appropedia's own CSS, WikiMed's own CSS) — out of scope, ZIM-internal
- Do not add a dark-mode *toggle* — post-alpha feature (§5 candidate)
- Do not touch the kiwix-tools binary, kiwix-desktop, or fork anything upstream

**If Sonnet gets stuck:** the three most likely failure modes are (a) sub_filter never fires because `nginx-core` is still installed — check `nginx -V`; (b) response is gzipped — check `curl -I -H "Accept-Encoding: gzip" http://localhost/library/` returns no `Content-Encoding` header; (c) the selector names in kiwix-overrides.css don't match the actual kiwix-serve HTML — always inspect live output before writing the override file.

---

## §2 — Awaiting reflash to verify (no code work needed, just hardware test)

### Verified in pre-alpha.22 (2026-04-17)

| Fix | Outcome |
|---|---|
| S-1: Smoke test ZIM gaps (individual ZIM checks, slug content-fetches, /meshcore-flash/) | ✅ All 3 MComz ZIMs individually checked by slug; content-fetches all 200; /meshcore-flash/ 200 ✅ |
| S-2: MeshCore CORS probe (`mode:'no-cors'`) | ✅ Flasher provisioned and responding; online-routing needs manual verify on connected hub |
| S-4: Kiwix slug routing (OPDS catalog, b.name in dashboard) | ✅ All 3 ZIMs with correct slugs; content fetches by slug all pass; titles via filename fallback working |
| S-5: MeshCore CI hardening (retry + rescue→fail + CI verify step) | ✅ /meshcore-flash/ serves correctly in pre-alpha.22 — CI step passed |
| S-6: FreeDATA arch-aware UI (`freedata_installed` field) | ✅ API returns `false` on ARM64; section hidden; html-check.py 120/120 |
| VNC stack: Xvnc, noVNC, websockify | ✅ All confirmed by smoke test (5901 open, websockify 101, noVNC page) |
| JS8Call `.config` ownership | ✅ Playbook fix confirmed — /home/mcomz/.config is mcomz-owned in new image |
| WikiMed `Restart=on-failure` + `RestartSec=30` | ✅ Confirmed — fired once on first boot, downloaded 2.1 GB wikimed-maxi successfully |

### Verified in pre-alpha.21/22 (2026-04-16/17)

| Fix | Outcome |
|---|---|
| VNC no-auth + correct noVNC path (`path=websockify`) | ✅ JS8Call window confirmed visible in Chrome + Safari |
| MeshCore CORS probe | ✅ flasher.meshcore.co.uk opens when online |
| Mumble voice | ✅ Confirmed working |
| VNC websockify upgrade — smoke test | ✅ Confirmed |
| iOS Safari HTTPS | ✅ Confirmed |

### Still awaiting hardware confirmation

| Fix | Where | Verify with |
|---|---|---|
| Captive portal suppression + avahi restart on AP stop | `site.yml` + `status.py` (6c9d6b0) | Flash new image; connect to hotspot → no CNA popup; stop hotspot → mcomz.local resolves again within ~5 s |
| JS8Call with radio | — | Connect radio, open JS8Call via VNC, make a contact on #MCOMZ net |
| Pat send/receive | — | **After JS8Call radio test** — send a Winlink check-in, confirm it arrives. User has never used Pat before so JS8Call experience first. |

---

## §3 — Blocked: needs hardware diagnostic logs

For each item below: SSH to the Pi (or open a terminal locally), run the listed commands, paste the full output into `.claude/feedback/hardware-test-results.md` under the named heading. Once that's done, the next code session can diagnose and write the fix.

### B-8. SSH password auth rejected on new image

`ssh-copy-id` fails with `Permission denied (publickey,password)` on pre-alpha.22. Either the playbook hardens sshd (`PasswordAuthentication no`) or the Pi image defaults to key-only. Needs one-time manual key install from the Pi:

```sh
# From the Pi console or via the user's existing key
sudo -u mcomz mkdir -p /home/mcomz/.ssh
echo "YOUR_PUBLIC_KEY" >> /home/mcomz/.ssh/authorized_keys
sudo chmod 700 /home/mcomz/.ssh && sudo chmod 600 /home/mcomz/.ssh/authorized_keys
```

Or investigate: `grep -i PasswordAuthentication /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf`

### ~~B-1. JS8Call / VNC~~ — RESOLVED this session

Root cause diagnosed and fixed 2026-04-17:
- VNC auth only works over HTTPS (HTTP path has a silent auth failure — acceptable, dashboard links to `https://mcomz.local/vnc/`)
- `/home/mcomz/.config/` was `root:root`; JS8Call couldn't create its ini file and crashed immediately
- Fixed live on Pi + playbook fix at `site.yml:289`
- JS8Call confirmed loading in VNC session

### ~~B-4. Kiwix ZIM content 404 after download~~ — superseded by §1.S-4

Root cause is now known: kiwix-serve's content route expects the **slug**, not the UUID. Plan in §1.S-4 fixes this without further diagnostics. If S-4 is shipped and the bug still occurs, then re-open this entry and run the Pi-side commands below.

<details><summary>Original diagnostic commands (kept in case S-4 doesn't resolve it)</summary>

```sh
curl -s http://localhost:8888/library/catalog/v2/entries | grep -E "<id>|<title>|<name>"
ls -lh /var/lib/kiwix/*.zim 2>/dev/null || find /var/lib -name "*.zim" -ls 2>/dev/null
find /home -name "*.zim" -ls 2>/dev/null
find /opt -name "*.zim" -ls 2>/dev/null
sudo systemctl status kiwix-serve
sudo journalctl -u kiwix-serve -n 100 --no-pager
curl -i "http://localhost:8888/content/171ffc5a-c68a-4f92-8ad1-279170745a3e/"
```
**Paste under heading:** `## v0.0.2-pre-alpha.21 — Kiwix UUID 404 diagnostic` (only if needed).
</details>

### ~~B-5. MeshCore flash CORS bug~~ — RESOLVED by §1.S-2

Already shipped: `index.html:702` adds `mode:'no-cors'` to the connectivity probe. Awaiting hardware verify (§2).

### B-6. WikiMed first-boot download did not produce a ZIM

**Pre-alpha.21 status:** §1.A catalog name fix is in main, but it's still unconfirmed whether the `mcomz-wikimed-download` oneshot actually ran to completion on first boot. Gather:

```sh
sudo systemctl status mcomz-wikimed-download
sudo journalctl -u mcomz-wikimed-download -n 200 --no-pager
ls -lh /var/mcomz/library/
```

**Paste under heading:** `## v0.0.2-pre-alpha.21 — WikiMed first-boot diagnostic`.

### B-7. Mumble websocket bridge shows `err` despite text chat working

The status badge is driven by `systemctl is-active`. If `mcomz-mumble-ws` failed once at boot and `Restart=on-failure` recovered it, `is-active` may still report a stale failed state — or the dashboard's badge mapping treats `activating` as `err`. Need:

```sh
systemctl status mcomz-mumble-ws
sudo journalctl -u mcomz-mumble-ws -n 200 --no-pager
ss -lntp | grep 64737
curl -i http://127.0.0.1:64737/
```

**Paste under heading:** `## v0.0.2-pre-alpha.21 — Mumble websocket status diagnostic`.

Once logs land: code fix in `src/api/status.py` to either treat `active`-or-`activating` as healthy and only `failed`/`inactive` as err, or check port responsiveness on `localhost:64737` for this service rather than relying solely on `is-active`.

### B-2. Meshtastic showing `err` ("Service crashed, check journalctl")

```sh
sudo journalctl -u meshtasticd -n 200 --no-pager
sudo systemctl status meshtasticd
ls -l /dev/serial/by-id/ 2>/dev/null
ls /dev/i2c-* /dev/spidev* 2>/dev/null
cat /etc/meshtasticd/config.yaml 2>/dev/null | head -60
```
**Paste under heading:** `## v0.0.2-pre-alpha.21 — Meshtastic crash diagnostic`.

### B-3. APRS / direwolf stuck `activating`

```sh
sudo journalctl -u direwolf -n 200 --no-pager
sudo systemctl status direwolf
aplay -l 2>&1
arecord -l 2>&1
ls /dev/snd 2>/dev/null
```
**Paste under heading:** `## v0.0.2-pre-alpha.21 — APRS/direwolf diagnostic`.

---

## §4 — Won't fix / external

- **Kiwix download speed** — server-side throughput / Pi uplink. No code lever.
- **FreeDATA ARM64 (upstream)** — no upstream AppImage; correct fix is a PR to `DJ2LS/FreeDATA` adding ARM64 to its release matrix. Playbook already skips install gracefully. **Dashboard arch-aware UI is in §1.S-6** so pre-alpha.21's "dead Connect button" symptom is addressed in-product even while the upstream gap remains.
- **MComzLibrary ZIM metadata empty (upstream)** — pre-alpha.21 found the MComz ZIMs are missing internal title/language/etc. Fix belongs in the `MComzLibrary` build pipeline (add `--title --description --language --creator --publisher` to whatever wraps `zimwriterfs`). Dashboard already falls back to filename-derived titles, so impact in-product is cosmetic. Action: file an issue on the MComzLibrary repo.
- **PDF books inline on iOS Chrome** — platform limitation.
- **Mumble mic on iOS Chrome** — Apple restricts WebRTC to Safari only on iOS.

---

## §5 — Post-v0.0.2 Roadmap

### WAN Remote Access (WireGuard VPN)
LAN-only today. WireGuard is the recommended approach (fully open source, aligns with "no closed ecosystems").
- **Why:** "Internet is up but I'm not home" — access dashboard, relay messages, check status remotely.
- **Approach:** WireGuard peer config generated at provision time; hub is a peer, user devices are peers, a VPS or home router acts as relay endpoint. Key generation and `wg0.conf` deployed by Ansible.
- **Alternatives considered:** Tailscale (closed coordination server), Headscale (open but more complex to self-host), ZeroTier (similar trade-off to Tailscale).
- Not a priority when internet is down (core use case) — but valuable for pre-positioned hubs managed remotely.

### APRS Map Viewer
Direwolf decodes APRS but no map UI. Future release could add Xastir or a lightweight web-based APRS viewer.

### Dashboard features (requested 2026-04-09)

**Inline service guides (offline-friendly):**
- Mumble: inline "How to connect" guide on the dashboard card. Cover: enter any username, leave password blank, allow microphone when prompted, push-to-talk vs voice-activated. *(Mumble guide already shipped — verify and tick off.)*
- JS8Call: brief inline guide covering #MCOMZ net schedule and how to send a message.
- Pat: inline guide covering callsign setup and sending a Winlink check-in.

**Radio Communications tab:**
- Add a "Radio Communications" tab alongside "Mesh Communications".
- Gate licenced-radio features behind: "Do you have an Amateur Radio licence and a radio?"
  - No → show explanation of what a licence enables, link to licensing info.
  - Yes → reveal JS8Call (VNC), Pat (Winlink), ardopcf, Direwolf APRS, FreeDATA (when available).
- Unlicenced LoRa hardware (Meshtastic, MeshCore) stays visible without the gate.

**Admin login / protected functions:**
- Login screen protecting admin-only functions (simple password, stored locally — no internet auth).
- Protected: power off / reboot, WiFi panel, add Kiwix books, anything that affects other users on the network.
- Non-admin users can use all comms features without logging in.

**Kiwix library onboarding:**
- Flash screen on first login (or if library is empty) suggesting at least WikiMed.
- "Add Books" button in the Library section — requires login.
- Recommended books list with size variants (uses §1.A real catalog names).

---

## §6 — Historical record (do not edit)

### Key Decisions Made
- TigerVNC + noVNC chosen over Wayland + RustDesk (lighter, browser-native, battle-tested)
- Mumble chosen over XMPP (voice + ephemeral text in one tool; persistent chat not needed for emergency comms)
- websockify used for Mumble bridge instead of mumble-web-proxy (avoids Rust compilation on Pi, already in apt)
- meshtasticd from OBS repo (official apt package, includes bundled web UI)
- pyMC_Repeater for MeshCore (Python, runs on Pi with LoRa HAT, has web dashboard)

### Service Port Map (snapshot)

| Service | Port | Status |
|---------|------|--------|
| Nginx (dashboard) | 80 / 443 | ✅ |
| noVNC (JS8Call etc.) | 6080 → /vnc/ | ✅ |
| Mumble voice+text | 64737 → /mumble/ws | ✅ |
| Meshtastic web UI | 8080 → /meshtastic/ | ✅ |
| MeshCore dashboard | 8000 → /meshcore/ | ✅ |
| Murmur (native client) | 64738 | ✅ |
| Meshtastic TCP API | 4403 | ✅ |
| Kiwix | 8888 → /library/ | ✅ |
| Pat HTTP gateway | 18081 → :8081 (HTTPS) | ✅ |
| Direwolf APRS | 8010 (AGWPORT), 8011 (KISS) | ✅ |
| ardopcf HF modem | 8515 (TCP) | ✅ |
| Status API | 9000 → /api/ | ✅ |

### Major completed milestones (audit log)

- ✅ Multi-architecture support (deb_arch variable for arm64/amd64)
- ✅ XMPP replaced with Mumble browser voice+text (mumble-web + websockify)
- ✅ Meshtastic integration (meshtasticd + built-in web UI on port 8080)
- ✅ MeshCore integration (pyMC_Repeater + web dashboard on port 8000)
- ✅ ardopcf build (build-essential + libasound2-dev, make, install to PATH)
- ✅ Headless display fixed (TigerVNC + noVNC, replaced broken Wayland + RustDesk)
- ✅ Pat and FreeDATA URLs made architecture-aware
- ✅ WiFi AP + captive portal (hostapd, dnsmasq, avahi, static IP, hostname)
- ✅ Kiwix ZIM content + systemd service (port 8888, library.xml, nginx /library/ proxy)
- ✅ Missing systemd units: kiwix-serve, direwolf, ardopcf, pat
- ✅ Dashboard backend: stdlib-only Python status API on :9000, nginx proxies /api/
- ✅ Raspberry Pi Imager repository JSON published with each release
- ✅ GitHub Actions image build workflow (RPi ARM64 + x86_64), build_mode skips raspi-config
- ✅ Fake systemctl restored in both chroot builds; enable via `file: state=link` symlinks
- ✅ JS8Call headless: openbox xstartup, dbus-run-session, autoconnect, password hint
- ✅ Bare-metal bootstrap: ghost user, git, python3-apt, /opt/mcomz, FreeDATA 404, Mercury pip, Pat .deb URL via GitHub API
- ✅ x86 build: gnupg, OverlayFS via overlayroot, build re-enabled
- ✅ Mumble HTTPS for microphone access (self-signed cert)
- ✅ Phase A: build green with ignore_errors as scaffolding
- ✅ Phase A.5: ignore_errors removed; ardopcf URL fixed; MeshCore install rewritten; Mercury removed
- ✅ Phase B: every service enable uses `file: state=link` symlink — no ignore_errors remain

### Pre-alpha.11–.13 hardware-test fixes (P0)

- ✅ Kiwix CSS/images broken — `--urlRootLocation /library`
- ✅ Pat fails to start — `mcomz_user=pi` removed; default `mcomz` used
- ✅ mumble-web WebSocket bridge — global npm path corrected; websockify TCP-only; nginx alias for static
- ✅ AP hotspot button stuck — AbortController 4s timeout
- ✅ nginx not starting on first boot — explicit multi-user.target.wants symlink
- ✅ Safari iOS refuses HTTPS — cert validity reduced to 397 days
- ✅ Kiwix `/libraryINVALID URL` — proxy_pass preserves `/library/` prefix
- ✅ Meshtastic / MeshCore 502 — open in new tab + inline offline guard
- ✅ hostapd / dnsmasq "off" badge → "(standby — activates with hotspot)" inline note
- ✅ Manage Books: MComzLibrary entries with GitHub-API URL fetch
- ✅ meshtasticd `failed` status — distinct error/standby/off badges
- ✅ direwolf/mcomz-meshcore `activating` — `ConditionPathExists=` on /dev/snd, /dev/spidev0.0

### Pre-alpha.19 hardware-test fixes

- ✅ iOS Safari HTTPS-redirect-page approach (later reverted in pre-alpha.20 — see §2)
- ✅ Kiwix ZIM reader URLs use `b.id` UUID
- ✅ Kiwix.org recommended URLs via OPDS catalog (`fetchKiwixUrl(kiwixName)`)
- ✅ Installed books filtered out of recommended list
- ✅ Mesh card before Licensed Radio
- ✅ Tooltip delay — `data-tip=` + CSS `::after`
- ✅ WiFi icon clipped — viewBox expanded
- ✅ Offline MeshCore flasher for Heltec v4 — local clone + GitHub firmware download
- ✅ Installed ZIM sizes — `os.path.getsize`
- ✅ WikiMed Mini moved to first-boot oneshot (note: catalog name still wrong — see §1.A)
- ✅ smoke-test.py: misleading detail strings + OPDS catalog check
- ✅ smoke-test.py: VNC/noVNC TCP banner check

### Pre-alpha.20 hardware-test fixes (all in §2 above pending verify)

- ✅ iOS Safari revert — full dashboard on HTTPS
- ✅ Removed global "Not using HTTPS" banner
- ✅ Pat button literal `https://`
- ✅ Kiwix viewer URL `/library/viewer#<uuid>`
- ✅ /meshcore-flash/ 403 — recursive www-data chown
- ✅ websocket-upgrade smoke test
