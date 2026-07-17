# Issue #77 — Regression Report

**Issue:** #77 — Fleet rate setup (default keys + Plan Values Options)  
**Framework stage:** Regression Agent  
**Engine version:** **v57.95**  
**Generated:** 2026-07-17  
**Verdict:** **PASS**

---

## Scope of intentional change

| Area | Intentional? |
|------|----------------|
| `Output/rates/QuikPl*` keys + members | **Yes** |
| `quikplan` PLANVALOPT / *VARY* only | **Yes** |
| Factor grids (Gps/Dbs/Cvs/Tvs/Dvs/Nps) | **No** — must be unchanged |
| Policy tables (quikmstr, quikridr, …) | **No** |

---

## 1. Row counts — factor grids (must be stable)

Compared to Issue #77 pre-Dev fleet audit inventory:

| Table | Pre-#77 audit | Current | Match |
|-------|-------------:|--------:|:-----:|
| QuikGps | 11,983 | 11,983 | **Y** |
| QuikDbs | 2,513 | 2,513 | **Y** |
| QuikCvs | 38,047 | 38,047 | **Y** |
| QuikTvs | 53,818 | 53,818 | **Y** |
| QuikDvs | 6,452 | 6,452 | **Y** |
| QuikNps | 52,647 | 52,647 | **Y** |

---

## 2. Key / member tables — intentional growth

| Table | Pre-stub (approx) | Current | Note |
|-------|------------------:|--------:|------|
| QuikPlGp plans | 109 | 126 | stubs + coverage |
| QuikPlDb plans | 23 | 126 | stubs |
| QuikPlCv plans | 46 | 126 | stubs |
| QuikPlTv plans | 80 | 126 | stubs |
| QuikPlDv plans | 20 | 126 | stubs |
| QuikPlSt | 126 | 126 | MLOANINT filled |

---

## 3. Unrelated quikplan fields

| Field | Spot-check | Result |
|-------|------------|--------|
| LOANINTX | 141 × `A` | **Unchanged** (#70) |
| FORM / DESCR / LOANINT | Present on 1658CS / 280PUA | **OK** |
| Only PVO columns targeted by enrich | Validator / apply path | **OK** |

---

## 4. Prior fix preservation

| Check | Result |
|-------|--------|
| #25 MPOLICY 10-char (200-row sample) | **PASS** |
| #26 quikridr MPREM (0 blank / 6,936) | **PASS** |
| #71 BAND=`00` on members/keys | **PASS** (stub band still `00` when no real band) |
| #73 ISSCNTRY=`0000` on QuikPlSt | **PASS** |

---

## 5. Schema / package integrity

| Check | Result |
|-------|--------|
| Test_Validation quikplan + key/member CSVs byte-match Output | **PASS** |
| Both `app.py` = v57.95 | **PASS** |
| No Gender 0 + F/M coexistence | **PASS** |
| No invented factor cells | **PASS** |

---

## 6. Fleet impact summary

| Metric | Value |
|--------|------:|
| Plans with complete 5-family keys | 126 |
| quikplan PLANVALOPT=Y | 133 |
| Policy conversion tables touched by #77 apply | **0** |

---

## Gate G6 — Regression Pass

- [x] Factor row counts stable  
- [x] Unrelated fields OK  
- [x] #25 / #26 preserved  
- [x] Report published  
- [x] Status: **Ready for Client UAT** / Closure (Composer 2.5)

---

## Recommended next

```
Issue #77 Validation and Regression PASS.

Run Closure Agent on Composer 2.5.
Produce Issue_77_Resolution_Summary.md / Closure report per AI_Agents/Closure_Agent.md.
```

UAT reload: `QLA_Migration/Output/Test_Validation/quikplan.csv` + `Test_Validation/rates/QuikPl*.csv` (keys + members).
