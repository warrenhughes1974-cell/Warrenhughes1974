# Issue #160 — Validation Report

**Issue:** #160 — PUA phase stays Expired (56) instead of following base terminal status
**Framework stage:** Validation Agent (independent re-derivation, not a re-run of the coder's own claims)
**Engine version:** v59.09
**Validator:** `tools/validators/validate_issue160_pua_terminal_status.py`
**Output directory:** `QLA_Migration/Output/`
**Before snapshot:** `QLA_Migration/Archive/issue160_pre_remap/quikridr_pre_issue160.csv`
**Generated:** 2026-09-07
**Verdict:** **PASS**

---

## 0. Independence statement

This report is based on an independent re-verification (separate read-only tester pass), not a re-statement of the coder's own claims:

1. Read `app.py` and `QLA_Migration/app.py` directly at `_apply_pua_rider_inheritance` (not trusting Implementation Notes' quoted excerpt).
2. Read the validator's full source to confirm it independently re-derives expected values from the archive snapshot rather than trusting the remap script's own output — confirmed **not circular**.
3. Wrote a fresh, independently-coded Python join against `Output/quikridr.csv` to re-derive the 239/27/228 population counts from scratch.
4. Raw byte/line-ending inspection and SHA-256 hash comparison.

---

## 1. Commands Run

```text
python tools\validators\validate_issue160_pua_terminal_status.py
```
Plus independently-written ad hoc Python for population re-derivation, field-level diff vs archive, byte/line-ending inspection, SHA-256 hash compare, and trace-policy lookups.

---

## 2. Code Review — `_apply_pua_rider_inheritance`

Confirmed **identical** in both files. Quoted block (`app.py` lines 3631–3646, `QLA_Migration/app.py` lines 3630–3645 — byte-for-byte identical text):

```3631:3646:C:\Users\warren\Documents\GitHub\Warrenhughes1974\app.py
        base_status = self._quikridr_status_code_int(entry.get("MPHSTAT", ""))
        if base_status in (44, 45):
            # Issue #108D: base on ETI/RPU terminates every other coverage (spec 54).
            # Statuses 44/45 fall inside the Issue #60 "< 50" window but are not the
            # active base that rule was written for.
            row_data["MPHSTAT"] = "54"
        elif base_status < 50:
            row_data["MPHSTAT"] = "41"
        else:
            # Issue #160: PUA follows base phase's terminal status (e.g. 50 Suspended,
            # 53 Terminated/Death, 55 Surrendered, 57 Matured) instead of keeping its
            # own PPBEN-mapped status. Carve-out approved by Warren against SD-60-12
            # (Issue #60), which only addressed base < 50 and 44/45.
            base_mphstat_raw = self.normalize(entry.get("MPHSTAT", ""))
            if base_mphstat_raw:
                row_data["MPHSTAT"] = base_mphstat_raw
```

Confirmed the `44/45` and `<50` branches are untouched, the new `else` sits after both without intercepting them, and `MPAR`/`MPLAN`/`MEXPRY`/`MEFFDATE`/`MAGE`/`MPAYUP` (all set earlier in the function) were not touched.

`APP_VERSION` confirmed `"v59.09"` in both `app.py:644` and `QLA_Migration/app.py:643`.

---

## 3. Validator Source Review (circularity check)

The validator loads `Output/quikridr.csv` **and** the archive snapshot independently from disk, re-derives base phase-1 status per policy from the current file itself, and separately re-derives per-row expected value for each of the three buckets. It cross-checks every non-`MPHSTAT` column between archive and current, keyed by `MPOLICY`+`MPHASE`. **Not circular** — an independent third implementation (this report) reproduces its exact numbers.

### Validator raw stdout (final run, after line-ending fix — see §9)

```text
Issue #160 PUA terminal status validator
quikridr rows=6956
archive rows=6956
  OK: row count unchanged (6956)
  OK: terminal-base PUA MPHSTAT matches base raw (239 rows)
  OK: base 44/45 PUA MPHSTAT=54 (27 rows)
  OK: base <50 PUA MPHSTAT=41 (228 rows)
  OK: non-MPHSTAT columns identical to archive (6956 rows compared)
RESULT: PASS
```
Exit code: **0**

---

## 4. Independent Population Re-derivation

| Bucket | Expected (claimed) | Independent count | Match? | Mismatches |
|---|---:|---:|---|---:|
| Terminal (base ≥50, not 44/45) → PUA = base raw MPHSTAT | 239 | **239** | Yes | **0** |
| — by base status | 50:1, 53:163, 55:71, 57:4 | **50:1, 53:163, 55:71, 57:4** | Yes | — |
| Base 44/45 → PUA = 54 | 27 | **27** | Yes | **0** |
| Base <50 → PUA = 41 | 228 | **228** | Yes | **0** |
| Total quikridr rows | 6,956 | **6,956** (current and archive) | Yes | — |

Non-MPHSTAT field-level drift check (all 39 other columns, keyed `MPOLICY+MPHASE`, all 6,956 rows): **0 drift events, 0 key mismatches.**

---

## 5. Byte-diff Spot Check (8 policies across base 50/53/55/57)

| Policy | MPHASE | Base status | PUA MPLAN | Column(s) changed |
|---|---|---|---|---|
| 9010521213C | 2 | 50 | 1708PA | MPHSTAT only (22→50) |
| 9010150910C | 3 | 53 | 221EPA | MPHSTAT only (56→53) |
| 9010363098C | 5 | 53 | 1960PA | MPHSTAT only (56→53) |
| 9010360289C | 2 | 55 | 1708PA | MPHSTAT only (56→55) |
| 9010360290C | 2 | 55 | 1708PA | MPHSTAT only (56→55) |
| 9010235370C | 2 | 57 | 280EPA | MPHSTAT only (56→57) |
| 9010378485C | 2 | 57 | 1960PA | MPHSTAT only (56→57) |

`MSAVESTAT` (independent snapshot field) confirmed **unchanged** on all sampled rows — correctly not touched by this fix, same as `MSAVEAGE`/`MSAVEUNIT`.

---

## 6. Regression Check — Other Output Tables

| File | Touched by this fix? |
|---|---|
| `quikridr.csv` + `Test_Validation/quikridr.csv` | Yes — expected |
| `quikmstr.csv`, `quikplan.csv`, `quikclnt.csv`, `quikbenf.csv` | **No** — mtimes predate this change |

---

## 7. Trace Policy Results

| Policy | Base MPHSTAT (before→after) | PUA MPLAN | PUA MPHSTAT (before→after) | Result |
|---|---|---|---|---|
| 9010360289C | 55→55 | 1708PA | 56→55 | PASS |
| 9010367705C | 55→55 | 1708PA | 56→55 | PASS |
| 9010376522C | 55→55 | 1960PA | 56→55 | PASS |
| 9010379405C | 55→55 | 1960PA | 56→55 | PASS |
| 9010391228C | 55→55 | 1970PA | 56→55 | PASS |
| 9010521213C | 50→50 | 1708PA | 22→50 | PASS |

**Note on 9010521213C:** base=50 (Suspended/Death Claim Pending) — the same defect class previously flagged only in the **Issue #133 discovery notes** (never formally fixed there). The approved broader scope for #160 (all terminal statuses ≥50, not just 55) resolves this policy's PUA status as a side effect. No #133 artifact was modified; this is purely a consequence of #160 now covering base=50 too.

---

## 8. Test_Validation Publish Check

Confirmed `Output/Test_Validation/quikridr.csv` is byte-identical (SHA-256 match) to `Output/quikridr.csv` after the line-ending fix in §9.

---

## 9. Findings — raised during independent review, both resolved before this report was finalized

### Finding 1 — Line-ending convention (RESOLVED)
The remap script wrote `quikridr.csv` with LF-only line endings, while the rest of `Output/` (and the pre-fix archive snapshot) uses CRLF. Field values were unaffected (0 drift, confirmed in §4), but this was a real, undisclosed byte-level inconsistency. **Fixed:** normalized `Output/quikridr.csv` back to CRLF (matching the rest of the package) and re-synced `Test_Validation/quikridr.csv`. Validator re-run after the fix — still **PASS** (§3 stdout is the post-fix run).

### Finding 2 — Written approval record (RESOLVED)
Discovery/Planning/Risk/Dependency Gate all scoped this to base=55 only pending written Warren approval to broaden further. Warren's approval (both the SD-60-12 carve-out and the "fix all" scope) was given in chat on 2026-09-07 but had not yet been recorded in the repo. **Fixed:** added **SD-60-13** to `Issue_Log_Items/Issue_60/Issue_60_Scope_Decisions.md` documenting the approval and scope, and updated `Issue_160_Tracking_Sheet_Row.tsv` Notes accordingly.

---

## 10. Overall Verdict

**PASS** — code identity confirmed in both `app.py` files, version bump confirmed, validator PASSes independently, population counts (239/27/228) independently re-derived with zero mismatches, byte-diff spot checks confirm only `MPHSTAT` changed at the field-value level, no other Output table touched, trace policies confirmed, Test_Validation copy confirmed identical. Both findings from the independent review (line-ending drift, missing written approval record) have been corrected.

**Status: Ready for Regression.**
