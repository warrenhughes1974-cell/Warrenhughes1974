# Issue #118 — Dependency Gate

**Issue:** #118 — Align QLAdmin underwriting class codes/labels to client "Underwriting Classes by Form"
**Framework stage:** Dependency Gate (Stage 3 of 8)
**Generated:** 2026-07-26  
**Re-evaluated:** 2026-08-07 (Eric clarifications); **2026-08-08** (all client clarifications closed)  
**Agent:** Cursor Grok 4.5  
**Code changes:** none (prohibited at this stage)

---

## Status: **PASS**

All client clarification blockers are closed. Spreadsheet + Eric answers + Warren lock decisions are recorded in `Issue_118_Client_Clarification_20260807.md` (§1–§12).

**B9** (re-prove Closed #136 PVO/UW flags + Issue A A10) is a **Regression** task after Development — not a Dependency Gate hold.

Per Framework: proceed to **Risk**, then stop for **Development approval**.

Records: `Issue_118_Client_Clarification_20260807.md`, `Issue_118_Review_Findings_20260807.md`, `Issue_118_UAT_Example_Policies.md`

---

## 1. Checklist

### Source data

| Check | Met? | Evidence |
|-------|------|----------|
| Client UW catalog present | **Met** | `docs/Underwriting Classes by Form.xlsx` (42 forms) |
| Rate extract with UNDERWRITING_CLASS | **Met** | `Rate_Table_Extract_20260427.csv` |
| Policy UW source | **Met** | `PPBEN_PolicyBenefit_Extract_20260630.csv` |
| Re-extract required? | **No** | Remap is conversion-side (unless L14 needs more rate letters) |

### Field definitions

| Check | Met? | Evidence |
|-------|------|----------|
| QLAdmin UWCLASS C(2) on rate keys | **Met** | `rate_dbf_schema.py` |
| QuikPlUw / QuikUwpo layouts | **Met** | Help §7.230 / member schema; Issue A A10 |
| quikridr.MUWCLASS | **Met** | Rulebook + `map_rider_uwclass` |
| L14 LifePRO letter semantics | **Met** | Eric approved N→NT, T→ST, Q→PQ, R→PR |
| Form-aware `S` / `B` semantics | **Met** | Clarification §5 — spreadsheet is source of truth |
| L14 rate source for ST/PQ/PR | **Met (scoped)** | Premiums in PAAGERAT; CV/RV/NP/NF stay `N` only — gap documented per Clarification §7 |

### Client clarification

| Check | Met? | Evidence |
|-------|------|----------|
| Scope: change keys + rates + all UW uses | **Met** | Client request at issue open |
| L14 letter→code matrix | **Met** | Clarification §1 |
| QuikUwpo single label per code | **Met** | Clarification §3 |
| ISWL forms not on sheet / membership | **Met** | ST + PR (Clarification §2) |
| Non-ISWL riders / other unlisted | **Met** | Clarification §9 — keep current |
| Named UAT policies | **Met** | `Issue_118_UAT_Example_Policies.md` |
| Letter→code for `S`/`B` by form family | **Met** | Clarification §5 |
| Drop NS from QuikUwpo | **Met** | Clarification §10 |

### Evidence

| Check | Met? | Evidence |
|-------|------|----------|
| Before-state measurable | **Met** | Current Output rates + QuikPlUw + QuikUwpo + quikridr |
| Spreadsheet parsed | **Met** | Intake / Planning; codes ST/PR/SM/BL/NT/PQ |
| Eric answers recorded | **Met** | `Issue_118_Client_Clarification_20260807.md` |
| Named UAT policies | **Met** | `Issue_118_UAT_Example_Policies.md` |

### Regression guards

| Check | Met? | Evidence |
|-------|------|----------|
| Preserves #25 MPOLICY | **Met** | Out of scope |
| Preserves #26 MPREM | **Met** | Out of scope |
| No unrelated rulebook edits planned | **Met** | Only MUWCLASS map / notes |

---

## 2. Blockers (owner + requested action)

| ID | Blocker | Status | Owner | Requested action |
|----|---------|--------|-------|------------------|
| B1a | L14 `N/T/Q/R` → NT/ST/PQ/PR | **CLOSED** | — | Eric approved 2026-08-07 |
| B1b | Form-aware `S→SM` vs `S→ST`, `B→BL` | **CLOSED** | — | Spreadsheet is source of truth (Clarification §5) |
| B2 | L14 ST/PQ/PR missing CV/reserve grids (premiums exist) | **CLOSED** | — | Map policies + emit premiums; do **not** invent/share CV; note missing cash values on final report (Clarification §7, 2026-08-08). Other sheet-vs-rate gaps (non-L14) stay under B4b. |
| B3 | Fleet QuikUwpo labels | **CLOSED** | — | Eric confirmed BL/NT/PQ/PR/SM/ST labels |
| B4a | ISWL membership | **CLOSED** | — | ST + PR |
| B4b | Non-ISWL riders / other unlisted plans (incl. 3 L10-family coverages) | **CLOSED** | — | Keep current mapping; only change spreadsheet/Eric items (Clarification §9) |
| B5 | Class-`0` / sheet-ST forms — re-key to ST or keep `00`? | **CLOSED** | — | Keep **`00`**; QuikUwpo/QuikPlUw descr = **Standard**; do not remap to ST (Clarification §4) |
| B6 | Blank `UNDERWRITING_CLASS` on Standard-only forms (SAL ML / SAL OL) | **CLOSED** | — | Spreadsheet = Standard only → treat blank as Standard / code `00` (Clarification §12) |
| B7 | `NT` / `PQ` labels overflow `UWDESCR` C(20) | **CLOSED** | — | Truncate to fit C(20): `STANDARD NON-TOBACCO` / `PREFERRED NON-TOBAC` (Clarification §8) |
| B8 | Older MUWCLASS sample expects `Q→NS` (`validate_issue59_muwclass.py`) | **CLOSED — not a blocker** | Conversion | Update sample to `PQ` in #118 Development (v57.83 UW sample only; not client Closed #59 MSTATUS) |
| B9 | Closed **#136** PVO/UW flags and Issue A **A10** move when class counts change | **CLOSED for Gate** (Regression task) | Conversion | Explicit re-proof in Regression after Development (Review F8) |

Detail and evidence: `Issue_118_Review_Findings_20260807.md`.

---

## 3. What is already ready

- Full touch-point list in Planning §11.
- Before-state code set: `00`, `NS`, `SM`, `PR`, `ST`.
- New codes required: `BL`, `NT`, `PQ` (plus retained `ST`, `PR`, `SM`).
- Locked labels for QuikUwpo (plus `00` = **Standard**, not Not Applicable).
- Locked L14 policy letter map.
- Locked ISWL QuikPlUw target membership: ST, PR.
- Locked class-`0` handling: stay on code `00` (no `00→ST` re-key).
- Locked form-aware letter map from spreadsheet (`B→BL`; `S` by form family).
- Locked validation standard: **no orphan MUWCLASS** — every policy must have a valid QLA rate class (Clarification §6).
- Locked L14 value-grid handling: map policies + emit premiums; **no invented CV** for ST/PQ/PR; final-report gap note required (Clarification §7).
- Locked unlisted plans: keep current mapping (Clarification §9).
- Locked QuikUwpo: **drop NS** (Clarification §10).
- UAT anchors published (`Issue_118_UAT_Example_Policies.md`).

---

## 4. Recommended issue status

**Ready for Risk Review**

Dependency Gate **PASS**. Next: Risk → stop for Development approval.

---

## 5. Gate criteria (G2)

- [x] Dependency gate document published
- [x] Status **PASS** — clarifications complete
- [x] Tracking sheet status updated (see `Issue_118_Tracking_Sheet_Row.tsv`)
- [x] Clarification answers recorded
- [x] No code changes
