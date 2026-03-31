#!/usr/bin/env bash
# Run this once to connect your local repo to GitHub.
# Usage: ./setup_github_remote.sh <github-username> <repo-name>
#
# Prerequisites:
#   1. Create a new repo on GitHub (do NOT initialize with README)
#   2. Generate a new Personal Access Token at https://github.com/settings/tokens
#      (needs: repo scope)
#   3. Run: ./setup_github_remote.sh your-username science_education

set -e

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <github-username> <repo-name>"
  exit 1
fi

USER="$1"
REPO="$2"

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$USER/$REPO.git"
echo "Remote set to: https://github.com/$USER/$REPO.git"
echo ""
echo "Now push with:"
echo "  git push -u origin main"
echo ""
echo "You will be prompted for credentials."
echo "For the password, use a Personal Access Token (not your GitHub password)."
echo "Generate one at: https://github.com/settings/tokens"
