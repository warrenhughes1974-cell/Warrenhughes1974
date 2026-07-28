# Issue #121 — ART Family Research

**Date:** 2026-07-28  
**Purpose:** Confirm whether other Annual Renewable Term products share the false-ETI defect on `5667AT`.  
**Development:** Held until this research delivered.

---

## 1. How ART products were identified

| Source | Finding |
|--------|---------|
| `product_catalog_crosswalk.csv` | Three coverages with description “Annual Renewable Term” or “ART …” |
| `Modal_Premium_Factors_By_Plan.csv` | Same three QL plans |
| `PPBEN` Benefit_Seq 1 | Row counts match Output |
| `quikridr` Output | Emit codes present |

No additional ART plans found in Output or PPBEN beyond these three.

---

## 2. Product inventory

| # | LifePRO `PLAN_CODE` | QL `MPLAN` | Friendly name | Policies in Output |
|---|---------------------|------------|---------------|-------------------:|
| 1 | `667 ART` | `5667AT` | Annual Renewable Term | 195 |
| 2 | `646 ART` | `5646AT` | Annual Renewable Term | 1 |
| 3 | `667 ART CR` | `57ATCR` | ART Preferred Credit Life | 1 |
| | | | **Total ART family** | **197** |

User shorthand `5667ART` = emit plan **`5667AT`**.

---

## 3. Status outcome by plan

| MPLAN | Policies | MSTATUS 44 ETI | 54 Lapsed | 53 Death | 22 Active | Other |
|-------|---------:|---------------:|----------:|---------:|----------:|------:|
| `5667AT` | 195 | **90** | 71 | 22 | 11 | 1 (90) |
| `5646AT` | 1 | **0** | 1 | 0 | 0 | 0 |
| `57ATCR` | 1 | **0** | 1 | 0 | 0 | 0 |

Phase-1 `MPHSTAT` matches `MSTATUS` on all ART rows checked (including the 90 ETI).

---

## 4. Shared LifePRO coding (`PAID_UP_TYPE = LE`)

| MPLAN | Policies with PUT=`LE` | Of those, ETI today |
|-------|----------------------:|--------------------:|
| `5667AT` | 173 | 90 |
| `5646AT` | 1 | 0 |
| `57ATCR` | 1 | 0 |

Sibling detail:

| MPOLICY | MPLAN | CONTRACT | PUT | MSTATUS | Why not ETI |
|---------|-------|----------|-----|---------|-------------|
| 9010516211C | 5646AT | T / LP | LE | 54 | #13 T-wins → `ST_T_LP` |
| 9010916282C | 57ATCR | T / LP | LE | 54 | #13 T-wins → `ST_T_LP` |

So the **same LE source field** exists on all three ART plans; false ETI appears only when LE is applied under an **Active** contract (almost entirely `5667AT`).

---

## 5. Conclusion

| Question | Answer |
|----------|--------|
| Other Annual Renewable Term products? | **Yes — two:** `5646AT` (`646 ART`) and `57ATCR` (`667 ART CR`) |
| Same ETI defect happening now? | **No** on those two (both Lapsed 54) |
| Same underlying risk? | **Yes** — LE is present; Active+LE would become 44 under current rules |
| Recommended Dev scope when approved | Guard **ART family** (all three QL codes / LifePRO ART plans), not only `5667AT` |

---

## 6. Evidence file

`Issue_Log_Items/Issue_121/evidence/issue121_art_family_status_population.csv` — 197 rows (all ART family policies).
