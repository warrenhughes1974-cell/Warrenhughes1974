# Issue #21D — Track A: Interest Rate Strategy

**Date:** 2026-06-27  
**Converter version:** v57.35  
**Track:** A — Interest crediting rate (ISWL 4.00% vs 4.50%)  
**Status:** Planning complete — no implementation

---

## 1. Problem statement

QLAdmin **Dividend Accum Int Rate** displays **4.00%** on ISWL policies. Client confirms **4.50%** is authoritative for all ISWL plans. Intake traced the displayed value to **`quikdvdp.MDEPINT`**, hardcoded in the quikdvdp rulebook — not to `quikplan.NFOINT` (already `A` / 4.50% via CSO crosswalk).

**Affected population:** 2,268 ISWL policies (100% of ISWL fleet).

**Critical planning discovery:** The current rulebook default applies **`MDEPINT = 4.00` to all 5,083 policies**, not ISWL only. Any fleet-wide constant change is **out of scope** without non-ISWL rate validation.

---

## 2. QLAdmin field authority map

| QLAdmin label | QLA table.field | Current ISWL value | Correct authority |
|---------------|-----------------|--------------------|-------------------|
| Dividend Accum Int Rate | `quikdvdp.MDEPINT` | **4.00** (wrong) | **4.50%** (client + CSO) |
| Plan NFO interest code | `quikplan.NFOINT` | **A** (correct) | CSO Mortality Crosswalk |
| Cash value interest path | `quikplan.NFOINT` + rate keys | Separate from display | Issue #21E dependency |

Planning assumes **MDEPINT is the sole fix target** for the Dividend Accum Int Rate display defect. NFOINT alignment is already correct and must not be regressed.

---

## 3. Option analysis

### Option A — Rulebook constant 4.00 → 4.50

**Description:** Change `Sync_Rulebook_quikdvdp.csv` line 6 from `4.00` to `4.50`.

| Dimension | Assessment |
|-----------|------------|
| **Technical complexity** | Very low — one CSV cell |
| **Regression risk** | **HIGH** — affects **2,815 non-ISWL policies** currently at 4.00 |
| **Maintainability** | Poor — duplicates rate truth; diverges from CSO crosswalk |
| **Client impact** | Fixes ISWL; may silently wrong-rate non-ISWL products |
| **Data governance** | Violates single-source-of-truth principle |
| **Operational simplicity** | Highest short-term |
| **Long-term ownership** | Actuarial must maintain two rate stores (CSO + rulebook) |

**Verdict:** **Reject as fleet-wide change.** Acceptable only as a **temporary hotfix** if paired with explicit non-ISWL rate sign-off (not available). **Not recommended.**

---

### Option B — Derive MDEPINT from product / CSO authority (plan-aware)

**Description:** At `quikdvdp` conversion, resolve each policy's base `MPLAN` (via quikridr phase 1 or quikmstr), look up crediting rate from **`CSO_Mortiality_Crosswalk.csv`** (`nfo_interest_source` → numeric percent), and set `MDEPINT` per plan. Non-ISWL plans retain current default or their CSO row rate where defined.

**Implementation sketch (for Development — not executed here):**

1. Reuse `qla_core/cso_mortality_crosswalk.py` loader (already used for quikplan NFOINT).
2. Add surgical post-rulebook step in `app.py` / `QLA_Migration/app.py` during `quikdvdp` emit: if MPLAN maps to CSO row with numeric `nfo_interest_source`, set `MDEPINT` to that value (e.g. `4.50`); else retain rulebook default.
3. ISWL plan list (8 codes) serves as validation boundary, not hardcode list — CSO row presence is the gate.

| Dimension | Assessment |
|-----------|------------|
| **Technical complexity** | Low–medium — isolated branch; reuses existing CSO module |
| **Regression risk** | **Low** — scoped to plans with CSO rate rows; non-ISWL unchanged unless CSO defines them |
| **Maintainability** | **Strong** — same authority as NFOINT; one CSV update propagates |
| **Client impact** | Corrects all 2,268 ISWL policies to 4.50% |
| **Data governance** | Aligns with existing actuarial crosswalk delivery model |
| **Operational simplicity** | Medium — requires app.py touch + validator |
| **Long-term ownership** | Actuarial owns CSO crosswalk; conversion reads it |

