#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,time
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
TARGETS=[
 ("P52","https://epapers.bham.ac.uk/id/eprint/1754/7/04_P52.xml","https://epapers.bham.ac.uk/id/eprint/1754/"),
 ("P66","https://epapers.bham.ac.uk/id/eprint/1759/10/04_P66.xml","https://epapers.bham.ac.uk/id/eprint/1759/"),
 ("P75","https://epapers.bham.ac.uk/id/eprint/1742/10/04_P75.xml","https://epapers.bham.ac.uk/id/eprint/1742/"),
]
session=requests.Session()
session.headers.update({"User-Agent":"El-Relato-preservation/1.0","Accept-Encoding":"identity"})
report={"source":"International Greek New Testament Project / University of Birmingham ePapers","license_note":"CC BY-NC-SA as specified in transcription headers and repository records","items":[]}

for ms,xml_url,record_url in TARGETS:
    out=ROOT/f"sources/manuscripts/{ms}/transcription/raw/igntp"
    out.mkdir(parents=True,exist_ok=True)
    item={"manuscript":ms,"xml_url":xml_url,"record_url":record_url}
    for label,url,name,minsize in [
      ("xml",xml_url,f"04_{ms}.xml",1000),
      ("record",record_url,"repository-record.html",1000),
    ]:
        last=None
        for a in range(4):
            try:
                r=session.get(url,timeout=120); r.raise_for_status()
                data=r.content
                if len(data)<minsize: raise RuntimeError(f"too small {len(data)}")
                p=out/name; p.write_bytes(data)
                item[label]={
                  "local_path":str(p.relative_to(ROOT)),
                  "resolved_url":r.url,
                  "bytes":len(data),
                  "sha256":hashlib.sha256(data).hexdigest(),
                  "content_type":r.headers.get("Content-Type"),
                }
                break
            except Exception as exc:
                last=exc; time.sleep(2**a)
        else:
            item[label]={"error":f"{type(last).__name__}: {last}"}
    item["complete"]="error" not in item.get("xml",{}) and "error" not in item.get("record",{})
    report["items"].append(item)

p=ROOT/"data/derived/manuscripts/igntp-transcription-mirror-summary.json"
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if not all(x["complete"] for x in report["items"]):
    raise SystemExit("One or more IGNTP transcriptions failed to preserve")
print(json.dumps(report,ensure_ascii=False,indent=2))
