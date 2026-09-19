# Gospel SOURCE editions

Esta capa almacena las **ediciones canónicas de Mateo, Marcos, Lucas y Juan** que alimentan el lector multilingüe `/gospels/`.

## Separación de dominios

- `book/el-relato-book.sqlite`: ediciones editoriales de **El Relato**.
- SOURCE normalizado / `build/el-relato.sqlite`: griego, tokens, Strong, lema, morfología y evidencia.
- `sources/gospel-editions/`: traducciones de los **Evangelios como corpus canónico**, independientes de El Relato.

Nunca se usa una traducción de El Relato como traducción automática del Evangelio ni viceversa.

## Edición griega base

`edition:gospels:grc-sblgnt-2010:v1` se materializa directamente desde la base SOURCE generada. Mantiene los IDs de token y por eso cada palabra puede abrir su ficha técnica.

## Agregar una traducción

Crear un directorio, por ejemplo:

`sources/gospel-editions/es-419-v1/`

con:

1. `edition.json`
2. `verses.jsonl`

Cada línea de `verses.jsonl`:

```json
{"book":"John","chapter":1,"verse":1,"text":"..."}
```

Una traducción marcada `consolidated` o `published` sólo se publica si contiene exactamente el mismo conjunto canónico de versículos que el griego base. Las ediciones `draft` no aparecen en la web.

El vínculo mínimo es versículo → versículo griego. Una futura capa de alineamiento explícito podrá agregar palabra/frase → token griego sin fabricar equivalencias.
