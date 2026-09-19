#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/derived/manuscripts"
OUT.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def vaticanus_gospels(label: str):
    try:
        p = int(label)
    except (TypeError, ValueError):
        return []
    gs = []
    if 1235 <= p <= 1277:
        gs.append("Matthew")
    if 1277 <= p <= 1303:
        gs.append("Mark")
    if 1304 <= p <= 1349:
        gs.append("Luke")
    if 1349 <= p <= 1382:
        gs.append("John")
    return gs


def folio_ord(label: str):
    m = re.fullmatch(r"f\.\s*(\d+)([rv])", label or "")
    if not m:
        return None
    n = int(m.group(1))
    side = 0 if m.group(2) == "r" else 1
    return n * 2 + side


def in_folio_range(label, start, end):
    x = folio_ord(label)
    a = folio_ord(start)
    b = folio_ord(end)
    return x is not None and a <= x <= b


def sinaiticus_gospels(label: str):
    gs = []
    if in_folio_range(label, "f. 200r", "f. 217r"):
        gs.append("Matthew")
    if in_folio_range(label, "f. 217v", "f. 228r"):
        gs.append("Mark")
    if in_folio_range(label, "f. 228r", "f. 246v"):
        gs.append("Luke")
    if in_folio_range(label, "f. 247r", "f. 260r"):
        gs.append("John")
    return gs


def candidate_urls(source, service):
    service = service.rstrip("/")
    if source == "Vaticanus":
        return [
            service + "/full/full/0/default.jpg",
            service + "/full/max/0/default.jpg",
        ]
    return [
        service + "/full/max/0/default.jpg",
        service + "/full/full/0/default.jpg",
    ]


def probe_one(row):
    import requests

    session = requests.Session()
    session.headers.update({
        "User-Agent": "El-Relato-preservation/1.0",
        "Accept-Encoding": "identity",
    })
    result = dict(row)
    result.update({
        "full_image_url": None,
        "http_status": None,
        "content_type": None,
        "content_length": None,
        "size_probe_status": "unprobed",
    })
    for url in candidate_urls(row["source"], row["image_service"]):
        try:
            r = session.get(
                url,
                headers={"Range": "bytes=0-0"},
                stream=True,
                timeout=(10, 25),
                allow_redirects=True,
            )
            result["http_status"] = r.status_code
            result["content_type"] = r.headers.get("Content-Type")
            total = None
            cr = r.headers.get("Content-Range", "")
            if "/" in cr:
                tail = cr.rsplit("/", 1)[1]
                if tail.isdigit():
                    total = int(tail)
            if total is None:
                cl = r.headers.get("Content-Length")
                if cl and cl.isdigit() and r.status_code == 200:
                    total = int(cl)
            if r.status_code in (200, 206) and (result["content_type"] or "").startswith("image/"):
                result["full_image_url"] = r.url
                result["content_length"] = total
                result["size_probe_status"] = "measured" if total is not None else "url-confirmed-size-unknown"
                r.close()
                return result
            r.close()
        except Exception as exc:
            result["size_probe_status"] = f"error:{type(exc).__name__}"
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe-sizes", action="store_true")
    args = ap.parse_args()

    sources = [
        (
            "Vaticanus",
            ROOT / "sources/manuscripts/Vaticanus/raw/iiif-canvases.jsonl",
            vaticanus_gospels,
        ),
        (
            "Sinaiticus-BL",
            ROOT / "sources/manuscripts/Sinaiticus/raw/british-library/iiif-canvases.jsonl",
            sinaiticus_gospels,
        ),
    ]

    selected = []
    for source, path, selector in sources:
        for row in read_jsonl(path):
            gs = selector(row.get("label"))
            if not gs:
                continue
            selected.append({
                "source": source,
                "label": row.get("label"),
                "gospels": gs,
                "canvas_id": row.get("id"),
                "width": row.get("width"),
                "height": row.get("height"),
                "image_id": row.get("image_id"),
                "image_service": row.get("image_service"),
            })

    if args.probe_sizes:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            selected = list(ex.map(probe_one, selected))

    plan = OUT / "core-gospel-facsimile-plan.jsonl"
    with plan.open("w", encoding="utf-8", newline="\n") as fh:
        for row in selected:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    by_source = {}
    by_gospel = {}
    total_known = 0
    known_files = 0
    unknown_files = 0
    for row in selected:
        by_source[row["source"]] = by_source.get(row["source"], 0) + 1
        for g in row["gospels"]:
            by_gospel[g] = by_gospel.get(g, 0) + 1
        if args.probe_sizes:
            if row.get("content_length") is not None:
                known_files += 1
                total_known += row["content_length"]
            else:
                unknown_files += 1

    summary = {
        "selected_canvases": len(selected),
        "by_source": by_source,
        "by_gospel_membership": by_gospel,
        "size_probe_enabled": args.probe_sizes,
        "measured_files": known_files,
        "unmeasured_files": unknown_files,
        "known_total_bytes": total_known if args.probe_sizes else None,
        "known_total_gib": round(total_known / (1024 ** 3), 3) if args.probe_sizes else None,
        "note": "Gospel memberships overlap at boundary canvases where a page/folio contains material from two Gospels.",
    }
    (OUT / "core-gospel-facsimile-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
