# Issue Log #26 — Premium Per Unit Mismatch (Research Report)

**Status:** Research complete — **No-Go pending client field confirmation and surgical mapping fix**  
**Date:** 2026-06-26  
**Script:** `QLA_Migration/_research_issue26_ppu.py` (read-only)  
**Scope:** Planning / investigation only — **no code changes made**

---

## 1. Executive Finding

The reported “Premium Per Unit” mismatches are **not random conversion corruption**. Traced values prove:

1. **LifePRO “Premium Per Unit”** on the client screenshots corresponds to **`ANN_PREM_PER_UNIT`** in `PPBEN_PolicyBenefit_Extract` (base benefit, `BENEFIT_SEQ = 1`).

2. **Reported QLAdmin values** (`18.10`, `174.40`, `31.20`) **exactly match** emitted **`MPREM`** (Modal Premium) in **`quikridr.csv` phase 1**, which is a **direct pass-through** of LifePRO **`MODE_PREMium`**.

3. **`ANN_PREM_PER_UNIT` is not mapped** to any QLAdmin output field in the current rulebook.

4. **`MVPU`** in `quikridr` receives **`VALUE_PER_UNIT`** ($1,000 face amount per unit for these policies), **not** the premium rate. This is correct for “value per unit” semantics but **does not carry** LifePRO’s annual premium-per-unit rate.

**Conclusion:** The issue is a **source-field / target-field semantic mismatch** (and likely a **client UI comparison mismatch**), not unit scaling, crosswalk identity, or rider phase selection. The conversion emits what the rulebook specifies; the rulebook does **not** emit LifePRO’s premium rate field to the QLAdmin field the client is comparing.

**Severity:** Treat as **No-Go** until the business confirms which QLAdmin screen/field is authoritative for “Premium Per Unit,” then apply a **surgical rulebook mapping** only.

---

## 2. Root-Cause Hypothesis

| Layer | Assessment |
|-------|------------|
| Source extraction | **Pass** — `ANN_PREM_PER_UNIT`, `MODE_PREMIUM`, `VALUE_PER_UNIT`, `NUMBER_OF_UNITS` present in PPBEN |
| Crosswalk / policy ID | **Pass** — policies crosswalk correctly |
| Rider / phase selection | **Pass** — phase 1 base coverage (`BENEFIT_SEQ=1`) traced; phase 2 PUA riders have `.00` MPREM |
| Unit scaling | **Not the cause** — units emit correctly (`MUNIT` = `NUMBER_OF_UNITS`) |
| Modal / mode conversion | **Contributing factor** — `MPREM` reflects **billing-mode modal premium** (may include policy-level fee allocation), not annual rate per unit |
| Rulebook mapping | **Primary cause** — `ANN_PREM_PER_UNIT` unmapped; client compares it to `MPREM` |
| QLAdmin display | **Likely** — reported values match `MPREM`, not `MVPU` ($1,000) |

**Primary hypothesis:** Client compares LifePRO **`ANN_PREM_PER_UNIT`** (annual premium **rate** per unit) to QLAdmin **`MPREM`** (coverage **modal premium** total for the billing mode). These are **different LifePRO fields** by design.

**Secondary hypothesis:** QLAdmin screen label “Premium Per Unit” may bind to **`MPREM`** or policy-level modal premium rather than a per-unit **rate** field — requires client confirmation against QLAdmin Help / Coverage Master screen field list.

---

## 3. Exact Source Field(s)

| LifePRO extract | Field | Role |
|-----------------|-------|------|
| **PPBEN** (`PPBEN_PolicyBenefit_Extract_20260530.csv`) | **`ANN_PREM_PER_UNIT`** | LifePRO “Premium Per Unit” — **matches all three reported LifePRO values exactly** |
| PPBEN | `MODE_PREMIUM` | Modal premium for coverage phase → emitted as `MPREM` |
| PPBEN | `VALUE_PER_UNIT` | Face / value per unit ($1,000 typical) → emitted as `MVPU` |
| PPBEN | `NUMBER_OF_UNITS` | Units → emitted as `MUNIT` |
| PPBEN | `BENEFIT_FEE` | Policy/benefit fee — explains `MODE_PREMIUM ≈ ANN_PPU × units + fee` on some policies |
| PPOLC | `MODE_PREMIUM` | Policy-level modal premium → `quikmstr.MMODEPREM` |
| PPOLC | `BILLING_MODE` | Billing frequency → `quikmstr.MMODE` |
| PPOLC | `ANNUAL_PREMIUM` | Annual premium total (policy level) |

