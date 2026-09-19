# El-Relato — Estado vivo

Última actualización: 2026-09-19

## Estado general
**Fase activa:** corpus lingüístico + preservación de manuscritos.  
**Regla operativa:** un bloqueo se registra y se deja abierto; el proyecto continúa por el siguiente bloque independiente y luego vuelve a los bloqueos.

## Completado

### Gobierno / arquitectura
- [x] Repositorio privado `sebasmonsu-lab/El-Relato`.
- [x] PROJECT_PLAN.md.
- [x] docs/ARCHITECTURE.md.
- [x] docs/LOOP_PROTOCOL.md.
- [x] Convenciones de IDs.
- [x] 14 epics en GitHub Issues.
- [x] Schemas iniciales de toda la cadena de datos.
- [x] CI de validación activo.
- [x] Workflows escritores con rebase/reintento para evitar non-fast-forward.

### SBLGNT
- [x] Mateo, Marcos, Lucas y Juan TXT.
- [x] Mateo, Marcos, Lucas y Juan XML estructurado.
- [x] Aparato SBLGNT de los cuatro Evangelios en TXT.
- [x] Aparato SBLGNT de los cuatro Evangelios en XML.
- [x] README / About / LICENSE upstream.
- [x] Corpus estructurado generado desde XML.
- [x] **3.768 versículos**.
- [x] **64.686 tokens**.
- [x] Puntuación preservada separadamente de cada token.

### STEPBible
- [x] README upstream.
- [x] TEGMC.
- [x] TBESG completo: 4.736.912 bytes, reconstruido y verificado contra blob Git upstream.
- [x] TAGNT Mat–Jhn completo: 14.300.601 bytes, reconstruido y verificado contra blob Git upstream.
- [x] TBESG normalizado: **11.035 entradas / 10.847 eStrong únicos**.
- [x] TAGNT normalizado: **66.926 filas**.
- [x] TEGMC normalizado: **1.644 códigos morfológicos**.

### Strong histórico
- [x] Strong Greek Dictionary XML v1.9 preservado.
- [x] README/licencia upstream preservados.
- [x] **5.523 entradas** normalizadas.
- [x] **7.056 referencias cruzadas** Strong preservadas.
- [x] Separación explícita entre Strong histórico y Extended Strong de STEPBible.

### Integridad
- [x] SHA-256 automático de la capa preservada.
- [x] Manifiestos machine-readable.
- [x] Procedencia SBLGNT, STEPBible y Strong histórico.
- [x] Registro de licencias/permisos declarado.

### Manuscritos
- [x] 9 testigos núcleo normalizados inicialmente.
- [x] Autoridad de registro definida: INTF Kurzgefasste Liste / NTVMR.
- [x] Scope obligatorio definido: todos los papiros de los Evangelios + majúsculos hasta s. V.
- [x] IIIF manifest de Codex Vaticanus preservado.
- [x] Inventario de **1.555 canvases** de Vaticanus.
- [x] IIIF manifest British Library de Codex Sinaiticus preservado.
- [x] Inventario de **694 canvases** de Sinaiticus-BL.

## En ejecución

### L-001 — SBLGNT ↔ TAGNT
- [ ] Alinear los 64.686 tokens SBLGNT con las filas TAGNT marcadas SBL.
- [ ] Incorporar Strong, lema, morfología, glosa y traducción española solo cuando el enlace sea verificable.
- [ ] Reportar tokens no alineados sin forzar datos.
- [ ] Vincular cada Strong con TBESG y, cuando exista, Strong histórico.

### M-001 — Facsímiles núcleo
- [ ] Identificar canvases de Mateo/Marcos/Lucas/Juan en Vaticanus y Sinaiticus.
- [ ] Calcular tamaño/volumen de imágenes.
- [ ] Definir almacenamiento binario (Git LFS o archivo externo versionado) antes de descargar GB de imágenes.
- [ ] Descargar, hash y mapear folio ↔ pasaje.

## Bloqueos abiertos

### B-003 — INTF / NTVMR API timeouts
**Objetivo afectado:** inventario exhaustivo de papiros y majúsculos hasta siglo V.

**Estado:** ABIERTO.

**Qué se comprobó:**
- la API oficial está documentada y accesible;
- las consultas amplias y también algunos probes `detail=count` por rangos grandes exceden el timeout del runner;
- no se perdió información ni se generó un inventario incompleto presentado como completo.

**Próximo intento cuando volvamos al bloqueo:**
- eliminar probes amplios;
- consultar por rangos docID pequeños/determinísticos o por IDs individuales;
- persistir cada respuesta exitosa inmediatamente;
- reanudar desde checkpoint para no repetir llamadas.

Mientras B-003 esté abierto, el inventario núcleo manual/institucional sigue disponible, pero no se declara exhaustivo.

## Bloqueos cerrados

### B-001 — archivos grandes STEPBible
**CERRADO.** Resolución: descarga HTTP por rangos de 900.000 bytes con `Accept-Encoding: identity`, reconstrucción y verificación contra SHA-1 del blob Git upstream.

### B-002 — GitHub Actions / CI
**CERRADO.** CI funciona. Se detectó además un problema posterior de pushes concurrentes, resuelto con helper de rebase/reintento y concurrencia por workflow.

## Siguiente orden de ejecución

1. Terminar L-001 y medir cobertura SBLGNT ↔ TAGNT.
2. Resolver excepciones de alineación si son acotadas.
3. Construir índice token → lema → Strong → TBESG → Strong histórico → morfología.
4. Modelar variantes desde TAGNT + aparato SBLGNT.
5. Seleccionar y dimensionar facsímiles de Vaticanus/Sinaiticus.
6. Copiar facsímiles + checksums + mapping.
7. Repetir preservación para P4, P45, P52, P66, P75, P104 y P137.
8. Volver a B-003 y completar inventario exhaustivo INTF.
9. Expandir manuscritos según inventario.
10. Construir índice pasaje ↔ manuscrito ↔ folio ↔ imagen ↔ transcripción.
11. Generar base de consulta SQLite/DuckDB.
12. Interfaz de investigación.
13. Backup independiente + restore test.
14. Auditoría final.

## Regla de estado
Nada se elimina por fallar. Todo ítem queda como **completado, en ejecución o bloqueado**, con estrategia de retorno explícita.
