#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import sqlite3
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DB=ROOT/"build/el-relato.sqlite"
BOOKS={"matthew":"Matthew","mark":"Mark","luke":"Luke","john":"John",
       "mateo":"Matthew","marcos":"Mark","lucas":"Luke","juan":"John"}


def ensure_db(path:Path):
    if path.exists():
        return
    subprocess.run(
        [sys.executable,str(ROOT/"scripts/build_query_db.py"),"--output",str(path.relative_to(ROOT))],
        cwd=ROOT,check=True
    )


def parse_ref(value:str):
    value=" ".join(value.strip().split())
    if not value:
        return None
    if ":" not in value:
        return None
    left,verse=value.rsplit(":",1)
    bits=left.rsplit(" ",1)
    if len(bits)!=2:
        return None
    book_raw,chapter=bits
    book=BOOKS.get(book_raw.casefold(),book_raw.title())
    try:
        return book,int(chapter),int(verse)
    except ValueError:
        return None


def q(con,sql,args=()):
    con.row_factory=sqlite3.Row
    return [dict(x) for x in con.execute(sql,args).fetchall()]


def passage_payload(con,book,chapter,verse):
    tokens=q(con,"""
      SELECT position,surface,prefix_before,punctuation_after,textual_status,
             strongs,lemma,morphology_code,gloss,spanish_translation,
             match_method,strong_original_id
      FROM tokens WHERE book=? AND chapter=? AND verse=? ORDER BY position
    """,(book,chapter,verse))
    apparatus=q(con,"""
      SELECT ordinal,location_label,raw_note,readings_json
      FROM edition_apparatus WHERE book=? AND chapter=? AND verse=? ORDER BY ordinal
    """,(book,chapter,verse))
    pid=f"passage:{book.lower()}:{chapter}:{verse}"
    evidence=q(con,"""
      SELECT passage_id,manuscript_id,manuscript_label,ga_id,status,
             image_ids_json,transcription_ids_json,primary_source
      FROM passage_evidence WHERE passage_id=? ORDER BY manuscript_id
    """,(pid,))
    transcriptions=q(con,"""
      SELECT manuscript_id,transcription_id,layer,text,source_id
      FROM verse_transcriptions WHERE book=? AND chapter=? AND verse=?
      ORDER BY manuscript_id
    """,(book,chapter,verse))
    return {
      "reference":f"{book} {chapter}:{verse}",
      "tokens":tokens,
      "apparatus":apparatus,
      "evidence":evidence,
      "transcriptions":transcriptions,
    }


def strong_payload(con,strong):
    strong=strong.upper().strip()
    if strong.startswith("G") and strong[1:].isdigit():
        strong="G"+strong[1:].zfill(4)
    occurrences=q(con,"""
      SELECT book,chapter,verse,position,surface,lemma,gloss,morphology_code
      FROM token_analysis WHERE strongs LIKE ? ORDER BY
      CASE book WHEN 'Matthew' THEN 1 WHEN 'Mark' THEN 2 WHEN 'Luke' THEN 3 ELSE 4 END,
      chapter,verse,position
    """,(strong+"%",))
    original=q(con,"SELECT * FROM strong_original WHERE strong_id=?",(strong,))
    extended=q(con,"SELECT * FROM strong_extended WHERE e_strong=? OR d_strong_id=?",(strong,strong))
    return {"strong":strong,"occurrences":occurrences,"original":original,"extended":extended}


CSS="""
body{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#f7f4ee;color:#1d1d1b}
header{background:#1d1d1b;color:white;padding:18px 28px}
main{max-width:1180px;margin:auto;padding:24px}
form{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 24px}
input{font-size:16px;padding:10px 12px;min-width:280px}
button{padding:10px 16px;font-weight:600}
.card{background:white;border:1px solid #ddd7cb;border-radius:10px;padding:16px;margin:12px 0}
.greek{font-family:'Times New Roman',serif;font-size:22px;line-height:1.65}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;border-bottom:1px solid #eee7dc;padding:7px;vertical-align:top}
.muted{color:#6e6a63;font-size:13px}
.badge{display:inline-block;border:1px solid #bbb;padding:2px 6px;border-radius:8px;font-size:12px}
a{color:#284e7a}
code{background:#eee9df;padding:2px 4px;border-radius:4px}
"""


