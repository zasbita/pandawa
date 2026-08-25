#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build Pandawa template release archives for each supported AI assistant and script type.
# Usage: .github/workflows/scripts/create-release-packages.sh <version>
#   Version argument should include leading 'v'.
#   Optionally set AGENTS and/or SCRIPTS env vars to limit what gets built.
#     AGENTS  : space or comma separated subset of: claude gemini copilot cursor-agent qwen opencode windsurf codex amp shai bob (default: all)
#     SCRIPTS : space or comma separated subset of: sh ps (default: both)
#   Examples:
#     AGENTS=claude SCRIPTS=sh $0 v0.2.0
#     AGENTS="copilot,gemini" $0 v0.2.0
#     SCRIPTS=ps $0 v0.2.0

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version-with-v-prefix>" >&2
  exit 1
fi
NEW_VERSION="$1"
if [[ ! $NEW_VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must look like v0.0.0" >&2
  exit 1
fi

echo "Building release packages for $NEW_VERSION"

# Create and use .genreleases directory for all build artifacts
GENRELEASES_DIR=".genreleases"
mkdir -p "$GENRELEASES_DIR"
rm -rf "$GENRELEASES_DIR"/* || true

rewrite_paths() {
  # $1: this agent's commands dir, relative to the generated project root (e.g. .claude/commands)
  # $2: this agent's command file extension (e.g. md, toml, agent.md)
  #
  # templates/commands/*.md never ships as-is (see the `-not -path "templates/commands/*"`
  # exclusion below) — each file is transformed per-agent into "$commands_rel_dir/pandawa.<name>.$ext".
  # A cross-reference like "Read `/templates/commands/specify.md`" must be rewritten to that
  # real sibling path, NOT to the generic `.pandawa/templates/` rule below (which only applies to
  # templates/ content that actually gets copied verbatim, and does not exist for templates/commands/).
  local commands_rel_dir=$1 ext=$2
  sed -E \
    -e "s@/?templates/commands/([a-zA-Z0-9_-]+)\.md@${commands_rel_dir}/pandawa.\1.${ext}@g" \
    -e 's@(/?)memory/@.pandawa/memory/@g' \
    -e 's@(/?)scripts/@.pandawa/scripts/@g' \
    -e 's@(/?)templates/@.pandawa/templates/@g'
}

generate_commands() {
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4 script_variant=$5 commands_rel_dir=$6
  mkdir -p "$output_dir"
  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name description script_command agent_script_command body
    name=$(basename "$template" .md)
    
    # Normalize line endings
    file_content=$(tr -d '\r' < "$template")
    
    # Extract description and script command from YAML frontmatter.
    # Fed via a here-string (<<<), NOT a pipe from printf: awk's `exit` below terminates
    # reading early, and if fed through a live pipe that can SIGPIPE the writer (printf)
    # once its buffer fills and awk stops reading — pipefail then aborts the whole script
    # (observed intermittently in CI as `exit 141`). A here-string has bash write the
    # content to an fd before awk ever starts, so there's no concurrent writer to signal.
    description=$(awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}' <<< "$file_content")
    script_command=$(awk -v sv="$script_variant" '/^[[:space:]]*'"$script_variant"':[[:space:]]*/ {sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, ""); print; exit}' <<< "$file_content")

    if [[ -z $script_command ]]; then
      echo "Warning: no script command found for $script_variant in $template" >&2
      script_command="(Missing script command for $script_variant)"
    fi

    # Extract agent_script command from YAML frontmatter if present (same here-string reasoning)
    agent_script_command=$(awk '
      /^agent_scripts:$/ { in_agent_scripts=1; next }
      in_agent_scripts && /^[[:space:]]*'"$script_variant"':[[:space:]]*/ {
        sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, "")
        print
        exit
      }
      in_agent_scripts && /^[a-zA-Z]/ { in_agent_scripts=0 }
    ' <<< "$file_content")
    
    # Replace {SCRIPT} placeholder with the script command
    body=$(printf '%s\n' "$file_content" | sed "s|{SCRIPT}|${script_command}|g")
    
    # Replace {AGENT_SCRIPT} placeholder with the agent script command if found
    if [[ -n $agent_script_command ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT}|${agent_script_command}|g")
    fi
    
    # Remove the scripts: and agent_scripts: sections from frontmatter while preserving YAML structure
    body=$(printf '%s\n' "$body" | awk '
      /^---$/ { print; if (++dash_count == 1) in_frontmatter=1; else in_frontmatter=0; next }
      in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^agent_scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^[a-zA-Z].*:/ && skip_scripts { skip_scripts=0 }
      in_frontmatter && skip_scripts && /^[[:space:]]/ { next }
      { print }
    ')
    
    # Apply other substitutions
    body=$(printf '%s\n' "$body" | sed "s/{ARGS}/$arg_format/g" | sed "s/__AGENT__/$agent/g" | rewrite_paths "$commands_rel_dir" "$ext")
    
    case $ext in
      toml)
        body=$(printf '%s\n' "$body" | sed 's/\\/\\\\/g')
        { echo "description = \"$description\""; echo; echo "prompt = \"\"\""; echo "$body"; echo "\"\"\""; } > "$output_dir/pandawa.$name.$ext" ;;
      md)
        echo "$body" > "$output_dir/pandawa.$name.$ext" ;;
      agent.md)
        echo "$body" > "$output_dir/pandawa.$name.$ext" ;;
    esac
  done
}

