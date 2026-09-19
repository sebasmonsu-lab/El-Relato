#!/usr/bin/env python3
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, re, time
from pathlib import Path
from urllib.parse import urlsplit
import requests

ROOT=Path(__file__).resolve().parents[1]
URL_RE=re.compile(r'(?:(?:https?:)?//images\.csntm\.org/IIIFServer\.ashx/[^"\'<>\s]+?/full/100,/0/native\.jpg)',re.I)

def safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+","_",s).strip("_") or "image"

def inventory(ms):
    html=(ROOT/f"sources/manuscripts/{ms}/raw/csntm/page.html").read_text(encoding="utf-8")
    urls=[]
    seen=set()
    for u in URL_RE.findall(html):
        if u.startswith("//"): u="https:"+u
        # Service base is everything before /full/100,...
        base=u.split("/full/100,",1)[0]
        if base in seen: continue
        seen.add(base)
        urls.append(base)
    return urls

def candidates(base):
    return [
        base+"/full/full/0/native.jpg",
        base+"/full/max/0/native.jpg",
        base+"/full/full/0/default.jpg",
    ]

def get_one(ms,base):
    filename=urlsplit(base).path.rsplit("/",1)[-1]
    dest=ROOT/f"sources/manuscripts/{ms}/images/csntm"/safe(filename)
    # Ensure jpg suffix exists.
    if not dest.name.lower().endswith(".jpg"):
        dest=dest.with_suffix(".jpg")
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and dest.stat().st_size>10000:
        data=dest.read_bytes()
        return {"service_base":base,"url":None,"local_path":dest.relative_to(ROOT).as_posix(),"status":"already-present","size":len(data),"sha256":hashlib.sha256(data).hexdigest(),"error":None}

    ses=requests.Session()
    ses.headers.update({"User-Agent":"El-Relato-preservation/1.0","Accept-Encoding":"identity"})
    last=None
    for url in candidates(base):
        for attempt in range(1,4):
            tmp=dest.with_suffix(".jpg.part")
            try:
                with ses.get(url,stream=True,timeout=(15,120),allow_redirects=True) as r:
                    r.raise_for_status()
                    ctype=r.headers.get("Content-Type","")
                    if not ctype.startswith("image/"): raise RuntimeError(f"content type {ctype}")
                    h=hashlib.sha256(); n=0
                    with tmp.open("wb") as out:
                        for chunk in r.iter_content(262144):
                            if chunk:
                                out.write(chunk); h.update(chunk); n+=len(chunk)
                if n<10000: raise RuntimeError(f"too small: {n}")
                tmp.replace(dest)
                return {"service_base":base,"url":url,"local_path":dest.relative_to(ROOT).as_posix(),"status":"mirrored","size":n,"sha256":h.hexdigest(),"error":None}
            except Exception as exc:
                last=f"{type(exc).__name__}: {exc}"
                tmp.unlink(missing_ok=True)
                time.sleep(attempt)
    return {"service_base":base,"url":None,"local_path":dest.relative_to(ROOT).as_posix(),"status":"failed","size":None,"sha256":None,"error":last}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manuscript",required=True)
    args=ap.parse_args()
    ms=args.manuscript
    bases=inventory(ms)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        rows=list(ex.map(lambda b:get_one(ms,b),bases))
    mdir=ROOT/f"data/manifests/facsimiles/{ms}"
    mdir.mkdir(parents=True,exist_ok=True)
    summary={
        "manuscript":ms,
        "source":"CSNTM",
        "listed_images":len(bases),
        "mirrored_or_present":sum(x["status"] in {"mirrored","already-present"} for x in rows),
        "failed":sum(x["status"]=="failed" for x in rows),
        "total_bytes":sum(x["size"] or 0 for x in rows),
        "complete":all(x["status"]!="failed" for x in rows),
        "files":rows,
    }
    (mdir/"csntm-mirror.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="files"},indent=2))

if __name__=="__main__":
    main()
