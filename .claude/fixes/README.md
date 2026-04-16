# Fix log

One file per fix attempt, named `YYYY-MM-DD-<short-sha>-<slug>.md`.

Purpose: record each attempted fix as a falsifiable hypothesis — what we
thought the problem was, what we changed, what we expected to see, and what
actually happened on hardware. This makes it easy to tell:

- What was tried for a given bug
- Why we picked this approach over the alternatives
- Whether the hypothesis was validated or proven wrong
- How to roll back if the fix made things worse

Entries are updated in place after hardware verification — the **Outcome**
section is filled in once test results come back, not left as a dangling TODO.

## When to create an entry

- Non-trivial bug fix whose behaviour on real hardware can't be observed in CI
- Any fix where the hypothesis is uncertain (confidence below ~90%)
- Any fix that touches multiple subsystems or has a plausible regression surface

Skip for: typo fixes, pure docs changes, dependency bumps with no behaviour change.

## Template

```markdown
# <Title> — `<short-sha>`

**Date:** YYYY-MM-DD
**Commit:** `<sha>` — `<commit subject>`
**Files changed:** `path/a`, `path/b`
**Related:** hardware test pre-alpha.N, todo.md item, previous attempt <sha>
**Status:** shipped / verified / failed / superseded

---

## Problem

What was observed. Quote verbatim user/test feedback where possible.
Severity — does it block a user journey, or is it cosmetic?

## Reproduction

Exact steps to hit the bug before the fix.

## Hypothesis (root cause)

What we think is actually wrong, stated so it can be proven false.

## Alternatives considered

- Option A — rejected because …
- Option B — rejected because …

## Fix

What changed and how it is supposed to address the hypothesis.
Reference `file:line` where useful.

## Expected outcome

- On success we expect to see: …
- If we instead see X, the real cause is probably Y.

## Confidence

High / Medium / Low — and a sentence explaining what would invalidate it.

## Risks / failure modes

- Regression surface: what else could this break?
- Conditions under which the fix silently degrades
- External dependencies that could change and break it later

## Test plan

Preconditions, steps, explicit pass/fail criteria. Include regression checks
for anything the fix touches indirectly.

## Rollback

How to revert if the fix turns out to be wrong or causes a new regression.
Usually `git revert <sha>`; note anything extra (cache wipes, data migrations).

## Outcome

*(Filled in after hardware verification.)*

- Verified on: release tag, date, hardware
- Result: worked / partially worked / did not work
- What actually happened:
- Follow-up:
```
```
```
