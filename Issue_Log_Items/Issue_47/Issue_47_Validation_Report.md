# Issue #47 — Validation Report

**Issue:** #47 — Bill Day zero fallback from Paid-To day  
**Framework stage:** Validation Agent (G5)  
**Engine:** **v57.65**  
**Date:** 2026-07-09  
**Result:** **PASS**

---

## Commands run

```text
python QLA_Migration/_validate_issue47_billday.py
→ PASS
```

Quikmstr already re-emitted under v57.65 during Development.

---

## Trace policies

| Policy | MBILLDAY | Expected | MPAIDTO | Pass? |
|--------|---------:|---------:|---------|-------|
| `018187C` | **28** | 28 | 19660728 | Yes (BA) |
| `010713704C` | 15 | 15 | 20260719 | Yes (#21B) |
| `010765930C` | 28 | 28 | 20260724 | Yes (#21B) |
| `010718309C` | 22 | 22 | 20260722 | Yes (#21B) |
| `010818663C` | 12 | 12 | 20260712 | Yes (#21B) |

---

## Fleet field alignment

| Metric | Value |
|--------|------:|
| Matched rows | 5083 |
| Source `POLICY_BILL_DAY` zero | 2967 |
| Source zeros still `MBILLDAY` zero | **0** |
| Non-zero parity (`MBILLDAY` = source) | **2116 / 2116** |
| Fleet mismatches vs expected rule | **0** |

Evidence: `evidence/issue47_validation_summary.csv`

---

## Untouched fields (spot-check)

| Field | Check | Result |
|-------|-------|--------|
| `MPAIDTO` / `MBILLTO` | Still mapped from source dates on traces | Pass |
| `MMODEPREM` | Unchanged on #21B samples | Pass |
| `MSTATUS` | `018187C` remains 45 (RPU) | Pass |

---

## Row counts

| Table | Rows |
|-------|-----:|
| `quikmstr.csv` | 5083 |

---

## G5 gate: **PASS**

**Next:** Regression Agent (G6).
