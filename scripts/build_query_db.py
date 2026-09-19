#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    p=ROOT/path
    if not p.exists():
        return []
    with p.open(encoding="utf-8-sig") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def j(value):
    return json.dumps(value,ensure_ascii=False,separators=(",",":")) if value is not None else None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default="build/el-relato.sqlite")
    ap.add_argument("--stats-output",default=None)
    args=ap.parse_args()
    out=ROOT/args.output
    out.parent.mkdir(parents=True,exist_ok=True)
    out.unlink(missing_ok=True)

    tokens=rows(Path("data/normalized/sblgnt/tokens.jsonl"))
    links=rows(Path("data/normalized/links/sbl-tagnt-links.jsonl"))
    links_by_token={x["token_id"]:x for x in links}
    strong_ext=rows(Path("data/normalized/stepbible/strong-entries.jsonl"))
    strong_orig=rows(Path("data/normalized/strong-original/strong-original-entries.jsonl"))
    morphology=rows(Path("data/normalized/stepbible/morphology.jsonl"))
    apparatus=rows(Path("data/normalized/apparatus/edition-apparatus-units.jsonl"))
    manuscripts=rows(Path("data/normalized/manuscripts.jsonl"))
    sources=rows(Path("data/normalized/sources.jsonl"))
    manuscript_images=rows(Path("data/normalized/manuscript-evidence/images.jsonl"))
    witness_attestations=rows(Path("data/normalized/manuscript-evidence/witness-attestations.jsonl"))
    transcriptions_all=(
        rows(Path("data/normalized/transcriptions/sinaiticus-gospels.jsonl"))
        + rows(Path("data/normalized/transcriptions/igntp-papyri.jsonl"))
    )

    facsimile_summary_path=ROOT/"data/derived/manuscripts/core-gospel-facsimile-mirror-summary.json"
    facsimiles=[]
    if facsimile_summary_path.exists():
        facsimiles=json.loads(facsimile_summary_path.read_text(encoding="utf-8")).get("manifest_entries",[])

    con=sqlite3.connect(out)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.executescript("""
    CREATE TABLE tokens (
      token_id TEXT PRIMARY KEY,
      book TEXT NOT NULL,
      chapter INTEGER NOT NULL,
      verse INTEGER NOT NULL,
      position INTEGER NOT NULL,
      surface TEXT NOT NULL,
      prefix_before TEXT,
      punctuation_after TEXT,
      textual_status TEXT NOT NULL,
      tagnt_row_id TEXT,
      match_method TEXT,
      tagnt_surface TEXT,
      strongs TEXT,
      lemma TEXT,
      morphology_code TEXT,
      morphology_components_json TEXT,
      morphology_known INTEGER,
      gloss TEXT,
      spanish_translation TEXT,
      sub_meaning TEXT,
      tbesg_entry_ids_json TEXT,
      strong_original_id TEXT
    );

    CREATE TABLE strong_extended (
      id TEXT PRIMARY KEY,
      e_strong TEXT,
      d_strong_id TEXT,
      u_strong TEXT,
      greek TEXT,
      transliteration TEXT,
      lexical_morphology TEXT,
      gloss TEXT,
      meaning_html TEXT
    );

    CREATE TABLE strong_original (
      id TEXT PRIMARY KEY,
      strong_id TEXT,
      number INTEGER,
      lemma TEXT,
      transliteration TEXT,
      pronunciation TEXT,
      derivation TEXT,
      strongs_definition TEXT,
      kjv_definition TEXT,
      cross_references_json TEXT
    );

    CREATE TABLE morphology (
      code TEXT PRIMARY KEY,
      part_of_speech TEXT,
      person TEXT,
      tense TEXT,
      voice TEXT,
      mood TEXT,
      grammatical_case TEXT,
      number TEXT,
      gender TEXT,
      degree TEXT,
      raw_expansion TEXT
    );

    CREATE TABLE edition_apparatus (
      id TEXT PRIMARY KEY,
      book TEXT,
      chapter INTEGER,
      verse INTEGER,
      ordinal INTEGER,
      location_label TEXT,
      raw_note TEXT,
      readings_json TEXT,
      parse_status TEXT
    );

    CREATE TABLE manuscripts (
      id TEXT PRIMARY KEY,
      ga_id TEXT,
      label TEXT,
      gospels_json TEXT,
      dating_json TEXT,
      institution TEXT,
      shelfmark TEXT,
      primary_source TEXT,
      content_summary TEXT,
      facsimile_status TEXT,
      transcription_status TEXT
    );

    CREATE TABLE facsimiles (
      source TEXT,
      label TEXT,
      gospels_json TEXT,
      canvas_id TEXT,
      source_url TEXT,
      local_path TEXT PRIMARY KEY,
      width INTEGER,
      height INTEGER,
      sha256 TEXT,
      size INTEGER,
      status TEXT
    );

    CREATE TABLE manuscript_images (
      id TEXT PRIMARY KEY,
      manuscript_id TEXT NOT NULL,
      source_id TEXT,
      folio TEXT,
      page_label TEXT,
      side TEXT,
      local_path TEXT,
      upstream_url TEXT,
      sha256 TEXT,
      mime_type TEXT,
      width INTEGER,
      height INTEGER,
      notes TEXT,
      metadata_json TEXT
    );

    CREATE TABLE witness_attestations (
      id TEXT PRIMARY KEY,
      manuscript_id TEXT NOT NULL,
      passage_id TEXT NOT NULL,
      status TEXT,
      source_id TEXT,
      image_ids_json TEXT,
      transcription_ids_json TEXT,
      reading_id TEXT,
      notes TEXT
    );

    CREATE TABLE transcriptions (
      id TEXT PRIMARY KEY,
      manuscript_id TEXT NOT NULL,
      source_id TEXT,
      book TEXT,
      chapter INTEGER,
      verse INTEGER,
      passage_ids_json TEXT,
      image_id TEXT,
      layer TEXT,
      format TEXT,
      text TEXT,
      local_path TEXT,
      notes TEXT
    );

    CREATE TABLE sources (
      id TEXT PRIMARY KEY,
      title TEXT,
      category TEXT,
      institution TEXT,
      upstream_url TEXT,
      external_id TEXT,
      version TEXT,
      local_path TEXT,
      sha256 TEXT,
      capture_status TEXT
    );
    """)

    token_rows=[]
    for t in tokens:
        l=links_by_token.get(t["id"],{})
        token_rows.append((
            t["id"],t["book"],t["chapter"],t["verse"],t["position"],t["surface"],
            t.get("prefix_before"),t.get("punctuation_after"),t.get("textual_status","main"),
            l.get("tagnt_row_id"),l.get("match_method"),l.get("surface_tagnt"),l.get("strongs"),
            l.get("lemma"),l.get("morphology_code"),j(l.get("morphology_components")),
            1 if l.get("morphology_known") else 0 if l else None,
            l.get("gloss"),l.get("spanish_translation"),l.get("sub_meaning"),
            j(l.get("tbesg_entry_ids")),l.get("strong_original_id")
        ))
    con.executemany("INSERT INTO tokens VALUES ("+",".join(["?"]*22)+")",token_rows)

    con.executemany("INSERT INTO strong_extended VALUES (?,?,?,?,?,?,?,?,?)",[
        (x["id"],x.get("e_strong"),x.get("d_strong_id"),x.get("u_strong"),x.get("greek"),
         x.get("transliteration"),x.get("lexical_morphology"),x.get("gloss"),x.get("meaning_html"))
        for x in strong_ext
    ])
    con.executemany("INSERT INTO strong_original VALUES (?,?,?,?,?,?,?,?,?,?)",[
        (x["id"],x.get("strong_id"),x.get("number"),x.get("lemma"),x.get("transliteration"),
         x.get("pronunciation"),x.get("derivation"),x.get("strongs_definition"),
         x.get("kjv_definition"),j(x.get("cross_references")))
        for x in strong_orig
    ])
    con.executemany("INSERT INTO morphology VALUES (?,?,?,?,?,?,?,?,?,?,?)",[
        (x["code"],x.get("part_of_speech"),x.get("person"),x.get("tense"),x.get("voice"),
         x.get("mood"),x.get("case"),x.get("number"),x.get("gender"),x.get("degree"),x.get("raw_expansion"))
        for x in morphology
    ])
    con.executemany("INSERT INTO edition_apparatus VALUES (?,?,?,?,?,?,?,?,?)",[
        (x["id"],x["book"],x["chapter"],x["verse"],x["ordinal"],x.get("location_label"),
         x["raw_note"],j(x["readings"]),x["parse_status"])
        for x in apparatus
    ])
    con.executemany("INSERT INTO manuscripts VALUES (?,?,?,?,?,?,?,?,?,?,?)",[
        (x["id"],x["ga_id"],x["label"],j(x["gospels"]),j(x["dating"]),x.get("institution"),
         x.get("shelfmark"),x["primary_source"],x.get("content_summary"),
         x.get("facsimile_status"),x.get("transcription_status"))
        for x in manuscripts
    ])
    con.executemany("INSERT INTO facsimiles VALUES (?,?,?,?,?,?,?,?,?,?,?)",[
        (x["source"],x["label"],j(x.get("gospels")),x.get("canvas_id"),x.get("source_url"),
         x["local_path"],x.get("width"),x.get("height"),x.get("sha256"),x.get("size"),x.get("status"))
        for x in facsimiles
    ])
    con.executemany("INSERT INTO manuscript_images VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",[
        (
          x["id"],x["manuscript_id"],x.get("source_id"),x.get("folio"),
          x.get("page_label"),x.get("side"),x.get("local_path"),x.get("upstream_url"),
          x.get("sha256"),x.get("mime_type"),x.get("width"),x.get("height"),
          x.get("notes"),j(x)
        )
        for x in manuscript_images
    ])
    con.executemany("INSERT INTO witness_attestations VALUES (?,?,?,?,?,?,?,?,?)",[
        (
          x["id"],x["manuscript_id"],x["passage_id"],x.get("status"),x.get("source_id"),
          j(x.get("image_ids")),j(x.get("transcription_ids")),x.get("reading_id"),x.get("notes")
        )
        for x in witness_attestations
    ])
    transcription_rows=[]
    for x in transcriptions_all:
        book=chapter=verse=None
        pids=x.get("passage_ids") or []
        if pids:
            parts=pids[0].split(":")
            if len(parts)>=4:
                book=parts[1].capitalize()
                chapter=int(parts[2])
                verse=int(parts[3])
        transcription_rows.append((
          x["id"],x["manuscript_id"],x.get("source_id"),book,chapter,verse,
          j(pids),x.get("image_id"),x.get("layer"),x.get("format"),x.get("text"),
          x.get("local_path"),x.get("notes")
        ))
    con.executemany("INSERT INTO transcriptions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",transcription_rows)

    con.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?)",[
        (x["id"],x["title"],x["category"],x.get("institution"),x["upstream_url"],x.get("external_id"),
         x.get("version"),x.get("local_path"),x.get("sha256"),x.get("capture_status"))
        for x in sources
    ])

    con.executescript("""
    CREATE INDEX idx_tokens_ref ON tokens(book,chapter,verse,position);
    CREATE INDEX idx_tokens_strong ON tokens(strongs);
    CREATE INDEX idx_tokens_lemma ON tokens(lemma);
    CREATE INDEX idx_tokens_morph ON tokens(morphology_code);
    CREATE INDEX idx_app_ref ON edition_apparatus(book,chapter,verse);
    CREATE INDEX idx_strong_ext_e ON strong_extended(e_strong);
    CREATE INDEX idx_strong_ext_d ON strong_extended(d_strong_id);
    CREATE INDEX idx_strong_orig_id ON strong_original(strong_id);
    CREATE INDEX idx_ms_images_ms ON manuscript_images(manuscript_id);
    CREATE INDEX idx_ms_images_label ON manuscript_images(manuscript_id,page_label);
    CREATE INDEX idx_attest_passage ON witness_attestations(passage_id);
    CREATE INDEX idx_attest_ms ON witness_attestations(manuscript_id);
    CREATE INDEX idx_tx_ref ON transcriptions(book,chapter,verse);
    CREATE INDEX idx_tx_ms ON transcriptions(manuscript_id);

    CREATE VIEW token_analysis AS
      SELECT token_id,book,chapter,verse,position,surface,textual_status,
             strongs,lemma,morphology_code,morphology_known,gloss,
             spanish_translation,sub_meaning,match_method,strong_original_id
      FROM tokens;

    CREATE VIEW passage_evidence AS
      SELECT a.passage_id,a.manuscript_id,a.status,
             a.image_ids_json,a.transcription_ids_json,
             m.label AS manuscript_label,m.ga_id,
             m.primary_source
      FROM witness_attestations a
      LEFT JOIN manuscripts m ON m.id=a.manuscript_id;

    CREATE VIEW verse_transcriptions AS
      SELECT book,chapter,verse,manuscript_id,text,layer,source_id,id AS transcription_id
      FROM transcriptions
      WHERE book IS NOT NULL AND chapter IS NOT NULL AND verse IS NOT NULL;
    """)
    con.commit()

    stats={
        "tokens":con.execute("SELECT count(*) FROM tokens").fetchone()[0],
        "linked_tokens":con.execute("SELECT count(*) FROM tokens WHERE tagnt_row_id IS NOT NULL").fetchone()[0],
        "strong_extended_entries":con.execute("SELECT count(*) FROM strong_extended").fetchone()[0],
        "strong_original_entries":con.execute("SELECT count(*) FROM strong_original").fetchone()[0],
        "morphology_codes":con.execute("SELECT count(*) FROM morphology").fetchone()[0],
        "edition_apparatus_units":con.execute("SELECT count(*) FROM edition_apparatus").fetchone()[0],
        "manuscripts":con.execute("SELECT count(*) FROM manuscripts").fetchone()[0],
        "facsimiles":con.execute("SELECT count(*) FROM facsimiles").fetchone()[0],
        "manuscript_images":con.execute("SELECT count(*) FROM manuscript_images").fetchone()[0],
        "witness_attestations":con.execute("SELECT count(*) FROM witness_attestations").fetchone()[0],
        "transcription_units":con.execute("SELECT count(*) FROM transcriptions").fetchone()[0],
        "database_bytes":out.stat().st_size,
    }
    con.close()
    if args.stats_output:
        stats_path=ROOT/args.stats_output
        stats_path.parent.mkdir(parents=True,exist_ok=True)
        stats_path.write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(stats,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
