# MotoSafe GBA — Guía Completa del Proyecto (explicada desde cero)

## Cómo leer este documento

Este documento asume que no sabés nada de programación, ni de bases de datos, ni de Inteligencia Artificial. Cada vez que aparece un concepto técnico, se explica antes de usarlo. Si en algún momento sentís que "ya sabés esto", podés saltar el bloque — está marcado con un título claro para que puedas ubicarte.

La idea es que, al terminar de leer, entiendas: qué construiste, por qué cada pieza existe, cómo se conectan entre sí, y qué es real versus qué es una simplificación temporal.

---

## Parte 1 — El proyecto, explicado sin tecnicismos

### ¿Qué es MotoSafe GBA?

Es una aplicación (un programa que corre en una página web) pensada para motociclistas del Gran Buenos Aires. Muestra un mapa donde algunas zonas están pintadas de verde, amarillo, naranja o rojo, según qué tan riesgoso es circular por ahí en moto. Ese color no está puesto "a ojo" — sale de un cálculo hecho por una Inteligencia Artificial que aprendió, mirando miles de siniestros reales que ya ocurrieron, a predecir qué tan grave suele ser un accidente en cada tipo de situación.

Además del mapa de riesgo, la aplicación permite:
- Trazar una ruta entre dos puntos (como Google Maps), y te dice si esa ruta pasa por zonas peligrosas.
- Reportar un problema en la vía (un pozo, falta de luz, etc.) desde tu celular.
- Ver el clima actual, porque llover aumenta el riesgo.
- Activar un "Modo Viaje" que te avisa en tiempo real si te estás acercando a una zona peligrosa mientras andás.

### ¿Por qué existe este proyecto?

Es tu trabajo final de la carrera de Ingeniería en Informática. La idea original (documentada en los primeros capítulos de tu tesis) era construir algo que combine tres fuentes de información — el historial de siniestros, el clima del momento, y reportes de otros motociclistas — para calcular un "riesgo dinámico" que ninguna app de navegación existente (ni Waze, ni Google Maps) calcula específicamente para motos.

---

## Parte 2 — Conceptos básicos que necesitás para entender el resto

Si alguno de estos términos ya te resulta familiar, salteálo. Están acá para quien no tenga ningún contacto previo con programación.

### ¿Qué es "código" o "programar"?

Programar es escribir instrucciones, en un idioma muy estricto y preciso (un "lenguaje de programación"), que una computadora puede ejecutar paso a paso. A diferencia de hablarle a una persona, la computadora no interpreta ni adivina — si la instrucción tiene un error de sintaxis (una coma de más, una palabra mal escrita), directamente no funciona.

### ¿Qué es una "terminal" o "consola"?

Es una ventana negra (o de otro color) donde en vez de hacer clic en botones, escribís comandos de texto para darle órdenes a la computadora. Es más rápida y potente que usar el mouse para tareas técnicas, pero exige escribir exactamente bien — un espacio de más, o estar "parado" en la carpeta equivocada, hace que el comando falle.

### ¿Qué es un "servidor"?

Un servidor es, en esencia, un programa que queda "escuchando" pedidos y respondiendo con información. Pensalo como un mozo de restaurante: se queda esperando, y cuando alguien le pide algo, va, lo busca, y lo trae. En este proyecto tenés dos servidores corriendo en tu propia computadora (no en internet, todavía): uno que sirve la parte visual (lo que ves en el navegador) y otro que sirve los datos (los puntos del mapa, las predicciones).

### ¿Qué es una "base de datos"?

Es un sistema organizado para guardar información de forma que se pueda buscar y consultar rápido, como una biblioteca con fichas ordenadas en vez de libros tirados en el piso. En este proyecto, la base de datos guarda los 740 puntos de riesgo del mapa (ubicación, cantidad de siniestros históricos, etc.).

### ¿Qué es una "API"?

API es la forma en que dos programas se hablan entre sí. Si el servidor es el mozo, la API es el menú: una lista fija de "cosas que podés pedir" y en qué formato. En este proyecto, el navegador (frontend) le pide cosas al servidor de datos (backend) usando su API — por ejemplo, "dame la lista de zonas de riesgo" es un pedido a la API.

### ¿Qué es "Machine Learning" (Aprendizaje Automático)?

