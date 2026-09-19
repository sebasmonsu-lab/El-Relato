#!/usr/bin/env python3
from __future__ import annotations
import html as htmlmod, json, re
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
MSS=["P4","P45","P52","P66","P104"]
ANCHOR_RE=re.compile(r'<a\s+href="#"\s+imageId="(?P<id>\d+)"\s+imageName="(?P<name>[^"]+)"',re.I)
TAG_RE=re.compile(r"<[^>]+>")

ses=requests.Session()
ses.headers.update({"User-Agent":"El-Relato-preservation/1.0","Accept-Encoding":"identity"})

for ms in MSS:
    base=ROOT/f"sources/manuscripts/{ms}/raw/csntm"
    page=(base/"page.html").read_text(encoding="utf-8")
    pairs=[]
    seen=set()
    for m in ANCHOR_RE.finditer(page):
        key=m.group("id")
        if key not in seen:
            seen.add(key)
            pairs.append((key,m.group("name")))
    outdir=base/"image-details"
    outdir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for image_id,name in pairs:
        url=f"https://manuscripts.csntm.org/manuscript/ImageDetails?imageId={image_id}"
        try:
            r=ses.get(url,timeout=45)
            r.raise_for_status()
            raw=r.text
            (outdir/f"{image_id}.html").write_text(raw,encoding="utf-8")
            txt=htmlmod.unescape(TAG_RE.sub(" ",raw))
            txt=" ".join(txt.split())
            rows.append({"image_id":int(image_id),"image_name":name,"details_url":url,"status":r.status_code,"details_text":txt})
        except Exception as exc:
            rows.append({"image_id":int(image_id),"image_name":name,"details_url":url,"status":None,"details_text":None,"error":f"{type(exc).__name__}: {exc}"})
    with (base/"image-details.jsonl").open("w",encoding="utf-8",newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
    print(ms,len(rows),sum(x.get("status")==200 for x in rows))
