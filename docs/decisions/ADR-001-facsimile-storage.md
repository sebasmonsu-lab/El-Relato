# ADR-001 — Almacenamiento de facsímiles

**Estado:** Accepted  
**Fecha:** 2026-09-19

## Contexto

El-Relato necesita preservar copias locales de facsímiles manuscritos, no solamente URLs externas.

El primer conjunto medido contiene:
- Vaticanus: 148 canvases de Evangelios, 127.556.061 bytes medidos.
- Sinaiticus-BL: 121 canvases; 48 medidos suman 31.073.590 bytes y el promedio observado es ~647 KB por imagen.
- Proyección inicial total del núcleo: ~206 MB.

El proyecto crecerá luego con papiros y otros manuscritos.

## Decisión

Los archivos binarios de imagen se almacenarán mediante **Git LFS** dentro del repositorio privado.

Git normal seguirá conteniendo:
- manifests;
- JSON/JSONL;
- XML;
- TXT;
- scripts;
- checksums;
- metadata y provenance.

## Motivos

1. GitHub recomienda Git LFS para archivos binarios.
2. Evita inflar el historial Git principal al agregar cientos o miles de imágenes.
3. Mantiene la copia asociada al mismo repositorio y su historial.
4. A 2026-09-19 GitHub Free/Pro incluye 10 GiB de almacenamiento Git LFS y 10 GiB de bandwidth mensual.
5. El primer bloque (~0,2 GiB proyectados) está muy por debajo de esa asignación.

## Fuentes

- https://docs.github.com/en/billing/concepts/product-billing/git-lfs
- https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits

## Reevaluación

Si el archivo de manuscritos supera el presupuesto LFS disponible:
- mantener manifests/checksums en GitHub;
- incorporar object storage/cold storage como segundo backend;
- conservar procedimientos de restauración y referencias de objetos;
- nunca eliminar una fuente del plan por limitación de almacenamiento.
