import { useState, useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap, useMapEvents } from 'react-leaflet'
import MarkerClusterGroup from 'react-leaflet-cluster'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import './App.css'

const CENTRO_GBA = { lat: -34.62, lng: -58.44 }
const UMBRAL_CRUCE_KM = 0.6
const UMBRAL_REPORTE_KM = 0.5
const ORDEN_NIVELES = ['bajo', 'medio', 'alto', 'critico']
const PESO_RIESGO = { bajo: 1, medio: 2, alto: 3, critico: 5 }
const BBOX_GBA = '-59.5,-33.9,-57.8,-35.3'
const API_URL = 'http://localhost:8000'
const CLAVE_REPORTES = 'motosafe_reportes'
const CLAVE_NIVELES = 'motosafe_niveles_activos'

const NIVELES = {
  bajo:    { label: 'Bajo',    color: '#3DDC84' },
  medio:   { label: 'Medio',   color: '#FFD23F' },
  alto:    { label: 'Alto',    color: '#FF8C42' },
  critico: { label: 'Crítico', color: '#FF3B3B' },
}

const CODIGOS_LLUVIA = [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99]

const CATEGORIAS_REPORTE = [
  { id: 'pavimento', label: 'Pavimento en mal estado', icon: '🕳️' },
  { id: 'corte', label: 'Corte o desvío', icon: '🚧' },
  { id: 'iluminacion', label: 'Falta de iluminación', icon: '💡' },
  { id: 'inseguro', label: 'Zona insegura', icon: '⚠️' },
]

