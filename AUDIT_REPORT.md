# El-Relato — Audit Report

Generated: 2026-09-19T05:28:15+00:00

**Overall: PASS_WITH_BLOCKERS**

- PASS: 22
- WARN / BLOCKED: 4
- FAIL: 0

## Checks

### ✅ gov:README.md — Required project file: README.md

### ✅ gov:PROJECT_PLAN.md — Required project file: PROJECT_PLAN.md

### ✅ gov:STATUS.md — Required project file: STATUS.md

### ✅ gov:docs/ARCHITECTURE.md — Required project file: docs/ARCHITECTURE.md

### ✅ gov:docs/LOOP_PROTOCOL.md — Required project file: docs/LOOP_PROTOCOL.md

### ✅ gov:docs/ID_CONVENTIONS.md — Required project file: docs/ID_CONVENTIONS.md

### ✅ corpus:sblgnt — SBLGNT Gospel structured corpus
~~~json
{
  "edition": "edition:sblgnt:2010",
  "verses": 3768,
  "tokens": 64686,
  "verses_by_book": {
    "Matthew": 1068,
    "Mark": 673,
    "Luke": 1149,
    "John": 878
  },
  "tokens_by_book": {
    "Matthew": 18329,
    "Mark": 11286,
    "Luke": 19446,
    "John": 15625
  }
}
~~~

### ✅ corpus:alignment — SBLGNT ↔ TAGNT/Strong/morphology alignment
193 SBLGNT tokens remain explicitly unmatched; positional links remain auditable.
~~~json
{
  "sbl_tokens": 64686,
  "sbl_main_tokens": 64298,
  "sbl_double_bracketed_tokens": 388,
  "tagnt_rows_total": 66926,
  "tagnt_rows_marked_sbl": 64234,
  "linked_tokens": 64493,
  "coverage": 0.9970163559348236,
  "unmatched_tokens": 193,
  "methods": {
    "normalized-exact": 63524,
    "positional-replace": 639,
    "double-bracketed-exact": 330
  },
  "low_confidence_positional_links": 639,
  "links_with_unknown_morphology_code": 0,
  "unique_unknown_morphology_codes": 0,
  "links_with_strong_but_no_tbesg_entry": 0,
  "links_with_strong_original": 64452,
  "verses_total": 3768,
  "verses_main_exact_sequence": 3098
}
~~~

### ⚠️ corpus:alignment-exceptions — Alignment exceptions remain explicit
These are not silently imputed; see data/derived/alignment/sbl-tagnt-unmatched.jsonl.
~~~json
{
  "unmatched_tokens": 193,
  "low_confidence_positional_links": 639
}
~~~

### ✅ corpus:stepbible — STEPBible normalized datasets
~~~json
{
  "TBESG": {
    "entries": 11035,
    "unique_eStrong": 10847,
    "with_dStrong": 11035
  },
  "TAGNT": {
    "rows": 66926,
    "rows_by_book": {
      "Matthew": 18887,
      "Mark": 11845,
      "Luke": 20120,
      "John": 16074
    },
    "rows_marked_SBL_by_book": {
      "Matthew": 18307,
      "Mark": 11102,
      "Luke": 19412,
      "John": 15413
    },
    "unique_references": 3779
  },
  "TEGMC": {
    "full_morphology_codes": 1644,
    "unique_codes": 1644
  }
}
~~~

### ✅ corpus:strong-original — Strong historical Greek dictionary
~~~json
{
  "entries": 5523,
  "min_number": 1,
  "max_number": 5624,
  "cross_references": 7056
}
~~~

### ✅ corpus:apparatus — SBLGNT edition apparatus
~~~json
{
  "units": 3672,
  "units_by_book": {
    "Matthew": 827,
    "Mark": 930,
    "Luke": 1142,
    "John": 773
  },
  "parse_status": {
    "parsed": 3672
  },
  "edition_sigla_counts": {
    "RP": 3672,
    "NA28": 3670,
    "Treg": 3670,
    "WH": 3648,
    "NIV": 150,
    "WHmarg": 14,
    "Holmes": 12,
    "TR": 2,
    "Greeven": 1
  },
  "unknown_tail_tokens": {}
}
~~~

### ✅ ms:core-codices — Vaticanus + Sinaiticus Gospel facsimile mirror
~~~json
{
  "planned_files": 269,
  "mirrored_files": 269,
  "missing_files": 0,
  "total_bytes": 206287520
}
~~~

### ✅ ms:p75 — P75 facsimile mirror
~~~json
{
  "planned": 108,
  "mirrored": 108,
  "missing": 0,
  "total_bytes": 201965150
}
~~~

### ⚠️ ms:csntm-core — Core papyrus facsimile preservation
P66/P104 source-specific CSNTM gaps are superseded by complete institutional fallbacks. P45 composite renderings remain a source-specific gap while component images are preserved.
~~~json
{
  "unresolved_source_specific": [
    {
      "manuscript": "P45",
      "failed": 2
    }
  ]
}
~~~

### ✅ ms:fallbacks — Institutional fallback facsimiles
~~~json
{
  "P66": {
    "mirrored_or_present": 163,
    "failed": 0,
    "total_bytes": 835837966,
    "complete": true
  },
  "P104": {
    "mirrored_or_present": 2,
    "failed": 0,
    "total_bytes": 9277363,
    "complete": true
  },
  "P137": {
    "mirrored_or_present": 0,
    "failed": 1,
    "total_bytes": 0,
    "complete": false
  },
  "P137_publication_pdf_preserved": true
}
~~~

