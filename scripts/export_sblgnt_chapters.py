#!/usr/bin/env python3
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/normalized/sblgnt/edition-verses.jsonl"
OUT=ROOT/"data/normalized/sblgnt/chapters"
groups=defaultdict(list)
for line in SRC.read_text(encoding="utf-8").splitlines():
    if not line.strip(): continue
    row=json.loads(line)
    book=row.get("book") or row.get("book_name")
    chapter=int(row["chapter"])
    if book not in {"Matthew","Mark","Luke","John"}: continue
    groups[(book,chapter)].append(row)
OUT.mkdir(parents=True,exist_ok=True)
for (book,chapter),rows in sorted(groups.items()):
    slug=book.lower()
    path=OUT/f"{slug}-{chapter:02d}.jsonl"
    path.write_text("\n".join(json.dumps(r,ensure_ascii=False,separators=(",",":")) for r in rows)+"\n",encoding="utf-8")
manifest={"source":"data/normalized/sblgnt/edition-verses.jsonl","chapters":len(groups),"verses":sum(map(len,groups.values())),"files":[f"{b.lower()}-{c:02d}.jsonl" for b,c in sorted(groups)]}
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert manifest["chapters"]==89, manifest
assert manifest["verses"]==3768, manifest
print(json.dumps(manifest))
