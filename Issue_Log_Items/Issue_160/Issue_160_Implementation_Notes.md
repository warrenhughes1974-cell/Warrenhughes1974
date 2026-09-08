# Issue #160 — Implementation Notes

**Issue:** #160 — PUA phase stays Expired (56) instead of following the base terminal status  
**Engine:** **v59.09**  
**Developed:** 2026-09-07  
**Code + Output remap applied** (scoped `MPHSTAT`-only remap of `quikridr` PUA rows)

---

## What changed

1. **Both `app.py` copies** — `_apply_pua_rider_inheritance` now has a third branch: when the base phase is any terminal status (not 44/45 and not `< 50`), the PUA row inherits the base phase's own raw `MPHSTAT`. Warren approved this carve-out against SD-60-12 (Issue #60) and approved generalizing beyond Surrendered/55 to all terminal base statuses.
2. **Current Output** — remapped `quikridr.MPHSTAT` on 239 PUA rows so they match the base phase. Every other field on every row is identical to the pre-remap snapshot.
3. **Validator** — `tools/validators/validate_issue160_pua_terminal_status.py` (fail-closed). Register in `SMOKE_JOBS` at Closure.

Rate tables, PVO, MPREM, MPOLICY, MPAR, dates, and non-PUA riders were not edited.

---

## Files touched

| File | Change |
|---|---|
| `app.py` | terminal-status else-branch + APP_VERSION v59.09 |
| `QLA_Migration/app.py` | same |
| `QLA_Migration/Output/quikridr.csv` | PUA MPHSTAT remap (239 rows) |
| `QLA_Migration/Output/Test_Validation/quikridr.csv` | published copy |
| `tools/validators/validate_issue160_pua_terminal_status.py` | new |
| `Issue_Log_Items/Issue_160/tools/apply_issue160_pua_terminal_status_remap.py` | scoped remap |
| `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv` | before snapshot |

---

## Before / after (UAT)

| Policy | PUA plan | Base MPHSTAT | Before (PUA) | After (PUA) |
|---|---|---|---|---|
| 9010521213C | 1708PA | 50 | 22 | 50 |
| 9010150910C | 221EPA | 53 | 56 | 53 |
| 9010363098C | 1960PA | 53 | 56 | 53 |
| 9010360289C | 1708PA | 55 | 56 | 55 |
| 9010360290C | 1708PA | 55 | 56 | 55 |
| 9010235370C | 280EPA | 57 | 56 | 57 |

Counts: base 50 → 1; base 53 → 163; base 55 → 71; base 57 → 4. Total PUA `MPHSTAT` deltas = **239**. Remap warnings (44/45 or `< 50` mismatches left untouched) = **0**.

Untouched regression populations: base 44/45 PUA still 54 (27 rows); base `< 50` PUA still 41 (228 rows).

---

## Not invented

No new status codes. PUA now copies the base phase's existing `MPHSTAT` for terminal bases. The #108D (44/45 → 54) and #60 (base `< 50` → 41) branches are unchanged. Non-PUA riders, base phase 1, and every non-`MPHSTAT` column were not edited.

---

## Rollback

Restore `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv` over `QLA_Migration/Output/quikridr.csv` and revert the `else` branch in both `app.py` files (leave the 44/45 and `< 50` branches as they were).

---

## Post-Development correction (independent Validation review)

Independent Validation (`Issue_160_Validation_Report.md`) flagged that the remap script wrote `quikridr.csv` with LF-only line endings (rest of `Output/` uses CRLF). Field values were unaffected (0 drift), but the file was normalized back to CRLF and `Test_Validation/quikridr.csv` re-synced. Validator re-run and reconfirmed **PASS** after the fix. Warren's approval (SD-60-12 carve-out + full scope) is now also recorded in writing as **SD-60-13** in `Issue_Log_Items/Issue_60/Issue_60_Scope_Decisions.md`.