generate_copilot_prompts() {
  local agents_dir=$1 prompts_dir=$2
  mkdir -p "$prompts_dir"
  
  # Generate a .prompt.md file for each .agent.md file
  for agent_file in "$agents_dir"/pandawa.*.agent.md; do
    [[ -f "$agent_file" ]] || continue
    
    local basename=$(basename "$agent_file" .agent.md)
    local prompt_file="$prompts_dir/${basename}.prompt.md"
    
    # Create prompt file with agent frontmatter
    cat > "$prompt_file" <<EOF
---
agent: ${basename}
---
EOF
  done
}

build_variant() {
  local agent=$1 script=$2
  local base_dir="$GENRELEASES_DIR/sdd-${agent}-package-${script}"
  echo "Building $agent ($script) package..."
  mkdir -p "$base_dir"
  
  # Copy base structure but filter scripts by variant
  # Create .pandawa structure
  SPEC_DIR="$base_dir/.pandawa"
  mkdir -p "$SPEC_DIR"
  
  [[ -d memory ]] && { cp -r memory "$SPEC_DIR/"; echo "Copied memory -> .pandawa"; }
  
  # Only copy the relevant script variant directory
  if [[ -d scripts ]]; then
    mkdir -p "$SPEC_DIR/scripts"
    case $script in
      sh)
        [[ -d scripts/bash ]] && { cp -r scripts/bash "$SPEC_DIR/scripts/"; echo "Copied scripts/bash -> .pandawa/scripts"; }
        # Copy any script files that aren't in variant-specific directories
        find scripts -maxdepth 1 -type f -exec cp {} "$SPEC_DIR/scripts/" \; 2>/dev/null || true
        ;;
      ps)
        [[ -d scripts/powershell ]] && { cp -r scripts/powershell "$SPEC_DIR/scripts/"; echo "Copied scripts/powershell -> .pandawa/scripts"; }
        # Copy any script files that aren't in variant-specific directories
        find scripts -maxdepth 1 -type f -exec cp {} "$SPEC_DIR/scripts/" \; 2>/dev/null || true
        ;;
    esac
  fi
  
  [[ -d templates ]] && { mkdir -p "$SPEC_DIR/templates"; find templates -type f -not -path "templates/commands/*" -not -name "vscode-settings.json" -exec cp --parents {} "$SPEC_DIR"/ \; ; echo "Copied templates -> .pandawa/templates"; }
  
  # NOTE: We substitute {ARGS} internally. Outward tokens differ intentionally:
  #   * Markdown/prompt (claude, copilot, cursor-agent, opencode): $ARGUMENTS
  #   * TOML (gemini, qwen): {{args}}
  # This keeps formats readable without extra abstraction.

  case $agent in
    claude)
      mkdir -p "$base_dir/.claude/commands"
      generate_commands claude md "\$ARGUMENTS" "$base_dir/.claude/commands" "$script" ".claude/commands" ;;
    gemini)
      mkdir -p "$base_dir/.gemini/commands"
      generate_commands gemini toml "{{args}}" "$base_dir/.gemini/commands" "$script" ".gemini/commands"
      [[ -f agent_templates/gemini/GEMINI.md ]] && cp agent_templates/gemini/GEMINI.md "$base_dir/GEMINI.md" ;;
    copilot)
      mkdir -p "$base_dir/.github/agents"
      generate_commands copilot agent.md "\$ARGUMENTS" "$base_dir/.github/agents" "$script" ".github/agents"
      # Generate companion prompt files
      generate_copilot_prompts "$base_dir/.github/agents" "$base_dir/.github/prompts"
      # Create VS Code workspace settings
      mkdir -p "$base_dir/.vscode"
      [[ -f templates/vscode-settings.json ]] && cp templates/vscode-settings.json "$base_dir/.vscode/settings.json"
      ;;
    cursor-agent)
      mkdir -p "$base_dir/.cursor/commands"
      generate_commands cursor-agent md "\$ARGUMENTS" "$base_dir/.cursor/commands" "$script" ".cursor/commands" ;;
    qwen)
      mkdir -p "$base_dir/.qwen/commands"
      generate_commands qwen toml "{{args}}" "$base_dir/.qwen/commands" "$script" ".qwen/commands"
      [[ -f agent_templates/qwen/QWEN.md ]] && cp agent_templates/qwen/QWEN.md "$base_dir/QWEN.md" ;;
    opencode)
      mkdir -p "$base_dir/.opencode/command"
      generate_commands opencode md "\$ARGUMENTS" "$base_dir/.opencode/command" "$script" ".opencode/command" ;;
    windsurf)
      mkdir -p "$base_dir/.windsurf/workflows"
      generate_commands windsurf md "\$ARGUMENTS" "$base_dir/.windsurf/workflows" "$script" ".windsurf/workflows" ;;
    codex)
      mkdir -p "$base_dir/.codex/prompts"
      generate_commands codex md "\$ARGUMENTS" "$base_dir/.codex/prompts" "$script" ".codex/prompts" ;;
    kilocode)
      mkdir -p "$base_dir/.kilocode/workflows"
      generate_commands kilocode md "\$ARGUMENTS" "$base_dir/.kilocode/workflows" "$script" ".kilocode/workflows" ;;
    auggie)
      mkdir -p "$base_dir/.augment/commands"
      generate_commands auggie md "\$ARGUMENTS" "$base_dir/.augment/commands" "$script" ".augment/commands" ;;
    roo)
      mkdir -p "$base_dir/.roo/commands"
      generate_commands roo md "\$ARGUMENTS" "$base_dir/.roo/commands" "$script" ".roo/commands" ;;
    codebuddy)
      mkdir -p "$base_dir/.codebuddy/commands"
      generate_commands codebuddy md "\$ARGUMENTS" "$base_dir/.codebuddy/commands" "$script" ".codebuddy/commands" ;;
    qoder)
      mkdir -p "$base_dir/.qoder/commands"
      generate_commands qoder md "\$ARGUMENTS" "$base_dir/.qoder/commands" "$script" ".qoder/commands" ;;
    amp)
      mkdir -p "$base_dir/.agents/commands"
      generate_commands amp md "\$ARGUMENTS" "$base_dir/.agents/commands" "$script" ".agents/commands" ;;
    shai)
      mkdir -p "$base_dir/.shai/commands"
      generate_commands shai md "\$ARGUMENTS" "$base_dir/.shai/commands" "$script" ".shai/commands" ;;
    q)
      mkdir -p "$base_dir/.amazonq/prompts"
      generate_commands q md "\$ARGUMENTS" "$base_dir/.amazonq/prompts" "$script" ".amazonq/prompts" ;;
    bob)
      mkdir -p "$base_dir/.bob/commands"
      generate_commands bob md "\$ARGUMENTS" "$base_dir/.bob/commands" "$script" ".bob/commands" ;;
  esac
  ( cd "$base_dir" && zip -r "../pandawa-template-${agent}-${script}-${NEW_VERSION}.zip" . )
  echo "Created $GENRELEASES_DIR/pandawa-template-${agent}-${script}-${NEW_VERSION}.zip"
}

