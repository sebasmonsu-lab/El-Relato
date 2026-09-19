#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
OUT="build/backups"
mkdir -p "$OUT"
git bundle create "$OUT/el-relato.bundle" --all
sha256sum "$OUT/el-relato.bundle" > "$OUT/el-relato.bundle.sha256"
python - <<'PY'
import json,subprocess
from datetime import datetime,timezone
from pathlib import Path
p=Path("build/backups/el-relato.bundle")
meta={
  "generated_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
  "head":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
  "branches":subprocess.check_output(["git","branch","--format=%(refname:short)"],text=True).splitlines(),
  "bundle_bytes":p.stat().st_size,
}
Path("build/backups/backup-metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
print(json.dumps(meta,indent=2))
PY