Es una rama de la Inteligencia Artificial donde, en vez de escribirle a la computadora una regla fija ("si llueve, sube el riesgo un nivel"), le mostrás miles de ejemplos reales del pasado y dejás que ella misma descubra los patrones. Por ejemplo: le mostrás 23.343 siniestros reales de motociclistas, con toda la información que se tiene de cada uno (hora, día, tipo de calle, con qué chocó, edad del motociclista, y qué tan grave terminó siendo), y el algoritmo "aprende" solo qué combinaciones de esos factores suelen terminar en accidentes graves.

### ¿Qué es "entrenar un modelo"?

Es el proceso de mostrarle al algoritmo esos miles de ejemplos reales para que aprenda el patrón. El resultado de ese entrenamiento es un archivo (en este proyecto, `modelo_final.pkl`) que contiene ese "conocimiento aprendido", listo para usarse en predicciones nuevas.

### ¿Qué es "predecir"?

Una vez entrenado, el modelo puede recibir una situación **nueva** (que nunca vio en los datos de entrenamiento) y estimar qué tan probable es que termine siendo leve, grave o mortal. Por ejemplo: "es viernes a las 22hs, en una avenida, chocó con un auto, el motociclista tiene 25 años" — el modelo devuelve una probabilidad para cada resultado posible.

---

## Parte 3 — La historia completa del proyecto, en orden

### Fase 1 — Preparar la computadora (desde cero, PC recién formateada)

Se instaló todo el software necesario: un programa para manejar bases de datos (Docker + PostgreSQL), el lenguaje de programación Python, el entorno para construir la parte visual (Node.js), un editor de código (VS Code), y un programa para inspeccionar bases de datos visualmente (DBeaver).

### Fase 2 — Construir la interfaz visual (el "frontend")

Se armó el mapa interactivo que ves en el navegador: primero con datos de ejemplo inventados (para poder mostrar cómo se vería la aplicación terminada), y con todas las funciones (búsqueda, filtros, rutas, reportes, clima) construidas sobre esa base temporal.

### Fase 3 — Conseguir y limpiar los datos reales

Se descargaron los datos oficiales del gobierno de la Ciudad de Buenos Aires: un registro de 65.818 siniestros viales ocurridos entre 2019 y 2025, con su ubicación exacta, y otro registro de las 75.197 víctimas de esos siniestros (una persona puede estar involucrada sin que sea "su" siniestro si hubo más de un afectado).

Estos datos, tal como los entrega el gobierno, tienen errores típicos de cualquier base real: texto con mayúsculas y minúsculas mezcladas para la misma categoría (por ejemplo, "MOTO" y "moto" contados como cosas distintas), un error de exportación de Excel que dejó basura en una fila, y edades de víctimas fuera de rango humano posible (0 años, 116 años). Todo esto se identificó y se corrigió.

### Fase 4 — Encontrar los puntos de riesgo real (clustering)

Con los 23.343 siniestros de motociclistas ya limpios, se usó un algoritmo llamado DBSCAN para encontrar **agrupaciones geográficas reales** — es decir, esquinas o tramos de avenida donde los siniestros no son casualidad aislada, sino que se repiten una y otra vez en el mismo lugar. El primer intento agrupó "demasiado" (toda la ciudad en un solo grupo gigante, por un error de calibración), pero ajustando los parámetros se llegó a zonas de riesgo reales y bien definidas.

Esta calibración se revisó más adelante con un barrido sistemático (probando 60 combinaciones de radio y cantidad mínima de siniestros por zona) en vez de quedarse con el primer ajuste manual que funcionó. El resultado: con radio de 100 metros y mínimo 12 siniestros por zona, la cobertura subió de 32.1% a 49.9% de los siniestros históricos, sin volver a caer en el problema de fusionar toda la ciudad en un cluster gigante — pero seguía quedando más de la mitad de los siniestros sin zona.

