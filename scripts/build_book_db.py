#!/usr/bin/env python3
import base64,csv,json,math,re,sqlite3,statistics,zlib
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BOOK=ROOT/"book"; DATA=BOOK/"data"; OUT=BOOK/"el-relato-book.sqlite"
VERSES=ROOT/"data/normalized/sblgnt/edition-verses.jsonl"
TOKENS=ROOT/"data/normalized/sblgnt/tokens.jsonl"
TAGNT=ROOT/"data/normalized/stepbible/tagnt-rows.jsonl"
SRC="edition:sblgnt:2010"; TAGNT_SRC="src:stepbible:tagnt-mat-jhn"; EDITION="edition:el-relato:grc-sblgnt-2010:v1"
BOOKS={"Mt":("Matthew","matthew"),"Mc":("Mark","mark"),"L":("Luke","luke"),"J":("John","john")}
RX=re.compile(r"^(Mt|Mc|L|J)(\d+):(\d+)([a-z])?(?:-(\d+))?$")

def csvrows(p):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def jsonl(p):
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():yield json.loads(line)
def parse(ref):
    m=RX.fullmatch(ref.strip())
    if not m:raise ValueError(f"Unsupported reference: {ref}")
    b,c,v,s,e=m.groups(); name,slug=BOOKS[b]
    return b,name,slug,int(c),int(v),int(e or v),s
def toktext(ts):
    return " ".join(((t.get("prefix_before")or"").lstrip())+(t.get("surface")or"")+((t.get("punctuation_after")or"").rstrip()) for t in ts).strip()
def bonus(t):
    p=t.get("punctuation_after")or""
    return 2.5 if any(x in p for x in ".·;:?!") else (1.25 if "," in p else 0)
def split(ts,labels,weights):
    n=len(ts); k=len(labels)
    if k==1:return {labels[0]:ts}
    if n<k:return {x:(ts[i:i+1] if i<n else []) for i,x in enumerate(labels)}
    total=sum(weights)or k; cum=0; cuts=[]; prev=0
    for i in range(k-1):
        cum+=weights[i]; ideal=n*cum/total; rem=k-i-1
        lo,hi=prev+1,n-rem; rad=max(3,round(n*.12))
        a,b=max(lo,math.floor(ideal)-rad),min(hi,math.ceil(ideal)+rad)
        if a>b:a,b=lo,hi
        pos=min(range(a,b+1),key=lambda q:(abs(q-ideal)-bonus(ts[q-1])+(0.4 if q-prev==1 else 0),q))
        cuts.append(pos); prev=pos
    starts=[0]+cuts; ends=cuts+[n]
    return {lab:ts[a:b] for lab,a,b in zip(labels,starts,ends)}

chapters=csvrows(DATA/"chapters.csv"); scenes=csvrows(DATA/"scenes.csv")
parts=sorted(DATA.glob("structure.part*.b64"))
if not parts:raise SystemExit("Missing book/data/structure.part*.b64")
compact=json.loads(zlib.decompress(base64.b64decode("".join(p.read_text().strip() for p in parts))).decode())
scene_ch={int(x["scene_number"]):x["chapter_number"] for x in scenes}
scene_ord=defaultdict(int); units=[]
for i,(sn,ref,w) in enumerate(compact,1):
    sn=int(sn); scene_ord[sn]+=1
    units.append({"unit_id":f"unit:{i:04d}","chapter_number":scene_ch[sn],"scene_number":sn,
                  "scene_order":scene_ord[sn],"global_order":i,"reference":str(ref),"weight":int(w)})
if (len(chapters),len(scenes),len(units))!=(6,120,4123):raise SystemExit("Book structure count mismatch")

