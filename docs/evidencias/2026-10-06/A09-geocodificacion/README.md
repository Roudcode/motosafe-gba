# A09 — Geocodificación de zonas de prensa (SES-069)

Fecha: 2026-10-06. Origen: en la corrida del scraper dentro del compose de producción (SES-067), la nota «Monte Grande: un detenido por el robo de un auto» quedó en (-34.53, -58.51), en Munro (Vicente López), a unos 33 km de Monte Grande.

## Causa

- `encontrar_zona` traduce el alias «Monte Grande» al partido «Esteban Echeverría» y la consulta era `Esteban Echeverría, Buenos Aires, Argentina`. Nominatim devolvía la **calle** Esteban Echeverría de Munro. El geocode no validaba en qué partido caía el resultado.
- Muchos partidos y barrios tienen nombres de personas que también son calles, estaciones o parques.

## Medición sobre todo el gazetteer (`medir_zonas.py`)

Se midieron 30 partidos/localidades, 9 alias y 48 barrios. Cada punto se verificó por **geocodificación inversa** (`/reverse`), independiente del código evaluado: en qué partido o barrio cae realmente.

| Tipo | Método anterior: bien / mal | Método nuevo: bien / mal |
|---|---|---|
| Partidos | 25 / 5 | 30 / 0 |
| Alias | 5 / 4 | 9 / 0 |
| Barrios de CABA | 46 / 2 | 48 / 0 |
| **Total** | **76 / 11 (12,6 % mal)** | **87 / 0** |

Errores del método anterior (`resultado.txt`):

| Zona | Dónde caía |
|---|---|
| Esteban Echeverría y Monte Grande | Vicente López |
| Almirante Brown y Don Orione | General Rodríguez (parque homónimo) |
| Malvinas Argentinas y Grand Bourg | la localidad homónima de Almirante Brown |
| La Matanza y Virrey del Pino | Presidente Perón |
| Tres de Febrero | CABA |
| Belgrano | estación Belgrano, en Monserrat |
| Vélez Sarsfield | estación Floresta |

## Cambio (`backend/scrapear_noticias_robos.py`)

1. `geocodificar_en_zona`: en el nivel `barrio` consulta con `featureType=settlement` (solo lugares y límites administrativos) y valida que el resultado pertenezca a la zona de la nota (`resultado_en_zona`). Si no valida, prueba `Partido de X`. Si nada valida, la nota no se ubica.
2. En los niveles calle e intersección se valida el partido, o CABA si la zona es un barrio, y no el barrio exacto: cerca de un límite Nominatim puede informar el barrio vecino.
3. El partido del resultado se lee de `state_district`/`county`, de `town`/`city` cuando dicen «Partido de…», o de `display_name` (caso Burzaco). Se aceptan variantes reales de OSM («General San Martín», «Partido del Pilar»).
4. `encontrar_zona` ya no toma como zona un nombre seguido de «al <número>» («Almirante Brown al 500» es una calle). Caso real: una nota de Grand Bourg terminaba ubicada en Almirante Brown.
5. El resumen del scraper separa «geocode vacío» de «fuera de la zona».

## Corrida real del scraper (modo prueba, sin guardar)

| | Antes del ajuste final (`corrida_dry_run_antes_del_ajuste.txt`) | Final (`corrida_dry_run.txt`) |
|---|---|---|
| Candidatas | 132 | 132 |
| Ubicadas | 78 | 79 |
| Sin resultado en Nominatim (también fallaban antes) | 29 | 29 |
| Fuera de zona (abstención) | 3 | 2 |

`revisar_rechazos.py` revisó cada abstención:

- Las 2 finales son correctas: el extractor había tomado dos partidos como si fueran una esquina («Florencio Varela y Quilmes», «Avellaneda y Lanús») y el resultado caía en otro partido.
- La tercera de la primera corrida («Almirante Brown 500») llevó a los ajustes 3 y 4.
- Monte Grande ahora queda en (-34.825, -58.477) y la nota de Grand Bourg, en (-34.491, -58.742).

## Límites

- La medición de zonas cubre el nivel `barrio`. La validación de calles e intersecciones se comprobó solo con la corrida real; no hay conjunto etiquetado de direcciones.
- Las filas ya guardadas en `reportes_prensa` con coordenadas del método anterior no se corrigieron. Hacerlo requiere escribir en la base de Rodo.
- El extractor sigue leyendo «X y Y» como intersección aunque X e Y sean partidos. Ahora se abstiene, pero no los ubica.
- Las respuestas de Nominatim cambian con las ediciones de OSM; `cache_nominatim.json` conserva las usadas.
