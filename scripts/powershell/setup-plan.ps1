#!/usr/bin/env pwsh
# Setup implementation plan for a feature

[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Output "Usage: ./setup-plan.ps1 [-Json] [-Help]"
    Write-Output "  -Json     Output results in JSON format"
    Write-Output "  -Help     Show this help message"
    exit 0
}

# Load common functions
. "$PSScriptRoot/common.ps1"

# Get all paths and variables from common functions
$paths = Get-FeaturePathsEnv

# Check if we're on a proper feature branch (only for git repos)
if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -HasGit $paths.HAS_GIT)) { 
    exit 1 
}

# Ensure the feature directory exists
New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null

# Copy plan template if it exists, otherwise note it or create empty file
$template = Join-Path $paths.REPO_ROOT '.pandawa/templates/plan-template.md'
if (Test-Path $template) { 
    Copy-Item $template $paths.IMPL_PLAN -Force
    Write-Output "Copied plan template to $($paths.IMPL_PLAN)"
    # Auto-prune generic Option 1/2/3 placeholder for known project types (e.g., Laravel monolith)
    try {
        $composer = Join-Path $paths.REPO_ROOT 'composer.json'
        $isLaravel = (Test-Path $composer) -and (Test-Path (Join-Path $paths.REPO_ROOT 'artisan')) -and ((Get-Content $composer -Raw -ErrorAction SilentlyContinue) -match 'laravel')
        if ($isLaravel) {
            $planContent = Get-Content $paths.IMPL_PLAN -Raw -ErrorAction SilentlyContinue
            if ($planContent -and $planContent.Contains('# [REMOVE IF UNUSED] Option 1')) {
                $laravelStructure = @"
``````text
# Laravel monolith (detected: composer.json + artisan)
app/
├── Http/Controllers/
├── Models/
├── Services/
└── Console/Commands/

resources/
├── views/
└── js/  # or frontend via Vite

database/
├── migrations/
└── seeders/

routes/
├── web.php
├── api.php
└── console.php

tests/
├── Feature/
└── Unit/
``````
"@
                # Replace the entire fenced block containing Option 1/2/3 with concrete structure
                $pattern = '```text\s*\r?\n# \[REMOVE IF UNUSED\] Option 1:[\s\S]*?ios/ or android/[\s\S]*?\[platform-specific structure[^\n]*\]\s*\r?\n```'
                $newContent = [regex]::Replace($planContent, $pattern, $laravelStructure)
                if ($newContent -ne $planContent) {
                    Set-Content -Path $paths.IMPL_PLAN -Value $newContent -Encoding utf8
                    Write-Output "[pandawa] Detected Laravel monolith — pruned generic Option 1/2/3 template"
                }
            }
        }
    } catch { Write-Verbose "setup-plan prune skipped: $_" }
} else {
    Write-Warning "Plan template not found at $template"
    # Create a basic plan file if template doesn't exist
    New-Item -ItemType File -Path $paths.IMPL_PLAN -Force | Out-Null
}

# Output results
if ($Json) {
    $result = [PSCustomObject]@{ 
        FEATURE_SPEC = $paths.FEATURE_SPEC
        IMPL_PLAN = $paths.IMPL_PLAN
        SPECS_DIR = $paths.FEATURE_DIR
        BRANCH = $paths.CURRENT_BRANCH
        HAS_GIT = $paths.HAS_GIT
    }
    $result | ConvertTo-Json -Compress
} else {
    Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Output "SPECS_DIR: $($paths.FEATURE_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Output "HAS_GIT: $($paths.HAS_GIT)"
}
