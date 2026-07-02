# ISWL Next Stage Prompt — Development Agent (Phase 1: QUIKCVS)

**Copy this prompt to launch the Development Agent for the first approved ISWL table.**

---

## Context

You are the **Development Agent** for Issue #31 follow-on — **ISWL QUIKCVS implementation**.

**Project:** LifePRO → QLAdmin Conversion Platform  
**Current version:** v57.39 (increment `app.py` version if touched)  
**Mode:** Surgical implementation only — no architecture redesign

**Authoritative planning docs (read first):**

- `docs/research/ISWL_Implementation/ISWL_Implementation_Blueprint.md`
- `docs/research/ISWL_Implementation/ISWL_Table_By_Table_Design.md` § QUIKCVS
- `docs/research/ISWL_Implementation/ISWL_Validation_Strategy.md` § QUIKCVS
- `docs/research/ISWL_Implementation/ISWL_Development_Order.md` Phase 1
- `Issue_Log_Items/Issue_31/Issue_31_Extract_Validation_Report.md`
- `docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Addendum_20260629.md`

---

## Objective

Implement **ISWL-scoped QUIKCVS** emission using the existing Rate_Table → QuikCvs pipeline, with validation gates and zero regression to non-ISWL plans.

**In scope:**

- Cash value factors for 8 ISWL MPLANs: `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`
- QuikPlCv assumption keys via CSO mortality crosswalk
- Dry-run validation artifacts

**Out of scope (this phase):**

- QUIKGPS, QUIKCOI, QUIKGCOI
- PDAGE as authoritative source (parity script only — do not switch routing unless parity passes SME threshold)
- PSEGT `SEGT_DATA` decode
- QUIKUINT, QUIKISSC

---

## Business rules (non-negotiable)

1. **Hierarchy:** PCOMP → PCOVR → PCOVRSGT → PSEGT (`SEGT_TYPE=CV`) → Rate_Table `TYPE=CV` → crosswalk PLAN → QuikCvs.
2. **MPHASE 1** = base coverage; do not conflate riders.
3. **NC is not QUIKCOI** — irrelevant here but do not introduce NC routing.
4. **ISWL allowlist:** `qla_core/cso_mortality_crosswalk.ISWL_MPLAN_ALLOWLIST`
5. **VARGP=2** for QuikCvs (issue age × duration) — do not change ISWL to VARGP=3 for CV.
6. **Preserve** existing QLA formatting, field order, types, lengths.
7. **Surgical edits only** — do not rewrite `app.py` wholesale.

---

## Implementation tasks

### Task 1 — Config and scope gate

- Ensure `rate_loader_config.json` (or example promoted to active config) points to:
  - `Rate_Table_Extract_20260427.csv`
  - PCOVRSGT, PCOVR, crosswalk, CSO crosswalk
- Add ISWL-only filter or validation that emitted QuikCvs PLAN rows for this feature are in `ISWL_MPLAN_ALLOWLIST` when running ISWL mode (do not drop non-ISWL rows from global dry-run unless explicitly scoped).

### Task 2 — PSEGT CV validation hook

- Add lightweight check (validator script acceptable): all 8 ISWL coverages have PSEGT `SEGT_TYPE=CV` on resolved PCOVRSGT segment.
- Source: `QLA_Migration/Source/PSEGT_Segment_Extract_20260629.csv`

### Task 3 — CSO crosswalk verification

- Confirm all 8 ISWL MPLANs resolve MORT/ETIMORT/NFOINT/INTMETHCV with `matched=True`.
- ISWL MDEPINT = 4.50% path already in crosswalk module.

### Task 4 — PDAGE parity script (non-blocking)

- Create `tools/research/iswl_quikcvs_parity.py` (or `tools/validators/`):
  - Compare Rate_Table CV vs PDAGE CV for ISWL coverages
  - Output match rate, deltas, keys-only-in-one-source
  - Do **not** switch loader source based on script alone

### Task 5 — Dry-run and artifacts

