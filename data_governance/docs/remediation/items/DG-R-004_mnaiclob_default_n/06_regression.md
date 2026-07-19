# DG-R-004 — Regression

**Date:** 2026-07-18  
**Result:** **PASS** (no QuikPlan MNAICLOB data mutation; DG-R-001 / DG-R-003 still hold; blast radius limited to rule 024)

---

## Guards checked

### 1. No QuikPlan MNAICLOB data mutation

| Check | Result |
|-------|--------|
| CSO `quikplan.dbf` written? | **No** |
| WPA `QUIKPLAN.DBF` written? | **No** |
| Source modified flag on governance run | **False** |

Production/CSO data remain `NAPLAN` as found; rule now matches that practice.

### 2. DG-R-001 CLOSED outcomes (still hold)

| Check | Expected | Result |
|-------|----------|--------|
| QuikList / QuikChrt remediation from DG-R-001 | Untouched by this item | **No edits** under DG-R-004 |
| DG-QUIKLIST-002 / DG-QUIKPLAN-032 | Not re-run; no dependency on MNAICLOB | Unaffected |

### 3. DG-R-003 CLOSED outcomes (still hold)

| Check | Expected | Result |
|-------|----------|--------|
| QuikDate PAC/DIR/REIN | Prior-month-end values from DG-R-003 | **Not edited** |
| Conversion `quikdate` emit | Unchanged | **Not edited** |
| APP_VERSION | Remains prior bump from DG-R-003 | **No bump** this item |

### 4. Other DG-QUIKPLAN rules

| Check | Result |
|-------|--------|
| Rules 001–023, 025–033 | Implementation unchanged |
| Only 024 expected value | `N` → `NAPLAN` |

### 5. Conversion blast radius

| Check | Result |
|-------|--------|
| QuikPlan sync rulebook MNAICLOB | Already `NAPLAN` — no change |
| `app.py` / converters modified? | **No** |
| APP_VERSION bumped? | **No** (not required) |

---

## Residuals (not blocking)

| Item | Detail |
|------|--------|
| Baseline finding text | `BASELINE_FINDINGS.md` still describes pre-R1 mass-fail narrative; historical — superseded by this CLOSED item |
| Other LOB codes | Rule requires exact `NAPLAN`; if future plans need alternate NAIC LOB codes, whitelist would be a new decision |
| Production WPA spot-check | User confirmed NAPLAN; this run validated CSO 142/142 only |

---

## Suggested tracker status

**CLOSED** — control tower to confirm artifacts and open DG-R-005.
