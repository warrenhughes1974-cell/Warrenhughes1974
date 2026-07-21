# Issue #85 — Planning Report

**Issue:** #85 — Duplicate claim headers sharing the same policy + phase  
**Framework stage:** Planning Agent (G1)  
**Status:** Planning Complete → Dependency Gate  
**Generated:** 2026-07-17  
**Model:** Cursor Grok 4.5 (locked)  
**Code changes:** None  
**Scope authority:** `Issue_85_Scope_Decisions.md`

---

## 1. Executive Finding

Real Policy book has **0** duplicate `MPOLICY`+`MPHASE` claim headers; our emit has **3,054**. That structural mismatch is the main reason policy-level Net Payment vs payee checks is only ~60% balanced in our data vs **99.8%** in the real book. Fix is a **header identity / consolidation rule**, not a money-formula tweak. **Go for Dependency Gate / Risk** after decisions D1–D5 (defaults documented).

---

## 2. Confirmed Sources / Targets

| Layer | Path | Role |
|-------|------|------|
| Authority | `docs/Policy/quikclms.dbf` | 0 dup pol+phase |
| Authority payees | `docs/Policy/quikclmp.dbf` | 99.8% policy-level balance |
| Converted headers | `QLA_Migration/Output/quikclms.csv` | 5,624 rows; 3,054 dups |
| Converted payees | `QLA_Migration/Output/quikclmp.csv` | Must re-attach, not invent |
| Evidence | `Issue_84/.../risk_review_issue84_join_check.py` | Quantified structure gap |

---

## 3. Recommended Technical Direction (no code yet)

1. Detect duplicate groups on (`MPOLICY`, `MPHASE`).  
2. Apply winner rule (D2).  
3. Re-point `quikclmp` rows per D4.  
4. Drop or archive losers per D3.  
5. Emit audit CSV under `Reports/` (never in Output root).  
6. Hand off cleaned headers to #84 Track B.

---

## 4. Estimated Impact

| Metric | Count |
|--------|------:|
| Duplicate header rows | 3,054 |
| Multi-header policies | 735 |
| Unbalanced policies (money) | 898 (owned jointly with #84 after structure fix) |

---

## 5. Open Questions

See Decisions D1–D5 in `Issue_85_Scope_Decisions.md`. Non-blocking for Risk if planning defaults accepted.

---

## 6. Recommended Risk Prompt

```
Proceed to Risk Agent for Issue #85.
Read Scope Decisions (D1–D5). Quantify winner/loser impact under D1-A default.
No code. Preserve #78 payees and #79 CLAIMSTAT.
```