Después de esa primera vuelta se probó un algoritmo distinto, HDBSCAN, que en vez de usar un único radio fijo para toda la ciudad se adapta a la densidad local de cada zona (una esquina con siniestros muy pegados entre sí y un tramo de avenida con siniestros más dispersos pueden formar zonas igual de válidas, cada una con su propia "escala"). Se evaluó igual que DBSCAN, chequeando en cada combinación de parámetros el tamaño del cluster más grande como porcentaje del total (para descartar el mismo riesgo de "blob" que motivó la calibración anterior). Con `min_cluster_size=12` (mismo piso de siniestros reales por zona que antes, ahora garantizado de forma nativa por el algoritmo, sin post-proceso) y `min_samples=3`, se llegó a **740 zonas de riesgo, con una cobertura del 75.6%** de los siniestros históricos, y con el cluster más grande ocupando apenas 0.41% del total (más chico incluso que el 0.73% de la versión con DBSCAN). Es la configuración final: mejor cobertura y, según esta misma medida de seguridad, más conservadora que la anterior.

### Fase 5 — Entrenar el modelo predictivo

Con esos datos reales, se entrenaron y compararon **cuatro versiones distintas** de modelos de Machine Learning, probando dos algoritmos distintos (Random Forest y XGBoost) y dos conjuntos de información distinta (solo contexto del lugar, versus contexto más datos de la víctima como edad y sexo). Se midió cuál predecía mejor los casos graves y mortales — que son los que menos casos tienen mientras que los leves son en su mayoría los que hay en la base de datos, así que hacía falta usar formas específicas de medir esto (no simplemente "cuántas veces acertó en total", que hubiera sido engañoso).

El mejor resultado fue el Random Forest que incluye edad y sexo de la víctima — se guardó como el modelo definitivo.

### Fase 6 — Conectar todo: el mapa ahora usa el modelo real

Finalmente, se conectó el modelo entrenado al servidor de datos, de forma que cada vez que el mapa pide "dame las zonas de riesgo", el servidor le pregunta al modelo real —en el momento, con la hora y el día actuales— qué probabilidad de gravedad tiene cada una de las 740 zonas, y pinta el mapa con ese resultado. Ya no es un color fijo inventado: es la salida en vivo de una Inteligencia Artificial entrenada con datos reales.

### Fase 7 — Corredores de riesgo (avenidas completas, no solo puntos)

Los 740 hotspots son puntos aislados, pero el riesgo real de una avenida no se vive punto por punto: se vive como un tramo completo. Se agregó una segunda forma de ver el mapa donde, en vez de círculos sueltos, avenidas enteras (9 de Julio, Rivadavia, Corrientes, etc.) se pintan de punta a punta según un score de riesgo calculado sobre todos los siniestros que caen dentro de un radio de esa avenida. Esto se sirve desde un endpoint nuevo del backend (`/corredores`) y se puede alternar en el mapa junto con la vista de clusters y el mapa de calor.

### Fase 8 — Reportes colaborativos reales (dejaron de vivir solo en tu navegador)

Los reportes que un usuario manda desde la app (un pozo, falta de luz, un corte) dejaron de guardarse solo en la memoria del navegador de quien los carga: ahora se guardan en la base de datos del backend (`POST /reportes`), así que cualquiera que abra la app los ve, no solo quien los reportó. Cada reporte tiene una categoría con una vigencia distinta según qué tan rápido deja de ser útil esa información (un corte de calle vence en 12 horas, un problema de iluminación o pavimento tarda 30 días en vencer) — pasado ese tiempo, el reporte se descarta solo. Mientras un reporte está vigente, se muestra cada vez más transparente a medida que envejece, así se distingue de un vistazo un reporte fresco de uno que ya casi vence.

### Fase 9 — El eje de inseguridad: un segundo tipo de riesgo, aparte del siniestro vial

Hasta acá todo el riesgo calculado era de siniestralidad vial (choques, caídas). Pero para un motociclista real, la inseguridad (robos, arrebatos) es un riesgo igual de concreto y de naturaleza distinta. Se incorporó un dataset público de delitos de la Ciudad de Buenos Aires (1.387.622 delitos registrados), del cual se aplicó el mismo proceso de clustering que se usó originalmente para los siniestros, pero recalibrado — porque los delitos se concentran de forma distinta en el mapa que los choques, y usar los mismos parámetros hubiera generado hotspots mal formados. De ese proceso salieron 805 hotspots de inseguridad: 303 de delito general (DBSCAN) y 502 de robos con moto (HDBSCAN, después de una segunda vuelta de calibración — ver la nota más abajo), guardados como dos capas independientes (no una es subconjunto filtrado de la otra en la interfaz, aunque en los datos sí lo sea, porque un usuario puede querer ver un panorama general o específicamente el patrón de robos a motociclistas, y mezclar ambos en el mapa solo duplicaría puntos sobre los mismos hechos).

