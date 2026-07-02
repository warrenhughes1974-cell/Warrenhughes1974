# Issue #32 — MLOANINTX Source Review

**Issue:** #32 — Policy Loan Conversion  
**Question:** Can `MLOANINTX` (A=Advance, R=Arrears) be derived from plan setup or source data?  
**Manual guidance:** Loan interest type based on **Plan Information File** for phase 1  
**Generated:** 2026-06-29

---

## 1. Executive Finding

| Verdict | Detail |
|---------|--------|
| **PLOAN columns** | **Cannot** supply A/R — `INTEREST_TYPE=F` (100%), `INT_METHOD=D` (100%) |
| **Plan Information File (QuikPlan)** | **Intended source** — field `LOANINTX` |
| **Current QuikPlan CSV emit** | **Not reliable** — all 133 staged plans show `LOANINTX=22` (invalid A/R) |
| **Rulebook default** | **`LOANINTX = A`** in `Sync_Rulebook_quikplan.csv` |
| **Approved conversion rule** | **QuikPlan lookup** → use if `A` or `R`; else **default `A`** |

---

## 2. Search Results

### 2.1 PLOAN extract

| Column | Fleet values | Maps to A/R? |
|--------|--------------|:------------:|
| `INTEREST_TYPE` | F (93,857) | No — Fixed rate |
| `INT_METHOD` | D (93,857) | No — not Adv/Arr |

Policy `9010331768`: INTEREST_TYPE=F, INT_METHOD=D; screenshot shows **Fixed** + **Advance** as **separate** labels.

**Conclusion:** Reject PLOAN `INTEREST_TYPE` and `INT_METHOD` for `MLOANINTX`.

---

### 2.2 QuikPlan — Plan Information File (phase 1)

QLAdmin **Plan Information File** = **`QuikPlan`** table (per `phase_r1_rate_architecture_analysis/qladmin_rate_table_relationships.md`).

| Attribute | Detail |
|-----------|--------|
| Field | `LOANINTX` C(1) |
| Semantics | A=advance, R=arrears (per `rate_dbf_physical_structure_inventory.csv`, QuikPlSt) |
| Rulebook | `QLA_Migration/Configs/Sync_Rulebook_quikplan.csv` line 10: **default `A`** |
| Governance | `rulebook_coverage_analysis.csv`: LOANINTX **MAPPED**, default **A** |

**Sample staged emit (`plan_governance/staged/uat/quikplan_staged.csv`):**

| PLAN | LOANINT | LOANINTX | DESCR |
|------|--------:|----------|-------|
| 1960PO | 0.00 | **22** | PREFERRED ORDINARY WHOLE LIFE |
| *(all 133 plans)* | varies | **22** | — |

**Problem:** `22` is not a valid QLAdmin A/R code. Likely CSV staging/alignment artifact or uninitialized plan field in current quikplan emit — **not suitable for direct copy without validation**.

---

### 2.3 QuikPlSt — state override (phase 2 / optional)

| Field | Semantics |
|-------|-----------|
| `MLOANINTX` | State-specific loan interest type override (A/R) |
| `MLOANINT` | State loan rate override |

Per rate architecture docs, state overrides apply when plan values options specify state-specific loan rates. **Not in scope for initial QuikLoan policy emit** unless policy state routing is added later.

---

### 2.4 LifePRO plan extracts

No LifePRO plan extract in current ZIP with explicit Adv/Arr loan timing code was found for direct join. Plan timing is expected to flow **LifePRO product config → QuikPlan LOANINTX** at plan conversion time.

---

### 2.5 QLAdmin Help / manual alignment

| Source | Statement |
|--------|-----------|
| QLAdmin Help p.180 (extract) | Loan interest calculated as **Interest in Advance** or **Interest in Arrears** |
| Manual guidance | Adv / Arr from Plan Information File phase 1 |
| Screenshot 9010331768 | Interest Method = **Advance** |

---

