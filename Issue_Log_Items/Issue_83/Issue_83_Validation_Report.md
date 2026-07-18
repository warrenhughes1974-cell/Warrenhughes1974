# Issue #83 - Validation Report

**Issue:** #83 - Fleet gender companion rate keys (F/M; Values=N)  
**Framework stage:** Validation  
**Status:** PASS  
**Generated:** 2026-07-17  
**Version:** v58.02

---

## 1. Validation Commands

```powershell
python QLA_Migration/_validate_issue83_gender_companion_keys.py
python QLA_Migration/_research_issue83_gender_companion_keys.py
python QLA_Migration/_validate_issue77_rate_setup.py
python -m py_compile qla_core/rate_key_setup.py qla_core/rate_pipeline.py QLA_Migration/_apply_issue83_gender_companion_keys.py QLA_Migration/_research_issue83_gender_companion_keys.py QLA_Migration/_validate_issue83_gender_companion_keys.py QLA_Migration/_print_issue83_uat_samples.py
```

---

## 2. Results

| Check | Result | Notes |
|-------|--------|-------|
| Issue #83 dedicated validator | PASS | 0 companion gaps; `221END` anchor OK; Test_Validation parity OK |
| Fleet companion audit | PASS | `issue83_gender_companion_key_gaps.csv` now has 0 rows |
| Issue #77 rate setup validator | PASS | 126 rated plans have GP/DB/CV/TV/DV keys; PVO and NA-member rules OK |
| Python syntax check | PASS | Touched Python files compile |
| Lints | PASS | No linter errors on touched validation/apply scripts |

---

## 3. Loaded Output Counts

After applying Issue #83 to current Output/rates:

| Table | Before | After | Added |
|-------|-------:|------:|------:|
| QuikPlGp | 242 | 281 | 39 |
| QuikPlDb | 128 | 209 | 81 |
| QuikPlCv | 176 | 229 | 53 |
| QuikPlTv | 266 | 279 | 13 |
| QuikPlDv | 136 | 209 | 73 |
| Total | 948 | 1207 | 259 |

`quikplan` PVO rows updated: 83 plans.

Published to:

- `QLA_Migration/Output/rates/`
- `QLA_Migration/Output/quikplan.csv`
- `QLA_Migration/Output/Test_Validation/quikplan.csv`
- `QLA_Migration/Output/Test_Validation/rates/`

---

## 4. Anchor Checks

| Plan | Family | Sex | Expected Values | Key result |
|------|--------|-----|-----------------|------------|
| 221END | QuikPlCv | F | N | Present; MORT=N1, ETIMORT=N1, NFOINT=2, INTMETHCV=0 |
| 221END | QuikPlCv | M | Y | Present; MORT=N1, ETIMORT=N1, NFOINT=2, INTMETHCV=0 |
| 221END | QuikPlTv | F | Y | Present |
| 221END | QuikPlTv | M | Y | Present |

---

## 5. Residual Notes

The Issue #80 validator was also run as a cross-check. It failed only because it is hard-coded for `APP_VERSION = v58.01` and the prior #80 Test_Validation allowlist, while Issue #83 legitimately publishes additional rate member/key tables. Its valuation value comparison still reached the expected 51 plans.

Issue #83 validation is therefore PASS.
