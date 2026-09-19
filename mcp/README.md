# MCP interfaces

This directory exposes two deliberately independent MCP interfaces over the repository.

## 1. `gospels_*` — canonical Gospel source interface

Scope: **Matthew, Mark, Luke and John only**. It reads normalized Greek/source datasets under `data/normalized/` and exposes passage, token, Strong, manuscript-evidence and translation-packet tools.

Strong data is lexical/indexing evidence; it is not labelled as "the original Greek".

## 2. `el_relato_*` — El Relato editorial interface

Scope: the editorial harmony **El Relato**, stored under `book/`. It exposes scenes and available generated translations.

**Invariant:** El Relato is not a fifth Gospel and must never be represented at the same canonical/source level as Matthew, Mark, Luke or John. A client may query both interfaces in one conversation, but provenance must remain explicit.

## Run locally

```bash
cd mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
python server.py
```

The Streamable HTTP endpoint is `http://127.0.0.1:8000/mcp`.

Recommended public endpoint convention: `https://mcp.elrelato.org/mcp`.

## Tools

- `gospels_get_passage`
- `gospels_get_tokens`
- `gospels_get_strong`
- `gospels_get_manuscript_evidence`
- `gospels_translation_packet`
- `el_relato_get_scene`
- `el_relato_list_scenes`
- `interfaces_about`
