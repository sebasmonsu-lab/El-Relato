#!/usr/bin/env python3
"""Build El Relato public static site. BOOK DB is strictly read-only."""
from __future__ import annotations
import argparse, hashlib, html, json, re, sqlite3, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BOOK_DB=ROOT/"book/el-relato-book.sqlite"; QUERY_DB=ROOT/"build/el-relato.sqlite"
BOOK_SLUGS={"Matthew":"matthew","Mark":"mark","Luke":"luke","John":"john"}
BOOK_LABELS={"Matthew":"Mateo","Mark":"Marcos","Luke":"Lucas","John":"Juan"}
CSS="""*{box-sizing:border-box}body{margin:0;background:#f6f3ec;color:#211f1a;font-family:system-ui,-apple-system,sans-serif}header{position:sticky;top:0;z-index:5;background:#1d1d1b;color:#fff;padding:14px 5vw;display:flex;gap:20px;align-items:center;flex-wrap:wrap}header a{color:#fff;text-decoration:none}nav{display:flex;gap:14px}main{max-width:1120px;margin:auto;padding:30px 22px 70px}a{color:#315d85}.hero{padding:38px 0 20px}.card{background:#fff;border:1px solid #ddd6c8;border-radius:12px;padding:18px;margin:14px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.muted{color:#716c62}.greek{font-family:Georgia,'Times New Roman',serif;font-size:1.35rem;line-height:1.9}.text{font-size:1.12rem;line-height:1.75}.token{display:inline-block;padding:0 2px;border-radius:4px;text-decoration:none;color:#202b35}.token:hover{background:#e9dfca}.ref{font-size:.9rem}.badge{display:inline-block;border:1px solid #c9c0b0;border-radius:999px;padding:2px 8px;font-size:.78rem;margin:2px}.unit{border-left:3px solid #d6c6a5;padding-left:14px;margin:18px 0}.crumbs{font-size:.9rem;margin-bottom:22px}.analysis dt{font-weight:700}.analysis dd{margin:0 0 10px}code{overflow-wrap:anywhere}@media(max-width:600px){.greek{font-size:1.18rem}header{position:static}}"""
def esc(x): return html.escape(str(x or ""))
def safe(s): return re.sub(r"[^A-Za-z0-9._-]+","-",str(s)).strip("-").lower()
def q(c,sql,args=()): c.row_factory=sqlite3.Row; return [dict(r) for r in c.execute(sql,args).fetchall()]
def write(p,t): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(t,encoding="utf-8")
def page(root,title,body): return f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · El Relato</title><style>{CSS}</style></head><body><header><a href="{root}index.html"><strong>El Relato</strong></a><nav><a href="{root}editions/index.html">Ediciones</a><a href="{root}source/index.html">Fuentes</a><a href="{root}about.html">Método</a></nav></header><main>{body}</main></body></html>'
def token_span(root,t):
    tid=t.get("token_id"); s=esc(t.get("surface")); pre=esc(t.get("prefix_before")); post=esc(t.get("punctuation_after"))
    return pre+(f'<a class="token" href="{root}token/{safe(tid)}.html" title="{esc(t.get("strongs"))}">{s}</a>' if tid else s)+post
def edition_slug(e): return safe(e["edition_id"])
def connect_ro(path): return sqlite3.connect(f"file:{path.as_posix()}?mode=ro",uri=True)

