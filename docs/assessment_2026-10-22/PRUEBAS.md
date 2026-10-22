# Ejecuciones de auditoría — 22/10/2026

- Frontend: Vitest 7 archivos, **108 passed**, 2,57 s. Primer intento sandbox falló ENOENT en caché (70 tests pasados); la repetición externa pasó completa.
- ESLint: exit 0.
- Build separado (`vite build --outDir dist_assessment`): 1853 módulos, exit 0, 2,41 s; mapa JS 1037,98 kB (277,28 gzip), worker 487,10 kB. Advertencia >500 kB. Se retiró sólo ese build temporal.
- Backend: `venv312/Scripts/python.exe -m pytest tests -q`, con MOTOSAFE_TEST_DATABASE_URL del contenedor exclusivo: **157 passed, 3 failed, 1 warning, 30,90 s**. Sin skips en esa corrida. Primer intento sandbox sin salida se interrumpió.
- Probes: API/SQL reales en base aislada, proveedores/mail simulados, exit 0; resultados en los archivos adjuntos. Primer harness Node necesitó ajustar resolución de imports e import.meta.env; no se modificaron funciones de cálculo.

## Fallos de backend

1. `test_auth.py::test_sin_login_la_app_arranca_sin_variables_de_auth_y_no_exige_sesion`: espera registro 404, obtiene 422 por faltar nombre_usuario.
2. `test_integracion_postgres.py::test_carga_inicial_solo_llena_tablas_vacias`: espera 1135 hotspots de inseguridad, obtiene 1121 (619+502). 740 hotspots viales y 243 corredores sí coinciden.
3. `test_integracion_postgres.py::test_flujo_completo_reset_password`: alta sin nombre_usuario, no se crea la cuenta y codigo_reset es None. El probe separado usa un alta válida y demuestra el fallo de códigos anteriores.

Warning StarletteDeprecationWarning: uso de httpx con TestClient; no causa esos fallos.

## Aislamiento

Contenedor `motosafe-assessment-20261022`, postgis/postgis:16-3.4, puerto 127.0.0.1:55439, credenciales ficticias. Bases aleatorias creadas y borradas por cada suite/probe. Contenedor y volumen eliminados mediante docker stop y docker rm -v al cerrar; ambas órdenes exitosas. No se modificó ni detuvo motosafe-db. No se enviaron correos ni solicitudes de pago, ni se hizo carga contra servicios públicos.

## Límite de herramientas al cerrar

El sandbox dejó de responder en un intento de escritura de PRUEBAS.md; se comprobó fuera del sandbox que el archivo no existía y el índice Git seguía vacío. Se canceló esa orquestación antes de su paso Git y se completó el cierre fuera del sandbox. No se presenta ese intento como una operación exitosa.
