# Arquitectura de El-Relato

## Capas

### 1. RAW / Preservation
Copias exactas de fuentes externas.

`vendor/`
- repositorios/datasets completos o subconjuntos preservados.

`sources/manuscripts/<id>/raw/`
- imágenes;
- transcripciones;
- metadata original.

### 2. Provenance
`data/manifests/`
- fuente;
- versión;
- URLs;
- hashes;
- estado de mirror.

### 3. Normalized
`data/normalized/`
- manuscritos;
- versos;
- tokens;
- léxicos;
- morfología;
- variantes.

Nunca reemplaza RAW.

### 4. Derived
`data/derived/`
- índices;
- estadísticas;
- SQLite/DuckDB;
- búsquedas;
- relaciones.

Siempre regenerable.

### 5. Validation
`schemas/`
`scripts/validate/`
`.github/workflows/`

### 6. Application
`app/` o proyecto separado.

La interfaz no será fuente de verdad.

## Entidades centrales

`Source`
→ recurso upstream.

`Manuscript`
→ testigo físico/catalográfico.

`ManuscriptImage`
→ imagen/folio.

`TranscriptionUnit`
→ unidad de transcripción vinculada al folio.

`Passage`
→ libro/capítulo/versículo o rango.

`TextEdition`
→ SBLGNT u otra edición.

`Token`
→ palabra concreta de una edición.

`Lexeme`
→ lema.

`StrongEntry`
→ identificador Strong + fuente de glosas.

`Morphology`
→ análisis gramatical.

`VariantUnit`
→ lugar de variación.

`Reading`
→ lectura dentro de una variante.

`WitnessAttestation`
→ relación testigo ↔ lectura/pasaje.

## Regla de soberanía
Los links externos son referencias, nunca el único lugar donde reside un recurso que hayamos decidido preservar.
