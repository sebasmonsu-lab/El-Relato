#!/usr/bin/env python3
from __future__ import annotations
import collections, json, re, unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/normalized/variants"
DER=ROOT/"data/derived/variants"
OUT.mkdir(parents=True,exist_ok=True); DER.mkdir(parents=True,exist_ok=True)

FILES=[
 ROOT/"data/normalized/transcriptions/sinaiticus-gospels.jsonl",
 ROOT/"data/normalized/transcriptions/igntp-papyri.jsonl",
]
BOOK_NAMES={"matthew":"Matthew","mark":"Mark","luke":"Luke","john":"John"}

def rows(path):
    if not path.exists(): return []
    with path.open(encoding="utf-8-sig") as f:
        return [json.loads(x) for x in f if x.strip()]

def norm(s):
    s=unicodedata.normalize("NFD",s.casefold())
    out=[]
    for ch in s:
        cat=unicodedata.category(ch)
        if cat.startswith("M") or cat.startswith("P") or cat.startswith("Z") or ch.isspace():
            continue
        out.append(ch)
    return "".join(out).replace("ς","σ")

def ref(tx):
    pids=tx.get("passage_ids") or []
    if len(pids)!=1: return None
    parts=pids[0].split(":")
    if len(parts)!=4: return None
    _,book,ch,v=parts
    try: return (BOOK_NAMES[book.lower()],int(ch),int(v))
    except (KeyError,ValueError): return None

def incomplete(tx):
    text=tx.get("text") or ""
    return "⟦lacuna:" in text or not norm(text)

def main():
    alltx=[]
    for p in FILES: alltx.extend(rows(p))
    grouped=collections.defaultdict(list)
    for tx in alltx:
        r=ref(tx)
        if r: grouped[r].append(tx)

    variants=[]; comparable=0; identical=0; excluded_lacuna=0
    overlaps=0
    by_pair=collections.Counter()
    for (book,ch,v),txs in sorted(grouped.items()):
        # one transcription per manuscript per passage
        unique={}
        for tx in txs: unique.setdefault(tx["manuscript_id"],tx)
        if len(unique)<2: continue
        overlaps+=1
        usable=[]
        for tx in unique.values():
            if incomplete(tx):
                excluded_lacuna+=1
                continue
            usable.append(tx)
        if len(usable)<2: continue
        comparable+=1
        reading_groups=collections.defaultdict(list)
        for tx in usable:
            reading_groups[norm(tx["text"])].append(tx)
        if len(reading_groups)<2:
            identical+=1
            continue

        passage=f"{book.lower()}:{ch}:{v}"
        readings=[]
        for n,(key,members) in enumerate(sorted(reading_groups.items(),key=lambda kv:kv[0]),1):
            witnesses=sorted(x["manuscript_id"] for x in members)
            readings.append({
                "id":f"reading:variant:{passage}:{n}",
                "text":members[0]["text"],
                "witnesses":witnesses,
                "note":"Diplomatic text from preserved transcription; witnesses grouped by conservative normalized equality."
            })
        for a in range(len(readings)):
            for b in range(a+1,len(readings)):
                for wa in readings[a]["witnesses"]:
                    for wb in readings[b]["witnesses"]:
                        by_pair["|".join(sorted((wa,wb)))]+=1
        variants.append({
            "id":f"variant:{passage}:verse-comparison",
            "book":book,"chapter":ch,"verse":v,
            "source_id":"src:el-relato:transcription-comparison",
            "location_note":"Verse-level comparison derived from preserved diplomatic transcriptions; not an exhaustive segment-level apparatus.",
            "readings":readings
        })

    out=OUT/"manuscript-verse-variants.jsonl"
    with out.open("w",encoding="utf-8",newline="\n") as f:
        for x in variants: f.write(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n")
    report={
      "transcription_units_loaded":len(alltx),
      "passages_with_two_or_more_witnesses":overlaps,
      "comparable_passages_after_lacuna_filter":comparable,
      "identical_comparable_passages":identical,
      "variant_units":len(variants),
      "transcription_units_excluded_for_lacuna_in_overlap":excluded_lacuna,
      "variant_pairs":dict(by_pair.most_common()),
      "granularity":"verse-level",
      "exhaustive":False
    }
    (DER/"manuscript-verse-variant-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
