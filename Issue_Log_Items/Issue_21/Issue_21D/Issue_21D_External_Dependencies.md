# Issue #21D — External Dependencies

**Date:** 2026-06-27  
**Converter version:** v57.35

---

## Summary

| Category | External? | Blocks Development? | Blocks Release? |
|----------|-----------|---------------------|-----------------|
| Track A — CSO crosswalk | No (in repo) | No | No |
| Track A — Client UAT | Yes | No | Yes |
| Track A — #21E coordination | Internal cross-issue | No | Conditional |
| Track B — RNA re-extract | **Yes** | No (B1 only) | **Yes (full Track B)** |
| Track B — Client UAT | Yes | No | Yes |

---

## Track A — External dependencies

| ID | Dependency | Owner | Status | Required for |
|----|------------|-------|--------|--------------|
| EXT-A1 | Client confirmation: 4.50% for all ISWL | Client / Business | ✅ **Received** (Intake) | Planning — done |
| EXT-A2 | Client confirmation: non-ISWL remain 4.00% until governed | Client / Actuarial | ⏳ **Recommended** | Release sign-off |
| EXT-A3 | QLAdmin UAT — Dividend Accum Int Rate display | Client | 🔲 Pending | Release / close |
| EXT-A4 | Issue #21E cash-value decision | Client | 🔲 Open (separate issue) | #21E close; coordinate with #21D UAT |

**No external data file required for Track A Development.**

---

## Track B — External dependencies

| ID | Dependency | Owner | Status | Required for |
|----|------------|-------|--------|--------------|
| EXT-B1 | **RNA re-extract** — IN/PO rows for 18 policies | Client / LifePRO extract team | 🔲 **Not delivered** | B2; full blank-name resolution |
| EXT-B2 | Policy list handoff | Conversion team | ✅ Available | `Issue_21D_Blank_Name_Population.csv` |
| EXT-B3 | QLAdmin UAT — name display | Client | 🔲 Pending | Release / close |
| EXT-B4 | LifePRO role confirmation (if re-extract fails) | Client | 🔲 Contingency | Policies where IN/PO not in source system |

---

## Track B — Internal vs external by policy category

### Converter-only (internal — Phase B1)

Policies where IN/PO exist in quikclid but quikclnt row missing:

| MPOLICY | Missing MCLIENTID(s) | RNA names present |
|---------|----------------------|-------------------|
| 010766896C | 592064 | JOHNSON, PENNY |
| 011080481C | 607190 | YOUNTS, JOSHUA |
| 010464869C | 589330 | (in RNA) |
| 010464870C | 589331 | (in RNA) |
| 010872417C | 604080 | (in RNA) |
| 011047402C | 589331 | (in RNA) |
| 011047403C | 589330 | (in RNA) |

**Count:** 7 policies — **no external dependency for Development start.**

### Client extract required (external — Phase B2)

**RNA missing both IN and PO (9 policies):**

010422977C, 010713704C, 010713705C, 010826551C, 010948278C, 014112C, 018900C, 010150910C, 01ML8151C

**RNA missing IN only (3 policies):**

010774773C, 010816156C, 010877890C

**RNA missing PO only (6 policies):**

011188773C, 010397945C, 010790779C, 010834096C, 011062307C, 011064567C

**Count:** 18 policies — **require EXT-B1 before full Track B release.**

---

## RNA re-extract request specification (for client)

| Field | Value |
|-------|-------|
| **Extract** | PRELSA / `RelationshipNameAddress_Extract` |
| **Priority policies** | Issue #21 golden set + `Issue_21D_Blank_Name_Population.csv` |
| **Required roles** | At minimum `IN`, `PO` where they exist in LifePRO |
| **Evidence of gap** | Policy `9010713704` (010713704C): LifePRO hierarchy shows IN\|PA\|PO; current RNA has SA+BK only |
| **Delivery** | Drop into `QLA_Migration/Source/`; re-run batch |

---

## quikclnt gap — technical external boundary

| Item | Internal | External |
|------|----------|----------|
| Fix emit for NULL ADDRESS_ID | ✅ Conversion team | — |
| Deliver corrected RNA rows | — | ✅ Extract team |
| Validate names in QLAdmin | — | ✅ Client UAT |

---

## Dependency on other issues (not external orgs)

| Issue | Relationship |
|-------|--------------|
| #21E | Track A MDEPINT may affect CV display; validate together — does not block Development |
| #25, #26, #28 | No external dependency |
| #21M, #21M-FU | No external dependency |

---

## Readiness matrix

| Milestone | Track A | Track B1 | Track B2 | Full #21D |
|-----------|---------|----------|----------|-----------|
| **Development start** | ✅ Ready | ✅ Ready | ❌ Blocked | ⚠️ Partial |
| **Internal QA complete** | After dev | After dev | After EXT-B1 | After both |
| **Client UAT** | EXT-A3 | Partial | EXT-B3 | EXT-B3 |
| **Production** | After UAT | Partial fix OK | Full fix needed | All above |
