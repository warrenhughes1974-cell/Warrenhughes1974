# Issue 21G — Intake Summary

**Issue:** #21G — Total Premium / Cost Basis  
**Date:** 2026-07-11  
**Framework stage:** **Intake (G0)** — no code; framing only  
**Assigned model:** Cursor Grok 4.5  
**Owner (recommended):** **Both** — Conversion (source math / staging) + **Client** (QLAdmin screen/field or “not required”)  
**Priority / severity:** Medium (tax / cost-basis servicing; not billing-critical)  
**Status recommendation:** **Planning** (then likely **Blocked — Awaiting Client Clarification** until target named)

---

## 1. Issue ID and title

| Field | Value |
|---|---|
| ID | **21G** |
| Title | Total Premium / Cost Basis |
| Parent | Issue #21 open-item packet |
| Tracking (CSV) | Still shows `AWAITING CLIENT` |
| Tracking (MD / Master) | Marked **DECIDED ✓** (source locked; staged report v57.63) |

**Intake framing:** This is not a greenfield defect discovery. Source authority and interim staging were already decided. What remains open — and what this Intake re-scopes — is the **QLAdmin destination** (or confirmation that conversion load is **not required**).

---

## 2. Client symptom

### Verbatim (tracking / issue log)

> LifePRO has Premiums Paid and Tax Basis but QLAdmin shows no equivalent. Example: 010448806C LifePRO Premiums Paid=$6552.00 Tax Basis=$2483.97; no matching QLAdmin field identified.

> **Question:** Where should Total Premium Paid and Cost/Tax Basis appear in QLAdmin? Identify target screen and field or confirm not required at conversion.

### Normalized

LifePRO Benefit Detail (and related fund screens for ISWL) display **cumulative Premiums Paid** and **Tax / Cost / Post-TEFRA Basis**. Converted QLAdmin policy screens do not show matching totals. Conversion currently does **not** load these values into any `quik*` table field; they are staged only to a Reports CSV.

---

## 3. Example policies

| MPOLICY | Book (staged) | LifePRO values cited | Intake note |
|---|---|---|---|
| **010448806C** | TRADITIONAL | Premiums Paid **$6,552.00**; Tax Basis **$2,483.97** | Matches **BA-only** PPBENTYP row exactly |
| **010391895C** | TRADITIONAL | Tax Basis **$1,095.36** / Premiums Paid **$3,305.00** (Final Analysis C12) | Also **BA-only** |
| **010391876C** | TRADITIONAL | Tax Basis **$751.14** / Premiums Paid **$3,077.79** | BA-only; PU rows zero |
| **010713704C** | ISWL_UL | Post-TEFRA / Premiums Paid-to-Date (screenshots) | Workbook: FV Gross Deposits / Basis |
| **010818663C** | ISWL_UL | Same class of LifePRO fields imaged | ISWL fund path |

**Primary trace policy for traditional:** `010448806C`  
**Primary trace policy for ISWL:** `010713704C`

---

## 4. Suspected domain

| Layer | Artifact | Role |
|---|---|---|
| Source (traditional) | `PPBENTYP_BenefitType_Extract` | `PREMIUMS_PAID`, `TAX_BASIS`, `PU_*`, also `SU_*` / `SL_*` tax/premium columns exist |
| Source (ISWL/UL) | `PPBEN_PolicyBenefit_Extract` FV rows | `FV_GUAR_DEPOSITS`, `FV_BASIS2` |
| Client authority | `docs/Copy of Premium Paid Fields.xlsx` (sheets Non-ISWL / ISWL) | Maps category → extract → column |
| Interim conversion | `Reports/issue21g_premium_basis_totals.csv` (~4,886 rows) | Staged informational; `QLADMIN_TARGET=PENDING_CLIENT_FIELD` |
| Helper (already in codebase) | `qla_core/issue21_open_item_decisions.py` → `build_premium_basis_totals` | **Do not change at Intake** |
| Suspected QLAdmin tables | Unknown — **not** in current `quikmstr` / `quikridr` / `quikbenf` rulebooks | Candidates historically guessed: values/dividend area (`quikdvpr` etc.) — **unconfirmed** |
| Related load path | `quikprmh` (Issue **21F**) | Lifetime **premiums paid** reconciliation via adjustment row — **not** tax basis |

**Domain:** Policy financial / tax attributes (premium-paid total + cost/tax basis) — **target-definition gap**, not a proven mapping bug.

