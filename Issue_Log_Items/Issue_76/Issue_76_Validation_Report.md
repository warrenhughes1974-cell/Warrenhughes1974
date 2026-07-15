# Issue #76 — Validation Report

**Issue:** #76 — ETI/RPU phase-1 pay-up + duration for Policy Display cash values  
**Framework stage:** Validation Agent  
**Engine version:** v57.93  
**Validation script:** `tools/validators/validate_issue76_eti_rpu_payup.py`  
**Output directory:** `QLA_Migration/Output/`  
**Generated:** 2026-07-15  
**Model:** Cursor Grok 4.5 (locked)  
**Verdict:** **PASS**

---

## Commands Run

```bash
python tools/validators/validate_issue76_eti_rpu_payup.py
python tools/validators/validate_mpolicy_width.py
```

Supplemental read-only checks: non-candidate gate, #60 PUA phase>1, #72 sample, Test_Validation publish.

**Primary validator:** exit **0 / PASS**  
**MPOLICY (#25):** exit **0 / PASS**

---

## 1. Trace Policy Results

| Policy | Phase | MSTATUS | MPAIDTO | MPAYUP | MLASTANN | Expected | Result |
|--------|------:|---------|---------|--------|----------|----------|--------|
| **010407670C** | 1 | 45 | 20121001 | **20121001** | **14** | 14 (2026−2012) | **PASS** |
| **010407670C** | 2 | 45 | — | **19720201** (=MEFFDATE) | 54 | #60 PUA unchanged | **PASS** |
| 010374099C | 1 | 44 | 20090921 | **20090921** | **17** | 17 | **PASS** |
| 010149295C | 1 | 44 | 19921201 | 19921201 | **34** | 34 | **PASS** |
| **010367131C** | 1 | 22 | 20260801 | 20520801 (unchanged) | 56 | not ETI/RPU | **PASS** |

Detail: `evidence/issue76_validation_summary.csv` (400 candidate rows, all PAYUP_OK / MLAST_OK)

---

## 2. Acceptance Criteria (Risk checklist §10)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `010407670C` phase 1: MPAYUP=20121001, MLASTANN=14 | **PASS** |
| 2 | `010407670C` phase 2 `1708PA`: MPAYUP=MEFFDATE (19720201) | **PASS** |
| 3 | All 400 phase-1 @44/45: MPAYUP=MPAIDTO, MLASTANN=sys_year−payup_year | **PASS** (0 violations) |
| 4 | Non-44/45 phase-1 not wrongly overridden | **PASS** (0 false positives) |
| 5 | #72 sample: 010407670C MSTATUS=45 MNFOPT=3 | **PASS** |
| 6 | MPOLICY width (#25) | **PASS** |
| 7 | quikridr row count stable | **PASS** (6,934) |
| 8 | `Test_Validation/quikridr.csv` published | **PASS** (matches Output) |
| 9 | Rebatch log: Issue #76 adjusted 400 policies | **PASS** |

**Out of scope (not #76 regression):** `validate_issue72_mnfopt_status.py` NFO>0 life-with-CV fleet check reports 91 pre-existing failures unrelated to quikridr pay-up/duration.

---

## 3. Field Alignment

| Field | Scope | Result |
|-------|-------|--------|
| `MPAYUP` | Phase-1 @44/45 only | **PASS** — equals `quikmstr.MPAIDTO` |
| `MLASTANN` | Phase-1 @44/45 only | **PASS** — `2026 − year(MPAYUP)` |
| `MEFFDATE` / `MAGE` / `MEXPRY` / `MUNIT` | Untouched | **PASS** (spot-check traces) |
| `MPREM` (#26) | Untouched | **PASS** (no blank MPREM introduced) |
| `MNFOPT` (#72) | Untouched on quikridr | **PASS** |
| #60 PUA later phases | 27 rows checked | **PASS** (0 MPAYUP≠MEFFDATE) |

---

## 4. Untouched Tables / Fields

| Item | Check | Result |
|------|-------|--------|
| `quikmstr` logic | Rebatched for cache only; no #76 hook | **PASS** (5,083 rows) |
| Rulebooks | Not modified | **PASS** |
| Rates | Not modified | **PASS** |
| `MCV0/1/2` | Still blank on traditional (rebuild UAT) | **PASS** (expected) |

---

## 5. Row Counts

| Table | Count | Notes |
|-------|------:|-------|
| quikmstr | 5,083 | Stable |
| quikridr | 6,934 | Stable |
| Phase-1 candidates @44/45 | **400** | All pass formula |
| MPAYUP changes (vs risk baseline) | **223** | Matches risk simulation |
| MLASTANN changes | **400** | All candidates |

---

## 6. Impact Summary

| Metric | Value |
|--------|------:|
| Policies adjusted (rebatch log) | 400 |
| MPAYUP violations after fix | 0 |
| MLASTANN violations after fix | 0 |
| PUA phase>1 regressions | 0 |
| Non-candidate false overrides | 0 |

---

## 7. Client UAT (pending)

1. Reload `Output/Test_Validation/quikridr.csv` into QLAdmin  
2. Data Admin on **`010407670C`**  
3. Rebuild CV  
4. Confirm Cash Value dates near **10/01/2026–2027**, not 2080  

MCV amounts may remain blank until rebuild (by design).

---

## Gate Criteria (G5 — Validation Pass)

- [x] All trace policies pass  
- [x] Validation script exits 0  
- [x] Untouched fields confirmed for issue scope  
- [x] Validation report published  
- [x] Status: **Ready for Regression**

---

## Next step

Say **“Proceed to Regression Agent”** for fleet non-candidate proof and closure path.
