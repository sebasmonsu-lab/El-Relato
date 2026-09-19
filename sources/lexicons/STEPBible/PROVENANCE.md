# STEPBible / Tyndale House data — procedencia

- Fuente: https://github.com/STEPBible/STEPBible-Data
- Árbol fuente observado: `b99716b0cddb648ddb95cc786a197180f2f97d48`
- Fecha de captura inicial: 2026-09-19
- Uso en El-Relato: Strong extendido griego, morfología, lematización y datos de apoyo para los cuatro Evangelios.

## Estado de preservación

- README upstream: **preservado**.
- TEGMC (Greek Morphology Codes): **preservado**.
- TBESG (Extended Strong Greek): **preservado y verificado byte a byte**.
- TAGNT Mat–Jhn: **preservado y verificado byte a byte**.

## Ingesta de archivos grandes

Los archivos grandes se descargaron mediante rangos HTTP de 900.000 bytes, se reensamblaron en el runner y se validaron contra el SHA-1 del objeto Git upstream.

### TBESG
- tamaño: 4.736.912 bytes
- chunks: 6
- Git blob upstream/verificado: `efe271a1dbb73fa01f8fa6e0f164c6687757a9ae`
- SHA-256: `312f723d7b8ef263bbdfb0451c9b8057125804dfff390b6f8544cff2a84b57f4`

### TAGNT Mat–Jhn
- tamaño: 14.300.601 bytes
- chunks: 16
- Git blob upstream/verificado: `b4e80bbf11fe2f9546531303c22821f05c75971a`
- SHA-256: `1179cc0de292f5ee4cbfbc5fd06331c0f1dc623e4fca93e38fbeecf5906f36d9`

El manifest máquina-legible está en `data/manifests/stepbible-large-files.json`.
