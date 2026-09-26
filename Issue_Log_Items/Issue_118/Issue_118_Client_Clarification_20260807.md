# Issue #118 — Client Clarification (2026-08-07)

**Source:** Eric responses on Warren’s confirmation email (UW-class conversion questions).  
**Recorded:** 2026-08-07  
**Code changes:** none

---

## Confirmed answers

### 1. L14 LifePRO letter → QLAdmin code — **APPROVED**

| LifePRO | QLAdmin | Label |
|---------|---------|-------|
| `N` | `NT` | Standard, Non-Tobacco |
| `T` | `ST` | Standard |
| `Q` | `PQ` | Preferred, Non-Tobacco |
| `R` | `PR` | Preferred |

### 2. Forms not on the spreadsheet / ISWL — **PARTIAL**

Eric: use **ST — Standard** and **PR — Preferred** for the **ISWL products**.

Notes:
- Sheet already lists 658/659 CEN* forms as `ST|PR` (aligned with this answer).
- Answer does **not** yet cover non-ISWL riders / other plans absent from the sheet, or whether annuity/`00` stays `00`.

### 3. QuikUwpo master labels — **CONFIRMED**

| Code | Label |
|------|-------|
| `BL` | Blended |
| `NT` | Standard, Non-Tobacco |
| `PQ` | Preferred, Non-Tobacco |
| `PR` | Preferred |
| `SM` | Standard Smoker |
| `ST` | Standard |

### 4. LifePRO class `0` / QLAdmin `00` — **APPROVED 2026-08-07 (Warren / Eric)**

**Decision:** Keep code **`00`**. Do **not** re-key rate grids or `MUWCLASS` from `00` → `ST`.

**Description:** QuikUwpo / QuikPlUw label for `00` is **Standard** (not Not Applicable). That matches how LifePRO labeled class `0`. Having both **`00` = Standard** and **`ST` = Standard** is intentional and accepted (same word, two keys — as in LifePRO).

**Scope:** Applies to the class-`0`-only plans (~68 QuikPlUw members today; ~18 forms the sheet called ST with 100% letter-`0` grids). No code change in this clarification pass — implement the label at Development with the rest of #118.

**Evidence:** Current Output still shows `00` / `NOT APPLICABLE`; L10-family plans that already use real Standard keep code `ST` / `STANDARD` (12 plans).

### 5. Spreadsheet is source of truth for form-aware letters — **APPROVED 2026-08-07 (Warren)**

**Decision:** **Underwriting Classes by Form** is the authoritative map for LifePRO letter → QLAdmin code by product/form. Match the spreadsheet. No separate one-letter global map.

**Locked letter rules (from the sheet):**

| LifePRO | QLAdmin | When |
|---------|---------|------|
| `B` | `BL` | L10 blended / smoker-blend family (sheet lists Blended) |
| `S` | `SM` | L10 smoker/blend forms (sheet lists Smoker) |
| `S` | `ST` | Preferred / Standard / ST-only forms (sheet lists Standard, not Smoker) |
| `P` | `PR` | Preferred (all forms that list it) |
| `0` | `00` | Single-class / non-varying — code stays `00`, descr Standard (§4) |

**Visible proof anchors used in discussion:**
- L10 LP95 / `1L1095`: policy `9011189929C` letter `B` → **BL** (today wrongly `ST`); `9011190516C` letter `S` → **SM**.
- L01 10Y LT / `5L0110`: policy `9011059291C` letter `S` → **ST** (today wrongly `SM`).

No code change in this clarification pass — implement at Development with the rest of #118.

### 6. No orphan UW codes — standard validation — **APPROVED 2026-08-07 (Warren)**

**Rule:** Every policy/rider benefit we convert must land on a **valid QLAdmin underwriting rate class**. Bare LifePRO letters (e.g. `R`, `T`, `Q`) or unknown codes must **not** pass through to `quikridr.MUWCLASS`.

