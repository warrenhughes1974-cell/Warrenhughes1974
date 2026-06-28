# Issue #21D — Track B1 Validation

**Date:** 2026-06-27  
**Converter version:** v57.36  
**Batch output:** `QLA_Migration/Output/` (v57.36 full batch)  
**Validators:** `validate_issue21d_blank_names.py`, `validate_insured_owner_golden.py`

---

## 1. Validation scope

Verify quikclnt referential integrity fix, seven B1-target policy recovery, both-blank population reduction, and v57.28 MPRIMID guard preservation.

**Track B2 policies excluded from failure criteria.**

---

## 2. B1-target policy verification (7/7)

| MPOLICY | MPRIMID | Resolved name | Status |
|---------|---------|---------------|--------|
| 010766896C | 592064 | JOHNSON, PENNY | ✅ PASS |
| 011080481C | 607190 | YOUNTS, JOSHUA | ✅ PASS |
| 010464869C | 589330 | ULMER, ARTHUR | ✅ PASS |
| 010464870C | 589331 | ULMER, IRENE | ✅ PASS |
| 010872417C | 604080 | EPLEY, JOHN | ✅ PASS |
| 011047402C | 589331 | ULMER, IRENE | ✅ PASS |
| 011047403C | 589330 | ULMER, ARTHUR | ✅ PASS |

---

## 3. quikclnt population

| Metric | v57.35 | v57.36 | Delta | Status |
|--------|--------|--------|-------|--------|
| quikclnt rows | 13,502 | 13,514 | **+12** | ✅ Expected |
| quikclid-referenced IDs missing from quikclnt | 14 | **0** (excl. cancelled 598766) | −14 | ✅ PASS |
| Duplicate MCLIENTID | 0 | 0 | 0 | ✅ PASS |

**Note:** Client `598766` has legitimate `CANCEL_DATE=20050615` in RNA — correctly excluded from quikclnt.

---

## 4. Both-blank population

| Metric | v57.35 | v57.36 | Status |
|--------|--------|--------|--------|
| Both-blank policies (population CSV) | 25 | **9** | ✅ Reduced |
| B1-target recovered | — | 7/7 | ✅ PASS |
| Additional recoveries (non-B1 list) | — | 9 policies | ✅ Acceptable |

### Remaining nine both-blank policies (Track B2 — RNA deficiency)

All nine have `HAS_IN_IN_QUikCLID = N` and `HAS_PO_IN_QUikCLID = N`:

| MPOLICY |
|---------|
| 010422977C |
| 010713704C |
| 010713705C |
| 010826551C |
| 010948278C |
| 014112C |
| 018900C |
| 010150910C |
| 01ML8151C |

**These correspond only to known RNA gaps — not B1 failures.**

---

## 5. v57.28 MPRIMID safeguard

| Check | Result |
|-------|--------|
| `MPRIMID = 'I'` count | **0** ✅ |
| Single-letter MPRIMID leak | **0** ✅ |
| PPOLC `PRIMARY_PERSON='I'` rows | 4,929 (correctly not mapped) |

---

## 6. Validator results

### `validate_issue21d_blank_names.py`

```text
RESULT: PASS — B1 referential integrity and target policies OK
Exit code: 0
```

### `validate_insured_owner_golden.py`

```text
Exit code: 1
Failures: 010713704C MPRIMID/MOWNRID blank
```

**Assessment:** `010713704C` is a **Track B2** golden policy (RNA missing IN/PO). Failure is **expected and excluded** from B1 acceptance per Validation Agent scope. All other golden policies pass.

---

## 7. Track B1 decision

```text
PASS
```

---

*Track B1 validation complete.*
