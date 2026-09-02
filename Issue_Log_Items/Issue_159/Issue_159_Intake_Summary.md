# Issue #159 — Intake Summary

**Issue:** #159 — L10/L14 traditional-life reserves at $0 (UW key mismatch)  
**Framework stage:** Intake Agent (G0)  
**Status recommendation:** Intake Complete → Planning → Dependency Gate → Risk  
**Generated:** 2026-09-02  
**Owner:** Conversion  
**Priority:** Go-No Go — Traditional Life valuation is $2.87M low; $2.53M of the $0-reserve bucket sits on three plans

---

## Client symptom (verbatim)

Traditional life (LOB = L): QLAdmin is $2.87M LOW. Driver is 608 matched rows where QLA reserve is exactly $0.00 but LifePRO has a reserve, totalling $2,909,627. Concentrated in `1L1095` (L10 LP95), `1L10OD` (L10 PRE97), and `1L14SC` (L14). Client states these were matching before and are not matching now.

## Symptom (normalized)

QLAdmin CSO valuation does not attach the loaded TV/NP rate file on those policies, so `MRESERVE` is $0. Policy `MUWCLASS` no longer matches the rate-file `UWCLASS` key. Rate tables are present and non-zero. This is a #118 emit regression, not a missing-rate extract.

## Example policies

| Policy | Plan | LifePRO letter (#118 UAT) | Required MUWCLASS | Current MUWCLASS |
|---|---|---|---|---|
| 9011189929C | 1L1095 | B | BL | BL (still correct) |
| 9011190516C | 1L1095 | S | SM | **ST** |
| 9011193156C | 1L1095 | P | PR | PR (still correct) |
| 9011206462C | 1L14SC | N | NT | **00** |
| 9011208194C | 1L14SC | T | ST | **00** |
| 9011207210C | 1L14SC | Q | PQ | **00** |

Zero-reserve QuikValf join (2026-06-30 compare): 157 `1L1095` all ST ($1,111,309); 30 `1L10OD` all ST ($236,667); 108 `1L14SC` all 00 ($1,184,340).

## Suspected domain

Policy / rider underwriting class — `quikridr.MUWCLASS`. Converter path: PPBEN `UNDERWRITING_CLASS` via `Sync_Rulebook_quikridr.csv`, then `map_rider_uwclass` in `app.py`.

## In scope (first pass)

- Pass `plan=` into `map_rider_uwclass` in both `app.py` copies
- Re-emit `quikridr` from LifePRO letters (not from already-mapped MUWCLASS)
- Fail-closed validator on #118 UAT anchors + L10 S must not emit ST
- Publish `Output/Test_Validation/quikridr.csv` on PASS

## Out of scope (first pass)

- Inventing L14 PQ/ST/PR TV/NP grids (source is N-only; #118 known gap)
- Issue #107 / PSUBSSEG LP95 vs LP9595 (dollar variance on BL/PR that already calculate)
- PVO / `PLANVALOPT` / `GDVARYTV` (already Y; Closed #96/#136)
- Band keys (Closed #71)
- QuikValf itself (moves after CSO reloads riders and revalues)
- Non-L10 `S→ST` (correct per the form sheet; e.g. `5L0110`)

## Related issues

| Issue | Relationship |
|---|---|
| #118 | Parent remap. Still Eric-approval pending. #159 owns the durable `app.py` wiring. |
| #107 | Out of scope |
| #59 / #96 / #136 / #71 / #157 / #158 | Closed or adjacent; do not reopen |

## Immediate blockers

None for Intake. PPBEN letters for the UAT anchors are already on file in #118. Source extract is used at batch time via the existing rulebook.

## Artifact inventory

| Have | Missing |
|---|---|
| Valuation compare + tier-2 exceptions | New Eric screenshots (not required) |
| Current `quikridr` / QuikTvs / QuikPlTv | — |
| #118 UAT letters and post-remap inventory (SM 216 / L14 NT 101 PQ 111 PR 13 ST 7) | — |
| Rulebook `UNDERWRITING_CLASS → MUWCLASS` | — |

## Owner / priority

Conversion. Go-No Go. No client data request.
