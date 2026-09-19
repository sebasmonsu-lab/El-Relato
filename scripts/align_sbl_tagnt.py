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
    s = unicodedata.normalize("NFD", s.casefold())
    chars = []
    for ch in s:
        cat = unicodedata.category(ch)
        if cat.startswith("M") or cat.startswith("P") or cat.startswith("Z"):
            continue
        chars.append(ch)
    return "".join(chars).replace("ς", "σ")


def is_sbl_row(row) -> bool:
    return bool(re.search(r"(^|[+ ;])SBL($|[+ ;])", row.get("editions") or ""))


def morphology_parts(code: str | None):
    if not code:
        return []
    return [x.strip() for x in re.split(r"\\s*\\+\\s*", code) if x.strip()]


def strong_base(s: str | None):
    if not s:
        return None
    m = re.search(r"G(\d{4,5})", s)
    if not m:
        return None
    n = int(m.group(1))
    return f"G{n:04d}" if n <= 9999 else f"G{n:05d}"


def sequence_map(source_pairs, target_rows, *, exact_method, positional_method=None):
    """Return source-index -> (target-index, method).

    source_pairs is [(original_sbl_index, token), ...].
    For editorially double-bracketed material we deliberately disable
    positional replacement and only accept normalized equal blocks.
    """
    sn = [norm_greek(row["surface"]) for _, row in source_pairs]
    tn = [norm_greek(row["greek"]) for row in target_rows]
    matcher = difflib.SequenceMatcher(a=sn, b=tn, autojunk=False)
    mapped = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for di in range(i2 - i1):
                original_index = source_pairs[i1 + di][0]
                mapped[original_index] = (j1 + di, exact_method)
        elif (
            positional_method is not None
            and tag == "replace"
            and (i2 - i1) == (j2 - j1)
        ):
            for di in range(i2 - i1):
                original_index = source_pairs[i1 + di][0]
                mapped[original_index] = (j1 + di, positional_method)
    return mapped


