# ISWL Implementation Blueprint

**Project:** LifePRO → QLAdmin Conversion Platform  
**Version baseline:** v57.39  
**Date:** 2026-06-30 (updated 2026-06-30 — QUIKCOI/QUIKGCOI transform finalized)  
**Mode:** Planning only — no code changes  
**Authority:** Issue #31 extract validation, PSEGT segment trace, Product Book addendum, QLAdmin Help §7.73 / §7.93, existing `qla_core` rate pipeline

---

## Scope

Implementation blueprint for four QLAdmin targets validated as **implementation-ready**:

| Target | QLAdmin table(s) | Readiness |
|--------|------------------|-----------|
| QUIKCVS | `QuikCvs` + `QuikPlCv` | **Implementation ready** (conditional PDAGE parity) |
| QUIKGPS | `QuikGps` + `QuikPlGp` | **Implementation ready** |
| QUIKCOI | `QuikCoi` | **Implementation ready** (partial MPLAN coverage) |
| QUIKGCOI | `QuikGcoi` | **Implementation ready** (partial MPLAN coverage) |

**ISWL fleet (8 MPLANs):** `1658C1`, `1658CS`, `1659C2`, `1659CR`, `1659CS`, `1659SR`, `1669SR`, `1679CS`

**Out of scope for this blueprint:** QUIKUINT, QUIKISSC, Expenses (partially resolved — separate issues).

---

## Mandatory hierarchy (all targets)

```text
PCOMP (PRODUCT_ID = coverage id for ISWL)
  ↓
PCOVR (coverage metadata, POLICY_FORM_NUM)
  ↓
PCOVRSGT (SEGT_FLAG=Y slots → SEGT_ID)
  ↓
PSEGT (SEGMENT_ID + SEGT_TYPE capability rows)
  ↓
Rate table (PAAGERAT | PDAGE | Rate_Table per segment rate type)
  ↓
Policy Form Crosswalk → authoritative PLAN (MPLAN)
  ↓
QLAdmin factor / UL table
```

**PPRDF:** Not in repo; ISWL hierarchy starts at PCOMP. Non-blocking.

**Non-negotiable rule:** Never emit from `TYPE_CODE` alone. Every emit path must resolve `PCOVRSGT.SEGT_ID` → `PSEGT.SEGT_TYPE` → rate row → PLAN.

---

## Authoritative ISWL U5/U6 transform (final)

PAAGERAT `U5`/`U6` rows are **attained-age scalar rates**, not issue-age × duration grids.

| Path | Segment | Source | Target |
|------|---------|--------|--------|
| Current COI | PSEGT `U6` | PAAGERAT `TYPE_CODE=U6` | `QuikCoi` |
| Guaranteed COI | PSEGT `U5` | PAAGERAT `TYPE_CODE=U5` | `QuikGcoi` |

**Transform (one PAAGERAT row → one QUIKCOI/QUIKGCOI row):**

| PAAGERAT | QLAdmin | Rule |
|----------|---------|------|
| `SEQ` | `AGE` | Attained age (VARGP=3); zero-pad C2; cap at 99 |
| (fixed) | `CNTL` | `"00"` |
| `VALUE_INFO` | `QX0` | Authoritative rate; format CHAR(10) |
| — | `QX1`–`QX9` | **Blank** (intentionally unused for ISWL attained-age data) |
| `SEX` / `UWCLS` / `BAND` | `GENDER` / `UWCLASS` / `BAND` | Standard crosswalks |
| Config | `ISSCNTRY` / `ISSUEST` / `EFFDATE` | `0000` / `00` / `19000101` |

**Critical rules:**

- **`VALUE_FLOAT` must not be used** when `VALUE_INFO` is populated (U5/U6: FLOAT is always 0.0 in extract).
- **No duration pivot** for current ISWL PAAGERAT data — QX1–QX9 are not populated from ten durations.
- **`SEQ=100`** handled via documented AGE C(2) cap/collision rule (SEQ 99 wins over capped SEQ 100).
- **`quikplan.VARGP = 3`** (attained-age semantics) for MPLANs receiving QUIKCOI/QUIKGCOI factors.

---

## Expected source and output counts (U5/U6)

| Target | PAAGERAT rows | Segments | MPLANs | Expected DBF rows (after AGE cap) |
|--------|---------------|----------|--------|-----------------------------------|
| QUIKCOI (U6) | 800 | `658 CEN I`, `659 CEN II` | `1658CS`, `1679CS` | **~792–800** |
| QUIKGCOI (U5) | 200 | `659 CEN II` | `1679CS` | **~198–200** |

---

## Shared infrastructure (already implemented)

