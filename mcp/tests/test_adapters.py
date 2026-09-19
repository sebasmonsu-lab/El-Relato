from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp"))

from adapters import ElRelatoRepository, GospelRepository

def test_gospels_are_canonical_and_restricted():
    repo = GospelRepository(ROOT)
    result = repo.get_passage("John", 1, 1, 1)
    assert result["interface"] == "gospels"
    assert result["canonical"] is True
    assert result["book"] == "John"
    assert result["verses"]
    assert "Ἐν" in result["verses"][0]["text"]

def test_el_relato_is_editorial_not_canonical():
    repo = ElRelatoRepository(ROOT)
    result = repo.get_scene(1)
    assert result["interface"] == "el_relato"
    assert result["canonical"] is False
    assert result["work_type"] == "editorial_harmony"

def test_el_relato_cannot_enter_gospels_namespace():
    repo = GospelRepository(ROOT)
    try:
        repo.get_passage("El Relato", 1)
    except ValueError:
        return
    raise AssertionError("El Relato must not be accepted as a Gospel book")
