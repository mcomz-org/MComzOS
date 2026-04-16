# Fix RECOMMENDED_ZIMS catalog names — `XXXXXXX`

**Date:** 2026-04-16
**Commit:** `XXXXXXX` — `fix(dashboard,site): correct Kiwix ZIM catalog names in RECOMMENDED_ZIMS and first-boot script`
**Files changed:** `site.yml`, `src/dashboard/index.html`, `tests/smoke-test.py`, `tests/html-check.py`
**Related:** todo.md §1.A, hardware test pre-alpha.20
**Status:** shipped

---

## Problem

Three `kiwixName` values in `RECOMMENDED_ZIMS` (dashboard) and the first-boot WikiMed install script (site.yml) referenced ZIM names that do not exist in the live Kiwix catalog (`library.kiwix.org/catalog/v2/entries`):

| Name in code | Real status |
|---|---|
| `wikipedia_en_medicine_mini` (site.yml first-boot) | Does not exist |
| `wikimed_en_all_mini` (dashboard) | Does not exist |
| `wikipedia_en_all_mini` (dashboard) | Does not exist |

Result: first-boot WikiMed install silently fails (catalog query returns no entries), and the Manage Books panel shows "Not found in Kiwix catalog" for two of the four Kiwix-sourced recommended titles.

## Reproduction

1. Boot a fresh image, wait for first-boot oneshot to run.
2. SSH in: `systemctl status mcomz-firstboot` — exits 1 due to `sys.exit(1)` on empty catalog response.
3. Open Manage Books panel → WikiMed and Wikipedia (mini) rows show "Not found in Kiwix catalog".

## Hypothesis (root cause)

Kiwix reorganised their catalog names. The "mini" variants never existed; `wikimed_en_all_mini` was a guess at naming, and `wikipedia_en_all_mini` was similarly invented. The correct names were verified live against the catalog API on 2026-04-16.

## Alternatives considered

- Keep `wikipedia_en_all` (full English Wikipedia) — 118 GB, not a reasonable recommendation.
- Drop the Wikipedia recommendation entirely — less useful for offline reference.
- Use `wikipedia_en_top` (~315 MB) — best-of subset, practical size, confirmed to exist.

## Fix

1. `site.yml:1069` — query string `name=wikipedia_en_medicine_mini` → `name=wikipedia_en_medicine`
2. `src/dashboard/index.html` RECOMMENDED_ZIMS:
   - `wikimed_en_all_mini` → `wikipedia_en_medicine`, title updated to drop "(mini, ...)".
   - `wikipedia_en_all_mini` / "Wikipedia English (mini, ~900 MB)" → `wikipedia_en_top` / "Best of Wikipedia (~315 MB)".
3. `tests/smoke-test.py` — new Section 11 checks each `kiwixName` against the live catalog API; wraps in try/except so it warns rather than failing on an offline LAN.
4. `tests/html-check.py` — regression guard asserting none of the three obsolete names appear in the source.

## Expected outcome

- First-boot oneshot exits 0 and downloads `wikimed-mini.zim` from the correct OPDS entry.
- Manage Books panel shows all four Kiwix community titles with resolvable download URLs.
- `python3 tests/html-check.py` passes (regression guard).
- `python3 tests/smoke-test.py <host>` (with internet) reports all four names as resolved.

## Confidence

High — catalog names verified directly via `curl https://library.kiwix.org/catalog/v2/entries?name=...` on 2026-04-16. Could break if Kiwix renames their catalog again, but the smoke-test will catch that.

## Risks / failure modes

- `wikipedia_en_top` is a curated subset; its content may differ from user expectations of "Wikipedia". Label makes this clear ("Best of Wikipedia").
- First-boot download still depends on internet connectivity at first boot (unchanged assumption).

## Test plan

1. Flash next image (v0.0.2-pre-alpha.21 or later).
2. Watch first-boot oneshot: `journalctl -u mcomz-firstboot -f` — should download and log "Downloaded ... wikimed-mini.zim".
3. Open Manage Books panel — all four Kiwix rows should show a download URL (not "Not found in Kiwix catalog").
4. Run `python3 tests/smoke-test.py mcomz.local` from a laptop with internet — Section 11 should show four ✅.

## Rollback

`git revert <sha>` — no data migration needed. ZIM already downloaded by first-boot is unaffected.

## Outcome

*(Filled in after hardware verification.)*

- Verified on:
- Result:
- What actually happened:
- Follow-up:
