# El-Relato — Estado vivo

Última actualización: 2026-09-19

## Estado general
**Estado:** versión interna auditable en cierre.  
**Auditoría vigente:** PASS_WITH_BLOCKERS — 24 PASS / 3 WARN / 0 FAIL.

Regla operativa: todo bloqueo queda explícito; nada desaparece por fallar.

## Completado

### Corpus y lingüística
- [x] SBLGNT Mateo, Marcos, Lucas y Juan preservado en TXT/XML.
- [x] Aparato SBLGNT TXT/XML preservado.
- [x] 3.768 versículos / 64.686 tokens.
- [x] TBESG: 11.035 entradas.
- [x] TAGNT Mat–Jhn: 66.926 filas.
- [x] TEGMC: 1.644 códigos.
- [x] Strong histórico: 5.523 entradas.
- [x] Alineación SBLGNT ↔ TAGNT/Strong/morfología: 64.493 tokens (99,7016%).
- [x] 193 tokens no alineados preservados explícitamente.
- [x] 639 enlaces posicionales marcados como baja confianza.
- [x] 3.672 unidades de aparato entre ediciones completamente parseadas.

### Manuscritos núcleo
- [x] P4, P45, P52, P66, P75, P104, P137, Sinaiticus 01 y Vaticanus 03 registrados.
- [x] Vaticanus + Sinaiticus: 269 facsímiles de Evangelios preservados, 0 faltantes.
- [x] P75: 108 imágenes preservadas.
- [x] P66: fallback institucional Bodmer completo.
- [x] P104: fallback institucional Oxford completo.
- [x] P137: publicación P.Oxy. LXXXIII 5345 con imagen/texto preservada.
- [x] Sinaiticus: transcripción de Evangelios v1.95 normalizada (3.745 unidades).
- [x] IGNTP: P52/P66/P75 TEI preservado + 1.461 unidades normalizadas.
- [x] Evidencia integrada: 645 imágenes / 5.834 witness attestations / 5.206 unidades de transcripción.

### Infraestructura
- [x] Schemas e IDs estables.
- [x] CI y validación.
- [x] SHA-256 y manifests.
- [x] Licencias/permisos registrados: 23/23 fuentes.
- [x] SQLite reproducible.
- [x] Interfaz local de investigación + self-test.
- [x] Git bundle + Git LFS restore test completo.
- [x] Restore test: git fsck PASS, git-lfs fsck PASS, validation PASS, DB rebuild PASS, app PASS.
- [x] Auditoría actual con 0 FAIL.
- [x] EPIC 08 cerrado: variantes textuales implementadas a nivel versículo con provenance explícito.
- [x] EPIC 13 cerrado: backup independiente fuera de GitHub verificado en Google Drive.

## Limitaciones auditadas

### W-001 — Alineación lingüística residual
- 193 tokens SBLGNT no alineados.
- 639 enlaces posicionales de baja confianza.
- No se imputan datos silenciosamente.
- No bloquea la versión interna.

### W-002 — P45 composites de CSNTM
- 2 renderings composites específicos no se pudieron preservar.
- Las imágenes componentes sí están preservadas.
- No bloquea la versión interna.

## Bloqueos abiertos

### B-003 — INTF / NTVMR exhaustivo
**Objetivo:** certificar todos los papiros de Evangelios + majúsculos hasta siglo V.

**Estado:** harvest individual por docID en ejecución. Las consultas amplias fallaron por timeout.  
Si esta ejecución no termina, queda bloqueado para reanudar con checkpoints aún más pequeños.

### B-004 — backup independiente fuera de GitHub — RESUELTO
**Estado:** copia restaurable independiente verificada en Google Drive.

- Git bundle preservado;
- archivo LFS completo fragmentado en 26 partes;
- 27 archivos verificados en el destino externo;
- restore CI: git fsck PASS, git-lfs fsck PASS, validation PASS, DB rebuild PASS, app PASS;
- manifiesto: `data/derived/backup/independent-backup.json`.

### B-005 — aparato manuscrito exhaustivo — ROADMAP
La infraestructura de variantes ya está implementada y EPIC 08 está cerrado:
- 777 variant units versículo-a-versículo;
- readings con testigos;
- provenance explícito;
- ninguna variante inferida desde traducciones.

La extensión a un aparato exhaustivo segment-level equivalente en alcance a ECM/NA/INTF queda como roadmap de investigación en issue #15 y no bloquea la versión interna.

## Release
- [x] RELEASE_NOTES_v0.1.0-internal.md preparado.
- [x] tag `v0.1.0-internal` y release interno creados correctamente.
- [x] Release interno auditable disponible; `main` contiene mejoras posteriores (Book DB griega y backup externo).

## Regla de cierre
La versión interna puede liberarse con WARN/BLOCKERS, pero nunca con FAIL.  
Todo pendiente debe quedar visible en este archivo y en GitHub Issues.
