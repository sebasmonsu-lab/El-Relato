# El-Relato — Plan maestro

## Misión

Construir un corpus privado, preservado, trazable y consultable de los cuatro Evangelios que permita ir desde el facsímil manuscrito hasta el análisis léxico y morfológico de cada palabra, sin depender de la disponibilidad futura de fuentes externas.

## Principios no negociables

1. **Preservación:** siempre que tengamos acceso al recurso, conservar copia local además del enlace externo.
2. **Trazabilidad:** cada archivo debe registrar procedencia, URL, institución, fecha de captura, versión y checksum.
3. **Separación de niveles:** manuscrito ≠ transcripción ≠ edición crítica ≠ léxico ≠ traducción.
4. **Reproducibilidad:** todo dato derivado debe poder regenerarse desde fuentes preservadas.
5. **No pérdida:** ningún bloqueo se elimina del plan; se marca y se resuelve.
6. **Formato máquina-legible:** la información central debe existir en JSON/CSV/TSV/XML además de documentación humana.
7. **Validación automática:** schemas, checksums, pruebas y CI antes de considerar completo un bloque.
8. **Portabilidad:** el corpus debe poder reconstruirse fuera de GitHub.

---

# Fases

## Fase 0 — Gobierno y control del proyecto
**Objetivo:** que el proyecto sea retomable sin depender del chat.

Entregables:
- PROJECT_PLAN.md
- STATUS.md
- docs/LOOP_PROTOCOL.md
- docs/ARCHITECTURE.md
- decisiones técnicas registradas
- issues/epics de GitHub

**Gate:** toda tarea futura tiene estado, dependencia y criterio de finalización.

## Fase 1 — Inventario maestro de fuentes
Crear un catálogo exhaustivo de:
- manuscritos;
- transcripciones;
- ediciones críticas;
- léxicos;
- Strong;
- morfología;
- traducciones que decidamos conservar;
- metadatos académicos;
- repositorios institucionales.

Campos mínimos:
- id interno;
- título;
- categoría;
- institución;
- URL;
- identificador externo;
- versión/revisión;
- licencia declarada;
- fecha de captura;
- estado de mirror;
- checksum;
- notas.

**Gate:** ningún archivo preservado carece de entrada de manifiesto.

## Fase 2 — Mirror íntegro de SBLGNT
Preservar:
- Mateo, Marcos, Lucas, Juan TXT;
- XML;
- aparato disponible en upstream que corresponda;
- README;
- About;
- LICENSE;
- commit/tree upstream.

**Estado:** texto y XML de los cuatro Evangelios ya preservados.

**Gate:** checksum e inventario de todos los archivos seleccionados.

## Fase 3 — Mirror íntegro STEPBible
Preservar para los Evangelios:
- README;
- TBESG — Extended Strong Greek;
- TEGMC — Greek morphology;
- TAGNT Mat–Jhn;
- archivos auxiliares requeridos para interpretar campos/códigos;
- versión/tree upstream.

### Estrategia para archivos grandes
Descarga/copia por partes dentro de límites de API.
Cada parte debe incluir:
- índice de secuencia;
- tamaño;
- hash;
- procedimiento reproducible de ensamblado;
- hash final esperado.

**Gate:** TBESG y TAGNT Mat–Jhn reconstruibles byte a byte desde el repo.

## Fase 4 — Manuscritos: inventario exhaustivo por Evangelio
Primera capa núcleo:
- 𝔓4
- 𝔓45
- 𝔓52
- 𝔓66
- 𝔓75
- 𝔓104
- 𝔓137
- Codex Sinaiticus ℵ/01
- Codex Vaticanus B/03

Segunda capa:
- ampliar a todos los papiros tempranos relevantes;
- unciales tempranos relevantes;
- testigos adicionales cuando tengan valor textual significativo.

Por manuscrito:
- Gregory–Aland;
- sigla;
- fecha/rango;
- material;
- contenido;
- institución;
- catálogo;
- páginas/folios;
- URLs oficiales;
- bibliografía mínima;
- estado de imágenes;
- estado de transcripción.

**Gate:** cada Evangelio tiene cobertura documentada de sus testigos más antiguos y principales.

## Fase 5 — Preservación de facsímiles
Descargar/copiar imágenes públicas accesibles de los manuscritos seleccionados.

Estructura por manuscrito:
```
sources/manuscripts/<ID>/
  manifest.json
  provenance.md
  images/
  transcription/
  metadata/
  checksums.sha256
```

**Gate:** para cada imagen sabemos exactamente qué folio/página es, de dónde vino y su hash.

## Fase 6 — Transcripciones manuscritas
Preservar transcripciones diplomáticas disponibles y normalizarlas sin destruir el original.

Capas:
- `raw/`: copia exacta upstream;
- `normalized/`: formato común;
- `mapping/`: relación folio ↔ pasaje.

**Gate:** una transcripción normalizada nunca reemplaza ni altera la copia raw.

