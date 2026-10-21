# A05 — validación geográfica independiente de "cobertura desconocida" (2026-10-21)

P1. El código ya separaba cobertura por trazado y por fuente, exigía 60% sobre siniestros para la
recomendación de "menor exposición" y mostraba inseguridad aparte -- lo que faltaba era una validación
geográfica real, en pantalla, con el stack real levantado (`npm run dev:http`, backend real, sesión ya
autenticada del navegador pane, sin pedir ni ver contraseña).

## Qué se verificó (código leído antes de probar, para saber qué mirar)

- `calcularCoberturaRegistrada` (`frontend/src/utils/riesgoRuta.js`): muestrea hasta 120 puntos **a lo
  largo del trazado real de la ruta** y para cada uno chequea si hay alguna zona (siniestro o inseguridad)
  a menos de `UMBRAL_CRUCE_KM`. Es genuinamente **por trazado**, no un número agregado único -- cada punto
  del camino cuenta por separado.
- `calcularCoberturaPorFuente`: lo mismo pero separado por fuente (siniestro/inseguridad), nunca mezcladas.
- `App.jsx`: la ruta "más segura" (`idxMasSegura`) solo se elige entre rutas con `coberturaRegistrada >=
  0.6`; si ninguna llega, cae a la más rápida -- sin mostrar nunca una recomendación de seguridad sin
  respaldo.
- `RutaResumenPanel.jsx`: por debajo de 60% muestra literalmente "cobertura registrada insuficiente" (con
  ícono de alerta) en vez de cualquier nivel de riesgo o badge de "menor exposición".

## Caso 1 — ruta íntegramente en GBA profundo, lejos de CABA (cobertura nula esperada)

Origen y destino reales dentro del partido de Moreno (Plaza San Martín → Estación Moreno, ambos geocodificados
por Nominatim en vivo, no inventados): ruta real de TomTom, 1-1.8 km según alternativa.

**Valores reales devueltos** (panel "Ver cómo se calcula", las 3 alternativas):

| Ruta | Distancia | Cobertura siniestros | Cobertura inseguridad | Etiqueta mostrada |
|---|---|---|---|---|
| 1 | 1 km | **0%** | **0%** | "cobertura registrada insuficiente" |
| 2 | 1.2 km | **0%** | **0%** | "cobertura registrada insuficiente" |
| 3 | 1.8 km | **0%** | **0%** | "cobertura registrada insuficiente" |

**Ninguna ruta mostró badge de "menor exposición" ni ningún nivel de riesgo** -- confirma que una zona
genuinamente sin datos se marca como cobertura desconocida, no como "riesgo bajo" disfrazado. Esto es
exactamente el límite ya declarado de D01 (datos históricos de CABA, sin cobertura de GBA) comportándose
como debía en la interfaz real, no solo en el texto de un documento.

## Caso 2 — caso límite: ruta que cruza una zona con datos y otra sin ellos

Origen real con cobertura conocida (Paraguay 1854, CABA -- la misma dirección ya usada en D03) → destino
real lejos, cruzando la frontera CABA/GBA (Estación Don Torcuato, Tigre). Ruta real de 32,4 a 41,3 km según
alternativa (atraviesa buena parte de CABA y después varios partidos del norte del GBA).

**Valores reales devueltos:**

| Ruta | Distancia | Cobertura siniestros | Cobertura inseguridad | Etiqueta mostrada |
|---|---|---|---|---|
| 1 | 32.4 km | **57%** | **45%** | "cobertura registrada insuficiente" |
| 2 | 37.1 km | **57%** | **38%** | "cobertura registrada insuficiente" |
| 3 | 41.3 km | **47%** | **45%** | "cobertura registrada insuficiente" |

Captura real de pantalla: [`caso2_limite_caba_gba.jpg`](caso2_limite_caba_gba.jpg) (ruta trazada sobre CABA
y norte del GBA, panel de cobertura visible).

**Esto confirma lo que pedía el caso límite**: el número no se diluye hacia un extremo por mezclar el
tramo con datos (CABA) con el tramo sin ellos (GBA) -- sale un valor intermedio real (45-57%, no 95% ni
5%), coherente con que aproximadamente la mitad del trayecto cae dentro del área con datos y la otra mitad
fuera. Por estar bajo el 60%, sigue mostrando "cobertura registrada insuficiente" -- el sistema no
recomienda esta ruta como "más segura" pese a que una parte real sí tiene datos, exactamente el
comportamiento que A05 pedía confirmar (no inflar la confianza por el tramo que sí está cubierto).

## Conclusión

Los dos casos reales (cobertura nula en una zona genuinamente sin datos, y cobertura parcial real en una
ruta que cruza la frontera CABA/GBA) confirman en pantalla, con valores reales devueltos por la app, que
"sin datos" no se disfraza de "riesgo bajo" y que el cálculo de cobertura por trazado refleja de verdad el
tramo sin datos en vez de diluirlo con el tramo que sí los tiene. No se encontró ningún caso en el que la
interfaz mostrara una recomendación de seguridad sin respaldo de datos reales.
