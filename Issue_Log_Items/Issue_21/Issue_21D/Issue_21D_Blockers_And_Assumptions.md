# Issue #21D — Blockers and Assumptions

**Date:** 2026-06-27  
**Converter version:** v57.35

---

## Gate decision

| Scope | Decision |
|-------|----------|
| **Overall Issue #21D** | **CONDITIONAL PASS** |
| **Track A — Development** | **PASS** (with implementation conditions) |
| **Track A — Release / Production** | **CONDITIONAL** (UAT + #21E coordination) |
| **Track B — Development (B1 only)** | **PASS** |
| **Track B — Development (B2)** | **BLOCKED** (external RNA) |
| **Track B — Release / Production** | **BLOCKED** until RNA re-extract |

Track A is **not blocked** by Track B external dependencies.

---

## Track A — Blockers

| ID | Blocker | Severity | Blocks Development? | Resolution |
|----|---------|----------|---------------------|------------|
| A-BLK-1 | None | — | No | — |

---

## Track A — Conditions (must be enforced in Development)

| ID | Condition | Rationale |
|----|-----------|-----------|
| A-CON-1 | **MDEPINT override gated to ISWL plan allowlist (8 MPLAN codes)** | CSO crosswalk contains numeric rates for 25 non-ISWL plan codes affecting 1,688 policies; blanket CSO apply would violate "preserve 4.00% for non-ISWL" |
| A-CON-2 | **MPLAN resolved from in-batch `quikridr.csv`** (phase 1 base row) | PPBENTYP has no PLAN column; batch runs quikridr before quikdvdp |
| A-CON-3 | **Fallback MDEPINT = 4.00** when MPLAN not in ISWL allowlist | Preserves current non-ISWL behavior |
| A-CON-4 | **Do not change global rulebook constant to 4.50** | Would affect all 5,083 policies |

---

## Track A — Assumptions

| ID | Assumption | Risk if wrong |
|----|------------|---------------|
| A-ASM-1 | QLAdmin Dividend Accum Int Rate reads `quikdvdp.MDEPINT` as numeric percent | Medium — UAT on `010713704C` validates |
| A-ASM-2 | `4.50` stored in MDEPINT displays as 4.50% (not 0.045) | Low — matches current 4.00 format |
| A-ASM-3 | All ISWL crediting rates are uniformly 4.50% (no issue-date variance) | Low — client confirmed; CSO agrees |
| A-ASM-4 | CSO `nfo_interest_source` is acceptable MDEPINT authority (not just NFOINT code) | Medium — actuarial ownership decision in Ownership stage |
| A-ASM-5 | Track A fix alone does not close Issue #21E | High if assumed — CV load-vs-compute still open |

---

## Track B — Blockers

| ID | Blocker | Severity | Blocks Development? | Blocks Release? | Resolution |
|----|---------|----------|---------------------|-----------------|------------|
| B-BLK-1 | **RNA re-extract not delivered** for 18 policies missing IN and/or PO roles | High | B2 only | **Yes** | Client / LifePRO extract team re-pull PRELSA |
| B-BLK-2 | None for B1 quikclnt fix | — | No | No | Development can proceed |

---

## Track B — Conditions

| ID | Condition | Rationale |
|----|-----------|-----------|
| B-CON-1 | B1 must not synthesize NAME_IDs or map PRIMARY_PERSON=`I` to MPRIMID | v57.28 guard must remain |
| B-CON-2 | quikclnt fix limited to RNA-backed NAME_IDs with verifiable names | Data governance |
| B-CON-3 | Separator row NAME_ID `-----------` must remain excluded | Invalid ID in RNA |
| B-CON-4 | B1 and B2 may ship in separate releases | B2 external dependency |

---

## Track B — Assumptions

| ID | Assumption | Risk if wrong |
|----|------------|---------------|
| B-ASM-1 | NULL ADDRESS_ID is why 12/13 missing clients fail quikclnt emit | Medium — Development validates root cause first |
| B-ASM-2 | QLAdmin accepts quikclnt rows with blank address but populated names | Medium — UAT on 592064 / 607190 |
| B-ASM-3 | LifePRO holds IN/PO for RNA-gap policies (hierarchy analysis) | Medium — re-extract should restore; if not in LifePRO, unfixable |
| B-ASM-4 | 7 quikclnt-gap policies fully fixable by B1 | Low–medium |
| B-ASM-5 | 18 RNA-role-gap policies require extract, not converter inference | High if violated — identity risk |

---

## Policy population assumptions (Track B)

| Category | Count | Remediation owner |
|----------|------:|-------------------|
| RNA missing both IN and PO | 9 | Client extract (B2) |
| RNA missing IN only (PO present) | 3 | Client extract (B2) |
| RNA missing PO only (IN present) | 6 | Client extract (B2) |
| quikclnt missing row (IN/PO present in quikclid) | 7 | Development (B1) |
| **Total blank-name population** | **25** | Hybrid |

---

## External blockers summary

| Dependency | Owner | Tracks blocked | Development blocked? |
|------------|-------|----------------|----------------------|
| RNA re-extract for 18-policy list | Client / LifePRO | B2, full #21D close | **No** (A and B1 proceed) |
| Client UAT sign-off | Client | Release / Production | No |
| Non-ISWL 4.00% confirmation | Client | Track A release (recommended) | No |
