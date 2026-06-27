<#
.SYNOPSIS
    Phase 1 pre-flight source package validation (report only).

.DESCRIPTION
    Validates required source files, file sizes, row counts, and manifest presence.
    Outputs PASS, WARNING, or FAIL. Does not modify files or stop conversion.

.PARAMETER SourceRoot
    Folder to validate. Defaults to QLA_Migration/Source (flat folder).

.PARAMETER ManifestPath
    Optional path to SOURCE_MANIFEST.json. Defaults to SourceRoot/SOURCE_MANIFEST.json.

.EXAMPLE
    .\validate_source_package.ps1
    .\validate_source_package.ps1 -SourceRoot "..\Source\Current"
#>
[CmdletBinding()]
param(
    [string]$SourceRoot = "",
    [string]$ManifestPath = ""
)

$ErrorActionPreference = "Continue"

$RequiredFiles = @(
    @{ Name = "quikmstr.csv"; Required = $true; BaselineRows = 5084 }
    @{ Name = "PPBEN.csv"; Required = $true; BaselineRows = 11699 }
    @{ Name = "PPBENTYP.csv"; Required = $true; BaselineRows = 7003 }
    @{ Name = "RelationshipNameAddress_Extract.csv"; Required = $true; BaselineRows = 46877 }
    @{ Name = "PACTG_Accounting_Extract20260427.csv"; Required = $true; BaselineRows = 399059 }
    @{ Name = "PAGNT.csv"; Required = $true; BaselineRows = 4844 }
    @{ Name = "PPACH.csv"; Required = $true; BaselineRows = 7799 }
    @{ Name = "quikplan_source.csv"; Required = $true; BaselineRows = 142 }
    @{ Name = "PLOAN.csv"; Required = $false; BaselineRows = 93502 }
    @{ Name = "quikclid.csv"; Required = $true; BaselineRows = 0 }
    @{ Name = "quikbenf.csv"; Required = $true; BaselineRows = 0 }
)

function Resolve-DefaultSourceRoot {
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

function Get-CsvRowCount {
    param([string]$FilePath)
    try {
        $lineCount = 0
        $reader = [System.IO.File]::OpenText($FilePath)
        try {
            while ($null -ne $reader.ReadLine()) {
                $lineCount++
            }
        } finally {
            $reader.Close()
        }
        if ($lineCount -le 0) { return 0 }
        return [Math]::Max(0, $lineCount - 1)
    } catch {
        return -1
    }
}

function Resolve-ManifestPath {
    param([string]$Root, [string]$Override)
    if ($Override) { return $Override }
    $primary = Join-Path $Root "SOURCE_MANIFEST.json"
    if (Test-Path -LiteralPath $primary) { return $primary }
    $template = Join-Path $Root "SOURCE_MANIFEST_TEMPLATE.json"
    if (Test-Path -LiteralPath $template) { return $template }
    return $primary
}

$sourceRoot = Resolve-DefaultSourceRoot -Override $SourceRoot -ToolsDir $PSScriptRoot
$manifestFile = Resolve-ManifestPath -Root $sourceRoot -Override $ManifestPath

$failCount = 0
$warnCount = 0
$passCount = 0
$results = @()

Write-Host ""
Write-Host "========================================"
Write-Host " Source Package Validation (Phase 1)"
Write-Host "========================================"
Write-Host "Folder: $sourceRoot"
Write-Host "Time:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

foreach ($entry in $RequiredFiles) {
    $filePath = Join-Path $sourceRoot $entry.Name
    $status = "PASS"
    $detail = ""

    if (-not (Test-Path -LiteralPath $filePath)) {
        if ($entry.Required) {
            $status = "FAIL"
            $detail = "Missing required file"
            $failCount++
        } else {
            $status = "WARNING"
            $detail = "Optional file not present"
            $warnCount++
        }
    } else {
        $size = (Get-Item -LiteralPath $filePath).Length
        if ($size -le 0) {
            $status = "FAIL"
            $detail = "File size is 0 bytes"
            $failCount++
        } else {
            $rows = Get-CsvRowCount -FilePath $filePath
            if ($rows -lt 0) {
                $status = "WARNING"
                $detail = "Could not count rows"
                $warnCount++
            } elseif ($rows -eq 0) {
                $status = "FAIL"
                $detail = "No data rows detected"
                $failCount++
            } else {
                $detail = "Size=$size bytes, Rows=$rows"
                if ($entry.BaselineRows -gt 0) {
                    $pct = [Math]::Abs($rows - $entry.BaselineRows) / $entry.BaselineRows * 100
                    if ($pct -gt 5) {
                        $status = "WARNING"
                        $detail += " (>5% vs baseline $($entry.BaselineRows))"
                        $warnCount++
                    } else {
                        $passCount++
                    }
                } else {
                    $passCount++
                }
            }
        }
    }

    $results += [PSCustomObject]@{
        File   = $entry.Name
        Status = $status
        Detail = $detail
    }

    $color = switch ($status) {
        "FAIL"    { "Red" }
        "WARNING" { "Yellow" }
        default   { "Green" }
    }
    Write-Host ("[{0}] {1,-45} {2}" -f $status, $entry.Name, $detail) -ForegroundColor $color
}

Write-Host ""
Write-Host "--- Manifest ---"
if (Test-Path -LiteralPath $manifestFile) {
    Write-Host "[PASS] Manifest found: $manifestFile" -ForegroundColor Green
    $passCount++
    try {
        $null = Get-Content -LiteralPath $manifestFile -Raw | ConvertFrom-Json
        Write-Host "[PASS] Manifest JSON is valid" -ForegroundColor Green
        $passCount++
    } catch {
        Write-Host "[WARNING] Manifest JSON parse error: $($_.Exception.Message)" -ForegroundColor Yellow
        $warnCount++
    }
} else {
    Write-Host "[WARNING] No SOURCE_MANIFEST.json or template at: $manifestFile" -ForegroundColor Yellow
    $warnCount++
}

Write-Host ""
Write-Host "========================================"
$overall = "PASS"
if ($failCount -gt 0) {
    $overall = "FAIL"
} elseif ($warnCount -gt 0) {
    $overall = "WARNING"
}

$overallColor = switch ($overall) {
    "FAIL"    { "Red" }
    "WARNING" { "Yellow" }
    default   { "Green" }
}

Write-Host (" OVERALL: {0}" -f $overall) -ForegroundColor $overallColor
Write-Host (" Checks:  PASS=$passCount  WARNING=$warnCount  FAIL=$failCount")
Write-Host "========================================"
Write-Host ""
Write-Host "Note: Validation is advisory only. Does not modify files or stop conversion."
Write-Host ""

exit $(if ($overall -eq "FAIL") { 1 } elseif ($overall -eq "WARNING") { 2 } else { 0 })
