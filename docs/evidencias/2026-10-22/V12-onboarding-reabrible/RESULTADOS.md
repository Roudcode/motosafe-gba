# V12 — onboarding breve y ayuda reabrible (2026-10-22, SES-162)

Criterio de cierre: "Explica cobertura y colores sin cifras rígidas; usuario puede volver a leerlo."
Depende de A01/A05 (ya validados). `Onboarding.jsx` (A23 ya le encontró y corrigió un bug real de trampa de
foco -- no se tocó esa parte).

## Qué había antes (revisado en el código real)

- **Hallazgo real 1 ("reabrible")**: `mostrarOnboarding` solo se inicializaba leyendo localStorage (primera
  visita) y solo se ponía en `false` al cerrar -- ningún botón en toda la app volvía a ponerlo en `true`.
  Una vez cerrado (la primera vez o cualquier sesión posterior), no había forma de volver a verlo.
- **Hallazgo real 2 ("sin cifras rígidas")**: el texto decía "entrenado con 23.343 casos reales" -- un
  número fijo del tamaño de entrenamiento de un momento dado. Comparado contra el dato real de hoy (citado
  en la tesis, `docs/tesis/MotoSafe_GBA_Capitulos_1_a_6.docx`, sección 4.4: "23.338 registros de siniestros
  con motocicleta"): **ya estaba desactualizado**, por una diferencia chica pero real -- exactamente el
  problema que el criterio de cierre anticipaba al pedir evitar cifras rígidas acá.

## Qué se cambió

1. **Reabrible**: nuevo botón "Cómo funciona" en el menú de herramientas (`HerramientasMenu.jsx`, mismo
   lugar que "Estadísticas"/"Cerrar sesión"), que llama `setMostrarOnboarding(true)` -- reusa el mismo
   componente y el mismo cierre (`cerrarOnboarding`) que ya existían, sin estado nuevo que mantener aparte
   del que ya había.
2. **Sin cifra rígida**: "23.343 casos reales" → "miles de casos reales". Describe el método sin un número
   que haya que actualizar a mano cada vez que se reentrena el modelo (A19/A22 ya documentan que eso pasa
   con cierta frecuencia).

## Qué no se tocó

La trampa de foco y el manejo de teclado del modal (A23, SES-112) -- no se tocó nada de `useEffect` ni de
los refs. El resto del contenido del onboarding (explicación de "cobertura" y "colores" vía el párrafo
existente) ya era cualitativo, sin cifras -- solo la frase del tamaño de entrenamiento tenía el problema.

## Verificación

- `eslint src/`: limpio.
- `vitest run`: 108/108 (sin tests nuevos -- no hay test de componente de `Onboarding`/`HerramientasMenu`
  hoy).
- `vite build`: compila sin errores.
## Actualización 2026-10-22 (SES-163) — confirmado real

Con sesión real: menú de herramientas → "Cómo funciona" reabrió el modal real, con el texto actualizado
("miles de casos reales", sin la cifra vieja) y el foco inicial correctamente en "Entendido"
(`document.activeElement.className === 'onboarding-entendido'`) -- la trampa de foco de A23 sigue intacta al
reabrir. Captura real en [`onboarding_reabierto.jpg`](onboarding_reabierto.jpg). Cerrado con "Entendido" sin
problemas.
