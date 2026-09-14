# Ingesta de prensa multifluente

Actualizado: 2026-09-14. Esta guía describe la capa de noticias de MotoSafe GBA; no es una fuente estadística oficial ni reemplaza los datos históricos de siniestros o delitos.

## Qué entra a la capa

`backend/scrapear_noticias_robos.py` consulta únicamente fuentes periodísticas directas mediante RSS, sitemap o secciones públicas. Cada punto conserva el enlace de origen y la fuente que lo entregó.

El proceso acepta sólo noticias con una categoría textual y una ubicación plausible dentro del área acotada. Clasifica el hecho como `robo`, `inseguridad` o `choque`. `relacionado_moto` es otro atributo: vale verdadero sólo cuando el título o la descripción mencionan explícitamente una motocicleta, moto o motociclista; no se infiere desde una zona, una foto ni el medio. La expresión “moto de agua” queda excluida. En RSS se conserva `pubDate`; en páginas HTML se toma `article:published_time`, `datePublished` o JSON-LD. La vigencia, el orden y la antigüedad visible usan esa fecha real y recurren a la fecha de ingesta sólo si la fuente no la entrega.

Esto permite que el filtro **Motos** muestre robos, inseguridad y choques vinculados a motos sin convertir al resto de la capa en una capa exclusivamente de motos. Las entradas históricas previas a esta columna se mantienen compatibles: el cliente también detecta la palabra moto en el titular hasta que se vuelvan a procesar.

## Controles de calidad y volumen

- Las URL repetidas no se insertan por la restricción única de base.
- `url_fuente` usa tipo `TEXT` para conservar enlaces de fuentes directas sin truncamiento.
- Durante una corrida se omite el mismo titular normalizado dentro de la misma categoría antes de geocodificarlo. La firma conserva el titular editorial completo y no aplica deduplicación semántica.
- El geocodificador está limitado al área de CABA/GBA y se conserva el radio de precisión: intersección (80 m), calle (150 m) o barrio/partido (800 m).
- Cada medio tiene un límite de URLs por corrida y pausas entre peticiones. Aumentar volumen significa sumar ejecuciones regulares y fuentes permitidas, no descargar de forma agresiva un sitio.
- Al finalizar, el scraper informa candidatas, duplicadas, ubicadas, vinculadas a motos y el desglose por fuente. Ese resumen debe conservarse al evaluar si una nueva fuente agrega cobertura real o sólo repite notas.
- Cada inserción está aislada por un savepoint: una URL o fila inválida se informa y se omite sin revertir las noticias válidas de la corrida.

La capa de prensa no debe considerarse un conteo de incidentes ni alimentar directamente el modelo predictivo. A09 sigue abierto hasta medir precisión, duplicación semántica y error geográfico con un conjunto humano etiquetado.

### Evidencia de corrida del 2026-09-13

La corrida histórica previa al retiro de Google Noticias encontró 560 candidatas, ubicó 289 y guardó 267; 99 candidatas estuvieron vinculadas a motos. De las 267 guardadas, 234 provinieron del agregador. Esa corrida no es comparable con las corridas posteriores y no representa la cobertura vigente. Se conserva como evidencia histórica del cambio de alcance, no como medición de precisión o representatividad.

### Retiro de Google Noticias

El 2026-09-14 se retiraron todas las consultas RSS de Google Noticias. La decisión responde a la restricción declarada por su `robots.txt` para `/rss/` y al criterio de no sostener la ingesta en una vía cuya automatización no está permitida. La caída de volumen es parte de la limitación explícita de cobertura: de las 267 guardadas en la corrida histórica, 234 provenían del agregador y sólo 33 de medios directos. La primera corrida sin el agregador encontró 122 candidatas, ubicó 57 y guardó 4 filas nuevas; el número de inserciones refleja que muchas notas directas ya estaban en la base. Las futuras comparaciones deben indicar el conjunto de fuentes utilizado; un menor volumen posterior no implica por sí mismo una falla del scraper.

## Redes sociales y nuevas fuentes

No se automatizan cuentas ni se evaden restricciones de una red social. Para incorporar una red o una institución se requiere uno de estos caminos: API oficial con credenciales y términos vigentes, RSS/archivo público permitido, o exportación que la organización entregue. Antes de habilitarla se registra nombre, URL/API, alcance geográfico, fecha, licencia/términos, frecuencia, campos disponibles y resultado de una corrida de prueba.

La expansión práctica siguiente es agregar fuentes verificadas a las listas del scraper, ejecutar en seco, revisar cuántas candidatas se ubican y recién después guardar. La frecuencia y el tamaño de la base se deben decidir junto con la capacidad de PostgreSQL y el límite de Nominatim.

## Fechas ya almacenadas

Las filas antiguas pueden no tener `publicado_en` porque fueron descubiertas antes de que el scraper conservara metadatos editoriales. `backend/actualizar_fechas_prensa.py` revisa sus URLs y completa sólo las fechas que la página declara; no altera ubicación, categoría ni inserta una noticia nueva. Se ejecuta por lotes y con pausa para respetar a los medios.
