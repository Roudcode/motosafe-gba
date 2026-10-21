# T06 — ensayo de backup/restauración con el volumen persistente real, en local (2026-10-21)

Lo que faltaba según la propia fila de T06 en `BACKLOG.md` era ensayarlo "con el volumen real y en el
proveedor de hosting". Confirmado antes de arrancar (`docs/operacion/DESPLIEGUE_MVP.md`: *"Este documento
no declara que exista un servicio público desplegado todavía"*) que no hay ningún despliegue público ni
cuenta en ningún proveedor -- no hay producción real a la que arriesgar, y ningún proveedor real fue
tocado. **No se creó ninguna cuenta en ningún proveedor de hosting, no se ingresó ninguna tarjeta ni dato
de pago en ningún lado.**

Este ensayo corrió la **composición real de producción** (`docker-compose.production.yml`) en local, con
un volumen Docker nombrado persistente de verdad (no `--rm`, no efímero) -- no contenedores sueltos armados
a mano como en el ensayo anterior (SES-071).

## Entorno

- `.env` de prueba propio (`T06-ensayo.env`, en el scratchpad de la sesión, nunca commiteado): contraseña
  de PostGIS inventada para este ensayo (`ensayo_t06_password_de_prueba_no_real`), `TOMTOM_API_KEY` con un
  valor de prueba no real (no se probó `/rutas`, fuera de alcance de este ensayo), base y usuario con
  nombre `_ensayo` para no confundirlos nunca con algo real.
- `docker compose -f docker-compose.production.yml --env-file T06-ensayo.env -p motosafe-t06-ensayo up -d
  --build`: levantó los 4 servicios reales (`db`, `api`, `scraper`, `web`) con sus Dockerfiles reales, sin
  modificar nada del compose ni del backend/frontend.
- Volumen nombrado real: `motosafe-t06-ensayo_motosafe_postgres_data` (no anónimo, no `--rm`).
- `motosafe-db` (el contenedor real de 5432 que usa `DATABASE_URL` de desarrollo) nunca se tocó --
  verificado `docker ps` antes y después, siguió corriendo sin interrupción.

## Contenido real cargado

La carga inicial (`cargar_datos_iniciales.py`, vía el entrypoint real de `api`) trajo las capas reales
desde `./data` montado de solo lectura: 740 hotspots, 243 corredores, 1135 zonas de inseguridad. Sobre eso,
contenido escrito de verdad a través de la API real (no insertado a mano salvo una fila de prensa):

- 3 reportes colaborativos reales (`POST /reportes`).
- 1 confirmación real (`POST /reportes/{id}/confirmar`).
- 1 fila de prensa insertada directo por SQL para tener contenido inmediato en esa tabla (más las que el
  `scraper` real fue agregando solo, en vivo, mientras corría el ensayo -- ver abajo).

## Dump

`pg_dump --format=custom` real desde dentro del contenedor `db` (PostgreSQL 16.4): `motosafe_t06_ensayo.dump`,
247.186 bytes. Hash de contenido tomado ANTES del dump, por tabla (`md5(string_agg(t.*::text, '|' ORDER BY
id))`, ordenado por `id` para que sea determinístico):

| Tabla | md5 (antes del dump) |
|---|---|
| hotspots_riesgo | `a99cc86a510566275d6398e296313976` |
| corredores_riesgo | `cf0ae22e1ccb2871ae73c725e38e9dc1` |
| hotspots_inseguridad | `12b9484af18526338c44cf847449db72` |
| reportes_colaborativos | `b11a9dc73b73765ab93ccf4b6e3c6290` |
| reportes_confirmaciones | `22bb723bad0d1955ec27454cb67fc789` |
| reportes_prensa | `f440afa45faf3bbf6cc7402421cea0db` |

## Paso 1 — reinicio real sin perder el volumen

`docker compose ... -p motosafe-t06-ensayo down` (sin `-v`), simulando un reinicio real del contenedor:
confirmado el volumen `motosafe-t06-ensayo_motosafe_postgres_data` seguía existiendo (`docker volume ls`)
después de bajar todo. `docker compose ... up -d` de nuevo, sin tocar el dump: `/health` ok, y los hashes de
las seis tablas se volvieron a medir.

