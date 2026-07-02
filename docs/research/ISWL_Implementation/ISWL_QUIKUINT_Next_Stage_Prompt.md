# ISWL QUIKUINT Next Stage Prompt — Development Agent (Phase 5: PR-5)

**Copy this prompt to launch the Development Agent for PR-5 QUIKUINT.**

**Status:** **READY FOR DEVELOPMENT** — all SME gates **CLOSED** (2026-06-30).

---

## Context

You are the **Development Agent** for **Issue #32 — ISWL Phase 5 QUIKUINT (PR-5)**.

**Project:** LifePRO → QLAdmin Conversion Platform  
**Current version:** v57.39 (increment `app.py` version only if touched)  
**Mode:** Surgical implementation only — no architecture redesign

**Prerequisite:** Issue #31 (PR-1–PR-4) **CLOSED**. All SME gates **CLOSED** — see [`Issue_32_QUIKUINT_SME_Answers.md`](../../Issue_Log_Items/Issue_32/Issue_32_QUIKUINT_SME_Answers.md).

**Authoritative planning docs (read first):**

- `docs/research/ISWL_Implementation/ISWL_QUIKUINT_Implementation_Blueprint.md`
- `docs/research/ISWL_Implementation/ISWL_QUIKUINT_Table_Design.md`
- `docs/research/ISWL_Implementation/ISWL_QUIKUINT_Validation_Strategy.md`
- `docs/research/ISWL_Implementation/ISWL_QUIKUINT_Development_Order.md`
- `Issue_Log_Items/Issue_32/Issue_32_QUIKUINT_SME_Answers.md`

---

## Objective

Implement **ISWL-scoped QUIKUINT** emission: PDINT hierarchy → `QuikUint`, with validation gates and zero regression to Issue #31 rate tables.

**In scope:**

- UL interest rates for 8 ISWL MPLANs: `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`
- Hierarchy: PCOMP → PCOVR → PCOVRSGT → PSEGT(A1) → PDINT(CENII) → PDINTTBL → QuikUint
- **Full historical tier emit** for CENII/A1 when available
- Validator `iswl_quikuint_reconcile.py`

**Out of scope:**

- QUIKISSC, expenses, loan interest on QuikUint, DBF/`app.py` integration (unless requested)
- PSEGT `SEGT_DATA` decode
- PPBEN / CSO crosswalk as primary emit source

---

## SME decisions (CLOSED — apply exactly)

| Decision | Rule |
|----------|------|
| PDINT IDENT | **CENII** for all 8 ISWL MPLANs |
| Source type | **A1** only for rate values |
| MCURRATE | **PDINTTBL.DECLARED_RATE** from CENII/A1 |
| MGTDRATE | **Same value as MCURRATE** on each tier |
| MEFFDATE | **PDINTTBL.START_DATE** of each tier |
| Emit scope | **All historical tiers** when available; **current tier only** if history missing |
| Loan | **Not QuikUint** |
| Rate format | N(8.4) percent literal (`4.50000` = 4.5%) |
| DINT_RULE handling | **Union merge** — Rules 0 + 3; tie-break Rule 3 at 19800101 |
| Emit mode | **`union_merge`** (not Rule 3 only) |

---

## Authoritative transform (PR-5)

```text
For each ISWL MPLAN in ISWL_MPLAN_ALLOWLIST:
  1. PCOVRSGT → PSEGT(A1) gate — must resolve
  2. PDINT IDENT = CENII, TYPE_CODE = A1
  3. Collect PDINTTBL tiers from DINT_RULE 0 AND DINT_RULE 3
  4. Union merge by unique START_DATE:
       - One rule only → include
       - Both rules, same rate → include once
       - Both rules, different rates → prefer Rule 3 (tie-break at 19800101)
  5. If no tiers: emit current tier only (fallback)
  6. For each merged tier:
       MPLAN    = crosswalk PLAN
       MEFFDATE = PDINTTBL.START_DATE
       MCURRATE = PDINTTBL.DECLARED_RATE
       MGTDRATE = MCURRATE
```

**Expected output:**

| Mode | Rows | MEFFDATEs per MPLAN |
|------|-----:|---------------------|
| **Union merge (default)** | **32** | 19800101, 19890101, 19990101, 20020101 |
| Fallback — current tier | **8** | 20020101 only |

**Critical:** Do **not** filter to DINT_RULE=3 only — that omits Rule 0 tier at 19990101 @ 5.00000 (SME violation). See [`Issue_32_QUIKUINT_Historical_Tier_Validation.md`](../../Issue_Log_Items/Issue_32/Issue_32_QUIKUINT_Historical_Tier_Validation.md).

---

## Business rules (non-negotiable)

