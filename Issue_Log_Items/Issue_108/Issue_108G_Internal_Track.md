# Issue #108G — Internal track (not client-facing)

**Track:** **Internal only** — do **not** put this on the CSO / client issue log.  
**Parent:** Issue #108 (client tracks 108A–108F, 108H remain on the client log as applicable)  
**Owner:** Warren (request originated with Robert as architecture guidance)  
**Raised:** 2026-07-25  
**Status:** Active — Part 1 delivered; Part 2 remaining

## What this is

Internal **data-governance** work: cross-table status consistency checks (`DG-QUIKMSTR-027`–`032`), and a later Part 2 to retire in-program status forcing in the converter.

This is engineering / architecture hygiene, not a client UAT conversion defect row.

## Why it is internal

Robert’s ask was about *where* rules live (crosswalk + governance vs forcing in `app.py`). Part 1 added governance only — no `app.py` change, no version bump, no Output table change for the checks themselves. That belongs on the internal track with Issue A / #112, not the CSO numbered defect list.

## Status summary (2026-07-25)

| Part | Work | Status |
|------|------|--------|
| **1** | Six DG rules 027–032 (Robert’s four checks + election review + NFO field completeness) | **Delivered** — all PASS on current Output |
| **2** | Retire phase-1 `MPHSTAT` inherit and Issue #59 seven-policy allowlist | **Remaining** — needs 108E answered first, then its own release / batch / regression |

## Detail

Full write-up: [`Issue_108G_Implementation_Notes.md`](Issue_108G_Implementation_Notes.md)

## Do not

- Keep a **108G** row on the CSO Google Sheets issue log
- Treat Part 1 governance delivery as a client “Active / No-Go” conversion issue

## Related client tracks (stay on CSO log as needed)

- **108E** — riders in force on NFO (client/SME clarification) — gates Part 2
- **108H** — NFO election vs status (client decision)
- **108A–108D, 108F** — already closed conversion fixes
