# Issue #77 — Validation Report

**Issue:** #77 — Fleet rate setup (default keys + Plan Values Options)  
**Framework stage:** Validation Agent  
**Engine version:** **v57.95**  
**Validation script:** `QLA_Migration/_validate_issue77_rate_setup.py`  
**Extras:** `QLA_Migration/_research_issue77_validation_extras.py`  
**Output directory:** `QLA_Migration/Output/`  
**Before snapshot:** N/A (fleet setup; factor counts compared to pre-#77 audit baseline)  
**Generated:** 2026-07-17  
**Verdict:** **PASS**

---

## Commands Run

```bash
python QLA_Migration/_validate_issue77_rate_setup.py
python QLA_Migration/_research_issue77_validation_extras.py
```

Both exited **0**.

---

## 1. Trace plan results

| Plan | Check | Expected | Actual | Result |
|------|-------|----------|--------|--------|
| 1658CS | QuikPlDb + QuikPlDv keys | ≥1 each (stub OK) | Db=1, Dv=1 | **PASS** |
| 1658CS | Gender members | F/M only (no 0) | F, M | **PASS** |
| 1658CS | Factor Gps/Cvs/Tvs | Unchanged presence | 246 / 1015 / 1016; Dbs/Dvs=0 | **PASS** |
| 1658CS | STVARYGP / BDVARYDB / PLANVALOPT | Y / Y / Y | Y / Y / Y | **PASS** |
| 280PUA | Gender members | F/M only (no 0) | F, M | **PASS** |
| 280PUA | DB stub uses real gender | Not Gender 0 | QuikPlDb GENDER=F | **PASS** |
| 910RWP | TV factors present | Has QuikTvs | 618 factor rows; 7 keys | **PASS** |

---

## 2. Acceptance criteria (Risk checklist + #77 follow-up)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | All 126 rated plans have GP/DB/CV/TV/DV keys | **PASS** (0 missing) |
| 2 | PLANVALOPT ∈ {Y,N} only | **PASS** (133 Y, 8 N; no `F`) |
| 3 | STVARYGP=Y for rated/PVO plans | **PASS** (133) |
| 4 | BDVARY* = Y for rated plans in quikplan | **PASS** (validator) |
| 5 | QuikPlSt.MLOANINT populated | **PASS** (0 blank / 126) |
| 6 | No Gender 0 beside F/M; no UW 00 beside real UW | **PASS** |
| 7 | Factor grids not invented | **PASS** (counts match pre-stub baseline) |
| 8 | Test_Validation published / byte-match | **PASS** |
| 9 | APP_VERSION both app.py = v57.95 | **PASS** |

---

## 3. Factor vs key integrity

| Table | Rows | Plans |
|-------|-----:|------:|
| QuikGps | 11,983 | 109 |
| QuikDbs | 2,513 | 23 |
| QuikCvs | 38,047 | 46 |
| QuikTvs | 53,818 | 80 |
| QuikDvs | 6,452 | 20 |
| QuikNps | 52,647 | 76 |
| QuikPlGp | 242 | **126** |
| QuikPlDb | 128 | **126** |
| QuikPlCv | 174 | **126** |
| QuikPlTv | 266 | **126** |
| QuikPlDv | 135 | **126** |

Factor row counts match the Issue #77 pre-change fleet audit (no factor invent). Key plan coverage = 126 for all five families.

---

## 4. Untouched fields / policy smoke

| Check | Result |
|-------|--------|
| quikmstr / quikridr not modified by #77 apply | **PASS** (issue scope = rates + quikplan PVO) |
| #25 MPOLICY width (sample 200) | **PASS** (all length 10) |
| #26 MPREM blank rate on quikridr | **PASS** (0 blank / 6,936) |
| quikplan LOANINTX (non-PVO) | **PASS** (still fleet `A` = 141) |

---

## 5. Impact summary

| Metric | Value |
|--------|------:|
| Rated plans with complete family keys | 126 |
| quikplan PLANVALOPT=Y | 133 |
| Factor value rows changed | **0** |
| NA members pruned (v57.95) | 192 (apply log) |

---

## 6. Failures

None.

---

## Gate G5 — Validation Pass

- [x] Trace plans pass  
- [x] Validator exit 0  
- [x] Untouched / #25/#26 smoke OK  
- [x] Report published  
- [x] Status: **Ready for Regression**
