# book/

Capa editorial y composicional de El-Relato.

Esta carpeta está deliberadamente separada de `sources/`.

- `sources/` conserva y normaliza evidencia textual: manuscritos, facsímiles, transcripciones, ediciones griegas, léxicos, Strong, morfología y aparatos.
- `book/` define obras editoriales construidas sobre esa evidencia.

## Fuente canónica de la obra

Para **El Relato**, la fuente estructural canónica no es una traducción bíblica ni el DOCX final. Es el **Listado de referencias**, que define:

1. capítulo;
2. título de capítulo;
3. escena;
4. título de escena;
5. orden de cada unidad dentro de la escena;
6. referencia bíblica o combinación de referencias.

La obra contiene actualmente **6 capítulos, 120 escenas y 4.123 entradas de referencia ordenadas**.

El archivo `source/El Relato.docx` se preserva como realización editorial actual de esa estructura.

## Principio de rendering

Una obra se modela como:

`estructura editorial + secuencia de referencias + política textual + idioma/registro -> realización textual`

La misma estructura puede renderizarse utilizando:

- una traducción existente cuando su licencia/permiso permita el uso;
- una traducción propia previamente incorporada;
- una traducción nueva generada desde los textos griegos y capas lingüísticas preservadas en `sources/`.

Toda realización generada debe conservar provenance: fuente griega/edición, variantes consideradas, modelo, versión, prompt/política de traducción, idioma, fecha y revisión humana.

## Estructura

```
book/
  README.md
  TRANSLATION_ARCHITECTURE.md
  el-relato/
    manifest.json
    canon/
      El Relato - Listado de referencias.xlsx
    source/
      El Relato.docx
```

La capa `book/` está diseñada para admitir otras obras además de El Relato, cada una con su propio manifiesto composicional.
