# Source Authority

**Owner:** Actuarial / Product + Project Lead  
**Last updated:** 2026-07-12 (Stage 4A — findings populated; **no AUTHORITATIVE approvals**)  
**Register:** `manifests/source_authority_register.csv`  
**By domain:** `reports/governance/source_authority_by_domain.csv`

## Purpose

Define which source is authoritative for each Citizens data domain. Stage 4A records **proposed** precedence only.

## Authority Status Legend

| Status | Meaning |
|--------|---------|
| `PROPOSED` | Stage 4A recommendation pending confirmation |
| `PENDING_CLIENT_CONFIRMATION` | Needs client |
| `PENDING_ACTUARIAL_CONFIRMATION` | Needs actuarial |
| `SUPPORTING_ONLY` | May corroborate; not primary |
| `VALIDATION_ONLY` | Checkpoint only |
| `HISTORICAL_ONLY` | Archive / not current |
| `NOT_AUTHORITATIVE` | Must not drive conversion |
| `DERIVED_WORKING` | Internal work product |
| `UNKNOWN` | No source identified |
| `AUTHORITATIVE` | **Not used in Stage 4A** — requires approved DECISION_LOG |

---

## Plan Universe / Plan Code / Name / Family / Base vs Rider

| Domain | Proposed primary | Secondary | Validation | Status | Decision |
|--------|------------------|-----------|------------|--------|----------|
| Plan universe | Plans DBF (existence) + Tracker/Catalog (requirements coverage) + union for review | Crosswalk (mapping subset) | Product catalog (family-level) | PROPOSED / PENDING_CLIENT_CONFIRMATION | CIT-DEC-001/008 |
| Plan code | `cifi0004.pl_plan` when present | Tracker `cfic_plan_code` | Crosswalk | PROPOSED | CIT-DEC-001 |
| Plan name | DBF `pl_desc` (often blank) | Tracker/catalog family | — | PENDING_CLIENT_CONFIRMATION | CIT-DEC-001 |
| Product family | Requirements catalog / tracker | Access product catalog | — | DERIVED_WORKING | CIT-DEC-001 |
| Base vs rider | Catalog Product Form/Family | Tracker | — | PROPOSED | CIT-DEC-006 |
| Active vs historical | **UNKNOWN** at plan-code level | Access “all products ACTIVE” note is family-level only | — | PENDING_CLIENT_CONFIRMATION | CIT-DEC-007 |

**Conflict rule:** Do not drop tracker-only or DBF-only codes. Record both with reconciliation status.

**Gaps:** 23 tracker-only; 16 DBF-only; 15 reserve-staging-only codes; issue dates largely unknown.

---

## Dimensions (State / Sex / Smoker / Band / Issue Era)

| Domain | Proposed primary | Status | Decision |
|--------|------------------|--------|----------|
| Sex / smoker encoding | Plan-code suffix patterns + crosswalk grouping | PROPOSED (document; keep codes distinct) | CIT-DEC-005 |
| State / issue-era / band | **UNKNOWN** formal authority | PENDING_ACTUARIAL_CONFIRMATION | CIT-DEC-005/007 |

---

## Rate Requirements

| Proposed primary | Status | Decision |
|------------------|--------|----------|
| Requirements Catalog + Rate Load Tracker | DERIVED_WORKING / PENDING_CLIENT_CONFIRMATION | CIT-DEC-008 |

**Gaps:** Catalog Inventory Status largely “Not Reviewed”; Rate Gap Decision “TBD”.

---

## Gross Premiums

| Role | Source | Status |
|------|--------|--------|
| Proposed primary | Access extracts / MDB | PROPOSED / PENDING_ACTUARIAL_CONFIRMATION |
| Supporting | Rate-sheet PDFs | SUPPORTING_ONLY |
| Not authoritative | OCR extracts; Reserve DBF | NOT_AUTHORITATIVE / N/A |
| Decision | CIT-DEC-009 | |

---

## Cash Values

| Role | Source | Status |
|------|--------|--------|
| Proposed primary | `cifi0007.DBF` | PROPOSED / PENDING_ACTUARIAL_CONFIRMATION |
| Supporting | `source/original/cash_values/*_CV.zip` | SUPPORTING_ONLY |
| Validation | Access CashValue* checkpoints | VALIDATION_ONLY |
| Not authoritative | OCR; Draft QuikCvs | NOT_AUTHORITATIVE |
| Known gap | OBQ-1 factor basis | CIT-DEC-010 |

---

## Net Premiums / Terminal Reserves / Mean Reserves / Paid-Up

| Domain | Proposed primary | Status | Decision |
|--------|------------------|--------|----------|
| Net premiums | Reserve DBF | PROPOSED / PENDING_ACTUARIAL_CONFIRMATION | CIT-DEC-011 |
| Terminal reserves | Reserve DBF | PROPOSED / PENDING_ACTUARIAL_CONFIRMATION | CIT-DEC-012 |
| Mean reserves | Reserve DBF fields (candidate) | UNKNOWN mapping | CIT-DEC-012 |
| Paid-up | Reserve DBF PUP | PROPOSED / PENDING_ACTUARIAL_CONFIRMATION | CIT-DEC-013 |

**Conflict rule:** Prefer DBF over PDF/OCR when both exist. Staging CSVs are derived (SA-006), not independent authority.

---

## Extended Term / Dividends / Interest / Charges

| Domain | Status | Decision |
|--------|--------|----------|
| Extended-term insurance | UNKNOWN | CIT-DEC-014 |
| Dividends / dividend interest | UNKNOWN (catalog often N/A) | CIT-DEC-016 |
| Loan interest | Plans DBF IR1–IR8 **candidate** | CIT-DEC-015 |
| Guaranteed / current / credited interest | UNKNOWN | CIT-DEC-015 |
| COI / expenses / loads / surrender / modal / guideline / MEC / target / settlement | UNKNOWN (requirements flags only) | CIT-DEC-017 |
| Policy fees | Plans DBF fee fields **candidate** | CIT-DEC-017 |
| Rider premiums | Access rider tables + catalog **candidate** | CIT-DEC-006 |

---

## QLAdmin Mapping / Validation / UAT / Draft / Archive

| Domain | Status | Decision |
|--------|--------|----------|
| QLAdmin plan mapping | Working crosswalk incomplete — DERIVED_WORKING | CIT-DEC-004 |
| Validation | Access + issue evidence — VALIDATION_ONLY | CIT-DEC-018 |
| Client UAT | None yet | CIT-DEC-020 |
| Draft Quik outputs | NOT_AUTHORITATIVE | CIT-DEC-018 |
| SourceData_11-18-2024 | HISTORICAL_ONLY | CIT-DEC-019 |
| cifianu1.dbf | PENDING_REVIEW (quarantine) | Separate quarantine decision |

---

## Affected Conversion Work

- **May design neutrally now:** path config, Engine pin (no business rules encoded).
- **Blocked until authority/mapping approvals:** production Quik publish, approved mappings, UAT packaging for rates.
- **Blocked for specific rate types:** ETI, dividends, most UL/expense factors, gross premium fleet emit.

## Update Instructions

1. Promote any domain to formally authoritative only with `DECISION_LOG` status `APPROVED`.
2. Never treat draft Quik output or OCR as source authority.
3. Never equate blank, zero, missing, unknown, and not applicable.
