#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK_DB = ROOT / "book/el-relato-book.sqlite"
SBL_VERSES = ROOT / "data/normalized/sblgnt/edition-verses.jsonl"
BASE_BOOK_EDITION = "edition:el-relato:grc-sblgnt-2010:v1"
BASE_GOSPEL_EDITION = "edition:gospels:grc-sblgnt-2010:v1"
API_URL = "https://models.github.ai/inference/chat/completions"

TARGETS = {
    "es-419": {
        "language_code": "es", "locale": "es-419", "slug": "es-419-v1",
        "book_slug": "tk-es-419-v1",
        "book_edition_id": "edition:el-relato:tk-es-419:v1",
        "book_title": "El Relato — Español Latinoamericano IA V1",
        "gospel_edition_id": "edition:gospels:es-419:v1",
        "gospel_title": "Evangelios — Español Latinoamericano IA V1",
        "style": "español latinoamericano contemporáneo, natural para México, Colombia y comunidades hispanohablantes de Estados Unidos; usa ustedes, evita voseo, españolismos y arcaísmos innecesarios",
    },
    "en": {
        "language_code": "en", "locale": "en", "slug": "en-v1",
        "book_slug": "tk-en-v1",
        "book_edition_id": "edition:el-relato:tk-en:v1",
        "book_title": "El Relato — Contemporary English AI V1",
        "gospel_edition_id": "edition:gospels:en:v1",
        "gospel_title": "The Gospels — Contemporary English AI V1",
        "style": "clear contemporary international English; avoid archaic diction while preserving theological meaning and discourse relationships",
    },
    "pt-BR": {
        "language_code": "pt", "locale": "pt-BR", "slug": "pt-br-v1",
        "book_slug": "tk-pt-br-v1",
        "book_edition_id": "edition:el-relato:tk-pt-br:v1",
        "book_title": "El Relato — Português Brasileiro IA V1",
        "gospel_edition_id": "edition:gospels:pt-br:v1",
        "gospel_title": "Evangelhos — Português Brasileiro IA V1",
        "style": "português brasileiro contemporâneo, natural e claro; evita arcaísmos desnecessários e preserva com precisão o conteúdo teológico e discursivo do grego",
    },
}

SYSTEM = """You are translating the Greek text of the four canonical Gospels for a traceable research edition.
Translate ONLY from the supplied Greek source. Do not copy or imitate a named modern Bible translation. Preserve semantic content, participant reference, modality, aspect where relevant, theological terms, negation, conjunctions, quotations, and deliberate repetition. Do not harmonize parallel Gospel witnesses. Do not add explanations or doctrinal interpretation absent from the Greek. The target should read naturally in the requested locale, but fidelity takes priority over elegance.
Return ONLY valid JSON in the exact requested shape. Every input id must appear exactly once; no extra ids."""

class ModelError(RuntimeError): pass
class RateLimited(ModelError): pass

def ro(path: Path):
    c = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c

def jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)

def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp.replace(path)

def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            return json.loads(text[a:b+1])
        raise

def call_model(token: str, models: list[str], target, kind: str, batch):
    if kind == "book":
        payload_items = [{"id": x["unit_id"], "reference": x["reference_raw"], "greek": x["text"]} for x in batch]
        unit_note = "Each item is one editorial unit, sometimes deliberately a sentence fragment. Translate that unit only; do not complete it from memory. Context from neighboring items may resolve pronouns, but output must stay aligned 1:1 to ids."
    else:
        payload_items = [{"id": x["id"], "reference": f'{x["book"]} {x["chapter"]}:{x["verse"]}', "greek": x["text"]} for x in batch]
        unit_note = "Each item is one canonical verse. Translate the supplied Greek verse itself. Do not import wording from another verse or a published translation."
    prompt = (
        f"Target locale: {target['locale']}. Style: {target['style']}.\n"
        f"{unit_note}\n"
        "Return exactly this JSON shape: {\"items\":[{\"id\":\"...\",\"text\":\"...\"}]}.\n"
        "INPUT:\n" + json.dumps(payload_items, ensure_ascii=False, separators=(",", ":"))
    )
    unavailable = []
    last = None
    for model in models:
        body = json.dumps({
            "model": model,
            "messages": [{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],
            "max_tokens": 30000,
        }).encode()
        req = urllib.request.Request(API_URL, data=body, method="POST", headers={
            "Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"
        })
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=300) as resp:
                    data = json.loads(resp.read().decode())
                content = data["choices"][0]["message"]["content"]
                obj = extract_json(content)
                items = obj.get("items") if isinstance(obj, dict) else None
                if not isinstance(items, list): raise ModelError(f"Model {model} did not return items array")
                expected = [x["unit_id"] if kind=="book" else x["id"] for x in batch]
                got = [str(x.get("id")) for x in items]
                if len(got) != len(expected) or set(got) != set(expected) or len(got) != len(set(got)):
                    raise ModelError(f"Coverage mismatch from {model}: expected={len(expected)} got={len(got)}")
                mapped = {str(x["id"]): str(x.get("text") or "").strip() for x in items}
                if any(not mapped[i] for i in expected): raise ModelError(f"Empty translation from {model}")
                return mapped, model
            except urllib.error.HTTPError as e:
                raw = e.read().decode(errors="replace")[:1500]
                last = f"HTTP {e.code} {raw}"
                if e.code in (404, 400) and ("model" in raw.lower() or "unavailable" in raw.lower()):
                    unavailable.append(model); break
                if e.code == 429:
                    retry = int(e.headers.get("Retry-After") or min(60, 4 * (2 ** attempt)))
                    if attempt == 3: break
                    time.sleep(retry); continue
                if e.code >= 500 and attempt < 3:
                    time.sleep(3 * (attempt + 1)); continue
                break
            except (urllib.error.URLError, TimeoutError) as e:
                last = repr(e)
                if attempt < 3: time.sleep(3 * (attempt + 1)); continue
                break
            except (json.JSONDecodeError, KeyError, ModelError) as e:
                last = repr(e)
                if attempt < 2: time.sleep(2); continue
                break
    if last and "429" in last: raise RateLimited(last)
    raise ModelError(f"All models failed; unavailable={unavailable}; last={last}")

