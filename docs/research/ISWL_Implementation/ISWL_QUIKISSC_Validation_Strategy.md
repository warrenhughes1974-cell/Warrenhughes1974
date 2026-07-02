# ISWL QUIKISSC Validation Strategy

**Project:** LifePRO → QLAdmin — QUIKISSC  
**Issue:** #33 — Phase 6  
**Version baseline:** v57.40  
**Date:** 2026-06-28  
**Mode:** Planning only  
**Readiness:** **READY AFTER SME CONFIRMATION**  
**SME log:** [`Issue_33_SME_Questions.md`](../../Issue_Log_Items/Issue_33/Issue_33_SME_Questions.md)

---

## Validation principles

1. **Hierarchy-first:** Every QuikIssc row must trace PCOVRSGT → PSEGT(SR) → PSEGT(SL) → rate schedule before emit.
2. **No TYPE_CODE-only mapping:** Rate_Table SL rows invalid without segment proof.
3. **PLAN authority:** Crosswalk MPLAN only — all **8 ISWL MPLANs** covered per SME.
4. **TP/TX exclusion:** Zero rows sourced from tax TYPE_CODEs.
5. **Regression safety:** Issue #31 Phases 1–4 + Issue #32 Phase 5 unchanged.
6. **Schema integrity:** QuikIssc fields match Help §7.144.
7. **Duration pivot:** DURATION *n* → SCHG*n* with monotonic schedule where business expects decline.

---

## Expected row counts (forensically determined — pending SME sign-off)

Forensic resolution confirmed the SL schedule varies by **duration only** — `SEX=M`, `UWCLASS=S`, `BAND=1`, `AGE=0` are constant — so one row per MPLAN.

| Metric | Value | Notes |
|--------|------:|-------|
| ISWL MPLANs with QuikIssc rows | 8 | Fleet |
| Rows per MPLAN | 1 | Single all-age tuple |
| **Total QuikIssc rows** | **8** | Exact (forensic) |
| SCHG columns populated | 14 | Durations 1–14 in hub extract |
| SCHG columns blank | 6 | SCHG15–20 (no source) |
| PSEGT SR gate | 8/8 | Proven |
| PSEGT SL gate | 8/8 | Proven |

---

## Validation checks

### V-ISSC-01 — Schema conformance (Help §7.144)

```python
# QuikIssc rows:
#   PLAN C(6), AGE N(3), GENDER C(1), UWCLASS C(2), BAND C(2)
#   ISSCNTRY C(4), ISSUEST C(2)
#   SCHG01..SCHG20 N(8.4)
# Index: PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST
```

**Pass criteria:** Field names, order, and types match schema definition.

---

### V-ISSC-02 — PSEGT SR/SL gate

```python
# PCOVRSGT active slots → PSEGT must include SR and SL for all 8 ISWL coverages
# Expect: 8/8 for SR; 8/8 for SL
# Hub SEGMENT_ID: 659 CEN II
```

**Pass criteria:** 8/8 coverages; U7/U8 count = 0.

---

### V-ISSC-03 — Segment rate pointer resolved

```python
# Decode PSEGT(659 CEN II, SL).SEGT_DATA
# Assert pointer resolves to authoritative rate rows (not TP/TX, not PAAGERAT)
# Assert row count > 0 after join
```

**Pass criteria:** Pointer documented; join proven; SME-approved source name.

---

### V-ISSC-04 — SR → SL hierarchy

```python
# Product Book: SR parent accesses SL child
# Assert SL schedule loaded only after SR/SL segment proof
# Assert NOT using TYPE_CODE=SL without segment gate
```

**Pass criteria:** Hierarchy documented in loader status; no bypass path.

---

### V-ISSC-05 — Row count band

```python
# Assert total rows within SME-approved band (e.g. 8 minimum, 64 maximum)
# Assert each MPLAN in ISWL_MPLAN_ALLOWLIST has >= 1 row
```

**Pass criteria:** Matches SME-signed expected count.

---

### V-ISSC-06 — MPLAN coverage 8/8

```python
# distinct PLAN values == ISWL_UINT_MPLANS (same 8 MPLAN fleet)
```

**Pass criteria:** 8/8 MPLANs present.

---

### V-ISSC-07 — Duration pivot integrity

```python
# For each row:
#   SCHG01 populated iff DURATION=1 source exists
#   ...
#   SCHG14 populated for hub schedule
#   No SCHG column maps from wrong duration index
```

**Pass criteria:** 14 durations mapped; SCHG15–20 per SME Q9.

---

### V-ISSC-08 — Percent literal format

```python
# SME-approved: values like 100.0000 (not 1.0000) OR decimal per Q4
# Assert min/max within business range (0–100 if percent literal)
```

**Pass criteria:** Format matches SME Q4 decision.

---

### V-ISSC-09 — Unique index keys

```python
# No duplicate (PLAN, GENDER, UWCLASS, BAND, ISSCNTRY, ISSUEST)
```

**Pass criteria:** duplicate_index_keys = 0.

---

### V-ISSC-10 — TP/TX exclusion

```python
# Loader must not read TYPE_CODE in (TP, TX) for QUIKISSC stream
# Status counter: NO_TP_TX = pass
```

**Pass criteria:** Zero TP/TX sourced rows.

---

### V-ISSC-11 — Hub schedule shape (when approved)

```python
# Provisional anchor (659 CEN II / M / S / Band1):
# Durations 1-2: 100.0000; 3: 70; 4: 60; 5: 50; 6: 40; 7: 30; 8: 20
# 9: 15; 10: 10; 11: 8; 12: 6; 13: 4; 14: 2
# Apply only after SME confirms Rate_Table SL authority
```

**Pass criteria:** Schedule matches approved anchor within format tolerance.

---

### V-ISSC-12 — Phase 1–5 regression

```python
# Re-run:
#   iswl_quikcvs_reconcile.py
#   iswl_quikgps_reconcile.py
#   iswl_quikcoi_reconcile.py
#   iswl_quikgcoi_reconcile.py
#   iswl_quikuint_reconcile.py
# Factor row counts unchanged vs baselines
```

**Pass criteria:** All prior validators PASS; row counts locked.

---

## Optional validation (post-emit)

### V-ISSC-P1 — Policy surrender load reconcile

Compare sample policy `BF_CURR_SURR_LOAD` / `SURR_LOAD` against schedule lookup for policy year.

### V-ISSC-P2 — QuikCvs floor rule

Document-only check: surrender schedule consistent with CV floor business rule (no automated assert until policy engine available).

---

## Validator artifact plan

| Artifact | Path |
|----------|------|
| Summary JSON | `Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/iswl_quikissc_reconcile_summary.json` |
| Keys by MPLAN | `Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/iswl_quikissc_keys_by_mplan.csv` |
| Regression baseline | `Issue_Log_Items/Issue_33/output/baselines/iswl_quikissc_regression_baseline.json` |
| CSV emit | `QLA_Migration/Output/rates/QuikIssc.csv` |

---

## Pass / fail gate

**Emit ready** requires:

- V-ISSC-01 through V-ISSC-12 all **PASS**
- `blocker_count = 0`
- SME gates documented in `Issue_33_QUIKISSC_SME_Answers.md`

---

## Run commands (future)

```text
python tools/validators/iswl_quikissc_reconcile.py
python tools/validators/iswl_quikissc_reconcile.py --write-baseline --emit-csv
python tools/validators/iswl_quikuint_reconcile.py   # Phase 5 regression
python tools/validators/iswl_quikgcoi_reconcile.py   # Phase 4 regression
```
