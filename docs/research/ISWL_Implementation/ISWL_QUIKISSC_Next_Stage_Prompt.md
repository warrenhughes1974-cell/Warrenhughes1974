# ISWL QUIKISSC — Next Stage Prompt

**Issue:** #33 — Phase 6 QUIKISSC  
**Date:** 2026-06-28  
**Current readiness:** **READY AFTER SME CONFIRMATION**

---

## For SME Review Agent (run first)

```
SME Review Agent — Issue #33 QUIKISSC Gate Closure

Review Issue_Log_Items/Issue_33/Issue_33_SME_Questions.md

Close gates G1–G7 using:
  - Issue_33_Research_Summary.md
  - Issue_33_Blockers.md
  - docs/research/ISWL_Implementation/ISWL_QUIKISSC_*.md
  - QLAdmin Help §7.144 (QuikIssc schema)
  - PSEGT extract SR/SL payloads on 659 CEN II

Deliver: Issue_33_QUIKISSC_SME_Answers.md
Upgrade readiness to READY FOR DEVELOPMENT when all blocking gates closed.

Do NOT write loader code.
```

---

## For Development Agent (after SME closure only)

```
Development Agent — PR-6 Phase 6 QUIKISSC

Issue #33 planning is complete and SME gates are CLOSED.

Begin PR-6 development.

Target: QUIKISSC → QuikIssc.csv

Do NOT modify Issue #31 Phase 1–4 loader behavior.
Do NOT modify Issue #32 Phase 5 QUIKUINT behavior.
Do NOT begin expense setup.
Do NOT implement QuikIsrr.

Reference documentation:
  Issue_Log_Items/Issue_33/Issue_33_QUIKISSC_SME_Answers.md
  docs/research/ISWL_Implementation/ISWL_QUIKISSC_Implementation_Blueprint.md
  docs/research/ISWL_Implementation/ISWL_QUIKISSC_Table_Design.md
  docs/research/ISWL_Implementation/ISWL_QUIKISSC_Validation_Strategy.md
  docs/research/ISWL_Implementation/ISWL_QUIKISSC_Development_Order.md

Approved Transform (pending SME — replace with signed transform):
  PCOVRSGT → PSEGT(SR) → PSEGT(SL) on 659 CEN II
  → Rate_Table TYPE_CODE=SL (after pointer proof)
  → pivot DURATION → SCHG01..SCHGN
  → QuikIssc for each ISWL MPLAN

Validation: V-ISSC-01 through V-ISSC-12

Post-implementation:
  python tools/validators/iswl_quikissc_reconcile.py
  python tools/validators/iswl_quikuint_reconcile.py
  python tools/validators/iswl_quikgcoi_reconcile.py
  python tools/validators/iswl_quikcoi_reconcile.py
  python tools/validators/iswl_quikgps_reconcile.py
  python tools/validators/iswl_quikcvs_reconcile.py

Stop after PR-6.
```

---

## For Validation Agent (after PR-6)

```
Validation Agent — PR-6 Phase 6 QUIKISSC Review

Perform independent validation review per ISWL_QUIKISSC_Validation_Strategy.md.

Confirm:
  - V-ISSC-01 through V-ISSC-12
  - Phase 1–5 regression unchanged
  - No TP/TX sourcing
  - SR/SL hierarchy proof in loader status

Final recommendation: APPROVE PR-6 | APPROVE WITH NOTES | REJECT / FIX REQUIRED

Do NOT implement code.
Stop after PR-6 validation.
```

---

## Key anchors (do not change without SME)

| Item | Value |
|------|-------|
| Hub segment | `659 CEN II` |
| Segment types | SR (parent), SL (child) |
| Rate source | `Rate_Table TYPE_CODE=SL` (via `OSLNS00XT`/`SLD000`); PDAGE SL rejected (zero) |
| Excluded | U7, U8, TP, TX, PAAGERAT, PDAGE SL |
| QLAdmin table | `QuikIssc` Help §7.144 |
| Index key | PLAN + GENDER + UWCLASS + BAND + ISSCNTRY + ISSUEST |
| ISWL MPLANs | 8 (same fleet as QUIKUINT) |
| Expected row count | **8** (forensic — duration-only variation) |
| UWCLASS mapping | Source `S` → **`SM`** (established `UWCLASS_MAP`) |
| SCHG mapping | SCHG01–14 ← durations 1–14; SCHG15–20 blank (**SME closed Gate E**) |
| AGE | `0` single all-age row (**SME closed Gate C**) |
| Percent format | Percent literal (`100.0000` = 100%) |
| SME follow-up | `Issue_Log_Items/Issue_33/Issue_33_QUIKISSC_SME_Followup_Answers.md` |

---

## Planning package index

| Document | Path |
|----------|------|
| Research summary | `Issue_Log_Items/Issue_33/Issue_33_Research_Summary.md` |
| SME questions | `Issue_Log_Items/Issue_33/Issue_33_SME_Questions.md` |
| Forensic pointer resolution | `Issue_Log_Items/Issue_33/Issue_33_Forensic_Pointer_Resolution.md` |
| SME sign-off package | `Issue_Log_Items/Issue_33/Issue_33_QUIKISSC_SME_Answers.md` |
| Blockers | `Issue_Log_Items/Issue_33/Issue_33_Blockers.md` |
| Blueprint | `docs/research/ISWL_Implementation/ISWL_QUIKISSC_Implementation_Blueprint.md` |
| Table design | `docs/research/ISWL_Implementation/ISWL_QUIKISSC_Table_Design.md` |
| Validation | `docs/research/ISWL_Implementation/ISWL_QUIKISSC_Validation_Strategy.md` |
| Dev order | `docs/research/ISWL_Implementation/ISWL_QUIKISSC_Development_Order.md` |
