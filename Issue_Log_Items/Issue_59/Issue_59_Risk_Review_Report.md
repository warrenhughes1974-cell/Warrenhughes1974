# Issue #59 — Risk Review Report

**Issue:** #59 — Incorrect QL Status (`quikmstr.MSTATUS`)  
**Framework stage:** Risk Agent  
**Status:** **GO** — Ready for Development (await explicit Stage 5 approval)  
**Fallback simulated:** Narrow Active+LP only + Suspended-reason wins  
**Generated:** 2026-07-14  
**Baseline engine:** `APP_VERSION` **v57.83**  
**Evidence:** `evidence/issue59_risk_mstatus_deltas.csv`  
**Simulation script:** `QLA_Migration/_risk_review_issue59_mstatus.py`  
**Code changes in this stage:** None (read-only)  
**Model:** Cursor Grok 4.5 (locked Risk)

---

## Go / No-Go Recommendation

**GO**

Blast radius is **bounded and homogeneous**: **7** policies change visible `quikmstr.MSTATUS` (6× `54→22`, 1× `41→50`). Issue #13 (`T` wins) and Issue #49 (later-active-phase) are preserved. No translation-row adds required. Recommend surgical interceptor update only.

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Output-visible change? |
|-------|---------|----------|------------------------|
| **`quikmstr.MSTATUS`** | Non-`T`: if `PAID_UP_TYPE∈{PU,RU,ET,LE,LP,SP}` → `PUT_*` | (1) `T` unchanged (#13); (2) **`S` → `S_{REASON}`**; (3) **`A`+`LP` → `A_`**; (4) else existing PUT / code_reason | **Yes — 7 policies** |
| `quikmstr.MSTATDATE` | unchanged | unchanged | No |
| `quikridr.MPHSTAT` | no direct edit | cascade via phase-1 inherit on rebatch | Indirect on same 7 |
| `Master_Value_Translation.csv` | `ST_A_`, `ST_PUT_LP`, `ST_S_DP`, `ST_PUT_PU` already present | **No row changes** | No |

### Proposed composite (Development blueprint)

```text
if CONTRACT_CODE == T:
    use T_{REASON}                         # Issue #13 — preserve
elif CONTRACT_CODE == S:
    use S_{REASON}                         # NEW — Suspended / DP wins over PUT
elif CONTRACT_CODE == A and PAID_UP_TYPE == LP:
    use A_                                 # NEW — Active wins over PUT_LP
elif PAID_UP_TYPE in {PU,RU,ET,LE,LP,SP}:
    use PUT_{PUT}                          # preserve true NFO displays
else:
    use {CODE}_{REASON}
```

Then existing `ST_*` translation → Issue #49 later-active-phase override (unchanged).

---

## 2. Premium / Related Fields Untouched

| Target | Touched? |
|--------|----------|
| MPOLICY padding (#25) | **No** |
| `quikridr.MPREM` / MMODPREM (#26) | **No** |
| `MNFOPT` / `MDIVOPT` (#21A / #57) | **No** |
| `MBILLDAY` (#47) | **No** |
| Modal factors (#36 / #58 fees) | **No** |
| Claims / rates / MUWCLASS | **No** |
| Sync rulebooks | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `app.py` / `QLA_Migration/app.py` ~6519–6530 | MSTATUS composite interceptor (**edit here**) |
| Same files — `ST_` translate + Issue #49 override | Downstream; do not redesign |
| `QLA_Migration/Mapping/Master_Value_Translation.csv` | Read-only; keys already exist |
| `tools/validators/validate_issue13_mstatus.py` | Regression guard (preserve) |
| `tools/validators/validate_issue49_mstatus.py` | Regression guard (preserve) |
| New `tools/validators/validate_issue59_mstatus.py` | Stage 6 |

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| PPOLC policies scanned | 5,084 |
| Interceptor provisional key changes (sim before≠after) | **42** |
| Of those, already correct in Output via #49 (A+LP → 22) | **35** |
| **Output-visible `MSTATUS` changes** | **7** |
| `CONTRACT_CODE=T` provisional changes | **0** |
| Active non-LP NFO (`PU/RU/ET/LE/SP`) changes | **0** |
| Missing `ST_*` translation for proposed keys | **0** (ignore 1 garbage PPOLC header-like row) |

### Output-visible transitions

| Before → After | Count | Population |
|----------------|------:|------------|
| **54 → 22** | **6** | Client false-lapse list (exact) |
| **41 → 50** | **1** | `010521213C` Death Claim Pending |
| Other | 0 | |

### Why 42 provisional but only 7 visible?

Fleet `A`+`LP` = **41**. Issue #49 already forced `MSTATUS=22` on **35** of them when a later phase was active. Interceptor today still builds `PUT_LP→54` provisionally for all 41; proposed rule makes provisional `A_→22` for all 41. UAT-visible delta is only the **6** that #49 could not fix. That is desirable (corrects root cause; #49 becomes redundant for this cohort).

### Suspended fleet

| `CONTRACT_CODE=S` | Count | Current → Proposed |
|-------------------|------:|--------------------|
| `DP` + blank PUT | 15 | 50 → 50 (no change) |
| `DP` + `PU` | 1 | **41 → 50** |
| Other S reasons | 0 | — |

All current Suspended contracts are `DP`. Broad “`S` wins” equals “`S`+`DP` wins” on today’s extract.

### Breakdown (provisional key changes)

| cc | put | sim_before | sim_after | count |
|----|-----|------------|-----------|------:|
| A | LP | 54 | 22 | 41 |
| S | PU | 41 | 50 | 1 |

Full list: `evidence/issue59_risk_mstatus_deltas.csv`.

---

## 5. Fallback Recommendation

| Option | Output-visible rows | Assessment |
|--------|--------------------:|------------|
| **A+B (Planning):** Active+LP→22 **and** S-reason wins | **7** | **Recommended** |
| A only (Active+LP) | 6 | Incomplete — leaves Death Claim Pending wrong |
| B only (S-reason) | 1 | Incomplete — leaves six false lapses |
| Exclude `LP` from PUT list globally (incl. when would apply under T) | n/a | **Reject** — `T` already wins; risk of unintended LP semantics elsewhere |
| Broader “never PUT on Active” | hundreds (PU/ET/RU/LE/SP) | **Reject** — destroys intentional NFO master status |

**Recommended:** Option A+B as specified in §1.

---

## 6. Trace Policies

| Policy (QLA) | LifePRO | PPOLC | Before | Proposed | Pass? |
|--------------|---------|-------|-------:|---------:|:-----:|
| 01122D991C | 901122D991 | A / LP | 54 | **22** | Yes |
| 014FG8217C | 9014FG8217 | A / LP | 54 | **22** | Yes |
| 016FG8217C | 9016FG8217 | A / LP | 54 | **22** | Yes |
| 01ML8171C | 901ML8171 | A / LP | 54 | **22** | Yes |
| 01ML8250C | 901ML8250 | A / LP | 54 | **22** | Yes |
| 01ML8522C | 901ML8522 | A / LP | 54 | **22** | Yes |
| 010521213C | 9010521213 | S / DP / PU | 41 | **50** | Yes |

Phase-1 `MPHSTAT` today matches wrong master on these rows (54 or 41). After rebatch, inherit/`A→22` should align phase 1 with corrected `MSTATUS` (no direct `MPHSTAT` code change).

---

## 7. Top Changes

Status codes are categorical — all seven deltas are the material set. No numeric magnitude ranking.

| Policy | Before | After |
|--------|-------:|------:|
| six Active+LP | 54 | 22 |
| 010521213C | 41 | 50 |

---

## 8. Material Calculation Impact

| Effect | Intentional? |
|--------|--------------|
| Six policies stop appearing Lapsed while LifePRO Active | **Yes** — client No-Go |
| `010521213C` shows Death Claim Pending (50) not Paid Up | **Yes** — client No-Go |
| 35 A+LP already at 22 via #49 stay 22 | **Yes** — no UAT churn |
| Active Paid Up / ETI / RPU / SP displays | **Unchanged** |
| Terminated (#13) population | **Unchanged** |

Side effect: phase-1 `MPHSTAT` on the seven will refresh on `quikridr` rebatch. UAT should reload **both** `quikmstr` and `quikridr` (or full batch).

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — untouched |
| Issue #26 MPREM / MMODPREM | **Preserved** — untouched |
| Issue #13 `T` termination-first | **Preserved** — first branch unchanged; sim shows **0** T deltas |
| Issue #49 later-active-phase | **Preserved** — runs after interceptor; 35 prior fixes remain 22 |
| Issue #57 NFO on 010521213C | **Preserved** — `MNFOPT` not in change set; only `MSTATUS` 41→50 |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] Traces: six policies `MSTATUS=22`; `010521213C` `MSTATUS=50`
- [ ] Non-candidate: sample Active+`PU`/`ET`/`RU` unchanged vs pre-fix baseline
- [ ] Issue #13 samples still termination-correct (e.g. prior 010516211C / 011101663C pattern)
- [ ] Issue #49 samples still later-phase override (e.g. 01ML8007C / 018252C pattern)
- [ ] `quikmstr` row count stable (~5,083)
- [ ] No blank `MSTATUS` introduced
- [ ] MPOLICY padding unchanged on short keys (`01ML8171C`)
- [ ] `quikridr.MPREM` unchanged on traces
- [ ] Phase-1 `MPHSTAT` on the seven aligns with corrected master after rebatch
- [ ] Publish modified tables to `Output/Test_Validation/` on PASS

---

## 11. Recommended Development Agent Task

```
Issue #59 is approved for Development after user says so.

Switch to Composer 2.5. Read AI_Agents/Development_Agent.md and
Issue_59_Risk_Review_Report.md / Issue_59_Planning_Report.md.

Surgical only in app.py AND QLA_Migration/app.py MSTATUS composite interceptor:
1) After CONTRACT_CODE==T branch (Issue #13), add CONTRACT_CODE==S → S_{REASON}
2) Before generic PUT list, if CONTRACT_CODE==A and PAID_UP_TYPE==LP → A_
3) Keep existing PUT / else branches
4) Do NOT change Master_Value_Translation.csv, rulebooks, #49 block, #25/#26
5) Bump APP_VERSION in BOTH app.py files (from v57.83 → next)
6) Add tools/validators/validate_issue59_mstatus.py for the 7 traces + #13/#49 guards
7) Stop after Development; do not claim Validation complete
```

---

## Appendix

- Evidence CSV: `Issue_Log_Items/Issue_59/evidence/issue59_risk_mstatus_deltas.csv`
- Simulation: `QLA_Migration/_risk_review_issue59_mstatus.py`
- Related closed fixes: Issue #13 (v57.48), Issue #49 (v57.71)
- Client wording note: tracker said “Active” for `010521213C` in QLAdmin; current batch shows **Paid Up (41)** — fix still targets LifePRO Death Claim Pending → **50**
