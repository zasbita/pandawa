#!/usr/bin/env bash
set -euo pipefail

# create-github-release.sh
# Create a GitHub release with all template zip files
# Usage: create-github-release.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

# Remove 'v' prefix from version for release title
VERSION_NO_V=${VERSION#v}

# Glob instead of a hardcoded per-agent file list, so a new AI agent variant is included
# without editing this script. nullglob avoids passing a literal unmatched pattern to `gh`.
# Domain profiles are NOT part of this release — they live in the separate
# pandawa-marketplace-tooling repo and are fetched live on `pandawa init --profile`
# (see that repo's profiles.json), not packaged here.
shopt -s nullglob
assets=(.genreleases/pandawa-*-"$VERSION".zip)
shopt -u nullglob

if [[ ${#assets[@]} -eq 0 ]]; then
  echo "Error: no release assets found under .genreleases/ for $VERSION" >&2
  exit 1
fi

gh release create "$VERSION" \
  "${assets[@]}" \
  --title "Pandawa Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
