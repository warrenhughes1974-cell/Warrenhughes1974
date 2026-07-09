# Issue #21A — Intake Summary

**Issue:** NFO / Dividend Options  
**Parent bundle:** Issue #21  
**Framework stage:** Intake complete (G0)  
**Date:** 2026-07-04  
**Converter version analyzed:** v57.46  
**Status:** **INTAKE COMPLETE** → advance to Planning  
**Owner:** Conversion (Warren) · **Reporter:** Eric · **SME input:** New Era (2026-07-04)

---

## Client symptom (verbatim + normalized)

**Reported:** Non-Forfeiture Option (NFO) and Dividend Option from LifePRO show as **0** in QLAdmin instead of the client's real election.

**Example (Issue #21 packet):** Policy **010391895C** — LifePRO shows NFO = **ETI** and Dividend Option = **4 (Purchase of PUA)**; QLAdmin showed **NFO 0** and **DIV 0**.

**Normalized:** `quikmstr.MNFOPT` and `quikmstr.MDIVOPT` are not reliably populated from LifePRO benefit-type or policy-master elections. Text labels (ETI, RPU, APL ETI) and some LifePRO numeric codes fail translation or cache lookup, defaulting to **0** or mapping to the wrong QLAdmin code.

---

## SME guidance received (partial — 2026-07-04)

New Era confirmed LifePRO NFO code definitions and recommended mapping for **combined options where APL is attempted first**:

| LifePRO code | LifePRO meaning | SME recommendation for QLAdmin |
|:---:|:---|:---|
| **1** | APL/ETI — automatic premium loan attempted; if not possible, extended term insurance | **APL** (`MNFOPT = 1`) |
| **2** | APL/RPU — automatic premium loan attempted; if not possible, reduced paid-up insurance | **APL** (`MNFOPT = 1`) |

**Implied rule:** When LifePRO shows a combined value such as **"APL ETI"** (text) or code **1** / **2** (numeric), QLAdmin should display **APL (1)** because APL is the first action attempted.

**Not yet confirmed by client/SME:**

- LifePRO codes **3–6** — **no translation changes** (scope lock 2026-07-04)
- LifePRO codes **7–9** — not in QLAdmin crosswalk; remain **0**
- Full **Dividend Option** mapping (codes 0–9) — `Master_Value_Translation.csv` has `DV_1`–`DV_5` passthrough but cache resolution may still fail on some products
- Whether **`BF_NON_FORFEITURE`** filtered to **`Type_Code = BF`** is the authoritative column for ISWL / whole-life products (per Issue #21 analysis)

---

## QLAdmin target field reference

| QLAdmin field | Table | Meaning (Issue #21 analysis) |
|---|---|---|
| `MNFOPT` | quikmstr | NFO Option: **1** = APL, **2** = ETI, **3** = RPU |
| `MDIVOPT` | quikmstr | Dividend Option: **1–5** passthrough per `DV_*` translation |

LifePRO numeric codes **do not** match QLAdmin numeric codes directly (LifePRO 4 = ETI, QLAdmin 2 = ETI).

---

## Example policies (Issue #21 validation set)

| MPOLICY | LifePRO NFO (screenshot) | Current `MNFOPT` (v57.46 batch) | Current `MDIVOPT` | Gap |
|---|---|:---:|:---:|---|
| 010391895C | ETI | **0** | 4 | NFO wrong |
| 010448806C | RPU | **0** | 4 | NFO wrong |
| 010765930C | APL ETI | **0** | 0 | NFO wrong; DIV may also fail |
| 010713704C | ETI | **0** | 0 | Both wrong in UAT screenshots |
| 010818663C | (ETI family) | **0** | 0 | Both wrong in UAT screenshots |
| 010391876C | ETI | **2** | 4 | NFO may be correct (ETI) |
| 010718309C | APL ETI | **0** | 0 | NFO wrong |

These seven policies are **ISWL / whole-life** samples; they are **not** in the Issue #38 dividend-accumulation population (960 PO / GL85-heavy).

---

## Fleet output snapshot (v57.46 `quikmstr.csv`)

| Field | Value | Row count |
|---|---|---:|
| `MNFOPT = 0` | default / failed | 3,768 |
| `MNFOPT = 1` | APL | 438 |
| `MNFOPT = 2` | ETI | 470 |
| `MNFOPT = 3` | RPU | 407 |
| `MDIVOPT = 0` | default / failed | 4,272 |
| `MDIVOPT = 4` | Purchase PUA | 479 |

**Cross-check (Issue #38 population, PPBENTYP numeric `NON_FORFEITURE`):**

| Extract code | Policies | Current `MNFOPT` behavior | SME alignment |
|---|---:|---|---|
| **1** (APL/ETI) | 41 | 39 → **1**, 2 → **0** | Mostly correct; 2 cache misses |
| **2** (APL/RPU) | 2 | 2 → **2** (QLAdmin ETI) | **Wrong** — SME says should be **1** (APL) |
| **4** (LifePRO ETI) | 15 | 15 → **0** | **Wrong** — blocked by `NF_4→0` translation |
| **5** (LifePRO RPU) | 1 | 1 → **0** | **Wrong** — blocked by `NF_5→0` translation |

---

## Suspected root cause (planning-level — not validated in this intake)

Three layered defects, consistent with Issue #21 Final Analysis:

1. **Cache resolution** — `app.py` auto-loads `PPBENTYP` extract into `lifepro_extra['NON_FORFEITURE']` keyed by `POLICY_NUMBER` + `BENEFIT_SEQ=01`, but ISWL policies may store NFO on **`BF_NON_FORFEITURE`** under **`Type_Code = BF`**, not the column the cache reads.
2. **Value translation gaps** — Text labels `ETI`, `RPU`, `APL` map via `NF_ETI`, `NF_RPU`, `NF_APL`; combined **`APL ETI`** has **no** entry; numeric LifePRO codes **`NF_4→0`** and **`NF_5→0`** zero valid ETI/RPU elections.
3. **Numeric passthrough trap** — LifePRO code **2** passes through as QLAdmin **2** (ETI) without translation — contradicts SME rule (should be APL **1**).

**Engine touchpoints (read-only inventory):**

| Artifact | Role |
|---|---|
| `QLA_Migration/Configs/Sync_Rulebook_quikmstr.csv` | `NFO_OPT → MNFOPT` default 0; `MDIVOPT` default 0 + cache pull |
| `app.py` / `QLA_Migration/app.py` (~5327–5356) | PPBENTYP `NON_FORFEITURE` / `DIVIDEND` cache build |
| `app.py` (~5858–5875) | MNFOPT/MDIVOPT cache pull when rulebook value is 0 |
| `app.py` (~6012–6018) | `NF_` / `DV_` prefix translation + strict numeric shield |
| `Master_Value_Translation.csv` | `NF_APL→1`, `NF_ETI→2`, `NF_RPU→3`; **`NF_4→0`, `NF_5→0`** |
| `QLA_Migration/Mapping/Master_Value_Translation.csv` | Mirror of root translation file |

---

## Domain and scope (first pass)

| In scope | Out of scope (initial) |
|---|---|
| `quikmstr.MNFOPT` population from LifePRO NFO elections | Cash value / NFO interest (`quikplan.NFOINT`) — Issue #21D/E |
| `quikmstr.MDIVOPT` population from LifePRO dividend elections | Dividend **accumulation balance** — Issue #38 (closed) |
| Combined-option business rule (APL-first) for codes 1, 2, and text "APL ETI" | LifePRO billing NF_OPTION on PPCOM (separate from benefit-type NFO) |
| Value translation updates for LifePRO numeric code crosswalk | Non-forfeiture **processing** behavior in QLAdmin after load |

---

## Related issues

| Issue | Relationship |
|---|---|
| #21 (parent) | Original defect bundle; Items A + dividend half of screenshot evidence |
| #38 | Same PPBENTYP extract family; confirmed `NON_FORFEITURE` numeric codes 1/2/4/5 in source |
| #21D | Independent — plan NFO **interest** code, not policy NFO **option** |
| #25 / #26 | MPOLICY padding and MPREM — must not regress |

---

## Artifact inventory

| Provided | Status |
|---|---|
| Issue #21 screenshot packets (7 policies) | ✅ In `Issue_Log_Items/Issue_21/evidence/` |
| Issue #21 Final Analysis (Issue A confirmed) | ✅ |
| SME NFO code list + APL-first rule for codes 1 & 2 | ✅ 2026-07-04 |
| LifePRO NFO reference (Product Book excerpt) | ✅ Image provided in intake thread |
| `PPBENTYP_BenefitType_Extract` in Source/ | ❌ Not present locally (gitignored) — required for Planning validation |
| Approved mapping for LifePRO codes **1–2** | **Yes** — SME |
| LifePRO codes **3–6** | **No change** — scope lock |
| LifePRO codes **7–9** | **N/A** — QLAdmin **MNFOPT 0–3 only** |
| QLAdmin Help field definition for MNFOPT code set | ⚠️ Not yet cited — Planning should confirm against QLAdmin Help |

---

## Immediate blockers

| Blocker | Gate | Owner |
|---|---|---|
| PPBENTYP extract absent from local Source/ | Dependency Gate | Client / extract team |
| LifePRO codes 3–6 | **Not in scope** — crosswalk unchanged |
| Standalone text `ETI` / `RPU` vs numeric 4 / 5 crosswalk | Planning | New Era SME |
| `BF_NON_FORFEITURE` + `Type_Code=BF` filter vs current `NON_FORFEITURE` column | Planning | Conversion research |

**Partial unblock:** SME guidance for codes **1**, **2**, and combined **APL ETI** is sufficient to begin **Planning** for that subset. Full Development still requires complete code crosswalk and extract availability.

---

## G0 gate checklist

- [x] Issue folder created: `Issue_Log_Items/Issue_21/Issue_21A/`
- [x] Intake summary written
- [x] Example policies listed (7 from Issue #21 + Issue #38 cross-reference)
- [x] Owner assigned: Conversion + Client (SME)
- [x] No code, rulebook, or translation changes made

**Recommended tracking status:** `Intake` → **Planning**  
**Next stage:** Planning Agent — document approved LifePRO→QLAdmin crosswalk; trace ISWL sample policies against PPBENTYP when extract is available.
