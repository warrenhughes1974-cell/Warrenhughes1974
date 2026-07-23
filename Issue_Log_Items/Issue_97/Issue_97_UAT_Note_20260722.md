# Issue #97 — UAT Note (2026-07-22)

**Policy:** 010398471C  
**Plan:** 17085M (Phase 1)  
**Author:** Warren  
**Status:** Fee confirmed present in latest ShareFile package and in local QLAdmin

---

## Finding

Latest ShareFile / conversion Output already contains the annual policy fee for this policy. Local QLAdmin (Editing Phase 1 / Coverage) shows **Policy Fee = 10.4400**, matching Eric’s expected $10.44.

Related values on the same policy in QLAdmin:

| Item | Value |
|------|-------|
| Policy Fee (Phase 1) | 10.4400 |
| Mode | 12 |
| Mode Prem | 120.00 |
| Mode factors SA / Q | 52.0000 / 26.5000 |
| Expected Names-tab S / Q / M | 62.40 / 31.80 / 10.80 (consistent with factors + fee) |

## QLAdmin storage

| UI label | Table | Field | Notes |
|----------|-------|-------|-------|
| Policy Fee (coverage / phase edit) | **quikridr** | **MANNLFEE** | Base phase only; from LifePRO `POLICY_FEE` |
| Mode factors (Base Data) | quikmstr | MSEMI / MQTRL / MMTHD / MMTHB | Copied from plan factors (#36) |
| Mode Prem | quikmstr | MMODEPREM | From LifePRO `MODE_PREMIUM` |

Plan form `ANNLFEE` / related *FEE columns remain 0 by design. Fee is on the coverage (`quikridr`), not plan setup.

## Ask of Eric

Reload latest ShareFile package (`quikridr`, `quikmstr`, `quikmemo`) and recheck Phase 1 Policy Fee on 010398471C. If still $0, send screenshot of the screen in use.

## Related issues

#21C (MANNLFEE), #36 (policy factors), #58 (modal fees for Names tab), #89 (fee wipe on ridr-only rebatch), #50 (memo SEEK).

## Framework

Pre-Dev chain complete (Intake → Risk). Risk recommendation remains verify/reload track — no formula code change unless post-reload failure is proven.
