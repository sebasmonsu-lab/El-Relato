# Cómo usar El-Relato

## 1. Validar

```bash
python -m pip install jsonschema
python scripts/validate_repo.py
```

## 2. Reconstruir la base de consulta

```bash
python scripts/build_query_db.py --output build/el-relato.sqlite
```

La SQLite es derivada: puede borrarse y reconstruirse.

## 3. Interfaz local

```bash
python app/el_relato.py
```

Abrir:

`http://127.0.0.1:8765`

Consultas iniciales:
- `Juan 1:1`
- `John 18:37`
- Strong `G0746`

## 4. Consultar con SQLite

Ejemplo:

```sql
SELECT book, chapter, verse, position, surface, strongs, lemma, morphology_code
FROM token_analysis
WHERE strongs LIKE 'G0746%'
ORDER BY book, chapter, verse, position;
```

Evidencia manuscrita:

```sql
SELECT *
FROM passage_evidence
WHERE passage_id = 'passage:john:18:37';
```

Transcripciones:

```sql
SELECT *
FROM verse_transcriptions
WHERE book='John' AND chapter=1 AND verse=1;
```

## 5. Volver a la fuente

Nunca citar un dato derivado sin poder identificar su procedencia.

La cadena recomendada es:

`consulta → dataset normalizado → source_id → manifest/provenance → raw preservado → institución/upstream`

## 6. Reconstrucción total

Los pipelines están en `.github/workflows/`. Los archivos raw se conservan; los datasets normalizados y derivados se regeneran mediante scripts versionados.

## 7. Backup

```bash
bash backup/create_bundle.sh
bash backup/verify_restore.sh build/backups/el-relato.bundle
```

La restauración incluye Git y Git LFS.
