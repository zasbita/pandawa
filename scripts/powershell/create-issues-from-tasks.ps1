#!/usr/bin/env pwsh
# Create GitHub issues from tasks.md grouped by User Story / Bolt
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$DryRun,
    [ValidateSet("story","phase")][string]$GroupBy = "story",
    [string]$TasksFile,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'

if ($Help) {
    Write-Host "Usage: ./create-issues-from-tasks.ps1 [-GroupBy story|phase] [-TasksFile path] [-DryRun] [-Json]"
    Write-Host "  GroupBy story  : one issue per User Story tag [US1], [US2], etc. (default, 3-5 issues)"
    Write-Host "  GroupBy phase  : one issue per Phase header"
    Write-Host "  DryRun         : preview without creating issues"
    Write-Host "  Uses --body-file temp file to avoid Windows quoting issues"
    Write-Host "  Dedupes via gh issue list --search before create; throttles 0.5s between creates"
    exit 0
}

. "$PSScriptRoot/common.ps1"
$paths = Get-FeaturePathsEnv
if (-not $TasksFile) { $TasksFile = $paths.TASKS }
if (-not (Test-Path $TasksFile -PathType Leaf)) {
    $msg = "tasks.md not found: $TasksFile (run /pandawa.tasks first)"
    if ($Json) { Write-Output ('{"ERROR":"' + $msg.Replace('"','\"') + '"}') } else { Write-Output "ERROR: $msg" }
    exit 1
}

# Check gh exists
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Output "ERROR: gh CLI not found (https://cli.github.com/)"
    exit 1
}

$branch = $paths.CURRENT_BRANCH
$lines = Get-Content $TasksFile
$groups = [ordered]@{}
$currentPhase = "Tasks"
$currentPhaseNorm = "phase-unknown"
foreach ($line in $lines) {
    if ($line -match '^\s*##\s*Phase\s*\d+:\s*(.+)$') {
        $currentPhase = $matches[1].Trim()
        $currentPhaseNorm = ($currentPhase.ToLower() -replace '[^a-z0-9]+','-').Trim('-')
        if (-not $currentPhaseNorm) { $currentPhaseNorm = "phase" }
        continue
    }
    if ($line -match '^\s*-\s*\[[ xX]\]\s*(T\d+)\b(.*)$') {
        $taskId = $matches[1]
        $rest = $matches[2]
        # Detect US tag
        $usTag = "General"
        if ($rest -match '\[(US\d+)\]') { $usTag = $matches[1] }
        elseif ($currentPhase -match '(Foundational|Setup|Polish)') { $usTag = $currentPhase.Split(' ')[0] }
        $key = if ($GroupBy -eq "story") { $usTag } else { $currentPhaseNorm }
        $label = if ($GroupBy -eq "story") {
            if ($usTag -match '^US\d+') { "$usTag - $currentPhase" } else { $usTag }
        } else { $currentPhase }
        if (-not $groups.Contains($key)) { $groups[$key] = @{ Label=$label; Tasks=@() } }
        $groups[$key].Tasks += "- [ ] $taskId $rest".Trim()
    }
}

if ($groups.Count -eq 0) {
    Write-Output "No tasks found in $TasksFile"
    exit 0
}

# Dedup helper: fetch existing issue titles once
$existingTitles = @()
try {
    $existingJson = gh issue list --limit 100 --json title --jq ".[].title" 2>$null
    if ($LASTEXITCODE -eq 0 -and $existingJson) { $existingTitles = $existingJson -split "`n" | Where-Object { $_ } }
} catch { }

$results = @()
foreach ($kvp in $groups.GetEnumerator()) {
    $groupKey = $kvp.Key
    $group = $kvp.Value
    $title = "[$branch] $($group.Label) ($($group.Tasks.Count) tasks)"
    # Truncate title to 256
    if ($title.Length -gt 240) { $title = $title.Substring(0,240) }
    $isDuplicate = $existingTitles -contains $title
    $bodyLines = @(
        "_Generated from ``$TasksFile`` ($branch) — GroupBy=$GroupBy — tag ``$groupKey``_"
        ""
        "## Tasks"
        ""
    ) + $group.Tasks + @("", "_Use ``gh issue create --body-file`` temp file to avoid Windows quoting issues._")
    $body = $bodyLines -join "`n"

    if ($isDuplicate) {
        $results += [PSCustomObject]@{ title=$title; status="skipped-duplicate"; tasks=$group.Tasks.Count }
        if (-not $Json) { Write-Host "[skip] $title (already exists)" }
        continue
    }
    if ($DryRun) {
        $results += [PSCustomObject]@{ title=$title; status="dry-run"; tasks=$group.Tasks.Count; body_preview=($body.Substring(0, [Math]::Min(300,$body.Length))) }
        if (-not $Json) { Write-Host "[dry-run] $title ($($group.Tasks.Count) tasks)" }
        continue
    }
    # Create temp body-file
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("issue-" + [Guid]::NewGuid().ToString("N").Substring(0,8) + ".md")
    Set-Content -Path $tmp -Value $body -Encoding utf8
    try {
        $out = gh issue create --title $title --body-file $tmp 2>&1
        if ($LASTEXITCODE -eq 0) {
            $results += [PSCustomObject]@{ title=$title; status="created"; gh_output=$out; tasks=$group.Tasks.Count }
            if (-not $Json) { Write-Host "[created] $title -> $out" }
        } else {
            $results += [PSCustomObject]@{ title=$title; status="failed"; error=$out; tasks=$group.Tasks.Count }
            if (-not $Json) { Write-Host "[failed] $title : $out" -ForegroundColor Red }
        }
    } finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 500
}

if ($Json) {
    $results | ConvertTo-Json -Depth 4 -Compress | Write-Output
} else {
    Write-Host "`nDone: $($results.Count) groups, $(($results | Where-Object status -eq 'created').Count) created, $(($results | Where-Object status -eq 'skipped-duplicate').Count) skipped."
}
