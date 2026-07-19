# DG-R-010 — Examine: Missing Death Benefit setup/values (DG-QUIKPLAN-026)

**Status:** CLOSED (decision R1 applied)  
**Date:** 2026-07-19  
**Rule ID:** DG-QUIKPLAN-026  
**Primary tables:** QuikPlan (`VARDB`), QuikDbs, QuikPlDb  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`

---

## 1. What the rule currently requires

| Condition | Required |
|-----------|----------|
| `VARDB` ≠ 4 | Plan must exist in **both** QuikDbs and QuikPlDb |
| Supporting table missing | Could Not Be Checked |

Business text (`Data_Goverence.txt`):

> IF VARDB IS NOT 4 THEN WE NEED TO VALIDATE THERE IS A PLAN CODE IN QUIKDBS AND QUIKPLDB

Sync_Rulebook default: `VARDB=0`.

---

## 2. What VARDB means (QLAdmin)

From QLAdmin Help (Plan Information — Var DB):

| VARDB | Meaning |
|------:|---------|
| **0** | **Level** — death benefit from **Initial Val/Unit** (`INITVAL`); rate tables not used |
| **1** | Vary by policy year only |
| **2** | Vary by issue age and policy year |
| **3** | (used in this book for some varying schedules) |
| **4** | Death benefits **not on file** — skip supporting tables |

So requiring QuikDbs/QuikPlDb for **every** non-4 code treats **level (0)** the same as **varying (1/2/3)**. That conflicts with the product manual.

---

## 3. Live inventory — CSO

| Metric | Value |
|--------|------:|
| QuikPlan rows | 141 |
| QuikDbs distinct plans | 23 |
| QuikPlDb distinct plans | 126 |
| VARDB distribution | 0×121, 1×3, 2×7, 3×10 (**no VARDB=4**) |
| Governance 026 findings | **133** (all `MISSING_SUPPORTING_PLAN`) |

| VARDB | OK (both tables) | Missing QuikDbs only | Missing both |
|------:|-----------------:|---------------------:|-------------:|
| **0** (level) | 3 | **103** | **15** |
| **1** | **3** | 0 | 0 |
| **2** | **7** | 0 | 0 |
| **3** | **10** | 0 | 0 |

**Finding:** Every 026 failure is on **VARDB=0**. Every plan with VARDB 1/2/3 already has both QuikDbs and QuikPlDb.

Double-count math: 103 (dbs-only) + 15×2 (both missing → two findings each) = **133**.

Typical missing-dbs-only plans: ADB / waiver riders (have QuikPlDb keys, no QuikDbs factors). Missing-both: PUA, JPO, some SPWL, payor disability, etc.

---

## 4. Production — WPA_GABIE

| Metric | Value |
|--------|------:|
| QuikPlan | 1848 |
| QuikDbs plans | **3** |
| QuikPlDb plans | **4** |
| VARDB | almost all **0** |
| Plans with both tables | 3 (VARDB 1/2/3 graded/mod whole life) |

Production does **not** load death-benefit tables for level (VARDB=0) plans. Same pattern as CSO failures — not corrupt data.

---

## 5. Options

### Option R1 — Revise rule 026: require QuikDbs/QuikPlDb only when VARDB ∈ {1,2,3} (recommended)

**Action:** Update catalog, runner, tests, report wording, `Data_Goverence.txt`, RULE_CATALOG.  
Skip when VARDB is **0** (level) or **4** (not on file).  
**No** mass insert of QuikDbs/QuikPlDb rows.

| Pros | Cons |
|------|------|
| Matches QLAdmin + WPA | Written “not 4” line was over-broad |
| CSO would clear all 133 current findings without inventing rates | — |

### Option A — Create missing QuikDbs/QuikPlDb for all VARDB≠4 plans

Would force tables onto ~118 level plans. Contradicts production and INITVAL-level design. **Not recommended.**

### Option B — Set VARDB=4 on all level plans missing tables

Would silence the rule by reclassifying products as “not on file,” which is the wrong meaning for level products that use INITVAL. **Not recommended.**

---

## 6. Recommended option (discussion — not a decision)

**Option R1** — same family as DG-R-004 / 006 / 007: the written check is broader than the product model. Level death benefit (VARDB=0) does not need QuikDbs/QuikPlDb; varying codes (1/2/3) already have them on CSO.

In plain English: if the plan’s death benefit is a flat amount per unit, QLAdmin does not look up a death-benefit rate table. Governance should only demand those tables when the plan is coded to *vary* the death benefit.

---

## 7. Validation (after Implement)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --rule DG-QUIKPLAN-026
```

Expect: PASS (or only true VARDB 1/2/3 gaps if any appear later).

---

## 8. Decision prompt

Reply with:

1. `Decision: Option R1 — revise 026: require QuikDbs/QuikPlDb only when VARDB is 1, 2, or 3; no data changes`
2. Other / defer
