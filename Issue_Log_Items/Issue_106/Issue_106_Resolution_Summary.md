# Issue #106 — Resolution Summary

**Issue:** #106 — RV Rates Off by One Duration (QuikTvs)  
**Framework stage:** Closure Agent  
**Final status:** **Closed**  
**Engine version:** v58.31  
**Closed date:** 2026-07-24  
**Owner:** Conversion

---

## Resolution (issue log — paste-ready)

**Resolution:** QuikTvs RV factors now use the same duration year as LifePRO (Dur N to Dur N) instead of shifting one year early.

---

## Brief for issue log

```text
Resolution: QuikTvs RV factors now use the same duration year as LifePRO (Dur N to Dur N) instead of shifting one year early.
```

---

## Problem Statement

Eric reported RV rates off by one duration on 670 GL85-8 / GL85-M / GL858, 659 CEN II, 621 END85, and 960 OL (LifePRO Dur 1 vs QLAdmin Dur 0). Separate question on `1L1095` vs L10 LP9595 was split to #107.

---

## Root Cause

**Category:** Mapping error (duration indexing)

Non-CV families used `source_duration − 1`. After CV-only remaps (#37/#41/#98), RV still shifted LifePRO Dur N into QuikTvs Dur N−1.

---

## Resolution

RV (`TYPE_CODE=RV` → QuikTvs) now uses identity duration via `duration_to_ql_for_type`. NP/DV/DB/PR and CV paths unchanged. Rates re-emitted; proofs validated on full Output.

### Files changed

| File | Change |
|------|--------|
| `qla_core/rate_dbf_schema.py` | `rv_source_duration_to_ql`, `duration_to_ql_for_type` |
| `qla_core/rate_factor_loader.py` | RV route |
| `qla_core/rate_inheritance_loader.py` | RV route |
| `qla_core/pdage_missfill.py` | RV route |
| `qla_core/shared_rate_candidate_loader.py` | RV route |
| `app.py` / `QLA_Migration/app.py` | v58.31 |
| `tools/validators/validate_issue_log_accountability.py` | #106 IN_DATA anchors |

---

## Evidence

| Artifact | Path / result |
|----------|----------------|
| Validation | `Issue_106_Validation_Report.md` — **PASS** |
| Regression | `Issue_106_Regression_Report.md` — **PASS** |
| Validator | `validate_issue106_quiktvs_duration.py` — **PASS** on full `Output/rates/QuikTvs.csv` |
| Accountability | `#106` **IN_DATA** (170858 M/17 Dur2=8.76 Dur83=1000; 1659C2 M/17 SM Dur1=1 Dur83=978) |
| Test_Validation | `Output/Test_Validation/rates/QuikTvs.csv` |

---

## Trace confirmation

| Plan | Expected | Emitted | Match |
|------|----------|---------|-------|
| 170858 M/17 | Dur2=8.76, Dur83=1000 | same | Yes |
| 17085M / 170588 M/17 | same | same | Yes |
| 1659C2 M/17 SM | Dur1=1, Dur83=978 | same | Yes |
| 221END / 1960OL M/17 | Dur1 aligned | same | Yes |

---

## Explicitly Not Changed

- CV first-duration / FNZ remap (#37/#41/#98)
- NP/DV/DB/PR `source − 1`
- `1L1095` source segment (still L10 LP95) → **#107**

---

## Follow-ups

| ID | Item | Status |
|----|------|--------|
| **#107** | `1L1095` RV vs L10 LP9595 source | Open — DG BLOCKED |

---

## Rollback

Revert v58.31 duration helpers; re-emit QuikTvs from prior `source − 1` behavior; reload prior QuikTvs if needed.

---

## Network / Output note

`QLA_Migration/Output/` is gitignored. After pull: run **GENERATE RATE TABLES** (or rate loader emit) so network QuikTvs matches v58.31. Partial UAT: `Test_Validation/rates/QuikTvs.csv`.

---

## Git

| Item | Value |
|------|-------|
| Commit | `d6919ae` |
| Branch | `issue-34-pr7-quikisrr` |
| Message | Close Issue #106: QuikTvs RV duration identity (v58.31). |
