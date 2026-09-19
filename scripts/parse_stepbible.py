#!/usr/bin/env python3
from __future__ import annotations

import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TBESG = ROOT / "vendor/STEPBible-Data/Lexicons/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt"
TAGNT = ROOT / "vendor/STEPBible-Data/Older Formats/TAGNT Mat-Jhn - Translators Amalgamated Greek NT - STEPBible.org CC-BY.txt"
TEGMC = ROOT / "vendor/STEPBible-Data/Morphology codes/TEGMC - Translators Expansion of Greek Morphhology Codes - STEPBible.org CC BY.txt"

OUT = ROOT / "data/normalized/stepbible"
DERIVED = ROOT / "data/derived/stepbible"
OUT.mkdir(parents=True, exist_ok=True)
DERIVED.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def norm_nullable(value: str):
    value = value.strip()
    return value if value else None


def parse_tbesg():
    rows = []
    started = False
    ordinal = 0
    strong_re = re.compile(r"^G\d{4,5}$")
    dstrong_re = re.compile(r"\b(G\d{4,5}[A-Z]?)\b")

    for raw in TBESG.read_text(encoding="utf-8-sig").splitlines():
        if raw.startswith("eStrong\tdStrong\tuStrong\tGreek\t"):
            started = True
            continue
        if not started:
            continue
        if not raw or raw.startswith("="):
            continue

        parts = raw.split("\t")
        if not parts or not strong_re.fullmatch(parts[0].strip()):
            continue

        while len(parts) < 8:
            parts.append("")
        ordinal += 1
        e_strong, d_raw, u_strong, greek, translit, morph, gloss = [x.strip() for x in parts[:7]]
        meaning = "\t".join(parts[7:]).rstrip("\t").strip()
        d_match = dstrong_re.search(d_raw)

        rows.append({
            "id": f"strong-entry:{e_strong}:{ordinal:05d}",
            "source_id": "src:stepbible:tbesg",
            "e_strong": e_strong,
            "d_strong_raw": d_raw or None,
            "d_strong_id": d_match.group(1) if d_match else None,
            "u_strong": u_strong or None,
            "greek": greek,
            "transliteration": translit or None,
            "lexical_morphology": morph or None,
            "gloss": gloss,
            "meaning_html": meaning or None,
            "row_ordinal": ordinal,
        })
    return rows


TAGNT_REF = re.compile(
    r"^(?P<prefix>\d+)_(?P<book>Mat|Mrk|Luk|Jhn)\.(?P<chapter>\d{3})\.(?P<verse>\d{3})(?P<suffix>[^\t]*)$"
)
BOOKS = {"Mat": "Matthew", "Mrk": "Mark", "Luk": "Luke", "Jhn": "John"}


def parse_tagnt():
    rows = []
    positions = collections.Counter()
    per_book = collections.Counter()
    sbl_per_book = collections.Counter()

    for raw in TAGNT.read_text(encoding="utf-8-sig").splitlines():
        if not raw or raw.startswith("#") or raw.startswith("="):
            continue
        parts = raw.split("\t")
        if not parts:
            continue
        m = TAGNT_REF.match(parts[0].strip())
        if not m:
            continue

        while len(parts) < 15:
            parts.append("")
        reference = parts[0].strip()
        book = BOOKS[m.group("book")]
        chapter = int(m.group("chapter"))
        verse = int(m.group("verse"))
        key = (book, chapter, verse)
        positions[key] += 1
        pos = positions[key]
        per_book[book] += 1

        editions = parts[8].strip()
        if re.search(r"(^|[+ ;])SBL($|[+ ;])", editions):
            sbl_per_book[book] += 1

        rows.append({
            "id": f"tagnt:{book.lower()}:{chapter}:{verse}:{pos}",
            "source_id": "src:stepbible:tagnt-mat-jhn",
            "reference": reference,
            "book": book,
            "chapter": chapter,
            "verse": verse,
            "row_position": pos,
            "word_type": norm_nullable(parts[1]),
            "greek": parts[2].strip(),
            "english_translation": norm_nullable(parts[3]),
            "strongs": parts[4].strip(),
            "grammar": norm_nullable(parts[5]),
            "dictionary_form": norm_nullable(parts[6]),
            "gloss": norm_nullable(parts[7]),
            "editions": editions,
            "spelling_variants": norm_nullable(parts[9]),
            "meaning_variants": norm_nullable(parts[10]),
            "spanish_translation": norm_nullable(parts[11]),
            "sub_meaning": norm_nullable(parts[12]),
            "super_meaning": norm_nullable(parts[13]),
            "conjoin_word": norm_nullable(parts[14]),
            "extra_columns": [x for x in parts[15:] if x],
        })

    return rows, dict(per_book), dict(sbl_per_book)