1. **Hierarchy proof:** PCOVRSGT → PSEGT(A1) → PDINT(CENII) → PDINTTBL — no TYPE_CODE-only shortcuts.
2. **ISWL allowlist:** `qla_core/cso_mortality_crosswalk.ISWL_MPLAN_ALLOWLIST`
3. **QuikUint schema (Help §7.223):** MPLAN C(6), MEFFDATE D(8), MGTDRATE N(8.4), MCURRATE N(8.4).
4. **MGTDRATE = MCURRATE** on every row (SME confirmed).
5. **No loan column** on QuikUint.
6. **Surgical edits only** — preserve Issue #31 rate tables unchanged.
7. **Do not reuse** PAAGERAT attained-age loader.

---

## Implementation tasks

### Task 1 — Schema

Add `QuikUint` to `qla_core/rate_dbf_schema.py` (4 fields per Help §7.223). Separate stream — not in factor-grid map.

### Task 2 — Loader

Create `qla_core/pdint_uint_loader.py`:

- Read PDINT + PDINTTBL from config
- Reuse `SegmentResolver` for PSEGT A1 gate
- Collect tiers from **both** DINT_RULE 0 and 3; union merge by START_DATE
- MGTDRATE = MCURRATE on each row

### Task 3 — Config and pipeline

Add `iswl_phase5` to `rate_loader_config.json`:

```json
{
  "pdint_ident": "CENII",
  "dint_rules": ["0", "3"],
  "emit_mode": "union_merge",
  "dint_rule_tiebreak": "prefer_3",
  "g1_mode": "mirror_a1"
}
```

Wire uint stream in `rate_pipeline.py`.

### Task 4 — Validator

Create `tools/validators/iswl_quikuint_reconcile.py` — V-UINT-01 through V-UINT-08.

Output: `Issue_Log_Items/Issue_32/output/Phase5_QUIKUINT/`

### Task 5 — Dry-run

**Success criteria:**

- `blocker_count == 0`
- 8/8 ISWL MPLANs emitted
- CENII / A1 source confirmed
- MGTDRATE == MCURRATE on all rows
- Historical MEFFDATEs: 19800101, 19890101, **19990101**, 20020101
- 19990101 @ 5.00000 present (Rule 0 tier)
- Total rows = **32** (union merge) or **8** (fallback)
- Issue #31 regression PASS

### Task 6 — Documentation

Implementation note under `Issue_Log_Items/Issue_32/`.

---

## Validation checklist

- [ ] V-UINT-01: PSEGT A1/G1/LN 8/8
- [ ] V-UINT-02: CENII for all 8 MPLANs
- [ ] V-UINT-03: PDINTTBL historical tiers joined
- [ ] V-UINT-03b: Historical tiers emitted when available
- [ ] V-UINT-04: Schema §7.223; unique (MPLAN, MEFFDATE)
- [ ] V-UINT-05: MCURRATE from DECLARED_RATE; 4.50000 current tier
- [ ] V-UINT-05b: MEFFDATE from START_DATE
- [ ] V-UINT-06: MGTDRATE == MCURRATE (100%)
- [ ] V-UINT-07: Issue #31 regression PASS
- [ ] V-UINT-08: No loan on QuikUint

---

## Expected files to modify

| File | Purpose |
|------|---------|
| `qla_core/pdint_uint_loader.py` | **New** |
| `qla_core/rate_dbf_schema.py` | QuikUint layout |
| `qla_core/rate_pipeline.py` | Wire uint stream |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `iswl_phase5` |
| `tools/validators/iswl_quikuint_reconcile.py` | **New** |
| `tools/validators/iswl_common.py` | Phase 5 output paths |

**Do not modify:** `paagerat_ul_coi_loader.py`, `paagerat_bp_loader.py`, existing Issue #31 validators (except `iswl_common.py` paths).

---

## Stop conditions

**Stop and report if:**

- PDINT CENII/A1 cannot be resolved for any ISWL MPLAN
- PDINTTBL returns no tiers and fallback current tier also missing
- `(MPLAN, MEFFDATE)` index collision cannot be resolved surgically
- Issue #31 regression fails

---

## Deliverables

1. Code changes (minimal diff)
2. Dry-run artifacts under `Issue_Log_Items/Issue_32/output/Phase5_QUIKUINT/`
3. Row counts by MPLAN (expect **4 tiers × 8 = 32** union merge)
4. Regression note: Issue #31 table counts unchanged
5. SME decision log reference in implementation summary

---

## After validation PASS

1. CSV emit → `QLA_Migration/Output/rates/QuikUint.csv`
2. Issue #32 QUIKUINT closeout documentation
3. Loan interest remains separate PR (QuikPlan/QuikPlSt)
