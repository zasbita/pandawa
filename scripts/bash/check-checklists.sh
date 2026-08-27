#!/usr/bin/env bash
# check-checklists.sh — count checklist items without PowerShell pipe escaping
# Usage: ./check-checklists.sh [--json] [--checklists-dir DIR]
set -e
JSON_MODE=false
CHECKLISTS_DIR=""

for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --help|-h) echo "Usage: $0 [--json] [--checklists-dir DIR]"; echo "  DIR default: FEATURE_DIR/checklists (via common.sh)"; exit 0 ;;
    --checklists-dir) echo "ERROR: --checklists-dir requires value" >&2; exit 1 ;;
    --checklists-dir=*) CHECKLISTS_DIR="${arg#--checklists-dir=}" ;;
    *)
      if [[ "$prev" == "--checklists-dir" ]]; then CHECKLISTS_DIR="$arg"; prev=""; continue; fi
      if [[ "$arg" == "--checklists-dir" ]]; then prev="--checklists-dir"; continue; fi
      echo "ERROR: Unknown option '$arg'" >&2; exit 1
      ;;
  esac
done
# handle --checklists-dir <val> split
if [[ "$CHECKLISTS_DIR" == "" ]]; then
  for ((i=1;i<=$#;i++)); do
    eval "a=\${$i}"; eval "b=\${$((i+1))}"
    if [[ "$a" == "--checklists-dir" && -n "$b" && "$b" != --* ]]; then CHECKLISTS_DIR="$b"; fi
  done
fi

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
eval $(get_feature_paths)

if [[ -z "$CHECKLISTS_DIR" ]]; then
  CHECKLISTS_DIR="$FEATURE_DIR/checklists"
fi

# collect
results=()
total_all=0; done_all=0
shopt -s nullglob 2>/dev/null || true
files=("$CHECKLISTS_DIR"/*.md)
if [[ ! -d "$CHECKLISTS_DIR" || ${#files[@]} -eq 0 || ! -e "${files[0]}" ]]; then
  if $JSON_MODE; then
    printf '{"checklists_dir":"%s","checklists":[],"overall":"PASS","total":0,"completed":0,"incomplete":0}\n' "$(json_escape "$CHECKLISTS_DIR")"
  else
    echo "No checklists found in $CHECKLISTS_DIR"
  fi
  exit 0
fi

# json helpers
json_escape() { local s="$1"; s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; printf '%s' "$s"; }

overall="PASS"
json_items=""
for f in "${files[@]}"; do
  [[ -f "$f" ]] || continue
  name=$(basename "$f")
  # count lines matching - [ ] / - [x]
  total=$(grep -Ec '^[[:space:]]*-[[:space:]]*\[[ xX]\]' "$f" 2>/dev/null || echo 0)
  done=$(grep -Ec '^[[:space:]]*-[[:space:]]*\[[xX]\]' "$f" 2>/dev/null || echo 0)
  total=$(echo "$total" | tr -d '[:space:]'); done=$(echo "$done" | tr -d '[:space:]')
  incomplete=$((total - done))
  status="PASS"; [[ $incomplete -gt 0 ]] && status="FAIL" && overall="FAIL"
  total_all=$((total_all + total)); done_all=$((done_all + done))
  if $JSON_MODE; then
    item=$(printf '{"file":"%s","total":%d,"completed":%d,"incomplete":%d,"status":"%s"}' "$(json_escape "$name")" "$total" "$done" "$incomplete" "$status")
    if [[ -z "$json_items" ]]; then json_items="$item"; else json_items="$json_items,$item"; fi
  else
    results+=("$name|$total|$done|$incomplete|$status")
  fi
done

if $JSON_MODE; then
  incomplete_all=$((total_all - done_all))
  printf '{"checklists_dir":"%s","checklists":[%s],"overall":"%s","total":%d,"completed":%d,"incomplete":%d}\n' "$(json_escape "$CHECKLISTS_DIR")" "$json_items" "$overall" "$total_all" "$done_all" "$incomplete_all"
else
  printf "| Checklist | Total | Completed | Incomplete | Status |\n"
  printf "|-----------|-------|-----------|------------|--------|\n"
  for r in "${results[@]}"; do
    IFS='|' read -r n t d inc st <<< "$r"
    mark="✓ PASS"; [[ "$st" == "FAIL" ]] && mark="✗ FAIL"
    printf "| %s | %s | %s | %s | %s |\n" "$n" "$t" "$d" "$inc" "$mark"
  done
  if [[ "$overall" == "PASS" ]]; then echo "Overall: PASS"; else echo "Overall: FAIL"; fi
fi
