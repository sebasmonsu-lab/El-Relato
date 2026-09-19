#!/usr/bin/env python3
from __future__ import annotations
import json, xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"sources/manuscripts/Sinaiticus/transcription/raw/sinaiticus_full_v195.xml"
OUT=ROOT/"data/derived/manuscripts/Sinaiticus-transcription-inventory.json"

def local(tag):
    return tag.rsplit("}",1)[-1]

books=[]
pages=0
verses=0
words=0
current_book=None
book_counts={}

for event,elem in ET.iterparse(SRC,events=("start","end")):
    tag=local(elem.tag)
    if event=="start":
        if tag=="div" and elem.attrib.get("type")=="book":
            current_book={
                "attributes":dict(elem.attrib),
                "title":None,
                "verses":0,
                "words":0,
                "pages":0,
            }
            books.append(current_book)
        elif tag=="pb":
            pages+=1
            if current_book is not None: current_book["pages"]+=1
        elif tag=="ab":
            ident=elem.attrib.get("id") or elem.attrib.get("{http://www.w3.org/XML/1998/namespace}id") or ""
            if ident.startswith("V-"):
                verses+=1
                if current_book is not None: current_book["verses"]+=1
        elif tag=="w":
            words+=1
            if current_book is not None: current_book["words"]+=1
    else:
        if current_book is not None and current_book["title"] is None and tag in {"head","title"}:
            txt=" ".join("".join(elem.itertext()).split())
            if txt: current_book["title"]=txt
        if tag=="div" and elem.attrib.get("type")=="book":
            current_book=None
        elem.clear()

summary={
    "source":"sinaiticus_full_v195.xml",
    "books":books,
    "totals":{"books":len(books),"pages":pages,"verses":verses,"words":words},
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"totals":summary["totals"],"books":[{"attributes":b["attributes"],"title":b["title"],"verses":b["verses"],"words":b["words"],"pages":b["pages"]} for b in books]},ensure_ascii=False,indent=2))
