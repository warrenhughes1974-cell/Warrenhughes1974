# ISWL Validation Strategy

**Project:** LifePRO → QLAdmin — QUIKCVS, QUIKGPS, QUIKCOI, QUIKGCOI  
**Version baseline:** v57.39  
**Date:** 2026-06-30 (updated — QUIKCOI/QUIKGCOI transform finalized)  
**Mode:** Planning only

---

## Validation principles

1. **Hierarchy-first:** Every emitted row must trace to PSEGT `SEGT_TYPE` on the resolved segment chain.
2. **PLAN authority:** Crosswalk MPLAN is the only PLAN source — never invent from COVERAGE_ID text.
3. **No TYPE_CODE-only proof:** PAAGERAT row counts alone are insufficient; segment join must pass.
4. **Regression safety:** Non-ISWL rate loads must remain unchanged (overlap_plans = 0 pattern from R7 PR study).
5. **Schema integrity:** Field order, types, lengths match confirmed DBF spec before emit.

---

## Sample policies (fleet anchors)

Use these MPLANs as primary reconciliation anchors:

| MPLAN | Coverage | Role in validation |
|-------|----------|-------------------|
| 1658C1 | 658 CEN I | Hub CV/U6/BP segment; sparse PAAGERAT on parent |
| 1658CS | 1658CS | CV + BP + U6 PAAGERAT present |
| 1659C2 | 659 CEN II | Hub segment owner |
| 1659CS | 659 CEN SD | BP PAAGERAT present |
| 1659SR | 659 SR GD | PSEGT present; sparse PAAGERAT |
| 1669SR | 669 SR GD | BP PAAGERAT present |
| 1679CS | 679 CEN SD | U5, U6, BP PAAGERAT present |

**Policy count context:** 2,268 ISWL policies across 8 MPLANs (research fleet).

---

# QUIKCVS validation

## Expected row counts (ISWL)

| Source | Metric | Expected (research) | Notes |
|--------|--------|---------------------|-------|
| Rate_Table CV | Raw ISWL rows | ~72,271 | All 8 coverages |
| PDAGE CV | Raw ISWL rows | ~12,084 | Subset — parity required |
| QuikCvs emit | Distinct grid keys | TBD after pivot | ≤ raw rows (dedupe) |
| QuikPlCv | Distinct keys | One per segmentation tuple per PLAN | CSO crosswalk driven |

**Per-MPLAN factor row targets:** Derive from dry-run `distinct_keys` grouped by PLAN; expect non-zero for all 8 MPLANs if Rate_Table CV covers all parents.

## Validation queries

### V-CVS-01 — PSEGT CV gate

```sql
-- Conceptual (CSV join in Python)
SELECT p.COVERAGE_ID, p.SEGT_ID, ps.SEGT_TYPE
FROM PCOVRSGT p
JOIN PSEGT ps ON ps.SEGMENT_ID = p.SEGT_ID
WHERE p.COVERAGE_ID IN (ISWL_8_COVERAGES)
  AND p.SEGT_FLAG = 'Y'
  AND ps.SEGT_TYPE = 'CV';
-- Expect: 8/8 coverages with ≥1 CV capability row
```

### V-CVS-02 — Rate_Table coverage coverage

```python
# Group Rate_Table rows: TYPE_CODE=CV, COVERAGE_ID in ISWL set
# Expect: 8 distinct COVERAGE_IDs with row_count > 0
```

### V-CVS-03 — Grid uniqueness

```python
# After build_factor_grid: zero collisions for QuikCvs
# Pipeline V03 BLOCKER on duplicate (PLAN, AGE, CNTL, GENDER, UWCLASS, BAND, ...)
```

### V-CVS-04 — CSO crosswalk completeness

```python
# For each ISWL MPLAN in allowlist:
#   resolve(MORT, ETIMORT, NFOINT, INTMETHCV) matched=True
```

