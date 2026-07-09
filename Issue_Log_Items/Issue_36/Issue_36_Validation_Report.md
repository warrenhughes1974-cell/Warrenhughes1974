# Issue #36 — Validation Report

**Issue:** #36 — Modal Premium factors at policy level (`quikmstr`)  
**Framework stage:** Validation Agent (G5)  
**Engine version:** v57.62  
**Validation script:** `tools/validators/validate_issue36_quikmstr_modal_factors.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** N/A (fleet was 100% blank pre-fix; post-enrichment Output used)  
**Generated:** 2026-07-09  
**Verdict:** **PASS**

---

## Commands Run

```bat
python tools\validators\validate_issue36_quikmstr_modal_factors.py
python tools\validators\validate_issue21j_modal_factors.py
python tools\validators\validate_mpolicy_width.py
python Issue_Log_Items\Issue_36\scripts\_g5_supplemental_checks.py
```

`validate_issue26_mprem.py` skipped source-alignment (dated extract filenames missing in Source/) — MPREM / MMODEPREM blank-rate spot-check used instead (0 blanks).

---

## 1. Trace Policy Results

| Policy | Field(s) | Expected | Actual | Result |
|--------|----------|----------|--------|--------|
| 010148856C | MSEMI/MQTRL/MMTHD/MMTHB | 51.0140 / 26.0010 / 8.9964 / 8.9989 | match | **PASS** |
| 010713704C | MSEMI/MQTRL/MMTHD/MMTHB | 52.5000 / 27.0000 / 9.1999 / 8.8018 | match | **PASS** |
| 010560185C | PAC Q MQTRL + others | MQTRL=**25.0000**; S=52; D=9; B=8.3333 | match | **PASS** |
| 010442216C | PAC S MSEMI + others | MSEMI=**50.0000**; Q=26.5; D=9; B=8.3333 | match | **PASS** |
| 010148856C | vs quikplan 221END | all four equal plan SEMI/QTRL/MTHD/MTHB | True×4 | **PASS** |
| 010148856C | MMODEPREM | 19.23 (unchanged) | 19.23 | **PASS** |

### Client workbook PAC samples (all)

| Policy | Mode | Special | MSEMI | MQTRL | Result |
|--------|------|---------|-------|-------|--------|
| 010560185C | 03 | PAC Q | 52.0000 | **25.0000** | PASS |
| 010396186C | 03 | PAC Q | 52.0000 | **25.0000** | PASS |
| 010459011C | 03 | PAC Q | 52.0000 | **25.0000** | PASS |
| 010442216C | 06 | PAC S | **50.0000** | 26.5000 | PASS |
| 010473868C | 06 | PAC S | **50.0000** | 26.5000 | PASS |
| 010449334C | 06 | PAC S | **50.0000** | 26.5000 | PASS |
| 010488273C | 06 | PAC S | **50.0000** | 26.5000 | PASS |

---

## 2. Acceptance Criteria (from Risk checklist)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | ≥99.9% policies non-blank MSEMI/MQTRL/MMTHD/MMTHB | **PASS** — 100% (5083/5083) |
| 2 | Trace policies match proposed factors | **PASS** |
| 3 | PAC special mode 1 (Q): MQTRL=25.0000 | **PASS** — 4 policies |
| 4 | PAC special mode 2 (S): MSEMI=50.0000 | **PASS** — 8 policies |
| 5 | Client workbook samples correct | **PASS** — 7/7 |
| 6 | Where plan MTHD≠MTHB, mstr not collapsed | **PASS** — 0 collapsed of 3443 |
| 7 | MMODEPREM non-blank / preserved | **PASS** — 0 blank |
| 8 | quikplan factors unchanged (#21J) | **PASS** — 21J validator |
| 9 | quikmstr row count stable | **PASS** — 5083 |
| 10 | #25 MPOLICY width = 10 | **PASS** |
| 11 | #26 MPREM non-blank on quikridr | **PASS** — 0 blank of 6934 |

---

## 3. Source Alignment

| Check | Result |
|-------|--------|
| Phase-1 MPLAN → quikplan factors → quikmstr | **PASS** (fleet + 010148856C exact match) |
| Mapping fallback used | **No** (`used_mapping_fallback=0` at apply time) |
| Orphan / missing plan | **0** |
| PAC overrides after plan copy | **PASS** (Q/S win over 26.5 / 52.0) |

---

## 4. Untouched Fields Confirmed

| Field / table | Check | Result |
|---------------|-------|--------|
| quikmstr.MMODEPREM | blank count + trace values | **PASS** |
| quikridr.MPREM | blank count 0/6934 | **PASS** |
| quikplan SEMI/QTRL/MTHD/MTHB | #21J validator | **PASS** |
| MPOLICY width (#25) | exactly 10 | **PASS** |
| quikmstr / quikridr / quikplan row counts | 5083 / 6934 / 141 | **PASS** (no row invent/drop) |

---

## 5. Row Counts

| Table | Count | Notes |
|-------|------:|-------|
| quikmstr | 5,083 | Factor columns only enriched |
| quikridr | 6,934 | Untouched |
| quikplan | 141 | Untouched (read source) |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| Policies with factors populated | 5,083 |
| PAC quarterly overrides | 4 |
| PAC semiannual overrides | 8 |
| MMTHD≠MMTHB policies verified distinct | 3,443 |
| Engine version both apps | v57.62 |

---

## 7. Failures

None.

---

## 8. Recommendation

- [x] Advance to **Regression Agent**
- [ ] Return to Development — N/A

---

## Gate G5 checklist

- [x] All trace policies pass
- [x] Validation script exits 0
- [x] Untouched fields confirmed
- [x] Validation report published
- [x] Status: **Ready for Regression**

**G5 status:** **PASS**

---

## Appendix — Validator stdout (Issue #36)

```
MSEMI: non-blank 5083/5083 (100.0%)
MQTRL: non-blank 5083/5083 (100.0%)
MMTHD: non-blank 5083/5083 (100.0%)
MMTHB: non-blank 5083/5083 (100.0%)
PAC special modes: quarterly=4 semiannual=8
MMTHD!=MMTHB plan policies checked: 3443, collapsed: 0
MMODEPREM blank: 0/5083
PASS — Issue #36 quikmstr modal factors
```
