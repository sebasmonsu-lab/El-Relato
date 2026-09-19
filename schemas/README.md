# Schemas

Los schemas de este directorio definen el contrato estable para los datos normalizados de El-Relato.

## Reglas
- RAW nunca se fuerza a estos schemas.
- Normalized sí debe validar.
- Derived debe ser regenerable desde RAW + normalized.
- Los schemas se versionarán cuando un cambio rompa compatibilidad.
- Los IDs técnicos se mantienen estables; los labels pueden corregirse sin cambiar identidad.

## Schemas
- source.schema.json
- manuscript.schema.json
- passage.schema.json
- edition.schema.json
- manuscript-image.schema.json
- transcription-unit.schema.json
- token.schema.json
- lexeme.schema.json
- morphology.schema.json
- variant.schema.json
- witness-attestation.schema.json
- checksum-manifest.schema.json

Este conjunto cubre la cadena completa:
**fuente → manuscrito → imagen/transcripción → pasaje → edición/token → lema/Strong/morfología → variante/atestación → integridad**.
