# Issue #36 — Planning Report

**Issue:** #36 — Modal Premium factors at policy level (`quikmstr`)  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — ready for Dependency Gate  
**Generated:** 2026-07-09  
**Agent:** Planning Agent (read-only analysis)

---

## 1. Executive Finding

Names-tab **Modal Premiums** require policy-level factors on **`quikmstr`**: `MSEMI`, `MQTRL`, `MMTHD`, `MMTHB` (QLAdmin Help NUMERIC 7.4). Current Output has these **blank on all 5,083 policies**, so the UI falls back to crude mode division (confirmed on `010148856C`: 19.23 → 9.62 / 4.81 / 1.60).

Issue **#21J** already loads **plan-level** factors onto `quikplan` and applies **PAC GL85-only** overrides to `MSEMI`/`MQTRL`. It did **not** copy plan factors onto every policy. LifePRO extracts still have **no** policy-level quote factors (per #21J Planning Correction).

**Recommended direction:** After `quikmstr` + `quikridr` emit, copy each policy’s phase-1 `MPLAN` → `quikplan` SEMI/QTRL/MTHD/MTHB into `quikmstr` MSEMI/MQTRL/MMTHD/MMTHB (**MMTHD and MMTHB are independent** — 91/141 plans differ), then apply the **two PAC special modes** from `docs/Policy Form Modal Premium Factors.xlsx` (quarterly **25%**, semiannual **50%**) so PAC wins on those fields. Do **not** change `MMODEPREM`, `quikridr` fees, or plan overlay logic.

