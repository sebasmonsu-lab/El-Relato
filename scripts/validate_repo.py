#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []

try:
    import jsonschema
except ImportError:
    jsonschema = None


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return None


# 1) Every JSON file in data/ and schemas/ must parse.
for base in [ROOT / "data", ROOT / "schemas"]:
    if base.exists():
        for path in base.rglob("*.json"):
            load_json(path)

# 2) Validate JSONL normalized datasets when a sibling/schema mapping is known.
schema_map = {
    "sources.jsonl": "source.schema.json",
    "manuscripts.jsonl": "manuscript.schema.json",
    "tokens.jsonl": "token.schema.json",
    "lexemes.jsonl": "lexeme.schema.json",
    "morphology.jsonl": "morphology.schema.json",
    "variants.jsonl": "variant.schema.json",
    "strong-entries.jsonl": "strong-entry.schema.json",
    "strong-original-entries.jsonl": "strong-original-entry.schema.json",
    "tagnt-rows.jsonl": "tagnt-row.schema.json",
    "passages.jsonl": "passage.schema.json",
    "editions.jsonl": "edition.schema.json",
    "edition-verses.jsonl": "edition-verse.schema.json",
}

normalized = ROOT / "data" / "normalized"
if normalized.exists():
    for path in normalized.rglob("*.jsonl"):
        schema_name = schema_map.get(path.name)
        validator = None
        if schema_name and jsonschema is not None:
            schema = load_json(ROOT / "schemas" / schema_name)
            if schema is not None:
                validator_cls = jsonschema.validators.validator_for(schema)
                validator_cls.check_schema(schema)
                validator = validator_cls(schema, format_checker=jsonschema.FormatChecker())

        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            try:
                obj = json.loads(raw)
            except Exception as exc:
                errors.append(f"{path.relative_to(ROOT)}:{lineno}: invalid JSONL: {exc}")
                continue
            if validator is not None:
                row_errors = sorted(validator.iter_errors(obj), key=lambda e: list(e.path))
                for exc in row_errors:
                    where = ".".join(str(x) for x in exc.path)
                    suffix = f" [{where}]" if where else ""
                    errors.append(f"{path.relative_to(ROOT)}:{lineno}: schema error{suffix}: {exc.message}")

# 3) Basic preservation invariants.
required = [
    ROOT / "README.md",
    ROOT / "PROJECT_PLAN.md",
    ROOT / "STATUS.md",
    ROOT / "docs" / "ARCHITECTURE.md",
    ROOT / "docs" / "LOOP_PROTOCOL.md",
    ROOT / "data" / "manifests" / "core-sources.json",
    ROOT / "data" / "manifests" / "manuscripts.json",
]
for path in required:
    if not path.exists():
        errors.append(f"missing required project file: {path.relative_to(ROOT)}")

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("VALIDATION OK")
