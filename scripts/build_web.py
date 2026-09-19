#!/usr/bin/env python3
"""Build El Relato public static site. BOOK DB is strictly read-only."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_DB = ROOT / "book/el-relato-book.sqlite"
QUERY_DB = ROOT / "build/el-relato.sqlite"
ALIGN_PATH = ROOT / "build/translation-alignments.jsonl"
ALIGN_SUMMARY = ROOT / "build/translation-alignments-summary.json"

BOOK_SLUGS = {"Matthew": "matthew", "Mark": "mark", "Luke": "luke", "John": "john"}
BOOK_LABELS = {"Matthew": "Mateo", "Mark": "Marcos", "Luke": "Lucas", "John": "Juan"}
GREEK_LANGS = {"grc", "el", "gr"}

CSS = """*{box-sizing:border-box}
body{margin:0;background:#f6f3ec;color:#211f1a;font-family:system-ui,-apple-system,sans-serif}
header{position:sticky;top:0;z-index:5;background:#1d1d1b;color:#fff;padding:14px 5vw;display:flex;gap:20px;align-items:center;flex-wrap:wrap}
header a{color:#fff;text-decoration:none}nav{display:flex;gap:14px}
main{max-width:1120px;margin:auto;padding:30px 22px 70px}
a{color:#315d85}.hero{padding:38px 0 20px}
.card{background:#fff;border:1px solid #ddd6c8;border-radius:12px;padding:18px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.muted{color:#716c62}.greek{font-family:Georgia,'Times New Roman',serif;font-size:1.35rem;line-height:1.9}
.text{font-size:1.12rem;line-height:1.9}
.token{display:inline-block;padding:0 2px;border-radius:4px;text-decoration:none;color:#202b35}
.token:hover{background:#e9dfca}
.trans-token{display:inline-block;padding:0 2px;border-radius:4px;text-decoration:none;color:#183d66;border-bottom:2px solid #93aac2}
.trans-token:hover{background:#dfeaf3}.trans-token.medium{border-bottom-style:dashed}
.unaligned-token{border-bottom:1px dotted #b8aea0}
.ref{font-size:.9rem}.badge{display:inline-block;border:1px solid #c9c0b0;border-radius:999px;padding:2px 8px;font-size:.78rem;margin:2px}
.unit{border-left:3px solid #d6c6a5;padding-left:14px;margin:18px 0}
.crumbs{font-size:.9rem;margin-bottom:22px}.analysis dt{font-weight:700}.analysis dd{margin:0 0 10px}
.greek-layer{margin-top:10px;background:#faf8f2;padding:10px 12px;border-radius:8px}
.align-note{font-size:.82rem;color:#716c62}
code{overflow-wrap:anywhere}
@media(max-width:600px){.greek{font-size:1.18rem}header{position:static}}"""


def esc(x):
    return html.escape(str(x or ""))


def safe(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(s)).strip("-").lower()


def q(conn, sql, args=()):
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute(sql, args).fetchall()]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def page(root, title, body):
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)} · El Relato</title><style>{CSS}</style></head><body>"
        f'<header><a href="{root}index.html"><strong>El Relato</strong></a><nav>'
        f'<a href="{root}editions/index.html">Ediciones</a>'
        f'<a href="{root}source/index.html">Fuentes</a>'
        f'<a href="{root}about.html">Método</a></nav></header><main>{body}</main></body></html>'
    )


def token_span(root, token):
    tid = token.get("token_id")
    surface = esc(token.get("surface"))
    pre = esc(token.get("prefix_before"))
    post = esc(token.get("punctuation_after"))
    if tid:
        link = f'<a class="token" href="{root}token/{safe(tid)}.html" title="{esc(token.get("strongs"))}">{surface}</a>'
    else:
        link = surface
    return pre + link + post


def edition_slug(edition):
    return safe(edition["edition_id"])


def connect_ro(path):
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def render_translation(root, eslug, uid, text, alignment, token_by_id):
    text = text or ""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if not alignment or alignment.get("target_text_sha256") != digest:
        return esc(text), False

    parts = []
    cursor = 0
    for tok in alignment.get("target_tokens", []):
        start = int(tok["start"])
        end = int(tok["end"])
        if start < cursor or end > len(text):
            continue
        parts.append(esc(text[cursor:start]))
        label = esc(text[start:end])
        source_ids = [tid for tid in tok.get("source_token_ids", []) if tid in token_by_id]
        if source_ids:
            greek = " ".join(token_by_id[tid]["surface"] for tid in source_ids)
            conf = tok.get("confidence", "medium")
            parts.append(
                f'<a class="trans-token {esc(conf)}" '
                f'href="{root}alignment/{eslug}/{safe(uid)}/{tok["index"]}.html" '
                f'title="Griego: {esc(greek)}">{label}</a>'
            )
        else:
            parts.append(
                f'<span class="unaligned-token" title="Sin alineamiento automático">{label}</span>'
            )
        cursor = end
    parts.append(esc(text[cursor:]))
    return "".join(parts), True


def build(out):
    if not BOOK_DB.exists():
        raise SystemExit("Missing canonical BOOK DB")
    if not QUERY_DB.exists():
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_query_db.py"), "--output", "build/el-relato.sqlite"],
            cwd=ROOT,
            check=True,
        )

    book = connect_ro(BOOK_DB)
    source = connect_ro(QUERY_DB)
    try:
        chapters = q(book, "select * from chapters order by chapter_order")
        scenes = q(book, "select * from scenes order by scene_number")
        units = q(book, "select * from units order by global_order")
        editions = q(book, "select * from editions order by created_at, edition_id")
        edition_by_id = {e["edition_id"]: e for e in editions}

        all_texts = q(book, "select * from unit_texts")
        texts_by_ed = {}
        for row in all_texts:
            texts_by_ed.setdefault(row["edition_id"], {})[row["unit_id"]] = row

        witnesses = {}
        for row in q(book, "select * from unit_witnesses order by unit_id,witness_order"):
            witnesses.setdefault(row["unit_id"], []).append(row)

        scene_units = {}
        unit_by_id = {u["unit_id"]: u for u in units}
        for unit in units:
            scene_units.setdefault(unit["scene_number"], []).append(unit)

        source_tokens = q(
            source,
            """select * from tokens
               order by case book when 'Matthew' then 1 when 'Mark' then 2
                                  when 'Luke' then 3 else 4 end,
                        chapter,verse,position""",
        )
        token_by_id = {t["token_id"]: t for t in source_tokens}
        verse_tokens = {}
        for token in source_tokens:
            verse_tokens.setdefault((token["book"], token["chapter"], token["verse"]), []).append(token)

        alignment_rows = load_jsonl(ALIGN_PATH)
        align_by_unit = {(r["edition_id"], r["unit_id"]): r for r in alignment_rows}
        translation_reverse = {}
        for alignment in alignment_rows:
            for target in alignment.get("target_tokens", []):
                for tid in target.get("source_token_ids", []):
                    translation_reverse.setdefault(tid, []).append(
                        {
                            "edition_id": alignment["edition_id"],
                            "unit_id": alignment["unit_id"],
                            "scene_number": alignment.get("scene_number"),
                            "token_index": target["index"],
                            "surface": target["surface"],
                            "confidence": target.get("confidence", "medium"),
                        }
                    )

        if ALIGN_SUMMARY.exists():
            alignment_summary = json.loads(ALIGN_SUMMARY.read_text(encoding="utf-8"))
        else:
            alignment_summary = {
                "units": 0,
                "target_tokens": 0,
                "aligned_target_tokens": 0,
                "coverage": 0,
            }

        reverse = {}
        for uid, unit_witnesses in witnesses.items():
            unit = unit_by_id.get(uid)
            if not unit:
                continue
            for witness in unit_witnesses:
                for tid in json.loads(witness.get("source_token_ids_json") or "[]"):
                    reverse.setdefault(tid, []).append(
                        {
                            "unit_id": uid,
                            "scene_number": unit["scene_number"],
                            "reference": witness["reference_component"],
                        }
                    )

        edcards = "".join(
            f'<a class="card" href="editions/{edition_slug(e)}/index.html">'
            f'<h2>{esc(e["title"])}</h2><p>{esc(e["language_code"])} · {esc(e["version"])} · {esc(e["status"])}</p></a>'
            for e in editions
        )
        write(
            out / "index.html",
            page(
                "",
                "Inicio",
                '<section class="hero"><h1>El Relato</h1>'
                '<p>Libro multilingüe y herramienta de investigación trazable de los cuatro Evangelios.</p></section>'
                f'<h2>Ediciones disponibles</h2><div class="grid">{edcards}</div>'
                '<a class="card" href="source/index.html"><h2>Explorar SOURCE</h2>'
                '<p>Mateo, Marcos, Lucas y Juan palabra por palabra.</p></a>',
            ),
        )
        write(
            out / "editions/index.html",
            page("../", "Ediciones", f'<h1>Ediciones</h1><div class="grid">{edcards.replace("editions/", "")}</div>'),
        )

        by_chapter = {}
        for scene in scenes:
            by_chapter.setdefault(scene["chapter_number"], []).append(scene)

        for edition in editions:
            eslug = edition_slug(edition)
            texts = texts_by_ed.get(edition["edition_id"], {})
            cards = ""
            for chapter in chapters:
                cards += (
                    f'<div class="card"><h2>Capítulo {esc(chapter["chapter_number"])} · {esc(chapter["title"])}</h2><ol>'
                )
                cards += "".join(
                    f'<li><a href="scene/{scene["scene_number"]}.html">'
                    f'{scene["scene_number"]}. {esc(scene["title"])}</a></li>'
                    for scene in by_chapter.get(chapter["chapter_number"], [])
                )
                cards += "</ol></div>"

            write(
                out / f"editions/{eslug}/index.html",
                page(
                    "../../",
                    edition["title"],
                    f'<h1>{esc(edition["title"])}</h1>'
                    f'<p><span class="badge">{esc(edition["language_code"])}</span> '
                    f'<span class="badge">{esc(edition["version"])}</span> '
                    f'<span class="badge">{esc(edition["status"])}</span></p>'
                    f'<p class="muted"><code>{esc(edition["edition_id"])}</code></p>{cards}',
                ),
            )

            is_greek = (edition["language_code"] or "").lower() in GREEK_LANGS
            for scene in scenes:
                blocks = []
                for unit in scene_units.get(scene["scene_number"], []):
                    unit_text = texts.get(unit["unit_id"], {})
                    unit_witnesses = witnesses.get(unit["unit_id"], [])
                    primary = next(
                        (w for w in unit_witnesses if w["witness_id"] == unit_text.get("source_witness_id")),
                        unit_witnesses[0] if unit_witnesses else None,
                    )
                    tids = json.loads(primary.get("source_token_ids_json") or "[]") if primary else []
                    greek_tokens = [token_by_id[tid] for tid in tids if tid in token_by_id]

                    if is_greek:
                        rendered = (
                            "".join(token_span("../../../", token) for token in greek_tokens)
                            if greek_tokens
                            else esc(unit_text.get("text"))
                        )
                        aligned = False
                    else:
                        rendered, aligned = render_translation(
                            "../../../",
                            eslug,
                            unit["unit_id"],
                            unit_text.get("text"),
                            align_by_unit.get((edition["edition_id"], unit["unit_id"])),
                            token_by_id,
                        )

                    klass = "greek" if is_greek else "text"
                    source_link = (
                        f' · <a href="../../../source/{BOOK_SLUGS[primary["book_code"]]}/'
                        f'{primary["chapter"]}/{primary["verse_start"]}.html">fuente griega</a>'
                        if primary and primary["book_code"] in BOOK_SLUGS
                        else ""
                    )
                    refs = " · ".join(esc(w["reference_component"]) for w in unit_witnesses)
                    greek_layer = ""
                    if not is_greek and greek_tokens:
                        greek_text = "".join(token_span("../../../", token) for token in greek_tokens)
                        greek_layer = (
                            '<details class="greek-layer"><summary>Capa griega subyacente</summary>'
                            f'<div class="greek">{greek_text}</div>'
                            '<p class="align-note">Las palabras españolas subrayadas abren su alineamiento explícito '
                            "con estos tokens griegos.</p></details>"
                        )
                    align_badge = (
                        ' <span class="badge">alineación griega activa</span>'
                        if (not is_greek and aligned)
                        else ""
                    )
                    blocks.append(
                        f'<section class="unit" id="{esc(unit["unit_id"])}">'
                        f'<div class="ref"><strong>{esc(unit["reference_raw"])}</strong>'
                        f"{source_link}{align_badge}</div>"
                        f'<div class="{klass}">{rendered}</div>{greek_layer}'
                        f'<details><summary>Trazabilidad</summary><p>{refs}</p>'
                        f'<code>{esc(unit["unit_id"])}</code></details></section>'
                    )

                prev_link = (
                    f'<a href="{scene["scene_number"] - 1}.html">← anterior</a>'
                    if scene["scene_number"] > 1
                    else ""
                )
                next_link = (
                    f'<a href="{scene["scene_number"] + 1}.html">siguiente →</a>'
                    if scene["scene_number"] < len(scenes)
                    else ""
                )
                write(
                    out / f'editions/{eslug}/scene/{scene["scene_number"]}.html',
                    page(
                        "../../../",
                        scene["title"],
                        f'<div class="crumbs"><a href="../index.html">{esc(edition["title"])}</a> '
                        f'/ escena {scene["scene_number"]}</div>'
                        f'<h1>{scene["scene_number"]}. {esc(scene["title"])}</h1>'
                        f'{"".join(blocks)}<p>{prev_link} &nbsp; {next_link}</p>',
                    ),
                )

        # Static target-token pages: translated word/phrase -> one or more canonical Greek tokens.
        for alignment in alignment_rows:
            edition = edition_by_id.get(alignment.get("edition_id"))
            unit = unit_by_id.get(alignment.get("unit_id"))
            if not edition or not unit:
                continue
            unit_text = texts_by_ed.get(edition["edition_id"], {}).get(unit["unit_id"], {})
            text = unit_text.get("text") or ""
            if alignment.get("target_text_sha256") != hashlib.sha256(text.encode("utf-8")).hexdigest():
                continue
            eslug = edition_slug(edition)
            for target in alignment.get("target_tokens", []):
                source_ids = [tid for tid in target.get("source_token_ids", []) if tid in token_by_id]
                if not source_ids:
                    continue
                cards = []
                for tid in source_ids:
                    token = token_by_id[tid]
                    cards.append(
                        '<div class="card">'
                        f'<h2 class="greek"><a href="../../../token/{safe(tid)}.html">{esc(token["surface"])}</a></h2>'
                        '<dl class="analysis">'
                        f'<dt>Lema</dt><dd>{esc(token.get("lemma")) or "—"}</dd>'
                        f'<dt>Strong</dt><dd>{esc(token.get("strongs")) or "—"}</dd>'
                        f'<dt>Morfología</dt><dd>{esc(token.get("morphology_code")) or "—"}</dd>'
                        f'<dt>Glosa</dt><dd>{esc(token.get("gloss")) or "—"}</dd>'
                        "</dl>"
                        f'<code>{esc(tid)}</code></div>'
                    )
                back = (
                    f'../../../editions/{eslug}/scene/{unit["scene_number"]}.html#{esc(unit["unit_id"])}'
                )
                body = (
                    f'<div class="crumbs"><a href="{back}">← volver a la escena</a></div>'
                    f'<h1>{esc(target["surface"])}</h1>'
                    f'<p><span class="badge">{esc(target.get("confidence", "medium"))}</span> '
                    "alineamiento automático contextual con la capa griega.</p>"
                    '<h2>Token(s) griego(s) alineado(s)</h2>'
                    f'{"".join(cards)}'
                    f'<p class="muted">Método: {esc(alignment.get("alignment_method"))} · '
                    f'Modelo: {esc(alignment.get("alignment_model"))}. '
                    "Este enlace es una alineación computacional auditable; no sustituye revisión filológica humana.</p>"
                )
                write(
                    out / f'alignment/{eslug}/{safe(unit["unit_id"])}/{target["index"]}.html',
                    page("../../../", f'{target["surface"]} ↔ griego', body),
                )

        bookcards = "".join(
            f'<a class="card" href="{slug}/index.html"><h2>{BOOK_LABELS[book_code]}</h2></a>'
            for book_code, slug in BOOK_SLUGS.items()
        )
        write(
            out / "source/index.html",
            page("../", "Fuentes", f'<h1>Evangelios · SOURCE</h1><div class="grid">{bookcards}</div>'),
        )

        for book_code, slug in BOOK_SLUGS.items():
            keys = sorted(
                (key for key in verse_tokens if key[0] == book_code),
                key=lambda key: (key[1], key[2]),
            )
            chapter_numbers = sorted(set(key[1] for key in keys))
            body = ""
            for chapter_number in chapter_numbers:
                verses = [key[2] for key in keys if key[1] == chapter_number]
                body += (
                    f'<div class="card"><h2>Capítulo {chapter_number}</h2><p>'
                    + " ".join(
                        f'<a href="{chapter_number}/{verse}.html">{verse}</a>' for verse in verses
                    )
                    + "</p></div>"
                )
            write(
                out / f"source/{slug}/index.html",
                page("../../", BOOK_LABELS[book_code], f'<h1>{BOOK_LABELS[book_code]}</h1>{body}'),
            )

            for _, chapter_number, verse in keys:
                tokens = verse_tokens[(book_code, chapter_number, verse)]
                greek = "".join(token_span("../../../", token) for token in tokens)
                used = []
                seen = set()
                for token in tokens:
                    for hit in reverse.get(token["token_id"], []):
                        key = (hit["scene_number"], hit["unit_id"])
                        if key not in seen:
                            seen.add(key)
                            used.append(hit)
                usage = ""
                for hit in used:
                    links = " · ".join(
                        f'<a href="../../../editions/{edition_slug(e)}/scene/{hit["scene_number"]}.html#'
                        f'{esc(hit["unit_id"])}">{esc(e["language_code"])}</a>'
                        for e in editions
                    )
                    usage += (
                        f'<li>Escena {hit["scene_number"]} · {esc(hit["reference"])} — {links}</li>'
                    )
                write(
                    out / f"source/{slug}/{chapter_number}/{verse}.html",
                    page(
                        "../../../",
                        f"{BOOK_LABELS[book_code]} {chapter_number}:{verse}",
                        f'<h1>{BOOK_LABELS[book_code]} {chapter_number}:{verse}</h1>'
                        f'<div class="card greek">{greek}</div>'
                        f'<div class="card"><h2>Uso en El Relato</h2><ul>'
                        f'{usage or "<li>No utilizado.</li>"}</ul></div>',
                    ),
                )

        for token in source_tokens:
            hits = reverse.get(token["token_id"], [])
            fields = [
                ("Forma", token["surface"]),
                ("Lema", token.get("lemma")),
                ("Strong", token.get("strongs")),
                ("Morfología", token.get("morphology_code")),
                ("Glosa", token.get("gloss")),
                ("Estado", token.get("textual_status")),
                ("Alineación SOURCE", token.get("match_method")),
            ]
            dl = "".join(
                f"<dt>{esc(label)}</dt><dd>{esc(value) or '—'}</dd>" for label, value in fields
            )
            use = ""
            for hit in hits:
                links = " · ".join(
                    f'<a href="../editions/{edition_slug(e)}/scene/{hit["scene_number"]}.html#'
                    f'{esc(hit["unit_id"])}">{esc(e["language_code"])}</a>'
                    for e in editions
                )
                use += f'<li>Escena {hit["scene_number"]} — {links}</li>'

            aligned_translation = ""
            for match in translation_reverse.get(token["token_id"], []):
                edition = edition_by_id.get(match["edition_id"])
                if not edition:
                    continue
                eslug = edition_slug(edition)
                aligned_translation += (
                    f'<li><a href="../alignment/{eslug}/{safe(match["unit_id"])}/'
                    f'{match["token_index"]}.html">{esc(match["surface"])}</a> · '
                    f'{esc(edition["language_code"])} · escena {match["scene_number"]} · '
                    f'{esc(match["confidence"])}</li>'
                )

            write(
                out / "token" / (safe(token["token_id"]) + ".html"),
                page(
                    "../",
                    token["surface"],
                    f'<h1 class="greek">{esc(token["surface"])}</h1>'
                    f'<div class="card analysis"><dl>{dl}</dl><code>{esc(token["token_id"])}</code></div>'
                    f'<div class="card"><h2>Traducciones alineadas</h2><ul>'
                    f'{aligned_translation or "<li>Sin traducción tokenizada alineada.</li>"}</ul></div>'
                    f'<div class="card"><h2>Uso por edición</h2><ul>'
                    f'{use or "<li>No utilizado.</li>"}</ul></div>',
                ),
            )

        write(
            out / "about.html",
            page(
                "",
                "Método",
                "<h1>Método</h1><div class='card'>"
                "<p>BOOK se abre en modo SQLite read-only. El sitio nunca crea, actualiza ni migra "
                "<code>book/el-relato-book.sqlite</code>.</p>"
                "<p>Las ediciones se descubren automáticamente desde la tabla <code>editions</code>; "
                "agregar una traducción a BOOK hace que el siguiente build cree su interfaz web.</p>"
                "<p>Las traducciones pueden incorporar una capa derivada de alineamiento token-a-token "
                "con el griego. Esa capa conserva los IDs canónicos de SOURCE, admite uno-a-varios y "
                "varios-a-uno, registra método/modelo y distingue alineamiento automático de revisión "
                "filológica humana.</p></div>",
            ),
        )

        manifest = {
            "editions": [
                {
                    "edition_id": e["edition_id"],
                    "language_code": e["language_code"],
                    "version": e["version"],
                    "status": e["status"],
                }
                for e in editions
            ],
            "chapters": len(chapters),
            "scenes": len(scenes),
            "units": len(units),
            "source_tokens": len(source_tokens),
            "source_verses": len(verse_tokens),
            "translation_alignment": alignment_summary,
        }
        raw = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        manifest["content_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
        write(out / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

        assert len(scenes) == 120 and len(units) == 4123 and editions
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    finally:
        book.close()
        source.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="build/site")
    args = ap.parse_args()
    out = ROOT / args.output
    if out.exists():
        import shutil
        shutil.rmtree(out)
    build(out)


if __name__ == "__main__":
    main()
