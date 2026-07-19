# DG-R-008 — Examine: Blank plan + orphan plan values

**Status:** AWAITING_DECISION  
**Date:** 2026-07-18  
**Rule IDs:** DG-QUIKPLAN-001, DG-QUIKPLAN-002, DG-PLANVALUES-003 (cascade: DG-QUIKPLAN-008 residual)  
**Primary tables:** QuikPlan; QuikPlGp / QuikPlDb / QuikPlCv / QuikPlTv / QuikPlDv; QuikPlGd / QuikPlUw / QuikPlBd  
**Data region:** `Q:\CSO\CSO_Test_6_30_2026`

---

## 1. What the rules require

| Rule | Requirement |
|------|-------------|
| DG-QUIKPLAN-001 | PLAN exactly 6 characters after trim; **blank fails** |
| DG-QUIKPLAN-002 | PLAN six letters/numbers only; blank / short fails |
| DG-PLANVALUES-003 | Plan-value PLAN must exist in QuikPlan; **blank PLAN fails** |
| DG-QUIKPLAN-008 (overlap) | LOAGE &lt; HIAGE — blank QuikPlan shell has 0/0 |

Business: plan codes must be six characters; plan-value rows must reference a real plan.

---

## 2. Live inventory — CSO

| Table | Rows | Blank PLAN | Orphan nonblank PLAN |
|-------|-----:|-----------:|---------------------:|
| QuikPlan | 142 | **1** | — |
| QuikPlGp | 282 | **1** | 0 |
| QuikPlDb | 210 | **1** | 0 |
| QuikPlCv | 230 | **1** | 0 |
| QuikPlTv | 280 | **1** | 0 |
| QuikPlDv | 210 | **1** | 0 |
| QuikPlGd | 211 | **1** | 0 |
| QuikPlUw | 185 | **1** | 0 |
| QuikPlBd | 127 | **1** | 0 |
| QuikGps / QuikDbs / QuikCvs / QuikTvs / QuikNps | large | 0 | 0 |

**Blank QuikPlan row (record index 0):** PLAN/FORM/DESCR empty; LOAGE=0, HIAGE=0, BACTIVE=False — empty shell, not a real product.

**Blank plan-value / PVO option rows:** default keys (GENDER=0, UWCLASS=00, BAND=00, …) with EFFDATE=1900-01-01 or “NOT APPLICABLE” descriptors — template shells tied to blank PLAN.

### Governance findings (CSO, this session)

| Rule | Findings |
|------|---------:|
| DG-QUIKPLAN-001 | 1 (blank PLAN) |
| DG-QUIKPLAN-002 | 1 (invalid format on blank) |
| DG-PLANVALUES-003 | 5 (blank PLAN on five QuikPl* value tables) |
| DG-QUIKPLAN-008 | 1 (0/0 on blank QuikPlan — residual from DG-R-007) |

No CSO orphans where a **nonblank** plan-value PLAN is missing from QuikPlan.

---

## 3. Production check — WPA_GABIE

| Check | Result |
|-------|--------|
| Blank QuikPlan | **0** — different problem than CSO |
| Orphan rate/value PLAN vs QuikPlan | **Yes, material** — e.g. QuikTvs ~28k orphan rows (plans like 525T3R, 525T10…); QuikGps 130; QuikPlGp 20 (117L65, 117P65) |

WPA orphans are **out of scope for the CSO blank-shell cleanup**. Treat as a separate future item if/when production orphan rates are approved for remediation.

---

## 4. Conversion context

| Check | Result |
|-------|--------|
| `QLA_Migration/Output/quikplan.csv` | **141** rows, **0** blank PLAN |
| CSO QuikPlan | 142 = 141 real + 1 blank shell |

Conversion emit already excludes blank plans. The blank shells on CSO look like leftover DBF junk (or a prior load artifact), not current converter output. Still worth documenting: never load a blank PLAN QuikPlan / QuikPl* row.

---

## 5. Options (business decision)

### Option A — Delete blank shells on CSO (recommended)

**Action:**

1. Backup CSO folder (or at least QuikPlan + QuikPl* tables touched).
2. Delete the **1** QuikPlan row with blank PLAN.
3. Delete the **1** blank-PLAN row in each of: QuikPlGp, QuikPlDb, QuikPlCv, QuikPlTv, QuikPlDv, QuikPlGd, QuikPlUw, QuikPlBd.
4. Do **not** touch WPA.
5. Conversion: document “skip/hold blank PLAN” in CONVERSION_SYSTEM_DEFAULTS (emit already clean; no APP_VERSION unless code change needed).

| Pros | Cons |
|------|------|
| Clears 001/002/003/008 residuals from blank shells | Physical DBF deletes (need backup) |
| Small, surgical (9 rows total) | Must not delete any nonblank plan |

### Option B — Leave blank QuikPlan; only delete blank QuikPl* rows

Leaves 001/002/008 failing on QuikPlan. Not recommended.

### Option C — Soften rules to ignore blank PLAN

Hides junk rows; contradicts “plan needs six characters.” Not recommended.

### Option D — Defer; include WPA orphans in same item

Too large / different root cause. Keep WPA orphans as a follow-on.

---

## 6. Recommended option (discussion — not a decision)

**Option A on CSO** — delete the blank QuikPlan shell and the matching blank PLAN shells in the eight plan-value / option tables. WPA orphan rates deferred. Conversion already clean; note the default.

In plain English: there is one empty “ghost” plan row and matching empty rate-option rows with no plan code. They are not real products. Delete those shells so governance stops flagging them. Do not touch production orphan rate plans in this item.

---

## 7. Validation (after Implement)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" \
  --rule DG-QUIKPLAN-001 --rule DG-QUIKPLAN-002 --rule DG-PLANVALUES-003 --rule DG-QUIKPLAN-008
```

Expect: 001/002/003/008 PASS on CSO (no blank shells).

---

## 8. Regression guards

| Guard | Expect |
|-------|--------|
| QuikPlan row count | 142 → **141**; all remaining PLAN codes unchanged |
| Nonblank QuikPl* row counts | Unchanged except −1 blank each |
| DG-R-001…007 closed items | Still clean |
| WPA | Untouched |

---

## 9. Decision prompt (for user)

Reply with one of:

1. `Decision: Option A — delete CSO blank QuikPlan + blank QuikPl* shells; WPA orphans out of scope`
2. `Decision: Option B — delete blank QuikPl* only`
3. Other / defer
