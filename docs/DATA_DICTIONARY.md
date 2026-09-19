# Diccionario de datos

## Source
Un recurso upstream identificable: manuscrito digital, transcripción, edición, léxico, morfología o metadata.

ID: `src:<namespace>:<slug>`

## Manuscript
Un testigo manuscrito griego registrado mediante Gregory–Aland.

ID: `ms:ga:<ga>`

## Passage
Una unidad bíblica canónica usada para navegación.

ID: `passage:<book>:<chapter>:<verse>`

## Edition
Una edición textual, actualmente SBLGNT como base estructurada.

ID: `edition:<slug>:<version>`

## Token
Una palabra de una edición, con posición exacta dentro de un versículo.

ID: `token:<edition>:<book>:<chapter>:<verse>:<position>`

Campos importantes:
- `surface`
- `prefix_before`
- `punctuation_after`
- `textual_status`

## SBL ↔ TAGNT Link
Enlace auditable entre un token SBLGNT y una fila TAGNT.

Métodos:
- `normalized-exact`
- `double-bracketed-exact`
- `positional-replace` (menor confianza, nunca oculto)

## StrongEntry
Entrada Extended Strong derivada de TBESG.

## StrongOriginalEntry
Entrada del diccionario histórico de Strong preservado en XML.

Estas entidades son distintas.

## Morphology
Código morfológico TEGMC normalizado.

## EditionApparatusUnit
Diferencia entre ediciones (WH, Treg, NA28, RP, etc.).

**No equivale a una variante atestiguada por manuscritos.**

## ManuscriptImage
Archivo visual preservado de un manuscrito.

ID: `image:<source>:...`

## TranscriptionUnit
Vista diplomática por pasaje derivada de una transcripción académica raw.

El raw TEI/XML sigue siendo autoritativo.

## WitnessAttestation
Relación:

`manuscrito ↔ pasaje ↔ imágenes/transcripciones`

No implica automáticamente apoyo a una lectura textual específica. Para eso se requiere `Reading`/aparato de testigos.

## VariantUnit / Reading
Modelo reservado para variantes con evidencia manuscrita explícita.

No se generan variantes de testigos a partir de traducciones ni del aparato entre ediciones.

## Raw / Normalized / Derived

- **Raw:** copia exacta preservada.
- **Normalized:** representación común y validada.
- **Derived:** índices, reportes, SQLite y UI; regenerables.