---

## 4. Exact Output Field(s)

| QLAdmin table | Field | Current source (rulebook) | Emitted for trace policies |
|---------------|-------|---------------------------|----------------------------|
| **quikridr** | **`MPREM`** | `MODE_PREMIUM` | **18.10 / 174.40 / 31.20** — **matches client QLAdmin values** |
| **quikridr** | **`MVPU`** | `VALUE_PER_UNIT` | **1000.00** (face per unit — **not** premium rate) |
| **quikridr** | `MUNIT` | `NUMBER_OF_UNITS` | 15 / 15 / 5.434 |
| **quikridr** | `MSAVEVPU` | *(unmapped — blank)* | — |
| **quikmstr** | `MMODEPREM` | `MODE_PREMIUM` | Same modal totals as `MPREM` phase 1 |
| **quikmstr** | `MMODE` | `BILLING_MODE` | 01 / 12 / 06 |

**Rulebook reference:** `QLA_Migration/Configs/Sync_Rulebook_quikridr.csv`

```
NUMBER_OF_UNITS  → MUNIT
VALUE_PER_UNIT   → MVPU
MODE_PREMIUM     → MPREM
(ANN_PREM_PER_UNIT — not present)
```

**QLAdmin table for mismatch:** **`quikridr`** (Coverage / Rider Master), phase **1** base coverage row.

---

## 5. Policy-by-Policy Trace

| LifePRO | QLAdmin MPOLICY | Plan (phase 1) | Status | Mode (quikmstr) | Units | LifePRO ANN_PPU | LifePRO MODE_PREM | Emitted MVPU | Emitted MPREM | Client QLAdmin | MPREM match? |
|---------|-----------------|----------------|--------|-----------------|-------|-----------------|-------------------|--------------|---------------|----------------|--------------|
| 9010310404 | 010310404C | 1960PO | 22 | 01 (annual) | 15.00000 | **13.20** | 18.10 | 1000.00 | **18.10** | **18.10** | Yes |
| 9010331768 | 010331768C | 1960PO | 22 | 12 | 15.00000 | **10.96** | 174.40 | 1000.00 | **174.40** | **174.40** | Yes |
| 9010367131 | 010367131C | 17085M | 22 | 06 (semi) | 5.43400 | **9.12** | 31.20 | 1000.00 | **31.20** | **31.20** | Yes |

**Coverage structure (all three):** 2 `quikridr` phases — phase 1 base (`1960PO` / `17085M`), phase 2 PUA rider (`1960PA` / `1708PA`) with `MPREM = .00`.

**LifePRO plan codes (source):** `960 PO`, `670 GL85-M` (crosswalked to QLAdmin MPLAN above).

---

## 6. Calculation Comparison Table

| Policy | LifePRO expected (ANN_PPU) | QLAdmin reported | Emitted MPREM | Emitted MVPU | MPREM ÷ units | ANN_PPU × units + fee | ANN_PPU × units | PPOLC ANNUAL_PREM |
|--------|------------------------------|------------------|---------------|--------------|---------------|------------------------|-----------------|-------------------|
| 010310404C | 13.20 | 18.10 | 18.10 | 1000.00 | 1.21 | **208.00** | 198.00 | 208.00 |
| 010331768C | 10.96 | 174.40 | 174.40 | 1000.00 | 11.63 | **174.40** | 164.40 | 174.40 |
| 010367131C | 9.12 | 31.20 | 31.20 | 1000.00 | 5.74 | **60.00** | 49.56 | 60.00 |

**Observations:**

- **010331768C:** `MODE_PREMIUM` = `ANN_PPU × units + BENEFIT_FEE` exactly (174.40). Client compares **per-unit rate** (10.96) to **total modal premium** (174.40).
- **010310404C:** `MODE_PREMIUM` (18.10) ≠ `ANN_PPU` (13.20); ratio ≈ **1.371** (modal factor / billing-mode effect). Neither equals `MPREM/units` (1.21).
- **010367131C:** Semi-annual mode (`MMODE=06`); `MODE_PREMIUM` (31.20) reflects **semi-annual modal**, not annual rate (9.12).
- **None** of the reported QLAdmin values equal `MVPU` (1000.00) — client is **not** viewing face amount per unit.

---

## 7. Isolated or Systemic?

**Systemic** for the comparison pattern “LifePRO ANN_PPU vs QLAdmin MPREM”:

