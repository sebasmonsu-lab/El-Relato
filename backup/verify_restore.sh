#!/usr/bin/env bash
set -euo pipefail
BUNDLE="${1:-build/backups/el-relato.bundle}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
test -f "$BUNDLE"
sha256sum -c "${BUNDLE}.sha256"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git clone "$BUNDLE" "$TMP/restore"
cd "$TMP/restore"
git fsck --full
python -m pip install --disable-pip-version-check jsonschema >/dev/null
python scripts/validate_repo.py
python scripts/build_query_db.py --output build/el-relato.sqlite
python app/el_relato.py --db build/el-relato.sqlite --self-test
echo "EL-RELATO RESTORE TEST OK"
