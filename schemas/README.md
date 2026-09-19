# Schemas

Los schemas de este directorio definen el contrato estable para los datos normalizados de El-Relato.

## Reglas
- RAW nunca se fuerza a estos schemas.
- Normalized sí debe validar.
- Derived debe ser regenerable desde RAW + normalized.
- Los schemas se versionarán cuando un cambio rompa compatibilidad.

## Schemas iniciales
- source.schema.json
- manuscript.schema.json
- token.schema.json
- lexeme.schema.json
- morphology.schema.json
- variant.schema.json

Próximos:
- passage
- manuscript-image
- transcription-unit
- witness-attestation
- edition
- checksum-manifest