| Fleet metric (phase 1 base benefits, n=5,083) | Count | % |
|-----------------------------------------------|-------|---|
| `MPREM` == source `MODE_PREMIUM` | 4,954 | 97.5% |
| `MVPU` == source `VALUE_PER_UNIT` | 4,954 | 97.5% |
| `MVPU` == `ANN_PREM_PER_UNIT` | **0** | 0% |
| `ANN_PREM_PER_UNIT` ≠ `MPREM` | **4,453** | **87.6%** |

The conversion **correctly implements the current rulebook** for 97.5% of policies. The gap affects **any policy where annual premium rate per unit differs from modal premium** — the majority of the block.

**Not isolated** to 1960PO / 670 GL85-M — pattern is fleet-wide.

---

## 8. Recommended Development Agent Task (after client confirmation)

**Do not implement until client confirms target QLAdmin field.**

1. **Confirm with client** which QLAdmin Coverage Master field is labeled “Premium Per Unit” (screen + field name from QLAdmin Help).
2. If confirmed as a **rate** field (not modal total):
   - Add **`ANN_PREM_PER_UNIT` → target field** mapping in `Sync_Rulebook_quikridr.csv` only.
   - **Do not** overwrite `MVPU` with premium rate — `MVPU` carries **face/value per unit** ($1,000) and is distinct in LifePRO.
   - Candidate unmapped fields: **`MSAVEVPU`** (currently blank in rulebook) — **requires QLAdmin field definition confirmation**.
3. **Do not** change `MPREM` mapping — it correctly carries modal premium.
4. Add post-conversion validation: for phase 1 base rows, compare emitted rate field to `ANN_PREM_PER_UNIT` within tolerance.
5. Version bump + targeted re-test on three trace policies + regression sample of 10 policies where `ANN_PPU × units + fee = MODE_PREMIUM`.

**If client confirms they compared modal premium to premium rate:** reclassify as **documentation / UAT comparison error** — no code change.

---

## 9. Testing Agent Checklist

- [ ] Client documents QLAdmin screen + field name for “Premium Per Unit”
- [ ] Verify LifePRO source: `ANN_PREM_PER_UNIT` on PPBEN seq 1 matches client LifePRO screenshot
- [ ] Verify current emit: `quikridr.MPREM` = PPBEN `MODE_PREMIUM` for trace policies
- [ ] Verify `quikridr.MVPU` = PPBEN `VALUE_PER_UNIT` (typically 1000.00)
- [ ] After any fix: emitted rate field = `ANN_PREM_PER_UNIT` for phase 1 base coverage
- [ ] Confirm `MPREM` unchanged (modal premium still correct)
- [ ] Confirm phase 2 PUA riders unaffected
- [ ] Fleet sample: 20 policies spanning billing modes 01 / 06 / 12
- [ ] No change to `quikmstr.MMODEPREM`, units, plan codes, or crosswalk IDs

---

## 10. Classification Recommendation

| Category | Verdict |
|----------|---------|
| **Conversion logic** | **Yes** — rulebook omits `ANN_PREM_PER_UNIT`; maps `MODE_PREMIUM` → `MPREM` instead |
| **Source-data interpretation** | **Partial** — LifePRO distinguishes **rate** (`ANN_PREM_PER_UNIT`) vs **face** (`VALUE_PER_UNIT`) vs **modal total** (`MODE_PREMIUM`); rulebook only maps latter two categories |
| **QLAdmin display behavior** | **Possible** — client-reported values match `MPREM` exactly; client may be viewing modal premium while reading LifePRO per-unit rate |

---

## Appendix A — Where Mismatch Is **Not** Occurring

| Checked area | Result |
|--------------|--------|
| Source extraction | Fields present and populated |
| Crosswalk | Correct MPOLICY identity |
| Phase / benefit seq | Phase 1 base row correct |
| Unit scaling | `MUNIT` matches `NUMBER_OF_UNITS` |
| Rider mix-up | Phase 2 PUA has zero premium — not source of reported values |
| quikprmh | Premium **history** amounts — different issue domain (see 21F) |
| quikplan | Plan setup — not premium per unit on coverage |
| Rate table lookup | Not used for migrated MPREM/MVPU pass-through |

---

## Appendix B — Related Issues

- **Issue 21J (Modal Premium Factors):** Related — modal premium breakdown on `quikmstr` (MMODEPREM vs derived semiannual/quarterly). Distinct from per-unit **rate** on coverage.
- **Issue 21F (Premium History):** `quikprmh` truncation — unrelated to per-unit rate on rider.

---

## Appendix C — Reproduce

```powershell
python QLA_Migration\_research_issue26_ppu.py
```
