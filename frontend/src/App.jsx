import { useState, useEffect, useMemo, useRef, useCallback, lazy, Suspense } from 'react'
import './App.css'

import {
  X,
  Compass,
  Siren, ShieldAlert, Layers, Newspaper, ArrowUpRight, Search,
} from 'lucide-react'

import {
  CENTRO_GBA, UMBRAL_CRUCE_KM, UMBRAL_ALERTA_KM, ORDEN_NIVELES, PESO_RIESGO,
  RADIO_ALERTA_REPORTE_KM, MINUTOS_ALERTA_REPORTE_RECIENTE, CATEGORIAS_ALERTA_PROXIMIDAD,
  API_URL, CLAVE_AUTOR_ID, CLAVE_TOKENS_REPORTES, CLAVE_NIVELES, CLAVE_FAVORITOS, CLAVE_TEMA, CLAVE_ONBOARDING, CLAVE_CAPA_MAPA, NIVELES, CATEGORIAS_REPORTE,
  CLAVE_CAPA_INSEGURIDAD, CLAVE_CAPA_TRAFICO, UMBRAL_ZOOM_TRAFICO,
  CLAVE_FILTRO_HEXAGONO,
  CLAVE_CACHE_HOTSPOTS, CLAVE_CACHE_CORREDORES, CLAVE_CACHE_INSEGURIDAD_GENERAL, CLAVE_CACHE_INSEGURIDAD_MOTO,
  CLAVE_CAPA_PRENSA,
} from './constants'
import { siguientePaso, distanciaKm, calcularAjuste, geocodificar, calcularRumbo, calcularProgresoRuta, distanciaAPolilinea } from './utils/geoRiesgo'
import {
  unificarZonasInseguridad, unificarZonasRiesgo, calcularZonasCruzadasPorRuta, calcularCoberturaPorFuente, calcularRutasConScore,
  brechaCoberturaEnRecomendada,
} from './utils/riesgoRuta'
import { formatearDistancia } from './utils/tiempo'
import { iconoClima, reproducirBeep, textoManiobra, iconoManiobra } from './utils/ui'
import { cargarDeLocalStorage, guardarEnLocalStorage, generarUuidV4Fallback } from './utils/storage'
import { resolverBarrio } from './utils/barrio'
import { LoadingScreen } from './components/LoadingScreen'
import { Onboarding } from './components/Onboarding'
import { ThemeToggle } from './components/ThemeToggle'
import { CapasPanel } from './components/CapasPanel'
import { ActividadPortal } from './components/ActividadPortal'
import { RutaResumenPanel } from './components/RutaResumenPanel'
import { HerramientasMenu } from './components/HerramientasMenu'
import { ReportSheet } from './components/ReportSheet'
import { NavegacionManiobra } from './components/NavegacionManiobra'
import { NavegacionResumen } from './components/NavegacionResumen'
import { DetalleZonaPanel } from './components/DetalleZonaPanel'
import { CapaErrorBanners } from './components/CapaErrorBanners'
import { ActividadReciente } from './components/ActividadReciente'
import { RutaForm } from './components/RutaForm'
import { LegendStack } from './components/LegendStack'
import { SearchBar } from './components/SearchBar'
// MapLibre pesa ~800 kB: se carga aparte para que la app abra antes (SES-086).
const MapaMotoSafe = lazy(() => import('./components/MapaMotoSafe').then((m) => ({ default: m.MapaMotoSafe })))
import { useBusquedaDireccion } from './hooks/useBusquedaDireccion'
import { usePanelSaliente } from './hooks/usePanelSaliente'
import { useSesion } from './sesion'


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
// Reporte de usuario (prueba real en celular): "apenas inicio el viaje avisa
// 'te desviaste' un instante y se estabiliza". El GPS recién adquirido
// (watchPosition arrancando en frío) suele dar sus primeros fixes con
// accuracy de cientos de metros antes de bloquear una posición precisa --
// esos fixes pueden caer, los tres seguidos, del mismo lado equivocado de la
// ruta, así que el freno de "3 fixes seguidos" (pensado para ruido disperso
// de +-15-30m) no alcanza a filtrarlos. Se descartan fixes con accuracy
// peor a este umbral antes de que lleguen a miUbicacion.
const ACCURACY_MAXIMA_GPS_M = 100
// Reporte de usuario: el filtro de accuracy de arriba no alcanzó a resolverlo
// del todo ("sigue pasando"). No todos los navegadores/dispositivos reportan
// coords.accuracy de forma confiable (puede venir null, o un valor optimista
// que no refleja el error real del primer fix en frío) -- depender solo de
// ese dato no alcanza. Capa extra, independiente del accuracy reportado: se
// ignora la detección de desvío (no la de llegada) durante los primeros
// segundos de cada viaje, dándole tiempo al GPS a asentarse sin importar qué
// diga accuracy.
const GRACIA_INICIO_VIAJE_MS = 8000
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
  // SES-141: vive acá (no adentro de SearchBar) para que el botón de la
  // topbar y el cierre automático (foco perdido sin texto / resultado
  // elegido) controlen el mismo estado.
  const [busquedaAbierta, setBusquedaAbierta] = useState(false)
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

  // Precarga de barrios (reporte de usuario: "los barrios van cargando muy
  // lento uno por uno" al abrir Actividad). resolverBarrio ya pacea sus
  // pedidos y cachea por clave de módulo (ver utils/barrio.js), así que
  // arrancar la cola acá, apenas llegan los datos, en vez de recién cuando
  // se abre el portal, hace que gran parte ya esté resuelta (o en camino)
  // para cuando el usuario lo abre. Resultado descartado a propósito: esto
  // solo calienta la cache compartida, ActividadPortal vuelve a pedir las
  // mismas claves y las recibe ya resueltas. Acotado a los últimos 7 días
  // (mismo filtro por defecto de ActividadPortal) para no gastar pedidos en
  // ítems viejos que probablemente no se lleguen a mirar.
  useEffect(() => {
    const haceSieteDias = Date.now() - 7 * 24 * 3600000
    const puntos = [
      ...reportesPrensa.filter((r) => new Date(r.fechaReferencia).getTime() >= haceSieteDias),
      ...reportes.filter((r) => new Date(r.creadoEn).getTime() >= haceSieteDias),
    ]
    for (const p of puntos) resolverBarrio(p.lat, p.lng, () => {})
  }, [reportesPrensa, reportes])

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

  // Reporte de usuario (prueba real en celular): filtrar categoría dentro del
  // portal de Actividad no cambiaba nada en el mapa -- dos filtros sueltos
  // sin relación. Primero se sincronizó solo al cerrar el panel; a pedido de
  // Rodo ("tmb debe filtrar en el mapa", sin esperar a cerrar) pasa a
  // aplicarse apenas se toca un botón de categoría (ver onCambiarFiltro en
  // <ActividadPortal>, más abajo). Si la categoría elegida tiene equivalente
  // real en el filtro de prensa del mapa (moto/robo/choque/todas), se aplica
  // ahí y se prende la capa de prensa para que se note. Las categorías que
  // solo existen para reportes colaborativos (inseguro, pavimento, corte,
  // iluminación) no tienen hoy un filtro propio en el mapa -- no se inventa
  // uno, se deja el filtro de prensa como estaba.
  const FILTRO_ACTIVIDAD_A_PRENSA = { todas: 'todos', moto: 'moto', robo: 'robo', choque: 'choque' }
  const sincronizarFiltroActividadConMapa = (filtroCategoria) => {
    const equivalente = FILTRO_ACTIVIDAD_A_PRENSA[filtroCategoria]
    if (equivalente) {
      setFiltroPrensa(equivalente)
      setCapaPrensa(true)
    }
  }

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
        // Fix de baja precisión (típico del arranque en frío del GPS): se
        // descarta antes de tocar posición, rumbo o velocidad, en vez de
        // dejar que alimente la detección de desvío/llegada con ruido grande.
        if (pos.coords.accuracy != null && pos.coords.accuracy > ACCURACY_MAXIMA_GPS_M) return
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
    // V01 (SES-161): faltaba acá -- si el buscador estaba abierto (su
    // desplegable de sugerencias no se ocultaba con ningún otro booleano de
    // los de arriba), quedaba flotando encima de RutaForm, dos paneles
    // compitiendo por el mismo rincón superior de la pantalla.
    setBusquedaAbierta(false)
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
  //
  // Llegada falsa lejos del destino (hallazgo B02, auditoría de Codex
  // 2026-10-23): la proyección sobre cada tramo se clampea a [0,1] (A11), así
  // que un GPS alineado con el último tramo pero bastante más allá del
  // destino proyecta igual que el propio destino -- faltanKm da 0 aunque el
  // GPS esté a kilómetros de verdad. Se exige además que el GPS esté cerca
  // del trazado (distanciaAlTrazadoKm), no solo que su progreso proyectado
  // coincida con el del destino.
  useEffect(() => {
    if (!modoViaje || !miUbicacion || rutasCalculadas.length === 0) return
    const ruta = rutasCalculadas[rutaSeleccionada]
    const pasos = ruta?.pasos || []
    const ultimoPaso = pasos[pasos.length - 1]
    if (!ultimoPaso || ultimoPaso.tipo !== 'arrive' || pasoActual < pasos.length - 1) return
    let faltanKm
    if (ruta?.coords) {
      const progresoGps = calcularProgresoRuta(miUbicacion, ruta.coords)
      const progresoUltimo = calcularProgresoRuta(ultimoPaso, ruta.coords)
      faltanKm = Math.max(
        progresoUltimo.distanciaRecorridaKm - progresoGps.distanciaRecorridaKm,
        progresoGps.distanciaAlTrazadoKm,
        0
      )
    } else {
      faltanKm = distanciaKm(miUbicacion, ultimoPaso)
    }
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
  const inicioViajeTsRef = useRef(0)
  useEffect(() => {
    if (!modoViaje) { desviosSeguidosRef.current = 0; ultimoRerouteTsRef.current = 0; inicioViajeTsRef.current = 0; return }
    if (!inicioViajeTsRef.current) inicioViajeTsRef.current = Date.now()
    if (Date.now() - inicioViajeTsRef.current < GRACIA_INICIO_VIAJE_MS) return
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
    // B05 (auditoría Codex 2026-10-23): antes dependía solo de [busqueda], pero
    // también lee zonasFiltradas -- si las zonas todavía no habían cargado
    // cuando se tipeó la búsqueda, el efecto veía cero coincidencias y nunca
    // se volvía a correr cuando los datos llegaban y pasaban a dar exactamente
    // una. zonasFiltradas ya está memoizada con sus propias dependencias, así
    // que agregarla acá no dispara renders de más.
  }, [busqueda, zonasFiltradas])

  const zonasCruzadasPorRuta = useMemo(
    () => calcularZonasCruzadasPorRuta(rutasCalculadas, zonasRiesgoTodas, UMBRAL_CRUCE_KM),
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
    () => calcularRutasConScore(rutasCalculadas, zonasCruzadasPorRuta, coberturaPorFuente),
    [rutasCalculadas, zonasCruzadasPorRuta, coberturaPorFuente]
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

  // DEC-026 (D03, caso 2): si la ruta de "menor exposición" depende de una
  // fuente con mucha menos cobertura registrada que la otra, avisar -- la
  // ausencia de dato no es ausencia de riesgo (ver comentario largo en
  // brechaCoberturaEnRecomendada, riesgoRuta.js).
  const brechaCoberturaRecomendada = useMemo(
    () => brechaCoberturaEnRecomendada(rutasConScore, idxMasSegura),
    [rutasConScore, idxMasSegura]
  )

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

  // B04 (auditoría Codex 2026-10-23): usaba zonasAjustadas (todas las zonas
  // de siniestros cargadas) pese a etiquetarse "del mapa visible" -- apagar
  // un nivel o buscar por nombre no lo movía un punto, porque esos filtros
  // viven en zonasFiltradas, no acá. Usa zonasFiltradas para que sí refleje
  // niveles activos y búsqueda; sigue sin contemplar zoom/paneo del mapa en
  // sí (eso necesitaría leer los bounds del mapa, no solo los filtros).
  const indiceRiesgo = useMemo(() => {
    if (zonasFiltradas.length === 0) return 0
    const total = zonasFiltradas.reduce((acc, z) => acc + PESO_RIESGO[z.ajuste.nivel], 0)
    const maximoPosible = zonasFiltradas.length * PESO_RIESGO.critico
    return Math.round((total / maximoPosible) * 100)
  }, [zonasFiltradas])

  const totalSiniestros = useMemo(() => zonasAjustadas.reduce((acc, z) => acc + (z.cantidad || 0), 0), [zonasAjustadas])

  const top5Peligrosas = useMemo(() => {
    return [...zonasAjustadas].sort((a, b) => (b.cantidad || 0) - (a.cantidad || 0)).slice(0, 5)
  }, [zonasAjustadas])

  const hayFiltrosApagados = nivelesActivos.size < Object.keys(NIVELES).length
  // "Opciones de ruta" abierto (ver el panel .ruta-resumen más abajo): mismo
  // booleano para esconder la leyenda mientras se muestra, así los dos no
  // compiten por el mismo rincón de la pantalla en celular.
  const mostrandoOpcionesRuta = rutasCalculadas.length > 0 && !modoViaje
  // V01 (SES-161): el comportamiento de "modo" ya existía (explorar vs.
  // comparar vs. navegar se infería de modoViaje/rutasCalculadas.length,
  // y ya eran excluyentes entre sí -- RutaForm cierra al calcular rutas,
  // modoViaje oculta el resto). Lo que faltaba era hacerlo explícito en vez
  // de inferirlo cada vez; esta derivación no cambia ningún comportamiento,
  // solo le pone nombre a lo que ya pasaba, para poder engancharle CSS/tests
  // por modo sin repetir la misma combinación de booleanos en cada lugar.
  const modoActual = modoViaje ? 'navegar' : mostrandoOpcionesRuta ? 'comparar' : 'explorar'
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
    <div className="app" data-modo={modoActual}>
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
            {/* SES-141: antes era un círculo con la lupa flotando solo en el
                medio de la pantalla -- a pedido de Rodo ("queda sola ahí,
                suelta"), se mudó a la topbar, agrupado con los demás
                botones de exploración (tema/capas/actividad). */}
            {!vistaNavegacion && (
              <button
                className="capa-toggle"
                onClick={() => setBusquedaAbierta((v) => !v)}
                aria-label="Buscar lugar, calle o local"
                aria-expanded={busquedaAbierta}
                title="Buscar"
              >
                <Search size={15} />
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
            className={`topbar-status ${mostrarAlerta ? 'alerta' : ''} ${modoViaje ? 'viaje' : ''} ${tengoReportesPropios ? 'clickeable' : ''} ${vistaNavegacion ? 'nav-activa' : ''}`}
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

      <NavegacionManiobra
        modoViaje={modoViaje} rutasCalculadas={rutasCalculadas} rutaSeleccionada={rutaSeleccionada} pasoActual={pasoActual}
        miUbicacion={miUbicacion} distanciaManiobraKm={distanciaManiobraKm}
        formatearDistancia={formatearDistancia} textoManiobra={textoManiobra} iconoManiobra={iconoManiobra}
      />

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

      <CapaErrorBanners
        backendError={backendError} cargarHotspots={cargarHotspots}
        erroresCapas={erroresCapas} ultimaConsultaCapas={ultimaConsultaCapas} setRecargaCapas={setRecargaCapas}
        capaTrafico={capaTrafico} traficoNoDisponible={traficoNoDisponible} setCapaTrafico={setCapaTrafico}
        capasVacias={{
          corredores: corredores.length === 0,
          inseguridadGeneral: inseguridadGeneral.length === 0,
          inseguridadMoto: inseguridadMoto.length === 0,
          hotspots: ZONAS_RIESGO.length === 0,
        }}
      />


      {panelActividad.montado && tengoReportesPropios && (
        <ActividadReciente
          panelActividad={panelActividad} setActividadAbierta={setActividadAbierta}
          cargandoHistorial={cargandoHistorial} errorHistorial={errorHistorial} historialReportes={historialReportes} misReportes={misReportes}
          horaActual={horaActual} setVuelo={setVuelo} borrarReportes={borrarReportes}
        />
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
          onCambiarFiltro={sincronizarFiltroActividadConMapa}
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
      <SearchBar
        abierto={busquedaAbierta} setAbierto={setBusquedaAbierta}
        vistaNavegacion={vistaNavegacion} busqueda={busqueda} setBusqueda={setBusqueda} sugBusqueda={sugBusqueda}
        buscaEnFoco={buscaEnFoco} setBuscaEnFoco={setBuscaEnFoco} recientes={recientes} buscarEnMapa={buscarEnMapa}
        lugarElegido={lugarElegido} setLugarElegido={setLugarElegido} rutaAbierta={rutaAbierta} irAlLugar={irAlLugar}
      />

      {rutaAbierta && (
        <RutaForm
          origenTexto={origenTexto} setOrigenTexto={setOrigenTexto} origenPunto={origenPunto} setOrigenPunto={setOrigenPunto} sugOrigen={sugOrigen}
          destinoTexto={destinoTexto} setDestinoTexto={setDestinoTexto} destinoPunto={destinoPunto} setDestinoPunto={setDestinoPunto} sugDestino={sugDestino}
          campoActivo={campoActivo} marcarEnMapa={marcarEnMapa} elegirSugerencia={elegirSugerencia} intercambiar={intercambiar}
          favoritos={favoritos} guardarFavorito={guardarFavorito} usarFavorito={usarFavorito} usarMiUbicacionComoOrigen={usarMiUbicacionComoOrigen}
          rutaError={rutaError} cerrarTodoRuta={cerrarTodoRuta} buscarRuta={buscarRuta}
        />
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

      {/* A17: extraido a components/RutaResumenPanel.jsx (SES-128). Mismo
          comportamiento, ahora detras de una interfaz de props chica en vez
          de 145 lineas inline. */}
      <RutaResumenPanel
        panelRuta={panelRuta}
        editarRuta={editarRuta}
        rutasConScore={rutasConScore}
        rutaSeleccionada={rutaSeleccionada}
        setRutaSeleccionada={setRutaSeleccionada}
        idxMasRapida={idxMasRapida}
        idxEquilibrada={idxEquilibrada}
        idxMasSegura={idxMasSegura}
        brechaCoberturaRecomendada={brechaCoberturaRecomendada}
        detalleRutaAbierto={detalleRutaAbierto}
        setDetalleRutaAbierto={setDetalleRutaAbierto}
        zonasCruzadasOrdenadas={zonasCruzadasOrdenadas}
        iniciarNavegacionRuta={iniciarNavegacionRuta}
        cerrarTodoRuta={cerrarTodoRuta}
      />

      <NavegacionResumen
        rutasCalculadas={rutasCalculadas} modoViaje={modoViaje} velocidadActual={velocidadActual}
        etaInfo={etaInfo} rutasConScore={rutasConScore} rutaSeleccionada={rutaSeleccionada}
        desactivarModoViaje={desactivarModoViaje} siguiendoUbicacion={siguiendoUbicacion}
        recentrarUbicacion={recentrarUbicacion} vistaNavegacion={vistaNavegacion}
      />

      <DetalleZonaPanel panelDetalle={panelDetalle} zonaMostrada={zonaMostrada} setZonaSeleccionada={setZonaSeleccionada} coberturaCapas={coberturaCapas} />

      {/* La leyenda se esconde mientras está abierto "Opciones de ruta": ahí
          el riesgo ya se lee en cada tarjeta de ruta (bajo/medio/alto/
          crítico) y en las burbujas de hotspot del mapa, así que la leyenda
          + filtro por nivel no suma nada en ese momento y sí compite por el
          mismo espacio de pantalla en celular (a pedido de Rodo: que
          "Opciones de ruta" pueda usar ese lugar en vez de compartirlo). */}
      <LegendStack
        vistaNavegacion={vistaNavegacion} panelRutaMontado={panelRuta.montado} capaMapa={capaMapa}
        filtroHexagono={filtroHexagono} setFiltroHexagono={setFiltroHexagono} coberturaCapas={coberturaCapas}
        nivelesActivos={nivelesActivos} toggleNivel={toggleNivel} conteos={conteos}
        hayFiltrosApagados={hayFiltrosApagados} restablecerFiltros={restablecerFiltros}
        capaInseguridad={capaInseguridad} conteosInseguridad={conteosInseguridad}
      />

      {!rutaAbierta && rutasCalculadas.length === 0 && (
        <button className="route-fab panel-enter" style={{ animationDelay: '0.22s' }} onClick={abrirPanelRuta}><Compass size={16} /> <span>Trazar ruta</span></button>
      )}

      <HerramientasMenu
        herramientasAbiertas={herramientasAbiertas} setHerramientasAbiertas={setHerramientasAbiertas}
        pedirUbicacion={pedirUbicacion} buscandoUbicacion={buscandoUbicacion}
        modoViaje={modoViaje} toggleModoViaje={toggleModoViaje}
        vistaNavegacion={vistaNavegacion} setVistaNavegacion={setVistaNavegacion}
        setStatsAbierto={setStatsAbierto} setActividadAbierta={setActividadAbierta} setCapasAbiertas={setCapasAbiertas}
        sesion={sesion}
        onAbrirAyuda={() => { setMostrarOnboarding(true); setHerramientasAbiertas(false) }}
      />

      <ReportSheet
        paso={paso} setPaso={setPaso} setCampoActivo={setCampoActivo}
        panelRutaMontado={panelRuta.montado} iniciarReporte={iniciarReporte}
        ubicacionReporte={ubicacionReporte} confirmarReporte={confirmarReporte}
      />
    </div>
  )
}

export default App

