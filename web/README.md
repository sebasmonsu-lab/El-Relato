# web/

Aplicación web pública generada de El Relato.

La especificación canónica está en `docs/WEB_PLATFORM.md`.

Regla central: **la web y los documentos son artefactos hermanos**. Ningún DOCX se parsea para reconstruir el sitio; ambos se generan desde BOOK + SOURCE y comparten `edition_id`, provenance y manifest.

## Primer objetivo

Publicar `edition:el-relato:grc-sblgnt-2010:v1` con:

- 6 capítulos;
- 120 escenas;
- 4.123 unidades editoriales;
- navegación por token;
- enlace Libro → SOURCE;
- enlace SOURCE → Libro;
- Strong, lema, morfología y evidencia textual disponible;
- política de publicación por fuente.

## Directorios previstos

```
web/
  src/          # interfaz
  public/       # assets estáticos
  generated/    # datasets generados; no editarlos manualmente
```

El build debe ser determinista y ejecutarse en CI.
