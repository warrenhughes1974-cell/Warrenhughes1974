# ISWL QUIKUINT Validation Strategy

**Project:** LifePRO → QLAdmin — QUIKUINT  
**Issue:** #32 — Phase 5  
**Version baseline:** v57.39  
**Date:** 2026-06-30 (SME gate closure)  
**Mode:** Planning only  
**Readiness:** **READY FOR DEVELOPMENT**  
**SME log:** [`Issue_32_QUIKUINT_SME_Answers.md`](../../Issue_Log_Items/Issue_32/Issue_32_QUIKUINT_SME_Answers.md)

---

## Validation principles

1. **Hierarchy-first:** Every QuikUint row must trace PCOVRSGT → PSEGT(A1) → PDINT IDENT=CENII → PDINTTBL rate.
2. **PLAN authority:** Crosswalk MPLAN only — all **8 ISWL MPLANs** emitted.
3. **SME mapping:** CENII / A1 source; MGTDRATE mirrors MCURRATE; full historical tiers when available.
4. **Regression safety:** Issue #31 rate tables unchanged.
5. **Schema integrity:** QuikUint fields match Help §7.223.
6. **Loan separation:** No loan rate on QuikUint.

---

## Expected row counts (SME-approved)

| Metric | Expected | Notes |
|--------|----------|-------|
| ISWL MPLANs with QuikUint rows | **8** | All fleet MPLANs |
| QuikUint rows (union merge) | **32** | 8 × 4 unique START_DATEs (Rules 0+3) |
| QuikUint rows (fallback) | **8** | Current tier only if no history |
| PSEGT A1 / G1 / LN gate | **8/8** each | Proven |
| CENII A1 current rate | **4.50000** | Tier MEFFDATE=20020101 |

---

## Validation queries

### V-UINT-01 — PSEGT A1/G1/LN gate

```python
# PCOVRSGT active slots → PSEGT must include A1, G1, LN for all 8 ISWL coverages
# Expect: 8/8 for each type
```

### V-UINT-02 — CENII IDENT for all 8 MPLANs

```python
# For each ISWL MPLAN in ISWL_MPLAN_ALLOWLIST:
#   assert PDINT IDENT resolved == "CENII"
#   assert PDINT TYPE_CODE == "A1" row exists
# Expect: 8/8 MPLANs; UNRESOLVED_IDENT count = 0
```

### V-UINT-03 — PDINTTBL historical tier join

```python
# Join PDINTTBL for IDENT=CENII, TYPE_CODE=A1, DINT_RULE in (0, 3)
# Union merge by unique START_DATE (tie-break: prefer Rule 3 at collision)
# Expect: 4 tiers per MPLAN — MEFFDATE 19800101, 19890101, 19990101, 20020101
# Total fleet rows: 32 (8 MPLANs × 4 tiers)
# DECLARED_RATE populated for every tier
```

### V-UINT-03b — Historical tier coverage

```python
# Union merge mode: 4 MEFFDATEs per MPLAN
#   19800101 @ 11.00000 (Rule 3 — tie-break)
#   19890101 @ 9.00000  (Rule 3)
#   19990101 @ 5.00000  (Rule 0 — must not be omitted)
#   20020101 @ 4.50000  (both rules)
# Assert Rule 0 tier at 19990101 present (SME historical-load compliance)
# Fallback mode: single row MEFFDATE=20020101 @ 4.50000
```

### V-UINT-04 — Schema conformance (Help §7.223)

```python
# QuikUint rows:
#   MPLAN C(6), MEFFDATE D8, MGTDRATE/MCURRATE N(8.4)
#   Exactly 4 fields — no loan column
# Index uniqueness: (MPLAN, MEFFDATE) unique across all rows
```

### V-UINT-05 — MCURRATE from DECLARED_RATE

```python
# MCURRATE == PDINTTBL.DECLARED_RATE for each tier
# Current tier (20020101): MCURRATE == 4.50000 for all 8 MPLANs
# Rate format: percent literal (4.50000 not 0.04500)
# Cross-validation: PPBEN FV_GUAR_RATE == 4.50 spot-check (WARNING only)
```

### V-UINT-05b — MEFFDATE from START_DATE

```python
# MEFFDATE == PDINTTBL.START_DATE for each emitted tier
# Historical emit: multiple MEFFDATEs per MPLAN (not only 20020101)
# Assert MEFFDATE != 19000101
```

### V-UINT-06 — MGTDRATE mirrors MCURRATE (SME confirmed)

```python
# For every QuikUint row: MGTDRATE == MCURRATE
# Document in summary JSON: "g1_mode": "mirror_a1"
# Expect: 100% match across all tiers and MPLANs
```

### V-UINT-07 — Issue #31 regression

```python
# QuikCvs/Gps/Coi/Gcoi row counts == Issue_31 baselines
# blocker_count = 0; emit_ready = true
```

### V-UINT-08 — No loan interest on QuikUint

```python
# Assert no loan rate field or LN-sourced value on QuikUint rows
# PSEGT LN gate passes 8/8 — tracked separately under QuikPlan/QuikPlSt
```

---

## Sample reconciliation

1. Pick `MPLAN=1659CS`.
2. Trace `659 CEN SD` → PCOVRSGT → `659 CEN II` → PSEGT `A1`.
3. Lookup PDINT `CENII` / `A1` / `DINT_RULE=3`.
4. Verify **4 historical tiers** with MEFFDATE = 19800101, 19890101, 19990101, 20020101.
5. Confirm 19990101 @ 5.00000 present (Rule 0 tier — SME compliance check).
6. Confirm MCURRATE = MGTDRATE = DECLARED_RATE on each tier.
7. Confirm total fleet rows = **32** (union merge) or **8** (fallback).

---

## Pass / fail summary

| ID | Check | Pass criteria |
|----|-------|---------------|
| V-UINT-01 | PSEGT A1/G1/LN 8/8 | PASS |
| V-UINT-02 | CENII for all 8 MPLANs | PASS — 0 unresolved |
| V-UINT-03 | PDINTTBL join + rates | PASS |
| V-UINT-03b | Historical tiers when available | PASS |
| V-UINT-04 | Schema §7.223 + unique index | PASS |
| V-UINT-05 | MCURRATE from DECLARED_RATE | PASS |
| V-UINT-05b | MEFFDATE from START_DATE | PASS |
| V-UINT-06 | MGTDRATE == MCURRATE | PASS |
| V-UINT-07 | Issue #31 regression | PASS |
| V-UINT-08 | No loan on QuikUint | PASS |

**Gate for CSV emit:** `blocker_count=0`, `emit_ready=true`.

---

## Validator deliverable (PR-5)

**Script:** `tools/validators/iswl_quikuint_reconcile.py`

**Artifacts:**

- `Issue_Log_Items/Issue_32/output/Phase5_QUIKUINT/iswl_quikuint_reconcile_summary.json`
- `Issue_Log_Items/Issue_32/output/Phase5_QUIKUINT/iswl_quikuint_rates_by_mplan.csv`
- `Issue_Log_Items/Issue_32/output/baselines/iswl_quikuint_regression_baseline.json`