Además, se armó un índice de inseguridad por comuna, pensado como una capa de contexto adicional (a diferencia de los hotspots, que son puntuales y salen de clustering, el índice es una foto por comuna completa, calculada una sola vez y actualizada manualmente cuando el dataset de delitos se refresca, no en vivo como las predicciones del modelo de siniestros).

### Fase 10 — Integrar inseguridad a lo que ya importaba: rutas y alertas en viaje

Tener el dato de inseguridad en el mapa no alcanzaba si el cálculo de ruta y las alertas en tiempo real lo seguían ignorando. Se unificó el modelo de riesgo: cada zona (sea de siniestro o de inseguridad) ya usa la misma escala ordinal de severidad (bajo/medio/alto/crítico, calculada por percentiles dentro de su propio dataset), así que sumar sus pesos para armar un score total de ruta es matemáticamente razonable — sumar cantidades crudas de siniestros y delitos no lo hubiera sido, porque son magnitudes de naturaleza distinta.

Con esa base, cada opción de ruta ahora muestra un score total, pero siempre desglosado: cuántas zonas de siniestro cruza y cuántas de inseguridad, por separado, además del nivel más grave que atraviesa. Fusionar todo en un solo número sin mostrar el desglose hubiera ocultado información importante para la decisión del usuario (no es lo mismo una ruta con mucho riesgo de choque que una con mucho riesgo de robo). Las alertas en viaje también se diferenciaron: si te acercás a una zona de siniestro suena una alerta de riesgo vial, si te acercás a una zona de inseguridad suena una alerta distinta, con ícono y patrón de vibración propios.

### Fase 11 — Un panel único para controlar qué se ve en el mapa

Con dos ejes de riesgo (siniestro e inseguridad) y tres formas de ver el de siniestro (clusters, mapa de calor, corredores), la interfaz empezaba a acumular botones sueltos sin una lógica clara. Se rediseñó como un único "Panel de Capas": un lado controla qué vista de fondo se usa para siniestros, el otro controla si se muestra inseguridad y con qué dataset (apagada, delito general, o robos con moto — mutuamente excluyentes, no combinables). La capa de inseguridad se dibuja con una paleta de violeta/magenta deliberadamente distinta de la paleta verde-amarillo-naranja-rojo de siniestros, para que se distinga de un vistazo incluso superpuesta a las otras capas, y cuando está activa el resto del mapa se atenúa (baja de opacidad) para que la capa recién activada quede en primer plano visual. También se agregó agrupamiento por zoom (clustering de marcadores) a la capa de inseguridad, que hasta ese momento dibujaba cada punto individual sin importar qué tan alejado estuvieras — algo que la vista de clusters de siniestros ya tenía resuelto desde antes.

### Fase 12 — Tráfico en vivo y rutas reales con TomTom (reemplazando al servidor de pruebas OSRM)

Hasta acá, el trazado de la ruta en el mapa (qué calles seguir para ir de un punto a otro) salía de OSRM, un servicio gratuito y público, pero pensado explícitamente para pruebas: no da ninguna garantía de que vaya a estar disponible ni de cuánto se puede usar antes de que empiece a fallar. Servía perfecto mientras el proyecto se probaba en una sola computadora, pero no era algo sobre lo que construir una app real.

Se sumó una cuenta propia en TomTom (una empresa que, entre otras cosas, vende exactamente este tipo de servicio: calcular rutas y saber qué tan congestionada está cada calle en este momento) y se migró a ella en dos pasos. Primero se agregó una capa visual opcional en el mapa que muestra, con líneas de color, qué tan lento está el tránsito en cada calle ahora mismo (igual que en Google Maps o Waze) — una capa que el usuario prende o apaga a gusto, sin afectar nada del cálculo de riesgo. Después se reemplazó el cálculo de ruta en sí: en vez de pedirle el trazado a OSRM y por separado un tiempo estimado a TomTom (que podían no coincidir del todo, porque cada uno elige sus propias calles), ahora un único pedido a TomTom trae el trazado, las alternativas, el tiempo de viaje con y sin tráfico en vivo, y las indicaciones de manejo (doblar en tal calle, entrar a la rotonda, etc.) todo junto y consistente entre sí.

