# DEC-026 (caso 2 de D03) — aviso cuando la recomendación depende de una fuente con cobertura parcial (2026-10-22, SES-157)

Ejecución directa de una decisión ya tomada (DEC-026 en `docs/gestion/DECISIONES.md`, Rodo delegó el
criterio explícitamente: "usa tu criterio"). Solo se toca el caso 2 (cobertura de inseguridad baja en la
ruta recomendada) -- el caso 4 (el score no pesa magnitud) queda **explícitamente sin tocar**, según la
propia DEC-026: es una decisión de diseño del algoritmo de scoring, no una corrección de UI, y no se cambia
sin que Rodo lo pida aparte.

## El problema real (caso 2 de D03)

`docs/evidencias/2026-09-13/D03/rutas_referencia.csv`, fila `id=2`: destino fuera de CABA (Vicente López,
GBA), a propósito, para un tramo donde el dataset de siniestros (GCBA, 2019-2025) no tiene cobertura
completa. De las 3 alternativas reales, el sistema recomienda como "menor exposición" la ruta con
cobertura de **siniestros 86%** pero cobertura de **inseguridad apenas 56%** -- una brecha de 30 puntos
porcentuales entre las dos fuentes que hoy no tiene ningún aviso. El riesgo real: esa ruta puede parecer
más segura simplemente porque falta dato de inseguridad en ese tramo, no porque sea un trazado más seguro
de verdad.

## Qué se implementó

- **`frontend/src/utils/riesgoRuta.js`**: nueva función pura `brechaCoberturaEnRecomendada(rutasConScore,
  idxRecomendada)`. Compara `coberturaPorFuente.siniestro` vs `.inseguridad` de la ruta recomendada; si
  alguna de las dos es `null` (fuente sin ningún dato, caso ya cubierto aparte) no dispara nada; si la
  brecha entre ambas es `>= UMBRAL_BRECHA_COBERTURA_FUENTES` (fijado en **0,20**, 20 puntos porcentuales)
  devuelve `{ fuenteMenor, coberturaMenor, coberturaMayor }`; si no, devuelve `null`.
- **Umbral elegido con los 4 casos reales de D03** (no arbitrario): la ruta recomendada de cada caso tiene
  una brecha real entre fuentes de 11pp (caso 1), **30pp (caso 2)**, 0pp (caso 3) y 1pp (caso 4). Un umbral
  de 20pp separa limpio el único caso que amerita el aviso (30pp) de los otros tres (≤11pp), sin necesitar
  ajustar nada caso por caso.
- **`frontend/src/App.jsx`**: `useMemo` nuevo (`brechaCoberturaRecomendada`) que llama a la función de
  arriba con `rutasConScore`/`idxMasSegura` (el mismo índice que ya usa el badge "Menor exposición"),
  pasado como prop nueva a `RutaResumenPanel`.
- **`frontend/src/components/RutaResumenPanel.jsx`**: un párrafo nuevo, condicional, inmediatamente debajo
  del aviso general de cobertura que ya existía (misma clase base `ruta-cobertura-aviso`, mismo patrón
  visual de la app -- no se inventó un componente nuevo). Texto real: "La recomendación de menor exposición
  se apoya en datos de cobertura parcial de {fuente} ({cobertura_menor}%, contra {cobertura_mayor}% de la
  otra fuente) -- puede haber zonas sin ese dato que no se están viendo." Con ícono `TriangleAlert` (el
  mismo que ya usan los demás avisos de nivel advertencia en este mismo panel) y color
  `var(--amarillo-text)` (ya definido en el tema, reusado, no un color nuevo).
- **`frontend/src/App.css`**: dos reglas nuevas (`.ruta-cobertura-aviso-brecha` y su `svg`), que solo
  agregan color/alineación sobre la clase base ya existente -- no duplican estilos.

## Probado contra los 4 casos reales de D03

`frontend/src/utils/riesgoRuta.test.js`, bloque `brechaCoberturaEnRecomendada (DEC-026, D03 caso 2)`: cada
test reproduce la cobertura real documentada de la ruta recomendada de cada caso (vía
`calcularRutasConScore` con `coberturaPorFuente` real, no inventada) y confirma:

| Caso | Cobertura de la ruta recomendada | Brecha | Resultado esperado |
|---|---|---|---|
| 1 (desvío) | siniestros 100% / inseguridad 89% | 11pp | sin aviso |
| **2 (cobertura parcial)** | **siniestros 86% / inseguridad 56%** | **30pp** | **dispara el aviso** (`fuenteMenor: 'inseguridad'`) |
| 3 (empate) | 100% / 100% | 0pp | sin aviso |
| 4 (discordancia de fuentes) | siniestros 100% / inseguridad 99% | 1pp | sin aviso |

Más dos tests de borde: no dispara si a alguna fuente le falta directamente el dato (`null`, caso distinto
de cobertura baja), y confirma que identifica correctamente cuál de las dos fuentes es la de menor
cobertura cuando es `siniestro` en vez de `inseguridad` (no quedó hardcodeado a un solo sentido).

## Por qué no se verificó en pantalla con el stack real

Se levantó el stack real (frontend `npm run dev` + backend ya corriendo, `/health` real confirmado) con la
intención de reproducir el caso 2 real (mismas direcciones: Paraguay 1854 → Avenida Maipú 1300, Vicente
López) en el navegador. La app requiere sesión logueada (`AUTH_USERNAME`/`AUTH_PASSWORD_HASH` en
`backend/.env`, por diseño del script `generar_password.py` **la contraseña en texto plano no queda
guardada en ningún lado** -- ni en el repo ni en ningún archivo que este agente pueda leer) y no se cuenta
con esa credencial real para iniciar sesión. No se intentó adivinarla ni se tocó el mecanismo de auth. Esto
es la misma limitación ya documentada en otras entradas del backlog cuando no hay acceso al stack completo
logueado (ej. A17: "sin verificación visual en navegador en vivo (requiere backend + PostgreSQL + auth)").
La verificación real para este caso queda en los tests unitarios contra los datos reales de D03 (arriba),
que prueban exactamente la lógica nueva con los números reales del caso que motivó el pedido.

## Verificación

- `node node_modules/vitest/vitest.mjs run` (desde `frontend/`): **108/108** en verde (102 antes + 6 de
  `brechaCoberturaEnRecomendada` + 1 de DEC-025, ver su propia evidencia).
- Lint (`eslint src/`): limpio.
- Build (`vite build`): compila sin errores, 1853 módulos transformados.

## Qué no se tocó (a propósito)

El caso 4 de D03 (el score combinado no pesa magnitud, solo cercanía/nivel) queda documentado como
limitación conocida en `DECISIONES.md`, sin tocar `calcularRutasConScore` ni el algoritmo de scoring --
es una decisión de diseño que afecta a todos los usuarios, no una corrección de UI acotada, y DEC-026 es
explícita en que eso no se toca sin que Rodo lo pida aparte.
