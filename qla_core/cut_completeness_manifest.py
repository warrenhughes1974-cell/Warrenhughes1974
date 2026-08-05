"""Wave 1 Cut Completeness Manifest — fail-closed gate for full UAT cuts.

PASS semantics (locked): Cut Control + Required Registry PASS.
Does NOT mean every Closed issue in the company log is IN_DATA when
wave1_deferred_gaps is nonempty.

Artifacts are written under QLA_Migration/Reports/ only — never Output root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = REPO_ROOT / "plan_governance" / "config" / "cut_profile_uat_bat_full.json"
DEFAULT_REGISTRY = REPO_ROOT / "plan_governance" / "config" / "approved_issue_registry.json"
DEFAULT_OUTPUT = REPO_ROOT / "QLA_Migration" / "Output"
DEFAULT_REPORTS = REPO_ROOT / "QLA_Migration" / "Reports"

TABLE_STATUSES = (
    "WRITTEN",
    "SKIPPED",
    "GATED_NO_WRITE",
    "REUSED_EXISTING",
    "FAILED",
)

DATE_TOKEN_RE = re.compile(r"(20\d{6})")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_file(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_mtime_iso(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _file_mtime_epoch(path: Path) -> Optional[float]:
    if not path.is_file():
        return None
    return path.stat().st_mtime


def _row_count(path: Path) -> Optional[int]:
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            n = sum(1 for _ in fh)
        return max(n - 1, 0)
    except OSError:
        return None


def _header(path: Path) -> Optional[List[str]]:
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            line = fh.readline().strip("\n\r")
        if not line:
            return []
        return [c.strip() for c in line.split(",")]
    except OSError:
        return None


def _env_truthy(name: str, default: str = "") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_sha(repo_root: Path = REPO_ROOT) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
        return out.strip() or "unknown"
    except Exception:
        return "unknown"


def extract_date_token(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    name = os.path.basename(str(path))
    matches = DATE_TOKEN_RE.findall(name)
    return matches[-1] if matches else None


def load_profile(path: Optional[Path] = None) -> dict:
    return _load_json(path or DEFAULT_PROFILE)


def load_registry(path: Optional[Path] = None) -> dict:
    return _load_json(path or DEFAULT_REGISTRY)


class CutRunJournal:
    """Per-batch table result journal."""

    def __init__(self, batch_started_at: Optional[str] = None):
        self.batch_started_at = batch_started_at or _utc_now_iso()
        self.batch_started_epoch = datetime.now(timezone.utc).timestamp()
        self.tables: Dict[str, dict] = {}
        self.locked_src_base: Optional[str] = None
        self.locked_rule_base: Optional[str] = None
        self.run_mode: Optional[str] = None
        self.app_version: Optional[str] = None
        self.launched_app_path: Optional[str] = None

    @classmethod
    def start(
        cls,
        *,
        app_version: str,
        launched_app_path: str,
        run_mode: str,
        locked_src_base: Optional[str] = None,
        locked_rule_base: Optional[str] = None,
    ) -> "CutRunJournal":
        j = cls()
        j.app_version = app_version
        j.launched_app_path = launched_app_path
        j.run_mode = run_mode
        j.locked_src_base = locked_src_base
        j.locked_rule_base = locked_rule_base
        return j

    def record(
        self,
        table_id: str,
        status: str,
        *,
        reason: str = "",
        source_path: Optional[str] = None,
        output_relpath: Optional[str] = None,
        row_count: Optional[int] = None,
        schema_ok: Optional[bool] = None,
        extra: Optional[dict] = None,
    ) -> None:
        if status not in TABLE_STATUSES:
            raise ValueError(f"invalid table status: {status}")
        entry = {
            "table_id": table_id,
            "status": status,
            "reason": reason or "",
            "source_path": source_path,
            "source_mtime": _file_mtime_iso(Path(source_path)) if source_path else None,
            "source_sha256": _sha256_file(Path(source_path)) if source_path else None,
            "source_date_token": extract_date_token(source_path),
            "output_relpath": output_relpath,
            "row_count": row_count,
            "schema_ok": schema_ok,
            "recorded_at": _utc_now_iso(),
            "run_mode": self.run_mode,
            "profile_context": "uat_bat_full",
        }
        # Capture output hash/mtime/header at journal time when path is known.
        if output_relpath and extra and extra.get("output_abs_path"):
            out_abs = Path(str(extra["output_abs_path"]))
        elif output_relpath and extra and extra.get("output_dir"):
            out_abs = Path(str(extra["output_dir"])) / output_relpath
        else:
            out_abs = None
        if out_abs is not None and out_abs.is_file():
            entry["output_mtime"] = _file_mtime_iso(out_abs)
            entry["output_sha256"] = _sha256_file(out_abs)
            entry["schema_header"] = _header(out_abs)
            if entry.get("row_count") is None:
                entry["row_count"] = _row_count(out_abs)
        if extra:
            entry["extra"] = extra
        self.tables[table_id] = entry

    def to_dict(self) -> dict:
        return {
            "batch_started_at": self.batch_started_at,
            "batch_started_epoch": self.batch_started_epoch,
            "app_version": self.app_version,
            "launched_app_path": self.launched_app_path,
            "run_mode": self.run_mode,
            "locked_src_base": self.locked_src_base,
            "locked_rule_base": self.locked_rule_base,
            "tables": deepcopy(self.tables),
        }


def snapshot_flags(profile: dict) -> dict:
    names: List[str] = []
    for pair in profile.get("flag_pairs") or []:
        names.extend([pair["enable"], pair["write"]])
    for name in (profile.get("required_flags") or {}):
        names.append(name)
    for name in (profile.get("forbidden_flags") or {}):
        names.append(name)
    for extra in (
        "QLA_RUN_MODE",
        "QLA_VALUATION_DATE",
        "QLA_ENABLE_QUIKISWL_EMIT",
        "QLA_ENABLE_QUIKISRR_EMIT",
        "QLA_BATCH_INCLUDE_CLAIMS_UAT",
        "QLA_BATCH_INCLUDE_RATE_TABLES",
        "QLA_PRODUCT_SETUP_ISOLATED",
        "QLA_SKIP_CUT_MANIFEST",
        "QLA_CUT_WAIVER_PATH",
    ):
        names.append(extra)
    snap = {}
    for name in sorted(set(names)):
        snap[name] = os.environ.get(name, "")
    return snap


def load_waiver(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return {"_error": f"waiver file missing: {path}"}
    try:
        data = _load_json(p)
    except Exception as exc:
        return {"_error": f"waiver unreadable: {exc}"}
    data["_path"] = str(p)
    return data


def waiver_covers(waiver: Optional[dict], code: str) -> bool:
    if not waiver or waiver.get("_error"):
        return False
    expires = str(waiver.get("expires_at") or "").strip()
    if expires:
        try:
            exp = datetime.strptime(expires[:10], "%Y-%m-%d").date()
            if datetime.now(timezone.utc).date() > exp:
                return False
        except ValueError:
            return False
    codes = waiver.get("codes") or []
    return code in codes or any(code.startswith(str(c)) for c in codes)


def evaluate_flags(profile: dict, flags: dict, waiver: Optional[dict] = None) -> List[dict]:
    findings: List[dict] = []
    run_mode = (flags.get("QLA_RUN_MODE") or os.environ.get("QLA_RUN_MODE") or "").strip().upper()
    required_mode = str(profile.get("required_run_mode") or "UAT").upper()
    # Empty/missing RUN_MODE must fail uat_bat_full (no silent default to PASS).
    if not run_mode or run_mode != required_mode:
        code = "FLAG_RUN_MODE"
        if not waiver_covers(waiver, code):
            findings.append(
                {
                    "code": code,
                    "detail": f"QLA_RUN_MODE={run_mode!r} required={required_mode} (empty/missing fails)",
                }
            )

    required_val = str(profile.get("required_valuation_date") or "").strip()
    actual_val = (
        flags.get("QLA_VALUATION_DATE")
        or os.environ.get("QLA_VALUATION_DATE")
        or ""
    ).strip()
    actual_digits = "".join(c for c in actual_val if c.isdigit())[:8]
    # AUTO / ACTIVE / * = accept any YYYYMMDD that has a matching PPOLC extract
    # under Source/ or Source/LifePRO_Extracts_YYYYMMDD/ (not locked to one cut).
    if required_val.upper() in ("AUTO", "ACTIVE", "*"):
        if len(actual_digits) != 8:
            code = "VALUATION_DATE_MISMATCH"
            if not waiver_covers(waiver, code):
                findings.append(
                    {
                        "code": code,
                        "detail": (
                            f"QLA_VALUATION_DATE={actual_val!r} required=AUTO "
                            f"(must be YYYYMMDD matching the active source package)"
                        ),
                    }
                )
        else:
            src_root = REPO_ROOT / "QLA_Migration" / "Source"
            candidates = [
                src_root / f"PPOLC_PolicyMaster_Extract_{actual_digits}.csv",
                src_root
                / f"LifePRO_Extracts_{actual_digits}"
                / f"PPOLC_PolicyMaster_Extract_{actual_digits}.csv",
            ]
            if actual_digits == "20251231":
                candidates.extend(
                    [
                        src_root / "12312025_Data" / "PPOLC_PolicyMaster_Extract_20260102.csv",
                        src_root / "PPOLC_PolicyMaster_Extract_20260102.csv",
                    ]
                )
            if not any(p.is_file() for p in candidates):
                code = "VALUATION_DATE_MISMATCH"
                if not waiver_covers(waiver, code):
                    findings.append(
                        {
                            "code": code,
                            "detail": (
                                f"QLA_VALUATION_DATE={actual_digits!r} AUTO: "
                                f"no matching PPOLC extract under Source/"
                            ),
                        }
                    )
    elif required_val and actual_val != required_val:
        code = "VALUATION_DATE_MISMATCH"
        if not waiver_covers(waiver, code):
            findings.append(
                {
                    "code": code,
                    "detail": f"QLA_VALUATION_DATE={actual_val!r} required={required_val}",
                }
            )

    for pair in profile.get("flag_pairs") or []:
        en = flags.get(pair["enable"], "")
        wr = flags.get(pair["write"], "")
        if _env_like_on(en) and not _env_like_on(wr):
            code = "FLAG_EMIT_WITHOUT_WRITE"
            detail = f"{pair['enable']}=on but {pair['write']} not enabled"
            if not waiver_covers(waiver, code) and not waiver_covers(waiver, f"{code}:{pair['enable']}"):
                findings.append({"code": code, "detail": detail})

    for name, allowed in (profile.get("required_flags") or {}).items():
        val = flags.get(name, "")
        allowed_l = {str(a).lower() for a in allowed}
        if val.strip().lower() not in allowed_l:
            code = f"FLAG_REQUIRED_OFF:{name}"
            if not waiver_covers(waiver, code) and not waiver_covers(waiver, "FLAG_REQUIRED_OFF"):
                findings.append({"code": code, "detail": f"{name}={val!r} required in {sorted(allowed_l)}"})

    for name, forbidden in (profile.get("forbidden_flags") or {}).items():
        val = flags.get(name, "")
        forbidden_l = {str(a).lower() for a in forbidden}
        if val.strip().lower() in forbidden_l:
            code = f"FLAG_FORBIDDEN_ON:{name}"
            if not waiver_covers(waiver, code):
                findings.append({"code": code, "detail": f"{name}={val!r} must be off for this profile"})
    return findings


def _env_like_on(val: str) -> bool:
    return str(val or "").strip().lower() in ("1", "true", "yes", "on")


def _parse_iso_epoch(iso: str) -> Optional[float]:
    if not iso:
        return None
    try:
        if iso.endswith("Z"):
            iso = iso[:-1] + "+00:00"
        return datetime.fromisoformat(iso).timestamp()
    except ValueError:
        return None


def enrich_table_entry(
    entry: dict,
    *,
    output_dir: Path,
    batch_started_epoch: float,
) -> dict:
    out = deepcopy(entry)
    rel = out.get("output_relpath")
    if not rel:
        tid = out.get("table_id") or ""
        if tid.startswith("rates/") or tid.startswith("rates\\"):
            rel = tid.replace("\\", "/")
        elif tid.lower().startswith("quik") or tid.startswith("Quik"):
            rel = f"{tid}.csv" if not tid.lower().endswith(".csv") else tid
        else:
            rel = f"{tid}.csv"
        out["output_relpath"] = rel
    path = output_dir / rel
    out["output_mtime"] = _file_mtime_iso(path)
    out["output_sha256"] = _sha256_file(path)
    if out.get("row_count") is None:
        out["row_count"] = _row_count(path)
    out["schema_header"] = _header(path)
    mtime = _file_mtime_epoch(path)
    status = out.get("status")
    stale = bool(status == "WRITTEN" and mtime is not None and mtime < batch_started_epoch)
    out["stale"] = stale
    return out


def synthesize_missing_required(
    profile: dict,
    journal: CutRunJournal,
    output_dir: Path,
) -> Dict[str, dict]:
    """Fill REQUIRED tables absent from journal as SKIPPED (fail-closed)."""
    filled = deepcopy(journal.tables)
    mapping = profile.get("table_output_map") or {}
    for tid in profile.get("required_tables") or []:
        if tid in filled:
            continue
        rel = mapping.get(tid, f"{tid}.csv")
        path = output_dir / rel
        if path.is_file():
            filled[tid] = {
                "table_id": tid,
                "status": "REUSED_EXISTING",
                "reason": "MISSING_JOURNAL_ENTRY",
                "output_relpath": rel,
                "source_path": None,
            }
        else:
            filled[tid] = {
                "table_id": tid,
                "status": "SKIPPED",
                "reason": "MISSING_JOURNAL_AND_OUTPUT",
                "output_relpath": rel,
                "source_path": None,
            }
    for rate in profile.get("required_rates") or []:
        tid = f"rates/{rate}"
        if tid in filled or rate in filled:
            continue
        rel = f"rates/{rate}.csv"
        path = output_dir / rel
        key = tid
        if path.is_file():
            filled[key] = {
                "table_id": key,
                "status": "REUSED_EXISTING",
                "reason": "MISSING_JOURNAL_ENTRY",
                "output_relpath": rel,
                "source_path": None,
            }
        else:
            filled[key] = {
                "table_id": key,
                "status": "SKIPPED",
                "reason": "MISSING_JOURNAL_AND_OUTPUT",
                "output_relpath": rel,
                "source_path": None,
            }
    return filled


def evaluate_tables(
    profile: dict,
    tables: Dict[str, dict],
    *,
    output_dir: Path,
    batch_started_epoch: float,
    waiver: Optional[dict] = None,
) -> Tuple[Dict[str, dict], List[dict]]:
    findings: List[dict] = []
    enriched: Dict[str, dict] = {}
    required = set(profile.get("required_tables") or [])
    required_rates = {f"rates/{r}" for r in (profile.get("required_rates") or [])}
    mapping = profile.get("table_output_map") or {}

    for tid, raw in tables.items():
        entry = deepcopy(raw)
        if not entry.get("output_relpath"):
            if tid in mapping:
                entry["output_relpath"] = mapping[tid]
            elif tid.startswith("rates/"):
                entry["output_relpath"] = f"{tid}.csv" if not tid.endswith(".csv") else tid
        entry = enrich_table_entry(
            entry, output_dir=output_dir, batch_started_epoch=batch_started_epoch
        )
        entry["requirement"] = (
            "REQUIRED"
            if (tid in required or tid in required_rates or tid.replace(".csv", "") in required)
            else "OPTIONAL"
        )
        enriched[tid] = entry

        is_required = entry["requirement"] == "REQUIRED"
        status = entry.get("status")
        if is_required and status in ("SKIPPED", "GATED_NO_WRITE", "REUSED_EXISTING", "FAILED"):
            code = f"TABLE_{status}:{tid}"
            if not waiver_covers(waiver, code) and not waiver_covers(waiver, f"TABLE_{status}"):
                findings.append(
                    {
                        "code": code,
                        "detail": f"required table {tid} status={status} reason={entry.get('reason')}",
                    }
                )
        if is_required and status == "WRITTEN" and entry.get("stale"):
            code = f"STALE_OUTPUT:{tid}"
            if not waiver_covers(waiver, code) and not waiver_covers(waiver, "STALE_OUTPUT"):
                findings.append({"code": code, "detail": f"WRITTEN but output mtime before batch start: {tid}"})
    return enriched, findings


def evaluate_source_dates(
    profile: dict,
    tables: Dict[str, dict],
    valuation_date: str,
    waiver: Optional[dict] = None,
) -> List[dict]:
    findings: List[dict] = []
    allow = set(profile.get("source_date_allowlist") or [])
    expected = (valuation_date or "").strip()
    for tid, entry in tables.items():
        if entry.get("requirement") != "REQUIRED":
            continue
        token = entry.get("source_date_token")
        if not token:
            continue
        if token == expected or token in allow:
            continue
        code = f"SOURCE_DATE_MISMATCH:{tid}"
        if not waiver_covers(waiver, code) and not waiver_covers(waiver, "SOURCE_DATE_MISMATCH"):
            findings.append(
                {
                    "code": code,
                    "detail": f"{tid} source date token={token} valuation={expected} path={entry.get('source_path')}",
                }
            )
    return findings


def evaluate_hygiene(profile: dict, output_dir: Path, waiver: Optional[dict] = None) -> Tuple[List[dict], List[str]]:
    findings: List[dict] = []
    offenders: List[str] = []
    if not output_dir.is_dir():
        findings.append({"code": "HYGIENE_OUTPUT_MISSING", "detail": str(output_dir)})
        return findings, offenders

    try:
        from qla_core.run_logging import _is_allowed_output_table_csv
    except Exception:  # pragma: no cover
        _is_allowed_output_table_csv = None

    for item in output_dir.iterdir():
        if item.is_dir():
            continue
        if not item.is_file():
            continue
        name = item.name
        lower = name.lower()
        if not lower.endswith(".csv"):
            code = "HYGIENE_NON_CSV"
            offenders.append(name)
            if not waiver_covers(waiver, code):
                findings.append({"code": code, "detail": name})
            continue
        allowed = (
            _is_allowed_output_table_csv(name)
            if _is_allowed_output_table_csv is not None
            else (lower.startswith("quik") or name.startswith("Quik"))
        )
        if not allowed:
            code = "HYGIENE_NON_TABLE_CSV"
            offenders.append(name)
            if not waiver_covers(waiver, code) and not waiver_covers(waiver, f"{code}:{name}"):
                findings.append({"code": code, "detail": name})
    return findings, offenders


def evaluate_tv_parity(
    profile: dict,
    registry: dict,
    output_dir: Path,
    waiver: Optional[dict] = None,
) -> List[dict]:
    findings: List[dict] = []
    tv_dir = output_dir / "Test_Validation"
    owned = list(profile.get("tv_parity_owned_tables") or [])
    for issue in registry.get("issues") or []:
        if not issue.get("tv_parity"):
            continue
        for rel in issue.get("owned_tables") or []:
            rel_path = rel if str(rel).endswith(".csv") else f"{rel}.csv"
            if str(rel).startswith("rates/"):
                rel_path = str(rel) if str(rel).endswith(".csv") else f"{rel}.csv"
            owned.append(rel_path.replace("\\", "/"))
    # Unique preserve order
    seen = set()
    uniq = []
    for rel in owned:
        if rel not in seen:
            seen.add(rel)
            uniq.append(rel)

    for rel in uniq:
        out_p = output_dir / rel
        tv_p = tv_dir / rel
        if not out_p.is_file():
            continue
        if not tv_p.is_file():
            # T4: absence OK unless required publish — Wave 1 only fails mismatch when present
            continue
        osha = _sha256_file(out_p)
        tsha = _sha256_file(tv_p)
        if osha != tsha:
            code = f"TV_PARITY_MISMATCH:{rel}"
            if not waiver_covers(waiver, code) and not waiver_covers(waiver, "TV_PARITY_MISMATCH"):
                findings.append({"code": code, "detail": f"Output vs Test_Validation sha mismatch for {rel}"})
    return findings


def run_validator(script_rel: str, repo_root: Path = REPO_ROOT, timeout: int = 600) -> dict:
    path = repo_root / script_rel
    if not path.is_file():
        return {
            "script": script_rel,
            "status": "MISSING",
            "returncode": None,
            "detail": "validator path missing",
        }
    try:
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        ok = proc.returncode == 0
        return {
            "script": script_rel,
            "status": "PASS" if ok else "FAIL",
            "returncode": proc.returncode,
            "detail": (proc.stdout or "")[-800:] + (("\n" + proc.stderr) if proc.stderr else ""),
        }
    except subprocess.TimeoutExpired:
        return {"script": script_rel, "status": "FAIL", "returncode": None, "detail": "timeout"}
    except Exception as exc:
        return {"script": script_rel, "status": "FAIL", "returncode": None, "detail": str(exc)}


def evaluate_registry(
    registry: dict,
    *,
    repo_root: Path = REPO_ROOT,
    run_validators: bool = True,
    enforce_accountability: Optional[bool] = None,
    waiver: Optional[dict] = None,
) -> Tuple[List[dict], List[dict], List[dict], List[dict]]:
    """Returns (findings, validator_results, deferred_gaps_echo, accountability_rows).

    Accountability policy (Wave 1): for each required registry issue with
    accountability=required_in_data, validator exit 0 is the IN_DATA equivalent.
    Soft count-only spots are never used. SKIPPED_DRY / missing / fail ⇒ cannot PASS
    when enforce_accountability is true (defaults to run_validators).
    """
    findings: List[dict] = []
    results: List[dict] = []
    deferred = list(registry.get("wave1_deferred_gaps") or [])
    if enforce_accountability is None:
        enforce_accountability = bool(run_validators)

    issue_validator_status: Dict[str, List[str]] = {}

    for issue in registry.get("issues") or []:
        if not issue.get("required"):
            continue
        iid = str(issue.get("id"))
        validators = issue.get("validators") or []
        if not validators:
            code = f"REGISTRY_VALIDATOR_MISSING:{iid}"
            if not waiver_covers(waiver, code):
                findings.append({"code": code, "detail": f"required issue {iid} has no validators"})
            issue_validator_status.setdefault(iid, []).append("MISSING")
            continue
        for script in validators:
            if not (repo_root / script).is_file():
                code = f"REGISTRY_VALIDATOR_MISSING:{iid}"
                results.append(
                    {"id": iid, "script": script, "status": "MISSING", "returncode": None, "detail": "missing"}
                )
                issue_validator_status.setdefault(iid, []).append("MISSING")
                if not waiver_covers(waiver, code):
                    findings.append({"code": code, "detail": f"{iid} validator missing: {script}"})
                continue
            if not run_validators:
                results.append(
                    {"id": iid, "script": script, "status": "SKIPPED_DRY", "returncode": None, "detail": "dry-run"}
                )
                issue_validator_status.setdefault(iid, []).append("SKIPPED_DRY")
                continue
            res = run_validator(script, repo_root=repo_root)
            res["id"] = iid
            results.append(res)
            issue_validator_status.setdefault(iid, []).append(res["status"])
            if res["status"] != "PASS":
                code = f"REGISTRY_VALIDATOR_FAIL:{iid}"
                if not waiver_covers(waiver, code) and not waiver_covers(waiver, "REGISTRY_VALIDATOR_FAIL"):
                    findings.append(
                        {"code": code, "detail": f"{iid} {script} rc={res.get('returncode')} status={res['status']}"}
                    )

    accountability: List[dict] = []
    for issue in registry.get("issues") or []:
        if not issue.get("required"):
            continue
        if str(issue.get("accountability") or "") != "required_in_data":
            continue
        iid = str(issue.get("id"))
        statuses = issue_validator_status.get(iid) or []
        if statuses and all(s == "PASS" for s in statuses):
            row = {
                "id": iid,
                "status": "IN_DATA",
                "equivalent": "required_registry_validator_exit_0",
                "detail": "All required validators PASS",
            }
        elif any(s == "SKIPPED_DRY" for s in statuses):
            row = {
                "id": iid,
                "status": "NOT_RUN",
                "equivalent": "required_registry_validator_exit_0",
                "detail": "Validators skipped (dry); IN_DATA not proven",
            }
            if enforce_accountability:
                code = f"ACCOUNTABILITY_NOT_PROVEN:{iid}"
                if not waiver_covers(waiver, code) and not waiver_covers(waiver, "ACCOUNTABILITY_NOT_PROVEN"):
                    findings.append({"code": code, "detail": row["detail"]})
        else:
            row = {
                "id": iid,
                "status": "GAP",
                "equivalent": "required_registry_validator_exit_0",
                "detail": f"validator statuses={statuses}",
            }
            if enforce_accountability:
                code = f"ACCOUNTABILITY_GAP:{iid}"
                if not waiver_covers(waiver, code) and not waiver_covers(waiver, "ACCOUNTABILITY_GAP"):
                    findings.append({"code": code, "detail": row["detail"]})
        accountability.append(row)

    return findings, results, deferred, accountability


def write_journal_unavailable_manifest(
    *,
    reason: str,
    reports_dir: Path,
    package_ok: Optional[bool] = None,
    app_version: str = "",
    launched_app_path: str = "",
) -> dict:
    """Fail-closed artifact when batch journal could not be started."""
    reports_dir = Path(reports_dir)
    identity = {
        "profile": "uat_bat_full",
        "pass_label": "Cut Control + Required Registry PASS",
        "app_version": app_version,
        "launched_app_path": launched_app_path,
        "git_sha": git_sha(),
        "QLA_VALUATION_DATE": os.environ.get("QLA_VALUATION_DATE", ""),
        "run_mode": os.environ.get("QLA_RUN_MODE", ""),
        "batch_started_at": None,
    }
    manifest = {
        "status": "FAIL",
        "pass_semantics": "Cut Control + Required Registry PASS",
        "full_closed_fleet_claim": False,
        "identity": identity,
        "batch_finished_at": _utc_now_iso(),
        "findings": [{"code": "JOURNAL_UNAVAILABLE", "detail": reason}],
        "warnings": [],
        "waived": [],
        "deferred_gaps": (load_registry().get("wave1_deferred_gaps") or []),
        "accountability": [],
        "accountability_policy": (
            "Required registry validator exit 0 is the Wave 1 IN_DATA equivalent; "
            "journal unavailable blocks handoff before accountability can run."
        ),
        "package_ok": package_ok,
        "handoff_ok": False,
        "manifest_created_at": _utc_now_iso(),
    }
    arts = write_manifest_artifacts(manifest, reports_dir)
    manifest["artifacts"] = arts
    return manifest


def build_identity(
    *,
    profile: dict,
    journal: CutRunJournal,
    repo_root: Path = REPO_ROOT,
    valuation_date: Optional[str] = None,
) -> dict:
    root_app = repo_root / "app.py"
    twin_app = repo_root / "QLA_Migration" / "app.py"
    root_sha = _sha256_file(root_app)
    twin_sha = _sha256_file(twin_app)
    return {
        "profile": profile.get("profile"),
        "pass_label": profile.get("pass_label"),
        "app_version": journal.app_version,
        "launched_app_path": journal.launched_app_path,
        "root_app_sha256": root_sha,
        "twin_app_sha256": twin_sha,
        "twin_app_match": bool(root_sha and twin_sha and root_sha == twin_sha),
        "git_sha": git_sha(repo_root),
        "QLA_VALUATION_DATE": valuation_date or os.environ.get("QLA_VALUATION_DATE", ""),
        "locked_src_base": journal.locked_src_base,
        "locked_rule_base": journal.locked_rule_base,
        "run_mode": journal.run_mode or os.environ.get("QLA_RUN_MODE", ""),
        "batch_started_at": journal.batch_started_at,
        "wave0_baseline_ref": profile.get("wave0_baseline_ref"),
        "rates_tv_parity_tier": profile.get("rates_tv_parity_tier"),
    }


def render_markdown(manifest: dict) -> str:
    status = manifest.get("status")
    identity = manifest.get("identity") or {}
    lines = [
        f"# Cut Completeness Manifest — {status}",
        "",
        f"**Pass semantics:** {identity.get('pass_label') or 'Cut Control + Required Registry PASS'}",
        "",
        "This PASS (if any) does **not** claim full Closed-fleet accountability while deferred_gaps are nonempty.",
        "",
        "## Identity",
        "",
        f"- profile: `{identity.get('profile')}`",
        f"- app_version: `{identity.get('app_version')}`",
        f"- git_sha: `{identity.get('git_sha')}`",
        f"- valuation: `{identity.get('QLA_VALUATION_DATE')}`",
        f"- twin_app_match: `{identity.get('twin_app_match')}`",
        f"- batch_started_at: `{identity.get('batch_started_at')}`",
        f"- batch_finished_at: `{manifest.get('batch_finished_at')}`",
        f"- rates_tv_parity_tier: `{identity.get('rates_tv_parity_tier')}`",
        "",
        "## Findings",
        "",
    ]
    findings = manifest.get("findings") or []
    if not findings:
        lines.append("_None_")
    else:
        for f in findings:
            lines.append(f"- `{f.get('code')}` — {f.get('detail')}")
    lines.extend(["", "## Deferred gaps (explicit)", ""])
    deferred = manifest.get("deferred_gaps") or []
    if not deferred:
        lines.append("_None_")
    else:
        for d in deferred:
            lines.append(f"- **#{d.get('id')}** — {d.get('reason')}")
    lines.extend(["", "## Warnings", ""])
    warns = manifest.get("warnings") or []
    if not warns:
        lines.append("_None_")
    else:
        for w in warns:
            lines.append(f"- {w}")
    lines.extend(["", "## Waived", ""])
    waived = manifest.get("waived") or []
    if not waived:
        lines.append("_None_")
    else:
        for w in waived:
            lines.append(f"- `{w}`")
    lines.append("")
    return "\n".join(lines)


def write_manifest_artifacts(
    manifest: dict,
    reports_dir: Path,
    *,
    stamp: Optional[str] = None,
) -> dict:
    reports_dir.mkdir(parents=True, exist_ok=True)
    stamp = stamp or _utc_stamp()
    json_path = reports_dir / f"cut_manifest_{stamp}.json"
    md_path = reports_dir / f"cut_manifest_{stamp}.md"
    latest_json = reports_dir / "cut_manifest_latest.json"
    latest_md = reports_dir / "cut_manifest_latest.md"
    payload = json.dumps(manifest, indent=2, default=str)
    json_path.write_text(payload, encoding="utf-8")
    md_path.write_text(render_markdown(manifest), encoding="utf-8")
    shutil.copy2(json_path, latest_json)
    shutil.copy2(md_path, latest_md)
    return {
        "json": str(json_path),
        "md": str(md_path),
        "latest_json": str(latest_json),
        "latest_md": str(latest_md),
        "stamp": stamp,
    }


def build_and_evaluate_cut_manifest(
    journal: CutRunJournal,
    *,
    output_dir: Optional[Path] = None,
    reports_dir: Optional[Path] = None,
    repo_root: Path = REPO_ROOT,
    profile_path: Optional[Path] = None,
    registry_path: Optional[Path] = None,
    run_validators: bool = True,
    write_artifacts: bool = True,
    package_ok: Optional[bool] = None,
    mutate_hygiene: bool = False,
) -> dict:
    """Build + evaluate cut manifest. Returns manifest dict including status/artifacts."""
    profile = load_profile(profile_path)
    registry = load_registry(registry_path)
    output_dir = Path(output_dir or DEFAULT_OUTPUT)
    reports_dir = Path(reports_dir or DEFAULT_REPORTS)

    skip_env = _env_truthy("QLA_SKIP_CUT_MANIFEST")
    waiver_path = os.environ.get("QLA_CUT_WAIVER_PATH", "").strip() or None
    waiver = load_waiver(waiver_path)

    flags = snapshot_flags(profile)
    identity = build_identity(
        profile=profile,
        journal=journal,
        repo_root=repo_root,
        valuation_date=flags.get("QLA_VALUATION_DATE") or os.environ.get("QLA_VALUATION_DATE"),
    )
    identity["batch_finished_at"] = _utc_now_iso()

    warnings: List[str] = []
    findings: List[dict] = []
    waived: List[str] = []

    if not identity.get("twin_app_match"):
        warnings.append("TWIN_APP_HASH_MISMATCH (Wave 1 WARN only)")

    if waiver and waiver.get("_error"):
        findings.append({"code": "WAIVER_INVALID", "detail": waiver["_error"]})
        waiver = None

    if skip_env:
        if waiver_covers(waiver, "QLA_SKIP_CUT_MANIFEST") or waiver_covers(waiver, "BREAK_GLASS"):
            warnings.append("QLA_SKIP_CUT_MANIFEST honored with recorded waiver (break-glass)")
            waived.append("QLA_SKIP_CUT_MANIFEST")
        else:
            findings.append(
                {
                    "code": "BREAK_GLASS_WITHOUT_WAIVER",
                    "detail": "QLA_SKIP_CUT_MANIFEST=1 requires explicit dated waiver",
                }
            )

    if mutate_hygiene:
        try:
            from qla_core.run_logging import relocate_non_table_csvs

            relocate_non_table_csvs(str(output_dir), str(reports_dir))
        except Exception as exc:
            findings.append({"code": "HYGIENE_RELOCATE_ERROR", "detail": str(exc)})

    findings.extend(evaluate_flags(profile, flags, waiver))

    tables_raw = synthesize_missing_required(profile, journal, output_dir)
    tables, table_findings = evaluate_tables(
        profile,
        tables_raw,
        output_dir=output_dir,
        batch_started_epoch=float(journal.batch_started_epoch),
        waiver=waiver,
    )
    findings.extend(table_findings)
    findings.extend(
        evaluate_source_dates(
            profile,
            tables,
            valuation_date=str(identity.get("QLA_VALUATION_DATE") or ""),
            waiver=waiver,
        )
    )
    hyg_findings, hyg_offenders = evaluate_hygiene(profile, output_dir, waiver)
    findings.extend(hyg_findings)
    findings.extend(evaluate_tv_parity(profile, registry, output_dir, waiver))

    reg_findings, reg_results, deferred, accountability = evaluate_registry(
        registry,
        repo_root=repo_root,
        run_validators=run_validators,
        enforce_accountability=run_validators,
        waiver=waiver,
    )
    findings.extend(reg_findings)

    # Filter findings covered by waiver into waived list
    remaining = []
    for f in findings:
        code = f.get("code") or ""
        if waiver_covers(waiver, code):
            waived.append(code)
        else:
            remaining.append(f)
    findings = remaining

    status = "PASS" if not findings else "FAIL"
    if skip_env and "QLA_SKIP_CUT_MANIFEST" in waived and not findings:
        status = "PASS"

    handoff_ok = status == "PASS" and (package_ok is True if package_ok is not None else True)

    manifest = {
        "status": status,
        "pass_semantics": profile.get("pass_label"),
        "full_closed_fleet_claim": False,
        "identity": identity,
        "batch_finished_at": identity["batch_finished_at"],
        "flags": flags,
        "tables": tables,
        "findings": findings,
        "warnings": warnings,
        "waived": waived,
        "waiver": {k: waiver.get(k) for k in ("waiver_id", "approved_by", "approved_at", "expires_at", "reason", "_path")}
        if waiver
        else None,
        "deferred_gaps": deferred,
        "registry_results": reg_results,
        "accountability_policy": (
            "Required registry validator exit 0 is the Wave 1 IN_DATA equivalent "
            "(soft count-only spots are not used). Deferred gaps remain visible and "
            "do not claim full Closed-fleet green."
        ),
        "accountability": accountability,
        "hygiene_offenders": hyg_offenders,
        "package_ok": package_ok,
        "handoff_ok": handoff_ok,
        "break_glass_env": skip_env,
        "rates_tv_parity_tier": profile.get("rates_tv_parity_tier"),
        "manifest_created_at": _utc_now_iso(),
    }

    if write_artifacts:
        artifacts = write_manifest_artifacts(manifest, reports_dir)
        manifest["artifacts"] = artifacts
    return manifest


def evaluate_handoff(manifest: dict, package_ok: bool) -> bool:
    return bool(manifest.get("status") == "PASS" and package_ok)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Cut Completeness Manifest (Wave 1)")
    ap.add_argument("--dry-run", action="store_true", help="Evaluate current Output without relocating files")
    ap.add_argument("--no-validators", action="store_true", help="Skip running registry validators")
    ap.add_argument("--simulate-written", action="store_true", help="Mark existing required tables WRITTEN for dry-run")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS)
    ap.add_argument("--write", action="store_true", help="Write Reports artifacts (default on for non-dry unless --no-write)")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)

    # Do not default to a stale midyear date — resolve from env or active PPOLC.
    try:
        from qla_core.valuation_date import apply_valuation_date_env

        apply_valuation_date_env(REPO_ROOT / "QLA_Migration" / "Source")
    except Exception:
        pass
    journal = CutRunJournal.start(
        app_version=os.environ.get("QLA_APP_VERSION_OVERRIDE", "dry-run"),
        launched_app_path=str(REPO_ROOT / "app.py"),
        run_mode=os.environ.get("QLA_RUN_MODE", "UAT"),
        locked_src_base=str(REPO_ROOT / "QLA_Migration" / "Source"),
        locked_rule_base=str(REPO_ROOT / "QLA_Migration" / "Rulebooks"),
    )
    if args.simulate_written:
        profile = load_profile()
        mapping = profile.get("table_output_map") or {}
        for tid, rel in mapping.items():
            p = args.output_dir / rel
            if p.is_file():
                journal.record(tid, "WRITTEN", output_relpath=rel, row_count=_row_count(p))
        for rate in profile.get("required_rates") or []:
            rel = f"rates/{rate}.csv"
            p = args.output_dir / rel
            if p.is_file():
                journal.record(f"rates/{rate}", "WRITTEN", output_relpath=rel, row_count=_row_count(p))
        # Backdate journal start so current files are not stale
        journal.batch_started_epoch = 0.0
        journal.batch_started_at = "1970-01-01T00:00:00Z"

    write_artifacts = (not args.no_write) and (args.write or not args.dry_run or args.simulate_written)
    if args.dry_run and not args.write:
        write_artifacts = False

    manifest = build_and_evaluate_cut_manifest(
        journal,
        output_dir=args.output_dir,
        reports_dir=args.reports_dir,
        run_validators=not args.no_validators,
        write_artifacts=write_artifacts,
        package_ok=None,
        mutate_hygiene=False,
    )
    print(json.dumps({
        "status": manifest.get("status"),
        "findings_count": len(manifest.get("findings") or []),
        "findings": [f.get("code") for f in (manifest.get("findings") or [])][:40],
        "deferred_gaps": [d.get("id") for d in (manifest.get("deferred_gaps") or [])],
        "artifacts": manifest.get("artifacts"),
        "pass_semantics": manifest.get("pass_semantics"),
        "full_closed_fleet_claim": manifest.get("full_closed_fleet_claim"),
    }, indent=2))
    return 0 if manifest.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
