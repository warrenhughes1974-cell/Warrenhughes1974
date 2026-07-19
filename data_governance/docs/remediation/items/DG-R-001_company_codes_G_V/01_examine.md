# DG-R-001 — Examine: Company codes G / V missing

**Status:** DECIDED (Option A) — group fate still open  
**Date:** 2026-07-18  
**Rule IDs:** DG-QUIKLIST-002, DG-QUIKPLAN-032  
**Primary tables:** QuikComp (reference), QuikList, QuikChrt; also check QuikAgts, QuikActg if present  
**Data region:** TBD (confirm before Implement)

---

## 1. What the rules require

| Rule | Check | Required |
|------|--------|----------|
| DG-QUIKLIST-002 | `QuikList.MCOMP` | Must exist **exactly once** in `QuikComp.MCOMP` |
| DG-QUIKPLAN-032 | Company codes on QuikAgts / QuikActg / QuikList / QuikChrt | Same — must exist once in QuikComp |

Validity is **not** a hardcoded alphabet list. A code is valid only if it is a unique nonblank row in Company Setup (`QuikComp`).

Business / conversion context in this repo:

- Conversion defaults company code to **C** (Loyal American pattern).
- No company crosswalk remaps G→C or V→C in Mapping / plan_governance.
- Sample names `GTEST01`, `TERMG`, `TEST1` look like **test groups**, not production book of business.

---

## 2. Scope from baseline report

### QuikList (Group Billing)

| Group | Current MCOMP | Finding |
|-------|---------------|---------|
| GTEST01 | V | Company code V not in Company Setup |
| TERMG | G | Company code G not in Company Setup |
| TEST1 | G | Company code G not in Company Setup |

### QuikChrt + Plan Setup Group Billing

- Many QuikChrt rows with `MCOMP = G`
- Many QuikChrt rows with `MCOMP = V`
- Plan Setup / Group Billing findings for G and V (DG-QUIKPLAN-032)

Exact live counts require a read of the audited data folder (not in git).

### QuikComp

- G and V were **not** found (per governance). Inventory of which codes *do* exist (likely including `C`) must be confirmed on the live region before Implement.

---

## 3. Options (business decision)

### Option A — Remap G/V → existing company `C` (recommended default)

**Action:** Update `MCOMP` from `G` or `V` to `C` on all referencing tables (QuikList, QuikChrt, and QuikAgts/QuikActg if inventory shows them). Do **not** create G or V in QuikComp.

| Pros | Cons |
|------|------|
| Matches conversion default / single-company Loyal American setup | Loses any intentional multi-company distinction if G/V were real |
| Clears 002/032 without inventing companies | Must confirm `C` exists once in QuikComp |
| Clean for test leftovers | Chart/agent history shows C instead of G/V |

**Blast radius:** All rows currently coded G or V. Policy suffix / DG-QUIKCOMP-003 consistency: policies whose last character is G or V would still fail company rules unless those codes exist or policies are remapped separately — **inventory must check policy last-char vs QuikComp**.

### Option B — Create G and/or V in QuikComp

**Action:** Insert Company Setup rows for `G` and/or `V` with required QuikComp fields (name, etc. per schema). Leave referencing rows unchanged.

| Pros | Cons |
|------|------|
| Preserves existing MCOMP on groups/charts | Implies real multi-company setup; needs legal/ops names |
| No mass remap | If G/V were test-only, pollutes Company Setup |
| | Must still fix test group *defaults* under DG-R-002 |

### Option C — Mixed

Examples:

- Delete or neutralize test groups in **DG-R-002**, and remap remaining QuikChrt G/V → C under this item.
- Create only `G` if ops confirms a real company; remap `V` → C (or delete GTEST01).

| Pros | Cons |
|------|------|
| Flexible | Needs clearer business facts |
| Can isolate test data | Slightly more complex change log |

### Option D — Defer remap; inventory-only this sprint

Park until data-region path + QuikComp inventory + policy-suffix check are available.

---

## 4. Dependencies

| Item | Relationship |
|------|----------------|
| **DG-R-002** | Same three QuikList groups also fail billing defaults. Decision on delete vs keep groups affects whether 001 needs to touch those List rows at all. |
| DG-QUIKCOMP-003 (policy last char) | If policies end in G/V, Option A alone may leave policy-level company failures. Flag in inventory before Implement. |
| Later items | None block Examine/Decision; Implement needs confirmed data path + backup. |

**Recommended sequencing note:** You may decide DG-R-001 now even if DG-R-002 is “delete groups” — Execution Agent for 001 would then skip List rows that 002 will delete, or 002 runs first. Prefer: **decide both group fate (keep/delete) here or explicitly defer List rows to DG-R-002**.

---

## 5. Recommended option (for discussion — not a decision)

**Option A (remap G/V → C)** for QuikChrt and any production-like List rows, **and** treat `GTEST01` / `TERMG` / `TEST1` as test data to **delete in DG-R-002** (so this item may only need Chart + any non-test List/Agts/Actg remaps).

If you prefer to keep the three groups, Option A still applies to their `MCOMP`, and DG-R-002 fixes defaults only.

---

## 6. Validation (after Implement)

- Governance: `DG-QUIKLIST-002` and `DG-QUIKPLAN-032` → zero findings for G/V
- Inventory: no remaining `MCOMP` in {G,V} on QuikList / QuikChrt / QuikAgts / QuikActg (unless Option B created them and they remain)
- QuikComp still has unique codes; `C` present exactly once (Option A)

Suggested command (after data path known):

```bash
python -m data_governance run --input "<DATA_REGION>" --output "<OUT>" --rule DG-QUIKLIST-002
python -m data_governance run --input "<DATA_REGION>" --output "<OUT>" --rule DG-QUIKPLAN-032
```

---

## 7. Regression guards

- QuikComp rows for codes other than any newly created ones: unchanged
- QuikList / QuikChrt rows whose `MCOMP` was already a valid code (not G/V): unchanged
- No edits to QuikPlan plan fields, QuikDate, or plan-value tables under this item
- Previously CLOSED DG-R items: none yet

---

## 8. What we need from you

1. **Business decision:** A / B / C / D (with details if C).  
2. **Fate of test groups** for this item: remap their MCOMP now, leave to DG-R-002 delete, or keep + remap.  
3. **Data region path** (folder of Quik*.dbf/csv that produced the report) — required before Implement, not required to decide.  
4. Confirm whether **C** is the correct target company (or name another existing QuikComp code).

Reply with something like:

`Decision: Option A — remap all G/V to C; delete test groups in DG-R-002; target company C`