Un detalle de diseño importante: la clave de acceso a TomTom nunca llega al navegador. Todos los pedidos pasan primero por el backend propio, que es quien de verdad le habla a TomTom — si la clave viajara hasta el navegador, cualquiera podría copiarla desde ahí y gastar la cuota gratuita del proyecto.

### Fase 13 — Segunda vuelta de calibración: HDBSCAN también para los hotspots de robos con moto

Después de pasar los hotspots de siniestro a HDBSCAN (Fase 4), quedó la duda de si convenía hacer lo mismo con los dos hotspots de inseguridad (delito general y robos con moto), que seguían con la calibración manual original de DBSCAN, sin el barrido sistemático que sí se le hizo a los de siniestros.

Antes de tocar nada se midió la cobertura real de cada uno (algo que no estaba documentado con un número exacto hasta ese momento): delito general venía en 29.2%, pero robos con moto en apenas 14.1% — bastante bajo. Se probó un barrido de HDBSCAN sobre robos con moto (un dataset de unos 16 mil casos, tamaño parecido al de los siniestros de moto) y el resultado fue contundente: 74.3% de cobertura, más del quíntuple de lo que daba DBSCAN, con el cluster más grande en apenas 0.79% del total (más seguro que el 3% que toleraba la calibración anterior). Se actualizó `notebooks/identificar_hotspots_inseguridad.py` para usar HDBSCAN ahí.

Con delito general fue distinto: es un dataset mucho más grande (más de 400 mil casos, casi 20 veces más denso que robos con moto), y HDBSCAN no llegó a terminar ni una sola combinación en el entorno de trabajo usado para esta migración, ni esperando varios minutos. Es probable que en una computadora normal sí termine, solo que tardando más de lo razonable para probarlo a mano varias veces seguidas, así que se dejó armado un script aparte (`notebooks/sweep_hdbscan_inseguridad_general.py`) para correrlo una sola vez, sin apuro, y decidir después si vale la pena migrar esa capa también. Por ahora delito general sigue con DBSCAN.

---

## Parte 4 — Cómo se conecta todo, explicado con una analogía

Imaginate un restaurante:

- **El frontend (lo que ves en el navegador)** es el salón del restaurante y el menú: la parte con la que interactuás directamente, donde ves el mapa, tocás botones, escribís direcciones.
- **El backend (el servidor de datos)** es la cocina: no lo ves directamente, pero es quien recibe tu pedido ("quiero ver las zonas de riesgo"), lo procesa, y te devuelve el resultado.
- **La base de datos** es la despensa: donde están guardados los ingredientes base (los 740 puntos de riesgo, su ubicación, su historial).
- **El modelo de Machine Learning** es el chef con experiencia: alguien que, después de haber visto miles de platos servidos antes (los 23.343 siniestros históricos), sabe estimar "con esta combinación de ingredientes, este plato probablemente sale así de bueno o malo" — sin tener que consultar un libro de recetas fijas, porque aprendió el patrón con la práctica.

Cuando abrís la aplicación: el salón (frontend) le pide a la cocina (backend) el menú del día. La cocina va a la despensa (base de datos), saca los 740 ingredientes base, y para cada uno le pregunta al chef (modelo) "con este ingrediente, en este momento del día, ¿qué tan bien va a salir?". El chef responde con su estimación, y la cocina arma el plato final (el color de cada zona) que el salón te muestra en el mapa.

---

## Parte 5 — Los programas instalados, uno por uno, explicados

