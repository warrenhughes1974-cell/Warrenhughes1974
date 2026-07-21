# Issue A — Conversion Checklist (RUNNING)

**Purpose:** Internal QuikPlan / PVO / rate-key checks that must run on **every conversion** Warren requests.  
**Track:** Internal only — not reported to the client.  
**Authority:** Issue A (Robert 2026-07-20)  
**How to use:** Copy a new **Run log** section at the bottom for each conversion. Mark each check PASS / FAIL / N/A / BLOCKED. Do not delete prior run logs.

**Cursor rule:** `.cursor/rules/issue-a-conversion-checklist.mdc`

---

## Master check list (keep updated)

| ID | Check | Expected | Status | Notes / owner |
|----|-------|----------|--------|---------------|
| **A1** | Single-premium plans | `PAYYRS` (Prem Years) = **1**; Semi / Quarterly / Monthly Direct / Monthly Draft mode factors = **0.00** (Annual may stay 100) | **IMPLEMENTED v58.20** | DESCR SP: `1668SP`, `10L171`, `10L172`, `1L17SP`. Verified PASS on Single Table run 2026-07-20. |
| **A2** | Deficiency reserves (Calc Dfcy) | For plans **without** indeterminate premiums: confirm CSO wants Calc Dfcy; if yes → **`DEFICIENCY=Y`** | **Planning — Awaiting CSO** | All 141=`N` today. Heuristic indet: 8 ISWL. See `Issue_A_A2_Planning_Report.md` |
| **A3** | Default PVO keys even with no rates | Every plan has default category records + default keys (`0`/`00`/…). Gold: **TESTRD** | **Decision — Warren 2026-07-20: every plan** | Fleet rule locked: every plan gets default keys. Implement when approved for Development. See `Issue_A_A3_Planning_Report.md` |
| **A4** | Empty QuikPl* PLAN rows | No blank-`PLAN` orphan records in emitted QuikPl* / QuikPI* tables (verify CSV, not UI placeholder alone) | **IMPLEMENTED v58.21** | Fleet scan 0 blank rows; rate emit drops blank PLAN defensively |
| **A5** | Missing basis info | Plans with real CV/TV keys have required basis populated; default-only stubs may leave basis empty (internal TESTRD) | **Source = Valuation_Setup** | Follow CSO Valuation_Setup / Issue #80 — not an Eric question |
| **A6** | Category settings match keys | For each plan, GP/DB/CV/TV/DV checkboxes on Gender/Band/UW/State match actual keys. Example fail: `130JEB` | **PARTIAL v58.21** | Orphan Y flags cleared when no keys; 2 plans still GP keys + STVARYGP=N |
| **A7** | VarGP matches PVO / GP rates | If GP rates/keys exist, `VARGP` must not be “no variation” (e.g. not **4** when rates present). Example: `1659C2` | OPEN | 126/141 VARGP=4 with GP keys — Go-Live Item 09; awaiting Eric |
| **A8a** | Annuity — participating | Annuity plans: **PAR = 0** (not participating) | **IMPLEMENTED v58.21** | A60MIR, A96DAR corrected |
| **A8b** | Annuity — VarDB | Annuity plans: **VARDB = 0** (no DB rates expected) | **IMPLEMENTED v58.21** | A60MIR VARDB was 2 → 0 |
| **A8c** | Annuity — interest rates | Annuity interest rates loaded where required | OPEN | Awaiting Eric scope |
| **A8d** | Annuity — schg | Surrender charge (schg) configured where required | OPEN | Awaiting Eric scope |
| **A8e** | Annuity — PVO defaults | Annuity PVO all default **0** (including gender) | **IMPLEMENTED v58.21** | PLANVALOPT=N; all *VARY*=N on A-prefix |
| **A9a** | Supp `9*` — supp type | Plans with PLAN prefix **9** have supp type populated | OPEN | Eric: confirm field name |
| **A9b** | Supp `9*` — PAR | Prefix-**9** plans have **PAR = 0** | **IMPLEMENTED v58.21** | 26 plans corrected; fleet scan PAR=1: 0 |
| **A10** | QuikUwpo UW class master | Every distinct plan `UWCODE` (from QuikPlUw / keys) has **one** `QuikUwpo` row; key = `UWCODE` (no dupes); default `00` always present | **IMPLEMENTED v58.22** | Emits `Output/rates/QuikUwpo.csv`: 00/NS/PR/SM/ST. Verified PASS 2026-07-20. |

### How to add new checks

When Robert (or internal review) finds another plan-setup defect:
1. Add a new row `A10`, `A11`, … above.
2. Mention it in the next conversion run log.
3. Do **not** remove closed checks — mark Status **CLOSED** and leave history in run logs.

---

## Per-conversion procedure (agent must do)

When the user asks to run a conversion / full batch / re-emit / production package:

