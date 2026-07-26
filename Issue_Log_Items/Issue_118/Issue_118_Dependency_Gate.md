# Issue #118 — Dependency Gate

**Issue:** #118 — Align QLAdmin underwriting class codes/labels to client "Underwriting Classes by Form"
**Framework stage:** Dependency Gate (Stage 3 of 8)
**Generated:** 2026-07-26
**Agent:** Cursor Grok 4.5
**Code changes:** none (prohibited at this stage)

---

## Status: **FAIL — Blocked — Awaiting Client Clarification**

The client catalog spreadsheet is in-repo and the touch surfaces are fully inventoried, but Development cannot safely remap keys without a confirmed LifePRO-letter → client-code matrix by form family. Implementing the wrong meaning of `S` (Smoker vs Standard) or inventing L14 `ST`/`PQ`/`PR` rate rows would corrupt the rate package and policy joins.

Per Framework: **do not proceed to Risk** until this gate PASSes (or the user waives specific OQs in writing).

---

## 1. Checklist

### Source data

| Check | Met? | Evidence |
|-------|------|----------|
| Client UW catalog present | **Met** | `docs/Underwriting Classes by Form.xlsx` (42 forms) |
| Rate extract with UNDERWRITING_CLASS | **Met** | `Rate_Table_Extract_20260427.csv` |
| Policy UW source | **Met** | `PPBEN_PolicyBenefit_Extract_20260630.csv` |
| Re-extract required? | **No** | Remap is conversion-side |

### Field definitions

| Check | Met? | Evidence |
|-------|------|----------|
| QLAdmin UWCLASS C(2) on rate keys | **Met** | `rate_dbf_schema.py` |
| QuikPlUw / QuikUwpo layouts | **Met** | Help §7.230 / member schema; Issue A A10 |
| quikridr.MUWCLASS | **Met** | Rulebook + `map_rider_uwclass` |
| LifePRO letter semantics by form | **Missing** | Global map conflicts with sheet (OQ-1) |
| L14 rate source for ST/PQ/PR | **Missing** | Rate_Table L14 = letter `N` only (OQ-2) |

### Client clarification

| Check | Met? | Evidence |
|-------|------|----------|
| Scope: change keys + rates + all UW uses | **Met** | Client request at issue open |
| Letter→code matrix approved | **Missing** | Planning §4a / §5 OQ-1 |
| QuikUwpo single label per code | **Missing** | OQ-3 |
| Forms not on sheet | **Missing** | OQ-4 (ISWL / riders) |
| UAT acceptance policies | **Missing** | OQ-6 |

### Evidence

| Check | Met? | Evidence |
|-------|------|----------|
| Before-state measurable | **Met** | Current Output rates + QuikPlUw + QuikUwpo + quikridr |
| Spreadsheet parsed | **Met** | Intake / Planning; codes ST/PR/SM/BL/NT/PQ |
| Named UAT policies | **Missing** | OQ-6 |

### Regression guards

| Check | Met? | Evidence |
|-------|------|----------|
| Preserves #25 MPOLICY | **Met** | Out of scope |
| Preserves #26 MPREM | **Met** | Out of scope |
| No unrelated rulebook edits planned | **Met** | Only MUWCLASS map / notes |

---

## 2. Blockers (owner + requested action)

| ID | Blocker | Owner | Requested action |
|----|---------|-------|------------------|
| B1 | LifePRO `S`/`B`/`N`/`Q` → client codes by form family not signed off | **Client / Warren** | Confirm or correct Planning §4a matrix |
| B2 | L14 sheet has NT/ST/PQ/PR; rate extract only has `N` | **Client / Actuarial** | State where ST/PQ/PR rates come from, or confirm membership-only |
| B3 | Fleet QuikUwpo labels for PR/SM/ST/BL/NT/PQ | **Client** | Approve one label per code |
| B4 | Plans absent from spreadsheet (ISWL 1658/1659, riders, etc.) | **Client** | Keep / remap / add to sheet |

---

## 3. What is already ready (does not block inventory)

- Full touch-point list in Planning §11 (maps, rate loaders, quikridr, validators, CSO, Issue A A10, Output artifacts).
- Clear before-state code set: `00`, `NS`, `SM`, `PR`, `ST`.
- Clear new codes required by sheet: `BL`, `NT`, `PQ` (plus retained `ST`, `PR`, `SM`).

---

## 4. Recommended issue status

**Blocked — Awaiting Client Clarification**

When B1–B4 answered (or waived): re-run Dependency Gate → expect PASS → Risk → Development approval.

---

## 5. Gate criteria (G2)

- [x] Dependency gate document published
- [x] Status is FAIL with no advancement to Risk
- [x] Tracking sheet status updated (see `Issue_118_Tracking_Sheet_Row.tsv`)
- [x] No code changes
