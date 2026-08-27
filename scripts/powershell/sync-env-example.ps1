#!/usr/bin/env pwsh
# sync-env-example.ps1 — ensure .env.example contains all env() keys from config/services.php (Laravel)
[CmdletBinding()]
param(
    [string]$EnvExample,
    [string[]]$ConfigFiles,
    [switch]$Check,
    [switch]$Fix,
    [switch]$Json,
    [switch]$Help
)
$ErrorActionPreference='Stop'
if ($Help) {
    Write-Output "Usage: ./sync-env-example.ps1 [-EnvExample .env.example] [-ConfigFiles config/services.php] [-Check] [-Fix] [-Json]"
    Write-Output "  -Check: exit 1 if missing keys (CI gate, no write)"
    Write-Output "  -Fix: append missing keys to .env.example (default if not -Check)"
    Write-Output "  Without flags: check and report, fix if missing and not -Check"
    exit 0
}
. "$PSScriptRoot/common.ps1"
$paths = Get-FeaturePathsEnv
if (-not $EnvExample) { $EnvExample = Join-Path $paths.REPO_ROOT ".env.example" }
if (-not $ConfigFiles -or $ConfigFiles.Count -eq 0) {
    $cands = @()
    $svc = Join-Path $paths.REPO_ROOT "config/services.php"
    if (Test-Path $svc) { $cands += $svc }
    # also scan config/*.php for env() usage
    if (Test-Path (Join-Path $paths.REPO_ROOT "config")) {
        Get-ChildItem -Path (Join-Path $paths.REPO_ROOT "config") -Filter *.php -ErrorAction SilentlyContinue | ForEach-Object { if ($cands -notcontains $_.FullName) { $cands += $_.FullName } }
    }
    $ConfigFiles = $cands
}
if ($ConfigFiles.Count -eq 0) {
    if ($Json) { Write-Output '{"missing":[],"envExample":"'+($EnvExample -replace '\\','\\')+'","status":"no-config"}' } else { Write-Output "No config files found" }
    exit 0
}
$keys = @()
foreach ($cf in $ConfigFiles) {
    if (-not (Test-Path $cf)) { continue }
    $txt = Get-Content $cf -Raw -ErrorAction SilentlyContinue
    if (-not $txt) { continue }
    $m = [regex]::Matches($txt, "env\(\s*['`"]([^'`"]+)['`"]")
    foreach ($mm in $m) { $k = $mm.Groups[1].Value; if ($keys -notcontains $k) { $keys += $k } }
}
if ($keys.Count -eq 0) {
    if ($Json) { Write-Output '{"missing":[],"keys":[]}' } else { Write-Output "No env() keys found in $($ConfigFiles -join ', ')" }
    exit 0
}
$exampleContent = ""
if (Test-Path $EnvExample) { $exampleContent = Get-Content $EnvExample -Raw -ErrorAction SilentlyContinue; if (-not $exampleContent) { $exampleContent = "" } }
$missing = @()
foreach ($k in $keys) {
    if ($exampleContent -notmatch "(?m)^\s*$([regex]::Escape($k))\s*=") { $missing += $k }
}
if ($Check) {
    if ($Json) {
        $missJson = ($missing | ForEach-Object { '"' + $_ + '"' }) -join ','
        Write-Output ('{"missing":['+$missJson+'],"keys":['+ (($keys | ForEach-Object { '"' + $_ + '"' }) -join ',') +'],"envExample":"'+($EnvExample -replace '\\','\\' -replace '"','\"')+'"}')
    } else {
        if ($missing.Count -gt 0) { Write-Output "Missing in .env.example: $($missing -join ', ')"; Write-Output "Run with -Fix to append" } else { Write-Output "All env keys present in .env.example" }
    }
    if ($missing.Count -gt 0) { exit 1 } else { exit 0 }
}
if ($missing.Count -gt 0) {
    if (-not (Test-Path $EnvExample)) { New-Item -ItemType File -Path $EnvExample -Force | Out-Null; $exampleContent = "" }
    $append = "`n# Added by sync-env-example.ps1 on $(Get-Date -Format yyyy-MM-dd) — from $($ConfigFiles -join ', ')`n"
    foreach ($k in $missing) { $append += "$k=`n" }
    # append LF without BOM
    $newContent = $exampleContent.TrimEnd("`r","`n") + $append
    $lf = $newContent -replace "`r`n","`n" -replace "`r","`n"
    try { Set-Content -LiteralPath $EnvExample -Value $lf -NoNewline -Encoding utf8NoBOM -ErrorAction Stop } catch {
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($EnvExample, $lf, $utf8NoBom)
    }
    if ($Json) {
        $missJson = ($missing | ForEach-Object { '"' + $_ + '"' }) -join ','
        Write-Output ('{"fixed":true,"missing":['+$missJson+'],"envExample":"'+($EnvExample -replace '\\','\\' -replace '"','\"')+'"}')
    } else { Write-Output "Added $($missing.Count) key(s) to .env.example: $($missing -join ', ')" }
} else {
    if ($Json) { Write-Output '{"fixed":false,"missing":[]}' } else { Write-Output "All env keys present in .env.example" }
}
