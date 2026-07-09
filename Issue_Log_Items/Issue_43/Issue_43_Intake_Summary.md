# Issue #43 — Intake Summary

**Issue:** #43 — ISWL Expense Charge Source Discovery  
**Date:** 2026-07-08  
**Framework stage:** Investigation complete — awaiting client confirmation  
**Status:** Investigation Complete / Awaiting Client  
**Owner:** Warren · **Assigned:** Client (Sujitha) / LifePRO SME  
**Priority:** Awaiting Client / No Go for expense mapping until confirmed

---

## Client / business question

Client found **"Expense Type: Policy fee"** in a txt file and asked whether it is the same as QLAdmin **"Monthly expense per policy."** They did not find source evidence for:

- Percent of premium expense
- Monthly expense per $1,000

**Scope:** Eight ISWL products only. Investigation only — no code, mapping, output, or documentation changes.

| LifePRO Coverage ID | QL Plan Code |
|-------------------|--------------|
| 658 CEN I | 1658C1 |
| 658 CEN SD | 1658CS |
| 659 CEN II | 1659C2 |
| 659 CEN SR | 1659CR |
| 659 CEN SD | 1659CS |
| 659 SR GD | 1659SR |
| 669 SR GD | 1669SR |
| 679 CEN SD | 1679CS |

---

## 1. Where is "Expense Type: Policy fee" coming from?

| Attribute | Value |
|-----------|-------|
| **Prior discovery file** | `Issue_Log_Items/Expense_Rate_Discovery_By_LifePRO_Plan.txt` |
| **Source extract** | `PCOVR_Coverage_Extract_20260530.csv` |
| **In-repo normalized copy** | `plan_analysis/source_data/coverage/PCOVR.csv` |
| **Table / record** | `PCOVR` — coverage / product master |
| **Field name** | `POLICY_FEE` |
| **Basis** | Coverage / product (plan-level, not policy-level) |

**Example row:** `659 CEN II`, `DESCRIPTION=Interest-Sensitive Whole Life`, `POLICY_FEE=25.00`, `PLAN_TYPE=U`, `PRODUCT_TYPE=05`

---

## 2. Is "Policy fee" equivalent to QLAdmin "Monthly expense per policy"?

**Not supported as automatic equivalence.**

| Factor | Finding |
|--------|---------|
| Source naming | Field is `POLICY_FEE`, not monthly expense |
| Product Book | `UF` = Per Policy Monthly Expense; `POLICY_FEE` is a separate coverage attribute |
| UF rate evidence | Only `UF` row found: `659 CEN II`, `VALUE=.0000000` — does not show 25.00 monthly |
| Existing conversion | Issue #21C maps `POLICY_FEE` → `quikridr.MANNLFEE` (annual/modal policy fee on base rider), not expense table setup |
| Frequency | `POLICY_FEE` on PCOVR is a product default; monthly expense would normally trace through `UF` segment rates |

**Conclusion:** `25.00` is confirmed source data for policy fee. Whether it should populate QLAdmin monthly expense per policy requires client / SME confirmation.

---

## 3. Product-by-product — Policy Fee = 25.00?

**Confirmed for all eight ISWL products** from `PCOVR.POLICY_FEE`:

| LifePRO Coverage ID | QL Plan Code | POLICY_FEE | Source |
|-------------------|--------------|------------|--------|
| 658 CEN I | 1658C1 | 25.00 | PCOVR.csv |
| 658 CEN SD | 1658CS | 25.00 | PCOVR.csv |
| 659 CEN II | 1659C2 | 25.00 | PCOVR.csv |
| 659 CEN SR | 1659CR | 25.00 | PCOVR.csv |
| 659 CEN SD | 1659CS | 25.00 | PCOVR.csv |
| 659 SR GD | 1659SR | 25.00 | PCOVR.csv |
| 669 SR GD | 1669SR | 25.00 | PCOVR.csv |
| 679 CEN SD | 1679CS | 25.00 | PCOVR.csv |

---

## 4. Other expense charge source evidence

### Found