| Programa | Qué es, en criollo | Para qué se usa acá |
|---|---|---|
| **Docker Desktop** | Un programa que te deja correr "cajas" con software ya preparado adentro, sin instalar ese software directo en tu Windows. | Levanta la base de datos sin tener que instalar PostgreSQL a mano. |
| **PostgreSQL + PostGIS** | Un sistema de base de datos, con un agregado (PostGIS) que sabe manejar coordenadas geográficas de forma eficiente. | Guarda los 740 puntos de riesgo con su ubicación exacta. |
| **Python** | Un lenguaje de programación, uno de los más usados para análisis de datos e Inteligencia Artificial. | El lenguaje en el que está escrito todo el análisis, el modelo, y el servidor de datos. |
| **Node.js** | Un entorno que permite correr JavaScript (otro lenguaje de programación) fuera del navegador. | Necesario para construir y probar la parte visual (el mapa). |
| **Visual Studio Code (VS Code)** | Un editor de texto especializado en escribir código, con ayudas visuales (colores, sugerencias). | Donde escribiste y modificaste todos los archivos del proyecto. |
| **DBeaver** | Un programa con botones e interfaz visual para mirar bases de datos sin escribir comandos a mano. | Para confirmar que los datos se cargaron bien en la base. |
| **Git y GitHub** | Git es un sistema que guarda el "historial de cambios" de tu código. GitHub es una copia de ese historial guardada en internet. | Respaldo de todo el proyecto — si tu computadora se rompe, el código no se pierde. |
| **Jupyter Notebook** | Un programa que te deja escribir y ejecutar código Python "de a pedazos" (celdas), viendo el resultado de cada pedazo al instante. | Donde se hizo todo el trabajo de limpieza de datos y entrenamiento del modelo. |

---

## Parte 6 — El diagrama completo del sistema

```
┌──────────────────┐
│   TU NAVEGADOR     │   ← acá interactuás vos, con el mouse y el teclado
│  (el mapa que ves)  │
└──────────────────┘
          │
          │  "dame las zonas de riesgo"
          ▼
┌──────────────────┐
│  El servidor de       │   ← recibe el pedido, lo procesa
│  datos (backend)      │
└──────────────────┘
          │
          ├──────────────► Le pregunta a la base de datos:
          │                "¿cuáles son los 740 puntos de riesgo?"
          │
          └──────────────► Para cada uno, le pregunta al modelo entrenado:
                            "con este contexto y la hora de ahora,
                             ¿qué probabilidad de gravedad hay?"
                                       │
                                       ▼
                            El modelo responde con un número
                            (por ejemplo: 45% grave, 38% leve, 17% mortal)
                                       │
                                       ▼
          El servidor traduce eso a un color (verde/amarillo/naranja/rojo)
          y se lo devuelve al navegador, que pinta el mapa.
```

El mismo backend expone hoy más pedidos posibles que "dame las zonas de riesgo": entre otros, `/corredores` (avenidas completas con score de riesgo), `/hotspots-inseguridad` (los 805 hotspots de delitos), y `/reportes` (leer, crear o borrar reportes colaborativos, ya guardados en la base de datos y no solo en el navegador de quien los carga).

Además, el navegador le habla directamente a dos servicios externos, aplicaciones gratuitas de terceros que se usan como piezas:
- **Open-Meteo**: te da el clima real del momento.
- **Nominatim**: convierte una dirección escrita ("Av. Rivadavia 1200") en coordenadas.

El cálculo de ruta y el tráfico en vivo (TomTom) son distintos: no se le habla directo desde el navegador, sino que el backend hace ese pedido por vos (ver Fase 12) — así la clave de acceso a TomTom nunca queda expuesta en el navegador.

---

## Parte 7 — Qué es 100% real, y qué es una simplificación consciente

Es importante que tengas esto clarísimo, porque en algún momento (en la defensa de tu tesis, por ejemplo) te pueden preguntar exactamente esto.

### Lo que es genuinamente real:

- Los 65.818 siniestros descargados del gobierno son datos oficiales, no inventados.
- Los 23.343 casos de motociclistas usados para entrenar el modelo son reales.
- Los 740 puntos de riesgo en el mapa salen de un análisis matemático real (HDBSCAN, con parámetros elegidos tras comparar contra DBSCAN en un barrido sistemático, no a mano) sobre esos datos, no fueron puestos a mano.
- El modelo que predice cada nivel de riesgo fue entrenado de verdad con esos 23.343 casos, y evaluado correctamente para ver qué tan bien predice.
- Las predicciones que ves ahora mismo en el mapa son la respuesta real de ese modelo, calculada en el momento — no son un color fijo escrito en el código.
- El clima que aparece arriba es el clima real de Buenos Aires en este instante.
- Los 805 hotspots de inseguridad (303 de delito general con DBSCAN, 502 de robos con moto con HDBSCAN) salen de un proceso real de clustering aplicado sobre delitos oficiales de la Ciudad, recalibrado para este dataset porque los delitos se agrupan geográficamente distinto que los siniestros.
- El score de riesgo de cada ruta suma de verdad ambos ejes (siniestro e inseguridad) y siempre lo muestra desglosado por tipo, no es una etiqueta decorativa: la suma es válida porque ambos ejes ya están en la misma escala ordinal de severidad calculada por percentiles.
- El trazado de cada ruta, sus alternativas, el tiempo con tráfico en vivo y la capa de congestión que se ve en el mapa salen de la Routing API real de TomTom, no de una estimación fija — se actualizan en cada pedido.

