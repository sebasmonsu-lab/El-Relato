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

def read_json(path):
    if not path.exists(): return None
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def add_image(images,image_ids,row):
    if row["id"] in image_ids: return
    images.append(row); image_ids.add(row["id"])

def attestation(att_map,ms_id,passage,source_id,notes):
    key=(ms_id,passage)
    if key not in att_map:
        slug=passage.split(":")[1]
        rest=passage.split(":")[2:]
        ms_short=ms_id.split(":")[-1]
        att_map[key]={
          "id":"attest:"+ms_short+":"+slug+":"+":".join(rest),
          "manuscript_id":ms_id,"passage_id":passage,"reading_id":None,
          "image_ids":[],"transcription_ids":[],"status":"extant",
          "source_id":source_id,"notes":notes
        }
    return att_map[key]

def main():
    images=[]; image_ids=set(); att_map={}; missing_files=[]

    # 1) CSNTM image + passage metadata.
    for ms in MSS:
        rows=read_jsonl(ROOT/f"sources/manuscripts/{ms}/raw/csntm/image-details.jsonl")
        for row in rows:
            name=row["image_name"]
            dest=ROOT/f"sources/manuscripts/{ms}/images/csntm"/safe(name)
            if not dest.exists():
                missing_files.append({"manuscript":ms,"image_name":name})
                continue
            image_id=f"image:csntm:{ms.lower()}:{row['image_id']}"
            group="GA_P66_Bodmer" if ms=="P66" else f"GA_{ms}"
            upstream=f"https://images.csntm.org/IIIFServer.ashx/{group}/{name}/full/full/0/native.jpg"
            add_image(images,image_ids,{
                "id":image_id,"manuscript_id":MS_ID[ms],"source_id":SRC_ID[ms],
                "folio":None,"page_label":name,"side":"unknown",
                "local_path":dest.relative_to(ROOT).as_posix(),"upstream_url":upstream,
                "sha256":sha(dest),"mime_type":"image/jpeg","width":None,"height":None,
                "notes":f"CSNTM image id {row['image_id']}"
            })
            for m in REF_RE.finditer(row.get("details_text") or ""):
                b=BOOK[m.group(1)]; ch=int(m.group(2)); v=int(m.group(3))
                passage=f"passage:{b.lower()}:{ch}:{v}"
                a=attestation(att_map,MS_ID[ms],passage,SRC_ID[ms],
                    "Passage-to-image mapping derived from preserved CSNTM ImageDetails metadata.")
                if image_id not in a["image_ids"]: a["image_ids"].append(image_id)

    # 2) P66 official Bodmer IIIF fallback: preserve all images in canonical image index.
    fallback=read_json(ROOT/"data/derived/manuscripts/fallback-facsimile-mirror-summary.json") or {}
    for x in fallback.get("P66",{}).get("files",[]):
        if x.get("status") not in ("mirrored","present"): continue
        p=ROOT/x["path"]
        if not p.exists(): continue
        label=str(x.get("label") or p.stem)
        image_id=f"image:bodmer:p66:{safe(label).lower()}"
        add_image(images,image_ids,{
          "id":image_id,"manuscript_id":"ms:ga:p66","source_id":"src:bodmer:p66-facsimile",
          "folio":None,"page_label":label,"side":"unknown","local_path":x["path"],
          "upstream_url":x.get("url"),"sha256":x.get("sha256") or sha(p),
          "mime_type":"image/jpeg","width":None,"height":None,
          "notes":"Official Bodmer Lab IIIF canvas; passage mapping supplied separately by transcription."
        })

    # 3) P104 Oxford high-resolution recto/verso.
    p104_passages={
      "recto":[f"passage:matthew:21:{v}" for v in range(34,38)],
      "verso":[f"passage:matthew:21:{v}" for v in range(43,46)],
    }
    for x in fallback.get("P104",{}).get("files",[]):
        if x.get("status") not in ("mirrored","present"): continue
        side=x.get("side") or Path(x["path"]).stem
        p=ROOT/x["path"]
        if not p.exists(): continue
        image_id=f"image:oxford:p104:{side}"
        add_image(images,image_ids,{
          "id":image_id,"manuscript_id":"ms:ga:p104","source_id":"src:oxford:p104-facsimile",
          "folio":None,"page_label":side,"side":"recto" if side=="recto" else "verso",
          "local_path":x["path"],"upstream_url":x.get("url"),"sha256":x.get("sha256") or sha(p),
          "mime_type":"image/jpeg","width":None,"height":None,
          "notes":"Oxford P.Oxy. LXIV 4404 high-resolution archival copy."
        })
        for passage in p104_passages.get(side,[]):
            a=attestation(att_map,"ms:ga:p104",passage,"src:oxford:p104-facsimile",
                "Passage mapping follows P.Oxy. LXIV 4404 recto/verso contents.")
            if image_id not in a["image_ids"]: a["image_ids"].append(image_id)

    # 4) P75 complete Vatican image set; verse links come from IGNTP transcription.
    p75=read_json(ROOT/"data/derived/manuscripts/P75-facsimile-summary.json") or {}
    for i,x in enumerate(p75.get("files",[]),1):
        p=ROOT/x["path"]
        if not p.exists(): continue
        label=p.stem
        image_id=f"image:vatlib:p75:{safe(label).lower()}"
        add_image(images,image_ids,{
          "id":image_id,"manuscript_id":"ms:ga:p75","source_id":"src:vatlib:p75-facsimile",
          "folio":label,"page_label":label,"side":"recto" if label.endswith("r") else ("verso" if label.endswith("v") else "unknown"),
          "local_path":x["path"],"upstream_url":None,"sha256":x.get("sha256") or sha(p),
          "mime_type":"image/jpeg","width":None,"height":None,
          "notes":"Vatican DigiVatLib P75 facsimile; canvas source retained in raw IIIF manifest."
        })

    # 5) P137 primary EES publication PDF attests the published fragment.
    p137_pdf=ROOT/"sources/manuscripts/P137/raw/POxy-LXXXIII-5345-text-and-image.pdf"
    if p137_pdf.exists():
        for v in (7,8,9,16,17,18):
            attestation(att_map,"ms:ga:p137",f"passage:mark:1:{v}","src:ees:p137-edition-pdf",
                "Extant passage attested by preserved EES P.Oxy. LXXXIII 5345 publication PDF (text + photographic plate).")

    # 6) Every normalized diplomatic transcription becomes passage evidence.
    transcription_files=[
      ROOT/"data/normalized/transcriptions/sinaiticus-gospels.jsonl",
      ROOT/"data/normalized/transcriptions/igntp-papyri.jsonl",
    ]
    tx_count=0
    for tx_file in transcription_files:
        for tx in read_jsonl(tx_file):
            tx_count+=1
            for passage in tx.get("passage_ids") or []:
                a=attestation(att_map,tx["manuscript_id"],passage,tx.get("source_id"),
                    "Passage attestation derived from preserved normalized scholarly transcription.")
                if tx["id"] not in a["transcription_ids"]: a["transcription_ids"].append(tx["id"])

    images.sort(key=lambda x:x["id"])
    atts=sorted(att_map.values(),key=lambda x:x["id"])
    out=ROOT/"data/normalized/manuscript-evidence"
    out.mkdir(parents=True,exist_ok=True)
    with (out/"images.jsonl").open("w",encoding="utf-8",newline="\n") as fh:
        for x in images: fh.write(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n")
    with (out/"witness-attestations.jsonl").open("w",encoding="utf-8",newline="\n") as fh:
        for x in atts: fh.write(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n")

    all_ms=["p4","p45","p52","p66","p75","p104","p137","01","03"]
    report={
      "manuscript_images":len(images),
      "witness_attestations":len(atts),
      "normalized_transcription_units_processed":tx_count,
      "source_specific_missing_image_files":len(missing_files),
      "missing_samples":missing_files[:100],
      "by_manuscript":{
        ms:{
          "images":sum(x["manuscript_id"]==f"ms:ga:{ms}" for x in images),
          "attestations":sum(x["manuscript_id"]==f"ms:ga:{ms}" for x in atts),
          "attestations_with_images":sum(x["manuscript_id"]==f"ms:ga:{ms}" and bool(x["image_ids"]) for x in atts),
          "attestations_with_transcriptions":sum(x["manuscript_id"]==f"ms:ga:{ms}" and bool(x["transcription_ids"]) for x in atts),
        } for ms in all_ms
      }
    }
    p=ROOT/"data/derived/manuscripts/csntm-evidence-mapping-report.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
