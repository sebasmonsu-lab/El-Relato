# Arquitectura de traducción y generación editorial

## Idea central

La secuencia de referencias es independiente del texto visible. Por eso El-Relato puede separar:

- **qué pasajes y fragmentos componen una escena**;
- **en qué orden aparecen**;
- **qué evidencia textual respalda cada referencia**;
- **cómo se realiza esa estructura en un idioma o registro concreto**.

## Capas

### 1. Composition layer — canónica para cada obra
Define capítulos, escenas, orden y referencias. No contiene una traducción obligatoria.

### 2. Evidence layer — `sources/`
Contiene texto griego, manuscritos, transcripciones, variantes, lema, Strong, morfología y provenance.

### 3. Translation layer — derivada
Produce una realización textual para un idioma o política de traducción.

Cada generación debe registrar al menos:
- `book_id`;
- `composition_version`;
- edición/base griega utilizada;
- fuentes lingüísticas usadas;
- idioma de destino;
- política de traducción;
- proveedor/modelo y versión;
- parámetros relevantes;
- fecha;
- estado de revisión;
- hash del resultado.

### 4. Publication layer — derivada
DOCX, PDF, EPUB, web u otros formatos construidos desde la composición y una translation layer.

## Traducciones existentes

Una referencia bíblica puede apuntar a cualquier traducción para consulta, comparación o rendering **solo cuando el uso del texto esté autorizado por su licencia o permiso aplicable**.

La existencia de la referencia, del griego, de Strong o de concordancias no concede derechos sobre la redacción de una traducción moderna de terceros.

## Traducciones generadas por LLM

Sí se puede generar una traducción nueva desde fuentes griegas que el proyecto tenga derecho a utilizar. La traducción debe tratarse como un derivado nuevo, no como copia ni imitación de una traducción moderna específica.

Para calidad filológica:
- traducir desde el griego y no desde otra traducción salvo que sea explícitamente una fuente auxiliar autorizada;
- preservar segmentación y provenance;
- marcar decisiones donde existan variantes textuales;
- impedir que el modelo complete silenciosamente lagunas;
- someter las versiones publicables a revisión humana;
- conservar el output y los parámetros para reproducibilidad.

## Consecuencia

El motor no está limitado a un solo libro. Cualquier obra futura puede definirse como una composición de unidades referenciadas y renderizarse en múltiples idiomas o políticas textuales sin duplicar la capa de evidencia.
