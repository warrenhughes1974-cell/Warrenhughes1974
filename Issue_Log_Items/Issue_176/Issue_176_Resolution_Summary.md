# Issue 176 — Resolution Summary

**Issue:** 176 — ISWL Projected CV Blank
**Closed:** 2026-09-28
**Code change:** None. The Preferred cash value rate was already in the rate file from Issue 172. The CSO test region was still on the September 22 cash value file, which did not have that Preferred key.

## What Warren confirmed

Policy Display for `9010715467C`, plan 1659C2, male, Preferred, 50 units:

| Date | Cash value |
|---|---:|
| 05/14/2026 | 38,050.00 |
| 10/14/2026 | 38,320.83 |
| 05/14/2027 | 38,700.00 |

$38,050 is 761.00 per unit times 50. $38,700 is 774.00 per unit times 50. Those are the gross table cash values. The net fund after the surrender charge remains 9,757.73 and is not what this screen calculates.

## Smoke

`python tools/validators/validate_issue176_preferred_cv.py`

Fails if the 1659C2 male Preferred age-46 cash value row or plan key is missing from Output, or if this policy is no longer Preferred on that plan.
