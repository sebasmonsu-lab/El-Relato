#!/usr/bin/env python3
"""Build the public, static El Relato research site from canonical BOOK + SOURCE data."""
from __future__ import annotations
import argparse, hashlib, html, json, re, sqlite3, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BOOK_DB=ROOT/"book/el-relato-book.sqlite"
QUERY_DB=ROOT/"build/el-relato.sqlite"
EDITION="edition:el-relato:grc-sblgnt-2010:v1"
BOOK_SLUGS={"Matthew":"matthew","Mark":"mark","Luke":"luke","John":"john"}
BOOK_LABELS={"Matthew":"Mateo","Mark":"Marcos","Luke":"Lucas","John":"Juan"}

CSS="""*{box-sizing:border-box}body{margin:0;background:#f6f3ec;color:#211f1a;font-family:system-ui,-apple-system,sans-serif}
header{position:sticky;top:0;z-index:5;background:#1d1d1b;color:#fff;padding:14px 5vw;display:flex;gap:20px;align-items:center;flex-wrap:wrap}
header a{color:#fff;text-decoration:none}nav{display:flex;gap:14px}main{max-width:1120px;margin:auto;padding:30px 22px 70px}
a{color:#315d85}.hero{padding:38px 0 20px}.card{background:#fff;border:1px solid #ddd6c8;border-radius:12px;padding:18px;margin:14px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.muted{color:#716c62}.greek{font-family:Georgia,'Times New Roman',serif;font-size:1.35rem;line-height:1.9}
.token{display:inline-block;padding:0 2px;border-radius:4px;text-decoration:none;color:#202b35}.token:hover{background:#e9dfca}.ref{font-size:.9rem}
.badge{display:inline-block;border:1px solid #c9c0b0;border-radius:999px;padding:2px 8px;font-size:.78rem;margin:2px}
.unit{border-left:3px solid #d6c6a5;padding-left:14px;margin:18px 0}.crumbs{font-size:.9rem;margin-bottom:22px}.analysis dt{font-weight:700}.analysis dd{margin:0 0 10px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid #eee8dc;vertical-align:top}
input{padding:10px 12px;font-size:1rem;min-width:260px}button{padding:10px 14px}code{overflow-wrap:anywhere}
@media(max-width:600px){.greek{font-size:1.18rem}header{position:static}}"""

def esc(x): return html.escape(str(x or ""))
def safe(s): return re.sub(r"[^A-Za-z0-9._-]+","-",str(s)).strip("-").lower()
def q(con,sql,args=()):
    con.row_factory=sqlite3.Row
    return [dict(r) for r in con.execute(sql,args).fetchall()]
def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding="utf-8")
def page(root,title,body):
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · El Relato</title><style>{CSS}</style></head><body>
<header><a href="{root}index.html"><strong>El Relato</strong></a><nav><a href="{root}edition/index.html">Libro</a><a href="{root}source/index.html">Fuentes</a><a href="{root}about.html">Método</a></nav></header>
<main>{body}</main></body></html>"""
def token_href(root,token_id): return root+"token/"+safe(token_id)+".html"
def source_href(root,book,ch,v): return f"{root}source/{BOOK_SLUGS[book]}/{ch}/{v}.html"
def scene_href(root,n): return f"{root}edition/scene/{n}.html"

def token_span(root,t):
    tid=t.get("token_id") or t.get("id")
    surface=esc(t.get("surface"))
    punct=esc(t.get("punctuation_after"))
    prefix=esc(t.get("prefix_before"))
    if tid:
        return prefix+f'<a class="token" href="{token_href(root,tid)}" title="{esc(t.get("strongs") or "")}">{surface}</a>'+punct
    return prefix+surface+punct

def build(out):
    if not BOOK_DB.exists(): raise SystemExit("Missing book/el-relato-book.sqlite")
    if not QUERY_DB.exists():
        subprocess.run([sys.executable,str(ROOT/"scripts/build_query_db.py"),"--output","build/el-relato.sqlite"],cwd=ROOT,check=True)
    b=sqlite3.connect(BOOK_DB); s=sqlite3.connect(QUERY_DB)
    chapters=q(b,"select * from chapters order by chapter_order")
    scenes=q(b,"select * from scenes order by scene_number")
    units=q(b,"select * from units order by global_order")
    texts={r["unit_id"]:r for r in q(b,"select * from unit_texts where edition_id=?",(EDITION,))}
    witnesses={}
    for r in q(b,"select * from unit_witnesses order by unit_id,witness_order"):
        witnesses.setdefault(r["unit_id"],[]).append(r)
    scene_units={}
    for u in units: scene_units.setdefault(u["scene_number"],[]).append(u)
    source_tokens=q(s,"select * from tokens order by case book when 'Matthew' then 1 when 'Mark' then 2 when 'Luke' then 3 else 4 end,chapter,verse,position")
    token_by_id={t["token_id"]:t for t in source_tokens}
    verse_tokens={}
    for t in source_tokens: verse_tokens.setdefault((t["book"],t["chapter"],t["verse"]),[]).append(t)

    # Reverse index from source token/passages to editorial units/scenes.
    reverse={}
    for uid,ws in witnesses.items():
        u=next((x for x in units if x["unit_id"]==uid),None)
        if not u: continue
        for w in ws:
            ids=json.loads(w.get("source_token_ids_json") or "[]")
            for tid in ids:
                reverse.setdefault(tid,[]).append({"unit_id":uid,"scene_number":u["scene_number"],"reference":w["reference_component"],"primary":w["witness_order"]==1})

    # Home.
    write(out/"index.html",page("","Inicio",f"""<section class="hero"><h1>El Relato</h1><p>Una edición navegable y trazable de la narración de los cuatro Evangelios.</p></section>
