#!/usr/bin/env python3
from __future__ import annotations
import json,re,xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"sources/manuscripts/Sinaiticus/transcription/raw/sinaiticus_full_v195.xml"
OUT_XML=ROOT/"sources/manuscripts/Sinaiticus/transcription/derived/gospels"
OUT_JSONL=ROOT/"data/normalized/transcriptions/sinaiticus-gospels.jsonl"
REPORT=ROOT/"data/derived/manuscripts/Sinaiticus-gospel-transcription-report.json"
XML_ID="{http://www.w3.org/XML/1998/namespace}id"

BOOKS={
 "MATT":"Matthew",
 "MARK":"Mark",
 "LUKE":"Luke",
 "JOHN":"John",
}
ID_RE=re.compile(r"B-B\d+-\d+-(MATT|MARK|LUKE|JOHN)$",re.I)
VERSE_ID_RE=re.compile(r"K(\d+)V(\d+)",re.I)

def local(tag): return tag.rsplit("}",1)[-1]

def flatten_words(node):
    words=[]
    for el in node.iter():
        if local(el.tag)=="w":
            txt="".join(el.itertext())
            txt=" ".join(txt.split())
            if txt: words.append(txt)
    return " ".join(words)

def recurse(node,book,chapter,rows,problems):
    tag=local(node.tag)
    ch=chapter
    if tag=="div" and node.attrib.get("type")=="chapter":
        raw=node.attrib.get("n") or node.attrib.get("chapter") or ""
        m=re.search(r"\d+",raw)
        if m: ch=int(m.group())
    if tag=="ab":
        ident=node.attrib.get("id") or node.attrib.get(XML_ID) or ""
        verse_raw=node.attrib.get("n") or node.attrib.get("verse") or ""
        chapter_num=ch
        verse_num=None
        m=VERSE_ID_RE.search(ident)
        if m:
            chapter_num=int(m.group(1)); verse_num=int(m.group(2))
        else:
            m2=re.search(r"\d+",verse_raw)
            if m2: verse_num=int(m2.group())
        if chapter_num and verse_num:
            slug=book.lower()
            text=flatten_words(node)
            rows.append({
                "id":f"tx:sinaiticus:{slug}:{chapter_num}:{verse_num}",
                "manuscript_id":"ms:ga:01",
                "source_id":"src:sinaiticus:itsee-v195",
                "image_id":None,
                "passage_ids":[f"passage:{slug}:{chapter_num}:{verse_num}"],
                "layer":"diplomatic",
                "format":"plain",
                "text":text,
                "local_path":f"sources/manuscripts/Sinaiticus/transcription/derived/gospels/{book}.xml",
                "notes":f"Derived from XML ab {ident}" if ident else "Derived from ITSEE v1.95 XML"
            })
        else:
            problems.append({"book":book,"id":ident,"n":verse_raw})
    for child in list(node):
        recurse(child,book,ch,rows,problems)

def main():
    tree=ET.parse(SRC)
    root=tree.getroot()
    OUT_XML.mkdir(parents=True,exist_ok=True)
    OUT_JSONL.parent.mkdir(parents=True,exist_ok=True)
    REPORT.parent.mkdir(parents=True,exist_ok=True)

    rows=[]; problems=[]; found={}
    for div in root.iter():
        if local(div.tag)!="div" or div.attrib.get("type")!="book": continue
        ident=div.attrib.get(XML_ID) or div.attrib.get("id") or ""
        m=ID_RE.search(ident)
        if not m: continue
        book=BOOKS[m.group(1).upper()]
        found[book]=ident
        xml_bytes=ET.tostring(div,encoding="utf-8",xml_declaration=True)
        (OUT_XML/f"{book}.xml").write_bytes(xml_bytes)
        recurse(div,book,None,rows,problems)

    rows.sort(key=lambda x:(["Matthew","Mark","Luke","John"].index(x["passage_ids"][0].split(":")[1].capitalize()) if False else 0,x["id"]))
    # Stable uniqueness and meaningful coverage.
    ids=[x["id"] for x in rows]
    duplicates=len(ids)-len(set(ids))
    if duplicates:
        raise RuntimeError(f"Duplicate normalized transcription IDs: {duplicates}")
    if set(found)!={"Matthew","Mark","Luke","John"}:
        raise RuntimeError(f"Missing Gospel book divs: found {sorted(found)}")
    if len(rows)<3700:
        raise RuntimeError(f"Suspicious Gospel verse count: {len(rows)}")

    with OUT_JSONL.open("w",encoding="utf-8",newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")

    by_book={}
    for row in rows:
        book=row["id"].split(":")[2].capitalize()
        by_book[book]=by_book.get(book,0)+1
    report={
        "source_version":"1.95",
        "book_div_ids":found,
        "normalized_units":len(rows),
        "units_by_book":by_book,
        "unmapped_ab_units":len(problems),
        "unmapped_samples":problems[:100],
    }
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
