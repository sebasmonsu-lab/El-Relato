#!/usr/bin/env bash
set -euo pipefail
BUNDLE="${1:-build/backups/el-relato.bundle}"
LFS_TAR="${2:-build/backups/el-relato-lfs.tar}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

test -f "$BUNDLE"
test -f "$LFS_TAR"
sha256sum -c "${BUNDLE}.sha256"
sha256sum -c "${LFS_TAR}.sha256"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Clone without asking any remote for LFS objects.
GIT_LFS_SKIP_SMUDGE=1 git clone "$BUNDLE" "$TMP/restore"

# Restore the exact LFS object store into the new repository.
tar -xf "$LFS_TAR" -C "$TMP/restore"
cd "$TMP/restore"
git lfs checkout
git lfs fsck
git fsck --full

python -m pip install --disable-pip-version-check jsonschema >/dev/null
python scripts/validate_repo.py
python scripts/build_query_db.py --output build/el-relato.sqlite
python app/el_relato.py --db build/el-relato.sqlite --self-test

# Defensive check: no tracked LFS pointer should remain in the worktree
# where the real object is expected.
python - <<'PY'
from pathlib import Path
bad=[]
for p in Path(".").rglob("*"):
    if not p.is_file() or ".git" in p.parts:
        continue
    try:
        head=p.read_bytes()[:80]
    except OSError:
        continue
    if head.startswith(b"version https://git-lfs.github.com/spec/v1"):
        bad.append(str(p))
if bad:
    raise SystemExit("Unsmudged LFS pointers remain: "+", ".join(bad[:20]))
print("LFS WORKTREE RESTORED")
PY

echo "EL-RELATO RESTORE TEST OK"
