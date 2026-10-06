# Re-geocodificación de las filas históricas de prensa (SES-073)

Fecha: 2026-10-06. Decisión de Rodo: re-geocodificar las filas de `reportes_prensa` ubicadas con el método anterior a SES-069, con un backup previo.

## Backup previo

Los archivos quedaron fuera del repositorio, en `C:\Users\rodol\motosafe_backups\`:

- `motosafe_gba_pre_regeo_20261006.dump`: `pg_dump --format=custom` de la base de desarrollo completa, 350.864 bytes, SHA256 `055ba1d601283e4d…`. Se verificó que `pg_restore --list` lo lee e incluye los datos de `reportes_prensa`.
- `reportes_prensa_pre_regeo_20261006.csv` y `reportes_prensa_post_regeo_20261006.csv`: la tabla antes y después.

Para volver atrás: `pg_restore --clean --if-exists --no-owner --dbname <url> motosafe_gba_pre_regeo_20261006.dump`, o actualizar solo `lat`, `lng`, `nivel_precision` y `radio_metros` desde el CSV previo.

## Método (`regeocodificar_prensa.py`)

La tabla guarda solo el titular. De las 450 filas, 232 vienen de Google Noticias, que no se vuelve a consultar (DEC-011). No se descargó nada de los medios.

1. **Zona (418 filas):** el punto viejo de nivel barrio coincidía exactamente con el resultado del método anterior para una de las 87 zonas medidas (`../A09-geocodificacion/resultado.json`). Se le asignó el punto nuevo validado de esa misma zona.
2. **Titular (9 filas):** se re-extrajo la ubicación del titular y se geocodificó con validación. Si el titular daba menos precisión que la guardada, se verificó con geocodificación inversa si el punto viejo caía en la zona del titular. Si caía, quedó como estaba, por ser preciso y consistente. Si no, se movió al punto de la zona y bajó a nivel barrio (800 m).
3. **Sin cambio (23 filas):** sin pista en el titular, o punto preciso ya dentro de su zona.

## Resultado

Aplicado en una transacción, con guarda de coordenadas viejas en el `WHERE`.

| | Filas |
|---|---|
| Total | 450 (antes y después) |
| **Cambiaron de ubicación** | **142** |
| — corrigen una nota ubicada en otro partido o barrio | 94 (La Matanza 87, Tres de Febrero 2, Malvinas Argentinas 1, Almirante Brown 1, más 3 re-extraídas del titular) |
| — misma zona, otro punto representativo (mediana 516 m, máximo 4,7 km) | 44 |
| — re-extraídas del titular | 7 (3 bajaron a nivel barrio por estar fuera de su zona) |
| Desplazadas más de 20 km | 95 |
| Otras columnas modificadas | 0 |

Las 87 de La Matanza estaban en Presidente Perón, por la calle homónima medida en `../A09-geocodificacion/`. 72 de las 142 filas corregidas venían de Google Noticias.

El detalle por fila está en `propuesta.csv`: método, punto viejo y nuevo, distancia y si el anterior caía en otra zona. La verificación posterior comparó el export de la base antes y después: las 142 filas que cambiaron son exactamente las propuestas.

## Límites

- 23 filas quedaron sin cambio. Entre ellas hay notas de fuera del GBA (Mar del Plata) que no se pueden validar sin la descripción original.
- Las filas de calle o intersección dentro de su zona conservan su punto, que no se pudo revalidar a nivel calle.
