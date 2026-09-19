#!/usr/bin/env python3
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/derived/audit"
OUT.mkdir(parents=True,exist_ok=True)

def load_json(path):
    p=ROOT/path
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def jsonl_count(path):
    p=ROOT/path
    if not p.exists():
        return None
    with p.open(encoding="utf-8-sig") as f:
        return sum(1 for x in f if x.strip())

checks=[]
def add(id,status,title,detail=None,metrics=None):
    checks.append({"id":id,"status":status,"title":title,"detail":detail,"metrics":metrics or {}})

def exists(path):
    return (ROOT/path).exists()

for p in ["README.md","PROJECT_PLAN.md","STATUS.md","docs/ARCHITECTURE.md","docs/LOOP_PROTOCOL.md","docs/ID_CONVENTIONS.md"]:
    add("gov:"+p,"PASS" if exists(p) else "FAIL",f"Required project file: {p}")

sbl=load_json("data/derived/sblgnt/parse-stats.json")
if sbl:
    ok=sbl.get("verses")==3768 and sbl.get("tokens")==64686
    add("corpus:sblgnt","PASS" if ok else "FAIL","SBLGNT Gospel structured corpus",metrics=sbl)
else:
    add("corpus:sblgnt","FAIL","SBLGNT Gospel structured corpus","Missing parse stats")

alignment=load_json("data/derived/alignment/sbl-tagnt-report.json")
if alignment:
    coverage=alignment.get("coverage",0)
    status="PASS" if coverage>=0.99 and alignment.get("links_with_unknown_morphology_code")==0 else "FAIL"
    add("corpus:alignment",status,"SBLGNT ↔ TAGNT/Strong/morphology alignment",
        f"{alignment.get('unmatched_tokens')} SBLGNT tokens remain explicitly unmatched; positional links remain auditable.",alignment)
    if alignment.get("unmatched_tokens",0)>0:
        add("corpus:alignment-exceptions","WARN","Alignment exceptions remain explicit",
            "These are not silently imputed; see data/derived/alignment/sbl-tagnt-unmatched.jsonl.",
            {"unmatched_tokens":alignment.get("unmatched_tokens"),"low_confidence_positional_links":alignment.get("low_confidence_positional_links")})
else:
    add("corpus:alignment","FAIL","SBLGNT ↔ TAGNT alignment","Missing report")

step=load_json("data/derived/stepbible/parse-stats.json")
if step:
    ok=step["TBESG"]["entries"]>=11000 and step["TAGNT"]["rows"]>=66000 and step["TEGMC"]["full_morphology_codes"]>=1600
    add("corpus:stepbible","PASS" if ok else "FAIL","STEPBible normalized datasets",metrics=step)
else:
    add("corpus:stepbible","FAIL","STEPBible normalized datasets","Missing report")

strong=load_json("data/derived/strong-original/parse-stats.json")
add("corpus:strong-original","PASS" if strong and strong.get("entries",0)>=5500 else "FAIL","Strong historical Greek dictionary",metrics=strong or {})

apparatus=load_json("data/derived/apparatus/sblgnt-apparatus-report.json")
if apparatus:
    ok=apparatus.get("units",0)>=3600 and apparatus.get("parse_status",{}).get("parsed")==apparatus.get("units")
    add("corpus:apparatus","PASS" if ok else "FAIL","SBLGNT edition apparatus",metrics=apparatus)
else:
    add("corpus:apparatus","FAIL","SBLGNT edition apparatus","Missing report")

core=load_json("data/derived/manuscripts/core-gospel-facsimile-mirror-summary.json")
metrics={k:core.get(k) for k in ("planned_files","mirrored_files","missing_files","total_bytes")} if core else {}
add("ms:core-codices","PASS" if core and core.get("complete") and core.get("mirrored_files")==269 else "FAIL",
    "Vaticanus + Sinaiticus Gospel facsimile mirror",metrics=metrics)

p75=load_json("data/derived/manuscripts/P75-facsimile-summary.json")
metrics={k:p75.get(k) for k in ("planned","mirrored","missing","total_bytes")} if p75 else {}
add("ms:p75","PASS" if p75 and p75.get("complete") else "FAIL","P75 facsimile mirror",metrics=metrics)

csntm=load_json("data/derived/manuscripts/csntm-core-mirror-summary.json")
if csntm:
    incomplete=[x for x in csntm.get("manuscripts",[]) if not x.get("complete")]
    add("ms:csntm-core","WARN" if incomplete else "PASS","CSNTM core papyrus mirror",
        "Source-specific CSNTM gaps are tracked; institutional fallbacks may supersede them.",
        {"incomplete":[{"manuscript":x["manuscript"],"failed":x["failed"]} for x in incomplete]})
else:
    add("ms:csntm-core","FAIL","CSNTM core papyrus mirror","Missing report")

fallback=load_json("data/derived/manuscripts/fallback-facsimile-mirror-summary.json")
if fallback:
    incomplete=[k for k,v in fallback.items() if not v.get("complete")]
    add("ms:fallbacks","PASS" if not incomplete else "WARN","Institutional fallback facsimiles",
        None if not incomplete else f"Incomplete fallbacks: {', '.join(incomplete)}",
        {k:{x:v.get(x) for x in ("mirrored_or_present","failed","total_bytes","complete")} for k,v in fallback.items()})
