from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

BOOK_ALIASES = {
    "matthew": "Matthew", "matt": "Matthew", "mat": "Matthew", "mateo": "Matthew",
    "mark": "Mark", "mrk": "Mark", "marcos": "Mark",
    "luke": "Luke", "luk": "Luke", "lucas": "Luke",
    "john": "John", "jhn": "John", "juan": "John",
}

def _jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue

def _book(value: str) -> str:
    key = value.strip().lower()
    if key not in BOOK_ALIASES:
        raise ValueError("Only Matthew, Mark, Luke and John are available through the Gospels interface.")
    return BOOK_ALIASES[key]

def _ref_matches(row: dict[str, Any], book: str, chapter: int, verse: int | None = None) -> bool:
    b = str(row.get("book") or row.get("book_name") or row.get("bookName") or "")
    c = row.get("chapter") or row.get("chapter_number") or row.get("chapterNumber")
    v = row.get("verse") or row.get("verse_number") or row.get("verseNumber") or row.get("verse_start")
    osis = str(row.get("osis_ref") or row.get("osis") or row.get("reference") or row.get("ref") or "")
    if b and b.lower() != book.lower(): return False
    if c is not None and str(c) != str(chapter): return False
    if not b and osis and not (osis.startswith(f"{book}.{chapter}.") or osis.startswith(f"{book}.{chapter}:")): return False
    if verse is not None:
        if v is not None and str(v) != str(verse): return False
        if v is None and osis and not (osis == f"{book}.{chapter}.{verse}" or osis.startswith(f"{book}.{chapter}.{verse}.")): return False
    return bool(b or osis)

class GospelRepository:
    def __init__(self, root: Path):
        self.root = root
        self.verses = root / "data/normalized/sblgnt/edition-verses.jsonl"
        self.tokens = root / "data/normalized/sblgnt/tokens.jsonl"\n        self.links = root / "data/normalized/links/sbl-tagnt-links.jsonl"
        self.strong = root / "data/normalized/stepbible/strong-entries.jsonl"
        self.strong_original = root / "data/normalized/strong-original/strong-original-entries.jsonl"
        self.attestations = root / "data/normalized/manuscript-evidence/witness-attestations.jsonl"
        self.variants = root / "data/normalized/variants/manuscript-verse-variants.jsonl"

    def _range(self, start: int | None, end: int | None) -> tuple[int, int]:
        return (1, 999) if start is None else (start, end if end is not None else start)

    def get_passage(self, book: str, chapter: int, verse_start: int | None = None, verse_end: int | None = None) -> dict[str, Any]:
        canonical = _book(book); lo, hi = self._range(verse_start, verse_end); rows = []
        for row in _jsonl(self.verses):
            if not _ref_matches(row, canonical, chapter): continue
            v = row.get("verse") or row.get("verse_number") or row.get("verseNumber") or row.get("verse_start")
            try: vn = int(v)
            except (TypeError, ValueError): continue
            if lo <= vn <= hi: rows.append(row)
        return {"interface":"gospels","canonical":True,"book":canonical,"chapter":chapter,"verse_start":verse_start,"verse_end":verse_end,"edition":"SBLGNT 2010 normalized repository edition","verses":rows,"provenance":["data/normalized/sblgnt/edition-verses.jsonl"]}

    def get_tokens(self, book: str, chapter: int, verse: int) -> dict[str, Any]:
        canonical = _book(book)
        rows = [r for r in _jsonl(self.tokens) if _ref_matches(r, canonical, chapter, verse)]
        return {"interface":"gospels","canonical":True,"reference":f"{canonical} {chapter}:{verse}","tokens":rows,"provenance":["data/normalized/sblgnt/tokens.jsonl"]}

    def get_strong(self, strong: str) -> dict[str, Any]:
        key = strong.strip().upper()
        if key and key[0].isdigit(): key = "G" + key
        matches = []
        for source in (self.strong_original, self.strong):
            for row in _jsonl(source):
                values = [str(row.get(k, "")).upper() for k in ("strong","strongs","strong_number","id","number")]
                if key in values or any(key == v.replace("STRONG:", "") for v in values):
                    matches.append({"source":str(source.relative_to(self.root)),"entry":row})
        return {"interface":"gospels","strong":key,"entries":matches}

    def get_manuscript_evidence(self, book: str, chapter: int, verse: int) -> dict[str, Any]:
        canonical = _book(book)
        att = [r for r in _jsonl(self.attestations) if _ref_matches(r, canonical, chapter, verse)]
        var = [r for r in _jsonl(self.variants) if _ref_matches(r, canonical, chapter, verse)]
        return {"interface":"gospels","canonical":True,"reference":f"{canonical} {chapter}:{verse}","witness_attestations":att,"variants":var,"provenance":["data/normalized/manuscript-evidence/witness-attestations.jsonl","data/normalized/variants/manuscript-verse-variants.jsonl"]}

    def translation_packet(self, book: str, chapter: int, verse_start: int | None, verse_end: int | None, target_language: str, translation_preferences: str) -> dict[str, Any]:
        passage = self.get_passage(book, chapter, verse_start, verse_end); token_rows = []
        for vr in passage["verses"]:
            v = vr.get("verse") or vr.get("verse_number") or vr.get("verseNumber") or vr.get("verse_start")
            if v is not None: token_rows.extend(self.get_tokens(passage["book"], chapter, int(v))["tokens"])
        return {"interface":"gospels","task":"personalized_translation_source_packet","target_language":target_language,"translation_preferences":translation_preferences,"passage":passage,"tokens":token_rows,"translation_instruction":"Translate from the supplied Greek evidence. Preserve ambiguity where evidence is ambiguous; do not treat Strong numbers as a substitute for the Greek text. Clearly distinguish translation from explanatory notes."}

class ElRelatoRepository:
    def __init__(self, root: Path):
        self.root = root
        self.scenes = root / "book/exports/scenes.jsonl"
        self.translations = root / "book/translations"

    def get_scene(self, scene_number: int, locale: str | None = None) -> dict[str, Any]:
        scene = next((r for r in _jsonl(self.scenes) if int(r.get("scene_number", -1)) == scene_number), None)
        if scene is None: raise ValueError(f"El Relato scene {scene_number} was not found.")
        result: dict[str, Any] = {"interface":"el_relato","canonical":False,"work_type":"editorial_harmony","scene":scene,"provenance":["book/exports/scenes.jsonl"]}
        if locale:
            p = self.translations / locale / "generated" / f"scene-{scene_number:03d}.jsonl"
            if p.exists():
                result["translation_locale"] = locale; result["translation_units"] = list(_jsonl(p)); result["provenance"].append(str(p.relative_to(self.root)))
        return result

    def list_scenes(self, chapter_number: str | None = None) -> dict[str, Any]:
        items = []
        for row in _jsonl(self.scenes):
            if chapter_number is not None and str(row.get("chapter_number")) != str(chapter_number): continue
            items.append({k:row.get(k) for k in ("scene_number","chapter_number","title","edition_id")})
        return {"interface":"el_relato","canonical":False,"work_type":"editorial_harmony","scenes":items}
