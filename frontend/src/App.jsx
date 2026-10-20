import { useState, useEffect, useMemo, useRef, useCallback, lazy, Suspense } from 'react'
import './App.css'

import {
  Search, X, MapPin, ArrowUpDown, Home, Save, Briefcase, LocateFixed, Pencil, Zap, Scale,
  ShieldCheck, CircleCheck, TriangleAlert, Compass, Bike, Box, BarChart3, LogOut, Wrench, WifiOff,
  Siren, ShieldAlert, Layers, Navigation, Square, Gauge, CornerDownRight, Clock, Newspaper, ArrowUpRight, ArrowUp,
  ChevronDown, ChevronUp,
} from 'lucide-react'

import {
  CENTRO_GBA, UMBRAL_CRUCE_KM, UMBRAL_ALERTA_KM, ORDEN_NIVELES, PESO_RIESGO,
  RADIO_ALERTA_REPORTE_KM, MINUTOS_ALERTA_REPORTE_RECIENTE, CATEGORIAS_ALERTA_PROXIMIDAD,
  API_URL, CLAVE_AUTOR_ID, CLAVE_TOKENS_REPORTES, CLAVE_NIVELES, CLAVE_FAVORITOS, CLAVE_TEMA, CLAVE_ONBOARDING, CLAVE_CAPA_MAPA, NIVELES, CATEGORIAS_REPORTE,
  CLAVE_CAPA_INSEGURIDAD, OPCIONES_CAPA_INSEGURIDAD, NIVELES_INSEGURIDAD_COLOR, CLAVE_CAPA_TRAFICO, UMBRAL_ZOOM_TRAFICO,
  CLAVE_FILTRO_HEXAGONO, OPCIONES_FILTRO_HEXAGONO,
  CLAVE_CACHE_HOTSPOTS, CLAVE_CACHE_CORREDORES, CLAVE_CACHE_INSEGURIDAD_GENERAL, CLAVE_CACHE_INSEGURIDAD_MOTO,
  CLAVE_CAPA_PRENSA,
} from './constants'
import { siguientePaso, distanciaKm, calcularAjuste, geocodificar, calcularRumbo, calcularProgresoRuta, distanciaAPolilinea } from './utils/geoRiesgo'
import {
  unificarZonasInseguridad, unificarZonasRiesgo, calcularZonasCruzadasPorRuta, calcularCoberturaRegistrada, calcularCoberturaPorFuente, calcularRutasConScore,
} from './utils/riesgoRuta'
import { formatearAntiguedad, formatearDistancia, formatearPeriodo } from './utils/tiempo'
import { iconoClima, reproducirBeep, textoManiobra, iconoManiobra } from './utils/ui'
import { cargarDeLocalStorage, guardarEnLocalStorage, generarUuidV4Fallback } from './utils/storage'
import { LoadingScreen } from './components/LoadingScreen'
import { Onboarding } from './components/Onboarding'
import { ThemeToggle } from './components/ThemeToggle'
import { CapasPanel } from './components/CapasPanel'
import { ActividadPortal } from './components/ActividadPortal'
// MapLibre pesa ~800 kB: se carga aparte para que la app abra antes (SES-086).
const MapaMotoSafe = lazy(() => import('./components/MapaMotoSafe').then((m) => ({ default: m.MapaMotoSafe })))
import { useBusquedaDireccion } from './hooks/useBusquedaDireccion'
import { usePanelSaliente } from './hooks/usePanelSaliente'
import { useSesion } from './sesion'

// Colores para mostrar la probabilidad cruda del modelo (LEVE/GRAVE/MORTAL) en el
// panel de detalle de zona — mismos tonos semánticos que los niveles de riesgo
// (bajo=verde, alto=naranja, crítico=rojo), pero mapeados a las clases reales del
// modelo en vez de al nivel ya traducido.
const COLOR_CLASE_MODELO = { LEVE: '#3DDC84', GRAVE: '#FF8C42', MORTAL: '#FF3B3B' }

// Nivel de zoom "de navegación", tipo Waze/Google Maps al arrancar un viaje
// (mucho más cerca que el zoom de exploración general, zoomInicial=11 más
// abajo). Se aplica una sola vez al activar Modo Viaje -- después el usuario
// puede alejarse con pellizco sin que se lo pisemos en cada actualización de
// posición, mismo criterio que usan esas apps.
const ZOOM_NAVEGACION = 17

// Distancia mínima entre dos fixes de GPS para confiar en el rumbo calculado
// por diferencia de posición (fallback cuando coords.heading no está
// disponible). Por debajo de esto el ruido normal del GPS da rumbos
// erráticos que harían temblar el mapa sin que el usuario se haya movido.
const DISTANCIA_MIN_PARA_RUMBO_KM = 0.003

// Velocidad mínima (m/s) para confiar en coords.heading -- ese campo es
// "rumbo sobre el terreno" (course over ground), calculado por el propio GPS
// a partir de fixes consecutivos: con el vehículo detenido o a paso de
// caminata es tan ruidoso como calcularlo a mano, pero a diferencia del
// fallback manual (ver DISTANCIA_MIN_PARA_RUMBO_KM) no tenía ningún filtro,
// así que la cámara 3D podía "volverse loca" girando sola parado en un
// semáforo o probando la app sin moverse en moto real. Mismo criterio de
// fondo que el piso de velocidad para el ETA más abajo: por debajo de esto,
// la señal no alcanza para decir hacia dónde se apunta.
const VELOCIDAD_MIN_PARA_RUMBO_GPS = 1.5
// Por debajo de ~15 km/h (4,2 m/s) el ritmo GPS no sirve para estimar el tiempo: el
// reparto proporcional de la ruta es mas estable (SES-089). Antes el piso era 1,5 m/s.
const VELOCIDAD_MIN_PARA_ETA_GPS = 4.2
const CLAVE_BUSQUEDAS_RECIENTES = 'motosafe_busquedas_recientes'

// Umbral para considerar que el usuario se desvió de la ruta calculada (no
// que el GPS tembló): más que el ruido normal en calle (~15-30m con buena
// señal), lo bastante chico como para reaccionar rápido si de verdad se
// dobló mal. Se exige, además, que se mantenga por varios fixes seguidos
// (ver DESVIOS_SEGUIDOS_PARA_RECALCULAR) antes de recalcular.
const UMBRAL_DESVIO_RUTA_KM = 0.06
const DESVIOS_SEGUIDOS_PARA_RECALCULAR = 3
// Si la ruta recalculada sigue sin "pegarse" a la posición real (calle
// dividida, sentido único, snapping del backend a la calle paralela), sin
// este freno el ciclo detección-de-desvío -> reroute -> sigue desviado se
// repetía cada pocos segundos y el toast de aviso terminaba apareciendo todo
// el tiempo. Con el cooldown, como mucho se avisa una vez cada tanto aunque
// el desvío real persista.
const COOLDOWN_RECALCULO_MS = 20000

// Recorrido restante (sobre la ruta, no en línea recta -- ver el efecto de
// llegada) para dar el viaje por terminado solo. Mismo orden que el radio de
// maniobra normal (30 m, ver siguientePaso).
const RADIO_LLEGADA_KM = 0.03

// Barra de escala manual (mismo cálculo que antes, con Leaflet): MapLibre no
// tiene un control de escala con este estilo visual propio (el suyo trae su
// propio look), así que se mantiene el mismo diseño calculando a mano sobre
// la instancia real de maplibregl.Map en vez de useMap() de react-leaflet.
function EscalaMapa({ mapa }) {
  const [texto, setTexto] = useState('')
  useEffect(() => {
    if (!mapa) return
    const actualizar = () => {
      const centro = mapa.getCenter()
      const zoom = mapa.getZoom()
      const metrosPorPixel = 156543.03392 * Math.cos((centro.lat * Math.PI) / 180) / Math.pow(2, zoom)
      const metros = metrosPorPixel * 80
      const pasos = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
      const cercano = pasos.reduce((prev, curr) => (Math.abs(curr - metros) < Math.abs(prev - metros) ? curr : prev))
      setTexto(cercano >= 1000 ? `${cercano / 1000} km` : `${cercano} m`)
    }
    actualizar()
    mapa.on('zoomend', actualizar)
    mapa.on('moveend', actualizar)
    return () => { mapa.off('zoomend', actualizar); mapa.off('moveend', actualizar) }
  }, [mapa])
  return (
    <div className="escala-mapa">
      <div className="escala-linea" />
      <span>{texto}</span>
    </div>
  )
}

