# El Relato Web — arquitectura de publicación trazable

## Objetivo

Cada edición publicable de El Relato (DOCX/PDF/EPUB) debe tener una representación web versionada generada desde la misma base editorial. El sitio no se deriva del DOCX: el DOCX y la web son artefactos hermanos producidos desde BOOK + SOURCE.

## Principio de identidad

Una edición tiene un `edition_id` estable. Todos sus artefactos comparten ese ID:

- DOCX
- PDF
- EPUB
- Web
- manifest de build
- reporte de validación

Una corrección en BOOK o SOURCE regenera todos los artefactos y conserva la versión anterior.

## Rutas públicas

- `/editions/` — catálogo de ediciones
- `/editions/<edition_id>/` — portada de una edición
- `/editions/<edition_id>/chapter/<n>/`
- `/editions/<edition_id>/scene/<n>/`
- `/editions/<edition_id>/unit/<unit_id>/`
- `/source/` — explorador del corpus
- `/source/<book>/<chapter>/`
- `/source/<book>/<chapter>/<verse>/`
- `/token/<token_id>/`
- `/strong/<strong_id>/`
- `/manuscript/<manuscript_id>/`

## Navegación Libro → evidencia

Cada palabra/token del texto griego de la edición debe ser interactiva. El token abre un panel o página con:

- forma superficial;
- lema;
- Strong;
- morfología;
- glosa;
- edición fuente;
- referencia canónica;
- estado textual;
- método de alineación y confianza;
- variantes conocidas;
- testigos manuscritos disponibles;
- transcripciones;
- facsímiles cuando su política de publicación lo permita;
- enlace al pasaje completo en SOURCE.

Cada unidad editorial conserva además todas sus referencias paralelas aunque la edición V1 use una de ellas como texto primario.

## Navegación evidencia → Libro

Desde cualquier versículo o token de los cuatro Evangelios se podrá consultar:

- escenas de El Relato donde se utiliza;
- unidad editorial;
- posición dentro de la escena;
- edición/es del libro que lo materializan;
- referencias paralelas asociadas.

Esto permite investigar el corpus sin pasar por el libro y volver desde SOURCE hacia la composición editorial.

## Fuentes sin tocar

SOURCE conserva el material normalizado y la copia preservada. La web distingue explícitamente:

1. **source-preserved**: copia preservada tal como fue adquirida;
2. **source-normalized**: representación normalizada para consulta;
3. **book-derived**: uso editorial dentro de El Relato.

La interfaz nunca presenta un derivado como si fuera la fuente original.

## Política de publicación

Cada recurso debe resolver a una política:

- `public`: contenido puede servirse directamente;
- `metadata-only`: se publica ficha, provenance, checksum y enlace institucional, no el archivo/texto restringido;
- `private`: sólo existe en el repositorio/backup privado.

El build público debe fallar si intenta incluir un recurso no autorizado.

## Arquitectura técnica

### Build

`BOOK + SOURCE + publication policy -> web dataset -> static site -> deploy`

La web pública se genera automáticamente en CI. No consulta directamente los SQLite privados desde el navegador.

### Datos web

Los datasets se exportan en fragmentos JSON versionados:

- `editions.json`
- `chapters/<edition>/<chapter>.json`
- `scenes/<edition>/<scene>.json`
- `passages/<book>/<chapter>/<verse>.json`
- `tokens/<prefix>.json`
- `strong/<id>.json`
- `manuscripts/<id>.json`
- `reverse-index/source-to-book.json`

El particionado evita cargar el corpus completo para una consulta.

### Frontend

Interfaz responsive, apta para escritorio y móvil:

- lector del libro;
- panel de análisis por palabra;
- explorador de Evangelios;
- comparador de referencias paralelas;
- navegador de variantes/testigos;
- búsqueda por referencia, palabra, lema o Strong;
- permalink para cualquier escena, versículo, token o análisis.

## Versionado

Ejemplo conceptual:

`/editions/grc-sblgnt-2010-v1/scene/42/`

Una edición posterior no rompe los enlaces anteriores. `/latest/` puede redirigir a la versión publicable vigente.

## Relación con los DOCX

No habrá “un sitio mantenido manualmente por DOCX”. Cada vez que el pipeline produzca una edición DOCX publicable:

1. valida BOOK y SOURCE;
2. genera DOCX/PDF;
3. genera dataset web de la misma edición;
4. ejecuta validaciones de enlaces y provenance;
5. publica la nueva edición web;
6. conserva las ediciones anteriores;
7. produce un manifest común con hashes y `edition_id`.

Así el libro impreso, el archivo descargable y el sitio web son vistas del mismo objeto editorial.

## Fases

### W1 — Web griega
Primera edición navegable basada en `edition:el-relato:grc-sblgnt-2010:v1`: 6 capítulos, 120 escenas, unidades y tokens enlazados.

### W2 — SOURCE browser
Mateo, Marcos, Lucas y Juan completos, versículo/token, Strong, lema, morfología, aparato y evidencia manuscrita.

### W3 — navegación inversa
SOURCE → todas las apariciones en El Relato.

### W4 — ediciones traducidas
La misma estructura para español y futuras traducciones, con alineación palabra/frase al griego.

### W5 — publicación editorial
DOCX/PDF/EPUB + Web generados en un mismo release y manifest.

## Criterios de aceptación de W1

- 120/120 escenas navegables.
- 4.123/4.123 unidades con permalink.
- 0 referencias rotas.
- todo token mostrado tiene identificador estable.
- cada token resoluble enlaza a SOURCE.
- toda unidad muestra provenance.
- ninguna fuente restringida se filtra al build público.
- build reproducible desde `main`.
