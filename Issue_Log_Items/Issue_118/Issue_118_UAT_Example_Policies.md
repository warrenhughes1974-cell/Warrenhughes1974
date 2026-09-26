# Issue #118 — UAT Example Policies

**Recorded:** 2026-08-08  
**Purpose:** Screen-proof anchors after the UW remap ships. No code changes in this note.

Source of truth for letter→code: **Underwriting Classes by Form** + Eric L14 map (Clarification §1 / §5).

| Scenario | Form / plan | Policy | LifePRO letter (today) | Target QLA class | Why it proves the fix |
|----------|-------------|--------|------------------------|------------------|------------------------|
| L10 Blended | L10 LP95 / `1L1095` | `9011189929C` | `B` | **BL** | Today wrongly `ST`; sheet wants Blended |
| L10 Smoker | L10 LP95 / `1L1095` | `9011190516C` | `S` | **SM** | S = Smoker on L10 |
| L10 Preferred | L10 LP95 / `1L1095` | `9011193156C` | `P` | **PR** | Preferred unchanged |
| Preferred/Standard form — S means Standard | L01 10Y LT / `5L0110` | `9011059291C` | `S` | **ST** | Today wrongly `SM` |
| Preferred/Standard form — Preferred | L01 10Y LT / `5L0110` | `9011052719C` | `P` | **PR** | Preferred unchanged |
| L14 Non-Tobacco | L14 / `1L14SC` | `9011206462C` | `N` | **NT** | Today `NS` |
| L14 Standard | L14 / `1L14SC` | `9011208194C` | `T` | **ST** | Today orphan `T` |
| L14 Pref Non-Tobacco | L14 / `1L14SC` | `9011207210C` | `Q` | **PQ** | Today `NS`; L14-scoped |
| L14 Preferred | L14 / `1L14SC` | `9011215903C` | `R` | **PR** | Today orphan `R` |
| Class-0 / `00` = Standard | 670 GL85-8 / `170858` | `9010360290C` | `0` | **00** (descr Standard) | Keep code `00`; label Standard |
| ISWL ST/PR membership | 659 CEN II / `1659C2` | `9010713704C` | `P` (base) | **PR** | ISWL membership ST+PR per Eric |

**Known gap to show on L14 ST/PQ/PR (final report):** cash value / reserve tables exist for letter `N` only — do not invent CV for ST/PQ/PR.
