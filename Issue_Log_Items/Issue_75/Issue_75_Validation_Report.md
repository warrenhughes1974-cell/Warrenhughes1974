# Issue #75 — Validation Report (REOPEN — PPCOM recovery)

**Issue:** #75 — Bank Acct / `MBANKNO` via PPCOM  
**Framework stage:** Validation Agent (G5)  
**Date:** 2026-07-25  
**Engine:** v58.35  
**Model:** Cursor Grok 4.5 (locked)  
**Verdict:** **PASS**

---

## Method

1. Rebuilt `Source/aba_routing_lookup.csv` from June PPCOM (4,562 keys; unique + latest-ambiguous; checksum-valid).
2. Converter helpers updated (checksum ABA; preserve account leading zeros).
3. Applied MBANKNO via `scripts/apply_issue75_ppcom_mbankno.py` (same helpers as converter bank cache; `MBANKNO` only).
4. Ran `scripts/validate_issue75_mbankno.py`.

Full GUI batch still recommended before client UAT reload to prove the in-batch cache path end-to-end; Output/`Test_Validation` now match the apply.

---

## Results

| Check | Result |
|-------|--------|
| Helper unit tests | **PASS** |
| `invalid_filled` | **0** |
| Bank-draft filled | 1,222 → **2,081** |
| Bank-draft blank remaining | 910 → **51** |
| Newly filled | **882** |
| Trace 9010161748C | `091303855/0000002000581` |
| Trace 9010157076C | `104910135/212919` |
| Trace 9010348734C | `081518113/208787` |
| Regression 9010713704C | `104000016/47374579` unchanged |

Published: `QLA_Migration/Output/Test_Validation/quikmstr.csv`  
Audit: `QLA_Migration/Reports/issue75_ppcom_mbankno_apply_audit.csv`

---

## Leading zeros (confirmed in emit)

- ABA values that start with `0` (e.g. `091303855`) retained.
- Account values retain source zeros (e.g. `0000002000581`, `050515635`).

---

## Next

**Stop after Validation readout** (framework). Ready for Regression → Closure when you say proceed.
