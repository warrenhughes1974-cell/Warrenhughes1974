"""Wave 1 cut-completeness unit/control tests (no production Output mutation)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from qla_core.cut_completeness_manifest import (
    CutRunJournal,
    build_and_evaluate_cut_manifest,
    evaluate_flags,
    evaluate_handoff,
    evaluate_hygiene,
    evaluate_registry,
    evaluate_source_dates,
    evaluate_tables,
    evaluate_tv_parity,
    load_profile,
    load_registry,
    render_markdown,
    snapshot_flags,
    waiver_covers,
    write_journal_unavailable_manifest,
    write_manifest_artifacts,
)
from qla_core.run_logging import relocate_non_table_csvs

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture()
def profile():
    return load_profile()


@pytest.fixture()
def registry():
    return load_registry()


def _journal(**kwargs) -> CutRunJournal:
    return CutRunJournal.start(
        app_version="v58.70-test",
        launched_app_path=str(REPO / "app.py"),
        run_mode="UAT",
        locked_src_base=str(REPO / "QLA_Migration" / "Source"),
        locked_rule_base=str(REPO / "QLA_Migration" / "Rulebooks"),
        **kwargs,
    )


def test_pass_path_with_simulated_written_tables(tmp_path, profile, monkeypatch):
    out = tmp_path / "Output"
    reports = tmp_path / "Reports"
    out.mkdir()
    (out / "rates").mkdir()
    (out / "Test_Validation").mkdir()
    mapping = profile["table_output_map"]
    for tid, rel in mapping.items():
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("H\n1\n", encoding="utf-8")
    for rate in profile["required_rates"]:
        (out / "rates" / f"{rate}.csv").write_text("H\n1\n", encoding="utf-8")

    monkeypatch.setenv("QLA_RUN_MODE", "UAT")
    monkeypatch.setenv("QLA_VALUATION_DATE", "20260630")
    monkeypatch.setenv("QLA_BATCH_INCLUDE_CLAIMS_UAT", "1")
    monkeypatch.setenv("QLA_ENABLE_QUIKISRR_EMIT", "1")
    monkeypatch.setenv("QLA_BATCH_INCLUDE_RATE_TABLES", "1")
    monkeypatch.setenv("QLA_ENABLE_QUIKLOAN_EMIT", "1")
    monkeypatch.setenv("QLA_QUIKLOAN_WRITE_OUTPUT", "1")
    monkeypatch.setenv("QLA_ENABLE_QUIKBENH_LOAN_EMIT", "1")
    monkeypatch.setenv("QLA_QUIKBENH_LOAN_WRITE_OUTPUT", "1")
    monkeypatch.setenv("QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT", "1")
    monkeypatch.setenv("QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT", "1")
    monkeypatch.setenv("QLA_ENABLE_REINSURANCE_EMIT", "1")
    monkeypatch.setenv("QLA_REINSURANCE_WRITE_OUTPUT", "1")
    monkeypatch.delenv("QLA_PRODUCT_SETUP_ISOLATED", raising=False)
    monkeypatch.delenv("QLA_SKIP_CUT_MANIFEST", raising=False)

    j = _journal()
    j.batch_started_epoch = 0.0
    for tid, rel in mapping.items():
        j.record(tid, "WRITTEN", output_relpath=rel, row_count=1)
    for rate in profile["required_rates"]:
        j.record(f"rates/{rate}", "WRITTEN", output_relpath=f"rates/{rate}.csv", row_count=1)

    manifest = build_and_evaluate_cut_manifest(
        j,
        output_dir=out,
        reports_dir=reports,
        run_validators=False,
        write_artifacts=True,
        package_ok=True,
        mutate_hygiene=False,
    )
    assert manifest["status"] == "PASS"
    assert manifest["full_closed_fleet_claim"] is False
    assert any(d["id"] == "117" for d in manifest["deferred_gaps"])
    assert "117" in render_markdown(manifest)
    assert evaluate_handoff(manifest, True) is True
    assert (reports / "cut_manifest_latest.json").is_file()


def test_missing_source_skip_fails(tmp_path, profile, monkeypatch):
    out = tmp_path / "Output"
    out.mkdir()
    monkeypatch.setenv("QLA_RUN_MODE", "UAT")
    monkeypatch.setenv("QLA_VALUATION_DATE", "20260630")
    for name, vals in profile["required_flags"].items():
        monkeypatch.setenv(name, vals[0])
    j = _journal()
    j.record("quikprmh", "SKIPPED", reason="MISSING_SOURCE", output_relpath="quikprmh.csv")
    tables, findings = evaluate_tables(
        profile, j.tables, output_dir=out, batch_started_epoch=j.batch_started_epoch
    )
    assert any(f["code"].startswith("TABLE_SKIPPED:quikprmh") for f in findings)


def test_disabled_write_flag_fails(profile, monkeypatch):
    monkeypatch.setenv("QLA_ENABLE_QUIKLOAN_EMIT", "1")
    monkeypatch.setenv("QLA_QUIKLOAN_WRITE_OUTPUT", "0")
    flags = snapshot_flags(profile)
    findings = evaluate_flags(profile, flags)
    assert any(f["code"] == "FLAG_EMIT_WITHOUT_WRITE" for f in findings)


def test_stale_output_fails(tmp_path, profile):
    out = tmp_path / "Output"
    out.mkdir()
    p = out / "quikmstr.csv"
    p.write_text("H\n1\n", encoding="utf-8")
    os.utime(p, (1_000_000_000, 1_000_000_000))
    j = _journal()
    j.batch_started_epoch = 2_000_000_000
    j.record("quikmstr", "WRITTEN", output_relpath="quikmstr.csv", row_count=1)
    _, findings = evaluate_tables(
        profile, {"quikmstr": j.tables["quikmstr"]}, output_dir=out, batch_started_epoch=j.batch_started_epoch
    )
    assert any(f["code"].startswith("STALE_OUTPUT") for f in findings)


def test_source_date_mismatch_fails(profile):
    tables = {
        "quikmemo": {
            "table_id": "quikmemo",
            "requirement": "REQUIRED",
            "status": "WRITTEN",
            "source_date_token": "20251231",
            "source_path": "PNOTE_Extract_20251231.csv",
        }
    }
    findings = evaluate_source_dates(profile, tables, valuation_date="20260630")
    assert any(f["code"].startswith("SOURCE_DATE_MISMATCH") for f in findings)


def test_registry_validator_missing_fails(tmp_path, monkeypatch):
    reg = {
        "issues": [
            {
                "id": "999Z",
                "required": True,
                "validators": ["tools/validators/does_not_exist_999z.py"],
                "tv_parity": False,
                "owned_tables": [],
            }
        ],
        "wave1_deferred_gaps": [{"id": "117", "reason": "test"}],
    }
    reg_path = tmp_path / "reg.json"
    reg_path.write_text(json.dumps(reg), encoding="utf-8")
    profile_path = REPO / "plan_governance" / "config" / "cut_profile_uat_bat_full.json"
    out = tmp_path / "Output"
    reports = tmp_path / "Reports"
    out.mkdir()
    monkeypatch.setenv("QLA_RUN_MODE", "UAT")
    monkeypatch.setenv("QLA_VALUATION_DATE", "20260630")
    monkeypatch.setenv("QLA_BATCH_INCLUDE_CLAIMS_UAT", "1")
    monkeypatch.setenv("QLA_ENABLE_QUIKISRR_EMIT", "1")
    monkeypatch.setenv("QLA_BATCH_INCLUDE_RATE_TABLES", "1")
    j = _journal()
    j.batch_started_epoch = 0.0
    # Minimal required tables present+written so registry miss is visible among findings
    prof = load_profile(profile_path)
    for tid, rel in prof["table_output_map"].items():
        (out / rel).write_text("H\n", encoding="utf-8")
        j.record(tid, "WRITTEN", output_relpath=rel, row_count=0)
    for rate in prof["required_rates"]:
        (out / "rates").mkdir(exist_ok=True)
        (out / "rates" / f"{rate}.csv").write_text("H\n", encoding="utf-8")
        j.record(f"rates/{rate}", "WRITTEN", output_relpath=f"rates/{rate}.csv", row_count=0)
    for pair in prof["flag_pairs"]:
        monkeypatch.setenv(pair["enable"], "1")
        monkeypatch.setenv(pair["write"], "1")
    manifest = build_and_evaluate_cut_manifest(
        j,
        output_dir=out,
        reports_dir=reports,
        profile_path=profile_path,
        registry_path=reg_path,
        run_validators=True,
        write_artifacts=False,
        package_ok=True,
    )
    assert manifest["status"] == "FAIL"
    assert any("REGISTRY_VALIDATOR_MISSING" in f["code"] for f in manifest["findings"])


def test_deferred_gaps_truthfulness(registry):
    ids = {d["id"] for d in registry["wave1_deferred_gaps"]}
    for required in ("55", "60", "76", "96", "116", "117", "136"):
        assert required in ids
    gap96 = next(d for d in registry["wave1_deferred_gaps"] if d["id"] == "96")
    assert gap96["validators"] == ["Issue_Log_Items/Issue_96/validate_issue96_cso_pvo.py"]
    assert registry.get("pass_semantics")
    # Required set must include Wave 0 anchors
    req_ids = {i["id"] for i in registry["issues"] if i.get("required")}
    for rid in ("21F", "54", "95", "114", "120", "124", "135"):
        assert rid in req_ids


def test_tv_parity_mismatch_fails(tmp_path, profile, registry):
    out = tmp_path / "Output"
    tv = out / "Test_Validation"
    tv.mkdir(parents=True)
    (out / "quikprmh.csv").write_text("A\n1\n", encoding="utf-8")
    (tv / "quikprmh.csv").write_text("A\n2\n", encoding="utf-8")
    findings = evaluate_tv_parity(profile, registry, out)
    assert any("TV_PARITY_MISMATCH" in f["code"] for f in findings)


def test_hygiene_failure_and_relocate(tmp_path, profile):
    out = tmp_path / "Output"
    reports = tmp_path / "Reports"
    out.mkdir()
    reports.mkdir()
    bad = out / "claims_review_hold_manifest.csv"
    orphan = out / "quikmemo_orphan_log.csv"
    bad.write_text("x\n", encoding="utf-8")
    orphan.write_text("x\n", encoding="utf-8")
    (out / "quikmstr.csv").write_text("H\n", encoding="utf-8")
    findings, offenders = evaluate_hygiene(profile, out)
    assert "claims_review_hold_manifest.csv" in offenders
    assert "quikmemo_orphan_log.csv" in offenders
    assert any(f["code"] == "HYGIENE_NON_TABLE_CSV" for f in findings)
    moved = relocate_non_table_csvs(str(out), str(reports))
    assert moved["moved"]
    assert not bad.exists()
    assert not orphan.exists()
    assert (out / "quikmstr.csv").exists()
    findings2, offenders2 = evaluate_hygiene(profile, out)
    assert "claims_review_hold_manifest.csv" not in offenders2
    assert "quikmemo_orphan_log.csv" not in offenders2


def test_idempotent_manifest_generation(tmp_path, profile, monkeypatch):
    out = tmp_path / "Output"
    reports = tmp_path / "Reports"
    out.mkdir()
    (out / "rates").mkdir()
    monkeypatch.setenv("QLA_RUN_MODE", "UAT")
    monkeypatch.setenv("QLA_VALUATION_DATE", "20260630")
    for name, vals in profile["required_flags"].items():
        monkeypatch.setenv(name, vals[0])
    for pair in profile["flag_pairs"]:
        monkeypatch.setenv(pair["enable"], "1")
        monkeypatch.setenv(pair["write"], "1")
    j = _journal()
    j.batch_started_epoch = 0.0
    for tid, rel in profile["table_output_map"].items():
        (out / rel).write_text("H\n1\n", encoding="utf-8")
        j.record(tid, "WRITTEN", output_relpath=rel, row_count=1)
    for rate in profile["required_rates"]:
        (out / "rates" / f"{rate}.csv").write_text("H\n1\n", encoding="utf-8")
        j.record(f"rates/{rate}", "WRITTEN", output_relpath=f"rates/{rate}.csv", row_count=1)
    m1 = build_and_evaluate_cut_manifest(
        j, output_dir=out, reports_dir=reports, run_validators=False, write_artifacts=True, package_ok=True
    )
    m2 = build_and_evaluate_cut_manifest(
        j, output_dir=out, reports_dir=reports, run_validators=False, write_artifacts=True, package_ok=True
    )
    assert m1["status"] == m2["status"] == "PASS"
    assert [f["code"] for f in m1["findings"]] == [f["code"] for f in m2["findings"]]
    assert Path(m1["artifacts"]["json"]).is_file()
    assert Path(m2["artifacts"]["json"]).is_file()
    # New timestamped artifact when stamps differ; same-second re-run may overwrite same stamp
    assert (reports / "cut_manifest_latest.json").is_file()


def test_break_glass_without_waiver_fails(tmp_path, profile, monkeypatch):
    out = tmp_path / "Output"
    reports = tmp_path / "Reports"
    out.mkdir()
    (out / "rates").mkdir()
    monkeypatch.setenv("QLA_SKIP_CUT_MANIFEST", "1")
    monkeypatch.delenv("QLA_CUT_WAIVER_PATH", raising=False)
    monkeypatch.setenv("QLA_RUN_MODE", "UAT")
    monkeypatch.setenv("QLA_VALUATION_DATE", "20260630")
    for name, vals in profile["required_flags"].items():
        monkeypatch.setenv(name, vals[0])
    for pair in profile["flag_pairs"]:
        monkeypatch.setenv(pair["enable"], "1")
        monkeypatch.setenv(pair["write"], "1")
    j = _journal()
    j.batch_started_epoch = 0.0
    for tid, rel in profile["table_output_map"].items():
        (out / rel).write_text("H\n", encoding="utf-8")
        j.record(tid, "WRITTEN", output_relpath=rel)
    for rate in profile["required_rates"]:
        (out / "rates" / f"{rate}.csv").write_text("H\n", encoding="utf-8")
        j.record(f"rates/{rate}", "WRITTEN", output_relpath=f"rates/{rate}.csv")
    manifest = build_and_evaluate_cut_manifest(
        j, output_dir=out, reports_dir=reports, run_validators=False, write_artifacts=False, package_ok=True
    )
    assert manifest["status"] == "FAIL"
    assert any(f["code"] == "BREAK_GLASS_WITHOUT_WAIVER" for f in manifest["findings"])


def test_waiver_covers_and_expiry():
    waiver = {
        "codes": ["STALE_OUTPUT"],
        "expires_at": "2099-01-01",
    }
    assert waiver_covers(waiver, "STALE_OUTPUT:quikmstr")
    expired = {"codes": ["STALE_OUTPUT"], "expires_at": "2020-01-01"}
    assert not waiver_covers(expired, "STALE_OUTPUT")


def test_rollback_safe_artifacts_not_in_output(tmp_path):
    out = tmp_path / "Output"
    reports = tmp_path / "Reports"
    out.mkdir()
    reports.mkdir()
    manifest = {
        "status": "FAIL",
        "identity": {"pass_label": "Cut Control + Required Registry PASS"},
        "findings": [{"code": "X", "detail": "y"}],
        "deferred_gaps": [{"id": "117", "reason": "deferred"}],
        "warnings": [],
        "waived": [],
    }
    arts = write_manifest_artifacts(manifest, reports, stamp="20260804T000000Z")
    assert "Output" not in arts["json"].replace("\\", "/") or "/Output/" not in arts["json"].replace("\\", "/")
    assert Path(arts["json"]).parent == reports
    assert not any(out.iterdir())


def test_journal_written_success_not_reused(tmp_path, profile):
    out = tmp_path / "Output"
    out.mkdir()
    actg = out / "quikactg.csv"
    actg.write_text("H\n1\n", encoding="utf-8")
    j = _journal()
    j.batch_started_epoch = 0.0
    j.record(
        "quikactg",
        "WRITTEN",
        source_path=str(tmp_path / "PACTG_20260630.csv"),
        output_relpath="quikactg.csv",
        row_count=1,
        extra={"output_abs_path": str(actg), "feature": "quikactg_pactg"},
    )
    assert j.tables["quikactg"]["status"] == "WRITTEN"
    assert j.tables["quikactg"].get("output_sha256")
    filled = __import__(
        "qla_core.cut_completeness_manifest", fromlist=["synthesize_missing_required"]
    ).synthesize_missing_required(profile, j, out)
    assert filled["quikactg"]["status"] == "WRITTEN"
    assert filled["quikactg"]["status"] != "REUSED_EXISTING"


def test_journal_unavailable_fail_closed(tmp_path):
    reports = tmp_path / "Reports"
    manifest = write_journal_unavailable_manifest(
        reason="simulated import failure",
        reports_dir=reports,
        package_ok=True,
        app_version="v58.70",
        launched_app_path=str(REPO / "app.py"),
    )
    assert manifest["status"] == "FAIL"
    assert manifest["handoff_ok"] is False
    assert any(f["code"] == "JOURNAL_UNAVAILABLE" for f in manifest["findings"])
    assert Path(manifest["artifacts"]["json"]).is_file()


def test_empty_run_mode_fails(profile, monkeypatch):
    monkeypatch.delenv("QLA_RUN_MODE", raising=False)
    flags = snapshot_flags(profile)
    flags["QLA_RUN_MODE"] = ""
    findings = evaluate_flags(profile, flags)
    assert any(f["code"] == "FLAG_RUN_MODE" for f in findings)


def test_valuation_date_mismatch_fails(profile, monkeypatch):
    monkeypatch.setenv("QLA_RUN_MODE", "UAT")
    monkeypatch.setenv("QLA_VALUATION_DATE", "20251231")
    # Explicit pinned date still hard-fails on mismatch (AUTO is separate).
    pinned = dict(profile)
    pinned["required_valuation_date"] = "20260630"
    flags = snapshot_flags(pinned)
    findings = evaluate_flags(pinned, flags)
    assert any(f["code"] == "VALUATION_DATE_MISMATCH" for f in findings)


def test_valuation_date_auto_accepts_matching_extract(profile, monkeypatch):
    monkeypatch.setenv("QLA_RUN_MODE", "UAT")
    # Prefer 20260731 when that package exists; else midyear 20260630 at Source root.
    src = REPO / "QLA_Migration" / "Source"
    if (src / "LifePRO_Extracts_20260731" / "PPOLC_PolicyMaster_Extract_20260731.csv").is_file():
        vd = "20260731"
    else:
        vd = "20260630"
    monkeypatch.setenv("QLA_VALUATION_DATE", vd)
    auto = dict(profile)
    auto["required_valuation_date"] = "AUTO"
    flags = snapshot_flags(auto)
    findings = evaluate_flags(auto, flags)
    assert not any(f["code"] == "VALUATION_DATE_MISMATCH" for f in findings)


def test_valuation_date_auto_rejects_unknown_cut(profile, monkeypatch):
    monkeypatch.setenv("QLA_RUN_MODE", "UAT")
    monkeypatch.setenv("QLA_VALUATION_DATE", "20990101")
    auto = dict(profile)
    auto["required_valuation_date"] = "AUTO"
    flags = snapshot_flags(auto)
    findings = evaluate_flags(auto, flags)
    assert any(f["code"] == "VALUATION_DATE_MISMATCH" for f in findings)


def test_accountability_not_proven_when_validators_skipped(registry):
    findings, results, deferred, accountability = evaluate_registry(
        registry, run_validators=False, enforce_accountability=True
    )
    assert accountability
    assert any(a["status"] == "NOT_RUN" for a in accountability)
    assert any(f["code"].startswith("ACCOUNTABILITY_NOT_PROVEN") for f in findings)
    # With enforce off (unit dry path), no false IN_DATA claim
    findings2, _, _, acc2 = evaluate_registry(
        registry, run_validators=False, enforce_accountability=False
    )
    assert not any(f["code"].startswith("ACCOUNTABILITY_NOT_PROVEN") for f in findings2)
    assert all(a["status"] == "NOT_RUN" for a in acc2)
