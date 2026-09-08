import { useState, useEffect, useMemo, useRef } from 'react'
import './App.css'

import {
  Search, X, MapPin, ArrowUpDown, Home, Save, Briefcase, LocateFixed, Pencil, Zap, Scale,
  ShieldCheck, CircleCheck, TriangleAlert, Share2, Compass, Bike, Box, BarChart3, Wrench, WifiOff,
  Siren, ShieldAlert, Layers, Navigation, Square, Volume2, VolumeX, Gauge,
} from 'lucide-react'

import {
  CENTRO_GBA, UMBRAL_CRUCE_KM, UMBRAL_ALERTA_KM, ORDEN_NIVELES, PESO_RIESGO,
  API_URL, CLAVE_AUTOR_ID, CLAVE_NIVELES, CLAVE_FAVORITOS, CLAVE_TEMA, CLAVE_ONBOARDING, CLAVE_CAPA_MAPA, NIVELES, CATEGORIAS_REPORTE,
  CLAVE_CAPA_INSEGURIDAD, OPCIONES_CAPA_INSEGURIDAD, NIVELES_INSEGURIDAD_COLOR, CLAVE_CAPA_TRAFICO, UMBRAL_ZOOM_TRAFICO, CLAVE_VOZ,
} from './constants'
import { distanciaKm, calcularAjuste, geocodificar, calcularRumbo, calcularProgresoRuta, distanciaAPolilinea } from './utils/geoRiesgo'
import {
  unificarZonasInseguridad, unificarZonasRiesgo, calcularZonasCruzadasPorRuta, calcularRutasConScore,
} from './utils/riesgoRuta'
import { formatearAntiguedad } from './utils/tiempo'
import { iconoClima, reproducirBeep, textoManiobra, iconoManiobra } from './utils/ui'
import { cargarDeLocalStorage, generarUuidV4Fallback } from './utils/storage'
import { LoadingScreen } from './components/LoadingScreen'
import { Onboarding } from './components/Onboarding'
import { ThemeToggle } from './components/ThemeToggle'
import { CapasPanel } from './components/CapasPanel'
import { MapaMotoSafe } from './components/MapaMotoSafe'
import { useSegundosDesde } from './hooks/useSegundosDesde'

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

