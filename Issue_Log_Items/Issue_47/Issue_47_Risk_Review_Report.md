# Issue #47 — Risk Review Report

**Issue:** #47 — Bill Day zero fallback from Paid-To day  
**Framework stage:** Risk Agent (G3)  
**Status:** **GO** — Ready for Development (await explicit Development approval)  
**Fallback simulated:** Yes — read-only before/after on full quikmstr join  
**Generated:** 2026-07-09  
**Agent:** Risk Agent — read-only review (no production code in this stage)

**Status note:** Risk analysis only — no production code changes unless later approved.

---

## Go / No-Go Recommendation

**GO** — Surgical `quikmstr.MBILLDAY` fallback only:

When mapped Bill Day is **0/blank**, set `MBILLDAY = day-of-month(PAID_TO_DATE)`. Preserve all non-zero `#21B` values. Simulation shows **2967** corrections, **0** non-zero regressions, **0** fallback failures, and BA sample `018187C`: **0 → 28**.

Blast radius is large in row count but **single-field** and fully specified by the issue log. Soft edge (6 Paid-To ≠ Billed-To) accepted per issue wording (use Paid To).

---

## 1. Current vs Proposed Mapping

| Field | Current | Proposed | Change? |
|-------|---------|----------|---------|
| `quikmstr.MBILLDAY` | `POLICY_BILL_DAY` pass-through (#21B), including `0` | Non-zero: unchanged; **0/blank → `EXTRACT_DAY(PAID_TO_DATE)`** | **Yes** (zeros only) |
| `MPAIDTO` | `PAID_TO_DATE` | Unchanged | **No** |
| `MBILLTO` | `BILLED_TO_DATE` | Unchanged | **No** |
| `MBLLDOM` / `MORGBLLDOM` | Blank | Unchanged (out of scope) | **No** |

---

## 2. Premium / Related Fields Untouched

| Target | Source | Touched? |
|--------|--------|----------|
| `quikmstr.MMODEPREM` | `MODE_PREMIUM` | **No** |
| `quikridr.MPREM` | #26 | **No** |
| Modal factors MSEMI/MQTRL/MMTHD/MMTHB | #36 | **No** |
| MPOLICY padding | #25 | **No** |
| `MSTATUS` / #13 | PPOLC status path | **No** |
| Non-zero `MBILLDAY` | `POLICY_BILL_DAY` #21B | **No** |

---

## 3. Repo References

| Location | Role |
|----------|------|
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` L9 | Current `POLICY_BILL_DAY → MBILLDAY` |
| `QLA_Migration/app.py` / root `app.py` `extract_day()` | Day extract helper |
| Rulebook note hook `EXTRACT_DAY` | Existing transform path |
| `tools/validators/validate_issue21.py` | #21B sample checks (extend / add #47) |

**Preferred surgical shape:** After quikmstr row mapping (or dedicated post-pass on `MBILLDAY`), if value normalizes to 0/blank, replace with `str(int(extract_day(PAID_TO_DATE)))` so style matches current unpadded days (`1`, `15`, `28` — not `01`).

---

## 4. Population Analysis

| Metric | Count |
|--------|------:|
| Total matched quikmstr rows | 5083 |
| Rows that would change (`MBILLDAY`) | **2967** |
| Rows unchanged | **2116** |
| Non-zero rows that would change (regression) | **0** |
| Zero rows with no usable Paid-To day | **0** |
| Zero rows where Paid-To day ≠ Billed-To day | **6** |

### Breakdown by `MSTATUS` (changing rows only)

| MSTATUS | Would change |
|---------|-------------:|
| 22 | 1128 |
| 53 | 755 |
| 55 | 430 |
| 54 | 188 |
| 44 (ETI) | 152 |
| 45 (RPU) | 144 |
| 57 | 110 |
| Other | 60 |

### After-day distribution (top, changing rows)

| Proposed day | Count |
|-------------:|------:|
| 1 | 790 |
| 15 | 219 |
| 20 | 100 |
| 10 | 99 |
| 28 | 94 |

Evidence: `evidence/issue47_risk_impact_summary.csv`, `evidence/issue47_risk_delta_simulation.csv`

### Informational — Paid-To day vs Issue day

Of the 2967 changes, **2946** proposed days equal the **issue-date day**. That is expected for anniversary billing calendars; it is **not** a return to the #21B defect. #21B failure mode was: **non-zero specified bill day overwritten by issue day** (e.g. 15→19). This fix **never** touches non-zero `POLICY_BILL_DAY` (simulated regressions = 0). Authority for zeros is **Paid To**, per BA.

---

## 5. Fallback Recommendation

| Option | Rows changed | Assessment |
|--------|-------------:|------------|
| A. Paid-To day when bill day 0 | 2967 | **Recommended** — matches issue text + screenshot |
| B. Billed-To day when bill day 0 | ~2961 same; 6 differ | Reject as primary — contradicts issue wording |
| C. Issue-date day when bill day 0 | ~2946 overlap | Reject — reopens #21B confusion; BA said Paid To |
| D. Leave zeros | 0 | Reject — fails `018187C` UAT |

**Recommended:** Option A. For the **6** Paid≠Billed edges, still use Paid To (`evidence/issue47_paid_ne_billed_edges.csv`).

---

## 6. Trace Policies

| Policy | Before | Proposed | Pass? |
|--------|-------:|---------:|-------|
| `018187C` | 0 | **28** | Yes (BA) |
| `010143726C` | 0 | 1 | Yes |
| `010165095C` | 0 | 1 | Yes |
| `010171334C` | 0 | 19 | Yes |
| `010713704C` | 15 | 15 | Yes (#21B) |
| `010765930C` | 28 | 28 | Yes (#21B) |
| `010718309C` | 22 | 22 | Yes (#21B) |
| `010818663C` | 12 | 12 | Yes (#21B) |

---

## 7. Top edge cases (Paid-To ≠ Billed-To)

| Policy | Paid-To | Billed-To | Proposed MBILLDAY |
|--------|---------|-----------|------------------:|
| `011115534C` | 20200813 | (blank/0) | 13 |
| `011174600C` | 20250803 | 20251016 | 3 |
| `011180300C` | 20231001 | 20231123 | 1 |
| `011192047C` | 20210809 | 20211001 | 9 |
| `011253007C` | 20180509 | 20180615 | 9 |
| `019731970C` | 20241009 | 20250829 | 9 |

---

## 8. Material Calculation Impact

- **Intentional:** Bill Day calendar correction on ~58% of policies where LifePRO stored `POLICY_BILL_DAY=0`.
- **Not a premium recalculation:** Mode premium, rider premium, status, dates unchanged.
- **Billing systems:** QLAdmin Bill Day drives display/draft day-of-month; Risk accepts BA-directed correction.

---

## 9. Prior Fix Preservation

| Check | Result |
|-------|--------|
| Issue #25 MPOLICY padding | **Preserved** — not in change path |
| Issue #26 MPREM / MMODPREM | **Preserved** — not touched |
| Issue #21B non-zero Bill Day | **Preserved** — 0 simulated regressions; samples 15/28/22/12 hold |
| Issue #36 modal factors | **Preserved** |

---

## 10. Regression Testing Checklist (for Validation Agent)

- [ ] `018187C`: `MBILLDAY=28`
- [ ] All previously zero `MBILLDAY` = Paid-To day (fleet assert)
- [ ] #21B samples unchanged: `010713704C=15`, `010765930C=28`, `010718309C=22`, `010818663C=12`
- [ ] Non-zero before count still 2116 with identical values
- [ ] `MPAIDTO` / `MBILLTO` / `MMODEPREM` / `MSTATUS` unchanged vs pre-fix baseline
- [ ] Row count `quikmstr` stable (5083)
- [ ] Schema / column order unchanged
- [ ] Spot-check 6 Paid≠Billed edges use Paid-To day

---

## 11. Recommended Development Agent Task

1. In quikmstr conversion path (both root `app.py` and `QLA_Migration/app.py` if duplicated, or shared helper): after `MBILLDAY` is mapped from `POLICY_BILL_DAY`, if normalized value is `''`/`0`, set `MBILLDAY` from `extract_day(PAID_TO_DATE)` (or mapped `MPAIDTO`), normalized as `str(int(...))` when numeric.
2. Update rulebook note on the `POLICY_BILL_DAY` line to document Issue #47 zero-fallback (comment only — or implement via code post-pass; prefer code post-pass for clarity).
3. Do **NOT** change: non-zero bill days, `MPAIDTO`/`MBILLTO`, premiums, status, #25/#26, `MBLLDOM`.
4. Version bump both `APP_VERSION` → **v57.65**.
5. Add `Issue_Log_Items/Issue_47/scripts/_validate_issue47_billday.py` (or `QLA_Migration/_validate_issue47_billday.py`) covering checklist §10.
6. Keep evidence CSVs under `Issue_Log_Items/Issue_47/evidence/`.

---

## Appendix

| Artifact | Path |
|----------|------|
| Impact summary | `evidence/issue47_risk_impact_summary.csv` |
| Full delta simulation | `evidence/issue47_risk_delta_simulation.csv` |
| Paid≠Billed edges | `evidence/issue47_paid_ne_billed_edges.csv` |
| Planning | `Issue_47_Planning_Report.md` |
| Dependency Gate | `Issue_47_Dependency_Gate.md` (PASS) |

**Next:** User approval → Development Agent.