else:
    add("ms:fallbacks","WARN","Institutional fallback facsimiles","Mirror workflow has not yet produced its report.")

images=jsonl_count("data/normalized/manuscript-evidence/images.jsonl")
att=jsonl_count("data/normalized/manuscript-evidence/witness-attestations.jsonl")
add("ms:evidence","PASS" if (images or 0)>=372 and (att or 0)>=623 else "FAIL",
    "Normalized manuscript image/passages evidence",metrics={"images":images,"witness_attestations":att})

sinrep=load_json("data/derived/manuscripts/Sinaiticus-gospel-transcription-report.json")
add("tx:sinaiticus","PASS" if sinrep and sinrep.get("normalized_units",0)>=3745 else "FAIL",
    "Sinaiticus Gospel transcription",metrics=sinrep or {})

igntp=load_json("data/derived/manuscripts/igntp-transcription-mirror-summary.json")
if igntp:
    ok=all(x.get("complete") for x in igntp.get("items",[]))
    add("tx:igntp","PASS" if ok else "WARN","IGNTP P52/P66/P75 raw transcriptions",
        metrics={"items":[{"manuscript":x.get("manuscript"),"complete":x.get("complete")} for x in igntp.get("items",[])]})
else:
    add("tx:igntp","WARN","IGNTP P52/P66/P75 raw transcriptions","Mirror workflow has not yet produced its report.")

checksum=load_json("data/checksums/preservation-sha256.json")
count=len(checksum.get("files",[])) if checksum else 0
add("integrity:checksums","PASS" if count>=30 else "WARN","Preservation SHA-256 manifest",
    "Checksum workflow should be refreshed after the latest mirrors." if count<30 else None,
    {"files":count,"generated_at":checksum.get("generated_at") if checksum else None})

licenses=load_json("data/manifests/license-registry.json")
licensed={x["source_id"] for x in licenses.get("entries",[])} if licenses else set()
p=ROOT/"data/normalized/sources.jsonl"
source_rows=[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
source_ids={x["id"] for x in source_rows}
missing_license=sorted(source_ids-licensed)
add("integrity:license-registry","PASS" if not missing_license else "WARN","Source license/permission registry",
    None if not missing_license else f"Sources without license registry entries: {missing_license}",
    {"sources":len(source_rows),"license_entries":len(licensed)})

db=load_json("data/derived/query/db-stats.json")
add("query:db","PASS" if db and db.get("tokens")==64686 and db.get("witness_attestations",0)>=623 else "FAIL",
    "Integrated reproducible SQLite query layer",metrics=db or {})
add("query:app","PASS" if exists("app/el_relato.py") and exists(".github/workflows/test-app.yml") else "FAIL",
    "Local research interface and self-test")

status_text=(ROOT/"STATUS.md").read_text(encoding="utf-8") if exists("STATUS.md") else ""
if "B-003" in status_text:
    add("blocker:intf","WARN","INTF/NTVMR exhaustive catalogue harvest remains blocked",
        "The nucleus is preserved, but the declared exhaustive scope (all Gospel papyri + majuscules through s. V) is not yet certified complete.")
else:
    add("blocker:intf","FAIL","INTF blocker tracking missing")

add("backup:procedure","PASS" if exists("backup/create_bundle.sh") and exists("backup/verify_restore.sh") else "FAIL",
    "Git + LFS backup/restore procedure")
add("backup:independent","WARN","Independent off-GitHub backup target not yet verified",
    "GitHub Actions artifacts do not count as an independent backup. A second storage destination and restore test are still required.")

fails=sum(x["status"]=="FAIL" for x in checks)
warnings=sum(x["status"]=="WARN" for x in checks)
passes=sum(x["status"]=="PASS" for x in checks)
overall="FAIL" if fails else ("PASS_WITH_BLOCKERS" if warnings else "PASS")
report={"generated_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),"overall":overall,
        "counts":{"pass":passes,"warn":warnings,"fail":fails},"checks":checks}
(OUT/"audit-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

lines=["# El-Relato — Audit Report","",f"Generated: {report['generated_at']}","",f"**Overall: {overall}**","",
       f"- PASS: {passes}",f"- WARN / BLOCKED: {warnings}",f"- FAIL: {fails}","","## Checks",""]
for x in checks:
    icon={"PASS":"✅","WARN":"⚠️","FAIL":"❌"}[x["status"]]
    lines.append(f"### {icon} {x['id']} — {x['title']}")
    if x.get("detail"): lines.append(x["detail"])
    if x.get("metrics"):
        lines.extend(["~~~json",json.dumps(x["metrics"],ensure_ascii=False,indent=2),"~~~"])
    lines.append("")
(ROOT/"AUDIT_REPORT.md").write_text("\n".join(lines),encoding="utf-8")
print(json.dumps({"pass":passes,"warn":warnings,"fail":fails,"overall":overall},indent=2))
if fails:
    raise SystemExit(f"Audit has {fails} integrity failures")