## Fase 7 — Corpus canónico de los cuatro Evangelios
Crear una representación común:
- libro;
- capítulo;
- versículo;
- token;
- forma superficial;
- lema;
- transliteración;
- Strong;
- morfología;
- posición;
- puntuación;
- fuente textual.

Formatos:
- JSONL;
- CSV/TSV;
- SQLite o DuckDB derivado;
- Markdown solo como vista humana.

**Gate:** cada token puede trazarse a su fuente textual.

## Fase 8 — Strong y capa léxica
Por lema:
- Strong ID;
- forma griega;
- transliteración;
- glosas Strong;
- TBESG;
- otras fuentes públicas acordadas;
- ocurrencias en Evangelios;
- estadísticas;
- formas flexionadas.

Regla:
No presentar una glosa como “el significado” sin distinguir fuente y contexto.

**Gate:** consulta bidireccional token → lema → Strong → ocurrencias.

## Fase 9 — Morfología
Normalizar códigos morfológicos y crear esquema humano/máquina:
- parte de discurso;
- caso;
- número;
- género;
- persona;
- tiempo;
- voz;
- modo;
- grado;
- campos especiales.

**Gate:** 100% de tokens etiquetados cuando la fuente disponga de análisis.

## Fase 10 — Variantes textuales
Modelar variantes separando:
- lugar de variación;
- lectura;
- testigos;
- fuente del aparato;
- certeza/metadatos;
- notas editoriales.

Nunca inferir variantes desde traducciones.

**Gate:** las variantes incluidas tienen evidencia citada y procedencia identificable.

## Fase 11 — Relación manuscrito ↔ pasaje
Construir índice:
```
Evangelio:capítulo:versículo
  -> manuscritos que preservan el pasaje
  -> folios/imágenes
  -> transcripciones
  -> lectura
```

**Gate:** desde un versículo se puede navegar hacia la evidencia manuscrita disponible.

## Fase 12 — Provenance y checksums
Generar:
- SHA-256 por archivo;
- manifest por recurso;
- manifest global;
- fecha de ingestión;
- URL original;
- versión upstream;
- hash upstream cuando exista.

**Gate:** verificación automática completa sin errores.

## Fase 13 — Schemas y validación
JSON Schema para:
- source;
- manuscript;
- witness coverage;
- verse;
- token;
- lexeme;
- variant;
- provenance.

Validadores automáticos.

**Gate:** CI rechaza datos inválidos.

## Fase 14 — Pipeline reproducible
Scripts para:
- ingest;
- fragmentación/ensamblado de archivos grandes;
- normalización;
- hashes;
- validación;
- generación de índices;
- exportación.

**Gate:** un checkout nuevo puede reconstruir los derivados.

## Fase 15 — Índices y motor de consulta
Consultas objetivo:
- Strong → todas las ocurrencias;
- lema → formas;
- palabra → pasajes;
- versículo → tokens;
- versículo → manuscritos;
- manuscrito → pasajes;
- variantes de un pasaje;
- palabras de Jesús (fase posterior, con criterio explícito de fuente);
- búsquedas semánticas como capa derivada, nunca sustituto del corpus.

**Gate:** suite de consultas de referencia produce resultados reproducibles.

## Fase 16 — Documentación de investigación
Crear guías:
- cómo interpretar Strong;
- cómo leer morfología;
- qué es un manuscrito;
- qué es una edición crítica;
- cómo leer una variante;
- cómo citar El-Relato;
- limitaciones metodológicas.

**Gate:** un tercero puede usar el corpus sin conocer su implementación.

## Fase 17 — Interfaz
Primera versión:
- búsqueda por cita;
- griego;
- tokenización;
- Strong;
- morfología;
- manuscritos disponibles;
- links/copia local;
- variantes.

Arquitectura desacoplada del corpus.

**Gate:** interfaz consume exclusivamente datos derivados reproducibles.

## Fase 18 — Respaldo y soberanía
Mínimo:
- GitHub privado;
- bundle Git periódico;
- snapshot externo;
- export de objetos Git LFS si se usa;
- manifests/hashes;
- procedimiento documentado de restauración.

Ideal:
- segundo remote (GitLab/self-hosted o almacenamiento frío).

**Gate:** restauración probada desde un backup independiente.

## Fase 19 — Auditoría y release
Auditar:
- completitud;
- enlaces rotos;
- hashes;
- schemas;
- cobertura por Evangelio;
- fuentes sin mirror;
- archivos sin provenance;
- datos derivados no reproducibles.

Generar release/tag interno.

**Gate:** cero pendientes silenciosos; todo faltante aparece en STATUS.md.

---

# Orden de ejecución inmediato

1. Gobierno/estado/arquitectura.
2. Completar STEPBible grande en fragmentos.
3. Terminar manifests + hashes de SBLGNT/STEPBible.
4. Profundizar inventario de manuscritos.
5. Copiar transcripciones/facsímiles disponibles.
6. Definir schemas.
7. Construir corpus tokenizado.
8. Unir Strong + morfología.
9. Construir witness coverage y variantes.
10. Validación + CI.
11. Consultas.
12. Interfaz.
13. Backup independiente.
14. Auditoría final.