- Run `rate_pipeline.run()` for ISWL-relevant plans
- Produce:
  - `dryrun_validation_issues.csv`
  - Summary JSON with `distinct_plans` per QuikCvs
  - Row counts by MPLAN
- **Success criteria:** `blocker_count == 0`; 8 ISWL MPLANs with QuikCvs distinct_keys > 0

### Task 6 — Documentation

- Add brief implementation note to `Issue_Log_Items/Issue_31/` or update Issue #31 resolution status
- List exact files changed and regression risk

---

## Validation checklist (must pass)

- [ ] V-CVS-01: PSEGT CV 8/8
- [ ] V-CVS-02: Rate_Table CV rows for 8 coverages
- [ ] V-CVS-03: Zero grid collisions (V03)
- [ ] V-CVS-04: CSO crosswalk complete for 8 MPLANs
- [ ] V-CVS-05: Parity script executed (result documented)
- [ ] V-X-01: Non-ISWL plans unchanged in dry-run diff
- [ ] V-X-03: QuikPlNb EFFDATE = 19000101
- [ ] No new blank MRIDRID values in policy conversion paths (if app.py touched)

---

## Expected files to modify

| File | Purpose |
|------|---------|
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | Source paths |
| `qla_core/rate_factor_loader.py` | Optional ISWL scope (minimal) |
| `qla_core/rate_pipeline.py` | Only if config wiring required |
| `tools/research/iswl_quikcvs_parity.py` | **New** |
| `QLA_Migration/app.py` | Version bump only if integration changed |

**Do not modify unless required:**

- `paagerat_pr_loader.py`
- `rate_dbf_schema.py` TYPE_TO_TABLE (CV already mapped)

---

## Stop conditions

**Stop and report (do not guess) if:**

- Rate_Table CV rows missing for any of 8 ISWL coverages
- CSO crosswalk returns unmatched for any ISWL MPLAN
- Dry-run blockers cannot be resolved surgically
- PDAGE parity reveals systematic divergence requiring SME decision

---

## Deliverables

1. Code changes (minimal diff)
2. Dry-run validation CSV/JSON
3. PDAGE parity report
4. Implementation summary with row counts by MPLAN
5. Regression note: non-ISWL plan factor counts before/after

---

## After QUIKCVS approval

Next Development Agent targets in sequence:

1. **QUIKGPS (Phase 2)** — extend PAAGERAT attained-age loader for `TYPE_CODE=BP`.
2. **QUIKCOI (Phase 3)** — spec complete. Attained-age scalar emit: `SEQ`→`AGE`, `CNTL=00`, `VALUE_INFO`→`QX0`, QX1–QX9 blank. 800 source rows → ~792–800 output; MPLANs `1658CS`, `1679CS`.
3. **QUIKGCOI (Phase 4)** — reuse Phase 3 loader for `U5`. 200 source rows → ~198–200 output; MPLAN `1679CS` only.

See `ISWL_Development_Order.md` and `ISWL_Table_By_Table_Design.md` §3–4 for full COI/GCOI implementation spec.

---

## QUIKCOI / QUIKGCOI — spec status (Phases 3–4)

**Design complete. Ready for Development Agent after Phases 1–2.**

Authoritative transform (do not use issue-age × duration pivot for ISWL PAAGERAT U5/U6):

| Rule | Value |
|------|-------|
| Hierarchy | PCOMP → PCOVR → PCOVRSGT → PSEGT → PAAGERAT → QuikCoi/QuikGcoi |
| U6 → QUIKCOI | 800 rows; segments `658 CEN I`, `659 CEN II` |
| U5 → QUIKGCOI | 200 rows; segment `659 CEN II` |
| `SEQ` | → `AGE` (attained age, VARGP=3) |
| `CNTL` | `"00"` |
| Rate | `VALUE_INFO` → `QX0` only; **never VALUE_FLOAT when VALUE_INFO populated** |
| `QX1`–`QX9` | Blank |
| SEQ=100 | AGE cap/collision rule per existing pipeline |

Remaining risks: partial MPLAN coverage (6/8 U6, 7/8 U5 PSEGT-only); SME/client confirmation for sparse fleet emit.
