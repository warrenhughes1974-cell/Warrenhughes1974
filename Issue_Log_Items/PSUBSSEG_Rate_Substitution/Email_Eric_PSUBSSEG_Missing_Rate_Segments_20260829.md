# Email draft — missing rate segments behind the substitution tables

**To:** Eric
**Subject:** Substitution tables from New Era — need rates for a few more segment IDs

---

Eric,

We worked through the substitution files New Era provided (PSUBS / PSUBSSEG / PCONT) and they line up with what we suspected on several of the reserve questions. Short version: for policies issued on or after certain dates, LifePRO doesn't use the plan's own reserve and net premium segments — it substitutes a different segment ID, usually the 1995-basis version.

The catch is that a dozen of those substituted segment IDs don't appear anywhere in the PAAGE / PDAGE / rate table extracts we have, so we can't load the right rates for the affected policies yet. Could New Era pull the attained age and age/duration rate rows for these segment IDs?

- L01 10Y 95
- L05 10Y 95
- L07 5Y 95
- L10 CDT 95
- 619 DT 95
- 619DTCH95
- 619DTSP95
- 619CHPU95
- 619SPPU95
- 670 GL858
- 670GL858NL
- 991 PWL73
- 667 ART 95 (we have its reserves in PDAGE but not its net premiums)

These cover roughly 350 policies, mostly the 1995-and-later issues on the L01/L05/L07 term plans, the 619 decreasing term family, the 670 GL85 plans, and L10 CDT. It also looks like this explains the "zero reserve" readings we were seeing on L01/L05/L07 — the reserves aren't zero, they just live on segment IDs that weren't in the extract. (667 ART is the exception: its 95-era reserve segment is in the extract and really is all zeros, which makes sense for ART.)

Thanks,
Warren
