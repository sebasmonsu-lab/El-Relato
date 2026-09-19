# El-Relato v0.1.0-internal

Fecha: 2026-09-19

## Alcance de esta versión

Primera versión interna auditable del archivo/corpus de investigación de los cuatro Evangelios.

### Corpus griego y análisis lingüístico
- SBLGNT preservado en TXT/XML con aparato.
- 3.768 versículos y 64.686 tokens.
- 64.493 tokens vinculados a TAGNT / Strong / morfología.
- Cobertura de alineación: 99,7016%.
- 193 tokens no alineados y 639 enlaces posicionales quedan explícitamente auditables.
- TBESG: 11.035 entradas.
- TEGMC: 1.644 códigos.
- Strong histórico: 5.523 entradas.
- Aparato SBLGNT: 3.672 unidades de comparación entre ediciones.

### Evidencia manuscrita
Núcleo preservado/documentado:
- P4
- P45
- P52
- P66
- P75
- P104
- P137
- Codex Sinaiticus (GA 01)
- Codex Vaticanus (GA 03)

Incluye, según disponibilidad:
- facsímiles;
- manifiestos IIIF;
- transcripciones académicas;
- hashes;
- mapping pasaje ↔ manuscrito ↔ imagen/transcripción.

Estado integrado:
- 645 imágenes normalizadas;
- 5.834 witness attestations;
- 5.206 unidades de transcripción;
- facsímiles completos de Evangelios de Vaticanus + Sinaiticus;
- P75 completo;
- fallbacks institucionales completos para P66 y P104;
- publicación con imagen/texto preservada para P137.

### Consulta
- SQLite reproducible.
- interfaz local de investigación;
- self-test y acceptance tests verdes.

### Integridad y restauración
- Git LFS para binarios;
- SHA-256 y manifests;
- auditoría automática;
- restore test desde Git bundle + LFS archive:
  - git fsck: PASS
  - git lfs fsck: PASS
  - validación: PASS
  - rebuild SQLite: PASS
  - app self-test: PASS

## Limitaciones conocidas

1. **INTF/NTVMR exhaustivo**: el inventario completo de todos los papiros de Evangelios + majúsculos hasta s. V todavía no está certificado por timeouts/API. El núcleo sí está preservado.
2. **Alineación lingüística**: 193 tokens SBLGNT no tienen enlace TAGNT y 639 enlaces son posicionales. No se imputan silenciosamente.
3. **P45**: faltan dos renderings composites específicos de CSNTM; las imágenes componentes están preservadas.
4. **Aparato manuscrito exhaustivo**: el repo distingue aparato entre ediciones y witness attestations, pero todavía no reemplaza un aparato crítico manuscrito completo ECM/NA/INTF.
5. **Backup externo**: el restore local/CI está probado. La copia independiente fuera de GitHub queda sujeta a la transferencia del archivo LFS fragmentado.

## Criterio de uso

Esta versión es apta para:
- investigación reproducible;
- consulta palabra por palabra;
- Strong/morfología;
- navegación de evidencia manuscrita preservada;
- desarrollo de herramientas y análisis sobre El-Relato.

No debe presentarse como una edición crítica exhaustiva de todos los testigos griegos conocidos.
