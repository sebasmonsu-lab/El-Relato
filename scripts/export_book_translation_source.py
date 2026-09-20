#!/usr/bin/env python3
import json, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/"book/el-relato-book.sqlite"
OUT=ROOT/"book/translations/_source-export"
BASE="edition:el-relato:grc-sblgnt-2010:v1"
OUT.mkdir(parents=True,exist_ok=True)
c=sqlite3.connect(f"file:{DB.as_posix()}?mode=ro",uri=True)
c.row_factory=sqlite3.Row
for scene in range(57,121):
    rows=list(c.execute("""
      SELECT u.unit_id,u.scene_number,u.scene_order,u.global_order,u.reference_raw,ut.text
      FROM units u JOIN unit_texts ut ON ut.unit_id=u.unit_id
      WHERE ut.edition_id=? AND u.scene_number=?
      ORDER BY u.scene_order
    """,(BASE,scene)))
    p=OUT/f"scene-{scene:03d}.jsonl"
    with p.open("w",encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(dict(r),ensure_ascii=False,separators=(",",":"))+"\n")
print(json.dumps({"scenes":64,"first":57,"last":120}))