verse_text={(r["book"],int(r["chapter"]),int(r["verse"])):r["text"] for r in jsonl(VERSES)}
token_map=defaultdict(list)
for r in jsonl(TOKENS):token_map[(r["book"],int(r["chapter"]),int(r["verse"]))].append(r)
for k in token_map:token_map[k].sort(key=lambda x:int(x["position"]))
tagnt_map=defaultdict(list)
for r in jsonl(TAGNT):tagnt_map[(r["book"],int(r["chapter"]),int(r["verse"]))].append(r)
for k in tagnt_map:tagnt_map[k].sort(key=lambda x:int(x["row_position"]))

weights=defaultdict(lambda:defaultdict(list))
for u in units:
    for comp in u["reference"].split(";"):
        b,name,slug,c,v,e,s=parse(comp)
        if s:weights[(name,c,v)][s].append(u["weight"])
segdef={}
for key,d in weights.items():
    mx=max(ord(x)-97 for x in d); labels=[chr(97+i) for i in range(mx+1)]
    known=[statistics.median(v) for v in d.values()]; fb=statistics.median(known) if known else 1
    segdef[key]=(labels,[float(statistics.median(d[x])) if x in d else float(fb) for x in labels])
segcache={}

def piece(comp):
    b,name,slug,c,v,e,s=parse(comp); pids=[f"passage:{slug}:{c}:{x}" for x in range(v,e+1)]
    if s:
        key=(name,c,v); ts=token_map.get(key,[])
        if not ts:return None,pids,[],"missing-source",0.0,"missing-source",SRC
        if key not in segcache:
            labs,ws=segdef.get(key,([s],[1.0]))
            if s not in labs:
                labs=[chr(97+i) for i in range(max(ord(s)-96,len(labs)))]; ws=[1.0]*len(labs)
            segcache[key]=split(ts,labs,ws)
        st=segcache[key].get(s,[])
        if not st:return None,pids,[],"missing-segment",0.0,"segmented-proportional-punctuation-v1",SRC
        return toktext(st),pids,[x["id"] for x in st],"ok",0.68,"segmented-proportional-punctuation-v1",SRC
    if all((name,c,x) in verse_text for x in range(v,e+1)):
        texts=[]; tids=[]
        for x in range(v,e+1):
            key=(name,c,x); texts.append(verse_text[key]); tids += [t["id"] for t in token_map.get(key,[])]
        return " ".join(texts).strip(),pids,tids,"ok",1.0,"exact-source-range",SRC

    # SBLGNT intentionally omits a small set of later textual additions.
    # If any verse in the requested range is absent, materialize the whole
    # witness from TAGNT so a single witness never silently mixes editions.
    texts=[]; tids=[]; tpids=[]
    for x in range(v,e+1):
        rows=tagnt_map.get((name,c,x),[])
        if not rows:return None,tpids,tids,"missing-source",0.0,"missing-source",TAGNT_SRC
        greek=" ".join((r.get("greek") or "").strip() for r in rows if (r.get("greek") or "").strip()).strip()
        if not greek:return None,tpids,tids,"missing-source",0.0,"missing-source",TAGNT_SRC
        texts.append(greek); tids += [r["id"] for r in rows]; tpids.append(f"tagnt-ref:{slug}:{c}:{x}")
    return " ".join(texts).strip(),tpids,tids,"ok",1.0,"exact-tagnt-fallback",TAGNT_SRC

if OUT.exists():OUT.unlink()
db=sqlite3.connect(OUT); db.execute("PRAGMA foreign_keys=ON")
db.executescript((BOOK/"schema.sql").read_text())
prov=json.loads((DATA/"provenance.json").read_text()); now=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
meta={"book_id":"book:el-relato","title":"El Relato","schema_version":"1","book_database_version":"1","created_at":now,
      "structure_units":"4123","structure_scenes":"120","structure_chapters":"6","greek_source_edition":SRC,
      "primary_reference_policy":"first-reference-component","microsegment_policy":"editorial-fragment-weight + Greek punctuation; heuristic V1",
      "fallback_source_policy":"SBLGNT primary; exact TAGNT fallback only when the requested SBLGNT verse is absent",
      "structure_source_sha256":prov["book_structure_source"]["sha256"],"segmentation_helper_sha256":prov["segmentation_helper"]["sha256"]}
