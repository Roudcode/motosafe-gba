# A09 — guía para revisar la ubicación de 50 noticias

`etiquetado_rodo.csv` copia las 50 filas de `muestra_calles.csv` y agrega columnas vacías para el juicio de Rodolfo. La muestra original no se modifica. **No hay etiquetas ni resultados de precisión todavía.**

## Cómo completar cada fila

1. Leer `titulo` y `descripcion_completa`. Abrir `url` cuando ese texto no alcance para decidir. La descripción fue obtenida en vivo el 21/10/2026 y puede diferir de la que vio el scraper al guardar la noticia.
2. Comparar el lugar que afirma la nota con `query_extraida`. No tomar `nivel_precision` como prueba de que la extracción es correcta: es la categoría asignada por el sistema, también revisable.
3. Completar `juicio_ubicacion` con **correcta**, **parcial**, **incorrecta** o **indeterminable**. Usar `parcial` si el partido/barrio coincide pero la calle o intersección no está sostenida por la nota; `indeterminable` si la nota no da ubicación suficiente o no está disponible.
4. En `ubicacion_correcta`, escribir el lugar sostenido por la nota cuando la extracción sea parcial o incorrecta. En `evidencia_en_nota`, copiar solo una referencia breve que permita encontrarlo (por ejemplo, «Av. X y calle Y»). En `observacion`, aclarar ambigüedades o que la URL cambió.

Dejar los campos de juicio vacíos si una fila todavía no fue revisada. En particular, las filas **55** y **800** tienen `query_extraida` vacía en la exportación: requieren un juicio humano; no son automáticamente errores del extractor.

Cuando las 50 filas estén revisadas, se calcularán resultados separando `calle`/`interseccion` de `barrio`, con denominadores explícitos. Las filas `indeterminable` se reportarán por separado; no se contarán como aciertos ni se esconderán. La revisión humana de las noticias y cualquier discrepancia se documentarán antes de cambiar reglas del scraper o publicar una cifra de precisión.
