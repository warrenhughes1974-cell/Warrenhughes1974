# Issue #58 — Intake Summary

**Issue:** #58 — Premium Mode Amounts Incorrect  
**Client log ID:** 58 (Active)  
**Date:** 2026-07-13  
**Framework stage:** Intake complete (G0)  
**Status recommendation:** Planning  
**Owner:** Conversion (Warren) · **Business status:** No-Go (Eric)  
**Priority:** High (Names-tab Modal Premium **amounts** wrong when policy fee present)

---

## 1. Client / business symptom (verbatim + normalized)

**Verbatim (issue log):**

> Premium mode amounts do not match factors on Plan level. Policy 010367131C amounts should be $60, $31.20, $15.90, and $5.40 (Factors 0.52, 0.265, and 0.09) and amounts on Name Tab are $60, $31.20, $13.13, and $4.46.

**Normalized:**

QLAdmin Policy Display → **Names** tab → **Modal Premiums** grid shows correct **annual** and **current-mode** premium, but **hypothetical** quarterly and monthly/draft amounts are low when the policy carries a non-zero annual policy fee.

| Mode | Eric expected | Names tab (actual) | Delta |
|------|---------------|-------------------|-------|
| Annual | $60.00 | $60.00 | OK |
| Semi-annual | $31.20 | $31.20 | OK |
| Quarterly | $15.90 | $13.13 | **−$2.77** |
| Monthly / Draft | $5.40 | $4.46 | **−$0.94** |

Plan **`17085M`** (670 GL85-M) factors on `quikplan` / `quikmstr`: Semi **52%**, Qtr **26.5%**, Mth draft **9%**, Mth bill **8.3333%**.

---

## 2. Example policies / evidence

