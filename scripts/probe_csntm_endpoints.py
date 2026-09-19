#!/usr/bin/env python3
from __future__ import annotations
import json,re,urllib.parse
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
TARGETS={
 "P4":"https://manuscripts.csntm.org/manuscript/View/GA_P4",
 "P45":"https://manuscripts.csntm.org/manuscript/View/GA_P45",
 "P52":"https://manuscripts.csntm.org/manuscript/View/GA_P52",
 "P66":"https://manuscripts.csntm.org/Manuscript/Group/GA_P66_Bodmer",
 "P104":"https://manuscripts.csntm.org/manuscript/View/GA_P104",
}
PATTERNS=[
 r'https?://[^"\'<>\s]+',
 r'IIIFServer[^"\'<>\s]*',
 r'OpenSeaDragon[^"\'<>\s]*',
 r'[^"\'<>\s]+manifest\.json[^"\'<>\s]*',
 r'[^"\'<>\s]+\.jpg[^"\'<>\s]*',
 r'[^"\'<>\s]+\.jp2[^"\'<>\s]*',
 r'[^"\'<>\s]+/api/[^"\'<>\s]*',
]

ses=requests.Session()
ses.headers.update({"User-Agent":"El-Relato-preservation/1.0","Accept-Encoding":"identity"})

for ms,url in TARGETS.items():
    out=ROOT/f"sources/manuscripts/{ms}/raw/csntm"
    out.mkdir(parents=True,exist_ok=True)
    report={"manuscript":ms,"page_url":url,"status":None,"final_url":None,"scripts":[],"matches":[],"errors":[]}
    try:
        r=ses.get(url,timeout=60,allow_redirects=True)
        report["status"]=r.status_code; report["final_url"]=r.url
        html=r.text
        (out/"page.html").write_text(html,encoding="utf-8")
        found=set()
        for pat in PATTERNS:
            found.update(re.findall(pat,html,re.I))
        report["matches"]=sorted(found)[:500]

        script_srcs=re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html,re.I)
        for i,src in enumerate(script_srcs[:30]):
            full=urllib.parse.urljoin(r.url,src)
            item={"url":full,"status":None,"local":None,"matches":[]}
            try:
                jr=ses.get(full,timeout=45)
                item["status"]=jr.status_code
                if jr.ok and "javascript" in jr.headers.get("Content-Type","").lower():
                    name=f"script-{i:02d}.js"
                    (out/name).write_text(jr.text,encoding="utf-8")
                    item["local"]=name
                    hits=set()
                    for pat in PATTERNS:
                        hits.update(re.findall(pat,jr.text,re.I))
                    item["matches"]=sorted(hits)[:300]
            except Exception as exc:
                item["error"]=f"{type(exc).__name__}: {exc}"
            report["scripts"].append(item)
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    (out/"probe.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(ms, report["status"], len(report["matches"]), sum(len(x.get("matches",[])) for x in report["scripts"]))
