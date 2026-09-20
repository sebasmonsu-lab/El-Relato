#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "book/el-relato-book.sqlite"
DEFAULT_TRANSLATION = ROOT / "book/translations/tk-es-419-v1"

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_generated(folder: Path) -> list[dict]:
    rows: list[dict] = []
    expected = [folder / "generated" / f"scene-{n:03d}.jsonl" for n in range(1, 121)]
    missing = [str(p.relative_to(ROOT)) for p in expected if not p.exists()]
    if missing:
        raise SystemExit(f"Missing generated scene files: {missing}")
    for path in expected:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not row.get("unit_id") or not str(row.get("text") or "").strip():
                raise SystemExit(f"{path}:{line_no}: unit_id/text required")
            rows.append(row)
    return rows

def connect(db: Path, apply: bool) -> sqlite3.Connection:
    if apply:
        con = sqlite3.connect(db)
    else:
        con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate or consolidate one complete BOOK translation into the canonical SQLite database."
    )
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--translation-dir", type=Path, default=DEFAULT_TRANSLATION)
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Write the edition. Without this flag the command is strictly read-only.",
    )
    args = ap.parse_args()

    tdir = args.translation_dir.resolve()
    db = args.db.resolve()
    manifest = read_json(tdir / "manifest.json")
    validation = read_json(tdir / "validation-report.json")
    if validation.get("status") != "PASS":
        raise SystemExit("Refusing consolidation: validation-report.json is not PASS.")

    generated = read_generated(tdir)
    if len(generated) != 4123:
        raise SystemExit(f"Expected 4,123 translated units, found {len(generated):,}.")

    edition_id = manifest["edition_id"]
    baseline_id = manifest["baseline_edition_id"]
    policy_path = tdir / "POLICY.md"
    policy_sha = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    output_digest = hashlib.sha256(
        "\n".join(f'{r["unit_id"]}\t{r["text"]}' for r in generated).encode("utf-8")
    ).hexdigest()
    run_id = f'run:{manifest["code"]}:{output_digest[:16]}'

    con = connect(db, args.apply)
    try:
        existing_editions = [
            dict(r) for r in con.execute(
                "SELECT edition_id, language_code, locale, title, status FROM editions ORDER BY created_at, edition_id"
            )
        ]
        units = [dict(r) for r in con.execute(
            "SELECT unit_id, global_order FROM units ORDER BY global_order"
        )]
        if len(units) != 4123:
            raise SystemExit(f"Canonical BOOK has {len(units):,} units, expected 4,123.")
        expected_ids = [r["unit_id"] for r in units]
        generated_ids = [r["unit_id"] for r in generated]
        if generated_ids != expected_ids:
            missing = sorted(set(expected_ids) - set(generated_ids))
            extra = sorted(set(generated_ids) - set(expected_ids))
            raise SystemExit(
                f"Unit order/coverage mismatch. missing={missing[:20]} extra={extra[:20]}"
            )

        baseline = {
            r["unit_id"]: r["text"]
            for r in con.execute(
                "SELECT unit_id, text FROM unit_texts WHERE edition_id=?",
                (baseline_id,),
            )
        }
        if len(baseline) != 4123:
            raise SystemExit(
                f"Baseline edition {baseline_id} has {len(baseline):,} unit_texts, expected 4,123."
            )

        base_meta = con.execute(
            "SELECT source_edition_id FROM editions WHERE edition_id=?",
            (baseline_id,),
        ).fetchone()
        if base_meta is None:
            raise SystemExit(f"Baseline edition not found: {baseline_id}")

        existing = con.execute(
            "SELECT edition_id FROM editions WHERE edition_id=?",
            (edition_id,),
        ).fetchone()
        if existing:
            current = {
                r["unit_id"]: r["text"]
                for r in con.execute(
                    "SELECT unit_id, text FROM unit_texts WHERE edition_id=?",
                    (edition_id,),
                )
            }
            incoming = {r["unit_id"]: r["text"] for r in generated}
            if current == incoming and len(current) == 4123:
                print(json.dumps({
                    "status": "NOOP",
                    "edition_id": edition_id,
                    "reason": "Edition already exists with identical 4,123 unit texts.",
                    "output_sha256": output_digest,
                }, ensure_ascii=False, indent=2))
                return 0
            raise SystemExit(
                f"Refusing overwrite: {edition_id} already exists with different or incomplete content."
            )

        summary = {
            "status": "READY_TO_APPLY" if not args.apply else "APPLYING",
            "edition_id": edition_id,
            "baseline_edition_id": baseline_id,
            "units": len(generated),
            "scenes": 120,
            "output_sha256": output_digest,
            "policy_sha256": policy_sha,
            "run_id": run_id,
            "write_enabled": bool(args.apply),
            "existing_editions": existing_editions,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if not args.apply:
            return 0

        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        con.execute("BEGIN IMMEDIATE")
        con.execute(
            """INSERT INTO editions
               (edition_id, book_id, language_code, locale, title, edition_role,
                version, derivation_policy, source_edition_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                edition_id,
                manifest["book_id"],
                manifest["language_code"],
                manifest.get("locale"),
                manifest["title"],
                "translation",
                str(manifest["version"]),
                str(policy_path.relative_to(ROOT)),
                base_meta["source_edition_id"],
                manifest.get("status", "generated-full"),
                now,
            ),
        )

        for row in generated:
            unit_id = row["unit_id"]
            text = row["text"]
            model = row.get("model") or "legacy-unattributed"
            row_status = row.get("status") or "legacy-unreviewed"
            method = (
                "llm-translation-from-greek"
                if model == "GPT-5.6 Sol"
                else "legacy-translation-retained"
            )
            con.execute(
                """INSERT INTO unit_texts
                   (edition_id, unit_id, text, source_witness_id, derivation_method, status)
                   VALUES (?, ?, ?, NULL, ?, ?)""",
                (edition_id, unit_id, text, method, row_status),
            )
            con.execute(
                """INSERT INTO translation_unit_audit
                   (edition_id, unit_id, baseline_edition_id, source_text_sha256,
                    output_text_sha256, policy_sha256, model_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    edition_id,
                    unit_id,
                    baseline_id,
                    sha256_text(baseline[unit_id]),
                    sha256_text(text),
                    policy_sha,
                    model,
                ),
            )

        con.execute(
            """INSERT INTO translation_runs
               (run_id, edition_id, baseline_edition_id, provider, model_name,
                policy_id, policy_sha256, target_locale, units_expected,
                units_generated, generated_at, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                edition_id,
                baseline_id,
                manifest.get("provider", "mixed-validated"),
                manifest.get("model_name", "mixed"),
                f'policy:{manifest["code"]}',
                policy_sha,
                manifest["locale"],
                4123,
                4123,
                now,
                "complete",
                (
                    "Consolidated only after validation PASS. "
                    "Legacy rows retain legacy-unattributed provenance; "
                    "GPT-5.6 Sol rows retain explicit model provenance."
                ),
            ),
        )

        count = con.execute(
            "SELECT COUNT(*) FROM unit_texts WHERE edition_id=?", (edition_id,)
        ).fetchone()[0]
        audit_count = con.execute(
            "SELECT COUNT(*) FROM translation_unit_audit WHERE edition_id=?", (edition_id,)
        ).fetchone()[0]
        if count != 4123 or audit_count != 4123:
            raise RuntimeError(
                f"Post-insert verification failed: texts={count}, audit={audit_count}"
            )
        con.commit()
        print(json.dumps({
            "status": "APPLIED",
            "edition_id": edition_id,
            "unit_texts": count,
            "audit_rows": audit_count,
            "run_id": run_id,
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        if args.apply:
            con.rollback()
        raise
    finally:
        con.close()

if __name__ == "__main__":
    raise SystemExit(main())
