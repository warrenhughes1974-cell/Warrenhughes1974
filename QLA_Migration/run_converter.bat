@echo off
REM Launch from repo root so claims_analysis resolves correctly (Phase 17-20).
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%"

set QLA_RUN_MODE=UAT
set QLA_BATCH_INCLUDE_CLAIMS_UAT=1
set QLA_VALIDATE_CLAIMS_MPOLICY=1
set QLA_GENERATE_UAT_CLAIMS_DBF=1
set QLA_CLAIMS_ORCHESTRATE=1
set QLA_ENABLE_QUIKLOAN_EMIT=1
set QLA_QUIKLOAN_WRITE_OUTPUT=1
set QLA_ENABLE_QUIKBENH_LOAN_EMIT=1
set QLA_QUIKBENH_LOAN_WRITE_OUTPUT=1
set QLA_ENABLE_QUIKBENH_DIVIDEND_EMIT=1
set QLA_QUIKBENH_DIVIDEND_WRITE_OUTPUT=1
set QLA_BATCH_INCLUDE_RATE_TABLES=1
set QLA_ENABLE_QUIKISRR_EMIT=1
set QLA_ENABLE_REINSURANCE_EMIT=1
set QLA_REINSURANCE_WRITE_OUTPUT=1
REM The valuation date must match the source package being converted.
REM Never reuse a prior year-end date for a current/midyear source extract.
if not defined QLA_VALUATION_DATE (
  echo ERROR: Set QLA_VALUATION_DATE to the source valuation date before running.
  echo Example: set QLA_VALUATION_DATE=20260630
  exit /b 2
)

echo ============================================================
echo QLA Enterprise Data Integration Engine - UAT Batch Mode
echo ============================================================
echo Repo root : %REPO_ROOT%
echo RUN_MODE  : %QLA_RUN_MODE%
echo VALUATION : %QLA_VALUATION_DATE%  (QUIKRIDR.MLASTANN)
echo Engine    : v58.41 full UAT batch
echo   claims + QuikLoan + QuikBenh (loan+#114 dividend) + rates + QuikIsrr + Reinsurance
echo.
echo In the UI, set paths to QLA_Migration:
echo   Source    : QLA_Migration\Source\  (any CSV; engine resolves dated extracts)
echo   Crosswalk : QLA_Migration\Mapping\Master_Crosswalk.csv
echo   Translate : QLA_Migration\Mapping\Master_Value_Translation.csv
echo   Relational: QLA_Migration\Output\quikclid.csv
echo   Output    : QLA_Migration\Output
echo   Rulebook  : QLA_Migration\Configs\Sync_Rulebook_quikplan.csv
echo.
echo Rate Table Generation panel: "Include in full batch migration" ON
echo   (auto-set via QLA_BATCH_INCLUDE_RATE_TABLES=1)
echo.
echo Click EXECUTE FULL BATCH MIGRATION
echo ============================================================
echo.

python app.py

pause
