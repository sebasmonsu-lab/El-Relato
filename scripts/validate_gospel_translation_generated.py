#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data/normalized/sblgnt/chapters"
TARGETS = {
    "es-419": ROOT / "sources/gospel-editions/es-419-v1/generated",
    "en": ROOT / "sources/gospel-editions/en-v1/generated",
    "pt-BR": ROOT / "sources/gospel-editions/pt-br-v1/generated",
}
BASE = "edition:gospels:grc-sblgnt-2010:v1"
CANON = ["Matthew", "Mark", "Luke", "John"]


def load_jsonl(path: Path):
    out = []
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{n}: invalid JSON: {e}")
            out.append(row)
    return out


def source_chapters():
    out = {}
    for path in sorted(SOURCE_DIR.glob("*.jsonl")):
        if path.name == "manifest.json":
            continue
        rows = load_jsonl(path)
        if not rows:
            continue
        book = rows[0]["book"]
        chapter = int(rows[0]["chapter"])
        keys = {(r["book"], int(r["chapter"]), int(r["verse"])) for r in rows}
        if len(keys) != len(rows):
            raise SystemExit(f"Duplicate SOURCE key in {path}")
        out[(book, chapter)] = (path, keys)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--locale", choices=TARGETS, required=True)
    ap.add_argument("--book", choices=CANON)
    ap.add_argument("--require-book-complete", action="store_true")
    ap.add_argument("--require-complete", action="store_true")
    args = ap.parse_args()

    source = source_chapters()
    target_dir = TARGETS[args.locale]
    files = sorted(target_dir.glob("*.jsonl")) if target_dir.exists() else []

    seen_keys = set()
    seen_ids = set()
    translated_by_chapter = {}
    errors = []

    for path in files:
        rows = load_jsonl(path)
        if not rows:
            errors.append(f"{path}: empty chapter")
            continue
        book = rows[0].get("book")
        chapter = int(rows[0].get("chapter"))
        ck = (book, chapter)
        if ck not in source:
            errors.append(f"{path}: unknown SOURCE chapter {ck}")
            continue

        keys = []
        for row in rows:
            key = (row.get("book"), int(row.get("chapter")), int(row.get("verse")))
            keys.append(key)
            if key in seen_keys:
                errors.append(f"duplicate translated key: {key}")
            seen_keys.add(key)

            rid = str(row.get("id") or "")
            if not rid:
                errors.append(f"{path}: missing id for {key}")
            elif rid in seen_ids:
                errors.append(f"duplicate translation id: {rid}")
            seen_ids.add(rid)

            if not str(row.get("text") or "").strip():
                errors.append(f"{path}: empty text for {key}")
            if row.get("base_edition_id") != BASE:
                errors.append(f"{path}: wrong base_edition_id for {key}")
            if not str(row.get("model") or "").strip():
                errors.append(f"{path}: missing model provenance for {key}")

        keyset = set(keys)
        src_keys = source[ck][1]
        missing = sorted(src_keys - keyset)
        extra = sorted(keyset - src_keys)
        if missing or extra:
            errors.append(
                f"{path}: verse-set mismatch missing={missing[:8]} extra={extra[:8]}"
            )
        translated_by_chapter[ck] = len(keyset)

    selected_source = {
        ck: data for ck, data in source.items()
        if args.book is None or ck[0] == args.book
    }
    selected_translated = {
        ck: n for ck, n in translated_by_chapter.items()
        if args.book is None or ck[0] == args.book
    }

    if args.require_book_complete and args.book:
        missing_chapters = sorted(set(selected_source) - set(selected_translated))
        if missing_chapters:
            errors.append(f"missing translated chapters for {args.book}: {missing_chapters}")

    if args.require_complete:
        missing_chapters = sorted(set(source) - set(translated_by_chapter))
        if missing_chapters:
            errors.append(f"missing translated chapters: {missing_chapters}")

    src_verses = sum(len(data[1]) for data in selected_source.values())
    translated_verses = sum(selected_translated.values())
    by_book = Counter()
    chapters_by_book = defaultdict(int)
    for (book, chapter), n in translated_by_chapter.items():
        by_book[book] += n
        chapters_by_book[book] += 1

    report = {
        "status": "PASS" if not errors else "FAIL",
        "locale": args.locale,
        "book_filter": args.book,
        "translated_chapters": len(selected_translated),
        "source_chapters": len(selected_source),
        "translated_verses": translated_verses,
        "source_verses": src_verses,
        "coverage": round(translated_verses / src_verses, 6) if src_verses else 0,
        "all_generated_by_book": {
            b: {"chapters": chapters_by_book[b], "verses": by_book[b]} for b in CANON
        },
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