function distanciaKm(a, b) {
  const R = 6371
  const dLat = (b.lat - a.lat) * Math.PI / 180
  const dLng = (b.lng - a.lng) * Math.PI / 180
  const lat1 = a.lat * Math.PI / 180
  const lat2 = b.lat * Math.PI / 180
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

function distanciaAPolilinea(punto, coords) {
  let min = Infinity
  for (const [lat, lng] of coords) {
    const d = distanciaKm(punto, { lat, lng })
    if (d < min) min = d
  }
  return min
}

function calcularAjuste(zona, climaCode, reportes) {
  let idx = ORDEN_NIVELES.indexOf(zona.nivel)
  const motivos = []
  const esLluvia = climaCode != null && CODIGOS_LLUVIA.includes(climaCode)
  if (esLluvia && idx < 3) { idx += 1; motivos.push('lluvia actual') }
  const reportesCercanos = reportes.filter((r) => distanciaKm(zona, r) <= UMBRAL_REPORTE_KM).length
  if (reportesCercanos > 0 && idx < 3) { idx += 1; motivos.push(`${reportesCercanos} reporte${reportesCercanos > 1 ? 's' : ''} tuyo${reportesCercanos > 1 ? 's' : ''} cerca`) }
  return { nivel: ORDEN_NIVELES[idx], subio: idx > ORDEN_NIVELES.indexOf(zona.nivel), motivos, reportesCercanos }
}

function iconoClima(code) {
  if (code === 0) return { icon: '☀️', label: 'Despejado' }
  if ([1, 2, 3].includes(code)) return { icon: '⛅', label: 'Parcialmente nublado' }
  if ([45, 48].includes(code)) return { icon: '🌫️', label: 'Niebla' }
  if ([51, 53, 55, 56, 57].includes(code)) return { icon: '🌦️', label: 'Llovizna' }
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return { icon: '🌧️', label: 'Lluvia' }
  if ([71, 73, 75, 77, 85, 86].includes(code)) return { icon: '❄️', label: 'Nieve' }
  if ([95, 96, 99].includes(code)) return { icon: '⛈️', label: 'Tormenta' }
  return { icon: '🌡️', label: 'Sin datos' }
}

async function geocodificar(texto) {
  const q = encodeURIComponent(`${texto}, Buenos Aires, Argentina`)
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${q}&viewbox=${BBOX_GBA}&bounded=1&limit=1`
  const res = await fetch(url, { headers: { 'Accept-Language': 'es' } })
  const data = await res.json()
  if (!data || data.length === 0) return null
  return {
    lat: parseFloat(data[0].lat),
    lng: parseFloat(data[0].lon),
    label: data[0].display_name.split(',').slice(0, 2).join(','),
  }
}

function crearIconoCluster(cluster) {
  const count = cluster.getChildCount()
  const hijos = cluster.getAllChildMarkers()
  const tieneCritico = hijos.some((m) => m.options.nivelData === 'critico')
  const size = count < 10 ? 34 : count < 30 ? 42 : 50
  return L.divIcon({
    html: `<div class="cluster-bubble ${tieneCritico ? 'cluster-critico' : ''}" style="width:${size}px;height:${size}px;line-height:${size}px;">${count}</div>`,
    className: 'cluster-icon-wrapper',
    iconSize: L.point(size, size),
  })
}

function VueloControlado({ destino }) {
  const map = useMap()
  useEffect(() => {
    if (destino) map.flyTo([destino.lat, destino.lng], destino.zoom || 15, { duration: 1.4, easeLinearity: 0.15 })
  }, [destino, map])
  return null
}

function ControlesZoom() {
  const map = useMap()
  return (
    <div className="zoom-controls panel-enter" style={{ animationDelay: '0.1s' }}>
      <button onClick={() => map.zoomIn(0.5)} aria-label="Acercar mapa">+</button>
      <button onClick={() => map.zoomOut(0.5)} aria-label="Alejar mapa">−</button>
    </div>
  )
}

function ClicksDeMapa({ campoActivo, onClick }) {
  useMapEvents({
    click(e) {
      if (campoActivo) onClick({ lat: e.latlng.lat, lng: e.latlng.lng })
    },
  })
  return null
}

function EscalaMapa() {
  const map = useMap()
  const [texto, setTexto] = useState('')
  useEffect(() => {
    const actualizar = () => {
      const centro = map.getCenter()
      const zoom = map.getZoom()
      const metrosPorPixel = 156543.03392 * Math.cos((centro.lat * Math.PI) / 180) / Math.pow(2, zoom)
      const metros = metrosPorPixel * 80
      const pasos = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
      const cercano = pasos.reduce((prev, curr) => (Math.abs(curr - metros) < Math.abs(prev - metros) ? curr : prev))
      setTexto(cercano >= 1000 ? `${cercano / 1000} km` : `${cercano} m`)
    }
    actualizar()
    map.on('zoomend moveend', actualizar)
    return () => map.off('zoomend moveend', actualizar)
  }, [map])
  return (
    <div className="escala-mapa">
      <div className="escala-linea" />
      <span>{texto}</span>
    </div>
  )
}

function useSegundosDesde() {
  const [segundos, setSegundos] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setSegundos((s) => s + 1), 1000)
    return () => clearInterval(id)
  }, [])
  return segundos
}

function cargarDeLocalStorage(clave, porDefecto) {
  try {
    const guardado = localStorage.getItem(clave)
    return guardado ? JSON.parse(guardado) : porDefecto
  } catch {
    return porDefecto
  }
}

function App() {
  const [ZONAS_RIESGO, setZonasRiesgo] = useState([])
  const [cargandoHotspots, setCargandoHotspots] = useState(true)
  const [backendError, setBackendError] = useState(false)
  const [nivelesActivos, setNivelesActivos] = useState(
    () => new Set(cargarDeLocalStorage(CLAVE_NIVELES, Object.keys(NIVELES)))
  )
  const [busqueda, setBusqueda] = useState('')
  const [paso, setPaso] = useState('idle')
  const [ubicacionReporte, setUbicacionReporte] = useState(null)
  const [reportes, setReportes] = useState(() => cargarDeLocalStorage(CLAVE_REPORTES, []))
  const [miUbicacion, setMiUbicacion] = useState(null)
  const [buscandoUbicacion, setBuscandoUbicacion] = useState(false)
  const [vuelo, setVuelo] = useState(null)
  const [zonaSeleccionada, setZonaSeleccionada] = useState(null)
  const [zonaResaltada, setZonaResaltada] = useState(null)
  const [clima, setClima] = useState(null)
  const [actividadAbierta, setActividadAbierta] = useState(false)
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
          motivo: `${h.cantidad_siniestros} siniestros de motociclistas registrados, ${h.mortales} mortales, ${h.graves} graves.`,
        }))
        setZonasRiesgo(zonasFormateadas)
        setCargandoHotspots(false)
        setBackendError(false)
      })
      .catch(() => {
        setBackendError(true)
        setCargandoHotspots(false)
      })
  }

  useEffect(() => {
    cargarHotspots()
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

  // Persistencia liviana en el propio navegador (no toca el backend).
  useEffect(() => {
    localStorage.setItem(CLAVE_REPORTES, JSON.stringify(reportes))
  }, [reportes])
  useEffect(() => {
    localStorage.setItem(CLAVE_NIVELES, JSON.stringify([...nivelesActivos]))
  }, [nivelesActivos])

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key !== 'Escape') return
      if (rutaAbierta) { cerrarTodoRuta(); return }
      if (paso === 'eligiendo') { setPaso('idle'); return }
      if (zonaSeleccionada) { setZonaSeleccionada(null); return }
      if (actividadAbierta) { setActividadAbierta(false); return }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rutaAbierta, paso, zonaSeleccionada, actividadAbierta])

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
    const nuevo = {
      id: Date.now(), lat: ubicacionReporte.lat, lng: ubicacionReporte.lng, categoria,
      hora: new Date().toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' }),
    }
    setReportes((prev) => [nuevo, ...prev])
    setPaso('idle')
    mostrarToast('✓ Reporte enviado — gracias por sumar el dato')
  }

  const borrarReportes = () => {
    setReportes([])
    setActividadAbierta(false)
    mostrarToast('Reportes de esta sesión borrados')
  }

  const abrirPanelRuta = () => {
    setRutaAbierta(true)
    setZonaSeleccionada(null)
    setActividadAbierta(false)
    setRutasCalculadas([])
    setRutaError(null)
  }
  const cerrarTodoRuta = () => {
    setRutaAbierta(false); setCampoActivo(null)
    setOrigenTexto(''); setDestinoTexto('')
    setOrigenPunto(null); setDestinoPunto(null)
    setRutasCalculadas([]); setRutaSeleccionada(0); setRutaError(null)
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
      const url = `https://router.project-osrm.org/route/v1/driving/${a.lng},${a.lat};${b.lng},${b.lat}?overview=full&geometries=geojson&alternatives=3`
      const res = await fetch(url)
      if (!res.ok) throw new Error('OSRM respondió con error')
      const data = await res.json()
      if (!data.routes || data.routes.length === 0) throw new Error('Sin ruta disponible')
      const rutas = data.routes.map((r) => ({
        coords: r.geometry.coordinates.map(([lng, lat]) => [lat, lng]),
        km: (r.distance / 1000).toFixed(1),
        min: Math.round(r.duration / 60),
      }))
      setRutasCalculadas(rutas)
      setRutaSeleccionada(0)
    } catch {
      setRutaError('No se pudo calcular la ruta (servidor de demo caído o sin conexión). Probá de nuevo.')
    } finally {
      setRutaCargando(false)
    }
  }

  const zonasAjustadas = useMemo(() => {
    return ZONAS_RIESGO.map((z) => ({ ...z, ajuste: calcularAjuste(z, clima?.weathercode, reportes) }))
  }, [ZONAS_RIESGO, clima, reportes])

  const zonasFiltradas = zonasAjustadas.filter(
    (z) => nivelesActivos.has(z.ajuste.nivel) && z.nombre.toLowerCase().includes(busqueda.toLowerCase())
  )
  const criticosVisibles = zonasFiltradas.filter((z) => z.ajuste.nivel === 'critico').length

  useEffect(() => {
    if (busqueda.trim().length > 2 && zonasFiltradas.length === 1) {
      const z = zonasFiltradas[0]
      setVuelo({ lat: z.lat, lng: z.lng, zoom: 15 })
      setZonaResaltada(z.id)
      const t = setTimeout(() => setZonaResaltada(null), 3000)
      return () => clearTimeout(t)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busqueda])

  const zonasCruzadasPorRuta = useMemo(() => {
    return rutasCalculadas.map((r) => zonasAjustadas.filter((z) => distanciaAPolilinea(z, r.coords) <= UMBRAL_CRUCE_KM))
  }, [rutasCalculadas, zonasAjustadas])
  const zonasCruzadasActual = zonasCruzadasPorRuta[rutaSeleccionada] || []

  const zonasCruzadasOrdenadas = useMemo(() => {
    return [...zonasCruzadasActual].sort(
      (a, b) => ORDEN_NIVELES.indexOf(b.ajuste.nivel) - ORDEN_NIVELES.indexOf(a.ajuste.nivel)
    )
  }, [zonasCruzadasActual])

  const rutasConScore = useMemo(() => {
    return rutasCalculadas.map((r, i) => ({
      ...r,
      riesgo: (zonasCruzadasPorRuta[i] || []).reduce((acc, z) => acc + PESO_RIESGO[z.ajuste.nivel], 0),
    }))
  }, [rutasCalculadas, zonasCruzadasPorRuta])

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

  const conteos = Object.keys(NIVELES).reduce((acc, n) => {
    acc[n] = zonasAjustadas.filter((z) => z.ajuste.nivel === n).length
    return acc
  }, {})

  const referencia = miUbicacion || CENTRO_GBA
  const cercanas = useMemo(() => {
    return [...zonasFiltradas]
      .map((z) => ({ ...z, distancia: distanciaKm(referencia, z) }))
      .sort((a, b) => a.distancia - b.distancia)
      .slice(0, 4)
  }, [zonasFiltradas, referencia])

  const hayFiltrosApagados = nivelesActivos.size < Object.keys(NIVELES).length
  const mostrarAlerta = criticosVisibles > 0 && criticosVisibles <= 5 && reportes.length === 0 && rutasCalculadas.length === 0
  let textoTopbar
  if (rutasCalculadas.length > 0) textoTopbar = `Ruta: ${rutasCalculadas[rutaSeleccionada].km} km · ${rutasCalculadas[rutaSeleccionada].min} min`
  else if (cargandoHotspots) textoTopbar = 'Conectando con el servidor de datos...'
  else if (reportes.length > 0) textoTopbar = `${reportes.length} reporte${reportes.length > 1 ? 's' : ''} tuyo${reportes.length > 1 ? 's' : ''} · hace ${segundos}s`
  else if (mostrarAlerta) textoTopbar = `⚠ ${criticosVisibles} zona${criticosVisibles > 1 ? 's' : ''} crítica${criticosVisibles > 1 ? 's' : ''} visible${criticosVisibles > 1 ? 's' : ''}`
  else textoTopbar = `${zonasFiltradas.length} zonas registradas · hace ${segundos}s`

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-dot" />
          <span className="brand-name">MotoSafe</span>
          <span className="brand-badge">GBA</span>
        </div>
        <div className="topbar-right">
          {clima && (
            <div className="clima-badge" title={iconoClima(clima.weathercode).label}>
              {iconoClima(clima.weathercode).icon} {Math.round(clima.temperature)}°C
            </div>
          )}
          <div
            className={`topbar-status ${mostrarAlerta ? 'alerta' : ''} ${reportes.length > 0 ? 'clickeable' : ''}`}
            onClick={() => reportes.length > 0 && setActividadAbierta((v) => !v)}
          >
            <span className="status-dot" />
            {textoTopbar}
          </div>
        </div>
      </header>

      {toast && <div className="toast panel-enter">{toast}</div>}

      {backendError && (
        <div className="ruta-banner ruta-banner-error panel-enter backend-banner">
          ⚠ Sin conexión con el backend (localhost:8000). Reintentando cada 5s.
          <button onClick={cargarHotspots}>Reintentar ahora</button>
        </div>
      )}

      {actividadAbierta && reportes.length > 0 && (
        <div className="actividad-panel panel-enter hazard-edge">
          <div className="actividad-header">
            <span className="cercanas-title">Actividad reciente</span>
            <button className="detalle-cerrar" onClick={() => setActividadAbierta(false)} aria-label="Cerrar panel de actividad">✕</button>
          </div>
          {reportes.map((rep) => {
            const cat = CATEGORIAS_REPORTE.find((c) => c.id === rep.categoria)
            return (
              <button key={rep.id} className="actividad-item" onClick={() => { setVuelo({ lat: rep.lat, lng: rep.lng, zoom: 16 }); setActividadAbierta(false) }}>
                <span className="actividad-icon">{cat?.icon}</span>
                <span className="actividad-texto">
                  <span className="actividad-label">{cat?.label}</span>
                  <span className="actividad-hora">{rep.hora}</span>
                </span>
              </button>
            )
          })}
          <button className="actividad-borrar" onClick={borrarReportes}>Borrar mis reportes</button>
        </div>
      )}

      <div className="searchbar panel-enter hazard-edge" style={{ animationDelay: '0.05s' }}>
        <span className="searchbar-icon">🔍</span>
        <input type="text" placeholder="Buscar zona o avenida..." value={busqueda} onChange={(e) => setBusqueda(e.target.value)} aria-label="Buscar zona o avenida" />
        {busqueda && <button className="searchbar-clear" onClick={() => setBusqueda('')} aria-label="Limpiar búsqueda">✕</button>}
      </div>

      {rutaAbierta && (
        <div className="ruta-form panel-enter hazard-edge">
          <div className="ruta-form-fila">
            <span className="ruta-form-punto ruta-form-punto-origen" />
            <input placeholder="Origen" value={origenTexto} onChange={(e) => { setOrigenTexto(e.target.value); setOrigenPunto(null) }} aria-label="Origen de la ruta" />
            <button className={`ruta-form-pin ${campoActivo === 'origen' ? 'activo' : ''}`} title="Marcar en el mapa" aria-label="Marcar origen en el mapa" onClick={() => marcarEnMapa('origen')}>📍</button>
          </div>
          <button className="ruta-form-swap" onClick={intercambiar} title="Intercambiar" aria-label="Intercambiar origen y destino">⇅</button>
          <div className="ruta-form-fila">
            <span className="ruta-form-punto ruta-form-punto-destino" />
            <input placeholder="Destino" value={destinoTexto} onChange={(e) => { setDestinoTexto(e.target.value); setDestinoPunto(null) }} aria-label="Destino de la ruta" />
            <button className={`ruta-form-pin ${campoActivo === 'destino' ? 'activo' : ''}`} title="Marcar en el mapa" aria-label="Marcar destino en el mapa" onClick={() => marcarEnMapa('destino')}>📍</button>
          </div>
          {campoActivo && <p className="ruta-form-hint">Tocá el mapa para marcar el {campoActivo}.</p>}
          <button className="ruta-form-miubicacion" onClick={usarMiUbicacionComoOrigen}>🎯 Usar mi ubicación como origen</button>
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

      <MapContainer
        center={[CENTRO_GBA.lat, CENTRO_GBA.lng]}
        zoom={11}
        zoomControl={false}
        zoomSnap={0.5}
        zoomDelta={0.5}
        preferCanvas={true}
        className="map"
      >
        <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <ControlesZoom />
        <EscalaMapa />
        <VueloControlado destino={vuelo} />
        <ClicksDeMapa campoActivo={campoActivo} onClick={clicMapa} />

        {rutasCalculadas.map((r, i) => (
          <Polyline
            key={i}
            positions={r.coords}
            pathOptions={{
              color: i === rutaSeleccionada ? '#4FA8E8' : '#6B7178',
              weight: i === rutaSeleccionada ? 5 : 4,
              opacity: i === rutaSeleccionada ? 0.9 : 0.45,
              dashArray: i === rutaSeleccionada ? null : '6 6',
            }}
            eventHandlers={{ click: () => setRutaSeleccionada(i) }}
          />
        ))}

        {origenPunto && (
          <CircleMarker center={[origenPunto.lat, origenPunto.lng]} radius={8} pathOptions={{ color: '#3DDC84', fillColor: '#3DDC84', fillOpacity: 1, weight: 3 }}>
            <Popup>Origen</Popup>
          </CircleMarker>
        )}
        {destinoPunto && (
          <CircleMarker center={[destinoPunto.lat, destinoPunto.lng]} radius={8} pathOptions={{ color: '#FF3B3B', fillColor: '#FF3B3B', fillOpacity: 1, weight: 3 }}>
            <Popup>Destino</Popup>
          </CircleMarker>
        )}

        <MarkerClusterGroup chunkedLoading iconCreateFunction={crearIconoCluster} maxClusterRadius={55}>
          {zonasFiltradas.map((zona) => {
            const cruzada = zonasCruzadasActual.some((z) => z.id === zona.id)
            const resaltada = zonaResaltada === zona.id
            return (
              <CircleMarker
                key={zona.id}
                center={[zona.lat, zona.lng]}
                radius={resaltada ? 14 : zona.ajuste.nivel === 'critico' ? 11 : 8}
                pathOptions={{
                  color: cruzada ? '#4FA8E8' : resaltada ? '#FFC933' : NIVELES[zona.ajuste.nivel].color,
                  fillColor: NIVELES[zona.ajuste.nivel].color,
                  fillOpacity: 0.75,
                  weight: cruzada || zona.ajuste.subio || resaltada ? 3 : 2,
                  nivelData: zona.ajuste.nivel,
                }}
                className={zona.ajuste.nivel === 'critico' || resaltada ? 'pulse-marker' : ''}
                eventHandlers={{ click: () => setZonaSeleccionada(zona) }}
              />
            )
          })}
        </MarkerClusterGroup>

        {reportes.map((rep) => (
          <CircleMarker key={rep.id} center={[rep.lat, rep.lng]} radius={8} pathOptions={{ color: '#FFC933', fillColor: '#FFC933', fillOpacity: 0.7, weight: 2 }} className="pulse-marker-report">
            <Popup>
              <div className="popup-content">
                <span className="popup-nivel" style={{ color: '#FFC933' }}>Tu reporte · {rep.hora}</span>
                <strong>{CATEGORIAS_REPORTE.find((c) => c.id === rep.categoria)?.label}</strong>
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {miUbicacion && (
          <CircleMarker center={[miUbicacion.lat, miUbicacion.lng]} radius={7} pathOptions={{ color: '#4FA8E8', fillColor: '#4FA8E8', fillOpacity: 0.9, weight: 3 }} className="pulse-marker-yo">
            <Popup>Tu ubicación actual</Popup>
          </CircleMarker>
        )}
      </MapContainer>

      {rutasCalculadas.length > 0 && (
        <div className="ruta-resumen panel-enter hazard-edge">
          <div className="ruta-resumen-header">
            <span className="cercanas-title">Opciones de ruta</span>
            <button className="ruta-resumen-editar" onClick={editarRuta} aria-label="Editar origen y destino">✏️</button>
          </div>
          {rutasConScore.length > 1 && (
            <div className="ruta-prioridad">
              <button className={rutaSeleccionada === idxMasRapida ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxMasRapida)}>⚡ Rápida</button>
              {rutasConScore.length >= 3 && (
                <button className={rutaSeleccionada === idxEquilibrada ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxEquilibrada)}>⚖️ Equilibrada</button>
              )}
              <button className={rutaSeleccionada === idxMasSegura ? 'activa' : ''} onClick={() => setRutaSeleccionada(idxMasSegura)}>🛡️ Segura</button>
            </div>
          )}
          {rutasConScore.map((r, i) => (
            <button key={i} className={`ruta-opcion ${i === rutaSeleccionada ? 'activa' : ''}`} onClick={() => setRutaSeleccionada(i)}>
              <span className="ruta-opcion-num">
                Ruta {i + 1}
                {i === idxMasRapida && i === idxMasSegura && <span className="ruta-opcion-badge badge-ambas">⚡🛡️ recomendada</span>}
                {i === idxMasRapida && i !== idxMasSegura && <span className="ruta-opcion-badge badge-rapida">⚡ rápida</span>}
                {i === idxMasSegura && i !== idxMasRapida && <span className="ruta-opcion-badge badge-segura">🛡️ segura</span>}
                {i === idxEquilibrada && i !== idxMasRapida && i !== idxMasSegura && <span className="ruta-opcion-badge badge-equilibrada">⚖️ equilibrada</span>}
              </span>
              <span className="ruta-opcion-datos">{r.km} km · {r.min} min</span>
              <span className={`ruta-opcion-riesgo ${r.riesgo === 0 ? 'ok' : r.riesgo <= 3 ? 'warn' : 'alto'}`}>
                {r.riesgo === 0 ? '✅ sin cruces' : `⚠ riesgo ${r.riesgo} pts · cruza ${zonasCruzadasPorRuta[i].length}`}
              </span>
            </button>
          ))}
          {rutasConScore.length === 1 && (
            <p className="ruta-sin-alternativa">OSRM no encontró una ruta alternativa razonable para este tramo.</p>
          )}
          {zonasCruzadasOrdenadas.length > 0 && (
            <div className="ruta-resumen-detalle">
              {zonasCruzadasOrdenadas.slice(0, 6).map((z) => (
                <div key={z.id} className="ruta-resumen-item">
                  <span className="cercanas-dot" style={{ background: NIVELES[z.ajuste.nivel].color }} />{z.nombre}
                </div>
              ))}
              {zonasCruzadasOrdenadas.length > 6 && (
                <p className="ruta-resumen-mas">+ {zonasCruzadasOrdenadas.length - 6} zonas más de menor riesgo</p>
              )}
            </div>
          )}
          <button className="ruta-resumen-nueva" onClick={cerrarTodoRuta}>Nueva ruta</button>
        </div>
      )}

      {rutasCalculadas.length === 0 && !rutaAbierta && zonaSeleccionada && (
        <div className="detalle-panel panel-enter hazard-edge">
          <button className="detalle-cerrar" onClick={() => setZonaSeleccionada(null)} aria-label="Cerrar detalle de zona">✕</button>
          <span className="popup-nivel" style={{ color: NIVELES[zonaSeleccionada.ajuste.nivel].color }}>
            Riesgo {NIVELES[zonaSeleccionada.ajuste.nivel].label}
          </span>
          <strong className="detalle-nombre">{zonaSeleccionada.nombre}</strong>
          <p className="detalle-motivo">{zonaSeleccionada.motivo}</p>
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

      {rutasCalculadas.length === 0 && !rutaAbierta && !zonaSeleccionada && !actividadAbierta && (
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

      {!rutaAbierta && rutasCalculadas.length === 0 && (
        <button className="route-fab panel-enter" style={{ animationDelay: '0.22s' }} onClick={abrirPanelRuta}>🧭 <span>Trazar ruta</span></button>
      )}

      <button className="locate-fab panel-enter" style={{ animationDelay: '0.25s' }} onClick={pedirUbicacion} disabled={buscandoUbicacion} aria-label="Centrar en mi ubicación">
        {buscandoUbicacion ? <span className="spinner" /> : '🎯'}
      </button>

      <button className={`report-fab panel-enter ${paso !== 'idle' ? 'active' : ''}`} style={{ animationDelay: '0.3s' }} onClick={iniciarReporte}>
        {paso === 'buscando' ? <span className="spinner" /> : paso === 'eligiendo' ? '✕' : '⚠'}
        <span>{paso === 'buscando' ? 'Ubicando...' : paso === 'eligiendo' ? 'Cancelar' : 'Reportar'}</span>
      </button>

      {paso === 'eligiendo' && (
        <div className="report-sheet hazard-edge">
          <h3>¿Qué estás viendo en la vía?</h3>
          <div className="report-options">
            {CATEGORIAS_REPORTE.map((cat) => (
              <button key={cat.id} onClick={() => confirmarReporte(cat.id)}>{cat.icon} {cat.label}</button>
            ))}
          </div>
          <p className="report-hint">📍 Ubicación tomada por GPS del dispositivo.</p>
        </div>
      )}
    </div>
  )
}

export default App