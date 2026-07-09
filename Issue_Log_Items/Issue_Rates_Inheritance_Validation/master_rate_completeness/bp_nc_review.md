# BP / NC Review

Date: 2026-07-07

Source: `docs/Product (1).pdf`

## BP

Product Book section: `6.28 BP - Billable Premium Segment`.

Definition found:

> The BP - Billable Premium Segment directs LifePRO to the premium rates to use for non-flex UL products (fixed or EIWL).

The Product Book also notes that LifePRO uses billable premium logic with COI, interest, expenses, and rules to calculate the billable premium.

Current inventory status:

- Source: `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`
- Rows: 1,336
- Candidate QLAdmin destination already used for enabled BP rows: `QuikGps`
- Current status: present but not fully emitted because the BP loader is allowlist-gated.

Plain-English conclusion:

> BP means billable premium. We should not blindly load every BP row until we confirm which plans use BP as the premium authority, because some plans already use PR as the premium authority and loading both could duplicate or override premium rates.

## NC

Product Book section: `6.168 NC - Net Premium Credited Segment`.

Definition found:

> The NC - Net Premium Credited Segment is used to designate the total amount credited to the fund of a fixed premium UL. It is applicable to fixed premium UL coverages only.

Current inventory status:

- Source: `PAAGERAT_AttainedAge_Rates_Extract_20260428.csv`
- Rows: 690
- Confirmed QLAdmin destination: not yet confirmed in this inventory.

Plain-English conclusion:

> NC is not a normal gross premium, net valuation premium, reserve, cash value, or nonforfeiture factor. It is the amount credited to the fund for fixed premium UL. We need to confirm the QLAdmin table/field that expects this before loading it.

## Recommendation

Use `BP` only where QLAdmin/product rules confirm BP is the plan's gross premium authority. Keep `NC` out of the load until the destination is confirmed.
