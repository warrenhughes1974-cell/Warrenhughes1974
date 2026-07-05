"""Shared lookups for Phase 1 reinsurance conversion."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from qla_core.normalize_utils import format_qladmin_mpolicy
from qla_core.reinsurance_source_loader import _normalize_benefit_seq, _s, read_lifepro_csv


def load_reinsurer_crosswalk(path: str | None = None) -> dict[str, dict[str, str]]:
    crosswalk_path = path or os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "plan_governance", "config", "reinsurer_crosswalk.csv")
    )
    if not os.path.isfile(crosswalk_path):
        return {}
    df = pd.read_csv(crosswalk_path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip().upper() for c in df.columns]
    out: dict[str, dict[str, str]] = {}
    for _, row in df.iterrows():
        treaty = _s(row.get("TREATY_CODE", ""))
        if not treaty:
            continue
        out[treaty.upper()] = {
            "TREATY_CODE": treaty,
            "MREINCO": _s(row.get("MREINCO", "")),
            "MREINNAME": _s(row.get("MREINNAME", "")),
            "REINSURER_NAME": _s(row.get("REINSURER_NAME", "")),
            "MREINADDR1": _s(row.get("MREINADDR1", "")),
            "MREINADDR2": _s(row.get("MREINADDR2", "")),
            "MREINCITY": _s(row.get("MREINCITY", "")),
            "MREINST": _s(row.get("MREINST", "")),
            "MREINZIP": _s(row.get("MREINZIP", "")),
            "MREINZIP2": _s(row.get("MREINZIP2", "")),
            "CONFIDENCE": _s(row.get("CONFIDENCE", "")),
            "SOURCE": _s(row.get("SOURCE", "")),
            "NOTES": _s(row.get("NOTES", "")),
        }
    return out


def load_reinsurance_type_crosswalk(path: str | None = None) -> dict[str, str]:
    crosswalk_path = path or os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "plan_governance", "config", "reinsurance_type_crosswalk.csv")
    )
    if not os.path.isfile(crosswalk_path):
        return {"C": "CO", "Y": "YRT", "I": "COI"}
    df = pd.read_csv(crosswalk_path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip().upper() for c in df.columns]
    return {_s(r.get("REINSURANCE_CODE", "")).upper(): _s(r.get("MTYPE", "")) for _, r in df.iterrows() if _s(r.get("REINSURANCE_CODE", ""))}


def normalize_phase(val: Any) -> str:
    s = _s(val).replace(".0", "")
    if not s:
        return "1"
    if s.isdigit():
        return str(int(s))
    return s


def load_quikridr_index(path: str | None) -> dict[tuple[str, str], dict[str, str]]:
    if not path or not os.path.isfile(path):
        return {}
    df = read_lifepro_csv(path)
    index: dict[tuple[str, str], dict[str, str]] = {}
    for _, row in df.iterrows():
        pol = format_qladmin_mpolicy(row.get("MPOLICY", ""))
        phase = normalize_phase(row.get("MPHASE", ""))
        if not pol:
            continue
        index[(pol, phase)] = {
            "MPOLICY": pol,
            "MPHASE": phase,
            "MPLAN": _s(row.get("MPLAN", "")),
            "MSTATUS": _s(row.get("MPHSTAT", "")),
            "MUWCLASS": _s(row.get("MUWCLASS", "")),
        }
    return index


def load_quikmstr_index(path: str | None) -> dict[str, dict[str, str]]:
    if not path or not os.path.isfile(path):
        return {}
    df = read_lifepro_csv(path)
    index: dict[str, dict[str, str]] = {}
    for _, row in df.iterrows():
        pol = format_qladmin_mpolicy(row.get("MPOLICY", ""))
        if not pol:
            continue
        index[pol] = {
            "MPOLICY": pol,
            "MMODE": _s(row.get("MMODE", "")),
            "MMODEPREM": _s(row.get("MMODEPREM", "")),
        }
    return index


def load_quikmstr_policy_set(path: str | None) -> set[str]:
    if not path or not os.path.isfile(path):
        return set()
    df = read_lifepro_csv(path)
    return {format_qladmin_mpolicy(v) for v in df.get("MPOLICY", []) if _s(v)}


def resolve_mpolicy(source_policy: str, cw_map: dict[str, str] | None) -> tuple[str, str]:
    src = _s(source_policy)
    cw_map = cw_map or {}
    mapped = cw_map.get(src, src)
    return format_qladmin_mpolicy(mapped), ("CROSSWALK_APPLIED" if src in cw_map else "SOURCE_POLICY")


def candidate_phase_from_benefit_seq(benefit_seq: Any) -> str:
    return normalize_phase(_normalize_benefit_seq(benefit_seq))


def resolve_quikridr_phase(
    mpolicy: str,
    benefit_seq: Any,
    quikridr_index: dict[tuple[str, str], dict[str, str]],
) -> tuple[str, dict[str, str] | None, str]:
    """
    Resolve converted MPHASE via quikridr — do not assume BENEFIT_SEQ=MPHASE blindly.

    1. Try normalized BENEFIT_SEQ as candidate MPHASE (quikridr rulebook default).
    2. If missing, scan converted phases for the policy when exactly one exists.
    """
    if not mpolicy or not quikridr_index:
        return "", None, "NO_QUIKRIDR_INDEX"

    candidate = candidate_phase_from_benefit_seq(benefit_seq)
    rider = quikridr_index.get((mpolicy, candidate))
    if rider is not None:
        return candidate, rider, "BENEFIT_SEQ_CANDIDATE"

    phases = sorted(
        {phase for (pol, phase) in quikridr_index if pol == mpolicy},
        key=lambda p: (len(p), p),
    )
    if len(phases) == 1:
        phase = phases[0]
        return phase, quikridr_index.get((mpolicy, phase)), "SINGLE_POLICY_PHASE"

    for phase in phases:
        if phase == candidate:
            rider = quikridr_index.get((mpolicy, phase))
            if rider is not None:
                return phase, rider, "BENEFIT_SEQ_CANDIDATE"

    return candidate, None, "UNRESOLVED_PHASE"


def build_ptrty_treaty_index(ptrty_df: pd.DataFrame) -> dict[str, pd.Series]:
    index: dict[str, pd.Series] = {}
    for _, row in ptrty_df.iterrows():
        code = _s(row.get("TREATY_CODE", "")).upper()
        if code:
            index[code] = row
    return index