### Lo que es una simplificación consciente (no un engaño, una decisión de alcance):

- **Cobertura de hotspots del 75.6%, no del 100%**: casi un cuarto de los siniestros históricos de moto (24.4%) quedan "aislados", sin caer dentro de ningún hotspot — casos demasiado dispersos como para formar una zona compacta bajo cualquier calibración razonable. Es una mejora real frente al 49.9% que daba la calibración anterior con DBSCAN, lograda al pasar a HDBSCAN, pero sigue siendo un trade-off consciente entre cobertura y precisión geográfica: forzar coberturas más altas todavía empieza a arriesgar el mismo problema de fusionar zonas distintas en una sola que ya se había descartado antes, verificado en ambos casos chequeando el tamaño del cluster más grande como % del total.
- **El modelo prioriza detectar casos graves y mortales por sobre la precisión general, a propósito**: se probaron varias configuraciones del Random Forest contra un holdout temporal real (2025, nunca visto durante el ajuste) y se eligió una (`class_weight="balanced_subsample"`, hojas mínimas de 5 en vez de 1) que casi duplica la detección de casos graves y mortales a cambio de una accuracy general más baja y más falsas alarmas en casos leves. Para una app de seguridad vial es la decisión correcta, pero es una decisión de producto explícita, no la que un ajuste automático ciego hubiera elegido (de hecho, un ajuste automático por validación cruzada encontró una configuración que rendía mejor en el propio período de entrenamiento pero mucho peor contra datos futuros reales — sobreajuste puro).
- **Alcance geográfico**: el proyecto cubre solo la Ciudad de Buenos Aires (CABA). No se encontraron datos públicos y geolocalizados equivalentes para el resto del Gran Buenos Aires, a pesar de haberlos buscado.
- **El modelo usa el "perfil típico" de cada zona, no la situación exacta del momento**: cuando el sistema calcula el riesgo de una zona, usa la hora actual (correcto) pero el tipo de contraparte, edad y sexo "más comunes" en el historial de esa zona (una aproximación razonable, pero no la situación exacta de la persona que está mirando el mapa ahora mismo).
- **Un 40% de las edades de víctimas usadas para entrenar el modelo son estimadas**, no reales — esa información faltaba en un 40% de los registros originales del gobierno, y en vez de descartar esos casos se completó con un valor promedio, dejando marcado cuáles eran estimados.
- **El índice de inseguridad por comuna no es un cálculo en vivo**: a diferencia de las predicciones de siniestro (que se recalculan en cada pedido con la hora actual) o de los hotspots (que salen de clustering sobre datos ya cargados), el índice se actualiza manualmente cuando se refresca el dataset de delitos, algo que hoy ocurre una vez al año porque así se publica el dataset oficial. Esto está explícito en la interfaz, no oculto.
- **Los hotspots de "delito general" y de "robos con moto" son capas separadas y mutuamente excluyentes en el mapa, no combinables**: es una decisión de diseño (mostrar ambas juntas duplicaría puntos sobre los mismos hechos, porque el robo con moto es un subconjunto del delito general), no una limitación técnica evaluada a fondo contra otras alternativas de presentación.
- **Tus filtros elegidos en el mapa se guardan solo en tu propia computadora** (en la memoria del navegador). Los reportes que mandás sí dejaron de ser así: desde que se conectaron al backend, se guardan en la base de datos y los ve cualquiera que abra la app, no solo quien los cargó.

---

## Parte 8 — Glosario completo

