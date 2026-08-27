#!/usr/bin/env bash
# update-tasks.sh — auto-mark tasks.md checkboxes (bash, no head/&& issues)
set -e
TASK_IDS=""
TASKS_FILE=""
LOG_FILE=""
STATUS="done"
JSON_MODE=false

prev=""
for arg in "$@"; do
  # handle --task-ids T001,T002 split
  if [[ "$prev" == "--task-ids" ]]; then TASK_IDS="$arg"; prev=""; continue; fi
  if [[ "$prev" == "--tasks-file" ]]; then TASKS_FILE="$arg"; prev=""; continue; fi
  if [[ "$prev" == "--log-file" ]]; then LOG_FILE="$arg"; prev=""; continue; fi
  case "$arg" in
    --task-ids) prev="--task-ids" ;;
    --task-ids=*) TASK_IDS="${arg#--task-ids=}" ;;
    --tasks-file) prev="--tasks-file" ;;
    --tasks-file=*) TASKS_FILE="${arg#--tasks-file=}" ;;
    --log-file) prev="--log-file" ;;
    --log-file=*) LOG_FILE="${arg#--log-file=}" ;;
    --status) prev="--status" ;; --status=*) STATUS="${arg#--status=}" ;;
    --json) JSON_MODE=true ;;
    --from-log) FROM_LOG=true ;;
    --help|-h) echo "Usage: $0 [--task-ids T001,T002] [--tasks-file path] [--log-file path] [--from-log] [--status done|running|pending|failed] [--json]"; exit 0 ;;
    *)
      if [[ "$prev" == "--status" ]]; then STATUS="$arg"; prev=""; continue; fi
      echo "Unknown: $arg" >&2; exit 1
      ;;
  esac
done
if [[ "$prev" == "--task-ids" ]]; then echo "ERROR: --task-ids requires value" >&2; exit 1; fi

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
eval $(get_feature_paths)
if [[ -z "$TASKS_FILE" ]]; then TASKS_FILE="$TASKS"; fi
if [[ -z "$LOG_FILE" ]]; then LOG_FILE="$FEATURE_DIR/implementation-log.md"; fi
if [[ ! -f "$TASKS_FILE" ]]; then echo "ERROR: tasks.md not found: $TASKS_FILE" >&2; exit 1; fi

# fallback: parse log for T###
if [[ -z "$TASK_IDS" ]]; then
  if [[ -f "$LOG_FILE" ]]; then
    TASK_IDS=$(grep -oE '\bT[0-9]{3,}\b' "$LOG_FILE" 2>/dev/null | awk '!seen[$0]++' | paste -sd, -)
  fi
fi
if [[ -z "$TASK_IDS" ]]; then
  if $JSON_MODE; then echo '{"updated":0,"taskIds":[]}'; else echo "No TaskIds found (provide --task-ids or ensure implementation-log.md contains T###)"; fi
  exit 0
fi

# normalize comma/space separated
TASK_IDS=$(echo "$TASK_IDS" | tr ',' ' ' | tr -s ' ' | sed 's/^ *//;s/ *$//')
CHECK=" "; [[ "$STATUS" == "done" || "$STATUS" == "failed" ]] && CHECK="X"
MARKER="$STATUS"
updated=0
for id in $TASK_IDS; do
  # try to update line: - [ ] T001 -> - [X] T001 [done]
  # use python for robust regex (fallback to sed if no python)
  if command -v python3 >/dev/null 2>&1; then _py="python3"; elif command -v python >/dev/null 2>&1; then _py="python"; else _py=""; fi
  if [[ -n "$_py" ]]; then
    before=$(grep -cE "^\s*-\s*\[[ xX]\]\s*$id\b" "$TASKS_FILE" || true)
    $_py - "$TASKS_FILE" "$id" "$CHECK" "$MARKER" << 'PY'
import re, sys
path, tid, check, marker = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
p = open(path, encoding="utf-8").read()
pat = rf"(?m)^(\s*-\s*\[)[ xX](\]\s*{re.escape(tid)}\b)(\s*\[.*?\])?\s*"
rep = rf"\g<1>{check}\g<2> [{marker}] "
new, n = re.subn(pat, rep, p, count=1)
if n==0:
    pat2 = rf"(?m)^(\s*-\s*\[)[ xX](\]\s*{re.escape(tid)}\b)"
    rep2 = rf"\g<1>{check}\g<2> [{marker}]"
    new, n = re.subn(pat2, rep2, p, count=1)
if n>0:
    open(path, "w", encoding="utf-8", newline="\n").write(new)
PY
    after=$(grep -cE "^\s*-\s*\[[ xX]\]\s*$id\s*\[$MARKER\]" "$TASKS_FILE" || true)
    if [[ "$after" -gt 0 ]]; then updated=$((updated+1)); fi
  else
    # sed fallback
    if grep -qE "^\s*-\s*\[ \] *$id\b" "$TASKS_FILE"; then
      sed -i.bak -E "s/^(\s*-\s*\[) \[(\] *$id\b)/\1$CHECK\2 [$MARKER]/" "$TASKS_FILE" && rm -f "$TASKS_FILE.bak"
      updated=$((updated+1))
    fi
  fi
done
if $JSON_MODE; then
  # build json array
  ids_json=$(echo "$TASK_IDS" | awk '{for(i=1;i<=NF;i++) printf "%s\"%s\"", (i>1?",":""), $i}')
  printf '{"updated":%d,"taskIds":[%s],"status":"%s","tasksFile":"%s"}\n' "$updated" "$ids_json" "$STATUS" "$(printf '%s' "$TASKS_FILE" | sed 's/\\/\\\\/g; s/"/\\"/g')"
else
  echo "Updated $updated task(s) to [$STATUS]: $TASK_IDS in $TASKS_FILE"
fi
