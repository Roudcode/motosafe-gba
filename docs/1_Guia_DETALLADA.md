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

Es un sistema organizado para guardar información de forma que se pueda buscar y consultar rápido, como una biblioteca con fichas ordenadas en vez de libros tirados en el piso. En este proyecto, la base de datos guarda los 430 puntos de riesgo del mapa (ubicación, cantidad de siniestros históricos, etc.).

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

Con los 23.343 siniestros de motociclistas ya limpios, se usó un algoritmo llamado DBSCAN para encontrar **agrupaciones geográficas reales** — es decir, esquinas o tramos de avenida donde los siniestros no son casualidad aislada, sino que se repiten una y otra vez en el mismo lugar. El primer intento agrupó "demasiado" (toda la ciudad en un solo grupo gigante, por un error de calibración), pero ajustando los parámetros se llegó a 430 zonas de riesgo reales y bien definidas.

### Fase 5 — Entrenar el modelo predictivo

Con esos datos reales, se entrenaron y compararon **cuatro versiones distintas** de modelos de Machine Learning, probando dos algoritmos distintos (Random Forest y XGBoost) y dos conjuntos de información distinta (solo contexto del lugar, versus contexto más datos de la víctima como edad y sexo). Se midió cuál predecía mejor los casos graves y mortales — que son los que menos casos tienen mientras que los leves son en su mayoría los que hay en la base de datos, así que hacía falta usar formas específicas de medir esto (no simplemente "cuántas veces acertó en total", que hubiera sido engañoso).

El mejor resultado fue el Random Forest que incluye edad y sexo de la víctima — se guardó como el modelo definitivo.

### Fase 6 — Conectar todo: el mapa ahora usa el modelo real

Finalmente, se conectó el modelo entrenado al servidor de datos, de forma que cada vez que el mapa pide "dame las zonas de riesgo", el servidor le pregunta al modelo real —en el momento, con la hora y el día actuales— qué probabilidad de gravedad tiene cada una de las 430 zonas, y pinta el mapa con ese resultado. Ya no es un color fijo inventado: es la salida en vivo de una Inteligencia Artificial entrenada con datos reales.

---

## Parte 4 — Cómo se conecta todo, explicado con una analogía

Imaginate un restaurante:

- **El frontend (lo que ves en el navegador)** es el salón del restaurante y el menú: la parte con la que interactuás directamente, donde ves el mapa, tocás botones, escribís direcciones.
- **El backend (el servidor de datos)** es la cocina: no lo ves directamente, pero es quien recibe tu pedido ("quiero ver las zonas de riesgo"), lo procesa, y te devuelve el resultado.
- **La base de datos** es la despensa: donde están guardados los ingredientes base (los 430 puntos de riesgo, su ubicación, su historial).
- **El modelo de Machine Learning** es el chef con experiencia: alguien que, después de haber visto miles de platos servidos antes (los 23.343 siniestros históricos), sabe estimar "con esta combinación de ingredientes, este plato probablemente sale así de bueno o malo" — sin tener que consultar un libro de recetas fijas, porque aprendió el patrón con la práctica.

Cuando abrís la aplicación: el salón (frontend) le pide a la cocina (backend) el menú del día. La cocina va a la despensa (base de datos), saca los 430 ingredientes base, y para cada uno le pregunta al chef (modelo) "con este ingrediente, en este momento del día, ¿qué tan bien va a salir?". El chef responde con su estimación, y la cocina arma el plato final (el color de cada zona) que el salón te muestra en el mapa.

---

## Parte 5 — Los programas instalados, uno por uno, explicados

| Programa | Qué es, en criollo | Para qué se usa acá |
|---|---|---|
| **Docker Desktop** | Un programa que te deja correr "cajas" con software ya preparado adentro, sin instalar ese software directo en tu Windows. | Levanta la base de datos sin tener que instalar PostgreSQL a mano. |
| **PostgreSQL + PostGIS** | Un sistema de base de datos, con un agregado (PostGIS) que sabe manejar coordenadas geográficas de forma eficiente. | Guarda los 430 puntos de riesgo con su ubicación exacta. |
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
          │                "¿cuáles son los 430 puntos de riesgo?"
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

Además, el navegador también le habla directamente a tres servicios externos, que no son parte de tu proyecto sino aplicaciones gratuitas de terceros que se usan como piezas:
- **Open-Meteo**: te da el clima real del momento.
- **OSRM**: calcula rutas reales siguiendo las calles.
- **Nominatim**: convierte una dirección escrita ("Av. Rivadavia 1200") en coordenadas.

---

## Parte 7 — Qué es 100% real, y qué es una simplificación consciente

Es importante que tengas esto clarísimo, porque en algún momento (en la defensa de tu tesis, por ejemplo) te pueden preguntar exactamente esto.

### Lo que es genuinamente real:

- Los 65.818 siniestros descargados del gobierno son datos oficiales, no inventados.
- Los 23.343 casos de motociclistas usados para entrenar el modelo son reales.
- Los 430 puntos de riesgo en el mapa salen de un análisis matemático real (DBSCAN) sobre esos datos, no fueron puestos a mano.
- El modelo que predice cada nivel de riesgo fue entrenado de verdad con esos 23.343 casos, y evaluado correctamente para ver qué tan bien predice.
- Las predicciones que ves ahora mismo en el mapa son la respuesta real de ese modelo, calculada en el momento — no son un color fijo escrito en el código.
- El clima que aparece arriba es el clima real de Buenos Aires en este instante.

### Lo que es una simplificación consciente (no un engaño, una decisión de alcance):

- **Alcance geográfico**: el proyecto cubre solo la Ciudad de Buenos Aires (CABA). No se encontraron datos públicos y geolocalizados equivalentes para el resto del Gran Buenos Aires, a pesar de haberlos buscado.
- **El modelo usa el "perfil típico" de cada zona, no la situación exacta del momento**: cuando el sistema calcula el riesgo de una zona, usa la hora actual (correcto) pero el tipo de contraparte, edad y sexo "más comunes" en el historial de esa zona (una aproximación razonable, pero no la situación exacta de la persona que está mirando el mapa ahora mismo).
- **Un 40% de las edades de víctimas usadas para entrenar el modelo son estimadas**, no reales — esa información faltaba en un 40% de los registros originales del gobierno, y en vez de descartar esos casos se completó con un valor promedio, dejando marcado cuáles eran estimados.
- **Los reportes que mandás desde la app, y tus filtros elegidos, se guardan solo en tu propia computadora** (en la memoria del navegador), no en un servidor compartido.

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
| **DBSCAN** | El algoritmo específico de clustering usado para encontrar los 430 hotspots. |
| **Random Forest / XGBoost** | Dos algoritmos distintos de Machine Learning, ambos usados y comparados en este proyecto. |
| **Hotspot** | Una zona donde se repiten siniestros con más frecuencia de lo normal. |
| **API** | La forma en que dos programas se comunican entre sí, con reglas fijas de qué se puede pedir. |
| **Repositorio (repo)** | La carpeta completa de un proyecto, tal como la ve Git. |
| **Commit** | Una "foto" guardada del estado del código en un momento determinado. |
| **Push** | Mandar tus commits guardados localmente hacia GitHub. |
| **Terminal / Consola** | Ventana donde escribís comandos de texto para darle instrucciones a la computadora. |
| **Servidor** | Un programa que queda esperando pedidos y respondiendo con información. |
| **Localhost** | Una forma de decir "esta misma computadora" — no es internet, es tu propia PC. |

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
