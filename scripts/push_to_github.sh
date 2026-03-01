#!/usr/bin/env bash
set -euo pipefail
# Simple helper to commit all changes and push to a remote GitHub repo.
# Usage:
#   GITHUB_TOKEN=xxx ./scripts/push_to_github.sh [repo_url] [branch]
# If GITHUB_TOKEN is set, uses it for HTTPS auth (x-access-token). Otherwise uses existing git auth (SSH or configured HTTPS).

REPO_URL="${1:-https://github.com/NortCoding/ada.git}"
BRANCH="${2:-main}"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "git not found. Install git to use this script." >&2
  exit 1
fi

if [ ! -d .git ]; then
  echo "No git repo found in $ROOT_DIR — initializing a new repo."
  git init
fi

git add -A
read -r -p "Commit message (default: 'Update from ADA workspace'): " COMMIT_MSG
if [ -z "${COMMIT_MSG// /}" ]; then
  COMMIT_MSG="Update from ADA workspace"
fi
if git commit -m "$COMMIT_MSG"; then
  echo "Committed changes."
else
  echo "Nothing to commit. Continuing..."
fi

if [ -n "${GITHUB_TOKEN:-}" ]; then
  if [[ "$REPO_URL" == https://* ]]; then
    AUTH_URL="${REPO_URL/https:\/\//https://x-access-token:${GITHUB_TOKEN}@}"
  else
    AUTH_URL="$REPO_URL"
  fi
  git remote remove origin 2>/dev/null || true
  git remote add origin "$AUTH_URL"
else
  git remote remove origin 2>/dev/null || true
  git remote add origin "$REPO_URL"
fi

git branch -M "$BRANCH"
echo "Pushing to $REPO_URL (branch $BRANCH) ..."
git push -u origin "$BRANCH"

echo "Push complete."
