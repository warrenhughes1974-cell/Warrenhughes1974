# Issue #59 — Planning Report

**Issue:** #59 — Incorrect QL Status  
**Framework stage:** Planning Agent  
**Status:** Ready for Dependency Gate → (expected) Ready for Risk Review  
**Generated:** 2026-07-14  
**Intake reference:** `Issue_Log_Items/Issue_59/Issue_59_Intake_Summary.md`  
**Engine baseline:** current `QLA_Migration/Output/quikmstr.csv` (post #13/#49)  
**Code changes:** None (planning is read-only)  
**Model:** Cursor Grok 4.5 (locked Planning)

---

## 1. Executive Finding

Client No-Go is confirmed in the current batch: six Active LifePRO policies emit `MSTATUS=54` (Lapsed), and `010521213C` emits `41` (Paid Up) instead of Death Claim Pending.

Root cause is **one interceptor rule** in `app.py` / `QLA_Migration/app.py`: for any non-`T` contract, `PAID_UP_TYPE ∈ {PU,RU,ET,LE,LP,SP}` forces `PUT_*` and ignores `CONTRACT_CODE` / `CONTRACT_REASON`. That is correct for true NFO displays (PU/RU/ET/LE/SP → 41/45/44/42, all active 0–49), but wrong for:

1. **`PAID_UP_TYPE=LP` on `CONTRACT_CODE=A`** → `ST_PUT_LP` → **54** (inactive) while contract and PPBEN base are Active.  
2. **`PAID_UP_TYPE=PU` on `CONTRACT_CODE=S` + `DP`** → `ST_PUT_PU` → **41** while `ST_S_DP` → **50** already exists unused.

**Recommended direction (surgical, two narrow precedence tweaks — do not implement yet):**

| Rule | Proposed |
|------|----------|
| A | If `CONTRACT_CODE=A` and `PAID_UP_TYPE=LP`, use `A_` (→22), **not** `PUT_LP`. |
| B | If `CONTRACT_CODE=S` (or at least `S`+`DP`), use `S_{CONTRACT_REASON}` (→50 for DP), **not** PUT — mirror Issue #13 “contract status wins” for Suspended death-claim-pending. |

Issue #13 (`T` wins) and Issue #49 (later-active-phase override) remain unchanged. Estimated direct `MSTATUS` deltas: **6** (54→22) + **1** (41→50); cascade may refresh phase-1 `MPHSTAT` on rebatch via existing inherit.

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Notes |
|--------------|--------------|---------------------|-------|
| PPOLC | `PPOLC_PolicyMaster_Extract_20260630.csv` | Yes | Authority for contract status / PUT |
| PPBEN | `PPBEN_PolicyBenefit_Extract_20260630.csv` | Yes | Confirms base benefit Active; DP reason on 010521213C |

### Available source fields

| Field | Column | Notes |
|-------|--------|-------|
| Policy number | `POLICY_NUMBER` | Crosswalk + #25 pad |
| Contract status | `CONTRACT_CODE` | A / T / S |
| Contract reason | `CONTRACT_REASON` | DP for death claim pending |
| Paid-up / NFO marker | `PAID_UP_TYPE` | LP, PU, … |
| Benefit status | `STATUS_CODE` / `STATUS_REASON` | Corroboration only |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Role |
|-------|-------|------|------|
| `quikmstr` | `MSTATUS` | status code | Policy master status (primary fix) |
| `quikmstr` | `MSTATDATE` | date | Out of scope unless client requires DP date alignment |
| `quikridr` | `MPHSTAT` | status code | No direct edit; phase-1 may inherit corrected `MSTATUS` |

**Translation keys (already present):**

| Source_Code | QLA_Result | Meaning |
|-------------|------------|---------|
| `ST_A_` | 22 | Active |
| `ST_PUT_LP` | 54 | Lapsed (via PUT) |
| `ST_PUT_PU` | 41 | Paid Up |
| `ST_S_DP` | 50 | Death Claim Pending |

**Code path:** `app.py` ~6519–6530 (MSTATUS composite) → `ST_*` translate → Issue #49 override (~6718+).

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPOLC | `CONTRACT_CODE` + `CONTRACT_REASON` + `PAID_UP_TYPE` | `quikmstr.MSTATUS` | Composite → `ST_*` | **Yes** (precedence only) |
| PPBEN | `STATUS_CODE` | `quikridr.MPHSTAT` | Existing | No direct change |

### Proposed composite logic (Development blueprint — not executed)

Current:

```text
if CONTRACT_CODE == T:
    use T_{REASON}
else if PAID_UP_TYPE in {PU,RU,ET,LE,LP,SP}:
    use PUT_{PUT}
else:
    use {CODE}_{REASON}
```

Proposed:

```text
if CONTRACT_CODE == T:
    use T_{REASON}                         # Issue #13 unchanged
elif CONTRACT_CODE == S:
    use S_{REASON}                         # NEW — Death Claim Pending / suspended wins over PUT
elif CONTRACT_CODE == A and PAID_UP_TYPE == LP:
    use A_                                 # NEW — Active wins over PUT_LP
elif PAID_UP_TYPE in {PU,RU,ET,LE,LP,SP}:
    use PUT_{PUT}                          # unchanged for true NFO on Active
else:
    use {CODE}_{REASON}
```

**Why LP-only for Active (not all PUT):**  
`PUT_PU/RU/ET/LE/SP` map to **active** QL statuses (0–49). Only `PUT_LP` maps to **inactive** 54 while `CONTRACT_CODE` remains Active — that is the false-lapse defect. Broader “never use PUT on Active” would incorrectly clear Paid Up / ETI / RPU displays.

### Fields that must remain unchanged

| Target | Touch this issue? |
|--------|-------------------|
| MPOLICY padding (#25) | **No** |
| `quikridr.MPREM` (#26) | **No** |
| Issue #13 `T` precedence | **No** (preserve) |
| Issue #49 later-phase override | **No** (preserve; becomes no-op for these 6 after root fix) |
| `MNFOPT` / #57 | **No** |
| Rulebook CSV wholesale | **No** — interceptor only (optional: no translation row changes required) |

---

## 5. Open Client Questions

1. **Confirm Cohort A:** For Active contracts with `PAID_UP_TYPE=LP`, should QLAdmin show **Active (22)** (recommended), or is LP intentionally Lapsed even when LifePRO contract code is A?  
2. **Confirm Cohort B:** For `CONTRACT_CODE=S` + `CONTRACT_REASON=DP`, should QLAdmin show **50 Death Claim Pending** even if `PAID_UP_TYPE=PU` (recommended)?  
3. **Scope of S-wins:** Apply S-reason precedence for **all** Suspended contracts, or **only** `DP`? (Planning default: all `S`, since translation already keys `ST_S_*`.)  
4. **UAT acceptance:** Reload `quikmstr` (+ `quikridr` if phase-1 inherit refreshes) and verify the seven policies only?

**Planning assumption if Gate accepts without new client reply:** Eric’s tracker text is the business rule (Active vs Lapsed; Death Claim Pending vs current wrong status). Proceed to Risk on that basis; flag for explicit UAT sign-off.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) — unchanged |
| Status codes | Numeric via existing `Master_Value_Translation` `ST_*` rows |
| Dates | Do not change `MSTATDATE` in this issue unless Risk finds DP date required |
| Blanks | Preserve existing blank-reason `A_` / `S_` handling |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA  
2. `format_qladmin_mpolicy()` CHARACTER(10) (#25)  
3. Orphans: N/A — all seven resolve in Output

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| Client-cited policies | 7 | Tracker |
| Fleet A+LP with current `MSTATUS=54` | **6** | Equals client list (35 other A+LP already 22 via #49) |
| Fleet S+DP | **16** | PPOLC |
| S+DP with PUT forcing wrong status | **1** | `010521213C` only (`PU`) |
| Expected `MSTATUS` value changes under proposed rules | **7** | 6× 54→22; 1× 41→50 |
| Translation rows to add | **0** | `ST_A_`, `ST_S_DP` already exist |

---

## 10. Sample Trace (7 policies)

| Policy (QLA) | LifePRO | PPOLC | Before MSTATUS | After (proposed) | Notes |
|--------------|---------|-------|----------------|------------------|-------|
| 01122D991C | 901122D991 | A / LP | 54 | **22** | Single phase; #49 N/A |
| 014FG8217C | 9014FG8217 | A / LP | 54 | **22** | |
| 016FG8217C | 9016FG8217 | A / LP | 54 | **22** | |
| 01ML8171C | 901ML8171 | A / LP | 54 | **22** | Client wrote 01ML8171 |
| 01ML8250C | 901ML8250 | A / LP | 54 | **22** | Ph2=56; #49 cannot help |
| 01ML8522C | 901ML8522 | A / LP | 54 | **22** | |
| 010521213C | 9010521213 | S / DP / PU | 41 | **50** | `ST_S_DP` |

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Broader PUT change on Active NFO (PU/ET/…) | High if over-scoped | Limit Active exception to **LP only** |
| S-wins changes other Suspended reasons | Low (all current S are DP) | Risk Agent fleet scan of all `CONTRACT_CODE=S` |
| Phase-1 `MPHSTAT` still 54 until rebatch inherit | Medium | Rebatch `quikridr` or document UAT reload of both tables |
| Regression of #13 / #49 | Medium | Explicit preserve tests in validator |
| Client “Active” wording vs current 41 on 010521213C | Low | Explain Paid Up vs Active; fix still to 50 per LifePRO DP |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes |
| Field definitions confirmed | Yes |
| Client scope clear | Mostly — Eric text + recommended assumptions |
| Example policies available | Yes |
| #25 / #26 preserved in plan | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #59.

Read AI_Agents/Risk_Agent.md and AI_Agents/Templates/Risk_Report_Template.md.
Model: Cursor Grok 4.5 (locked). Do not code.

Produce before/after impact analysis for:
1) CONTRACT_CODE=A + PAID_UP_TYPE=LP → use ST_A_ (22) instead of ST_PUT_LP (54)
2) CONTRACT_CODE=S → use S_{CONTRACT_REASON} instead of PUT_* (010521213C: ST_S_DP → 50)

Preserve Issue #13 (T wins) and Issue #49 (later-active-phase).
Fleet-scan all A+LP and all S contracts. Go/no-go recommendation.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Surgically update MSTATUS composite interceptor in **both** `app.py` and `QLA_Migration/app.py` per §4.  
2. Bump `APP_VERSION` in both files.  
3. Do **not** change `Master_Value_Translation.csv` unless Risk finds a missing `ST_S_*` key.  
4. Add `tools/validators/validate_issue59_mstatus.py` asserting the seven traces + #13/#49 guards.  
5. Rebatch (or targeted emit) `quikmstr` (+ `quikridr` if inherit must refresh); copy modified tables to `Output/Test_Validation/` on Validation PASS.  
6. Stop after Development; Validation/Regression on Cursor Grok 4.5.

---

## Appendix

- Related: Issue #13, Issue #49, Intake Summary  
- Translation: `QLA_Migration/Mapping/Master_Value_Translation.csv`  
- Misfiled prior notes: `Issue_Log_Items/_worknotes/MUWCLASS_v5783_Implementation_Notes.md` (not this issue)