### V-CVS-05 — PDAGE parity (pre-switch gate)

Compare for each `(COVERAGE_ID, SEX, UWCLS, BAND, AGE, DURATION)`:

- Rate_Table VALUE vs PDAGE VALUE
- Report: match rate %, max delta, rows only in one source
- **Emit blocker:** if parity < SME threshold (recommend 99.5% for matched keys)

## Sample reconciliation

1. Pick `PLAN=1659CS`, `GENDER=M`, `UWCLASS=NS`, `BAND=01`, `AGE=35`, `CNTL=00`.
2. Manual lookup in Rate_Table extract for `659 CEN SD`, TYPE=CV.
3. Compare QuikCvs dry-run CSV `CV0`…`CV9` to source.
4. Verify QuikPlCv MORT/NFOINT against CSO crosswalk row for `1659CS`.

## Reconciliation strategy

| Layer | Method |
|-------|--------|
| Source → loader | Row count by COVERAGE_ID × TYPE=CV |
| Loader → grid | Collision audit = 0 blockers |
| Grid → DBF | Field width / precision audit (fmt_issues) |
| DBF → QLAdmin | Import test on one MPLAN (manual SME) |
| Cross-source | PDAGE parity report before routing change |

---

# QUIKGPS validation

## Expected row counts (ISWL)

| Metric | Expected |
|--------|----------|
| PAAGERAT BP raw (ISWL) | 1,164 |
| Distinct parent coverages with BP | 4 (658 CEN SD, 659 CEN SD, 669 SR GD, 679 CEN SD) |
| Distinct MPLANs with BP factors | 4 (`1658CS`, `1659CS`, `1669SR`, `1679CS`) |
| QuikGps grid keys | ≤ 1,164 (after dedupe; segment-tier duplicates possible) |

**VARGP check:** All 4 MPLANs above must appear in `paagerat_vargp3_plans` set; `quikplan.VARGP=3`.

## Validation queries

### V-GPS-01 — Segment chain for BP

```python
# For each PAAGERAT row TYPE=BP, COVERAGE_ID=SEGT_ID:
#   resolver.resolve(SEGT_ID) -> parent, PLAN
#   assert PSEGT has U5/BP? -> BP for SEGMENT_ID
# Expect: 100% IN_SCOPE resolution (mirror R7 PR: unresolved=0)
```

### V-GPS-02 — PR exclusion

```python
# PAAGERAT TYPE=PR on ISWL waiver segments: must NOT enter BP loader
# Count PR ISWL rows ~328 — separate stream only
```

### V-GPS-03 — Parent vs segment ID

```python
# COVERAGE_ID on PAAGERAT = 658 CEN I or 659 CEN II (not parent SD)
# Resolved PLAN = 1658CS when parent = 658 CEN SD
```

### V-GPS-04 — Factor sanity

```python
# VALUE_FLOAT > 0 for BP rows
# GP0 populated; GP1-GP9 blank (VARGP=3)
```

## Sample reconciliation

1. `PAAGERAT`: `COVERAGE_ID=659 CEN II`, `TYPE=BP`, `SEQ=45`, `SEX=M`, `UWCLS=N`, `BAND=1`.
2. Expect `PLAN=1679CS` (parent 679 CEN SD) or matching parent per row.
3. Dry-run QuikGps row: `AGE=45`, `GP0=<formatted VALUE_FLOAT>`.

## Reconciliation strategy

| Layer | Method |
|-------|--------|
| PAAGERAT → resolver | Match R7 PR pattern: 0 unresolved segments |
| Row count | 1,164 ± 0 for ISWL BP filter |
| MPLAN coverage | 4 plans with factors; document 4 plans with PSEGT-only BP |
| VARGP | QuikPlan export shows VARGP=3 for ISWL BP plans |
| Non-regression | Existing PR QuikGps plans unchanged (diff dry-run before/after) |

---

