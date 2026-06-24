<#
.SYNOPSIS
    Phase 1 source governance - sync Current/ to flat Source/ for engine compatibility.

.DESCRIPTION
    Copies all CSV files from QLA_Migration/Source/Current/ into QLA_Migration/Source/
    without deleting existing files at the flat Source level.

    Interim governance bridge (optional — engine v57.24+ accepts LifePRO names directly):
      RelationshipNameAddress_Extract*.csv is used for quikclnt, quikclid, quikbenf
      without copying to quikclid.csv / quikbenf.csv.

    Legacy bridge copies (rollback only):
      RelationshipNameAddress_Extract.csv -> quikclid.csv
      RelationshipNameAddress_Extract.csv -> quikbenf.csv

    Does NOT modify app.py or conversion engine logic.

.PARAMETER SourceRoot
    Optional override for QLA_Migration/Source path.

.EXAMPLE
    .\sync_current_to_source.ps1
#>
[CmdletBinding()]
param(
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"

function Resolve-SourceRoot {
    param([string]$Override, [string]$ToolsDir)
    if ($Override -and (Test-Path -LiteralPath $Override)) {
        return (Resolve-Path -LiteralPath $Override).Path
    }
    $candidate = Join-Path (Split-Path -Parent $ToolsDir) "Source"
    if (-not (Test-Path -LiteralPath $candidate)) {
        throw "Source folder not found: $candidate"
    }
    return (Resolve-Path -LiteralPath $candidate).Path
}

function Write-SyncLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message"
}

$sourceRoot = Resolve-SourceRoot -Override $SourceRoot -ToolsDir $PSScriptRoot
$currentDir = Join-Path $sourceRoot "Current"

if (-not (Test-Path -LiteralPath $currentDir)) {
    throw "Current folder not found: $currentDir"
}

$csvFiles = Get-ChildItem -LiteralPath $currentDir -Filter "*.csv" -File
if (-not $csvFiles -or $csvFiles.Count -eq 0) {
    throw "No CSV files found in Current/: $currentDir"
}

Write-SyncLog "Source root: $sourceRoot"
Write-SyncLog "Current folder: $currentDir"
Write-SyncLog "Copying $($csvFiles.Count) CSV file(s) from Current/ to flat Source/ (no deletions)"

$copied = @()
foreach ($file in $csvFiles) {
    $dest = Join-Path $sourceRoot $file.Name
    Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
    $copied += $file.Name
    Write-SyncLog "  Copied: $($file.Name)"
}

$rnaName = "RelationshipNameAddress_Extract.csv"
$rnaPath = Join-Path $currentDir $rnaName

if (-not (Test-Path -LiteralPath $rnaPath)) {
    $rnaPath = Join-Path $sourceRoot $rnaName
}

if (Test-Path -LiteralPath $rnaPath) {
    $bridgeTargets = @("quikclid.csv", "quikbenf.csv")
    foreach ($target in $bridgeTargets) {
        $dest = Join-Path $sourceRoot $target
        Copy-Item -LiteralPath $rnaPath -Destination $dest -Force
        Write-SyncLog "  Bridge copy: $rnaName -> $target"
        if ($copied -notcontains $target) {
            $copied += $target
        }
    }
} else {
    Write-SyncLog "WARNING: $rnaName not found - quikclid.csv / quikbenf.csv not updated"
}

Write-SyncLog "Sync complete. Files touched: $($copied.Count)"
Write-SyncLog "Engine reads flat Source/ - no application changes required."
