# Issue #28 — Blockers and Assumptions

**Gate date:** 2026-06-24  
**Gate status:** CONDITIONAL PASS

---

## Active blockers

| ID | Blocker | Owner | Blocks stage | Requested action | Evidence |
|----|---------|-------|--------------|------------------|----------|
| **B-01** | Client written confirmation that Policy Form Crosswalk **5/22/2026** is **binding** for all 33 PLAN code changes | **Client** | **Development** (G2) | Email, issue log sign-off, or change-order referencing xlsx as sole PLAN authority | Issue opened with crosswalk as authority; **no waiver document in repo** |
| **B-02** | Client written acceptance of **re-UAT scope** for 33 changed quikplan PLAN values | **Client** | **Release / Production** | Confirm product catalog re-review and acceptance criteria for 3 client examples + spot checks | Planning § UAT; v57.34 baseline invalid for plan review |
| **B-03** | `DISCHO25` catalog row absent | **Internal (Development Phase 0)** | **Full 141/141 catalog alignment** | Add row from xlsx before or with Phase 1 | Gate verification: only xlsx ID missing from catalog |
| **B-04** | Issue #28 validator not yet implemented | **Internal (Development)** | **Validation (G4)** | Create `_validate_issue28_plan_mapping.py` | Planned in Implementation Strategy — not a pre-dev gate blocker |
| **B-05** | `QLA_Migration/Mapping/product_catalog_crosswalk.csv` stale (133 vs 140 rows) | **Internal (Development/Release)** | **Production deploy** | Sync with `plan_governance/` copy in same change set | Intake catalog drift |

---

## Non-blockers (resolved dependencies)

| Item | Resolution |
|------|------------|
| Root cause unknown | Resolved — Intake/Planning |
| Crosswalk file missing | Resolved — xlsx + catalog column in repo |
| DISCHO25 = DISCHO247C? | Resolved — **separate products** (`Issue_28_DISCHO25_Investigation.md`) |
| Which remediation option | Resolved — Option A Phase 1 recommended |
| Runtime function location | Resolved — `load_product_catalog_crosswalk()` |
| Protected issue touch | Resolved — orthogonal paths; validators only |

---

## Documented assumptions (proceed if client silent — with risk)

| ID | Assumption | Risk if wrong | Waivable? |
|----|------------|---------------|-----------|
| **A-01** | Issue #28 client report implies crosswalk binding without separate sign-off | Client rejects 33 PLAN changes post-fix | **No** — requires B-01 |
| **A-02** | FORM column changes remain **out of scope** for #28 | Scope creep if client expects form alignment | Yes — confirm at UAT (Q4) |
| **A-03** | Phase 2 P3E can ship in same release as Phase 1 | quikridr MPLAN lag if deferred | Yes — Phase 2 optional for Phase 1 release |
| **A-04** | Rate table gaps (`PLAN_NOT_IN_TARGET`) are pre-existing | Rate UAT failures on corrected PLAN codes | Yes — internal rate review (Q5) |
| **A-05** | `ql_plan_code` compat column retained for rollback | None — documented rollback | Yes |

---

## Assumptions explicitly NOT permitted

| Prohibited assumption | Reason |
|-----------------------|--------|
| DISCHO25 aliases to DISCHO247C | Disproven by crosswalk rows, descriptions, and plan codes |
| Overlay default ON replaces Option A | Incomplete for quikridr; dual-path |
| Development without client crosswalk binding | Framework G2 violation |
| Skip protected issue validators | Framework non-negotiable |

---

## Blocker → stage matrix

| Stage | Can proceed under CONDITIONAL PASS? | Condition |
|-------|-------------------------------------|-----------|
| Ownership Decision | **Yes** | Formalize code/data/client ownership |
| Risk Agent | **Yes** | Quantify rate/MPLAN impact |
| Development Phase 0 (DISCHO25 row) | **Yes** | Internal data — no client blocker |
| Development Phase 1 (code) | **No** until **B-01 cleared** or **written client waiver** | G2 |
| Validation | **No** until Development complete + **B-04** | G4 |
| Client UAT | **No** until **B-02 cleared** | Release gate |
| Production | **No** until B-01, B-02, B-05 cleared | Deploy gate |

---

## Recommended issue status

**Active — Conditional Gate Pass (Awaiting Client Clarification on B-01, B-02)**

Sub-status for tracking:
- Technical dependencies: **Ready for Ownership Decision + Risk Review**
- Client dependencies: **Blocked — Awaiting Client Clarification** (B-01, B-02)
