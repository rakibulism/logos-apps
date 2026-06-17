#!/usr/bin/env bash
# Pull ONLY new/updated logo SVGs from the upstream repo, then regenerate the site +
# manifest with your own branding. Nothing else from upstream is merged, so your
# README / index.html / templates / LICENSE stay exactly as they are.
#
# Usage:  ./scripts/sync_upstream_logos.sh [upstream-remote] [branch]
#   defaults: upstream  master
set -euo pipefail

UPSTREAM="${1:-upstream}"
BRANCH="${2:-master}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Ensure the upstream remote exists (points at the original logo source).
if ! git remote get-url "$UPSTREAM" >/dev/null 2>&1; then
  echo "Remote '$UPSTREAM' not found. Add it once, e.g.:"
  echo "  git remote add upstream https://github.com/ln-dev7/logos-apps.git"
  exit 1
fi

echo "Fetching $UPSTREAM/$BRANCH…"
git fetch "$UPSTREAM" "$BRANCH"

# Grab only the logos/ directory from upstream — new files appear, nothing else moves.
echo "Checking out logos/ from $UPSTREAM/$BRANCH…"
git checkout "$UPSTREAM/$BRANCH" -- logos/

echo "Regenerating README, categories, index.html and assets/logos.json…"
python3 scripts/gen_site.py >/dev/null

ADDED=$(git status --porcelain logos/ | grep -c '^A\|^??' || true)
echo "Done. Review the changes:"
echo "  git status"
echo "  git add -A && git commit -m 'Sync logos from upstream'"