# Determine agent list
ALL_AGENTS=(claude gemini copilot cursor-agent qwen opencode windsurf codex kilocode auggie roo codebuddy amp shai q bob qoder)
ALL_SCRIPTS=(sh ps)

norm_list() {
  # convert comma+space separated -> line separated unique while preserving order of first occurrence
  tr ',\n' '  ' | awk '{for(i=1;i<=NF;i++){if(!seen[$i]++){printf((out?"\n":"") $i);out=1}}}END{printf("\n")}'
}

validate_subset() {
  local type=$1; shift; local -n allowed=$1; shift; local items=("$@")
  local invalid=0
  for it in "${items[@]}"; do
    local found=0
    for a in "${allowed[@]}"; do [[ $it == "$a" ]] && { found=1; break; }; done
    if [[ $found -eq 0 ]]; then
      echo "Error: unknown $type '$it' (allowed: ${allowed[*]})" >&2
      invalid=1
    fi
  done
  return $invalid
}

if [[ -n ${AGENTS:-} ]]; then
  mapfile -t AGENT_LIST < <(printf '%s' "$AGENTS" | norm_list)
  validate_subset agent ALL_AGENTS "${AGENT_LIST[@]}" || exit 1
else
  AGENT_LIST=("${ALL_AGENTS[@]}")
fi

if [[ -n ${SCRIPTS:-} ]]; then
  mapfile -t SCRIPT_LIST < <(printf '%s' "$SCRIPTS" | norm_list)
  validate_subset script ALL_SCRIPTS "${SCRIPT_LIST[@]}" || exit 1
else
  SCRIPT_LIST=("${ALL_SCRIPTS[@]}")
fi

echo "Agents: ${AGENT_LIST[*]}"
echo "Scripts: ${SCRIPT_LIST[*]}"

for agent in "${AGENT_LIST[@]}"; do
  for script in "${SCRIPT_LIST[@]}"; do
    build_variant "$agent" "$script"
  done
done

# Domain profiles are NOT packaged/released here — they live in the separate
# pandawa-marketplace-tooling repo (profiles/<id>/, registered in its root profiles.json)
# and pandawa fetches a profile's folder live from there (GitLab repository-archive API
# scoped to its path) on `pandawa init --profile`. Nothing to build/exclude in this repo.

echo "Archives in $GENRELEASES_DIR:"
ls -1 "$GENRELEASES_DIR"/pandawa-*-"${NEW_VERSION}".zip