def main():
    sbl = read_jsonl(SBL)
    tagnt_all = read_jsonl(TAGNT)
    tbesg = read_jsonl(TBESG)
    morphology = read_jsonl(MORPH)
    strong_original = read_jsonl(STRONG_ORIG)

    s_by_ref = collections.defaultdict(list)
    t_sbl_by_ref = collections.defaultdict(list)
    t_non_sbl_by_ref = collections.defaultdict(list)

    for row in sbl:
        s_by_ref[(row["book"], row["chapter"], row["verse"])].append(row)
    for row in tagnt_all:
        key = (row["book"], row["chapter"], row["verse"])
        (t_sbl_by_ref if is_sbl_row(row) else t_non_sbl_by_ref)[key].append(row)

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
    low_confidence = []
    verse_stats = []
    methods = collections.Counter()

    for ref in sorted(s_by_ref):
        ss = s_by_ref[ref]
        main_pairs = [(i, row) for i, row in enumerate(ss) if row.get("textual_status") != "double-bracketed"]
        bracket_pairs = [(i, row) for i, row in enumerate(ss) if row.get("textual_status") == "double-bracketed"]

        sbl_candidates = t_sbl_by_ref.get(ref, [])
        non_sbl_candidates = t_non_sbl_by_ref.get(ref, [])

        mapped = {}
        mapped.update(sequence_map(
            main_pairs,
            sbl_candidates,
            exact_method="normalized-exact",
            positional_method="positional-replace",
        ))

        bracket_mapped = sequence_map(
            bracket_pairs,
            non_sbl_candidates,
            exact_method="double-bracketed-exact",
            positional_method=None,
        )
        # Mark target pool so the correct row collection is used later.
        for i, (j, method) in bracket_mapped.items():
            mapped[i] = (j, method)

        for i, srow in enumerate(ss):
            if i not in mapped:
                candidates = non_sbl_candidates if srow.get("textual_status") == "double-bracketed" else sbl_candidates
                unmatched.append({
                    "token_id": srow["id"],
                    "book": srow["book"],
                    "chapter": srow["chapter"],
                    "verse": srow["verse"],
                    "position": srow["position"],
                    "surface": srow["surface"],
                    "textual_status": srow.get("textual_status","main"),
                    "reason": "no-TAGNT-row-aligned",
                    "tagnt_candidates": [x["greek"] for x in candidates],
                })
                continue

            j, method = mapped[i]
            if method == "double-bracketed-exact":
                trow = non_sbl_candidates[j]
            else:
                trow = sbl_candidates[j]

            raw_strong = trow.get("strongs") or None
            base = strong_base(raw_strong)
            tbesg_ids = list(tbesg_by_d.get(raw_strong, [])) if raw_strong else []
            if not tbesg_ids and base:
                tbesg_ids = list(tbesg_by_e.get(base, []))

            original_id = original_by_id.get(base) if base else None
            morphology_code = trow.get("grammar") or None
            morphology_components = morphology_parts(morphology_code)
            morphology_known = bool(morphology_components) and all(x in morph_codes for x in morphology_components)
            methods[method] += 1

            link = {
                "id": f"link:sbl-tagnt:{srow['book'].lower()}:{srow['chapter']}:{srow['verse']}:{srow['position']}",
                "token_id": srow["id"],
                "tagnt_row_id": trow["id"],
                "book": srow["book"],
                "chapter": srow["chapter"],
                "verse": srow["verse"],
                "token_position": srow["position"],
                "surface_sbl": srow["surface"],
                "surface_tagnt": trow["greek"],
                "textual_status": srow.get("textual_status","main"),
                "match_method": method,
                "normalized_equal": norm_greek(srow["surface"]) == norm_greek(trow["greek"]),
                "strongs": raw_strong,
                "morphology_code": morphology_code,
                "morphology_components": morphology_components,
                "morphology_known": morphology_known,
                "lemma": trow.get("dictionary_form"),
                "gloss": trow.get("gloss"),
                "spanish_translation": trow.get("spanish_translation"),
                "sub_meaning": trow.get("sub_meaning"),
                "editions": trow.get("editions"),
                "tbesg_entry_ids": tbesg_ids,
                "strong_original_id": original_id,
            }
            links.append(link)
            if method == "positional-replace":
                low_confidence.append(link)

        main_norm = [norm_greek(x["surface"]) for _, x in main_pairs]
        sbl_norm = [norm_greek(x["greek"]) for x in sbl_candidates]
        verse_stats.append({
            "book": ref[0],
            "chapter": ref[1],
            "verse": ref[2],
            "sbl_tokens": len(ss),
            "main_tokens": len(main_pairs),
            "double_bracketed_tokens": len(bracket_pairs),
            "tagnt_sbl_rows": len(sbl_candidates),
            "tagnt_non_sbl_rows": len(non_sbl_candidates),
            "mapped": sum(1 for i in range(len(ss)) if i in mapped),
            "main_exact_sequence": main_norm == sbl_norm,
        })

    linked_token_ids = [x["token_id"] for x in links]
    if len(linked_token_ids) != len(set(linked_token_ids)):
        raise RuntimeError("Duplicate SBL token links")

    coverage = len(links) / len(sbl) if sbl else 0
    if coverage < 0.98:
        raise RuntimeError(f"Alignment coverage too low: {coverage:.4%}")

    with (OUT / "sbl-tagnt-links.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for row in links:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    for filename, rows in [
        ("sbl-tagnt-unmatched.jsonl", unmatched),
        ("sbl-tagnt-low-confidence.jsonl", low_confidence),
        ("verse-alignment-stats.jsonl", verse_stats),
    ]:
        with (DERIVED / filename).open("w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    unknown_morph = collections.Counter(
        x["morphology_code"] for x in links
        if x["morphology_code"] and not x["morphology_known"]
    )
    (DERIVED / "unknown-morphology-codes.json").write_text(
        json.dumps(dict(unknown_morph.most_common()), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = {
        "sbl_tokens": len(sbl),
        "sbl_main_tokens": sum(x.get("textual_status") != "double-bracketed" for x in sbl),
        "sbl_double_bracketed_tokens": sum(x.get("textual_status") == "double-bracketed" for x in sbl),
        "tagnt_rows_total": len(tagnt_all),
        "tagnt_rows_marked_sbl": sum(len(x) for x in t_sbl_by_ref.values()),
        "linked_tokens": len(links),
        "coverage": coverage,
        "unmatched_tokens": len(unmatched),
        "methods": dict(methods),
        "low_confidence_positional_links": len(low_confidence),
        "links_with_unknown_morphology_code": sum(unknown_morph.values()),
        "unique_unknown_morphology_codes": len(unknown_morph),
        "links_with_strong_but_no_tbesg_entry": sum(bool(x["strongs"]) and not x["tbesg_entry_ids"] for x in links),
        "links_with_strong_original": sum(x["strong_original_id"] is not None for x in links),
        "verses_total": len(s_by_ref),
        "verses_main_exact_sequence": sum(x["main_exact_sequence"] for x in verse_stats),
    }
    (DERIVED / "sbl-tagnt-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
