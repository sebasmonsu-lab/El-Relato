# TK-es-419 — Traducción Tokenizada

## Identidad

- **ID de edición:** `edition:el-relato:tk-es-419:v0.1`
- **Nombre corto:** `tk-es-419`
- **Familia:** TK — Traducción Tokenizada
- **Idioma:** español latinoamericano (`es-419`)
- **Estado inicial:** draft / revisión humana requerida
- **Obra:** `book:el-relato`

TK no identifica una traducción bíblica histórica o publicada por terceros. Identifica una
traducción nueva generada computacionalmente desde la evidencia griega preservada por
El-Relato, con trazabilidad por unidad y testigo.

## Fuente y precedencia

1. La composición canónica de El Relato define capítulos, escenas, unidades, orden y referencias.
2. Cada unidad se traduce desde su testigo griego primario materializado en
   `book/el-relato-book.sqlite`.
3. SBLGNT 2010 es la edición griega primaria de V1.
4. Los fallbacks TAGNT/Textus Receptus ya identificados por la base se conservan como tales.
5. Los testigos paralelos se conservan para auditoría; no se mezclan silenciosamente para crear
   un texto griego híbrido.
6. Strong, lema y morfología son evidencia lingüística auxiliar cuando estén enlazados; no son
   una traducción española de referencia.

## Política lingüística es-419

La salida debe ser español latinoamericano contemporáneo comprensible de manera natural para
lectores de México, Colombia y comunidades hispanohablantes de Estados Unidos.

- Evitar voseo, argentinismos, españolismos y regionalismos locales innecesarios.
- Usar `ustedes`, no `vosotros`.
- Priorizar fidelidad semántica al griego sobre calcos sintácticos.
- Conservar carga teológica cuando una simplificación alteraría el significado.
- No imitar deliberadamente la redacción distintiva de una traducción bíblica moderna.
- No agregar explicaciones, sujetos, causalidades o armonizaciones ausentes de la unidad fuente,
  salvo lo estrictamente exigido por la gramática española; tales decisiones deben ser
  auditables cuando sean materialmente interpretativas.
- Mantener nombres propios de forma consistente en toda la obra.
- Las escenas deben leerse como narración continua, pero la fluidez editorial no puede borrar
  la provenance de las unidades que las componen.

## Unidad de traducción

La unidad mínima persistida es `unit_id`. La generación puede considerar contexto de escena
para resolver pronombres, elipsis y continuidad discursiva, pero debe producir una realización
por unidad antes del ensamblado final.

Por cada unidad TK deben conservarse como mínimo:

- `edition_id`;
- `unit_id`;
- texto TK;
- `source_witness_id`;
- método de derivación;
- modelo/proveedor y versión;
- versión de esta política;
- fecha;
- estado de revisión.

## Estados

`generated` → `reviewed` → `approved` → `published`

Una edición generada no debe presentarse como revisión filológica humana hasta alcanzar el
estado correspondiente.

## Criterio V0.1

V0.1 se valida primero sobre escenas iniciales. Una vez estabilizados literalidad, registro,
nombres propios, terminología teológica y continuidad narrativa, la misma política se aplica a
las 120 escenas y cualquier excepción se registra explícitamente.