def pack(groups, max_chars=15000):
    batches=[]; cur=[]; n=0
    for group in groups:
        gn=sum(len(str(x.get("text") or ""))+len(str(x.get("reference_raw") or ""))+80 for x in group)
        if cur and n+gn>max_chars:
            batches.append(cur); cur=[]; n=0
        cur.extend(group); n+=gn
    if cur: batches.append(cur)
    return batches

def book_source_rows():
    c=ro(BOOK_DB)
    rows=[dict(r) for r in c.execute("""
        SELECT u.unit_id,u.scene_number,u.scene_order,u.global_order,u.reference_raw,ut.text
        FROM units u JOIN unit_texts ut ON ut.unit_id=u.unit_id
        WHERE ut.edition_id=? ORDER BY u.global_order
    """,(BASE_BOOK_EDITION,))]
    c.close()
    if len(rows)!=4123: raise SystemExit(f"Expected 4123 Greek BOOK units, got {len(rows)}")
    return rows

def source_rows():
    rows=[]
    for r in jsonl(SBL_VERSES):
        rows.append({"id":f'{r["book"]}:{int(r["chapter"])}:{int(r["verse"])}',"book":r["book"],"chapter":int(r["chapter"]),"verse":int(r["verse"]),"text":r["text"]})
    if len(rows)!=3768: raise SystemExit(f"Expected 3768 SBLGNT verses, got {len(rows)}")
    return rows

def existing_book(target):
    d=ROOT/"book/translations"/target["book_slug"]/"generated"
    out={}
    if d.exists():
        for p in d.glob("scene-*.jsonl"):
            for r in jsonl(p): out[r["unit_id"]]=r["text"]
    return out

def existing_source(target):
    d=ROOT/"sources/gospel-editions"/target["slug"]/"generated"
    out={}
    if d.exists():
        for p in d.glob("*.jsonl"):
            for r in jsonl(p): out[r["id"]]=r["text"]
    return out

def save_book_batch(target, source_by_id, mapped):
    by_scene=defaultdict(list)
    for uid,text in mapped.items(): by_scene[source_by_id[uid]["scene_number"]].append((source_by_id[uid],text))
    base=ROOT/"book/translations"/target["book_slug"]/"generated"
    for scene,pairs in by_scene.items():
        existing={}
        p=base/f"scene-{scene:03d}.jsonl"
        if p.exists(): existing={r["unit_id"]:r["text"] for r in jsonl(p)}
        for s,t in pairs: existing[s["unit_id"]]=t
        ordered=[{"unit_id":s["unit_id"],"text":existing[s["unit_id"]]} for s in sorted((x for x in source_by_id.values() if x["scene_number"]==scene),key=lambda x:x["scene_order"]) if s["unit_id"] in existing]
        write_jsonl(p,ordered)

def save_source_batch(target, source_by_id, mapped):
    by_ch=defaultdict(list)
    for vid,text in mapped.items():
        s=source_by_id[vid]; by_ch[(s["book"],s["chapter"])].append((s,text))
    base=ROOT/"sources/gospel-editions"/target["slug"]/"generated"
    for (book,ch),pairs in by_ch.items():
        slug=book.lower()
        p=base/f"{slug}-{ch:02d}.jsonl"; existing={}
        if p.exists(): existing={r["id"]:r["text"] for r in jsonl(p)}
        for s,t in pairs: existing[s["id"]]=t
        ids=sorted((x for x in source_by_id.values() if x["book"]==book and x["chapter"]==ch),key=lambda x:x["verse"])
        rows=[{"id":s["id"],"book":s["book"],"chapter":s["chapter"],"verse":s["verse"],"text":existing[s["id"]]} for s in ids if s["id"] in existing]
        write_jsonl(p,rows)

