#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/derived/manuscripts/core-gospel-facsimile-plan.jsonl"
MANIFEST_ROOT = ROOT / "data/manifests/facsimiles"
SUMMARY_PATH = ROOT / "data/derived/manuscripts/core-gospel-facsimile-mirror-summary.json"


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def safe_label(label: str):
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", label.strip())
    return s.strip("_") or "unnamed"


def local_path(row):
    if row["source"] == "Vaticanus":
        base = ROOT / "sources/manuscripts/Vaticanus/images/gospels"
    elif row["source"] == "Sinaiticus-BL":
        base = ROOT / "sources/manuscripts/Sinaiticus/images/gospels"
    else:
        raise ValueError(row["source"])
    return base / f"{safe_label(row['label'])}.jpg"


def sha256_file(path: Path):
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def download_one(row):
    import requests

    dest = local_path(row)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Existing full files from an earlier batch/rerun are verified and reused.
    if dest.exists() and dest.stat().st_size > 10_000:
        sha, size = sha256_file(dest)
        return {
            **row,
            "status": "already-present",
            "local_path": dest.relative_to(ROOT).as_posix(),
            "sha256": sha,
            "size": size,
            "error": None,
        }

    url = row.get("full_image_url")
    if not url:
        return {
            **row,
            "status": "failed",
            "local_path": dest.relative_to(ROOT).as_posix(),
            "sha256": None,
            "size": None,
            "error": "missing full_image_url",
        }

    session = requests.Session()
    session.headers.update({
        "User-Agent": "El-Relato-preservation/1.0",
        "Accept-Encoding": "identity",
    })

    last_error = None
    for attempt in range(1, 5):
        tmp = dest.with_suffix(".jpg.part")
        try:
            with session.get(url, stream=True, timeout=(15, 90), allow_redirects=True) as r:
                r.raise_for_status()
                ctype = r.headers.get("Content-Type", "")
                if not ctype.startswith("image/"):
                    raise RuntimeError(f"unexpected content type: {ctype}")
                h = hashlib.sha256()
                size = 0
                with tmp.open("wb") as out:
                    for chunk in r.iter_content(1024 * 256):
                        if not chunk:
                            continue
                        out.write(chunk)
                        h.update(chunk)
                        size += len(chunk)

            if size < 10_000:
                raise RuntimeError(f"image too small: {size} bytes")
            # JPEG SOI marker. The current IIIF plan requests default.jpg.
            with tmp.open("rb") as fh:
                if fh.read(2) != b"\xff\xd8":
                    raise RuntimeError("downloaded file is not JPEG")
            expected = row.get("content_length")
            if isinstance(expected, int) and expected > 0 and expected != size:
                raise RuntimeError(f"size mismatch: got {size}, expected {expected}")

            tmp.replace(dest)
            return {
                **row,
                "status": "mirrored",
                "local_path": dest.relative_to(ROOT).as_posix(),
                "sha256": h.hexdigest(),
                "size": size,
                "error": None,
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            time.sleep(attempt * 2)

    return {
        **row,
        "status": "failed",
        "local_path": dest.relative_to(ROOT).as_posix(),
        "sha256": None,
        "size": None,
        "error": last_error,
    }


def run_batch(source, offset, limit):
    rows = [x for x in read_jsonl(PLAN) if x["source"] == source]
    batch = rows[offset:offset + limit]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(download_one, batch))

    outdir = MANIFEST_ROOT / safe_label(source)
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": source,
        "offset": offset,
        "limit": limit,
        "selected": len(batch),
        "mirrored_or_present": sum(x["status"] in {"mirrored","already-present"} for x in results),
        "failed": sum(x["status"] == "failed" for x in results),
        "files": results,
    }
    path = outdir / f"batch-{offset:04d}-{offset+max(len(batch)-1,0):04d}.json"
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "manifest": path.relative_to(ROOT).as_posix(),
        "selected": manifest["selected"],
        "mirrored_or_present": manifest["mirrored_or_present"],
        "failed": manifest["failed"],
    },indent=2))


def audit():
    plan = read_jsonl(PLAN)
    rows = []
    missing = 0
    total = 0
    by_source = {}
    for item in plan:
        dest = local_path(item)
        entry = {
            "source": item["source"],
            "label": item["label"],
            "gospels": item["gospels"],
            "canvas_id": item["canvas_id"],
            "source_url": item.get("full_image_url"),
            "local_path": dest.relative_to(ROOT).as_posix(),
            "width": item.get("width"),
            "height": item.get("height"),
            "sha256": None,
            "size": None,
            "status": "missing",
        }
        if dest.exists() and dest.stat().st_size > 10_000:
            sha, size = sha256_file(dest)
            entry["sha256"] = sha
            entry["size"] = size
            entry["status"] = "mirrored"
            total += size
            by_source.setdefault(item["source"], {"files":0,"bytes":0})
            by_source[item["source"]]["files"] += 1
            by_source[item["source"]]["bytes"] += size
        else:
            missing += 1
        rows.append(entry)

    summary = {
        "planned_files": len(plan),
        "mirrored_files": len(plan)-missing,
        "missing_files": missing,
        "complete": missing == 0,
        "total_bytes": total,
        "total_gib": round(total/(1024**3),3),
        "by_source": by_source,
        "manifest_entries": rows,
    }
    SUMMARY_PATH.parent.mkdir(parents=True,exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="manifest_entries"},indent=2))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",choices=["Vaticanus","Sinaiticus-BL"])
    ap.add_argument("--offset",type=int,default=0)
    ap.add_argument("--limit",type=int,default=50)
    ap.add_argument("--audit",action="store_true")
    args=ap.parse_args()
    if args.audit:
        audit()
    else:
        if not args.source:
            ap.error("--source is required unless --audit")
        run_batch(args.source,args.offset,args.limit)


if __name__=="__main__":
    main()