def parse_tegmc():
    text = TEGMC.read_text(encoding="utf-8-sig")
    marker = "FULL MORPHOLOGY CODES:"
    if marker not in text:
        raise RuntimeError("Could not locate FULL MORPHOLOGY CODES section in TEGMC")
    body = text.split(marker, 1)[1]
    lines = body.splitlines()

    rows = []
    i = 0
    while i < len(lines):
        if lines[i].strip() != "$":
            i += 1
            continue
        block = []
        i += 1
        while i < len(lines) and lines[i].strip() != "$":
            if lines[i].strip():
                block.append(lines[i])
            i += 1
        if not block:
            continue

        first = block[0].split("\t", 1)
        code = first[0].strip()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9-]*", code):
            continue
        expansion = first[1].strip() if len(first) > 1 else ""
        values = {}
        for item in expansion.split(";"):
            if "=" in item:
                k, v = item.split("=", 1)
                values[k.strip().lower()] = v.strip()

        part = values.get("function")
        if not part:
            continue
        extra = values.get("extra", "")
        degree = extra if extra.lower() in {"comparative", "superlative"} else None

        rows.append({
            "code": code,
            "source_id": "src:stepbible:tegmc",
            "part_of_speech": part,
            "person": values.get("person"),
            "tense": values.get("tense"),
            "voice": values.get("voice"),
            "mood": values.get("mood"),
            "case": values.get("case"),
            "number": values.get("number"),
            "gender": values.get("gender"),
            "degree": degree,
            "raw_expansion": " | ".join(block[:4]),
        })
    return rows


def main():
    strong = parse_tbesg()
    tagnt, tagnt_by_book, sbl_by_book = parse_tagnt()
    morphology = parse_tegmc()

    if len(strong) < 5000:
        raise RuntimeError(f"Suspicious TBESG parse: only {len(strong)} rows")
    if len(tagnt) < 100000:
        raise RuntimeError(f"Suspicious TAGNT parse: only {len(tagnt)} rows")
    if len(morphology) < 500:
        raise RuntimeError(f"Suspicious TEGMC parse: only {len(morphology)} codes")

    write_jsonl(OUT / "strong-entries.jsonl", strong)
    write_jsonl(OUT / "tagnt-rows.jsonl", tagnt)
    write_jsonl(OUT / "morphology.jsonl", morphology)

    stats = {
        "TBESG": {
            "entries": len(strong),
            "unique_eStrong": len({x["e_strong"] for x in strong}),
            "with_dStrong": sum(x["d_strong_id"] is not None for x in strong),
        },
        "TAGNT": {
            "rows": len(tagnt),
            "rows_by_book": tagnt_by_book,
            "rows_marked_SBL_by_book": sbl_by_book,
            "unique_references": len({(x["book"], x["chapter"], x["verse"]) for x in tagnt}),
        },
        "TEGMC": {
            "full_morphology_codes": len(morphology),
            "unique_codes": len({x["code"] for x in morphology}),
        },
    }
    (DERIVED / "parse-stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