db.executemany("insert into metadata values (?,?)",meta.items())
db.executemany("insert into chapters values (?,?,?)",[(x["chapter_number"],int(x["chapter_order"]),x["title"]) for x in chapters])
db.executemany("insert into scenes values (?,?,?,?)",[(int(x["scene_number"]),x["chapter_number"],int(x["scene_order_in_chapter"]),x["title"]) for x in scenes])
db.executemany("insert into units values (?,?,?,?,?,?,?,?)",[(u["unit_id"],u["chapter_number"],u["scene_number"],u["scene_order"],u["global_order"],u["reference"],u["weight"],u["reference"].split(";")[0]) for u in units])
db.execute("insert into source_editions values (?,?,?,?,?,?)",(SRC,"SBL Greek New Testament","2010","grc","data/normalized/sblgnt/","Primary Greek source."))
db.execute("insert into source_editions values (?,?,?,?,?,?)",(TAGNT_SRC,"STEPBible TAGNT Mat-Jhn",None,"grc","data/normalized/stepbible/tagnt-rows.jsonl","Fallback only for requested verses absent from SBLGNT; never silently mixed within one witness."))
db.execute("insert into editions values (?,?,?,?,?,?,?,?,?,?,?)",(EDITION,"book:el-relato","grc",None,"El Relato — Griego fuente (SBLGNT 2010 + TAGNT fallback) — V1","source-derived-master","1","First reference is primary; parallels retained; SBLGNT primary; TAGNT fallback for SBL-omitted verses; microsegments heuristic V1.",SRC,"draft-source-derived",now))

stats=defaultdict(int)
for u in units:
    primary=None; ptext=None; pstatus="source-missing"
    for j,comp in enumerate([x.strip() for x in u["reference"].split(";") if x.strip()],1):
        b,name,slug,c,v,e,s=parse(comp); text,pids,tids,status,conf,method,source_id=piece(comp)
        wid=f'{u["unit_id"]}:w{j}'; stats["witnesses"]+=1
        stats["heuristic_segment_witness_materializations" if method.startswith("segmented-") else ("tagnt_fallback_witness_materializations" if method=="exact-tagnt-fallback" else "exact_witness_materializations")] += (status=="ok")
        if status!="ok":
            stats["unresolved_witnesses"]+=1
            db.execute("insert into validation_issues(severity,code,unit_id,reference_component,message) values (?,?,?,?,?)",
                       ("ERROR","SOURCE_REFERENCE_UNRESOLVED",u["unit_id"],comp,f"Could not materialize {comp} from {SRC}."))
        db.execute("insert into unit_witnesses values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (wid,u["unit_id"],j,comp,b,c,v,e,s,text,source_id,json.dumps(pids,separators=(",",":")),
                    json.dumps(tids,separators=(",",":")),method,conf,status))
        if j==1:primary,ptext,pstatus=wid,text,("ok" if status=="ok" else "source-missing")
    db.execute("insert into unit_texts values (?,?,?,?,?,?)",(EDITION,u["unit_id"],ptext,primary,"primary-first-witness-v1",pstatus))

stats.update({"chapters":6,"scenes":120,"units":4123,"primary_text_rows":4123,"segmented_base_verses":len(segdef)})
db.executemany("insert into build_stats values (?,?)",[(k,str(v)) for k,v in stats.items()])
if db.execute("select count(*) from units").fetchone()[0]!=4123 or db.execute("select count(*) from unit_texts").fetchone()[0]!=4123:raise RuntimeError("Structural validation failed")
if db.execute("pragma foreign_key_check").fetchall():raise RuntimeError("Foreign key validation failed")
db.commit(); db.execute("vacuum"); db.close()
print(json.dumps({"output":"book/el-relato-book.sqlite",**stats},ensure_ascii=False,indent=2))
