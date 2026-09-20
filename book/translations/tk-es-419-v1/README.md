# El Relato — TK es-419 v1

Estado canónico de la traducción del BOOK al español latinoamericano.

## Estado

- Edición: `edition:el-relato:tk-es-419:v1`
- Base griega: `edition:el-relato:grc-sblgnt-2010:v1`
- Escenas: **120/120**
- Unidades: **4.123/4.123**
- Validación estructural: **PASS**
- Traducción generada/revisada con GPT-5.6 Sol: **2.431 unidades**
- Legado conservado sin atribución de modelo: **1.692 unidades**
- Revisión humana/filológica: **requerida antes de publicación editorial definitiva**

## Fuente de verdad

La fuente griega canónica es `book/el-relato-book.sqlite`.
No hay un export griego paralelo dentro de `book/translations/`.

La traducción de trabajo vive únicamente en:

`book/translations/tk-es-419-v1/generated/scene-001.jsonl` … `scene-120.jsonl`.

## Validación

Reporte persistido:

`book/translations/tk-es-419-v1/validation-report.json`

Valida contra la edición griega canónica de la SQLite:
- cobertura completa;
- mismo orden de `unit_id`;
- ausencia de faltantes y extras;
- ausencia de duplicados;
- ausencia de textos vacíos.

## Consolidación segura

El importador es:

`scripts/consolidate_book_translation.py`

Por defecto es **read-only**:

```bash
python scripts/consolidate_book_translation.py
```

Sólo modifica la SQLite con autorización explícita mediante:

```bash
python scripts/consolidate_book_translation.py --apply
```

Es idempotente: si la edición ya existe con los mismos 4.123 textos, no hace nada; si existe con contenido distinto o incompleto, aborta y no sobrescribe.

## Provenance

No se atribuye a Copilot ningún texto cuyo modelo no esté demostrado.
Las filas antiguas sin provenance permanecen como `legacy-unattributed`.
Las filas generadas en la fase actual conservan `model: GPT-5.6 Sol`.
