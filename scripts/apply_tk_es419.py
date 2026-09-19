#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "book/el-relato-book.sqlite"
TRANS_DIR = ROOT / "book/translations/tk-es-419"
GENERATED_DIR = TRANS_DIR / "generated"
MANIFEST_PATH = TRANS_DIR / "manifest.json"
POLICY_PATH = TRANS_DIR / "POLICY.md"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def load_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or "unit_id" not in row or "text" not in row:
                raise RuntimeError(f"Invalid translation row at {path}:{lineno}")
            yield row


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Missing Book DB: {DB_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    policy_hash = sha256_bytes(POLICY_PATH.read_bytes())

    edition_id = manifest["edition_id"]
    baseline_id = manifest["baseline_edition_id"]
    expected = int(manifest["pilot"]["units_expected"])
    scene_start = int(manifest["pilot"]["scene_start"])
    scene_end = int(manifest["pilot"]["scene_end"])
    model = manifest["model_name"]
    provider = manifest["provider"]
    policy_id = manifest["policy_id"]

    files = sorted(GENERATED_DIR.glob("scene-*.jsonl"))
    if not files:
        raise RuntimeError("No generated translation files found")

    rows = []
    seen = set()
    for path in files:
        for row in load_jsonl(path):
            uid = row["unit_id"]
            text = row["text"].strip()
            if uid in seen:
                raise RuntimeError(f"Duplicate translated unit: {uid}")
            if not text:
                raise RuntimeError(f"Empty translation: {uid}")
            seen.add(uid)
            rows.append((uid, text))

    if len(rows) != expected:
        raise RuntimeError(f"Expected {expected} translated units, got {len(rows)}")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        baseline = conn.execute(
            "SELECT source_edition_id FROM editions WHERE edition_id=?",
            (baseline_id,),
        ).fetchone()
        if not baseline:
            raise RuntimeError(f"Baseline edition not found: {baseline_id}")
        ultimate_source_id = baseline[0]

        pilot_units = {
            uid: (scene, witness, greek)
            for uid, scene, witness, greek in conn.execute(
                """
                SELECT u.unit_id, u.scene_number, ut.source_witness_id, ut.text
                FROM units u
                JOIN unit_texts ut ON ut.unit_id=u.unit_id
                WHERE ut.edition_id=?
                  AND u.scene_number BETWEEN ? AND ?
                """,
                (baseline_id, scene_start, scene_end),
            )
        }
        if len(pilot_units) != expected:
            raise RuntimeError(
                f"Baseline pilot should contain {expected} units, got {len(pilot_units)}"
            )

        translated_ids = {uid for uid, _ in rows}
        expected_ids = set(pilot_units)
        missing = sorted(expected_ids - translated_ids)
        extra = sorted(translated_ids - expected_ids)
        if missing or extra:
            raise RuntimeError(
                f"Translation unit coverage mismatch; missing={missing[:10]}, extra={extra[:10]}"
            )

        # Idempotent replacement of this generated edition.
        conn.execute("DELETE FROM editions WHERE edition_id=?", (edition_id,))

        derivation_policy = (
            "TK-es-419 V0.1: AI translation from the primary Greek text already "
            "materialized per editorial unit; natural contemporary Latin American Spanish; "
            "parallel witnesses are not silently harmonized; human review required."
        )
        conn.execute(
            """
            INSERT INTO editions(
                edition_id,book_id,language_code,locale,title,edition_role,version,
                derivation_policy,source_edition_id,status,created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                edition_id,
                manifest["book_id"],
                manifest["language_code"],
                manifest["locale"],
                manifest["title"],
                "ai-translation",
                manifest["version"],
                derivation_policy,
                ultimate_source_id,
                manifest["status"],
                now,
            ),
        )

        for uid, text in rows:
            scene, source_witness_id, greek = pilot_units[uid]
            conn.execute(
                """
                INSERT INTO unit_texts(
                    edition_id,unit_id,text,source_witness_id,derivation_method,status
                ) VALUES (?,?,?,?,?,?)
                """,
                (
                    edition_id,
                    uid,
                    text,
                    source_witness_id,
                    "ai-translation:tk-es-419:v0.1",
                    "generated",
                ),
            )
            conn.execute(
                """
                INSERT INTO translation_unit_audit(
                    edition_id,unit_id,baseline_edition_id,source_text_sha256,
                    output_text_sha256,policy_sha256,model_name
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    edition_id,
                    uid,
                    baseline_id,
                    sha256_text(greek),
                    sha256_text(text),
                    policy_hash,
                    model,
                ),
            )

        run_id = "run:tk-es-419:v0.1:pilot-scenes-001-010"
        conn.execute("DELETE FROM translation_runs WHERE run_id=?", (run_id,))
        conn.execute(
            """
            INSERT INTO translation_runs(
                run_id,edition_id,baseline_edition_id,provider,model_name,policy_id,
                policy_sha256,target_locale,units_expected,units_generated,
                generated_at,status,notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                run_id,
                edition_id,
                baseline_id,
                provider,
                model,
                policy_id,
                policy_hash,
                manifest["locale"],
                expected,
                len(rows),
                now,
                "generated-pilot",
                f"Complete pilot coverage for scenes {scene_start}-{scene_end}; human review required before approval.",
            ),
        )

        count = conn.execute(
            "SELECT COUNT(*) FROM unit_texts WHERE edition_id=?",
            (edition_id,),
        ).fetchone()[0]
        audit_count = conn.execute(
            "SELECT COUNT(*) FROM translation_unit_audit WHERE edition_id=?",
            (edition_id,),
        ).fetchone()[0]
        if count != expected or audit_count != expected:
            raise RuntimeError(
                f"Translation persistence mismatch: unit_texts={count}, audit={audit_count}"
            )

        fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk:
            raise RuntimeError(f"Foreign key check failed: {fk[:10]}")

        conn.commit()

        report = {
            "status": "PASS",
            "edition_id": edition_id,
            "baseline_edition_id": baseline_id,
            "locale": manifest["locale"],
            "provider": provider,
            "model_name": model,
            "policy_id": policy_id,
            "policy_sha256": policy_hash,
            "scenes": [scene_start, scene_end],
            "translated_units": count,
            "expected_units": expected,
            "human_review_required": True,
            "foreign_key_check": "ok",
        }
        report_path = TRANS_DIR / "build-report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