**Resultado real, no esperado de antemano**: 5 de 6 tablas dieron el mismo hash. `reportes_prensa` cambió
(`f440afa4...` → `3c007695...`) -- no es una pérdida ni una corrupción: el conteo subió de 4 a 8 filas. El
`scraper` real del compose (`scraper-loop.sh`) siguió corriendo todo el tiempo y agregó 4 notas reales más
mientras duraba el ensayo (confirmado con `max(creado_en)` de la tabla, timestamp reciente real). Confirma
que el volumen no solo no perdió nada al reiniciar, sino que el servicio de fondo siguió escribiendo sobre
él con normalidad.

## Paso 2 — restauración real en una instancia nueva y descartable

Para probar la restauración en sí (no solo la persistencia), se restauró el dump (tomado en el paso
anterior, antes del reinicio) en un PostGIS 16 **completamente nuevo y descartable** (`motosafe-t06-restore`,
puerto 55434, nunca `motosafe-db` ni el volumen del ensayo): `pg_restore --no-owner`, código de salida 0,
sin advertencias.

Hashes de la base restaurada, mismas seis tablas, mismo método: **idénticos a la tabla de arriba, incluida
`reportes_prensa` (`f440afa4...`, el valor de ANTES de que el scraper agregara más filas -- correcto, porque
el dump se tomó en ese momento).** Restauración byte-a-contenido-idéntica confirmada.

## Paso 3 — API real sobre la copia restaurada

Se corrió la imagen real de `api` (ya construida por el compose) apuntando `DATABASE_URL` a la base
restaurada (red Docker separada, contenedor nuevo `motosafe-t06-restore-api`):

- `/health` → `ok`.
- `/hotspots` → datos reales (740 zonas).
- `/reportes/mios` con el `delete_token` real del reporte id=1 → lo recupera con su confirmación intacta
  (`"confirmaciones":1`) -- confirma que la credencial privada (hash del token) y la relación con
  `reportes_confirmaciones` sobrevivieron la restauración.
- Un reporte nuevo (`POST /reportes`) recibe **id=4** -- confirma que la secuencia de PostgreSQL se
  restauró correctamente (no volvió a empezar en 1).

## Límites declarados

- Volumen de prueba chico (unos cientos de KB más las capas reales de 740/243/1135 filas); no mide tiempos
  de dump/restore con el volumen de producción real, que no existe todavía.
- Sigue sin ensayarse contra ningún proveedor de hosting real -- no corresponde todavía, porque no hay
  ningún despliegue público (confirmado al principio de este documento).
- `TOMTOM_API_KEY` fue un valor de prueba; no se probó `/rutas` en este ensayo (fuera de alcance: T06 es
  sobre persistencia de datos, no sobre todos los servicios externos).

## Limpieza

Todos los contenedores, la red y el volumen de prueba se borraron al terminar (`docker compose down -v`,
`docker rm`, `docker network rm`, `docker rmi` de las tres imágenes construidas para el ensayo).
`motosafe-db` (el real) siguió corriendo sin interrupción durante todo el ensayo.

## Conclusión

Con la composición real de producción y un volumen nombrado persistente real (no contenedores sueltos), se
confirmó que: (1) un reinicio real del stack sin `-v` no pierde nada del volumen, y el `scraper` de fondo
sigue escribiendo con normalidad sobre él; (2) `pg_dump`/`pg_restore` reales producen una copia
byte-a-contenido-idéntica de las seis tablas en una instancia nueva; (3) la API real funciona de punta a
punta sobre esa copia, incluidas credenciales privadas y secuencias de id. Lo único que falta del
pendiente original ("el proveedor de hosting") no es ensayable todavía porque genuinamente no existe un
despliegue en ningún proveedor -- no es una tarea pendiente de este ensayo, es una dependencia real que
todavía no se cumple.
