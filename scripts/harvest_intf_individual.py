#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures,datetime as dt,hashlib,json,time
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"sources/catalogs/INTF-Liste/individual"
OUT.mkdir(parents=True,exist_ok=True)
API="https://ntvmr.uni-muenster.de/community/vmr/api/metadata/liste/search/"

# Gregory-Aland docID namespaces used by the Liste:
# papyri 10000-series, majuscules 20000-series.
TARGETS=list(range(10001,10201))+list(range(20001,20351))

def fetch(docid):
    p=OUT/f"{docid}.json"
    if p.exists() and p.stat().st_size>2:
        data=p.read_bytes()
        return {"docID":docid,"status":"cached","bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"path":str(p.relative_to(ROOT))}
    s=requests.Session()
    s.headers.update({"User-Agent":"El-Relato academic preservation/1.0 (private research corpus)","Accept-Encoding":"identity"})
    params={"docID":str(docid),"detail":"document","format":"json","limit":"10"}
    last=None
    for attempt in range(2):
        try:
            r=s.get(API,params=params,timeout=(8,20))
            if r.status_code==429:
                time.sleep(5*(attempt+1)); continue
            r.raise_for_status()
            data=r.content
            p.write_bytes(data)
            return {"docID":docid,"status":"ok","bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
                    "url":r.url,"path":str(p.relative_to(ROOT)),"content_type":r.headers.get("Content-Type")}
        except Exception as exc:
            last=exc
            time.sleep(1.5*(attempt+1))
    return {"docID":docid,"status":"error","error":f"{type(last).__name__}: {last}"}

def main():
    results=[]
    # Low concurrency on purpose: this is an academic institutional API.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for i,res in enumerate(ex.map(fetch,TARGETS),1):
            results.append(res)
            if i%50==0: print(f"{i}/{len(TARGETS)}")
    manifest={
      "api":API,
      "captured_at":dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
      "strategy":"individual deterministic docID requests; no broad Liste search",
      "target_ranges":["10001-10200 papyrus namespace","20001-20350 majuscule namespace"],
      "results":results,
      "summary":{
        "targets":len(results),
        "ok_or_cached":sum(x["status"] in ("ok","cached") for x in results),
        "errors":sum(x["status"]=="error" for x in results),
        "nontrivial_responses":sum((x.get("bytes") or 0)>20 for x in results),
      }
    }
    (ROOT/"sources/catalogs/INTF-Liste/individual-capture-manifest.json").write_text(
      json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest["summary"],indent=2))
    # Do not fail for individual errors; they are explicit blockers. Fail only if the method itself is unusable.
    if manifest["summary"]["ok_or_cached"]<500:
        raise SystemExit("Too many individual INTF requests failed; keep B-003 open")

if __name__=="__main__":
    main()