| Component | Path | Role |
|-----------|------|------|
| Segment resolver | `qla_core/rate_segment_resolution.py` | PAAGERAT `COVERAGE_ID` = `SEGT_ID` → parent → PLAN |
| Rate factor loader | `qla_core/rate_factor_loader.py` | Rate_Table transform, grid pivot, CHAR(7) factors |
| PAAGERAT PR loader | `qla_core/paagerat_pr_loader.py` | VARGP=3 attained-age pattern (template for U5/U6/BP) |
| Rate pipeline | `qla_core/rate_pipeline.py` | Orchestrates Rate_Table + PAAGERAT PR streams |
| DBF schema | `qla_core/rate_dbf_schema.py` | `QuikCvs`/`QuikGps` layouts; **QuikCoi/QuikGcoi to be added** |
| CSO crosswalk | `qla_core/cso_mortality_crosswalk.py` | ISWL allowlist, NFOINT/MDEPINT 4.50% |
| Config | `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Source paths, segmentation defaults |

---

## Target summaries

### QUIKCVS — Cash Values

**Hierarchy:** PSEGT `CV` → **Rate_Table** or **PDAGE** `TYPE=CV` → `QuikCvs`.

**VARGP:** 2 (issue age × duration grid).

**Complexity:** **Medium** (parity gate + ISWL MPLAN allowlist).

---

### QUIKGPS — Billable Premium (BP segment)

**Hierarchy:** PSEGT `BP` → **PAAGERAT** `TYPE_CODE=BP` → `QuikGps`.

**VARGP:** 3 (`SEQ` → `AGE`, single factor at CNTL=00/GP0).

**Complexity:** **Medium** (extend PAAGERAT loader for BP).

---

### QUIKCOI — Current COI (U6 segment)

**Hierarchy:** PSEGT `U6` (8/8) → PAAGERAT `U6` (800 rows) → `QuikCoi`.

**Schema:** QLAdmin Help §7.73 — `PLAN`, `AGE`, `CNTL`, `QX0`–`QX9` (C10), segmentation, `EFFDATE`. **Confirmed.**

**Transform:** Attained-age scalar emit — **one PAAGERAT row → one QuikCoi row**, `QX0` only.

**Complexity:** **Medium** (new loader + schema constants; shares attained-age core with QUIKGPS).

**Partial fleet:** Only `1658CS` and `1679CS` have PAAGERAT U6 rows; 6/8 MPLANs have PSEGT U6 capability only.

---

### QUIKGCOI — Guaranteed COI (U5 segment)

**Hierarchy:** PSEGT `U5` (8/8) → PAAGERAT `U5` (200 rows) → `QuikGcoi`.

**Schema:** QLAdmin Help §7.93 — same field layout as QuikCoi (`PLAN` C6). **Confirmed.**

**Transform:** Same attained-age scalar emit as QUIKCOI; filter `TYPE_CODE=U5`.

**Complexity:** **Medium** (reuse Phase 3 loader core).

**Partial fleet:** Only `1679CS` has PAAGERAT U5 rows; 7/8 MPLANs have PSEGT U5 capability only.

---

## Cross-cutting risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| SD parent indirection | U6/BP PAAGERAT keyed to hub SEGT_ID resolves to SD parent PLAN | Use `SegmentResolver`; document in validation |
| 6/8 MPLANs sparse U5/U6 | PSEGT capability without PAAGERAT rows | Document partial emit; SME/client confirmation for fleet gaps |
| SEQ=100 vs AGE C(2) | Cap collision at AGE=99 | Existing cap/collision rules; audit SEQ 99 vs 100 |
| PDAGE vs Rate_Table CV mismatch | 12,084 vs 72,271 ISWL CV rows | Parity study before CV source switch |
| QX1–QX9 blank | Help describes duration 0–9 columns | Document VARGP=3 scalar mode; intentional for ISWL |
| PSEGT `SEGT_DATA` undecoded | SR/SL rate pointer unknown | Out of scope |

---

## Related deliverables

| Document | Purpose |
|----------|---------|
| [`ISWL_Table_By_Table_Design.md`](ISWL_Table_By_Table_Design.md) | Per-table hierarchy, fields, transforms |
| [`ISWL_Validation_Strategy.md`](ISWL_Validation_Strategy.md) | Row counts, queries, reconciliation |
| [`ISWL_Development_Order.md`](ISWL_Development_Order.md) | Build sequence |
| [`ISWL_Next_Stage_Prompt.md`](ISWL_Next_Stage_Prompt.md) | Development Agent handoff |

---

## Issue #31 status (planning context)

**Source dependency closed.** PSEGT/PDINT/PDINTTBL available under `QLA_Migration/Source/`. QUIKCOI/QUIKGCOI DBF layouts confirmed via QLAdmin Help. Implementation proceeds under follow-on issues for each QLA table.
