# Issue #80 — Regression Report

**Issue:** #80 — CSO Valuation Setup → QuikPlCv / QuikPlTv / quikplan assumptions  
**Framework stage:** Regression Agent (Cursor Grok 4.5)  
**Engine version:** **v58.01**  
**Generated:** 2026-07-17  
**Verdict:** **PASS**

---

## Scope of intentional change

| Area | Intentional? |
|------|----------------|
| `Output/rates/QuikPlCv.csv` assumption columns (51 IN_SCOPE; 48 with keys) | **Yes** |
| `Output/rates/QuikPlTv.csv` assumption columns | **Yes** |
| `quikplan` NFOINT / INTMETHCV for 51 plans | **Yes** |
| Factor grids (Gps/Dbs/Cvs/Tvs/Dvs/Nps) | **No** — must not shrink / no invented cells |
| Policy tables (quikmstr, quikridr, …) | **No** |
| PUA plans (#81/#82) | **No** — out of scope |
| Citizens / CFIC folders | **No** |

---

## Commands run

```powershell
python QLA_Migration/_validate_issue80_valuation_setup.py
python Issue_Log_Items/Issue_80/scripts/regression_issue80.py
```

Evidence: `evidence/issue80_regression_checks.csv` (27 checks, 0 FAIL).

---

## 1. Candidate plans — exact authority match

| Metric | Value |
|--------|------:|
| IN_SCOPE plans | 51 |
| Rate-key plans | 48 |
| Quikplan-only (`10L171`, `10L172`, `117JPO`) | 3 |
| Exact cell comparisons | **1,248** |
| Mismatches | **0** |

Anchors verified: `1960PO`, `1658C1`, `17CSI3`, `1L1095`, `221END`, `1668SP`.

---

## 2. Non-candidates — quikplan target fields

Baseline: `QLA_Migration/Archive/quikplan_pre_issue80_moved_from_output.csv`

| Check | Result |
|-------|--------|
| Non-candidate plans | 90 |
| NFOINT / INTMETHCV drift | **0** |
| Intentional candidate updates from archive | 36 cells |

**Informational (not #80):** 4 non-candidates show unrelated `FORM` `NA`→blank (`943CWP`, `9CTRWP`, `9FTRWP`, `9STRWP`). Issue #80 does not write `FORM`; attribution unsupported.

---

## 3. Rate keys / invent rules

| Check | Result |
|-------|--------|
| No QuikPlCv/Tv keys for `10L171` / `10L172` / `117JPO` | **PASS** |
| PUA plans in `CSO_Valuation_Setup.csv` | **0** (isolated) |
| Blank authority → blank emit | **PASS** (validator) |

---

## 4. Factor grids

Compared to `QLA_Migration/Archive/rates/` (older snapshot). Current emit is larger or equal on all six factor tables — **no shrink**. #80 does not invent factor cells (assumption columns on keys only).

| Table | Archive | Current |
|-------|--------:|--------:|
| QuikGps | 11,947 | 11,983 |
| QuikDbs | 1,380 | 2,513 |
| QuikCvs | 25,717 | 38,407 |
| QuikTvs | 26,097 | 53,818 |
| QuikDvs | 3,978 | 6,736 |
| QuikNps | 26,650 | 52,647 |

---

## 5. Prior fix preservation

| Check | Result |
|-------|--------|
| #25 MPOLICY 10-char (200-row sample) | **PASS** |
| #26 MPREM spot (`010310404C`, `010331768C`, `010367131C`) | **PASS** |
| Official #80 validator (schema, package, PUA) | **PASS** |

---

## 6. Package / version integrity

| Check | Result |
|-------|--------|
| Test_Validation = only 3 CSVs + manifest | **PASS** |
| Byte parity Output ↔ Test_Validation | **PASS** |
| Both `app.py` = **v58.01** | **PASS** |
| Citizens / CFIC | Untracked local trees; not in #80 touch list |

---

## Residual limitations

1. No full pre-#80 QuikPlCv/Tv baseline after #77 emit — non-candidate rate-key assumption immutability proven for **quikplan** targets vs archive; rate-key non-candidates rely on authority isolation + validator (PUA not in authority file).
2. Unrelated `FORM` blanking on 4 rider plans noted above — outside #80.

---

## Gate G6 — Regression Pass

- [x] Candidates match Valuation_Setup coded expected  
- [x] Non-candidate quikplan NFOINT/INTMETHCV unchanged  
- [x] No invented keys for quikplan-only plans  
- [x] PUA isolation  
- [x] Factor grids not shrunk  
- [x] #25 / #26 preserved  
- [x] Test_Validation package clean  
- [x] Report published  
- [x] Status: **Ready for Closure** (Composer 2.5)

---

## Recommended next

```
Issue #80 Validation and Regression PASS.

Run Closure Agent on Composer 2.5.
Produce Issue_80_Resolution_Summary.md / Closure report per AI_Agents/Closure_Agent.md.
```

UAT reload: `QLA_Migration/Output/Test_Validation/quikplan.csv` + `rates/QuikPlCv.csv` + `rates/QuikPlTv.csv`.
