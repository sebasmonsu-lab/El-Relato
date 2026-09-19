# Política de licencias de El-Relato

El-Relato es un corpus compuesto. **No existe una única licencia raíz que pueda reemplazar las licencias y permisos de todas las fuentes.**

## Capas

### Código propio
Los scripts, schemas, documentación y software desarrollados específicamente para El-Relato pueden licenciarse separadamente en una futura publicación del proyecto.

### Datos derivados propios
Los índices, IDs internos, mappings, reportes y bases derivadas deben conservar siempre la procedencia de los materiales que los originan.

### Fuentes de terceros
Cada fuente conserva:
- institución/autores;
- URL upstream;
- licencia o permiso declarado;
- evidencia documental cuando está disponible;
- copia local;
- checksum.

El registro máquina-legible está en:

`data/manifests/license-registry.json`

## Regla

Que el repositorio sea privado no convierte automáticamente un material de terceros en redistribuible públicamente. Antes de abrir el repositorio, publicar un release o redistribuir un subconjunto, se debe auditar la licencia de ese subconjunto.

## Strong

Se preservan por separado:
- Strong histórico en representación XML CC0;
- Extended Strong / STEPBible con su licencia upstream.

No deben fusionarse de manera que se pierda la identidad de la fuente de una definición o glosa.
