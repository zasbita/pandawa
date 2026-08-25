#!/usr/bin/env bash
set -euo pipefail

# create-gitlab-release.sh
# Create the GitLab release for <version>, attaching every file in .genreleases/ as a
# release asset. Asset attachment loops over whatever create-release-packages.sh actually
# produced, so adding a new AI agent template never requires editing this script or
# .gitlab-ci.yml. Note: domain profiles are NOT part of this release — they live in the
# separate pandawa-marketplace-tooling repo and are fetched live on `pandawa init --profile`
# (see that repo's profiles.json + pandawa_cli's fetch_profile_index/download_profile_archive_from_gitlab).
# Usage: create-gitlab-release.sh <version>
#
# Requires the `release-cli` binary on PATH (the create-release job in .gitlab-ci.yml runs
# this under the registry.gitlab.com/gitlab-org/release-cli image) plus the standard
# predefined GitLab CI variables (CI_API_V4_URL, CI_PROJECT_ID, CI_JOB_TOKEN, CI_SERVER_URL)
# which release-cli reads automatically.

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"
VERSION_NO_V=${VERSION#v}

echo "Preparing GitLab release for version $VERSION_NO_V"
echo "Release artifacts are in .genreleases/"
echo ""
echo "Release artifacts:"
ls -la .genreleases/*.zip 2>/dev/null || echo "No artifacts found"

ASSET_ARGS=()
for f in .genreleases/pandawa-*-"${VERSION}".zip; do
  [[ -f "$f" ]] || continue
  name=$(basename "$f")
  url="${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/packages/generic/pandawa-templates/${VERSION}/${name}"
  ASSET_ARGS+=(--assets-link "{\"name\":\"${name}\",\"url\":\"${url}\"}")
done

if [[ ${#ASSET_ARGS[@]} -eq 0 ]]; then
  echo "Error: no release assets found in .genreleases/ — refusing to create an empty release" >&2
  exit 1
fi

echo ""
echo "Attaching ${#ASSET_ARGS[@]} asset(s) to release $VERSION"

# --ref is intentionally NOT passed: release-cli defaults it to $CI_COMMIT_SHA, which is how
# the $VERSION tag gets auto-created by the GitLab Releases API today (this pipeline never
# runs `git tag`/`git push` anywhere). Passing --ref explicitly, or assuming the tag already
# exists, would silently stop tag creation and corrupt the next release's version math
# (get-next-version-gitlab.sh relies on `git describe --tags`).
release-cli create \
  --tag-name "$VERSION" \
  --name "$VERSION" \
  --description release_notes.md \
  "${ASSET_ARGS[@]}"
