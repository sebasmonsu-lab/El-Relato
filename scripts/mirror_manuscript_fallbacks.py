#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,time
from pathlib import Path
from urllib.parse import quote
import requests

ROOT=Path(__file__).resolve().parents[1]
DER=ROOT/"data/derived/manuscripts"
DER.mkdir(parents=True,exist_ok=True)
session=requests.Session()
session.headers.update({"User-Agent":"El-Relato-preservation/1.0","Accept-Encoding":"identity"})

def download(url,path,min_bytes=1000,attempts=4):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.stat().st_size>=min_bytes:
        data=path.read_bytes()
        return {"status":"present","url":url,"path":str(path.relative_to(ROOT)),"size":len(data),"sha256":hashlib.sha256(data).hexdigest()}
    last=None
    for a in range(attempts):
        try:
            r=session.get(url,timeout=120)
            r.raise_for_status()
            data=r.content
            if len(data)<min_bytes:
                raise RuntimeError(f"too small: {len(data)}")
            path.write_bytes(data)
            return {"status":"mirrored","url":r.url,"path":str(path.relative_to(ROOT)),"size":len(data),"sha256":hashlib.sha256(data).hexdigest()}
        except Exception as exc:
            last=exc; time.sleep(2**a)
    return {"status":"failed","url":url,"path":str(path.relative_to(ROOT)),"size":None,"sha256":None,"error":f"{type(last).__name__}: {last}"}

report={"P66":{"source":"Bodmer Lab","files":[]},"P104":{"source":"Oxford/Wikimedia archival copy","files":[]},"P137":{"source":"Egypt Exploration Society","files":[]}}

# P66 / PB 2 official Bodmer Lab IIIF.
manifest_url="https://bodmerlab.unige.ch/constellations/papyri/manifest/1072205287"
r=session.get(manifest_url,timeout=120); r.raise_for_status()
raw=r.content
mdir=ROOT/"sources/manuscripts/P66/raw/bodmer"
mdir.mkdir(parents=True,exist_ok=True)
(mdir/"iiif-manifest.json").write_bytes(raw)
obj=r.json()
canvases=(obj.get("sequences") or [{}])[0].get("canvases") or obj.get("items") or []
report["P66"]["manifest_url"]=manifest_url
report["P66"]["manifest_sha256"]=hashlib.sha256(raw).hexdigest()
report["P66"]["canvas_count"]=len(canvases)

for idx,c in enumerate(canvases,1):
    label=c.get("label")
    if isinstance(label,dict):
        label=" | ".join(sum(([str(y) for y in x] if isinstance(x,list) else [str(x)] for x in label.values()),[]))
    label=str(label or idx)
    service=None
    if c.get("images"):
        res=c["images"][0].get("resource") or {}
        svc=res.get("service")
        if isinstance(svc,list): svc=svc[0] if svc else None
        if isinstance(svc,dict): service=svc.get("@id") or svc.get("id")
    if not service and c.get("items"):
        try:
            body=c["items"][0]["items"][0]["body"]
            svc=body.get("service")
            if isinstance(svc,list): svc=svc[0] if svc else None
            if isinstance(svc,dict): service=svc.get("id") or svc.get("@id")
        except Exception: pass
    if not service:
        report["P66"]["files"].append({"status":"failed","label":label,"error":"no image service"}); continue
    # IIIF v2 service; pct:100 is what Bodmer's own viewer exposes.
    url=service.rstrip("/")+"/full/pct:100/0/default.jpg"
    safe=f"{idx:03d}.jpg"
    item=download(url,ROOT/"sources/manuscripts/P66/images/bodmer"/safe,min_bytes=10000)
    item.update({"label":label,"canvas_id":c.get("@id") or c.get("id"),"image_service":service})
    report["P66"]["files"].append(item)

# P104: current high-resolution archival copies sourced from Oxford SDS, mirrored through Commons.
commons_files=[
 ("recto","Oxford, Sackler Library Ms LXIV 4404 (Papyrus 104) recto Matt 21, 34-37.jpg"),
 ("verso","Oxford, Sackler Library Ms LXIV 4404 (Papyrus 104) verso Matt 21, 43-45.jpg"),
]
for side,name in commons_files:
    url="https://commons.wikimedia.org/wiki/Special:Redirect/file/"+quote(name,safe="")
    item=download(url,ROOT/f"sources/manuscripts/P104/images/oxford-commons/{side}.jpg",min_bytes=100000)
    item.update({
      "side":side,
      "described_source":"https://portal.sds.ox.ac.uk/articles/online_resource/P_Oxy_LXIV_4404_Matthew_XXI_34-37_43_and_45_/21178702",
      "license":"Public Domain / Public Domain Mark as described by Wikimedia Commons"
    })
    report["P104"]["files"].append(item)

# P137 official EES image.
p137_url="https://www.ees.ac.uk/static/5f06544239c2a2f77ad812ed57681219/opengraphimage_83f4e8796336604b59d7216d0ecd81a5_4a7c7e45a350/POxy-LXXXIII-5345.jpg"
item=download(p137_url,ROOT/"sources/manuscripts/P137/images/ees/POxy-LXXXIII-5345.jpg",min_bytes=10000)
item.update({"source_page":"https://www.ees.ac.uk/resource/p-oxy-lxxxiii-5345.html"})
report["P137"]["files"].append(item)

for ms in report:
    files=report[ms]["files"]
    report[ms]["mirrored_or_present"]=sum(x.get("status") in ("mirrored","present") for x in files)
    report[ms]["failed"]=sum(x.get("status")=="failed" for x in files)
    report[ms]["total_bytes"]=sum(x.get("size") or 0 for x in files)
    report[ms]["complete"]=report[ms]["failed"]==0 and bool(files)

out=DER/"fallback-facsimile-mirror-summary.json"
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:{x:v for x,v in val.items() if x!="files"} for k,val in report.items()},ensure_ascii=False,indent=2))
