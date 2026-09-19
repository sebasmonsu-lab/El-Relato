#!/usr/bin/env python3
from __future__ import annotations

import collections
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "vendor/SBLGNT/data/sblgntapp/xml"
OUT = ROOT / "data/normalized/apparatus"
DERIVED = ROOT / "data/derived/apparatus"
OUT.mkdir(parents=True, exist_ok=True)
DERIVED.mkdir(parents=True, exist_ok=True)

FILES = {
    "Matthew": "Matt.xml",
    "Mark": "Mark.xml",
    "Luke": "Luke.xml",
    "John": "John.xml",
}

KNOWN_SIGLA = {
    "WH","WHmarg","Treg","NA28","RP","NIV","Holmes","TR","Greeven","SBL","SBLGNT",
}
LOCATION_RE = re.compile(r"^(?:•\s*)?(?P<loc>(?:\d+:)?\d+(?:[–-]\d+)?)\s+(?P<rest>.*)$")
SIGLUM_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")


def parse_segment(segment: str):
    raw = segment.strip()
    tokens = raw.split()
    sigla = []
    while tokens:
        token = tokens[-1].strip(" ,.")
        if token in KNOWN_SIGLA:
            sigla.append(token)
            tokens.pop()
        else:
            break
    sigla.reverse()
    return {
        "raw_segment": raw,
        "text": " ".join(tokens).strip(),
        "edition_sigla": sigla,
    }


def main():
    rows = []
    unknown_tail_tokens = collections.Counter()
    sigla_counts = collections.Counter()
    by_book = collections.Counter()
    parse_status = collections.Counter()

    for book, filename in FILES.items():
        root = ET.parse(APP_DIR / filename).getroot()
        current_chapter = current_verse = None
        ordinal = 0

        for elem in root:
            if elem.tag == "verse":
                ref = (elem.text or "").strip()
                m = re.fullmatch(rf"{book} (\d+):(\d+)", ref)
                if not m:
                    raise RuntimeError(f"Unexpected apparatus verse ref: {ref!r}")
                current_chapter = int(m.group(1))
                current_verse = int(m.group(2))
                ordinal = 0
                continue
            if elem.tag != "note":
                continue
            if current_chapter is None:
                raise RuntimeError(f"Apparatus note before verse in {filename}")

            ordinal += 1
            raw = " ".join((elem.text or "").replace("\u00a0"," ").split())
            loc = None
            body = raw.lstrip("• ").strip()
            m = LOCATION_RE.match(raw)
            if m:
                loc = m.group("loc")
                body = m.group("rest").strip()

            # Primary apparatus separator. Additional right-hand readings
            # are commonly separated with ASCII semicolons.
            if "]" in body:
                left, right = body.split("]", 1)
                segments = [left.strip()] + [x.strip() for x in right.split(";") if x.strip()]
                status = "parsed"
            else:
                segments = [body]
                status = "raw-only"

            readings = [parse_segment(x) for x in segments if x]
            if not readings:
                readings = [{"raw_segment": body, "text": body, "edition_sigla": []}]
                status = "raw-only"

            for rd in readings:
                for sig in rd["edition_sigla"]:
                    sigla_counts[sig] += 1
                # Track likely edition-like tail tokens that our known list missed.
                tail = rd["raw_segment"].split()[-1].strip(" ,.;") if rd["raw_segment"].split() else ""
                if tail and SIGLUM_RE.fullmatch(tail) and not rd["edition_sigla"]:
                    unknown_tail_tokens[tail] += 1
                    if status == "parsed":
                        status = "partial"

            parse_status[status] += 1
            by_book[book] += 1
            rows.append({
                "id": f"edition-apparatus:sblgnt:{book.lower()}:{current_chapter}:{current_verse}:{ordinal}",
                "source_id": "src:sblgnt:faithlife",
                "book": book,
                "chapter": current_chapter,
                "verse": current_verse,
                "ordinal": ordinal,
                "location_label": loc,
                "raw_note": raw,
                "readings": readings,
                "parse_status": status,
            })

    if len(rows) < 500:
        raise RuntimeError(f"Suspiciously small SBLGNT apparatus: {len(rows)} notes")

    with (OUT / "edition-apparatus-units.jsonl").open("w",encoding="utf-8",newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")

    report={
        "units":len(rows),
        "units_by_book":dict(by_book),
        "parse_status":dict(parse_status),
        "edition_sigla_counts":dict(sigla_counts.most_common()),
        "unknown_tail_tokens":dict(unknown_tail_tokens.most_common(50)),
    }
    (DERIVED/"sblgnt-apparatus-report.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
