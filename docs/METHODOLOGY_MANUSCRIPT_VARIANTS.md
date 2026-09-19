# Metodología — comparación de lecturas manuscritas

Esta capa **no reemplaza** un aparato crítico exhaustivo (ECM/NA/INTF).

## Fuente de los datos

Se comparan exclusivamente transcripciones académicas preservadas localmente:
- Codex Sinaiticus (ITSEE / Codex Sinaiticus Project), GA 01.
- IGNTP TEI para P52, P66 y P75.

La transcripción raw preservada sigue siendo la autoridad. El JSONL es derivado y regenerable.

## Unidad de comparación

La primera implementación usa **versículo completo** como unidad. Solo se genera una unidad de variante cuando:

1. hay al menos dos manuscritos transcritos para el mismo versículo;
2. la lectura puede compararse sin una laguna explícita;
3. después de una normalización mecánica conservadora existen dos o más lecturas distintas.

## Normalización usada para agrupar

Para comparar, no para sustituir el texto diplomático:
- Unicode NFD;
- eliminación de diacríticos;
- eliminación de puntuación y espacios;
- sigma final normalizada a sigma;
- minúsculas.

El campo `text` de cada reading conserva el texto diplomático original del dataset normalizado.

## Exclusiones

Las unidades IGNTP que contienen marcadores `⟦lacuna:...⟧` se excluyen de la comparación automática. No se reconstruyen letras faltantes ni se imputan lecturas.

## Alcance

La salida documenta diferencias **entre los testigos transcritos presentes en El-Relato**. No implica ausencia/presencia en testigos no transcritos y no debe citarse como aparato exhaustivo de manuscritos.