---

## 5. What the issue is (problem statement)

Two related LifePRO attributes are visible to users and missing from QLAdmin conversion output as loadable fields:

1. **Total / cumulative Premiums Paid** (lifetime or benefit-level, depending on screen)
2. **Tax Basis / Cost Basis / Post-TEFRA Basis**

Without a named QLAdmin screen + field (or an explicit “informational only / not required”), conversion cannot map, validate, or UAT these values in the admin system.

---

## 6. What is already known (not missing)

### Source mapping (locked — Official Decisions + client workbook)

| Book | Premiums Paid source | Tax / Cost Basis source |
|---|---|---|
| Non-ISWL (traditional) | BA/BF `PREMIUMS_PAID` + PU `PU_PREMIUMS_PAID` | BA/BF `TAX_BASIS` + PU `PU_TAX_BASIS` |
| ISWL / UL | `FV_GUAR_DEPOSITS` | `FV_BASIS2` |

Workbook examples align (e.g. Non-ISWL `010310404C` BA+PU; ISWL `010713704C` FV deposits/basis).

### Interim behavior (v57.63+)

- Full batch writes **`QLA_Migration/Reports/issue21g_premium_basis_totals.csv`** only (not Output load package).
- Every row: `STATUS=STAGED_INFORMATIONAL`, `QLADMIN_TARGET=PENDING_CLIENT_FIELD`.
- Counts in current report: TRADITIONAL **2,560** · ISWL_UL **2,326**.

### Rulebook / schema scan (intake)

- No `TAX_BASIS`, cost-basis, or cumulative-premiums-paid target in `Sync_Rulebook_quikmstr.csv`, `quikridr`, `quikprmh`, or `quikdvpr` (dividend amounts only).
- `QLAdmin_Converted_Tables.txt` lists no dedicated tax-basis table in the populated set.

---

## 7. What is missing

| Gap | Why it blocks Development |
|---|---|
| **QLAdmin target screen** | Cannot tell UAT where to look |
| **QLAdmin target field name(s)** | Cannot write rulebook / engine mapping |
| **Load vs informational decision** | If “not required,” issue closes without load; if required, need schema |
| **Grain of display** | BA-only (screenshot) vs BA+PU total (workbook / staged report) vs BA+PU+SU+SL (21F premium total) |
| **Whether Tax Basis and Premiums Paid are one screen or two fields** | May be one values panel or separate attributes |
| **ISWL vs traditional same target?** | May differ by product book |
| **SU/SL tax-basis inclusion** | Extract has `SU_TAX_BASIS` / `SL_TAX_BASIS`; 21G formula currently omits them |
| **Reconciliation vs LifePRO screen** | Client example ≠ staged BA+PU total (see §9) |

---

## 8. In scope / out of scope (first pass)

### In scope

- Identify or confirm **QLAdmin home** for Premiums Paid and Tax/Cost Basis (screen + field), **or** document “not required at conversion”
- Preserve / refine **source formula** once grain is confirmed (BA-only vs BA+PU vs +SU/SL)
- If a load field is named: plan surgical map into that table only
- Keep staging report until load path exists (or close as informational)

### Out of scope (first pass)

- Coding / rulebook changes / new Output columns (Intake–Risk prohibited)
- Replacing **21F** `quikprmh` conversion-adjustment design (premiums history reconciliation)
- Inventing a new QLAdmin table or inventing field names
- Full PACTG history re-extract (21F already addressed lifetime premium *history* differently)
- Cash value (**21E**), interest rate (**21D**), modal factors (**21J**)

---

## 9. Critical intake finding — example policy math

For **010448806C** (`9010448806`) in current PPBENTYP extract:

| TYPE | Premiums Paid | Tax Basis |
|---|---:|---:|
| BA | **6,552.00** | **2,483.97** |
| PU | 4,068.03 | 4,068.03 |
| SL | 0.00 | 0.00 |
| **BA+PU (current 21G stage)** | **10,620.03** | **6,552.00** |

- Client symptom amounts = **BA Benefit Detail only** (exact match).
- Staged 21G report for this policy: `PREMIUMS_PAID=10620.03`, `TAX_BASIS=6552.00` (= BA+PU).
- Therefore: **LifePRO UI grain and conversion “total” grain may differ.** Planning must decide which grain QLAdmin should store if a field is named — and whether UAT compares to Benefit Detail BA or policy-level total.

