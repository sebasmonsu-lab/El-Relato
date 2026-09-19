#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML_DIR = ROOT / "vendor/SBLGNT/data/sblgnt/xml"
OUT = ROOT / "data/normalized"
SBL_OUT = OUT / "sblgnt"
DERIVED = ROOT / "data/derived/sblgnt"
SBL_OUT.mkdir(parents=True, exist_ok=True)
DERIVED.mkdir(parents=True, exist_ok=True)

BOOK_FILES = {
    "Matthew": "Matt.xml",
    "Mark": "Mark.xml",
    "Luke": "Luke.xml",
    "John": "John.xml",
}
BOOK_SLUG = {k: k.lower() for k in BOOK_FILES}
EDITION_ID = "edition:sblgnt:2010"
SOURCE_ID = "src:sblgnt:faithlife"


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def parse_ref(ref):
    m = re.fullmatch(r"(Matthew|Mark|Luke|John) (\d+):(\d+)", ref)
    if not m:
        raise ValueError(f"Unexpected SBLGNT verse id: {ref!r}")
    return m.group(1), int(m.group(2)), int(m.group(3))


def main():
    passages = []
    edition_verses = []
    tokens = []
    per_book_tokens = Counter()
    per_book_verses = Counter()

    for expected_book, filename in BOOK_FILES.items():
        root = ET.parse(XML_DIR / filename).getroot()
        current = None
        current_tokens = []
        last_token = None
        pending_prefix = ""
        double_bracket = False

        def flush():
            nonlocal current, current_tokens, last_token, pending_prefix
            if current is None:
                return
            book, chapter, verse = current
            slug = BOOK_SLUG[book]
            passage_id = f"passage:{slug}:{chapter}:{verse}"
            visible = " ".join(
                ((t["prefix_before"] or "").lstrip()) +
                t["surface"] +
                ((t["punctuation_after"] or "").rstrip())
                for t in current_tokens
            )
            passages.append({
                "id": passage_id,
                "book": book,
                "chapter": chapter,
                "verse_start": verse,
                "verse_end": verse,
                "osis_ref": f"{book}.{chapter}.{verse}",
                "notes": None,
            })
            edition_verses.append({
                "id": f"edition-verse:sblgnt:{slug}:{chapter}:{verse}",
                "edition_id": EDITION_ID,
                "passage_id": passage_id,
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "text": visible,
                "token_count": len(current_tokens),
                "source_ref": SOURCE_ID,
            })
            per_book_verses[book] += 1
            current = None
            current_tokens = []
            last_token = None

        for elem in root.iter():
            if elem.tag == "verse-number":
                flush()
                current = parse_ref(elem.attrib["id"])
                if current[0] != expected_book:
                    raise RuntimeError(f"Book mismatch in {filename}: {current}")
            elif elem.tag == "w" and current is not None:
                book, chapter, verse = current
                slug = BOOK_SLUG[book]
                pos = len(current_tokens) + 1
                status = "double-bracketed" if (double_bracket or "⟦" in pending_prefix) else "main"
                token = {
                    "id": f"token:sblgnt:{slug}:{chapter}:{verse}:{pos}",
                    "edition_id": EDITION_ID,
                    "book": book,
                    "chapter": chapter,
                    "verse": verse,
                    "position": pos,
                    "surface": elem.text or "",
                    "normalized": None,
                    "lemma_id": None,
                    "lemma": None,
                    "transliteration": None,
                    "strong_id": None,
                    "morphology_code": None,
                    "punctuation_after": None,
                    "prefix_before": pending_prefix or None,
                    "textual_status": status,
                    "source_ref": SOURCE_ID,
                }
                current_tokens.append(token)
                tokens.append(token)
                per_book_tokens[book] += 1
                last_token = token
                if "⟦" in pending_prefix:
                    double_bracket = True
                pending_prefix = ""
            elif elem.tag == "prefix" and current is not None:
                pending_prefix += elem.text or ""
            elif elem.tag == "suffix" and current is not None and last_token is not None:
                last_token["punctuation_after"] = elem.text or None
                if "⟧" in (elem.text or ""):
                    double_bracket = False

        flush()

    # Defensive uniqueness / coverage checks.
    for name, rows in [("passages", passages), ("edition verses", edition_verses), ("tokens", tokens)]:
        ids = [x["id"] for x in rows]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"Duplicate IDs in {name}")

    if len(passages) < 3000:
        raise RuntimeError(f"Suspicious Gospel verse count: {len(passages)}")
    if len(tokens) < 50000:
        raise RuntimeError(f"Suspicious Gospel token count: {len(tokens)}")

    editions = [{
        "id": EDITION_ID,
        "title": "SBL Greek New Testament",
        "version": "2010",
        "source_id": SOURCE_ID,
        "language": "grc",
        "local_path": "vendor/SBLGNT/data/sblgnt",
        "notes": "Base Gospel text parsed directly from preserved SBLGNT XML <w>/<suffix> structure.",
    }]

    write_jsonl(OUT / "editions.jsonl", editions)
    write_jsonl(OUT / "passages.jsonl", passages)
    write_jsonl(SBL_OUT / "edition-verses.jsonl", edition_verses)
    write_jsonl(SBL_OUT / "tokens.jsonl", tokens)

    stats = {
        "edition": EDITION_ID,
        "verses": len(passages),
        "tokens": len(tokens),
        "verses_by_book": dict(per_book_verses),
        "tokens_by_book": dict(per_book_tokens),
    }
    (DERIVED / "parse-stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
