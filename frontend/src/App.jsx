import { useState, useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import './App.css'

const CENTRO_GBA = { lat: -34.62, lng: -58.44 }
const UMBRAL_CRUCE_KM = 0.6 // qué tan cerca de la ruta tiene que estar una zona para contar como "cruzada"

const ZONAS_RIESGO = [
  { id: 1, nombre: 'Av. Rivadavia y Gral. Paz, Ramos Mejía', lat: -34.6432, lng: -58.5622, nivel: 'critico', motivo: 'Alta siniestralidad histórica + hora pico' },
  { id: 2, nombre: 'Av. Mitre, Avellaneda', lat: -34.6626, lng: -58.3654, nivel: 'alto', motivo: 'Cruce sin semáforo, poca visibilidad nocturna' },
  { id: 3, nombre: 'Ruta 8 y Panamericana, San Isidro', lat: -34.4708, lng: -58.5468, nivel: 'alto', motivo: 'Velocidad alta, tránsito pesado' },
  { id: 4, nombre: 'Av. Calchaquí, Quilmes', lat: -34.7186, lng: -58.2831, nivel: 'medio', motivo: 'Pavimento irregular reportado' },
  { id: 5, nombre: 'Av. Hipólito Yrigoyen, Lomas de Zamora', lat: -34.7614, lng: -58.4056, nivel: 'medio', motivo: 'Congestión en horario escolar' },
  { id: 6, nombre: 'Av. Santa Fe, Palermo', lat: -34.5875, lng: -58.4205, nivel: 'bajo', motivo: 'Buena iluminación, baja siniestralidad' },
  { id: 7, nombre: 'Camino de Cintura, La Matanza', lat: -34.7095, lng: -58.6152, nivel: 'critico', motivo: 'Zona con reportes recientes de usuarios' },
  { id: 8, nombre: 'Av. Rivadavia, San Justo', lat: -34.6773, lng: -58.5637, nivel: 'medio', motivo: 'Obra vial en curso' },
]

const NIVELES = {
  bajo:    { label: 'Bajo',    color: '#4CAF6D' },
  medio:   { label: 'Medio',   color: '#E8C547' },
  alto:    { label: 'Alto',    color: '#E8823D' },
  critico: { label: 'Crítico', color: '#E1493F' },
}

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

function VueloControlado({ destino }) {
  const map = useMap()
  useEffect(() => {
    if (destino) map.flyTo([destino.lat, destino.lng], destino.zoom || 15, { duration: 1.1 })
  }, [destino, map])
  return null
}

function ControlesZoom() {
  const map = useMap()
  return (
    <div className="zoom-controls panel-enter" style={{ animationDelay: '0.1s' }}>
      <button onClick={() => map.zoomIn()}>+</button>
      <button onClick={() => map.zoomOut()}>−</button>
    </div>
  )
}

function ClicksDeRuta({ activo, onClick }) {
  useMapEvents({
    click(e) {
      if (activo) onClick({ lat: e.latlng.lat, lng: e.latlng.lng })
    },
  })
  return null
}

function useSegundosDesde() {
  const [segundos, setSegundos] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setSegundos((s) => s + 1), 1000)
    return () => clearInterval(id)
  }, [])
  return segundos
}

