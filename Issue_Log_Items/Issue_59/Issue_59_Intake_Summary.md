# Issue #59 — Intake Summary

**Issue:** #59 — Incorrect QL Status  
**Date:** 2026-07-14  
**Framework stage:** Intake complete (G0)  
**Status recommendation:** Planning  
**Owner:** Conversion (Warren) · **Reporter:** Eric · **Business status:** No-Go (unchanged)  
**Model:** Cursor Grok 4.5 (locked Intake)

---

## Folder note

`Issue_Log_Items/Issue_59/` previously held **MUWCLASS / cash-value** implementation notes (v57.83). That work is **not** this client Issue #59. Those notes were relocated to:

`Issue_Log_Items/_worknotes/MUWCLASS_v5783_Implementation_Notes.md`

This folder is now reserved for **Incorrect QL Status** per the 7/14/2026 client tracker row.

---

## Client symptom (verbatim)

> 6 Policies are showing as Lapsed in QLAdmin, but are active on the 6/30/26 Extract. Policy Numbers are 01122D991C, 014FG8217C, 016FG8217C, 01ML8171, 01ML8250C, and 01ML8522C. There is one policy that is Active in QLAdmin, but Death Claim Pending in LifePRO. Policy Number is 010521213C.

---

## Normalized symptom

Two cohorts, same domain (`quikmstr.MSTATUS`):

| Cohort | Client claim | Current `quikmstr.MSTATUS` (Output) | LifePRO 6/30 extract |
|--------|--------------|--------------------------------------|----------------------|
| **A — false Lapse** | QLAdmin Lapsed; extract Active | **54** Lapsed on all 6 | PPOLC `CONTRACT_CODE=A`; PPBEN base `STATUS_CODE=A` |
| **B — missing Death Claim Pending** | QLAdmin Active; LifePRO Death Claim Pending | **41** Paid Up (not 22 Active) | PPOLC `CONTRACT_CODE=S`, `CONTRACT_REASON=DP`, `PAID_UP_TYPE=PU`; PPBEN `STATUS_CODE=A`, `STATUS_REASON=DP` |

Policy key notes:

| Client ID | QLAdmin `MPOLICY` | LifePRO `POLICY_NUMBER` |
|-----------|-------------------|-------------------------|
| 01122D991C | `01122D991C` | `901122D991` |
| 014FG8217C | `014FG8217C` | `9014FG8217` |
| 016FG8217C | `016FG8217C` | `9016FG8217` |
| 01ML8171 | ` 01ML8171C` (#25 pad) | `901ML8171` |
| 01ML8250C | ` 01ML8250C` | `901ML8250` |
| 01ML8522C | ` 01ML8522C` | `901ML8522` |
| 010521213C | `010521213C` | `9010521213` |

---

## Suspected domain

**Policy status** — `quikmstr.MSTATUS` (and indirectly phase-1 `quikridr.MPHSTAT` via inherit).

Not claims tables, not rates, not MUWCLASS.

---

## Intake verification (read-only, 2026-07-14)

### Cohort A — Active + `PAID_UP_TYPE=LP`

All six share:

| Field | Value |
|-------|-------|
| PPOLC `CONTRACT_CODE` | **A** |
| PPOLC `PAID_UP_TYPE` | **LP** |
| PPOLC `CONTRACT_REASON` | blank |
| PPBEN base `STATUS_CODE` | **A** |
| Emitted `MSTATUS` | **54** |

Converter interceptor (`app.py` MSTATUS composite): for non-`T` contracts, if `PAID_UP_TYPE ∈ {PU,RU,ET,LE,LP,SP}`, emit `PUT_{put}` → `ST_PUT_LP` → **54**.

`ST_A_` → **22** exists but is never used for these rows because **LP wins**.

**Issue #49 overlap:** Fleet `CONTRACT_CODE=A` + `PAID_UP_TYPE=LP` = **41** policies. Of those, **35** already show `MSTATUS=22` via the Issue #49 later-active-phase override. The **6** cited policies have no later phase in 0–49 (phase 1 shows 54; `01ML8250C` phase 2 is 56), so #49 correctly does **not** override — root cause remains PUT_LP on Active.

### Cohort B — Suspended Death Claim Pending

| Field | Value |
|-------|-------|
| PPOLC `CONTRACT_CODE` | **S** |
| PPOLC `CONTRACT_REASON` | **DP** |
| PPOLC `PAID_UP_TYPE` | **PU** |
| Translation `ST_S_DP` | **50** (exists, unused) |
| Emitted `MSTATUS` | **41** via `ST_PUT_PU` |

Client said “Active” in QLAdmin; current batch shows **Paid Up (41)**. Same wrong-precedence class: PUT over contract status/reason. `ST_S_DP→50` is already in `Master_Value_Translation.csv`.

Fleet `CONTRACT_CODE=S` + `CONTRACT_REASON=DP`: **16** policies; **15** have blank `PAID_UP_TYPE` (would already take `ST_S_DP`); **only this one** has `PU` and is forced to 41.

---

## In scope / out of scope (first pass)

| In scope | Out of scope |
|----------|--------------|
| `quikmstr.MSTATUS` precedence for Active+LP and Suspended+DP | Claims `CLAIMSTAT` / quikclms |
| Phase-1 `MPHSTAT` only as cascade of corrected `MSTATUS` inherit | Redesign of all PUT / NFO statuses |
| Preserve Issue #13 (`T` termination-first) and Issue #49 (later-active-phase) | MUWCLASS / cash-value work (separate notes) |
| | Wholesale rewrite of `Master_Value_Translation.csv` |

---

## Related issues

| Reference | Relationship |
|-----------|--------------|
| **#13** (CLOSED v57.48) | Same interceptor; fixed `T` vs PUT. This issue is the **non-T** side (A+LP, S+DP). |
| **#49** (CLOSED v57.71) | Mitigated 35 of 41 A+LP via later-phase override; **does not cover** these 6. |
| **#57** | Touched `010521213C` for NFO; not status precedence. |
| **#25 / #26** | Must not regress MPOLICY padding / MPREM. |

---

## Artifact inventory

| Artifact | Status |
|----------|--------|
| Client tracker row (7/14/2026, No-Go, Eric→Warren) | Provided |
| Example policies | Provided (7) |
| 6/30/2026 PPOLC / PPBEN in `QLA_Migration/Source/` | Present |
| Current `quikmstr.csv` / `quikridr.csv` | Present — symptom confirmed |
| Screenshots | Not provided (not required — measurable in Output) |
| Master tracking sheet row for #59 | Missing — add on Intake |

---

## Immediate blockers

None for Intake. Planning can proceed with confirmed sources and measurable before-state.

**Open business confirmation (for Planning / Gate):** Confirm that:

1. Active contract + `PAID_UP_TYPE=LP` should display **Active (22)**, not Lapsed (54).  
2. `CONTRACT_CODE=S` + `CONTRACT_REASON=DP` should display **Death Claim Pending (50)** even when `PAID_UP_TYPE=PU`.

---

## Severity / owner

| Item | Value |
|------|-------|
| Severity | High (No-Go; false lapse / wrong claim-pending status) |
| Owner | **Conversion** |
| Client data gap | None |

---

## Gate criteria (G0)

- [x] Issue folder created under `Issue_Log_Items/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

**Next agent:** Planning Agent (Cursor Grok 4.5)
