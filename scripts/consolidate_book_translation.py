#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'book/el-relato-book.sqlite'
BASE='edition:el-relato:grc-sblgnt-2010:v1'
TARGETS={
'es-419':{'dir':'tk-es-419-v1','edition_id':'edition:el-relato:tk-es-419:v1'},
'en':{'dir':'tk-en-v1','edition_id':'edition:el-relato:tk-en:v1'},
'pt-BR':{'dir':'tk-pt-br-v1','edition_id':'edition:el-relato:tk-pt-br:v1'},
}

def jsonl(p):
  with p.open(encoding='utf-8') as f:
    for line in f:
      if line.strip(): yield json.loads(line)

def sha(s): return hashlib.sha256(s.encode()).hexdigest()

def main():
  ap=argparse.ArgumentParser(); ap.add_argument('--locale',choices=TARGETS,required=True); a=ap.parse_args(); cfg=TARGETS[a.locale]
  tdir=ROOT/'book/translations'/cfg['dir']; manifest=json.loads((tdir/'manifest.json').read_text()); policy_hash=hashlib.sha256((tdir/'POLICY.md').read_bytes()).hexdigest()
  rows={}
  for p in sorted((tdir/'generated').glob('scene-*.jsonl')):
    for r in jsonl(p):
      if r['unit_id'] in rows: raise SystemExit(f'duplicate {r["unit_id"]}')
      rows[r['unit_id']]=r['text'].strip()
  if len(rows)!=4123: raise SystemExit(f'expected 4123 translated units, got {len(rows)}')
  now=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
  c=sqlite3.connect(DB); c.execute('pragma foreign_keys=on')
  try:
    base={r[0]:(r[1],r[2]) for r in c.execute('''select u.unit_id,ut.source_witness_id,ut.text from units u join unit_texts ut on ut.unit_id=u.unit_id where ut.edition_id=? order by u.global_order''',(BASE,))}
    if len(base)!=4123 or set(base)!=set(rows): raise SystemExit('baseline coverage mismatch')
    source_id=c.execute('select source_edition_id from editions where edition_id=?',(BASE,)).fetchone()[0]
    eid=manifest['edition_id']
    c.execute('delete from editions where edition_id=?',(eid,))
    c.execute('''insert into editions(edition_id,book_id,language_code,locale,title,edition_role,version,derivation_policy,source_edition_id,status,created_at) values(?,?,?,?,?,?,?,?,?,?,?)''',(
      eid,manifest['book_id'],manifest['language_code'],manifest['locale'],manifest['title'],'ai-translation','1',
      'Direct AI translation from the primary Greek text per editorial unit; no silent harmonization; generated full coverage; human review required.',source_id,'generated-full',now))
    for uid,text in rows.items():
      witness,greek=base[uid]
      c.execute('insert into unit_texts values (?,?,?,?,?,?)',(eid,uid,text,witness,f'ai-translation:{manifest["code"]}:v1','generated'))
      c.execute('insert into translation_unit_audit values (?,?,?,?,?,?,?)',(eid,uid,BASE,sha(greek or ''),sha(text),policy_hash,manifest['model_name']))
    run=f'run:{manifest["code"]}:v1:full'
    c.execute('delete from translation_runs where run_id=?',(run,))
    c.execute('''insert into translation_runs values (?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
      run,eid,BASE,manifest['provider'],manifest['model_name'],manifest['code']+'-v1',policy_hash,manifest['locale'],4123,4123,now,'generated-full','120/120 scenes; human review required before approval/published status.'))
    if c.execute('select count(*) from unit_texts where edition_id=?',(eid,)).fetchone()[0]!=4123: raise SystemExit('persistence count mismatch')
    fk=c.execute('pragma foreign_key_check').fetchall()
    if fk: raise SystemExit(f'foreign key errors: {fk[:5]}')
    c.commit()
    report={'status':'PASS','edition_id':eid,'translated_units':4123,'expected_units':4123,'locale':manifest['locale'],'model':manifest['model_name'],'human_review_required':True,'foreign_key_check':'ok'}
    (tdir/'build-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
  finally: c.close()
if __name__=='__main__': main()