**Valid QLA rate classes (target domain after #118):**  
`00` (Standard label), `ST`, `PR`, `SM`, `BL`, `NT`, `PQ` — plus retained legacy codes only while still in membership (`NS` until retired per OQ-D).

**How mapping works (example `R → PR`):**  
On L14, Eric’s map says LifePRO **`R` = Preferred** → write **`PR`**. Same for `T→ST`, `Q→PQ`, `N→NT`. Form-aware spreadsheet rules cover `S`/`B` elsewhere. Mapping is applied in both:
1. Policy `MUWCLASS` (so the policy can join rates)
2. Rate-table `UWCLASS` (so the rates exist under that key)

**Standard validation (must fail the release if broken):**
1. Every non-blank `quikridr.MUWCLASS` is in the approved QLA UW domain (no orphans: `R`, `T`, raw `Q`, junk, etc.).
2. That `MUWCLASS` exists on the plan’s QuikPlUw membership (or fleet QuikUwpo where applicable).
3. For rate-bearing plans, the policy’s `MUWCLASS` can join the **premium** rate key for that plan where those premiums exist. Known gap: L14 ST/PQ/PR have no cash-value / reserve grids in source (§7) — document on the final report; do not invent shared CV keys.

Implement as part of Issue #118 Validation (extend/replace Issue #59 MUWCLASS checks as needed). No code in this clarification pass.

### 7. L14 map policies correctly; do not invent cash values — **APPROVED 2026-08-08 (Warren)**

**Decision:**
1. **Map L14 policies** to the locked letter codes (`N→NT`, `T→ST`, `Q→PQ`, `R→PR`) — no orphan `T`/`R`/`Q` on `MUWCLASS`. `Q→PQ` is **L14-scoped** (Review F12: two `DISCHO29` rider rows inherit `Q` from an L14 base and must not become fleet-wide `PQ`).
2. **Emit L14 premium rates** for all four classes (stop dropping PAAGERAT `T`/`Q`/`R` rows).
3. **Do not invent or share** cash-value / reserve / net-premium / non-forfeiture grids for ST / PQ / PR. Source has those value tables for letter **`N` only** (confirmed F12 across Rate_Table + PDAGE).
4. **Final report notation (required):** state that cash values (and related value/reserve tables) are **missing** for L14 policies in underwriting classes **ST, PQ, and PR**. Example anchors: `9011208194C` (T→ST), `9011207210C` (Q→PQ), `9011215903C` (R→PR). Class NT keeps the existing `N` value grids.

**Not chosen:** copying/sharing the `N` CV grid under ST/PQ/PR.

No code change in this clarification pass — implement at Development with the rest of #118.

### 8. Truncate `NT` / `PQ` descriptions to C(20) — **APPROVED 2026-08-08 (Warren)**

`QuikPlUw.UWDESCR` / `QuikUwpo.UWDESCR` are **C(20)**. Eric’s full labels overflow:

| Code | Full label (Eric) | Length | Stored (truncate / fit C20) |
|------|-------------------|-------:|-----------------------------|
| NT | Standard, Non-Tobacco | 21 | `STANDARD NON-TOBACCO` (20) |
| PQ | Preferred, Non-Tobacco | 22 | `PREFERRED NON-TOBAC` (18) |

Other locked labels already fit: BL, PR, SM, ST, and `00` = Standard.

No code change in this clarification pass — implement at Development with the rest of #118.

### 9. Unlisted plans — keep current mapping — **APPROVED 2026-08-08 (Warren)**

Only change what Eric / the spreadsheet asks for. Plans and riders **not** on the spreadsheet keep today’s conversion mapping (including `DISCHO29` / `9DIS29` inherited-`Q` riders). No silent ST/PR default for unlisted coverages.

### 10. Drop `NS` from QuikUwpo — **APPROVED 2026-08-08 (Warren)**

Remove **`NS`** from the fleet QuikUwpo dropdown. L14 uses **`NT`**; ISWL uses **ST / PR**. Do not keep `NS` as a legacy dropdown value once #118 ships.

### 11. UAT example policies — **PUBLISHED 2026-08-08**

Screen-proof anchors are in `Issue_118_UAT_Example_Policies.md` (L10 B/S/P, L01 S/P, L14 N/T/Q/R, class-0 `00`, ISWL).

### 12. Blank `UNDERWRITING_CLASS` on Standard-only forms — **APPROVED 2026-08-08 (Warren)**

**Source table:** `PPBEN_PolicyBenefit_Extract_20260630.csv`, field `UNDERWRITING_CLASS`.

**Decision:** Where the spreadsheet lists the form as **Standard only** (including **SAL ML** and **SAL OL**), a blank LifePRO underwriting class is treated as **Standard**. Per Clarification §4 those class-`0` plans keep code **`00`** with description **Standard** (do not re-key to `ST`), so blank policies join the existing `00` rate keys.

**Base-benefit examples used for the call:**

| POLICY_NUMBER | BENEFIT_SEQ | BENEFIT_TYPE | PLAN_CODE | STATUS | UNDERWRITING_CLASS |
|---------------|-------------|--------------|-----------|--------|--------------------|
| 901353D732 | 1 | BA | SAL ML | A/CR | blank |
| 9012FG8217 | 1 | BA | SAL ML | T/DC | blank |
| 9014048 | 1 | BA | SAL ML | T/DC | blank |
| 901122D991 | 1 | BA | SAL OL | A | blank |
| 901222DC | 1 | BA | SAL OL | A/CR | blank |

(Other blank rows are mostly `FV` / `UV` non-base benefits; they follow the same Standard/`00` rule when on Standard-only forms.)

---

## Still open (needed before safe Development)

None for client clarification. Remaining work is Development implementation + Regression re-proof of Closed #136 PVO/UW flags and Issue A A10.

**Not a blocker:** older `validate_issue59_muwclass.py` sample `Q→NS` → update to `PQ` during #118 Development (v57.83 UW sample only; **not** client Closed #59 MSTATUS).

---

## Locked rules (ready for Development when gate clears)

- `B` → `BL` on L10 blended family (spreadsheet)
- `S` → `SM` on L10 smoker/blend forms; `S` → `ST` on Preferred/Standard / ST-only forms (spreadsheet)
- `P` → `PR`
- ISWL QuikPlUw membership = `ST`, `PR` only (per Eric)
- Class `0` → code `00`, description Standard (not re-key to ST)
- L14 letters per §1 (`N→NT`, `T→ST`, `Q→PQ` L14-scoped, `R→PR`)
- QuikUwpo labels per §3 (+ `00` = Standard; **no `NS`**)
- **No orphan MUWCLASS codes** — every converted policy must have a valid QLA rate class; enforce with a standard validator (§6)
- **L14:** map policies + emit four premium classes; **do not invent CV** for ST/PQ/PR; **note missing cash values on the final report** (§7)
- **Truncate** NT/PQ labels to fit `UWDESCR` C(20) (§8)
- **Unlisted plans:** keep current mapping; only change spreadsheet/Eric items (§9)
- **Drop `NS`** from QuikUwpo (§10)
- **UAT anchors:** `Issue_118_UAT_Example_Policies.md` (§11)
- **Blank UW on Standard-only forms (SAL ML, SAL OL, …):** treat as Standard → code `00` / descr Standard (§12 + §4)
