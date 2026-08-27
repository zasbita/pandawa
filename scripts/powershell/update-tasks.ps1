#!/usr/bin/env pwsh
# update-tasks.ps1 — auto-mark tasks.md checkboxes from implementation-log or explicit IDs (PS 5.1 compat)
[CmdletBinding()]
param(
    [string[]]$TaskIds,
    [string]$TasksFile,
    [string]$LogFile,
    [ValidateSet("done","running","pending","failed")][string]$Status = "done",
    [switch]$FromLog,
    [switch]$Json,
    [switch]$Help
)
$ErrorActionPreference='Stop'
if ($Help) {
    Write-Output "Usage: ./update-tasks.ps1 [-TaskIds T001,T002] [-TasksFile path] [-LogFile path] [-FromLog] [-Status done|running|pending|failed] [-Json]"
    Write-Output "  No -TaskIds and -FromLog or no args: auto-parse FEATURE_DIR/implementation-log.md for T\\d+"
    Write-Output "  PWSh 5.1 compat: no head/&&, use Select-Object -First etc"
    exit 0
}
. "$PSScriptRoot/common.ps1"
$paths = Get-FeaturePathsEnv
if (-not $TasksFile) { $TasksFile = $paths.TASKS }
if (-not (Test-Path $TasksFile -PathType Leaf)) { Write-Output "ERROR: tasks.md not found: $TasksFile"; exit 1 }
if (-not $LogFile) { $LogFile = Join-Path $paths.FEATURE_DIR "implementation-log.md" }

# resolve TaskIds
if (-not $TaskIds -or $TaskIds.Count -eq 0) {
    if (Test-Path $LogFile -PathType Leaf) {
        $txt = Get-Content $LogFile -Raw -ErrorAction SilentlyContinue
        if ($txt) {
            $m = [regex]::Matches($txt, '\bT\d{3,}\b')
            $ids = @()
            foreach ($mm in $m) { if ($ids -notcontains $mm.Value) { $ids += $mm.Value } }
            $TaskIds = $ids
        }
    }
}
if (-not $TaskIds -or $TaskIds.Count -eq 0) {
    if ($Json) { Write-Output '{"updated":0,"taskIds":[]}' } else { Write-Output "No TaskIds found (provide -TaskIds or ensure implementation-log.md contains T###)" }
    exit 0
}

$check = if ($Status -eq "done" -or $Status -eq "failed") { "X" } else { " " }
$marker = $Status
$content = Get-Content $TasksFile -Raw -ErrorAction Stop
# Normalize to LF for processing, but keep file LF without BOM on write
$orig = $content
$updated = 0
foreach ($id in $TaskIds) {
    $id = $id.Trim().Trim(',')
    if (-not $id) { continue }
    # pattern: - [ ] T001 optionally with [status] -> replace with - [X] T001 [done]
    $pattern = "(?m)^(\s*-\s*\[)[ xX](\]\s*"+[regex]::Escape($id)+@"\b)(\s*\[.*?\])?\s*"
    $replacement = "`$1$check`$2 [$marker] "
    $newContent = [regex]::Replace($content, $pattern, $replacement, 1)
    if ($newContent -ne $content) { $updated++; $content = $newContent }
    else {
        # fallback: plain - [ ] T001 without bracket marker
        $pat2 = "(?m)^(\s*-\s*\[)[ xX](\]\s*"+[regex]::Escape($id)+@"\b)"
        $rep2 = "`$1$check`$2 [$marker]"
        $new2 = [regex]::Replace($content, $pat2, $rep2, 1)
        if ($new2 -ne $content) { $updated++; $content = $new2 }
    }
}
if ($updated -gt 0 -and $content -ne $orig) {
    # write LF without BOM (PS 5.1 compat)
    $lf = $content -replace "`r`n","`n" -replace "`r","`n"
    try {
        Set-Content -LiteralPath $TasksFile -Value $lf -NoNewline -Encoding utf8NoBOM -ErrorAction Stop
    } catch {
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($TasksFile, $lf, $utf8NoBom)
    }
}
if ($Json) {
    $idsJson = '"' + ($TaskIds -join '","') + '"'
    if ($TaskIds.Count -eq 1) { $idsJson = '"' + $TaskIds[0] + '"' }
    Write-Output ('{"updated":'+$updated+',"taskIds":['+ ($TaskIds | ForEach-Object { '"' + $_ + '"' }) -join ',' + '],"status":"'+$Status+'","tasksFile":"'+ ($TasksFile -replace '\\','\\' -replace '"','\"') +'"}')
} else {
    Write-Output "Updated $updated task(s) to [$Status]: $($TaskIds -join ', ') in $TasksFile"
}
