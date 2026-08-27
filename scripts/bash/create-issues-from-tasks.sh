#!/usr/bin/env bash
set -e
# Create GitHub issues from tasks.md grouped by User Story / Bolt (bash)
# Usage: ./create-issues-from-tasks.sh [--group-by story|phase] [--tasks-file path] [--dry-run] [--json]

GROUP_BY="story"
TASKS_FILE=""
DRY_RUN=false
JSON_MODE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --group-by) GROUP_BY="$2"; shift 2;;
    --tasks-file) TASKS_FILE="$2"; shift 2;;
    --dry-run) DRY_RUN=true; shift;;
    --json) JSON_MODE=true; shift;;
    --help|-h) echo "Usage: $0 [--group-by story|phase] [--tasks-file path] [--dry-run] [--json]"; echo "  story: one issue per [USx] (default)"; echo "  phase: one issue per Phase header"; exit 0;;
    *) echo "Unknown: $1" >&2; exit 1;;
  esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
eval $(get_feature_paths)
if [[ -z "$TASKS_FILE" ]]; then TASKS_FILE="$TASKS"; fi
if [[ ! -f "$TASKS_FILE" ]]; then
  msg="tasks.md not found: $TASKS_FILE (run /pandawa.tasks first)"
  if $JSON_MODE; then printf '{"ERROR":"%s"}\n' "$(json_escape "$msg")"; else echo "ERROR: $msg" >&2; fi
  exit 1
fi
if ! command -v gh >/dev/null 2>&1; then echo "ERROR: gh CLI not found" >&2; exit 1; fi
BRANCH="$CURRENT_BRANCH"

# Parse tasks grouped
declare -A GROUP_LABEL
declare -A GROUP_TASKS
GROUP_KEYS=()
current_phase="Tasks"
current_phase_norm="phase-unknown"

# helper to add task to group
add_to_group() {
  local key="$1" label="$2" task="$3"
  if [[ -z "${GROUP_LABEL[$key]+x}" ]]; then
    GROUP_LABEL[$key]="$label"
    GROUP_TASKS[$key]="$task"
    GROUP_KEYS+=("$key")
  else
    GROUP_TASKS[$key]="${GROUP_TASKS[$key]}"$'\n'"$task"
  fi
}

while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" =~ ^[[:space:]]*\#\#[[:space:]]*Phase[[:space:]]*[0-9]+:[[:space:]]*(.+)$ ]]; then
    current_phase="${BASH_REMATCH[1]}"
    current_phase_norm=$(echo "$current_phase" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g; s/^-//; s/-$//')
    [[ -z "$current_phase_norm" ]] && current_phase_norm="phase"
    continue
  fi
  if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*\[[\ xX]\][[:space:]]*(T[0-9]+)(.*)$ ]]; then
    task_id="${BASH_REMATCH[1]}"
    rest="${BASH_REMATCH[2]}"
    us_tag="General"
    if [[ "$rest" =~ \[(US[0-9]+)\] ]]; then us_tag="${BASH_REMATCH[1]}"
    elif [[ "$current_phase" =~ (Foundational|Setup|Polish) ]]; then us_tag=$(echo "$current_phase" | awk '{print $1}')
    fi
    key=""; label=""
    if [[ "$GROUP_BY" == "story" ]]; then
      key="$us_tag"
      if [[ "$us_tag" =~ ^US[0-9]+$ ]]; then label="$us_tag - $current_phase"; else label="$us_tag"; fi
    else
      key="$current_phase_norm"; label="$current_phase"
    fi
    task_line="- [ ] $task_id $rest"
    add_to_group "$key" "$label" "$task_line"
  fi
done < "$TASKS_FILE"

if [[ ${#GROUP_KEYS[@]} -eq 0 ]]; then echo "No tasks found in $TASKS_FILE"; exit 0; fi

# dedup: fetch existing titles
existing_titles=""
if gh issue list --limit 100 --json title --jq '.[].title' >/tmp/pandawa_existing_titles 2>/dev/null; then
  existing_titles=$(cat /tmp/pandawa_existing_titles)
fi

results_json="["; first=true
created=0; skipped=0
for key in "${GROUP_KEYS[@]}"; do
  label="${GROUP_LABEL[$key]}"
  tasks_block="${GROUP_TASKS[$key]}"
  count=$(echo "$tasks_block" | grep -c '^' || true)
  title="[$BRANCH] $label ($count tasks)"
  if [[ ${#title} -gt 240 ]]; then title="${title:0:240}"; fi
  # check duplicate
  is_dup=false
  if echo "$existing_titles" | grep -Fxq "$title"; then is_dup=true; fi
  if $is_dup; then
    $JSON_MODE || echo "[skip] $title (already exists)"
    skipped=$((skipped+1))
    if $JSON_MODE; then
      $first || results_json+=","
      results_json+="{\"title\":\"$(json_escape "$title")\",\"status\":\"skipped-duplicate\",\"tasks\":$count}"
      first=false
    fi
    continue
  fi
  if $DRY_RUN; then
    $JSON_MODE || echo "[dry-run] $title ($count tasks)"
    if $JSON_MODE; then
      $first || results_json+=","
      results_json+="{\"title\":\"$(json_escape "$title")\",\"status\":\"dry-run\",\"tasks\":$count}"
      first=false
    fi
    continue
  fi
  tmp=$(mktemp /tmp/issue-XXXXXX.md)
  {
    echo "_Generated from \`$TASKS_FILE\` ($BRANCH) — GroupBy=$GROUP_BY — tag \`$key\`_"
    echo ""
    echo "## Tasks"
    echo ""
    echo "$tasks_block"
    echo ""
    echo "_Use --body-file temp file to avoid Windows quoting issues._"
  } > "$tmp"
  set +e
  out=$(gh issue create --title "$title" --body-file "$tmp" 2>&1)
  rc=$?
  set -e
  rm -f "$tmp"
  if [[ $rc -eq 0 ]]; then
    $JSON_MODE || echo "[created] $title -> $out"
    created=$((created+1))
    if $JSON_MODE; then
      $first || results_json+=","
      results_json+="{\"title\":\"$(json_escape "$title")\",\"status\":\"created\",\"tasks\":$count}"
      first=false
    fi
  else
    $JSON_MODE || echo "[failed] $title : $out" >&2
    if $JSON_MODE; then
      $first || results_json+=","
      results_json+="{\"title\":\"$(json_escape "$title")\",\"status\":\"failed\",\"tasks\":$count,\"error\":\"$(json_escape "$out")\"}"
      first=false
    fi
  fi
  sleep 0.5
done
results_json+="]"
if $JSON_MODE; then echo "$results_json"; else echo ""; echo "Done: ${#GROUP_KEYS[@]} groups, $created created, $skipped skipped."; fi
