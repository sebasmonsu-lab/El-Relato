# El-Relato — Estado vivo

Última actualización: 2026-09-19

## Estado general
**Estado:** versión interna auditable en cierre.  
**Auditoría vigente:** PASS_WITH_BLOCKERS — 22 PASS / 4 WARN / 0 FAIL.

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
- [x] 10 epics cerrados como completed.

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

### B-004 — backup independiente fuera de GitHub
**Objetivo:** copia restaurable en segundo almacenamiento.

**Estado:** restore local/CI probado. El artifact único de 2,46 GB excedió el límite de 512 MB del conector.  
Se agregó fragmentación en partes de 450 MB para transferir a Google Drive. Workflow en ejecución.

### B-005 — aparato manuscrito exhaustivo
El repositorio ya conserva:
- aparato SBLGNT entre ediciones;
- witness attestations;
- transcripciones de varios testigos.

Todavía no se declara equivalente a un aparato crítico manuscrito exhaustivo ECM/NA/INTF. EPIC 08 permanece abierto.

## Release
- [x] RELEASE_NOTES_v0.1.0-internal.md preparado.
- [ ] tag `v0.1.0-internal` y release privado: workflow en cola/ejecución.
- [ ] EPIC 14 se cierra después de confirmar tag/release.

## Regla de cierre
La versión interna puede liberarse con WARN/BLOCKERS, pero nunca con FAIL.  
Todo pendiente debe quedar visible en este archivo y en GitHub Issues.
