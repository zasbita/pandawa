#!/usr/bin/env bash

set -e

# Parse command line arguments
JSON_MODE=false
ARGS=()

for arg in "$@"; do
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --help|-h) 
            echo "Usage: $0 [--json]"
            echo "  --json    Output results in JSON format"
            echo "  --help    Show this help message"
            exit 0 
            ;;
        *) 
            ARGS+=("$arg") 
            ;;
    esac
done

# Get script directory and load common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get all paths and variables from common functions
eval $(get_feature_paths)

# Check if we're on a proper feature branch (only for git repos)
check_feature_branch "$CURRENT_BRANCH" "$HAS_GIT" || exit 1

# Ensure the feature directory exists
mkdir -p "$FEATURE_DIR"

# Copy plan template if it exists
TEMPLATE="$REPO_ROOT/.pandawa/templates/plan-template.md"
if [[ -f "$TEMPLATE" ]]; then
    cp "$TEMPLATE" "$IMPL_PLAN"
    echo "Copied plan template to $IMPL_PLAN"
    # Auto-prune generic Option 1/2/3 placeholder for known project types (e.g., Laravel monolith)
    if [[ -f "$REPO_ROOT/composer.json" && -f "$REPO_ROOT/artisan" ]] && grep -qi laravel "$REPO_ROOT/composer.json" 2>/dev/null; then
        if grep -q "# \[REMOVE IF UNUSED\] Option 1" "$IMPL_PLAN" 2>/dev/null; then
            # Replace the fenced block containing Option 1/2/3 with Laravel structure (portable via python if available, else sed)
            if command -v python3 >/dev/null 2>&1; then
                python3 - "$IMPL_PLAN" << 'PY'
import re, pathlib, sys
p = pathlib.Path(sys.argv[1])
text = p.read_text(encoding="utf-8")
laravel = """```text
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
```"""
pattern = r'```text\s*\n# \[REMOVE IF UNUSED\] Option 1:[\s\S]*?ios/ or android/[\s\S]*?\[platform-specific structure[^\n]*\]\s*\n```'
new, n = re.subn(pattern, laravel, text)
if n:
    p.write_text(new, encoding="utf-8")
    print("[pandawa] Detected Laravel monolith — pruned generic Option 1/2/3 template")
PY
            else
                echo "[pandawa] Detected Laravel but python3 not available — skipping prune"
            fi
        fi
    fi
else
    echo "Warning: Plan template not found at $TEMPLATE"
    # Create a basic plan file if template doesn't exist
    touch "$IMPL_PLAN"
fi

# Output results
if $JSON_MODE; then
    # HAS_GIT emitted as a JSON boolean (true/false, unquoted) to match the PowerShell variant
    printf '{"FEATURE_SPEC":"%s","IMPL_PLAN":"%s","SPECS_DIR":"%s","BRANCH":"%s","HAS_GIT":%s}\n' \
        "$(json_escape "$FEATURE_SPEC")" "$(json_escape "$IMPL_PLAN")" "$(json_escape "$FEATURE_DIR")" "$(json_escape "$CURRENT_BRANCH")" "$HAS_GIT"
else
    echo "FEATURE_SPEC: $FEATURE_SPEC"
    echo "IMPL_PLAN: $IMPL_PLAN" 
    echo "SPECS_DIR: $FEATURE_DIR"
    echo "BRANCH: $CURRENT_BRANCH"
    echo "HAS_GIT: $HAS_GIT"
fi