def write_meta(target, model_used, book_done, source_done, blocked=None):
    bdir=ROOT/"book/translations"/target["book_slug"]; bdir.mkdir(parents=True,exist_ok=True)
    policy=f"""# {target['book_slug']} — política V1

Traducción nueva generada directamente desde el griego primario materializado en BOOK. Target: {target['style']}.

Reglas: fidelidad semántica; no imitar traducciones bíblicas modernas; no armonizar testigos; no agregar exégesis; una salida por unidad; trazabilidad a la unidad y testigo griego. Estado generado requiere revisión humana antes de presentarse como revisión filológica.
"""
    (bdir/"POLICY.md").write_text(policy,encoding="utf-8")
    manifest={"edition_id":target["book_edition_id"],"baseline_edition_id":BASE_BOOK_EDITION,"book_id":"book:el-relato","family":"TK","code":target["book_slug"],"language_code":target["language_code"],"locale":target["locale"],"title":target["book_title"],"version":"1","status":"generated-full" if book_done else "generating","provider":"GitHub Models","model_name":model_used or "pending","units_expected":4123,"review_required":True}
    (bdir/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    sdir=ROOT/"sources/gospel-editions"/target["slug"]; sdir.mkdir(parents=True,exist_ok=True)
    edition={"edition_id":target["gospel_edition_id"],"title":target["gospel_title"],"language_code":target["language_code"],"version":"1","status":"consolidated" if source_done else "draft","kind":"translation","base_edition_id":BASE_GOSPEL_EDITION,"materialization":"verses-jsonl","publication":"public" if source_done else "private","notes":f"AI translation directly from Greek SBLGNT source; {target['style']}; human review required."}
    (sdir/"edition.json").write_text(json.dumps(edition,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    prog={"locale":target["locale"],"book_complete":book_done,"source_complete":source_done,"complete":book_done and source_done,"model":model_used,"blocked":blocked}
    (ROOT/"build").mkdir(exist_ok=True)
    (ROOT/"build/translation-status.json").write_text(json.dumps(prog,indent=2)+"\n",encoding="utf-8")
    return prog

def finalize_source(target, src_rows):
    have=existing_source(target)
    if len(have)!=len(src_rows): return False
    rows=[{"book":s["book"],"chapter":s["chapter"],"verse":s["verse"],"text":have[s["id"]]} for s in src_rows]
    write_jsonl(ROOT/"sources/gospel-editions"/target["slug"] / "verses.jsonl",rows)
    return True

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--locale",choices=TARGETS,required=True); ap.add_argument("--max-calls",type=int,default=35)
    a=ap.parse_args(); target=TARGETS[a.locale]
    token=os.environ.get("GITHUB_TOKEN")
    if not token: raise SystemExit("GITHUB_TOKEN required")
    models=[x.strip() for x in os.environ.get("TRANSLATION_MODELS","openai/gpt-5.6-sol,openai/gpt-5,openai/gpt-4.1").split(",") if x.strip()]

    bsrc=book_source_rows(); ssrc=source_rows(); b_by={x["unit_id"]:x for x in bsrc}; s_by={x["id"]:x for x in ssrc}
    bhave=existing_book(target); shave=existing_source(target)
    bgroups=[]
    for scene in range(1,121):
        g=[x for x in bsrc if x["scene_number"]==scene and x["unit_id"] not in bhave]
        if g: bgroups.append(g)
    order={"Matthew":1,"Mark":2,"Luke":3,"John":4}
    sgdict=defaultdict(list)
    for x in ssrc:
        if x["id"] not in shave: sgdict[(x["book"],x["chapter"])].append(x)
    sgroups=[sgdict[k] for k in sorted(sgdict,key=lambda k:(order[k[0]],k[1]))]
    batches=[("book",x) for x in pack(bgroups,14500)] + [("source",x) for x in pack(sgroups,14500)]
    calls=0; model_used=None; blocked=None
    for kind,batch in batches:
        if calls>=a.max_calls: break
        try:
            mapped,model=call_model(token,models,target,kind,batch); model_used=model; calls+=1
            if kind=="book": save_book_batch(target,b_by,mapped); bhave.update(mapped)
            else: save_source_batch(target,s_by,mapped); shave.update(mapped)
            print(json.dumps({"call":calls,"kind":kind,"items":len(mapped),"model":model,"book":len(bhave),"source":len(shave)},ensure_ascii=False),flush=True)
            time.sleep(1.2)
        except RateLimited as e:
            blocked="rate-limited: "+str(e); print(blocked,file=sys.stderr); break
        except ModelError as e:
            blocked="model-error: "+str(e); print(blocked,file=sys.stderr); break

    book_done=len(bhave)==4123
    source_done=finalize_source(target,ssrc) if len(shave)==3768 else False
    prog=write_meta(target,model_used,book_done,source_done,blocked)
    prog.update({"book_units":len(bhave),"book_expected":4123,"source_verses":len(shave),"source_expected":3768,"calls_this_run":calls})
    (ROOT/"build/translation-status.json").write_text(json.dumps(prog,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(prog,ensure_ascii=False,indent=2))
    if blocked and calls==0: return 2
    return 0

if __name__=="__main__": raise SystemExit(main())
