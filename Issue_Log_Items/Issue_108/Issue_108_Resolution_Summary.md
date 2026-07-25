# Issue #108 — Resolution Summary (Closure)

**Date:** 2026-07-25
**Releases:** v58.32 (108A–108D), v58.33 (108F + Issue #72 downgrade)
**Closed tracks:** 108A, 108B, 108C, 108D, 108F
**Still open (client log):** 108E (client/SME), 108H (client decision)  
**Internal only (not CSO log):** 108G — see `Issue_108G_Internal_Track.md`

## What was wrong

Robert's ETI/RPU specification (`QLAdmin_ETI_RPU.docx`) describes what QLAdmin does when a
policy is placed into Extended Term or Reduced Paid-Up. Comparing the conversion output
against it found five defects on the 400 ETI/RPU policies, plus one that affected the whole
book.

## What changed

| Track | Fix | Release |
|---|---|---|
| 108A | Phase-1 `MSAVEAGE/MSAVEUNIT/MSAVEVPU/MSAVEPREM/MSAVESTAT` left blank on NFO policies instead of mirroring the post-NFO values | v58.32 |
| 108B | Phase-1 `MAGE` set to attained age at the paid-to date; `MLASTANN` measured to the NFO anniversary against the batch valuation date | v58.32 |
| 108C | Phase-1 `MPREM` zeroed on ETI (RPU intentionally untouched) | v58.32 |
| 108D | PUA riders on ETI/RPU policies terminate at `MPHSTAT` 54 instead of inheriting Issue #60's 41 | v58.32 |
| 108F | `MNFOPT` enrichment repointed at the source `POLICY_NUMBER` after the Issue #2 key change stranded the crosswalk lookup | v58.33 |

108F also downgraded Issue #72: `MNFOPT` is no longer forced from `MSTATUS`. Disagreements
are reported to `QLA_Migration/Reports/nfo_election_status_mismatch.csv` for source review,
which is what Robert asked for.

## Evidence

| Track | Result |
|---|---|
| 108A | All five `MSAVE*` fields blank on 400/400 NFO phase-1 rows; non-NFO mirror preserved |
| 108B | `MAGE` corrected on 400/400; `MLASTANN` corrected on 312; `MPHDOB` moved on 0 |
| 108C | ETI phase-1 rows with non-zero `MPREM`: 0 of 206; RPU `MPREM` moved on 0 of 194 |
| 108D | 27 PUA rows on NFO bases now 54; 467 non-NFO PUA rows unchanged |
| 108F | 3,946 elections recovered; all six Issue #57 client traces carry their specified value; no other quikmstr column moved |

## G7 gate

| Requirement | Status |
|---|---|
| Issue validator PASS on full `QLA_Migration/Output/` | PASS — #57, #60, #72, #76 |
| Accountability `IN_DATA` | IN_DATA — #57, #60, #72, #76 |
| Affected tables published to `Output/Test_Validation/` | `quikmstr.csv`, `quikridr.csv` |

The four validators had to be brought current first — they encoded behaviour these fixes
deliberately supersede. That work is Issue #112; see `Issue_Log_Items/Issue_112/`.

Validator run against the closing package (`QLA_VALUATION_DATE=20251231`):

```text
validate_issue76_eti_rpu_payup v2.0   candidates=400 payup_fail=0 mlast_fail=0        PASS
validate_issue72_mnfopt_status v2.0   disagreements emitted=277 reported=277          PASS
validate_issue60_pua_phase 2.0        PUA=494 (NFO-terminated 27) hard drift=0        PASS
validate_issue57_mnfopt v1.1          6/6 client traces correct                       PASS
```

## Carried forward

- **108E** — 82 in-force rider rows on NFO policies, 77 of them the 1SALML zero-unit base
  structure. No rule until Robert confirms the source is legitimate.
- **108G** — cross-table status governance checks. Partially delivered: the Issue #72
  downgrade means Robert's check 4 fires for the first time.
- **108H** — 277 election/status disagreements are now visible rather than overwritten.
  166 have no source election at all. Client decides whether blank is acceptable.
- Cash values and reserves move on the 400 NFO policies as a direct result of 108B. Send
  Robert the before/after before any UAT reload.

## Related

- `Issue_108_Validation_Report.md` — full field-level results
- `Issue_108_Implementation_Notes.md` — code changes and sequencing
- `Issue_108_Robert_Reply_Draft.md` — open questions
