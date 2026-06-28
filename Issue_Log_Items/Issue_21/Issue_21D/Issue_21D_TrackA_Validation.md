# Issue #21D — Track A Validation

**Date:** 2026-06-27  
**Converter version:** v57.36  
**Batch output:** `QLA_Migration/Output/` (v57.36 full batch)  
**Validator:** `tools/validators/validate_issue21d_mdepint.py`

---

## 1. Validation scope

Verify ISWL-scoped `quikdvdp.MDEPINT = 4.50` for exactly 2,268 policies; non-ISWL remain `4.00`; no unintended fleet-wide rate change.

---

## 2. ISWL allowlist verification

| MPLAN | In batch (phase-1 quikridr) | CSO rate |
|-------|------------------------------|----------|
| 1658C1 | ✅ | 4.50% |
| 1658CS | ✅ | 4.50% |
| 1659C2 | ✅ | 4.50% |
| 1659CR | ✅ | 4.50% |
| 1659CS | ✅ | 4.50% |
| 1659SR | ✅ | 4.50% |
| 1669SR | ✅ | 4.50% |
| 1679CS | ✅ | 4.50% |

**All eight ISWL plans present:** ✅

---

## 3. Population results

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| ISWL policies (allowlist) | 2,268 | 2,268 | ✅ PASS |
| ISWL `MDEPINT = 4.50` | 2,268 | 2,268 | ✅ PASS |
| Non-ISWL policies | 2,815 | 2,815 | ✅ PASS |
| Non-ISWL `MDEPINT = 4.00` | 2,815 | 2,815 | ✅ PASS |
| Unique MDEPINT values | 4.00, 4.50 | 4.00, 4.50 | ✅ PASS |
| Fleet quikdvdp rows | 5,083 | 5,083 | ✅ PASS |

---

## 4. Sample policy verification

| MPOLICY | MPLAN | MDEPINT | Expected | Status |
|---------|-------|---------|----------|--------|
| 010713704C | 1659C2 | 4.50 | 4.50 | ✅ PASS |
| 010818663C | 1659C2 | 4.50 | 4.50 | ✅ PASS |

---

## 5. NFOINT regression check

ISWL quikplan templates retain `NFOINT = A` (unchanged path). No quikplan row-count or PLAN mapping change detected.

---

## 6. Validator output

```text
RESULT: PASS — ISWL MDEPINT 4.50; non-ISWL unchanged at 4.00
Exit code: 0
```

---

## 7. Track A decision

```text
PASS
```

---

*Track A validation complete.*
