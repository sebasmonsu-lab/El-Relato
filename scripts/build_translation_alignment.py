#!/usr/bin/env python3
"""Build a derived translation-to-Greek alignment layer.

The canonical BOOK SQLite is opened read-only. The output is a build artifact
for the web layer and never mutates BOOK.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOOK_DB = ROOT / "book/el-relato-book.sqlite"
DEFAULT_QUERY_DB = ROOT / "build/el-relato.sqlite"
GREEK_LANGS = {"grc", "el", "gr"}
WORD_RE = re.compile(r"[^\W\d_]+(?:[’'ʼ-][^\W\d_]+)*|\d+(?:[.,]\d+)*", re.UNICODE)


def connect_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def lexical_tokens(text: str) -> list[dict]:
    return [
        {"index": i, "surface": m.group(0), "start": m.start(), "end": m.end()}
        for i, m in enumerate(WORD_RE.finditer(text or ""))
    ]


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book-db", default=str(DEFAULT_BOOK_DB))
    ap.add_argument("--query-db", default=str(DEFAULT_QUERY_DB))
    ap.add_argument("--output", default="build/translation-alignments.jsonl")
    ap.add_argument("--summary", default="build/translation-alignments-summary.json")
    args = ap.parse_args()

    book_db = Path(args.book_db)
    query_db = Path(args.query_db)
    out = ROOT / args.output if not Path(args.output).is_absolute() else Path(args.output)
    summary_path = ROOT / args.summary if not Path(args.summary).is_absolute() else Path(args.summary)

    if not book_db.exists():
        raise SystemExit(f"Missing BOOK DB: {book_db}")
    if not query_db.exists():
        raise SystemExit(f"Missing SOURCE query DB: {query_db}")

    book = connect_ro(book_db)
    source = connect_ro(query_db)
    try:
        hidden_statuses = {"generated-partial", "superseded", "archived"}
        editions = {
            r["edition_id"]: dict(r)
            for r in book.execute("SELECT * FROM editions ORDER BY created_at, edition_id")
            if (r["language_code"] or "").lower() not in GREEK_LANGS
            and (r["status"] or "").lower() not in hidden_statuses
        }
        rows = [
            dict(r)
            for r in book.execute(
                """
                SELECT ut.edition_id, ut.unit_id, ut.text, ut.source_witness_id,
                       u.scene_number, u.global_order
                FROM unit_texts ut
                JOIN units u ON u.unit_id=ut.unit_id
                WHERE ut.text IS NOT NULL AND trim(ut.text)<>''
                ORDER BY u.global_order, ut.edition_id
                """
            )
            if r["edition_id"] in editions
        ]
        witnesses = {
            r["witness_id"]: dict(r)
            for r in book.execute("SELECT * FROM unit_witnesses")
        }
        first_witness = {}
        for r in book.execute("SELECT * FROM unit_witnesses ORDER BY unit_id,witness_order"):
            first_witness.setdefault(r["unit_id"], dict(r))

        source_tokens = {
            r["token_id"]: dict(r)
            for r in source.execute("SELECT * FROM tokens")
        }

        if not rows:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("", encoding="utf-8")
            summary = {
                "status": "PASS",
                "editions": [],
                "units": 0,
                "target_tokens": 0,
                "aligned_target_tokens": 0,
                "traceable_target_tokens": 0,
                "direct_alignment_coverage": 0.0,
                "traceability_coverage": 0.0,
                "coverage": 0.0,
            }
            summary_path.write_text(
                json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return

        try:
            from simalign import SentenceAligner
        except Exception as exc:
            raise SystemExit("SimAlign is required only when translated BOOK editions exist: pip install simalign==0.4") from exc

        # m = maximum-weight matching, a = argmax intersection, i = itermax.
        # The union improves recall while each relation records the method(s) supporting it.
        aligner = SentenceAligner(model="bert", token_type="bpe", matching_methods="mai")
        output_rows = []
        stats = {
            "status": "PASS",
            "engine": "simalign-0.4",
            "model": "bert-base-multilingual-cased",
            "method": "mwmf+itermax+argmax-consensus",
            "editions": sorted(editions),
            "units": 0,
            "target_tokens": 0,
            "aligned_target_tokens": 0,
            "traceable_target_tokens": 0,
            "high_support_tokens": 0,
            "medium_support_tokens": 0,
            "low_support_tokens": 0,
            "unaligned_target_tokens": 0,
            "missing_source_token_ids": 0,
        }

        for row in rows:
            witness = witnesses.get(row["source_witness_id"]) or first_witness.get(row["unit_id"])
            if not witness:
                continue

            raw_ids = json.loads(witness.get("source_token_ids_json") or "[]")
            src_ids = [tid for tid in raw_ids if tid in source_tokens]
            stats["missing_source_token_ids"] += len(raw_ids) - len(src_ids)
            src_words = [source_tokens[tid]["surface"] for tid in src_ids]

            target = lexical_tokens(row["text"])
            tgt_words = [t["surface"] for t in target]

            inter_pairs: set[tuple[int, int]] = set()
            iter_pairs: set[tuple[int, int]] = set()
            mwmf_pairs: set[tuple[int, int]] = set()

            if src_words and tgt_words:
                aligns = aligner.get_word_aligns(src_words, tgt_words)
                inter_pairs = {tuple(x) for x in aligns.get("inter", [])}
                iter_pairs = {tuple(x) for x in aligns.get("itermax", [])}
                mwmf_pairs = {tuple(x) for x in aligns.get("mwmf", [])}

            direct_pairs = inter_pairs | iter_pairs | mwmf_pairs
            by_target: dict[int, list[int]] = {}
            for si, ti in sorted(direct_pairs):
                if 0 <= si < len(src_ids) and 0 <= ti < len(target):
                    by_target.setdefault(ti, []).append(si)

            aligned_count = 0
            for tok in target:
                ti = tok["index"]
                source_indices = by_target.get(ti, [])
                tok["source_token_ids"] = [src_ids[i] for i in source_indices]
                supports = []

                for si in source_indices:
                    pair = (si, ti)
                    methods = []
                    if pair in inter_pairs:
                        methods.append("argmax-intersection")
                    if pair in iter_pairs:
                        methods.append("itermax")
                    if pair in mwmf_pairs:
                        methods.append("mwmf")
                    supports.append({"source_index": si, "methods": methods})

                tok["support"] = supports
                if source_indices:
                    aligned_count += 1
                    pairs = [(si, ti) for si in source_indices]
                    if all(pair in inter_pairs for pair in pairs):
                        tok["confidence"] = "high"
                        stats["high_support_tokens"] += 1
                    elif all(pair in (inter_pairs | iter_pairs) for pair in pairs):
                        tok["confidence"] = "medium"
                        stats["medium_support_tokens"] += 1
                    else:
                        tok["confidence"] = "low"
                        stats["low_support_tokens"] += 1
                    tok["trace_status"] = "direct-token-alignment"
                else:
                    # Do not fabricate a lexical equivalence. The web still links this
                    # Spanish token to its exact Greek source unit as contextual provenance.
                    tok["confidence"] = "contextual"
                    tok["trace_status"] = "source-unit-context"

            stats["units"] += 1
            stats["target_tokens"] += len(target)
            stats["aligned_target_tokens"] += aligned_count
            stats["traceable_target_tokens"] += len(target)
            stats["unaligned_target_tokens"] += len(target) - aligned_count

            output_rows.append(
                {
                    "edition_id": row["edition_id"],
                    "unit_id": row["unit_id"],
                    "scene_number": row["scene_number"],
                    "target_text_sha256": sha256_text(row["text"]),
                    "source_witness_id": witness["witness_id"],
                    "source_token_ids": src_ids,
                    "target_tokens": target,
                    "alignment_engine": stats["engine"],
                    "alignment_model": stats["model"],
                    "alignment_method": stats["method"],
                }
            )

        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            for item in output_rows:
                fh.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")

        stats["direct_alignment_coverage"] = (
            round(stats["aligned_target_tokens"] / stats["target_tokens"], 6)
            if stats["target_tokens"]
            else 0.0
        )
        stats["traceability_coverage"] = (
            round(stats["traceable_target_tokens"] / stats["target_tokens"], 6)
            if stats["target_tokens"]
            else 0.0
        )
        # Backward-compatible: "coverage" means direct token alignment, not contextual trace.
        stats["coverage"] = stats["direct_alignment_coverage"]

        summary_path.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    finally:
        book.close()
        source.close()


if __name__ == "__main__":
    main()
