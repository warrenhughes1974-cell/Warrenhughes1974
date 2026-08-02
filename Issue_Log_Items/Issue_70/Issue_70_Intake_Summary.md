# Issue #70 — Intake Summary

**Issue:** #70 — QuikPlan `LOANINTX` Advance/Arrears authority (CSO guidance needed)  
**Framework stage:** Intake Agent (G0) — **refreshed 2026-08-02** (prior Intake 2026-07-14 retained below)  
**Status after this Intake refresh:** Ready for Planning (tracking sheet status **not** changed this session)  
**Generated:** 2026-07-14 · **Addendum:** 2026-08-02  
**Model:** Cursor Grok 4.5 (locked)  
**Owner:** Client / CSO (codebook authority) · Conversion (emit once rule locked)  
**Priority:** Go-No Go — drives plan-file loan interest timing and QuikLoan `MLOANINTX`  
**Reporter chain:** Chris (invalid plan value) → conversion analysis 2026-07-14 → CSO extract evidence 2026-08-02  

---

## Client symptom (verbatim + normalized)

**Verbatim (original):** Chris reported QuikPlan `LOANINTX` cannot be `2` (invalid). QLAdmin accepts only **`A`** (Interest in Advance) or **`R`** (Interest in Arrears).

**Normalized (current):** Plan catalog must emit valid `LOANINTX ∈ {A, R}` for every QuikPlan row. Conversion interim (v57.89) forces fleet **`A`** (141/141) so the plan file loads. That interim remains **unconfirmed as product truth** until Advance/Arrears is sourced from LifePRO coverage setup (or CSO explicitly accepts fleet Advance). Related QuikLoan `MLOANINTX` follows QuikPlan per Issue #32.

---

## Current conversion posture (unchanged this Intake)

| Item | Detail |
|------|--------|
| Engine | v57.89 — `_normalize_quikplan_loanintx` in `qla_core/quikplan_converter.py` |
| Rulebook | `Sync_Rulebook_quikplan.csv` default `LOANINTX=A`, `SKIP_TRANSLATION` |
| Governance | `QLA_Migration/Data_Goverence.txt` — LOANINTX must be A or R, default A |
| QuikLoan | Looks up QuikPlan `LOANINTX`; invalid/missing → fallback `A` (`quikloan_derivation_rules.json`) |
| Output now | `QLA_Migration/Output/quikplan.csv` — **141 / 141 = A** |
| Notes | `Issue_70_Implementation_Notes.md` — interim emit; awaiting CSO |

