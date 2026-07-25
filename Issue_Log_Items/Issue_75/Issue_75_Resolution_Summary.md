# Issue #75 — Resolution Summary

**Issue:** Bank Acct / `MBANKNO` QLA validation (PPCOM recovery)  
**Status:** Closed  
**Release:** v58.35  
**Date Resolved:** 2026-07-25  
**Owner:** Warren  

---

Resolution: Bank-draft `quikmstr.MBANKNO` is rebuilt from June PPCOM routing joined by account digits, emitting only a checksum-valid 9-digit ABA and a digits-only account (source leading zeros kept). Stats: bank-draft 2132; populated QLA-safe 2081; still blank 51; invalid 0; all-policy MBANKNO populated 2706. Loaded examples: 9010161748C=091303855/0000002000581; 9010157076C=104910135/212919; 9010348734C=081518113/208787; 9010713704C=104000016/47374579. Still missing 51 (49 no PPCOM routing e.g. 9010428747C/9010451385C/9010464590C; 2 account too short 9010550564C and 9010919258C acct 238).

---

## Problem

QLAdmin rejected Bank Acct on policy edit (`Invalid routing number`) when conversion emitted truncated ABA, punctuation, or multi-slash values. After the v57.92 QLA-safe blanking fix, ~910 bank-draft policies remained blank because the May ABA lookup did not cover PPPAC accounts. June PPCOM supplies complete routing.

## Fix

1. Rebuild `aba_routing_lookup.csv` from `PPCOM_PACAccountInformation_Extract_20260630.csv` for PPACH+PPPAC accounts (unique + latest-ambiguous; checksum-valid 9-digit ABA).
2. Converter v58.35: checksum ABA helpers; preserve account leading zeros; keep ABA leading zero when part of the 9-digit routing.
3. Apply path / batch uses lookup to fill `MBANKNO` as `ABA/ACCOUNT`.

## Results

| Metric | Value |
|--------|------:|
| Bank-draft filled | 1,222 → 2,081 |
| Bank-draft blank | 910 → 51 |
| Invalid filled | 0 |
| quikmstr rows changed (MBANKNO only) | 954 |

Traces: `9010161748C` → `091303855/0000002000581`; `9010713704C` unchanged.

## Gates

| Gate | Result |
|------|--------|
| Validation | PASS (`validate_issue75_mbankno.py`) |
| Regression | PASS (MBANKNO-only diffs) |
| G7 accountability | **#75 IN_DATA**; #45 IN_DATA (`MBANKNO populated=2706`) |
| Test_Validation | `Output/Test_Validation/quikmstr.csv` |

## Rollback

- Restore prior `Source/aba_routing_lookup.csv` and pre-apply quikmstr backup under `Issue_75/evidence/quikmstr_before_issue75_v5835_*.csv`
- Revert app.py to v58.34

## Artifacts

- `Issue_75_Validation_Report.md`, `Issue_75_Regression_Report.md`
- `scripts/rebuild_aba_routing_lookup_from_ppcom.py`, `apply_issue75_ppcom_mbankno.py`
- `Reports/issue75_ppcom_mbankno_apply_audit.csv`
