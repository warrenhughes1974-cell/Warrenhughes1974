# Issue #21D — Development Authorization

**Date:** 2026-06-27  
**Converter version (baseline):** v57.35  
**Authorized by:** Ownership Decision Agent  
**Effective:** Upon publication of this document

---

## Authorization summary

| Work stream | Decision | Effective scope |
|-------------|----------|-----------------|
| **Track A** — Interest crediting rate (MDEPINT) | **GO** | ISWL-scoped CSO-driven MDEPINT = 4.50 |
| **Track B1** — quikclnt referential integrity | **GO** | NULL-address / missing quikclnt row repair |
| **Track B2** — RNA re-extract | **HOLD** | Pending client delivery of corrected PRELSA extract |

**Overall:** **PARTIAL DEVELOPMENT AUTHORIZED**

Development shall proceed **only** for Track A and Track B1. Track B2 remains pending client action. No Development work on B2 until RNA extract is delivered and a separate authorization is recorded.

---

## Track A — GO

### Justification

| Criterion | Status |
|-----------|--------|
| Dependency Gate PASS | ✅ |
| CSO crosswalk in repo with 8/8 ISWL @ 4.50% | ✅ |
| 2,268 policy population verified | ✅ |
| No external data blocker | ✅ |
| Implementation conditions documented (A-CON-1 through A-CON-4) | ✅ |
| Client ISWL rate rule confirmed | ✅ |

### Authorized Development scope

| Item | Authorized? |
|------|-------------|
| Surgical `app.py` / `QLA_Migration/app.py` MDEPINT enrichment | ✅ |
| ISWL allowlist gate (8 MPLAN codes) | ✅ Required |
| MPLAN lookup from in-batch `quikridr.csv` | ✅ Required |
| Extend `qla_core/cso_mortality_crosswalk.py` (rate-percent helper) | ✅ |
| Rulebook comment update on `Sync_Rulebook_quikdvdp.csv` | ✅ |
| Global rulebook change 4.00 → 4.50 | ❌ **Prohibited** |
| Blanket CSO numeric apply to non-ISWL plans | ❌ **Prohibited** |
| Create `validate_issue21d_mdepint.py` | ✅ |
| Version bump (e.g. v57.36) | ✅ |

### Mandatory implementation constraints

1. **A-CON-1:** Override only when base MPLAN ∈ ISWL allowlist (8 codes).
2. **A-CON-2:** Resolve MPLAN from phase-1 quikridr row per policy.
3. **A-CON-3:** Fallback MDEPINT = 4.00 for all other policies.
4. **A-CON-4:** Do not change fleet-wide rulebook constant.

### Not authorized by Track A alone

- Issue #21E cash value remediation
- QUIKAINT / rate-table changes
- quikplan.NFOINT changes (must not regress)

---

## Track B1 — GO

### Justification

| Criterion | Status |
|-----------|--------|
| Dependency Gate PASS for B1 | ✅ |
| Root cause bounded (14 NAME_IDs; NULL ADDRESS_ID) | ✅ |
| ~7 policies recoverable without external data | ✅ |
| No blocker on Development start | ✅ |
| v57.28 guard must be preserved | ✅ Documented |

### Authorized Development scope

| Item | Authorized? |
|------|-------------|
| Surgical quikclnt emit fix (NULL ADDRESS_ID + valid names) | ✅ |
| Optional post-pass: quikclid-referenced IDs → quikclnt | ✅ |
| Extend `validate_insured_owner_golden.py` | ✅ |
| Create `validate_issue21d_blank_names.py` | ✅ |
| Synthesize NAME_IDs or infer roles from PPOLC | ❌ **Prohibited** |
| Map PRIMARY_PERSON = `I` to MPRIMID | ❌ **Prohibited** |
| Version bump (same release as A or separate) | ✅ |

### Mandatory implementation constraints

1. **B-CON-1:** Preserve v57.28 MPRIMID guard.
2. **B-CON-2:** Only emit clients backed by RNA NAME_ID with verifiable names.
3. **B-CON-3:** Exclude separator NAME_ID `-----------`.
4. **B-CON-4:** Document partial fix — 18 policies remain until B2.

### Expected outcome (B1 only)

- ~7 policies in blank-name population resolve
- 14 RNA NAME_IDs present in quikclnt (13 valid clients)
- 18 policies still require B2 for full Track B close

---

## Track B2 — HOLD

### Justification

| Criterion | Status |
|-----------|--------|
| External dependency EXT-B1 | ❌ Not delivered |
| 18 policies require IN/PO in RNA | Client-owned |
| Converter cannot manufacture identities | Dependency Gate confirmed |
| Development without new extract | ❌ No authorized work |

### Hold conditions (release from HOLD)

1. Client delivers updated `RelationshipNameAddress_Extract_*.csv` with IN/PO rows for affected policies.
2. QLAdmin validates extract against `Issue_21D_Blank_Name_Population.csv`.
3. Separate note or amendment authorizes B2 re-batch only (no new code expected).

### Authorized when HOLD lifts

| Item | Authorized after RNA delivery? |
|------|-------------------------------|
| Re-run full batch with new RNA | ✅ |
| Re-run blank-name validators | ✅ |
| New converter logic for missing IN/PO | ❌ Unless extract still insufficient |

---

## Combined release authorization

| Release package | Development | Client UAT | Production |
|-----------------|-------------|------------|------------|
| v57.36 Track A only | GO | Required | After UAT |
| v57.36 Track A + B1 | GO | Required (partial B) | After UAT; document 18 open |
| Full #21D (A + B1 + B2) | A+B1 GO; B2 HOLD | Required (full) | After B2 + UAT |

---

## Sign-off chain (post-Development)

| Step | Owner |
|------|-------|
| Internal validation PASS | QLAdmin |
| Client UAT PASS (Track A) | Client |
| Client UAT PASS (Track B partial/full) | Client |
| Production approval | Shared |

---

*Development authorized for Track A and Track B1 only. Proceed to Risk Agent before coding.*