// Umbral para considerar que el usuario se desvió de la ruta calculada (no
// que el GPS tembló): más que el ruido normal en calle (~15-30m con buena
// señal), lo bastante chico como para reaccionar rápido si de verdad se
// dobló mal. Se exige, además, que se mantenga por varios fixes seguidos
// (ver DESVIOS_SEGUIDOS_PARA_RECALCULAR) antes de recalcular.
const UMBRAL_DESVIO_RUTA_KM = 0.06
const DESVIOS_SEGUIDOS_PARA_RECALCULAR = 3

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
  const [ZONAS_RIESGO, setZonasRiesgo] = useState([])
  const [corredores, setCorredores] = useState([])
  const [inseguridadGeneral, setInseguridadGeneral] = useState([])
  const [inseguridadMoto, setInseguridadMoto] = useState([])
  const [cargandoHotspots, setCargandoHotspots] = useState(true)
  const [primeraVezListo, setPrimeraVezListo] = useState(false)
  const [backendError, setBackendError] = useState(false)
  const [tema, setTema] = useState(() => cargarDeLocalStorage(CLAVE_TEMA, 'dark'))
  const [capaMapa, setCapaMapa] = useState(() => cargarDeLocalStorage(CLAVE_CAPA_MAPA, 'clusters'))
  const [capaInseguridad, setCapaInseguridad] = useState(() => cargarDeLocalStorage(CLAVE_CAPA_INSEGURIDAD, 'apagado'))
  // Tráfico en vivo (TomTom): apagado por default -- no todos tienen la API key
  // configurada en el backend, y aunque la tengan, no queremos gastar cuota
  // gratuita para usuarios que nunca miraron esta capa.
  const [capaTrafico, setCapaTrafico] = useState(() => cargarDeLocalStorage(CLAVE_CAPA_TRAFICO, false))
  const [traficoNoDisponible, setTraficoNoDisponible] = useState(false)
  // Guía por voz de las maniobras (Web Speech API, nativa del navegador --
  // sin librerías ni claves nuevas). Activada por default: es lo que hace
  // que la app sea usable manejando de verdad, sin tener que mirar la
  // pantalla en cada giro. El toggle queda en "Herramientas".
  const [vozActivada, setVozActivada] = useState(() => cargarDeLocalStorage(CLAVE_VOZ, true))
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
      localStorage.setItem(CLAVE_AUTOR_ID, JSON.stringify(id))
    }
    return id
  })
  const [favoritos, setFavoritos] = useState(() => cargarDeLocalStorage(CLAVE_FAVORITOS, { casa: null, trabajo: null }))
  const [miUbicacion, setMiUbicacion] = useState(null)
  const [buscandoUbicacion, setBuscandoUbicacion] = useState(false)
  const [vuelo, setVuelo] = useState(null)
  const [zonaSeleccionada, setZonaSeleccionada] = useState(null)
  const [zonaResaltada, setZonaResaltada] = useState(null)
  const [clima, setClima] = useState(null)
  const [actividadAbierta, setActividadAbierta] = useState(false)
  const [statsAbierto, setStatsAbierto] = useState(false)
  const [herramientasAbiertas, setHerramientasAbiertas] = useState(false)
  const [capasAbiertas, setCapasAbiertas] = useState(false)
  const [toast, setToast] = useState(null)
  const segundos = useSegundosDesde()

  const [rutaAbierta, setRutaAbierta] = useState(false)
  const [origenTexto, setOrigenTexto] = useState('')
  const [destinoTexto, setDestinoTexto] = useState('')
  const [origenPunto, setOrigenPunto] = useState(null)
  const [destinoPunto, setDestinoPunto] = useState(null)
  const [campoActivo, setCampoActivo] = useState(null)
  const [geocodificando, setGeocodificando] = useState(false)
  const [rutasCalculadas, setRutasCalculadas] = useState([])
  const [rutaSeleccionada, setRutaSeleccionada] = useState(0)
  const [rutaCargando, setRutaCargando] = useState(false)
  const [rutaError, setRutaError] = useState(null)
  const [pasoActual, setPasoActual] = useState(1)

  const [modoViaje, setModoViaje] = useState(false)
  const [vistaNavegacion, setVistaNavegacion] = useState(false)
  const [watchId, setWatchId] = useState(null)
  const [zonasAlertadas, setZonasAlertadas] = useState(new Set())
  const [alertaViaje, setAlertaViaje] = useState(null)
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
  // rumboActual: dirección de movimiento real, no una brújula del
  // dispositivo. Se toma de coords.heading (lo calcula el propio GPS a
  // partir del desplazamiento, igual que Waze/Google Maps mientras estás en
  // movimiento) y si el navegador no lo entrega, se calcula a mano con
  // calcularRumbo() entre el fix anterior y el actual (ver toggleModoViaje).
  // La brújula del dispositivo (DeviceOrientationEvent, con su permiso
  // explícito en iOS) quedaría como mejora aparte para cuando el vehículo
  // está detenido, que es el único caso que esto no cubre.
  const mapaRef = useRef(null)
  const [mapaListo, setMapaListo] = useState(false)
  const [rumboActual, setRumboActual] = useState(0)
  const zoomNavegacionHechoRef = useRef(false)

  useEffect(() => {
    if (vuelo && mapaListo) mapaRef.current?.flyTo({ center: [vuelo.lng, vuelo.lat], zoom: vuelo.zoom || 15, duration: 1400 })
  }, [vuelo, mapaListo])

  useEffect(() => {
    if (!modoViaje) zoomNavegacionHechoRef.current = false
  }, [modoViaje])

  // Seguimiento de cámara en 2D (norte arriba, sin inclinación). Cuando
  // vistaNavegacion está activa, es MapaMotoSafe quien controla la cámara
  // (centro + zoom + pitch + bearing juntos, ver ese componente) para que no
  // compitan los dos por moverla al mismo tiempo.
  useEffect(() => {
    const map = mapaRef.current
    if (!modoViaje || !miUbicacion || !mapaListo || vistaNavegacion || !map) return
    if (!zoomNavegacionHechoRef.current) {
      zoomNavegacionHechoRef.current = true
      map.easeTo({ center: [miUbicacion.lng, miUbicacion.lat], zoom: ZOOM_NAVEGACION, duration: 1200 })
    } else {
      map.panTo([miUbicacion.lng, miUbicacion.lat], { animate: true, duration: 800 })
    }
  }, [modoViaje, miUbicacion, mapaListo, vistaNavegacion])

  // Ahora "real" (no segundos desde el montaje): se usa para calcular antiguedad
  // y opacidad de los reportes colaborativos, se refresca cada 30s (alcanza para
  // el nivel de granularidad de "hace X min" que mostramos).
  const [horaActual, setHoraActual] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setHoraActual(Date.now()), 30000)
    return () => clearInterval(id)
  }, [])

  const mostrarToast = (texto) => {
    setToast(texto)
    setTimeout(() => setToast(null), 2200)
  }

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
        }))
        setZonasRiesgo(zonasFormateadas)
        setCargandoHotspots(false)
        setPrimeraVezListo(true)
        setBackendError(false)
      })
      .catch(() => {
        setBackendError(true)
        setCargandoHotspots(false)
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
      .then((r) => (r.ok ? r.json() : []))
      .then(setCorredores)
      .catch(() => {})
  }, [])

  useEffect(() => {
    // Hotspots de inseguridad (delitos reales del GCBA, no siniestros de moto):
    // dos capas independientes (general / con moto), precalculadas offline
    // igual que corredores. Se cargan una sola vez al montar; son secundarias,
    // el usuario las ve si cambia de capa.
    fetch(`${API_URL}/hotspots-inseguridad?tipo=general`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setInseguridadGeneral)
      .catch(() => {})
    fetch(`${API_URL}/hotspots-inseguridad?tipo=moto`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setInseguridadMoto)
      .catch(() => {})
  }, [])

  const cargarReportes = () => {
    fetch(`${API_URL}/reportes`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => setReportes(data.map((r) => ({
        id: r.id,
        lat: r.lat,
        lng: r.lng,
        categoria: r.categoria,
        autorId: r.autor_id,
        creadoEn: r.creado_en,
      }))))
      .catch(() => { /* backend caido: se mantienen los reportes que ya estaban cargados */ })
  }

  useEffect(() => {
    cargarReportes()
    // Reportes de otros usuarios pueden aparecer sin que este dispositivo haga nada:
    // se refresca cada 30s para que el mapa los muestre sin recargar la pagina.
    const id = setInterval(cargarReportes, 30000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    if (!backendError) return
    const id = setInterval(cargarHotspots, 5000)
    return () => clearInterval(id)
  }, [backendError])

  useEffect(() => {
    fetch(`https://api.open-meteo.com/v1/forecast?latitude=${CENTRO_GBA.lat}&longitude=${CENTRO_GBA.lng}&current_weather=true`)
      .then((r) => r.json())
      .then((data) => setClima(data.current_weather))
      .catch(() => setClima(null))
  }, [])

  useEffect(() => { localStorage.setItem(CLAVE_NIVELES, JSON.stringify([...nivelesActivos])) }, [nivelesActivos])
  useEffect(() => { localStorage.setItem(CLAVE_FAVORITOS, JSON.stringify(favoritos)) }, [favoritos])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', tema)
    localStorage.setItem(CLAVE_TEMA, JSON.stringify(tema))
  }, [tema])
  useEffect(() => {
    localStorage.setItem(CLAVE_CAPA_MAPA, JSON.stringify(capaMapa))
  }, [capaMapa])

  useEffect(() => {
    localStorage.setItem(CLAVE_CAPA_INSEGURIDAD, JSON.stringify(capaInseguridad))
  }, [capaInseguridad])

  useEffect(() => {
    localStorage.setItem(CLAVE_CAPA_TRAFICO, JSON.stringify(capaTrafico))
  }, [capaTrafico])

  useEffect(() => {
    localStorage.setItem(CLAVE_VOZ, JSON.stringify(vozActivada))
  }, [vozActivada])

  useEffect(() => {
    return () => { if (watchId != null) navigator.geolocation.clearWatch(watchId) }
  }, [watchId])

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key !== 'Escape') return
      if (mostrarOnboarding) { cerrarOnboarding(); return }
      if (rutaAbierta) { cerrarTodoRuta(); return }
      if (paso === 'eligiendo') { setPaso('idle'); return }
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

  // Arranca el seguimiento GPS. conVistaNavegacion=true es el camino que usa
  // "Iniciar viaje" desde una ruta ya calculada: además de prender Modo Viaje,
  // deja lista la cámara 3D de una sola vez, sin que el usuario tenga que ir
  // a buscar el toggle de "Vista inclinada" por separado (que es justamente
  // el problema de UX que se pidió resolver -- que la app se acomode sola).
  const activarModoViaje = (conVistaNavegacion = false) => {
    if (!navigator.geolocation) { mostrarToast('Tu navegador no soporta geolocalización'); return }
    const id = navigator.geolocation.watchPosition(
      (pos) => {
        const punto = { lat: pos.coords.latitude, lng: pos.coords.longitude }
        const heading = pos.coords.heading
        if (heading != null && !Number.isNaN(heading)) {
          // El GPS ya viene con rumbo calculado (lo más confiable mientras
          // hay movimiento real, que es el caso normal andando en moto).
          setRumboActual(heading)
        } else {
          // Fallback: sin heading del navegador, lo calculamos a mano contra
          // el fix anterior. Se ignoran desplazamientos chicos (ruido de GPS
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
        // pos.coords.speed viene en m/s y es null en varios navegadores/con
        // poca señal -- se ignora ese caso en vez de mostrar un ETA basado en
        // 0 (que leería como "nunca llegás"), y calcularEtaInfo cae al
        // reparto proporcional por distancia total como fallback.
        if (pos.coords.speed != null && !Number.isNaN(pos.coords.speed) && pos.coords.speed > 0.5) {
          setVelocidadActual(pos.coords.speed)
        }
      },
      () => mostrarToast('No se pudo obtener tu ubicación en vivo'),
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 }
    )
    setWatchId(id)
    setModoViaje(true)
    setZonasAlertadas(new Set())
    if (conVistaNavegacion) setVistaNavegacion(true)
    mostrarToast(conVistaNavegacion ? 'Navegación iniciada' : 'Modo Viaje activado')
  }

  const desactivarModoViaje = () => {
    if (watchId != null) navigator.geolocation.clearWatch(watchId)
    setWatchId(null)
    setModoViaje(false)
    setVistaNavegacion(false)
    setRumboActual(0)
    setVelocidadActual(null)
    setZonasAlertadas(new Set())
    setAlertaViaje(null)
    mostrarToast('Modo Viaje desactivado')
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

  const iniciarReporte = () => {
    if (paso === 'eligiendo' || paso === 'buscando') { setPaso('idle'); return }
    setPaso('buscando')
    const usar = (punto) => {
      setUbicacionReporte(punto)
      setVuelo({ ...punto, zoom: 15 })
      setPaso('eligiendo')
    }
    if (!navigator.geolocation) {
      usar({ lat: CENTRO_GBA.lat + (Math.random() - 0.5) * 0.1, lng: CENTRO_GBA.lng + (Math.random() - 0.5) * 0.1 })
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => usar({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => usar({ lat: CENTRO_GBA.lat + (Math.random() - 0.5) * 0.1, lng: CENTRO_GBA.lng + (Math.random() - 0.5) * 0.1 }),
      { timeout: 6000 }
    )
  }

  const confirmarReporte = (categoria) => {
    const nuevo = { lat: ubicacionReporte.lat, lng: ubicacionReporte.lng, categoria, autor_id: autorId }
    setPaso('idle')
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
          autorId: creado.autor_id,
          creadoEn: creado.creado_en,
        }, ...prev])
        mostrarToast('Reporte enviado — gracias por sumar el dato')
      })
      .catch(() => mostrarToast('No se pudo enviar el reporte (¿backend caído?)'))
  }

  const borrarReportes = () => {
    fetch(`${API_URL}/reportes?autor_id=${encodeURIComponent(autorId)}`, { method: 'DELETE' })
      .then(() => setReportes((prev) => prev.filter((r) => r.autorId !== autorId)))
      .catch(() => mostrarToast('No se pudo borrar (¿backend caído?)'))
    setActividadAbierta(false)
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
  const clicMapa = (punto) => {
    if (campoActivo === 'origen') { setOrigenPunto(punto); setOrigenTexto('Punto marcado en el mapa') }
    if (campoActivo === 'destino') { setDestinoPunto(punto); setDestinoTexto('Punto marcado en el mapa') }
    setCampoActivo(null)
  }

  const usarFavorito = (fav) => { setDestinoTexto(fav.texto); setDestinoPunto(fav.punto) }
  const guardarFavorito = async (clave, label) => {
    let punto = destinoPunto
    if (!punto) {
      punto = await geocodificar(destinoTexto)
      if (!punto) { mostrarToast(`No pudimos ubicar "${destinoTexto}" para guardarlo`); return }
    }
    setFavoritos((prev) => ({ ...prev, [clave]: { texto: destinoTexto, punto } }))
    mostrarToast(`${label} guardado`)
  }

  const buscarRuta = async () => {
    setRutaError(null)
    if (!origenTexto.trim() || !destinoTexto.trim()) { setRutaError('Completá origen y destino.'); return }
    setGeocodificando(true)
    try {
      let a = origenPunto
      let b = destinoPunto
      if (!a) a = await geocodificar(origenTexto)
      if (!b) b = await geocodificar(destinoTexto)
      if (!a) { setRutaError(`No encontramos "${origenTexto}". Probá con más detalle (ej: "Av. Rivadavia 1200, Ramos Mejía").`); setGeocodificando(false); return }
      if (!b) { setRutaError(`No encontramos "${destinoTexto}". Probá con más detalle.`); setGeocodificando(false); return }
      setGeocodificando(false)
      setRutaAbierta(false)
      await calcularRuta(a, b)
    } catch {
      setGeocodificando(false)
      setRutaError('Error buscando las direcciones. Probá de nuevo.')
    }
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
    () => reportes.filter((r) => r.autorId === autorId),
    [reportes, autorId]
  )

  const zonasAjustadas = useMemo(() => {
    return ZONAS_RIESGO.map((z) => ({ ...z, ajuste: calcularAjuste(z, clima?.weathercode, reportes) }))
  }, [ZONAS_RIESGO, clima, reportes])

  // La lógica de unificación de ejes de riesgo vive en utils/riesgoRuta.js
  // (funciones puras, testeadas aparte). nivel ya viene en la misma escala
  // ordinal en los tres casos (percentiles calculados dentro de cada
  // dataset), asi que sumar PESO_RIESGO entre tipos es valido.
  const zonasInseguridadUnificadas = useMemo(
    () => unificarZonasInseguridad(inseguridadGeneral, inseguridadMoto, new Date(horaActual).getHours()),
    [inseguridadGeneral, inseguridadMoto, horaActual]
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

  useEffect(() => {
    if (!modoViaje || !miUbicacion || rutasCalculadas.length === 0) return
    const pasos = rutasCalculadas[rutaSeleccionada]?.pasos || []
    if (pasoActual >= pasos.length) return
    const objetivo = pasos[pasoActual]
    if (distanciaKm(miUbicacion, objetivo) <= 0.03) {
      // Reaccion a un cambio de posicion GPS (sistema externo), no estado derivado.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPasoActual((p) => Math.min(p + 1, pasos.length - 1))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [miUbicacion, modoViaje])

  // --- guía por voz de las maniobras (Web Speech API) -----------------------
  // Es el hueco más grande que tenía la app para el caso de uso real (andar
  // en moto): sin audio, cada giro exige mirar la pantalla, que es
  // exactamente lo que no se puede hacer manejando. ultimoPasoHabladoRef
  // evita repetir el mismo aviso en cada re-render/fix de GPS que no
  // adelantó el paso.
  const ultimoPasoHabladoRef = useRef(-1)
  // Un reroute automático (ver más abajo) resetea pasoActual a 1 igual que
  // una ruta nueva -- sin esto, si el paso 1 de la ruta VIEJA ya se había
  // hablado, la nueva instrucción del paso 1 de la ruta RECALCULADA se
  // saltearía por tener el mismo índice.
  useEffect(() => { ultimoPasoHabladoRef.current = -1 }, [rutasCalculadas])
  useEffect(() => {
    if (!modoViaje) { ultimoPasoHabladoRef.current = -1; return }
    if (!vozActivada || !('speechSynthesis' in window)) return
    const pasos = rutasCalculadas[rutaSeleccionada]?.pasos || []
    const pasoActivo = pasos[pasoActual]
    if (!pasoActivo || pasoActual === ultimoPasoHabladoRef.current) return
    ultimoPasoHabladoRef.current = pasoActual
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(textoManiobra(pasoActivo))
    utterance.lang = 'es-AR'
    utterance.rate = 1
    window.speechSynthesis.speak(utterance)
  }, [modoViaje, vozActivada, pasoActual, rutasCalculadas, rutaSeleccionada])

  // Si se desactiva la voz a mitad de una frase, corta ahí -- no tiene
  // sentido que siga hablando después de que el usuario la apagó.
  useEffect(() => {
    if (!vozActivada && 'speechSynthesis' in window) window.speechSynthesis.cancel()
  }, [vozActivada])

  // --- detección de desvío + reroute automático -----------------------------
  // Hasta ahora, si te equivocabas de calle en plena navegación, la ruta se
  // quedaba "colgada" con instrucciones que ya no aplicaban -- había que
  // cortar el viaje y trazar todo de nuevo a mano. Waze/Maps recalculan
  // solos; esto hace lo mismo, con la ruta ya calculada por el backend
  // (misma función que arma la ruta inicial) contra el mismo destino.
  const desviosSeguidosRef = useRef(0)
  const rerouteEnCursoRef = useRef(false)
  useEffect(() => {
    if (!modoViaje) { desviosSeguidosRef.current = 0; return }
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
    () => calcularRutasConScore(rutasCalculadas, zonasCruzadasPorRuta),
    [rutasCalculadas, zonasCruzadasPorRuta]
  )

  const idxMasRapida = useMemo(() => {
    if (rutasConScore.length === 0) return 0
    return rutasConScore.reduce((best, r, i) => (r.min < rutasConScore[best].min ? i : best), 0)
  }, [rutasConScore])

  const idxMasSegura = useMemo(() => {
    if (rutasConScore.length === 0) return 0
    return rutasConScore.reduce((best, r, i) => (r.riesgo < rutasConScore[best].riesgo ? i : best), 0)
  }, [rutasConScore])

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

  const etaInfo = useMemo(() => {
    if (!progresoRuta) return null
    const ruta = rutasConScore[rutaSeleccionada]
    if (!ruta) return null
    // Con velocidad GPS real disponible, el tiempo restante sale del ritmo
    // actual (más fiel si vas parado en un semáforo o zafando de tráfico).
    // Sin eso, repartimos el tiempo total de la ruta en proporción a la
    // distancia que falta -- una aproximación razonable, no exacta.
    const minRestante = velocidadActual
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

  const referencia = miUbicacion || CENTRO_GBA
  const cercanas = useMemo(() => {
    return [...zonasFiltradas]
      .map((z) => ({ ...z, distancia: distanciaKm(referencia, z) }))
      .sort((a, b) => a.distancia - b.distancia)
      .slice(0, 4)
  }, [zonasFiltradas, referencia])

  const compartirRuta = async () => {
    const r = rutasConScore[rutaSeleccionada]
    const cruces = zonasCruzadasPorRuta[rutaSeleccionada]?.length || 0
    const texto = `🏍️ MotoSafe GBA\nEn camino: ${r.km} km, ~${r.min} min.\n${cruces === 0 ? 'Ruta sin zonas de riesgo registradas.' : `Cruza ${cruces} zona(s) de riesgo.`}`
    if (navigator.share) {
      try { await navigator.share({ title: 'Mi ruta en MotoSafe GBA', text: texto }) } catch { /* usuario canceló */ }
    } else if (navigator.clipboard) {
      await navigator.clipboard.writeText(texto)
      mostrarToast('Ruta copiada al portapapeles')
    }
  }

  const hayFiltrosApagados = nivelesActivos.size < Object.keys(NIVELES).length
  const mostrarAlerta = criticosVisibles > 0 && criticosVisibles <= 5 && misReportes.length === 0 && rutasCalculadas.length === 0
  let textoTopbar
  if (modoViaje) textoTopbar = 'Modo Viaje · siguiendo tu ubicación'
  else if (rutasCalculadas.length > 0) textoTopbar = `Ruta: ${rutasCalculadas[rutaSeleccionada].km} km · ${rutasCalculadas[rutaSeleccionada].min} min`
  else if (cargandoHotspots) textoTopbar = 'Conectando con el servidor de datos...'
  else if (misReportes.length > 0) textoTopbar = `${misReportes.length} reporte${misReportes.length > 1 ? 's' : ''} tuyo${misReportes.length > 1 ? 's' : ''} · hace ${segundos}s`
  else if (mostrarAlerta) textoTopbar = `${criticosVisibles} zona${criticosVisibles > 1 ? 's' : ''} crítica${criticosVisibles > 1 ? 's' : ''} visible${criticosVisibles > 1 ? 's' : ''}`
  else textoTopbar = `${zonasFiltradas.length} zonas registradas · hace ${segundos}s`

  const climaInfo = clima ? iconoClima(clima.weathercode) : null

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

      <header className="topbar">
        <div className="brand">
          <span className="brand-dot" />
          <span className="brand-name">MotoSafe</span>
          <span className="brand-badge">GBA</span>
        </div>
        <div className="topbar-right">
          {/* En navegación se saca todo lo que no es la información de viaje
              en sí -- tema, capas y clima son decisiones de exploración, no
              algo que se toque manejando. Menos chrome arriba también le
              deja más aire vertical a la tarjeta de próximo giro. */}
          {!vistaNavegacion && <ThemeToggle tema={tema} onCambiar={toggleTema} />}
          {!vistaNavegacion && (
            <button
              className={`capa-toggle ${capaInseguridad !== 'apagado' || capaMapa !== 'clusters' ? 'capas-con-cambios' : ''}`}
              onClick={() => setCapasAbiertas((v) => !v)}
              aria-label="Capas del mapa"
              title="Capas del mapa"
            >
              <Layers size={15} />
            </button>
          )}
          {climaInfo && !vistaNavegacion && (
            <div className="clima-badge" title={climaInfo.label}>
              <climaInfo.Icon size={13} /> {Math.round(clima.temperature)}°C
            </div>
          )}
          <div
            className={`topbar-status ${mostrarAlerta ? 'alerta' : ''} ${modoViaje ? 'viaje' : ''} ${misReportes.length > 0 ? 'clickeable' : ''}`}
            onClick={() => { if (misReportes.length > 0) { setActividadAbierta((v) => !v); setCapasAbiertas(false) } }}
          >
            <span className="status-dot" />
            {textoTopbar}
          </div>
        </div>
      </header>

      {capasAbiertas && (
        <CapasPanel
          capaMapa={capaMapa}
          onCambiarCapaMapa={setCapaMapa}
          capaInseguridad={capaInseguridad}
          onCambiarCapaInseguridad={setCapaInseguridad}
          capaTrafico={capaTrafico}
          onCambiarCapaTrafico={(v) => {
            if (v && traficoNoDisponible) { mostrarToast('Tráfico en vivo no disponible ahora'); return }
            setCapaTrafico(v)
          }}
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
            <span className="navegacion-icono"><ManiobraIcon size={24} /></span>
            <div className="navegacion-texto">
              <strong>{textoManiobra(pasoActivo)}</strong>
              {miUbicacion && (
                <span className="navegacion-distancia">
                  {Math.round(distanciaKm(miUbicacion, pasoActivo) * 1000)} m
                </span>
              )}
              {/* Preview del giro siguiente, más chico -- ayuda en cruces
                  seguidos a no quedar "ciego" un paso adelante, que era el
                  caso hasta ahora (solo se veía el giro inmediato). */}
              {pasoSiguiente && (
                <span className="navegacion-siguiente">
                  Después: {textoManiobra(pasoSiguiente)}
                </span>
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

      {backendError && (
        <div className="ruta-banner ruta-banner-error panel-enter backend-banner">
          <WifiOff size={14} /> Sin conexión con el backend (localhost:8000). Reintentando cada 5s.
          <button onClick={cargarHotspots}>Reintentar ahora</button>
        </div>
      )}

      {capaTrafico && !traficoNoDisponible && zoomActual < UMBRAL_ZOOM_TRAFICO && (
        <div className="ruta-banner panel-enter">
          <Zap size={14} /> Acercate para ver el tráfico en detalle
        </div>
      )}

      {actividadAbierta && misReportes.length > 0 && (
        <div className="actividad-panel panel-enter hazard-edge">
          <div className="actividad-header">
            <span className="cercanas-title">Actividad reciente</span>
            <button className="detalle-cerrar" onClick={() => setActividadAbierta(false)} aria-label="Cerrar panel de actividad"><X size={14} /></button>
          </div>
          {misReportes.map((rep) => {
            const cat = CATEGORIAS_REPORTE.find((c) => c.id === rep.categoria)
            return (
              <button key={rep.id} className="actividad-item" onClick={() => { setVuelo({ lat: rep.lat, lng: rep.lng, zoom: 16 }); setActividadAbierta(false) }}>
                <span className="actividad-icon">{cat?.Icon && <cat.Icon size={15} />}</span>
                <span className="actividad-texto">
                  <span className="actividad-label">{cat?.label}</span>
                  <span className="actividad-hora">{formatearAntiguedad(rep.creadoEn, horaActual)}</span>
                </span>
              </button>
            )
          })}
          <button className="actividad-borrar" onClick={borrarReportes}>Borrar mis reportes</button>
        </div>
      )}

      {statsAbierto && (
        <div className="stats-panel panel-enter hazard-edge">
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

      {/* Se oculta durante la navegación: no solo no hace falta buscar
          mientras estás en camino, sino que en pantalla chica quedaba
          asomando detrás de la tarjeta de "doblá acá" (se veía en las
          capturas que mandaste) -- las dos ocupaban la misma franja
          horizontal arriba. */}
      {!vistaNavegacion && (
        <div className="searchbar panel-enter hazard-edge" style={{ animationDelay: '0.05s' }}>
          <span className="searchbar-icon"><Search size={13} /></span>
          <input type="text" placeholder="Buscar zona o avenida..." value={busqueda} onChange={(e) => setBusqueda(e.target.value)} aria-label="Buscar zona o avenida" />
          {busqueda && <button className="searchbar-clear" onClick={() => setBusqueda('')} aria-label="Limpiar búsqueda"><X size={12} /></button>}
        </div>
      )}

      {rutaAbierta && (
        <div className="ruta-form panel-enter hazard-edge">
          <div className="ruta-form-fila">
            <span className="ruta-form-punto ruta-form-punto-origen" />
            <input placeholder="Origen" value={origenTexto} onChange={(e) => { setOrigenTexto(e.target.value); setOrigenPunto(null) }} aria-label="Origen de la ruta" />
            <button className={`ruta-form-pin ${campoActivo === 'origen' ? 'activo' : ''}`} title="Marcar en el mapa" aria-label="Marcar origen en el mapa" onClick={() => marcarEnMapa('origen')}><MapPin size={14} /></button>
          </div>
          <button className="ruta-form-swap" onClick={intercambiar} title="Intercambiar" aria-label="Intercambiar origen y destino"><ArrowUpDown size={13} /></button>
          <div className="ruta-form-fila">
            <span className="ruta-form-punto ruta-form-punto-destino" />
            <input placeholder="Destino" value={destinoTexto} onChange={(e) => { setDestinoTexto(e.target.value); setDestinoPunto(null) }} aria-label="Destino de la ruta" />
            <button className={`ruta-form-pin ${campoActivo === 'destino' ? 'activo' : ''}`} title="Marcar en el mapa" aria-label="Marcar destino en el mapa" onClick={() => marcarEnMapa('destino')}><MapPin size={14} /></button>
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
            <button className="ruta-form-buscar" onClick={buscarRuta} disabled={geocodificando}>
              {geocodificando ? <span className="spinner" /> : 'Buscar ruta'}
            </button>
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
        <MapaMotoSafe
          tema={tema}
          centro={CENTRO_GBA}
          zoomInicial={11}
          onZoomChange={setZoomActual}
          onReady={(map) => { mapaRef.current = map; setMapaListo(true) }}
          apiUrl={API_URL}
          capaTrafico={capaTrafico}
          onTraficoEstado={(disponible) => setTraficoNoDisponible(!disponible)}
          campoActivo={campoActivo}
          onClickMapa={clicMapa}
          zonasFiltradas={zonasFiltradas}
          zonaResaltada={zonaResaltada}
          zonasCruzadasIds={zonasCruzadasIds}
          onClickZona={(zona) => { setZonaSeleccionada(zona); setCapasAbiertas(false) }}
          atenuarFondo={atenuarFondo}
          capaMapa={capaMapa}
          corredoresFiltrados={corredoresFiltrados}
          capaInseguridad={capaInseguridad}
          inseguridadFiltrada={capaInseguridad === 'moto' ? inseguridadMotoFiltrada : inseguridadGeneralFiltrada}
          reportes={reportes}
          autorId={autorId}
          horaActual={horaActual}
          rutasCalculadas={rutasCalculadas}
          rutaSeleccionada={rutaSeleccionada}
          onClickRuta={setRutaSeleccionada}
          origenPunto={origenPunto}
          destinoPunto={destinoPunto}
          miUbicacion={miUbicacion}
          vistaNavegacion={vistaNavegacion}
          rumboActual={rumboActual}
          progresoRutaIndice={progresoRuta?.indiceCercano ?? null}
        />
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
      {rutasCalculadas.length > 0 && !modoViaje && (
        <div className="ruta-resumen panel-enter hazard-edge">
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
              <button className={rutaSeleccionada === idxMasSegura ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxMasSegura)}><ShieldCheck size={12} /> Segura</button>
            </div>
          )}
          {rutasConScore.map((r, i) => (
            <button key={i} className={`ruta-opcion ${i === rutaSeleccionada ? 'activa' : ''}`} onClick={() => setRutaSeleccionada(i)}>
              <span className="ruta-opcion-num">
                Ruta {i + 1}
                {i === idxMasRapida && i === idxMasSegura && <span className="ruta-opcion-badge badge-ambas"><Zap size={10} /><ShieldCheck size={10} /> recomendada</span>}
                {i === idxMasRapida && i !== idxMasSegura && <span className="ruta-opcion-badge badge-rapida"><Zap size={10} /> rápida</span>}
                {i === idxMasSegura && i !== idxMasRapida && <span className="ruta-opcion-badge badge-segura"><ShieldCheck size={10} /> segura</span>}
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
              <span className={`ruta-opcion-riesgo ${r.riesgo === 0 ? 'ok' : r.riesgo <= 3 ? 'warn' : 'alto'}`}>
                {r.riesgo === 0
                  ? <><CircleCheck size={12} /> sin cruces</>
                  : <><TriangleAlert size={12} /> riesgo {NIVELES[r.nivelMaximo]?.label.toLowerCase()}</>}
              </span>
              {r.riesgo > 0 && (
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
          {zonasCruzadasOrdenadas.length > 0 && (
            <div className="ruta-resumen-detalle">
              {zonasCruzadasOrdenadas.slice(0, 6).map((z) => (
                <div key={z.id} className="ruta-resumen-item">
                  <span className="cercanas-dot" style={{ background: NIVELES[z.nivel].color }} />
                  {z.tipoRiesgo === 'inseguridad' ? <ShieldAlert size={11} className="ruta-resumen-icono" /> : <Siren size={11} className="ruta-resumen-icono" />}
                  {z.nombre}
                </div>
              ))}
              {zonasCruzadasOrdenadas.length > 6 && (
                <p className="ruta-resumen-mas">+ {zonasCruzadasOrdenadas.length - 6} zonas más de menor riesgo</p>
              )}
            </div>
          )}
          <button className="ruta-resumen-iniciar" onClick={iniciarNavegacionRuta}>
            <Navigation size={15} /> Iniciar viaje
          </button>
          <div className="ruta-resumen-acciones-finales">
            <button className="ruta-resumen-compartir" onClick={compartirRuta}><Share2 size={13} /> Compartir</button>
            <button className="ruta-resumen-nueva" onClick={cerrarTodoRuta}>Nueva ruta</button>
          </div>
        </div>
      )}

      {/* Tira mínima de navegación activa: reemplaza al panel completo de
          arriba mientras hay ruta + Modo Viaje. Es la barra de "cuánto
          falta" que le faltaba a la app -- antes, una vez que arrancabas a
          navegar, no había NINGÚN indicador de progreso del viaje. */}
      {rutasCalculadas.length > 0 && modoViaje && (
        <div className="nav-resumen-mini panel-enter">
          <div className="nav-resumen-mini-datos">
            <strong>{etaInfo ? etaInfo.distanciaRestanteKm.toFixed(1) : rutasConScore[rutaSeleccionada]?.km} km</strong>
            <span className="nav-resumen-mini-sep">·</span>
            <strong>{etaInfo ? etaInfo.minRestante : rutasConScore[rutaSeleccionada]?.min} min</strong>
            {etaInfo && <span className="nav-resumen-mini-llegada">llegás {etaInfo.horaLlegada}</span>}
          </div>
          <button className="nav-resumen-mini-detener" onClick={desactivarModoViaje} aria-label="Detener navegación">
            <Square size={13} />
          </button>
        </div>
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

      {rutasCalculadas.length === 0 && !rutaAbierta && zonaSeleccionada && (
        <div className="detalle-panel panel-enter hazard-edge">
          <button className="detalle-cerrar" onClick={() => setZonaSeleccionada(null)} aria-label="Cerrar detalle de zona"><X size={14} /></button>
          <span className="popup-nivel" style={{ color: NIVELES[zonaSeleccionada.ajuste.nivel].color }}>
            Riesgo {NIVELES[zonaSeleccionada.ajuste.nivel].label}
          </span>
          <strong className="detalle-nombre">{zonaSeleccionada.nombre}</strong>
          <p className="detalle-motivo">{zonaSeleccionada.motivo}</p>
          {zonaSeleccionada.prediccionModelo && (
            <div className="detalle-modelo">
              <span className="detalle-modelo-titulo">Salida del modelo, ahora mismo</span>
              {Object.entries(zonaSeleccionada.prediccionModelo).map(([clase, prob]) => (
                <div className="detalle-modelo-fila" key={clase}>
                  <span className="detalle-modelo-label">{clase}</span>
                  <div className="detalle-modelo-track">
                    <div className="detalle-modelo-fill" style={{ width: `${prob * 100}%`, background: COLOR_CLASE_MODELO[clase] || '#8A9099' }} />
                  </div>
                  <span className="detalle-modelo-num">{Math.round(prob * 100)}%</span>
                </div>
              ))}
              {zonaSeleccionada.contextoEstimado && (
                <p className="detalle-modelo-nota">Esta zona no tiene perfil histórico propio: se usó el perfil promedio de la ciudad.</p>
              )}
            </div>
          )}
          {zonaSeleccionada.ajuste.subio && (
            <div className="detalle-ajuste">
              <span className="detalle-ajuste-base">Base: {NIVELES[zonaSeleccionada.nivel].label}</span>
              <span className="detalle-ajuste-flecha">→</span>
              <span className="detalle-ajuste-ahora" style={{ color: NIVELES[zonaSeleccionada.ajuste.nivel].color }}>
                Ahora: {NIVELES[zonaSeleccionada.ajuste.nivel].label}
              </span>
              <p className="detalle-ajuste-motivo">Subió por: {zonaSeleccionada.ajuste.motivos.join(' + ')}</p>
            </div>
          )}
        </div>
      )}

      {rutasCalculadas.length === 0 && !rutaAbierta && !zonaSeleccionada && !actividadAbierta && !statsAbierto && !capasAbiertas && (
        <div className="cercanas-panel panel-enter hazard-edge" style={{ animationDelay: '0.15s' }}>
          <span className="cercanas-title">Zonas cercanas {miUbicacion ? '· a vos' : '· al centro del GBA'}</span>
          {cargandoHotspots && <p className="cercanas-empty">Cargando...</p>}
          {!cargandoHotspots && cercanas.length === 0 && <p className="cercanas-empty">Sin resultados</p>}
          {cercanas.map((z) => (
            <button key={z.id} className="cercanas-item" onClick={() => setVuelo({ lat: z.lat, lng: z.lng, zoom: 15 })}>
              <span className="cercanas-dot" style={{ background: NIVELES[z.ajuste.nivel].color }} />
              <span className="cercanas-nombre">{z.nombre}</span>
              <span className="cercanas-km">{z.distancia.toFixed(1)} km</span>
            </button>
          ))}
        </div>
      )}

      {!vistaNavegacion && (
        <div className="legend panel-enter hazard-edge" style={{ animationDelay: '0.2s' }}>
          <div className="legend-header">
            <span className="legend-title">Nivel de riesgo <em>(tocá para filtrar)</em></span>
            {hayFiltrosApagados && <button className="legend-reset" onClick={restablecerFiltros}>Restablecer</button>}
          </div>
          {Object.entries(NIVELES).map(([key, val]) => (
            <button key={key} className={`legend-item ${nivelesActivos.has(key) ? '' : 'inactive'}`} onClick={() => toggleNivel(key)}>
              <span className="legend-swatch" style={{ background: val.color }} />
              {val.label}
              <span className="legend-count">{conteos[key]}</span>
            </button>
          ))}
        </div>
      )}

      {capaInseguridad !== 'apagado' && !vistaNavegacion && (
        <div className="legend legend-inseguridad panel-enter hazard-edge" style={{ animationDelay: '0.22s' }}>
          <div className="legend-header">
            <span className="legend-title">{OPCIONES_CAPA_INSEGURIDAD.find((o) => o.id === capaInseguridad)?.label} <em>(datos GCBA)</em></span>
          </div>
          {Object.entries(NIVELES).map(([key, val]) => (
            <button key={key} className={`legend-item ${nivelesActivos.has(key) ? '' : 'inactive'}`} onClick={() => toggleNivel(key)}>
              <span className="legend-swatch" style={{ background: NIVELES_INSEGURIDAD_COLOR[key] }} />
              {val.label}
              <span className="legend-count">{conteosInseguridad[key]}</span>
            </button>
          ))}
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
            <button className={vozActivada ? 'activo' : ''} onClick={() => setVozActivada((v) => !v)}>
              {vozActivada ? <Volume2 size={15} /> : <VolumeX size={15} />} Guía por voz {vozActivada ? '· activa' : '· silenciada'}
            </button>
            <button onClick={() => { setStatsAbierto(true); setHerramientasAbiertas(false); setActividadAbierta(false); setCapasAbiertas(false) }}>
              <BarChart3 size={15} /> Estadísticas
            </button>
          </div>
        )}
        <button
          className={`herramientas-fab ${herramientasAbiertas ? 'activo' : ''}`}
          onClick={() => setHerramientasAbiertas((v) => !v)}
          aria-label="Más herramientas"
        >
          {herramientasAbiertas ? <X size={18} /> : <Wrench size={18} />}
        </button>
      </div>

      <button className={`report-fab panel-enter ${paso !== 'idle' ? 'active' : ''}`} style={{ animationDelay: '0.3s' }} onClick={iniciarReporte}>
        {paso === 'buscando' ? <span className="spinner" /> : paso === 'eligiendo' ? <X size={16} /> : <TriangleAlert size={16} />}
        <span>{paso === 'buscando' ? 'Ubicando...' : paso === 'eligiendo' ? 'Cancelar' : 'Reportar'}</span>
      </button>

      {paso === 'eligiendo' && (
        <div className="report-sheet hazard-edge">
          <h3>¿Qué estás viendo en la vía?</h3>
          <div className="report-options">
            {CATEGORIAS_REPORTE.map((cat) => (
              <button key={cat.id} onClick={() => confirmarReporte(cat.id)}><cat.Icon size={15} /> {cat.label}</button>
            ))}
          </div>
          <p className="report-hint"><MapPin size={12} /> Ubicación tomada por GPS del dispositivo.</p>
        </div>
      )}
    </div>
  )
}

export default App
