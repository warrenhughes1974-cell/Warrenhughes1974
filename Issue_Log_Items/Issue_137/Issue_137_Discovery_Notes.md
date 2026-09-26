# Issue #137 — Discovery Notes (Search & Discuss)

**Issue:** #137 — Names-tab Modalized Annual Premium  
**Date:** 2026-08-05  
**Framework stage:** Stage 0 Discovery (G-D)  
**Reporter / context:** Warren / Eric LifePRO Policy Values screen vs QLAdmin Names → Modal Premiums  
**Code:** None (Discovery only)

---

## Client ask (normalized)

LifePRO Policy Values shows a **modalized annual** premium (mode premium ÷ that mode’s factor), not calendar `MODE × payments/year`. QLAdmin Names-tab **Annl** is higher (ISWL example ~506 vs LifePRO **436**). Monthly billed amount already matches. Policy fee stays separate.

Gold: **`9010722550C`** (plan `1659C2`, monthly Direct) — LifePRO Annually **436**, Monthly **40.11**, fee **25** separate.

---

## Verdict

This is real, and it is **not** a missing modal-factor problem (#21J / #36 already load factors).

QLAdmin Names-tab dollars are computed at runtime as:

```text
(MPREM × MUNIT × factor/100) + modal_fee
```

(documented in Issue #58). For the gold policy that produces **Annl = 506.32**, which matches the wrong UAT number exactly:

| Component | Value |
|-----------|------:|
| `MPREM` × `MUNIT` | 9.6264 × 50 = **481.32** |
| `MANNLFEE` | **25.00** |
| Names Annl total | **506.32** |
| LifePRO modalized annual (ex fee) | **~436.00** = 40.11 ÷ (9.1999/100) |

So the Annl cell is driven by **`quikridr.MPREM × MUNIT`**, not by reverse-engineering from `MMODEPREM` + factors.

**Must change (direction):** The annual premium base behind Names-tab Annl (`MPREM × MUNIT`, typically via the blank-`ANN_PREM_PER_UNIT` fallback) so it equals **mode premium ÷ current mode factor**, mode-aware — not `MODE × 12/4/2`.

**Must not change:**

- `quikmstr.MMODEPREM` (Issue #26 / billed mode premium)
- Plan/policy modal **factors** (#21J / #36) except as the divisor source
- Fee fields (#21C / #58) — fee stays outside the 436
- Inventing dollars into a new parallel premium engine

---

## Source findings

| Source | Role |
|--------|------|
| `PPOLC` `MODE_PREMIUM` | Billed mode amount → `MMODEPREM` (correct; leave alone) |
| `PPOLC` `ANNUAL_PREMIUM` | Calendar annual (gold = 481.32) — **ignore for Names Annl** |
| `PPOLC` `BILLING_MODE` / `BILLING_FORM` | Mode + Direct vs PAC |
| Client workbook / `Modal_Premium_Factors_By_Plan.csv` | SEMI/QTRL/MTHD/MTHB percents |
| `quikmstr` MSEMI/MQTRL/MMTHD/MMTHB | Policy factors already present |

### Mode codes on this book (confirmed Output crosstab)

| LifePRO `BILLING_MODE` / `MMODE` | Meaning | Divisor for modalized annual |
|----------------------------------|---------|------------------------------|
| `01` | Monthly | `MMTHD` if Direct (`MBILLFRM=1`); `MMTHB` if PAC (`MBILLFRM=2`) |
| `03` | Quarterly | `MQTRL` |
| `06` | Semiannual | `MSEMI` |
| `12` | Annual | none — `MMODEPREM` is already annual |

### Worked examples

**Monthly ISWL — `9010722550C`**

```text
modalized_annual = 40.11 ÷ (9.1999/100) ≈ 436.00
```

**Semiannual traditional — `9010367131C`** (Issue #58 gold)

```text
modalized_annual = 31.20 ÷ (52/100) = 60.00
```

Here `MPREM × MUNIT` is already ~49.56 (ex-fee), and Annl with fee ~60 — Names-tab already agrees with modalized math. Pattern problem is concentrated where blank-ANN fallback used **crude** annualization.

**Semiannual ISWL — `9010732078C`**

```text
MMODEPREM 59.19 ÷ 0.525 ≈ 112.74 modalized
MPREM × MUNIT = 118.38  (calendar-style; too high)
```

---

## Current conversion path (smoking gun)

Issue **#88** blank-ANN fallback in `app.py` / `QLA_Migration/app.py`:

```text
ann_factor = {12: 1.0, 6: 2.0, 3: 4.0, 1: 12.0}   # payments per year
MPREM = (MODE_PREMIUM × ann_factor) / NUMBER_OF_UNITS
```

For monthly: `40.11 × 12 / 50 = 9.6264` → Names Annl premium **481.32**, not **436**.

That crude ×12 (etc.) is what LifePRO’s statement **does not** use for “Annually”; LifePRO uses modal factors.

---

## Suspected QLAdmin target

| UI | QLAdmin Policy Display → **Names** → **Modal Premiums** (Annl / Semi / Qtrly / Mthly / Draft) |
| Target fields | `quikridr.MPREM` (and thus `MPREM × MUNIT` annual base); factors already on `quikmstr`; fees on `quikridr.M*FEE` |
| Not the target | `quikmstr.MMODEPREM`; QuikVal modal premiums (#128 / #93) — separate domain |

---

## Related issues

| Issue | Relationship |
|-------|----------------|
| **#21J** | Plan factors — preserve |
| **#36** | Policy factors on `quikmstr` — preserve; use as divisors |
| **#58** | Modal fees; documents Names formula `(MPREM×MUNIT×f)+fee` |
| **#26** | Populated `ANN_PREM_PER_UNIT` → `MPREM` — preserve; do not regress |
| **#88** | Blank-ANN fallback annualizes with ×12/4/2 — **likely change point** |
| **#128 / #93** | QuikVal modal premiums — **out of scope** unless Intake explicitly merges |

---

## Proposed work list (Planning will refine — no code)

1. Confirm with Help / UAT that Names Annl is always `(MPREM×MUNIT) + MANNLFEE` (premium + fee), and LifePRO “436” is premium-only.
2. Replace crude `ann_factor` payments-per-year with **mode + bill-form factor** reverse-engineer for the blank-ANN `MPREM` path (or equivalent surgical emit), mode-aware.
3. Keep `MMODEPREM` untouched; keep fee derivation (#58) on annual fee × factors.
4. Validator: gold `9010722550C` → `MPREM×MUNIT ≈ 436`; mode samples for 03/06/12 and PAC monthly; #26/#88/#58 non-regression.
5. UAT Names tab + watch QuikVal Prem/Unit impact (same `MPREM` field).

---

## Open questions / defaults locked at Discovery

| ID | Question | Discovery default |
|----|----------|-------------------|
| DQ-1 | Does LifePRO “Annually 436” exclude the $25 fee? | **Yes** — fee separate; Names may still show Annl = 436+25 if UI adds `MANNLFEE` |
| DQ-2 | Scope: blank-ANN fallback only, all ISWL, or fleet-wide where crude ≠ modal? | **Fleet blank-ANN path** preferred so one rule; quantify at Intake |
| DQ-3 | Changing `MPREM` will move Coverage Prem/Unit and QuikVal — accept for modalized truth? | **Flag for Risk / client UAT**; #88 intentionally used ×12 for valuation |
| DQ-4 | Client issue log ID if not #137? | Using **#137** as next free internal ID until sheet says otherwise |
| DQ-5 | Distinct from #128 QuikVal Modal Premiums? | **Yes** — Names-tab / `MPREM` base, not QuikVal |

---

## Stop

Discovery complete 2026-08-05. User said **Proceed to Intake** — Pre-Dev chain continued (Intake → Planning → DG → Risk).
