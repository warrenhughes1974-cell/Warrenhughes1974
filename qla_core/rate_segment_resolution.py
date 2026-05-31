"""
LifePRO segment resolution for rate loading.

Business chain (PAAGERAT policy premium rates):
  PAAGERAT.COVERAGE_ID  =  PCOVRSGT.SEGT_ID   (segment ID, NOT policy form)
  PCOVRSGT.COVERAGE_ID  =  PCOVR.COVERAGE_ID  (parent coverage)
  Policy Form Crosswalk :  parent COVERAGE_ID -> authoritative QLAdmin PLAN

Rate_Table_Extract uses parent-style COVERAGE_ID values and may resolve DIRECTLY
via crosswalk. PAAGERAT must always use the segment chain first.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass


@dataclass(frozen=True)
class SegmentResolution:
    """Result of PAAGERAT segment -> parent coverage -> PCOVR enrichment."""
    source_segment_id: str
    parent_coverage_id: str
    plan: str
    resolution_path: str  # SEGMENT | DIRECT
    pcovr_description: str = ""
    pcovr_policy_form: str = ""
    pcovr_status: str = ""


class SegmentResolver:
    """Loads PCOVRSGT + PCOVR and resolves segment IDs to authoritative PLANs."""

    def __init__(self, segt_to_parent: dict, pcovr_by_id: dict, cov2plan: dict):
        self._segt_to_parent = segt_to_parent
        self._pcovr = pcovr_by_id
        self._cov2plan = cov2plan

    @classmethod
    def from_files(cls, pcovrsgt_csv: str, pcovr_csv: str, cov2plan: dict):
        return cls(load_pcovrsgt(pcovrsgt_csv), load_pcovr(pcovr_csv), cov2plan)

    def parent_coverage(self, segment_id: str) -> str | None:
        """PCOVRSGT lookup: SEGT_ID -> parent COVERAGE_ID (SEGT_FLAG=Y rows only)."""
        return self._segt_to_parent.get((segment_id or "").strip())

    def resolve(self, coverage_or_segment_id: str, *, source: str = "paagerat") -> SegmentResolution | None:
        """
        Resolve a source identifier to authoritative PLAN.

        source='paagerat'  -> segment chain required (SEGT_ID -> parent -> crosswalk)
        source='rate_table' -> direct crosswalk first, then segment fallback
        """
        cid = (coverage_or_segment_id or "").strip()
        if not cid:
            return None

        if source == "rate_table":
            if cid in self._cov2plan:
                meta = self._pcovr.get(cid, {})
                return SegmentResolution(
                    source_segment_id=cid,
                    parent_coverage_id=cid,
                    plan=self._cov2plan[cid],
                    resolution_path="DIRECT",
                    pcovr_description=meta.get("description", ""),
                    pcovr_policy_form=meta.get("policy_form", ""),
                    pcovr_status=meta.get("status", ""),
                )
            parent = self.parent_coverage(cid)
            if parent and parent in self._cov2plan:
                meta = self._pcovr.get(parent, {})
                return SegmentResolution(
                    source_segment_id=cid,
                    parent_coverage_id=parent,
                    plan=self._cov2plan[parent],
                    resolution_path="SEGMENT",
                    pcovr_description=meta.get("description", ""),
                    pcovr_policy_form=meta.get("policy_form", ""),
                    pcovr_status=meta.get("status", ""),
                )
            return None

        # PAAGERAT: COVERAGE_ID is always treated as SEGT_ID
        parent = self.parent_coverage(cid)
        if not parent:
            return None
        plan = self._cov2plan.get(parent)
        if not plan:
            return None
        meta = self._pcovr.get(parent, {})
        return SegmentResolution(
            source_segment_id=cid,
            parent_coverage_id=parent,
            plan=plan,
            resolution_path="SEGMENT",
            pcovr_description=meta.get("description", ""),
            pcovr_policy_form=meta.get("policy_form", ""),
            pcovr_status=meta.get("status", ""),
        )


def load_pcovrsgt(path: str) -> dict:
    """
    Return SEGT_ID -> parent COVERAGE_ID for segment rows (SEGT_FLAG = Y).
    """
    segt_to_parent = {}
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        si = hdr.index("SEGT_ID")
        ci = hdr.index("COVERAGE_ID")
        sf = hdr.index("SEGT_FLAG")
        for row in rd:
            if len(row) <= max(si, ci, sf):
                continue
            if row[sf].strip() != "Y":
                continue
            segt = row[si].strip()
            parent = row[ci].strip()
            if segt:
                segt_to_parent[segt] = parent
    return segt_to_parent


def load_pcovr(path: str) -> dict:
    """Return COVERAGE_ID -> {description, policy_form, status}."""
    out = {}
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        rd = csv.reader(f)
        hdr = [c.strip() for c in next(rd)]
        ci = hdr.index("COVERAGE_ID")
        di = hdr.index("DESCRIPTION") if "DESCRIPTION" in hdr else None
        pi = hdr.index("POLICY_FORM_NUM") if "POLICY_FORM_NUM" in hdr else None
        si = hdr.index("STATUS_CODE") if "STATUS_CODE" in hdr else None
        for row in rd:
            if len(row) <= ci:
                continue
            cov = row[ci].strip()
            if not cov or cov.startswith("-"):
                continue
            out[cov] = {
                "description": row[di].strip() if di is not None and di < len(row) else "",
                "policy_form": row[pi].strip() if pi is not None and pi < len(row) else "",
                "status": row[si].strip() if si is not None and si < len(row) else "",
            }
    return out
