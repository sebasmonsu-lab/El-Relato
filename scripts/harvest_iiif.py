#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]

def label_text(value):
    if value is None: return None
    if isinstance(value,str): return value
    if isinstance(value,dict):
        if "@value" in value: return str(value["@value"])
        vals=[]
        for v in value.values():
            if isinstance(v,list): vals.extend(str(x) for x in v)
            elif isinstance(v,str): vals.append(v)
        return " | ".join(vals) if vals else json.dumps(value,ensure_ascii=False)
    return str(value)

def extract_canvas(c):
    row={
      "id":c.get("@id") or c.get("id"),
      "label":label_text(c.get("label")),
      "width":c.get("width"),"height":c.get("height"),
      "image_id":None,"image_service":None
    }
    images=c.get("images") or []
    if images:
        res=images[0].get("resource") or {}
        row["image_id"]=res.get("@id") or res.get("id")
        service=res.get("service")
        if isinstance(service,list): service=service[0] if service else None
        if isinstance(service,dict): row["image_service"]=service.get("@id") or service.get("id")
    if not row["image_id"]:
        pages=c.get("items") or []
        if pages:
            anns=pages[0].get("items") or []
            if anns:
                body=anns[0].get("body") or {}
                row["image_id"]=body.get("id") or body.get("@id")
                service=body.get("service")
                if isinstance(service,list): service=service[0] if service else None
                if isinstance(service,dict): row["image_service"]=service.get("id") or service.get("@id")
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--id",required=True)
    ap.add_argument("--url",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()

    out=ROOT/args.output_dir
    out.mkdir(parents=True,exist_ok=True)
    r=requests.get(args.url,headers={"User-Agent":"El-Relato-preservation/1.0","Accept-Encoding":"identity"},timeout=120)
    r.raise_for_status()
    raw=r.content
    obj=r.json()
    (out/"iiif-manifest.json").write_bytes(raw)

    seqs=obj.get("sequences") or []
    canvases=(seqs[0].get("canvases") or []) if seqs else []
    version="2"
    if not canvases:
        canvases=obj.get("items") or []
        version="3"

    rows=[extract_canvas(c) for c in canvases]
    with (out/"iiif-canvases.jsonl").open("w",encoding="utf-8",newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
    summary={
      "id":args.id,"source_url":args.url,
      "iiif_presentation_version_detected":version,
      "manifest_bytes":len(raw),
      "manifest_sha256":hashlib.sha256(raw).hexdigest(),
      "canvas_count":len(rows),
      "canvases_with_image_service":sum(bool(x["image_service"]) for x in rows),
      "canvases_with_dimensions":sum(x["width"] is not None and x["height"] is not None for x in rows),
      "first_labels":[x["label"] for x in rows[:20]],
      "last_labels":[x["label"] for x in rows[-20:]],
    }
    (out/"iiif-summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