# QUIKCOI validation

## Expected row counts (ISWL)

| Metric | Expected |
|--------|----------|
| PAAGERAT U6 raw (ISWL) | **800** |
| PAAGERAT segments | `658 CEN I` (400), `659 CEN II` (400) |
| MPLANs with U6 factors | **2** (`1658CS`, `1679CS`) |
| PSEGT U6 capability | 8/8 coverages |
| QuikCoi emit (v1) | **~792–800 rows** (after SEQ=100 AGE cap/collision) |
| MPLANs PSEGT-only (no PAAGERAT) | **6** — document; SME/client confirmation for partial fleet |

## Transform validation rules

| Rule | Check |
|------|-------|
| Attained-age scalar | One PAAGERAT row → one QuikCoi row (no duration pivot) |
| `SEQ` → `AGE` | Zero-pad C2; cap 99; audit SEQ=100 collisions |
| `CNTL` | All rows `"00"` |
| `VALUE_INFO` → `QX0` | Rate from VALUE_INFO; **reject VALUE_FLOAT-only path for U6** |
| `QX1`–`QX9` | **All blank** for ISWL attained-age data |
| VARGP | `quikplan.VARGP=3` for COI MPLANs |

## Validation queries

### V-COI-01 — U6 segment proof

```python
# All 8 coverages: PCOVRSGT -> PSEGT SEGT_TYPE=U6
```

### V-COI-02 — NC exclusion

```python
# PAAGERAT TYPE=NC must not enter COI loader
# NC = Net Premium Credited (Product Book)
```

### V-COI-03 — Resolution path audit

```python
# U6 rows: COVERAGE_ID in {658 CEN I, 659 CEN II}
# PLAN in {1658CS, 1679CS}
```

### V-COI-04 — Schema conformance

```python
# Field order/types match QLAdmin Help §7.73
# QX0-QX9 CHAR(10); PLAN, AGE, CNTL, segmentation, EFFDATE
```

### V-COI-05 — VALUE_INFO fidelity

```python
# For sample rows: QX0 == formatted VALUE_INFO (not VALUE_FLOAT)
# Assert zero U6 rows emit rate=0 when VALUE_INFO non-zero
```

### V-COI-06 — QX1–QX9 blank check

```python
# All emitted QuikCoi rows: QX1 through QX9 are empty strings
```

### V-COI-07 — SEQ=100 cap collision

```python
# SEQ=99 and SEQ=100 at same key: SEQ=99 retained, SEQ=100 dropped (audited)
# Expect up to 8 cap collisions for U6 (4 tuples × 2 segments)
```

## Sample reconciliation

1. `PLAN=1679CS`: sample attained ages 1, 25, 50, 75, 99 via `SEQ`.
2. Compare PAAGERAT U6 `VALUE_INFO` to QuikCoi `QX0`.
3. Verify no U6 rows map to wrong MPLAN via segment mis-resolution.
4. Confirm QX1–QX9 blank on all sample rows.

## Reconciliation strategy

| Layer | Method |
|-------|--------|
| Source → loader | 800 IN_SCOPE U6 rows; 2 MPLANs |
| Loader → grid | 1:1 row mapping; zero genuine collisions |
| Grid → output | ~792–800 QuikCoi rows |
| Partial fleet | Document 6 MPLAN PSEGT-only gap; no invented rates |
| Regression | U5/BP/PR/CV streams unaffected |

---

# QUIKGCOI validation

## Expected row counts (ISWL)

| Metric | Expected |
|--------|----------|
| PAAGERAT U5 raw (ISWL) | **200** |
| PAAGERAT segment | `659 CEN II` only |
| MPLANs with U5 factors | **1** (`1679CS`) |
| PSEGT U5 capability | 8/8 coverages |
| QuikGcoi emit (v1) | **~198–200 rows** (after SEQ=100 AGE cap/collision) |
| MPLANs PSEGT-only (no PAAGERAT) | **7** — document; SME/client confirmation |

