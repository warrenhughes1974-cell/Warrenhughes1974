# Issue #47 — Planning Report

**Issue:** #47 — Bill Day zero fallback from Paid-To day  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning complete — Ready for Dependency Gate / Risk  
**Generated:** 2026-07-09  
**Agent:** Planning Agent (read-only analysis)

---

## 1. Executive Finding

QLAdmin Bill Day (`quikmstr.MBILLDAY`) is **0** on policy `018187C` while Paid To is **07/28/1966**. BA rule: when Bill Day is zero, set it to the **day of Paid To** (expect **28**).

Root cause is **not** a broken #21B mapping. Fleet check shows **100% parity** between `PPOLC.POLICY_BILL_DAY` and `MBILLDAY` (5083/5083). LifePRO stores `POLICY_BILL_DAY=0` on **2967** policies (~58%); the converter correctly passes that through. Issue #47 is a **post-#21B fallback gap**.

**Recommended direction:** Keep `POLICY_BILL_DAY → MBILLDAY` when non-zero; when source is 0/blank, set `MBILLDAY = EXTRACT_DAY(PAID_TO_DATE)`. Do not use Issue Date (that was the #21B defect).

---

## 2. Confirmed LifePRO Source Table/File(s)

| Source table | File pattern | In Source/ package? | Row count |
|--------------|--------------|---------------------|----------:|
| PPOLC Policy Master | `PPOLC_PolicyMaster_Extract_20260630.csv` | Yes | 5084 |

### Available source fields

| Field | Column / source | Populated % | Notes |
|-------|-----------------|------------:|-------|
| Policy number | `POLICY_NUMBER` | 100% | Crosswalk `9018187` → `018187C` |
| Specified bill day | `POLICY_BILL_DAY` | 100% (41.6% non-zero) | **0** on 2967 rows |
| Paid to | `PAID_TO_DATE` | 100% on zero-bill-day set | YYYYMMDD |
| Billed to | `BILLED_TO_DATE` | 100% | Day matches Paid-To on 2961/2967 zeros |
| Issue date | `ISSUE_DATE ` (trailing space in header) | Present | **Do not** use for Bill Day (#21B) |
| Loan / AR bill day | `LOAN_BILL_DAY`, `AR_BILL_DAY` | Often 0 | Out of scope |

---

## 3. Confirmed QLAdmin Target Structure

| Table | Field | Type | Length | Source (Help / schema) |
|-------|-------|------|--------|------------------------|
| `quikmstr` | `MBILLDAY` | numeric / day-of-month | schema list in `app.py` | Policy Display “Bill Day” |
| `quikmstr` | `MPAIDTO` | date YYYYMMDD | — | Already mapped from `PAID_TO_DATE` |
| `quikmstr` | `MBILLTO` | date YYYYMMDD | — | Already mapped from `BILLED_TO_DATE` |
| `quikmstr` | `MBLLDOM` / `MORGBLLDOM` | — | — | Present in schema; currently blank; **out of scope** unless Risk expands |

**Repo references:**

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` L9 | `POLICY_BILL_DAY,MBILLDAY,,… (Issue 21B)` |
| `QLA_Migration/app.py` `extract_day()` | Day extract helper (YYYYMMDD or M/D/Y) |
| `QLA_Migration/app.py` rulebook note `EXTRACT_DAY` | Existing transform hook |
| `tools/validators/validate_issue21.py` | #21B sample assertions |

---

## 4. Required Source-to-Target Field Mapping

| LifePRO source | LifePRO field | QLAdmin target | Transformation | Change? |
|----------------|---------------|----------------|----------------|---------|
| PPOLC | `POLICY_BILL_DAY` (if ≠ 0) | `MBILLDAY` | Pass-through (existing #21B) | **No** |
| PPOLC | `PAID_TO_DATE` (only if bill day 0/blank) | `MBILLDAY` | `EXTRACT_DAY` → day 1–31 | **Yes** |
| PPOLC | `PAID_TO_DATE` | `MPAIDTO` | Existing date map | **No** |
| PPOLC | `BILLED_TO_DATE` | `MBILLTO` | Existing date map | **No** |

### Fields that must remain unchanged

| Target | Current source | Touch this issue? |
|--------|----------------|-------------------|
| Non-zero `MBILLDAY` | `POLICY_BILL_DAY` (#21B) | **No** — preserve |
| `MPAIDTO` / `MBILLTO` | Paid/Billed dates | **No** |
| `quikridr.MPREM` | #26 | **No** |
| MPOLICY padding | #25 `format_qladmin_mpolicy` | **No** |
| Modal factors MSEMI/… | #36 | **No** |

### Proposed implementation shape (Development — do not implement yet)

Prefer **surgical** post-map or rulebook transform:

1. **Option A (preferred):** After rulebook apply for quikmstr, if `MBILLDAY` in {`''`,`0`}, set from `extract_day(PAID_TO_DATE)` (or from already-mapped `MPAIDTO`).
2. **Option B:** Rulebook note / special transform on `POLICY_BILL_DAY` row: “use field unless zero else EXTRACT_DAY(PAID_TO_DATE)”.

Either must leave non-zero source values untouched.

---

## 5. Open Client Questions

| # | Question | Blocks Development? | Disposition |
|---|----------|---------------------|-------------|
| Q1 | Confirm fallback source is **Paid To** (not Billed To / Issue Date) when Bill Day = 0? | Soft | Issue text says Paid To; fleet Paid-To day = Billed-To day on **2961/2967** zeros |
| Q2 | For the **6** policies where Paid-To day ≠ Billed-To day, still use Paid To? | Soft | Default **Yes** per issue wording; Risk can accept |
| Q3 | Should `MBLLDOM` / `MORGBLLDOM` also be set? | No | Out of scope unless BA expands |

**No hard client blocker** for Planning → Risk if we accept issue-log wording as the business rule.

---

## 6. Recommended Formatting Rules

| Rule | Recommendation |
|------|----------------|
| Policy key | Crosswalk + 10-char MPOLICY padding (#25) — unchanged |
| Dates | Existing QLA date formatting for `MPAIDTO`/`MBILLTO` — unchanged |
| Bill day | Integer day **1–31** (match current non-zero style: unpadded `15`, `28`, not `015`) |
| Blanks / zeros | Treat `0`, `0.0`, blank as “missing specified bill day” → fallback |
| Fallback failure | If Paid-To day cannot be extracted, leave `0` and log (fleet currently 0 failures) |

---

## 7. Memo / Text / Special Handling

N/A.

---

## 8. Policy Number Key Handling

1. LifePRO `POLICY_NUMBER` → `Master_Crosswalk.csv` → QLA  
2. `format_qladmin_mpolicy()` for CHARACTER(10) keys (#25)  
3. Trace key: `9018187` → `018187C`

---

## 9. Estimated Record Counts

| Metric | Count | Basis |
|--------|------:|-------|
| PPOLC rows | 5084 | Source extract |
| quikmstr rows | 5083 | Current Output |
| `POLICY_BILL_DAY` / `MBILLDAY` = 0 | **2967** | Would receive fallback |
| Non-zero bill day (preserve #21B) | **2116** | Must not change |
| Fallback would set non-zero day | **2967** | All zeros have usable `PAID_TO_DATE` |
| Paid-To day ≠ Billed-To day (zeros) | **6** | Edge cases |

Evidence: `evidence/issue47_population_summary.csv`

---

## 10. Sample Trace

| Policy (QLA) | LifePRO LP | `POLICY_BILL_DAY` | `PAID_TO_DATE` | Before `MBILLDAY` | After (proposed) | Notes |
|--------------|------------|-------------------|:--------------:|------------------:|-----------------:|-------|
| `018187C` | 9018187 | 0 | 19660728 | **0** | **28** | BA screenshot / RPU |
| `010143726C` | 9010143726 | 0 | 20270501 | 0 | 1 | Active-style zero |
| `010165095C` | 9010165095 | 0 | 19881201 | 0 | 1 | RPU zero |
| `010171334C` | 9010171334 | 0 | 19821019 | 0 | 19 | Zero → paid day 19 |
| `010713704C` | 9010713704 | **15** | 20260719 | **15** | **15** | #21B preserve |
| `010765930C` | 9010765930 | **28** | 20260724 | **28** | **28** | #21B preserve |

Evidence: `evidence/issue47_sample_trace.csv`

---

## 11. Risks and Unknowns

| Risk | Severity | Mitigation |
|------|----------|------------|
| Large blast radius (~2967 `MBILLDAY` changes) | Medium | Risk Agent quantify by status; validation asserts only zeros change |
| Regress #21B (non-zero → wrong day) | High | Explicit preserve test on 713704C=15, 765930C=28 |
| Using Issue Date again | High | Forbidden; only Paid-To when source bill day is 0 |
| RPU/ETI with Mode Prem 0 still need Bill Day | Low | BA cited RPU sample — apply fleet-wide per rule |
| `MBLLDOM` left blank | Low | Out of scope |

---

## 12. Dependency Gate Preview

| Check | Met? |
|-------|------|
| Source file present | Yes |
| Field definitions confirmed | Yes |
| Client scope clear | Yes (issue text); soft Q1/Q2 |
| Example policies available | Yes (`018187C` + screenshot) |
| #25 / #26 preserved in plan | Yes |

---

## 13. Recommended Risk Agent Prompt

```
Proceed to Risk Agent for Issue #47.

Read AI_Agents/Risk_Agent.md and Issue_Log_Items/Issue_47/Issue_47_Planning_Report.md.

Do not code. Quantify before/after impact of:
  MBILLDAY = POLICY_BILL_DAY if non-zero else EXTRACT_DAY(PAID_TO_DATE)

Confirm:
- ~2967 policies change 0 → Paid-To day
- ~2116 non-zero #21B values unchanged
- Trace 018187C: 0 → 28
- No changes to MPAIDTO/MBILLTO/MPREM/MPOLICY padding

Produce go / conditional-go / no-go with fallback rules and validation plan.
```

---

## 14. Recommended Development Task (Do Not Implement)

1. Add surgical fallback after quikmstr bill-day mapping (or dedicated transform): if `MBILLDAY` is 0/blank → `extract_day(PAID_TO_DATE)` / `MPAIDTO`.
2. Do **not** alter non-zero `POLICY_BILL_DAY` path (#21B).
3. Version bump: both root `app.py` and `QLA_Migration/app.py` (`APP_VERSION`).
4. Validation script: `QLA_Migration/_validate_issue47_billday.py` (or under `Issue_Log_Items/Issue_47/scripts/`) asserting:
   - `018187C` → 28
   - All former zeros = Paid-To day
   - #21B samples unchanged (15, 28, etc.)
5. Regression: unrelated quikmstr columns unchanged; #25/#26 untouched.

---

## Appendix

- Intake: `Issue_47_Intake_Summary.md`
- Screenshot: `evidence/018187C_Policy_Display_BillDay0.png`
- Population: `evidence/issue47_population_summary.csv`
- Trace: `evidence/issue47_sample_trace.csv`
- Prior: Issue #21B — `POLICY_BILL_DAY → MBILLDAY` (v57.22 / v57.34)