### 2.6 Other repo references

| Location | Reference |
|----------|-----------|
| `claims_analysis/phase17.../_qladmin_key_pages.txt` | Advance vs arrears anniversary-to-anniversary |
| `qla_core/rate_member_setup.py` | QuikPlSt MLOANINTX blank placeholder |
| Phase L1 `unresolved_mloanintx.csv` | 912 policies flagged INTEREST_TYPE=F |

---

## 3. Derivation Options Evaluated

| Option | Feasibility | Recommendation |
|--------|:-----------:|----------------|
| A. PLOAN `INTEREST_TYPE` | ❌ | Reject |
| B. PLOAN `INT_METHOD` | ❌ | Reject |
| C. QuikPlan `LOANINTX` by MPLAN | ⚠️ | **Implement with A/R validation** |
| D. Rulebook default `A` | ✅ | **Fallback** |
| E. Hard-coded fleet `A` | ✅ | Acceptable as fallback only |
| F. QuikPlSt state override | ⚠️ | Future enhancement |
| G. SME-only with no default | ❌ | Unnecessary — manual + rulebook provide A |

---

## 4. Approved MLOANINTX Algorithm (Development)

```
1. Resolve QLAdmin plan code for policy:
   - Preferred: quikmstr.MPLAN for MPOLICY (in-batch join)
   - Alternate: PLOAN.PLAN_CODE → Policy Form Crosswalk → QuikPlan.PLAN

2. Read QuikPlan.LOANINTX for that plan.

3. Normalize:
   - If LOANINTX in ('A', 'R') → MLOANINTX = LOANINTX
   - Elif LOANINTX in ('Adv', 'Arr') → map to A/R (if ever seen)
   - Else → MLOANINTX = config mloanintx_default ('A')

4. Do NOT read PLOAN INTEREST_TYPE or INT_METHOD for MLOANINTX.
```

---

## 5. Why Default `A` Is Acceptable (Conditional)

| Evidence | Weight |
|----------|--------|
| Manual: phase 1 plan file controls timing | High |
| Rulebook: LOANINTX default **A** for all QuikPlan rows | High |
| Screenshot: Advance for trace policy | Medium |
| Fleet PLOAN: no arrears indicator | Medium |
| QuikPlan CSV: corrupt `22` — forces fallback anyway | Operational |

**Risk:** If any plan uses arrears (`R`) and QuikPlan LOANINTX is not correctly emitted, policy would incorrectly get `A`. **Mitigation:** UAT spot-check; future fix to QuikPlan LOANINTX emit; optional SME plan list for `R` plans.

**Active loan plan mix (top codes):** 659 CEN II, 658 CEN I, L10 LP95, 960 PO, etc. — all receive fallback `A` until QuikPlan LOANINTX emit is corrected.

---

## 6. QuikPlan LOANINTX Data Quality Flag

| Observation | Action |
|-------------|--------|
| 133/133 plans show LOANINTX=`22` in staged CSV | Log warning in converter trace |
| Rulebook expects default `A` at plan build | Plan emit issue — **out of Issue #32 scope** unless blocking |
| QuikLoan can still load with fallback `A` | **Proceed** under Conditional PASS |

Recommend separate ticket: verify QuikPlan DBF `LOANINTX` vs CSV export for plan `1960PO`.

---

## 7. Conclusion

| Question | Answer |
|----------|--------|
| Can MLOANINTX be derived from plan setup? | **Yes — intended path via QuikPlan.LOANINTX** |
| Is current plan CSV usable as-is? | **No** — values not A/R |
| Approved interim rule? | **Lookup + fallback `A`** |
| Must SME confirm before Development? | **No** — manual + rulebook sufficient for Conditional PASS |
| Full PASS condition | UAT + optional QuikPlan LOANINTX emit fix |

---

**Machine-readable profile:** `Issue_32_MLOANINTX_Profile.json` (partial — plan join deferred due CSV quality)