function App() {
  // Estado inicial desde la última respuesta buena guardada en localStorage
  // (ver cargarHotspots/cargarCorredores/cargarInseguridad más abajo, que la
  // renuevan en cada fetch exitoso) -- así, si el celular abre la app sin
  // señal, aparece el último mapa de riesgo conocido en vez de una pantalla
  // de carga infinita. Sigue intentando traer datos frescos en paralelo.
  const [ZONAS_RIESGO, setZonasRiesgo] = useState(() => cargarDeLocalStorage(CLAVE_CACHE_HOTSPOTS, []))
  const [corredores, setCorredores] = useState(() => cargarDeLocalStorage(CLAVE_CACHE_CORREDORES, []))
  const [inseguridadGeneral, setInseguridadGeneral] = useState(() => cargarDeLocalStorage(CLAVE_CACHE_INSEGURIDAD_GENERAL, []))
  const [inseguridadMoto, setInseguridadMoto] = useState(() => cargarDeLocalStorage(CLAVE_CACHE_INSEGURIDAD_MOTO, []))
  const hayHotspotsEnCache = ZONAS_RIESGO.length > 0
  const [cargandoHotspots, setCargandoHotspots] = useState(!hayHotspotsEnCache)
  const [primeraVezListo, setPrimeraVezListo] = useState(hayHotspotsEnCache)
  const [backendError, setBackendError] = useState(false)
  const [erroresCapas, setErroresCapas] = useState({})
  const [actualizacionesCapas, setActualizacionesCapas] = useState({})
  const [recargaCapas, setRecargaCapas] = useState(0)
  const [tema, setTema] = useState(() => cargarDeLocalStorage(CLAVE_TEMA, 'light'))
  // 'hexagonos', no 'clusters': rediseño SES-115, a pedido explícito de Rodo
  // tras comparar con mapas de cobertura tipo Uber/Cabify -- se entiende la
  // zona de un vistazo mejor que los puntos o el heatmap. Solo afecta a quien
  // nunca tocó el panel de Capas (esto es el valor de arranque antes de leer
  // localStorage); quien ya eligió otra vista conserva su elección.
  const [capaMapa, setCapaMapa] = useState(() => cargarDeLocalStorage(CLAVE_CAPA_MAPA, 'hexagonos'))
  const [capaInseguridad, setCapaInseguridad] = useState(() => cargarDeLocalStorage(CLAVE_CAPA_INSEGURIDAD, 'apagado'))
  // Filtro DENTRO de la vista de hexágonos (SES-115): qué datos arma la
  // grilla -- 'todo' por default, igual criterio que el filtro de categoría
  // del portal de Actividad (arranca mostrando todo, se achica desde ahí).
  // Independiente de capaInseguridad (ese es el toggle de la capa de puntos
  // de delitos, una vista de fondo distinta) -- los datos de inseguridad ya
  // se piden siempre (ver fetch de /hotspots-inseguridad más abajo, no
  // depende de que esa capa esté prendida), así que este filtro puede
  // usarlos sin necesidad de prender la otra capa también.
  const [filtroHexagono, setFiltroHexagono] = useState(() => cargarDeLocalStorage(CLAVE_FILTRO_HEXAGONO, 'todo'))
  // Tráfico en vivo (TomTom): apagado por default -- no todos tienen la API key
  // configurada en el backend, y aunque la tengan, no queremos gastar cuota
  // gratuita para usuarios que nunca miraron esta capa.
  const [capaTrafico, setCapaTrafico] = useState(() => cargarDeLocalStorage(CLAVE_CAPA_TRAFICO, false))
  const [traficoNoDisponible, setTraficoNoDisponible] = useState(false)
  // Prensa (robos scrapeados de noticias, ver backend/scrapear_noticias_robos.py):
  // prendida por default, ver la nota en constants.js sobre por qué.
  const [capaPrensa, setCapaPrensa] = useState(() => cargarDeLocalStorage(CLAVE_CAPA_PRENSA, true))
  const [filtroPrensa, setFiltroPrensa] = useState('todos')
  const [reportesPrensa, setReportesPrensa] = useState([])
  const [zoomActual, setZoomActual] = useState(11)
  const [mostrarOnboarding, setMostrarOnboarding] = useState(() => !cargarDeLocalStorage(CLAVE_ONBOARDING, false))
  const [nivelesActivos, setNivelesActivos] = useState(
    () => new Set(cargarDeLocalStorage(CLAVE_NIVELES, Object.keys(NIVELES)))
  )
  const [busqueda, setBusqueda] = useState('')
  const [paso, setPaso] = useState('idle')
  const [ubicacionReporte, setUbicacionReporte] = useState(null)
  const [reportes, setReportes] = useState([])
  const [autorId] = useState(() => {
    // Id de dispositivo, no de usuario: no hay login en el sistema. Sirve solo
    // para que "Borrar mis reportes" borre los del dispositivo que los creo,
    // no los de otro usuario (ver nota en backend/main.py, _asegurar_tabla_reportes).
    let id = cargarDeLocalStorage(CLAVE_AUTOR_ID, null)
    if (!id) {
      id = crypto.randomUUID ? crypto.randomUUID() : generarUuidV4Fallback()
      guardarEnLocalStorage(CLAVE_AUTOR_ID, id)
    }
    return id
  })
  const [tokensReportes, setTokensReportes] = useState(() => cargarDeLocalStorage(CLAVE_TOKENS_REPORTES, {}))
  const [favoritos, setFavoritos] = useState(() => cargarDeLocalStorage(CLAVE_FAVORITOS, { casa: null, trabajo: null }))
  const [miUbicacion, setMiUbicacion] = useState(null)
  const [buscandoUbicacion, setBuscandoUbicacion] = useState(false)
  const [vuelo, setVuelo] = useState(null)
  const [zonaSeleccionada, setZonaSeleccionada] = useState(null)
  const [zonaResaltada, setZonaResaltada] = useState(null)
  const [clima, setClima] = useState(null)
  // Período que cubren los datos de cada capa (/capas/cobertura, A10/A11/A15).
  // Si falla no se muestra nada: es contexto, no bloquea el mapa.
  const [coberturaCapas, setCoberturaCapas] = useState(null)
  const [actividadAbierta, setActividadAbierta] = useState(false)
  const [statsAbierto, setStatsAbierto] = useState(false)
  const [portalActividadAbierto, setPortalActividadAbierto] = useState(false)
  // Lector de notas: vive acá (no adentro de ActividadPortal) porque
  // también se abre desde los marcadores de prensa del mapa (MapaMotoSafe),
  // no solo desde el portal -- un solo lector, dos puntos de entrada.
  const [lectorNota, setLectorNota] = useState(null)
  // Alto regulable del lector (SES-115, pedido de Rodo): arrastrando el
  // "agarre" de arriba se puede ver la nota más grande. Guardado en % de
  // alto de pantalla (no px) para que se adapte solo si el celular rota.
  const [alturaLector, setAlturaLector] = useState(62)
  const arrastrandoLectorRef = useRef(false)
  useEffect(() => {
    const mover = (e) => {
      if (!arrastrandoLectorRef.current) return
      const vh = ((window.innerHeight - e.clientY) / window.innerHeight) * 100
      setAlturaLector(Math.min(94, Math.max(28, vh)))
    }
    const soltar = () => {
      if (!arrastrandoLectorRef.current) return
      arrastrandoLectorRef.current = false
      document.body.style.userSelect = ''
    }
    window.addEventListener('pointermove', mover)
    window.addEventListener('pointerup', soltar)
    return () => {
      window.removeEventListener('pointermove', mover)
      window.removeEventListener('pointerup', soltar)
    }
  }, [])
  const sesion = useSesion()
  const [herramientasAbiertas, setHerramientasAbiertas] = useState(false)
  const [capasAbiertas, setCapasAbiertas] = useState(false)
  const [toast, setToast] = useState(null)
  // Animación de salida de paneles (SES-115): no cambia qué significa
  // "abierto" en el resto de la app, solo cuándo deja de renderizarse.
  const panelCapas = usePanelSaliente(capasAbiertas)
  const panelActividad = usePanelSaliente(actividadAbierta)
  const panelStats = usePanelSaliente(statsAbierto)
  const panelPortalActividad = usePanelSaliente(portalActividadAbierto)
  const panelLectorNota = usePanelSaliente(!!lectorNota)
  const [lectorNotaMostrada, setLectorNotaMostrada] = useState(null)
  if (lectorNota && lectorNota !== lectorNotaMostrada) setLectorNotaMostrada(lectorNota)
  // zonaMostrada retiene la última zona no nula para poder seguir
  // renderizando su contenido durante la animación de salida, incluso
  // cuando zonaSeleccionada ya volvió a null al cerrar.
  const [zonaMostrada, setZonaMostrada] = useState(null)

  const [rutaAbierta, setRutaAbierta] = useState(false)
  // R-04 (Capitulo 6): la prueba real con 12 motociclistas pidio mostrar
  // menos por default y dejar el detalle del calculo como algo opcional
  // (Casos 4 y 10). Arranca cerrado: cada tarjeta de ruta muestra de
  // entrada solo tiempo, distancia y la advertencia principal; cobertura
  // por fuente y el desglose de puntos quedan detras de este toggle.
  const [detalleRutaAbierto, setDetalleRutaAbierto] = useState(false)
  const [origenTexto, setOrigenTexto] = useState('')
  const [destinoTexto, setDestinoTexto] = useState('')
  const [origenPunto, setOrigenPunto] = useState(null)
  const [destinoPunto, setDestinoPunto] = useState(null)
  const [lugarElegido, setLugarElegido] = useState(null)
  // Origen/destino y la barra de búsqueda buscan solo al confirmar (Enter o
  // botón), nunca mientras se escribe: Nominatim prohíbe el autocompletado.
  const sugOrigen = useBusquedaDireccion(origenPunto ? '' : origenTexto, miUbicacion)
  const sugDestino = useBusquedaDireccion(destinoPunto ? '' : destinoTexto, miUbicacion)
  // La barra de búsqueda de arriba filtraba zonas ya cargadas, pero no
  // servía para buscar una dirección que no fuera ya una zona del dataset
  // (una avenida cualquiera, por ejemplo) -- reusa el mismo geocoder que
  // origen/destino para eso, y "elegir" un resultado la manda directo a
  // centra el mapa en el resultado (ver buscarEnMapa más abajo).
  const sugBusqueda = useBusquedaDireccion(busqueda, miUbicacion)
  const [recientes, setRecientes] = useState(() => cargarDeLocalStorage(CLAVE_BUSQUEDAS_RECIENTES, []))
  const [buscaEnFoco, setBuscaEnFoco] = useState(false)
  const [campoActivo, setCampoActivo] = useState(null)
  const [rutasCalculadas, setRutasCalculadas] = useState([])
  const [rutaSeleccionada, setRutaSeleccionada] = useState(0)
  const [rutaCargando, setRutaCargando] = useState(false)
  const [rutaError, setRutaError] = useState(null)
  const [pasoActual, setPasoActual] = useState(1)

  const [modoViaje, setModoViaje] = useState(false)
  const [vistaNavegacion, setVistaNavegacion] = useState(false)
  // Waze/Maps dejan que uno se mueva por el mapa mientras navega (para ver
  // qué hay más adelante, por ejemplo) y muestran un botón de "recentrar"
  // en vez de forzar la cámara de vuelta -- antes acá la cámara se
  // reencuadraba en la posición del GPS en CADA fix (cada 1-2s), así que
  // cualquier intento de mover el mapa a mano quedaba pisado enseguida.
  // true = la cámara sigue al GPS (comportamiento de siempre); false = el
  // usuario paneó a mano y la cámara se queda quieta hasta que toque
  // "recentrar".
  const [siguiendoUbicacion, setSiguiendoUbicacion] = useState(true)
  const [watchId, setWatchId] = useState(null)
  const [zonasAlertadas, setZonasAlertadas] = useState(new Set())
  const [alertaViaje, setAlertaViaje] = useState(null)
  // Alerta de proximidad a un reporte de robo reciente (ver efecto mas abajo,
  // junto al de zonasRiesgoTodas) -- separada de alertaViaje porque esa es
  // contra riesgo historico y esta contra un hecho puntual reportado por otro
  // usuario hace minutos.
  const [reportesAlertados, setReportesAlertados] = useState(new Set())
  const [alertaReporte, setAlertaReporte] = useState(null)
  // Velocidad real del GPS (m/s, la unidad nativa de coords.speed) -- se usa
  // para estimar el tiempo restante de viaje con el ritmo actual en vez de
  // repartir el tiempo total de la ruta en proporción a la distancia (que
  // ignora que ya vas más lento o más rápido que el promedio calculado).
  const [velocidadActual, setVelocidadActual] = useState(null)

  // Instancia real de maplibregl.Map, expuesta por MapaMotoSafe via onReady.
  // Reemplaza lo que antes hacían VueloControlado/SeguimientoEnVivo/
  // ControlesZoom/EscalaMapa con useMap() de react-leaflet: acá se llama
  // directo a los métodos del mapa.
  //
  // rumboActual, en orden de prioridad: 1) coords.heading (lo calcula el
  // propio GPS a partir del desplazamiento, lo más confiable mientras hay
  // movimiento real) -- 2) la brújula del dispositivo (DeviceOrientationEvent,
  // ver activarBrujula más abajo), que es la única fuente que sigue dando un
  // rumbo válido con el vehículo DETENIDO (semáforo, cortada), que es
  // justamente el caso que el GPS no puede cubrir sin desplazamiento -- 3) si
  // ninguna de las dos está disponible, cálculo a mano con calcularRumbo()
  // entre el fix anterior y el actual (ver activarModoViaje).
  const mapaRef = useRef(null)
  // Mide la altura real del topbar (varia segun 1 o 2 lineas, badge de clima
  // presente, largo del texto del status pill, portrait vs landscape) y la
  // publica como variable CSS --topbar-h, de la que dependen --y1/--y2/--y3
  // (ver App.css). Reemplaza los offsets en px hardcodeados que se
  // desincronizaban de la altura real cada vez que el contenido del topbar
  // cambiaba, causando superposiciones repetidas con la searchbar y otros
  // paneles flotantes.
  const topbarRef = useRef(null)
  const [mapaListo, setMapaListo] = useState(false)
  const [rumboActual, setRumboActual] = useState(0)
  // Espejo en ref (no state) de la última lectura de brújula: se lee dentro
  // del callback de watchPosition, que quedó cerrado sobre el render en el
  // que se creó -- un ref siempre da el valor más nuevo sin tener que
  // recrear el watch cada vez que cambia.
  const rumboBrujulaRef = useRef(null)
  const listenerBrujulaRef = useRef(null)
  const zoomNavegacionHechoRef = useRef(false)

  useEffect(() => {
    if (vuelo && mapaListo) mapaRef.current?.flyTo({ center: [vuelo.lng, vuelo.lat], zoom: vuelo.zoom ?? mapaRef.current.getZoom(), duration: 1400 })
  }, [vuelo, mapaListo])

  // Pide la ubicación UNA vez al abrir la app, en silencio (sin mover el
  // mapa ni mostrar nada) -- antes `miUbicacion` quedaba en null hasta que
  // el usuario tocaba "Mi ubicación" o arrancaba un viaje, así que buscar
  // "farmacia" recién abierta la app siempre sesgaba desde CABA aunque el
  // celular tuviera GPS activado (SES-109: Rodo lo reportó parado en
  // Pilar). Si el usuario no dio permiso, falla en silencio y queda como
  // estaba: sin ubicación, igual que antes de este cambio.
  useEffect(() => {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition(
      (pos) => setMiUbicacion((anterior) => anterior ?? { lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => {},
      { timeout: 8000, maximumAge: 300000 }
    )
  }, [])

  // Publica la altura real del topbar en --topbar-h en cada resize (rotar el
  // celular, que el badge de clima aparezca/desaparezca, que el status pill
  // pase a 2 lineas por un texto largo, etc). ResizeObserver dispara una vez
  // al observar y despues en cada cambio de tamaño real del elemento.
  useEffect(() => {
    const el = topbarRef.current
    if (!el) return
    // Altura total de la barra, con su padding (contentRect no lo incluye y dejaba
    // la barra de busqueda encima de los botones redondos; SES-088). Se mide al
    // montar y en cada resize de ventana, y ademas con ResizeObserver para los
    // cambios de contenido (clima, estado) que la hacen cambiar de alto.
    const medir = () => {
      const alto = el.offsetHeight
      if (alto) document.documentElement.style.setProperty('--topbar-h', `${Math.round(alto)}px`)
    }
    medir()
    window.addEventListener('resize', medir)
    const obs = new ResizeObserver(medir)
    obs.observe(el)
    return () => { obs.disconnect(); window.removeEventListener('resize', medir) }
  }, [])

  useEffect(() => {
    if (!modoViaje) zoomNavegacionHechoRef.current = false
  }, [modoViaje])

  // Al arrancar (o reiniciar) el viaje, la cámara vuelve a seguir al GPS --
  // si el usuario había paneado a mano en un viaje anterior, eso no debe
  // "heredarse" al viaje nuevo. El setState va en un setTimeout (no directo
  // en el cuerpo del efecto) por la regla de lint set-state-in-effect.
  useEffect(() => {
    if (!modoViaje) return
    const id = setTimeout(() => setSiguiendoUbicacion(true), 0)
    return () => clearTimeout(id)
  }, [modoViaje])

  // Seguimiento de cámara en 2D (norte arriba, sin inclinación). Cuando
  // vistaNavegacion está activa, es MapaMotoSafe quien controla la cámara
  // (centro + zoom + pitch + bearing juntos, ver ese componente) para que no
  // compitan los dos por moverla al mismo tiempo. siguiendoUbicacion en false
  // significa que el usuario paneó el mapa a mano -- se deja de recentrar
  // hasta que toque el botón de "recentrar" (ver recentrarUbicacion).
  useEffect(() => {
    const map = mapaRef.current
    if (!modoViaje || !miUbicacion || !mapaListo || vistaNavegacion || !map || !siguiendoUbicacion) return
    if (!zoomNavegacionHechoRef.current) {
      zoomNavegacionHechoRef.current = true
      map.easeTo({ center: [miUbicacion.lng, miUbicacion.lat], zoom: ZOOM_NAVEGACION, duration: 1200 })
    } else {
      map.panTo([miUbicacion.lng, miUbicacion.lat], { animate: true, duration: 800 })
    }
  }, [modoViaje, miUbicacion, mapaListo, vistaNavegacion, siguiendoUbicacion])

  // Handler del botón "recentrar" (estilo Waze/Maps): retoma el seguimiento
  // automático y fuerza un primer re-centrado inmediato (si no, con
  // siguiendoUbicacion recién puesto en true, este mismo efecto esperaría al
  // próximo fix de GPS para reaccionar).
  const recentrarUbicacion = () => {
    setSiguiendoUbicacion(true)
    const map = mapaRef.current
    if (map && miUbicacion) {
      if (vistaNavegacion) return // MapaMotoSafe se encarga de esa cámara
      map.easeTo({ center: [miUbicacion.lng, miUbicacion.lat], zoom: ZOOM_NAVEGACION, duration: 600 })
    }
  }

  // Detecta que el usuario paneó el mapa a mano (arrastre real, no una
  // animación programática de easeTo/panTo/flyTo) mientras está en modo
  // viaje, y deja de seguir el GPS hasta que pida recentrar.
  // useCallback (acá y en el resto de los callbacks que bajan a
  // MapaMotoSafe): ese componente ahora está en React.memo (ver su export)
  // para no volver a renderizar el mapa entero cada segundo por el tick de
  // useSegundosDesde -- pero memo compara props por referencia, así que un
  // callback recreado en cada render de App (como estaban antes, funciones
  // inline sueltas) rompía el memo igual. La dependencia real es modoViaje;
  // por eso esta función sí cambia de referencia cuando corresponde, pero ya
  // no en cada tick del reloj.
  const manejarPaneoManual = useCallback(() => {
    if (modoViaje) setSiguiendoUbicacion(false)
  }, [modoViaje])

  // Ahora "real" (no segundos desde el montaje): se usa para calcular antiguedad
  // y opacidad de los reportes colaborativos, se refresca cada 30s (alcanza para
  // el nivel de granularidad de "hace X min" que mostramos).
  const [horaActual, setHoraActual] = useState(() => Date.now())
  // El reloj actualiza App cada segundo. Sin memo, filter() creaba una lista
  // nueva aunque no hubiera noticias nuevas y desmontaba los marcadores/popup.
  const reportesPrensaFiltrados = useMemo(() => {
    if (!capaPrensa) return []
    return reportesPrensa.filter((r) => (
      filtroPrensa === 'todos'
      || r.tipoIncidente === filtroPrensa
      || (filtroPrensa === 'moto' && (r.relacionadoMoto || /\bmoto(?:s|cicleta|cicletas)?\b/i.test(r.titular || '')))
    ))
  }, [capaPrensa, filtroPrensa, reportesPrensa])
  useEffect(() => {
    const id = setInterval(() => setHoraActual(Date.now()), 30000)
    return () => clearInterval(id)
  }, [])

  const mostrarToast = (texto) => {
    setToast(texto)
    setTimeout(() => setToast(null), 2200)
  }

  // Antes esto era un cartel fijo (.ruta-banner) que se quedaba en pantalla
  // TODO el tiempo que estuvieras con la capa de tráfico prendida y alejado
  // del umbral de zoom -- Rodo lo reportó como invasivo y constante, con
  // razón: no avisa una vez, insiste. Ahora es un toast (se muestra solo,
  // se apaga solo a los 2.2s) que aparece una sola vez por cada vez que SE
  // CRUZA el umbral hacia abajo (alejando el zoom con tráfico prendido, o
  // prendiendo tráfico ya alejado) -- no en cada render mientras siga
  // alejado. bajoUmbralRef guarda el estado anterior para detectar ese
  // cruce sin volver a disparar el toast en cada cambio de zoom mientras ya
  // estabas alejado.
  const bajoUmbralTraficoRef = useRef(false)
  useEffect(() => {
    if (!capaTrafico || traficoNoDisponible) { bajoUmbralTraficoRef.current = false; return }
    const bajoUmbral = zoomActual < UMBRAL_ZOOM_TRAFICO
    if (bajoUmbral && !bajoUmbralTraficoRef.current) {
      const id = setTimeout(() => mostrarToast('Acercate para ver el tráfico en detalle'), 0)
      bajoUmbralTraficoRef.current = bajoUmbral
      return () => clearTimeout(id)
    }
    bajoUmbralTraficoRef.current = bajoUmbral
  }, [capaTrafico, traficoNoDisponible, zoomActual])

  const cargarHotspots = () => {
    setCargandoHotspots(true)
    fetch(`${API_URL}/hotspots`)
      .then((r) => {
        if (!r.ok) throw new Error('Respuesta no OK')
        return r.json()
      })
      .then((data) => {
        const zonasFormateadas = data.map((h) => ({
          id: h.id,
          nombre: `Zona ${h.cluster} (${h.cantidad_siniestros} siniestros históricos)`,
          lat: h.latitud,
          lng: h.longitud,
          nivel: h.nivel_riesgo,
          cantidad: h.cantidad_siniestros,
          mortales: h.mortales,
          graves: h.graves,
          motivo: `${h.cantidad_siniestros} siniestros de motociclistas registrados, ${h.mortales} mortales, ${h.graves} graves.`,
          prediccionModelo: h.prediccion_modelo || null,
          contextoEstimado: !!h.contexto_estimado,
          // Ajuste por choque reportado en prensa cerca (ver _aplicar_ajuste_riesgo
          // en backend/main.py), ya presente en /hotspots pero que hasta ahora se
          // descartaba acá -- sin esto un hotspot "crítico de toda la vida" y uno
          // crítico recién por una noticia reciente se veían 100% idénticos en el
          // mapa y en el panel de detalle (ver zonaSeleccionada.ajustadoPorReciente
          // más abajo, y el borde propio en MapaMotoSafe.jsx). Eje distinto del de
          // calcularAjuste/zona.ajuste (ese es por reportes comunitarios de
          // pavimento/corte/iluminación): este viene calibrado por el modelo+prensa.
          ajustadoPorReciente: !!h.ajustado_por_reciente,
          motivoAjuste: h.motivo_ajuste || null,
        }))
        setZonasRiesgo(zonasFormateadas)
        guardarEnLocalStorage(CLAVE_CACHE_HOTSPOTS, zonasFormateadas)
        // El clima es el mismo para los 740 hotspots (una sola ciudad, un
        // solo momento) -- se toma del primero. Es el mismo objeto que ya
        // usó el modelo para calcular nivel_riesgo, no un dato aparte: ver
        // el comentario de iconoClima en utils/ui.js.
        if (data[0]?.clima) setClima(data[0].clima)
        setCargandoHotspots(false)
        setPrimeraVezListo(true)
        setBackendError(false)
      })
      .catch(() => {
        setBackendError(true)
        setCargandoHotspots(false)
        // En una primera visita sin cache no hay mapa para mostrar, pero sí
        // tiene que quedar visible el mensaje con reintento; el loader no
        // puede tapar indefinidamente la única salida disponible.
        setPrimeraVezListo(true)
      })
  }

  useEffect(() => {
    // Fetch de datos al montar: uso canonico de useEffect (sincronizar con un sistema externo).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    cargarHotspots()
  }, [])

  useEffect(() => {
    // Corredores de riesgo (calles completas, precalculadas offline): se cargan
    // una sola vez al montar, igual que los hotspots. No hacen falta reintentos
    // agresivos como con /hotspots porque esta capa es secundaria (arranca en
    // 'clusters') y el usuario la ve recien si cambia de vista.
    fetch(`${API_URL}/corredores`)
      .then((r) => { if (!r.ok) throw new Error('No se pudieron cargar corredores'); return r.json() })
      .then((data) => { setCorredores(data); setErroresCapas((prev) => ({ ...prev, corredores: false })); setActualizacionesCapas((prev) => ({ ...prev, corredores: Date.now() })); if (data.length) guardarEnLocalStorage(CLAVE_CACHE_CORREDORES, data) })
      .catch(() => { setErroresCapas((prev) => ({ ...prev, corredores: true })) })
  }, [recargaCapas])

  useEffect(() => {
    // Hotspots de inseguridad (delitos reales del GCBA, no siniestros de moto):
    // dos capas independientes (general / con moto), precalculadas offline
    // igual que corredores. Se cargan una sola vez al montar; son secundarias,
    // el usuario las ve si cambia de capa.
    fetch(`${API_URL}/hotspots-inseguridad?tipo=general`)
      .then((r) => { if (!r.ok) throw new Error('No se pudo cargar inseguridad general'); return r.json() })
      .then((data) => { setInseguridadGeneral(data); setErroresCapas((prev) => ({ ...prev, inseguridadGeneral: false })); setActualizacionesCapas((prev) => ({ ...prev, inseguridadGeneral: Date.now() })); if (data.length) guardarEnLocalStorage(CLAVE_CACHE_INSEGURIDAD_GENERAL, data) })
      .catch(() => { setErroresCapas((prev) => ({ ...prev, inseguridadGeneral: true })) })
    fetch(`${API_URL}/hotspots-inseguridad?tipo=moto`)
      .then((r) => { if (!r.ok) throw new Error('No se pudo cargar inseguridad con moto'); return r.json() })
      .then((data) => { setInseguridadMoto(data); setErroresCapas((prev) => ({ ...prev, inseguridadMoto: false })); setActualizacionesCapas((prev) => ({ ...prev, inseguridadMoto: Date.now() })); if (data.length) guardarEnLocalStorage(CLAVE_CACHE_INSEGURIDAD_MOTO, data) })
      .catch(() => { setErroresCapas((prev) => ({ ...prev, inseguridadMoto: true })) })
  }, [recargaCapas])

  const cargarReportes = useCallback(() => {
    fetch(`${API_URL}/reportes`)
      .then((r) => { if (!r.ok) throw new Error('No se pudieron cargar reportes'); return r.json() })
        .then((data) => setReportes(data.map((r) => ({
          id: r.id,
        lat: r.lat,
        lng: r.lng,
        categoria: r.categoria,
          esPropio: Boolean(tokensReportes[String(r.id)]),
          creadoEn: r.creado_en,
          confirmaciones: r.confirmaciones || 0,
          venceEn: r.vence_en,
          desmentidas: r.desmentidas || 0,
          estado: 'vigente',
      }))))
      .catch(() => { /* backend caido: se mantienen los reportes que ya estaban cargados */ })
  }, [tokensReportes])

  useEffect(() => {
    cargarReportes()
    // Reportes de otros usuarios pueden aparecer sin que este dispositivo haga nada:
    // se refresca cada 30s para que el mapa los muestre sin recargar la pagina.
    const id = setInterval(cargarReportes, 30000)
    return () => clearInterval(id)
  }, [cargarReportes])

  useEffect(() => {
    // Reportes de prensa (scrapeados a mano/tarea programada, no en vivo, ver
    // scrapear_noticias_robos.py): refrescar cada 30s como los reportes de
    // usuarios sería inútil, esta fuente cambia a lo sumo unas pocas veces
    // por día. 10 minutos alcanza de sobra para que aparezca algo nuevo sin
    // recargar la página, sin pegarle al backend por nada.
    const cargarReportesPrensa = () => {
      fetch(`${API_URL}/reportes-prensa`)
        .then((r) => { if (!r.ok) throw new Error('No se pudo cargar prensa'); return r.json() })
        .then((data) => setReportesPrensa(data.map((r) => ({
          id: r.id,
          lat: r.lat,
          lng: r.lng,
          nivelPrecision: r.nivel_precision,
          radioMetros: r.radio_metros,
          titular: r.titular,
          urlFuente: r.url_fuente,
          fuente: r.fuente,
          tipoIncidente: r.tipo_incidente,
          relacionadoMoto: Boolean(r.relacionado_moto),
          fechaReferencia: r.publicado_en || r.creado_en,
          creadoEn: r.creado_en,
        }))))
        .catch(() => { /* backend caido: se mantienen los que ya estaban cargados */ })
    }
    cargarReportesPrensa()
    const id = setInterval(cargarReportesPrensa, 10 * 60 * 1000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    if (!backendError) return
    const id = setInterval(cargarHotspots, 5000)
    return () => clearInterval(id)
  }, [backendError])

  useEffect(() => {
    // Hotspots incluyen hora y clima actuales: renovar aunque el pedido
    // anterior haya funcionado evita llamar "en vivo" a una respuesta vieja.
    const id = setInterval(cargarHotspots, 5 * 60 * 1000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    fetch(`${API_URL}/capas/cobertura`)
      .then((r) => (r.ok ? r.json() : null))
      .then(setCoberturaCapas)
      .catch(() => setCoberturaCapas(null))
  }, [])

  useEffect(() => { guardarEnLocalStorage(CLAVE_NIVELES, [...nivelesActivos]) }, [nivelesActivos])
  useEffect(() => { guardarEnLocalStorage(CLAVE_FAVORITOS, favoritos) }, [favoritos])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', tema)
    guardarEnLocalStorage(CLAVE_TEMA, tema)
  }, [tema])
  useEffect(() => {
    guardarEnLocalStorage(CLAVE_CAPA_MAPA, capaMapa)
  }, [capaMapa])
  useEffect(() => {
    guardarEnLocalStorage(CLAVE_FILTRO_HEXAGONO, filtroHexagono)
  }, [filtroHexagono])

  useEffect(() => {
    guardarEnLocalStorage(CLAVE_CAPA_INSEGURIDAD, capaInseguridad)
  }, [capaInseguridad])

  useEffect(() => {
    guardarEnLocalStorage(CLAVE_CAPA_TRAFICO, capaTrafico)
  }, [capaTrafico])

  useEffect(() => {
    guardarEnLocalStorage(CLAVE_CAPA_PRENSA, capaPrensa)
  }, [capaPrensa])

  useEffect(() => {
    return () => { if (watchId != null) navigator.geolocation.clearWatch(watchId) }
  }, [watchId])

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key !== 'Escape') return
      if (mostrarOnboarding) { cerrarOnboarding(); return }
      if (rutaAbierta) { cerrarTodoRuta(); return }
      if (paso === 'eligiendo') { setPaso('idle'); setCampoActivo(null); return }
      if (zonaSeleccionada) { setZonaSeleccionada(null); return }
      if (statsAbierto) { setStatsAbierto(false); return }
      if (actividadAbierta) { setActividadAbierta(false); return }
      if (herramientasAbiertas) { setHerramientasAbiertas(false); return }
      if (capasAbiertas) { setCapasAbiertas(false); return }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [mostrarOnboarding, rutaAbierta, paso, zonaSeleccionada, statsAbierto, actividadAbierta, herramientasAbiertas, capasAbiertas])

  const toggleTema = () => setTema((t) => (t === 'dark' ? 'light' : 'dark'))

  // function (no const arrow) para que quede hoisted: se usa en el listener
  // de Escape mas arriba en el archivo, antes de esta linea.
  function cerrarOnboarding() {
    setMostrarOnboarding(false)
    localStorage.setItem(CLAVE_ONBOARDING, JSON.stringify(true))
  }

  const toggleNivel = (nivel) => {
    setNivelesActivos((prev) => {
      const next = new Set(prev)
      next.has(nivel) ? next.delete(nivel) : next.add(nivel)
      return next
    })
  }
  const restablecerFiltros = () => setNivelesActivos(new Set(Object.keys(NIVELES)))

  const pedirUbicacion = () => {
    setBuscandoUbicacion(true)
    if (!navigator.geolocation) { setBuscandoUbicacion(false); return }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const punto = { lat: pos.coords.latitude, lng: pos.coords.longitude }
        setMiUbicacion(punto)
        setVuelo({ ...punto, zoom: 14 })
        setBuscandoUbicacion(false)
      },
      () => setBuscandoUbicacion(false),
      { timeout: 6000 }
    )
  }

  // Brújula del dispositivo: única fuente que sigue dando un rumbo válido
  // con el vehículo detenido (coords.heading del GPS se pone null o deja de
  // actualizarse sin desplazamiento real -- un semáforo, una cortada). En
  // iOS 13+ el permiso de DeviceOrientationEvent SOLO se puede pedir en
  // respuesta directa a un gesto del usuario, por eso esto se llama desde
  // adentro del handler del botón que prende Modo Viaje, nunca desde un
  // useEffect en el montaje.
  const activarBrujula = () => {
    const manejarOrientacion = (evento) => {
      let heading = null
      if (evento.webkitCompassHeading != null) {
        // iOS: ya viene como heading real de brújula, corregido por
        // orientación de pantalla -- se usa tal cual.
        heading = evento.webkitCompassHeading
      } else if (evento.alpha != null) {
        // Android/otros: alpha es la rotación desde el norte en sentido
        // antihorario: hay que invertirla, y sumarle el ángulo de rotación
        // de pantalla (si el celular está montado en horizontal en el
        // manillar, alpha solo no alcanza para el rumbo real).
        const anguloPantalla = window.screen?.orientation?.angle ?? window.orientation ?? 0
        heading = (360 - evento.alpha + anguloPantalla) % 360
      }
      if (heading != null && !Number.isNaN(heading)) rumboBrujulaRef.current = heading
    }
    const escuchar = () => {
      const nombreEvento = 'ondeviceorientationabsolute' in window ? 'deviceorientationabsolute' : 'deviceorientation'
      window.addEventListener(nombreEvento, manejarOrientacion)
      listenerBrujulaRef.current = { nombreEvento, manejarOrientacion }
    }
    const DOE = window.DeviceOrientationEvent
    if (!DOE) return
    if (typeof DOE.requestPermission === 'function') {
      DOE.requestPermission().then((estado) => { if (estado === 'granted') escuchar() }).catch(() => {})
    } else {
      escuchar()
    }
  }

  const desactivarBrujula = () => {
    if (listenerBrujulaRef.current) {
      window.removeEventListener(listenerBrujulaRef.current.nombreEvento, listenerBrujulaRef.current.manejarOrientacion)
      listenerBrujulaRef.current = null
    }
    rumboBrujulaRef.current = null
  }

  // Arranca el seguimiento GPS. conVistaNavegacion=true es el camino que usa
  // "Iniciar viaje" desde una ruta ya calculada: además de prender Modo Viaje,
  // deja lista la cámara 3D de una sola vez, sin que el usuario tenga que ir
  // a buscar el toggle de "Vista inclinada" por separado (que es justamente
  // el problema de UX que se pidió resolver -- que la app se acomode sola).
  const activarModoViaje = (conVistaNavegacion = false) => {
    if (!navigator.geolocation) { mostrarToast('Tu navegador no soporta geolocalización'); return }
    activarBrujula()
    const id = navigator.geolocation.watchPosition(
      (pos) => {
        const punto = { lat: pos.coords.latitude, lng: pos.coords.longitude }
        const heading = pos.coords.heading
        const velocidadGps = pos.coords.speed
        // Cada fix reemplaza la lectura anterior: conservar un valor viejo
        // al detenerse convertía un semáforo en una velocidad/ETA ficticias.
        setVelocidadActual(
          velocidadGps != null && !Number.isNaN(velocidadGps) && velocidadGps > 0.5
            ? velocidadGps
            : null
        )
        const hayVelocidadConfiable = velocidadGps != null && !Number.isNaN(velocidadGps) && velocidadGps >= VELOCIDAD_MIN_PARA_RUMBO_GPS
        if (heading != null && !Number.isNaN(heading) && hayVelocidadConfiable) {
          // El GPS ya viene con rumbo calculado (lo más confiable mientras
          // hay movimiento real, que es el caso normal andando en moto) --
          // pero solo si ese movimiento es real: a velocidad casi nula,
          // coords.heading es tan ruidoso como cualquier otro cálculo por
          // diferencia de posición, y usarlo sin filtro hacía temblar la
          // cámara 3D con el vehículo parado.
          setRumboActual(heading)
        } else if (rumboBrujulaRef.current != null) {
          // Sin heading de GPS (típico parado, sin desplazamiento del que
          // derivar rumbo): la brújula sigue dando una lectura válida, que
          // es justo el caso que el cálculo manual de abajo no cubre.
          setRumboActual(rumboBrujulaRef.current)
        } else {
          // Último fallback: sin GPS ni brújula, se calcula a mano contra el
          // fix anterior. Se ignoran desplazamientos chicos (ruido de GPS
          // con el vehículo casi detenido) para que el rumbo no tiemble.
          setMiUbicacion((anterior) => {
            if (anterior && distanciaKm(anterior, punto) > DISTANCIA_MIN_PARA_RUMBO_KM) {
              setRumboActual(calcularRumbo(anterior, punto))
            }
            return punto
          })
          return
        }
        setMiUbicacion(punto)
      },
      () => mostrarToast('No se pudo obtener tu ubicación en vivo'),
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 }
    )
    setWatchId(id)
    setModoViaje(true)
    setZonasAlertadas(new Set())
    setReportesAlertados(new Set())
    if (conVistaNavegacion) setVistaNavegacion(true)
    mostrarToast(conVistaNavegacion ? 'Navegación iniciada' : 'Modo Viaje activado')
  }

  // `mensaje` lo pisa la llegada automática ("Llegaste a destino" en vez de
  // "Modo Viaje desactivado") -- mismo apagado, distinto motivo.
  const desactivarModoViaje = (mensaje = 'Modo Viaje desactivado') => {
    if (watchId != null) navigator.geolocation.clearWatch(watchId)
    desactivarBrujula()
    setWatchId(null)
    setModoViaje(false)
    setVistaNavegacion(false)
    setRumboActual(0)
    setVelocidadActual(null)
    setZonasAlertadas(new Set())
    setAlertaViaje(null)
    setReportesAlertados(new Set())
    setAlertaReporte(null)
    mostrarToast(mensaje)
  }

  const toggleModoViaje = () => {
    if (modoViaje) { desactivarModoViaje(); return }
    activarModoViaje(false)
  }

  // Acción de "Iniciar viaje" en el resumen de ruta: si ya está en Modo Viaje
  // (por ejemplo lo prendió manualmente antes de trazar la ruta) solo suma la
  // vista 3D; si no, arranca todo junto. Así "comenzar ruta" activa de una la
  // experiencia completa en vez de pedirle al usuario que junte dos toggles.
  const iniciarNavegacionRuta = () => {
    if (modoViaje) { setVistaNavegacion(true); mostrarToast('Navegación iniciada'); return }
    activarModoViaje(true)
  }

  // Antes, si la geolocalización fallaba o el navegador no la soportaba, el
  // reporte se ubicaba en un punto ALEATORIO cerca del centro del GBA sin
  // avisarle nada al usuario -- para una app cuyo valor entero depende de
  // que los datos de ubicación sean reales, eso es peor que no tener el
  // dato: un incidente "fantasma" en un lugar inventado. Ahora, si no hay
  // GPS, se le pide directamente al usuario que toque el mapa para marcar
  // el punto (mismo mecanismo que ya existía para marcar origen/destino de
  // ruta), y ese mismo tap queda disponible siempre durante 'eligiendo' por
  // si el GPS acertó el barrio pero no la esquina exacta.
  const iniciarReporte = () => {
    if (paso === 'eligiendo' || paso === 'buscando') { setPaso('idle'); setCampoActivo(null); return }
    setPaso('buscando')
    const usar = (punto) => {
      setUbicacionReporte(punto)
      setVuelo({ ...punto, zoom: 15 })
      setPaso('eligiendo')
      setCampoActivo('reporte')
    }
    const sinUbicacion = () => {
      setUbicacionReporte(null)
      setPaso('eligiendo')
      setCampoActivo('reporte')
      mostrarToast('No pudimos ubicarte -- tocá el mapa para marcar dónde fue')
    }
    if (!navigator.geolocation) { sinUbicacion(); return }
    navigator.geolocation.getCurrentPosition(
      (pos) => usar({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      sinUbicacion,
      { timeout: 6000 }
    )
  }

  const confirmarReporte = (categoria) => {
    if (!ubicacionReporte) { mostrarToast('Marcá primero el lugar en el mapa'); return }
    const nuevo = { lat: ubicacionReporte.lat, lng: ubicacionReporte.lng, categoria, autor_id: autorId }
    setPaso('idle')
    setCampoActivo(null)
    fetch(`${API_URL}/reportes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(nuevo),
    })
      .then((r) => { if (!r.ok) throw new Error('respuesta no ok'); return r.json() })
      .then((creado) => {
        setReportes((prev) => [{
          id: creado.id,
          lat: creado.lat,
          lng: creado.lng,
          categoria: creado.categoria,
          esPropio: true,
          creadoEn: creado.creado_en,
          confirmaciones: 0,
          desmentidas: 0,
          estado: 'vigente',
        }, ...prev])
        if (creado.delete_token) {
          setTokensReportes((anteriores) => {
            const actualizados = { ...anteriores, [String(creado.id)]: creado.delete_token }
            guardarEnLocalStorage(CLAVE_TOKENS_REPORTES, actualizados)
            return actualizados
          })
        }
        mostrarToast('Reporte enviado — gracias por sumar el dato')
      })
      .catch(() => mostrarToast('No se pudo enviar el reporte (¿backend caído?)'))
  }

  const borrarReportes = async () => {
    const borrables = misReportes.filter((r) => tokensReportes[String(r.id)])
    if (borrables.length === 0) {
      mostrarToast('Estos reportes son anteriores a la protección actual y ya no se pueden borrar desde el dispositivo')
      return
    }
    try {
      const resultados = await Promise.all(borrables.map(async (reporte) => {
        const respuesta = await fetch(`${API_URL}/reportes/${reporte.id}`, {
          method: 'DELETE',
          headers: { 'X-Report-Delete-Token': tokensReportes[String(reporte.id)] },
        })
        if (!respuesta.ok) throw new Error('No se pudo borrar el reporte')
        return reporte.id
      }))
      const eliminados = new Set(resultados)
      setReportes((prev) => prev.filter((r) => !eliminados.has(r.id)))
      setTokensReportes((anteriores) => {
        const actualizados = Object.fromEntries(Object.entries(anteriores).filter(([id]) => !eliminados.has(Number(id))))
        guardarEnLocalStorage(CLAVE_TOKENS_REPORTES, actualizados)
        return actualizados
      })
      mostrarToast(`${resultados.length} reporte${resultados.length === 1 ? '' : 's'} eliminado${resultados.length === 1 ? '' : 's'}`)
    } catch {
      mostrarToast('No se pudieron borrar todos los reportes; volvé a intentar')
    }
    setActividadAbierta(false)
  }

  // Verificacion social sobre un reporte ajeno: "sigue ahi" / "ya no esta". El
  // backend rechaza votar el propio reporte (ver confirmar_reporte en main.py) y
  // acumula desmentidas para retirarlo antes de tiempo si la comunidad coincide
  // en que ya no aplica. Optimista sobre el contador local para que se sienta
  // instantaneo; si falla, no rompe nada -- el proximo cargarReportes corrige.
  const votarReporte = (reporteId, tipo) => {
    setReportes((prev) => prev.map((r) => (
      r.id === reporteId
        ? { ...r, confirmaciones: r.confirmaciones + (tipo === 'confirma' ? 1 : 0), desmentidas: r.desmentidas + (tipo === 'desmiente' ? 1 : 0) }
        : r
    )))
    fetch(`${API_URL}/reportes/${reporteId}/confirmar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ autor_id: autorId, tipo }),
    })
      .then((r) => { if (!r.ok) throw new Error(); return r.json() })
      .then(() => mostrarToast(tipo === 'confirma' ? 'Gracias, confirmado' : 'Gracias, avisamos que ya no está'))
      .catch(() => mostrarToast('No se pudo registrar el voto (¿backend caído?)'))
  }

  const abrirPanelRuta = () => {
    setRutaAbierta(true)
    setZonaSeleccionada(null)
    setActividadAbierta(false)
    setStatsAbierto(false)
    setCapasAbiertas(false)
    setRutasCalculadas([])
    setRutaError(null)
  }
  // function (no const arrow) para que quede hoisted: se usa en el listener
  // de Escape mas arriba en el archivo, antes de esta linea.
  function cerrarTodoRuta() {
    setRutaAbierta(false); setCampoActivo(null)
    setOrigenTexto(''); setDestinoTexto('')
    setOrigenPunto(null); setDestinoPunto(null)
    setRutasCalculadas([]); setRutaSeleccionada(0); setRutaError(null)
    setPasoActual(1)
  }
  const editarRuta = () => {
    setRutasCalculadas([]); setRutaError(null); setRutaAbierta(true)
  }
  const intercambiar = () => {
    setOrigenTexto(destinoTexto); setDestinoTexto(origenTexto)
    setOrigenPunto(destinoPunto); setDestinoPunto(origenPunto)
  }
  const usarMiUbicacionComoOrigen = () => {
    if (miUbicacion) {
      setOrigenPunto(miUbicacion); setOrigenTexto('Tu ubicación actual')
      return
    }
    setBuscandoUbicacion(true)
    navigator.geolocation?.getCurrentPosition(
      (pos) => {
        const p = { lat: pos.coords.latitude, lng: pos.coords.longitude }
        setMiUbicacion(p); setOrigenPunto(p); setOrigenTexto('Tu ubicación actual')
        setBuscandoUbicacion(false)
      },
      () => setBuscandoUbicacion(false)
    )
  }
  const marcarEnMapa = (campo) => setCampoActivo(campo === campoActivo ? null : campo)
  const elegirSugerencia = (campo, sug) => {
    if (campo === 'origen') { setOrigenTexto(sug.label); setOrigenPunto({ lat: sug.lat, lng: sug.lng }); sugOrigen.limpiar() }
    else { setDestinoTexto(sug.label); setDestinoPunto({ lat: sug.lat, lng: sug.lng }); sugDestino.limpiar() }
  }
  const clicMapa = useCallback((punto) => {
    if (campoActivo === 'origen') { setOrigenPunto(punto); setOrigenTexto('Punto marcado en el mapa'); setCampoActivo(null) }
    if (campoActivo === 'destino') { setDestinoPunto(punto); setDestinoTexto('Punto marcado en el mapa'); setCampoActivo(null) }
    // Para el reporte, a propósito NO se apaga campoActivo: mientras la
    // hojita de categorías sigue abierta, el usuario puede re-tocar el mapa
    // las veces que quiera para afinar el punto antes de confirmar.
    if (campoActivo === 'reporte') { setUbicacionReporte(punto); setVuelo({ ...punto, zoom: 15 }) }
  }, [campoActivo])

  // Tocar el mapa vacío marca destino directo (estilo Maps/Waze): reusa la
  // misma tarjeta "lugar elegido" + botón "Ir" que ya usa la búsqueda de
  // direcciones, así que no hace falta geocodificación inversa ni UI nueva
  // -- mismo rótulo que ya usa "marcar en el mapa" en el formulario de ruta
  // (Punto marcado en el mapa / Punto en el mapa), para que se lea como el
  // mismo gesto en los dos lugares. Deshabilitado mientras cualquier otro
  // flujo ya está usando el toque sobre el mapa (marcar origen/destino,
  // reportar) o mientras no tendría sentido (navegando, con "Opciones de
  // ruta" abierto).
  const tapRapidoHabilitado = !campoActivo && paso === 'idle' && !vistaNavegacion && rutasCalculadas.length === 0
  const tapMapaVacio = useCallback((punto) => {
    setLugarElegido({ ...punto, label: 'Punto en el mapa' })
  }, [])

  // Mismo motivo que clicMapa/manejarPaneoManual más arriba: referencia
  // estable para que MapaMotoSafe (en React.memo) no vuelva a renderizar el
  // mapa por cada tick de segundos de la topbar.
  const onMapaReady = useCallback((map) => { mapaRef.current = map; setMapaListo(true) }, [])
  const onTraficoEstadoCambio = useCallback((disponible) => setTraficoNoDisponible(!disponible), [])
  const onClickZonaMapa = useCallback((zona) => { setZonaSeleccionada(zona); setCapasAbiertas(false) }, [])

  const usarFavorito = (fav) => { setDestinoTexto(fav.texto); setDestinoPunto(fav.punto) }
  // Elegir un resultado de la búsqueda de arriba centra el mapa en ese lugar
  // (como cualquier buscador) y lo deja cargado como destino para "Trazar ruta",
  // sin abrir el panel de ruta que tapaba el mapa (SES-088).
  const buscarEnMapa = (sug) => {
    const nuevasRecientes = [sug, ...recientes.filter((r) => r.label !== sug.label)].slice(0, 5)
    setRecientes(nuevasRecientes)
    guardarEnLocalStorage(CLAVE_BUSQUEDAS_RECIENTES, nuevasRecientes)
    setLugarElegido(sug)
    setVuelo({ lat: sug.lat, lng: sug.lng })
    setBusqueda('')
    sugBusqueda.limpiar()
  }
  // "Ir": calcula la ruta al lugar elegido desde el origen actual, o desde tu
  // ubicación si el origen está vacío. Sin ubicación, abre el panel para elegir.
  const irAlLugar = () => {
    if (!lugarElegido) return
    const destino = { lat: lugarElegido.lat, lng: lugarElegido.lng }
    const origen = origenPunto || miUbicacion
    setDestinoTexto(lugarElegido.label)
    setDestinoPunto(destino)
    setLugarElegido(null)
    if (origen) {
      if (!origenPunto) { setOrigenPunto(origen); setOrigenTexto('Tu ubicación actual') }
      setRutaAbierta(false)
      calcularRuta(origen, destino)
    } else {
      abrirPanelRuta()
    }
  }
  const guardarFavorito = async (clave, label) => {
    let punto = destinoPunto
    if (!punto) {
      punto = await geocodificar(destinoTexto)
      if (!punto) { mostrarToast(`No pudimos ubicar "${destinoTexto}" para guardarlo`); return }
    }
    setFavoritos((prev) => ({ ...prev, [clave]: { texto: destinoTexto, punto } }))
    mostrarToast(`${label} guardado`)
  }

  // Un campo sin punto elegido no se resuelve a ciegas: se muestran las
  // opciones y el usuario toca la correcta. Antes se tomaba el primer
  // resultado, y con nombres ambiguos (Monte Grande existe en varios partidos)
  // la ruta arrancaba en el lugar equivocado (SES-084).
  const buscarRuta = () => {
    setRutaError(null)
    if (!origenTexto.trim() || !destinoTexto.trim()) { setRutaError('Completá origen y destino.'); return }
    if (!origenPunto || !destinoPunto) {
      if (!origenPunto) sugOrigen.buscar(origenTexto)
      if (!destinoPunto) sugDestino.buscar(destinoTexto)
      return
    }
    setRutaAbierta(false)
    calcularRuta(origenPunto, destinoPunto)
  }

  const calcularRuta = async (a, b) => {
    setRutaCargando(true); setRutaError(null)
    try {
      // Antes usaba el servidor de demo publico de OSRM (router.project-osrm.org),
      // pensado solo para pruebas, sin garantia de disponibilidad. Ahora usa el
      // backend propio, que a su vez llama a la Routing API de TomTom (misma
      // cuenta/key que la capa de trafico en vivo) -- ver backend/main.py
      // /rutas. Esto de paso resuelve el problema de que el trazado dibujado
      // (antes de OSRM) y el tiempo con trafico (de TomTom) podian venir de
      // rutas ligeramente distintas: ahora ambos salen del mismo calculo.
      const url = `${API_URL}/rutas?origen_lat=${a.lat}&origen_lng=${a.lng}&destino_lat=${b.lat}&destino_lng=${b.lng}&alternativas=2`
      const res = await fetch(url)
      if (!res.ok) throw new Error('El backend respondió con error')
      const data = await res.json()
      if (!Array.isArray(data) || data.length === 0) throw new Error('Sin ruta disponible')
      const rutas = data.map((r) => ({
        coords: r.coords,
        km: r.km,
        min: r.min,
        etaTrafico: r.eta_trafico
          ? {
              con_trafico_min: r.eta_trafico.con_trafico_min,
              sin_trafico_min: r.eta_trafico.sin_trafico_min,
              diferencia_min: r.eta_trafico.diferencia_min,
            }
          : null,
        pasos: (r.pasos || []).map((p) => ({
          tipo: p.tipo,
          modificador: p.modificador,
          calle: p.calle || 'la vía',
          lat: p.lat,
          lng: p.lng,
        })),
      }))
      setRutasCalculadas(rutas)
      setRutaSeleccionada(0)
      setPasoActual(1)
    } catch {
      setRutaError('No se pudo calcular la ruta (revisá tu conexión o probá de nuevo en un momento).')
    } finally {
      setRutaCargando(false)
    }
  }

  const misReportes = useMemo(
    () => reportes.filter((r) => r.esPropio || tokensReportes[String(r.id)]),
    [reportes, tokensReportes]
  )
  // F08: distinto de misReportes (solo vigentes, sale de GET /reportes). Esto
  // puede tener reportes vencidos o retirados por consenso, que GET /reportes
  // excluye a propósito porque el mapa público solo muestra lo vigente -- ver
  // POST /reportes/mios en el backend. Se pide solo cuando se abre el panel
  // (no hace falta tenerlo cargado todo el tiempo) y con la misma credencial
  // privada (id + delete_token) que ya se usa para borrar.
  const tengoReportesPropios = Object.keys(tokensReportes).length > 0
  const [historialReportes, setHistorialReportes] = useState([])
  const [cargandoHistorial, setCargandoHistorial] = useState(false)
  const [errorHistorial, setErrorHistorial] = useState(false)
  useEffect(() => {
    if (!actividadAbierta) return
    const ids = Object.keys(tokensReportes)
    if (ids.length === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setHistorialReportes([])
      return
    }
    const controller = new AbortController()
    setCargandoHistorial(true)
    setErrorHistorial(false)
    fetch(`${API_URL}/reportes/mios`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      body: JSON.stringify({ reportes: ids.map((id) => ({ id: Number(id), delete_token: tokensReportes[id] })) }),
    })
      .then((r) => { if (!r.ok) throw new Error('No se pudo cargar el historial'); return r.json() })
      .then((data) => setHistorialReportes(data.map((r) => ({
        id: r.id, lat: r.lat, lng: r.lng, categoria: r.categoria,
        creadoEn: r.creado_en, estado: r.estado,
      }))))
      .catch(() => { if (!controller.signal.aborted) setErrorHistorial(true) })
      .finally(() => { if (!controller.signal.aborted) setCargandoHistorial(false) })
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [actividadAbierta])

  const zonasAjustadas = useMemo(() => {
    return ZONAS_RIESGO.map((z) => ({ ...z, ajuste: calcularAjuste(z, reportes) }))
  }, [ZONAS_RIESGO, reportes])

  // La lógica de unificación de ejes de riesgo vive en utils/riesgoRuta.js
  // (funciones puras, testeadas aparte). nivel ya viene en la misma escala
  // ordinal en los tres casos (percentiles calculados dentro de cada
  // dataset), asi que sumar PESO_RIESGO entre tipos es valido.
  const zonasInseguridadUnificadas = useMemo(
    // El ajuste por franja horaria ya viene aplicado desde el backend (ver
    // ajustado_por_horario/motivo_ajuste_horario en cada hotspot de
    // /hotspots-inseguridad); no depende de horaActual de este lado.
    () => unificarZonasInseguridad(inseguridadGeneral, inseguridadMoto),
    [inseguridadGeneral, inseguridadMoto]
  )

  const zonasRiesgoTodas = useMemo(
    () => unificarZonasRiesgo(zonasAjustadas, zonasInseguridadUnificadas),
    [zonasAjustadas, zonasInseguridadUnificadas]
  )

  useEffect(() => {
    if (!modoViaje || !miUbicacion || zonasRiesgoTodas.length === 0) return
    const candidatas = zonasRiesgoTodas.filter(
      (z) => (z.nivel === 'alto' || z.nivel === 'critico')
        && !zonasAlertadas.has(z.id)
        && distanciaKm(miUbicacion, z) <= UMBRAL_ALERTA_KM
    )
    if (candidatas.length > 0) {
      const zona = candidatas[0]
      // Reaccion a un cambio de posicion GPS (sistema externo), no estado derivado.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setAlertaViaje(zona)
      setZonasAlertadas((prev) => new Set(prev).add(zona.id))
      if (navigator.vibrate) navigator.vibrate(zona.tipoRiesgo === 'inseguridad' ? [200, 80, 200, 80, 200] : [250, 100, 250])
      reproducirBeep()
      setTimeout(() => setAlertaViaje(null), 6000)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [miUbicacion, modoViaje, zonasRiesgoTodas])

  // Alerta de proximidad a un reporte de ROBO reciente (evento puntual, no zona
  // de riesgo historico -- ver CATEGORIAS_ALERTA_PROXIMIDAD). Distinta del efecto
  // de arriba: esa alerta contra los hotspots/corredores precalculados, esta
  // contra lo que otro usuario reporto hace minutos. Solo dispara una vez por
  // reporte (reportesAlertados), y solo si sigue "reciente" segun
  // MINUTOS_ALERTA_REPORTE_RECIENTE, no solo vigente en el mapa.
  useEffect(() => {
    if (!modoViaje || !miUbicacion || reportes.length === 0) return
    const ahoraMs = Date.now()
    const candidatos = reportes.filter((r) => {
      if (!CATEGORIAS_ALERTA_PROXIMIDAD.includes(r.categoria)) return false
      if (reportesAlertados.has(r.id)) return false
      const edadMin = (ahoraMs - new Date(r.creadoEn).getTime()) / 60000
      if (edadMin > MINUTOS_ALERTA_REPORTE_RECIENTE) return false
      return distanciaKm(miUbicacion, r) <= RADIO_ALERTA_REPORTE_KM
    })
    if (candidatos.length > 0) {
      const rep = candidatos[0]
      const edadMin = Math.max(1, Math.round((ahoraMs - new Date(rep.creadoEn).getTime()) / 60000))
      const cat = CATEGORIAS_REPORTE.find((c) => c.id === rep.categoria)
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setAlertaReporte({ label: cat?.label || rep.categoria, minutos: edadMin })
      setReportesAlertados((prev) => new Set(prev).add(rep.id))
      if (navigator.vibrate) navigator.vibrate([200, 80, 200, 80, 200])
      reproducirBeep()
      setTimeout(() => setAlertaReporte(null), 8000)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [miUbicacion, modoViaje, reportes])

  useEffect(() => {
    if (!modoViaje || !miUbicacion || rutasCalculadas.length === 0) return
    const pasos = rutasCalculadas[rutaSeleccionada]?.pasos || []
    if (pasoActual >= pasos.length) return
    // Si el GPS se saltó una maniobra (curva rápida, saltos de señal), el paso
    // activo quedaba trabado atrás y la tarjeta mostraba distancias absurdas
    // (58,6 km para una maniobra a 130 m, SES-087). Ahora se avanza al último
    // paso de los próximos cinco que esté a menos de 30 m. Nunca retrocede.
    const nuevoPaso = siguientePaso(miUbicacion, pasos, pasoActual)
    if (nuevoPaso > pasoActual) {
      // Reaccion a un cambio de posicion GPS (sistema externo), no estado derivado.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPasoActual(nuevoPaso)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [miUbicacion, modoViaje])

  // Llegada a destino: antes la tarjeta de maniobra llegaba a mostrar "Llegaste
  // a destino" (texto del último paso, tipo 'arrive') y se quedaba así -- nada
  // apagaba el viaje. pasoActual llega al último índice de pasos (ver
  // siguientePaso) apenas se entra en su radio de maniobra, así que acá se
  // exige además estar cerca de verdad antes de cortar.
  //
  // "Cerca" se mide IGUAL que la tarjeta (ver distanciaManiobraKm): recorrido
  // sobre la polilínea de la ruta, no línea recta GPS-a-punto. Probado en
  // sitio real (SES-103): con origen y destino en el mismo lugar, la ruta mide
  // ~0 km y la tarjeta ya decía "0 m", pero la distancia en línea recta entre
  // el GPS real y el punto de "arrive" de TomTom (la dirección geocodificada,
  // no donde estás parado) seguía sin entrar en el radio -- medir en línea
  // recta nunca iba a cortar en ese caso aunque la ruta ya estuviera recorrida
  // entera. Con el mismo criterio que ve el usuario en pantalla, los dos
  // coinciden siempre.
  useEffect(() => {
    if (!modoViaje || !miUbicacion || rutasCalculadas.length === 0) return
    const ruta = rutasCalculadas[rutaSeleccionada]
    const pasos = ruta?.pasos || []
    const ultimoPaso = pasos[pasos.length - 1]
    if (!ultimoPaso || ultimoPaso.tipo !== 'arrive' || pasoActual < pasos.length - 1) return
    const faltanKm = ruta?.coords
      ? Math.max(0, calcularProgresoRuta(ultimoPaso, ruta.coords).distanciaRecorridaKm
                     - calcularProgresoRuta(miUbicacion, ruta.coords).distanciaRecorridaKm)
      : distanciaKm(miUbicacion, ultimoPaso)
    if (faltanKm > RADIO_LLEGADA_KM) return
    // Reaccion a un cambio de posicion GPS (sistema externo), no estado derivado.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    desactivarModoViaje('Llegaste a destino')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [miUbicacion, modoViaje, pasoActual])

  // --- detección de desvío + reroute automático -----------------------------
  // Hasta ahora, si te equivocabas de calle en plena navegación, la ruta se
  // quedaba "colgada" con instrucciones que ya no aplicaban -- había que
  // cortar el viaje y trazar todo de nuevo a mano. Waze/Maps recalculan
  // solos; esto hace lo mismo, con la ruta ya calculada por el backend
  // (misma función que arma la ruta inicial) contra el mismo destino.
  const desviosSeguidosRef = useRef(0)
  const rerouteEnCursoRef = useRef(false)
  const ultimoRerouteTsRef = useRef(0)
  useEffect(() => {
    if (!modoViaje) { desviosSeguidosRef.current = 0; ultimoRerouteTsRef.current = 0; return }
    if (!miUbicacion || !destinoPunto || rutasCalculadas.length === 0 || rerouteEnCursoRef.current) return
    const ruta = rutasCalculadas[rutaSeleccionada]
    if (!ruta?.coords) return
    const distancia = distanciaAPolilinea(miUbicacion, ruta.coords)
    if (distancia > UMBRAL_DESVIO_RUTA_KM) {
      desviosSeguidosRef.current += 1
    } else {
      desviosSeguidosRef.current = 0
    }
    if (desviosSeguidosRef.current >= DESVIOS_SEGUIDOS_PARA_RECALCULAR) {
      desviosSeguidosRef.current = 0
      // Sin este freno, si la ruta recalculada sigue sin coincidir con la
      // posición real, el ciclo se repetía cada pocos segundos (ver
      // COOLDOWN_RECALCULO_MS más arriba).
      if (Date.now() - ultimoRerouteTsRef.current < COOLDOWN_RECALCULO_MS) return
      ultimoRerouteTsRef.current = Date.now()
      rerouteEnCursoRef.current = true
      mostrarToast('Te desviaste -- recalculando ruta...')
      calcularRuta(miUbicacion, destinoPunto).finally(() => { rerouteEnCursoRef.current = false })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [miUbicacion, modoViaje])

  // useMemo acá no es solo optimización: MapaMotoSafe reconstruye la capa
  // entera de clusters cuando cambia la REFERENCIA de este array (a
  // diferencia de react-leaflet, que reconciliaba por `key` sin importar
  // la identidad del array). Sin memoizar, el re-render cada 1s de
  // `segundos` (useSegundosDesde) generaba un array nuevo por referencia
  // en cada tick y tiraba abajo y reconstruía la capa de siniestros todo
  // el tiempo, así que las burbujas nunca llegaban a verse en pantalla.
  const zonasFiltradas = useMemo(
    () => zonasAjustadas.filter(
      (z) => nivelesActivos.has(z.ajuste.nivel) && z.nombre.toLowerCase().includes(busqueda.toLowerCase())
    ),
    [zonasAjustadas, nivelesActivos, busqueda]
  )
  const criticosVisibles = zonasFiltradas.filter((z) => z.ajuste.nivel === 'critico').length

  useEffect(() => {
    if (busqueda.trim().length > 2 && zonasFiltradas.length === 1) {
      const z = zonasFiltradas[0]
      // Efecto disparado por texto tipeado por el usuario, con su propio cleanup.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setVuelo({ lat: z.lat, lng: z.lng, zoom: 15 })
      setZonaResaltada(z.id)
      const t = setTimeout(() => setZonaResaltada(null), 3000)
      return () => clearTimeout(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busqueda])

  const zonasCruzadasPorRuta = useMemo(
    () => calcularZonasCruzadasPorRuta(rutasCalculadas, zonasRiesgoTodas, UMBRAL_CRUCE_KM),
    [rutasCalculadas, zonasRiesgoTodas]
  )

  const coberturaPorRuta = useMemo(
    () => calcularCoberturaRegistrada(rutasCalculadas, zonasRiesgoTodas, UMBRAL_CRUCE_KM),
    [rutasCalculadas, zonasRiesgoTodas]
  )
  const coberturaPorFuente = useMemo(
    () => calcularCoberturaPorFuente(rutasCalculadas, zonasRiesgoTodas, UMBRAL_CRUCE_KM),
    [rutasCalculadas, zonasRiesgoTodas]
  )
  const zonasCruzadasActual = useMemo(
    () => zonasCruzadasPorRuta[rutaSeleccionada] || [],
    [zonasCruzadasPorRuta, rutaSeleccionada]
  )
  // Solo los ids: es lo unico que necesita MapaMotoSafe para resaltar el
  // borde de una zona cruzada por la ruta seleccionada.
  const zonasCruzadasIds = useMemo(
    () => new Set(zonasCruzadasActual.map((z) => z.id)),
    [zonasCruzadasActual]
  )

  const zonasCruzadasOrdenadas = useMemo(() => {
    return [...zonasCruzadasActual].sort(
      (a, b) => ORDEN_NIVELES.indexOf(b.nivel) - ORDEN_NIVELES.indexOf(a.nivel)
    )
  }, [zonasCruzadasActual])

  const rutasConScore = useMemo(
    () => calcularRutasConScore(rutasCalculadas, zonasCruzadasPorRuta, coberturaPorRuta, coberturaPorFuente),
    [rutasCalculadas, zonasCruzadasPorRuta, coberturaPorRuta, coberturaPorFuente]
  )

  const idxMasRapida = useMemo(() => {
    if (rutasConScore.length === 0) return 0
    return rutasConScore.reduce((best, r, i) => (r.min < rutasConScore[best].min ? i : best), 0)
  }, [rutasConScore])

  const idxMasSegura = useMemo(() => {
    if (rutasConScore.length === 0) return 0
    const comparables = rutasConScore
      .map((ruta, indice) => ({ ruta, indice }))
      .filter(({ ruta }) => ruta.coberturaRegistrada >= 0.6)
    if (!comparables.length) return idxMasRapida
    return comparables.reduce((best, actual) => (actual.ruta.riesgo < best.ruta.riesgo ? actual : best)).indice
  }, [rutasConScore, idxMasRapida])

  const idxEquilibrada = useMemo(() => {
    if (rutasConScore.length < 3) return idxMasRapida
    const tiempos = rutasConScore.map((r) => r.min)
    const riesgos = rutasConScore.map((r) => r.riesgo)
    const minT = Math.min(...tiempos), maxT = Math.max(...tiempos)
    const minR = Math.min(...riesgos), maxR = Math.max(...riesgos)
    const normalizado = rutasConScore.map((r) => {
      const t = maxT > minT ? (r.min - minT) / (maxT - minT) : 0
      const rk = maxR > minR ? (r.riesgo - minR) / (maxR - minR) : 0
      return t + rk
    })
    return normalizado.indexOf(Math.min(...normalizado))
  }, [rutasConScore, idxMasRapida])

  // Progreso sobre la ruta seleccionada mientras se está navegando -- de acá
  // sale la barra de "quedan X km / Y min, llegás a las Z" (ver
  // .nav-resumen-mini más abajo). Antes la app solo sabía el km/min TOTAL de
  // la ruta calculada al inicio; esto lo recalcula contra la posición GPS
  // actual en cada fix.
  const progresoRuta = useMemo(() => {
    if (!modoViaje || !miUbicacion) return null
    const ruta = rutasConScore[rutaSeleccionada]
    if (!ruta?.coords) return null
    return calcularProgresoRuta(miUbicacion, ruta.coords)
  }, [modoViaje, miUbicacion, rutasConScore, rutaSeleccionada])

  // Distancia a la próxima maniobra medida POR LA RUTA (no en línea recta):
  // recorrido hasta el paso menos el recorrido actual, sobre la polilínea (SES-094).
  // Si no hay geometría, cae a la distancia en línea recta.
  const distanciaManiobraKm = (paso) => {
    const ruta = rutasConScore[rutaSeleccionada]
    if (!progresoRuta || !ruta?.coords || !paso) return distanciaKm(miUbicacion, paso)
    const recorridoPaso = calcularProgresoRuta(paso, ruta.coords).distanciaRecorridaKm
    return Math.max(0, recorridoPaso - progresoRuta.distanciaRecorridaKm)
  }
  const etaInfo = useMemo(() => {
    if (!progresoRuta) return null
    const ruta = rutasConScore[rutaSeleccionada]
    if (!ruta) return null
    // Con velocidad GPS real disponible, el tiempo restante sale del ritmo
    // actual (más fiel reflejando tráfico real). Pero dividir la distancia
    // que falta por una velocidad casi nula (parado en un semáforo, GPS
    // ruidoso probando la app sin moverse) da un ETA absurdo -- "1989 min"
    // en vez de "52 min" con apenas 2 km/h de velocidad instantánea, el caso
    // real que motivó este piso. Por debajo de VELOCIDAD_MIN_PARA_RUMBO_GPS
    // (mismo umbral que ya se usa para no confiar en el rumbo a esa
    // velocidad) se cae al reparto proporcional del tiempo total de la ruta,
    // una aproximación razonable para "estoy parado un momento", no exacta.
    const velocidadConfiableParaEta = velocidadActual != null && velocidadActual >= VELOCIDAD_MIN_PARA_ETA_GPS
    const minRestante = velocidadConfiableParaEta
      ? (progresoRuta.distanciaRestanteKm / (velocidadActual * 3.6)) * 60
      : ruta.min * (1 - progresoRuta.fraccionRecorrida)
    const llegada = new Date(Date.now() + minRestante * 60000)
    return {
      distanciaRestanteKm: progresoRuta.distanciaRestanteKm,
      minRestante: Math.max(0, Math.round(minRestante)),
      horaLlegada: llegada.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
    }
  }, [progresoRuta, rutasConScore, rutaSeleccionada, velocidadActual])

  const corredoresFiltrados = useMemo(
    () => corredores.filter((c) => nivelesActivos.has(c.nivel_riesgo)),
    [corredores, nivelesActivos]
  )

  const inseguridadGeneralFiltrada = useMemo(
    () => inseguridadGeneral.filter((h) => nivelesActivos.has(h.nivel_riesgo)),
    [inseguridadGeneral, nivelesActivos]
  )
  const inseguridadMotoFiltrada = useMemo(
    () => inseguridadMoto.filter((h) => nivelesActivos.has(h.nivel_riesgo)),
    [inseguridadMoto, nivelesActivos]
  )

  const conteos = Object.keys(NIVELES).reduce((acc, n) => {
    acc[n] = capaMapa === 'corredores'
      ? corredores.filter((c) => c.nivel_riesgo === n).length
      : zonasAjustadas.filter((z) => z.ajuste.nivel === n).length
    return acc
  }, {})

  const fuenteInseguridad = capaInseguridad === 'moto' ? inseguridadMoto : inseguridadGeneral
  const conteosInseguridad = Object.keys(NIVELES).reduce((acc, n) => {
    acc[n] = fuenteInseguridad.filter((h) => h.nivel_riesgo === n).length
    return acc
  }, {})

  const indiceRiesgo = useMemo(() => {
    if (zonasAjustadas.length === 0) return 0
    const total = zonasAjustadas.reduce((acc, z) => acc + PESO_RIESGO[z.ajuste.nivel], 0)
    const maximoPosible = zonasAjustadas.length * PESO_RIESGO.critico
    return Math.round((total / maximoPosible) * 100)
  }, [zonasAjustadas])

  const totalSiniestros = useMemo(() => zonasAjustadas.reduce((acc, z) => acc + (z.cantidad || 0), 0), [zonasAjustadas])

  const top5Peligrosas = useMemo(() => {
    return [...zonasAjustadas].sort((a, b) => (b.cantidad || 0) - (a.cantidad || 0)).slice(0, 5)
  }, [zonasAjustadas])

  const hayFiltrosApagados = nivelesActivos.size < Object.keys(NIVELES).length
  // "Opciones de ruta" abierto (ver el panel .ruta-resumen más abajo): mismo
  // booleano para esconder la leyenda mientras se muestra, así los dos no
  // compiten por el mismo rincón de la pantalla en celular.
  const mostrandoOpcionesRuta = rutasCalculadas.length > 0 && !modoViaje
  // Animación de salida del panel de ruta (SES-115): la leyenda y el FAB de
  // reportar esperan a que panelRuta.montado baje a false (recién ahí
  // "mostrandoOpcionesRuta" realmente liberó el rincón de la pantalla) en
  // vez de reaccionar al booleano crudo -- si no, reaparecerían de golpe
  // mientras el panel de ruta todavía se está desvaneciendo encima.
  const panelRuta = usePanelSaliente(mostrandoOpcionesRuta)
  const detalleVisible = rutasCalculadas.length === 0 && !rutaAbierta && !!zonaSeleccionada
  const panelDetalle = usePanelSaliente(detalleVisible)
  if (zonaSeleccionada && zonaSeleccionada !== zonaMostrada) setZonaMostrada(zonaSeleccionada)
  const mostrarAlerta = criticosVisibles > 0 && criticosVisibles <= 5 && misReportes.length === 0 && rutasCalculadas.length === 0
  let textoTopbar
  // Texto corto a propósito: con "· siguiendo tu ubicación" el pill se
  // ensanchaba tanto que dejaba de leerse como una insignia en la esquina
  // (arriba a la derecha) y competía con el cartel de navegación, centrado,
  // por el mismo espacio -- Rodo lo vio en captura real. El estado de
  // "dejó de seguir" ya tiene su propio aviso (el botón de recentrar que
  // aparece), así que no hace falta repetirlo acá.
  // Mismo criterio que "Modo Viaje" más arriba: el pill de estado vive en la
  // misma fila que los íconos de tema/capas/clima, y su ancho depende del
  // texto -- con "740 zonas registradas · hace 45s" no entraba y el topbar
  // pasaba a 2 (o 3) líneas, corriendo todo lo de abajo y rompiendo la
  // simetría con la marca de la izquierda (Rodo lo vio en captura real: con
  // un reporte, texto corto, quedaba prolijo en una sola fila; al borrarlo,
  // volvía el texto largo y se desarmaba). Se acorta cada variante para que
  // el pill entre en una sola línea en el caso común, en vez de perseguir el
  // problema por breakpoint cada vez que cambia el estado que se muestra.
  if (modoViaje) textoTopbar = 'Modo Viaje'
  else if (rutasCalculadas.length > 0) textoTopbar = `Ruta: ${rutasCalculadas[rutaSeleccionada].km} km · ${rutasCalculadas[rutaSeleccionada].min} min`
  else if (cargandoHotspots) textoTopbar = 'Conectando...'
  else if (misReportes.length > 0) textoTopbar = `${misReportes.length} reporte${misReportes.length > 1 ? 's' : ''} tuyo${misReportes.length > 1 ? 's' : ''}`
  else if (mostrarAlerta) textoTopbar = `${criticosVisibles} zona${criticosVisibles > 1 ? 's' : ''} crítica${criticosVisibles > 1 ? 's' : ''}`
  else textoTopbar = `${zonasFiltradas.length} zonas`

  const climaInfo = iconoClima(clima)
  const ultimaConsultaCapas = Object.entries(actualizacionesCapas)
    .filter(([, momento]) => momento)
    .map(([capa, momento]) => `${({ corredores: 'corredores', inseguridadGeneral: 'inseguridad general', inseguridadMoto: 'inseguridad con moto' }[capa] || capa)} ${new Date(momento).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}`)
    .join(' · ')

  // Cuando la capa de inseguridad esta prendida, el fondo (clusters/calor/
  // corredores) se atenua para que la capa recien activada quede como
  // protagonista en vez de competir en igualdad de jerarquia visual.
  // Durante la navegación con vista inclinada, el mapa de fondo (heatmap,
  // corredores) se atenúa fuerte -- no se apaga del todo para no perder la
  // referencia de que ahí sigue habiendo zonas de riesgo, pero deja de
  // competir visualmente con la ruta y el próximo giro, que es lo único que
  // importa mientras se está manejando. Se multiplica en vez de reemplazar
  // para no perder el atenuado ya existente entre capas (siniestros vs.
  // inseguridad activa).
  const atenuarFondo = (capaInseguridad !== 'apagado' ? 0.4 : 1) * (vistaNavegacion ? 0.1 : 1)

  return (
    <div className="app">
      <LoadingScreen visible={!primeraVezListo} />
      {mostrarOnboarding && primeraVezListo && <Onboarding onCerrar={cerrarOnboarding} />}

      <header className="topbar" ref={topbarRef}>
        <div className="brand">
          <span className="brand-dot" />
          <span className="brand-name">MotoSafe</span>
          <span className="brand-badge">GBA</span>
        </div>
        <div className="topbar-right">
          {/* SES-120: separado en dos filas fijas (iconos+clima arriba,
              estado abajo) en vez de depender de que el flex-wrap de
              celular decida solo cuándo no entra. El pill de estado
              (textoTopbar) cambia mucho de largo según el caso -- "3
              zonas", "2 zonas críticas", "Ruta: 1.6 km · 5 min", "Modo
              Viaje" -- y con todo en una sola fila de flex, a veces entraba
              y a veces no, asi que la topbar cambiaba de alto de forma
              impredecible segun el texto (eso es lo que se vio como "a
              veces se agranda todo", no una medida puntual mal puesta).
              Fijando el pill siempre en su propia fila, el alto de la
              topbar deja de depender del contenido. */}
          <div className="topbar-right-iconos">
            {/* En navegación se saca todo lo que no es la información de viaje
                en sí -- tema, capas y clima son decisiones de exploración, no
                algo que se toque manejando. Menos chrome arriba también le
                deja más aire vertical a la tarjeta de próximo giro. */}
            {!vistaNavegacion && <ThemeToggle tema={tema} onCambiar={toggleTema} />}
            {!vistaNavegacion && (
              <button
                className={`capa-toggle ${capaInseguridad !== 'apagado' || capaMapa !== 'hexagonos' ? 'capas-con-cambios' : ''}`}
                onClick={() => setCapasAbiertas((v) => !v)}
                aria-label="Capas del mapa"
                aria-expanded={capasAbiertas}
                title="Capas del mapa"
              >
                <Layers size={15} />
              </button>
            )}
            {!vistaNavegacion && (
              <button
                className="capa-toggle"
                onClick={() => setPortalActividadAbierto(true)}
                aria-label="Actividad: prensa y reportes de la ciudad"
                title="Actividad"
              >
                <Newspaper size={15} />
              </button>
            )}
            {clima && !vistaNavegacion && (
              <div
                className="clima-badge"
                title={`${climaInfo.label}: el nivel de riesgo que ves ya tiene en cuenta este clima`}
              >
                <climaInfo.Icon size={13} /> {Math.round(clima.temperatura)}°C
              </div>
            )}
          </div>
          <div
            className={`topbar-status ${mostrarAlerta ? 'alerta' : ''} ${modoViaje ? 'viaje' : ''} ${tengoReportesPropios ? 'clickeable' : ''}`}
            onClick={() => { if (tengoReportesPropios) { setActividadAbierta((v) => !v); setCapasAbiertas(false) } }}
          >
            <span className="status-dot" />
            {textoTopbar}
          </div>
        </div>
      </header>

      {panelCapas.montado && (
        <CapasPanel
          saliendo={panelCapas.saliendo}
          coberturaPrensa={coberturaCapas?.prensa}
          horaActual={horaActual}
          capaMapa={capaMapa}
          onCambiarCapaMapa={setCapaMapa}
          capaInseguridad={capaInseguridad}
          onCambiarCapaInseguridad={setCapaInseguridad}
          capaTrafico={capaTrafico}
          onCambiarCapaTrafico={(v) => {
            if (v && traficoNoDisponible) { mostrarToast('Tráfico en vivo no disponible ahora'); return }
            setCapaTrafico(v)
          }}
          capaPrensa={capaPrensa}
          onCambiarCapaPrensa={setCapaPrensa}
          filtroPrensa={filtroPrensa}
          onCambiarFiltroPrensa={setFiltroPrensa}
          cantidadReportesPrensa={reportesPrensa.length}
          cantidadReportesPrensaFiltrados={reportesPrensaFiltrados.length}
          onCerrar={() => setCapasAbiertas(false)}
        />
      )}

      {toast && <div className="toast panel-enter">{toast}</div>}

      {modoViaje && rutasCalculadas.length > 0 && rutasCalculadas[rutaSeleccionada]?.pasos?.[pasoActual] && (() => {
        const pasos = rutasCalculadas[rutaSeleccionada].pasos
        const pasoActivo = pasos[pasoActual]
        const pasoSiguiente = pasos[pasoActual + 1]
        const ManiobraIcon = iconoManiobra(pasoActivo)
        return (
          <div className="navegacion-panel panel-enter">
            <span className="navegacion-icono-chip"><ManiobraIcon size={26} /></span>
            <div className="navegacion-texto">
              {miUbicacion && (
                <span className="navegacion-distancia">
                  {formatearDistancia(distanciaManiobraKm(pasoActivo))}
                </span>
              )}
              <strong>{textoManiobra(pasoActivo)}</strong>
              {/* Preview del giro siguiente, más chico -- ayuda en cruces
                  seguidos a no quedar "ciego" un paso adelante, que era el
                  caso hasta ahora (solo se veía el giro inmediato). Separado
                  del resto con su propio borde superior en vez de solo ser
                  texto más chico, para que se lea como un dato secundario y
                  no como continuación del mismo mensaje. */}
              {pasoSiguiente && (
                <div className="navegacion-luego">
                  <span className="navegacion-luego-etiqueta">Luego</span>
                  <CornerDownRight size={13} />
                  <span className="navegacion-luego-texto">{textoManiobra(pasoSiguiente)}</span>
                </div>
              )}
            </div>
          </div>
        )
      })()}

      {alertaViaje && (
        <div className={`alerta-viaje panel-enter ${alertaViaje.nivel === 'critico' ? 'critica' : 'alta'}`}>
          <span className="alerta-viaje-cabecera">
            {alertaViaje.tipoRiesgo === 'inseguridad' ? <ShieldAlert size={16} /> : <Siren size={16} />}
            {' '}Te acercás a una zona de {alertaViaje.tipoRiesgo === 'inseguridad' ? 'inseguridad' : 'riesgo de siniestro'} {NIVELES[alertaViaje.nivel].label.toUpperCase()}
          </span>
          <span className="alerta-viaje-detalle">{alertaViaje.nombre}</span>
        </div>
      )}

      {alertaReporte && (
        <div className="alerta-viaje panel-enter critica alerta-reporte">
          <span className="alerta-viaje-cabecera">
            <Siren size={16} />
            {' '}{alertaReporte.label} reportado hace {alertaReporte.minutos} min
          </span>
          <span className="alerta-viaje-detalle">Cerca de tu posición actual</span>
        </div>
      )}

      {backendError && (
        <div className="ruta-banner ruta-banner-error panel-enter backend-banner" role="alert">
          <WifiOff size={14} /> Sin conexión con el backend. Reintentando cada 5s.
          <button onClick={cargarHotspots}>Reintentar ahora</button>
        </div>
      )}
      {!backendError && Object.values(erroresCapas).some(Boolean) && (
        <div className="ruta-banner ruta-banner-error panel-enter backend-banner" role="status" aria-live="polite">
          <WifiOff size={14} /> No se actualizaron: {Object.entries(erroresCapas).filter(([, fallo]) => fallo).map(([capa]) => ({ corredores: 'corredores', inseguridadGeneral: 'inseguridad general', inseguridadMoto: 'inseguridad con moto' }[capa] || capa)).join(', ')}. Se mantiene la última información disponible.
          {ultimaConsultaCapas && <span className="backend-banner-fecha">Última consulta: {ultimaConsultaCapas}</span>}
          <button onClick={() => setRecargaCapas((v) => v + 1)}>Reintentar capas</button>
        </div>
      )}
      {/* SES-112: con el backend caído, activar tráfico quedaba sin ningún
          aviso -- las fichas de calle (tiles PNG de TomTom vía backend)
          fallan en silencio, MapLibre no dispara un error que el usuario vea,
          y el panel de capas seguía marcando la opción como activa. El toast
          de App.jsx solo avisaba en un SEGUNDO intento de activarla (si
          traficoNoDisponible ya era true). Este banner cubre el primer
          intento, con la misma fuente/reintento que el resto de las capas. */}
      {!backendError && capaTrafico && traficoNoDisponible && (
        <div className="ruta-banner ruta-banner-error panel-enter backend-banner" role="status" aria-live="polite">
          <WifiOff size={14} /> Tráfico en vivo (TomTom) no disponible ahora. Se mantiene el mapa sin esa capa.
          <button onClick={() => { setCapaTrafico(false); setTimeout(() => setCapaTrafico(true), 50) }}>Reintentar tráfico</button>
        </div>
      )}


      {panelActividad.montado && tengoReportesPropios && (
        <div className={`actividad-panel panel-enter hazard-edge ${panelActividad.saliendo ? 'panel-exit' : ''}`}>
          <div className="actividad-header">
            <span className="cercanas-title">Actividad reciente</span>
            <button className="detalle-cerrar" onClick={() => setActividadAbierta(false)} aria-label="Cerrar panel de actividad"><X size={14} /></button>
          </div>
          {/* F08: mientras el historial no cargó (o si falló), se ve lo
              vigente -- que ya se tenía antes, sin esperar a la red -- para
              no mostrar el panel vacío. Una vez que historialReportes trae
              algo, manda eso: incluye además lo vencido y lo retirado por
              consenso, que misReportes nunca tiene porque sale de GET
              /reportes (solo vigente, a propósito). */}
          {cargandoHistorial && historialReportes.length === 0 && <p className="actividad-estado-carga">Cargando historial…</p>}
          {errorHistorial && <p className="actividad-estado-carga">No se pudo cargar el historial completo; se muestra lo vigente.</p>}
          {(historialReportes.length > 0
            ? historialReportes
            : misReportes.map((r) => ({ id: r.id, lat: r.lat, lng: r.lng, categoria: r.categoria, creadoEn: r.creadoEn, estado: 'vigente' }))
          ).map((rep) => {
            const cat = CATEGORIAS_REPORTE.find((c) => c.id === rep.categoria)
            const textoEstado = rep.estado === 'vencido' ? `Venció · ${formatearAntiguedad(rep.creadoEn, horaActual)}`
              : rep.estado === 'desmentido' ? `Retirado por la comunidad · ${formatearAntiguedad(rep.creadoEn, horaActual)}`
              : `Vigente · ${formatearAntiguedad(rep.creadoEn, horaActual)}`
            return (
              <button
                key={rep.id}
                className={`actividad-item ${rep.estado !== 'vigente' ? 'actividad-item-historico' : ''}`}
                onClick={() => { setVuelo({ lat: rep.lat, lng: rep.lng, zoom: 16 }); setActividadAbierta(false) }}
              >
                <span className="actividad-icon">{cat?.Icon && <cat.Icon size={15} />}</span>
                <span className="actividad-texto">
                  <span className="actividad-label">{cat?.label}</span>
                  <span className="actividad-hora">{textoEstado}</span>
                </span>
              </button>
            )
          })}
          {misReportes.length > 0 && <button className="actividad-borrar" onClick={borrarReportes}>Borrar mis reportes</button>}
        </div>
      )}

      {panelStats.montado && (
        <div className={`stats-panel panel-enter hazard-edge ${panelStats.saliendo ? 'panel-exit' : ''}`}>
          <div className="stats-header">
            <span className="cercanas-title">Estadísticas de la Ciudad</span>
            <button className="detalle-cerrar" onClick={() => setStatsAbierto(false)} aria-label="Cerrar estadísticas"><X size={14} /></button>
          </div>
          <p className="stats-subtitulo">{totalSiniestros.toLocaleString('es-AR')} siniestros históricos en {zonasAjustadas.length} zonas (CABA)</p>
          <div className="stats-indice">
            <span className="stats-indice-numero" style={{ color: indiceRiesgo >= 60 ? '#FF3B3B' : indiceRiesgo >= 35 ? '#FF8C42' : '#3DDC84' }}>{indiceRiesgo}</span>
            <span className="stats-indice-label">Índice de riesgo del mapa visible (0-100)</span>
          </div>
          <div className="stats-barras">
            {Object.entries(NIVELES).map(([key, val]) => (
              <div className="stats-barra-fila" key={key}>
                <span className="stats-barra-label">{val.label}</span>
                <div className="stats-barra-track">
                  <div className="stats-barra-fill" style={{ width: `${zonasAjustadas.length ? (conteos[key] / zonasAjustadas.length) * 100 : 0}%`, background: val.color }} />
                </div>
                <span className="stats-barra-num">{conteos[key]}</span>
              </div>
            ))}
          </div>
          <span className="stats-top-titulo">Top 5 zonas más siniestradas</span>
          {top5Peligrosas.map((z, i) => (
            <button key={z.id} className="stats-top-item" onClick={() => { setVuelo({ lat: z.lat, lng: z.lng, zoom: 15 }); setStatsAbierto(false) }}>
              <span className="stats-top-rank">#{i + 1}</span>
              <span className="cercanas-dot" style={{ background: NIVELES[z.ajuste.nivel].color }} />
              <span className="cercanas-nombre">{z.nombre}</span>
            </button>
          ))}
        </div>
      )}

      {panelPortalActividad.montado && (
        <ActividadPortal
          saliendo={panelPortalActividad.saliendo}
          reportesPrensa={reportesPrensa}
          reportes={reportes}
          horaActual={horaActual}
          onCerrar={() => setPortalActividadAbierto(false)}
          onVerEnMapa={(punto) => { setVuelo({ ...punto, zoom: 16 }); setPortalActividadAbierto(false) }}
          onAbrirLector={setLectorNota}
        />
      )}

      {/* Lector de notas: pedido explícito de que NO tape toda la app --
          panel flotante (como ruta-resumen/capas-panel), no pantalla
          completa. Se abre desde acá (portal) y desde los marcadores de
          prensa del mapa (MapaMotoSafe -> onAbrirLector), por eso vive al
          nivel de App y no adentro de ActividadPortal. */}
      {panelLectorNota.montado && lectorNotaMostrada && (
        <>
        <div className={`lector-nota-scrim ${panelLectorNota.saliendo ? 'panel-exit' : ''}`} onClick={() => setLectorNota(null)} />
        <div
          className={`lector-nota panel-enter ${panelLectorNota.saliendo ? 'panel-exit' : ''}`}
          role="dialog"
          aria-label={`Leyendo: ${lectorNotaMostrada.titulo}`}
          style={{ height: `${alturaLector}vh` }}
        >
          <div
            className="lector-nota-agarre"
            onPointerDown={(e) => { e.preventDefault(); arrastrandoLectorRef.current = true; document.body.style.userSelect = 'none' }}
            role="slider"
            aria-label="Cambiar el alto del lector"
            aria-valuenow={Math.round(alturaLector)}
            aria-valuemin={28}
            aria-valuemax={94}
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'ArrowUp') setAlturaLector((a) => Math.min(94, a + 5))
              if (e.key === 'ArrowDown') setAlturaLector((a) => Math.max(28, a - 5))
            }}
          >
            <span className="lector-nota-agarre-barra" />
          </div>
          <div className="lector-nota-header">
            <span className="lector-nota-fuente">{lectorNotaMostrada.fuente || 'Nota'}</span>
            <div className="lector-nota-acciones">
              <a className="lector-nota-abrir" href={lectorNotaMostrada.url} target="_blank" rel="noopener noreferrer">
                Abrir en pestaña nueva <ArrowUpRight size={13} />
              </a>
              <button className="detalle-cerrar" onClick={() => setLectorNota(null)} aria-label="Cerrar lector"><X size={16} /></button>
            </div>
          </div>
          <p className="lector-nota-aviso">Algunos sitios no permiten mostrarse acá adentro -- si no carga, abrila en una pestaña nueva.</p>
          <iframe className="lector-nota-iframe" src={lectorNotaMostrada.url} title={lectorNotaMostrada.titulo} />
        </div>
        </>
      )}

      {/* Se oculta durante la navegación: no solo no hace falta buscar
          mientras estás en camino, sino que en pantalla chica quedaba
          asomando detrás de la tarjeta de "doblá acá" (se veía en las
          capturas que mandaste) -- las dos ocupaban la misma franja
          horizontal arriba.
          Sin hazard-edge: la franja de "cinta de peligro" sobre una píldora
          se veía mal (a pedido de Rodo) -- ese motivo queda reservado para
          paneles de datos de riesgo, no para el buscador. */}
      {!vistaNavegacion && (
        <div className="searchbar panel-enter" style={{ animationDelay: '0.05s' }}>
          <button type="button" className="searchbar-icon" onClick={() => sugBusqueda.buscar(busqueda)} aria-label="Buscar dirección" disabled={!busqueda.trim()}><Search size={13} /></button>
          <input type="text" placeholder="Buscar lugar, calle o local..." value={busqueda} onChange={(e) => { setBusqueda(e.target.value); sugBusqueda.limpiar() }} onKeyDown={(e) => { if (e.key === 'Enter') sugBusqueda.buscar(busqueda) }} onFocus={() => setBuscaEnFoco(true)} onBlur={() => { setBuscaEnFoco(false); setTimeout(sugBusqueda.limpiar, 150) }} aria-label="Buscar lugar, calle o local" autoComplete="off" />
          {sugBusqueda.buscando && <span className="ruta-form-sug-spinner spinner spinner-dark" />}
          {busqueda && <button className="searchbar-clear" onClick={() => { setBusqueda(''); sugBusqueda.limpiar() }} aria-label="Limpiar búsqueda"><X size={12} /></button>}
          {(sugBusqueda.resultados.length > 0 || sugBusqueda.buscada || sugBusqueda.error) && (
            <ul className="ruta-form-sugerencias searchbar-sugerencias">
              {sugBusqueda.resultados.map((s, i) => (
                <li key={i}>
                  <button type="button" onMouseDown={() => buscarEnMapa(s)}>
                    <MapPin size={12} /> {s.label}
                  </button>
                </li>
              ))}
              {sugBusqueda.buscada && sugBusqueda.resultados.length === 0 && <li className="ruta-form-sin-resultados">No encontramos esa dirección. Probá con más detalle.</li>}
              {sugBusqueda.error && <li className="ruta-form-sin-resultados">No pudimos buscar. Probá de nuevo.</li>}
            </ul>
          )}
          {buscaEnFoco && !busqueda.trim() && recientes.length > 0 && (
            <ul className="ruta-form-sugerencias searchbar-sugerencias">
              <li className="ruta-form-sin-resultados">Recientes</li>
              {recientes.map((r, i) => (
                <li key={`${r.label}-${i}`}>
                  <button type="button" onMouseDown={() => buscarEnMapa(r)}>
                    <Clock size={12} /> {r.label}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {lugarElegido && !rutaAbierta && (
        <div className="lugar-card panel-enter" role="dialog" aria-label="Lugar elegido">
          <div className="lugar-card-texto">
            <MapPin size={14} />
            <span>
              {lugarElegido.label}
              {lugarElegido.categoria && <em className="lugar-card-categoria">{lugarElegido.categoria}</em>}
            </span>
          </div>
          <div className="lugar-card-acciones">
            <button type="button" className="lugar-card-cerrar" onClick={() => setLugarElegido(null)}>Cerrar</button>
            <button type="button" className="lugar-card-ir" onClick={irAlLugar}><Navigation size={13} /> Ir</button>
          </div>
        </div>
      )}

      {rutaAbierta && (
        <div className="ruta-form panel-enter">
          <div className="ruta-form-fila ruta-form-fila-con-sugerencias">
            <span className="ruta-form-punto ruta-form-punto-origen" />
            <input placeholder="Origen" value={origenTexto} onChange={(e) => { setOrigenTexto(e.target.value); setOrigenPunto(null); sugOrigen.limpiar() }} onKeyDown={(e) => { if (e.key === 'Enter' && !origenPunto) sugOrigen.buscar(origenTexto) }} onBlur={() => setTimeout(sugOrigen.limpiar, 150)} aria-label="Origen de la ruta" autoComplete="off" />
            {sugOrigen.buscando && <span className="ruta-form-sug-spinner spinner spinner-dark" />}
            <button className={`ruta-form-pin ${campoActivo === 'origen' ? 'activo' : ''}`} title="Marcar en el mapa" aria-label="Marcar origen en el mapa" onClick={() => marcarEnMapa('origen')}><MapPin size={14} /></button>
            {(sugOrigen.resultados.length > 0 || sugOrigen.buscada || sugOrigen.error) && (
              <ul className="ruta-form-sugerencias">
                {sugOrigen.resultados.map((s, i) => (
                  <li key={i}>
                    <button type="button" onMouseDown={() => elegirSugerencia('origen', s)}>
                      <MapPin size={12} /> {s.label}
                    </button>
                  </li>
                ))}
                {sugOrigen.buscada && sugOrigen.resultados.length === 0 && <li className="ruta-form-sin-resultados">No encontramos esa dirección.</li>}
                {sugOrigen.error && <li className="ruta-form-sin-resultados">No pudimos buscar. Probá de nuevo.</li>}
              </ul>
            )}
          </div>
          <button className="ruta-form-swap" onClick={intercambiar} title="Intercambiar" aria-label="Intercambiar origen y destino"><ArrowUpDown size={13} /></button>
          <div className="ruta-form-fila ruta-form-fila-con-sugerencias">
            <span className="ruta-form-punto ruta-form-punto-destino" />
            <input placeholder="Destino" value={destinoTexto} onChange={(e) => { setDestinoTexto(e.target.value); setDestinoPunto(null); sugDestino.limpiar() }} onKeyDown={(e) => { if (e.key === 'Enter' && !destinoPunto) sugDestino.buscar(destinoTexto) }} onBlur={() => setTimeout(sugDestino.limpiar, 150)} aria-label="Destino de la ruta" autoComplete="off" />
            {sugDestino.buscando && <span className="ruta-form-sug-spinner spinner spinner-dark" />}
            <button className={`ruta-form-pin ${campoActivo === 'destino' ? 'activo' : ''}`} title="Marcar en el mapa" aria-label="Marcar destino en el mapa" onClick={() => marcarEnMapa('destino')}><MapPin size={14} /></button>
            {(sugDestino.resultados.length > 0 || sugDestino.buscada || sugDestino.error) && (
              <ul className="ruta-form-sugerencias">
                {sugDestino.resultados.map((s, i) => (
                  <li key={i}>
                    <button type="button" onMouseDown={() => elegirSugerencia('destino', s)}>
                      <MapPin size={12} /> {s.label}
                    </button>
                  </li>
                ))}
                {sugDestino.buscada && sugDestino.resultados.length === 0 && <li className="ruta-form-sin-resultados">No encontramos esa dirección.</li>}
                {sugDestino.error && <li className="ruta-form-sin-resultados">No pudimos buscar. Probá de nuevo.</li>}
              </ul>
            )}
          </div>
          <div className="favoritos-fila">
            {favoritos.casa ? (
              <button className="favorito-chip" onClick={() => usarFavorito(favoritos.casa)}><Home size={12} /> Casa</button>
            ) : destinoTexto.trim() ? (
              <button className="favorito-chip favorito-chip-guardar" onClick={() => guardarFavorito('casa', 'Casa')}><Save size={12} /> Guardar como Casa</button>
            ) : (
              <button className="favorito-chip favorito-chip-vacio" disabled><Home size={12} /> Casa</button>
            )}
            {favoritos.trabajo ? (
              <button className="favorito-chip" onClick={() => usarFavorito(favoritos.trabajo)}><Briefcase size={12} /> Trabajo</button>
            ) : destinoTexto.trim() ? (
              <button className="favorito-chip favorito-chip-guardar" onClick={() => guardarFavorito('trabajo', 'Trabajo')}><Save size={12} /> Guardar como Trabajo</button>
            ) : (
              <button className="favorito-chip favorito-chip-vacio" disabled><Briefcase size={12} /> Trabajo</button>
            )}
          </div>
          {campoActivo && <p className="ruta-form-hint">Tocá el mapa para marcar el {campoActivo}.</p>}
          <button className="ruta-form-miubicacion" onClick={usarMiUbicacionComoOrigen}><LocateFixed size={14} /> Usar mi ubicación como origen</button>
          {rutaError && <p className="ruta-form-error">{rutaError}</p>}
          <div className="ruta-form-acciones">
            <button className="ruta-form-cancelar" onClick={cerrarTodoRuta}>Cancelar</button>
            <button className="ruta-form-buscar" onClick={buscarRuta}>Buscar ruta</button>
          </div>
        </div>
      )}

      {rutaCargando && (
        <div className="ruta-banner panel-enter"><span className="spinner spinner-dark" /> Calculando rutas reales...</div>
      )}
      {rutaError && !rutaAbierta && (
        <div className="ruta-banner ruta-banner-error panel-enter">{rutaError}<button onClick={cerrarTodoRuta}>Cerrar</button></div>
      )}

      <div className={`mapa-wrapper ${primeraVezListo ? 'cargado' : ''}`}>
        <Suspense fallback={null}><MapaMotoSafe
          tema={tema}
          centro={CENTRO_GBA}
          zoomInicial={11}
          onZoomChange={setZoomActual}
          onReady={onMapaReady}
          apiUrl={API_URL}
          capaTrafico={capaTrafico}
          onTraficoEstado={onTraficoEstadoCambio}
          campoActivo={campoActivo}
          onClickMapa={clicMapa}
          tapRapidoHabilitado={tapRapidoHabilitado}
          onTapMapaVacio={tapMapaVacio}
          onAbrirLector={setLectorNota}
          zonasFiltradas={zonasFiltradas}
          zonaResaltada={zonaResaltada}
          zonasCruzadasIds={zonasCruzadasIds}
          onClickZona={onClickZonaMapa}
          atenuarFondo={atenuarFondo}
          capaMapa={capaMapa}
          filtroHexagono={filtroHexagono}
          corredoresFiltrados={corredoresFiltrados}
          capaInseguridad={capaInseguridad}
          inseguridadFiltrada={capaInseguridad === 'moto' ? inseguridadMotoFiltrada : inseguridadGeneralFiltrada}
          reportes={reportes}
          onVotarReporte={votarReporte}
          reportesPrensa={reportesPrensaFiltrados}
          horaActual={horaActual}
          rutasCalculadas={rutasCalculadas}
          rutaSeleccionada={rutaSeleccionada}
          onClickRuta={setRutaSeleccionada}
          origenPunto={origenPunto}
          destinoPunto={destinoPunto}
          ubicacionReporte={paso === 'eligiendo' ? ubicacionReporte : null}
          lugarElegido={rutaAbierta ? null : lugarElegido}
          miUbicacion={miUbicacion}
          vistaNavegacion={vistaNavegacion}
          modoViaje={modoViaje}
          rumboActual={rumboActual}
          progresoRutaIndice={progresoRuta?.indiceCercano ?? null}
          siguiendoUbicacion={siguiendoUbicacion}
          onPaneoManual={manejarPaneoManual}
        /></Suspense>
        {mapaListo && (
          <>
            <div className="zoom-controls panel-enter" style={{ animationDelay: '0.1s' }}>
              <button onClick={() => mapaRef.current.zoomTo(mapaRef.current.getZoom() + 0.5, { duration: 200 })} aria-label="Acercar mapa">+</button>
              <button onClick={() => mapaRef.current.zoomTo(mapaRef.current.getZoom() - 0.5, { duration: 200 })} aria-label="Alejar mapa">−</button>
            </div>
            <EscalaMapa mapa={mapaRef.current} />
          </>
        )}
      </div>

      {/* Panel completo de opciones de ruta: SOLO antes de arrancar a navegar.
          Elegir entre rutas alternativas no tiene sentido una vez que ya
          estás en camino -- ahí lo único que hace falta ver es el próximo
          giro (navegacion-panel, arriba) y cuánto falta (nav-resumen-mini,
          abajo). Tenerlo abierto durante la navegación era el problema de
          clutter más visible de las capturas que mandaste. */}
      {panelRuta.montado && (
        <div className={`ruta-resumen panel-enter hazard-edge ${panelRuta.saliendo ? 'panel-exit' : ''}`}>
        {/* "Iniciar viaje" quedaba adentro del mismo scroll que la lista de
            rutas y zonas cruzadas -- con 2+ rutas y varias zonas, ese botón
            terminaba fuera de vista sin scrollear (Rodo lo reportó en
            captura real). Ahora solo esta parte de arriba scrollea; el CTA
            y las acciones secundarias quedan fijas abajo del panel, visibles
            siempre sin importar cuánto contenido haya arriba. */}
        <div className="ruta-resumen-scroll">
          <div className="ruta-resumen-header">
            <span className="cercanas-title">Opciones de ruta</span>
            <button className="ruta-resumen-editar" onClick={editarRuta} aria-label="Editar origen y destino"><Pencil size={13} /></button>
          </div>
          {rutasConScore.length > 1 && (
            <div className="ruta-prioridad">
              <button className={rutaSeleccionada === idxMasRapida ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxMasRapida)}><Zap size={12} /> Rápida</button>
              {rutasConScore.length >= 3 && (
                <button className={rutaSeleccionada === idxEquilibrada ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxEquilibrada)}><Scale size={12} /> Equilibrada</button>
              )}
              <button className={rutaSeleccionada === idxMasSegura ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxMasSegura)} title="Menor exposición registrada entre estas alternativas"><ShieldCheck size={12} /> Menor exposición</button>
            </div>
          )}
          {rutasConScore.map((r, i) => (
            <button key={i} className={`ruta-opcion ${i === rutaSeleccionada ? 'activa' : ''}`} onClick={() => setRutaSeleccionada(i)}>
              <span className="ruta-opcion-num">
                Ruta {i + 1}
                {i === idxMasRapida && i === idxMasSegura && r.coberturaRegistrada >= 0.6 && <span className="ruta-opcion-badge badge-ambas"><Zap size={10} /><ShieldCheck size={10} /> rápida y menor exposición</span>}
                {i === idxMasRapida && i !== idxMasSegura && <span className="ruta-opcion-badge badge-rapida"><Zap size={10} /> rápida</span>}
                {i === idxMasSegura && i !== idxMasRapida && r.coberturaRegistrada >= 0.6 && <span className="ruta-opcion-badge badge-segura"><ShieldCheck size={10} /> menor exposición</span>}
                {i === idxEquilibrada && i !== idxMasRapida && i !== idxMasSegura && <span className="ruta-opcion-badge badge-equilibrada"><Scale size={10} /> equilibrada</span>}
              </span>
              <span className="ruta-opcion-datos">
                {r.km} km · {r.min} min
                {r.etaTrafico && (
                  <span className="ruta-opcion-trafico" title="Tiempo estimado con tráfico en vivo (TomTom) -- puede variar del trazado exacto de esta ruta">
                    {' '}· <Zap size={10} /> {r.etaTrafico.con_trafico_min} min con tráfico
                  </span>
                )}
              </span>
              <span className={`ruta-opcion-riesgo ${r.riesgo === 0 ? 'ok' : `nivel-${r.nivelRelativo}`}`}>
                {r.coberturaRegistrada < 0.6
                  ? <><TriangleAlert size={12} /> cobertura registrada insuficiente</>
                  : r.riesgo === 0
                  ? <><CircleCheck size={12} /> sin zonas registradas cerca</>
                  : <><TriangleAlert size={12} /> exposición {NIVELES[r.nivelRelativo]?.label.toLowerCase()} entre alternativas</>}
              </span>
              {detalleRutaAbierto && (
                <span className="ruta-opcion-cobertura">
                  Cobertura: siniestros {r.coberturaPorFuente.siniestro == null ? 'sin datos' : `${Math.round(r.coberturaPorFuente.siniestro * 100)}%`}
                  {' · '}inseguridad {r.coberturaPorFuente.inseguridad == null ? 'sin datos' : `${Math.round(r.coberturaPorFuente.inseguridad * 100)}%`}
                </span>
              )}
              {detalleRutaAbierto && r.riesgo > 0 && (
                <span className="ruta-opcion-desglose">
                  {r.cantSiniestros > 0 && <span className="desglose-item desglose-siniestro" title={`${r.cantSiniestros} zonas de siniestro cruzadas`}><Siren size={11} /> {r.cantSiniestros}</span>}
                  {r.cantInseguridad > 0 && <span className="desglose-item desglose-inseguridad" title={`${r.cantInseguridad} zonas de inseguridad cruzadas`}><ShieldAlert size={11} /> {r.cantInseguridad}</span>}
                  <span className="desglose-pts" title="Puntaje interno: suma de severidad de cada zona cruzada">{r.riesgo} pts</span>
                </span>
              )}
            </button>
          ))}
          {rutasConScore.length === 1 && (
            <p className="ruta-sin-alternativa">No encontramos una ruta alternativa razonable para este tramo.</p>
          )}
          <p className="ruta-cobertura-aviso">
            La exposición compara zonas históricas registradas; no estima la probabilidad de un siniestro ni confirma cobertura completa fuera de las áreas con datos.
          </p>
          {/* R-04/R-05 (Capitulo 6): toggle de detalle + ejemplo visual fijo
              en vez de un tooltip que solo aparece con hover (inutil en
              celular, que es como la mayoria usa esto en la calle). La
              prueba real mostro que el texto aclaratorio solo no alcanza
              para que se entienda "cobertura" (Casos 1, 3, 10, 12); un
              ejemplo concreto con numeros reales es mas dificil de leer mal
              que una definicion abstracta. */}
          <button
            type="button"
            className="ruta-detalle-toggle"
            onClick={() => setDetalleRutaAbierto((v) => !v)}
            aria-expanded={detalleRutaAbierto}
          >
            {detalleRutaAbierto ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {detalleRutaAbierto ? 'Ocultar cómo se calcula' : 'Ver cómo se calcula'}
          </button>
          {detalleRutaAbierto && (
            <p className="ruta-detalle-ejemplo">
              Ejemplo: "siniestros 40%" significa que 4 de cada 10 tramos de esta ruta pasan cerca de un punto con
              siniestros de moto ya registrados; el 60% restante no tiene ese registro, no significa que ahí no
              ocurran. Los "pts" de cada zona son un puntaje interno para ordenar rutas entre sí, no una chance de
              choque.
            </p>
          )}
          {zonasCruzadasOrdenadas.length > 0 && (
            <div className="ruta-resumen-detalle">
              {zonasCruzadasOrdenadas.slice(0, 6).map((z) => (
                <div key={z.id} className="ruta-resumen-item">
                  <span className="cercanas-dot" style={{ background: NIVELES[z.nivel].color }} />
                  {z.tipoRiesgo === 'inseguridad' ? <ShieldAlert size={11} className="ruta-resumen-icono" /> : <Siren size={11} className="ruta-resumen-icono" />}
                  {z.nombre}
                  {/* A11: distancia real al segmento de ruta más cercano, no
                      solo "cruza" (el umbral ya filtra eso). "cruza a 80m" y
                      "cruza a 580m" expresan una incertidumbre muy distinta
                      sobre si la zona corresponde de verdad al tramo. */}
                  {Number.isFinite(z.distanciaSegmentoKm) && (
                    <span
                      className="ruta-resumen-distancia"
                      title="Distancia desde esta zona al punto más cercano del trazado de la ruta"
                    >
                      a {formatearDistancia(z.distanciaSegmentoKm)}
                    </span>
                  )}
                  {z.ajustadoPorHorario && (
                    <Clock size={11} className="ruta-resumen-ajuste" title={z.motivoAjusteHorario || 'Nivel subido por franja horaria'} />
                  )}
                  {z.ajustadoPorReciente && (
                    <Newspaper size={11} className="ruta-resumen-ajuste" title={z.motivoAjuste || 'Nivel subido por un reporte de prensa reciente'} />
                  )}
                </div>
              ))}
              {zonasCruzadasOrdenadas.length > 6 && (
                <p className="ruta-resumen-mas">+ {zonasCruzadasOrdenadas.length - 6} zonas más de menor riesgo</p>
              )}
            </div>
          )}
        </div>
          <button className="ruta-resumen-iniciar" onClick={iniciarNavegacionRuta}>
            <Navigation size={15} /> Iniciar viaje
          </button>
          <div className="ruta-resumen-acciones-finales">
            {/* Antes iba "Compartir" acá -- a pedido de Rodo, se cambia por
                un Cancelar más directo (mismo cierre completo que ya hacía
                "Nueva ruta") para que salir de "Opciones de ruta" y volver a
                la búsqueda sea más fácil, sin tener que buscar el ícono de
                editar (lápiz) arriba del panel. */}
            <button className="ruta-resumen-compartir" onClick={cerrarTodoRuta}><X size={13} /> Cancelar</button>
            <button className="ruta-resumen-nueva" onClick={cerrarTodoRuta}>Nueva ruta</button>
          </div>
        </div>
      )}

      {/* Tira mínima de navegación activa: reemplaza al panel completo de
          arriba mientras hay ruta + Modo Viaje. Es la barra de "cuánto
          falta" que le faltaba a la app -- antes, una vez que arrancabas a
          navegar, no había NINGÚN indicador de progreso del viaje. */}
      {rutasCalculadas.length > 0 && modoViaje && (
        <div className="nav-resumen-mini panel-enter" role="status" aria-live="polite">
          {velocidadActual != null && (
            <div className="viaje-velocidad" title="Velocidad actual (GPS)">
              <strong>{Math.round(velocidadActual * 3.6)}</strong>
              <span>km/h</span>
            </div>
          )}
          <div className="viaje-tiempo">
            <strong>{etaInfo ? etaInfo.minRestante : rutasConScore[rutaSeleccionada]?.min} min</strong>
            <span>
              {etaInfo ? etaInfo.distanciaRestanteKm.toFixed(1) : rutasConScore[rutaSeleccionada]?.km} km
              {etaInfo && <> · llegás {etaInfo.horaLlegada}</>}
            </span>
          </div>
          <button className="viaje-salir" onClick={() => desactivarModoViaje()} aria-label="Detener navegación">
            <Square size={12} /> <span>Salir</span>
          </button>
        </div>
      )}

      {/* Botón de recentrar (estilo Waze/Maps): aparece solo cuando el
          usuario paneó el mapa a mano durante el viaje y la cámara dejó de
          seguir al GPS -- ver siguiendoUbicacion más arriba. */}
      {modoViaje && !siguiendoUbicacion && (
        <button className="recenter-fab panel-enter" onClick={recentrarUbicacion} aria-label="Volver a mi ubicación">
          <LocateFixed size={18} />
        </button>
      )}

      {/* Velocímetro en vivo (mismo lugar que en Waze/Maps: círculo abajo a
          la izquierda). Solo aparece si el GPS realmente entrega velocidad
          -- no todos los navegadores/dispositivos la dan, y mostrar 0 fijo
          sería peor que no mostrar nada. */}
      {vistaNavegacion && velocidadActual != null && (
        <div className="velocimetro panel-enter" title="Velocidad actual (GPS)">
          <Gauge size={12} className="velocimetro-icono" />
          <strong>{Math.round(velocidadActual * 3.6)}</strong>
          <span>km/h</span>
        </div>
      )}

      {panelDetalle.montado && zonaMostrada && (
        <div className={`detalle-panel panel-enter hazard-edge ${panelDetalle.saliendo ? 'panel-exit' : ''}`}>
          <button className="detalle-cerrar" onClick={() => setZonaSeleccionada(null)} aria-label="Cerrar detalle de zona"><X size={14} /></button>
            <span className="popup-nivel" style={{ color: NIVELES[zonaMostrada.ajuste.nivel].color }}>
            Gravedad estimada: {NIVELES[zonaMostrada.ajuste.nivel].label}
          </span>
          <strong className="detalle-nombre">{zonaMostrada.nombre}</strong>
          <p className="detalle-motivo">{zonaMostrada.motivo}</p>
          {zonaMostrada.prediccionModelo && (
            <div className="detalle-modelo">
              <span className="detalle-modelo-titulo">Gravedad estimada si ocurre un siniestro</span>
              {Object.entries(zonaMostrada.prediccionModelo).map(([clase, prob]) => (
                <div className="detalle-modelo-fila" key={clase}>
                  <span className="detalle-modelo-label">{clase}</span>
                  <div className="detalle-modelo-track">
                    <div className="detalle-modelo-fill" style={{ width: `${prob * 100}%`, background: COLOR_CLASE_MODELO[clase] || '#8A9099' }} />
                  </div>
                  <span className="detalle-modelo-num">{Math.round(prob * 100)}%</span>
                </div>
              ))}
              {zonaMostrada.contextoEstimado && (
                <p className="detalle-modelo-nota">Esta zona no tiene perfil histórico propio: se usó el perfil promedio de la ciudad.</p>
              )}
              <p className="detalle-modelo-nota">No estima la probabilidad de sufrir un siniestro durante tu viaje.</p>
            </div>
          )}
          {zonaMostrada.ajustadoPorReciente && (
            <p className="popup-ajuste"><ArrowUp size={12} /> Nivel subido: {zonaMostrada.motivoAjuste}</p>
          )}
          {zonaMostrada.ajuste.subio && (
            <div className="detalle-ajuste">
              <span className="detalle-ajuste-base">Base: {NIVELES[zonaMostrada.nivel].label}</span>
              <span className="detalle-ajuste-flecha">→</span>
              <span className="detalle-ajuste-ahora" style={{ color: NIVELES[zonaMostrada.ajuste.nivel].color }}>
                Ahora: {NIVELES[zonaMostrada.ajuste.nivel].label}
              </span>
              <p className="detalle-ajuste-motivo">Subió por: {zonaMostrada.ajuste.motivos.join(' + ')}</p>
            </div>
          )}
        </div>
      )}

      {/* La leyenda se esconde mientras está abierto "Opciones de ruta": ahí
          el riesgo ya se lee en cada tarjeta de ruta (bajo/medio/alto/
          crítico) y en las burbujas de hotspot del mapa, así que la leyenda
          + filtro por nivel no suma nada en ese momento y sí compite por el
          mismo espacio de pantalla en celular (a pedido de Rodo: que
          "Opciones de ruta" pueda usar ese lugar en vez de compartirlo). */}
      {!vistaNavegacion && !panelRuta.montado && (
        <div className="legend-stack">
          <div className="legend panel-enter hazard-edge" style={{ animationDelay: '0.2s' }}>
            <div className="legend-header">
              <span className="legend-title">Nivel de riesgo <em>(tocá para filtrar)</em></span>
              {hayFiltrosApagados && <button className="legend-reset" onClick={restablecerFiltros}>Restablecer</button>}
            </div>
            {capaMapa === 'hexagonos' && (
              <div className="portal-actividad-filtros-fila legend-filtro-hexagono">
                {OPCIONES_FILTRO_HEXAGONO.map((f) => (
                  <button key={f.id} className={filtroHexagono === f.id ? 'activo' : ''} onClick={() => setFiltroHexagono(f.id)}>{f.label}</button>
                ))}
              </div>
            )}
            <TextoCobertura meta={coberturaCapas?.[capaMapa === 'corredores' ? 'corredores' : 'hotspots']} prefijo="Siniestros" />
            {Object.entries(NIVELES).map(([key, val]) => (
              <button key={key} className={`legend-item ${nivelesActivos.has(key) ? '' : 'inactive'}`} onClick={() => toggleNivel(key)}>
                <span className="legend-swatch" style={{ background: val.color }} />
                {val.label}
                <span className="legend-count">{conteos[key]}</span>
              </button>
            ))}
          </div>

          {capaInseguridad !== 'apagado' && (
            <div className="legend legend-inseguridad panel-enter hazard-edge" style={{ animationDelay: '0.22s' }}>
              <div className="legend-header">
                <span className="legend-title">{OPCIONES_CAPA_INSEGURIDAD.find((o) => o.id === capaInseguridad)?.label} <em>(datos GCBA)</em></span>
              </div>
              <TextoCobertura meta={coberturaCapas?.[`inseguridad_${capaInseguridad}`]} prefijo="Delitos" />
              {Object.entries(NIVELES).map(([key, val]) => (
                <button key={key} className={`legend-item ${nivelesActivos.has(key) ? '' : 'inactive'}`} onClick={() => toggleNivel(key)}>
                  <span className="legend-swatch" style={{ background: NIVELES_INSEGURIDAD_COLOR[key] }} />
                  {val.label}
                  <span className="legend-count">{conteosInseguridad[key]}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {!rutaAbierta && rutasCalculadas.length === 0 && (
        <button className="route-fab panel-enter" style={{ animationDelay: '0.22s' }} onClick={abrirPanelRuta}><Compass size={16} /> <span>Trazar ruta</span></button>
      )}

      <div className="herramientas-stack">
        {herramientasAbiertas && (
          <div className="herramientas-menu panel-enter">
            <button onClick={() => { pedirUbicacion(); setHerramientasAbiertas(false) }}>
              {buscandoUbicacion ? <span className="spinner" /> : <LocateFixed size={15} />} Mi ubicación
            </button>
            <button className={modoViaje ? 'activo' : ''} onClick={toggleModoViaje}>
              <Bike size={15} /> Modo Viaje {modoViaje ? '· activo' : ''}
            </button>
            {modoViaje && (
              <button className={vistaNavegacion ? 'activo' : ''} onClick={() => setVistaNavegacion((v) => !v)}>
                <Box size={15} /> Vista inclinada {vistaNavegacion ? '· activa' : ''}
              </button>
            )}
            <button onClick={() => { setStatsAbierto(true); setHerramientasAbiertas(false); setActividadAbierta(false); setCapasAbiertas(false) }}>
              <BarChart3 size={15} /> Estadísticas
            </button>
            {sesion && (
              <button onClick={() => { setHerramientasAbiertas(false); sesion.cerrarSesion() }} title={`Sesión de ${sesion.usuario}`}>
                <LogOut size={15} /> Cerrar sesión
              </button>
            )}
          </div>
        )}
        <button
          className={`herramientas-fab ${herramientasAbiertas ? 'activo' : ''}`}
          onClick={() => setHerramientasAbiertas((v) => !v)}
          aria-label="Más herramientas"
          aria-expanded={herramientasAbiertas}
        >
          {herramientasAbiertas ? <X size={18} /> : <Wrench size={18} />}
        </button>
      </div>

      <button className={`report-fab panel-enter ${paso !== 'idle' ? 'active' : ''} ${panelRuta.montado ? 'oculto-por-ruta' : ''}`} style={{ animationDelay: '0.3s' }} onClick={iniciarReporte} aria-label={paso === 'idle' ? 'Reportar' : undefined}>
        {paso === 'buscando' ? <span className="spinner" /> : paso === 'eligiendo' ? <X size={16} /> : <TriangleAlert size={16} />}
        <span>{paso === 'buscando' ? 'Ubicando...' : paso === 'eligiendo' ? 'Cancelar' : 'Reportar'}</span>
      </button>

      {paso === 'eligiendo' && (
        <div className="report-sheet hazard-edge">
          <div className="report-sheet-cabecera">
            <h3>¿Qué estás viendo en la vía?</h3>
            <button type="button" className="report-sheet-cerrar" aria-label="Cancelar reporte" onClick={() => { setPaso('idle'); setCampoActivo(null) }}><X size={16} /></button>
          </div>
          <div className={`report-options ${!ubicacionReporte ? 'deshabilitadas' : ''}`}>
            {CATEGORIAS_REPORTE.map((cat) => (
              <button key={cat.id} onClick={() => confirmarReporte(cat.id)}><cat.Icon size={15} /> {cat.label}</button>
            ))}
          </div>
          <p className="report-hint">
            <MapPin size={12} />
            {ubicacionReporte ? 'Ubicación por GPS -- tocá el mapa si no es exacta.' : 'Tocá el mapa para marcar dónde fue.'}
          </p>
        </div>
      )}
    </div>
  )
}

// Línea de cobertura bajo el título de una leyenda: el período de los datos es
// lo principal (con eso se juzga la vigencia del riesgo); la fecha en que se
// generó el archivo de la capa va solo en el tooltip.
function TextoCobertura({ meta, prefijo }) {
  const periodo = formatearPeriodo(meta?.desde, meta?.hasta)
  if (!periodo) return null
  const detalle = `${meta.descripcion}: ${meta.desde} a ${meta.hasta} (${meta.registros.toLocaleString('es-AR')} registros). ${meta.fuente}.`
    + (meta.archivo_generado ? ` Archivo de la capa generado el ${meta.archivo_generado}.` : '')
  return (
    <p className="legend-cobertura" title={detalle}>
      {prefijo} {periodo} · GCBA
    </p>
  )
}

export default App

