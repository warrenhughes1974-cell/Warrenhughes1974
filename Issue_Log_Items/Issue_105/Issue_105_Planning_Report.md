# Issue #105 — Planning Report

**Issue:** #105 — QuikRidr MPAR must be True for participating products  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-24  
**Model:** Cursor Grok 4.5  
**Depends on:** `Issue_105_Intake_Summary.md`

---

## 1. Executive finding

`quikridr.MPAR` is the QLAdmin “participating?” flag on coverage rows. It is **always 0** in current Output even when the product (`quikplan.PAR`) is participating. Client wants **product participating → `MPAR = 1` (True)**.

Authority should be **product `PAR`**, not LifePRO `PPBENTYP.PAR_TYPE` (which can be `N` on policies whose product is participating).

---

## 2. Confirmed LifePRO / plan sources

| Source | Field | Role for #105 |
|--------|-------|---------------|
| Product setup / `quikplan` emit | `EXHIBIT_PAR_NONPAR` → `PAR` | Canonical product participating (already P→1 / N→0 via `PAR_` translation, v57.57) |
| Policy benefit extract | `PPBENTYP.PAR_TYPE` | **Current** rulebook source for `MPAR` — **supersede for this flag** |
| Rider row | `MPLAN` | Join key to look up product `PAR` |

---

## 3. Confirmed QLAdmin targets

| Table | Field | Type | Semantics |
|-------|-------|------|-----------|
| `quikridr` | `MPAR` | CHAR(1) | `1` = participating (True), `0` = non-par |

Schema: `qladmin_core/qladmin_units_schema.py` and `app.py` quikridr header list include `MPAR`.

---

## 4. Proposed source-to-target mapping

**Preferred (matches client wording — product authority):**

After normal `quikridr` row build (keep existing PAR_TYPE pull if useful for logging), **set**:

```text
MPAR = quikplan.PAR[MPLAN]   # "1" if participating product, else "0"
```

Implementation sketch (surgical):

1. Build / reuse a `dict[plan_code → PAR]` from the in-batch `quikplan` rows (or same EXHIBIT_PAR_NONPAR path used for plan emit).
2. When writing `quikridr.MPAR`, override with that lookup on `row_data["MPLAN"]`.
3. Fallback if MPLAN missing from map: `"0"` (fail closed).
4. Preserve existing sanitizer that maps blank/N/X/F → `0`, P → `1` (harmless if already 0/1).

**Avoid:**

- Broad rulebook rewrite of unrelated `PAR_TYPE` consumers
- Changing `quikplan.PAR` or Issue A annuity/supp PAR=0 rules
- Touching MPREM / MPOLICY / fees

**Rulebook note (optional):** Update `Sync_Rulebook_quikridr.csv` Transformation_Note for `MPAR` to document product-PAR authority; code override is the durable fix.

---

## 5. Open client questions

1. Confirm authority: **product `quikplan.PAR` wins** over `PPBENTYP.PAR_TYPE` even when LifePRO says `N` on a par product. (**Assumed Yes** from symptom text.)
2. Apply to **all phases** (base + riders) based on each row’s own `MPLAN`? (**Assumed Yes.**)
3. Any named UAT policies beyond fleet rule? (Nice-to-have; not blocking.)

None of these block Development given the stated product rule.

---

## 6. Formatting / fallback rules

| Case | MPAR |
|------|------|
| `quikplan.PAR(MPLAN) == "1"` | `"1"` |
| `quikplan.PAR(MPLAN) == "0"` or unknown plan | `"0"` |
| Annuity / prefix-`9*` (Issue A forces plan PAR=0) | `"0"` via inheritance |
| Emit values | Character `"0"` / `"1"` only (not boolean True/False text) |

---

## 7. Policy key handling

- Preserve Issue **#25** MPOLICY padding (do not touch MPOLICY formatting).
- Preserve Issue **#26** MPREM mapping (do not touch MPREM).
- Join on already-emitted / crosswalked `MPLAN` only.

---

## 8. Estimated record counts (current Output)

| Population | Count |
|------------|------:|
| `quikridr` rows | 6,934 |
| Rows expected to flip `0 → 1` | **2,895** |
| Distinct policies gaining MPAR=1 | **2,683** |
| Of which base MPHASE=1 | 2,683 |
| Rider phases MPHASE>1 on par MPLAN | 212 |
| Rows that must stay `MPAR=0` | 4,039 |
| Rows with plan PAR=0 but MPAR=1 today | **0** (no reverse defects) |

---

## 9. Sample trace (≥3)

| MPOLICY | MPHASE | MPLAN | MPAR before | Plan PAR | MPAR after |
|---------|--------|-------|-------------|----------|------------|
| 9010143726C | 1 | 221END | 0 | 1 | **1** |
| 9010148272C | 1 | 221END | 0 | 1 | **1** |
| 9010382520C | 2 | 528CTR | 0 | 1 | **1** |
| 9010391228C | 1 | 1970JB | 0 | 0 | **0** |

---

## 10. Risks and unknowns

| Risk | Notes |
|------|-------|
| PPBENTYP intentional non-par election | Client said product rule; document override |
| Plan map not loaded on ridr-only rebatch | Must load PAR map even when quikplan not in same emit |
| Blind True/False strings | Must emit `1`/`0` for QLAdmin CHAR flag |

---

## 11. Recommended Risk Agent prompt

> Risk-review Issue #105: quantify 0→1 MPAR flips by plan; confirm no non-par plan gets MPAR=1; confirm #25/#26 untouched; GO/NO-GO for product-PAR authority override.

---

## 12. Recommended Development task (do not implement yet)

1. Surgical override of `quikridr.MPAR` from product `PAR` by `MPLAN`.
2. Version bump root + `QLA_Migration/app.py`.
3. Add `tools/validators` (or issue script) asserting: every ridr row with plan PAR=1 has MPAR=1; plan PAR=0 has MPAR=0.
4. No other quikridr columns.

**Do not start until:** Dependency Gate PASS + Risk GO + **“Approved for Development.”**