**Verdict:** **Recommended primary approach.**

---

### Option C — Source extract-driven MDEPINT

**Description:** Map `MDEPINT` from a LifePRO extract field (e.g. dividend event, benefit type, or policy-level rate column) instead of a conversion default.

| Dimension | Assessment |
|-----------|------------|
| **Feasibility** | **Low today** — no extract column is currently mapped to `MDEPINT` |
| **Intake evidence** | `PEVNTNONFC` / `PPBENTYP` supply deposit/int date amounts, not crediting rate percent |
| **Client extract request** | Would require LifePRO team to expose policy-level crediting rate — lead time unknown |
| **Regression risk** | Medium — extract quality varies by policy era |
| **Maintainability** | Good if extract is authoritative; bad if extract sparse |
| **Data governance** | Preferred in theory (source-of-record) but **not available** in current package |

**Verdict:** **Defer.** Revisit only if client confirms a specific LifePRO column holds policy-level Dividend Accum Int Rate. Not preferable to Option B given CSO crosswalk already delivered and accepted.

---

## 4. Recommended authority model

### Primary recommendation: **Option B (CSO crosswalk–driven, plan-aware MDEPINT)**

| Principle | Detail |
|-----------|--------|
| **Authority** | `plan_analysis/source_data/rates/CSO_Mortiality_Crosswalk.csv` |
| **Key column** | `nfo_interest_source` (e.g. `4.50%`) → normalize to `MDEPINT` numeric |
| **Scope gate** | Apply override when CSO row exists for policy's base MPLAN |
| **Fallback** | Retain rulebook default `4.00` for plans without CSO numeric rate |
| **Alignment** | Keeps `quikplan.NFOINT` code and `quikdvdp.MDEPINT` percent synchronized per plan |

### Why not Option A

Fleet-wide `4.50` would change **2,815 non-ISWL policies** with no business sign-off on their correct Dividend Accum rates.

### Why not Option C (now)

No mapped extract exists; CSO crosswalk already satisfies client 4.50% rule for ISWL.

---

## 5. Issue #21E coordination note

Cash value (Issue #21E) may depend on interest assumptions beyond `MDEPINT`. Planning requires:

- Development validates whether QLAdmin CV computation reads `MDEPINT`, `NFOINT`, or QUIKAINT keys.
- UAT for #21D and #21E should run on shared golden policies (`010713704C`, `010818663C`).
- **Do not close #21E** based on MDEPINT fix alone.

---

## 6. Validation targets (Track A)

| Check | Expected after fix |
|-------|-------------------|
| ISWL `quikdvdp.MDEPINT` | **4.50** for all 2,268 policies |
| Non-ISWL without CSO rate row | Unchanged from baseline (4.00) |
| ISWL `quikplan.NFOINT` | Remains **A** (no regression) |
| QLAdmin sample `010713704C` | Dividend Accum Int Rate **4.50%** |
| Schema | `quikdvdp` field order/types unchanged |

---

## 7. Files anticipated for Development (Track A)

| File | Change type |
|------|-------------|
| `QLA_Migration/Configs/Sync_Rulebook_quikdvdp.csv` | Update comment; default may remain 4.00 as fallback |
| `app.py` / `QLA_Migration/app.py` | Surgical MDEPINT enrichment from CSO by MPLAN |
| `qla_core/cso_mortality_crosswalk.py` | Optional: expose rate-percent resolver (read-only extension) |
| `tools/validators/validate_issue21d_mdepint.py` | **New** — ISWL population check |
| `Issue_21D_Interest_Rate_Population.csv` | Before/after regression fixture |

**Version bump:** Required on `app.py` when Development executes (e.g. v57.36).

---

## 8. Client actions (Track A)

| Action | Required? |
|--------|-----------|
| Confirm 4.50% for all ISWL | **Done** (intake) |
| Confirm non-ISWL policies should remain at 4.00% until separately governed | **Recommended before release** |
| Provide LifePRO extract for policy-level rate | **Not required** if Option B approved |

---

*Track A strategy complete. See `Issue_21D_Decision_Matrix.md` for scored comparison.*
