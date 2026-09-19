#!/usr/bin/env python3
from __future__ import annotations

import collections
import difflib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SBL = ROOT / "data/normalized/sblgnt/tokens.jsonl"
TAGNT = ROOT / "data/normalized/stepbible/tagnt-rows.jsonl"
TBESG = ROOT / "data/normalized/stepbible/strong-entries.jsonl"
MORPH = ROOT / "data/normalized/stepbible/morphology.jsonl"
STRONG_ORIG = ROOT / "data/normalized/strong-original/strong-original-entries.jsonl"

OUT = ROOT / "data/normalized/links"
DERIVED = ROOT / "data/derived/alignment"
OUT.mkdir(parents=True, exist_ok=True)
DERIVED.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: Path):
    with path.open(encoding="utf-8-sig") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def norm_greek(s: str) -> str:
    # Alignment normalization only. Original forms remain untouched.
    s = unicodedata.normalize("NFD", s.casefold())
    chars = []
    for ch in s:
        cat = unicodedata.category(ch)
        if cat.startswith("M"):
            continue
        if cat.startswith("P") or cat.startswith("Z"):
            continue
        chars.append(ch)
    return "".join(chars).replace("ς", "σ")


def is_sbl_row(row) -> bool:
    # TAGNT editions are compound strings such as NA27+NA28+Tyn+SBL+WH...
    return bool(re.search(r"(^|[+ ;])SBL($|[+ ;])", row.get("editions") or ""))


def strong_base(s: str | None):
    if not s:
        return None
    m = re.search(r"G(\d{4,5})", s)
    if not m:
        return None
    n = int(m.group(1))
    return f"G{n:04d}" if n <= 9999 else f"G{n:05d}"


