# Issue #47 — Intake Summary

**Issue:** #47 — Bill Day zero fallback from Paid-To day  
**Date:** 2026-07-09  
**Framework stage:** Intake complete (G0)  
**Status:** Approved → Planning  
**Owner:** Conversion (Warren) · **Assigned:** Warren  
**Business status:** No-Go for Development until G1 + G2 + G3  

---

## 1. Client / business symptom (verbatim + normalized)

**Issue log (verbatim):**

> Bill day needs to match the day intoo paid to date of the bill day is zero.

**Normalized:**

When QLAdmin **Bill Day** (`quikmstr.MBILLDAY`) is **0**, set it to the **day-of-month** from the policy **Paid To** date (`MPAIDTO` / LifePRO `PAID_TO_DATE`). Non-zero Bill Day values must remain as mapped today.

**What the BA sees (screenshot — policy `018187C`):**

| Field | Value |
|-------|-------|
| Policy | `018187C` |
| Status | RPU (45) |
| Bill Day | **0** (highlighted defect) |
| Paid To | **07/28/1966** → day **28** (expected Bill Day) |
| Billed To | 07/28/2026 |
| Issued | 12/28/1949 |
| Mode / Mode Prem | 12 / 0.00 |

Screenshot saved: `evidence/018187C_Policy_Display_BillDay0.png`

---

## 2. Suspected domain

| Layer | Table / path | Role |
|-------|--------------|------|
| Target | `quikmstr.MBILLDAY` | Bill Day on Policy Display |
| Related dates | `quikmstr.MPAIDTO` / `MBILLTO` | Paid To / Billed To (already mapped) |
| Source | `PPOLC.POLICY_BILL_DAY`, `PAID_TO_DATE` | Bill day + paid-to |
| Prior fix | Issue **#21B** | `POLICY_BILL_DAY → MBILLDAY` (do not regress) |

**Domain:** Policy master billing calendar day — **not** modal premiums, loans, or status.

---

## 3. Intake evidence (already measured — Planning will formalize)

| Check | Result |
|-------|--------|
| Current output `018187C` | `MBILLDAY=0`, `MPAIDTO=19660728`, `MBILLTO=20260728`, `MSTATUS=45` |
| LifePRO `9018187` → `018187C` | `POLICY_BILL_DAY=0`, `PAID_TO_DATE=19660728` |
| `POLICY_BILL_DAY` vs `MBILLDAY` parity | **5083 / 5083** exact match — **#21B mapping is correct** |
| Source zeros | **2967 / 5084** PPOLC rows have `POLICY_BILL_DAY=0` (~58%) |
| Suspected root cause | Faithful pass-through of source **0**; missing **fallback** when source bill day is zero |

This is **not** a regression of #21B (issue-date day). It is a **gap** after #21B: zero source values need a Paid-To-day fallback per BA rule.

---

## 4. In scope / out of scope (first pass)

### In scope

- When `POLICY_BILL_DAY` is 0 / blank, derive `MBILLDAY` from day of `PAID_TO_DATE`.
- Preserve non-zero `POLICY_BILL_DAY` → `MBILLDAY` (#21B).
- Validate on `018187C` (expect **28**) and fleet zero population.

### Out of scope (unless Planning expands)

- Changing `MPAIDTO` / `MBILLTO` mapping.
- Populating `MBLLDOM` / `MORGBLLDOM` (currently blank; not cited by BA).
- Reverting #21B to issue-date extraction.
- Inventing bill day when `PAID_TO_DATE` is also missing (fleet: all 2967 zeros have usable paid-to day).

---

## 5. Related issues

| Issue | Relationship |
|-------|----------------|
| **#21B** | Parent Bill Day mapping — **released**; this issue adds zero-fallback only |
| **#25** | MPOLICY padding — must not change |
| **#26** | MPREM — unrelated; must not change |
| **#36** | Modal factors on quikmstr — unrelated |

---

## 6. Artifact inventory

| Artifact | Status |
|----------|--------|
| BA / issue-log rule (zero → Paid-To day) | Provided |
| Screenshot `018187C` Policy Display | Provided → `evidence/` |
| PPOLC extract `..._20260630.csv` | Present |
| Current `Output/quikmstr.csv` | Present (defect reproducible) |
| Issue #21B rulebook line | Present (`Sync_Rulebook_quikmstr.csv`) |
| Written confirmation: Billed-To vs Paid-To if days differ | Optional — fleet almost always same day when bill day is 0 |

---

## 7. Immediate blockers visible at intake

| Blocker | Blocks? | Notes |
|---------|---------|-------|
| Source extracts | No | PPOLC + output available |
| Field definitions | No | `MBILLDAY` / `MPAIDTO` known |
| Business rule | No for Planning | Issue text states the rule |
| Blast radius (~2967 policies) | No for Planning | Risk must quantify |

---

## 8. Severity / owner / priority

| Field | Value |
|-------|--------|
| Severity | **Medium** — billing calendar day wrong on majority of policies with source bill day 0; sample is RPU with mode prem 0 |
| Owner | Conversion |
| Priority (Go/No-Go) | **No-Go** until Risk; expected Conditional/Go after G1–G3 |
| Recommended next status | **Planning** |

---

## 9. Gate G0 checklist

- [x] Issue folder created: `Issue_Log_Items/Issue_47/`
- [x] Intake summary written
- [x] Example policies listed (`018187C`)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

---

## 10. Recommended next stage

**Planning Agent** — document:

1. Fallback rule: `MBILLDAY = POLICY_BILL_DAY` if non-zero; else `EXTRACT_DAY(PAID_TO_DATE)`.
2. Preserve #21B for non-zero source values.
3. Impact: ~2967 policies; sample after-state `018187C → 28`.
4. Open question only if Paid-To day ≠ Billed-To day (rare: 6 of 2967).
