# Issue #174 — Discovery Notes

**Issue:** #174 — Pending Death Benefit Policies
**Framework stage:** Discovery
**Date:** 2026-09-28
**Raised by:** Eric (sheet, 2026-09-25); diagnosed by Brianna
**Code changes:** None

---

## 1. Client ask

Sheet:

> Policies in Pending Death Benefit status are not calculating return of premium or allowing edits to items such as beneficiaries.

Brianna, on `9011085655C`:

> This policy is in a pending death status (50) but so is the phase of coverage. The user is not able to make any edits to the policy like edit the beneficiary because they are receiving this error about the policy status not in sync with the coverage status. However, they are in sync, policy and phase is status 50.
>
> Normally, when a policy is in a pending death status the phase status remains active (22). This is an example of where I added a pending claim and you can see the phases status is still set to 22.
>
> I'm also able to edit the beneficiary while the policy is in pending death.
>
> These pending death policies need to be looked at to make sure the policy is converted over with an active phase of coverage.

**Normalized:** Policy header stays Death Claim Pending (50). Coverage phase stays Active (22). QLAdmin then allows beneficiary edits. Return of premium is on Eric's sheet and is not in Brianna's note; no separate return-of-premium load field was found. Treat it as a QLAdmin calculation that depends on the phase staying active until Brianna says otherwise.

## 2. What the example actually is

`9011085655C` — Century SR interest-sensitive whole life, plan `1659CR`.

| Layer | Value | Where |
|---|---|---|
| LifePRO contract | `S` / `DP` | 8/31 fund population file, `issue155_fund_population_20260831.csv` |
| LifePRO base benefit | `A` (Active) | same file, `BASE_STATUS` |
| `quikmstr.MSTATUS` | **50** | current `QLA_Migration/Output/quikmstr.csv` |
| `quikridr` phase 1 `MPHSTAT` | **50** | current `Output/quikridr.csv` |
| `MSAVESTAT` | **50** | same row; it mirrors `MPHSTAT` |

LifePRO did not move the benefit off Active. Conversion copied the policy status onto the phase.

## 3. Why the phase becomes 50

After the policy status is translated (`ST_S_DP` → 50), phase 1 inherits any policy status that is not blank, 11, 22, or the word ACTIVE:

```9813:9818:QLA_Migration/app.py
                            # Prefer Issue #13 provisional status so #49 QuikMstr override does not change phase 1
                            _prov_map = getattr(self, "_mstatus_provisional_for_phase1_cache", None) or {}
                            qm_status = _prov_map.get(tp) or self._qm_status_cache.get(tp)
                            # Inherit meaningful policy-level terminal status; block active statuses
                            if qm_status and qm_status not in ["", "11", "22", "ACTIVE"]:
                                row_data['MPHSTAT'] = qm_status
```

Status 50 is inside that copy. The rider rulebook would have left the phase at the benefit's own Active code. The inherit overwrites it. The same block exists in root `app.py`.

## 4. Current Output population

Every policy whose header is 50 also has phase 1 at 50. Sixteen policies:

| Policy | Phase 1 plan | Other phases |
|---|---|---|
| 9010521213C | 17085M | phase 2 PUA `1708PA` also 50 |
| 9010741334C | 1659C2 | |
| 9010772919C | 1659C2 | |
| 9010797197C | 1658C1 | |
| 9010835310C | 1659CR | |
| 9010841124C | 1659CR | |
| 9011085270C | 5L0110 | |
| 9011085655C | 1659CR | Brianna's example |
| 9011112998C | 1L10SO | |
| 9011176240C | 1L10SO | |
| 9011177866C | 1L10SO | |
| 9011190416C | 1L10SR | |
| 9011194146C | 1L10SO | |
| 9011248017C | 1L14SC | |
| 9011262791C | 1L14SC | |
| 9015000239C | 17CSI5 | |

On the 8/31 interest-sensitive fund file, `S`/`DP` policies that appear there still have base benefit status `A` (`9010772919`, `9010797197`, `9010803420`, `9010969653`, `9011085655`). `9010803420` and `9010969653` are not status 50 in the current Output package.

## 5. What must change, and what must not

**Must:** On Death Claim Pending, keep `quikmstr.MSTATUS` at 50 and leave the coverage phase Active (22), including `MSAVESTAT`. That is the shape Brianna produced by adding a pending claim herself.

**Must not:** Change surrendered, death, matured, or lapsed policies. Those phases should keep following the policy. This exception is status 50 only.

**Must not:** Let Issue #49 see the Active phase and put the header back to 22. That is the defect #59 (one policy) and #133-PS (PUA) were written to stop.

## 6. Closed-work conflict — do not code past this without Warren

Brianna's rule disagrees with two earlier decisions that treated 50 like every other terminal status:

| Prior work | What it did | Tension |
|---|---|---|
| Phase-1 inherit (above) | Copies 50 from the policy onto phase 1 | This is the direct cause |
| Closed #160 | PUA phase copies the base's terminal status, including 50 | `9010521213C` phase 2 is 50 because of this. If the base stays 22, #60 would set that PUA to Paid Up (41) instead |
| #133-PS (code shipped, not Closed) | Header stays 50 because the PUA is treated as terminal when the base is terminal | If the base is left at 22, that protection does not fire unless status 50 is special-cased on the contract |
| #108 | Terminated policy (≥50) terminates every coverage | Status 50 would be an exception |

Do not implement until Warren accepts that status 50 is an exception to #160 / #108 for the coverage phase, while the policy header stays 50.

## 7. Open questions

1. Return of premium: confirm with Brianna that it starts working once the phase is 22, and that there is no separate amount to load.
2. PUA on a pending-death policy (`9010521213C` phase 2): stay Active (22) with the base, or stay 50 under #160?
3. `9010439999C` was the #133-PS example (header pulled back to Active by an Active PUA). It is still header 22 / phase 1 22 / PUA 41 in current Output. Confirm whether that policy is still death-pending on the extract this package was built from.

## 8. Stop

Discovery only. Awaiting **Proceed to Intake**.
