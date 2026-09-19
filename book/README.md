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


## Base editorial SQLite

La base materializada de la obra es `book/el-relato-book.sqlite`. Se reconstruye de forma determinista con `scripts/build_book_db.py` a partir de la estructura editorial normalizada y del corpus griego preservado.

### Edición griega V1

ID: `edition:el-relato:grc-sblgnt-2010:v1`

- **6 capítulos**
- **120 escenas**
- **4.123 unidades editoriales**
- **5.381 testigos/referencias griegas**
- **4.913** materializaciones exactas desde SBLGNT
- **456** materializaciones de microsegmentos `a/b/c/...`, con límites heurísticos trazables sobre tokens SBLGNT
- **12** materializaciones de fallback desde la selección **Textus Receptus (TR)** de STEPBible TAGNT, exclusivamente para referencias numeradas que SBLGNT omite del texto principal
- **0** testigos sin resolver
- **0** textos primarios vacíos
- **0** errores de integridad referencial

Cuando una unidad contiene referencias paralelas, todas se conservan en `unit_witnesses`; la primera referencia de la unidad se usa como texto editorial primario de esta V1. Esto evita fabricar un texto griego híbrido entre Evangelios.

Los fallbacks TR están identificados mediante `derivation_method = 'tagnt-tr-fallback'` y una edición fuente independiente. No se presentan como texto SBLGNT.
