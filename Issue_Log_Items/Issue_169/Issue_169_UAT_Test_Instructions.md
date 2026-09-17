# Issue #169 — 667 ART reserves — UAT test package

## What's in the package

| Table | Why it's here |
|---|---|
| `QuikNps.dbf` | **The fix.** 1,736 new net-premium rows for plan `5667AT` (667 ART), which previously had none. |
| `QuikPlTv.dbf` | 4 new key rows for `5667AT`. Without these the net premium grid is ignored and the reserve still values 0. |
| `QuikTvs`, `QuikCvs`, `QuikNff`, `QuikPlCv`, `QuikPlDb`, `QuikPlDv` | Unchanged by this fix, included so the rate set stays internally consistent with the L14 set already loaded. |

Nothing else changed. `quikplan` and all policy tables (`quikmstr`, `quikridr`, etc.) are
**not** part of this package and do not need reloading.

## Important — the reserve is not in these tables

QLAdmin calculates the reserve at valuation time from the net premium grid. Loading the
tables on their own will not show any change. **A valuation has to run** before anything is
testable.

## How to test

1. Reload the rate tables from this package.
2. Run a valuation as of **8/31/2026**.
3. Pull the reserve for plan **667 ART (form 1595)** and compare to the anchors below.

Every one of these policies reserved **$0.00** before the fix.

| QL policy | Units | Expected reserve |
|---|---:|---:|
| `9010800356C` | 200 | $8,239.00 |
| `9010837136C` | 200 | $6,954.00 |
| `9010816232C` | 100 | $6,312.50 |
| `9010844919C` | 100 | $4,855.00 |
| `9010777321C` | 200 | $4,285.00 |
| `9010773561C` | 100 | $3,790.50 |
| `9010768802C` | 30 | $490.35 |
| `9010764248C` | 50 | $474.50 |
| `9010764158C` | 25 | $181.87 |

**Plan total to expect: about $132,229** across the 95 records that carry units.

The full 96-record list with expected amounts is in `Issue_169_UAT_Test_Anchors.csv`.

## One record that will not match

Policy `9010886099C`, second coverage, carries a **$1,317.00** reserve in LifePRO against
**zero units**. A per-unit rate table cannot reproduce a reserve on zero units, so this one
is expected to stay at $0 and is being tracked as a separate question. Please don't treat it
as a failure of this fix.

## Still outstanding on Issue 169

These are **not** addressed by this package and are waiting on input:

| Form | LifePRO | QL | Waiting on |
|---|---:|---:|---|
| 619 SPS PU | $90.47 | $0.00 | CSO — no valuation setup row (no mortality table, reserve interest, or reserve method) |
| 1596 L01 | $261.45 | $98.00 | CSO — same |
| 1596 | $54.00 | $25.00 | CSO — same |
| 960 LP85-M | $1,858.42 | $0.00 | Actuarial — LifePRO stores only 12 durations, the policy is at duration 57 |
| 1595 WP / SAL ADB / 1596 667 | $0.00 | $104.00 | Jill — LifePRO reserves nothing on these; confirm whether any reserve is expected |
