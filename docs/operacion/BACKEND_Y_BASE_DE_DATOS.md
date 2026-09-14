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

## Validación pendiente T01

La aceptación requiere una base efímera: aplicar migraciones dos veces,
comprobar que la segunda no cambia el esquema, crear/votar/borrar un reporte y
forzar una excepción para verificar rollback y recuperación del pool. No se
declara completado hasta ejecutar ese escenario contra PostgreSQL real.

## Backup y restauración

Usar herramientas compatibles con la versión del servidor:

```powershell
pg_dump --format=custom --file motosafe_YYYYMMDD.dump $env:DATABASE_URL
createdb motosafe_restore
pg_restore --clean --if-exists --no-owner --dbname $env:DATABASE_URL_RESTORE motosafe_YYYYMMDD.dump
```

El backup contiene reportes y potencialmente ubicaciones: guardarlo fuera del
repositorio, con acceso limitado. T06 se cierra sólo tras restaurar un backup
en una instancia aislada y registrar fecha, tamaño y resultado sin publicar
datos.

## CI

`.github/workflows/ci.yml` ejecuta lint, pruebas y build del frontend, más
sintaxis del backend en Python 3.12. No reemplaza T01: la CI actual no levanta
PostgreSQL ni servicios externos.

## Entorno productivo

`docker-compose.production.yml` separa web, API, scraper y PostGIS. No publica
el puerto de la base y deja el frontend como único puerto expuesto. La API
ejecuta migraciones al iniciar; el scraper aplica las mismas migraciones antes
de su ciclo. Copiar `.env.production.example` a `.env.production`, que está
ignorado por Git, y no reutilizar secretos de desarrollo.
