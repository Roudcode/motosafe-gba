# Despliegue del MVP productivo

**Estado:** preparación reproducible. Este documento no declara que exista un
servicio público desplegado todavía.

## Arquitectura objetivo

El MVP publicado usa cuatro procesos separados:

1. **web:** Nginx sirve el frontend compilado y reenvía `/api` al backend.
2. **api:** FastAPI aplica migraciones antes de iniciar y atiende sólo dentro
   de la red privada del despliegue.
3. **db:** PostgreSQL con PostGIS conserva reportes y prensa en un volumen
   persistente, sin exponer su puerto a Internet.
4. **scraper:** proceso independiente que ejecuta una ingesta y espera el
   intervalo configurado. Si una corrida falla, deja el error en logs y vuelve
   a intentarlo; no derriba la API ni borra resultados anteriores.

Un proxy con TLS administrado por el proveedor o por el servidor debe exponer
solamente el frontend. El navegador usa `/api`, por lo que API y mapa no
dependen de `localhost`, una IP de LAN ni un túnel temporal.

## Preparación sin secretos en el repositorio

1. Copiar `.env.production.example` a `.env.production`.
2. Generar una contraseña larga y única para `POSTGRES_PASSWORD` y repetirla
   en `DATABASE_URL`, codificada para URL si contiene caracteres reservados.
3. Definir el dominio público definitivo en `CORS_ALLOWED_ORIGINS`.
4. Cargar una clave de TomTom exclusiva de producción y limitarla por dominio
   o IP en el panel del proveedor cuando esa opción esté disponible.
5. Conservar `.env.production` solamente en el gestor de secretos del hosting
   o en el servidor. No copiarlo a documentación, issues ni commits.

## Ejecución reproducible

En un servidor o entorno aislado con Docker Compose:

```powershell
Copy-Item .env.production.example .env.production
# editar .env.production con secretos y dominio reales
docker compose --env-file .env.production -f docker-compose.production.yml up --build -d
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

La primera salida de `api` debe registrar la migración `001_...sql` (o indicar
que ya estaba aplicada). Comprobar desde la red del despliegue:

```powershell
Invoke-WebRequest http://localhost:8080/api/health
docker compose --env-file .env.production -f docker-compose.production.yml logs --tail=100 api scraper
```

En una plataforma gestionada conviene crear los mismos cuatro servicios, con
una base PostgreSQL/PostGIS administrada y una tarea programada que ejecute
`python scrapear_noticias_robos.py --guardar` cada 180 minutos. En ese caso no
se usa el contenedor `scraper` en ciclo: el scheduler del proveedor evita que
se dupliquen ejecuciones.

### Login y datos (verificado el 2026-10-05, SES-067)

- El login de `backend/auth.py` es solo para el acceso personal por Tailscale
  Funnel. `docker-compose.production.yml` y `render.yaml` fijan
  `AUTH_HABILITADO=false`, así que el MVP público no necesita `AUTH_*` ni
  `SESSION_SECRET`. Si la variable falta, el login queda activado y la API no
  arranca sin credenciales: así se evita exponer sin querer la app de Funnel.
- Con una base nueva, el stack levantó sano (`/api/health` ok, migraciones
  aplicadas una sola vez aunque `api` y `scraper` arranquen juntos), pero
  `/api/hotspots`, `/api/corredores` y `/api/hotspots-inseguridad` responden
  500 porque las tablas de datos (`hotspots_riesgo` y otras) las crean los
  scripts `cargar_*.py`, que leen `../data/` y no forman parte de la imagen ni
  del Blueprint. **Pendiente de decisión:** cómo llegan esos datos a producción
  (incluirlos en la imagen, migración semilla o servicio de carga única).

## Ruta rápida en Render

El repositorio incluye `render.yaml`, un Blueprint que crea los recursos sin
copiar contraseñas al repositorio: API privada, sitio web público, cron de
prensa cada tres horas y PostgreSQL 16. Render permite PostGIS en PostgreSQL
administrado; la migración `002_postgis.sql` lo habilita al iniciar.

1. Entrar a [Render](https://dashboard.render.com), iniciar sesión con GitHub
   y elegir **New → Blueprint**.
2. Elegir el repositorio `Roudcode/motosafe-gba` y la rama `main`.
3. Confirmar el Blueprint. Render pedirá únicamente `TOMTOM_API_KEY`; no pegar
   la clave en GitHub ni en el chat.
4. Esperar los builds y abrir la URL `onrender.com` de `motosafe-web`.
5. En el panel de la base, ejecutar una vez `CREATE EXTENSION IF NOT EXISTS
   postgis;` sólo si el log de la migración indicara que no tuvo permisos. En
   condiciones normales la migración lo ejecuta automáticamente.
6. Abrir el historial del cron `motosafe-scraper` y lanzar una corrida manual;
   confirmar que finaliza y que las noticias aparecen en el mapa.

El Blueprint configura la base con plan gratuito sólo para publicar y validar
rápidamente. Según Render, una base gratuita vence a los 30 días, por lo que
no es una operación sostenida. Antes de presentar el MVP como productivo hay
que mover la base a un plan persistente, activar backups y definir presupuesto.

## Operación segura

- Publicar con HTTPS y redirigir HTTP a HTTPS. La geolocalización móvil exige
  contexto seguro fuera de `localhost`.
- Mantener la base privada; administrar acceso mediante la red interna del
  proveedor y respaldos cifrados.
- Revisar `/api/health` y logs de API/scraper al menos una vez al día durante
  el piloto. No registrar ni imprimir `DATABASE_URL`, tokens de borrado ni
  ubicaciones de usuarios en observabilidad.
- Ejecutar backup diario y ensayar una restauración mensual en una base nueva.
  El procedimiento detallado está en `BACKEND_Y_BASE_DE_DATOS.md`.
- Antes de aumentar la frecuencia del scraper, medir duración, volumen,
  duplicación y cumplimiento de condiciones de las fuentes. La frecuencia por
  defecto de tres horas es un punto de partida, no una garantía de actualidad.

## Costos que hay que presupuestar

No se fijan importes aquí porque cambian por proveedor y región. Para comparar
alternativas, calcular por separado:

| Rubro | Unidad a comparar | Variable que más impacta |
|---|---|---|
| Frontend/CDN | GB transferidos y requests | visitas y mapas base |
| API | RAM, CPU y horas activas | cálculos de hotspots/rutas |
| PostgreSQL/PostGIS | tamaño, RAM, IOPS y backups | retención de prensa/reportes |
| Scheduler | ejecuciones y minutos | frecuencia/duración del scraper |
| Mapas/ruteo | transacciones o cuota | búsquedas, rutas y tráfico TomTom |
| Observabilidad | retención de logs/métricas | detalle y período de logs |
| Dominio/TLS | anual o mensual | proveedor y dominio elegido |

Para el piloto, fijar límites de gasto y alertas en TomTom y en el proveedor
cloud antes de abrir el acceso público. Elegir un proveedor recién cuando se
definan región, presupuesto mensual, dominio y volumen esperado; esa decisión
debe quedar registrada en `DECISIONES.md`.

## Criterio de entrega productiva

La preparación se considera lista para despliegue cuando `docker compose ...
config` valida la configuración y los artefactos construyen. Se considera
**productivo** sólo después de registrar evidencia de: despliegue HTTPS,
migración en base aislada, `/health` verde, una corrida programada, backup y
restauración, pruebas de flujos críticos y límites de gasto activos.
