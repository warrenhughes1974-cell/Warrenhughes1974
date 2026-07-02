# Issue #21K — Release Note (Closure)

**Issue:** #21K — PUA Amount Precision  
**Status:** **CLOSED**  
**Engine version:** v57.39  
**Closure date:** 2026-06-28  
**Type:** Clarification — no converter change

---

## Summary

Issue #21K is **closed**. The conversion correctly preserves five-decimal PUA unit values. A visible whole-dollar difference on the QLAdmin **Coverage** tab is **display-only rounding** and does **not** affect stored units, death benefit calculation, or payment.

---

## What was reported

Policy **`010448806C`** PUA:

| Source | Amount |
|--------|-------:|
| LifePRO face | **$5,752.96** |
| QLAdmin Coverage tab (Amount Ins) | **$5,753.00** |

---

## What was confirmed

| Layer | Result |
|-------|--------|
| LifePRO source | Units **5.75296**, VPU **1000.00** |
| v57.39 `quikridr.csv` | `MUNIT = 5.75296`, `MVPU = 1000.00` |
| DBF storage | Five-decimal field precision (**N(10,5)**) in place |
| Death benefit / payment | Uses **five-decimal MUNIT** — pays **correctly** |
| Coverage screen | **Whole-dollar display rounding only** |

---

## What did NOT change at closure

- **No** `app.py` or converter changes
- **No** rulebook or crosswalk changes
- **No** additional DBF schema work beyond completed N(10,5) update
- **No** regression batch required

---

## Client guidance

When reviewing policies on the **Coverage Information** screen:

- **Amount Ins** may show a whole-dollar rounded value (e.g. **$5,753.00**).
- **Authoritative unit precision** is in stored `MUNIT` (five decimals).
- **Benefit payment** reflects full precision — not the rounded display value.

Example **`010448806C`**: display **$5,753.00**; stored units **5.75296**; true face **$5,752.96**; payment engine correct.

---

## Validators (unchanged)

| Validator | v57.39 result |
|-----------|---------------|
| `validate_issue21k_munit.py` | PASS |
| `validate_issue21k_fleet.py` | PASS |

---

## Related release documentation

Platform release note updated: `Release_Notes/v57.39_Release_Notes.md` — Issue #21K display-only clarification.

---

**Issue #21K:** **CLOSED — conversion correct; QLAdmin Coverage display rounding accepted**
