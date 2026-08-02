# Issue #135 — Output / Test_Validation reconcile (2026-08-02)

## Discrepancy found

| Location | quikclms | quikclmp | Notes |
|---|---:|---:|---|
| `Output/` (before promote) | **5594** | **5366** | Byte-identical to pre-#135 archive `*_pre_issue135_20260802T205039Z.csv` (marker=0) |
| `Output/Test_Validation/` | **6044** | **5497** | Intended #135 package (+ #134 PNOTE-B); marker=308 |
| Prior apply evidence | 6044 | 5497 | `issue135_production_apply_summary.json` / `issue135_134_overlay_apply_summary.json` |

Root cause: Output root was overwritten back to the pre-#135 baseline after Test_Validation was published. Evidence/reports that claimed Output was already 6044/5497 were false for the actual Output root at reconcile time. Concurrent claims validation artifacts (`claims_*`) were also left in Output root around the overwrite.

## Intended package decision (authorized)

User authorized proceed. Independent checks on Test_Validation confirmed the intended package:

- Option-3 corrected headers: **43/43**
- DERIVED_HIGH headers: **142/142** (with `[PNOTE-B]` after #134)
- NO_PACTG_HISTORY marker: **308** (0 with quikclmp payees)
- HOLD_INCOMPLETE_SOURCE: **9** absent from both tables
- Schemas match Output columns; MINTAMT nonzero = 0

Promotion of only `quikclms.csv` + `quikclmp.csv` from Test_Validation → Output was therefore safe.

## Promotion

| Item | Value |
|---|---|
| Occurred | **Yes** |
| Before Output | 5594 / 5366 |
| After Output | **6044 / 5497** |
| Test_Validation | 6044 / 5497 (kept synchronized, byte-identical) |
| Rollback archives | `QLA_Migration/Archive/quikclms_pre_issue135_reconcile_20260802T210607Z.csv`, `quikclmp_pre_issue135_reconcile_20260802T210607Z.csv` |
| Non-table `claims_*` | Moved to `QLA_Migration/Reports/*_reconcile_20260802T210607Z*` |

## Post-promote validators (actual Output root)

| Check | Result |
|---|---|
| Issue #135 production | **PASS** |
| Issue #135 MINTAMT | **PASS** (`clms_rows=6044`, `mintamt_nonzero=0`) |
| Issue #134 claim memos | **PASS** (`missing [PNOTE-B]=0`; death+B=1351) |
| Grok second-pass v58.57 | **PASS** |
| Output root non-table artifacts | **[]** |
| Accountability #135 | **IN_DATA** (validator + spot-check 6044/5497/marker 308) |
| Fleet accountability | exit non-zero — unrelated GAPs remain |

## Closure

**Not Closed.** Nine HOLDs remain documented; 459 policy resolution category remains. Issue-scoped G7 for #135 is green on actual Output after promote; do not close while holds/459 remain open work and fleet GAPs persist.