| Artifact | Path / note |
|----------|-------------|
| Trace policy | **`010367131C`** — Mode 6 (semi), `MMODEPREM` **31.20**, plan **`17085M`** |
| LifePRO PPOLC | `ANNUAL_PREMIUM=60.00`, `MODE_PREMIUM=31.20`, `POLICY_FEE=10.44` |
| LifePRO PPBEN (seq 1) | `ANN_PREM_PER_UNIT=9.12`, `UNITS=5.434`, `POLICY_FEE=10.44` |
| Conversion quikridr (phase 1) | `MPREM=9.12`, `MUNIT=5.434`, `MANNLFEE=10.44`; **MSEMIFEE/MQTRLFEE/MMTHDFEE/MMTHBFEE blank** |
| Conversion quikmstr | `MSEMI=52.0000`, `MQTRL=26.5000`, `MMTHD=9.0000`, `MMTHB=8.3333` (Issue #36 — **factors OK**) |

**Reconciliation math (010367131C):**

```
Base premium (MPREM × MUNIT)     = 9.12 × 5.434 = $49.56
Annual policy fee (MANNLFEE)     = $10.44
Total annual                     = $60.00  ✓

QLAdmin Names tab (observed):
  Qtr  = $49.56 × 26.5%           = $13.13  (fee omitted)
  Mth  = $49.56 × 9%              = $4.46   (fee omitted)

Eric expected (fee modalized):
  Qtr  = $60.00 × 26.5%           = $15.90
  Mth  = $60.00 × 9%              = $5.40

Fee component alone:
  Qtr fee = $10.44 × 26.5%        = $2.77   (= 15.90 − 13.13)
  Mth fee = $10.44 × 9%           = $0.94   (= 5.40 − 4.46)
```

Semi-annual **$31.20** matches because `MMODEPREM` is loaded from LifePRO `MODE_PREMIUM` (Issue #26), which already includes the modalized fee. Other modes are **computed** in QLAdmin from base premium × factor **plus** modal fee slots on `quikridr`.

---

## 3. Suspected domain

| Domain | Assessment |
|--------|------------|
| Rider fees (`quikridr.MSEMIFEE` / `MQTRLFEE` / `MMTHDFEE` / `MMTHBFEE`) | **Primary** — fleet-wide blank (0 / 4,457) while `MANNLFEE` populated |
| Policy master factors (`quikmstr.MSEMI` …) | **Not broken** — Issue #36 closed; factors present |
| Plan setup (`quikplan` factors) | **Not broken** — Issue #21J closed |
| `MMODEPREM` / `MPREM` | **Not broken** — Issue #26; do not overwrite |

---

## 4. In scope / out of scope (first pass)

**In scope**

- Populate `quikridr.MSEMIFEE`, `MQTRLFEE`, `MMTHDFEE`, `MMTHBFEE` on **base-coverage (MPHASE 1)** rows where `MANNLFEE > 0`, using plan/policy modal factors from `quikmstr` (post–Issue #36) or `quikplan`.
- Formula (proposed): `modal_fee = MANNLFEE × (factor / 100)` per mode; round to QLAdmin NUMERIC 8.4.
- Preserve Issue #21C `MANNLFEE` behavior; preserve Issue #36 PAC GL85 overrides for factor source.
- Fleet validator: Eric trace + spot-check policies with `MANNLFEE > 0`.

**Out of scope (unless Planning proves otherwise)**

- Changing `MMODEPREM`, `MPREM`, or plan-level factors.
- Rider phases > 1 (fee typically on base row only per #21C).
- Recalculating Coverage-tab billed premium (already correct via `MODE_PREMIUM`).
- LifePRO extract columns for modal fees (none found — derive from `POLICY_FEE` + factors).

---

## 5. Related issues

| Issue | Relationship |
|-------|----------------|
| **#21C** | Parent partial fix — `POLICY_FEE` → `MANNLFEE` only; modal fee slots left blank |
| **#21J** | Plan-level modal **factors** on `quikplan` |
| **#36** | Policy-level modal **factors** on `quikmstr` — closed; factors OK but amounts still wrong without modal fees |
| **#26** | `MPREM` / `MMODEPREM` — must not regress |

**Regression note:** Issue #36 closed with “Names-tab Modal Premiums work” based on **factor population** validation, not **amount** reconciliation on fee-bearing policies.

---

## 6. Fleet impact (intake measurement)

| Check | Result |
|-------|--------|
| Base `quikridr` rows (MPHASE 1) | 5,083 |
| `MANNLFEE` populated | **4,457** |
| `MSEMIFEE` / `MQTRLFEE` / `MMTHDFEE` / `MMTHBFEE` populated | **0 / 0 / 0 / 0** |

Any policy with a non-zero annual policy fee and blank modal fees is a candidate for the Eric symptom on non-current modes.

---

## 7. Immediate blockers visible at intake

| Blocker? | Item | Notes |
|----------|------|-------|
| No | Symptom / trace policy | `010367131C` with full math proof |
| No | Factor source | Issue #36 + #21J already populate factors |
| **Open for Planning** | QLAdmin fee formula confirmation | Strong evidence: base×factor + modal fee; confirm NUMERIC scale and rounding |
| **Open for Planning** | PAC GL85 special modes | Use overridden `MSEMI`/`MQTRL` (25 / 50) when computing modal fees |
| Soft | Post-emit ordering | Modal fees must run **after** quikmstr factor enrichment (#36) |

**No hard client-data blocker at Intake.** Proceed to Planning Agent.

---

## 8. Artifact inventory

| Provided | Missing |
|----------|---------|
| Issue log row (#58) | Names-tab screenshot for `010367131C` |
| Trace policy + LifePRO extracts | Client-signed confirmation of derive-vs-extract for modal fees |
| Math proof from conversion output | — |

---

## 9. Severity / owner

| Attribute | Value |
|-----------|-------|
| Severity | **High** — 4,457 policies; CS Names-tab quotes wrong on 3 of 4 modes when fee present |
| Blast radius (expected) | `quikridr` four modal fee columns on base rows only |
| Owner | **Conversion** |
| Client role | UAT on Names tab after Development |

---

## 10. Gate G0 checklist

- [x] Issue folder created: `Issue_Log_Items/Issue_58/`
- [x] Intake summary written
- [x] Example policies listed (`010367131C`)
- [x] Owner and priority assigned
- [x] No code or rulebook changes made

**G0 status:** **PASS** — advance to Planning Agent.