function App() {
  const [nivelesActivos, setNivelesActivos] = useState(new Set(Object.keys(NIVELES)))
  const [busqueda, setBusqueda] = useState('')
  const [paso, setPaso] = useState('idle')
  const [ubicacionReporte, setUbicacionReporte] = useState(null)
  const [reportes, setReportes] = useState([])
  const [miUbicacion, setMiUbicacion] = useState(null)
  const [buscandoUbicacion, setBuscandoUbicacion] = useState(false)
  const [vuelo, setVuelo] = useState(null)
  const segundos = useSegundosDesde()

  // --- Ruta ---
  const [modoRuta, setModoRuta] = useState(false)
  const [origen, setOrigen] = useState(null)
  const [destino, setDestino] = useState(null)
  const [rutaCoords, setRutaCoords] = useState(null)
  const [rutaInfo, setRutaInfo] = useState(null) // { km, min }
  const [rutaCargando, setRutaCargando] = useState(false)
  const [rutaError, setRutaError] = useState(null)

  const toggleNivel = (nivel) => {
    setNivelesActivos((prev) => {
      const next = new Set(prev)
      next.has(nivel) ? next.delete(nivel) : next.add(nivel)
      return next
    })
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
  }

  // --- Lógica de ruta ---
  const activarModoRuta = () => {
    setModoRuta(true)
    setOrigen(null)
    setDestino(null)
    setRutaCoords(null)
    setRutaInfo(null)
    setRutaError(null)
  }

  const cancelarRuta = () => {
    setModoRuta(false)
    setOrigen(null)
    setDestino(null)
    setRutaCoords(null)
    setRutaInfo(null)
    setRutaError(null)
  }

  const clicMapaRuta = async (punto) => {
    if (!origen) {
      setOrigen(punto)
      return
    }
    if (!destino) {
      setDestino(punto)
      setModoRuta(false)
      await calcularRuta(origen, punto)
    }
  }

  const calcularRuta = async (a, b) => {
    setRutaCargando(true)
    setRutaError(null)
    try {
      const url = `https://router.project-osrm.org/route/v1/driving/${a.lng},${a.lat};${b.lng},${b.lat}?overview=full&geometries=geojson`
      const res = await fetch(url)
      if (!res.ok) throw new Error('OSRM respondió con error')
      const data = await res.json()
      if (!data.routes || data.routes.length === 0) throw new Error('Sin ruta disponible')
      const coords = data.routes[0].geometry.coordinates.map(([lng, lat]) => [lat, lng])
      setRutaCoords(coords)
      setRutaInfo({
        km: (data.routes[0].distance / 1000).toFixed(1),
        min: Math.round(data.routes[0].duration / 60),
      })
    } catch (err) {
      setRutaError('No se pudo calcular la ruta (servidor de demo caído o sin conexión). Probá de nuevo.')
    } finally {
      setRutaCargando(false)
    }
  }

  const zonasCruzadas = useMemo(() => {
    if (!rutaCoords) return []
    return ZONAS_RIESGO.filter((z) => distanciaAPolilinea(z, rutaCoords) <= UMBRAL_CRUCE_KM)
  }, [rutaCoords])

  const zonasFiltradas = ZONAS_RIESGO.filter(
    (z) => nivelesActivos.has(z.nivel) && z.nombre.toLowerCase().includes(busqueda.toLowerCase())
  )
  const criticosVisibles = zonasFiltradas.filter((z) => z.nivel === 'critico').length

  const conteos = Object.keys(NIVELES).reduce((acc, n) => {
    acc[n] = ZONAS_RIESGO.filter((z) => z.nivel === n).length
    return acc
  }, {})

  const referencia = miUbicacion || CENTRO_GBA
  const cercanas = useMemo(() => {
    return [...zonasFiltradas]
      .map((z) => ({ ...z, distancia: distanciaKm(referencia, z) }))
      .sort((a, b) => a.distancia - b.distancia)
      .slice(0, 4)
  }, [zonasFiltradas, referencia])

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-dot" />
          <span className="brand-name">MotoSafe</span>
          <span className="brand-badge">GBA</span>
        </div>
        <div className={`topbar-status ${criticosVisibles > 0 && reportes.length === 0 && !rutaCoords ? 'alerta' : ''}`}>
          <span className="status-dot" />
          {rutaCoords
            ? `Ruta: ${rutaInfo.km} km · ${rutaInfo.min} min`
            : reportes.length > 0
              ? `${reportes.length} reporte${reportes.length > 1 ? 's' : ''} tuyo${reportes.length > 1 ? 's' : ''} · hace ${segundos}s`
              : criticosVisibles > 0
                ? `⚠ ${criticosVisibles} zona${criticosVisibles > 1 ? 's' : ''} crítica${criticosVisibles > 1 ? 's' : ''} en el mapa`
                : `Datos de ejemplo · actualizado hace ${segundos}s`}
        </div>
      </header>

      <div className="searchbar panel-enter hazard-edge" style={{ animationDelay: '0.05s' }}>
        <span className="searchbar-icon">🔍</span>
        <input type="text" placeholder="Buscar zona o avenida..." value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
        {busqueda && <button className="searchbar-clear" onClick={() => setBusqueda('')}>✕</button>}
      </div>

      {modoRuta && (
        <div className="ruta-banner panel-enter">
          {!origen ? '📍 Tocá el mapa para marcar el origen' : '🏁 Ahora tocá el destino'}
          <button onClick={cancelarRuta}>Cancelar</button>
        </div>
      )}

      {rutaCargando && (
        <div className="ruta-banner panel-enter">
          <span className="spinner spinner-dark" /> Calculando ruta real...
        </div>
      )}

      {rutaError && (
        <div className="ruta-banner ruta-banner-error panel-enter">
          {rutaError}
          <button onClick={cancelarRuta}>Cerrar</button>
        </div>
      )}

      <MapContainer center={[CENTRO_GBA.lat, CENTRO_GBA.lng]} zoom={11} zoomControl={false} className="map">
        <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <ControlesZoom />
        <VueloControlado destino={vuelo} />
        <ClicksDeRuta activo={modoRuta} onClick={clicMapaRuta} />

        {rutaCoords && (
          <Polyline positions={rutaCoords} pathOptions={{ color: '#4FA8E8', weight: 5, opacity: 0.85 }} />
        )}

        {origen && (
          <CircleMarker center={[origen.lat, origen.lng]} radius={8} pathOptions={{ color: '#4CAF6D', fillColor: '#4CAF6D', fillOpacity: 1, weight: 3 }}>
            <Popup>Origen</Popup>
          </CircleMarker>
        )}
        {destino && (
          <CircleMarker center={[destino.lat, destino.lng]} radius={8} pathOptions={{ color: '#E1493F', fillColor: '#E1493F', fillOpacity: 1, weight: 3 }}>
            <Popup>Destino</Popup>
          </CircleMarker>
        )}

        {zonasFiltradas.map((zona) => {
          const cruzada = zonasCruzadas.some((z) => z.id === zona.id)
          return (
            <div key={zona.id}>
              {(zona.nivel === 'critico' || cruzada) && (
                <CircleMarker
                  center={[zona.lat, zona.lng]}
                  radius={12}
                  pathOptions={{ color: cruzada ? '#4FA8E8' : NIVELES.critico.color, fillOpacity: 0, weight: 2 }}
                  className="radar-ping"
                />
              )}
              <CircleMarker
                center={[zona.lat, zona.lng]}
                radius={zona.nivel === 'critico' ? 12 : 9}
                pathOptions={{
                  color: cruzada ? '#4FA8E8' : NIVELES[zona.nivel].color,
                  fillColor: NIVELES[zona.nivel].color,
                  fillOpacity: 0.6,
                  weight: cruzada ? 3 : 2,
                }}
                className={zona.nivel === 'critico' ? 'pulse-marker' : ''}
              >
                <Popup>
                  <div className="popup-content">
                    <span className="popup-nivel" style={{ color: NIVELES[zona.nivel].color }}>Riesgo {NIVELES[zona.nivel].label}</span>
                    <strong>{zona.nombre}</strong>
                    <p>{zona.motivo}</p>
                    {cruzada && <p className="popup-cruzada">⚠ Tu ruta pasa cerca de esta zona</p>}
                  </div>
                </Popup>
              </CircleMarker>
            </div>
          )
        })}

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

      {rutaCoords && (
        <div className="ruta-resumen panel-enter hazard-edge">
          <span className="cercanas-title">Resumen de la ruta</span>
          <p className="ruta-resumen-linea">{rutaInfo.km} km · ~{rutaInfo.min} min</p>
          {zonasCruzadas.length === 0 ? (
            <p className="ruta-resumen-ok">✅ No cruza zonas de riesgo alto o crítico registradas</p>
          ) : (
            <>
              <p className="ruta-resumen-warn">⚠ Cruza {zonasCruzadas.length} zona{zonasCruzadas.length > 1 ? 's' : ''} de riesgo:</p>
              {zonasCruzadas.map((z) => (
                <div key={z.id} className="ruta-resumen-item">
                  <span className="cercanas-dot" style={{ background: NIVELES[z.nivel].color }} />
                  {z.nombre}
                </div>
              ))}
            </>
          )}
          <button className="ruta-resumen-nueva" onClick={cancelarRuta}>Nueva ruta</button>
        </div>
      )}

      {!rutaCoords && !modoRuta && (
        <div className="cercanas-panel panel-enter hazard-edge" style={{ animationDelay: '0.15s' }}>
          <span className="cercanas-title">Zonas cercanas {miUbicacion ? '· a vos' : '· al centro del GBA'}</span>
          {cercanas.length === 0 && <p className="cercanas-empty">Sin resultados</p>}
          {cercanas.map((z) => (
            <button key={z.id} className="cercanas-item" onClick={() => setVuelo({ lat: z.lat, lng: z.lng, zoom: 15 })}>
              <span className="cercanas-dot" style={{ background: NIVELES[z.nivel].color }} />
              <span className="cercanas-nombre">{z.nombre}</span>
              <span className="cercanas-km">{z.distancia.toFixed(1)} km</span>
            </button>
          ))}
        </div>
      )}

      <div className="legend panel-enter hazard-edge" style={{ animationDelay: '0.2s' }}>
        <span className="legend-title">Nivel de riesgo <em>(tocá para filtrar)</em></span>
        {Object.entries(NIVELES).map(([key, val]) => (
          <button key={key} className={`legend-item ${nivelesActivos.has(key) ? '' : 'inactive'}`} onClick={() => toggleNivel(key)}>
            <span className="legend-swatch" style={{ background: val.color }} />
            {val.label}
            <span className="legend-count">{conteos[key]}</span>
          </button>
        ))}
      </div>

      {!modoRuta && !rutaCoords && (
        <button className="route-fab panel-enter" style={{ animationDelay: '0.22s' }} onClick={activarModoRuta}>
          🧭 <span>Trazar ruta</span>
        </button>
      )}

      <button className="locate-fab panel-enter" style={{ animationDelay: '0.25s' }} onClick={pedirUbicacion} disabled={buscandoUbicacion}>
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