<div class="grid"><a class="card" href="edition/index.html"><h2>Leer El Relato</h2><p>6 capítulos · 120 escenas · 4.123 unidades editoriales.</p></a>
<a class="card" href="source/index.html"><h2>Explorar las fuentes</h2><p>Mateo, Marcos, Lucas y Juan, palabra por palabra.</p></a></div>
<div class="card"><h2>Principio de trazabilidad</h2><p>Libro → unidad → token → texto fuente → Strong/lema/morfología → evidencia. Y también en sentido inverso.</p></div>"""))

    # Edition index + chapter pages.
    by_chapter={}
    for sc in scenes: by_chapter.setdefault(sc["chapter_number"],[]).append(sc)
    cards=""
    for ch in chapters:
        cards+=f'<div class="card"><h2>Capítulo {esc(ch["chapter_number"])} · {esc(ch["title"])}</h2><ol>'
        for sc in by_chapter.get(ch["chapter_number"],[]): cards+=f'<li><a href="scene/{sc["scene_number"]}.html">{sc["scene_number"]}. {esc(sc["title"])}</a></li>'
        cards+="</ol></div>"
    write(out/"edition/index.html",page("../","Edición griega",f'<h1>El Relato · edición griega V1</h1><p class="muted"><code>{EDITION}</code></p>{cards}'))

    # Scene pages.
    for sc in scenes:
        blocks=[]
        for u in scene_units.get(sc["scene_number"],[]):
            ut=texts.get(u["unit_id"],{})
            ws=witnesses.get(u["unit_id"],[])
            primary=next((x for x in ws if x["witness_id"]==ut.get("source_witness_id")),ws[0] if ws else None)
            tids=json.loads(primary.get("source_token_ids_json") or "[]") if primary else []
            toks=[token_by_id[x] for x in tids if x in token_by_id]
            greek="".join(token_span("../../",t) for t in toks) if toks else esc(ut.get("text"))
            refs=" · ".join(esc(x["reference_component"]) for x in ws)
            source_link=""
            if primary and primary["book_code"] in BOOK_SLUGS:
                source_link=f' · <a href="../../source/{BOOK_SLUGS[primary["book_code"]]}/{primary["chapter"]}/{primary["verse_start"]}.html">ver fuente</a>'
            blocks.append(f'<section class="unit" id="{esc(u["unit_id"])}"><div class="ref"><strong>{esc(u["reference_raw"])}</strong>{source_link}</div><div class="greek">{greek}</div><details><summary>Provenance y referencias paralelas</summary><p>{refs}</p><code>{esc(u["unit_id"])}</code></details></section>')
        prev=f'<a href="{sc["scene_number"]-1}.html">← escena anterior</a>' if sc["scene_number"]>1 else ""
        nxt=f'<a href="{sc["scene_number"]+1}.html">escena siguiente →</a>' if sc["scene_number"]<120 else ""
        body=f'<div class="crumbs"><a href="../index.html">Edición</a> / escena {sc["scene_number"]}</div><h1>{sc["scene_number"]}. {esc(sc["title"])}</h1>{"".join(blocks)}<p>{prev} &nbsp; {nxt}</p>'
        write(out/f'edition/scene/{sc["scene_number"]}.html',page("../../",sc["title"],body))

    # Source index.
    book_cards="".join(f'<a class="card" href="{slug}/index.html"><h2>{BOOK_LABELS[b]}</h2><p>Texto griego, tokens y análisis.</p></a>' for b,slug in BOOK_SLUGS.items())
    write(out/"source/index.html",page("../","Fuentes",f'<h1>Evangelios · SOURCE browser</h1><p>La capa fuente se mantiene separada de la composición editorial.</p><div class="grid">{book_cards}</div>'))

    # Source books + verse pages.
    for book,slug in BOOK_SLUGS.items():
        keys=sorted([k for k in verse_tokens if k[0]==book],key=lambda x:(x[1],x[2]))
        chapters_n=sorted(set(k[1] for k in keys))
        chhtml=""
        for ch in chapters_n:
            verses=[k[2] for k in keys if k[1]==ch]
            chhtml+=f'<div class="card"><h2>Capítulo {ch}</h2><p>'+ " ".join(f'<a href="{ch}/{v}.html">{v}</a>' for v in verses)+"</p></div>"
        write(out/f"source/{slug}/index.html",page("../../",BOOK_LABELS[book],f'<h1>{BOOK_LABELS[book]}</h1>{chhtml}'))
        for _,ch,v in keys:
            toks=verse_tokens[(book,ch,v)]
            greek="".join(token_span("../../../",t) for t in toks)
            used=[]
            seen=set()
            for t in toks:
                for hit in reverse.get(t["token_id"],[]):
                    key=(hit["scene_number"],hit["unit_id"])
                    if key not in seen: seen.add(key); used.append(hit)
            usage="".join(f'<li><a href="../../../edition/scene/{x["scene_number"]}.html#{esc(x["unit_id"])}">Escena {x["scene_number"]}</a> · {esc(x["reference"])}</li>' for x in used) or "<li>No utilizado en la composición actual.</li>"
            body=f'<div class="crumbs"><a href="../index.html">{BOOK_LABELS[book]}</a> / {ch}:{v}</div><h1>{BOOK_LABELS[book]} {ch}:{v}</h1><div class="card greek">{greek}</div><div class="card"><h2>Uso en El Relato</h2><ul>{usage}</ul></div>'
            write(out/f"source/{slug}/{ch}/{v}.html",page("../../../",f"{BOOK_LABELS[book]} {ch}:{v}",body))

    # Token pages.
    for t in source_tokens:
        hits=reverse.get(t["token_id"],[])
        strong=t.get("strongs") or ""
        use="".join(f'<li><a href="../edition/scene/{x["scene_number"]}.html#{esc(x["unit_id"])}">Escena {x["scene_number"]}</a> · {esc(x["reference"])}</li>' for x in hits) or "<li>No utilizado en El Relato.</li>"
        fields=[("Forma",t["surface"]),("Lema",t.get("lemma")),("Strong",strong),("Morfología",t.get("morphology_code")),("Glosa",t.get("gloss")),("Traducción auxiliar",t.get("spanish_translation")),("Estado textual",t.get("textual_status")),("Alineación",t.get("match_method"))]
        dl="".join(f"<dt>{esc(k)}</dt><dd>{esc(v) or '—'}</dd>" for k,v in fields)
        ref=f'{BOOK_LABELS[t["book"]]} {t["chapter"]}:{t["verse"]}'
        body=f'<div class="crumbs"><a href="{source_href("../",t["book"],t["chapter"],t["verse"])}">{ref}</a></div><h1 class="greek">{esc(t["surface"])}</h1><div class="card analysis"><dl>{dl}</dl><code>{esc(t["token_id"])}</code></div><div class="card"><h2>Uso en El Relato</h2><ul>{use}</ul></div>'
        write(out/"token"/(safe(t["token_id"])+".html"),page("../",t["surface"],body))

    write(out/"about.html",page("","Método","""<h1>Método</h1><div class="card"><p>El sitio es un artefacto derivado de las bases BOOK y SOURCE. El texto editorial, los identificadores de token y la provenance se generan de forma reproducible.</p><p>Las fuentes preservadas, las normalizaciones y los derivados editoriales son capas distintas. La publicación de facsímiles y otros recursos depende de su política de licencia.</p></div>"""))

    manifest={"edition_id":EDITION,"chapters":len(chapters),"scenes":len(scenes),"units":len(units),"source_tokens":len(source_tokens),"source_verses":len(verse_tokens),"reverse_index_tokens":len(reverse)}
    payload=json.dumps(manifest,ensure_ascii=False,indent=2)+"\n"
    manifest["content_sha256"]=hashlib.sha256(payload.encode()).hexdigest()
    write(out/"manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    b.close(); s.close()
    assert len(scenes)==120 and len(units)==4123
    assert (out/"edition/scene/120.html").exists()
    assert (out/"source/john/1/1.html").exists()
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="build/site")
    a=ap.parse_args(); out=ROOT/a.output
    if out.exists():
        import shutil; shutil.rmtree(out)
    build(out)

if __name__=="__main__": main()
