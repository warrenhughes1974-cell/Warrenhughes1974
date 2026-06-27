# Issue #28 — UAT Dependencies

**Gate date:** 2026-06-24

---

## UAT dependency summary

| UAT requirement | Timing | Status | Owner |
|-----------------|--------|--------|-------|
| Client confirms crosswalk binding (33 PLAN changes) | **Before Development** (G2) | **Missing** | Client |
| Client accepts re-UAT scope | **Before Release / Production** | **Missing** | Client |
| Internal validation (automated) | Before Client UAT | Planned | Internal |
| Client QLAdmin product catalog review | After Validation PASS | Required | Client |
| Phase 2 rider MPLAN review | After Phase 2 deploy | Recommended | Client |

---

## Required before Development

| Item | Required? | Evidence |
|------|-----------|----------|
| Written client confirmation that 5/22/2026 crosswalk is **binding** for all 33 PLAN code changes | **YES** | Framework G2; Planning Q1; **not in repo** |
| Client approval to proceed with code change | **YES** (same as above) | Option A changes emit behavior for 23.4% of plans |

**Verdict:** Client UAT dependency **blocks Development** until B-01 cleared.

---

## Required before Release

| Item | Required? | Evidence |
|------|-----------|----------|
| Full automated validation PASS (V-28-01 through protected validators) | **YES** | G4/G5/G6 |
| Client acceptance of **re-UAT scope** (33 PLAN value changes) | **YES** | Planning Q2; **not in repo** |
| Client spot-check of 3 reported examples | **YES** | Primary acceptance test |
| Internal rate/CSO review (recommended) | **Recommended** | Q5 — soft gate |

**Verdict:** Client re-UAT scope acceptance **must be documented before Release** (B-02).

---

## Required before Production

| Item | Required? | Evidence |
|------|-----------|----------|
| Client UAT PASS on product catalog / plan codes | **YES** | 33 PLAN changes are client-visible |
| Catalog copies synchronized (governance + migration) | **YES** | B-05 |
| Rollback procedure communicated | **YES** | Implementation Strategy |
| v57.35 release notes published | **YES** | Release dependency |
| Protected issues regression PASS on production candidate batch | **YES** | #25, #26, #21M, #21M-FU |

**Verdict:** Production requires **Client UAT PASS** + B-01/B-02 satisfied.

---

## Not required

| Item | Reason |
|------|--------|
| Client UAT before Ownership Decision | Ownership is internal governance |
| Client UAT before Risk Agent | Risk quantifies impact; no deploy |
| Re-UAT of QUIKMEMO (#21M) | No code path change |
| Re-UAT of MPOLICY width (#25) | No MPOLICY logic change |
| Re-UAT of MPREM (#26) | No MPREM rulebook change |
| Re-UAT of MUNIT (#21K) | No MUNIT change in #28 scope |

---

## Client UAT test packet (draft — for Release)

### Primary acceptance (must PASS)

| # | LifePRO Coverage_ID | Expected quikplan.PLAN | v57.34 (fail) |
|---|---------------------|------------------------|---------------|
| 1 | 10827 MN5K | 1CSIMN | 10827 MN5K |
| 2 | 0823 960CH | 960CWP | 0823 960CH |
| 3 | 0824 P DIS | 94PDIS | 0824 P DIS |

### Secondary acceptance (spot-check 5 from divergent set)

Source: `Issue_28_Mapping_Differences.csv` where `matches_authoritative=N`

Suggested: 1579 GPO → 9GPO79, L10 PRE97 → 1L10OD, DISCHO247C → 9DS24C, 621 PUA → 121PUA, WP 646 → 9WP646

### Phase 2 acceptance (if P3E in release)

| Check | Expected |
|-------|----------|
| Rider MPLAN on sample policy with 0823 960CH | 960CWP |
| No orphan MPLAN values absent from quikplan.PLAN | Referential integrity |

---

## UAT baseline invalidation

| Artifact | Invalid after fix? |
|----------|------------------|
| v57.34 `quikplan.csv` PLAN column (33 values) | **Yes** |
| Client plan review sign-off on v57.34 (if any) | **Yes** |
| v57.34 quikridr MPLAN (Phase 2) | **Partial** — rider rows on affected plans |
| Memo/MPOLICY/MPREM UAT evidence | **No** |

---

## UAT dependency decision

| Question | Answer |
|----------|--------|
| Does 33 PLAN change require client re-UAT? | **YES** |
| Before Development? | Binding confirmation only (B-01) |
| Before Release? | Re-UAT scope acceptance (B-02) + validation PASS |
| Before Production? | Full client UAT PASS on plan catalog |

**Do not assume** client has accepted re-UAT — **document Missing** until written confirmation in issue log or client artifact folder.
