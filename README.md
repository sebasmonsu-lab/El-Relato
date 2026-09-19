# El-Relato

Archivo privado y trazable de fuentes primarias, transcripciones, textos griegos y recursos léxicos para el estudio de los cuatro Evangelios.

## Objetivo

Preservar una copia verificable de las fuentes utilizadas para estudiar Mateo, Marcos, Lucas y Juan, manteniendo simultáneamente:

- copia local del recurso;
- referencia a la fuente original;
- institución custodiante;
- identificador del manuscrito o edición;
- fecha de captura;
- licencia o base de uso declarada;
- checksum cuando corresponda;
- notas de procedencia y versión.

## Principio de trazabilidad

La jerarquía de trabajo del proyecto es:

1. **Fuente primaria:** manuscritos y facsímiles.
2. **Evidencia textual:** transcripciones y ediciones críticas.
3. **Análisis lingüístico:** lema, morfología, concordancias y léxicos.
4. **Traducción / interpretación:** traducciones y notas de estudio.

Strong se trata como sistema de identificación léxica y concordancia, no como sustituto del texto griego ni como una traducción definitiva.

## Alcance inicial

### Evangelios
- Mateo
- Marcos
- Lucas
- Juan

### Testigos núcleo
- 𝔓4
- 𝔓45
- 𝔓52
- 𝔓66
- 𝔓75
- 𝔓104
- 𝔓137
- Codex Vaticanus (B / 03)
- Codex Sinaiticus (ℵ / 01)

### Recursos léxicos y textuales
- SBL Greek New Testament (SBLGNT)
- Strong Greek Dictionary / numeración Strong
- datos de STEPBible/Tyndale House
- morfología y lematización asociadas
- transcripciones disponibles de manuscritos

## Estructura

```
sources/
  manuscripts/
  critical-texts/
  lexicons/
  morphology/
gospels/
  matthew/
  mark/
  luke/
  john/
data/
  manifests/
  checksums/
  indexes/
methodology/
vendor/
```

## Preservación

Los recursos externos se conservan, cuando están disponibles, dentro de `vendor/` o `sources/`, acompañados por un archivo de procedencia. Los links externos se mantienen aunque exista copia local para conservar la trazabilidad.

Este repositorio es **privado** y está pensado como archivo de preservación y corpus de investigación.