def build(out):
    if not BOOK_DB.exists(): raise SystemExit("Missing canonical BOOK DB")
    if not QUERY_DB.exists(): subprocess.run([sys.executable,str(ROOT/"scripts/build_query_db.py"),"--output","build/el-relato.sqlite"],cwd=ROOT,check=True)
    b=connect_ro(BOOK_DB); s=connect_ro(QUERY_DB)
    chapters=q(b,"select * from chapters order by chapter_order"); scenes=q(b,"select * from scenes order by scene_number"); units=q(b,"select * from units order by global_order")
    editions=q(b,"select * from editions order by created_at, edition_id")
    all_texts=q(b,"select * from unit_texts")
    texts_by_ed={}
    for r in all_texts: texts_by_ed.setdefault(r["edition_id"],{})[r["unit_id"]]=r
    witnesses={}
    for r in q(b,"select * from unit_witnesses order by unit_id,witness_order"): witnesses.setdefault(r["unit_id"],[]).append(r)
    scene_units={}
    unit_by_id={u["unit_id"]:u for u in units}
    for u in units: scene_units.setdefault(u["scene_number"],[]).append(u)
    source_tokens=q(s,"select * from tokens order by case book when 'Matthew' then 1 when 'Mark' then 2 when 'Luke' then 3 else 4 end,chapter,verse,position")
    token_by_id={t["token_id"]:t for t in source_tokens}; verse_tokens={}
    for t in source_tokens: verse_tokens.setdefault((t["book"],t["chapter"],t["verse"]),[]).append(t)
    reverse={}
    for uid,ws in witnesses.items():
        u=unit_by_id.get(uid)
        if not u: continue
        for w in ws:
            for tid in json.loads(w.get("source_token_ids_json") or "[]"):
                reverse.setdefault(tid,[]).append({"unit_id":uid,"scene_number":u["scene_number"],"reference":w["reference_component"]})

    edcards="".join(f'<a class="card" href="editions/{edition_slug(e)}/index.html"><h2>{esc(e["title"])}</h2><p>{esc(e["language_code"])} · {esc(e["version"])} · {esc(e["status"])}</p></a>' for e in editions)
    write(out/"index.html",page("","Inicio",f'<section class="hero"><h1>El Relato</h1><p>Libro multilingüe y herramienta de investigación trazable de los cuatro Evangelios.</p></section><h2>Ediciones disponibles</h2><div class="grid">{edcards}</div><a class="card" href="source/index.html"><h2>Explorar SOURCE</h2><p>Mateo, Marcos, Lucas y Juan palabra por palabra.</p></a>'))
    write(out/"editions/index.html",page("../","Ediciones",f'<h1>Ediciones</h1><div class="grid">{edcards.replace("editions/","")}</div>'))

    for e in editions:
        eslug=edition_slug(e); texts=texts_by_ed.get(e["edition_id"],{})
        by_ch={}
        for sc in scenes: by_ch.setdefault(sc["chapter_number"],[]).append(sc)
        cards=""
        for ch in chapters:
            cards+=f'<div class="card"><h2>Capítulo {esc(ch["chapter_number"])} · {esc(ch["title"])}</h2><ol>'
            cards+="".join(f'<li><a href="scene/{sc["scene_number"]}.html">{sc["scene_number"]}. {esc(sc["title"])}</a></li>' for sc in by_ch.get(ch["chapter_number"],[]))+"</ol></div>"
        write(out/f"editions/{eslug}/index.html",page("../../",e["title"],f'<h1>{esc(e["title"])}</h1><p><span class="badge">{esc(e["language_code"])}</span> <span class="badge">{esc(e["version"])}</span> <span class="badge">{esc(e["status"])}</span></p><p class="muted"><code>{esc(e["edition_id"])}</code></p>{cards}'))
        is_greek=e["language_code"] in ("grc","el","gr")
        for sc in scenes:
            blocks=[]
            for u in scene_units.get(sc["scene_number"],[]):
                ut=texts.get(u["unit_id"],{}); ws=witnesses.get(u["unit_id"],[])
                primary=next((x for x in ws if x["witness_id"]==ut.get("source_witness_id")),ws[0] if ws else None)
                tids=json.loads(primary.get("source_token_ids_json") or "[]") if primary else []
                toks=[token_by_id[x] for x in tids if x in token_by_id]
                # Greek source editions get token-level rendering. Translations preserve their authored unit text and link the unit to Greek evidence.
                rendered="".join(token_span("../../../",t) for t in toks) if is_greek and toks else esc(ut.get("text"))
                klass="greek" if is_greek else "text"
                source_link=f' · <a href="../../../source/{BOOK_SLUGS[primary["book_code"]]}/{primary["chapter"]}/{primary["verse_start"]}.html">fuente griega</a>' if primary and primary["book_code"] in BOOK_SLUGS else ""
                refs=" · ".join(esc(x["reference_component"]) for x in ws)
                blocks.append(f'<section class="unit" id="{esc(u["unit_id"])}"><div class="ref"><strong>{esc(u["reference_raw"])}</strong>{source_link}</div><div class="{klass}">{rendered}</div><details><summary>Trazabilidad</summary><p>{refs}</p><code>{esc(u["unit_id"])}</code></details></section>')
            prev=f'<a href="{sc["scene_number"]-1}.html">← anterior</a>' if sc["scene_number"]>1 else ""; nxt=f'<a href="{sc["scene_number"]+1}.html">siguiente →</a>' if sc["scene_number"]<len(scenes) else ""
            write(out/f'editions/{eslug}/scene/{sc["scene_number"]}.html',page("../../../",sc["title"],f'<div class="crumbs"><a href="../index.html">{esc(e["title"])}</a> / escena {sc["scene_number"]}</div><h1>{sc["scene_number"]}. {esc(sc["title"])}</h1>{"".join(blocks)}<p>{prev} &nbsp; {nxt}</p>'))

    bookcards="".join(f'<a class="card" href="{slug}/index.html"><h2>{BOOK_LABELS[b]}</h2></a>' for b,slug in BOOK_SLUGS.items())
    write(out/"source/index.html",page("../","Fuentes",f'<h1>Evangelios · SOURCE</h1><div class="grid">{bookcards}</div>'))
    for book,slug in BOOK_SLUGS.items():
        keys=sorted((k for k in verse_tokens if k[0]==book),key=lambda x:(x[1],x[2])); chs=sorted(set(k[1] for k in keys)); h=""
        for ch in chs:
            vs=[k[2] for k in keys if k[1]==ch]; h+=f'<div class="card"><h2>Capítulo {ch}</h2><p>'+" ".join(f'<a href="{ch}/{v}.html">{v}</a>' for v in vs)+"</p></div>"
        write(out/f"source/{slug}/index.html",page("../../",BOOK_LABELS[book],f'<h1>{BOOK_LABELS[book]}</h1>{h}'))
        for _,ch,v in keys:
            toks=verse_tokens[(book,ch,v)]; greek="".join(token_span("../../../",t) for t in toks); used=[]; seen=set()
            for t in toks:
                for hit in reverse.get(t["token_id"],[]):
                    key=(hit["scene_number"],hit["unit_id"])
                    if key not in seen: seen.add(key); used.append(hit)
            # Link a source hit to every edition so translations automatically participate.
            usage=""
            for hit in used:
                links=" · ".join(f'<a href="../../../editions/{edition_slug(e)}/scene/{hit["scene_number"]}.html#{esc(hit["unit_id"])}">{esc(e["language_code"])}</a>' for e in editions)
                usage+=f'<li>Escena {hit["scene_number"]} · {esc(hit["reference"])} — {links}</li>'
            write(out/f"source/{slug}/{ch}/{v}.html",page("../../../",f"{BOOK_LABELS[book]} {ch}:{v}",f'<h1>{BOOK_LABELS[book]} {ch}:{v}</h1><div class="card greek">{greek}</div><div class="card"><h2>Uso en El Relato</h2><ul>{usage or "<li>No utilizado.</li>"}</ul></div>'))
    for t in source_tokens:
        hits=reverse.get(t["token_id"],[]); fields=[("Forma",t["surface"]),("Lema",t.get("lemma")),("Strong",t.get("strongs")),("Morfología",t.get("morphology_code")),("Glosa",t.get("gloss")),("Estado",t.get("textual_status")),("Alineación",t.get("match_method"))]
        dl="".join(f"<dt>{esc(k)}</dt><dd>{esc(v) or '—'}</dd>" for k,v in fields); use=""
        for x in hits:
            links=" · ".join(f'<a href="../editions/{edition_slug(e)}/scene/{x["scene_number"]}.html#{esc(x["unit_id"])}">{esc(e["language_code"])}</a>' for e in editions)
            use+=f'<li>Escena {x["scene_number"]} — {links}</li>'
        write(out/"token"/(safe(t["token_id"])+".html"),page("../",t["surface"],f'<h1 class="greek">{esc(t["surface"])}</h1><div class="card analysis"><dl>{dl}</dl><code>{esc(t["token_id"])}</code></div><div class="card"><h2>Uso por edición</h2><ul>{use or "<li>No utilizado.</li>"}</ul></div>'))
    write(out/"about.html",page("","Método","<h1>Método</h1><div class='card'><p>BOOK se abre en modo SQLite read-only. El sitio nunca crea, actualiza ni migra <code>book/el-relato-book.sqlite</code>.</p><p>Las ediciones se descubren automáticamente desde la tabla <code>editions</code>; agregar una traducción a BOOK hace que el siguiente build cree su interfaz web.</p></div>"))
    manifest={"editions":[{"edition_id":e["edition_id"],"language_code":e["language_code"],"version":e["version"],"status":e["status"]} for e in editions],"chapters":len(chapters),"scenes":len(scenes),"units":len(units),"source_tokens":len(source_tokens),"source_verses":len(verse_tokens)}
    raw=json.dumps(manifest,ensure_ascii=False,sort_keys=True); manifest["content_sha256"]=hashlib.sha256(raw.encode()).hexdigest(); write(out/"manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    b.close(); s.close(); assert len(scenes)==120 and len(units)==4123 and editions
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default="build/site"); a=ap.parse_args(); out=ROOT/a.output
    if out.exists(): import shutil; shutil.rmtree(out)
    build(out)
if __name__=="__main__": main()