### ✅ ms:evidence — Integrated normalized manuscript evidence
Canonical evidence combines CSNTM, Bodmer, Oxford, P75 Vatican, P137 EES, Sinaiticus and IGNTP transcription attestations.
~~~json
{
  "images": 645,
  "witness_attestations": 5834,
  "by_manuscript": {
    "p4": {
      "images": 10,
      "attestations": 94,
      "attestations_with_images": 94,
      "attestations_with_transcriptions": 0
    },
    "p45": {
      "images": 215,
      "attestations": 521,
      "attestations_with_images": 521,
      "attestations_with_transcriptions": 0
    },
    "p52": {
      "images": 2,
      "attestations": 5,
      "attestations_with_images": 5,
      "attestations_with_transcriptions": 5
    },
    "p66": {
      "images": 308,
      "attestations": 830,
      "attestations_with_images": 3,
      "attestations_with_transcriptions": 830
    },
    "p75": {
      "images": 108,
      "attestations": 626,
      "attestations_with_images": 0,
      "attestations_with_transcriptions": 626
    },
    "p104": {
      "images": 2,
      "attestations": 7,
      "attestations_with_images": 7,
      "attestations_with_transcriptions": 0
    },
    "p137": {
      "images": 0,
      "attestations": 6,
      "attestations_with_images": 0,
      "attestations_with_transcriptions": 0
    },
    "01": {
      "images": 0,
      "attestations": 3745,
      "attestations_with_images": 0,
      "attestations_with_transcriptions": 3745
    },
    "03": {
      "images": 0,
      "attestations": 0,
      "attestations_with_images": 0,
      "attestations_with_transcriptions": 0
    }
  }
}
~~~

### ✅ tx:sinaiticus — Sinaiticus Gospel transcription
~~~json
{
  "source_version": "1.95",
  "book_div_ids": {
    "Matthew": "B-B33-33-MATT",
    "Mark": "B-B34-34-MARK",
    "Luke": "B-B35-35-LUKE",
    "John": "B-B36-36-JOHN"
  },
  "normalized_units": 3745,
  "units_by_book": {
    "John": 866,
    "Luke": 1150,
    "Mark": 661,
    "Matthew": 1068
  },
  "unmapped_ab_units": 4,
  "unmapped_samples": [
    {
      "book": "Matthew",
      "id": "V-B33K1V0-33-MATT",
      "n": "0"
    },
    {
      "book": "Mark",
      "id": "V-B34K1V0-34-MARK",
      "n": "0"
    },
    {
      "book": "Luke",
      "id": "V-B35K1V0-35-LUKE",
      "n": "0"
    },
    {
      "book": "John",
      "id": "V-B36K1V0-36-JOHN",
      "n": "0"
    }
  ]
}
~~~

### ✅ tx:igntp — IGNTP P52/P66/P75 transcriptions
Raw scholarly TEI is preserved and a diplomatic verse-level view is regenerated from it.
~~~json
{
  "raw_items": [
    {
      "manuscript": "P52",
      "complete": true
    },
    {
      "manuscript": "P66",
      "complete": true
    },
    {
      "manuscript": "P75",
      "complete": true
    }
  ],
  "normalized": {
    "manuscripts": {
      "P52": {
        "normalized_units": 5,
        "features": {
          "gap": 8,
          "supplied": 71,
          "unclear": 12,
          "apparatus": 0,
          "nomina_sacra": 2
        }
      },
      "P66": {
        "normalized_units": 830,
        "features": {
          "gap": 179,
          "supplied": 2515,
          "unclear": 1108,
          "apparatus": 440,
          "nomina_sacra": 557
        }
      },
      "P75": {
        "normalized_units": 626,
        "features": {
          "gap": 20,
          "supplied": 2637,
          "unclear": 2147,
          "apparatus": 51,
          "nomina_sacra": 345
        }
      }
    },
    "total_units": 1461
  }
}
~~~

### ✅ integrity:checksums — Preservation SHA-256 manifest
~~~json
{
  "files": 35,
  "generated_at": "2026-09-19T04:01:16+00:00"
}
~~~

### ✅ integrity:license-registry — Source license/permission registry
~~~json
{
  "sources": 23,
  "license_entries": 23
}
~~~

### ✅ query:db — Integrated reproducible SQLite query layer
~~~json
{
  "tokens": 64686,
  "linked_tokens": 64493,
  "strong_extended_entries": 11035,
  "strong_original_entries": 5523,
  "morphology_codes": 1644,
  "edition_apparatus_units": 3672,
  "manuscripts": 9,
  "facsimiles": 269,
  "manuscript_images": 645,
  "witness_attestations": 5834,
  "transcription_units": 5206,
  "database_bytes": 37838848
}
~~~

### ✅ query:app — Local research interface and self-test

### ⚠️ blocker:intf — INTF/NTVMR exhaustive catalogue harvest remains blocked
The nucleus is preserved, but the declared exhaustive scope (all Gospel papyri + majuscules through s. V) is not yet certified complete.

### ✅ backup:procedure — Git + LFS backup/restore procedure
Offline restore from Git bundle + LFS archive is tested in CI.
~~~json
{
  "tested_at": "2026-09-19T05:15:52+00:00",
  "head": "e34d9bc72b4e068b32bae2e08d52faef310f359c",
  "restore_test": "PASS",
  "git_fsck": "PASS",
  "git_lfs_fsck": "PASS",
  "repository_validation": "PASS",
  "query_database_rebuild": "PASS",
  "app_self_test": "PASS",
  "bundle_bytes": 22507469,
  "lfs_archive_bytes": 2434508800,
  "lfs_tracked_entries": 924
}
~~~

### ⚠️ backup:independent — Independent off-GitHub backup
A second storage destination and recorded copy are still required.