def main():
    sbl = read_jsonl(SBL)
    tagnt_all = read_jsonl(TAGNT)
    tbesg = read_jsonl(TBESG)
    morphology = read_jsonl(MORPH)
    strong_original = read_jsonl(STRONG_ORIG)

    s_by_ref = collections.defaultdict(list)
    t_by_ref = collections.defaultdict(list)
    for row in sbl:
        s_by_ref[(row["book"], row["chapter"], row["verse"])].append(row)
    for row in tagnt_all:
        if is_sbl_row(row):
            t_by_ref[(row["book"], row["chapter"], row["verse"])].append(row)

    morph_codes = {x["code"] for x in morphology}
    original_by_id = {x["strong_id"]: x["id"] for x in strong_original}
    tbesg_by_d = collections.defaultdict(list)
    tbesg_by_e = collections.defaultdict(list)
    for x in tbesg:
        if x.get("d_strong_id"):
            tbesg_by_d[x["d_strong_id"]].append(x["id"])
        tbesg_by_e[x["e_strong"]].append(x["id"])

    links = []
    unmatched = []
    verse_stats = []
    methods = collections.Counter()

    all_refs = sorted(set(s_by_ref) | set(t_by_ref))
    for ref in all_refs:
        ss = s_by_ref.get(ref, [])
        tt = t_by_ref.get(ref, [])
        sn = [norm_greek(x["surface"]) for x in ss]
        tn = [norm_greek(x["greek"]) for x in tt]

        matcher = difflib.SequenceMatcher(a=sn, b=tn, autojunk=False)
        mapped = {}
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for di in range(i2 - i1):
                    mapped[i1 + di] = (j1 + di, "normalized-exact")
            elif tag == "replace" and (i2 - i1) == (j2 - j1):
                # Preserve as lower-confidence alignment; never call it exact.
                for di in range(i2 - i1):
                    mapped[i1 + di] = (j1 + di, "positional-replace")

        for i, srow in enumerate(ss):
            if i not in mapped:
                unmatched.append({
                    "token_id": srow["id"],
                    "book": srow["book"],
                    "chapter": srow["chapter"],
                    "verse": srow["verse"],
                    "position": srow["position"],
                    "surface": srow["surface"],
                    "reason": "no-TAGNT-SBL-row-aligned",
                    "tagnt_candidates": [x["greek"] for x in tt],
                })
                continue

            j, method = mapped[i]
            trow = tt[j]
            raw_strong = trow.get("strongs") or None
            base = strong_base(raw_strong)
            tbesg_ids = []
            if raw_strong:
                tbesg_ids = list(tbesg_by_d.get(raw_strong, []))
            if not tbesg_ids and base:
                tbesg_ids = list(tbesg_by_e.get(base, []))

            original_id = original_by_id.get(base) if base else None
            morphology_code = trow.get("grammar") or None
            methods[method] += 1

            links.append({
                "id": f"link:sbl-tagnt:{srow['book'].lower()}:{srow['chapter']}:{srow['verse']}:{srow['position']}",
                "token_id": srow["id"],
                "tagnt_row_id": trow["id"],
                "book": srow["book"],
                "chapter": srow["chapter"],
                "verse": srow["verse"],
                "token_position": srow["position"],
                "surface_sbl": srow["surface"],
                "surface_tagnt": trow["greek"],
                "match_method": method,
                "normalized_equal": norm_greek(srow["surface"]) == norm_greek(trow["greek"]),
                "strongs": raw_strong,
                "morphology_code": morphology_code,
                "morphology_known": morphology_code in morph_codes if morphology_code else False,
                "lemma": trow.get("dictionary_form"),
                "gloss": trow.get("gloss"),
                "spanish_translation": trow.get("spanish_translation"),
                "sub_meaning": trow.get("sub_meaning"),
                "editions": trow.get("editions"),
                "tbesg_entry_ids": tbesg_ids,
                "strong_original_id": original_id,
            })

        verse_stats.append({
            "book": ref[0],
            "chapter": ref[1],
            "verse": ref[2],
            "sbl_tokens": len(ss),
            "tagnt_sbl_rows": len(tt),
            "mapped": sum(1 for i in range(len(ss)) if i in mapped),
            "exact_sequence": sn == tn,
        })

    link_ids = [x["token_id"] for x in links]
    if len(link_ids) != len(set(link_ids)):
        raise RuntimeError("Duplicate SBL token links")

    coverage = len(links) / len(sbl) if sbl else 0
    exact = sum(x["match_method"] == "normalized-exact" for x in links)
    positional = sum(x["match_method"] == "positional-replace" for x in links)
    unknown_morph = sum(bool(x["morphology_code"]) and not x["morphology_known"] for x in links)
    no_tbesg = sum(bool(x["strongs"]) and not x["tbesg_entry_ids"] for x in links)

    # Initial gate: high coverage required, but unresolved cases remain explicit.
    if coverage < 0.98:
        raise RuntimeError(f"Alignment coverage too low: {coverage:.4%}")

    with (OUT / "sbl-tagnt-links.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for row in links:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    with (DERIVED / "sbl-tagnt-unmatched.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for row in unmatched:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    with (DERIVED / "verse-alignment-stats.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for row in verse_stats:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    report = {
        "sbl_tokens": len(sbl),
        "tagnt_rows_total": len(tagnt_all),
        "tagnt_rows_marked_sbl": sum(len(x) for x in t_by_ref.values()),
        "linked_tokens": len(links),
        "coverage": coverage,
        "unmatched_tokens": len(unmatched),
        "methods": dict(methods),
        "normalized_exact_links": exact,
        "positional_replace_links": positional,
        "links_with_unknown_morphology_code": unknown_morph,
        "links_with_strong_but_no_tbesg_entry": no_tbesg,
        "links_with_strong_original": sum(x["strong_original_id"] is not None for x in links),
        "verses_total": len(s_by_ref),
        "verses_with_exact_sequence": sum(x["exact_sequence"] for x in verse_stats),
    }
    (DERIVED / "sbl-tagnt-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
