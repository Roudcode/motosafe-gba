# Ingesta de prensa multifluente

Actualizado: 2026-09-13. Esta guía describe la capa de noticias de MotoSafe GBA; no es una fuente estadística oficial ni reemplaza los datos históricos de siniestros o delitos.

## Qué entra a la capa

`backend/scrapear_noticias_robos.py` consulta fuentes públicas mediante RSS, sitemap o secciones periodísticas. Además de los medios directos, incorpora dos consultas públicas de Google Noticias para seguridad y motos en Buenos Aires/GBA. Su función es descubrir medios locales que no publican un feed propio. Cada punto conserva el enlace de origen y la fuente que lo entregó.

El proceso acepta sólo noticias con una categoría textual y una ubicación plausible dentro del área acotada. Clasifica el hecho como `robo`, `inseguridad` o `choque`. `relacionado_moto` es otro atributo: vale verdadero sólo cuando el título o la descripción mencionan explícitamente una motocicleta, moto o motociclista; no se infiere desde una zona, una foto ni el medio. La expresión “moto de agua” queda excluida. En RSS se conserva `pubDate`; la vigencia, el orden y la antigüedad visible usan esa fecha real y recurren a la fecha de ingesta sólo si la fuente no la entrega.

Esto permite que el filtro **Motos** muestre robos, inseguridad y choques vinculados a motos sin convertir al resto de la capa en una capa exclusivamente de motos. Las entradas históricas previas a esta columna se mantienen compatibles: el cliente también detecta la palabra moto en el titular hasta que se vuelvan a procesar.

## Controles de calidad y volumen

- Las URL repetidas no se insertan por la restricción única de base.
- Durante una corrida se omite el mismo titular normalizado dentro de la misma categoría antes de geocodificarlo.
- El geocodificador está limitado al área de CABA/GBA y se conserva el radio de precisión: intersección (80 m), calle (150 m) o barrio/partido (800 m).
- Cada medio tiene un límite de URLs por corrida y pausas entre peticiones. Aumentar volumen significa sumar ejecuciones regulares y fuentes permitidas, no descargar de forma agresiva un sitio.

La fuente agregadora puede repetir una nota ya vista en un medio directo, alterar títulos o enlazar una redirección. Por eso no debe considerarse un conteo de incidentes ni alimentar directamente el modelo predictivo. A09 sigue abierto hasta medir precisión, duplicación semántica y error geográfico con un conjunto humano etiquetado.

## Redes sociales y nuevas fuentes

No se automatizan cuentas ni se evaden restricciones de una red social. Para incorporar una red o una institución se requiere uno de estos caminos: API oficial con credenciales y términos vigentes, RSS/archivo público permitido, o exportación que la organización entregue. Antes de habilitarla se registra nombre, URL/API, alcance geográfico, fecha, licencia/términos, frecuencia, campos disponibles y resultado de una corrida de prueba.

La expansión práctica siguiente es agregar fuentes verificadas a las listas del scraper, ejecutar en seco, revisar cuántas candidatas se ubican y recién después guardar. La frecuencia y el tamaño de la base se deben decidir junto con la capacidad de PostgreSQL y el límite de Nominatim.
