# Issue #21D — Risk Ownership

**Date:** 2026-06-27  
**Converter version:** v57.35

---

## Purpose

Assign **residual risk ownership** after Ownership Decision. Risks not eliminated by Development remain owned by the organization best positioned to manage them.

---

## Risk categories

| Category | Definition |
|----------|------------|
| **Technical risk** | Implementation, regression, schema, converter behavior |
| **Data quality risk** | Source extract completeness, referential integrity |
| **Business approval risk** | UAT, actuarial authority, production sign-off |

---

## Track A — Interest crediting rate

| Risk ID | Description | Category | Owner | Mitigation owner |
|---------|-------------|----------|-------|----------------|
| A-R1 | Non-ISWL policies incorrectly set to 4.50% | Technical | **QLAdmin** | QLAdmin — ISWL allowlist gate + validator |
| A-R2 | MPLAN lookup fails → wrong MDEPINT | Technical | **QLAdmin** | QLAdmin — fallback 4.00; validator |
| A-R3 | QLAdmin field mapping wrong (not MDEPINT) | Technical | **Shared** | QLAdmin implements; Client validates UAT |
| A-R4 | CSO crosswalk out of date vs actuarial truth | Data quality | **Client** | Client delivers CSV updates; QLAdmin consumes |
| A-R5 | Future ISWL plan added without CSO row | Data quality | **Shared** | Client catalog + CSO; QLAdmin validator flags gap |
| A-R6 | MDEPINT fix does not resolve #21E cash value | Business approval | **Client** | Client #21E decision; joint UAT |
| A-R7 | NFOINT / MDEPINT divergence on ISWL | Technical | **QLAdmin** | Validator asserts NFOINT=A unchanged |
| A-R8 | Production deploy without client UAT | Business approval | **Client** | Client UAT gate before prod |

---

## Track B1 — quikclnt integrity

| Risk ID | Description | Category | Owner | Mitigation owner |
|---------|-------------|----------|-------|----------------|
| B1-R1 | NULL-address quikclnt rows rejected by QLAdmin | Technical | **Shared** | QLAdmin implements; Client UAT on 592064 |
| B1-R2 | Duplicate MCLIENTID from emit fix | Technical | **QLAdmin** | QLAdmin dedup + schema validation |
| B1-R3 | PRIMARY_PERSON type-flag leak reintroduced | Technical | **QLAdmin** | Preserve v57.28; golden validator |
| B1-R4 | Partial fix perceived as complete | Business approval | **Shared** | QLAdmin documents 18 open; Client informed |
| B1-R5 | Wrong client row emitted (not root cause) | Technical | **QLAdmin** | Root-cause validation before merge |

---

## Track B2 — RNA completeness

| Risk ID | Description | Category | Owner | Mitigation owner |
|---------|-------------|----------|-------|----------------|
| B2-R1 | RNA re-extract delayed or not delivered | Data quality | **Client** | Client / LifePRO extract team |
| B2-R2 | Re-extract still missing IN/PO for some policies | Data quality | **Client** | Client verifies LifePRO source; EXT-B4 contingency |
| B2-R3 | IN/PO never existed in LifePRO (unfixable) | Data quality | **Client** | Client business decision on manual remediation |
| B2-R4 | Full Track B close blocked indefinitely | Business approval | **Client** | Client owns extract SLA |
| B2-R5 | Identity mismatch if converter infers roles | Technical | **QLAdmin** | **Prohibited** — no B2 converter inference authorized |

---

## Cross-track / program risks

| Risk ID | Description | Category | Owner |
|---------|-------------|----------|-------|
| X-R1 | #21E UAT conflated with #21D close | Business approval | **Shared** |
| X-R2 | Regression on #25 / #26 / #28 / #21M | Technical | **QLAdmin** |
| X-R3 | Combined release bundles A+B1 before B2 UAT | Business approval | **Shared** — document partial state |

---

## Ownership summary by organization

### QLAdmin owns

- Implementation quality and regression containment
- Validator coverage and batch integrity
- ISWL allowlist enforcement
- v57.28 guard preservation
- Documenting partial vs full fix scope

### Client owns

- RNA extract completeness (B2)
- Actuarial / business rate authority (CSO content)
- UAT execution and production approval
- LifePRO source data quality for relationship rows
- #21E business decision
- Contingency if IN/PO absent from LifePRO source system

### Shared owns

- CSO crosswalk governance (content vs consumption)
- QLAdmin field behavior confirmation (UAT)
- Release timing (partial vs full #21D)
- Joint #21D / #21E validation

---

## Risk acceptance (explicit)

| Risk | Accepted by | Condition |
|------|-------------|-----------|
| 18 policies remain blank until RNA | **Client** | Accepts partial release of B1 |
| Non-ISWL 4.00% until governed | **Client** | Pending CA-5 confirmation |
| #21E unresolved after Track A | **Client** | Separate issue scope |

---

*Risk ownership assigned. Risk Agent will expand into formal risk register before Development.*