1. Open this file.
2. Against the **new** `QLA_Migration/Output/` (and `rates/` if emitted), evaluate every **OPEN** check.
3. Append a **Run log** below with date, engine version, source package, and PASS/FAIL per ID.
4. Call out FAIL plan codes (sample or full list in `Issue_Log_Items/Issue_A/Reports/` if large).
5. Do not claim conversion “clean” if any OPEN check FAILs unless user waives in writing.

---

## Run logs

### Template

```
### Run YYYY-MM-DD — app.py vX.YY — Source=<path>
Operator: <agent/user>
Result summary: <n PASS / n FAIL / n BLOCKED / n N/A>

| ID | Result | Evidence |
|----|--------|----------|
| A1 | PASS/FAIL/BLOCKED/N/A | |
| A2 | | |
| A3 | | |
| A4 | | |
| A5 | | |
| A6 | | |
| A7 | | |
| A8a | | |
| A8b | | |
| A8c | | |
| A8d | | |
| A8e | | |
| A9a | | |
| A9b | | |
| A10 | | |

Notes:
-
```

### Run 2026-07-20 — checklist established (no conversion this session)

Operator: Intake Agent (Cursor Grok 4.5)  
Result summary: Checklist created; **0** conversion checks executed this session.

| ID | Result | Evidence |
|----|--------|----------|
| A1–A9b | N/A | Issue opened; await next conversion request |

Notes:
- Robert examples recorded: `10L171`, `TESTRD`, `130JEB`, `1659C2`, empty QuikPITv/Cv, annuity + `9*` rules.
- Gate FAIL pending Eric/CSO answers (see Dependency Gate).

### Run 2026-07-20 — app.py v58.20 — Single Table quikplan

Operator: Development / user request  
Result summary: **1 PASS** (A1) · **1 BLOCKED** (A2) · remainder not evaluated

| ID | Result | Evidence |
|----|--------|----------|
| A1 | **PASS** | `1668SP`, `10L171`, `10L172`, `1L17SP`: PAYYRS=1; S/Q/M/B=0 |
| A2 | **BLOCKED** | All 141 DEFICIENCY=N; awaiting CSO |
| A3–A9b | N/A | Not in scope this run |

Notes:
- Output: `QLA_Migration/Output/quikplan.csv`
- Log: `QLA_Migration/Logs/_single_quikplan_test_log.txt`

### Run 2026-07-20 — app.py v58.21 — Single Table quikplan (A4–A9 fixes)

Operator: Development / user request  
Result summary: **7 PASS** · **1 PARTIAL** · **1 BLOCKED** · **4 OPEN/N/A**

| ID | Result | Evidence |
|----|--------|----------|
| A1 | **PASS** | `1668SP`, `10L171`, `10L172`, `1L17SP`: PAYYRS=1; S/Q/M/B=0 |
| A2 | **BLOCKED** | All 141 DEFICIENCY=N; awaiting CSO |
| A3 | **BLOCKED** | 15 plans missing PVO defaults; awaiting Eric |
| A4 | **PASS** | 0 blank-PLAN rows in QuikPl*.csv; emit filter added |
| A5 | **OPEN** | Basis scope not evaluated; awaiting Eric |
| A6 | **PARTIAL** | 47 orphan flags cleared; 2 plans GP keys + STVARYGP=N remain |
| A7 | **OPEN** | 126/141 VARGP=4 with QuikPlGp keys; awaiting Eric (Item 09) |
| A8a | **PASS** | A-prefix PAR=0 (A60MIR, A96DAR) |
| A8b | **PASS** | A-prefix VARDB=0 |
| A8c | **OPEN** | Awaiting Eric — annuity interest scope |
| A8d | **OPEN** | Awaiting Eric — schg scope |
| A8e | **PASS** | A-prefix PLANVALOPT=N; all *VARY*=N |
| A9a | **OPEN** | Supp type field name — awaiting Eric |
| A9b | **PASS** | 56 prefix-9 plans; PAR=1 count 0 |

Notes:
- Engine: `apply_issue_a_plan_setup` — A6 orphan=47, A8 plans=2, A8e cells=19, A9b PAR=26
- Verify: `Issue_Log_Items/Issue_A/scripts/verify_issue_a_a4_a9.py`
- Test reload: `QLA_Migration/Output/Test_Validation/quikplan.csv`
- Email ready: `Issue_A_Email_Questions.md`

### Run 2026-07-20 — app.py v58.22 — QuikUwpo emit (A10)

Operator: Development / Approved for Development (A10)  
Result summary: **A10 PASS**

| ID | Result | Evidence |
|----|--------|----------|
| A10 | **PASS** | `QuikUwpo.csv` 5 rows: 00, NS, PR, SM, ST; 0 dupes; full QuikPlUw coverage |

Notes:
- Output: `QLA_Migration/Output/rates/QuikUwpo.csv`
- Test reload: `QLA_Migration/Output/Test_Validation/rates/QuikUwpo.csv`
- Wired into rate emit (CSV + DBF) for future Rate Tables runs
- Verify: `Issue_Log_Items/Issue_A/scripts/verify_issue_a_a10_quikuwpo.py`