| Charge type | Evidence | Notes |
|-------------|----------|-------|
| UF (Per Policy Monthly Expense) | PSEGT wired 8/8 via hub `659 CEN II`; Rate_Table 1 row; May ZIP PDAGE 12 rows | All zero-valued (`.0000000`) |
| Policy fee | `PCOVR.POLICY_FEE` | 25.00 on all 8 ISWL coverages |

### Not found

| Charge type | Search result |
|-------------|---------------|
| Percent of premium expense | No `U2` or `G2` ISWL rate rows; no workbook / extract field |
| Monthly expense per $1,000 | No `U3` or `G3` ISWL rate rows |
| Premium collection fees (`U1`) | 0/8 in PSEGT segment trace |
| Guaranteed monthly policy fee (`GF`) | 0/8 in PSEGT segment trace |
| PAAGERAT expense TYPE_CODEs | No `UF/U1/U2/U3/G2/G3/GF` rows for ISWL |
| PDDIC expense dictionary | Prior ZIP scan: 0 expense definition rows |

---

## 5. Files searched

**Primary extracts**

- `plan_analysis/source_data/coverage/PCOVR.csv`
- `plan_analysis/source_data/rates/Rate_Table_Extract_20260427.csv`
- `plan_analysis/source_data/rates/PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`
- `plan_analysis/source_data/coverage/PCOVRSGT.csv`
- `plan_analysis/PCOMP.csv`
- `Issue_Log_Items/Expense_Rate_Discovery_By_LifePRO_Plan.txt`

**Prior analysis artifacts**

- `docs/research/iswl_zip_prior_finding_revalidation_20260530.md`
- `docs/research/iswl_zip_target_source_analysis_20260530.csv`
- `docs/research/ISWL_Segment_Trace/ISWL_Segment_Trace_Matrix_20260629.csv`
- `docs/research/ISWL_Product_Book_Manual_Findings_Addendum.md`

**Workbooks / logic**

- `plan_analysis/source_data/crosswalk/Policy Form Crosswalk 5.22.26.xlsx`
- `docs/Policy Form Modal Premium Factors.xlsx`
- `docs/Copy of Premium Paid Fields.xlsx`
- `Issue_Log_Items/Issue_21/evidence/Issue_21.xlsx` (Policy Fees tab only)
- `app.py` / `QLA_Migration/app.py` (Issue #21C `POLICY_FEE` → `MANNLFEE`)

**Note:** `QLA_Migration/Source/` not present locally; May extract evidence taken from prior ZIP scan artifacts.

---

## 6. Search terms used

`policy fee`, `POLICY_FEE`, `monthly expense`, `percent of premium`, `per $1,000`, `per 1000`, `expense type`, `expense amount`, `admin fee`, `policy charge`, `monthly charge`, `per policy charge`, `premium load`, `percent premium`, `expense rate`, LifePRO segment codes `UF`, `U1`, `U2`, `U3`, `G2`, `G3`, `GF`, and all eight ISWL coverage / QL plan codes.

---

## 7. Recommendation for Sujitha

Suggested client response:

> We found "Policy fee" in LifePRO coverage/product setup, field `PCOVR.POLICY_FEE`. For all eight ISWL products reviewed, that value is **25.00**. We do **not** have source support to say this is the same as "Monthly expense per policy." The LifePRO monthly per-policy expense segment appears to be **UF**, and the only UF evidence found for ISWL is zero-valued/incomplete. We also did **not** find source evidence for percent-of-premium expense, monthly expense per $1,000, per-thousand expense, or premium percentage load. Please confirm whether the missing expense charges should be treated as **0.00**, and separately confirm whether the **25.00 Policy Fee** should be loaded as a monthly policy expense or handled as a policy fee.

---

## Not in scope

- ISWL expense table mapping or QUIKAEXP setup
- Defaulting missing expense charges to 0.00 in code
- Changes to `quikplan` staged expense fields
- Issue #21C policy fee (`MANNLFEE`) behavior — separate, already released

---

## Related issues

| Issue | Relationship |
|-------|--------------|
| **#21C** | Released — maps policy-level `POLICY_FEE` to `quikridr.MANNLFEE`; not expense table |
| **#31–#33** | ISWL rate / segment work — expense setup explicitly deferred |
| **#42** | Separate source-gap issue (L01/L10 rate extracts) |