**Doc note:** `docs/Copy of Premium Paid Fields.xlsx` is **Premiums Paid / Tax Basis** mapping (Non-ISWL vs ISWL sheets) — **not** modal-factor authority. Modal exceptions for the two PAC modes are in `docs/Policy Form Modal Premium Factors.xlsx` (annotations on plans `170858` / `17085M`).

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/? | Role for #36 |
|--------------|--------------|-------------|--------------|
| PPOLC | `PPOLC_PolicyMaster_Extract_*.csv` | Yes | Policy identity, `MODE_PREMIUM` → `MMODEPREM` (unchanged) |
| — | Policy-level modal factor % | **No** | Not in extracts (#21J confirmed) |

**Authoritative factor source for this issue (conversion-owned):**

| Source | File | Fields |
|--------|------|--------|
| Converted plan setup | `Output/quikplan.csv` | `PLAN`, `SEMI`, `QTRL`, `MTHD`, `MTHB` (from #21J mapping) |
| Client mapping (upstream of quikplan) | `Mapping/Modal_Premium_Factors_By_Plan.csv` | Same factor columns by `QL_PLAN` |
| Phase-1 plan on policy | `Output/quikridr.csv` | `MPOLICY`, `MPHASE=1`, `MPLAN` |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy number | PPOLC / quikmstr.MPOLICY | 100% | #25 padding |
| Mode premium | PPOLC.MODE_PREMIUM → MMODEPREM | High | Do not touch |
| Modal factor % | **Absent** in LifePRO extract | 0% | Use quikplan |
| Plan factors | quikplan SEMI/QTRL/MTHD/MTHB | **100%** (141/141 plans non-blank SEMI) | Copy target |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source |
|-------|-------|------|--------|--------|
| QuikMstr | MSEMI | NUMERIC | 7.4 | Help p.836 — Semi-annual modal factor |
| QuikMstr | MQTRL | NUMERIC | 7.4 | Help p.836 — Quarterly modal factor |
| QuikMstr | MMTHD | NUMERIC | 7.4 | Help p.836 — Monthly direct modal factor |
| QuikMstr | MMTHB | NUMERIC | 7.4 | Help p.836 — Monthly bank draft modal factor |

**Not targets:** `quikridr.MSEMIFEE` / `MQTRLFEE` / `MMTHDFEE` / `MMTHBFEE` (fee columns; client title was misleading).

**Repo references:**

| Location | Role |
|----------|------|
| `Sync_Rulebook_quikmstr.csv` | No rows for MSEMI/MQTRL/MMTHD/MMTHB (blank by default) |
| `qla_core/modal_premium_factors.py` | Plan overlay + PAC GL85 overrides + memos |
| `QLA_Migration/app.py` / root `app.py` | Calls `apply_pac_gl85_modal_overrides` after quikridr emit |
| `tools/validators/validate_issue21j_modal_factors.py` | Validates plan factors + PAC subset |

---

## 4. Required Source-to-Target Field Mapping

| Source | Source field | QLAdmin target | Transformation | Change? |
|--------|--------------|----------------|----------------|---------|
| quikplan via phase-1 MPLAN | SEMI | quikmstr.MSEMI | Copy as-is (percent scale e.g. 51.0140) | **Yes — new** |
| quikplan via phase-1 MPLAN | QTRL | quikmstr.MQTRL | Copy as-is | **Yes — new** |
| quikplan via phase-1 MPLAN | MTHD | quikmstr.MMTHD | Copy as-is | **Yes — new** |
| quikplan via phase-1 MPLAN | MTHB | quikmstr.MMTHB | Copy as-is | **Yes — new** |
| PAC GL85 override (#21J) | mode 3 → 25.0000 / mode 6 → 50.0000 | MQTRL / MSEMI | Apply **after** plan copy | **Preserve** |
| PPOLC | MODE_PREMIUM | MMODEPREM | Existing rulebook | **No** |

### Two PAC modes that differ from plan defaults (required)

Client workbook `docs/Policy Form Modal Premium Factors.xlsx` documents **two billing modes** that override plan factors on GL85 PAC policies:

| Special mode | Bill form | `MMODE` | Override field | Factor | Plan default (would be wrong) | Client sample policies (workbook) |
|--------------|-----------|---------|----------------|--------|-------------------------------|-----------------------------------|
| **PAC Quarterly** | PAC / `2` | `3` | `MQTRL` | **25.0000** (0.25) | 26.5000 | 010560185C, 010396186C, 010459011C |
| **PAC Semiannual** | PAC / `2` | `6` | `MSEMI` | **50.0000** (0.50) | 52.0000 | 010442216C, 010473868C, 010449334C, 010488273C |

Scope of override: plans **`170858`** / **`17085M`** only. Other factor columns on those policies still receive normal plan copy (`MMTHD`/`MMTHB` stay 9.0000 / 8.3333 — **not** equalized).

Current Output population: **4** PAC quarterly + **8** PAC semiannual candidates (includes workbook samples + additional fleet matches).

### Monthly Direct vs Monthly Draft (also different)

| Field | Source | Rule |
|-------|--------|------|
| `MMTHD` | quikplan.`MTHD` | Copy as-is — monthly **direct** |
| `MMTHB` | quikplan.`MTHB` | Copy as-is — monthly **bank draft** |

Do **not** copy MTHD into both, or average them. Example: `170858` → MMTHD=9.0000, MMTHB=8.3333.

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| quikmstr.MMODEPREM | PPOLC.MODE_PREMIUM | **No** |
| quikmstr.MMODE / MBILLFRM / etc. | PPOLC | **No** |
| quikridr.MPREM | ANN_PREM_PER_UNIT (#26) | **No** |
| quikridr.M*FEE | Existing | **No** |
| quikplan ANNL/SEMI/QTRL/MTHD/MTHB | #21J overlay | **No** (read only) |
| MPOLICY padding | format_qladmin_mpolicy (#25) | **No** |

---

## 5. Open Client Questions

| # | Question | Disposition for Development |
|---|----------|------------------------------|
| Q1 | Confirm factors are **percent of annual** (51.0140 = 51.014%) matching Help 7.4 and #21J mapping? | **Accepted assumption** — same scale as closed #21J / quikplan |
| Q2 | Populate all four factors on **every** policy (not only current billing mode)? | **Yes** — Names tab shows full grid; blank fields break UI |
| Q3 | Client title said quikridr — confirm target is quikmstr? | **Yes** — Help + UI evidence; document in Closure |
| Q4 | Expected Names-tab amounts after fix (plan% × annualized) vs today’s ÷mode? | **UAT** — Conversion populates factors; QLAdmin computes display |

No blocking client clarification required to implement factor copy.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Existing #25 `format_qladmin_mpolicy` when joining |
| Factor format | Preserve quikplan string precision (typically 4 decimals, e.g. `51.0140`) |
| Missing plan | Should not occur (0/5083 today); leave blank + log count if ever missing |
| PAC override | After copy: PAC + plan 170858/17085M + mode 3/6 → MQTRL=25.0000 / MSEMI=50.0000 |
| Blanks / zeros | Do not write `0` when plan factor exists; do not invent factors |

---

## 7. Memo / Text / Special Handling

Optional: #21J `[CONVERSION]` memos already document plan factors. **No memo change required** for #36 unless Risk wants a one-line note that policy-level quikmstr factors were populated. Default: **no memo change**.

---

## 8. Policy Number Key Handling

1. Join `quikmstr.MPOLICY` ↔ phase-1 `quikridr.MPOLICY` with padded keys  
2. Resolve `MPLAN` → `quikplan.PLAN`  
3. Orphans: log; do not invent factors  

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| quikmstr policies | 5,083 | Current Output |
| With phase-1 MPLAN | 5,083 | 100% |
| MPLAN in quikplan | 5,083 | 0 missing |
| Rows that would gain non-blank factors | **5,083** | All currently blank |
| PAC GL85 mode 3/6 override subset | 12 | Existing #21J path |

---

## 10. Sample Trace (3 policies)

| Policy | MPLAN | MMODEPREM | Before factors | After (proposed from quikplan) | Note |
|--------|-------|-----------|----------------|--------------------------------|------|
| 010148856C | 221END | 19.23 | blank | MSEMI=51.0140, MQTRL=26.0010, MMTHD=8.9964, MMTHB=8.9989 | Names-tab example |
| 010713704C | 1659C2 | 43.91 | blank | 52.5000 / 27.0000 / 9.1999 / 8.8018 | #21J census example |
| 010560185C | 170858 | 15.00 | blank | plan 52/26.5/9/8.3333 then **MQTRL→25.0000** (PAC Q) | PAC quarterly special mode |
| 010442216C | 170858 | 60.00 | blank | plan then **MSEMI→50.0000** (PAC S); MMTHD=9.0000 MMTHB=8.3333 | PAC semiannual special mode |

**Display expectation (UAT):** With factors present, Names-tab should stop using crude ÷2/÷4/÷12 and use QLAdmin’s factor-based modal grid (exact dollar math is QLAdmin runtime).

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Names-tab still wrong if QLAdmin expects decimal 0.51 not 51.01 | Medium | Match #21J / quikplan scale already accepted in UAT path |
| Overwriting intentional blank policy overrides | Low | No LifePRO policy overrides in extract; PAC is only known override |
| Stale Output missing even PAC overrides | Low | Re-batch after Development; validate PAC + fleet |
| Touching MMODEPREM accidentally | High if done | Explicitly exclude from write set |
| Confusing with quikridr fee fields | Low | Scope docs + validator on quikmstr only |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | **Yes** — quikplan + mapping + quikridr (no new LifePRO extract) |
| Field definitions confirmed | **Yes** — Help screenshot |
| Client scope clear | **Yes** — populate quikmstr factors for Names tab |
| Example policies available | **Yes** — 010148856C + screenshots |

---

## 13. Recommended Risk Agent Prompt

```
Risk Agent — Issue #36: Policy-level modal factors on quikmstr

Read AI_Agents/Risk_Agent.md, Issue_36_Planning_Report.md, Issue_36_Dependency_Gate.md.

Quantify before/after: all 5083 policies currently blank MSEMI/MQTRL/MMTHD/MMTHB;
simulate copy from quikplan via phase-1 MPLAN; then PAC GL85 overrides.
Do not change code. Issue Go / Conditional Go / No-Go for Development.
Preserve #25, #26, #21J plan overlay and PAC override behavior.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Add `apply_plan_modal_factors_to_quikmstr(mstr_df, quikridr_df, quikplan_df|path)` in `qla_core/modal_premium_factors.py` — copy SEMI→MSEMI, QTRL→MQTRL, MTHD→MMTHD, MTHB→MMTHB by phase-1 plan.
2. In `app.py` and `QLA_Migration/app.py`, after quikridr emit: **first** plan-factor copy, **then** existing `apply_pac_gl85_modal_overrides`.
3. Bump `APP_VERSION` in both app.py files.
4. Validator: `tools/validators/validate_issue36_quikmstr_modal_factors.py` — fleet non-blank rate, trace policies, PAC overrides, MMODEPREM unchanged vs baseline.
5. Do not modify Sync_Rulebook_quikmstr for these fields (post-emit enrichment, same pattern as PAC).

---

## Appendix

- Intake: `Issue_36_Intake_Summary.md`
- Evidence: `evidence/qladmin_help_quikmstr_modal_factors.png`, `evidence/policy_010148856C_names_tab_modal_premiums.png`
- Related: Issue #21J (closed v57.46), #26, #25
- References: QLAdmin Help QuikMstr p.836; `Modal_Premium_Factors_By_Plan.csv`
