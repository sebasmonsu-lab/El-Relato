#!/usr/bin/env python3
from __future__ import annotations

import json, math, re, sqlite3, statistics, zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
CANON = BOOK / "el-relato/canon/El Relato - Listado de referencias.xlsx"
EDITORIAL = BOOK / "el-relato/source/El Relato.docx"
OUT = BOOK / "el-relato-book.sqlite"
VERSES = ROOT / "data/normalized/sblgnt/edition-verses.jsonl"
TOKENS = ROOT / "data/normalized/sblgnt/tokens.jsonl"
SRC = "edition:sblgnt:2010"
EDITION = "edition:el-relato:grc-sblgnt-2010:v1"
BOOKS = {"Mt": ("Matthew","matthew"), "Mc": ("Mark","mark"), "L": ("Luke","luke"), "J": ("John","john")}
RX = re.compile(r"^(Mt|Mc|L|J)(\d+):(\d+)([a-z])?(?:-(\d+))?$")
NSX = {"x":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
NSW = {"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

def xlsx_rows(path: Path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows=[]
    for row in root.findall(".//x:sheetData/x:row", NSX):
        vals={}
        for c in row.findall("x:c", NSX):
            ref=c.attrib["r"]; col=re.match(r"[A-Z]+",ref).group()
            if c.attrib.get("t")=="inlineStr":
                val="".join(x.text or "" for x in c.findall(".//x:t",NSX))
            else:
                v=c.find("x:v",NSX); val=(v.text if v is not None else "")
            vals[col]=val
        rows.append(vals)
    hdr={k:v for k,v in rows[0].items()}
    return [{hdr[c]:r.get(c,"") for c in hdr} for r in rows[1:]]

def word_weights_from_docx(path: Path, expected_refs):
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read("word/document.xml"))
    weights=[]; idx=0; words=0
    for p in root.findall(".//w:body/w:p",NSW):
        for run in p.findall("w:r",NSW):
            txt="".join(t.text or "" for t in run.findall(".//w:t",NSW))
            va=run.find("w:rPr/w:vertAlign",NSW)
            is_super=va is not None and va.attrib.get("{%s}val"%NSW["w"])=="superscript"
            if is_super and idx < len(expected_refs) and txt.strip()==expected_refs[idx]:
                weights.append(max(1,words)); idx+=1; words=0
            elif not is_super:
                words += len(re.findall(r"\b[\wÁÉÍÓÚÜÑáéíóúüñ'-]+\b", txt, flags=re.UNICODE))
        if words: words += 1
    if idx != len(expected_refs):
        raise RuntimeError(f"Editorial DOCX reference alignment failed at {idx}/{len(expected_refs)}; expected {expected_refs[idx] if idx<len(expected_refs) else None}")
    return weights

def jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip(): yield json.loads(line)

def parse(ref):
    m=RX.fullmatch(ref.strip())
    if not m: raise ValueError(f"Unsupported reference: {ref}")
    b,c,v,s,e=m.groups(); name,slug=BOOKS[b]
    return b,name,slug,int(c),int(v),int(e or v),s

def toktext(ts):
    return " ".join(((t.get("prefix_before") or "").lstrip())+(t.get("surface") or "")+((t.get("punctuation_after") or "").rstrip()) for t in ts).strip()

def punctuation_bonus(t):
    p=t.get("punctuation_after") or ""
    return 2.5 if any(x in p for x in ".·;:?!") else (1.25 if "," in p else 0)

def split_tokens(ts,labels,weights):
    n=len(ts); k=len(labels)
    if k==1:return {labels[0]:ts}
    if n<k:return {x:(ts[i:i+1] if i<n else []) for i,x in enumerate(labels)}
    total=sum(weights) or k; cum=0; cuts=[]; prev=0
    for i in range(k-1):
        cum+=weights[i]; ideal=n*cum/total; rem=k-i-1
        lo,hi=prev+1,n-rem; rad=max(3,round(n*.12))
        a,b=max(lo,math.floor(ideal)-rad),min(hi,math.ceil(ideal)+rad)
        if a>b:a,b=lo,hi
        pos=min(range(a,b+1), key=lambda q:(abs(q-ideal)-punctuation_bonus(ts[q-1])+(0.4 if q-prev==1 else 0),q))
        cuts.append(pos); prev=pos
    starts=[0]+cuts; ends=cuts+[n]
    return {lab:ts[a:b] for lab,a,b in zip(labels,starts,ends)}

rows=xlsx_rows(CANON)
if len(rows)!=4123: raise SystemExit(f"Canonical Excel has {len(rows)} rows, expected 4123")
expected=[r["Referencia"] for r in rows]
weights_for_units=word_weights_from_docx(EDITORIAL, expected)

chapters=[]; scenes=[]; seen_ch=set(); seen_sc=set(); units=[]
for i,(r,w) in enumerate(zip(rows,weights_for_units),1):
    ch=r["Capítulo (#)"]; sn=int(float(r["Escena (#)"])); order=int(float(r["Orden"]))
    if ch not in seen_ch:
        seen_ch.add(ch); chapters.append((ch,len(chapters)+1,r["Capítulo (título)"]))
    if sn not in seen_sc:
        seen_sc.add(sn); scenes.append((sn,ch,1+sum(1 for x in scenes if x[1]==ch),r["Escena (título)"]))
    units.append({"unit_id":f"unit:{i:04d}","chapter_number":ch,"scene_number":sn,"scene_order":order,
                  "global_order":i,"reference":r["Referencia"],"weight":w})
if (len(chapters),len(scenes),len(units))!=(6,120,4123): raise SystemExit("Book structure count mismatch")

verse_text={(r["book"],int(r["chapter"]),int(r["verse"])):r["text"] for r in jsonl(VERSES)}
token_map=defaultdict(list)
for r in jsonl(TOKENS): token_map[(r["book"],int(r["chapter"]),int(r["verse"]))].append(r)
for k in token_map: token_map[k].sort(key=lambda x:int(x["position"]))

segment_weights=defaultdict(lambda:defaultdict(list))
for u in units:
    for comp in u["reference"].split(";"):
        b,name,slug,c,v,e,s=parse(comp)
        if s: segment_weights[(name,c,v)][s].append(u["weight"])
segment_defs={}
for key,d in segment_weights.items():
    mx=max(ord(x)-97 for x in d); labels=[chr(97+i) for i in range(mx+1)]
    known=[statistics.median(v) for v in d.values()]; fallback=statistics.median(known) if known else 1
    segment_defs[key]=(labels,[float(statistics.median(d[x])) if x in d else float(fallback) for x in labels])
segment_cache={}

def materialize(comp):
    b,name,slug,c,v,e,s=parse(comp); pids=[f"passage:{slug}:{c}:{x}" for x in range(v,e+1)]
    if s:
        key=(name,c,v); ts=token_map.get(key,[])
        if not ts:return None,pids,[],"missing-source",0.0,"missing-source"
        if key not in segment_cache:
            labels,ws=segment_defs.get(key,([s],[1.0]))
            if s not in labels:
                labels=[chr(97+i) for i in range(max(ord(s)-96,len(labels)))]; ws=[1.0]*len(labels)
            segment_cache[key]=split_tokens(ts,labels,ws)
        st=segment_cache[key].get(s,[])
        if not st:return None,pids,[],"missing-segment",0.0,"segmented-proportional-punctuation-v1"
        return toktext(st),pids,[x["id"] for x in st],"ok",0.68,"segmented-proportional-punctuation-v1"
    texts=[]; tids=[]
    for x in range(v,e+1):
        key=(name,c,x)
        if key not in verse_text:return None,pids,tids,"missing-source",0.0,"exact-source-range"
        texts.append(verse_text[key]); tids += [t["id"] for t in token_map.get(key,[])]
    return " ".join(texts).strip(),pids,tids,"ok",1.0,"exact-source-range"

if OUT.exists():OUT.unlink()
db=sqlite3.connect(OUT); db.execute("PRAGMA foreign_keys=ON")
db.executescript((BOOK/"schema.sql").read_text())
now=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
meta={"book_id":"book:el-relato","title":"El Relato","schema_version":"1","book_database_version":"1","created_at":now,
      "structure_units":"4123","structure_scenes":"120","structure_chapters":"6","greek_source_edition":SRC,
      "primary_reference_policy":"first-reference-component","microsegment_policy":"editorial-fragment-weight + Greek punctuation; heuristic V1"}
db.executemany("insert into metadata values (?,?)",meta.items())
db.executemany("insert into chapters values (?,?,?)",chapters)
db.executemany("insert into scenes values (?,?,?,?)",scenes)
db.executemany("insert into units values (?,?,?,?,?,?,?,?)",[(u["unit_id"],u["chapter_number"],u["scene_number"],u["scene_order"],u["global_order"],u["reference"],u["weight"],u["reference"].split(";")[0]) for u in units])
db.execute("insert into source_editions values (?,?,?,?,?,?)",(SRC,"SBL Greek New Testament","2010","grc","data/normalized/sblgnt/","Source corpus remains outside Book DB; Greek text and source locators are materialized here."))
db.execute("insert into editions values (?,?,?,?,?,?,?,?,?,?,?)",(EDITION,"book:el-relato","grc",None,"El Relato — Griego fuente (SBLGNT 2010) — V1","source-derived-master","1","First reference is primary; parallels retained; microsegments heuristic V1.",SRC,"draft-source-derived",now))

stats=defaultdict(int)
for u in units:
    primary=None; ptext=None; pstatus="source-missing"
    for j,comp in enumerate([x.strip() for x in u["reference"].split(";") if x.strip()],1):
        b,name,slug,c,v,e,s=parse(comp); text,pids,tids,status,conf,method=materialize(comp)
        wid=f'{u["unit_id"]}:w{j}'; stats["witnesses"]+=1
        stats["heuristic_segment_witness_materializations" if method.startswith("segmented-") else "exact_witness_materializations"] += int(status=="ok")
        if status!="ok":
            stats["unresolved_witnesses"]+=1
            db.execute("insert into validation_issues(severity,code,unit_id,reference_component,message) values (?,?,?,?,?)",
                       ("ERROR","SOURCE_REFERENCE_UNRESOLVED",u["unit_id"],comp,f"Could not materialize {comp} from {SRC}."))
        db.execute("insert into unit_witnesses values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (wid,u["unit_id"],j,comp,b,c,v,e,s,text,SRC,json.dumps(pids,separators=(",",":")),json.dumps(tids,separators=(",",":")),method,conf,status))
        if j==1:primary,ptext,pstatus=wid,text,("ok" if status=="ok" else "source-missing")
    db.execute("insert into unit_texts values (?,?,?,?,?,?)",(EDITION,u["unit_id"],ptext,primary,"primary-first-witness-v1",pstatus))

stats.update({"chapters":6,"scenes":120,"units":4123,"primary_text_rows":4123,"segmented_base_verses":len(segment_defs)})
db.executemany("insert into build_stats values (?,?)",[(k,str(v)) for k,v in stats.items()])
if db.execute("select count(*) from units").fetchone()[0]!=4123 or db.execute("select count(*) from unit_texts").fetchone()[0]!=4123:raise RuntimeError("Structural validation failed")
if db.execute("pragma foreign_key_check").fetchall():raise RuntimeError("Foreign key validation failed")
db.commit(); db.execute("vacuum"); db.close()
print(json.dumps({"output":"book/el-relato-book.sqlite",**stats},ensure_ascii=False,indent=2))
