# Convenciones de identificadores

Los IDs internos deben ser estables, legibles y no depender de nombres de archivo.

## Source
`src:<namespace>:<slug>`

Ejemplos:
- `src:sblgnt:faithlife`
- `src:stepbible:tbesg`
- `src:csntm:p52`

## Manuscript
`ms:ga:<normalized-ga-id>`

Ejemplos:
- `ms:ga:p52`
- `ms:ga:01`
- `ms:ga:03`

## Passage
`passage:<book>:<chapter>:<verse>`

Ejemplo:
- `passage:john:1:1`

Rangos:
- `passage:john:18:31-33`

## Text edition
`edition:<slug>:<version>`

Ejemplo:
- `edition:sblgnt:2010`

## Token
`token:<edition>:<book>:<chapter>:<verse>:<position>`

Ejemplo:
- `token:sblgnt:john:1:1:1`

## Lexeme
Preferir Strong cuando exista como identificador secundario, no como ID primario universal.

`lexeme:grc:<normalized-lemma>`

Ejemplo:
- `lexeme:grc:ἀρχή`

## Strong entry
`strong:G<zero-padded-number>`

Ejemplo:
- `strong:G0746`

## Variant
`variant:<book>:<chapter>:<verse>:<ordinal>`

## Reading
`reading:<variant-id>:<ordinal>`

## Witness attestation
`attest:<manuscript-id>:<reading-id>`

## Reglas
- minúsculas salvo convenciones externas como Strong;
- UTF-8 permitido en lemas;
- IDs no cambian por correcciones ortográficas de labels;
- todo ID externo se conserva además en campos específicos;
- nunca reutilizar un ID eliminado para otra entidad.
