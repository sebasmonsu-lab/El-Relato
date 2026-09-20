#!/usr/bin/env python3
"""Build the canonical, multilingual Gospel reader into the existing static site.

Greek is materialized from the normalized SOURCE query database. Additional
translations live under sources/gospel-editions/<slug>/ and are published only
when their edition metadata is marked consolidated/published.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from build_web import BOOK_LABELS, BOOK_SLUGS, CSS, esc, safe, token_span

ROOT = Path(__file__).resolve().parents[1]
EDITIONS_ROOT = ROOT / "sources/gospel-editions"
PUBLIC_STATUSES = {"canonical-source", "consolidated", "published"}
CANON = ["Matthew", "Mark", "Luke", "John"]
GREEK_EDITION_ID = "edition:gospels:grc-sblgnt-2010:v1"


def gospel_page(site_root, title, body):
    greek_slug = safe(GREEK_EDITION_ID)
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)} · Los Evangelios</title><style>{CSS}.reader{max-width:760px;margin:auto}.reader .unit{border:0;padding:0;margin:.25rem 0}.reader .ref{display:inline;font-size:.72rem;vertical-align:super;margin-right:.25rem}.reader .ref .badge{display:none}.reader .greek,.reader .text{display:inline;font-size:1.25rem;line-height:2}.chapter-nav{display:flex;justify-content:space-between;gap:16px;margin:24px 0}.chapter-picker{display:flex;gap:7px;flex-wrap:wrap;margin:18px 0}.chapter-picker a{display:inline-block;border:1px solid #c9c0b0;border-radius:999px;padding:5px 9px;text-decoration:none}.chapter-picker a.current{background:#211f1a;color:white}.reader-note{font-size:.88rem;color:#716c62}</style></head><body>"
        f'<header><a href="{site_root}gospels/index.html"><strong>Los Evangelios</strong></a><nav>'
        f'<a href="{site_root}gospels/index.html">Ediciones</a>'
        f'<a href="{site_root}gospels/{greek_slug}/index.html">Griego</a>'
        f'</nav></header><main>{body}</main></body></html>'
    )


def connect_ro(path: Path):
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_editions():
    editions = []
    if not EDITIONS_ROOT.exists():
        return editions
    for meta_path in sorted(EDITIONS_ROOT.glob("*/edition.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["_dir"] = str(meta_path.parent)
        if meta.get("status") in PUBLIC_STATUSES:
            editions.append(meta)
    return editions


def load_translation(meta):
    verses_path = Path(meta["_dir"]) / "verses.jsonl"
    if not verses_path.exists():
        raise SystemExit(f"Published translation has no verses.jsonl: {meta['edition_id']}")
    rows = {}
    with verses_path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            key = (row["book"], int(row["chapter"]), int(row["verse"]))
            if key in rows:
                raise SystemExit(f"Duplicate Gospel verse {key} in {meta['edition_id']}")
            rows[key] = row
    return rows


def greek_text(tokens, root):
    return "".join(token_span(root, token) for token in tokens)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="build/site")
    ap.add_argument("--query-db", default="build/el-relato.sqlite")
    args = ap.parse_args()

    site = ROOT / args.site
    query_db = ROOT / args.query_db
    editions = load_editions()
    if not editions:
        raise SystemExit("No public Gospel SOURCE editions found")

    source = connect_ro(query_db)
    try:
        tokens = [dict(r) for r in source.execute(
            """select * from tokens
               order by case book when 'Matthew' then 1 when 'Mark' then 2
                                  when 'Luke' then 3 else 4 end,
                        chapter,verse,position"""
        )]
    finally:
        source.close()

    verse_tokens = {}
    for token in tokens:
        verse_tokens.setdefault((token["book"], token["chapter"], token["verse"]), []).append(token)
    canonical_keys = set(verse_tokens)

    edition_verses = {}
    for edition in editions:
        if edition["edition_id"] == GREEK_EDITION_ID:
            edition_verses[edition["edition_id"]] = None
            continue
        rows = load_translation(edition)
        missing = canonical_keys - set(rows)
        extra = set(rows) - canonical_keys
        if missing or extra:
            raise SystemExit(
                f"Consolidated Gospel edition {edition['edition_id']} must match canonical verse set: "
                f"missing={len(missing)} extra={len(extra)}"
            )
        edition_verses[edition["edition_id"]] = rows

    def eslug(e):
        return safe(e["edition_id"])

    cards = "".join(
        f'<a class="card" href="{eslug(e)}/index.html"><h2>{esc(e["title"])}</h2>'
        f'<p>{esc(e["language_code"])} · {esc(e["version"])} · {esc(e["status"])}</p></a>'
        for e in editions
    )
    (site / "gospels").mkdir(parents=True, exist_ok=True)
    (site / "gospels/index.html").write_text(
        gospel_page(
            "../",
            "Los Evangelios",
            '<section class="hero"><h1>Los Evangelios</h1>'
            '<p>Mateo, Marcos, Lucas y Juan en orden canónico. Elegí una edición o idioma.</p></section>'
            f'<div class="grid">{cards}</div>'
            '<p class="muted">Las traducciones publicadas conservan una referencia explícita a la edición griega base.</p>',
        ),
        encoding="utf-8",
    )

    greek_slug = safe(GREEK_EDITION_ID)
    for edition in editions:
        slug = eslug(edition)
        is_greek = edition["edition_id"] == GREEK_EDITION_ID
        translation_rows = edition_verses[edition["edition_id"]]
        book_cards = "".join(
            f'<a class="card" href="{BOOK_SLUGS[b]}/index.html"><h2>{BOOK_LABELS[b]}</h2></a>'
            for b in CANON
        )
        edir = site / "gospels" / slug
        edir.mkdir(parents=True, exist_ok=True)
        (edir / "index.html").write_text(
            gospel_page(
                "../../",
                edition["title"],
                f'<h1>{esc(edition["title"])}</h1>'
                f'<p><span class="badge">{esc(edition["language_code"])}</span> '
                f'<span class="badge">{esc(edition["version"])}</span> '
                f'<span class="badge">{esc(edition["status"])}</span></p>'
                f'<div class="grid">{book_cards}</div>',
            ),
            encoding="utf-8",
        )

        for book in CANON:
            bslug = BOOK_SLUGS[book]
            book_keys = sorted(
                [k for k in canonical_keys if k[0] == book],
                key=lambda k: (k[1], k[2]),
            )
            chapters = sorted({k[1] for k in book_keys})
            chapter_links = "".join(
                f'<a class="card" href="{ch}/index.html"><h2>Capítulo {ch}</h2></a>'
                for ch in chapters
            )
            bdir = edir / bslug
            bdir.mkdir(parents=True, exist_ok=True)
            (bdir / "index.html").write_text(
                gospel_page(
                    "../../../",
                    BOOK_LABELS[book],
                    f'<div class="crumbs"><a href="../index.html">{esc(edition["title"])}</a></div>'
                    f'<h1>{BOOK_LABELS[book]}</h1><div class="grid">{chapter_links}</div>',
                ),
                encoding="utf-8",
            )

            for chapter in chapters:
                verses = [k[2] for k in book_keys if k[1] == chapter]
                chapter_index = chapters.index(chapter)
                prev_ch = chapters[chapter_index - 1] if chapter_index > 0 else None
                next_ch = chapters[chapter_index + 1] if chapter_index + 1 < len(chapters) else None
                nav = (
                    (f'<a href="../{prev_ch}/index.html">← capítulo {prev_ch}</a>' if prev_ch else "")
                    + " &nbsp; "
                    + (f'<a href="../{next_ch}/index.html">capítulo {next_ch} →</a>' if next_ch else "")
                )
                selector = " · ".join(
                    f'<a href="../../../{eslug(other)}/{bslug}/{chapter}/index.html">'
                    f'{esc(other["language_code"])}</a>'
                    for other in editions
                )
                blocks = []
                for verse in verses:
                    key = (book, chapter, verse)
                    if is_greek:
                        rendered = greek_text(verse_tokens[key], "../../../../")
                        klass = "greek"
                        provenance = '<span class="badge">SOURCE griego</span>'
                    else:
                        row = translation_rows[key]
                        rendered = esc(row["text"])
                        klass = "text"
                        provenance = (
                            f'<a class="badge" href="../../../{greek_slug}/{bslug}/{chapter}/{verse}.html">'
                            'ver griego base</a>'
                        )
                    blocks.append(
                        f'<section class="unit" id="v{verse}">'
                        f'<div class="ref"><a href="{verse}.html">{BOOK_LABELS[book]} {chapter}:{verse}</a> '
                        f'{provenance}</div><div class="{klass}">{rendered}</div></section>'
                    )

                    vbody = (
                        f'<div class="crumbs"><a href="index.html">← {BOOK_LABELS[book]} {chapter}</a></div>'
                        f'<h1>{BOOK_LABELS[book]} {chapter}:{verse}</h1>'
                        f'<div class="card {klass}">{rendered}</div>'
                    )
                    if not is_greek:
                        vbody += (
                            f'<p><a href="../../../{greek_slug}/{bslug}/{chapter}/{verse}.html">'
                            'Abrir el versículo griego base →</a></p>'
                        )
                    (edir / bslug / str(chapter)).mkdir(parents=True, exist_ok=True)
                    (edir / bslug / str(chapter) / f"{verse}.html").write_text(
                        gospel_page("../../../../", f"{BOOK_LABELS[book]} {chapter}:{verse}", vbody),
                        encoding="utf-8",
                    )

                picker = " ".join(
                    f'<a class="{"current" if ch == chapter else ""}" href="../{ch}/index.html">{ch}</a>'
                    for ch in chapters
                )
                cbody = (
                    f'<div class="reader"><div class="crumbs"><a href="../index.html">{BOOK_LABELS[book]}</a> / capítulo {chapter}</div>'
                    f'<h1>{BOOK_LABELS[book]} {chapter}</h1>'
                    f'<p class="reader-note">Edición: <strong>{esc(edition["title"])}</strong> · Cambiar: {selector}</p>'
                    f'<div class="chapter-picker" aria-label="Capítulos">{picker}</div>'
                    f'<div class="chapter-nav">{nav}</div>'
                    f'{"".join(blocks)}'
                    f'<div class="chapter-nav">{nav}</div></div>'
                )
                cdir = edir / bslug / str(chapter)
                cdir.mkdir(parents=True, exist_ok=True)
                (cdir / "index.html").write_text(
                    gospel_page("../../../../", f"{BOOK_LABELS[book]} {chapter}", cbody),
                    encoding="utf-8",
                )

    manifest_path = site / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["gospel_editions"] = [
        {
            "edition_id": e["edition_id"],
            "title": e["title"],
            "language_code": e["language_code"],
            "version": e["version"],
            "status": e["status"],
            "base_edition_id": e.get("base_edition_id"),
        }
        for e in editions
    ]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gospel_editions": len(editions), "canonical_verses": len(canonical_keys)}, indent=2))


if __name__ == "__main__":
    main()
