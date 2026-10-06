# Operación del backend y base de datos

**Ítems:** A12, A14, T01, T04, T05, T06.  
**Estado:** procedimientos y CI incorporados; la composición productiva está
preparada en `docker-compose.production.yml`, pero falta ensayo contra
PostgreSQL aislado y despliegue HTTPS real. Ver `DESPLIEGUE_MVP.md`.

## Inicio seguro

1. Copiar `.env.example` a `backend/.env` y definir una `DATABASE_URL` local.
2. Levantar PostgreSQL/PostGIS con `docker compose up -d db`.
3. Desde `backend`, ejecutar `python migrar.py`. El script registra cada SQL
   aplicado en `schema_migrations`; repetirlo no reaplica archivos ya hechos.
4. Cargar únicamente datos de prueba o los pipelines documentados.
5. Iniciar API y consultar `GET /health`. Devuelve sólo estado de servicio,
   disponibilidad de base y hora UTC; nunca URL, claves, GPS ni usuarios.

## Integración con PostgreSQL real (T01, A12)

`backend/tests/test_integracion_postgres.py` corre contra un servidor
PostgreSQL/PostGIS desechable. Crea una base con nombre aleatorio y la borra
al terminar; nunca usa la base personal ni `DATABASE_URL`. Si no está definida
`MOTOSAFE_TEST_DATABASE_URL`, se saltea.

```powershell
docker run -d --name motosafe-integ-db -e POSTGRES_USER=motosafe -e POSTGRES_PASSWORD=<clave> -p 127.0.0.1:55433:5432 postgis/postgis:16-3.4
$env:MOTOSAFE_TEST_DATABASE_URL = "postgresql://motosafe:<clave>@127.0.0.1:55433/postgres"
python -m pytest -q tests/test_integracion_postgres.py
docker rm -f motosafe-integ-db
```

Cubre:

- migraciones aplicadas una sola vez con cuatro procesos a la vez, e idempotentes;
- PostGIS habilitado;
- límite del pool con conexiones reales;
- conexión reutilizable después de un error SQL (rollback);
- conexión cortada por el servidor (`pg_terminate_backend`): se descarta y la siguiente funciona;
- ciclo de reportes: el token no se guarda en claro, el voto repetido se reemplaza, `ON DELETE CASCADE`;
- `/health` con base real.

Verificado el 2026-10-06 (SES-070) con PostGIS 16.4. Control negativo: sin
el lock de `migrar.py`, el test de concurrencia falla.

Límite conocido: la primera consulta que recibe una conexión cortada por el
servidor falla (500) antes de que el pool la descarte. La siguiente ya
funciona. No hay reintento automático.

## Backup y restauración

Usar herramientas compatibles con la versión del servidor:

```powershell
pg_dump --format=custom --file motosafe_YYYYMMDD.dump $env:DATABASE_URL
createdb motosafe_restore
pg_restore --clean --if-exists --no-owner --dbname $env:DATABASE_URL_RESTORE motosafe_YYYYMMDD.dump
```

El backup contiene reportes y potencialmente ubicaciones: guardarlo fuera del
repositorio, con acceso limitado.

Ensayo real del 2026-10-06 (SES-071, evidencia en
`docs/evidencias/2026-10-06/T06-backup/`): estos tres comandos, con los clientes
de una instancia PostgreSQL 16.4 desechable, restauraron una base idéntica a la
de origen. Dieron iguales el hash del contenido de las seis tablas, las 10
constraints y PostGIS 3.4.3, y la API funcionó sobre la copia, incluida la
secuencia de ids. Usar `pg_dump`/`pg_restore` de la misma versión mayor que el
servidor; en Docker, los del propio contenedor (`docker exec <contenedor> pg_dump ...`).

## CI

`.github/workflows/ci.yml` ejecuta lint, pruebas y build del frontend. En el
backend instala `requirements.lock` con hashes y corre toda la suite de pytest
con un servicio `postgis/postgis:16-3.4`, así que incluye los tests de
integración. No levanta servicios externos (TomTom, Nominatim, Open-Meteo).

## Entorno productivo

`docker-compose.production.yml` separa web, API, scraper y PostGIS. No publica
el puerto de la base y deja el frontend como único puerto expuesto. La API
ejecuta migraciones al iniciar; el scraper aplica las mismas migraciones antes
de su ciclo. Copiar `.env.production.example` a `.env.production`, que está
ignorado por Git, y no reutilizar secretos de desarrollo.
