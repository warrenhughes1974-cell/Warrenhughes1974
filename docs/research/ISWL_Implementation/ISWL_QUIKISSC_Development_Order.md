# ISWL QUIKISSC Development Order

**Project:** LifePRO → QLAdmin — QUIKISSC (ISWL Surrender Charges)  
**Issue:** #33 — Phase 6  
**Version baseline:** v57.40  
**Date:** 2026-06-28  
**Mode:** Planning only  
**Readiness:** **READY AFTER SME CONFIRMATION**

---

## Context

Issue #31 (PR-1 through PR-4) is **CLOSED**. Issue #32 PR-5 QUIKUINT is **APPROVED** (32-row QuikUint emit).

**Phase 6 target:** QUIKISSC → `QuikIssc` (Help §7.144 — duration columns SCHG01–SCHG20)

---

## Recommended build sequence

```text
Phase 0 — SME sign-off  ☐ AWAITING SME (gates A–F forensically resolved)

  ◐ A: Source authority — OSLNS00XT/SLD000 → Rate_Table TYPE_CODE=SL (PDAGE SL rejected)
  ◐ B: Replicate hub schedule to 8 MPLANs (→ 8 rows)
  ✅ C: AGE=0 single all-age row — **CLOSED** (SME confirmed)
  ◐ D: UWCLASS=S → **SM** (established `UWCLASS_MAP`; PR-1–PR-4)
  ✅ E: SCHG15–20 blank — **CLOSED** (SME confirmed)
  ◐ F: Percent literal format (100.0000 = 100%; SCHG01–20 N(8.4))
  ✅ TP/TX excluded
  ✅ U7/U8 absent
  ✅ QuikIssc schema §7.144

  (◐ = forensically resolved; awaiting SME APPROVE/CORRECT in Issue_33_QUIKISSC_SME_Answers.md)

Phase 0b — Pointer decode research  ✅ COMPLETE

  ✅ SEGT_DATA decode for 659 CEN II SR/SL (Issue_33_Forensic_Pointer_Resolution.md)
  ✅ Join to Rate_Table SL rows documented
  ☐ Optional: validate vs policy surrender load on pilot policies
  ☐ Optional: client reference QuikIssc.dbf

Phase 6 — QUIKISSC  ★ Development Agent target — BLOCKED until Phase 0 sign-off

  ├── Add QuikIssc to rate_dbf_schema (Help §7.144)
  ├── New quikissc_loader.py — segment-gated duration pivot
  ├── Wire iswl_phase6 in rate_loader_config.json
  ├── PSEGT SR/SL gate (8/8)
  ├── Pivot DURATION 1..14 → SCHG01..SCHG14; SCHG15–20 blank
  ├── Dry-run: exactly 8 rows
  └── Validator iswl_quikissc_reconcile.py (V-ISSC-01–12)

Phase 6b — CSV emit (after validation PASS)

  ├── rate_loader_emit.py --csv-only includes QuikIssc.csv
  ├── Issue #31 + #32 regression unchanged
  └── Artifacts under Issue_Log_Items/Issue_33/output/Phase6_QUIKISSC/
```

---

## Prerequisites checklist

| # | Prerequisite | Status |
|---|--------------|--------|
| 1 | Issue #31 PR-1–PR-4 closed | ✅ |
| 2 | Issue #32 PR-5 QUIKUINT approved | ✅ |
| 3 | PSEGT extract in repo | ✅ |
| 4 | SR/SL 8/8 segment wiring | ✅ STRONG EVIDENCE |
| 5 | QuikIssc Help schema §7.144 | ✅ |
| 6 | Rate pointer decode | ❌ OPEN |
| 7 | SME gate closure doc | ❌ OPEN |
| 8 | Reference QuikIssc DBF (optional) | ❌ OPEN |

---

## File touch list (PR-6 — future)

| File | Action |
|------|--------|
| `qla_core/quikissc_loader.py` | **Create** |
| `qla_core/rate_dbf_schema.py` | Add QuikIssc |
| `qla_core/rate_dbf_writer.py` | QuikIssc writers |
| `qla_core/rate_pipeline.py` | Wire phase6 (minimal) |
| `qla_core/rate_validation.py` | QuikIssc family entry |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.json` | `iswl_phase6` |
| `plan_analysis/phase_r5_rate_loader/rate_loader_config.example.json` | Sync |
| `plan_analysis/phase_r5_rate_loader/rate_loader_emit.py` | QuikIssc emit |
| `tools/validators/iswl_common.py` | Phase 6 paths |
| `tools/validators/iswl_quikissc_reconcile.py` | **Create** |
| `Issue_Log_Items/Issue_33/Issue_33_Phase6_QUIKISSC_Implementation_Notes.md` | Post-dev |

**Do not modify:** Phase 1–5 loader logic beyond shared config/pipeline wiring.

---

## Config sketch (`iswl_phase6` — provisional)

```json
{
  "iswl_phase6": {
    "_note": "ISWL QUIKISSC — PSEGT SR/SL → surrender schedule → QuikIssc",
    "quikissc_enabled": false,
    "hub_segment_id": "659 CEN II",
    "parent_seg_type": "SR",
    "child_seg_type": "SL",
    "rate_source": "rate_table_sl",
    "rate_coverage_id": "659 CEN II",
    "rate_type_code": "SL",
    "emit_mode": "duration_pivot",
    "mplan_allowlist": ["1658C1", "1658CS", "1659C2", "1659CR", "1659CS", "1659SR", "1669SR", "1679CS"],
    "replicate_hub_to_all_mplans": true,
    "iss_cntry_default": "0000",
    "iss_state_default": "00",
    "schg_max_duration": 20
  }
}
```

**Enable only after SME gate closure.**

---

## Agent routing

| Agent | When |
|-------|------|
| **SME Review Agent** | Now — close Phase 0 gates |
| **Research Agent** | Phase 0b pointer decode if SME cannot answer Q2 |
| **Development Agent** | After `Issue_33_QUIKISSC_SME_Answers.md` marks **READY FOR DEVELOPMENT** |
| **Validation Agent** | After PR-6 implementation |

---

## Deferred (out of Phase 6 scope)

| Item | Track |
|------|-------|
| Expenses (UF/U1/U2/U3) | Issue TBD |
| QuikIsrr partial surrender | Separate |
| QuikIswl values | Separate |
| Production DBF / app.py | Separate integration issue |
