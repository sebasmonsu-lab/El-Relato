#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"book/translations/_source-export"
GEN=ROOT/"book/translations/tk-es-419-v1/generated"
REPORT=ROOT/"book/translations/tk-es-419-v1/validation-report.json"

def rows(path):
    out=[]
    with path.open(encoding="utf-8") as fh:
        for n,line in enumerate(fh,1):
            if not line.strip(): continue
            r=json.loads(line)
            if not isinstance(r,dict): raise SystemExit(f"{path}:{n}: row is not object")
            out.append(r)
    return out

expected_files=[f"scene-{i:03d}.jsonl" for i in range(1,121)]
src_files=sorted(p.name for p in SRC.glob("scene-*.jsonl"))
gen_files=sorted(p.name for p in GEN.glob("scene-*.jsonl"))
missing_files=sorted(set(expected_files)-set(gen_files))
extra_files=sorted(set(gen_files)-set(expected_files))
if src_files != expected_files:
    raise SystemExit(f"SOURCE export file coverage mismatch: {len(src_files)}")
if missing_files or extra_files:
    raise SystemExit(f"generated scene coverage mismatch missing={missing_files} extra={extra_files}")

src_ids=[]
gen_ids=[]
models=Counter()
statuses=Counter()
scene_reports=[]
empty=[]
scene_mismatch=[]
for name in expected_files:
    s=rows(SRC/name)
    g=rows(GEN/name)
    sids=[r["unit_id"] for r in s]
    gids=[r["unit_id"] for r in g]
    src_ids.extend(sids); gen_ids.extend(gids)
    if sids != gids:
        scene_mismatch.append({"scene":name,"source_count":len(sids),"generated_count":len(gids),
                               "missing":sorted(set(sids)-set(gids))[:20],
                               "extra":sorted(set(gids)-set(sids))[:20]})
    for r in g:
        if not str(r.get("text") or "").strip(): empty.append(r.get("unit_id"))
        models[str(r.get("model") or "legacy-unattributed")]+=1
        statuses[str(r.get("status") or "legacy-unreviewed")]+=1
    scene_reports.append({"scene":int(name[6:9]),"units":len(g)})

src_dups=[k for k,v in Counter(src_ids).items() if v>1]
gen_dups=[k for k,v in Counter(gen_ids).items() if v>1]
missing_ids=sorted(set(src_ids)-set(gen_ids))
extra_ids=sorted(set(gen_ids)-set(src_ids))
ok=(len(src_ids)==4123 and len(gen_ids)==4123 and not src_dups and not gen_dups and
    not missing_ids and not extra_ids and not empty and not scene_mismatch)

report={
 "status":"PASS" if ok else "FAIL",
 "edition_id":"edition:el-relato:tk-es-419:v1",
 "baseline_edition_id":"edition:el-relato:grc-sblgnt-2010:v1",
 "locale":"es-419",
 "scene_files_expected":120,
 "scene_files_present":len(gen_files),
 "source_units":len(src_ids),
 "translated_units":len(gen_ids),
 "expected_units":4123,
 "missing_unit_ids":len(missing_ids),
 "extra_unit_ids":len(extra_ids),
 "duplicate_source_ids":len(src_dups),
 "duplicate_translation_ids":len(gen_dups),
 "empty_translations":len(empty),
 "scene_order_mismatches":len(scene_mismatch),
 "models":dict(models),
 "row_statuses":dict(statuses),
 "provenance_note":"Rows without model/status are retained legacy output and are not relabeled. Structural validation does not imply full philological review.",
 "human_review_required":True
}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
if not ok: raise SystemExit(1)
