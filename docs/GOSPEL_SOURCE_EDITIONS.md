# Gospel SOURCE Editions — arquitectura

## Objetivo

Publicar los cuatro Evangelios como una familia de ediciones canónicas multilingües independiente de las ediciones narrativas de **El Relato**.

La ruta humana es:

`/gospels/<edition>/<book>/<chapter>/`

El orden canónico es Mateo → Marcos → Lucas → Juan.

## Regla de referencia

La edición griega SOURCE es la capa de referencia. Cada traducción consolidada conserva como mínimo un enlace versículo-a-versículo hacia el griego. El alineamiento palabra/frase → token griego sólo se publicará cuando exista una relación explícita almacenada; no se inferirá durante el render.

## Publicación

Estados:

- `draft`: no se publica.
- `canonical-source`: fuente griega navegable.
- `consolidated`: traducción completa lista para navegación.
- `published`: edición formalmente publicada.

Una traducción consolidada debe cubrir exactamente el conjunto de versículos disponible en la edición griega base. El build falla ante faltantes, extras o duplicados.

## Navegadores

- **El Relato**: composición editorial por escenas.
- **Evangelios**: lectura corrida en orden canónico y selector de idioma.
- **Fuentes**: explorador técnico del SOURCE, token, Strong, lema, morfología, variantes y manuscritos.

Los tres navegadores apuntan al mismo sistema de IDs y provenance, pero no mezclan sus responsabilidades.
