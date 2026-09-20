#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CANON=[("Matthew","matthew"),("Mark","mark"),("Luke","luke"),("John","john")]
TARGETS={
 "es-419":{"dir":"es-419-v1","edition_id":"edition:gospels:es-419:v1"}
}

def read_jsonl(p):
    with p.open(encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if line.strip():
                try: yield json.loads(line)
                except Exception as e: raise SystemExit(f"{p}:{n}: invalid JSON: {e}")

def expected_rows():
    out={}
    for book,slug in CANON:
        for p in sorted((ROOT/"data/normalized/sblgnt/chapters").glob(f"{slug}-*.jsonl")):
            for r in read_jsonl(p):
                k=(r["book"],int(r["chapter"]),int(r["verse"]))
                if k in out: raise SystemExit(f"duplicate Greek key {k}")
                out[k]=r
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--locale",choices=TARGETS,required=True)
    a=ap.parse_args()
    cfg=TARGETS[a.locale]
    root=ROOT/"sources/gospel-editions"/cfg["dir"]
    gen=root/"generated"
    expected=expected_rows()
    got={}
    provenance={}
    files=sorted(gen.glob("*.jsonl"))
    for p in files:
        for r in read_jsonl(p):
            k=(r["book"],int(r["chapter"]),int(r["verse"]))
            if k in got: raise SystemExit(f"duplicate translated key {k}")
            text=str(r.get("text") or "").strip()
            if not text: raise SystemExit(f"empty translation {k}")
            got[k]=text
            provenance[k]={
                "model":r.get("model"),
                "policy":r.get("policy"),
                "status":r.get("status"),
                "file":p.name
            }
    missing=sorted(set(expected)-set(got))
    extra=sorted(set(got)-set(expected))
    if len(expected)!=3768:
        raise SystemExit(f"unexpected Greek baseline count: {len(expected)}")
    if missing or extra:
        raise SystemExit(f"coverage mismatch expected={len(expected)} got={len(got)} missing={missing[:20]} extra={extra[:20]}")
    order={b:i for i,(b,_) in enumerate(CANON)}
    keys=sorted(expected,key=lambda k:(order[k[0]],k[1],k[2]))
    out=root/"verses.jsonl"
    with out.open("w",encoding="utf-8") as f:
        for k in keys:
            f.write(json.dumps({"book":k[0],"chapter":k[1],"verse":k[2],"text":got[k]},ensure_ascii=False,separators=(",",":"))+"\n")
    meta=json.loads((root/"edition.json").read_text(encoding="utf-8"))
    meta["status"]="consolidated"
    meta["publication"]="public"
    meta["notes"]=(
        "AI translation directly from the Greek SBLGNT source; complete canonical coverage "
        "validated 3768/3768 verses with exact book/chapter/verse key equality. "
        "Contemporary es-419; human philological review remains recommended. "
        "Legacy generated material was retained only in the single V1 path and direct GPT-5.6 Sol "
        "chapters completed the missing corpus."
    )
    (root/"edition.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    models={}
    statuses={}
    for p in provenance.values():
        models[str(p.get("model") or "unknown")]=models.get(str(p.get("model") or "unknown"),0)+1
        statuses[str(p.get("status") or "unknown")]=statuses.get(str(p.get("status") or "unknown"),0)+1
    report={
        "status":"PASS","locale":a.locale,"edition_id":cfg["edition_id"],
        "expected_verses":len(expected),"translated_verses":len(got),
        "missing":0,"extra":0,"chapter_files":len(files),
        "models":models,"row_statuses":statuses
    }
    (root/"validation-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
