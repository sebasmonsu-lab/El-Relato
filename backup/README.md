# Backup y restauración de El-Relato

## Objetivo

El repositorio no debe depender de una única copia operativa de GitHub.

## Backup reproducible

```bash
bash backup/create_bundle.sh
```

Genera:
- `build/backups/el-relato.bundle`
- `build/backups/el-relato.bundle.sha256`
- `build/backups/backup-metadata.json`

El bundle contiene el historial Git completo disponible en el checkout.

## Verificar restauración

```bash
bash backup/verify_restore.sh build/backups/el-relato.bundle
```

La prueba:
1. verifica SHA-256;
2. clona exclusivamente desde el bundle;
3. verifica objetos Git;
4. ejecuta el validador del repositorio;
5. reconstruye la SQLite;
6. ejecuta el self-test de la interfaz.

## Copia independiente

Un artifact de GitHub Actions **no cuenta como backup independiente de GitHub**. El bundle debe copiarse además a almacenamiento fuera de GitHub (GitLab, almacenamiento de objetos, NAS o cold storage). Esa capa se considera completa únicamente después de una restauración probada desde ese destino.
