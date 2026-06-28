# Issue #21D — Deployment Steps

**Date:** 2026-06-27  
**Converter version:** v57.36  
**Scope:** Track A + Track B1 partial release

---

## Phase 1 — Pre-deployment (QLAdmin)

| Step | Action | Owner | Status |
|------|--------|-------|--------|
| 1.1 | Confirm v57.36 in `app.py` and `QLA_Migration/app.py` headers | QLAdmin | ✅ |
| 1.2 | Archive v57.36 batch output (`QLA_Migration/Output/`) | QLAdmin | Recommended |
| 1.3 | Run Issue #21D validators (MDEPINT + blank names) | QLAdmin | ✅ PASS |
| 1.4 | Run protected-issue validators (#25/#26/#28/#21M) | QLAdmin | ✅ PASS |
| 1.5 | Run #21K validators if org policy requires | QLAdmin | ⚠️ Optional (DBF artifact) |
| 1.6 | Package release notes (`Issue_21D_Partial_Release_Notes` in UAT pack) | QLAdmin | ✅ |

---

## Phase 2 — Staging / limited release

| Step | Action | Owner |
|------|--------|-------|
| 2.1 | Deploy v57.36 converter to UAT/staging environment | QLAdmin |
| 2.2 | Run full batch against current LifePRO source extracts | QLAdmin |
| 2.3 | Load output into QLAdmin UAT instance | QLAdmin |
| 2.4 | Provide `Issue_21D_Client_UAT_Package.md` to client | QLAdmin |
| 2.5 | Document partial scope: 9 policies remain blank (B2) | QLAdmin |

---

## Phase 3 — Client UAT

| Step | Action | Owner |
|------|--------|-------|
| 3.1 | Client executes Track A UAT (ISWL rate display) | Client |
| 3.2 | Client executes Track B1 UAT (name display on 7 samples) | Client |
| 3.3 | Client acknowledges 9 B2 policies out of scope for this release | Client |
| 3.4 | Client signs UAT results or logs defects | Client |

---

## Phase 4 — Production (after UAT pass)

| Step | Action | Owner |
|------|--------|-------|
| 4.1 | Production deployment approval | Client + QLAdmin |
| 4.2 | Deploy v57.36 to production conversion pipeline | QLAdmin |
| 4.3 | Production batch + validator gate | QLAdmin |
| 4.4 | Monitor MDEPINT and quikclnt metrics post-release | QLAdmin |

---

## Phase 5 — Track B2 (parallel / follow-on)

| Step | Action | Owner |
|------|--------|-------|
| 5.1 | Client delivers corrected PRELSA extract (EXT-B1) | Client |
| 5.2 | Drop extract into `QLA_Migration/Source/` | Client |
| 5.3 | Re-batch on v57.36 (no code change expected) | QLAdmin |
| 5.4 | Re-run blank-name validator; target 0 both-blank | QLAdmin |
| 5.5 | Full Track B UAT + issue closure | Client + QLAdmin |

---

## Rollback procedure (if needed)

| Trigger | Action |
|---------|--------|
| Non-ISWL MDEPINT ≠ 4.00 | Revert to v57.35; re-batch |
| quikclnt duplicate/regression | Revert B1 logic; re-batch |
| Client UAT critical fail on Track A/B1 | Hold production; assess revert |

Detail: `Issue_21D_Rollback_Strategy.md`

---

*Deployment steps complete.*
