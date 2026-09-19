#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "vendor/StrongGreekOriginal/strongsgreek.xml"
OUT = ROOT / "data/normalized/strong-original"
DERIVED = ROOT / "data/derived/strong-original"
OUT.mkdir(parents=True, exist_ok=True)
DERIVED.mkdir(parents=True, exist_ok=True)

SPACE = re.compile(r"\s+")


def sref_id(node):
    prefix = "G" if node.attrib["language"] == "GREEK" else "H"
    return prefix + f"{int(node.attrib['strongs']):04d}"


def flatten(node):
    parts = []
    if node.text:
        parts.append(node.text)
    for child in node:
        if child.tag == "strongsref":
            parts.append(sref_id(child))
        elif child.tag == "greek":
            parts.append(child.attrib.get("unicode", ""))
        elif child.tag == "pronunciation":
            parts.append(child.attrib.get("strongs", ""))
        else:
            parts.append(flatten(child))
        if child.tail:
            parts.append(child.tail)
    return SPACE.sub(" ", "".join(parts)).strip()


def main():
    root = ET.parse(SRC).getroot()
    rows = []

    for entry in root.findall("./entries/entry"):
        number = int(entry.attrib["strongs"])
        greek = entry.find("./greek")
        if greek is None:
            continue
        strong_id = f"G{number:04d}"
        pronunciation = entry.find("./pronunciation")
        derivation = entry.find("./strongs_derivation")
        definition = entry.find("./strongs_def")
        kjv = entry.find("./kjv_def")

        refs = []
        seen = set()
        for ref in entry.findall(".//strongsref"):
            key = (ref.attrib["language"], sref_id(ref))
            if key not in seen:
                seen.add(key)
                refs.append({"language": key[0], "strong_id": key[1]})

        rows.append({
            "id": f"strong-original:{strong_id}",
            "source_id": "src:morphgnt:strongs-greek-xml",
            "strong_id": strong_id,
            "number": number,
            "lemma": greek.attrib.get("unicode", ""),
            "beta_code": greek.attrib.get("BETA"),
            "transliteration": greek.attrib.get("translit", ""),
            "pronunciation": pronunciation.attrib.get("strongs") if pronunciation is not None else None,
            "derivation": flatten(derivation) if derivation is not None else None,
            "strongs_definition": flatten(definition) if definition is not None else "",
            "kjv_definition": flatten(kjv) if kjv is not None else None,
            "cross_references": refs,
        })

    if len(rows) < 5400:
        raise RuntimeError(f"Suspicious Strong Greek entry count: {len(rows)}")
    ids = [x["id"] for x in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate Strong original IDs")

    out = OUT / "strong-original-entries.jsonl"
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    stats = {
        "entries": len(rows),
        "min_number": min(x["number"] for x in rows),
        "max_number": max(x["number"] for x in rows),
        "cross_references": sum(len(x["cross_references"]) for x in rows),
    }
    (DERIVED / "parse-stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
