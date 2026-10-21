# V10 — mensaje específico para "sin datos" real (distinto de error) (2026-10-21, SES-153)

Único hueco que quedaba de V10 según su propia fila en `BACKLOG.md`: una capa que responde 200 con una
lista vacía (sin datos reales en esa zona, no un fallo) no tenía un mensaje distinto del caso de fallo.
Alcance acotado a cerrar específicamente ese hueco -- no se tocó ningún otro ítem del catálogo V.

## Qué capas pueden devolver legítimamente una lista vacía con 200 (revisado en el código real antes de asumir)

Leído `backend/main.py` endpoint por endpoint:

- **`/corredores`**: tiene un `if not resultado: return []` **explícito** -- el propio código ya declara
  que una base vacía de corredores es un camino normal, no un error.
- **`/hotspots-inseguridad?tipo=general|moto`**: hace `SELECT ... WHERE tipo = %s` y devuelve `resultado`
  directo; si esa tabla no tiene filas para un tipo dado, el camino natural también es una lista vacía, sin
  ningún `raise` ni manejo especial de error.
- **`/hotspots`**: queda **fuera a propósito**. Hoy siempre trae las 740 filas reales (no hay ningún código
  que filtre por zona dentro del endpoint); una lista vacía ahí sería un bug real del backend, no un estado
  legítimo de "sin datos en esta zona" -- tratarlo igual que los otros dos habría sido inventar un caso que
  no existe hoy.

Estas mismas tres capas (`corredores`, `inseguridadGeneral`, `inseguridadMoto`) son exactamente las que
`erroresCapas` ya trackea en `App.jsx` -- el aviso nuevo reusa esa misma estructura de estado, no agrega
ningún mecanismo paralelo.

## Implementación

- `App.jsx`: nuevo prop derivado `capasVacias` (objeto `{corredores, inseguridadGeneral, inseguridadMoto}`,
  cada uno `== 0` sobre el estado ya existente) pasado a `CapaErrorBanners`. No se agregó estado nuevo --
  se deriva de los arrays que la app ya mantiene.
- `CapaErrorBanners.jsx`: un banner nuevo, mismo patrón visual que los existentes (`ruta-banner`, mismo
  `panel-enter`), pero **sin el modificador `ruta-banner-error`** (ese agrega el borde rojo de alerta) y
  **sin ícono** (los otros tres usan `WifiOff`, que implica un problema de conexión -- no corresponde acá) y
  **sin botón de reintento** (no tiene sentido reintentar algo que no falló). Solo se muestra para una capa
  si está vacía **y no** está en `erroresCapas` al mismo tiempo (si está fallando de verdad, gana el banner
  de error existente, no el de "sin datos").
- Texto: *"Sin datos registrados todavía en esta zona: {capas}. No es un fallo -- el mapa sigue funcionando
  con el resto de las capas."* -- mismo tono/longitud que los banners existentes.

## Verificación

**Tests de componente** (`CapaErrorBanners.test.jsx`, nuevo, 5 casos): el aviso aparece cuando una capa
está vacía y no fallando; no tiene botón de reintento; no aparece si esa misma capa SÍ está marcada como
fallando (y ahí sigue mostrándose el banner de error real, con su reintento); lista varias capas vacías
juntas en un solo aviso, sin mezclar las que tienen datos; no aparece ningún aviso cuando no hay capas
vacías. 101/101 tests de frontend en verde (96 anteriores + 5 nuevos), eslint limpio.

**Confirmación real en navegador**, con el stack levantado y tu sesión real logueada: se simuló que
`/api/corredores` responde `200` con `[]` (service worker temporal, `frontend/public/_test_sw_v10.js`,
borrado al terminar -- mismo método ya usado en G04 para "cortar una capa" sin tocar el backend real).
Resultado real en pantalla: *"Sin datos registrados todavía en esta zona: corredores. No es un fallo -- el
mapa sigue funcionando con el resto de las capas."*, sin ícono de alerta, sin botón, y el resto de las capas
(hotspots: 195/513/30/2 por nivel) siguió funcionando normal. Captura real:
[`aviso_capa_sin_datos.jpg`](aviso_capa_sin_datos.jpg). Al desregistrar el service worker y recargar, el
aviso desapareció solo, sin dejar rastro.

## Corrección encontrada en la revisión de Claude (antes de commitear este trabajo)

El razonamiento de arriba para excluir `/hotspots` ("una lista vacía ahí sería un bug real, no un
estado legítimo") no es exacto. Leyendo `backend/main.py` línea 623, ese endpoint tiene exactamente el
mismo guard que `/corredores`:

```python
# Una instalación recién creada puede no tener hotspots todavía. Es un
# estado válido de la aplicación, no una entrada válida para sklearn.
if not resultado:
    return []
```

El propio comentario del backend declara el caso vacío como un estado **válido**, exactamente lo que V10
pedía distinguir de un fallo -- lo contrario de lo que afirma este documento. Es cierto que hoy no es un
caso real (la base de producción siempre trae las 740 filas), así que no hay ningún bug activo ni se
fuerza un cambio de código sin que Rodo lo pida. Pero la justificación para dejar `/hotspots` fuera de
`capasVacias` estaba mal fundamentada, y queda así señalado en vez de dejarse pasar.

## Qué no se tocó

Ningún otro ítem del catálogo V (V01-V09, V11-V14) ni F -- como pidió Rodo explícitamente, esos quedan para
que él decida el alcance antes de pedirlos. Tampoco se rediseñó nada más de los banners existentes (fuente,
reintento, formato) más allá de agregar el bloque nuevo.

## Conclusión

El hueco identificado en V10 ("sin mensaje específico para sin datos vs. fallo") queda cerrado: las tres
capas que de verdad pueden devolver una lista vacía legítima (confirmado leyendo el código del backend, no
asumido) ahora muestran un aviso propio, visualmente distinto del de error, verificado con tests de
componente y en pantalla real.
