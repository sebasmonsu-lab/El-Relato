# El-Relato — Estado vivo

Última actualización: 2026-09-19

## Estado general
**Fase activa:** Gobierno completado; preservación STEPBible bloqueada parcialmente; schemas/validación en ejecución.

## Completado
- [x] Repositorio privado `sebasmonsu-lab/El-Relato`.
- [x] README inicial.
- [x] PROJECT_PLAN.md maestro.
- [x] docs/ARCHITECTURE.md.
- [x] docs/LOOP_PROTOCOL.md.
- [x] 14 epics de ejecución creados en GitHub Issues.
- [x] Metodología básica de jerarquía de fuentes.
- [x] Registro inicial de manuscritos núcleo.
- [x] SBLGNT Mateo TXT/XML.
- [x] SBLGNT Marcos TXT/XML.
- [x] SBLGNT Lucas TXT/XML.
- [x] SBLGNT Juan TXT/XML.
- [x] README/About/LICENSE SBLGNT.
- [x] README STEPBible.
- [x] TEGMC — códigos de morfología griega.
- [x] Procedencia inicial SBLGNT.
- [x] Procedencia inicial STEPBible.

## En ejecución
- [ ] Schemas de datos.
- [ ] Convenciones de IDs.
- [ ] Validación automática inicial.
- [ ] Inventario académico ampliado de manuscritos.

## Pendiente con bloqueo
- [ ] TBESG — Extended Strong Greek completo.
- [ ] TAGNT Mat–Jhn completo.

## Bloqueos conocidos

### B-001 — lectura incremental de blobs grandes de STEPBible
**Afecta:** TBESG (~4.5 MB) y TAGNT Mat–Jhn (~14 MB).

**Observación técnica:** el endpoint del conector disponible no entrega rangos parciales para estos blobs grandes. Aunque se solicitan rangos de líneas, el conector intenta resolver el blob completo y falla por límite de cuerpo.

**Estrategia acordada por el proyecto:** preservación incremental/fragmentada, sin abandonar los archivos.

**Estado:** ABIERTO. Debemos elegir/implementar un mecanismo que realmente permita leer fragmentos del upstream (por ejemplo un proceso externo controlado o una acción dentro de GitHub) y después verificar hash final. Hasta entonces no se marca como mirrored.

## Próximo bloque
1. Terminar schemas e IDs.
2. Crear validadores y CI.
3. Completar manifests/checksums de lo ya preservado.
4. Profundizar metadata de manuscritos núcleo.
5. Resolver B-001 y completar TBESG/TAGNT.
6. Continuar con facsímiles/transcripciones.

## Regla de estado
Un ítem nunca desaparece porque falle. Se mueve a **Bloqueos conocidos** hasta resolverlo.