def page(title,body):
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
    <title>{html.escape(title)} — El-Relato</title><style>{CSS}</style></head>
    <body><header><b>El-Relato</b> · Corpus privado de los cuatro Evangelios</header>
    <main>{body}</main></body></html>"""


def render_home():
    return page("Inicio","""
    <h1>Investigación textual de los Evangelios</h1>
    <p>Consulta el corpus preservado desde texto griego hasta evidencia manuscrita.</p>
    <div class="card"><h2>Por pasaje</h2>
      <form action="/passage"><input name="ref" placeholder="Juan 1:1 / John 1:1"><button>Buscar</button></form>
    </div>
    <div class="card"><h2>Por Strong</h2>
      <form action="/strong"><input name="id" placeholder="G0746"><button>Buscar</button></form>
    </div>
    """)


def strong_links(value:str):
    ids=[]
    for raw in (value or "").replace(","," ").replace(";"," ").split():
        token=raw.strip().upper()
        if token.startswith("G") and token[1:].isdigit():
            token="G"+token[1:].zfill(4)
            if token not in ids: ids.append(token)
    if not ids: return html.escape(value or "")
    return " ".join(f"<a class='strong-link' href='/strong?id={urllib.parse.quote(x)}' title='Ver significado y apariciones'>{html.escape(x)}</a>" for x in ids)


def brief_definition(original:dict):
    raw=(original.get("strongs_definition") or original.get("definition") or original.get("gloss") or "").strip()
    if not raw: return "Definición resumida no disponible en la fuente léxica local."
    first=raw.split(";")[0].strip()
    return first if len(first)<=220 else first[:217].rsplit(" ",1)[0]+"…"


def render_passage(payload):
    toks=payload["tokens"]
    greek=" ".join(
      (x.get("prefix_before") or "")+x["surface"]+(x.get("punctuation_after") or "")
      for x in toks
    )
    rows="".join(
      f"<tr><td>{x['position']}</td><td class='greek'>{html.escape(x['surface'])}</td>"
      f"<td>{strong_links(x.get('strongs') or '')}</td><td class='greek'>{html.escape(x.get('lemma') or '')}</td>"
      f"<td>{html.escape(x.get('morphology_code') or '')}</td><td>{html.escape(x.get('gloss') or '')}</td>"
      f"<td>{html.escape(x.get('spanish_translation') or '')}</td>"
      f"<td><span class='badge'>{html.escape(x.get('textual_status') or '')}</span></td></tr>"
      for x in toks
    )
    ev="".join(
      f"<li><b>{html.escape(x.get('manuscript_label') or x['manuscript_id'])}</b> "
      f"({html.escape(x.get('ga_id') or '')}) — {html.escape(x.get('status') or '')}"
      f" · <code>{html.escape(x.get('image_ids_json') or '[]')}</code></li>"
      for x in payload["evidence"]
    ) or "<li>Sin evidencia manuscrita mapeada todavía.</li>"
    tx="".join(
      f"<div class='card'><b>{html.escape(x['manuscript_id'])}</b><div class='greek'>{html.escape(x.get('text') or '')}</div></div>"
      for x in payload["transcriptions"]
    )
    app="".join(
      f"<li>{html.escape(x['raw_note'])}</li>" for x in payload["apparatus"]
    ) or "<li>Sin nota de aparato de ediciones para este versículo.</li>"
    return page(payload["reference"],f"""
      <h1>{html.escape(payload['reference'])}</h1>
      <div class="card greek">{html.escape(greek)}</div>
      <h2>Palabra por palabra</h2>
      <div class="card"><table><thead><tr><th>#</th><th>Griego</th><th>Strong</th><th>Lema</th><th>Morf.</th><th>Glosa</th><th>Español</th><th>Estado</th></tr></thead><tbody>{rows}</tbody></table></div>
      <h2>Evidencia manuscrita</h2><div class="card"><ul>{ev}</ul></div>
      <h2>Transcripciones</h2>{tx or '<div class="card">Sin transcripción normalizada mapeada todavía.</div>'}
      <h2>Aparato entre ediciones</h2><div class="card"><ul>{app}</ul></div>
      <p><a href="/">← Inicio</a></p>
    """)


def render_strong(payload):
    occ="".join(
      f"<tr><td>{html.escape(x['book'])} {x['chapter']}:{x['verse']}</td><td class='greek'>{html.escape(x['surface'])}</td>"
      f"<td class='greek'>{html.escape(x.get('lemma') or '')}</td><td>{html.escape(x.get('morphology_code') or '')}</td>"
      f"<td>{html.escape(x.get('gloss') or '')}</td></tr>"
      for x in payload["occurrences"]
    )
    original=payload["original"][0] if payload["original"] else {}
    definition=html.escape(original.get("strongs_definition") or "")
    return page(payload["strong"],f"""
      <h1>{html.escape(payload['strong'])}</h1>
      <div class="card"><b>Strong histórico:</b> <span class="greek">{html.escape(original.get('lemma') or '')}</span>
      — {definition}</div>
      <p>{len(payload['occurrences'])} ocurrencias enlazadas en los cuatro Evangelios.</p>
      <div class="card"><table><thead><tr><th>Pasaje</th><th>Forma</th><th>Lema</th><th>Morf.</th><th>Glosa</th></tr></thead><tbody>{occ}</tbody></table></div>
      <p><a href="/">← Inicio</a></p>
    """)


class Handler(BaseHTTPRequestHandler):
    db_path=DEFAULT_DB

    def send_html(self,content,status=200):
        data=content.encode()
        self.send_response(status); self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)

    def send_json(self,obj,status=200):
        data=(json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode()
        self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        u=urllib.parse.urlparse(self.path)
        params=urllib.parse.parse_qs(u.query)
        con=sqlite3.connect(self.db_path)
        try:
            if u.path=="/":
                return self.send_html(render_home())
            if u.path in ("/passage","/api/passage"):
                ref=parse_ref((params.get("ref") or [""])[0])
                if not ref:
                    return self.send_json({"error":"Referencia inválida"},400) if u.path.startswith("/api") else self.send_html(page("Error","<h1>Referencia inválida</h1>"),400)
                payload=passage_payload(con,*ref)
                return self.send_json(payload) if u.path.startswith("/api") else self.send_html(render_passage(payload))
            if u.path in ("/strong","/api/strong"):
                ident=(params.get("id") or [""])[0]
                payload=strong_payload(con,ident)
                return self.send_json(payload) if u.path.startswith("/api") else self.send_html(render_strong(payload))
            return self.send_html(page("404","<h1>No encontrado</h1>"),404)
        finally:
            con.close()

    def log_message(self,fmt,*args):
        sys.stderr.write("[El-Relato] "+fmt%args+"\n")


def self_test(db):
    con=sqlite3.connect(db)
    p=passage_payload(con,"John",1,1)
    assert len(p["tokens"])==17
    assert any(x["manuscript_id"]=="ms:ga:01" for x in p["transcriptions"])
    p52=passage_payload(con,"John",18,37)
    assert any(x["manuscript_id"]=="ms:ga:p52" for x in p52["evidence"])
    st=strong_payload(con,"G0746")
    assert st["occurrences"]
    con.close()
    print("EL-RELATO APP SELF-TEST OK")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db",default=str(DEFAULT_DB))
    ap.add_argument("--host",default="127.0.0.1")
    ap.add_argument("--port",type=int,default=8765)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    db=Path(args.db)
    ensure_db(db)
    if args.self_test:
        return self_test(db)
    Handler.db_path=db
    print(f"El-Relato: http://{args.host}:{args.port}")
    ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()


if __name__=="__main__":
    main()
