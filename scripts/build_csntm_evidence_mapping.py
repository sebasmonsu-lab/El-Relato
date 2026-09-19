#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MSS=["P4","P45","P52","P66","P104"]
MS_ID={"P4":"ms:ga:p4","P45":"ms:ga:p45","P52":"ms:ga:p52","P66":"ms:ga:p66","P104":"ms:ga:p104"}
SRC_ID={"P4":"src:csntm:p4","P45":"src:csntm:p45","P52":"src:csntm:p52","P66":"src:csntm:p66","P104":"src:csntm:p104"}
BOOK={"Matt":"Matthew","Matthew":"Matthew","Mark":"Mark","Luke":"Luke","John":"John"}
REF_RE=re.compile(r"\b(Matt|Matthew|Mark|Luke|John)\s+(\d+)\.(\d+)\b")

def safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+","_",s).strip("_") or "image"

def read_jsonl(path):
    if not path.exists(): return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def main():
    images=[]; att_map={}
    missing_files=[]
    for ms in MSS:
        rows=read_jsonl(ROOT/f"sources/manuscripts/{ms}/raw/csntm/image-details.jsonl")
        for row in rows:
            name=row["image_name"]
            dest=ROOT/f"sources/manuscripts/{ms}/images/csntm"/safe(name)
            if not dest.exists():
                missing_files.append({"manuscript":ms,"image_name":name})
                continue
            data=dest.read_bytes()
            image_id=f"image:csntm:{ms.lower()}:{row['image_id']}"
            # derive upstream service url from the known CSNTM layout
            group="GA_P66_Bodmer" if ms=="P66" else f"GA_{ms}"
            upstream=f"https://images.csntm.org/IIIFServer.ashx/{group}/{name}/full/full/0/native.jpg"
            images.append({
                "id":image_id,
                "manuscript_id":MS_ID[ms],
                "source_id":SRC_ID[ms],
                "folio":None,
                "page_label":name,
                "side":"unknown",
                "local_path":dest.relative_to(ROOT).as_posix(),
                "upstream_url":upstream,
                "sha256":hashlib.sha256(data).hexdigest(),
                "mime_type":"image/jpeg",
                "width":None,
                "height":None,
                "notes":f"CSNTM image id {row['image_id']}"
            })
            refs=[]
            for m in REF_RE.finditer(row.get("details_text") or ""):
                b=BOOK[m.group(1)]; ch=int(m.group(2)); v=int(m.group(3))
                refs.append((b,ch,v))
            for b,ch,v in refs:
                slug=b.lower()
                passage=f"passage:{slug}:{ch}:{v}"
                key=(MS_ID[ms],passage)
                a=att_map.setdefault(key,{
                    "id":f"attest:{ms.lower()}:{slug}:{ch}:{v}",
                    "manuscript_id":MS_ID[ms],
                    "passage_id":passage,
                    "reading_id":None,
                    "image_ids":[],
                    "transcription_ids":[],
                    "status":"extant",
                    "source_id":SRC_ID[ms],
                    "notes":"Passage-to-image mapping derived from preserved CSNTM ImageDetails metadata."
                })
                if image_id not in a["image_ids"]: a["image_ids"].append(image_id)

    images.sort(key=lambda x:x["id"])
    atts=sorted(att_map.values(),key=lambda x:x["id"])
    out=ROOT/"data/normalized/manuscript-evidence"
    out.mkdir(parents=True,exist_ok=True)
    with (out/"images.jsonl").open("w",encoding="utf-8",newline="\n") as fh:
        for x in images: fh.write(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n")
    with (out/"witness-attestations.jsonl").open("w",encoding="utf-8",newline="\n") as fh:
        for x in atts: fh.write(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n")
    report={
        "manuscript_images":len(images),
        "witness_attestations":len(atts),
        "missing_image_files":len(missing_files),
        "missing_samples":missing_files[:100],
        "by_manuscript":{
            ms:{
                "images":sum(x["manuscript_id"]==MS_ID[ms] for x in images),
                "attestations":sum(x["manuscript_id"]==MS_ID[ms] for x in atts),
            } for ms in MSS
        }
    }
    p=ROOT/"data/derived/manuscripts/csntm-evidence-mapping-report.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
