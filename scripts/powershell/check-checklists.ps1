#!/usr/bin/env pwsh
# check-checklists.ps1 — count checklist items without pipe-escaping issues
[CmdletBinding()]
param(
    [switch]$Json,
    [string]$ChecklistsDir,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'
if ($Help) {
    Write-Output "Usage: ./check-checklists.ps1 [-Json] [-ChecklistsDir DIR]"
    Write-Output "  DIR default: FEATURE_DIR/checklists (via common.ps1)"
    exit 0
}
. "$PSScriptRoot/common.ps1"
$paths = Get-FeaturePathsEnv
if (-not $ChecklistsDir) { $ChecklistsDir = Join-Path $paths.FEATURE_DIR "checklists" }

$esc = { param($s) '"' + ((([string]$s) -replace '\\', '\\') -replace '"', '\"') + '"' }

if (-not (Test-Path $ChecklistsDir -PathType Container)) {
    if ($Json) { Write-Output ('{"checklists_dir":' + (& $esc $ChecklistsDir) + ',"checklists":[],"overall":"PASS","total":0,"completed":0,"incomplete":0}') }
    else { Write-Output "No checklists found in $ChecklistsDir" }
    exit 0
}
$files = Get-ChildItem -Path $ChecklistsDir -Filter *.md -File -ErrorAction SilentlyContinue
if (-not $files -or $files.Count -eq 0) {
    if ($Json) { Write-Output ('{"checklists_dir":' + (& $esc $ChecklistsDir) + ',"checklists":[],"overall":"PASS","total":0,"completed":0,"incomplete":0}') }
    else { Write-Output "No checklists found in $ChecklistsDir" }
    exit 0
}
$items = @()
$totalAll = 0; $doneAll = 0; $overall = "PASS"
foreach ($f in $files) {
    $content = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $content) { $content = "" }
    $total = ([regex]::Matches($content, '^\s*-\s*\[[ xX]\]', 'Multiline')).Count
    $done = ([regex]::Matches($content, '^\s*-\s*\[[xX]\]', 'Multiline')).Count
    $incomplete = $total - $done
    $status = if ($incomplete -gt 0) { "FAIL" } else { "PASS" }
    if ($status -eq "FAIL") { $overall = "FAIL" }
    $totalAll += $total; $doneAll += $done
    $items += [PSCustomObject]@{ file=$f.Name; total=$total; completed=$done; incomplete=$incomplete; status=$status }
}
if ($Json) {
    $arr = ($items | ForEach-Object {
        '{"file":' + (& $esc $_.file) + ',"total":' + $_.total + ',"completed":' + $_.completed + ',"incomplete":' + $_.incomplete + ',"status":"' + $_.status + '"}'
    }) -join ','
    $incompleteAll = $totalAll - $doneAll
    Write-Output ('{"checklists_dir":' + (& $esc $ChecklistsDir) + ',"checklists":[' + $arr + '],"overall":"' + $overall + '","total":' + $totalAll + ',"completed":' + $doneAll + ',"incomplete":' + $incompleteAll + '}')
} else {
    Write-Output "| Checklist | Total | Completed | Incomplete | Status |"
    Write-Output "|-----------|-------|-----------|------------|--------|"
    foreach ($it in $items) {
        $mark = if ($it.status -eq "PASS") { "✓ PASS" } else { "✗ FAIL" }
        Write-Output ("| " + $it.file + " | " + $it.total + " | " + $it.completed + " | " + $it.incomplete + " | " + $mark + " |")
    }
    Write-Output "Overall: $overall"
}
