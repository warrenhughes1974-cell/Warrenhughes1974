# Issue #56 — Client rate-file evidence (960 PO PUA CV)

**Received:** 2026-07-14  
**Source:** Client screenshot of LifePRO attained-age rate file  
**Saved as:** `evidence/960_PO_PUA_CV_rate_file_screenshot.png`

---

## What the screenshot shows

Header (highlighted):

`960 PO PUA ,CV ,F ,1 ,0 , 1,N , … ,D ,`

Then male block:

`960 PO PUA ,CV ,M ,1 ,0 , 1,N , … ,D ,`

Packed rate values in the blob (examples): `11296`, `11140`, `11382`, … ending near `96618`.

---

## Match to repo extracts (exact)

| Screenshot packed | PAAGERAT `VALUE_INFO` (F CV) | PAAGE raw blob |
|-------------------|------------------------------|----------------|
| 11296 | **112.9600000** (SEQ 1) | same packed field in `PAAGE_…20260630.csv` |
| 11140 | **111.4000000** (SEQ 2) | same |
| 11382 | **113.8200000** (SEQ 3) | same |
| … | … | … |
| 96618 | **966.1800000** (SEQ 100) | same |

**Conclusion:** Client’s rate-file screenshot is the same LifePRO attained-age CV table we already have as:

- `QLA_Migration/Source/PAAGE_AttainedAge_Rates_Extract_20260630.csv` (packed row)
- `QLA_Migration/Source/PAAGERAT_AttainedAge_Rates_Extract_20260630.csv` (unpacked 100 F + 100 M CV factors)

Scale: factors are **per $1,000** of PUA face (e.g. age~83 M ≈ 829.28 → × 5.94278 units ≈ **$4,928** CV for sample policy — below face $5,942.78).

---

## Impact on open questions

| Question | Status after this evidence |
|----------|----------------------------|
| Are PUA CVs from attained-age `960 PO PUA` CV rates? | **Answered — Yes** |
| Do we have the rate content in Source/? | **Answered — Yes** (already present) |
| Correct LifePRO **policy** PUA CV $ for `010310404C`? | **Still needed** |
| Catalog plan `1POPUA` vs synthetic `1960PA`? | **Still needed** |

---

## Does this complete Development?

**No — not by itself.** It **confirms the rate source** for Option B emit (PAAGERAT → QuikCvs under `1POPUA`). Coding still waits on:

1. Client: correct PUA cash-value dollar on the policy (acceptance target)  
2. Client/New Era: OK to use catalog plan codes instead of `1960PA`  
3. Explicit Development approval → Composer 2.5  

Risk recommendation unchanged: **Conditional Go — Option B**.
