#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
OUT="build/backups"
mkdir -p "$OUT"

# Git history / refs.
git bundle create "$OUT/el-relato.bundle" --all
sha256sum "$OUT/el-relato.bundle" > "$OUT/el-relato.bundle.sha256"

# LFS is outside ordinary Git object storage. Fetch every reachable LFS object
# and archive the local LFS object store so restore does not need GitHub.
if command -v git-lfs >/dev/null 2>&1 || git lfs version >/dev/null 2>&1; then
  git lfs fetch --all
  tar -cf "$OUT/el-relato-lfs.tar" .git/lfs/objects
  sha256sum "$OUT/el-relato-lfs.tar" > "$OUT/el-relato-lfs.tar.sha256"
else
  echo "git-lfs is required for a complete El-Relato backup" >&2
  exit 1
fi

python - <<'PY'
import json,subprocess
from datetime import datetime,timezone
from pathlib import Path

bundle=Path("build/backups/el-relato.bundle")
lfs=Path("build/backups/el-relato-lfs.tar")
lfs_listing=subprocess.check_output(["git","lfs","ls-files","--all","--long"],text=True).splitlines()
meta={
  "generated_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
  "head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
  "branches":subprocess.check_output(["git","branch","--format=%(refname:short)"],text=True).splitlines(),
  "bundle_bytes":bundle.stat().st_size,
  "lfs_archive_bytes":lfs.stat().st_size,
  "lfs_tracked_entries":len(lfs_listing),
  "components":[
    {"path":str(bundle),"sha256_file":"build/backups/el-relato.bundle.sha256"},
    {"path":str(lfs),"sha256_file":"build/backups/el-relato-lfs.tar.sha256"},
  ],
}
Path("build/backups/backup-metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
print(json.dumps(meta,indent=2))
PY