Same pattern on **010391895C**: BA premiums 3,305.00 / tax 1,095.36; staged sums BA+PU.

---

## 10. Related issues

| Issue | Relationship |
|---|---|
| **21F** | Shares premium-paid *source family*; 21F **loads** a `quikprmh` adjustment so history sum ≈ LifePRO lifetime premiums (BA+PU+SU+SL). **Does not** place Tax Basis on a master field. 21G remains the tax-basis / screen-field question. |
| **21E** | ISWL fund values (`FV_BALANCE2` → MCV0); adjacent FV extract, different attribute |
| **21D** | Crediting rate; not basis |
| Prior 21G decision (v57.63) | Source + staging locked; **target still open** — this Intake treats that residual as the active work |

**Not a duplicate of 21F:** 21F answers “how do we make cumulative premiums paid *in payment history* match?” 21G asks “where do Premiums Paid **and Tax Basis** appear as *policy attributes* in QLAdmin (if at all)?”

---

## 11. Artifact inventory

| Artifact | Status |
|---|---|
| Client symptom + example policy | **Present** |
| LifePRO screenshot evidence (Final Analysis C12) | **Present** (010391895C, 010448806C, 010391876C; ISWL Post-TEFRA screens cited) |
| Client workbook `docs/Copy of Premium Paid Fields.xlsx` | **Present** |
| Official decision write-up | **Present** (`Issue_21_Open_Items_Official_Decisions.md` §21G) |
| Staged report `Reports/issue21g_premium_basis_totals.csv` | **Present** (~4,886 policies) |
| QLAdmin target screen/field | **Missing** |
| QLAdmin Help citation for cost basis / premiums paid | **Not confirmed at Intake** |
| Client answer: required vs informational | **Missing** |
| Agreement on BA-only vs BA+PU (+SU/SL) display grain | **Missing** |

---

## 12. Open questions (for Planning / client)

### Blocking (client / SME)

1. **Where in QLAdmin** should **Total Premiums Paid** appear (menu path / screen name)?
2. **Which field** (DBF / table column) holds it — or is it display-only / computed?
3. **Where / which field** for **Tax Basis / Cost Basis / Post-TEFRA Basis**?
4. Is either value **required at conversion**, or **informational only** (staged report sufficient for go-live)?
5. For traditional policies, should QLAdmin match **BA Benefit Detail** (client example) or **BA+PU workbook total** (current staging)?
6. Should **SU / SL** premiums and tax basis be included in “total”?
7. Do **ISWL** and **traditional** use the **same** QLAdmin fields?

### Conversion / Planning (internal)

8. If informational-only: close 21G with staged report as the deliverable and document UAT as N/A for QLAdmin screens.
9. If a field is named: confirm schema length/type and whether load belongs in an existing converter table or requires New Era / client config.
10. Align 21G premium total grain with 21F (BA+PU+SU+SL) **only if** business says they must match; they serve different purposes today.

---

## 13. Immediate blockers visible at Intake

1. **No QLAdmin target field** — Development cannot map.
2. **Display-grain ambiguity** (BA vs BA+PU) — validation criteria unclear even if a field is named later.
3. **Tracking-sheet drift** — CSV still `AWAITING CLIENT`; MD/Master say `DECIDED` (staging). Recommend unifying to: *Source decided / Target awaiting client* or status **Blocked — Awaiting Client Clarification** after Planning documents the single decision packet.

**No stop condition for Intake itself:** Issue ID, symptom, and examples are present. Not a duplicate merge — residual of prior staging decision.

---

## 14. Owner and priority

| | |
|---|---|
| **Owner** | **Both** — Client names target (or “not required”); Conversion owns source formula + any future surgical load |
| **Severity** | **Medium** — tax/cost basis matters for servicing and tax questions; does not block modal billing |
| **Code at this stage** | **None** (Intake complete → Planning next) |

---

## 15. Gate G0 checklist

- [x] Issue folder created: `Issue_Log_Items/Issue_21/Issue_21G/`
- [x] Intake summary written
- [x] Example policies listed
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

---

## 16. Next stage

**Planning Agent** — document candidate QLAdmin homes (Help / schema research), freeze open-question list for client, clarify BA vs BA+PU vs 21F grain, and produce `Issue_21G_Planning_Report.md`.

Do **not** advance to Development until G1 + G2 + G3. Expect Dependency Gate to hold on **client target-field (or not-required) answer** unless Planning finds a definitive QLAdmin field in Help that product already uses.
