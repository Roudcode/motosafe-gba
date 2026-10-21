# V11 — contraste real sobre mapas claros (2026-10-21, SES-154)

**Alcance confirmado antes de empezar**: la app solo tiene dos estilos de mapa (`frontend/src/components/
MapaMotoSafe.jsx`): `light` (OpenFreeMap "liberty") y `dark` (OpenFreeMap "dark"). **No existe un estilo
satelital** -- queda esta tarea acotada al modo claro solamente, como anticipaba el pedido. No se tocó la
paleta de riesgo en sí (verde/amarillo/naranja/rojo de siniestros, violeta/magenta de inseguridad) -- eso es
V04, explícitamente fuera de esta tarea.

## Método: medido, no a ojo

1. **Fondo real**: capturada una pantalla real de la app (navegador real, tema claro, "Vista de fondo:
   Apagada" para ver el mapa base sin ninguna capa de datos encima) y muestreados con PIL tres pixeles
   reales en zonas representativas del estilo real (no inventados): un área de parque/verde
   `(226,211,156)`, un área de uso general `(245,233,221)` y una zona con tinte distinto (agua/landuse)
   `(235,230,234)`.
2. **Colores reales de los elementos**: tomados directo de `frontend/src/constants.js` (`NIVELES`,
   `NIVELES_INSEGURIDAD_COLOR`) y de los `line-color`/colores hardcodeados reales en `MapaMotoSafe.jsx`
   (ruta seleccionada, borde de ruta).
3. **Contraste WCAG 2.1** calculado con la fórmula real de luminancia relativa (no una librería de terceros,
   la misma fórmula que usan las herramientas de devtools), script completo y reproducible en
   [`medir_contraste.py`](medir_contraste.py), salida real en [`salida_contraste.txt`](salida_contraste.txt).

## Resultado real: antes de tocar nada

| Elemento | tan/parque | crema | lavanda |
|---|---|---|---|
| Ruta seleccionada `#4FA8E8` | 1.73 **FALLA** | 2.17 **FALLA** | 2.10 **FALLA** |
| Ruta, borde `#0B1620` (ya existía) | 12.20 ok | 15.29 ok | 14.82 ok |
| Siniestros bajo `#3DDC84` | 1.19 **FALLA** | 1.49 **FALLA** | 1.45 **FALLA** |
| Siniestros medio `#FFD23F` | 1.04 **FALLA** | 1.21 **FALLA** | 1.17 **FALLA** |
| Siniestros alto `#FF8C42` | 1.54 **FALLA** | 1.94 **FALLA** | 1.88 **FALLA** |
| Siniestros crítico `#FF3B3B` | 2.36 **FALLA** | 2.96 **FALLA** | 2.87 **FALLA** |
| Inseguridad bajo `#D9A6FF` | 1.29 **FALLA** | 1.62 **FALLA** | 1.57 **FALLA** |
| Inseguridad medio `#B266FF` | 2.25 **FALLA** | 2.82 **FALLA** | 2.73 **FALLA** |
| Inseguridad alto `#9B30FF` | 3.29 ok | 4.13 ok | 4.00 ok |
| Inseguridad crítico `#FF2E92` | 2.32 **FALLA** | 2.90 **FALLA** | 2.81 **FALLA** |

**Hallazgo real**: casi todos los colores de nivel de riesgo (siniestros e inseguridad) dan entre 1.0 y
3.0:1 contra el mapa claro real -- por debajo del mínimo de 3:1 (AA, elementos gráficos no textuales). Solo
"inseguridad alto" (un violeta oscuro) y la **ruta seleccionada ya pasan**, pero la ruta pasa únicamente
gracias a su contorno oscuro (`#0B1620`) que ya existía -- el color de relleno solo (`#4FA8E8`) también
falla (1.7-2.2:1). Esa técnica de contorno, ya usada para la ruta, es la que se extendió a los demás
elementos.

## Ajuste propuesto y aplicado: mismo contorno oscuro que ya usa la ruta

**No se tocó ningún color de la paleta de riesgo.** Se replicó el contorno (`#0B1620`, el mismo color
oscuro que ya usa el borde de la ruta) en los dos lugares que todavía no lo tenían:

- **Hexágonos de cobertura** (`MapaMotoSafe.jsx`): el borde ya existía pero era blanco semitransparente
  (`rgba(255,255,255,0.35)`) -- apropiado para tema oscuro, casi invisible contra un fondo claro (por eso
  no mejoraba nada el contraste real). Ahora es theme-aware: oscuro `rgba(11,22,32,0.55)` en tema claro,
  blanco sin cambios en tema oscuro.
- **Corredores de riesgo** (`MapaMotoSafe.jsx`): no tenían ningún contorno. Se agregó una capa "casing"
  debajo de la línea de color, mismo patrón ya usado para la ruta seleccionada -- solo en tema claro (en
  tema oscuro el mismo color ya contrasta bien contra el fondo navy, no hacía falta).

**Corregido durante la propia medición**: la primera versión de la línea de casing de corredores escalaba
su opacidad igual que la línea de color por nivel (0,35 "bajo" a 0,9 "crítico"), lo que dejaba el contorno
de los corredores de nivel bajo/medio todavía por debajo de 3:1 (1.8-2.8:1, medido). Corregido a una
opacidad **fija** (0,7, no escalada por nivel) -- el contorno tiene que verse igual de bien sin importar el
nivel de riesgo, es la línea de color la que ya distingue bajo de crítico, no el contorno.

## Resultado real: después del ajuste

| Elemento | tan/parque | crema | lavanda |
|---|---|---|---|
| Borde de hexágono (0.55 opacidad) | 3.61 ok | 3.87 ok | 3.81 ok |
| Borde de corredor (0.7 opacidad fija) | 5.59 ok | 6.29 ok | 6.20 ok |

Los dos contornos quedan cómodamente por encima del mínimo de 3:1 en las tres zonas reales muestreadas.

## Verificación en pantalla real

Con el stack real levantado, tema claro, sesión real logueada:

- **Hexágonos**: capturada una pantalla real con la capa de hexágonos activa; muestreados los píxeles de la
  captura con PIL -- confirmados múltiples píxeles oscuros (compatibles con el nuevo borde) en los bordes
  de celda, donde antes no había ninguno. Captura:
  [`hexagonos_con_borde_oscuro.jpg`](hexagonos_con_borde_oscuro.jpg).
- **Corredores**: capturada una pantalla real con la capa de corredores activa -- las calles con score de
  riesgo muestran un contorno visible, distinto de antes. Captura:
  [`corredores_con_borde.jpg`](corredores_con_borde.jpg).
- Sin errores de consola al activar ninguna de las dos capas (verificado en una pestaña nueva del
  navegador, sin estado de recarga en caliente de por medio -- ver nota abajo).

**Nota honesta sobre un falso positivo durante la verificación**: mientras se editaba el archivo con el
servidor de desarrollo corriendo, apareció un warning real de React ("The final argument passed to %s
changed size between renders") en la pestaña que ya estaba abierta -- se investigó a fondo (se descartó
que fuera un problema real de los dos efectos editados, cuyos arrays de dependencias son de longitud fija
en el código fuente) y se confirmó, abriendo una pestaña completamente nueva y reiniciando el servidor de
desarrollo, que el warning **no aparece en una carga real limpia** -- era un artefacto de Hot Module
Replacement de Vite/React Fast Refresh durante la edición en vivo, no un bug del código final.

96/96 → **101/101** tests de frontend en verde (sin tests nuevos específicos de V11 -- cambios de capas
GL/CSS puros, verificados con medición real y en pantalla). Eslint limpio.

## Qué no se tocó

Ningún color de la paleta de riesgo (V04). Ningún otro ítem del catálogo V. No se midió el modo oscuro (no
estaba en duda, el pedido lo acotaba a "mapas claros y satelitales" y el satelital no existe).