## Transform validation rules

Same attained-age scalar rules as QUIKCOI (§ Transform validation rules): `SEQ`→`AGE`, `CNTL=00`, `VALUE_INFO`→`QX0`, QX1–QX9 blank, VARGP=3.

## Validation queries

### V-GCOI-01 — U5 vs U6 separation

```python
# No row emitted to both QuikCoi and QuikGcoi
# TYPE_CODE filter strict: U6 -> COI, U5 -> GCOI
```

### V-GCOI-02 — Single parent concentration

```python
# All 200 U5 rows: COVERAGE_ID=659 CEN II -> PLAN=1679CS
```

### V-GCOI-03 — Schema conformance

```python
# Field order/types match QLAdmin Help §7.93
```

### V-GCOI-04 — VALUE_INFO and QX blank checks

Same as V-COI-05, V-COI-06, V-COI-07 applied to U5/QuikGcoi.

## Sample reconciliation

Attained age spot-check on `1679CS` U5 rows; compare `VALUE_INFO` to `QX0`; confirm QX1–QX9 blank.

## Reconciliation strategy

| Layer | Method |
|-------|--------|
| Source → loader | 200 IN_SCOPE U5 rows; 1 MPLAN |
| Loader → output | ~198–200 QuikGcoi rows |
| Partial fleet | Document 7 MPLAN PSEGT-only gap |
| Regression | U6/BP/PR/CV streams unaffected |

---

# Cross-table validation

## V-X-01 — PLAN allowlist isolation

```python
from qla_core.cso_mortality_crosswalk import ISWL_MPLAN_ALLOWLIST
# All four tables: every emitted PLAN in allowlist OR existing non-ISWL set
# No ISWL logic mutates non-ISWL PLAN rows
```

## V-X-02 — Dry-run pipeline gate

Run `rate_pipeline.run()` with ISWL config:

- `emit_ready == True` for QUIKCVS + QUIKGPS + QUIKCOI + QUIKGCOI (after respective phases implemented)
- QUIKCOI: ~792–800 rows, 2 MPLANs; QUIKGCOI: ~198–200 rows, 1 MPLAN

## V-X-03 — Member table consistency

- `QuikPlNb.EFFDATE = 19000101`
- `QuikPlSt`, `QuikPlUw`, `QuikPlBd` codes cover all segmentation tuples

## V-X-04 — Version bump

Any `app.py` integration change requires version increment per AGENTS.md.

---

# Validation deliverables (per Development Agent phase)

| Phase | Script / artifact | Location |
|-------|-------------------|----------|
| QUIKCVS | `iswl_quikcvs_parity.py` | `tools/research/` or `tools/validators/` |
| QUIKCVS | Dry-run summary JSON | `plan_analysis/phase_r5_rate_loader/` |
| QUIKGPS | BP row reconciliation CSV | Issue folder |
| QUIKCOI/GCOI | `iswl_quikcoi_reconcile.py`, `iswl_quikgcoi_reconcile.py` | `tools/validators/` |
| All | `dryrun_validation_issues.csv` | From `rate_pipeline.write_issue_reports()` |

---

# SME sign-off checklist

- [ ] PDAGE vs Rate_Table CV parity threshold met
- [ ] Partial emit acceptable for 6 MPLANs without PAAGERAT U6 and 7 without U5
- [ ] VARGP=3 confirmed for ISWL on quikplan for GPS/COI/GCOI
- [ ] NC confirmed out of scope for QUIKCOI
- [ ] BP confirmed as QUIKGPS authority (not PR)
- [ ] SEQ=100 / AGE C(2) cap collision behavior accepted
- [ ] QX1–QX9 blank for attained-age COI/GCOI emit accepted by SME/client
- [ ] VALUE_INFO (not VALUE_FLOAT) confirmed as U5/U6 rate authority
