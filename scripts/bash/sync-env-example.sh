#!/usr/bin/env bash
# sync-env-example.sh — ensure .env.example contains all env() keys from config/services.php
set -e
ENV_EXAMPLE=""
CHECK=false
FIX=false
JSON_MODE=false
CONFIG_FILES=()

prev=""
for arg in "$@"; do
  if [[ "$prev" == "--env-example" ]]; then ENV_EXAMPLE="$arg"; prev=""; continue; fi
  if [[ "$prev" == "--config" ]]; then CONFIG_FILES+=("$arg"); prev=""; continue; fi
  case "$arg" in
    --env-example) prev="--env-example" ;;
    --env-example=*) ENV_EXAMPLE="${arg#--env-example=}" ;;
    --config) prev="--config" ;;
    --config=*) CONFIG_FILES+=("${arg#--config=}") ;;
    --check) CHECK=true ;;
    --fix) FIX=true ;;
    --json) JSON_MODE=true ;;
    --help|-h) echo "Usage: $0 [--env-example .env.example] [--config config/services.php] [--check] [--fix] [--json]"; exit 0 ;;
    *) echo "Unknown: $arg" >&2; exit 1 ;;
  esac
done

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"
eval $(get_feature_paths)
if [[ -z "$ENV_EXAMPLE" ]]; then ENV_EXAMPLE="$REPO_ROOT/.env.example"; fi
if [[ ${#CONFIG_FILES[@]} -eq 0 ]]; then
  if [[ -f "$REPO_ROOT/config/services.php" ]]; then CONFIG_FILES+=("$REPO_ROOT/config/services.php"); fi
  for f in "$REPO_ROOT"/config/*.php; do [[ -f "$f" ]] || continue; found=0; for c in "${CONFIG_FILES[@]}"; do [[ "$c" == "$f" ]] && found=1; done; [[ $found -eq 0 ]] && CONFIG_FILES+=("$f"); done
fi
if [[ ${#CONFIG_FILES[@]} -eq 0 ]]; then
  if $JSON_MODE; then printf '{"missing":[],"envExample":"%s","status":"no-config"}\n' "$(json_escape "$ENV_EXAMPLE")"; else echo "No config files found"; fi
  exit 0
fi

# extract env keys via grep -oE
keys=()
for cf in "${CONFIG_FILES[@]}"; do
  [[ -f "$cf" ]] || continue
  # portable: use sed to extract env('KEY' or env("KEY"
  while IFS= read -r line; do
    # extract via grep -o
    for k in $(grep -oE "env\( *['\"][^'\"]+['\"]" "$cf" 2>/dev/null | sed -E "s/env\( *['\"]//; s/['\"].*//"); do
      # dedupe
      found=0; for e in "${keys[@]}"; do [[ "$e" == "$k" ]] && found=1; done; [[ $found -eq 0 ]] && keys+=("$k")
    done
    break
  done < <(echo 1)
  # alternative: do once per file (above loop break makes it once)
  # actually redo naively: extract all at once
  # re-extract correctly per file
  true
done
# re-do correctly: extract per file without early break
keys=()
for cf in "${CONFIG_FILES[@]}"; do
  [[ -f "$cf" ]] || continue
  while IFS= read -r k; do
    [[ -z "$k" ]] && continue
    found=0; for e in "${keys[@]}"; do [[ "$e" == "$k" ]] && found=1; done; [[ $found -eq 0 ]] && keys+=("$k")
  done < <(grep -oE "env\( *['\"][^'\"]+['\"]" "$cf" 2>/dev/null | sed -E "s/env\( *['\"]//; s/['\"].*//" || true)
done

if [[ ${#keys[@]} -eq 0 ]]; then
  if $JSON_MODE; then echo '{"missing":[],"keys":[]}'; else echo "No env() keys found in ${CONFIG_FILES[*]}"; fi
  exit 0
fi

missing=()
if [[ -f "$ENV_EXAMPLE" ]]; then
  for k in "${keys[@]}"; do
    if ! grep -qE "^[[:space:]]*$k[[:space:]]*=" "$ENV_EXAMPLE" 2>/dev/null; then missing+=("$k"); fi
  done
else
  missing=("${keys[@]}")
fi

if $CHECK; then
  if $JSON_MODE; then
    miss_json=$(printf '"%s",' "${missing[@]}" | sed 's/,$//')
    keys_json=$(printf '"%s",' "${keys[@]}" | sed 's/,$//')
    printf '{"missing":[%s],"keys":[%s],"envExample":"%s"}\n' "$miss_json" "$keys_json" "$(json_escape "$ENV_EXAMPLE")"
  else
    if [[ ${#missing[@]} -gt 0 ]]; then echo "Missing in .env.example: ${missing[*]}"; echo "Run with --fix to append"; else echo "All env keys present in .env.example"; fi
  fi
  [[ ${#missing[@]} -gt 0 ]] && exit 1 || exit 0
fi

if [[ ${#missing[@]} -gt 0 ]]; then
  if [[ ! -f "$ENV_EXAMPLE" ]]; then touch "$ENV_EXAMPLE"; fi
  {
    echo ""
    echo "# Added by sync-env-example.sh on $(date +%Y-%m-%d) — from ${CONFIG_FILES[*]}"
    for k in "${missing[@]}"; do echo "$k="; done
  } >> "$ENV_EXAMPLE"
  if $JSON_MODE; then
    miss_json=$(printf '"%s",' "${missing[@]}" | sed 's/,$//')
    printf '{"fixed":true,"missing":[%s],"envExample":"%s"}\n' "$miss_json" "$(json_escape "$ENV_EXAMPLE")"
  else
    echo "Added ${#missing[@]} key(s) to .env.example: ${missing[*]}"
  fi
else
  if $JSON_MODE; then echo '{"fixed":false,"missing":[]}'; else echo "All env keys present in .env.example"; fi
fi