PLOAN `INT_METHOD=D` and `INTEREST_TYPE=F` remain **rejected** as A/R sources (Issue #32).

---

## CSO evidence addendum (2026-08-02) — repo-verified

User-supplied CSO reading of LifePRO extracts; spot-checked against `QLA_Migration/Source/` package dated **20260630**.

### PCOVR — `LOAN_ADV_ARREARS` (Excel column CJ)

| Source | `QLA_Migration/Source/PCOVR_Coverage_Extract_20260630.csv` |
|--------|-------------------------------------------------------------|
| Column | `LOAN_ADV_ARREARS` (field index 88 = Excel **CJ**) |
| Rows | 142 (incl. header underline row) |

| Value | Count | CSO / Intake reading |
|-------|------:|----------------------|
| `0` | 129 | **In Advance** → candidate QuikPlan `A` |
| `N` | 8 | **In Advance** (same family as `0`) → candidate `A` |
| `1` | 4 | **In Arrears** → candidate QuikPlan `R` |

**Arrears (`1`) coverages only (SAL family):**

| COVERAGE_ID | POLICY_FORM_NUM | LOANS_AVAILABLE | Crosswalk QuikPlan |
|-------------|-----------------|-----------------|--------------------|
| SAL OL | *(blank)* | Y | `1SALOL` |
| SAL ML | SAL ML | Y | `1SALML` |
| SAL MULTPL | SAL ML | Y | `1SALMI` |
| SAL ADB | SAL ADB | N | `9SLADB` |

User note (“only SAL OL and SAL ML forms”) matches the **form family**; extract also flags **SAL MULTPL** (form SAL ML) and **SAL ADB**.

`N` rows are non-SAL coverages (DISCHO*, L15/L16/L17 BASE) with blank `LOANS_AVAILABLE` — treat as Advance candidates pending Planning codebook lock.

### PLOAN — `INT_METHOD` (column M)

| Source | `QLA_Migration/Source/PLOAN_LoanInformation_Extract_20260630.csv` |
|--------|-------------------------------------------------------------------|
| `INT_METHOD` | **`D` fleet-wide** (94,151 data rows; 1 underline) |
| SAL loan rows | **0** — no PLOAN rows with SAL* `PLAN_CODE` |
| SAL policies (PPBEN) | 163 policies on SAL OL/ML/MULTPL/ADB; **0** of those appear in PLOAN |

Confirms: (1) PLOAN still cannot supply A/R; (2) Arrears-coded SAL coverages currently have **no in-force loan population**.

### Prior UI / #32 evidence (still valid)

| Item | Reference |
|------|-----------|
| Sample UI Advance | `9010331768` / `010331768C` (Issue #32 screenshot) |
| #32 MLOANINTX review | `Issue_Log_Items/Issue_32/Issue_32_MLOANINTX_Source_Review.md` — rejected PLOAN F/D; QuikPlan intended |
| #104 coupling | Claim/surrender interest UAT may depend on Advance timing; do not silently reopen #32/#104 in #70 |

---

## Suspected domain

**Plan setup / rates** — QuikPlan `LOANINTX`; downstream QuikLoan `MLOANINTX` via existing #32 lookup (no QuikLoan principal/balance change).

---

## In scope / out of scope (Intake refresh)

| In scope | Out of scope |
|----------|----------------|
| Lock LifePRO → QuikPlan `LOANINTX` authority (PCOVR `LOAN_ADV_ARREARS` codebook) | Changing loan balances / QuikLoan principal math (#32) |
| Decide whether SAL Arrears plans emit `R` despite zero loans | Reopening #104 claim/surrender interest settlement |
| After rule lock: emit A/R on QuikPlan (+ QuikLoan inherits) | Mapping PLOAN `INT_METHOD`/`INTEREST_TYPE` to A/R |
| Document join: PCOVR `COVERAGE_ID` → Master_Crosswalk → QuikPlan `PLAN` | Inventing Adv/Arr from PLOAN F/D |

---

## Assumptions (Intake — must be confirmed in Planning / CSO)

1. PCOVR `LOAN_ADV_ARREARS` is the LifePRO **product** Advance/Arrears switch (not a UI-only flag).
2. Codebook hypothesis: `0` and `N` → `A`; `1` → `R`.
3. Plan catalog should reflect product setup even when no loans exist on Arrears plans (SAL).
4. Fleet interim `A` remains correct for all non-`1` coverages under that codebook.
5. Formal written CSO “fleet Advance” email is **not** required to enter Planning if extract authority is accepted; may still be required before Closure if Risk demands it.

---

## Unresolved questions (for Planning / CSO)

1. Confirm codebook: do both `0` and `N` mean Advance? Any third meaning for blank/other?
2. Emit `R` for all four Arrears coverages (SAL OL, SAL ML, SAL MULTPL, SAL ADB), or only base forms SAL OL / SAL ML?
3. Is zero-loan Arrears still required on QuikPlan for catalog fidelity, or may Conversion keep `A` with a documented exception?
4. Does CSO treat this extract reading as **final authority**, or is a short written confirmation still needed?
5. Any interaction with #104 Advance settlement UAT if only SAL would flip to `R` (no active loans → likely **no operational impact**)?

---

## Acceptance criteria (draft for Planning to harden)

1. Every QuikPlan row has `LOANINTX` ∈ {`A`,`R`} (governance already requires this).
2. Documented source rule: PCOVR `LOAN_ADV_ARREARS` → `LOANINTX` (or explicit CSO fleet-`A` waiver with rationale).
3. Arrears population (if any) limited to CSO-approved coverages; non-candidates remain `A`.
4. QuikLoan `MLOANINTX` continues to follow QuikPlan lookup + `A` fallback (#32); no PLOAN A/R invent.
5. Validator / accountability can prove Output matches the locked rule (G7 before Closure).

---

## Related issues

- **#32** — QuikLoan mapping; LOANINTX fallback A; invalid staged `22` history
- **#44** — QuikLoan latest-row selection (closed; unrelated to A/R)
- **#104** — Claim/surrender loan interest settlement UAT; may ask whether plan timing is wrong — keep coupled but out of #70 emit scope unless SME expands

---

## Immediate blockers

| Prior blocker (2026-07-14) | Status after CSO evidence |
|----------------------------|---------------------------|
| No LifePRO extract field maps to `LOANINTX` A/R | **Lifted for Planning** — PCOVR `LOAN_ADV_ARREARS` is the candidate source |
| Need CSO fleet Advance vs Arrears plan list | **Partially met** — extract supplies candidate Arrears list (SAL*); codebook still needs Planning lock / optional CSO confirm |

**No Intake-stopping blocker remains.** Symptom, examples, owner, and source path are known.

---

## Artifact inventory

| Provided | Missing / deferred |
|----------|-------------------|
| Chris invalid `2`/`22` symptom | Formal CSO email (optional if extract accepted) |
| #32 screenshot Advance on `9010331768` | LifePRO field help text for `LOAN_ADV_ARREARS` (nice-to-have) |
| PCOVR 20260630 + PLOAN 20260630 in Source | — |
| User CSO reading (0/N Advance, 1 Arrears; SAL; no loans) | Written confirm of `N`==Advance if Risk requires |
| Current Output 141/141 `A` + Implementation Notes | — |

---

## Severity / owner

| | |
|--|--|
| **Severity** | Go-No Go (plan load + loan interest timing) |
| **Owner** | Client/CSO for codebook authority; Conversion for emit |
| **Regression risk if wrong** | Medium on SAL plans only if `R` omitted or over-applied; low on active loan fleet if only SAL flips and SAL has zero loans |

---

## Intake outcome / recommendation for Planning

**G0 Intake Complete — proceed to Planning.**

New CSO extract evidence is **sufficient to leave Intake** and map a source-driven `LOANINTX` rule. It is **not** by itself a Closure waiver: Planning should lock the codebook and join path; Risk/Dependency Gate should decide whether a one-line CSO confirm is still required before Development.

**Planning should focus on:**

1. Proposed mapping: `PCOVR.LOAN_ADV_ARREARS` → QuikPlan `LOANINTX` via `COVERAGE_ID` → `Master_Crosswalk` → `PLAN`.
2. Candidate emit: `0`/`N` → `A`; `1` → `R` for SAL OL / SAL ML / SAL MULTPL / SAL ADB (`1SALOL`, `1SALML`, `1SALMI`, `9SLADB`).
3. Explicit decision: keep current fleet-`A` interim vs emit the four `R` plans (zero-loan impact note).
4. Keep #32 QuikLoan lookup unchanged; do not touch #104 unless Planning finds coupling.

**Do not start Development** until Planning → Dependency Gate → Risk Go and user Development approval (framework).

---

## Gate Criteria (G0 — Intake Complete)

- [x] Issue folder exists under `Issue_Log_Items/Issue_70/`
- [x] Intake summary written / refreshed
- [x] Example policies listed (`9010331768`; SAL coverages as Arrears candidates; none provided for loan activity on SAL)
- [x] Owner and priority assigned
- [x] No code, Output, rulebook, or issue-status changes made this Intake

---

## Historical Intake (2026-07-14) — preserved

Original framing before PCOVR authority was identified:

- QuikPlan rulebook defaults `LOANINTX` to **`A`**; QuikLoan falls back to **`A`**.
- Belief at the time: **LifePRO extract does not supply Advance/Arrears** (PLOAN F/D only).
- Historical bad value `22` was mistranslation of default `A` through status map `A→22`, truncating to `2` in C(1).
- **Interim:** fleet `A` for loadability pending CSO guidance.
- **Blocker then:** no extract field + need CSO fleet vs Arrears list.

That blocker set is superseded by the 2026-08-02 addendum above for Planning entry; interim emit facts remain accurate until a later Development approval changes code/Output.
