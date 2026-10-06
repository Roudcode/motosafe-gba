# T06 — Ensayo real de backup y restauración (SES-071)

Fecha: 2026-10-06. Sin tocar la base personal: todo ocurrió en contenedores `postgis/postgis:16-3.4` desechables, en una red Docker propia, que se borraron al terminar.

## Pasos

1. **Origen:** base `motosafe_gba` armada con `migrar.py` y los tres `cargar_*.py` del repo, con 740 hotspots, 243 corredores y 633 + 502 zonas de inseguridad. Se le agregaron un reporte y un voto creados por la API.
2. **Backup**, según `docs/operacion/BACKEND_Y_BASE_DE_DATOS.md`:
   - `pg_dump --format=custom` con el cliente del mismo contenedor (PostgreSQL 16.4).
   - Archivo `motosafe_20261006.dump`: 242.382 bytes, SHA256 `3154a50686af9c90…`. Se borró al terminar porque solo contenía datos de prueba.
3. **Restauración** en otra instancia: `createdb motosafe_restore` y `pg_restore --clean --if-exists --no-owner`, con código de salida 0 y sin advertencias.
4. **Comparación** (`comparacion_origen_restaurada.txt`): hash md5 del contenido ordenado de cada tabla, cantidad y definición de constraints, versión de PostGIS y geometrías inválidas. **Origen y restaurada dieron idénticas** (`diff` vacío).
5. **API sobre la base restaurada** (`api_sobre_restaurada.txt`):
   - `/health` ok.
   - Las cuatro capas completas.
   - El reporte restaurado conserva su voto.
   - Un reporte nuevo recibe id 2, lo que confirma que la secuencia se restauró, y se borra con su token.

## Límites

- Volumen de prueba (unos 240 kB). No se midió el tiempo con la base real de Rodo ni con la tabla `reportes_prensa` (la crea el scraper, no las migraciones).
- No se ensayó en el proveedor de hosting: Render no da acceso a `pg_dump` en el plan gratuito sin configuración adicional.
- No se probó la restauración sobre una base existente con datos: `--clean` borra y recrea los objetos del dump.