| Término | Explicación simple |
|---|---|
| **Frontend** | La parte de una aplicación que ves e interactuás directamente (botones, mapa, texto). |
| **Backend** | La parte de una aplicación que corre "detrás de escena", procesando pedidos y sirviendo datos. |
| **Endpoint** | Una dirección específica dentro de una API a la que le pedís algo puntual. |
| **Base de datos** | Sistema organizado para guardar y consultar información. |
| **Modelo (de Machine Learning)** | El resultado de entrenar un algoritmo con datos históricos; queda "guardado" y listo para predecir casos nuevos. |
| **Entrenar** | El proceso de mostrarle datos históricos a un algoritmo para que aprenda un patrón. |
| **Predecir / Predicción** | Usar un modelo ya entrenado para estimar un resultado sobre una situación nueva. |
| **Dataset** | Un conjunto de datos, generalmente organizado como una tabla (filas y columnas). |
| **Limpieza de datos** | El proceso de corregir errores, inconsistencias y datos faltantes antes de usarlos. |
| **Clustering / Agrupamiento** | Técnica para encontrar grupos de puntos que están cerca entre sí. |
| **HDBSCAN** | El algoritmo específico de clustering usado para encontrar los 740 hotspots de siniestro. A diferencia de DBSCAN (que usa un radio fijo), se adapta a la densidad local de cada zona. |
| **Random Forest / XGBoost** | Dos algoritmos distintos de Machine Learning, ambos usados y comparados en este proyecto. |
| **Hotspot** | Una zona donde se repiten siniestros con más frecuencia de lo normal. |
| **API** | La forma en que dos programas se comunican entre sí, con reglas fijas de qué se puede pedir. |
| **Repositorio (repo)** | La carpeta completa de un proyecto, tal como la ve Git. |
| **Commit** | Una "foto" guardada del estado del código en un momento determinado. |
| **Push** | Mandar tus commits guardados localmente hacia GitHub. |
| **Terminal / Consola** | Ventana donde escribís comandos de texto para darle instrucciones a la computadora. |
| **Servidor** | Un programa que queda esperando pedidos y respondiendo con información. |
| **Localhost** | Una forma de decir "esta misma computadora" — no es internet, es tu propia PC. |
| **Índice de inseguridad** | Un valor por comuna que resume qué tan inseguro es un área en general, calculado una vez sobre el dataset de delitos y actualizado manualmente, no en vivo. |
| **Hotspot de inseguridad** | Una zona donde se repiten delitos con más frecuencia de lo normal. Delito general usa DBSCAN; robos con moto pasó a HDBSCAN (mismo algoritmo que los siniestros) después de una segunda calibración, porque el dataset es de tamaño parecido al de siniestros y se beneficiaba de lo mismo. |
| **Score de ruta / desglose** | El número total de riesgo que suma una opción de ruta, siempre mostrado junto con cuánto de ese total corresponde a siniestro y cuánto a inseguridad, para no ocultar de qué tipo es el riesgo. |
| **Percentil (para nivel de riesgo)** | La posición relativa de un valor dentro de su propio dataset (por ejemplo, "está en el percentil 95" significa que es más alto que el 95% de los demás casos). Se usa para definir los cortes entre bajo/medio/alto/crítico dentro de cada eje de riesgo. |

---

## Parte 9 — Preguntas frecuentes

**¿Si apago la computadora, se pierde todo?**
No. El código está guardado en tu disco duro y también respaldado en GitHub. Lo único que se "apaga" es que los programas dejan de estar corriendo — hay que volver a levantarlos siguiendo el Manual de Operación.

**¿Otra persona podría usar esta aplicación desde su celular ahora mismo?**
No todavía. Hoy todo corre únicamente en tu computadora. Para que otra persona pueda usarlo desde afuera, habría que "publicar" (deploy) el proyecto en un servidor de internet — no forma parte de lo construido hasta ahora.

**¿El modelo va a seguir prediciendo bien para siempre?**
No necesariamente — fue entrenado con datos hasta 2025. Si cambian los patrones de siniestralidad, habría que volver a entrenarlo con datos más nuevos.

**¿Qué pasa si quiero agregar el conurbano bonaerense más adelante?**
Habría que encontrar un dataset con la misma estructura para la Provincia de Buenos Aires, y repetir el mismo proceso de limpieza, clustering y entrenamiento que se hizo para CABA.

**¿La capa de inseguridad se actualiza en vivo como la de siniestros?**
No de la misma forma. Los hotspots de inseguridad y el índice por comuna salen de un dataset de delitos que el gobierno publica con periodicidad anual, así que se recalculan cuando ese dataset se refresca, no en cada pedido al mapa como sí ocurre con las predicciones del modelo de siniestros. Esto queda explícito en el panel de capas de la aplicación.
