# CFIC Issue #01 — Open Business Questions

**Status:** OPEN — QLAdmin emit held; Wave 1 extract pilot may proceed after Risk Conditional Go  
**Program:** Citizens / CFIC Rates  
**Planning reference:** `CFIC_Issue_01_Planning_Report.md`

---

## OBQ-1 — Factor basis (BLOCKER for emit)

**Question:** Are all green-sheet numeric columns expressed **per $1,000** of current inforce (sheet shows `CURRENT INFORCE = 1,000.00`)?

**Why it matters:** QLAdmin rate factors assume a unit basis. Wrong basis scales every CV, reserve, and paid-up value.

**Need decision:**
1. Per $1,000 face (default assumption)
2. Per $1 unit
3. Absolute dollars (unlikely)
4. Varies by column

---

## OBQ-2 — Rate-key assumptions (BLOCKER for emit)

**Question:** What are the Citizens values for `QuikPlCv` and `QuikPlTv` assumption fields per plan?

| Key table | Required fields |
|-----------|-----------------|
| `QuikPlCv` | `MORT`, `ETIMORT`, `NFOINT`, `INTMETHCV` |
| `QuikPlTv` | `MORT`, `RSVINT`, `RSVMETH`, `INTMETHTV`, `STOREMEANS`, `CALCMIDS` |

**Why it matters:** QLAdmin will not load factor tables without companion key rows. These values are **not on the green sheets**.

**Need:** Actuarial / product spreadsheet or Access walkthrough answers.

---

## OBQ-3 — Extended term insurance mapping

**Question:** How should **EXT INS - YRS** and **EXT INS - DAYS** load into QLAdmin?

**Options:**
1. `QuikNff` non-forfeiture factor table
2. Plan-level NFO option setup only (no factor table)
3. Combined years+days encoded into a single factor
4. Staging only for initial release

---

## OBQ-4 — Mean reserve handling

**Question:** Should **MEAN RESERVE** be loaded to a QLAdmin table, or does QLAdmin derive mean reserve from terminal reserve using `STOREMEANS` / `CALCMIDS` on `QuikPlTv`?

**Default recommendation:** Stage for audit; do not emit until confirmed.

---

## OBQ-5 — Expiry-age PDF naming (802M)

**Question:** For `802M/Exiry Age {n}.pdf` files, what does the filename age represent, and how does it map to QLAdmin `AGE` (issue age)?

**Need:** Business rule or actuarial convention document (802M includes `Directions.pdf`).

---

## OBQ-6 — Consolidated mega-sheets

**Question:** For single-PDF products (`ALP2/Cash Value Sheets.pdf`, `GDB`, `P8FN`, etc.), is automated age-band splitting acceptable, or must actuarial review each split?

**Impact:** 29 consolidated PDFs — highest OCR complexity.

---

## OBQ-7 — R69G crosswalk gap

**Question:** `R69G` appears in `MultipleCashValueFiles.zip` but not in `Citizens_Plan_Crosswak.xlsx`. Is it active? What is the QLPlan code?

---

## OBQ-8 — Source of truth when Access differs

**Question:** When Access illustration columns (`CashValueIn10/20/At65`) disagree with green-sheet OCR values, which is authoritative?

**Planning assumption:** Green sheets are authoritative for full-duration grids; Access is a **parity checkpoint** only. Confirm with business.

---

## OBQ-9 — PL7 vs PL8 illustration alignment

**Question:** PermaLife 7 and 8 premiums are identical but illustration values differ. Which Access table should P7* green sheets validate against?

**Planning default:** Match plan code generation (P7* → PL7; P8* → PL8).

---

## Coding / emit gates

| Activity | Blocked by |
|----------|------------|
| Wave 1 P7MN extract pilot | None (after Risk Conditional Go) |
| Wave 3 QLAdmin emit | OBQ-1, OBQ-2 |
| ETI / NFO emit | OBQ-3 |
| Mean reserve emit | OBQ-4 |
| 802M emit | OBQ-5 |
| ALP/GDB emit | OBQ-6 |
| R69G emit | OBQ-7 |

Warren `QLA_Migration/` is not modified for any CFIC issue.
