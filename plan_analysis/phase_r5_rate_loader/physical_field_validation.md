# R5 — Factor Field Physical Validation (Overflow Reframed)

Resolves **Business Clarification #1**: the two "overflow" plans are **NOT blocked**. No scaling,
division, truncation, quarantine, or special-case logic was applied or invented.

## Questions answered

**1. True storage capacity of the target field?**
`Character(7)` — a literal **7-character text string**. Capacity is "any decimal string that
fits 7 characters" (including a literal `.` and an optional leading `-`). Integer magnitude up
to **9,999,999**; with one decimal up to `99999.9`; with two decimals up to `9999.99`.
**CONFIRMED** (DBF field descriptor: type `C`, length `7`, decimals `0`, all 6 factor tables).

**2. Is the field Numeric / Character / Implied-decimal / Other?**
**Character.** Not numeric and not an implied-decimal/packed field — the decimal point is a
literal character stored in the text. **CONFIRMED** from the descriptor (`decimals=0`).

**3. Can QLAdmin store and retrieve values above 9999.99?**
**Yes, when the textual representation fits 7 characters.** e.g. `26418.10 → "26418.1"`,
`28134.00 → "28134.0"`. Whether QLAdmin's runtime parses such 1-decimal text back to the
correct number is **LIKELY** (populated cells are always numeric text and the field is plain
text), but the runtime parse has not been exercised in a live QLAdmin instance → **UNKNOWN until
a live read-back test**.

**4. Are the observed populated examples representative of actual limits?**
**No.** The populated reference DBFs happen to use a 2-decimal convention (100% of ~7.3M cells),
which made `9999.99` *look* like a ceiling. That is a **convention, not a physical limit**. The
physical limit is the 7-character width. **CONFIRMED** the 2-decimal pattern is convention only.

## Physical representability of the 1,633 flagged values (measured)

| Outcome | Count | Meaning |
|---|---|---|
| Cannot fit 7 chars even as integer | **0** | no true overflow exists |
| Fit losslessly at 1 decimal (trailing zero dropped) | **1,373** | e.g. `28134.00→"28134.0"`, `26418.10→"26418.1"` |
| Fit at 1 decimal with sub-cent rounding | **260** | e.g. `10649.85→"10649.9"` (magnitude preserved, ≤0.005 precision) |

All values from `2665ST` (DB) and `A96DAR` (CV) are **storable**. The only effect is that 260
`A96DAR` cash values lose the 2nd decimal place to fit the 7-char width; **magnitude is never
changed**. The loader's `format_factor()` does this adaptively and flags each reduced cell as a
**WARNING (`V10 PRECISION_REDUCED`)**, never a blocker, never a rescale.

## Disposition
- `2665ST` and `A96DAR` remain **valid candidate plans for loading**.
- Status changed from `NEEDS PHYSICAL FIELD VALIDATION` → **RESOLVED: storable as CHAR(7) text**.
- Open follow-up (non-blocking): a live QLAdmin read-back test to confirm 1-decimal text parses
  as expected for >9999.99 values, and a business note that 260 CV cells carry 1-decimal precision.
