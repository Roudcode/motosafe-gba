# V07 — detalle de zona con explicación progresiva (2026-10-22, SES-162)

Criterio de cierre: "Primero conclusión y fecha; fuente y método ampliables sin saturar." Depende de A11
(ya validado).

## Qué había antes (revisado en `DetalleZonaPanel.jsx` real)

Ya mostraba la conclusión primero (nivel de gravedad estimado + nombre de zona + motivo en texto), pero:

- **Hallazgo real 1**: no había ninguna fecha. Ningún período de los datos que arman el nivel mostrado --
  el criterio de cierre nombra "fecha" explícitamente y no estaba en ningún lado del panel.
- **Hallazgo real 2**: "fuente y método" no eran ampliables -- el desglose de probabilidad del modelo
  (`prediccionModelo`, LEVE/GRAVE/MORTAL con barras) y la explicación del ajuste ("Subió por: ...") se
  mostraban siempre, sin ningún toggle, a diferencia del patrón "Ver cómo se calcula" que ya existe en
  `RutaResumenPanel.jsx` para un problema parecido (texto de más, siempre visible, sin necesidad).

## Qué se cambió

1. **Fecha**: nuevo párrafo `.detalle-periodo` debajo del nivel, con el período real de los datos de
   siniestros (`coberturaCapas.hotspots`, mismo dato y misma función `formatearPeriodo` que ya usa
   `LegendStack.jsx` para la misma capa -- no se inventó un dato nuevo, se reusó el que ya viaja por
   `App.jsx`). Se agregó `coberturaCapas` como prop nueva del componente.
2. **Fuente y método ampliables**: el desglose de probabilidad del modelo y la explicación de "Subió por"
   quedan detrás de un toggle nuevo ("Ver fuente y método" / "Ocultar fuente y método"), reusando la misma
   clase visual que ya existe (`ruta-detalle-toggle`, mismo ícono `ChevronDown`/`ChevronUp`) -- no se
   inventó un componente nuevo, se reutilizó el patrón ya validado en otro panel. El toggle solo aparece si
   hay algo que ampliar (`prediccionModelo` o `ajuste.subio`).

## Qué queda siempre visible (no es "método", es la conclusión o una alerta vigente)

- Nivel de gravedad estimado, nombre de zona y motivo (conclusión).
- El aviso de ajuste por reporte de prensa reciente (`ajustadoPorReciente`) -- no se movió detrás del
  toggle: es información vigente ahora mismo (algo pasó hace poco cerca), no una explicación de método
  histórico, y ocultarla detrás de un clic podría hacer que alguien se la pierda.

## Verificación

- `eslint src/`: limpio.
- `vitest run`: 108/108 (sin tests nuevos -- no hay test de componente propio de `DetalleZonaPanel` hoy;
  mismo criterio que V06, que tampoco lo tenía).
- `vite build`: compila sin errores.
- No se verificó en pantalla real (sin credencial de acceso a la app).

## Qué no se tocó

Ningún dato nuevo del backend -- la fecha ya viajaba en `coberturaCapas`, solo no llegaba a este
componente. No se cambió el cálculo de `prediccionModelo` ni del ajuste.

## Actualización 2026-10-22 (SES-163)

Con sesión real disponible, se intentó abrir el panel de detalle tocando una zona real del mapa (hexágono),
pero no se logró un click confiable sobre la capa GL del mapa desde esta herramienta de automatización (el
mapa recalcula posiciones por proyección/zoom, y los intentos de click por coordenada no dispararon el
`onClickZona`) -- no es evidencia de un bug, es una limitación de esta sesión de verificación, no del
código. El cambio queda respaldado por lint/tests/build en verde y por la revisión directa del código
(prop nueva correctamente enchufada en `App.jsx`, mismo patrón de toggle ya probado en `RutaResumenPanel`).
Verificación visual puntual de este panel específico queda pendiente para una próxima sesión con mejor
control de clicks sobre el mapa (o con Rodo probándolo directo).
