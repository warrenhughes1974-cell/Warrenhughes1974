# Issue #108 — Reply to Robert (draft)

**Date:** 2026-07-25
**To:** Robert De Sarro
**Re:** Conversion - Statuses, NFO

---

Robert,

Thanks for this, the ETI/RPU write-up and the two example workbooks were exactly what I needed. I went through our conversion against them and here's where we stand.

Agree on the architecture. We do have a crosswalk driving the status codes and it's getting 44 and 45 right, but we've also accumulated several places where the program forces statuses after the fact, and a couple of them are forcing the exact things you want checked. Phase 1 coverage status is forced to match the policy status, and MNFOPT is forced from the policy status, so two of your four checks can never fire on our output. I'm going to pull those back and move them into data governance where you wanted them.

I ran your four checks against our current output, 5,083 policies. Terminated policy with an in-force coverage came back clean, zero. Active policy with no in-force coverage, also zero. Phase 1 not matching the policy status is zero but only because we force it, so that one doesn't mean anything yet.

Phases 2+ still in force on an NFO policy found 109 rows, and this is the one I want to walk you through because it splits three ways.

27 of them are paid-up additions sitting at status 41 instead of 54. That's our bug - we have a rule that sets PUA to Paid Up whenever the base coverage is under 50, and 44 and 45 are under 50, so it catches ETI and RPU policies it shouldn't. Easy fix.

77 of them are the SAL ML block and I don't think they're wrong, I think they'd have been a disaster if I'd just applied the rule. On those policies the phase 1 base coverage has zero units and the actual face amount is sitting on the phase 2 rider. 147 of the 152 SAL ML policies look like that, and 77 of them are on RPU. If I terminated all the phase 2 coverages the way the rule says, I'd zero out the entire in-force amount on 77 RPU policies. So this is one for you - is that phase structure legitimate, base with no units and the insurance on phase 2, or is something wrong with how those got set up in the first place?

That leaves 5 rows on 4 policies that look like genuine leftovers. All four are plan 5667AT on ETI with waiver of premium and accidental death riders still active: 9010779553C, 9010820645C, 9011001302C, 9011136641C. One of them, 9010779553C, has the waiver terminated at 56 but the accidental death still at 22 on the same policy, which makes me think it's a source data problem rather than intentional. Can you check those against LifePRO?

On the NFO field set, the biggest thing I found is the age. MAGE on our phase 1 rows is the issue age, not the attained age at the paid-to date, on all 400 ETI and RPU policies. The gap averages about 25 years and the worst one is 55 years. Since we're leaving the cash values blank for QLAdmin to rebuild, that means the rebuild is running the net single premium at an age that's decades too young on the whole NFO book. I'm fixing that, but you should expect cash values and reserves to move on those 400 policies once it's in, and I'd like to send you the before and after before we reload anything.

Also fixing: the ETI premium isn't being zeroed out, that's 204 of the 206 ETI policies. And the duration is a year high on 167 of them because we were subtracting calendar years instead of going off the anniversary.

On the save fields, right now we're copying the current values into them, which is the worst of the three options you listed. On an ETI policy MSAVESTAT comes out as 44 and MSAVEUNIT is the post-NFO amount, so if anybody ever reinstated one of those in QLAdmin it would restore the policy right back into ETI. I'm going to blank them on 44 and 45 like you suggested. I'll check with Greg but blank seems clearly better than what we have.

A few things I need from you or the source system:

For a policy that's already on ETI or RPU in LifePRO, does the base coverage NUMBER_OF_UNITS already have the PUA folded in? Your ETI example adds them, 4.976 plus 4.25349 gives 9.22949. But if LifePRO already did that before we extracted, I'd be adding it twice. Take 9010391355C, base 17085M at 13.71152 with a PUA at 4.29952 - is 13.71152 already the combined figure or not?

Your write-up has ETI setting MPREM to 0.00 but the RPU section doesn't mention it, and your RPU example keeps it at 9.96. Is that intentional? A fully paid-up policy still carrying a premium per unit seems odd to me but I don't want to guess.

92 of our 206 ETI policies have an expiry date that works out to attained age 95 or older, which looks like the original maturity date rather than a calculated ETI expiry. The other 114 are under 90 and look right. We pass the expiry straight through from LifePRO so I don't think we're breaking it, but can you check whether those 92 ever got recalculated on the source side?

Last thing, minor - your document refers to MCVO but the field in the table is MCV0 with a zero. Just flagging it so nobody chases the wrong field.

One other thing I noticed while I was in there. Our MNFOPT is empty on almost everything. 4,346 policies have a real non-forfeiture election in the source and we're writing zero for nearly all of them, including 1,933 policies that are still in force. Turned out to be a key mismatch on our side from a change we made a couple days ago, not a data problem. Fixing that as part of this. Once it's populated your check comparing MNFOPT against the policy status will actually mean something - right now I can already see 111 NFO policies where the source election doesn't match the status, so we'll have some to go through.

Warren
