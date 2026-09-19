# El-Relato — Estado vivo

Última actualización: 2026-09-19

## Estado general
**Fase actual:** 0 / 3 en paralelo — Gobierno + preservación STEPBible.

## Completado
- [x] Repositorio privado `sebasmonsu-lab/El-Relato`.
- [x] README inicial.
- [x] Metodología básica de jerarquía de fuentes.
- [x] Registro inicial de manuscritos núcleo.
- [x] SBLGNT Mateo TXT.
- [x] SBLGNT Marcos TXT.
- [x] SBLGNT Lucas TXT.
- [x] SBLGNT Juan TXT.
- [x] SBLGNT Mateo XML.
- [x] SBLGNT Marcos XML.
- [x] SBLGNT Lucas XML.
- [x] SBLGNT Juan XML.
- [x] README/About/LICENSE SBLGNT.
- [x] README STEPBible.
- [x] TEGMC — códigos de morfología griega.
- [x] Procedencia inicial SBLGNT.
- [x] Procedencia inicial STEPBible.

## En ejecución
- [ ] TBESG — Extended Strong Greek completo.
- [ ] TAGNT Mat–Jhn completo.
- [ ] Estrategia de fragmentación y reconstrucción de archivos grandes.
- [ ] Checksums iniciales.
- [ ] Plan maestro y arquitectura.

## Próximo bloque
- [ ] Validar inventario real de archivos SBLGNT/STEPBible.
- [ ] Crear manifests con hashes.
- [ ] Completar datos académicos de manuscritos núcleo.
- [ ] Localizar/capturar transcripciones y facsímiles.

## Bloqueos conocidos

### B-001 — límite del conector para archivos grandes
Afecta TBESG y TAGNT Mat–Jhn.

**Resolución acordada:** copiar por partes dentro del límite de API, almacenar manifest de partes y procedimiento de ensamblado. No cerrar hasta comprobar hash del archivo reconstruido.

## Regla de estado
Un ítem nunca desaparece porque falle. Se mueve a **Bloqueos conocidos** hasta resolverlo.
