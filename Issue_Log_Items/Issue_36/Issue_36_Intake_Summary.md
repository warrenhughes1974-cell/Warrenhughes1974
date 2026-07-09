# Issue #36 — Intake Summary

**Issue:** #36 — Modal Premium factors at policy level (`quikmstr`)  
**Client log ID:** 46 (Active)  
**Date:** 2026-07-09  
**Framework stage:** Intake complete (G0)  
**Status recommendation:** Planning  
**Owner:** Conversion (Warren) · **Assigned:** Warren · **Business status:** No-Go (Eric) until framework gates clear  
**Priority:** High (Names-tab Modal Premiums non-functional without factors)

---

## 1. Client / business symptom (verbatim + normalized)

**Verbatim (issue log):**

> Modal Premium factors in quikridr  
> We need to make sure we are getting the correct modal premiums in quikmstr.  
> This is in relation to 21J. When we dont have these factors in quikmstr the Modal Premiums on the Names tab do not work.

**Normalized:**

QLAdmin Policy Display → **Names** tab → **Modal Premiums** box requires policy-level modal factors on **`quikmstr`**:

| Field | Help description | Type |
|-------|------------------|------|
| `MSEMI` | Semi-annual modal factor | NUMERIC 7.4 |
| `MQTRL` | Quarterly modal factor | NUMERIC 7.4 |
| `MMTHD` | Monthly direct modal factor | NUMERIC 7.4 |
| `MMTHB` | Monthly bank draft modal factor | NUMERIC 7.4 |

Without these values populated, the Names-tab modal premium grid does not work correctly (falls back to crude mode division or blanks).

**Title mismatch note:** Client title says “in quikridr,” but symptom, Help schema, and UI all point to **`quikmstr`**. `quikridr` has fee fields (`MSEMIFEE` / `MQTRLFEE` / `MMTHDFEE` / `MMTHBFEE`), which are **not** the Names-tab modal factors. Intake scopes this issue to **`quikmstr`**.

---

## 2. Example policies / evidence

| Artifact | Path / note |
|----------|-------------|
| QLAdmin Help — QuikMstr modal factor fields | `evidence/qladmin_help_quikmstr_modal_factors.png` (p.836) |
| Policy Display Names tab — Modal Premiums | `evidence/policy_010148856C_names_tab_modal_premiums.png` |
| Trace policy | **`010148856C`** — Active, Mode 12, Mode Prem **19.23**, plan **`221END`** |

**Screen values on `010148856C` (Names tab):**

| Annl | Semi | Qtly | Mthly | Draft |
|------|------|------|-------|-------|
| 19.23 | 9.62 | 4.81 | 1.60 | 1.60 |

These match **simple division** of annual/mode premium (÷2 / ÷4 / ÷12), **not** plan factors currently on `quikplan` for `221END` (`SEMI=51.0140`, `QTRL=26.0010`, `MTHD=8.9964`, `MTHB=8.9989`).

**Current conversion output (intake measurement 2026-07-09):**

| Check | Result |
|-------|--------|
| `quikmstr` row count | 5,083 |
| Non-blank `MSEMI` / `MQTRL` / `MMTHD` / `MMTHB` | **0 / 0 / 0 / 0** (fleet-wide blank) |
| `010148856C` factors | all blank |
| PAC GL85 mode 3/6 candidates (21J override population) | 12 policies — also blank in current Output |

---

## 3. Suspected domain

| Domain | Assessment |
|--------|------------|
| Policy master (`quikmstr`) | **Primary** — target fields confirmed in Help |
| Plan setup (`quikplan` ANNL/SEMI/QTRL/MTHD/MTHB) | Related source of truth for factors (Issue #21J) |
| Rider (`quikridr`) | **Out of scope** for Names-tab factors (fee fields only) |
| Premium recalculation engine | Out of scope — populate factors; do not recompute `MMODEPREM` |

---

## 4. In scope / out of scope (first pass)

**In scope**

- Populate `quikmstr.MSEMI`, `MQTRL`, `MMTHD`, `MMTHB` so Names-tab Modal Premiums work.
- Align with Issue #21J plan-level factor mapping (`Modal_Premium_Factors_By_Plan.csv` / `quikplan` factors).
- Preserve / integrate PAC GL85 policy overrides already coded in `apply_pac_gl85_modal_overrides` (Issue #21J).
- Preserve `MMODEPREM` (Issue #26 / LifePRO `MODE_PREMIUM`) — do not overwrite.

**Out of scope (unless Planning proves otherwise)**

- Changing `quikridr` fee columns (`M*FEE`).
- Changing plan-level `quikplan` factor overlay logic (already closed under #21J) except as a read source.
- Recalculating or correcting `MMODEPREM` / Coverage-tab premium math beyond factor population.
- LifePRO runtime Premium Quote factors not present in extracts (documented under #21J Planning Correction).

---

## 5. Related issues

| Issue | Relationship |
|-------|----------------|
| **#21J** | Parent — plan-level factors on `quikplan` + PAC GL85 `MSEMI`/`MQTRL` overrides + memos. **Closed v57.46**, but fleet policy-level factor copy to `quikmstr` was **not** done (only PAC subset). This issue completes the policy-level gap Eric cites. |
| **#26** | `MMODEPREM` / `MPREM` — must not regress |
| **#25** | `MPOLICY` padding — must not regress |

---

## 6. Immediate blockers visible at intake

| Blocker? | Item | Notes |
|----------|------|-------|
| No | Field definitions | Confirmed via QLAdmin Help screenshot |
| No | Symptom / UI | Names-tab screenshot for `010148856C` |
| **Open for Planning** | Authoritative factor source for policy-level copy | Likely inherit from phase-1 `MPLAN` → `quikplan` factors (same as #21J mapping). Confirm scale: Help NUMERIC 7.4 vs plan factors stored as percent (e.g. 51.0140). |
| **Open for Planning** | Whether blank factors should be filled for **all** policies or only billed modes | Client says Names tab “do not work” without factors → default assumption: populate all four for every policy from plan. |
| Soft | Current Output blank including PAC overrides | Suggests either stale batch vs v57.46 code path, or override not persisting — Planning must verify call site + re-batch expectation. |

**No hard client-data blocker at Intake.** Proceed to Planning.

---

## 7. Artifact inventory

| Provided | Missing |
|----------|---------|
| Issue log row (ID 46 / #36) | Formal tracking sheet row (created with this intake) |
| Help schema screenshot (MSEMI/MQTRL/MMTHD/MMTHB) | LifePRO extract column for policy-level modal factors (known absent per #21J) |
| Names-tab screenshot `010148856C` | Client-signed factor scale confirmation (percent vs decimal) — may reuse #21J mapping |
| Relation to #21J | — |
| Current `quikmstr.csv` blank-factor proof | — |

---

## 8. Severity / owner

| Attribute | Value |
|-----------|-------|
| Severity | **High** — UI Modal Premiums broken fleet-wide when factors blank |
| Blast radius (expected) | `quikmstr` four factor columns only (+ preserve PAC override behavior) |
| Owner | **Conversion** |
| Client role | UAT on Names tab after Development; confirm factors match product expectations |

---

## 9. Gate G0 checklist

- [x] Issue folder created: `Issue_Log_Items/Issue_36/`
- [x] Intake summary written
- [x] Example policies listed (`010148856C`)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

**G0 status:** **PASS** — advance to Planning Agent.
