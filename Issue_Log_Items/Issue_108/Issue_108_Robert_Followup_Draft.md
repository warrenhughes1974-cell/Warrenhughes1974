# Issue #108 — Follow-up email to Robert (draft 4, direct questions with examples)

**Date:** 2026-07-25
**To:** Robert De Sarro
**Re:** Conversion - Statuses, NFO
**Assumes:** the first reply (`Issue_108_Robert_Reply_Draft.md`) already went out

All policy numbers and values verified against `QLA_Migration/Output/` at app v58.34.

---

Robert,

Update on the ETI/RPU work. Everything I flagged is fixed and validated. MAGE is the attained
age at the paid-to date now on all 400 ETI and RPU policies, duration comes off the
anniversary, ETI premium is zeroed, the save fields are blank on 44 and 45, and the 27 paid up
additions that were sitting at 41 are terminated at 54. MNFOPT is populated again.

Cash values and reserves will move on those 400 policies now that the age is right. I will be
updating the data in your folder soon so you can look at it there. I want to send you the
before and after before we reload anything.

I also moved your four checks into the data governance program so the converter is not forcing
statuses. They run on every conversion now.

I have six questions. Each one has a policy you can pull up.

1. Is the SAL ML structure right? 9014059C, RPU. Phase 1 is 1SALML with 0.00000 units at status
45. Phase 2 is 1SALMI with 0.60400 units at status 22. All the insurance is on phase 2 and the
base has nothing. There are 77 RPU policies like this. If I terminate phase 2 the way the rule
reads I zero out the entire in force amount on all 77.

2. Should these riders be terminated? 9010820645C, ETI at 44. Phase 1 is 5667AT at 44 and phase
2 is 9595WP waiver still at 22. Same setup on 9011001302C and 9011136641C. On 9010779553C the
waiver is terminated at 56 but the accidental death 967ADB is still at 22 on the same policy,
which is why I think it is a source problem. Should all four be 54?

3. Does the base already have the PUA in it? 9010391355C, ETI at 44. Base 17085M is 13.71152
units and the PUA 1708PA is 4.29952. Should the base become 18.01104, or is 13.71152 already
the combined number from LifePRO? I do not want to add it twice.

4. Were these expiries ever recalculated? 9010764158C, ETI, paid-to 09/09/2026, DOB 12/30/1965,
expiry 09/09/2066. That is attained age 100. 92 of the 206 ETI policies look like that. It
reads like the original maturity date, not a calculated ETI expiry.

5. Is a blank election OK on an NFO policy? 9010768802C is ETI at 44 with MNFOPT 0 because
there is no election in the source at all. 166 of the 400 are like that. Separately 9010165095C
is RPU at 45 but the source election is 2 for ETI, and there are 111 of those. Do you want the
166 defaulted off the status or left blank?

6. Should RPU keep a premium? 9010732975C, RPU at 45, plan 1659C2, MPREM 9.858156. Your write
up zeroes MPREM on ETI but the RPU section does not mention it and your RPU example keeps it at
9.96. 63 of our RPU policies still carry one. Is that intentional?

Warren
