# Defensa MotoSafe GBA

## Versión Motion — 25/10/2026

Rodo pidió acercar el estilo a las dos referencias de YouTube y confirmó **ambos formatos**. Los nuevos entregables son:

- `MotoSafe_GBA_Motion.html`: recorrido autónomo de 12 escenas, 84 segundos. Se puede reproducir automáticamente o controlar escena por escena. Las cinco capturas originales están incrustadas; la vista móvil se repite en la apertura y en su escena específica.
- `MotoSafe_GBA_Motion.mp4`: versión de video a 1920 × 1080, 24 fps, con base instrumental original sintetizada localmente. Sin locución. El audio es parte del MP4; el HTML permanece sin audio.

Las referencias orientan el lenguaje visual: dispositivos inclinados, desplazamientos y acercamientos de las capturas, tipografía grande, textos breves y alternancia de composición. No se reutilizaron videos, música o recursos descargados de los autores. Las pantallas son capturas animadas, no una grabación nueva de uso real de la app.

Controles del HTML Motion: **Espacio** reproduce/pausa, **flechas** cambian de escena, **F** alterna pantalla completa, **G** abre índice, **N** abre notas, **R** vuelve al inicio. La barra inferior permite buscar un instante. La reproducción comienza pausada para que el expositor decida cuándo iniciar. Las notas y el índice pausan el recorrido.

Se conservó la defensa académica de 21 diapositivas de la sección siguiente. La versión corta muestra el producto y sus límites, y no pretende cubrir toda la defensa metodológica o económica.

Para regenerar, desde la raíz del repositorio:

```powershell
node docs/tesis/para_ppt/generar_motion.cjs
python docs/tesis/para_ppt/generar_video.py
```

El video requiere Pillow, numpy e imageio-ffmpeg. En esta sesión se usó el Python empaquetado de Codex y se instaló imageio-ffmpeg únicamente en `%TEMP%/motosafe-motion-runtime`, sin cambiar dependencias de la aplicación. `motion_scenes.json` contiene el guion compartido por ambos formatos. Los encuadres y efectos de composición son propios de cada medio, por lo que el video no es una captura de reproducción del HTML.

Las verificaciones y sus límites se registran en BITACORA, SES-185. El bloqueo previo de apertura de archivos `file:` no se eludió para revisar el HTML.

## Versión académica — 23/10/2026

Abrir `MotoSafe_GBA_Defensa.html` con un navegador de escritorio. Es un archivo autónomo: incluye las cinco capturas y no necesita conexión para mostrar la presentación. El enlace final a la aplicación y la fuente ANSV sí requieren conexión.

## Controles

- Flechas izquierda/derecha, Page Up/Page Down o espacio: navegar.
- F: pantalla completa.
- G: índice de las 21 diapositivas.
- N: notas del expositor y referencia de la diapositiva actual. Cerrar antes de seguir la defensa.
- B: pantalla negra, cualquier tecla la desactiva.
- Inicio/Fin: primera/última diapositiva.
- Clic en una captura: ampliarla. Escape: cerrar captura, notas o índice.
- ?: mostrar u ocultar ayuda.

En dispositivos táctiles también se puede deslizar horizontalmente. La composición está diseñada para exposición en pantalla horizontal 16:9. Respeta la preferencia del sistema de reducir movimiento.

## Edición

El HTML contiene texto, estilos y navegación editables. Para regenerarlo desde la raíz del repositorio:

```powershell
node docs/tesis/para_ppt/generar_presentacion.cjs
```

El generador usa las cinco imágenes JPG de esta carpeta. No modifica el prompt, las capturas originales ni la tesis. La presentación aplica la actualización HTML del prompt como referencia de formato. No incorpora un mapa interactivo real ni simula que las capturas sean una aplicación en funcionamiento. El último enlace permite abrir la aplicación pública para una demo separada.

## Alcance de cifras y fuentes

Preparada el 23/10/2026 bajo G01/SES-184. Las cifras del modelo publicadas en la tesis se distinguen de las reconstrucciones de SES-171/173. La evaluación temporal se describe como retrospectiva y con límites de independencia. La cobertura de rutas se explica como muestreo de puntos. Los conteos 168/108 corresponden al corte de auditoría SES-171. El escenario económico se presenta como condicional, con sensibilidad a ingresos y funciones Premium propuestas. Las notas identifican referencias y límites por diapositiva.

El 46% corresponde al informe preliminar ANSV de siniestralidad fatal 2024, edición marzo de 2025, enlazado en la segunda diapositiva. No se presenta como cifra actual de 2026.

## Comprobaciones ejecutadas y límites

- Generación con Node: archivo HTML de 498.982 bytes, 21 diapositivas y 5 imágenes JPEG incrustadas.
- Sintaxis del JavaScript incrustado comprobada con `vm.Script` de Node, sin errores.
- Recuento estructural: 21 secciones, 5 imágenes incrustadas, 0 scripts externos.
- No se ejecutaron suites de la app: este trabajo solo crea material de defensa.
- La inspección visual y las interacciones en navegador quedan pendientes. El navegador integrado rechazó el protocolo `file:` por política de seguridad. No se intentó eludir ese bloqueo. Tampoco se verificaron impresión/PDF, pantalla completa o hardware móvil real.

No hubo commit, push, publicación, cambio de modelo ni acceso a cuentas de producción.
