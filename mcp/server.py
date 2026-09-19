from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from adapters import ElRelatoRepository, GospelRepository

ROOT = Path(__file__).resolve().parents[1]
gospels = GospelRepository(ROOT)
el_relato = ElRelatoRepository(ROOT)

INSTRUCTIONS = """Two independent interfaces are exposed.
1. gospels_* tools expose the four canonical Gospels (Matthew, Mark, Luke, John) and their philological/source evidence.
2. el_relato_* tools expose the editorial harmony 'El Relato'.
Never present El Relato as a fifth Gospel or as a canonical biblical source. El Relato is an editorial work derived from canonical Gospel passages. When combining results, preserve provenance and identify which interface each claim came from.
"""

mcp = MCPServer("Gospels + El Relato", instructions=INSTRUCTIONS)


@mcp.tool()
def gospels_get_passage(book: str, chapter: int, verse_start: int | None = None, verse_end: int | None = None) -> dict[str, Any]:
    """Return Greek text for a canonical Gospel passage with source provenance. Books: Matthew, Mark, Luke, John (aliases accepted)."""
    return gospels.get_passage(book, chapter, verse_start, verse_end)


@mcp.tool()
def gospels_get_tokens(book: str, chapter: int, verse: int) -> dict[str, Any]:
    """Return token-level Greek evidence for one canonical Gospel verse, including lemma/morphology/Strong fields when present."""
    return gospels.get_tokens(book, chapter, verse)


@mcp.tool()
def gospels_get_strong(strong: str) -> dict[str, Any]:
    """Look up a Greek Strong identifier (for example G3056) in the normalized lexical sources."""
    return gospels.get_strong(strong)


@mcp.tool()
def gospels_get_manuscript_evidence(book: str, chapter: int, verse: int) -> dict[str, Any]:
    """Return manuscript/transcription evidence available in the repository for one canonical Gospel verse."""
    return gospels.get_manuscript_evidence(book, chapter, verse)


@mcp.tool()
def gospels_translation_packet(book: str, chapter: int, verse_start: int | None = None, verse_end: int | None = None, target_language: str = "es-419", translation_preferences: str = "") -> dict[str, Any]:
    """Build an auditable source packet for an AI to produce a personalized translation."""
    return gospels.translation_packet(book, chapter, verse_start, verse_end, target_language, translation_preferences)


@mcp.tool()
def el_relato_get_scene(scene_number: int, locale: str | None = None) -> dict[str, Any]:
    """Return one scene from the independent editorial work El Relato. This is not a canonical Gospel interface."""
    return el_relato.get_scene(scene_number, locale)


@mcp.tool()
def el_relato_list_scenes(chapter_number: str | None = None) -> dict[str, Any]:
    """List the editorial scenes of El Relato, optionally filtered by its internal chapter number."""
    return el_relato.list_scenes(chapter_number)


@mcp.tool()
def interfaces_about() -> dict[str, Any]:
    """Describe the strict semantic boundary between the canonical Gospels interface and the El Relato editorial interface."""
    return {
        "interfaces": {
            "gospels": {"type": "canonical_biblical_source_interface", "books": ["Matthew", "Mark", "Luke", "John"], "namespace": "gospels_*", "data_root": "data/normalized"},
            "el_relato": {"type": "editorial_harmony_interface", "namespace": "el_relato_*", "data_root": "book", "derived_from": ["Matthew", "Mark", "Luke", "John"]},
        },
        "invariant": "El Relato must never be represented as a Gospel, a fifth canonical book, or a source at the same authority level as Matthew, Mark, Luke, or John.",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
