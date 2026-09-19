#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,re
from html import unescape
from pathlib import Path
from urllib.parse import urljoin
import requests

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"sources/manuscripts/fallback-discovery"
OUT.mkdir(parents=True,exist_ok=True)

TARGETS={
 "P66-bodmer":{
   "urls":[
     "https://bodmerlab.unige.ch/constellations/papyri/barcode/1072205287",
     "https://bodmerlab.unige.ch/constellations/papyri/mirador/1072205287",
   ]
 },
 "P104-csntm":{
   "urls":["https://manuscripts.csntm.org/manuscript/View/GA_P104"]
 },
 "P137-ees":{
   "urls":["https://www.ees.ac.uk/resource/p-oxy-lxxxiii-5345.html"]
 }
}

session=requests.Session()
session.headers.update({"User-Agent":"El-Relato-preservation/1.0","Accept-Encoding":"identity"})

href_re=re.compile(r'''(?:href|src)=["']([^"']+)["']''',re.I)
url_re=re.compile(r'''https?://[^"'<>\s]+''',re.I)

def score(link):
    s=link.lower()
    points=0
    for term,w in [
      ("iiif",10),("manifest",10),("mirador",6),(".json",5),
      (".jpg",5),(".jpeg",5),(".png",5),(".jp2",5),(".tif",5),
      (".pdf",4),("download",3),("5345",8),("4404",8),("pb2",5),
      ("bodmer",4),("oxyrhynchus",4)
    ]:
      if term in s: points+=w
    return points

summary={"targets":[]}
for name,cfg in TARGETS.items():
    d=OUT/name
    d.mkdir(parents=True,exist_ok=True)
    all_links=set()
    pages=[]
    for i,url in enumerate(cfg["urls"],1):
        r=session.get(url,timeout=90)
        r.raise_for_status()
        raw=r.content
        suffix=".html"
        p=d/f"page-{i}{suffix}"
        p.write_bytes(raw)
        text=r.text
        links=set()
        for x in href_re.findall(text):
            links.add(urljoin(r.url,unescape(x)))
        for x in url_re.findall(text):
            links.add(unescape(x).rstrip("\\);,"))
        all_links.update(links)
        pages.append({
          "url":r.url,"status":r.status_code,"bytes":len(raw),
          "sha256":hashlib.sha256(raw).hexdigest(),"local_path":str(p.relative_to(ROOT))
        })
    ranked=sorted(
      [{"url":x,"score":score(x)} for x in all_links if score(x)>0],
      key=lambda x:(-x["score"],x["url"])
    )
    (d/"discovered-links.json").write_text(
      json.dumps(ranked,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    summary["targets"].append({"name":name,"pages":pages,"candidate_links":ranked[:100]})

(ROOT/"data/derived/manuscripts").mkdir(parents=True,exist_ok=True)
(ROOT/"data/derived/manuscripts/fallback-source-discovery.json").write_text(
 json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
)
print(json.dumps(summary,ensure_ascii=False,indent=2))
