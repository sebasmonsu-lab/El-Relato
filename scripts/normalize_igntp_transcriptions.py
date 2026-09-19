#!/usr/bin/env python3
from __future__ import annotations
import json,re,xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NS="{http://www.tei-c.org/ns/1.0}"
TARGETS={
 "P52":{"ms":"ms:ga:p52","source":"src:igntp:p52","path":"sources/manuscripts/P52/transcription/raw/igntp/04_P52.xml","min":5},
 "P66":{"ms":"ms:ga:p66","source":"src:igntp:p66","path":"sources/manuscripts/P66/transcription/raw/igntp/04_P66.xml","min":500},
 "P75":{"ms":"ms:ga:p75","source":"src:igntp:p75","path":"sources/manuscripts/P75/transcription/raw/igntp/04_P75.xml","min":400},
}
REF=re.compile(r"B04K(\d+)V(\d+)$")
OUT=ROOT/"data/normalized/transcriptions"
REPORT=ROOT/"data/derived/manuscripts/igntp-normalization-report.json"
OUT.mkdir(parents=True,exist_ok=True); REPORT.parent.mkdir(parents=True,exist_ok=True)

def local(tag): return tag.rsplit("}",1)[-1]

def render(node):
    tag=local(node.tag)
    if tag=="gap":
        unit=node.attrib.get("unit","gap")
        extent=node.attrib.get("extent","")
        return f"⟦lacuna:{extent or '?'} {unit}⟧"
    if tag=="app":
        # A diplomatic base-text view: prefer the explicitly encoded original reading.
        rdgs=[x for x in list(node) if local(x.tag)=="rdg"]
        orig=next((x for x in rdgs if x.attrib.get("type")=="orig"),rdgs[0] if rdgs else None)
        return render(orig) if orig is not None else ""
    if tag=="rdg":
        if (node.text or "").strip()=="OM":
            return "⟦om⟧"
    parts=[]
    if node.text: parts.append(node.text)
    for child in list(node):
        parts.append(render(child))
        if child.tail: parts.append(child.tail)
    text="".join(parts)
    if tag=="w":
        return " "+text.strip()+" "
    if tag=="pc":
        return text.strip()
    return text

def count_features(ab):
    counts={"gap":0,"supplied":0,"unclear":0,"apparatus":0,"nomina_sacra":0}
    for el in ab.iter():
        t=local(el.tag)
        if t=="gap": counts["gap"]+=1
        elif t=="supplied": counts["supplied"]+=1
        elif t=="unclear": counts["unclear"]+=1
        elif t=="app": counts["apparatus"]+=1
        elif t=="abbr" and el.attrib.get("type")=="nomSac": counts["nomina_sacra"]+=1
    return counts

def clean(text):
    return " ".join(text.split()).replace(" ·","·").replace(" .",".").replace(" ,",",")

def main():
    all_rows=[]; report={"manuscripts":{}}
    for label,cfg in TARGETS.items():
        root=ET.parse(ROOT/cfg["path"]).getroot()
        rows=[]; features={k:0 for k in ("gap","supplied","unclear","apparatus","nomina_sacra")}
        for ab in root.iter(NS+"ab"):
            n=ab.attrib.get("n","")
            m=REF.fullmatch(n)
            if not m: continue
            chapter,verse=map(int,m.groups())
            f=count_features(ab)
            for k,v in f.items(): features[k]+=v
            text=clean(render(ab))
            row={
              "id":f"tx:igntp:{label.lower()}:john:{chapter}:{verse}",
              "manuscript_id":cfg["ms"],
              "source_id":cfg["source"],
              "image_id":None,
              "passage_ids":[f"passage:john:{chapter}:{verse}"],
              "layer":"diplomatic",
              "format":"plain",
              "text":text,
              "local_path":cfg["path"],
              "notes":f"Derived from IGNTP TEI {n}; original-reading branch preferred where <app> is encoded. Raw TEI remains authoritative."
            }
            rows.append(row)
        ids=[x["id"] for x in rows]
        if len(ids)!=len(set(ids)): raise RuntimeError(f"{label}: duplicate verse IDs")
        if len(rows)<cfg["min"]: raise RuntimeError(f"{label}: suspiciously low verse count {len(rows)}")
        all_rows.extend(rows)
        report["manuscripts"][label]={"normalized_units":len(rows),"features":features}

    # Append to a dedicated IGNTP file, avoiding collision with Sinaiticus.
    path=OUT/"igntp-papyri.jsonl"
    with path.open("w",encoding="utf-8",newline="\n") as fh:
        for row in all_rows:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
    report["total_units"]=len(all_rows)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
