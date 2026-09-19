# Interfaz El-Relato

Interfaz local, sin dependencias web externas, construida sobre la SQLite reproducible del corpus.

## Ejecutar

```bash
python app/el_relato.py
```

Abrir: `http://127.0.0.1:8765`

La aplicación reconstruye `build/el-relato.sqlite` automáticamente si no existe.

## Consultas iniciales

- Pasaje: `Juan 1:1` / `John 1:1`
- Strong: `G0746`
- API JSON:
  - `/api/passage?ref=John+18:37`
  - `/api/strong?id=G0746`

La UI es una vista derivada. La fuente de verdad continúa siendo `data/normalized/` + material preservado.
