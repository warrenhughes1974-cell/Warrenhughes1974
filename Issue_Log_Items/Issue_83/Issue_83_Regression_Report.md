# Issue #83 — Regression Report

**Issue:** #83 — Fleet gender companion rate keys (F/M; Values=N)  
**Framework stage:** Regression Agent  
**Engine version:** **v58.02**  
**Baseline:** `QLA_Migration/Archive/rates` (BAND-normalized for #71) + official #83/#77 validators  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-17  
**Verdict:** **PASS**

---

## 1. Scope of Change (expected)

| Component | Expected impact |
|-----------|-----------------|
| `Output/rates/QuikPlGp/Db/Cv/Tv/Dv` | **Yes** — +259 companion F/M key rows |
| `Output/rates/QuikPlGd/Uw/Bd/St/Nb` | Members already present; no invent |
| `quikplan` PLANVALOPT / GDVARY* | **Yes** — PVO recompute (83 plans) |
| Factor grids (Gps/Dbs/Cvs/Tvs/Dvs/Nps) | **No** — must not invent / no shrink |
| Policy tables (quikmstr, quikridr, …) | **No** |

---

## 2. Commands

```powershell
python Issue_Log_Items/Issue_83/scripts/regression_issue83.py
```

Evidence: `Issue_Log_Items/Issue_83/evidence/issue83_regression_checks.csv`

---

## 3. Factor grids (no invent)

| Table | Archive | Current | No-shrink |
|-------|--------:|--------:|:---------:|
| QuikGps | 11,947 | 11,983 | **Y** |
| QuikDbs | 1,380 | 2,513 | **Y** |
| QuikCvs | 25,717 | 38,407 | **Y** |
| QuikTvs | 26,097 | 53,818 | **Y** |
| QuikDvs | 3,978 | 6,736 | **Y** |
| QuikNps | 26,650 | 52,647 | **Y** |

Apply script `_apply_issue83_gender_companion_keys.py` writes keys/members/quikplan only — **does not emit factor CSVs**.

---

## 4. Key tables — intentional growth

| Table | Archive | Current | Delta |
|-------|--------:|--------:|------:|
| QuikPlGp | 201 | 281 | +80 |
| QuikPlDb | 12 | 209 | +197 |
| QuikPlCv | 70 | 229 | +159 |
| QuikPlTv | 112 | 279 | +167 |
| QuikPlDv | 20 | 209 | +189 |

Issue #83 companion delta on pre-apply current package: **+259** (documented in Validation Report).

---

## 5. Preservation checks

| Check | Result |
|-------|--------|
| Official #83 validator | **PASS** |
| Official #77 validator | **PASS** |
| Companion gaps | **0** |
| Non-candidate F/M keys preserved (BAND-normalized) | **PASS** |
| Candidate prior F/M keys preserved | **PASS** |
| #71 BAND=`00` on F/M keys | **PASS** |
| #25 MPOLICY width (200-row sample) | **PASS** |
| #26 MPREM spot (3 policies) | **PASS** |
| Test_Validation parity | **PASS** |
| `app.py` / `QLA_Migration/app.py` = v58.02 | **PASS** |

---

## 6. Anchor

| Plan | Check | Result |
|------|-------|--------|
| `221END` QuikPlCv | F + M keys | **PASS** |
| `221END` | F Values=N (no QuikCvs F factors) | **PASS** |
| `221END` | M Values=Y | **PASS** |
| `221END` | F/M assumptions match sibling | **PASS** |

---

## Gate G6 — Regression Pass

- [x] Factor no invent / no shrink  
- [x] Unrelated policy fields OK (#25/#26)  
- [x] Non-candidate keys preserved  
- [x] Report published  
- [x] Status: **Ready for Client UAT** / Closure (Composer 2.5)

---

## Recommended next

```
Issue #83 Validation and Regression PASS.

Run Closure Agent on Composer 2.5.
Produce Issue_83_Resolution_Summary.md per AI_Agents/Closure_Agent.md.
```

UAT reload: `QLA_Migration/Output/Test_Validation/quikplan.csv` + `Test_Validation/rates/QuikPl*.csv` (keys + members).
