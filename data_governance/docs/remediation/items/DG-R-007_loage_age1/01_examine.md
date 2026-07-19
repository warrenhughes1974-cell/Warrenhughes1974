# DG-R-007 — Examine: LOAGE Age-1 must be zero (DG-QUIKPLAN-008)

**Status:** AWAITING_DECISION  
**Date:** 2026-07-18  
**Rule ID:** DG-QUIKPLAN-008  
**Primary table:** QuikPlan  
**Fields:** `LOAGE`, `HIAGE`  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`

---

## 1. What the rule currently requires

| Check | Required |
|-------|----------|
| Readable numerics | LOAGE and HIAGE must decode |
| Age-1 / low age | **LOAGE must equal 0** |
| Range | LOAGE must be **&lt;** HIAGE |

Business text (`Data_Goverence.txt` line 115):

> LOAGE- AGE 1 NEEDS TO BE 0 IN THE TABLE, AND THE LOAGE NEEDS TO BE &lt; THE HIAGE

Catalog purpose: *"Ensure the low age is zero for the Age 1 row and is less than the high age."*

---

## 2. Live inventory — CSO

| Metric | Value |
|--------|------:|
| QuikPlan rows | 142 |
| LOAGE = 0 | **87** |
| LOAGE ≠ 0 | **55** |
| LOAGE ≥ HIAGE (incl. blank plan 0/0) | **1** (blank PLAN: 0/0) |
| Rule 008 failure class (approx.) | **56** (55 non-zero + 1 range) |

Non-zero LOAGE values look like real product minimums, not garbage:

| LOAGE | Count (CSO) | Typical products |
|------:|------------:|------------------|
| 15 | 16 | ADB / WP riders |
| 18 | 12 | Term / spouse riders |
| 20 | 7 | Various |
| 46 | 4 | CSI Life |
| 45 / 50 / 19 / 1 | rest | Adult / special ages |

---

## 3. Production check — WPA_GABIE (readable)

| Metric | Value |
|--------|------:|
| QuikPlan rows | 1848 |
| LOAGE = 0 | **1473** (~80%) |
| LOAGE ≠ 0 | **375** (~20%) |
| Common non-zero lows | 16 (141), 20 (78), 18 (58), 15 (51), 21 (23), … |

Production **intentionally** stores non-zero minimum issue ages on a large minority of plans (health, riders, adult-issue products). This is not a corrupt-logical / unanimous-default situation like HCOMMIP; it is product configuration.

---

## 4. QLAdmin manual — what LOAGE actually is

`docs/claims_conversion_reference/QLAdmin_Help.pdf` Plan Information File, General Tab (p. 538):

> **Issue Ages** — Lowest and highest age for which this plan may be issued.

So QuikPlan `LOAGE` / `HIAGE` = **issue-age eligibility band**, not a fixed “Age 1 must be zero” system switch.

Rate tables separately use AGE beginning with `00` for duration grids — that is a different concept from plan-level Issue Ages. The written “AGE 1 NEEDS TO BE 0” line in `Data_Goverence.txt` appears to be a **misread** of that rate-table convention (or similar), applied incorrectly to QuikPlan.LOAGE.

---

## 5. Conversion / rulebook context

| Source | Behavior |
|--------|----------|
| `Sync_Rulebook_quikplan.csv` | `MIN_ISSUE_AGE` → `LOAGE`, Default=`0` |
| Emit path | Source min issue age wins when present; default 0 only when empty |

Default 0 is fine as an empty-source system default. **Forcing LOAGE=0 over real MIN_ISSUE_AGE would erase product rules** and fight both conversion mapping and production.

---

## 6. Options (business decision)

### Option R1 — Revise rule 008: drop “LOAGE must be 0”; keep readable + LOAGE &lt; HIAGE (recommended)

**Action:** Change DG-QUIKPLAN-008 (catalog, runner, tests, report wording, `Data_Goverence.txt`, schema notes). No QuikPlan DBF writes.

| Pros | Cons |
|------|------|
| Matches QLAdmin manual and WPA/CSO practice | Slightly weaker than original written line |
| Preserves real min issue ages | Blank-plan 0/0 still fails on LOAGE &lt; HIAGE (good; overlaps DG-R-008) |

### Option R2 — Retire rule 008 entirely

Remove all LOAGE/HIAGE checks. Not recommended — range and readability still matter.

### Option A — Data fix: set LOAGE=0 on all non-zero plans

**Not recommended.** Would destroy real issue-age floors on ~55 CSO / ~375 WPA plans.

### Option B — Soften rule only in decoder (treat non-zero as warning)

Weaker than R1; still implies zero is preferred when production shows otherwise.

---

## 7. Recommended option (discussion — not a decision)

**Option R1** — same family as DG-R-004 / DG-R-006: the written “must be 0” requirement is wrong relative to the product manual and production. Keep **LOAGE &lt; HIAGE** (and readable). Leave conversion default 0 for empty source. **No data rewrite.**

In plain English: the system is allowed to say “this rider only issues from age 15 to 55.” The governance check that says every plan’s low age must be zero is incorrect and should be removed; we should still require that the low age is less than the high age.

---

## 8. Validation (after Implement)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --rule DG-QUIKPLAN-008
```

Expect: only remaining failures are true range/unreadable issues (e.g. blank PLAN 0/0), not non-zero LOAGE.

---

## 9. Regression guards

| Guard | Expect |
|-------|--------|
| DG-R-004 / 005 / 006 | Unchanged (NAPLAN, HCOMMIP/HRIGPKEY, 022 retired) |
| No QuikPlan DBF writes | Pass |
| Sync_Rulebook MIN_ISSUE_AGE→LOAGE default 0 | Unchanged |
| Conversion does not force LOAGE=0 over source | Confirm / document |

---

## 10. Decision prompt (for user)

Reply with one of:

1. `Decision: Option R1 — revise 008: drop LOAGE=0 requirement; keep LOAGE < HIAGE; no data changes`
2. `Decision: Option R2 — retire 008 entirely`
3. Other / defer
