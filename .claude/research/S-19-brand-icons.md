# S-19 Brand Icons — Research Notes
_Researched 2026-04-19_

## Summary verdict

Five of six projects are clean. Meshtastic is a registered trademark with a published policy — the safe path is the **M-PWRD logo** (no permission or notification required). The main Meshtastic wordmark/logo requires a 7-day notification email. Recommendation: use M-PWRD for Meshtastic, standard logos for the rest.

---

## Per-project findings

### JS8Call
- **Logo:** `artwork/installer_logo.svg` in https://github.com/js8call/js8call
- **License:** GPLv3 covers entire project including assets
- **Dashboard use:** ✅ Permitted — GPLv3 allows display/reproduction with attribution
- **Gotchas:** None

### Pat (Winlink)
- **Logo:** `web/src/static/pat_logo.png` in https://github.com/la5nta/pat
- **License:** MIT — fully permissive
- **Dashboard use:** ✅ Permitted
- **Gotchas:** None

### Meshtastic
- **Main logo:** `static/img/logo.svg` — registered trademark ® of Meshtastic LLC
- **M-PWRD logo:** https://github.com/meshtastic/design/tree/master/Meshtastic%20Powered%20Logo (SVG + PNG variants, "M-Powered" and "M-PWRD")
- **Policy:** https://meshtastic.org/docs/legal/licensing-and-trademark/

**Use the M-PWRD logo** — explicitly designed for projects powered by Meshtastic; no trademark grant or notification required.

If the main logo is preferred instead, community/non-commercial use is permitted with:
1. Hyperlink logo to `https://meshtastic.org`
2. Display on same page: *"This site is not affiliated with or endorsed by the Meshtastic project"*
3. Use ® symbol on first instance
4. Email `trademark@meshtastic.org` within 7 days of deployment

**Forbidden for any logo:** using "Meshtastic" in domain names, as primary/secondary product branding, or modifying the mark.

**Required attribution statement** (if main logo used):
> "Meshtastic® is a registered trademark of Meshtastic LLC. Meshtastic software components are released under various licenses, see GitHub for details. No warranty is provided — use at your own risk."

### MeshCore
- **Logo:** `logo/meshcore.svg` in https://github.com/liamcottle/meshcore (MIT project; `_tm` variant filename suggests trademark awareness but no formal policy found)
- **Dashboard use:** ✅ Likely fine for nominative use — no formal trademark filing or policy found as of 2026-04-19
- **Gotchas:** Consider adding a note to README that MeshCore is used nominatively; ping the repo if uncertain

### Mumble
- **Logo:** `icons/mumble.svg` in https://github.com/mumble-voip/mumble
- **License:** BSD 3-Clause project-wide
- **Dashboard use:** ✅ Permitted
- **Gotchas:** `license@mumble.info` available for questions; no brand policy page found

### FreeDATA
- **Logo:** `freedata_gui/src/assets/logo.png` in https://github.com/DJ2LS/FreeDATA
- **License:** GPLv3
- **Dashboard use:** ✅ Permitted
- **Gotchas:** None

---

## Implementation recommendation

1. **Use M-PWRD** for Meshtastic (no approval required). Download from the design repo.
2. Download all other logos at 32×32 or 24×24 SVG where available, PNG fallback.
3. Store in `src/dashboard/icons/` with a `LICENSES.md` noting each source + license.
4. Add to `README.md`: *"Logos and trademarks are property of their respective owners and are used nominatively for identification purposes. Meshtastic® is a registered trademark of Meshtastic LLC; the M-PWRD logo is used per Meshtastic's community logo policy."*
5. For Meshtastic main logo (if M-PWRD is rejected on aesthetic grounds): email `trademark@meshtastic.org` within 7 days of first public release that includes it.

---

## Verdict table

| Project | Use | Action needed |
|---------|-----|---------------|
| JS8Call | ✅ Main logo | None |
| Pat | ✅ Main logo | None |
| Meshtastic | ✅ M-PWRD logo | None — if main logo used instead, email within 7 days |
| MeshCore | ✅ Main logo | None (no formal policy) |
| Mumble | ✅ Main logo | None |
| FreeDATA | ✅ Main logo | None |
