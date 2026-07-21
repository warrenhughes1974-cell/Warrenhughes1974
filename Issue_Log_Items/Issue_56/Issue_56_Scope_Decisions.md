# Issue #56 — Scope Decisions

**Issue:** #56 — PUA CV is incorrect  
**Updated:** 2026-07-14 (Slack + Eric answers)  
**Model:** Cursor Grok 4.5 (locked)

---

## Client / project decisions

| ID | Decision | Date | Source |
|----|----------|------|--------|
| **SD-1** | PUA riders use QLAdmin plan **`1960PA`** (first four of base + `PA`) — not catalog `1POPUA` | 2026-07-14 | Warren / conversion pattern |
| **SD-2** | PUA CV rates = LifePRO attained-age **`960 PO PUA` / CV`** (PAAGE/PAAGERAT) | 2026-07-14 | Rate file + extract |
| **SD-3** | PUA **must have its own CV** (not follow base) — confirmed per **policy forms** | 2026-07-14 | Eric via Warren (Slack) |
| **SD-4** | New Era: if PA has own rates → **add PA plan to plan files** and load **full CV + TV + basis**; if PA omitted from plan file, QLA uses **base** | 2026-07-14 | Robert (Slack) |
| **SD-5** | Pilot first on one PA plan (`1960PA` / `010310404C`) per Robert’s Build-CV test path | 2026-07-14 | Robert |

---

## Impact on prior Risk recommendation

| Prior option | Status |
|--------------|--------|
| **Option B** (remap to `1POPUA`) | **Withdrawn** |
| **Option C** (omit PA plan → inherit base CV) | **Reject** — conflicts with SD-3/SD-4 |
| **Option A** (keep `1960PA`; add plan + own QuikCvs/QuikTvs) | **Confirmed** by New Era + Eric |

---

## Critical caveat — `1960PA` shared by four LifePRO PUA products

| LifePRO PUA plan | Ridr rows on `1960PA` | Own PAAGERAT CV? |
|------------------|----------------------:|------------------|
| `960 PO PUA` (Eric) | **22** | Yes |
| `960 OL PUA` | 32 | Yes (different) |
| `960 65 PUA` | 16 | Yes (different) |
| `960 LP PUA` | 1 | Yes (different) |

**SD-6 (pilot scope):** Issue #56 Development = **`1960PA` + `960 PO PUA` CV/TV** first (A1). OL/65/LP residual until separate plan codes or separate issue.

---

## Still needed before / during Development

1. LifePRO correct PUA CV **$** on `010310404C` (nice for acceptance; Robert’s Build-CV delta test can prove rate attachment even without exact $)  
2. Explicit **Approved for Development** → **Composer 2.5**  
3. Confirm TV source for `960 PO PUA` in extracts (PAAGERAT TYPE or Rate_Table) during Dev  

---

## Development direction (awaiting approval — do not implement yet)

1. Keep `_apply_pua_rider_inheritance` → `1960PA`.  
2. Add **`1960PA`** to plan emit (`quikplan` + required plan basis / QuikPl* pointers).  
3. Emit **QuikCvs + QuikTvs** (and basis) for `1960PA` from LifePRO **`960 PO PUA`** — not a silent copy of `1960PO` for production (copy-base only as Robert’s optional UAT step 1).  
4. Do not change base `1960PO` rates.  
5. Validate on `010310404C` with Build CV tool path Robert described.  

Detail: `Issue_56_New_Era_Slack_Answers_20260714.md`
