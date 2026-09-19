#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, time
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]

def read_jsonl(path):
    with path.open(encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]

def safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+","_",s).strip("_") or "unnamed"

def url_candidates(service):
    service=service.rstrip("/")
    return [
        service+"/full/full/0/default.jpg",
        service+"/full/max/0/default.jpg",
        service+"/full/2000,/0/default.jpg",
    ]

def download(row,dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and dest.stat().st_size>10000:
        data=dest.read_bytes()
        return {"status":"already-present","sha256":hashlib.sha256(data).hexdigest(),"size":len(data),"url":None}
    ses=requests.Session()
    ses.headers.update({"User-Agent":"El-Relato-preservation/1.0","Accept-Encoding":"identity"})
    last=None
    for u in url_candidates(row["image_service"]):
        for attempt in range(1,4):
            tmp=dest.with_suffix(".jpg.part")
            try:
                with ses.get(u,stream=True,timeout=(15,90),allow_redirects=True) as r:
                    r.raise_for_status()
                    if not (r.headers.get("Content-Type","").startswith("image/")):
                        raise RuntimeError("not image")
                    h=hashlib.sha256(); size=0
                    with tmp.open("wb") as out:
                        for chunk in r.iter_content(262144):
                            if chunk:
                                out.write(chunk); h.update(chunk); size+=len(chunk)
                if size<10000: raise RuntimeError(f"too small {size}")
                with tmp.open("rb") as fh:
                    if fh.read(2)!=b"\xff\xd8": raise RuntimeError("not JPEG")
                tmp.replace(dest)
                return {"status":"mirrored","sha256":h.hexdigest(),"size":size,"url":u}
            except Exception as exc:
                last=f"{type(exc).__name__}: {exc}"
                tmp.unlink(missing_ok=True)
                time.sleep(attempt)
    return {"status":"failed","sha256":None,"size":None,"url":None,"error":last}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manuscript",required=True)
    ap.add_argument("--inventory",required=True)
    ap.add_argument("--offset",type=int,default=0)
    ap.add_argument("--limit",type=int,default=50)
    args=ap.parse_args()

    inv=read_jsonl(ROOT/args.inventory)
    batch=inv[args.offset:args.offset+args.limit]
    results=[]
    for row in batch:
        dest=ROOT/f"sources/manuscripts/{args.manuscript}/images"/f"{safe(row.get('label') or str(args.offset+len(results)))}.jpg"
        res=download(row,dest)
        results.append({
            "manuscript":args.manuscript,
            "label":row.get("label"),
            "canvas_id":row.get("id"),
            "image_service":row.get("image_service"),
            "local_path":dest.relative_to(ROOT).as_posix(),
            **res
        })

    mdir=ROOT/f"data/manifests/facsimiles/{args.manuscript}"
    mdir.mkdir(parents=True,exist_ok=True)
    end=args.offset+max(len(batch)-1,0)
    path=mdir/f"batch-{args.offset:04d}-{end:04d}.json"
    path.write_text(json.dumps({
        "manuscript":args.manuscript,
        "offset":args.offset,
        "selected":len(batch),
        "mirrored_or_present":sum(x["status"] in {"mirrored","already-present"} for x in results),
        "failed":sum(x["status"]=="failed" for x in results),
        "files":results,
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(path, len(batch), sum(x["status"]=="failed" for x in results))

if __name__=="__main__":
    main()
