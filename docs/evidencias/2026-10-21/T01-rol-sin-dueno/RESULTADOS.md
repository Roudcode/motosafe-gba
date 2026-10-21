# T01 — permisos mínimos reales de un rol sin privilegios de dueño (2026-10-21, SES-149)

Objetivo: encontrar el conjunto mínimo real de privilegios que necesita un rol de PostgreSQL SIN
superusuario/dueño para que el backend funcione, corriendo `tests/test_integracion_postgres.py` con ese
rol contra un PostGIS descartable -- nunca contra `motosafe-db` (el contenedor de 5432 que usa
`DATABASE_URL` real) ni la base personal de Rodo.

## Entorno descartable

Contenedor nuevo y separado: `docker run -d --name motosafe-test-postgis -e POSTGRES_PASSWORD=postgres -p
55433:5432 postgis/postgis:16-3.4` (puerto 55433, no 5432). `motosafe-db` (el real) nunca se tocó --
verificado que siguió corriendo sin interrupciones (`docker ps` antes/después). El contenedor de prueba se
borró al terminar (`docker rm -f motosafe-test-postgis`).

## Mecanismo

`tests/test_integracion_postgres.py` ya crea una base nueva por corrida como administrador
(`MOTOSAFE_TEST_DATABASE_URL`, pensado exactamente para esto) y la migra con `migrar.py` -- eso necesita
privilegios de dueño/DDL y así debe seguir siendo (migrar el esquema es una operación de administración,
no algo que haga el backend en producción). Lo que faltaba probar es **con qué rol se conecta el backend
en sí** (el pool de `main.py`) para servir pedidos reales.

Se agregaron temporalmente dos variables de entorno opcionales a dos fixtures del archivo
(`migrada`/`pool_real`), sin cambiar nada del comportamiento por defecto (si no están seteadas, el archivo
se comporta exactamente igual que antes):

- `MOTOSAFE_TEST_ROL_SIN_DUENO`: si está seteada, el pool de la app (`pool_real`) se conecta con ESE rol en
  vez del admin.
- `MOTOSAFE_TEST_GRANTS_SQL`: sentencias `GRANT` (separadas por `;`, con `{rol}`/`{db}` como placeholders)
  que el admin ejecuta sobre la base recién migrada, antes de que el pool se conecte con el rol limitado.
  Vacía por defecto -- permite probar explícitamente "cero permisos" primero.

Este cambio queda sin commitear (el `git diff` lo muestra); es un agregado útil para repetir esta
verificación más adelante, pero la decisión de si conservarlo es de Rodo.

## Resultado real, medido por iteración

1. **Rol recién creado, sin ningún GRANT** (`CREATE ROLE motosafe_app_sin_dueno LOGIN PASSWORD '...'
   NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION`): confirmado primero con una conexión directa de
   control (otro rol, otra tabla) que Postgres de verdad deniega sin privilegios
   (`psycopg2.errors.InsufficientPrivilege: permission denied for table t`) -- así el resultado de abajo no
   es un falso "pasa porque no se está probando nada de verdad.
2. **Con `CONNECT` + `USAGE` en el schema + `SELECT/INSERT/UPDATE/DELETE` en todas las tablas, SIN tocar
   las secuencias**: 2 tests fallan reales --
   `psycopg2.errors.InsufficientPrivilege: permission denied for sequence reportes_colaborativos_id_seq`
   al crear un reporte nuevo (columnas `SERIAL`, no `GENERATED ... AS IDENTITY`, así que `nextval()` pide
   su propio privilegio aparte de la tabla).
3. **Agregando `GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA public`**: 11/11 pasan.
4. **Reducido a solo `GRANT USAGE ON ALL SEQUENCES`** (sin `SELECT` sobre las secuencias, que no hace falta
   para `nextval()`): **11/11 siguen pasando** -- este es el conjunto mínimo real encontrado, no solo uno
   que funciona.

### Conjunto mínimo real confirmado

```sql
GRANT CONNECT ON DATABASE <base> TO <rol>;
GRANT USAGE ON SCHEMA public TO <rol>;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO <rol>;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO <rol>;
```

Sin `CREATEDB`, sin `CREATEROLE`, sin superusuario, sin ser dueño de ninguna tabla. `tests/
test_integracion_postgres.py` completo (11/11, incluidos los dos tests que usan `TestClient` contra el
backend real con el pool corriendo bajo este rol) pasa igual que con el administrador.

## Qué no se cubrió

- No se probó remover `DELETE` o `UPDATE` uno por uno para confirmar que cada uno es estrictamente
  necesario (son los verbos que ya usan endpoints reales de `main.py` -- borrar reportes, actualizar estado
  -- así que quitarlos haría fallar funcionalidad real conocida, no solo un test; no se consideró necesario
  medirlo por separado).
- `CREATE EXTENSION postgis` y las migraciones en sí siguen necesitando un rol con privilegios de dueño --
  eso es correcto y esperado (DDL de administración, no tráfico de la aplicación), no un hallazgo.

## Conclusión

El conjunto mínimo real para el rol que conecta el backend en producción es: `CONNECT` a la base, `USAGE`
en el schema `public`, `SELECT/INSERT/UPDATE/DELETE` en todas las tablas, y `USAGE` (no `SELECT`) en todas
las secuencias. Ningún privilegio de dueño, `CREATEDB` o superusuario hace falta para que el backend
funcione de punta a punta contra Postgres/PostGIS real.
