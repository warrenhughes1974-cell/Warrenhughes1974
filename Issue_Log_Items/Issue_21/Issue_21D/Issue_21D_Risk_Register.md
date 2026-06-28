# Issue #21D — Risk Register

**Date:** 2026-06-27  
**Converter version:** v57.35  
**Scope:** Track A + Track B1 (Development authorized) · Track B2 (external — documented, not scored)  
**Overall risk decision:** **GO** (Development may proceed)

---

## Register

| Risk ID | Track | Category | Description | Owner | Likelihood | Impact | Severity | Mitigation | Status |
|---------|-------|----------|-------------|-------|------------|--------|----------|------------|--------|
| A-R01 | A | Technical | Non-ISWL policies incorrectly receive MDEPINT 4.50% | QLAdmin | M | H | **High** | ISWL allowlist gate (A-CON-1); baseline diff validator | Open → Mitigate in Dev |
| A-R02 | A | Technical | ISWL policy retains 4.00% due to MPLAN lookup failure | QLAdmin | L | H | **Medium** | Phase-1 quikridr lookup; 2,268-row pass criteria | Open → Mitigate in Dev |
| A-R03 | A | Technical | NFOINT regression during MDEPINT work | QLAdmin | L | M | **Low** | Assert NFOINT unchanged in validator | Open → Mitigate in Dev |
| A-R04 | A | Business | QLAdmin display field differs from assumed MDEPINT path | Client | L | H | **Low** | UAT on 010713704C Dividend Accum Int Rate | Open → UAT |
| A-R05 | A | Business | #21E conflated with #21D Track A closure | Shared | M | M | **Medium** | Separate issue tracking; joint UAT only | Open → Monitor |
| A-R06 | A | Data | New ISWL plan added without allowlist update | Shared | L | M | **Low** | CSO + allowlist sync validator | Open → Monitor |
| A-R07 | A | Technical | Fleet rulebook constant changed to 4.50 | QLAdmin | L | H | **High** | **Prohibited** — code review | Closed (preventive) |
| A-R08 | A | Operational | CSO crosswalk updated with wrong rate | Client | L | M | **Medium** | Client actuarial owns CSV; QLAdmin validates on batch | Open → Monitor |
| A-R09 | A | Operational | Non-ISWL 4.00% not confirmed before prod | Client | M | M | **Medium** | EXT-A2 sign-off recommended | Open → UAT |
| B1-R01 | B1 | Technical | MPRIMID='I' type-flag leak reintroduced | QLAdmin | L | H | **Medium** | Preserve v57.28 guard; validator | Open → Mitigate in Dev |
| B1-R02 | B1 | Technical | Duplicate quikclnt MCLIENTID rows | QLAdmin | L | M | **Low** | Dedup by MCLIENTID; uniqueness validator | Open → Mitigate in Dev |
| B1-R03 | B1 | Technical | Incorrect client association emitted | QLAdmin | L | H | **Low** | RNA NAME_ID only; golden policy checks | Open → Mitigate in Dev |
| B1-R04 | B1 | Operational | QLAdmin rejects NULL-address quikclnt row | Client | L | M | **Low** | UAT on client 592064 | Open → UAT |
| B1-R05 | B1 | Business | Partial B1 fix perceived as full Track B closure | Shared | M | M | **Medium** | Release notes; 18-policy B2 list | Open → Communicate |
| B1-R06 | B1 | Technical | Over-broad quikclnt emit beyond 14 IDs | QLAdmin | L | M | **Low** | Bound to missing IDs with RNA names | Open → Mitigate in Dev |
| B1-R07 | B1 | Technical | quikclnt schema / field order drift | QLAdmin | L | H | **Low** | Standard schema validation | Open → Mitigate in Dev |
| B2-R01 | B2 | Data | RNA missing IN/PO for 18 policies | **Client** | H | M | **High** | EXT-B1 re-extract | **External — not Dev scope** |
| B2-R02 | B2 | Data | LifePRO source lacks IN/PO (unfixable by extract) | **Client** | L | H | **Medium** | EXT-B4 contingency; document exception | External |
| B2-R03 | B2 | Business | Full #21D blocked until B2 complete | Client | M | M | **Medium** | Partial release for A+B1 | External |
| B2-R04 | B2 | Operational | RNA re-extract delayed indefinitely | Client | M | M | **Medium** | Client action register P1 | External |
| X-R01 | Cross | Technical | Regression on Issue #25 MPOLICY | QLAdmin | L | H | **Low** | No MPOLICY touch; run validate_issue21.py | Open → Test |
| X-R02 | Cross | Technical | Regression on Issue #26 MPREM | QLAdmin | L | H | **Low** | No quikridr MPREM touch; run validator | Open → Test |
| X-R03 | Cross | Technical | Regression on Issue #28 plan mapping | QLAdmin | L | H | **Low** | No crosswalk authority change | Open → Test |
| X-R04 | Cross | Technical | Regression on Issue #21M QUIKMEMO | QLAdmin | L | M | **Low** | No quikmemo grain change | Open → Test |
| X-R05 | Cross | Technical | Regression on Issue #21M-FU DBF packaging | QLAdmin | L | M | **Low** | No packaging change | Open → Test |
| X-R06 | Cross | Technical | Regression on Issue #21K fleet/MUNIT | QLAdmin | L | M | **Low** | No quikplan MUNIT touch | Open → Test |
| X-R07 | Cross | Technical | v57.28 MPRIMID guard bypassed | QLAdmin | L | H | **Medium** | Code review + validator | Open → Mitigate in Dev |

---

## Severity legend

| Severity | Criteria |
|----------|----------|
| **High** | Fleet-wide impact or blocks release without mitigation |
| **Medium** | Bounded impact or release-conditional |
| **Low** | Mitigated by standard validation |

---

## Track decisions (from register)

| Track | Decision | Highest open severity |
|-------|----------|----------------------|
| **Track A** | **GO** | A-R01 (mitigated by allowlist) |
| **Track B1** | **GO** | B1-R01 (mitigated by v57.28 preservation) |
| **Track B2** | **External** — not in Dev GO/NO-GO | B2-R01 (client-owned) |

---

## Acceptance criteria for risk closure (post-Development)

| Risk ID | Closure criterion |
|---------|-------------------|
| A-R01, A-R02 | `validate_issue21d_mdepint.py` PASS |
| A-R03 | NFOINT diff empty for ISWL templates |
| B1-R01 | MPRIMID='I' count = 0 |
| B1-R02 | quikclnt MCLIENTID unique |
| B1-R03, B1-R06 | 7-policy name resolution + row count ≤ +14 |
| X-R01–X-R07 | Protected-issue validators PASS |
| B2-R01 | Closed only after EXT-B1 delivery + revalidation |

---

*Risk register maintained by Risk Agent. Update after Development and QA.*
