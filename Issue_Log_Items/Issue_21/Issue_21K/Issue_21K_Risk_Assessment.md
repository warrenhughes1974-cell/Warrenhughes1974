# Issue #21K — Risk Assessment (Reopened)

**Issue:** #21K — PUA Amount Precision  
**Generated:** 2026-06-28  
**Verdict:** **No-Go** — deployment incomplete / unverified

---

## Risk Summary

| Category | Level | Notes |
|----------|-------|-------|
| Converter regression | **Low** | CSV verified correct at v57.39 |
| Wrong fix layer | **High** | Changing converter would harm 1,065 rows |
| Incomplete DBF migration | **High** | Widen-without-reload leaves truncated values |
| QLAdmin display rounding | **Medium–High** | Explains $5,753.00 reopened symptom |
| Stale index / wrong folder | **Medium** | Common post-migration failure mode |
| Fleet financial exposure | **Low–Medium** | Cents-level per row; ~950 policies |

---

## Technical Risks

### R1 — Structure-only migration false completion

| Attribute | Detail |
|-----------|--------|
| Description | Client widens DBF to N(10,5) but does not reload from CSV |
| Likelihood | **High** (reported "field sizes increased" but display still wrong) |
| Impact | Stored MUNIT remains 5.752; face $5,752.00 or wrong rounded display |
| Mitigation | Mandate `--reload-quikridr`; verify stored value not just structure |

### R2 — QLAdmin display rounding layer

| Attribute | Detail |
|-----------|--------|
| Description | UI computes Amount Ins with 3 dp round or whole-dollar round |
| Likelihood | **Medium–High** for $5,753.00 symptom |
| Impact | DBF may be correct; UI still wrong — requires vendor fix |
| Mitigation | Export production DBF values; compare to UI |

### R3 — Active data path mismatch

| Attribute | Detail |
|-----------|--------|
| Description | QLAdmin reads different folder than migrated DBF set |
| Likelihood | **Medium** |
| Impact | Screenshot reflects old N(10,3) data |
| Mitigation | Confirm QLAdmin.ini / data directory; file timestamps |

### R4 — Index not rebuilt

| Attribute | Detail |
|-----------|--------|
| Description | Stale `QuikRdr.ntx` after DBF replace |
| Likelihood | **Medium** |
| Impact | Intermittent old values in search/display |
| Mitigation | Reindex procedure + timestamp audit |

### R5 — Five tables not migrated

| Attribute | Detail |
|-----------|--------|
| Description | Only QUIKRIDR widened; valuation tables remain N(*,3) |
| Likelihood | **High** (prior gate: 1/6 staging, 0/6 production) |
| Impact | Reports/valuation screens still truncate; Coverage tab may be OK if QUIKRIDR correct |
| Mitigation | Complete six-table `--migrate-dir` |

---

## Protected Issue Regression Risk

| Issue | Risk if 21K "fixed" in converter | Assessment |
|-------|----------------------------------|------------|
| #27 SL suppression | Modifying quikridr emit | **Do not** — PUA row verified |
| #26 MPREM | Touching rider loop | **Do not** |
| #25 MPOLICY padding | Touching key fields | **Do not** |
| #21M memo | Unrelated | None |
| #28 PLAN | Unrelated | None |

**Recommendation:** Keep fix in **qladmin_core deployment path** only.

---

## Business / Client Risks

| Risk | Impact |
|------|--------|
| Continued No-Go on Issue #21K | Blocks closure of Issue #21 umbrella item |
| Client trust | Visible $0.04–$1.00 mismatches on Coverage tab |
| False "implemented" status | Field widen without reload creates illusion of fix |

---

## Risk of Inaction

| Consequence | Severity |
|-------------|----------|
| ~950 policies show incorrect Amount Ins | Medium |
| PUA accumulation reports wrong | Medium |
| Re-work if converter incorrectly changed | **High** |

---

## Risk-Control Matrix

| Control | Owner | Status |
|---------|-------|--------|
| CSV precision validator | Repo | **PASS** |
| Staging DBF reload validator | Repo | **PASS** |
| Production DBF audit | Client | **MISSING** |
| Six-table migration manifest | Client | **MISSING** |
| UI UAT sign-off | Client | **MISSING** |
| Reindex confirmation | Client | **MISSING** |

---

## Go / No-Go

| Gate | Decision |
|------|----------|
| Issue #21K closure | **NO-GO** |
| Converter change | **NO-GO** |
| Deployment remediation | **GO** (after Dependency Gate) |
| Vendor escalation path | **GO** if DBF correct + UI wrong |

---

## Related

- `Issue_21K_Proposed_Fix.md`
- `Issue_21K_Next_Stage_Prompt.md`
