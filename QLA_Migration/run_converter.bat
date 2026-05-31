@echo off
REM Launch from repo root so claims_analysis resolves correctly (Phase 17-20).
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%"

set QLA_RUN_MODE=UAT
set QLA_BATCH_INCLUDE_CLAIMS_UAT=1
set QLA_VALIDATE_CLAIMS_MPOLICY=1
set QLA_GENERATE_UAT_CLAIMS_DBF=1
set QLA_CLAIMS_ORCHESTRATE=1

echo ============================================================
echo QLA Enterprise Data Integration Engine - UAT Batch Mode
echo ============================================================
echo Repo root : %REPO_ROOT%
echo RUN_MODE  : %QLA_RUN_MODE%
echo.
echo In the UI, set paths to QLA_Migration:
echo   Source    : QLA_Migration\Source\quikplan.csv
echo   Crosswalk : QLA_Migration\Mapping\Master_Crosswalk.csv
echo   Translate : QLA_Migration\Mapping\Master_Value_Translation.csv
echo   Relational: QLA_Migration\Output\quikclid.csv
echo   Output    : QLA_Migration\Output
echo   Rulebook  : QLA_Migration\Configs\Sync_Rulebook_quikplan.csv
echo.
echo Click EXECUTE FULL BATCH MIGRATION
echo ============================================================
echo.

python app.py

pause
