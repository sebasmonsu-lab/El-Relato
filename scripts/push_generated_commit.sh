#!/usr/bin/env bash
set -euo pipefail

for attempt in 1 2 3 4 5; do
  echo "Push attempt $attempt/5"
  git fetch origin main
  if git rebase origin/main; then
    if git push origin HEAD:main; then
      exit 0
    fi
  fi
  git rebase --abort 2>/dev/null || true
  sleep $((attempt * 2))
done

echo "Could not push generated commit after 5 rebase attempts." >&2
exit 1
