# DG-R-004 — Examine: MNAICLOB must default to N

**Status:** AWAITING_DECISION (revised after production evidence)  
**Date:** 2026-07-18  
**Rule ID:** DG-QUIKPLAN-024  
**Primary table:** QuikPlan (`quikplan.dbf` / `QUIKPLAN.DBF`)  
**Field:** `MNAICLOB` (C(6) — NAIC line-of-business)

---

## 1. What the rule currently requires

| Rule | Field | Required (current catalog) |
|------|--------|----------------------------|
| DG-QUIKPLAN-024 | `MNAICLOB` | Exactly **`N`** after trim/casefold |

Written business input in repo: `QLA_Migration/Data_Goverence.txt` — `MNAICLOB- DEFAULT N`.

---

## 2. Evidence from data (not a one-off CSO defect)

| Region | File | Rows | MNAICLOB |
|--------|------|-----:|----------|
| CSO test (governance target) | `Q:\CSO\CSO_Test_6_30_2026\quikplan.dbf` | 142 | **All `NAPLAN`** |
| Production (user screenshot) | `Q:\WPA\WPA_GABIE\QUIKPLAN.DBF` | 1861 | **Visible column all `NAPLAN`** |

Staged `plan_governance/staged/quikplan_staged.csv` also carries `NAPLAN`.

**Conclusion:** Production practice defaults to **`NAPLAN`**, not `N`. The governance rule (and `Data_Goverence.txt` line) appear **misaligned with production**, not the other way around.

---

## 3. Options (business decision) — REVISED

### Option R1 — Change the rule to require `NAPLAN` (user-leaning / recommended after production evidence)

**Action (code/docs only — no QuikPlan data rewrite for this item):**

1. Update DG-QUIKPLAN-024 expected value from `N` → `NAPLAN` (catalog, rule impl, tests, business descriptions, `Data_Goverence.txt`, schema notes as needed).
2. Re-run governance on CSO region — DG-QUIKPLAN-024 should pass for current data.
3. Conversion: emit/preserve `MNAICLOB=NAPLAN` as the default (do **not** force `N`).

| Pros | Cons |
|------|------|
| Matches production WPA_GABIE + CSO reality | Contradicts earlier written “DEFAULT N” note — that note must be corrected |
| Avoids mass rewrite of 142 (CSO) / 1861 (prod) plans | If some plans legitimately need other LOB codes later, rule may need a whitelist |

### Option R2 — Keep rule = `N` and mass-correct data

Force `MNAICLOB='N'` on CSO (and eventually prod) + conversion emit `N`. **Conflicts with production evidence.**

### Option R3 — Allow set {`N`, `NAPLAN`}

Pass if value is either. Weaker; only if both are intentionally valid.

### Option R4 — Defer until client confirms NAIC LOB meaning of NAPLAN vs N

---

## 4. Dependencies

| Item | Relationship |
|------|----------------|
| DG-R-005+ | Independent QuikPlan fields; unaffected by R1 |
| Conversion QuikPlan emit | If R1: default/preserve NAPLAN; if R2: force N |

---

## 5. Recommended option (discussion — not a decision)

**Option R1** — change DG-QUIKPLAN-024 (and governance text) to **`NAPLAN`**, leave production/CSO QuikPlan data as-is for this field.

---

## 6. Validation (after Implement, if R1)

```bash
python -m data_governance run --input "Q:\CSO\CSO_Test_6_30_2026" --output "<item>/validation_out" --rule DG-QUIKPLAN-024
```

Expect: PASS on current NAPLAN data. Spot-check against `Q:\WPA\WPA_GABIE` if accessible.

---

## 7. Regression guards (if R1)

- No QuikPlan DBF writes for MNAICLOB  
- DG-R-001 / DG-R-003 outcomes unchanged  
- Other DG-QUIKPLAN rules unchanged except 024 expected value  

---

## 8. What we need from you

Example:

`Decision: Option R1 — change DG-QUIKPLAN-024 required value to NAPLAN; do not rewrite QuikPlan data; update Data_Goverence.txt and conversion default accordingly`
